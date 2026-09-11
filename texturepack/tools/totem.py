# -*- coding: utf-8 -*-
"""Totem of undying, getekend in plaats van per pixel gezet.

De oude totem was een blokkerig poppetje van zestien bij zestien. Twee
dingen lossen dat op. Ten eerste mag een item-texture groter: 64x64 is
nog steeds één kleine plaat en kost geen frametijd, alleen geheugen.
Ten tweede wordt hier op vier keer die grootte getekend en daarna
teruggeschaald, zodat rondingen echt rond worden in plaats van getrapt.
"""
from PIL import Image, ImageDraw

SS = 4                                  # overbemonstering


def _c(h):
    """'E8B93C' naar iets wat ImageDraw slikt."""
    return "#" + h.lstrip("#")


def _d(size):
    im = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def totem(size=64, gold="E8B93C", gold_d="A8791C", gold_l="FFE08A",
          body="2FA860", body_d="18653A", body_l="5FD68C",
          gem="D8443C", eye="F4F8FA", line="1A2A22"):
    """Een gouden hoofdtooi, een groen gezicht en een lijf met armen."""
    gold, gold_d, gold_l = _c(gold), _c(gold_d), _c(gold_l)
    body, body_d, body_l = _c(body), _c(body_d), _c(body_l)
    gem, eye, line = _c(gem), _c(eye), _c(line)
    im, d = _d(size)
    S = size * SS
    u = S / 64.0                        # één vanilla-pixel in deze schaal

    def box(x0, y0, x1, y1, fill, outline=None, w=1):
        d.rectangle([x0 * u, y0 * u, x1 * u, y1 * u], fill=fill,
                    outline=outline, width=int(w * u))

    def ell(x0, y0, x1, y1, fill, outline=None, w=1):
        d.ellipse([x0 * u, y0 * u, x1 * u, y1 * u], fill=fill,
                  outline=outline, width=int(w * u))

    def poly(pts, fill, outline=None):
        d.polygon([(x * u, y * u) for (x, y) in pts], fill=fill,
                  outline=outline)

    # --- hoofdtooi: brede waaier achter het hoofd
    veren = ((-20, 14), (-13, 8), (-6, 4), (1, 3), (8, 4), (15, 8), (21, 14))
    for i, (dx, top) in enumerate(veren):
        poly([(32 + dx - 4.6, 22), (32 + dx - 1.6, top),
              (32 + dx + 1.6, top), (32 + dx + 4.6, 22)],
             fill=gold if i % 2 == 0 else gold_d)
        if i % 2 == 0:
            poly([(32 + dx - 4.6, 22), (32 + dx - 1.6, top),
                  (32 + dx, top), (32 + dx, 22)], fill=gold_l)

    # --- hoofdband
    box(15, 19, 49, 25, gold, outline=line, w=1)
    box(16, 20, 48, 22, gold_l)
    for gx in range(19, 47, 5):                    # inkepingen in de band
        box(gx, 20, gx + 1, 24, gold_d)

    # --- oorplaten
    ell(11, 28, 18, 40, gold, outline=line, w=1)
    ell(46, 28, 53, 40, gold, outline=line, w=1)
    ell(13, 30, 16, 38, gold_l)
    ell(48, 30, 51, 38, gold_l)

    # --- gezicht: smal ovaal
    ell(19, 22, 45, 48, body, outline=line, w=1)
    ell(21, 24, 39, 42, body_l)                    # licht van linksboven
    ell(25, 30, 45, 48, body)
    ell(27, 36, 44, 48, body_d)                    # kaak in de schaduw
    ell(19, 22, 45, 48, None, outline=line, w=1)

    # --- wenkbrauwrichel
    poly([(22, 30), (32, 28), (42, 30), (42, 32), (32, 30), (22, 32)],
         fill=gold_d)

    # --- ogen: smal en gesneden
    for ex in (24, 34):
        ell(ex, 32, ex + 6, 37, line)
        ell(ex, 32, ex + 6, 36, eye)
        ell(ex + 2, 33, ex + 4, 36, line)

    # --- neus
    poly([(32, 33), (29, 41), (35, 41)], fill=body_d)
    poly([(32, 33), (32, 41), (35, 41)], fill=body)
    box(29, 41, 35, 42, line)

    # --- mond
    box(26, 44, 38, 47, line)
    box(27, 44, 37, 46, gold)
    box(27, 46, 37, 46, gold_d)

    # --- hals
    box(28, 48, 36, 51, body_d)

    # --- lijf, tot onderaan
    poly([(20, 50), (44, 50), (49, 64), (15, 64)], fill=body, outline=line)
    poly([(20, 50), (32, 50), (32, 64), (15, 64)], fill=body_l)
    poly([(35, 50), (44, 50), (49, 64), (35, 64)], fill=body_d)

    # --- armen gekruist met gouden banden
    poly([(16, 55), (30, 51), (31, 55), (17, 59)], fill=gold, outline=line)
    poly([(48, 55), (34, 51), (33, 55), (47, 59)], fill=gold, outline=line)

    # --- steen op de borst
    ell(28, 55, 36, 63, gem, outline=line, w=1)
    ell(29, 56, 32, 59, gold_l)

    return im.resize((size, size), Image.LANCZOS)
