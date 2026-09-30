"""Podzimní kino v Lidovém domě – hlasování o filmu. Reels 1080x1920, 30 fps, hudební podkres pro voiceover."""
import os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import audio as A
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, rect_img, El, TextScene)
from kino2 import Words
from kino import outline, NIGHT

HERE = R.HERE
OUT = os.path.join(HERE, "podzimni_kino.mp4")
OCHRE, RUST = (232, 170, 60), (196, 106, 52)
FILMS = ["Kulový blesk", "Obecná škola", "Slavnosti sněženek"]

# ---------- samolepky ----------
def logo_sticker():
    w, h = 400, 250
    img = Image.new("RGBA", (w + 40, h + 50), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 34, w + 20, h + 34], radius=34, fill=(27, 38, 59, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=34, fill=WHITE)
    d.polygon([(w * .87, h), (w, h * .8), (w, h), ], fill=(0, 0, 0, 0))
    d.polygon([(w * .87, h), (w, h * .8), (w * .87, h * .8)], fill=(214, 220, 228))   # odlepený roh
    f = font(84, "ExtraBold")
    d.text((36, 26), "dobrá", font=f, fill=DARK)
    d.text((36, 118), "s", font=f, fill=G)
    d.text((36 + f.getlength("s"), 118), "práva", font=f, fill=DARK)
    img.alpha_composite(card, (20, 20))
    return img

def opus_sticker():
    w, h = 540, 230
    img = Image.new("RGBA", (w + 40, h + 50), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 34, w + 20, h + 34], radius=34, fill=(0, 0, 0, 80))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([20, 20, w + 20, h + 20], radius=34, fill=DARK)
    d.text((56, 44), "spolek", font=font(40, "SemiBold"), fill=GL)
    d.text((52, 92), "O.P.U.S.", font=font(104, "ExtraBold"), fill=WHITE)
    d.rounded_rectangle([56, 214, 180, 222], radius=4, fill=OCHRE)
    return outline(img, 9)

LOGO = logo_sticker()
OPUS = opus_sticker()
TOMAS = Image.open(os.path.join(HERE, "tomas_sticker.png")).convert("RGBA")
def scaled(im, w):
    return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)

class Slap(El):
    """Samolepka plácne ze zvětšení a zůstane lehce natočená, pak se jemně houpe."""
    def __init__(self, img, cx, cy, at, rot=-6):
        super().__init__(img, cx, cy, at); self.rot = rot
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out(clamp((k + 1) / 7))
        s = 2.0 - 1.0 * p
        wob = 1.5 * math.sin(k * .12) if k > 7 else 0
        img = self.img.resize((int(self.img.width * s), int(self.img.height * s)), Image.BILINEAR)
        img = img.rotate(self.rot * p + wob, expand=True, resample=Image.BICUBIC)
        a = clamp(p * 1.6)
        if a < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

class Rise(El):
    """Osoba (samolepka) vyjede zespodu a usadí se u spodního okraje."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        dy = (1 - ease_out_back(clamp(k / 14), 1.2)) * 1000
        wob = 1.2 * math.sin(k * .09)
        img = self.img.rotate(wob, resample=Image.BICUBIC, center=(self.img.width / 2, self.img.height))
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(H - img.height + 30 + dy)))

# ---------- atmosféra: zrno, vinětace, listí ----------
_rng = np.random.default_rng(5)
GRAIN = []
for i in range(4):
    n = _rng.integers(0, 255, (H // 3, W // 3), dtype=np.uint8)
    a = Image.fromarray(n).resize((W, H), Image.NEAREST)
    g = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    g.putalpha(a.point(lambda v: 12 if v > 238 else 0))
    GRAIN.append(g)
VIG = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_vd = np.zeros((H, W), np.float32)
yy, xx = np.mgrid[0:H, 0:W]
_vd = np.clip((np.sqrt(((xx - W / 2) / (W * .75)) ** 2 + ((yy - H / 2) / (H * .7)) ** 2) - .45) * 1.6, 0, 1)
VIG.putalpha(Image.fromarray((_vd * 170).astype(np.uint8)))

def leaf_img(col, s=70):
    img = Image.new("RGBA", (s * 2, s * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(s, 8), (s * 1.55, s * .7), (s * 1.45, s * 1.35), (s, s * 1.9), (s * .55, s * 1.35), (s * .45, s * .7)], fill=col)
    d.line([(s, 20), (s, s * 1.9)], fill=tuple(max(0, v - 50) for v in col), width=4)
    return img
LEAVES = [leaf_img(c) for c in (OCHRE, RUST, G, GD, (220, 140, 50))]

class Leaves(El):
    def __init__(self, seed=1, n=16, alpha=1.0):
        super().__init__(None, 0, 0, 0)
        r = random.Random(seed)
        self.l = [(r.choice(LEAVES), r.uniform(0, W), r.uniform(-H, H), r.uniform(2.5, 5), r.uniform(0, 6), r.uniform(.4, 1.0))
                  for _ in range(n)]
        self.alpha = alpha
    def draw(self, c, f):
        for img, x, y0, v, ph, sc in self.l:
            y = (y0 + v * f) % (H + 300) - 150
            x2 = x + 60 * math.sin(f * .04 + ph)
            rot = 50 * math.sin(f * .05 + ph)
            w = max(.25, abs(math.cos(f * .06 + ph)))
            im = img.resize((max(4, int(img.width * sc * w)), int(img.height * sc)), Image.BILINEAR).rotate(rot, expand=True)
            c.alpha_composite(im, (int(x2 - im.width / 2), int(y - im.height / 2)))

class Artsy:
    """Obal scény: tmavé pozadí, světelný závoj, listí, zrno, vinětace."""
    def __init__(self, n, els, bg=NIGHT, leaves=False, glow=(0.5, 0.25)):
        self.n, self.els, self.bg, self.leaves, self.glow = n, els, bg, Leaves(7, 14) if leaves else None, glow
    def render(self, f):
        c = Image.new("RGBA", (W, H), self.bg + (255,))
        q = 8
        gl = Image.new("RGBA", (W // q, H // q), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gl)
        gx = (W * self.glow[0] + 160 * math.sin(f * .02)) / q
        gy = (H * self.glow[1] + 120 * math.cos(f * .017)) / q
        gd.ellipse([gx - 88, gy - 88, gx + 88, gy + 88], fill=GD + (90,))
        gd.ellipse([W / q - gx - 62, H / q - gy - 50, W / q - gx + 62, H / q - gy + 75], fill=(120, 80, 30, 60))
        c.alpha_composite(gl.filter(ImageFilter.GaussianBlur(20)).resize((W, H), Image.BILINEAR))
        if self.leaves:
            self.leaves.draw(c, f)
        for e in self.els:
            e.draw(c, f)
        c.alpha_composite(VIG)
        c.alpha_composite(GRAIN[(f // 3) % 4])
        return c

# ---------- S1: Podzimní kino v malém sále Lidového domu ----------
class Hall(El):
    """Malý sál: plátno se světlem a řady sedadel zezadu."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out(clamp(k / 18))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        fl = int(200 + 30 * math.sin(f * .8) + 10 * math.sin(f * 2.3))
        sx0, sy0, sx1, sy1 = 190, 1180, 890, 1560
        for gi in range(6, 0, -1):
            m = gi * 14
            d.rounded_rectangle([sx0 - m, sy0 - m, sx1 + m, sy1 + m], radius=m, fill=(fl, fl, 230, int(14 * p)))
        d.rectangle([sx0, sy0, sx1, sy1], fill=(fl, fl, 238, int(255 * p)))
        d.text(((sx0 + sx1) / 2, (sy0 + sy1) / 2), "?", font=font(220, "ExtraBold"), fill=(40, 48, 70, int(200 * p)), anchor="mm")
        for row in range(3):
            y = 1640 + row * 110
            for i in range(9):
                x = 60 + i * 120 + (row % 2) * 60
                col = (12, 16, 26, int(255 * p))
                d.ellipse([x - 34, y - 60, x + 34, y + 8], fill=col)
                d.rounded_rectangle([x - 56, y, x + 56, y + 140], radius=26, fill=col)
        c.alpha_composite(layer, (0, int((1 - p) * 200)))

S1 = Artsy(150, [Words("Těšíme se na", 330, 4, 84), Words("*podzimní* kino!", 460, 12, 108),
                 Words("tentokrát v malém sále", 690, 58, 72), Words("Lidového domu", 800, 70, 88),
                 Hall(None, 0, 0, 30)])

# ---------- S2: Film opět vybíráte vy ----------
def film_card(title, w=860, h=300):
    img = Image.new("RGBA", (w + 40, h + 50), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 34, w + 20, h + 34], radius=26, fill=(0, 0, 0, 90))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([20, 20, w + 20, h + 20], radius=26, fill=WHITE)
    d.text((70, 62), title, font=font(70, "ExtraBold"), fill=DARK)
    d.line([(20, 175), (w + 20, 175)], fill=(226, 231, 238), width=3)
    d.rounded_rectangle([70, 205, w - 30, 285], radius=14, fill=G)
    d.text(((w + 40) / 2, 245), "Hlasovat", font=font(46, "ExtraBold"), fill=WHITE, anchor="mm")
    return outline(img, 8)

class Fly(El):
    def __init__(self, img, cx, cy, at, rot, side):
        super().__init__(img, cx, cy, at); self.rot, self.side = rot, side
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 13), 1.1)
        x = self.cx + (1 - p) * 1200 * self.side
        img = self.img.rotate(self.rot * p + (1 - p) * 25 * self.side, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(x - img.width / 2), int(self.cy - img.height / 2)))

S2 = Artsy(95, [Words("Film opět", 330, 3, 100), Words("vybíráte *vy.*", 460, 10, 110),
                Fly(film_card(FILMS[0]), W // 2, 780, 22, 2.5, 1), Fly(film_card(FILMS[1]), W // 2, 1110, 30, -2, -1),
                Fly(film_card(FILMS[2]), W // 2, 1440, 38, 1.5, 1)], glow=(.3, .6))

# ---------- S3: hlasujeme u nás na webu ----------
def phone_page():
    pw, ph = 600, 1180
    img = Image.new("RGBA", (pw + 60, ph + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 46, pw + 30, ph + 46], radius=80, fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([30, 30, pw + 30, ph + 30], radius=80, fill=DARK)
    scr = Image.new("RGBA", (pw - 36, ph - 36), (246, 248, 250, 255))
    sd = ImageDraw.Draw(scr)
    sw = scr.width
    sd.rectangle([0, 0, sw, 150], fill=WHITE)
    f = font(44, "ExtraBold")
    sd.text((40, 52), "dobrá", font=f, fill=DARK)
    sd.text((40, 96), "s", font=f, fill=G); sd.text((40 + f.getlength("s"), 96), "práva", font=f, fill=DARK)
    sd.line([(0, 150), (sw, 150)], fill=(226, 231, 238), width=2)
    sd.text((40, 185), "Podzimní kino", font=font(46, "ExtraBold"), fill=DARK)
    ft = font(28, "SemiBold")
    for i, line in enumerate(["Co se bude promítat? O tom nám", "můžete pomoci rozhodnout právě vy."]):
        sd.text((40, 252 + i * 40), line, font=ft, fill=(100, 112, 130))
    for i, t in enumerate(FILMS):
        y = 360 + i * 245
        sd.rounded_rectangle([30, y, sw - 30, y + 215], radius=18, fill=WHITE, outline=(226, 231, 238), width=2)
        sd.text((60, y + 30), t, font=font(38, "ExtraBold"), fill=DARK)
        sd.rounded_rectangle([60, y + 120, sw - 60, y + 180], radius=10, fill=G)
        sd.text((sw / 2, y + 150), "Hlasovat", font=font(32, "ExtraBold"), fill=WHITE, anchor="mm")
    m = Image.new("L", scr.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.width - 1, scr.height - 1], radius=62, fill=255)
    img.paste(scr, (48, 48), m)
    d.rounded_rectangle([30 + pw / 2 - 70, 58, 30 + pw / 2 + 70, 88], radius=15, fill=DARK)
    return img
PHONE = phone_page()
PH_X, PH_Y = W // 2 - 20, 1010
TAP_AT = 70

class Phone(El):
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 14), 1.1)
        y = self.cy + (1 - p) * 1200
        img = self.img.copy()
        # klepnutí na tlačítko prvního filmu
        t = f - TAP_AT
        if t >= 0:
            d = ImageDraw.Draw(img)
            bx, by = 48 + (PHONE.width - 96) / 2 - 20, 48 + 360 + 150
            r = 30 + t * 9
            if t < 14:
                d.ellipse([bx - r, by - r, bx + r, by + r], outline=(255, 255, 255, int(220 * (1 - t / 14))), width=8)
            if 4 < t < 60:   # neutrální potvrzení (bez zvýraznění konkrétního filmu)
                a = clamp((t - 4) / 5) * clamp((60 - t) / 8)
                tw, th = 360, 70
                tx, ty = (PHONE.width - tw) / 2, 48 + 175
                d.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=35, fill=DARK + (int(235 * a),))
                d.text((tx + tw / 2, ty + th / 2), "Díky za hlas!", font=font(34, "ExtraBold"), fill=(255, 255, 255, int(255 * a)), anchor="mm")
        img = img.rotate(-3 * p, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(y - img.height / 2)))

class Finger(El):
    """Kurzor-prst, který přijede a klepne."""
    def draw(self, c, f):
        k = f - (TAP_AT - 16)
        if k < 0 or k > 34:
            return
        tx, ty = PH_X - PHONE.width / 2 + 48 + (PHONE.width - 96) / 2 - 10, PH_Y - PHONE.height / 2 + 48 + 360 + 175
        p = ease_in_out(clamp(k / 14))
        x = tx + (1 - p) * 300; y = ty + (1 - p) * 350
        press = 0.9 if 14 <= k <= 18 else 1.0
        a = clamp((34 - k) / 6)
        r = 44 * press
        d = ImageDraw.Draw(c)
        d.ellipse([x - r - 8, y - r - 8, x + r + 8, y + r + 8], fill=(255, 255, 255, int(255 * a)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=G + (int(255 * a),))

S3 = Artsy(165, [Words("Hlasujeme", 250, 3, 100), Words("u nás *na_webu.*", 375, 10, 100),
                 Phone(PHONE, PH_X, PH_Y, 16), Finger(None, 0, 0, 0),
                 Slap(LOGO, 850, 1560, 100, rot=8),
                 Words("*dobrasprava.cz*", 1760, 118, 88)], glow=(.7, .5))

# ---------- S4: do 14 dnů, spolek O.P.U.S. ----------
class Days(El):
    """Velké „14“ s kalendářními dlaždicemi dnů, které se odškrtávají."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        d = ImageDraw.Draw(c)
        for i in range(14):
            p = clamp((k - i * 2) / 8)
            if p <= 0:
                continue
            col, row = i % 7, i // 7
            x = 100 + col * 128 + 60; y = 820 + row * 150
            s = 0.4 + 0.6 * ease_out_back(p)
            w2, h2 = 50 * s, 60 * s
            d.rounded_rectangle([x - w2, y - h2, x + w2, y + h2], radius=int(14 * s), fill=WHITE)
            d.rectangle([x - w2, y - h2, x + w2, y - h2 + 26 * s], fill=G)
            d.text((x, y + 12 * s), str(i + 1), font=font(max(10, int(46 * s)), "ExtraBold"), fill=DARK, anchor="mm")

S4 = Artsy(195, [Words("Vítězný film promítneme", 300, 3, 76), Words("do *14_dnů*", 430, 12, 120),
                 Days(None, 0, 0, 22),
                 Words("od převzetí Lidového domu", 1190, 70, 70), Words("spolkem", 1300, 84, 70),
                 Slap(OPUS, W // 2, 1520, 96, rot=-5)], glow=(.4, .35))

# ---------- S5: zveme vás společně ----------
S5 = Artsy(115, [Words("Zveme vás společně", 290, 3, 84), Words("s *Dobrou_správou.*", 410, 12, 96),
                 Rise(scaled(TOMAS, 860), W // 2 - 40, 0, 20),
                 Slap(LOGO, 830, 720, 44, rot=7), Slap(scaled(OPUS, 400), 250, 760, 54, rot=-8)], glow=(.5, .7))

# ---------- S6: Tak který film to bude? ----------
class Titles(El):
    """Názvy filmů se střídají jako na promítačce, pak se ukážou všechny tři."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        d = ImageDraw.Draw(c)
        x0, y0, x1, y1 = 90, 700, 990, 1120
        fl = 215 + int(25 * math.sin(f * 1.3))
        d.rectangle([x0, y0, x1, y1], fill=(fl, fl, 236))
        d.rectangle([x0, y0, x1, y1], outline=WHITE, width=8)
        if k < 48:
            t = FILMS[(k // 8) % 3]
            d.text(((x0 + x1) / 2, (y0 + y1) / 2), t, font=font(78, "ExtraBold"), fill=DARK, anchor="mm")
        else:
            d.text(((x0 + x1) / 2, (y0 + y1) / 2), "?", font=font(300, "ExtraBold"), fill=GD, anchor="mm")
        for i in range(3):   # „promítací“ tečky
            cx = (x0 + x1) / 2 - 60 + i * 60
            on = (k // 6) % 3 == i
            d.ellipse([cx - 12, y1 + 40, cx + 12, y1 + 64], fill=G if on else (80, 90, 110))

S6 = Artsy(150, [Words("Tak který film", 360, 3, 100), Words("*to_bude?*", 490, 12, 120),
                 Titles(None, 0, 0, 20),
                 Words("Hlasujte na", 1330, 70, 76), Words("*dobrasprava.cz*", 1450, 78, 96),
                 Slap(scaled(LOGO, 330), 830, 1690, 96, rot=7), Slap(scaled(OPUS, 360), 260, 1700, 104, rot=-6)],
            glow=(.5, .45))

SCENES = [S1, S2, S3, S4, S5, S6]

def frames():
    TRX = 10
    prev_last = None
    for i, sc in enumerate(SCENES):
        for f in range(sc.n):
            cur = sc.render(f)
            if i and f < TRX:   # prolnutí se zábleskem
                a = (f + 1) / (TRX + 1)
                cur = Image.blend(prev_last, cur, a)
                if f < 4:
                    cur.alpha_composite(Image.new("RGBA", (W, H), (255, 245, 225, int(60 * (1 - f / 4)))))
            yield cur.convert("RGB")
        prev_last = sc.render(sc.n - 1)

# ---------- zvuk: klidný podkres pod voiceover ----------
def pad_note(freqs, dur):
    x = sum(A.osc("saw", f, dur) + A.osc("saw", f * 1.005, dur) for f in freqs)
    x = A.lp(x, 900)
    n = len(x); e = np.minimum(1, np.arange(n) / (0.6 * A.SR)) * np.minimum(1, (n - np.arange(n)) / (0.8 * A.SR))
    return x * e * 0.08

def e_piano(f, dur=1.2):
    n = int(dur * A.SR); t = A.t_(n)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)) * np.exp(-t / 0.5)

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    b = 60 / 84
    prog = [("A2", "min"), ("F2", "maj"), ("C3", "maj"), ("G2", "maj")]
    nbar = int(total / (4 * b)) + 1
    for k in range(nbar):
        root, kind = prog[k % 4]
        r = A.m(root)
        cs = A.chord(r + 12, kind)
        out.add(k * 4 * b, pad_note(cs, 4 * b + .5), 1.0)
        out.add(k * 4 * b, A.sub(A.mf(r - 12), 4 * b * .95) * 0.5, 0.3)
        arp = [cs[0] * 2, cs[1] * 2, cs[2] * 2, cs[1] * 2]
        for j in range(8):
            out.add(k * 4 * b + j * b / 2, e_piano(arp[j % 4], 1.0), 0.12)
        for j in range(4):
            out.add(k * 4 * b + j * b, A.kick(0.5), 0.12)
            out.add(k * 4 * b + j * b + b / 2, A.hat(), 0.08)
    # projektor na začátku
    for j in range(int(2 * 14)):
        out.add(j / 14, A.hat(), 0.12)
    import kino as K1
    for sc_i, at in ((2, 100), (3, 96), (4, 44), (4, 54), (5, 96), (5, 104)):
        out.add(st[sc_i] + at / FPS, A.fx_impact(), 0.35)
        out.add(st[sc_i] + at / FPS, K1.fx_pop(), 0.4)
    for at in (22, 30, 38):
        out.add(st[1] + at / FPS - .1, A.fx_whoosh(0.3), 0.35)
    out.add(st[2] + TAP_AT / FPS, K1.fx_pop(), 0.5)
    out.add(st[2] + (TAP_AT + 5) / FPS, A.fx_ding(), 0.4)
    out.add(st[4] + 20 / FPS, A.fx_whoosh(0.5), 0.4)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fi = int(0.8 * SR); y[:fi] *= np.linspace(0, 1, fi)
    fo = int(1.5 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.5    # tišší podkres, aby byl slyšet hlas
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

if __name__ == "__main__":
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    st = 0
    for i, s in enumerate(SCENES):
        print(f"scéna {i + 1}: {st / FPS:5.1f} s – {(st + s.n) / FPS:5.1f} s"); st += s.n
    AUD = os.path.join(HERE, "podzim_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
