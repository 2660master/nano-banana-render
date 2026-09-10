# -*- coding: utf-8 -*-
"""Bouwt het geluidsgedeelte van de keuringspagina.

De pagina krijgt WAV op 22050 Hz mee in plaats van de OGG uit het pack:
OGG Vorbis speelt niet in elke browser, WAV overal. Het pack zelf houdt
gewoon OGG, want dat is wat Minecraft accepteert.
"""
import base64
import html
import io

import numpy as np
import soundfile as sf

import sound_catalog
import sound_events

PREVIEW_SR = 22050

GROUPS = [
    ("Gevecht &amp; totem",
     "Hout op hout met een wolk ritselend blad. De totem is het langst: lage bonk, opbloeiend akkoord, en vogels die opvliegen.",
     ["verdant/combat/hit1", "verdant/combat/hit2", "verdant/combat/hit3",
      "verdant/combat/crit1", "verdant/combat/crit2", "verdant/combat/sweep",
      "verdant/combat/knockback", "verdant/combat/weak1", "verdant/combat/weak2",
      "verdant/combat/hurt1", "verdant/combat/hurt2", "verdant/combat/hurt3",
      "verdant/magic/totem", "verdant/magic/levelup",
      "verdant/magic/orb1", "verdant/magic/orb2",
      "verdant/magic/pop1", "verdant/magic/pop2"]),
    ("Voetstappen",
     "Dit hoor je vaker dan wat ook, dus ze zijn kort en zacht gehouden. Vier varianten per ondergrond, zodat lopen niet gaat ratelen.",
     [f"verdant/step/{m}{i}" for m in ("grass", "stone", "wood", "sand", "gravel", "wool", "snow")
      for i in range(1, 5)]),
    ("Breken &amp; plaatsen",
     "Dezelfde klankwereld als de voetstappen, maar langer en met meer lichaam.",
     [f"verdant/dig/{m}{i}" for m in ("grass", "stone", "wood", "sand") for i in range(1, 4)]),
    ("Weer &amp; omgeving",
     "Regen loopt rond zonder hoorbare naad. De grotklank is een lage bromtoon met een druppel in de verte.",
     ["verdant/ambient/rain", "verdant/ambient/thunder1", "verdant/ambient/thunder2",
      "verdant/ambient/cave1", "verdant/ambient/cave2", "verdant/ambient/cave3",
      "verdant/ambient/water"]),
    ("Deuren, kisten &amp; water",
     "Scharnieren zijn een stijgende toon met beving, plus een houten rand.",
     ["verdant/misc/door_open", "verdant/misc/door_close",
      "verdant/misc/chest_open", "verdant/misc/chest_close",
      "verdant/misc/splash", "verdant/misc/swim1", "verdant/misc/swim2",
      "verdant/misc/swim3"]),
]


def events_for(path):
    """Welke Minecraft-gebeurtenissen dit bestand aansturen."""
    return [ev for ev, (_c, files, _s, _v) in sound_events.EVENTS.items() if path in files]


def wav_uri(samples):
    down = samples[:: max(1, round(44100 / PREVIEW_SR))]
    buf = io.BytesIO()
    sf.write(buf, down, PREVIEW_SR, format="WAV", subtype="PCM_16")
    return "data:audio/wav;base64," + base64.b64encode(buf.getvalue()).decode()


def wave_svg(samples, w=132, h=26, buckets=60):
    """Kleine golfvorm zodat de lijst te scannen is."""
    a = np.abs(samples)
    step = max(1, a.size // buckets)
    peaks = np.array([a[i:i + step].max() for i in range(0, a.size, step)][:buckets])
    if peaks.max() > 0:
        peaks = peaks / peaks.max()
    dx = w / max(1, peaks.size - 1)
    top = " ".join(f"{i * dx:.1f},{h / 2 - p * (h / 2 - 1):.1f}" for i, p in enumerate(peaks))
    bot = " ".join(f"{i * dx:.1f},{h / 2 + p * (h / 2 - 1):.1f}"
                   for i, p in reversed(list(enumerate(peaks))))
    return (f'<svg class="wave" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'aria-hidden="true"><polygon points="{top} {bot}" fill="currentColor"/></svg>')


def row(path, samples):
    dur = samples.size / 44100
    evs = events_for(path)
    ev_txt = evs[0] if len(evs) == 1 else f"{evs[0]} +{len(evs) - 1}"
    short = path.rsplit("/", 1)[-1]
    return (
        f'<div class="srow tile" data-name="{html.escape(path)}">'
        f'<button type="button" class="play" data-src="{wav_uri(samples)}" '
        f'aria-label="speel {html.escape(short)}"><span class="tri"></span></button>'
        f'<div class="sname"><b>{html.escape(short)}</b>'
        f'<code>{html.escape(ev_txt)}</code></div>'
        f'{wave_svg(samples)}'
        f'<span class="dur">{dur:.2f}s</span>'
        f'<div class="verdict" role="group" aria-label="oordeel {html.escape(short)}">'
        f'<button type="button" class="v v-ok" data-v="ok">goed</button>'
        f'<button type="button" class="v v-fix" data-v="fix">anders</button></div>'
        f'<input class="note" id="note-{html.escape(path)}" type="text" hidden '
        f'placeholder="wat moet er anders?" autocomplete="off"></div>'
    )


def build():
    cat = sound_catalog.catalog()
    rendered = {k: v() for k, v in cat.items()}
    parts, count = [], 0
    for title, blurb, paths in GROUPS:
        paths = [p for p in paths if p in rendered]
        count += len(paths)
        rows = "".join(row(p, rendered[p]) for p in paths)
        parts.append(f'<section class="grp"><h3>{title}</h3>'
                     f'<p class="blurb">{blurb}</p><div class="slist">{rows}</div></section>')
    return "".join(parts), count
