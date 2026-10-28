# Observatoire SCPI — actualisation automatique

Tableau de bord pour **31 SCPI** (liste Spirica transmise, sélection Meilleurtaux et compléments), comprenant : prix de part, valeur de reconstitution, historique, décote/surcote, taux d'occupation, documents, répartitions (si publiées), acquisitions documentées et clés indicatives de démembrement et estimation théorique du délai de retrait des SCPI à capital variable.

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
- **Comparateur et fiche PDF** : jusqu'à quatre SCPI et leurs dates de référence sont reprises dans un tableau ; le bouton « Imprimer / enregistrer en PDF » ouvre la fonction d'impression du navigateur. Sélectionner « Enregistrer en PDF » dans le dialogue d'impression pour obtenir le fichier.
- **Corrections locales persistantes** : les champs modifiés manuellement dans le navigateur sont conservés dans son **localStorage** et restent visibles après la synchronisation officielle ; un avertissement apparaît dans la fiche et les valeurs peuvent être réinitialisées. La sauvegarde et la restauration JSON permettent une copie manuelle. Le fichier exporté peut contenir des notes personnelles : le conserver dans un espace privé.
- **Attention** : ces corrections ne sont **ni enregistrées sur GitHub**, ni partagées entre navigateurs/appareils, ni synchronisées sur le serveur. Elles ne sont pas protégées par un accès authentifié côté navigateur. Ne pas y inscrire de données nominatives ou confidentielles de clients. Une synchronisation multi-appareils exigerait un backend privé, une authentification et une gestion explicite des accès.
- Les acquisitions documentées ne sont pas exhaustives et les durées de démembrement ne sont pas des barèmes contractuellement garantis. Les sources, périodes, méthodes et limitations de la liquidité doivent être vérifiées avant utilisation professionnelle.

## Fichiers

- `index.html` : interface responsive avec tableau de bord, comparateur, fiabilité des données, documentation, fiches SCPI (valorisation, lecture conseil, patrimoine, démembrement, liquidité) et impression d'un rapport PDF depuis le navigateur.
- `data/scpi.json` : référentiel SCPI, historique et preuves conservées.
- `data/status.json` : audit des synchronisations et échecs.
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
