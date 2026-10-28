"""Extraction prudente des répartitions dans les bulletins PDF des SCPI.

Lit les mots et leurs coordonnées (sans OCR). Un graphique en image seule
reste non exploitable et n'est pas transformé en valeurs fictives.
"""
from __future__ import annotations
import re
import unicodedata

try:
    import fitz
except ImportError:
    fitz = None


COUNTRIES = [
    "Pays-Bas", "Royaume-Uni", "Allemagne", "France", "Italie",
    "Irlande", "Espagne", "Finlande", "Belgique", "Lituanie",
    "Slovénie", "Portugal", "Estonie", "Lettonie", "Pologne",
    "République tchèque", "Autriche", "Canada", "États-Unis",
    "Norvège", "Suède", "Danemark", "Luxembourg", "Suisse",
    "Paris", "Île-de-France", "Île-de-France hors Paris",
    "Régions", "Régions françaises", "Province",
    "Grand Paris", "Région parisienne", "France hors Île-de-France",
    "Europe hors France", "France hors Paris", "Europe",
]
SECTORS = [
    "Bureau", "Bureaux", "Commerce", "Commerces", "Hôtellerie",
    "Hôtels", "Logistique", "Industriel & logistique",
    "Industrie et logistique", "Activité", "Activités", "Santé",
    "Éducation & loisirs", "Éducation et loisirs",
    "Éducation", "Santé et éducation", "Services",
    "Résidentiel", "Résidences services", "Soins",
    "Hôtel", "Entrepôts", "Locaux commerciaux",
    "Commerces périphériques", "Commerces de centre-ville",
    "Galeries commerciales",
]
SECTION_TITLES = {
    "geo": ["répartition géographique", "repartition geographique", "répartition par pays",
            "répartition par zones géographiques", "répartition géographique du patrimoine"],
    "types": ["répartition typologique", "repartition typologique", "répartition sectorielle",
              "répartition par typologie", "répartition par type de locaux"],
}
END_TITLES = [
    "taux d'occupation", "taux d’occupation", "taux d occupation",
    "locaux vacants", "évolution du patrimoine",
    "activité locative", "les acquisitions", "acquisitions du trimestre",
    "répartition géographique", "repartition geographique", "répartition typologique", "repartition typologique",
    "répartition sectorielle", "répartition par pays",
]
PERCENT = re.compile(r"^(?:100|\d{1,2})(?:[,.]\d{1,2})?%?$")


def normalize(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def rows_from_words(words):
    """Regroupe les mots dans des lignes géométriques en tolérant les graphiques."""
    rows = []
    for w in sorted(words, key=lambda w: ((w[1]+w[3])/2, w[0])):
        cx, cy = (w[0]+w[2])/2, (w[1]+w[3])/2
        match = next((row for row in rows if abs(row["y"]-cy) <= 2.9), None)
        if match is None:
            match = {"y":cy, "words":[]}
            rows.append(match)
        match["words"].append((str(w[4]), cx, cy))
    for row in rows:
        row["words"].sort(key=lambda w:w[1])
    return rows


def percentages(words):
    values = []
    for i,(token,x,y) in enumerate(words):
        value = token.strip().replace(" ","").replace(",",".")
        if not PERCENT.fullmatch(value):
            continue
        has_symbol = value.endswith("%")
        if not has_symbol:
            has_symbol = any(
                t.strip()=="%" and 0 <= nextx-x <= 23 and abs(nexty-y)<3.5
                for t,nextx,nexty in words[i+1:i+3]
            )
        if not has_symbol:
            continue
        try:
            p = float(value.rstrip("%"))
        except ValueError:
            continue
        if 0 < p <= 100:
            values.append((x,y,p))
    return values


def contains_heading(text, names):
    n=normalize(text)
    return any(normalize(label) in n for label in names)


def section_words(page, kind):
    if fitz is None:
        return None
    headings = SECTION_TITLES[kind]
    other = SECTION_TITLES["types" if kind=="geo" else "geo"]
    start = []
    for name in headings:
        start.extend(page.search_for(name))
    if not start:
        return None
    origin = min(start, key=lambda r:r.y0)
    end = []
    for name in END_TITLES + other:
        for r in page.search_for(name):
            if r.y0 > origin.y1+9:
                end.append(r.y0)
    bottom = min(end) if end else min(page.rect.height-18, origin.y0+350)
    if bottom-origin.y1 < 28:
        return None
    clip = fitz.Rect(0,origin.y1+1,page.rect.width,bottom-2)
    return page.get_text("words",clip=clip)


def label_candidate(row, labels, side="left"):
    entries = row["words"]
    ordered = sorted(labels,key=len,reverse=True)
    text = " ".join(w[0] for w in entries)
    norm = normalize(text)
    for label in ordered:
        n=normalize(label)
        if norm == n or norm.startswith(n+" "):
            matched_words=n.split()
            xs=[]
            for w,x,y in entries:
                if normalize(w) in matched_words:
                    xs.append(x)
            return label, (sum(xs)/len(xs) if xs else entries[0][1])
    return None


def parse_geo(words):
    rows=rows_from_words(words)
    output={}
    for row in rows:
        label=label_candidate(row,COUNTRIES)
        if label is None:
            continue
        name,cx=label
        match=[(x,v) for x,y,v in percentages(row["words"]) if x>cx-3]
        if len(match)!=1 or name in output:
            continue
        output[name]=match[0][1]
    if not (3 <= len(output) <= 35 and 97 <= sum(output.values()) <= 103):
        return None
    return [[k,v] for k,v in output.items()]


def sector_labels(words):
    """Trouve chaque libellé de secteur, même si plusieurs colonnes sont alignées."""
    labels=[]
    norm_words=[normalize(w[0]) for w in words]
    for sector in sorted(SECTORS,key=lambda s:len(normalize(s).split()),reverse=True):
        target=normalize(sector).split()
        for i in range(len(words)-len(target)+1):
            if norm_words[i:i+len(target)] != target:
                continue
            xs=[w[1] for w in words[i:i+len(target)]]
            ys=[w[2] for w in words[i:i+len(target)]]
            if max(ys)-min(ys)>7:
                continue
            labels.append((sector,sum(xs)/len(xs),sum(ys)/len(ys)))
    return labels


def parse_types(words):
    rows=rows_from_words(words)
    labels=[]
    marks=[]
    for row in rows:
        labels.extend(sector_labels(row["words"]))
        marks.extend(percentages(row["words"]))
    if not labels or not marks:
        return None
    pairs=[]
    used=set()
    for sector,x,y in labels:
        ranked=sorted(
            ((abs(mx-x)+abs(my-y)*0.2,idx,v) for idx,(mx,my,v) in enumerate(marks)
             if idx not in used and abs(mx-x)<85 and abs(my-y)<90),
            key=lambda a:a[0])
        if not ranked:
            continue
        score,idx,value=ranked[0]
        # La proportion doit être au voisinage direct du libellé.
        if score>89:
            continue
        if normalize(sector) in [normalize(k) for k,_ in pairs]:
            continue
        pairs.append((sector,value))
        used.add(idx)
    # Les catégories multi-mots ne doivent pas coexister avec une de leurs sous-catégories.
    if 3 <= len(pairs) <= 18 and 97 <= sum(x[1] for x in pairs) <= 103:
        return [[k,v] for k,v in pairs]
    return None


def extract_pdf_allocations(blob, max_pages=20):
    """Renvoie uniquement des répartitions complètes et cohérentes.

    Le résultat contient page et méthode d'extraction pour l'audit.
    Renvoie {} si le bulletin n'a pas de texte exploitable.
    """
    if fitz is None or not blob.startswith(b"%PDF"):
        return {}
    doc=fitz.open(stream=blob,filetype="pdf")
    try:
        found={}
        for index in range(min(len(doc),max_pages)):
            page=doc[index]
            for kind,func in (("geo",parse_geo),("types",parse_types)):
                if kind in found:
                    continue
                word_list=section_words(page,kind)
                if not word_list:
                    continue
                values=func(word_list)
                if values:
                    found[kind]={"values":values,"page":index+1,"method":"coordonnées PDF (texte vectoriel)"}
        return found
    finally:
        doc.close()
