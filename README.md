# Observatoire SCPI — actualisation automatique

Tableau de bord pour **31 SCPI** (liste Spirica transmise, sélection Meilleurtaux et compléments), comprenant : prix de part, valeur de reconstitution, historique, décote/surcote, taux d'occupation, documents, répartitions (si publiées), acquisitions documentées et clés indicatives de démembrement et estimation théorique du délai de retrait des SCPI à capital variable.

## Veille automatique et alertes de fraîcheur

- La rubrique **Veille**, placée en dernier dans le menu (l'**Observatoire** est la page d'accueil), affiche les nouveautés sourcées de `automatedHistory` et de `data/status.json`, les échecs de récupération et les publications à recontrôler.
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

## Fiabilité renforcée du référentiel (correctif n°6)

- **Plusieurs points d'entrée du même gérant** : l'actualisation essaie l'URL officielle configurée, le domaine HTTPS sans « www » si pertinent, puis les pages de documentation déjà connues et hébergées sur le domaine de l'éditeur. Aucune désactivation de la vérification TLS et aucune URL de domaine tiers n'est admise comme voie de secours.
- **PDF officiel et identité vérifiés** : la récupération d'une page HTML ne vaut pas lecture d'un PDF. Les mises à jour automatiques provenant d'un bulletin exigent un contrôle du fonds, de la période lorsque celle-ci figure dans le document, et du domaine autorisé. Un PDF déjà documenté peut être utilisé lorsque la page du gérant est momentanément inaccessible.
- **Écriture atomique par SCPI** : l'extraction est faite dans une copie de la fiche. Une date future, un recul de période, une valeur hors plage, une répartition qui ne totalise pas 100 %, une clé NP non monotone, un volume de parts invalide ou une source non approuvée entraîne le **rejet intégral des nouvelles modifications de cette fiche**. Les anciennes données restent intactes.
- **Répartitions** : les ventilations extraites automatiquement exigent un total compris entre 99 et 101 % et conservent leurs propres dates et liens documentaires, y compris lorsque leur source est une page HTML officielle.
- **Audit non destructif** : les anciennes fiches sont contrôlées sans effacer des chiffres historiques. Le rapport `data/status.json` contient `quality` (dates, sources, ancienneté indicative, incohérences par SCPI), `rejectedUpdates`, `fallbackRecovered` ainsi que les voies de collecte effectivement tentées pour chaque SCPI.
- **Interface Fiabilité** : filtres « anomalies », « données anciennes » et « modifications rejetées » ; détail des avertissements et des sources consultées. Le panneau d'audit apparaît **après l'exécution du nouveau robot** (il n'est pas rempli artificiellement à partir des anciennes données).
- **Limites** : des sites peuvent continuer à refuser les robots, et des tableaux PDF fondés sur des images ne sont pas convertis par reconnaissance visuelle approximative. Aucun taux ni aucune clé de démembrement n'est extrapolé pour combler une lacune.

## TD annuels : gestion automatique des millésimes (correctif n°7)

- La collecte PDF n'est plus limitée au TD 2025. Elle recherche un **taux de distribution annuel**, explicitement associé à une année civile clôturée. Les taux provisoires, objectifs, estimations et annualisations trimestrielles sont exclus. La prochaine année (2026) peut être prise en compte à partir de 2027, si une publication officielle exploitable l'indique.
- `tdHistory` contient les taux historiques par année avec **valeur, millésime, période, lien justificatif, méthode et extrait probant**. Les TD du référentiel existant sont automatiquement migrés à partir de leur millésime connu (2025 pour les anciens champs historiques qui n'avaient pas d'année explicite), sans inventer une nouvelle source.
- Les valeurs nouvelles ne remplacent pas les années antérieures. **Deux TD contradictoires pour le même millésime** sont conservés comme conflit à vérifier (`tdConflicts`) et ne sont pas arbitrés automatiquement. La valeur affichée `td` et son millésime `tdYear` évoluent uniquement lorsqu'une année civile plus récente est confirmée.
- Le validateur refuse une **année non terminée**, un changement de millésime incohérent, une nouvelle entrée sans source officielle autorisée ou l'effacement d'un millésime historique.
- Tableaux, fiches individuelles et comparateur indiquent l'année du TD et proposent les archives disponibles. Le comparateur présente les années côte à côte et ne transforme pas des taux de millésimes différents en un seul indicateur.
- Le **simulateur d'allocation** recherche d'abord le dernier millésime commun à toutes les SCPI sélectionnées. Si aucun millésime commun n'est disponible pour toute l'allocation, il affiche **TD global non calculable**, la couverture du millésime choisi et une alerte, plutôt que mélanger les années ou extrapoler des chiffres absents.
- Les synthèses imprimées et le CSV indiquent désormais les millésimes. Le TD reste historique, sans garantie de rendement futur.

## Graphiques historiques et comparaison des trajectoires (correctif n°8)

- L'onglet **Évolution** donne accès aux séries **prix de part, reconstitution, TOF, TD annuel, parts en attente et retraits exécutés par trimestre**. La fiche SCPI ouvre directement ses graphiques.
- Le robot reconstruit progressivement `indicatorHistory` depuis les données datées et vérifiées du référentiel ; les nouvelles mesures y sont ajoutées automatiquement **après validation** de leur publication. Les archives de reconstitution déjà recensées (`history`), l'ancien prix daté, l'historique des TD (`tdHistory`) et les retraits trimestriels recensés (`withdrawals4Q`) sont repris **sans inventer les sources manquantes**.
- Chaque point contient une **date de référence, une valeur et éventuellement l'URL justificative**. Les archives sans provenance précise restent identifiées comme telles. Les données de périodes contradictoires ne s'écrasent pas : l'anomalie est conservée dans `historyConflicts`.
- Les séries sont limitées à **48 observations par indicateur** et triées par date. Les variations comparent uniquement les **deux derniers points réellement datés**, avec leurs dates.
- Les courbes ne sont **pas prolongées** au-delà des observations. Les segments sont interrompus si l'intervalle entre deux points excède celui normalement attendu (125 jours pour TOF, liquidité ; 400 jours pour TD annuels, reconstitution et prix publiés). Un seul point donne un marqueur, **aucune tendance**.
- Les comparaisons réunissent **jusqu'à 4 SCPI**, avec un **indice base 100 calculé seulement à partir d'une date exactement commune et de valeurs positives**. Sans date commune, le site explique pourquoi la comparaison est indisponible plutôt que fabriquer un point de départ. Les périodes manquantes ne sont pas interpolées.
- Sur une SCPI à marché secondaire, les **anciens prix de souscription** sont exclus de la série des prix de confrontation afin de ne pas afficher une évolution trompeuse.
- Aucune correction manuelle des données officielles : les données sont mises à jour par la collecte quotidienne. Une source inaccessible ou un bulletin non interprétable ne crée pas de point historique.

## Correctif de collecte suite au contrôle du 28 octobre 2026

Les erreurs affichées sur **Edissimmo, Efimmo 1, Immorente, Sofidynamic, Sofidy Europe Invest et Altixia Cadence XII** étaient des résultats de la collecte du 28/10/2026, antérieurs aux ajustements de découverte documentaire. Les tests et le déploiement du site ne prouvent pas, à eux seuls, que les domaines des gérants sont de nouveau accessibles.

- Les chemins de secours documentaires sont explicitement configurés pour **Amundi Immobilier, Sofidy et Altixia**, toujours sur leurs propres domaines HTTPS. Le robot peut désormais examiner certains documents PDF connus même si la page de catalogue n'est pas disponible, après vérification de la SCPI, de la nature « bulletin trimestriel » et de la période effectivement imprimée.
- Le robot examine un nombre limité de liens PDF dont le nom ne contient pas de trimestre (notamment les URL « doc1 » d'Altixia), sans les présenter comme fiables avant lecture de leur contenu.
- Les erreurs **503 / certificat TLS / délai de réponse / refus d'accès** sont classées et affichées de façon compréhensible. Une erreur de certificat n'est **jamais contournée** par la désactivation de la vérification SSL. Le même hôte dont le certificat a été rejeté n'est pas interrogé en boucle.
- L'onglet **Veille** et l'onglet **Fiabilité** masquent également les anciennes traces brutes `HTTPSConnectionPool` déjà présentes dans `data/status.json`. Les fiches indiquent la dernière période documentée dans le référentiel, sans confondre celle-ci avec une nouvelle collecte réussie.
- **Limite vérifiable** : la réussite des tests unitaires et de GitHub Pages ne signifie pas que l'éditeur a réparé son HTTP 503 ou sa chaîne de certificats. Le résultat réel des tentatives de secours est mesuré lors de la **prochaine exécution automatique** ; les dernières données fiables restent conservées jusque-là.

## Actualisation à la demande depuis le site

- Le bouton **Actualiser maintenant** fonctionne en mode sécurisé dès que le Worker Cloudflare privé est déployé et que sa variable d'URL GitHub est renseignée. Dans ce cas, **un seul clic** envoie un formulaire POST au Worker, après éventuelle authentification Cloudflare Access. Le Worker vérifie l'identité avant de déclencher `workflow_dispatch` : **aucun jeton GitHub n'est présent dans le site public**.
- Chaque demande possède un **UUID de suivi**. Le workflow enregistre `refreshRequestId` dans `data/status.json` ; le navigateur ne confirme la fin que lorsque la publication correspond exactement à sa demande, sans confondre avec la collecte quotidienne.
- **Sans Worker activé**, le même bouton ouvre la page [GitHub Actions](https://github.com/LenaAlban/observatoire-scpi-LLS/actions/workflows/pages.yml) et demande une confirmation **Run workflow**. C'est le mode de secours, sans secret ni authentification supplémentaire.
- Le contrôle du référentiel publié s'effectue toutes les **20 secondes**, pendant **46 minutes maximum** tant que la page reste active. **Vérifier les résultats** recharge le dernier état publié sans lancer de collecte ; les erreurs PDF et données anciennes restent visibles.
- Le déclencheur GitHub existant traite les **31 SCPI**, conserve les validations strictes des sources et republie les fichiers JSON après contrôle. La collecte quotidienne reste active.
- **Activation nécessaire :** suivre [worker/README.md](worker/README.md) pour créer le Worker, activer Cloudflare Access, configurer ses deux secrets et la variable GitHub `SCPI_REFRESH_WORKER_URL`. Le code est présent dans le dépôt ; tant que cette configuration externe n'est pas faite, le mode un clic reste indisponible.

## Fonctionnement

- Le site affiche les données de `data/scpi.json`. Les premières données constituent un **instantané du 28 octobre 2026** et ne doivent pas être confondues avec des données récupérées en temps réel.
- Un workflow GitHub Actions (`.github/workflows/pages.yml`) s'exécute **tous les jours à 06:17 UTC** (07:17 ou 08:17 à Paris selon l'heure d'été). Il essaie de consulter les 31 sources des sociétés de gestion déclarées dans `scripts/official_sources.py`.
- Le programme reconnaît les **nouveaux bulletins** dans les pages publiques. Lorsqu'un lien PDF est clairement identifié, il essaie d'en extraire des indicateurs avec des contrôles stricts. Un prix / une valeur de reconstitution n'est modifié que si la valeur est non ambiguë et sa **date est explicitement retrouvée**. En cas de doute, l'ancienne valeur est conservée, avec une alerte dans `data/status.json`.
- Pour le volet **Liquidité & revente**, le robot recherche dans les PDF officiels le nombre de **parts en attente de retrait**, de **parts effectivement retirées pendant le trimestre** et de **demandes enregistrées**. Il refuse les tableaux multi-périodes ambigus et conserve les chiffres avec leur date et leur source. Aucune estimation n’apparaît si le stock et le flux ne sont pas vérifiables sur la même période. La moyenne sur quatre trimestres n’est accessible que si quatre trimestres consécutifs sont présents.
- **Toutes les données ne sont pas automatiquement interprétables**, notamment les graphiques de répartition, les acquisitions sans texte exploitable, certaines clés de démembrement et les documents protégés contre l'accès automatisé. Le système affiche alors la source et le statut, sans inventer de valeur. Les valeurs initiales peuvent rester anciennes.
- L'interface charge les données à l'ouverture. « Vérifier les résultats » recharge les données publiées ; « Actualiser maintenant » lance un traitement via le Worker sécurisé si celui-ci est activé, ou ouvre le lancement manuel GitHub en mode de secours. Le site vérifie aussi les données toutes les quatre heures tant qu'il reste ouvert.

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
