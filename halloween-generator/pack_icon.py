"""pack.png icons: a jack-o'-lantern for the glint pack, the Watcher's eye for the sky pack.

    python3 pack_icon.py ../halloween-glint/pack.png pumpkin
    python3 pack_icon.py ../halloween-sky/pack.png   eye
"""
import sys
import numpy as np
from PIL import Image
from skylib import pumpkin_sprite

S = 512


def _bg(inner, outer, tight=1.05, gain=1.45):
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.sqrt(((xx - S / 2) / (S / 2)) ** 2 + ((yy - S * 0.56) / (S / 2)) ** 2)
    bg = np.zeros((S, S, 3))
    bg += np.array(outer) * np.clip(1 - r * 0.5, 0, 1)[..., None]
    bg += np.array(inner) * np.clip(1 - r * tight, 0, 1)[..., None] ** 2 * gain
    return bg + np.array(outer) * 0.6


def _paste(bg, spr, gl, cy=0.52, glow_gain=1.7, body_gain=1.10):
    h, w = spr.shape[:2]
    y0 = int(S * cy - h / 2); x0 = int(S * 0.5 - w / 2)
    sl = (slice(max(y0, 0), min(y0 + h, S)), slice(max(x0, 0), min(x0 + w, S)))
    sub = spr[max(-y0, 0):h - max(y0 + h - S, 0), max(-x0, 0):w - max(x0 + w - S, 0)]
    a = sub[..., 3:4] / 255.0
    bg[sl] = bg[sl] * (1 - a) + sub[..., :3] / 255.0 * a * body_gain
    if gl is not None:
        gsub = gl[max(-y0, 0):h - max(y0 + h - S, 0), max(-x0, 0):w - max(x0 + w - S, 0)]
        bg[sl] += gsub[..., :3] / 255.0 * (gsub[..., 3:4] / 255.0) * glow_gain
    return bg


def _save(bg, path, k=0.10):
    x = np.clip(bg, 0, None)
    L = x @ np.array([0.2126, 0.7152, 0.0722])
    x = x * (L / (1 + L * k) / np.maximum(L, 1e-6))[..., None]
    Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8)) \
         .resize((128, 128), Image.LANCZOS).save(path, optimize=True)


if __name__ == "__main__":
    out = sys.argv[1]
    kind = sys.argv[2] if len(sys.argv) > 2 else "pumpkin"
    if kind == "eye":
        from scary import watcher_sprite
        spr, gl = watcher_sprite(int(S * 0.92))
        bg = _bg((0.42, 0.14, 0.05), (0.030, 0.014, 0.048), tight=0.95, gain=1.15)
        bg = _paste(bg, spr, gl, cy=0.50, glow_gain=1.25, body_gain=1.0)
    else:
        spr, gl = pumpkin_sprite(int(S * 0.80), body=(228, 116, 26), dark=(126, 50, 10),
                                 rim=(255, 176, 78), glowcol=(255, 236, 168), halo=(255, 122, 24),
                                 face_style=0)
        bg = _bg((1.00, 0.36, 0.05), (0.035, 0.012, 0.055))
        bg = _paste(bg, spr, gl)
    _save(bg, out)
    print(f"{kind} icon -> {out}")
