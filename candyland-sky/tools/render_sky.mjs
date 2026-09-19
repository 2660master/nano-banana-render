/**
 * Bubblegum Noon -> Nuit square-textured skybox atlas.
 *
 * Everything in this file is a function of a *direction vector*, never of a
 * 2D canvas position. That is what makes the six faces seamless: two pixels
 * that sit on either side of a cube edge look up the same direction and so
 * get the same colour, by construction rather than by retouching.
 *
 * Atlas layout is Nuit's, read off Utils.TEXTURE_FACES in the mod source:
 *
 *     +--------+--------+--------+
 *     | bottom |  top   | south  |   row 0
 *     +--------+--------+--------+
 *     |  west  | north  |  east  |   row 1
 *     +--------+--------+--------+
 *
 * Minecraft axes: +X east, -Z north, +Y up.
 *
 *   node render_sky.mjs [--size 1024] [--out DIR]
 */

import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

/* ------------------------------------------------------------------ args */

const argv = process.argv.slice(2);
const argOf = (name, dflt) => {
  const i = argv.indexOf("--" + name);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : dflt;
};
const S = parseInt(argOf("size", "1024"), 10);           // pixels per cube face
const OUT = path.resolve(argOf("out", "./out"));
fs.mkdirSync(OUT, { recursive: true });

const TAU = Math.PI * 2;

/* ------------------------------------------------------------------ prng */

function makeRng(seed) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}
const rnd = makeRng(770377);
const rr = (a, b) => a + rnd() * (b - a);
const pick = (a) => a[Math.floor(rnd() * a.length) % a.length];

/* ------------------------------------------------------------- face maths
 * a = 2u-1, b = 2v-1 over a face; u,v are the face's own texture coords with
 * v = 0 at the top. These six expressions come straight from Nuit's per-face
 * rotation matrices applied to its base quad. */

const FACES = [
  { name: "bottom", col: 0, row: 0, dir: (a, b) => [a, -1, b] },
  { name: "north",  col: 1, row: 1, dir: (a, b) => [a, -b, -1] },
  { name: "south",  col: 2, row: 0, dir: (a, b) => [-a, -b, 1] },
  { name: "top",    col: 1, row: 0, dir: (a, b) => [a, 1, -b] },
  { name: "east",   col: 2, row: 1, dir: (a, b) => [1, -b, a] },
  { name: "west",   col: 0, row: 1, dir: (a, b) => [-1, -b, -a] },
];

for (const f of FACES) f.n = null;   // filled in once `norm` is defined, below

/* Inverse: where does this direction land on that face? Returns null when the
 * direction points away from the face. */
function faceCoords(f, v) {
  const [x, y, z] = v;
  let k, a, b;
  switch (f.name) {
    case "bottom": if (y >= -1e-6) return null; k = -1 / y; a = x * k; b = z * k; break;
    case "north":  if (z >= -1e-6) return null; k = -1 / z; a = x * k; b = -y * k; break;
    case "south":  if (z <= 1e-6) return null;  k = 1 / z;  a = -x * k; b = -y * k; break;
    case "top":    if (y <= 1e-6) return null;  k = 1 / y;  a = x * k; b = -z * k; break;
    case "east":   if (x <= 1e-6) return null;  k = 1 / x;  a = z * k; b = -y * k; break;
    case "west":   if (x >= -1e-6) return null; k = -1 / x; a = -z * k; b = -y * k; break;
  }
  return [a, b, k];
}

const norm = (v) => {
  const l = Math.hypot(v[0], v[1], v[2]);
  return [v[0] / l, v[1] / l, v[2] / l];
};
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
/** azimuth measured from north, clockwise (so 90 deg = east), altitude in radians */
const fromAzAlt = (az, alt) => {
  const ca = Math.cos(alt);
  return [Math.sin(az) * ca, Math.sin(alt), -Math.cos(az) * ca];
};

for (const f of FACES) f.n = norm(f.dir(0, 0));

const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const smooth = (e0, e1, x) => {
  const t = clamp((x - e0) / (e1 - e0), 0, 1);
  return t * t * (3 - 2 * t);
};
const hex = (h) => [
  parseInt(h.slice(1, 3), 16),
  parseInt(h.slice(3, 5), 16),
  parseInt(h.slice(5, 7), 16),
];

/* ============================================================== THE SKY ===
 * Bubblegum Noon. Zenith is bubblegum, the horizon washes out to a pale
 * sherbet, whipped-cream banks sit low, and gumballs and blown bubbles float
 * at every size all the way around the compass. */

/* --- 1. the gradient, keyed on sin(altitude) so it packs detail near the
 *        horizon where the player actually looks --- */
const SKY_STOPS = [
  [-1.00, hex("#D2699B")],
  [-0.42, hex("#EC96BE")],
  [-0.12, hex("#F7C4DD")],
  [-0.030, hex("#F9DCEC")],
  [ 0.000, hex("#EFF6FD")],
  [ 0.035, hex("#FBE4F4")],
  [ 0.100, hex("#FFD2EC")],
  [ 0.240, hex("#FFBCE4")],
  [ 0.460, hex("#FFA2DA")],
  [ 0.720, hex("#FF87CA")],
  [ 1.000, hex("#FF6FC0")],
];

function gradientAt(y, out) {
  let i = 0;
  while (i < SKY_STOPS.length - 2 && y > SKY_STOPS[i + 1][0]) i++;
  const [t0, c0] = SKY_STOPS[i];
  const [t1, c1] = SKY_STOPS[i + 1];
  const t = clamp((y - t0) / (t1 - t0), 0, 1);
  out[0] = c0[0] + (c1[0] - c0[0]) * t;
  out[1] = c0[1] + (c1[1] - c0[1]) * t;
  out[2] = c0[2] + (c1[2] - c0[2]) * t;
}

/* --- 2. the bright quarter of the sky. Not a sun disc: Nuit draws the real,
 *        moving sun through the decorations layer. This is just the ambient
 *        lift so the cube isn't evenly lit. --- */
const SUN = norm(fromAzAlt((138 * Math.PI) / 180, (46 * Math.PI) / 180));

/* --- 3. whipped-cream banks, as clusters of soft puffs --- */
const PUFFS = [];
for (let c = 0; c < 17; c++) {
  const az = rnd() * TAU;
  const alt = 0.07 + Math.pow(rnd(), 1.6) * 0.5;
  const n = 8 + Math.floor(rnd() * 11);
  const spreadAz = rr(0.2, 0.55), spreadAlt = rr(0.035, 0.105);
  for (let i = 0; i < n; i++) {
    const pAlt = clamp(alt + rr(-spreadAlt, spreadAlt), 0.0, 0.74);
    const pAz = az + rr(-spreadAz, spreadAz) / Math.max(0.25, Math.cos(pAlt));
    PUFFS.push({
      d: norm(fromAzAlt(pAz, pAlt)),
      r: rr(0.062, 0.135),
      alt: pAlt,
    });
  }
}

/* --- 4. gumballs and bubbles. The giant one sits just under the western
 *        horizon so only its crown shows: it gives the sky a landmark, which
 *        is what stops a 360 skybox feeling like wallpaper. --- */
const CANDY = [hex("#FF5FAE"), hex("#5FD8B2"), hex("#FFC93F"), hex("#A98BFF"),
               hex("#5FCBFF"), hex("#FF7FB8"), hex("#FFE873"), hex("#FF9ED2"),
               hex("#6FEAC4"), hex("#FFC48B"), hex("#8FD8FF"), hex("#C6A9FF")];

const BALLS = [];
function ball(az, alt, r, color, opts = {}) {
  BALLS.push({
    d: norm(fromAzAlt(az, alt)),
    r,
    color,
    alpha: opts.alpha === undefined ? 1 : opts.alpha,
    irid: !!opts.irid,
  });
}

/* the landmark */
ball((262 * Math.PI) / 180, -0.13, 0.30, hex("#F5479F"), { alpha: 1 });

/* large floaters, spread right around the compass */
for (let i = 0; i < 11; i++) {
  ball(rnd() * TAU, rr(0.06, 0.82), rr(0.065, 0.135), pick(CANDY),
       { alpha: i % 4 === 0 ? 0.68 : 1, irid: i % 3 === 0 });
}
/* mid */
for (let i = 0; i < 16; i++) {
  ball(rnd() * TAU, rr(0.02, 0.95), rr(0.028, 0.065), pick(CANDY),
       { alpha: i % 4 === 0 ? 0.68 : 1, irid: i % 3 === 0 });
}
/* clumps of little blown bubbles */
for (let c = 0; c < 12; c++) {
  const az = rnd() * TAU, alt = rr(0.03, 0.9);
  for (let i = 0, n = 3 + Math.floor(rnd() * 4); i < n; i++) {
    const bAlt = clamp(alt + rr(-0.055, 0.055), -0.02, 1.35);
    ball(az + rr(-0.06, 0.06) / Math.max(0.25, Math.cos(bAlt)), bAlt,
         rr(0.012, 0.03), pick([hex("#FFF2F9"), hex("#FFC7E6"), hex("#B8F0E4"), hex("#FFE9A8")]),
         { alpha: 0.72, irid: true });
  }
}

/* --- 5. sugar sparkle --- */
const SPARKS = [];
for (let i = 0; i < 90; i++) {
  SPARKS.push({
    d: norm(fromAzAlt(rnd() * TAU, rr(0.03, 1.45))),
    r: rr(0.006, 0.016),
    a: rr(0.35, 0.95),
  });
}

const LIGHT = norm([-0.45, 0.62, 0.64]);   // in each ball's own billboard frame
const HALF = norm([LIGHT[0], LIGHT[1], LIGHT[2] + 1]);
const WORLD_UP = [0, 1, 0];

/* --- 6. sugar grain: 3D value noise, so it too crosses cube edges cleanly --- */
function hash3(i, j, k) {
  let h = Math.imul(i, 374761393) ^ Math.imul(j, 668265263) ^ Math.imul(k, 2147483647);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
function noise3(x, y, z) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const xf = x - xi, yf = y - yi, zf = z - zi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf), w = zf * zf * (3 - 2 * zf);
  const c = (di, dj, dk) => hash3(xi + di, yi + dj, zi + dk);
  const x00 = c(0,0,0) + (c(1,0,0) - c(0,0,0)) * u;
  const x10 = c(0,1,0) + (c(1,1,0) - c(0,1,0)) * u;
  const x01 = c(0,0,1) + (c(1,0,1) - c(0,0,1)) * u;
  const x11 = c(0,1,1) + (c(1,1,1) - c(0,1,1)) * u;
  return (x00 + (x10 - x00) * v) + ((x01 + (x11 - x01) * v) - (x00 + (x10 - x00) * v)) * w;
}

/* ------------------------------------------------------- per-pixel shading */

const tmp = [0, 0, 0];

/** Gradient + the ambient lift from the bright quarter of the sky. */
function shadeBase(d, out) {
  gradientAt(d[1], tmp);
  const sd = Math.max(0, dot(d, SUN));
  const lift = Math.pow(sd, 10) * 30 + Math.pow(sd, 2.4) * 10;
  out[0] = Math.min(255, tmp[0] + lift);
  out[1] = Math.min(255, tmp[1] + lift * 0.96);
  out[2] = Math.min(255, tmp[2] + lift * 0.82);
}

/** Composite accumulated cloud coverage over a base colour, in place. */
function compositeCloud(out, sum, lsum, wsum) {
  if (sum <= 0) return;
  const cov = clamp(1 - Math.exp(-sum * 3.0), 0, 1);
  const a = smooth(0.10, 0.60, cov) * 0.97;
  const lt = wsum > 0 ? lsum / wsum : 0.5;
  const cr = 255, cg = 211 + 44 * lt, cb = 234 + 21 * lt;
  out[0] += (cr - out[0]) * a;
  out[1] += (cg - out[1]) * a;
  out[2] += (cb - out[2]) * a;
}

/** Full background for one direction. Only used by the preview camera, where
 *  there is no per-face buffer to accumulate into. */
function shadeBackground(d, out) {
  shadeBase(d, out);
  const pixAlt = Math.asin(clamp(d[1], -1, 1));
  let sum = 0, lsum = 0, wsum = 0;
  for (let i = 0; i < PUFFS.length; i++) {
    const p = PUFFS[i];
    const c = dot(d, p.d);
    if (c < p.cosR) continue;
    const ang = Math.sqrt(Math.max(0, 2 * (1 - c)));
    const t = 1 - ang * p.invR;
    const w = t * t;
    sum += w;
    wsum += w;
    lsum += clamp(0.5 + (pixAlt - p.alt) * p.invR * 0.95, 0, 1) * w;
  }
  compositeCloud(out, sum, lsum, wsum);
}

/* Precompute per-object constants. */
for (const p of PUFFS) { p.cosR = Math.cos(p.r); p.invR = 1 / p.r; }
for (const b of BALLS) {
  b.cosR = Math.cos(b.r);
  b.sinR = Math.sin(b.r);
  let up = [WORLD_UP[0] - b.d[0] * b.d[1], WORLD_UP[1] - b.d[1] * b.d[1], WORLD_UP[2] - b.d[2] * b.d[1]];
  if (Math.hypot(up[0], up[1], up[2]) < 1e-4) up = [1, 0, 0];
  b.up = norm(up);
  b.right = norm(cross(b.up, b.d));
  /* A see-through bubble picks up sky from behind it, so its shadow side must
   * not fall as far as a solid gumball's or it reads as a grey pebble. */
  b.amb = b.alpha < 1 ? 0.56 : 0.34;
  b.dif = b.alpha < 1 ? 0.6 : 0.78;
}
for (const s of SPARKS) {
  s.cosR = Math.cos(s.r * 2.6);
  s.up = norm([WORLD_UP[0] - s.d[0] * s.d[1], WORLD_UP[1] - s.d[1] * s.d[1], WORLD_UP[2] - s.d[2] * s.d[1]]);
  s.right = norm(cross(s.up, s.d));
}

/* ------------------------------------------------------------- rasteriser */

function render() {
  const AW = S * 3, AH = S * 2;
  const img = new Uint8Array(AW * AH * 3);
  const px = [0, 0, 0];
  const pixAng = Math.PI / 2 / S;          // roughly one pixel, in radians

  for (const f of FACES) {
    const ox = f.col * S, oy = f.row * S;
    const dirs = new Float32Array(S * S * 3);

    /* Which slab of this face can an object touch? Shading a few thousand
     * pixels per object beats walking a million. The shading itself always
     * uses the true angular distance, so a box that is too generous costs
     * time but never changes a pixel. */
    const boxFor = (dir, angR) => {
      if (dot(dir, f.n) < -Math.sin(Math.min(1.5, angR)) - 0.05) return null;
      const fc = faceCoords(f, dir);
      if (!fc || fc[2] < 0.4) return [0, 0, S - 1, S - 1];
      const rad = (Math.tan(Math.min(1.3, angR)) * 1.3 / fc[2]) * 0.5 * S + 2;
      const cx = ((fc[0] + 1) / 2) * S, cy = ((fc[1] + 1) / 2) * S;
      const x0 = Math.floor(cx - rad), x1 = Math.ceil(cx + rad);
      const y0 = Math.floor(cy - rad), y1 = Math.ceil(cy + rad);
      if (x1 < 0 || y1 < 0 || x0 > S - 1 || y0 > S - 1) return null;
      return [Math.max(0, x0), Math.max(0, y0), Math.min(S - 1, x1), Math.min(S - 1, y1)];
    };

    /* pass 1: directions + gradient */
    for (let y = 0; y < S; y++) {
      const b = ((y + 0.5) / S) * 2 - 1;
      for (let x = 0; x < S; x++) {
        const a = ((x + 0.5) / S) * 2 - 1;
        const d = norm(f.dir(a, b));
        const i3 = (y * S + x) * 3;
        dirs[i3] = d[0]; dirs[i3 + 1] = d[1]; dirs[i3 + 2] = d[2];
        shadeBase(d, px);
        const o = ((oy + y) * AW + ox + x) * 3;
        img[o] = clamp(px[0], 0, 255);
        img[o + 1] = clamp(px[1], 0, 255);
        img[o + 2] = clamp(px[2], 0, 255);
      }
    }

    /* pass 2: accumulate cloud coverage, one puff's bounding box at a time */
    const csum = new Float32Array(S * S);
    const clsum = new Float32Array(S * S);
    const cwsum = new Float32Array(S * S);
    for (const p of PUFFS) {
      const box = boxFor(p.d, p.r);
      if (!box) continue;
      for (let y = box[1]; y <= box[3]; y++) {
        for (let x = box[0]; x <= box[2]; x++) {
          const i = y * S + x, i3 = i * 3;
          const c = dirs[i3] * p.d[0] + dirs[i3 + 1] * p.d[1] + dirs[i3 + 2] * p.d[2];
          if (c < p.cosR) continue;
          const t = 1 - Math.sqrt(Math.max(0, 2 * (1 - c))) * p.invR;
          const w = t * t;
          csum[i] += w;
          cwsum[i] += w;
          const pixAlt = Math.asin(clamp(dirs[i3 + 1], -1, 1));
          clsum[i] += clamp(0.5 + (pixAlt - p.alt) * p.invR * 0.95, 0, 1) * w;
        }
      }
    }
    for (let y = 0; y < S; y++) {
      for (let x = 0; x < S; x++) {
        const i = y * S + x;
        if (csum[i] <= 0) continue;
        const o = ((oy + y) * AW + ox + x) * 3;
        px[0] = img[o]; px[1] = img[o + 1]; px[2] = img[o + 2];
        compositeCloud(px, csum[i], clsum[i], cwsum[i]);
        img[o] = clamp(px[0], 0, 255);
        img[o + 1] = clamp(px[1], 0, 255);
        img[o + 2] = clamp(px[2], 0, 255);
      }
    }

    /* gumballs and bubbles */
    for (const ball of BALLS) {
      const box = boxFor(ball.d, ball.r);
      if (!box) continue;
      const aaScale = clamp(pixAng / ball.r, 0.0015, 0.5);
      for (let y = box[1]; y <= box[3]; y++) {
        for (let x = box[0]; x <= box[2]; x++) {
          const i3 = (y * S + x) * 3;
          const dx = dirs[i3], dy = dirs[i3 + 1], dz = dirs[i3 + 2];
          const c = dx * ball.d[0] + dy * ball.d[1] + dz * ball.d[2];
          if (c < ball.cosR - 0.002) continue;

          /* position on the disc, in units of the ball's radius */
          const ox2 = dx - ball.d[0] * c, oy2 = dy - ball.d[1] * c, oz2 = dz - ball.d[2] * c;
          const pxx = (ox2 * ball.right[0] + oy2 * ball.right[1] + oz2 * ball.right[2]) / ball.sinR;
          const pyy = (ox2 * ball.up[0] + oy2 * ball.up[1] + oz2 * ball.up[2]) / ball.sinR;
          const r2 = pxx * pxx + pyy * pyy;
          if (r2 > 1.02) continue;

          const edge = clamp((1 - Math.sqrt(r2)) / aaScale, 0, 1);
          if (edge <= 0) continue;

          const nz = Math.sqrt(Math.max(0, 1 - Math.min(1, r2)));
          const diff = Math.max(0, pxx * LIGHT[0] + pyy * LIGHT[1] + nz * LIGHT[2]);
          const shade = ball.amb + ball.dif * diff;
          const sh = Math.max(0, pxx * HALF[0] + pyy * HALF[1] + nz * HALF[2]);
          const spec = Math.pow(sh, 96) * 0.8 + Math.pow(sh, 20) * 0.1;
          const rim = Math.pow(1 - nz, 3.2);

          let cr = ball.color[0] * shade, cg = ball.color[1] * shade, cb = ball.color[2] * shade;
          /* a cool bounce along the shadowed lower edge keeps it candy, not clay */
          const bounce = Math.pow(Math.max(0, -(pxx * LIGHT[0] + pyy * LIGHT[1] + nz * LIGHT[2])), 1.6) * 0.3;
          cr += 255 * bounce * 0.55; cg += 190 * bounce * 0.55; cb += 225 * bounce * 0.55;

          if (ball.irid) {
            const h = (Math.atan2(pyy, pxx) / TAU + 1) % 1;
            cr += rim * 150 * (0.55 + 0.45 * Math.sin(h * TAU));
            cg += rim * 150 * (0.55 + 0.45 * Math.sin(h * TAU + 2.1));
            cb += rim * 150 * (0.55 + 0.45 * Math.sin(h * TAU + 4.2));
          } else {
            cr += rim * 70; cg += rim * 70; cb += rim * 70;
          }
          cr += spec * 185; cg += spec * 185; cb += spec * 185;

          const o = ((oy + y) * AW + ox + x) * 3;
          const a = edge * ball.alpha;
          img[o] = clamp(img[o] + (cr - img[o]) * a, 0, 255);
          img[o + 1] = clamp(img[o + 1] + (cg - img[o + 1]) * a, 0, 255);
          img[o + 2] = clamp(img[o + 2] + (cb - img[o + 2]) * a, 0, 255);
        }
      }
    }

    /* sparkle */
    for (const sp of SPARKS) {
      const box = boxFor(sp.d, sp.r * 2.8);
      if (!box) continue;
      for (let y = box[1]; y <= box[3]; y++) {
        for (let x = box[0]; x <= box[2]; x++) {
          const i3 = (y * S + x) * 3;
          const dx = dirs[i3], dy = dirs[i3 + 1], dz = dirs[i3 + 2];
          const c = dx * sp.d[0] + dy * sp.d[1] + dz * sp.d[2];
          if (c < sp.cosR) continue;
          const ox2 = dx - sp.d[0] * c, oy2 = dy - sp.d[1] * c, oz2 = dz - sp.d[2] * c;
          const pxx = (ox2 * sp.right[0] + oy2 * sp.right[1] + oz2 * sp.right[2]) / sp.r;
          const pyy = (ox2 * sp.up[0] + oy2 * sp.up[1] + oz2 * sp.up[2]) / sp.r;
          const t = Math.pow(Math.abs(pxx), 0.42) + Math.pow(Math.abs(pyy), 0.42);
          if (t >= 1) continue;
          const a = Math.pow(1 - t, 1.6) * sp.a;
          const o = ((oy + y) * AW + ox + x) * 3;
          img[o] = clamp(img[o] + (255 - img[o]) * a, 0, 255);
          img[o + 1] = clamp(img[o + 1] + (255 - img[o + 1]) * a, 0, 255);
          img[o + 2] = clamp(img[o + 2] + (255 - img[o + 2]) * a, 0, 255);
        }
      }
    }

    /* sugar grain, last, over everything */
    for (let y = 0; y < S; y++) {
      for (let x = 0; x < S; x++) {
        const i3 = (y * S + x) * 3;
        const n = noise3(dirs[i3] * 190, dirs[i3 + 1] * 190, dirs[i3 + 2] * 190) - 0.5;
        const o = ((oy + y) * AW + ox + x) * 3;
        const g = n * 7.5;
        img[o] = clamp(img[o] + g, 0, 255);
        img[o + 1] = clamp(img[o + 1] + g, 0, 255);
        img[o + 2] = clamp(img[o + 2] + g, 0, 255);
      }
    }

    process.stdout.write("  " + f.name + " done\n");
  }
  return { img, AW, AH };
}

/* --------------------------------------------------------------- png out */

const CRC_TABLE = (() => {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c;
  }
  return t;
})();
function crc32(buf) {
  let c = -1;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
}
function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const td = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(td), 0);
  return Buffer.concat([len, td, crc]);
}
function writePNG(file, w, h, rgb) {
  const stride = w * 3;
  const raw = Buffer.alloc((stride + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (stride + 1)] = 0;
    Buffer.from(rgb.buffer, rgb.byteOffset + y * stride, stride).copy(raw, y * (stride + 1) + 1);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  fs.writeFileSync(file, Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", zlib.deflateSync(raw, { level: 9 })),
    chunk("IEND", Buffer.alloc(0)),
  ]));
}

/* ------------------------------------------------------- perspective look
 * A player's-eye view, for checking the thing reads before it ever gets
 * loaded in game. Same sky function, different camera. */
function preview(file, azDeg, altDeg, w, h, fovDeg) {
  const fwd = norm(fromAzAlt((azDeg * Math.PI) / 180, (altDeg * Math.PI) / 180));
  const right = norm(cross([0, 1, 0], fwd));
  const up = cross(fwd, right);
  const f = 1 / Math.tan(((fovDeg * Math.PI) / 180) / 2);
  const img = new Uint8Array(w * h * 3);
  const px = [0, 0, 0];
  for (let y = 0; y < h; y++) {
    const sy = (1 - (2 * (y + 0.5)) / h) / f;
    for (let x = 0; x < w; x++) {
      const sx = ((2 * (x + 0.5)) / w - 1) * (w / h) / f;
      const d = norm([
        fwd[0] + right[0] * sx + up[0] * sy,
        fwd[1] + right[1] * sx + up[1] * sy,
        fwd[2] + right[2] * sx + up[2] * sy,
      ]);
      shadeBackground(d, px);
      let r = px[0], g = px[1], b = px[2];
      for (const ball of BALLS) {
        const c = dot(d, ball.d);
        if (c < ball.cosR - 0.002) continue;
        const o2 = [d[0] - ball.d[0] * c, d[1] - ball.d[1] * c, d[2] - ball.d[2] * c];
        const pxx = dot(o2, ball.right) / ball.sinR, pyy = dot(o2, ball.up) / ball.sinR;
        const r2 = pxx * pxx + pyy * pyy;
        if (r2 > 1) continue;
        const nz = Math.sqrt(Math.max(0, 1 - r2));
        const diff = Math.max(0, pxx * LIGHT[0] + pyy * LIGHT[1] + nz * LIGHT[2]);
        const shade = ball.amb + ball.dif * diff;
        const sh = Math.max(0, pxx * HALF[0] + pyy * HALF[1] + nz * HALF[2]);
        const spec = Math.pow(sh, 96) * 0.8 + Math.pow(sh, 20) * 0.1;
        const rim = Math.pow(1 - nz, 3.2);
        let cr = ball.color[0] * shade + rim * 70 + spec * 185;
        let cg = ball.color[1] * shade + rim * 70 + spec * 185;
        let cb = ball.color[2] * shade + rim * 70 + spec * 185;
        const a = ball.alpha;
        r += (cr - r) * a; g += (cg - g) * a; b += (cb - b) * a;
      }
      const o = (y * w + x) * 3;
      img[o] = clamp(r, 0, 255); img[o + 1] = clamp(g, 0, 255); img[o + 2] = clamp(b, 0, 255);
    }
  }
  writePNG(file, w, h, img);
}

/* ------------------------------------------------------------ cube check
 * The shading is a pure function of direction, so seams can only come from
 * the six dir()/faceCoords() pairs disagreeing about which patch of sky each
 * face holds. Two properties settle that:
 *   1. round trip - every (face, a, b) maps to a direction that maps back to
 *      the same (a, b);
 *   2. exact cover - every direction lands inside exactly one face.
 * If both hold, the six faces tile the sphere once with no gap and no
 * overlap, which is the definition of a seamless cubemap. */
function cubeCheck() {
  let worstRoundTrip = 0, badCover = 0, samples = 0;
  const g = makeRng(4242);

  for (const f of FACES) {
    for (let i = 0; i < 4000; i++) {
      const a = g() * 2 - 1, b = g() * 2 - 1;
      const fc = faceCoords(f, norm(f.dir(a, b)));
      if (!fc) { badCover++; continue; }
      worstRoundTrip = Math.max(worstRoundTrip, Math.abs(fc[0] - a), Math.abs(fc[1] - b));
    }
  }

  for (let i = 0; i < 30000; i++) {
    /* uniform point on the sphere */
    const z = g() * 2 - 1, th = g() * TAU, s = Math.sqrt(1 - z * z);
    const d = [s * Math.cos(th), z, s * Math.sin(th)];
    let hits = 0;
    for (const f of FACES) {
      const fc = faceCoords(f, d);
      if (fc && Math.abs(fc[0]) <= 1 + 1e-9 && Math.abs(fc[1]) <= 1 + 1e-9) hits++;
    }
    samples++;
    if (hits !== 1) badCover++;
  }
  return { worstRoundTrip, badCover, samples };
}

/* -------------------------------------------------------------------- go */

console.log("Bubblegum Noon -> " + S + "px faces (" + S * 3 + "x" + S * 2 + " atlas)");
console.log("  " + PUFFS.length + " cloud puffs, " + BALLS.length + " gumballs, " + SPARKS.length + " sparkles");

const cc = cubeCheck();
console.log("  cube check: round-trip error " + cc.worstRoundTrip.toExponential(2) +
            ", " + cc.badCover + " bad of " + cc.samples + " coverage samples");
if (cc.worstRoundTrip > 1e-4 || cc.badCover > 0) {
  console.error("  FACE MAPPING IS WRONG - refusing to render a seamed atlas");
  process.exit(1);
}

const t0 = Date.now();
const { img, AW, AH } = render();
writePNG(path.join(OUT, "bubblegum_noon.png"), AW, AH, img);
console.log("  atlas written in " + ((Date.now() - t0) / 1000).toFixed(1) + "s");

preview(path.join(OUT, "preview_west.png"), 262, 8, 1280, 720, 50);
preview(path.join(OUT, "preview_up.png"), 40, 34, 1280, 720, 50);
preview(path.join(OUT, "pack.png"), 262, 6, 128, 128, 58);
console.log("  previews and pack icon written");
