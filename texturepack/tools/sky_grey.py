# -*- coding: utf-8 -*-
"""Lucht voor het grijze pack: wolken, zon, maan en de End-lucht.

Wat een resource pack aan de lucht kan veranderen is precies vier dingen:
sun.png, moon_phases.png, clouds.png en end_sky.png. De sterren en de
kleurverloop van de gewone nachtlucht zitten in de code van het spel, niet
in een texture — die kun je zonder mod niet aanpassen. Planeten en een
zwart gat kunnen dus alleen in de End-lucht, en dat is precies waar
crystal PvP zich afspeelt.

clouds.png is het enige vel hier dat frametijd kost: Minecraft bouwt uit
elke pixel met alpha > 0 een echte wolkendoos. Meer dekking is letterlijk
meer geometrie. De zon en de maan zijn gewone platen en kosten niets
extra, dus die mogen scherp.
"""
from PIL import Image

from blocks import mix, mul, noise
from palette import hx
from sky import fbm2


def clouds(size=256, coverage=0.34, lump=4, wisp=0.30, seed=7, wind=2.0):
    """Wolkenvel. `lump` is hoe grof de wolken zijn, `wind` hoe langgerekt.

    De dekking wordt op de gewenste fractie afgekapt door de drempel uit de
    gesorteerde waarden te halen, niet door een vaste grens. Zo klopt "een
    derde bewolkt" ook echt, wat de ruis ook doet.
    """
    cx = max(1, int(round(lump / wind)))
    vals = [[0.0] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            bank = fbm2(x, y, size, seed, octaves=4, cells_x=cx, cells_y=lump)
            fine = fbm2(x, y, size, seed + 12, octaves=4,
                        cells_x=cx * 3, cells_y=lump * 3)
            vals[y][x] = (1.0 - wisp) * bank + wisp * fine

    flat = sorted(v for row in vals for v in row)
    cut = flat[int(len(flat) * (1.0 - coverage))]
    top = flat[-1]
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    for y in range(size):
        for x in range(size):
            v = vals[y][x]
            if v < cut:
                continue
            t = min(1.0, (v - cut) / max(1e-6, top - cut))
            g = 236 + int(t * 19) + int(noise(x, y, 3) * 4)
            px[x, y] = (min(255, g), min(255, g), min(255, g + 3), 255)
    return im


def sun(size=64, disc=0.56, corona=0.96, core="FFFFFF", rim="FFF2D0"):
    """Zon: een harde schijf met een zachte krans eromheen.

    De zon is een platte plaat in het spel, geen geometrie, dus die mag
    groter en scherper dan vanilla zonder dat het iets kost.
    """
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    c, r = hx(core), hx(rim)
    half = size / 2.0
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - half, y + 0.5 - half
            d = (dx * dx + dy * dy) ** 0.5 / half
            if d <= disc:
                t = (d / disc) ** 2
                col = mix(c, r, t * 0.9)
                px[x, y] = (col[0], col[1], col[2], 255)
            elif d <= corona:
                t = (d - disc) / (corona - disc)
                a = int(215 * (1.0 - t) ** 2.1)
                if a > 0:
                    col = mul(r, 1.0 - t * 0.25)
                    px[x, y] = (col[0], col[1], col[2], a)
    return im


def moon_phases(size=64, base="D8DEE4", sea="9AA4AE", craters=22,
                glow=0.0):
    """Maan: acht fasen naast elkaar, zoals het spel het vel verwacht.

    Het vel is vier breed en twee hoog. Fase 0 is vol, daarna schuift er
    een schaduw overheen. De maanzeeën en kraters zitten in de volle maan
    en worden mee afgedekt, dus ze staan elke nacht op dezelfde plek —
    net als echt.
    """
    import math

    half = size / 2.0
    full = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fp = full.load()
    b, s = hx(base), hx(sea)
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - half, y + 0.5 - half
            d = (dx * dx + dy * dy) ** 0.5 / half
            if d > 0.94:
                continue
            # maanzeeën: grote donkere vlakken
            n = fbm2(x, y, size, 31, octaves=3, cells_x=3, cells_y=3)
            col = mix(b, s, max(0.0, (n - 0.46)) * 2.4)
            col = mul(col, 1.0 - 0.22 * (d ** 3))          # rand loopt weg
            fp[x, y] = (col[0], col[1], col[2], 255)
    # kraters: een lichte rand met een donkere kom
    for k in range(craters):
        cx = noise(k, 60, 31) * size
        cy = noise(k, 61, 31) * size
        r = 1.5 + noise(k, 62, 31) * (size / 14.0)
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if not (0 <= x < size and 0 <= y < size):
                    continue
                if fp[x, y][3] == 0:
                    continue
                dd = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
                if dd > r:
                    continue
                f = 0.80 if dd < r * 0.66 else 1.16        # kom, dan rand
                fp[x, y] = mul(fp[x, y], f)

    sheet = Image.new("RGBA", (size * 4, size * 2), (0, 0, 0, 0))
    for phase in range(8):
        # De grens tussen licht en donker is een ellips over de schijf.
        # k loopt van -1 (vol) naar +1 (nieuw); w is de halve breedte van
        # de schijf op die hoogte, dus k*w is waar de grens ligt.
        if phase <= 4:                                     # afnemend
            k = -math.cos(math.pi * phase / 4.0)
            mirror = False
        else:                                              # wassend
            k = -math.cos(math.pi * (8 - phase) / 4.0)
            mirror = True
        tile = full.copy()
        tp = tile.load()
        for y in range(size):
            for x in range(size):
                if tp[x, y][3] == 0:
                    continue
                u = (x + 0.5 - half) / half
                v = (y + 0.5 - half) / half
                w = max(0.0, 1.0 - v * v) ** 0.5
                edge = k * w
                lit = (-u >= edge) if mirror else (u >= edge)
                if not lit:
                    tp[x, y] = (0, 0, 0, 0)
        sheet.alpha_composite(tile, ((phase % 4) * size, (phase // 4) * size))
    if glow:
        sheet = _halo(sheet, size, glow)
    return sheet


def _halo(sheet, size, strength):
    """Zachte kring om elke fase heen."""
    out = sheet.copy()
    op = out.load()
    sp = sheet.load()
    half = size / 2.0
    for ty in range(2):
        for tx in range(4):
            ox, oy = tx * size, ty * size
            for y in range(size):
                for x in range(size):
                    if sp[ox + x, oy + y][3]:
                        continue
                    dx, dy = x + 0.5 - half, y + 0.5 - half
                    d = (dx * dx + dy * dy) ** 0.5 / half
                    if d > 1.0:
                        continue
                    a = int(120 * strength * (1.0 - d) ** 2)
                    if a > 0:
                        op[ox + x, oy + y] = (226, 234, 244, a)
    return out


def end_sky(size=256, seed=5, stars=260, nebula=0.55, planets=(),
            hole=None, base="05070C", neb1="1A2030", neb2="0E1626"):
    """De End-lucht: het enige vel waar planeten en een zwart gat kunnen.

    Let op hoe het spel dit vel gebruikt: het wordt over elk vlak van de
    hemelkoepel zestien keer naast elkaar gelegd. Wat hier één planeet is,
    staan er in het spel dus honderden — precies goed voor "heel veel
    planeten", maar één enkel zwart gat bestaat niet; ook dat herhaalt.

    Het is een gewone platte texture, geen geometrie, dus de grootte kost
    geen frametijd.
    """
    im = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    px = im.load()
    b, n1, n2 = hx(base), hx(neb1), hx(neb2)
    for y in range(size):
        for x in range(size):
            a = fbm2(x, y, size, seed, octaves=4, cells_x=2, cells_y=2)
            c = fbm2(x, y, size, seed + 8, octaves=4, cells_x=5, cells_y=3)
            col = mix(b, n1, max(0.0, a - 0.48) * 2.0 * nebula)
            col = mix(col, n2, max(0.0, c - 0.55) * 1.8 * nebula)
            px[x, y] = col

    for k in range(stars):
        sx = int(noise(k, 50, seed) * size)
        sy = int(noise(k, 51, seed) * size)
        b2 = noise(k, 52, seed)
        col = mix(hx("6C7688"), hx("FFFFFF"), b2 ** 1.6)
        px[sx, sy] = col
        if b2 > 0.90:                                  # heldere ster straalt
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = (sx + dx) % size, (sy + dy) % size
                px[nx, ny] = mix(px[nx, ny], col, 0.50)

    for (cx, cy, r, light, dark, ring) in planets:
        _planet(px, size, cx, cy, r, light, dark, ring, seed)

    if hole:
        _black_hole(px, size, *hole)
    return im


def _planet(px, size, cx, cy, r, light, dark, ring, seed):
    """Bol met licht van linksboven en eventueel een ring."""
    l, d = hx(light), hx(dark)
    if ring:
        rr = hx(ring)
        for y in range(int(cy - r * 2.4), int(cy + r * 2.4) + 1):
            for x in range(int(cx - r * 2.4), int(cx + r * 2.4) + 1):
                if not (0 <= x < size and 0 <= y < size):
                    continue
                u = (x - cx) / (r * 2.2)
                v = (y - cy) / (r * 0.62)
                e = (u * u + v * v) ** 0.5
                if 0.80 < e < 1.0:
                    px[x, y] = mix(px[x, y], rr, 0.75)
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if not (0 <= x < size and 0 <= y < size):
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            e = (dx * dx + dy * dy) ** 0.5 / r
            if e > 1.0:
                continue
            # licht uit linksboven, en banden zoals een gasplaneet
            lam = max(0.0, (-dx * 0.6 - dy * 0.6) / r * 0.5 + 0.55)
            band = noise(0, int(y - cy + r), seed + 71) * 0.30
            col = mix(d, l, min(1.0, lam + band))
            if e > 0.92:
                col = mul(col, 0.72)
            px[x, y] = col


def _black_hole(px, size, cx, cy, r, disc="C8D4E4"):
    """Zwarte schijf met een gloeiende schijf eromheen."""
    dc = hx(disc)
    for y in range(int(cy - r * 3.2), int(cy + r * 3.2) + 1):
        for x in range(int(cx - r * 3.2), int(cx + r * 3.2) + 1):
            if not (0 <= x < size and 0 <= y < size):
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            e = (dx * dx + dy * dy) ** 0.5 / r
            if e <= 1.0:                               # de horizon zelf
                px[x, y] = (0, 0, 0, 255)
                continue
            # de schijf: een platte ellips die er omheen draait
            u, v = dx / (r * 3.0), dy / (r * 0.85)
            f = (u * u + v * v) ** 0.5
            if f < 1.0:
                t = 1.0 - abs(f - 0.66) / 0.66
                if t > 0:
                    px[x, y] = mix(px[x, y], dc, min(1.0, t * 1.15))
            if 1.0 < e < 1.45:                         # lichtring op de rand
                px[x, y] = mix(px[x, y], dc, (1.45 - e) / 0.45 * 0.9)
