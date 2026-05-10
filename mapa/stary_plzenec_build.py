#!/usr/bin/env python3
"""
Starý Plzenec – SVG mapa pro laserování
Opravené souřadnice:
  - Sedlec je na VÝCHODĚ (13.490°E), ne na severu
  - Velký rybník u Úslavy je JV od Sedlce
  - Železniční trať prochází jižní částí města
  - Rotunda sv. Petra a Pavla je na SZ (kopec Hůrka)
"""

import math, os

# ── Bounding box ─────────────────────────────────────────────────────────────
# Pokrývá: Starý Plzenec, Sedlec (V), Radyně (JZ), rybník Úslava, Rotunda (SZ)
# Bbox ~6.2 × 6.2 km (čtverec v reálném měřítku)
S, W, N, E = 49.696, 13.430, 49.748, 13.517

SVG  = 920    # výstupní px
PAD  = 24     # okraj

# ── Projekce ─────────────────────────────────────────────────────────────────
draw_w = SVG - 2 * PAD
draw_h = SVG - 2 * PAD

# Oprava aspektu: mapu vykreslíme do skutečného poměru, zbytek je padding
cos_m  = math.cos(math.radians((S + N) / 2))
lat_km = (N - S) * 111.32
lon_km = (E - W) * cos_m * 111.32

if lat_km >= lon_km:
    map_h = draw_h
    map_w = int(draw_h * lon_km / lat_km)
else:
    map_w = draw_w
    map_h = int(draw_w * lat_km / lon_km)

ox = PAD + (draw_w - map_w) // 2   # x-offset pro centrování
oy = PAD + (draw_h - map_h) // 2   # y-offset

def px(lat, lon):
    x = ox + (lon - W) / (E - W) * map_w
    y = oy + (N - lat) / (N - S) * map_h
    return round(x, 2), round(y, 2)

def pts(*coords):
    return " ".join(f"{px(la,lo)[0]},{px(la,lo)[1]}" for la,lo in coords)

def polyline(coords, **kw):
    a = " ".join(f'{k.replace("_","-")}="{v}"' for k,v in kw.items())
    return f'<polyline points="{pts(*coords)}" {a}/>'

def polygon(coords, **kw):
    a = " ".join(f'{k.replace("_","-")}="{v}"' for k,v in kw.items())
    return f'<polygon points="{pts(*coords)}" {a}/>'

# ═══════════════════════════════════════════════════════════════════════════════
#  G E O D A T A   (WGS84 – opraveno podle screenshotu Google Maps)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Lesy ─────────────────────────────────────────────────────────────────────
FORESTS = [
    # Radyňský les – kopec s hradem (JZ)
    [(49.714, 13.432), (49.714, 13.452), (49.710, 13.462),
     (49.704, 13.464), (49.699, 13.461), (49.697, 13.452),
     (49.699, 13.440), (49.704, 13.433), (49.710, 13.430)],
    # Kopec Hůrka – u Rotundy (SZ od centra)
    [(49.735, 13.446), (49.738, 13.452), (49.740, 13.460),
     (49.737, 13.465), (49.733, 13.462), (49.731, 13.454),
     (49.732, 13.447)],
    # Les u Bezděkova (J)
    [(49.702, 13.468), (49.700, 13.478), (49.698, 13.490),
     (49.696, 13.495), (49.696, 13.505), (49.700, 13.510),
     (49.704, 13.508), (49.706, 13.498), (49.705, 13.480),
     (49.706, 13.470)],
    # Les na SV (za Sedlcem)
    [(49.738, 13.495), (49.742, 13.500), (49.748, 13.505),
     (49.748, 13.517), (49.740, 13.517), (49.736, 13.507),
     (49.734, 13.498)],
    # Menší les Z od centra
    [(49.725, 13.432), (49.724, 13.440), (49.720, 13.443),
     (49.717, 13.440), (49.717, 13.433), (49.721, 13.430)],
]

# ── Rybníky a vodní plochy ────────────────────────────────────────────────────
# Velký Staroplzenecký/Sedlecký rybník na Úslavě (vpravo od Sedlce, JV)
POND_MAIN = [
    (49.733, 13.498), (49.730, 13.503), (49.727, 13.508),
    (49.724, 13.511), (49.720, 13.513), (49.717, 13.512),
    (49.714, 13.509), (49.712, 13.504), (49.712, 13.498),
    (49.714, 13.494), (49.718, 13.491), (49.722, 13.490),
    (49.726, 13.491), (49.730, 13.494),
]

WATER_POLYGONS = [
    # Menší rybník v centru Sedlce (u toku)
    [(49.728, 13.487), (49.726, 13.490), (49.724, 13.490),
     (49.723, 13.487), (49.724, 13.484), (49.727, 13.484)],
    # Rybníček Z od centra (u Olešné)
    [(49.722, 13.445), (49.720, 13.449), (49.718, 13.449),
     (49.717, 13.446), (49.718, 13.443), (49.721, 13.443)],
    # Malý rybník pod Radyní
    [(49.708, 13.450), (49.706, 13.454), (49.704, 13.453),
     (49.703, 13.449), (49.705, 13.447)],
]

# ── Vodní toky ────────────────────────────────────────────────────────────────
# Úslava – teče od S na SZ, prochází rybníkem
RIVER_USLAVA = [
    (49.696, 13.510),
    (49.700, 13.510),
    (49.705, 13.508),
    (49.710, 13.505),
    (49.712, 13.501),   # vstup do rybníku
    (49.720, 13.513),   # přes rybník
    (49.733, 13.498),   # výtok ze severu
    (49.738, 13.495),
    (49.743, 13.494),
    (49.748, 13.493),
]

# Potok Olešná – Z od centra
STREAM_OLESNA = [
    (49.697, 13.440),
    (49.702, 13.443),
    (49.707, 13.447),
    (49.712, 13.452),
    (49.717, 13.457),
    (49.720, 13.462),
    (49.722, 13.469),
    (49.724, 13.478),
    (49.726, 13.487),
    (49.727, 13.490),
]

# Menší tok k rybníku
STREAM_SMALL = [
    (49.718, 13.486),
    (49.719, 13.490),
    (49.721, 13.493),
    (49.723, 13.495),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  S I L N I C E  &  Ž E L E Z N I C E
# ═══════════════════════════════════════════════════════════════════════════════

# Silnice II/180 – hlavní průtah Starým Plzencem
# Z Plzně (SZ) → centrum → JV (Šťáhlavy / Blovice)
ROAD_MAIN_180 = [
    (49.748, 13.440),   # SZ vstup (od Plzně)
    (49.742, 13.448),
    (49.736, 13.455),   # oblast Rotundy / S od centra
    (49.730, 13.460),
    (49.727, 13.464),
    (49.724, 13.468),   # centrum Starého Plzence
    (49.721, 13.472),
    (49.718, 13.477),
    (49.715, 13.483),   # křižovatka u nádraží
    (49.712, 13.490),
    (49.709, 13.498),
    (49.707, 13.507),
    (49.705, 13.517),   # JV výjezd (Šťáhlavy)
]

# Radyňská – od centra na JZ k hradu Radyně
ROAD_RADYNSKA = [
    (49.724, 13.468),   # centrum
    (49.721, 13.465),
    (49.718, 13.462),
    (49.715, 13.460),
    (49.712, 13.458),
    (49.709, 13.456),
    (49.706, 13.453),   # hrad Radyně
]

# Silnice do Sedlce (od centra na V/SV)
ROAD_TO_SEDLEC = [
    (49.724, 13.468),
    (49.726, 13.474),
    (49.727, 13.479),
    (49.728, 13.483),
    (49.729, 13.488),
    (49.730, 13.492),   # Sedlec centrum
    (49.732, 13.498),
    (49.734, 13.504),
]

# Silnice Z od centra (k Olešné / Plzeň via Dýšina)
ROAD_WEST = [
    (49.724, 13.468),
    (49.722, 13.460),
    (49.721, 13.452),
    (49.720, 13.444),
    (49.719, 13.436),
    (49.718, 13.430),
]

# Silnice na Rotundu / sever (Roupovská / k Hůrce)
ROAD_ROTUNDA = [
    (49.724, 13.468),
    (49.727, 13.463),
    (49.730, 13.459),
    (49.733, 13.457),
    (49.736, 13.455),
    (49.738, 13.454),   # Rotunda sv. Petra a Pavla
    (49.741, 13.452),
    (49.745, 13.449),
    (49.748, 13.448),
]

# Vedlejší silnice – Bezděkov (J od centra, k Bezděkovu)
ROAD_BEZDEKOV = [
    (49.715, 13.483),   # u nádraží
    (49.713, 13.475),
    (49.711, 13.470),
    (49.710, 13.465),
    (49.709, 13.460),   # Bezděkov
    (49.706, 13.453),   # propojení na Radyni
]

# Silnice Sedlec – sever (k výjezdu ze Sedlce)
ROAD_SEDLEC_N = [
    (49.730, 13.492),
    (49.734, 13.492),
    (49.738, 13.490),
    (49.742, 13.490),
    (49.746, 13.491),
    (49.748, 13.492),
]

# Silnice Sedlec – JV (kolem rybníku)
ROAD_SEDLEC_SE = [
    (49.730, 13.492),
    (49.728, 13.498),
    (49.726, 13.504),
    (49.724, 13.510),
    (49.722, 13.515),
    (49.720, 13.517),
]

# ── Železniční trať Plzeň–Písek ───────────────────────────────────────────────
# Prochází jižní částí Starého Plzence, nádraží uprostřed
RAILWAY = [
    (49.730, 13.430),   # SZ vstup trati
    (49.726, 13.438),
    (49.722, 13.447),
    (49.719, 13.457),
    (49.716, 13.468),   # oblast nádraží
    (49.715, 13.480),
    (49.714, 13.492),
    (49.713, 13.500),
    (49.712, 13.507),
    (49.711, 13.517),   # výjezd JV
]

# ── Ulice v centru Starého Plzence ────────────────────────────────────────────
STREETS = [
    # Masarykovo náměstí (smyčka)
    [(49.7230, 13.4665), (49.7232, 13.4685), (49.7218, 13.4690),
     (49.7215, 13.4670), (49.7220, 13.4660), (49.7230, 13.4665)],
    # Plzeňská (západ náměstí)
    [(49.7225, 13.4580), (49.7227, 13.4610), (49.7228, 13.4640),
     (49.7228, 13.4660)],
    # Rooseveltova (V od náměstí)
    [(49.7232, 13.4685), (49.7238, 13.4695), (49.7244, 13.4704)],
    # Komenského (S od náměstí)
    [(49.7232, 13.4665), (49.7240, 13.4658), (49.7248, 13.4652)],
    # Tyršova
    [(49.7218, 13.4690), (49.7212, 13.4700), (49.7208, 13.4712)],
    # Nádražní (k nádraží)
    [(49.7215, 13.4670), (49.7208, 13.4678), (49.7200, 13.4688),
     (49.7192, 13.4700), (49.7185, 13.4715)],
    # K Sedlci / Sedlecká
    [(49.7244, 13.4704), (49.7250, 13.4720), (49.7258, 13.4740),
     (49.7264, 13.4760), (49.7270, 13.4790), (49.7275, 13.4830)],
    # Ke Strži / pod Radyni
    [(49.7200, 13.4688), (49.7195, 13.4696), (49.7188, 13.4706)],
    # Zahradní
    [(49.7215, 13.4670), (49.7210, 13.4655), (49.7207, 13.4640),
     (49.7205, 13.4620)],
    # Lipová
    [(49.7248, 13.4652), (49.7252, 13.4665), (49.7255, 13.4680),
     (49.7255, 13.4695)],
    # V Zahradách
    [(49.7244, 13.4704), (49.7244, 13.4720), (49.7240, 13.4735)],
    # Bezděkovská (propoj)
    [(49.7185, 13.4715), (49.7178, 13.4720), (49.7170, 13.4720)],
    # Ke Konci (slepá J)
    [(49.7185, 13.4715), (49.7180, 13.4730), (49.7176, 13.4745)],
    # Olešná – ulice Z
    [(49.7228, 13.4640), (49.7222, 13.4630), (49.7215, 13.4615),
     (49.7210, 13.4600)],
    # Spojka na Sedlec přes pole
    [(49.7275, 13.4830), (49.7283, 13.4860), (49.7290, 13.4885)],
    # U Rybníka
    [(49.7262, 13.4900), (49.7258, 13.4912), (49.7252, 13.4920)],
    # Sedlec – hlavní ulice
    [(49.7290, 13.4885), (49.7298, 13.4895), (49.7308, 13.4906),
     (49.7316, 13.4915), (49.7322, 13.4920)],
    # Sedlec – příčná
    [(49.7300, 13.4860), (49.7305, 13.4878), (49.7308, 13.4895)],
    # Sedlec – k rybníku (V)
    [(49.7305, 13.4906), (49.7308, 13.4920), (49.7310, 13.4940),
     (49.7308, 13.4960)],
]

# ═══════════════════════════════════════════════════════════════════════════════
#  S V G   G E N E R A T O R
# ═══════════════════════════════════════════════════════════════════════════════

def build():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'width="{SVG}" height="{SVG}" viewBox="0 0 {SVG} {SVG}">')
    out.append(f'  <title>Starý Plzenec · vektorová mapa · laser cut</title>')

    # Pozadí
    out.append(f'  <rect width="{SVG}" height="{SVG}" fill="#f4efe5"/>')

    # ── Lesy ──
    out.append('  <g id="lesy">')
    for f in FORESTS:
        out.append('    ' + polygon(f, fill="#c8dda8", stroke="#8ab862",
                                    stroke_width="0.3", opacity="0.7"))
    out.append('  </g>')

    # ── Velký rybník ──
    out.append('  <g id="rybnik-hlavni">')
    out.append('    ' + polygon(POND_MAIN, fill="#6db8e0", stroke="#3a88b8",
                                stroke_width="0.8"))
    out.append('  </g>')

    # ── Menší vodní plochy ──
    out.append('  <g id="rybníky">')
    for w in WATER_POLYGONS:
        out.append('    ' + polygon(w, fill="#7ec4e0", stroke="#3a88b8",
                                    stroke_width="0.6"))
    out.append('  </g>')

    # ── Vodní toky ──
    out.append('  <g id="toky">')
    out.append('    ' + polyline(RIVER_USLAVA, fill="none", stroke="#3a88b8",
                                 stroke_width="2.0",
                                 stroke_linecap="round", stroke_linejoin="round"))
    out.append('    ' + polyline(STREAM_OLESNA, fill="none", stroke="#5598c0",
                                 stroke_width="1.0",
                                 stroke_linecap="round", stroke_linejoin="round"))
    out.append('    ' + polyline(STREAM_SMALL, fill="none", stroke="#5598c0",
                                 stroke_width="0.6",
                                 stroke_linecap="round", stroke_linejoin="round"))
    out.append('  </g>')

    # ── Železnice ──
    out.append('  <g id="zeleznice">')
    # Podklad dráhy (šedý)
    out.append('    ' + polyline(RAILWAY, fill="none", stroke="#888888",
                                 stroke_width="3.5",
                                 stroke_linecap="butt", stroke_linejoin="round"))
    # Bílé pražce (čárkovaná)
    out.append('    ' + polyline(RAILWAY, fill="none", stroke="#eeeeee",
                                 stroke_width="1.5",
                                 stroke_dasharray="6,5",
                                 stroke_linecap="butt", stroke_linejoin="round"))
    out.append('  </g>')

    # ── Silnice – casing ──
    road_defs = [
        (ROAD_MAIN_180,   6.5, "#ffffff"),
        (ROAD_ROTUNDA,    5.0, "#ffffff"),
        (ROAD_RADYNSKA,   4.5, "#ffffff"),
        (ROAD_TO_SEDLEC,  4.5, "#ffffff"),
        (ROAD_WEST,       4.2, "#ffffff"),
        (ROAD_BEZDEKOV,   3.8, "#ffffff"),
        (ROAD_SEDLEC_N,   4.2, "#ffffff"),
        (ROAD_SEDLEC_SE,  3.8, "#ffffff"),
    ]
    out.append('  <g id="silnice-casing">')
    for coords, w, col in road_defs:
        out.append('    ' + polyline(coords, fill="none", stroke=col,
                                     stroke_width=str(w),
                                     stroke_linecap="round",
                                     stroke_linejoin="round"))
    out.append('  </g>')

    # ── Silnice – fill ──
    road_fill = [
        (ROAD_MAIN_180,   4.2, "#e8903a"),   # hlavní – oranžová
        (ROAD_ROTUNDA,    3.0, "#e8a040"),   # vedlejší hlavní
        (ROAD_RADYNSKA,   2.8, "#e8a040"),
        (ROAD_TO_SEDLEC,  2.8, "#e8a040"),
        (ROAD_WEST,       2.5, "#d0d0d0"),
        (ROAD_BEZDEKOV,   2.2, "#d0d0d0"),
        (ROAD_SEDLEC_N,   2.6, "#e8a040"),
        (ROAD_SEDLEC_SE,  2.3, "#d0d0d0"),
    ]
    out.append('  <g id="silnice">')
    for coords, w, col in road_fill:
        out.append('    ' + polyline(coords, fill="none", stroke=col,
                                     stroke_width=str(w),
                                     stroke_linecap="round",
                                     stroke_linejoin="round"))
    out.append('  </g>')

    # ── Ulice v centru ──
    out.append('  <g id="ulice">')
    for s in STREETS:
        out.append('    ' + polyline(s, fill="none", stroke="#cccccc",
                                     stroke_width="1.3",
                                     stroke_linecap="round",
                                     stroke_linejoin="round"))
    out.append('  </g>')

    # ── Popisky ──
    def lbl(lat, lon, text, fs=10, fw="normal", col="#222",
            dx=0, dy=0, anchor="middle", halo="#f4efe5"):
        x, y = px(lat, lon)
        return (f'<text x="{x+dx:.1f}" y="{y+dy:.1f}" '
                f'font-size="{fs}" font-weight="{fw}" fill="{col}" '
                f'text-anchor="{anchor}" font-family="Arial,sans-serif" '
                f'stroke="{halo}" stroke-width="3" paint-order="stroke">'
                f'{text}</text>')

    out.append('  <g id="popisky">')

    # Starý Plzenec
    out.append('    ' + lbl(49.7240, 13.4680, "STARÝ PLZENEC",
                             fs=13, fw="bold", col="#111", dy=-2))

    # Sedlec
    out.append('    ' + lbl(49.7300, 13.4910, "SEDLEC",
                             fs=10, fw="bold", col="#333", dy=-3))

    # Radyně – stylizovaná věž
    rx, ry = px(49.706, 13.453)
    out.append(f'    <g id="radyne" transform="translate({rx},{ry})">')
    out.append(f'      <circle r="6" fill="#7a3010" stroke="#401000" stroke-width="1"/>')
    out.append(f'      <rect x="-3.5" y="-13" width="7" height="9" '
               f'fill="#7a3010" stroke="#401000" stroke-width="0.8"/>')
    out.append(f'      <rect x="-4.5" y="-16" width="3" height="4" fill="#7a3010"/>')
    out.append(f'      <rect x="-0.5" y="-16" width="2.5" height="4" fill="#f4efe5"/>')
    out.append(f'      <rect x="2"    y="-16" width="3" height="4" fill="#7a3010"/>')
    out.append(f'    </g>')
    out.append('    ' + lbl(49.706, 13.453, "Radyně",
                             fs=9, fw="bold", col="#5a1800", dy=20))

    # Rotunda
    bx, by = px(49.738, 13.454)
    out.append(f'    <circle cx="{bx}" cy="{by}" r="5" '
               f'fill="#5b2d8e" stroke="#3a1866" stroke-width="1"/>')
    out.append(f'    <text x="{bx}" y="{by-8}" '
               f'font-size="8.5" font-weight="bold" fill="#4a1878" '
               f'text-anchor="middle" font-family="Arial,sans-serif" '
               f'stroke="#f4efe5" stroke-width="2.5" paint-order="stroke">'
               f'Rotunda sv. Petra a Pavla</text>')

    # Popisky vody
    out.append('    ' + lbl(49.7208, 13.5020, "Staroplzenecký\nrybník",
                             fs=8, col="#2060a0", dy=0))
    out.append('    ' + lbl(49.7230, 13.4620, "Olešná",
                             fs=7.5, col="#3078b0", dy=0, anchor="start"))
    out.append('    ' + lbl(49.7155, 13.5060, "Úslava",
                             fs=7.5, col="#2060a0", dy=0, anchor="start"))

    # Radyňská (ulice)
    ux, uy = px(49.7185, 13.4590)
    out.append(f'    <text x="{ux}" y="{uy}" '
               f'font-size="7.5" fill="#888" text-anchor="middle" '
               f'font-family="Arial,sans-serif" font-style="italic" '
               f'transform="rotate(-45,{ux},{uy})">'
               f'Radyňská</text>')

    # Popis II/180
    qx, qy = px(49.7100, 13.5040)
    out.append(f'    <text x="{qx}" y="{qy}" '
               f'font-size="7" fill="#7a4010" text-anchor="middle" '
               f'font-family="Arial,sans-serif" '
               f'stroke="#f4efe5" stroke-width="2" paint-order="stroke">'
               f'II/180</text>')

    out.append('  </g>')

    # ── Kompas ──
    ncx, ncy = SVG - PAD - 20, PAD + 22
    out.append(f'  <g id="kompas" transform="translate({ncx},{ncy})">')
    out.append(f'    <circle r="17" fill="white" stroke="#ccc" stroke-width="0.8" opacity="0.85"/>')
    out.append(f'    <polygon points="0,-13 3.5,4 0,1.5 -3.5,4" fill="#c0392b" stroke="none"/>')
    out.append(f'    <polygon points="0,13 3.5,-4 0,-1.5 -3.5,-4" fill="#888" stroke="none"/>')
    out.append(f'    <text x="0" y="-16" text-anchor="middle" '
               f'font-size="8" font-weight="bold" font-family="Arial" fill="#333">N</text>')
    out.append(f'  </g>')

    # ── Měřítko (1 km) ──
    km_per_px = (E - W) * cos_m * 111.32 / map_w
    sc_px = 1.0 / km_per_px
    sx, sy = ox + 6, oy + map_h - 10
    out.append(f'  <g id="meritko">')
    out.append(f'    <rect x="{sx-2}" y="{sy-14}" width="{sc_px+4:.0f}" height="18" '
               f'fill="white" opacity="0.75" rx="2"/>')
    out.append(f'    <line x1="{sx:.0f}" y1="{sy:.0f}" x2="{sx+sc_px:.0f}" y2="{sy:.0f}" '
               f'stroke="#333" stroke-width="2"/>')
    out.append(f'    <line x1="{sx:.0f}" y1="{sy-4}" x2="{sx:.0f}" y2="{sy+4}" '
               f'stroke="#333" stroke-width="1.5"/>')
    out.append(f'    <line x1="{sx+sc_px:.0f}" y1="{sy-4}" x2="{sx+sc_px:.0f}" y2="{sy+4}" '
               f'stroke="#333" stroke-width="1.5"/>')
    out.append(f'    <text x="{sx+sc_px/2:.0f}" y="{sy-6}" '
               f'text-anchor="middle" font-size="8" font-family="Arial" fill="#333">1 km</text>')
    out.append(f'  </g>')

    # ── Titul ──
    out.append(f'  <text x="{SVG//2}" y="{SVG-5}" '
               f'font-family="Arial" font-size="7.5" text-anchor="middle" fill="#999">'
               f'© OpenStreetMap contributors · Starý Plzenec · laser map</text>')

    # ── Rámeček ──
    out.append(f'  <rect x="1.5" y="1.5" width="{SVG-3}" height="{SVG-3}" '
               f'fill="none" stroke="#555" stroke-width="1.5"/>')
    out.append(f'  <rect x="{ox-5}" y="{oy-5}" '
               f'width="{map_w+10}" height="{map_h+10}" '
               f'fill="none" stroke="#aaa" stroke-width="0.5" stroke-dasharray="4,3"/>')

    out.append('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "stary_plzenec.svg")
    svg = build()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✓ {out_path}")
    print(f"  SVG {SVG}×{SVG} px  |  bbox {S}–{N}°N, {W}–{E}°E")
    print(f"  mapa: {map_w}×{map_h} px  ({lat_km:.1f}×{lon_km:.1f} km)")
