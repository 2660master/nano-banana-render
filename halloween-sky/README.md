# Halloween Sky — "De Wachter"

Losse resourcepack met **alleen** een lucht. Geen items, geen glint, geen GUI — niets wat met
een andere pack kan botsen. `pack_format: 75` (= Minecraft 1.21.11); via `supported_formats`
laadt hij ook op omliggende versies zonder waarschuwing.

**Vereist de mod [Nuit](https://modrinth.com/mod/nuit)** (Fabric of NeoForge). Zonder die mod
laadt de pack gewoon, maar gebeurt er niets.

## Installeren

Map naar `.minecraft/resourcepacks/` kopiëren, of zippen — `pack.mcmeta` moet dan in de wortel
van de zip staan, niet in een extra submap. Daarna aanzetten in *Options → Resource Packs*.

## Wat je ziet

Geen maan: in het noordwesten hangt een kolossaal oog dat op je neerkijkt, met een roodbruine
iris, adertjes en een vaste catchlight. De lucht is bijna zwart paars met tentakelachtige
nevelslierten, en er gaan zesentwintig kleinere ogen open, verspreid tot hoog boven je hoofd.

Aan de horizon staat een kerkhof in twee dieptelagen: smeedijzeren hekken, grafstenen met scheve
kruisen, kale bomen, skelethanden die uit de grond klauwen, een galg met strop, twee
vogelverschrikkers met gloeiende ogen, een kerktoren, een spookhuis met verlichte ramen, kraaien
in de takken en paren ogen die vanuit het donker tussen de bomen kijken. Daar drijven tien
jack-o'-lanterns en zes geesten tussendoor, boven een laag grondmist.

## Bestanden

```
assets/nuit/sky/watcher.json              <- Nuit laadt elke .json uit assets/nuit/sky/
assets/halloween/textures/sky/watcher.png <- 3072x2048 (6 vlakken van 1024)
```

Nuit's `square-textured` leest die ene textuur als een 3×2 raster. De volgorde komt uit
`Utils.TEXTURE_FACES` in de broncode van de mod (branch `1.21.11/dev`):

| | kolom 0 | kolom 1 | kolom 2 |
|---|---|---|---|
| **rij 0** | bottom | top | south |
| **rij 1** | west | north | east |

De zijkanten staan rechtop en lopen rond als N → O → Z → W. Het oog valt precies op de hoek
tussen *top*, *west* en *north* en loopt over alle drie de vlakken door: alle objecten worden
gnomonisch geprojecteerd vanuit richtingsvectoren, dus randen sluiten exact aan. De generator
controleert dat na elke render — alle 12 kubusranden moeten door precies twee vlakken gedeeld
worden en de pixelrijen erlangs moeten dezelfde kleur hebben.

## Twee dingen die je misschien wilt aanpassen

**1. Alleen 's nachts.** Nu staat de lucht altijd aan (eeuwige halloween-nacht). Voor
dag/nacht-wisseling zet je een fade in `properties` van `watcher.json`:

```json
"fade": {
  "duration": 24000,
  "keyFrames": { "11800": 0.0, "13500": 1.0, "22200": 1.0, "23600": 0.0 }
}
```

**2. De zon terug.** Nuit annuleert de vanilla sky-pass zodra er een skybox actief is, dus zon,
maan en sterren zijn weg (die van deze lucht zitten in de textuur). Wil je de echte zon erbij,
zet er dan een tweede bestand naast, `assets/nuit/sky/decorations.json`:

```json
{
  "schemaVersion": 1,
  "type": "decorations",
  "properties": { "layer": 1 },
  "showSun": true,
  "blend": { "type": "decorations" }
}
```

## Een andere lucht

Er zijn tien ontwerpen; deze pack bevat er één. Zie `../halloween-generator/README.md` om er een
andere in te zetten. Let op: zet maar één `.json` in `assets/nuit/sky/` — Nuit laadt ze allemaal
en dan renderen ze over elkaar heen.
