# Kerst Sky voor Nuit — Minecraft 1.21.11

Twee complete kersthemel-resourcepacks voor de **Nuit** mod (de opvolger van
FabricSkyboxes). Kies er één — of installeer ze allebei en zet de pack die je
wil bovenaan in de resourcepack-lijst.

| | Variant A — *Stille Nacht* | Variant B — *Kerstmarkt* |
|---|---|---|
| Sfeer | koel, ingetogen, "heilige nacht" | warm, gezellig, feestelijk |
| Kleuren | diep indigo en staalblauw | pruim, magenta en amber |
| Blikvanger | de Kerstster met lange lichtstaart | kerstboom-sterrenbeeld |
| Sneeuwman | in het oosten, met groene sjaal | in het zuiden, met rode sjaal |
| Verder | noorderlicht in groen met rode toppen, melkweg | lichtjesslingers rond de hele hemel, rood-groene suikerstokwolken |
| Preview | `previews/a-ingame.png`, `previews/a-sneeuwman.png`, `previews/a-panorama.png` | `previews/b-ingame.png`, `previews/b-sneeuwman.png`, `previews/b-panorama.png` |

Beide varianten hebben een **sneeuwman-sterrenbeeld**: drie ballen, hoge hoed,
takarmen, kooloogjes, een wortelneus en een sjaal in de kleur van de hemel.
Hij staat vast aan de horizon (draait niet mee), zodat je hem altijd op
dezelfde plek terugvindt.

Beide packs laten de dag-hemel, zon en maan gewoon met rust: de kersthemel
fade't in bij zonsondergang en weer uit bij zonsopkomst.

## Wat je nodig hebt

- Minecraft Java **1.21.11**
- De mod **Nuit** (Fabric of NeoForge) — <https://modrinth.com/mod/nuit>
- Fabric API (bij Fabric)

Zonder de Nuit-mod doet het pack niets; het bevat geen vanilla-texturen.

## Installeren

1. Pak `variant-a-stille-nacht.zip` of `variant-b-kerstmarkt.zip` (niet uitpakken).
2. Zet de zip in je `.minecraft/resourcepacks` map.
3. Start Minecraft, ga naar **Opties → Resourcepacks** en schuif de pack naar rechts.
4. Ga in-game naar de nacht (`/time set night`) om het resultaat te zien.

Wil je wisselen: zet gewoon de andere pack aan. De twee packs gebruiken
dezelfde JSON-bestandsnamen, dus als je ze allebei aanzet wint de bovenste —
ze gaan elkaar dus niet zitten stapelen.

## Hoe het in elkaar zit

Elke pack bestaat uit vier lagen in `assets/nuit/sky/`:

| Bestand | Type | Wat het doet |
|---|---|---|
| `00_vanilla_sky.json` | `overworld` | houdt de gewone daghemel, zonsopkomst en zonsondergang intact |
| `10_kerst_sky.json` | `square-textured` | de geschilderde kersthemel; staat stil, want horizon-gloed en noorderlicht horen aan de horizon vast te zitten |
| `20_kerst_stars.json` | `square-textured`, blend `add` | het sterrenveld; draait mee met de zon zoals vanilla-sterren |
| `30_decorations.json` | `decorations` | zon en maan blijven, vanilla-sterren uit (de textuur levert z'n eigen sterren) |

De texturen staan in `assets/kerstsky/textures/sky/` en zijn
3×2-kubuskaarten van 3072×2048 (1024 px per vlak), in de indeling die Nuit
verwacht:

```
kolom:     0          1          2
rij 0:   bottom      top       south
rij 1:    west      north      east
```

## Zelf aanpassen

**Sterren draaien de verkeerde kant op?** In `20_kerst_stars.json`, zet
`"axis": {"0": [90.0, 0.0, 0.0]}` om naar `[-90.0, 0.0, 0.0]`.

**Liever een stilstaande sterrenhemel?** Zet in hetzelfde bestand
`"speed"` op `0.0`.

**Vanilla-sterren er toch bij?** Zet in `30_decorations.json`
`"showStars"` op `true`.

**Andere fade-tijden?** De `keyFrames` in `10_kerst_sky.json` en
`20_kerst_stars.json` zijn ticks van een Minecraft-dag (0 = 6:00 's ochtends,
12000 = 18:00, 18000 = middernacht). Nu: onzichtbaar overdag, volledig zichtbaar
tussen tick 13400 en 22200.

**Ook in de Nether of End?** Haal het `conditions`-blok weg, of voeg de
dimensie toe aan `entries`.

## Opnieuw genereren

De texturen zijn volledig procedureel; er is geen Photoshop aan te pas gekomen
en er zijn geen externe libraries nodig (geen Pillow, geen numpy):

```bash
python3 tools/generate_sky.py              # 1024 px per vlak (zoals geleverd)
python3 tools/generate_sky.py --quick      # snelle lage-resolutie testronde
python3 tools/generate_sky.py --only a     # alleen variant A
```

Alles wordt in *richtingsruimte* geschilderd — elke pixel wordt eerst een
3D-richting — waardoor de zes kubusvlakken naadloos op elkaar aansluiten en je
composities in azimut/hoogte kunt uitdrukken ("de ster 39° boven de zuidelijke
horizon"). De kleuren van de hemel worden in lineair licht opgeteld en pas bij
het wegschrijven naar sRGB omgezet.

- `tools/skylib.py` — PNG-schrijver, kubusvlakken, noise, schilder-primitieven
- `tools/generate_sky.py` — de twee scènes, het sterrenveld, previews en packbouw
