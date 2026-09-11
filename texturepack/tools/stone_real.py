# -*- coding: utf-8 -*-
"""Natuurlijke blokken met een realistische korrel.

Echte steen bestaat uit korrels, niet uit ruis. Daarom is de basis hier
cellulaire ruis (Worley): het vlak wordt in kiemcellen verdeeld, elke cel
krijgt een eigen tint en een bolle vorm. Daaroverheen komt fijne ruis voor
het oppervlak. Alles tegelt naadloos omdat zowel de cel-index als de
afstand modulo 16 gaat.

Het blijft 16x16, dus de kosten zijn precies die van vanilla. "Low FPS"
komt niet van minder detail maar van niet groter worden dan het spel
verwacht.
"""
from PIL import Image

from blocks import mix, mul, noise
from palette import hx
from sky import fbm, fbm2

N = 16


def _points(cells, seed):
    """Eén kiempunt per cel, op subpixel-positie."""
    step = N / cells
    pts = []
    for cy in range(cells):
        for cx in range(cells):
            px = (cx + 0.15 + noise(cx, cy, seed) * 0.70) * step
            py = (cy + 0.15 + noise(cx, cy, seed + 5) * 0.70) * step
            pts.append((px, py, cx, cy))
    return pts


def cellular(cells, seed):
    """Per pixel: (afstand tot dichtstbijzijnde kiem 0..1, cel-toon 0..1).

    De afstand wrapt over de rand, dus de korrels lopen door aan de
    overkant van het blok.
    """
    pts = _points(cells, seed)
    reach = N / cells * 1.6
    out = [[(1.0, 0.5)] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            best, tone = 1e9, 0.5
            for (px, py, cx, cy) in pts:
                dx = abs(x + 0.5 - px)
                dy = abs(y + 0.5 - py)
                if dx > N / 2:
                    dx = N - dx                     # naadloos over de rand
                if dy > N / 2:
                    dy = N - dy
                d = (dx * dx + dy * dy) ** 0.5
                if d < best:
                    best = d
                    tone = noise(cx, cy, seed + 17)
            out[y][x] = (min(1.0, best / reach), tone)
    return out


def layered(base, seed, blotch=0.18, grain=0.12, cracks=0, cells=5,
            pebble=0.55, dark=None, light=None):
    """Steenachtige textuur: korrels + vlekken + fijne ruis."""
    im = Image.new("RGBA", (N, N))
    px = im.load()
    b = hx(base)
    d = hx(dark) if dark else mul(b, 0.58)
    l = hx(light) if light else mul(b, 1.38)
    cel = cellular(cells, seed)
    for y in range(N):
        for x in range(N):
            dist, tone = cel[y][x]
            bump = (1.0 - dist) ** 1.5                       # bol per korrel
            big = fbm(x, y, N, seed, octaves=2, cells=2)     # grondtoon
            fine = noise(x, y, seed + 23)                    # oppervlak
            t = (tone - 0.5) * pebble \
                + (bump - 0.45) * pebble * 0.55 \
                + (big - 0.5) * blotch \
                + (fine - 0.5) * grain
            c = mix(b, l, t * 1.8) if t > 0 else mix(b, d, -t * 1.8)
            px[x, y] = c
    for k in range(cracks):
        cx = int(noise(k, 70, seed) * N)
        cy = int(noise(k, 71, seed) * N)
        for step in range(5 + int(noise(k, 72, seed) * 6)):
            px[cx % N, cy % N] = mul(px[cx % N, cy % N], 0.76)
            if noise(cx, cy, seed + step) < 0.55:
                cx += 1
            else:
                cy += 1
    return im


def streaked(base, seed, streak=0.30, cells=7, pebble=0.30, grain=0.10,
             dark=None, light=None):
    """Deepslate-achtig: horizontale banden over de korrel heen.

    De banden komen uit ruis die per rij verschilt maar per kolom traag
    varieert, dus ze lopen zichtbaar horizontaal zonder een streepjespatroon
    te worden.
    """
    im = layered(base, seed, blotch=0.08, grain=grain, cells=cells,
                 pebble=pebble, dark=dark, light=light)
    px = im.load()
    rows = [noise(0, y, seed + 41) - 0.5 for y in range(N)]
    rows = [(rows[(y - 1) % N] + rows[y] * 2 + rows[(y + 1) % N]) / 4.0
            for y in range(N)]                              # zachte overgang
    for y in range(N):
        for x in range(N):
            wob = fbm2(x, y, N, seed + 53, octaves=2, cells_x=2, cells_y=5) - 0.5
            t = rows[y] * streak * 0.55 + wob * streak
            px[x, y] = mul(px[x, y], 1.0 + t)
    return im


def _two_nearest(cells, seed):
    """Per pixel: (afstand eerste kiem, afstand tweede, toon, buurtoon).

    Het verschil tussen die twee afstanden is klein op de grens tussen
    twee kiemen — precies waar de voeg van cobblestone hoort.
    """
    pts = _points(cells, seed)
    out = [[(1.0, 1.0, 0.5, 0.5)] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            f1, f2, tone, near = 1e9, 1e9, 0.5, 0.5
            for (px, py, cx, cy) in pts:
                dx = abs(x + 0.5 - px)
                dy = abs(y + 0.5 - py)
                if dx > N / 2:
                    dx = N - dx
                if dy > N / 2:
                    dy = N - dy
                d = (dx * dx + dy * dy) ** 0.5
                if d < f1:
                    f2 = f1
                    f1 = d
                    near = tone
                    tone = noise(cx, cy, seed + 17)
                elif d < f2:
                    f2 = d
                    near = noise(cx, cy, seed + 17)
            out[y][x] = (f1, f2, tone, near)
    return out


def cobble(base, seed, cells=4, spread=0.30, grain=0.10, mortar=0.9,
           gap=0.62, dark=None, light=None):
    """Keien met een donkere voeg ertussen.

    Elke kei krijgt een eigen tint en een bolle vorm. Waar de twee
    dichtstbijzijnde kiemen even ver weg zijn ligt de grens tussen twee
    keien; die lijn wordt in één keer donker gezet, niet uitgesmeerd —
    een zachte voeg leest als ruis, een harde leest als steen.
    """
    im = Image.new("RGBA", (N, N))
    px = im.load()
    b = hx(base)
    d = hx(dark) if dark else mul(b, 0.56)
    l = hx(light) if light else mul(b, 1.34)
    cel = _two_nearest(cells, seed)
    reach = N / cells * 1.5
    for y in range(N):
        for x in range(N):
            f1, f2, tone, _ = cel[y][x]
            bump = 1.0 - min(1.0, f1 / reach)               # bolle kei
            t = (tone - 0.5) * spread + (bump - 0.55) * spread * 0.9 \
                + (noise(x, y, seed + 23) - 0.5) * grain
            c = mix(b, l, t * 1.8) if t > 0 else mix(b, d, -t * 1.8)
            if f2 - f1 < mortar:                            # harde voeg
                c = mul(c, gap)
            px[x, y] = c
    return im


def facets(base, seed, cells=4, spread=0.26, grain=0.06, edge=1.42,
           edge_width=0.9, sheen=0.0, sparkle=0.0, dark=None, light=None):
    """Kristalvlakken: platte facetten met een lichte rand ertussen.

    Hetzelfde kiempatroon als cobble, maar de grens wordt juist lichter in
    plaats van donkerder — zo leest het als gebroken glas of obsidiaan.
    `sparkle` strooit er losse lichte pixels in, zoals glans op een
    breukvlak. `sheen` legt een lichtval van boven naar beneden overheen —
    let op dat die per blok herhaalt, dus een muur krijgt dan banden.
    """
    im = Image.new("RGBA", (N, N))
    px = im.load()
    b = hx(base)
    d = hx(dark) if dark else mul(b, 0.52)
    l = hx(light) if light else mul(b, 1.70)
    cel = _two_nearest(cells, seed)
    for y in range(N):
        for x in range(N):
            f1, f2, tone, near = cel[y][x]
            t = (tone - 0.5) * spread + (noise(x, y, seed + 23) - 0.5) * grain
            c = mix(b, l, t * 1.6) if t > 0 else mix(b, d, -t * 1.6)
            if f2 - f1 < edge_width:
                # alleen de lichtste kant van een grens krijgt de glans,
                # anders wordt het hele blok een net van lichte lijnen
                c = mul(c, edge if tone > near else 0.80)
            if sheen:
                c = mul(c, 1.0 + sheen * (0.5 - y / (N - 1.0)))
            if sparkle and noise(x, y, seed + 37) > 1.0 - sparkle:
                c = mix(c, hx("FFFFFF"), 0.42)
            px[x, y] = c
    return im
