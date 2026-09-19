# Candyland — Bubblegum Noon

A custom overworld sky for the [Nuit](https://github.com/FlashyReese/nuit) mod
(formerly FabricSkyBoxes). Bubblegum at the zenith washing out to pale sherbet
at the horizon, whipped-cream banks sitting low, and gumballs and blown bubbles
floating at every size right around the compass — with one giant one resting
just under the western horizon as a landmark.

Chosen from five concepts in `skies.html`. The other four (Cotton Candy Dawn,
Gumdrop Midnight, Caramel Drizzle Dusk, Sherbet Aurora) are still in that file
if you want a second sky later.

## Installing

1. Install **Nuit** (Fabric or NeoForge) and its dependencies.
2. Drop `Candyland-BubblegumNoon.zip` into `.minecraft/resourcepacks/`.
3. Enable it in **Options → Resource Packs**.

## What's in the pack

```
pack.mcmeta
pack.png
assets/nuit/sky/bubblegum_noon.json              the sky cube
assets/nuit/sky/bubblegum_noon_decorations.json  sun and moon
assets/candyland/textures/sky/bubblegum_noon.png 3072x2048 cubemap atlas
```

The atlas is a 3×2 grid of 1024×1024 faces, in the order Nuit expects
(`Utils.TEXTURE_FACES`):

```
+--------+--------+--------+
| bottom |  top   | south  |
+--------+--------+--------+
|  west  | north  |  east  |
+--------+--------+--------+
```

## Two things worth knowing

**The sky only covers the day.** Both layers fade out between tick 13000 and
22500, which takes them to alpha 0. Nuit treats a skybox at alpha 0 as
inactive, and when nothing is active it hands the sky back to vanilla — so
nights look normal. To make it permanent instead, replace the `keyFrames`
object in both JSON files with `{}`.

**The decorations layer is not optional.** Nuit *replaces* the vanilla sky
while a skybox is active, sun and moon included. `bubblegum_noon_decorations.json`
puts them back, following Minecraft's real sun position
(`"skyboxRotation": false`). If you delete it, the sky loses its sun. Its fade
must stay identical to the sky's — if the two fall out of step, one layer stays
active alone and you get sun with no sky, or sky with no sun.

## Version compatibility

`pack.mcmeta` declares `pack_format: 55` with `supported_formats` spanning
15–99, which covers roughly 1.20 through current. If Minecraft still flags the
pack as made for another version, set `pack_format` to the number for your
version — the pack itself does not change between versions, only that
declaration does.

## Rebuilding the texture

```
cd tools
node render_sky.mjs --size 1024 --out ./out
node check_pack.mjs ../pack
```

`render_sky.mjs` is not a painting program. Every element — gradient, clouds,
gumballs, sparkle, grain — is evaluated as a function of a **direction vector**
rather than a position on a 2D canvas, so pixels either side of a cube edge
look up the same direction and get the same colour. The seams are correct by
construction, not by retouching. Before it renders anything the script proves
the six faces tile the sphere exactly once (round-trip error and coverage
count) and refuses to write a seamed atlas.

`--size` sets the per-face resolution; 512 and 2048 both work. Everything is
seeded, so the same size always produces the same sky.

`check_pack.mjs` validates the JSON against field names read out of Nuit's
codecs rather than its docs — a misspelled optional field doesn't error in
game, it silently falls back to its default.

## Tuning

In `tools/render_sky.mjs`:

| Want | Change |
|------|--------|
| Different pinks | `SKY_STOPS` |
| More or fewer bubbles | the three `ball(...)` loops |
| Bigger or smaller landmark | the `/* the landmark */` line — `0.30` is its angular radius in radians |
| Thicker clouds | `PUFFS` count, and the `1 - Math.exp(-sum * 3.0)` coverage curve |
| Where the sky is brightest | `SUN` (azimuth from north, then altitude) |
