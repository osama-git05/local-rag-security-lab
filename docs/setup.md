# Setup and local operation

Commands target Windows PowerShell and the current package layout. Release verification distinguishes the committed Git tree from the current working source.

## Clean-source verification on 5 November 2026

An archive of Git commit `bea69ed` contains the original health-endpoint implementation. The current `app/main.py`, payment feature and regression suite are working-tree files outside that commit. A fresh checkout of the commit therefore cannot reproduce the current application.

A separate temporary copy of the current application, data fixtures and scripts started without credentials, an index or a payment database. Python 3.11.9 created a fresh virtual environment and installed `requirements.lock` from PyPI. `pip check` passed. With generated temporary credentials and a fresh activation of the synthetic fixture, FastAPI TestClient verified the homepage, health endpoint, the administrator’s November total of 8,000.000 BHD and employee HTTP 403. The smoke check exercised the payment path. Fresh checkout verification of the current source and rebuilding the generation model and vector index remain open. [Clean-source report](../results/clean-source-verification-20261105T104807638159Z.json).

## 1. Prepare the Python environment

Open PowerShell in the repository root, where `app/main.py`, `app/auth.py`, `app/ingest.py`, `app/retrieve.py` and `app/rag.py` live.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Prefer the repository's actual dependency lock when one exists:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
```

If no dependency file has been created, the shared source imports require at least the following packages. This is a reconstruction aid, not a substitute for a tested, pinned dependency file:

```powershell
.\.venv\Scripts\python.exe -m pip install fastapi uvicorn httpx chromadb python-dotenv pydantic
```

The code uses Pydantic v2 features and Python 3.10+ syntax. Record the Python version actually used and lock the working package versions before release.

## 2. Prepare local models

Ollama must serve requests at `http://127.0.0.1:11434`.

```powershell
ollama --version
ollama list
```

Current generation model: `optimized-gemma:latest`. Current embedding model: `embeddinggemma`.

The generation model is a local tag. Its exact weight identity, observed settings and the publisher’s licensing statements are recorded separately. A rebuild from scratch remains unverified. [Model provenance](model-provenance.md).

Changing the generation model does not require replacing the embeddings. Changing the embedding model requires compatible ingestion and retrieval settings and a deliberate index rebuild.

### Direct generation smoke test

```powershell
$gemmaBody = @{
    model = "optimized-gemma:latest"
    system = "Answer using only the supplied context. Give one short sentence."
    prompt = "Context: Employees receive 25 days of annual leave. Question: How many days do they receive?"
    stream = $false
    think = $false
    options = @{
        temperature = 0
        num_ctx = 4096
        num_predict = 256
    }
} | ConvertTo-Json -Depth 5

$gemmaResult = Invoke-RestMethod `
    -Uri "http://127.0.0.1:11434/api/generate" `
    -Method Post `
    -ContentType "application/json" `
    -Body $gemmaBody `
    -TimeoutSec 180

[pscustomobject]@{
    Model = $gemmaResult.model
    Answer = $gemmaResult.response
    DoneReason = $gemmaResult.done_reason
    OutputTokens = $gemmaResult.eval_count
    ThinkingCharacters = ([string]$gemmaResult.thinking).Length
} | Format-List
```

The observed control result was a complete answer about 25 days, `stop`, 11 output tokens and zero reported thinking characters. This is a smoke test, not a benchmark.

## 3. Create local account tokens

Run the existing preparation script once:

```powershell
.\.venv\Scripts\python.exe -m scripts.setup_tokens
git check-ignore .env
```

The script uses exclusive file creation to avoid overwriting an existing `.env`. If the file exists, inspect its structure locally and preserve any unrelated settings. Do not rerun by deleting credentials merely to bypass that protection.

`app/auth.py` expects `EMPLOYEE_TOKEN` and `ADMIN_TOKEN`, each at least 32 characters long and different from one another. Its two identities are:

| Environment key | User ID | Role |
| --- | --- | --- |
| `EMPLOYEE_TOKEN` | `employee-01` | `employee` |
| `ADMIN_TOKEN` | `admin-01` | `admin` |

The proposed commit includes `.env.example` with blank values. Use the token setup script to create `.env`.

```dotenv
EMPLOYEE_TOKEN=
ADMIN_TOKEN=
```

Do not use placeholders as credentials. Keep `.env`, `.venv/`, `.chroma/`, Python caches, downloaded model files and unsanitized logs out of Git.

## 4. Prepare and ingest the corpus

The project includes five synthetic Markdown documents in `data/corpus/` and their manifest at `data/manifest.json`.

| Document ID | Filename | Access | Trust |
| --- | --- | --- | --- |
| `policy-leave` | `leave-policy.md` | employee | curated |
| `policy-security` | `security-policy.md` | employee | curated |
| `ticket-1042` | `support-ticket.md` | employee | untrusted |
| `admin-finance` | `finance-admin.md` | admin | curated |
| `ticket-onboarding-injection` | `onboarding-injection.md` | employee | untrusted |

The shared manifest reports dataset version `0.1.0`, including after the injection fixture was added. Before a controlled comparison, version or hash the exact fixture state rather than assuming this version string identifies immutable content.

```powershell
.\.venv\Scripts\python.exe -m json.tool data\manifest.json
.\.venv\Scripts\python.exe -m app.ingest
```

Ingestion validates labels, document IDs, file location, extension and size; embeds the documents; and upserts the collection. Review the printed counts and labels. It intentionally stops if existing collection IDs are absent from the manifest. Do not delete the database automatically to bypass this check.

## 5. Start FastAPI

The current working diagnostic port is 8001:

```powershell
.\.venv\Scripts\python.exe -u -m uvicorn app.main:app --app-dir . --host 127.0.0.1 --port 8001 --reload --log-level debug --access-log
```

Open [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs). Leave the server terminal open. This development command enables reload for saved Python edits. Verify the reload/startup messages and execute a fresh request after edits. A manually running instance without reload must be restarted. Confirm the expected `rag.__file__` and active response mode if saved code and API behavior disagree.

The company interface and live check scripts use port 8001. Run the identity check with `python -m tests.live.check_auth`.

## 6. Authorize safely in Swagger

From another terminal in the project root, copy the parsed employee token without displaying it:

```powershell
.\.venv\Scripts\python.exe -c "from dotenv import dotenv_values; print(dotenv_values('.env')['EMPLOYEE_TOKEN'], end='')" | Set-Clipboard
```

In Swagger, choose Authorize, log out any previous account, paste the token value without adding `Bearer`, then Authorize and Close. The dotenv parser removes surrounding file quotation syntax.

Run `GET /whoami` and check the employee identity before role-specific queries. For administrator tests, repeat the command using `ADMIN_TOKEN`, authorize again, and verify the administrator identity.

Avoid screenshots of Swagger's generated curl command, which contains the authorization header. Clear the token from the clipboard when finished if the clipboard is shared or synchronized.

## 7. Query the assistant

Send this JSON to `POST /query`:

```json
{
  "question": "How much annual leave do employees receive?"
}
```

The endpoint expects `question`, not `prompt`. `/generate` expects `prompt` and does not retrieve documents. The request models forbid extra fields.

Verify the generation model, mode label, answer and source list. Follow [testing](testing.md) for the role and injection scenarios.

## 8. Rotate a disclosed credential

For an exposed employee token:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; from dotenv import set_key; set_key('.env', 'EMPLOYEE_TOKEN', secrets.token_urlsafe(32)); print('Employee token replaced.')"
```

Use `ADMIN_TOKEN` instead for the administrator token. Restart every running FastAPI instance that loaded the old credentials, then authorize again. Remove exposed images from the intended publication set. Rotation is effective for a process only after it loads the replacement.

## 9. Run the regression checks

Save each check script in the project root before invoking it. The documentation ZIP contains Markdown, not the Python implementation or tests.

```powershell
.\.venv\Scripts\python.exe -m tests.isolated.check_output_validation
.\.venv\Scripts\python.exe -m tests.isolated.check_query_output
.\.venv\Scripts\python.exe -m tests.isolated.check_authorization
.\.venv\Scripts\python.exe -m tests.live.check_chroma_authorization
```

| Script | Expected completion | Observed evidence |
| --- | --- | --- |
| `tests/isolated/check_output_validation.py` | 10/10 with the expanded cases | Original eight-case run passed; expanded script and reference check supplied, developer-machine ten-case output not retained |
| `tests/isolated/check_query_output.py` | 4/4 | Confirmed 4/4 after validation wiring was corrected |
| `tests/isolated/check_authorization.py` | Eight tests and OK | Confirmed |
| `tests/live/check_chroma_authorization.py` | 3/3 | Confirmed against stored index |

The output-function and authorization tests do not require model requests. The route/output test uses FastAPI's in-process client, real local authentication and simulated retrieval/generation, so it does not use the running Uvicorn listener. The Chroma check requires the existing corpus index but supplies a fixed stored vector rather than calling Ollama.

The API integration test deliberately triggers two 502 responses. Logged `CitationValidationError` tracebacks are expected for those negative cases; use the final test verdict and HTTP/body checks to determine success.

## 10. Verify the live refusal path

With the server running and an employee token authorized, submit the finance marker question. The confirmed final response was the canonical insufficient-information message with `policy-security` and `ticket-1042` as employee sources. `admin-finance` and the marker were absent.

The validator allows the canonical message plus the complete observed refusal variation and returns the canonical wording. It does not allow arbitrary uncited facts or arbitrary refusal prefixes. Remove the temporary raw `MODEL_ANSWER` diagnostic print after troubleshooting; its removal was requested but not independently verified in the retained source.

## 11. Live development runners

`evaluation/run_regression.py` contains nine known development cases, and `evaluation/run_extended_regression.py` adds three. Both require a matching environment snapshot. Completed runs and unresolved failures are linked in [testing](testing.md); these are not held-out benchmarks.

## 12. Use the local operator console

```powershell
.venv\Scripts\python.exe -m scripts.lab_console --serve
```

Open [the console](http://127.0.0.1:8010/) and use the existing administrator token. Select a fixed suite to run the existing scripts. Live workflows check readiness, capture a new environment and retain detailed evaluation reports. The launcher reuses the existing company API or starts an owned companion when port 8001 is free. Keep the launch terminal open. Ollama and the configured models remain prerequisites.

For a terminal-only extended workflow, use `.venv\Scripts\python.exe -m scripts.lab_console`. For details, other suite choices, report locations and operator protections, see [the console guide](lab-console-implementation.md).
