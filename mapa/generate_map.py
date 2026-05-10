#!/usr/bin/env python3
"""
Starý Plzenec – SVG mapa z reálných OSM dat pro laserování
=========================================================
Spusť z vlastního PC (ne z cloudu – OSM blokuje cloudové IP).

Instalace závislostí:
    pip install osmnx shapely lxml

Spuštění:
    python generate_map.py

Výstup:
    stary_plzenec_osm.svg  (~900×900 px, čtverec, vrstvy pro laser)
"""

import math, os, sys

# ── Bbox: Starý Plzenec + Sedlec (V) + Radyně (JZ) + rybník Úslava ──────────
NORTH = 49.748
SOUTH = 49.696
WEST  = 13.430
EAST  = 13.517

OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "stary_plzenec_osm.svg")
SVG_SIZE = 920   # px – výstup je čtverec

# ─────────────────────────────────────────────────────────────────────────────

def check_deps():
    missing = []
    for pkg in ["osmnx", "shapely"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Chybí balíčky: {', '.join(missing)}")
        print(f"Nainstaluj je:  pip install {' '.join(missing)}")
        sys.exit(1)

# ── Projekce bbox → SVG čtverec ──────────────────────────────────────────────
cos_m  = math.cos(math.radians((NORTH + SOUTH) / 2))
lat_km = (NORTH - SOUTH) * 111.32
lon_km = (EAST  - WEST)  * cos_m * 111.32
PAD    = 28

if lat_km >= lon_km:
    map_h = SVG_SIZE - 2 * PAD
    map_w = int(map_h * lon_km / lat_km)
else:
    map_w = SVG_SIZE - 2 * PAD
    map_h = int(map_w * lat_km / lon_km)

ox = PAD + (SVG_SIZE - 2 * PAD - map_w) // 2
oy = PAD + (SVG_SIZE - 2 * PAD - map_h) // 2

def to_xy(lat, lon):
    x = ox + (lon - WEST)  / (EAST  - WEST)  * map_w
    y = oy + (NORTH - lat) / (NORTH - SOUTH) * map_h
    return x, y

def geom_to_points(geom):
    """Shapely geometry → SVG points string."""
    from shapely.geometry import LineString, Polygon, MultiLineString, MultiPolygon
    results = []
    if geom.geom_type == "LineString":
        results.append(_linestring_pts(geom))
    elif geom.geom_type == "MultiLineString":
        for part in geom.geoms:
            results.append(_linestring_pts(part))
    elif geom.geom_type == "Polygon":
        results.append(_linestring_pts(geom.exterior))
    elif geom.geom_type == "MultiPolygon":
        for part in geom.geoms:
            results.append(_linestring_pts(part.exterior))
    return results

def _linestring_pts(ls):
    parts = []
    for lon, lat in ls.coords:
        x, y = to_xy(lat, lon)
        parts.append(f"{x:.1f},{y:.1f}")
    return " ".join(parts)

# ── Barvy silnic ──────────────────────────────────────────────────────────────
ROAD_STYLE = {
    "motorway":      (5.5, "#e8603a", 8.0),
    "motorway_link": (3.5, "#e8603a", 5.5),
    "trunk":         (5.0, "#e8803a", 7.5),
    "trunk_link":    (3.0, "#e8803a", 5.0),
    "primary":       (4.2, "#e89030", 6.5),
    "primary_link":  (2.8, "#e89030", 4.5),
    "secondary":     (3.5, "#f0c040", 5.5),
    "secondary_link":(2.5, "#f0c040", 4.0),
    "tertiary":      (2.8, "#ffffff", 4.5),
    "tertiary_link": (2.0, "#ffffff", 3.5),
    "residential":   (2.0, "#ffffff", 3.5),
    "living_street": (1.8, "#ffffff", 3.2),
    "unclassified":  (2.0, "#ffffff", 3.5),
    "service":       (1.2, "#eeeeee", 2.2),
    "track":         (1.0, "#d4b890", 1.8),
    "path":          (0.5, "#cccccc", 0.0),
    "footway":       (0.5, "#cccccc", 0.0),
    "cycleway":      (0.6, "#88aad0", 0.0),
    "pedestrian":    (1.2, "#eeeeee", 2.0),
    "steps":         (0.5, "#bbbbbb", 0.0),
}

ROAD_ORDER = [
    "steps","path","footway","cycleway",
    "track","service","pedestrian","living_street",
    "residential","unclassified",
    "tertiary","tertiary_link",
    "secondary","secondary_link",
    "primary","primary_link",
    "trunk","trunk_link",
    "motorway","motorway_link",
]

def road_rank(hw):
    try:
        return ROAD_ORDER.index(hw)
    except ValueError:
        return -1

# ── Hlavní funkce ─────────────────────────────────────────────────────────────
def main():
    check_deps()
    import osmnx as ox
    from shapely.geometry import box

    bbox = (NORTH, SOUTH, EAST, WEST)   # osmnx format: N, S, E, W
    clip = box(WEST, SOUTH, EAST, NORTH)

    print("═" * 55)
    print("  Starý Plzenec – stahování OSM dat")
    print(f"  Bbox: {SOUTH}–{NORTH}°N, {WEST}–{EAST}°E")
    print("═" * 55)

    # ── Silniční síť ──
    print("  [1/4] Silnice ...")
    G = ox.graph_from_bbox(bbox, network_type="all",
                           retain_all=False, simplify=True)
    gdf_edges = ox.graph_to_gdfs(G, nodes=False)
    gdf_edges = gdf_edges.clip(clip)
    print(f"        {len(gdf_edges)} segmentů")

    # ── Vodní plochy ──
    print("  [2/4] Vodní plochy a rybníky ...")
    water_tags = {"natural": "water", "landuse": ["reservoir", "basin"],
                  "waterway": "riverbank"}
    try:
        gdf_water = ox.features_from_bbox(bbox, tags=water_tags)
        gdf_water = gdf_water.clip(clip)
        print(f"        {len(gdf_water)} ploch")
    except Exception as e:
        print(f"        (žádné: {e})")
        gdf_water = None

    # ── Vodní toky ──
    print("  [3/4] Řeky a potoky ...")
    stream_tags = {"waterway": ["river", "stream", "canal", "drain"]}
    try:
        gdf_streams = ox.features_from_bbox(bbox, tags=stream_tags)
        gdf_streams = gdf_streams[gdf_streams.geometry.geom_type.isin(
            ["LineString", "MultiLineString"])]
        gdf_streams = gdf_streams.clip(clip)
        print(f"        {len(gdf_streams)} toků")
    except Exception as e:
        print(f"        (žádné: {e})")
        gdf_streams = None

    # ── Zelené plochy ──
    print("  [4/4] Lesy a zeleň ...")
    green_tags = {"natural": ["wood", "scrub"], "landuse": ["forest", "meadow", "grass"]}
    try:
        gdf_green = ox.features_from_bbox(bbox, tags=green_tags)
        gdf_green = gdf_green[gdf_green.geometry.geom_type.isin(
            ["Polygon", "MultiPolygon"])]
        gdf_green = gdf_green.clip(clip)
        print(f"        {len(gdf_green)} ploch")
    except Exception as e:
        print(f"        (žádné: {e})")
        gdf_green = None

    print("\n  Generuji SVG ...")
    svg = render_svg(gdf_edges, gdf_water, gdf_streams, gdf_green)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)
    sz = os.path.getsize(OUT_FILE) // 1024
    print(f"\n  ✓ Hotovo: {OUT_FILE}  ({sz} kB)")
    print(f"  ✓ Rozměr: {SVG_SIZE}×{SVG_SIZE} px (čtverec)")
    print(f"  ✓ Oblasti: silnice, vodní plochy, toky, lesy")
    print("═" * 55)

# ── SVG renderer ──────────────────────────────────────────────────────────────
def render_svg(gdf_edges, gdf_water, gdf_streams, gdf_green):
    lines = []
    a = lines.append   # zkrácení

    a('<?xml version="1.0" encoding="UTF-8"?>')
    a(f'<svg xmlns="http://www.w3.org/2000/svg" '
      f'width="{SVG_SIZE}" height="{SVG_SIZE}" '
      f'viewBox="0 0 {SVG_SIZE} {SVG_SIZE}">')
    a(f'  <title>Starý Plzenec · OSM · laser map</title>')
    a(f'  <rect width="{SVG_SIZE}" height="{SVG_SIZE}" fill="#f4efe5"/>')

    # ── Zelené plochy ──
    if gdf_green is not None and len(gdf_green):
        a('  <g id="zelen" opacity="0.65">')
        for _, row in gdf_green.iterrows():
            lu = row.get("landuse", "") or ""
            nat = row.get("natural", "") or ""
            col = "#c4d8a0" if nat == "wood" or lu == "forest" else "#d8e8b8"
            stroke = "#96b866" if nat == "wood" or lu == "forest" else "#b0cc88"
            for pts in geom_to_points(row.geometry):
                a(f'    <polygon points="{pts}" '
                  f'fill="{col}" stroke="{stroke}" stroke-width="0.3"/>')
        a('  </g>')

    # ── Vodní plochy ──
    if gdf_water is not None and len(gdf_water):
        a('  <g id="voda-plochy">')
        for _, row in gdf_water.iterrows():
            for pts in geom_to_points(row.geometry):
                a(f'    <polygon points="{pts}" '
                  f'fill="#6db8e0" stroke="#3a88b8" stroke-width="0.7"/>')
        a('  </g>')

    # ── Vodní toky ──
    if gdf_streams is not None and len(gdf_streams):
        a('  <g id="voda-toky">')
        for _, row in gdf_streams.iterrows():
            ww = row.get("waterway", "stream")
            sw = "2.2" if ww == "river" else "0.9"
            for pts in geom_to_points(row.geometry):
                a(f'    <polyline points="{pts}" fill="none" '
                  f'stroke="#3a88b8" stroke-width="{sw}" '
                  f'stroke-linecap="round" stroke-linejoin="round"/>')
        a('  </g>')

    # ── Železnice ──
    rail_rows = gdf_edges[gdf_edges.get("railway", pd_na()).notna()
                          ] if "railway" in gdf_edges.columns else None
    # Filtruj přes highway – railway jede přes edges pokud je zaznačeno
    rail_mask = gdf_edges.index.get_level_values("osmid") if False else None

    # Zkus najít železnici v datech
    try:
        import pandas as pd
        hw_col = gdf_edges.get("highway") if hasattr(gdf_edges, "get") else None
        rail_df = gdf_edges[
            gdf_edges["highway"].astype(str).isin(["rail","light_rail","subway","tram"])
        ] if "highway" in gdf_edges.columns else pd.DataFrame()
    except Exception:
        rail_df = None

    if rail_df is not None and len(rail_df):
        a('  <g id="zeleznice">')
        for _, row in rail_df.iterrows():
            for pts in geom_to_points(row.geometry):
                a(f'    <polyline points="{pts}" fill="none" '
                  f'stroke="#888" stroke-width="3.5" '
                  f'stroke-linecap="butt"/>')
                a(f'    <polyline points="{pts}" fill="none" '
                  f'stroke="#eee" stroke-width="1.5" '
                  f'stroke-dasharray="7,5" stroke-linecap="butt"/>')
        a('  </g>')

    # ── Silnice – seřazené dle důležitosti ──
    road_df = gdf_edges.copy()
    road_df["_hw"] = road_df["highway"].apply(
        lambda v: (v if isinstance(v, str) else
                   (v[0] if isinstance(v, list) and v else "unclassified"))
    )
    road_df["_rank"] = road_df["_hw"].apply(road_rank)
    road_df = road_df.sort_values("_rank")

    # Casing (bílý obrys)
    a('  <g id="silnice-casing">')
    for _, row in road_df.iterrows():
        hw = row["_hw"]
        style = ROAD_STYLE.get(hw)
        if style is None:
            continue
        _w, _col, casing_w = style
        if casing_w <= 0:
            continue
        for pts in geom_to_points(row.geometry):
            a(f'    <polyline points="{pts}" fill="none" '
              f'stroke="#ffffff" stroke-width="{casing_w}" '
              f'stroke-linecap="round" stroke-linejoin="round"/>')
    a('  </g>')

    # Silnice samotné
    a('  <g id="silnice">')
    for _, row in road_df.iterrows():
        hw = row["_hw"]
        style = ROAD_STYLE.get(hw)
        if style is None:
            continue
        sw, col, _ = style
        dash = ' stroke-dasharray="5,4"' if hw in ("track", "path", "footway") else ""
        for pts in geom_to_points(row.geometry):
            a(f'    <polyline points="{pts}" fill="none" '
              f'stroke="{col}" stroke-width="{sw}"{dash} '
              f'stroke-linecap="round" stroke-linejoin="round"/>')
    a('  </g>')

    # ── Kompas ──
    ncx, ncy = SVG_SIZE - PAD - 20, PAD + 22
    a(f'  <g id="kompas" transform="translate({ncx},{ncy})">')
    a(f'    <circle r="17" fill="white" stroke="#ccc" '
      f'stroke-width="0.8" opacity="0.9"/>')
    a(f'    <polygon points="0,-13 3.5,4 0,1.5 -3.5,4" '
      f'fill="#c0392b" stroke="none"/>')
    a(f'    <polygon points="0,13 3.5,-4 0,-1.5 -3.5,-4" '
      f'fill="#aaa" stroke="none"/>')
    a(f'    <text x="0" y="-16" text-anchor="middle" '
      f'font-size="8" font-weight="bold" font-family="Arial" fill="#333">N</text>')
    a(f'  </g>')

    # ── Měřítko (1 km) ──
    km_per_px = lon_km / map_w
    sc_px = 1.0 / km_per_px
    sx, sy = ox + 6, oy + map_h - 10
    a(f'  <g id="meritko">')
    a(f'    <rect x="{sx-3}" y="{sy-16}" width="{sc_px+6:.0f}" height="20" '
      f'fill="white" opacity="0.8" rx="2"/>')
    a(f'    <line x1="{sx:.0f}" y1="{sy:.0f}" x2="{sx+sc_px:.0f}" y2="{sy:.0f}" '
      f'stroke="#333" stroke-width="2"/>')
    a(f'    <line x1="{sx:.0f}" y1="{sy-4}" x2="{sx:.0f}" y2="{sy+4}" '
      f'stroke="#333" stroke-width="1.5"/>')
    a(f'    <line x1="{sx+sc_px:.0f}" y1="{sy-4}" '
      f'x2="{sx+sc_px:.0f}" y2="{sy+4}" '
      f'stroke="#333" stroke-width="1.5"/>')
    a(f'    <text x="{sx+sc_px/2:.0f}" y="{sy-7}" '
      f'text-anchor="middle" font-size="8" '
      f'font-family="Arial" fill="#333">1 km</text>')
    a(f'  </g>')

    # ── Titulek ──
    a(f'  <text x="{SVG_SIZE//2}" y="{SVG_SIZE-6}" '
      f'font-family="Arial" font-size="7.5" '
      f'text-anchor="middle" fill="#999">'
      f'© OpenStreetMap contributors · Starý Plzenec · laser map</text>')

    # ── Rámeček ──
    a(f'  <rect x="1.5" y="1.5" width="{SVG_SIZE-3}" height="{SVG_SIZE-3}" '
      f'fill="none" stroke="#555" stroke-width="1.5"/>')

    a('</svg>')
    return "\n".join(lines)


def pd_na():
    """Bezpečný null pro pandas."""
    try:
        import pandas as pd
        return pd.NA
    except Exception:
        return None


if __name__ == "__main__":
    main()
