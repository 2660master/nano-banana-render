/* ============================================================================
 * LEAKESTAN — CONFIGURATIE
 * ----------------------------------------------------------------------------
 * Dit is het ENIGE bestand dat je hoeft aan te passen om de site te vullen.
 *
 *  1. DISCORD_INVITE  -> zet hier je echte Discord-invite in.
 *  2. PACKS           -> per item: naam, categorie, afbeelding en downloadlink.
 *
 * De downloadknop:
 *  download: ""   -> knop is nog LEEG en serveert assets/blank.txt ("blank").
 *  download: "https://.../pack.zip"  -> knop wordt een echte download.
 * ==========================================================================*/

window.LEAKESTAN = {
  /* Plak hier je Discord-invite, bijvoorbeeld "https://discord.gg/abc123".
     Zolang dit leeg is toont de knop netjes "nog niet ingesteld". */
  DISCORD_INVITE: "",

  /* Bestand dat gedownload wordt zolang een pack nog geen echte link heeft. */
  BLANK_DOWNLOAD: "assets/blank.txt",

  PACKS: [
    {
      id: "azure-edge",
      name: "Azure Edge 16x",
      category: "PvP",
      image: "assets/previews/azure-edge.svg",
      download: "",
      resolution: "16x",
      size: "4.2 MB",
      added: "2026-09-18",
      hits: 18420,
      featured: true,
    },
    {
      id: "frostbyte",
      name: "Frostbyte",
      category: "PvP",
      image: "assets/previews/frostbyte.svg",
      download: "",
      resolution: "32x",
      size: "7.8 MB",
      added: "2026-09-16",
      hits: 15310,
      featured: true,
    },
    {
      id: "neon-circuit",
      name: "Neon Circuit",
      category: "UI",
      image: "assets/previews/neon-circuit.svg",
      download: "",
      resolution: "64x",
      size: "12.1 MB",
      added: "2026-09-14",
      hits: 9870,
      featured: false,
    },
    {
      id: "glacier",
      name: "Glacier",
      category: "Bedwars",
      image: "assets/previews/glacier.svg",
      download: "",
      resolution: "16x",
      size: "3.6 MB",
      added: "2026-09-12",
      hits: 22140,
      featured: true,
    },
    {
      id: "cobalt-dream",
      name: "Cobalt Dream",
      category: "Bedwars",
      image: "assets/previews/cobalt-dream.svg",
      download: "",
      resolution: "32x",
      size: "8.4 MB",
      added: "2026-09-09",
      hits: 7420,
      featured: false,
    },
    {
      id: "deep-blue",
      name: "Deep Blue 32x",
      category: "PvP",
      image: "assets/previews/deep-blue.svg",
      download: "",
      resolution: "32x",
      size: "9.0 MB",
      added: "2026-09-06",
      hits: 13080,
      featured: false,
    },
    {
      id: "midnight-drip",
      name: "Midnight Drip",
      category: "Skyblock",
      image: "assets/previews/midnight-drip.svg",
      download: "",
      resolution: "64x",
      size: "16.7 MB",
      added: "2026-09-03",
      hits: 6150,
      featured: false,
    },
    {
      id: "hydro-wave",
      name: "Hydro Wave",
      category: "Practice",
      image: "assets/previews/hydro-wave.svg",
      download: "",
      resolution: "16x",
      size: "2.9 MB",
      added: "2026-08-30",
      hits: 11260,
      featured: false,
    },
    {
      id: "sapphire-ops",
      name: "Sapphire Ops",
      category: "PvP",
      image: "assets/previews/sapphire-ops.svg",
      download: "",
      resolution: "16x",
      size: "5.1 MB",
      added: "2026-08-27",
      hits: 19730,
      featured: true,
    },
    {
      id: "arctic-vanilla",
      name: "Arctic Vanilla",
      category: "Vanilla+",
      image: "assets/previews/arctic-vanilla.svg",
      download: "",
      resolution: "16x",
      size: "3.1 MB",
      added: "2026-08-24",
      hits: 5240,
      featured: false,
    },
    {
      id: "voltage",
      name: "Voltage",
      category: "UI",
      image: "assets/previews/voltage.svg",
      download: "",
      resolution: "32x",
      size: "6.3 MB",
      added: "2026-08-21",
      hits: 8490,
      featured: false,
    },
    {
      id: "blue-nova",
      name: "Blue Nova 8x",
      category: "Practice",
      image: "assets/previews/blue-nova.svg",
      download: "",
      resolution: "8x",
      size: "1.8 MB",
      added: "2026-08-18",
      hits: 14670,
      featured: false,
    },
  ],
};
