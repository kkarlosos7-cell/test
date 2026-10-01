"""Otevřená radnice: do hotového reelu přidá nenápadné poznámky, že jde o návrh / ukázku."""
import subprocess
from PIL import Image
import render as R
from render import W, H, FPS, text_img, clamp

SRC = "/home/user/sedleckekviti-26a9e98a/reels/otevrena-radnice/otevrena-radnice-reel.mp4"
OUT = R.HERE + "/otevrena-radnice-navrh.mp4"
GREY = (110, 122, 140)
N1 = text_img("Takhle chceme, aby to fungovalo", 32, GREY, w="SemiBold",
              pill=(255, 255, 255), pad=(22, 10), radius=20)
N2 = text_img("Tohle chceme na radnici prosadit.", 36, GREY, w="SemiBold")
# (obrázek, levý okraj x, střed y, od, do) – časy v sekundách
NOTES = [(N1, 540 - N1.width // 2, 515, 14.4, 25.0),   # nad telefonem během ukázky aplikace
         (N2, 90, 695, 25.8, 99)]                       # pod „Schůzku si sjednáte jednoduše online.“

def alpha(t, t0, t1):
    return clamp((t - t0) / .4) * clamp((t1 - t) / .3)

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
    im = Image.frombuffer("RGB", (W, H), b).convert("RGBA")
    t = n / FPS
    for img, x, cy, t0, t1 in NOTES:
        a = alpha(t, t0, t1)
        if a <= 0:
            continue
        img2 = img.copy()
        if a < 1:
            img2.putalpha(img2.getchannel("A").point(lambda v: int(v * a)))
        im.alpha_composite(img2, (x, int(cy - img.height / 2)))
    wr.stdin.write(im.convert("RGB").tobytes())
    n += 1
wr.stdin.close(); wr.wait(); rd.wait()
print("hotovo", OUT, n)
