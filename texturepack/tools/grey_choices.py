# -*- coding: utf-8 -*-
"""Wat er per stuk gekozen is voor het grijze pack.

Bijhouden terwijl we door de lijst lopen, zodat de keuzes niet in de chat
blijven hangen maar in het pack terechtkomen.
"""

# Namen die we bewust NIET meeleveren: wat niet in het pack zit, pakt
# Minecraft uit zijn eigen bestanden.
VANILLA = {
    "mace",
    "netherite_helmet", "netherite_chestplate",
    "netherite_leggings", "netherite_boots",
}

# Wat al vastligt.
GEKOZEN = {
    "netherite_sword": "grijs met witte gloed van boven naar beneden",
    "trident": "donker grijs, vanilla-silhouet",
    "netherite_pickaxe": "donker grijs met gloed",
    "netherite_axe": "donker grijs met gloed, vlakke bovenkant",
    "end_crystal": "wit, dunne rand per vlak, midden doorzichtig",
    "respawn_anchor": "wit, witte gloed in de cirkel, bovenkant 5 ringen",
    "stone": "licht en glad: layered('989EA4', 13, cells=6, pebble=0.26,"
             " blotch=0.07, grain=0.07)",
    "deepslate": "bijna zwart: layered('343940', 23, cells=7, pebble=0.34,"
                 " blotch=0.07, grain=0.10)",
    "dirt": "donker bruin: layered('5E452E', 32, cells=5, pebble=0.50,"
            " blotch=0.12, grain=0.18)",
    "gras": "grof met contrast: blades(44, spread=0.40, fine=0.18,"
            " length=3), rand depth=7",
    "hout": "eik licht: bark('6E5134', 51), log_top/planks('B08E5C', 51)",
    "cobblestone": "normale keien: cobble('8C9096', 62, cells=4,"
                   " spread=0.26, grain=0.09)",
    "obsidian": "zwart en glad: layered('15171A', 71, cells=7, pebble=0.26,"
                " blotch=0.06, grain=0.06)",
    "end_stone": "vanilla geel-wit: layered('DCD8A8', 84, cells=6,"
                 " pebble=0.24, blotch=0.06, grain=0.07)",
    "bladeren": "veel gaten: leaves(92, spread=0.30, holes=0.26, clump=4)",
    "zand": "vanilla tint: layered('DBCB9A', 101, cells=8, pebble=0.16,"
            " blotch=0.05, grain=0.12)",
    "grind": "vanilla tint: cobble('878B90', 101, cells=6, spread=0.30,"
             " grain=0.12, gap=0.66)",
    "netherrack": "vanilla rood: layered('7A3A38', 111, cells=5,"
                  " pebble=0.42, blotch=0.14, grain=0.16)",
    "wolken": "dunne slierten: clouds(coverage=0.40, lump=6, wisp=0.55,"
              " wind=3.0)",
}

# Nog te doen, in volgorde.
TE_DOEN = [
 "overige pvp items",
    "natuurlijke blokken", "end crystal", "respawn anchor",
    "lucht dag", "lucht nacht", "totem",
]
