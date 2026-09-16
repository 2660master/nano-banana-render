"""Five scarier takes on the graveyard sky, each with a dark-tinted moon."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from skylib import (fbm3, ridged, starfield, splat, pumpkin_sprite, moon_sprite,
                    bat_sprite, tree_sprite, smooth, window_glow)
from concepts import dirv, grad, clouds, soften, spire_sprite, grave_sprite, _ground


def _canvas(S, F=2):
    C = S * F
    img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img), C


def _done(img, S, glow=None):
    a = np.asarray(img.resize((S, S), Image.LANCZOS)).astype(np.float64)
    if glow is None:
        return a
    g = window_glow(np.asarray(glow.resize((S, S), Image.LANCZOS)).astype(np.float64))
    return a, g


# ------------------------------------------------------------- silhouettes --
def raven_sprite(S=256, col=(5, 5, 9), flying=False):
    img, dr, C = _canvas(S)
    cx, cy = C * 0.5, C * 0.55
    if not flying:
        dr.ellipse([cx - C * 0.115, cy - C * 0.115, cx + C * 0.115, cy + C * 0.135], fill=col)
        dr.ellipse([cx - C * 0.150, cy - C * 0.215, cx - C * 0.030, cy - C * 0.095], fill=col)
        dr.polygon([(cx - C * 0.140, cy - C * 0.170), (cx - C * 0.255, cy - C * 0.148),
                    (cx - C * 0.138, cy - C * 0.118)], fill=col)          # beak
        dr.polygon([(cx + C * 0.070, cy + C * 0.030), (cx + C * 0.280, cy + C * 0.170),
                    (cx + C * 0.225, cy + C * 0.205), (cx + C * 0.050, cy + C * 0.110)], fill=col)
        dr.polygon([(cx - C * 0.060, cy - C * 0.030), (cx + C * 0.095, cy + C * 0.055),
                    (cx + C * 0.010, cy + C * 0.110)], fill=col)          # folded wing
        for ox in (-0.045, 0.045):
            dr.line([(cx + C * ox, cy + C * 0.120), (cx + C * ox, cy + C * 0.215)],
                    fill=col, width=max(2, int(C * 0.012)))
    else:
        for w in (-1, 1):                     # seen from below: wings out to both sides
            dr.polygon([(cx + w * C * 0.035, cy - C * 0.055), (cx + w * C * 0.175, cy - C * 0.150),
                        (cx + w * C * 0.325, cy - C * 0.180), (cx + w * C * 0.455, cy - C * 0.125),
                        (cx + w * C * 0.475, cy - C * 0.045), (cx + w * C * 0.400, cy - C * 0.028),
                        (cx + w * C * 0.432, cy + C * 0.022), (cx + w * C * 0.330, cy + C * 0.006),
                        (cx + w * C * 0.342, cy + C * 0.058), (cx + w * C * 0.222, cy + C * 0.012),
                        (cx + w * C * 0.200, cy + C * 0.068), (cx + w * C * 0.055, cy + C * 0.046)],
                       fill=col)
        dr.ellipse([cx - C * 0.048, cy - C * 0.105, cx + C * 0.048, cy + C * 0.130], fill=col)
        dr.polygon([(cx - C * 0.048, cy + C * 0.095), (cx + C * 0.048, cy + C * 0.095),
                    (cx + C * 0.030, cy + C * 0.235), (cx - C * 0.030, cy + C * 0.235)], fill=col)
        dr.ellipse([cx - C * 0.040, cy - C * 0.170, cx + C * 0.040, cy - C * 0.086], fill=col)
        dr.polygon([(cx - C * 0.019, cy - C * 0.150), (cx + C * 0.019, cy - C * 0.150),
                    (cx, cy - C * 0.220)], fill=col)
    return _done(img, S)


def gallows_sprite(S=384, col=(6, 6, 10)):
    img, dr, C = _canvas(S)
    x = C * 0.30
    w = C * 0.030
    dr.rectangle([x - w, C * 0.10, x + w, C], fill=col)
    dr.rectangle([x - w, C * 0.10, C * 0.80, C * 0.10 + w * 1.7], fill=col)
    dr.polygon([(x + w, C * 0.26), (x + C * 0.20, C * 0.13), (x + C * 0.20, C * 0.175),
                (x + w, C * 0.305)], fill=col)                                   # brace
    dr.rectangle([C * 0.40, C * 0.90, C * 0.96, C], fill=col)                    # platform
    rx = C * 0.70
    dr.line([(rx, C * 0.125), (rx, C * 0.46)], fill=col, width=max(2, int(C * 0.016)))
    dr.arc([rx - C * 0.075, C * 0.44, rx + C * 0.075, C * 0.60], 0, 360,
           fill=col, width=max(3, int(C * 0.022)))                               # noose loop
    dr.line([(rx - C * 0.030, C * 0.455), (rx + C * 0.030, C * 0.455)],
            fill=col, width=max(2, int(C * 0.014)))
    return _done(img, S)


def hand_sprite(S=256, col=(8, 8, 12)):
    """A skeletal hand clawing out of the ground."""
    img, dr, C = _canvas(S)
    cx = C * 0.5
    dr.polygon([(cx - C * 0.105, C), (cx + C * 0.105, C),
                (cx + C * 0.080, C * 0.80), (cx - C * 0.085, C * 0.80)], fill=col)   # forearm
    dr.polygon([(cx - C * 0.150, C * 0.82), (cx + C * 0.145, C * 0.82),
                (cx + C * 0.175, C * 0.615), (cx + C * 0.020, C * 0.565),
                (cx - C * 0.170, C * 0.625)], fill=col)                              # palm
    fw = max(3, int(C * 0.046))
    for ox, h, bend, lift in [(-0.150, 0.30, -0.075, 0.00), (-0.072, 0.40, -0.030, 0.02),
                              (0.016, 0.44, 0.010, 0.03), (0.100, 0.37, 0.055, 0.01)]:
        x0, y0 = cx + C * ox, C * (0.63 - lift)
        dr.line([(x0, y0), (x0 + C * bend * 0.8, y0 - C * h * 0.55),
                 (x0 + C * bend * 2.1, y0 - C * h * 0.88), (x0 + C * bend * 3.4, y0 - C * h)],
                fill=col, width=fw, joint="curve")
        for t, r in ((0.55, 0.030), (0.88, 0.026), (1.0, 0.022)):
            jx = x0 + C * bend * (0.8 if t < 0.6 else 2.1 if t < 0.95 else 3.4)
            jy = y0 - C * h * t
            dr.ellipse([jx - C * r, jy - C * r, jx + C * r, jy + C * r], fill=col)
    dr.line([(cx - C * 0.150, C * 0.755), (cx - C * 0.255, C * 0.700),
             (cx - C * 0.330, C * 0.590)], fill=col, width=fw, joint="curve")        # thumb
    dr.ellipse([cx - C * 0.355, C * 0.565, cx - C * 0.305, C * 0.615], fill=col)
    dr.rectangle([0, C * 0.965, C, C], fill=col)
    return _done(img, S)


def fence_sprite(S=512, col=(6, 6, 10), bars=13):
    img, dr, C = _canvas(S)
    top, bot = C * 0.40, C
    w = max(2, int(C * 0.012))
    dr.rectangle([0, C * 0.56, C, C * 0.56 + w * 1.6], fill=col)
    dr.rectangle([0, C * 0.86, C, C * 0.86 + w * 1.6], fill=col)
    for k in range(bars):
        x = (k + 0.5) * C / bars
        dr.rectangle([x - w, top, x + w, bot], fill=col)
        dr.polygon([(x - w * 2.0, top + C * 0.035), (x + w * 2.0, top + C * 0.035),
                    (x, top - C * 0.045)], fill=col)
    for x in (C * 0.04, C * 0.96):
        dr.rectangle([x - w * 2.6, C * 0.30, x + w * 2.6, bot], fill=col)
        dr.polygon([(x - w * 4.0, C * 0.32), (x + w * 4.0, C * 0.32), (x, C * 0.245)], fill=col)
    dr.rectangle([0, C * 0.985, C, C], fill=col)
    return _done(img, S)


def scarecrow_sprite(S=384, col=(6, 6, 10), glow_eyes=(255, 150, 40)):
    img, dr, C = _canvas(S)
    glow, gdr, _ = _canvas(S)
    cx = C * 0.5
    dr.rectangle([cx - C * 0.022, C * 0.30, cx + C * 0.022, C], fill=col)
    dr.rectangle([cx - C * 0.26, C * 0.40, cx + C * 0.26, C * 0.435], fill=col)
    dr.polygon([(cx - C * 0.175, C * 0.40), (cx + C * 0.175, C * 0.40),
                (cx + C * 0.215, C * 0.70), (cx + C * 0.130, C * 0.66),
                (cx + C * 0.090, C * 0.78), (cx + C * 0.020, C * 0.68),
                (cx - C * 0.040, C * 0.80), (cx - C * 0.115, C * 0.66),
                (cx - C * 0.205, C * 0.72)], fill=col)                     # ragged coat
    for s in (-1, 1):                                                      # straw at the cuffs
        for k in range(5):
            dr.line([(cx + s * C * 0.245, C * 0.425),
                     (cx + s * C * (0.30 + 0.02 * k), C * (0.46 + 0.03 * k))],
                    fill=col, width=max(1, int(C * 0.008)))
    dr.ellipse([cx - C * 0.105, C * 0.185, cx + C * 0.105, C * 0.405], fill=col)
    dr.polygon([(cx - C * 0.20, C * 0.235), (cx + C * 0.20, C * 0.235),
                (cx + C * 0.11, C * 0.195), (cx - C * 0.11, C * 0.195)], fill=col)   # hat brim
    dr.polygon([(cx - C * 0.085, C * 0.200), (cx + C * 0.085, C * 0.200),
                (cx + C * 0.030, C * 0.105), (cx - C * 0.045, C * 0.110)], fill=col)
    for sx in (-1, 1):
        e = [cx + sx * C * 0.045 - C * 0.026, C * 0.275, cx + sx * C * 0.045 + C * 0.026, C * 0.315]
        dr.ellipse(e, fill=glow_eyes + (255,))
        gdr.ellipse(e, fill=glow_eyes + (255,))
    g = glow.filter(ImageFilter.GaussianBlur(C * 0.045))
    return _done(img, S, Image.fromarray((np.asarray(g).astype(np.float64) * 1.5)
                                         .clip(0, 255).astype(np.uint8)))


def mansion_sprite(S=512, col=(6, 6, 10), win=(240, 150, 46)):
    img, dr, C = _canvas(S)
    glow, gdr, _ = _canvas(S)
    dr.rectangle([C * 0.20, C * 0.52, C * 0.80, C], fill=col)
    dr.polygon([(C * 0.16, C * 0.52), (C * 0.84, C * 0.52), (C * 0.50, C * 0.27)], fill=col)
    dr.rectangle([C * 0.60, C * 0.30, C * 0.74, C * 0.56], fill=col)                # tower
    dr.polygon([(C * 0.565, C * 0.31), (C * 0.775, C * 0.31), (C * 0.67, C * 0.14)], fill=col)
    for x in (0.30, 0.44):                                                          # chimneys
        dr.rectangle([C * x, C * 0.30, C * (x + 0.055), C * 0.45], fill=col)
    dr.rectangle([C * 0.12, C * 0.70, C * 0.24, C], fill=col)
    dr.polygon([(C * 0.09, C * 0.70), (C * 0.27, C * 0.70), (C * 0.18, C * 0.60)], fill=col)
    for (x, y, w, h) in [(0.29, 0.62, 0.075, 0.095), (0.46, 0.62, 0.075, 0.095),
                         (0.63, 0.37, 0.070, 0.085), (0.34, 0.80, 0.065, 0.085),
                         (0.58, 0.80, 0.065, 0.085), (0.145, 0.78, 0.055, 0.070)]:
        box = [C * x, C * y, C * (x + w), C * (y + h)]
        dr.rectangle(box, fill=win + (255,))
        gdr.rectangle(box, fill=win + (255,))
    g = glow.filter(ImageFilter.GaussianBlur(C * 0.030))
    return _done(img, S, Image.fromarray((np.asarray(g).astype(np.float64) * 1.25)
                                         .clip(0, 255).astype(np.uint8)))


def eyes_sprite(S=128, col=(255, 150, 40), gap=0.30):
    """A pair of glowing eyes, for hiding in the treeline."""
    img, dr, C = _canvas(S, 3)
    glow, gdr, _ = _canvas(S, 3)
    for sx in (-1, 1):
        box = [C * (0.5 + sx * gap / 2) - C * 0.062, C * 0.452,
               C * (0.5 + sx * gap / 2) + C * 0.062, C * 0.568]
        dr.ellipse(box, fill=col + (255,))
        gdr.ellipse(box, fill=col + (255,))
    g = glow.filter(ImageFilter.GaussianBlur(C * 0.09))
    return _done(img, S, Image.fromarray((np.asarray(g).astype(np.float64) * 1.9)
                                         .clip(0, 255).astype(np.uint8)))


def ghost_sprite(S=320, col=(196, 224, 214), alpha=120):
    img, dr, C = _canvas(S)
    glow, gdr, _ = _canvas(S)
    cx = C * 0.5
    body = [(cx - C * 0.22, C * 0.40), (cx - C * 0.26, C * 0.66), (cx - C * 0.16, C * 0.60),
            (cx - C * 0.08, C * 0.74), (cx, C * 0.62), (cx + C * 0.09, C * 0.76),
            (cx + C * 0.17, C * 0.60), (cx + C * 0.26, C * 0.68), (cx + C * 0.22, C * 0.40)]
    dr.ellipse([cx - C * 0.22, C * 0.20, cx + C * 0.22, C * 0.58], fill=col + (alpha,))
    dr.polygon(body, fill=col + (alpha,))
    gdr.ellipse([cx - C * 0.22, C * 0.20, cx + C * 0.22, C * 0.58], fill=col + (255,))
    gdr.polygon(body, fill=col + (255,))
    for sx in (-1, 1):                                                   # hollow eyes
        dr.ellipse([cx + sx * C * 0.095 - C * 0.048, C * 0.315,
                    cx + sx * C * 0.095 + C * 0.048, C * 0.405], fill=(4, 8, 10, 235))
    dr.ellipse([cx - C * 0.045, C * 0.435, cx + C * 0.045, C * 0.525], fill=(4, 8, 10, 215))
    im = img.filter(ImageFilter.GaussianBlur(C * 0.008))
    g = glow.filter(ImageFilter.GaussianBlur(C * 0.075))
    return _done(im, S, Image.fromarray((np.asarray(g).astype(np.float64) * 0.55)
                                        .clip(0, 255).astype(np.uint8)))


# ------------------------------------------------------------------ moons ---
def skull_moon_sprite(S=512, disc=(150, 154, 138), dark=(28, 32, 30), tint=(1.0, 1.0, 1.0)):
    img, dr, C = _canvas(S)
    glow, gdr, _ = _canvas(S)
    R = C * 0.40
    dr.ellipse([C / 2 - R, C / 2 - R, C / 2 + R, C / 2 + R], fill=disc + (255,))
    gdr.ellipse([C / 2 - R, C / 2 - R, C / 2 + R, C / 2 + R], fill=disc + (255,))
    rng = np.random.default_rng(5)
    for _ in range(16):                                        # a few craters for texture
        a = rng.uniform(0, 2 * np.pi); rr = R * np.sqrt(rng.uniform(0, 0.85))
        x = C / 2 + np.cos(a) * rr; y = C / 2 + np.sin(a) * rr
        cr = R * rng.uniform(0.05, 0.14)
        sh = rng.uniform(0.86, 0.96)
        dr.ellipse([x - cr, y - cr, x + cr, y + cr],
                   fill=tuple(int(v * sh) for v in disc) + (255,))
    cx, cy = C / 2, C / 2
    for sx in (-1, 1):                                         # eye sockets
        dr.ellipse([cx + sx * R * 0.34 - R * 0.235, cy - R * 0.36,
                    cx + sx * R * 0.34 + R * 0.235, cy + R * 0.10], fill=dark + (255,))
    dr.polygon([(cx, cy + R * 0.02), (cx - R * 0.115, cy + R * 0.30),
                (cx + R * 0.115, cy + R * 0.30)], fill=dark + (255,))      # nasal cavity
    dr.polygon([(cx - R * 0.40, cy + R * 0.44), (cx + R * 0.40, cy + R * 0.44),
                (cx + R * 0.33, cy + R * 0.70), (cx - R * 0.33, cy + R * 0.70)],
               fill=dark + (255,))                              # jaw
    for k in range(-2, 3):                                      # chunky teeth
        x = cx + k * R * 0.145
        dr.line([(x, cy + R * 0.455), (x, cy + R * 0.69)],
                fill=tuple(int(v * 0.80) for v in disc) + (255,), width=max(3, int(C * 0.011)))
    dr.line([(cx - R * 0.375, cy + R * 0.565), (cx + R * 0.375, cy + R * 0.565)],
            fill=tuple(int(v * 0.80) for v in disc) + (255,), width=max(3, int(C * 0.010)))
    arr = np.asarray(img).astype(np.float64)
    for i in range(3):
        arr[..., i] *= tint[i]
    g1 = np.asarray(glow.filter(ImageFilter.GaussianBlur(C * 0.05))).astype(np.float64) * 0.5
    g2 = np.asarray(glow.filter(ImageFilter.GaussianBlur(C * 0.20))).astype(np.float64) * 0.95
    gi = np.clip(g1 + g2, 0, 255)
    for i in range(3):
        gi[..., i] *= tint[i]
    return _done(Image.fromarray(arr.clip(0, 255).astype(np.uint8)), S,
                 Image.fromarray(gi.astype(np.uint8)))


def eclipse_sprite(S=560, disc=(9, 6, 12), ring=(255, 120, 40), halo=(210, 70, 30)):
    img, dr, C = _canvas(S)
    glow, gdr, _ = _canvas(S)
    R = C * 0.33
    gdr.ellipse([C / 2 - R * 1.05, C / 2 - R * 1.05, C / 2 + R * 1.05, C / 2 + R * 1.05],
                fill=ring + (255,))
    ring_img = glow.filter(ImageFilter.GaussianBlur(C * 0.012))
    corona = glow.filter(ImageFilter.GaussianBlur(C * 0.075))
    wide = glow.filter(ImageFilter.GaussianBlur(C * 0.21))
    g = (np.asarray(ring_img).astype(np.float64) * 1.25 +
         np.asarray(corona).astype(np.float64) * 0.85)
    w = np.asarray(wide).astype(np.float64)
    for i in range(3):
        w[..., i] *= halo[i] / max(ring[i], 1)
    g = np.clip(g + w * 0.85, 0, 255)
    dr.ellipse([C / 2 - R, C / 2 - R, C / 2 + R, C / 2 + R], fill=disc + (255,))
    inner = np.asarray(img).astype(np.float64)
    hole = inner[..., 3] > 0
    g[hole] *= 0.10                                     # the moon itself blocks the corona
    return _done(img, S, Image.fromarray(g.clip(0, 255).astype(np.uint8)))


def watcher_sprite(S=720, iris=(122, 32, 16), rim=(228, 118, 42)):
    """A colossal eye: the moon, but looking back."""
    img, dr, C = _canvas(S)
    glow, gdr, _ = _canvas(S)
    cx, cy = C * 0.5, C * 0.5
    W, H = C * 0.44, C * 0.235
    lid = []
    for k in range(65):
        t = k / 64 * 2 - 1
        lid.append((cx + t * W, cy - H * (1 - t * t) ** 0.72))
    for k in range(65):
        t = 1 - k / 64 * 2
        lid.append((cx + t * W, cy + H * (1 - t * t) ** 0.72))
    dr.polygon(lid, fill=(168, 162, 146, 255))
    gdr.polygon(lid, fill=(120, 110, 96, 255))
    arr = np.asarray(img).astype(np.float64)
    yy, xx = np.mgrid[0:C, 0:C]
    m = arr[..., 3] > 0
    sh = np.clip(1.15 - 0.85 * np.abs((yy - cy) / H) ** 2, 0.25, 1.15)
    arr[..., :3] *= sh[..., None]
    rr = np.sqrt(((xx - cx) / (C * 0.145)) ** 2 + ((yy - cy) / (C * 0.145)) ** 2)
    ir = rr < 1.0
    ang = np.arctan2(yy - cy, xx - cx)
    fib = 0.62 + 0.38 * np.abs(np.sin(ang * 26 + rr * 6))
    for i in range(3):
        arr[..., i] = np.where(ir & m, iris[i] * fib * (1.25 - 0.55 * rr), arr[..., i])
    pu = rr < 0.40
    arr[pu & m] = [6, 4, 8, 255]
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(img)
    dr.ellipse([cx - C * 0.145, cy - C * 0.145, cx + C * 0.145, cy + C * 0.145],
               outline=(20, 8, 10, 255), width=max(3, int(C * 0.010)))
    dr.ellipse([cx - C * 0.062, cy - C * 0.072, cx - C * 0.018, cy - C * 0.030],
               fill=(232, 216, 196, 195))                                   # catchlight
    rng = np.random.default_rng(8)
    for _ in range(26):                                                     # veins
        a = rng.uniform(0, 2 * np.pi)
        x0, y0 = cx + np.cos(a) * W * 0.95, cy + np.sin(a) * H * 0.95
        x1, y1 = cx + np.cos(a) * C * 0.17, cy + np.sin(a) * C * 0.17
        pts = [(x0, y0)]
        for t in (0.35, 0.7):
            pts.append((x0 + (x1 - x0) * t + rng.uniform(-C * 0.02, C * 0.02),
                        y0 + (y1 - y0) * t + rng.uniform(-C * 0.012, C * 0.012)))
        pts.append((x1, y1))
        dr.line(pts, fill=(112, 30, 30, 205), width=max(1, int(C * 0.0035)), joint="curve")
    lid_line = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    ImageDraw.Draw(lid_line).polygon(lid, outline=rim + (200,), width=max(3, int(C * 0.009)))
    img = Image.alpha_composite(img, lid_line)
    g = glow.filter(ImageFilter.GaussianBlur(C * 0.10))
    g = np.asarray(g).astype(np.float64) * 1.1
    return _done(img, S, Image.fromarray(g.clip(0, 255).astype(np.uint8)))


def web_sprite(S=640, col=(206, 212, 214), spokes=12, rings=7):
    img, dr, C = _canvas(S)
    ox, oy = C * 0.06, C * 0.06
    w = max(1, int(C * 0.0035))
    R = C * 1.02
    ends = []
    for k in range(spokes + 1):
        a = np.pi / 2 * k / spokes
        ends.append((ox + np.cos(a) * R, oy + np.sin(a) * R))
        dr.line([(ox, oy), ends[-1]], fill=col + (150,), width=w)
    for r in range(1, rings + 1):
        t = (r / rings) ** 1.35
        pts = []
        for k in range(spokes + 1):
            a = np.pi / 2 * k / spokes
            sag = 1.0 - 0.055 * np.sin(np.pi * (k / spokes))
            pts.append((ox + np.cos(a) * R * t * sag, oy + np.sin(a) * R * t * sag))
        dr.line(pts, fill=col + (130,), width=w, joint="curve")
    sx, sy = ox + C * 0.40, oy + C * 0.44
    b = C * 0.030
    dr.line([(ox, oy), (sx, sy - b * 2.6)], fill=col + (120,), width=w)
    dr.ellipse([sx - b, sy - b * 1.25, sx + b, sy + b * 1.25], fill=(8, 6, 10, 255))
    dr.ellipse([sx - b * 0.55, sy - b * 2.1, sx + b * 0.55, sy - b * 0.9], fill=(8, 6, 10, 255))
    for s in (-1, 1):
        for k, (a1, a2) in enumerate([(0.55, 1.15), (0.20, 0.75), (-0.20, 0.35), (-0.55, -0.05)]):
            j1 = (sx + s * b * 2.4 * np.cos(a1), sy - b * 2.2 * np.sin(a1))
            j2 = (sx + s * b * 4.4 * np.cos(a2), sy - b * 1.2 * np.sin(a2) + b * 1.6)
            dr.line([(sx + s * b * 0.5, sy), j1, j2], fill=(8, 6, 10, 255),
                    width=max(2, int(C * 0.006)), joint="curve")
    return _done(img, S)


def lightning_sprite(S=512, col=(210, 232, 255), seed=1):
    img, dr, C = _canvas(S)
    glow, gdr, _ = _canvas(S)
    rng = np.random.default_rng(seed)

    def bolt(x, y, ang, length, w, depth, draws):
        if depth == 0 or length < C * 0.02:
            return
        nx = x + np.cos(ang) * length
        ny = y + np.sin(ang) * length
        for d in draws:
            d.line([(x, y), (nx, ny)], fill=col + (255,), width=max(1, int(w)))
        bolt(nx, ny, ang + rng.uniform(-0.62, 0.62), length * rng.uniform(0.74, 0.96),
             w * 0.88, depth - 1, draws)
        if rng.random() < 0.55:
            bolt(nx, ny, ang + rng.uniform(-1.2, 1.2), length * rng.uniform(0.3, 0.55),
                 w * 0.5, max(depth - 2, 0), draws)
    bolt(C * 0.5, 0, np.pi / 2 + rng.uniform(-0.30, 0.30), C * 0.115, C * 0.024, 13, [dr, gdr])
    g = np.asarray(glow.filter(ImageFilter.GaussianBlur(C * 0.012))).astype(np.float64) * 1.15
    g += np.asarray(glow.filter(ImageFilter.GaussianBlur(C * 0.045))).astype(np.float64) * 0.75
    return _done(img, S, Image.fromarray(g.clip(0, 255).astype(np.uint8)))


# ================================================================== scenes ==
_CACHE = {}


def cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


def horizon_ring(rgb, glow, d, pal, seed=4, gallows=1, hands=9, scarecrows=2,
                 mansion=True, spire=True, eyes=14, ravens=8, fences=5):
    """The graveyard silhouette band: two depth layers of props all around the player."""
    rng = np.random.default_rng(seed)
    far, near = pal["far"], pal["near"]
    far_trees = [cached(("ft", far, s), lambda s=s: tree_sprite(340, col=far, seed=s)) for s in range(4)]
    trees = [cached(("nt", near, s), lambda s=s: tree_sprite(460, col=near, seed=s)) for s in range(6)]
    fgrave = cached(("fg", far), lambda: grave_sprite(240, col=far))
    ngrave = cached(("ng", near), lambda: grave_sprite(280, col=near))
    ffence = cached(("ff", far), lambda: fence_sprite(440, col=far))
    nfence = cached(("nf", near), lambda: fence_sprite(512, col=near))
    hand = cached(("hd", near), lambda: hand_sprite(256, col=near))
    perched = cached(("rv", near), lambda: raven_sprite(224, col=near))
    eyepair = cached(("ey", pal["eyes"]), lambda: eyes_sprite(128, col=pal["eyes"]))

    for k in range(30):                                     # far, hazed-out ring
        az = k * 12 + rng.uniform(-5, 5)
        size = rng.uniform(9, 15)
        splat(rgb, glow, d, far_trees[k % 4], dirv(az, _ground(size, 4.5)), size, opacity=0.62)
    for k in range(14):
        size = rng.uniform(5, 8)
        splat(rgb, glow, d, fgrave, dirv(rng.uniform(0, 360), _ground(size, 3.0)), size, opacity=0.55)
    for k in range(fences):
        size = rng.uniform(13, 19)
        splat(rgb, glow, d, ffence, dirv(rng.uniform(0, 360), _ground(size, 6.0)), size, opacity=0.5)
    if spire:
        splat(rgb, glow, d, cached(("fs", far), lambda: spire_sprite(420, col=far, win=(150, 100, 40))),
              dirv(96, _ground(20.0, 5.0)), 20.0, opacity=0.70)

    for k in range(fences):                                 # near, solid black
        size = rng.uniform(16, 24)
        splat(rgb, glow, d, nfence, dirv(rng.uniform(0, 360), _ground(size, 7.0)), size)
    for k in range(18):
        size = rng.uniform(7, 13)
        splat(rgb, glow, d, ngrave, dirv(rng.uniform(0, 360), _ground(size, 2.2)), size)
    for k in range(hands):
        size = rng.uniform(4, 7.5)
        splat(rgb, glow, d, hand, dirv(rng.uniform(0, 360), _ground(size, 1.6)), size,
              roll_deg=rng.uniform(-9, 9))
    for k in range(24):
        az = k * 15 + rng.uniform(-6, 6)
        size = rng.uniform(16, 30)
        splat(rgb, glow, d, trees[k % 6], dirv(az, _ground(size, 3.2)), size,
              roll_deg=rng.uniform(-pal.get("lean", 0), pal.get("lean", 0)))
    for k in range(gallows):
        size = rng.uniform(21, 27)
        splat(rgb, glow, d, cached(("gl", near), lambda: gallows_sprite(384, col=near)),
              dirv(28 + k * 165 + rng.uniform(-20, 20), _ground(size, 4.0)), size)
    for k in range(scarecrows):
        size = rng.uniform(15, 20)
        spr, gl = cached(("sc", near, pal["eyes"]),
                         lambda: scarecrow_sprite(384, col=near, glow_eyes=pal["eyes"]))
        splat(rgb, glow, d, spr, dirv(212 + k * 97 + rng.uniform(-25, 25), _ground(size, 3.0)),
              size, glow=gl, glow_scale=2.4, glow_strength=0.55)
    if mansion:
        spr, gl = cached(("mn", near), lambda: mansion_sprite(512, col=near))
        splat(rgb, glow, d, spr, dirv(152, _ground(30.0, 5.0)), 30.0,
              glow=gl, glow_scale=2.2, glow_strength=0.45)
    if spire:
        splat(rgb, glow, d, cached(("ns", near), lambda: spire_sprite(560, col=near)),
              dirv(305, _ground(34.0, 4.0)), 34.0)
    for k in range(ravens):                                 # crows perched in the branches
        size = rng.uniform(2.4, 4.2)
        splat(rgb, glow, d, perched, dirv(rng.uniform(0, 360), rng.uniform(2.0, 11.0)), size,
              roll_deg=rng.uniform(-6, 6))
    spr, gl = eyepair
    for k in range(eyes):                                   # something watching from the dark
        size = rng.uniform(1.1, 2.3)
        splat(rgb, glow, d, spr, dirv(rng.uniform(0, 360), rng.uniform(-1.5, 7.0)), size,
              roll_deg=rng.uniform(-7, 7), glow=gl, glow_scale=3.0, glow_strength=0.75)


def lanterns(rgb, glow, d, pal, spots, seed=1):
    pks = [cached(("pk", pal["lantern"], i),
                  lambda i=i: pumpkin_sprite(320, face_style=i, body=pal["lantern"][0],
                                             dark=pal["lantern"][1], glowcol=pal["lantern"][2],
                                             halo=pal["lantern"][3], seed=i)) for i in range(5)]
    for i, (az, alt, s) in enumerate(spots):
        p, pg = pks[i % 5]
        splat(rgb, glow, d, p, dirv(az, alt), s, roll_deg=(i * 37) % 21 - 10,
              glow=pg, glow_scale=2.5, glow_strength=0.62)


def base_sky(d, pal, star_seed=17):
    y = d[..., 1]
    rgb = grad(y, pal["grad"])
    rgb += starfield(d, 54, 0.16, 0.095, seed=star_seed, warm=pal.get("star_warm", 0.1),
                     bright=pal.get("star_bright", 0.78))
    rgb += starfield(d, 104, 0.12, 0.055, seed=star_seed + 44, warm=0.0,
                     bright=pal.get("star_bright", 0.78) * 0.5)
    return rgb


def ground_mist(rgb, d, pal, seed=94, gain=0.80, width=0.075):
    y = d[..., 1]
    m = np.exp(-((y + 0.005) / width) ** 2) * (0.45 + 0.75 * fbm3(d * 5.2, 5, seed=seed))
    rgb += np.array(pal["mist"]) * np.clip(m, 0, 1.3)[..., None] * gain


LANTERN_SPOTS = [(12, 9.5, 7.0), (58, 13.0, 5.0), (96, 7.5, 6.0), (143, 15.5, 4.2),
                 (188, 8.5, 7.4), (222, 14.0, 4.6), (263, 10.0, 5.6), (300, 17.0, 3.6),
                 (338, 8.0, 5.0), (75, 21.0, 2.8), (250, 23.0, 2.4), (170, 25.0, 2.0),
                 (20, 19.0, 3.2), (120, 11.0, 3.8), (285, 5.5, 4.4), (208, 30.0, 1.9)]


# ------------------------------------------------------------ A. BLOEDMAAN --
PAL_BLOOD = dict(
    grad=[(-1.0, (0.010, 0.004, 0.006)), (-0.06, (0.048, 0.014, 0.014)),
          (0.03, (0.175, 0.032, 0.026)), (0.13, (0.105, 0.020, 0.030)),
          (0.45, (0.030, 0.008, 0.030)), (1.0, (0.012, 0.004, 0.018))],
    mist=(0.150, 0.045, 0.040), far=(38, 16, 18), near=(6, 4, 6),
    eyes=(255, 66, 30), star_warm=0.85, star_bright=0.55,
    lantern=((198, 84, 20), (104, 36, 8), (255, 196, 110), (255, 96, 20)))


def blood(d):
    rgb = base_sky(d, PAL_BLOOD, star_seed=17)
    y = d[..., 1]
    glow = np.zeros_like(rgb)
    mc = np.array(dirv(318, 31))
    hal = np.clip(d @ mc, 0, 1)
    rgb += np.array([0.62, 0.075, 0.045]) * (hal ** 24)[..., None] * 0.55
    m, mg = moon_sprite(512, col=(126, 30, 24), tint=(1.0, 0.92, 0.92))
    splat(rgb, glow, d, m, mc, 13.5, glow=mg, glow_scale=2.8, glow_strength=0.40)
    c = clouds(d, 2.3, 2.5, seed=71)
    veil = smooth(c, 0.44, 0.76) * (1 - smooth(y, 0.60, 0.98))
    rgb = rgb * (1 - veil[..., None] * 0.55) + \
        grad(y, [(-0.1, (0.055, 0.014, 0.014)), (0.5, (0.030, 0.008, 0.016))]) * (veil[..., None] * 0.55)
    edge = smooth(c, 0.415, 0.450) * (1 - smooth(c, 0.450, 0.495))
    rgb += np.array([0.85, 0.12, 0.05]) * (edge * (0.22 + 1.0 * hal ** 2))[..., None] * 0.34
    streak = smooth(clouds(d, 4.6, 1.4, seed=133, octaves=5), 0.60, 0.92) * smooth(y, 0.05, 0.55)
    rgb += np.array([0.45, 0.05, 0.06]) * streak[..., None] * 0.35
    ground_mist(rgb, d, PAL_BLOOD, gain=0.85)
    horizon_ring(rgb, glow, d, PAL_BLOOD, seed=4, gallows=2, hands=12, scarecrows=1, eyes=16)
    lanterns(rgb, glow, d, PAL_BLOOD, LANTERN_SPOTS[:12])
    fly = raven_sprite(224, col=(5, 4, 6), flying=True)
    rng = np.random.default_rng(31)
    for k in range(26):
        az = 318 + rng.uniform(-70, 70) if k < 16 else rng.uniform(0, 360)
        splat(rgb, glow, d, fly, dirv(az, rng.uniform(8, 46)), rng.uniform(1.8, 5.2),
              roll_deg=rng.uniform(-30, 30), opacity=0.95)
    return rgb + glow


# --------------------------------------------------------- B. VERDUISTERING --
PAL_ECLIPSE = dict(
    grad=[(-1.0, (0.006, 0.006, 0.012)), (-0.06, (0.022, 0.030, 0.040)),
          (0.03, (0.052, 0.086, 0.094)), (0.13, (0.034, 0.042, 0.072)),
          (0.45, (0.014, 0.012, 0.038)), (1.0, (0.006, 0.005, 0.020))],
    mist=(0.055, 0.130, 0.150), far=(22, 34, 44), near=(5, 5, 9),
    eyes=(120, 240, 255), star_warm=0.0, star_bright=1.15,
    lantern=((196, 96, 24), (104, 40, 10), (255, 214, 128), (255, 124, 30)))


def eclipse(d):
    rgb = base_sky(d, PAL_ECLIPSE, star_seed=23)
    y = d[..., 1]
    glow = np.zeros_like(rgb)
    mc = np.array(dirv(318, 35))
    hal = np.clip(d @ mc, 0, 1)
    rgb += np.array([0.55, 0.20, 0.10]) * (hal ** 20)[..., None] * 0.30
    rgb += np.array([0.10, 0.06, 0.16]) * (hal ** 3)[..., None] * 0.12
    spr, gl = eclipse_sprite(560)
    splat(rgb, glow, d, spr, mc, 12.0, glow=gl, glow_scale=3.2, glow_strength=1.05)
    web = web_sprite(680)
    splat(rgb, glow, d, web, dirv(72, 46), 82.0, roll_deg=-14, opacity=0.34)
    veil = smooth(clouds(d, 3.1, 2.0, seed=91), 0.52, 0.86) * (1 - smooth(y, 0.55, 0.98))
    rgb = rgb * (1 - veil[..., None] * 0.32) + np.array([0.030, 0.050, 0.062]) * (veil[..., None] * 0.32)
    ground_mist(rgb, d, PAL_ECLIPSE, gain=0.72, width=0.062)
    horizon_ring(rgb, glow, d, PAL_ECLIPSE, seed=9, gallows=1, hands=8, scarecrows=2, eyes=24)
    lanterns(rgb, glow, d, PAL_ECLIPSE, LANTERN_SPOTS[:11])
    gspr, ggl = ghost_sprite(320, col=(180, 230, 236), alpha=105)
    rng = np.random.default_rng(12)
    for k in range(5):
        splat(rgb, glow, d, gspr, dirv(rng.uniform(0, 360), rng.uniform(4, 14)),
              rng.uniform(4.5, 8.0), glow=ggl, glow_scale=2.4, glow_strength=0.40)
    return rgb + glow


# --------------------------------------------------------- C. SCHEDELMAAN ---
PAL_SKULL = dict(
    grad=[(-1.0, (0.008, 0.011, 0.010)), (-0.06, (0.030, 0.048, 0.040)),
          (0.03, (0.082, 0.125, 0.092)), (0.13, (0.046, 0.072, 0.070)),
          (0.45, (0.017, 0.026, 0.048)), (1.0, (0.006, 0.011, 0.028))],
    mist=(0.105, 0.200, 0.150), far=(24, 44, 38), near=(6, 8, 9),
    eyes=(170, 255, 190), star_warm=0.05, star_bright=0.62,
    lantern=((198, 96, 22), (104, 40, 10), (255, 212, 124), (255, 120, 28)))


def skull(d):
    rgb = base_sky(d, PAL_SKULL, star_seed=51)
    y = d[..., 1]
    glow = np.zeros_like(rgb)
    mc = np.array(dirv(318, 17))
    hal = np.clip(d @ mc, 0, 1)
    rgb += np.array([0.34, 0.44, 0.34]) * (hal ** 16)[..., None] * 0.30
    spr, gl = skull_moon_sprite(640, disc=(104, 112, 94), dark=(14, 18, 16), tint=(0.80, 0.92, 0.78))
    splat(rgb, glow, d, spr, mc, 30.0, glow=gl, glow_scale=2.4, glow_strength=0.34)
    veil = smooth(clouds(d, 2.5, 2.3, seed=71), 0.44, 0.76) * (1 - smooth(y, 0.55, 0.95))
    rgb = rgb * (1 - veil[..., None] * 0.48) + \
        grad(y, [(-0.1, (0.040, 0.070, 0.058)), (0.5, (0.024, 0.038, 0.056))]) * (veil[..., None] * 0.48)
    aur = ridged(d * np.array([1.6, 5.5, 1.6]), 5, seed=311)
    rgb += np.array([0.10, 0.44, 0.24]) * (smooth(aur, 0.58, 0.97) * smooth(y, 0.12, 0.62)
                                           * (1 - smooth(y, 0.72, 1.0)))[..., None] * 0.42
    ground_mist(rgb, d, PAL_SKULL, gain=1.05, width=0.095)
    horizon_ring(rgb, glow, d, PAL_SKULL, seed=14, gallows=1, hands=10, scarecrows=3, eyes=14)
    lanterns(rgb, glow, d, PAL_SKULL, LANTERN_SPOTS[:13])
    gspr, ggl = ghost_sprite(320, col=(198, 228, 210), alpha=118)
    rng = np.random.default_rng(21)
    for k in range(11):
        splat(rgb, glow, d, gspr, dirv(rng.uniform(0, 360), rng.uniform(2.5, 13.0)),
              rng.uniform(4.0, 9.0), roll_deg=rng.uniform(-10, 10),
              glow=ggl, glow_scale=2.4, glow_strength=0.45)
    perch = raven_sprite(224, col=(6, 8, 9))
    for k in range(6):
        splat(rgb, glow, d, perch, dirv(rng.uniform(0, 360), rng.uniform(3, 12)),
              rng.uniform(2.4, 4.0), roll_deg=rng.uniform(-6, 6))
    fly = raven_sprite(224, col=(6, 8, 9), flying=True)
    for k in range(14):
        az = 318 + rng.uniform(-60, 60) if k < 8 else rng.uniform(0, 360)
        splat(rgb, glow, d, fly, dirv(az, rng.uniform(12, 52)), rng.uniform(1.6, 4.4),
              roll_deg=rng.uniform(-30, 30), opacity=0.94)
    return rgb + glow


# --------------------------------------------------------------- D. ONWEER --
PAL_STORM = dict(
    grad=[(-1.0, (0.006, 0.008, 0.011)), (-0.06, (0.026, 0.034, 0.044)),
          (0.03, (0.060, 0.080, 0.096)), (0.13, (0.034, 0.044, 0.062)),
          (0.45, (0.013, 0.016, 0.030)), (1.0, (0.005, 0.007, 0.018))],
    mist=(0.070, 0.105, 0.135), far=(24, 32, 40), near=(5, 6, 8),
    eyes=(190, 235, 255), star_warm=0.0, star_bright=0.35, lean=9,
    lantern=((196, 92, 22), (100, 38, 10), (255, 208, 120), (255, 116, 26)))


def storm(d):
    rgb = base_sky(d, PAL_STORM, star_seed=67)
    y = d[..., 1]
    glow = np.zeros_like(rgb)
    mc = np.array(dirv(292, 42))
    m, mg = moon_sprite(512, col=(76, 88, 72), tint=(0.86, 1.0, 0.86))
    splat(rgb, glow, d, m, mc, 10.0, glow=mg, glow_scale=2.6, glow_strength=0.30)
    c = clouds(d, 1.65, 2.7, seed=101, octaves=6, warp=0.65)
    body = smooth(c, 0.455, 0.60) * (1 - smooth(y, 0.75, 1.0) * 0.30)
    cl = grad(y, [(-0.2, (0.030, 0.038, 0.048)), (0.2, (0.020, 0.026, 0.036)),
                  (0.8, (0.012, 0.015, 0.026))])
    rgb = rgb * (1 - body[..., None] * 0.95) + cl * (body[..., None] * 0.95)
    edge = smooth(c, 0.430, 0.458) * (1 - smooth(c, 0.458, 0.495))
    rgb += np.array([0.42, 0.56, 0.72]) * edge[..., None] * 0.40
    rgb += np.array([0.30, 0.40, 0.58]) * (smooth(clouds(d, 3.4, 1.7, seed=141, octaves=5), 0.62, 0.94)
                                           * smooth(y, 0.02, 0.5))[..., None] * 0.25
    rng = np.random.default_rng(77)
    for k, (az, alt, s, seed) in enumerate([(24, 32, 34.0, 3), (146, 38, 29.0, 9), (263, 28, 25.0, 17)]):
        lspr, lgl = lightning_sprite(512, col=(206, 228, 255), seed=seed)
        rgb += np.array([0.10, 0.16, 0.30]) * np.clip(
            (d @ np.array(dirv(az, alt))) ** 12, 0, 1)[..., None] * 0.55
        splat(rgb, glow, d, lspr, dirv(az, alt), s, glow=lgl, glow_scale=2.0, glow_strength=0.85)
    ground_mist(rgb, d, PAL_STORM, gain=0.80, width=0.070)
    horizon_ring(rgb, glow, d, PAL_STORM, seed=27, gallows=1, hands=10, scarecrows=2, eyes=12)
    lanterns(rgb, glow, d, PAL_STORM, LANTERN_SPOTS[:10])
    bat = bat_sprite(224)
    for k in range(34):
        splat(rgb, glow, d, bat, dirv(rng.uniform(0, 360), rng.uniform(6, 50)),
              rng.uniform(1.6, 4.8), roll_deg=rng.uniform(-35, 35), opacity=0.95)
    return rgb + glow


# ----------------------------------------------------------- E. DE WACHTER --
PAL_WATCH = dict(
    grad=[(-1.0, (0.005, 0.003, 0.008)), (-0.06, (0.022, 0.012, 0.034)),
          (0.03, (0.050, 0.026, 0.070)), (0.13, (0.032, 0.016, 0.056)),
          (0.45, (0.013, 0.007, 0.030)), (1.0, (0.005, 0.003, 0.016))],
    mist=(0.090, 0.045, 0.135), far=(30, 20, 44), near=(5, 4, 8),
    eyes=(255, 158, 44), star_warm=0.15, star_bright=0.50,
    lantern=((198, 92, 22), (100, 38, 10), (255, 210, 122), (255, 118, 26)))


def watcher(d):
    rgb = base_sky(d, PAL_WATCH, star_seed=88)
    y = d[..., 1]
    glow = np.zeros_like(rgb)
    w1 = ridged(d * 1.7, 6, seed=203)
    w2 = fbm3(d * 3.2, 6, seed=229)
    tent = np.clip(smooth(w1, 0.50, 0.97) * smooth(w2, 0.28, 0.82), 0, 1)
    rgb += np.array([0.26, 0.070, 0.38]) * tent[..., None] * 0.62
    rgb += np.array([0.32, 0.10, 0.03]) * (smooth(w2, 0.66, 0.99) * smooth(w1, 0.35, 0.85))[..., None] * 0.45
    ec = np.array(dirv(318, 33))
    hal = np.clip(d @ ec, 0, 1)
    rgb += np.array([0.50, 0.16, 0.06]) * (hal ** 10)[..., None] * 0.28
    spr, gl = watcher_sprite(760)
    splat(rgb, glow, d, spr, ec, 44.0, roll_deg=-6, glow=gl, glow_scale=2.0, glow_strength=0.38)
    ground_mist(rgb, d, PAL_WATCH, gain=0.78, width=0.068)
    horizon_ring(rgb, glow, d, PAL_WATCH, seed=33, gallows=1, hands=11, scarecrows=2, eyes=20)
    lanterns(rgb, glow, d, PAL_WATCH, LANTERN_SPOTS[:10])
    espr, egl = eyes_sprite(128, col=(255, 150, 40))
    rng = np.random.default_rng(45)
    for k in range(26):                                   # eyes opening all over the sky
        splat(rgb, glow, d, espr, dirv(rng.uniform(0, 360), rng.uniform(6, 70)),
              rng.uniform(1.0, 3.2), roll_deg=rng.uniform(-25, 25),
              glow=egl, glow_scale=3.0, glow_strength=0.70)
    gspr, ggl = ghost_sprite(320, col=(214, 196, 236), alpha=100)
    for k in range(6):
        splat(rgb, glow, d, gspr, dirv(rng.uniform(0, 360), rng.uniform(3, 15)),
              rng.uniform(4.0, 7.5), glow=ggl, glow_scale=2.4, glow_strength=0.40)
    return rgb + glow


SCARY = [
    ("S1", "Bloedmaan", "s_blood", blood,
     "Donkerrode bloedmaan, roodverlichte wolken, galg, zwerm kraaien, rode ogen in het duister"),
    ("S2", "Verduistering", "s_eclipse", eclipse,
     "Zwarte maan met brandende ring, reuzenspinnenweb, ijskoude ogen tussen de bomen, geesten"),
    ("S3", "Schedelmaan", "s_skull", skull,
     "Reusachtige schedelmaan laag boven het kerkhof, dikke mist, vogelverschrikkers, spoken"),
    ("S4", "Onweer", "s_storm", storm,
     "Zwart onweer, bliksem in drie richtingen, dode maan achter de wolken, vleermuiszwerm"),
    ("S5", "De Wachter", "s_watcher", watcher,
     "Een kolossaal oog in plaats van de maan, paarse tentakelwolken, tientallen ogen die opengaan"),
]
