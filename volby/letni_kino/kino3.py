"""Letní kino + spolky, verze 3: kino → udělal ho spolek → spolků je víc → podpora má být běžná."""
import os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kino2 as V2
import kino as K1
import audio as A
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, El, TextScene)
from kino2 import Words, S0, S4, SLAM4, sport_img, beep
from kino import outline, NIGHT, POP

HERE = K1.HERE
OUT = os.path.join(HERE, "letni_kino.mp4")
GOLD = (244, 206, 96)

# ---------- přiťuknutí sektem ----------
def flute(s=1.0):
    w, h = int(120 * s), int(330 * s)
    img = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = (w + 40) / 2
    top, bowl_b = 20, 20 + h * .55
    d.polygon([(cx - w * .36, top), (cx + w * .36, top), (cx + w * .2, bowl_b), (cx - w * .2, bowl_b)], fill=(235, 242, 248))
    d.polygon([(cx - w * .31, top + h * .1), (cx + w * .31, top + h * .1), (cx + w * .19, bowl_b - 6), (cx - w * .19, bowl_b - 6)], fill=GOLD)
    r = random.Random(3)
    for _ in range(7):
        bx, by = cx + r.uniform(-w * .18, w * .18), r.uniform(top + h * .15, bowl_b - 20)
        d.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=(255, 246, 210))
    d.rectangle([cx - 5, bowl_b, cx + 5, 20 + h * .92], fill=(220, 230, 238))
    d.ellipse([cx - w * .3, 20 + h * .9, cx + w * .3, 20 + h], fill=(220, 230, 238))
    return outline(img, 8)
FLUTE = flute(1.35)
FLUTE_S = flute(0.85)
CLINK_AT = 34

class Clink(El):
    """Dvě skleničky sektu přijedou k sobě a přiťuknou si."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 10))
        hit = CLINK_AT - self.at
        if k < hit:
            q = ease_in_out(clamp((k - 6) / (hit - 6)))
        else:
            q = 1 - 0.12 * math.sin(clamp((k - hit) / 6) * math.pi)
        gap = 110 * (1 - q) + 30
        for side in (-1, 1):
            img = FLUTE_S.rotate(-side * (8 + 10 * q), expand=True, resample=Image.BICUBIC)
            s = 0.4 + 0.6 * p
            img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
            c.alpha_composite(img, (int(self.cx + side * gap - img.width / 2), int(self.cy - img.height / 2)))
        t = k - hit
        if 0 <= t < 14:   # jiskra
            d = ImageDraw.Draw(c)
            a = 1 - t / 14; r = 30 + t * 6
            x, y = self.cx + 105, self.cy - 120
            for i in range(8):
                ang = i * math.pi / 4
                d.line([(x + math.cos(ang) * r * .4, y + math.sin(ang) * r * .4), (x + math.cos(ang) * r, y + math.sin(ang) * r)],
                       fill=(255, 240, 180, int(255 * a)), width=7)

import armsticker as AS
ME_GLASS = AS.ArmSticker(620, FLUTE, gscale=1.0)
ME_IN = 8

class MeCheers(El):
    """Já se skleničkou: vyjedu zespodu a kývu s ní na zdraví (s cinknutím, když si ťukají lidé v záběru)."""
    def draw(self, c, f):
        k = f - ME_IN
        if k < 0:
            return
        dy = (1 - ease_out_back(clamp(k / 12), 1.2)) * 900
        a = -7 + 7 * math.sin((f - CLINK_AT) * .45 + math.pi / 2)
        img = ME_GLASS.image(a)
        x0, y0 = self.cx, int(H - img.height + 30 + dy)
        c.alpha_composite(img, (x0, y0))
        t = f - CLINK_AT
        if 0 <= t < 14:   # jiskra u skleničky
            d = ImageDraw.Draw(c)
            aa = 1 - t / 14; r = 30 + t * 6
            gx = x0 + AS.GRIP[0] * ME_GLASS.s + 75
            gy = y0 + (AS.GRIP[1] + ME_GLASS.off) * ME_GLASS.s - 250
            for i in range(8):
                ang = i * math.pi / 4
                d.line([(gx + math.cos(ang) * r * .4, gy + math.sin(ang) * r * .4), (gx + math.cos(ang) * r, gy + math.sin(ang) * r)],
                       fill=(255, 240, 180, int(255 * aa)), width=7)

class Clip:
    n = len(K1.VID)
    els = [Words("Letní kino.", 300, 2, 100), Words("*V_Sedlci.*", 420, 10, 100),
           MeCheers(None, 330, 0, 0)]
    def render(self, f):
        c = Image.open(K1.VID[min(f, self.n - 1)]).convert("RGBA")
        c.alpha_composite(K1.grad)
        for e in self.els:
            e.draw(c, f)
        return c
S1 = Clip()

# ---------- S2: udělali ho lidé ze spolku ----------
S_ORG = TextScene(105, BG, [V2.Kernels(3),
                            Words("Udělali ho", 640, 3, 100), Words("lidé ze *spolku.*", 770, 12, 110),
                            Words("Ve svém volném čase.", 960, 40, 76)])

# ---------- S3: spolků je u nás víc – velké ikonky ----------
KINDS = ["cinema", "foot", "hall", "tennis", "canoe", "gym"]
TILE = 330

class Grid(El):
    def draw(self, c, f):
        for i, kd in enumerate(KINDS):
            k = f - self.at - i * 5
            if k < 0:
                continue
            col, row = i % 3, i // 3
            x = W / 2 + (col - 1) * (TILE + 16)
            y = 880 + (row - .5) * (TILE + 16)
            p = ease_out_back(clamp(k / 10))
            s = 0.3 + 0.7 * p
            if kd == "hall":
                s *= 1 + 0.05 * math.sin(k * .25)
            img = sport_img(kd, f).resize((max(2, int(TILE * s)), max(2, int(TILE * s))), Image.BILINEAR)
            img = img.rotate((-3, 2, -2, 3, -3, 2)[i], expand=True, resample=Image.BICUBIC)
            c.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))

S_GRID = TextScene(150, NIGHT, [Words("A takových spolků", 300, 3, 92), Words("je u nás *víc.*", 420, 12, 100),
                                Grid(None, 0, 0, 24),
                                Words("Kulturních", 1330, 70, 96), Words("i *sportovních.*", 1450, 80, 100)])

# ---------- S4: podpora má být běžná ----------
S_MSG = TextScene(140, BG, [Words("Jejich podpora", 470, 3, 100), Words("nemá být *výjimka.*", 590, 12, 100),
                            Words("Má být *běžná.*", 790, 40, 120),
                            Words("Město má být", 1040, 72, 92), Words("*partner.*", 1170, 82, 130)])

# ---------- závěr: ukazuju rukou na vstupenku ----------
ME_POINT = AS.ArmSticker(600)
class MePoint(El):
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        dy = (1 - ease_out_back(clamp(k / 12), 1.3)) * 1000
        a = -8 + 7 * math.sin(k * .22) if k > 12 else -15
        img = ME_POINT.image(a)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(H - img.height + 30 + dy)))
from render import Slam as _Slam
END_ELS = [e for e in S4.els if not isinstance(e, (_Slam, K1.Bounce))]
END_ELS += [MePoint(None, 790, 0, SLAM4), K1.Bounce(POP, 190, 1650, SLAM4 + 16, -10)]
S_END = TextScene(S4.n, BG, END_ELS, post=S4.post)

SCENES = [(S0, False), (S1, False), (S_ORG, True), (S_GRID, True), (S_MSG, True), (S4, True)]
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

def fx_glass():
    n = int(0.8 * A.SR); t = A.t_(n)
    return sum(a * np.sin(2 * np.pi * fq * t) * np.exp(-t / d) for fq, a, d in
               ((2637, .6, .35), (3951, .35, .25), (5274, .2, .15), (6645, .12, .1)))

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc, _ in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    for j in range(int(1.2 * 16)):
        out.add(j / 16, A.hat(), 0.4)
    for j in range(3):
        out.add(j * 12 / FPS, beep(880 if j < 2 else 1320), 0.8)
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
        out.add(st[1], kz / (np.max(np.abs(kz)) + 1e-9), 0.6)
    except Exception as e:
        print("zvuk z videa:", e)
    out.add(st[1] + CLINK_AT / FPS, fx_glass(), 0.9)
    out.add(st[1] + ME_IN / FPS, A.fx_whoosh(0.4), 0.5)
    for a in (2, 10, 14):
        out.add(st[1] + a / FPS, K1.fx_pop(), 0.5)
    for a in (3, 12, 40):
        out.add(st[2] + a / FPS, K1.fx_pop(), 0.5)
    for a in [3, 12, 70, 80] + [24 + i * 5 for i in range(6)]:
        out.add(st[3] + a / FPS, K1.fx_pop(), 0.45)
    for a in (3, 12, 40, 72, 82):
        out.add(st[4] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[4] + 82 / FPS, A.fx_ding(), 0.7)
    out.add(st[5] + 8 / FPS, A.fx_whoosh(0.4), 0.8)
    out.add(st[5] + 20 / FPS, A.fx_impact(), 0.5)
    out.add(st[5] + (SLAM4 + 5) / FPS - 0.02, A.fx_impact(), 1.0)
    out.add(st[5] + (SLAM4 + 10) / FPS, K1.fx_pop(), 0.6)
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
    AUD = os.path.join(HERE, "kino3_mix.wav")
    build_audio(AUD)
    cmd = [K1.R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
