/* ============================================================================
 * LEAKESTAN — CONFIGURATIE
 * ----------------------------------------------------------------------------
 * Dit is het ENIGE bestand dat je hoeft aan te passen om de site te vullen.
 *
 *  1. DISCORD_INVITE -> zet hier je echte Discord-invite in.
 *  2. CATEGORIES     -> het menu links. "home" toont alles.
 *  3. ITEMS          -> per item: naam, categorie, afbeelding, downloadlink.
 *
 * De downloadknop:
 *  download: ""  -> knop is LEEG. Er wordt niets echts gedownload.
 *
 * Er worden bewust GEEN .jar- of .zip-bestanden meegeleverd of gehost.
 *
 * Categorieen zonder items (Tools, Ratters, Scammers) tonen vanzelf een
 * "nog leeg"-melding. Je hoeft daar niets voor te doen.
 * ==========================================================================*/

window.LEAKESTAN = {
  /* Plak hier je Discord-invite, bijvoorbeeld "https://discord.gg/abc123".
     Zolang dit leeg is toont de knop netjes "nog niet ingesteld". */
  DISCORD_INVITE: "",

  /* Bestand dat "gedownload" wordt: een leeg tekstbestand, geen archief. */
  BLANK_DOWNLOAD: "assets/blank.txt",

  /* Het menu in de zijbalk. "home" is bijzonder: die toont alle items. */
  CATEGORIES: [
    { key: "home",     label: "Home",     icon: "home" },
    { key: "clients",  label: "Clients",  icon: "file" },
    { key: "tools",    label: "Tools",    icon: "tool" },
    { key: "ratters",  label: "Ratters",  icon: "bug" },
    { key: "scammers", label: "Scammers", icon: "warn" },
  ],

  /* ---------------------------------------------------------------------
   * Een item heeft maar vier dingen nodig: naam, categorie, afbeelding en
   * (later) een link. `added` bepaalt alleen de volgorde bij "Newest first".
   *
   * Nieuw item toevoegen: zet je afbeelding in assets/previews/ en kopieer
   * een blok hieronder. Let op dat `id` uniek blijft.
   * ------------------------------------------------------------------- */
  ITEMS: [
    {
      id: "base-debug",
      name: "Base Debug",
      category: "clients",
      image: "assets/previews/base-debug.webp",
      download: "",
      added: "2026-09-22",
    },
    {
      id: "water-client-dev-prerelease",
      name: "Water Client Dev Version Pre Release",
      category: "clients",
      image: "assets/previews/water-client-dev-prerelease.webp",
      download: "",
      added: "2026-09-21",
    },
    {
      id: "swyzzy-client",
      name: "Swyzzy Client",
      category: "clients",
      image: "assets/previews/swyzzy-client.webp",
      download: "",
      added: "2026-09-20",
    },
    {
      id: "larp-debug-v8",
      name: "Larp Debug V8",
      category: "clients",
      image: "assets/previews/larp-debug-v8.png",
      download: "",
      added: "2026-09-19",
    },
    {
      id: "krypton-avengers-addon",
      name: "Krypton Avengers Addon",
      category: "clients",
      image: "assets/previews/krypton-avengers-addon.png",
      download: "",
      added: "2026-09-18",
    },
  ],
};
