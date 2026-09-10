# -*- coding: utf-8 -*-
"""Belichting die van een plat silhouet een ronde vorm maakt.

De aanpak: uit het silhouet wordt een afstandsveld gehaald — hoe diep zit
een pixel in de vorm. Dat veld is in feite een hoogtekaart, en de helling
ervan geeft de normaal van het oppervlak. Daar wordt gewoon Lambert-licht
op losgelaten, plus een glans.

Zo krijgt elk item vanzelf een bolle kant naar het licht toe en een
donkere rand ervan af, zonder dat er één pixel met de hand bijgetekend
hoeft te worden.

De kleurverschuiving is net zo belangrijk als de helderheid: licht loopt
naar warm, schaduw naar koel. Dat is wat pixelkunst geverfd laat ogen in
plaats van uitgebleekt.
"""
import math

LIGHT = (-0.46, -0.58, 0.67)          # linksboven, iets naar de kijker toe
_L = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _L for c in LIGHT)

# halfvector voor de glans (kijkrichting is recht van voren)
_H = (LIGHT[0], LIGHT[1], LIGHT[2] + 1.0)
_HL = math.sqrt(sum(c * c for c in _H))
HALF = tuple(c / _HL for c in _H)

NEIGH8 = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))


def shade(c, f, spec=0.0):
    """f schaalt de helderheid; spec zet er een warme glans bovenop."""
    r, g, b = float(c[0]), float(c[1]), float(c[2])
    if f >= 1.0:
        k = min(0.85, f - 1.0)
        r += (255 - r) * k * 1.15
        g += (255 - g) * k * 0.94
        b += (255 - b) * k * 0.60
    else:
        k = min(0.88, 1.0 - f)
        r *= 1.0 - k * 1.14
        g *= 1.0 - k * 1.00
        b *= 1.0 - k * 0.88          # blauw blijft iets langer staan: koele schaduw
    if spec > 0:
        r += (255 - r) * spec
        g += (255 - g) * spec * 0.96
        b += (255 - b) * spec * 0.88
    return (max(0, min(255, int(r))), max(0, min(255, int(g))),
            max(0, min(255, int(b))), c[3])


def grain(x, y, seed=0):
    n = (x * 73856093 ^ y * 19349663 ^ seed * 83492791) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFF) / 255.0


def depth_field(grid, size, cap=4):
    """Chebyshev-afstand tot de dichtstbijzijnde lege pixel."""
    d = [[0.0 if grid[y][x][3] == 0 else float(cap) for x in range(size)]
         for y in range(size)]
    for _ in range(cap):
        for y in range(size):
            for x in range(size):
                if d[y][x] == 0.0:
                    continue
                lo = cap
                for dx, dy in NEIGH8:
                    nx, ny = x + dx, y + dy
                    v = 0.0 if not (0 <= nx < size and 0 <= ny < size) else d[ny][nx]
                    lo = min(lo, v)
                d[y][x] = min(d[y][x], lo + 1.0)
    return d


def light(grid, size, seed=0, roundness=1.35, ambient=0.52):
    """Geeft per pixel (helderheidsfactor, glans) terug."""
    d = depth_field(grid, size)
    out = [[(1.0, 0.0)] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            if grid[y][x][3] == 0:
                continue

            def at(px, py):
                return d[py][px] if 0 <= px < size and 0 <= py < size else 0.0

            # helling van de hoogtekaart -> normaal van het oppervlak
            nx = -(at(x + 1, y) - at(x - 1, y)) * 0.5
            ny = -(at(x, y + 1) - at(x, y - 1)) * 0.5
            nz = roundness
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            nx, ny, nz = nx / ln, ny / ln, nz / ln

            lam = max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])
            f = ambient + lam * 0.62

            # occlusie: dun materiaal en binnenhoeken vangen minder licht
            f *= 0.93 + min(1.0, d[y][x] / 2.2) * 0.09

            hdot = max(0.0, nx * HALF[0] + ny * HALF[1] + nz * HALF[2])
            spec = (hdot ** 20) * 0.34

            f *= 0.985 + grain(x, y, seed) * 0.030
            out[y][x] = (f, spec)
    return out
