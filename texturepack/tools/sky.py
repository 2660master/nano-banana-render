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


def value_noise2(x, y, cells_x, cells_y, size, seed):
    """Zelfde als value_noise, maar met een eigen celtelling per as.

    Uitrekken door x te schalen brak het naadloos herhalen: de lattice
    liep dan niet meer rond op de textuurbreedte. Door in plaats daarvan
    minder cellen in x te nemen blijft het wel netjes wrappen.
    """
    sx, sy = size / cells_x, size / cells_y
    gx, gy = x / sx, y / sy
    x0, y0 = int(math.floor(gx)) % cells_x, int(math.floor(gy)) % cells_y
    x1, y1 = (x0 + 1) % cells_x, (y0 + 1) % cells_y
    tx, ty = _smooth(gx - math.floor(gx)), _smooth(gy - math.floor(gy))
    n00, n10 = noise(x0, y0, seed), noise(x1, y0, seed)
    n01, n11 = noise(x0, y1, seed), noise(x1, y1, seed)
    return _lerp(_lerp(n00, n10, tx), _lerp(n01, n11, tx), ty)


def fbm2(x, y, size, seed, octaves=4, cells_x=4, cells_y=4):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * value_noise2(x, y, cells_x * (2 ** o), cells_y * (2 ** o),
                                    size, seed + o * 37)
        norm += amp
        amp *= 0.5
    return total / norm


def fbm(x, y, size, seed, octaves=4, cells=4):
    """Gestapelde value-noise; elke octaaf verdubbelt het rooster."""
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * value_noise(x, y, cells * (2 ** o), size, seed + o * 37)
        norm += amp
        amp *= 0.5
    return total / norm


# ----------------------------------------------------------------- hemellichten
def sun(size=64):
    """Warme zon met een hete kern en een zachte krans.

    Op 64x64 in plaats van de vanilla 32x32: het verloop wordt daardoor
    glad in plaats van getrapt. Het gaat om één texture, dus dat kost
    niets aan frametijd — anders dan bij de wolken, zie clouds().
    """
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    c = (size - 1) / 2
    stops = [(0.00, hx("FFFFFF")), (0.20, hx("FFFCE8")), (0.42, hx("FFEDB4")),
             (0.62, hx("FFCE68")), (0.80, hx("F5A73C")), (1.00, hx("E8801E"))]
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / (size / 2)
            if d > 1.0:
                continue
            for i in range(len(stops) - 1):
                p0, c0 = stops[i]
                p1, c1 = stops[i + 1]
                if p0 <= d <= p1:
                    col = mix(c0, c1, (d - p0) / max(1e-6, p1 - p0))
                    break
            else:
                col = stops[-1][1]
            # zachte krans aan de buitenrand in plaats van een harde stop
            a = 255 if d < 0.82 else int(255 * (1.0 - (d - 0.82) / 0.18) ** 1.6)
            j = 0.985 + noise(x, y, 5) * 0.030
            px[x, y] = (min(255, int(col[0] * j)), min(255, int(col[1] * j)),
                        min(255, int(col[2] * j)), max(0, a))
    return im


def moon_phases(size=64):
    """Acht schijngestalten in het raster van 4 x 2 dat het spel uitleest.

    Op 64x64 per fase: genoeg ruimte voor echte zeeen en kraters. De
    verhouding 4:2 blijft, want daar rekent het spel mee.
    """
    sheet = Image.new("RGBA", (size * 4, size * 2), (0, 0, 0, 0))
    disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dp = disc.load()
    c = (size - 1) / 2
    face, mare, dark = hx("E6E8DE"), hx("B4B8AE"), hx("8E948C")

    # grote donkere vlakken, zoals de zeeen op de echte maan
    seas = [(0.36, 0.30, 0.20), (0.62, 0.44, 0.15), (0.44, 0.66, 0.17),
            (0.70, 0.72, 0.11), (0.26, 0.56, 0.10)]
    # kraters: (x, y, straal)
    craters = [(0.72, 0.24, 0.075), (0.30, 0.74, 0.060), (0.56, 0.20, 0.045),
               (0.22, 0.42, 0.040), (0.80, 0.56, 0.038), (0.48, 0.50, 0.034),
               (0.64, 0.82, 0.030), (0.38, 0.16, 0.026), (0.14, 0.62, 0.024),
               (0.86, 0.38, 0.022), (0.52, 0.36, 0.020), (0.68, 0.62, 0.018)]

    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / (size / 2)
            if d > 0.99:
                continue
            nx, ny = x / size, y / size
            col = face
            for sx, sy, sr in seas:
                dd = math.hypot(nx - sx, ny - sy) / sr
                edge = fbm(x, y, size, 61, octaves=3, cells=4) * 0.45
                if dd < 1.0 + edge:
                    col = mix(col, mare, min(1.0, (1.0 + edge - dd) * 1.6))
            col = mul(col, 0.96 + fbm(x, y, size, 91, octaves=4, cells=5) * 0.12)
            for cx, cy, cr in craters:
                dd = math.hypot(nx - cx, ny - cy) / cr
                if dd < 0.86:
                    col = mix(col, dark, 0.55 * (1.0 - dd))     # bodem
                elif dd < 1.10:
                    col = mul(col, 1.14)                        # opstaande rand
            col = mul(col, 1.05 - (d ** 2) * 0.30)              # randverdonkering
            a = 255 if d < 0.95 else int(255 * (0.99 - d) / 0.04)
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


def clouds(size=256, coverage=0.30):
    """Wolkenbanken, uitgerekt in de windrichting.

    Blijft bewust op 256x256. Minecraft bouwt uit elke pixel met alpha > 0
    een echte wolkendoos, dus een grotere texture is letterlijk meer
    geometrie en kost wel frametijd — anders dan de zon en de maan.

    Echte wolken zijn langgerekt langs de wind en rafelig aan de randen.
    Daarom wordt de ruis in x samengedrukt (banken) en komt er een fijne
    laag overheen die de randen laat uitfranselen.
    """
    vals = [[0.0] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            # minder cellen in x dan in y: banken die langs de wind liggen
            bank = fbm2(x, y, size, 7, octaves=4, cells_x=2, cells_y=6)
            wisp = fbm2(x, y, size, 19, octaves=4, cells_x=7, cells_y=13)
            vals[y][x] = 0.70 * bank + 0.30 * wisp

    flat = sorted(v for row in vals for v in row)
    cut = flat[int(len(flat) * (1.0 - coverage))]
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    for y in range(size):
        for x in range(size):
            v = vals[y][x]
            if v < cut:
                continue
            # dichter naar het hart van de bank toe iets witter
            t = min(1.0, (v - cut) / max(1e-6, flat[-1] - cut))
            g = 232 + int(t * 22) + int(noise(x, y, 3) * 6)
            px[x, y] = (min(255, g), min(255, g), min(255, g + 5), 255)
    return im


def end_sky(size=64):
    """Sterrenveld met een vage groene nevel.

    Op 64x64 in plaats van 16x16: bij zestien pixels zie je het raster van
    de herhaling meteen. Vier keer groter betekent zestien keer minder
    zichtbare herhaling, en het blijft een enkele kleine texture.
    """
    im = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    px = im.load()
    base, neb = hx("07100C"), hx("16321F")
    for y in range(size):
        for x in range(size):
            n = fbm(x, y, size, 23, octaves=4, cells=3)
            px[x, y] = mix(base, neb, max(0.0, (n - 0.42)) * 1.5)
    for k in range(46):
        sx = int(noise(k, 50, 23) * size)
        sy = int(noise(k, 51, 23) * size)
        b = noise(k, 52, 23)
        col = mix(hx("6E8A78"), hx("E8F4E8"), b ** 2)
        px[sx, sy] = col
        if b > 0.86:                       # de helderste sterren stralen uit
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = (sx + dx) % size, (sy + dy) % size
                px[nx, ny] = mix(px[nx, ny], col, 0.45)
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
