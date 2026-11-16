# Data and privacy

The receiver uses aircraft broadcasts decoded by dump1090-fa. Route/type lookups come from an optional third-party API and can be stale or absent.

**Locally generated files (not committed):** `aircraft_types.json`, `routes.json`, and `captured_aircraft_log.csv`. These can reveal the aircraft observed at a specific receiving location/time and contain externally supplied annotations. The `examples/` files are synthetic and demonstrate only the input schema.

- The `adsb_roll.py` log records each distinct ICAO code when first observed during a run.
- The lookup cache is keyed by ICAO aircraft hex and by flight callsign; it does not have a fixed expiry.
- The display should not be treated as a verified source for operational air traffic decisions.
