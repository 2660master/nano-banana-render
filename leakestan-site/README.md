# Leakestan — pack archive (statische site)

Statische site: geen build, geen dependencies. Open `index.html` in de browser,
of zet de map op een host (GitHub Pages, Netlify, Vercel, eigen webserver).

```
leakestan-site/
├── index.html            # opbouw van de pagina
├── css/styles.css        # blauw thema
├── js/app.js             # zoeken, filteren, sorteren, lightbox, downloads
├── data/packs.js         # ← DIT bestand pas je aan
└── assets/
    ├── blank.txt         # tijdelijke download ("blank")
    ├── logo.svg
    └── previews/*.svg    # placeholder-afbeeldingen
```

## Wat je aanpast

Alles staat in **`data/packs.js`**. Verder hoef je nergens in te duiken.

### 1. Discord-link

```js
DISCORD_INVITE: "https://discord.gg/jouwinvite",
```

Zolang dit leeg is, staan de drie Discord-knoppen (zijbalk, bovenbalk, footer)
in een grijze "nog niet ingesteld"-stand en tonen ze een melding bij klikken.
Zodra je de invite invult, worden het gewone links die in een nieuw tabblad openen.

### 2. De downloadknoppen

Elk pack heeft een `download`-veld. Dat staat nu bewust **leeg**:

```js
{ id: "azure-edge", name: "Azure Edge 16x", download: "", ... }
```

Leeg betekent: de knop serveert `assets/blank.txt` (inhoud: het woord `blank`)
en downloadt als `azure-edge-blank.txt`. De knop werkt dus al, maar levert nog
niets echts op.

Later vul je de echte link in:

```js
download: "https://jouwhost.nl/packs/azure-edge.zip",
```

Meer hoeft er niet te gebeuren — de knop wordt automatisch een echte download.

### 3. Packs en afbeeldingen

Een item in de lijst ziet er zo uit:

```js
{
  id: "azure-edge",              // uniek, gebruikt voor de link #pack-azure-edge
  name: "Azure Edge 16x",        // naam onder de afbeelding
  category: "PvP",               // vult automatisch het menu links
  image: "assets/previews/azure-edge.svg",
  download: "",                  // leeg = blank
  resolution: "16x",
  size: "4.2 MB",
  added: "2026-09-18",           // bepaalt de "Newest first"-sortering
  hits: 18420,
  featured: true,                // zet het "Hot"-label op de afbeelding
}
```

Eigen afbeeldingen: zet je bestanden (`.png`, `.jpg`, `.webp`) in
`assets/previews/` en wijs `image` ernaar. Beeldverhouding 16:9 past het beste;
andere formaten worden netjes bijgesneden.

De categorieën in de zijbalk worden uit de `category`-velden opgebouwd, inclusief
de aantallen. Je hoeft daar niets apart voor bij te houden.

## Wat de site doet

- Zoeken op naam, categorie of resolutie (`/` springt naar het zoekveld)
- Filteren per categorie via de zijbalk
- Sorteren op nieuwste, meest gedownload of A→Z
- Wisselen tussen raster- en lijstweergave (keuze wordt onthouden)
- Klik op een afbeelding voor een grote weergave met downloadknop (Esc sluit)
- Link naar een specifiek pack kopiëren via het schakel-icoon
- Werkt op telefoon: de zijbalk schuift in via de menuknop

## Let op

De afbeeldingen zijn zelfgemaakte placeholders en de teksten, namen en
aantallen zijn voorbeelden. Vervang ze door je eigen materiaal.
