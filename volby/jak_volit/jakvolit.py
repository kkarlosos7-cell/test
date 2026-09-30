"""Jak volit ve Starém Plzenci – reels 1080x1920, 30 fps, se zvukem."""
import os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import audio as A
import festival as FE
import kino as K1
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, rect_img, El, TextScene, Slam)
from kino2 import Words
from kino import outline, shake_post
import armsticker as AS

HERE = R.HERE
OUT = os.path.join(HERE, "jak_volit.mp4")
GREY = (96, 108, 128)

def card(w, h, fill=WHITE, r=26):
    img = Image.new("RGBA", (w + 40, h + 50), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 32, w + 20, h + 32], radius=r, fill=(27, 38, 59, 45))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(img).rounded_rectangle([20, 20, w + 20, h + 20], radius=r, fill=fill)
    return img

class Pop(El):
    def __init__(self, img, cx, cy, at, rot=0):
        super().__init__(img, cx, cy, at); self.rot = rot
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 10))
        s = 0.3 + 0.7 * p
        img = self.img.resize((max(2, int(self.img.width * s)), max(2, int(self.img.height * s))), Image.BILINEAR)
        if self.rot:
            img = img.rotate(self.rot * p, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

# ---------- ikonky ----------
def ballot_box(s=420):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 150, s - 40, s - 30], radius=26, fill=WHITE)
    d.rounded_rectangle([40, 150, s - 40, 215], radius=26, fill=G)
    d.rectangle([40, 190, s - 40, 215], fill=G)
    d.rounded_rectangle([s / 2 - 90, 168, s / 2 + 90, 186], radius=9, fill=DARK)   # otvor
    d.text((s / 2, 300), "✓", font=font(120, "ExtraBold"), fill=G, anchor="mm")
    return outline(img, 10)

def envelope(w=210, h=140):
    img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, w + 10, h + 10], radius=10, fill=(248, 240, 214))
    d.polygon([(10, 10), (w + 10, 10), (w / 2 + 10, h * .6)], fill=(232, 220, 186))
    return outline(img, 7)

def id_card():
    img = Image.new("RGBA", (380, 250), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, 370, 240], radius=22, fill=(214, 232, 244))
    d.rounded_rectangle([10, 10, 370, 60], radius=22, fill=(96, 140, 190)); d.rectangle([10, 40, 370, 60], fill=(96, 140, 190))
    d.rounded_rectangle([34, 82, 134, 212], radius=12, fill=(170, 186, 204))
    d.ellipse([62, 100, 106, 144], fill=(236, 240, 244)); d.rounded_rectangle([52, 150, 116, 212], radius=20, fill=(236, 240, 244))
    for i, wd in enumerate((190, 160, 200, 120)):
        d.rounded_rectangle([156, 90 + i * 32, 156 + wd, 106 + i * 32], radius=8, fill=(160, 176, 196))
    return outline(img, 9)

def passport():
    img = Image.new("RGBA", (250, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, 240, 320], radius=20, fill=(120, 30, 50))
    d.ellipse([85, 90, 165, 170], outline=(232, 190, 90), width=8)
    d.text((125, 240), "PAS", font=font(54, "ExtraBold"), fill=(232, 190, 90), anchor="mm")
    return outline(img, 9)

def phone_edoklady():
    img = Image.new("RGBA", (240, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, 230, 410], radius=34, fill=DARK)
    d.rounded_rectangle([24, 30, 216, 392], radius=24, fill=WHITE)
    d.rounded_rectangle([44, 70, 196, 170], radius=14, fill=(214, 232, 244))
    d.text((120, 215), "eDoklady", font=font(34, "ExtraBold"), fill=DARK, anchor="mm")
    for i in range(3):
        d.rounded_rectangle([50, 260 + i * 36, 190, 276 + i * 36], radius=8, fill=(220, 226, 232))
    return outline(img, 9)

def clock_icon(s=150):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([10, 10, s - 10, s - 10], fill=GL)
    d.ellipse([24, 24, s - 24, s - 24], fill=WHITE, outline=GD, width=6)
    c = s / 2
    d.line([(c, c), (c, c - 36)], fill=DARK, width=8)
    d.line([(c, c), (c + 28, c + 10)], fill=DARK, width=8)
    return img

def day_card(day, date, hours):
    img = card(900, 230)
    d = ImageDraw.Draw(img)
    img.alpha_composite(clock_icon(150), (50, 60))
    d.text((230, 58), f"{day} {date}", font=font(56, "ExtraBold"), fill=DARK)
    d.text((230, 138), hours, font=font(84, "ExtraBold"), fill=GD)
    return img

def info_card(title, text, icon_txt):
    img = card(920, 210)
    d = ImageDraw.Draw(img)
    d.ellipse([50, 60, 170, 180], fill=GL)
    d.text((110, 120), icon_txt, font=font(64, "ExtraBold"), fill=GD, anchor="mm")
    d.text((210, 58), title, font=font(50, "ExtraBold"), fill=DARK)
    d.text((210, 128), text, font=font(40, "SemiBold"), fill=GREY)
    return img

# ---------- S1: Jak volit ve Starém Plzenci? ----------
class Drop(El):
    """Obálka padá do urny."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        loop = k % 40
        p = ease_in_out(clamp(loop / 22))
        y = self.cy - 260 + p * 200
        img = self.img
        if loop > 22:
            return
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(y - img.height / 2)))

BOX = ballot_box()
def chip(t):
    return outline(text_img(t, 50, DARK, w="ExtraBold", pill=GL, pad=(30, 16), radius=14), 7)

class Ballot(El):
    """Hlasovací lístek s křížkem padá do urny (smyčka)."""
    def __init__(self, cx, cy, at):
        img = Image.new("RGBA", (200, 250), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([10, 10, 190, 240], radius=12, fill=WHITE, outline=(210, 216, 224), width=4)
        for i in range(5):
            d.rounded_rectangle([34, 40 + i * 40, 60, 66 + i * 40], radius=4, outline=DARK, width=4)
            d.rounded_rectangle([74, 46 + i * 40, 166, 58 + i * 40], radius=6, fill=(214, 220, 228))
        d.line([(38, 124), (56, 142)], fill=G, width=6); d.line([(56, 124), (38, 142)], fill=G, width=6)
        super().__init__(outline(img, 7), cx, cy, at)
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        loop = k % 36
        if loop > 24:
            return
        p = ease_in_out(loop / 24)
        y = self.cy - 100 + p * 200
        img = self.img.rotate(8 * (1 - p), expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(y - img.height / 2)))

S1 = TextScene(120, BG, [Words("Jak volit", 330, 3, 130), Words("v *komunálních_volbách?*", 470, 12, 72),
                         Pop(chip("Kdy"), 250, 650, 26, -4), Pop(chip("Co s sebou"), 700, 650, 32, 3),
                         Pop(chip("Kolik zastupitelů"), 330, 775, 38, 2), Pop(chip("Když nemůžete"), 800, 785, 44, -3),
                         El(text_img("9.–10. října", 96, WHITE, w="ExtraBold", pill=G, pad=(44, 18)), W // 2, 935, 54, dur=10),
                         Ballot(W // 2, 1300, 60),
                         Pop(BOX.resize((560, 560), Image.LANCZOS), W // 2, 1460, 20)])

# ---------- S2: kdy ----------
S2 = TextScene(135, BG, [Words("Kdy?", 330, 3, 130),
                         Pop(day_card("Pátek", "9. října", "14–22 h"), W // 2, 700, 14, -1.5),
                         Pop(day_card("Sobota", "10. října", "8–14 h"), W // 2, 1010, 30, 1.5),
                         Words("Ve své volební místnosti", 1330, 60, 64),
                         Words("podle *trvalého_bydliště.*", 1430, 68, 64)])

# ---------- S3: co s sebou ----------
S3 = TextScene(140, GL, [Words("Co s sebou?", 330, 3, 120),
                         Words("Stačí *jedno* z toho:", 460, 12, 72),
                         Pop(id_card(), 300, 800, 28, -6), Pop(passport(), 780, 820, 36, 5),
                         Pop(phone_edoklady(), W // 2, 1180, 44, -3),
                         Words("Občanka · pas · eDoklady", 1480, 60, 66)])

# ---------- S4: 17 zastupitelů, jeden lístek ----------
class People(El):
    def draw(self, c, f):
        d = ImageDraw.Draw(c)
        for i in range(17):
            k = f - self.at - i * 2
            if k < 0:
                continue
            p = ease_out_back(clamp(k / 8))
            row, col = divmod(i, 6)
            n_in_row = 6 if row < 2 else 5
            x = W / 2 + (col - (n_in_row - 1) / 2) * 150
            y = 820 + row * 190
            s = p
            col_ = G if i % 3 == 0 else (GD if i % 3 == 1 else DARK)
            d.ellipse([x - 32 * s, y - 80 * s, x + 32 * s, y - 16 * s], fill=col_)
            d.rounded_rectangle([x - 52 * s, y - 8 * s, x + 52 * s, y + 90 * s], radius=int(34 * s) + 1, fill=col_)

S4 = TextScene(130, BG, [Words("Ve Starém Plzenci volíme", 300, 3, 64), Words("*17_zastupitelů.*", 450, 10, 110),
                         People(None, 0, 0, 24),
                         Words("Na *jednom* lístku.", 1470, 70, 92)])

# ---------- S5: nemůžete přijít? ----------
S5 = TextScene(175, BG, [Words("Nemůžete přijít?", 300, 3, 110),
                         Pop(info_card("Voličský průkaz?", "U komunálních voleb nejde.", "✗"), W // 2, 620, 18, -1),
                         Pop(info_card("Ze zahraničí?", "Komunální volby to neumožňují.", "✗"), W // 2, 880, 34, 1),
                         Pop(info_card("Nemoc?", "Požádejte úřad o přenosnou urnu.", "✓"), W // 2, 1140, 50, -1),
                         Words("Volí se *osobně.*", 1450, 80, 96)])

# ---------- S6: závěr ----------
ME = AS.ArmSticker(780)
class MePoint(El):
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        dy = (1 - ease_out_back(clamp(k / 12), 1.3)) * 1000
        a = -8 + 7 * math.sin(k * .22) if k > 12 else -15
        img = ME.image(a)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(H - img.height + 30 + dy)))

SLAM6 = 50
from podzim import logo_sticker
LOGO = logo_sticker()
S6 = TextScene(165, BG, [Words("Přijďte volit!", 290, 3, 110),
                         El(text_img("9.–10. října", 130, WHITE, w="ExtraBold", pill=G, pad=(56, 26)), W // 2, 450, 12, dur=11),
                         El(text_img("Karel Krupička", 92, DARK, w="ExtraBold"), W // 2, 620, 30, dur=11),
                         El(text_img("www.dobrasprava.cz", 38, DARK + (140,), w="SemiBold"), W // 2, 705, 38, "rise"),
                         MePoint(None, 690, 0, SLAM6),
                         Pop(LOGO.resize((int(LOGO.width * .85), int(LOGO.height * .85)), Image.LANCZOS), 225, 1200, SLAM6 + 16, -6)],
               post=shake_post([SLAM6 + 5], BG))

SCENES = [S1, S2, S3, S4, S5, S6]
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
    out.add(0, A.seg_pop(total + .2, 0.55)[: int(total * SR)])
    pops = {0: (3, 12, 20), 1: (3, 14, 30, 60, 68), 2: (3, 12, 28, 36, 44, 60), 3: (3, 10, 70),
            4: (3, 18, 34, 50, 80), 5: (3, 12, 30, 38)}
    for i, lst in pops.items():
        for a in lst:
            out.add(st[i] + a / FPS, K1.fx_pop(), 0.5)
    for j in range(3):
        out.add(st[0] + (30 + 40 * j + 22) / FPS, A.kick(0.6), 0.5)
    for i in range(17):
        out.add(st[3] + (24 + i * 2) / FPS, K1.fx_pop(), 0.2)
    out.add(st[3] + 70 / FPS, A.fx_ding(), 0.7)
    out.add(st[4] + 80 / FPS, A.fx_ding(), 0.6)
    out.add(st[5] + 12 / FPS, A.fx_ding(), 0.6)
    out.add(st[5] + SLAM6 / FPS, A.fx_whoosh(0.4), 0.6)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fo = int(1.2 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

if __name__ == "__main__":
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "jakvolit_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
