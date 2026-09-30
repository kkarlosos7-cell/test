"""Samolepka se zdviženou rukou a skleničkou sektu (sklenička v horní vrstvě), předloktí se hýbe v lokti."""
from PIL import Image, ImageDraw
SRC = Image.open(__file__.replace("toaststicker.py", "karel_toast.png")).convert("RGBA")
ELBOW = (180, 585)
PINCH = (138, 272)
POLY = [(0, 180), (200, 180), (225, 400), (262, 470), (262, 640), (80, 640), (0, 460)]
PAD = 260

class ToastSticker:
    def __init__(self, width, flute, gscale=1.0):
        m = Image.new("L", SRC.size, 0)
        ImageDraw.Draw(m).polygon(POLY, fill=255)
        arm = Image.new("RGBA", SRC.size, (0, 0, 0, 0)); arm.paste(SRC, (0, 0), m)
        base = SRC.copy()
        base.putalpha(Image.composite(SRC.getchannel("A"), Image.new("L", SRC.size, 0), Image.eval(m, lambda v: 255 - v)))
        W2, H2 = SRC.width, SRC.height + PAD
        b2 = Image.new("RGBA", (W2, H2), (0, 0, 0, 0)); b2.alpha_composite(base, (0, PAD))
        a2 = Image.new("RGBA", (W2, H2), (0, 0, 0, 0)); a2.alpha_composite(arm, (0, PAD))
        g = flute.resize((int(flute.width * gscale), int(flute.height * gscale)), Image.LANCZOS)
        # stopka mezi prsty: 70 % výšky obrázku skleničky = místo úchopu; sklenička nahoře (nad rukou)
        a2.alpha_composite(g, (int(PINCH[0] - g.width / 2 + 4), int(PINCH[1] + PAD - g.height * .70)))
        self.s = width / W2
        sz = (width, int(H2 * self.s))
        self.base = b2.resize(sz, Image.LANCZOS)
        self.arm = a2.resize(sz, Image.LANCZOS)
        self.pivot = (ELBOW[0] * self.s, (ELBOW[1] + PAD) * self.s)
        self.glass_top = (PINCH[0] * self.s, (PINCH[1] + PAD - g.height * .70) * self.s)
    def image(self, angle):
        out = Image.new("RGBA", self.base.size, (0, 0, 0, 0))
        out.alpha_composite(self.base)
        out.alpha_composite(self.arm.rotate(angle, center=self.pivot, resample=Image.BICUBIC))
        return out
