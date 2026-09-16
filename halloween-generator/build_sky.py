"""Render a concept into Nuit's square-textured 3x2 skybox sheet, and verify the seams.

Face layout is taken from Nuit's Utils.TEXTURE_FACES (branch 1.21.11/dev):

    row 0 |  bottom | top   | south
    row 1 |  west   | north | east
"""
import sys, time
import numpy as np
from PIL import Image
import skylib
from preview import tonemap

FACE_ORDER = ["bottom", "top", "south", "west", "north", "east"]


def render_faces(fn, size):
    faces = {}
    for name in FACE_ORDER:
        t = time.time()
        d = skylib.face_dirs(name, size)
        faces[name] = tonemap(fn(d)).astype(np.float64) / 255.0
        print(f"  {name:<7} {size}x{size}  {time.time() - t:5.1f}s")
    return faces


def sheet_from_faces(faces, size):
    sheet = np.zeros((size * 2, size * 3, 3))
    for name, (col, row) in skylib.FACE_GRID.items():
        sheet[row * size:(row + 1) * size, col * size:(col + 1) * size] = faces[name]
    return sheet


def _edges(arr):
    return {"top": arr[0, :], "bottom": arr[-1, :], "left": arr[:, 0], "right": arr[:, -1]}


def check_seams(faces, size, tol_dir=0.01):
    """Every cube edge is shared by exactly two faces; the pixels along it must agree."""
    dirs = {f: _edges(skylib.face_dirs(f, size)) for f in FACE_ORDER}
    cols = {f: _edges(faces[f]) for f in FACE_ORDER}
    keys = [(f, e) for f in FACE_ORDER for e in ("top", "bottom", "left", "right")]
    matched, worst = 0, 0.0
    for i, (fa, ea) in enumerate(keys):
        for fb, eb in keys[i + 1:]:
            if fa == fb:
                continue
            da, db = dirs[fa][ea], dirs[fb][eb]
            fwd = np.abs(da - db).max()
            rev = np.abs(da - db[::-1]).max()
            flip = rev < fwd
            if min(fwd, rev) > tol_dir:
                continue
            ca = cols[fa][ea]
            cb = cols[fb][eb][::-1] if flip else cols[fb][eb]
            diff = np.abs(ca - cb)
            matched += 1
            worst = max(worst, diff.mean())
            print(f"  seam {fa:<7}.{ea:<6} <-> {fb:<7}.{eb:<6} "
                  f"{'(flipped)' if flip else '         '} "
                  f"mean dC {diff.mean():.4f}  max dC {diff.max():.3f}")
    print(f"  -> {matched}/12 cube edges matched, worst mean colour delta {worst:.4f}")
    assert matched == 12, f"expected 12 shared edges, found {matched}"
    assert worst < 0.02, f"seam colour mismatch too large: {worst}"


if __name__ == "__main__":
    import concepts, scary
    slug = sys.argv[1]
    size = int(sys.argv[2])
    out = sys.argv[3]
    fn = {c[2]: c[3] for c in concepts.CONCEPTS + scary.SCARY}[slug]
    print(f"rendering '{slug}' at {size}px/face")
    faces = render_faces(fn, size)
    print("verifying seams")
    check_seams(faces, size)
    sheet = sheet_from_faces(faces, size)
    Image.fromarray((sheet * 255 + 0.5).astype(np.uint8)).save(out, optimize=True)
    print(f"wrote {out}  {sheet.shape[1]}x{sheet.shape[0]}")
