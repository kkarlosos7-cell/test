#!/usr/bin/env python3
"""
Starý Plzenec - vektorová SVG mapa pro laserování
Stahuje data z OpenStreetMap (Overpass API)
Zahrnuje: ulice, Radyně, Sedlec, rybníky
"""

import requests
import xml.etree.ElementTree as ET
import math
import os

# Bbox pokrývající Starý Plzenec, Radyni, Sedlec a rybníky
BBOX = {
    'south': 49.694,
    'west':  13.425,
    'north': 49.748,
    'east':  13.508
}

SVG_SIZE = 900  # px výstupní rozměr (čtverec)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OVERPASS_QUERY = """
[out:xml][timeout:90];
(
  way["highway"]({s},{w},{n},{e});
  way["natural"="water"]({s},{w},{n},{e});
  way["landuse"="reservoir"]({s},{w},{n},{e});
  way["landuse"="basin"]({s},{w},{n},{e});
  relation["natural"="water"]({s},{w},{n},{e});
  way["waterway"~"river|stream|canal"]({s},{w},{n},{e});
  way["natural"="wood"]({s},{w},{n},{e});
  way["landuse"="forest"]({s},{w},{n},{e});
  node["historic"="castle"]({s},{w},{n},{e});
  node["place"~"village|suburb|hamlet|quarter"]({s},{w},{n},{e});
);
out body;
>;
out skel qt;
"""


def fetch_osm(bbox):
    q = OVERPASS_QUERY.format(
        s=bbox['south'], w=bbox['west'],
        n=bbox['north'], e=bbox['east']
    )
    print("  Stahuji OSM data z Overpass API...")
    resp = requests.post(OVERPASS_URL, data={'data': q}, timeout=120)
    resp.raise_for_status()
    return resp.text


def parse_osm(xml_text):
    root = ET.fromstring(xml_text)

    nodes = {}
    for node in root.findall('node'):
        nid = node.get('id')
        lat = float(node.get('lat'))
        lon = float(node.get('lon'))
        tags = {t.get('k'): t.get('v') for t in node.findall('tag')}
        nodes[nid] = {'lat': lat, 'lon': lon, 'tags': tags}

    ways = []
    for way in root.findall('way'):
        tags = {t.get('k'): t.get('v') for t in way.findall('tag')}
        nds = [nd.get('ref') for nd in way.findall('nd')]
        ways.append({'tags': tags, 'nodes': nds, 'id': way.get('id')})

    return nodes, ways


def road_style(hw):
    """Vrátí (šířka_čáry, barva) pro typ silnice - optimalizováno pro laserování."""
    s = {
        'motorway':      (4.0,  '#1a1a1a'),
        'motorway_link': (2.5,  '#1a1a1a'),
        'trunk':         (3.5,  '#1a1a1a'),
        'trunk_link':    (2.0,  '#1a1a1a'),
        'primary':       (3.0,  '#111111'),
        'primary_link':  (2.0,  '#111111'),
        'secondary':     (2.5,  '#222222'),
        'secondary_link':(1.8,  '#222222'),
        'tertiary':      (2.0,  '#333333'),
        'tertiary_link': (1.5,  '#333333'),
        'residential':   (1.4,  '#444444'),
        'living_street': (1.2,  '#555555'),
        'unclassified':  (1.3,  '#444444'),
        'service':       (0.8,  '#666666'),
        'track':         (0.7,  '#888888'),
        'path':          (0.4,  '#999999'),
        'footway':       (0.4,  '#999999'),
        'cycleway':      (0.5,  '#777777'),
        'steps':         (0.4,  '#aaaaaa'),
        'pedestrian':    (0.8,  '#777777'),
    }
    return s.get(hw, (0.5, '#bbbbbb'))


def make_svg(nodes, ways, bbox, size):
    cos_mid = math.cos(math.radians((bbox['south'] + bbox['north']) / 2))
    lat_range = bbox['north'] - bbox['south']
    lon_range = (bbox['east'] - bbox['west']) * cos_mid

    # Výpočet rozměrů v reálném měřítku (zachování aspektu)
    km_lat = lat_range * 111.32
    km_lon = lon_range * 111.32

    if km_lat >= km_lon:
        svg_h = size
        svg_w = int(size * km_lon / km_lat)
    else:
        svg_w = size
        svg_h = int(size * km_lat / km_lon)

    pad = 20  # padding v px
    draw_w = svg_w - 2 * pad
    draw_h = svg_h - 2 * pad

    def xy(lat, lon):
        x = pad + (lon - bbox['west']) / (bbox['east'] - bbox['west']) * draw_w
        y = pad + (bbox['north'] - lat) / (bbox['north'] - bbox['south']) * draw_h
        return x, y

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'width="{svg_w}" height="{svg_h}" '
               f'viewBox="0 0 {svg_w} {svg_h}">')
    out.append(f'  <title>Starý Plzenec - vektorová mapa</title>')

    # Pozadí (světlý papír)
    out.append(f'  <rect width="{svg_w}" height="{svg_h}" fill="#f4efe6" stroke="none"/>')

    # ---- Lesy ----
    out.append('  <g id="lesy">')
    for way in ways:
        t = way['tags']
        if not (t.get('natural') == 'wood' or t.get('landuse') in ('forest',)):
            continue
        pts = _way_points(way, nodes, xy)
        if len(pts) >= 3:
            out.append(f'    <polygon points="{pts}" '
                       f'fill="#c8ddb0" stroke="#a0be80" stroke-width="0.3" opacity="0.6"/>')
    out.append('  </g>')

    # ---- Voda (plochy) ----
    out.append('  <g id="voda-plochy">')
    for way in ways:
        t = way['tags']
        is_water = (
            t.get('natural') == 'water' or
            t.get('landuse') in ('reservoir', 'basin') or
            t.get('waterway') in ('riverbank',)
        )
        if not is_water:
            continue
        nds = way['nodes']
        if not nds or nds[0] != nds[-1]:
            continue  # pouze uzavřené plochy
        pts = _way_points(way, nodes, xy)
        if len(pts) >= 3:
            out.append(f'    <polygon points="{pts}" '
                       f'fill="#8eb8d8" stroke="#5090b8" stroke-width="0.6"/>')
    out.append('  </g>')

    # ---- Vodní toky (čáry) ----
    out.append('  <g id="voda-toky">')
    for way in ways:
        t = way['tags']
        if t.get('waterway') not in ('river', 'stream', 'canal'):
            continue
        pts = _way_points(way, nodes, xy)
        if pts:
            ww = 1.2 if t.get('waterway') == 'river' else 0.6
            out.append(f'    <polyline points="{pts}" '
                       f'fill="none" stroke="#5090b8" stroke-width="{ww}"/>')
    out.append('  </g>')

    # ---- Silnice - vrstvení (nejprve casing, pak fill) ----
    # Řazení: nejprve malé, pak velké (aby velké byly navrchu)
    road_order = [
        'path', 'footway', 'steps', 'cycleway',
        'track', 'service',
        'pedestrian', 'living_street',
        'residential', 'unclassified',
        'tertiary', 'tertiary_link',
        'secondary', 'secondary_link',
        'primary', 'primary_link',
        'trunk', 'trunk_link',
        'motorway', 'motorway_link',
    ]

    road_ways = [w for w in ways if 'highway' in w['tags']]

    def sort_key(w):
        hw = w['tags'].get('highway', '')
        return road_order.index(hw) if hw in road_order else -1

    road_ways.sort(key=sort_key)

    # Casing (obrys silnic pro lepší čitelnost)
    out.append('  <g id="silnice-casing">')
    for way in road_ways:
        hw = way['tags'].get('highway', '')
        w, _ = road_style(hw)
        if w < 1.0:
            continue
        pts = _way_points(way, nodes, xy)
        if pts:
            cw = w + 1.0
            out.append(f'    <polyline points="{pts}" fill="none" '
                       f'stroke="#ffffff" stroke-width="{cw}" '
                       f'stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>')
    out.append('  </g>')

    # Silnice samotné
    out.append('  <g id="silnice">')
    for way in road_ways:
        hw = way['tags'].get('highway', '')
        w, col = road_style(hw)
        pts = _way_points(way, nodes, xy)
        if pts:
            dash = 'stroke-dasharray="4,3"' if hw in ('track', 'path', 'footway') else ''
            out.append(f'    <polyline points="{pts}" fill="none" '
                       f'stroke="{col}" stroke-width="{w}" '
                       f'stroke-linecap="round" stroke-linejoin="round" {dash}/>')
    out.append('  </g>')

    # ---- Popisky míst ----
    out.append('  <g id="popisy" font-family="Arial,sans-serif" text-anchor="middle">')
    for nid, nd in nodes.items():
        t = nd['tags']
        name = t.get('name', '')
        place = t.get('place', '')
        historic = t.get('historic', '')

        if not name:
            continue

        nx, ny = xy(nd['lat'], nd['lon'])

        if historic == 'castle' or 'Radyně' in name:
            out.append(f'    <circle cx="{nx:.1f}" cy="{ny:.1f}" r="4" '
                       f'fill="#8B4513" stroke="#4a2000" stroke-width="0.8"/>')
            out.append(f'    <text x="{nx:.1f}" y="{ny - 7:.1f}" '
                       f'font-size="8" font-weight="bold" fill="#4a2000" '
                       f'stroke="white" stroke-width="2" paint-order="stroke">'
                       f'{name}</text>')
        elif place in ('village', 'suburb', 'quarter', 'hamlet'):
            fs = 9 if place == 'village' else 7
            out.append(f'    <text x="{nx:.1f}" y="{ny:.1f}" '
                       f'font-size="{fs}" font-weight="bold" fill="#222" '
                       f'stroke="#f4efe6" stroke-width="2.5" paint-order="stroke">'
                       f'{name}</text>')

    out.append('  </g>')

    # ---- Rámeček ----
    out.append(f'  <rect x="0" y="0" width="{svg_w}" height="{svg_h}" '
               f'fill="none" stroke="#333" stroke-width="1.5"/>')

    # Legenda / název
    out.append(f'  <text x="{svg_w//2}" y="{svg_h - 6}" '
               f'font-family="Arial,sans-serif" font-size="9" '
               f'text-anchor="middle" fill="#555">'
               f'Starý Plzenec · OpenStreetMap contributors · laser cut map</text>')

    out.append('</svg>')
    return '\n'.join(out)


def _way_points(way, nodes, xy_fn):
    pts = []
    for nid in way['nodes']:
        nd = nodes.get(nid)
        if nd:
            x, y = xy_fn(nd['lat'], nd['lon'])
            pts.append(f'{x:.2f},{y:.2f}')
    return ' '.join(pts)


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(out_dir, 'stary_plzenec.svg')

    print("=== Starý Plzenec – generátor SVG mapy ===")
    print(f"  Bbox: {BBOX}")

    xml_data = fetch_osm(BBOX)

    print("  Parsování OSM dat...")
    nodes, ways = parse_osm(xml_data)
    print(f"  Nalezeno: {len(nodes)} uzlů, {len(ways)} cest")

    hw_count = sum(1 for w in ways if 'highway' in w['tags'])
    water_count = sum(1 for w in ways if w['tags'].get('natural') == 'water'
                      or w['tags'].get('landuse') in ('reservoir', 'basin'))
    print(f"  Silnice: {hw_count}, vodní plochy: {water_count}")

    print("  Generuji SVG...")
    svg = make_svg(nodes, ways, BBOX, SVG_SIZE)

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(svg)

    size_kb = os.path.getsize(out_file) // 1024
    print(f"  Hotovo: {out_file} ({size_kb} kB)")
    print(f"  Rozměr SVG: {SVG_SIZE}x{SVG_SIZE} px (čtverec)")


if __name__ == '__main__':
    main()
