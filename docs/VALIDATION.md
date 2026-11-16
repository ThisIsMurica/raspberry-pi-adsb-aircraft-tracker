# Verification plan

## Offline tests

```bash
python3 -m compileall -q adsb_matrix.py adsb_roll.py adsb_lookup_cache.py
python3 -m unittest discover -s tests -v
```

The unit tests exercise aircraft/flight lookup parsing, local cache writing and synthetic example data. They do **not** simulate RF reception or physical matrix rendering.

## Hardware tests to document

| Area | Acceptance check | Evidence to collect |
| --- | --- | --- |
| 1090 MHz receive path | RTL-SDR and decoder receive real aircraft frames | dump1090 counters, antenna/SDR configuration |
| JSON feed | Aircraft entries update and stale targets disappear | Sample sanitized JSON and timing |
| RGB panel | 64 × 32 output, correct colors and readable labels | Photo/video and adapter identification |
| Aircraft selection | Candidate priority matches intended UI logic | Controlled test vectors |
| Route/telemetry views | View alternation and text positioning remain readable | Short matrix demonstration |
| Night brightness | Transition at Pi local 20:00/07:00 | Observed brightness settings |
| Logging | First occurrence per process run captured in CSV | Sanitized test capture |
| Optional lookups | Cache update, failures and staleness handling | Lookup statistics without personal data |
| Endurance | Multiple-hour run without decoder/matrix failures | CPU/RAM use and uptime |

## Known design constraints

- Aircraft selection is **metadata-priority**, not range-based or distance-based.
- The route cache is keyed to callsign, so future reuse of a callsign can make old routes misleading.
- `adsb_roll.py` logs first sightings for the current session, not every decoded RF frame.
- Backend RF demodulation and matrix GPIO timing are provided by the upstream projects rather than this Python layer.
