# -*- coding: utf-8 -*-
"""Het grijze PvP-pack: paletten en effecten.

Strak betekent hier: vlakke kleurvlakken, harde randen, geen ruis. Waar het
natuurpack korrel en mos had, staat hier alleen vorm en licht.
"""
from palette import hx

# gewone PvP-uitrusting: koel grijs, drie stappen plus een greep
GREY = {
    "L": hx("E4E9EC"),    # hoogsel
    "M": hx("AAB2B7"),    # basis
    "D": hx("6E767B"),    # schaduw
    "K": hx("454B50"),    # outline
    "H": hx("5A6166"),    # pareerstang
    "G": hx("3C4145"),    # greep
}

# netherite: zelfde grijs, maar met de witte gloed eroverheen (zie sheen)
NETHERITE = {
    "L": hx("C6CED4"),
    "M": hx("767F88"),
    "D": hx("434A51"),
    "K": hx("22272B"),
    "H": hx("3A4046"),
    "G": hx("23282D"),
}


def sheen(im, top=1.62, bottom=0.30, gamma=1.00):
    """Witte gloed die van boven naar beneden uitdooft.

    Boven vangt het volle licht, onderin zakt het weg. Het verloop gaat
    naar wit toe in plaats van simpelweg lichter, zodat het als glans
    leest en niet als een uitgebleekte texture.
    """
    px = im.load()
    w, h = im.size
    for y in range(h):
        t = (y / (h - 1)) ** gamma
        f = top + (bottom - top) * t
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if f >= 1.0:
                k = min(0.85, f - 1.0)
                r += (255 - r) * k
                g += (255 - g) * k
                b += (255 - b) * k
            else:
                k = 1.0 - f
                r *= 1.0 - k
                g *= 1.0 - k
                b *= 1.0 - k
            px[x, y] = (int(r), int(g), int(b), a)
    return im
