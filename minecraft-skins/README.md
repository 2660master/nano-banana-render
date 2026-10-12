# Kerst & Blad Skins

Minecraft-skins (64×64, Java en Bedrock) met een preview-website:

- **35 kerstskins**: 5 kerstversies van de skin van elk van de spelers `spawnerbase`, `2660master`, `stitchcpvp`, `akosdebeste`, `pickzugng`, `johnpork400` en `ITZberryTT_x`.
- **5 bladskins**: bladwezens die geen basis-skin nodig hebben.

Open `index.html` in een browser voor de preview: een 3D-weergave met loop-, ren- en zwaai-animatie, voor- en achterkant per skin, en downloads als PNG of als ZIP.

## Hoe de kerstversies gemaakt worden

De eigen skin blijft staan: gezicht, haar, kleding en de tweede laag. Er komen alleen kerstaccessoires bij, meestal op de tweede laag, zodat de speler herkenbaar blijft. De generator kijkt naar de skin zelf: waar de mouwen eindigen (voor manchetten en lichtjes), welke kleuren het shirt heeft (voor de muts en de kersttrui) en of het een slim-skin is (armen van 3 px). Oude 64×32-skins worden omgezet.

| Versie | Wat erbij komt |
| --- | --- |
| Kerstmuts | Rode kerstmuts met pompon op de rug, bontkraag, bontmanchetten waar de mouwen eindigen, hulsttakje op de borst |
| Winterwarm | Gebreide muts in de eigen shirtkleur, gestreepte sjaal met franje, gebreide wanten, sneeuw op muts, schouders en schoenen |
| Kerstlichtjes | Twee lichtslingers rond de romp, lampjes in spiraal om de armen, lichtjeskrans om het hoofd, gouden ster |
| Rendier | Gewei en oortjes, rode Rudolph-neus, rood lint met gouden belletje, wit staartje |
| Kersttrui | Het eigen shirt omgebreid: breisteek in de eigen kleuren, kerstboom voor, sneeuwvlok achter, zigzag- en stippenbanden |

| Bladwezen | Details |
| --- | --- |
| Eikenwachter | Eikenblad, takkenkroon, eikels, amberkleurige ogen |
| Herfstgeest | Rood-oranje-goud blad, vliegenzwammen, vallende blaadjes |
| Bloesemdryade | Kersenbloesem, bloesemkroon, bloesemtak over de rug |
| Azaleahoeder | Azaleablad met magenta bloemen, mosmat op de schouders |
| Junglegeest | Junglegroen blad, hangende lianen met gloeibessen, cyaan ogen |

## De echte skins van de spelers

Toen dit gemaakt werd waren de Minecraft-servers niet bereikbaar, dus de kerstskins zijn nog gemaakt van een neutrale voorbeeldbasis (`skins/kerst/_voorbeeldbasis/`). Er zijn twee manieren om de echte versies te maken:

1. **In de website**: klik bij een speler op *Skin laden* (of sleep de PNG op de rij van die speler); de vijf kerstversies worden dan meteen van die skin gemaakt. Met *Skins van spelers laden* kun je alle zeven tegelijk kiezen, zolang de spelersnaam in de bestandsnaam staat. Een skin-PNG download je bijvoorbeeld via NameMC.
2. **Met Node.js** (vanuit deze map):

   ```sh
   npm install
   npm run fetch   # haalt de skins op bij Mojang en zet ze in bases/
   npm run build   # maakt skins/kerst/<speler>/*.png en zet de skins in index.html
   ```

   Je kunt de PNG's ook zelf in `bases/<spelernaam>.png` zetten en daarna `npm run build` draaien.

## Bestanden

- `src/skinforge.js`: de generator (werkt in de browser en in Node)
- `src/page.html`: de websitepagina; `build.js` voegt de generator in en schrijft `index.html`
- `fetch-bases.js`: haalt de huidige skins van de spelers op
- `skins/natuur/`: de 5 bladskins
- `skins/kerst/_voorbeeldbasis/`: de 5 kerstversies van de voorbeeldbasis
- `skins/kerst/<speler>/`: verschijnt na `npm run build` met een basis in `bases/`
