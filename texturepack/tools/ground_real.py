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


def leaves(seed, base="9A9A9A", spread=0.28, holes=0.16, clump=4,
           shadow=0.30):
    """Bladerdek, ook weer grijs omdat het spel er de biome-kleur op legt.

    Bladeren zitten in plukjes: een grove ruis bepaalt waar het dicht is
    en waar je erdoorheen kijkt. Onder elk gat komt een donkere pixel,
    zodat het dek diepte krijgt in plaats van plat te ogen.
    """
    im = Image.new("RGBA", (N, N))
    px = im.load()
    b = hx(base)
    d = mul(b, 0.62)
    l = mul(b, 1.32)
    clumps = [[fbm2(x, y, N, seed + 3, octaves=2, cells_x=clump, cells_y=clump)
               for x in range(N)] for y in range(N)]
    for y in range(N):
        for x in range(N):
            t = (clumps[y][x] - 0.5) * spread \
                + (noise(x, y, seed + 21) - 0.5) * spread * 0.9
            px[x, y] = mix(b, l, t * 2.0) if t > 0 else mix(b, d, -t * 2.0)
    if holes:
        gat = []
        for y in range(N):
            for x in range(N):
                if noise(x, y, seed + 47) < holes and clumps[y][x] < 0.56:
                    gat.append((x, y))
        for (x, y) in gat:
            px[x, y] = (0, 0, 0, 0)
        for (x, y) in gat:                                  # schaduw eronder
            below = (x, (y + 1) % N)
            if px[below] != (0, 0, 0, 0):
                px[below] = mul(px[below], 1.0 - shadow)
    return im
