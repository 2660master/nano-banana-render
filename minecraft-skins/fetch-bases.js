// Haalt de huidige skins van de spelers op bij Mojang en zet ze in bases/.
// Vereist internettoegang tot api.mojang.com, sessionserver.mojang.com en textures.minecraft.net.
const fs = require("fs");
const path = require("path");

const PLAYERS = ["spawnerbase", "2660master", "stitchcpvp", "akosdebeste", "pickzugng", "johnpork400", "ITZberryTT_x"];
const dir = path.join(__dirname, "bases");

async function json(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} bij ${url}`);
  return res.json();
}

(async () => {
  fs.mkdirSync(dir, { recursive: true });
  for (const name of PLAYERS) {
    try {
      const { id } = await json(`https://api.mojang.com/users/profiles/minecraft/${encodeURIComponent(name)}`);
      const profile = await json(`https://sessionserver.mojang.com/session/minecraft/profile/${id}`);
      const prop = profile.properties.find((p) => p.name === "textures");
      const textures = JSON.parse(Buffer.from(prop.value, "base64").toString("utf8")).textures;
      if (!textures.SKIN) throw new Error("speler heeft de standaardskin (geen eigen skin)");
      const png = Buffer.from(await (await fetch(textures.SKIN.url)).arrayBuffer());
      fs.writeFileSync(path.join(dir, `${name}.png`), png);
      console.log(`✓ ${name}${textures.SKIN.metadata && textures.SKIN.metadata.model === "slim" ? " (slim)" : ""}`);
    } catch (err) {
      console.log(`✗ ${name}: ${err.message}`);
    }
  }
})();
