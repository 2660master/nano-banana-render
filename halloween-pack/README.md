# Halloween Pack — Minecraft 1.21.11

Resourcepack met twee onderdelen:

| Onderdeel | Nodig |
|---|---|
| Oranje pompoen-glint (items + harnas) | alleen vanilla |
| Halloween sky "De Wachter" | mod [Nuit](https://modrinth.com/mod/nuit) (Fabric of NeoForge) |

`pack_format: 75` (= 1.21.11). Via `supported_formats` laadt de pack ook op oudere/nieuwere
versies zonder "incompatible"-waarschuwing.

## Installeren

Kopieer de map `halloween-pack` naar `.minecraft/resourcepacks/` (of zip 'm — `pack.mcmeta` moet
dan in de wortel van de zip staan, niet in een extra submap). Activeer in *Options → Resource Packs*.

Zonder Nuit werkt de glint gewoon; de sky wordt dan simpelweg genegeerd.

---

## De sky — "De Wachter"

```
assets/nuit/sky/watcher.json              <- Nuit laadt alles uit assets/nuit/sky/
assets/halloween/textures/sky/watcher.png <- 3072x2048 (6 vlakken van 1024)
```

Geen maan: in het noordwesten hangt een kolossaal oog dat op je neerkijkt, met een roodbruine iris,
adertjes en een vaste catchlight. De lucht is bijna zwart paars met tentakelachtige nevelslierten
(ridged noise), en er gaan zesentwintig kleinere ogen open, verspreid tot hoog boven je hoofd.

Aan de horizon staat een kerkhof in twee dieptelagen: smeedijzeren hekken, grafstenen met scheve
kruisen, kale bomen, skelethanden die uit de grond klauwen, een galg met strop, twee
vogelverschrikkers met gloeiende ogen, een kerktoren, een spookhuis met verlichte ramen, kraaien
in de takken en paren ogen die vanuit het donker tussen de bomen kijken. Daar drijven tien
jack-o'-lanterns en zes geesten tussendoor, boven een laag grondmist.

Het oog valt precies op de hoek tussen *top*, *west* en *north* in het 3×2 vel en loopt over alle
drie de vlakken naadloos door — zie de face-layout hieronder.

### Face-layout

Nuit's `square-textured` leest één textuur als een 3×2 raster. De volgorde komt uit
`Utils.TEXTURE_FACES` in de broncode (branch `1.21.11/dev`):

| | kolom 0 | kolom 1 | kolom 2 |
|---|---|---|---|
| **rij 0** | bottom | top | south |
| **rij 1** | west | north | east |

De zijkanten staan rechtop en lopen rond als N → O → Z → W. `build_sky.py` controleert na het
renderen alle 12 kubusranden: elke rand moet door precies twee vlakken gedeeld worden en de
pixelrijen langs die rand moeten dezelfde kleur hebben. Objecten worden gnomonisch geprojecteerd,
dus een boom of maan die over een rand valt loopt naadloos door.

### Twee dingen die je misschien wilt aanpassen

**1. Alleen 's nachts halloween.** Nu staat de sky altijd aan (eeuwige halloween-nacht). Voor
dag/nacht-wisseling zet je een fade in `properties` van `watcher.json`:

```json
"fade": {
  "duration": 24000,
  "keyFrames": { "11800": 0.0, "13500": 1.0, "22200": 1.0, "23600": 0.0 }
}
```

**2. De zon terug.** Nuit annuleert de vanilla sky-pass zodra er een skybox actief is, dus zon,
maan en sterren zijn weg (die van deze sky zitten in de textuur). Wil je de echte zon erbij, zet
er dan een tweede bestand naast, `assets/nuit/sky/decorations.json`:

```json
{
  "schemaVersion": 1,
  "type": "decorations",
  "properties": { "layer": 1 },
  "showSun": true,
  "blend": { "type": "decorations" }
}
```

---

## De glint

| Bestand | Formaat | Waarom |
|---|---|---|
| `assets/minecraft/textures/misc/enchanted_glint_item.png` | 512×512 | losjes gestrooid veld kleine lantaarns |
| `assets/minecraft/textures/misc/enchanted_glint_armor.png` | 1024×1024 | dicht veld nog kleinere lantaarns |

Waarom twee verschillende ontwerpen: Minecraft schuift de glint over het model met een
texture-matrix, en de schaal daarvan verschilt per rendertype.

* **Items** gebruiken schaal `8.0`: de textuur wordt 8× herhaald over een sprite van 16 px, dus één
  tegel is ~2 item-pixels breed. Individuele pompoenen zijn daar fysiek niet te zien — je ziet een
  oranje schittering die over je zwaard schuift. Om die schittering tóch te laten leven ligt er een
  laagfrequente helderheidsdrift over het veld: sommige lantaarns branden feller dan andere, en dat
  contrast overleeft het uitmiddelen wel.
* **Gedragen harnas** gebruikt schaal `0.16`: over een borststuk zie je maar ~2 % van de textuur,
  enorm uitvergroot. Daar staan daarom véél kleinere pompoenen op (~1,7 % van de breedte), die als
  grote gloeiende koppen over je harnas trekken.

Elke lantaarn wordt uit vijf gesneden gezichten, ribben, steel met krul en blad, speculaire
highlight en een gloed vanuit de gaten opgebouwd, en krijgt een eigen maat, rotatie en helderheid.
Beide bestanden tegelen naadloos (strepen uit band-gefilterde ruis in het frequentiedomein,
pompoenen met wrap-around gestempeld). De `.png.mcmeta` zet `blur: true`, net als vanilla, zodat
de sterk uitvergrote harnas-glint glad blijft.

De glint mengt additief met `SRC_COLOR, ONE` — de kleur wordt dus effectief gekwadrateerd. Daarom
is zwart in de textuur "onzichtbaar" en is de rest ruim helder gehouden.

---

## Zelf aanpassen

Alles is procedureel gegenereerd; `generator/` bevat de bronscripts (Python + Pillow + NumPy).

```bash
pip install pillow numpy
cd generator
python3 build_sky.py s_watcher 1024 ../assets/halloween/textures/sky/watcher.png
python3 glint.py    ../assets/minecraft/textures/misc
python3 pack_icon.py ../pack.png
python3 preview.py  .        # previews van alle vijf de sky-concepten
```

* `skylib.py` — ruis, sterrenvelden, sprites (pompoen, maan, vleermuis, boom) en de kubus-/
  equirect-/perspectiefprojecties.
* `concepts.py` — de vijf eerste sky-ontwerpen.
* `build_sky.py` — rendert een concept naar het 3×2 vel en controleert de naden.
* `glint.py` — de twee glint-sheets.

* `scary.py` — de horror-props (kraaien, galg, skelethanden, hek, vogelverschrikker, spookhuis,
  ogen, geesten, spinnenweb, bliksem), de donkere manen en de vijf enge varianten.

Alle tien de sky-ontwerpen zitten er nog in. `python3 preview.py .` rendert previews van
allemaal, of geef slugs mee voor een paar: `python3 preview.py . s_blood s_eclipse`. Een andere
sky in de pack zetten is één commando plus de bestandsnaam in de JSON aanpassen:

| slug | sky |
|---|---|
| `s_watcher` | De Wachter *(zit nu in de pack)* |
| `s_blood` / `s_eclipse` / `s_skull` / `s_storm` | Bloedmaan, Verduistering, Schedelmaan, Onweer |
| `graveyard` | Kerkhof Nacht (de eerste, rustigere versie) |
| `bloodmoon` / `nebula` / `witching` / `void` | de vier niet-kerkhof concepten |

```bash
python3 build_sky.py s_storm 1024 ../assets/halloween/textures/sky/storm.png
```

Zet daarna maar één `.json` in `assets/nuit/sky/` — Nuit laadt ze namelijk allemaal, en dan
renderen ze over elkaar heen.
