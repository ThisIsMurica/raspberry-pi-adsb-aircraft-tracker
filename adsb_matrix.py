#!/usr/bin/env python3

import json
import os
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions

AIRCRAFT_JSON = Path(os.environ.get("ADSB_AIRCRAFT_JSON", "/run/dump1090-fa/aircraft.json"))
AIRCRAFT_DB = Path(os.environ.get("ADSB_DATA_DIR", str(Path(__file__).resolve().parent))) / "aircraft_types.json"
ROUTE_DB = Path(os.environ.get("ADSB_DATA_DIR", str(Path(__file__).resolve().parent))) / "routes.json"

WIDTH = 64
HEIGHT = 32
DAY_BRIGHTNESS = 20
NIGHT_BRIGHTNESS = 1
NIGHT_START_HOUR = 20
NIGHT_END_HOUR = 7
BRIGHTNESS = DAY_BRIGHTNESS
NIGHT_COLOR_SCALE = 0.35  # 0.50 half brightness, 0.75 slight dim

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.brightness = BRIGHTNESS
options.hardware_mapping = "adafruit-hat"

matrix = RGBMatrix(options=options)
font = ImageFont.load_default()

def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default

def clean(v, default="---"):
    if v is None:
        return default
    v = str(v).strip()
    return v if v else default

def fmt_alt(v):
    if v is None:
        return "---"
    if str(v).lower() == "ground":
        return "GND"
    try:
        n = float(v)
        if n >= 1000:
            return f"{n/1000:.1f}k"
        return str(int(round(n)))
    except Exception:
        return clean(v)

def fmt_num(v):
    if v is None:
        return "---"
    try:
        return str(int(round(float(v))))
    except Exception:
        return clean(v)

def simplify_type(t):
    t = clean(t, "----").upper().replace("-", " ")

    if t in ("----", "---", ""):
        return "----"

    if len(t) <= 4 and any(c.isdigit() for c in t):
        return t

    if "737" in t:
        if "900" in t or "924" in t:
            return "B739"
        if "800" in t or "823" in t or "824" in t or "NG" in t:
            return "B738"
        if "700" in t:
            return "B737"
        return "B737"

    if "757" in t:
        return "B752"
    if "767" in t:
        return "B763"
    if "777" in t:
        return "B772"
    if "787" in t:
        return "B788"

    if "A319" in t:
        return "A319"
    if "A320" in t:
        return "A320"
    if "A321" in t:
        return "A321"
    if "A330" in t:
        return "A333"
    if "A350" in t:
        return "A359"

    if "E75" in t or "175" in t:
        return "E75L"
    if "CRJ" in t:
        return "CRJ"
    if "A36" in t or "BONANZA" in t:
        return "A36"

    return t[:4]

def get_ident(ac):
    flight = clean(ac.get("flight"), "")
    if flight:
        return flight.replace(" ", "").upper()
    return clean(ac.get("hex"), "NOID").upper()

def get_type(ac, type_db):
    for key in ("t", "type", "aircraft_type"):
        if ac.get(key):
            return simplify_type(ac.get(key))

    hx = clean(ac.get("hex"), "").upper()
    entry = type_db.get(hx) or type_db.get(hx.lower())

    if isinstance(entry, dict):
        return simplify_type(entry.get("type") or entry.get("t") or entry.get("icao_type"))
    if isinstance(entry, str):
        return simplify_type(entry)

    return "----"

def get_route(ident, route_db):
    ident = ident.replace(" ", "").upper()
    entry = route_db.get(ident)
    if isinstance(entry, dict):
        dep = clean(entry.get("dep") or entry.get("from"), "")
        arr = clean(entry.get("arr") or entry.get("to"), "")
        if dep and arr:
            return f"{dep}-{arr}".upper()
        return clean(entry.get("route"), "---").upper()
    if isinstance(entry, str):
        return entry.upper()
    return "---"

def choose_aircraft(aircraft, type_db, route_db):
    recent = [a for a in aircraft if a.get("seen", 999) < 90]

    def score(a):
        ident = get_ident(a)
        typ = get_type(a, type_db)
        route = get_route(ident, route_db)
        return (
            typ != "----",
            route != "---",
            bool(a.get("flight")),
            bool(a.get("alt_baro")),
            bool(a.get("gs")),
            a.get("messages", 0),
        )

    recent.sort(key=score, reverse=True)
    return recent[0] if recent else None

while True:
    hour = time.localtime().tm_hour
    if hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR:
        matrix.brightness = NIGHT_BRIGHTNESS
    else:
        matrix.brightness = DAY_BRIGHTNESS

    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        data = load_json(AIRCRAFT_JSON, {"aircraft": [], "messages": 0})
        type_db = load_json(AIRCRAFT_DB, {})
        route_db = load_json(ROUTE_DB, {})

        ac = choose_aircraft(data.get("aircraft", []), type_db, route_db)
        msg = data.get("messages", 0)

        if ac:
            ident = get_ident(ac)
            typ = get_type(ac, type_db)
            route = get_route(ident, route_db)
            alt = fmt_alt(ac.get("alt_baro"))
            spd = fmt_num(ac.get("gs"))
            trk = fmt_num(ac.get("track"))

            route_screen = route != "---" and int(time.time() / 4) % 2 == 1

            if route_screen:
                draw.text((0, 0), ident[:10], fill=(0, 255, 180), font=font)
                draw.text((0, 10), route[:10], fill=(255, 255, 255), font=font)
                draw.text((0, 20), f"{typ[:4]} {alt}"[:10], fill=(255, 180, 0), font=font)
            else:
                draw.text((0, 0), ident[:10], fill=(0, 255, 180), font=font)

                if typ != "----":
                    draw.text((0, 10), f"{typ[:4]} {alt}"[:10], fill=(255, 255, 255), font=font)
                elif route != "---":
                    draw.text((0, 10), route[:10], fill=(255, 255, 255), font=font)
                else:
                    draw.text((0, 10), f"ALT {alt}"[:10], fill=(255, 255, 255), font=font)

                draw.text((0, 20), f"SPD{spd}"[:7], fill=(0, 180, 255), font=font)
                if trk != "---":
                    draw.text((36, 20), f"T{trk}"[:5], fill=(255, 180, 0), font=font)
        else:
            draw.text((0, 0), "ADS-B", fill=(0, 255, 180), font=font)
            draw.text((0, 10), "NO AC", fill=(255, 0, 0), font=font)
            draw.text((0, 20), f"MSG {msg}", fill=(255, 255, 255), font=font)

    except Exception as e:
        draw.text((0, 0), "SCRIPT", fill=(255, 0, 0), font=font)
        draw.text((0, 10), "ERROR", fill=(255, 255, 255), font=font)

    # Extra night dimming after drawing the image
    if time.localtime().tm_hour >= NIGHT_START_HOUR or time.localtime().tm_hour < NIGHT_END_HOUR:
        img = img.point(lambda px: int(px * NIGHT_COLOR_SCALE))

    matrix.SetImage(img)
    time.sleep(1)
