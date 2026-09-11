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
from sky import fbm

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
