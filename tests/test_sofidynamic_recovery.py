"""Régression : le bulletin T2 2026 Sofidynamic doit être vérifié comme PDF."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import sync
from official_sources import OFFICIAL_FALLBACKS

DOC='https://www.sofidy.com/app/uploads/2026/07/Bulletin_Trimestriel_-_Sofidynamic_OPTI.pdf'
PAGE='https://www.sofidy.com/solutions/sofidynamic/'
ARTICLE='https://www.sofidy.com/actualites/scpi-sofidy-les-bulletins-trimestriels-du-2eme-trimestre-2026/'
TEXT="SOFIDYNAMIC SCPI DIVERSIFIÉE - Bulletin trimestriel d'information - 2ème TRIMESTRE 2026 N° 10"


def scpi():
    return {'id':'sofidynamic','name':'Sofidynamic','bulletin':'T2 2026',
            'bulletinDate':'2026-06-30','bulletinUrl':ARTICLE,
            'sourceUrl':PAGE,'fieldSources':{},'officialSource':PAGE}


class SofidynamicTests(unittest.TestCase):
    def test_exact_official_t2_pdf_and_apex_fallback(self):
        self.assertIn(DOC,OFFICIAL_FALLBACKS['sofidynamic'])
        urls=sync.official_entry_points(scpi(),PAGE,'sofidy.com')
        self.assertIn(DOC,urls)
        self.assertIn(DOC.replace('www.sofidy.com','sofidy.com'),urls)
        self.assertLess(urls.index(DOC),urls.index(ARTICLE))

    def test_content_must_prove_fund_and_quarter(self):
        with patch.object(sync,'pdf_text',return_value=TEXT):
            candidate=sync.pdf_candidate_from_bytes(b'%PDF-1.7 artificial',DOC,scpi())
        self.assertEqual(candidate['period']['label'],'T2 2026')
        self.assertEqual(candidate['period']['date'],'2026-06-30')
        with patch.object(sync,'pdf_text',return_value=TEXT.replace('SOFIDYNAMIC','IMMORENTE')):
            self.assertIsNone(sync.pdf_candidate_from_bytes(b'%PDF-1.7 artificial',DOC,scpi()))
        with patch.object(sync,'pdf_text',return_value=TEXT.replace('2ème TRIMESTRE','1er TRIMESTRE')):
            candidate=sync.pdf_candidate_from_bytes(b'%PDF-1.7 artificial',DOC,scpi())
        self.assertEqual(candidate['period']['label'],'T1 2026')

    def test_shared_news_page_never_assigns_other_funds_pdf(self):
        html="""
        <section><h3>Bulletin trimestriel T2 2026</h3>
          <a href="/app/uploads/2026/07/Bulletin_Trimestriel_-_Immorente.pdf">Télécharger le bulletin</a>
          <a href="/app/uploads/2026/07/Bulletin_Trimestriel_-_Sofidynamic_OPTI.pdf">Télécharger le bulletin</a>
          <a href="/app/uploads/2026/07/Bulletin_Trimestriel_-_Efimmo-1.pdf">Télécharger le bulletin</a>
        </section>
        """
        results=sync.discover(html,ARTICLE,scpi(),'sofidy.com')
        urls=[x['url'] for x in results]
        self.assertIn(DOC,urls)
        self.assertNotIn('https://www.sofidy.com/app/uploads/2026/07/Bulletin_Trimestriel_-_Immorente.pdf',urls)
        self.assertNotIn('https://www.sofidy.com/app/uploads/2026/07/Bulletin_Trimestriel_-_Efimmo-1.pdf',urls)

    def test_direct_document_recovery_after_www_ssl_failure(self):
        item=scpi()
        apex=DOC.replace('www.sofidy.com','sofidy.com')
        def fetch(session,url,host,limit=sync.MAX_HTML):
            if url.startswith('https://www.sofidy.com'):
                raise requests.exceptions.SSLError('certificate verify failed')
            if url==apex:return (b'%PDF-synthetic','application/pdf',apex)
            raise requests.exceptions.HTTPError('503')
        with patch.object(sync,'fetch',side_effect=fetch),patch.object(sync,'pdf_text',return_value=TEXT):
            html,_,candidates,attempts=sync.collect_official_candidates(None,item,PAGE,'sofidy.com')
        self.assertIsNone(html)
        self.assertTrue(any(x['url']==apex and x['period']['label']=='T2 2026' for x in candidates))
        self.assertTrue(any(x['status']=='pdf_verifie' for x in attempts))
        self.assertTrue(any(x.get('kind')=='tls' for x in attempts))
        self.assertFalse(any('certificate verify failed' in str(x) for x in attempts))

    def test_ssl_verified_apex_retry_on_real_pdf_candidate(self):
        item=scpi()
        apex=DOC.replace('www.sofidy.com','sofidy.com')
        requests_made=[]
        def getter(sess,url,host,limit=sync.MAX_HTML):
            requests_made.append(url)
            if url==DOC:
                raise requests.exceptions.SSLError('certificate verify failed')
            if url==apex:
                return (b'%PDF-synthetic','application/pdf',apex)
            raise ValueError('Unexpected request: '+url)
        candidate={'url':DOC,'period':sync.period_from('T2 2026')}
        with patch.object(sync,'fetch',side_effect=getter),patch.object(sync,'pdf_text',return_value=TEXT):
            pdf=sync.verified_pdf_from_candidate(None,candidate,item,'sofidy.com')
        self.assertEqual(requests_made,[DOC,apex])
        self.assertEqual(pdf[2],apex)
        self.assertEqual(pdf[1],TEXT)

    def test_pdf_with_no_period_is_not_reported_verified(self):
        item=scpi()
        candidate={'url':DOC,'period':sync.period_from('T2 2026')}
        with patch.object(sync,'fetch',return_value=(b'%PDF-synthetic','application/pdf',DOC)),patch.object(
                sync,'pdf_text',return_value='SOFIDYNAMIC Bulletin trimestriel, sans indication du trimestre'):
            self.assertIsNone(sync.verified_pdf_from_candidate(None,candidate,item,'sofidy.com'))

    def test_source_not_declared_validated_from_index_alone(self):
        item=scpi()
        with patch.object(sync,'pdf_text',return_value='SOFIDYNAMIC - Rapport annuel 2025'):
            self.assertIsNone(sync.pdf_candidate_from_bytes(b'%PDF-synthetic',DOC,item))
        with patch.object(sync,'pdf_text',return_value='SOFIDYNAMIC - Bulletin trimestriel 2ème TRIMESTRE 2026'):
            candidate=sync.pdf_candidate_from_bytes(b'%PDF-synthetic',DOC,item)
        self.assertIsNotNone(candidate)


if __name__=='__main__':
    unittest.main()
