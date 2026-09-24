# Leakestan (statische site)

Statische site: geen build, geen dependencies. Open `index.html` in de browser,
of zet de map op een host (GitHub Pages, Netlify, Vercel, eigen webserver).

```
leakestan-site/
├── index.html            # opbouw van de pagina
├── 404.html              # foutpagina voor kapotte links (staat helemaal op zichzelf)
├── css/styles.css        # rood/zwart thema
├── js/app.js             # zoeken, filteren, sorteren, lightbox, downloads
├── js/fx.js              # intro, animaties, kantelende kaarten, scroll-balk
├── js/cursor.js          # eigen muiscursor
├── data/content.js       # ← DIT bestand pas je aan
└── assets/
    ├── blank.txt         # tijdelijke download ("blank")
    ├── logo.svg          # LK-logo (favicon + zijbalk)
    ├── donut.png         # donut-logo naast de kop in de hero
    ├── wordmark.svg      # LK zonder kader
    ├── og-image.jpg      # plaatje dat Discord toont bij een geplakte link
    ├── apple-touch-icon.png  # icoon als iemand de site op zijn iPhone-beginscherm zet
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
  added: "2026-09-22",           // volgorde, "updated"-datum én het NEW-label

  // optioneel:
  tags: ["MC 1.21.11"],          // labels rechtsboven op de afbeelding
  focus: "50% 40%",              // welk deel van de afbeelding in beeld blijft
}
```

De kaart toont afbeelding, naam eronder en daaronder de downloadknop. De drie
nieuwste items verschijnen automatisch als uitgewaaierde stapel in de hero
(op schermen vanaf 1520px breed; daaronder is het donut-logo de blikvanger).

Eigen afbeeldingen: zet je bestanden (`.png`, `.jpg`, `.webp`) in
`assets/previews/` en wijs `image` ernaar. Beeldverhouding 16:9 past het beste;
andere formaten worden bijgesneden. Valt er iets belangrijks buiten beeld
(zoals de kop van een menu), schuif het dan terug met `focus`: het eerste getal
is links↔rechts, het tweede boven↔onder (`"50% 0%"` = bovenkant).

### 5. Labels

- **NEW** komt er vanzelf op bij alles wat in de laatste 7 dagen is toegevoegd
  (volgens `added`). Zet bij een nieuwe client dus de echte datum. Hoeveel dagen:
  `NEW_DAYS` bovenin `content.js` (0 = uit).
- **Eigen labels** zet je met `tags`, bijvoorbeeld de Minecraft-versie of
  `"Addon"`. Je kunt er ook op zoeken: `1.21` vindt alles met dat label.

### 6. Tellers in de hero

- **Clients** telt vanzelf hoeveel items er in de categorie `clients` staan.
- **Downloads** is een oplopende teller, geen echte telling (een statische site
  kan geen downloads tellen). Instellen met `DOWNLOADS` in `content.js`: hij
  stond op 4720 op 24 september 2026 en krijgt elke dag om middernacht (UTC)
  er willekeurig 20 tot 40 bij. Elke bezoeker ziet op dezelfde dag hetzelfde
  getal en het gaat nooit omlaag.

### 7. Discord-preview

Als iemand je link in Discord plakt, toont Discord `assets/og-image.jpg` met
de titel en beschrijving uit `index.html`. **Eén ding moet je doen zodra de
site online staat:** zet in `index.html` bij `og:image` en `twitter:image` het
volledige adres, bijvoorbeeld:

```html
<meta property="og:image" content="https://jouwdomein.nl/assets/og-image.jpg">
```

Discord kan een half adres (`assets/og-image.jpg`) niet altijd vinden. Na een
wijziging kan het even duren voordat Discord het nieuwe plaatje laat zien.

### 8. 404-pagina

`404.html` verschijnt vanzelf bij een kapotte link — GitHub Pages, Netlify en
Vercel pakken dat bestand automatisch op, zolang het in de hoofdmap van de site
staat. Staat de site in een submap (bijvoorbeeld `jouwnaam.github.io/leakestan/`),
zet dan bovenin `404.html` `data-home="/leakestan/"`. Bij een GitHub-projectpagina
gaat dat al vanzelf goed.

## Wat de site doet

- Zoeken op naam of categorie (`/` of `Ctrl K` / `⌘ K` springt naar het zoekveld)
- Filteren per categorie via de zijbalk, met aantallen en een meeglijdende markering
- Sorteren op nieuwste of A→Z
- Wisselen tussen raster- en lijstweergave (keuze wordt onthouden)
- Klik op een afbeelding voor een grote weergave; blader met `←` `→`, sluit met `Esc`
- Werkt op telefoon: de zijbalk schuift in via de menuknop

## Details en effecten

- **Rode muis** — een gewone muispijl, maar rood. Boven alles wat klikbaar is
  wordt het een rood handje, in het zoekveld een rood streepje. Bij elke klik
  een kleine rode explosie (op telefoon bij tikken). De grootte kies je met
  `CURSOR_SIZE` in `content.js`: 1 (klein) t/m 5 (groot); de explosie groeit mee.
- **Intro** — kort LK-scherm bij het eerste bezoek (één keer per sessie).
- **Kaarten** — schuiven in beeld bij het scrollen, kantelen licht mee met de
  muis met een lichtvlek eroverheen, en tonen een laad-animatie tot de
  screenshot binnen is.
- **Hero** — groen "live"-bolletje met de datum van het nieuwste item, een
  glanzende kop met een groot donut-logo ernaast, "Leakestan By Dexter", en de
  tellers Clients en Downloads, die bij het laden als een kilometerteller
  omhoog rollen naar het juiste getal.
- **Kleine dingen** — voortgangsbalk bovenaan, knop terug naar boven, meldingen met
  afteltijd-balk, rode tekstselectie en scrollbalk, filmkorrel en langzaam
  bewegend rood licht op de achtergrond.

Wie "minder beweging" heeft aanstaan in het besturingssysteem krijgt geen
intro, geen inschuivende kaarten en geen kantelen — alles staat dan meteen stil.

### Iets uitzetten

- Cursor: haal `<script src="js/cursor.js"></script>` weg uit `index.html`.
- Alle effecten: haal `<script src="js/fx.js"></script>` weg. De site blijft
  gewoon werken; er blijft niets onzichtbaar hangen.

## Let op

De afbeeldingen en namen zijn handmatig aangeleverd. Een paar zijn bijgewerkt:
bij Coffee Client is het watermerk van 9minecraft.net eraf geknipt, bij Radium
Client de zwarte balken boven en onder, en het menu van Krypton Avengers Addon
staat nu helemaal in beeld. Opsec Mod en Volt Client zijn maar 299 pixels breed
en blijven daardoor wat wazig — een groter origineel lost dat op.

De datums bij `added` zijn verzonnen; ze bepalen de volgorde en het NEW-label.
Er worden geen bestanden gehost of gelinkt: elke downloadknop serveert
`assets/blank.txt`.
