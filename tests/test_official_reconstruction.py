import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'scripts'))
from sync import update_manager_page_recon,OFFICIAL

class OfficialReconstitutionTest(unittest.TestCase):
 def test_own_manager_page(self):
  item={'id':'epargne-pierre-europe','name':'Épargne Pierre Europe','recon':None,'reconDate':None,'history':[]}
  html='<h3>Valeur de reconstitution au 01/07/2026</h3><p>20,54 €</p>'
  changed=update_manager_page_recon(item,html,OFFICIAL['epargne-pierre-europe'][0]);self.assertTrue(changed)
  self.assertEqual(item['recon'],20.54);self.assertEqual(item['reconDate'],'2026-07-01')
 def test_external_manager_rejected(self):
  item={'id':'epargne-pierre-europe','name':'Épargne Pierre Europe','recon':None,'reconDate':None}
  self.assertEqual(update_manager_page_recon(item,'Valeur de reconstitution au 01/07/2026 20,54 €','https://placement.meilleurtaux.com/x'),[])
 def test_without_date_rejected(self):
  item={'id':'epargne-pierre-europe','name':'Épargne Pierre Europe','recon':None,'reconDate':None}
  self.assertEqual(update_manager_page_recon(item,'Valeur de reconstitution : 20,54 €',OFFICIAL['epargne-pierre-europe'][0]),[])
 def test_prior_date_rejected(self):
  item={'id':'epargne-pierre-europe','name':'Épargne Pierre Europe','recon':23,'reconDate':'2026-10-01'}
  self.assertEqual(update_manager_page_recon(item,'Valeur de reconstitution au 01/07/2026 20,54 €',OFFICIAL['epargne-pierre-europe'][0]),[])
