# -*- coding: utf-8 -*-
"""Hout: bast, kopse kant en planken.

Bast is verticaal, de kopse kant is concentrisch en planken zijn
horizontale delen met een naad ertussen. Alle drie tegelen naadloos over
16 pixels.
"""
from PIL import Image

from blocks import mix, mul, noise
from palette import hx
from sky import fbm2

N = 16


def bark(base, seed, groove=0.34, grain=0.12, dark=None, light=None):
    """Verticale groeven, zoals schors."""
    im = Image.new("RGBA", (N, N))
    px = im.load()
    b = hx(base)
    d = hx(dark) if dark else mul(b, 0.60)
    l = hx(light) if light else mul(b, 1.30)
    cols = [noise(x, 1, seed + 41) - 0.5 for x in range(N)]
    cols = [(cols[(x - 1) % N] + cols[x] * 2 + cols[(x + 1) % N]) / 4.0
            for x in range(N)]
    for y in range(N):
        for x in range(N):
            wob = fbm2(x, y, N, seed + 53, octaves=2, cells_x=6, cells_y=2) - 0.5
            t = cols[x] * groove + wob * groove * 0.7 \
                + (noise(x, y, seed + 23) - 0.5) * grain
            px[x, y] = mix(b, l, t * 1.8) if t > 0 else mix(b, d, -t * 1.8)
    return im


def log_top(base, seed, rings=4.0, grain=0.10, dark=None, light=None):
    """Kopse kant: jaarringen rond het hart, met een lichte schors-rand."""
    im = Image.new("RGBA", (N, N))
    px = im.load()
    b = hx(base)
    d = hx(dark) if dark else mul(b, 0.60)
    l = hx(light) if light else mul(b, 1.30)
    import math
    for y in range(N):
        for x in range(N):
            dx, dy = x + 0.5 - N / 2, y + 0.5 - N / 2
            r = (dx * dx + dy * dy) ** 0.5 / (N / 2)
            wob = (noise(x, y, seed + 61) - 0.5) * 0.10
            ring = math.sin((r + wob) * rings * 6.283)
            t = ring * 0.20 + (noise(x, y, seed + 23) - 0.5) * grain
            c = mix(b, l, t * 1.6) if t > 0 else mix(b, d, -t * 1.6)
            if r > 0.86:                                   # schorsrand
                c = mul(c, 0.74)
            px[x, y] = c
    return im


def planks(base, seed, boards=4, grain=0.14, dark=None, light=None):
    """Horizontale delen met een donkere naad en nerf in de lengte."""
    im = Image.new("RGBA", (N, N))
    px = im.load()
    b = hx(base)
    d = hx(dark) if dark else mul(b, 0.58)
    l = hx(light) if light else mul(b, 1.28)
    h = N // boards
    for y in range(N):
        idx = y // h                                       # welke plank
        tone = (noise(idx, 7, seed + 71) - 0.5) * 0.22     # plank eigen tint
        for x in range(N):
            streak = fbm2(x, y, N, seed + idx * 13, octaves=2,
                          cells_x=2, cells_y=6) - 0.5
            t = tone + streak * grain * 1.6 \
                + (noise(x, y, seed + 23) - 0.5) * grain * 0.6
            c = mix(b, l, t * 1.8) if t > 0 else mix(b, d, -t * 1.8)
            if y % h == 0:                                 # naad tussen delen
                c = mul(c, 0.66)
            px[x, y] = c
        # elke plank een eindnaad op een eigen plek
        ex = int(noise(idx, 9, seed + 83) * N)
        for yy in range(idx * h + 1, idx * h + h):
            if yy < N:
                px[ex, yy] = mul(px[ex, yy], 0.82)
    return im
