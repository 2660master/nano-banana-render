# -*- coding: utf-8 -*-
"""Koppelt Minecraft-gebeurtenissen aan de gesynthetiseerde bestanden.

"replace": true zorgt dat de vanilla-varianten er niet doorheen blijven
spelen. De subtitle-sleutels zijn de vanilla-sleutels, zodat ondertiteling
blijft werken voor wie die aan heeft staan.
"""

C = "verdant/combat/"
M = "verdant/magic/"
S = "verdant/step/"
D = "verdant/dig/"
A = "verdant/ambient/"
X = "verdant/misc/"

HIT = [C + "hit1", C + "hit2", C + "hit3"]
HURT = [C + "hurt1", C + "hurt2", C + "hurt3"]
CRIT = [C + "crit1", C + "crit2"]
WEAK = [C + "weak1", C + "weak2"]
SWIM = [X + "swim1", X + "swim2", X + "swim3"]


def steps(mat):
    return [f"{S}{mat}{i}" for i in range(1, 5)]


def digs(mat):
    return [f"{D}{mat}{i}" for i in range(1, 4)]


# gebeurtenis: (categorie, bestanden, ondertitel, volume)
EVENTS = {
    # -- gevecht en totem
    "entity.player.attack.strong":    ("player", HIT, "subtitles.entity.player.attack.strong", 1.0),
    "entity.player.attack.crit":      ("player", CRIT, "subtitles.entity.player.attack.crit", 1.0),
    "entity.player.attack.sweep":     ("player", [C + "sweep"], "subtitles.entity.player.attack.sweep", 1.0),
    "entity.player.attack.knockback": ("player", [C + "knockback"], "subtitles.entity.player.attack.knockback", 1.0),
    "entity.player.attack.weak":      ("player", WEAK, "subtitles.entity.player.attack.weak", 1.0),
    "entity.player.attack.nodamage":  ("player", WEAK, "subtitles.entity.player.attack.nodamage", 0.8),
    "entity.player.hurt":             ("player", HURT, "subtitles.entity.player.hurt", 1.0),
    "entity.player.levelup":          ("player", [M + "levelup"], "subtitles.entity.player.levelup", 0.9),
    "entity.experience_orb.pickup":   ("player", [M + "orb1", M + "orb2"], "subtitles.entity.experience_orb.pickup", 0.5),
    "entity.item.pickup":             ("player", [M + "pop1", M + "pop2"], "subtitles.entity.item.pickup", 0.5),
    "item.totem.use":                 ("player", [M + "totem"], "subtitles.item.totem.use", 1.0),

    # -- voetstappen, breken en plaatsen
    "block.grass.step":   ("block", steps("grass"), "subtitles.block.generic.footsteps", 1.0),
    "block.grass.break":  ("block", digs("grass"), "subtitles.block.generic.break", 1.0),
    "block.grass.place":  ("block", digs("grass"), "subtitles.block.generic.place", 1.0),
    "block.grass.hit":    ("block", steps("grass"), "subtitles.block.generic.hit", 0.6),
    "block.grass.fall":   ("block", steps("grass"), None, 0.8),
    "block.stone.step":   ("block", steps("stone"), "subtitles.block.generic.footsteps", 1.0),
    "block.stone.break":  ("block", digs("stone"), "subtitles.block.generic.break", 1.0),
    "block.stone.place":  ("block", digs("stone"), "subtitles.block.generic.place", 1.0),
    "block.stone.hit":    ("block", steps("stone"), "subtitles.block.generic.hit", 0.6),
    "block.stone.fall":   ("block", steps("stone"), None, 0.8),
    "block.wood.step":    ("block", steps("wood"), "subtitles.block.generic.footsteps", 1.0),
    "block.wood.break":   ("block", digs("wood"), "subtitles.block.generic.break", 1.0),
    "block.wood.place":   ("block", digs("wood"), "subtitles.block.generic.place", 1.0),
    "block.wood.hit":     ("block", steps("wood"), "subtitles.block.generic.hit", 0.6),
    "block.wood.fall":    ("block", steps("wood"), None, 0.8),
    "block.sand.step":    ("block", steps("sand"), "subtitles.block.generic.footsteps", 1.0),
    "block.sand.break":   ("block", digs("sand"), "subtitles.block.generic.break", 1.0),
    "block.sand.place":   ("block", digs("sand"), "subtitles.block.generic.place", 1.0),
    "block.sand.hit":     ("block", steps("sand"), "subtitles.block.generic.hit", 0.6),
    "block.sand.fall":    ("block", steps("sand"), None, 0.8),
    "block.gravel.step":  ("block", steps("gravel"), "subtitles.block.generic.footsteps", 1.0),
    "block.gravel.break": ("block", steps("gravel"), "subtitles.block.generic.break", 1.0),
    "block.gravel.place": ("block", steps("gravel"), "subtitles.block.generic.place", 1.0),
    "block.wool.step":    ("block", steps("wool"), "subtitles.block.generic.footsteps", 1.0),
    "block.wool.break":   ("block", steps("wool"), "subtitles.block.generic.break", 1.0),
    "block.wool.place":   ("block", steps("wool"), "subtitles.block.generic.place", 1.0),
    "block.snow.step":    ("block", steps("snow"), "subtitles.block.generic.footsteps", 1.0),
    "block.snow.break":   ("block", steps("snow"), "subtitles.block.generic.break", 1.0),
    "block.snow.place":   ("block", steps("snow"), "subtitles.block.generic.place", 1.0),

    # -- weer, grot en water
    "weather.rain":                 ("weather", [A + "rain"], None, 1.0),
    "weather.rain.above":           ("weather", [A + "rain"], None, 1.0),
    "entity.lightning_bolt.thunder": ("weather", [A + "thunder1", A + "thunder2"],
                                      "subtitles.entity.lightning_bolt.thunder", 1.0),
    "ambient.cave":                 ("ambient", [A + "cave1", A + "cave2", A + "cave3"],
                                     "subtitles.ambient.cave", 1.0),
    "block.water.ambient":          ("ambient", [A + "water"], "subtitles.block.water.ambient", 0.8),

    # -- deuren, kisten en water
    "block.wooden_door.open":  ("block", [X + "door_open"], "subtitles.block.door.toggle", 1.0),
    "block.wooden_door.close": ("block", [X + "door_close"], "subtitles.block.door.toggle", 1.0),
    "block.chest.open":        ("block", [X + "chest_open"], "subtitles.block.chest.open", 1.0),
    "block.chest.close":       ("block", [X + "chest_close"], "subtitles.block.chest.close", 1.0),
    "entity.generic.splash":   ("player", [X + "splash"], "subtitles.entity.generic.splash", 1.0),
    "entity.generic.swim":     ("player", SWIM, "subtitles.entity.generic.swim", 1.0),
    "entity.player.splash":    ("player", [X + "splash"], "subtitles.entity.generic.splash", 1.0),
    "entity.player.swim":      ("player", SWIM, "subtitles.entity.generic.swim", 1.0),
}


def sounds_json():
    doc = {}
    for event, (cat, files, subtitle, vol) in EVENTS.items():
        entry = {"replace": True, "category": cat,
                 "sounds": [{"name": f, "volume": vol} for f in files]}
        if subtitle:
            entry["subtitle"] = subtitle
        doc[event] = entry
    return doc
