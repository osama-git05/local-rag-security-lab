# File moves

- `auth.py` -> `app/auth.py`
- `ingest.py` -> `app/ingest.py`
- `main.py` -> `app/main.py`
- `output_validation.py` -> `app/output_validation.py`
- `paths.py` -> `app/paths.py`
- `query_guard.py` -> `app/query_guard.py`
- `rag.py` -> `app/rag.py`
- `retrieve.py` -> `app/retrieve.py`
- `capture_environment.py` -> `scripts/capture_environment.py`
- `setup_tokens.py` -> `scripts/setup_tokens.py`
- `run_extended_regression.py` -> `evaluation/run_extended_regression.py`
- `run_regression.py` -> `evaluation/run_regression.py`
- `prepare_lab_model.py` -> `experiments/prepare_lab_model.py`
- `check_api_authorization.py` -> `tests/isolated/check_api_authorization.py`
- `check_authorization.py` -> `tests/isolated/check_authorization.py`
- `check_output_validation.py` -> `tests/isolated/check_output_validation.py`
- `check_query_output.py` -> `tests/isolated/check_query_output.py`
- `check_retrieval_authorization.py` -> `tests/isolated/check_retrieval_authorization.py`
- `check_retrieval_policy.py` -> `tests/isolated/check_retrieval_policy.py`
- `check_auth.py` -> `tests/live/check_auth.py`
- `check_chroma_authorization.py` -> `tests/live/check_chroma_authorization.py`

Screenshots: `screenshots/` -> `docs/screenshots/`. Numbered Markdown copies now use canonical names. The model template is in `experiments/`.

Recapture environment snapshots after the layout change. Historical snapshots and reports are preserved.
