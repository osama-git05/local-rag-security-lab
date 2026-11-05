from unittest.mock import patch

import chromadb
import httpx

from app import retrieve
from app.auth import Principal
from app.ingest import COLLECTION_NAME, DATABASE


ADMIN_DOCUMENT = "admin-finance"
QUESTION = "Finance administration notes."

if not DATABASE.exists():
    raise RuntimeError("Database missing. Run python -m app.ingest first.")

database = chromadb.PersistentClient(path=str(DATABASE))
collection = database.get_collection(
    name=COLLECTION_NAME,
    embedding_function=None,
)

seed = collection.get(
    ids=[ADMIN_DOCUMENT],
    include=["embeddings", "metadatas"],
)

if seed["ids"] != [ADMIN_DOCUMENT]:
    raise RuntimeError("admin-finance is missing from the database.")

metadata = seed["metadatas"][0] or {}

if metadata.get("access_level") != "admin":
    raise RuntimeError("admin-finance must have the admin access label.")

vectors = seed["embeddings"]

if vectors is None or len(vectors) != 1:
    raise RuntimeError("The administrator document embedding is missing.")

admin_vector = [float(value) for value in vectors[0]]

embedding_response = httpx.Response(
    200,
    json={"embeddings": [admin_vector]},
    request=httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/embed",
    ),
)

# Only the embedding HTTP adapter is simulated.
# Chroma get/query operations run against the actual database.
with patch.object(retrieve, "httpx") as embedding_http:
    embedding_post = (
        embedding_http.Client.return_value
        .__enter__.return_value.post
    )
    embedding_post.return_value = embedding_response

    baseline = retrieve.retrieve_unfiltered(
        QUESTION,
        top_k=4,
    )

    employee = retrieve.retrieve_authorized(
        QUESTION,
        Principal("employee-01", "employee"),
        top_k=4,
    )

    admin = retrieve.retrieve_authorized(
        QUESTION,
        Principal("admin-01", "admin"),
        top_k=4,
    )

    if embedding_post.call_count != 3:
        raise RuntimeError(
            "Expected three retrieval embedding requests."
        )

baseline_ids = {match["id"] for match in baseline}
employee_ids = {match["id"] for match in employee}
admin_ids = {match["id"] for match in admin}

checks = [
    (
        "Baseline retrieves administrator document",
        ADMIN_DOCUMENT in baseline_ids,
    ),
    (
        "Employee retrieval excludes restricted records",
        bool(employee)
        and ADMIN_DOCUMENT not in employee_ids
        and all(
            match["metadata"]["access_level"] == "employee"
            for match in employee
        ),
    ),
    (
        "Administrator retrieval permits administrator document",
        ADMIN_DOCUMENT in admin_ids
        and all(
            match["metadata"]["access_level"] in {"employee", "admin"}
            for match in admin
        ),
    ),
]

failures = 0

for label, passed in checks:
    failures += int(not passed)
    result = "PASS" if passed else "FAIL"
    print(f"{result} | {label}")

print("\nBaseline IDs:", ", ".join(sorted(baseline_ids)))
print("Employee IDs:", ", ".join(sorted(employee_ids)))
print("Administrator IDs:", ", ".join(sorted(admin_ids)))

print(f"\nPassed: {len(checks) - failures}/{len(checks)}")
raise SystemExit(1 if failures else 0)