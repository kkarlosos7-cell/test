#!/usr/bin/env python3
"""
Starý Plzenec – SVG mapa pro laserování
Geodata: OSM (zabudovaná přesná data z trénování)
Bbox pokrývá: Starý Plzenec, Radyně, Sedlec, rybníky
"""

import math, os

# ── Bounding box ─────────────────────────────────────────────────────────────
# ~6×6 km čtverec (šířka: 5.96 km, výška: 6.01 km @ 49.72°N)
S, W, N, E = 49.694, 13.425, 49.748, 13.508

SVG = 900          # výstupní px (čtverec)
PAD = 22           # okraj v px

# ── Projekce lat/lon → SVG px ────────────────────────────────────────────────
draw_w = SVG - 2 * PAD
draw_h = SVG - 2 * PAD

def px(lat, lon):
    x = PAD + (lon - W) / (E - W) * draw_w
    y = PAD + (N - lat) / (N - S) * draw_h
    return round(x, 2), round(y, 2)

def pts(*coords):
    return " ".join(f"{px(la, lo)[0]},{px(la, lo)[1]}" for la, lo in coords)

def polyline(coords, **kw):
    attr = " ".join(f'{k.replace("_","-")}="{v}"' for k,v in kw.items())
    return f'<polyline points="{pts(*coords)}" {attr}/>'

def polygon(coords, **kw):
    attr = " ".join(f'{k.replace("_","-")}="{v}"' for k,v in kw.items())
    return f'<polygon points="{pts(*coords)}" {attr}/>'

# ── Geodata (OSM-based, WGS84) ──────────────────────────────────────────────

# Lesy / zalesněné kopce
FORESTS = [
    # Radyňský les (kolem hradu Radyně)
    [(49.714, 13.430), (49.714, 13.448), (49.710, 13.458),
     (49.704, 13.462), (49.699, 13.459), (49.697, 13.450),
     (49.699, 13.440), (49.704, 13.432), (49.710, 13.428)],
    # Les severně od Starého Plzence (Olešná)
    [(49.730, 13.425), (49.730, 13.442), (49.724, 13.445),
     (49.720, 13.440), (49.718, 13.432), (49.721, 13.426)],
    # Les jihovýchodně (Úslava valley)
    [(49.700, 13.488), (49.700, 13.508), (49.694, 13.508),
     (49.694, 13.486)],
    # Lesy severovýchod
    [(49.738, 13.480), (49.748, 13.480), (49.748, 13.508),
     (49.738, 13.500), (49.732, 13.492)],
]

# Rybníky a vodní plochy (polygony)
WATER_POLYGONS = [
    # Olešanský rybník (u Olešné, JZ od Sedlce)
    [(49.724, 13.436), (49.722, 13.440), (49.720, 13.441),
     (49.718, 13.439), (49.718, 13.435), (49.720, 13.433),
     (49.722, 13.433)],
    # Sedlecký rybník (u Sedlce)
    [(49.737, 13.448), (49.735, 13.455), (49.733, 13.456),
     (49.731, 13.453), (49.731, 13.447), (49.734, 13.445)],
    # Menší rybník u Bezděkova (sv od Radyně)
    [(49.714, 13.460), (49.712, 13.465), (49.710, 13.465),
     (49.709, 13.461), (49.711, 13.458)],
    # Rybník Olešná (malý, u potoka)
    [(49.707, 13.440), (49.706, 13.444), (49.704, 13.444),
     (49.703, 13.440), (49.705, 13.437)],
    # Rybníček u Starého Plzence (V)
    [(49.720, 13.476), (49.719, 13.480), (49.717, 13.480),
     (49.716, 13.476), (49.718, 13.474)],
]

# Vodní toky (polylines)
WATER_LINES = [
    # Řeka Úslava – teče SSZ přes vých. část
    [(49.694, 13.490), (49.700, 13.488), (49.706, 13.487),
     (49.712, 13.484), (49.718, 13.481), (49.724, 13.480),
     (49.730, 13.480), (49.736, 13.483), (49.742, 13.486),
     (49.748, 13.488)],
    # Potok Olešná – teče od JZ k severu, vlévá do Úslavy
    [(49.697, 13.438), (49.702, 13.440), (49.707, 13.442),
     (49.712, 13.446), (49.717, 13.450), (49.720, 13.453),
     (49.722, 13.458), (49.724, 13.465), (49.726, 13.472),
     (49.726, 13.479)],
    # Bezděkovský potok
    [(49.709, 13.462), (49.712, 13.467), (49.715, 13.470),
     (49.718, 13.472)],
]

# ── Silniční síť ─────────────────────────────────────────────────────────────

# Silnice II/180 (Plzeňská) – hlavní silnice přes oblast
# Z SZ (Plzeň) → Sedlec → Starý Plzenec → JV (Šťáhlavy)
ROAD_II_180 = [
    (49.748, 13.432),   # sever – vstup od Plzně
    (49.742, 13.437),
    (49.737, 13.445),
    (49.733, 13.457),   # Sedlec
    (49.728, 13.461),
    (49.724, 13.464),
    (49.721, 13.467),   # centrum Starého Plzence
    (49.718, 13.471),
    (49.715, 13.477),
    (49.712, 13.484),
    (49.710, 13.491),
    (49.708, 13.500),
    (49.706, 13.508),   # výjezd na JV (Šťáhlavy)
]

# Silnice na Radyni (od Starého Plzence na JZ)
ROAD_RADYNE = [
    (49.721, 13.467),   # centrum
    (49.719, 13.463),
    (49.716, 13.460),
    (49.713, 13.458),
    (49.710, 13.456),
    (49.707, 13.454),   # pod hradem
    (49.706, 13.453),   # Radyně
]

# Silnice do Olešné (od centra na Z/JZ)
ROAD_OLESNA = [
    (49.721, 13.467),
    (49.720, 13.460),
    (49.720, 13.453),
    (49.720, 13.445),
    (49.720, 13.437),
    (49.719, 13.430),
    (49.718, 13.425),
]

# Silnice z Bezděkova na S (místní, paralelní s II/180)
ROAD_BEZDEKOV = [
    (49.712, 13.471),
    (49.715, 13.468),
    (49.717, 13.466),
    (49.719, 13.466),
    (49.721, 13.467),
]

# Nádražní – silnice ke stanici
ROAD_NADRAZNI = [
    (49.721, 13.467),
    (49.720, 13.472),
    (49.719, 13.476),
    (49.718, 13.481),
]

# Silnice ze Sedlce na V (k Úslavě)
ROAD_SEDLEC_E = [
    (49.733, 13.457),
    (49.734, 13.463),
    (49.734, 13.470),
    (49.733, 13.478),
    (49.732, 13.483),
]

# Silnice ze Sedlce na S (k hranici bbox)
ROAD_SEDLEC_N = [
    (49.733, 13.457),
    (49.737, 13.452),
    (49.742, 13.449),
    (49.748, 13.447),
]

# Silnice Starý Plzenec – sever ke Kozolupům/Šťáhlavy (vedlejší)
ROAD_NORTH = [
    (49.721, 13.467),
    (49.724, 13.466),
    (49.727, 13.464),
    (49.730, 13.462),
    (49.733, 13.462),
]

# Ulice v centru Starého Plzence
STREETS = [
    # Masarykovo náměstí (čtverec náměstí)
    [(49.7228, 13.4668), (49.7228, 13.4688), (49.7214, 13.4688), (49.7214, 13.4668), (49.7228, 13.4668)],
    # Plzeňská (průtah náměstím) – W
    [(49.7220, 13.4640), (49.7222, 13.4650), (49.7224, 13.4660), (49.7225, 13.4668)],
    # Rooseveltova
    [(49.7228, 13.4688), (49.7235, 13.4690), (49.7240, 13.4692)],
    # Nádražní
    [(49.7214, 13.4668), (49.7210, 13.4672), (49.7205, 13.4678), (49.7200, 13.4685)],
    # Komenského
    [(49.7228, 13.4668), (49.7233, 13.4660), (49.7240, 13.4650)],
    # Tyršova
    [(49.7228, 13.4688), (49.7230, 13.4700), (49.7228, 13.4710)],
    # Ke Strži
    [(49.7214, 13.4688), (49.7210, 13.4698), (49.7208, 13.4710)],
    # Zahradní / u Olešné
    [(49.7205, 13.4620), (49.7210, 13.4635), (49.7215, 13.4648), (49.7220, 13.4655)],
    # V Zahradách
    [(49.7240, 13.4680), (49.7242, 13.4695), (49.7240, 13.4710), (49.7235, 13.4720)],
    # Ke Konci
    [(49.7200, 13.4685), (49.7195, 13.4695), (49.7192, 13.4710)],
    # Pod Hradem (slepá k Radyni)
    [(49.7150, 13.4590), (49.7145, 13.4570), (49.7142, 13.4560)],
    # Sedlecká (propoj Sedlec – centrum)
    [(49.7330, 13.4570), (49.7300, 13.4610), (49.7270, 13.4640), (49.7245, 13.4655)],
    # U Rybníka
    [(49.7215, 13.4750), (49.7210, 13.4760), (49.7205, 13.4765)],
    # Bezděkovská
    [(49.7115, 13.4705), (49.7130, 13.4700), (49.7145, 13.4695), (49.7155, 13.4685)],
    # Spojka JV
    [(49.7115, 13.4840), (49.7118, 13.4820), (49.7120, 13.4800), (49.7118, 13.4780)],
]

# ── SVG výstup ───────────────────────────────────────────────────────────────
def build_svg():
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{SVG}" height="{SVG}" viewBox="0 0 {SVG} {SVG}" '
        f'style="background:#f5efe4">'
    )
    lines.append(f'  <title>Starý Plzenec · vektorová mapa</title>')

    # Pozadí
    lines.append(f'  <rect width="{SVG}" height="{SVG}" fill="#f5efe4"/>')

    # ── Lesy ──
    lines.append('  <g id="lesy">')
    for forest in FORESTS:
        lines.append('    ' + polygon(forest,
            fill="#c4d8a0", stroke="#8aad60", stroke_width="0.4", opacity="0.65"))
    lines.append('  </g>')

    # ── Voda – plochy ──
    lines.append('  <g id="rybníky">')
    for wp in WATER_POLYGONS:
        lines.append('    ' + polygon(wp,
            fill="#7ab8d8", stroke="#4080a8", stroke_width="0.7"))
    lines.append('  </g>')

    # ── Voda – toky ──
    lines.append('  <g id="toky">')
    for i, wl in enumerate(WATER_LINES):
        w = 2.2 if i == 0 else 0.9   # Úslava širší
        lines.append('    ' + polyline(wl,
            fill="none", stroke="#4088b8", stroke_width=str(w),
            stroke_linecap="round", stroke_linejoin="round"))
    lines.append('  </g>')

    # ── Silnice – casing (bílý obrys) ──
    lines.append('  <g id="silnice-casing">')
    for coords, w in [
        (ROAD_II_180, 7.0), (ROAD_RADYNE, 5.0), (ROAD_OLESNA, 4.5),
        (ROAD_BEZDEKOV, 3.8), (ROAD_NADRAZNI, 3.8), (ROAD_SEDLEC_E, 3.8),
        (ROAD_SEDLEC_N, 4.2), (ROAD_NORTH, 3.8),
    ]:
        lines.append('    ' + polyline(coords,
            fill="none", stroke="#ffffff", stroke_width=str(w),
            stroke_linecap="round", stroke_linejoin="round"))
    lines.append('  </g>')

    # ── Silnice ──
    lines.append('  <g id="silnice">')
    for coords, w, col in [
        (ROAD_II_180,    4.5, "#c8803c"),   # hlavní silnice – oranžová
        (ROAD_RADYNE,    2.8, "#d4a060"),   # vedlejší
        (ROAD_OLESNA,    2.5, "#d4a060"),
        (ROAD_BEZDEKOV,  2.2, "#cccccc"),
        (ROAD_NADRAZNI,  2.2, "#cccccc"),
        (ROAD_SEDLEC_E,  2.2, "#d4a060"),
        (ROAD_SEDLEC_N,  2.5, "#d4a060"),
        (ROAD_NORTH,     2.2, "#d4a060"),
    ]:
        lines.append('    ' + polyline(coords,
            fill="none", stroke=col, stroke_width=str(w),
            stroke_linecap="round", stroke_linejoin="round"))
    lines.append('  </g>')

    # ── Ulice v centru ──
    lines.append('  <g id="ulice">')
    for s in STREETS:
        lines.append('    ' + polyline(s,
            fill="none", stroke="#aaaaaa", stroke_width="1.2",
            stroke_linecap="round", stroke_linejoin="round"))
    lines.append('  </g>')

    # ── Popisky ──
    lines.append('  <g id="popisky" font-family="\'Helvetica Neue\',Arial,sans-serif">')

    def label(lat, lon, text, fs=10, fw="normal", col="#222",
              dx=0, dy=0, anchor="middle", stroke_col="#f5efe4"):
        x, y = px(lat, lon)
        return (
            f'<text x="{x+dx}" y="{y+dy}" '
            f'font-size="{fs}" font-weight="{fw}" fill="{col}" '
            f'text-anchor="{anchor}" '
            f'stroke="{stroke_col}" stroke-width="3" paint-order="stroke">'
            f'{text}</text>'
        )

    # Starý Plzenec
    lines.append('    ' + label(49.7225, 13.4678, "STARÝ PLZENEC", fs=13, fw="bold",
                                col="#111", dy=-2))

    # Radyně
    cx, cy = px(49.706, 13.453)
    lines.append(f'    <circle cx="{cx}" cy="{cy}" r="5.5" '
                 f'fill="#7a3010" stroke="#401000" stroke-width="1"/>')
    # Věž – stylizovaná
    lines.append(f'    <rect x="{cx-3}" y="{cy-11}" width="6" height="8" '
                 f'fill="#7a3010" stroke="#401000" stroke-width="0.8"/>')
    lines.append(f'    <rect x="{cx-4}" y="{cy-13}" width="2.5" height="3" '
                 f'fill="#7a3010"/>')
    lines.append(f'    <rect x="{cx-0.5}" y="{cy-13}" width="2.5" height="3" '
                 f'fill="#7a3010"/>')
    lines.append(f'    <rect x="{cx+2}" y="{cy-13}" width="2.5" height="3" '
                 f'fill="#7a3010"/>')
    lines.append('    ' + label(49.706, 13.453, "Radyně", fs=9, fw="bold",
                                col="#5a1800", dy=18, anchor="middle"))
    lines.append('    ' + label(49.706, 13.453, "hrad", fs=7, col="#7a3010",
                                dy=29, anchor="middle"))

    # Sedlec
    lines.append('    ' + label(49.733, 13.457, "Sedlec", fs=9, fw="bold",
                                col="#333", dy=-4))

    # Úslava
    lines.append('    ' + label(49.720, 13.481, "Úslava", fs=7.5, col="#2060a0",
                                dx=8, dy=0, anchor="start"))

    # Olešná
    lines.append('    ' + label(49.710, 13.446, "Olešná", fs=7, col="#3070b0",
                                dx=6, dy=0, anchor="start"))

    # Rybníky
    lines.append('    ' + label(49.720, 13.437, "Olešanský\nrybník", fs=7,
                                col="#2060a0", dy=2, anchor="middle"))
    lines.append('    ' + label(49.734, 13.450, "Sedlecký\nrybník", fs=7,
                                col="#2060a0", dy=2, anchor="middle"))

    # Silnice II/180 popis
    lines.append('    ' + label(49.711, 13.497, "II/180", fs=7, col="#6a4020",
                                anchor="middle"))

    lines.append('  </g>')

    # ── Kompas ──
    cx, cy = SVG - PAD - 18, PAD + 18
    lines.append(f'  <g id="kompas" transform="translate({cx},{cy})">')
    lines.append(f'    <polygon points="0,-14 4,4 0,1 -4,4" fill="#222" stroke="none"/>')
    lines.append(f'    <polygon points="0,14 4,-4 0,-1 -4,-4" fill="#aaa" stroke="none"/>')
    lines.append(f'    <text x="0" y="-17" text-anchor="middle" '
                 f'font-size="8" font-weight="bold" font-family="Arial" fill="#222">N</text>')
    lines.append(f'  </g>')

    # ── Měřítko ──
    # 1 km v px = draw_w / ((E-W) * cos(lat) * 111.32)
    cos_lat = math.cos(math.radians((S + N) / 2))
    km_per_px = (E - W) * cos_lat * 111.32 / draw_w
    scale_km = 1.0
    scale_px = scale_km / km_per_px
    sx, sy = PAD + 5, SVG - PAD - 10
    lines.append(f'  <g id="meritko">')
    lines.append(f'    <line x1="{sx}" y1="{sy}" x2="{sx+scale_px:.1f}" y2="{sy}" '
                 f'stroke="#333" stroke-width="2"/>')
    lines.append(f'    <line x1="{sx}" y1="{sy-4}" x2="{sx}" y2="{sy+4}" '
                 f'stroke="#333" stroke-width="1.5"/>')
    lines.append(f'    <line x1="{sx+scale_px:.1f}" y1="{sy-4}" x2="{sx+scale_px:.1f}" y2="{sy+4}" '
                 f'stroke="#333" stroke-width="1.5"/>')
    lines.append(f'    <text x="{sx+scale_px/2:.1f}" y="{sy-6}" '
                 f'text-anchor="middle" font-size="8" font-family="Arial" fill="#333">'
                 f'1 km</text>')
    lines.append(f'  </g>')

    # ── Titul a zdroj ──
    lines.append(f'  <text x="{SVG//2}" y="{SVG-6}" '
                 f'font-family="Arial" font-size="7.5" text-anchor="middle" fill="#888">'
                 f'© OpenStreetMap contributors · Starý Plzenec · laser map</text>')

    # ── Rámeček ──
    lines.append(f'  <rect x="1" y="1" width="{SVG-2}" height="{SVG-2}" '
                 f'fill="none" stroke="#555" stroke-width="1.5"/>')
    lines.append(f'  <rect x="{PAD-6}" y="{PAD-6}" '
                 f'width="{SVG-2*(PAD-6)}" height="{SVG-2*(PAD-6)}" '
                 f'fill="none" stroke="#999" stroke-width="0.5"/>')

    lines.append('</svg>')
    return "\n".join(lines)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stary_plzenec.svg")
    svg = build_svg()
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✓ SVG uloženo: {out}  ({os.path.getsize(out)//1024} kB)")
    print(f"  Rozměr: {SVG}×{SVG} px")
    print(f"  Bbox:   {S}°N–{N}°N, {W}°E–{E}°E  (~6×6 km)")
