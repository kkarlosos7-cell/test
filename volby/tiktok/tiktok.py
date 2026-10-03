"""TikTok série: Co jsou komunální volby + Jak volit. 1080x1920, 30 fps, se zvukem. Důležité věci nad spodní UI zónou TikToku (cca y < 1500)."""
import os, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
import audio as A
import kino as K1
import jakvolit2 as JV
from jakvolit2 import (ballot_card, BallotDemo, Counter, CFG1, CFG2, CFG3, option_card, SlideIn, card_row, IC_OK, IC_NO,
                       step_pill, sub_t, LogoSlam, bg_fx, BADGE_L, LOGO, J, thud)
from render import (W, H, FPS, DARK, G, GD, GL, BG, WHITE, font, clamp, ease_out, ease_out_back, ease_in_out,
                    text_img, El, TextScene)
from kino2 import Words
from kino import outline, shake_post

HERE = R.HERE
JV.PARTY[:] = ["Kandidátka A", "Kandidátka B", "Kandidátka C"]     # obecný lístek bez značky
JV.HDR_SIZE[:] = [27, 27, 27]
OUTDIR = os.path.join(HERE, "tiktok"); os.makedirs(OUTDIR, exist_ok=True)
Pop = J.Pop
GREY = J.GREY

# ---------- společné prvky ----------
import festival as FE
import armsticker as AS
from podzim import logo_sticker

class BallotDemoT(BallotDemo):
    def __init__(self, cfg, at, cy=790, sc=0.74):
        super().__init__(cfg, at); self.cy, self.sc = cy, sc
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 12), 1.15)
        img, lit, lost = ballot_card(k, self.cfg)
        s = (0.55 + 0.45 * p) * self.sc
        img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
        a = clamp(k / 6)
        if a < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

class CounterT(Counter):
    def __init__(self, cfg, at, mode, bat=10, cy=1190, cx=380):
        super().__init__(cfg, at, mode, bat); self.cy, self.cx = cy, cx

# ---- samolepky pro reakce ----
def headphones_on(im):
    im = im.copy(); d = ImageDraw.Draw(im)
    d.arc([402, 318, 800, 760], 188, 352, fill=DARK, width=34)
    for x0 in (372, 770):
        d.rounded_rectangle([x0, 600, x0 + 66, 730], radius=30, fill=DARK)
        d.rounded_rectangle([x0 + 10, 618, x0 + 56, 712], radius=22, fill=G)
    return im
KOVBOJ = Image.open(os.path.join(HERE, "kovboj.png")).convert("RGBA")
ST = {"swag": FE.ST_SWAG, "hat": FE.ST_HAT, "plain": FE.ST_PLAIN, "head": headphones_on(FE.BASE), "kov": KOVBOJ}
_ARM = AS.ArmSticker(520)

class Reaction(El):
    """Karel se objeví v pravém dolním rohu (nad spodní UI zónou TikToku) a jemně se pohupuje."""
    def __init__(self, kind, at, cx=870, bottom=1690, w=500):
        super().__init__(None, cx, bottom, at); self.kind, self.w = kind, w
        self.img = None if kind == "point" else FE.fade_bottom(FE.scaled(ST[kind], w), 0.28)
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 12), 1.6)
        img = self.img
        if self.kind == "point":
            img = FE.fade_bottom(_ARM.image(-8 + 7 * math.sin(f * .22)), 0.25)
        s = .35 + .65 * p
        im2 = img.resize((max(2, int(img.width * s)), max(2, int(img.height * s))), Image.BILINEAR)
        bob = 7 * math.sin(f * .13)
        c.alpha_composite(im2, (int(self.cx - im2.width / 2), int(self.cy - im2.height + bob)))

def bubble_img(text, size=50):
    f = font(size, "ExtraBold")
    tw = int(f.getlength(text))
    w, h = tw + 80, size + 56
    img = Image.new("RGBA", (w + 40, h + 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], radius=(h) // 2, fill=WHITE)
    d.polygon([(20 + w - 90, 20 + h - 6), (20 + w - 40, 20 + h - 6), (20 + w - 40, 20 + h + 44)], fill=WHITE)
    d.text((20 + w / 2, 20 + h / 2), text, font=f, fill=DARK, anchor="mm")
    return outline(img, 6)

class Bubble(El):
    def __init__(self, text, cx, cy, at, rot=-3, size=50):
        super().__init__(bubble_img(text, size), cx, cy, at); self.rot = rot
    def draw(self, c, f):
        k = f - self.at
        if k < 0:
            return
        p = ease_out_back(clamp(k / 9), 1.8)
        img = self.img.resize((max(2, int(self.img.width * (.4 + .6 * p))), max(2, int(self.img.height * (.4 + .6 * p)))), Image.BILINEAR)
        img = img.rotate(self.rot * p + 1.2 * math.sin(f * .1), expand=True, resample=Image.BICUBIC)
        c.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2)))

def rx(kind, at, text, bx=720, by=1180, rot=-3, size=50, **kw):
    """Reakce: samolepka + bublina s hláškou."""
    return []

class PeopleT(El):
    def __init__(self, y0, at):
        super().__init__(None, 0, 0, at); self.y0 = y0
    def draw(self, c, f):
        d = ImageDraw.Draw(c)
        for i in range(17):
            k = f - self.at - i * 2
            if k < 0:
                continue
            p = ease_out_back(clamp(k / 8))
            row, col = divmod(i, 6)
            n_in_row = 6 if row < 2 else 5
            x = W / 2 + (col - (n_in_row - 1) / 2) * 140
            y = self.y0 + row * 175
            s = p
            col_ = G if i % 3 == 0 else (GD if i % 3 == 1 else DARK)
            d.ellipse([x - 30 * s, y - 74 * s, x + 30 * s, y - 14 * s], fill=col_)
            d.rounded_rectangle([x - 48 * s, y - 8 * s, x + 48 * s, y + 84 * s], radius=int(32 * s) + 1, fill=col_)

def S(n, els):
    return TextScene(n, BG, els, extra=bg_fx)

# ---- koncovka: jasně Starý Plzenec + Dobrá správa ----
LOGO_E = LOGO.resize((640, int(LOGO.height * 640 / LOGO.width)), Image.LANCZOS)
END_SW = FE.fade_bottom(FE.scaled(FE.ST_SWAG, 640), 0.25)
def end_card():
    pill = text_img("Starý Plzenec  ·  kandidátka č. 3", 48, WHITE, w="ExtraBold", pill=G, pad=(40, 16), radius=34)
    return TextScene(110, BG, [Words("Přijďte volit!", 290, 3, 116),
                               El(text_img("9.–10. října", 100, WHITE, w="ExtraBold", pill=DARK, pad=(50, 18)), W // 2, 490, 10, dur=11),
                               LogoSlam(LOGO_E, W // 2, 780, 18),
                               El(pill, W // 2, 1040, 36, dur=10),
                               Reaction("swag", 46, cx=W // 2, bottom=1700, w=600)],
                     extra=bg_fx, post=shake_post([24], BG, amp=14))
END_EV = [(0, 'pop', 3), (0, 'pop', 10), (0, 'impact', 24), (0, 'ding', 25), (0, 'pop', 36), (0, 'whoosh', 46), (0, 'pop', 56), (0, 'ding', 58)]

def fact_card(text, kind="ok"):
    w, h = 940, 150
    img = Image.new("RGBA", (w + 60, h + 80), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 44, 30 + w, 44 + h], radius=36, fill=(27, 38, 59, 60))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([30, 30, 30 + w, 30 + h], radius=36, fill=WHITE)
    ic = IC_OK if kind == "ok" else IC_NO
    img.alpha_composite(ic.resize((96, 96), Image.LANCZOS), (30 + 34, 30 + 27))
    size = 50
    while font(size, "ExtraBold").getlength(text) > w - 190 and size > 30:
        size -= 2
    d.text((30 + 160, 30 + h / 2), text, font=font(size, "ExtraBold"), fill=DARK, anchor="lm")
    return img

# ---------- render pomocníci ----------
def frames_of(scenes):
    TR = 8
    for i, sc in enumerate(scenes):
        prev_last = scenes[i - 1].render(scenes[i - 1].n - 1) if i else None
        for f in range(sc.n):
            cur = sc.render(f)
            if prev_last is not None and f < TR:
                e = ease_in_out((f + 1) / (TR + 1))
                cc = Image.new("RGBA", (W, H))
                cc.paste(prev_last, (0, int(-e * H * 0.35)))
                cc.paste(cur, (0, int((1 - e) * H)))
                cur = cc
            yield cur.convert("RGB")

def make_audio(scenes, events, path):
    SR = A.SR
    st, t = [], 0
    for sc in scenes:
        st.append(t / FPS); t += sc.n
    total = t / FPS
    out = A.Track(total)
    out.add(0, A.seg_pop(total + .2, 0.55)[: int(total * SR)])
    for (si, kind, fr) in events:
        at = st[si] + fr / FPS
        if kind == 'pop':
            out.add(at, K1.fx_pop(), 0.45)
        elif kind == 'tick':
            out.add(at, K1.fx_pop(), 0.12)
        elif kind == 'ding':
            out.add(at, A.fx_ding(), 0.55)
        elif kind == 'kick':
            out.add(at, A.kick(0.45), 0.35)
        elif kind == 'impact':
            out.add(at, A.fx_impact(), 0.7)
        elif kind == 'whoosh':
            out.add(at, A.fx_whoosh(0.35), 0.4)
    y = out.b[: int(total * SR)]
    y = A.hp(y, 30)
    fo = int(1.0 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

def render_video(name, scenes, events):
    out = os.path.join(OUTDIR, name)
    aud = os.path.join(HERE, "tiktok_" + name.replace(".mp4", ".wav"))
    make_audio(scenes, events, aud)
    cmd = [R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", aud, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    for fr in frames_of(scenes):
        p.stdin.write(fr.tobytes()); n += 1
    p.stdin.close(); p.wait()
    print("hotovo", name, round(n / FPS, 1), "s")
    return out

def offset_events(scenes, base_idx, evs):
    return [(base_idx + si, k, f) for (si, k, f) in evs]

VIDEOS = {}
chip = J.chip

# ===== 1) Co jsou komunální volby? =====
v1a = S(135, [Words("Kdo rozhoduje,", 300, 3, 108), Words("co se ve městě *staví?*", 430, 12, 82),
              El(sub_t("A kam jdou peníze města?", 50), W // 2, 540, 26, "rise"),
              Pop(chip("opravy a stavby"), 300, 700, 40, -3), Pop(chip("rozpočet"), 770, 790, 48, 3),
              Pop(chip("školy"), 290, 890, 56, -2), Pop(chip("kultura a akce"), 760, 985, 64, 2)]
          + rx("swag", 76, "Spoiler: vy.", by=1205))
v1b = S(150, [Words("Rozhoduje", 300, 3, 112), Words("*zastupitelstvo.*", 430, 10, 112),
              PeopleT(600, 22), El(sub_t("Ve Starém Plzenci jich je 17. Na 4 roky.", 46), W // 2, 1110, 76, "rise"),
              El(sub_t("V každé obci je počet jiný.", 40), W // 2, 1175, 92, "rise")]
          + rx("hat", 84, "Tohle je ta parta.", by=1205, bx=690))
v1c = S(170, [Words("Co zastupitelé", 300, 3, 96), Words("*dělají?*", 430, 10, 120),
              SlideIn(fact_card("Schvalují rozpočet města"), W // 2, 650, 30),
              SlideIn(fact_card("Rozhodují o stavbách a opravách"), W // 2, 830, 56),
              SlideIn(fact_card("Volí starostu a radu"), W // 2, 1010, 82)]
          + rx("head", 100, "A hlídají kasu.", by=1205))
v1d = S(130, [Words("Vy rozhodnete,", 330, 3, 108), Words("kdo tam *bude.*", 460, 12, 116),
              El(text_img("9.–10. října", 100, WHITE, w="ExtraBold", pill=G, pad=(50, 20)), W // 2, 650, 40, dur=11),
              El(sub_t("Komunální volby jsou jednou za 4 roky.", 44), W // 2, 790, 60, "rise")]
          + rx("point", 60, "Jo, myslím tebe.", by=1190, bx=640))
s1 = [v1a, v1b, v1c, v1d, end_card()]
e1 = [(0, 'pop', 3), (0, 'pop', 12), (0, 'pop', 26), (0, 'pop', 40), (0, 'pop', 48), (0, 'pop', 56), (0, 'pop', 64),
      (1, 'pop', 3), (1, 'pop', 10)] + [(1, 'tick', 22 + 2 * i) for i in range(17)] + [(1, 'pop', 76), (1, 'ding', 76),
      (2, 'pop', 3), (2, 'pop', 10), (2, 'pop', 30), (2, 'pop', 56), (2, 'pop', 82),
      (3, 'pop', 3), (3, 'pop', 12), (3, 'pop', 40), (3, 'pop', 60)] + offset_events(None, 4, END_EV)
VIDEOS["01_co_jsou_komunalni_volby.mp4"] = (s1, e1)

# ===== 2) Kdy, kam a co s sebou =====
v2a = S(170, [Words("Kdy se volí?", 300, 3, 122),
              Pop(J.day_card("Pátek", "9. října", "14–22 h"), W // 2, 520, 16, -1.5),
              Pop(J.day_card("Sobota", "10. října", "8–14 h"), W // 2, 790, 34, 1.5),
              Words("Ve své volební místnosti", 1010, 70, 54),
              Words("podle *trvalého_bydliště.*", 1080, 80, 54)]
          + rx("swag", 96, "Zapiš si to.", by=1205, bx=690))
v2b = TextScene(175, GL, [Words("Co s sebou?", 280, 3, 120), Words("Stačí *jedno* z toho:", 390, 12, 68),
                          Pop(J.id_card(), 290, 640, 28, -6), Pop(J.passport(), 770, 665, 36, 5),
                          Pop(J.phone_edoklady(), W // 2, 900, 44, -3),
                          Words("Občanka · pas · eDoklady", 1120, 62, 56)] + rx("hat", 84, "Bez občanky ani ránu.", by=1215, bx=650, size=44), extra=bg_fx)
s2 = [v2a, v2b, end_card()]
e2 = [(0, 'pop', 3), (0, 'pop', 16), (0, 'pop', 34), (0, 'pop', 70), (0, 'pop', 80),
      (1, 'pop', 3), (1, 'pop', 12), (1, 'pop', 28), (1, 'pop', 36), (1, 'pop', 44), (1, 'pop', 62), (1, 'ding', 62)] + offset_events(None, 2, END_EV)
VIDEOS["02_kdy_kam_a_co_s_sebou.mp4"] = (s2, e2)

# ===== 3) 17 hlasů a tři možnosti =====
v3a = S(190, [Words("Víte, kolik", 290, 3, 104), Words("máte *hlasů?*", 440, 10, 124),
              El(sub_t("Tolik, kolik je zastupitelů v obci.", 46), W // 2, 570, 24, "rise"),
              Pop(text_img("Ve Starém Plzenci: 17", 66, WHITE, w="ExtraBold", pill=G, pad=(46, 16), radius=36), W // 2, 690, 40, -2),
              El(sub_t("A tři možnosti, jak je použít.", 46), W // 2, 810, 60, "rise"),
              SlideIn(option_card(1, "Celá kandidátka", "Jeden křížek u názvu."), W // 2, 980, 76),
              SlideIn(option_card(2, "Jednotliví kandidáti", "Křížky u jmen."), W // 2, 1180, 100),
              SlideIn(option_card(3, "Obojí dohromady", "Kandidátka a navíc jména."), W // 2, 1380, 124)])
s3 = [v3a, end_card()]
e3 = [(0, 'pop', 3), (0, 'pop', 10), (0, 'pop', 24), (0, 'pop', 40), (0, 'ding', 44), (0, 'pop', 60), (0, 'whoosh', 76), (0, 'pop', 80), (0, 'whoosh', 100), (0, 'pop', 104),
      (0, 'whoosh', 124), (0, 'pop', 128)] + offset_events(None, 1, END_EV)
VIDEOS["03_mate_17_hlasu.mp4"] = (s3, e3)

# ===== 4–6) tři způsoby označení =====
def demo_scene(i, title_words, sub_text, cfg, mode, n, captions, reaction):
    els = [El(step_pill(i), W // 2, 150, 0, "rise", dur=8), title_words,
           El(sub_t(sub_text, 42), W // 2, 365, 18, "rise"),
           El(text_img("Příklad: Starý Plzenec, 17 zastupitelů", 34, GD, w="ExtraBold", pill=(226, 240, 222), pad=(26, 10), radius=22), W // 2, 450, 22, "rise"),
           BallotDemoT(cfg, 10, cy=900, sc=0.78), CounterT(cfg, {1: 64, 2: 60, 3: 54}[i], mode, 10, cy=1330, cx=540)]
    for text, y, at in captions:
        els.append(El(text_img(text, 40, GREY, w="SemiBold"), W // 2, y, at, "rise"))
    return S(n, els + reaction)

d1 = demo_scene(1, Words("Celá *kandidátka*", 270, 3, 100), "Jeden křížek u názvu kandidátky.", CFG1, "party", 205,
                [("Hlas dostanou všichni její kandidáti.", 1420, 124)], [])
d2 = demo_scene(2, Words("Jednotliví *kandidáti*", 270, 3, 96), "Křížky u jmen, klidně z různých kandidátek.", CFG2, "indiv", 250,
                [("Označit můžete nejvýše tolik kandidátů,", 1420, 176), ("kolik je zastupitelů (u nás 17).", 1475, 186)], [])
d3 = demo_scene(3, Words("Obojí *dohromady*", 270, 3, 104), "Kandidátka a navíc jména z jiných.", CFG3, "mix", 305,
                [("Kandidátce se ubere tolik hlasů,", 1420, 206), ("kolik jste dali jiným kandidátům.", 1475, 220)], [])
ev_pop = [(0, 'pop', 3), (0, 'pop', 8), (0, 'pop', 18)]
VIDEOS["04_cela_kandidatka.mp4"] = ([d1, end_card()], ev_pop + [(0, 'kick', 44)] + [(0, 'tick', 60 + 3 * r) for r in range(17)]
                                    + [(0, 'ding', 112), (0, 'pop', 124)] + offset_events(None, 1, END_EV))
VIDEOS["05_jednotlivi_kandidati.mp4"] = ([d2, end_card()], ev_pop + [(0, 'kick', a) for a in (50, 76, 102, 128, 154)]
                                         + [(0, 'ding', 60), (0, 'pop', 176)] + offset_events(None, 1, END_EV))
VIDEOS["06_oboji_dohromady.mp4"] = ([d3, end_card()], ev_pop + [(0, 'kick', a) for a in (46, 72, 98, 130)]
                                    + [(0, 'tick', 142 + 3 * r) for r in range(14)] + [(0, 'impact', 190), (0, 'pop', 206), (0, 'pop', 220)]
                                    + offset_events(None, 1, END_EV))

# ===== 7) Nemůžete přijít? =====
v7 = S(195, [Words("Nemůžete přijít?", 290, 3, 112)]
       + card_row("Voličský průkaz?", "U komunálních voleb nejde.", "no", 520, 18)
       + card_row("Ze zahraničí?", "Komunální volby to neumožňují.", "no", 740, 38)
       + card_row("Nemoc?", "Požádejte úřad o přenosnou urnu.", "ok", 960, 58)
       + [Words("Volí se *osobně.*", 1125, 84, 80)] + rx("swag", 110, "Sorry, jede se osobně.", by=1235, bx=620, size=42))
e7 = [(0, 'pop', 3), (0, 'pop', 18), (0, 'impact', 26), (0, 'kick', 26), (0, 'pop', 38), (0, 'impact', 46), (0, 'kick', 46),
      (0, 'pop', 58), (0, 'ding', 66), (0, 'pop', 84)] + offset_events(None, 1, END_EV)
VIDEOS["07_nemuzete_prijit.mp4"] = ([v7, end_card()], e7)

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "prev":
        key = sys.argv[2]
        scenes = VIDEOS[key][0]
        for a in sys.argv[3:]:
            si, fr = [int(x) for x in a.split(":")]
            scenes[si].render(fr).convert("RGB").save(os.path.join(HERE, "hlas", f"tt_{key[:2]}_{si}_{fr}.jpg"))
        sys.exit()
    only = sys.argv[1:] 
    for name, (scenes, ev) in VIDEOS.items():
        if only and not any(name.startswith(o) for o in only):
            continue
        render_video(name, scenes, ev)
