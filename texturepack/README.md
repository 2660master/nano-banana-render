# Verdant — natuur-texturepack voor Minecraft 1.21.11

Een 16×16 resourcepack in een natuurthema (bos, blad, steen, hars, dauw, wortel).
Alle texturen worden **procedureel gegenereerd** uit tekenkaarten in `tools/`, zodat
de hele set één consistente stijl en één palet deelt.

## Status

| Deel | Inhoud | Status |
|---|---|---|
| 1 | Items, gereedschap & wapens (selectie van 65) | goedgekeurd |
| 2 | Bouwblokken | goedgekeurd |
| 3 | Natuurblokken: aarde, gras, blad, erts, zand, planten, gewassen | goedgekeurd |
| 4 | Lucht, weer, water en lava | **klaar — ter beoordeling** |
| 5 | Geluiden | gepland |
| 6 | Dieren (geen monsters) | gepland |
| — | Resterende items (harnas, schild, gereedschap, potions, …) | volgt na akkoord |

## Afgesproken scope

Vastgelegd na de eerste keuringsronde:

**Lucht — alleen vanilla.** Er komt geen OptiFine- of FabricSkyBoxes-laag. Dat
betekent concreet: `sun.png`, `moon_phases.png`, `clouds.png` en `end_sky.png`
krijgen een natuurbehandeling. Bergen, vogels en gelaagde wolken aan de hemel
kunnen daarmee niet — een vanilla-resourcepack kan de skybox zelf niet
vervangen. De lucht blijft dus subtiel: warmere zon, zachtere maan, organischere
wolkenvorm.

**Geluid — drie groepen, geen mobs.**

1. Gevecht & totem: zwaardhits, kritieke treffers, totem-pop, schade, level-up.
2. Voetstappen & blokken: gras, steen, hout, zand; plaatsen en breken.
3. Sfeer & omgeving: regen, donder, deuren, kisten, water, grot-ambience.

Mobgeluiden blijven vanilla. Alle klanken worden gesynthetiseerd (ruisfilters
voor blad en wind, toonvegen voor water en vogels, houtklopjes voor hits) en
geleverd als mono OGG Vorbis via `sounds.json`. Dit werkt zonder mods.

**Blokken — bouwblokken eerst.** Planken, bakstenen, beton, wol, glas, trappen
en muren gaan voor op aarde, steen, erts en zand.

**Dieren wel, monsters niet.** Koeien, schapen, varkens, kippen en papegaaien
komen in het natuurthema; monster-texturen blijven vanilla.

## Prestaties

De pack blijft strikt op **16×16**, precies de vanilla resolutie. Geen enkele
texture is groter, er zitten geen shaders, geen extra modellen en geen animaties
met veel frames in. Daardoor is de atlas even groot als vanilla en is de impact
op FPS en VRAM nul.

## Installeren

1. Pak `dist/Verdant-1.21.11.zip`.
2. Zet het bestand in `.minecraft/resourcepacks/`.
3. In Minecraft: **Options → Resource Packs** → Verdant naar rechts schuiven.

Vereist Minecraft Java **1.21.11** (`pack_format` 75). Het pack draait ook op
1.21.7–1.21.10 via `supported_formats`.

## Zelf bouwen

```bash
pip install Pillow
cd texturepack/tools
python3 build.py           # schrijft ../Verdant/ en ../dist/*.zip
python3 preview.py         # overzichtsplaat items
python3 preview_blocks.py  # overzichtsplaat blokken
python3 make_review_page.py  # keuringspagina
```

## Mappen

```
texturepack/
├── Verdant/            het pack zelf (uitgepakt)
├── dist/               zip + previewplaat
└── tools/
    ├── palette.py      kleuren per materiaal-tier
    ├── render.py       tekenkaart -> PNG (schaduw, rand, spikkels)
    ├── sprites_tools.py  5 gereedschapsvormen
    ├── sprites_items.py  losse items
    ├── blocks.py       procedurele blokpatronen (planken, ringen, mos, voegen)
    ├── sprites_blocks.py  blokcatalogus met natuurpaletten
    ├── build.py        bouwt pack + zip
    ├── preview.py      overzichtsplaat items
    ├── sky.py         lucht, weer, water en lava
    ├── preview_blocks.py  overzichtsplaat blokken
    └── make_review_page.py  keuringspagina
```

## Materiaal-tiers

Elke vanilla-tier is hertaald naar een natuurmateriaal, met dezelfde steel en
hetzelfde blaadje op elk stuk gereedschap:

| Vanilla | Verdant | Kleur |
|---|---|---|
| wood | Twijghout | licht, warm hout |
| stone | Moskei | grijze kei met mosspikkels |
| iron | Berksteen | bleke, koele steen |
| gold | Amber | warme hars |
| diamond | Dauwkristal | cyaan kristal |
| netherite | Sintelwortel | verkoold hout met sintels |


## Blokpatronen

De blokken worden niet met de hand getekend maar procedureel opgebouwd uit
een handvol patronen in `blocks.py`. Elk patroon tegelt naadloos: structuur
wordt met modulo-rekenen op 16 gelegd en de ruis is puur een functie van
`(x % 16, y % 16)`.

| Patroon | Gebruikt voor |
|---|---|
| `planks` | alle plankensoorten — vier lange gangen, nerf loopt horizontaal door |
| `log_side` / `log_top` | bast en jaarringen; berk krijgt zijn zwarte streepjes |
| `bricks` | metselwerk in halfsteensverband |
| `cobble` | tegelbare Voronoi voor keien en cobbled deepslate |
| `stone` | gevlekte steen, met losse spikkels voor graniet en dioriet |
| `fabric` | wol, met opstaande pluisjes |
| `smooth` / `powder` | beton en betonpoeder |
| `clay` | terracotta met horizontale sliblagen |
| `glass` | ruit met doorlopende rand en instelbare dichtheid |
| `moss_over` | mos in plukken over kei en metselwerk, sterker naar boven |
| `leaves` | overlappende blaadjesclusters met gaten in het bladerdek |
| `ore` | ertsklodders in het gastgesteente, lichte kern en donkere rand |
| `sand` / `grass_top` / `grass_side` | zand, graskop en de kraag op de blokzijde |
| `ice` | doorschijnend ijs met scheuren |

## Texturen die het spel zelf inkleurt

Een paar texturen worden door Minecraft met de biome-kleur vermenigvuldigd.
Die staan hier bewust bleek en bijna neutraal — een verzadigd groene texture
zou in-game veel te donker uitkomen.

| Texture | Wordt ingekleurd |
|---|---|
| `grass_block_top`, `grass_block_side_overlay` | ja, grijswaarden |
| `oak/spruce/birch/jungle/acacia/dark_oak/mangrove_leaves` | ja, ontzadigd |
| `short_grass`, `fern`, `tall_grass_*`, `large_fern_*`, `vine`, `sugar_cane` | ja, bleek grijsgroen |
| `cherry_leaves`, `azalea_leaves`, `pale_oak_leaves` | nee, vaste kleur |
| bloemen, gewassen, mos, glow lichen | nee, vaste kleur |


## Lucht, weer en vloeistoffen

Alles staat op vanilla-formaat, dus er verandert niets aan de kosten.

| Texture | Formaat | Bijzonderheid |
|---|---|---|
| `environment/sun.png` | 32x32 | warme amberkern met krans |
| `environment/moon_phases.png` | 128x64 | acht schijngestalten in een raster van 4 x 2 |
| `environment/clouds.png` | 256x256 | alpha bepaalt de wolk |
| `environment/end_sky.png` | 16x16 | getegeld over de end-hemel |
| `environment/rain.png`, `snow.png` | 32x32 | |
| `block/water_still.png` | 16x512 | 32 frames, frametime 2 |
| `block/water_flow.png` | 32x1024 | 32 frames, frametime 1 |
| `block/lava_still.png` | 16x320 | 20 frames, frametime 2 |
| `block/lava_flow.png` | 32x640 | 20 frames, frametime 3 |

De animaties zijn opgebouwd uit sinusfases: frame N gebruikt fase `2*pi*N/F`,
dus het laatste frame sluit exact aan op het eerste en de lus springt nooit.

**Wolken en FPS.** Minecraft bouwt echte wolkendozen uit elke pixel in
`clouds.png` met alpha > 0. Meer wolk is dus letterlijk meer geometrie. De
dekking blijft daarom rond de 34%, ongeveer vanilla, en de alpha is hard
afgesneden op 0 of 255 — zachte randen zouden alleen maar extra dozen opleveren.
