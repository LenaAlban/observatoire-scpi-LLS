"""Tests des contrôles automatiques non destructifs et des voies officielles de secours."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import sync
from data_quality import (audit_scpi,quality_report,validate_updates,
                          valid_allocation,valid_keys,approved_update_source)

BASE='https://www.corum.fr/nos-scpi/corum-origin/documents'
DOC='https://www.corum.fr/docs/bulletin-t3-2026.pdf'


def specimen():
    return {'id':'corum-origin','name':'CORUM Origin','officialSource':BASE,
            'sourceUrl':BASE,'bulletin':'T2 2026','bulletinDate':'2026-06-30',
            'bulletinUrl':'https://www.corum.fr/bulletin-t2-2026.pdf',
            'recon':200,'reconDate':'2026-06-30',
            'price':220,'priceType':'Souscription','priceDate':'2026-06-30',
            'tof':95,'tofDate':'2026-06-30','td':6,'tdYear':2025,
            'geo':[['France',60],['Allemagne',40]],'geoDate':'2026-06-30',
            'types':[['Bureaux',60],['Commerces',40]],'typesDate':'2026-06-30',
            'fieldSources':{k:{'url':DOC,'date':'2026-06-30'} for k in ('recon','price','tof','geo','types','td')},
            'keys':{'5':80,'10':65},'keySource':DOC,'keyDate':'2026-06-30',
            'liquidityData':{'waitingParts':10,'withdrawalsExecuted':2,'periodEnd':'2026-06-30','sourceUrl':DOC}}


class QualityTests(unittest.TestCase):
    def test_valid_latest_changes(self):
        before=specimen()
        after=copy.deepcopy(before)
        after['recon']=210
        after['reconDate']='2026-09-30'
        after['fieldSources']['recon']['date']='2026-09-30'
        self.assertEqual(validate_updates(before,after,'2026-10-29'),[])

    def test_invalid_future_and_price(self):
        before=specimen()
        after=copy.deepcopy(before)
        after['price']=9000
        after['priceDate']='2026-12-31'
        text=';'.join(validate_updates(before,after,'2026-10-29'))
        self.assertIn('date de référence future',text)
        self.assertIn('hors plage',text)

    def test_no_regression_of_reference_date(self):
        before=specimen()
        after=copy.deepcopy(before)
        after['recon']=180
        after['reconDate']='2026-03-31'
        self.assertIn('régression',str(validate_updates(before,after,'2026-10-29')))

    def test_domain_mismatch_blocks_update(self):
        before=specimen()
        after=copy.deepcopy(before)
        after['tof']=88
        after['fieldSources']['tof']['url']='https://random-finance.fr/not-official.pdf'
        self.assertIn('hors domaine',str(validate_updates(before,after,'2026-10-29')))
        self.assertFalse(approved_update_source(after,'tof','https://random-finance.fr/not-official.pdf'))
        self.assertTrue(approved_update_source(after,'tof',DOC))

    def test_bad_ventilation_not_published(self):
        before=specimen()
        after=copy.deepcopy(before)
        after['geo']=[['France',80],['Allemagne',10]]
        after['geoDate']='2026-09-30'
        self.assertFalse(valid_allocation(after['geo']))
        self.assertIn('incomplète',str(validate_updates(before,after,'2026-10-29')))

    def test_bad_keys_not_published(self):
        before=specimen()
        after=copy.deepcopy(before)
        after['keys']={'5':65,'10':80}
        self.assertFalse(valid_keys(after['keys']))
        self.assertIn('non monotone',str(validate_updates(before,after,'2026-10-29')))

    def test_bad_liquidity_counts_not_published(self):
        before=specimen()
        after=copy.deepcopy(before)
        after['liquidityData']['waitingParts']=-5
        self.assertIn('nombre de parts invalide',str(validate_updates(before,after,'2026-10-29')))

    def test_missing_historical_date_is_warning_not_blocker(self):
        before=specimen()
        before['keyDate']=None
        before['keySource']=None
        after=copy.deepcopy(before)
        after['tof']=94
        self.assertEqual(validate_updates(before,after,'2026-10-29'),[])
        issues=audit_scpi(before,'2026-10-29')
        self.assertTrue(any(x['field']=='keys' and x['kind']=='date_absente' for x in issues))
        self.assertTrue(any(x['field']=='keys' and x['kind']=='source_absente' for x in issues))

    def test_quality_report_has_dates_and_sources_without_guessing(self):
        row=specimen()
        report=quality_report([row],'2026-10-29')
        self.assertEqual(report['asOf'],'2026-10-29')
        self.assertEqual(report['affectedScpi'],0)
        self.assertEqual(report['issueCounts']['source_absente'],0)
        row['geoDate']='2025-01-01'
        report=quality_report([row],'2026-10-29')
        self.assertGreater(report['issueCounts']['ancienne'],0)

    def test_undocumented_liquidity_is_not_marked_as_inconsistent(self):
        row=specimen()
        row['liquidityData']={'waitingParts':None,'withdrawalsExecuted':None,'periodEnd':None}
        self.assertFalse(any(x['field']=='liquidityData' for x in audit_scpi(row,'2026-10-29')))

    def test_official_fallbacks_only_same_manager_domain(self):
        row=specimen()
        row['sourceUrl']='https://www.corum.fr/notre-scpi/corum-origin'
        row['fieldSources']['tof']['url']='https://thirdparty.example/bulletin.pdf'
        urls=sync.official_entry_points(row,BASE,'corum.fr')
        self.assertEqual(urls[0],BASE)
        self.assertIn(row['sourceUrl'],urls)
        self.assertTrue(all(sync.host_is(u,'corum.fr') for u in urls))
        self.assertNotIn('https://thirdparty.example/bulletin.pdf',urls)

    def test_recovery_from_unreachable_primary_uses_verified_canonical_domain(self):
        row=specimen()
        row['sourceUrl']='https://www.corum.fr/une-autre-page'
        html=b'<html><a href="/docs/bulletin-t3-2026.pdf">CORUM Origin : Bulletin T3 2026</a></html>'
        def fake_fetch(sess,url,host,limit=sync.MAX_HTML):
            if url==BASE:
                raise requests.exceptions.HTTPError('503 publisher')
            if url==row['sourceUrl']:
                return html,'text/html',url
            raise ValueError(url)
        with patch.object(sync,'fetch',side_effect=fake_fetch):
            text,url,candidates,attempts=sync.collect_official_candidates(None,row,BASE,'corum.fr')
        self.assertEqual(url,row['sourceUrl'])
        self.assertEqual(candidates[0]['period']['label'],'T3 2026')
        self.assertEqual(attempts[0]['status'],'error')
        self.assertEqual(attempts[1]['status'],'accessible')

    def test_old_landing_cannot_be_used_as_verified_pdf(self):
        row=specimen()
        row['sourceUrl']='https://www.corum.fr/une-autre-page'
        html=b'<a href="/documents/reponse.pdf">CORUM Origin : Bulletin T2 2026</a>'
        def fake_fetch(sess,url,host,limit=sync.MAX_HTML):
            if url==BASE:
                return html,'text/html',url
            raise ValueError(url)
        with patch.object(sync,'fetch',side_effect=fake_fetch):
            _,_,candidates,_=sync.collect_official_candidates(None,row,BASE,'corum.fr')
        self.assertTrue(all(candidate['period']['label']=='T2 2026' for candidate in candidates))


if __name__=='__main__':
    unittest.main()
