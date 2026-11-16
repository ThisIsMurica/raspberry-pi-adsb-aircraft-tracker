# Dependencies and attribution

This repository contains the custom Python tracker and presentation scripts, **not** the upstream components themselves.

- **FlightAware dump1090-fa** — Mode S / ADS-B decoder: https://github.com/flightaware/dump1090 . The developer's local copy in the archive pointed to `edgeofspace/dump1090-fa` as its Git remote; users should install and update a trusted version separately.
- **Henner Zeller's rpi-rgb-led-matrix** — Raspberry Pi HUB75 LED driver and Python bindings: https://github.com/hzeller/rpi-rgb-led-matrix . Its upstream source includes GPL licensing notices.
- **Pillow** — Python image and text rendering: https://pillow.readthedocs.io/ .
- **ADSBdb** — Optional aircraft and flight route lookup service: https://www.adsbdb.com/ .

The original development archive contained source trees, compiled artifacts and nested `.git` directories for the first two projects. They are excluded here so the repository presents the original application code rather than a bundled third-party environment.

The custom application source does not yet have an explicit open-source license. This does not change upstream license obligations for any separately installed dependencies.
