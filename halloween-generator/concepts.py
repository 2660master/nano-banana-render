"""The 5 Halloween sky concepts. Each concept is a function dirs -> RGB float (H,W,3)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from skylib import (fbm3, ridged, starfield, splat, pumpkin_sprite, moon_sprite,
                    bat_sprite, tree_sprite, smooth, lerp3, window_glow)


def soften(spr, px):
    im = Image.fromarray(np.clip(spr, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(px))).astype(np.float64)


def dirv(az_deg, alt_deg):
    """Minecraft direction from azimuth (0=north, 90=east) and altitude."""
    a = np.radians(az_deg); e = np.radians(alt_deg)
    return (np.sin(a) * np.cos(e), np.sin(e), -np.cos(a) * np.cos(e))


def grad(y, stops):
    out = np.zeros(y.shape + (3,))
    for i in range(len(stops) - 1):
        y0, c0 = stops[i]; y1, c1 = stops[i + 1]
        t = np.clip((y - y0) / (y1 - y0), 0, 1)
        t = t * t * (3 - 2 * t)
        m = ((y >= y0) & (y < y1)) if i else (y < y1)
        if i == len(stops) - 2:
            m = m | (y >= y1)
        out[m] = lerp3(c0, c1, t)[m]
    return out


def clouds(d, scale=2.0, squash=2.6, seed=5, octaves=6, warp=0.45):
    p = (d * scale).copy()
    p[..., 1] *= squash
    if warp:
        w = fbm3(p * 1.7, 3, seed=seed + 91)
        p = p + (w[..., None] - 0.5) * warp
    return fbm3(p, octaves, seed=seed)


def spire_sprite(S=512, col=(7, 6, 11), win=(255, 156, 46)):
    F = 2; C = S * F
    img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cx = C * 0.5
    dr.rectangle([cx - C * 0.090, C * 0.40, cx + C * 0.090, C], fill=col + (255,))
    dr.polygon([(cx - C * 0.115, C * 0.40), (cx + C * 0.115, C * 0.40), (cx, C * 0.075)], fill=col + (255,))
    dr.rectangle([cx - C * 0.006, C * 0.008, cx + C * 0.006, C * 0.085], fill=col + (255,))
    dr.rectangle([cx - C * 0.030, C * 0.026, cx + C * 0.030, C * 0.038], fill=col + (255,))
    dr.rectangle([cx - C * 0.175, C * 0.62, cx - C * 0.090, C], fill=col + (255,))
    dr.polygon([(cx - C * 0.190, C * 0.62), (cx - C * 0.075, C * 0.62), (cx - C * 0.132, C * 0.535)], fill=col + (255,))
    dr.rectangle([cx + C * 0.090, C * 0.70, cx + C * 0.205, C], fill=col + (255,))
    dr.polygon([(cx + C * 0.078, C * 0.70), (cx + C * 0.218, C * 0.70), (cx + C * 0.148, C * 0.615)], fill=col + (255,))
    for (wx, wy, ww, wh) in [(-0.028, 0.50, 0.056, 0.055), (-0.148, 0.71, 0.038, 0.045),
                             (0.130, 0.79, 0.038, 0.045)]:
        dr.rectangle([cx + C * wx, C * wy, cx + C * (wx + ww), C * (wy + wh)], fill=win + (255,))
    return np.asarray(img.resize((S, S), Image.LANCZOS)).astype(np.float64)


# ============================================================ 1. BLOODMOON =
def bloodmoon(d):
    y = d[..., 1]
    rgb = grad(y, [(-1.0, (0.016, 0.004, 0.011)), (-0.10, (0.055, 0.011, 0.017)),
                   (0.02, (0.255, 0.042, 0.032)), (0.16, (0.165, 0.028, 0.050)),
                   (0.52, (0.052, 0.013, 0.058)), (1.0, (0.020, 0.008, 0.040))])
    MA, MALT = 168.0, 25.0
    mc = np.array(dirv(MA, MALT))
    hal = np.clip(d @ mc, 0, 1)
    rgb += np.array([0.90, 0.26, 0.07]) * (hal ** 30)[..., None] * 0.55
    rgb += np.array([0.50, 0.11, 0.05]) * (hal ** 5)[..., None] * 0.13
    rgb += starfield(d, 58, 0.10, 0.105, seed=11, warm=0.9, bright=0.60) * \
        np.clip(1.25 - hal * 1.1, 0, 1)[..., None]
    glow = np.zeros_like(rgb)
    p, pg = pumpkin_sprite(600, body=(198, 76, 20), dark=(104, 30, 8), rim=(255, 150, 70),
                           glowcol=(255, 214, 128), halo=(255, 96, 18), face_style=0)
    splat(rgb, glow, d, p, mc, 32.0, glow=pg, glow_scale=2.1, glow_strength=0.62)
    # low cloud bank
    c = clouds(d, 2.05, 3.1, seed=5)
    band = smooth(c, 0.47, 0.70) * smooth(y, -0.34, -0.02) * (1 - smooth(y, 0.28, 0.72))
    cl = grad(y, [(-0.2, (0.040, 0.010, 0.018)), (0.15, (0.075, 0.018, 0.028)), (0.6, (0.048, 0.013, 0.032))])
    rgb = rgb * (1 - band[..., None] * 0.94) + cl * (band[..., None] * 0.94)
    rim = smooth(c, 0.435, 0.50) * (1 - smooth(c, 0.50, 0.58)) * smooth(y, -0.3, 0.02)
    rgb += np.array([0.85, 0.26, 0.06]) * (rim * (0.22 + 0.95 * np.clip(hal * 1.5, 0, 1)))[..., None] * 0.42
    # high wisps
    c2 = clouds(d, 4.4, 1.5, seed=21, octaves=5)
    wisp = smooth(c2, 0.53, 0.86) * smooth(y, 0.02, 0.5)
    rgb += np.array([0.36, 0.08, 0.11]) * wisp[..., None] * 0.34
    c3 = clouds(d, 7.5, 1.2, seed=57, octaves=4)
    rgb += np.array([0.30, 0.09, 0.06]) * (smooth(c3, 0.62, 0.92) * smooth(y, 0.25, 0.95))[..., None] * 0.16
    bat = bat_sprite(224)
    for az, alt, s, r in [(158, 34, 7.0, -12), (177, 31.5, 5.6, 9), (148, 18.5, 5.0, 16),
                          (186, 15.5, 4.2, -7), (197, 28, 3.6, 20), (139, 29, 3.2, -18),
                          (207, 20, 2.9, 5), (127, 23, 2.6, 12), (218, 33, 2.3, -22),
                          (118, 13, 2.1, 8)]:
        splat(rgb, glow, d, bat, dirv(az, alt), s, roll_deg=r, opacity=0.96)
    return rgb + glow


# ============================================================== 2. NEBULA ==
def nebula(d):
    y = d[..., 1]
    rgb = grad(y, [(-1.0, (0.007, 0.005, 0.014)), (-0.05, (0.015, 0.011, 0.032)),
                   (0.25, (0.020, 0.013, 0.044)), (1.0, (0.009, 0.007, 0.026))])
    axis = np.array(dirv(112, 24)); axis = axis / np.linalg.norm(axis)
    band = np.abs(d @ axis)
    galaxy = np.exp(-(band / 0.36) ** 2)
    n1 = ridged(d * 2.4, 6, seed=31)
    n2 = fbm3(d * 4.1, 6, seed=47)
    n3 = fbm3(d * 1.35, 5, seed=63)
    dust = smooth(n2, 0.30, 0.80)
    orange = np.clip((n1 ** 1.7) * galaxy * 1.85 * smooth(n3, 0.25, 0.75), 0, 2)
    purple = np.clip(smooth(n3, 0.40, 0.92) * (0.35 + 0.9 * galaxy) * 1.25, 0, 2)
    teal = np.clip(smooth(fbm3(d * 3.0, 5, seed=88), 0.62, 0.95) * (0.25 + galaxy), 0, 2)
    rgb += np.array([1.00, 0.40, 0.055]) * (orange * 0.80)[..., None]
    rgb += np.array([0.46, 0.13, 0.62]) * (purple * 0.52)[..., None]
    rgb += np.array([0.06, 0.52, 0.42]) * (teal * 0.30)[..., None]
    rgb *= (1 - 0.45 * (dust * galaxy)[..., None])
    rgb += starfield(d, 44, 0.34, 0.085, seed=13, warm=0.25, bright=1.05) * (1 - 0.30 * galaxy)[..., None]
    rgb += starfield(d, 88, 0.26, 0.055, seed=29, warm=0.05, bright=0.55)
    rgb += starfield(d, 26, 0.06, 0.055, seed=71, warm=0.5, bright=1.6)
    glow = np.zeros_like(rgb)
    amod = np.clip(0.45 + 1.05 * fbm3(d * 6.0, 5, seed=123), 0, 1.25)
    p, pg = pumpkin_sprite(640, body=(255, 122, 26), dark=(150, 42, 72), rim=(255, 198, 112),
                           glowcol=(255, 238, 178), halo=(255, 108, 30), face_style=1)
    ps = soften(p, 7.0); ps[..., 3] *= 0.70
    splat(rgb, glow, d, ps, dirv(112, 26), 48.0, glow=window_glow(soften(pg, 10.0)),
          glow_scale=2.0, glow_strength=0.62, alpha_mod=amod)
    p2, pg2 = pumpkin_sprite(320, body=(196, 74, 148), dark=(92, 26, 84), rim=(232, 152, 222),
                             glowcol=(232, 204, 255), halo=(196, 70, 216), face_style=2)
    p2s = soften(p2, 4.0); p2s[..., 3] *= 0.58
    splat(rgb, glow, d, p2s, dirv(296, 16), 22.0, glow=window_glow(soften(pg2, 6.0)),
          glow_scale=2.0, glow_strength=0.5, alpha_mod=amod)
    p3, pg3 = pumpkin_sprite(256, body=(126, 196, 116), dark=(42, 94, 52), rim=(194, 255, 174),
                             glowcol=(214, 255, 202), halo=(96, 216, 120), face_style=0)
    p3s = soften(p3, 3.5); p3s[..., 3] *= 0.52
    splat(rgb, glow, d, p3s, dirv(18, 48), 16.0, glow=window_glow(soften(pg3, 5.0)),
          glow_scale=2.0, glow_strength=0.45, alpha_mod=amod)
    return rgb + glow


# =========================================================== 3. GRAVEYARD ==
def grave_sprite(S=256, col=(7, 8, 12)):
    """A small cluster of headstones + a leaning cross, standing on the canvas floor."""
    F = 2; C = S * F
    img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    g = C * 0.5
    dr.rectangle([g - C * 0.115, C * 0.52, g + C * 0.115, C], fill=col + (255,))
    dr.ellipse([g - C * 0.115, C * 0.44, g + C * 0.115, C * 0.60], fill=col + (255,))
    dr.rectangle([g - C * 0.315, C * 0.66, g - C * 0.165, C], fill=col + (255,))
    dr.polygon([(g - C * 0.325, C * 0.66), (g - C * 0.155, C * 0.66), (g - C * 0.240, C * 0.575)],
               fill=col + (255,))
    for (ox, w, h, lean) in [(0.255, 0.030, 0.30, 0.055)]:
        x = g + C * ox
        dr.polygon([(x - C * w, C), (x + C * w, C),
                    (x + C * (w + lean), C * (1 - h)), (x - C * (w - lean), C * (1 - h))],
                   fill=col + (255,))
        dr.polygon([(x + C * (lean * 0.55) - C * 0.095, C * (1 - h * 0.78)),
                    (x + C * (lean * 0.55) + C * 0.095, C * (1 - h * 0.82)),
                    (x + C * (lean * 0.55) + C * 0.095, C * (1 - h * 0.70)),
                    (x + C * (lean * 0.55) - C * 0.095, C * (1 - h * 0.66))], fill=col + (255,))
    dr.rectangle([0, C * 0.965, C, C], fill=col + (255,))
    return np.asarray(img.resize((S, S), Image.LANCZOS)).astype(np.float64)


def _ground(size, sink=3.0):
    """Altitude that puts a sprite's floor just under the horizon."""
    return 0.48 * size - sink


def graveyard(d):
    y = d[..., 1]
    rgb = grad(y, [(-1.0, (0.009, 0.013, 0.013)), (-0.06, (0.032, 0.056, 0.050)),
                   (0.03, (0.100, 0.205, 0.158)), (0.14, (0.052, 0.110, 0.110)),
                   (0.45, (0.019, 0.033, 0.068)), (1.0, (0.007, 0.013, 0.036))])
    mc = np.array(dirv(318, 34))
    hal = np.clip(d @ mc, 0, 1)
    rgb += np.array([0.50, 0.60, 0.58]) * (hal ** 34)[..., None] * 0.26
    rgb += starfield(d, 54, 0.16, 0.095, seed=17, warm=0.1, bright=0.78) * \
        np.clip(1.15 - hal * 0.8, 0, 1)[..., None]
    rgb += starfield(d, 104, 0.12, 0.055, seed=61, warm=0.0, bright=0.40)
    glow = np.zeros_like(rgb)
    m, mg = moon_sprite(512, col=(226, 236, 222), tint=(0.92, 1.0, 0.94))
    splat(rgb, glow, d, m, mc, 11.0, glow=mg, glow_scale=2.6, glow_strength=0.42)
    # thin cloud veils drifting past the moon
    c = clouds(d, 2.6, 2.2, seed=71)
    veil = smooth(c, 0.46, 0.78) * (1 - smooth(y, 0.55, 0.95))
    rgb = rgb * (1 - veil[..., None] * 0.40) + \
        grad(y, [(-0.1, (0.042, 0.080, 0.070)), (0.5, (0.028, 0.046, 0.066))]) * (veil[..., None] * 0.40)
    # ground mist
    mist = np.exp(-((y + 0.005) / 0.075) ** 2) * (0.45 + 0.75 * fbm3(d * 5.2, 5, seed=94))
    rgb += np.array([0.10, 0.26, 0.21]) * np.clip(mist, 0, 1.3)[..., None] * 0.80
    rng = np.random.default_rng(4)
    # --- far silhouette ring: hazy, mist-tinted, sits low -----------------
    far_trees = [tree_sprite(340, col=(21, 44, 42), seed=s) for s in range(4)]
    for k in range(30):
        az = k * (360 / 30) + rng.uniform(-5, 5)
        size = rng.uniform(9, 15)
        splat(rgb, glow, d, far_trees[k % 4], dirv(az, _ground(size, 4.5)), size, opacity=0.62)
    far_graves = grave_sprite(240, col=(24, 48, 45))
    for k in range(14):
        size = rng.uniform(5, 8)
        splat(rgb, glow, d, far_graves, dirv(rng.uniform(0, 360), _ground(size, 3.0)),
              size, opacity=0.55)
    splat(rgb, glow, d, spire_sprite(420, col=(20, 42, 40), win=(180, 120, 46)),
          dirv(96, _ground(20.0, 5.0)), 20.0, opacity=0.70)
    # --- near silhouette ring: solid black, taller ------------------------
    near_graves = grave_sprite(280, col=(6, 8, 11))
    for k in range(16):
        size = rng.uniform(7, 13)
        splat(rgb, glow, d, near_graves, dirv(rng.uniform(0, 360), _ground(size, 2.2)), size)
    trees = [tree_sprite(460, col=(6, 8, 12), seed=s) for s in range(6)]
    for k in range(24):
        az = k * (360 / 24) + rng.uniform(-6, 6)
        size = rng.uniform(16, 30)
        splat(rgb, glow, d, trees[k % 6], dirv(az, _ground(size, 3.2)), size)
    splat(rgb, glow, d, spire_sprite(560), dirv(305, _ground(34.0, 4.0)), 34.0)
    # --- floating jack-o-lanterns ----------------------------------------
    pks = [pumpkin_sprite(320, face_style=i, body=(206, 100, 24), dark=(112, 46, 12),
                          glowcol=(255, 214, 128), halo=(255, 124, 30), seed=i) for i in range(5)]
    spots = [(12, 9.5, 7.5), (58, 13.0, 5.2), (96, 7.5, 6.4), (143, 15.5, 4.4),
             (188, 8.5, 8.0), (222, 14.0, 4.8), (263, 10.0, 6.0), (300, 17.0, 3.8),
             (338, 8.0, 5.4), (75, 21.0, 3.0), (250, 23.0, 2.6), (170, 25.0, 2.2),
             (20, 19.0, 3.4), (120, 11.0, 4.0), (285, 5.5, 4.6), (208, 30.0, 2.0)]
    for i, (az, alt, s) in enumerate(spots):
        p, pg = pks[i % 5]
        splat(rgb, glow, d, p, dirv(az, alt), s, roll_deg=(i * 37) % 21 - 10,
              glow=pg, glow_scale=2.5, glow_strength=0.62)
    # --- bats around the moon --------------------------------------------
    bat = bat_sprite(224)
    for az, alt, s, r in [(311, 42, 4.6, -12), (327, 29, 3.6, 10), (298, 27, 3.0, 18),
                          (336, 45, 2.6, -8), (283, 38, 2.2, 14), (346, 34, 2.0, -18),
                          (45, 26, 2.4, 9), (152, 31, 2.1, -14), (232, 35, 1.9, 6)]:
        splat(rgb, glow, d, bat, dirv(az, alt), s, roll_deg=r, opacity=0.95)
    return rgb + glow


# ============================================================ 4. WITCHING ==
def witching(d):
    y = d[..., 1]
    rgb = grad(y, [(-1.0, (0.018, 0.007, 0.014)), (-0.08, (0.155, 0.044, 0.018)),
                   (0.015, (0.78, 0.315, 0.042)), (0.10, (0.46, 0.125, 0.042)),
                   (0.30, (0.235, 0.058, 0.082)), (0.62, (0.062, 0.017, 0.070)),
                   (1.0, (0.024, 0.010, 0.046))])
    mc = np.array(dirv(268, 30))
    hal = np.clip(d @ mc, 0, 1)
    rgb += np.array([0.95, 0.80, 0.45]) * (hal ** 46)[..., None] * 0.30
    rgb += starfield(d, 60, 0.12, 0.10, seed=23, warm=0.35, bright=0.60) * (1 - 0.6 * hal)[..., None]
    glow = np.zeros_like(rgb)
    m, mg = moon_sprite(512, col=(250, 234, 190), tint=(1.0, 0.96, 0.84))
    splat(rgb, glow, d, m, mc, 15.0, glow=mg, glow_scale=2.6, glow_strength=0.45)
    c = clouds(d, 1.75, 2.9, seed=101, octaves=6, warp=0.6)
    body = smooth(c, 0.500, 0.585) * (1 - smooth(y, 0.55, 1.0) * 0.55)
    cl = grad(y, [(-0.2, (0.048, 0.014, 0.014)), (0.2, (0.036, 0.011, 0.020)), (0.8, (0.026, 0.009, 0.026))])
    rgb = rgb * (1 - body[..., None] * 0.97) + cl * (body[..., None] * 0.97)
    edge = smooth(c, 0.468, 0.500) * (1 - smooth(c, 0.500, 0.540))
    rgb += np.array([1.0, 0.44, 0.075]) * (edge * (0.35 + 0.75 * np.clip(1 - np.abs(y) * 2.4, 0, 1)))[..., None] * 0.48
    rgb += np.array([1.0, 0.84, 0.52]) * (edge * (hal ** 4))[..., None] * 0.55
    c2 = clouds(d, 3.6, 1.8, seed=133, octaves=5)
    streak = smooth(c2, 0.58, 0.88) * smooth(y, 0.02, 0.45)
    rgb += np.array([0.50, 0.15, 0.05]) * streak[..., None] * 0.30
    pks = [pumpkin_sprite(340, face_style=i % 3, glowcol=(255, 218, 136), halo=(255, 118, 26))
           for i in range(3)]
    for i, (az, alt, s, r) in enumerate([(288, 20, 11.0, -13), (243, 27, 8.0, 15),
                                         (312, 11, 6.5, 8), (205, 15, 5.5, -20),
                                         (338, 24, 4.6, 11), (168, 9, 4.0, -6),
                                         (28, 17, 6.0, 18), (92, 11, 5.0, -10),
                                         (128, 23, 3.6, 22), (64, 6, 3.2, -14),
                                         (258, 44, 4.2, 6), (355, 38, 3.0, -16)]):
        p, pg = pks[i % 3]
        splat(rgb, glow, d, p, dirv(az, alt), s, roll_deg=r, glow=pg, glow_scale=2.5, glow_strength=0.68)
    bat = bat_sprite(224)
    rng = np.random.default_rng(9)
    for k in range(18):
        az = 268 + rng.uniform(-48, 48); alt = 31 + rng.uniform(-20, 18)
        splat(rgb, glow, d, bat, dirv(az, alt), rng.uniform(1.9, 5.4),
              roll_deg=rng.uniform(-25, 25), opacity=0.97)
    for k in range(8):
        az = 60 + rng.uniform(-45, 45); alt = 18 + rng.uniform(-11, 16)
        splat(rgb, glow, d, bat, dirv(az, alt), rng.uniform(1.8, 3.6),
              roll_deg=rng.uniform(-25, 25), opacity=0.95)
    return rgb + glow


# ================================================================ 5. VOID ==
def void(d):
    y = d[..., 1]
    rgb = grad(y, [(-1.0, (0.005, 0.003, 0.010)), (0.0, (0.019, 0.009, 0.030)),
                   (0.35, (0.013, 0.007, 0.026)), (1.0, (0.004, 0.003, 0.013))])
    w1 = ridged(d * 1.9, 6, seed=201)
    w2 = fbm3(d * 3.4, 6, seed=222)
    wisp = np.clip(smooth(w1, 0.46, 0.95) * smooth(w2, 0.30, 0.85), 0, 1)
    rgb += np.array([0.32, 0.075, 0.44]) * wisp[..., None] * 0.55
    rgb += np.array([0.045, 0.22, 0.12]) * (smooth(w2, 0.62, 0.98) * smooth(w1, 0.3, 0.8))[..., None] * 0.50
    rgb += starfield(d, 70, 0.06, 0.085, seed=37, warm=0.0, bright=0.60)
    glow = np.zeros_like(rgb)
    rng = np.random.default_rng(12)
    pks = [pumpkin_sprite(380, face_style=i % 3, silhouette=True, glowcol=g, halo=h)
           for i, (g, h) in enumerate([((255, 190, 86), (255, 104, 16)),
                                       ((255, 166, 56), (240, 72, 12)),
                                       ((255, 208, 120), (255, 126, 26))])]
    spots = []
    for k in range(26):
        spots.append((rng.uniform(0, 360), rng.uniform(-16, 70), rng.uniform(2.6, 8.0)))
    spots += [(24, 16, 20.0), (140, 34, 14.0), (250, 6, 25.0), (318, 47, 11.0), (196, 60, 9.0)]
    spots.sort(key=lambda s: s[2])
    for i, (az, alt, s) in enumerate(spots):
        p, pg = pks[i % 3]
        f = np.clip(s / 25.0, 0.12, 1.0)
        splat(rgb, glow, d, p, dirv(az, alt), s, roll_deg=rng.uniform(-14, 14),
              opacity=0.55 + 0.45 * f, glow=pg, glow_scale=2.2, glow_strength=0.34 + 0.38 * f)
    return rgb + glow


CONCEPTS = [
    ("1", "Bloedmaan", "bloodmoon", bloodmoon,
     "Reuze jack-o'-lantern als bloedmaan, donkere wolkenbanden, vleermuizen, rood-paarse lucht"),
    ("2", "Pompoen Nevel", "nebula", nebula,
     "Ruimte-nevel in oranje/paars/groen die een pompoengezicht vormt, dichte sterrenhemel"),
    ("3", "Kerkhof Nacht", "graveyard", graveyard,
     "Giftig groene lucht, mist, kale bomen + kerktoren rond de horizon, zwevende lantaarns, bleke maan"),
    ("4", "Heksenuur", "witching", witching,
     "Poster-stijl oranje horizon, zwarte wolken met gloeiende rand, volle maan, pompoenen + vleermuizen"),
    ("5", "De Leegte", "void", void,
     "Bijna zwart, paarse mistslierten, tientallen gloeiende pompoengezichten die je aanstaren"),
]
