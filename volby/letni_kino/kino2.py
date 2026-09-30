"""Letní kino + spolky, verze 2 (filmová): odpočet, video, texty, filmový pás se sporty, vstupenka."""
import os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kino as K1
import audio as A
import festival as FE
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, rect_img, El, TextScene, Slam)
from kino import outline, shake_post, NIGHT, POP

HERE = K1.HERE
OUT = os.path.join(HERE, "letni_kino.mp4")

def back(p):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
def eo(p): return 1 - (1 - p) ** 3

# ---------- slova ve stylu „Městský Facebook“ ----------
def word_img(w, hl, size):
    f = font(size, "ExtraBold")
    tw = f.getlength(w); asc, desc = f.getmetrics()
    px, pt, pb = int(.26 * size), int(.08 * size), int(.12 * size)
    wi, hi = int(tw + 2 * px), int(asc + desc * 0.4 + pt + pb)
    img = Image.new("RGBA", (wi + 60, hi + 70), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 42, 30 + wi, 42 + hi], radius=int(.2 * size), fill=(0, 0, 0, 60))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([30, 30, 30 + wi, 30 + hi], radius=int(.2 * size), fill=G if hl else WHITE)
    d.text((30 + px, 30 + pt - 2), w, font=f, fill=WHITE if hl else DARK)
    return img

class Words(El):
    def __init__(self, line, y, t0, size=96, gap=4):
        super().__init__(None, W // 2, y, t0)
        self.ws = [(word_img(w.strip("*").replace("_", " "), w.startswith("*"), size), w.startswith("*")) for w in line.split(" ")]
        self.gap = gap
        total = sum(im.width - 60 for im, _ in self.ws) + 17 * (len(self.ws) - 1)
        x = W / 2 - total / 2
        self.xs = []
        for im, _ in self.ws:
            self.xs.append(x + (im.width - 60) / 2); x += im.width - 60 + 17
    def draw(self, c, f):
        for i, ((im, hl), cx) in enumerate(zip(self.ws, self.xs)):
            p = clamp((f - self.at - i * self.gap) / 9)
            if p <= 0:
                continue
            s = 0.35 + 0.65 * back(p)
            img = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
            if hl:
                img = img.rotate(-2.5 * eo(p), expand=True, resample=Image.BICUBIC)
            a = clamp(p * 3)
            if a < 1:
                img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
            c.alpha_composite(img, (int(cx - img.width / 2), int(self.cy + (1 - eo(p)) * 60 - img.height / 2)))

# ---------- S0: filmový odpočet 3-2-1 ----------
LEADER = (58, 62, 70)
class Countdown:
    n = 36
    def render(self, f):
        c = Image.new("RGBA", (W, H), LEADER + (255,))
        d = ImageDraw.Draw(c)
        num = 3 - f // 12
        p = (f % 12) / 12
        cx, cy, r = W // 2, H // 2, 360
        # výseč, která obíhá
        d.pieslice([cx - 900, cy - 900, cx + 900, cy + 900], -90, -90 + 360 * p, fill=(88, 94, 104))
        d.line([(0, cy), (W, cy)], fill=(30, 32, 36), width=4)
        d.line([(cx, 0), (cx, H)], fill=(30, 32, 36), width=4)
        for rr in (r, r - 40):
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=WHITE, width=10)
        d.text((cx, cy), str(num), font=font(420, "ExtraBold"), fill=WHITE, anchor="mm")
        rnd = random.Random(f)
        for _ in range(3):   # škrábance a zrno
            x = rnd.uniform(0, W)
            d.line([(x, 0), (x + rnd.uniform(-20, 20), H)], fill=(200, 200, 200, 90), width=2)
        for _ in range(40):
            x, y = rnd.uniform(0, W), rnd.uniform(0, H)
            d.ellipse([x, y, x + 4, y + 4], fill=(20, 20, 20))
        return c
S0 = Countdown()

# ---------- S1: video ----------
class Clip:
    n = len(K1.VID)
    els = [Words("Letní kino.", 300, 2, 100), Words("*V_Sedlci.*", 420, 10, 100),
           K1.Bounce(POP, 880, 1600, 26, 8)]
    def render(self, f):
        c = Image.open(K1.VID[min(f, self.n - 1)]).convert("RGBA")
        c.alpha_composite(K1.grad)
        for e in self.els:
            e.draw(c, f)
        return c
S1 = Clip()

# ---------- S2: výjimka → běžná věc ----------
class Kernels(El):
    """Jemně padající popcorn v pozadí."""
    def __init__(self, seed=1, n=16):
        super().__init__(None, 0, 0, 0)
        r = random.Random(seed)
        self.k = [(r.uniform(40, W - 40), r.uniform(-400, H), r.uniform(3, 6), r.uniform(18, 30), r.uniform(0, 6)) for _ in range(n)]
    def draw(self, c, f):
        d = ImageDraw.Draw(c)
        for x, y0, v, rr, ph in self.k:
            y = (y0 + v * f) % (H + 200) - 100
            x2 = x + 20 * math.sin(f * .05 + ph)
            d.ellipse([x2 - rr - 5, y - rr - 5, x2 + rr + 5, y + rr + 5], fill=(236, 242, 232))
            d.ellipse([x2 - rr, y - rr, x2 + rr, y + rr], fill=(255, 246, 214))

S2 = TextScene(135, BG, [Kernels(3),
                         Words("Takové večery", 560, 3, 92), Words("nemají být", 680, 10, 92),
                         Words("*výjimkou.*", 800, 18, 110),
                         Words("Kultura má být", 1010, 50, 92), Words("*běžná.*", 1130, 58, 110),
                         Words("A pro všechny.", 1290, 76, 80)])

# ---------- S3: filmový pás se sporty ----------
FR_W, FR_H, FR_GAP = 470, 470, 40
STRIP_Y0, STRIP_Y1 = 600, 1200

def cinema_frame(k):
    """Rámeček s malým letním kinem (plátno + hlavy diváků)."""
    img = K1.vignette()
    d = ImageDraw.Draw(img)
    d.rectangle([15, 15, 395, 395], fill=NIGHT)
    r = random.Random(1)
    for _ in range(18):
        x, y = r.uniform(20, 390), r.uniform(20, 160)
        d.ellipse([x, y, x + 4, y + 4], fill=WHITE)
    fl = 200 + int(40 * math.sin(k * .7))
    d.rectangle([80, 70, 330, 220], fill=(fl, fl, 230))
    d.rectangle([80, 70, 330, 220], outline=WHITE, width=5)
    for i in range(7):
        x = 40 + i * 55
        d.ellipse([x, 280, x + 50, 330], fill=(40, 48, 66))
        d.rounded_rectangle([x - 6, 318, x + 56, 400], radius=20, fill=(40, 48, 66))
    return img

def sport_img(kind, k):
    """Vykreslí animovaný sport do samostatného obrázku (bez natočení)."""
    cls = {"foot": K1.Football, "tennis": K1.Tennis, "gym": K1.Gym}.get(kind)
    canvas = Image.new("RGBA", (520, 520), (0, 0, 0, 0))
    if kind == "canoe":
        el = _canoe
    elif kind == "cinema":
        return cinema_frame(k)
    else:
        el = cls(None, 0, 0, 0)
    el.cx, el.cy, el.at, el.tilt = 260, 260, -1000, 0
    el.draw(canvas, k + 1000)
    return canvas.crop((260 - 205, 260 - 205, 260 + 205, 260 + 205))
_canoe = K1.Canoe(0, 0, 0)

KINDS = ["foot", "canoe", "tennis", "gym", "cinema"] * 2

class FilmStrip(El):
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = eo(clamp(k / 12))
        y0 = STRIP_Y0 + (1 - p) * 700
        strip = Image.new("RGBA", (W + 200, STRIP_Y1 - STRIP_Y0), (14, 16, 20, 255))
        sd = ImageDraw.Draw(strip)
        off = (k * 11) % 60
        for x in range(-60, W + 200, 60):   # perforace
            xx = x - off
            sd.rounded_rectangle([xx + 12, 22, xx + 44, 52], radius=6, fill=(236, 240, 232))
            sd.rounded_rectangle([xx + 12, STRIP_Y1 - STRIP_Y0 - 52, xx + 44, STRIP_Y1 - STRIP_Y0 - 22], radius=6, fill=(236, 240, 232))
        scroll = k * 11
        for i, kind in enumerate(KINDS):
            x = 60 + i * (FR_W + FR_GAP) - scroll
            if x > W + 200 or x + FR_W < -50:
                continue
            fr = sport_img(kind, k).resize((FR_W, FR_H), Image.BILINEAR)
            strip.alpha_composite(fr, (int(x), (STRIP_Y1 - STRIP_Y0 - FR_H) // 2))
        strip = strip.rotate(-3, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(strip, (-100 - (strip.width - W - 200) // 2, int(y0 - (strip.height - (STRIP_Y1 - STRIP_Y0)) / 2)))

S3 = TextScene(210, NIGHT, [Words("Za tím vším", 300, 3, 92), Words("jsou *spolky.*", 420, 11, 100),
                            FilmStrip(None, 0, 0, 20),
                            Words("Jejich podpora je zásadní.", 1330, 90, 66),
                            Words("Město má být", 1470, 118, 84), Words("*jejich_partner.*", 1590, 128, 96)],
               extra=None)

# ---------- S4: vstupenka ----------
def ticket():
    w, h = 920, 480
    img = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 30, w + 20, h + 30], radius=30, fill=(27, 38, 59, 60))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    t = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=30, fill=WHITE)
    d.rounded_rectangle([0, 0, 230, h - 1], radius=30, fill=G)
    d.rectangle([200, 0, 230, h - 1], fill=G)
    for y in range(20, h - 10, 34):   # perforace
        d.ellipse([222, y, 238, y + 16], fill=(236, 240, 232))
    for cy in (0, h):                 # výřezy
        d.ellipse([205, cy - 28, 261, cy + 28], fill=(0, 0, 0, 0))
    st = Image.new("RGBA", (h, 230), (0, 0, 0, 0))
    ImageDraw.Draw(st).text((h / 2, 115), "VSTUP VOLNÝ", font=font(50, "ExtraBold"), fill=WHITE, anchor="mm")
    t.alpha_composite(st.rotate(90, expand=True), (0, 0))
    d.text((290, 60), "VSTUPENKA", font=font(40, "ExtraBold"), fill=G)
    d.text((290, 115), "Komunální volby", font=font(66, "ExtraBold"), fill=DARK)
    d.text((290, 205), "9.–10. října", font=font(100, "ExtraBold"), fill=GD)
    d.text((290, 360), "Starý Plzenec · Sedlec", font=font(46, "SemiBold"), fill=(96, 108, 128))
    img.alpha_composite(t, (20, 20))
    return outline(img, 10)

class TicketIn(El):
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 12), 1.3)
        y = self.cy - (1 - p) * 1300
        r = -3 * p + 20 * (1 - p)
        img = self.img.rotate(r, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(y - img.height / 2)))

SLAM4 = 64
bar = rect_img(120, 10, G, 5)
ME = FE.scaled(FE.ST_PLAIN, 800)
S4 = TextScene(180, BG, [Words("Přijďte k volbám!", 250, 3, 84),
                         TicketIn(ticket(), W // 2, 600, 8),
                         El(text_img("Dejte hlas člověku,", 62, DARK, w="SemiBold"), W // 2, 915, 30, "rise"),
                         El(text_img("který podpoří spolky.", 62, GD, w="ExtraBold"), W // 2, 990, 36, "rise"),
                         El(text_img("Karel Krupička", 92, DARK, w="ExtraBold"), W // 2, 1100, 50, dur=11),
                         El(text_img("www.dobrasprava.cz", 38, DARK + (140,), w="SemiBold"), W // 2, 1180, 58, "rise"),
                         Slam(ME, W // 2, 0, SLAM4),
                         K1.Bounce(POP, 880, 1640, SLAM4 + 10, 10)],
               post=shake_post([SLAM4 + 5], BG))

SCENES = [(S0, False), (S1, False), (S2, True), (S3, True), (S4, True)]
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
def beep(fq=1000, d=0.12):
    n = int(d * A.SR); t = A.t_(n)
    return np.sin(2 * np.pi * fq * t) * np.minimum(1, (n - np.arange(n)) / 400) * 0.6

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc, _ in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    # odpočet: projektor + pípnutí
    for j in range(int(1.2 * 16)):
        out.add(j / 16, A.hat(), 0.4)
    for j in range(3):
        out.add(j * 12 / FPS, beep(880 if j < 2 else 1320), 0.8)
    # hudba od videa dál (během videa tišeji + zvuk z kina)
    mus = A.seg_pop(total - st[1] + 0.2, 0.6)[: int((total - st[1]) * SR)]
    env = np.ones(len(mus)); env[: int((st[2] - st[1]) * SR)] = 0.4
    k_ = int(0.2 * SR); env = np.convolve(env, np.ones(k_) / k_, mode="same")
    out.add(st[1], mus * env)
    out.add(st[1], A.crash(), 0.6)
    try:
        _, kz = A.wavfile.read(os.path.join(HERE, "kino_audio.wav"))
        kz = kz.astype(np.float64) / 32768
        if kz.ndim > 1: kz = kz.mean(1)
        fi = int(0.1 * SR); kz[-fi:] *= np.linspace(1, 0, fi)
        out.add(st[1], kz / (np.max(np.abs(kz)) + 1e-9), 0.7)
    except Exception as e:
        print("zvuk z videa:", e)
    for a in (2, 10, 26):
        out.add(st[1] + a / FPS, K1.fx_pop(), 0.6)
    for a in (3, 10, 18, 50, 58, 76):
        out.add(st[2] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[3] + 20 / FPS, A.fx_whoosh(0.5), 0.8)
    for k in range(30, 200, 9):   # projektor pod filmovým pásem
        out.add(st[3] + k / FPS, A.hat(), 0.18)
    for a in (3, 11, 90, 118, 128):
        out.add(st[3] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[3] + 128 / FPS, A.fx_ding(), 0.7)
    out.add(st[4] + 8 / FPS, A.fx_whoosh(0.4), 0.8)
    out.add(st[4] + 20 / FPS, A.fx_impact(), 0.5)
    out.add(st[4] + (SLAM4 + 5) / FPS - 0.02, A.fx_impact(), 1.0)
    out.add(st[4] + (SLAM4 + 10) / FPS, K1.fx_pop(), 0.6)
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
    AUD = os.path.join(HERE, "kino2_mix.wav")
    build_audio(AUD)
    cmd = [K1.R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
