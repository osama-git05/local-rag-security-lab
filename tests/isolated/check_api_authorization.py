from app.paths import ROOT
from pathlib import Path
from unittest.mock import patch

from dotenv import dotenv_values
from fastapi.testclient import TestClient

from app.main import app


tokens = dotenv_values(ROOT / ".env")
employee_token = tokens.get("EMPLOYEE_TOKEN")
admin_token = tokens.get("ADMIN_TOKEN")

if not employee_token or not admin_token:
    raise RuntimeError("Employee and administrator tokens are required.")

question = {"question": "How much annual leave do employees receive?"}

employee_identity = {
    "user_id": "employee-01",
    "role": "employee",
}

admin_identity = {
    "user_id": "admin-01",
    "role": "admin",
}

# label, method, path, token, body, expected status, expected identity
cases = [
    (
        "Missing identity",
        "GET", "/whoami", None, None, 401, None,
    ),
    (
        "Invalid identity",
        "GET", "/whoami", "invalid-test-token", None, 401, None,
    ),
    (
        "Employee identity",
        "GET", "/whoami", employee_token, None,
        200, employee_identity,
    ),
    (
        "Administrator identity",
        "GET", "/whoami", admin_token, None,
        200, admin_identity,
    ),
    (
        "Query without credentials",
        "POST", "/query", None, question, 401, None,
    ),
    (
        "Query with invalid credentials",
        "POST", "/query", "invalid-test-token", question, 401, None,
    ),
    (
        "Employee cannot submit an admin role",
        "POST", "/query", employee_token,
        {**question, "role": "admin"}, 422, None,
    ),
    (
        "Employee principal reaches pipeline",
        "POST", "/query", employee_token, question,
        200, employee_identity,
    ),
    (
        "Administrator principal reaches pipeline",
        "POST", "/query", admin_token, question,
        200, admin_identity,
    ),
]

stub_result = {
    "mode": "authorization_test",
    "model": "test_stub",
    "answer": "Synthetic test response.",
    "sources": [],
}

failures = 0

with TestClient(app) as client:
    for (
        label,
        method,
        path,
        token,
        body,
        expected_status,
        expected_identity,
    ) in cases:
        headers = {}

        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        with patch(
            "app.main.answer_question",
            return_value=stub_result,
        ) as pipeline:
            response = client.request(
                method,
                path,
                headers=headers,
                json=body,
            )

        passed = response.status_code == expected_status

        if path == "/whoami":
            passed = passed and pipeline.call_count == 0

            if expected_identity is not None:
                passed = passed and response.json() == expected_identity

        elif expected_status == 200:
            passed = passed and pipeline.call_count == 1

            if pipeline.call_count == 1:
                principal = pipeline.call_args.args[1]

                actual_identity = {
                    "user_id": principal.user_id,
                    "role": principal.role,
                }

                passed = passed and actual_identity == expected_identity
                passed = passed and response.json() == stub_result

        else:
            # Rejected requests must never reach the RAG pipeline.
            passed = passed and pipeline.call_count == 0

        failures += int(not passed)
        result = "PASS" if passed else "FAIL"

        print(f"{result} | {label} | HTTP {response.status_code}")

print(f"\nPassed: {len(cases) - failures}/{len(cases)}")
raise SystemExit(1 if failures else 0)