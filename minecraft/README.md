# MadisonBeerSky — Nuit skybox pack

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
| Textuur | 6144 × 4096 (2048 px per cubeface) |

## Installeren

1. Installeer **Nuit** voor 1.21.11 in je mods-map (plus Fabric API of NeoForge).
2. Kopieer de map `MadisonBeerSky/` naar `.minecraft/resourcepacks/`.
   Minecraft accepteert een map net zo goed als een `.zip`; wil je toch een zip, run dan
   `bash minecraft/tools/package.sh`.
3. Start het spel, zet het pack aan bij **Opties → Resource Packs**, en klaar.

## Wat staat waar

```
MadisonBeerSky/
├── pack.mcmeta                              pack_format 75
├── pack.png                                 pack-icoon
└── assets/nuit/sky/
    ├── madison_beer_sky.json                de skybox-definitie
    └── madison_beer_sky.png                 3×2 atlas met de zes cubefaces
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

In `madison_beer_sky.json`:

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
past, voeg dan dit toe aan `properties` in `madison_beer_sky.json`:

```json
"fog": { "modifyColors": true, "red": 0.62, "green": 0.72, "blue": 0.84 }
```

## Textuur opnieuw genereren

```bash
pip install pillow numpy
python3 minecraft/tools/build_skybox.py
```

Handige opties: `--face-size 1536` voor een kleinere atlas, `--wraps 1` voor een unieke
maar zachtere lucht (zie hieronder), en `--preview-dir <map>` om de zes faces los weg te
schrijven zodat je ze kan nakijken. Een volledige build duurt ongeveer een minuut.

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

## Wolkenkwaliteit

De scherpte van de lucht wordt begrensd door de bron: de panoramategel is maar 2000 px
breed. Hoe minder graden hemel elke bronpixel moet bedekken, hoe meer detail overleeft.
Daarom herhaalt `--wraps 2` (de standaard) het panorama twee keer rond de horizon in
plaats van één keer over de volle 360° uit te rekken. Dat verdubbelt de hoekdichtheid en
maakt de wolken zichtbaar scherper.

De prijs is dat de lucht een periode van 180° heeft: de oost- en westkant tonen dezelfde
wolken. Je kan ze nooit tegelijk zien — je moet je een halve slag omdraaien om het te
merken — en de twee naden vallen precies midden op de noord- en zuidkant, waar de
portretten eroverheen staan. Wil je liever een unieke lucht rondom en neem je de zachtere
wolken voor lief, gebruik dan `--wraps 1`.

Verder doet het script nog drie dingen voor de kwaliteit:

- **Naadzoeker.** Het panorama moet op zichzelf aansluiten, maar beide originele randen
  zijn drukke wolkenpartijen. Het script zoekt het paar randen dat het beste op elkaar
  aansluit (hier scheelt dat 41%) en offert daar een paar honderd kolommen voor op. Dat
  kost veel minder detail dan de overvloeier breder maken tot de sprong niet meer opvalt.
- **Detailherstel.** Twee unsharp-passes — een brede voor lokaal contrast in de
  wolkenmassa's, een smalle voor de randen — halen terug wat het opschalen kost. Dat
  gebeurt op de equirectangulaire kaart en niet per face, want per face filteren laat een
  lichte of donkere haarlijn achter langs elke cuberand.
- **Bronreparatie.** De onderste ~50 rijen van de panoramategel bevatten twee donkere,
  hardgerande vlekken die de generator heeft achtergelaten. Op ware grootte vallen ze niet
  op, uitvergroot worden het storende spikkels, dus de uitsnede stopt erboven.

## Bronmateriaal

`source-images/` bevat de drie aangeleverde afbeeldingen. De wolkencollage heeft linksboven
een `created by SODVIC`-watermerk; die tegel wordt niet gebruikt — het pack put alleen uit
de brede panoramategel onderaan en de schone tegel rechtsboven.
