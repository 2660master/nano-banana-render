"""128x128 pack.png: a jack-o'-lantern on a dark halloween glow."""
import sys
import numpy as np
from PIL import Image
from skylib import pumpkin_sprite

S = 512
yy, xx = np.mgrid[0:S, 0:S]
r = np.sqrt(((xx - S / 2) / (S / 2)) ** 2 + ((yy - S * 0.56) / (S / 2)) ** 2)
bg = np.zeros((S, S, 3))
bg += np.array([0.055, 0.020, 0.075]) * np.clip(1 - r * 0.5, 0, 1)[..., None]
bg += np.array([1.00, 0.36, 0.05]) * np.clip(1 - r * 1.05, 0, 1)[..., None] ** 2 * 1.45
bg += np.array([0.035, 0.012, 0.055])
spr, gl = pumpkin_sprite(int(S * 0.80), body=(228, 116, 26), dark=(126, 50, 10),
                         rim=(255, 176, 78), glowcol=(255, 236, 168), halo=(255, 122, 24),
                         face_style=0)
h, w = spr.shape[:2]
y0 = int(S * 0.52 - h / 2); x0 = int(S * 0.5 - w / 2)
sl = (slice(max(y0, 0), min(y0 + h, S)), slice(max(x0, 0), min(x0 + w, S)))
sub = spr[max(-y0, 0):h - max(y0 + h - S, 0), max(-x0, 0):w - max(x0 + w - S, 0)]
gsub = gl[max(-y0, 0):h - max(y0 + h - S, 0), max(-x0, 0):w - max(x0 + w - S, 0)]
a = sub[..., 3:4] / 255.0
bg[sl] = bg[sl] * (1 - a) + sub[..., :3] / 255.0 * a * 1.10
bg[sl] += gsub[..., :3] / 255.0 * (gsub[..., 3:4] / 255.0) * 1.7    # glow sits on top
x = np.clip(bg, 0, None)
L = x @ np.array([0.2126, 0.7152, 0.0722])
x = x * (L / (1 + L * 0.10) / np.maximum(L, 1e-6))[..., None]
img = Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8)).resize((128, 128), Image.LANCZOS)
img.save(sys.argv[1], optimize=True)
print("pack.png written")
