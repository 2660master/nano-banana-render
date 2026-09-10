# -*- coding: utf-8 -*-
"""Dier-texturen.

Anders dan blokken en items zijn dit uitgevouwen modellen: elk kubusje van
het model pakt een vast rechthoekje uit het vel. Die indeling zit in de
modelcode van het spel, niet in de texture zelf. Ik kon de vanilla-bestanden
hier niet ophalen (Mojang's servers zijn geblokkeerd), dus de gezichten zijn
berekend met de standaard doos-uitvouwing:

    voorkant : (u+d,     v+d)  breedte w, hoogte h
    achterkant:(u+d+w+d, v+d)
    links    : (u,       v+d)  breedte d
    rechts   : (u+d+w,   v+d)  breedte d
    boven    : (u+d,     v)    hoogte d
    onder    : (u+d+w,   v)

De rest van het vel wordt volledig met vacht gevuld. Dat is bewust: valt de
uitvouwing een paar pixels anders uit, dan zie je dat aan een egale vacht
nauwelijks. Alleen de gezichten moeten kloppen — die check je in het spel.
"""
from PIL import Image

from blocks import mix, mul, noise
from palette import hx


def box_uv(u, v, w, h, d):
    return {
        "front":  (u + d, v + d, w, h),
        "back":   (u + d + w + d, v + d, w, h),
        "left":   (u, v + d, d, h),
        "right":  (u + d + w, v + d, d, h),
        "top":    (u + d, v, w, d),
        "bottom": (u + d + w, v, w, d),
    }


def hide(w, h, base, seed, patch=None, patch_amount=0.0, fur=0.20, patch_scale=5):
    """Vult het hele vel met vacht: fijne korrel plus grovere plukken."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            fine = noise(x, y, seed)
            coarse = noise(x // 3, y // 3, seed + 17)
            v = 0.45 * fine + 0.55 * coarse
            c = mul(base, 1.0 - fur / 2 + v * fur)
            if patch is not None:
                ps = patch_scale
                blob = (0.75 * noise(x // ps, y // ps, seed + 41)
                        + 0.25 * noise(x // 2, y // 2, seed + 43))
                if blob < patch_amount:
                    c = mul(patch, 0.94 + noise(x, y, seed + 51) * 0.14)
            px[x, y] = c
    return im


def fill(im, rect, col):
    x0, y0, w, h = rect
    px = im.load()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if 0 <= x < im.width and 0 <= y < im.height:
                px[x, y] = col


def dot(im, x, y, col):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.load()[x, y] = col


def face(im, rect, eye=hx("1E1A18"), eye_white=None, muzzle=None,
         eye_row=0.35, eye_inset=1, muzzle_rows=0.45):
    """Tekent ogen en snuit in het voorvlak van de kop."""
    x0, y0, w, h = rect
    ey = y0 + max(1, int(h * eye_row))
    for ex in (x0 + eye_inset, x0 + w - 1 - eye_inset):
        if eye_white:
            dot(im, ex, ey, eye_white)
            dot(im, ex, ey + 1, eye)
        else:
            dot(im, ex, ey, eye)
            dot(im, ex, ey + 1, eye)
    if muzzle:
        my = y0 + int(h * muzzle_rows) + 1
        mh = max(1, h - (my - y0) - 1)
        fill(im, (x0 + 2, my, max(1, w - 4), mh), muzzle)
        for nx in (x0 + 2, x0 + w - 3):
            dot(im, nx, my + max(0, mh // 2), mul(muzzle, 0.55))



def veined(w, h, base, vein, seed, density=0.16):
    """Bladachtig vel: vacht als basis, met nerven die er doorheen lopen."""
    im = hide(w, h, base, seed, fur=0.16)
    px = im.load()
    for y in range(h):
        for x in range(w):
            # schuine nerven, met wat ruis zodat ze niet kaarsrecht lopen
            t = (x * 0.6 + y * 1.0 + noise(x // 3, y // 3, seed + 5) * 4) % 7
            if t < 1.0:
                px[x, y] = mul(vein, 0.92 + noise(x, y, seed + 9) * 0.16)
            elif noise(x, y, seed + 21) < density * 0.3:
                px[x, y] = mul(base, 1.14)
    return im


# Kop-dozen uit de standaardmodellen: (u, v, breedte, hoogte, diepte)
HEADS = {
    "cow":     (0, 0, 8, 8, 6),
    "pig":     (0, 0, 8, 8, 8),
    "sheep":   (0, 0, 6, 6, 8),
    "chicken": (0, 0, 4, 6, 3),
    "wolf":    (0, 0, 6, 6, 4),
}


def build():
    """pad in het pack (zonder .png) -> afbeelding."""
    out = {}

    # -- koe: donkere huid met roomkleurige vlekken --------------------------
    cow = hide(64, 64, hx("4A3524"), 900, hx("E4DCC8"), 0.40, patch_scale=9)
    face(cow, box_uv(*HEADS["cow"])["front"], muzzle=hx("E8D8C0"), eye_row=0.28)
    out["entity/cow/cow"] = cow

    red = hide(64, 64, hx("9E2A22"), 901, hx("C4443A"), 0.22)
    face(red, box_uv(*HEADS["cow"])["front"], muzzle=hx("D8C0B0"), eye_row=0.28)
    out["entity/cow/red_mooshroom"] = red

    brown = hide(64, 64, hx("6E4A2E"), 902, hx("8E6238"), 0.26, patch_scale=8)
    face(brown, box_uv(*HEADS["cow"])["front"], muzzle=hx("D8C8B4"), eye_row=0.28)
    out["entity/cow/brown_mooshroom"] = brown

    # -- varken ---------------------------------------------------------------
    pig = hide(64, 64, hx("E09A96"), 903, hx("EEB6B0"), 0.20)
    face(pig, box_uv(*HEADS["pig"])["front"], muzzle=hx("D0736E"), eye_row=0.30)
    out["entity/pig/pig"] = pig

    # -- schaap: het vel eronder, plus de vacht die het spel inkleurt ---------
    sheep = hide(64, 64, hx("D8CFBC"), 904, hx("BCB2A0"), 0.18)
    face(sheep, box_uv(*HEADS["sheep"])["front"], muzzle=hx("C8BCA8"), eye_row=0.30)
    out["entity/sheep/sheep"] = sheep
    # bijna wit: het spel vermenigvuldigt dit met de verfkleur van het schaap
    out["entity/sheep/sheep_wool"] = hide(64, 64, hx("F2EFE6"), 905, hx("E2DED2"), 0.30, fur=0.14)

    # -- kip ------------------------------------------------------------------
    chicken = hide(64, 32, hx("EFEBDD"), 906, hx("D8D2C0"), 0.22, fur=0.16)
    f = box_uv(*HEADS["chicken"])["front"]
    face(chicken, f, eye_row=0.30, eye_inset=0)
    fill(chicken, (14 + 2, 0 + 2, 4, 2), hx("E8A83A"))       # snavel
    fill(chicken, (14 + 2, 4 + 2, 2, 2), hx("C4362E"))       # lel
    out["entity/chicken"] = chicken

    # -- wolf -----------------------------------------------------------------
    for name, coat, eye_col in (("wolf", "A8A49A", "C9A24A"),
                                ("wolf_tame", "C4BEB0", "6E9CC4"),
                                ("wolf_angry", "9A9086", "C4362E")):
        w = hide(64, 32, hx(coat), 907, hx("6E6A62"), 0.18, fur=0.22)
        face(w, box_uv(*HEADS["wolf"])["front"], eye=hx(eye_col),
             muzzle=hx("E4E0D6"), eye_row=0.28)
        out[f"entity/wolf/{name}"] = w

    # -- elytra: bladvleugels met nerven --------------------------------------
    out["entity/elytra"] = veined(64, 32, hx("5E8A4A"), hx("36542C"), 910)

    # -- drietand en schild ---------------------------------------------------
    out["entity/trident"] = veined(32, 32, hx("BCC8C0"), hx("7E8A84"), 911, density=0.10)
    shield = hide(64, 64, hx("7A5A38"), 912, hx("5A4128"), 0.30, patch_scale=7)
    fill(shield, (0, 0, 12, 22), hx("6B4F2C"))          # greep
    fill(shield, (26, 22, 12, 12), hx("CBD2CA"))        # metalen knop
    fill(shield, (28, 24, 8, 8), hx("9CA69D"))
    out["entity/shield_base"] = shield
    out["entity/shield_base_nopattern"] = shield.copy()

    # -- end crystal en enderkist --------------------------------------------
    out["entity/end_crystal/end_crystal"] = veined(64, 32, hx("93E9DD"), hx("2F8981"), 913, density=0.08)
    out["entity/end_crystal/end_crystal_beam"] = veined(16, 16, hx("D8FFF6"), hx("7FCFC4"), 914)
    ender = hide(64, 64, hx("2A3A34"), 915, hx("1A2620"), 0.30, patch_scale=6)
    fill(ender, (0, 0, 14, 14), hx("4E8A6A"))           # slot
    out["entity/chest/ender"] = ender

    return out
