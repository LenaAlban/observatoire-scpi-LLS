"""Tests de non-régression des messages de liquidité affichés dans le navigateur."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LiquidityUiTests(unittest.TestCase):
    def test_liquidity_messages_from_real_catalogue(self):
        # Utilise les vraies fonctions du site, et non une copie de leurs calculs.
        js = r"""
const fs = require('fs');
const assert = require('assert/strict');
const html = fs.readFileSync('index.html', 'utf8');
const start = html.indexOf('function liqNumbers(s){');
const end = html.indexOf('function liquidityView(s){', start);
assert.ok(start >= 0 && end > start, 'Fonctions de liquidité introuvables');
const slice = html.slice(start, end);
const {liquidityAssessment, liquidityMonthsSummary, formatLiquidityProjection} =
    new Function('fr', 'date', slice + '\nreturn {liquidityAssessment, liquidityMonthsSummary, formatLiquidityProjection};')(
       (value, digits=0) => Number(value).toLocaleString('fr-FR',{maximumFractionDigits:digits,minimumFractionDigits:digits}),
       value => value || 'Date non renseignée'
    );
const catalog = JSON.parse(fs.readFileSync('data/scpi.json','utf8'));
const byName = name => {const x=catalog.find(s=>s.name===name); assert.ok(x,name); return x;};
assert.equal(liquidityAssessment(byName('Ficommerce')).code, 'severe');
assert.equal(liquidityAssessment(byName('Épargne Foncière')).code, 'severe');
assert.equal(liquidityAssessment(byName('Pierval Santé')).code, 'high');
assert.equal(liquidityAssessment(byName('Remake Live')).code, 'clear');
assert.equal(liquidityAssessment(byName('Patrimmo Croissance')).code, 'market');
assert.equal(liquidityAssessment(byName('Iroko Zen')).code, 'unknown');
assert.equal(liquidityAssessment(byName('Épargne Pierre')).code, 'regular');
assert.ok(!liquidityMonthsSummary(byName('Ficommerce')).includes('6901'), 'Affichage d’un délai absurde');
assert.ok(!liquidityMonthsSummary(byName('Épargne Foncière')).includes('23460'), 'Affichage d’un délai absurde');
const pierval = byName('Pierval Santé');
const zeroFlow = {...pierval,liquidityData:{...pierval.liquidityData,withdrawalsExecuted:0}};
assert.equal(liquidityAssessment(zeroFlow).code, 'blocked');
for (const [months, phrase] of [[120,'> 10 ans'],[60,'> 5 ans'],[24,'> 2 ans'],[0,'Aucune file'],[1.5,'mois théoriques']]) {
    assert.ok(formatLiquidityProjection(months).includes(phrase), String(months) + ' mois');
}
assert.equal(formatLiquidityProjection(Infinity), 'Projection non calculable');
console.log('Scénarios de liquidité : 7 SCPI + limites validés.');
"""
        result = subprocess.run(
            ["node", "-e", js],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)


if __name__ == "__main__":
    unittest.main()
