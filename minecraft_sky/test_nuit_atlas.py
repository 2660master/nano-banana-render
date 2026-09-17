#!/usr/bin/env python3
"""Check the atlas against Nuit's own renderer maths.

test_cube_seams.py only proves the six faces are consistent with each other.
They could still be consistent and rotated as a set, which in game shows up
as a sky that is upside down or facing the wrong way. So this test
reimplements what Nuit actually does when it draws a square-textured
skybox, straight from its source:

  Utils.TEXTURE_FACES        - which atlas cell each face reads
  Utils.MATRIX4F_ROTATED_FACE - how that cell is rotated into the world
  SquareTexturedSkybox.renderSkybox - which quad corner gets which UV

and asserts that the direction Nuit will show at a given atlas pixel is the
direction this generator drew there. Face order is Nuit's:
0 bottom, 1 north, 2 south, 3 top, 4 east, 5 west.

Run: python3 test_nuit_atlas.py
"""

import math

import numpy as np

from sky_generator import ATLAS_CELLS, ATLAS_COLS, ATLAS_ROWS, face_dirs

SIZE = 32

# Utils.TEXTURE_FACES, in Nuit's face order: (minU, minV, maxU, maxV)
TEXTURE_FACES = [
    (0.0, 0.0, 1 / 3, 1 / 2),      # bottom
    (1 / 3, 1 / 2, 2 / 3, 1.0),    # north
    (2 / 3, 0.0, 1.0, 1 / 2),      # south
    (1 / 3, 0.0, 2 / 3, 1 / 2),    # top
    (2 / 3, 1 / 2, 1.0, 1.0),      # east
    (0.0, 1 / 2, 1 / 3, 1.0),      # west
]
FACE_ORDER = ["bottom", "north", "south", "top", "east", "west"]


def _rx(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)


def _ry(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)


def _rz(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)


# Utils.MATRIX4F_ROTATED_FACE. JOML's .rotateX(a).rotateY(b) post-multiplies,
# so the matrix is Rx(a) @ Ry(b) and Ry lands on the vector first.
FACE_MATRIX = [
    np.eye(3),                    # bottom
    _rx(90),                      # north
    _rx(-90) @ _ry(180),          # south
    _rx(180),                     # top
    _rz(90) @ _ry(-90),           # east
    _rz(-90) @ _ry(90),           # west
]


def nuit_direction(face_index, s, t):
    """Where Nuit points the quad corner that samples UV (s, t) of a cell.

    renderSkybox lays the quad out at y = -100 with x running along U and
    z along V, then rotates it by the face matrix.
    """
    local = np.stack([-100.0 + 200.0 * s,
                      np.full_like(s, -100.0),
                      -100.0 + 200.0 * t], axis=-1)
    world = local @ FACE_MATRIX[face_index].T
    return world / np.linalg.norm(world, axis=-1, keepdims=True)


def main():
    # 1. every face's cell in ATLAS_CELLS must be the rect Nuit reads from
    for idx, name in enumerate(FACE_ORDER):
        col, row = ATLAS_CELLS[name]
        expect = (col / ATLAS_COLS, row / ATLAS_ROWS,
                  (col + 1) / ATLAS_COLS, (row + 1) / ATLAS_ROWS)
        got = TEXTURE_FACES[idx]
        assert np.allclose(expect, got, atol=1e-6), (name, expect, got)
        print(f"ok  {name:6s} cell col {col} row {row} == Nuit UV rect")

    # 2. and every pixel inside it must carry the direction Nuit will show
    worst = 0.0
    g = (np.arange(SIZE, dtype=np.float64) + 0.5) / SIZE
    s, t = np.meshgrid(g, g)
    for idx, name in enumerate(FACE_ORDER):
        theirs = nuit_direction(idx, s, t)
        mine = face_dirs(name, SIZE).astype(np.float64)
        err = np.abs(theirs - mine).max()
        worst = max(worst, err)
        print(f"{'ok ' if err < 1e-6 else 'BAD'} {name:6s} orientation "
              f"max |diff| {err:.2e}")

    print("atlas matches Nuit's renderer" if worst < 1e-6
          else f"FAILED: worst {worst:.2e}")
    raise SystemExit(0 if worst < 1e-6 else 1)


if __name__ == "__main__":
    main()
