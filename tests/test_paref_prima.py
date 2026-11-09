"""Contrôles documentaires de l'intégration de PAREF Prima."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from official_sources import OFFICIAL, OFFICIAL_FALLBACKS
from sync import host_is, official_entry_points, period_from

class ParefPrimaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entries = json.loads((ROOT / "data/scpi.json").read_text(encoding="utf-8"))
        cls.row = next(entry for entry in entries if entry["id"] == "paref-prima")

    def test_official_t3_bulletin_is_used(self):
        row = self.row
        self.assertEqual(row["bulletin"], "T3 2026")
        self.assertEqual(row["bulletinDate"], "2026-09-30")
        self.assertEqual(period_from(row["bulletin"])["date"], row["bulletinDate"])
        self.assertTrue(host_is(row["bulletinUrl"], OFFICIAL["paref-prima"][1]))
        self.assertIn(row["bulletinUrl"], OFFICIAL_FALLBACKS["paref-prima"])
        self.assertEqual(official_entry_points(row, *OFFICIAL["paref-prima"])[0], row["bulletinUrl"])

    def test_dated_allocation_and_liquidity(self):
        row = self.row
        self.assertAlmostEqual(sum(float(value) for _, value in row["geo"]), 100)
        self.assertAlmostEqual(sum(float(value) for _, value in row["types"]), 100)
        # Le graphique géographique du bulletin T3 s'appuie sur les expertises au T2.
        self.assertEqual(row["geoDate"], "2026-06-30")
        self.assertEqual(row["typesDate"], "2026-09-30")
        self.assertEqual(row["reconDate"], "2026-06-30")
        self.assertEqual(row["tofDate"], "2026-09-30")
        self.assertEqual(row["liquidityData"]["waitingParts"], 151028)
        for key in ("geo", "types", "recon", "tof"):
            self.assertEqual(row["fieldSources"][key]["url"], row["bulletinUrl"])

if __name__ == "__main__":
    unittest.main()
