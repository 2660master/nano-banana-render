# -*- coding: utf-8 -*-
"""Procedurele 16x16 blokpatronen voor het Verdant natuur-texturepack.

Alle patronen tegelen naadloos: structuur wordt met modulo-rekenen op 16
gelegd en de ruis is puur een functie van (x % 16, y % 16).
"""
from PIL import Image

from palette import hx

N = 16


# ------------------------------------------------------------------- helpers
def noise(x, y, seed):
    """Deterministische ruis in [0,1). Tegelt omdat x en y al mod 16 zijn."""
    n = (x * 374761393 + y * 668265263 + seed * 2654435761) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def mul(c, f):
    return (max(0, min(255, int(c[0] * f))),
            max(0, min(255, int(c[1] * f))),
            max(0, min(255, int(c[2] * f))),
            c[3] if len(c) > 3 else 255)


def mix(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t),
            255)


def img(fill=(0, 0, 0, 0)):
    return Image.new("RGBA", (N, N), fill)


def moss_over(im, seed, color=hx("5C8A3A"), amount=0.12, top_bias=True):
    """Legt mos- en korstmosspikkels over een blok. Hecht bovenaan sterker."""
    px = im.load()
    for y in range(N):
        for x in range(N):
            if px[x, y][3] == 0:
                continue
            bias = (1.0 - y / N) * 0.8 + 0.2 if top_bias else 1.0
            clump = 0.65 * noise(x // 2, y // 2, seed + 77) + 0.35 * noise(x, y, seed + 78)
            if clump < amount * bias:
                t = 0.55 + noise(x, y, seed + 91) * 0.35
                px[x, y] = mix(px[x, y], color, t)
    return im


# ------------------------------------------------------------------ patronen
def planks(base, seed, rows=4):
    """Vier lange plankgangen. De nerf loopt horizontaal door, alleen de
    naad tussen de gangen is donker en er zit maar op twee gangen een
    kopse naad — anders leest het als metselwerk."""
    im = img()
    px = im.load()
    h = N // rows
    for y in range(N):
        r = y // h
        ry = y % h
        tint = 0.94 + noise(0, r, seed) * 0.13      # elke gang eigen tint
        line = noise(0, y, seed + 3)                 # nerf over de hele breedte
        for x in range(N):
            v = 0.72 * line + 0.28 * noise(x // 3, y, seed + r * 17)
            c = mul(base, tint * (0.93 + v * 0.15))
            if ry == h - 1:
                c = mul(base, 0.58)                  # naad tussen de gangen
            elif ry == 0:
                c = mul(c, 1.07)                     # lichte bovenkant
            px[x, y] = c
    for r in (0, 2):                                 # kopse naad op twee gangen
        jx = (3 + r * 5 + int(noise(r, 9, seed) * 5)) % N
        for ry in range(h - 1):
            px[jx, r * h + ry] = mul(base, 0.68)
    return im


def log_side(bark, seed, dashes=False):
    """Verticale bast met diepe groeven en een enkele kwast.
    dashes=True geeft de zwarte streepjes van berkenbast."""
    im = img()
    px = im.load()
    for x in range(N):
        col_v = noise(x, 0, seed)
        groove = col_v < 0.26
        for y in range(N):
            v = noise(x, y // 2, seed + 5)
            c = mul(bark, 0.84 + v * 0.30)
            if groove:
                c = mul(c, 0.70)
            if (x * 3 + y) % 11 == 0:
                c = mul(c, 1.06)
            px[x, y] = c
    if dashes:
        for k in range(5):
            dx = int(noise(k, 40, seed) * 12)
            dy = int(noise(k, 41, seed) * 15)
            w = 2 + int(noise(k, 42, seed) * 3)
            for i in range(w):
                px[(dx + i) % N, dy] = mul(bark, 0.30)
                px[(dx + i) % N, (dy + 1) % N] = mul(bark, 0.46)
        return im
    # kwast
    kx, ky = 4 + int(noise(1, 1, seed) * 7), 5 + int(noise(2, 2, seed) * 6)
    for dy in range(-2, 3):
        for dx in range(-1, 2):
            d = abs(dx) * 2 + abs(dy)
            if d <= 3:
                px[(kx + dx) % N, (ky + dy) % N] = mul(bark, 0.60 + d * 0.06)
    return im


def log_top(bark, core, seed):
    """Jaarringen met een bastrand die netjes rondom doorloopt."""
    im = img()
    px = im.load()
    cx = cy = 7.5
    for y in range(N):
        for x in range(N):
            dx, dy = x - cx, y - cy
            d = (dx * dx + dy * dy) ** 0.5
            if max(abs(dx), abs(dy)) >= 7.0:
                px[x, y] = mul(bark, 0.82 + noise(x, y, seed) * 0.28)
                continue
            # ringen van ~3,3 px zodat ze op 16x16 echt als ringen lezen
            ring = (d * 0.30 + noise(x, y, seed + 3) * 0.12) % 1.0
            c = mul(core, 1.05) if ring < 0.5 else mul(core, 0.76)
            if d < 1.2:
                c = mul(core, 0.66)            # merg in het hart
            px[x, y] = mul(c, 0.97 + noise(x, y, seed + 9) * 0.06)
    return im


def bricks(base, mortar, seed, bw=8, bh=4, offset=True):
    """Halfsteensverband. bw en bh moeten op 16 passen zodat het tegelt."""
    im = img()
    px = im.load()
    for y in range(N):
        row = y // bh
        shift = (bw // 2) if (offset and row % 2) else 0
        for x in range(N):
            lx = (x + shift) % bw
            ly = y % bh
            if lx == 0 or ly == bh - 1:
                px[x, y] = mul(mortar, 0.92 + noise(x, y, seed + 2) * 0.18)
            else:
                v = noise(x, y, seed + row * 7)
                c = mul(base, 0.86 + v * 0.26)
                if ly == 0:
                    c = mul(c, 1.07)
                px[x, y] = c
    return im


def cobble(base, seed, cells=4, mortar_f=0.55):
    """Tegelbare Voronoi: keien van ongelijke maat met donkere voegen."""
    step = N // cells
    pts = []
    for cy in range(cells):
        for cx in range(cells):
            jx = noise(cx, cy, seed) * (step - 1)
            jy = noise(cx, cy, seed + 31) * (step - 1)
            pts.append((cx * step + jx, cy * step + jy, noise(cx, cy, seed + 63)))
    im = img()
    px = im.load()
    for y in range(N):
        for x in range(N):
            best = best2 = 1e9
            shade = 0.0
            for (pxx, pyy, s) in pts:
                dx = abs(x - pxx); dx = min(dx, N - dx)
                dy = abs(y - pyy); dy = min(dy, N - dy)
                d = dx * dx + dy * dy
                if d < best:
                    best2, best, shade = best, d, s
                elif d < best2:
                    best2 = d
            edge = (best2 ** 0.5 - best ** 0.5) < 1.15
            c = mul(base, 0.80 + shade * 0.36)
            c = mul(c, 0.94 + noise(x, y, seed + 11) * 0.12)
            px[x, y] = mul(c, mortar_f) if edge else c
    return im


def stone(base, seed, contrast=0.30, blotch=True, specks=0.0, speck_f=0.72):
    """Gevlekte steen: fijne korrel, grotere vlekken en losse spikkels.
    specks > 0 zet de karakteristieke stippen van graniet en dioriet."""
    im = img()
    px = im.load()
    for y in range(N):
        for x in range(N):
            fine = noise(x, y, seed)
            coarse = noise(x // 3, y // 3, seed + 17) if blotch else 0.5
            v = 0.50 * fine + 0.50 * coarse
            c = mul(base, 1.0 - contrast / 2 + v * contrast)
            if specks and noise(x, y, seed + 29) < specks:
                c = mul(c, speck_f)
            elif specks and noise(x, y, seed + 30) < specks * 0.7:
                c = mul(c, 1.0 / speck_f)
            px[x, y] = c
    return im


def fabric(base, seed):
    """Wol: pluizige korrel met een lichte weefstructuur."""
    im = img()
    px = im.load()
    for y in range(N):
        for x in range(N):
            v = noise(x, y, seed) * 0.55 + noise(x // 2, y // 2, seed + 8) * 0.45
            c = mul(base, 0.84 + v * 0.30)
            if noise(x, y, seed + 21) > 0.90:
                c = mul(c, 1.12)                     # opstaand pluisje
            elif noise(x, y, seed + 22) < 0.08:
                c = mul(c, 0.86)
            px[x, y] = c
    return im


def smooth(base, seed, grain=0.07):
    """Beton: vlak, met net genoeg korrel om niet dood te ogen."""
    im = img()
    px = im.load()
    for y in range(N):
        for x in range(N):
            v = noise(x, y, seed) * 0.5 + noise(x // 4, y // 4, seed + 4) * 0.5
            px[x, y] = mul(base, 1.0 - grain / 2 + v * grain)
    return im


def clay(base, seed):
    """Terracotta: horizontale sliblagen zoals in gebakken klei."""
    im = img()
    px = im.load()
    for y in range(N):
        band = 0.90 + noise(0, y, seed) * 0.16
        for x in range(N):
            v = noise(x, y, seed + 6) * 0.35 + noise(x // 4, y, seed + 12) * 0.65
            px[x, y] = mul(base, band * (0.94 + v * 0.14))
    return im


def glass(tint, seed, frame=None, alpha=26):
    """Glas: open midden, doorlopende rand en twee lichtvegen.
    alpha regelt hoe dicht de ruit is — getint glas is bijna ondoorzichtig."""
    im = img()
    px = im.load()
    frame = frame or mul(tint, 1.18)
    for y in range(N):
        for x in range(N):
            on_edge = x == 0 or y == 0 or x == N - 1 or y == N - 1
            if on_edge:
                px[x, y] = (frame[0], frame[1], frame[2], 235)
            elif (x - y) % 9 == 0 and 2 <= x <= 13 and 2 <= y <= 13:
                px[x, y] = (tint[0], tint[1], tint[2], min(255, alpha + 64))
            elif noise(x, y, seed) < 0.05:
                px[x, y] = (tint[0], tint[1], tint[2], min(255, alpha + 34))
            else:
                px[x, y] = (tint[0], tint[1], tint[2], alpha)
    return im


def solid(col):
    return img(col if len(col) == 4 else col + (255,))


def crack(im, seed, n=3):
    """Trekt een paar grillige scheuren over een bestaand blok."""
    px = im.load()
    for k in range(n):
        x = int(noise(k, 0, seed) * N)
        y = int(noise(k, 1, seed) * N)
        for step in range(4 + int(noise(k, 2, seed) * 6)):
            px[x % N, y % N] = mul(px[x % N, y % N], 0.62)
            if noise(x, y, seed + step) < 0.5:
                x += 1
            else:
                y += 1 if noise(x, y, seed + step * 3) < 0.6 else -1
    return im


def chiseled(base, seed):
    """Uitgehakt paneel: rand, verdiept vlak en een gegraveerd motief."""
    im = stone(base, seed, contrast=0.14)
    px = im.load()
    for y in range(N):
        for x in range(N):
            if x in (0, N - 1) or y in (0, N - 1):
                px[x, y] = mul(px[x, y], 1.10)
            elif x in (1, N - 2) or y in (1, N - 2):
                px[x, y] = mul(px[x, y], 0.74)
    for y in range(4, 12):                      # gegraveerde loot/blad
        for x in range(4, 12):
            d = abs(x - 7.5) + abs(y - 7.5)
            if 2.5 < d < 4.5:
                px[x, y] = mul(px[x, y], 0.70)
            elif d <= 2.5:
                px[x, y] = mul(px[x, y], 1.08)
    return im


def powder(base, seed):
    """Betonpoeder: korreliger en iets lichter dan het uitgeharde blok."""
    im = img()
    px = im.load()
    for y in range(N):
        for x in range(N):
            v = noise(x, y, seed) * 0.7 + noise(x // 2, y // 2, seed + 3) * 0.3
            px[x, y] = mul(base, 1.02 - 0.13 + v * 0.26)
    return im
