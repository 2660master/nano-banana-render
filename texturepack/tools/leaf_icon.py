# -*- coding: utf-8 -*-
"""Het pack-icoon: een blad.

Wordt op vier keer de eindmaat getekend en daarna verkleind, zodat de
randen en nerven glad worden. Dit bestand komt niet in het spel terecht
als texture — het is alleen het plaatje naast de packnaam — dus hier mag
het wel glad zijn in plaats van pixelig.
"""
import math

from PIL import Image, ImageFilter


def _lerp3(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def leaf(size=128, ss=4):
    """Blad met middennerf, zijnerven en een licht gekartelde rand."""
    n = size * ss
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = im.load()

    cx, cy = n * 0.5, n * 0.52
    L = n * 0.42                      # halve lengte van de bladschijf
    tilt = math.radians(-24)
    ca, sa = math.cos(tilt), math.sin(tilt)

    tip = (18, 46, 26)
    mid = (58, 122, 52)
    edge = (126, 186, 78)
    vein = (196, 224, 150)

    for y in range(n):
        for x in range(n):
            dx, dy = x - cx, y - cy
            # in het assenstelsel van het blad: t langs de nerf, u dwars
            t = (dx * ca + dy * sa) / L
            u = (-dx * sa + dy * ca) / L
            if not -1.0 <= t <= 1.0:
                continue
            s = (t + 1.0) / 2.0                       # 0 aan de steel, 1 aan de punt
            # breedte volgt een boog, met een kleine karteling erop
            w = 0.42 * (math.sin(math.pi * s) ** 0.72) * (1.0 - 0.18 * s)
            w += 0.012 * math.sin(s * math.pi * 22)
            au = abs(u)
            if au > w:
                continue

            k = au / max(w, 1e-6)                     # 0 op de nerf, 1 aan de rand
            col = _lerp3(_lerp3(mid, tip, max(0.0, 0.75 - s) * 1.1),
                         edge, k ** 1.4)
            # middennerf
            if au < 0.016 + 0.012 * (1 - s):
                col = _lerp3(col, vein, 0.75)
            else:
                # zijnerven: schuin weglopend van de middennerf
                f = (s * 13.0 - k * 2.6) % 1.0
                if f < 0.10:
                    col = _lerp3(col, vein, 0.34 * (1 - k * 0.5))
            # rand iets donkerder, geeft diepte
            if k > 0.93:
                col = _lerp3(col, tip, (k - 0.93) / 0.07 * 0.5)
            px[x, y] = col + (255,)

    # steel
    st = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    sp = st.load()
    for i in range(int(L * 0.34)):
        d = L + i
        sx = int(cx - d * ca)
        sy = int(cy - d * sa)
        for w in range(-int(n * 0.011), int(n * 0.011) + 1):
            for h in range(-int(n * 0.011), int(n * 0.011) + 1):
                if 0 <= sx + w < n and 0 <= sy + h < n:
                    sp[sx + w, sy + h] = (92, 74, 38, 255)
    st.alpha_composite(im)
    im = st

    # achtergrond: donker bos met een zachte gloed achter het blad
    bg = Image.new("RGBA", (n, n))
    bp = bg.load()
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - n / 2, y - n / 2) / (n / 2)
            base = _lerp3((26, 46, 30), (10, 18, 13), min(1.0, d))
            bp[x, y] = base + (255,)

    glow = im.filter(ImageFilter.GaussianBlur(n * 0.05))
    bg.alpha_composite(Image.blend(Image.new("RGBA", (n, n), (0, 0, 0, 0)), glow, 0.45))
    bg.alpha_composite(im)
    return bg.resize((size, size), Image.LANCZOS).convert("RGBA")


if __name__ == "__main__":
    leaf(512).save("/tmp/claude-0/-home-user-nano-banana-render/673b7979-40bd-557d-ae11-258818c67e59/scratchpad/leaf_big.png")
    print("ok")
