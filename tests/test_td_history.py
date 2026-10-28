"""TD SCPI : extraction annuelle, conservation de l'historique et cohérence des écrans."""
import copy
import datetime as dt
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from td_history import extract_annual_td, normalize_history, update_annual_td

SOURCE='https://www.corum.fr/docs/bulletin.pdf'

class AnnualTdTests(unittest.TestCase):
    def test_annual_explicit_and_mixed_years(self):
        txt='Taux de distribution 2025 : 6,50 %. Le taux de distribution 2024 : 6,00 %.'
        result=extract_annual_td(txt,'2026-10-29')
        self.assertEqual(result[2025]['value'],6.5)
        self.assertEqual(result[2024]['value'],6)
        self.assertEqual(len(result),2)

    def test_no_current_year_annual_before_year_end(self):
        self.assertEqual(extract_annual_td('Taux de distribution 2026 : 7,10 %','2026-10-29'),{})

    def test_new_year_becomes_available_next_year(self):
        self.assertEqual(extract_annual_td('Taux de distribution 2026 : 7,10 %','2027-01-10')[2026]['value'],7.1)

    def test_no_forecast_or_estimate(self):
        self.assertEqual(extract_annual_td('Prévision du taux de distribution 2025 : 7,10 %','2026-10-29'),{})
        self.assertEqual(extract_annual_td('Taux de distribution 2025 : 7,10 % provisoire','2026-10-29'),{})
        self.assertEqual(extract_annual_td('TOF 2025 96 %, taux de distribution prévisionnel 2026 de 8 %','2027-02-10'),{})

    def test_conflicting_values_not_taken(self):
        self.assertEqual(extract_annual_td('TD 2025 : 5,40 %. Taux de distribution 2025 : 6,10 %','2026-10-29'),{})

    def test_legacy_year_backfill_preserves_old_source(self):
        scpi={'td':6.5,'fieldSources':{'td':{'url':SOURCE,'method':'source 2025'}}}
        history=normalize_history(scpi)
        self.assertEqual(scpi['tdYear'],2025)
        self.assertEqual(history['2025']['value'],6.5)
        self.assertEqual(history['2025']['source'],SOURCE)
        self.assertEqual(len(history),1)

    def test_new_verified_year_preserves_older(self):
        scpi={'td':6.5,'tdYear':2025,'fieldSources':{'td':{'url':SOURCE}}}
        normalize_history(scpi)
        changes=[]
        def recorder(item,field,before,after,period,url):
            changes.append((field,before,after,period,url))
        result=update_annual_td(scpi,'Taux de distribution 2026 : 7,25 %',SOURCE,'2027-01-10',recorder)
        self.assertEqual(scpi['td'],7.25)
        self.assertEqual(scpi['tdYear'],2026)
        self.assertEqual(scpi['tdHistory']['2025']['value'],6.5)
        self.assertEqual(scpi['tdHistory']['2026']['value'],7.25)
        self.assertEqual(scpi['fieldSources']['td']['date'],'2026-12-31')
        self.assertTrue(any(c[0]=='td' for c in changes))
        self.assertIn('TD affiché actualisé',result)
        update_annual_td(scpi,'Taux de distribution 2025 : 5,90 %',SOURCE,'2027-01-11',recorder)
        self.assertEqual(scpi['td'],7.25)
        self.assertEqual(scpi['tdYear'],2026)
        self.assertEqual(len(scpi['tdConflicts']),1)

    def test_no_mix_in_allocation_and_report_pdf(self):
        js=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const html=fs.readFileSync('index.html','utf8');
const a=html.indexOf('function tdHistory(s){');
const b=html.indexOf('function compareSortedItems(){',a);
const x=html.indexOf('const allocationState=');
const y=html.indexOf('function renderSources(){',x);
assert.ok(a>=0&&b>a&&x>=0&&y>x);
const helpers=html.slice(a,b);
const engine=html.slice(x,y);
const catalogue=JSON.parse(fs.readFileSync('data/scpi.json','utf8'));
const old=catalogue.find(s=>s.id==='iroko-zen');
const another=catalogue.find(s=>s.id==='pierval-sante');
const newTD={...old,td:7.4,tdYear:2026,tdHistory:{
 '2025':{value:7.14,source:'https://www.iroko.eu/2025.pdf'},
 '2026':{value:7.4,source:'https://www.iroko.eu/2026.pdf'}}};
const older={...another,td:4.06,tdYear:2025,
 tdHistory:{'2025':{value:4.06,source:'https://www.euryale-am.fr/2025.pdf'}}};
const fr=(v,d=2)=>Number(v).toLocaleString('fr-FR',{minimumFractionDigits:d,maximumFractionDigits:d});
const inject=new Function('items','liquidityAssessment','watchAgeDays','fr','date',helpers+'\n'+engine+'\nreturn {tdLatest,tdForYear,tdYearForSelection,allocationCompute};');
const obj=inject([newTD,older],s=>({code:'regular',label:'Rythme observé',detail:'',period:'2026-09-30'}),()=>10,fr,x=>x);
assert.equal(obj.tdLatest(newTD).year,2026);
assert.equal(obj.tdYearForSelection([newTD,older]).year,2025);
assert.equal(obj.tdForYear(newTD,2025).value,7.14);
const res=obj.allocationCompute(100000,{'iroko-zen':50,'pierval-sante':50});
assert.equal(res.tdYear,2025);
assert.ok(Math.abs(res.td-5.6)<1e-8);
assert.ok(res.warnings.some(x=>x.includes('sans mélanger')||x.includes('Aucun mélange')));
const none={...older,td:null,tdHistory:{'2024':{value:5}}};
const obj2=inject([newTD,none],s=>({code:'regular',label:'Rythme observé',detail:'',period:'2026-09-30'}),()=>10,fr,x=>x);
const missing=obj2.allocationCompute(100000,{'iroko-zen':60,'pierval-sante':40});
assert.equal(missing.td,null);
assert.ok(missing.tdCoverage<100);
console.log('TD : années et agrégations cohérentes.');
"""
        result=subprocess.run(['node','-e',js],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)

if __name__=='__main__':
    unittest.main()
