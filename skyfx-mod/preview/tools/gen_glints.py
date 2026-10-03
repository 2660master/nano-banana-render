"""Generates the tileable 512x512 glint textures for the SkyFX glint packs (galaxy, rainbow, ice, summer).

The glint is blended additively, so black = no glint and bright = glint colour. Every texture tiles seamlessly
(all noise is built in the frequency domain or from integer-frequency waves).

    python3 preview/tools/gen_glints.py
"""
import os
import numpy as np
from PIL import Image

N = 512
HERE = os.path.dirname(os.path.abspath(__file__))
PACKS = os.path.join(HERE, '..', '..', 'src', 'client', 'resources', 'resourcepacks')
rng = np.random.default_rng(1337)
yy, xx = np.mgrid[0:N, 0:N] / N  # 0..1, periodic


def noise(beta, seed):
    """Periodic fractal noise with a 1/f^beta spectrum, normalised to 0..1."""
    r = np.random.default_rng(seed)
    f = np.fft.fftfreq(N)[:, None] ** 2 + np.fft.fftfreq(N)[None, :] ** 2
    f[0, 0] = 1
    spec = (r.normal(size=(N, N)) + 1j * r.normal(size=(N, N))) / f ** (beta / 2)
    spec[0, 0] = 0
    n = np.real(np.fft.ifft2(spec))
    return (n - n.min()) / (n.max() - n.min())


def stars(count, seed, size=1.0, bright=1.0):
    """Wrapped soft star dots."""
    r = np.random.default_rng(seed)
    img = np.zeros((N, N))
    for _ in range(count):
        cx, cy = r.uniform(0, 1, 2)
        s = size * r.uniform(0.5, 1.6) / N
        b = bright * r.uniform(0.3, 1.0) ** 2
        dx = (xx - cx + 0.5) % 1 - 0.5
        dy = (yy - cy + 0.5) % 1 - 0.5
        img += b * np.exp(-(dx * dx + dy * dy) / (2 * s * s))
    return img


def sparkle(count, seed, length=10.0):
    """Four-point sparkles (a dot with a thin cross)."""
    r = np.random.default_rng(seed)
    img = np.zeros((N, N))
    for _ in range(count):
        cx, cy = r.uniform(0, 1, 2)
        b = r.uniform(0.5, 1.0)
        dx = np.abs((xx - cx + 0.5) % 1 - 0.5) * N
        dy = np.abs((yy - cy + 0.5) % 1 - 0.5) * N
        core = np.exp(-(dx * dx + dy * dy) / 3.0)
        cross = np.exp(-dy * dy / 0.8) * np.exp(-dx / length) + np.exp(-dx * dx / 0.8) * np.exp(-dy / length)
        img += b * (core + 0.7 * cross)
    return img


def hsv(h, s, v):
    h = (h % 1.0) * 6
    i = np.floor(h)
    f = h - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    i = i.astype(int) % 6
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)


def save(rgb, pack, description):
    rgb = np.clip(rgb, 0, 1)
    img = Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), 'RGB').convert('RGBA')
    tex = os.path.join(PACKS, pack, 'assets', 'minecraft', 'textures', 'misc')
    os.makedirs(tex, exist_ok=True)
    for name in ('enchanted_glint_item.png', 'enchanted_glint_armor.png'):
        img.save(os.path.join(tex, name), optimize=True)
    with open(os.path.join(PACKS, pack, 'pack.mcmeta'), 'w') as f:
        f.write('{\n\t"pack": {\n\t\t"description": "%s",\n\t\t"min_format": 75,\n\t\t"max_format": 75\n\t}\n}\n' % description)
    preview = os.path.join(HERE, '..', 'textures', pack + '.png')
    img.resize((256, 256), Image.LANCZOS).save(preview, optimize=True)
    print('wrote', pack)


# galaxy: purple / pink / blue nebula clouds with dust lanes and lots of stars
n1, n2, n3 = noise(2.6, 1), noise(2.2, 2), noise(3.0, 3)
ridge = 1 - np.abs(2 * noise(2.4, 4) - 1)
neb = np.clip((n1 - 0.35) * 2.2, 0, 1) ** 1.6
col = (neb[..., None] * np.array([0.55, 0.18, 0.95])
       + (np.clip((n2 - 0.5) * 2.5, 0, 1) ** 2)[..., None] * np.array([0.95, 0.30, 0.75])
       + (ridge ** 6 * n3)[..., None] * np.array([0.25, 0.55, 1.0]))
col *= (0.55 + 0.45 * n3)[..., None]
st = stars(380, 5, 0.9) + stars(40, 6, 1.6, 1.4) + sparkle(14, 7, 9)
col += st[..., None] * np.array([0.95, 0.92, 1.0])
save(col * 1.3, 'galaxy_glint', 'SkyFX - Galaxy enchantment glint')

# rainbow (a soft, flowing holographic shimmer, not flag stripes): hue drifts smoothly across the texture with
# wavy pastel-to-vivid bands, a satin sheen and sparkles
warp = (noise(3.2, 11) - 0.5) * 0.18 + 0.05 * np.sin(2 * np.pi * (2 * yy - xx))
hue = (xx + yy + warp) % 1.0
sat = 0.62 + 0.25 * noise(3.0, 12)
sheen = 0.5 + 0.5 * np.sin(2 * np.pi * (4 * xx - 3 * yy + noise(3.0, 13) * 0.8))
val = 0.45 + 0.40 * sheen ** 3
col = hsv(hue, sat, val)
col += sparkle(26, 14, 8)[..., None] * 0.9
save(col * 0.85, 'rainbow_glint', 'SkyFX - Holographic rainbow enchantment glint')

# ice blue: frosty crystal cracks and frozen shimmer in icy blues and white
cells = np.zeros((N, N)) + 9
pts = rng.uniform(0, 1, (140, 2))
second = np.zeros((N, N)) + 9
for px, py in pts:
    dx = (xx - px + 0.5) % 1 - 0.5
    dy = (yy - py + 0.5) % 1 - 0.5
    d = np.sqrt(dx * dx + dy * dy)
    second = np.where(d < cells, cells, np.minimum(second, d))
    cells = np.minimum(cells, d)
cracks = np.exp(-((second - cells) * N) ** 2 / 2.5) * np.clip((noise(2.0, 25) - 0.25) * 2.2, 0, 1)
frost = noise(1.8, 21)
col = (cracks[..., None] * np.array([0.65, 0.92, 1.0]) * (0.6 + 0.4 * frost)[..., None]
       + (np.clip((noise(2.6, 22) - 0.45) * 2.0, 0, 1) ** 2)[..., None] * np.array([0.10, 0.45, 0.95])
       + (frost ** 4)[..., None] * np.array([0.35, 0.70, 1.0]) * 0.5)
col += (sparkle(30, 23, 11) + stars(120, 24, 0.8))[..., None] * np.array([0.85, 0.97, 1.0])
save(col * 0.9, 'ice_glint', 'SkyFX - Ice blue enchantment glint')

# summer: warm sunset waves (mango, coral, pink) with turquoise sea ripples, a few little suns and sparkles
w = noise(2.7, 31)
band = (yy + 0.12 * np.sin(2 * np.pi * xx * 2) + (w - 0.5) * 0.25) % 1.0
palette = np.array([[1.00, 0.62, 0.10], [1.00, 0.36, 0.38], [1.00, 0.30, 0.62], [1.00, 0.85, 0.20], [0.10, 0.85, 0.80]])
k = band * len(palette)
i0 = np.floor(k).astype(int) % len(palette)
i1 = (i0 + 1) % len(palette)
t = (k - np.floor(k))[..., None]
t = t * t * (3 - 2 * t)
col = palette[i0] * (1 - t) + palette[i1] * t
ripple = 0.5 + 0.5 * np.sin(2 * np.pi * (6 * yy + 3 * xx) + w * 6)
col *= (0.55 + 0.40 * ripple ** 2)[..., None]
suns = np.zeros((N, N))
for sx, sy in rng.uniform(0, 1, (5, 2)):
    dx = (xx - sx + 0.5) % 1 - 0.5
    dy = (yy - sy + 0.5) % 1 - 0.5
    d = np.sqrt(dx * dx + dy * dy) * N
    ang = np.arctan2(dy, dx)
    suns += np.clip(1.0 - (d - 9) / 1.5, 0, 1) + np.clip(np.cos(ang * 8) * 0.5 + 0.5, 0, 1) ** 6 * np.exp(-((d - 16) / 4) ** 2)
col += suns[..., None] * np.array([1.0, 0.86, 0.30])
col += sparkle(18, 33, 8)[..., None] * np.array([1.0, 0.95, 0.80])
save(col, 'summer_glint', 'SkyFX - Summer colours enchantment glint')
