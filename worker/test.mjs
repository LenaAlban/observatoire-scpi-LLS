import test from "node:test";
import assert from "node:assert/strict";
import worker from "./src/index.mjs";

const ID = "4a552c5b-9dc0-4e66-a208-0d66d3a522ff";
const ORIGIN = "https://lenaalban.github.io";
const ENV = { OWNER_EMAIL: "proprietaire@example.org", GH_DISPATCH_TOKEN: "secret-test" };
const ACCESS = { access: { getIdentity: async () => ({ email: "proprietaire@example.org" }) } };
function post(id = ID, origin = ORIGIN, method = "POST") {
  return new Request("https://scpi-refresh.example.workers.dev/run", {
    method,
    headers: { Origin: origin, "Content-Type": "application/x-www-form-urlencoded" },
    ...(method === "POST" ? { body: new URLSearchParams({ request_id: id }) } : {})
  });
}
test("refuse toute requête sans contexte Cloudflare Access", async () => {
  const res = await worker.fetch(post(), ENV, {});
  assert.equal(res.status, 403);
});
test("refuse les requêtes GET, même avec Access", async () => {
  const res = await worker.fetch(post(ID, ORIGIN, "GET"), ENV, ACCESS);
  assert.equal(res.status, 405);
});
test("refuse les origines externes (protection CSRF)", async () => {
  const res = await worker.fetch(post(ID, "https://malicious.example"), ENV, ACCESS);
  assert.equal(res.status, 403);
});
test("refuse une identité non autorisée", async () => {
  const res = await worker.fetch(post(), ENV, {
    access: { getIdentity: async () => ({ email: "intrus@example.org" }) }
  });
  assert.equal(res.status, 403);
});
test("échoue fermé quand les secrets ne sont pas définis", async () => {
  const res = await worker.fetch(post(), {}, ACCESS);
  assert.equal(res.status, 503);
});
test("refuse les identifiants de demande invalides", async () => {
  const res = await worker.fetch(post("foo"), ENV, ACCESS);
  assert.equal(res.status, 400);
});
test("déclenche seulement le workflow autorisé avec l'identifiant demandé", async () => {
  const previous = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async (url, init) => {
    calls++;
    assert.equal(url, "https://api.github.com/repos/LenaAlban/observatoire-scpi-LLS/actions/workflows/pages.yml/dispatches");
    assert.equal(init.method, "POST");
    assert.deepEqual(JSON.parse(init.body), { ref: "main", inputs: { request_id: ID } });
    assert.equal(init.headers.Authorization, "Bearer secret-test");
    return new Response(null, { status: 204 });
  };
  try {
    const res = await worker.fetch(post(), ENV, ACCESS);
    assert.equal(res.status, 200);
    assert.equal(calls, 1);
    assert.match(await res.text(), /GitHub a accepté la demande/);
  } finally {
    globalThis.fetch = previous;
  }
});
test("ne déclare pas la collecte lancée si GitHub refuse", async () => {
  const previous = globalThis.fetch;
  globalThis.fetch = async () => new Response("forbidden", { status: 403 });
  try {
    const res = await worker.fetch(post(), ENV, ACCESS);
    assert.equal(res.status, 502);
  } finally {
    globalThis.fetch = previous;
  }
});
