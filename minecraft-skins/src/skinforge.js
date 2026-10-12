/*
 * SkinForge — procedurele generator voor Minecraft-skins (64×64).
 *
 * - 5 kerstversies van een bestaande skin: de eigen skin blijft staan
 *   en krijgt kerstaccessoires (muts, sjaal, lichtjes, gewei, kersttrui
 *   in de eigen shirtkleuren), zodat de speler herkenbaar blijft.
 * - 5 natuur/bladeren-skins die geen basis nodig hebben.
 *
 * Werkt in de browser (window.SkinForge) en in Node (require).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.SkinForge = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ------------------------------------------------------------------
  // Kleur
  // ------------------------------------------------------------------
  function hex(h) {
    h = h.replace("#", "");
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16), 255];
  }
  function toHex(c) {
    return "#" + [0, 1, 2].map((k) => Math.round(c[k]).toString(16).padStart(2, "0")).join("");
  }
  function mix(a, b, t) {
    return [
      Math.round(a[0] + (b[0] - a[0]) * t),
      Math.round(a[1] + (b[1] - a[1]) * t),
      Math.round(a[2] + (b[2] - a[2]) * t),
      255,
    ];
  }
  function rgb2hsl(c) {
    const r = c[0] / 255, g = c[1] / 255, b = c[2] / 255;
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
    const l = (mx + mn) / 2;
    if (mx === mn) return [0, 0, l];
    const d = mx - mn;
    const s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
    let h;
    if (mx === r) h = (g - b) / d + (g < b ? 6 : 0);
    else if (mx === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    return [h * 60, s, l];
  }
  function hsl2rgb(h, s, l) {
    h = ((h % 360) + 360) % 360;
    const c = (1 - Math.abs(2 * l - 1)) * s;
    const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    const m = l - c / 2;
    let r = 0, g = 0, b = 0;
    if (h < 60) [r, g, b] = [c, x, 0];
    else if (h < 120) [r, g, b] = [x, c, 0];
    else if (h < 180) [r, g, b] = [0, c, x];
    else if (h < 240) [r, g, b] = [0, x, c];
    else if (h < 300) [r, g, b] = [x, 0, c];
    else [r, g, b] = [c, 0, x];
    return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255), 255];
  }
  function hueToward(h, target, deg) {
    let diff = ((target - h + 540) % 360) - 180;
    if (Math.abs(diff) < deg) return target;
    return h + Math.sign(diff) * deg;
  }
  // Pixel-art schaduw: donkerder schuift naar koel (blauw/paars),
  // lichter schuift naar warm (geel). amt in [-1, 1].
  function shade(c, amt) {
    if (!amt) return c;
    const [h, s, l] = rgb2hsl(c);
    if (amt < 0) {
      return hsl2rgb(hueToward(h, 250, -amt * 22), Math.min(1, s * (1 - amt * 0.12)), Math.max(0, l * (1 + amt)));
    }
    return hsl2rgb(hueToward(h, 55, amt * 18), s * (1 - amt * 0.25), Math.min(1, l + (1 - l) * amt));
  }

  // ------------------------------------------------------------------
  // Ruis (deterministisch)
  // ------------------------------------------------------------------
  function hash(x, y, s) {
    let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(s | 0, 982451653);
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  }
  function vnoise(x, y, s) {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const a = hash(xi, yi, s), b = hash(xi + 1, yi, s);
    const c = hash(xi, yi + 1, s), d = hash(xi + 1, yi + 1, s);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }

  // ------------------------------------------------------------------
  // Skin-buffer
  // ------------------------------------------------------------------
  class Skin {
    constructor(data) {
      this.width = 64;
      this.height = 64;
      this.data = new Uint8ClampedArray(64 * 64 * 4);
      if (data) this.data.set(data);
    }
    get(x, y) {
      const i = (y * 64 + x) * 4, d = this.data;
      return [d[i], d[i + 1], d[i + 2], d[i + 3]];
    }
    alpha(x, y) {
      return this.data[(y * 64 + x) * 4 + 3];
    }
    set(x, y, c) {
      if (x < 0 || y < 0 || x > 63 || y > 63) return;
      const i = (y * 64 + x) * 4, d = this.data;
      if (c == null) {
        d[i] = d[i + 1] = d[i + 2] = d[i + 3] = 0;
        return;
      }
      d[i] = c[0];
      d[i + 1] = c[1];
      d[i + 2] = c[2];
      d[i + 3] = c[3] == null ? 255 : c[3];
    }
    clearRect(x, y, w, h) {
      for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) this.set(i, j, null);
    }
    clone() {
      return new Skin(this.data);
    }
  }

  // ------------------------------------------------------------------
  // UV-indeling
  // ------------------------------------------------------------------
  const PARTS = {
    head: { b: [0, 0], o: [32, 0], w: 8, h: 8, d: 8 },
    body: { b: [16, 16], o: [16, 32], w: 8, h: 12, d: 4 },
    rarm: { b: [40, 16], o: [40, 32], w: 4, h: 12, d: 4, arm: true },
    larm: { b: [32, 48], o: [48, 48], w: 4, h: 12, d: 4, arm: true },
    rleg: { b: [0, 16], o: [0, 32], w: 4, h: 12, d: 4 },
    lleg: { b: [16, 48], o: [0, 48], w: 4, h: 12, d: 4 },
  };
  const FACE_NAMES = ["top", "bottom", "right", "front", "left", "back"];

  function geom(part, slim) {
    const p = PARTS[part];
    return Object.assign({}, p, { w: p.arm && slim ? 3 : p.w });
  }
  function faceRects(g, layer) {
    const [u, v] = layer === "o" ? g.o : g.b;
    const { w, h, d } = g;
    return {
      top: { x: u + d, y: v, w, h: d },
      bottom: { x: u + d + w, y: v, w, h: d },
      right: { x: u, y: v + d, w: d, h },
      front: { x: u + d, y: v + d, w, h },
      left: { x: u + d + w, y: v + d, w: d, h },
      back: { x: u + d + w + d, y: v + d, w, h },
    };
  }

  // Schildert één onderdeel. fn(info) → kleur, null (wissen) of undefined (laten staan).
  // info.s is de positie rondom het onderdeel (rechts → voor → links → achter),
  // zodat patronen naadloos om armen en benen lopen.
  function paint(skin, slim, part, layer, fn, only) {
    const g = geom(part, slim);
    const rects = faceRects(g, layer);
    const P = 2 * (g.w + g.d);
    const ringOff = { right: 0, front: g.d, left: g.d + g.w, back: 2 * g.d + g.w };
    const outerFace = part === "rarm" || part === "rleg" ? "right" : part === "larm" || part === "lleg" ? "left" : null;
    const innerFace = outerFace === "right" ? "left" : outerFace === "left" ? "right" : null;
    // dezelfde pixel op de andere laag (basis <-> tweede laag)
    const [tx, ty] = layer === "o" ? [g.b[0] - g.o[0], g.b[1] - g.o[1]] : [g.o[0] - g.b[0], g.o[1] - g.b[1]];
    for (const face of only || FACE_NAMES) {
      const r = rects[face];
      for (let y = 0; y < r.h; y++) {
        for (let x = 0; x < r.w; x++) {
          const X = r.x + x, Y = r.y + y;
          const info = {
            part, layer, face, x, y, w: r.w, h: r.h, X, Y, g, P,
            s: face in ringOff ? ringOff[face] + x : -1,
            side: face === "right" || face === "left",
            outer: face === outerFace,
            inner: face === innerFace,
            cur: skin.get(X, Y),
            twin: skin.get(X + tx, Y + ty),
          };
          const c = fn(info);
          if (c !== undefined) skin.set(X, Y, c);
        }
      }
    }
  }

  // ------------------------------------------------------------------
  // Invoer normaliseren (64×32 legacy, HD-skins, slim-detectie)
  // ------------------------------------------------------------------
  function mirrorPart(skin, from, to, layerFrom, layerTo) {
    const gf = geom(from, false), gt = geom(to, false);
    const rf = faceRects(gf, layerFrom), rt = faceRects(gt, layerTo);
    const map = { top: "top", bottom: "bottom", front: "front", back: "back", right: "left", left: "right" };
    for (const face of FACE_NAMES) {
      const src = rf[map[face]], dst = rt[face];
      for (let y = 0; y < dst.h; y++)
        for (let x = 0; x < dst.w; x++) skin.set(dst.x + x, dst.y + y, skin.get(src.x + (src.w - 1 - x), src.y + y));
    }
  }

  function fromImageData(img) {
    const { width, height, data } = img;
    const s = new Skin();
    const scale = width / 64;
    const rows = height === width / 2 ? 32 : 64;
    for (let y = 0; y < rows; y++)
      for (let x = 0; x < 64; x++) {
        const i = (Math.floor(y * scale) * width + Math.floor(x * scale)) * 4;
        s.set(x, y, [data[i], data[i + 1], data[i + 2], data[i + 3]]);
      }
    if (rows === 32) {
      // Oud formaat: linkerarm/-been zijn spiegelingen, hoed-laag vaak volledig gevuld.
      mirrorPart(s, "rleg", "lleg", "b", "b");
      mirrorPart(s, "rarm", "larm", "b", "b");
      let opaque = true;
      for (let y = 0; y < 16 && opaque; y++) for (let x = 32; x < 64; x++) if (s.alpha(x, y) < 128) { opaque = false; break; }
      if (opaque) s.clearRect(32, 0, 32, 16);
    }
    return s;
  }

  function areaIs(skin, x, y, w, h, test) {
    for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) if (!test(skin.get(i, j))) return false;
    return true;
  }
  function detectSlim(skin) {
    const transparent = (c) => c[3] === 0;
    const black = (c) => c[0] === 0 && c[1] === 0 && c[2] === 0;
    const white = (c) => c[0] === 255 && c[1] === 255 && c[2] === 255;
    const check = (t) => areaIs(skin, 50, 16, 2, 4, t) && areaIs(skin, 54, 20, 2, 12, t) && areaIs(skin, 42, 48, 2, 4, t) && areaIs(skin, 46, 52, 2, 12, t);
    return check(transparent) || check(black) || check(white);
  }

  // ------------------------------------------------------------------
  // Analyse van de basis-skin
  // ------------------------------------------------------------------
  function dominant(skin, rects, exclude) {
    const buckets = new Map();
    for (const [x0, y0, w, h] of rects)
      for (let y = y0; y < y0 + h; y++)
        for (let x = x0; x < x0 + w; x++) {
          const c = skin.get(x, y);
          if (c[3] < 200) continue;
          if (exclude && exclude.some((e) => dist(e, c) < 40)) continue;
          const k = (c[0] >> 4) * 256 + (c[1] >> 4) * 16 + (c[2] >> 4);
          const b = buckets.get(k) || { n: 0, r: 0, g: 0, b: 0 };
          b.n++; b.r += c[0]; b.g += c[1]; b.b += c[2];
          buckets.set(k, b);
        }
    let best = null;
    for (const b of buckets.values()) if (!best || b.n > best.n) best = b;
    return best ? [Math.round(best.r / best.n), Math.round(best.g / best.n), Math.round(best.b / best.n), 255] : null;
  }
  function dist(a, b) {
    return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]);
  }

  function analyze(skin) {
    const slim = detectSlim(skin);
    const hair = dominant(skin, [[8, 0, 8, 8]]) || hex("#4a3020");
    let tone = dominant(skin, [[9, 11, 6, 5]], [hair]) || dominant(skin, [[8, 8, 8, 8]]) || hex("#c99a76");
    const shirt = dominant(skin, [[20, 20, 8, 12], [20, 36, 8, 12]]) || hex("#3d6fb6");
    const pants = dominant(skin, [[4, 20, 4, 8], [20, 52, 4, 8]]) || hex("#2d3550");
    const [, sat, l] = rgb2hsl(shirt);
    const accent = sat > 0.32 && l > 0.16 && l < 0.7 ? shirt : null;
    return { slim, hair, tone, shirt, pants, accent };
  }

  // ------------------------------------------------------------------
  // Gedeelde schildertechnieken
  // ------------------------------------------------------------------
  // Stof: licht van boven, donkerder naar beneden en aan de achterkant.
  function cloth(c, i, seed, grain) {
    let t;
    if (i.face === "top") t = 0.1;
    else if (i.face === "bottom") t = -0.3;
    else t = 0.07 - (i.y / Math.max(1, i.h - 1)) * 0.16;
    if (i.face === "back") t -= 0.05;
    if (i.side) t -= 0.03;
    t += (hash(i.X, i.Y, seed) - 0.5) * (grain == null ? 0.07 : grain);
    return shade(c, t);
  }
  // Pluizig bont (kraagjes, kerstmuts, baard).
  const FUR = hex("#f4f1ea");
  function fur(i, seed, edgeShadow) {
    const n = hash(i.X, i.Y, seed);
    let t = n < 0.22 ? -0.13 : n > 0.82 ? 0.08 : -0.02;
    if (edgeShadow) t -= 0.12;
    if (i.face === "bottom") t -= 0.12;
    return shade(FUR, t);
  }
  // Metaal: verloop + glimlicht linksboven.
  function metal(c, lx, ly, w, h) {
    if (lx === 0 && ly === 0) return shade(c, 0.45);
    const t = 0.15 - ((lx / Math.max(1, w - 1)) * 0.2 + (ly / Math.max(1, h - 1)) * 0.25);
    return shade(c, t);
  }

  const P = (s, A) => (part, layer, fn, only) => paint(s, A.slim, part, layer, fn, only);
  const ARMS = ["rarm", "larm"], LEGS = ["rleg", "lleg"];

  // De kerstversies laten de eigen skin staan: alleen accessoires komen erbij,
  // meestal op de tweede laag. Zo blijft de speler herkenbaar.
  const XR = hex("#c8102e"), XG = hex("#1f7a3a"), XGOLD = hex("#e8b33c"), CREAM = hex("#f3efe4");
  const SNOW = [hex("#ffffff"), hex("#eef4fa"), hex("#d6e3ef"), hex("#b9cde0")];
  const snowPx = (i, seed, under) => {
    const n = hash(i.X, i.Y, seed);
    return n > 0.88 ? SNOW[0] : n > 0.4 ? SNOW[1] : under ? SNOW[3] : SNOW[2];
  };
  // Is dit de laag die je echt ziet? (de tweede laag wint als die gevuld is)
  const isTop = (i) => (i.layer === "o" ? i.cur[3] > 0 : i.twin[3] === 0);

  // Rij waar de hand begint (eerste rij die vooral huidskleur heeft)
  function sleeveEnd(skin, A, arm) {
    const g = geom(arm, A.slim), fb = faceRects(g, "b").front, fo = faceRects(g, "o").front;
    for (let y = 0; y < 12; y++) {
      let n = 0;
      for (let x = 0; x < fb.w; x++) {
        const o = skin.get(fo.x + x, fo.y + y);
        const c = o[3] > 0 ? o : skin.get(fb.x + x, fb.y + y);
        if (dist(c, A.tone) < 45) n++;
      }
      if (n * 2 > fb.w) return y;
    }
    return 12;
  }
  function cuffRow(skin, A, arm) {
    const e = sleeveEnd(skin, A, arm);
    if (e >= 2 && e <= 11) return e - 1;
    return e === 12 ? 9 : -1;
  }
  // Breiwerk-kleur die past bij de speler: de shirtkleur als die uitgesproken is
  function knitColor(A) {
    const [h, sat, l] = rgb2hsl(A.shirt);
    if (sat > 0.25 && l > 0.15 && l < 0.75) return hsl2rgb(h, Math.max(0.45, Math.min(0.8, sat)), Math.max(0.3, Math.min(0.5, l)));
    return XR;
  }
  const knitPx = (c, i) => shade(c, (((i.s >= 0 ? i.s : i.x) & 1) ? -0.08 : 0.03) + (hash(i.X, i.Y, 7) - 0.5) * 0.05);

  // Kerstmuts op de hoed-laag (voorkant 1 rij bont, zodat het gezicht vrij blijft)
  function paintSantaHat(p) {
    const velvet = (i, seed) => shade(cloth(XR, i, seed, 0.09), hash(i.X, i.Y, seed + 3) > 0.9 ? 0.1 : 0);
    p("head", "o", (i) => {
      if (i.face === "bottom") return undefined;
      if (i.face === "top") return shade(velvet(i, 21), 0.12 - (7 - i.y) * 0.03 + (i.y === 3 ? -0.18 : 0));
      if (i.y <= 1) return shade(velvet(i, 22), i.y === 1 ? -0.04 : 0.04);
      if (i.y === 2) return fur(i, 23, false);
      if (i.y === 3 && i.face !== "front") return fur(i, 24, hash(i.X, i.Y, 5) > 0.5);
      return undefined;
    });
    p("head", "o", (i) => {
      const tail = { 0: [3, 6], 1: [3, 6], 2: [4, 6], 3: [4, 6], 4: [4, 5] }[i.y];
      if (tail && i.x >= tail[0] && i.x <= tail[1]) return shade(velvet(i, 25), (i.x === tail[1] ? -0.25 : i.x === tail[0] ? 0.08 : 0) - i.y * 0.03);
      const pom = { 5: [4, 5], 6: [3, 6], 7: [4, 5] }[i.y];
      if (pom && i.x >= pom[0] && i.x <= pom[1]) return fur(i, 26, i.y === 7 || i.x === 6);
      return undefined;
    }, ["back"]);
  }
  // Rood lint om de hals met een gouden belletje
  function paintBellCollar(p) {
    p("body", "o", (i) => {
      if (i.face === "top") return i.y === 0 || i.y === 3 || i.x === 0 || i.x === 7 ? shade(XR, i.y === 0 ? 0.05 : -0.05) : undefined;
      if (i.face === "bottom") return undefined;
      if (i.y === 0) return shade(XR, i.s % 3 === 0 ? -0.12 : 0.02);
      if (i.face === "front") {
        if (i.y === 1 && (i.x === 2 || i.x === 5)) return shade(XR, -0.08); // strikje
        if (i.y === 1 && (i.x === 3 || i.x === 4)) return metal(XGOLD, i.x - 3, 0, 2, 3);
        if (i.y === 2 && (i.x === 3 || i.x === 4)) return i.x === 3 ? hex("#5b3f12") : shade(XGOLD, -0.25);
      }
      return undefined;
    });
  }

  // ------------------------------------------------------------------
  // KERST 1 — Kerstmuts
  // ------------------------------------------------------------------
  function santaHat(base) {
    const A = analyze(base);
    const s = base.clone(), p = P(s, A);
    paintSantaHat(p);
    // bontkraag
    p("body", "o", (i) => {
      if (i.face === "top") return i.y === 0 || i.y === 3 || i.x === 0 || i.x === 7 ? fur(i, 31, false) : undefined;
      if (i.face === "bottom") return undefined;
      if (i.y === 0) return fur(i, 32, hash(i.X, i.Y, 6) > 0.7);
      return undefined;
    });
    // hulsttakje op de borst
    p("body", "o", (i) => {
      const H = { "5,1": "#1d5e2a", "6,1": "#2f8a3b", "5,2": "#2f8a3b", "6,2": "#e02c34", "5,3": "#c41f2e", "6,3": "#1d5e2a" }[i.x + "," + i.y];
      return H ? hex(H) : undefined;
    }, ["front"]);
    // bontmanchetten aan het eind van de mouwen
    for (const arm of ARMS) {
      const r = cuffRow(s, A, arm);
      if (r < 0) continue;
      p(arm, "o", (i) => (i.face !== "top" && i.face !== "bottom" && i.y === r ? fur(i, 33, false) : undefined));
    }
    return s;
  }

  // ------------------------------------------------------------------
  // KERST 2 — Winterwarm: muts, sjaal, wanten en sneeuw
  // ------------------------------------------------------------------
  function winter(base) {
    const A = analyze(base);
    const s = base.clone(), p = P(s, A);
    const K = knitColor(A);
    const scarfA = dist(K, XR) < 80 ? XG : XR;
    // muts met pompon en sneeuw
    p("head", "o", (i) => {
      if (i.face === "bottom") return undefined;
      if (i.face === "top") {
        const dx = i.x - 3.5, dy = i.y - 3.5, r = dx * dx + dy * dy;
        if (r < 4.6) return fur(i, 41, r > 2.5 && (dx > 0 || dy > 0));
        if ((i.x === 0 || i.y === 0 || i.x === 7 || i.y === 7) && hash(i.X, i.Y, 42) > 0.55) return snowPx(i, 43);
        return knitPx(K, i);
      }
      if (i.y === 0) return hash(i.X, i.Y, 44) > 0.8 ? snowPx(i, 45) : knitPx(K, i);
      if (i.y === 1) return i.s % 3 === 1 ? shade(CREAM, -0.02) : knitPx(K, i);
      if (i.y === 2) return shade(K, (i.s & 1) ? -0.24 : -0.1); // omgeslagen boord
      return undefined;
    });
    // gestreepte sjaal om de hals, uiteinde hangt voor
    const scarf = (u) => (Math.floor(u / 2) & 1 ? shade(CREAM, -0.03) : scarfA);
    p("body", "o", (i) => {
      if (i.face === "top") return i.y === 0 || i.y === 3 || i.x === 0 || i.x === 7 ? scarf(i.x + i.y) : undefined;
      if (i.face === "bottom") return undefined;
      if (i.y <= 1) return shade(scarf(i.s), i.y === 1 ? -0.1 : 0.02);
      if (i.face === "front" && (i.x === 1 || i.x === 2)) {
        if (i.y <= 7) return shade(scarf(i.y), i.x === 2 ? -0.12 : 0);
        if (i.y === 8) return (i.x + i.y) & 1 ? shade(scarfA, -0.2) : undefined; // franje
      }
      return undefined;
    });
    // wanten met witte rand
    for (const arm of ARMS) {
      p(arm, "b", (i) => (i.y >= 10 || i.face === "bottom" ? knitPx(shade(K, i.face === "bottom" ? -0.2 : 0), i) : undefined));
      p(arm, "o", (i) => {
        if (i.face === "top") return snowPx(i, 46); // sneeuw op de schouders
        if (i.face === "bottom") return knitPx(shade(K, -0.2), i);
        if (i.y === 0 && !i.inner && hash(i.X, i.Y, 47) > 0.45) return snowPx(i, 48, true);
        if (i.y === 9) return fur(i, 49, false);
        if (i.y >= 10) return knitPx(K, i);
        return undefined;
      });
    }
    // sneeuw rond de schoenen
    for (const leg of LEGS)
      p(leg, "o", (i) => (i.face !== "top" && i.face !== "bottom" && i.y === 11 && hash(i.X, i.Y, 51) > 0.45 ? snowPx(i, 52, true) : undefined));
    return s;
  }

  // ------------------------------------------------------------------
  // KERST 3 — Kerstlichtjes
  // ------------------------------------------------------------------
  function lights(base) {
    const A = analyze(base);
    const s = base.clone(), p = P(s, A);
    const BULBS = ["#ff3b3b", "#ffd23f", "#3ddc5a", "#3fa9ff", "#ff5ad1"].map(hex);
    const WIRE = hex("#173a22");
    const bulb = (k, i) => shade(BULBS[((k % 5) + 5) % 5], hash(i.X, i.Y, 61) > 0.5 ? 0.25 : 0.05);
    const SWAG = [0, 1, 2, 2, 1, 0];
    // twee slingers rond de romp
    p("body", "o", (i) => {
      if (i.face === "top" || i.face === "bottom") return undefined;
      for (const [row, shift] of [[1, 0], [7, 3]]) {
        const ph = (i.s + shift) % 6, wy = row + SWAG[ph];
        if (i.y === wy) return WIRE;
        if (i.y === wy + 1 && (ph === 1 || ph === 4)) return bulb(Math.floor(i.s / 3) + shift, i);
      }
      return undefined;
    });
    // spiraal om de armen (tot aan de hand)
    for (const arm of ARMS) {
      const end = Math.min(10, sleeveEnd(s, A, arm));
      p(arm, "o", (i) => {
        if (i.face === "top" || i.face === "bottom" || i.y >= end) return undefined;
        const step = Math.floor((4 * i.s) / i.P);
        if ((((i.y - step) % 4) + 4) % 4 !== 0) return undefined;
        return i.s % 3 === 1 ? bulb(i.s + i.y, i) : WIRE;
      });
    }
    // lichtjeskrans om het hoofd, ster bovenop
    p("head", "o", (i) => {
      if (i.face === "bottom") return undefined;
      if (i.face === "top") {
        const STAR = ["...Y....", "..YYY...", "YYYWYYY.", ".YYYYY..", ".YY.YY..", "Y.....Y."];
        const ch = (STAR[i.y - 1] || "")[i.x];
        if (ch === "Y") return shade(XGOLD, i.y < 3 ? 0.15 : -0.05);
        if (ch === "W") return hex("#fff6c8");
        return undefined;
      }
      if (i.y === 0) return i.s % 3 === 1 ? bulb(i.s, i) : WIRE;
      return undefined;
    });
    return s;
  }

  // ------------------------------------------------------------------
  // KERST 4 — Rendier: gewei, rode neus, belletje
  // ------------------------------------------------------------------
  function reindeer(base) {
    const A = analyze(base);
    const s = base.clone(), p = P(s, A);
    const ANT = hex("#d8bf87"), EAR = hex("#7d4b2a"), NOSE = hex("#e3202b");
    const ANT_TOP = ["........", ".a....a.", "aa....aa", ".a....a.", ".aa..aa.", "..a..a..", "........", "........"];
    p("head", "o", (i) => (ANT_TOP[i.y][i.x] === "a" ? shade(ANT, i.y > 3 ? -0.08 : 0.08) : undefined), ["top"]);
    p("head", "o", (i) => {
      const bx = i.face === "right" ? i.x : 7 - i.x; // 0 = achterkant
      const SIDE = ["a.a.a...", ".aaa....", "..aa.ee.", "...aeEe.", "....ee.."];
      const ch = (SIDE[i.y] || "")[bx];
      if (ch === "a") return shade(ANT, -0.05 * i.y + (hash(i.X, i.Y, 7) > 0.6 ? 0.1 : 0));
      if (ch === "e") return shade(EAR, bx === 6 ? 0.05 : -0.12);
      if (ch === "E") return mix(hex("#d98b8b"), EAR, 0.25);
      return undefined;
    }, ["right", "left"]);
    p("head", "o", (i) => (i.y === 5 && (i.x === 3 || i.x === 4) ? (i.x === 3 ? shade(NOSE, 0.3) : NOSE) : undefined), ["front"]);
    paintBellCollar(p);
    // wit staartje
    p("body", "o", (i) => {
      const t = { 9: [3, 4], 10: [2, 5], 11: [3, 4] }[i.y];
      return t && i.x >= t[0] && i.x <= t[1] ? fur(i, 71, i.y === 11) : undefined;
    }, ["back"]);
    return s;
  }

  // ------------------------------------------------------------------
  // KERST 5 — Eigen shirt omgebreid tot kersttrui
  // ------------------------------------------------------------------
  function sweater(base) {
    const A = analyze(base);
    const s = base.clone(), p = P(s, A);
    // de stofkleuren van het eigen shirt
    const g = geom("body", false), fb = faceRects(g, "b").front, fo = faceRects(g, "o").front;
    const seen = new Skin();
    for (let y = 0; y < 12; y++)
      for (let x = 0; x < 8; x++) {
        const o = s.get(fo.x + x, fo.y + y);
        seen.set(fb.x + x, fb.y + y, o[3] > 0 ? o : s.get(fb.x + x, fb.y + y));
      }
    const c1 = dominant(seen, [[fb.x, fb.y, 8, 12]], [A.tone]) || A.shirt;
    const c2 = dominant(seen, [[fb.x, fb.y, 8, 12]], [A.tone, c1]);
    const cols = c2 ? [c1, c2] : [c1];
    const fabric = (c) => c[3] > 0 && cols.some((k) => dist(k, c) < 70) && dist(c, A.tone) > 45;
    const [hue, , light] = rgb2hsl(c1);
    const W = light > 0.72 ? hex("#b3172b") : CREAM;
    const reddish = hue < 20 || hue > 330, greenish = hue > 75 && hue < 170;
    const C2 = reddish ? XG : XR;
    const TREE_C = greenish ? CREAM : XG;
    const TREE = ["...YY...", "...GG...", "..GRGG..", "..GGGG..", ".GYGGRG.", ".GGRGGG.", "...TT..."];
    const FLAKE = ["W..W..W", ".W.W.W.", "..WWW..", "WWW.WWW", "..WWW..", ".W.W.W.", "W..W..W"];
    const pattern = (i) => {
      if (i.face === "top" || i.face === "bottom") return null;
      if (i.y === 0) return shade(i.cur, (i.s & 1) ? -0.2 : 0.02); // boord
      if (i.y === 1) return i.s % 2 === 0 ? W : null;
      if (i.y === 9) return i.s % 4 === 1 ? C2 : null;
      if (i.y === 10) return i.s % 4 === 0 || i.s % 4 === 2 ? C2 : null;
      if (i.face === "front") {
        const ch = (TREE[i.y - 2] || "")[i.x];
        if (ch === "Y") return shade(XGOLD, i.y === 2 && i.x === 3 ? 0.3 : 0);
        if (ch === "G") return knitPx(TREE_C, i);
        if (ch === "R") return reddish ? XGOLD : XR;
        if (ch === "T") return hex("#6b4226");
      }
      if (i.face === "back" && (FLAKE[i.y - 2] || "")[i.x - 1] === "W") return W;
      if (i.side && (i.y === 4 || i.y === 6) && ((i.x + (i.y === 6 ? 1 : 0)) & 1)) return W;
      return null;
    };
    const knitBody = (i) => {
      if (!isTop(i) || !fabric(i.cur)) return undefined;
      return pattern(i) || knitPx(i.cur, i);
    };
    p("body", "b", knitBody);
    p("body", "o", knitBody);
    for (const arm of ARMS) {
      const end = sleeveEnd(s, A, arm);
      const sleeve = (i) => {
        if (!isTop(i) || !fabric(i.cur) || i.y >= end) return undefined;
        if (i.face === "top" || i.face === "bottom") return knitPx(i.cur, i);
        if (i.y === end - 1 && end < 12) return shade(i.cur, (i.s & 1) ? -0.22 : 0); // manchet
        if (i.y === 1) return i.s % 2 === 0 ? W : knitPx(i.cur, i);
        if (i.y === 3) return i.s % 4 === 1 ? C2 : knitPx(i.cur, i);
        if (i.y === 4) return i.s % 4 === 0 || i.s % 4 === 2 ? C2 : knitPx(i.cur, i);
        if (i.y === 6) return i.s % 4 === 2 ? W : knitPx(i.cur, i);
        return knitPx(i.cur, i);
      };
      p(arm, "b", sleeve);
      p(arm, "o", sleeve);
    }
    // sneeuwvlokje in het haar
    p("head", "o", (i) => {
      const F = { "1,1": 1, "0,0": 1, "2,0": 1, "0,2": 1, "2,2": 1 }[(i.x - 4) + "," + (i.y - 0)];
      return F ? (i.x === 5 && i.y === 1 ? SNOW[0] : SNOW[2]) : undefined;
    }, ["right"]);
    return s;
  }

  // ------------------------------------------------------------------
  // Neutrale voorbeeldbasis (geen echte speler)
  // ------------------------------------------------------------------
  function exampleBase() {
    const s = new Skin(), p = P(s, { slim: false });
    const SKIN = hex("#c99b78"), HAIR = hex("#4b2f1f"), EYE = hex("#3f6fb5"), TEE = hex("#5d6b78"), JEAN = hex("#2f3d5c"), SHOE = hex("#3b3433");
    p("head", "b", (i) => {
      let c = shade(SKIN, i.face === "back" ? -0.05 : i.side ? -0.03 : 0);
      const hairRows = i.face === "front" ? 1 : i.face === "back" ? 6 : i.side ? 3 : 8;
      if (i.face === "top" || i.y < hairRows) c = shade(HAIR, (hash(i.X, i.Y, 1) - 0.5) * 0.15);
      if (i.side && i.y === 3 && i.face === "right" && i.x < 5) c = shade(HAIR, -0.05);
      if (i.side && i.y === 3 && i.face === "left" && i.x > 2) c = shade(HAIR, -0.05);
      if (i.face === "front") {
        if (i.y === 1 && (i.x === 0 || i.x === 7 || i.x === 1)) c = HAIR;
        if (i.y === 3 && (i.x === 1 || i.x === 2 || i.x === 5 || i.x === 6)) c = shade(HAIR, 0.05);
        if (i.y === 4 && (i.x === 1 || i.x === 6)) c = hex("#f2f2f2");
        if (i.y === 4 && (i.x === 2 || i.x === 5)) c = EYE;
        if (i.y === 5 && (i.x === 3 || i.x === 4)) c = shade(SKIN, -0.12);
        if (i.y === 6 && i.x >= 2 && i.x <= 5) c = shade(hex("#9a5b4b"), i.x === 2 || i.x === 5 ? 0.1 : 0);
      }
      if (i.face === "bottom") c = shade(SKIN, -0.15);
      return c;
    });
    p("body", "b", (i) => cloth(TEE, i, 5));
    for (const arm of ARMS) p(arm, "b", (i) => (i.y < 4 && i.face !== "bottom" ? cloth(TEE, i, 6) : shade(SKIN, i.side ? -0.04 : 0)));
    for (const leg of LEGS) p(leg, "b", (i) => (i.y < 10 && i.face !== "bottom" ? cloth(JEAN, i, 7) : shade(SHOE, i.y === 11 ? -0.15 : 0)));
    return s;
  }

  // ------------------------------------------------------------------
  // NATUUR — bladwezens
  // ------------------------------------------------------------------
  const LEAF_THEMES = {
    eik: {
      leaf: ["#1d4614", "#2c6a1f", "#3f8a2b", "#5ca83b", "#86c95a"],
      bark: ["#3b2716", "#563a20", "#71502e", "#8c6a43"],
      moss: "#5f8a2c", glow: ["#9b6a12", "#f2b632", "#fff2a8"], seed: 11,
    },
    herfst: {
      leaf: ["#5e1a0c", "#9a2f12", "#cf5a1c", "#ec8f2b", "#f7c75a"],
      leafAlt: ["#4a2a0e", "#7a4a16", "#a8701f", "#cf9a2c", "#ecc05a"],
      bark: ["#2d1f15", "#45301f", "#5e4430", "#7a5d43"],
      moss: "#7a7a2a", glow: ["#9a3a0a", "#ff8a2a", "#ffe0a0"], seed: 23,
    },
    bloesem: {
      leaf: ["#7e2c4f", "#b84d79", "#e083a5", "#f4b2c8", "#ffe2ec"],
      bark: ["#3a2224", "#56322f", "#714540", "#8e5c55"],
      moss: "#6a8a3a", glow: ["#a8487a", "#ffb3d6", "#fff4fa"], seed: 37,
    },
    azalea: {
      leaf: ["#253f15", "#3b5e20", "#55802d", "#73a03a", "#9cc35a"],
      bark: ["#3b2e1c", "#54432a", "#6e5b3a", "#887550"],
      flower: ["#6d1f78", "#a9349f", "#d65ccb", "#f29ae8"],
      moss: "#6b8f2c", glow: ["#6c2a8a", "#d48bff", "#f6e2ff"], seed: 41,
    },
    jungle: {
      leaf: ["#0f3311", "#1b4f1a", "#2a7024", "#3f9130", "#68b84a"],
      bark: ["#2f2416", "#4a3a24", "#634f33", "#7d6846"],
      vine: ["#1d4a19", "#2f6b23"], berry: ["#b45309", "#ff9d2e", "#ffe08a"],
      moss: "#3f7a2a", glow: ["#0f6f7a", "#4ff0ff", "#d8ffff"], seed: 53,
    },
  };

  function leafSkin(name) {
    const T = LEAF_THEMES[name];
    const leaf = T.leaf.map(hex), bark = T.bark.map(hex), glow = T.glow.map(hex), moss = hex(T.moss);
    const leafAlt = T.leafAlt ? T.leafAlt.map(hex) : null;
    const s = new Skin(), p = P(s, { slim: false });
    const seed = T.seed;

    // ring-coördinaat (naadloos rondom) of gewone x; bovenkant apart
    const U = (i) => (i.s >= 0 ? i.s : i.x + 100);
    const V = (i) => i.y + (i.face === "top" ? 200 : 0);
    const off = (i) => i.g.b[0] * 7 + i.g.b[1] * 3;

    // Bladclusters (Worley-ruis): elk cluster is een blaadje met licht
    // midden, glimlicht linksboven en een donkere rand.
    const cluster = (u, v, sd) => {
      const C = 3, cu = Math.floor(u / C), cv = Math.floor(v / C);
      let best = 1e9, bdx = 0, bdy = 0, id = 0;
      for (let j = -1; j <= 1; j++)
        for (let k = -1; k <= 1; k++) {
          const gx = cu + k, gy = cv + j;
          const px = (gx + hash(gx, gy, sd)) * C, py = (gy + hash(gx, gy, sd + 1)) * C;
          const dx = u + 0.5 - px, dy = v + 0.5 - py, d = Math.sqrt(dx * dx + dy * dy);
          if (d < best) { best = d; bdx = dx; bdy = dy; id = hash(gx, gy, sd + 2); }
        }
      return { d: best, dx: bdx, dy: bdy, id };
    };
    const leafColor = (i, sd, cl) => {
      cl = cl || cluster(U(i) + off(i), V(i), sd);
      let k = cl.d < 0.75 ? 3 : cl.d < 1.35 ? 2 : cl.d < 1.85 ? 1 : 0;
      if (cl.dx < -0.2 && cl.dy < -0.2 && cl.d < 1.5) k++;
      if (cl.id < 0.25) k--;
      if (i.face === "top") k++;
      if (i.face === "back" || i.face === "bottom") k--;
      if (hash(i.X, i.Y, sd + 9) > 0.93) k += 1;
      k = Math.max(0, Math.min(4, k));
      const ramp = leafAlt && cl.id > 0.62 ? leafAlt : leaf;
      return ramp[k];
    };
    // Bladlaag met gaten; dichtheid 0..1 (1 = vol)
    const leaves = (i, sd, density) => {
      const cl = cluster(U(i) + off(i), V(i), sd);
      if (cl.d > 0.85 + density * 1.35) return null;
      if (density < 0.9 && hash(i.X, i.Y, sd + 4) > 0.35 + density * 0.6) return null;
      return leafColor(i, sd, cl);
    };
    const barkPx = (i, sd) => {
      const u = U(i);
      const grain = vnoise(u * 1.4 + i.g.b[0], i.y * 0.22 + i.g.b[1], sd);
      let k = grain < 0.3 ? 0 : grain < 0.55 ? 1 : grain < 0.8 ? 2 : 3;
      if (vnoise(u * 2.1, i.y * 0.35, sd + 3) > 0.8) k = 0; // scheuren
      if (i.face === "top") k = Math.min(3, k + 1);
      if (i.face === "bottom") k = 0;
      let c = bark[k];
      if (vnoise(i.X * 0.4, i.Y * 0.4, sd + 7) > 0.76 && i.face !== "bottom") c = shade(moss, (k - 1.5) * 0.12);
      return c;
    };
    // Bloemetjes (plus-vorm) op willekeurige plekken
    const flowerAt = (i, sd, ramp, density) => {
      const u = U(i) + off(i), v = V(i), C = 4;
      const cu = Math.floor(u / C), cv = Math.floor(v / C);
      for (let j = -1; j <= 1; j++)
        for (let k = -1; k <= 1; k++) {
          const gx = cu + k, gy = cv + j;
          if (hash(gx, gy, sd) > density) continue;
          const ox = gx * C + 1 + Math.floor(hash(gx, gy, sd + 1) * 2), oy = gy * C + 1 + Math.floor(hash(gx, gy, sd + 2) * 2);
          const dx = u - ox, dy = v - oy;
          if (dx === 0 && dy === 0) return ramp[ramp.length - 1];
          if (Math.abs(dx) + Math.abs(dy) === 1) return dy < 0 || dx < 0 ? ramp[2] : ramp[1];
        }
      return null;
    };

    // ---- Hoofd: bast-gezicht ----
    p("head", "b", (i) => {
      if (i.face !== "front" || i.y === 0) return barkPx(i, seed + 1);
      const x = i.x, y = i.y, edge = x === 0 || x === 7;
      const plank = (hash(x, 3, seed) > 0.7 ? bark[1] : bark[2]);
      if (y === 1) return edge ? bark[1] : plank;
      if (y === 2) return x === 1 || x === 2 || x === 5 || x === 6 ? bark[0] : edge ? bark[1] : bark[2]; // wenkbrauwen
      if (y === 3 || y === 4) {
        const L = x === 1 || x === 2, R = x === 5 || x === 6;
        if (L || R) {
          const inner = (L && x === 2) || (R && x === 5);
          if (y === 3) return inner ? glow[2] : glow[1];
          return inner ? glow[1] : glow[0];
        }
        if (x === 3 || x === 4) return y === 3 ? bark[3] : bark[2]; // neusbrug
        return bark[1];
      }
      if (y === 5) {
        if (x === 3) return bark[3];
        if (x === 4) return bark[2];
        if (edge) return shade(moss, 0.08);
        return x === 2 || x === 5 ? shade(bark[2], -0.06) : bark[2];
      }
      if (y === 6) {
        if (x >= 2 && x <= 5) return x === 3 || x === 4 ? shade(glow[0], -0.45) : hex("#160f0a"); // mond
        return edge ? moss : bark[1];
      }
      return (x & 1) ? moss : shade(moss, -0.22); // mosbaard
    });
    // ---- Hoofd: bladerkap ----
    p("head", "o", (i) => {
      if (i.face === "bottom") return (i.x + i.y) % 3 === 0 ? shade(moss, -0.15) : undefined;
      if (i.face === "top") return leaves(i, seed + 2, 1);
      if (i.face === "front") {
        if (i.y === 0) return leaves(i, seed + 3, 1);
        if (i.y === 1) return hash(i.X, i.Y, seed) > 0.4 ? leaves(i, seed + 3, 1) || undefined : undefined;
        if ((i.x === 0 || i.x === 7) && i.y <= 5) return hash(i.X, i.Y, seed + 4) > 0.25 ? leaves(i, seed + 3, 1) || undefined : undefined;
        return undefined;
      }
      return leaves(i, seed + 5, i.y < 5 ? 1 : 1 - (i.y - 4) * 0.2) || undefined;
    });

    // ---- Romp ----
    p("body", "b", (i) => {
      if (i.face === "front") {
        // levenshart: gloeiende kern met jaarringen
        const dx = i.x - 3.5, dy = i.y - 4.5, r = Math.sqrt(dx * dx + dy * dy);
        if (r < 1) return glow[2];
        if (r < 1.6) return glow[1];
        if (r < 2.3) return shade(glow[0], -0.15);
        if (r < 3.1) return (Math.round(r * 3) & 1) ? bark[3] : bark[1];
      }
      return barkPx(i, seed + 6);
    });
    p("body", "o", (i) => {
      if (i.face === "bottom") return undefined;
      if (i.face === "top") return leaves(i, seed + 8, 1);
      if (i.face === "back") return leaves(i, seed + 9, i.y < 9 ? 1 : 1 - (i.y - 8) * 0.25) || undefined; // bladmantel
      if (i.face === "front") {
        if (i.y === 0) return leaves(i, seed + 10, 1) || undefined;
        if (i.y <= 2 && (i.x <= 1 || i.x >= 6)) return leaves(i, seed + 10, 1) || undefined;
        if (i.y >= 10 && hash(i.X, i.Y, seed + 11) > 0.35) return leaves(i, seed + 11, 1) || undefined;
        // ranke diagonaal over de borst, om het hart heen
        const t = i.x + i.y;
        if ((t === 11 || t === 12) && i.y >= 6) return name === "jungle" ? hex(T.vine[1]) : shade(bark[0], 0.12);
        if ((t === 10 || t === 13) && i.y >= 6 && hash(i.X, i.Y, seed + 12) > 0.45) return leafColor(i, seed + 13);
        return undefined;
      }
      if (i.y <= 3) return leaves(i, seed + 10, 1 - i.y * 0.15) || undefined;
      if (i.y >= 10) return leaves(i, seed + 11, 0.6) || undefined;
      return undefined;
    });

    // ---- Armen ----
    for (const arm of ARMS) {
      p(arm, "b", (i) => {
        if (i.y >= 10 && i.face !== "top") {
          // twijgvingers
          if (i.face === "bottom") return bark[0];
          if (i.face === "front" && i.y === 11) return (i.x & 1) ? bark[2] : bark[0];
          return i.y === 11 ? bark[0] : bark[1];
        }
        return barkPx(i, seed + 14);
      });
      p(arm, "o", (i) => {
        if (i.face === "bottom") return undefined;
        if (i.face === "top") return leaves(i, seed + 15, 1);
        if (i.y <= 3) return leaves(i, seed + 16, 1 - i.y * 0.18) || undefined;
        if (i.y === 7 || i.y === 8) return leaves(i, seed + 17, 0.45) || undefined;
        return undefined;
      });
    }
    // ---- Benen met wortels ----
    for (const leg of LEGS) {
      p(leg, "b", (i) => {
        if (i.face === "bottom") return bark[0];
        if (i.y >= 9 && i.face !== "top") {
          if (i.y === 9) return hash(i.X, i.Y, seed) > 0.5 ? moss : shade(moss, -0.2);
          const root = ((U(i) + (i.y === 10 ? 1 : 0)) % 3) === 0;
          return root ? bark[2] : bark[0];
        }
        return barkPx(i, seed + 18);
      });
      p(leg, "o", (i) => {
        if (i.face === "top" || i.face === "bottom") return undefined;
        if (i.y <= 2) return leaves(i, seed + 19, 0.7 - i.y * 0.2) || undefined;
        if (i.y === 11) return ((U(i) % 3) === 1) ? shade(bark[1], -0.1) : undefined; // wortels
        if (i.y === 10) return ((U(i) % 4) === 1) ? bark[1] : undefined;
        return undefined;
      });
    }

    // ---- Thema-details ----
    const deco = DECOR[name];
    if (deco) deco(s, p, T, { leaf, bark, glow, moss, flowerAt, U, leafColor });
    return s;
  }

  // Takkenkroon op de zijkanten van de kap (0 = achterkant).
  const CROWN = ["b.b.b...", ".bbb.b..", "..b.bb..", "...bb...", "....b..."];
  function twigCrown(p, color, leafy) {
    p("head", "o", (i) => {
      const bx = i.face === "right" ? i.x : 7 - i.x;
      if ((CROWN[i.y] || "")[bx] !== "b") return undefined;
      if (leafy && leafy(i)) return leafy(i);
      return shade(color, 0.05 - i.y * 0.04 + (hash(i.X, i.Y, 3) > 0.7 ? 0.12 : 0));
    }, ["right", "left"]);
  }

  const DECOR = {
    // Takkenkroon en eikels
    eik(s, p, T, k) {
      twigCrown(p, k.bark[3]);
      const CAP = hex("#6b4a24"), NUT = hex("#c08a3e");
      const acorn = (i, ax, ay) => {
        if (i.x === ax && i.y === ay) return shade(CAP, 0.12);
        if (i.x === ax + 1 && i.y === ay) return shade(CAP, -0.1);
        if (i.x === ax && i.y === ay + 1) return shade(NUT, 0.18);
        if (i.x === ax + 1 && i.y === ay + 1) return NUT;
        if (i.x === ax && i.y === ay + 2) return shade(NUT, -0.2);
        return undefined;
      };
      p("head", "o", (i) => acorn(i, 4, 4), ["right"]);
      p("head", "o", (i) => acorn(i, 2, 4), ["left"]);
      p("rarm", "o", (i) => acorn(i, 1, 4), ["front"]);
      p("body", "o", (i) => acorn(i, 5, 8), ["back"]);
      p("lleg", "o", (i) => acorn(i, 1, 1), ["front"]);
    },
    // Paddenstoelen + vallende blaadjes
    herfst(s, p) {
      const CAP = hex("#c22a1f"), DOT = hex("#f4efe2"), STEM = hex("#e8dcc0");
      const shroom = (i, ax, ay) => {
        const dx = i.x - ax, dy = i.y - ay;
        if (dy === 0 && dx >= 0 && dx <= 2) return dx === 1 ? DOT : shade(CAP, dx === 0 ? 0.1 : -0.08);
        if (dy === -1 && dx === 1) return shade(CAP, 0.15);
        if (dy === 1 && dx === 1) return STEM;
        return undefined;
      };
      p("larm", "o", (i) => shroom(i, 0, 1), ["front"]);
      p("rleg", "o", (i) => shroom(i, 0, 8), ["right"]);
      p("head", "o", (i) => shroom(i, 3, 2), ["back"]);
      p("body", "o", (i) => shroom(i, 1, 7), ["right"]);
      const fall = [hex("#e0742a"), hex("#c9481b"), hex("#f2b544")];
      for (const leg of LEGS)
        p(leg, "o", (i) => (i.y >= 4 && i.y <= 8 && hash(i.X, i.Y, 99) > 0.86 ? fall[(i.X + i.Y) % 3] : undefined), ["front", "right", "left", "back"]);
      for (const arm of ARMS)
        p(arm, "o", (i) => (i.y >= 5 && i.y <= 9 && hash(i.X, i.Y, 98) > 0.9 ? fall[(i.X + 2 * i.Y) % 3] : undefined), ["front", "right", "left", "back"]);
    },
    // Bloesemkroon, bloemetjes, tak over de rug
    bloesem(s, p, T, k) {
      const petals = [hex("#9e3d63"), hex("#f3a9c4"), hex("#ffe1ec"), hex("#ffd84a")];
      twigCrown(p, k.bark[1], (i) => (hash(i.X, i.Y, 61) > 0.55 ? petals[1 + (i.X & 1)] : null));
      p("head", "o", (i) => {
        if (i.face === "front") return undefined;
        if (i.face !== "top" && i.y > 4) return undefined;
        return k.flowerAt(i, 71, petals, 0.55) || undefined;
      });
      p("body", "o", (i) => {
        const line = i.x - Math.round(i.y * 0.6) - 1;
        if (line === 0 && i.y <= 9) return shade(k.bark[0], 0.1);
        if (Math.abs(line) === 1 && i.y <= 9 && hash(i.X, i.Y, 5) > 0.5) return petals[1 + (i.X & 1)];
        return undefined;
      }, ["back"]);
      for (const part of ["rarm", "larm", "rleg", "lleg"])
        p(part, "o", (i) => (i.y >= 4 && i.y <= 9 && hash(i.X, i.Y, 77) > 0.88 ? petals[1 + ((i.X + i.Y) & 1)] : undefined), ["front", "right", "left", "back"]);
    },
    // Magenta bloemen tussen het blad
    azalea(s, p, T, k) {
      const fl = T.flower.map(hex);
      const ramp = [fl[0], fl[1], fl[2], hex("#ffe27a")];
      const onLeaves = (i) => (i.cur[3] > 0 ? k.flowerAt(i, 81, ramp, 0.5) || undefined : undefined);
      p("head", "o", onLeaves, ["top", "right", "left", "back"]);
      p("body", "o", onLeaves, ["top", "back", "right", "left"]);
      p("rarm", "o", onLeaves); p("larm", "o", onLeaves);
      // dikke mosmat op de schouders
      for (const arm of ARMS) p(arm, "b", (i) => (i.y <= 1 || i.face === "top" ? shade(k.moss, (hash(i.X, i.Y, 5) - 0.5) * 0.3) : undefined));
    },
    // Hangende lianen met gloeibessen
    jungle(s, p, T, k) {
      const VN = T.vine.map(hex), B = T.berry.map(hex);
      const vine = (i, cols, len) => {
        const col = cols.indexOf(i.s);
        if (col < 0) return undefined;
        const L = len[col];
        if (i.y > L) return undefined;
        if (i.y === L) return B[2];
        if (i.y === L - 1) return B[1];
        if ((i.y + col) % 3 === 0 && i.y > 1) return k.leafColor(i, 91);
        return shade(VN[(i.y + col) & 1], 0.15);
      };
      p("head", "o", (i) => (i.face === "front" ? undefined : vine(i, [1, 5, 10, 13, 18, 23, 27, 30], [6, 7, 5, 7, 6, 7, 5, 6])), ["right", "left", "back"]);
      p("head", "o", (i) => ((i.x === 0 || i.x === 7) && i.y >= 4 && i.y <= 6 ? (i.y === 6 ? B[2] : shade(VN[1], 0.15)) : undefined), ["front"]);
      p("body", "o", (i) => vine(i, [1, 13, 15, 18, 21], [9, 7, 10, 8, 11]), ["right", "left", "back"]);
      for (const part of ["rarm", "larm"]) p(part, "o", (i) => vine(i, [1, 6, 10], [10, 8, 9]), ["right", "left", "back", "front"]);
      p("head", "o", (i) => (hash(i.X, i.Y, 93) > 0.9 ? B[2] : hash(i.X, i.Y, 94) > 0.92 ? B[1] : undefined), ["top"]);
    },
  };

  // ------------------------------------------------------------------
  // Catalogus
  // ------------------------------------------------------------------
  const CHRISTMAS = [
    { id: "kerstmuts", name: "Kerstmuts", make: santaHat, notes: ["Rode fluwelen kerstmuts met bontrand", "Punt met pompon hangt over de rug", "Witte bontkraag", "Bontmanchetten waar de mouwen eindigen", "Hulsttakje met bessen op de borst", "Eigen gezicht, haar en kleding blijven"] },
    { id: "winterwarm", name: "Winterwarm", make: winter, notes: ["Gebreide muts in de eigen shirtkleur, met pompon", "Gestreepte sjaal met franje", "Gebreide wanten met witte rand", "Sneeuw op muts en schouders", "Sneeuwhoopjes rond de schoenen", "Eigen gezicht en kleding blijven"] },
    { id: "kerstlichtjes", name: "Kerstlichtjes", make: lights, notes: ["Twee lichtslingers rond de romp", "Lampjes in spiraal om de armen", "Lichtjeskrans om het hoofd", "Gouden ster bovenop", "Lampjes in vijf kleuren met glimlicht", "Eigen kleding blijft zichtbaar"] },
    { id: "rendier", name: "Rendier", make: reindeer, notes: ["Gewei op de zijkanten en bovenkant", "Rendieroortjes met roze binnenkant", "Rode Rudolph-neus", "Rood lint met gouden belletje", "Wit staartje op de rug", "Eigen haar, ogen en kleding blijven"] },
    { id: "kersttrui", name: "Kersttrui", make: sweater, notes: ["Het eigen shirt omgebreid tot kersttrui", "Breisteek in de eigen shirtkleuren", "Kerstboom met ballen op de borst", "Sneeuwvlok op de rug", "Zigzag- en stippenbanden op romp en mouwen", "Sneeuwvlokje in het haar"] },
  ];
  const NATURE = [
    { id: "eik", name: "Eikenwachter", notes: ["Frisgroene eikenbladeren als kap en mantel", "Bastgezicht met amberkleurige ogen", "Gloeiend levenshart in de borst", "Eikels op kap, arm en rug", "Twijgvingers en wortelvoeten"] },
    { id: "herfst", name: "Herfstgeest", notes: ["Rood, oranje en goud gemengd blad", "Oranje gloeiende ogen", "Vliegenzwammen op schouder, been en kap", "Vallende blaadjes rond de benen", "Mosbaard onder de kin"] },
    { id: "bloesem", name: "Bloesemdryade", notes: ["Roze kersenbloesem als bladerkap", "Bloemetjes met gele hartjes", "Bloesemtak over de rug", "Losse blaadjes op armen en benen", "Roodbruine kersenbast"] },
    { id: "azalea", name: "Azaleahoeder", notes: ["Azaleablad met magenta bloemen", "Paarse gloed in ogen en hart", "Bemoste bast", "Bloemen op kap, mantel en armen", "Wortelvoeten met mos"] },
    { id: "jungle", name: "Junglegeest", notes: ["Donker junglegroen blad", "Hangende lianen rondom", "Gloeibessen aan de lianen en op de kap", "Cyaan gloeiende ogen", "Liaan over de borst"] },
  ];

  return {
    Skin, fromImageData, analyze, detectSlim, exampleBase, leafSkin,
    CHRISTMAS, NATURE, toHex, hex,
  };
});
