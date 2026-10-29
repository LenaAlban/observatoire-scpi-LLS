/**
 * Déclencheur privé des collectes de l'Observatoire SCPI.
 * PROTÉGER CE WORKER avec Cloudflare Access (production + previews).
 * Aucun secret GitHub ni identité autorisée ne doit être ajouté au site public.
 */
const SITE_ORIGIN = "https://lenaalban.github.io";
const SITE_URL = SITE_ORIGIN + "/observatoire-scpi-LLS/";
const ACTIONS_URL = "https://github.com/LenaAlban/observatoire-scpi-LLS/actions/workflows/pages.yml";
const API_URL = "https://api.github.com/repos/LenaAlban/observatoire-scpi-LLS/actions/workflows/pages.yml/dispatches";
const REQUEST_ID_RE = /^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));
}

function page(title, detail, status) {
  const ok = status < 400;
  const html = '<!doctype html><html lang="fr"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">' +
    '<title>' + escapeHtml(title) + ' - Observatoire SCPI</title>' +
    '<style>body{background:#f6f4f1;color:#2f2926;font:16px/1.6 system-ui,sans-serif;' +
    'margin:0;display:grid;min-height:100vh;place-items:center}' +
    'main{max-width:570px;background:#fff;border:1px solid #e5dfda;border-radius:16px;' +
    'padding:30px;margin:20px;box-shadow:0 6px 30px #00000008}' +
    'h1{font-size:24px;margin:0 0 10px}a{color:#73472e}p{margin:12px 0}' +
    '.note{font-size:13px;color:#716965}.state{font-weight:700;color:' +
    (ok ? '#20714c' : '#a14436') + '}</style></head><body><main>' +
    '<h1>' + escapeHtml(title) + '</h1><p class="state">' + escapeHtml(detail) + '</p>' +
    '<p><a href="' + SITE_URL + '">Retour à l’observatoire</a></p>' +
    '<p><a href="' + ACTIONS_URL + '" rel="noopener noreferrer">Suivi GitHub Actions</a></p>' +
    '<p class="note">Le lancement ne garantit pas que les 31 bulletins seront accessibles : ' +
    'les erreurs restent visibles dans l’onglet Fiabilité.</p>' +
    '</main></body></html>';
  return new Response(html, {
    status,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
      "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; " +
        "frame-ancestors 'none'; base-uri 'none'; form-action " + SITE_ORIGIN
    }
  });
}

export default {
  async fetch(request, env, ctx) {
    const pathname = new URL(request.url).pathname;
    // Aucune action sur GET, HEAD, OPTIONS ni sur un chemin arbitraire.
    if (pathname !== "/run" || request.method !== "POST") {
      return page("Service d’actualisation", "Utilisez le bouton de l’observatoire.", 405);
    }
    // Refus par défaut si Cloudflare Access n'est pas activé sur CE Worker.
    // Cloudflare valide l'identité et expose ctx.access uniquement si le
    // navigateur s'est correctement authentifié via Access.
    if (!ctx?.access) {
      return page("Accès refusé", "Authentification Cloudflare Access obligatoire.", 403);
    }
    if (request.headers.get("Origin") !== SITE_ORIGIN) {
      return page("Requête refusée", "Lancement autorisé depuis l’observatoire uniquement.", 403);
    }
    if (!env?.OWNER_EMAIL || !env?.GH_DISPATCH_TOKEN) {
      return page("Configuration incomplète", "L’accès sécurisé n’est pas encore configuré.", 503);
    }
    let identity;
    try {
      identity = await ctx.access.getIdentity();
    } catch {
      return page("Accès refusé", "Impossible de vérifier votre identité.", 403);
    }
    if (!identity?.email ||
      identity.email.trim().toLowerCase() !== env.OWNER_EMAIL.trim().toLowerCase()) {
      return page("Accès refusé", "Ce compte n’est pas autorisé à lancer la collecte.", 403);
    }
    let form;
    try {
      form = await request.formData();
    } catch {
      return page("Requête incorrecte", "Formulaire de lancement invalide.", 400);
    }
    const requestId = form.get("request_id");
    if (typeof requestId !== "string" || !REQUEST_ID_RE.test(requestId)) {
      return page("Requête incorrecte", "Identifiant de collecte invalide.", 400);
    }
    try {
      const github = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + env.GH_DISPATCH_TOKEN,
          "Accept": "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "Content-Type": "application/json",
          "User-Agent": "observatoire-scpi-refresh"
        },
        body: JSON.stringify({ ref: "main", inputs: { request_id: requestId } }),
      });
      if (github.status !== 204 && github.status !== 200) {
        return page("Lancement refusé", "GitHub n’a pas accepté la demande (HTTP " +
          github.status + "). Vérifiez les permissions du jeton.", 502);
      }
      return page("Collecte demandée", "GitHub a accepté la demande. " +
        "Retournez à l’observatoire : il vérifiera la publication de cette collecte.", 200);
    } catch {
      return page("Service indisponible", "Impossible de contacter GitHub pour le moment.", 502);
    }
  }
};
