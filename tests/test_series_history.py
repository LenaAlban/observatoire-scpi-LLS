"""Séries chronologiques : observation datée, source et aucune interpolation."""
import sys
import unittest
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from series_history import sync_history,append_point,valid_day

class HistoricalSeriesTests(unittest.TestCase):
    def test_reconstitution_and_price_archives_keep_distinct_provenance(self):
        item={'price':200,'priceDate':'2026-09-30','previousPrice':190,'previousPriceDate':'2025-12-31',
          'previousPriceSource':'https://example.org/previous.pdf','priceSource':'https://example.org/price.pdf',
          'recon':210,'reconDate':'2026-06-30','fieldSources':{'recon':{'url':'https://example.org/recon2026.pdf'}},
          'history':[{'date':'2025-12-31','value':205},{'date':'2026-06-30','value':210}]}
        hist=sync_history(item)
        self.assertEqual(len(hist['recon']),2)
        self.assertIsNone(hist['recon'][0]['source'])
        self.assertEqual(hist['recon'][1]['source'],'https://example.org/recon2026.pdf')
        self.assertEqual(len(hist['price']),2)
        self.assertEqual(hist['price'][0]['source'],'https://example.org/previous.pdf')
        self.assertEqual(hist['price'][1]['source'],'https://example.org/price.pdf')
        self.assertEqual(len(sync_history(item)['recon']),2)

    def test_flows_stocks_and_td_observed_only(self):
        item={'tdHistory':{'2024':{'value':5.8,'source':'https://example.org/2024.pdf'},'2025':{'value':6.0,'source':'https://example.org/2025.pdf'}},
          'liquidityData':{'periodEnd':'2026-09-30','waitingParts':1000,'withdrawalsExecuted':30,
          'sourceUrl':'https://example.org/q3.pdf','withdrawals4Q':[{'periodEnd':'2026-06-30','parts':12},{'periodEnd':'2026-09-30','parts':30}]}}
        hist=sync_history(item)
        self.assertEqual([p['value'] for p in hist['td']],[5.8,6])
        self.assertEqual([p['value'] for p in hist['withdrawalsExecuted']],[12,30])
        self.assertIsNone(hist['withdrawalsExecuted'][0]['source'])
        self.assertEqual(hist['withdrawalsExecuted'][1]['source'],'https://example.org/q3.pdf')
        self.assertEqual(len(hist['waitingParts']),1)

    def test_conflicts_are_recorded_without_replacing_point(self):
        item={}
        self.assertTrue(append_point(item,'tof','2026-06-30',95,'https://example.org/t2.pdf'))
        self.assertFalse(append_point(item,'tof','2026-06-30',94,'https://example.org/t2-revised.pdf'))
        self.assertEqual(item['indicatorHistory']['tof'][0]['value'],95)
        self.assertEqual(len(item['historyConflicts']),1)
        self.assertFalse(append_point(item,'tof','2026-02-30',90,'https://example.org/invalid.pdf'))
        self.assertFalse(valid_day('2026-02-30'))

    def test_series_bounded_and_ordered(self):
        item={}
        for year in range(2010,2027):
            for month in (3,6,9,12):
                append_point(item,'recon',f'{year}-{month:02d}-28',100+year-2010,'https://example.org/r.pdf')
        vals=item['indicatorHistory']['recon']
        self.assertEqual(len(vals),48)
        self.assertEqual(vals,sorted(vals,key=lambda p:p['date']))

    def test_frontend_series_and_real_date_comparison(self):
        js=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const html=fs.readFileSync('index.html','utf8');
const records=JSON.parse(fs.readFileSync('data/scpi.json','utf8'));
const a=html.indexOf('function tdHistory(s){');
const b=html.indexOf('function compareSortedItems(){',a);
const start=html.indexOf('const HISTORY_METRICS=');
const end=html.indexOf('function renderSources(){',start);
assert.ok(a>=0&&b>a&&start>=0&&end>start);
const esc=v=>String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const fr=(v,d=2)=>Number(v).toLocaleString('fr-FR',{minimumFractionDigits:d,maximumFractionDigits:d});
const date=v=>String(v||'').slice(0,10);
const link=(url,label)=>/^https:\/\//.test(url||'')?'<a href="'+esc(url)+'">'+esc(label)+'</a>':'';
const empty=v=>'<p>'+esc(v)+'</p>';
const code=html.slice(a,b)+'\n'+html.slice(start,end);
const f=new Function('items','esc','fr','date','link','empty',code+'\nreturn {historicalSeries,historicalDelta,historicalPlot,historicalTable,tdHistory};');
const h=f(records,esc,fr,date,link,empty);
const iroko=records.find(s=>s.id==='iroko-zen');
const recon=h.historicalSeries(iroko,'recon');
assert.ok(recon.length>=2,'La valeur de reconstitution historique existante est disponible avant la collecte suivante');
assert.ok(recon.every((p,i)=>!i||p.date>=recon[i-1].date));
const delta=h.historicalDelta(recon,'recon');
assert.ok(delta.includes('du ')&&delta.includes(' au '));
assert.ok(h.historicalPlot([{name:iroko.name,points:recon}],'recon').includes('<svg'));
assert.ok(h.historicalTable([{name:iroko.name,points:recon}],'recon').includes('Source historique non identifiée'));
assert.equal(h.historicalPlot([{name:'Vide',points:[]}],'tof').includes('<svg'),false);
const custom={...iroko,indicatorHistory:{tof:[{date:'2026-03-31',value:95,source:'https://example.org/a.pdf'},{date:'2026-09-30',value:93,source:'https://example.org/c.pdf'}]}};
const tof=h.historicalSeries(custom,'tof');
const svg=h.historicalPlot([{name:'Test',points:tof}],'tof');
assert.ok(svg.includes(' M'),'Les trimestres absents produisent des segments disjoints');
assert.ok(!svg.includes(' L'),'Le trimestre manquant ne doit pas être traversé par une ligne');
const own={...iroko,indicatorHistory:{recon:[{date:'2025-12-31',value:201,source:'https://example.org/year2025.pdf'}]},history:[],recon:null,reconDate:null};
const other={...iroko,id:'other',name:'Autre',indicatorHistory:{recon:[{date:'2026-06-30',value:300,source:'https://example.org/2026.pdf'}]},history:[],recon:null,reconDate:null};
const i1=h.historicalSeries(own,'recon'),i2=h.historicalSeries(other,'recon');
assert.equal(i1.filter(p=>i2.some(x=>x.date===p.date)).length,0,'Ne pas simuler une date commune inexistante');
const line=h.historicalPlot([{name:'SCPI A',points:i1.map(x=>({...x,value:100}))},{name:'SCPI B',points:i2.map(x=>({...x,value:100}))}],'recon',true);
assert.ok(line.includes('base 100')||line.includes('indice 100'));
for(const id of ['history-scpi','history-metric','history-compare-add','history-compare-metric','history-compare-chart'])assert.ok(html.includes('id="'+id+'"'),id);
assert.ok(html.includes('data-history-open'));
console.log('Graphiques : dates, sources, données manquantes, et segments vérifiés.');
"""
        p=subprocess.run(['node','-e',js],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)

if __name__=='__main__':
    unittest.main()
