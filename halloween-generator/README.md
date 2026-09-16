# Halloween generator

Alle textures in `../halloween-sky` en `../halloween-glint` zijn procedureel gegenereerd; dit is
de bron. Python met Pillow en NumPy, verder niets.

```bash
pip install pillow numpy
cd halloween-generator

# de lucht (duurt ~1 min, controleert daarna zelf de naden)
python3 build_sky.py s_watcher 1024 ../halloween-sky/assets/halloween/textures/sky/watcher.png

# de twee glint-vellen
python3 glint.py ../halloween-glint/assets/minecraft/textures/misc

# de pack-iconen
python3 pack_icon.py ../halloween-sky/pack.png   eye
python3 pack_icon.py ../halloween-glint/pack.png pumpkin

# previews (perspectief + 360° panorama) van alle tien de luchten, of van een paar
python3 preview.py /tmp
python3 preview.py /tmp s_blood s_eclipse
python3 glint_preview.py ../halloween-glint/assets/minecraft/textures/misc
```

## Bestanden

| | |
|---|---|
| `skylib.py` | ruis, sterrenvelden, de pompoen-/maan-/vleermuis-/boom-sprites, en de kubus-, equirect- en perspectiefprojecties |
| `concepts.py` | de vijf eerste sky-ontwerpen |
| `scary.py` | de horror-props (kraaien, galg, skelethanden, hek, vogelverschrikker, spookhuis, ogen, geesten, spinnenweb, bliksem), de donkere manen en de vijf enge varianten |
| `build_sky.py` | rendert een ontwerp naar Nuit's 3×2 vel en verifieert de naden |
| `glint.py` | de twee glint-vellen |
| `preview.py`, `glint_preview.py`, `pack_icon.py` | previews en iconen |

## Een andere lucht in de pack zetten

| slug | lucht |
|---|---|
| `s_watcher` | De Wachter — *zit nu in de pack* |
| `s_blood` | Bloedmaan — donkerrode maan, kraaienzwerm, galgen |
| `s_eclipse` | Verduistering — zwarte maan met brandende ring, reuzenspinnenweb |
| `s_skull` | Schedelmaan — schedel laag boven het kerkhof, dikke mist, spoken |
| `s_storm` | Onweer — bliksem, zwaar wolkendek, vleermuiszwerm |
| `graveyard` | Kerkhof Nacht — de eerste, rustigere kerkhofversie |
| `bloodmoon`, `nebula`, `witching`, `void` | de vier niet-kerkhof concepten |

```bash
python3 build_sky.py s_storm 1024 ../halloween-sky/assets/halloween/textures/sky/storm.png
```

Pas daarna de `texture`-regel in `assets/nuit/sky/*.json` aan, en hernoem het JSON-bestand mee.
Zorg dat er maar **één** `.json` in `assets/nuit/sky/` staat: Nuit laadt ze allemaal en dan
renderen ze over elkaar heen.

## Waarom de naden kloppen

Sprites worden niet op het vel geplakt maar per pixel gnomonisch geprojecteerd vanuit
richtingsvectoren. Elk vlak wordt los gerenderd met dezelfde continue functie, dus een boom of
een oog dat over een kubusrand valt loopt vanzelf door op het buurvlak. `build_sky.py`
controleert dat na afloop: alle 12 kubusranden moeten door precies twee vlakken gedeeld worden
en de pixelrijen langs elke gedeelde rand moeten dezelfde kleur hebben (het script faalt bij een
gemiddelde afwijking boven 0,02; in de praktijk zit hij rond 0,004).
