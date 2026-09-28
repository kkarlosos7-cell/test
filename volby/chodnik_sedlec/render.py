"""Chodník Sedlec – reels/story 1080x1920, 30 fps, bez hudby."""
import os, subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
W, H, FPS = 1080, 1920, 30
OUT = os.path.join(HERE, "chodnik_sedlec.mp4")

DARK = (27, 38, 59)       # #1B263B
G = (78, 159, 61)         # #4E9F3D
GD = (58, 122, 46)        # #3A7A2E
GL = (217, 234, 210)      # #D9EAD2
BG = (246, 250, 244)      # světlé pozadí s nádechem zelené
WHITE = (255, 255, 255)

FONTS = {k: os.path.join(HERE, "fonts", f"Inter-{k}.ttf") for k in ("Bold", "ExtraBold", "SemiBold")}
_fc = {}
def font(size, w="Bold"):
    key = (size, w)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(FONTS[w], size)
    return _fc[key]

# ---------- easing ----------
def clamp(x): return max(0.0, min(1.0, x))
def ease_out_back(p, s=1.9):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1
def ease_in_out(p): return 4*p*p*p if p < .5 else 1 - (-2*p + 2)**3 / 2
def ease_out(p): return 1 - (1 - p)**3

# ---------- prvky ----------
def text_img(text, size, color, w="Bold", pill=None, pad=(44, 22), radius=None, max_w=920):
    f = font(size, w)
    while f.getlength(text) + (2*pad[0] if pill else 0) > max_w:
        size -= 4
        f = font(size, w)
    asc, desc = f.getmetrics()
    tw = int(math.ceil(f.getlength(text)))
    th = asc + desc
    px, py = pad if pill else (0, 0)
    img = Image.new("RGBA", (tw + 2*px + 8, th + 2*py + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if pill:
        r = radius if radius is not None else 16
        d.rounded_rectangle([4, 4, tw + 2*px + 4, th + 2*py + 4], radius=r, fill=pill)
    d.text((px + 4, py + 4), text, font=f, fill=color)
    return img

def rich_line(parts, size, w="Bold", max_w=920):
    """parts = [(text, color), ...] v jednom řádku."""
    full = "".join(t for t, _ in parts)
    f = font(size, w)
    while f.getlength(full) > max_w:
        size -= 4
        f = font(size, w)
    asc, desc = f.getmetrics()
    img = Image.new("RGBA", (int(f.getlength(full)) + 8, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 4
    for t, c in parts:
        d.text((x, 4), t, font=f, fill=c)
        x += f.getlength(t)
    return img

def rect_img(w, h, color, radius=12):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=color)
    return img

class El:
    """Prvek, který 'vyskočí' (pop) v daném snímku scény."""
    def __init__(self, img, cx, cy, at, kind="pop", dur=10):
        self.img, self.cx, self.cy, self.at, self.kind, self.dur = img, cx, cy, at, kind, dur

    def draw(self, canvas, f):
        p = clamp((f - self.at) / self.dur)
        if p <= 0:
            return
        img = self.img
        if self.kind == "pop":
            s = 0.4 + 0.6 * ease_out_back(p)
            a = clamp(p * 2.5)
            dy = 0
        elif self.kind == "rise":
            s, a, dy = 1.0, clamp(p * 1.6), (1 - ease_out(p)) * 70
        elif self.kind == "grow_x":  # zleva doprava (podtržení)
            e = ease_out(p)
            wcut = max(1, int(img.width * e))
            img = img.crop((0, 0, wcut, img.height))
            canvas.alpha_composite(img, (int(self.cx - self.img.width / 2), int(self.cy - img.height / 2)))
            return
        if s != 1.0:
            img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
        if a < 1:
            al = img.getchannel("A").point(lambda v: int(v * a))
            img = img.copy(); img.putalpha(al)
        canvas.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2 + dy)))

# ---------- scény ----------
class TextScene:
    def __init__(self, n, bg, els, extra=None, post=None):
        self.n, self.bg, self.els, self.extra, self.post = n, bg, els, extra, post
    def render(self, f):
        c = Image.new("RGBA", (W, H), self.bg + (255,))
        if self.extra:
            self.extra(c, f)
        for e in self.els:
            e.draw(c, f)
        return self.post(c, f) if self.post else c

def location_tag(text, at, dark=False):
    """Malý štítek s lokací nahoře."""
    f = font(38, "SemiBold")
    tw = int(f.getlength(text))
    h = 76
    img = Image.new("RGBA", (tw + 110, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, tw + 104, h + 4], radius=14, fill=(WHITE if dark else GL))
    # špendlík
    cx, cy = 50, 4 + h // 2 - 4
    d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=G)
    d.polygon([(cx - 12, cy + 7), (cx + 12, cy + 7), (cx, cy + 26)], fill=G)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(WHITE if dark else GL))
    d.text((78, 4 + (h - 46) // 2), text, font=f, fill=DARK)
    return El(img, W // 2, 330, at, "rise")

def stack(lines, cy, gap=10):
    """Vrátí y-středy řádků vycentrované kolem cy."""
    hs = [im.height for im in lines]
    total = sum(hs) + gap * (len(hs) - 1)
    y = cy - total / 2
    out = []
    for h in hs:
        out.append(y + h / 2)
        y += h + gap
    return out

def sidewalk(canvas, f, y=1450, start=26, tiles=9):
    """Chodník, který se 'staví' dlaždice po dlaždici."""
    tw, th, gap = 104, 62, 10
    total = tiles * tw + (tiles - 1) * gap
    x0 = (W - total) // 2
    # obrubník
    p = ease_out(clamp((f - start + 6) / 14))
    kw = int(total * p)
    if kw > 0:
        canvas.alpha_composite(rect_img(kw, 16, DARK, 8), (x0, y + th + 14))
    for i in range(tiles):
        pi = clamp((f - start - i * 3) / 9)
        if pi <= 0:
            continue
        s = 0.3 + 0.7 * ease_out_back(pi)
        col = G if i % 2 == 0 else GD
        t = rect_img(max(1, int(tw * s)), max(1, int(th * s)), col, 12)
        cx = x0 + i * (tw + gap) + tw / 2
        canvas.alpha_composite(t, (int(cx - t.width / 2), int(y + th / 2 - t.height / 2)))

# S1 – úvod
l1 = text_img("Z Polní", 150, DARK)
l2 = text_img("na Tymákovskou.", 118, DARK)
l3 = text_img("S kočárkem.", 104, WHITE, pill=G)
ys = stack([l1, l2, l3], 960, gap=26)
S1 = TextScene(84, BG, [location_tag("Sedlec, Starý Plzenec", 2),
                        El(l1, W//2, ys[0], 4), El(l2, W//2, ys[1], 12), El(l3, W//2, ys[2], 28)])

# S2 – Chodník? Žádný.
m1 = text_img("Chodník?", 150, WHITE)
m2 = text_img("Žádný.", 210, GL, w="ExtraBold")
ys = stack([m1, m2], 940, gap=10)
S2 = TextScene(56, GD, [El(m1, W//2, ys[0], 4), El(m2, W//2, ys[1], 18, dur=11)])

# video
VID = sorted(os.path.join(HERE, "vid", x) for x in os.listdir(os.path.join(HERE, "vid")))
grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(grad)
for yy in range(H):
    a = 0
    if yy > 1100: a = int(150 * ((yy - 1100) / 820) ** 1.4)
    if yy < 420: a = int(110 * ((420 - yy) / 420) ** 1.5)
    gd.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
v_tag = text_img("Z Polní → Tymákovská", 44, WHITE, w="SemiBold", pill=G, pad=(34, 16))
v_pill = text_img("Jen silnice a auta.", 84, DARK, pill=WHITE, pad=(48, 26))

class VideoScene:
    n = len(VID)
    els = [El(v_tag, W//2, 330, 0, "rise", dur=8), El(v_pill, W//2, 1420, 3, dur=8)]
    def render(self, f):
        c = Image.open(VID[min(f, len(VID) - 1)]).convert("RGBA")
        c.alpha_composite(grad)
        for e in self.els:
            e.draw(c, f)
        return c
S_VID = VideoScene()

# S3 – Plzenec není jen centrum.
p1 = text_img("Plzenec", 160, DARK)
p2 = text_img("není jen", 160, DARK)
p3 = text_img("centrum.", 160, GD)
ys = stack([p1, p2, p3], 930, gap=4)
under = rect_img(p3.width - 20, 22, G, 11)
S3 = TextScene(72, GL, [El(p1, W//2, ys[0], 3), El(p2, W//2, ys[1], 10), El(p3, W//2, ys[2], 17),
                        El(under, W//2, ys[2] + p3.height/2 + 20, 30, "grow_x", dur=12)])

# S4 – Chodníky potřebujeme i u nás v Sedlci.
c1 = text_img("Chodníky", 150, DARK)
c2 = text_img("potřebujeme", 132, DARK)
c3 = text_img("i u nás", 132, DARK)
c4 = text_img("v Sedlci.", 150, WHITE, w="ExtraBold", pill=G, pad=(46, 14))
ys = stack([c1, c2, c3, c4], 860, gap=8)
S4 = TextScene(84, BG, [El(c1, W//2, ys[0], 3), El(c2, W//2, ys[1], 9), El(c3, W//2, ys[2], 15),
                        El(c4, W//2, ys[3] + 16, 24, dur=11)],
               extra=lambda c, f: sidewalk(c, f, y=1400, start=34))

# S5 – Chci to změnit.
k1 = text_img("Chci to", 170, WHITE, w="ExtraBold")
k2 = text_img("změnit.", 170, GL, w="ExtraBold")
k3 = text_img("Chodník z Polní na Tymákovskou", 68, WHITE, w="SemiBold")
k4 = rich_line([("je pro mě ", WHITE), ("priorita.", GL)], 68, w="Bold")
ys = stack([k1, k2], 800, gap=0)
S5 = TextScene(105, GD, [El(k1, W//2, ys[0], 3), El(k2, W//2, ys[1], 11),
                         El(k3, W//2, 1140, 26, "rise", dur=12), El(k4, W//2, 1230, 32, "rise", dur=12)])

# S6 – výzva k volbám
f1 = text_img("Přijďte k volbám", 104, DARK)
f2 = text_img("9.–10. října", 132, WHITE, w="ExtraBold", pill=G, pad=(56, 26))
f3 = text_img("Dejte hlas lidem, kteří tudy", 62, DARK, w="SemiBold")
f4 = text_img("chodí každý den.", 62, DARK, w="SemiBold")
bar = rect_img(120, 10, G, 5)
f5 = text_img("Karel Krupička", 96, DARK, w="ExtraBold")
f6 = text_img("www.dobrasprava.cz", 38, DARK + (140,), w="SemiBold")
_st = Image.open(os.path.join(HERE, "sticker.png")).convert("RGBA")
STW = 880
sticker = _st.resize((STW, int(_st.height * STW / _st.width)), Image.LANCZOS)

class Slam(El):
    """Sticker 'plácne' na obrazovku a zatřese se."""
    def draw(self, canvas, f):
        k = f - self.at
        if k < 0:
            return
        IN = 6
        if k < IN:
            p = ease_out((k + 1) / IN)
            s, a, rot, dx = 1.8 - 0.8 * p, clamp(p * 1.5), -8 * (1 - p), 0
        else:
            t = k - IN
            decay = math.exp(-t / 5.0)
            s = 1 + 0.035 * math.sin(t * 1.3) * decay
            rot = 5.0 * math.sin(t * 1.9) * decay
            dx = 18 * math.sin(t * 2.4) * decay
            a = 1
        img = self.img
        if s != 1:
            img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
        if abs(rot) > 0.05:
            img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
        if a < 1:
            img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        cy = H - self.img.height / 2 + 20
        canvas.alpha_composite(img, (int(W / 2 - img.width / 2 + dx), int(cy - img.height / 2)))

SLAM_AT = 60

def shake(c, f):
    """Krátký otřes celé obrazovky při dopadu stickeru."""
    t = f - (SLAM_AT + 5)
    if t < 0 or t > 10:
        return c
    d = math.exp(-t / 3.0)
    ox, oy = int(14 * math.sin(t * 2.7) * d), int(10 * math.cos(t * 3.1) * d)
    out = Image.new("RGBA", (W, H), BG + (255,))
    out.paste(c, (ox, oy))
    return out

S6 = TextScene(165, BG, [El(f1, W//2, 300, 3), El(f2, W//2, 460, 12, dur=11),
                         El(f3, W//2, 615, 26, "rise", dur=12), El(f4, W//2, 690, 30, "rise", dur=12),
                         El(bar, W//2, 785, 50, "grow_x", dur=10), El(f5, W//2, 860, 54, dur=11),
                         El(f6, W//2, 950, 66, "rise", dur=14),
                         Slam(sticker, W//2, 0, SLAM_AT)],
               post=shake)

SCENES = [S1, S2, S_VID, S3, S4, S5, S6]
TR = 8  # snímky přechodu (nová scéna vyjede zespodu)

def frames():
    for i, sc in enumerate(SCENES):
        prev_last = SCENES[i - 1].render(SCENES[i - 1].n - 1) if i else None
        for f in range(sc.n):
            cur = sc.render(f)
            if prev_last is not None and f < TR:
                e = ease_in_out((f + 1) / (TR + 1))
                c = Image.new("RGBA", (W, H))
                c.paste(prev_last, (0, int(-e * H * 0.35)))
                c.paste(cur, (0, int((1 - e) * H)))
                cur = c
            yield cur.convert("RGB")

if __name__ == "__main__":
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    cmd = [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev_dir = os.path.join(HERE, "preview"); os.makedirs(prev_dir, exist_ok=True)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
        if k % 15 == 0:
            fr.resize((270, 480)).save(os.path.join(prev_dir, f"{k:04d}.png"))
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
