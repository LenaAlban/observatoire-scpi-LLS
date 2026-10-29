
# Pages et documents hébergés chez les gérants, vérifiés comme voies de
# secours. Leur présence n'atteste jamais à elle seule qu'un bulletin est lu.
SOFIDY_BULLETINS='https://www.sofidy.com/actualites/scpi-sofidy-les-bulletins-trimestriels-du-2eme-trimestre-2026/'
SOFIDY_DOCUMENTATION='https://www.sofidy.com/documentation/'
OFFICIAL_FALLBACKS = {
    'altixia-cadence-xii': [
        'https://www.altixia.fr/documentation.php?listeProduit=1',
        # Bulletin T2 2026 signalé depuis le domaine officiel Altixia.
        # Le robot doit encore vérifier sa SCPI et sa période dans le PDF.
        'https://www.altixia.fr/medias/documentations/doc1-20260730-213536.pdf',
        'https://www.altixia.fr/medias/documentations/doc1-20260430-122013.pdf',
    ],
    'edissimmo': [
        'https://www.amundi-immobilier.com/Local-content/Producsheet/SCPI/EDISSIMMO/L-essentiel',
        # Bulletin officiel 2nd semestre 2025 : recours si les pages sont en 503.
        'https://www.amundi-immobilier.com/ezjscore/call/ezjscamundibuzz%3A%3AsfForwardFront%3A%3AparamsList%3Dservice%3DProxyGedApi%26routeId%3D_dl_05dd8d96-770e-40ad-b786-f1482ab0a0b1',
    ],
    'rivoli-avenir-patrimoine': [
        'https://www.amundi-immobilier.com/Local-content/Producsheet/SCPI/RIVOLI-AVENIR-PATRIMOINE/L-essentiel',
    ],
    'efimmo-1': [
        # Bulletin T2 2026 communiqué par l'utilisateur ; vérifier dans le
        # PDF la SCPI et le trimestre avant toute actualisation de chiffres.
        'https://www.sofidy.com/app/uploads/2026/07/Bulletin_Trimestriel_-_Efimmo_OPTI.pdf',
        SOFIDY_BULLETINS, SOFIDY_DOCUMENTATION,
    ],
    'immorente': [
        # URL PDF T2 2026 déjà enregistrée dans la fiche SCPI.
        'https://www.sofidy.com/app/uploads/2026/07/Bulletin_Trimestriel_-_Immorente_2026_2T_OPTI.pdf',
        SOFIDY_BULLETINS, SOFIDY_DOCUMENTATION,
    ],
    'sofidynamic': [
        # Bulletin T2 2026 officiel fourni par un conseiller ; toujours
        # confirmer dans le texte PDF le fonds et le trimestre avant usage.
        'https://www.sofidy.com/app/uploads/2026/07/Bulletin_Trimestriel_-_Sofidynamic_OPTI.pdf',
        SOFIDY_BULLETINS, SOFIDY_DOCUMENTATION,
    ],
    'sofidy-europe-invest': [SOFIDY_BULLETINS, SOFIDY_DOCUMENTATION],
    'pf-grand-paris': [
        'https://www.perial.com/documentation',
        # PDF publié sur le CDN explicitement lié par la page PERIAL.
        'https://cdn.prod.website-files.com/68d505281630e4a2223e1bee/6a7cda7ae845ffc70aa1350e_PERIAL%20Grand%20Paris%20-%20Bulletin%20trimestriel%20d%27information%20%28T2%202026%29.pdf',
    ],
    'pfo2': [
        'https://www.perial.com/documentation',
        'https://cdn.prod.website-files.com/68d505281630e4a2223e1bee/6a7cda5d0727e6de700af0b9_PERIAL%20O%E2%82%82%20-%20Bulletin%20trimestriel%20d%27information%20%28T2%202026%29.pdf',
    ],
    'principal-inside': [
        'https://fr.principalam.com/notre-scpi',
        'https://fr.principalam.com/nos-publications',
    ],
}

"""Pages officielles vérifiées au 28 octobre 2026. Les liens sont des pages, non des PDF hypothétiques."""
OFFICIAL = {
 'iroko-zen': ('https://www.iroko.eu/bulletins-trimestriels/t2-2026', 'iroko.eu'),
 'pierval-sante': ('https://www.euryale-am.fr/nos-solutions/pierval/', 'euryale-am.fr'),
 'corum-origin': ('https://www.corum.fr/nos-scpi/corum-origin/documents', 'corum.fr'),
 'remake-live': ('https://www.remake.fr/remake-live', 'remake.fr'),
 'actipierre-europe': ('https://www.aewpatrimoine.com/nos-produits/scpi-dimmobilier-dentreprise/aew-commerces-europe', 'aewpatrimoine.com'),
 'altixia-cadence-xii': ('https://www.altixia.fr/scpi-cadence.php', 'altixia.fr'),
 'atream-hotels': ('https://atream.com/solutions/fonds-ouverts/scpi-atream-hotels/', 'atream.com'),
 'edissimmo': ('https://www.amundi-immobilier.com/Local-content/Producsheet/SCPI/EDISSIMMO/Documents', 'amundi-immobilier.com'),
 'efimmo-1': ('https://www.sofidy.com/solutions/efimmo1/', 'sofidy.com'),
 'epargne-fonciere': ('https://www.la-francaise.com/fr-fr/investisseur/nos-fonds/actifs-non-cotes/immobilier/scpi.aspx?Scpi=Epargne-Fonciere&amcScpi=16969&code=EE', 'la-francaise.com'),
 'ficommerce': ('https://www.fiducial-gerance.fr/investir-en-scpi/nos-scpi/ficommerce-proximite', 'fiducial-gerance.fr'),
 'immorente': ('https://www.sofidy.com/solutions/immorente/', 'sofidy.com'),
 'laffitte-pierre': ('https://www.aewpatrimoine.com/nos-produits/scpi-dimmobilier-dentreprise/laffitte-pierre', 'aewpatrimoine.com'),
 'lf-europimmo': ('https://www.la-francaise.com/fr-fr/investisseur/nos-fonds/actifs-non-cotes/immobilier/scpi.aspx?Scpi=LF-Europimmo&amcScpi=16849&code=D1', 'la-francaise.com'),
 'lf-grand-paris-patrimoine': ('https://www.la-francaise.com/fr-fr/investisseur/nos-fonds/actifs-non-cotes/immobilier/scpi.aspx?Scpi=LF-Grand-Paris-Patrimoine&amcScpi=19050&code=Z2', 'la-francaise.com'),
 'patrimmo-commerce': ('https://www.praemiareim.fr/fr/scpi-patrimmo-commerce', 'praemiareim.fr'),
 'patrimmo-croissance': ('https://www.praemiareim.fr/fr/scpi-patrimmo-croissance', 'praemiareim.fr'),
 'pf-grand-paris': ('https://www.perial.com/scpi/perial-grand-paris', 'perial.com'),
 'primopierre': ('https://www.praemiareim.fr/fr/scpi-primopierre', 'praemiareim.fr'),
 'primovie': ('https://www.praemiareim.fr/fr/scpi-primovie', 'praemiareim.fr'),
 'pfo2': ('https://www.perial.com/scpi/perial-o2', 'perial.com'),
 'rivoli-avenir-patrimoine': ('https://www.amundi-immobilier.com/Local-content/Producsheet/SCPI/RIVOLI-AVENIR-PATRIMOINE/Documents', 'amundi-immobilier.com'),
 'selectinvest-1': ('https://www.la-francaise.com/fr-fr/nos-solutions-pour-vous/nos-produits/product/Scpi/i9-selectinvest-1/', 'la-francaise.com'),
 'epargne-pierre': ('https://atland-voisin.com/scpi/epargne-pierre/', 'atland-voisin.com'),
 'sofidynamic': ('https://www.sofidy.com/solutions/sofidynamic/', 'sofidy.com'),
 'transitions-europe': ('https://www.arkea-reim.com/immobilier/pa_89367/scpi-transitions-europe', 'arkea-reim.com'),
 'epargne-pierre-europe': ('https://atland-voisin.com/scpi/epargne-pierre-europe/', 'atland-voisin.com'),
 'epargne-pierre-sophia': ('https://atland-voisin.com/scpi/epargne-pierre-sophia/', 'atland-voisin.com'),
 'sofidy-europe-invest': ('https://www.sofidy.com/solutions/sofidy-europe-invest/', 'sofidy.com'),
 'principal-inside': ('https://fr.principalam.com/notre-scpi', 'principalam.com'),
 'corum-usa': ('https://www.corum.fr/nos-scpi/corum-usa/documents', 'corum.fr'),
}
# Aliases for name validation inside PDFs (OCR and publisher variations).
ALIASES={
 'ficommerce':['FICOMMERCE PROXIMITÉ','FICOMMERCE'],
 'efimmo-1':['EFIMMO 1','EFIMMO'],
 'pfo2':['PFO2','PFO₂','PERIAL O2','PERIAL O₂'],
 'pf-grand-paris':['PF GRAND PARIS','PERIAL GRAND PARIS'],
 'patrimmo-croissance':['PATRIMMO CROISSANCE IMPACT','PATRIMMO CROISSANCE'],
 'sofidynamic':['SOFIDYNAMIC'],
 'actipierre-europe':['ACTIPIERRE EUROPE','AEW COMMERCES EUROPE'],
}
# Statuses based on explicit published suspension announcements; do not conflate with the trading price.
LIQUIDITY={
 'primopierre': ('Capital variable suspendu · marché secondaire', '2026-01-07', 'https://www.praemiareim.fr/fr/scpi-primopierre'),
 'primovie': ('Capital variable suspendu · marché secondaire', '2026-06-23', 'https://www.praemiareim.fr/fr/scpi-primovie'),
 'patrimmo-commerce': ('Capital variable suspendu · marché secondaire', '2026-06-25', 'https://www.praemiareim.fr/fr/scpi-patrimmo-commerce'),
 'patrimmo-croissance': ('Capital variable suspendu · marché secondaire', '2026-06-24', 'https://www.praemiareim.fr/fr/scpi-patrimmo-croissance'),
 'lf-grand-paris-patrimoine': ('Capital variable suspendu · marché par confrontation', '2026-06-01', 'https://www.la-francaise.com/fr-fr/investisseur/nos-fonds/actifs-non-cotes/immobilier/scpi.aspx?Scpi=LF-Grand-Paris-Patrimoine&amcScpi=19050&code=Z2'),
 'selectinvest-1': ('Capital variable suspendu · marché par confrontation', '2026-06-01', 'https://www.la-francaise.com/fr-fr/investisseur/nos-fonds/actifs-non-cotes/immobilier/scpi.aspx?Scpi=Selectinvest-1&amcScpi=17357&code=I9'),
 'pf-grand-paris': ('Marché secondaire (PERIAL)', '2026-02-25', 'https://www.perial.com/groupe-perial/actualites/suspension-temporaire-perial-o2-perial-grand-paris'),
 'pfo2': ('Marché secondaire (PERIAL)', '2026-10-28', 'https://www.perial.com/scpi/perial-o2'),
}
