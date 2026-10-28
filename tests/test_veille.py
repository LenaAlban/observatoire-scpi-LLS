"""Tests du journal de veille automatique et des seuils d'actualité."""
import sys
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import sync


class VeilleTests(unittest.TestCase):
    def test_event_recorded_only_when_value_changes(self):
        item={}
        sync.record_auto_change(item,'tof',90.5,91.5,'2026-09-30','https://www.corum.fr/test.pdf')
        self.assertEqual(len(item['automatedHistory']),1)
        self.assertEqual(item['automatedHistory'][0]['previous'],90.5)
        self.assertEqual(item['automatedHistory'][0]['value'],91.5)
        self.assertEqual(item['automatedHistory'][0]['period'],'2026-09-30')
        self.assertEqual(item['automatedHistory'][0]['source'],'https://www.corum.fr/test.pdf')
        sync.record_auto_change(item,'tof',91.5,91.5,'2026-09-30','https://www.corum.fr/test.pdf')
        self.assertEqual(len(item['automatedHistory']),1)

    def test_event_history_bounded(self):
        item={}
        for i in range(160):
            sync.record_auto_change(item,'tof',i,i+1,'2026-09-30','https://www.corum.fr/test.pdf')
        self.assertEqual(len(item['automatedHistory']),120)
        self.assertEqual(item['automatedHistory'][0]['previous'],40)

    def test_veille_ui_uses_actual_catalogue_and_journal(self):
        script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const html=fs.readFileSync('index.html','utf8');
const begin=html.indexOf('function watchAgeDays(');
const end=html.indexOf('function renderSources(){',begin);
assert.ok(begin>0 && end>begin,'fonctions de veille présentes');
const code=html.slice(begin,end);
const catalogue=JSON.parse(fs.readFileSync('data/scpi.json','utf8'));
const status=JSON.parse(fs.readFileSync('data/status.json','utf8'));
const fr=(v,d=0)=>Number(v).toLocaleString('fr-FR',{minimumFractionDigits:d,maximumFractionDigits:d});
const fn=new Function('items','syncStatus','fr', code+'\nreturn {watchData,watchAgeDays,watchFormatValue};');
let {watchData,watchAgeDays,watchFormatValue}=fn(catalogue,status,fr);
assert.equal(watchData().errors.length,(status.results||[]).filter(x=>x.status==='partial'||x.status==='error').length);
assert.ok(watchData().old.length>0,'des dates historiques sont bien signalées');
assert.equal(watchAgeDays('pas une date'),null);
assert.ok(watchFormatValue('tof',91.7).includes('%'));
assert.ok(watchFormatValue('keys',{'5':80,'10':60}).includes('10 ans'));
const event={
  field:'bulletin',previous:'T2 2026',value:'T3 2026',period:'2026-09-30',
  recordedAt:new Date().toISOString(),source:'https://www.corum.fr/docs/2026.pdf',
  scpiId:'corum-origin',scpiName:'CORUM Origin'
};
const withEvent=fn(catalogue,{...status,recentEvents:[event]},fr).watchData();
assert.equal(withEvent.changes.filter(x=>x.field==='bulletin').length,1);
assert.equal(withEvent.changes[0].previous,'T2 2026');
assert.equal(withEvent.changes[0].source,event.source);
const duplicate=fn(catalogue,{...status,recentEvents:[event,event]},fr).watchData();
assert.equal(duplicate.changes.filter(x=>x.field==='bulletin').length,1);
console.log('Veille : dates, erreurs, événements, dédoublonnage et détails vérifiés.');
"""
        proc=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout+'\n'+proc.stderr)


if __name__=='__main__':
    unittest.main()
