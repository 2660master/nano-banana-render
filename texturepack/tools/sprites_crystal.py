# -*- coding: utf-8 -*-
"""End crystal en respawn anchor, met een echt patroon in plaats van ruis.

De vorige versie vulde het vel met ruis. Dat werkt voor vacht, maar een
kristal heeft juist vlakken en breuklijnen nodig — anders leest het als
een vlek. Hier worden de facetten expliciet gelegd.
"""
from PIL import Image

from blocks import mul
from palette import hx

# groen, van diep naar licht
GREEN = ["1E4A2E", "2A6B3E", "36894E", "46A85E", "5EC474", "8CE49A"]


def _facet_id(x, y, cell, seed):
    """Twee scheve assen delen het vlak op in onregelmatige facetten."""
    a = (x + 2 * y) // cell
    b = (2 * x - y) // cell
    n = (a * 73856093 ^ b * 19349663 ^ seed * 83492791) & 0xFFFFFFFF
    return (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF


def facets(w, h, cols, seed=0, cell=16, glow=1.30):
    """Geslepen vlak: grote facetten, elk met licht over het oppervlak.

    Klein snijden geeft ruis, en dat was juist het probleem. Dus weinig
    en grote vlakken, met binnen elk vlak een verloop van licht naar
    donker, en een dunne naad ertussen.
    """
    im = Image.new("RGBA", (w, h))
    px = im.load()
    n = len(cols)
    for y in range(h):
        for x in range(w):
            f = _facet_id(x, y, cell, seed)
            col = hx(cols[(f >> 8) % n])
            # plaats binnen het facet bepaalt hoeveel licht het vangt
            u = ((x + 2 * y) % cell) / cell
            v = ((2 * x - y) % cell) / cell
            shade = 1.18 - (u * 0.22 + v * 0.20)
            border = any(_facet_id((x + dx) % w, (y + dy) % h, cell, seed) != f
                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            px[x, y] = mul(col, glow) if border else mul(col, shade)
    return im


def end_crystal(w=64, h=32):
    return facets(w, h, GREEN, seed=1, cell=17)


def end_crystal_beam(w=16, h=16):
    return facets(w, h, GREEN[2:], seed=3, cell=9, glow=1.24)


# ---------------------------------------------------------------- anchor
# 1/2 = donkere rand, 3/4 = steen, 5..8 = groene gloed (8 is het felst)
ANCHOR_PAL = {
    "1": hx("14161A"), "2": hx("1E2228"), "3": hx("2A3038"), "4": hx("343C46"),
    "5": hx("2A6B3E"), "6": hx("46A85E"), "7": hx("6ED184"), "8": hx("B4F4C2"),
}

TOP = [
    "1111111111111111",
    "1222222222222221",
    "1233333333333321",
    "1233333366333321",
    "1233333677633321",
    "1233336777763321",
    "1233367788776321",
    "1233677888887321",
    "1233677888887321",
    "1233367788776321",
    "1233336777763321",
    "1233333677633321",
    "1233333366333321",
    "1233333333333321",
    "1222222222222221",
    "1111111111111111",
]

BOTTOM = [
    "1111111111111111",
    "1222222222222221",
    "1233333333333321",
    "1233444444433321",
    "1233444444433321",
    "1233444334433321",
    "1233443333433321",
    "1233433333343321",
    "1233433333343321",
    "1233443333433321",
    "1233444334433321",
    "1233444444433321",
    "1233444444433321",
    "1233333333333321",
    "1222222222222221",
    "1111111111111111",
]


def anchor_side(charge):
    """Zijkant met een venster dat van onderaf volloopt met gloed."""
    rows = []
    for y in range(16):
        row = []
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                ch = "1"
            elif x in (1, 14) or y in (1, 14):
                ch = "2"
            elif 4 <= x <= 11 and 3 <= y <= 12:
                if charge and y >= 13 - charge * 2 - 1:
                    # kern feller dan de rand van het venster
                    ch = "8" if 6 <= x <= 9 else "7"
                else:
                    ch = "4" if (x + y) % 3 else "3"
            else:
                ch = "3" if (x * 5 + y * 3) % 4 else "4"
            row.append(ch)
        rows.append("".join(row))
    return rows


def build_blocks():
    """naam -> 16x16 afbeelding, voor de blokkenmap."""
    import render
    out = {
        "respawn_anchor_top": render.render(TOP, ANCHOR_PAL, "anchor_top",
                                            outline=False, rim=False, relief=0),
        "respawn_anchor_top_off": render.render(BOTTOM, ANCHOR_PAL, "anchor_off",
                                                outline=False, rim=False, relief=0),
        "respawn_anchor_bottom": render.render(BOTTOM, ANCHOR_PAL, "anchor_bottom",
                                               outline=False, rim=False, relief=0),
    }
    for c in range(5):
        out[f"respawn_anchor_side{c}"] = render.render(
            anchor_side(c), ANCHOR_PAL, f"anchor_side{c}",
            outline=False, rim=False, relief=0)
    return out


def build_entities():
    return {
        "entity/end_crystal/end_crystal": end_crystal(),
        "entity/end_crystal/end_crystal_beam": end_crystal_beam(),
    }
