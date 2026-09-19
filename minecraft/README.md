# Eternal Sky — Nuit skybox pack

Een Minecraft resource pack voor de **Nuit**-mod (de opvolger van FabricSkyBoxes) dat de
vanilla-lucht vervangt door één vaste wolkenlucht, met een foto op de noordkant en een
foto op de zuidkant.

De lucht verandert **nooit**: ochtend, middag, avond en nacht zien er identiek uit, in
elke dimensie, elk biome en bij elk weertype.

| | |
|---|---|
| Minecraft | Java Edition **1.21.11** |
| Vereiste mod | [Nuit](https://modrinth.com/mod/nuit) `1.0.0-beta.6` (Fabric of NeoForge) |
| `pack_format` | 75 |
| Textuur | 4608 × 3072 (1536 px per cubeface) |

## Installeren

1. Installeer **Nuit** voor 1.21.11 in je mods-map (plus Fabric API of NeoForge).
2. Kopieer de map `nuit-eternal-sky/` naar `.minecraft/resourcepacks/`.
   Minecraft accepteert een map net zo goed als een `.zip`; wil je toch een zip, run dan
   `bash minecraft/tools/package.sh`.
3. Start het spel, zet het pack aan bij **Opties → Resource Packs**, en klaar.

## Wat staat waar

```
nuit-eternal-sky/
├── pack.mcmeta                              pack_format 75
├── pack.png                                 pack-icoon
└── assets/nuit/sky/
    ├── eternal_sky.json                     de skybox-definitie
    └── eternal_sky.png                      3×2 atlas met de zes cubefaces
```

### Oriëntatie van de foto's

| Richting | Inhoud |
|---|---|
| **Noord** (−Z) | `front.webp` — het portret met bruin haar |
| **Zuid** (+Z) | `back.webp` — het portret met donker haar |
| Oost / west | wolken |
| Boven | omhoogkijkende wolkenfoto |
| Onder | wolkendek van bovenaf |

Druk op F3 om je kijkrichting te zien. Beide portretten zijn uitgeknipt (de bronbestanden
hebben al een alphakanaal), dus ze zweven tegen de wolken in plaats van op een witte
rechthoek, en de onderkant lost op in het wolkendek.

## Hoe "altijd" is geregeld

In `eternal_sky.json`:

- **`fade` weggelaten** → Nuit leest dat als lege keyframes en zet de alpha permanent op
  `1.0`. Dat is de officiële manier om een skybox altijd aan te laten staan; keyframes
  zoals `{"0": 0, "12000": 1.0}` zouden hem juist per tijdstip laten in- en uitfaden.
- **`conditions: {}`** → elke lege conditielijst telt als "altijd waar", dus geen
  beperking op dimensie, biome, weer of coördinaten.
- **`rotation` weggelaten** → zonder keyframes in `mapping`/`axis` past Nuit helemaal geen
  rotatie toe, dus de lucht draait niet met de zon mee.
- **`sunSkyTint: false`** → schakelt de oranje zonsopgang-/zonsondergangstint uit die
  anders over de horizon en de mist zou lopen.

Zolang er een Nuit-skybox actief is, slaat Nuit de vanilla-lucht over: geen zon, geen
maan, geen sterren en geen End-lucht. Precies wat je wil als de lucht altijd hetzelfde
moet blijven.

### Optioneel: zon, maan en sterren terug

Zet dit als extra bestand in `assets/nuit/sky/` (bijvoorbeeld `decorations.json`):

```json
{
  "schemaVersion": 1,
  "type": "decorations",
  "properties": { "layer": 1 },
  "conditions": {},
  "showSun": true,
  "showMoon": true,
  "showStars": true
}
```

### Optioneel: mist ook vastzetten

De wereldmist wordt 's nachts nog steeds donker. Wil je dat de verte altijd bij de lucht
past, voeg dan dit toe aan `properties` in `eternal_sky.json`:

```json
"fog": { "modifyColors": true, "red": 0.62, "green": 0.72, "blue": 0.84 }
```

## Textuur opnieuw genereren

```bash
pip install pillow numpy
python3 minecraft/tools/build_skybox.py --face-size 1536
```

Handige opties: `--face-size 2048` voor een scherpere (ca. 13 MB) atlas, en
`--preview-dir <map>` om de zes faces los weg te schrijven zodat je ze kan nakijken.

Wil je de portretten groter, kleiner of hoger in beeld? Pas `PORTRAIT_HEIGHT` en
`PORTRAIT_CENTER_Y` bovenin het script aan. Een cubeface beslaat 90°, dus `0.56` is een
figuur van ongeveer 50° — groter dan ongeveer `0.62` en de bovenkant valt buiten beeld bij
de standaard FOV van 70.

### Controleren zonder Minecraft op te starten

```bash
python3 minecraft/tools/preview.py --out-dir skybox-preview
```

Dit rendert 16:9-beelden vanuit het midden van de cube (noord, oost, zuid, west en recht
omhoog), bij de standaard FOV van 70. Het script bouwt de cube na met de UV-ranges en
rotatiematrices uit de mod zelf, los van `build_skybox.py` — staat een face scheef,
gespiegeld of in de verkeerde cel, dan zie je dat hier meteen.

Het script bouwt uit `source-images/sky.webp` eerst een naadloze equirectangulaire
360°-lucht en projecteert die daarna op de zes cubefaces. De cel-indeling volgt
`Utils.TEXTURE_FACES` uit de Nuit-broncode (tag `mc1.21.11-1.0.0-beta.6`), die afwijkt van
de tabel in `docs/square-textured.md` van de mod:

```
col 0      col 1     col 2
bottom     top       south     <- rij 0
west       north     east      <- rij 1
```

## Bronmateriaal

`source-images/` bevat de drie aangeleverde afbeeldingen. De wolkencollage heeft linksboven
een `created by SODVIC`-watermerk; die tegel wordt niet gebruikt — het pack put alleen uit
de brede panoramategel onderaan en de schone tegel rechtsboven.
