"""Kleurpaletten voor het Verdant nature-texturepack.

Alle kleuren zijn RGBA tuples. Het pack blijft strikt 16x16 (vanilla resolutie),
zodat er geen enkele impact op FPS of VRAM is.
"""

def hx(s, a=255):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


# --- gedeelde natuur-elementen (elk gereedschap gebruikt dezelfde steel) ---
WOOD = {
    "w": hx("9A7549"),   # bast licht
    "W": hx("74562F"),   # bast midden
    "k": hx("4C381E"),   # bast donker
}
CORD = {
    "c": hx("C7AC7A"),   # touw licht
    "C": hx("9C8354"),   # touw donker
}
LEAF = {
    "v": hx("8CC55E"),   # blad licht
    "V": hx("4F8A33"),   # blad donker
}

BASE = {}
BASE.update(WOOD)
BASE.update(CORD)
BASE.update(LEAF)
BASE["."] = (0, 0, 0, 0)


# --- materiaal-tiers, elk hertaald naar een natuur-materiaal ---------------
# L = highlight, M = basis, D = schaduw, K = outline, * = accent
MATERIALS = {
    # Hout -> levend twijghout met verse spint
    "wooden": {
        "L": hx("DCC08A"), "M": hx("B99A62"), "D": hx("8B7040"), "K": hx("5C4526"),
        "*": hx("8CC55E"),
        "label": "Twijghout",
    },
    # Steen -> bemoste rivierkei
    "stone": {
        "L": hx("B9BEB2"), "M": hx("90968B"), "D": hx("686E64"), "K": hx("434840"),
        "*": hx("6E9C46"),
        "label": "Moskei",
    },
    # IJzer -> gepolijste berkensteen (koel, bleek)
    "iron": {
        "L": hx("F1F5EF"), "M": hx("CBD2CA"), "D": hx("9CA69D"), "K": hx("6B756C"),
        "*": hx("A9C6B0"),
        "label": "Berksteen",
    },
    # Goud -> hars / honingamber
    "golden": {
        "L": hx("FFE596"), "M": hx("F2B93F"), "D": hx("C0842A"), "K": hx("87581A"),
        "*": hx("FFF6C8"),
        "label": "Amber",
    },
    # Diamant -> dauwkristal
    "diamond": {
        "L": hx("DFFFF7"), "M": hx("93E9DD"), "D": hx("55BDB3"), "K": hx("2F8981"),
        "*": hx("FFFFFF"),
        "label": "Dauwkristal",
    },
    # Netherite -> verkoolde wortel met sintels
    "netherite": {
        "L": hx("70594E"), "M": hx("4A3B34"), "D": hx("30251F"), "K": hx("1A1310"),
        "*": hx("C9552B"),
        "label": "Sintelwortel",
    },
}

TIER_ORDER = ["wooden", "stone", "iron", "golden", "diamond", "netherite"]


def material_palette(mat):
    p = dict(BASE)
    m = MATERIALS[mat]
    for k in ("L", "M", "D", "K", "*"):
        p[k] = m[k]
    return p


# Deterministische spikkels per materiaal: (tekens, kleur, mod, offset)
SPECKLE = {
    "wooden":    ("M",  hx("9E8047"), 9, 2),    # houtnerf
    "stone":     ("M",  hx("6E9C46"), 11, 3),   # mos
    "netherite": ("DK", hx("A8431F"), 8, 4),    # sintels
}


def material_speckle(mat):
    return SPECKLE.get(mat)
