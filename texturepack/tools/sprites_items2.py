# -*- coding: utf-8 -*-
"""De resterende items: voedsel, drank, boeken, gereedschap en losse buit.

Hergebruikt de basisvormen uit deel 1 waar dat kan (klomp, staaf, kristal)
en voegt daar zo'n twintig nieuwe vormen aan toe.
"""
from palette import hx
from sprites_items import (GEM, INGOT, LEATHER, LUMP, NUGGET, S, CARROT, BREAD,
                           APPLE, REDSTONE)

# ------------------------------------------------------------------- vormen
MEAT = S(
    "", "", "", "",
    "....111111",
    "..1111111111",
    ".111133111111",
    ".111133111112",
    ".111111311122",
    "..1111331222",
    "..1111222222",
    "...2222222",
)

FISH = S(
    "", "", "", "",
    ".11",
    ".111....1111",
    ".1111.111111111",
    ".11111111111311",
    ".11111111111111",
    ".1111.111111112",
    ".111....111222",
    ".11",
)

BOTTLE = S(
    "", "",
    "......111",
    "......131",
    "......131",
    ".....11311",
    "....1133311",
    "...113333311",
    "...113333311",
    "...113333311",
    "...113333311",
    "....1133311",
    ".....11111",
)

BOTTLE_FILL = S(
    "", "", "", "", "", "", "",
    "....11111",
    "...1111111",
    "...1111111",
    "...1111111",
    "....11111",
)

BOOK = S(
    "", "", "",
    "..3333333333",
    "..3111111113",
    "..3122222213",
    "..3111111113",
    "..3122222213",
    "..3111111113",
    "..3122222213",
    "..3111111113",
    "..3333333333",
)

PAPER = S(
    "", "", "",
    "..1111111111",
    "..1111111111",
    "..1122111111",
    "..1111111111",
    "..1111112211",
    "..1122111111",
    "..1111111111",
    "..1111111111",
    "..2222222222",
)

BOWL_FULL = S(
    "", "", "", "", "",
    "..333333333333",
    "..311111111113",
    "...3111111113",
    "...2222222222",
    "....22222222",
    ".....222222",
)

ROD = S(
    "", "",
    "..........11",
    ".........121",
    "........121",
    ".......121",
    "......121",
    ".....121",
    "....121",
    "...121",
    "..121",
    "..21",
)

BERRY = S(
    "", "", "",
    ".....3",
    "....311",
    "...11121",
    "...11211....3",
    "....111....311",
    "........1112111",
    "......11121121",
    "......112111",
    ".......111",
)

BRUSH = S(
    "", "",
    "..........333",
    ".........3333",
    "........3333",
    ".......2222",
    "......222",
    ".....11",
    "....11",
    "...11",
    "..11",
    ".11",
)

SHEARS = S(
    "", "",
    "..3.......3",
    "..33.....33",
    "...33...33",
    "....33.33",
    ".....333",
    "....11111",
    "...11.1.11",
    "..11..1..11",
    "..1...1...1",
    "..1...1...1",
)

FLINT_STEEL = S(
    "", "", "",
    "........11111",
    ".......1111111",
    ".......11...11",
    "...3...11...11",
    "..333..1111111",
    ".33333..11111",
    "..3333....1",
    "...333...11",
    "....3.....1",
)

FISHING_ROD = S(
    "", "",
    ".............1",
    "............12",
    "...........12",
    "..........12",
    ".........12.c",
    "........12..c",
    ".......12...c",
    "......12....c",
    ".....12.....c",
    "....12......c",
    "...12......333",
    "..12",
)

SPYGLASS = S(
    "", "", "",
    "...........333",
    "..........31113",
    ".........31113",
    "........31113",
    ".......22222",
    "......31113",
    ".....31113",
    "....31113",
    "...3333",
)

EGG = S(
    "", "", "",
    ".....111",
    "....11111",
    "...1111111",
    "...1111111",
    "..111111112",
    "..111111112",
    "..111111222",
    "...1112222",
    "....22222",
)

SHELL = S(
    "", "", "",
    ".....1111",
    "...11333311",
    "..1133113311",
    "..1311111331",
    "..1311111331",
    "..1133113311",
    "...11333311",
    ".....1111",
)

STAR = S(
    "", "",
    ".......1",
    ".......1",
    "......131",
    "..1...131...1",
    "...11113111",
    ".....13331",
    "...11113111",
    "..1...131...1",
    "......131",
    ".......1",
)

EYE = S(
    "", "", "",
    ".....1111",
    "...11111111",
    "..1113331111",
    "..1133233111",
    "..1133333111",
    "..1113331111",
    "...11111111",
    ".....1111",
)

MEMBRANE = S(
    "", "", "",
    "...11....11",
    "..1111..1111",
    "..1121111211",
    "...1111111",
    "...1111111",
    "....11111",
    "..1..111..1",
    "..11.....11",
)

SCUTE = S(
    "", "", "", "",
    "....111111",
    "..1122221111",
    "..1222222211",
    "..1222222211",
    "..1122221111",
    "....111111",
)

CRYSTALS = S(
    "", "",
    ".......1",
    "......131...1",
    "......131..131",
    "..1...131..131",
    ".131..131..13",
    ".131.13311.1",
    ".13..133311",
    "..1.11333311",
    "....11111111",
)

LEAD = S(
    "", "",
    "......111",
    ".....1...1",
    ".....1...1",
    "......111",
    ".......2",
    "......2",
    ".....2",
    "....2",
    "...2",
    "..22",
)

SADDLE = S(
    "", "", "",
    "...11111111",
    "..1111111111",
    ".111133331111",
    ".111133331111",
    ".111111111111",
    "..1122222211",
    "...22....22",
    "...22....22",
)

NAME_TAG = S(
    "", "", "",
    "...1111111111",
    "..111111111111",
    "..131111111111",
    "..111111111111",
    "..111111111111",
    "..222222222222",
    "...2222222222",
)

MAP_ITEM = S(
    "", "",
    "..1111111111",
    "..1333333331",
    "..1311331331",
    "..1331113331",
    "..1313311331",
    "..1331133131",
    "..1313311331",
    "..1333333331",
    "..1111111111",
)

COOKIE = S(
    "", "", "", "",
    "....111111",
    "..1113111111",
    "..1111111311",
    "..1131111111",
    "..1111113111",
    "..1113111121",
    "...11111122",
    "....222222",
)

PIE = S(
    "", "", "", "",
    "...11111111",
    "..1133333311",
    "..1333333331",
    "..1333333331",
    "..1133333311",
    "..1111111111",
    "...22222222",
)

MELON = S(
    "", "", "",
    "..1111111111",
    "..1222222221",
    "..1233333321",
    "...12333321",
    "...12333321",
    "....123321",
    ".....1221",
    "......11",
)

CHORUS = S(
    "", "",
    ".....111",
    "....11311",
    "....11111",
    ".....111",
    "...1111111",
    "..111311111",
    "..111111111",
    "...1111111",
    "....11111",
)

KELP = S(
    "", "",
    "....1111",
    "...112211",
    "...121121",
    "...112211",
    "...121121",
    "...112211",
    "...121121",
    "...112211",
    "....1111",
)

INK = S(
    "", "", "",
    ".....111",
    "...1111111",
    "..111111111",
    "..111311111",
    "..111111111",
    "...1111111",
    ".....111",
)

SMALL_NUGGET = S(
    "", "", "", "", "",
    ".....111",
    "....11111",
    "....11121",
    ".....1221",
    "......11",
)

BRICK_ITEM = S(
    "", "", "", "", "",
    "...11111111",
    "..1111111112",
    "..1111111112",
    "..2222222222",
)

FOOT = S(
    "", "", "",
    ".....11",
    "....1111",
    "....1111",
    ".....111",
    ".....111",
    "....11111",
    "...1111111",
    "...1122111",
    "....22222",
)


# ------------------------------------------------------------------ paletten
from sprites_items import P, WATER_BUCKET, BUCKET, TOTEM  # noqa: E402

DYES = [
    ("white", "E9E7DC"), ("orange", "D2782F"), ("magenta", "B25C9C"),
    ("light_blue", "6FA4CA"), ("yellow", "D6B944"), ("lime", "8CBF43"),
    ("pink", "D993A4"), ("gray", "474B47"), ("light_gray", "9AA096"),
    ("cyan", "3E8A8E"), ("purple", "764A98"), ("blue", "3C4E96"),
    ("brown", "7A5433"), ("green", "5B7A2E"), ("red", "A63A32"), ("black", "232320"),
]


def bucket_fill(a, b, hi):
    """Emmerpalet: 1/2 blijft de bast, 4/5 is wat erin zit."""
    return {**P("EFEBDD", "CFC7B2", "5B5647", a, b), "5": hx(hi)}


def items():
    out = {}

    # -- vlees en vis ---------------------------------------------------------
    meats = [
        ("beef",           "C24A44", "8C2E2A", "E8908A"),
        ("cooked_beef",    "8A5430", "5E3620", "B98A5E"),
        ("porkchop",       "E89A9A", "B96E70", "F4C4C4"),
        ("cooked_porkchop", "C98A56", "94603A", "E8B98A"),
        ("chicken",        "E8B9A0", "B98A74", "F4D9C8"),
        ("cooked_chicken", "C9945A", "94663A", "E8C08A"),
        ("mutton",         "D2645E", "9A3E3A", "EE9A94"),
        ("cooked_mutton",  "9A6238", "6E4224", "C4934E"),
        ("rabbit",         "D2706A", "9A4642", "EEA49E"),
        ("cooked_rabbit",  "A56A3A", "744824", "CE9A5E"),
    ]
    for name, a, b, c in meats:
        out[name] = (MEAT, P(a, b, c))

    fishes = [
        ("cod",            "C9BC9A", "8E8168", "E2D9BE"),
        ("cooked_cod",     "C99A56", "94703A", "E8C08A"),
        ("salmon",         "D2705E", "9A4636", "EEA492"),
        ("cooked_salmon",  "C97F4A", "946030", "E8AC7A"),
        ("tropical_fish",  "E8A03A", "B96E1E", "F4D07A"),
        ("pufferfish",     "E8C452", "B08A22", "F4E29A"),
    ]
    for name, a, b, c in fishes:
        out[name] = (FISH, P(a, b, c))

    # -- overig voedsel -------------------------------------------------------
    out["rotten_flesh"] = (MEAT, P("7A6A4A", "4E4230", "9E8E68"))
    out["spider_eye"] = (EYE, P("8A2E2E", "3A1010", "E8C43A"))
    out["fermented_spider_eye"] = (EYE, P("6E4A8A", "36204E", "9AC44E"))
    out["cookie"] = (COOKIE, P("C08A4E", "8E6030", "4E3018"))
    out["pumpkin_pie"] = (PIE, P("D8A44A", "9A6E24", "E8C87A"))
    out["melon_slice"] = (MELON, P("4E8A32", "2E5A1E", "D2483E"))
    out["glistering_melon_slice"] = (MELON, P("F2B93F", "B87E28", "FFE596"))
    out["dried_kelp"] = (KELP, P("3E5A38", "24361E"))
    out["chorus_fruit"] = (CHORUS, P("9A6EA8", "5E3A6E", "C8A4D2"))
    out["popped_chorus_fruit"] = (CHORUS, P("C8A47A", "8E6E4E", "E2C8A4"))
    out["baked_potato"] = (LUMP, P("C29A5A", "8E6A34"))
    out["poisonous_potato"] = (LUMP, P("A8B45A", "6E7A2E"))
    out["beetroot"] = (LUMP, P("A6322E", "6E1A18"))
    out["golden_carrot"] = (CARROT, P("F2B93F", "B87E28"))
    out["enchanted_golden_apple"] = (APPLE, P("F5C842", "D89A22", "A66E15", "FFFAD8"))
    out["sweet_berries"] = (BERRY, P("C4323A", "7A1A20", "5B7A2E"))
    out["glow_berries"] = (BERRY, P("E8A83A", "B07018", "5B7A2E"))
    out["bowl"] = (BOWL_FULL, P("A07B4E", "6B4F2C", "B98F5E"))
    for name, col in (("mushroom_stew", "C49A6A"), ("beetroot_soup", "A6423A"),
                      ("rabbit_stew", "B4713A"), ("suspicious_stew", "8FA85A")):
        out[name] = (BOWL_FULL, {**P("A07B4E", "6B4F2C", col)})

    # -- drank ----------------------------------------------------------------
    out["glass_bottle"] = (BOTTLE, P("C4D2C8", "8A9A90", "DCE8DE"))
    out["potion"] = (BOTTLE, P("C4D2C8", "8A9A90", "DCE8DE"))
    out["splash_potion"] = (BOTTLE, P("BCC8CE", "849098", "D4E0E4"))
    out["lingering_potion"] = (BOTTLE, P("C8C0D6", "8E88A0", "E0DCEC"))
    # grijswaarden: het spel kleurt de vloeistof met het effect mee
    out["potion_overlay"] = (BOTTLE_FILL, P("D8D8D8"))
    out["experience_bottle"] = (BOTTLE, P("A8C46A", "6E8E3A", "D2E8A4"))
    out["ominous_bottle"] = (BOTTLE, P("B4A0C8", "746088", "D8CCE4"))
    out["honey_bottle"] = (BOTTLE, P("E8A93A", "B07018", "FFD87A"))

    # -- boeken en papier -----------------------------------------------------
    out["book"] = (BOOK, P("C9A063", "8E6B3A", "8A3A2E"))
    out["writable_book"] = (BOOK, P("D2C8A4", "9A9068", "5E7A3A"))
    out["written_book"] = (BOOK, P("C8B48A", "94805A", "3E5A8A"))
    out["enchanted_book"] = (BOOK, P("D2C0E4", "9A88B0", "6E4A9A"))
    out["knowledge_book"] = (BOOK, P("C8C0A4", "948C70", "3E7A6A"))
    out["paper"] = (PAPER, P("EDEBE0", "C4C2B4"))
    out["map"] = (MAP_ITEM, P("EDE6CE", "B4A98A", "8E7A54"))
    out["filled_map"] = (MAP_ITEM, P("EDE6CE", "B4A98A", "5B7A4E"))
    out["name_tag"] = (NAME_TAG, P("D2C4A0", "9A8E6E", "8A4A32"))

    # -- gereedschap en uitrusting -------------------------------------------
    out["shears"] = (SHEARS, P("6B4F2C", "4A3720", "CBD2CA"))
    out["flint_and_steel"] = (FLINT_STEEL, P("CBD2CA", "8E968E", "4E5052"))
    out["fishing_rod"] = (FISHING_ROD, P("A07B4E", "6B4F2C", "EDEDE6"))
    out["fishing_rod_cast"] = (FISHING_ROD, P("A07B4E", "6B4F2C", "C4362E"))
    out["spyglass"] = (SPYGLASS, P("C87F52", "8E5836", "5E4A38"))
    out["brush"] = (BRUSH, P("A07B4E", "C87F52", "F0EDDF"))
    out["lead"] = (LEAD, P("C7AC7A", "8E7A50"))
    out["saddle"] = (SADDLE, P("A0603A", "6E3E22", "CBD2CA"))

    # -- emmers ---------------------------------------------------------------
    out["lava_bucket"] = (WATER_BUCKET, bucket_fill("D9701E", "F5A63A", "FFD07A"))
    out["milk_bucket"] = (WATER_BUCKET, bucket_fill("F2F2EC", "FFFFFA", "FFFFFF"))
    out["powder_snow_bucket"] = (WATER_BUCKET, bucket_fill("E4EEF4", "F6FAFC", "FFFFFF"))
    out["cod_bucket"] = (WATER_BUCKET, bucket_fill("3B7DD8", "C9BC9A", "6BA8F0"))
    out["salmon_bucket"] = (WATER_BUCKET, bucket_fill("3B7DD8", "D2705E", "6BA8F0"))
    out["pufferfish_bucket"] = (WATER_BUCKET, bucket_fill("3B7DD8", "E8C452", "6BA8F0"))
    out["tropical_fish_bucket"] = (WATER_BUCKET, bucket_fill("3B7DD8", "E8A03A", "6BA8F0"))
    out["axolotl_bucket"] = (WATER_BUCKET, bucket_fill("3B7DD8", "E8A4C4", "6BA8F0"))
    out["tadpole_bucket"] = (WATER_BUCKET, bucket_fill("3B7DD8", "4E4038", "6BA8F0"))

    # -- ruwe buit en grondstoffen -------------------------------------------
    out["raw_iron"] = (LUMP, P("C6BCA8", "8E8474"))
    out["raw_copper"] = (LUMP, P("C87F52", "8E5836"))
    out["raw_gold"] = (LUMP, P("E8B84A", "A87E22"))
    out["netherite_scrap"] = (LUMP, P("7A5A48", "4A3428"))
    out["iron_nugget"] = (SMALL_NUGGET, P("CBD2CA", "9CA69D", "F1F5EF"))
    out["gold_nugget"] = (SMALL_NUGGET, P("F2B93F", "C0842A", "FFE596"))
    out["quartz"] = (GEM, P("E4DED4", "B4AC9E", "FFFFFF"))
    out["prismarine_shard"] = (GEM, P("64A896", "3E7A68", "A4DCCC"))
    out["prismarine_crystals"] = (CRYSTALS, P("8ADCC4", "4E9A86", "D8FFF4"))
    out["echo_shard"] = (GEM, P("2E6A78", "163E4A", "6ECBD2"))
    out["heart_of_the_sea"] = (EYE, P("3E8A96", "1E4E58", "9AE4EC"))
    out["nautilus_shell"] = (SHELL, P("E4DCC4", "A89E86", "8A6A3A"))
    out["nether_star"] = (STAR, P("F0EDDF", "C8C4B4", "FFFFFF"))
    out["ender_eye"] = (EYE, P("3E8A6A", "1E4E3A", "C8F0A4"))
    out["ghast_tear"] = (EYE, P("D8E8E4", "9AB4B0", "FFFFFF"))
    out["phantom_membrane"] = (MEMBRANE, P("C8C0A4", "948C70"))
    out["rabbit_foot"] = (FOOT, P("C8A47A", "8E6E4E"))
    out["rabbit_hide"] = (LEATHER, P("C8A47A", "8E6E4E"))
    out["turtle_scute"] = (SCUTE, P("86C45E", "4E8A32"))
    out["armadillo_scute"] = (SCUTE, P("C8A46A", "8E6E3A"))
    out["ink_sac"] = (INK, P("23231E", "0E0E0C", "4A4A44"))
    out["glow_ink_sac"] = (INK, P("2E6A78", "163E4A", "8ADCC4"))
    out["cocoa_beans"] = (BERRY, P("8A4A22", "5A2E12", "5B7A2E"))
    out["blaze_rod"] = (ROD, P("E8C452", "B08A22"))
    out["brick"] = (BRICK_ITEM, P("9E5A48", "6E3A2C"))
    out["nether_brick"] = (BRICK_ITEM, P("42303A", "241820"))
    out["snowball"] = (NUGGET, P("F2F6F8", "C8D4DC"))
    out["egg"] = (EGG, P("EDE4CE", "B8AC90"))
    out["magma_cream"] = (NUGGET, P("E8922A", "8E3A14"))
    out["glowstone_dust"] = (REDSTONE, P("E8D46A", "B09A2E"))
    out["gunpowder"] = (REDSTONE, P("8A8A8A", "4E4E4E"))
    out["sugar"] = (REDSTONE, P("F2F2EC", "C4C4BC"))
    out["blaze_powder"] = (REDSTONE, P("E8A83A", "B06E14"))
    out["bone_meal"] = (REDSTONE, P("F0EDDF", "C2BCA6"))

    # -- kleurstoffen ---------------------------------------------------------
    for dye, col in DYES:
        c = hx(col)
        dark = (int(c[0] * 0.62), int(c[1] * 0.62), int(c[2] * 0.62), 255)
        out[f"{dye}_dye"] = (REDSTONE, {"1": c, "2": dark})

    # -- zaden ----------------------------------------------------------------
    for name, a, b in (("melon_seeds", "D8D2A8", "A29A70"),
                       ("pumpkin_seeds", "E4DCB4", "AEA47C"),
                       ("beetroot_seeds", "C8A88A", "8E7058"),
                       ("torchflower_seeds", "C8B48A", "8E7A54"),
                       ("pitcher_pod", "8A6AA8", "543A6E")):
        out[name] = (REDSTONE, P(a, b))

    return out


ITEMS2 = items()
