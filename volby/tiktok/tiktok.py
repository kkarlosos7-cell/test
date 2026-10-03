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
OUTDIR = os.path.join(HERE, "tiktok"); os.makedirs(OUTDIR, exist_ok=True)
Pop = J.Pop
GREY = J.GREY

# ---------- společné prvky ----------
class BallotDemoT(BallotDemo):
    def __init__(self, cfg, at, cy=870, sc=0.9):
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
    def __init__(self, cfg, at, mode, bat=10, cy=1370):
        super().__init__(cfg, at, mode, bat); self.cy = cy

LOGO_E = LOGO.resize((760, int(LOGO.height * 760 / LOGO.width)), Image.LANCZOS)
def end_card():
    return TextScene(95, BG, [Words("Přijďte volit!", 380, 3, 112),
                              El(text_img("9.–10. října", 100, WHITE, w="ExtraBold", pill=G, pad=(50, 20)), W // 2, 530, 10, dur=11),
                              LogoSlam(LOGO_E, W // 2, 860, 18),
                              Pop(BADGE_L, W // 2, 1190, 40, 2)],
                     extra=bg_fx, post=shake_post([24], BG, amp=16))
END_EV = [(0, 'pop', 3), (0, 'pop', 10), (0, 'impact', 24), (0, 'ding', 25), (0, 'pop', 40), (0, 'ding', 44)]

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

# ===== 1) Co jsou komunální volby? =====
chip = J.chip
v1a = TextScene(130, BG, [Words("Kdo rozhoduje,", 330, 3, 108), Words("co se ve městě *staví?*", 460, 12, 82),
                          El(sub_t("A kam jdou peníze města?", 50), W // 2, 580, 26, "rise"),
                          Pop(chip("opravy a stavby"), 300, 790, 40, -3), Pop(chip("rozpočet"), 770, 880, 48, 3),
                          Pop(chip("školy"), 290, 990, 56, -2), Pop(chip("kultura a akce"), 760, 1090, 64, 2)])
v1b = TextScene(150, BG, [Words("Rozhoduje", 320, 3, 112), Words("*zastupitelstvo.*", 450, 10, 112),
                          J.People(None, 0, 0, 22),
                          Words("17 lidí na 4 roky.", 1380, 74, 84)])
v1c = TextScene(170, BG, [Words("Co zastupitelé", 310, 3, 96), Words("*dělají?*", 450, 10, 120),
                          SlideIn(fact_card("Schvalují rozpočet města"), W // 2, 740, 30),
                          SlideIn(fact_card("Rozhodují o stavbách a opravách"), W // 2, 940, 56),
                          SlideIn(fact_card("Volí starostu a radu"), W // 2, 1140, 82)])
v1d = TextScene(130, BG, [Words("Vy rozhodnete,", 380, 3, 108), Words("kdo tam *bude.*", 510, 12, 116),
                          El(text_img("9.–10. října", 100, WHITE, w="ExtraBold", pill=G, pad=(50, 20)), W // 2, 700, 40, dur=11),
                          El(sub_t("Komunální volby jsou jednou za 4 roky.", 44), W // 2, 840, 60, "rise")])
s1 = [v1a, v1b, v1c, v1d, end_card()]
e1 = [(0, 'pop', 3), (0, 'pop', 12), (0, 'pop', 26), (0, 'pop', 40), (0, 'pop', 48), (0, 'pop', 56), (0, 'pop', 64),
      (1, 'pop', 3), (1, 'pop', 10)] + [(1, 'tick', 22 + 2 * i) for i in range(17)] + [(1, 'ding', 74), (1, 'pop', 74),
      (2, 'pop', 3), (2, 'pop', 10), (2, 'pop', 30), (2, 'pop', 56), (2, 'pop', 82), (2, 'ding', 94),
      (3, 'pop', 3), (3, 'pop', 12), (3, 'pop', 40), (3, 'pop', 60)] + offset_events(None, 4, END_EV)
VIDEOS["01_co_jsou_komunalni_volby.mp4"] = (s1, e1)

# ===== 2) Kdy, kam a co s sebou =====
v2a = TextScene(165, BG, [Words("Kdy se volí?", 330, 3, 122),
                          Pop(J.day_card("Pátek", "9. října", "14–22 h"), W // 2, 700, 16, -1.5),
                          Pop(J.day_card("Sobota", "10. října", "8–14 h"), W // 2, 1010, 34, 1.5),
                          Words("Ve své volební místnosti", 1290, 70, 62),
                          Words("podle *trvalého_bydliště.*", 1380, 80, 62)])
v2b = TextScene(170, GL, [Words("Co s sebou?", 330, 3, 120), Words("Stačí *jedno* z toho:", 460, 12, 72),
                          Pop(J.id_card(), 300, 800, 28, -6), Pop(J.passport(), 780, 820, 36, 5),
                          Pop(J.phone_edoklady(), W // 2, 1170, 44, -3),
                          Words("Občanka · pas · eDoklady", 1420, 62, 64)])
s2 = [v2a, v2b, end_card()]
e2 = [(0, 'pop', 3), (0, 'pop', 16), (0, 'pop', 34), (0, 'pop', 70), (0, 'pop', 80),
      (1, 'pop', 3), (1, 'pop', 12), (1, 'pop', 28), (1, 'pop', 36), (1, 'pop', 44), (1, 'pop', 62), (1, 'ding', 62)] + offset_events(None, 2, END_EV)
VIDEOS["02_kdy_kam_a_co_s_sebou.mp4"] = (s2, e2)

# ===== 3) 17 hlasů a tři možnosti =====
v3a = TextScene(185, BG, [Words("Víte, že máte", 310, 3, 100), Words("*17_hlasů?*", 465, 10, 134),
                          El(sub_t("A tři možnosti, jak je použít.", 50), W // 2, 600, 24, "rise"),
                          SlideIn(option_card(1, "Celá kandidátka", "Jeden křížek u názvu."), W // 2, 830, 44),
                          SlideIn(option_card(2, "Jednotliví kandidáti", "Křížky u jmen."), W // 2, 1060, 72),
                          SlideIn(option_card(3, "Obojí dohromady", "Kandidátka a navíc jména."), W // 2, 1290, 100)])
s3 = [v3a, end_card()]
e3 = [(0, 'pop', 3), (0, 'pop', 10), (0, 'pop', 24), (0, 'whoosh', 44), (0, 'pop', 48), (0, 'whoosh', 72), (0, 'pop', 76), (0, 'whoosh', 100), (0, 'pop', 104),
      (0, 'ding', 130)] + offset_events(None, 1, END_EV)
VIDEOS["03_mate_17_hlasu.mp4"] = (s3, e3)

# ===== 4–6) tři způsoby označení =====
def demo_scene(i, title_words, sub_text, cfg, mode, n, captions):
    els = [El(step_pill(i), W // 2, 160, 0, "rise", dur=8), title_words,
           El(sub_t(sub_text), W // 2, 385, 18, "rise"),
           BallotDemoT(cfg, 10), CounterT(cfg, {1: 64, 2: 60, 3: 54}[i], mode, 10)]
    for text, y, at in captions:
        els.append(El(sub_t(text, 46), W // 2, y, at, "rise"))
    return TextScene(n, BG, els)

d1 = demo_scene(1, Words("Celá *kandidátka*", 280, 3, 104), "Jeden křížek u názvu kandidátky.", CFG1, "party", 205,
                [("Hlas dostane všech 17 kandidátů z ní.", 1465, 124)])
d2 = demo_scene(2, Words("Jednotliví *kandidáti*", 280, 3, 100), "Křížky u jmen, klidně z různých kandidátek.", CFG2, "indiv", 250,
                [("Označit můžete nejvýše 17 kandidátů.", 1465, 176)])
d3 = demo_scene(3, Words("Obojí *dohromady*", 280, 3, 108), "Kandidátka a navíc jména z jiných kandidátek.", CFG3, "mix", 305,
                [("Kandidátce se ubere tolik hlasů,", 1450, 206), ("kolik jste dali jiným kandidátům.", 1512, 220)])
ev_pop = [(0, 'pop', 3), (0, 'pop', 8), (0, 'pop', 18)]
VIDEOS["04_celá_kandidátka.mp4".replace("á", "a")] = ([d1, end_card()], ev_pop + [(0, 'kick', 44)] + [(0, 'tick', 60 + 3 * r) for r in range(17)]
                                                    + [(0, 'ding', 112), (0, 'pop', 124)] + offset_events(None, 1, END_EV))
VIDEOS["05_jednotlivi_kandidati.mp4"] = ([d2, end_card()], ev_pop + [(0, 'kick', a) for a in (50, 76, 102, 128, 154)]
                                         + [(0, 'ding', 60), (0, 'pop', 176)] + offset_events(None, 1, END_EV))
VIDEOS["06_obojí_dohromady.mp4".replace("í", "i")] = ([d3, end_card()], ev_pop + [(0, 'kick', a) for a in (46, 72, 98, 130)]
                                                    + [(0, 'tick', 142 + 3 * r) for r in range(14)] + [(0, 'impact', 190), (0, 'pop', 206), (0, 'pop', 220)]
                                                    + offset_events(None, 1, END_EV))

# ===== 7) Nemůžete přijít? =====
v7 = TextScene(190, BG, [Words("Nemůžete přijít?", 300, 3, 112)]
               + card_row("Voličský průkaz?", "U komunálních voleb nejde.", "no", 600, 18)
               + card_row("Ze zahraničí?", "Komunální volby to neumožňují.", "no", 860, 38)
               + card_row("Nemoc?", "Požádejte úřad o přenosnou urnu.", "ok", 1120, 58)
               + [Words("Volí se *osobně.*", 1380, 84, 92)])
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
