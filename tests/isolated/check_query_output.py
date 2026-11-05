from app.paths import ROOT
from pathlib import Path
from unittest.mock import patch

import httpx
from dotenv import dotenv_values
from fastapi.testclient import TestClient

from app import rag
from app.main import app
from app.output_validation import NO_ANSWER


tokens = dotenv_values(ROOT / ".env")
employee_token = tokens.get("EMPLOYEE_TOKEN")

if not employee_token:
    raise RuntimeError("EMPLOYEE_TOKEN is missing from .env.")

matches = [
    {
        "id": "policy-leave",
        "text": "Employees receive 25 days of annual leave per year.",
        "metadata": {
            "source": "leave-policy.md",
            "access_level": "employee",
        },
    }
]

cases = [
    (
        "Valid citation",
        "Employees receive 25 days [policy-leave].",
        200,
    ),
    (
        "Citation outside retrieved set",
        "Employees receive 25 days [admin-finance].",
        502,
    ),
    (
        "Missing citation",
        "Employees receive 25 days.",
        502,
    ),
    (
        "Standard no-answer response",
        NO_ANSWER,
        200,
    ),
]

failures = 0

with TestClient(app) as client:
    for label, generated_answer, expected_status in cases:
        simulated_response = httpx.Response(
            200,
            json={
                "response": generated_answer,
                "done_reason": "stop",
            },
            request=httpx.Request("POST", rag.OLLAMA_URL),
        )

        with (
            patch(
                "app.rag.retrieve_authorized",
                return_value=matches,
            ) as retrieval,
            patch("app.rag.httpx.Client") as model_client,
        ):
            model_post = (
                model_client.return_value
                .__enter__.return_value.post
            )
            model_post.return_value = simulated_response

            response = client.post(
                "/query",
                headers={
                    "Authorization": f"Bearer {employee_token}",
                },
                json={
                    "question": "How much annual leave do employees receive?",
                },
            )

        passed = (
            response.status_code == expected_status
            and retrieval.call_count == 1
            and model_post.call_count == 1
        )

        body = response.json()

        if expected_status == 200:
            passed = passed and body.get("answer") == generated_answer
            passed = passed and body.get("sources") == [
                {
                    "document_id": "policy-leave",
                    "source": "leave-policy.md",
                    "access_level": "employee",
                }
            ]
        else:
            passed = passed and body == {
                "detail": "Could not complete the local RAG request."
            }

        failures += int(not passed)
        result = "PASS" if passed else "FAIL"
        print(f"{result} | {label} | HTTP {response.status_code}")

print(f"\nPassed: {len(cases) - failures}/{len(cases)}")
raise SystemExit(1 if failures else 0)