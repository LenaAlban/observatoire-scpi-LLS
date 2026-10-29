# Actualisation SCPI en un clic - activation du service privé

Le code du déclencheur est inclus dans ce dépôt, **mais il ne devient opérationnel qu'après déploiement dans TON compte Cloudflare et configuration de Cloudflare Access**. GitHub Pages n'héberge pas de code serveur et ne doit jamais exposer un jeton GitHub.

## 1. Déployer le Worker

Créer un compte Cloudflare (ou se connecter à l'existant), activer Zero Trust, puis sur un ordinateur disposant de Node.js :

```bash
git clone https://github.com/LenaAlban/observatoire-scpi-LLS.git
cd observatoire-scpi-LLS/worker
npx wrangler login
npx wrangler deploy
```

Noter l'URL de base affichée par Cloudflare, du type `https://observatoire-scpi-refresh.<votre-sous-domaine>.workers.dev`. **Ne pas ajouter `/run`** à l'URL de configuration GitHub.

## 2. Sécuriser avant d'activer le bouton

Dans Cloudflare : **Workers & Pages > observatoire-scpi-refresh > Access > Protect this Worker behind Access**. Choisir **All traffic / production et previews** et une politique Allow contenant **uniquement ton adresse email vérifiée**. Ne pas sélectionner un domaine email entier, « everyone » ou une règle bypass.

Pour que le formulaire POST venant de GitHub Pages fonctionne depuis un domaine différent, conserver **SameSite: None** pour le cookie d'application `CF_Authorization` dans les paramètres avancés de Cloudflare Access (valeur par défaut documentée). Avec `Lax` ou `Strict`, le cookie peut être omis sur un POST intersite et provoquer un nouvel écran de connexion. Le Worker contrôle toujours strictement l'origine et l'identité.

Le code refuse par défaut les appels sans `ctx.access`. Il vérifie aussi l'adresse du compte Access et le domaine d'origine du formulaire avant d'appeler GitHub. Cloudflare demande normalement une connexion au premier passage (ou lorsque la session Access expire) : si cette connexion interrompt l'envoi du formulaire, il suffit de cliquer de nouveau sur « Actualiser » après authentification.

## 3. Configurer les secrets du Worker

Créer dans GitHub un **fine-grained personal access token** limité au seul dépôt `LenaAlban/observatoire-scpi-LLS`, avec les permissions repository **Actions: Read and write** et **Metadata: Read** (implicite). Donner une date d'expiration raisonnable, prévoir son renouvellement. La création manuelle de workflow repose sur cette permission [GitHub Actions API](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event).

Toujours dans le répertoire `worker`, exécuter :

```bash
npx wrangler secret put GH_DISPATCH_TOKEN
npx wrangler secret put OWNER_EMAIL
```

Coller le jeton uniquement à l'invite de la première commande, puis **l'adresse email exacte autorisée par Cloudflare Access** à l'invite de la seconde. **Ne jamais copier de jeton dans l'observatoire, un message, un fichier GitHub ou un paramètre d'URL.**

## 4. Activer le bouton public, sans publier de secret

Sur GitHub : **Settings > Secrets and variables > Actions > Variables > New repository variable**.

- Nom : `SCPI_REFRESH_WORKER_URL`
- Valeur : URL de base du Worker déployé (en HTTPS, sans `/run`).

Relancer le workflow `Observatoire SCPI - actualisation et publication` dans **Actions > Run workflow** afin de republier le site et son fichier public `refresh-config.json`. Ce fichier contient seulement l'URL du Worker, **pas de secret**. Tant que cette variable n'est pas renseignée, le bouton continue d'ouvrir GitHub pour une confirmation manuelle.

## 5. Vérification fonctionnelle

1. Ouvrir l'observatoire, cliquer sur **Actualiser les SCPI**. Le formulaire POST part vers le Worker dans un nouvel onglet.
2. Après connexion Access si nécessaire, le Worker doit afficher « Collecte demandée - GitHub a accepté la demande ». Une réponse 403 signale un accès interdit ; 503 une configuration manquante ; 502 un refus du jeton par GitHub.
3. Le workflow doit démarrer sur `main`. Le site relit le rapport toutes les 20 secondes et n'annonce la fin que lorsque `refreshRequestId` correspond à la demande exacte du bouton.
4. Vérifier le nombre de PDF réellement lus, les statuts et les nouvelles périodes. Le déclenchement ne garantit pas que tous les gérants permettent la récupération des bulletins.

## Sécurité / exploitation

- Cloudflare Access protège l'entrée du Worker ; le Worker vérifie ensuite `ctx.access.getIdentity()`, l'email `OWNER_EMAIL`, la méthode POST, l'origine HTTPS du site, et un UUID de suivi.
- Le code n'expose jamais `GH_DISPATCH_TOKEN`, même lors d'un refus GitHub. Aucun jeton n'est transféré au navigateur.
- Le bouton est utilisable en un clic **après ouverture de session Access** ; lors de la toute première utilisation, un passage par l'authentification peut être nécessaire.
- Les données sont toujours publiées par le workflow GitHub, pas directement par le Worker. La collecte quotidienne à 06:17 UTC reste active.
- Ne pas désactiver Access pour « réparer » une erreur 403. Renouveler le token en cas d'expiration et surveiller les échecs de workflow.

Documentation : [Cloudflare Access Workers](https://developers.cloudflare.com/workers/configuration/cloudflare-access/) · [GitHub workflow dispatch](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event).
