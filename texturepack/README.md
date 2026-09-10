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
| 4 | Lucht, weer, water en lava | goedgekeurd |
| 5 | Geluiden (73 klanken) | goedgekeurd |
| 6 | Resterende items (225 in totaal) | **klaar — ter beoordeling** |
| 7 | Boerderijdieren en wolven | **klaar — moet in het spel gecheckt** |
| 8 | CPvP: mace, drietand, kruisboog, elytra, schild, end crystal, obsidian, respawn anchor | **klaar** |
| — | Overige dieren (paard, vos, papegaai, bij, …) | wacht op bevestiging dat de uitvouwing klopt |

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
    ├── sounds.py      synthese-gereedschap (ruis, filters, tonen, enveloppen)
    ├── sound_catalog.py  het geluidsontwerp zelf
    ├── sound_events.py   koppeling naar Minecraft-gebeurtenissen
    ├── sound_preview.py  geluidsgedeelte van de keuringspagina
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
| `environment/sun.png` | 64x64 | hete kern, glad verloop, zachte krans |
| `environment/moon_phases.png` | 256x128 | acht fasen van 64x64, met zeeen en kraters |
| `environment/clouds.png` | 256x256 | alpha bepaalt de wolk — bewust niet groter |
| `environment/end_sky.png` | 64x64 | sterrenveld met vage nevel |
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


## Geluid

73 klanken, van nul gesynthetiseerd uit ruis en toon — er zitten geen samples
in het pack. Mono, 44100 Hz, OGG Vorbis. **Mono is niet optioneel**: Minecraft
plaatst alleen mono-geluiden in de ruimte. Een stereobestand klinkt overal
even hard, waar de bron ook staat.

`assets/minecraft/sounds.json` koppelt 53 gebeurtenissen aan die bestanden,
elk met `"replace": true` zodat de vanilla-varianten er niet doorheen blijven
spelen, en met de vanilla subtitle-sleutels zodat ondertiteling blijft werken.

| Groep | Klankidee |
|---|---|
| Gevecht | hout op hout, met een wolk ritselend blad eroverheen |
| Totem | lage bonk, opbloeiend groot akkoord, vogels die opvliegen |
| Voetstappen | kort en zacht, vier varianten per ondergrond tegen het ratelen |
| Breken | dezelfde klankwereld, langer en met meer lichaam |
| Weer | regen met trage golving, donder als scheur plus wegzakkende rommel |
| Grot | lage bromtoon van twee ontstemde sinussen, met een druppel in de verte |
| Scharnieren | stijgende toon met beving, plus een houten rand |

De bouwstenen staan in `sounds.py`: gefilterde ruis, onharmonische partialen
voor hout en steen, toonvegen voor vogels en water, en een biquad voor de
band- en laagdoorlaatfilters.

**Prestaties.** Geluid draait op de audio-thread, niet op de renderthread.
Het pack voegt hier dus niets toe aan de frametijd.


## Dieren

Dier-texturen zijn geen platte plaatjes maar **uitgevouwen modellen**: elk
kubusje van het model pakt een vast rechthoekje uit het vel. Die indeling
staat in de modelcode van het spel, niet in de texture.

De vanilla-bestanden waren hier niet op te halen — Mojang's servers zijn
achter de proxy geblokkeerd — dus de gezichten zijn berekend met de
standaard doos-uitvouwing uit `sprites_entity.box_uv`:

| Vlak | Positie |
|---|---|
| voorkant | `(u + d, v + d)`, breedte `w`, hoogte `h` |
| achterkant | `(u + d + w + d, v + d)` |
| links | `(u, v + d)`, breedte `d` |
| rechts | `(u + d + w, v + d)`, breedte `d` |
| boven | `(u + d, v)`, hoogte `d` |
| onder | `(u + d + w, v)` |

De kop-dozen staan in `sprites_entity.HEADS`. Het hele vel wordt met vacht
gevuld: valt de uitvouwing een paar pixels anders uit, dan zie je dat aan
een egale vacht nauwelijks. **Alleen de gezichten moeten kloppen, en die
moeten in het spel gecontroleerd worden.** Klopt het, dan volgen de
overige dieren; klopt het niet, dan is er één getal per dier dat verschuift.


## CPvP-uitrusting

De mace gebruikt dezelfde bast-steel, touwgreep en rank als het gereedschap
uit deel 1, zodat hij bij de rest van het pack hoort. De kop deelt het
sintelwortel-palet met netherite.

De kruisboog wordt met één functie gebouwd, `sprites_cpvp.crossbow(pull, ammo)`:
`pull` schuift de pees omlaag (0 t/m 3), `ammo` tekent wat er op de kolf ligt.
Zo blijven de acht standen — standby, drie spanstanden, pijl en vuurwerk —
gegarandeerd identiek op de pees en de lading na.

Verder: obsidiaan, huilend obsidiaan, glowstone, netherite-blok, respawn
anchor in alle vijf de laadstanden, betoveringstafel en aambeeld.

Elytra, drietand, schild, end crystal en de enderkist zijn uitgevouwen
modellen, net als de dieren. Die vellen zijn volledig gevuld, dus een
verschuiving in de uitvouwing valt daar nauwelijks op.

## Beeld van de lucht

`tools/render_sky.py` zet zon, maan en wolken in perspectief op een vlak
boven de speler, zoals het spel dat ook doet, en zet er een blokkig
heuvelsilhouet onder. Zo zie je hoe de lucht er echt uit gaat zien in
plaats van alleen de platte bestanden.


## Belichting

Twee lichtmodellen, allebei in code, geen enkele pixel met de hand bijgetekend.

**Items** (`shading.py`). Uit het silhouet komt een afstandsveld: hoe diep
zit een pixel in de vorm. Dat veld is in feite een hoogtekaart, en de
helling ervan geeft de normaal van het oppervlak. Daar valt Lambert-licht
op uit linksboven, plus een glans. Elk item krijgt zo vanzelf een bolle
lichtkant en een zachte schaduw ervan af.

**Blokken** (`blocks.emboss`). Daar kan het silhouet niet gebruikt worden —
een blok heeft geen rand, het herhaalt. Dus wordt de eigen helderheid van
de texture als hoogtekaart gelezen en de buren modulo 16 genomen. Zo blijft
het reliëf naadloos tegelen.

In allebei verschuift de kleur mee met de helderheid: licht loopt naar warm,
schaduw naar koel. Dat is wat pixelkunst geverfd laat ogen in plaats van
uitgebleekt.

## Vogels

Een resourcepack kan niets in de lucht laten vliegen — daar zit geen texture
achter, en zonder mod is er geen laag om iets aan toe te voegen. Wat wel kan:
de dieren die in het spel al vliegen mooier maken. Daarom zitten er nu vijf
papegaaien, een vleermuis en een allay in het pack.

De vogels op `verdant-lucht-foto.png` zijn onderdeel van die tekening, niet
van het pack.


## CPvP, item voor item gekozen

Elk stuk is als vier varianten voorgelegd en één is gekozen:

| Item | Keuze |
|---|---|
| End crystal | groen, geslepen facetten |
| Respawn anchor | groen venster dat volloopt |
| Mace | geflensde kop met verticale ribben |
| Drietand | groen kristal, dikke tanden |
| Kruisboog | donker hout |
| Elytra | donker blad met felgroene nerf |
| Schild | mossteen |
| Obsidian | zwart-paars (bestaande won) |
| Crying obsidian | veel kleine paarse tranen |
| Glowstone | honingkleurig |
| Enderkist | donker met groen slot (bestaande won) |
| Aambeeld | mossteen |
| Betoveringstafel | groen-donker met lichtgroene runen |
| Breeze rod | amber |
| Totem, wind charge, heavy core | vanilla |

**Vanilla laten staan** gebeurt via de `VANILLA`-lijst in `build.py`: die
namen slaan we over bij het schrijven, en wat niet in het pack zit haalt
Minecraft uit zijn eigen bestanden. Dat is de nette manier om een item
onaangeroerd te laten — een kopie van de originele texture meeleveren zou
dat ook doen, maar dan sleep je andermans werk mee.


## Waarom de zon groter mag en de wolken niet

Zon, maan en end-hemel zijn gewone texturen: groter betekent alleen een
gladder verloop en minder zichtbare herhaling, en kost een paar honderd
kilobyte videogeheugen. Die staan daarom nu op 64x64 en 256x128.

`clouds.png` is een ander geval. Minecraft bouwt uit elke pixel met
alpha > 0 een echte wolkendoos. De resolutie van dat bestand bepaalt dus
hoeveel geometrie er in de lucht hangt. Die blijft daarom op 256x256, en
de dekking op 30% — iets onder de vorige 34%, dus er komt zelfs iets
minder geometrie bij dan eerst.

**Uitrekken zonder de naad te breken.** Echte wolken liggen langgerekt
langs de wind. De eerste poging schaalde de x-coordinaat, maar dan loopt
het ruisrooster niet meer rond op de textuurbreedte en zie je een
verticale naad in de lucht. `value_noise2` neemt in plaats daarvan minder
cellen in x dan in y: hetzelfde uitgerekte effect, en het wrapt weer
netjes. Gemeten verschil op de naad: 0, tegen 4 binnenin de texture.
