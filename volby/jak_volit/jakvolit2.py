"""Jak volit v2: červené křížky u toho, co nejde, animace vhazování lístku Dobré správy a závěr hlavně za Dobrou správu. 1080x1920, 30 fps, se zvukem."""
import os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import audio as A
import festival as FE
import kino as K1
import toaststicker as TS
import jakvolit as J
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, El, TextScene, Slam)
from kino2 import Words
from kino import outline, shake_post

HERE = R.HERE
OUT = os.path.join(HERE, "jak_volit_v2.mp4")
GREY = J.GREY
RED = (214, 48, 58)
LOGO = J.LOGO
Pop = J.Pop

# ---------- S5: nemůžete přijít? – červené křížky ----------
def mark_icon(kind, d=124):
    img = Image.new("RGBA", (d + 16, d + 16), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    col = RED if kind == "no" else G
    dr.ellipse([8, 8, 8 + d, 8 + d], fill=col)
    c = 8 + d / 2
    if kind == "no":
        o = d * .22
        for a, b in (((c - o, c - o), (c + o, c + o)), ((c - o, c + o), (c + o, c - o))):
            dr.line([a, b], fill=WHITE, width=int(d * .13))
        for p in ((c - o, c - o), (c + o, c + o), (c - o, c + o), (c + o, c - o)):
            dr.ellipse([p[0] - d * .065, p[1] - d * .065, p[0] + d * .065, p[1] + d * .065], fill=WHITE)
    else:
        dr.line([(c - d * .24, c + d * .01), (c - d * .06, c + d * .2), (c + d * .27, c - d * .17)], fill=WHITE, width=int(d * .13), joint="curve")
    return outline(img, 5)

def info_card2(title, text, kind):
    img = J.card(920, 210)
    d = ImageDraw.Draw(img)
    if kind == "no":
        d.rounded_rectangle([20, 20, 34, 230], radius=7, fill=RED)
    d.text((220, 58), title, font=font(50, "ExtraBold"), fill=DARK)
    d.text((220, 128), text, font=font(40, "SemiBold"), fill=GREY)
    return img

class Cross(El):
    """Ikona se ‚přibije‘: zvětšená dopadne na kartu a krátce zatřese."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out(clamp((k + 1) / 6))
        s = 2.2 - 1.2 * p
        rot = 0 if k < 6 else 6 * math.sin((k - 6) * 1.7) * math.exp(-(k - 6) / 4)
        img = self.img.resize((int(self.img.width * s), int(self.img.height * s)), Image.BILINEAR)
        if rot:
            img = img.rotate(rot, expand=True, resample=Image.BICUBIC)
        if p < 1:
            img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * clamp(p * 1.6))))
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

IC_NO, IC_OK = mark_icon("no"), mark_icon("ok")
def card_row(title, text, kind, cy, at):
    ic = IC_NO if kind == "no" else IC_OK
    return [Pop(info_card2(title, text, kind), W // 2, cy, at, -1), Cross(ic, W // 2 - 350, cy - 10, at + 8)]
S5 = TextScene(175, BG, [Words("Nemůžete přijít?", 300, 3, 110)]
               + card_row("Voličský průkaz?", "U komunálních voleb nejde.", "no", 620, 18)
               + card_row("Ze zahraničí?", "Komunální volby to neumožňují.", "no", 880, 38)
               + card_row("Nemoc?", "Požádejte úřad o přenosnou urnu.", "ok", 1140, 58)
               + [Words("Volí se *osobně.*", 1450, 84, 96)])

# ---------- S5b: lístek Dobré správy putuje do urny ----------
PW, PH = 340, 440
def ballot_paper():
    paper_h = PH
    tot_h = int((paper_h - 14) / 0.70)
    img = Image.new("RGBA", (PW + 20, tot_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, PW + 10, paper_h + 10], radius=16, fill=WHITE, outline=(200, 208, 220), width=5)
    lg = LOGO.resize((290, int(LOGO.height * 290 / LOGO.width)), Image.LANCZOS)
    img.alpha_composite(lg, (10 + (PW - lg.width) // 2, 24))
    y0 = 24 + lg.height + 14
    for i in range(4):
        y = y0 + i * 52
        d.rounded_rectangle([40, y, 78, y + 38], radius=7, outline=DARK, width=5)
        d.rounded_rectangle([98, y + 10, 98 + (190 if i == 0 else 150 - i * 10), y + 28], radius=8, fill=(214, 220, 228) if i else (190, 214, 184))
        if i == 0:
            d.line([(46, y + 20), (58, y + 32), (78, y + 4)], fill=G, width=8, joint="curve")
    return img
BALLOT = ballot_paper()
EMPTY = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
KW = 700
ME_B = TS.ToastSticker(KW, BALLOT, gscale=1.0)
ME_E = TS.ToastSticker(KW, EMPTY)
ks = ME_B.s
LP = 340
class Padded:
    def __init__(self, me):
        w, h = me.base.size
        self.base = Image.new("RGBA", (w + LP, h), (0, 0, 0, 0)); self.base.alpha_composite(me.base, (LP, 0))
        self.arm = Image.new("RGBA", (w + LP, h), (0, 0, 0, 0)); self.arm.alpha_composite(me.arm, (LP, 0))
        self.pivot = (me.pivot[0] + LP, me.pivot[1])
    def image(self, angle):
        out = Image.new("RGBA", self.base.size, (0, 0, 0, 0))
        out.alpha_composite(self.base)
        out.alpha_composite(self.arm.rotate(angle, center=self.pivot, resample=Image.BICUBIC))
        return out
ME_B_P, ME_E_P = Padded(ME_B), Padded(ME_E)
# střed lístku v souřadnicích samolepky (před otočením), bez ohledu na ruku
g_x = TS.PINCH[0] + 4
g_y = TS.PINCH[1] + TS.PAD - BALLOT.height * .70
P_REL0 = ((g_x) * ks, (g_y + (PH + 20) / 2) * ks)          # střed papíru
PIV = ME_B.pivot
TH_MAX = 34.0
def rot_about(p, th):
    r = math.radians(th); vx, vy = p[0] - PIV[0], p[1] - PIV[1]
    return (PIV[0] + vx * math.cos(r) + vy * math.sin(r), PIV[1] - vx * math.sin(r) + vy * math.cos(r))
PH_S = (PH + 20) * ks
PW_S = (PW + 20) * ks
SLOT_X = 330
K_Y0 = H + 30 - ME_B.base.height
PIV_ABS = None
cen = rot_about(P_REL0, TH_MAX)
K_X0 = SLOT_X - cen[0]
SLOT_Y = K_Y0 + cen[1] + PH_S / 2 + 70
BOX_S = 520
BOX = J.ballot_box(420).resize((BOX_S, BOX_S), Image.LANCZOS)
BOX_SLOT = (BOX_S / 2, 177 * BOX_S / 420)
BOX_X0, BOX_Y0 = SLOT_X - BOX_SLOT[0], SLOT_Y - BOX_SLOT[1]
print("geom", round(K_X0), round(K_Y0), round(SLOT_Y), round(BOX_Y0 + BOX_S), "paper", round(PW_S), round(PH_S))

T_IN, T_SW0, T_SW1, T_REL, T_FALL = 12, 34, 56, 58, 16
class Vote(El):
    def theta(self, f):
        if f < T_SW0:
            return 0.0
        if f < T_SW1:
            return TH_MAX * ease_in_out((f - T_SW0) / (T_SW1 - T_SW0))
        if f < T_SW1 + 4:
            return TH_MAX
        k = f - T_SW1 - 4
        return TH_MAX * (1 - ease_out_back(clamp(k / 16), 1.5)) + (3 * math.sin(k * .5) * math.exp(-k / 8) if k > 10 else 0)
    def draw(self, c, f):
        k = f - T_IN
        dy = (1 - ease_out_back(clamp(k / 12), 1.2)) * 1100 if k >= 0 else 1100
        t_land = T_REL + T_FALL
        # urna (s ‚nárazem‘ po vhození)
        kb = f - t_land
        bs = 1 + (0.06 * math.sin(kb * .9) * math.exp(-kb / 5) if kb >= 0 else 0)
        bimg = BOX if bs == 1 else BOX.resize((int(BOX_S * bs), int(BOX_S * bs)), Image.BILINEAR)
        ub = clamp((f - 4) / 10)
        bdy = (1 - ease_out_back(ub, 1.2)) * 600
        bx = int(BOX_X0 + BOX_S / 2 - bimg.width / 2); by = int(BOX_Y0 + BOX_S - bimg.height + bdy)
        c.alpha_composite(bimg, (bx, by))
        th = self.theta(f)
        released = f >= T_REL
        # padající lístek (oříznutý v otvoru urny)
        if released and f < t_land + 3:
            p = clamp((f - T_REL) / T_FALL)
            c0 = rot_about(P_REL0, TH_MAX)
            sx0, sy0 = K_X0 + c0[0], K_Y0 + c0[1]
            ex, ey = SLOT_X, SLOT_Y + PH_S / 2 - 6
            x = sx0 + (ex - sx0) * ease_out(p); y = sy0 + (ey - sy0) * p * p
            ang = TH_MAX * (1 - ease_out(p))
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            pimg = BALLOT.crop((0, 0, BALLOT.width, int(PH + 20))).resize((int(PW_S), int(PH_S)), Image.LANCZOS)
            pimg = pimg.rotate(ang, expand=True, resample=Image.BICUBIC)
            lay.alpha_composite(pimg, (int(x - pimg.width / 2), int(y - pimg.height / 2)))
            c.alpha_composite(lay.crop((0, 0, W, int(SLOT_Y))), (0, 0))
        # Karel (před urnou – ruka sahá nad ni)
        me = ME_E_P if released else ME_B_P
        img = me.image(th)
        c.alpha_composite(img, (int(K_X0 - LP), int(K_Y0 + dy)))
        # jiskra a fajfka po vhození
        t = f - t_land
        if 0 <= t < 16:
            d = ImageDraw.Draw(c)
            aa = 1 - t / 16; r = 36 + t * 7
            for i in range(10):
                ang = i * math.pi / 5
                d.line([(SLOT_X + math.cos(ang) * r * .5, SLOT_Y + math.sin(ang) * r * .5 - 20),
                        (SLOT_X + math.cos(ang) * r, SLOT_Y + math.sin(ang) * r - 20)], fill=(120, 190, 100, int(255 * aa)), width=8)
        if t >= 10:
            p = ease_out_back(clamp((t - 10) / 10), 1.8)
            ic = IC_OK.resize((int(IC_OK.width * 1.25 * p) + 2, int(IC_OK.height * 1.25 * p) + 2), Image.BILINEAR)
            c.alpha_composite(ic, (int(SLOT_X + 140 - ic.width / 2), int(BOX_Y0 + 60 - ic.height / 2)))

S5B = TextScene(150, BG, [Words("Dejte hlas", 290, 3, 112), Words("*Dobré_správě.*", 430, 11, 124),
                          Vote(None, 0, 0, 0)])

# ---------- S6: závěr hlavně za Dobrou správu ----------
SL6 = 40
ROLE = "vedoucí týmu digitalizace a automatizace"
LOGO_S = LOGO.resize((int(LOGO.width * .8), int(LOGO.height * .8)), Image.LANCZOS)
def corner_badge():
    f = font(40, "ExtraBold")
    label = "kandidátka č. 3"
    tw = int(f.getlength(label)); d_ = 112
    w, h = tw + d_ + 70, d_ + 24
    img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle([10, 10, 10 + w, 10 + h], radius=h // 2, fill=WHITE)
    dr.text((10 + 38, 10 + h / 2), label, font=f, fill=DARK, anchor="lm")
    cx0 = 10 + w - d_ - 12
    dr.ellipse([cx0, 22, cx0 + d_, 22 + d_], fill=G)
    dr.text((cx0 + d_ / 2, 10 + h / 2 + 4), "3", font=font(92, "ExtraBold"), fill=WHITE, anchor="mm")
    return outline(img, 6)
BADGE = corner_badge()
LOGO_S = LOGO.resize((int(LOGO.width * 1.0), int(LOGO.height * 1.0)), Image.LANCZOS)
S6 = TextScene(175, BG, [Pop(BADGE, W - 40 - BADGE.width // 2, 215, 14, 3),
                         Words("Přijďte volit!", 390, 3, 118),
                         El(text_img("9.–10. října", 112, WHITE, w="ExtraBold", pill=G, pad=(50, 20)), W // 2, 540, 12, dur=11),
                         El(text_img("Karel Krupička", 72, DARK, w="ExtraBold"), W // 2, 720, 30, dur=11),
                         El(text_img(ROLE, 36, GREY, w="SemiBold"), W // 2, 788, 38, "rise"),
                         El(text_img("dobrasprava.cz", 62, GD, w="ExtraBold"), W // 2, 870, 46, "rise"),
                         Slam(FE.scaled(FE.ST_PLAIN, 860), W // 2 + 40, 0, SL6),
                         Pop(LOGO_S, 250, 1560, SL6 + 16, -6)],
               post=shake_post([SL6 + 5], BG))

SCENES = [J.S1, J.S2, J.S3, J.S4, S5, S5B, S6]
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

def thud():
    n = int(0.25 * A.SR); t = A.t_(n)
    return np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.08) + 0.3 * np.sin(2 * np.pi * 140 * t) * np.exp(-t / 0.05)

def build_audio(path):
    SR = A.SR
    st, t = [], 0
    for sc in SCENES:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    out.add(0, A.seg_pop(total + .2, 0.55)[: int(total * SR)])
    pops = {0: (3, 12, 20, 26, 32, 38, 44, 54), 1: (3, 14, 30, 60, 68), 2: (3, 12, 28, 36, 44, 60), 3: (3, 10, 70), 4: (3,),
            5: (3, 11), 6: (3, 12, 24, 38, 44, 50, SL6 + 16)}
    for i, lst in pops.items():
        for a in lst:
            out.add(st[i] + a / FPS, K1.fx_pop(), 0.5)
    for j in range(3):
        out.add(st[0] + (30 + 40 * j + 22) / FPS, A.kick(0.6), 0.5)
    for i in range(17):
        out.add(st[3] + (24 + i * 2) / FPS, K1.fx_pop(), 0.2)
    out.add(st[3] + 70 / FPS, A.fx_ding(), 0.7)
    # křížky: ‚cvak‘ + hluboký dopad
    for a in (18, 38):
        out.add(st[4] + (a + 8) / FPS, A.fx_impact(), 0.45)
        out.add(st[4] + (a + 8) / FPS, A.kick(0.5), 0.35)
    out.add(st[4] + 18 / FPS, K1.fx_pop(), 0.5); out.add(st[4] + 38 / FPS, K1.fx_pop(), 0.5); out.add(st[4] + 58 / FPS, K1.fx_pop(), 0.5)
    out.add(st[4] + 66 / FPS, A.fx_ding(), 0.6)
    out.add(st[4] + 84 / FPS, K1.fx_pop(), 0.5)
    # vhazování lístku
    out.add(st[5] + T_IN / FPS, A.fx_whoosh(0.4), 0.5)
    out.add(st[5] + T_SW0 / FPS, A.fx_whoosh(0.3), 0.4)
    out.add(st[5] + T_REL / FPS, K1.fx_pop(), 0.4)
    out.add(st[5] + (T_REL + T_FALL) / FPS, thud(), 0.8)
    out.add(st[5] + (T_REL + T_FALL + 10) / FPS, A.fx_ding(), 0.7)
    out.add(st[6] + 12 / FPS, A.fx_ding(), 0.6)
    out.add(st[6] + (SL6 + 5) / FPS, A.fx_impact(), 0.8)
    out.add(st[6] + 14 / FPS, A.fx_whoosh(0.3), 0.4)
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
            SCENES[int(args[i])].render(int(args[i + 1])).convert("RGB").save(os.path.join(HERE, "hlas", f"j{args[i]}_{args[i+1]}.jpg"))
        sys.exit()
    total = sum(s.n for s in SCENES)
    print("snímků:", total, "délka:", round(total / FPS, 2), "s")
    AUD = os.path.join(HERE, "jakvolit2_audio.wav")
    build_audio(AUD)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k, fr in enumerate(frames()):
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("hotovo:", OUT)
