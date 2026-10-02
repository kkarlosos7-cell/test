"""Reels: Hlášení závad z mobilu (hlaseni.tmapy.cz) – víte, že to existuje? 1080x1920, 30 fps, se zvukem."""
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
from kino import outline, shake_post
import armsticker as AS
from podzim import logo_sticker
from rozpocet2 import Pop, MePoint, SlamLeft

HERE = R.HERE
OUT = os.path.join(HERE, "hlaseni_reels.mp4")
LOGO = logo_sticker()

# ---------- snímky obrazovky (plné rozlišení 1170 px, ořez bez stavového řádku a lišty prohlížeče) ----------
CROP = (0, 140, 1170, 2236)
FORM = Image.open(os.path.join(HERE, "hlas", "form.png")).convert("RGBA").crop(CROP)
LIST = Image.open(os.path.join(HERE, "hlas", "list.png")).convert("RGBA").crop(CROP)
OY = CROP[1]
def box(x0, y0, x1, y1):            # souřadnice z původního snímku -> ořez
    return (x0, y0 - OY, x1, y1 - OY)

SCR_W = 600
SCR_H = round(SCR_W * FORM.height / FORM.width)
SC = SCR_W / FORM.width
PH_W, PH_H = SCR_W + 36, SCR_H + 36
PH_CX, PH_TOP = 410, 400
_pm = Image.new("L", (SCR_W, SCR_H), 0)
ImageDraw.Draw(_pm).rounded_rectangle([0, 0, SCR_W - 1, SCR_H - 1], radius=50, fill=255)
PHONE = Image.new("RGBA", (PH_W + 80, PH_H + 90), (0, 0, 0, 0))
_s = Image.new("RGBA", PHONE.size, (0, 0, 0, 0))
ImageDraw.Draw(_s).rounded_rectangle([40, 60, PH_W + 40, PH_H + 60], radius=70, fill=(27, 38, 59, 90))
PHONE.alpha_composite(_s.filter(ImageFilter.GaussianBlur(22)))
ImageDraw.Draw(PHONE).rounded_rectangle([40, 40, PH_W + 40, PH_H + 40], radius=70, fill=DARK)

def put_phone(c, scr, cx=PH_CX, top=PH_TOP):
    x0 = cx - PHONE.width // 2
    c.alpha_composite(PHONE, (x0, top - 40))
    c.paste(scr.resize((SCR_W, SCR_H), Image.LANCZOS).convert("RGB"), (x0 + 58, top + 18), _pm)
    return x0 + 58, top + 18     # levý horní roh displeje

FIELD = (83, 94, 107, 255)
FTXT = (236, 240, 244)
def field_text(d, b, text, size=46, erase=False):
    if erase:
        d.rectangle([b[0] + 6, b[1] + 8, b[2] - 6, b[3] - 8], fill=FIELD)
    d.text((b[0] + 28, (b[1] + b[3]) / 2), text, font=font(size, "SemiBold"), fill=FTXT, anchor="lm")

def ripple(d, x, y, k):
    """Klepnutí prstem: kruh, který se rozšíří a zmizí (k = snímky od klepnutí)."""
    if 0 <= k < 14:
        p = k / 14
        r = 30 + 60 * ease_out(p)
        a = int(200 * (1 - p))
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, a), width=10)
        if k < 6:
            d.ellipse([x - 34, y - 34, x + 34, y + 34], fill=(255, 255, 255, 140))

def pin(c, x, y, k):
    if k < 0:
        return
    p = ease_out_back(clamp(k / 8), 1.6)
    yy = y - 70 * (1 - p)
    d = ImageDraw.Draw(c)
    d.ellipse([x - 34, yy - 100, x + 34, yy - 32], fill=(220, 60, 50, 255), outline=WHITE, width=6)
    d.polygon([(x - 26, yy - 50), (x + 26, yy - 50), (x, yy)], fill=(220, 60, 50, 255))
    d.ellipse([x - 12, yy - 78, x + 12, yy - 54], fill=WHITE)

# políčka formuláře (původní souřadnice)
B_MAP_TAP = (165, 1180)
B_MISTO = box(340, 376, 1000, 496)
B_KAT = box(340, 580, 1122, 700)
B_POPIS = box(340, 782, 1122, 1022)
B_MAIL = box(340, 1104, 1122, 1224)
B_FOTO = box(600, 1312, 1122, 1428)
B_CHECK = box(340, 1462, 400, 1522)
B_SEND = box(722, 1582, 1122, 1702)
def mid(b): return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

POPIS = ["Pod lípami je láhev", "s vyjetým olejem."]
T_MAP, T_KAT, T_POP, T_MAIL, T_FOTO, T_CHK, T_SEND = 16, 50, 80, 120, 136, 150, 170

def form_screen(f):
    s = FORM.copy()
    d = ImageDraw.Draw(s, "RGBA")
    pin(s, B_MAP_TAP[0], B_MAP_TAP[1] - OY, f - T_MAP - 2)
    if f >= T_MAP + 8:
        field_text(d, B_MISTO, "Školní, Starý Plzenec", erase=True)
    if f >= T_KAT + 4:
        field_text(d, B_KAT, "Černá skládka, autovrak")
    if f >= T_POP + 2:
        n = int((f - T_POP - 2) * 1.4)
        y = B_POPIS[1] + 60
        for line in POPIS:
            part = line[:max(0, n)]
            n -= len(line)
            d.text((B_POPIS[0] + 28, y), part, font=font(46, "SemiBold"), fill=FTXT, anchor="lm")
            y += 66
    if f >= T_MAIL:
        field_text(d, B_MAIL, "jmeno@email.cz")
    if f >= T_FOTO + 3:
        d.rectangle([B_FOTO[0] + 4, B_FOTO[1] + 12, B_FOTO[2] - 8, B_FOTO[3] - 12], fill=FIELD)
        d.text((B_FOTO[2] - 24, mid(B_FOTO)[1]), "skladka.jpg", font=font(48, "SemiBold"),
               fill=FTXT, anchor="rm")
    if f >= T_CHK + 2:
        d.rectangle(B_CHECK, fill=G)
        cx, cy = mid(B_CHECK)
        d.line([(cx - 18, cy), (cx - 4, cy + 16), (cx + 20, cy - 16)], fill=WHITE, width=8)
    if f >= T_CHK + 2:      # tlačítko Odeslat se rozsvítí
        d.rectangle(B_SEND, fill=G)
        d.text(mid(B_SEND), "Odeslat", font=font(50, "SemiBold"), fill=WHITE, anchor="mm")
    if f >= T_SEND + 1:
        k = f - T_SEND
        d.rectangle(B_SEND, fill=GD if k < 6 else G)
        d.text(mid(B_SEND), "Odeslat", font=font(50, "SemiBold"), fill=WHITE, anchor="mm")
    for t, (x, y) in ((T_MAP, (B_MAP_TAP[0], B_MAP_TAP[1] - OY)), (T_KAT, mid(B_KAT)), (T_POP, mid(B_POPIS)),
                      (T_FOTO, mid(B_FOTO)), (T_CHK, mid(B_CHECK)), (T_SEND, mid(B_SEND))):
        ripple(d, x, y, f - t)
    return s

# ---------- S2: vyplnění hlášení ----------
FCAPS = [(0, "Klikněte do *mapy*"), (T_KAT - 4, "Vyberte *kategorii*"), (T_POP - 4, "Napište *pár_slov*"),
         (T_FOTO - 6, "Přidejte *fotku*"), (T_SEND - 10, "A *odešlete.*")]
ME_D = AS.ArmSticker(560)

def caption(caps, c, f):
    cur = max([w for t, w in caps if t <= f] or [caps[0][1]], key=lambda w: w.at)
    cur.draw(c, f)

class FormDemo:
    n = T_SEND + 22
    caps = [(t, Words(s, 230, t + 2, 64)) for t, s in FCAPS]
    def render(self, f):
        c = Image.new("RGBA", (W, H), BG + (255,))
        put_phone(c, form_screen(f))
        caption(self.caps, c, f)
        MePoint(895, 6, ME_D).draw(c, f)
        return c
S2 = FormDemo()

# ---------- S3: seznam hlášení se stavem ----------
P_STAT = [box(356, 326, 570, 446), box(600, 326, 820, 446), box(854, 326, 1106, 446)]   # Přijato / V řešení / Vyřešeno
L_RES1 = box(345, 1215, 1060, 1280)
L_DATE1 = box(345, 1300, 735, 1400)
L_OK = [box(935, 548, 1130, 605), box(935, 1528, 1130, 1585)]
L_DATE2 = box(345, 2085, 735, 2200)
LCAPS = [(0, "Sledujte *stav_hlášení*"), (52, "Vidíte, *kdo_to_řeší*"), (100, "i kdy je *hotovo.*")]

def hl_ring(d, b, k, col=G, pad=10, w=8):
    if k < 0:
        return
    p = ease_out_back(clamp(k / 8), 1.4)
    e = (1 - p) * 30
    d.rounded_rectangle([b[0] - pad - e, b[1] - pad - e, b[2] + pad + e, b[3] + pad + e], radius=28,
                        outline=col + (int(255 * clamp(k / 4)),), width=w)

def hl_mark(d, b, k, col=(78, 159, 61)):
    """Zvýrazňovač: zelený pruh se natáhne přes řádek."""
    if k < 0:
        return
    p = ease_out(clamp(k / 10))
    d.rounded_rectangle([b[0] - 8, b[1], b[0] - 8 + (b[2] - b[0] + 16) * p, b[3]], radius=12, fill=col + (60,))

def list_screen(f):
    s = LIST.copy()
    o = Image.new("RGBA", s.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(o)
    for i, b in enumerate(P_STAT):
        if 10 + i * 9 <= f < 52:
            hl_ring(d, b, f - 10 - i * 9, (G if i == 2 else DARK) if f - 10 - i * 9 < 9 or i == 2 else (180, 190, 200), 6)
    hl_mark(d, L_RES1, f - 58)
    hl_mark(d, L_DATE1, f - 106)
    hl_mark(d, L_DATE2, f - 116)
    for i, b in enumerate(L_OK):
        hl_ring(d, b, f - 106 - i * 10, G, 8, 7)
    s.alpha_composite(o)
    return s

class ListDemo:
    n = 165
    caps = [(t, Words(s, 230, t + 2, 64)) for t, s in LCAPS]
    def render(self, f):
        c = Image.new("RGBA", (W, H), BG + (255,))
        # jemné přiblížení k první kartě
        z = 1 + 0.06 * ease_in_out(clamp((f - 40) / 100))
        scr = list_screen(f)
        if z > 1:
            w2, h2 = scr.width / z, scr.height / z
            x0 = (scr.width - w2) * 0.7
            scr = scr.crop((int(x0), 0, int(x0 + w2), int(h2)))
        put_phone(c, scr)
        caption(self.caps, c, f)
        MePoint(895, 6, ME_D).draw(c, f)
        return c
S3 = ListDemo()

# ---------- S1: háček ----------
MINI = 0.6
class IntroPhone(El):
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 14), 1.1)
        ph = PHONE.copy()
        ph.paste(FORM.resize((SCR_W, SCR_H), Image.LANCZOS).convert("RGB"), (58, 58), _pm)
        ph = ph.resize((int(ph.width * MINI), int(ph.height * MINI)), Image.LANCZOS).rotate(4, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(ph, (int(self.cx - ph.width / 2 + (1 - p) * 800), int(self.cy - ph.height / 2)))

SLAM1 = 34
S1 = TextScene(105, BG, [Words("Víte, že *závadu*", 250, 3, 96), Words("ve městě nahlásíte", 370, 10, 84),
                         Words("*z_mobilu?*", 500, 18, 120),
                         IntroPhone(None, 790, 1180, 14),
                         SlamLeft(FE.scaled(FE.ST_PLAIN, 640), 300, 0, SLAM1),
                         Words("Skládka, hřiště, *lampa…*", 660, 54, 60)],
               post=shake_post([SLAM1 + 5], BG))

# ---------- S4: co chceme ----------
S4 = TextScene(120, BG, [Words("Chceme, abyste *viděli,*", 520, 3, 80),
                         Words("za jak dlouho", 680, 16, 96), Words("se to *vyřeší*", 800, 24, 110),
                         Words("a kdo to má *na_starosti.*", 980, 50, 72)])

# ---------- S5: pointa ----------
S5 = TextScene(85, BG, [Words("Ať je jasné, že", 760, 3, 96), Words("*hlásit_má_smysl.*", 900, 14, 110)])

# ---------- S6: závěr ----------
ME_END = AS.ArmSticker(780)
BIG_LOGO = LOGO.resize((int(LOGO.width * 1.2), int(LOGO.height * 1.2)), Image.LANCZOS)
S6 = TextScene(150, BG, [Words("Nahlaste to", 260, 3, 104), Words("*z_mobilu*", 385, 10, 110),
                         El(text_img("hlaseni.tmapy.cz", 72, DARK, w="ExtraBold"), W // 2, 530, 22, dur=11),
                         Pop(BIG_LOGO, 300, 1180, 34, -6),
                         MePoint(770, 50, ME_END)])

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

def tap():
    n = int(0.06 * A.SR); t = A.t_(n)
    return np.sin(2 * np.pi * 1800 * t) * np.exp(-t / 0.012)

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    out.add(0, A.seg_pop(total + .2, 0.55)[: int(total * SR)])
    for a in (3, 10, 18, 54):
        out.add(st[0] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[0] + 14 / FPS, A.fx_whoosh(0.5), 0.5)
    out.add(st[0] + (SLAM1 + 5) / FPS, A.fx_impact(), 0.9)
    for tt, w in S2.caps:
        out.add(st[1] + w.at / FPS, K1.fx_pop(), 0.45)
    for tt in (T_MAP, T_KAT, T_POP, T_FOTO, T_CHK, T_SEND):
        out.add(st[1] + tt / FPS, tap(), 0.5)
    for k in range(0, 26, 2):                       # psaní
        out.add(st[1] + (T_POP + 2 + k) / FPS, A.hat(), 0.18)
    out.add(st[1] + (T_SEND + 2) / FPS, A.fx_ding(), 0.5)
    for tt, w in S3.caps:
        out.add(st[2] + w.at / FPS, K1.fx_pop(), 0.45)
    for a in (10, 19, 28, 58, 106, 116):
        out.add(st[2] + a / FPS, A.hat(), 0.35)
    for a in (3, 16, 24, 50):
        out.add(st[3] + a / FPS, K1.fx_pop(), 0.5)
    for a in (3, 14):
        out.add(st[4] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[4] + 14 / FPS, A.fx_ding(), 0.6)
    for a in (3, 10, 22):
        out.add(st[5] + a / FPS, K1.fx_pop(), 0.5)
    out.add(st[5] + 34 / FPS, A.fx_impact(), 0.5)
    out.add(st[5] + 50 / FPS, A.fx_whoosh(0.4), 0.5)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fo = int(1.2 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:          # náhled: python hlaseni.py <scéna> <snímek> ...
        args = sys.argv[1:]
        for i in range(0, len(args), 2):
            SCENES[int(args[i])].render(int(args[i + 1])).convert("RGB").save(os.path.join(HERE, "hlas", f"p{args[i]}_{args[i+1]}.jpg"))
        sys.exit()
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "hlaseni_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
