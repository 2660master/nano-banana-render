/* ============================================================================
 * LEAKESTAN — CONFIGURATIE
 * ----------------------------------------------------------------------------
 * Dit is het ENIGE bestand dat je hoeft aan te passen om de site te vullen.
 *
 *  1. DISCORD_INVITE -> zet hier je echte Discord-invite in.
 *  2. CATEGORIES     -> het menu links. "home" toont alles.
 *  3. ITEMS          -> per item: naam, categorie, afbeelding en downloadlink.
 *
 * De downloadknop:
 *  download: ""  -> knop is nog LEEG, er wordt niets echts gedownload.
 *  download: "https://.../client.zip"  -> knop wordt een echte download.
 *
 * Categorieen zonder items (Tools, Ratters, Scammers) tonen vanzelf een
 * "nog leeg"-melding. Je hoeft daar niets voor te doen.
 * ==========================================================================*/

window.LEAKESTAN = {
  /* Plak hier je Discord-invite, bijvoorbeeld "https://discord.gg/abc123".
     Zolang dit leeg is toont de knop netjes "nog niet ingesteld". */
  DISCORD_INVITE: "",

  /* Bestand dat gedownload wordt zolang een item nog geen echte link heeft. */
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
   * PLACEHOLDERS. De namen en afbeeldingen hieronder zijn opvulling —
   * vervang ze door de echte clients (naam + afbeelding + link).
   * ------------------------------------------------------------------- */
  ITEMS: [
    {
      id: "client-01",
      name: "Client 01",
      category: "clients",
      image: "assets/previews/client-01.svg",
      download: "",
      version: "v1.0",
      added: "2026-09-18",
      hits: 18420,
      featured: true,
    },
    {
      id: "client-02",
      name: "Client 02",
      category: "clients",
      image: "assets/previews/client-02.svg",
      download: "",
      version: "v1.0",
      added: "2026-09-16",
      hits: 15310,
      featured: true,
    },
    {
      id: "client-03",
      name: "Client 03",
      category: "clients",
      image: "assets/previews/client-03.svg",
      download: "",
      version: "v1.0",
      added: "2026-09-14",
      hits: 9870,
      featured: false,
    },
    {
      id: "client-04",
      name: "Client 04",
      category: "clients",
      image: "assets/previews/client-04.svg",
      download: "",
      version: "v1.0",
      added: "2026-09-12",
      hits: 22140,
      featured: true,
    },
    {
      id: "client-05",
      name: "Client 05",
      category: "clients",
      image: "assets/previews/client-05.svg",
      download: "",
      version: "v1.0",
      added: "2026-09-09",
      hits: 7420,
      featured: false,
    },
    {
      id: "client-06",
      name: "Client 06",
      category: "clients",
      image: "assets/previews/client-06.svg",
      download: "",
      version: "v1.0",
      added: "2026-09-06",
      hits: 13080,
      featured: false,
    },
    {
      id: "client-07",
      name: "Client 07",
      category: "clients",
      image: "assets/previews/client-07.svg",
      download: "",
      version: "v1.0",
      added: "2026-09-03",
      hits: 6150,
      featured: false,
    },
    {
      id: "client-08",
      name: "Client 08",
      category: "clients",
      image: "assets/previews/client-08.svg",
      download: "",
      version: "v1.0",
      added: "2026-08-30",
      hits: 11260,
      featured: false,
    },
    {
      id: "client-09",
      name: "Client 09",
      category: "clients",
      image: "assets/previews/client-09.svg",
      download: "",
      version: "v1.0",
      added: "2026-08-27",
      hits: 19730,
      featured: true,
    },
    {
      id: "client-10",
      name: "Client 10",
      category: "clients",
      image: "assets/previews/client-10.svg",
      download: "",
      version: "v1.0",
      added: "2026-08-24",
      hits: 5240,
      featured: false,
    },
    {
      id: "client-11",
      name: "Client 11",
      category: "clients",
      image: "assets/previews/client-11.svg",
      download: "",
      version: "v1.0",
      added: "2026-08-21",
      hits: 8490,
      featured: false,
    },
    {
      id: "client-12",
      name: "Client 12",
      category: "clients",
      image: "assets/previews/client-12.svg",
      download: "",
      version: "v1.0",
      added: "2026-08-18",
      hits: 14670,
      featured: false,
    },
  ],
};
