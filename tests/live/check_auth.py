from app.paths import ROOT
from pathlib import Path

import httpx
from dotenv import dotenv_values

tokens = dotenv_values(ROOT / ".env")

cases = [
    ("Missing token", None, 401, None),
    ("Invalid token", "invalid-test-token", 401, None),
    (
        "Employee token",
        tokens["EMPLOYEE_TOKEN"],
        200,
        {"user_id": "employee-01", "role": "employee"},
    ),
    (
        "Administrator token",
        tokens["ADMIN_TOKEN"],
        200,
        {"user_id": "admin-01", "role": "admin"},
    ),
]

failures = 0

with httpx.Client(timeout=10.0) as client:
    for label, token, expected_status, expected_identity in cases:
        headers = {}

        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        response = client.get(
            "http://127.0.0.1:8001/whoami",
            headers=headers,
        )

        passed = response.status_code == expected_status

        if expected_identity is not None:
            passed = passed and response.json() == expected_identity

        result = "PASS" if passed else "FAIL"
        print(f"{result} | {label} | HTTP {response.status_code}")

        if not passed:
            failures += 1

print(f"\nPassed: {len(cases) - failures}/{len(cases)}")
raise SystemExit(1 if failures else 0)