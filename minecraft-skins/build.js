// Bouwt de PNG-bestanden in skins/ en de losse preview-pagina index.html.
// Basis-skins van spelers worden gelezen uit bases/<spelernaam>.png.
const fs = require("fs");
const path = require("path");
const { PNG } = require("pngjs");
const SF = require("./src/skinforge.js");

const PLAYERS = ["spawnerbase", "2660master", "stitchcpvp", "akosdebeste", "pickzugng", "johnpork400", "ITZberryTT_x"];
const root = __dirname;

function save(skin, file) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const png = new PNG({ width: 64, height: 64 });
  png.data = Buffer.from(skin.data);
  fs.writeFileSync(file, PNG.sync.write(png));
}
function load(file) {
  const png = PNG.sync.read(fs.readFileSync(file));
  return SF.fromImageData({ width: png.width, height: png.height, data: png.data });
}

const out = path.join(root, "skins");
for (const def of SF.NATURE) save(SF.leafSkin(def.id), path.join(out, "natuur", `${def.id}.png`));

const example = SF.exampleBase();
save(example, path.join(out, "kerst", "_voorbeeldbasis", "basis.png"));
for (const def of SF.CHRISTMAS) save(def.make(example), path.join(out, "kerst", "_voorbeeldbasis", `${def.id}.png`));

const embedded = {};
const found = [];
for (const player of PLAYERS) {
  const file = path.join(root, "bases", `${player}.png`);
  if (!fs.existsSync(file)) continue;
  const base = load(file);
  for (const def of SF.CHRISTMAS) save(def.make(base), path.join(out, "kerst", player, `${def.id}.png`));
  embedded[player] = "data:image/png;base64," + fs.readFileSync(file).toString("base64");
  found.push(player);
}

const tpl = fs.readFileSync(path.join(root, "src", "page.html"), "utf8");
const html = tpl
  .replace("/*SKINFORGE*/", () => fs.readFileSync(path.join(root, "src", "skinforge.js"), "utf8"))
  .replace("/*BASES*/{}", () => JSON.stringify(embedded));
// index.html is een volledig document om lokaal te openen; met --fragment <pad>
// wordt ook alleen de pagina-inhoud weggeschreven (voor publicatie als artifact).
const doc = `<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
${html}
</body>
</html>
`;
fs.writeFileSync(path.join(root, "index.html"), doc);
const fragArg = process.argv.indexOf("--fragment");
if (fragArg > 0) fs.writeFileSync(process.argv[fragArg + 1], html);

console.log(`Natuur: ${SF.NATURE.length} skins`);
console.log(`Kerst op voorbeeldbasis: ${SF.CHRISTMAS.length} skins`);
console.log(`Spelers met eigen basis: ${found.length ? found.join(", ") : "geen"} (${found.length * SF.CHRISTMAS.length} kerstskins)`);
const missing = PLAYERS.filter((p) => !found.includes(p));
if (missing.length) console.log(`Geen basis gevonden voor: ${missing.join(", ")} (zet ze in bases/<naam>.png of draai npm run fetch)`);
