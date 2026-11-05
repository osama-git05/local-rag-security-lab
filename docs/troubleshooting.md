# Troubleshooting

Use the actual status, response body and server traceback to choose a fix. Authentication, retrieval and generation are separate stages. Do not count an infrastructure error as a blocked attack.

## 401: Missing or invalid authentication token

This is the authentication dependency's response before the RAG handler runs. Common possibilities include a missing header, a stale token, copying `.env` quotation marks, an incorrect pasted value, or a process that loaded older credentials. The exact cause of each session failure was not established.

1. Verify which server port is being tested.
2. Run `python -m tests.live.check_auth` against the company server on port 8001.
3. If the script accepts credentials but Swagger does not, log out Swagger's old account and authorize again with the parsed token value.
4. If the script rejects a locally current credential, restart the intended process so it rereads the module-relative `.env`, then retest.

Safely copy the employee value from the project directory:

```powershell
.\.venv\Scripts\python.exe -c "from dotenv import dotenv_values; print(dotenv_values('.env')['EMPLOYEE_TOKEN'], end='')" | Set-Clipboard
```

Paste into Swagger's HTTPBearer authorization field without adding `Bearer`. Confirm `/whoami` returns the intended role. Do not paste the token into issues or screenshots.

## 422: Unprocessable Entity

Inspect the response's `detail` field. `/query` expects:

```json
{"question": "How much annual leave do employees receive?"}
```

`/generate` expects `prompt` instead. Extra fields are forbidden; field lengths are limited to 1 to 4000 characters, and whitespace-only content is rejected in the handler. A reported 422 occurred during development, but its precise rejected input was not retained.

## Invalid manifest JSON

A missing comma after the newly inserted injection entry was identified and corrected. Adjacent objects inside an array need a comma between them; the final object needs no trailing comma.

```powershell
.\.venv\Scripts\python.exe -m json.tool data\manifest.json
```

Once valid, run `app/ingest.py` and inspect its labels/counts. Do not infer successful ingestion merely from saving the JSON file.

## Ingestion rejects existing collection IDs

The shared script stops when the collection contains records absent from the current manifest. This prevents accidental stale-document retention during a nominal rebuild.

Review the manifest, collection and intended dataset state before changing anything. A controlled removal/rebuild procedure is still to be documented. Do not blindly erase `.chroma` or remove the validation check to get a passing run.

## 500: Internal Server Error

Find the request in the terminal serving that exact port, then retain `ERROR: Exception in ASGI application` and the final exception line. Copy the traceback without credentials or unrelated personal paths.

During this session, a 500 on port 8000 had no captured traceback. A fresh diagnostic instance succeeded on port 8001:

```powershell
.\.venv\Scripts\python.exe -u -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --log-level debug --access-log
```

Use `http://127.0.0.1:8001/docs` when testing that process. This was a diagnostic workaround, not a confirmed root-cause fix. Running another process does not stop or update the earlier one.

## 502 or 504 from the model/RAG adapter

The shared routes map selected HTTP/response-validation errors to 502 and HTTP timeouts to 504. That differs from an unhandled 500.

Check that Ollama is running at the configured address, that the requested model exists, and that the expected response fields are present. A timeout does not establish a policy decision. Preserve the actual traceback and local runtime state before increasing limits.

The replacement RAG code rejects nonempty-response failures and `done_reason: length`. A generation request rejected for truncation should be recorded as an error, not silently presented as a complete answer.

## Qwen emits long analysis instead of finishing

Observed behavior: 256 output tokens were exhausted before a concise answer. `/api/chat`, `think: false`, `/no_think` and a separate template experiment did not resolve the tested setup. The template contained an opening `<think>` prefix, but that observation did not prove the full cause.

The working route in this session was to test another installed model and select `optimized-gemma:latest`. Do not claim the template experiment fixed Qwen. Do not blindly strip analysis or increase limits and relabel an unfinished answer as successful.

## Literal `<eos>`, repetition or missing citations

The first Gemma RAG response showed these artifacts. Stop sequences for `<eos>` and `<end_of_turn>`, clearer answer instructions and a reported-truncation check were added. A later answer was clean and included `[policy-leave]`.

If artifacts recur, retain the raw local response and inspect the actual custom model template and parameters. The current controls do not establish a universal template fix or citation validator.

## Old mode after replacing `app/rag.py`

The replacement code defines:

```python
MODE = "retrieval_authorized_prompt_hardened"
```

An initial screenshot still showed `retrieval_authorized`. This mismatch was later resolved: the saved module was correct, but the listener on port 8001 needed a targeted restart. Restart the intended listener after confirming its identity; the current development command includes `--reload`.

If the old label persists, run from the project folder:

```powershell
.\.venv\Scripts\python.exe -c "import rag; print('Loaded file:', rag.__file__); print('Mode:', getattr(rag, 'MODE', 'MODE constant missing'))"
```

Inspect the actual imported file. Sanitize personal directory names before publishing diagnostic output. In this session the module path, new constant, function use of `MODE` and absence of inline old-mode strings were all correct. Identifying and restarting the real listener resolved the mismatch. A changed string by itself is not proof that all intended prompt changes were applied; compare the saved code too.

## `_PROMPT` is defined but `SYSTEM_PROMPT` is referenced

The pasted code defined `_PROMPT` while the payload referenced `SYSTEM_PROMPT`. Use one matching name. The provided complete replacement consistently defines and references `SYSTEM_PROMPT`.

The same pasted snippet also contained `OLLAMA_URL,SYSTEM` before `json=payload`. The corrected call is:

```python
response = client.post(
    OLLAMA_URL,
    json=payload,
)
```

These are identified source errors in a pasted edit. They were not established as the cause of the earlier port-8000 failure.

## Injection fixture absent from sources

Confirm that its file and manifest entry exist and ingestion succeeded. Verify the role can access it and use the intended onboarding question. If it is not retrieved, classify the attempt as not exercised for model-resistance purposes rather than counting a successful defense.

## Admin marker appears in an administrator answer

That is expected under the current positive authorization control. The marker is deliberately synthetic. The employee must not retrieve it. A policy to redact secrets for every role would be a separate output control, which is not implemented here.

## Citation unit tests pass but API tests return 200 for invalid output

This occurred: the function-level suite passed, but route integration passed only 2/4. A function can be correct without being connected to the API return path.

Verify that `app/rag.py` imports `validate_citations` and assigns its result before returning the generated answer:

```python
answer = validate_citations(
    data["response"],
    {match["id"] for match in matches},
)
```

The corrected route integration passed 4/4. It imports the application in a fresh process, so restarting a separate Uvicorn listener does not fix an unsaved or incorrect file used by that test.

## Live employee query returns 502 for an uncited refusal

The confirmed cause in this case was the exact-message refusal exception, not a broken retrieval filter. The traceback showed a missing citation, and temporary answer inspection showed a legitimate complete no-answer variation.

The observed refusal is now matched as a complete normalized message and returned as the canonical response. An appended uncited factual claim does not qualify. Keep normal citation enforcement enabled; accepting every answer without citations would bypass the tested output rule. Other unseen refusal variants may still require review.

The later live response used the canonical message and employee-only sources. Server-side exception logging remains available for failures. The temporary raw-answer print should be removed before publication; do not retain prompts or real sensitive content in diagnostic logs.

## Expected exceptions during negative integration tests

`tests/isolated/check_query_output.py` deliberately supplies missing and out-of-set citations. A logged traceback plus HTTP 502 is expected for those cases. The final confirmed output was 4/4, with valid citations and the standard no-answer response returning 200.

Do not interpret those deliberate exceptions as unexpected live-generation failures. Conversely, a legitimate live request rejected because of incompatible output formatting is a compatibility issue that should be recorded and fixed.

## Test script cannot be opened

The authorization test initially failed with a file-not-found message. Create `tests/isolated/check_authorization.py` in the project root, paste the complete test code and save it before invoking it.

```powershell
Test-Path .\tests/isolated/check_authorization.py
.\.venv\Scripts\python.exe -m tests.isolated.check_authorization
```

The observed result after saving was eight tests and OK. Activation of `.venv` does not create the test file.

## Literal PID placeholder gives an invalid CIM query

The process command initially failed because `REPLACE_WITH_PID` was left as literal text. This automatic discovery avoids manual substitution:

```powershell
$labProcessIds = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

foreach ($labProcessId in $labProcessIds) {
    Get-CimInstance Win32_Process -Filter "ProcessId = $labProcessId" |
        Select-Object ProcessId, ExecutablePath, CommandLine |
        Format-List
}
```

Confirm that the identified process is the lab's Uvicorn listener before stopping it. Never reuse a recorded PID later or stop every Python process. Restart the project server from the intended directory, wait for startup and execute a fresh request.

## Real-index test does not contact Ollama

That is intentional. The Chroma integration test supplies the stored administrator vector to make the permission comparison repeatable. It still runs actual database get/query operations and production retrieval functions. It verifies the exercised metadata boundary, not model relevance or end-to-end performance.

## Prepared live runner stops before requests

The separately available `evaluation/run_regression.py` requires an environment snapshot and matching saved-source/manifest/corpus hashes. A missing or stale snapshot is a precondition failure, not a model-security result. Verify the current `scripts/capture_environment.py`, its output and the implementation expected by the runner before using it; no successful full runner execution is claimed in this update.
