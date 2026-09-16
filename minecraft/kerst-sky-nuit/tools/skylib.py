"""Dependency-free cubemap painting toolkit for Nuit skyboxes.

Everything here works with plain CPython: no Pillow, no numpy.

The cube face layout is taken from Nuit's own renderer
(``common/src/main/java/me/flashyreese/mods/nuit/util/Utils.java``), where
``TEXTURE_FACES`` and ``SKYBOX_FACES`` define a 3x2 atlas:

    col:      0          1          2
    row 0:  bottom      top       south
    row 1:   west      north      east

Faces are painted in *direction space*: every pixel is turned into a world
direction first, and all imagery is a function of that direction.  That keeps
the six faces seamless by construction and makes "put the star 40 degrees above
the southern horizon" the natural way to express a composition.

Minecraft world axes: +X east, -Z north, +Y up.
"""

import math
import struct
import zlib
from array import array

# --------------------------------------------------------------------------
# PNG output
# --------------------------------------------------------------------------


def _chunk(tag, data):
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def write_png(path, width, height, rows, channels, level=9):
    """Write an 8-bit PNG. ``rows`` is an iterable of one bytes object per line."""
    color_type = {1: 0, 3: 2, 4: 6}[channels]
    raw = bytearray()
    for row in rows:
        raw.append(0)  # filter type 0 (None)
        raw += row
    blob = b"\x89PNG\r\n\x1a\n"
    blob += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
    blob += _chunk(b"IDAT", zlib.compress(bytes(raw), level))
    blob += _chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(blob)


# --------------------------------------------------------------------------
# small vector / curve helpers
# --------------------------------------------------------------------------

DEG = math.pi / 180.0


def normalize(v):
    x, y, z = v
    length = math.sqrt(x * x + y * y + z * z) or 1.0
    return (x / length, y / length, z / length)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else (hi if x > hi else x)


def smoothstep(edge0, edge1, x):
    if edge1 == edge0:
        return 0.0 if x < edge0 else 1.0
    t = clamp((x - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def mix(a, b, t):
    return a + (b - a) * t


def mix3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def direction(azimuth_deg, elevation_deg):
    """Azimuth 0 = north, 90 = east; elevation 0 = horizon, 90 = zenith."""
    az = azimuth_deg * DEG
    el = elevation_deg * DEG
    ce = math.cos(el)
    return (ce * math.sin(az), math.sin(el), -ce * math.cos(az))


def azimuth_elevation(d):
    x, y, z = d
    az = math.degrees(math.atan2(x, -z)) % 360.0
    el = math.degrees(math.asin(clamp(y, -1.0, 1.0)))
    return az, el


def angle_delta(a, b):
    """Shortest signed distance from angle ``b`` to angle ``a``, in degrees."""
    return (a - b + 180.0) % 360.0 - 180.0


def tangent_basis(center):
    """Right/up vectors for a small image plane pinned around ``center``."""
    n = normalize(center)
    up_hint = (0.0, 1.0, 0.0)
    if abs(dot(n, up_hint)) > 0.985:
        up_hint = (0.0, 0.0, -1.0)
    right = normalize(cross(up_hint, n))
    up = normalize(cross(n, right))
    return right, up


# --------------------------------------------------------------------------
# value noise
# --------------------------------------------------------------------------

_M32 = 0xFFFFFFFF


def _hash3(i, j, k, seed):
    n = (i * 73856093) ^ (j * 19349663) ^ (k * 83492791) ^ (seed * 2654435761)
    n &= _M32
    n = ((n ^ (n >> 13)) * 1274126177) & _M32
    return ((n ^ (n >> 16)) & _M32) * 2.3283064370807974e-10


def vnoise3(x, y, z, seed=0):
    xi = math.floor(x)
    yi = math.floor(y)
    zi = math.floor(z)
    xf = x - xi
    yf = y - yi
    zf = z - zi
    u = xf * xf * (3.0 - 2.0 * xf)
    v = yf * yf * (3.0 - 2.0 * yf)
    w = zf * zf * (3.0 - 2.0 * zf)
    xi = int(xi)
    yi = int(yi)
    zi = int(zi)
    h = _hash3
    c000 = h(xi, yi, zi, seed)
    c100 = h(xi + 1, yi, zi, seed)
    c010 = h(xi, yi + 1, zi, seed)
    c110 = h(xi + 1, yi + 1, zi, seed)
    c001 = h(xi, yi, zi + 1, seed)
    c101 = h(xi + 1, yi, zi + 1, seed)
    c011 = h(xi, yi + 1, zi + 1, seed)
    c111 = h(xi + 1, yi + 1, zi + 1, seed)
    x00 = c000 + (c100 - c000) * u
    x10 = c010 + (c110 - c010) * u
    x01 = c001 + (c101 - c001) * u
    x11 = c011 + (c111 - c011) * u
    y0 = x00 + (x10 - x00) * v
    y1 = x01 + (x11 - x01) * v
    return y0 + (y1 - y0) * w


def fbm3(x, y, z, octaves=4, seed=0, lacunarity=2.0, gain=0.5):
    total = 0.0
    amplitude = 1.0
    norm = 0.0
    freq = 1.0
    for octave in range(octaves):
        total += amplitude * vnoise3(x * freq, y * freq, z * freq, seed + octave * 101)
        norm += amplitude
        amplitude *= gain
        freq *= lacunarity
    return total / norm


# --------------------------------------------------------------------------
# cube faces
# --------------------------------------------------------------------------


class Face:
    """One cube face: origin + du/dv spans, straight out of Nuit's SKYBOX_FACES."""

    __slots__ = ("index", "name", "col", "row", "normal", "right", "down")

    def __init__(self, index, name, col, row, origin, du, dv):
        self.index = index
        self.name = name
        self.col = col
        self.row = row
        # centre of the face == its outward normal (all spans are +-1)
        self.normal = (
            origin[0] + du[0] * 0.5 + dv[0] * 0.5,
            origin[1] + du[1] * 0.5 + dv[1] * 0.5,
            origin[2] + du[2] * 0.5 + dv[2] * 0.5,
        )
        self.right = (du[0] * 0.5, du[1] * 0.5, du[2] * 0.5)
        self.down = (dv[0] * 0.5, dv[1] * 0.5, dv[2] * 0.5)

    def direction(self, a, b):
        """``a``/``b`` in [-1, 1]; ``a`` runs right, ``b`` runs down the image."""
        n, r, d = self.normal, self.right, self.down
        return normalize(
            (
                n[0] + r[0] * a + d[0] * b,
                n[1] + r[1] * a + d[1] * b,
                n[2] + r[2] * a + d[2] * b,
            )
        )

    def project(self, v):
        """Inverse of :meth:`direction`; returns (a, b) or None if behind."""
        depth = dot(v, self.normal)
        if depth <= 1e-6:
            return None
        return (dot(v, self.right) / depth, dot(v, self.down) / depth)


FACES = [
    Face(0, "bottom", 0, 0, (-1, -1, -1), (2, 0, 0), (0, 0, 2)),
    Face(1, "north", 1, 1, (-1, 1, -1), (2, 0, 0), (0, -2, 0)),
    Face(2, "south", 2, 0, (1, 1, 1), (-2, 0, 0), (0, -2, 0)),
    Face(3, "top", 1, 0, (-1, 1, 1), (2, 0, 0), (0, 0, -2)),
    Face(4, "east", 2, 1, (1, 1, -1), (0, 0, 2), (0, -2, 0)),
    Face(5, "west", 0, 1, (-1, 1, 1), (0, 0, -2), (0, -2, 0)),
]

ATLAS_COLS = 3
ATLAS_ROWS = 2


# --------------------------------------------------------------------------
# painting
# --------------------------------------------------------------------------


class FaceBuffer:
    """Linear-light RGB(A) accumulation buffer for a single cube face."""

    def __init__(self, face, size, channels=3):
        self.face = face
        self.size = size
        self.channels = channels
        self.data = array("f", bytes(4 * size * size * channels))

    # -- coordinate helpers -------------------------------------------------

    def pixel_direction(self, x, y):
        size = self.size
        a = (x + 0.5) * 2.0 / size - 1.0
        b = (y + 0.5) * 2.0 / size - 1.0
        return self.face.direction(a, b)

    # -- bulk fill ----------------------------------------------------------

    def fill_field(self, field_fn, lowres):
        """Evaluate ``field_fn(direction) -> (r, g, b)`` cheaply.

        The field is sampled on a ``lowres`` x ``lowres`` grid whose samples sit
        exactly on the face edges, then separably upsampled.  Neighbouring faces
        therefore evaluate identical directions along shared edges and the cube
        stays seamless.
        """
        size = self.size
        face = self.face
        n = lowres
        step = 2.0 / (n - 1)

        grid = []
        for j in range(n):
            b = -1.0 + step * j
            row = []
            for i in range(n):
                a = -1.0 + step * i
                row.extend(field_fn(face.direction(a, b)))
            grid.append(row)

        # horizontal pass: n rows at full width
        wide = []
        scale = (n - 1) / size
        cols = []
        for x in range(size):
            t = (x + 0.5) * scale
            i0 = int(t)
            if i0 >= n - 1:
                i0 = n - 2
            cols.append((i0 * 3, t - i0))
        for j in range(n):
            src = grid[j]
            row = []
            for base, frac in cols:
                inv = 1.0 - frac
                row.append(src[base] * inv + src[base + 3] * frac)
                row.append(src[base + 1] * inv + src[base + 4] * frac)
                row.append(src[base + 2] * inv + src[base + 5] * frac)
            wide.append(row)

        # vertical pass straight into the float buffer
        data = self.data
        channels = self.channels
        stride = size * channels
        for y in range(size):
            t = (y + 0.5) * scale
            j0 = int(t)
            if j0 >= n - 1:
                j0 = n - 2
            frac = t - j0
            inv = 1.0 - frac
            top = wide[j0]
            bot = wide[j0 + 1]
            blended = [a * inv + b * frac for a, b in zip(top, bot)]
            if channels == 3:
                data[y * stride : (y + 1) * stride] = array("f", blended)
            else:
                row = array("f", bytes(4 * stride))
                row[0::4] = array("f", blended[0::3])
                row[1::4] = array("f", blended[1::3])
                row[2::4] = array("f", blended[2::3])
                data[y * stride : (y + 1) * stride] = row

    # -- local, exact rendering --------------------------------------------

    def paint_local(self, center, radius_deg, shade_fn):
        """Evaluate ``shade_fn(direction) -> (r, g, b, a)`` per pixel near ``center``.

        Only the pixels inside the cone are touched, so this stays cheap while
        remaining geometrically exact (no low-res blur, no cube distortion).
        """
        face = self.face
        size = self.size
        projected = face.project(center)
        if projected is None:
            # The cone may still clip this face when it is very wide.
            if radius_deg < 60.0:
                return
            a0, b0 = 0.0, 0.0
            reach = 4.0
        else:
            a0, b0 = projected
            spread = math.tan(min(radius_deg, 80.0) * DEG)
            reach = spread * (1.0 + a0 * a0 + b0 * b0) + 2.0 / size

        a_min = max(-1.0, a0 - reach)
        a_max = min(1.0, a0 + reach)
        b_min = max(-1.0, b0 - reach)
        b_max = min(1.0, b0 + reach)
        if a_min >= a_max or b_min >= b_max:
            return

        x0 = max(0, int((a_min + 1.0) * 0.5 * size) - 1)
        x1 = min(size - 1, int((a_max + 1.0) * 0.5 * size) + 1)
        y0 = max(0, int((b_min + 1.0) * 0.5 * size) - 1)
        y1 = min(size - 1, int((b_max + 1.0) * 0.5 * size) + 1)

        data = self.data
        channels = self.channels
        # Fade whatever the shader returns to zero before the cone edge, so a
        # wide glow can never end in a hard circular cut.
        cos_limit = math.cos(min(radius_deg, 179.0) * DEG)
        cos_inner = math.cos(min(radius_deg, 179.0) * 0.72 * DEG)
        span = (cos_inner - cos_limit) or 1.0
        for y in range(y0, y1 + 1):
            base_row = y * size * channels
            for x in range(x0, x1 + 1):
                d = self.pixel_direction(x, y)
                depth = dot(d, center)
                if depth < cos_limit:
                    continue
                shaded = shade_fn(d)
                if shaded is None:
                    continue
                r, g, b, alpha = shaded
                if alpha <= 0.0:
                    continue
                if depth < cos_inner:
                    t = (depth - cos_limit) / span
                    alpha *= t * t * (3.0 - 2.0 * t)
                idx = base_row + x * channels
                if channels == 3:
                    data[idx] += r * alpha
                    data[idx + 1] += g * alpha
                    data[idx + 2] += b * alpha
                else:
                    data[idx] += r * alpha
                    data[idx + 1] += g * alpha
                    data[idx + 2] += b * alpha
                    data[idx + 3] += alpha

    def splat(self, center, radius_px, color, intensity=1.0, falloff=2.0):
        """Fast additive point sprite, used for the thousands of ordinary stars."""
        face = self.face
        projected = face.project(center)
        if projected is None:
            return
        a, b = projected
        margin = 1.0 + (radius_px + 2.0) * 2.0 / self.size
        if abs(a) > margin or abs(b) > margin:
            return
        size = self.size
        # local scale: face coordinates stretch away from the face centre
        stretch = 1.0 + a * a * 0.5 + b * b * 0.5
        rad = radius_px * stretch
        cx = (a + 1.0) * 0.5 * size - 0.5
        cy = (b + 1.0) * 0.5 * size - 0.5
        x0 = max(0, int(cx - rad))
        x1 = min(size - 1, int(cx + rad) + 1)
        y0 = max(0, int(cy - rad))
        y1 = min(size - 1, int(cy + rad) + 1)
        if x0 > x1 or y0 > y1:
            return
        data = self.data
        channels = self.channels
        cr, cg, cb = color
        inv = 1.0 / (rad * rad) if rad > 0 else 0.0
        for y in range(y0, y1 + 1):
            dy = y - cy
            base_row = y * size * channels
            dy2 = dy * dy
            for x in range(x0, x1 + 1):
                dx = x - cx
                q = (dx * dx + dy2) * inv
                if q >= 1.0:
                    continue
                weight = (1.0 - q) ** falloff * intensity
                idx = base_row + x * channels
                data[idx] += cr * weight
                data[idx + 1] += cg * weight
                data[idx + 2] += cb * weight
                if channels == 4:
                    data[idx + 3] += weight


# --------------------------------------------------------------------------
# tone mapping + atlas assembly
# --------------------------------------------------------------------------

_SRGB = [0] * 4096
for _i in range(4096):
    _c = _i / 4095.0
    _s = 1.055 * (_c ** (1.0 / 2.4)) - 0.055 if _c > 0.0031308 else _c * 12.92
    _SRGB[_i] = max(0, min(255, int(_s * 255.0 + 0.5)))


def encode_rows(buffers, size, channels, gamma_encode=True):
    """Yield atlas scanlines (3x2 grid of faces) as bytes."""
    by_cell = {}
    for buf in buffers:
        by_cell[(buf.face.col, buf.face.row)] = buf
    srgb = _SRGB
    for row in range(ATLAS_ROWS):
        cells = [by_cell[(col, row)] for col in range(ATLAS_COLS)]
        for y in range(size):
            line = bytearray()
            for buf in cells:
                stride = size * channels
                chunk = buf.data[y * stride : (y + 1) * stride]
                if gamma_encode:
                    if channels == 3:
                        line += bytes(
                            srgb[4095 if v >= 1.0 else (0 if v <= 0.0 else int(v * 4095.0))]
                            for v in chunk
                        )
                    else:
                        out = bytearray(stride)
                        for i in range(0, stride, 4):
                            out[i] = srgb[
                                4095 if chunk[i] >= 1.0 else (0 if chunk[i] <= 0.0 else int(chunk[i] * 4095.0))
                            ]
                            out[i + 1] = srgb[
                                4095 if chunk[i + 1] >= 1.0 else (0 if chunk[i + 1] <= 0.0 else int(chunk[i + 1] * 4095.0))
                            ]
                            out[i + 2] = srgb[
                                4095 if chunk[i + 2] >= 1.0 else (0 if chunk[i + 2] <= 0.0 else int(chunk[i + 2] * 4095.0))
                            ]
                            a = chunk[i + 3]
                            out[i + 3] = 255 if a >= 1.0 else (0 if a <= 0.0 else int(a * 255.0 + 0.5))
                        line += out
                else:
                    line += bytes(
                        255 if v >= 1.0 else (0 if v <= 0.0 else int(v * 255.0 + 0.5))
                        for v in chunk
                    )
            yield bytes(line)


class CubeSampler:
    """Reads back a finished atlas so previews can be rendered from it."""

    def __init__(self, faces_bytes, size, channels):
        self.faces = faces_bytes  # dict: face index -> bytes
        self.size = size
        self.channels = channels

    _BY_NAME = {f.name: f for f in FACES}

    def sample(self, d):
        # the dominant axis picks the face outright - no need to test all six
        x, y, z = d
        ax, ay, az = abs(x), abs(y), abs(z)
        if ax >= ay and ax >= az:
            face = self._BY_NAME["east" if x > 0 else "west"]
        elif ay >= az:
            face = self._BY_NAME["top" if y > 0 else "bottom"]
        else:
            face = self._BY_NAME["south" if z > 0 else "north"]
        projected = face.project(d)
        if projected is None:
            return (0, 0, 0, 0)
        a, b = projected
        size = self.size
        channels = self.channels
        data = self.faces[face.index]

        # Bilinear, because that is what the GPU does with the finished texture.
        fx = (a + 1.0) * 0.5 * size - 0.5
        fy = (b + 1.0) * 0.5 * size - 0.5
        x0 = int(math.floor(fx))
        y0 = int(math.floor(fy))
        tx = fx - x0
        ty = fy - y0
        x0 = 0 if x0 < 0 else (size - 1 if x0 > size - 1 else x0)
        y0 = 0 if y0 < 0 else (size - 1 if y0 > size - 1 else y0)
        x1 = x0 + 1 if x0 + 1 < size else x0
        y1 = y0 + 1 if y0 + 1 < size else y0

        i00 = (y0 * size + x0) * channels
        i10 = (y0 * size + x1) * channels
        i01 = (y1 * size + x0) * channels
        i11 = (y1 * size + x1) * channels
        w00 = (1.0 - tx) * (1.0 - ty)
        w10 = tx * (1.0 - ty)
        w01 = (1.0 - tx) * ty
        w11 = tx * ty

        out = []
        for c in range(channels):
            out.append(
                data[i00 + c] * w00
                + data[i10 + c] * w10
                + data[i01 + c] * w01
                + data[i11 + c] * w11
            )
        if channels == 3:
            return (out[0], out[1], out[2], 255)
        return (out[0], out[1], out[2], out[3])
