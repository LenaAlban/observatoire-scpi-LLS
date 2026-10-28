"""Non-regression du comparateur SCPI et de son rapport PDF."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ComparatorTests(unittest.TestCase):
    def test_real_catalogue_comparison_and_pdf(self):
        js=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const html=fs.readFileSync('index.html','utf8'),all=JSON.parse(fs.readFileSync('data/scpi.json','utf8'));
function slice(a,b){let i=html.indexOf(a),j=html.indexOf(b,i+a.length);assert.ok(i>=0&&j>i,a);return html.slice(i,j);}
const helpers=slice('const $=id=>','let syncStatus=');
const selection=slice('function compareSortedItems(){','function auditChecks(');
const details=slice('function compareCellHtml(','function watchAgeDays(');
const els={};
const document={getElementById(id){return els[id]??(els[id]={innerHTML:'',textContent:'',disabled:false});}};
let printCalls=0;
const window={print(){printCalls++;}};
const bars=data=>data.map(x=>x[0]+' : '+x[1]+'%').join(' / ');
const liqNumbers=s=>{const d=s.liquidityData||{},secondary=s.priceType?.includes('Marché secondaire')||s.liquidity?.label?.includes('suspendu');return {d,w:d.waitingParts,v:d.withdrawalsExecuted,secondary:!!secondary,valid:!!d.periodEnd&&d.withdrawalsExecuted!=null};};
const liquidityAssessment=s=>({label:liqNumbers(s).secondary?'Marché par ordres':'Retrait classique',period:s.liquidityData?.periodEnd||'Non daté',detail:'Mode de sortie à confirmer'});
const make=new Function('items','selected','document','window','bars','liqNumbers','liquidityAssessment','toast',helpers+'\n'+selection+'\n'+details+'\nreturn {compareSelectedItems,compareSortedItems,renderCompare,compareGroups,compareAllocationTop,compareGapLabel,compareKeyYears,compareKeyTableHtml,compareTableHtml,renderCompareExtras,printReport,comparePortfolioCard};');
const chosen=['iroko-zen','lf-grand-paris-patrimoine','corum-origin','ficommerce'];
const h=make(all,chosen,document,window,bars,liqNumbers,liquidityAssessment,()=>{});
const find=id=>all.find(s=>s.id===id);
assert.equal(h.compareSelectedItems().length,4);
assert.ok(h.compareSortedItems().slice(0,3).every(s=>(s.tags||[]).includes('Meilleurtaux Placement')),'Meilleurtaux doit être affiché en premier');
const ir=find('iroko-zen'),lf=find('lf-grand-paris-patrimoine');
assert.equal(h.compareGapLabel(lf),'Non comparable','Aucune décote sur marché secondaire');
assert.ok(h.compareGapLabel(ir).startsWith('Décote de'),'Décote explicitée sans signe ambigu');
assert.ok(h.compareAllocationTop(ir,'geo').includes('France :'));
const years=h.compareKeyYears([ir,lf]);
assert.ok(years.includes(10));
const keys=h.compareKeyTableHtml([ir,lf]);
assert.ok(keys.includes('65,50 %'),'Clé Iroko à 10 ans');
assert.ok(keys.includes('Durée non publiée'),'Absence de barème non interpolée');
h.renderCompare();
assert.ok(els['compare-selected'].innerHTML.includes('data-compare-remove'));
assert.ok(els['compare-choices'].innerHTML.includes('disabled'),'Ne pas pouvoir ajouter une cinquième SCPI');
assert.ok(els['compare-counter'].textContent.includes('4 / 4'));
h.renderCompareExtras();
const matrix=els['compare-matrix'].innerHTML;
for(const label of ['Prix de référence','Valeur de retrait','Taux de distribution 2025','TOF','Liquidité','Principales zones géographiques','Principaux secteurs','Nue-propriété']){
 assert.ok(matrix.includes(label),label);
}
assert.ok(matrix.includes('Reconstitution'),'Sources individuelles');
assert.ok(matrix.includes('https://'),'Références documentaires dans le comparatif');
assert.ok(matrix.includes('Non comparable'),'Prix secondaire non utilisé pour une décote');
assert.ok(els['compare-cards'].innerHTML.includes('Répartition géographique complète'));
assert.ok(els['compare-cards'].innerHTML.includes('Répartition sectorielle complète'));
const before=printCalls;
h.printReport(chosen);
assert.equal(printCalls,before+1,'L’impression doit être déclenchée');
const report=els['print-report'].innerHTML;
assert.ok(report.includes('Clés indicatives'));
assert.ok(report.includes('France'));
assert.ok(report.includes('Source :'));
assert.ok(report.includes('65,50 %'));
assert.ok(report.includes('Non comparable'));
assert.ok(html.includes('id="compare-search"'));
assert.ok(html.includes('id="compare-clear"'));
assert.ok(html.includes('data-compare-add'));
assert.ok(!html.includes('id="detail-edit"'));
console.log('Comparateur : sélection, prix secondaires, répartitions, NP, sources et PDF vérifiés.');
"""
        result=subprocess.run(['node','-e',js],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)


if __name__=='__main__':
    unittest.main()
