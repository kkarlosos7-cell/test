"""Městský Facebook + kladívka: původní reel doplněný o údery kladívek a bubliny s informacemi."""
import os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kladivka as K
import audio as A
from render import W, H, FPS, DARK, G, GD, GL, WHITE, font, clamp, ease_out, text_img

HERE = K.HERE
SRC = "/home/user/sedleckekviti-26a9e98a/reels/mestsky-facebook/mestsky-facebook-reel.mp4"
OUT = os.path.join(HERE, "mestsky-facebook-kladivka.mp4")
FF = K.R.FFMPEG

CUT = 510          # vložení po snímku 17,0 s
INS = 190          # délka vložené části (6,3 s)
RESUME = 516       # původní video pokračuje od 17,2 s
XF = 8             # prolínání zpět do originálu
SRC_N = 600
TOTAL = CUT + INS + (SRC_N - RESUME - XF)

# údery do telefonu u „Plakát. Plakát. Plakát.“ (flash v originále na 3,0/3,4/3,8 s)
HITS_A = [((395, 700), 90, 1), ((690, 800), 102, -1), ((420, 930), 114, 1)]
# údery ve vložené části (telefon je posunutý dolů a zmenšený)
HITS_B = [((430, 980), CUT + 12, 1), ((650, 1200), CUT + 26, -1)]
HAM = K.hammer_img(300)

def back(p):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
def eo(p): return 1 - (1 - p) ** 3

# ---------- slova ve stylu původního reelu ----------
CAP = 84
def word_img(w, hl):
    f = font(CAP, "ExtraBold")
    tw = f.getlength(w); asc, desc = f.getmetrics()
    px, pt, pb = int(.26 * CAP), int(.08 * CAP), int(.12 * CAP)
    wi, hi = int(tw + 2 * px), int(asc + desc * 0.4 + pt + pb)
    img = Image.new("RGBA", (wi + 60, hi + 70), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 42, 30 + wi, 42 + hi], radius=int(.2 * CAP), fill=(27, 38, 59, 46))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([30, 30, 30 + wi, 30 + hi], radius=int(.2 * CAP), fill=G if hl else WHITE)
    d.text((30 + px, 30 + pt - 2), w, font=f, fill=WHITE if hl else DARK)
    return img

class Words:
    def __init__(self, line, y, t0, gap=4):
        self.ws = [(word_img(w.lstrip("*"), w.startswith("*")), w.startswith("*")) for w in line.split(" ")]
        self.y, self.t0, self.gap = y, t0, gap
        total = sum(im.width - 60 for im, _ in self.ws) + 17 * (len(self.ws) - 1)
        x = W / 2 - total / 2
        self.xs = []
        for im, _ in self.ws:
            self.xs.append(x + (im.width - 60) / 2); x += im.width - 60 + 17
    def draw(self, c, f, out=0.0):
        for i, ((im, hl), cx) in enumerate(zip(self.ws, self.xs)):
            p = clamp((f - self.t0 - i * self.gap) / 9)
            if p <= 0:
                continue
            s = (0.35 + 0.65 * back(p)) * (1 - out * 0.15)
            img = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
            if hl:
                img = img.rotate(-2.5 * eo(p), expand=True, resample=Image.BICUBIC)
            a = min(clamp(p * 3), 1 - out)
            if a < 1:
                img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
            c.alpha_composite(img, (int(cx - img.width / 2), int(self.y + (1 - eo(p)) * 60 - out * 70 - img.height / 2)))

# ---------- vložená část ----------
L0 = 30  # začátek bublin (snímek vložené části)
words = [Words("Z posledního", 250, L0), Words("*zastupitelstva:", 360, L0 + 8)]
CX = 70
from render import El
els = []
els.append(El(K.white_card(940, 300), W // 2, 470 + 150, L0 + 20, dur=10))
t1 = text_img("Bylo odhlasováno…", 72, DARK, w="ExtraBold")
els.append(El(t1, CX + 40 + t1.width // 2, 470 + 75, L0 + 24, "rise"))
for i, (wd, at) in enumerate(((820, 30), (760, 34), (520, 38))):
    els.append(K.Shimmer(CX + 50, 470 + 150 + i * 50, wd, 28, L0 + at))
els.append(El(K.white_card(940, 190), W // 2, 810 + 95, L0 + 50, dur=10))
els.append(El(K.icon("pin"), CX + 90, 810 + 95, L0 + 53))
p1 = text_img("Dostavba centra", 58, DARK, w="ExtraBold")
p2 = text_img("Starý Plzenec – park", 58, GD, w="ExtraBold")
els.append(El(p1, CX + 170 + p1.width // 2, 810 + 62, L0 + 55, "rise"))
els.append(El(p2, CX + 170 + p2.width // 2, 810 + 130, L0 + 58, "rise"))
BUB = [("start", "Začátek stavby", "říjen 2026", L0 + 72), ("end", "Konec stavby", "srpen 2027", L0 + 88),
       ("cone", "Omezení provozu", None, L0 + 104)]
DINGS = [L0 + 20, L0 + 50] + [b[3] for b in BUB]
for i, (ic, lab, val, at) in enumerate(BUB):
    y = 1040 + i * 165
    els.append(El(K.white_card(940, 140), W // 2, y + 70, at, dur=10))
    els.append(El(K.icon(ic), CX + 90, y + 70, at + 3))
    l = text_img(lab, 40, (96, 108, 128), w="SemiBold")
    els.append(El(l, CX + 170 + l.width // 2, y + 42, at + 4, "rise"))
    if val:
        v = text_img(val, 60, DARK, w="ExtraBold")
        els.append(El(v, CX + 170 + v.width // 2, y + 98, at + 7, "rise"))
    else:
        els.append(K.Shimmer(CX + 172, y + 80, 420, 36, at + 7))
OUT_AT = INS - 22  # bubliny odjíždějí

def draw_hammers(c, g, hits):
    for tg, t, side in hits:
        pose = K.hammer_pose(g, t, side, tg)
        if pose:
            (px, py), a = pose
            img = HAM.rotate(a, resample=Image.BICUBIC)
            c.alpha_composite(img, (int(px - img.width / 2), int(py - img.height / 2)))

def shake(c, g, hits, amp=12):
    for _, t, _ in hits:
        k = g - t
        if 0 <= k <= 9:
            dd = math.exp(-k / 3)
            out = Image.new("RGBA", (W, H), (243, 247, 241, 255))
            out.paste(c, (int(amp * math.sin(k * 2.8) * dd), int(amp * 0.7 * math.cos(k * 3.3) * dd)))
            return out
    return c

def flash(c, g, times):
    for t in times:
        k = g - t
        if 0 <= k < 4:
            c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(150 * (1 - k / 4)))))
    return c

_blur_cache = {}
def insert_frame(freeze, k):
    g = CUT + k
    bl = eo(clamp((k - 24) / 12))
    if bl <= 0:
        c = freeze.copy()
    else:
        key = round(bl, 2)
        if key not in _blur_cache:
            b = freeze.filter(ImageFilter.GaussianBlur(26 * bl))
            b.alpha_composite(Image.new("RGBA", (W, H), (243, 247, 241, int(175 * bl))))
            _blur_cache[key] = b
        c = _blur_cache[key].copy()
    out = eo(clamp((k - OUT_AT) / 12))
    if out < 1:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for w in words:
            w.draw(layer, k, out)
        for e in els:
            e.draw(layer, k)
        if out > 0:
            s = 1 - 0.12 * out
            layer = layer.resize((int(W * s), int(H * s)), Image.BILINEAR)
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * (1 - out))))
            c.alpha_composite(layer, (int((W - layer.width) / 2), int((H - layer.height) / 2)))
        else:
            c.alpha_composite(layer)
    draw_hammers(c, g, HITS_B)
    c = flash(c, g, [t for _, t, _ in HITS_B])
    return shake(c, g, HITS_B)

def fix_bar(arr, n):
    """Horní ukazatel průběhu přepočítaný na novou délku."""
    arr[0:10, :, :] = arr[12:13, :, :]
    w = int(n / TOTAL * W)
    arr[0:10, :w, :] = (78, 159, 61)
    return arr

# ---------- zvuk ----------
def build_audio(path):
    dur = TOTAL / FPS
    out = A.Track(dur)
    SR = A.SR
    mus = A.seg_pop(dur + 0.2, 0.55)[: int(dur * SR)]
    out.add(0, mus)
    for tg, fr, side in HITS_A + HITS_B:
        out.add(fr / FPS - 0.25, A.fx_whoosh(0.3), 0.7)
        out.add(fr / FPS, K.fx_clink(), 1.1)
    for d in DINGS:
        out.add((CUT + d) / FPS, A.fx_ding(), 0.8)
    for tk in (L0 + 30, L0 + 34, L0 + 38, BUB[2][3] + 7):
        for j in range(4):
            out.add((CUT + tk) / FPS + j * 0.05, A.hat(), 0.45)
    out.add((CUT + OUT_AT) / FPS, A.fx_whoosh(0.4), 0.6)
    # závěr originálu: zelená vlna 17,3 s, samolepka dopadá ~18,6 s (posunuto o vloženou část)
    shift = (CUT + INS - RESUME - XF + XF) / FPS - (RESUME) / FPS + RESUME / FPS
    off = (CUT + INS) / FPS - RESUME / FPS
    out.add(17.3 + off, A.fx_whoosh(0.5), 0.8)
    out.add(18.55 + off, A.fx_impact(), 1.0)
    y = out.b[: int(dur * SR)]
    y = A.hp(y, 30)
    fo = int(1.0 * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    y = y / np.max(np.abs(y)) * 0.89
    A.wavfile.write(path, SR, (np.stack([y, y], 1) * 32767).astype(np.int16))

if __name__ == "__main__":
    print("snímků:", TOTAL, "délka:", round(TOTAL / FPS, 2), "s")
    AUD = os.path.join(HERE, "fb_kladivka_audio.wav")
    build_audio(AUD)
    rd = subprocess.Popen([FF, "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    FS = W * H * 3
    def read():
        b = rd.stdout.read(FS)
        return np.frombuffer(b, np.uint8).reshape(H, W, 3).copy() if len(b) == FS else None
    wr = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", AUD, "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    prev = os.path.join(HERE, "prev4"); os.makedirs(prev, exist_ok=True)
    n = 0
    def emit(img):
        global n
        arr = np.asarray(img.convert("RGB")).copy()
        arr = fix_bar(arr, n)
        wr.stdin.write(arr.tobytes())
        if n % 10 == 0:
            Image.fromarray(arr).resize((270, 480)).save(os.path.join(prev, f"{n:04d}.png"))
        n += 1
    freeze = None
    for i in range(CUT):
        fr = Image.fromarray(read()).convert("RGBA")
        if i == CUT - 2:
            freeze = fr.copy()
        if 70 <= i <= 135:
            draw_hammers(fr, i, HITS_A)
            fr = shake(fr, i, HITS_A, 10)
        emit(fr)
    buf = []
    for i in range(CUT, RESUME + XF):
        buf.append(read())
    ahead = buf[RESUME - CUT:]
    for k in range(INS):
        c = insert_frame(freeze, k)
        if k >= INS - XF:
            a = (k - (INS - XF) + 1) / (XF + 1)
            o = Image.fromarray(ahead[k - (INS - XF)]).convert("RGBA")
            c = Image.blend(c, o, a)
        emit(c)
    while True:
        a = read()
        if a is None:
            break
        emit(Image.fromarray(a))
    wr.stdin.close(); wr.wait(); rd.wait()
    print("hotovo:", OUT, n)
