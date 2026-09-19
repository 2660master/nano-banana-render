/**
 * Validates the resource pack against Nuit's actual codecs.
 *
 * The field names and constraints checked here were read out of the mod
 * source (components/Properties.java, Fade.java, Rotation.java,
 * Conditions.java and the skybox codecs), not out of the docs, because a
 * misspelled optional field does not error in game - it silently falls back
 * to its default and the sky quietly does the wrong thing.
 *
 *   node check_pack.mjs [packDir]
 */
import fs from "node:fs";
import path from "node:path";

const P = path.resolve(process.argv[2] || "../pack");
let fail = 0;
const ok = (c, m) => { console.log((c ? "  ok   " : "  FAIL ") + m); if (!c) fail++; };

ok(fs.existsSync(path.join(P, "pack.mcmeta")), "pack.mcmeta present");
ok(fs.existsSync(path.join(P, "pack.png")), "pack.png present");

const tex = path.join(P, "assets/candyland/textures/sky/bubblegum_noon.png");
ok(fs.existsSync(tex), "sky texture present");
if (fs.existsSync(tex)) {
  const b = fs.readFileSync(tex);
  const w = b.readUInt32BE(16), h = b.readUInt32BE(20);
  ok(b.subarray(1, 4).toString() === "PNG", "texture is a real PNG");
  ok(w / h === 1.5, `atlas is a 3x2 face grid (${w}x${h})`);
  ok(w % 3 === 0 && h % 2 === 0, "atlas divides cleanly into six square faces");
}

const skyDir = path.join(P, "assets/nuit/sky");
const files = fs.readdirSync(skyDir).filter((f) => f.endsWith(".json"));
ok(files.length > 0, "at least one sky definition under assets/nuit/sky/");

const PROP = new Set(["layer", "clock", "fade", "transitionInDuration",
  "transitionOutDuration", "fog", "sunSkyTint", "visibleUnderwater", "rotation"]);
const COND = new Set(["biomes", "skyboxes", "worlds", "dimensions", "effects",
  "weather", "xRanges", "yRanges", "zRanges"]);
const ROT = new Set(["skyboxRotation", "mapping", "axis", "duration", "speed"]);
const TYPES = new Set(["overworld", "end", "monocolor", "square-textured",
  "multi-textured", "decorations"]);

const fades = [];
for (const f of files) {
  const j = JSON.parse(fs.readFileSync(path.join(skyDir, f), "utf8"));
  console.log("  -- " + f);
  ok(j.schemaVersion === 1, "schemaVersion is 1");
  ok(TYPES.has(j.type), `type "${j.type}" is a built-in type`);
  for (const k of Object.keys(j.properties || {})) ok(PROP.has(k), `properties.${k} is a real field`);
  for (const k of Object.keys(j.conditions || {})) ok(COND.has(k), `conditions.${k} is a real field`);
  for (const k of Object.keys(j.properties?.rotation || {})) ok(ROT.has(k), `rotation.${k} is a real field`);
  const fd = j.properties?.fade;
  if (fd) {
    fades.push(JSON.stringify(fd.keyFrames));
    const dur = fd.duration ?? 24000;
    for (const [t, v] of Object.entries(fd.keyFrames || {})) {
      ok(Number.isInteger(+t) && +t >= 0 && +t < dur, `keyframe ${t} is within [0, ${dur})`);
      ok(v >= 0 && v <= 1, `keyframe ${t} alpha ${v} is within [0,1]`);
    }
  }
  if (j.type === "square-textured") {
    ok(typeof j.texture === "string" && j.texture.includes(":"), "texture is a namespaced identifier");
    const [ns, rest] = j.texture.split(":");
    ok(fs.existsSync(path.join(P, "assets", ns, rest)), "texture identifier resolves to a file on disk");
  }
}
/* If the two layers fell out of step, night would lose its sky: Nuit replaces
 * the vanilla sky whenever any renderable skybox is active. */
ok(new Set(fades).size <= 1, "every layer shares one fade schedule");

console.log(fail ? `\n${fail} PROBLEM(S)` : "\nall checks passed");
process.exit(fail ? 1 : 0);
