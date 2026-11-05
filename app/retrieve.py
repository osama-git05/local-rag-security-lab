import argparse

import chromadb
import httpx

from app.auth import Principal
from app.ingest import DATABASE, COLLECTION_NAME, EMBEDDING_MODEL


def _retrieve(question: str, top_k: int = 2, where=None):
    question = question.strip()

    if not question or len(question) > 4000:
        raise ValueError("Question must contain between 1 and 4000 characters.")

    if not 1 <= top_k <= 4:
        raise ValueError("top_k must be between 1 and 4.")

    database = chromadb.PersistentClient(path=str(DATABASE))
    collection = database.get_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
    )

    if collection.metadata.get("embedding_model") != EMBEDDING_MODEL:
        raise ValueError("Collection embedding model does not match.")

    eligible_ids = collection.get(
        where=where,
        include=[],
    )["ids"]

    if not eligible_ids:
        return []

    with httpx.Client(timeout=180.0) as client:
        response = client.post(
            "http://127.0.0.1:11434/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": question,
                "truncate": False,
            },
        )
        response.raise_for_status()
        embedding = response.json()["embeddings"][0]

    results = collection.query(
        query_embeddings=[embedding],
        where=where,
        n_results=min(top_k, len(eligible_ids)),
        include=["documents", "metadatas", "distances"],
    )

    return [
        {
            "id": record_id,
            "text": text,
            "metadata": metadata,
            "distance": distance,
        }
        for record_id, text, metadata, distance in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def retrieve_unfiltered(question: str, top_k: int = 2):
    # Retained for explicit local baseline experiments.
    return _retrieve(question, top_k)


def retrieve_authorized(
    question: str,
    principal: Principal,
    top_k: int = 2,
):
    permissions = {
        "employee": ["employee"],
        "admin": ["employee", "admin"],
    }

    allowed = permissions.get(principal.role)

    if allowed is None:
        raise PermissionError("Unknown role.")

    matches = _retrieve(
        question,
        top_k,
        where={"access_level": {"$in": allowed}},
    )

    # Check again before any retrieved content reaches generation.
    for match in matches:
        metadata = match["metadata"] or {}

        if metadata.get("access_level") not in allowed:
            raise PermissionError("Retrieved document violates access policy.")

    return matches


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run an explicit unfiltered baseline retrieval test."
    )
    parser.add_argument("question")
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()

    if not args.baseline:
        parser.error("Use --baseline for unfiltered local experiments.")

    print("Mode: UNFILTERED BASELINE")

    for match in retrieve_unfiltered(args.question):
        print(f"\nDocument: {match['id']}")
        print(f"Metadata: {match['metadata']}")
        print(match["text"])