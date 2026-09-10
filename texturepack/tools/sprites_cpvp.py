# -*- coding: utf-8 -*-
"""CPvP-uitrusting: mace, drietand, kruisboog en wat erbij hoort.

De mace gebruikt dezelfde bast-steel, touwgreep en rank als het gereedschap
uit deel 1, zodat hij bij de rest van het pack hoort.
"""
from palette import hx
from sprites_items import P, S

MACE = S(
    "",
    "......111111",
    ".....11111111",
    "....1122222111",
    "....1123322111",
    "....1123322111",
    "....1122222111",
    ".....11111111",
    "......111111",
    ".......WW",
    "......WW",
    "....vWW",
    "...vVW",
    "...WW",
    "..cW",
    "..cc",
)

TRIDENT = S(
    "",
    "...........1.1.1",
    "...........1.1.1",
    "...........11111",
    "............111",
    "...........12",
    "..........12",
    ".........12",
    "........12",
    ".......12",
    "......12",
    ".....12",
    "....12",
    "...12",
    "..12",
    ".12",
)


def crossbow(pull=0, ammo=None):
    """Kruisboog: brede boog boven, pees ertussen, kolf eronder.

    pull schuift de pees omlaag (0 = ontspannen, 3 = volledig gespannen).
    ammo tekent wat er op de kolf ligt: "arrow" of "firework".
    """
    rows = [
        "................",
        "................",
        ".1............1.",
        ".111........111.",
        "..111......111..",
        "...1........1...",
        "...1........1...",
        "...1........1...",
        "......1111......",
        "......1111......",
        "......11........",
        "......11........",
        "......11........",
        ".....1111.......",
        ".....1111.......",
        "................",
    ]
    string_row = 5 + pull
    r = list(rows[string_row])
    for x in range(4, 12):
        if r[x] == ".":
            r[x] = "c"
    rows[string_row] = "".join(r)
    if ammo:
        ch = "3" if ammo == "arrow" else "4"
        for y in (8, 9):
            row = list(rows[y])
            for x in (6, 7, 8, 9):
                row[x] = ch
            rows[y] = "".join(row)
    return rows


WIND_CHARGE = S(
    "", "",
    ".....1111",
    "...11333311",
    "..1133113311",
    "..1311111131",
    "..1311111131",
    "..1133113311",
    "...11333311",
    ".....1111",
)

BREEZE_ROD = S(
    "", "",
    "..........11",
    ".........131",
    "........131",
    ".......131",
    "......131",
    ".....131",
    "....131",
    "...131",
    "..131",
    "..11",
)

HEAVY_CORE = S(
    "", "", "",
    "....111111",
    "..11322311",
    "..13222231",
    "..13222231",
    "..13222231",
    "..11322311",
    "....111111",
)


def items():
    """naam -> (vorm, palet)."""
    out = {}
    # de kop van de mace deelt het sintelwortel-palet met netherite
    # donkere kop met een groene kern, zodat hij bij de crystal hoort
    out["mace"] = (MACE, {"1": hx("2E2A2E"), "2": hx("4A4650"), "3": hx("46A85E")})
    out["trident"] = (TRIDENT, P("BCC8C0", "7E8A84"))
    wood = P("A07B4E", "6B4F2C", "6E7075", "C4362E")
    out["crossbow_standby"] = (crossbow(0), wood)
    for i in range(3):
        out[f"crossbow_pulling_{i}"] = (crossbow(i + 1), wood)
    out["crossbow_arrow"] = (crossbow(3, "arrow"), wood)
    out["crossbow_firework"] = (crossbow(3, "firework"), wood)
    out["wind_charge"] = (WIND_CHARGE, P("BCD2C8", "7E948C", "E4F0EA"))
    out["breeze_rod"] = (BREEZE_ROD, P("8ED2C4", "4E8A80", "D8F4EC"))
    out["heavy_core"] = (HEAVY_CORE, P("8E9A94", "3A423E", "C4D0CA"))
    return out
