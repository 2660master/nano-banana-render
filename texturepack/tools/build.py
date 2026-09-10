# -*- coding: utf-8 -*-
"""Bouwt het Verdant nature-texturepack.

Alles blijft 16x16 (vanilla resolutie) -> nul impact op FPS/VRAM.
Draai:  python3 build.py
"""
import json
import os
import shutil
import zipfile
from PIL import Image

import palette
import render
import sky
import sprites_blocks
import sprites_items
import sprites_tools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACK = os.path.join(ROOT, "Verdant")
ITEM_DIR = os.path.join(PACK, "assets", "minecraft", "textures", "item")
BLOCK_DIR = os.path.join(PACK, "assets", "minecraft", "textures", "block")
ENV_DIR = os.path.join(PACK, "assets", "minecraft", "textures", "environment")
DIST = os.path.join(ROOT, "dist")

PACK_FORMAT = 75          # Minecraft 1.21.11
MIN_FORMAT = 64           # 1.21.7 / 1.21.8
MAX_FORMAT = 75

DESCRIPTION = "§2Verdant §r§7– natuur-texturepack\n§8Items · blokken · lucht · water  §a16x"


# --------------------------------------------------------------- boog-frames
def bow_pulling(nock_x):
    """Boog met gespannen pees + genokte pijl, procedureel getekend."""
    img = render.render(sprites_items.BOW, sprites_items.ITEMS["bow"][1], "bow")
    px = img.load()
    cord = palette.CORD["c"]
    shaft = palette.hx("A07B4E")
    head = palette.hx("6E7075")

    # oude rechte pees weghalen (kolom x=12, y=3..11)
    for y in range(3, 12):
        if px[12, y][3] and px[12, y][:3] == cord[:3]:
            px[12, y] = (0, 0, 0, 0)

    def line(x0, y0, x1, y1, col):
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(steps + 1):
            t = i / steps if steps else 0
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            if px[x, y][3] == 0:
                px[x, y] = col

    line(12, 2, nock_x, 7, cord)          # bovenste pees
    line(nock_x, 7, 12, 12, cord)         # onderste pees
    for x in range(nock_x + 1, 15):       # pijlschacht
        if px[x, 7][3] == 0:
            px[x, 7] = shaft
    px[15, 7] = head
    px[14, 7] = head
    return img


# ------------------------------------------------------------------- bouwen
def build():
    if os.path.isdir(PACK):
        shutil.rmtree(PACK)
    os.makedirs(ITEM_DIR)
    os.makedirs(BLOCK_DIR)
    os.makedirs(ENV_DIR)
    os.makedirs(DIST, exist_ok=True)

    written = []

    # 1. gereedschap: 5 vormen x 6 tiers
    for mat in palette.TIER_ORDER:
        pal = palette.material_palette(mat)
        spk = palette.material_speckle(mat)
        for tool, rows in sprites_tools.TOOLS.items():
            name = f"{mat}_{tool}"
            img = render.render(rows, pal, name, speckle=spk)
            img.save(os.path.join(ITEM_DIR, name + ".png"))
            written.append(name)

    # 2. losse items
    for name, spec in sprites_items.ITEMS.items():
        rows, pal = spec[0], spec[1]
        img = render.render(rows, pal, name)
        img.save(os.path.join(ITEM_DIR, name + ".png"))
        written.append(name)

    # 3. boog-spanframes (anders springt de boog terug naar vanilla)
    for i, nock in enumerate((10, 8, 6)):
        name = f"bow_pulling_{i}"
        bow_pulling(nock).save(os.path.join(ITEM_DIR, name + ".png"))
        written.append(name)

    # 4. bouwblokken
    blocks_written = []
    for name, make in sprites_blocks.catalog().items():
        make().save(os.path.join(BLOCK_DIR, name + ".png"))
        blocks_written.append(name)

    # 5. lucht, weer, water en lava
    env_written = build_sky()

    # 6. pack.mcmeta
    meta = {
        "pack": {
            "pack_format": PACK_FORMAT,
            "supported_formats": {"min_inclusive": MIN_FORMAT, "max_inclusive": MAX_FORMAT},
            "description": DESCRIPTION,
        }
    }
    with open(os.path.join(PACK, "pack.mcmeta"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 7. pack-icoon
    make_icon().save(os.path.join(PACK, "pack.png"))

    # 8. zip
    zip_path = os.path.join(DIST, "Verdant-1.21.11.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _dirs, files in os.walk(PACK):
            for fn in sorted(files):
                full = os.path.join(base, fn)
                z.write(full, os.path.relpath(full, PACK))

    print(f"{len(written)} item-texturen -> {os.path.relpath(ITEM_DIR, ROOT)}")
    print(f"{len(blocks_written)} blok-texturen -> {os.path.relpath(BLOCK_DIR, ROOT)}")
    print(f"{len(env_written)} lucht-, weer- en vloeistoftexturen")
    print(f"zip -> {os.path.relpath(zip_path, ROOT)}")
    return written + blocks_written + env_written


# Geanimeerde texturen: frametime is hoeveel ticks een frame blijft staan.
ANIMATED = {
    "water_still": (sky.water_still, 2),
    "water_flow": (sky.water_flow, 1),
    "lava_still": (sky.lava_still, 2),
    "lava_flow": (sky.lava_flow, 3),
}


def build_sky():
    """Schrijft lucht en weer naar environment/, water en lava naar block/."""
    done = []
    for name, make in (("sun", sky.sun), ("moon_phases", sky.moon_phases),
                       ("clouds", sky.clouds), ("end_sky", sky.end_sky),
                       ("rain", sky.rain), ("snow", sky.snow_weather)):
        make().save(os.path.join(ENV_DIR, name + ".png"))
        done.append(name)

    for name, (make, frametime) in ANIMATED.items():
        strip = make()
        strip.save(os.path.join(BLOCK_DIR, name + ".png"))
        with open(os.path.join(BLOCK_DIR, name + ".png.mcmeta"), "w", encoding="utf-8") as f:
            json.dump({"animation": {"frametime": frametime}}, f, indent=2)
            f.write("\n")
        done.append(name)

    # het vlak dat je ziet als je vanuit water tegen een blok aan kijkt
    still = sky.water_still()
    still.crop((0, 0, 16, 16)).save(os.path.join(BLOCK_DIR, "water_overlay.png"))
    done.append("water_overlay")
    return done


def make_icon(size=128):
    """Pack-icoon: bosgradient met het dauwkristal-zwaard."""
    ico = Image.new("RGBA", (size, size))
    px = ico.load()
    top, bot = (94, 154, 96), (26, 46, 32)
    for y in range(size):
        t = y / (size - 1)
        col = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(size):
            px[x, y] = col + (255,)
    pal = palette.material_palette("diamond")
    sw = render.render(sprites_tools.SWORD, pal, "icon").resize((size, size), Image.NEAREST)
    ico.alpha_composite(sw)
    return ico


if __name__ == "__main__":
    build()
