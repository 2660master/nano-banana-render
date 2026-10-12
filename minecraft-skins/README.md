# Kerst & Blad Skins

Minecraft-skins (64×64, Java en Bedrock) met een preview-website:

- **35 kerstskins**: 5 kerstoutfits voor elk van de spelers `spawnerbase`, `2660master`, `stitchcpvp`, `akosdebeste`, `pickzugng`, `johnpork400` en `ITZberryTT_x`.
- **5 bladskins**: bladwezens die geen basis-skin nodig hebben.

Open `index.html` in een browser voor de preview: een 3D-weergave met loop-, ren- en zwaai-animatie, voor- en achterkant per skin, en een downloadknop per skin.

## Hoe de kerstskins op de basis-skin worden gezet

Het hoofd van de speler (gezicht, haar, hoed-laag) blijft behouden. De outfit vervangt romp, armen en benen. De huidskleur van het gezicht wordt gebruikt voor handen en elfenoren. De shirtkleur van de basis bepaalt de kleur van de kersttrui en de jas van de notenkraker, als die kleur uitgesproken genoeg is. Slim-skins (armen van 3 px) worden herkend en blijven slim.

| Outfit | Details |
| --- | --- |
| Kerstman | Fluwelen muts met pompon op de rug, baard en snor, bontkraag en bontzoom, riem met gouden gesp, cadeauzak met zuurstok, laarzen |
| Foute kersttrui | Gebreide trui met kerstboom voor en sneeuwvlok achter, muts met pompon, sjaal met franje, tartan pyjamabroek, rendier-sloffen |
| Kerstelf | Elfenmuts met belletje, puntoren, gekartelde kraag, hulstbroche, zuurstok-kousen in spiraal, krulschoenen |
| Rendier-onesie | Capuchon met gewei en oortjes, rode Rudolph-neus, buikvacht, lint met belletje, staartje, hoefjes |
| Notenkraker | Kolbak met pluim en kinband, huzarenjas met gouden tressen, epauletten, witte handschoenen, glanzende laarzen |

| Bladwezen | Details |
| --- | --- |
| Eikenwachter | Eikenblad, takkenkroon, eikels, amberkleurige ogen |
| Herfstgeest | Rood-oranje-goud blad, vliegenzwammen, vallende blaadjes |
| Bloesemdryade | Kersenbloesem, bloesemkroon, bloesemtak over de rug |
| Azaleahoeder | Azaleablad met magenta bloemen, mosmat op de schouders |
| Junglegeest | Junglegroen blad, hangende lianen met gloeibessen, cyaan ogen |

## De echte skins van de spelers

Toen dit gemaakt werd waren de Minecraft-servers niet bereikbaar, dus de kerstskins staan nog op een neutrale voorbeeldbasis (`skins/kerst/_voorbeeldbasis/`). Er zijn twee manieren om de echte versies te maken:

1. **In de website**: klik bij een speler op *Skin laden* (of sleep de PNG op de rij van die speler). Met *Skins van spelers laden* kun je alle zeven tegelijk kiezen, zolang de spelersnaam in de bestandsnaam staat. Een skin-PNG download je bijvoorbeeld via NameMC.
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
- `skins/kerst/_voorbeeldbasis/`: de 5 kerstoutfits op de voorbeeldbasis
- `skins/kerst/<speler>/`: verschijnt na `npm run build` met een basis in `bases/`
