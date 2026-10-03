# SkyFX – Fabric mod voor Minecraft 1.21.11

Geanimeerde custom skies, een neon palmboom-glint, een block aura (klassiek of galaxy) en een item aura, alles in één menu (toets **K**).

Open **`SkyFX-preview.html`** in je browser voor een live preview van alles: de vier luchten, de glints, de block aura en hetzelfde menu als in-game. De preview draait exact dezelfde GLSL-shaders als de mod (ze worden er door `preview/build-preview.mjs` in geplakt).

## Wat zit erin

### 4 geanimeerde luchten
Alle luchten zijn 100% procedurele shaders: geen plaatjes, dus scherp op elke resolutie en ze bewegen continu.

| Lucht | Wat beweegt er |
| --- | --- |
| **Noorderlicht** | Groene gordijnen van noorderlicht die golven, krullen en "ademen", met lichtstralen die erdoorheen rimpelen, twinkelende sterren en vallende sterren. Kleur instelbaar: groen, roze, blauw of regenboog. |
| **Galaxy** | Diepe ruimte met scherpe paars-roze-blauwe nevelslierten die langzaam stromen, heldere sterren met glinsterkruisjes, een draaiende spiraalgalaxie, een grote kraterplaneet met gloeiende paarse scheuren, een ijsmaan die eromheen draait (vóór en achter de planeet langs), een gasreus met ringen, een lavaplaneet, een asteroïdengordel en losse rotsblokken die tuimelend voorbij drijven. |
| **Anime Wolken** | Zonnige anime-lucht met grote bolle stapelwolken uit ronde "puffen", cel-shaded (wit, perzik aan de zonkant, blauw onderin), die over de horizon drijven en zachtjes ademen, sliertige cirruswolken, draaiende zonnestralen, zes zwermen vogels die in V-formatie alle kanten op vliegen en grote meeuwen die rondcirkelen en zweven. |
| **Stormzee** | Een zee van stormwolken onder een gigantische kratermaan: torenhoge onweerswolken die kolken, veel bliksem met vertakte schichten, regengordijnen, flarden wolk die voor de maan langs trekken, een draaikolk recht boven je, een sikkelplaneet, en een gedetailleerd piratenschip dat op de wolkenzee deint en rond de horizon vaart: houten planken, een gouden reling en sierstreep, een rij kanonpoorten (een paar verlicht, met kanonlopen), verlichte ramen in het achterkasteel, een lantaarn op een paal, een kraaiennest, ra's en touwladders, gerafelde zeilen met naden en een doodshoofd, twee fokken op de boegspriet, een wapperende zwarte Jolly Roger-vlag en schuim bij de boeg. |

Opties: animatiesnelheid (0–300%), helderheid, noorderlicht-kleur, vanilla wolken verbergen, en "mist past bij de lucht" (verre terrein vloeit over in de horizonkleur).

> Tip: de luchten zijn altijd zichtbaar, ook overdag. Voor de nacht-luchten is `/time set night` het mooist omdat de wereld dan ook donker belicht is.

### Glints
- **Vanilla** – de gewone paarse glint
- **Palmbomen** – vijf neon palmbomen (cyaan, oranje, roze, lime, lila) die over alle betoverde items, boeken en armor schuiven

Glints zijn ingebouwde resource packs die de vanilla glint-shader vervangen. Bij wisselen herlaadt SkyFX de textures automatisch (zodra je op *Klaar* drukt). Meer glints toevoegen: maak een map `src/client/resources/resourcepacks/<naam>/` met een `pack.mcmeta` en `assets/minecraft/shaders/core/glint.fsh`, en zet een regel in `GlintType.java`.

### Block aura
Vervangt de dunne zwarte block-outline door een aura op elk blok waar je naar kijkt, met een platte, scherpe rand (geen gloed). Twee stijlen:
- **Klassiek** – een egale gekleurde rand met een doorschijnende (pulserende) vulling
- **Galaxy** – het blok wordt een doorschijnend raam naar de ruimte (sterren en nevels), met een platte gekleurde rand

Instelbaar: aan/uit, stijl, kleur (hex-code, RGB-sliders of 8 snelkleuren), regenboog-modus, pulse-snelheid van de vulling, rand-dikte en vulling.

### Item aura
Een gloeiende rand (standaard roze) rond het item dat je vasthoudt in first person. Instelbaar: aan/uit, kleur, regenboog-modus, randdikte en gloed.

## Installeren
1. Installeer [Fabric Loader](https://fabricmc.net/use/) voor Minecraft **1.21.11** (Loader 0.17 of nieuwer).
2. Zet [Fabric API](https://modrinth.com/mod/fabric-api) (0.141.6+1.21.11 of nieuwer) in je `mods` map.
3. Zet `skyfx-1.0.0.jar` in je `mods` map.
4. Start het spel en druk in een wereld op **K**.

**Jar downloaden:** elke push bouwt de mod automatisch via GitHub Actions (workflow *SkyFX mod build*). Open de laatste run onder het tabblad *Actions* en download het artifact **skyfx-mod-jar**. Het artifact **skyfx-screenshots** bevat screenshots die de CI-test in echte Minecraft heeft gemaakt.

Instellingen worden opgeslagen in `config/skyfx.json`. De toets kun je wijzigen bij *Opties → Besturing → SkyFX*.

## Zelf bouwen
Gradle draait op JDK 25 (Fabric Loom 1.18); de mod zelf is Java 21.
```
cd skyfx-mod
./gradlew build                 # -> build/libs/skyfx-1.0.0.jar
./gradlew runClient             # start Minecraft met de mod
./gradlew runClientGameTest     # start Minecraft, test alles en maakt screenshots
node preview/build-preview.mjs  # bouwt SkyFX-preview.html opnieuw na shader-wijzigingen
```

## Hoe het werkt
- **Luchten:** een mixin op `SkyRenderer.renderSkyDisc` tekent een kubus rond de camera met een eigen `RenderPipeline`; de fragment-shader (`assets/skyfx/shaders/core/sky_*.fsh`) rekent per pixel de lucht uit. Tijd, helderheid en palet gaan via het standaard `DynamicTransforms` uniform-block naar de shader. Zon, maan, sterren en zonsopgang van vanilla worden overgeslagen; vanilla wolken optioneel ook. Mocht een shader niet compileren op een GPU, dan valt SkyFX automatisch terug op de vanilla lucht.
- **Mist:** een mixin op `FogRenderer.computeFogColor` geeft de mist de horizonkleur van de gekozen lucht (niet onder water/lava of met blindness).
- **Glint:** ingebouwd resource pack `skyfx:palm_glint` met een eigen glint-textuur en `core/glint.vsh`/`glint.fsh` (textuur 3x kleiner zodat hele palmbomen op een item passen, kleuren exact).
- **Item aura:** een mixin op `GameRenderer.renderItemInHand` tekent de hand één keer extra naar een eigen masker-textuur; een fullscreen-shader tekent daar de rand en gloed omheen, waarna de hand normaal wordt getekend.
- **Block aura:** Fabric's `WorldRenderEvents.BEFORE_BLOCK_OUTLINE`: een doorschijnend gevuld blok (of de galaxy-shader) en één platte, effen lijn langs de randen.
