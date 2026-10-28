import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'scripts'))
from sync import period_from,discover,host_is,metric_matches,single_consistent,match_identity,OFFICIAL,verified_key_table,extract_clean_breakdowns
class TestCollection(unittest.TestCase):
  def test_periods(self):
    for inp,expect in [('Bulletin Trimestriel T2 2026','2026-06-30'),('CORUM Origin - Fil d’Actualités 2026-T3.pdf','2026-09-30'),('Bulletin d’information semestriel S1 2026','2026-06-30'),('2ème trimestre 2026','2026-06-30'),('Bulletin Trimestriel 30/06/2026','2026-06-30')]:
      self.assertEqual((period_from(inp) or {}).get('date'),expect,inp)
  def test_security(self):
    self.assertTrue(host_is('https://www.sofidy.com/solutions/','sofidy.com'))
    self.assertFalse(host_is('http://sofidy.com/file.pdf','sofidy.com'))
    self.assertFalse(host_is('https://www.sofidy.com.evil.com/x','sofidy.com'))
  def test_singles(self):
    txt='VALEUR DE RECONSTITUTION au 30/06/2026 : 212,34 €\nTaux d’occupation financier 91,25 %'
    got=single_consistent(metric_matches(txt,'recon',20,5000),True)
    self.assertEqual(got['value'],212.34)
    self.assertEqual(got['date'],'2026-06-30')
  def test_bulletin_match(self):
    html='<html><body><h3>Bulletin Trimestriel - T2 2026</h3><div><a href="https://www.sofidy.com/wp-content/T2_2026_Immorente.pdf">Télécharger le bulletin</a></div></body></html>'
    got=discover(html,'https://www.sofidy.com/solutions/immorente/',{'id':'immorente','name':'Immorente'},'sofidy.com')
    self.assertEqual(got[0]['period']['label'],'T2 2026')
  def test_keys_complementarity(self):
    html='<table><tr><th>Durée</th><th>3 ans</th><th>5 ans</th><th>8 ans</th><th>10 ans</th></tr><tr><td>Valeur d’une part en nue-propriété en %</td><td>88,5 %</td><td>80 %</td><td>71.5 %</td><td>65 %</td></tr><tr><td>Valeur d’une part en usufruit en %</td><td>11,5 %</td><td>20 %</td><td>28.5 %</td><td>35 %</td></tr></table>'
    self.assertEqual(verified_key_table(html,'Example'),{'3':88.5,'5':80,'8':71.5,'10':65})
  def test_allocation_requires_publication_date(self):
    from bs4 import BeautifulSoup
    html='<h4>Répartition des biens</h4><h5>Par type de locaux</h5><ul><li>Bureaux (60%)</li><li>Commerces (30%)</li><li>Activités (10%)</li></ul>'
    item={'allocationDate':None,'officialSource':'https://test.example.com','types':[]}
    self.assertEqual(extract_clean_breakdowns(BeautifulSoup(html,'html.parser'),item),[])
  def test_all_catalogued(self):
    import json
    src=Path(__file__).resolve().parents[1]/'data'/'scpi.json'
    entries=json.loads(src.read_text())
    self.assertEqual(len(entries),31)
    self.assertEqual(set(OFFICIAL),{s['id'] for s in entries})
if __name__=='__main__':unittest.main()
