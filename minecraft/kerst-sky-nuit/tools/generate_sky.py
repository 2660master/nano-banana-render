#!/usr/bin/env python3
"""Build the two Christmas skybox resource packs for the Nuit mod (MC 1.21.11).

Usage::

    python3 tools/generate_sky.py            # full quality (1024 px per face)
    python3 tools/generate_sky.py --quick    # fast preview pass
    python3 tools/generate_sky.py --only a   # just one variant

Everything is painted procedurally in direction space, so the six cube faces of
the 3x2 Nuit atlas line up seamlessly.  No third-party libraries are used.
"""

import argparse
import json
import math
import os
import random
import shutil
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import skylib as S
from skylib import (
    DEG,
    FACES,
    CubeSampler,
    FaceBuffer,
    angle_delta,
    azimuth_elevation,
    clamp,
    cross,
    direction,
    dot,
    encode_rows,
    fbm3,
    mix,
    mix3,
    normalize,
    smoothstep,
    tangent_basis,
    vnoise3,
    write_png,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_FORMAT = 75  # Minecraft Java 1.21.11
NAMESPACE = "kerstsky"


# --------------------------------------------------------------------------
# colour helpers
# --------------------------------------------------------------------------


def srgb(hex_code):
    """'#rrggbb' -> linear-light RGB triple."""
    hex_code = hex_code.lstrip("#")
    out = []
    for i in range(3):
        c = int(hex_code[i * 2 : i * 2 + 2], 16) / 255.0
        out.append(((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92)
    return tuple(out)


def ramp(stops, x):
    """Piecewise-smooth colour ramp; ``stops`` is [(position, colour), ...]."""
    if x <= stops[0][0]:
        return stops[0][1]
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if x <= p1:
            t = (x - p0) / (p1 - p0)
            t = t * t * (3.0 - 2.0 * t)
            return mix3(c0, c1, t)
    return stops[-1][1]


# --------------------------------------------------------------------------
# shared sky ingredients
# --------------------------------------------------------------------------


def horizon_band(el, up_width, down_width):
    """Glow centred on the horizon that falls off in *both* directions."""
    width = up_width if el >= 0.0 else down_width
    t = el / width
    if t * t > 12.0:
        return 0.0
    return math.exp(-t * t)


def milky_way(d, pole, width, seed, warp=0.0):
    """Soft dust band around the great circle whose pole is ``pole``."""
    x = dot(d, pole)
    if warp:
        x += warp * (vnoise3(d[0] * 1.7, d[1] * 1.7, d[2] * 1.7, seed + 9) - 0.5)
    q = x / width
    if q * q > 9.0:
        return 0.0
    falloff = math.exp(-q * q)
    # a concentrated core inside the broad band, like the real galactic bulge
    core = falloff * 0.72 + falloff ** 3 * 0.55
    mottle = fbm3(d[0] * 3.4, d[1] * 3.4, d[2] * 3.4, 4, seed)
    dust = fbm3(d[0] * 6.1 + 11.0, d[1] * 6.1, d[2] * 6.1, 3, seed + 31)
    return core * clamp(0.08 + 1.55 * mottle * mottle) * clamp(1.2 - 1.05 * dust)


class Aurora:
    """A set of hanging curtains, expressed in azimuth/elevation."""

    def __init__(self, ribbons, seed, low=None, mid=None, high=None):
        self.ribbons = ribbons
        self.seed = seed
        self.low = low or srgb("#2ff08d")
        self.mid = mid or srgb("#39d6c6")
        self.high = high or srgb("#ff3d63")

    def intensity(self, az, el):
        """Returns (strength, height_fraction) for the brightest ribbon here."""
        total = 0.0
        height = 0.0
        for center_az, half_width, top, strength, phase in self.ribbons:
            dx = angle_delta(az, center_az)
            if abs(dx) >= half_width:
                continue
            env = smoothstep(half_width, half_width * 0.45, abs(dx))
            # three scales: where a curtain hangs at all, its folds, its threads
            sheet = vnoise3(dx * 0.035 + phase, 0.0, 0.0, self.seed)
            fold = vnoise3(dx * 0.16 + phase * 2.0, 0.0, 0.0, self.seed + 5)
            presence = clamp((sheet * 0.68 + fold * 0.46) - 0.20) * 1.75
            if presence <= 0.02:
                continue
            top_here = top * (0.55 + 0.85 * sheet) * (0.78 + 0.42 * fold)
            if top_here < 4.0 or el >= top_here or el < -3.0:
                continue
            v = clamp(el / top_here)
            profile = (1.0 - v) ** 1.5 * smoothstep(0.0, 0.14, v)
            thread = vnoise3(dx * 0.62 + phase * 3.0, v * 0.8, 0.0, self.seed + 11)
            value = env * presence * profile * (0.5 + 0.8 * thread) * strength
            if value > 0.0:
                total += value
                if value > height:
                    height = v
        return total, height

    def color(self, height_fraction):
        if height_fraction < 0.40:
            return mix3(self.low, self.mid, smoothstep(0.08, 0.40, height_fraction))
        return mix3(self.mid, self.high, smoothstep(0.40, 0.82, height_fraction))


def four_point_star(d, center, right, up, core_deg, arm_long, arm_short, limit_deg,
                    halo_gain=0.30, halo_deg=1.0):
    """Classic cross-flare shape; returns an intensity >= 0.

    The halo uses a power-law tail rather than an exponential one: on a sky this
    dark an exponential drops off fast enough that the eye reads its edge as a
    disc, while ``1 / (1 + r^2)^1.4`` keeps fading long past the point of being
    visible. ``halo_deg`` is the glow radius in degrees.
    """
    depth = dot(d, center)
    if depth <= 0.0:
        return 0.0
    ang = math.degrees(math.acos(clamp(depth, -1.0, 1.0)))
    if ang >= limit_deg:
        return 0.0
    u = math.degrees(math.asin(clamp(dot(d, right), -1.0, 1.0)))
    w = math.degrees(math.asin(clamp(dot(d, up), -1.0, 1.0)))

    core = math.exp(-((ang / core_deg) ** 2)) * 2.4
    halo = halo_gain / (1.0 + (ang / halo_deg) ** 2) ** 1.4 if halo_gain > 0.0 else 0.0

    au, aw = abs(u), abs(w)
    # the vertical arm reaches further downwards, like a comet tail
    down_scale = 1.9 if w < 0.0 else 1.0
    vert = math.exp(-((au / (core_deg * 0.62)) ** 1.25)) * math.exp(
        -((aw / (arm_long * down_scale)) ** 2.0)
    )
    horiz = math.exp(-((aw / (core_deg * 0.62)) ** 1.25)) * math.exp(
        -((au / arm_short) ** 2.0)
    )
    diag = 0.0
    for sx, sy in ((1, 1), (1, -1)):
        p = (u * sx + w * sy) * 0.7071
        q = (u * sy * -1 + w * sx) * 0.7071
        diag += math.exp(-((abs(q) / (core_deg * 0.5)) ** 1.4)) * math.exp(
            -((abs(p) / (arm_short * 0.62)) ** 2.0)
        )
    return core + halo + 1.05 * vert + 0.95 * horiz + 0.34 * diag


def draw_arc(buffer, a, b, color, intensity, radius_px, samples=None):
    """Faint line between two sky directions (used for constellation figures).

    Sampling density follows the texture resolution so the line never beads.
    """
    ang = math.degrees(math.acos(clamp(dot(a, b), -1.0, 1.0)))
    if samples is None:
        samples = max(4, int(ang * (buffer.size / 90.0) / 0.7))
    for i in range(samples + 1):
        t = i / samples
        d = normalize(
            (
                a[0] + (b[0] - a[0]) * t,
                a[1] + (b[1] - a[1]) * t,
                a[2] + (b[2] - a[2]) * t,
            )
        )
        buffer.splat(d, radius_px, color, intensity, falloff=1.4)


def garland_path(az0, el0, az1, el1, sag, steps):
    """Catenary-ish arc between two sky points."""
    points = []
    for i in range(steps + 1):
        t = i / steps
        az = mix(az0, az1, t)
        el = mix(el0, el1, t) - sag * math.sin(math.pi * t)
        points.append(direction(az, el))
    return points


# --------------------------------------------------------------------------
# variant A - "Stille Nacht"
# --------------------------------------------------------------------------


class StilleNacht:
    key = "a"
    folder = "variant-a-stille-nacht"
    slug = "stille_nacht"
    title = "Kerst Sky A - Stille Nacht"
    description = "Diepblauwe kerstnacht met noorderlicht in groen en rood, en de Kerstster boven de zuidelijke horizon."
    seed = 20251224

    sky_stops = [
        (-25.0, srgb("#03050c")),
        (-6.0, srgb("#071022")),
        (0.0, srgb("#1b4870")),
        (3.5, srgb("#17395e")),
        (10.0, srgb("#112a4e")),
        (24.0, srgb("#0d1e3e")),
        (48.0, srgb("#08132c")),
        (90.0, srgb("#05091d")),
    ]
    star_color_pool = [
        (srgb("#dce7ff"), 0.46),
        (srgb("#ffffff"), 0.24),
        (srgb("#a8c4ff"), 0.16),
        (srgb("#ffe6c4"), 0.10),
        (srgb("#ffd0a0"), 0.04),
    ]
    star_count = 4200

    hero = direction(176.0, 39.0)
    hero_color = srgb("#fff3d6")
    preview_az = 176.0
    preview_el = 15.0

    def __init__(self):
        self.aurora = Aurora(
            ribbons=[
                # (azimuth centre, half width, top elevation, strength, phase)
                (2.0, 78.0, 44.0, 1.00, 0.0),
                (330.0, 52.0, 31.0, 0.72, 13.7),
                (46.0, 46.0, 26.0, 0.60, 31.2),
                (286.0, 34.0, 20.0, 0.34, 57.9),
            ],
            seed=self.seed,
            low=srgb("#2bf08a"),
            mid=srgb("#3ad3cd"),
            high=srgb("#ff3a60"),
        )
        self.band_pole = normalize(direction(104.0, 56.0))
        self.glow_color = srgb("#8fc8ff")

    def field(self, d):
        az, el = azimuth_elevation(d)
        r, g, b = ramp(self.sky_stops, el)

        # cold horizon bloom, hugging the horizon line from both sides and
        # breathing a little around the compass so it is not a painted stripe
        vary = 0.48 + 0.52 * vnoise3(az * 0.018, 0.0, 0.0, self.seed + 3)
        bloom = horizon_band(el, 7.0, 2.6) * 0.14 * vary
        gc = self.glow_color
        r += gc[0] * bloom
        g += gc[1] * bloom
        b += gc[2] * bloom

        # milky way
        band = milky_way(d, self.band_pole, 0.17, self.seed, warp=0.05)
        if band > 0.0:
            r += 0.050 * band
            g += 0.078 * band
            b += 0.185 * band

        # high, thin cirrus so the sky is not perfectly flat
        veil = fbm3(d[0] * 2.1, d[1] * 3.0, d[2] * 2.1, 4, self.seed + 71)
        veil = clamp((veil - 0.54) * 1.9) * smoothstep(-2.0, 22.0, el)
        r += 0.012 * veil
        g += 0.017 * veil
        b += 0.030 * veil

        # aurora
        strength, height = self.aurora.intensity(az, el)
        if strength > 0.0:
            ac = self.aurora.color(height)
            k = clamp(strength * 0.55, 0.0, 2.2)
            r += ac[0] * k
            g += ac[1] * k
            b += ac[2] * k

        return (r, g, b)

    def paint_static(self, buffer):
        """The Christmas star, painted at full resolution."""
        right, up = tangent_basis(self.hero)
        hero = self.hero
        warm = self.hero_color
        tip = srgb("#ffd27a")

        def shade(d):
            value = four_point_star(
                d, hero, right, up, 0.42, 14.0, 8.0, 32.0,
                halo_gain=0.34, halo_deg=1.4,
            )
            if value <= 0.004:
                return None
            ang = math.degrees(math.acos(clamp(dot(d, hero), -1.0, 1.0)))
            tint = mix3(warm, tip, smoothstep(0.8, 9.0, ang))
            return (tint[0], tint[1], tint[2], min(value, 3.2))

        buffer.paint_local(hero, 32.0, shade)

        # a handful of bright companion stars with small flares
        rng = random.Random(self.seed + 4)
        for _ in range(9):
            az = rng.uniform(0.0, 360.0)
            el = rng.uniform(6.0, 70.0)
            d0 = direction(az, el)
            if dot(d0, hero) > 0.93:
                continue
            r2, u2 = tangent_basis(d0)
            scale = rng.uniform(0.7, 1.35)
            color = srgb("#eaf1ff") if rng.random() < 0.7 else srgb("#ffe3bd")

            def shade_small(d, d0=d0, r2=r2, u2=u2, scale=scale, color=color):
                value = four_point_star(
                    d, d0, r2, u2, 0.20 * scale, 2.2 * scale, 1.5 * scale, 7.0 * scale,
                    halo_gain=0.10, halo_deg=0.34 * scale,
                )
                if value <= 0.006:
                    return None
                return (color[0], color[1], color[2], min(value * 0.85, 2.6))

            buffer.paint_local(d0, 7.0 * scale, shade_small)


# --------------------------------------------------------------------------
# variant B - "Kerstmarkt"
# --------------------------------------------------------------------------


class Kerstmarkt:
    key = "b"
    folder = "variant-b-kerstmarkt"
    slug = "kerstmarkt"
    title = "Kerst Sky B - Kerstmarkt"
    description = "Warme pruim-en-amber kersthemel met rood-groene suikerstokwolken, gouden lichtjesslingers en een kerstboom-sterrenbeeld."
    seed = 1225

    sky_stops = [
        (-25.0, srgb("#080311")),
        (-6.0, srgb("#14071c")),
        (0.0, srgb("#b8541d")),
        (2.5, srgb("#9c3a2a")),
        (7.0, srgb("#6d2440")),
        (16.0, srgb("#45184a")),
        (34.0, srgb("#2a0f3c")),
        (60.0, srgb("#170827")),
        (90.0, srgb("#0d0418")),
    ]
    star_color_pool = [
        (srgb("#fff4e0"), 0.42),
        (srgb("#ffffff"), 0.24),
        (srgb("#ffe2b4"), 0.18),
        (srgb("#e6ecff"), 0.12),
        (srgb("#ffcf9a"), 0.04),
    ]
    star_count = 2900
    preview_az = 8.0
    preview_el = 20.0

    def __init__(self):
        self.band_pole = normalize(direction(288.0, 47.0))
        self.band_dir = normalize(cross(self.band_pole, (0.0, 1.0, 0.0)))
        self.candy_red = srgb("#f2505a")
        self.candy_green = srgb("#3fbf72")
        self.horizon_glow = srgb("#ff8a3c")
        self.tree_center = direction(8.0, 30.0)
        # Azimuths are unwrapped on purpose: 285 -> 435 strings the garland
        # across the north, not the long way round through the south.
        self.garlands = [
            # (az0, el0, az1, el1, sag, bulbs, phase)
            (285.0, 33.0, 435.0, 31.0, 22.0, 32, 0.0),
            (25.0, 45.0, 165.0, 39.0, 17.0, 26, 0.6),
            (150.0, 27.0, 290.0, 31.0, 14.0, 24, 0.25),
            (330.0, 54.0, 210.0, 50.0, 16.0, 21, 0.85),
        ]
        self.bulb_colors = [
            srgb("#ffc561"),
            srgb("#ff6b5a"),
            srgb("#63d98a"),
            srgb("#ffe9b0"),
        ]

    def field(self, d):
        az, el = azimuth_elevation(d)
        r, g, b = ramp(self.sky_stops, el)

        # warm afterglow, brightest toward the west where the sun went down
        west = clamp(0.5 + 0.5 * math.cos((az - 265.0) * DEG))
        vary = 0.70 + 0.30 * vnoise3(az * 0.02, 0.0, 0.0, self.seed + 8)
        bloom = horizon_band(el, 9.0, 3.2) * (0.12 + 0.34 * west * west) * vary
        hg = self.horizon_glow
        r += hg[0] * bloom
        g += hg[1] * bloom
        b += hg[2] * bloom

        # candy-cane nebula: broad red and green ribbons running along a band,
        # with a darker gap between them so they read as separate stripes
        density = milky_way(d, self.band_pole, 0.34, self.seed + 3, warp=0.14)
        density *= smoothstep(-2.0, 22.0, el)
        if density > 0.0:
            swirl = fbm3(d[0] * 1.25, d[1] * 1.8 + 3.0, d[2] * 1.25, 4, self.seed)
            wave = math.sin(dot(d, self.band_dir) * 8.5 + swirl * 3.4)
            cc = mix3(self.candy_green, self.candy_red, smoothstep(-0.35, 0.35, wave))
            separation = 0.22 + 0.78 * abs(wave)
            k = density * 0.55 * separation
            r += cc[0] * k
            g += cc[1] * k
            b += cc[2] * k

        # soft snow haze high up
        haze = fbm3(d[0] * 2.6 + 5.0, d[1] * 3.4, d[2] * 2.6, 3, self.seed + 44)
        haze = clamp((haze - 0.52) * 1.9) * smoothstep(4.0, 40.0, el)
        r += 0.048 * haze
        g += 0.034 * haze
        b += 0.052 * haze

        return (r, g, b)

    def paint_static(self, buffer):
        self._paint_garlands(buffer)
        self._paint_tree(buffer)

    def _paint_garlands(self, buffer):
        rng = random.Random(self.seed + 77)
        wire = srgb("#3b2a3f")
        hairline = max(0.9, 0.11 * buffer.size / 90.0)
        for az0, el0, az1, el1, sag, bulbs, phase in self.garlands:
            path = garland_path(az0, el0, az1, el1, sag, 260)
            for i in range(len(path) - 1):
                draw_arc(buffer, path[i], path[i + 1], wire, 0.16, hairline)
            for k in range(bulbs):
                t = (k + 0.5) / bulbs
                idx = int(t * (len(path) - 1))
                center = path[idx]
                color = self.bulb_colors[(k + int(phase * 7)) % len(self.bulb_colors)]
                size = rng.uniform(0.16, 0.26)
                gain = rng.uniform(0.85, 1.35)

                def shade(d, center=center, color=color, size=size, gain=gain):
                    ang = math.degrees(math.acos(clamp(dot(d, center), -1.0, 1.0)))
                    core = math.exp(-((ang / size) ** 2)) * 2.1
                    glow = math.exp(-((ang / (size * 4.0)) ** 1.5)) * 0.28
                    value = (core + glow) * gain
                    if value <= 0.006:
                        return None
                    return (color[0], color[1], color[2], min(value, 2.8))

                buffer.paint_local(center, size * 10.0, shade)

    def _paint_tree(self, buffer):
        """A fir-tree constellation: outline stars joined by faint lines."""
        center = self.tree_center
        right, up = tangent_basis(center)

        def place(u_deg, v_deg):
            return normalize(
                (
                    center[0] + right[0] * u_deg * DEG + up[0] * v_deg * DEG,
                    center[1] + right[1] * u_deg * DEG + up[1] * v_deg * DEG,
                    center[2] + right[2] * u_deg * DEG + up[2] * v_deg * DEG,
                )
            )

        top = place(0.0, 15.5)
        # the trunk corners only carry lines - stars there turn the figure into
        # an unreadable cluster
        shoulder_l = place(-5.8, 4.4)
        shoulder_r = place(5.8, 4.4)
        foot_l = place(-12.6, -7.0)
        foot_r = place(12.6, -7.0)
        outline = [
            shoulder_l,
            foot_l,
            place(-2.4, -7.0),
            place(-2.4, -13.0),
            place(2.4, -13.0),
            place(2.4, -7.0),
            foot_r,
            shoulder_r,
        ]
        star_points = [shoulder_l, foot_l, foot_r, shoulder_r]
        line_color = srgb("#9dbcff")
        hairline = max(0.9, 0.10 * buffer.size / 90.0)
        chain = [top] + outline + [top]
        for i in range(len(chain) - 1):
            draw_arc(buffer, chain[i], chain[i + 1], line_color, 0.13, hairline)

        star_color = srgb("#eef3ff")
        for point in star_points:
            r2, u2 = tangent_basis(point)

            def shade(d, point=point, r2=r2, u2=u2):
                value = four_point_star(
                    d, point, r2, u2, 0.16, 1.5, 1.1, 4.5,
                    halo_gain=0.08, halo_deg=0.30,
                )
                if value <= 0.008:
                    return None
                return (star_color[0], star_color[1], star_color[2], min(value * 0.75, 2.2))

            buffer.paint_local(point, 4.5, shade)

        # the star on top gets the full treatment
        r2, u2 = tangent_basis(top)
        gold = srgb("#ffd98a")

        def shade_top(d):
            value = four_point_star(
                d, top, r2, u2, 0.34, 5.5, 3.6, 13.0, halo_gain=0.24, halo_deg=0.85
            )
            if value <= 0.006:
                return None
            return (gold[0], gold[1], gold[2], min(value * 1.15, 3.0))

        buffer.paint_local(top, 13.0, shade_top)


VARIANTS = {"a": StilleNacht, "b": Kerstmarkt}


# --------------------------------------------------------------------------
# starfield (the rotating additive layer)
# --------------------------------------------------------------------------


def build_stars(scene, count):
    rng = random.Random(scene.seed + 991)
    pool = scene.star_color_pool
    total_weight = sum(w for _, w in pool)
    stars = []
    for _ in range(count):
        y = rng.uniform(-1.0, 1.0)
        radius = math.sqrt(max(0.0, 1.0 - y * y))
        theta = rng.uniform(0.0, math.tau)
        d = (radius * math.cos(theta), y, radius * math.sin(theta))

        pick = rng.uniform(0.0, total_weight)
        color = pool[-1][0]
        acc = 0.0
        for candidate, weight in pool:
            acc += weight
            if pick <= acc:
                color = candidate
                break

        # sizes are angular so the look does not change with texture resolution
        magnitude = rng.random() ** 3.1
        brightness = 0.14 + 1.55 * magnitude ** 2.0
        size_deg = 0.05 + 0.17 * magnitude ** 1.3
        stars.append((d, color, brightness, size_deg))
    return stars


def paint_starfield(buffer, stars, scene):
    px_per_degree = buffer.size / 90.0
    for d, color, brightness, size_deg in stars:
        radius = max(0.8, size_deg * px_per_degree)
        buffer.splat(d, radius, color, brightness, falloff=2.6)

    # a few showpiece stars with visible flares
    rng = random.Random(scene.seed + 313)
    for _ in range(14):
        y = rng.uniform(-0.25, 0.95)
        radius = math.sqrt(max(0.0, 1.0 - y * y))
        theta = rng.uniform(0.0, math.tau)
        d0 = normalize((radius * math.cos(theta), y, radius * math.sin(theta)))
        r2, u2 = tangent_basis(d0)
        color = scene.star_color_pool[0][0]
        scale = rng.uniform(0.8, 1.5)

        def shade(d, d0=d0, r2=r2, u2=u2, scale=scale, color=color):
            value = four_point_star(
                d, d0, r2, u2, 0.18 * scale, 2.0 * scale, 1.4 * scale, 6.5 * scale,
                halo_gain=0.09, halo_deg=0.30 * scale,
            )
            if value <= 0.01:
                return None
            return (color[0], color[1], color[2], min(value * 0.9, 2.4))

        buffer.paint_local(d0, 6.5 * scale, shade)


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------


def render_cube(size, channels, field_fn, paint_fn, lowres, label):
    faces_bytes = {}
    buffers = []
    for face in FACES:
        started = time.time()
        buffer = FaceBuffer(face, size, channels)
        if field_fn is not None:
            buffer.fill_field(field_fn, lowres)
        if paint_fn is not None:
            paint_fn(buffer)
        buffers.append(buffer)
        print(
            "    %s %-6s %5.1fs" % (label, face.name, time.time() - started),
            flush=True,
        )
    rows = list(encode_rows(buffers, size, channels))
    # keep the encoded faces around for previews
    stride = size * channels
    for face in FACES:
        chunks = []
        for y in range(size):
            row = rows[face.row * size + y]
            start = face.col * stride
            chunks.append(row[start : start + stride])
        faces_bytes[face.index] = b"".join(chunks)
    return rows, faces_bytes


# --------------------------------------------------------------------------
# previews
# --------------------------------------------------------------------------


def composite(sky, stars):
    r = sky[0] + stars[0] * (stars[3] / 255.0)
    g = sky[1] + stars[1] * (stars[3] / 255.0)
    b = sky[2] + stars[2] * (stars[3] / 255.0)
    return (min(255, int(r)), min(255, int(g)), min(255, int(b)))


def render_panorama(path, sky_sampler, star_sampler, width=1440, height=720):
    rows = []
    for y in range(height):
        el = 90.0 - 180.0 * (y + 0.5) / height
        line = bytearray()
        for x in range(width):
            az = -180.0 + 360.0 * (x + 0.5) / width
            d = direction(az, el)
            r, g, b = composite(sky_sampler.sample(d), star_sampler.sample(d))
            line += bytes((r, g, b))
        rows.append(bytes(line))
    write_png(path, width, height, rows, 3)


TREES = [
    (-58.0, 3.2, 9.5),
    (-44.0, 2.1, 6.2),
    (-30.0, 4.0, 12.5),
    (-12.0, 2.4, 7.0),
    (4.0, 3.0, 9.0),
    (17.0, 5.0, 15.0),
    (33.0, 2.6, 8.0),
    (46.0, 3.4, 10.5),
    (61.0, 2.2, 6.4),
]


def ground_elevation(az_rel):
    """Silhouette height (degrees) of the snowy tree line at a relative azimuth."""
    base = -2.0 + 1.35 * math.sin(az_rel * 0.09) + 0.9 * math.sin(az_rel * 0.21 + 1.1)
    top = base
    for center, half, height in TREES:
        dx = abs(az_rel - center)
        if dx < half:
            t = 1.0 - dx / half
            # three tiers so it reads as a fir tree
            tier = height * (0.35 + 0.65 * t ** 0.7)
            tier *= 1.0 - 0.10 * math.cos(t * 9.0)
            top = max(top, base + tier)
    return top


def render_ingame(path, sky_sampler, star_sampler, look_az, look_el=10.0,
                  width=1280, height=720, hfov=100.0):
    forward = direction(look_az, look_el)
    right, up = tangent_basis(forward)
    half = math.tan(hfov * 0.5 * DEG)
    aspect = height / width
    ground = (10, 14, 22)
    snow = (74, 86, 106)
    rows = []
    for y in range(height):
        sy = (1.0 - 2.0 * (y + 0.5) / height) * half * aspect
        line = bytearray()
        for x in range(width):
            sx = (2.0 * (x + 0.5) / width - 1.0) * half
            d = normalize(
                (
                    forward[0] + right[0] * sx + up[0] * sy,
                    forward[1] + right[1] * sx + up[1] * sy,
                    forward[2] + right[2] * sx + up[2] * sy,
                )
            )
            az, el = azimuth_elevation(d)
            az_rel = angle_delta(az, look_az)
            horizon = ground_elevation(az_rel)
            if el <= horizon:
                if el > horizon - 0.14:
                    line += bytes(snow)
                else:
                    fade = clamp((horizon - el) / 12.0)
                    line += bytes(
                        (
                            int(ground[0] * (1.0 - 0.45 * fade)),
                            int(ground[1] * (1.0 - 0.45 * fade)),
                            int(ground[2] * (1.0 - 0.45 * fade)),
                        )
                    )
            else:
                r, g, b = composite(sky_sampler.sample(d), star_sampler.sample(d))
                line += bytes((r, g, b))
        rows.append(bytes(line))
    write_png(path, width, height, rows, 3)


def render_icon(path, sky_sampler, star_sampler, look_az, look_el, size=128):
    render_ingame(
        path, sky_sampler, star_sampler, look_az, look_el,
        width=size, height=size, hfov=95.0,
    )


# --------------------------------------------------------------------------
# pack assembly
# --------------------------------------------------------------------------


def night_fade():
    """Alpha curve: invisible by day, full between dusk and dawn."""
    return {
        "duration": 24000,
        "keyFrames": {
            "0": 0.0,
            "11200": 0.0,
            "13400": 1.0,
            "22200": 1.0,
            "23600": 0.0,
        },
    }


def write_pack(scene, out_dir, sky_rows, star_rows, size):
    assets = os.path.join(out_dir, "assets")
    sky_dir = os.path.join(assets, "nuit", "sky")
    tex_dir = os.path.join(assets, NAMESPACE, "textures", "sky")
    os.makedirs(sky_dir, exist_ok=True)
    os.makedirs(tex_dir, exist_ok=True)

    sky_png = os.path.join(tex_dir, "%s_sky.png" % scene.slug)
    star_png = os.path.join(tex_dir, "%s_stars.png" % scene.slug)
    write_png(sky_png, size * 3, size * 2, sky_rows, 3)
    write_png(star_png, size * 3, size * 2, star_rows, 3)

    def dump(name, payload):
        with open(os.path.join(sky_dir, name), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")

    # 1. keep the vanilla daytime sky, sunrise and sunset intact
    dump(
        "00_vanilla_sky.json",
        {
            "schemaVersion": 1,
            "type": "overworld",
            "properties": {"layer": 0},
            "conditions": {"dimensions": {"entries": ["minecraft:overworld"]}},
        },
    )

    # 2. the painted Christmas sky, anchored to the horizon (no rotation)
    dump(
        "10_kerst_sky.json",
        {
            "schemaVersion": 1,
            "type": "square-textured",
            "texture": "%s:textures/sky/%s_sky.png" % (NAMESPACE, scene.slug),
            "blend": {"type": "normal"},
            "properties": {
                "layer": 10,
                "fade": night_fade(),
                "transitionInDuration": 40,
                "transitionOutDuration": 40,
                "sunSkyTint": False,
                "rotation": {"skyboxRotation": True, "speed": 0.0},
            },
            "conditions": {"dimensions": {"entries": ["minecraft:overworld"]}},
        },
    )

    # 3. the starfield, turning with the sun like vanilla stars do
    dump(
        "20_kerst_stars.json",
        {
            "schemaVersion": 1,
            "type": "square-textured",
            "texture": "%s:textures/sky/%s_stars.png" % (NAMESPACE, scene.slug),
            "blend": {"type": "add"},
            "properties": {
                "layer": 20,
                "fade": night_fade(),
                "transitionInDuration": 40,
                "transitionOutDuration": 40,
                "sunSkyTint": False,
                "rotation": {
                    "skyboxRotation": False,
                    "speed": 1.0,
                    "axis": {"0": [90.0, 0.0, 0.0]},
                },
            },
            "conditions": {"dimensions": {"entries": ["minecraft:overworld"]}},
        },
    )

    # 4. sun and moon stay, vanilla stars are off (the texture supplies its own)
    dump(
        "30_decorations.json",
        {
            "schemaVersion": 1,
            "type": "decorations",
            "showSun": True,
            "showMoon": True,
            "showStars": False,
            "blend": {"type": "decorations"},
            "properties": {"layer": 30},
            "conditions": {"dimensions": {"entries": ["minecraft:overworld"]}},
        },
    )

    with open(os.path.join(out_dir, "pack.mcmeta"), "w", encoding="utf-8") as handle:
        json.dump(
            {
                "pack": {
                    "pack_format": PACK_FORMAT,
                    "min_format": PACK_FORMAT,
                    "max_format": PACK_FORMAT,
                    "description": scene.description,
                }
            },
            handle,
            indent=2,
        )
        handle.write("\n")


def zip_pack(out_dir, zip_path):
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for base, _dirs, files in os.walk(out_dir):
            for name in sorted(files):
                full = os.path.join(base, name)
                archive.write(full, os.path.relpath(full, out_dir))


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


def build(scene, size, lowres, previews):
    print("  building %s (%d px per face)" % (scene.title, size), flush=True)
    out_dir = os.path.join(ROOT, scene.folder)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)

    sky_rows, sky_faces = render_cube(size, 3, scene.field, scene.paint_static, lowres, "sky  ")
    stars = build_stars(scene, scene.star_count)
    # The starfield is an opaque RGB texture on purpose: Nuit's "add" blend is
    # SRC_ALPHA/ONE, so with alpha = 1 the GPU adds exactly the painted colour and
    # the layer's fade alpha still scales the whole thing. Black adds nothing.
    star_rows, star_faces = render_cube(
        size, 3, None, lambda buf: paint_starfield(buf, stars, scene), lowres, "stars"
    )

    write_pack(scene, out_dir, sky_rows, star_rows, size)

    preview_dir = os.path.join(ROOT, "previews")
    os.makedirs(preview_dir, exist_ok=True)
    sky_sampler = CubeSampler(sky_faces, size, 3)
    star_sampler = CubeSampler(star_faces, size, 3)
    look_az = scene.preview_az
    look_el = scene.preview_el

    render_icon(
        os.path.join(out_dir, "pack.png"), sky_sampler, star_sampler, look_az, look_el
    )

    if previews:
        started = time.time()
        render_panorama(
            os.path.join(preview_dir, "%s-panorama.png" % scene.key),
            sky_sampler,
            star_sampler,
        )
        render_ingame(
            os.path.join(preview_dir, "%s-ingame.png" % scene.key),
            sky_sampler,
            star_sampler,
            look_az,
            look_el,
        )
        print("    previews %5.1fs" % (time.time() - started), flush=True)

    zip_pack(out_dir, os.path.join(ROOT, "%s.zip" % scene.folder))
    return out_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--face-size", type=int, default=1024)
    parser.add_argument("--lowres", type=int, default=176)
    parser.add_argument("--quick", action="store_true", help="fast, low resolution pass")
    parser.add_argument("--only", choices=sorted(VARIANTS), help="build a single variant")
    parser.add_argument("--no-previews", action="store_true")
    args = parser.parse_args()

    size = 192 if args.quick else args.face_size
    lowres = 72 if args.quick else args.lowres

    keys = [args.only] if args.only else sorted(VARIANTS)
    started = time.time()
    for key in keys:
        scene = VARIANTS[key]()
        build(scene, size, lowres, not args.no_previews)
    print("done in %.1fs" % (time.time() - started))


if __name__ == "__main__":
    main()
