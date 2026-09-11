# -*- coding: utf-8 -*-
"""End crystal: wit, hol, alleen de buitenranden.

Het kristalmodel is een kubus van 8x8x8 met een kleinere kern erin. Elk
vlak van die kubus pakt een blokje van 8 bij 8 uit het vel. Door alleen
op de veelvouden van 8 een witte lijn te zetten, krijgt élk vlak vanzelf
een nette rand en blijft het midden doorzichtig — je kijkt er dwars
doorheen. De kern is kleiner dan een cel en valt dus binnen het lege
midden: precies het "midden moet weg" dat gevraagd is.

Dat werkt zonder te hoeven weten waar de kern precies in het vel ligt.
"""
from PIL import Image

from palette import hx

CELL = 8


def cage(w=64, h=32, thickness=1, corners=0, diagonal=False,
         col="FFFFFF", dim="C8D2D8"):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    white, grey = hx(col), hx(dim)
    for y in range(h):
        for x in range(w):
            cx, cy = x % CELL, y % CELL
            on_edge = (cx < thickness or cx >= CELL - thickness
                       or cy < thickness or cy >= CELL - thickness)
            in_corner = corners and (
                (cx < corners or cx >= CELL - corners)
                and (cy < corners or cy >= CELL - corners))
            on_diag = diagonal and (cx == cy or cx == CELL - 1 - cy)
            if on_edge:
                px[x, y] = white if not in_corner else white
            elif on_diag:
                px[x, y] = grey
    return im


def variants():
    return [
        ("1  dunne rand", cage(thickness=1)),
        ("2  dikke rand", cage(thickness=2)),
        ("3  rand met kruis", cage(thickness=1, diagonal=True)),
        ("4  dikke rand, kruis", cage(thickness=2, diagonal=True)),
    ]
