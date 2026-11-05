# Environment and reproducibility record

## Active payment dataset tracking — 5 November 2026

Environment capture records the active payment version, source CSV SHA-256, import timestamp and row count. It records an explicit null when there is no active dataset. Capture reads metadata from SQLite without creating a database or including payment rows.

The regression runner compares the snapshot metadata with the local active dataset before running cases and again after the last case. A new activation requires recapture even when it imports identical CSV bytes. A mismatch at the end fails the workflow while preserving the individual case results. Older snapshots remain available as historical evidence and require recapture for a current run.

The report records the captured dataset and the final compatibility check. The checks compare the local active pointer at two points in time. The latest extended workflow also exercises the payment endpoint and checks returned provenance.

Run the capture and regression together with `.venv\Scripts\python.exe -m scripts.lab_console --suite extended`.

The initial 5 November workflow passed 126 isolated checks, three index authorization checks and all 12 live RAG cases. The later run added four live payment cases, for 16 total, and passed dataset compatibility. [Initial workflow](../results/lab-workflow-20261105T103141459241Z-30ca1925.json) · [Initial case report](../results/development-regression-20261105T103203243363Z.json) · [Initial snapshot](../results/environment-20261105T103201467256Z.json) · [Latest snapshot](../results/environment-20261105T103928690087Z.json).

## Combined policy milestone — 4 November 2026

[environment-20261104T203500740652Z.json](../results/environment-20261104T203500740652Z.json) records the first combined payment-policy milestone. All 47 Python-source and six asset hashes matched. Its associated [extended workflow](../results/lab-workflow-20261104T203442939723Z-de882dad.json) passed 123 isolated checks, three index checks and all twelve existing RAG cases. The [14-case browser report](../results/payment-ui-verification-20261104T203425201Z.json) records active payment and exact policy provenance plus screenshot/driver/fixture hashes; source remained unchanged between the browser run and later capture. Its capture-after-checks association is explicit. Original corpus/manifest were preserved. This run predates automated payment compatibility checks.

## Payment interface milestone — 4 November 2026

The [environment-20261104T202223012020Z.json](../results/environment-20261104T202223012020Z.json) captures the payment frontend and optional live browser driver. All 45 Python-source and six asset hashes matched after execution. It is linked to the [12-case browser report](../results/payment-ui-verification-20261104T202147653Z.json), with capture-after-checks ordering stated explicitly and unchanged driver/fixture/frontend hashes verified. Payment provenance remains an explicit report field rather than an automatically enforced snapshot field. This does not supersede or relabel the older LLM reports below. See [the milestone guide](payment-ui.md).

## Operator workflow capture on 4 November 2026

The [environment-20261104T174452431671Z.json](../results/environment-20261104T174452431671Z.json) captures content-hashed assistant asset delivery and explicit no-store headers. Five UI-route checks and a live script/version/header check passed. No additional model-case evaluation is attributed to this presentation/cache update; earlier live reports remain associated with their own snapshots.

The later [environment-20261104T173711255044Z.json](../results/environment-20261104T173711255044Z.json) captures the presentation-only change that hides inline citation tags in chat prose. It updates the interface hash; source chips and the citation-bearing API response remain intact. JavaScript syntax and sample formatting were checked. No new live generation/evaluation is attributed to this asset capture; the twelve-case passing report below belongs to its original snapshot.

The refusal-fix retest now uses [environment-20261104T171734132005Z.json](../results/environment-20261104T171734132005Z.json), associated with [the passing workflow](../results/lab-workflow-20261104T171718796408Z-cf0afb79.json) and [12/12 extended case report](../results/development-regression-20261104T171735992539Z.json). Current-source compatibility passed. The [before/after verification](../results/refusal-fix-verification-20261104T171946867356Z.json) confirms identical model digests, prompt/mode and corpus/manifest hashes; only the validator and new targeted Python test changed. The captures below remain historical evidence.

The earlier operator implementation run used [environment-20261104T142300564638Z.json](../results/environment-20261104T142300564638Z.json). It records actual package versions, installed generation/embedding identifiers and digests, corpus hashes, Python source hashes and six interface assets. It matched that earlier source state; the later snapshot above covers the refusal fix. The later provenance review identified the exact weight and recorded the local settings. Terms for redistribution of the merged artifact remain unresolved. [Model provenance](model-provenance.md).

The [workflow record](../results/lab-workflow-20261104T142248372652Z-d41920c1.json) links this snapshot to the completed [extended case report](../results/development-regression-20261104T142302177784Z.json). Historical snapshots remain unchanged. The older checkpoint notes below describe their original evidence state and do not supersede this capture. Snapshots identify saved files, not an already-running API's loaded code.

Snapshot date: 3 November 2026. Only values established by the shared code or reported outputs are included. Hardware details from other projects are not assumed to describe this run.

## Recorded values

| Item | Recorded value | Evidence or qualification |
| --- | --- | --- |
| Development shell | Windows PowerShell | Commands and outputs from the local development session |
| Python environment | `.venv`; process/traceback paths include `Python311` | Python 3.11 installation path observed; exact version output still not retained |
| Ollama CLI | `0.20.5` | Reported by the developer; server version output not retained |
| Generation model | `optimized-gemma:latest` | Returned by successful API and direct smoke tests |
| Local model-list ID | `c40843ebaf9d` | Abbreviated ID from the reported listing, not a full digest |
| Displayed model size | 3.4 GB | Listing value; not measured RAM or VRAM use |
| Embedding model | `embeddinggemma` | Shared ingestion and retrieval configuration |
| Collection | `exampleco_documents` | Shared code |
| Vector-store directory | `.chroma/` | Shared code |
| Manifest version | `0.1.0` | Shared JSON, including injection fixture |
| Manifest entries | Five | All five named fixtures appeared across the real Chroma control results; total printed collection count not retained |
| Default retrieval count | 2 | Shared retrieval function default; validated range 1 to 4 |
| Generation temperature | 0 | Explicit RAG request override |
| Generation context setting | 4096 | Explicit RAG request override |
| Maximum output tokens | 256 | Explicit RAG request override |
| Thinking request | `false` | Request field; not a guarantee of a model's internal behavior |
| Streaming | `false` | Shared code |
| RAG stop sequences | `<eos>`, `<end_of_turn>` | Added during output troubleshooting |
| HTTP client timeout | 180 seconds per Ollama client request | Separate embedding and generation calls; not an overall request deadline |
| Working API base | `http://127.0.0.1:8001` | Successful diagnostic instance |
| Ollama base | `http://127.0.0.1:11434` | Shared code and direct tests |

The custom model has local optimizations according to the developer. The complete Modelfile, underlying model identity, quantization and GPU settings were not supplied. Do not infer them from the model tag or displayed size.

## Model experiments

| Model/configuration | Observed result |
| --- | --- |
| `qwen3:4b`, `/api/generate` | Verbose analysis appeared in answer output; earlier application answers were unfinished |
| `qwen3:4b`, fresh `/api/chat` control | 256-token limit reached; no completed short answer |
| `qwen3:4b`, `/no_think` appended | Same basic failure in the tested request |
| `qwen3-lab:4b`, modified template | Template experiment also reached the output cap without a clean answer |
| `llama3.1:latest`, fresh chat control | Returned “They receive 25 days.”; `stop`; 7 output tokens |
| `optimized-gemma:latest`, direct generation | Returned “Employees receive 25 days of annual leave.”; `stop`; 11 output tokens; zero reported thinking characters |

These were troubleshooting controls with different models/configurations. They do not establish a controlled speed or quality ranking.

## Capture before evaluation

Record Python, package and server versions, OS build, CPU, installed RAM, GPU and driver, actual accelerator placement, full model digest and model license. Preserve the custom model recipe with an approved distribution route. Export resolved dependencies to reviewed lock files.

Useful noncredential commands include:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip list
ollama --version
ollama list
ollama ps
Invoke-RestMethod http://127.0.0.1:11434/api/version
```

Inspect output before publishing, especially local filesystem paths or custom model metadata. Do not publish the real `.env` or account-token values.

## Unrecorded measurements

End-to-end latency, median/p95, cold-start cost, memory use, GPU utilization and concurrent load behavior have not been measured in a retained evaluation. Token counts from a control answer do not establish latency or throughput.

Future run records should include commit SHA, complete corpus fingerprint, prompt hash, model digest, role, settings, port/process configuration, timing method and outcome. No commit SHA or run ID has been invented for this snapshot.

## Current runtime and test evidence

The active response mode is `retrieval_authorized_prompt_hardened`. A saved-module check showed that `rag.MODE` had the new value and the function used that constant, while the listener still returned an old label. The Uvicorn process on port 8001 was identified by PID and command line, stopped and restarted; subsequent API responses used the new label.

The development command now includes `--reload`:

```powershell
.\.venv\Scripts\python.exe -u -m uvicorn app.main:app --app-dir . --host 127.0.0.1 --port 8001 --reload
```

PIDs are ephemeral and are not configuration values. A base-Python executable path in a Windows process report does not by itself prove that the virtual environment is wrong.

Observed automated results are eight authorization tests in 0.002 seconds (OK), four route/output integration cases (4/4), and three actual-index authorization checks (3/3). The unit-test duration is a test-run duration, not RAG response latency. The original citation suite passed 8/8; it was expanded to ten cases, but that full developer-machine rerun was not supplied.

The Chroma integration run uses a stored embedding as the query vector and does not call Ollama. The route/output test also simulates retrieval and generation. Neither should be timed or reported as end-to-end model performance.

A separate `evaluation/run_regression.py` artifact references `scripts/capture_environment.py` and `results/environment-*.json`, and checks hashes before a live run. An actual environment snapshot/report was not reviewed here. Its existence must not be used to populate missing hardware values, digests, source hashes or benchmark results.
