# -*- coding: utf-8 -*-
"""Gras: de bovenkant en de rand op de zijkant.

Let op: Minecraft vermenigvuldigt grass_block_top, grass_block_side_overlay
en het losse gras met een biome-kleur. Wat hier wordt getekend is dus
bewust grijs — de groene tint komt uit het spel. Wie hier groen tekent
krijgt in het spel dubbel groen.

Alles tegelt naadloos en blijft 16x16.
"""
from PIL import Image

from blocks import mix, mul, noise
from palette import hx
from sky import fbm2

N = 16


def blades(seed, base="9A9A9A", spread=0.22, fine=0.14, length=3):
    """Grijze grasmat: korte sprieten met wat variatie in toon.

    De sprieten lopen licht schuin naar boven, zoals gras dat plat ligt.
    """
    im = Image.new("RGBA", (N, N))
    px = im.load()
    b = hx(base)
    d = mul(b, 0.70)
    l = mul(b, 1.26)
    for y in range(N):
        for x in range(N):
            # een spriet is een korte streep: neem de ruis een paar pixels
            # terug mee, zodat naburige pixels bij dezelfde spriet horen
            v = 0.0
            for k in range(length):
                v += noise((x - k) % N, (y + k) % N, seed) / length
            patch = fbm2(x, y, N, seed + 9, octaves=2, cells_x=3, cells_y=3)
            t = (v - 0.5) * spread \
                + (patch - 0.5) * spread * 0.8 \
                + (noise(x, y, seed + 31) - 0.5) * fine
            px[x, y] = mix(b, l, t * 2.0) if t > 0 else mix(b, d, -t * 2.0)
    return im


def overlay(seed, base="9A9A9A", depth=5, spread=0.22):
    """De grasrand die over de zijkant van het blok valt.

    Bovenaan dicht, naar beneden toe rafelig: per kolom een eigen
    hoogte, dus je ziet losse slierten over het dirt hangen.
    """
    top = blades(seed, base=base, spread=spread)
    tp = top.load()
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = im.load()
    for x in range(N):
        h = 2 + int(noise(x, 3, seed + 7) * depth)
        for y in range(h):
            px[x, y] = tp[x, y]
        # een enkele losse spriet nog een pixel lager
        if noise(x, 4, seed + 13) > 0.55:
            px[x, h % N] = mul(tp[x, h % N], 0.92)
    return im


def tint(im, colour="91BD59"):
    """Zoals het spel het doet: vermenigvuldigen met de biome-kleur."""
    c = hx(colour)
    out = im.copy()
    op = out.load()
    px = im.load()
    for y in range(N):
        for x in range(N):
            r, g, b, a = px[x, y]
            op[x, y] = (r * c[0] // 255, g * c[1] // 255, b * c[2] // 255, a)
    return out
