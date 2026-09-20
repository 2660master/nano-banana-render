#!/usr/bin/env python3
"""Build the "breckie hill sky" Nuit skybox resource pack.

Pipeline: enhance the three source cut-outs -> generate a pink sky with a thick
cloud deck over the six cube faces -> composite the portraits onto the north and
south faces -> lay a foreground cloud bank over their feet -> write the 3x2
atlas, the Nuit JSON and a ready-to-use .zip.

Run:  python3 generator/build_pack.py
"""
import json
import os
import shutil
import zipfile

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PHOTOS = os.path.join(HERE, "source_photos")
PACK = os.path.join(ROOT, "breckie hill sky")
NAMESPACE = "breckiehill"

FACE = 1536                      # pixels per cube face
SEED = 20260919

# ---------------------------------------------------------------------------
# Nuit cube layout.  Values copied verbatim from Utils.TEXTURE_FACES in
# FlashyReese/nuit (26.3/dev): the atlas is a 3x2 grid laid out as
#   row 0: bottom | top   | south
#   row 1: west   | north | east
# Each entry is (name, minU, minV, maxU, maxV) in 0..1 atlas space.
# ---------------------------------------------------------------------------
FACES = [
    ("bottom", 0 / 3, 0 / 2, 1 / 3, 1 / 2),
    ("north", 1 / 3, 1 / 2, 2 / 3, 2 / 2),
    ("south", 2 / 3, 0 / 2, 3 / 3, 1 / 2),
    ("top", 1 / 3, 0 / 2, 2 / 3, 1 / 2),
    ("east", 2 / 3, 1 / 2, 3 / 3, 2 / 2),
    ("west", 0 / 3, 1 / 2, 1 / 3, 2 / 2),
]


def _rx(deg):
    a = np.radians(deg)
    return np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])


def _ry(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])


def _rz(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])


# Utils.MATRIX4F_ROTATED_FACE, same order as FACES.  JOML post-multiplies, so
# `new Matrix4f().rotateX(-90).rotateY(180)` is Rx(-90) @ Ry(180).
MATRICES = [
    np.eye(3),
    _rx(90),
    _rx(-90) @ _ry(180),
    _rx(180),
    _rz(90) @ _ry(-90),
    _rz(-90) @ _ry(90),
]

# The untransformed quad lives on the y = -100 plane.  These are the four
# corners the renderer pins to (minU,minV), (minU,maxV), (maxU,maxV), (maxU,minV).
QUAD = np.array([
    [-100.0, -100.0, -100.0],   # s=0, t=0   (cell top-left)
    [-100.0, -100.0, 100.0],    # s=0, t=1   (cell bottom-left)
    [100.0, -100.0, 100.0],     # s=1, t=1   (cell bottom-right)
    [100.0, -100.0, -100.0],    # s=1, t=0   (cell top-right)
])


def face_corners(i):
    """World-space positions of the four texture corners of face `i`."""
    return QUAD @ MATRICES[i].T


def face_directions(i, size):
    """Unit view direction for every pixel of face `i`, in atlas orientation."""
    a, b, _c, d = face_corners(i)
    t, s = np.meshgrid(
        (np.arange(size) + 0.5) / size,
        (np.arange(size) + 0.5) / size,
        indexing="ij",
    )
    p = a + s[..., None] * (d - a) + t[..., None] * (b - a)
    return (p / np.linalg.norm(p, axis=-1, keepdims=True)).astype(np.float32)


def assert_upright(i):
    """Fail loudly if a face we paste portraits onto is rotated or mirrored.

    A mirrored face would flip the necklace lettering, so this is worth
    checking rather than assuming.
    """
    a, b, c, d = face_corners(i)
    fwd = (a + c) / 2
    fwd = fwd / np.linalg.norm(fwd)
    up = np.array([0.0, 1.0, 0.0])
    right = np.cross(fwd, up)
    right = right / np.linalg.norm(right)
    img_x = (d - a) / np.linalg.norm(d - a)      # texture +x
    img_y = (b - a) / np.linalg.norm(b - a)      # texture +y (downwards)
    assert np.dot(img_x, right) > 0.99, f"face {i} is mirrored"
    assert np.dot(img_y, -up) > 0.99, f"face {i} is rotated"


# ---------------------------------------------------------------------------
# Noise
# ---------------------------------------------------------------------------
GRID = 128


def _lattice(seed):
    rng = np.random.default_rng(seed)
    return rng.random((GRID, GRID, GRID), dtype=np.float32)


def value_noise2(u, v, lat, layer):
    """Bilinearly interpolated 2D value noise, read off one slice of `lat`."""
    iu = np.floor(u).astype(np.int32)
    iv = np.floor(v).astype(np.int32)
    fu = (u - iu).astype(np.float32)
    fv = (v - iv).astype(np.float32)
    fu = fu * fu * (3.0 - 2.0 * fu)
    fv = fv * fv * (3.0 - 2.0 * fv)
    u0, u1 = np.mod(iu, GRID), np.mod(iu + 1, GRID)
    v0, v1 = np.mod(iv, GRID), np.mod(iv + 1, GRID)
    sl = lat[layer % GRID]
    c0 = sl[u0, v0] * (1 - fu) + sl[u1, v0] * fu
    c1 = sl[u0, v1] * (1 - fu) + sl[u1, v1] * fu
    return c0 * (1 - fv) + c1 * fv


# Rotating the domain between octaves hides the axis-aligned lattice.
_ROT2 = np.array([[0.8660, -0.5000], [0.5000, 0.8660]], dtype=np.float32)


def fbm2(u, v, lat, octaves=6, gain=0.5, detail=None, layer=0, billow=False):
    """Fractal 2D noise.

    `detail` is a per-pixel 0..1 mask that fades the finer octaves out. Near the
    horizon a cloud deck compresses towards infinity, so the high frequencies
    land below one pixel and would alias into moire without this.
    """
    total = np.zeros(u.shape, dtype=np.float32)
    amp, norm = 1.0, 0.0
    uu, vv = u.astype(np.float32), v.astype(np.float32)
    for k in range(octaves):
        n = value_noise2(uu, vv, lat, layer + k * 13)
        if billow and k > 1:
            n = 1.0 - np.abs(2.0 * n - 1.0)
        if detail is not None and k > 0:
            # Octave k is only allowed once the deck is far enough from the
            # horizon for its cells to stay above pixel size. Faded octaves are
            # replaced by their own mean so the overall level does not drift.
            w = smoothstep(0.013 * (2.0 ** k), 0.030 * (2.0 ** k), detail)
            n = w * n + (1.0 - w) * 0.5
        total += amp * n
        norm += amp
        amp *= gain
        uu, vv = (uu * _ROT2[0, 0] + vv * _ROT2[0, 1]) * 2.02, \
                 (uu * _ROT2[1, 0] + vv * _ROT2[1, 1]) * 2.02
    return total / max(norm, 1e-6)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------------------
# Colour
# ---------------------------------------------------------------------------
def ramp(t, stops):
    """Piecewise-linear colour ramp; `stops` is [(pos, (r,g,b)), ...] ascending."""
    pos = np.array([s[0] for s in stops], dtype=np.float32)
    col = np.array([s[1] for s in stops], dtype=np.float32)
    out = np.empty(t.shape + (3,), dtype=np.float32)
    for ch in range(3):
        out[..., ch] = np.interp(t, pos, col[:, ch])
    return out


SKY_STOPS = [
    (-1.00, (226, 132, 184)),   # straight down, under the deck
    (-0.45, (244, 166, 200)),
    (-0.12, (254, 204, 218)),
    (0.00, (255, 212, 214)),    # horizon, warm and pale
    (0.14, (255, 198, 218)),
    (0.38, (250, 156, 202)),
    (0.62, (238, 126, 190)),
    (0.82, (222, 104, 180)),
    (1.00, (206, 96, 176)),     # zenith stays rose
]

# Lit tops are near-white, undersides fall to a dusty rose rather than to grey.
CLOUD_RAMP = [
    (0.00, (198, 106, 166)),
    (0.18, (220, 132, 186)),
    (0.42, (240, 154, 200)),
    (0.66, (253, 200, 226)),
    (0.84, (255, 232, 242)),
    (1.00, (255, 253, 254)),
]

LIGHT = np.array([0.46, 0.38, -0.80])
LIGHT = (LIGHT / np.linalg.norm(LIGHT)).astype(np.float32)


RMAX = 130.0         # soft cap, in noise cells, on how far we sample the deck
DETAIL_GAIN = 25.0   # maps angular cell size onto fbm2's octave-fade thresholds


def cloud_deck(dirs, lats, above, cells, seed_off, cover=0.45, gain=0.44,
               octaves=5, warp=0.9, light_step=0.50, band=None, haze=(0.02, 0.22)):
    """One horizontal deck of thick pink clouds, as (alpha, rgb).

    A view ray is intersected with a horizontal plane, which is what gives real
    cloud decks their convergence towards the horizon. Plane height and noise
    scale only ever appear as a product, so `cells` folds them into a single
    knob: roughly how many cloud cells fit between the viewer and the point of
    the deck directly overhead.
    """
    base, warp_lat, cov_lat = lats
    y = dirs[..., 1]
    facing = ((y > 0) if above else (y < 0)).astype(np.float32)
    ay = np.maximum(np.abs(y), 1e-4).astype(np.float32)

    t = cells / ay
    u = dirs[..., 0] * t
    v = dirs[..., 2] * t
    r = np.sqrt(u * u + v * v) + 1e-6
    squash = RMAX * np.tanh(r / RMAX) / r     # keeps the far field finite
    u = (u * squash + seed_off).astype(np.float32)
    v = (v * squash + seed_off * 0.7).astype(np.float32)

    # Angular size of one noise cell; drives how much detail can survive.
    detail = (ay * ay / cells * DETAIL_GAIN).astype(np.float32)

    # Domain warp gives the banks billowy, non-circular outlines.
    wu = fbm2(u * 0.30 + 3.1, v * 0.30 + 7.7, warp_lat, octaves=3, detail=detail)
    wv = fbm2(u * 0.30 + 19.3, v * 0.30 + 2.9, warp_lat, octaves=3, detail=detail)
    u = u + (wu - 0.5) * warp
    v = v + (wv - 0.5) * warp

    density = fbm2(u, v, base, octaves=octaves, gain=gain, detail=detail)
    coverage = fbm2(u * 0.19 + 41.0, v * 0.19 + 13.0, cov_lat, octaves=3, detail=detail)

    # Low threshold => "superveel" cloud; coverage noise still carves open gaps.
    thresh = cover - 0.14 * coverage
    alpha = smoothstep(thresh - 0.008, thresh + 0.055, density)   # defined but not crunchy

    # Treat the density above the threshold as the height of a billowing dome,
    # then light its surface normal. Sampling the neighbours in deck space
    # rather than in screen space keeps the shading consistent on every face.
    def dome(d):
        return 1.0 - np.exp(-np.clip(d - thresh, 0.0, None) / 0.20)

    eps = light_step * 0.22
    h = dome(density)
    hu = dome(fbm2(u + eps, v, base, octaves=octaves, gain=gain, detail=detail))
    hv = dome(fbm2(u, v + eps, base, octaves=octaves, gain=gain, detail=detail))

    relief = 2.0 * cells
    nx = -(hu - h) / eps * relief
    nz = -(hv - h) / eps * relief
    inv = 1.0 / np.sqrt(nx * nx + nz * nz + 1.0)
    # Deck space (u, v) maps to world (x, z); the dome's own axis is world up.
    ndl = np.clip((nx * LIGHT[0] + nz * LIGHT[2] + LIGHT[1]) * inv, 0.0, 1.0)

    # Thin edges scatter light through, so lift them back up.
    powder = (1.0 - h) ** 2
    lit = np.clip(0.16 + 0.76 * ndl + 0.14 * powder, 0.0, 1.0)
    rgb = ramp(lit, CLOUD_RAMP)

    alpha = alpha * smoothstep(haze[0], haze[1], ay) * facing
    if band is not None:
        # Ragged edge: the band boundary is nudged by the cloud density itself
        # so it never reads as a straight horizontal cut.
        lo, hi = band
        alpha = alpha * smoothstep(lo, hi, y + (density - 0.5) * 0.09)
    return np.clip(alpha, 0, 1).astype(np.float32), rgb


def render_face(dirs, lats):
    """Pink gradient sky, a high ceiling of cloud and a sea of cloud below."""
    y = dirs[..., 1]
    sky = ramp(y, SKY_STOPS)

    # Gentle bloom along the horizon, brightest towards north, so the portraits
    # land against a clean patch rather than a busy one.
    horizon = np.exp(-((y / 0.30) ** 2)).astype(np.float32)
    northness = np.clip(-dirs[..., 2], 0.0, 1.0) ** 2
    sky += (horizon * (4.0 + 14.0 * northness))[..., None] * np.array(
        [1.0, 0.88, 0.93], dtype=np.float32)

    out = sky
    # Ceiling above, then the sea the portraits will stand on.
    a, rgb = cloud_deck(dirs, lats, True, 3.2, 0.0, cover=0.455,
                        haze=(0.03, 0.30))
    out = out * (1.0 - a[..., None]) + rgb * a[..., None]

    a, rgb = cloud_deck(dirs, lats, False, 4.6, 61.0, cover=0.375,
                        haze=(0.03, 0.26))
    out = out * (1.0 - a[..., None]) + rgb * a[..., None]
    return np.clip(out, 0, 255)


def foreground_bank(dirs, lats):
    """The near cloud puffs the portraits stand among, as an RGBA overlay.

    Restricted to a latitude band just below the horizon so it wraps the whole
    sky continuously instead of stopping at a face edge, and so it covers their
    feet without swallowing them.
    """
    return cloud_deck(dirs, lats, False, 2.4, 205.0, cover=0.44, octaves=5,
                      warp=1.1, light_step=0.55, haze=(0.02, 0.12),
                      band=(-0.14, -0.36))


# ---------------------------------------------------------------------------
# Portraits
# ---------------------------------------------------------------------------
def bleed_edges(rgb, alpha, rounds=14):
    """Grow opaque colour into transparent pixels.

    The RGB values hiding under alpha=0 are garbage; without this the resampler
    drags them in and rims the cut-out with a dark halo.
    """
    rgb = rgb.astype(np.float32)
    known = (alpha > 8).astype(np.float32)
    for _ in range(rounds):
        if known.min() > 0.5:
            break
        acc = np.zeros_like(rgb)
        wsum = np.zeros_like(known)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            w = np.roll(np.roll(known, dy, 0), dx, 1)
            acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * w[..., None]
            wsum += w
        fill = wsum > 0
        rgb = np.where(fill[..., None] & (known[..., None] < 0.5),
                       acc / np.maximum(wsum, 1e-6)[..., None], rgb)
        known = np.clip(known + fill.astype(np.float32), 0, 1)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def enhance_portrait(name, scale=3):
    """Trim to the subject, upscale, recover detail, tidy the matte, grade."""
    im = Image.open(os.path.join(PHOTOS, name)).convert("RGBA")
    arr = np.array(im)

    a = arr[..., 3]
    ys, xs = np.where(a > 16)
    pad = 2
    arr = arr[max(0, ys.min() - pad):ys.max() + 1 + pad,
              max(0, xs.min() - pad):xs.max() + 1 + pad]

    colour = Image.fromarray(bleed_edges(arr[..., :3], arr[..., 3]), "RGB")
    alpha = Image.fromarray(arr[..., 3], "L")

    size = (colour.width * scale, colour.height * scale)
    colour = colour.resize(size, Image.LANCZOS)
    alpha = alpha.resize(size, Image.LANCZOS)

    # Mild on purpose: the sources are ~400px wide and hard sharpening just
    # amplifies compression artefacts.
    colour = colour.filter(ImageFilter.UnsharpMask(radius=2.2, percent=110, threshold=3))
    colour = colour.filter(ImageFilter.UnsharpMask(radius=6.0, percent=38, threshold=4))
    colour = ImageEnhance.Contrast(colour).enhance(1.07)
    colour = ImageEnhance.Color(colour).enhance(1.08)
    colour = ImageEnhance.Brightness(colour).enhance(1.02)

    # A touch of the sky's pink bounced back, so she belongs in the scene.
    cv = np.array(colour).astype(np.float32)
    cv = cv * 0.93 + np.array([255, 206, 226], dtype=np.float32) * 0.07
    colour = Image.fromarray(np.clip(cv, 0, 255).astype(np.uint8), "RGB")

    # Tighten the matte: crush the near-transparent fringe, keep a soft edge.
    av = np.array(alpha).astype(np.float32) / 255.0
    av = np.clip((av - 0.12) / 0.76, 0, 1)
    av = av * av * (3 - 2 * av)

    # Dissolve the bottom of the cut-out so the hard crop never shows; the
    # foreground cloud bank covers the rest.
    h = av.shape[0]
    fade = np.ones(h, dtype=np.float32)
    start = int(h * 0.84)
    fade[start:] = np.linspace(1.0, 0.0, h - start) ** 1.4
    av = av * fade[:, None]

    alpha = Image.fromarray((av * 255).astype(np.uint8), "L")
    return Image.merge("RGBA", (*colour.split(), alpha))


def fit_height(sprite, px):
    w = max(1, round(sprite.width * px / sprite.height))
    return sprite.resize((w, px), Image.LANCZOS)


def paste_portrait(face, sprite, cx, feet_y, glow=1.0):
    """Composite one portrait onto a face, with a soft lift behind her.

    `cx` and `feet_y` are 0..1 fractions of the face; `feet_y` is where the
    bottom of the sprite lands.
    """
    size = face.width
    x = int(cx * size - sprite.width / 2)
    y = int(feet_y * size - sprite.height)

    if glow > 0:
        # Wide and weak: a lift in the clouds behind her, not a spotlight.
        gr = int(max(sprite.width, sprite.height) * 1.35)
        yy, xx = np.mgrid[-gr:gr, -gr:gr].astype(np.float32)
        d = np.sqrt((xx / gr) ** 2 + (yy / gr) ** 2)
        g = np.clip(1.0 - d, 0, 1) ** 2.6
        halo = np.zeros((2 * gr, 2 * gr, 4), dtype=np.uint8)
        halo[..., 0] = 255
        halo[..., 1] = 236
        halo[..., 2] = 245
        halo[..., 3] = (g * 62 * glow).astype(np.uint8)
        face.alpha_composite(Image.fromarray(halo, "RGBA"),
                             (x + sprite.width // 2 - gr,
                              y + int(sprite.height * 0.46) - gr))

    face.alpha_composite(sprite, (x, y))


# ---------------------------------------------------------------------------
# Pack assembly
# ---------------------------------------------------------------------------
def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def main():
    print("enhancing portraits ...")
    portraits = [enhance_portrait(f"{i}.png") for i in (1, 2, 3)]
    for i, p in enumerate(portraits, 1):
        print(f"  {i}.png -> {p.size}")

    lats = (_lattice(SEED), _lattice(SEED + 1), _lattice(SEED + 2))

    north_i = next(i for i, f in enumerate(FACES) if f[0] == "north")
    south_i = next(i for i, f in enumerate(FACES) if f[0] == "south")
    assert_upright(north_i)
    assert_upright(south_i)

    atlas = Image.new("RGB", (FACE * 3, FACE * 2), (0, 0, 0))
    rendered = {}
    for idx, (name, min_u, min_v, _u, _v) in enumerate(FACES):
        print(f"rendering {name} ...")
        dirs = face_directions(idx, FACE)
        face = Image.fromarray(render_face(dirs, lats).astype(np.uint8), "RGB").convert("RGBA")

        # One portrait in front of the player, two behind.
        if idx == north_i:
            paste_portrait(face, fit_height(portraits[0], int(FACE * 0.46)), 0.50, 0.62)
        elif idx == south_i:
            # Back one first so the front one overlaps it.
            paste_portrait(face, fit_height(portraits[2], int(FACE * 0.34)), 0.670, 0.645, glow=0.7)
            paste_portrait(face, fit_height(portraits[1], int(FACE * 0.39)), 0.355, 0.640, glow=0.85)

        # Cloud bank in front of everything, hiding the crop at their feet.
        a, rgb = foreground_bank(dirs, lats)
        overlay = np.concatenate([rgb, (a * 255)[..., None]], axis=-1)
        face.alpha_composite(Image.fromarray(np.clip(overlay, 0, 255).astype(np.uint8), "RGBA"))

        rendered[name] = face
        atlas.paste(face.convert("RGB"), (int(min_u * FACE * 3), int(min_v * FACE * 2)))

    # --- files -------------------------------------------------------------
    if os.path.isdir(PACK):
        shutil.rmtree(PACK)
    tex_dir = os.path.join(PACK, "assets", NAMESPACE, "textures", "sky")
    os.makedirs(tex_dir, exist_ok=True)

    atlas_path = os.path.join(tex_dir, "breckie_hill_sky.png")
    atlas.save(atlas_path, optimize=True)
    print(f"atlas -> {atlas_path} ({os.path.getsize(atlas_path)/1e6:.1f} MB)")

    write_json(os.path.join(PACK, "assets", "nuit", "sky", "breckie_hill_sky.json"), {
        "schemaVersion": 1,
        "type": "square-textured",
        "texture": f"{NAMESPACE}:textures/sky/breckie_hill_sky.png",
        "blend": {"type": "normal"},
        "properties": {
            "layer": 0,
            "sunSkyTint": False,
            "visibleUnderwater": False,
            "transitionInDuration": 20,
            "transitionOutDuration": 20,
            "rotation": {
                "skyboxRotation": True,
                "speed": 0.0,
                "duration": 24000,
            },
            "fog": {
                "modifyColors": True,
                "red": 1.0,
                "green": 0.73,
                "blue": 0.85,
                "modifyDensity": False,
                "density": 0.0,
                "showInDenseFog": False,
            },
        },
        "conditions": {
            "dimensions": {"excludes": False, "entries": ["minecraft:overworld"]},
        },
    })

    write_json(os.path.join(PACK, "pack.mcmeta"), {
        "pack": {
            "pack_format": 64,
            "supported_formats": {"min_inclusive": 9, "max_inclusive": 99},
            "description": "\u00a7dmade by 2660master",
        },
    })

    with open(os.path.join(PACK, "credits.txt"), "w", encoding="utf-8") as fh:
        fh.write("made by 2660master\n"
                 "add .master.26 on dc for your custom packs\n")

    # Pack icon, from the supplied artwork. Minecraft wants a square; flatten
    # any transparency onto white rather than letting it go black.
    icon = Image.open(os.path.join(HERE, "pack_icon.png")).convert("RGBA")
    side = min(icon.size)
    icon = icon.crop(((icon.width - side) // 2, (icon.height - side) // 2,
                      (icon.width + side) // 2, (icon.height + side) // 2))
    flat = Image.new("RGB", icon.size, (255, 255, 255))
    flat.paste(icon, mask=icon.split()[3])
    flat.resize((512, 512), Image.LANCZOS).save(
        os.path.join(PACK, "pack.png"), optimize=True)

    zip_path = os.path.join(ROOT, "breckie hill sky.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for base, _dirs, files in os.walk(PACK):
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.relpath(full, PACK))
    print(f"zip   -> {zip_path} ({os.path.getsize(zip_path)/1e6:.1f} MB)")

    # Flat previews, handy for eyeballing without launching the game.
    prev = os.path.join(HERE, "preview")
    os.makedirs(prev, exist_ok=True)
    for name in ("north", "south", "top", "east", "bottom", "west"):
        rendered[name].convert("RGB").resize((640, 640), Image.LANCZOS).save(
            os.path.join(prev, f"{name}.png"))
    atlas.resize((1536, 1024), Image.LANCZOS).save(os.path.join(prev, "atlas.png"))


if __name__ == "__main__":
    main()
