# Security model and development limitations

This repository is a local educational RAG security lab. Its corpus and secret markers are synthetic. The implementation is still being evaluated and should not be presented as a production-ready authentication or prompt-injection defense system.

## Local credential rotation

The local employee and administrator credentials were rotated on 5 November 2026. The restarted API rejected both immediately previous tokens and verified the roles of the replacement tokens. The verification record contains outcomes only. [Rotation record](results/credential-rotation-20261105T112710208082Z.json).

## Supplier-payment data

The combined operation now includes one exact approved finance-policy paragraph from the existing corpus, with raw source/manifest hashes and line provenance. Policy loading occurs only after administrator authorization. The adapter requires the manifest's admin/curated classification and an approved complete paragraph; missing, ambiguous or changed policy fails safely with HTTP 503 and no partial result. It does not interpret arbitrary instructions or infer that a payment was approved. This scoped excerpt selection leaves the original RAG and administrator synthetic-marker permissions unchanged. See [policy controls](docs/payment-policy.md).

`POST /payments/query` requires the existing server-verified administrator role before database access. Employees receive a generic 403 without payment rows, aggregates or dataset metadata. Requests select one fixed operation and a validated calendar month; extra fields and caller-supplied roles, thresholds, SQL and file paths are rejected. Parameterized read-only queries and exact integer calculations produce results without model involvement. The separate `data/payments.sqlite3` retains versioned synthetic data and is ignored by Git; local import commands rely on operating-system file access. A separate payment view below the chat consumes the structured result; natural-language routing is not implemented. It clears records on account/month changes, discards late responses after disconnect, renders supplier names as text and checks exact row totals. Server authorization remains authoritative. The extended regression verifies active dataset compatibility before and after execution. The four live payment cases verify exact results, provenance and employee denial.

## Local operator console

The optional test console is a separate loopback application at `http://127.0.0.1:8010/`, launched with `python -m scripts.lab_console --serve`. It reuses the existing administrator principal for operator access. Employees cannot execute workflows or view/download their summaries. This is a local lab privilege, not a company SSO or account-management service.

Only fixed test suites can run. Browser actions require the exact console Origin, a JSON request and a custom action header; untrusted Host and cross-site requests are rejected. Report IDs are validated, summaries are curated and non-cacheable, and the console exposes no arbitrary shell/file endpoints. Tokens stay in page memory. A shared OS lock serializes console/CLI runs, and child stages have finite time limits.

Raw diagnostic files remain local and ignored by Git, with configured credential values and personal root paths redacted. They are not served by the console. Detailed evaluator records contain synthetic case material and remain separate from the browser's safe summary. Disconnect does not cancel a running server-side job.

The launcher starts a companion company API only when port 8001 is free and stops only that owned companion. It never replaces an existing listener, rebuilds the index, downloads models or recreates credentials. Direct legacy capture/evaluation commands do not share the orchestration lock and should not run concurrently with a console workflow.

## Intended deployment

Bind FastAPI to `127.0.0.1`, keep Ollama local, and use embedded ChromaDB. Do not expose the intentionally vulnerable baseline or local model service to an external network. No host/network isolation, TLS termination, production rate limiting or managed identity service has been demonstrated.

## Attacker and operator assumptions

The experiment's attacker may submit API questions with their own employee credential and influence low-trust document content in controlled fixtures. The operator owns backend source, account configuration and manifest labels.

The experiment does not assume an attacker can read the host filesystem, edit `.env`, change trusted access labels or modify Python code. Host compromise and a malicious operator are outside this initial scope. The API does not implement an untrusted-user ingestion endpoint; attack documents are installed by the lab operator to model a lower-trust content channel.

## Role policy

| Verified principal | Allowed records |
| --- | --- |
| employee | `access_level: employee` |
| administrator | `access_level: employee` and `access_level: admin` |

Roles come from validated bearer tokens. Question text cannot grant a role. Unknown roles are rejected by retrieval. Access labels come from a trusted manifest, not from Markdown text.

Current policy permits an authenticated administrator to retrieve the fake finance marker. The marker demonstrates authorized access and is not an actual secret. A universal no-secret-output policy is not implemented; it would need a separate specification and output-validation tests.

## Controls represented in the shared implementation

- Validated request models and explicit whitespace rejection.
- Static-token authentication with different local employee/admin credentials.
- Server-derived principal passed into RAG retrieval.
- Role-based Chroma filtering and a post-retrieval access check.
- Manifest label/path/size validation and document content hashes.
- Local processing, finite generation limits and HTTP client timeouts.
- Basic nonempty-output and reported-truncation checks.
- An active explicit prompt to treat retrieved text as reference data, rechecked with the onboarding and leave questions.
- Citation-ID validation connected before the API returns answers, with controlled rejection tests.
- Full-message normalization for the canonical and one observed insufficient-information response.
- Eight deterministic authorization tests and three actual-index authorization checks.

## Known gaps

- Tokens are stored as plaintext in a local `.env`; in-memory hashing does not encrypt that file.
- Token expiry, refresh, per-person account provisioning and multiuser audit trails are absent.
- FastAPI authentication does not protect direct local calls to Ollama or host files.
- `trust_level` is recorded but no deterministic quarantine policy or content classifier is implemented.
- Prompt instructions are guidance for generation, not authorization enforcement.
- Citation IDs are validated, but factual support, complete citation coverage, prompt extraction and universal secret output are not established as enforced controls by the reviewed evidence.
- Additional attack variants, broader metadata and read-path coverage, controlled evaluation and CI remain pending. The current authorization suite covers specific missing and invalid labels. [Fresh checkout verification](docs/setup.md#verified-fresh-checkout-on-5-november-2026).
- The original port-8000 500 remains undiagnosed. The separate stale-mode issue on port 8001 was resolved by restarting the identified listener.
- Temporary raw-answer diagnostic printing was requested to be removed before publication; verify its removal.

See [findings](docs/findings.md) for evidence and [roadmap](docs/roadmap.md) for remaining work.

## Credential and evidence hygiene

Keep real `.env`, environments, local databases, model weights and unsanitized logs out of Git. Use placeholders in `.env.example`. Swagger's generated curl command includes the bearer token, so screenshots should show only the needed request/response area.

If a real token appears in a screenshot or commit, replace it, restart every affected API process and remove the unsafe evidence from the intended publication set. Assess history and distributed copies if publication occurred. Redaction alone does not revoke credentials.

The strings beginning `LAB_SECRET_` and `LAB_INJECTION_` in the synthetic corpus are test fixtures. Do not use actual account tokens as attack markers.

## Reporting an issue

For an issue involving credentials or other private data, contact the repository owner through an available private channel before posting details publicly. This snapshot does not assume that a particular GitHub reporting feature is enabled and provides no invented contact address.

For a sanitized reproducible issue, include the affected commit, mode, model identifier, synthetic case, expected/actual behavior and a traceback if applicable. Do not include real bearer tokens or `.env` contents.

## Reference guidance

- [OWASP prompt-injection prevention guidance](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [FastAPI security reference](https://fastapi.tiangolo.com/reference/security/)
- [Ollama generation API](https://docs.ollama.com/api/generate)
- [Ollama Modelfile reference](https://docs.ollama.com/modelfile)
- [Chroma metadata filtering](https://docs.trychroma.com/docs/querying-collections/metadata-filtering)

These resources explain mechanisms and defensive principles. They are not evidence that every recommended control is implemented or verified in this repository.

## Refusal normalization and citation-check limits

The observed live refusal was: “There are no finance administration notes in the provided documents, and therefore no secret marker can be retrieved.” It was safe insufficient-information wording for the tested employee query, but initially produced a missing-citation exception.

The fix recognizes complete allowlisted messages after whitespace/case normalization and replaces them with `NO_ANSWER`. It does not accept arbitrary strings containing a refusal phrase. A test was supplied to reject that refusal followed by an uncited factual claim.

The citation validator still accepts an ordinary answer if its parsed citations belong to the retrieved set; it does not assess entailment or require a citation on every factual sentence. An answer can contain a valid citation and still be wrong. Additional secret-handling and extraction controls need explicit policies and evidence.

The available live regression runner includes a system-prompt-request scenario and expects a particular guard-refusal shape. A runner's expected response is not evidence that the guard exists or resisted the attack. No completed extraction result is claimed in this update.
