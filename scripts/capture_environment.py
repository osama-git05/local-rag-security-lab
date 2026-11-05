from app.paths import asset_files, source_files
from app.paths import ROOT
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import httpx

from app import ingest
from app import rag
from app.payment_store import active_dataset




def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed"


def git_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        return None


def main():
    captured_at = datetime.now(timezone.utc)
    ollama_base = rag.OLLAMA_URL.rsplit("/api/", 1)[0]

    with httpx.Client(timeout=30.0) as client:
        server_response = client.get(f"{ollama_base}/api/version")
        server_response.raise_for_status()

        models_response = client.get(f"{ollama_base}/api/tags")
        models_response.raise_for_status()

    installed_models = models_response.json()["models"]

    selected_models = {}

    for name in (rag.MODEL, ingest.EMBEDDING_MODEL):
        tagged_name = name if ":" in name else f"{name}:latest"

        matching = [
            item
            for item in installed_models
            if item["name"] in {name, tagged_name}
        ]

        if len(matching) != 1:
            raise ValueError(f"Could not identify model uniquely: {name}")

        item = matching[0]

        selected_models[name] = {
            "installed_name": item["name"],
            "digest": item["digest"],
            "size_bytes": item.get("size"),
            "details": item.get("details"),
        }

    manifest = json.loads(
        ingest.MANIFEST.read_text(encoding="utf-8-sig")
    )

    corpus_hashes = {}

    for entry in manifest["documents"]:
        path = (ingest.CORPUS / entry["file"]).resolve()

        if path.parent != ingest.CORPUS or path.suffix.lower() != ".md":
            raise ValueError("Unexpected corpus file path.")

        corpus_hashes[path.name] = file_hash(path)

    snapshot = {
        "captured_at_utc": captured_at.isoformat(),
        "git_commit": git_commit(),
        "python_version": platform.python_version(),
        "operating_system": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "packages": {
            name: package_version(name)
            for name in (
                "fastapi",
                "uvicorn",
                "chromadb",
                "httpx",
                "pydantic",
                "python-dotenv",
            )
        },
        "ollama_server_version": server_response.json()["version"],
        "models": selected_models,
        "mode": rag.MODE,
        "system_prompt_sha256": hashlib.sha256(
            rag.SYSTEM_PROMPT.encode("utf-8")
        ).hexdigest(),
        "dataset_version": manifest["dataset_version"],
        "active_payment_dataset": active_dataset(),
        "manifest_sha256": file_hash(ingest.MANIFEST),
        "corpus_file_sha256": corpus_hashes,
        "python_source_sha256": {
            path.relative_to(ROOT).as_posix(): file_hash(path)
            for path in source_files()
        },
        "application_asset_sha256": {
            path.relative_to(ROOT).as_posix(): file_hash(path)
            for path in asset_files()
        },
    }

    output_directory = ROOT / "results"
    output_directory.mkdir(exist_ok=True)

    timestamp = captured_at.strftime("%Y%m%dT%H%M%S%fZ")
    output_path = output_directory / f"environment-{timestamp}.json"

    output_path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Saved: results/{output_path.name}")
    print(f"Mode: {snapshot['mode']}")
    print(f"Models recorded: {len(selected_models)}")
    print(f"Corpus files recorded: {len(corpus_hashes)}")


if __name__ == "__main__":
    main()
