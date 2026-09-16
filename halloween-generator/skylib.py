"""Procedural sky renderer for Minecraft skyboxes (Nuit square-textured, 3x2 grid)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------- noise ----
def _hash3(ix, iy, iz, seed):
    h = (ix.astype(np.int64) * np.int64(73856093)) ^ \
        (iy.astype(np.int64) * np.int64(19349663)) ^ \
        (iz.astype(np.int64) * np.int64(83492791)) ^ np.int64(seed * 2654435761 + 12345)
    h = h.astype(np.uint64)
    h ^= h >> np.uint64(33); h *= np.uint64(0xff51afd7ed558ccd)
    h ^= h >> np.uint64(33); h *= np.uint64(0xc4ceb9fe1a85ec53)
    h ^= h >> np.uint64(33)
    return (h >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def vnoise3(p, seed=0):
    i = np.floor(p)
    f = p - i
    f = f * f * (3.0 - 2.0 * f)
    ix = i[..., 0]; iy = i[..., 1]; iz = i[..., 2]
    fx = f[..., 0]; fy = f[..., 1]; fz = f[..., 2]
    o = np.zeros_like(ix)
    one = o + 1.0
    def H(dx, dy, dz):
        return _hash3(ix + dx, iy + dy, iz + dz, seed)
    c00 = H(o, o, o) * (1 - fx) + H(one, o, o) * fx
    c10 = H(o, one, o) * (1 - fx) + H(one, one, o) * fx
    c01 = H(o, o, one) * (1 - fx) + H(one, o, one) * fx
    c11 = H(o, one, one) * (1 - fx) + H(one, one, one) * fx
    c0 = c00 * (1 - fy) + c10 * fy
    c1 = c01 * (1 - fy) + c11 * fy
    return c0 * (1 - fz) + c1 * fz


def fbm3(p, octaves=5, lac=2.02, gain=0.5, seed=0):
    total = np.zeros(p.shape[:-1]); amp = 0.5; freq = 1.0; norm = 0.0
    for o in range(octaves):
        total += amp * vnoise3(p * freq, seed + o * 37)
        norm += amp
        amp *= gain; freq *= lac
    return total / norm


def ridged(p, octaves=5, lac=2.05, gain=0.5, seed=0):
    total = np.zeros(p.shape[:-1]); amp = 0.5; freq = 1.0; norm = 0.0
    for o in range(octaves):
        n = 1.0 - np.abs(vnoise3(p * freq, seed + o * 53) * 2.0 - 1.0)
        total += amp * n * n
        norm += amp
        amp *= gain; freq *= lac
    return total / norm


# ---------------------------------------------------------------- stars ----
def starfield(d, cells=64.0, prob=0.08, radius=0.10, seed=3, warm=0.0, bright=1.0):
    """Procedural seamless star field over direction vectors. Returns (H,W,3) additive."""
    p = d * cells
    i = np.floor(p)
    f = p - i
    ix = i[..., 0].astype(np.int64); iy = i[..., 1].astype(np.int64); iz = i[..., 2].astype(np.int64)
    r0 = _hash3(ix, iy, iz, seed)
    has = r0 < prob
    jx = _hash3(ix, iy, iz, seed + 101) * 0.6 + 0.2
    jy = _hash3(ix, iy, iz, seed + 202) * 0.6 + 0.2
    jz = _hash3(ix, iy, iz, seed + 303) * 0.6 + 0.2
    mag = _hash3(ix, iy, iz, seed + 404)
    tint = _hash3(ix, iy, iz, seed + 505)
    dist = np.sqrt((f[..., 0] - jx) ** 2 + (f[..., 1] - jy) ** 2 + (f[..., 2] - jz) ** 2)
    rad = radius * (0.45 + 0.95 * mag ** 2)
    v = np.exp(-(dist / np.maximum(rad, 1e-6)) ** 2 * 3.2)
    v = np.where(has, v, 0.0) * (0.25 + 0.95 * mag ** 2) * bright
    col = np.stack([
        v * (1.0 + 0.30 * warm * tint),
        v * (0.96 - 0.10 * tint - 0.18 * warm * tint),
        v * (0.92 - 0.30 * tint + 0.25 * (1 - warm) * (1 - tint)),
    ], axis=-1)
    return np.clip(col, 0.0, None)


# ------------------------------------------------------------ projection ---
FACES = {
    #            corner(u0,v0)        corner(u0,v1)       corner(u1,v1)       corner(u1,v0)
    "bottom": ((-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1)),
    "north":  ((-1, 1, -1), (-1, -1, -1), (1, -1, -1), (1, 1, -1)),
    "south":  ((1, 1, 1), (1, -1, 1), (-1, -1, 1), (-1, 1, 1)),
    "top":    ((-1, 1, 1), (-1, 1, -1), (1, 1, -1), (1, 1, 1)),
    "east":   ((1, 1, -1), (1, -1, -1), (1, -1, 1), (1, 1, 1)),
    "west":   ((-1, 1, 1), (-1, -1, 1), (-1, -1, -1), (-1, 1, -1)),
}
# grid position (col,row) in the 3x2 sheet
FACE_GRID = {"bottom": (0, 0), "top": (1, 0), "south": (2, 0),
             "west": (0, 1), "north": (1, 1), "east": (2, 1)}


def face_dirs(face, size):
    c00, c01, c11, c10 = (np.array(c, dtype=np.float64) for c in FACES[face])
    u = (np.arange(size) + 0.5) / size
    v = (np.arange(size) + 0.5) / size
    uu, vv = np.meshgrid(u, v)
    uu = uu[..., None]; vv = vv[..., None]
    p = (c00 * (1 - uu) * (1 - vv) + c10 * uu * (1 - vv) +
         c01 * (1 - uu) * vv + c11 * uu * vv)
    return p / np.linalg.norm(p, axis=-1, keepdims=True)


def equirect_dirs(w, h, lon_offset=0.0):
    lon = (np.arange(w) + 0.5) / w * 2 * np.pi + lon_offset
    lat = np.pi / 2 - (np.arange(h) + 0.5) / h * np.pi
    lo, la = np.meshgrid(lon, lat)
    # lon 0 => north (-Z), increasing eastwards
    x = np.sin(lo) * np.cos(la)
    y = np.sin(la)
    z = -np.cos(lo) * np.cos(la)
    return np.stack([x, y, z], axis=-1)


def perspective_dirs(w, h, fov_deg=70.0, yaw_deg=0.0, pitch_deg=10.0):
    f = 1.0 / np.tan(np.radians(fov_deg) / 2)
    ar = w / h
    px = ((np.arange(w) + 0.5) / w * 2 - 1) * ar
    py = (1 - (np.arange(h) + 0.5) / h * 2)
    gx, gy = np.meshgrid(px, py)
    d = np.stack([gx, gy, np.full_like(gx, f)], axis=-1)
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    p = np.radians(-pitch_deg); ya = np.radians(yaw_deg)   # positive pitch = look up
    # pitch about X
    x, y, z = d[..., 0], d[..., 1], d[..., 2]
    y2 = y * np.cos(p) - z * np.sin(p)
    z2 = y * np.sin(p) + z * np.cos(p)
    # yaw about Y ; camera looks towards -Z at yaw 0 (north)
    x3 = x * np.cos(ya) + z2 * np.sin(ya)
    z3 = -x * np.sin(ya) + z2 * np.cos(ya)
    return np.stack([x3, y2, -z3], axis=-1)


def basis(center):
    c = np.array(center, dtype=np.float64)
    c /= np.linalg.norm(c)
    up = np.array([0.0, 1.0, 0.0])
    if abs(np.dot(c, up)) > 0.98:
        up = np.array([0.0, 0.0, 1.0])
    r = np.cross(up, c); r /= np.linalg.norm(r)
    u = np.cross(c, r); u /= np.linalg.norm(u)
    return c, r, u


def splat(rgb, glow_acc, d, sprite, center, ang_deg, roll_deg=0.0, opacity=1.0,
          glow=None, glow_scale=1.0, glow_strength=1.0, alpha_mod=None):
    """Gnomonic-project an RGBA sprite onto the sky. Seamless across cube faces."""
    c, r, u = basis(center)
    if roll_deg:
        a = np.radians(roll_deg)
        r, u = r * np.cos(a) + u * np.sin(a), -r * np.sin(a) + u * np.cos(a)
    half = np.tan(np.radians(ang_deg) / 2.0)
    lim = np.cos(min(np.radians(ang_deg) * 0.95 * max(1.0, glow_scale), np.radians(88.0)))
    dot = d @ c
    sel = dot > lim
    if not sel.any():
        return
    ds = d[sel]
    t = ds / (ds @ c)[:, None]
    lx = (t @ r); ly = (t @ u)

    def sample(spr, scale, into, mul):
        sh, sw = spr.shape[:2]
        sx = (lx / (half * scale) * 0.5 + 0.5) * sw - 0.5
        sy = (0.5 - ly / (half * scale) * 0.5) * sh - 0.5
        inside = (sx > -1) & (sx < sw) & (sy > -1) & (sy < sh)
        if not inside.any():
            return
        sxc = np.clip(sx[inside], 0, sw - 1.001); syc = np.clip(sy[inside], 0, sh - 1.001)
        x0 = np.floor(sxc).astype(int); y0 = np.floor(syc).astype(int)
        fx = (sxc - x0)[:, None]; fy = (syc - y0)[:, None]
        x1 = np.minimum(x0 + 1, sw - 1); y1 = np.minimum(y0 + 1, sh - 1)
        s = (spr[y0, x0] * (1 - fx) * (1 - fy) + spr[y0, x1] * fx * (1 - fy) +
             spr[y1, x0] * (1 - fx) * fy + spr[y1, x1] * fx * fy)
        a = (s[:, 3:4] / 255.0) * mul
        col = s[:, :3] / 255.0
        idx = np.where(sel)
        idx = tuple(i[inside] for i in idx)
        if alpha_mod is not None:
            a = a * alpha_mod[idx][:, None]
        if into is rgb:
            rgb[idx] = rgb[idx] * (1 - a) + col * a
        else:
            into[idx] += col * a

    if glow is not None:
        sample(glow, glow_scale, glow_acc, glow_strength)
    sample(sprite, 1.0, rgb, opacity)


def window_glow(g, inner=0.52, outer=0.99):
    S0, S1 = g.shape[0], g.shape[1]
    yy, xx = np.mgrid[0:S0, 0:S1]
    r = np.sqrt(((xx - (S1 - 1) / 2) / (S1 / 2)) ** 2 + ((yy - (S0 - 1) / 2) / (S0 / 2)) ** 2)
    w = np.clip((outer - r) / (outer - inner), 0, 1)
    w = w * w * (3 - 2 * w)
    out = g.copy()
    out[..., 3] *= w
    return out


# ---------------------------------------------------------------- sprites --
def _poly(dr, pts, fill, outline=None, width=0):
    dr.polygon([tuple(p) for p in pts], fill=fill, outline=outline, width=width)


def _face_polys(S, style):
    """Jack-o-lantern face polygons in canvas coords; returns list of polygons."""
    cx = S * 0.5
    P = []
    if style == 0:      # classic angry
        ey = S * 0.44; ew = S * 0.135; eh = S * 0.115
        P.append([(cx - S * 0.30, ey - eh), (cx - S * 0.30 + ew, ey - eh * 0.1), (cx - S * 0.30 + ew * 0.15, ey + eh * 0.5)])
        P.append([(cx + S * 0.30, ey - eh), (cx + S * 0.30 - ew, ey - eh * 0.1), (cx + S * 0.30 - ew * 0.15, ey + eh * 0.5)])
        P.append([(cx, ey + eh * 0.55), (cx - S * 0.055, ey + eh * 1.75), (cx + S * 0.055, ey + eh * 1.75)])
        m = []
        x0, x1 = cx - S * 0.30, cx + S * 0.30
        top, bot = S * 0.615, S * 0.735
        n = 6
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            m.append((x, top if k % 2 == 0 else top + S * 0.045))
        for k in range(n, -1, -1):
            x = x0 + (x1 - x0) * k / n
            m.append((x, bot if k % 2 == 1 else bot - S * 0.045))
        P.append(m)
    elif style == 1:    # round eyes, grin
        ey = S * 0.44
        for sx in (-1, 1):
            P.append([(cx + sx * S * 0.30, ey - S * 0.115), (cx + sx * S * 0.145, ey - S * 0.02),
                      (cx + sx * S * 0.235, ey + S * 0.085)])
        P.append([(cx, ey + S * 0.055), (cx - S * 0.05, ey + S * 0.155), (cx + S * 0.05, ey + S * 0.155)])
        m = []
        x0, x1 = cx - S * 0.275, cx + S * 0.275
        n = 20
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            t = (k / n) * 2 - 1
            m.append((x, S * 0.615 + S * 0.075 * (1 - t * t)))
        for k in range(n, -1, -1):
            x = x0 + (x1 - x0) * k / n
            t = (k / n) * 2 - 1
            m.append((x, S * 0.685 + S * 0.085 * (1 - t * t)))
        P.append(m)
        for sx in (-1, 1):   # fangs
            P.append([(cx + sx * S * 0.16, S * 0.655), (cx + sx * S * 0.215, S * 0.66), (cx + sx * S * 0.185, S * 0.745)])
    elif style == 2:    # wicked slanted
        ey = S * 0.45
        for sx in (-1, 1):
            P.append([(cx + sx * S * 0.325, ey - S * 0.135), (cx + sx * S * 0.125, ey + S * 0.005),
                      (cx + sx * S * 0.315, ey + S * 0.06)])
        P.append([(cx - S * 0.055, ey + S * 0.155), (cx + S * 0.055, ey + S * 0.155), (cx, ey + S * 0.045)])
        m = []
        x0, x1 = cx - S * 0.315, cx + S * 0.315
        n = 8
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            t = (k / n) * 2 - 1
            m.append((x, S * 0.60 + S * 0.05 * (1 - t * t) + (S * 0.05 if k % 2 else 0)))
        for k in range(n, -1, -1):
            x = x0 + (x1 - x0) * k / n
            t = (k / n) * 2 - 1
            m.append((x, S * 0.70 + S * 0.075 * (1 - t * t) - (S * 0.05 if k % 2 else 0)))
        P.append(m)
    elif style == 3:    # surprised: round eyes and an O mouth
        ey = S * 0.435
        for sx in (-1, 1):
            P.append([(cx + sx * S * 0.215 + np.cos(a) * S * 0.082,
                       ey + np.sin(a) * S * 0.082) for a in np.linspace(0, 2 * np.pi, 14, endpoint=False)])
        P.append([(cx, ey + S * 0.070), (cx - S * 0.044, ey + S * 0.150), (cx + S * 0.044, ey + S * 0.150)])
        P.append([(cx + np.cos(a) * S * 0.118, S * 0.715 + np.sin(a) * S * 0.088)
                  for a in np.linspace(0, 2 * np.pi, 18, endpoint=False)])
    else:               # style 4: sly cat eyes, narrow toothy smirk
        ey = S * 0.445
        for sx in (-1, 1):
            P.append([(cx + sx * S * 0.315, ey - S * 0.05), (cx + sx * S * 0.145, ey - S * 0.115),
                      (cx + sx * S * 0.165, ey + S * 0.02), (cx + sx * S * 0.305, ey + S * 0.045)])
        P.append([(cx - S * 0.06, ey + S * 0.16), (cx + S * 0.06, ey + S * 0.16),
                  (cx + S * 0.02, ey + S * 0.055), (cx - S * 0.02, ey + S * 0.055)])
        m = []
        x0, x1 = cx - S * 0.295, cx + S * 0.295
        n = 24
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            t = (k / n) * 2 - 1
            m.append((x, S * 0.625 + S * 0.09 * (1 - t * t) - S * 0.03 * t))
        for k in range(n, -1, -1):
            x = x0 + (x1 - x0) * k / n
            t = (k / n) * 2 - 1
            m.append((x, S * 0.675 + S * 0.10 * (1 - t * t) - S * 0.03 * t))
        P.append(m)
        for sx, off in [(-1, 0.155), (1, 0.035), (1, 0.165)]:   # teeth biting into the smile
            x = cx + sx * S * off
            P.append([(x - S * 0.030, S * 0.655), (x + S * 0.030, S * 0.658), (x, S * 0.742)])
    return P


N_FACE_STYLES = 5


def pumpkin_sprite(S=384, body=(214, 108, 26), dark=(126, 54, 12), rim=(255, 168, 66),
                   glowcol=(255, 210, 120), halo=(255, 122, 26), face_style=0, lit=True,
                   silhouette=False, stem=(84, 104, 44), seed=0):
    """Returns (rgba uint8 HxWx4, glow rgba uint8) sprite arrays."""
    F = 3 if S <= 192 else 2
    C = S * F
    img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cx, cy = C * 0.5, C * 0.545
    W, H = C * 0.432, C * 0.388
    lobes = [(-0.76, 0.30, 0.62), (-0.55, 0.36, 0.78), (-0.30, 0.41, 0.91),
             (0.0, 0.44, 1.0), (0.30, 0.41, 0.91), (0.55, 0.36, 0.78), (0.76, 0.30, 0.62)]
    bcol = body if not silhouette else (16, 12, 20)
    dcol = dark if not silhouette else (8, 6, 12)
    scol = stem if not silhouette else (12, 10, 16)
    lw = max(2, int(C * 0.0065))

    # ---- stem, curl and leaf sit behind the body ----------------------------
    sx0, sy0 = cx - C * 0.016, cy - H * 0.90
    dr.polygon([(sx0 - C * 0.040, sy0), (sx0 + C * 0.046, sy0),
                (sx0 + C * 0.062, sy0 - C * 0.058), (sx0 + C * 0.105, sy0 - C * 0.092),
                (sx0 + C * 0.140, sy0 - C * 0.118), (sx0 + C * 0.098, sy0 - C * 0.140),
                (sx0 + C * 0.052, sy0 - C * 0.112), (sx0 + C * 0.012, sy0 - C * 0.062),
                (sx0 - C * 0.030, sy0 - C * 0.030)], fill=scol)
    if not silhouette:
        dr.line([(sx0 + C * 0.010, sy0 - C * 0.020), (sx0 + C * 0.058, sy0 - C * 0.082),
                 (sx0 + C * 0.104, sy0 - C * 0.110)],
                fill=tuple(int(v * 1.35) % 256 for v in scol), width=max(1, int(C * 0.006)))
        dr.arc([cx + C * 0.060, cy - H * 1.30, cx + C * 0.215, cy - H * 1.02],
               200, 480, fill=scol, width=max(2, int(C * 0.009)))
        lx, ly = cx - C * 0.105, cy - H * 0.98
        dr.polygon([(lx, ly), (lx - C * 0.085, ly - C * 0.055), (lx - C * 0.135, ly - C * 0.012),
                    (lx - C * 0.105, ly + C * 0.042), (lx - C * 0.040, ly + C * 0.038)], fill=scol)
        dr.line([(lx, ly + C * 0.006), (lx - C * 0.115, ly - C * 0.010)],
                fill=tuple(int(v * 0.55) for v in scol), width=max(1, int(C * 0.004)))

    # ---- body ---------------------------------------------------------------
    for ox, hw, hh in lobes:
        dr.ellipse([cx + ox * W - hw * W, cy - hh * H, cx + ox * W + hw * W, cy + hh * H], fill=bcol)

    arr = np.asarray(img).astype(np.float64)
    if not silhouette:
        yy, xx = np.mgrid[0:C, 0:C]
        nx = (xx - cx) / W
        ny = (yy - cy) / H
        rr = np.sqrt(nx ** 2 + ny ** 2)
        shade = np.clip(1.20 - 0.46 * rr ** 2, 0.42, 1.24)
        shade *= np.clip(1.12 - 0.32 * (ny + 0.6), 0.55, 1.22)
        # ribs: a bright crown per lobe, a dark crease between them
        ribs = np.zeros_like(nx)
        for ox, hw, _ in lobes:
            ribs += np.exp(-((nx - ox * 0.92) / 0.22) ** 2)
        ribs = ribs / max(ribs.max(), 1e-6)
        shade *= 0.72 + 0.47 * ribs
        # skin speckle
        rng = np.random.default_rng(seed + 7)
        sp = rng.random((max(C // 12, 4), max(C // 12, 4)))
        sp = np.asarray(Image.fromarray((sp * 255).astype(np.uint8)).resize((C, C), Image.BICUBIC)) / 255.0
        shade *= 0.965 + 0.07 * sp
        edge = np.clip((rr - 0.70) / 0.32, 0, 1)
        shade *= (1 - 0.58 * edge)
        arr[..., :3] *= shade[..., None]
        # specular bloom, upper left
        spec = np.exp(-(((nx + 0.42) / 0.36) ** 2 + ((ny + 0.44) / 0.30) ** 2))
        arr[..., :3] += np.array(rim) * (spec * 0.17)[..., None]
        np.clip(arr, 0, 255, out=arr)

    img = Image.fromarray(arr.astype(np.uint8))
    dr = ImageDraw.Draw(img)
    for ox, hw, hh in lobes:                       # rib seams
        dr.ellipse([cx + ox * W - hw * W, cy - hh * H, cx + ox * W + hw * W, cy + hh * H],
                   outline=dcol, width=lw)
    if not silhouette:
        dr.arc([cx - W, cy - H, cx + W, cy + H], 188, 318, fill=rim + (170,), width=lw + 1)
        dr.arc([cx - W * 0.97, cy - H * 0.97, cx + W * 0.97, cy + H * 0.97], 20, 130,
               fill=dcol + (140,), width=lw)

    # ---- carved face --------------------------------------------------------
    glow_img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    gdr = ImageDraw.Draw(glow_img)
    polys = _face_polys(C, face_style)
    if lit:
        wall = tuple(int(v * 0.42 + 40) for v in glowcol)
        for p in polys:                            # carved wall catching the candle
            dr.polygon([(q[0], q[1] + C * 0.012) for q in p], fill=wall + (255,))
            dr.polygon([tuple(q) for q in p], fill=glowcol + (255,), outline=dcol + (255,), width=lw)
        mask = Image.new("L", (C, C), 0)
        mdr = ImageDraw.Draw(mask)
        for p in polys:
            mdr.polygon([tuple(q) for q in p], fill=255)
        m = np.asarray(mask).astype(np.float64)[..., None] / 255.0
        a = np.asarray(img).astype(np.float64)
        yy = np.mgrid[0:C, 0:C][0][..., None] / C
        hot = np.array(glowcol) * (0.86 + 0.55 * np.clip((yy - 0.44) / 0.34, 0, 1))
        a[..., :3] = a[..., :3] * (1 - m) + np.clip(hot, 0, 255) * m
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        for p in polys:
            gdr.polygon([tuple(q) for q in p], fill=halo + (255,))
        h1 = glow_img.filter(ImageFilter.GaussianBlur(C * 0.05))
        h2 = glow_img.filter(ImageFilter.GaussianBlur(C * 0.17))
        g = np.asarray(h1).astype(np.float64) * 0.55 + np.asarray(h2).astype(np.float64) * 1.05
        glow_img = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))
    else:
        dr2 = ImageDraw.Draw(img)
        for p in polys:
            dr2.polygon([tuple(q) for q in p], fill=(10, 8, 12, 255))

    img = img.resize((S, S), Image.LANCZOS)
    glow_img = glow_img.resize((S, S), Image.LANCZOS)
    return (np.asarray(img).astype(np.float64),
            window_glow(np.asarray(glow_img).astype(np.float64)))


def moon_sprite(S=512, col=(236, 232, 214), crater=True, tint=(1.0, 1.0, 1.0)):
    F = 2; C = S * F
    img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    R = C * 0.40
    dr.ellipse([C / 2 - R, C / 2 - R, C / 2 + R, C / 2 + R], fill=col + (255,))
    if crater:
        rng = np.random.default_rng(7)
        for _ in range(26):
            a = rng.uniform(0, 2 * np.pi); rr = R * np.sqrt(rng.uniform(0, 0.82))
            x = C / 2 + np.cos(a) * rr; y = C / 2 + np.sin(a) * rr
            cr = R * rng.uniform(0.035, 0.13)
            sh = rng.uniform(0.82, 0.95)
            dr.ellipse([x - cr, y - cr, x + cr, y + cr],
                       fill=(int(col[0] * sh), int(col[1] * sh), int(col[2] * sh), 255))
    arr = np.asarray(img).astype(np.float64)
    arr[..., 0] *= tint[0]; arr[..., 1] *= tint[1]; arr[..., 2] *= tint[2]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((S, S), Image.LANCZOS)
    g = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([C / 2 - R, C / 2 - R, C / 2 + R, C / 2 + R], fill=col + (255,))
    g1 = np.asarray(g.filter(ImageFilter.GaussianBlur(C * 0.05))).astype(np.float64) * 0.6
    g2 = np.asarray(g.filter(ImageFilter.GaussianBlur(C * 0.19))).astype(np.float64) * 1.1
    gi = np.clip(g1 + g2, 0, 255)
    gi[..., 0] *= tint[0]; gi[..., 1] *= tint[1]; gi[..., 2] *= tint[2]
    gimg = Image.fromarray(gi.astype(np.uint8)).resize((S, S), Image.LANCZOS)
    return (np.asarray(img).astype(np.float64),
            window_glow(np.asarray(gimg).astype(np.float64)))


def bat_sprite(S=256, col=(10, 8, 14), spread=1.0):
    F = 2; C = S * F
    img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cx, cy = C * 0.5, C * 0.5
    b = C * 0.09
    dr.ellipse([cx - b * 0.55, cy - b, cx + b * 0.55, cy + b], fill=col + (255,))
    dr.polygon([(cx - b * 0.5, cy - b * 0.8), (cx - b * 0.75, cy - b * 1.7), (cx - b * 0.1, cy - b * 1.15)], fill=col + (255,))
    dr.polygon([(cx + b * 0.5, cy - b * 0.8), (cx + b * 0.75, cy - b * 1.7), (cx + b * 0.1, cy - b * 1.15)], fill=col + (255,))
    for s in (-1, 1):
        w = C * 0.44 * spread
        pts = [(cx + s * b * 0.4, cy - b * 0.5),
               (cx + s * w * 0.45, cy - b * 2.2), (cx + s * w * 0.78, cy - b * 1.2),
               (cx + s * w, cy - b * 1.9), (cx + s * w * 0.96, cy + b * 0.4),
               (cx + s * w * 0.66, cy - b * 0.1), (cx + s * w * 0.60, cy + b * 1.15),
               (cx + s * w * 0.36, cy + b * 0.25), (cx + s * w * 0.28, cy + b * 1.35),
               (cx + s * b * 0.5, cy + b * 0.6)]
        dr.polygon(pts, fill=col + (255,))
    return np.asarray(img.resize((S, S), Image.LANCZOS)).astype(np.float64)


def tree_sprite(S=512, col=(9, 8, 14), seed=1):
    F = 2; C = S * F
    img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)

    def branch(x, y, ang, length, w, depth):
        if depth == 0 or length < C * 0.010:
            return
        nx = x + np.cos(ang) * length
        ny = y - np.sin(ang) * length
        dr.line([(x, y), (nx, ny)], fill=col + (255,), width=max(1, int(w)))
        n = 2 if depth > 2 else rng.integers(2, 4)
        for _ in range(n):
            branch(nx, ny, ang + rng.uniform(-0.75, 0.75), length * rng.uniform(0.58, 0.76),
                   w * 0.66, depth - 1)
    branch(C * 0.5, C * 0.98, np.pi / 2 + rng.uniform(-0.12, 0.12), C * 0.225, C * 0.055, 6)
    return np.asarray(img.resize((S, S), Image.LANCZOS)).astype(np.float64)


# ------------------------------------------------------------------ misc ---
def srgb_u8(rgb):
    return (np.clip(rgb, 0, 1) ** (1 / 1.0) * 255.0 + 0.5).astype(np.uint8)


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def lerp3(c0, c1, t):
    c0 = np.array(c0, dtype=np.float64); c1 = np.array(c1, dtype=np.float64)
    return c0 + (c1 - c0) * t[..., None]
