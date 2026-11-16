#!/usr/bin/env python3

import json
import os
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

AIRCRAFT_JSON = Path(os.environ.get("ADSB_AIRCRAFT_JSON", "/run/dump1090-fa/aircraft.json"))
TYPE_DB = Path(os.environ.get("ADSB_DATA_DIR", str(Path(__file__).resolve().parent))) / "aircraft_types.json"
ROUTE_DB = Path(os.environ.get("ADSB_DATA_DIR", str(Path(__file__).resolve().parent))) / "routes.json"

BASE = "https://api.adsbdb.com/v0"

def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default

def save_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
    tmp.replace(path)

def fetch_json(url):
    req = Request(url, headers={"User-Agent": "adsb-matrix/1.0"})
    with urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))

def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)

def first_value(obj, keys):
    keys = set(keys)
    for d in walk(obj):
        for k, v in d.items():
            if k in keys and v not in (None, "", [], {}):
                return v
    return None

def code(x):
    if isinstance(x, dict):
        for k in ("iata_code", "iata", "icao_code", "icao", "airport_iata", "airport_icao"):
            if x.get(k):
                s = str(x[k]).upper()
                return s[1:] if len(s) == 4 and s.startswith("K") else s
    elif isinstance(x, str):
        s = x.upper()
        return s[1:] if len(s) == 4 and s.startswith("K") else s
    return None

def extract_route(data):
    # Common shape: response -> flightroute -> origin/destination
    for d in walk(data):
        if "origin" in d and "destination" in d:
            dep = code(d.get("origin"))
            arr = code(d.get("destination"))
            if dep and arr:
                return f"{dep}-{arr}"

    dep = first_value(data, ("origin_iata", "departure_iata", "dep_iata", "from_iata"))
    arr = first_value(data, ("destination_iata", "arrival_iata", "arr_iata", "to_iata"))
    if dep and arr:
        return f"{code(dep)}-{code(arr)}"

    return None

def main():
    live = load_json(AIRCRAFT_JSON, {"aircraft": []})
    type_db = load_json(TYPE_DB, {})
    route_db = load_json(ROUTE_DB, {})

    updated_types = 0
    updated_routes = 0

    aircraft = live.get("aircraft", [])
    recent = [a for a in aircraft if a.get("seen", 999) < 300]

    for ac in recent:
        hx = str(ac.get("hex", "")).strip().upper()
        ident = str(ac.get("flight", "")).strip().replace(" ", "").upper()

        if hx and hx not in type_db:
            try:
                url = f"{BASE}/aircraft/{quote(hx)}"
                if ident:
                    url += f"?callsign={quote(ident)}"
                data = fetch_json(url)

                icao_type = first_value(data, ("icao_type", "aircraft_type", "type"))
                reg = first_value(data, ("registration", "reg"))

                if icao_type:
                    type_db[hx] = {
                        "type": str(icao_type).upper(),
                        "reg": str(reg).upper() if reg else ""
                    }
                    updated_types += 1
                    print(f"TYPE {hx}: {type_db[hx]}")
            except Exception as e:
                print(f"TYPE lookup failed {hx}: {e}")

            time.sleep(0.25)

        if ident and ident not in route_db:
            try:
                data = fetch_json(f"{BASE}/callsign/{quote(ident)}")
                route = extract_route(data)
                if route:
                    route_db[ident] = route
                    updated_routes += 1
                    print(f"ROUTE {ident}: {route}")
            except Exception as e:
                print(f"ROUTE lookup failed {ident}: {e}")

            time.sleep(0.25)

    save_json(TYPE_DB, type_db)
    save_json(ROUTE_DB, route_db)

    print(f"Done. Types updated: {updated_types}, routes updated: {updated_routes}")

if __name__ == "__main__":
    main()
