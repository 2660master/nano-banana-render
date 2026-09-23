# Leakestan (statische site)

Statische site: geen build, geen dependencies. Open `index.html` in de browser,
of zet de map op een host (GitHub Pages, Netlify, Vercel, eigen webserver).

```
leakestan-site/
├── index.html            # opbouw van de pagina
├── css/styles.css        # rood/zwart thema
├── js/app.js             # zoeken, filteren, sorteren, lightbox, downloads
├── data/content.js       # ← DIT bestand pas je aan
└── assets/
    ├── blank.txt         # tijdelijke download ("blank")
    ├── logo.svg          # LK-logo (favicon + zijbalk)
    ├── wordmark.svg      # LK zonder kader
    └── previews/*.svg    # placeholder-afbeeldingen
```

## Wat je aanpast

Alles staat in **`data/content.js`**. Verder hoef je nergens in te duiken.

### 1. Discord-link

```js
DISCORD_INVITE: "https://discord.gg/jouwinvite",
```

Zolang dit leeg is, staan de drie Discord-knoppen (zijbalk, bovenbalk, footer)
in een grijze "nog niet ingesteld"-stand en tonen ze een melding bij klikken.
Zodra je de invite invult, worden het gewone links die in een nieuw tabblad openen.

### 2. Categorieën

```js
CATEGORIES: [
  { key: "home",     label: "Home",     icon: "home" },
  { key: "clients",  label: "Clients",  icon: "file" },
  { key: "tools",    label: "Tools",    icon: "tool" },
  { key: "ratters",  label: "Ratters",  icon: "bug"  },
  { key: "scammers", label: "Scammers", icon: "warn" },
],
```

`home` is bijzonder: die toont álle items. De rest filtert op `key`. Een
categorie zonder items toont vanzelf een "nog leeg"-blok — daar hoef je niets
voor te doen. Beschikbare iconen: `home`, `file`, `tool`, `bug`, `warn`, `dot`.

### 3. De downloadknoppen

Elk item heeft een `download`-veld. Dat staat nu bewust **leeg**:

```js
{ id: "client-01", name: "Client 01", download: "", ... }
```

Leeg betekent: de knop serveert `assets/blank.txt` (inhoud: het woord `blank`)
en downloadt als `client-01-blank.txt`. De knop werkt dus al, maar levert nog
niets echts op.

Later vul je de echte link in:

```js
download: "https://jouwhost.nl/clients/client-01.zip",
```

Meer hoeft er niet te gebeuren — de knop wordt automatisch een echte download.

### 4. Items en afbeeldingen

Een item heeft maar vier dingen nodig:

```js
{
  id: "nova-addon",              // uniek, gebruikt voor de link #item-nova-addon
  name: "Nova Addon",            // naam onder de afbeelding
  category: "clients",           // moet overeenkomen met een key hierboven
  image: "assets/previews/nova-addon.svg",
  download: "",                  // leeg = blank
  added: "2026-09-18",           // bepaalt alleen de "Newest first"-sortering
}
```

De kaart toont precies dat: afbeelding, naam eronder, daaronder de
downloadknop. Verder niets.

Eigen afbeeldingen: zet je bestanden (`.png`, `.jpg`, `.webp`) in
`assets/previews/` en wijs `image` ernaar. Beeldverhouding 16:9 past het beste;
andere formaten worden netjes bijgesneden.

## Wat de site doet

- Zoeken op naam, categorie of versie (`/` springt naar het zoekveld)
- Filteren per categorie via de zijbalk, met aantallen
- Sorteren op nieuwste, meest bekeken of A→Z
- Wisselen tussen raster- en lijstweergave (keuze wordt onthouden)
- Klik op een afbeelding voor een grote weergave met downloadknop (Esc sluit)
- Link naar een specifiek item kopiëren via het schakel-icoon
- Werkt op telefoon: de zijbalk schuift in via de menuknop

## Let op

De afbeeldingen en namen zijn handmatig aangeleverd. Alleen de datums bij
`added` zijn verzonnen — die bepalen niets anders dan de volgorde bij
"Newest first". Er worden geen bestanden gehost of gelinkt: elke downloadknop
serveert `assets/blank.txt`.
