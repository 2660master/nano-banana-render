#!/usr/bin/env python3
"""Check that the six cube faces actually join up.

Two faces that touch must look along the same directions on their shared
edge. Comparing the direction vectors instead of rendered pixels makes this
exact: a mirrored or rotated face fails here even where the sky happens to
be black on both sides, which is exactly the case a pixel diff would miss.

Run: python3 test_cube_seams.py
"""

import numpy as np

from sky_generator import CUBE_FACES, face_dirs

SIZE = 64

# All twelve edges of the cube, named as seen in each face's image.
PAIRS = [
    ("north", "right", "east", "left"),
    ("east", "right", "south", "left"),
    ("south", "right", "west", "left"),
    ("west", "right", "north", "left"),
    ("top", "top", "south", "top"),
    ("top", "bottom", "north", "top"),
    ("top", "left", "west", "top"),
    ("top", "right", "east", "top"),
    ("bottom", "top", "north", "bottom"),
    ("bottom", "bottom", "south", "bottom"),
    ("bottom", "left", "west", "bottom"),
    ("bottom", "right", "east", "bottom"),
]


def edge(d, which):
    return {"left": d[:, 0], "right": d[:, -1],
            "top": d[0], "bottom": d[-1]}[which]


def main():
    # sample the face boundary, so a shared edge is literally shared
    dirs = {f: face_dirs(f, SIZE, pixel_centres=False) for f in CUBE_FACES}

    failures = []
    for fa, ea, fb, eb in PAIRS:
        a, b = edge(dirs[fa], ea), edge(dirs[fb], eb)
        # the shared edge may be traversed in either order
        err = min(np.abs(a - b).max(), np.abs(a - b[::-1]).max())
        ok = err < 1e-5
        print(f"{'ok ' if ok else 'BAD'} {fa:6s} {ea:6s} <-> {fb:6s} {eb:6s}"
              f"   max |diff| {err:.2e}")
        if not ok:
            failures.append((fa, ea, fb, eb))

    # Sanity: the six faces must look down the six unit axes, once each.
    fwd = sorted(tuple(v[2]) for v in CUBE_FACES.values())
    assert fwd == sorted([(0, 0, -1), (0, 0, 1), (1, 0, 0),
                          (-1, 0, 0), (0, 1, 0), (0, -1, 0)]), fwd

    # Each side face must put the horizon exactly across its middle: with an
    # even SIZE no sample lands on y == 0, so check the two that straddle it.
    for f in ("north", "south", "east", "west"):
        y = dirs[f][:, SIZE // 2, 1]
        assert abs(y[SIZE // 2 - 1] + y[SIZE // 2]) < 1e-6, (f, y[SIZE // 2])

    print("all twelve edges join" if not failures else f"FAILED: {failures}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
