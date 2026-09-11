# -*- coding: utf-8 -*-
"""Shield, elytra, ender chest en potions.

Let op het verschil tussen de twee soorten hier. De potions zijn gewone
item-plaatjes van 16x16: die kun je pixel voor pixel neerzetten omdat je
precies weet waar alles terechtkomt.

Shield, elytra en de ender chest zijn entity-vellen: het model plakt daar
stukken uit op vlakken van een 3D-vorm, en zonder de vanilla-vellen ernaast
weet je niet welk stuk waar landt. Daarom zijn die hier dekkend getekend —
een doorlopend patroon over het hele vel, zodat elk stuk dat het model
eruit pakt er hetzelfde uitziet. Dezelfde truc als bij de end crystal.
"""
from PIL import Image

from blocks import mix, mul, noise
from palette import hx
from sky import fbm2


def _plaat(w, h, base, licht, donker, seed, korrel=0.10, band=0.22):
    """Geborsteld metaal: fijne verticale nerf plus grote vlakken licht."""
    im = Image.new("RGBA", (w, h))
    px = im.load()
    b, l, d = hx(base), hx(licht), hx(donker)
    for y in range(h):
        for x in range(w):
            nerf = noise(x, y // 2, seed) - 0.5
            vlak = fbm2(x, y, max(w, h), seed + 7, octaves=3,
                        cells_x=2, cells_y=4) - 0.5
            t = nerf * korrel + vlak * band
            px[x, y] = mix(b, l, t * 1.8) if t > 0 else mix(b, d, -t * 1.8)
    return im


def shield(size=64, base="8A9298", licht="E2E8EC", donker="4A5157",
           seed=61):
    """Schildvel: doorlopend geborsteld metaal, zonder naden.

    Eerste opzet zette elke zestien pixels een donkere naad neer als
    beslag. Dat lijkt netjes op het vel, maar het model knipt er stukken
    uit op plekken die niets met dat raster te maken hebben, dus op het
    schild zelf belanden die lijnen willekeurig. Een doorlopend materiaal
    ziet er overal goed uit, waar het model ook snijdt.
    """
    return _plaat(size, size, base, licht, donker, seed, korrel=0.12,
                  band=0.20)


def elytra(w=64, h=32, base="C2CAD0", licht="FFFFFF", donker="6E767C",
           seed=71, veren=6):
    """Elytravel, dekkend, met schuine veerlijnen over het hele vel."""
    im = _plaat(w, h, base, licht, donker, seed, korrel=0.08, band=0.18)
    px = im.load()
    stap = max(2, h // veren)
    for y in range(h):
        for x in range(w):
            if (x + y) % stap == 0:                  # veernerf
                px[x, y] = mul(px[x, y], 0.80)
            elif (x + y) % stap == 1:
                px[x, y] = mul(px[x, y], 1.14)
    return im


def ender_chest(size=64, base="20242A", licht="9AA4B0", donker="0E1114",
                vonk="E8EEF4", seed=81, vonken=0.055):
    """Ender chest: donker doorlopend, met losse lichtpunten erin.

    Ook hier geen raster om dezelfde reden als bij het schild. De vonken
    doen het werk dat de groene ogen in vanilla doen, en die mogen overal
    vallen — dat is juist wat ze moeten doen.
    """
    im = _plaat(size, size, base, licht, donker, seed, korrel=0.08, band=0.30)
    px = im.load()
    for y in range(size):
        for x in range(size):
            if noise(x, y, seed + 33) > 1.0 - vonken:
                px[x, y] = mix(px[x, y], hx(vonk), 0.75)
    return im


# ------------------------------------------------------------------ potions
N = 16
# De fles: 'g' is glas, 'k' de kurk, 'r' de rand. Het vocht zit in een
# tweede plaatje dat het spel inkleurt, dus dat wordt hier grijs getekend.
FLES = (
    "................",
    "................",
    "......kkk.......",
    "......kkk.......",
    "......ggg.......",
    ".....ggggg......",
    "....ggggggg.....",
    "...ggggggggg....",
    "...ggggggggg....",
    "..ggggggggggg...",
    "..ggggggggggg...",
    "..ggggggggggg...",
    "..ggggggggggg...",
    "...ggggggggg....",
    "....rrrrrrr.....",
    "................",
)


def potion(glas="C8D2D8", glans="FFFFFF", kurk="6E767C", rand="4A5157"):
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = im.load()
    kleur = {"g": hx(glas), "k": hx(kurk), "r": hx(rand)}
    for y, rij in enumerate(FLES):
        for x, ch in enumerate(rij):
            if ch != ".":
                px[x, y] = kleur[ch]
    for y in range(N):                                # glans links
        for x in range(N):
            if px[x, y][3] and FLES[y][x] == "g" and x in (3, 4) and y > 7:
                px[x, y] = hx(glans)
    return im


def potion_overlay(vocht="E4E9EC", diep="B4BCC1", niveau=9):
    """Het vocht. Het spel vermenigvuldigt dit met de drankkleur, dus het
    staat hier bewust in grijs: wie hier kleurt krijgt dubbele kleur."""
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = im.load()
    for y, rij in enumerate(FLES):
        if y < niveau:
            continue
        for x, ch in enumerate(rij):
            if ch == "g":
                px[x, y] = hx(vocht) if y < niveau + 2 else hx(diep)
    return im
