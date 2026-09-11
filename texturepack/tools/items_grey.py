# -*- coding: utf-8 -*-
"""Losse PvP-items voor het grijze pack.

Deze blijven bewust 16x16, net als het zwaard en de bijl: een item dat
vier keer scherper is dan de rest valt uit de toon in je hotbar.
"""
import math

from PIL import Image

from blocks import mix, mul, noise
from palette import hx

N = 16


def orb(base="AAB2B7", light="E8EDF0", dark="5A6166", rim="343A3E",
        radius=7.0, swirl=0.0, swirl_col="FFFFFF", glow=0.0, seed=3):
    """Een bol met licht uit linksboven.

    De rand is één pixel donker zodat hij los komt van de achtergrond,
    zoals elk vanilla-item. Straal 7.0 is met opzet gekozen: bij 6.6 en
    6.8 steken de vier pixels op de assen uit en krijg je een plusvorm
    langs de rand. Bij 7.0 loopt het netjes 6, 8, 10, 12, 14 breed.
    """
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = im.load()
    b, l, d, r = hx(base), hx(light), hx(dark), hx(rim)
    cx = cy = N / 2.0
    for y in range(N):
        for x in range(N):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > radius:
                continue
            if dist > radius - 1.0:
                px[x, y] = r
                continue
            # bolvorm: de normaal volgt uit de plek op de schijf
            u, v = dx / radius, dy / radius
            w = max(0.0, 1.0 - u * u - v * v) ** 0.5
            lam = max(0.0, -u * 0.52 - v * 0.58 + w * 0.63)
            c = mix(d, b, min(1.0, lam * 1.7))
            c = mix(c, l, max(0.0, lam - 0.62) * 2.2)
            if swirl:
                # een band die om de bol krult
                ang = math.atan2(v, u)
                band = math.sin(ang * 2.0 + dist * 1.5 + seed)
                if band > 1.0 - swirl:
                    c = mix(c, hx(swirl_col), (band - (1.0 - swirl)) / swirl * 0.8)
            if glow:
                c = mix(c, hx("FFFFFF"), glow * max(0.0, 1.0 - dist / radius) ** 2)
            px[x, y] = c
    return im
