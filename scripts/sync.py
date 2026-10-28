#!/usr/bin/env python3
"""Collecte quotidienne SCPI. Données ambiguës conservées, pas d'invention.

Dépendances installées dans GitHub Actions. L'exécution réseau n'est pas effectuée
lors de la construction initiale de l'archive.
"""
from __future__ import annotations
import argparse, datetime as dt, io, json, logging, re, sys, unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
try:
    import fitz
except ImportError:
    fitz = None
from official_sources import ALIASES, LIQUIDITY, OFFICIAL

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'scpi.json'
STATUS = ROOT / 'data' / 'status.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; SCPI-Observatoire/1.0; patrimonial-research; public-information-only)'}
MAX_HTML = 3_000_000
MAX_PDF = 16_000_000
TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()
LOG = logging.getLogger('scpi-sync')


def fold(s):
    s = ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s).strip().lower()


def host_is(url, expected):
    try:
        u = urlparse(url)
        hostname = (u.hostname or '').lower()
        return u.scheme == 'https' and (hostname == expected or hostname.endswith('.'+expected))
    except ValueError:
        return False


def session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def fetch(s, url, host, limit=MAX_HTML):
    if not host_is(url, host):
        raise ValueError('URL hors domaine éditeur autorisé : ' + url)
    with s.get(url, timeout=(8, 23), allow_redirects=True, stream=True) as res:
        res.raise_for_status()
        if not host_is(res.url, host):
            raise ValueError('Redirection hors domaine éditeur : ' + res.url)
        size = 0
        chunks = []
        for chunk in res.iter_content(65_536):
            size += len(chunk)
            if size > limit:
                raise ValueError('Document trop volumineux')
            chunks.append(chunk)
        return b''.join(chunks), res.headers.get('Content-Type', ''), res.url


def period_from(text):
    """Return period info only if a bulletin period is explicit in the input."""
    txt = fold(text).replace('–','-').replace('_',' ').replace('’', "'")
    patterns = [
        r'\b(?:t|q|trimestre\s*|trim\s*)([1-4])\s*[- /]*\s*(20\d\d)\b',
        r'\b(20\d\d)\s*[- /]*\s*(?:t|q|trim)\s*([1-4])\b',
        r'\b([1-4])\s*(?:er|e|eme|ieme)?\s*trimestre\s*(20\d\d)\b',
        r'\b([1-4])(?:er|e|eme|ieme)?\s*trim\.?\s*(20\d\d)\b',
        r'\b([1-4])\s*t\s*(20\d\d)\b',
    ]
    for idx, pattern in enumerate(patterns):
        m = re.search(pattern, txt, re.I)
        if m:
            y, q = (int(m.group(1)),int(m.group(2))) if idx==1 else (int(m.group(2)),int(m.group(1)))
            if 2023 <= y <= 2035:
                return {'label':f'T{q} {y}', 'date':f'{y}-{q*3:02d}-{(31 if q in [1,4] else 30):02d}', 'rank':y*4+q, 'periodType':'T'}
    sm = re.search(r'\b(?:s|semestre\s*)([12])\s*[- /]*\s*(20\d\d)\b', txt)
    if not sm:
        sm = re.search(r'\b([12])\s*(?:er|e|eme|ieme)?\s*semestre\s*(20\d\d)\b', txt)
    if sm:
        half,y = int(sm.group(1)),int(sm.group(2))
        if 2023 <= y <= 2035:
            return {'label':f'S{half} {y}','date':f'{y}-{"06-30" if half==1 else "12-31"}','rank':y*4+(2 if half==1 else 4),'periodType':'S'}
    # Reporting explicitly date-tagged, only if bulletin/reporting appears before a date
    m = re.search(r'\b(?:bulletin|reporting|fil d.actualites)\b.{0,75}?\b(31/03|30/06|30/09|31/12)/(20\d\d)\b', txt)
    if m:
        d,y=m.group(1),int(m.group(2)); q={'31/03':1,'30/06':2,'30/09':3,'31/12':4}[d]
        return {'label':f'T{q} {y}','date':f'{y}-{q*3:02d}-{(31 if q in (1,4) else 30):02d}','rank':y*4+q,'periodType':'T'}
    return None


def existing_rank(item):
    label = (item.get('bulletin') or '')
    p = period_from(label)
    return p['rank'] if p else 0


def local_context(anchor):
    fragments = [anchor.get_text(' ',strip=True), anchor.get('title',''), anchor.get('aria-label',''), anchor.get('href','')]
    parent = anchor.parent
    for _ in range(3):
        if parent is None: break
        t = parent.get_text(' ',strip=True)
        if len(t) <= 500:
            fragments.append(t)
        parent=parent.parent
    # headings just before the link
    for x in anchor.find_all_previous(['h2','h3','h4','h5','h6','strong'],limit=3):
        txt=x.get_text(' ',strip=True)
        if len(txt)<180: fragments.append(txt)
    return ' '.join(dict.fromkeys(fragments))


def discover(html, base_url, scpi, host):
    soup=BeautifulSoup(html,'html.parser')
    name=fold(scpi['name'])
    aliases=[name]+[fold(v) for v in ALIASES.get(scpi['id'],[])]
    shared=any(x in base_url for x in ['/bt','/documentation/']) and any(x in base_url for x in ('la-francaise','atland-voisin'))
    candidates=[]
    for a in soup.find_all('a',href=True):
        href=urljoin(base_url,a.get('href',''))
        if not host_is(href,host): continue
        context=local_context(a)
        norm=fold(context)
        is_pdf=('.pdf' in urlparse(href).path.lower())
        has_bulletin = any(x in norm for x in ('bulletin','fil d actualites','fil d\'actualites','reporting','bti','newsletter'))
        if not (is_pdf or has_bulletin): continue
        if any(x in norm for x in ('rapport annuel','dic','statuts','note d information')) and not has_bulletin: continue
        p=period_from(context)
        if not p: continue
        if shared and not any(alias in norm for alias in aliases): continue
        # dedicated pages can have other SCPI in related links; prefer explicit name or pdf matching
        score=p['rank']*10 + (6 if is_pdf else 0) + (5 if any(alias in norm for alias in aliases) else 0) + (4 if has_bulletin else 0)
        candidates.append({'url':href,'period':p,'score':score,'description':context[:250]})
    return sorted(candidates,key=lambda c:c['score'],reverse=True)


def match_identity(doc_text, item):
    sample=fold(doc_text[:30_000])
    aliases=[item['name']]+ALIASES.get(item['id'],[])
    return any(fold(n) in sample for n in aliases)


def pdf_text(blob):
    if fitz is None: raise RuntimeError('pymupdf manquant')
    if blob[:4] != b'%PDF': raise ValueError('Ce lien ne fournit pas un PDF')
    doc=fitz.open(stream=blob,filetype='pdf')
    text='\n'.join(doc.load_page(i).get_text(sort=True) for i in range(min(len(doc),20)))
    return text[:250_000]


def date_in_context(s):
    m=re.search(r'\b([0-3]?\d)[/.-]([01]?\d)[/.-](20\d\d)\b',s)
    if m:
        try: return dt.date(int(m.group(3)),int(m.group(2)),int(m.group(1))).isoformat()
        except ValueError: return None
    return None


def metric_matches(text,label,minval,maxval):
    """Extract only clearly labelled, local (±110 characters) euro/percentage values."""
    rx = {
      'recon':r'valeur\s+de\s+reconstitution',
      'price':r'prix\s+(?:de\s+)?(?:souscription|de\s+la\s+part)',
      'tof':r'taux\s+d.occupation\s+financier|\bTOF\b',
    }[label]
    out=[]
    for m in re.finditer(rx, text, re.I):
        context=text[max(0,m.start()-70):m.end()+105]
        # reject crowded comparison/historical tables and numbers unrelated to the label
        after=text[m.end():m.end()+68]
        # label then value, optionally a date between them
        number=re.search(r'(?<!\d)(\d{1,4}(?:[\s\u00a0]\d{3})*(?:[,.]\d{1,2})?)\s*(€|euros?|%)',after,re.I)
        if not number: continue
        if label=='tof' and number.group(2)!='%':continue
        if label!='tof' and '%' in number.group(2):continue
        try: val=float(number.group(1).replace('\u00a0','').replace(' ','').replace(',','.'))
        except ValueError:continue
        if not(minval<=val<=maxval):continue
        effective=date_in_context(context) if label in ('price','recon') else None
        out.append({'value':round(val,2),'date':effective,'proof':context[:180]})
    return out


def single_consistent(arr,require_date=False):
    if require_date: arr=[x for x in arr if x['date']]
    if not arr:return None
    # Reject if two conflicting price or valuation numbers in one document
    if len({x['value'] for x in arr})>1:return None
    if require_date and len({x['date'] for x in arr})>1:return None
    return arr[0]



# Les chiffres de liquidité sont volontairement extraits uniquement lorsqu'une
# ligne du bulletin est univoque ; les tableaux multi-périodes sont ignorés.
LIQ_LABELS = {
 'waitingParts': re.compile(r'\b(?:nombre\s+de\s+)?parts?\s+en\s+attente(?:\s+de\s+retrait)?',re.I),
 'withdrawalsExecuted': re.compile(r'\b(?:nombre\s+de\s+)?(?:parts?\s+(?:retir[ée]es?|rembours[ée]es?|vendues)\s+(?:sur|au\s+cours\s+du)\s+(?:le|ce|du)?\s*trimestre|retraits?\s+(?:ex[ée]cut[ée]s?|effectu[ée]s?|compens[ée]s?)\s+(?:sur|au\s+cours\s+du)\s+(?:le|ce|du)?\s*trimestre|nombre\s+de\s+retraits?\s+(?:ex[ée]cut[ée]s?|effectu[ée]s?)|parts?\s+(?:retir[ée]es?|rembours[ée]es?))',re.I),
 'withdrawalRequests': re.compile(r'\b(?:demandes?\s+de\s+retrait\s+(?:enregistr[ée]es?|re[çc]ues?)|parts?\s+pr[ée]sent[ée]es?\s+au\s+retrait)\b',re.I),
}

def count_on_unique_line(line, match):
    """Un seul entier après l'intitulé, sans unité monétaire ni %. Sinon abstention."""
    tail=line[match.end():].strip().lstrip(':-| ') .strip()
    tail=re.sub(r'^(?:\(retraits?\)\s*)', '',tail,flags=re.I).strip(':-| ').strip()
    if not tail or re.search(r'[€%]',tail):return None
    # exactly one integer, possibly formatted with French thousands spaces
    m=re.fullmatch(r'(\d{1,3}(?:[ \u00a0\u202f]\d{3})+|\d+)\s*(?:parts?)?\s*[.]?',tail,re.I)
    if not m:return None
    val=int(re.sub(r'\s','',m.group(1)))
    return val if 0<=val<=100_000_000 else None


def extract_liquidity_counts(text):
    """Extraction prudente des libellés de liquidité dans le texte d'un bulletin PDF.

    Un tableau comportant plusieurs valeurs ou une donnée en euros n'est pas
    confondu avec un nombre de parts. Les données sans provenance datée ne
    donnent pas lieu à un délai estimé.
    """
    lines=[re.sub(r'[\t\u00a0\u202f]+',' ',ln).strip() for ln in text.splitlines()]
    values={k:[] for k in LIQ_LABELS}
    for i,line in enumerate(lines):
        if len(line)>220: continue
        for key,rx in LIQ_LABELS.items():
            m=rx.search(line)
            if not m:continue
            val=count_on_unique_line(line,m)
            if val is None:
                # Le libellé peut inclure "AU 31/03/2026", sans être la valeur.
                remainder=line[m.end():].strip(' :-|')
                only_label=(not remainder or bool(re.fullmatch(r'(?:au|à la date du)\s+\d{1,2}/\d{1,2}/20\d{2}',remainder,re.I)))
                if only_label:
                    # Disposition PDF parfois "181 973" puis "PARTS EN ATTENTE".
                    for j in (i+1,i-1):
                        if not 0<=j<len(lines):continue
                        nxt=lines[j]
                        val=count_on_unique_line('N '+nxt,re.match('N','N '+nxt))
                        if val is not None:break
                    if val is None and not remainder and i+2<len(lines) and re.fullmatch(r'(?:au|à la date du)\s+\d{1,2}/\d{1,2}/20\d{2}',lines[i+1],re.I):
                        val=count_on_unique_line('N '+lines[i+2],re.match('N','N '+lines[i+2]))
            if val is not None:values[key].append(val)
    return {k:(v[0] if v and len(set(v))==1 else None) for k,v in values.items()}


def update_liquidity(item, txt, period, url):
    """Stocke des valeurs *de même période*, un historique de flux trimestriels,
    et n'infère jamais un délai à partir d'un stock isolé."""
    got=extract_liquidity_counts(txt)
    if not any(v is not None for v in got.values()):return []
    old=item.get('liquidityData') or {}
    if old.get('periodEnd') and period['date']<old['periodEnd']:return []
    same=old.get('periodEnd')==period['date']
    nextd={**old} if same else {'withdrawals4Q':list(old.get('withdrawals4Q') or [])}
    nextd['periodEnd']=period['date']
    nextd['periodLabel']=period['label']
    # Sur un nouveau trimestre, ne JAMAIS recycler des volumes d'un autre trimestre
    if not same:
        for key in LIQ_LABELS:nextd[key]=None
    for k,v in got.items():
        if v is not None:nextd[k]=v
    nextd.update({'sourceUrl':url,'verifiedAt':TODAY,'method':'Lecture univoque du bulletin PDF ; flux de parts uniquement'})
    # Histoire seulement si trimestre clairement identifié (pas semestre)
    if period['periodType']=='T' and got['withdrawalsExecuted'] is not None:
        hist=[h for h in nextd['withdrawals4Q'] if h.get('periodEnd') != period['date']]
        hist.append({'periodEnd':period['date'],'parts':got['withdrawalsExecuted']})
        nextd['withdrawals4Q']=sorted(hist,key=lambda h:h['periodEnd'])[-4:]
    if nextd == old:return []
    item['liquidityData']=nextd
    item['waiting']=nextd.get('waitingParts')
    item.setdefault('fieldSources',{})['liquidityData']={'url':url,'date':period['date'],'method':nextd['method'],'proof':'libellés + valeurs univoques'}
    return ['liquidité / retraits']


def update_indicators(item,txt,period,url):
    changes=[]
    specs=[('recon',20,5000,True,'reconDate'),('price',20,5000,True,'priceDate'),('tof',0,100,False,None)]
    for key,lo,hi,needdate,datefield in specs:
        if key == 'price' and (item.get('priceType') or '').startswith('Marché secondaire'):
            continue  # Ne pas écraser un prix de confrontation par l'ancien prix de souscription d'un bulletin.
        got=single_consistent(metric_matches(txt,key,lo,hi),needdate)
        if not got: continue
        dated=got['date'] if datefield else period['date']
        if datefield and item.get(datefield) and dated < item[datefield]:continue
        if key=='tof' and item.get('bulletinDate') and dated < item['bulletinDate']:continue
        if item.get(key)!=got['value']:
            item[key]=got['value']
            if datefield:item[datefield]=dated
            item.setdefault('fieldSources',{})[key]={'url':url,'date':dated,'method':'extraction PDF stricte','proof':got['proof']}
            changes.append(key)
            if key=='recon':
                hist=[h for h in (item.get('history') or []) if h.get('date') != dated]
                hist.append({'date':dated,'value':got['value']})
                item['history']=sorted(hist,key=lambda x:x['date'])
    return changes


def extract_clean_breakdowns(soup, item):
    """Conservative, dated geographical and sector lists from a product page."""
    lines=[re.sub(r'\s+',' ',x).strip() for x in soup.get_text('\n',strip=True).split('\n')]
    lines=[x for x in lines if x]
    sections=[('geo',('par zones geographiques','repartition geographique')),
              ('types',('par type de locaux','repartition sectorielle','repartition typologique'))]
    found={}
    for key,titles in sections:
        for idx,line in enumerate(lines):
            if fold(line) not in titles:continue
            vals=[]
            for row in lines[idx+1:idx+22]:
                if re.search(r'\b(?:par zones|par type|repartition|nos actualites|documentation|les investissements)\b',fold(row)):break
                m=re.match(r'^(.{2,45}?)\s*\((\d{1,2}(?:[.,]\d+)?)%\)$',row)
                if m:vals.append([m.group(1),float(m.group(2).replace(',','.'))])
            if len(vals)>=3 and 97 <= sum(x[1] for x in vals)<=103:
                found[key]=vals;break
    if not found:return []
    # The date must expressly describe the ALLOCATION, not the report publication or page footer.
    dates=[]
    for idx,line in enumerate(lines):
        if 'repartition' not in fold(line):continue
        vicinity=' '.join(lines[max(0,idx-3):idx+3])
        for match in re.finditer(r'\b([0-3]\d/[01]\d/20\d\d)\b',vicinity):
            d=date_in_context(match.group(1))
            if d: dates.append(d)
    if not dates:return []
    latest=max(dates)
    if latest < (item.get('allocationDate') or '1900-01-01'):return []
    changed=[]
    for key,vals in found.items():
        if item.get(key)!=vals or latest!=(item.get('allocationDate') or ''):
            item[key]=vals;changed.append(key)
    if changed:
        item['allocationDate']=latest
        item.setdefault('fieldSources',{})['allocation']={'url':item['officialSource'],'date':latest,'method':'répartition textuelle contrôlée, somme ~100 %'}
    return changed


def discover_acquisition_news(soup,item,base_url,host):
    """Link announcements by the manager; no synthetic property descriptions."""
    out=[]
    for a in soup.find_all('a',href=True):
        title=a.get_text(' ',strip=True)
        if not (10<=len(title)<=145 and 'acquisition' in fold(title)):continue
        url=urljoin(base_url,a['href'])
        if not host_is(url,host):continue
        if url==base_url:continue
        parent=a.parent
        ctx=parent.get_text(' ',strip=True)[:250] if parent else title
        dates=re.findall(r'\b\d{2}/\d{2}/20\d{2}\b',ctx)
        when=dates[0] if dates else 'Annonce de la société de gestion · date non identifiée'
        if all(x['url']!=url for x in out):
            out.append({'when':when,'title':title,'details':'Annonce publiée par la société de gestion ; consulter la source pour les chiffres et la date.', 'url':url})
    return out[:5]


def verified_key_table(html, product_name):
    """Read aligned duration / nue-propriété / usufruit table; require complements to total 100%."""
    soup=BeautifulSoup(html,'html.parser')
    found={}
    for table in soup.find_all('table'):
        rows=[]
        for tr in table.find_all('tr'):
            rows.append([td.get_text(' ',strip=True) for td in tr.find_all(['td','th'])])
        if len(rows)<3:continue
        norm=[fold(' '.join(row)) for row in rows]
        np_row=next((i for i,x in enumerate(norm) if 'nue-propriete' in x),None)
        us_row=next((i for i,x in enumerate(norm) if 'usufruit' in x),None)
        if np_row is None or us_row is None or np_row==us_row:continue
        head=rows[0]
        years=[]
        for cell in head[1:]:
            m=re.search(r'\b(\d{1,2})\s*ans?\b',fold(cell))
            years.append(m.group(1) if m else None)
        nps=[];uses=[]
        for cell in rows[np_row][1:]:
            m=re.search(r'(\d{1,2}(?:[.,]\d+)?)\s*%',cell);nps.append(float(m.group(1).replace(',','.')) if m else None)
        for cell in rows[us_row][1:]:
            m=re.search(r'(\d{1,2}(?:[.,]\d+)?)\s*%',cell);uses.append(float(m.group(1).replace(',','.')) if m else None)
        keys={}
        for year,np,us in zip(years,nps,uses):
            if year is not None and np is not None and us is not None and 10<np<99 and abs(np+us-100)<=0.15:
                keys[year]=np
        if len(keys)>=4:found=keys;break
    return found



def update_manager_page_recon(item, html, url):
    """Extract ONLY the explicit 'valeur de reconstitution au DD/MM/YYYY' on
    this SCPI's own official product page. Require one value/date and no regression.
    This cannot silently convert a price of subscription to reconstitution.
    """
    if not (OFFICIAL.get(item['id']) and host_is(url, OFFICIAL[item['id']][1])):
        return []
    text=BeautifulSoup(html,'html.parser').get_text(' ',strip=True)
    pat=re.compile(r'valeur\s+de\s+reconstitution\s+au\s+([0-3]?\d[/.-][01]?\d[/.-]20\d\d)\s*[:\-]?\s*(\d{1,4}(?:[ \u00a0\u202f]\d{3})*(?:[,.]\d{1,2})?)\s*€',re.I)
    found=list(pat.finditer(text))
    if len(found)!=1:return []
    m=found[0];date=date_in_context(m.group(1))
    if not date:return []
    value=float(re.sub(r'\s','',m.group(2)).replace(',','.'))
    if not (5 <= value <= 5000):return []
    if item.get('reconDate') and item['reconDate'] > date:return []
    if item.get('recon')==value and item.get('reconDate')==date:return []
    item['recon']=value;item['reconDate']=date
    item.setdefault('fieldSources',{})['recon']={'url':url,'date':date,'method':'Extraction prudente de la fiche officielle du gérant','proof':m.group(0)}
    history=[h for h in (item.get('history') or []) if h.get('date') != date]
    history.append({'date':date,'value':value});item['history']=sorted(history,key=lambda x:x['date'])
    return ['reconstitution (site société de gestion)']


def refresh_keys(s,item):
    """Actualiser uniquement un tableau explicite du gérant ou de Meilleurtaux Placement.

    La source Meilleurtaux doit correspondre à la fiche SCPI renseignée.
    Toute grille ambiguë conserve la valeur précédente ; pas d'interpolation.
    """
    url = item.get('keySource')
    if not url:
        return []
    hostname = (urlparse(url).hostname or '').lower().removeprefix('www.')
    manager_entry = OFFICIAL.get(item['id'])
    is_manager = bool(manager_entry and host_is(url,manager_entry[1]))
    mtp_profile = item.get('mtxUrl') or ''
    is_mtp = (
        host_is(url,'placement.meilleurtaux.com')
        and bool(mtp_profile)
        and host_is(mtp_profile,'placement.meilleurtaux.com')
        and (url == mtp_profile or (
            item['id'] == 'sofidynamic'
            and '/scpi/actualites/2026-octobre/scpi-sofidynamic-en-nue-propriete-' in url
        ))
    )
    if not (is_manager or is_mtp):
        return []
    try:
        blob,ctype,final_url = fetch(s,url,hostname,limit=MAX_HTML)
        if blob.startswith(b'%PDF'):
            return []  # Une grille PDF doit être validée séparément.
        html=blob.decode('utf-8','replace')
        soup=BeautifulSoup(html,'html.parser')
        # La page doit faire explicitement référence à la SCPI suivie.
        heading=fold(' '.join(x.get_text(' ',strip=True) for x in soup.find_all(['h1','h2'])[:6]))
        expected=fold(item['name'])
        if is_mtp and expected not in heading:
            return []
        keys=verified_key_table(html,item['name'])
        if not keys or len(keys)<4:
            return []
        # Toutes les durées doivent être distinctes et plus longues = clé NP
        # décroissante ou constante ; sinon conserver l'ancien barème.
        ordered=sorted(((int(year),float(value)) for year,value in keys.items()))
        if any(year<1 or year>30 or not (1<value<99) for year,value in ordered):
            return []
        if any(ordered[i][1] < ordered[i+1][1] for i in range(len(ordered)-1)):
            return []
        normalised={str(year):value for year,value in ordered}
        if item.get('keys')==normalised:
            item['keyVerifiedAt']=TODAY
            return []
        item['keys']=normalised
        item['keyVerifiedAt']=TODAY
        item['keySourceType']='Meilleurtaux Placement' if is_mtp else 'Société de gestion'
        # Ne pas utiliser la date de consultation comme date d'entrée en vigueur.
        if is_mtp:
            item['keyDate']=None
        item['keyNote']=(
            'Barème indicatif relevé sur Meilleurtaux Placement ; vérifier les conditions avant souscription.'
            if is_mtp else
            'Grille indicative publiée par la société de gestion ; confirmer avant souscription.'
        )
        return ['démembrement ('+('Meilleurtaux Placement' if is_mtp else 'gérant')+')']
    except Exception as exc:
        LOG.debug('Clés non actualisées pour %s : %s',item['name'],exc)
    return []


def source_for(item):
    return OFFICIAL.get(item['id'])


def refresh_one(s,item):
    entry=source_for(item)
    if not entry:raise RuntimeError('Source officielle absente du référentiel')
    url,host=entry
    page_bytes,ctype,final_url=fetch(s,url,host)
    if b'%PDF' == page_bytes[:4]:raise ValueError('La page de recherche renvoie un PDF brut')
    html=page_bytes.decode('utf-8',errors='replace')
    candidates=discover(html,final_url,item,host)
    item['officialSource']=final_url
    # Several managers publish dated reconstitution values on the SCPI page itself.
    # This path does not require a PDF bulletin and refuses undated numbers.
    changes=update_manager_page_recon(item,html,final_url)
    changes+=extract_clean_breakdowns(BeautifulSoup(html,'html.parser'),item)
    news=discover_acquisition_news(BeautifulSoup(html,'html.parser'),item,final_url,host)
    if news and not item.get('acquisitions'):
        item['acquisitions']=news
        changes.append('acquisitions')
    # Iroko has predictable HTML release pages; validate candidate via actual content.
    if item['id']=='iroko-zen':
        q = dt.date.today().month
        year=dt.date.today().year
        # Only probe the current and previous closed quarter, and verify page text.
        for y,k in [(year, i) for i in range(1,5)]+[(year-1,4)]:
            if y*4+k <= existing_rank(item):continue
            if dt.date(y,k*3,[31,30,30,31][k-1])>dt.date.today():continue
            candidate_url=f'https://www.iroko.eu/bulletins-trimestriels/t{k}-{y}'
            try:
                content,_,candidate_final=fetch(s,candidate_url,host)
                if not re.search(rf'\b(?:{k}(?:er|e|eme)?\s*trimestre|t{k})\s*{y}\b',fold(content.decode('utf-8','replace'))):continue
                candidates.append({'url':candidate_final,'period':period_from(f'T{k} {y}'),'score':y*40+k*10+7,'description':'Bulletin Iroko Zen - page officielle'})
            except Exception:pass
    if candidates:
        best=max(candidates,key=lambda c:(c['period']['rank'],c['score']))
        p=best['period']
        if p['rank']>=existing_rank(item):
            cand_url=best['url']
            # Some pages offer a landing HTML rather than a PDF; both are valid sources.
            if p['rank']>existing_rank(item) or not item.get('bulletinUrl'):
                item.update({'bulletin':p['label'],'bulletinDate':p['date'],'bulletinUrl':cand_url})
                changes.append('bulletin')
            if '.pdf' in urlparse(cand_url).path.lower():
                try:
                    blob,_,resolved=fetch(s,cand_url,host,limit=MAX_PDF)
                    txt=pdf_text(blob)
                    if not match_identity(txt,item):
                        raise ValueError('Identité SCPI absente dans le PDF : vérification requise')
                    changes+=update_indicators(item,txt,p,resolved)
                    changes+=update_liquidity(item,txt,p,resolved)
                    item['pdfVerifiedAt']=TODAY
                except Exception as exc:
                    item['pdfWarning']=str(exc)[:180]
            else:
                # A HTML document is still linked for consultation.
                item.pop('pdfWarning',None)
    changes+=refresh_keys(s,item)
    item['lastChecked']=TODAY
    item['automatedCheck']='Source officielle consultée' if candidates else 'Site accessible · bulletin non détecté automatiquement'
    return changes, bool(candidates)


def main():
    ap=argparse.ArgumentParser(description='Synchronise les informations officielles publiques des SCPI')
    ap.add_argument('--dry-run',action='store_true',help='Ne pas sauvegarder')
    ap.add_argument('--only',default='',help='Identifiant SCPI, pour diagnostic')
    ap.add_argument('--offline-test',action='store_true',help='Tester les règles sans connexion réseau')
    args=ap.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s')
    items=json.loads(DATA.read_text(encoding='utf-8'))
    for item in items:
        item['officialSource']=OFFICIAL.get(item['id'],(item.get('sourceUrl'),'none'))[0]
        if item['id'] in LIQUIDITY:
            label,effective,src=LIQUIDITY[item['id']]
            item['liquidity']={'label':label,'effective':effective,'source':src}
    if args.offline_test:
        print(json.dumps({'scpi':len(items),'source_configs':len(OFFICIAL),'keys':sum(bool(i.get('keys')) for i in items)},ensure_ascii=False));return
    statuses=[];changed=0;ok=0;found=0
    ss=session()
    for item in items:
        if args.only and item['id']!=args.only:continue
        try:
            updates,detected=refresh_one(ss,item)
            ok+=1;found+=int(detected);changed+=int(bool(updates))
            statuses.append({'id':item['id'],'name':item['name'],'status':'ok' if detected else 'partial','changes':updates,'message':item.get('automatedCheck',''),'source':item['officialSource']})
            LOG.info('%s: %s',item['name'],', '.join(updates) or ('bulletin déjà à jour' if detected else 'source accessible, bulletin non détecté'))
        except Exception as e:
            statuses.append({'id':item['id'],'name':item['name'],'status':'error','changes':[],'message':str(e)[:220],'source':item['officialSource']})
            item['automatedCheck']='Échec de récupération · données précédentes conservées'
            LOG.warning('%s: %s',item['name'],e)
    report={'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),'total':len(statuses),'sourceAccessible':ok,'bulletinFound':found,'updated':changed,'results':statuses}
    print(json.dumps({'date':TODAY,'sources_accessibles':ok,'bulletins_detectes':found,'fiches_modifiees':changed,'erreurs':len(statuses)-ok},ensure_ascii=False))
    if not args.dry_run:
        DATA.write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        STATUS.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
