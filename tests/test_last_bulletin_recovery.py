"""Rattrapage automatique des PDF non lus, conservant les périodes et les éditeurs."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import sync
from data_quality import approved_update_source
from official_sources import OFFICIAL, OFFICIAL_FALLBACKS

PERIAL_PDF=("https://cdn.prod.website-files.com/68d505281630e4a2223e1bee/"
            "6a7cda7ae845ffc70aa1350e_PERIAL%20Grand%20Paris%20-%20"
            "Bulletin%20trimestriel%20d%27information%20%28T2%202026%29.pdf")
PERIAL_O2=("https://cdn.prod.website-files.com/68d505281630e4a2223e1bee/"
           "6a7cda5d0727e6de700af0b9_PERIAL%20O%E2%82%82%20-%20"
           "Bulletin%20trimestriel%20d%27information%20%28T2%202026%29.pdf")

FAILING=['altixia-cadence-xii','edissimmo','efimmo-1','immorente',
         'pf-grand-paris','pfo2','rivoli-avenir-patrimoine','sofidynamic',
         'sofidy-europe-invest','principal-inside']


class LastBulletinTests(unittest.TestCase):
    def test_every_problem_fund_has_official_fallbacks(self):
        self.assertEqual(len(FAILING),10)
        self.assertTrue(all(OFFICIAL_FALLBACKS.get(id) for id in FAILING))
        for id in FAILING:
            url,host=OFFICIAL[id]
            item={'id':id,'sourceUrl':url,'fieldSources':{}}
            points=sync.official_entry_points(item,url,host)
            self.assertTrue(all(sync.host_is(link,host) for link in points),id)
            self.assertGreaterEqual(len(points),2,id)

    def test_efimmo_direct_t2_pdf_is_first_and_really_read(self):
        # Le lien transmis pour Efimmo doit être lu même si le catalogue
        # Sofidy ne répond pas (TLS/503). Son nom seul ne suffit pas.
        direct='https://www.sofidy.com/app/uploads/2026/07/Bulletin_Trimestriel_-_Efimmo_OPTI.pdf'
        item={'id':'efimmo-1','name':'Efimmo 1','sourceUrl':OFFICIAL['efimmo-1'][0],
              'fieldSources':{}}
        self.assertIn(direct,OFFICIAL_FALLBACKS['efimmo-1'])
        self.assertEqual(sync.official_entry_points(item,*OFFICIAL['efimmo-1'])[0],direct)
        content="EFIMMO 1 - Bulletin trimestriel d'information - 2e trimestre 2026"
        with patch.object(sync,'pdf_text',return_value=content) as pdf_reader:
            found=sync.pdf_candidate_from_bytes(b'%PDF-1.7 synthetic',direct,item)
        pdf_reader.assert_called_once()
        self.assertEqual(found['period']['label'],'T2 2026')
        self.assertEqual(found['url'],direct)

    def test_pdf_rejected_if_wrong_fund_or_not_a_bulletin(self):
        direct=OFFICIAL_FALLBACKS['efimmo-1'][0]
        item={'id':'efimmo-1','name':'Efimmo 1'}
        with patch.object(sync,'pdf_text',return_value="SOFIDYNAMIC - Bulletin trimestriel - T2 2026"):
            self.assertIsNone(sync.pdf_candidate_from_bytes(b'%PDF-mock',direct,item))
        with patch.object(sync,'pdf_text',return_value="EFIMMO 1 - Rapport annuel - T2 2026"):
            self.assertIsNone(sync.pdf_candidate_from_bytes(b'%PDF-mock',direct,item))

    def test_all_configured_direct_pdfs_are_prioritized_without_html(self):
        for identifier in FAILING:
            refs=[x for x in OFFICIAL_FALLBACKS[identifier]
                  if x.lower().split('?')[0].endswith('.pdf')]
            if not refs: continue
            item={'id':identifier,'name':identifier,
                  'sourceUrl':OFFICIAL[identifier][0],'fieldSources':{}}
            points=sync.official_entry_points(item,*OFFICIAL[identifier])
            self.assertEqual(points[:len(refs)*2:2],refs,id)

    def test_perial_cdn_is_allowed_only_for_own_documents(self):
        for id,url in [('pf-grand-paris',PERIAL_PDF),('pfo2',PERIAL_O2)]:
            self.assertIn(url,OFFICIAL_FALLBACKS[id])
            self.assertTrue(sync.host_is(url,'perial.com'))
            self.assertTrue(approved_update_source({'officialSource':'https://www.perial.com/scpi/perial-o2'},
                                                   'tof',url))
        self.assertFalse(sync.host_is('https://cdn.prod.website-files.com/other-site/unverified.pdf',
                                      'perial.com'))
        self.assertFalse(sync.host_is(PERIAL_PDF,'sofidy.com'))
        self.assertFalse(sync.host_is('http://cdn.prod.website-files.com/68d505281630e4a2223e1bee/doc.pdf','perial.com'))

    def test_principal_editor_cdn_authorization(self):
        url='https://brandassets.principal.com/asset/12345678-1234-1234-1234-123456789abc/Bulletin-d-information.pdf'
        self.assertTrue(sync.host_is(url,'principalam.com'))
        self.assertTrue(approved_update_source({'officialSource':'https://fr.principalam.com/notre-scpi'},'tof',url))
        self.assertFalse(sync.host_is('https://brandassets.principal.com/other/document.pdf','principalam.com'))

    def test_perial_downloaded_pdf_verified_by_identity_and_quarter(self):
        item={'id':'pf-grand-paris','name':'PF Grand Paris'}
        text='PERIAL GRAND PARIS - Bulletin trimestriel d’information - 2T 2026'
        with patch.object(sync,'pdf_text',return_value=text):
            c=sync.pdf_candidate_from_bytes(b'%PDF-1.7 synthetic',PERIAL_PDF,item)
        self.assertEqual(c['period']['date'],'2026-06-30')
        with patch.object(sync,'pdf_text',return_value=text.replace('GRAND PARIS','O2')):
            self.assertIsNone(sync.pdf_candidate_from_bytes(b'%PDF-1.7 synthetic',PERIAL_PDF,item))

    def test_semestrial_amundi_is_not_conflated_with_quarterly_report(self):
        text='Edissimmo Bulletin d’information 2nd semestre 2025. Période analysée : juillet à décembre'
        item={'id':'edissimmo','name':'Edissimmo'}
        self.assertEqual(sync.period_from(text)['label'],'S2 2025')
        with patch.object(sync,'pdf_text',return_value=text):
            pdf=sync.pdf_candidate_from_bytes(b'%PDF-1.7 synthetic',
                OFFICIAL_FALLBACKS['edissimmo'][-1],item)
        self.assertEqual(pdf['period']['periodType'],'S')
        self.assertNotEqual(pdf['period']['label'],'T2 2025')

    def test_perial_case_can_recover_from_html_page_pdf(self):
        item={'id':'pf-grand-paris','name':'PF Grand Paris'}
        page='https://www.perial.com/scpi/perial-grand-paris'
        html=('<html><a href="'+PERIAL_PDF+'">Bulletin trimestriel 2T 2026 '
              'PERIAL Grand Paris - Télécharger</a></html>')
        found=sync.discover(html,page,item,'perial.com')
        self.assertTrue(any(c['url']==PERIAL_PDF and c['period']['label']=='T2 2026'
                            for c in found))
        def downloader(session,url,host,limit=sync.MAX_HTML):
            if url==page:return html.encode(),'text/html',url
            if url==PERIAL_PDF:return b'%PDF-synthetic','application/pdf',url
            raise requests.exceptions.HTTPError('503')
        with patch.object(sync,'fetch',side_effect=downloader),patch.object(
            sync,'pdf_text',return_value='PERIAL Grand Paris - Bulletin trimestriel 2T 2026'):
            _,_,candidates,attempts=sync.collect_official_candidates(None,item,page,'perial.com')
        self.assertTrue(any(c['url']==PERIAL_PDF for c in candidates))

    def test_all_ten_funds_stay_in_status_even_after_recovery(self):
        import json
        statuses=json.loads((ROOT/'data/status.json').read_text())['results']
        ids={row['id'] for row in statuses}
        self.assertTrue(set(FAILING).issubset(ids))
        self.assertEqual(len(ids),len(statuses))

if __name__=='__main__':
    unittest.main()
