/* Real local API + optional browser-response simulations, explicitly labelled. */
const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const ROOT = path.resolve(__dirname, "../..");
const stamp = new Date().toISOString().replace(/[-:.]/g, "");
const screenshots = [];
const results = [];
let browser;
let dataset;
let policy;
let phase = "browser-startup";
const base = "http://127.0.0.1:8001";
const credentials = { admin: process.env.PAYMENT_UI_ADMIN_TOKEN, employee: process.env.PAYMENT_UI_EMPLOYEE_TOKEN };

async function check(id, kind, action) {
  phase = id;
  const started = performance.now();
  try {
    await action();
    results.push({ case_id: id, kind, status: "pass", elapsed_ms: +(performance.now() - started).toFixed(3), failed_checks: [] });
    console.log(`PASS | ${id}`);
  } catch (error) {
    results.push({ case_id: id, kind, status: "fail", elapsed_ms: +(performance.now() - started).toFixed(3), failed_checks: [id], error: error.name });
    throw error;
  }
}
async function capture(page, number, name) {
  const folder = path.join(ROOT, "docs/screenshots");
  // Preserve earlier evidence when rerunning the same numbered case.
  const standard = `${number}-${name}.png`;
  const filename = fs.existsSync(path.join(folder, standard)) ? `${number}-${name}-${stamp}.png` : standard;
  await page.locator(".payments-panel").screenshot({ path: path.join(folder, filename) });
  screenshots.push({ file: `docs/screenshots/${filename}`, case_id: phase, kind: "real-local-api", sha256: crypto.createHash("sha256").update(fs.readFileSync(path.join(folder, filename))).digest("hex") });
}
async function login(page, role) {
  await page.getByRole("button", { name: "Connect account", exact: true }).click();
  await page.getByLabel("Access token", { exact: true }).fill(credentials[role]);
  await page.getByRole("button", { name: "Connect to ExampleCo", exact: false }).click();
  await page.getByRole("button", { name: role === "admin" ? "Administrator · Disconnect" : "Employee · Disconnect", exact: true }).waitFor();
}
async function loadMonth(page, month) {
  await page.getByLabel("Payment month", { exact: true }).fill(month);
  await page.getByRole("button", { name: "View payments", exact: false }).click();
  await page.locator("#payments-status").filter({ hasText: `Showing ${month}` }).waitFor();
}
async function main() {
  if (!credentials.admin || !credentials.employee) throw new Error("Missing test prerequisites");
  browser = await chromium.launch({ channel: "chrome", headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
  const page = await context.newPage();
  await page.goto(base);
  await check("signed-out-access-boundary", "real-local-api", async () => {
    assert.equal(await page.locator("#payments-form").isVisible(), false);
    assert.match(await page.locator("#payments-access").innerText(), /Connect an administrator/);
  });
  await check("administrator-october-result", "real-local-api", async () => {
    await login(page, "admin");
    const response = page.waitForResponse(r => r.url() === base + "/payments/query" && r.status() === 200);
    await loadMonth(page, "2026-10");
    const data = await (await response).json(); dataset = data.dataset; policy = data.policy;
    assert.equal(data.total_bhd, "18750.125");
    assert.deepEqual(data.rows.map(r => r.payment_id), ["PAY-001", "PAY-003", "PAY-004"]);
    assert.equal(await page.locator(".payments-table tbody tr").count(), 3);
    assert.match(await page.locator(".payments-summary").innerText(), /18,750\.125 BHD/);
    await page.getByText("Dataset & calculation details", { exact: true }).click();
    assert.match(await page.locator(".payment-provenance").innerText(), new RegExp(dataset.version));
    await capture(page, 64, "admin-payment-results");
  });
  await check("administrator-source-grounded-policy", "real-local-api", async () => {
    assert.equal(policy.document_id, "admin-finance");
    assert.equal(policy.source_sha256, crypto.createHash("sha256").update(fs.readFileSync(path.join(ROOT, "data/corpus/finance-admin.md"))).digest("hex"));
    assert.equal(policy.manifest_sha256, crypto.createHash("sha256").update(fs.readFileSync(path.join(ROOT, "data/manifest.json"))).digest("hex"));
    assert.equal(policy.excerpt, "The finance team reviews supplier payments every Friday.\nPayments above 5000 BHD require approval from two administrators.");
    assert.match(await page.locator(".payment-policy").innerText(), /These records do not show whether approval was obtained/);
    await page.getByText("Policy source details", { exact: true }).click();
    assert.match(await page.locator(".payment-policy").innerText(), new RegExp(policy.source_sha256));
    await capture(page, 68, "payments-with-policy-provenance");
  });
  await check("administrator-empty-month", "real-local-api", async () => {
    await loadMonth(page, "2026-12");
    assert.match(await page.locator(".payments-summary").innerText(), /0\.000 BHD/);
    assert.equal(await page.locator(".payments-table").count(), 0);
    assert.equal(await page.locator(".payment-policy").count(), 1);
    await capture(page, 65, "payments-empty-month");
  });
  await check("mobile-payment-view", "real-local-api", async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    await loadMonth(page, "2026-10");
    const region = page.getByRole("region", { name: "Payment records; scroll horizontally on small screens" });
    assert.equal(await region.isVisible(), true);
    assert.match(await page.locator(".payments-summary").innerText(), /18,750\.125 BHD/);
    await capture(page, 67, "payments-mobile-view");
    await page.setViewportSize({ width: 1440, height: 1100 });
  });
  await check("employee-switch-clears-finance-results", "real-local-api", async () => {
    await page.getByRole("button", { name: "Administrator · Disconnect", exact: true }).click();
    assert.equal(await page.locator("#payments-result").innerText(), "");
    await login(page, "employee");
    assert.equal(await page.locator("#payments-form").isVisible(), false);
    assert.equal(await page.locator(".payments-table").count(), 0);
    assert.match(await page.locator("#payments-access").innerText(), /restricted to administrator/);
    assert.equal(await page.locator(".payment-policy").count(), 0);
    await capture(page, 66, "employee-payment-boundary");
    await capture(page, 69, "employee-policy-boundary");
    const response = await context.request.post(base + "/payments/query", {
      headers: { Authorization: `Bearer ${credentials.employee}` },
      data: { operation: "supplier_payments_above_threshold", month: "2026-10" },
    });
    assert.equal(response.status(), 403);
    assert.deepEqual(await response.json(), { detail: "Access denied." });
    await page.getByRole("button", { name: "Employee · Disconnect", exact: true }).click();
    await login(page, "admin");
  });
  await check("unavailable-service-clears-old-results-and-recovers", "simulated-browser-response", async () => {
    await loadMonth(page, "2026-10");
    await page.route("**/payments/query", route => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Payment data is unavailable." }) }));
    await page.getByRole("button", { name: "View payments", exact: false }).click();
    await page.locator("#payments-status").filter({ hasText: "Payment data is unavailable" }).waitFor();
    assert.equal(await page.locator("#payments-result").innerText(), "");
    assert.equal(await page.locator("#payments-submit").isEnabled(), true);
    await page.unroute("**/payments/query");
    await loadMonth(page, "2026-10");
  });
  await check("supplier-markup-is-text", "simulated-browser-response", async () => {
    await page.route("**/payments/query", async route => {
      const response = await route.fetch(); const data = await response.json();
      data.rows[0].supplier_name = '<img src=x onerror="alert(1)">';
      await route.fulfill({ response, json: data });
    });
    await loadMonth(page, "2026-10");
    assert.equal(await page.locator(".payments-table img").count(), 0);
    assert.match(await page.locator(".payments-table").innerText(), /<img src=x/);
    await page.unroute("**/payments/query");
  });
  await check("inconsistent-total-is-rejected", "simulated-browser-response", async () => {
    await page.route("**/payments/query", async route => {
      const response = await route.fetch(); const data = await response.json(); data.total_bhd = "1.000";
      await route.fulfill({ response, json: data });
    });
    await page.getByRole("button", { name: "View payments", exact: false }).click();
    await page.locator("#payments-status").filter({ hasText: "total does not match" }).waitFor();
    assert.equal(await page.locator("#payments-result").innerText(), "");
    await page.unroute("**/payments/query");
  });
  await check("invalid-policy-reference-is-rejected", "simulated-browser-response", async () => {
    await page.route("**/payments/query", async route => {
      const response = await route.fetch(); const data = await response.json(); data.policy.access_level = "employee";
      await route.fulfill({ response, json: data });
    });
    await page.getByRole("button", { name: "View payments", exact: false }).click();
    await page.locator("#payments-status").filter({ hasText: "invalid policy reference" }).waitFor();
    assert.equal(await page.locator("#payments-result").innerText(), "");
    await page.unroute("**/payments/query");
  });
  await check("disconnect-during-request-discards-delayed-result", "simulated-browser-delay", async () => {
    let release;
    const gate = new Promise(resolve => { release = resolve; });
    let reached;
    const arrived = new Promise(resolve => { reached = resolve; });
    await page.route("**/payments/query", async route => {
      const response = await route.fetch(); reached(); await gate;
      try { await route.fulfill({ response }); } catch (_) { /* Aborted by disconnect. */ }
    });
    await page.getByRole("button", { name: "View payments", exact: false }).click();
    await arrived;
    await page.getByRole("button", { name: "Administrator · Disconnect", exact: true }).click();
    release(); await page.unrouteAll({ behavior: "wait" });
    assert.equal(await page.locator("#payments-result").innerText(), "");
    assert.equal(await page.locator("#payments-form").isVisible(), false);
    await login(page, "employee");
    assert.equal(await page.locator(".payments-table").count(), 0);
  });
  await check("reload-clears-account-and-finance-data", "real-browser-state", async () => {
    await page.reload();
    assert.equal(await page.getByRole("button", { name: "Connect account", exact: true }).isVisible(), true);
    assert.equal(await page.locator("#payments-result").innerText(), "");
    assert.equal(await page.locator("#payments-form").isVisible(), false);
  });
  await check("month-change-clears-results", "real-browser-state", async () => {
    await login(page, "admin");
    await loadMonth(page, "2026-10");
    await page.getByLabel("Payment month", { exact: true }).fill("2026-11");
    await page.getByLabel("Payment month", { exact: true }).blur();
    assert.equal(await page.locator("#payments-result").innerText(), "");
  });
  await check("new-conversation-clears-finance-results", "real-browser-state", async () => {
    await loadMonth(page, "2026-10");
    await page.getByRole("button", { name: "＋ New conversation", exact: true }).click();
    assert.equal(await page.locator("#payments-result").innerText(), "");
    assert.equal(await page.locator("#payments-form").isVisible(), true);
  });
  await context.close();
}
main().catch(error => {
  // Never print Playwright call logs: login failures may contain input values.
  console.log(`Browser verification stopped at ${phase}: ${error.name}`);
  if (!results.some(r => r.status === "fail")) results.push({ case_id: phase, status: "error", error: error.name, failed_checks: [] });
  process.exitCode = 1;
}).finally(async () => {
  if (browser) await browser.close();
  const counts = Object.fromEntries(["pass", "fail", "error"].map(status => [status, results.filter(r => r.status === status).length]));
  const filename = `payment-ui-verification-${stamp}.json`;
  const artifacts = ["app/static/index.html", "app/static/assistant.js", "app/static/assistant.css", "app/payment_policy.py", "data/corpus/finance-admin.md", "data/manifest.json", "tests/live/check_payment_ui.py", "tests/live/check_payment_ui.cjs", "tests/fixtures/supplier-payments.csv"];
  const source_artifact_sha256 = Object.fromEntries(artifacts.map(file => [file, crypto.createHash("sha256").update(fs.readFileSync(path.join(ROOT, file))).digest("hex")]));
  fs.writeFileSync(path.join(ROOT, "results", filename), JSON.stringify({ run_type: "payment-ui-development-verification", base_url: base, dataset, policy, counts, results, screenshots, source_artifact_sha256, limitations: ["Known synthetic development fixture, not a held-out benchmark.", "Screenshots are genuine component captures from separate headless Chrome against the local API.", "Response simulations and delays are labelled per case; no simulated screenshot evidence is saved.", "No model-generated explanation was tested; policy is an exact approved source excerpt."] }, null, 2));
  console.log(`Report: results/${filename}`); console.log(JSON.stringify(counts));
});
