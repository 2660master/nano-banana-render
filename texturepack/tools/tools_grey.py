# -*- coding: utf-8 -*-
"""Zwaard, pickaxe, bijl, schep en schoffel in de vanilla-vorm.

Met de hand tellen op zestien pixels gaf steeds net niet de juiste vorm,
dus alles wordt hier gerekend, net als bij de boog. Eén hulpstuk doet het
werk: een balk met een richting, een dikte en drie lagen — hoogsel aan de
kant waar het licht vandaan komt, kern in het midden, schaduw aan de
andere kant. Daarmee is een kling hetzelfde als een steel, alleen anders
gericht.

Legenda: L hoogsel, M kern, D schaduw, H pareerstang, G greep/steel.
"""
import math

N = 16


def _leeg():
    return [["."] * N for _ in range(N)]


def _zet(g, x, y, ch, over):
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < N and 0 <= yi < N and g[yi][xi] in over:
        g[yi][xi] = ch


def _balk(g, a, b, dik, lagen, over=".", stappen=260):
    """Balk van a naar b. `lagen` is per zijstap (offset, teken).

    De zijstap staat loodrecht op de richting, dus een schuine kling
    krijgt zijn hoogsel netjes langs de snede in plaats van langs de
    pixelrand.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    lengte = math.hypot(dx, dy) or 1.0
    ux, uy = dx / lengte, dy / lengte
    px, py = -uy, ux                                   # loodrecht
    for offset, ch in lagen:
        for i in range(stappen):
            t = i / (stappen - 1.0)
            x = a[0] + dx * t + px * offset * dik
            y = a[1] + dy * t + py * offset * dik
            _zet(g, x, y, ch, over)


def _rijen(g):
    return ["".join(r) for r in g]


def zwaard():
    """Kling schuin omhoog, pareerstang er dwars op, greep naar linksonder."""
    g = _leeg()
    basis, punt = (5.2, 10.8), (14.0, 2.0)
    # kling: hoogsel aan de bovenkant (waar het licht vandaan komt)
    _balk(g, basis, punt, 1.0, ((-1, "L"), (0, "M"), (1, "D")))
    _zet(g, 14, 1, "L", ".")
    # pareerstang: dwars op de kling, dus langs dezelfde diagonaal terug
    mid = (4.6, 11.4)
    dwars = 2.6
    _balk(g, (mid[0] - dwars * 0.7071, mid[1] - dwars * 0.7071),
          (mid[0] + dwars * 0.7071, mid[1] + dwars * 0.7071),
          1.0, ((-0.5, "H"), (0.5, "H")), over=".")
    # greep met knop
    _balk(g, (4.0, 12.0), (1.6, 14.4), 1.0, ((-0.5, "G"), (0.5, "G")), ".")
    _zet(g, 1, 15, "G", ".")
    _zet(g, 0, 14, "G", ".")
    return _rijen(g)


def _kromme(g, p0, p1, p2, lagen, dik=1.0, stappen=300):
    """Kwadratische kromme; p1 trekt de bocht naar zich toe."""
    vorig = None
    for i in range(stappen):
        t = i / (stappen - 1.0)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        if vorig:
            dx, dy = x - vorig[0], y - vorig[1]
            lengte = math.hypot(dx, dy) or 1.0
            px, py = -dy / lengte, dx / lengte
            for offset, ch in lagen:
                _zet(g, x + px * offset * dik, y + py * offset * dik, ch, ".")
        vorig = (x, y)


def pickaxe():
    """Brede kop met twee punten, steel schuin naar linksonder."""
    g = _leeg()
    _kromme(g, (2.6, 7.4), (8.0, 0.6), (14.2, 5.4),
            ((-1, "L"), (0, "M"), (1, "D")))
    _zet(g, 2, 8, "D", ".")
    _zet(g, 14, 6, "D", ".")
    _balk(g, (9.4, 5.0), (2.0, 14.2), 1.0, ((-0.5, "G"), (0.5, "G")), ".")
    _zet(g, 1, 15, "G", ".")
    return _rijen(g)


def _vlak(g, punten, ch, over="."):
    """Vult een veelhoek. Per rij de snijpunten met de randen zoeken en
    daartussen doorstrepen — zo blijft een bolle snede echt bol."""
    for y in range(N):
        yy = y + 0.5
        snij = []
        for i in range(len(punten)):
            (x0, y0), (x1, y1) = punten[i], punten[(i + 1) % len(punten)]
            if (y0 <= yy < y1) or (y1 <= yy < y0):
                snij.append(x0 + (yy - y0) / (y1 - y0) * (x1 - x0))
        snij.sort()
        for i in range(0, len(snij) - 1, 2):
            for x in range(int(round(snij[i])), int(round(snij[i + 1])) + 1):
                _zet(g, x, y, ch, over)


def _boogpunten(p0, p1, p2, n=24):
    """Punten langs een kwadratische kromme, om in een veelhoek te zetten."""
    uit = []
    for i in range(n + 1):
        t = i / float(n)
        uit.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return uit


def bijl():
    """Bijlkop links: rechte bovenkant, bolle snede eronder, oog rechts.

    Drie keer bijgesteld. Eerst werd alleen de snede getekend en tussen de
    uiterste pixels per rij gevuld — zonder achterkant gaf dat een ronde
    klodder. Daarna was de kop een lens met een punt bovenaan, en juist
    die punt maakte het weer rond: een bijl heeft een rechte rug bovenaan
    en alleen onderlangs een bocht. Let ook op het stuurpunt: een
    kwadratische kromme haalt maar de helft van de weg naar zijn
    stuurpunt, dus dat ligt verder weg dan waar de bocht moet komen.
    """
    g = _leeg()
    snede = _boogpunten((7.0, 10.2), (-1.6, 7.9), (2.2, 2.0))
    _vlak(g, [(2.2, 2.0), (8.8, 2.0), (8.8, 9.4)] + snede, "M")
    _kromme(g, (7.0, 10.2), (-1.6, 7.9), (2.2, 2.0), ((0, "L"),))
    _kromme(g, (7.0, 9.2), (-0.4, 7.4), (3.0, 2.0), ((0, "L"),))
    for x in range(2, 9):
        if g[2][x] in "ML":
            g[2][x] = "L"
    for y in range(N):
        for x in range(N):
            if g[y][x] == "M" and x >= 7:
                g[y][x] = "D"
    _balk(g, (8.2, 2.8), (8.2, 9.2), 1.0, ((-0.5, "H"), (0.5, "H")), ".MD")
    _balk(g, (9.0, 4.0), (13.8, 14.6), 1.0, ((-0.5, "G"), (0.5, "G")), ".")
    _zet(g, 14, 15, "G", ".")
    return _rijen(g)


def schep():
    """Recht blad bovenaan, steel schuin naar linksonder."""
    g = _leeg()
    for y in range(1, 7):
        for x in range(9, 14):
            g[y][x] = "M"
    for y in range(1, 7):
        g[y][9] = "L"
        g[y][13] = "D"
    for x in range(9, 14):
        g[1][x] = "L" if x < 12 else "M"
        g[6][x] = "D"
    _balk(g, (11.0, 6.4), (2.0, 14.4), 1.0, ((-0.5, "G"), (0.5, "G")), ".")
    _zet(g, 1, 15, "G", ".")
    return _rijen(g)


def schoffel():
    """Haakse kop, steel schuin naar linksonder."""
    g = _leeg()
    _balk(g, (8.6, 2.0), (14.0, 2.0), 1.0, ((-0.5, "L"), (0.5, "M")), ".")
    _balk(g, (8.6, 2.0), (8.6, 6.2), 1.0, ((-0.5, "M"), (0.5, "D")), ".")
    _balk(g, (9.6, 3.0), (2.0, 14.4), 1.0, ((-0.5, "G"), (0.5, "G")), ".")
    _zet(g, 1, 15, "G", ".")
    return _rijen(g)


def drietand():
    """Trident: lange schacht, dwarsbalk, drie tanden.

    Twee dingen moesten anders. De tanden worden eerst gezet en pas
    daarna de dwarsbalk en de schacht, anders kunnen ze nergens meer heen.
    En ze staan verder uit elkaar en zijn één pixel dun: op anderhalve
    pixel afstand met twee pixels dikte liepen ze in elkaar over en werd
    de kop een blok.
    """
    g = _leeg()
    ux, uy = 0.7071, -0.7071
    px, py = 0.7071, 0.7071
    kop = (10.0, 6.0)
    a = (kop[0] - 3.0 * px, kop[1] - 3.0 * py)
    b = (kop[0] + 3.0 * px, kop[1] + 3.0 * py)
    for voet in (a, kop, b):
        tip = (voet[0] + 4.2 * ux, voet[1] + 4.2 * uy)
        _balk(g, voet, tip, 1.0, ((0, "L"),), ".")
    _balk(g, a, b, 1.0, ((-0.5, "H"), (0.5, "H")), ".")
    _balk(g, (1.6, 14.4), kop, 1.0, ((-0.5, "G"), (0.5, "G")), ".")
    _zet(g, 1, 15, "G", ".")
    return _rijen(g)


ALLES = {
    "netherite_sword": zwaard,
    "netherite_pickaxe": pickaxe,
    "netherite_axe": bijl,
    "netherite_shovel": schep,
    "netherite_hoe": schoffel,
    "trident": drietand,
}


def speer():
    """Speer: lange schacht met een bladvormige punt.

    Het blad is geen veelhoek maar een balk die versmalt: kern over de
    hele lengte, hoogsel en schaduw alleen over het eerste stuk. Als
    veelhoek was hij zo dun dat er na het afronden niets van overbleef.
    """
    g = _leeg()
    kop = (10.0, 6.0)
    _balk(g, (1.4, 14.6), kop, 1.0, ((-0.5, "G"), (0.5, "G")), ".")
    _zet(g, 0, 15, "G", ".")
    _balk(g, (kop[0] - 0.9, kop[1] - 0.9), (kop[0] + 0.9, kop[1] + 0.9),
          1.0, ((-0.5, "H"), (0.5, "H")), ".")
    basis, punt = (10.4, 5.6), (14.8, 1.2)
    breed = (basis[0] + (punt[0] - basis[0]) * 0.62,
             basis[1] + (punt[1] - basis[1]) * 0.62)
    _balk(g, basis, breed, 1.0, ((-1, "L"), (1, "D")), ".")
    # twee halve stappen naast elkaar: een enkele lijn op precies 45
    # graden laat na afronden gaten vallen
    _balk(g, basis, punt, 1.0, ((-0.4, "M"), (0.4, "M")), ".")
    _zet(g, 14, 1, "L", ".M")
    return _rijen(g)


ALLES["copper_spear"] = speer
