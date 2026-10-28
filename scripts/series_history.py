"""Points historiques vérifiables pour les graphiques SCPI.

Jamais d'interpolation, de copie de date de vérification comme période, ni
de remplacement d'un point contradictoire. Les archives non sourcées sont
signalées explicitement, et non attribuées à une publication plus récente.
"""
from __future__ import annotations
import datetime as dt
from urllib.parse import urlparse

METRICS=('price','recon','tof','td','waitingParts','withdrawalsExecuted')
LIMIT=48

def valid_day(value):
    try:
        if not isinstance(value,str) or len(value)!=10:return False
        return dt.date.fromisoformat(value).isoformat()==value
    except ValueError:
        return False

def valid_source(value):
    try:
        u=urlparse(value or '')
        return u.scheme=='https' and bool(u.hostname) and not u.username and not u.password
    except ValueError:
        return False

def append_point(item,metric,day,value,source=None,kind=None):
    if metric not in METRICS or not valid_day(day):return False
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not (0<=value<1e8):return False
    values=item.setdefault('indicatorHistory',{})
    series=values.setdefault(metric,[])
    found=next((point for point in series if point.get('date')==day),None)
    if found:
        if found.get('value')!=value:
            issues=item.setdefault('historyConflicts',[])
            conflict={'metric':metric,'date':day,'recorded':found.get('value'),'observed':value}
            if conflict not in issues:issues.append(conflict)
            item['historyConflicts']=issues[-25:]
            return False
        if not found.get('source') and valid_source(source):
            found['source']=source
        return False
    point={'date':day,'value':value,'source':source if valid_source(source) else None}
    if kind:point['kind']=kind
    series.append(point)
    series.sort(key=lambda p:p['date'])
    values[metric]=series[-LIMIT:]
    return True

def sync_history(item):
    """Ajoute uniquement les observations dont les dates et chiffres sont connus.

    La valeur de reconstitution historique issue de 'history' n'a pas
    nécessairement de lien documentaire : on n'invente jamais la provenance.
    """
    fields=item.get('fieldSources') or {}
    for metric,daykey in [('price','priceDate'),('recon','reconDate'),('tof','tofDate')]:
        source=(fields.get(metric) or {}).get('url')
        if metric=='price' and not source:source=item.get('priceSource')
        append_point(item,metric,item.get(daykey),item.get(metric),source,kind='current')
    for point in item.get('history') or []:
        if isinstance(point,dict):
            append_point(item,'recon',point.get('date'),point.get('value'),point.get('source'),kind='archive')
    append_point(item,'price',item.get('previousPriceDate'),item.get('previousPrice'),
                 item.get('previousPriceSource'),kind='previous')
    for year,entry in (item.get('tdHistory') or {}).items():
        if isinstance(entry,dict) and str(year).isdigit():
            append_point(item,'td',str(year)+'-12-31',entry.get('value'),
                         entry.get('source'),kind='annual')
    liquidity=item.get('liquidityData') or {}
    d=liquidity.get('periodEnd')
    source=liquidity.get('sourceUrl')
    append_point(item,'waitingParts',d,liquidity.get('waitingParts'),source,kind='stock')
    append_point(item,'withdrawalsExecuted',d,liquidity.get('withdrawalsExecuted'),source,kind='quarter')
    for q in liquidity.get('withdrawals4Q') or []:
        if isinstance(q,dict):
            # Certains points de retrait archivés n'ont pas d'URL propre.
            # Ne leur affecter la source actuelle que si le trimestre correspond.
            period=q.get('periodEnd')
            append_point(item,'withdrawalsExecuted',period,q.get('parts'),
                         source if period==d else q.get('sourceUrl'),kind='quarter')
    return item.get('indicatorHistory',{})
