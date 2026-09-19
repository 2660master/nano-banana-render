#!/usr/bin/env python3
"""Build the Nuit square-textured skybox atlas for the MadisonBeerSky resource pack.

The atlas is a 3x2 grid of cube faces. Nuit's face -> cell mapping is taken from
``Utils.TEXTURE_FACES`` in the mod source (tag ``mc1.21.11-1.0.0-beta.6``):

    col 0        col 1        col 2
    bottom       top          south     <- row 0
    west         north        east      <- row 1

Pipeline:
  1. Cut the cloud collage into its tiles and keep the wide bottom panorama.
  2. Warp that panorama into a seamless 2:1 equirectangular sky (poles included).
  3. Re-project the equirectangular map onto the six cube faces.
  4. Composite one cut-out portrait onto the north face and one onto the south face.

Cloud sharpness is bounded by the source: the panorama is only 2000 px wide, so the
fewer degrees of sky each of those pixels has to cover, the more detail survives.
``--wraps 2`` therefore repeats the panorama twice around the horizon instead of
stretching one copy over the full 360 degrees, doubling the angular pixel density.
The two joins land dead centre on the north and south faces, where the portraits
cover them.

Usage:  python3 build_skybox.py [--face-size 2048] [--wraps 2] [--out <path.png>]
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO_ROOT / "minecraft" / "source-images"
DEFAULT_OUT = REPO_ROOT / "minecraft" / "MadisonBeerSky" / "assets" / "nuit" / "sky" / "madison_beer_sky.png"

# Collage geometry of sky.webp (2000x1333); seams detected at x=667, x=1333, y=667.
# The top-left tile carries the stock-photo watermark and is deliberately unused.
#
# The panorama tile is 666 rows tall, but its bottom ~50 rows hold two dark, hard-edged
# blobs the generator left in the shadowed deck. They pass unnoticed at 1:1 and turn
# into obvious specks once the sky is magnified, so the crop stops above them.
PANORAMA_BOX = (0, 667, 2000, 1279)
ZENITH_BOX = (1333, 0, 2000, 667)  # top-right tile: upward shot, deep blue sky
NADIR_BOX = (1120, 336, 1650, 608)  # dense cloud deck, clear of those blobs

# How far past the cap the fisheye photo is faded out, as a multiple of the cap angle.
CAP_FADE_SCALE = 2.2

# Row of the panorama where the distant cloud deck meets the blue sky. Measured by
# tracking where per-row "blueness" (mean B - mean R) crosses zero.
HORIZON_ROW = 390

# Vertical field of view the cropped panorama is stretched to cover, per --wraps
# setting. One wrap is close to isotropic; two wraps double the horizontal pixel
# density, and 71.7 degrees still carries the band to the top of every side face
# while holding the vertical stretch to a barely visible 1.3x. Both values put the
# horizon 45.7 degrees below the top of the band, so the geometry matches either way.
PANORAMA_FOV_DEG = {1: 103.0, 2: 71.7}

# Width of the wrap-around overlap used to close each seam, in equirect columns.
# Kept narrow on purpose: a cross-fade is a double exposure, so every column it spans
# loses cloud detail. The loop search below is what makes a narrow one hold up.
SEAM_BLEND_PX = 256

# How many columns the loop search may trim from each end of the panorama while
# hunting for the pair of edges that butt together most cleanly.
LOOP_SEARCH_PX = 260
LOOP_STRIP_PX = 24

# Sized so a 2048 px face samples the map at roughly 1:1 (a face spans a quarter of
# the width), which keeps the projection from adding a second round of upscaling.
EQUIRECT_WIDTH = 8192
EQUIRECT_HEIGHT = 4096

# Detail restoration for the sky, applied per face before the portraits go on.
# (radius, percent, threshold) for PIL's unsharp mask: a wide, gentle pass lifts
# local contrast in the cloud masses, a tight one puts the edges back after upscaling.
CLARITY_UNSHARP = (30, 22, 2)
DETAIL_UNSHARP = (2.0, 62, 3)

# Strength of the pole smoothing. The fisheye caps already converge on a point, so
# this only has to catch what is left; too high and it softens the zenith for nothing.
POLE_RELAX = 0.35

# Portrait placement on its cube face, as fractions of the face size. A face spans
# 90 degrees, so 0.56 is a 50 degree figure; centring it at 0.44 puts it 5 degrees
# above the horizon. That leaves the top about 4 degrees clear of a default 70
# degree FOV, and keeps the head well above the terrain horizon.
PORTRAIT_HEIGHT = 0.56
PORTRAIT_CENTER_Y = 0.44
# Bottom fraction of the portrait dissolved into the sky. The horizon crosses the
# figure around 61% down, so the whole dissolve stays below it: from the ground it is
# hidden behind terrain, and it only has to hold up when you are flying.
PORTRAIT_FADE = 0.22


def load_sky() -> Image.Image:
    return Image.open(SOURCE_DIR / "sky.webp").convert("RGB")


def match_tone(source: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Shift a cap photo onto the panorama's mean and spread, per channel.

    Without this the zenith photo and the panorama meet at a visible brightness
    step; matched, the cross-fade between them reads as haze.
    """
    src_mean = source.mean(axis=(0, 1))
    src_std = source.std(axis=(0, 1)) + 1e-6
    ref_mean = reference.mean(axis=(0, 1))
    ref_std = reference.std(axis=(0, 1)) + 1e-6
    return (source - src_mean) / src_std * ref_std + ref_mean


def fisheye_cap(photo: np.ndarray, theta: np.ndarray, lon: np.ndarray, extent: float) -> np.ndarray:
    """Sample a photo as a circular fisheye centred on a pole.

    ``theta`` is the angle away from the pole and ``lon`` the azimuth, so every
    column collapses onto the same photo pixel at theta = 0. That is what keeps
    the pole free of the radial streaks a mirrored panorama produces there.
    """
    height, width = photo.shape[:2]
    radius = min(width, height) / 2.0 - 1.0
    r = np.clip(theta / extent, 0.0, 1.0) * radius
    fx = np.clip(width / 2.0 + r * np.sin(lon), 0, width - 1.001)
    fy = np.clip(height / 2.0 - r * np.cos(lon), 0, height - 1.001)

    x0 = fx.astype(np.int64)
    y0 = fy.astype(np.int64)
    tx = (fx - x0)[..., None]
    ty = (fy - y0)[..., None]
    x1 = np.minimum(x0 + 1, width - 1)
    y1 = np.minimum(y0 + 1, height - 1)
    top = photo[y0, x0] * (1 - tx) + photo[y0, x1] * tx
    bottom = photo[y1, x0] * (1 - tx) + photo[y1, x1] * tx
    return top * (1 - ty) + bottom * ty


def _smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def blend_cap(
    equirect: np.ndarray,
    photo: np.ndarray,
    reference: np.ndarray,
    cap_rows: int,
    *,
    nadir: bool,
) -> None:
    """Cross-fade a fisheye cap photo over the pole region of the map, in place."""
    height, width = equirect.shape[:2]
    cap_angle = max(cap_rows, 1) / height * math.pi
    fade_end = min(cap_angle * CAP_FADE_SCALE, math.radians(70.0))
    full = fade_end * 0.35
    rows = int(math.ceil(fade_end / math.pi * height))

    photo = match_tone(photo, reference)
    lon = (np.arange(width, dtype=np.float32) / width) * 2.0 * math.pi
    for i in range(rows):
        row = height - 1 - i if nadir else i
        theta = (i + 0.5) / height * math.pi
        weight = 1.0 - _smoothstep(full, fade_end, np.float32(theta))
        if weight <= 0.001:
            continue
        cap = fisheye_cap(photo, np.full(width, theta, dtype=np.float32), lon, fade_end)
        equirect[row] = equirect[row] * (1.0 - weight) + cap * weight


def best_loop_crop(panorama: Image.Image) -> Image.Image:
    """Trim the panorama to the pair of edges that join up most cleanly.

    The panorama has to meet itself where it wraps, and its two original edges are
    both busy cloud, which a cross-fade can only turn into mush. Giving up a couple
    of hundred columns to find edges that already agree costs far less detail than
    widening the blend until the mismatch stops showing.
    """
    pixels = np.asarray(panorama.convert("RGB"), dtype=np.float32)
    width = pixels.shape[1]
    strip = LOOP_STRIP_PX

    best_cost, best = None, (0, width)
    for left in range(0, LOOP_SEARCH_PX + 1, 4):
        head = pixels[:, left : left + strip]
        for right in range(width - LOOP_SEARCH_PX, width + 1, 4):
            cost = float(np.abs(pixels[:, right - strip : right] - head).mean())
            if best_cost is None or cost < best_cost:
                best_cost, best = cost, (left, right)

    left, right = best
    return panorama.crop((left, 0, right, panorama.height))


def build_equirect(sky: Image.Image, wraps: int) -> np.ndarray:
    """Warp the collage into a seamless equirectangular sky map (H, W, 3) float32."""
    full_panorama = sky.crop(PANORAMA_BOX)
    panorama = best_loop_crop(full_panorama)
    width, height = EQUIRECT_WIDTH, EQUIRECT_HEIGHT
    copy_width = width // wraps

    # Stretch the panorama over its share of the horizon, with SEAM_BLEND_PX of extra
    # width so the right edge can be cross-faded back onto the left edge.
    band_height = int(round(PANORAMA_FOV_DEG[wraps] / 180.0 * height))
    wide = panorama.resize((copy_width + SEAM_BLEND_PX, band_height), Image.LANCZOS)
    band = np.asarray(wide, dtype=np.float32)

    # Overlap blend: copy[x] = lerp(band[copy_width + x], band[x]) across the first
    # SEAM_BLEND_PX columns. copy[0] then equals band[copy_width], the column directly
    # after copy[copy_width - 1] = band[copy_width - 1], so the copy tiles seamlessly
    # against itself and every join between wraps is continuous.
    copy = band[:, :copy_width].copy()
    t = (np.arange(SEAM_BLEND_PX, dtype=np.float32) / SEAM_BLEND_PX)[None, :, None]
    copy[:, :SEAM_BLEND_PX] = band[:, copy_width:] * (1.0 - t) + band[:, :SEAM_BLEND_PX] * t
    del band

    # Roll the joins onto the north and south faces, where the portraits cover them.
    out_band = np.roll(np.tile(copy, (1, wraps, 1)), -(SEAM_BLEND_PX // 2), axis=1)
    del copy

    # Place the band so its horizon sits exactly on the equator of the sphere.
    horizon_in_band = int(round(HORIZON_ROW / panorama.height * band_height))
    top = height // 2 - horizon_in_band
    bottom = top + band_height

    equirect = np.zeros((height, width, 3), dtype=np.float32)
    equirect[top:bottom] = out_band

    # Zenith cap: continue the band upward with a vertical mirror, then converge on
    # the average colour of the topmost row so the pole is a single point.
    if top > 0:
        mirror = out_band[1 : top + 1][::-1]
        if mirror.shape[0] < top:
            mirror = np.concatenate([np.repeat(mirror[:1], top - mirror.shape[0], axis=0), mirror])
        pole = out_band[0].mean(axis=0)[None, None, :]
        w = (np.arange(top, dtype=np.float32) / max(top - 1, 1))[:, None, None]
        equirect[:top] = pole * (1.0 - w) + mirror * w

    # Nadir cap: same trick downward, converging on the cloud deck's average colour.
    if bottom < height:
        n = height - bottom
        mirror = out_band[-n - 1 : -1][::-1]
        if mirror.shape[0] < n:
            mirror = np.concatenate([mirror, np.repeat(mirror[-1:], n - mirror.shape[0], axis=0)])
        pole = out_band[-1].mean(axis=0)[None, None, :]
        w = (np.arange(n, dtype=np.float32) / max(n - 1, 1))[:, None, None]
        equirect[bottom:] = mirror * (1.0 - w) + pole * w

    # Looking straight up and straight down is where a stretched panorama falls
    # apart, so both caps come from dedicated photos instead.
    zenith = np.asarray(sky.crop(ZENITH_BOX), dtype=np.float32)
    blend_cap(equirect, zenith, out_band[:64], top, nadir=False)
    # NADIR_BOX is measured on the uncropped tile, so take it from there.
    nadir = np.asarray(full_panorama.crop(NADIR_BOX), dtype=np.float32)
    blend_cap(equirect, nadir, out_band[-64:], height - bottom, nadir=True)
    del out_band

    return relax_poles(sharpen_sky(equirect))


def sharpen_sky(equirect: np.ndarray) -> np.ndarray:
    """Put back the micro-contrast that upscaling a 2000 px panorama costs.

    Sharpening happens here rather than per face because the map wraps: filtering
    each cube face on its own would leave a bright or dark hairline along every
    cube edge where the kernel ran out of neighbours.
    """
    height, width = equirect.shape[:2]
    pad = 128  # comfortably past the reach of the widest unsharp radius
    wrapped = np.concatenate([equirect[:, width - pad :], equirect, equirect[:, :pad]], axis=1)
    image = Image.fromarray(np.clip(wrapped, 0, 255).astype(np.uint8), "RGB")
    for radius, percent, threshold in (CLARITY_UNSHARP, DETAIL_UNSHARP):
        image = image.filter(ImageFilter.UnsharpMask(radius, percent, threshold))
    return np.asarray(image, dtype=np.float32)[:, pad : pad + width]


def _circular_box_blur(row: np.ndarray, radius: int) -> np.ndarray:
    """Box blur a single equirect row, wrapping around the 360 degree seam."""
    width = row.shape[0]
    span = 2 * radius + 1
    if span >= width:
        return np.repeat(row.mean(axis=0, keepdims=True), width, axis=0)
    extended = np.concatenate([row[width - radius :], row, row[: radius + 1]], axis=0)
    sums = np.concatenate([np.zeros((1, row.shape[1]), dtype=np.float64), np.cumsum(extended, axis=0)])
    return ((sums[span : span + width] - sums[:width]) / span).astype(np.float32)


def relax_poles(equirect: np.ndarray) -> np.ndarray:
    """Remove the radial starburst the poles would otherwise show.

    Near a pole every column of the map collapses onto the same point, so columns
    that disagree in colour turn into streaks. Blurring each row by roughly
    1/sin(theta) pixels keeps detail constant in *sphere* space instead of map
    space: untouched at the horizon, converging on a single colour at the poles.
    """
    height, width = equirect.shape[:2]
    for row in range(height):
        theta = (row + 0.5) / height * math.pi
        radius = int(round((1.0 / max(math.sin(theta), 1e-6) - 1.0) * POLE_RELAX))
        if radius < 1:
            continue
        radius = min(radius, width // 2)
        blurred = _circular_box_blur(equirect[row], radius)
        equirect[row] = _circular_box_blur(blurred, max(1, radius // 2))
    return equirect


# (u, v) in [0,1] with u left->right and v top->bottom of the cell, mapped to a
# Minecraft-space direction (+X east, +Y up, +Z south). Derived from the vertex/UV
# pairs in SquareTexturedSkybox.renderSkybox combined with Utils.MATRIX4F_ROTATED_FACE.
FACE_DIRECTIONS = {
    "bottom": lambda u, v: (2 * u - 1, -np.ones_like(u), 2 * v - 1),
    "top": lambda u, v: (2 * u - 1, np.ones_like(u), 1 - 2 * v),
    "north": lambda u, v: (2 * u - 1, 1 - 2 * v, -np.ones_like(u)),
    "south": lambda u, v: (1 - 2 * u, 1 - 2 * v, np.ones_like(u)),
    "east": lambda u, v: (np.ones_like(u), 1 - 2 * v, 2 * u - 1),
    "west": lambda u, v: (-np.ones_like(u), 1 - 2 * v, 1 - 2 * u),
}


def sample_equirect(equirect: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Bilinear lookup of a direction field in an equirectangular map."""
    height, width = equirect.shape[:2]
    norm = np.sqrt(x * x + y * y + z * z)

    # Azimuth measured from north (-Z) towards east (+X); north lands mid-map.
    lon = (np.arctan2(x, -z) / (2 * math.pi) + 0.5) % 1.0
    lat = np.arccos(np.clip(y / norm, -1.0, 1.0)) / math.pi

    fx = lon * width - 0.5
    fy = np.clip(lat * height - 0.5, 0.0, height - 1.0)

    x0 = np.floor(fx).astype(np.int64)
    y0 = np.floor(fy).astype(np.int64)
    tx = (fx - x0)[..., None]
    ty = (fy - y0)[..., None]
    x0 %= width
    x1 = (x0 + 1) % width
    y1 = np.clip(y0 + 1, 0, height - 1)
    y0 = np.clip(y0, 0, height - 1)

    top = equirect[y0, x0] * (1 - tx) + equirect[y0, x1] * tx
    bottom = equirect[y1, x0] * (1 - tx) + equirect[y1, x1] * tx
    return top * (1 - ty) + bottom * ty


def render_face(equirect: np.ndarray, face: str, size: int) -> Image.Image:
    axis = (np.arange(size, dtype=np.float32) + 0.5) / size
    u, v = np.meshgrid(axis, axis)
    x, y, z = FACE_DIRECTIONS[face](u, v)
    pixels = sample_equirect(equirect, x, y, z)
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), "RGB")


def prepare_portrait(path: Path, size: int) -> Image.Image:
    """Scale a cut-out portrait to the face and dissolve its hard bottom edge."""
    portrait = Image.open(path).convert("RGBA")
    target_h = int(round(size * PORTRAIT_HEIGHT))
    target_w = max(1, int(round(portrait.width * target_h / portrait.height)))
    portrait = portrait.resize((target_w, target_h), Image.LANCZOS)

    alpha = np.asarray(portrait.getchannel("A"), dtype=np.float32) / 255.0
    fade_rows = int(round(target_h * PORTRAIT_FADE))
    if fade_rows > 1:
        ramp = np.linspace(1.0, 0.0, fade_rows, dtype=np.float32)
        # Smoothstep keeps the dissolve from showing a straight edge where it starts.
        ramp = ramp * ramp * (3.0 - 2.0 * ramp)
        alpha[-fade_rows:] *= ramp[:, None]

    portrait.putalpha(Image.fromarray(np.clip(alpha * 255.0, 0, 255).astype(np.uint8), "L"))
    return portrait


def paste_portrait(face: Image.Image, portrait: Image.Image) -> Image.Image:
    size = face.width
    left = (size - portrait.width) // 2
    top = int(round(size * PORTRAIT_CENTER_Y - portrait.height / 2))
    canvas = face.convert("RGBA")
    canvas.alpha_composite(portrait, (left, top))
    return canvas.convert("RGB")


def build_atlas(face_size: int, wraps: int) -> tuple[Image.Image, dict[str, Image.Image]]:
    equirect = build_equirect(load_sky(), wraps)

    faces = {name: render_face(equirect, name, face_size) for name in FACE_DIRECTIONS}
    del equirect
    faces["north"] = paste_portrait(faces["north"], prepare_portrait(SOURCE_DIR / "front.webp", face_size))
    faces["south"] = paste_portrait(faces["south"], prepare_portrait(SOURCE_DIR / "back.webp", face_size))

    layout = {
        "bottom": (0, 0),
        "top": (1, 0),
        "south": (2, 0),
        "west": (0, 1),
        "north": (1, 1),
        "east": (2, 1),
    }
    atlas = Image.new("RGB", (face_size * 3, face_size * 2))
    for name, (col, row) in layout.items():
        atlas.paste(faces[name], (col * face_size, row * face_size))
    return atlas, faces


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--face-size", type=int, default=2048, help="pixels per cube face (default: 2048)")
    parser.add_argument(
        "--wraps",
        type=int,
        default=2,
        choices=sorted(PANORAMA_FOV_DEG),
        help="times the panorama repeats around the horizon; 2 is twice as sharp (default: 2)",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="atlas output path")
    parser.add_argument("--preview-dir", type=Path, default=None, help="also write the individual faces here")
    args = parser.parse_args()

    atlas, faces = build_atlas(args.face_size, args.wraps)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(args.out, optimize=True)
    print(f"wrote {args.out} ({atlas.width}x{atlas.height}, {args.out.stat().st_size / 1e6:.1f} MB)")

    # Only refresh the pack icon when writing the pack itself, not a scratch render.
    if args.out == DEFAULT_OUT:
        icon_path = DEFAULT_OUT.parents[3] / "pack.png"
        faces["north"].resize((128, 128), Image.LANCZOS).save(icon_path, optimize=True)
        print(f"wrote {icon_path}")

    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        for name, image in faces.items():
            image.save(args.preview_dir / f"{name}.png")
        print(f"wrote face previews to {args.preview_dir}")


if __name__ == "__main__":
    main()
