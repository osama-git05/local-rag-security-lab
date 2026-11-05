# Changelog

All entries are unreleased development work. No semantic version or release tag is claimed. The corpus manifest's `0.1.0` is a dataset label, not an application release.

## Unreleased - 2026-11-05

- Verified both credential replacements and rejection of both previous tokens. Reconstructed the local generation tag with an identical manifest digest.
- Verified the implementation commit from a fresh local clone, including dependency installation, new Chroma ingestion and all 16 live cases.

- Recorded a 61-second captioned walkthrough of the live employee and administrator flows, with screenshots 74–76 and a capture record.

- Added active payment dataset compatibility checks and four live payment cases. The extended workflow passed 126 isolated checks, three index checks and all 16 live cases.
- Verified chat login, Enter submission, loading, replayed 502 handling and live retry. Added screenshots 71–73.
- Recorded model provenance and merged-weight licensing questions. A fresh environment passed pinned dependency installation and payment smoke checks from the current working source.
- Prepared the commit review, reconciled Markdown status, and added the final development report and demo walkthrough.

## Unreleased - 2026-11-04

- Added an exact source-grounded finance-policy excerpt to the structured payment result and frontend, with source/manifest hashes and line provenance. The adapter checks existing admin/curated manifest classification and fails closed on changed or missing approved text. It makes no payment-approval claim or model call; general RAG permissions are unchanged.
- Added eight isolated policy adapter checks and three API checks. The combined view passed 14 browser cases (nine real API/browser-state cases and five labelled simulations), with reviewed screenshots 68–69. Earlier reports and screenshot versions remain preserved.
- Recaptured the combined milestone and passed the full extended workflow: 123 isolated checks, three actual-index checks and twelve unchanged live RAG cases, with no failures/errors. This checkpoint preceded payment-version compatibility enforcement.

- Added bounded supplier-payment CSV preview, versioned SQLite activation and administrator-only deterministic `/payments/query`, preserving the existing RAG corpus/index and policy. Added 31 isolated checks across validation, storage and API; the full model-free suite now passes 112.
- Added a payment view below the chat with month selection, exact totals, source-line table and dataset provenance. Account/month changes clear results; delayed requests cannot restore results after disconnect. Supplier markup renders as text and inconsistent totals are rejected.
- Verified 12 browser cases (eight real API/browser-state checks and four labelled simulations), saved reviewed numbered screenshots 64–67 and preserved timestamped repeats. Updated the environment snapshot, evidence index, feature guide and roadmap. This checkpoint preceded the source-grounded policy excerpt.

- Hid validated inline document-ID tags in chat prose while retaining source chips/context. The API answer and citation-validation rules are unchanged; only matching returned source references are removed from displayed text.
- Added content-hashed assistant asset URLs and `no-store` asset headers so reloading does not reuse an older citation renderer. Verified the live served script and five UI-route checks, including current-version delivery.

- Diagnosed the two extended-suite 502 cases as complete context-absence messages missing from refusal normalization. Added only those whole messages; preserved ordinary citation rules, role policy, model/prompt settings and all evaluator expectations.
- Added eight targeted function/API-path checks, including continued rejection of uncited additions and malformed/forbidden references. The full retest passed 80 isolated checks, 3 actual-index checks and all 12 extended live cases, with 0 failures and 0 errors. Historical failed reports and screenshots remain intact.
- Reviewed owner screenshots 57–59 and 59b; linked their actual run evidence and reserved 60/60b for the passing retest.

- Implemented shared orchestration and the `scripts.lab_console` CLI for isolated, index, nine-case and extended workflows.
- Added a separate loopback administrator console on port 8010 with readiness checks, background runs, stage progress, case summaries and protected summary downloads.
- Added fixed suite validation, same-origin action protection, Host validation, a shared OS lock, bounded child processes, private redacted diagnostics and interrupted-run recovery.
- Added owned companion-API startup when port 8001 is free; existing listeners are reused and never stopped by the launcher.
- Extended environment hashing to the operator interface assets while preserving historical artifacts.
- Initially verified 72 isolated cases, 3 existing-index checks and 9 HTTP console checks. The extended suite reproduced 10 passes and 2 unexpected-502 failures, resolved by the subsequent whole-message fix described above.
- Updated the console guide, setup, architecture, security, testing, environment and evidence records. Later entries record browser verification and new captures.

## Unreleased - 2026-11-03

### Historical checkpoint 28

- Confirmed active `retrieval_authorized_prompt_hardened` responses after identifying and restarting the actual port-8001 Uvicorn listener.
- Rechecked the onboarding payload and normal leave question under the explicit prompt; both produced expected answers and citations.
- Added `app/output_validation.py` to check citation syntax, require ordinary-answer references and reject IDs outside the permitted retrieved set.
- Used route integration to expose a missing enforcement connection (2/4), then confirmed its correction (4/4).
- Diagnosed the employee-query 502 as strict refusal-string handling, normalized one observed complete variation and confirmed the live standard refusal with employee-only sources.
- Expanded the output-validator script from eight to ten cases. Original 8/8 developer output and a ten-case authoring reference check are available; full expanded developer-machine output is not retained.
- Added/passed eight deterministic authorization checks and three controls against the actual Chroma index.
- Updated twelve Markdown files and the documentation ZIP with current results and remaining work.

### Additional prepared artifact

- A separate `evaluation/run_regression.py` defines nine live development cases, environment-snapshot checks and JSON result output. Completed execution and environment snapshot values were not reviewed here. Its expected prompt-request guard result is not evidence of an implemented defense.

### Added

- Local FastAPI generation and RAG query flow over synthetic company documents.
- Separate employee/administrator credentials and a verified `Principal` mapping.
- `/whoami` and an authentication-check script.
- Role-based retrieval filtering before generation, with a returned-label check.
- An employee-accessible indirect-injection onboarding fixture.
- Development test cases for role differences, role spoofing, normal answers and indirect injection.
- Repository documentation for setup, architecture, environment, implementation history, tests, findings, troubleshooting, evidence, security and remaining work.

### Changed

- Protected generation and query routes with bearer authentication.
- Passed the verified principal from the API to authorized retrieval.
- Changed generation from the problematic Qwen configuration to the locally installed `optimized-gemma:latest` after direct controls.
- Kept `embeddinggemma` as the embedding model.
- Added end-marker stop sequences and clearer concise-answer/citation instructions.
- Added rejection of a reported generation finish at the output token limit.
- Used port 8001 for a fresh diagnostic API instance after an unexplained 500 on port 8000.

### Corrected or addressed

- Missing comma between entries in the edited manifest JSON.
- `_PROMPT` versus `SYSTEM_PROMPT` mismatch in a pasted edit.
- Stray `SYSTEM` text in the pasted `client.post` call.
- Screenshot handling after credentials were visible: rotation and sanitized recapture procedures were provided; complete remediation remains unverified.
- Swagger credential-copying procedure using parsed dotenv values instead of manual copying with possible quote characters.

### Further fixes and diagnostics

- Resolved the old-mode listener mismatch with targeted process identification/restart and enabled development reload.
- Corrected an invalid process query caused by a literal PID placeholder.
- Corrected the test-file-not-found setup issue by saving the authorization script in the project root.
- Corrected a pasted test edit by moving the two new cases inside the `cases` list.
- Added local exception logging while retaining generic external API errors.
- Used temporary raw-answer printing to identify refusal wording; removal remains a publication check.

### Known issues and limitations

- Hardened-mode activation is confirmed. The expanded ten-case validator output still needs a retained developer-machine rerun, and the raw-answer diagnostic print should be verified removed.
- Root cause of the earlier 500 is unknown.
- Qwen template/thinking experiments did not establish a fix or complete diagnosis.
- No controlled before/after benchmark, universal output-secret rule, automated citation support validation, completed CI or verified clean-clone release.
