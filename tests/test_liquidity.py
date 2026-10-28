"""Tests de calcul des données disponibles et d'abstention de l'extracteur."""
import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sync import extract_liquidity_counts,update_liquidity
class TestLiquidity(unittest.TestCase):
 def test_strict_same_line(self):
  s='''Nombre de parts en attente de retrait : 15 000
Parts vendues sur le trimestre (retraits) : 3 000
Demandes de retrait enregistrées : 2 500'''
  self.assertEqual(extract_liquidity_counts(s),{'waitingParts':15000,'withdrawalsExecuted':3000,'withdrawalRequests':2500})
 def test_do_not_pick_columns(self):
  s='''Parts vendues sur le trimestre (retraits) | 2e trimestre 2025 4 000 | 3e trimestre 2025 3 000
Nombre de parts en attente de retrait | 13 000 | 15 000'''
  self.assertEqual(extract_liquidity_counts(s),{'waitingParts':None,'withdrawalsExecuted':None,'withdrawalRequests':None})
 def test_zero_and_missing(self):
  d=extract_liquidity_counts('Parts en attente de retrait : 0\nNombre de retraits exécutés au cours du trimestre : 0')
  self.assertEqual(d['waitingParts'],0)
  self.assertEqual(d['withdrawalsExecuted'],0)
 def test_period_pair_never_mixed(self):
  scpi={'id':'test','name':'Test','liquidityData':{'periodEnd':'2026-03-31','waitingParts':15000,'withdrawalsExecuted':3000,'withdrawals4Q':[{'periodEnd':'2026-03-31','parts':3000}]}}
  period={'date':'2026-06-30','label':'T2 2026','periodType':'T'}
  changes=update_liquidity(scpi,'Parts en attente de retrait : 12 000',period,'https://official.example/bulletin.pdf')
  self.assertIn('liquidité / retraits',changes)
  self.assertEqual(scpi['liquidityData']['waitingParts'],12000)
  self.assertIsNone(scpi['liquidityData']['withdrawalsExecuted'])
  self.assertEqual(scpi['liquidityData']['withdrawals4Q'],[{'periodEnd':'2026-03-31','parts':3000}])
 def test_add_four_quarters(self):
  item={'name':'Test'}
  p={'periodType':'T'}
  for date,vol in [('2025-12-31',3000),('2026-03-31',2000),('2026-06-30',4000),('2026-09-30',3000)]:
   p['date']=date;p['label']=date
   update_liquidity(item,f'Parts en attente de retrait : 15 000\nParts retirées sur le trimestre : {vol}',p,'https://official.example/p.pdf')
  self.assertEqual(len(item['liquidityData']['withdrawals4Q']),4)
  self.assertEqual(sum(x['parts'] for x in item['liquidityData']['withdrawals4Q']),12000)
  self.assertEqual(15000/3000*3,15)
if __name__=='__main__': unittest.main()
