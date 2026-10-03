"""Plán investic: do hotového reelu (v2) vloží jeden krátký ilustrační záběr s mapou investic v telefonu (bez popisku)."""
import os, subprocess, math, sys
from PIL import Image, ImageDraw, ImageFilter
import render as R
from render import W, H, FPS, font, clamp, ease_out, ease_out_back, ease_in_out

HERE = R.HERE
SRC = "/home/user/sedleckekviti-26a9e98a/reels/plan-investic/plan-investic-reel-v2.mp4"
OUT = os.path.join(HERE, "plan-investic-reel-v3.mp4")
MAP = Image.open(os.path.join(HERE, "inv", "map.png")).convert("RGB")
HDR_FRAME = Image.open(os.path.join(HERE, "inv", "t6.0.png")).convert("RGB")

# displej telefonu v reelu (změřeno ve snímku)
SX0, SY0, SX1, SY1 = 248, 583, 833, 1850
SW, SH = SX1 - SX0, SY1 - SY0
T_INS = 480          # snímek (16,0 s), za který se záběr vkládá
N_INS = 46           # délka vloženého záběru (snímky)

DARK = (27, 38, 59)
COL = {"hotovo": (78, 159, 61), "stavi": (38, 55, 84), "chysta": (136, 146, 160), "zpozdeni": (217, 119, 34)}
HDR_H, LEG_H = 94, 150
MAP_H = SH - HDR_H - LEG_H

# výřez mapy: bez „Domov“, bez posledně zobrazeného místa a bez Google prvků
S = MAP.width / 924
CROP = tuple(int(v * S) for v in (0, 630, 520, 1539))
mp = MAP.crop(CROP)
MAP_IMG = mp.resize((SW, int(SW * mp.height / mp.width)), Image.LANCZOS)
MAP_IMG = MAP_IMG.crop((0, 0, SW, MAP_H)) if MAP_IMG.height >= MAP_H else MAP_IMG.resize((SW, MAP_H), Image.LANCZOS)
KX, KY = SW / (CROP[2] - CROP[0]), MAP_IMG.height / (CROP[3] - CROP[1])

# (x, y v souřadnicích snímku mapy, stav)
PINS = [(130, 960, "hotovo"), (360, 960, "stavi"), (440, 1030, "hotovo"), (210, 1085, "zpozdeni"),
        (340, 1150, "stavi"), (95, 1205, "stavi"), (472, 1190, "hotovo"), (250, 1290, "stavi"),
        (330, 1375, "hotovo"), (140, 1405, "stavi"), (430, 1440, "stavi"), (60, 1010, "hotovo")]

def pin_img(col, sc=1.0):
    r = int(21 * sc)
    w, h = r * 2 + 24, int(r * 3.2) + 24
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, top = w / 2, 12
    def shape(dr, pad, fill):
        dr.polygon([(cx - r * .82 - pad, top + r * 1.35), (cx + r * .82 + pad, top + r * 1.35), (cx, top + r * 3.1 + pad)], fill=fill)
        dr.ellipse([cx - r - pad, top - pad, cx + r + pad, top + r * 2 + pad], fill=fill)
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shape(ImageDraw.Draw(sh), 3, (0, 0, 0, 90))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)), (3, 6))
    shape(d, 4, (255, 255, 255, 255))
    shape(d, 0, col + (255,))
    d.ellipse([cx - r * .38, top + r * .62, cx + r * .38, top + r * 1.38], fill=(255, 255, 255, 255))
    return img, (w / 2, top + r * 3.1 + 4)      # špička špendlíku
PIN = {k: pin_img(c) for k, c in COL.items()}

def header():
    return HDR_FRAME.crop((SX0, SY0, SX1, SY0 + HDR_H))

def legend():
    img = Image.new("RGB", (SW, LEG_H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.line([(0, 0), (SW, 0)], fill=(226, 230, 234), width=2)
    items = [("Hotovo", "hotovo"), ("Staví se", "stavi"), ("Zpoždění", "zpozdeni")]
    f = font(27, "SemiBold")
    tot = sum(f.getlength(t) + 28 + 40 for t, _ in items) - 40
    x = (SW - tot) / 2
    for t, k in items:
        d.ellipse([x, LEG_H / 2 - 9, x + 18, LEG_H / 2 + 9], fill=COL[k])
        d.text((x + 28, LEG_H / 2), t, font=f, fill=(60, 72, 92), anchor="lm")
        x += f.getlength(t) + 28 + 40
    return img
HDR, LEG = header(), legend()

def map_screen(i):
    """Obrazovka s mapou v čase i (0..N_INS-1)."""
    z = 1.0 + 0.06 * i / (N_INS - 1)
    base = MAP_IMG
    zw, zh = int(base.width * z), int(base.height * z)
    zoomed = base.resize((zw, zh), Image.BICUBIC)
    ox, oy = (zw - SW) // 2, (zh - MAP_H) // 2
    view = zoomed.crop((ox, oy, ox + SW, oy + MAP_H)).convert("RGBA")
    for n, (px, py, k) in enumerate(PINS):
        t0 = 9 + n * 2
        if i < t0:
            continue
        p = ease_out_back(clamp((i - t0) / 9), 1.7)
        img, tip = PIN[k]
        sx = (px * S - CROP[0]) * KX * z - ox
        sy = (py * S - CROP[1]) * KY * z - oy
        s = max(.05, p)
        im2 = img.resize((max(2, int(img.width * s)), max(2, int(img.height * s))), Image.BILINEAR)
        view.alpha_composite(im2, (int(sx - tip[0] * s), int(sy - tip[1] * s - (1 - clamp((i - t0) / 9)) * 40)))
    scr = Image.new("RGB", (SW, SH), (255, 255, 255))
    scr.paste(HDR, (0, 0))
    scr.paste(view.convert("RGB"), (0, HDR_H))
    scr.paste(LEG, (0, HDR_H + MAP_H))
    return scr

MASK = Image.new("L", (SW, SH), 0)
ImageDraw.Draw(MASK).rounded_rectangle([0, 0, SW - 1, SH - 1], radius=54, fill=255)

def insert_frame(base, i):
    a = ease_in_out(clamp(i / 8)) * ease_in_out(clamp((N_INS - 1 - i) / 8))
    orig = base.crop((SX0, SY0, SX1, SY1))
    scr = Image.blend(orig, map_screen(i), a)
    out = base.copy()
    out.paste(scr, (SX0, SY0), MASK)
    return out

if __name__ == "__main__":
    if len(sys.argv) > 1:       # náhled: python plan_map.py 0 12 24 40
        base = Image.open(os.path.join(HERE, "inv", "t16.0.png")).convert("RGB")
        ims = [insert_frame(base, int(a)).resize((405, 720)) for a in sys.argv[1:]]
        sheet = Image.new("RGB", (405 * len(ims), 720), "white")
        for k, im in enumerate(ims):
            sheet.paste(im, (k * 405, 0))
        sheet.save(os.path.join(HERE, "inv", "map_sheet.jpg"))
        sys.exit()
    rd = subprocess.Popen([R.FFMPEG, "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen([R.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT],
                          stdin=subprocess.PIPE)
    FS = W * H * 3
    n = 0
    while True:
        b = rd.stdout.read(FS)
        if len(b) < FS:
            break
        wr.stdin.write(b)
        if n == T_INS:
            base = Image.frombuffer("RGB", (W, H), b)
            for i in range(N_INS):
                wr.stdin.write(insert_frame(base, i).tobytes())
        n += 1
    wr.stdin.close(); wr.wait(); rd.wait()
    print("hotovo", OUT, n, "+", N_INS)
