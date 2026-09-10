# Verdant — natuur-texturepack voor Minecraft 1.21.11

Een 16×16 resourcepack in een natuurthema (bos, blad, steen, hars, dauw, wortel).
Alle texturen worden **procedureel gegenereerd** uit tekenkaarten in `tools/`, zodat
de hele set één consistente stijl en één palet deelt.

## Status

| Deel | Inhoud | Status |
|---|---|---|
| 1 | Items, gereedschap & wapens | **klaar — ter beoordeling** |
| 2 | Blokken (aarde, steen, hout, blad, erts, …) | wacht op akkoord op deel 1 |
| 3 | Lucht (zon, maan, wolken, end-sky) | gepland |
| 4 | Geluiden (zachte natuurklanken) | gepland |

## Prestaties

De pack blijft strikt op **16×16**, precies de vanilla resolutie. Geen enkele
texture is groter, er zitten geen shaders, geen extra modellen en geen animaties
met veel frames in. Daardoor is de atlas even groot als vanilla en is de impact
op FPS en VRAM nul.

## Installeren

1. Pak `dist/Verdant-1.21.11-items.zip`.
2. Zet het bestand in `.minecraft/resourcepacks/`.
3. In Minecraft: **Options → Resource Packs** → Verdant naar rechts schuiven.

Vereist Minecraft Java **1.21.11** (`pack_format` 75). Het pack draait ook op
1.21.7–1.21.10 via `supported_formats`.

## Zelf bouwen

```bash
pip install Pillow
cd texturepack/tools
python3 build.py      # schrijft ../Verdant/ en ../dist/*.zip
python3 preview.py    # schrijft ../dist/verdant-items-preview.png
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
    ├── build.py        bouwt pack + zip
    └── preview.py      overzichtsplaat
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
