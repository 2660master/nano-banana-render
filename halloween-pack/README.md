# Halloween Pack — Minecraft 1.21.11

Resourcepack met twee onderdelen:

| Onderdeel | Status | Nodig |
|---|---|---|
| Oranje pompoen-glint (items + harnas) | klaar | alleen vanilla |
| Halloween sky | concept gekozen → wordt toegevoegd | mod [Nuit](https://modrinth.com/mod/nuit) |

`pack_format: 75` (= 1.21.11). Via `supported_formats` laadt de pack ook op 1.21.6 t/m nieuwere versies
zonder "incompatible"-waarschuwing.

## Installeren

Kopieer de map `halloween-pack` naar `.minecraft/resourcepacks/` (of zip 'm en zet de zip daar neer —
`pack.mcmeta` moet in de wortel van de zip staan, niet in een extra submap). Activeer de pack in
*Options → Resource Packs*.

## De glint

| Bestand | Formaat | Waarom |
|---|---|---|
| `assets/minecraft/textures/misc/enchanted_glint_item.png` | 256×256 | grote pompoenen + brede strepen |
| `assets/minecraft/textures/misc/enchanted_glint_armor.png` | 1024×1024 | dicht veld kleine pompoenen |

Waarom twee verschillende ontwerpen: Minecraft schuift de glint over het model met een
texture-matrix, en de schaal daarvan verschilt per soort.

* **Items** gebruiken schaal `8.0`: de textuur wordt 8× herhaald over een sprite van 16 px, dus één
  tegel is ~2 item-pixels breed. Details zijn daar fysiek niet zichtbaar — je ziet een oranje
  schittering die over je zwaard schuift. Daarom staan er juist *grote* vormen op: die geven de
  variatie die je wél ziet.
* **Gedragen harnas** gebruikt schaal `0.16`: over een borststuk zie je maar ~2 % van de textuur,
  dus die wordt enorm uitvergroot. Daar staan daarom kleine pompoenen op (~1,7 % van de breedte),
  die op het harnas als grote gloeiende koppen voorbij komen.

Beide bestanden tegelen naadloos (de strepen komen uit band-gefilterde ruis in het frequentiedomein,
de pompoenen worden met wrap-around gestempeld). De `.png.mcmeta` zet `blur: true`, net als vanilla,
zodat de sterk uitvergrote harnas-glint glad blijft.

De glint wordt additief gemengd met `SRC_COLOR, ONE` — de kleur wordt dus effectief gekwadrateerd.
Daarom is zwart in de textuur "onzichtbaar" en is de rest ruim helder gehouden.

## Zelf aanpassen

Alles is procedureel gegenereerd; `generator/` bevat de bronscripts (Python + Pillow + NumPy).

```bash
pip install pillow numpy
cd generator
python3 glint.py  ../assets/minecraft/textures/misc   # glint-textures
python3 pack_icon.py ../pack.png                      # pack-icoon
python3 preview.py .                                  # sky-concept previews
```

* `skylib.py` — ruis, sterrenvelden, pompoen-/maan-/vleermuis-/boom-sprites, en de kubus-projectie
  (gnomonisch, dus vormen lopen naadloos door over de randen van de skybox).
* `concepts.py` — de vijf sky-ontwerpen.
* `glint.py` — de twee glint-sheets.
