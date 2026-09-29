"""Kladívka vs. informace – reels 1080x1920, 30 fps, se zvukem."""
import os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import festival as FE
import audio as A
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back,
                    text_img, rect_img, El, TextScene, Slam)

HERE = R.HERE
OUT = os.path.join(HERE, "kladivka.mp4")

WOOD = (166, 112, 64)
STEEL = (78, 88, 104)
STEEL_L = (132, 144, 162)
JACKET = (34, 40, 62)
SHIRT = (88, 120, 170)
SKIN = (226, 188, 160)
FEED_BG = (236, 240, 244)
SKEL = (214, 220, 228)

def outline(img, px=10, col=WHITE):
    a = img.getchannel("A").filter(ImageFilter.MaxFilter(px * 2 + 1))
    out = Image.new("RGBA", img.size, col + (0,))
    out.putalpha(a)
    out.alpha_composite(img)
    return out

# ---------- kladívko (střed obrázku = konec násady) ----------
def hammer_img(L=300, hw=170, hh=74):
    S = 2 * (L + hh) + 60
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img); c = S // 2
    d.rounded_rectangle([c - 15, c - L, c + 15, c + 8], radius=12, fill=WOOD)
    d.rounded_rectangle([c - hw // 2, c - L - hh // 2, c + hw // 2, c - L + hh // 2], radius=12, fill=STEEL)
    d.rounded_rectangle([c - hw // 2 + 12, c - L - hh // 2 + 9, c + hw // 2 - 12, c - L - hh // 2 + 20], radius=5, fill=STEEL_L)
    return outline(img, 10)

# ---------- ruka se sakem a kladivem (střed = rameno) ----------
ARM_L = 600
def arm_img():
    La = 300
    S = 2 * (ARM_L + 80) + 40
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img); c = S // 2
    d.rounded_rectangle([c - 17, c - ARM_L + 20, c + 17, c - La - 40], radius=12, fill=WOOD)       # násada
    d.rounded_rectangle([c - 52, c - La, c + 52, c + 60], radius=50, fill=JACKET)                # rukáv
    d.rounded_rectangle([c - 44, c - La - 26, c + 44, c - La + 14], radius=14, fill=SHIRT)        # manžeta
    d.ellipse([c - 52, c - La - 105, c + 52, c - La - 8], fill=SKIN)                               # pěst
    for k in range(3):
        d.arc([c - 40 + k * 26, c - La - 100, c - 12 + k * 26, c - La - 70], 200, 340, fill=(196, 150, 124), width=4)
    d.rounded_rectangle([c - 115, c - ARM_L - 42, c + 115, c - ARM_L + 42], radius=14, fill=STEEL)  # hlava kladiva
    d.rounded_rectangle([c - 100, c - ARM_L - 32, c + 100, c - ARM_L - 20], radius=5, fill=STEEL_L)
    return outline(img, 10)

def head_offset(a, L):
    r = math.radians(a)
    return (-math.sin(r) * L, -math.cos(r) * L)

# ---------- příspěvek ve feedu ----------
def feed_card(seed):
    r = random.Random(seed)
    cw, ch = 920, 600
    img = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 26, cw + 20, ch + 26], radius=22, fill=(0, 0, 0, 28))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=22, fill=WHITE)
    av = [(190, 200, 215), (200, 190, 180), (180, 200, 190), (205, 195, 215)][seed % 4]
    d.ellipse([28, 26, 98, 96], fill=av)
    d.rounded_rectangle([116, 36, 116 + r.randint(200, 320), 58], radius=11, fill=(70, 80, 98))
    d.rounded_rectangle([116, 70, 236, 86], radius=8, fill=SKEL)
    d.rounded_rectangle([28, 116, 28 + r.randint(600, 820), 134], radius=9, fill=SKEL)
    px0, py0, px1, py1 = 28, 156, cw - 28, 480
    pw, ph_ = px1 - px0, py1 - py0
    ph = Image.new("RGBA", (pw, ph_), (206, 224, 238, 255))
    pd = ImageDraw.Draw(ph)
    pd.rectangle([0, ph_ * 0.62, pw, ph_], fill=(150, 178, 120))
    base = ph_ * 0.92
    n = r.randint(4, 5)
    for k in range(n):
        x = 80 + k * (pw - 160) / (n - 1) + r.randint(-15, 15)
        if abs(x - pw / 2) < 130:
            continue
        hh = r.randint(150, 185)
        suit = r.choice([(55, 62, 80), (70, 70, 76), (48, 56, 74)])
        pd.rounded_rectangle([x - 34, base - hh, x + 34, base], radius=26, fill=suit)
        pd.ellipse([x - 24, base - hh - 52, x + 24, base - hh - 4], fill=(222, 190, 165))
        s = 1 if x < pw / 2 else -1
        ex, ey = x + s * 62, base - hh - 30
        pd.line([(x + s * 20, base - hh + 40), (ex, ey)], fill=suit, width=16)
        pd.line([(ex, ey), (ex + s * 18, ey - 58)], fill=WOOD, width=8)
        pd.rectangle([ex + s * 18 - 24, ey - 78, ex + s * 18 + 24, ey - 56], fill=STEEL)
    sx = pw / 2
    pd.polygon([(sx - 115, base), (sx + 115, base), (sx + 98, base - 125), (sx - 98, base - 125)], fill=(168, 168, 160))
    pd.polygon([(sx - 98, base - 125), (sx + 98, base - 125), (sx + 78, base - 146), (sx - 78, base - 146)], fill=(198, 198, 190))
    pd.text((sx, base - 62), "2026", font=font(46, "ExtraBold"), fill=(125, 125, 118), anchor="mm")
    mask = Image.new("L", ph.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph_ - 1], radius=16, fill=255)
    card.paste(ph, (px0, py0), mask)
    y = 505
    for k, col in enumerate([(66, 133, 244), (230, 80, 80), (245, 190, 60)]):
        d.ellipse([28 + k * 26, y, 64 + k * 26, y + 36], fill=col, outline=WHITE, width=3)
    d.rounded_rectangle([120, y + 10, 220, y + 26], radius=8, fill=SKEL)
    d.rounded_rectangle([cw - 260, y + 10, cw - 28, y + 26], radius=8, fill=SKEL)
    img.alpha_composite(card, (20, 20))
    return img

CARD_GAP = 20
cards = [feed_card(i) for i in range(6)]
TALL = Image.new("RGBA", (W, sum(c.height + CARD_GAP for c in cards) + 400), FEED_BG + (255,))
_y = 0
for c in cards:
    TALL.alpha_composite(c, ((W - c.width) // 2, _y)); _y += c.height + CARD_GAP
FEED_TOP = 380

def app_header():
    img = Image.new("RGBA", (W, 210), WHITE + (255,))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 120, 330, 160], radius=20, fill=(70, 80, 98))
    for k in range(3):
        x = W - 90 - k * 90
        d.ellipse([x - 30, 110, x + 30, 170], fill=(226, 231, 238))
    d.rectangle([0, 206, W, 210], fill=(222, 227, 234))
    return img
HEADER = app_header()

def crack(seed):
    r = random.Random(seed)
    rays = []
    for k in range(9):
        a = k / 9 * 2 * math.pi + r.uniform(-0.25, 0.25)
        L = r.uniform(70, 190)
        pts = [(0, 0)]
        for s in range(1, 5):
            rr = L * s / 4
            pts.append((math.cos(a) * rr + r.uniform(-10, 10), math.sin(a) * rr + r.uniform(-10, 10)))
        rays.append(pts)
    return rays

# ---------- scéna 1: feed + kladívka ----------
HITS = [((400, 820), 52, 1), ((690, 1210), 70, -1), ((380, 1480), 88, 1)]
ARM_HIT = 134
SHATTER = ARM_HIT
SCROLL = 3.0

HAM = hammer_img(300)
ARM = arm_img()

ST_W = 760
_st = FE.scaled(FE.BASE, ST_W); _k = ST_W / FE.BASE.width
ST_X = W - ST_W + 130
ST_Y = H - _st.height + 30
SHOULDER = (ST_X + FE.SHOULDERS[0][0] * _k + 30, ST_Y + FE.SHOULDERS[0][1] * _k + 40)
ARM_TARGET_A = 24
ARM_TARGET = (SHOULDER[0] + head_offset(ARM_TARGET_A, ARM_L)[0], SHOULDER[1] + head_offset(ARM_TARGET_A, ARM_L)[1])
ST_IN = 96
LABEL = text_img("Váš feed tento týden:", 56, WHITE, w="ExtraBold", pill=DARK, pad=(36, 18), radius=14)

def hammer_pose(f, t, side, target, L=300):
    k = f - t
    if k < -16 or k > 16:
        return None
    a_hit = 60 * side
    a_up = a_hit - 80 * side
    P = (target[0] + math.sin(math.radians(a_hit)) * L, target[1] + math.cos(math.radians(a_hit)) * L)
    if k < -8:
        p = ease_out((k + 16) / 8)
        off = (1 - p)
        return (P[0] + side * 800 * off, P[1] + 250 * off), a_up
    if k <= 0:
        p = ((k + 8) / 8) ** 2
        return P, a_up + (a_hit - a_up) * p
    if k <= 4:
        return P, a_hit - 10 * side * math.sin(k / 4 * math.pi)
    p = ease_out((k - 4) / 12) if k > 4 else 0
    return (P[0] + side * 900 * p, P[1] - 200 * p), a_hit - 60 * side * p

def feed_layer(f):
    s = min(f, SHATTER) * SCROLL
    c = Image.new("RGBA", (W, H), FEED_BG + (255,))
    c.alpha_composite(TALL.crop((0, int(s), W, int(s) + H - FEED_TOP)), (0, FEED_TOP))
    d = ImageDraw.Draw(c)
    for i, (tg, t, side) in enumerate(HITS):
        if f >= t:
            fy = tg[1] + t * SCROLL - s
            p = clamp((f - t + 1) / 3)
            for ray in crack(i):
                pts = [(tg[0] + x * p, fy + y * p) for x, y in ray]
                d.line(pts, fill=(40, 48, 64), width=5, joint="curve")
    c.alpha_composite(HEADER)
    if f >= 6:
        El(LABEL, W // 2, 300, 6).draw(c, f)
    return c

# střepy
_rs = random.Random(11)
COLS, ROWS = 6, 9
PIECES = []
for i in range(COLS):
    for j in range(ROWS):
        x0, y0 = int(i * W / COLS), int(j * H / ROWS)
        x1, y1 = int((i + 1) * W / COLS), int((j + 1) * H / ROWS)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = cx - ARM_TARGET[0], cy - ARM_TARGET[1]
        dist = math.hypot(dx, dy) + 1
        sp = _rs.uniform(18, 34) * (1.3 - min(dist, 1400) / 1800)
        PIECES.append(((x0, y0, x1, y1), (dx / dist * sp + _rs.uniform(-4, 4), dy / dist * sp - _rs.uniform(6, 16)),
                       _rs.uniform(-9, 9)))
_snap = None

def arm_angle(f):
    k = f - ST_IN
    if k < 12:
        return -30
    if f < ARM_HIT - 8:
        p = ease_out(clamp((k - 12) / 14))
        return -30 - 25 * p
    if f <= ARM_HIT:
        p = ((f - (ARM_HIT - 8)) / 8) ** 2
        return -55 + (ARM_TARGET_A + 55) * p
    if f <= ARM_HIT + 5:
        return ARM_TARGET_A - 8 * math.sin((f - ARM_HIT) / 5 * math.pi)
    p = ease_out(clamp((f - ARM_HIT - 5) / 18))
    return ARM_TARGET_A + (-15 - ARM_TARGET_A) * p

class FeedScene:
    n = 190
    def render(self, f):
        global _snap
        if f < SHATTER:
            c = feed_layer(f)
        else:
            if _snap is None:
                _snap = feed_layer(SHATTER)
            c = Image.new("RGBA", (W, H), BG + (255,))
            k = f - SHATTER
            for (box, (vx, vy), vr) in PIECES:
                piece = _snap.crop(box)
                px = box[0] + vx * k
                py = box[1] + vy * k + 0.9 * k * k
                if py > H + 200:
                    continue
                pr = piece.rotate(vr * k, expand=True, resample=Image.BILINEAR)
                c.alpha_composite(pr, (int(px - (pr.width - piece.width) / 2), int(py - (pr.height - piece.height) / 2)))
        # létající kladívka
        for tg, t, side in HITS:
            pose = hammer_pose(f, t, side, tg)
            if pose:
                (px, py), a = pose
                img = HAM.rotate(a, resample=Image.BICUBIC)
                c.alpha_composite(img, (int(px - img.width / 2), int(py - img.height / 2)))
        # samolepka s rukou
        if f >= ST_IN:
            dy = (1 - ease_out_back(clamp((f - ST_IN) / 12), 1.3)) * 900
            img = ARM.rotate(arm_angle(f), resample=Image.BICUBIC)
            c.alpha_composite(img, (int(SHOULDER[0] - img.width / 2), int(SHOULDER[1] - img.height / 2 + dy)))
            c.alpha_composite(_st, (ST_X, int(ST_Y + dy)))
        # otřesy + záblesk
        for t, amp in [(t, 12) for _, t, _ in HITS] + [(ARM_HIT, 26)]:
            k = f - t
            if 0 <= k <= 9:
                dd = math.exp(-k / 3)
                out = Image.new("RGBA", (W, H), FEED_BG + (255,))
                out.paste(c, (int(amp * math.sin(k * 2.8) * dd), int(amp * 0.7 * math.cos(k * 3.3) * dd)))
                c = out
        if 0 <= f - ARM_HIT < 4:
            c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(170 * (1 - (f - ARM_HIT) / 4)))))
        return c

S1 = FeedScene()

# ---------- scéna 2: skutečné informace ----------
def white_card(w, h, r=22):
    img = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 28, w + 20, h + 28], radius=r, fill=(27, 38, 59, 40))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(img).rounded_rectangle([20, 20, w + 20, h + 20], radius=r, fill=WHITE)
    return img

def icon(kind, s=96):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=18, fill=GL)
    if kind == "start":   # kalendář
        d.rounded_rectangle([20, 26, s - 20, s - 18], radius=8, fill=WHITE, outline=GD, width=5)
        d.rectangle([20, 26, s - 20, 42], fill=G)
        d.rounded_rectangle([32, 16, 40, 34], radius=3, fill=DARK)
        d.rounded_rectangle([s - 40, 16, s - 32, 34], radius=3, fill=DARK)
        for i in range(3):
            for j in range(2):
                d.rectangle([32 + i * 12, 52 + j * 12, 38 + i * 12, 58 + j * 12], fill=GD)
    elif kind == "end":   # cílová vlajka
        d.rounded_rectangle([26, 16, 32, s - 14], radius=3, fill=DARK)
        for i in range(4):
            for j in range(3):
                col = DARK if (i + j) % 2 == 0 else WHITE
                d.rectangle([32 + i * 11, 20 + j * 11, 43 + i * 11, 31 + j * 11], fill=col)
        d.rectangle([32, 20, 76, 53], outline=DARK, width=2)
    elif kind == "cone":  # dopravní kužel
        O = (240, 128, 40)
        d.polygon([(s / 2 - 8, 16), (s / 2 + 8, 16), (s / 2 + 26, s - 24), (s / 2 - 26, s - 24)], fill=O)
        d.polygon([(s / 2 - 13, 38), (s / 2 + 13, 38), (s / 2 + 17, 50), (s / 2 - 17, 50)], fill=WHITE)
        d.rounded_rectangle([16, s - 26, s - 16, s - 16], radius=4, fill=O)
    elif kind == "pin":
        d.ellipse([28, 16, s - 28, s - 40], fill=G)
        d.polygon([(32, 44), (s - 32, 44), (s / 2, s - 14)], fill=G)
        d.ellipse([40, 28, s - 40, s - 52], fill=WHITE)
    return img

class Grow(El):
    def __init__(self, x, y, w, h, at, col=SKEL, dur=10):
        super().__init__(rect_img(w, h, col, h // 2), x, y, at, "grow_x", dur)
        self.x = x
    def draw(self, canvas, f):
        p = clamp((f - self.at) / self.dur)
        if p <= 0:
            return
        wc = max(1, int(self.img.width * ease_out(p)))
        canvas.alpha_composite(self.img.crop((0, 0, wc, self.img.height)), (self.x, int(self.cy)))

class Shimmer(Grow):
    """Skica, která jemně 'dýchá' (načítá se)."""
    def draw(self, canvas, f):
        super().draw(canvas, f)
        if f < self.at + self.dur:
            return
        x = self.x + ((f * 18) % (self.img.width + 200)) - 100
        hl = Image.new("RGBA", (80, self.img.height), (255, 255, 255, 110))
        box = (max(self.x, int(x)), int(self.cy))
        if box[0] < self.x + self.img.width - 10:
            hl = hl.crop((0, 0, min(80, self.x + self.img.width - box[0]), self.img.height))
            m = self.img.crop((box[0] - self.x, 0, box[0] - self.x + hl.width, self.img.height)).getchannel("A")
            hl.putalpha(Image.eval(m, lambda v: min(v, 110)))
            canvas.alpha_composite(hl, box)

CX = 70
els = []
# karta 1 – zastupitelstvo
els.append(El(white_card(940, 430), W // 2, 440 + 215, 3, dur=10))
els.append(El(text_img("Z POSLEDNÍHO ZASTUPITELSTVA", 36, WHITE, w="ExtraBold", pill=G, pad=(24, 12), radius=10), 0, 0, 9, "rise"))
els[-1].cx = CX + 40 + els[-1].img.width // 2; els[-1].cy = 440 + 70
t1 = text_img("Bylo odhlasováno…", 76, DARK, w="ExtraBold")
els.append(El(t1, CX + 40 + t1.width // 2, 440 + 175, 14, "rise"))
for i, (wd, at) in enumerate(((820, 22), (760, 27), (520, 32))):
    els.append(Shimmer(CX + 50, 440 + 260 + i * 52, wd, 28, at))
# karta 2 – projekt
els.append(El(white_card(940, 200), W // 2, 920 + 100, 58, dur=10))
els.append(El(icon("pin"), CX + 90, 920 + 100, 62))
p1 = text_img("Dostavba centra", 58, DARK, w="ExtraBold")
p2 = text_img("Starý Plzenec – park", 58, GD, w="ExtraBold")
els.append(El(p1, CX + 170 + p1.width // 2, 920 + 68, 64, "rise"))
els.append(El(p2, CX + 170 + p2.width // 2, 920 + 138, 68, "rise"))
# bubliny
BUB = [("start", "Začátek stavby", "říjen 2026", 96), ("end", "Konec stavby", "srpen 2027", 124), ("cone", "Dopravní omezení", None, 152)]
for i, (ic, lab, val, at) in enumerate(BUB):
    y = 1170 + i * 170
    els.append(El(white_card(940, 146), W // 2, y + 73, at, dur=10))
    els.append(El(icon(ic), CX + 90, y + 73, at + 3))
    l = text_img(lab, 40, (96, 108, 128), w="SemiBold")
    els.append(El(l, CX + 170 + l.width // 2, y + 45, at + 4, "rise"))
    if val:
        v = text_img(val, 62, DARK, w="ExtraBold")
        els.append(El(v, CX + 170 + v.width // 2, y + 103, at + 7, "rise"))
    else:
        els.append(Shimmer(CX + 172, y + 84, 420, 38, at + 7))
S2 = TextScene(215, GL, els)
INFO_DINGS = [3, 58, 96, 124, 152]
INFO_TICKS = [22, 27, 32, 159]

# ---------- scéna 3: závěr ----------
def sticker_with_arm():
    a = 26
    ox, oy = 320, 620
    comp = Image.new("RGBA", (ST_W + ox, _st.height + oy), (0, 0, 0, 0))
    sh = (ox + FE.SHOULDERS[0][0] * _k + 30, oy + FE.SHOULDERS[0][1] * _k + 40)
    img = ARM.rotate(a, resample=Image.BICUBIC)
    comp.alpha_composite(img, (int(sh[0] - img.width / 2), int(sh[1] - img.height / 2)))
    comp.alpha_composite(_st, (ox, oy))
    return comp

bar = rect_img(120, 10, G, 5)
SLAM3 = 60
def shake3(c, f):
    t = f - (SLAM3 + 5)
    if t < 0 or t > 10:
        return c
    dd = math.exp(-t / 3.0)
    out = Image.new("RGBA", (W, H), BG + (255,))
    out.paste(c, (int(14 * math.sin(t * 2.7) * dd), int(10 * math.cos(t * 3.1) * dd)))
    return out

S3 = TextScene(165, BG, [El(text_img("Přijďte k volbám", 104, DARK), W//2, 300, 3),
                         El(text_img("9.–10. října", 132, WHITE, w="ExtraBold", pill=G, pad=(56, 26)), W//2, 460, 12, dur=11),
                         El(text_img("Dejte hlas lidem,", 62, DARK, w="SemiBold"), W//2, 615, 26, "rise", dur=12),
                         El(text_img("kteří tu žijí.", 62, DARK, w="SemiBold"), W//2, 690, 30, "rise", dur=12),
                         El(bar, W//2, 785, 50, "grow_x", dur=10),
                         El(text_img("Karel Krupička", 96, DARK, w="ExtraBold"), W//2, 860, 54, dur=11),
                         El(text_img("www.dobrasprava.cz", 38, DARK + (140,), w="SemiBold"), W//2, 950, 66, "rise", dur=14),
                         Slam(sticker_with_arm(), W//2, 0, SLAM3)],
               post=shake3)

SCENES = [S1, S2, S3]

# ---------- zvuk ----------
SR = A.SR
def fx_clink():
    n = int(0.6 * SR); t = A.t_(n)
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
            for f, a, d in ((1870, 0.5, 0.10), (2960, 0.35, 0.07), (4430, 0.25, 0.05), (6100, 0.15, 0.03)))
    x += A.hp(A.rng.standard_normal(n), 2000) * np.exp(-t / 0.008) * 0.7
    x += np.sin(2 * np.pi * np.cumsum(90 + 220 * np.exp(-t / 0.01)) / SR) * np.exp(-t / 0.08) * 0.9
    return x

def fx_shatter():
    n = int(1.6 * SR); t = A.t_(n)
    x = A.hp(A.rng.standard_normal(n), 2500) * np.exp(-t / 0.15) * 0.6
    for _ in range(80):
        st = int(A.rng.uniform(0, 1.0) * SR); f = A.rng.uniform(2500, 9000); dn = int(0.15 * SR)
        tt = A.t_(dn); seg = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.025) * A.rng.uniform(0.08, 0.35)
        e = min(n, st + dn); x[st:e] += seg[: e - st]
    return x

def seg_feed(dur):
    """Hravé pizzicato."""
    T = A.Track(dur); b = 60 / 112
    pat = ["C3", "G3", "E3", "G3", "A2", "E3", "C3", "E3", "F2", "C3", "A2", "C3", "G2", "D3", "B2", "D3"]
    for k in range(int(dur / (b / 2)) + 1):
        T.add(k * b / 2, A.pluck(A.mf(A.m(pat[k % 16])), 0.18, 1600), 0.7)
        if k % 2 == 0: T.add(k * b / 2, A.hat(), 0.35)
    mel = ["E5", None, "G5", "E5", None, "C5", "D5", None]
    for k in range(int(dur / b) + 1):
        n = mel[k % 8]
        if n: T.add(k * b, A.xylo(A.mf(A.m(n)), 0.3), 0.25)
    return T.b

def build_audio(path):
    s2 = S1.n / FPS
    s3 = (S1.n + S2.n) / FPS
    total = (S1.n + S2.n + S3.n) / FPS
    out = A.Track(total)
    first = HITS[0][1] / FPS
    shat = ARM_HIT / FPS
    x = seg_feed(first)
    fo = int(0.15 * SR); x[-fo:] *= np.linspace(1, 0, fo)
    out.add(0, x)
    # napětí: údery bubnu, zrychlují
    t = first; step = 0.42
    while t < shat - 0.05:
        out.add(t, A.kick(0.9), 0.55 + 0.4 * (t - first) / (shat - first))
        t += step; step = max(0.16, step * 0.86)
    for tg, fr, side in HITS:
        out.add(fr / FPS - 0.25, A.fx_whoosh(0.3), 0.8)
        out.add(fr / FPS, fx_clink(), 1.0)
    out.add(ST_IN / FPS, A.fx_whoosh(0.4), 0.6)
    out.add(shat - 0.25, A.fx_whoosh(0.3), 1.0)
    out.add(shat, fx_clink(), 1.0)
    out.add(shat, A.fx_impact(), 1.1)
    out.add(shat, fx_shatter(), 1.0)
    # informace + závěr
    x = A.seg_pop(total - s2 + 0.1, 0.8)
    fi = int(0.4 * SR); x[:fi] *= np.linspace(0, 1, fi)
    out.add(s2, x)
    for d in INFO_DINGS:
        out.add(s2 + d / FPS, A.fx_ding(), 0.9)
    for tk in INFO_TICKS:
        for j in range(4):
            out.add(s2 + tk / FPS + j * 0.05, A.hat(), 0.5)
    out.add(s3 + (SLAM3 + 5) / FPS - 0.02, A.fx_impact(), 1.0)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fo = int(1.2 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

if __name__ == "__main__":
    R.SCENES[:] = SCENES
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUDIO = os.path.join(HERE, "kladivka_audio.wav")
    build_audio(AUDIO)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUDIO, "-shortest",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev = os.path.join(HERE, "prev3"); os.makedirs(prev, exist_ok=True)
    for k, fr in enumerate(R.frames()):
        p.stdin.write(fr.tobytes())
        if k % 10 == 0:
            fr.resize((270, 480)).save(os.path.join(prev, f"{k:04d}.png"))
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
