"""Ukazující samolepka s pohyblivým předloktím (volitelně se skleničkou sektu v ruce)."""
import math
from PIL import Image, ImageDraw
SRC = Image.open(__file__.replace("armsticker.py", "karel_ukazuje.png")).convert("RGBA")
ELBOW = (335, 650)
FIST = (185, 445)
POLY = [(0, 300), (300, 320), (395, 560), (360, 700), (230, 700), (0, 540)]

def _split(img):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).polygon(POLY, fill=255)
    arm = Image.new("RGBA", img.size, (0, 0, 0, 0)); arm.paste(img, (0, 0), m)
    base = img.copy()
    inv = Image.eval(m, lambda v: 255 - v)
    a = Image.composite(base.getchannel("A"), Image.new("L", img.size, 0), inv)
    base.putalpha(a)
    return base, arm

def with_glass(arm, flute):
    arm = arm.copy()
    g = flute.resize((int(flute.width * .78), int(flute.height * .78)), Image.LANCZOS)
    arm.alpha_composite(g, (int(FIST[0] - g.width / 2 + 5), int(FIST[1] - g.height * .9)))
    return arm

class ArmSticker:
    def __init__(self, width, flute=None, gscale=.78):
        self.s = width / SRC.width
        base, arm = _split(SRC)
        if flute is not None:
            pad = 300
            b2 = Image.new("RGBA", (SRC.width, SRC.height + pad), (0, 0, 0, 0)); b2.alpha_composite(base, (0, pad))
            a2 = Image.new("RGBA", b2.size, (0, 0, 0, 0)); a2.alpha_composite(arm, (0, pad))
            global_off = pad
            a2 = with_glass(a2, flute) if False else a2
            arm_g = Image.new("RGBA", b2.size, (0, 0, 0, 0)); arm_g.alpha_composite(arm, (0, pad))
            g = flute.resize((int(flute.width * gscale), int(flute.height * gscale)), Image.LANCZOS)
            arm_g.alpha_composite(g, (int(FIST[0] - g.width / 2 + 5), int(FIST[1] + pad - g.height * .92)))
            base, arm, self.off = b2, arm_g, pad
        else:
            self.off = 0
        sz = (int(base.width * self.s), int(base.height * self.s))
        self.base = base.resize(sz, Image.LANCZOS)
        self.arm = arm.resize(sz, Image.LANCZOS)
        self.pivot = (ELBOW[0] * self.s, (ELBOW[1] + self.off) * self.s)
    def image(self, angle):
        out = Image.new("RGBA", self.base.size, (0, 0, 0, 0))
        out.alpha_composite(self.arm.rotate(angle, center=self.pivot, resample=Image.BICUBIC))
        out.alpha_composite(self.base)
        return out
