"""Reels na středu v3: připomenutí voleb postavené na Karlovi + Dobré správě. 1080x1920, 30 fps, se zvukem."""
import os, math, subprocess
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
from podzim import logo_sticker
from rozpocet2 import Pop
import rozpocet2 as RZ
import fv as FV

HERE = R.HERE
OUT = os.path.join(HERE, "streda_pripominka_v4.mp4")
LOGO = logo_sticker()
GREY = (110, 122, 140)

def pill(text, size=54):
    return text_img(text, size, DARK, w="ExtraBold", pill=WHITE, pad=(30, 14), radius=30)
def sub(text, size=50, col=GREY, w="SemiBold"):
    return text_img(text, size, col, w=w)

# ---------- jemné pozadí s hloubkou ----------
_bl = Image.new("RGBA", (W + 300, H + 300), (0, 0, 0, 0))
_d = ImageDraw.Draw(_bl)
for cx, cy, r, a in ((1000, 260, 430, 24), (120, 1060, 330, 16), (1020, 1500, 300, 14)):
    _d.ellipse([cx - r + 150, cy - r + 150, cx + r + 150, cy + r + 150], fill=G + (a,))
_bl = _bl.filter(ImageFilter.GaussianBlur(70))
def bg_fx(c, f):
    ox, oy = int(150 + 22 * math.sin(f * .02)), int(150 + 18 * math.cos(f * .017))
    c.alpha_composite(_bl.crop((ox, oy, ox + W, oy + H)))

def scene(n, els, post=None):
    return TextScene(n, BG, els, extra=bg_fx, post=post)

# ---------- S1: připomínka ----------
SL1 = 34
TAG = text_img("KOMUNÁLNÍ VOLBY", 38, GD, w="ExtraBold", pill=(226, 240, 222), pad=(30, 12), radius=26)
NAME_PILL = text_img("Karel Krupička", 50, WHITE, w="ExtraBold", pill=GD, pad=(26, 12), radius=24)
S1 = scene(110, [El(TAG, W // 2, 270, 2, "rise", dur=8),
                 Words("Už v *pátek*", 440, 6, 130), Words("volíme.", 595, 14, 150),
                 Pop(pill("pátek 14–22"), 295, 800, 26, -3), Pop(pill("sobota 8–14"), 785, 800, 32, 3),
                 El(sub("Stačí občanka. Zabere to pár minut.", 46), W // 2, 915, 42, "rise"),
                 Slam(FE.scaled(FE.ST_PLAIN, 1000), W // 2, 0, SL1),
                 Pop(NAME_PILL, 800, 1130, SL1 + 12, 5)],
           post=shake_post([SL1 + 5], BG))

# ---------- S2: finanční výbor ----------
SL2 = 30
JOKE = text_img("A pořád mě to baví.", 64, WHITE, w="ExtraBold", pill=G, pad=(42, 18), radius=34)
S2 = scene(125, [Words("Čtyři roky ve", 330, 3, 100), Words("*finančním_výboru.*", 460, 10, 104),
                 El(sub("Procházím, co jde do zastupitelstva,"), W // 2, 600, 18, "rise"),
                 El(sub("dřív, než se o tom hlasuje."), W // 2, 664, 23, "rise"),
                 Pop(JOKE, W // 2, 790, 64, -2),
                 Slam(FV.me_with_lupa(), W // 2, 0, SL2)],
           post=shake_post([SL2 + 5], BG))

# ---------- S3: rozpočet na klik ----------
LIVE = RZ.LIVE
class BigPhone(El):
    MINI, OFFSET = .72, 20
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 14), 1.1)
        ph = RZ.PHONE.copy()
        shot = Image.open(RZ.REC[min(k + self.OFFSET, len(RZ.REC) - 1)]).convert("RGBA")
        ph.paste(shot, (58, 58), RZ._pm)
        ph = ph.resize((int(ph.width * self.MINI), int(ph.height * self.MINI)), Image.LANCZOS).rotate(4, expand=True, resample=Image.BICUBIC)
        x, y = self.cx - ph.width / 2, self.cy - ph.height / 2 + (1 - p) * 1000
        c.alpha_composite(ph, (int(x), int(y)))
        if k > 18:
            lx, ly = int(self.cx - LIVE.width / 2), int(self.cy - ph.height / 2 - 30)
            c.alpha_composite(LIVE, (lx, ly))
            d = ImageDraw.Draw(c)
            a = 150 + int(105 * math.sin(f * .3))
            d.ellipse([lx + 34, ly + LIVE.height / 2 - 11, lx + 56, ly + LIVE.height / 2 + 11], fill=(220, 50, 50, a))

ROLE = "vedoucí týmu digitalizace a automatizace"
def avatar(d=124):
    face = FE.BASE.crop((360, 420, 820, 880)).resize((d, d), Image.LANCZOS)
    tile = Image.new("RGBA", (d, d), (226, 240, 222, 255)); tile.alpha_composite(face)
    m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).ellipse([0, 0, d - 1, d - 1], fill=255)
    out = Image.new("RGBA", (d + 12, d + 12), (0, 0, 0, 0))
    ImageDraw.Draw(out).ellipse([0, 0, d + 11, d + 11], fill=G)
    out.paste(tile, (6, 6), m)
    return out
def byline():
    w, h = 940, 164
    img = Image.new("RGBA", (w + 60, h + 80), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 44, 30 + w, 44 + h], radius=44, fill=(27, 38, 59, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([30, 30, 30 + w, 30 + h], radius=44, fill=WHITE)
    av = avatar(); img.alpha_composite(av, (30 + 24, 30 + (h - av.height) // 2))
    d.text((30 + 190, 30 + 60), "Karel Krupička", font=font(54, "ExtraBold"), fill=DARK, anchor="lm")
    d.text((30 + 190, 30 + 116), ROLE, font=font(31, "SemiBold"), fill=GREY, anchor="lm")
    return img
BYLINE = byline()
S3 = scene(110, [Words("Kam jdou", 270, 3, 100), Words("peníze města?", 390, 8, 100), Words("*Na_klik.*", 525, 14, 130),
                 El(sub("Interaktivní rozpočet. Žádný Excel."), W // 2, 640, 20, "rise"),
                 El(sub("dobrasprava.cz/rozpocet", 52, DARK, "ExtraBold"), W // 2, 704, 26, "rise"),
                 Pop(BYLINE, W // 2, 850, 34, 0),
                 BigPhone(None, 540, 1460, 14)])

# ---------- S4: chceme město ----------
CARD_W, CARD_H = 920, 150
def card(text, hl=False):
    img = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, CARD_W - 1, CARD_H - 1], radius=38, fill=G if hl else WHITE)
    if not hl:
        d.rounded_rectangle([0, 0, 16, CARD_H - 1], radius=8, fill=G)
    ck = FV.check_img(72)
    img.alpha_composite(ck, (46, (CARD_H - ck.height) // 2))
    size = 58
    while font(size, "ExtraBold").getlength(text) > CARD_W - 152 - 36:
        size -= 2
    d.text((152, CARD_H / 2), text, font=font(size, "ExtraBold"), fill=WHITE if hl else DARK, anchor="lm")
    return outline(img, 6)

HEADS = ["kde se dobře žije", "pro všechny generace", "které komunikuje", "které hospodaří s rozumem"]
class Slide(El):
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

s4 = [Words("Chceme *město,*", 540, 3, 108)]
for i, t in enumerate(HEADS):
    s4.append(Slide(card(t, i == 3), W // 2, 790 + i * 178, 14 + i * 9))
S4 = scene(120, s4)

# ---------- S5: závěr ----------
SL5 = 44
BIG_LOGO = LOGO.resize((int(LOGO.width * .85), int(LOGO.height * .85)), Image.LANCZOS)
def number_card():
    w, h = 900, 240
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=50, fill=WHITE)
    d.ellipse([34, 34, 34 + 172, 34 + 172], fill=G)
    d.text((34 + 86, 34 + 92), "3", font=font(150, "ExtraBold"), fill=WHITE, anchor="mm")
    d.text((250, 92), "Kandidátka č. 3", font=font(74, "ExtraBold"), fill=DARK, anchor="lm")
    d.text((250, 166), "Hledejte na hlasovacím lístku", font=font(40, "SemiBold"), fill=GREY, anchor="lm")
    return outline(img, 8)
S5 = scene(170, [Words("Dejte hlas", 260, 3, 106), Words("*Dobré_správě.*", 395, 10, 116),
                 FV.Stamp(number_card(), W // 2, 640, 20, rot=-2),
                 El(text_img("dobrasprava.cz", 62, GD, w="ExtraBold"), W // 2, 835, 44, "rise"),
                 Slam(FE.scaled(FE.ST_PLAIN, 860), W // 2, 0, SL5),
                 Pop(BIG_LOGO, W // 2, 1030, SL5 + 14, -4)],
           post=shake_post([24, SL5 + 5], BG))

SCENES = [S1, S2, S4, S5]
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
    for a in (2, 6, 14, 26, 32, 42, SL1 + 12):
        out.add(st[0] + a / FPS, K1.fx_pop(), 0.45)
    out.add(st[0] + (SL1 + 5) / FPS, A.fx_impact(), 0.9)
    for a in (3, 10, 18, 23, 64):
        out.add(st[1] + a / FPS, K1.fx_pop(), 0.45)
    out.add(st[1] + 64 / FPS, A.fx_ding(), 0.5)
    out.add(st[1] + (SL2 + 5) / FPS, A.fx_impact(), 0.8)
    out.add(st[2] + 3 / FPS, K1.fx_pop(), 0.5)
    for i in range(4):
        out.add(st[2] + (14 + i * 9) / FPS, A.fx_whoosh(0.2), 0.35)
        out.add(st[2] + (18 + i * 9) / FPS, K1.fx_pop(), 0.45)
    out.add(st[2] + 48 / FPS, A.fx_ding(), 0.5)
    for a in (3, 10, 44):
        out.add(st[3] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[3] + 24 / FPS, A.fx_impact(), 0.9)
    out.add(st[3] + 26 / FPS, A.fx_ding(), 0.6)
    out.add(st[3] + (SL5 + 5) / FPS, A.fx_impact(), 0.9)
    out.add(st[3] + (SL5 + 14) / FPS, K1.fx_pop(), 0.5)
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
            SCENES[int(args[i])].render(int(args[i + 1])).convert("RGB").save(os.path.join(HERE, "hlas", f"u{args[i]}_{args[i+1]}.jpg"))
        sys.exit()
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "streda4_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
