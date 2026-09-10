# -*- coding: utf-8 -*-
"""Bouwt de keuringspagina (HTML-artifact) met alle texturen ingebed."""
import base64
import html
import os

import build as B
import palette
import preview_blocks
import sound_preview
import sprites_blocks
import sprites_tools

OUT = "/tmp/claude-0/-home-user-nano-banana-render/673b7979-40bd-557d-ae11-258818c67e59/scratchpad/verdant-review.html"

TIER_NL = {
    "wooden": "hout", "stone": "steen", "iron": "ijzer",
    "golden": "goud", "diamond": "diamant", "netherite": "netherite",
}
TOOL_NL = {
    "sword": "zwaard", "pickaxe": "houweel", "axe": "bijl",
    "shovel": "schep", "hoe": "schoffel",
}

GROUPS = [
    ("Voedsel & oogst", "Wat je eet en oogst — hier telt of de kleur eetbaar oogt.",
     ["apple", "golden_apple", "bread", "carrot", "wheat", "wheat_seeds", "honeycomb"]),
    ("Grondstoffen", "Losse buit uit de wereld.",
     ["stick", "coal", "charcoal", "flint", "clay_ball", "leather", "string",
      "feather", "bone", "slime_ball", "ender_pearl"]),
    ("Staven", "Zelfde vorm, per materiaal een ander natuurpalet.",
     ["iron_ingot", "gold_ingot", "copper_ingot", "netherite_ingot"]),
    ("Kristallen & stof", "De felle kleuren — deze moeten opvallen zonder te schreeuwen.",
     ["diamond", "emerald", "amethyst_shard", "lapis_lazuli", "redstone"]),
    ("Uitrusting", "De boog heeft drie spanframes, anders springt hij terug naar vanilla.",
     ["bow", "bow_pulling_0", "bow_pulling_1", "bow_pulling_2", "arrow",
      "bucket", "water_bucket", "totem_of_undying"]),
]


def data_uri(name, folder=None):
    with open(os.path.join(folder or B.ITEM_DIR, name + ".png"), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def block_tile(name):
    """Blok-tegel: CSS herhaalt de 16x16 texture 2x2, zodat naden opvallen."""
    uri = data_uri(name, B.BLOCK_DIR)
    return (
        f'<figure class="tile btile" data-name="{html.escape(name)}">'
        f'<div class="bslot" style="background-image:url({uri})"></div>'
        f'<code>{html.escape(name)}.png</code>'
        f'<div class="verdict" role="group" aria-label="oordeel {html.escape(name)}">'
        f'<button type="button" class="v v-ok" data-v="ok">goed</button>'
        f'<button type="button" class="v v-fix" data-v="fix">anders</button>'
        f'</div>'
        f'<input class="note" id="note-{html.escape(name)}" type="text" hidden '
        f'placeholder="wat moet er anders?" autocomplete="off">'
        f'</figure>'
    )


# (naam, map, weergavebreedte px, herhaling, bijschrift)
SKY_STATIC = [
    ("sun", "env", 128, 1, "Warme amberkern met een zachte krans."),
    ("moon_phases", "env", 256, 1, "Alle acht schijngestalten in het raster van 4 x 2 dat het spel uitleest."),
    ("clouds", "env", 256, 1, "Wit is wolk, doorzichtig is lucht. 34% dekking — ongeveer vanilla."),
    ("end_sky", "env", 128, 8, "Diepgroen-zwart met sporen die licht vangen."),
    ("rain", "env", 128, 1, "Dunne strepen met een groenblauwe zweem."),
    ("snow", "env", 128, 1, "Zachte vlokken met een halo."),
]

# (naam, framebreedte, aantal frames, frametime in ticks, bijschrift)
SKY_ANIMATED = [
    ("water_still", 16, 32, 2, "Stilstaand water. Het spel kleurt dit met de biome-kleur, dus het staat hier bleek."),
    ("water_flow", 32, 32, 1, "Stromend water, met verticale strengen die meelopen."),
    ("lava_still", 16, 20, 2, "Donkere korst die opengaat en weer dichttrekt."),
    ("lava_flow", 32, 20, 3, "Lava die omlaag kruipt."),
]


def sky_tile(name, folder, width, repeat, caption):
    uri = data_uri(name, B.ENV_DIR if folder == "env" else B.BLOCK_DIR)
    style = f"width:{width}px;background-image:url({uri})"
    style += f";background-size:{width // repeat}px auto" if repeat > 1 else ";background-size:100% auto"
    im_h = {"sun": width, "moon_phases": width // 2, "clouds": width,
            "end_sky": width, "rain": width, "snow": width}[name]
    style += f";height:{im_h}px"
    return (
        f'<figure class="tile stile" data-name="{html.escape(name)}">'
        f'<div class="sslot" style="{style}"></div>'
        f'<code>{html.escape(name)}.png</code>'
        f'<p class="cap">{caption}</p>'
        f'<div class="verdict" role="group" aria-label="oordeel {html.escape(name)}">'
        f'<button type="button" class="v v-ok" data-v="ok">goed</button>'
        f'<button type="button" class="v v-fix" data-v="fix">anders</button></div>'
        f'<input class="note" id="note-{html.escape(name)}" type="text" hidden '
        f'placeholder="wat moet er anders?" autocomplete="off"></figure>'
    )


def anim_tile(name, fw, frames, frametime, caption):
    """Speelt de sprite-strip af met precies de snelheid die het spel gebruikt."""
    uri = data_uri(name, B.BLOCK_DIR)
    disp = 128
    dur = round(frames * frametime * 0.05, 2)      # 1 tick = 1/20 seconde
    style = (f"width:{disp}px;height:{disp}px;background-image:url({uri});"
             f"background-size:{disp}px auto;"
             f"animation-duration:{dur}s;--frames:{frames};"
             f"--strip:-{disp * frames}px")
    return (
        f'<figure class="tile stile" data-name="{html.escape(name)}">'
        f'<div class="aslot" style="{style}"></div>'
        f'<code>{html.escape(name)}.png</code>'
        f'<p class="cap">{caption} <b>{frames} frames</b>, {dur}s per ronde.</p>'
        f'<div class="verdict" role="group" aria-label="oordeel {html.escape(name)}">'
        f'<button type="button" class="v v-ok" data-v="ok">goed</button>'
        f'<button type="button" class="v v-fix" data-v="fix">anders</button></div>'
        f'<input class="note" id="note-{html.escape(name)}" type="text" hidden '
        f'placeholder="wat moet er anders?" autocomplete="off"></figure>'
    )


BLOCK_BLURBS = {
    "Planken": "Vier lange gangen met doorlopende nerf. Trappen, treden, hekken en deurpanelen erven deze texture automatisch.",
    "Stammen & stengels": "Bast aan de zijkant, jaarringen aan de kop. Berk heeft zijn zwarte streepjes gehouden.",
    "Steen": "Van bemoste kei tot gepolijste deepslate. Het mos zit in plukken, niet als losse stippen.",
    "Metselwerk": "Halfsteensverband met voegen die net iets lichter zijn dan de steen zelf.",
    "Wol": "Plantaardig geverfd: zachter en grijzer dan vanilla. Tapijt gebruikt dezelfde texture.",
    "Beton": "Vlak gehouden — beton hoort strak te zijn naast al dat gevlekte steen.",
    "Betonpoeder": "Korreliger en iets lichter, zodat je poeder en blok uit elkaar houdt.",
    "Terracotta": "Horizontale sliblagen, zoals in gebakken klei.",
    "Glas": "Doorlopende rand per blok en twee lichtvegen. Getint glas is bewust bijna dicht.",
    "Aarde & ondergrond": "Aarde, gras, zand, ijs en de nether-bodems. De graskraag zit op de zijkant, precies zoals vanilla het opbouwt.",
    "Bladeren": "Let op: eik, spar, berk, jungle, acacia, donkere eik en mangrove zien er hier bleek uit. Dat hoort zo — het spél kleurt ze in met de biome-kleur, dus een groene texture zou in-game veel te donker worden. Kers, azalea en pale oak hebben wél een vaste kleur; die zie je hier zoals ze in het spel worden.",
    "Ertsen": "De klodders hebben exact de kleuren van de items uit deel 1: amber voor goud, dauwkristal voor diamant, berksteen voor ijzer. Zo hoort erts bij wat je eruit haalt.",
    "Planten": "Ook deze worden door het spel ingekleurd, dus ze staan bewust bleek. In het spel krijgen ze de kleur van de biome waar ze groeien.",
    "Bloemen": "Vaste kleuren, deze worden niet ingekleurd. Elke bloem staat op dezelfde steel met hetzelfde blaadje.",
    "Gewassen": "Alle groeistadia. De stengels groeien mee en krijgen pas laat hun aar of vrucht, zodat je van een afstand ziet of iets oogstbaar is.",
}


def tile(name, caption=None):
    return (
        f'<figure class="tile" data-name="{html.escape(name)}">'
        f'<div class="slot"><img src="{data_uri(name)}" alt="{html.escape(name)}" '
        f'width="16" height="16"></div>'
        f'<figcaption>{html.escape(caption or name)}</figcaption>'
        f'<code>{html.escape(name)}.png</code>'
        f'<div class="verdict" role="group" aria-label="oordeel {html.escape(name)}">'
        f'<button type="button" class="v v-ok" data-v="ok">goed</button>'
        f'<button type="button" class="v v-fix" data-v="fix">anders</button>'
        f'</div>'
        f'<input class="note" id="note-{html.escape(name)}" type="text" hidden '
        f'placeholder="wat moet er anders?" autocomplete="off">'
        f'</figure>'
    )


def build_html():
    tools = list(sprites_tools.TOOLS.keys())

    # --- gereedschapsmatrix: rijen = tier, kolommen = stuk gereedschap
    matrix = ['<div class="matrix" role="table" aria-label="Gereedschap per materiaal">']
    matrix.append('<div class="mrow mhead" role="row"><div class="mtier" role="columnheader"></div>')
    for t in tools:
        matrix.append(f'<div class="mcell mlabel" role="columnheader">{TOOL_NL[t]}</div>')
    matrix.append("</div>")
    for mat in palette.TIER_ORDER:
        m = palette.MATERIALS[mat]
        swatch = "#%02X%02X%02X" % m["M"][:3]
        matrix.append('<div class="mrow" role="row">')
        matrix.append(
            f'<div class="mtier" role="rowheader">'
            f'<span class="chip" style="--sw:{swatch}"></span>'
            f'<b>{m["label"]}</b><span>{TIER_NL[mat]}</span></div>')
        for t in tools:
            matrix.append(f'<div class="mcell" role="cell">{tile(f"{mat}_{t}", TOOL_NL[t])}</div>')
        matrix.append("</div>")
    matrix.append("</div>")

    groups = []
    for title, blurb, names in GROUPS:
        cards = "".join(tile(n) for n in names)
        groups.append(
            f'<section class="grp"><h3>{title}</h3><p class="blurb">{blurb}</p>'
            f'<div class="grid">{cards}</div></section>')

    cat = sprites_blocks.catalog()
    bsections = []
    n_blocks = 0
    for title, names in preview_blocks.groups():
        names = [n for n in names if n in cat]
        n_blocks += len(names)
        cards = "".join(block_tile(n) for n in names)
        blurb = BLOCK_BLURBS.get(title, "")
        bsections.append(
            f'<section class="grp"><h3>{title}</h3><p class="blurb">{blurb}</p>'
            f'<div class="bgrid">{cards}</div></section>')

    sound_html, n_sounds = sound_preview.build()
    sky_html = ("".join(sky_tile(*t) for t in SKY_STATIC)
                + "".join(anim_tile(*t) for t in SKY_ANIMATED))
    n_sky = len(SKY_STATIC) + len(SKY_ANIMATED)

    total = (len(palette.TIER_ORDER) * len(tools) + sum(len(g[2]) for g in GROUPS)
             + n_blocks + n_sky + n_sounds)

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_template.html"),
              encoding="utf-8") as f:
        tpl = f.read()

    return (tpl
            .replace("@@MATRIX@@", "".join(matrix))
            .replace("@@GROUPS@@", "".join(groups))
            .replace("@@BLOCKS@@", "".join(bsections))
            .replace("@@NBLOCKS@@", str(n_blocks))
            .replace("@@SKY@@", sky_html)
            .replace("@@SOUNDS@@", sound_html)
            .replace("@@NSOUNDS@@", str(n_sounds))
            .replace("@@TOTAL@@", str(total)))


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build_html())
    print("geschreven:", OUT, os.path.getsize(OUT), "bytes")
