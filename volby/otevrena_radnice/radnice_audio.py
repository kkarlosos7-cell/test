"""Zvuk pro Otevřenou radnici: podkres + efekty na místech, kde se v obraze něco objeví (podle změn mezi snímky)."""
import subprocess, numpy as np
import render as R
import audio as A
import kino as K1

VID = R.HERE + "/otevrena-radnice-navrh.mp4"
OUT = R.HERE + "/otevrena-radnice-navrh-zvuk.mp4"
WAV = R.HERE + "/radnice_audio.wav"
w, h = 135, 240
p = subprocess.run([R.FFMPEG, "-v", "error", "-i", VID, "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                   capture_output=True)
fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w).astype(np.float32)
n = len(fr); fps = 30
diff = np.r_[0, np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))]
# nástupy pohybu: hodnota výrazně nad klouzavým minimem
base = np.array([diff[max(0, i - 15):i + 1].min() for i in range(n)])
on = diff - base
events, last = [], -99
for i in range(1, n - 1):
    if on[i] > 1.2 and on[i] >= on[i - 1] and on[i] >= on[i + 1] and i - last > 10:
        events.append(i); last = i
print("událostí:", len(events), [round(e / fps, 2) for e in events])
total = n / fps
out = A.Track(total)
out.add(0, A.seg_pop(total + .2, 0.5)[: int(total * A.SR)])
for e in events:
    t = e / fps
    if 25.2 < t < 25.9:
        out.add(t, A.fx_whoosh(0.5), 0.7)
    else:
        out.add(t, K1.fx_pop(), 0.45)
y = out.b[: int(total * A.SR)]
y = A.hp(y, 30)
fo = int(1.2 * A.SR); y[-fo:] *= np.linspace(1, 0, fo) ** 1.5
y = y / (np.percentile(np.abs(y), 99.7) + 1e-9) * 0.7
y = np.tanh(y * 1.2) / np.tanh(1.2)
y = y / np.max(np.abs(y)) * 0.89
A.wavfile.write(WAV, A.SR, (np.stack([y, y], 1) * 32767).astype(np.int16))
subprocess.run([R.FFMPEG, "-y", "-v", "error", "-i", VID, "-i", WAV, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                "-shortest", "-movflags", "+faststart", OUT], check=True)
print("hotovo", OUT)
