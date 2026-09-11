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
}

# Nog te doen, in volgorde.
TE_DOEN = [
 "overige pvp items",
    "natuurlijke blokken", "end crystal", "respawn anchor",
    "lucht dag", "lucht nacht", "totem",
]
