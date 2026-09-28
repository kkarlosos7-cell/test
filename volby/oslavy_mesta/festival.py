"""Oslavy města pro všechny generace – reels 1080x1920, 30 fps, bez hudby."""
import os, math, subprocess
from PIL import Image, ImageDraw
import render as R
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back,
                    ease_in_out, text_img, rich_line, rect_img, El, TextScene, stack, Slam)

HERE = R.HERE
OUT = os.path.join(HERE, "oslavy_mesta.mp4")

# ---------- sticker a jeho varianty ----------
PAD = 300  # místo nad hlavou pro klobouk
_raw = Image.open(os.path.join(HERE, "sticker.png")).convert("RGBA")
BASE = Image.new("RGBA", (_raw.width, _raw.height + PAD), (0, 0, 0, 0))
BASE.alpha_composite(_raw, (0, PAD))
EYES = (590, 308 + PAD)     # střed mezi očima (v souřadnicích BASE)
HEAD_TOP = (595, 45 + PAD)
SHOULDERS = ((250, 660 + PAD), (940, 660 + PAD))

def glasses_img(width):
    """Pixelové 'deal with it' brýle."""
    rows = ["XXXXXXXXXXXXXXXXXXXXXXXX",
            "XXXXXXXXXXXXXXXXXXXXXXXX",
            "..XWWXXXXXXX..XWWXXXXXX.",
            "..XXWWXXXXXX..XXWWXXXXX.",
            "...XXXXXXXX....XXXXXXX..",
            "....XXXXXX......XXXXX..."]
    cols = len(rows[0]); px = width / cols
    img = Image.new("RGBA", (int(width) + 2, int(px * len(rows)) + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            col = (12, 12, 12, 255) if ch == "X" else (255, 255, 255, 255)
            d.rectangle([c * px, r * px, (c + 1) * px, (r + 1) * px], fill=col)
    return img

GLASSES_W = 330
def with_glasses(im):
    im = im.copy()
    g = glasses_img(GLASSES_W)
    im.alpha_composite(g, (int(EYES[0] - g.width / 2), int(EYES[1] - g.height * 0.42)))
    return im

def with_hat(im):
    """Krojový klobouk s pérem a stužkou."""
    im = im.copy()
    d = ImageDraw.Draw(im)
    # péro
    fe = Image.new("RGBA", (120, 330), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fe)
    fd.ellipse([10, 0, 110, 300], fill=GL)
    fd.line([(60, 20), (60, 330)], fill=GD, width=8)
    for k in range(8):
        y = 50 + k * 30
        fd.line([(60, y), (20, y - 25)], fill=G, width=4)
        fd.line([(60, y), (100, y - 25)], fill=G, width=4)
    fe = fe.rotate(28, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(fe, (360, 40))
    # koruna klobouku
    d.rounded_rectangle([470, 230, 720, 410], radius=34, fill=DARK)
    # stuha
    d.rectangle([470, 345, 720, 392], fill=G)
    for x in range(495, 720, 44):
        d.ellipse([x - 11, 357, x + 11, 379], fill=WHITE)
        d.ellipse([x - 5, 363, x + 5, 373], fill=GD)
    # krempa
    d.ellipse([380, 385, 810, 445], fill=DARK)
    d.ellipse([400, 388, 790, 420], fill=(40, 54, 80))
    # visící stužky
    d.polygon([(740, 405), (772, 405), (805, 560), (775, 560)], fill=G)
    d.polygon([(778, 405), (800, 405), (840, 520), (815, 525)], fill=GL)
    return im

def fade_bottom(im, frac=0.3):
    im = im.copy(); a = im.getchannel("A")
    h0 = int(im.height * (1 - frac))
    m = Image.new("L", im.size, 255); md = ImageDraw.Draw(m)
    for y in range(h0, im.height):
        md.line([(0, y), (im.width, y)], fill=int(255 * (1 - (y - h0) / (im.height - h0)) ** 1.5))
    from PIL import ImageChops
    im.putalpha(ImageChops.multiply(a, m))
    return im

def scaled(im, w):
    return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)

ST_PLAIN = BASE
ST_HAT = with_hat(BASE)
ST_SWAG = with_glasses(BASE)

# ---------- pomocné prvky ----------
def label(text, at, y=300, bg=G, fg=WHITE):
    return El(text_img(text, 40, fg, w="ExtraBold", pill=bg, pad=(30, 14), radius=12), W // 2, y, at, "rise")

def tilted(img, deg):
    return img.rotate(deg, expand=True, resample=Image.BICUBIC)

def bubble(text, size=48):
    f = font(size, "SemiBold")
    tw = int(f.getlength(text)); asc, desc = f.getmetrics()
    w, h = tw + 80, asc + desc + 50
    img = Image.new("RGBA", (w + 10, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w, h], radius=16, fill=WHITE)
    d.polygon([(w // 2 - 30, h - 2), (w // 2 + 10, h - 2), (w // 2 - 40, h + 36)], fill=WHITE)
    d.text((40, 25), text, font=f, fill=DARK)
    return img

def note_img(color, size=90):
    img = Image.new("RGBA", (size, int(size * 1.3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size
    d.ellipse([0, s * 0.85, s * 0.5, s * 1.25], fill=color)
    d.rectangle([s * 0.42, s * 0.1, s * 0.5, s * 1.05], fill=color)
    d.polygon([(s * 0.46, s * 0.1), (s * 0.95, s * 0.3), (s * 0.95, s * 0.5), (s * 0.46, s * 0.3)], fill=color)
    return img

def guitar_img():
    img = Image.new("RGBA", (300, 640), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([130, 10, 170, 380], radius=8, fill=DARK)     # krk
    d.rounded_rectangle([115, 0, 185, 60], radius=12, fill=GD)        # hlava
    for k in range(3):
        d.ellipse([100, 8 + k * 17, 114, 22 + k * 17], fill=DARK)
        d.ellipse([186, 8 + k * 17, 200, 22 + k * 17], fill=DARK)
    d.ellipse([60, 300, 240, 460], fill=G)                             # horní část těla
    d.ellipse([30, 400, 270, 630], fill=G)                             # dolní část těla
    d.ellipse([112, 400, 188, 476], fill=DARK)                         # ozvučný otvor
    d.rounded_rectangle([105, 540, 195, 562], radius=6, fill=GD)       # kobylka
    for k in range(4):
        x = 138 + k * 8
        d.line([(x, 30), (x, 550)], fill=GL, width=2)
    return img

# ---------- S1: úvod ----------
a1 = text_img("Oslavy města?", 140, DARK)
a2 = text_img("Ať si je užije", 118, DARK)
a3 = text_img("každý.", 150, WHITE, w="ExtraBold", pill=G, pad=(46, 14))
ys = stack([a1, a2, a3], 720, gap=24)
tags = [("děti", -6, 260, 1200), ("rodiče", 5, 790, 1260), ("babičky a dědové", 4, 470, 1430), ("mladí", -5, 830, 1580)]
t_els = [El(tilted(text_img(t, 72, DARK, pill=GL, pad=(38, 18), radius=12), r), x, y, 30 + i * 5)
         for i, (t, r, x, y) in enumerate(tags)]
S1 = TextScene(84, BG, [El(a1, W//2, ys[0], 3), El(a2, W//2, ys[1], 12), El(a3, W//2, ys[2], 20, dur=11)] + t_els)

# ---------- S2: Bambuláček – loutka ----------
PUP_W = 560
_ps = fade_bottom(scaled(ST_PLAIN, PUP_W), 0.28); _k = PUP_W / BASE.width
PUP_STR = 330  # délka od vahadla k temeni hlavy
pup = Image.new("RGBA", (PUP_W + 200, _ps.height + PUP_STR + 60), (0, 0, 0, 0))
pd = ImageDraw.Draw(pup)
ox, oy = 100, PUP_STR + 40
cx = ox + HEAD_TOP[0] * _k
pup.alpha_composite(_ps, (ox, oy))
# vahadlo (kříž)
pd.rounded_rectangle([cx - 230, 18, cx + 230, 44], radius=10, fill=(139, 94, 60))
pd.rounded_rectangle([cx - 13, 0, cx + 13, 90], radius=10, fill=(139, 94, 60))
# provázky
for (sx, sy), tx in ((SHOULDERS[0], cx - 220), (SHOULDERS[1], cx + 220)):
    pd.line([(tx, 32), (ox + sx * _k, oy + sy * _k)], fill=(240, 240, 240), width=3)
pd.line([(cx, 80), (ox + HEAD_TOP[0] * _k, oy + HEAD_TOP[1] * _k + 6)], fill=(240, 240, 240), width=3)
PUP_PIVOT = (cx, 30)

class Puppet(El):
    def draw(self, canvas, f):
        k = f - self.at
        if k < 0:
            return
        drop = (1 - ease_out_back(clamp(k / 14), 1.4)) * -900
        ang = 7 * math.sin(k * 0.16) * (0.6 + 0.4 * math.exp(-k / 30))
        bob = 14 * math.sin(k * 0.32)
        img = self.img.rotate(ang, center=PUP_PIVOT, resample=Image.BICUBIC)
        canvas.alpha_composite(img, (int(self.cx - PUP_PIVOT[0]), int(self.cy + drop + bob)))

def stage(c, f):
    d = ImageDraw.Draw(c)
    # opona po stranách
    for side in (0, 1):
        for i in range(5):
            w = 34
            x = i * w if side == 0 else W - (i + 1) * w
            d.rectangle([x, 0, x + w, H], fill=G if i % 2 == 0 else GD)
    # lambrekýn nahoře
    d.rectangle([0, 0, W, 150], fill=GD)
    for i in range(12):
        x = i * 90 + 45
        d.ellipse([x - 50, 110, x + 50, 190], fill=GD)
    # podium dole
    d.rectangle([0, 1720, W, H], fill=(139, 94, 60))
    d.rectangle([0, 1720, W, 1740], fill=(110, 72, 44))

b1 = text_img("Bambuláček", 140, WHITE, w="ExtraBold")
b2 = text_img("pro nejmenší", 70, GL, w="Bold")
joke = bubble("Za nitky mě tahají jen děti.")
S2 = TextScene(110, DARK, [label("ODPOLEDNE", 2, y=270), El(b1, W//2, 420, 6), El(b2, W//2, 530, 14),
                           Puppet(pup, W//2, 600, 18), El(joke, W//2, 1580, 52, dur=10)], extra=stage)

# ---------- S3: Dechovka v kroji ----------
class Sway(El):
    """Sticker se kolébá do rytmu (od spodku obrazovky)."""
    def __init__(self, img, at, amp=4, speed=0.42, w=820):
        super().__init__(scaled(img, w), W // 2, 0, at)
        self.amp, self.speed = amp, speed
    def draw(self, canvas, f):
        k = f - self.at
        if k < 0:
            return
        dy = (1 - ease_out_back(clamp(k / 12), 1.2)) * 900
        ang = self.amp * math.sin(k * self.speed)
        img = self.img.rotate(ang, center=(self.img.width / 2, self.img.height), resample=Image.BICUBIC)
        canvas.alpha_composite(img, (int(W / 2 - img.width / 2), int(H - img.height + 30 + dy)))

class Float(El):
    """Nota, která se vznáší nahoru."""
    def draw(self, canvas, f):
        k = f - self.at
        if k < 0:
            return
        a = clamp(k / 8) * clamp((60 - k) / 15)
        if a <= 0:
            return
        img = self.img.rotate(10 * math.sin(k * 0.2), expand=True)
        img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        canvas.alpha_composite(img, (int(self.cx + 20 * math.sin(k * 0.15)), int(self.cy - k * 5)))

d1 = text_img("Dechovka", 150, DARK, w="ExtraBold")
d2 = rich_line([("v ", DARK), ("kroji", GD), (", jak se patří.", DARK)], 64)
notes = [Float(note_img(G), 140, 1000, 26), Float(note_img(GD, 70), 860, 950, 34),
         Float(note_img(G, 80), 900, 1250, 48), Float(note_img(GD), 120, 1300, 60)]
S3 = TextScene(95, GL, [label("ODPOLEDNE", 2, y=270, bg=GD), El(d1, W//2, 420, 6), El(d2, W//2, 540, 14),
                        Sway(ST_HAT, 20, w=780)] + notes)

# ---------- S4: Podvečer – kytara, sticker běží ----------
class Runner(El):
    def __init__(self, img, at, dur=34, y=1380, w=480):
        super().__init__(tilted(fade_bottom(scaled(img, w), 0.3), -9), 0, y, at)
        self.run_dur = dur
    def draw(self, canvas, f):
        k = f - self.at
        if k < 0 or k > self.run_dur:
            return
        p = k / self.run_dur
        x = -self.img.width + p * (W + 2 * self.img.width)
        bob = abs(math.sin(k * 0.9)) * -40
        d = ImageDraw.Draw(canvas)
        for i, (ly, lw) in enumerate(((0.35, 180), (0.55, 260), (0.75, 150))):
            yy = self.cy - self.img.height / 2 + self.img.height * ly + bob
            d.rounded_rectangle([x - lw - 30, yy, x - 30, yy + 16], radius=8, fill=G if i % 2 else GD)
        canvas.alpha_composite(self.img, (int(x), int(self.cy - self.img.height / 2 + bob)))

g1 = text_img("Kytara", 160, DARK, w="ExtraBold")
g2 = text_img("a písničky, co zná každý.", 62, DARK)
guit = El(tilted(guitar_img(), -24), W // 2, 1020, 12, dur=12)
S4 = TextScene(86, BG, [label("PODVEČER", 2, y=270), El(g1, W//2, 430, 5), El(g2, W//2, 555, 12), guit,
                        El(text_img("…a honem dál!", 56, GD, w="Bold"), W//2, 1720, 44, "rise"),
                        Runner(ST_PLAIN, 34, y=1330, w=600)])

# ---------- S5: Večer – kapela + swag brýle ----------
def beams(c, f):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i, (x0, ph, col) in enumerate(((120, 0, G), (540, 2.1, GL), (960, 4.2, G))):
        ang = math.radians(90 + 22 * math.sin(f * 0.07 + ph))
        L = 2300
        tipx, tipy = x0 + math.cos(ang) * L, math.sin(ang) * L
        nx, ny = -math.sin(ang) * 260, math.cos(ang) * 260
        d.polygon([(x0, -20), (tipx + nx, tipy + ny), (tipx - nx, tipy - ny)], fill=col + (38,))
    c.alpha_composite(ov)

SW_W = 820
_sw = scaled(ST_PLAIN, SW_W); _sk = SW_W / BASE.width
SLAM5 = 18
GL_AT = 44  # brýle začnou padat

class SwagDrop(El):
    def draw(self, canvas, f):
        k = f - GL_AT
        if k < 0:
            return
        g = self.img
        tx = W / 2 - _sw.width / 2 + EYES[0] * _sk - g.width / 2
        ty = H - _sw.height + 20 + EYES[1] * _sk - g.height * 0.42
        p = clamp(k / 22)
        y = -g.height + (ty + g.height) * ease_out(p) if p < 1 else ty
        canvas.alpha_composite(g, (int(tx), int(y)))

def s5_shake(c, f):
    t = f - (SLAM5 + 5)
    t2 = f - (GL_AT + 22)
    for tt, amp in ((t, 16), (t2, 8)):
        if 0 <= tt <= 10:
            dd = math.exp(-tt / 3.0)
            out = Image.new("RGBA", (W, H), DARK + (255,))
            out.paste(c, (int(amp * math.sin(tt * 2.7) * dd), int(amp * 0.7 * math.cos(tt * 3.1) * dd)))
            return out
    return c

v1 = text_img("Pořádná kapela.", 124, WHITE, w="ExtraBold")
v2 = rich_line([("Ať přijde i ", WHITE), ("mladá generace.", GL)], 60)
slam5 = Slam(_sw, W//2, 0, SLAM5)
S5 = TextScene(120, DARK, [label("VEČER", 2, y=270), El(v1, W//2, 420, 5), El(v2, W//2, 530, 12),
                           slam5, SwagDrop(glasses_img(GLASSES_W * _sk), 0, 0, 0),
                           El(text_img("DEAL WITH IT", 46, DARK, w="ExtraBold", pill=GL, pad=(26, 12), radius=10),
                              W//2, 700, GL_AT + 26, dur=8)],
               extra=beams, post=s5_shake)

# ---------- S6: pointa ----------
e1 = text_img("Ne jen folk.", 150, WHITE, w="ExtraBold")
e2 = text_img("Kultura je", 120, WHITE)
e3 = text_img("pro všechny.", 130, DARK, w="ExtraBold", pill=WHITE, pad=(44, 14))
ys = stack([e1, e2, e3], 640, gap=30)
minis = []
for i, (img, rot) in enumerate(((ST_PLAIN, -5), (ST_HAT, 4), (ST_PLAIN, -3), (ST_SWAG, 5))):
    m = tilted(fade_bottom(scaled(img, 400), 0.3), rot)
    minis.append(El(m, 170 + i * 247, 1520 - (50 if i % 2 else 0), 34 + i * 6))
S6 = TextScene(105, G, [El(e1, W//2, ys[0], 3), El(e2, W//2, ys[1], 16), El(e3, W//2, ys[2], 24, dur=11)] + minis)

# ---------- S7: závěr ----------
bar = rect_img(120, 10, G, 5)
SLAM7 = 60
def shake7(c, f):
    t = f - (SLAM7 + 5)
    if t < 0 or t > 10:
        return c
    dd = math.exp(-t / 3.0)
    out = Image.new("RGBA", (W, H), BG + (255,))
    out.paste(c, (int(14 * math.sin(t * 2.7) * dd), int(10 * math.cos(t * 3.1) * dd)))
    return out

S7 = TextScene(165, BG, [El(text_img("Přijďte k volbám", 104, DARK), W//2, 300, 3),
                         El(text_img("9.–10. října", 132, WHITE, w="ExtraBold", pill=G, pad=(56, 26)), W//2, 460, 12, dur=11),
                         El(text_img("Dejte hlas lidem,", 62, DARK, w="SemiBold"), W//2, 615, 26, "rise", dur=12),
                         El(text_img("kteří tu žijí.", 62, DARK, w="SemiBold"), W//2, 690, 30, "rise", dur=12),
                         El(bar, W//2, 785, 50, "grow_x", dur=10),
                         El(text_img("Karel Krupička", 96, DARK, w="ExtraBold"), W//2, 860, 54, dur=11),
                         El(text_img("www.dobrasprava.cz", 38, DARK + (140,), w="SemiBold"), W//2, 950, 66, "rise", dur=14),
                         Slam(scaled(ST_SWAG, 880), W//2, 0, SLAM7)],
               post=shake7)

SCENES = [S1, S2, S3, S4, S5, S6, S7]

if __name__ == "__main__":
    R.SCENES[:] = SCENES
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev = os.path.join(HERE, "prev2"); os.makedirs(prev, exist_ok=True)
    for k, fr in enumerate(R.frames()):
        p.stdin.write(fr.tobytes())
        if k % 15 == 0:
            fr.resize((270, 480)).save(os.path.join(prev, f"{k:04d}.png"))
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
