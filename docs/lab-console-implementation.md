# Local lab console

The one-command runner and separate administrator console are implemented. They orchestrate the existing checks and evaluators; they do not change the application's security policy or test expectations.

## Start the browser console

Run from the repository root:

```powershell
.venv\Scripts\python.exe -m scripts.lab_console --serve
```

Open [the operator console](http://127.0.0.1:8010/) and connect with the existing administrator token. The token stays in page memory and is cleared on reload/disconnect. Employee credentials cannot run workflows or read/download operator reports. The company assistant stays at [port 8001](http://127.0.0.1:8001/).

The launcher detects an existing listener on port 8001. If the port is free, it starts a companion company API in the same process; that owned companion stops when the launcher exits. An existing API is reused and never stopped or replaced. An occupied but unresponsive/wrong API must be investigated separately. Ollama and the configured models must already be installed and available.

Leave the launch terminal running. The console is bound to 127.0.0.1:8010; use that exact origin, not a different hostname. A second console instance cannot bind the same port. Changes to the console's Python code require restarting its launcher; reload the page after interface-asset changes.

## Buttons and workflow behavior

| Action | What runs | Prerequisites |
| --- | --- | --- |
| Isolated checks | `tests.run_isolated` | Existing dependencies and local authentication configuration |
| Chroma authorization | `tests.live.check_chroma_authorization` | Existing index/collection; embedding HTTP is simulated using a stored vector |
| Live regression | Isolated checks, index checks, readiness, environment capture, nine-case live evaluator | API, both identities, Ollama/models, corpus/index |
| Extended regression | Same sequence with the twelve-case evaluator | Same live prerequisites |

Readiness displays safe decisions for credentials, index presence, corpus, API, account mappings, Ollama/models and snapshot compatibility. Index presence is not collection validation; the Chroma suite supplies that check. Refresh readiness after a run to see the new snapshot state.

Workflows execute in a background thread with bounded subprocess stages. The browser polls stage status; it does not hold one HTTP request open for the full evaluation. Detailed case outcomes appear after the live evaluator finishes. One OS-backed lock prevents concurrent CLI/console workflows. The persistent lock file is ignored by Git and OS ownership is released after a crash, so ordinary recovery does not require deleting it.

Disconnecting clears browser state but leaves an active server-side run running. This version has no cancel button. Keep the launcher open until tests finish. If the process stops unexpectedly, the next report read marks an orphaned running record interrupted when no workflow lock is held. Do not run separate direct capture/evaluation commands concurrently: those legacy commands do not participate in the orchestration lock.

## One-command terminal operation

```powershell
.venv\Scripts\python.exe -m scripts.lab_console
.venv\Scripts\python.exe -m scripts.lab_console --suite isolated
.venv\Scripts\python.exe -m scripts.lab_console --suite chroma
.venv\Scripts\python.exe -m scripts.lab_console --suite regression
```

The default is the extended workflow. A live CLI invocation also starts an owned companion API if port 8001 is free and stops that companion afterwards. Isolated/Chroma-only invocations do not start services.

Exit codes are 0 for a passing workflow, 1 for a failed existing check/evaluation stage, 2 for an orchestration/prerequisite error and 130 for an interrupted workflow. Failure stops later stages. Preserve the outcome and investigate; do not weaken assertions to produce a pass.

## Reports and diagnostics

- `results/lab-workflow-<run-id>.json`: orchestration stages, timestamps, durations, safe readiness decisions, snapshot/report association and actual live case summaries.
- `results/environment-<timestamp>.json`: the existing capture's models, corpus and repository-relative Python/interface hashes.
- `results/development-regression-<timestamp>.json`: the unchanged live evaluator's per-case responses, checks, errors and response times.
- `results/lab-diagnostic-*.log`: private local diagnostics with configured token values and personal root paths redacted. These logs are ignored by Git and are not served by the console.

The download button returns a curated JSON summary, not arbitrary files or raw logs. Report IDs are validated; authenticated administrator access is checked again for reads and downloads. Stage summaries are distinct from independent test-case counts. Partial evaluator reports are linked when available, with missing final counts left unset rather than invented.

Python and asset changes require fresh capture. Asset discovery includes both `app/static/` and `scripts/console_static/`. Existing environment snapshots and reports remain intact. Hashes identify saved files; they do not prove an already-running API loaded the current source.

## Operator security boundary

The console is a separate FastAPI application in `scripts/lab_console_web.py`. It exposes only fixed suite names and uses subprocess argument arrays without a shell. Browser actions require the exact same Origin, JSON content and a custom action header; cross-site requests and untrusted Host values are rejected. No CORS access or cookie authentication is enabled. API responses are non-cacheable, and the UI renders report data as text.

The console never ingests data, recreates credentials, downloads models or offers arbitrary commands. It reuses the existing administrator identity as local operator authorization; it is not an additional company account/SSO service. Keep it loopback-only.

## Implementation map

- `scripts/lab_workflow.py`: shared locking, readiness, orchestration, reports and subprocess limits.
- `scripts/lab_console.py`: CLI, local server launcher and owned companion API lifecycle.
- `scripts/lab_console_web.py`: administrator-only endpoints and browser request boundary.
- `scripts/console_static/`: HTML/CSS/JavaScript operator interface.
- `tests/isolated/check_lab_console.py`: simulated operator, orchestration and startup-boundary checks.

## Verification and screenshots

The current execution evidence is recorded in [testing.md](testing.md). No browser visual verification is claimed when the browser connection is unavailable.

For the existing roadmap capture, use `docs/screenshots/38-environment-live-regression.png` after a full live workflow completes. Show actual case outcomes, failed checks and associated report/snapshot names. Preserve a failure image when adding a later retest. New console-specific filenames reserved after the original 31-56 plan are:

- `57-operator-console-home.png`: signed-out operator page, no token entered.
- `58-operator-console-readiness.png`: verified administrator with readiness decisions, token input cleared.
- `59-operator-console-results.png`: completed workflow, actual case counts and report association.

The owner supplied screenshots 57–59 and 59b, and they have been reviewed; see [the evidence index](evidence.md). They preserve the original failing result. The validator fix passed a new twelve-case run; reviewed screenshot 60 shows the owner’s passing retest summary. The case report records the corrected rows; the optional detailed 60b capture remains open. Crop personal paths, tokens and unrelated content. Record actual evidence metadata; a screenshot does not replace a machine-readable report.
