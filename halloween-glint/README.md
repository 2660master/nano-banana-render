# Halloween Glint — oranje pompoen-glint

Losse resourcepack met **alleen** de betovering-glint: de schittering over verhekste items en
harnassen wordt een veld van kleine gloeiende jack-o'-lanterns. Verder verandert er niets.
`pack_format: 75` (= Minecraft 1.21.11). Geen mods nodig.

Deze pack staat los van *Halloween Sky*, zodat je ze onafhankelijk aan en uit kunt zetten. Wil je
beide, zet ze dan gewoon allebei aan — ze raken elkaars bestanden niet.

## Installeren

Map naar `.minecraft/resourcepacks/` kopiëren, of zippen — `pack.mcmeta` moet dan in de wortel
van de zip staan, niet in een extra submap. Daarna aanzetten in *Options → Resource Packs*.

## De twee vellen

| Bestand | Formaat | Waarom |
|---|---|---|
| `assets/minecraft/textures/misc/enchanted_glint_item.png` | 512×512 | losjes gestrooid veld kleine lantaarns |
| `assets/minecraft/textures/misc/enchanted_glint_armor.png` | 1024×1024 | dicht veld nog kleinere lantaarns |

Waarom twee verschillende ontwerpen: Minecraft schuift de glint over het model met een
texture-matrix, en de schaal daarvan verschilt per rendertype.

* **Items** gebruiken schaal `8.0`: de textuur wordt 8× herhaald over een sprite van 16 px, dus één
  tegel is ~2 item-pixels breed. Individuele pompoenen zijn daar fysiek niet te zien — je ziet een
  oranje schittering die over je zwaard schuift. Om die schittering tóch te laten leven ligt er een
  laagfrequente helderheidsdrift over het veld: sommige lantaarns branden feller dan andere, en dat
  contrast overleeft het uitmiddelen wel.
* **Gedragen harnas** gebruikt schaal `0.16`: over een borststuk zie je maar ~2 % van de textuur,
  enorm uitvergroot. Daar staan daarom véél kleinere pompoenen op (~1,7 % van de breedte), die als
  grote gloeiende koppen over je harnas trekken.

Elke lantaarn wordt uit vijf gesneden gezichten, ribben, steel met krul en blad, speculaire
highlight en een gloed vanuit de gaten opgebouwd, en krijgt een eigen maat, rotatie en helderheid.
Beide bestanden tegelen naadloos (strepen uit band-gefilterde ruis in het frequentiedomein,
pompoenen met wrap-around gestempeld). De `.png.mcmeta` zet `blur: true`, net als vanilla, zodat
de sterk uitvergrote harnas-glint glad blijft.

De glint mengt additief met `SRC_COLOR, ONE` — de kleur wordt dus effectief gekwadrateerd. Daarom
is zwart in de textuur "onzichtbaar" en is de rest ruim helder gehouden.

Zelf aanpassen: zie `../halloween-generator/README.md`.
