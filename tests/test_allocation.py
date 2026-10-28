"""Tests de non-régression du simulateur d'allocation SCPI (moteur du site)."""
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class AllocationTests(unittest.TestCase):
    def test_real_allocation_logic_and_print(self):
        js=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const html=fs.readFileSync('index.html','utf8');
const records=JSON.parse(fs.readFileSync('data/scpi.json','utf8'));
function slice(start,end){
 const i=html.indexOf(start),j=html.indexOf(end,i+start.length);
 assert.ok(i>=0&&j>i,start+' -> '+end);
 return html.slice(i,j);
}
const get=(id)=>records.find(s=>s.id===id);
const date=v=>typeof v==='string'&&v.length===10?v.slice(8)+'/'+v.slice(5,7)+'/'+v.slice(0,4):'Non daté';
const fr=(v,d=2)=>Number(v).toLocaleString('fr-FR',{minimumFractionDigits:d,maximumFractionDigits:d});
const watchAgeDays=v=>v?Math.max(0,Math.floor((Date.now()-Date.parse(v+'T12:00:00Z'))/86400000)):null;
const es={};
const document={getElementById(id){return es[id]??(es[id]={value:'',innerHTML:'',textContent:'',className:'',disabled:false});}};
const esc=v=>String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const link=(url,label)=>/^https:\/\//.test(url||'')?'<a href="'+esc(url)+'">'+esc(label)+'</a>':'';
const euro=v=>v==null?'—':fr(v)+' €',pct=v=>v==null?'—':fr(v)+' %';
const empty=v=>esc(v);
let printed=0;
const window={print(){printed++;}};
const liqCode=String.raw; // avoids mocked risk formula: evaluate actual website functions
const liq=slice('function liqNumbers(s){','function liquidityView(s){');
const engine=slice('const allocationState=','function renderSources(){');
const env=new Function('items','document','window','watchAgeDays','date','fr','esc','link','pct','euro','empty','compareSortedItems','toast',
 liq+'\n'+engine+
 '\nreturn {allocationState,allocationCompute,allocationBuildBreakdown,allocationCanonicalGeo,allocationCanonicalSector,allocationEqualWeights,renderAllocation,renderAllocationResults,allocationAdd,printAllocationReport};');
const compareSortedItems=()=>records.slice().sort((a,b)=>a.name.localeCompare(b.name,'fr'));
const h=env(records,document,window,watchAgeDays,date,fr,esc,link,pct,euro,empty,compareSortedItems,()=>{});
const z=h.allocationCompute('100000',{'iroko-zen':50,'pierval-sante':50});
assert.ok(z.valid);
assert.equal(z.amount,100000);
assert.equal(z.positions.length,2);
assert.equal(z.positions[0].amount,50000);
assert.ok(Math.abs(z.td-5.6)<1e-8,'Pondération correcte du TD 2025');
assert.ok(Math.abs(z.geo.covered-100)<1e-8,'Géographie couverte');
assert.ok(Math.abs(z.types.covered-100)<1e-8,'Secteurs couverts');
assert.ok(Math.abs(z.geo.rows.reduce((t,x)=>t+x.percentage,0)-100)<1e-8,'Géographie totalise 100 %');
assert.ok(Math.abs(z.types.rows.reduce((t,x)=>t+x.percentage,0)-100)<1e-8,'Secteurs totalisent 100 %');
assert.ok(!z.geo.rows.some(x=>x.unclassified));
assert.equal(h.allocationCanonicalGeo('Île-de-France hors Paris'),'France');
assert.equal(h.allocationCanonicalGeo('Nord-Est'),'France');
assert.equal(h.allocationCanonicalGeo('Europe'),'Europe (zone non détaillée)');
assert.equal(h.allocationCanonicalSector('Bureaux'),'Bureaux');
assert.equal(h.allocationCanonicalSector('Commerce'),'Commerces');
assert.equal(h.allocationCanonicalSector('Santé, hôtellerie et autres'),'Santé, hôtellerie et autres');
assert.equal(h.allocationCanonicalSector('Logistique et activités'),'Logistique et activités');
const noTd=get('patrimmo-croissance'),withoutTd=h.allocationCompute(100000,{'iroko-zen':40,'patrimmo-croissance':60});
assert.equal(noTd.td,null);
assert.ok(Math.abs(withoutTd.tdCoverage-40)<1e-8);
assert.ok(withoutTd.warnings.some(x=>x.includes('TD 2025 manquant')));
assert.ok(!h.allocationCompute('100000',{'iroko-zen':80,'pierval-sante':30}).valid);
assert.ok(!h.allocationCompute('-10000',{'iroko-zen':100}).valid);
assert.ok(!h.allocationCompute('0',{'iroko-zen':100}).valid);
const weights=h.allocationEqualWeights(['iroko-zen','pierval-sante','corum-origin']);
assert.equal(Object.keys(weights).length,3);
assert.ok(Math.abs(Object.values(weights).reduce((a,b)=>a+b,0)-100)<1e-8);
assert.ok(h.allocationCompute(100000,weights).valid);
const fakeMissing={...get('pierval-sante'),geo:[],types:[],geoDate:null,typesDate:null};
const partial=h.allocationCompute(100000,{'iroko-zen':60,'pierval-sante':40},[get('iroko-zen'),fakeMissing]);
assert.ok(partial.valid);
assert.ok(Math.abs(partial.geo.covered-60)<1e-8);
assert.ok(partial.geo.rows.some(x=>x.unclassified&&Math.abs(x.percentage-40)<1e-8));
assert.ok(partial.warnings.some(x=>x.includes('non documentée')));
const secondary=h.allocationCompute(100000,{'lf-grand-paris-patrimoine':50,'pierval-sante':50});
assert.ok(secondary.valid);
assert.ok(secondary.liquidity.some(x=>x.code==='market'&&x.weight===50));
assert.ok(secondary.warnings.some(x=>x.includes('Marché par ordres')));
assert.ok(html.includes('id="allocation-add"'));
assert.ok(html.includes('id="allocation-total"'));
assert.ok(html.includes('id="allocation-print"'));
assert.ok(!html.includes('id="detail-edit"'));
h.allocationState.weights={'iroko-zen':50,'pierval-sante':50};
h.allocationState.amount='100000';
h.renderAllocation();
assert.ok(es['allocation-rows'].innerHTML.includes('data-alloc-weight'));
assert.ok(es['allocation-results'].innerHTML.includes('Répartition géographique consolidée'));
assert.ok(es['allocation-results'].innerHTML.includes('Exposition aux situations de liquidité'));
assert.ok(es['allocation-results'].innerHTML.includes('Sources et périodes par SCPI'));
assert.equal(es['allocation-print'].disabled,false);
h.printAllocationReport();
assert.equal(printed,1);
for(const term of ['Simulation d', 'Iroko Zen','Pierval Santé','Répartition géographique','Répartition sectorielle','TD historique 2025','Situations de liquidité','Publications et justificatifs','https://']){
 assert.ok(es['print-report'].innerHTML.includes(term),term);
}
h.allocationState.weights={'iroko-zen':65,'pierval-sante':50};
h.renderAllocationResults();
assert.equal(es['allocation-print'].disabled,true);
assert.ok(es['allocation-validation'].textContent.includes('100 % requis'));
assert.equal(printed,1);
console.log('Tests allocation : montants, TD partiel, géographie/secteurs, liquidité, PDF et invalidité OK');
"""
        result=subprocess.run(['node','-e',js],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)


if __name__=='__main__':
    unittest.main()
