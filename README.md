# Observatoire SCPI — actualisation automatique

Tableau de bord pour **31 SCPI** (liste Spirica transmise, sélection Meilleurtaux et compléments), comprenant : prix de part, valeur de reconstitution, historique, décote/surcote, taux d'occupation, documents, répartitions (si publiées), acquisitions documentées et clés indicatives de démembrement et estimation théorique du délai de retrait des SCPI à capital variable.

## Veille automatique et alertes de fraîcheur

- La rubrique **Veille**, ouverte par défaut, affiche les nouveautés sourcées de `automatedHistory` et de `data/status.json`, les échecs de récupération et les publications à recontrôler.
- **Aucune fausse nouveauté** : le journal des changements ne remonte pas artificiellement les anciennes données préexistantes. Il commence lorsqu'une valeur ou un bulletin est effectivement changé et validé par le robot, puis conserve l'ancienne valeur, la nouvelle, la période, l'heure de contrôle et l'URL justificative.
- `data/status.json` publie les **200 événements récents** (lors de chaque exécution automatique, et non lors d'une simple visite). Les événements sont également conservés, de manière limitée, dans chaque fiche SCPI.
- **Seuils indicatifs de recontrôle**, sans valeur réglementaire : bulletin trimestriel >150 jours, semestriel >250 jours, TOF >210 jours, répartitions >420 jours, reconstitution >540 jours, données de retrait >180 jours ; clé de démembrement sans date signalée. Les dates correspondent à la période publiée et non à la date à laquelle le robot a consulté le site.
- Les filtres distinguent **nouveautés**, **données à recontrôler** et **erreurs / collecte partielle**. Une absence de nouvel événement ne signifie pas qu'aucune publication n'existe chez un gérant qui ne permet pas l'extraction automatique.

## Simulateur d'allocation SCPI (correctif n°5)

- L'onglet **Allocation** permet de saisir un montant d'investissement et jusqu'à **10 SCPI** avec des pondérations indépendantes, strictement positives et totalisant **100 %**. Un bouton répartit les poids à parts égales (ajustement à 0,01 point près).
- Les **montants sont des objectifs de répartition**, calculés comme montant total × pondération, sans conversion en parts entières, frais, fiscalité ou exécution d'ordres.
- Le **TD 2025 pondéré** est calculé sur la somme des contributions de chaque SCPI uniquement si 100 % de l'allocation dispose d'un TD historique exploitable. En cas de données manquantes, le taux global est déclaré **non calculable** et le pourcentage couvert est indiqué. Il ne s'agit jamais d'une prévision de distribution.
- Les répartitions **géographiques et sectorielles consolidées** utilisent les dernières ventilations sourcées et datées. Les légers écarts de somme liés aux arrondis du gérant sont neutralisés par normalisation. La quote-part non documentée reste affichée à part et n'est jamais redistribuée sur les valeurs connues.
- Les localisations infranationales françaises (Paris, Île-de-France, régions, etc.) sont ramenées au groupe **France**. Les grandes zones sans détail (Europe, Étranger) restent distinctes. Les regroupements sectoriels sont conservateurs : par exemple « Santé, hôtellerie et autres » n'est pas attribué arbitrairement à la seule santé.
- La **liquidité** est présentée en poids d'allocation selon la catégorie de sortie ou le statut observé, jamais en un « délai moyen de liquidité ». Les marchés secondaires restent distingués des SCPI à capital variable. Les données anciennes et insuffisantes sont signalées.
- La **synthèse PDF** passe par l'impression du navigateur (choisir « Enregistrer en PDF ») et reproduit les montants, poids, informations agrégées, réserves, dates et liens documentaires.
- **Confidentialité :** la sélection, le montant et les pondérations sont seulement conservés en mémoire pendant la session du navigateur. Ils ne sont pas envoyés au serveur et ne sont pas enregistrés sur le site public. Ne pas saisir de données nominatives de clients.
- Les informations financières, barèmes et modalités de revente sont à confirmer auprès des sociétés de gestion avant toute recommandation ou souscription.

## Fonctionnement

- Le site affiche les données de `data/scpi.json`. Les premières données constituent un **instantané du 28 octobre 2026** et ne doivent pas être confondues avec des données récupérées en temps réel.
- Un workflow GitHub Actions (`.github/workflows/pages.yml`) s'exécute **tous les jours à 06:17 UTC** (07:17 ou 08:17 à Paris selon l'heure d'été). Il essaie de consulter les 31 sources des sociétés de gestion déclarées dans `scripts/official_sources.py`.
- Le programme reconnaît les **nouveaux bulletins** dans les pages publiques. Lorsqu'un lien PDF est clairement identifié, il essaie d'en extraire des indicateurs avec des contrôles stricts. Un prix / une valeur de reconstitution n'est modifié que si la valeur est non ambiguë et sa **date est explicitement retrouvée**. En cas de doute, l'ancienne valeur est conservée, avec une alerte dans `data/status.json`.
- Pour le volet **Liquidité & revente**, le robot recherche dans les PDF officiels le nombre de **parts en attente de retrait**, de **parts effectivement retirées pendant le trimestre** et de **demandes enregistrées**. Il refuse les tableaux multi-périodes ambigus et conserve les chiffres avec leur date et leur source. Aucune estimation n’apparaît si le stock et le flux ne sont pas vérifiables sur la même période. La moyenne sur quatre trimestres n’est accessible que si quatre trimestres consécutifs sont présents.
- **Toutes les données ne sont pas automatiquement interprétables**, notamment les graphiques de répartition, les acquisitions sans texte exploitable, certaines clés de démembrement et les documents protégés contre l'accès automatisé. Le système affiche alors la source et le statut, sans inventer de valeur. Les valeurs initiales peuvent rester anciennes.
- L'interface se recharge à l'ouverture et au clic sur « Actualiser ». Ce clic **recharge le dernier jeu de données produit automatiquement**, il ne télécharge pas directement un bulletin en temps réel. Le site vérifie aussi les données toutes les quatre heures tant qu'il reste ouvert.

## Liquidité & revente : méthodologie prudente

Calcul valable uniquement pour les demandes de retrait sur SCPI **à capital variable** avec retraits compensés :

- **Écoulement théorique de file** (mois) = `3 × parts en attente à la fin du trimestre / parts retirées au cours du trimestre` ;
- **Simulation d'une nouvelle demande** (mois) = `3 × (parts en attente + parts du client) / parts retirées au cours du trimestre` (placement hypothétique derrière la file actuelle) ;
- **Option 4 trimestres** : remplacer le flux trimestriel par la moyenne des quatre derniers trimestres **consécutifs** publiés. Ce n'est pas une garantie de délai.
- S'il manque les données, si le volume de retraits est nul, ou si la SCPI est passée à un marché secondaire avec carnet d'ordres : **aucun délai chiffré** (ou « délai indéterminable »). Ne jamais appliquer la méthode FIFO aux SCPI à capital fixe ou à variabilité suspendue.
- Valeur du stock en attente : `parts en attente × valeur de retrait`, **indicative** et sous réserve de concordance des dates. Ne pas utiliser le prix de souscription à la place du prix de retrait.
- Un client déjà inscrit doit obtenir son **rang effectif** auprès du gérant pour une estimation plus pertinente ; les demandes futures, fonds de remboursement, prix et souscriptions modifient le résultat.

Données sources : bulletins des sociétés de gestion. Pour le mécanisme réglementaire des retraits, voir [AMF](https://www.amf-france.org/fr/espace-epargnants/comprendre-les-produits-financiers/placements-collectifs/scpi-un-autre-moyen-dinvestir-dans-limmobilier) ; pour la formule d'illustration, [Meilleurtaux Placement](https://placement.meilleurtaux.com/scpi/scpi-revente.html).

## Mise en ligne (GitHub Pages)

Suivre **[INSTALLATION_GITHUB_PAS_A_PAS.md](INSTALLATION_GITHUB_PAS_A_PAS.md)**. L'ancienne procédure "Deploy from a branch" a été remplacée par **Settings → Pages → Source : GitHub Actions**. Le workflow fourni effectue lui-même la synchronisation et la publication, et ne nécessite pas d'import PDF manuel lorsque les documents officiels sont accessibles.

## Installer le collecteur ailleurs que GitHub

```bash
pip install -r requirements.txt
python scripts/sync.py
python -m unittest discover -s tests -v
```

Lancer `python scripts/sync.py` chaque jour dans un cron ou un autre ordonnanceur, et servir ce dossier via HTTPS. La collecte est volontairement limitée aux sites officiels configurés et aux documents publics. Certains sites peuvent refuser les robots ou modifier leur structure : le tableau de bord doit alors afficher une panne de synchronisation.

## Périmètre et vigilance professionnelle

- Les libellés « Meilleurtaux Placement » et « Spirica » sont des **informations de référencement**, pas une garantie de commercialisation actuelle ou d'éligibilité dans un contrat particulier. Vérifier les conditions de souscription/UC auprès de l'assureur.
- Les clés de démembrement ne sont importées **que depuis le site propre à la société de gestion**. Les clés précédemment reprises d’un distributeur ont été retirées. Les barèmes publiés sont **indicatifs** : une clé validée à la date d'une source ne constitue pas une cotation en temps réel. Confirmer le barème en vigueur et les possibilités de démembrement auprès du gérant avant toute opération.
- Le *prix de souscription* n'est pas interchangeable avec le *prix d'exécution sur marché secondaire*, notamment pour les SCPI dont la variabilité du capital est suspendue.
- Le taux de distribution (TD) initial affiché correspond à **2025** ; ne pas l'interpréter comme un rendement 2026 garanti.
- Un site hébergé et un ordonnanceur sont nécessaires : **le fichier HTML téléchargé seul ne peut pas mettre à jour les bulletins automatiquement**.


## Fonctions d'analyse et limites (version du 28 octobre 2026)

- **Fiabilité** : un tableau affiche la couverture de huit catégories de données et les statuts de la dernière synchronisation, SCPI par SCPI. La couverture n'est pas une notation de risque et « site accessible » ne garantit pas que les dernières valeurs ont été extraites d'un PDF.
- **Lecture conseil** : chaque fiche SCPI comporte des constats factuels sur la valorisation, le taux de distribution historique, le TOF, la liquidité et les concentrations géographique/sectorielle. Aucune note automatique ne constitue un conseil, une prédiction ou une recommandation personnalisée.
- **Comparateur conseiller (correctif n°4)** : recherche par nom ou société de gestion avec les SCPI Meilleurtaux Placement affichées en premier ; ajout/retrait rapide de **quatre SCPI maximum**. La comparaison regroupe la valorisation, les revenus historiques, la liquidité des parts détenues en direct, les concentrations géographiques et sectorielles (détails complets), les acquisitions documentées et les clés de nue-propriété **à toutes les durées effectivement disponibles**, sans interpolation.
- **Dates et sources** : chaque cellule du tableau comporte sa date de référence et un lien vers sa publication quand il est renseigné. Un prix de confrontation secondaire n'est pas traité comme un prix de souscription et ne génère pas de décote/surcote. Un barème sans date d'effet confirmée est indiqué comme tel.
- **Rapport PDF cohérent** : le bouton « Imprimer / enregistrer en PDF » reprend les mêmes indicateurs, les grilles NP, les répartitions détaillées et les références documentaires via l'impression du navigateur (choisir « Enregistrer en PDF »). Le rapport est factuel, non destiné à remplacer une analyse de conseil.
- **Consultation uniquement** : aucune modification, aucun ajout de SCPI ni import manuel de bulletins depuis l'interface. Les anciennes corrections conservées dans le stockage local des navigateurs sont ignorées pour éviter les différences entre conseillers. Seul le référentiel JSON publié par la collecte officielle est chargé.
- **Collecte renforcée** : le robot suit également les PDF présents derrière une page intermédiaire, contrôle l'identité SCPI et la période du document avant toute actualisation chiffrée, et conserve les valeurs antérieures lorsqu'un document ne peut pas être validé. La traçabilité des changements validés est enregistrée dans `automatedHistory`.
- **Publication quotidienne** : le traitement GitHub Actions continue selon son calendrier. Le bouton « Vérifier les données publiées » ne déclenche pas la collecte : il relit les derniers fichiers déjà publiés.
- **Accès** : bien que l'outil soit destiné aux collaborateurs de l'agence, GitHub Pages est public. Ne publier aucune donnée nominative ou confidentielle ; une restriction d'accès réelle nécessite un hébergement ou un mécanisme d'authentification adapté.
- Les acquisitions documentées ne sont pas exhaustives et les durées de démembrement ne sont pas des barèmes contractuellement garantis. Les sources, périodes, méthodes et limitations de la liquidité doivent être vérifiées avant utilisation professionnelle.

## Fichiers

- `index.html` : interface responsive avec veille et alertes de fraîcheur, tableau de bord, comparateur, fiabilité des données, documentation, fiches SCPI (valorisation, lecture conseil, patrimoine, démembrement, liquidité) et impression d'un rapport PDF depuis le navigateur.
- `data/scpi.json` : référentiel SCPI, historique et preuves conservées.
- `data/status.json` : audit des synchronisations, erreurs de collecte et événements récents sourcés.
- `scripts/sync.py` : collecte et extraction prudente, dont les stocks de retraits et les flux de parts effectivement retirées.
- `scripts/official_sources.py` : 31 sites officiels et alertes de fonctionnement du marché secondaire.
- `tests/` : tests de sécurité URL, détection de périodes, extractions et catalogue.
- `.github/workflows/pages.yml` : ordonnanceur quotidien.


## Prix de part et marché secondaire (mise à jour du 28/10/2026)

Les fiches distinguent le prix de souscription (capital variable), le dernier prix acquéreur de confrontation connu (capital suspendu / secondaire) et un ancien prix de souscription à titre historique lorsque la dernière confrontation n’est pas vérifiable. Aucune ancienne valeur n’est assimilée à un prix de revente actuel. Pour les SCPI en marché secondaire, le ratio prix/reconstitution est neutralisé. Les sources et dates sont conservées dans `data/scpi.json` (`priceSource`, `priceDate`, `priceType`, `previousPriceSource`). Le contrôle quotidien de publication ne vaut pas encore extraction automatique garantie de tous les prix de confrontation, notamment lorsque les marchés sont dynamiques.

## Vérification du référentiel du 28 octobre 2026

- Valeur de reconstitution : **29 SCPI sur 31** renseignées (dates variables), dont une valeur Ficommerce *recalculée* après division des parts par trois. **Deux** restent non renseignées dans le référentiel courant : Edissimmo et Rivoli Avenir Patrimoine.
- Clés de démembrement : **13 SCPI sur 31** possèdent au moins une durée chiffrée dans le référentiel du 28 octobre 2026, avec des sources hétérogènes et des dates qui peuvent être anciennes. L'absence de clé numérique signifie **non documenté dans le référentiel**, pas nécessairement indisponibilité du démembrement.
- Les sources et leurs dates sont détaillées dans `SOURCES_RECONSTITUTION_GESTIONNAIRES.csv` ; le site fournit un lien direct vers la source de chaque valeur reconstitution complétée.
- La collecte des valeurs de reconstitution publiées directement sur des fiches SCPI officielles est désormais prévue, en plus des PDF.
