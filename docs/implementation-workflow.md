# Implementation and documentation workflow

Agreed on 4 November 2026: the repository owner normally implements changes, runs checks and captures screenshots; the assistant provides instructions, reviews results and maintains documentation. The owner subsequently delegated implementation and verification of the one-command runner and browser console to the assistant. The owner subsequently requested successive business-feature batches and renewed assistant screenshot/documentation capture. Only the implemented, verified batches below are complete.

The [Word master plan](ExampleCo_Project_Master_Plan.docx) remains the roadmap. Work proceeds in small batches: instructions, owner execution, observed results, documentation update, then the next batch. Proposed changes and expected results must not be recorded as completed work.

## Current position

The 5 November extended workflow passed 126 isolated checks, three index checks and 16 live cases, including four payment cases. The latest chat browser check verified login, loading, safe error display and live retry. Model provenance is documented, and a clean copy of the working source passed dependency installation and payment smoke checks. The proposed commit is ready for review. The captioned demo is recorded. A fresh checkout from the reviewed commit remains open. [Final report](final-report.md) · [Commit review](release-review.md) · [Demo](demo.md).

## Earlier implementation checkpoints

Phase 0 Step 01 is complete: the initial baseline contained 51 isolated checks, operator tooling expanded that to 72, and the refusal fix now passes 80. Existing-index checks pass 3/3. See [current testing](testing.md#refusal-normalization-retest-on-4-november-2026).

Phase 0 Step 02 is complete for the two observed cases. The historical extended suite recorded HTTP 502 instead of the expected HTTP 200 for:

- `employee-forged-system-authority`
- `employee-encoded-secret-request`

Case-scoped diagnosis established that two safe complete refusal messages were absent from the normalization set. Whole-message additions fixed the compatibility issue while preserving citation/access checks and every evaluator assertion. The full retest passed 12/12, with the administrator positive control intact. Unseen model wording remains outside this narrow guarantee.

The owner preserved the failures in workflow `20261104T170526136280Z-33dc3ba4` and screenshots 59/59b. The passing retest is `20261104T171718796408Z-cf0afb79`. The owner’s later passing retest is shown in screenshot 60. The optional 60b capture remains open and the case report retains the detailed outcomes.

The owner supplied screenshot 60 from a subsequent passing run, `20261104T172341599479Z-ab899497`, and it has been reviewed against its actual report. Manual browser checks are tracked in [Browser workflow verification](browser-verification.md). New conversation, Disconnect, reload disconnection, Shift+Enter, clearing/disconnecting during an active request, account switching and narrow-pane layout are owner-reported passes. Employee/admin finance frames (34/33) match the expected answer/source behavior within the stated test context. The rejected-token dialog is preserved as screenshot 63. The owner delegated a real Ollama outage/recovery check: API failure and recovery passed, and Ollama was restored. The separate 5 November Chrome check verified connection, Enter, loading, error display and button recovery. The error used a replay of the real outage response, followed by a live retry.

The earlier Phase 0 Step 04 stabilization baseline was workflow `20261104T195654526978Z-6956ad0c` passed 81 isolated checks, 3 index checks and all 12 live cases, with a fresh compatible snapshot. See [the final stabilization record](testing.md). The later browser and provenance checks are linked in the current position above.

## Agreed automation before Step 02

The first Phase 1 contract is documented in [Supplier-payment feature contract](supplier-payments-contract.md): business question, existing-role access matrix, bounded CSV schema, exact query/result semantics, golden fixture and acceptance checks. CSV validation and a local JSON preview are now implemented with ten isolated checks and an eight-row synthetic fixture. Versioned SQLite storage and atomic activation are now implemented, with nine additional temporary-database checks; the eight-row synthetic fixture is active in the separate payment database. The administrator-only POST /payments/query operation is now implemented and verified: 112 isolated checks and eight targeted running-server cases passed. The payment interface is now implemented below the chat: month selection, exact total, table, source lines and dataset details. Twelve browser cases passed (eight real API/browser-state cases, four labelled simulations), with reviewed screenshots 64–67. See [the interface evidence](payment-ui.md). Source-grounded policy context is now implemented and verified, with screenshots 68–69, 14 browser cases and a fresh full workflow passing 123 isolated checks, three index checks and all twelve existing live RAG cases; see [policy evidence](payment-policy.md). Natural-language routing and model explanations remain pending. The 5 November extended workflow added compatibility checks and four live payment cases.

The owner chose a one-command runner and local browser test console, then delegated that implementation to the assistant. See [Lab console implementation](lab-console-implementation.md) for the implemented launcher, buttons and reports. It wraps existing checks, capture and evaluation. This operator-tooling addition precedes failure diagnosis; it does not itself fix either historical 502 case.

Use `.venv\Scripts\python.exe -m scripts.lab_console --serve`, open `http://127.0.0.1:8010/` and connect with the existing administrator token. The manual steps below remain the fallback and prerequisite guide. Report actual outcomes before advancing to a security-control change.

## Historical Step 02 reproduction procedure

Run from the repository root in PowerShell.

1. Check whether the intended API is responsive:

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8001/health -TimeoutSec 10
   ```

   Expected availability response: `status` is `ok`. Reuse a responsive server running the current `app.main:app` source. If the check fails, distinguish an absent server from an unresponsive existing listener before starting another instance:

   ```powershell
   Get-NetTCPConnection -State Listen -LocalPort 8001 -ErrorAction SilentlyContinue
   ```

   If no server is listening, start it in a separate terminal and leave that terminal open:

   ```powershell
   .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
   ```

   If a listener exists but does not respond, identify the existing server first and retain its error output. Do not start a competing instance.

2. Capture the current environment. The existing capture requires running Ollama and the two configured models. It preserves historical snapshots:

   ```powershell
   .venv\Scripts\python.exe -m scripts.capture_environment
   ```

   Retain the printed `results/environment-...json` filename. If capture fails, report that prerequisite error before continuing. This snapshot records the reproduction state; capture again after subsequent Python/interface changes.

3. Run the unchanged twelve-case development suite:

   ```powershell
   .venv\Scripts\python.exe -u -m evaluation.run_extended_regression
   ```

   Retain all case outcomes and the new report filename. The runner verifies employee/admin identities, reads credentials privately and records checks, responses and timings without including authorization headers. A failing summary and nonzero exit status are evidence to investigate, not an instruction to change assertions.

## Screenshot and result handoff

After the run finishes, save a readable terminal capture as `docs/screenshots/38-environment-live-regression.png`, as reserved in the master plan. Show the two relevant case outcomes, final counts and saved report name. Record the associated environment snapshot filename separately if it does not fit in the same frame. Crop personal paths and unrelated windows, and keep tokens, real `.env` contents and authenticated Swagger curl commands out of the capture.

This image is **pending** until captured and reviewed. Preserve it when later adding a retest image; do not overwrite a recorded failure with a later passing result.

Provide the terminal case summary, report filename, snapshot filename and screenshot filename. If HTTP 502 recurs, also provide the exception type/message from the API terminal at that time, with personal paths redacted. Do not add raw-token or request-header logging.

The next batch depends on these actual results. It will identify the failing stage and provide a focused implementation change, followed by the same-case retest. If the old failures do not reproduce, document that outcome and investigate reproducibility before claiming the cause is fixed.

## Documentation updates after each batch

- `docs/testing.md`: exact commands, observed counts, failures and verification scope.
- `docs/findings.md`: confirmed root cause, impact, change and retest reference.
- `docs/evidence.md`: existing screenshot link, caption, date, role, case/run IDs and source state.
- `README.md`, setup and architecture: implemented behavior and commands that actually changed.
- `CHANGELOG.md` and the Word master plan: completed milestones and material roadmap changes.

Keep expected output, pending screenshots and proposed features distinct from observed evidence. Documentation-only changes do not themselves establish a new application test result.
