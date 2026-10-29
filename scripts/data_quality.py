"""Contrôles non destructifs et validations avant publication de données SCPI.

Aucun indicateur n'est reconstitué ou comblé par estimation. Les anomalies
historiques sont reportées ; les nouvelles données non cohérentes sont rejetées.
"""
from __future__ import annotations

import datetime as dt
import re
from urllib.parse import urlparse

INDICATORS = {
    'price': ('priceDate', 540),
    'recon': ('reconDate', 540),
    'tof': ('tofDate', 210),
    'geo': ('geoDate', 420),
    'types': ('typesDate', 420),
    'keys': ('keyDate', 420),
    'liquidityData': ('periodEnd', 180),
}
NUMERIC = {'price': (1, 5000), 'recon': (1, 5000), 'tof': (0, 100), 'td': (0, 20)}
CHANGING = ('price', 'recon', 'td', 'tof', 'geo', 'types', 'keys', 'liquidityData', 'bulletin')


def official_url(url):
    try:
        u = urlparse(url or '')
        return u.scheme == 'https' and bool(u.hostname) and not u.username and not u.password
    except ValueError:
        return False


def parse_day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def field_day(item, key):
    if key == 'liquidityData':
        return (item.get('liquidityData') or {}).get('periodEnd')
    if key == 'td':
        return str(item.get('tdYear', 2025)) + '-12-31'
    if key == 'bulletin':
        return item.get('bulletinDate')
    return item.get(INDICATORS[key][0])


def field_source(item, key):
    if key == 'bulletin':
        return item.get('bulletinUrl')
    if key == 'keys':
        return item.get('keySource')
    if key == 'liquidityData':
        return (item.get('liquidityData') or {}).get('sourceUrl')
    if key == 'price':
        return (item.get('fieldSources') or {}).get(key, {}).get('url') or item.get('priceSource')
    return (item.get('fieldSources') or {}).get(key, {}).get('url')


def has_value(item, key):
    if key == 'liquidityData':
        value = item.get(key) or {}
        return any(value.get(field) is not None for field in ('waitingParts','withdrawalsExecuted','withdrawalRequests'))
    value = item.get(key)
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return bool(value)
    return True


def valid_allocation(values):
    if not isinstance(values, list) or len(values) < 2:
        return False
    seen = set()
    total = 0.0
    for row in values:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            return False
        name, value = row
        if not isinstance(name, str) or not name.strip() or name in seen:
            return False
        seen.add(name)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 100:
            return False
        total += value
    return 99 <= total <= 101


def valid_keys(values):
    if not isinstance(values, dict) or len(values) == 0:
        return False
    try:
        points = sorted((int(year), float(share)) for year, share in values.items())
    except (ValueError, TypeError):
        return False
    if len({year for year, _ in points}) != len(points):
        return False
    if any(not 1 <= year <= 30 or not 1 < share < 99 for year, share in points):
        return False
    return all(points[i][1] >= points[i + 1][1] for i in range(len(points) - 1))


def valid_liquidity(value):
    if not isinstance(value, dict):
        return False
    counts = [value.get(k) for k in ('waitingParts', 'withdrawalsExecuted', 'withdrawalRequests')]
    if not any(v is not None for v in counts):
        return False
    return all(v is None or (type(v) is int and 0 <= v < 100_000_000) for v in counts)


def approved_update_source(item, field, url):
    """Une nouvelle valeur doit provenir du gérant identifié, ou d'un barème
    de démembrement Meilleurtaux / La Française explicitement accepté.
    Les références anciennes recoupées ailleurs ne sont pas déclassées.
    """
    if not official_url(url):
        return False
    doc=(urlparse(url).hostname or '').lower().removeprefix('www.')
    manager=(urlparse(item.get('officialSource') or '').hostname or '').lower().removeprefix('www.')
    if manager and (doc==manager or doc.endswith('.'+manager)):
        return True
    if manager == 'perial.com' and doc == 'cdn.prod.website-files.com' and urlparse(url).path.startswith('/68d505281630e4a2223e1bee/') and urlparse(url).path.lower().endswith('.pdf'):
        # Hébergement de fichiers de la page officielle PERIAL Asset Management.
        return True
    if manager == 'principalam.com' and doc == 'brandassets.principal.com' and urlparse(url).path.startswith('/asset/') and urlparse(url).path.lower().endswith('.pdf'):
        return True
    if field=='keys' and doc in ('placement.meilleurtaux.com','lafrancaise-am-partenaires.com'):
        return True
    return False


def validate_td_history_updates(before, after, today):
    """Contrôle les millésimes qui changent, sans pénaliser les archives anciennes."""
    old=before.get('tdHistory') or {}
    new=after.get('tdHistory') or {}
    if not isinstance(old,dict) or not isinstance(new,dict):
        return ['Historique TD : format inattendu']
    issues=[]
    for year,previous in old.items():
        if year not in new:
            issues.append('Historique TD : suppression du millésime '+str(year))
    for key,value in new.items():
        if old.get(key)==value:continue
        try:year=int(key)
        except (TypeError,ValueError):
            issues.append('Historique TD : année invalide');continue
        if not (2022<=year<today.year):
            issues.append('Historique TD : année non clôturée ('+str(year)+')')
        if not isinstance(value,dict):
            issues.append('Historique TD : entrée sans justificatif');continue
        rate=value.get('value')
        if isinstance(rate,bool) or not isinstance(rate,(int,float)) or not (0<rate<20):
            issues.append('Historique TD : taux annuel invalide ('+str(year)+')')
        if value.get('date')!=f'{year}-12-31':
            issues.append('Historique TD : période annuelle incohérente ('+str(year)+')')
        if not approved_update_source(after,'td',value.get('source')):
            issues.append('Historique TD : source annuelle non approuvée ('+str(year)+')')
    latest=[int(y) for y,e in new.items() if y.isdigit() and isinstance(e,dict) and isinstance(e.get('value'),(int,float))]
    if latest:
        maximum=max(latest);entry=new[str(maximum)]
        if int(after.get('tdYear') or 0)!=maximum or after.get('td')!=entry.get('value'):
            issues.append('Historique TD : le TD affiché ne correspond pas au dernier millésime')
    return issues


def validate_updates(before, after, today):
    """Rejette seulement les nouvelles valeurs qui ne sont pas justifiées.

    Les vieilles lacunes du catalogue ne bloquent pas une autre nouvelle valeur
    correctement prouvée.
    """
    today = parse_day(today)
    if not today:
        raise ValueError('Date de contrôle invalide')
    issues = []
    for key in CHANGING:
        if before.get(key) == after.get(key) and field_day(before, key) == field_day(after, key):
            continue
        # Un champ préexistant non publié ne déclenche pas une erreur.
        if not has_value(after, key):
            issues.append(key + ' : effacement d’une valeur précédemment publiée')
            continue
        source = field_source(after, key)
        if not official_url(source):
            issues.append(key + ' : URL justificative HTTPS manquante')
        elif not approved_update_source(after,key,source):
            issues.append(key + ' : justificatif hors domaine éditeur approuvé')
        current = parse_day(field_day(after, key))
        if key != 'keys' and current is None:
            issues.append(key + ' : date de référence absente ou incorrecte')
        elif current and current > today:
            issues.append(key + ' : date de référence future')
        previous = parse_day(field_day(before, key))
        if current and previous and current < previous:
            issues.append(key + ' : tentative de régression de date')
        if key in NUMERIC:
            low, high = NUMERIC[key]
            value = after.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
                issues.append(key + ' : valeur hors plage contrôlée')
        elif key in ('geo', 'types') and not valid_allocation(after.get(key)):
            issues.append(key + ' : ventilation incomplète ou incohérente (somme ≠ 100 %)')
        elif key == 'keys' and not valid_keys(after.get(key)):
            issues.append(key + ' : barème non monotone ou invalide')
        elif key == 'liquidityData' and not valid_liquidity(after.get(key)):
            issues.append(key + ' : nombre de parts invalide')
    issues.extend(validate_td_history_updates(before,after,today))
    return issues


def audit_scpi(item, today):
    """Anomalies documentaires, non assimilées automatiquement à des erreurs gérant."""
    today = parse_day(today)
    if not today:
        raise ValueError('Date de contrôle invalide')
    issues = []
    def add(field, kind, detail, level='warning'):
        issues.append({'field': field, 'kind': kind, 'detail': detail, 'level': level,
                       'source': field_source(item, field) or item.get('officialSource')})
    for field, (date_key, threshold) in INDICATORS.items():
        if not has_value(item, field):
            continue
        day = parse_day(field_day(item, field))
        if day is None:
            add(field, 'date_absente', 'Date de référence manquante ou invalide')
        elif day > today:
            add(field, 'date_future', 'Date de référence postérieure au contrôle', 'error')
        elif (today - day).days > threshold:
            add(field, 'ancienne', f'Donnée du {day.isoformat()} : {(today-day).days} jours (seuil indicatif {threshold} jours)')
        if not official_url(field_source(item, field)):
            add(field, 'source_absente', 'Justificatif HTTPS spécifique non renseigné')
        if field in ('geo', 'types') and not valid_allocation(item.get(field)):
            add(field, 'incoherente', 'Ventilation géographique/sectorielle ne totalisant pas 100 %', 'error')
        if field == 'keys' and not valid_keys(item.get(field)):
            add(field, 'incoherente', 'Clés NP hors bornes ou non monotones', 'error')
        if field == 'liquidityData' and not valid_liquidity(item.get(field)):
            add(field, 'incoherente', 'Quantités de parts invalides', 'error')
    if has_value(item, 'td') and not official_url(field_source(item, 'td')):
        add('td', 'source_absente', 'TD historique sans URL justificative détaillée')
    return issues[:45]


def quality_report(items, today):
    audits = [{
        'id': item['id'], 'name': item['name'], 'issues': audit_scpi(item, today)
    } for item in items]
    counts = {'ancienne': 0, 'date_absente': 0, 'date_future': 0,
              'source_absente': 0, 'incoherente': 0}
    for row in audits:
        for issue in row['issues']:
            counts[issue['kind']] = counts.get(issue['kind'], 0) + 1
    return {
        'asOf': today, 'affectedScpi': sum(bool(row['issues']) for row in audits),
        'issueCounts': counts, 'scpi': audits
    }
