# -*- coding: utf-8 -*-
"""Strakke PvP-vormen voor het grijze pack.

Vanilla-silhouetten, zonder de blaadjes en bast van het natuurpack.
Legenda: L hoogsel, M basis, D schaduw, K outline, H pareerstang, G greep.
"""
from sprites_items import S

SWORD = S(
    "",
    "............LLM",
    "...........LLMD",
    "..........LLMD",
    ".........LLMD",
    "........LLMD",
    ".......LLMD",
    "......LLMD",
    ".....LLMD",
    "....LLMD",
    "...HHHHHH",
    "..HHHHHH",
    "..HGG",
    ".HGG",
    ".GG",
    "GG",
)

# Zware kop rechtsboven met een lichte kern, korte steel naar linksonder.
MACE = S(
    "",
    ".......KKKKKK",
    "......KDDDDDDK",
    ".....KDDMMMMDDK",
    ".....KDMLLLLMDK",
    ".....KDMLLLLMDK",
    ".....KDDMMMMDDK",
    "......KDDDDDDK",
    ".......KKKKKK",
    ".......GG",
    "......GG",
    ".....GG",
    "....GG",
    "...GG",
    "..GG",
    ".GG",
)

TRIDENT = S(
    "",
    "........LL.LL.LL",
    "........LL.LL.LL",
    "........LLLLLLLL",
    ".........MMMMMM",
    "..........MMMD",
    "..........MD",
    ".........MD",
    "........MD",
    ".......MD",
    "......MD",
    ".....MD",
    "....MD",
    "...MD",
    "..MD",
    ".MD",
)

PICKAXE = S(
    "",
    ".....LLLLLL",
    "...LLLLMMMMMM",
    ".LLLLMMMMMDDDDD",
    ".MD.....GG...DD",
    ".D......GG....D",
    ".......GG",
    ".......GG",
    "......GG",
    "......GG",
    ".....GG",
    ".....GG",
    "....GG",
    "....GG",
    "...GG",
    "...GG",
)

# Wig met een inspringing onder de kop; dat is wat een bijl als bijl laat lezen.
AXE = S(
    "",
    "..LLLLLL",
    "..LMMMMMKGG",
    "..LMMMMMKGG",
    "..LMMMMKGG",
    "..LMMMDKGG",
    "...LMDKGG",
    "....DDKGG",
    ".......GG",
    "......GG",
    "......GG",
    ".....GG",
    ".....GG",
    "....GG",
    "....GG",
    "...GG",
)



# ------------------------------------------------------------------ de boog
# Met de hand tekenen gaf een rechte streep in plaats van een boog, dus de
# vorm wordt hier gerekend. De houtboog is een kwartcirkel met middelpunt
# rechtsonder (13,13) en straal 11: die gaat precies door de twee punten
# (13,2) en (2,13). De pees is de rechte lijn tussen die punten, en bij
# spannen zakt het midden ervan naar de greep toe.
def bow_rows(pull=0.0):
    import math

    g = [["."] * 16 for _ in range(16)]

    def put(x, y, ch, over):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < 16 and 0 <= yi < 16 and g[yi][xi] in over:
            g[yi][xi] = ch

    cx, cy, r = 13.0, 13.0, 11.0
    steps = 400
    # Volgorde telt: eerst de buitenrand, dan de binnenkant, dan de kern
    # eroverheen. Andersom vreet een van de randen de boog op waar de
    # kromme bijna recht loopt.
    for i in range(steps):
        f = i / (steps - 1.0)
        t = f * (math.pi / 2)
        sx, sy = math.sin(t), math.cos(t)
        if 0.12 < f < 0.88:                       # de punten blijven dun
            put(cx - (r + 1.0) * sx, cy - (r + 1.0) * sy, "L", ".")
    for i in range(steps):
        t = i / (steps - 1.0) * (math.pi / 2)
        sx, sy = math.sin(t), math.cos(t)
        put(cx - (r - 1.0) * sx, cy - (r - 1.0) * sy, "D", ".")
    for i in range(steps):
        t = i / (steps - 1.0) * (math.pi / 2)
        sx, sy = math.sin(t), math.cos(t)
        put(cx - r * sx, cy - r * sy, "M", ".LD")

    ax, ay = 13.0, 2.0
    bx, by = 2.0, 13.0
    mx = (ax + bx) / 2 + pull * 0.7071
    my = (ay + by) / 2 + pull * 0.7071
    for (x0, y0) in ((ax, ay), (bx, by)):
        for i in range(200):
            t = i / 199.0
            put(x0 + (mx - x0) * t, y0 + (my - y0) * t, "v", ".")

    return ["".join(row) for row in g]


BOW = bow_rows(0.0)
BOW_PULL_1 = bow_rows(1.6)
BOW_PULL_2 = bow_rows(3.2)
BOW_PULL_3 = bow_rows(4.6)
