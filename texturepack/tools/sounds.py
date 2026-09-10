# -*- coding: utf-8 -*-
"""Gesynthetiseerde natuurgeluiden voor het Verdant texturepack.

Alles wordt hier van nul opgebouwd uit ruis en toon — er zitten geen samples
in. Mono, 44100 Hz, OGG Vorbis: mono is belangrijk, want Minecraft plaatst
alleen mono-geluiden echt in de ruimte. Stereo klinkt overal even hard.

De klankwereld: hout dat op hout tikt, blad dat ritselt, water dat druppelt,
en voor de totem een korte bloei van vogelachtige tonen.
"""
import numpy as np

SR = 44100


# ------------------------------------------------------------------- basis
def n_samples(seconds):
    return max(1, int(SR * seconds))


def rng(seed):
    return np.random.default_rng(seed)


def white(dur, seed):
    return rng(seed).standard_normal(n_samples(dur))


def env(dur, decay, attack=0.003, curve=1.0):
    """Aanslag plus exponentiële uitdoving."""
    n = n_samples(dur)
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-5), 0, 1) ** 0.6
    return a * np.exp(-(t / decay) ** curve)


def swell(dur, peak=0.35):
    """Zwelt op en zakt weer weg — voor wind en vegen."""
    n = n_samples(dur)
    t = np.linspace(0, 1, n)
    return np.sin(np.pi * np.clip(t / peak, 0, 1) * 0.5) ** 2 * np.exp(-(t - peak).clip(0) * 6)


def onepole_lp(x, cutoff):
    a = 1.0 - np.exp(-2.0 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(x.size):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def onepole_hp(x, cutoff):
    return x - onepole_lp(x, cutoff)


def biquad(x, b, a):
    y = np.empty_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(x.size):
        xi = x[i]
        yi = (b[0] * xi + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2) / a[0]
        x2, x1 = x1, xi
        y2, y1 = y1, yi
        y[i] = yi
    return y


def bandpass(x, f0, q=4.0):
    w0 = 2 * np.pi * f0 / SR
    al = np.sin(w0) / (2 * q)
    return biquad(x, (al, 0.0, -al), (1 + al, -2 * np.cos(w0), 1 - al))


def lowpass2(x, f0, q=0.707):
    w0 = 2 * np.pi * f0 / SR
    al = np.sin(w0) / (2 * q)
    c = np.cos(w0)
    return biquad(x, ((1 - c) / 2, 1 - c, (1 - c) / 2), (1 + al, -2 * c, 1 - al))


def tone(freq, dur, decay, harm=(1.0, 0.3, 0.12), attack=0.002):
    """Gedempte toon met boventonen — de basis voor hout en klokjes."""
    n = n_samples(dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for i, amp in enumerate(harm):
        y += amp * np.sin(2 * np.pi * freq * (i + 1) * t)
    return y * env(dur, decay, attack)


def bell(freq, dur, decay):
    """Onharmonische partialen: klinkt als hout of steen, niet als een orgel."""
    n = n_samples(dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for mult, amp, dfac in ((1.0, 1.0, 1.0), (2.76, 0.45, 0.6), (5.40, 0.22, 0.35),
                            (8.93, 0.11, 0.22)):
        y += amp * np.sin(2 * np.pi * freq * mult * t) * np.exp(-t / (decay * dfac))
    return y * env(dur, decay, attack=0.001)


def chirp(f0, f1, dur, decay=None):
    """Toonveeg — vogelachtig als hij kort en stijgend is."""
    n = n_samples(dur)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / max(t[-1], 1e-6))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(dur, decay or dur * 0.4, attack=0.004)


def place(*parts):
    """Legt (offset_in_seconden, signaal) over elkaar heen."""
    total = max(n_samples(off) + sig.size for off, sig in parts)
    out = np.zeros(total)
    for off, sig in parts:
        i = n_samples(off) if off else 0
        out[i:i + sig.size] += sig
    return out


def finish(x, peak=0.85, fade_ms=4):
    """Normaliseren en de randen afvlakken, anders hoor je een klik."""
    m = np.max(np.abs(x))
    if m > 0:
        x = x / m * peak
    f = max(1, int(SR * fade_ms / 1000))
    if x.size > 2 * f:
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
    return x.astype(np.float32)
