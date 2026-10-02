"""Reels na středu: připomenutí voleb + co chceme prosadit, se všemi samolepkami. 1080x1920, 30 fps, se zvukem."""
import os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
import render as R
import audio as A
import festival as FE
import kino as K1
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, El, TextScene, Slam)
from kino2 import Words
from kino import shake_post
import armsticker as AS
from podzim import logo_sticker
from rozpocet2 import Pop, MePoint
import pivo as PV

HERE = R.HERE
OUT = os.path.join(HERE, "streda_pripominka.mp4")
LOGO = logo_sticker()
GREY = (110, 122, 140)
KOVBOJ = Image.open(os.path.join(HERE, "kovboj.png")).convert("RGBA")

def pill(text, size=54):
    return text_img(text, size, DARK, w="ExtraBold", pill=WHITE, pad=(30, 14), radius=30)

def sub(text):
    return text_img(text, 50, GREY, w="SemiBold")

# ---------- S1: připomínka ----------
SL1 = 32
S1 = TextScene(105, BG, [Words("Už tento *pátek*", 250, 3, 100), Words("jsou *volby!*", 390, 12, 130),
                         Pop(pill("pátek 14–22"), 300, 560, 22, -3), Pop(pill("sobota 8–14"), 780, 560, 28, 3),
                         Slam(FE.scaled(FE.ST_PLAIN, 780), W // 2, 0, SL1),
                         Pop(text_img("Karel Krupička", 46, WHITE, w="ExtraBold", pill=GD, pad=(24, 10), radius=22), 790, 1230, SL1 + 12, 6)],
               post=shake_post([SL1 + 5], BG))

# ---------- S2–S5: čtyři pilíře programu (každý s jinou samolepkou) ----------
def counter(i):
    return text_img(f"Náš program  ·  {i}/4", 40, GD, w="ExtraBold", pill=(226, 240, 222), pad=(26, 10), radius=24)

def tag(text, rot):
    return text_img(text, 44, WHITE, w="ExtraBold", pill=GD, pad=(24, 10), radius=22)

def topic(i, lines, subs, sticker_el, n=78, slam_at=None, tag_el=None):
    els = [El(counter(i), W // 2, 200, 0, "rise", dur=8)]
    y = 330
    for j, ln in enumerate(lines):
        els.append(Words(ln, y, 4 + j * 7, 84)); y += 112
    y += 10
    for j, t in enumerate(subs):
        els.append(El(sub(t), W // 2, y, 18 + j * 5, "rise")); y += 64
    els.append(sticker_el)
    if tag_el:
        els.append(tag_el)
    return TextScene(n, BG, els, post=shake_post([slam_at + 5], BG) if slam_at is not None else None)

ST_W = 760
T1 = topic(1, ["Město, kde se", "*dobře_žije.*"], ["Živé centrum Sedlce, zeleň a stín,", "bezpečné přechody pro pěší."],
           Slam(FE.scaled(FE.ST_SWAG, ST_W), W // 2, 0, 18), slam_at=18,
           tag_el=Pop(tag("v létě ve stínu", 0), 800, 1150, 38, 7))
T2 = topic(2, ["Město pro", "*všechny_generace.*"], ["Spolky, senioři i rodiny s dětmi.", "Funkční Lidový dům."],
           Slam(FE.scaled(FE.ST_HAT, ST_W), W // 2, 0, 20), slam_at=20)
T3 = topic(3, ["Město, které", "*komunikuje.*"], ["Otevřená radnice, schůzka online.", "Srozumitelná úřední deska."],
           MePoint(560, 14, AS.ArmSticker(760)),
           tag_el=Pop(tag("moje parketa", 0), 860, 990, 34, 7))
KOV = FE.scaled(KOVBOJ, 800)
T4 = topic(4, ["Město, které", "hospodaří *s_rozumem.*"], ["Investice s jasným plánem.", "Odpady bez přeplněných kontejnerů."],
           Slam(KOV, W // 2, 0, 22), n=84, slam_at=22,
           tag_el=Pop(tag("šerif rozpočtu", 0), 820, 1170, 42, 8))

# ---------- S6: závěr ----------
NAME = text_img("Karel Krupička", 72, DARK, w="ExtraBold")
BIG_LOGO = LOGO.resize((int(LOGO.width * 1.05), int(LOGO.height * 1.05)), Image.LANCZOS)
PROG = sub("Celý program: dobrasprava.cz")
S6 = TextScene(170, BG, [Words("V pátek *k_volbám,*", 250, 3, 96), Words("pak klidně *na_pivo.*", 375, 12, 96),
                         El(NAME, W // 2, 520, 24, dur=11),
                         El(PROG, W // 2, 600, 30, "rise"),
                         PV.MeCheers(None, 300, 0, 34),
                         Pop(BIG_LOGO, 245, 1560, 52, -6)])
PV.CLINK = 64

SCENES = [S1, T1, T2, T3, T4, S6]
TR = 8

def frames():
    for i, sc in enumerate(SCENES):
        prev_last = SCENES[i - 1].render(SCENES[i - 1].n - 1) if i else None
        for f in range(sc.n):
            cur = sc.render(f)
            if prev_last is not None and f < TR:
                e = ease_in_out((f + 1) / (TR + 1))
                cc = Image.new("RGBA", (W, H))
                cc.paste(prev_last, (0, int(-e * H * 0.35)))
                cc.paste(cur, (0, int((1 - e) * H)))
                cur = cc
            yield cur.convert("RGB")

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    out.add(0, A.seg_pop(total + .2, 0.55)[: int(total * SR)])
    for a in (3, 12, 22, 28):
        out.add(st[0] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[0] + (SL1 + 5) / FPS, A.fx_impact(), 0.9)
    slams = {1: 18, 2: 20, 4: 22}
    for i in range(1, 5):
        out.add(st[i], A.fx_whoosh(0.3), 0.35)
        for a in (4, 11, 18):
            out.add(st[i] + a / FPS, K1.fx_pop(), 0.45)
        if i in slams:
            out.add(st[i] + (slams[i] + 5) / FPS, A.fx_impact(), 0.8)
        else:
            out.add(st[i] + 16 / FPS, A.fx_whoosh(0.4), 0.5)
    out.add(st[4] + 42 / FPS, A.fx_ding(), 0.5)
    out.add(st[1] + 38 / FPS, K1.fx_pop(), 0.5)
    out.add(st[3] + 34 / FPS, K1.fx_pop(), 0.5)
    for a in (3, 12, 24, 30):
        out.add(st[5] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[5] + 34 / FPS, A.fx_whoosh(0.4), 0.5)
    out.add(st[5] + 52 / FPS, A.fx_impact(), 0.5)
    out.add(st[5] + PV.CLINK / FPS, PV.clink(), 0.8)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fo = int(1.2 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        for i in range(0, len(args), 2):
            SCENES[int(args[i])].render(int(args[i + 1])).convert("RGB").save(os.path.join(HERE, "hlas", f"s{args[i]}_{args[i+1]}.jpg"))
        sys.exit()
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "streda_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
