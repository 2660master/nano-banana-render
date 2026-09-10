# -*- coding: utf-8 -*-
"""Het geluidsontwerp zelf: welke klank hoort bij welke gebeurtenis.

Elke functie geeft een mono float32-array terug. De opzet is steeds hetzelfde:
een korte aanslag (klop of tik), een lichaam met onharmonische partialen zodat
het naar hout of steen klinkt, en een ritselstaart van gefilterde ruis.
"""
import numpy as np

from sounds import (bandpass, bell, chirp, env, finish, lowpass2, n_samples,
                    onepole_hp, onepole_lp, place, swell, tone, white, SR)


# ------------------------------------------------------------------- gevecht
def sword_hit(seed, pitch=190.0, bright=1.0, level=0.9):
    """Hout op hout, met een wolk ritselend blad eroverheen."""
    body = bell(pitch, 0.24, 0.055)
    click = onepole_hp(white(0.02, seed), 2600) * env(0.02, 0.008) * 0.55
    rustle = bandpass(white(0.20, seed + 1), 3000 * bright, 1.1) * env(0.20, 0.055, 0.006) * 0.45
    return finish(place((0, body), (0, click), (0.004, rustle)), level)


def crit(seed):
    """Zelfde klop, hoger, met drie oplopende klokjes erachteraan."""
    base = sword_hit(seed, 250.0, 1.35, level=0.8)
    spark = place(*[(0.035 * i, bell(920 * (1.26 ** i), 0.28, 0.055) * 0.32) for i in range(3)])
    return finish(place((0, base), (0.012, spark)))


def sweep(seed):
    """Veeg: wind door takken, met een lage vlaag eronder."""
    air = bandpass(white(0.34, seed), 1700, 0.8) * swell(0.34, 0.22)
    low = onepole_lp(white(0.34, seed + 5), 400) * swell(0.34, 0.30) * 0.5
    return finish(place((0, air), (0, low)), 0.75)


def weak_hit(seed):
    return sword_hit(seed, 150.0, 0.7, level=0.55)


def hurt(seed):
    """Zacht en laag — mag niet schel worden, je hoort dit vaak."""
    body = bell(118.0, 0.32, 0.095)
    breath = bandpass(white(0.26, seed), 640, 1.0) * env(0.26, 0.075, 0.012) * 0.45
    return finish(place((0, body), (0.004, breath)), 0.8)


def knockback(seed):
    thud = bell(95.0, 0.30, 0.08) * 0.9
    air = bandpass(white(0.22, seed), 900, 0.7) * swell(0.22, 0.2) * 0.5
    return finish(place((0, thud), (0, air)), 0.8)


# --------------------------------------------------------------------- magie
def totem():
    """De totem: lage bonk, opbloeiend akkoord, en vogels die opvliegen."""
    root = 261.63                                   # C
    chord = place(
        (0.00, bell(root, 2.1, 0.80) * 0.70),
        (0.06, bell(root * 1.25, 2.0, 0.74) * 0.58),    # grote terts
        (0.12, bell(root * 1.50, 1.9, 0.70) * 0.52),    # kwint
        (0.19, bell(root * 2.00, 1.8, 0.64) * 0.44),    # octaaf
        (0.32, bell(root * 3.00, 1.5, 0.48) * 0.22),
    )
    thump = bell(78.0, 0.55, 0.17) * 0.85
    birds = place(*[(0.34 + 0.17 * i,
                     chirp(1350 + 210 * i, 2500 + 300 * i, 0.10) * 0.20)
                    for i in range(5)])
    wash = bandpass(white(2.3, 77), 2500, 0.8) * swell(2.3, 0.22) * 0.11
    return finish(place((0, thump), (0, chord), (0, birds), (0, wash)), 0.92)


def levelup():
    notes = (392.00, 523.25, 659.25)                # G - C - E
    return finish(place(*[(0.095 * i, bell(f, 1.1, 0.34) * 0.8)
                          for i, f in enumerate(notes)]), 0.85)


def orb(seed):
    return finish(bell(1150 + seed * 70, 0.20, 0.05), 0.7)


def pop(seed):
    blip = tone(680 + seed * 40, 0.10, 0.026, harm=(1.0, 0.18))
    tick = onepole_hp(white(0.012, seed), 3200) * env(0.012, 0.005) * 0.35
    return finish(place((0, blip), (0, tick)), 0.6)


# ---------------------------------------------------------------- voetstappen
def step_grass(seed):
    return finish(bandpass(white(0.09, seed), 2300, 0.85) * env(0.09, 0.028, 0.002), 0.42)


def step_stone(seed):
    body = bell(430.0, 0.09, 0.018) * 0.6
    grit = onepole_hp(white(0.05, seed), 1800) * env(0.05, 0.014) * 0.8
    return finish(place((0, body), (0, grit)), 0.46)


def step_wood(seed):
    body = bell(285.0, 0.14, 0.036)
    tick = onepole_hp(white(0.014, seed), 2600) * env(0.014, 0.006) * 0.4
    return finish(place((0, body), (0, tick)), 0.48)


def step_sand(seed):
    return finish(bandpass(white(0.12, seed), 4200, 0.6) * env(0.12, 0.042, 0.004), 0.36)


def step_gravel(seed):
    grains = place(*[(0.012 * i, bandpass(white(0.05, seed + i), 2600 + 400 * i, 1.4)
                      * env(0.05, 0.016) * (0.9 - 0.2 * i)) for i in range(3)])
    return finish(grains, 0.46)


def step_wool(seed):
    return finish(onepole_lp(white(0.10, seed), 700) * env(0.10, 0.032, 0.006), 0.30)


def step_snow(seed):
    crunch = bandpass(white(0.10, seed), 3100, 0.9) * env(0.10, 0.030, 0.003)
    squeak = chirp(1600, 1150, 0.05) * 0.18
    return finish(place((0, crunch), (0.006, squeak)), 0.38)


# ------------------------------------------------------- graven, breken, zetten
def dig_grass(seed):
    return finish(bandpass(white(0.26, seed), 1900, 0.7) * env(0.26, 0.075, 0.008), 0.6)


def dig_stone(seed):
    body = bell(360.0, 0.28, 0.06) * 0.7
    grit = onepole_hp(white(0.22, seed), 1500) * env(0.22, 0.055, 0.005)
    return finish(place((0, body), (0, grit)), 0.66)


def dig_wood(seed):
    body = bell(240.0, 0.30, 0.085)
    split = bandpass(white(0.20, seed), 1700, 1.1) * env(0.20, 0.05, 0.006) * 0.55
    return finish(place((0, body), (0, split)), 0.66)


def dig_sand(seed):
    return finish(bandpass(white(0.30, seed), 3600, 0.55) * env(0.30, 0.095, 0.010), 0.55)


# ------------------------------------------------------------------- omgeving
def rain(dur=3.6):
    """Ruis met trage golving, plus losse druppels die erbovenuit tikken."""
    n = n_samples(dur)
    body = bandpass(white(dur, 11), 1300, 0.55)
    t = np.arange(n) / SR
    body *= 0.72 + 0.28 * np.sin(2 * np.pi * t / dur * 3)      # loopt netjes rond
    drops = place(*[(0.11 + 0.26 * i,
                     bell(2100 + 500 * ((i * 7) % 5), 0.08, 0.018) * 0.16)
                    for i in range(12)])
    out = place((0, body * 0.55), (0, drops))[:n]
    return finish(out, 0.55)


def thunder(seed, dur=3.2):
    """Scheur, dan een rommel die wegzakt."""
    crack = onepole_hp(white(0.09, seed), 900) * env(0.09, 0.03) * 0.8
    rumble = lowpass2(white(dur, seed + 3), 130, 0.7) * swell(dur, 0.12)
    tail = lowpass2(white(dur * 0.7, seed + 9), 70, 0.6) * swell(dur * 0.7, 0.35) * 0.7
    return finish(place((0, crack), (0.02, rumble), (0.5, tail)), 0.9)


def cave(seed, dur=4.0):
    """Lage bromtoon met een druppel in de verte."""
    n = n_samples(dur)
    t = np.arange(n) / SR
    drone = (np.sin(2 * np.pi * 68 * t) + 0.6 * np.sin(2 * np.pi * 68.7 * t)) * 0.35
    drone *= 0.45 + 0.55 * np.sin(np.pi * t / dur) ** 2
    air = lowpass2(white(dur, seed), 420, 0.6) * 0.18
    drip = place((dur * 0.42, bell(1500, 0.30, 0.07) * 0.22),
                 (dur * 0.71, bell(1180, 0.26, 0.06) * 0.16))
    return finish(place((0, drone + air), (0, drip))[:n], 0.5)


def water_ambient(seed, dur=2.6):
    """Zacht geborrel: korte gestemde blipjes onder water."""
    blips = place(*[(0.14 + 0.19 * i,
                     chirp(320 + 90 * ((i * 5) % 6), 620 + 110 * ((i * 3) % 5), 0.07) * 0.28)
                    for i in range(12)])
    bed = onepole_lp(white(dur, seed), 900) * 0.12
    return finish(place((0, bed), (0, blips))[:n_samples(dur)], 0.45)


# ----------------------------------------------------------------------- misc
def creak(seed, f0=190.0, f1=320.0, dur=0.55, level=0.7):
    """Deurscharnier: stijgende toon met beving en een houten rand."""
    n = n_samples(dur)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / t[-1]) * (1.0 + 0.05 * np.sin(2 * np.pi * 11 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = (np.sin(ph) + 0.35 * np.sin(2 * ph)) * env(dur, dur * 0.5, 0.05)
    grain = bandpass(white(dur, seed), 1700, 1.6) * env(dur, dur * 0.45, 0.05) * 0.35
    return finish(place((0, body * 0.7), (0, grain)), level)


def door_open(seed):
    return finish(place((0, creak(seed, 180, 330, 0.6, 0.8)),
                        (0.55, bell(160, 0.22, 0.05) * 0.5)), 0.75)


def door_close(seed):
    return finish(place((0, creak(seed, 300, 170, 0.35, 0.6)),
                        (0.30, bell(140, 0.30, 0.075) * 0.9)), 0.8)


def chest_open(seed):
    return finish(creak(seed, 240, 400, 0.45, 0.6), 0.6)


def chest_close(seed):
    return finish(place((0, creak(seed, 380, 230, 0.26, 0.5)),
                        (0.22, bell(210, 0.20, 0.05) * 0.8)), 0.65)


def splash(seed):
    burst = bandpass(white(0.35, seed), 2400, 0.6) * env(0.35, 0.09, 0.004)
    low = onepole_lp(white(0.25, seed + 2), 500) * env(0.25, 0.06) * 0.6
    drops = place(*[(0.08 + 0.05 * i, bell(1700 + 300 * i, 0.10, 0.025) * 0.18)
                    for i in range(4)])
    return finish(place((0, burst), (0, low), (0, drops)), 0.8)


def swim(seed):
    return finish(bandpass(white(0.28, seed), 1500, 0.7) * swell(0.28, 0.3), 0.5)


# ------------------------------------------------------------------ catalogus
def catalog():
    """Pad in het pack -> functie. Pad wordt assets/minecraft/sounds/<pad>.ogg"""
    out = {}
    for i in range(3):
        out[f"verdant/combat/hit{i + 1}"] = lambda i=i: sword_hit(10 + i, 185 + i * 14)
        out[f"verdant/combat/hurt{i + 1}"] = lambda i=i: hurt(30 + i)
    for i in range(2):
        out[f"verdant/combat/crit{i + 1}"] = lambda i=i: crit(20 + i)
        out[f"verdant/combat/weak{i + 1}"] = lambda i=i: weak_hit(40 + i)
    out["verdant/combat/sweep"] = lambda: sweep(50)
    out["verdant/combat/knockback"] = lambda: knockback(60)

    out["verdant/magic/totem"] = totem
    out["verdant/magic/levelup"] = levelup
    for i in range(2):
        out[f"verdant/magic/orb{i + 1}"] = lambda i=i: orb(i)
        out[f"verdant/magic/pop{i + 1}"] = lambda i=i: pop(i)

    steps = {"grass": step_grass, "stone": step_stone, "wood": step_wood,
             "sand": step_sand, "gravel": step_gravel, "wool": step_wool,
             "snow": step_snow}
    for mat, fn in steps.items():
        for i in range(4):
            out[f"verdant/step/{mat}{i + 1}"] = lambda fn=fn, i=i: fn(100 + i)

    digs = {"grass": dig_grass, "stone": dig_stone, "wood": dig_wood, "sand": dig_sand}
    for mat, fn in digs.items():
        for i in range(3):
            out[f"verdant/dig/{mat}{i + 1}"] = lambda fn=fn, i=i: fn(200 + i)

    out["verdant/ambient/rain"] = rain
    for i in range(2):
        out[f"verdant/ambient/thunder{i + 1}"] = lambda i=i: thunder(300 + i)
    for i in range(3):
        out[f"verdant/ambient/cave{i + 1}"] = lambda i=i: cave(400 + i)
    out["verdant/ambient/water"] = lambda: water_ambient(500)

    out["verdant/misc/door_open"] = lambda: door_open(600)
    out["verdant/misc/door_close"] = lambda: door_close(601)
    out["verdant/misc/chest_open"] = lambda: chest_open(602)
    out["verdant/misc/chest_close"] = lambda: chest_close(603)
    out["verdant/misc/splash"] = lambda: splash(604)
    for i in range(3):
        out[f"verdant/misc/swim{i + 1}"] = lambda i=i: swim(610 + i)
    return out
