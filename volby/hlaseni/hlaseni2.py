"""Reels v2: hlášení závad + hlavní pecka – veřejný přehled rychlosti řešení (ukázka). 1080x1920, 30 fps, se zvukem."""
import os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import audio as A
import festival as FE
import kino as K1
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, El, TextScene)
from kino2 import Words
from kino import shake_post
import armsticker as AS
import hlaseni as HL
from hlaseni import put_phone, form_screen, list_screen, caption, IntroPhone, T_MAP, T_KAT, T_POP, T_FOTO, T_CHK, T_SEND
from rozpocet2 import Pop, SlamLeft

HERE = R.HERE
OUT = os.path.join(HERE, "hlaseni_reels_v2.mp4")
GREY = (110, 122, 140)
MUTED = (150, 160, 175)
LINE = (230, 234, 238)
ORANGE = (232, 163, 61)
SLATE = (96, 116, 150)

# ---------- S1: háček ----------
SLAM1 = 34
S1 = TextScene(100, BG, [Words("Rozbité *hřiště?*", 250, 3, 96), Words("*Černá_skládka?*", 375, 10, 96),
                         Words("Nahlaste to *z_mobilu.*", 500, 18, 76),
                         IntroPhone(None, 790, 1180, 14),
                         SlamLeft(FE.scaled(FE.ST_PLAIN, 640), 300, 0, SLAM1)],
               post=shake_post([SLAM1 + 5], BG))

# ---------- S2: vyplnění (bez ukazující ruky) ----------
class FormDemo:
    n = T_SEND + 16
    caps = HL.S2.caps
    def render(self, f):
        c = Image.new("RGBA", (W, H), BG + (255,))
        put_phone(c, form_screen(f), cx=W // 2)
        caption(self.caps, c, f)
        return c
S2 = FormDemo()

# ---------- S3: stav hlášení (zkráceno) ----------
class ListDemo:
    n = 100
    caps = [(t, Words(s, 230, t + 2, 64)) for t, s in [(0, "Sledujte *stav_hlášení*"), (50, "Vidíte, *kdo_to_řeší*")]]
    def render(self, f):
        c = Image.new("RGBA", (W, H), BG + (255,))
        put_phone(c, list_screen(f), cx=W // 2)
        caption(self.caps, c, f)
        return c
S3 = ListDemo()

# ---------- S4: most ----------
S4 = TextScene(62, BG, [Words("Ale chceme", 760, 3, 96), Words("*víc.*", 900, 12, 150)],
               post=shake_post([16], BG))

# ---------- S5: PECKA – veřejný přehled (ukázka, ilustrační data) ----------
CX0, CX1, CY0, CY1 = 50, 1030, 300, 1700
_card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(_sh).rounded_rectangle([CX0, CY0 + 24, CX1, CY1 + 24], radius=44, fill=(27, 38, 59, 70))
_card.alpha_composite(_sh.filter(ImageFilter.GaussianBlur(22)))
ImageDraw.Draw(_card).rounded_rectangle([CX0, CY0, CX1, CY1], radius=44, fill=WHITE)

TILES = [  # (cílová hodnota, formát, popisek, start)
    (2.4, lambda v: f"{v:.1f}".replace(".", ",") + " dne", "průměrně do vyřešení", 14),
    (86, lambda v: f"{int(round(v))} %", "vyřešeno do týdne", 22),
    (24, lambda v: f"do {int(round(v))} h", "první reakce úřadu", 30)]
BARS = [("Odpadkové koše", 1.0), ("Dětská hřiště", 1.5), ("Černé skládky", 2.0), ("Veřejné osvětlení", 3.5),
        ("Chodníky a silnice", 5.5)]
B_T0, MAXD, GOAL = 48, 9, 7
TICKETS = [  # (název, místo, stav, barva, kdo řeší, čas)
    ("Nesvítí lampa", "Sedlec", "V řešení", ORANGE, "Údržba města", "1 den"),
    ("Rozbitá lavička", "park", "Přijato", SLATE, "Údržba města", "před 3 h"),
    ("Výtluk na silnici", "Plzenecká", "Předáno", MUTED, "Správa silnic · termín 15. 10.", "4 dny"),
]
K_T0 = 140

def card_tiles(d, f):
    y0 = CY0 + 120
    tw = (CX1 - CX0 - 60 - 2 * 24) / 3
    for i, (v, fmt, lab, t0) in enumerate(TILES):
        k = f - t0
        if k < 0:
            continue
        p = ease_out(clamp(k / 26))
        x = CX0 + 30 + i * (tw + 24)
        a = clamp(k / 6)
        d.rounded_rectangle([x, y0, x + tw, y0 + 240], radius=26, fill=(240, 246, 238, int(255 * a)))
        d.text((x + tw / 2, y0 + 100), fmt(v * p), font=font(74, "ExtraBold"), fill=DARK + (int(255 * a),), anchor="mm")
        d.text((x + tw / 2, y0 + 182), lab, font=font(27, "SemiBold"), fill=GREY + (int(255 * a),), anchor="mm")

def card_bars(d, f):
    y0 = CY0 + 440
    k0 = f - B_T0
    if k0 < 0:
        return
    a = int(255 * clamp(k0 / 6))
    d.text((CX0 + 40, y0), "Průměrná doba vyřešení podle typu", font=font(42, "Bold"), fill=DARK + (a,), anchor="ls")
    lx, bx0, bx1 = CX0 + 40, CX0 + 420, CX1 - 40
    # cílová čára 7 dní
    kk = k0 - 30
    if kk >= 0:
        aa = int(255 * clamp(kk / 8))
        gx = bx0 + (bx1 - bx0) * GOAL / MAXD
        for yy in range(y0 + 30, y0 + 40 + len(BARS) * 86, 18):
            d.line([gx, yy, gx, yy + 9], fill=GD + (aa,), width=4)
        d.text((gx, y0 + 62 + len(BARS) * 86), "cíl: do 7 dní", font=font(30, "Bold"), fill=GD + (aa,), anchor="mm")

    for i, (name, days) in enumerate(BARS):
        k = k0 - 4 - i * 4
        y = y0 + 36 + i * 86
        if k < 0:
            continue
        p = ease_out(clamp(k / 18))
        aa = int(255 * clamp(k / 5))
        d.text((lx, y + 32), name, font=font(36, "SemiBold"), fill=DARK + (aa,), anchor="lm")
        bw = (bx1 - bx0) * days / MAXD * p
        if bw > 4:
            d.rounded_rectangle([bx0, y + 6, bx0 + bw, y + 58], radius=10, fill=G + (aa,))
        val = f"{days * p:.1f}".replace(".", ",").replace(",0", "") + " d"
        d.text((bx0 + bw + 14, y + 32), val, font=font(36, "Bold"), fill=DARK + (aa,), anchor="lm", stroke_width=6, stroke_fill=WHITE + (aa,))
def card_tickets(d, f):
    y0 = CY0 + 1010
    k0 = f - K_T0
    if k0 < 0:
        return
    a = int(255 * clamp(k0 / 6))
    d.text((CX0 + 40, y0), "Právě se řeší", font=font(42, "Bold"), fill=DARK + (a,), anchor="ls")
    for i, (name, place, st, col, who, tm) in enumerate(TICKETS):
        k = k0 - 6 - i * 7
        if k < 0:
            continue
        aa = int(255 * clamp(k / 6))
        dx = (1 - ease_out(clamp(k / 10))) * 80
        y = y0 + 22 + i * 118
        x = CX0 + 40 + dx
        d.line([CX0 + 40, y, CX1 - 40, y], fill=LINE + (aa,), width=2)
        d.text((x, y + 42), name, font=font(38, "Bold"), fill=DARK + (aa,), anchor="lm")
        nx = x + font(38, "Bold").getlength(name) + 14
        d.text((nx, y + 42), "· " + place, font=font(32, "SemiBold"), fill=MUTED + (aa,), anchor="lm")
        d.text((x, y + 90), who, font=font(30, "SemiBold"), fill=GREY + (aa,), anchor="lm")
        # štítek stavu: barevná tečka + text v tmavém inkoustu
        fw = font(28, "Bold").getlength(st)
        sx1 = CX1 - 40 - dx
        sx0 = sx1 - fw - 76
        d.rounded_rectangle([sx0, y + 18, sx1, y + 64], radius=23, fill=col + (int(aa * .18),))
        d.ellipse([sx0 + 20, y + 33, sx0 + 36, y + 49], fill=col + (aa,))
        d.text((sx0 + 48, y + 41), st, font=font(28, "Bold"), fill=DARK + (aa,), anchor="lm")
        d.text((sx1, y + 90), tm, font=font(30, "SemiBold"), fill=GREY + (aa,), anchor="rm")

HEAD = text_img("Hlášení ve městě · přehled", 44, DARK, w="ExtraBold")
BADGE = text_img("UKÁZKA", 26, WHITE, w="ExtraBold", pill=GD, pad=(18, 8), radius=18)
NOTE = text_img("Takhle chceme, aby to fungovalo · ilustrační data", 30, GREY, w="SemiBold")

class Dash:
    n = 285
    caps = [(t, Words(s, 230, t + 2, 64)) for t, s in
            [(0, "Za jak dlouho se to *vyřeší?*"), (K_T0 - 8, "Kdo to má *na_starosti?*")]]
    def render(self, f):
        c = Image.new("RGBA", (W, H), BG + (255,))
        p = ease_out_back(clamp(f / 14), 1.1)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.alpha_composite(_card)
        d = ImageDraw.Draw(layer)
        layer.alpha_composite(HEAD, (CX0 + 40, CY0 + 40))
        layer.alpha_composite(BADGE, (CX1 - 40 - BADGE.width, CY0 + 40))
        card_tiles(d, f)
        card_bars(d, f)
        card_tickets(d, f)
        c.alpha_composite(layer, (0, int((1 - p) * 1400)))
        caption(self.caps, c, f)
        if f > 20:
            nt = NOTE.copy()
            a = clamp((f - 20) / 10)
            nt.putalpha(nt.getchannel("A").point(lambda v: int(v * a)))
            c.alpha_composite(nt, (W // 2 - NOTE.width // 2, CY1 + 40))
        return c
S5 = Dash()

# ---------- S6: pointa + závěr (jediné místo s ukazující rukou, jen jemně) ----------
class MeCalm(El):
    def __init__(self, cx, at, sticker):
        super().__init__(None, cx, 0, at); self.st = sticker
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        dy = (1 - ease_out_back(clamp(k / 12), 1.3)) * 1000
        a = -6 + 2 * math.sin(f * .12)
        img = self.st.image(a)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(H - img.height + 30 + dy)))

LOGO = HL.LOGO
BIG_LOGO = LOGO.resize((int(LOGO.width * 1.2), int(LOGO.height * 1.2)), Image.LANCZOS)
S6 = TextScene(160, BG, [Words("Ať je jasné, že", 260, 3, 96), Words("*hlásit_má_smysl.*", 390, 12, 110),
                         Words("Tohle chceme", 560, 40, 72), Words("na radnici *prosadit.*", 660, 46, 72),
                         Pop(BIG_LOGO, 300, 1180, 56, -6),
                         MeCalm(770, 66, AS.ArmSticker(780))])

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

def tick():
    n = int(0.03 * A.SR); t = A.t_(n)
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t / 0.006)

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    out.add(0, A.seg_pop(total + .2, 0.55)[: int(total * SR)])
    for a in (3, 10, 18):
        out.add(st[0] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[0] + 14 / FPS, A.fx_whoosh(0.5), 0.5)
    out.add(st[0] + (SLAM1 + 5) / FPS, A.fx_impact(), 0.9)
    for tt, w in S2.caps:
        out.add(st[1] + w.at / FPS, K1.fx_pop(), 0.45)
    for tt in (T_MAP, T_KAT, T_POP, T_FOTO, T_CHK, T_SEND):
        out.add(st[1] + tt / FPS, HL.tap(), 0.5)
    for k in range(0, 26, 2):
        out.add(st[1] + (T_POP + 2 + k) / FPS, A.hat(), 0.18)
    out.add(st[1] + (T_SEND + 2) / FPS, A.fx_ding(), 0.5)
    for tt, w in S3.caps:
        out.add(st[2] + w.at / FPS, K1.fx_pop(), 0.45)
    for a in (10, 19, 28, 58):
        out.add(st[2] + a / FPS, A.hat(), 0.35)
    out.add(st[3] + 3 / FPS, K1.fx_pop(), 0.5)
    out.add(st[3] + 16 / FPS, A.fx_impact(), 0.9)
    # pecka: přílet karty, počítání čísel, růst sloupců, řádky
    out.add(st[4], A.fx_whoosh(0.5), 0.6)
    for tt, w in S5.caps:
        out.add(st[4] + w.at / FPS, K1.fx_pop(), 0.45)
    for v, fmt, lab, t0 in TILES:
        out.add(st[4] + t0 / FPS, K1.fx_pop(), 0.4)
        for k in range(0, 24, 3):
            out.add(st[4] + (t0 + k) / FPS, tick(), 0.25)
    for i in range(len(BARS)):
        out.add(st[4] + (B_T0 + 4 + i * 4) / FPS, A.hat(), 0.4)
    out.add(st[4] + (B_T0 + 30) / FPS, A.fx_ding(), 0.5)
    for i in range(len(TICKETS)):
        out.add(st[4] + (K_T0 + 6 + i * 7) / FPS, K1.fx_pop(), 0.4)
    for a in (3, 12, 40):
        out.add(st[5] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[5] + 12 / FPS, A.fx_ding(), 0.6)
    out.add(st[5] + 56 / FPS, A.fx_impact(), 0.5)
    out.add(st[5] + 66 / FPS, A.fx_whoosh(0.4), 0.5)
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
            SCENES[int(args[i])].render(int(args[i + 1])).convert("RGB").save(os.path.join(HERE, "hlas", f"q{args[i]}_{args[i+1]}.jpg"))
        sys.exit()
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "hlaseni2_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
