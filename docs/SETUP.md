# Hardware and installation

## Receiver and decoder

The system uses an **RTL-SDR** and an appropriate **1090 MHz antenna** with **FlightAware dump1090-fa**. Install the decoder independently for your Raspberry Pi OS release and verify that `/run/dump1090-fa/aircraft.json` is updating. This project consumes decoder output; it does **not** demodulate 1090 MHz samples itself.

Upstream: https://github.com/flightaware/dump1090

## RGB display

`adsb_matrix.py` expects an installed `rgbmatrix` Python binding from Henner Zeller's Raspberry Pi RGB LED matrix project, with a 64 × 32 panel and `adafruit-hat` hardware mapping.

Upstream: https://github.com/hzeller/rpi-rgb-led-matrix

Follow the upstream hardware/adapter, power supply and binding-install instructions for the assembled hardware. The driver may need platform-specific privileges and cannot be expected to operate on a non-Pi computer.

Pillow is the only standard PyPI runtime dependency for the display application. The other Python scripts use standard-library modules.

```bash
python3 -m pip install -r requirements.txt
python3 -c 'from PIL import Image; print("Pillow available")'
python3 -c 'from rgbmatrix import RGBMatrix; print("RGBMatrix binding available")'
```

If the OS manages Python packages externally, use an appropriate virtual environment or OS package while making sure the matrix binding and Pillow are installed in the *same interpreter*.

## Startup

```bash
cd /path/to/raspberry-pi-adsb-aircraft-tracker
python3 adsb_roll.py       # terminal data display and local log
python3 adsb_matrix.py     # run separately for the LED panel
python3 adsb_lookup_cache.py  # run occasionally for optional metadata
```

Each script uses the default `/run/dump1090-fa/aircraft.json`. Override it with `ADSB_AIRCRAFT_JSON` if the local installation differs. Generated caches and logs are stored next to the scripts unless `ADSB_DATA_DIR` is set to a writable directory.

## Troubleshooting

- **NO AC:** No aircraft meet the 90-second recency threshold; check dump1090 JSON and RF reception.
- **`No module named rgbmatrix`:** Install the hardware-specific bindings for the active Python interpreter.
- **Panel flicker/wrong colors:** Confirm power, HUB75 connections, hardware mapping and driver configuration.
- **Very dim display:** Night mode sets brightness to **1** from **20:00–07:00** local time and scales image pixels further.
- **Missing routes:** Route metadata is optional, relies on an external lookup provider, and may be unavailable or stale.

A fully reproducible setup needs documented Pi model, OS, adapter, power, driver version and receiver configuration from the assembled unit.
