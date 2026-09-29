"""Finanční výbor – reels 1080x1920, 30 fps, se zvukem."""
import os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import festival as FE
import audio as A
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, rect_img, El, TextScene, Slam)

HERE = R.HERE
OUT = os.path.join(HERE, "financni_vybor.mp4")
GREY = (96, 108, 128)

def card(w, h, fill=WHITE, r=22, shadow=40):
    img = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 28, w + 20, h + 28], radius=r, fill=(27, 38, 59, shadow))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(img).rounded_rectangle([20, 20, w + 20, h + 20], radius=r, fill=fill)
    return img

class Stamp(El):
    """Razítko: dopadne ze zvětšení a lehce se natočí."""
    def __init__(self, img, cx, cy, at, rot=-6):
        super().__init__(img, cx, cy, at); self.rot = rot
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out(clamp((k + 1) / 6))
        s = 2.3 - 1.3 * p
        a = clamp(p * 1.5)
        img = self.img.resize((int(self.img.width * s), int(self.img.height * s)), Image.BILINEAR)
        img = img.rotate(self.rot * p, expand=True, resample=Image.BICUBIC)
        if a < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

def outline(img, px=8, col=WHITE):
    a = img.getchannel("A").filter(ImageFilter.MaxFilter(px * 2 + 1))
    out = Image.new("RGBA", img.size, col + (0,)); out.putalpha(a); out.alpha_composite(img)
    return out

GOLD, GOLD_D, GOLD_T = (244, 194, 66), (214, 160, 40), (150, 100, 20)
def coin_img(s=130):
    img = Image.new("RGBA", (s + 30, s + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([15, 15, 15 + s, 15 + s], fill=GOLD_D)
    d.ellipse([23, 23, 7 + s, 7 + s], fill=GOLD)
    d.ellipse([33, 33, s - 3, s - 3], outline=GOLD_D, width=4)
    d.text((15 + s / 2, 15 + s / 2), "Kč", font=font(int(s * .36), "ExtraBold"), fill=GOLD_T, anchor="mm")
    return outline(img, 7)
COIN = coin_img()

class CoinRain(El):
    """Padající mince (samolepky), které se točí."""
    def __init__(self, at, n=14, seed=1, x0=60, x1=1020, y_end=H + 200, dur=70):
        super().__init__(COIN, 0, 0, at)
        r = random.Random(seed)
        self.coins = [(r.uniform(x0, x1), at + r.uniform(0, dur * .6), r.uniform(9, 16), r.uniform(.12, .25),
                       r.uniform(0, 6), r.uniform(.6, 1.1), r.uniform(-25, 25)) for _ in range(n)]
    def draw(self, c, f):
        for x, t0, v, sp, ph, sc, rot in self.coins:
            k = f - t0
            if k < 0:
                continue
            y = -160 + v * k + 0.35 * k * k
            if y > H + 150:
                continue
            w = max(.15, abs(math.cos(ph + sp * k)))
            img = self.img.resize((max(2, int(self.img.width * sc * w)), int(self.img.height * sc)), Image.BILINEAR)
            img = img.rotate(rot + k * 2, expand=True, resample=Image.BILINEAR)
            c.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))

def shake_post(times, bgc, amp=14):
    def post(c, f):
        for t in times:
            k = f - t
            if 0 <= k <= 9:
                dd = math.exp(-k / 3)
                out = Image.new("RGBA", (W, H), bgc + (255,))
                out.paste(c, (int(amp * math.sin(k * 2.7) * dd), int(amp * 0.7 * math.cos(k * 3.1) * dd)))
                return out
        return c
    return post

# ---------- S1: Jsem členem finančního výboru ve Starém Plzenci. 4 roky. ----------
STAMP1, ME1 = 70, 34
S1 = TextScene(165, BG, [El(text_img("Jsem členem", 104, DARK), W // 2, 300, 3),
                         El(text_img("finančního výboru", 104, DARK, w="ExtraBold"), W // 2, 420, 12),
                         El(text_img("ve Starém Plzenci.", 84, WHITE, w="ExtraBold", pill=G, pad=(40, 14)), W // 2, 545, 22),
                         CoinRain(60, n=12, seed=3, dur=90),
                         Slam(FE.scaled(FE.ST_PLAIN, 760), W // 2, 0, ME1),
                         Stamp(outline(text_img("4 ROKY", 130, WHITE, w="ExtraBold", pill=GD, pad=(48, 18)), 10), 790, 900, STAMP1, rot=-8)],
               post=shake_post([ME1 + 5, STAMP1 + 4], BG))

# ---------- S2: zastupitelstvo a dva povinné výbory, pak „šup“ do finančního ----------
def townhall_icon(s=150):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(s * .5, s * .06), (s * .95, s * .32), (s * .05, s * .32)], fill=G)
    d.rectangle([s * .1, s * .32, s * .9, s * .38], fill=GD)
    for i in range(4):
        x = s * (.18 + i * .2)
        d.rectangle([x, s * .42, x + s * .1, s * .82], fill=G)
    d.rectangle([s * .06, s * .84, s * .94, s * .94], fill=GD)
    d.ellipse([s * .44, s * .15, s * .56, s * .27], fill=WHITE)
    return img

def council_card():
    img = card(760, 330)
    d = ImageDraw.Draw(img)
    img.alpha_composite(townhall_icon(150), (70, 60))
    d.text((250, 80), "Zastupitelstvo", font=font(72, "ExtraBold"), fill=DARK)
    d.text((252, 172), "města", font=font(48, "SemiBold"), fill=GREY)
    for i in range(9):   # lidé u stolu
        x = 120 + i * 68
        col = G if i % 3 == 0 else (GL if i % 3 == 1 else (190, 200, 214))
        d.ellipse([x, 262, x + 38, 300], fill=col)
        d.rounded_rectangle([x - 8, 296, x + 46, 336], radius=18, fill=col)
    return img

def committee_card(l1, fill, fg):
    img = card(440, 230, fill=fill)
    d = ImageDraw.Draw(img)
    f1, f2 = font(66, "ExtraBold"), font(52, "Bold")
    d.text((20 + 220 - f1.getlength(l1) / 2, 70), l1, font=f1, fill=fg)
    d.text((20 + 220 - f2.getlength("výbor") / 2, 150), "výbor", font=f2, fill=fg)
    return img

CC = council_card()
FIN = committee_card("Finanční", G, WHITE)
KON = committee_card("Kontrolní", WHITE, DARK)
FIN_C, KON_C = (295, 1250), (785, 1250)
LINE_AT = 46

def connectors(c, f):
    p = ease_out(clamp((f - LINE_AT) / 14))
    if p <= 0:
        return
    d = ImageDraw.Draw(c)
    y0, y1, y2 = 1000, 1060, 1120
    d.line([(540, y0), (540, y0 + (y1 - y0) * min(1, p * 2))], fill=DARK, width=8)
    if p > .5:
        q = (p - .5) * 2
        for x in (FIN_C[0], KON_C[0]):
            xe = 540 + (x - 540) * q
            d.line([(540, y1), (xe, y1)], fill=DARK, width=8)
            if q > .6:
                d.line([(x, y1), (x, y1 + (y2 - y1) * (q - .6) / .4)], fill=DARK, width=8)
    d.ellipse([530, y0 - 10, 550, y0 + 10], fill=DARK)

class Pulse(El):
    def draw(self, c, f):
        if f < self.at:
            return
        k = f - self.at
        p = clamp(k / 10)
        s = 0.4 + 0.6 * ease_out_back(p)
        if f > 112:
            s *= 1 + 0.06 * math.sin((f - 112) * 0.45) * math.exp(-(f - 112) / 25)
        img = self.img.resize((int(self.img.width * s), int(self.img.height * s)), Image.BILINEAR)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

ZOOM_AT, S2N = 160, 200
t1 = text_img("Finanční výbor musí mít", 76, DARK, w="ExtraBold")
t2 = text_img("každé zastupitelstvo.", 76, DARK, w="ExtraBold")
tag = outline(text_img("Starý Plzenec: tady jsem já", 40, DARK, w="ExtraBold", pill=GL, pad=(24, 12), radius=12), 7)
t3 = text_img("Ze zákona. Spolu s kontrolním.", 50, GREY, w="SemiBold")
S2_base = TextScene(S2N, BG, [El(t1, W // 2, 300, 3), El(t2, W // 2, 395, 10), El(t3, W // 2, 480, 20, "rise"),
                              El(outline(CC, 8).rotate(-1.5, expand=True, resample=Image.BICUBIC), W // 2, 820, 26),
                              Pulse(outline(FIN, 8), *FIN_C, 64), El(outline(KON, 8), *KON_C, 72),
                              El(tag.rotate(4, expand=True, resample=Image.BICUBIC), FIN_C[0] + 150, FIN_C[1] + 180, 104)],
                    extra=connectors)

class ZoomScene:
    n = S2N
    def render(self, f):
        c = S2_base.render(f)
        if f < ZOOM_AT:
            return c
        p = ease_in_out(clamp((f - ZOOM_AT) / (S2N - ZOOM_AT - 4)))
        s = 1 + 11 * p
        cx, cy = FIN_C[0] + 20 * p, FIN_C[1] + 20 * p
        cw, ch = W / s, H / s
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        z = c.transform((W, H), Image.EXTENT, box, resample=Image.BILINEAR)
        a = clamp((p - .45) / .4)
        if a > 0:
            z.alpha_composite(Image.new("RGBA", (W, H), G + (int(255 * a),)))
        return z
S2 = ZoomScene()

# ---------- S3: uvnitř finančního výboru ----------
def doc_icon(s=90):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([14, 6, s - 14, s - 6], radius=8, fill=GL)
    d.polygon([(s - 34, 6), (s - 14, 26), (s - 34, 26)], fill=G)
    for i in range(4):
        d.rounded_rectangle([24, 34 + i * 12, s - 24 - (i % 2) * 14, 40 + i * 12], radius=3, fill=GD)
    return img

def doc_card(text):
    img = card(860, 150)
    img.alpha_composite(doc_icon(96), (50, 47))
    ImageDraw.Draw(img).text((170, 72), text, font=font(58, "ExtraBold"), fill=DARK)
    return img

class Toss(El):
    """Papír přiletí zprava a usadí se s lehkým natočením."""
    def __init__(self, img, cx, cy, at, rot):
        super().__init__(img, cx, cy, at); self.rot = rot
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 12), 1.1)
        x = self.cx + (1 - p) * 1100
        r = self.rot * p + (1 - p) * -18
        img = self.img.rotate(r, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(x - img.width / 2), int(self.cy - img.height / 2)))

def check_img(s=74):
    img = Image.new("RGBA", (s + 8, s + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, s + 4, s + 4], fill=WHITE)
    d.ellipse([10, 10, s - 2, s - 2], fill=G)
    d.line([(s * .3 + 4, s * .52 + 4), (s * .45 + 4, s * .67 + 4), (s * .72 + 4, s * .36 + 4)], fill=WHITE, width=9, joint="curve")
    return img

def magnifier(s=230):
    img = Image.new("RGBA", (s + 120, s + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = s // 2
    d.line([(r + 40 + r * .7, r + 40 + r * .7), (s + 100, s + 100)], fill=DARK, width=34)
    d.ellipse([40, 40, 40 + s, 40 + s], fill=(255, 255, 255, 70), outline=DARK, width=22)
    d.arc([70, 70, 40 + s - 30, 40 + s - 30], 200, 250, fill=WHITE, width=10)
    return img

DOCS = ["Rozpočet města", "Rozpočtová opatření", "Smlouvy", "Další podklady"]
DOC_Y = [560, 740, 920, 1100]
DOC_AT = [30, 50, 70, 90]
DOC_ROT = [2, -1.5, 1.5, -2]
CHECK_AT = [130, 150, 170, 190]
MAG = magnifier()

class Magnifier(El):
    def draw(self, c, f):
        if f < 110 or f > 214:
            return
        path = [(1200, 400)] + [(700, y - 20) for y in DOC_Y] + [(1250, 1300)]
        times = [110] + [a - 8 for a in CHECK_AT] + [214]
        for i in range(len(times) - 1):
            if times[i] <= f <= times[i + 1]:
                p = ease_in_out((f - times[i]) / (times[i + 1] - times[i]))
                x = path[i][0] + (path[i + 1][0] - path[i][0]) * p
                y = path[i][1] + (path[i + 1][1] - path[i][1]) * p
                break
        img = self.img.rotate(8 * math.sin(f * .2), resample=Image.BICUBIC)
        c.alpha_composite(img, (int(x - 155), int(y - 155)))

s3_els = [El(text_img("Co tam děláme?", 100, WHITE, w="ExtraBold"), W // 2, 330, 6),
          El(text_img("Procházíme, co jde do zastupitelstva:", 50, GL, w="SemiBold"), W // 2, 430, 16, "rise")]
for txt, y, at, rot in zip(DOCS, DOC_Y, DOC_AT, DOC_ROT):
    s3_els.append(Toss(doc_card(txt), W // 2, y, at, rot))
for y, at in zip(DOC_Y, CHECK_AT):
    s3_els.append(El(check_img(), W - 150, y - 50, at, dur=8))
s3_els.append(Magnifier(MAG, 0, 0, 0))
s3_els.append(CoinRain(200, n=10, seed=8, dur=60))
s3_els.append(El(outline(text_img("Než o nich zastupitelé hlasují.", 60, DARK, w="ExtraBold", pill=WHITE, pad=(36, 16)), 8)
                 .rotate(-2, expand=True, resample=Image.BICUBIC), W // 2, 1320, 205))
S3 = TextScene(275, G, s3_els)

# ---------- S4: nepřehledné podklady ----------
rng = random.Random(5)
NUMS = [["Položka", "Plán", "Skutečnost"], ["Silnice", "1 250 000", "1 180 400"], ["Školy", "860 000", "912 300"],
        ["Kultura", "320 000", "298 750"], ["Zeleň", "410 000", "437 900"]]
CW, RH = 280, 96
TX0, TY0 = (W - 3 * CW) // 2, 620
CELLS = []
for r, row in enumerate(NUMS):
    for ci, txt in enumerate(row):
        hdr = r == 0
        im = Image.new("RGBA", (CW - 8, RH - 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, CW - 9, RH - 9], radius=10, fill=G if hdr else (WHITE if r % 2 else (244, 247, 242)))
        fnt = font(40 if ci else 42, "ExtraBold" if hdr or ci == 0 else "Bold")
        d.text(((CW - 8) / 2, (RH - 8) / 2), txt, font=fnt, fill=WHITE if hdr else DARK, anchor="mm")
        tidy = (TX0 + ci * CW + CW / 2, TY0 + r * RH + RH / 2)
        messy = (tidy[0] + rng.uniform(-170, 170), tidy[1] + rng.uniform(-120, 160))
        CELLS.append((im, tidy, messy, rng.uniform(-28, 28), rng.uniform(0.75, 1.15)))
TIDY_AT = 70

class Table(El):
    def draw(self, c, f):
        if f < 26:
            return
        a = clamp((f - 26) / 8)
        for i, (im, tidy, messy, rot, sc) in enumerate(CELLS):
            p = ease_out_back(clamp((f - TIDY_AT - (i % 3) * 2 - (i // 3)) / 14), 1.2)
            x = messy[0] + (tidy[0] - messy[0]) * p
            y = messy[1] + (tidy[1] - messy[1]) * p + 6 * math.sin(f * .3 + i) * (1 - p)
            r = rot * (1 - p)
            s = sc + (1 - sc) * p
            img = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR).rotate(r, expand=True, resample=Image.BICUBIC)
            if a < 1:
                img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
            c.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))

S4 = TextScene(215, BG, [El(text_img("Chci, aby radnice dávala", 80, DARK, w="ExtraBold"), W // 2, 320, 3),
                         El(text_img("přehlednější podklady.", 88, WHITE, w="ExtraBold", pill=G, pad=(40, 14)), W // 2, 440, 14),
                         Table(None, 0, 0, 0),
                         El(outline(text_img("Aby bylo jasné,", 76, DARK, w="ExtraBold"), 8), W // 2, 1250, 100),
                         El(outline(text_img("o čem se hlasuje.", 76, GD, w="ExtraBold"), 8), W // 2, 1345, 110),
                         CoinRain(120, n=8, seed=12, dur=60)])

# ---------- S5: závěr ----------
bar = rect_img(120, 10, G, 5)
SLAM5 = 60
S5 = TextScene(180, BG, [El(text_img("Přijďte k volbám", 104, DARK), W // 2, 300, 3),
                         El(text_img("9.–10. října", 132, WHITE, w="ExtraBold", pill=G, pad=(56, 26)), W // 2, 460, 12, dur=11),
                         El(text_img("Dejte hlas člověku,", 66, DARK, w="SemiBold"), W // 2, 615, 26, "rise", dur=12),
                         El(text_img("který zná rozpočet.", 66, GD, w="ExtraBold"), W // 2, 695, 32, "rise", dur=12),
                         El(bar, W // 2, 785, 50, "grow_x", dur=10),
                         El(text_img("Karel Krupička", 96, DARK, w="ExtraBold"), W // 2, 860, 54, dur=11),
                         El(text_img("www.dobrasprava.cz", 38, DARK + (140,), w="SemiBold"), W // 2, 950, 66, "rise", dur=14),
                         Slam(FE.scaled(FE.ST_PLAIN, 880), W // 2, 0, SLAM5)],
               post=shake_post([SLAM5 + 5], BG))

# (scéna, přechod zespodu?)
SCENES = [(S1, False), (S2, True), (S3, False), (S4, True), (S5, True)]
TR = 8

def frames():
    for i, (sc, slide) in enumerate(SCENES):
        prev_last = SCENES[i - 1][0].render(SCENES[i - 1][0].n - 1) if (i and slide) else None
        for f in range(sc.n):
            cur = sc.render(f)
            if prev_last is not None and f < TR:
                e = ease_in_out((f + 1) / (TR + 1))
                c = Image.new("RGBA", (W, H))
                c.paste(prev_last, (0, int(-e * H * 0.35)))
                c.paste(cur, (0, int((1 - e) * H)))
                cur = c
            yield cur.convert("RGB")

# ---------- zvuk ----------
def coin_clink():
    n = int(0.25 * A.SR); t = A.t_(n)
    f0 = A.rng.uniform(2600, 3600)
    return (np.sin(2 * np.pi * f0 * t) + 0.6 * np.sin(2 * np.pi * f0 * 1.51 * t) + 0.3 * np.sin(2 * np.pi * f0 * 2.3 * t)) * np.exp(-t / 0.05)

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc, _ in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    mus = A.seg_pop(total + 0.2, 0.55)[: int(total * SR)]
    out.add(0, mus)
    out.add(st[0] + (ME1 + 5) / FPS, A.fx_impact(), 0.9)
    out.add(st[0] + (STAMP1 + 4) / FPS, A.fx_impact(), 0.8)
    for base, n in ((st[0] + 60 / FPS, 10), (st[2] + 200 / FPS, 8), (st[3] + 120 / FPS, 6)):
        for j in range(n):
            out.add(base + 0.35 + j * 0.13 + A.rng.uniform(0, .06), coin_clink(), 0.35)
    for a in (26, 64, 72):
        out.add(st[1] + a / FPS, A.xylo(A.mf(A.m("C6")), 0.3), 0.5)
    out.add(st[1] + LINE_AT / FPS, A.fx_whoosh(0.45), 0.4)
    out.add(st[1] + ZOOM_AT / FPS, A.fx_whoosh(1.2), 1.0)
    for a in DOC_AT:
        out.add(st[2] + a / FPS - 0.1, A.fx_whoosh(0.3), 0.7)
    for a in CHECK_AT:
        out.add(st[2] + a / FPS, A.fx_ding(), 0.9)
    for j in range(12):
        out.add(st[3] + (TIDY_AT + j * 1.5) / FPS, A.hat(), 0.6)
    out.add(st[3] + (TIDY_AT + 16) / FPS, A.fx_ding(), 0.8)
    out.add(st[4] + (SLAM5 + 5) / FPS - 0.02, A.fx_impact(), 1.0)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fo = int(1.2 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

if __name__ == "__main__":
    total = sum(s.n for s, _ in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "fv_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev = os.path.join(HERE, "prev6"); os.makedirs(prev, exist_ok=True)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
        if k % 10 == 0:
            fr.resize((270, 480)).save(os.path.join(prev, f"{k:04d}.png"))
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
