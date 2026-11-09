"""Keep official Sofidy T3 availability separate from PDF-verified indicators."""
import copy
import json
import sys
import unittest
import requests
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sync

SOFIDY = ("efimmo-1", "immorente", "sofidynamic", "sofidy-europe-invest")
ANNOUNCEMENT = "https://www.sofidy.com/actualites/scpi-sofidy-les-bulletins-trimestriels-du-3eme-trimestre-2026/"

class SofidyT3PublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {x["id"]:x for x in json.loads((ROOT/"data/scpi.json").read_text(encoding="utf-8"))}

    def test_t3_published_does_not_fake_t3_financial_figures(self):
        for identifier in SOFIDY:
            with self.subTest(scpi=identifier):
                s=self.rows[identifier]
                self.assertEqual(s["bulletin"], "T3 2026")
                self.assertEqual(s["bulletinDate"], "2026-09-30")
                self.assertEqual(s["bulletinUrl"], ANNOUNCEMENT)
                self.assertEqual(s["bulletinSourceType"], "publication_html")
                self.assertEqual(s["fieldSources"]["bulletin"]["url"], ANNOUNCEMENT)
                self.assertLessEqual(s["tofDate"], "2026-06-30")
                self.assertIn("PDF individuel non", s["bulletinNote"])

    def test_old_t2_pdf_cannot_downgrade_announced_t3(self):
        item=copy.deepcopy(self.rows["sofidynamic"])
        p=sync.period_from("T2 2026")
        candidate={"url":"https://www.sofidy.com/t2-2026.pdf","period":p,"score":1}
        with patch.object(sync,"collect_official_candidates",return_value=(None,None,[candidate],[])), \
             patch.object(sync,"verified_pdf_from_candidate",return_value=None), \
             patch.object(sync,"fetch",side_effect=requests.RequestException("offline")):
            with self.assertRaises(RuntimeError):
                sync.refresh_one(None,item)
        self.assertEqual(item["bulletin"],"T3 2026")
        self.assertEqual(item["bulletinDate"],"2026-09-30")
        self.assertEqual(item["bulletinUrl"],ANNOUNCEMENT)

    def test_verified_t3_pdf_replaces_announcement_not_period(self):
        item=copy.deepcopy(self.rows["sofidynamic"])
        pdf="https://www.sofidy.com/app/uploads/2026/11/sofidynamic-t3-test.pdf"
        p=sync.period_from("T3 2026")
        candidate={"url":pdf,"period":p,"score":1}
        with patch.object(sync,"collect_official_candidates",return_value=(None,None,[candidate],[{"status":"accessible","url":pdf}])), \
             patch.object(sync,"verified_pdf_from_candidate",return_value=(b"%PDF", "SOFIDYNAMIC Bulletin T3 2026",pdf)), \
             patch.object(sync,"update_indicators",return_value=[]), \
             patch.object(sync,"update_td",return_value=[]), \
             patch.object(sync,"update_liquidity",return_value=[]), \
             patch.object(sync,"update_pdf_allocations",return_value=[]), \
             patch.object(sync,"refresh_keys",return_value=[]):
            changes,verified=sync.refresh_one(None,item)
        self.assertTrue(verified)
        self.assertEqual(item["bulletin"],"T3 2026")
        self.assertEqual(item["bulletinUrl"],pdf)
        self.assertEqual(item["bulletinSourceType"],"pdf_verified")
        self.assertNotIn("bulletinNote",item)
        self.assertEqual(item["fieldSources"]["bulletin"]["url"],pdf)
        self.assertIn("bulletin",changes)

if __name__ == "__main__":
    unittest.main()
