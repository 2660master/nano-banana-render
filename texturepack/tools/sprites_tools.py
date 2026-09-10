"""Gereedschap-silhouetten. Alle vijf delen exact dezelfde steel + hetzelfde
blaadje, zodat de set als een familie leest. Legenda:
  .  transparant      L/M/D/K  materiaal licht/basis/schaduw/outline
  w/W/k  bast licht/midden/donker      c/C  touw       v/V  blad licht/donker
  *  materiaal-accent

Standaard steel: y=2..15, x0 = 9 - (y-2)//2, breedte 2.
"""

SWORD = [
    "................",
    ".............LM.",
    "............LMD.",
    "...........LMD..",
    "..........LMD...",
    ".........LMD....",
    "........LMD.....",
    ".......LMD......",
    "...v..LMD.......",
    "..vvVLMD........",
    "....wWWWk.......",
    "...wWWWk........",
    "...wW...........",
    "..wW............",
    "..cW............",
    ".cc.............",
]

PICKAXE = [
    "................",
    ".....LLLLLL.....",
    "...LLLLMMMMMM...",
    ".LLLLMMMMMDDDDD.",
    ".MD.....WW...DD.",
    ".D......WW....D.",
    ".......WW.......",
    ".......WW.......",
    ".....vWW........",
    "...vvVWW........",
    "....VWW.........",
    ".....WW.........",
    "....WW..........",
    "....WW..........",
    "...cW...........",
    "...cc...........",
]

AXE = [
    "................",
    "..LLLLL.........",
    "..LLMMMM........",
    "..LLMMMMMWW.....",
    "..LLMMMMWW......",
    "..LLMMMDWW......",
    "...LLMDWW.......",
    "....LDDWW.......",
    ".....vWW........",
    "...vvVWW........",
    "....VWW.........",
    ".....WW.........",
    "....WW..........",
    "....WW..........",
    "...cW...........",
    "...cc...........",
]

SHOVEL = [
    "................",
    ".......LLLL.....",
    ".......LMMD.....",
    ".......LMMD.....",
    ".......LMMD.....",
    ".......LMMD.....",
    ".......WW.......",
    ".......WW.......",
    ".....vWW........",
    "...vvVWW........",
    "....VWW.........",
    ".....WW.........",
    "....WW..........",
    "....WW..........",
    "...cW...........",
    "...cc...........",
]

HOE = [
    "................",
    "..LLLLLLL.......",
    "..LMMMMMMWW.....",
    "...DDDDDDWW.....",
    "........WW......",
    "........WW......",
    ".......WW.......",
    ".......WW.......",
    ".....vWW........",
    "...vvVWW........",
    "....VWW.........",
    ".....WW.........",
    "....WW..........",
    "....WW..........",
    "...cW...........",
    "...cc...........",
]

TOOLS = {
    "sword": SWORD,
    "pickaxe": PICKAXE,
    "axe": AXE,
    "shovel": SHOVEL,
    "hoe": HOE,
}
