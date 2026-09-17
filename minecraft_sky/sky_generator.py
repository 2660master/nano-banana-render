#!/usr/bin/env python3
"""Dark fantasy night sky generator for Minecraft skybox textures.

The sky is rendered once as a seamless 360x180 equirectangular panorama and
can then be projected onto the six cube faces a Minecraft sky renderer wants
(FabricSkyBoxes "square-textured", a custom mod renderer, or an atlas).

Everything is procedural:
  * 3D value-noise fbm sampled on the unit sphere, so there are no seams and
    no pole pinching in the nebulae;
  * analytic moons with phase, limb darkening and crater texture;
  * star splats with latitude-compensated kernels so stars stay round after
    the cube projection.

Usage:
    python3 sky_generator.py --list
    python3 sky_generator.py --preview            # all concepts, preview size
    python3 sky_generator.py bloodmoon --faces    # full res + cube faces
"""

from __future__ import annotations

import argparse
import math
import os

import numpy as np
from PIL import Image

# --------------------------------------------------------------- helpers --

ROOT = os.path.dirname(os.path.abspath(__file__))
CHUNK_ROWS = 64  # rows rendered per pass, keeps peak memory small


def srgb_to_linear(c):
    """(r, g, b) in 0-255 sRGB -> linear float32 triplet."""
    a = np.asarray(c, dtype=np.float32) / 255.0
    return (a ** 2.2).astype(np.float32)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def normalize(v):
    v = np.asarray(v, dtype=np.float32)
    return v / np.linalg.norm(v)


def direction(lat_deg, lon_deg):
    """Sky direction from elevation/azimuth in degrees. +y is up."""
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return np.array(
        [math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)],
        dtype=np.float32,
    )


# ----------------------------------------------------------------- noise --

_GRIDS: dict[tuple[int, int], np.ndarray] = {}


def _grid(seed: int, res: int) -> np.ndarray:
    key = (seed, res)
    g = _GRIDS.get(key)
    if g is None:
        g = np.random.default_rng(seed).random((res, res, res), dtype=np.float32)
        _GRIDS[key] = g
    return g


def vnoise(p, seed, res=64):
    """3D value noise: one lattice cell per unit of ``p``.

    A layer's ``scale`` is therefore "features per unit direction" - at
    scale 2 roughly four blobs span the sky, at scale 10 they are fist
    sized. The lattice repeats every ``res`` cells, far outside the unit
    sphere, so the sky never visibly tiles.
    """
    g = _grid(seed, res)
    i = np.floor(p)
    f = p - i
    f = f * f * (3.0 - 2.0 * f)
    i = i.astype(np.int32)
    x0 = i[..., 0] % res
    y0 = i[..., 1] % res
    z0 = i[..., 2] % res
    x1 = (x0 + 1) % res
    y1 = (y0 + 1) % res
    z1 = (z0 + 1) % res
    fx, fy, fz = f[..., 0], f[..., 1], f[..., 2]

    c00 = g[x0, y0, z0] * (1 - fx) + g[x1, y0, z0] * fx
    c10 = g[x0, y1, z0] * (1 - fx) + g[x1, y1, z0] * fx
    c01 = g[x0, y0, z1] * (1 - fx) + g[x1, y0, z1] * fx
    c11 = g[x0, y1, z1] * (1 - fx) + g[x1, y1, z1] * fx
    c0 = c00 * (1 - fy) + c10 * fy
    c1 = c01 * (1 - fy) + c11 * fy
    return c0 * (1 - fz) + c1 * fz


def _rotation(axis, angle):
    ax = normalize(axis)
    x, y, z = ax
    c, s, t = math.cos(angle), math.sin(angle), 1 - math.cos(angle)
    return np.array([
        [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
        [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
        [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
    ], dtype=np.float32)


# Turning the sample frame between octaves keeps the lattice from lining up
# with itself, which is what makes value-noise clouds grow straight edges.
_OCTAVE_ROT = _rotation((0.53, 0.81, 0.25), 0.947)


def fbm(p, seed, octaves=5, lac=2.0, gain=0.5, res=64, ridged=False):
    total = np.zeros(p.shape[:-1], np.float32)
    amp, norm, freq = 1.0, 0.0, 1.0
    for o in range(octaves):
        if o:
            p = p @ _OCTAVE_ROT
        n = vnoise(p * freq, seed + 101 * o, res)
        if ridged:
            n = 1.0 - np.abs(n * 2.0 - 1.0)
            n = n * n
        total += amp * n
        norm += amp
        amp *= gain
        freq *= lac
    return total / norm


def domain_warp(p, seed, amount, octaves=4):
    dx = fbm(p, seed + 3, octaves) - 0.5
    dy = fbm(p + 5.2, seed + 37, octaves) - 0.5
    dz = fbm(p + 11.3, seed + 71, octaves) - 0.5
    return p + amount * np.stack([dx, dy, dz], axis=-1)


# --------------------------------------------------------------- shading --

def _dirs_block(W, H, y0, y1):
    lon = (np.arange(W, dtype=np.float32) + 0.5) / W * (2 * np.pi) - np.pi
    lat = np.pi / 2 - (np.arange(y0, y1, dtype=np.float32) + 0.5) / H * np.pi
    lon2, lat2 = np.meshgrid(lon, lat)
    cl = np.cos(lat2)
    d = np.stack([cl * np.sin(lon2), np.sin(lat2), cl * np.cos(lon2)], axis=-1)
    return d.astype(np.float32), lat2.astype(np.float32), lon2.astype(np.float32)


def shade_nebula(col, d, cfg, aa, over=False):
    """Additive nebulae, subtractive dust and lit cloud decks.

    Layer modes:
      add    - glowing gas, colour ramped between ``color`` and ``color2``
      mul    - dark dust that eats whatever is behind it
      cloud  - an opaque deck banded around an elevation, with rim light
               picked up from ``cfg['light_dir']``

    Layers flagged ``over`` are drawn after the moons, so a cloud bank can
    veil the moon instead of always sitting behind it.
    """
    elev = d[..., 1]
    for layer in cfg.get("nebula", []):
        if bool(layer.get("over", False)) != over:
            continue
        p = d * layer["scale"]
        if layer.get("warp", 0.0):
            p = domain_warp(p, layer["seed"] + 500, layer["warp"],
                            octaves=layer.get("warp_octaves", 4))
        n = fbm(
            p,
            layer["seed"],
            octaves=layer.get("octaves", 5),
            gain=layer.get("gain", 0.5),
            ridged=layer.get("ridged", False),
        )
        mask = smoothstep(layer.get("lo", 0.45), layer.get("hi", 0.85), n)
        mask = mask ** layer.get("power", 1.0)

        if "band_axis" in layer:  # confine the layer to a great-circle band
            axis = normalize(layer["band_axis"])
            t = d @ axis
            mask *= np.exp(-((t / layer.get("band_width", 0.35)) ** 2))

        if layer.get("coverage_scale"):  # large scale break-up, no flat fog
            cov = fbm(d * layer["coverage_scale"], layer["seed"] + 900, octaves=3)
            mask *= smoothstep(layer.get("cov_lo", 0.42),
                               layer.get("cov_hi", 0.72), cov)

        if layer.get("detail"):  # break up the mask's own contours
            dn = fbm(d * layer.get("detail_scale", 7.0), layer["seed"] + 300,
                     octaves=3, gain=0.5)
            mask *= 1.0 - layer["detail"] * (1.0 - dn)

        if "elev_centre" in layer:  # keep a deck near one elevation
            mask *= np.exp(
                -((elev - layer["elev_centre"]) / layer.get("elev_spread", 0.35)) ** 2
            )

        mode = layer.get("mode", "add")

        if mode == "mul":  # dark dust that eats light
            col *= 1.0 - mask[..., None] * layer.get("strength", 1.0)
            continue

        if mode == "cloud":
            body = srgb_to_linear(layer["color"])
            col *= 1.0 - (mask * layer.get("opacity", 0.9))[..., None]
            col += (mask * layer.get("ambient", 0.05))[..., None] * body
            rim = layer.get("rim", 0.0)
            if rim and cfg.get("light_dir") is not None:
                ld = normalize(cfg["light_dir"])
                prox = np.exp(
                    -((np.arccos(np.clip(d @ ld, -1, 1))
                       / math.radians(layer.get("rim_size", 55.0))) ** 2)
                )
                edge = np.clip(mask * (1.0 - mask) * 4.0, 0.0, 1.0) ** 1.4
                col += (edge * prox * rim)[..., None] * srgb_to_linear(
                    layer.get("rim_color", (255, 255, 255))
                )
            continue

        ca = srgb_to_linear(layer["color"])
        cb = srgb_to_linear(layer.get("color2", layer["color"]))
        mix = np.clip((n - layer.get("lo", 0.45)) * 2.2, 0.0, 1.0)[..., None]
        col += (mask[..., None] * layer["strength"]) * (ca * (1 - mix) + cb * mix)
    return col


def _silhouette(phi, seed, amount, harmonics=8, facets=0):
    """Wobble the radius of a disc so it reads as a rock, not a circle.

    ``facets`` interpolates linearly between a ring of random radii, which
    leaves straight edges and sharp corners - what broken rock looks like.
    Without it the outline is a sum of sines: smooth lumps, right for a
    body big enough for gravity to have rounded it off.
    """
    rng = np.random.default_rng(seed)
    if facets:
        radii = rng.uniform(-1.0, 1.0, facets).astype(np.float32)
        k = (phi / (2 * np.pi) + 0.5) * facets
        i0 = np.floor(k).astype(np.int32) % facets
        t = k - np.floor(k)
        return amount * (radii[i0] * (1 - t) + radii[(i0 + 1) % facets] * t)

    out = np.zeros_like(phi)
    weight = 0.0
    for k in range(2, 2 + harmonics):
        amp = rng.uniform(0.45, 1.0) / (k - 1) ** 0.6
        out += amp * np.sin(k * phi + rng.uniform(0.0, 2 * np.pi))
        weight += amp
    return amount * out / weight


def shade_moon(col, d, moon, aa):
    md = normalize(moon["dir"])
    c = d @ md
    r = math.radians(moon["radius"])
    glow = moon.get("glow", 0.0)

    # Everything this moon can touch lies within `reach`. Most row blocks are
    # nowhere near it, and skipping them is what makes a debris field of
    # dozens of chunks affordable.
    reach = r * (moon.get("glow_size", 6.0) * 2.6 if glow else 2.0) + 4 * aa
    if float(c.max()) < math.cos(min(reach, math.pi)):
        return col

    ang = np.arccos(np.clip(c, -1.0, 1.0))

    if glow:
        halo = np.exp(-((ang / (r * moon.get("glow_size", 6.0))) ** 1.6)) * glow
        halo += np.exp(-((ang / (r * 1.8)) ** 2)) * glow * 1.7
        col += halo[..., None] * srgb_to_linear(moon.get("glow_color", moon["color"]))

    up = np.array([0.0, 1.0, 0.0], np.float32)
    if abs(float(md @ up)) > 0.95:
        up = np.array([0.0, 0.0, 1.0], np.float32)
    uax = normalize(np.cross(up, md))
    vax = np.cross(md, uax)

    sr = math.sin(r)
    u = (d @ uax) / sr
    v = (d @ vax) / sr

    rad = 1.0
    if moon.get("irregular"):
        rad = 1.0 + _silhouette(np.arctan2(v, u), moon["seed"],
                                moon["irregular"],
                                facets=moon.get("facets", 0))

    disc = smoothstep(r * rad + aa, r * rad - aa, ang)
    if not np.any(disc > 0.001):
        return col

    un = np.clip(u / rad, -1.0, 1.0)
    vn = np.clip(v / rad, -1.0, 1.0)
    nz = np.sqrt(np.clip(1.0 - un * un - vn * vn, 0.0, 1.0))
    nrm = uax * un[..., None] + vax * vn[..., None] + md * nz[..., None]

    # Relief comes from bump mapping, not from painting light and dark on a
    # smooth ball: craters only read as craters when their rims catch the
    # light and their floors fall into shadow.
    bump = moon.get("bump", 0.0)
    if bump:
        hs = moon.get("bump_scale", 14.0)
        oct_ = moon.get("bump_octaves", 3)
        # The finite difference has to stay well inside one cell of the
        # finest octave, otherwise the two samples are uncorrelated and the
        # "gradient" is just per-pixel noise. Dividing by hs keeps `bump`
        # meaning the same thing at any feature size.
        eps = 0.35 / (hs * 2 ** (oct_ - 1))
        # A low gain keeps the big shapes in charge of the gradient. At
        # gain 0.5 every octave contributes the same slope and the relief
        # turns into sand.
        hg = moon.get("bump_gain", 0.30)
        rg = moon.get("bump_ridged", False)
        kw = dict(octaves=oct_, gain=hg, ridged=rg)
        h0 = fbm(nrm * hs, moon["seed"] + 91, **kw)
        hu = fbm((nrm + uax * eps) * hs, moon["seed"] + 91, **kw)
        hv = fbm((nrm + vax * eps) * hs, moon["seed"] + 91, **kw)
        grad = ((hu - h0)[..., None] * uax + (hv - h0)[..., None] * vax) / eps
        nrm = nrm - (bump / hs) * grad
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)

    shade = np.ones_like(un)
    if moon.get("light") is not None:  # crescent / gibbous terminator
        ld = normalize(moon["light"])
        shade = smoothstep(-0.12, 0.25, nrm @ ld)
        shade = moon.get("ambient", 0.05) + (1.0 - moon.get("ambient", 0.05)) * shade

    shade *= 0.55 + 0.45 * nz ** moon.get("limb", 0.45)  # limb darkening

    tex = moon.get("texture", 0.0)
    if tex:
        craters = fbm(nrm * moon.get("texture_scale", 9.0), moon["seed"], octaves=5)
        shade *= 1.0 - tex * (1.0 - craters)
    fine = moon.get("fine_texture", 0.0)
    if fine:  # the pitting you only see once the moon is big on screen
        f2 = fbm(nrm * moon.get("fine_scale", 30.0), moon["seed"] + 7, octaves=4)
        shade *= 1.0 - fine * (1.0 - f2)
    maria = moon.get("maria", 0.0)
    if maria:  # big dark seas, the shapes you read from the ground
        m = fbm(nrm * moon.get("maria_scale", 2.0), moon["seed"] + 55, octaves=3)
        shade *= 1.0 - maria * smoothstep(0.44, 0.74, m)

    cr = None
    cracks = moon.get("cracks", 0.0)
    if cracks:
        cr = fbm(nrm * moon.get("crack_scale", 5.0), moon["seed"] + 21,
                 octaves=moon.get("crack_octaves", 4),
                 gain=moon.get("crack_gain", 0.5), ridged=True)
        shade *= 1.0 - cracks * smoothstep(0.55, 0.95, cr)

    body = (disc * shade * moon.get("brightness", 1.0))[..., None] * srgb_to_linear(
        moon["color"]
    )
    emit = moon.get("crack_glow", 0.0)
    if emit and cr is not None:  # light still leaking out of the fractures
        core = smoothstep(moon.get("crack_glow_lo", 0.80), 0.995, cr) \
            * disc * emit
        body = body + core[..., None] * srgb_to_linear(
            moon.get("crack_color", (168, 140, 255))
        )
    return col * (1.0 - disc[..., None]) + body


def debris_ring(axis, count, seed, tilt=5.0, size=(0.10, 1.3), gap=None,
                **common):
    """Chunks strung along a great circle - a ruined moon's leftovers.

    ``axis`` is the ring plane's normal, so the ring itself arcs across the
    sky perpendicular to it. ``tilt`` is how many degrees chunks stray out
    of the plane, and ``gap`` optionally opens a stretch of empty ring
    (start, end in degrees) so it reads as broken rather than tidy.
    """
    rng = np.random.default_rng(seed)
    n = normalize(axis)
    up = np.array([0.0, 1.0, 0.0], np.float32)
    if abs(float(n @ up)) > 0.95:
        up = np.array([0.0, 0.0, 1.0], np.float32)
    uax = normalize(np.cross(up, n))
    vax = np.cross(n, uax)

    out = []
    while len(out) < count:
        deg = rng.uniform(0.0, 360.0)
        if gap and gap[0] <= deg <= gap[1]:
            continue
        th = math.radians(deg)
        d = uax * math.cos(th) + vax * math.sin(th)
        d = normalize(d + n * math.radians(tilt) * rng.normal())
        chunk = dict(common)
        chunk["dir"] = d
        chunk["radius"] = size[0] + (size[1] - size[0]) * rng.random() ** 2.6
        chunk["seed"] = int(rng.integers(1, 10 ** 6))
        chunk["irregular"] = float(rng.uniform(0.18, 0.38))
        chunk["facets"] = int(rng.integers(6, 11))
        chunk["brightness"] = common.get("brightness", 1.0) * rng.uniform(0.7, 1.1)
        out.append(chunk)
    return out


def debris_field(centre, count, seed, inner=1.5, outer=7.0, size=(0.22, 2.0),
                 spread=1.7, flatten=0.5, **common):
    """Chunks scattered around a broken moon, thinning out with distance.

    ``inner`` and ``outer`` are degrees from the moon's centre, so ``inner``
    has to clear the moon's own radius or the chunks end up painted on top
    of its face. ``flatten`` squashes the field across one axis, which reads
    as debris strung out along the orbit rather than a uniform halo.

    Each chunk is an ordinary moon dict, so it picks up the same lighting,
    cratering and irregular silhouette as the body it came off.
    """
    rng = np.random.default_rng(seed)
    cd = normalize(centre)
    up = np.array([0.0, 1.0, 0.0], np.float32)
    if abs(float(cd @ up)) > 0.95:
        up = np.array([0.0, 0.0, 1.0], np.float32)
    uax = normalize(np.cross(up, cd))
    vax = np.cross(cd, uax)

    out = []
    for _ in range(count):
        phi = rng.uniform(0.0, 2 * math.pi)
        squash = math.hypot(math.cos(phi), flatten * math.sin(phi))
        dist = math.radians(
            inner + (outer - inner) * rng.random() ** spread * squash)
        off = uax * math.cos(phi) + vax * math.sin(phi)
        chunk = dict(common)
        chunk["dir"] = normalize(cd * math.cos(dist) + off * math.sin(dist))
        chunk["radius"] = size[0] + (size[1] - size[0]) * rng.random() ** 2.4
        chunk["seed"] = int(rng.integers(1, 10 ** 6))
        chunk["irregular"] = float(rng.uniform(0.16, 0.34))
        chunk["facets"] = int(rng.integers(6, 11))
        chunk["brightness"] = common.get("brightness", 1.0) * rng.uniform(0.8, 1.15)
        out.append(chunk)
    return out


def shade_aurora(col, d, lat, lon, cfg):
    au = cfg.get("aurora")
    if not au:
        return col
    for rib in au["ribbons"]:
        wobble = fbm(d * rib.get("noise_scale", 1.6), rib["seed"], octaves=4) - 0.5
        centre = math.radians(rib["lat"]) + math.radians(rib["amp"]) * np.sin(
            lon * rib["waves"] + rib["phase"]
        ) + math.radians(rib.get("wobble", 14.0)) * wobble
        t = (lat - centre) / math.radians(rib["width"])
        # real curtains have a hard bottom edge and trail off overhead
        band = np.exp(-(t * np.where(t > 0, 0.55, 1.7)) ** 2)

        # squashing y keeps the noise coherent vertically, which is what
        # turns a blob of noise into hanging rays
        stri = fbm(d * np.array([rib.get("striation", 9.0), 0.10,
                                 rib.get("striation", 9.0)], np.float32),
                   rib["seed"] + 4, octaves=4, gain=0.55)
        band *= 0.10 + 1.30 * smoothstep(0.40, 0.86, stri)
        band *= smoothstep(-0.06, 0.18, np.sin(lat))  # die out at the horizon

        hi = np.clip(t * 0.5 + 0.5, 0.0, 1.0)[..., None]
        ca, cb = srgb_to_linear(rib["color"]), srgb_to_linear(rib["color2"])
        col += (band[..., None] * rib["strength"]) * (ca * hi + cb * (1.0 - hi))
    return col


def shade_block(d, lat, lon, cfg, aa):
    elev = d[..., 1]

    t = smoothstep(-0.05, 0.85, elev)[..., None]
    col = srgb_to_linear(cfg["horizon"]) * (1 - t) + srgb_to_linear(cfg["zenith"]) * t
    col = col * np.ones(d.shape[:-1] + (1,), np.float32)

    below = smoothstep(0.0, -0.35, elev)[..., None]
    col = col * (1 - below) + srgb_to_linear(cfg.get("ground", (4, 4, 6))) * below

    col = shade_nebula(col, d, cfg, aa, over=False)
    col = shade_aurora(col, d, lat, lon, cfg)

    hg = cfg.get("horizon_glow")
    if hg:
        falloff = np.exp(-np.clip(elev, 0.0, 1.0) / hg["height"])
        falloff *= smoothstep(-0.25, 0.02, elev)
        if hg.get("patchy"):
            n = fbm(d * hg.get("patch_scale", 1.4), hg.get("seed", 99), octaves=4)
            floor = hg.get("patch_floor", 0.25)
            falloff *= floor + (1.6 - floor) * smoothstep(
                hg.get("patch_lo", 0.30), hg.get("patch_hi", 0.75), n)
        col += (falloff * hg["strength"])[..., None] * srgb_to_linear(hg["color"])

    for moon in cfg.get("moons", []):
        col = shade_moon(col, d, moon, aa)

    col = shade_nebula(col, d, cfg, aa, over=True)
    return col


def render_panorama(cfg, W, H):
    out = np.zeros((H, W, 3), np.float32)
    aa = 1.6 * np.pi / H
    for y0 in range(0, H, CHUNK_ROWS):
        y1 = min(y0 + CHUNK_ROWS, H)
        d, lat, lon = _dirs_block(W, H, y0, y1)
        out[y0:y1] = shade_block(d, lat, lon, cfg, aa)
    return out


# ----------------------------------------------------------------- stars --

def _splat(img, x, y, sx, sy, colour, spike=0.0):
    H, W, _ = img.shape
    rx = int(min(max(2.0, 3.0 * sx), 64))
    ry = int(min(max(2.0, 3.0 * sy), 24))
    if spike:
        rx = min(int(rx + 7 * spike), 96)
        ry = min(int(ry + 7 * spike), 48)

    cols = (np.arange(-rx, rx + 1) + int(round(x))) % W
    rows = np.arange(-ry, ry + 1) + int(round(y))
    keep = (rows >= 0) & (rows < H)
    rows = rows[keep]
    if rows.size == 0:
        return
    dx = (cols.astype(np.float32) - x + W / 2) % W - W / 2
    dy = rows.astype(np.float32) - y

    g = np.exp(-0.5 * ((dx / sx) ** 2)[None, :] - 0.5 * ((dy / sy) ** 2)[:, None])
    if spike:
        line = np.exp(-np.abs(dx) / (rx * 0.42))[None, :] * np.exp(
            -0.5 * (dy / (sy * 0.55)) ** 2
        )[:, None]
        line += np.exp(-np.abs(dy) / (ry * 0.42))[:, None] * np.exp(
            -0.5 * (dx / (sx * 0.55)) ** 2
        )[None, :]
        g = g + spike * 0.45 * line
    patch = g[..., None] * colour
    img[np.ix_(rows, cols)] += patch


def add_stars(img, cfg, seed_offset=0):
    st = cfg.get("stars")
    if not st:
        return
    H, W, _ = img.shape
    rng = np.random.default_rng(cfg["seed"] + 1234 + seed_offset)
    n = int(st["count"] * (W * H) / (2048 * 1024))

    u = rng.random(n) * 2.0 - 1.0
    lon = rng.random(n) * 2 * np.pi - np.pi
    lat = np.arcsin(u)

    if st.get("cluster_axis") is not None:  # crowd the milky way band
        axis = normalize(st["cluster_axis"])
        cl = np.cos(lat)
        d = np.stack([cl * np.sin(lon), np.sin(lat), cl * np.cos(lon)], -1)
        band = np.exp(-((d @ axis) / st.get("cluster_width", 0.30)) ** 2)
        keep = rng.random(n) < (st.get("cluster_base", 0.45) + 0.55 * band)
        lat, lon = lat[keep], lon[keep]
        n = lat.size

    mag = rng.random(n) ** st.get("falloff", 3.2)
    bright = rng.random(n) < st.get("bright_frac", 0.006)
    mag[bright] = 0.75 + 0.25 * rng.random(int(bright.sum()))
    # only the handful of named stars get glare, the rest stay points
    spike = np.where(bright, st.get("spikes", 0.6) * mag ** 2, 0.0)

    warm = srgb_to_linear(st.get("warm", (255, 196, 150)))
    cool = srgb_to_linear(st.get("cool", (176, 206, 255)))
    tint = rng.random(n)[:, None] ** st.get("warm_bias", 2.0)
    colour = (cool * (1 - tint) + warm * tint) * st["brightness"]
    colour *= (0.05 + mag[:, None]) ** 1.5

    x = (lon + np.pi) / (2 * np.pi) * W
    y = (np.pi / 2 - lat) / np.pi * H
    coslat = np.maximum(np.cos(lat), 0.02)
    base = st.get("size", 0.55) * (W / 2048.0)

    for k in range(n):
        s = base * (0.55 + 1.35 * mag[k])
        _splat(img, x[k], y[k], s / coslat[k], s, colour[k], spike=float(spike[k]))


def add_embers(img, cfg):
    em = cfg.get("embers")
    if not em:
        return
    H, W, _ = img.shape
    rng = np.random.default_rng(cfg["seed"] + 77)
    n = int(em["count"] * (W * H) / (2048 * 1024))
    lat = np.arcsin(rng.random(n) ** em.get("horizon_bias", 2.4) * 0.9)
    lon = rng.random(n) * 2 * np.pi - np.pi
    mag = rng.random(n) ** 1.7
    colour = srgb_to_linear(em["color"])[None, :] * (em["brightness"] * mag[:, None])
    x = (lon + np.pi) / (2 * np.pi) * W
    y = (np.pi / 2 - lat) / np.pi * H
    coslat = np.maximum(np.cos(lat), 0.05)
    base = em.get("size", 0.9) * (W / 2048.0)
    for k in range(n):
        s = base * (0.6 + 1.5 * mag[k])
        _splat(img, x[k], y[k], s / coslat[k], s, colour[k])


# ------------------------------------------------------------ tonemapping --

def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0)


def to_image(hdr, cfg, seed=0):
    grade = cfg.get("grade", {})
    x = hdr * grade.get("exposure", 1.0)
    x = aces(x)
    x = np.clip(x, 0.0, 1.0) ** (1.0 / 2.2)

    sat = grade.get("saturation", 1.0)
    if sat != 1.0:
        lum = (x * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
        x = np.clip(lum + (x - lum) * sat, 0.0, 1.0)
    if "lift" in grade:
        x = np.clip(x + srgb_to_linear(grade["lift"]) * 0.25, 0.0, 1.0)

    rng = np.random.default_rng(seed + 5)
    x = x + (rng.random(x.shape, dtype=np.float32) - 0.5) / 255.0  # kill banding
    return Image.fromarray(np.clip(x * 255.0 + 0.5, 0, 255).astype(np.uint8))


# ------------------------------------------------------------ projections --

def sample_equirect(pano, d):
    """Bilinear sample of an equirectangular float image by direction."""
    H, W, _ = pano.shape
    lon = np.arctan2(d[..., 0], d[..., 2])
    lat = np.arcsin(np.clip(d[..., 1], -1.0, 1.0))
    fx = (lon + np.pi) / (2 * np.pi) * W - 0.5
    fy = (np.pi / 2 - lat) / np.pi * H - 0.5
    x0 = np.floor(fx).astype(np.int64)
    y0 = np.floor(fy).astype(np.int64)
    tx = (fx - x0)[..., None]
    ty = (fy - y0)[..., None]
    x1, y1 = (x0 + 1) % W, np.clip(y0 + 1, 0, H - 1)
    x0, y0 = x0 % W, np.clip(y0, 0, H - 1)
    top = pano[y0, x0] * (1 - tx) + pano[y0, x1] * tx
    bot = pano[y1, x0] * (1 - tx) + pano[y1, x1] * tx
    return top * (1 - ty) + bot * ty


def perspective_view(pano, yaw, pitch, fov, w, h):
    ar = w / h
    fx = np.tan(math.radians(fov) / 2)
    sx = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 - 1
    sy = 1 - (np.arange(h, dtype=np.float32) + 0.5) / h * 2
    gx, gy = np.meshgrid(sx * fx * ar, sy * fx)
    d = np.stack([gx, gy, np.ones_like(gx)], -1)

    # positive pitch tilts the camera up, so the rays rotate by -pitch
    cy, sy_ = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    x, y, z = d[..., 0], d[..., 1] * cy + d[..., 2] * sy_, -d[..., 1] * sy_ + d[..., 2] * cy
    cz, sz = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    d = np.stack([x * cz + z * sz, y, -x * sz + z * cz], -1)
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    return sample_equirect(pano, d)


# Minecraft world axes: +x east, +y up, +z south.
# Each face is generated so that "up in the image" is up in the sky for the
# four side faces; top/bottom are laid out to join the north face seamlessly.
# A viewer stands inside the cube, so each face uses right = forward x up:
# facing north, east really is on your right.
#
# These orientations match the Nuit (formerly FabricSkyBoxes) renderer, read
# off its Utils.MATRIX4F_ROTATED_FACE: every side face has east/south/north
# on the right as below, top puts north at the bottom of the image and
# bottom puts north at the top. With that, all twelve cube edges line up -
# test_cube_seams.py checks it.
CUBE_FACES = {
    #         right (+u)           down (+v)            forward (centre)
    "north": ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
    "south": ((-1, 0, 0), (0, -1, 0), (0, 0, 1)),
    "east": ((0, 0, 1), (0, -1, 0), (1, 0, 0)),
    "west": ((0, 0, -1), (0, -1, 0), (-1, 0, 0)),
    "top": ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "bottom": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
}

# Nuit packs all six faces into one 3x2 atlas. Cell (column, row), read off
# Utils.TEXTURE_FACES:
#     bottom | top   | south
#     west   | north | east
ATLAS_CELLS = {
    "bottom": (0, 0), "top": (1, 0), "south": (2, 0),
    "west": (0, 1), "north": (1, 1), "east": (2, 1),
}
ATLAS_COLS, ATLAS_ROWS = 3, 2


def face_dirs(face, size, pixel_centres=True):
    """Unit direction for every pixel of one cube face.

    With ``pixel_centres`` the samples sit half a pixel inside the face, as
    a texture lookup does. Pass False to sample the face boundary itself,
    which is what lets two faces be compared along a shared edge.
    """
    right, down, fwd = (np.array(v, np.float32) for v in CUBE_FACES[face])
    if pixel_centres:
        s = (np.arange(size, dtype=np.float32) + 0.5) / size * 2 - 1
    else:
        s = np.linspace(-1.0, 1.0, size, dtype=np.float32)
    gx, gy = np.meshgrid(s, s)
    d = fwd + right * gx[..., None] + down * gy[..., None]
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


def cube_face(pano, face, size):
    return sample_equirect(pano, face_dirs(face, size))


def cube_atlas(pano, size):
    """The six faces packed into Nuit's 3x2 atlas."""
    out = np.zeros((ATLAS_ROWS * size, ATLAS_COLS * size, 3), np.float32)
    for face, (col, row) in ATLAS_CELLS.items():
        out[row * size:(row + 1) * size,
            col * size:(col + 1) * size] = cube_face(pano, face, size)
    return out


# --------------------------------------------------------------- concepts --

CONCEPTS: dict[str, dict] = {}

# 1 --------------------------------------------------------- BLOOD MOON ---
CONCEPTS["bloodmoon"] = {
    "title": "Bloedmaan",
    "blurb": "Zware bloedrode maan die door drijvende aswolken breekt.",
    "seed": 11,
    "zenith": (5, 3, 4),
    "horizon": (24, 7, 6),
    "ground": (3, 2, 2),
    "light_dir": direction(26, 8),
    "nebula": [
        # sparse blooms of red gas, mostly around the moon's quadrant
        {"seed": 101, "scale": 1.7, "warp": 0.45, "octaves": 4, "gain": 0.45,
         "lo": 0.46, "hi": 0.92, "power": 1.8, "strength": 0.55,
         "color": (86, 12, 10), "color2": (188, 52, 26),
         "coverage_scale": 0.85, "cov_lo": 0.44, "cov_hi": 0.80},
        # thin burning filaments
        {"seed": 131, "scale": 3.2, "warp": 0.35, "octaves": 3, "gain": 0.40,
         "ridged": True, "lo": 0.55, "hi": 0.93, "power": 2.0, "strength": 0.30,
         "color": (140, 24, 12), "color2": (255, 108, 46),
         "coverage_scale": 1.0, "cov_lo": 0.46, "cov_hi": 0.84},
        # ash deck drifting across the moon, rim lit by it
        {"seed": 171, "scale": 2.2, "warp": 0.40, "warp_octaves": 3,
         "octaves": 5, "gain": 0.50, "mode": "cloud", "over": True,
         "lo": 0.42, "hi": 0.80, "opacity": 0.80,
         "color": (26, 10, 9), "ambient": 0.05,
         "elev_centre": 0.14, "elev_spread": 0.30,
         "rim": 0.55, "rim_size": 34, "rim_color": (255, 98, 44)},
    ],
    "moons": [
        {"dir": direction(26, 8), "radius": 11.5, "color": (224, 58, 26),
         "brightness": 2.1, "glow": 0.22, "glow_size": 3.5,
         "glow_color": (150, 24, 12), "texture": 0.35, "texture_scale": 7.0,
         "maria": 0.45, "maria_scale": 2.2, "limb": 0.40, "seed": 8},
    ],
    "horizon_glow": {"color": (120, 20, 12), "height": 0.08, "strength": 0.38,
                     "patchy": True, "patch_scale": 1.6, "seed": 19},
    "stars": {"count": 4200, "brightness": 0.75, "falloff": 4.2, "size": 0.42,
              "warm": (255, 176, 128), "cool": (226, 186, 176), "warm_bias": 0.8,
              "bright_frac": 0.0035, "spikes": 0.55},
    "grade": {"exposure": 1.0, "saturation": 1.14},
    "preview": {"yaw": 8, "pitch": 20, "fov": 78},
}

# 2 ------------------------------------------------------ SHATTERED MOON ---
RING_AXIS = (-0.85, 0.35, -0.39)   # ring plane normal: a steep arc that
                                   # rises past the moon and over the zenith
MOON_DIR = direction(24, -24)
MOON_LIGHT = direction(16, -54)

CONCEPTS["shattered"] = {
    "title": "Verbrijzelde Maan",
    "blurb": "Reusachtige gebroken maan, puinring over de hemel, aswolken.",
    "seed": 23,
    "zenith": (3, 3, 6),
    "horizon": (9, 7, 14),
    "ground": (2, 2, 4),
    "light_dir": MOON_DIR,
    "nebula": [
        # bruised gas, desaturated - grim rather than pretty
        {"seed": 201, "scale": 1.4, "warp": 0.45, "octaves": 4, "gain": 0.45,
         "lo": 0.50, "hi": 0.93, "power": 2.0, "strength": 0.13,
         "color": (34, 18, 48), "color2": (98, 74, 128),
         "coverage_scale": 0.8, "cov_lo": 0.48, "cov_hi": 0.84},
        # dust strung along the ring, clumped
        {"seed": 231, "scale": 3.0, "warp": 0.30, "octaves": 4, "gain": 0.46,
         "ridged": True, "band_axis": RING_AXIS, "band_width": 0.042,
         "lo": 0.44, "hi": 0.92, "power": 1.6, "strength": 0.42,
         "color": (52, 46, 66), "color2": (170, 160, 190)},
        # gaps torn in that dust so the ring is broken, not tidy
        {"seed": 237, "scale": 5.0, "warp": 0.40, "octaves": 4, "mode": "mul",
         "band_axis": RING_AXIS, "band_width": 0.075,
         "lo": 0.48, "hi": 0.92, "strength": 0.60},
        # grain of unresolved rubble inside the ring
        {"seed": 261, "scale": 34.0, "octaves": 3, "gain": 0.55,
         "band_axis": RING_AXIS, "band_width": 0.045,
         "lo": 0.52, "hi": 0.86, "power": 1.6, "strength": 0.10,
         "color": (96, 92, 110), "color2": (196, 192, 214)},
        # high torn overcast, rim lit by the moon
        {"seed": 291, "scale": 1.9, "warp": 0.55, "octaves": 5, "gain": 0.5,
         "mode": "cloud", "over": True, "lo": 0.44, "hi": 0.80,
         "opacity": 0.94, "color": (12, 10, 17), "ambient": 0.075,
         "detail": 0.45, "detail_scale": 7.0,
         "elev_centre": 0.16, "elev_spread": 0.40,
         "rim": 0.46, "rim_size": 32, "rim_color": (176, 150, 226)},
        # a lower, heavier bank that eats the horizon
        {"seed": 297, "scale": 3.2, "warp": 0.45, "octaves": 5, "gain": 0.5,
         "mode": "cloud", "over": True, "lo": 0.44, "hi": 0.80,
         "opacity": 0.94, "color": (9, 8, 12), "ambient": 0.055,
         "detail": 0.50, "detail_scale": 9.0,
         "elev_centre": -0.02, "elev_spread": 0.17,
         "rim": 0.32, "rim_size": 42, "rim_color": (140, 118, 180)},
    ],
    "moons": [
        # it looms: close enough that the fissures are the main event
        {"dir": MOON_DIR, "radius": 18.0, "color": (104, 101, 120),
         "brightness": 0.78, "glow": 0.09, "glow_size": 1.6,
         "glow_color": (86, 74, 140), "texture": 0.18, "texture_scale": 9.0,
         "fine_texture": 0.10, "fine_scale": 38.0, "maria": 0.36,
         "bump": 0.52, "bump_scale": 9.0, "bump_octaves": 3, "bump_gain": 0.26,
         "irregular": 0.055, "cracks": 0.88, "crack_scale": 2.3,
         "crack_octaves": 1, "crack_glow_lo": 0.88,
         "crack_glow": 2.2, "crack_color": (152, 104, 255),
         "light": MOON_LIGHT, "ambient": 0.07, "seed": 3},
    ] + debris_field(
        MOON_DIR, 40, seed=4242, inner=20.0, outer=54.0,
        size=(0.16, 2.6), spread=1.4, flatten=0.5,
        color=(132, 128, 156), brightness=0.58, texture=0.22,
        texture_scale=9.0, fine_texture=0.14, fine_scale=30.0,
        bump=0.50, bump_scale=9.0, bump_octaves=3, bump_gain=0.28,
        light=MOON_LIGHT, ambient=0.045, limb=0.30,
    ) + debris_ring(
        RING_AXIS, 62, seed=909, tilt=4.0, size=(0.14, 2.2), gap=(96, 150),
        color=(126, 122, 150), brightness=0.55, texture=0.22,
        texture_scale=9.0, fine_texture=0.14, fine_scale=30.0,
        bump=0.50, bump_scale=9.0, bump_octaves=3, bump_gain=0.28,
        light=MOON_LIGHT, ambient=0.04, limb=0.30,
    ),
    # something is burning a long way off
    "horizon_glow": {"color": (104, 24, 14), "height": 0.05, "strength": 0.20,
                     "patchy": True, "patch_scale": 2.4, "patch_floor": 0.0,
                     "patch_lo": 0.58, "patch_hi": 0.80, "seed": 29},
    "stars": {"count": 5000, "brightness": 0.55, "falloff": 4.2, "size": 0.38,
              "warm": (214, 182, 150), "cool": (150, 166, 202), "warm_bias": 2.0,
              "bright_frac": 0.003, "spikes": 0.35},
    "grade": {"exposure": 1.75, "saturation": 0.88},
    "preview": {"yaw": -24, "pitch": 22, "fov": 80},
}

# 3 ----------------------------------------------------------- WRAITHLIGHT --
CONCEPTS["wraithlight"] = {
    "title": "Spooklicht",
    "blurb": "Grafgroene aurora-gordijnen onder een koude, bleke maan.",
    "seed": 37,
    "zenith": (4, 8, 12),
    "horizon": (9, 22, 26),
    "ground": (2, 5, 6),
    "light_dir": direction(46, 150),
    "nebula": [
        {"seed": 301, "scale": 1.6, "warp": 0.40, "octaves": 4, "gain": 0.45,
         "lo": 0.50, "hi": 0.92, "power": 1.8, "strength": 0.09,
         "color": (14, 44, 48), "color2": (56, 116, 104),
         "coverage_scale": 0.9, "cov_lo": 0.42, "cov_hi": 0.80},
        {"seed": 331, "scale": 3.0, "warp": 0.35, "octaves": 4, "mode": "mul",
         "lo": 0.48, "hi": 0.92, "strength": 0.45},
        # ragged mist bank under the curtains
        {"seed": 361, "scale": 2.4, "warp": 0.50, "octaves": 5, "gain": 0.5,
         "mode": "cloud", "over": True, "lo": 0.46, "hi": 0.84,
         "opacity": 0.72, "color": (8, 18, 20), "ambient": 0.06,
         "detail": 0.45, "detail_scale": 7.0,
         "elev_centre": 0.05, "elev_spread": 0.20,
         "rim": 0.18, "rim_size": 70, "rim_color": (150, 255, 210)},
    ],
    "aurora": {
        "ribbons": [
            {"seed": 341, "lat": 34, "amp": 16, "waves": 1.0, "phase": 0.0,
             "width": 10.0, "wobble": 6.0, "striation": 15.0, "strength": 0.30,
             "color": (150, 255, 208), "color2": (28, 150, 120)},
            {"seed": 347, "lat": 52, "amp": 12, "waves": 2.0, "phase": 2.1,
             "width": 8.0, "wobble": 5.0, "striation": 19.0, "strength": 0.17,
             "color": (186, 150, 255), "color2": (60, 190, 170)},
            {"seed": 353, "lat": 20, "amp": 9, "waves": 3.0, "phase": 4.2,
             "width": 6.0, "wobble": 4.0, "striation": 23.0, "strength": 0.11,
             "color": (128, 255, 190), "color2": (24, 110, 96)},
        ]
    },
    "moons": [
        {"dir": direction(46, 150), "radius": 5.5, "color": (218, 232, 236),
         "brightness": 1.05, "glow": 0.15, "glow_size": 5.5,
         "glow_color": (120, 176, 172), "texture": 0.42, "texture_scale": 9.0,
         "maria": 0.32,
         "light": direction(40, 176), "ambient": 0.12, "seed": 9},
    ],
    "horizon_glow": {"color": (30, 86, 78), "height": 0.10, "strength": 0.12,
                     "patchy": True, "patch_scale": 1.3, "seed": 39},
    "stars": {"count": 8000, "brightness": 0.95, "falloff": 3.6, "size": 0.42,
              "warm": (255, 226, 196), "cool": (186, 224, 255), "warm_bias": 2.8,
              "bright_frac": 0.0045, "spikes": 0.6},
    "grade": {"exposure": 1.22, "saturation": 1.08},
    "preview": {"yaw": 150, "pitch": 30, "fov": 84},
}

# 4 ---------------------------------------------------------- ASHEN EMBER --
CONCEPTS["ashfall"] = {
    "title": "Asregen",
    "blurb": "Rookdek, sintels in de lucht en een brandende horizon.",
    "seed": 53,
    "zenith": (7, 6, 7),
    "horizon": (34, 18, 11),
    "ground": (5, 4, 3),
    "light_dir": direction(6, -110),
    "nebula": [
        # smoke haze filling the upper sky
        {"seed": 401, "scale": 1.3, "warp": 0.50, "octaves": 4, "gain": 0.45,
         "lo": 0.48, "hi": 0.92, "power": 1.5, "strength": 0.10,
         "color": (44, 34, 32), "color2": (116, 88, 74)},
        # ember-lit underside of the smoke, banded near the horizon
        {"seed": 431, "scale": 2.2, "warp": 0.40, "octaves": 4, "gain": 0.45,
         "ridged": True, "lo": 0.56, "hi": 0.94, "power": 2.0, "strength": 0.16,
         "color": (150, 52, 12), "color2": (255, 146, 44),
         "elev_centre": 0.10, "elev_spread": 0.26,
         "coverage_scale": 1.1, "cov_lo": 0.42, "cov_hi": 0.80},
        # heavy overcast, the signature of this sky
        {"seed": 461, "scale": 1.8, "warp": 0.45, "octaves": 5, "gain": 0.5,
         "mode": "cloud", "over": True, "lo": 0.34, "hi": 0.76,
         "opacity": 0.88, "color": (22, 17, 16), "ambient": 0.05,
         "detail": 0.40, "detail_scale": 6.0,
         "elev_centre": 0.30, "elev_spread": 0.45,
         "rim": 0.35, "rim_size": 46, "rim_color": (255, 112, 32)},
    ],
    "moons": [
        {"dir": direction(34, -110), "radius": 8.0, "color": (196, 122, 62),
         "brightness": 1.25, "glow": 0.09, "glow_size": 5.0,
         "glow_color": (130, 62, 24), "texture": 0.50, "texture_scale": 6.0,
         "maria": 0.35, "limb": 0.6, "seed": 12},
    ],
    "horizon_glow": {"color": (205, 70, 16), "height": 0.11, "strength": 0.26,
                     "patchy": True, "patch_scale": 1.8, "seed": 57},
    "stars": {"count": 3000, "brightness": 0.55, "falloff": 4.5, "size": 0.42,
              "warm": (255, 198, 150), "cool": (224, 206, 190), "warm_bias": 0.6,
              "bright_frac": 0.003, "spikes": 0.4},
    "embers": {"count": 2000, "brightness": 1.15, "color": (255, 132, 40),
               "size": 0.40, "horizon_bias": 3.0},
    "grade": {"exposure": 1.18, "saturation": 1.15},
    "preview": {"yaw": -110, "pitch": 20, "fov": 82},
}

# 5 ---------------------------------------------------------- WITCHLIGHT ---
CONCEPTS["witchlight"] = {
    "title": "Heksenvuur",
    "blurb": "Gifgroene heksennevel met een groene en een bleke maan.",
    "seed": 71,
    "zenith": (4, 9, 8),
    "horizon": (10, 26, 20),
    "ground": (2, 6, 5),
    "light_dir": direction(33, 64),
    "nebula": [
        # swirling witchfire, the dominant feature
        {"seed": 501, "scale": 1.4, "warp": 0.60, "octaves": 4, "gain": 0.48,
         "ridged": True, "lo": 0.50, "hi": 0.93, "power": 1.9, "strength": 0.15,
         "color": (16, 86, 56), "color2": (132, 255, 172),
         "coverage_scale": 0.8, "cov_lo": 0.46, "cov_hi": 0.82},
        # cold cyan counter-glow
        {"seed": 541, "scale": 2.2, "warp": 0.40, "octaves": 4, "gain": 0.45,
         "lo": 0.52, "hi": 0.94, "power": 1.8, "strength": 0.10,
         "color": (14, 64, 80), "color2": (96, 220, 236),
         "coverage_scale": 1.0, "cov_lo": 0.44, "cov_hi": 0.82},
        {"seed": 571, "scale": 3.2, "warp": 0.45, "octaves": 4, "mode": "mul",
         "lo": 0.46, "hi": 0.92, "strength": 0.55},
        {"seed": 591, "scale": 2.6, "warp": 0.45, "octaves": 5, "gain": 0.5,
         "mode": "cloud", "over": True, "lo": 0.50, "hi": 0.86,
         "opacity": 0.60, "color": (8, 20, 16), "ambient": 0.05,
         "detail": 0.45, "detail_scale": 8.0,
         "elev_centre": 0.04, "elev_spread": 0.20,
         "rim": 0.18, "rim_size": 55, "rim_color": (140, 255, 176)},
    ],
    "moons": [
        {"dir": direction(33, 64), "radius": 9.5, "color": (146, 236, 150),
         "brightness": 1.05, "glow": 0.18, "glow_size": 5.0,
         "glow_color": (46, 168, 110), "texture": 0.50, "texture_scale": 7.5,
         "maria": 0.35,
         "light": direction(28, 88), "ambient": 0.14, "seed": 14},
        {"dir": direction(19, 96), "radius": 3.4, "color": (214, 226, 236),
         "brightness": 1.05, "glow": 0.08, "glow_size": 4.5,
         "glow_color": (86, 140, 160), "texture": 0.4, "texture_scale": 10.0,
         "light": direction(28, 88), "ambient": 0.10, "seed": 15},
    ],
    "horizon_glow": {"color": (36, 128, 78), "height": 0.10, "strength": 0.12,
                     "patchy": True, "patch_scale": 1.1, "seed": 73},
    "stars": {"count": 8500, "brightness": 0.95, "falloff": 3.6, "size": 0.42,
              "warm": (255, 228, 190), "cool": (190, 240, 232), "warm_bias": 3.0,
              "bright_frac": 0.005, "spikes": 0.6},
    "grade": {"exposure": 1.22, "saturation": 1.18},
    "preview": {"yaw": 76, "pitch": 24, "fov": 84},
}


# ------------------------------------------------------------------ main --

_FONTS = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def _font(size, bold=True):
    from PIL import ImageFont
    try:
        return ImageFont.truetype(_FONTS[0 if bold else 1], size)
    except OSError:
        return ImageFont.load_default()


def contact_card(cfg, index, view, pano):
    """One card per sky: the in-game look on top, the whole dome below."""
    from PIL import ImageDraw

    w = view.width
    strip = pano.resize((w, w // 4), Image.LANCZOS)
    bar = 58
    card = Image.new("RGB", (w, view.height + strip.height + bar + 6), (10, 10, 12))
    card.paste(view, (0, 0))
    card.paste(strip, (0, view.height + 6))

    dr = ImageDraw.Draw(card)
    y = view.height + strip.height + 6
    dr.rectangle([0, y, w, card.height], fill=(10, 10, 12))
    dr.text((18, y + 10), f"{index}.  {cfg['title']}", font=_font(26),
            fill=(236, 232, 240))
    dr.text((18, y + 36), cfg["blurb"], font=_font(16, bold=False),
            fill=(150, 146, 158))
    return card


def stats(name, img):
    """Luminance percentiles of the finished sky.

    A night sky should read mostly black: median around 0.05-0.12, p90 below
    ~0.45, and only the moon and the brightest gas near 1.0. Anything with a
    median past ~0.2 has turned into a coloured wall.
    """
    a = np.asarray(img, np.float32) / 255.0
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    top = a.max(axis=-1)
    p = np.percentile(lum, [50, 90, 99])
    q = np.percentile(top, [50, 90])
    print(f"  {name:11s} luma median {p[0]:.3f}  p90 {p[1]:.3f}  p99 {p[2]:.3f}"
          f"   |  chan median {q[0]:.3f}  p90 {q[1]:.3f}  max {top.max():.3f}")


def build(name, width, height, faces=False, face_size=512, outdir=None,
          preview_only=False, show_stats=False):
    cfg = CONCEPTS[name]
    outdir = outdir or os.path.join(ROOT, "previews")
    os.makedirs(outdir, exist_ok=True)

    hdr = render_panorama(cfg, width, height)
    add_stars(hdr, cfg)
    add_embers(hdr, cfg)

    pano = to_image(hdr, cfg, cfg["seed"])
    pv = cfg.get("preview", {"yaw": 0, "pitch": 18, "fov": 95})
    view = to_image(
        perspective_view(hdr, pv["yaw"], pv["pitch"], pv["fov"], width // 2,
                         int(width // 2 * 9 / 16)),
        cfg, cfg["seed"] + 1,
    )

    if show_stats:
        stats(name, pano)

    if preview_only:
        pano.save(os.path.join(outdir, f"{name}_panorama.jpg"), quality=92)
        view.save(os.path.join(outdir, f"{name}_view.jpg"), quality=93)
        index = list(CONCEPTS).index(name) + 1
        contact_card(cfg, index, view, pano).save(
            os.path.join(outdir, f"{index}_{name}.jpg"), quality=93)
    else:
        pano.save(os.path.join(outdir, f"{name}_panorama.png"))
        view.save(os.path.join(outdir, f"{name}_view.png"))

    if faces:
        fdir = os.path.join(outdir, name)
        os.makedirs(fdir, exist_ok=True)
        for face in CUBE_FACES:
            img = to_image(cube_face(hdr, face, face_size), cfg, cfg["seed"] + 2)
            img.save(os.path.join(fdir, f"{face}.png"))
    return hdr


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("concepts", nargs="*", default=[])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--preview", action="store_true",
                    help="preview resolution + jpg output")
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--faces", action="store_true", help="also write cube faces")
    ap.add_argument("--face-size", type=int, default=512)
    ap.add_argument("--out", default=None)
    ap.add_argument("--stats", action="store_true",
                    help="print luminance percentiles per sky")
    args = ap.parse_args()

    if args.list:
        for k, c in CONCEPTS.items():
            print(f"{k:12s} {c['title']:22s} {c['blurb']}")
        return

    names = args.concepts or list(CONCEPTS)
    width = args.width or (2048 if args.preview else 4096)
    for name in names:
        if name not in CONCEPTS:
            raise SystemExit(f"unknown concept {name!r}")
        print(f"rendering {name} at {width}x{width // 2} ...", flush=True)
        build(name, width, width // 2, faces=args.faces,
              face_size=args.face_size, outdir=args.out,
              preview_only=args.preview, show_stats=args.stats)
    print("done")


if __name__ == "__main__":
    main()
