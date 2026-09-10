# -*- coding: utf-8 -*-
"""Planten, bloemen en gewassen: hand getekende vormen plus groeistadia.

Let op welke texturen het spel zelf inkleurt. short_grass, fern, tall_grass,
large_fern, vine en sugar_cane worden met de biome-kleur vermenigvuldigd —
die krijgen hier dus een bleke, bijna neutrale basis. Bloemen, gewassen,
mos en glow lichen hebben een vaste kleur.
"""
import blocks as G
from palette import hx


def S(*rows):
    out = [r.ljust(16, ".") for r in rows]
    for r in out:
        if len(r) != 16:
            raise ValueError("rij te lang: %r" % r)
    while len(out) < 16:
        out.append("." * 16)
    if len(out) != 16:
        raise ValueError("te veel rijen")
    return out


# ------------------------------------------------------------------- vormen
ROUND = S(
    "", "",
    "......ppp",
    ".....pp1pp",
    ".....ppppp",
    "......ppp",
    ".......s",
    ".......s",
    "......ls",
    ".......sl",
    ".......s",
    ".......s",
    "......ls",
    ".......s",
    ".......s",
    ".......s",
)

PUFF = S(
    "",
    "....ppppp",
    "...ppp1ppp",
    "...ppppppp",
    "....ppppp",
    ".....ppp",
    ".......s",
    "......ls",
    ".......s",
    ".......sl",
    ".......s",
    ".......s",
    "......ls",
    ".......s",
    ".......s",
    ".......s",
)

BELLS = S(
    "", "", "",
    ".......s",
    "......ps",
    ".....pp.s",
    "......p.sp",
    ".......s.p",
    "......ls",
    ".......s",
    ".......s",
    "......ls",
    ".......s",
    ".......s",
    ".......s",
    ".......s",
)

TULIP = S(
    "", "",
    "......p.p",
    "......ppp",
    "......ppp",
    ".......p",
    ".......s",
    ".......s",
    "......ls",
    ".......sl",
    ".......s",
    ".......s",
    "......ls",
    ".......s",
    ".......s",
    ".......s",
)

# Grasachtigen staan bewust in grijstinten: het spel kleurt ze zelf in.
SHORT_GRASS = S(
    "", "", "", "",
    "..g......g...g",
    "..g...g..g...g",
    "..g..gg..g..gg",
    "..G.gG...G..gG",
    "..G.G....G..G",
    ".gG.G...gG..G",
    ".GG.G...GG.gG",
    ".GG.GG..GG.GG",
    "..GGGG..GGGG",
    "...GG....GG",
)

FERN = S(
    "", "",
    ".......g",
    "......ggg",
    ".....g.g.g",
    "....gg.g.gg",
    "...g..ggg..g",
    "...gg.ggg.gg",
    "....g.GGG.g",
    "...gg.GGG.gg",
    "....g.GGG.g",
    "......GGG",
    "......GGG",
    ".....GGGGG",
    "......GGG",
    "",
)

TALL_TOP = S(
    "", "",
    "..g..........g",
    "..g...g..g...g",
    "..g..gg..g...g",
    "..gg.gg.gg..gg",
    "..gg.gg.gg..gg",
    "..gg.Gg.gg..gg",
    "..Gg.Gg.Gg..Gg",
    "..Gg.GG.Gg..GG",
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
)

TALL_BOTTOM = S(
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
    "..GG.GG.GG..GG",
    ".GGG.GG.GG..GG",
    ".GGG.GG.GGG.GG",
    ".GGG.GG.GGG.GG",
    ".GGG.GGGGGG.GG",
    ".GGGGGGGGGGGGG",
    ".GGGGGGGGGGGGG",
    ".GGGGGGGGGGGGG",
    "..GGGGGGGGGGG",
    "..GGGGGGGGGG",
    "...GGGGGGGG",
)

VINE = S(
    "..g..........g",
    "..g...g......g",
    "..G..gg..g...G",
    "..G..gG..g...G",
    "..G.gG...G..gG",
    ".gG.G....G..G",
    ".G..G....G..G",
    ".G..G...gG..G",
    ".G.gG...G...G",
    ".G.G....G...G",
    ".G.G....G...G",
    "...G....G...G",
    "...G....G",
    "...G....G",
    "........G",
    "",
)

GLOW_LICHEN = S(
    "...a....a",
    "..aAa..aA",
    "...a..aAa...a",
    ".....aA.a..aA",
    "..a..a....aAa",
    ".aAa......a",
    "..a...aAa",
    "......aA.a..a",
    "...a...a...aAa",
    "..aAa.....aA",
    "...a..a....a",
    ".....aAa",
    "..a...a....a",
    ".aAa......aAa",
    "..a........a",
    "",
)

SUGAR_CANE = S(
    "...g...g....g",
    "...g...g....g",
    "...g..gg....g",
    "...G..gG....G",
    "...G..GG....G",
    "..gG..GG...gG",
    "..GG..GG...GG",
    "..GG..GG...GG",
    "..GG..GG...GG",
    "..GG..GG...GG",
    "..GG..GG...GG",
    "..GG..GG...GG",
    "..GG..GG...GG",
    "..GG..GG...GG",
    "..GG..GG...GG",
    "..GG..GG...GG",
)


# ------------------------------------------------------------------ paletten
STEM = {"s": hx("4E7A32"), "l": hx("6FA344")}
# bleek grijsgroen: het spel vermenigvuldigt dit met de biome-kleur
TINTED = {"g": hx("C8D2BE"), "G": hx("9BAA8E")}
LICHEN = {"a": hx("7FA98C"), "A": hx("A8CFA4")}

FLOWERS = [
    # naam,                vorm,   bloemblad, hart
    ("dandelion",          PUFF,   "F0D24A", "FFF0A0"),
    ("poppy",              ROUND,  "C4362E", "3A2418"),
    ("cornflower",         ROUND,  "4C6BC4", "8AA0E0"),
    ("oxeye_daisy",        ROUND,  "EFEDE0", "E8C64A"),
    ("allium",             PUFF,   "A97BC4", "D8BCE8"),
    ("azure_bluet",        ROUND,  "DCE4E8", "E8D66A"),
    ("blue_orchid",        ROUND,  "3E9BC4", "DCEFF4"),
    ("lily_of_the_valley", BELLS,  "EDEFE4", "EDEFE4"),
    ("red_tulip",          TULIP,  "BE3A32", "2E1E14"),
    ("orange_tulip",       TULIP,  "D2833A", "2E1E14"),
    ("white_tulip",        TULIP,  "E6E6DC", "2E1E14"),
    ("pink_tulip",         TULIP,  "D9A0B4", "2E1E14"),
]

PLANTS = [
    ("short_grass",     SHORT_GRASS, TINTED),
    ("fern",            FERN,        TINTED),
    ("tall_grass_top",  TALL_TOP,    TINTED),
    ("tall_grass_bottom", TALL_BOTTOM, TINTED),
    ("large_fern_top",  TALL_TOP,    TINTED),
    ("large_fern_bottom", TALL_BOTTOM, TINTED),
    ("vine",            VINE,        TINTED),
    ("sugar_cane",      SUGAR_CANE,  TINTED),
    ("glow_lichen",     GLOW_LICHEN, LICHEN),
]

# gewas, stengelkleur, aarkleur, aantal stadia
CROPS = [
    ("wheat",     "8FA24E", "D8B94A", 8),
    ("carrots",   "4E8A32", "E07A28", 4),
    ("potatoes",  "4E8A32", "86AE4E", 4),
    ("beetroots", "5B7A2E", "B4382E", 4),
]


def flower_palette(petal, centre):
    p = dict(STEM)
    p["p"] = hx(petal)
    p["1"] = hx(centre)
    return p


def crop(stalk, head, stage, stages, seed):
    """Groeistadium van een gewas: stengels die met het stadium meegroeien."""
    im = G.img()
    px = im.load()
    frac = stage / (stages - 1)
    h = int(4 + 11 * frac)
    for i, cx in enumerate((1, 5, 9, 13)):
        top = max(0, G.N - h - int(G.noise(i, 3, seed) * 2))
        for y in range(top, G.N):
            px[cx, y] = G.mul(stalk, 0.90 + G.noise(cx, y, seed) * 0.20)
            if y > top + 1 and (y - top) % 3 == 0:
                px[(cx + 1) % G.N, y] = G.mul(stalk, 0.78)
        if frac > 0.55 and head is not None:
            for y in range(top, min(G.N, top + 4)):
                px[cx, y] = G.mul(head, 0.90 + G.noise(cx, y, seed + 5) * 0.20)
                px[(cx + 1) % G.N, y] = G.mul(head, 0.76)
    return im
