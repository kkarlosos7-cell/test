"""Reels na volební den: odvolit trvá kratší dobu než vypít jedno pivo. 1080x1920, 30 fps, se zvukem."""
import os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import audio as A
import kino as K1
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, El, TextScene)
from kino2 import Words
from kino import outline, shake_post
import toaststicker as TS
from podzim import logo_sticker
from rozpocet2 import Pop

HERE = R.HERE
OUT = os.path.join(HERE, "volby_pivo.mp4")
LOGO = logo_sticker()
GREY = (110, 122, 140)
BEER = (242, 178, 44)
BEER_D = (214, 140, 24)
FOAM = (255, 252, 240)

# ---------- fotka (bez černých pruhů) ----------
PHOTO = Image.open(os.path.join(HERE, "hlas", "pivo.png")).convert("RGB").crop((0, 486, 1170, 2046))
_s = H / PHOTO.height * 1.02
PHOTO = PHOTO.resize((int(PHOTO.width * _s), int(PHOTO.height * _s)), Image.LANCZOS)
GRAD = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_gd = ImageDraw.Draw(GRAD)
for y in range(0, 1000):
    _gd.line([0, y, W, y], fill=(10, 16, 28, int(170 * (1 - y / 1000) ** 1.4)))

def photo_bg(f, n):
    z = 1 + 0.08 * f / n
    pw, ph = int(PHOTO.width * z), int(PHOTO.height * z)
    im = PHOTO.resize((pw, ph), Image.BILINEAR)
    x0 = (pw - W) // 2 + int(30 * f / n)
    y0 = (ph - H) // 2
    c = im.crop((x0, y0, x0 + W, y0 + H)).convert("RGBA")
    c.alpha_composite(GRAD)
    return c

# ---------- kreslený půllitr ----------
def mug(s=1.0, level=1.0, handle_center=False):
    bw, bh = int(150 * s), int(200 * s)
    hw = int(60 * s)
    pad = int(20 * s)
    foam_h = int(44 * s)
    w = bw + hw + 2 * pad
    body_x = pad + hw if handle_center else pad
    img = Image.new("RGBA", (w + (bw if handle_center else 0), bh + foam_h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top = pad + foam_h
    # ucho
    hx = body_x - hw if handle_center else body_x + bw - 10
    if handle_center:
        d.rounded_rectangle([hx, top + bh * .18, body_x + 20, top + bh * .78], radius=int(30 * s), outline=(225, 235, 242), width=int(18 * s))
    else:
        d.rounded_rectangle([body_x + bw - 20, top + bh * .18, body_x + bw + hw, top + bh * .78], radius=int(30 * s),
                            outline=(225, 235, 242), width=int(18 * s))
    # sklo + pivo
    d.rounded_rectangle([body_x, top, body_x + bw, top + bh], radius=int(22 * s), fill=(235, 242, 248))
    ly = top + 8 * s + (bh - 16 * s) * (1 - level)
    if level > 0.02:
        d.rounded_rectangle([body_x + 9 * s, ly, body_x + bw - 9 * s, top + bh - 9 * s], radius=int(16 * s), fill=BEER)
        for i in range(3):   # žebrování půllitru
            x = body_x + bw * (.27 + .23 * i)
            d.rounded_rectangle([x - 9 * s, max(ly + 14 * s, top + 40 * s), x + 9 * s, top + bh - 30 * s], radius=int(9 * s), fill=BEER_D)
        r = random.Random(4)
        for _ in range(8):
            bx, by = body_x + r.uniform(.15, .85) * bw, r.uniform(max(ly + 10 * s, top + 20 * s), top + bh - 20 * s)
            d.ellipse([bx - 4 * s, by - 4 * s, bx + 4 * s, by + 4 * s], fill=(255, 230, 160))
    if level > 0.6:   # pěna
        fy = ly
        for i in range(5):
            cx = body_x + bw * (.1 + .2 * i)
            d.ellipse([cx - 28 * s, fy - 34 * s, cx + 28 * s, fy + 16 * s], fill=FOAM)
        d.rectangle([body_x + 4 * s, fy - 6 * s, body_x + bw - 4 * s, fy + 16 * s], fill=FOAM)
    return outline(img, max(4, int(8 * s)))

def mug_for_hand(s):
    """Půllitr s uchem uprostřed obrázku v 70 % výšky – tak ho ToastSticker vloží do prstů."""
    m = mug(s, handle_center=True)
    hy = m.height * 0.5             # střed ucha
    hgt = int(hy / 0.70)
    cx = int(30 * s + 20 * s)       # x ucha
    w2 = max(cx, m.width - cx) * 2
    out = Image.new("RGBA", (w2, max(hgt, m.height)), (0, 0, 0, 0))
    out.alpha_composite(m, (w2 // 2 - cx, int(hgt * .70 - hy)))
    return out

def ballot(s=1.0):
    w, h = int(190 * s), int(170 * s)
    img = Image.new("RGBA", (w + 40, h + 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([20 + w * .2, 20, 20 + w * .8, 20 + h * .6], fill=WHITE)
    d.line([(20 + w * .35, 20 + h * .3), (20 + w * .47, 20 + h * .42), (20 + w * .66, 20 + h * .14)], fill=G, width=int(12 * s))
    d.rounded_rectangle([20, 20 + h * .45, 20 + w, 20 + h + 40], radius=int(16 * s), fill=DARK)
    d.rounded_rectangle([20 + w * .15, 20 + h * .45 - 6, 20 + w * .85, 20 + h * .45 + 10], radius=6, fill=(12, 18, 30))
    return outline(img, 7)

# ---------- S1: fotka + hlavní věta ----------
S1N = 120
S1W = [Words("Dnes jsou *volby.*", 230, 6, 104),
       Words("Odvolit trvá", 430, 40, 92), Words("*kratší_dobu*", 545, 48, 104),
       Words("než vypít", 660, 58, 92), Words("*jedno_pivo.*", 780, 66, 110)]
class Photo:
    n = S1N
    def render(self, f):
        c = photo_bg(f, self.n)
        for w in S1W:
            w.draw(c, f)
        return c
S1 = Photo()

# ---------- S2: závod ----------
BALLOT = ballot(1.05)
MUG = mug(0.85)
RACE_N = 140
V_DONE, P_LEN = 46, 150      # volby hotové za 46 snímků, pivo by trvalo ~150
class Race:
    """Oba pruhy startují naráz: volby doběhnou plynule do cíle, pivo se mezitím upije jen trochu."""
    n = RACE_N
    title = Words("Kdo bude *rychlejší?*", 300, 4, 90)
    win = Words("*Volby_vyhrávají.*", 1400, 72, 120)
    START = 24
    def bar(self, d, x0, x1, y, p, col):
        d.rounded_rectangle([x0, y - 36, x1, y + 36], radius=36, fill=(222, 230, 222))
        w = (x1 - x0) * p
        if w <= 1:
            return
        if w < 72:   # malý začátek jako kolečko, ať pruh „nevyskočí“
            r = w / 2
            d.ellipse([x0, y - r, x0 + w, y + r], fill=col)
        else:
            d.rounded_rectangle([x0, y - 36, x0 + w, y + 36], radius=36, fill=col)
    def render(self, f):
        c = Image.new("RGBA", (W, H), BG + (255,))
        self.title.draw(c, f)
        d = ImageDraw.Draw(c)
        k = f - self.START
        pv = ease_in_out(clamp(k / V_DONE))                 # volby: plynule do konce
        pb = 0.32 * ease_out(clamp(k / (V_DONE + 40)))      # pivo: jen kousek
        done = k >= V_DONE
        rows = [("Odvolit", 680, pv, G, "hotovo za pár minut" if done else "…"),
                ("Vypít pivo", 1080, pb, BEER, "ještě dobrou čtvrthodinku…" if done else "…")]
        for i, (lab, y, p, col, sub) in enumerate(rows):
            kk = f - 12 - i * 4
            if kk < 0:
                continue
            a = clamp(kk / 8)
            lay = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            yy = 150
            ic = BALLOT if i == 0 else mug(0.85, level=1 - pb)
            lay.alpha_composite(ic, (int(170 - ic.width / 2), int(yy - ic.height / 2)))
            ld.text((330, yy - 70), lab, font=font(72, "ExtraBold"), fill=DARK, anchor="ls")
            self.bar(ld, 330, 1000, yy, p, col)
            if i == 0 and done:
                s = ease_out_back(clamp((k - V_DONE) / 8), 2)
                r = 44 * s
                ld.ellipse([1000 - r, yy - r, 1000 + r, yy + r], fill=GD)
                if s > .5:
                    ld.line([(980, yy), (995, yy + 16), (1022, yy - 16)], fill=WHITE, width=9)
            if sub != "…":
                ld.text((330, yy + 100), sub, font=font(50, "SemiBold"), fill=GREY, anchor="ls")
            if a < 1:
                lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
            c.alpha_composite(lay, (0, int(y - 150 + (1 - ease_out(a)) * 40)))
        self.win.draw(c, f)
        return c
S2 = Race()

# ---------- S3: nejdřív volit, pak na pivo + časy ----------
def time_card(day, hours):
    img = Image.new("RGBA", (480, 270), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, 470, 260], radius=40, fill=WHITE)
    d.text((240, 82), day, font=font(58, "Bold"), fill=GREY, anchor="mm")
    d.text((240, 180), hours, font=font(100, "ExtraBold"), fill=DARK, anchor="mm")
    return outline(img, 6)
S3 = TextScene(125, BG, [Words("Tak nejdřív *volit,*", 380, 3, 96), Words("pak *na_pivo.*", 510, 14, 110),
                         Pop(time_card("pátek", "14–22"), 290, 860, 44, -3),
                         Pop(time_card("sobota", "8–14"), 790, 860, 52, 3),
                         Words("Nezapomeňte *občanku.*", 1150, 74, 80)])

# ---------- S4: závěr s přípitkem ----------
EMPTY = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
ME_BEER = TS.ToastSticker(860, EMPTY)
MUG_S = 0.95
MUG_END = mug(MUG_S)                                  # ucho vpravo = k Karlovi
_bw, _hw, _pad, _fh, _bh = 150 * MUG_S, 60 * MUG_S, 20 * MUG_S, 44 * MUG_S, 200 * MUG_S
GRIP = (_pad + _bw + _hw - 9 * MUG_S, _pad + _fh + _bh * 0.48)   # místo úchopu na uchu
CLINK = 70
class MeCheers(El):
    """Karel s půllitrem: ruka se jen lehce pohupuje, půllitr je v horní vrstvě (nad rukou)."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        dy = (1 - ease_out_back(clamp(k / 12), 1.2)) * 900
        t = f - CLINK
        bump = 4 * math.exp(-t / 6) * math.sin(t * .6) if t >= 0 else 0     # malé ťuknutí
        a = -2 + 1.2 * math.sin(f * .12) + bump
        img = ME_BEER.image(a)
        x0, y0 = int(self.cx), int(H - img.height + 30 + dy)
        c.alpha_composite(img, (x0, y0))
        # bod úchopu po otočení předloktí kolem lokte
        px, py = TS.PINCH[0] * ME_BEER.s, (TS.PINCH[1] + TS.PAD) * ME_BEER.s
        cx, cy = ME_BEER.pivot
        r = math.radians(a)
        qx = cx + (px - cx) * math.cos(r) + (py - cy) * math.sin(r)
        qy = cy - (px - cx) * math.sin(r) + (py - cy) * math.cos(r)
        m = MUG_END.rotate(a, expand=False, center=GRIP, resample=Image.BICUBIC)
        mx, my = x0 + qx - GRIP[0] + 6, y0 + qy - GRIP[1]
        c.alpha_composite(m, (int(mx), int(my)))
        if 0 <= t < 14:
            d = ImageDraw.Draw(c)
            aa = 1 - t / 14; rr = 30 + t * 6
            gx, gy = mx + 60, my + 20
            for i in range(8):
                ang = i * math.pi / 4
                d.line([(gx + math.cos(ang) * rr * .4, gy + math.sin(ang) * rr * .4), (gx + math.cos(ang) * rr, gy + math.sin(ang) * rr)],
                       fill=(255, 220, 120, int(255 * aa)), width=7)

S4 = TextScene(75, BG, [Words("Budeme rádi", 820, 3, 110), Words("za *váš_hlas.*", 960, 12, 130)])
SUB1 = text_img("Rozumím digitalizaci, projektům", 60, DARK, w="SemiBold")
SUB2 = text_img("i financím města.", 60, DARK, w="SemiBold")
BIG_LOGO = LOGO.resize((int(LOGO.width * 1.05), int(LOGO.height * 1.05)), Image.LANCZOS)
S5 = TextScene(190, BG, [Words("*Karel_Krupička*", 250, 3, 112),
                         El(SUB1, W // 2, 395, 16, "rise"), El(SUB2, W // 2, 470, 22, "rise"),
                         Words("A na pivo zajdu *rád.*", 620, CLINK - 8, 84),
                         MeCheers(None, 300, 0, 10),
                         Pop(BIG_LOGO, 245, 1560, 40, -6)])

SCENES = [S1, S2, S3, S4, S5]
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

def clink():
    n = int(0.7 * A.SR); t = A.t_(n)
    y = np.zeros(n)
    for f0, g in ((2100, 1), (3150, .6), (4420, .4)):
        y += g * np.sin(2 * np.pi * f0 * t) * np.exp(-t / 0.18)
    return y * 0.6

def fizz(dur=1.2):
    n = int(dur * A.SR)
    y = A.rng.standard_normal(n) * (A.rng.random(n) < 0.02)
    y = A.hp(y, 3000)
    return y * np.linspace(1, 0, n)

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    out.add(0, A.seg_pop(total + .2, 0.55)[: int(total * SR)])
    out.add(0, fizz(3.5), 0.25)
    for a in (6, 40, 48, 58, 66):
        out.add(st[0] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[0] + 66 / FPS, A.fx_ding(), 0.5)
    out.add(st[1] + 4 / FPS, K1.fx_pop(), 0.5)
    for k in range(24, 24 + V_DONE, 4):
        out.add(st[1] + k / FPS, A.hat(), 0.25)
    out.add(st[1] + (24 + V_DONE) / FPS, A.fx_ding(), 0.6)
    out.add(st[1] + 70 / FPS, A.fx_impact(), 0.6)
    for a in (3, 14, 44, 52, 74):
        out.add(st[2] + a / FPS, K1.fx_pop(), 0.5)
    for a in (3, 12):
        out.add(st[3] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[3] + 12 / FPS, A.fx_ding(), 0.5)
    for a in (3, 14, 22, 40, CLINK - 6):
        out.add(st[4] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[4] + 10 / FPS, A.fx_whoosh(0.4), 0.5)
    out.add(st[4] + CLINK / FPS, clink(), 0.8)
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
            SCENES[int(args[i])].render(int(args[i + 1])).convert("RGB").save(os.path.join(HERE, "hlas", f"b{args[i]}_{args[i+1]}.jpg"))
        sys.exit()
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "volby_pivo_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
