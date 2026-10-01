"""Story: přehledný klikací rozpočet Starého Plzence na dobrasprava.cz. 1080x1920, 30 fps, se zvukem."""
import os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import audio as A
import kino as K1
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, El, TextScene)
from kino2 import Words
from kino import outline, shake_post
import armsticker as AS
from podzim import logo_sticker

HERE = R.HERE
OUT = os.path.join(HERE, "rozpocet_story.mp4")
LOGO = logo_sticker()
ME = AS.ArmSticker(600)

class MePoint(El):
    """Ukazující samolepka: vyjede zespodu, ruka se pohupuje."""
    def __init__(self, cx, at, sticker=ME, slide=True):
        super().__init__(None, cx, 0, at); self.st, self.slide = sticker, slide
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        dy = (1 - ease_out_back(clamp(k / 12), 1.3)) * 1000 if self.slide else 0
        a = -8 + 7 * math.sin(f * .22)
        img = self.st.image(a)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(H - img.height + 30 + dy)))

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
            img = img.rotate(self.rot * p, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

# ---------- S1: úvod ----------
S1 = TextScene(90, BG, [Words("Rozpočet", 330, 3, 120), Words("Starého Plzence", 460, 10, 100),
                        Words("*přehledně* a na klik.", 600, 20, 70),
                        MePoint(760, 26)])

# ---------- S2: ukázka z webu ----------
SEG_DIR = os.path.join(HERE, "roz_seg")
SEGS = [sorted(os.path.join(SEG_DIR, str(i), x) for x in os.listdir(os.path.join(SEG_DIR, str(i)))) for i in range(6)]
CAPS = ["Kolik město *má_a_utrácí*", "Kam jde *každých_100_Kč*", "Klikněte a *rozbalte*",
        "Kam jdou *investice*", "*Podrobný* rozpočet", "I *minulé_roky*"]
CARD_W, CARD_H = 880, 1152
CARD_X, CARD_Y = (W - CARD_W) // 2, 330
_mask = Image.new("L", (CARD_W, CARD_H), 0)
ImageDraw.Draw(_mask).rounded_rectangle([0, 0, CARD_W - 1, CARD_H - 1], radius=40, fill=255)
_frame = Image.new("RGBA", (CARD_W + 60, CARD_H + 70), (0, 0, 0, 0))
_sh = Image.new("RGBA", _frame.size, (0, 0, 0, 0))
ImageDraw.Draw(_sh).rounded_rectangle([30, 44, CARD_W + 30, CARD_H + 44], radius=44, fill=(27, 38, 59, 70))
_frame.alpha_composite(_sh.filter(ImageFilter.GaussianBlur(18)))
ImageDraw.Draw(_frame).rounded_rectangle([18, 18, CARD_W + 42, CARD_H + 42], radius=52, fill=WHITE)
caps = [Words(t, 220, 0, 64) for t in CAPS]
ME2 = AS.ArmSticker(520)

class Demo:
    def __init__(self):
        self.starts, t = [], 0
        for s in SEGS:
            self.starts.append(t); t += len(s)
        self.n = t
    def load(self, i, k):
        im = Image.open(SEGS[i][k]).convert("RGBA")
        if i == 5:   # skrýt pracovní záhlaví stránky nahoře
            out = Image.new("RGBA", im.size, (248, 249, 250, 255))
            out.paste(im.crop((0, 230, im.width, im.height)), (0, 0))
            im = out
        return im
    def render(self, f):
        c = Image.new("RGBA", (W, H), BG + (255,))
        i = max(j for j, s in enumerate(self.starts) if s <= f)
        k = f - self.starts[i]
        p = ease_out_back(clamp(f / 12), 1.1)
        y = CARD_Y + (1 - p) * 1400
        c.alpha_composite(_frame, (CARD_X - 30, int(y) - 30))
        shot = self.load(i, min(k, len(SEGS[i]) - 1))
        if k < 4 and i > 0:   # krátké prolnutí mezi ukázkami
            prev = self.load(i - 1, len(SEGS[i - 1]) - 1)
            shot = Image.blend(prev, shot, (k + 1) / 5)
        c.paste(shot, (CARD_X, int(y)), _mask)
        # popisek: slova vyskočí na začátku každé ukázky
        cp = caps[i]; cp.at = self.starts[i] + 2
        cp.draw(c, f)
        MePoint(850, 6, ME2).draw(c, f)
        # postup ukázek (tečky)
        d = ImageDraw.Draw(c)
        for j in range(len(SEGS)):
            x = W / 2 + (j - 2.5) * 34
            d.ellipse([x - 9, 1525, x + 9, 1543], fill=G if j == i else (200, 210, 200))
        return c
S2 = Demo()

# ---------- S3: nečekal jsem ----------
S3 = TextScene(100, BG, [Words("Nečekal jsem,", 640, 3, 110), Words("až to udělá *někdo_jiný.*", 780, 14, 70),
                         Words("Udělal jsem to", 1000, 44, 96), Words("*pro_vás.*", 1120, 54, 120)])

# ---------- S4: dobrasprava.cz ----------
S4 = TextScene(130, BG, [Words("Mrkněte na", 300, 3, 100), Words("*dobrasprava.cz*", 430, 10, 110),
                         El(text_img("Karel Krupička", 88, DARK, w="ExtraBold"), W // 2, 600, 26, dur=11),
                         MePoint(690, 34, AS.ArmSticker(780)),
                         Pop(LOGO.resize((int(LOGO.width * .85), int(LOGO.height * .85)), Image.LANCZOS), 225, 1200, 52, -6)])

SCENES = [S1, S2, S3, S4]
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
    for a in (3, 10, 20):
        out.add(st[0] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[0] + 26 / FPS, A.fx_whoosh(0.4), 0.5)
    for s in S2.starts:
        out.add(st[1] + (s + 2) / FPS, K1.fx_pop(), 0.5)
        out.add(st[1] + (s + 2) / FPS, A.hat(), 0.4)
    for a in (3, 14, 44, 54):
        out.add(st[2] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[2] + 54 / FPS, A.fx_ding(), 0.6)
    for a in (3, 10, 26):
        out.add(st[3] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[3] + 34 / FPS, A.fx_whoosh(0.4), 0.5)
    out.add(st[3] + 52 / FPS, A.fx_impact(), 0.5)
    out.add(st[3] + 52 / FPS, K1.fx_pop(), 0.6)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fo = int(1.0 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

if __name__ == "__main__":
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "rozpocet_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
