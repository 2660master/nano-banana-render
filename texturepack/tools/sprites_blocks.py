# -*- coding: utf-8 -*-
"""Catalogus van blok-texturen: naam -> functie die een 16x16 PNG maakt.

Deel 2a: bouwblokken. Elk materiaal is naar een natuurpalet getrokken —
zachter, warmer en met mos of korstmos waar dat logisch is.
"""
from PIL import Image

import blocks as G
from palette import hx

# ------------------------------------------------------------------ houtsoorten
# (naam, plankkleur, bastkleur)
WOODS = [
    ("oak",       "B08A52", "6B5334"),
    ("spruce",    "7A5533", "3E2B18"),
    ("birch",     "D6C68C", "C6C3B4"),
    ("jungle",    "A9755A", "5A4429"),
    ("acacia",    "B4643A", "6A5236"),
    ("dark_oak",  "56391F", "3A2A18"),
    ("mangrove",  "8A4A3E", "5A3B33"),
    ("cherry",    "D8A0A4", "4E3238"),
    ("pale_oak",  "DFD5C2", "8A8377"),
]
STEMS = [("crimson", "7B3A55", "6A2E42"), ("warped", "2E6B62", "2A4F55")]

# ------------------------------------------------------------------ verfkleuren
# Plantaardig geverfd: zachter en grijzer dan vanilla-dyes.
DYES = [
    ("white",      "E9E7DC"), ("orange",     "D2782F"),
    ("magenta",    "B25C9C"), ("light_blue", "6FA4CA"),
    ("yellow",     "D6B944"), ("lime",       "8CBF43"),
    ("pink",       "D993A4"), ("gray",       "474B47"),
    ("light_gray", "9AA096"), ("cyan",       "3E8A8E"),
    ("purple",     "764A98"), ("blue",       "3C4E96"),
    ("brown",      "7A5433"), ("green",      "5B7A2E"),
    ("red",        "A63A32"), ("black",      "232320"),
]

CLAY_BASE = hx("96674B")


def _mixhex(a, b, t):
    return G.mix(hx(a), b, t)


def catalog():
    """Bouwt de volledige lijst (naam, maakfunctie) op."""
    out = {}

    def add(name, fn):
        out[name] = fn

    # -- planken, stammen en ontschorste stammen ------------------------------
    for i, (w, plank, bark) in enumerate(WOODS + STEMS):
        p, b = hx(plank), hx(bark)
        add(f"{w}_planks", lambda p=p, i=i: G.planks(p, 100 + i))
        suffix = "stem" if w in ("crimson", "warped") else "log"
        add(f"{w}_{suffix}", lambda b=b, i=i, w=w: G.log_side(b, 200 + i, dashes=(w == "birch")))
        add(f"{w}_{suffix}_top", lambda b=b, p=p, i=i: G.log_top(b, p, 300 + i))
        add(f"stripped_{w}_{suffix}",
            lambda p=p, i=i: G.log_side(G.mul(p, 0.94), 400 + i))
        add(f"stripped_{w}_{suffix}_top",
            lambda p=p, i=i: G.log_top(G.mul(p, 0.86), p, 500 + i))

    # -- bamboe: verticale latten in plaats van liggende planken -------------
    bam, bam_bark = hx("C5A24E"), hx("8C9A4A")
    add("bamboo_planks",
        lambda: G.planks(bam, 150).transpose(Image.ROTATE_90))
    add("bamboo_mosaic",
        lambda: G.bricks(bam, G.mul(bam, 0.68), 151, bw=8, bh=4).transpose(Image.ROTATE_90))
    add("bamboo_block", lambda: G.log_side(bam_bark, 152).transpose(Image.ROTATE_90)
        .transpose(Image.ROTATE_270))
    add("bamboo_block_top", lambda: G.log_top(bam_bark, bam, 153))
    add("stripped_bamboo_block", lambda: G.log_side(G.mul(bam, 0.92), 154))
    add("stripped_bamboo_block_top", lambda: G.log_top(G.mul(bam, 0.80), bam, 155))

    # -- steenfamilie ---------------------------------------------------------
    add("stone",            lambda: G.stone(hx("7C8078"), 11, contrast=0.34))
    add("smooth_stone",     lambda: G.smooth(hx("9A9E96"), 12, grain=0.05))
    add("cobblestone",      lambda: G.cobble(hx("7A7E76"), 13))
    add("mossy_cobblestone",
        lambda: G.moss_over(G.cobble(hx("74786F"), 13), 14, amount=0.30))
    add("stone_bricks",     lambda: G.bricks(hx("7C8078"), hx("5A5E56"), 15))
    add("mossy_stone_bricks",
        lambda: G.moss_over(G.bricks(hx("767A72"), hx("545850"), 15), 16, amount=0.30))
    add("cracked_stone_bricks",
        lambda: G.crack(G.bricks(hx("787C74"), hx("585C54"), 15), 17))
    add("chiseled_stone_bricks", lambda: G.chiseled(hx("7C8078"), 18))
    add("andesite",         lambda: G.stone(hx("86887F"), 19, specks=0.08, speck_f=0.80))
    add("polished_andesite", lambda: G.smooth(hx("8E9089"), 20))
    add("diorite",          lambda: G.stone(hx("C6C6C0"), 21, contrast=0.20, specks=0.12, speck_f=0.70))
    add("polished_diorite", lambda: G.smooth(hx("CACAC4"), 22))
    add("granite",          lambda: G.stone(hx("9A6A54"), 23, specks=0.10, speck_f=0.66))
    add("polished_granite", lambda: G.smooth(hx("A07058"), 24))
    add("deepslate",        lambda: G.log_side(hx("50505A"), 25))
    add("cobbled_deepslate", lambda: G.cobble(hx("4E4E56"), 26))
    add("polished_deepslate", lambda: G.smooth(hx("52525C"), 27))
    add("deepslate_bricks", lambda: G.bricks(hx("4E4E58"), hx("38383F"), 28))
    add("cracked_deepslate_bricks",
        lambda: G.crack(G.bricks(hx("4A4A54"), hx("34343B"), 28), 29))
    add("deepslate_tiles",  lambda: G.bricks(hx("46464F"), hx("303036"), 30, bw=8, bh=8, offset=False))
    add("cracked_deepslate_tiles",
        lambda: G.crack(G.bricks(hx("44444D"), hx("2E2E34"), 30, bw=8, bh=8, offset=False), 31))
    add("calcite",          lambda: G.stone(hx("DCDCD2"), 32, contrast=0.13))
    add("tuff",             lambda: G.stone(hx("6E6E64"), 33))
    add("polished_tuff",    lambda: G.smooth(hx("74746A"), 34))
    add("tuff_bricks",      lambda: G.bricks(hx("6E6E64"), hx("505046"), 35))
    add("blackstone",       lambda: G.stone(hx("2E282E"), 36, contrast=0.30))
    add("polished_blackstone", lambda: G.smooth(hx("322C32"), 37))
    add("polished_blackstone_bricks",
        lambda: G.bricks(hx("322C32"), hx("201C20"), 38))
    add("cracked_polished_blackstone_bricks",
        lambda: G.crack(G.bricks(hx("302A30"), hx("1E1A1E"), 38), 39))

    # -- gebakken en gestapeld ------------------------------------------------
    add("bricks",           lambda: G.bricks(hx("9E5A48"), hx("9C9088"), 40))
    add("mud_bricks",       lambda: G.bricks(hx("8A6E54"), hx("6E563F"), 41, bw=8, bh=4))
    add("nether_bricks",    lambda: G.bricks(hx("32202A"), hx("1E1218"), 42, bw=8, bh=4))
    add("red_nether_bricks", lambda: G.bricks(hx("4A1014"), hx("2A080B"), 43, bw=8, bh=4))
    add("end_stone_bricks", lambda: G.bricks(hx("D6D8A0"), hx("B0B27C"), 44))
    add("prismarine_bricks", lambda: G.bricks(hx("64A896"), hx("4C8878"), 45, bw=8, bh=8, offset=False))
    add("quartz_block_side", lambda: G.smooth(hx("E4DED4"), 46, grain=0.05))
    add("quartz_bricks",    lambda: G.bricks(hx("E4DED4"), hx("C4BCB0"), 47))
    add("resin_bricks",     lambda: G.bricks(hx("C4682C"), hx("9A4E1E"), 48))
    add("sandstone",        lambda: G.clay(hx("DCD0A0"), 49))
    add("sandstone_top",    lambda: G.stone(hx("E2D8AC"), 50, contrast=0.12))
    add("sandstone_bottom", lambda: G.stone(hx("D2C694"), 51, contrast=0.12))

    # -- geverfde blokken -----------------------------------------------------
    for i, (dye, col) in enumerate(DYES):
        c = hx(col)
        add(f"{dye}_wool",             lambda c=c, i=i: G.fabric(c, 600 + i))
        add(f"{dye}_concrete",         lambda c=c, i=i: G.smooth(G.mul(c, 1.05), 700 + i))
        add(f"{dye}_concrete_powder",  lambda c=c, i=i: G.powder(G.mul(c, 1.12), 800 + i))
        add(f"{dye}_terracotta",       lambda c=c, i=i: G.clay(G.mix(c, CLAY_BASE, 0.42), 900 + i))
        add(f"{dye}_stained_glass",    lambda c=c, i=i: G.glass(c, 1000 + i))
        add(f"{dye}_stained_glass_pane_top", lambda c=c: G.solid(G.mul(c, 1.15)))

    add("terracotta",   lambda: G.clay(CLAY_BASE, 950))
    add("glass",        lambda: G.glass(hx("C6DCC6"), 1100))
    add("glass_pane_top", lambda: G.solid(hx("DCE8DC")))
    add("tinted_glass", lambda: G.glass(hx("2A2430"), 1101, frame=hx("463E50"), alpha=215))

    return out
