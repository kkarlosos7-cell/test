"""Syntetizované podkresy pro jednotlivé scény (bez cizí hudby, bez licencí)."""
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 44100
rng = np.random.default_rng(7)

def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12)

N = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
def m(name):  # "C4" -> midi
    return 12 * (int(name[-1]) + 1) + N[name[:-1]]

def t_(n): return np.arange(n) / SR

def osc(kind, f, dur, vib=0.0):
    n = int(dur * SR); t = t_(n)
    ph = f * t
    if vib:
        ph = ph + vib * np.sin(2 * np.pi * 5.5 * t) / (2 * np.pi * 5.5) * f * 0.01
    if kind == "sine": return np.sin(2 * np.pi * ph)
    if kind == "saw": return 2 * (ph % 1) - 1
    if kind == "square": return np.sign(np.sin(2 * np.pi * ph))
    if kind == "tri": return 2 * np.abs(2 * (ph % 1) - 1) - 1

def env(n, a=0.005, d=0.1, s=0.6, r=0.05):
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n); e[:na] = np.linspace(0, 1, na)
    nd2 = min(nd, n - na)
    e[na:na + nd2] = np.linspace(1, s, nd)[:nd2]
    if nr and n > nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e

def decay(n, tau):
    return np.exp(-t_(n) / tau)

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)

class Track:
    def __init__(self, dur):
        self.b = np.zeros(int(dur * SR) + SR)
    def add(self, t, sig, g=1.0):
        i = int(t * SR)
        if i < 0: sig, i = sig[-i:], 0
        j = min(len(self.b), i + len(sig))
        if j > i: self.b[i:j] += sig[: j - i] * g

# ---------- nástroje ----------
def kick(g=1.0):
    n = int(0.35 * SR); t = t_(n)
    f = 45 + 110 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(n, 0.12) * g

def snare():
    n = int(0.22 * SR)
    return (bp(rng.standard_normal(n), 1200, 7000) * 0.8 + osc("sine", 190, 0.22)[:n] * 0.5) * decay(n, 0.06)

def clap():
    n = int(0.25 * SR); x = bp(rng.standard_normal(n), 900, 5000)
    e = np.zeros(n)
    for k in range(3):
        i = int(k * 0.011 * SR); e[i:] += np.exp(-t_(n - i) / (0.008 if k < 2 else 0.07))
    return x * e * 0.8

def hat(open_=False):
    d = 0.18 if open_ else 0.05
    n = int(d * SR)
    return hp(rng.standard_normal(n), 7000) * decay(n, d / 3) * 0.35

def crash():
    n = int(1.4 * SR)
    return hp(rng.standard_normal(n), 4000) * decay(n, 0.45) * 0.35

def pluck(f, dur=0.3, bright=3000):
    x = osc("saw", f, dur) * 0.5 + osc("square", f * 2, dur) * 0.15
    return lp(x, bright) * decay(len(x), dur / 4)

def xylo(f, dur=0.5):
    n = int(dur * SR)
    return (osc("sine", f, dur) + 0.35 * osc("sine", f * 4, dur) * decay(n, 0.03) + 0.2 * osc("sine", f * 3, dur)) * decay(n, 0.16)

def brass(f, dur, g=1.0, bright=2200):
    x = osc("saw", f, dur, vib=0.6) + 0.5 * osc("saw", f * 1.003, dur)
    return lp(x, bright) * env(len(x), 0.03, 0.08, 0.7, 0.05) * g

def tuba(f, dur):
    x = osc("saw", f, dur) * 0.7 + osc("sine", f, dur)
    return lp(x, 380) * env(len(x), 0.02, 0.1, 0.6, 0.05)

def dist_gtr(freqs, dur, g=1.0):
    x = sum(osc("saw", f, dur) + 0.4 * osc("saw", f * 1.005, dur) for f in freqs)
    x = np.tanh(x * 4)
    x = lp(x, 3200, 4)
    return x * env(len(x), 0.004, 0.05, 0.75, 0.03) * g

def sub(f, dur):
    x = osc("sine", f, dur) + 0.25 * osc("tri", f * 2, dur)
    return x * env(len(x), 0.005, 0.05, 0.8, 0.04)

def stab(freqs, dur, fc=2500):
    x = sum(osc("saw", f, dur) + osc("saw", f * 1.006, dur) for f in freqs)
    return lp(x, fc) * env(len(x), 0.003, 0.08, 0.3, 0.05) * 0.25

def chord(root, kind="maj"):
    iv = [0, 4, 7] if kind == "maj" else [0, 3, 7]
    return [mf(root + i) for i in iv]

# ---------- scény ----------
def seg_intro(dur):
    T = Track(dur); b = 0.5   # 120 BPM
    prog = [(m("C4"), "maj"), (m("G3"), "maj"), (m("A3"), "min"), (m("F3"), "maj")]
    for k in range(int(dur / (b / 2)) + 1):
        root, kind = prog[(k // 4) % 4]
        fs = chord(root, kind) + [mf(root + 12)]
        T.add(k * b / 2, pluck(fs[k % 4] * 2, 0.35), 0.35)
    for k in range(int(dur / b) + 1):
        T.add(k * b, kick(0.8), 0.6)
        if k % 2: T.add(k * b, clap(), 0.35)
        T.add(k * b + b / 2, hat(), 0.5)
    return T.b

def seg_bambulacek(dur):
    T = Track(dur); b = 0.3
    mel = ["C5", "E5", "G5", "E5", "F5", "A5", "G5", None, "E5", "G5", "C6", "G5", "A5", "F5", "D5", "C5"]
    for k, n in enumerate(mel * 2):
        if n and k * b < dur: T.add(k * b, xylo(mf(m(n))), 0.45)
    for k in range(int(dur / (2 * b)) + 1):
        root = [m("C3"), m("F3"), m("G3"), m("C3")][(k // 2) % 4]
        T.add(k * 2 * b, lp(osc("tri", mf(root), 0.5), 800) * decay(int(0.5 * SR), 0.15), 0.35)
    return T.b

def seg_dechovka(dur):
    T = Track(dur); b = 0.23   # polka, rychlé 2/4
    bass = [m("C2"), m("G1"), m("C2"), m("G1"), m("G1"), m("D2"), m("G1"), m("D2")]
    chords = [chord(m("C4")), chord(m("C4")), chord(m("G3"))[:1] + [mf(m("B3")), mf(m("D4")), mf(m("F4"))], chord(m("C4"))]
    for k in range(int(dur / b) + 1):
        T.add(k * 2 * b, tuba(mf(bass[k % 8]), b * 0.9), 0.9)
        cs = chords[(k // 2) % 4]
        T.add(k * 2 * b + b, sum(brass(f, b * 0.6, 1, 1800) for f in cs) / 3, 0.35)
        T.add(k * 2 * b, kick(0.5), 0.3)
    mel = [("G4", 1), ("C5", 1), ("E5", 1), ("C5", 1), ("G4", 1), ("C5", 1), ("E5", 2),
           ("F5", 1), ("E5", 1), ("D5", 1), ("C5", 1), ("B4", 1), ("D5", 1), ("G4", 2),
           ("G4", 1), ("C5", 1), ("E5", 1), ("G5", 1), ("E5", 2), ("C5", 2)]
    t = 0
    for n, l in mel:
        if t < dur: T.add(t, brass(mf(m(n)), l * b * 0.92, 1, 3000), 0.5)
        t += l * b
    return T.b

def seg_bigbit(dur):
    T = Track(dur); b = 60 / 150
    riff = [m("E2"), m("E2"), m("G2"), m("E2"), m("A2"), m("A2"), m("G2"), m("D2")]
    for k in range(int(dur / (b / 2)) + 1):
        r = riff[(k // 2) % 8]
        T.add(k * b / 2, dist_gtr([mf(r), mf(r + 7), mf(r + 12)], b / 2 * 0.9), 0.22)
        T.add(k * b / 2, lp(osc("saw", mf(r - 12), b / 2 * 0.9), 300) * env(int(b / 2 * 0.9 * SR)), 0.3)
        T.add(k * b / 2, hat(), 0.45)
    for k in range(int(dur / b) + 1):
        if k % 2 == 0: T.add(k * b, kick(), 0.8)
        else: T.add(k * b, snare(), 0.6)
    T.add(0, crash(), 0.8)
    return T.b

def seg_vecer(dur, dj_t):
    """Kapela (rock) do nástupu DJ, pak house 120 BPM."""
    T = Track(dur)
    b = 0.5
    rp = [m("A2"), m("A2"), m("F2"), m("G2")]
    for k in range(int(dj_t / (b / 2))):
        r = rp[(k // 4) % 4]
        T.add(k * b / 2, dist_gtr([mf(r), mf(r + 7), mf(r + 12)], b / 2 * 0.9), 0.2)
        T.add(k * b / 2, hat(), 0.4)
        if k % 2 == 0:
            T.add(k * b / 2, kick() if (k // 2) % 2 == 0 else snare(), 0.7)
    # riser před DJ
    rn = int(1.2 * SR); rt = t_(rn)
    riser = bp(rng.standard_normal(rn), 600, 9000) * (rt / rt[-1]) ** 2 * 0.5
    riser += osc("saw", 200, 1.2)[:rn] * 0 + np.sin(2 * np.pi * np.cumsum(200 + 900 * (rt / rt[-1]) ** 2) / SR) * (rt / rt[-1]) ** 2 * 0.15
    T.add(dj_t - 1.2, riser, 0.8)
    # drum & bass, 180 BPM
    b = 60 / 180
    bar = 4 * b
    nb = int((dur - dj_t) / bar) + 1
    notes = [m("F1"), m("F1"), m("G#1"), m("D#1")]
    for k in range(nb):
        t0 = dj_t + k * bar
        # breakbeat: kick 1, snare 2, kick 3a, snare 4 + ghost noty
        T.add(t0, kick(1.2), 1.0)
        T.add(t0 + 2.5 * b, kick(1.1), 0.9)
        T.add(t0 + b, snare(), 0.85)
        T.add(t0 + 3 * b, snare(), 0.85)
        T.add(t0 + 1.75 * b, snare(), 0.25)
        T.add(t0 + 3.75 * b, snare(), 0.3)
        for h in range(8):
            T.add(t0 + h * b / 2, hat(open_=(h == 7)), 0.4 if h % 2 else 0.25)
        for h in (3, 11, 13):
            T.add(t0 + h * b / 4, hat(), 0.3)
        # reese bass
        f = mf(notes[k % 4])
        n = int(bar * SR); tt = t_(n)
        x = osc("saw", f * 2, bar) + osc("saw", f * 2 * 1.008, bar) + osc("saw", f * 2 * 0.993, bar)
        fc = 250 + 650 * (0.5 + 0.5 * np.sin(2 * np.pi * tt / (b * 2)))
        y = np.zeros(n); st = 0.0
        a_ = 1 - np.exp(-2 * np.pi * fc / SR)
        for q in range(n):
            st += a_[q] * (x[q] - st); y[q] = st
        y = np.tanh(y * 2.5) * 0.5 + np.sin(2 * np.pi * f * tt) * 0.7
        T.add(t0, y * env(n, 0.01, 0.1, 0.9, 0.03), 0.55)
    # atmosférický pad
    pdur = dur - dj_t
    pad = sum(lp(osc("saw", mf(x_), pdur) + osc("saw", mf(x_) * 1.004, pdur), 1200) for x_ in (m("F3"), m("G#3"), m("C4")))
    T.add(dj_t, pad * env(len(pad), 0.4, 0.1, 1, 0.3), 0.05)
    T.add(dj_t, crash(), 0.8)
    return T.b

def seg_pop(dur, g=1.0):
    T = Track(dur); b = 0.5
    prog = [(m("C3"), "maj"), (m("G2"), "maj"), (m("A2"), "min"), (m("F2"), "maj")]
    for k in range(int(dur / b) + 1):
        root, kind = prog[(k // 4) % 4]
        cs = chord(root + 12, kind)
        T.add(k * b, kick(0.9), 0.7)
        if k % 2: T.add(k * b, clap(), 0.4)
        T.add(k * b + b / 2, hat(), 0.45)
        T.add(k * b, sub(mf(root - 12), b * 0.9), 0.4)
        for j, f in enumerate(cs + [cs[0] * 2]):
            T.add(k * b + j * b / 4, pluck(f * 2, 0.3), 0.25)
        if k % 4 == 0:
            T.add(k * b, sum(brass(f, b * 1.5, 1, 2600) for f in cs) / 3, 0.35)
    return T.b * g

# ---------- efekty ----------
def fx_boing():
    n = int(0.5 * SR); t = t_(n)
    f = 300 + 180 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / 0.2)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(n, 0.2) * 0.6

def fx_impact():
    n = int(0.9 * SR); t = t_(n)
    f = 35 + 120 * np.exp(-t / 0.05)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(n, 0.25)
    x += lp(rng.standard_normal(n), 1500) * decay(n, 0.05) * 0.8
    return x

def fx_whoosh(d=0.6):
    n = int(d * SR); t = t_(n)
    x = bp(rng.standard_normal(n), 300, 4000)
    return x * np.sin(np.pi * t / d) ** 2 * 0.4

def fx_ding():
    n = int(0.6 * SR)
    return (osc("sine", 1568, 0.6) + 0.5 * osc("sine", 2349, 0.6)) * decay(n, 0.15) * 0.35

def fx_scratch():
    n = int(0.35 * SR); t = t_(n)
    sp = np.sin(2 * np.pi * 5 * t)
    x = bp(rng.standard_normal(n), 500, 3000) * np.abs(sp)
    x += np.sin(2 * np.pi * np.cumsum(300 + 250 * sp) / SR) * 0.3
    return x * 0.6

# ---------- sestavení ----------
def build(starts, ev, path):
    total = ev["end"]
    out = Track(total)
    segs = [seg_intro, seg_bambulacek, seg_dechovka, seg_bigbit,
            lambda d: seg_vecer(d, ev["dj"] - starts[4]), lambda d: seg_pop(d), lambda d: seg_pop(d, 0.85)]
    ends = starts[1:] + [total]
    XF = 0.12
    for i, fn in enumerate(segs):
        dur = ends[i] - starts[i] + XF
        x = fn(dur)[: int(dur * SR)]
        fi, fo = int(0.02 * SR), int(XF * SR)
        x[:fi] *= np.linspace(0, 1, fi)
        if i < len(segs) - 1:
            x[-fo:] *= np.linspace(1, 0, fo)
        out.add(starts[i], x)
    out.add(ev["boing"], fx_boing(), 0.8)
    out.add(ev["slam5"] - 0.02, fx_impact(), 1.0)
    out.add(ev["glasses"] - 0.55, fx_whoosh(0.6), 0.9)
    out.add(ev["glasses"], fx_ding(), 1.0)
    out.add(ev["dj"] - 0.05, fx_scratch(), 0.9)
    out.add(ev["slam7"] - 0.02, fx_impact(), 1.0)
    y = out.b[: int(total * SR)]
    y = hp(y, 30)
    # konec: fade out
    fo = int(1.2 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    st = np.stack([y, y], axis=1)
    wavfile.write(path, SR, (st * 32767).astype(np.int16))
