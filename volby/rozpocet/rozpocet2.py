"""Reels: moderní rozklikávací rozpočet Starého Plzence (dobrasprava.cz/rozpocet). 1080x1920, 30 fps, se zvukem."""
import os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
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

HERE = R.HERE
OUT = os.path.join(HERE, "rozpocet_reels.mp4")
LOGO = logo_sticker()
GREY = (120, 130, 148)
NOTE = text_img("Testovací verze · zdroj dat: MF ČR", 30, GREY, w="SemiBold")

class Pop(El):
    def __init__(self, img, cx, cy, at, rot=0):
        super().__init__(img, cx, cy, at); self.rot = rot
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 10))
        s = 0.3 + 0.7 * p
        img = self.img.resize((max(2, int(self.img.width * s)), max(2, int(self.img.height * s))), Image.BILINEAR)
        if self.rot:
            img = img.rotate(self.rot * p + 1.2 * math.sin(k * .12), expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

class MePoint(El):
    def __init__(self, cx, at, sticker, base_y=30):
        super().__init__(None, cx, 0, at); self.st, self.by = sticker, base_y
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        dy = (1 - ease_out_back(clamp(k / 12), 1.3)) * 1000
        a = -8 + 7 * math.sin(f * .22)
        img = self.st.image(a)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(H - img.height + self.by + dy)))

# ---------- ikonky ----------
def coin(s=110):
    img = Image.new("RGBA", (s + 24, s + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([12, 12, 12 + s, 12 + s], fill=(214, 160, 40))
    d.ellipse([19, 19, 5 + s, 5 + s], fill=(244, 194, 66))
    d.text((12 + s / 2, 12 + s / 2), "Kč", font=font(int(s * .36), "ExtraBold"), fill=(150, 100, 20), anchor="mm")
    return outline(img, 6)
COIN = coin()

class Coins(El):
    def __init__(self, at, n=10, seed=2):
        super().__init__(None, 0, 0, at)
        r = random.Random(seed)
        self.c = [(r.uniform(80, W - 80), at + r.uniform(0, 40), r.uniform(10, 16), r.uniform(.12, .25), r.uniform(0, 6), r.uniform(.6, 1.0))
                  for _ in range(n)]
    def draw(self, c, f):
        for x, t0, v, sp, ph, sc in self.c:
            k = f - t0
            if k < 0:
                continue
            y = -120 + v * k + .3 * k * k
            if y > H + 100:
                continue
            w = max(.15, abs(math.cos(ph + sp * k)))
            img = COIN.resize((max(2, int(COIN.width * sc * w)), int(COIN.height * sc)), Image.BILINEAR)
            c.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))

def laptop():
    img = Image.new("RGBA", (420, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([50, 20, 370, 230], radius=16, fill=DARK)
    d.rounded_rectangle([64, 34, 356, 216], radius=8, fill=WHITE)
    for i, (w_, col) in enumerate(((180, G), (120, (40, 70, 120)), (220, GL))):
        d.rounded_rectangle([84, 56 + i * 48, 84 + w_, 86 + i * 48], radius=8, fill=col)
    d.rounded_rectangle([10, 230, 410, 262], radius=14, fill=(200, 208, 218))
    return outline(img, 9)

def mobile():
    img = Image.new("RGBA", (200, 360), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, 190, 350], radius=30, fill=DARK)
    d.rounded_rectangle([22, 28, 178, 332], radius=20, fill=WHITE)
    for i, (w_, col) in enumerate(((110, G), (80, (40, 70, 120)), (120, GL), (90, G))):
        d.rounded_rectangle([40, 60 + i * 60, 40 + w_, 90 + i * 60], radius=8, fill=col)
    return outline(img, 9)

# ---------- S1: háček ----------
SLAM1 = 30
S1 = TextScene(105, BG, [Words("Kam jdou", 330, 3, 120), Words("*naše_peníze?*", 470, 12, 120),
                         Coins(14, 9),
                         Slam(FE.scaled(FE.ST_PLAIN, 820), W // 2, 0, SLAM1)],
               post=shake_post([SLAM1 + 5], BG))

# ---------- S2: moderní rozklikávací rozpočet, web i mobil ----------
S2 = TextScene(105, GL, [Words("Moderní", 330, 3, 110), Words("*rozklikávací*", 490, 10, 120), Words("rozpočet města.", 645, 18, 96),
                         Pop(laptop(), 380, 1060, 34, -5), Pop(mobile(), 760, 1060, 42, 6),
                         Words("Na webu i *v_mobilu.*", 1360, 54, 84)])

# ---------- S3: ukázka v telefonu ----------
REC = sorted(os.path.join(HERE, "roz_m", x) for x in os.listdir(os.path.join(HERE, "roz_m")))
SCR_W, SCR_H = 540, 1112
PH_W, PH_H = SCR_W + 36, SCR_H + 36
PH_CX, PH_TOP = 400, 420
_pm = Image.new("L", (SCR_W, SCR_H), 0)
ImageDraw.Draw(_pm).rounded_rectangle([0, 0, SCR_W - 1, SCR_H - 1], radius=54, fill=255)
PHONE = Image.new("RGBA", (PH_W + 80, PH_H + 90), (0, 0, 0, 0))
_s = Image.new("RGBA", PHONE.size, (0, 0, 0, 0))
ImageDraw.Draw(_s).rounded_rectangle([40, 60, PH_W + 40, PH_H + 60], radius=72, fill=(27, 38, 59, 90))
PHONE.alpha_composite(_s.filter(ImageFilter.GaussianBlur(22)))
ImageDraw.Draw(PHONE).rounded_rectangle([40, 40, PH_W + 40, PH_H + 40], radius=72, fill=DARK)
CAPS = [(0, "*Aktuální* data."), (107, "Vyberte *téma*"), (139, "Kolik a *na_co*"),
        (246, "Přepněte *rok*"), (300, "Porovnejte *roky*")]
caps = [(t + 8, Words(s, 230, t + 10, 62)) for t, s in CAPS]
ME_S3 = AS.ArmSticker(560)
SUB = Words("Ne jednou za rok ani za čtvrtletí.", 330, 18, 46)

class Demo:
    n = len(REC) + 15
    def render(self, f):
        c = Image.new("RGBA", (W, H), BG + (255,))
        p = ease_out_back(clamp(f / 14), 1.1)
        top = PH_TOP + (1 - p) * 1500
        x0 = PH_CX - PHONE.width // 2
        c.alpha_composite(PHONE, (x0, int(top) - 40))
        shot = Image.open(REC[min(max(0, f - 8), len(REC) - 1)]).convert("RGBA")
        c.paste(shot, (x0 + 40 + 18, int(top) + 18), _pm)
        cur = max([cw for t, cw in caps if t <= f] or [caps[0][1]], key=lambda w: w.at)
        cur.draw(c, f)
        if cur is caps[0][1]:
            SUB.draw(c, f)
        MePoint(890, 10, ME_S3).draw(c, f)
        c.alpha_composite(NOTE, (PH_CX - NOTE.width // 2, int(top) + PH_H + 34))
        return c
S3 = Demo()

# ---------- S4: nečekal jsem ----------
S4 = TextScene(100, BG, [Words("Nečekal jsem,", 640, 3, 110), Words("až to udělá *někdo_jiný.*", 780, 14, 70),
                         Words("Udělal jsem to", 1000, 44, 96), Words("*pro_vás.*", 1120, 54, 120)])

# ---------- S5: závěr ----------
ME_END = AS.ArmSticker(780)
S5 = TextScene(150, BG, [Words("Vyzkoušejte", 280, 3, 100), Words("*dobrasprava.cz/rozpocet*", 410, 10, 72),
                         El(text_img("Karel Krupička", 84, DARK, w="ExtraBold"), W // 2, 580, 26, dur=11),
                         MePoint(690, 34, ME_END),
                         Pop(LOGO.resize((int(LOGO.width * .85), int(LOGO.height * .85)), Image.LANCZOS), 225, 1200, 52, -6),
                         El(NOTE, W // 2, 690, 40, "rise")])

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

def coin_clink():
    n = int(0.25 * A.SR); t = A.t_(n)
    f0 = A.rng.uniform(2600, 3600)
    return (np.sin(2 * np.pi * f0 * t) + 0.6 * np.sin(2 * np.pi * f0 * 1.51 * t)) * np.exp(-t / 0.05)

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    out.add(0, A.seg_pop(total + .2, 0.55)[: int(total * SR)])
    for a in (3, 12):
        out.add(st[0] + a / FPS, K1.fx_pop(), 0.5)
    for j in range(9):
        out.add(st[0] + (24 + j * 4) / FPS, coin_clink(), 0.3)
    out.add(st[0] + (SLAM1 + 5) / FPS, A.fx_impact(), 0.9)
    for a in (3, 10, 18, 34, 42, 54):
        out.add(st[1] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[2], A.fx_whoosh(0.5), 0.6)
    for tt, _ in CAPS:
        out.add(st[2] + (tt + 2) / FPS, K1.fx_pop(), 0.5)
    for a in (3, 14, 44, 54):
        out.add(st[3] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[3] + 54 / FPS, A.fx_ding(), 0.6)
    for a in (3, 10, 26):
        out.add(st[4] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[4] + 34 / FPS, A.fx_whoosh(0.4), 0.5)
    out.add(st[4] + 52 / FPS, A.fx_impact(), 0.5)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fo = int(1.2 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

if __name__ == "__main__":
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "rozpocet2_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
