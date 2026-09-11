# -*- coding: utf-8 -*-
"""Bouwt het grijze CPvP-pack uit de keuzes in grey_choices.py.

Alles blijft op vanilla-resolutie (16x16 blokken en items), op twee
uitzonderingen na die geen geometrie zijn en dus niets aan frametijd
kosten: de zon en de maan. clouds.png is het enige vel dat wel kost —
Minecraft bouwt uit elke pixel met alpha een wolkendoos — en dat blijft
op 256x256 met 40% dekking.

Draai:  python3 build_grey.py
"""
import json
import os
import shutil
import zipfile

from PIL import Image

import anchor_grey
import blocks as B
import crystal_grey
import extra_grey as EX
import grey
import ground_real as GR
import items_grey
import render as R
import sky_grey as SG
import sprites_grey as S
import stone_real as ST
import wood_real as W
from palette import hx

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACK = os.path.join(ROOT, "CPVP")
TEX = os.path.join(PACK, "assets", "minecraft", "textures")
ITEM = os.path.join(TEX, "item")
BLOCK = os.path.join(TEX, "block")
ENV = os.path.join(TEX, "environment")
ENTITY = os.path.join(TEX, "entity")
DIST = os.path.join(ROOT, "dist")

PACK_FORMAT, MIN_FORMAT, MAX_FORMAT = 75, 64, 75

# Wat hier niet in zit, pakt Minecraft uit zijn eigen bestanden. Dat is
# geen omissie maar de afspraak: deze wilde de gebruiker vanilla houden.
VANILLA = {
    "mace", "totem_of_undying", "ender_pearl",
    "netherite_helmet", "netherite_chestplate",
    "netherite_leggings", "netherite_boots",
}


def description(n):
    """De twee regels naast de packnaam. §-codes zijn kleuren."""
    return ("§7§lN§f§lT§7§lC§f§lL §r§fCPvP grijs\n"
            f"§8{n} texturen · §f16x §8· 1.21.11")


# ------------------------------------------------------------------ paletten
NETH = dict(grey.NETHERITE)
LICHT = dict(grey.GREY)
PEES = {"v": hx("FFFFFF")}
BLAD = {"v": hx("C8D0D6")}


def item(rows, pal, name, glow=None):
    im = R.render(rows, pal, name)
    if glow:
        im = grey.sheen(im, top=glow[0], bottom=glow[1])
    return im


def blok(im):
    """Reliëf uit de eigen helderheid, zoals in alle previews."""
    return B.emboss(im)


# ------------------------------------------------------------------- items
def items():
    out = {}
    tool = dict(NETH)
    out["netherite_sword"] = item(S.SWORD, tool, "sword", (1.55, 0.45))
    out["netherite_pickaxe"] = item(S.PICKAXE, tool, "pickaxe", (1.55, 0.45))
    out["netherite_axe"] = item(S.AXE, tool, "axe", (1.55, 0.45))
    out["trident"] = item(S.TRIDENT, tool, "trident")

    bow = dict(tool)
    bow.update(PEES)
    out["bow"] = item(S.BOW, bow, "bow")
    for i, pull in enumerate((1.6, 3.2, 4.6)):
        out["bow_pulling_%d" % i] = item(S.bow_rows(pull), bow, "bow")

    cb = dict(tool)
    cb.update(PEES)
    out["crossbow_standby"] = item(S.CROSSBOW, cb, "crossbow", (1.55, 0.45))
    for i, pull in enumerate((1.0, 2.0, 3.0)):
        out["crossbow_pulling_%d" % i] = item(
            S.crossbow_rows(pull), cb, "crossbow", (1.55, 0.45))

    out["crossbow_arrow"] = item(S.crossbow_rows(3.0, arrow="pijl"), cb,
                                "crossbow", (1.55, 0.45))
    out["crossbow_firework"] = item(S.crossbow_rows(3.0, arrow="vuurwerk"), cb,
                                   "crossbow", (1.55, 0.45))

    appel = dict(NETH)
    appel.update(BLAD)
    out["potion"] = EX.potion()
    out["splash_potion"] = EX.potion(kurk="4A5157")
    out["lingering_potion"] = EX.potion(kurk="9AA2A8")
    out["potion_overlay"] = EX.potion_overlay()

    out["golden_apple"] = item(S.APPLE, appel, "apple")
    out["enchanted_golden_apple"] = grey.sheen(
        item(S.APPLE, appel, "apple"), top=1.45, bottom=0.70)
    return out


# ------------------------------------------------------------------ blokken
LOOF = ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak",
        "mangrove", "cherry", "azalea", "flowering_azalea")

# bast, kern: elk houtsoort zijn eigen tint, zelfde tekening
HOUT = {
    "oak": ("6E5134", "B08E5C"),
    "spruce": ("4A3722", "8A6942"),
    "birch": ("C8C0AC", "DCCFA8"),
    "jungle": ("6A4C35", "B08054"),
    "acacia": ("6A5340", "B8703C"),
    "dark_oak": ("3C2C1C", "5E4228"),
    "mangrove": ("5A2E2A", "8A3E38"),
    "cherry": ("3C2C30", "E0B8B4"),
}


def blokken():
    out = {}

    steen = ST.layered("989EA4", 13, cells=6, pebble=0.26, blotch=0.07,
                       grain=0.07)
    out["stone"] = blok(steen)
    out["smooth_stone"] = blok(ST.layered("9EA4AA", 13, cells=9, pebble=0.10,
                                          blotch=0.04, grain=0.05))
    out["andesite"] = blok(ST.layered("8E9294", 41, cells=6, pebble=0.28,
                                      blotch=0.08, grain=0.08))
    out["diorite"] = blok(ST.layered("D2D4D6", 42, cells=5, pebble=0.34,
                                     blotch=0.10, grain=0.10))
    out["granite"] = blok(ST.layered("A8968E", 43, cells=5, pebble=0.30,
                                     blotch=0.10, grain=0.09))

    keien = ST.cobble("8C9096", 62, cells=4, spread=0.26, grain=0.09)
    out["cobblestone"] = blok(keien)
    out["gravel"] = blok(ST.cobble("878B90", 101, cells=6, spread=0.30,
                                   grain=0.12, gap=0.66))

    diep = ST.layered("343940", 23, cells=7, pebble=0.34, blotch=0.07,
                      grain=0.10)
    out["deepslate"] = blok(diep)
    out["deepslate_top"] = blok(diep)
    out["cobbled_deepslate"] = blok(ST.cobble("3A3F46", 24, cells=4,
                                              spread=0.26, grain=0.09))

    aarde = ST.layered("5E452E", 32, cells=5, pebble=0.50, blotch=0.12,
                       grain=0.18)
    out["dirt"] = blok(aarde)
    out["coarse_dirt"] = blok(ST.layered("56402A", 33, cells=4, pebble=0.56,
                                         blotch=0.14, grain=0.20))
    out["rooted_dirt"] = blok(ST.layered("664E36", 34, cells=5, pebble=0.48,
                                         blotch=0.12, grain=0.17))

    # gras is grijs getekend; het spel legt er de biome-kleur op
    mat = GR.blades(44, spread=0.40, fine=0.18, length=3)
    out["grass_block_top"] = blok(mat)
    rand = GR.overlay(44, spread=0.40, depth=7)
    out["grass_block_side_overlay"] = rand
    zij = blok(aarde).copy()
    zij.alpha_composite(rand)
    out["grass_block_side"] = zij

    blad = GR.leaves(92, spread=0.30, holes=0.26, clump=4)
    for soort in LOOF:
        out[soort + "_leaves"] = blad

    for soort, (bast, kern) in HOUT.items():
        out[soort + "_log"] = blok(W.bark(bast, 51))
        out[soort + "_log_top"] = blok(W.log_top(kern, 51))
        out[soort + "_planks"] = blok(W.planks(kern, 51))
        out["stripped_" + soort + "_log"] = blok(W.bark(kern, 52, groove=0.22))
        out["stripped_" + soort + "_log_top"] = blok(W.log_top(kern, 51))

    out["sand"] = blok(ST.layered("DBCB9A", 101, cells=8, pebble=0.16,
                                  blotch=0.05, grain=0.12))
    out["red_sand"] = blok(ST.layered("BE7434", 102, cells=8, pebble=0.16,
                                      blotch=0.05, grain=0.12))
    out["netherrack"] = blok(ST.layered("7A3A38", 111, cells=5, pebble=0.42,
                                        blotch=0.14, grain=0.16))

    obs = ST.layered("15171A", 71, cells=7, pebble=0.26, blotch=0.06,
                     grain=0.06)
    out["obsidian"] = blok(obs)
    out["crying_obsidian"] = blok(ST.facets("15171A", 72, cells=4, edge=1.55,
                                            sparkle=0.05))

    eind = ST.layered("DCD8A8", 84, cells=6, pebble=0.24, blotch=0.06,
                      grain=0.07)
    out["end_stone"] = blok(eind)

    # respawn anchor: wit blok, ronde gloed, bovenkant met vijf ringen
    for lading in range(5):
        out["respawn_anchor_side%d" % lading] = anchor_grey.side(
            lading, glow="FFFFFF")
    out["respawn_anchor_top"] = anchor_grey.top(rings=5)
    out["respawn_anchor_top_off"] = anchor_grey.top(
        rings=5, inner="C4CACE", outer="8A9298")
    out["respawn_anchor_bottom"] = anchor_grey.bottom()
    return out


def schrijf(mapnaam, spullen):
    os.makedirs(mapnaam, exist_ok=True)
    for naam, im in spullen.items():
        if naam in VANILLA:
            continue
        im.save(os.path.join(mapnaam, naam + ".png"))
    return [n for n in spullen if n not in VANILLA]


def build():
    if os.path.isdir(PACK):
        shutil.rmtree(PACK)
    for d in (ITEM, BLOCK, ENV, os.path.join(ENTITY, "end_crystal")):
        os.makedirs(d, exist_ok=True)

    namen = []
    namen += schrijf(ITEM, items())
    namen += schrijf(BLOCK, blokken())

    # lucht
    SG.sun(64, disc=0.54, corona=0.98, core="FFFBEC",
           rim="FFD48A").save(os.path.join(ENV, "sun.png"))
    SG.moon_phases(64, base="E2E8EE", sea="A8B2BC",
                   craters=30).save(os.path.join(ENV, "moon_phases.png"))
    SG.clouds(256, coverage=0.40, lump=6, wisp=0.55, wind=3.0,
              seed=10).save(os.path.join(ENV, "clouds.png"))
    planeten = (
        (58, 62, 13, "D8DEE6", "3A4250", None),
        (176, 44, 8, "BFC8D4", "2E3644", None),
        (200, 172, 17, "E4E9EF", "434C5A", "AAB4C2"),
        (92, 200, 10, "C8D0DA", "333B48", None),
        (140, 118, 6, "E8EEF4", "4A5260", None),
    )
    SG.end_sky(256, seed=6, stars=280, nebula=0.55,
               planets=planeten).save(os.path.join(ENV, "end_sky.png"))
    namen += ["sun", "moon_phases", "clouds", "end_sky"]

    # entity-vellen: dekkend getekend omdat de UV-indeling hier onbekend is
    EX.shield().save(os.path.join(ENTITY, "shield_base_nopattern.png"))
    EX.shield().save(os.path.join(ENTITY, "shield_base.png"))
    EX.elytra().save(os.path.join(ENTITY, "elytra.png"))
    os.makedirs(os.path.join(ENTITY, "chest"), exist_ok=True)
    EX.ender_chest().save(os.path.join(ENTITY, "chest", "ender.png"))
    namen += ["shield_base", "shield_base_nopattern", "elytra", "ender_chest"]

    # end crystal: alleen de buitenste lagen, het midden is doorzichtig
    crystal_grey.cage(thickness=1).save(
        os.path.join(ENTITY, "end_crystal", "end_crystal.png"))
    namen.append("end_crystal")

    meta = {
        "pack": {
            "pack_format": PACK_FORMAT,
            "supported_formats": {"min_inclusive": MIN_FORMAT,
                                  "max_inclusive": MAX_FORMAT},
            "description": description(len(namen)),
        }
    }
    with open(os.path.join(PACK, "pack.mcmeta"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")
    icon().save(os.path.join(PACK, "pack.png"))

    os.makedirs(DIST, exist_ok=True)
    zip_pad = os.path.join(DIST, "NTCL-CPvP.zip")
    if os.path.exists(zip_pad):
        os.remove(zip_pad)
    with zipfile.ZipFile(zip_pad, "w", zipfile.ZIP_DEFLATED) as z:
        for wortel, _, bestanden in os.walk(PACK):
            for b in bestanden:
                vol = os.path.join(wortel, b)
                z.write(vol, os.path.relpath(vol, PACK))
    return namen, zip_pad


def icon(size=128):
    """Packicoon: het zwaard met de gloed, op donkergrijs."""
    im = Image.new("RGBA", (size, size), hx("24282C"))
    zwaard = item(S.SWORD, dict(NETH), "sword", (1.55, 0.45))
    groot = zwaard.resize((size, size), Image.NEAREST)
    im.alpha_composite(groot)
    return im


if __name__ == "__main__":
    n, z = build()
    print("%d texturen" % len(n))
    print(z)
