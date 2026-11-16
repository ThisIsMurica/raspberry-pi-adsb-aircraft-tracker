import json
import tempfile
import unittest
from pathlib import Path

from adsb_lookup_cache import code, extract_route, first_value, load_json, save_json


class LookupTests(unittest.TestCase):
    def test_airport_codes(self):
        self.assertEqual(code({"icao_code": "KPHL"}), "PHL")
        self.assertEqual(code({"iata_code": "LHR"}), "LHR")
        self.assertEqual(code("EGLL"), "EGLL")

    def test_nested_route(self):
        result = {"response": {"flightroute": {
            "origin": {"icao_code": "KPHL"}, "destination": {"iata_code": "ATL"}
        }}}
        self.assertEqual(extract_route(result), "PHL-ATL")

    def test_fallback_route(self):
        self.assertEqual(extract_route({"response": {"origin_iata": "PHL", "destination_iata": "BOS"}}), "PHL-BOS")

    def test_type_lookup(self):
        self.assertEqual(first_value({"response": [{"aircraft": {"icao_type": "B738"}}]}, ("icao_type",)), "B738")

    def test_cache_read_write(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cache.json"
            self.assertEqual(load_json(path, {}), {})
            save_json(path, {"B": 2, "A": 1})
            self.assertEqual(load_json(path, {}), {"A": 1, "B": 2})
            self.assertFalse(path.with_suffix(".tmp").exists())

    def test_example_schema(self):
        root = Path(__file__).resolve().parents[1] / "examples"
        ac = json.loads((root / "aircraft.json").read_text())["aircraft"][0]
        typ = json.loads((root / "aircraft_types.json").read_text())
        routes = json.loads((root / "routes.json").read_text())
        self.assertIn(ac["hex"], typ)
        self.assertIn(ac["flight"], routes)


if __name__ == "__main__":
    unittest.main()
