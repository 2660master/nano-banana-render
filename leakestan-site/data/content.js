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

  /* Hoeveel dagen een item het rode "NEW"-label krijgt, gerekend vanaf
     de datum bij `added`. Zet op 0 om het label uit te zetten. */
  NEW_DAYS: 7,

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
   * (later) een link. `added` bepaalt de volgorde én het "NEW"-label, dus
   * zet bij een nieuwe client de echte datum van vandaag.
   *
   * Optioneel:
   *   tags:  ["MC 1.21.11"]   -> labels rechtsboven op de afbeelding
   *   focus: "50% 40%"        -> welk deel van de afbeelding in beeld blijft
   *                              (links/rechts, boven/onder)
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
      /* De kaart snijdt bij tot 16:9; zo blijft de kop van het menu in beeld. */
      focus: "50% 40%",
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
      tags: ["MC 1.21.11"],
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
    {
      id: "67client",
      name: "67client",
      category: "clients",
      image: "assets/previews/67client.webp",
      tags: ["MC 1.21.11"],
      download: "",
      added: "2026-09-17",
    },
    {
      id: "kryptonclient",
      name: "KryptonClient",
      category: "clients",
      image: "assets/previews/kryptonclient.png",
      download: "",
      added: "2026-09-16",
    },
    {
      id: "4e-client",
      name: "4e Client",
      category: "clients",
      image: "assets/previews/4e-client.png",
      download: "",
      added: "2026-09-15",
    },
    {
      id: "code-engine",
      name: "Code Engine",
      category: "clients",
      image: "assets/previews/code-engine.webp",
      tags: ["MC 1.21.11"],
      download: "",
      added: "2026-09-14",
    },
    {
      id: "gooba-client",
      name: "Gooba Client",
      category: "clients",
      image: "assets/previews/gooba-client.webp",
      download: "",
      added: "2026-09-13",
    },
    {
      id: "prestige-client",
      name: "Prestige Client",
      category: "clients",
      image: "assets/previews/prestige-client.png",
      download: "",
      added: "2026-09-12",
    },
    {
      id: "corz-client",
      name: "Corz Client",
      category: "clients",
      image: "assets/previews/corz-client.png",
      download: "",
      added: "2026-09-11",
    },
    {
      id: "opsec-mod",
      name: "Opsec Mod",
      category: "clients",
      image: "assets/previews/opsec-mod.jpg",
      download: "",
      added: "2026-09-10",
    },
    {
      id: "radium-client",
      name: "Radium Client",
      category: "clients",
      image: "assets/previews/radium-client.jpg",
      download: "",
      added: "2026-09-09",
    },
    {
      id: "volt-client",
      name: "Volt Client",
      category: "clients",
      image: "assets/previews/volt-client.jpg",
      download: "",
      added: "2026-09-08",
    },
    {
      id: "coffee-client",
      name: "Coffee Client",
      category: "clients",
      image: "assets/previews/coffee-client.jpg",
      download: "",
      added: "2026-09-07",
    },
  ],
};
