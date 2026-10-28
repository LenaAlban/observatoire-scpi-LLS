"""Historique annuel des TD SCPI. Pas de TD annualisé depuis un trimestre.

Les taux ne sont retenus que lorsqu'une année civile terminée, un libellé
de distribution annuel et une valeur unique sont explicitement rapprochés.
"""
from __future__ import annotations
import datetime as dt
import re
import unicodedata

def clean(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',text or '') if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',text.replace('\u00a0',' ').replace('\u202f',' ')).lower()

def extract_annual_td(text,today):
    today=dt.date.fromisoformat(today)
    raw=clean(text)[:250000]
    label=r'(?:taux\s+de\s+distribution|(?<![a-z])td(?![a-z]))'
    percent=r'(?P<rate>\d{1,2}(?:[,.]\d{1,2})?)\s*%'
    year=r'(?P<year>20\d{2})'
    patterns=[
        re.compile(label+r'(?:\s+(?:brut|annuel|de\s+l.annee|au\s+titre\s+de\s+l.annee)){0,3}\s*(?:[:\-\s]|de\s+)*'+year+r'\s*(?:[:=\-]|est|s.etablit\s+a|atteint|de)?\s*'+percent,re.I),
        re.compile(r'(?:en|pour|annee|exercice)\s+'+year+r'.{0,85}?'+label+r'(?:\s+(?:brut|annuel))?\s*(?::|de|a|atteint|s.etablit\s+a)?\s*'+percent,re.I),
        re.compile(label+r'(?:\s+(?:brut|annuel))?\s*[:\-]?\s*'+percent+r'\s*(?:en|pour|au\s+titre\s+de)\s+'+year,re.I),
    ]
    found={}
    blocked_terms=('prevision','previsionnel','objectif','cible','hypothese','estimation','projete','annualise',
                   'a date','au 30/','au 31/','provisoire','estime','non garanti pour')
    for rx in patterns:
        for m in rx.finditer(raw):
            y=int(m.group('year'))
            v=round(float(m.group('rate').replace(',','.')),2)
            if not (2022<=y<today.year and 0<v<20):continue
            snippet=raw[max(0,m.start()-35):min(len(raw),m.end()+35)]
            # Do not mistake a target/estimated return or annualized YTD for a final TD.
            if any(term in snippet for term in blocked_terms):continue
            found.setdefault(y,[]).append({'value':v,'proof':m.group(0)[:180]})
    return {
        y:vals[0] for y,vals in found.items()
        if vals and len({v['value'] for v in vals})==1
    }

def legacy_td_year(item):
    if item.get('td') is None:return None
    year=item.get('tdYear')
    try:year=int(year) if year is not None else 2025
    except (TypeError,ValueError):return None
    return year if 2022<=year<=2035 else None

def normalize_history(item):
    """Créer le point de départ à partir du TD historique connu, sans inventer de source."""
    history=dict(item.get('tdHistory') or {})
    y=legacy_td_year(item)
    if y is not None:
        key=str(y)
        if key not in history:
            source=(item.get('fieldSources') or {}).get('td') or {}
            history[key]={
                'value':float(item['td']),
                'date':f'{y}-12-31',
                'source':source.get('url'),
                'proof':source.get('proof'),
                'method':source.get('method') or 'TD historique initial du référentiel',
            }
        item['tdYear']=y
    item['tdHistory']={k:history[k] for k in sorted(history,key=int)}
    return item['tdHistory']

def update_annual_td(item,text,url,today,recorder):
    """Une nouvelle année civile terminée et documentée peut devenir le TD affiché.

    Les archives d'autres années sont conservées. Le TD de l'année courante
    n'est jamais projeté depuis les trimestres. Régression de TD interdite.
    """
    found=extract_annual_td(text,today)
    history=normalize_history(item)
    updated=[]
    for year,info in sorted(found.items()):
        key=str(year);value=info['value'];before=history.get(key)
        if before and before.get('value')==value:
            # Ne pas effacer une meilleure référence archivistique.
            if not before.get('source'):
                before['source']=url
                before['proof']=info['proof']
            continue
        if before and before.get('value')!=value:
            # Une valeur contradictoire n'est pas arbitrée automatiquement.
            item.setdefault('tdConflicts',[])
            conflict={'year':year,'recorded':before.get('value'),'observed':value,'source':url,'proof':info['proof']}
            if conflict not in item['tdConflicts']:
                item['tdConflicts']=(item['tdConflicts']+[conflict])[-12:]
            continue
        history[key]={'value':value,'date':f'{year}-12-31',
                      'source':url,'proof':info['proof'],
                      'method':'TD annuel explicite détecté dans une publication officielle'}
        updated.append(year)
        recorder(item,'tdHistory',None,{'year':year,'value':value},f'{year}-12-31',url)
    available=[int(y) for y,e in history.items() if isinstance(e,dict) and isinstance(e.get('value'),(int,float))]
    if available:
        last=max(available);info=history[str(last)]
        current=legacy_td_year(item)
        if current is None or last>current:
            recorder(item,'td',item.get('td'),info['value'],f'{last}-12-31',info.get('source') or url)
            item['td']=info['value']
            item['tdYear']=last
            item.setdefault('fieldSources',{})['td']={
                'url':info.get('source') or url,
                'date':f'{last}-12-31',
                'verifiedAt':today,
                'proof':info.get('proof') or '',
                'method':'TD annuel clos, extrait d’une publication officielle'
            }
            updated.append('td')
    return ['TD annuel '+str(y) for y in updated if isinstance(y,int)]+(['TD affiché actualisé'] if 'td' in updated else [])
