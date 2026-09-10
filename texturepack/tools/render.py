"""Pixel-art renderer: zet 16x16 tekenkaarten om naar PNG's."""
from PIL import Image
import shading
from palette import BASE

SIZE = 16


def validate(rows, name="?"):
    if len(rows) != SIZE:
        raise ValueError(f"{name}: {len(rows)} rijen i.p.v. {SIZE}")
    for i, r in enumerate(rows):
        if len(r) != SIZE:
            raise ValueError(f"{name}: rij {i} is {len(r)} tekens i.p.v. {SIZE} -> {r!r}")


def _mul(c, f):
    return (
        max(0, min(255, int(c[0] * f))),
        max(0, min(255, int(c[1] * f))),
        max(0, min(255, int(c[2] * f))),
        c[3],
    )


def render(rows, pal, name="?", outline=True, outline_factor=0.68, rim=True, rim_factor=1.10,
           speckle=None, no_outline="vVcC", relief=1.0):
    """rows: 16 strings. pal: dict char -> RGBA.

    outline: donkert de onder-/rechterrand af (klassieke Minecraft-look).
    rim:     licht de linker-/bovenrand licht op.
    speckle: (tekens, kleur, mod, offset) -> deterministische spikkels
             (mos op steen, sintels in netherite, nerf in hout).
    no_outline: tekens die geen randschaduw krijgen. Dunne details zoals
             ranken en boogpezen zouden anders volledig verduisteren.
    relief:  hoe sterk de belichting uit shading.py meedoet. 0 zet hem uit.
    """
    validate(rows, name)
    p = dict(BASE)
    p.update(pal)

    chars = [[rows[y][x] for x in range(SIZE)] for y in range(SIZE)]
    grid = []
    for y in range(SIZE):
        line = []
        for x in range(SIZE):
            ch = rows[y][x]
            if ch not in p:
                raise KeyError(f"{name}: onbekend teken {ch!r} op ({x},{y})")
            col = p[ch]
            if speckle:
                sch, scol, smod, soff = speckle
                if ch in sch and ((x * 7 + y * 13 + soff) % smod) == 0:
                    col = scol
            line.append(col)
        grid.append(line)

    def solid(x, y):
        return 0 <= x < SIZE and 0 <= y < SIZE and grid[y][x][3] > 0

    lit = shading.light(grid, SIZE, seed=len(name)) if relief > 0 else None

    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = out.load()
    for y in range(SIZE):
        for x in range(SIZE):
            c = grid[y][x]
            if c[3] == 0:
                continue
            thin = chars[y][x] in no_outline
            if outline and not thin and (not solid(x + 1, y) or not solid(x, y + 1)):
                c = _mul(c, outline_factor)
            elif rim and (not solid(x - 1, y) and not solid(x, y - 1)):
                c = _mul(c, rim_factor)
            if lit and not thin:
                f, spec = lit[y][x]
                f = 1.0 + (f - 1.0) * relief
                c = shading.shade(c, f, spec * relief)
            px[x, y] = c
    return out
