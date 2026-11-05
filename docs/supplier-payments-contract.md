# Supplier-payment feature contract

Status: CSV validation, local JSON preview, versioned SQLite storage, atomic activation, the administrator-only structured query and a payment view below the chat are implemented on 4 November 2026. A source-grounded review/approval excerpt is now included; natural-language routing, model explanations and exports remain unimplemented. See [policy provenance and evidence](payment-policy.md). See [interface usage and numbered evidence](payment-ui.md).

## Goal and first question

“Show supplier payments above 5,000 BHD in October 2026, their total, and the approval policy.”

The first vertical slice combines a deterministic authorized payment query with the existing policy source. Success means the administrator receives the exact permitted rows and total, with traceable data and policy references. Employee requests must not disclose finance records, totals or policy text restricted to administrators.

The authoritative existing policy is `data/corpus/finance-admin.md`, document ID `admin-finance`: reviews occur every Friday and payments above 5000 BHD require approval from two administrators. The current corpus does not establish whether an individual payment actually received approval. The answer must not claim that it did.

## Access matrix

| Operation | Employee | Administrator |
| --- | --- | --- |
| Existing employee document questions | Existing behavior | Existing behavior |
| View supplier-payment rows or aggregates | Denied | Allowed for this synthetic demo |
| View administrator finance policy | Existing retrieval restriction | Existing permission |
| Import or replace a payment dataset | Denied | Proposed administrator-only operation |
| Set role through a request or document | Never | Never |

Reuse server-assigned roles from `app.auth`; do not introduce finance-role claims supplied by the browser. Authorization must run before data access and calculation, including empty-result requests. Existing `/query` HTTP behavior, administrator access to synthetic markers and the five original corpus fixtures remain unchanged.

## Dataset contract

Initial input: a UTF-8 CSV containing only invented companies and payment records, stored separately from the existing corpus and manifest. The synthetic fixture is `tests/fixtures/supplier-payments.csv`. The local import command supports persistent activation; Excel support remains a later step.

| Field | Rule |
| --- | --- |
| `payment_id` | Required unique ID, 1–64 ASCII letters, digits, underscores or hyphens |
| `supplier_name` | Required text, 1–120 characters; treated as untrusted display data |
| `payment_date` | Valid ISO date `YYYY-MM-DD`; calendar date without time-zone conversion |
| `amount_bhd` | Positive decimal, at most three decimal places; no exponent, grouping separator, NaN or infinity |

Currency is fixed to BHD for this version. The validator rejects unknown/missing/duplicate columns, duplicate IDs, malformed rows and an empty dataset. Implemented limits: 1 MiB input and 1,000 rows. Amounts accept at most 15 integer digits, allowing exact arithmetic and bounded downstream storage. Supplier names containing control characters are rejected. Values are not silently trimmed; a UTF-8 BOM and reordered columns are accepted. Validation returns every row or raises a safe error without echoing input. The storage layer inserts the version, all rows and active-version pointer in one SQLite transaction; failures roll back together. Reimports create new versions even when source bytes match. Historical dataset/row updates and deletes are blocked by database triggers.

Store amounts as integer thousandths of BHD or exact decimals; never binary floating point. Retain an immutable dataset version, file SHA-256, original row number and import timestamp. Dataset activation must be atomic. Do not overwrite the original RAG corpus or rebuild its Chroma index.

## Query and result contract

Use an explicit approved operation, such as `supplier_payments_above_threshold`, with a validated month (`2026-10`). For the first version the threshold is fixed at 5000.000 BHD. Do not accept model-generated SQL, file paths, role fields or arbitrary operations.

Filter dates from the first day of the selected month, inclusive, to the first day of the next month, exclusive. Compare each individual payment using strict `amount > 5000.000`; do not group payments by supplier before applying the threshold. Sort by date, then payment ID. Return all qualifying rows within the bounded dataset; the displayed total must equal the returned rows' sum.

The structured result must include the operation, month, currency, threshold, row count, exact decimal total as a string, rows, dataset version/hash and row provenance. Cite `admin-finance` for approval-policy statements. A model may explain the approved result but must not compute or modify its numbers. Tables, charts and later exports must use the same authorized result.

For the proposed new structured endpoint: missing/invalid credentials → 401; employee → 403 with a generic denial and no finance metadata; invalid inputs or extra fields → 422; unavailable active dataset → 503 with a safe error. An authorized empty result → 200, zero rows and `0.000` BHD. These new endpoint contracts do not change the existing `/query` response semantics.

## Golden fixture and expected outcomes

All names below are fictional. These rows exist in the isolated test fixture; they have not been imported into an active dataset.

| ID | Supplier | Date | BHD | Included in October query? |
| --- | --- | --- | ---: | --- |
| PAY-001 | Demo Cedar Supplies | 2026-10-01 | 5500.000 | Yes |
| PAY-002 | Demo Harbor Services | 2026-10-10 | 5000.000 | No: equal to threshold |
| PAY-003 | Demo Palm Systems | 2026-10-15 | 7250.125 | Yes |
| PAY-004 | Demo Cedar Supplies | 2026-10-31 | 6000.000 | Yes |
| PAY-005 | Demo Coast Logistics | 2026-09-30 | 9000.000 | No: previous month |
| PAY-006 | Demo Dune Equipment | 2026-11-01 | 8000.000 | No: next month |
| PAY-007 | Demo Cedar Supplies | 2026-10-20 | 3000.000 | No: below threshold |
| PAY-008 | Demo Cedar Supplies | 2026-10-21 | 2500.000 | No: no supplier-level aggregation |

Expected administrator result: IDs `PAY-001`, `PAY-003`, `PAY-004`, in that order; count **3**; total **18750.125 BHD**. Friday review and two-administrator approval requirements come from the policy, not the CSV. An employee receives a denial without these rows, count or total. December 2026 is an authorized empty result.

## Methodology and acceptance checks

1. Implement bounded validation and preview with temporary isolated fixtures. Confirm whole-import rejection and preservation of the previous active version.
2. Add versioned storage and a read-only approved query. Assert exact IDs, order, count, total, boundary dates, threshold equality and empty results against the fixture above.
3. Enforce the access matrix before reading records. Exercise employee, administrator, missing/invalid token and caller role-spoof attempts. Use temporary test credentials.
4. Add the interface only after the structured result works. Render names as text, including an adversarial supplier name containing instructions or markup; it must not execute or change authorization or calculations.
5. Compare every displayed number with the structured result, and verify policy provenance. Reject or safely fall back from explanations that add unsupported numeric claims.
6. Run the existing isolated, actual-index and extended development regression checks unchanged. Capture a fresh environment snapshot after source changes; preserve earlier reports.

Do not record these checks as passed until implemented and executed. A known-fixture pass demonstrates this development contract, not general business or security correctness.

## Evidence and next implementation batch

Screenshots are optional at the owner's request. Once implemented, useful evidence is an administrator result showing the three rows and exact total, an employee denial for the same operation, and a safe invalid-import preview. Never include tokens, private paths or real company data. Save machine-readable checks and dataset provenance alongside any screenshots.

The CSV schema, bounded validation/preview and golden fixture are implemented in `app/payments.py`, `scripts/preview_payments.py` and `tests/isolated/check_payments.py`. Ten isolated tests cover the fixture oracle, invalid fields, exact arithmetic, schema/encoding, duplicate and late invalid rows, limits, untrusted text and CLI behavior. No HTTP route is exposed; future HTTP callers must authorize before supplying data to the validator. The CLI is a local maintenance tool under the operating-system user's access, not a substitute for API authorization.

Run from the repository root:

```powershell
.venv\Scripts\python.exe -m scripts.preview_payments tests/fixtures/supplier-payments.csv
.venv\Scripts\python.exe -m tests.isolated.check_payments
.venv\Scripts\python.exe -m tests.run_isolated
```

The preview prints eight validated rows, the original byte hash and physical source-line numbers, and `persisted: false`. Invalid input returns exit code 1 with a safe JSON error and no partial rows. The CLI takes a local file path relative to the current working directory; it does not look for `.env` or touch Chroma, the corpus or reports. No model is needed.

Versioned storage, atomic activation, the authorized query and its frontend are implemented. Dataset compatibility and four live payment cases are integrated in the extended workflow. Model explanations, charts, downloads and Excel/PDF ingestion remain later work. Historical snapshots remain preserved; source-changing batches require recapture before live evaluation.

## Local dataset activation

```powershell
.venv\Scripts\python.exe -m scripts.import_payments tests/fixtures/supplier-payments.csv
.venv\Scripts\python.exe -m tests.isolated.check_payment_store
.venv\Scripts\python.exe -m scripts.lab_console --suite isolated
```

The import command validates before opening the database and reads at most 1 MiB plus one byte. It saves exact original CSV bytes, SHA-256, a UUID version, UTC import time and original line numbers. BHD amounts are stored as integer thousandths. `app.paths.PAYMENTS_DB` resolves to repository-root `data/payments.sqlite3` regardless of working directory. Only the CLI input path is relative to the caller's directory. The database and SQLite sidecars are ignored by Git and separate from Chroma.

The eight-row synthetic fixture was activated on 4 November 2026 as version `bead851cc33a44cab8145c44158d9093`, source SHA-256 `312e0b125cc79e70a20081661145c0a7f19efab34ef838b6e76086131460416f`. Repeating the command creates another historical version and makes it active. No deletion or database rebuild is needed.

Nine isolated storage checks cover exact source/row retention, reimport history, invalid-file preservation, rollback after an injected activation failure, immutable-history triggers, unknown-schema rejection, concurrent imports, read-only metadata access and safe CLI errors. Tests use temporary databases. An actual process kill or power-loss test was not performed. Local SQLite transactions provide the activation boundary; this is not a backup or disaster-recovery implementation.

The payment query route enforces administrator authorization before storage access. Its browser view uses the same structured result and clears data on account/month changes. Local import operators use operating-system file access. Chat does not yet route natural-language payment questions to the structured operation. Earlier snapshots predate payment metadata. Current snapshots record the active version and source hash, and the extended regression checks compatibility and returned provenance.

## Implemented structured query

`POST /payments/query` accepts only:

```json
{"operation": "supplier_payments_above_threshold", "month": "2026-10"}
```

Use the existing administrator Bearer token. Server-assigned roles are unchanged. The route denies employees before storage access, rejects unknown fields/operations and malformed months, and implements the planned 401/403/422/503 statuses. Successful responses use `Cache-Control: no-store`. A parameterized read-only SQLite query reads active metadata and rows in one transaction, avoiding mixed versions during activation. Inclusive first/last calendar dates implement the planned month interval for date-only records, including December 9999. The strict per-payment threshold and deterministic date/ID ordering are preserved.

The response includes `operation`, `month`, `currency`, `threshold_bhd`, `row_count`, `total_bhd`, `rows` and `dataset`. Each row includes its payment ID, supplier, date, exact BHD string and source line. Dataset metadata includes version, source SHA-256 and import time. Totals use Python integer thousandths rather than SQLite `SUM`, avoiding aggregate overflow for valid large amounts. No model request is involved.

The endpoint now returns numerical results, dataset provenance and a required `policy` reference with an exact approved excerpt, source/manifest hashes and line range. It does not claim individual payments were approved. Missing or changed policy produces a safe 503 without partial results. `/query` behavior and administrator marker permissions are unchanged. See [policy implementation and tests](payment-policy.md).

The running-server verification passed 8/8 cases: administrator fixture, employee denial, missing/invalid tokens, extra role field, empty month, invalid month and unapproved operation. The [case report](../results/payment-api-verification-20261104T201400297645Z.json) includes response times, expected/actual status, failed checks and active-dataset metadata. Its [environment snapshot](../results/environment-20261104T201327357554Z.json) matched current source and assets at execution. Automatic payment compatibility checking is still required before extending the regression runner.

Twelve new isolated tests use temporary credentials and databases, including large totals, leap dates, ordering, reactivation and supplier markup retained as data. The full isolated workflow passed 112 checks. No browser rendering or model explanation was tested in this batch.

To exercise the API without displaying a token, run from the repository root:

```powershell
@'
import httpx
from dotenv import dotenv_values
from app.paths import ROOT
values = dotenv_values(ROOT / ".env")
response = httpx.post(
    "http://127.0.0.1:8001/payments/query",
    headers={"Authorization": "Bearer " + values["ADMIN_TOKEN"]},
    json={"operation": "supplier_payments_above_threshold", "month": "2026-10"},
    timeout=15, trust_env=False,
)
print(response.status_code)
print(response.json())
'@ | .venv\Scripts\python.exe -
```

Expected: HTTP 200, three rows and `total_bhd: "18750.125"`. The API must load current source. The development server command remains `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload`; reuse an existing listener.
