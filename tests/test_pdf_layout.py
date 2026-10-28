"""Régression de l'extraction géométrique des graphiques SCPI."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "scripts"))
from pdf_layout import extract_pdf_allocations, fitz
from sync import update_pdf_allocations


@unittest.skipIf(fitz is None, "PyMuPDF non installé")
class TestPdfLayout(unittest.TestCase):
    def sample(self, good=True):
        doc=fitz.open()
        page=doc.new_page(width=595,height=842)
        def put(x,y,txt,sz=10):
            page.insert_text((x,y),txt,fontsize=sz)
        put(32,50,"SCPI CORUM Origin - Bulletin T3 2026")
        put(32,115,"Repartition typologique")  # Sans accents : simule un PDF exporté.
        groups=[("Bureau",60),("Commerce",24),("Hotellerie",8),("Logistique",4),("Sante",4)]
        for i,(sector,p) in enumerate(groups):
            x=35+i*107
            put(x,150,str(p))
            put(x+14,150,"%")
            put(x,180,sector)
        put(32,242,"Repartition geographique")
        countries=[("Pays-Bas",28),("Italie",17),("Irlande",12),("France",43)]
        for i,(name,value) in enumerate(countries):
            y=270+30*i
            put(34,y,name)
            put(405,y,str(value))
            put(425,y,"%")
        put(32,460,"Taux d'occupation")
        if not good:
            page.insert_text((32,420),"Données non vérifiées",fontsize=10)
        raw=doc.tobytes()
        doc.close()
        return raw

    def test_geo_and_types_vector_pdf(self):
        res=extract_pdf_allocations(self.sample())
        self.assertEqual(dict(res["geo"]["values"]),{"Pays-Bas":28,"Italie":17,"Irlande":12,"France":43})
        self.assertEqual(sum(v for _,v in res["types"]["values"]),100)
        self.assertEqual(res["types"]["page"],1)

    def test_retains_existing_newer_distribution(self):
        item={"geo":[["Pays-Bas",28],["Italie",17],["Irlande",12],["France",43]],
              "geoDate":"2026-09-30","types":[],"allocationDate":"2026-09-30"}
        old=item["geo"].copy()
        changes=update_pdf_allocations(item,self.sample(),{"date":"2026-06-30"},"https://www.corum.fr/official.pdf")
        self.assertNotIn("geo",changes)
        self.assertEqual(item["geo"],old)

    def test_preserve_data_on_no_chart(self):
        item={"geo":[["France",100]],"geoDate":"2026-09-30"}
        changes=update_pdf_allocations(item,b"non pdf",{"date":"2026-12-31"},"https://www.corum.fr/x")
        self.assertEqual(changes,[])
        self.assertEqual(item["geo"],[["France",100]])


if __name__=="__main__":
    unittest.main()
