"""Non-régression : cas de collecte Sofidy / Amundi / Altixia remontés en agence."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import sync
from official_sources import OFFICIAL_FALLBACKS

class OfficialRecoveryTests(unittest.TestCase):
    def test_amundi_alternates_and_https(self):
        item={'id':'edissimmo','name':'Edissimmo','sourceUrl':'https://www.amundi-immobilier.com/Local-content/Producsheet/SCPI/EDISSIMMO/Documents',
              'fieldSources':{'geo':{'url':'https://www.amundi-immobilier.com/ezjscore/call/api-document'}}}
        url=item['sourceUrl']
        routes=sync.official_entry_points(item,url,'amundi-immobilier.com')
        self.assertEqual(routes[0],url)
        self.assertIn('https://www.amundi-immobilier.com/Local-content/Producsheet/SCPI/EDISSIMMO/L-essentiel',routes)
        self.assertIn('https://www.amundi-immobilier.com/ezjscore/call/api-document',routes)
        self.assertTrue(all(sync.host_is(x,'amundi-immobilier.com') for x in routes))

    def test_sofidy_alternates_and_apex_domain(self):
        item={'id':'immorente','name':'Immorente','sourceUrl':'https://www.sofidy.com/solutions/immorente/'}
        paths=sync.official_entry_points(item,item['sourceUrl'],'sofidy.com')
        self.assertEqual(paths[1],'https://sofidy.com/solutions/immorente/')
        self.assertIn('https://www.sofidy.com/actualites/scpi-sofidy-les-bulletins-trimestriels-du-2eme-trimestre-2026/',paths)
        self.assertIn('https://www.sofidy.com/documentation/',paths)

    def test_altixia_old_pdf_is_detectable_without_page_link(self):
        item={'id':'altixia-cadence-xii','name':'Altixia Cadence XII',
              'sourceUrl':'https://www.altixia.fr/scpi-cadence.php'}
        url='https://www.altixia.fr/medias/documentations/doc1-20260430-122013.pdf'
        self.assertIn(url,sync.official_entry_points(item,item['sourceUrl'],'altixia.fr'))
        fake_text='ALTIXIA CADENCE XII - BULLETIN TRIMESTRIEL - 1er TRIMESTRE 2026'
        with patch.object(sync,'pdf_text',return_value=fake_text):
            candidate=sync.pdf_candidate_from_bytes(b'%PDF-synthetic',url,item)
        self.assertEqual(candidate['period']['label'],'T1 2026')
        self.assertEqual(candidate['url'],url)

    def test_pdf_without_matching_scpi_or_report_is_rejected(self):
        item={'id':'altixia-cadence-xii','name':'Altixia Cadence XII'}
        url=OFFICIAL_FALLBACKS['altixia-cadence-xii'][-1]
        for text in ('Edissimmo BULLETIN TRIMESTRIEL T1 2026',
                     'ALTIXIA CADENCE XII RAPPORT ANNUEL 2025',
                     'ALTIXIA CADENCE XII BULLETIN TRIMESTRIEL sans date'):
            with self.subTest(text=text), patch.object(sync,'pdf_text',return_value=text):
                self.assertIsNone(sync.pdf_candidate_from_bytes(b'%PDF-synthetic',url,item))

    def test_source_error_is_human_readable_with_https_preserved(self):
        for exc,kind in (
            (requests.exceptions.SSLError("CERTIFICATE_VERIFY_FAILED"),'tls'),
            (requests.exceptions.HTTPError("503 Server Error"),'http_503'),
            (requests.exceptions.Timeout("Timed out"),'timeout'),
        ):
            message,found=sync.sanitized_collection_error(exc)
            self.assertEqual(found,kind)
            self.assertNotIn('HTTPSConnectionPool',message)
            self.assertIn('Données précédentes',message)
        with patch.object(sync,'fetch',side_effect=requests.exceptions.SSLError("CERTIFICATE_VERIFY_FAILED")):
            item={'id':'efimmo-1','name':'Efimmo 1','sourceUrl':'https://www.sofidy.com/solutions/efimmo1/'}
            with self.assertRaisesRegex(RuntimeError,'sources de secours'):
                sync.collect_official_candidates(None,item,item['sourceUrl'],'sofidy.com')
            self.assertTrue(item.get('sourceAttempts'))
            self.assertTrue(all(row.get('kind')=='tls' for row in item['sourceAttempts']))
            self.assertTrue(all('CERTIFICATE_VERIFY_FAILED' not in row.get('detail','') for row in item['sourceAttempts']))

    def test_recovery_from_primary_503_uses_proven_pdf(self):
        item={'id':'altixia-cadence-xii','name':'Altixia Cadence XII',
              'sourceUrl':'https://www.altixia.fr/scpi-cadence.php'}
        url='https://www.altixia.fr/medias/documentations/doc1-20260430-122013.pdf'
        def fake_fetch(sess,target,host,limit=sync.MAX_HTML):
            if target==url:return b'%PDF-synthetic','application/pdf',url
            raise requests.exceptions.HTTPError('503 Server Error')
        with patch.object(sync,'fetch',side_effect=fake_fetch), patch.object(
            sync,'pdf_text',return_value='ALTIXIA CADENCE XII - BULLETIN TRIMESTRIEL 1er TRIMESTRE 2026'
        ):
            page,final,candidates,attempts=sync.collect_official_candidates(None,item,item['sourceUrl'],'altixia.fr')
        self.assertIsNone(page)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]['period']['label'],'T1 2026')
        self.assertTrue(any(a['status']=='pdf_verifie' for a in attempts))

    def test_frontend_never_displays_raw_network_error(self):
        import subprocess
        js=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const html=fs.readFileSync('index.html','utf8');
const start=html.indexOf('function collectionIssueText(');
const end=html.indexOf('function renderWatch(){',start);
assert.ok(start>=0&&end>start);
const code=html.slice(start,end);
const h=new Function('items','date',code+'\nreturn collectionIssueText;')([],x=>x);
const old=JSON.parse(fs.readFileSync('data/status.json','utf8'));
const errors=old.results.filter(x=>x.status==='error');
for(const status of errors){
 const msg=h(status);
 assert.ok(msg.length<180,msg);
 assert.ok(!/HTTPSConnectionPool|SSLCertVerificationError|Max retries exceeded|for url:/.test(msg),msg);
}
assert.ok(h({status:'partial',message:'Site accessible · bulletin non détecté automatiquement'}).includes('aucun nouveau bulletin'));
console.log('Messages techniques anciens neutralisés dans l’interface.');
"""
        result=subprocess.run(['node','-e',js],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr+'\n'+result.stdout)

if __name__=='__main__':
    unittest.main()
