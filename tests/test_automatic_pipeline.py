"""Regression: only automatically validated manager publications may replace SCPI values."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import sync

ROOT=Path(__file__).resolve().parents[1]
ITEM={'id':'corum-origin','name':'CORUM Origin'}
P=sync.period_from('T3 2026')


class AutomaticPipelineTests(unittest.TestCase):
    def test_undated_pdf_link_on_dated_landing(self):
        html='<html><body><h1>SCPI CORUM Origin - bulletin T3 2026</h1><a href="/media/bulletin.pdf">Télécharger le PDF</a></body></html>'
        links=sync.pdf_links_on_landing(html,'https://www.corum.fr/bulletins/t3-2026',ITEM,'corum.fr',P)
        self.assertEqual(links,['https://www.corum.fr/media/bulletin.pdf'])

    def test_external_pdf_rejected(self):
        html='<a href="https://unrelated.com/malicious.pdf">Bulletin T3 2026 CORUM Origin</a>'
        self.assertEqual(sync.pdf_links_on_landing(html,'https://www.corum.fr/t3-2026',ITEM,'corum.fr',P),[])

    def test_old_pdf_not_selected_from_new_landing(self):
        html='<a href="/t2-2026.pdf">CORUM Origin Bulletin T2 2026</a><a href="/t3-2026.pdf">Bulletin CORUM Origin T3 2026</a>'
        urls=sync.pdf_links_on_landing(html,'https://www.corum.fr/docs',ITEM,'corum.fr',P)
        self.assertIn('https://www.corum.fr/t3-2026.pdf',urls)
        self.assertNotIn('https://www.corum.fr/t2-2026.pdf',urls)

    def test_verified_landing_follows_pdf_and_checks_identity(self):
        landing='https://www.corum.fr/actualites/bulletin-t3-2026'
        doc='https://www.corum.fr/media/bulletin.pdf'
        html=b'<h1>Bulletin CORUM Origin T3 2026</h1><a href="/media/bulletin.pdf">PDF du bulletin</a>'
        candidate={'url':landing,'period':P}
        with patch.object(sync,'fetch',side_effect=[
            (html,'text/html',landing),(b'%PDF-1.7 fake','application/pdf',doc)
        ]) as fetch_mock, patch.object(sync,'pdf_text',return_value='CORUM Origin - Bulletin T3 2026 - taux occupation financier'):
            result=sync.verified_pdf_from_candidate(None,candidate,ITEM,'corum.fr')
        self.assertEqual(result[2],doc)
        self.assertEqual(fetch_mock.call_count,2)

    def test_wrong_scpi_pdf_rejected(self):
        candidate={'url':'https://www.corum.fr/bulletin.pdf','period':P}
        with patch.object(sync,'fetch',return_value=(b'%PDF-1.7 fake','application/pdf',candidate['url'])), patch.object(sync,'pdf_text',return_value='SCPI Remake Live - Bulletin T3 2026'):
            self.assertIsNone(sync.verified_pdf_from_candidate(None,candidate,ITEM,'corum.fr'))

    def test_wrong_quarter_pdf_rejected(self):
        candidate={'url':'https://www.corum.fr/bulletin.pdf','period':P}
        with patch.object(sync,'fetch',return_value=(b'%PDF-1.7 fake','application/pdf',candidate['url'])), patch.object(sync,'pdf_text',return_value='SCPI CORUM Origin - Bulletin T2 2026'):
            self.assertIsNone(sync.verified_pdf_from_candidate(None,candidate,ITEM,'corum.fr'))

    def test_interface_has_no_manual_editing_controls(self):
        html=(ROOT/'index.html').read_text(encoding='utf-8')
        for forbidden in ('id="add-btn"', 'id="detail-edit"', 'id="detail-refresh"',
                          'id="import-btn"', 'id="preview-apply"', 'id="edit-form"',
                          'localOverrides[s.id]'):
            self.assertNotIn(forbidden,html,forbidden)
        self.assertIn('function exportCSV()',html)
        self.assertIn('function mergeOfficial(latest){return latest;}',html)


if __name__=='__main__':
    unittest.main()
