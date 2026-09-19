#!/usr/bin/env python3
"""Render what the MadisonBeerSky skybox looks like in game, without launching Minecraft.

This deliberately re-implements Nuit's renderer rather than reusing anything from
``build_skybox.py``: the quad, the UV ranges and the per-face matrices are ported
straight from ``SquareTexturedSkybox.renderSkybox`` and ``Utils`` (tag
``mc1.21.11-1.0.0-beta.6``). If the atlas were laid out wrongly, these previews
would show it as a rotated, mirrored or misplaced face.

Usage:  python3 preview.py [--atlas <path.png>] [--out-dir <dir>] [--fov 70]
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ATLAS = REPO_ROOT / "minecraft" / "MadisonBeerSky" / "assets" / "nuit" / "sky" / "madison_beer_sky.png"

# Utils.TEXTURE_FACES: (minU, minV, maxU, maxV) per face id.
TEXTURE_FACES = [
    (0.0, 0.0, 1 / 3, 1 / 2),  # 0 bottom
    (1 / 3, 1 / 2, 2 / 3, 1.0),  # 1 north
    (2 / 3, 0.0, 1.0, 1 / 2),  # 2 south
    (1 / 3, 0.0, 2 / 3, 1 / 2),  # 3 top
    (2 / 3, 1 / 2, 1.0, 1.0),  # 4 east
    (0.0, 1 / 2, 1 / 3, 1.0),  # 5 west
]
FACE_NAMES = ["bottom", "north", "south", "top", "east", "west"]

VIEWS = {
    "north": (0.0, -1.0),
    "east": (1.0, 0.0),
    "south": (0.0, 1.0),
    "west": (-1.0, 0.0),
}


def _rx(deg: float) -> np.ndarray:
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=np.float64)


def _ry(deg: float) -> np.ndarray:
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=np.float64)


def _rz(deg: float) -> np.ndarray:
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)


# Utils.MATRIX4F_ROTATED_FACE, in the same order as TEXTURE_FACES.
FACE_MATRICES = [
    np.eye(3),
    _rx(90.0),
    _rx(-90.0) @ _ry(180.0),
    _rx(180.0),
    _rz(90.0) @ _ry(-90.0),
    _rz(-90.0) @ _ry(90.0),
]


def face_samples(atlas: np.ndarray, face: int, steps: int) -> tuple[np.ndarray, np.ndarray]:
    """Points on one cube face plus their atlas colour, following the mod's quad."""
    height, width = atlas.shape[:2]
    min_u, min_v, max_u, max_v = TEXTURE_FACES[face]
    a, b = np.meshgrid(np.linspace(0, 1, steps), np.linspace(0, 1, steps))

    # The quad the renderer emits: the y = -100 plane, before the face matrix.
    local = np.stack([-1 + 2 * a, -np.ones_like(a), -1 + 2 * b], axis=-1)
    points = local.reshape(-1, 3) @ FACE_MATRICES[face].T

    u = np.clip((min_u + a * (max_u - min_u)) * width, 0, width - 1).astype(np.int64)
    v = np.clip((min_v + b * (max_v - min_v)) * height, 0, height - 1).astype(np.int64)
    return points, atlas[v.ravel(), u.ravel()]


def render(atlas: np.ndarray, forward: np.ndarray, size: int, fov: float, steps: int) -> Image.Image:
    """Perspective view with Minecraft's framing: 16:9, and `fov` measured vertically."""
    height = size
    width = int(round(size * 16 / 9))

    up_world = np.array([0.0, 1.0, 0.0])
    forward = forward / np.linalg.norm(forward)
    if abs(forward @ up_world) > 0.999:
        up_world = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, up_world)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)

    focal = (height / 2) / math.tan(math.radians(fov) / 2)
    canvas = np.zeros((height, width, 3), dtype=np.uint8)

    for face in range(6):
        points, colors = face_samples(atlas, face, steps)
        depth = points @ forward
        visible = depth > 1e-6
        if not visible.any():
            continue
        points, colors, depth = points[visible], colors[visible], depth[visible]
        px = (width / 2 + (points @ right) / depth * focal).astype(np.int64)
        py = (height / 2 - (points @ up) / depth * focal).astype(np.int64)
        inside = (px >= 0) & (px < width) & (py >= 0) & (py < height)
        canvas[py[inside], px[inside]] = colors[inside]

    return Image.fromarray(canvas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--out-dir", type=Path, default=Path("skybox-preview"))
    parser.add_argument("--size", type=int, default=512, help="preview resolution (default: 512)")
    parser.add_argument("--fov", type=float, default=70.0, help="vertical field of view (default: 70)")
    parser.add_argument("--steps", type=int, default=1400, help="samples per face axis (default: 1400)")
    args = parser.parse_args()

    atlas = np.asarray(Image.open(args.atlas).convert("RGB"))
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for name, (x, z) in VIEWS.items():
        image = render(atlas, np.array([x, 0.0, z]), args.size, args.fov, args.steps)
        image.save(args.out_dir / f"looking-{name}.png")
    render(atlas, np.array([0.0, 1.0, 0.0]), args.size, args.fov, args.steps).save(args.out_dir / "looking-up.png")
    print(f"wrote previews to {args.out_dir}")


if __name__ == "__main__":
    main()
