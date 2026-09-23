# Leakestan (statische site)

Statische site: geen build, geen dependencies. Open `index.html` in de browser,
of zet de map op een host (GitHub Pages, Netlify, Vercel, eigen webserver).

```
leakestan-site/
├── index.html            # opbouw van de pagina
├── css/styles.css        # rood/zwart thema
├── js/app.js             # zoeken, filteren, sorteren, lightbox, downloads
├── js/fx.js              # intro, animaties, kantelende kaarten, scroll-balk
├── js/cursor.js          # eigen muiscursor
├── data/content.js       # ← DIT bestand pas je aan
└── assets/
    ├── blank.txt         # tijdelijke download ("blank")
    ├── logo.svg          # LK-logo (favicon + zijbalk)
    ├── wordmark.svg      # LK zonder kader
    └── previews/         # screenshots van de clients
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
{ id: "base-debug", name: "Base Debug", download: "", ... }
```

Leeg betekent: de knop serveert `assets/blank.txt` (inhoud: het woord `blank`)
en downloadt als `base-debug-blank.txt`. De knop werkt dus al, maar levert nog
niets echts op.

Later vul je de echte link in:

```js
download: "https://jouwhost.nl/clients/base-debug.zip",
```

Meer hoeft er niet te gebeuren — de knop wordt automatisch een echte download.

### 4. Items en afbeeldingen

Een item heeft maar vier dingen nodig:

```js
{
  id: "base-debug",              // uniek, gebruikt voor de link #item-base-debug
  name: "Base Debug",            // naam onder de afbeelding
  category: "clients",           // moet overeenkomen met een key hierboven
  image: "assets/previews/base-debug.webp",
  download: "",                  // leeg = blank
  added: "2026-09-22",           // bepaalt de volgorde en de "updated"-datum
}
```

De kaart toont afbeelding, naam eronder en daaronder de downloadknop. Het
nummer linksboven (`#01`, `#02`…) volgt de volgorde in dit bestand. De drie
nieuwste items verschijnen automatisch als uitgewaaierde stapel in de hero
(op schermen vanaf 1440px breed) en alle namen lopen door de ticker.

Eigen afbeeldingen: zet je bestanden (`.png`, `.jpg`, `.webp`) in
`assets/previews/` en wijs `image` ernaar. Beeldverhouding 16:9 past het beste;
andere formaten worden netjes bijgesneden.

## Wat de site doet

- Zoeken op naam of categorie (`/` of `Ctrl K` / `⌘ K` springt naar het zoekveld)
- Filteren per categorie via de zijbalk, met aantallen en een meeglijdende markering
- Sorteren op nieuwste of A→Z
- Wisselen tussen raster- en lijstweergave (keuze wordt onthouden)
- Klik op een afbeelding voor een grote weergave; blader met `←` `→`, sluit met `Esc`
- Link naar een specifiek item kopiëren via het schakel-icoon
- Werkt op telefoon: de zijbalk schuift in via de menuknop

## Details en effecten

- **Eigen cursor** — rode stip met een ring die meebeweegt. Boven een preview
  wordt het een rode cirkel met "View", boven de achtergrond van de grote
  weergave "Close", boven knoppen groeit de ring en in het zoekveld wordt het
  een tekstcursor. Alleen met een muis; op telefoon en tablet blijft alles normaal.
- **Intro** — kort LK-scherm bij het eerste bezoek (één keer per sessie).
- **Kaarten** — schuiven in beeld bij het scrollen, kantelen licht mee met de
  muis met een lichtvlek eroverheen, en tonen een laad-animatie tot de
  screenshot binnen is.
- **Hero** — groen "live"-bolletje met de datum van het nieuwste item, een
  glanzende kop, en een ticker met alle namen.
- **Kleine dingen** — voortgangsbalk bovenaan, knop terug naar boven, rimpel
  bij klikken op knoppen, groen vinkje na link kopiëren, meldingen met
  afteltijd-balk, rode tekstselectie en scrollbalk, filmkorrel en langzaam
  bewegend rood licht op de achtergrond.

Wie "minder beweging" heeft aanstaan in het besturingssysteem krijgt geen
intro, geen inschuivende kaarten en geen kantelen — alles staat dan meteen stil.

### Iets uitzetten

- Cursor: haal `<script src="js/cursor.js"></script>` weg uit `index.html`.
- Alle effecten: haal `<script src="js/fx.js"></script>` weg. De site blijft
  gewoon werken; er blijft niets onzichtbaar hangen.

## Let op

De afbeeldingen en namen zijn handmatig aangeleverd. Alleen de datums bij
`added` zijn verzonnen — die bepalen niets anders dan de volgorde bij
"Newest first". Er worden geen bestanden gehost of gelinkt: elke downloadknop
serveert `assets/blank.txt`.
