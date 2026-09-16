"""Orange pumpkin enchantment glint for Minecraft (additive, seamlessly tiling).

Vanilla applies the glint texture through a scrolling texture matrix:
  * items        -> texture matrix scale 8.0   (tile repeats 8x over the sprite)
  * worn armour  -> texture matrix scale 0.16  (only ~2% of the sheet covers a chestplate)
So the two sheets need very different element sizes to read well in game.
"""
import numpy as np
from PIL import Image, ImageFilter
from skylib import pumpkin_sprite


def periodic_streaks(S, freq, spread, angle_deg, aniso, seed):
    rng = np.random.default_rng(seed)
    F = np.fft.fft2(rng.normal(size=(S, S)))
    fy = np.fft.fftfreq(S)[:, None] * S
    fx = np.fft.fftfreq(S)[None, :] * S
    r = np.sqrt(fx ** 2 + fy ** 2) + 1e-9
    a = np.radians(angle_deg + 90.0)
    proj = (fx * np.cos(a) + fy * np.sin(a)) / r
    out = np.real(np.fft.ifft2(F * np.exp(-((r - freq) / spread) ** 2) *
                               np.exp(-((1.0 - np.abs(proj)) * aniso) ** 2)))
    out -= out.min()
    return out / max(out.max(), 1e-9)


def wrap_add(dst, spr, cx, cy, gain=1.0):
    S = dst.shape[0]
    h, w = spr.shape[:2]
    ys = (np.arange(h) + int(cy) - h // 2) % S
    xs = (np.arange(w) + int(cx) - w // 2) % S
    a = spr[..., 3:4] / 255.0
    dst[np.ix_(ys, xs)] += spr[..., :3] / 255.0 * a * gain


def periodic_blur(img, px):
    S = img.shape[0]
    big = np.tile(img, (3, 3, 1))
    im = Image.fromarray(np.clip(big * 255, 0, 255).astype(np.uint8))
    im = im.filter(ImageFilter.GaussianBlur(px))
    return np.asarray(im).astype(np.float64)[S:2 * S, S:2 * S] / 255.0


def rot(spr, deg):
    if not deg:
        return spr
    return np.asarray(Image.fromarray(spr.astype(np.uint8)).rotate(
        deg, resample=Image.BICUBIC, expand=False)).astype(np.float64)


def make_variants(sizes, rots=(0, 9, -9, 18), pad=1.25):
    """Pre-render (sprite, glow) pumpkin variants so big fields stay cheap."""
    out = []
    for s in sizes:
        for style in range(3):
            spr, gl = pumpkin_sprite(int(s * pad), body=(255, 126, 22), dark=(148, 44, 0),
                                     rim=(255, 206, 120), glowcol=(255, 240, 186),
                                     halo=(255, 132, 28), face_style=style, stem=(156, 200, 74))
            for r in rots:
                out.append((rot(spr, r), rot(gl, r)))
    return out


def build(S, placements, streak_cfg, base, glow_px, glow_gain, blur_gain=0.45, level=1.0):
    rgb = np.zeros((S, S, 3)) + np.array(base)
    for freq, spread, ang, aniso, gain, lo, hi, col in streak_cfg:
        f = periodic_streaks(S, freq, spread, ang, aniso, int(freq * 7) + 13)
        t = np.clip((f - lo) / (hi - lo), 0, 1)
        t = t * t * (3 - 2 * t)
        rgb += np.array(col) * (t ** 1.35)[..., None] * gain
    body = np.zeros((S, S, 3))
    halo = np.zeros((S, S, 3))
    for fx, fy, (spr, gl) in placements:
        wrap_add(body, spr, fx * S, fy * S)
        wrap_add(halo, gl, fx * S, fy * S, gain=0.55)
    rgb += halo * glow_gain
    rgb += periodic_blur(body, glow_px) * blur_gain
    rgb += body
    return np.clip(rgb * level, 0, 1)


def item_glint(S=256):
    streaks = [
        (7.0, 3.0, 22.0, 2.6, 0.55, 0.42, 0.88, (1.00, 0.40, 0.045)),
        (15.0, 5.0, 18.0, 2.2, 0.32, 0.55, 0.95, (1.00, 0.50, 0.07)),
        (30.0, 9.0, 26.0, 1.8, 0.12, 0.62, 1.00, (1.00, 0.66, 0.20)),
    ]
    v = make_variants([116, 132, 104, 76], rots=(-8, 6, -14, 12))
    pk = [(0.22, 0.26, v[1]), (0.70, 0.56, v[4 * 3 + 5]), (0.44, 0.84, v[4 * 6 + 10]),
          (0.90, 0.10, v[4 * 9 + 1])]
    return build(S, pk, streaks, (0.030, 0.009, 0.001), S * 0.055, 0.85, level=0.86)


def armor_glint(S=2048):
    """Worn armour only shows ~2% of the sheet, so keep the lanterns ~1.7% wide."""
    streaks = [
        (26.0, 10.0, 20.0, 2.6, 0.34, 0.40, 0.92, (1.00, 0.38, 0.040)),
        (70.0, 22.0, 16.0, 2.2, 0.22, 0.55, 0.97, (1.00, 0.56, 0.11)),
        (150.0, 40.0, 24.0, 1.8, 0.11, 0.64, 1.00, (1.00, 0.76, 0.32)),
    ]
    v = make_variants([30, 34, 38], rots=(0, 10, -10, 20, -20, 6))
    rng = np.random.default_rng(3)
    n = 54
    step = 1.0 / n
    pk = []
    for iy in range(n):
        for ix in range(n):
            if rng.random() < 0.10:
                continue
            fx = ((ix + 0.5 + (0.5 if iy % 2 else 0.0)) * step + rng.uniform(-0.006, 0.006)) % 1.0
            fy = ((iy + 0.5) * step + rng.uniform(-0.005, 0.005)) % 1.0
            pk.append((fx, fy, v[rng.integers(0, len(v))]))
    return build(S, pk, streaks, (0.060, 0.017, 0.002), S * 0.006, 0.75,
                 blur_gain=0.55, level=0.95)


def save(arr, path, final=None):
    im = Image.fromarray((arr * 255 + 0.5).astype(np.uint8))
    if final and final != im.width:
        im = im.resize((final, final), Image.LANCZOS)   # supersampled -> crisp small shapes
    im.save(path, optimize=True)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    a = item_glint(); save(a, f"{out}/enchanted_glint_item.png")
    b = armor_glint(); save(b, f"{out}/enchanted_glint_armor.png", final=1024)
    print("item ", a.shape, "mean %.3f" % a.mean(), "| armor", b.shape, "mean %.3f" % b.mean())
