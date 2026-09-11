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
