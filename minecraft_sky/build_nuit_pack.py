#!/usr/bin/env python3
"""Build a Nuit (formerly FabricSkyBoxes) resource pack from a sky concept.

Nuit's square-textured skybox reads all six cube faces from one 3x2 atlas,
laid out bottom|top|south over west|north|east. test_nuit_atlas.py checks
that layout and each face's orientation against the mod's own renderer.

The skybox carries no `rotation` block on purpose: Nuit only applies a
rotation when you give it mapping/axis keyframes, and leaving it out keeps
the sky fixed to the world so the horizon glow stays on the horizon
instead of wheeling through it.

Usage:
    python3 build_nuit_pack.py shattered
    python3 build_nuit_pack.py shattered --face-size 2048 --pack-format 55
"""

from __future__ import annotations

import argparse
import json
import os
import shutil

import numpy as np
from PIL import Image

import sky_generator as sg

# Minecraft day: 0 is sunrise, 12000 sunset, 18000 midnight. Hold the sky at
# full strength through the night and fade it out over dusk and dawn.
NIGHT_KEYFRAMES = {
    "0": 0.0,
    "11800": 0.0,
    "13200": 1.0,
    "22200": 1.0,
    "23400": 0.0,
}


def build(concept, out_dir, width=4096, face_size=1024, pack_format=46,
          asset_name=None):
    cfg = sg.CONCEPTS[concept]
    asset_name = asset_name or concept

    print(f"rendering {concept} at {width}x{width // 2} ...", flush=True)
    hdr = sg.render_panorama(cfg, width, width // 2)
    sg.add_stars(hdr, cfg)
    sg.add_embers(hdr, cfg)

    print(f"projecting {face_size}px cube faces into a "
          f"{sg.ATLAS_COLS * face_size}x{sg.ATLAS_ROWS * face_size} atlas ...",
          flush=True)
    atlas = sg.to_image(sg.cube_atlas(hdr, face_size), cfg, cfg["seed"] + 2)

    pack = os.path.join(out_dir, f"nuit_{asset_name}")
    sky = os.path.join(pack, "assets", "nuit", "sky")
    if os.path.isdir(pack):
        shutil.rmtree(pack)
    os.makedirs(sky)

    atlas.save(os.path.join(sky, f"{asset_name}.png"))

    skybox = {
        "schemaVersion": 1,
        "type": "square-textured",
        "properties": {
            "fade": {"keyFrames": NIGHT_KEYFRAMES},
        },
        "texture": f"nuit:sky/{asset_name}.png",
    }
    with open(os.path.join(sky, f"{asset_name}.json"), "w") as fh:
        json.dump(skybox, fh, indent=2)

    mcmeta = {
        "pack": {
            "pack_format": pack_format,
            # honoured from 1.20.2 on, and ignored as an unknown field
            # before that, so the pack stays loadable either way
            "supported_formats": {"min_inclusive": 15, "max_inclusive": 99},
            "description": f"{cfg['title']} - dark fantasy night sky (Nuit)",
        }
    }
    with open(os.path.join(pack, "pack.mcmeta"), "w") as fh:
        json.dump(mcmeta, fh, indent=2)

    archive = shutil.make_archive(pack, "zip", root_dir=pack)
    print(f"wrote {archive} ({os.path.getsize(archive) / 1e6:.1f} MB)")
    return archive


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("concept", choices=list(sg.CONCEPTS))
    ap.add_argument("--width", type=int, default=4096,
                    help="panorama width the faces are projected from")
    ap.add_argument("--face-size", type=int, default=1024)
    ap.add_argument("--pack-format", type=int, default=46,
                    help="resource pack format for the target Minecraft")
    ap.add_argument("--name", default=None, help="asset name inside the pack")
    ap.add_argument("--out", default=os.path.join(sg.ROOT, "packs"))
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    build(args.concept, args.out, width=args.width, face_size=args.face_size,
          pack_format=args.pack_format, asset_name=args.name)


if __name__ == "__main__":
    main()
