# Demo Catalog

Een schone, static catalogus-webapp (donker thema, item-grid, zoeken, filteren en
detailpagina's) met fictieve, legale voorbeeld-inhoud. Bedoeld om lokaal te draaien.

## Lokaal draaien

Static bestanden — je hebt alleen een simpele webserver nodig.

### Optie 1: Python (voorgeïnstalleerd op de meeste systemen)

```bash
cd demo-catalog
python3 -m http.server 8000
```

Open daarna **http://localhost:8000** in je browser.

### Optie 2: Node.js

```bash
cd demo-catalog
npx serve .
```

## Structuur

| Bestand        | Omschrijving                                  |
| -------------- | --------------------------------------------- |
| `index.html`   | Overzichtspagina met grid, zoeken en filters  |
| `item.html`    | Detailpagina (`item.html?id=<id>`)            |
| `styles.css`   | Alle styling (donker thema)                   |
| `app.js`       | Rendering-logica voor overzicht + detail      |
| `data.js`      | De voorbeeld-items — vervang door je eigen    |

## Eigen inhoud

Pas `data.js` aan: elk item is een object met o.a. `id`, `name`, `category`,
`author`, `short`, `description` en `tags`. Voeg toe of verwijder naar wens —
de rest van de site past zich automatisch aan.
