# Payment review and approval context

Implemented on 4 November 2026. The payment view now combines its deterministic numerical result with an exact excerpt from the existing administrator finance source. No model-generated explanation is used.

## What changed

After an administrator selects a month, **Review & approval policy** appears below the payment table (also for an empty month). It quotes:

> The finance team reviews supplier payments every Friday.
> Payments above 5000 BHD require approval from two administrators.

The excerpt comes from `data/corpus/finance-admin.md`, lines 5–6, document ID `admin-finance` in the existing manifest. **Policy source details** exposes the filename, line range, corpus version, raw-file SHA-256 and manifest SHA-256. The dataset version/hash remains separately visible under calculation details; it identifies the payment records, not the policy.

The interface explicitly states that the records do not show whether approval was obtained. No approval-status field exists in the fixture. October's exact result remains three payments and **18,750.125 BHD**.

## Controls and methodology

`app.payment_policy` reads bounded files under the repository root only after the API's administrator dependency succeeds. It requires one `admin-finance` manifest entry, administrator access, curated trust, a nonempty corpus version and a Markdown path directly inside the corpus. It rejects oversized, missing, malformed or ambiguous source/manifest data.

This first adapter selects one complete, explicitly approved two-line paragraph from the actual file. It does not accept substring matches inside additional claims or interpret instructions elsewhere in the document. If that paragraph changes, it fails closed rather than silently displaying an obsolete rule. This is deliberately a narrow fixture adapter, not a general policy parser or automatic policy understanding system.

`POST /payments/query` now includes a required `policy` object containing the excerpt and provenance. If the expected policy is unavailable, administrators receive HTTP **503** with `Payment policy is unavailable.` and no partial numerical result. Employees still receive generic **403** before either policy or payment storage is accessed. Missing/invalid tokens retain **401**; invalid requests retain **422**. No source-file route or arbitrary document path is exposed.

The frontend validates the policy reference, displays text with safe DOM text nodes and clears the entire combined result on account/month changes, New conversation, failure or disconnect. Numerical values still come from exact integer calculations and are checked against the displayed rows. Policy failure does not fall back to a model's recollection.

The original corpus, manifest, index, models and credentials were preserved. General RAG behavior and administrator access to synthetic markers are unchanged. Selecting only the business paragraph for this operation is not a new global marker-redaction policy.

## Verification and screenshots

- Eight new isolated adapter tests cover exact source bytes/line provenance, policy changes, appended claims, duplicate paragraphs/entries, access/trust/path checks, malformed/oversized/missing files, BOM/CRLF and unrelated instructions.
- Three additional payment API tests cover source provenance, employee/invalid-token denial before policy loading and safe 503 without partial results. All 15 payment API tests and all eight adapter tests passed.
- The separate Chrome verification passed **14 cases, 0 failures, 0 errors**: [browser case report](../results/payment-ui-verification-20261104T203425201Z.json). Nine cases use real API/browser state; five simulate response faults or delay. The added real case checks the exact policy, source/manifest hashes and provenance display. The added simulation rejects a wrongly classified policy reference. Earlier browser assertions remain intact.

| Evidence | Observed result |
| --- | --- |
| [68 — Payments with policy provenance](screenshots/68-payments-with-policy-provenance.png) | Three rows and exact total; Friday/two-administrator quote; expanded source filename, lines and hashes; dataset details |
| [69 — Employee policy boundary](screenshots/69-employee-policy-boundary.png) | Restriction notice; no payment results, policy excerpt, form or provenance; API 403 also verified |

Both images are genuine, visually reviewed component screenshots from separate headless Chrome against the local API. No credentials, private paths or unrelated browser chrome are included. Earlier screenshots and reports remain preserved. Timestamped variants of 64–67 show this later combined view; the original 64–67 remain evidence of the earlier numerical-only milestone.

## Reproduce and maintain

The full extended workflow passed **123 isolated checks**, **3 existing-index authorization checks** and **12 unchanged live RAG development cases**, with **0 failures and 0 errors** in 111.6 seconds. [Workflow report](../results/lab-workflow-20261104T203442939723Z-de882dad.json), [live case report](../results/development-regression-20261104T203502436640Z.json), and [fresh environment snapshot](../results/environment-20261104T203500740652Z.json) are preserved. The administrator synthetic-marker positive control still passes. These RAG cases do not become business-query cases merely because they ran after this change.

All 47 Python source hashes and six frontend/console asset hashes matched the snapshot. The browser report separately records the CJS driver, fixture, policy/manifest hashes, active payment version and screenshot hashes. It was associated with the same snapshot after verifying unchanged source/assets; its capture-after-checks ordering is explicit. Original corpus and manifest hashes remain unchanged. This run predates the 5 November payment compatibility checks.

Reload the existing assistant at `http://127.0.0.1:8001/`, connect as administrator, scroll to **Supplier payments**, select October 2026 and click **View payments**. Expand **Policy source details**. Reconnect as employee to inspect the boundary. Reload clears account state by design.

```powershell
.venv\Scripts\python.exe -m tests.isolated.check_payment_policy
.venv\Scripts\python.exe -m tests.isolated.check_payment_api
.venv\Scripts\python.exe -m tests.live.check_payment_ui
.venv\Scripts\python.exe -m scripts.lab_console --suite extended
```

The browser command requires an installed Node, Playwright and Chrome. Use `--node` and `--node-modules` to point to existing dependencies when they are outside the default search path. See [the browser guide](payment-ui.md) for prerequisites and fixture assumptions.

When an authorized policy revision changes the approved paragraph, review and update the source adapter and corresponding expected tests deliberately, recapture the environment and rerun checks. Do not suppress a 503 by accepting arbitrary replacement text. Policy file hashes are raw-byte hashes and can differ from normalized content hashes used by ingestion.

## Next work

The extended runner now exercises four payment requests in addition to the 12 RAG cases. The three administrator requests verify October (three rows and 18,750.125 BHD), November (one row and 8,000.000 BHD), and December (zero rows and 0.000 BHD). Each checks exact row values and source lines, the active dataset version and hash, and the policy excerpt with its source and manifest hashes. The employee request requires HTTP 403 and the exact generic denial body.

Run `.venv\Scripts\python.exe -m scripts.lab_console --suite extended` with the synthetic fixture active. The runner checks its CSV hash before sending requests and requires the active dataset to match the snapshot at the start and end. The regular regression suite still exercises its nine RAG cases. See [environment capture and compatibility](environment.md#active-payment-dataset-tracking--5-november-2026).

All four payment cases passed in the 5 November extended run. [Case report](../results/development-regression-20261105T103930390851Z.json).
