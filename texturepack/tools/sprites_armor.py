# -*- coding: utf-8 -*-
"""Harnasstukken: vier silhouetten, zeven materialen.

Leer krijgt daarnaast een overlay-texture. Minecraft kleurt die met de
verfkleur van het stuk, dus die staat in grijstinten — net als bij bladeren
en gras.
"""
from sprites_items import S
from palette import hx

HELM = S(
    "", "", "",
    "....11111111",
    "...1111111111",
    "..111111111111",
    "..111111111111",
    "..113333333311",
    "..113333333311",
    "..112222222211",
    "..11........11",
    "..22........22",
)

CHEST = S(
    "", "",
    "..1111....1111",
    ".111111111111",
    ".111111111111",
    ".111122221111",
    ".111122221111",
    "..1111111111",
    "..1111111111",
    "...11111111",
    "...11111111",
    "...22222222",
)

LEGS = S(
    "", "", "",
    "..1111111111",
    "..1111111111",
    "..1122221111",
    "..1111..1111",
    "..1111..1111",
    "..1111..1111",
    "..1111..1111",
    "..2211..1122",
    "..22......22",
)

BOOTS = S(
    "", "", "", "", "", "",
    "..1111..1111",
    "..1111..1111",
    "..1111..1111",
    ".111111.111111",
    ".111111.111111",
    ".222222.222222",
)

PIECES = {"helmet": HELM, "chestplate": CHEST, "leggings": LEGS, "boots": BOOTS}

# materiaal -> (licht, basis, schaduw/donker)
MATS = {
    "leather":   ("B98A5E", "9A6B44", "6E4A2C"),
    "chainmail": ("B6BCC2", "8C939A", "5E656C"),
    "iron":      ("E6ECE4", "CBD2CA", "969E96"),
    "golden":    ("FFE596", "F2B93F", "B87E28"),
    "diamond":   ("CFF6EE", "93E9DD", "4FAFA6"),
    "netherite": ("6E5A50", "4A3B34", "2A211C"),
    "turtle":    ("86C45E", "4E8A32", "2F5A1E"),
}


def palette(light, base, dark):
    return {"1": hx(base), "2": hx(dark), "3": hx(light)}


def items():
    """naam -> (sprite, palet). Alleen de helm bestaat voor schildpad."""
    out = {}
    for mat, cols in MATS.items():
        pal = palette(*cols)
        pieces = ["helmet"] if mat == "turtle" else PIECES
        for piece in pieces:
            out[f"{mat}_{piece}"] = (PIECES[piece], pal)
    # grijswaarden-overlay: het spel kleurt die met de verfkleur van het stuk
    grey = {"1": hx("C8C8C8"), "2": hx("8E8E8E"), "3": hx("E4E4E4")}
    for piece in PIECES:
        out[f"leather_{piece}_overlay"] = (PIECES[piece], grey)
    for mat in ("leather", "iron", "golden", "diamond"):
        out[f"{mat}_horse_armor"] = (CHEST, palette(*MATS[mat]))
    return out
