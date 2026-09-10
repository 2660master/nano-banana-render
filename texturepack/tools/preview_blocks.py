# -*- coding: utf-8 -*-
"""Overzichtsplaat van de bouwblokken, elk 2x2 getegeld zodat naden opvallen."""
import os
from PIL import Image, ImageDraw, ImageFont

import build as B
import sprites_blocks
import sprites_plants

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG, FG, DIM, ACC = (24, 30, 26), (226, 234, 222), (140, 156, 140), (140, 197, 94)
S, T, COLS = 3, 2, 12
CELL, PAD, LAB = 16 * S * T, 12, 15

ORES = ["coal", "iron", "copper", "gold", "redstone", "lapis",
        "diamond", "emerald"]
WOODS = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak",
         "mangrove", "cherry", "pale_oak", "crimson", "warped"]


def groups():
    logs = []
    for w in WOODS:
        suf = "stem" if w in ("crimson", "warped") else "log"
        logs += [f"{w}_{suf}", f"{w}_{suf}_top",
                 f"stripped_{w}_{suf}", f"stripped_{w}_{suf}_top"]
    dyes = [d for d, _ in sprites_blocks.DYES]
    return [
        ("Planken", [f"{w}_planks" for w in WOODS] + ["bamboo_planks", "bamboo_mosaic"]),
        ("Stammen & stengels", logs + ["bamboo_block", "bamboo_block_top",
                                       "stripped_bamboo_block", "stripped_bamboo_block_top"]),
        ("Steen", ["stone", "smooth_stone", "cobblestone", "mossy_cobblestone",
                   "andesite", "polished_andesite", "diorite", "polished_diorite",
                   "granite", "polished_granite", "calcite", "tuff", "polished_tuff",
                   "deepslate", "cobbled_deepslate", "polished_deepslate",
                   "blackstone", "polished_blackstone",
                   "sandstone", "sandstone_top", "sandstone_bottom", "quartz_block_side"]),
        ("Metselwerk", ["stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks",
                        "chiseled_stone_bricks", "deepslate_bricks",
                        "cracked_deepslate_bricks", "deepslate_tiles",
                        "cracked_deepslate_tiles", "tuff_bricks",
                        "polished_blackstone_bricks",
                        "cracked_polished_blackstone_bricks", "bricks", "mud_bricks",
                        "nether_bricks", "red_nether_bricks", "end_stone_bricks",
                        "prismarine_bricks", "quartz_bricks", "resin_bricks"]),
        ("Wol", [f"{d}_wool" for d in dyes]),
        ("Beton", [f"{d}_concrete" for d in dyes]),
        ("Betonpoeder", [f"{d}_concrete_powder" for d in dyes]),
        ("Terracotta", ["terracotta"] + [f"{d}_terracotta" for d in dyes]),
        ("Glas", ["glass", "tinted_glass"] + [f"{d}_stained_glass" for d in dyes]),
        ("Aarde & ondergrond", [
            "dirt", "coarse_dirt", "rooted_dirt", "grass_block_top",
            "grass_block_side", "grass_block_side_overlay", "grass_block_snow",
            "podzol_top", "podzol_side", "mycelium_top", "mycelium_side",
            "farmland", "farmland_moist", "dirt_path_top", "dirt_path_side",
            "mud", "muddy_mangrove_roots_side", "muddy_mangrove_roots_top",
            "sand", "red_sand", "gravel", "clay", "snow", "powder_snow",
            "ice", "packed_ice", "blue_ice", "netherrack", "soul_sand",
            "soul_soil", "basalt_side", "basalt_top", "magma", "end_stone",
            "moss_block", "pale_moss_block", "amethyst_block"]),
        ("Bladeren", [
            "oak_leaves", "spruce_leaves", "birch_leaves", "jungle_leaves",
            "acacia_leaves", "dark_oak_leaves", "mangrove_leaves",
            "cherry_leaves", "pale_oak_leaves", "azalea_leaves",
            "flowering_azalea_leaves"]),
        ("Ertsen", [f"{o}_ore" for o in ORES] +
                   [f"deepslate_{o}_ore" for o in ORES] +
                   ["nether_gold_ore", "nether_quartz_ore",
                    "ancient_debris_side", "ancient_debris_top"]),
        ("Planten", [n for n, _r, _p in sprites_plants.PLANTS]),
        ("Bloemen", [n for n, _r, _a, _b in sprites_plants.FLOWERS]),
        ("CPvP-blokken", [
            "obsidian", "crying_obsidian", "glowstone", "netherite_block",
            "respawn_anchor_top", "respawn_anchor_top_off", "respawn_anchor_bottom",
            "respawn_anchor_side0", "respawn_anchor_side1", "respawn_anchor_side2",
            "respawn_anchor_side3", "respawn_anchor_side4",
            "enchanting_table_top", "enchanting_table_side",
            "enchanting_table_bottom", "anvil", "anvil_top"]),
        ("Gewassen", [f"{c}_stage{i}" for c, _s, _h, n in sprites_plants.CROPS
                      for i in range(n)]),
    ]


def tiled(name, cat):
    im = cat[name]()
    t = Image.new("RGBA", (16 * T, 16 * T), (128, 128, 128, 255))
    for ty in range(T):
        for tx in range(T):
            t.alpha_composite(im, (tx * 16, ty * 16))
    return t.resize((CELL, CELL), Image.NEAREST)


def main():
    cat = sprites_blocks.catalog()
    gs = [(t, [n for n in names if n in cat]) for t, names in groups()]
    f_title = ImageFont.truetype(FONT_B, 32)
    f_head = ImageFont.truetype(FONT_B, 19)
    f_small = ImageFont.truetype(FONT, 12)
    f_tiny = ImageFont.truetype(FONT, 10)

    H = 132
    for _t, names in gs:
        H += 42 + ((len(names) + COLS - 1) // COLS) * (CELL + PAD + LAB)
    W = 36 * 2 + COLS * (CELL + PAD)

    canvas = Image.new("RGBA", (W, H + 40), BG + (255,))
    d = ImageDraw.Draw(canvas)
    d.text((36, 32), "Verdant — bouwblokken", font=f_title, fill=FG)
    d.text((38, 74), "Deel 2 · %d blok-texturen · elk blok staat 2×2 getegeld, "
                     "zodat je meteen ziet of het naadloos herhaalt"
           % sum(len(n) for _t, n in gs), font=f_small, fill=ACC)

    y = 124
    for title, names in gs:
        d.text((36, y), title, font=f_head, fill=FG)
        y += 34
        for i, n in enumerate(names):
            cx = 36 + (i % COLS) * (CELL + PAD)
            cy = y + (i // COLS) * (CELL + PAD + LAB)
            canvas.alpha_composite(tiled(n, cat), (cx, cy))
            d.text((cx, cy + CELL + 3), n[:22], font=f_tiny, fill=DIM)
        y += ((len(names) + COLS - 1) // COLS) * (CELL + PAD + LAB) + 8

    out = os.path.join(B.DIST, "verdant-blocks-preview.png")
    canvas.convert("RGB").save(out, quality=95)
    print("preview ->", out, canvas.size)


if __name__ == "__main__":
    main()
