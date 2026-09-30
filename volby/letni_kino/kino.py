"""Letní kino + spolky – reels 1080x1920, 30 fps, se zvukem."""
import os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import festival as FE
import audio as A
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, rect_img, El, TextScene, Slam)

HERE = R.HERE
OUT = os.path.join(HERE, "letni_kino.mp4")
NIGHT = (22, 31, 50)
YEL = (246, 206, 80)

def outline(img, px=8, col=WHITE):
    a = img.getchannel("A").filter(ImageFilter.MaxFilter(px * 2 + 1))
    out = Image.new("RGBA", img.size, col + (0,)); out.putalpha(a); out.alpha_composite(img)
    return out

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

# ---------- S1: Letošní léto v Sedlci? Letní kino! ----------
def popcorn_img(s=230):
    img = Image.new("RGBA", (s + 40, int(s * 1.3) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = random.Random(4)
    top = int(s * .38) + 20
    for _ in range(22):   # popcorn
        x = r.uniform(40, s); y = r.uniform(20, top + 20); rr = r.uniform(26, 40)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 248, 225))
        d.ellipse([x - rr * .5, y - rr * .6, x + rr * .2, y - rr * .1], fill=(255, 236, 170))
    poly = [(20, top), (s + 20, top), (s - 10, int(s * 1.3) + 20), (50, int(s * 1.3) + 20)]
    d.polygon(poly, fill=WHITE)
    for i in range(5):   # pruhy
        x0 = 20 + i * s / 5
        if i % 2 == 0:
            d.polygon([(x0, top), (x0 + s / 5, top), (x0 + s / 5 - 6 + (i - 2) * -3, int(s * 1.3) + 20),
                       (x0 + 6 + (i - 2) * -3, int(s * 1.3) + 20)], fill=G)
    return outline(img, 9)
POP = popcorn_img()

class Bounce(El):
    def __init__(self, img, cx, cy, at, rot=0):
        super().__init__(img, cx, cy, at); self.rot = rot
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        s = 0.3 + 0.7 * ease_out_back(clamp(k / 10), 2.2)
        wob = 4 * math.sin(k * .25)
        img = self.img.resize((int(self.img.width * s), int(self.img.height * s)), Image.BILINEAR)
        img = img.rotate(self.rot + wob, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

class PopKernels(El):
    """Poletující popcorn z kbelíku."""
    def __init__(self, at, cx, cy, seed):
        super().__init__(None, cx, cy, at)
        r = random.Random(seed)
        self.k = [(r.uniform(-9, 9), r.uniform(-26, -16), r.uniform(18, 28), at + r.uniform(0, 30)) for _ in range(9)]
    def draw(self, c, f):
        d = ImageDraw.Draw(c)
        for vx, vy, rr, t0 in self.k:
            k = f - t0
            if k < 0 or k > 40:
                continue
            x = self.cx + vx * k; y = self.cy + vy * k + .9 * k * k
            d.ellipse([x - rr - 5, y - rr - 5, x + rr + 5, y + rr + 5], fill=WHITE)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 244, 210))

def s1_bg(c, f):
    d = ImageDraw.Draw(c)
    r = random.Random(2)
    for _ in range(60):   # hvězdy
        x, y, s = r.uniform(0, W), r.uniform(0, H * .6), r.uniform(2, 5)
        tw = .5 + .5 * math.sin(f * .15 + x)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 255, 255, int(120 + 120 * tw)))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # paprsek projektoru
    od = ImageDraw.Draw(ov)
    fl = 40 + 12 * math.sin(f * 1.7)
    od.polygon([(W + 40, H - 200), (-60, 380), (-60, 1080)], fill=GL + (int(fl),))
    c.alpha_composite(ov)

S1 = TextScene(84, NIGHT, [El(text_img("Letošní léto v Sedlci?", 88, WHITE, w="ExtraBold"), W // 2, 620, 3),
                           El(outline(text_img("Letní kino!", 150, WHITE, w="ExtraBold", pill=G, pad=(50, 20)), 10)
                              .rotate(-3, expand=True, resample=Image.BICUBIC), W // 2, 790, 14, dur=11),
                           PopKernels(34, 300, 1300, 1), PopKernels(40, 790, 1360, 2),
                           Bounce(POP, 300, 1400, 28, -8), Bounce(POP, 790, 1460, 34, 7)],
                extra=s1_bg)

# ---------- S2: video ----------
VID = sorted(os.path.join(HERE, "kino_vid", x) for x in os.listdir(os.path.join(HERE, "kino_vid")))
grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(grad)
for yy in range(H):
    a = 0
    if yy < 520: a = int(120 * ((520 - yy) / 520) ** 1.5)
    if yy > 1350: a = int(120 * ((yy - 1350) / 570) ** 1.5)
    gd.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
v_top = outline(text_img("Parádní večer.", 92, WHITE, w="ExtraBold", pill=G, pad=(40, 16)), 8)

class VideoScene:
    n = len(VID)
    els = [El(v_top, W // 2, 330, 4, dur=10)]
    def render(self, f):
        c = Image.open(VID[min(f, self.n - 1)]).convert("RGBA")
        c.alpha_composite(grad)
        for e in self.els:
            e.draw(c, f)
        return c
S2 = VideoScene()

# ---------- S3: výjimečné → běžné ----------
STRIKE = 40
w_vyj = text_img("výjimečné.", 130, DARK, w="ExtraBold")
class Strike(El):
    def draw(self, c, f):
        p = ease_out(clamp((f - self.at) / 8))
        if p <= 0:
            return
        d = ImageDraw.Draw(c)
        x0 = self.cx - w_vyj.width / 2 - 10
        d.line([(x0, self.cy + 8), (x0 + (w_vyj.width + 20) * p, self.cy - 4)], fill=G, width=18)
S3 = TextScene(120, BG, [El(text_img("Nemělo by to být", 92, DARK, w="ExtraBold"), W // 2, 640, 3),
                         El(w_vyj, W // 2, 780, 12), Strike(None, W // 2, 790, STRIKE),
                         El(outline(text_img("běžné.", 150, WHITE, w="ExtraBold", pill=G, pad=(50, 18)), 10)
                            .rotate(-4, expand=True, resample=Image.BICUBIC), W // 2, 960, STRIKE + 10, dur=10),
                         El(text_img("Kultura pro všechny.", 76, GD, w="ExtraBold"), W // 2, 1160, 72, "rise")],
               post=shake_post([STRIKE + 13], BG, 10))

# ---------- S4: spolky + nenápadné sporty ----------
def vignette(size=(380, 380)):
    img = Image.new("RGBA", (size[0] + 30, size[1] + 30), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([15, 15, size[0] + 15, size[1] + 15], radius=36, fill=WHITE)
    return img

# rybníky (tvar z mapy, souřadnice obrázku mapy)
POND_LOW = [(440, 555), (730, 475), (770, 500), (800, 550), (760, 690), (750, 720), (770, 850), (750, 920), (680, 960),
            (662, 985), (675, 1110), (655, 1210), (685, 1260), (685, 1300), (600, 1420), (640, 1505), (600, 1505),
            (560, 1450), (500, 1400), (410, 1300), (378, 1190), (390, 1050), (420, 850), (455, 720)]
POND_UP = [(270, 160), (310, 85), (330, 110), (460, 100), (480, 130), (540, 110), (590, 180), (598, 250), (710, 255),
           (745, 350), (730, 455), (530, 515), (470, 460), (455, 390), (365, 318), (348, 332)]
PATH = [(590, 1330), (560, 1150), (560, 950), (600, 760), (640, 590)]

def pond_map(s):
    """Mapa rybníků zmenšená do čtverce s x s; vrací obrázek a převod souřadnic."""
    x0, y0, x1, y1 = 250, 60, 820, 1520
    sc = s / (y1 - y0)
    ox = (s - (x1 - x0) * sc) / 2
    tf = lambda p: (ox + (p[0] - x0) * sc, (p[1] - y0) * sc)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for poly in (POND_UP, POND_LOW):
        d.polygon([tf(p) for p in poly], fill=(160, 212, 232))
    return img, tf

class Canoe(El):
    def __init__(self, cx, cy, at):
        super().__init__(None, cx, cy, at)
        self.map, self.tf = pond_map(350)
        self.base = vignette()
        self.base.alpha_composite(self.map, (30, 30))
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        img = self.base.copy()
        d = ImageDraw.Draw(img)
        pts = [self.tf(p) for p in PATH]
        u = (k * 0.012) % 2
        u = u if u < 1 else 2 - u
        seg = min(len(pts) - 2, int(u * (len(pts) - 1)))
        q = u * (len(pts) - 1) - seg
        x = pts[seg][0] + (pts[seg + 1][0] - pts[seg][0]) * q + 30
        y = pts[seg][1] + (pts[seg + 1][1] - pts[seg][1]) * q + 30
        ang = math.atan2(pts[seg + 1][1] - pts[seg][1], pts[seg + 1][0] - pts[seg][0])
        L = 30
        ca, sa = math.cos(ang), math.sin(ang)
        tip1 = (x + ca * L, y + sa * L); tip2 = (x - ca * L, y - sa * L)
        nx, ny = -sa * 7, ca * 7
        d.polygon([tip1, (x + nx, y + ny), tip2, (x - nx, y - ny)], fill=GD)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=YEL)
        pa = math.sin(k * .5) * 0.9
        px, py = -sa * math.cos(pa) * 22 + ca * math.sin(pa) * 10, ca * math.cos(pa) * 22 + sa * math.sin(pa) * 10
        d.line([(x - px, y - py), (x + px, y + py)], fill=DARK, width=4)
        for side in (-1, 1):   # vlnky
            wx, wy = x - ca * 38 + side * nx * 1.6, y - sa * 38 + side * ny * 1.6
            d.arc([wx - 8, wy - 8, wx + 8, wy + 8], 0, 180, fill=WHITE, width=3)
        s = 0.4 + 0.6 * ease_out_back(clamp(k / 10))
        img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR).rotate(getattr(self, 'tilt', -4), expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

class Football(El):
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        img = vignette()
        d = ImageDraw.Draw(img)
        d.rectangle([15, 300, 395, 395], fill=(150, 200, 120))
        gx0, gx1, gy0, gy1 = 150, 370, 120, 300
        t = (k % 40) / 40
        bulge = 14 * math.exp(-max(0, t - .45) * 12) if t > .45 else 0
        for i in range(8):   # síť
            x = gx0 + i * (gx1 - gx0) / 7
            d.line([(x + bulge * (i > 0 and i < 7), gy0), (x + bulge * (i > 0 and i < 7), gy1)], fill=(200, 208, 218), width=2)
        for j in range(6):
            y = gy0 + j * (gy1 - gy0) / 5
            d.line([(gx0, y), (gx1 + bulge, y)], fill=(200, 208, 218), width=2)
        d.line([(gx0, gy1), (gx0, gy0), (gx1, gy0), (gx1, gy1)], fill=DARK, width=10)
        if t < .45:
            p = t / .45
            bx, by = 60 + (250 - 60) * p, 300 - 170 * math.sin(p * math.pi * .85)
        else:
            bx, by = 250 + bulge, 230 + (t - .45) * 120
        r = 26
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=WHITE, outline=DARK, width=4)
        d.regular_polygon((bx, by, 10), 5, rotation=k * 20, fill=DARK)
        s = 0.4 + 0.6 * ease_out_back(clamp(k / 10))
        img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR).rotate(getattr(self, 'tilt', 4), expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

class Tennis(El):
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        img = vignette()
        d = ImageDraw.Draw(img)
        d.rectangle([15, 300, 395, 395], fill=(214, 140, 90))   # antuka
        d.line([(15, 300), (395, 300)], fill=WHITE, width=5)
        d.line([(205, 200), (205, 305)], fill=DARK, width=5)
        for yy in range(205, 300, 12):
            d.line([(205, yy), (205, yy)], fill=DARK)
        d.rectangle([200, 196, 210, 206], fill=DARK)
        t = (k % 36) / 36
        pp = t * 2 if t < .5 else 2 - t * 2
        bx = 90 + 250 * pp
        by = 250 - 150 * math.sin(pp * math.pi)
        # raketa vlevo
        swing = math.exp(-((t % 1) * 36) / 4) * 35 if t < .15 or t > .98 else 0
        ra = Image.new("RGBA", (140, 240), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ra)
        rd.rounded_rectangle([62, 120, 78, 235], radius=6, fill=DARK)
        rd.ellipse([20, 10, 120, 135], outline=G, width=10)
        for i in range(5):
            rd.line([(38 + i * 16, 18), (38 + i * 16, 128)], fill=(200, 208, 218), width=2)
            rd.line([(24, 30 + i * 20), (116, 30 + i * 20)], fill=(200, 208, 218), width=2)
        ra = ra.rotate(20 + swing, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(ra, (0, 110))
        r = 17
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=(214, 232, 70), outline=(150, 170, 40), width=3)
        d.arc([bx - r + 4, by - r - 6, bx + r - 4, by + r - 6], 30, 150, fill=WHITE, width=3)
        s = 0.4 + 0.6 * ease_out_back(clamp(k / 10))
        img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR).rotate(getattr(self, 'tilt', -3), expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

class Gym(El):
    """Gymnasta dělá salto na žíněnce."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        img = vignette()
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([60, 320, 350, 360], radius=12, fill=(96, 130, 190))
        t = (k % 44) / 44
        jump = math.sin(min(1, t / .8) * math.pi) if t < .8 else 0
        rot = 360 * ease_in_out(min(1, t / .8)) if t < .8 else 0
        cx, cy = 205, 250 - 120 * jump
        fig = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fig)
        fd.ellipse([84, 12, 116, 44], fill=(226, 188, 160))
        fd.rounded_rectangle([82, 46, 118, 110], radius=14, fill=G)
        fd.line([(90, 108), (80, 170)], fill=DARK, width=14)
        fd.line([(110, 108), (120, 170)], fill=DARK, width=14)
        arm = 60 if t < .8 else 10
        fd.line([(86, 56), (86 - math.sin(math.radians(arm)) * 50, 56 - math.cos(math.radians(arm)) * 50)], fill=(226, 188, 160), width=11)
        fd.line([(114, 56), (114 + math.sin(math.radians(arm)) * 50, 56 - math.cos(math.radians(arm)) * 50)], fill=(226, 188, 160), width=11)
        fig = fig.rotate(-rot, center=(100, 100), resample=Image.BICUBIC)
        img.alpha_composite(fig, (int(cx - 100), int(cy - 100 + (60 if jump == 0 else 0) * 0)))
        s = 0.4 + 0.6 * ease_out_back(clamp(k / 10))
        img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR).rotate(getattr(self, 'tilt', 3), expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

S4 = TextScene(165, GL, [Football(None, 250, 420, 30), Tennis(None, 830, 440, 38),
                         El(text_img("Podpora spolků", 96, DARK, w="ExtraBold"), W // 2, 780, 3),
                         El(text_img("je zásadní.", 96, DARK, w="ExtraBold"), W // 2, 890, 10),
                         El(text_img("Město má být", 84, GD, w="ExtraBold"), W // 2, 1025, 50, "rise"),
                         El(outline(text_img("partner.", 130, WHITE, w="ExtraBold", pill=G, pad=(46, 16)), 10)
                            .rotate(-3, expand=True, resample=Image.BICUBIC), W // 2, 1200, 60, dur=10),
                         Canoe(250, 1490, 46), Gym(None, 830, 1500, 54)])

# ---------- S5: závěr ----------
bar = rect_img(120, 10, G, 5)
SLAM5 = 60
S5 = TextScene(170, BG, [El(text_img("Přijďte k volbám", 104, DARK), W // 2, 300, 3),
                         El(text_img("9.–10. října", 132, WHITE, w="ExtraBold", pill=G, pad=(56, 26)), W // 2, 460, 12, dur=11),
                         El(text_img("Dejte hlas člověku,", 66, DARK, w="SemiBold"), W // 2, 615, 26, "rise", dur=12),
                         El(text_img("který podpoří spolky.", 66, GD, w="ExtraBold"), W // 2, 695, 32, "rise", dur=12),
                         El(bar, W // 2, 785, 50, "grow_x", dur=10),
                         El(text_img("Karel Krupička", 96, DARK, w="ExtraBold"), W // 2, 860, 54, dur=11),
                         El(text_img("www.dobrasprava.cz", 38, DARK + (140,), w="SemiBold"), W // 2, 950, 66, "rise", dur=14),
                         Slam(FE.scaled(FE.ST_PLAIN, 880), W // 2, 0, SLAM5)],
               post=shake_post([SLAM5 + 5], BG))

SCENES = [(S1, False), (S2, True), (S3, True), (S4, True), (S5, True)]
TR = 8

def frames():
    for i, (sc, slide) in enumerate(SCENES):
        prev_last = SCENES[i - 1][0].render(SCENES[i - 1][0].n - 1) if (i and slide) else None
        for f in range(sc.n):
            cur = sc.render(f)
            if prev_last is not None and f < TR:
                e = ease_in_out((f + 1) / (TR + 1))
                cc = Image.new("RGBA", (W, H))
                cc.paste(prev_last, (0, int(-e * H * 0.35)))
                cc.paste(cur, (0, int((1 - e) * H)))
                cur = cc
            yield cur.convert("RGB")

# ---------- zvuk ----------
def fx_pop():
    n = int(0.12 * A.SR); t = A.t_(n)
    f = 900 * np.exp(-t / 0.02) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / A.SR) * np.exp(-t / 0.03) * 0.8

def fx_splash():
    n = int(0.3 * A.SR); t = A.t_(n)
    return A.bp(A.rng.standard_normal(n), 400, 2500) * np.exp(-t / 0.08) * 0.5

def fx_pok():
    n = int(0.12 * A.SR); t = A.t_(n)
    return (np.sin(2 * np.pi * 520 * t) + A.bp(A.rng.standard_normal(n), 1500, 5000) * .5) * np.exp(-t / 0.02)

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc, _ in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    mus = A.seg_pop(total + 0.2, 0.55)[: int(total * SR)]
    # během videa hudbu ztlumit a pustit zvuk z kina
    env = np.ones(len(mus))
    a0, a1 = int(st[1] * SR), int(st[2] * SR)
    env[a0:a1] = 0.35
    out.add(0, mus * lp_env(env))
    try:
        sr0, kz = A.wavfile.read(os.path.join(HERE, "kino_audio.wav"))
        kz = kz.astype(np.float64) / 32768
        if kz.ndim > 1: kz = kz.mean(1)
        fi = int(0.15 * SR); kz[:fi] *= np.linspace(0, 1, fi); kz[-fi:] *= np.linspace(1, 0, fi)
        out.add(st[1], kz / (np.max(np.abs(kz)) + 1e-9), 0.8)
    except Exception as e:
        print("zvuk z videa:", e)
    # projektor
    for j in range(int(2.6 * 12)):
        out.add(st[0] + j / 12, A.hat(), 0.25)
    for a in (28, 34):
        out.add(st[0] + a / FPS, fx_pop(), 0.7)
    r = random.Random(3)
    for _ in range(14):
        out.add(st[0] + (36 + r.uniform(0, 36)) / FPS, fx_pop(), 0.35)
    out.add(st[2] + STRIKE / FPS, A.fx_whoosh(0.25), 0.6)
    out.add(st[2] + (STRIKE + 12) / FPS, A.fx_impact(), 0.7)
    for k in range(38, 165, 18):
        out.add(st[3] + k / FPS, fx_pok(), 0.35)
    for k in range(46, 165, 13):
        out.add(st[3] + k / FPS, fx_splash(), 0.25)
    for k in range(30, 165, 40):
        out.add(st[3] + (k + 18) / FPS, A.kick(0.6), 0.4)
    out.add(st[3] + 60 / FPS, A.fx_ding(), 0.7)
    out.add(st[4] + (SLAM5 + 5) / FPS - 0.02, A.fx_impact(), 1.0)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fo = int(1.2 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

def lp_env(e):
    k = int(0.2 * A.SR)
    return np.convolve(e, np.ones(k) / k, mode="same")

if __name__ == "__main__" and False:
    total = sum(s.n for s, _ in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "kino_mix.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
