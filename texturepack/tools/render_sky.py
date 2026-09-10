# -*- coding: utf-8 -*-
"""Rendert een voorbeeldbeeld van de lucht, zodat je ziet hoe zon, maan en
wolken er in het spel uit gaan zien in plaats van alleen de platte bestanden.

De wolken worden in perspectief op een vlak boven de speler geprojecteerd,
net als in het spel: hoe dichter bij de horizon, hoe verder weg.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import build as B
import sky

W, H = 660, 380
HORIZON = int(H * 0.62)
CLOUD_H = 120.0          # hoogte van het wolkendek boven de speler
FOV = math.radians(35)


def gradient(top, bottom):
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return im


def project_clouds(base, cloud_img, tint, offset=0.0, strength=1.0):
    """Legt het wolkendek in perspectief over de lucht."""
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


def paste_disc(base, disc, cx, cy, size, glow=None):
    d = disc.convert("RGBA").resize((size, size), Image.NEAREST)
    if glow:
        g = Image.new("RGBA", (size * 3, size * 3), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        for r in range(size * 3 // 2, 0, -2):
            a = int(glow[3] * (1 - r / (size * 1.5)) ** 2.2)
            gd.ellipse([size * 1.5 - r, size * 1.5 - r, size * 1.5 + r, size * 1.5 + r],
                       fill=(glow[0], glow[1], glow[2], a))
        base.paste(Image.alpha_composite(
            base.crop((cx - size * 3 // 2, cy - size * 3 // 2,
                       cx + size * 3 // 2, cy + size * 3 // 2)).convert("RGBA"), g),
            (cx - size * 3 // 2, cy - size * 3 // 2))
    base.paste(d, (cx - size // 2, cy - size // 2), d)
    return base


def terrain(im, night=False):
    """Blokkig heuvelsilhouet, zodat het beeld op Minecraft lijkt."""
    d = ImageDraw.Draw(im)
    grass = (46, 74, 38) if not night else (16, 26, 16)
    dirt = (58, 44, 30) if not night else (20, 16, 12)
    tree = (34, 58, 30) if not night else (12, 20, 12)
    step = 12
    hs = []
    for i in range(W // step + 2):
        hs.append(HORIZON + int(14 * math.sin(i * 0.45) + 8 * math.sin(i * 0.17 + 1.3)))
    for i, hy in enumerate(hs):
        x = i * step
        d.rectangle([x, hy, x + step, hy + step], fill=grass)
        d.rectangle([x, hy + step, x + step, H], fill=dirt)
    for i in range(3, len(hs), 9):          # een paar bomen op de horizon
        x, hy = i * step, hs[i]
        d.rectangle([x + 4, hy - 26, x + 8, hy], fill=(44, 32, 20) if not night else (16, 12, 8))
        d.ellipse([x - 8, hy - 44, x + 20, hy - 16], fill=tree)
    return im


def panel_day():
    im = gradient((116, 168, 232), (186, 214, 236)).convert("RGBA")
    im = project_clouds(im, sky.clouds(), (250, 250, 246)).convert("RGBA")
    im = paste_disc(im, sky.sun(), int(W * 0.74), int(H * 0.20), 54,
                    glow=(255, 214, 120, 130))
    return terrain(im)


def panel_night():
    im = gradient((10, 14, 34), (28, 36, 62).__class__((28, 36, 62))).convert("RGBA")
    d = ImageDraw.Draw(im)
    rs = np.random.default_rng(7)
    for _ in range(160):                     # sterren
        x, y = int(rs.random() * W), int(rs.random() * HORIZON)
        b = 120 + int(rs.random() * 135)
        d.point((x, y), fill=(b, b, min(255, b + 12)))
    im = project_clouds(im, sky.clouds(), (96, 106, 130), offset=40, strength=0.8).convert("RGBA")
    moon = sky.moon_phases().crop((0, 0, 32, 32))
    im = paste_disc(im, moon, int(W * 0.26), int(H * 0.18), 46,
                    glow=(200, 214, 226, 90))
    return terrain(im, night=True)


def panel_end():
    # in het spel staat de end-hemel ver weg; hier 3x vergroot zodat het
    # beeld klopt met hoe groot je de tegels daadwerkelijk ziet
    tile = sky.end_sky().resize((48, 48), Image.NEAREST)
    im = Image.new("RGBA", (W, H))
    for y in range(0, H, 48):
        for x in range(0, W, 48):
            im.paste(tile, (x, y))
    d = ImageDraw.Draw(im)
    for cx, cy, rw, rh in ((W * 0.30, H * 0.62, 150, 26), (W * 0.68, H * 0.44, 110, 20),
                           (W * 0.52, H * 0.80, 190, 30)):
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(212, 214, 156, 255))
        d.ellipse([cx - rw * 0.9, cy, cx + rw * 0.9, cy + rh * 2.4], fill=(176, 178, 124, 255))
    return im


def main():
    panels = [("Dag", panel_day()), ("Nacht", panel_night()), ("The End", panel_end())]
    f_t = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    f_l = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
    f_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    PAD, TOP = 26, 116
    canvas = Image.new("RGB", (PAD * 2 + W, TOP + len(panels) * (H + 46) + 16), (24, 30, 26))
    d = ImageDraw.Draw(canvas)
    d.text((PAD, 28), "Verdant — zo ziet de lucht eruit", font=f_t, fill=(232, 240, 228))
    d.text((PAD, 70), "Zon, maan en wolken uit het pack, in perspectief gezet zoals het spel ze tekent.",
           font=f_s, fill=(140, 197, 94))
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
