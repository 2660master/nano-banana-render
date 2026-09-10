# -*- coding: utf-8 -*-
"""Lucht, weer, water en lava voor het Verdant natuur-texturepack.

Alles blijft op vanilla-formaat. De geanimeerde texturen lopen wiskundig
rond: elke frame is een sinusfase, dus frame 0 sluit exact aan op de laatste
en je ziet nooit een sprong.

Wolken zijn bewust hard afgesneden (alpha 0 of 255) en blijven rond de
vanilla-dekking. Minecraft bouwt namelijk echte wolkendozen uit elke pixel
met alpha > 0 — meer wolk is dus letterlijk meer geometrie, en dat kost FPS.
"""
import math

from PIL import Image

from blocks import mix, mul, noise
from palette import hx


# ------------------------------------------------------------------- helpers
def _lerp(a, b, t):
    return a + (b - a) * t


def _smooth(t):
    return t * t * (3 - 2 * t)


def value_noise(x, y, cells, size, seed):
    """Tegelbare value-noise: het rooster wrapt op `cells`."""
    step = size / cells
    gx, gy = x / step, y / step
    x0, y0 = int(math.floor(gx)) % cells, int(math.floor(gy)) % cells
    x1, y1 = (x0 + 1) % cells, (y0 + 1) % cells
    tx, ty = _smooth(gx - math.floor(gx)), _smooth(gy - math.floor(gy))
    n00, n10 = noise(x0, y0, seed), noise(x1, y0, seed)
    n01, n11 = noise(x0, y1, seed), noise(x1, y1, seed)
    return _lerp(_lerp(n00, n10, tx), _lerp(n01, n11, tx), ty)


def fbm(x, y, size, seed, octaves=4, cells=4):
    """Gestapelde value-noise; elke octaaf verdubbelt het rooster."""
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * value_noise(x, y, cells * (2 ** o), size, seed + o * 37)
        norm += amp
        amp *= 0.5
    return total / norm


# ----------------------------------------------------------------- hemellichten
def sun(size=32):
    """Warme zon met een zachte krans, alsof je door bladeren omhoog kijkt."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    c = (size - 1) / 2
    core, rim, halo = hx("FFF6D2"), hx("FFD066"), hx("F0A63C")
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / (size / 2)
            if d > 1.0:
                continue
            if d < 0.52:
                col, a = mix(core, rim, d / 0.52), 255
            elif d < 0.78:
                col, a = mix(rim, halo, (d - 0.52) / 0.26), 255
            else:
                col = halo
                a = int(255 * (1.0 - (d - 0.78) / 0.22))
            j = noise(x, y, 5) * 0.06 + 0.97
            px[x, y] = (min(255, int(col[0] * j)), min(255, int(col[1] * j)),
                        min(255, int(col[2] * j)), max(0, a))
    return im


def moon_phases(size=32):
    """Alle acht schijngestalten in een raster van 4 x 2, zoals vanilla leest."""
    sheet = Image.new("RGBA", (size * 4, size * 2), (0, 0, 0, 0))
    disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dp = disc.load()
    c = (size - 1) / 2
    face, crater = hx("EDF0E6"), hx("C6CCC0")
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / (size / 2)
            if d > 0.98:
                continue
            t = fbm(x, y, size, 91, octaves=3, cells=3)
            col = mix(face, crater, min(1.0, max(0.0, (t - 0.34) * 2.6)))
            col = mul(col, 1.04 - d * 0.16)
            a = 255 if d < 0.94 else int(255 * (0.98 - d) / 0.04)
            dp[x, y] = (col[0], col[1], col[2], max(0, a))

    for p in range(8):
        frame = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        fp, t = frame.load(), math.cos(2 * math.pi * p / 8)
        for y in range(size):
            for x in range(size):
                src = dp[x, y]
                if src[3] == 0:
                    continue
                ny = (y - c) / (size / 2)
                nx = (x - c) / (size / 2)
                e = math.sqrt(max(0.0, 1.0 - ny * ny))
                lit = (nx >= -t * e) if p <= 4 else (nx <= t * e)
                if lit:
                    fp[x, y] = src
        sheet.paste(frame, ((p % 4) * size, (p // 4) * size))
    return sheet


def clouds(size=256, coverage=0.34):
    """Organische wolkenvelden, hard afgesneden om geometrie te sparen."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    vals = [[fbm(x, y, size, 7, octaves=4, cells=7) for x in range(size)]
            for y in range(size)]
    flat = sorted(v for row in vals for v in row)
    cut = flat[int(len(flat) * (1.0 - coverage))]
    for y in range(size):
        for x in range(size):
            if vals[y][x] >= cut:
                g = 236 + int(noise(x, y, 3) * 19)
                px[x, y] = (g, g, min(255, g + 4), 255)
    return im


def end_sky(size=16):
    """Diepgroen-zwarte end-hemel met zwevende sporen."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    px = im.load()
    base = hx("0E1A14")
    for y in range(size):
        for x in range(size):
            v = fbm(x, y, size, 23, octaves=3, cells=2)
            px[x, y] = mul(base, 0.7 + v * 0.8)
    for k in range(10):                      # sporen die licht vangen
        sx = int(noise(k, 50, 23) * size)
        sy = int(noise(k, 51, 23) * size)
        g = mix(hx("7FB58A"), hx("D6EFCF"), noise(k, 52, 23))
        px[sx, sy] = g
    return im


def rain(size=32, tint="A8C8D8", streaks=26):
    """Regen: dunne verticale strepen met een groenblauwe zweem."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    col = hx(tint)
    for k in range(streaks):
        x = int(noise(k, 1, 61) * size)
        y0 = int(noise(k, 2, 61) * size)
        length = 5 + int(noise(k, 3, 61) * 9)
        for i in range(length):
            y = (y0 + i) % size
            a = int(210 * (1.0 - abs(i - length / 2) / (length / 2)) + 30)
            px[x, y] = (col[0], col[1], col[2], min(255, a))
    return im


def snow_weather(size=32, flakes=52):
    """Sneeuw: zachte vlokken van een enkele pixel met een halo."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    col = hx("F4F8FA")
    for k in range(flakes):
        x = int(noise(k, 4, 71) * size)
        y = int(noise(k, 5, 71) * size)
        px[x, y] = (col[0], col[1], col[2], 235)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if noise(k, 6 + dx + dy * 3, 71) < 0.45:
                px[(x + dx) % size, (y + dy) % size] = (col[0], col[1], col[2], 90)
    return im


# ----------------------------------------------------------- geanimeerd (loopt rond)
def _strip(w, h, frames, fn):
    im = Image.new("RGBA", (w, h * frames), (0, 0, 0, 0))
    px = im.load()
    for f in range(frames):
        ph = 2 * math.pi * f / frames
        for y in range(h):
            for x in range(w):
                px[x, f * h + y] = fn(x, y, ph, w, h)
    return im


def water_still(frames=32, size=16):
    """Rimpelend water. Het spel kleurt dit met de biome-kleur, dus bleek."""
    base = hx("C8DCE8")

    def pix(x, y, ph, w, h):
        v = (0.32 * math.sin(2 * math.pi * x / w + ph)
             + 0.24 * math.sin(2 * math.pi * (x + y) / w - ph)
             + 0.22 * math.sin(2 * math.pi * 2 * y / w + ph * 2)
             + 0.22 * math.sin(2 * math.pi * 3 * (x - y) / w - ph * 3))
        c = mul(base, 0.76 + (v * 0.5 + 0.5) * 0.42)
        return (c[0], c[1], c[2], 235)

    return _strip(size, size, frames, pix)


def water_flow(frames=32, size=32):
    """Stromend water: banen die naar beneden trekken."""
    base = hx("C8DCE8")

    def pix(x, y, ph, w, h):
        v = (0.44 * math.sin(2 * math.pi * (2 * y / h) - ph * 2)
             + 0.30 * math.sin(2 * math.pi * (y / h + x / (w * 2)) - ph)
             + 0.26 * math.sin(2 * math.pi * 4 * x / w))      # verticale strengen
        c = mul(base, 0.74 + (v * 0.5 + 0.5) * 0.44)
        return (c[0], c[1], c[2], 235)

    return _strip(size, size, frames, pix)


def lava_still(frames=20, size=16):
    """Trage lava: donkere korst met opengaande gloed."""
    hot, crust = hx("F5A63A"), hx("6E1F0E")

    def pix(x, y, ph, w, h):
        # domeinvervorming breekt het ruitjespatroon dat twee sinussen geven
        u = x / w + 0.16 * math.sin(2 * math.pi * y / w + ph)
        v = y / w + 0.16 * math.sin(2 * math.pi * x / w - ph)
        n = (0.5 * math.sin(2 * math.pi * 2 * u + ph)
             + 0.3 * math.sin(2 * math.pi * 3 * v - ph * 1.3)
             + 0.2 * math.sin(2 * math.pi * 5 * (u + v) + ph * 0.7))
        t = (n * 0.5 + 0.5) ** 2.1
        c = mix(crust, hot, t)
        return (c[0], c[1], c[2], 255)

    return _strip(size, size, frames, pix)


def lava_flow(frames=20, size=32):
    """Lava die omlaag kruipt."""
    hot, crust = hx("F0902A"), hx("5E1A0C")

    def pix(x, y, ph, w, h):
        u = x / w + 0.10 * math.sin(2 * math.pi * 2 * y / h - ph)
        n = (0.55 * math.sin(2 * math.pi * (2 * y / h) - ph * 2)
             + 0.25 * math.sin(2 * math.pi * 3 * u + ph)
             + 0.20 * math.sin(2 * math.pi * 5 * y / h - ph * 3))
        t = (n * 0.5 + 0.5) ** 1.8
        c = mix(crust, hot, t)
        return (c[0], c[1], c[2], 255)

    return _strip(size, size, frames, pix)
