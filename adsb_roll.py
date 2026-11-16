#!/usr/bin/env python3

import json
import os
import time
from pathlib import Path
from datetime import datetime

AIRCRAFT_JSON = Path(os.environ.get("ADSB_AIRCRAFT_JSON", "/run/dump1090-fa/aircraft.json"))
LOG_FILE = Path(os.environ.get("ADSB_DATA_DIR", str(Path(__file__).resolve().parent))) / "captured_aircraft_log.csv"

seen_db = {}

def clean(v, default="---"):
    if v is None:
        return default
    v = str(v).strip()
    return v if v else default

def fmt_age(seconds):
    if seconds is None:
        return "---"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds//60}m{seconds%60:02d}s"

if not LOG_FILE.exists():
    LOG_FILE.write_text("time,hex,flight,alt_baro,gs,track,rssi,messages\n")

while True:
    try:
        data = json.loads(AIRCRAFT_JSON.read_text())
        total_messages = data.get("messages", 0)
        aircraft = data.get("aircraft", [])
        now_local = datetime.now().strftime("%H:%M:%S")

        for a in aircraft:
            hexid = clean(a.get("hex"), "").upper()
            if not hexid:
                continue

            old = seen_db.get(hexid, {})
            first_seen_time = old.get("first_seen_time", now_local)

            record = {
                "hex": hexid,
                "flight": clean(a.get("flight"), old.get("flight", "")),
                "alt": clean(a.get("alt_baro"), old.get("alt", "")),
                "gs": clean(a.get("gs"), old.get("gs", "")),
                "track": clean(a.get("track"), old.get("track", "")),
                "rssi": clean(a.get("rssi"), old.get("rssi", "")),
                "messages": a.get("messages", old.get("messages", 0)),
                "seen": a.get("seen", 999),
                "first_seen_time": first_seen_time,
                "last_seen_time": now_local,
            }

            if hexid not in seen_db:
                with LOG_FILE.open("a") as f:
                    f.write(
                        f"{now_local},{hexid},{record['flight']},{record['alt']},"
                        f"{record['gs']},{record['track']},{record['rssi']},{record['messages']}\n"
                    )

            seen_db[hexid] = record

        current = [r for r in seen_db.values() if r.get("seen", 999) < 90]
        current.sort(key=lambda r: r.get("messages", 0), reverse=True)

        all_seen = list(seen_db.values())
        all_seen.sort(key=lambda r: r.get("last_seen_time", ""), reverse=True)

        print("\033[2J\033[H", end="")
        print("ADS-B ROLLING CAPTURE")
        print("=" * 80)
        print(f"Time: {now_local} | Total dump1090 messages: {total_messages}")
        print(f"Currently recent: {len(current)} | Captured this run: {len(seen_db)}")
        print(f"Log file: {LOG_FILE}")
        print("=" * 80)

        print("RECENT AIRCRAFT")
        print(f"{'HEX':<8} {'FLIGHT':<10} {'ALT':>7} {'GS':>7} {'TRK':>7} {'RSSI':>8} {'AGE':>8}")
        print("-" * 80)

        if current:
            for r in current[:12]:
                print(
                    f"{r['hex']:<8} "
                    f"{r['flight']:<10} "
                    f"{r['alt']:>7} "
                    f"{r['gs']:>7} "
                    f"{r['track']:>7} "
                    f"{r['rssi']:>8} "
                    f"{fmt_age(r.get('seen')):>8}"
                )
        else:
            print("No recent aircraft yet. If messages increase, the receiver is hearing packets.")

        print()
        print("LAST CAPTURED")
        print(f"{'HEX':<8} {'FLIGHT':<10} {'ALT':>7} {'GS':>7} {'FIRST':>8} {'LAST':>8}")
        print("-" * 80)

        for r in all_seen[:10]:
            print(
                f"{r['hex']:<8} "
                f"{r['flight']:<10} "
                f"{r['alt']:>7} "
                f"{r['gs']:>7} "
                f"{r['first_seen_time']:>8} "
                f"{r['last_seen_time']:>8}"
            )

        time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopped.")
        break
    except Exception as e:
        print("\033[2J\033[H", end="")
        print("ADS-B rolling tracker waiting for data...")
        print(f"Error: {e}")
        time.sleep(2)
