"""Expected live responses for the synthetic supplier-payment fixture."""

from app.paths import ROOT


FIXTURE = ROOT / "tests/fixtures/supplier-payments.csv"
ENDPOINT = "/payments/query"
OPERATION = "supplier_payments_above_threshold"


CASES = [
    {
        "id": "payments-october",
        "role": "admin",
        "month": "2026-10",
        "status": 200,
        "total": "18750.125",
        "rows": [
            ("PAY-001", "Demo Cedar Supplies", "2026-10-01", "5500.000", 2),
            ("PAY-003", "Demo Palm Systems", "2026-10-15", "7250.125", 4),
            ("PAY-004", "Demo Cedar Supplies", "2026-10-31", "6000.000", 5),
        ],
    },
    {
        "id": "payments-november",
        "role": "admin",
        "month": "2026-11",
        "status": 200,
        "total": "8000.000",
        "rows": [("PAY-006", "Demo Dune Equipment", "2026-11-01", "8000.000", 7)],
    },
    {
        "id": "payments-empty-month",
        "role": "admin",
        "month": "2026-12",
        "status": 200,
        "total": "0.000",
        "rows": [],
    },
    {
        "id": "payments-employee-denied",
        "role": "employee",
        "month": "2026-10",
        "status": 403,
    },
]

for case in CASES:
    case["endpoint"] = ENDPOINT
    case["body"] = {"operation": OPERATION, "month": case["month"]}


def grade_payment_response(case, status, body, snapshot):
    checks = {"expected_http_status": status == case["status"]}
    if case["status"] == 403:
        checks["denial_without_finance_data"] = body == {"detail": "Access denied."}
        return checks

    if not isinstance(body, dict):
        body = {}
    row_fields = ("payment_id", "supplier_name", "payment_date", "amount_bhd", "source_line")
    expected_rows = [dict(zip(row_fields, row)) for row in case["rows"]]
    dataset = snapshot["active_payment_dataset"]
    checks.update({
        "operation_and_month": body.get("operation") == OPERATION and body.get("month") == case["month"],
        "currency_and_threshold": body.get("currency") == "BHD" and body.get("threshold_bhd") == "5000.000",
        "exact_total": body.get("total_bhd") == case["total"],
        "exact_rows_and_source_lines": body.get("rows") == expected_rows and body.get("row_count") == len(expected_rows),
        "captured_dataset_provenance": body.get("dataset") == {
            key: dataset[key] for key in ("version", "source_sha256", "imported_at_utc")
        },
        "policy_provenance_and_excerpt": body.get("policy") == {
            "document_id": "admin-finance",
            "source": "finance-admin.md",
            "access_level": "admin",
            "trust_level": "curated",
            "dataset_version": snapshot["dataset_version"],
            "source_sha256": snapshot["corpus_file_sha256"]["finance-admin.md"],
            "manifest_sha256": snapshot["manifest_sha256"],
            "excerpt": (
                "The finance team reviews supplier payments every Friday.\n"
                "Payments above 5000 BHD require approval from two administrators."
            ),
            "start_line": 5,
            "end_line": 6,
        },
    })
    return checks
