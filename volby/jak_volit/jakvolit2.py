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

# ---------- Jak označit lístek: 3 způsoby (podle Ministerstva vnitra) ----------
import random
CARD_W, CARD_H = 960, 930
COLW, GAP, PADX = 290, 20, 25
ROWS, ROW_H, HEAD_H = 17, 44, 130
LIT = (217, 234, 210)
LOST = (250, 226, 226)
_rng = random.Random(11)
BARS = [[_rng.randint(120, 214) for _ in range(ROWS)] for _ in range(3)]
PARTY = ["Dobrá správa", "Strana A", "Strana B"]

def col_x(i):
    return PADX + i * (COLW + GAP)

def row_y(r):
    return HEAD_H + 30 + r * ROW_H

def draw_x(d, cx, cy, size, k):
    """Křížek perem: dvě čáry se nakreslí postupně (k = snímky od označení)."""
    if k < 0:
        return
    o = size * .5
    p1 = ease_out(clamp(k / 4))
    d.line([(cx - o, cy - o), (cx - o + 2 * o * p1, cy - o + 2 * o * p1)], fill=DARK, width=7)
    p2 = ease_out(clamp((k - 3) / 4))
    if p2 > 0:
        d.line([(cx + o, cy - o), (cx + o - 2 * o * p2, cy - o + 2 * o * p2)], fill=DARK, width=7)

def ballot_card(f, cfg):
    img = Image.new("RGBA", (CARD_W + 60, CARD_H + 80), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 44, 30 + CARD_W, 44 + CARD_H], radius=40, fill=(27, 38, 59, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    ox, oy = 30, 30
    d.rounded_rectangle([ox, oy, ox + CARD_W, oy + CARD_H], radius=40, fill=WHITE)
    lit, lost, crosses = set(), set(), []     # (col,row) rozsvícené / ztracené řádky
    head_cross_k = None
    if cfg["party_at"] is not None and f >= cfg["party_at"]:
        head_cross_k = f - cfg["party_at"]
        rf = cfg.get("row_f", 2)
        n_lit = ((f - cfg["light_at"]) // rf + 1) if f >= cfg["light_at"] else 0
        n_lit = min(n_lit, cfg["n_party"])
        for r in range(n_lit):
            lit.add((0, r))
        if cfg.get("lost_at") is not None and f >= cfg["lost_at"]:
            for r in range(cfg["n_party"], ROWS):
                lost.add((0, r))
    for (c, r, at) in cfg["indiv"]:
        if f >= at:
            crosses.append((c, r, f - at))
            lit.add((c, r))
    for c in range(3):
        x = ox + col_x(c)
        is_ds = c == 0
        d.rounded_rectangle([x, oy + 24, x + COLW, oy + CARD_H - 24], radius=22, outline=G if is_ds else (214, 220, 228), width=5 if is_ds else 3)
        d.rounded_rectangle([x + 3, oy + 27, x + COLW - 3, oy + 24 + HEAD_H], radius=19, fill=GL if is_ds else (240, 243, 246))
        d.rounded_rectangle([x + 20, oy + 24 + HEAD_H // 2 - 22, x + 64, oy + 24 + HEAD_H // 2 + 22], radius=8, outline=DARK, width=5, fill=WHITE)
        f_h = font(30 if is_ds else 30, "ExtraBold")
        d.text((x + 84, oy + 24 + HEAD_H // 2), PARTY[c], font=f_h, fill=DARK if is_ds else (110, 122, 140), anchor="lm")
        for r in range(ROWS):
            y = oy + row_y(r)
            if (c, r) in lit:
                d.rounded_rectangle([x + 8, y - ROW_H // 2 + 3, x + COLW - 8, y + ROW_H // 2 - 3], radius=10, fill=LIT)
            elif (c, r) in lost:
                d.rounded_rectangle([x + 8, y - ROW_H // 2 + 3, x + COLW - 8, y + ROW_H // 2 - 3], radius=10, fill=LOST)
            d.rounded_rectangle([x + 20, y - 13, x + 46, y + 13], radius=5, outline=(90, 104, 128), width=3)
            d.rounded_rectangle([x + 62, y - 7, x + 62 + BARS[c][r] // 1 - 40, y + 7], radius=7, fill=(205, 212, 222))
            if (c, r) in lost and f >= cfg["lost_at"] + 4 * (r - cfg["n_party"]):
                d.line([(x + COLW - 50, y), (x + COLW - 26, y)], fill=RED, width=6)
    if head_cross_k is not None:
        x = ox + col_x(0)
        draw_x(d, x + 42, oy + 24 + HEAD_H // 2, 38, head_cross_k)
    for (c, r, k) in crosses:
        x = ox + col_x(c)
        draw_x(d, x + 33, oy + row_y(r), 30, k)
    return img, lit, lost

class BallotDemo(El):
    def __init__(self, cfg, at):
        super().__init__(None, W // 2, 1010, at); self.cfg = cfg
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 12), 1.15)
        img, lit, lost = ballot_card(k, self.cfg)
        s = 0.55 + 0.45 * p
        if s != 1:
            img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
        a = clamp(k / 6)
        if a < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

class Counter(El):
    """Kolik hlasů dostane Dobrá správa – počítá se podle rozsvícených řádků."""
    def __init__(self, cfg, at, mode, bat=8):
        super().__init__(None, W // 2, 1560, at); self.cfg, self.mode, self.bat = cfg, mode, bat
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        _, lit, lost = ballot_card(f - self.bat, self.cfg)
        if self.mode == "party":
            n = sum(1 for (cc, r) in lit if cc == 0)
            txt = f"{n} hlasů"
        elif self.mode == "indiv":
            n = len(lit)
            txt = f"{n} {'hlas' if n == 1 else 'hlasy' if 2 <= n <= 4 else 'hlasů'}"
        else:
            if f - self.bat < self.cfg["lost_at"] + 6:
                n = len(lit)
                txt = f"{n} {'hlas' if n == 1 else 'hlasy' if 2 <= n <= 4 else 'hlasů'}"
            else:
                txt = f"{self.cfg['n_party']} + {self.cfg['n_ind']} = 17"
        t = text_img(txt, 62, WHITE, w="ExtraBold", pill=G, pad=(46, 16), radius=36)
        p = ease_out_back(clamp(k / 8), 1.6)
        t = t.resize((max(2, int(t.width * (.6 + .4 * p))), max(2, int(t.height * (.6 + .4 * p)))), Image.BILINEAR)
        c.alpha_composite(t, (int(self.cx - t.width / 2), int(self.cy - t.height / 2)))

def step_pill(i):
    return text_img(f"Jak označit lístek  ·  {i}/3", 38, GD, w="ExtraBold", pill=(226, 240, 222), pad=(26, 10), radius=24)
def sub_t(text, size=46):
    return text_img(text, size, GREY, w="SemiBold")

CFG1 = dict(party_at=44, light_at=60, n_party=17, row_f=3, indiv=[])
CFG2 = dict(party_at=None, light_at=0, n_party=0, indiv=[(0, 1, 50), (0, 8, 76), (1, 3, 102), (1, 11, 128), (2, 5, 154)])
CFG3 = dict(party_at=130, light_at=142, n_party=14, n_ind=3, lost_at=190, row_f=3, indiv=[(1, 3, 46), (1, 10, 72), (2, 6, 98)])

V1 = TextScene(205, BG, [El(step_pill(1), W // 2, 190, 0, "rise", dur=8),
                         Words("Celá *strana*", 290, 3, 108),
                         El(sub_t("Jeden křížek u názvu strany."), W // 2, 395, 18, "rise"),
                         BallotDemo(CFG1, 10), Counter(CFG1, 64, "party", 10),
                         El(sub_t("Hlas dostane všech 17 kandidátů strany.", 44), W // 2, 1690, 124, "rise")])
V2 = TextScene(250, BG, [El(step_pill(2), W // 2, 190, 0, "rise", dur=8),
                         Words("Jednotlivé *osoby*", 290, 3, 108),
                         El(sub_t("Křížky u jmen, klidně z různých stran."), W // 2, 395, 18, "rise"),
                         BallotDemo(CFG2, 10), Counter(CFG2, 60, "indiv", 10),
                         El(sub_t("Označit můžete nejvýše 17 kandidátů.", 44), W // 2, 1690, 176, "rise")])
V3 = TextScene(305, BG, [El(step_pill(3), W // 2, 190, 0, "rise", dur=8),
                         Words("Obojí *dohromady*", 290, 3, 108),
                         El(sub_t("Strana a navíc jména z jiných stran."), W // 2, 395, 18, "rise"),
                         BallotDemo(CFG3, 10), Counter(CFG3, 54, "mix", 10),
                         El(sub_t("Straně se ubere tolik hlasů,", 46), W // 2, 1680, 206, "rise"),
                         El(sub_t("kolik jste dali jiným kandidátům.", 46), W // 2, 1744, 220, "rise")])

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
T_EXIT = 100
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
        if f < T_EXIT:
            return self.draw_in(c, f)
        if f > T_EXIT + 18:
            return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.draw_in(lay, f)
        dy = int(1300 * ease_in_out(clamp((f - T_EXIT) / 18)))
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.paste(lay, (0, dy))
        c.alpha_composite(out)
    def draw_in(self, c, f):
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
LOGO_XL = LOGO.resize((960, int(LOGO.height * 960 / LOGO.width)), Image.LANCZOS)
_bl = Image.new("RGBA", (W + 300, H + 300), (0, 0, 0, 0))
_bd = ImageDraw.Draw(_bl)
for cx, cy, r, a in ((900, 420, 460, 34), (150, 1450, 420, 26), (1000, 1700, 320, 18)):
    _bd.ellipse([cx - r + 150, cy - r + 150, cx + r + 150, cy + r + 150], fill=G + (a,))
_bl = _bl.filter(ImageFilter.GaussianBlur(80))
def bg_fx(c, f):
    ox, oy = int(150 + 24 * math.sin(f * .02)), int(150 + 18 * math.cos(f * .017))
    c.alpha_composite(_bl.crop((ox, oy, ox + W, oy + H)))

class LogoSlam(El):
    """Velké logo dopadne na obrazovku, zatřese se a pak jemně dýchá."""
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        IN = 7
        if k < IN:
            p = ease_out((k + 1) / IN)
            s, a, rot = 1.9 - 0.9 * p, clamp(p * 1.5), -9 * (1 - p) - 4 * p
            dx = 0
        else:
            t = k - IN
            dec = math.exp(-t / 6)
            s = 1 + 0.04 * math.sin(t * 1.3) * dec + 0.012 * math.sin(t * .09)
            rot = -4 + 4 * math.sin(t * 1.9) * dec + 0.8 * math.sin(t * .07)
            dx = 20 * math.sin(t * 2.4) * dec
            a = 1
        img = self.img.resize((int(self.img.width * s), int(self.img.height * s)), Image.BILINEAR)
        img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
        if a < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        c.alpha_composite(img, (int(self.cx - img.width / 2 + dx), int(self.cy - img.height / 2)))

SL6 = 116
BADGE_L = BADGE.resize((int(BADGE.width * 1.35), int(BADGE.height * 1.35)), Image.LANCZOS)
LOGO_M = LOGO.resize((820, int(LOGO.height * 820 / LOGO.width)), Image.LANCZOS)
S5B = TextScene(235, BG, [Words("Dejte hlas", 290, 3, 112), Words("*Dobré_správě.*", 430, 11, 124),
                          Vote(None, 0, 0, 0),
                          Words("Přijďte volit!", 610, T_EXIT + 4, 86),
                          El(text_img("9.–10. října", 104, WHITE, w="ExtraBold", pill=G, pad=(54, 20)), W // 2, 730, T_EXIT + 12, dur=11),
                          LogoSlam(LOGO_M, W // 2, 1150, SL6),
                          Pop(BADGE_L, W // 2, 1600, SL6 + 24, 2)],
               extra=bg_fx, post=shake_post([SL6 + 6], BG, amp=18))

SCENES = [J.S1, J.S2, J.S3, J.S4, V1, V2, V3, S5, S5B]
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
    pops = {0: (3, 12, 20, 26, 32, 38, 44, 54), 1: (3, 14, 30, 60, 68), 2: (3, 12, 28, 36, 44, 60), 3: (3, 10, 70), 7: (3,),
            8: (3, 11)}
    for i, lst in pops.items():
        for a in lst:
            out.add(st[i] + a / FPS, K1.fx_pop(), 0.5)
    for j in range(3):
        out.add(st[0] + (30 + 40 * j + 22) / FPS, A.kick(0.6), 0.5)
    for i in range(17):
        out.add(st[3] + (24 + i * 2) / FPS, K1.fx_pop(), 0.2)
    out.add(st[3] + 70 / FPS, A.fx_ding(), 0.7)
    # tři způsoby hlasování (pomaleji)
    for i in range(3):
        for a in (3, 8, 18):
            out.add(st[4 + i] + a / FPS, K1.fx_pop(), 0.45)
    out.add(st[4] + 44 / FPS, A.kick(0.5), 0.35)
    for r in range(17):
        out.add(st[4] + (60 + 3 * r) / FPS, K1.fx_pop(), 0.12)
    out.add(st[4] + 112 / FPS, A.fx_ding(), 0.6); out.add(st[4] + 124 / FPS, K1.fx_pop(), 0.5)
    for a in (50, 76, 102, 128, 154):
        out.add(st[5] + a / FPS, A.kick(0.45), 0.35)
    out.add(st[5] + 60 / FPS, A.fx_ding(), 0.4); out.add(st[5] + 176 / FPS, K1.fx_pop(), 0.5)
    for a in (46, 72, 98, 130):
        out.add(st[6] + a / FPS, A.kick(0.45), 0.35)
    for r in range(14):
        out.add(st[6] + (142 + 3 * r) / FPS, K1.fx_pop(), 0.12)
    out.add(st[6] + 190 / FPS, A.fx_impact(), 0.45); out.add(st[6] + 206 / FPS, K1.fx_pop(), 0.5); out.add(st[6] + 220 / FPS, K1.fx_pop(), 0.5)
    # křížky: ‚cvak‘ + hluboký dopad
    for a in (18, 38):
        out.add(st[7] + (a + 8) / FPS, A.fx_impact(), 0.45)
        out.add(st[7] + (a + 8) / FPS, A.kick(0.5), 0.35)
    out.add(st[7] + 18 / FPS, K1.fx_pop(), 0.5); out.add(st[7] + 38 / FPS, K1.fx_pop(), 0.5); out.add(st[7] + 58 / FPS, K1.fx_pop(), 0.5)
    out.add(st[7] + 66 / FPS, A.fx_ding(), 0.6)
    out.add(st[7] + 84 / FPS, K1.fx_pop(), 0.5)
    # vhazování lístku
    out.add(st[8] + T_IN / FPS, A.fx_whoosh(0.4), 0.5)
    out.add(st[8] + T_SW0 / FPS, A.fx_whoosh(0.3), 0.4)
    out.add(st[8] + T_REL / FPS, K1.fx_pop(), 0.4)
    out.add(st[8] + (T_REL + T_FALL) / FPS, thud(), 0.8)
    out.add(st[8] + (T_REL + T_FALL + 10) / FPS, A.fx_ding(), 0.7)
    out.add(st[8] + (T_EXIT + 2) / FPS, A.fx_whoosh(0.4), 0.5)
    out.add(st[8] + (T_EXIT + 4) / FPS, K1.fx_pop(), 0.5); out.add(st[8] + (T_EXIT + 12) / FPS, K1.fx_pop(), 0.5)
    out.add(st[8] + (SL6 + 6) / FPS, A.fx_impact(), 0.9)
    out.add(st[8] + (SL6 + 24) / FPS, A.fx_ding(), 0.6)
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
