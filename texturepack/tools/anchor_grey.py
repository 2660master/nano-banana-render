# -*- coding: utf-8 -*-
"""Respawn anchor: wit blok met een ronde gloeiende cirkel.

De zijkant houdt de cirkel — die vult van onderaf op naarmate er meer
ladingen in zitten. De bovenkant is het portaalvlak, hier in wit met
grijs in plaats van paars.
"""
import math

from PIL import Image

from palette import hx


def _ring(x, y, cx=7.5, cy=7.5):
    return math.hypot(x - cx, y - cy)


def side(charge, radius=4.3, glow="FFFFFF", stone="E8ECEE",
         shade="B4BCC1", line="6E767C", socket="3A4045"):
    """Wit blok met de ronde opening; vult van onderaf met gloed."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                c = hx(line)
            elif _ring(x, y) <= radius:
                if charge and y >= 12 - charge * 2:
                    # kern feller dan de rand van de cirkel
                    c = hx(glow) if _ring(x, y) <= radius - 1.4 else hx(shade)
                else:
                    c = hx(socket)
            elif (x * 5 + y * 3) % 4 == 0:
                c = hx(shade)
            else:
                c = hx(stone)
            px[x, y] = c
    return im


def top(rings=3, inner="FFFFFF", outer="9AA2A8", stone="E8ECEE",
        line="6E767C"):
    """Het portaalvlak: concentrische ringen in wit en grijs."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    for y in range(16):
        for x in range(16):
            d = _ring(x, y)
            if x in (0, 15) or y in (0, 15):
                c = hx(line)
            elif d <= 6.2:
                t = (d / 6.2 * rings) % 1.0
                c = hx(inner) if t < 0.5 else hx(outer)
            else:
                c = hx(stone)
            px[x, y] = c
    return im


def bottom(stone="D8DEE2", shade="AAB2B8", line="6E767C"):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                c = hx(line)
            else:
                c = hx(shade) if (x * 7 + y * 5) % 5 == 0 else hx(stone)
            px[x, y] = c
    return im
