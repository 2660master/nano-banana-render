# -*- coding: utf-8 -*-
"""Maakt een overzichtsplaat van alle gebouwde texturen (voor review)."""
import os
from PIL import Image, ImageDraw, ImageFont

import build as B
import palette
import item_groups
import sprites_tools

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG = (24, 30, 26)
FG = (226, 234, 222)
DIM = (140, 156, 140)
ACC = (140, 197, 94)

SCALE = 5                     # 16px -> 80px
CELL = 16 * SCALE
PAD = 14
LABEL_H = 16


def load(name):
    return Image.open(os.path.join(B.ITEM_DIR, name + ".png")).convert("RGBA")


def grid(draw, canvas, x0, y0, names, cols, fs):
    for i, name in enumerate(names):
        cx = x0 + (i % cols) * (CELL + PAD)
        cy = y0 + (i // cols) * (CELL + PAD + LABEL_H)
        draw.rounded_rectangle([cx - 4, cy - 4, cx + CELL + 3, cy + CELL + 3],
                               radius=6, fill=(34, 42, 35))
        canvas.alpha_composite(load(name).resize((CELL, CELL), Image.NEAREST), (cx, cy))
        label = name.replace("_", " ")
        w = draw.textlength(label, font=fs)
        draw.text((cx + CELL / 2 - w / 2, cy + CELL + 6), label, font=fs, fill=DIM)
    rows = (len(names) + cols - 1) // cols
    return y0 + rows * (CELL + PAD + LABEL_H)


def main():
    f_title = ImageFont.truetype(FONT_B, 34)
    f_head = ImageFont.truetype(FONT_B, 20)
    f_small = ImageFont.truetype(FONT, 13)
    f_tier = ImageFont.truetype(FONT_B, 14)

    tools = list(sprites_tools.TOOLS.keys())
    items = [n for _t, _b, names in item_groups.groups() for n in names]

    cols_i = 8
    tool_h = len(palette.TIER_ORDER) * (CELL + PAD + LABEL_H)
    item_h = ((len(items) + cols_i - 1) // cols_i) * (CELL + PAD + LABEL_H)
    W = 40 + 120 + len(tools) * (CELL + PAD)
    W = max(W, 40 + cols_i * (CELL + PAD))
    H = 168 + tool_h + 90 + item_h + 60

    canvas = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(canvas)

    d.text((36, 34), "NTCL — natuur-texturepack", font=f_title, fill=FG)
    d.text((38, 78), "Deel 1: items & gereedschap  ·  Minecraft 1.21.11  ·  16×16 (vanilla resolutie, 0 FPS-kosten)",
           font=f_small, fill=ACC)

    y = 122
    d.text((36, y), "Gereedschap & wapens", font=f_head, fill=FG)
    y += 50
    x0 = 36 + 120
    for i, t in enumerate(tools):
        d.text((x0 + i * (CELL + PAD) + 6, y - 18), t, font=f_tier, fill=DIM)
    for r, mat in enumerate(palette.TIER_ORDER):
        cy = y + r * (CELL + PAD + LABEL_H)
        d.text((36, cy + CELL / 2 - 16), mat, font=f_tier, fill=FG)
        d.text((36, cy + CELL / 2 + 2), palette.MATERIALS[mat]["label"], font=f_small, fill=ACC)
        for c, t in enumerate(tools):
            cx = x0 + c * (CELL + PAD)
            d.rounded_rectangle([cx - 4, cy - 4, cx + CELL + 3, cy + CELL + 3],
                                radius=6, fill=(34, 42, 35))
            canvas.alpha_composite(load(f"{mat}_{t}").resize((CELL, CELL), Image.NEAREST), (cx, cy))

    y += tool_h + 40
    d.text((36, y), "Items", font=f_head, fill=FG)
    y += 34
    grid(d, canvas, 36, y, items, cols_i, f_small)

    d.text((36, canvas.size[1] - 34),
           "Nog niet in deel 1: blokken, mobs, lucht en geluiden — die komen na jouw akkoord op deze stijl.",
           font=f_small, fill=DIM)

    out = os.path.join(B.DIST, "ntcl-items-preview.png")
    canvas.convert("RGB").save(out, quality=95)
    print("preview ->", out, canvas.size)


if __name__ == "__main__":
    main()
