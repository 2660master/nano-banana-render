# -*- coding: utf-8 -*-
"""Rendert een voorbeeldbeeld van de lucht, zodat je ziet hoe zon, maan en
wolken er in het spel uit gaan zien in plaats van alleen de platte bestanden.

De wolken worden in perspectief op een vlak boven de speler geprojecteerd,
net als in het spel: hoe dichter bij de horizon, hoe verder weg. De heuvels
staan in drie lagen die naar achteren toe in de nevel oplossen.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import build as B
import sky

W, H = 700, 340
HORIZON = int(H * 0.66)
CLOUD_H = 120.0
FOV = math.radians(35)


def gradient(stops):
    """stops: lijst van (positie 0-1, kleur)."""
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = (t - p0) / max(1e-6, p1 - p0)
                c = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
                break
        else:
            c = stops[-1][1]
        for x in range(W):
            px[x, y] = c
    return im


def project_clouds(base, cloud_img, tint, offset=0.0, strength=1.0):
    cl = np.asarray(cloud_img.convert("RGBA"), dtype=np.float32)
    ch, cw = cl.shape[:2]
    out = np.asarray(base.convert("RGB"), dtype=np.float32).copy()
    for y in range(0, HORIZON):
        ang = (HORIZON - y) / HORIZON * FOV
        if ang < 0.006:
            continue
        dist = CLOUD_H / math.tan(ang)
        if dist > 4000:
            continue
        fade = max(0.0, min(1.0, 1.0 - (dist / 2600) ** 1.4)) * strength
        if fade <= 0.01:
            continue
        xs = np.arange(W, dtype=np.float32)
        wx = (xs - W / 2) / W * dist * 2.0 * math.tan(FOV)
        u = np.mod(wx * 0.16, cw).astype(np.int32)
        v = int((dist * 0.16 + offset) % ch)
        a = cl[v, u, 3] / 255.0 * fade
        col = np.array(tint, dtype=np.float32)
        out[y] = out[y] * (1 - a[:, None]) + col * a[:, None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def paste_disc(base, disc, cx, cy, size, glow):
    """Hemellichaam met een zachte krans eromheen."""
    R = size * 2
    g = Image.new("RGBA", (R * 2, R * 2), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for r in range(R, 0, -1):
        a = int(glow[3] * (1 - r / R) ** 2.4)
        gd.ellipse([R - r, R - r, R + r, R + r], fill=(glow[0], glow[1], glow[2], a))
    box = (cx - R, cy - R, cx + R, cy + R)
    patch = base.crop(box).convert("RGBA")
    base.paste(Image.alpha_composite(patch, g), box[:2])
    d = disc.convert("RGBA").resize((size, size), Image.NEAREST)
    base.paste(d, (cx - size // 2, cy - size // 2), d)
    return base


def birds(im, col, flock=((0.18, 0.22, 7), (0.24, 0.28, 5), (0.30, 0.19, 6),
                          (0.58, 0.15, 8), (0.64, 0.21, 5), (0.70, 0.13, 4),
                          (0.45, 0.30, 4), (0.50, 0.25, 6))):
    """Vogels als kleine v-vormen; verder weg is kleiner en vager."""
    d = ImageDraw.Draw(im, "RGBA")
    for fx, fy, size in flock:
        x, y = fx * W, fy * H
        a = int(70 + size * 20)
        w = size
        d.line([(x - w, y), (x - w * 0.4, y - w * 0.55), (x, y - w * 0.15)],
               fill=col + (a,), width=1)
        d.line([(x, y - w * 0.15), (x + w * 0.4, y - w * 0.55), (x + w, y)],
               fill=col + (a,), width=1)
    return im


def hills(im, layers):
    """Heuvellagen; de verste lossen op in de nevel."""
    d = ImageDraw.Draw(im, "RGBA")
    for li, (col, amp, base_y, alpha, step) in enumerate(layers):
        pts = []
        for i in range(W // step + 2):
            x = i * step
            hy = base_y + amp * math.sin(i * 0.34 + li * 1.7) \
                 + amp * 0.45 * math.sin(i * 0.11 + li * 0.6)
            pts.append((x, hy))
        poly = pts + [(W, H), (0, H)]
        d.polygon(poly, fill=col + (alpha,))
    return im


def trees(im, col, ys, n=7):
    d = ImageDraw.Draw(im, "RGBA")
    for i in range(n):
        x = int((i + 0.5) * W / n) + (i % 3) * 9
        y = ys + (i % 4) * 4
        d.rectangle([x + 3, y - 20, x + 6, y], fill=(46, 34, 22, 255))
        d.ellipse([x - 9, y - 36, x + 18, y - 12], fill=col + (255,))
        d.ellipse([x - 4, y - 44, x + 13, y - 27], fill=col + (255,))
    return im


def panel_dawn():
    im = gradient([(0.0, (58, 78, 128)), (0.42, (196, 134, 118)),
                   (0.62, (244, 186, 120)), (1.0, (252, 214, 150))]).convert("RGBA")
    im = project_clouds(im, sky.clouds(), (255, 196, 158), offset=90).convert("RGBA")
    im = paste_disc(im, sky.sun(), int(W * 0.22), int(H * 0.56), 44, (255, 176, 104, 150))
    im = birds(im, (58, 44, 40))
    im = hills(im, [((122, 118, 140), 12, HORIZON - 26, 180, 14),
                    ((78, 84, 92), 14, HORIZON - 10, 220, 12),
                    ((40, 52, 40), 16, HORIZON + 4, 255, 10)])
    return trees(im, (32, 44, 30), HORIZON + 4)


def panel_day():
    im = gradient([(0.0, (86, 146, 226)), (0.55, (140, 186, 236)),
                   (1.0, (196, 220, 238))]).convert("RGBA")
    im = project_clouds(im, sky.clouds(), (252, 252, 248)).convert("RGBA")
    im = paste_disc(im, sky.sun(), int(W * 0.74), int(H * 0.17), 52, (255, 220, 130, 130))
    im = birds(im, (46, 52, 58))
    im = hills(im, [((150, 176, 196), 12, HORIZON - 26, 175, 14),
                    ((94, 126, 106), 14, HORIZON - 10, 225, 12),
                    ((52, 88, 44), 16, HORIZON + 4, 255, 10)])
    return trees(im, (40, 74, 36), HORIZON + 4)


def panel_dusk():
    im = gradient([(0.0, (32, 40, 78)), (0.40, (128, 82, 118)),
                   (0.60, (220, 126, 92)), (1.0, (240, 168, 108))]).convert("RGBA")
    im = project_clouds(im, sky.clouds(), (206, 132, 128), offset=160).convert("RGBA")
    im = paste_disc(im, sky.sun(), int(W * 0.78), int(H * 0.58), 46, (255, 148, 88, 155))
    im = birds(im, (30, 24, 30))
    im = hills(im, [((104, 88, 118), 12, HORIZON - 26, 180, 14),
                    ((62, 56, 74), 14, HORIZON - 10, 225, 12),
                    ((26, 34, 30), 16, HORIZON + 4, 255, 10)])
    return trees(im, (20, 30, 24), HORIZON + 4)


def panel_night():
    im = gradient([(0.0, (6, 9, 26)), (0.55, (16, 22, 48)),
                   (1.0, (34, 44, 74))]).convert("RGBA")
    d = ImageDraw.Draw(im)
    rs = np.random.default_rng(7)
    for _ in range(220):
        x, y = int(rs.random() * W), int(rs.random() * HORIZON)
        b = 110 + int(rs.random() * 145)
        d.point((x, y), fill=(b, b, min(255, b + 14)))
        if rs.random() > 0.94:
            d.point((x + 1, y), fill=(b // 2, b // 2, b // 2))
    im = project_clouds(im, sky.clouds(), (86, 96, 124), offset=40, strength=0.75).convert("RGBA")
    ph = sky.moon_phases()
    fs = ph.height // 2                      # één fase is een halve velhoogte
    moon = ph.crop((0, 0, fs, fs))
    im = paste_disc(im, moon, int(W * 0.24), int(H * 0.16), 48, (198, 212, 228, 95))
    im = birds(im, (10, 12, 20), flock=((0.60, 0.20, 6), (0.66, 0.25, 4), (0.72, 0.17, 5)))
    im = hills(im, [((44, 52, 78), 12, HORIZON - 26, 170, 14),
                    ((24, 30, 46), 14, HORIZON - 10, 220, 12),
                    ((10, 16, 16), 16, HORIZON + 4, 255, 10)])
    return trees(im, (8, 14, 12), HORIZON + 4)


def panel_end():
    src = sky.end_sky()
    step = src.width * 2                    # twee keer vergroot, zoals je het ziet
    tile = src.resize((step, step), Image.NEAREST)
    im = Image.new("RGBA", (W, H))
    for y in range(0, H, step):
        for x in range(0, W, step):
            im.paste(tile, (x, y))
    d = ImageDraw.Draw(im)
    for cx, cy, rw, rh in ((W * 0.28, H * 0.60, 150, 24), (W * 0.70, H * 0.42, 108, 18),
                           (W * 0.52, H * 0.80, 190, 28)):
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(214, 216, 158, 255))
        d.ellipse([cx - rw * 0.9, cy, cx + rw * 0.9, cy + rh * 2.4], fill=(172, 174, 120, 255))
    return im


def main():
    panels = [("Ochtend", panel_dawn()), ("Dag", panel_day()),
              ("Avond", panel_dusk()), ("Nacht", panel_night()),
              ("The End", panel_end())]
    f_t = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 31)
    f_l = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
    f_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    PAD, TOP = 26, 140
    canvas = Image.new("RGB", (PAD * 2 + W, TOP + len(panels) * (H + 46) + 16), (24, 30, 26))
    d = ImageDraw.Draw(canvas)
    d.text((PAD, 28), "Verdant \u2014 zo ziet de lucht eruit", font=f_t, fill=(232, 240, 228))
    d.text((PAD, 70), "Zon, maan en wolken uit het pack, in perspectief gezet zoals het spel ze tekent.",
           font=f_s, fill=(140, 197, 94))
    d.text((PAD, 90), "De vogels op deze tekening laten het idee zien \u2014 in het spel vliegen papegaaien, vleermuizen en allays.",
           font=f_s, fill=(140, 156, 140))
    y = TOP
    for name, im in panels:
        d.text((PAD, y - 24), name, font=f_l, fill=(232, 240, 228))
        canvas.paste(im.convert("RGB"), (PAD, y))
        y += H + 46
    out = os.path.join(B.DIST, "verdant-lucht-foto.png")
    canvas.save(out, quality=95)
    print("geschreven:", out, canvas.size)


if __name__ == "__main__":
    main()
