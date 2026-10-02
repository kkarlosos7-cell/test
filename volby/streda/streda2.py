"""Reels na středu v2: připomenutí voleb postavené na Karlovi – finanční výbor, rozpočet na klik, pilíře programu. 1080x1920, 30 fps."""
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
from kino import outline, shake_post
import armsticker as AS
from podzim import logo_sticker
from rozpocet2 import Pop, MePoint
import fv as FV

HERE = R.HERE
OUT = os.path.join(HERE, "streda_pripominka_v2.mp4")
LOGO = logo_sticker()
GREY = (110, 122, 140)
KOVBOJ = Image.open(os.path.join(HERE, "kovboj.png")).convert("RGBA")

def pill(text, size=54):
    return text_img(text, size, DARK, w="ExtraBold", pill=WHITE, pad=(30, 14), radius=30)
def sub(text, size=50):
    return text_img(text, size, GREY, w="SemiBold")

# ---------- S1: připomínka ----------
SL1 = 30
NAME_PILL = text_img("Karel Krupička", 46, WHITE, w="ExtraBold", pill=GD, pad=(24, 10), radius=22)
S1 = TextScene(105, BG, [Words("Už v *pátek*", 260, 3, 110), Words("volíme.", 390, 10, 110),
                         Pop(pill("pátek 14–22"), 300, 540, 18, -3), Pop(pill("sobota 8–14"), 780, 540, 24, 3),
                         Slam(FE.scaled(FE.ST_PLAIN, 780), W // 2, 0, SL1),
                         Pop(NAME_PILL, 790, 1230, SL1 + 12, 6)],
               post=shake_post([SL1 + 5], BG))

# ---------- S2: 4 roky ve finančním výboru ----------
SL2, ST2 = 30, 52
S2 = TextScene(120, BG, [Words("Čtyři roky ve", 260, 3, 96), Words("*finančním_výboru.*", 385, 10, 96),
                         El(sub("Procházím, co jde do zastupitelstva,"), W // 2, 510, 18, "rise"),
                         El(sub("dřív, než se o tom hlasuje."), W // 2, 574, 23, "rise"),
                         Slam(FV.me_with_lupa(), W // 2, 0, SL2),
                         ],
               post=shake_post([SL2 + 5], BG))

# ---------- S3: rozpočet na klik ----------
from rozpocet2 import IntroPhone
S3 = TextScene(120, BG, [Words("Kam jdou", 240, 3, 92), Words("peníze města?", 355, 8, 92), Words("*Na_klik.*", 480, 14, 120),
                         El(sub("Interaktivní rozpočet už běží"), W // 2, 600, 20, "rise"),
                         El(sub("na dobrasprava.cz/rozpocet"), W // 2, 664, 25, "rise"),
                         IntroPhone(None, 540, 1260, 16)])

# ---------- S4: pilíře programu – jen nadpisy ----------
CARD_W, CARD_H = 900, 132
def card(text, hl=False):
    img = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, CARD_W - 1, CARD_H - 1], radius=34, fill=G if hl else WHITE)
    if not hl:
        d.rounded_rectangle([0, 0, 14, CARD_H - 1], radius=7, fill=G)
    ck = FV.check_img(66)
    img.alpha_composite(ck, (44, (CARD_H - ck.height) // 2))
    d.text((140, CARD_H / 2), text, font=font(54, "ExtraBold"), fill=WHITE if hl else DARK, anchor="lm")
    return outline(img, 6)

HEADS = ["kde se dobře žije", "pro všechny generace", "které komunikuje", "které hospodaří s rozumem"]
class Slide(El):
    """Karta vyjede zleva s lehkým přestřelením."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 10), 1.3)
        a = clamp(k / 4)
        img = self.img
        if a < 1:
            img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        c.alpha_composite(img, (int(self.cx - img.width / 2 - (1 - p) * 300), int(self.cy - img.height / 2)))

s4 = [Words("Chceme *město,*", 260, 3, 110)]
for i, t in enumerate(HEADS):
    s4.append(Slide(card(t, i == 3), W // 2, 440 + i * 158, 14 + i * 9))
s4.append(MePoint(620, 44, AS.ArmSticker(640)))
S4 = TextScene(140, BG, s4)

# ---------- S5: závěr ----------
SL5 = 40
BIG_LOGO = LOGO.resize((int(LOGO.width * .95), int(LOGO.height * .95)), Image.LANCZOS)
S5 = TextScene(165, BG, [Words("Dejte hlas", 250, 3, 100), Words("*Dobré_správě.*", 380, 10, 120),
                         El(text_img("dobrasprava.cz", 72, DARK, w="ExtraBold"), W // 2, 525, 22, dur=11),
                         El(sub("Karel Krupička a celý tým Dobré správy", 44), W // 2, 605, 30, "rise"),
                         Slam(FE.scaled(FE.ST_PLAIN, 760), W // 2, 0, SL5),
                         Pop(BIG_LOGO, W // 2, 850, SL5 + 14, -4)],
               post=shake_post([SL5 + 5], BG))

SCENES = [S1, S2, S3, S4, S5]
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
    out.add(0, A.seg_pop(total + .2, 0.5)[: int(total * SR)])
    for a in (3, 10, 18, 24, SL1 + 12):
        out.add(st[0] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[0] + (SL1 + 5) / FPS, A.fx_impact(), 0.9)
    for a in (3, 10, 18, 23):
        out.add(st[1] + a / FPS, K1.fx_pop(), 0.45)
    out.add(st[1] + (SL2 + 5) / FPS, A.fx_impact(), 0.8)
    for a in (3, 12, 20, 25):
        out.add(st[2] + a / FPS, K1.fx_pop(), 0.45)
    out.add(st[2] + 16 / FPS, A.fx_whoosh(0.5), 0.6)
    out.add(st[3] + 3 / FPS, K1.fx_pop(), 0.5)
    for i in range(4):
        out.add(st[3] + (14 + i * 9) / FPS, A.fx_whoosh(0.2), 0.35)
        out.add(st[3] + (18 + i * 9) / FPS, K1.fx_pop(), 0.45)
    out.add(st[3] + 48 / FPS, A.fx_ding(), 0.5)
    out.add(st[3] + 30 / FPS, A.fx_whoosh(0.4), 0.4)
    for a in (3, 10, 22, 30):
        out.add(st[4] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[4] + (SL5 + 5) / FPS, A.fx_impact(), 0.9)
    out.add(st[4] + (SL5 + 14) / FPS, K1.fx_pop(), 0.5)
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
            SCENES[int(args[i])].render(int(args[i + 1])).convert("RGB").save(os.path.join(HERE, "hlas", f"t{args[i]}_{args[i+1]}.jpg"))
        sys.exit()
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "streda2_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
