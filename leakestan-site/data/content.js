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
   * LET OP: de afbeeldingen hieronder zijn eigen placeholders, niet de
   * screenshots van de originele site. Vervang `image` door je eigen
   * bestand zodra je het hebt.
   * ------------------------------------------------------------------- */
  ITEMS: [
    {
      id: "nova-addon",
      name: "Nova Addon",
      category: "clients",
      image: "assets/previews/nova-addon.svg",
      download: "",
      added: "2026-09-18",
    },
    {
      id: "lemon-debug",
      name: "Lemon Debug",
      category: "clients",
      image: "assets/previews/lemon-debug.svg",
      download: "",
      added: "2026-09-16",
    },
    {
      id: "larp-debug-v8",
      name: "Larp Debug V8",
      category: "clients",
      image: "assets/previews/larp-debug-v8.svg",
      download: "",
      added: "2026-09-14",
    },
  ],
};
