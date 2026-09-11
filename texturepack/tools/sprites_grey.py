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


# ------------------------------------------------------------- de kruisboog
# Zelfde aanpak als de boog: rekenen in plaats van tellen. De kolf loopt
# schuin van linksonder naar de kop; de bogen zijn een boog die naar voren
# bolt, zodat de pees er als rechte koorde achter valt.
def crossbow_rows(pull=0.0, arrow=None):
    """Kruisboog, recht van voren gezien.

    Schuin leggen zoals de boog werkte niet: op zestien pixels lopen de
    kolf, de bogen en de pees dan door elkaar heen en zie je alleen nog
    een kluwen. Recht van voren blijft elk onderdeel apart leesbaar.
    """
    import math

    g = [["."] * 16 for _ in range(16)]

    def put(x, y, ch, over):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < 16 and 0 <= yi < 16 and g[yi][xi] in over:
            g[yi][xi] = ch

    def line(x0, y0, x1, y1, ch, over, steps=240):
        for i in range(steps):
            t = i / (steps - 1.0)
            put(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, ch, over)

    # kolf: staande balk met de greep onderaan
    for x in (7, 8):
        line(x, 4, x, 10, "M", ".")
        line(x, 10, x, 14, "G", ".")
    line(9, 5, 9, 10, "D", ".")
    line(6, 11, 6, 13, "G", ".")
    put(6, 10, "M", ".")

    # pees: rechte lijn tussen de punten, bij spannen naar beneden
    ax, ay = 1.5, 7.0
    bx, by = 14.5, 7.0
    mx, my = 8.0, 7.0 + pull
    line(ax, ay, mx, my, "v", ".")
    line(bx, by, mx, my, "v", ".")

    # bogen: vlakke boog die naar boven bolt, pees eronder als koorde
    cx, cy, r = 8.0, 10.28, 7.28
    a0 = math.atan2(ay - cy, ax - cx)
    a1 = math.atan2(by - cy, bx - cx)
    # neem altijd de korte weg langs de cirkel; anders loopt de boog
    # onderlangs en krijg je twee staande balken langs de rand
    if a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    elif a1 - a0 < -math.pi:
        a1 += 2 * math.pi
    # twee lagen dik, niet drie: met een derde ring wordt de boog een
    # paddenstoelenhoed in plaats van een boog
    for i in range(320):
        t = a0 + (a1 - a0) * (i / 319.0)
        put(cx + r * math.cos(t), cy + r * math.sin(t), "M", ".Dv")
    for i in range(320):
        t = a0 + (a1 - a0) * (i / 319.0)
        put(cx + (r - 1.0) * math.cos(t), cy + (r - 1.0) * math.sin(t),
            "L", ".")

    if arrow:
        # de pijl ligt in de goot van de kolf en steekt er bovenuit
        line(7, 1, 7, 11, "L", ".vMD")
        put(7, 0, "L", ".")
        if arrow == "pijl":
            put(6, 2, "D", ".")
            put(8, 2, "D", ".")
        else:                                   # vuurwerk: dikke kop
            for y in (1, 2, 3):
                put(6, y, "L", ".vMD")
                put(8, y, "L", ".vMD")

    return ["".join(row) for row in g]


CROSSBOW = crossbow_rows(0.0)
CROSSBOW_PULL_1 = crossbow_rows(1.4)
CROSSBOW_PULL_2 = crossbow_rows(2.6)


# De appel: 'v' is het blaadje, dat krijgt geen randschaduw.
APPLE = S(
    "",
    "........K.......",
    ".......KvK......",
    "....LLLKvKDD....",
    "...LLMMMMMMMDD..",
    "..LLMMMMMMMMMDD.",
    "..LMMMMMMMMMMMD.",
    "..LMMMMMMMMMMMD.",
    "..LMMMMMMMMMMMD.",
    "..LMMMMMMMMMMMD.",
    "...LMMMMMMMMMD..",
    "...LMMMMMMMMMD..",
    "....LMMMMMMMD...",
    ".....LMMMMMD....",
    "......DDDDD.....",
    "",
)
