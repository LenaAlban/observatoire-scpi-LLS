"""Tests d'extraction TD historique 2025 dans les bulletins PDF."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "scripts"))
from sync import update_td_2025, update_indicators


class TestDistribution(unittest.TestCase):
    def test_explicit_rate(self):
        item={"td":None}
        changes=update_td_2025(item,"Taux de distribution 2025 : 6,50 %", "https://www.example.com/source.pdf")
        self.assertEqual(changes,["TD 2025"])
        self.assertEqual(item["td"],6.5)
        self.assertEqual(item["tdYear"],2025)

    def test_gross_not_net(self):
        item={"td":None}
        sample="Votre SCPI a généré en 2025 un taux de distribution de 5,00 % brut de fiscalité et de 4,81 % net."
        update_td_2025(item,sample,"https://www.example.com/source.pdf")
        self.assertEqual(item["td"],5.0)

    def test_missing_year_not_assumed(self):
        item={"td":4.8,"tdYear":2025}
        update_td_2025(item,"Taux de distribution : 7,8 %", "https://www.example.com/source.pdf")
        self.assertEqual(item["td"],4.8)

    def test_conflicting_rates_not_written(self):
        item={"td":4.8,"tdYear":2025}
        update_td_2025(item,"Taux de distribution 2025 5,00 % / Taux de distribution 2025 5,90 %",
                       "https://www.example.com/source.pdf")
        self.assertEqual(item["td"],4.8)

    def test_tof_date_recorded(self):
        item={"tof":95.0,"tofDate":"2026-03-31"}
        txt="Taux d'occupation financier 95,00 %"
        period={"date":"2026-06-30"}
        changes=update_indicators(item,txt,period,"https://www.example.com/source.pdf")
        self.assertIn("tof",changes)
        self.assertEqual(item["tofDate"],"2026-06-30")


if __name__=="__main__":
    unittest.main()
