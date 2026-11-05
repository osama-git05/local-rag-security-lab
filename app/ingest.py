from app.paths import ROOT
import hashlib
import json
from pathlib import Path

import chromadb
import httpx

CORPUS = (ROOT / "data" / "corpus").resolve()
MANIFEST = ROOT / "data" / "manifest.json"
DATABASE = ROOT / ".chroma"

EMBEDDING_MODEL = "embeddinggemma"
COLLECTION_NAME = "exampleco_documents"


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    version = manifest["dataset_version"]
    entries = manifest["documents"]

    if not isinstance(version, str) or not version.strip():
        raise ValueError("Dataset version must be a nonempty string.")

    if not isinstance(entries, list) or not entries:
        raise ValueError("Manifest must contain documents.")

    ids = []
    documents = []
    metadata = []

    for entry in entries:
        document_id = entry["document_id"]
        access = entry["access_level"]
        trust = entry["trust_level"]

        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError("Document IDs must be nonempty strings.")

        if document_id in ids:
            raise ValueError(f"Duplicate document ID: {document_id}")

        if access not in {"employee", "admin"}:
            raise ValueError(f"Invalid access label: {document_id}")

        if trust not in {"curated", "untrusted"}:
            raise ValueError(f"Invalid trust label: {document_id}")

        path = (CORPUS / entry["file"]).resolve()

        if path.parent != CORPUS or path.suffix.lower() != ".md":
            raise ValueError("Only Markdown files inside corpus are allowed.")

        if path.stat().st_size > 20_000:
            raise ValueError("Document exceeds the initial lab size limit.")

        text = path.read_text(encoding="utf-8-sig").strip()

        if not text:
            raise ValueError(f"Empty document: {path.name}")

        ids.append(document_id)
        documents.append(text)
        metadata.append({
            "document_id": document_id,
            "source": path.name,
            "access_level": access,
            "trust_level": trust,
            "dataset_version": version,
            "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })

    print(f"Validated documents: {len(documents)}")

    with httpx.Client(timeout=180.0) as client:
        response = client.post(
            "http://127.0.0.1:11434/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": documents,
                "truncate": False,
            },
        )
        response.raise_for_status()
        embeddings = response.json()["embeddings"]

    if len(embeddings) != len(documents):
        raise ValueError("Embedding count does not match document count.")

    database = chromadb.PersistentClient(path=str(DATABASE))
    collection = database.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
        metadata={"embedding_model": EMBEDDING_MODEL},
    )

    if collection.metadata.get("embedding_model") != EMBEDDING_MODEL:
        raise ValueError("Collection uses a different embedding model.")

    existing_ids = set(collection.get(include=[])["ids"])
    if existing_ids - set(ids):
        raise ValueError(
            "Collection contains documents outside the current manifest. "
            "Stop and review before rebuilding."
        )

    before = collection.count()

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadata,
    )

    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Records before ingestion: {before}")
    print(f"Records after ingestion: {collection.count()}")

    for item in metadata:
        print(
            f"{item['document_id']} | "
            f"access={item['access_level']} | "
            f"trust={item['trust_level']}"
        )


if __name__ == "__main__":
    main()