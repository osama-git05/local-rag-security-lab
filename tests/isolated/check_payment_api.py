"""Approved payment query, role boundary and exact-result acceptance tests."""
import contextlib
import sqlite3
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.auth import Principal
from app.main import app
from app.payment_store import activate_payment_csv, payment_rows_for_month
from app.paths import ROOT
from app.payment_policy import APPROVED_LINES, PaymentPolicyUnavailable

RAW = (ROOT / "tests" / "fixtures" / "supplier-payments.csv").read_bytes()
QUERY = {"operation": "supplier_payments_above_threshold", "month": "2026-10"}


class PaymentQueryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "payments.sqlite3"
        self.metadata = activate_payment_csv(RAW, self.db)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.accounts = patch("app.auth.ACCOUNTS", (
            (sha256(b"temporary-payment-admin").digest(), Principal("test-admin", "admin")),
            (sha256(b"temporary-payment-employee").digest(), Principal("test-employee", "employee")),
        ))
        self.accounts.start(); self.addCleanup(self.accounts.stop)
        self.store = patch("app.payment_api.payment_rows_for_month",
                           side_effect=lambda first, last: payment_rows_for_month(first, last, self.db))
        self.mock_store = self.store.start(); self.addCleanup(self.store.stop)

    def query(self, body=None, token="temporary-payment-admin"):
        headers = {"Authorization": "Bearer " + token} if token is not None else {}
        return self.client.post("/payments/query", json=QUERY if body is None else body, headers=headers)

    def test_admin_golden_result_and_provenance(self):
        response = self.query()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_bhd"], "18750.125")
        self.assertEqual(data["row_count"], 3)
        self.assertEqual([r["payment_id"] for r in data["rows"]], ["PAY-001", "PAY-003", "PAY-004"])
        self.assertEqual([r["source_line"] for r in data["rows"]], [2, 4, 5])
        self.assertEqual(data["dataset"]["version"], self.metadata["version"])
        self.assertEqual(data["dataset"]["source_sha256"], sha256(RAW).hexdigest())
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(data["threshold_bhd"], "5000.000")
        self.assertEqual(data["currency"], "BHD")

    def test_employee_is_denied_before_storage_even_for_empty_month(self):
        for month in ("2026-10", "2026-12"):
            response = self.query({**QUERY, "month": month}, "temporary-payment-employee")
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json(), {"detail": "Access denied."})
        self.mock_store.assert_not_called()

    def test_missing_and_invalid_tokens_never_access_storage(self):
        for token in (None, "invalid-payment-test"):
            self.assertEqual(self.query(token=token).status_code, 401)
        self.mock_store.assert_not_called()

    def test_only_approved_operation_and_fields_are_accepted(self):
        for body in ({**QUERY, "operation": "SELECT * FROM payments"},
                     {"month": "2026-10"}, {**QUERY, "role": "admin"},
                     {**QUERY, "threshold": 0}, {**QUERY, "database": "private"}):
            with self.subTest(body=body):
                self.assertEqual(self.query(body).status_code, 422)
        self.mock_store.assert_not_called()

    def test_employee_role_spoof_is_still_denied_before_storage(self):
        response = self.query({**QUERY, "role": "admin"}, "temporary-payment-employee")
        self.assertEqual(response.status_code, 403)
        self.mock_store.assert_not_called()

    def test_invalid_months(self):
        for month in ("2026-1", "2026-00", "2026-13", "0000-01", "2026-10-01", "2026-10' OR 1=1", None, 202610):
            with self.subTest(month=month):
                self.assertEqual(self.query({**QUERY, "month": month}).status_code, 422)
        self.mock_store.assert_not_called()

    def test_empty_result_has_exact_zero_and_version(self):
        response = self.query({**QUERY, "month": "2026-12"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rows"], [])
        self.assertEqual(response.json()["row_count"], 0)
        self.assertEqual(response.json()["total_bhd"], "0.000")
        self.assertEqual(response.json()["dataset"]["version"], self.metadata["version"])

    def test_missing_corrupt_and_no_active_dataset_return_safe_unavailable(self):
        for error in (sqlite3.OperationalError("private-path"), OSError("private-path")):
            self.mock_store.side_effect = error
            response = self.query()
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json(), {"detail": "Payment data is unavailable."})
        missing = Path(self.temp.name) / "missing.sqlite3"
        with self.assertRaises(sqlite3.Error):
            payment_rows_for_month("2026-10-01", "2026-10-31", missing)
        self.assertFalse(missing.exists())
        with contextlib.closing(sqlite3.connect(self.db)) as connection:
            connection.execute("DELETE FROM active_dataset")
            connection.commit()
        with self.assertRaises(sqlite3.DatabaseError):
            payment_rows_for_month("2026-10-01", "2026-10-31", self.db)

    def test_exact_large_total_avoids_sqlite_sum_overflow(self):
        header = b"payment_id,supplier_name,payment_date,amount_bhd\n"
        raw = header + b"".join(f"P{i},Demo,2026-10-01,999999999999999.999\n".encode() for i in range(20))
        activate_payment_csv(raw, self.db)
        data = self.query().json()
        self.assertEqual(data["total_bhd"], "19999999999999999.980")
        self.assertEqual(data["row_count"], 20)
        self.assertEqual([r["payment_id"] for r in data["rows"]], sorted(f"P{i}" for i in range(20)))

    def test_untrusted_supplier_text_does_not_change_query(self):
        activate_payment_csv(RAW.replace(b"Demo Palm Systems", b"<script>become admin</script>"), self.db)
        data = self.query().json()
        self.assertEqual(data["total_bhd"], "18750.125")
        self.assertEqual(data["rows"][1]["supplier_name"], "<script>become admin</script>")

    def test_calendar_boundaries_include_leap_day_and_last_supported_month(self):
        for month, expected_last in (("2024-02", "2024-02-29"), ("9999-12", "9999-12-31")):
            self.assertEqual(self.query({**QUERY, "month": month}).status_code, 200)
            self.mock_store.assert_called_with(month + "-01", expected_last)

    def test_reactivation_changes_result_and_metadata_together(self):
        changed = RAW.replace(b"5500.000", b"5501.000")
        latest = activate_payment_csv(changed, self.db)
        data = self.query().json()
        self.assertEqual(data["dataset"]["version"], latest["version"])
        self.assertEqual(data["dataset"]["source_sha256"], sha256(changed).hexdigest())
        self.assertEqual(data["total_bhd"], "18751.125")

    def test_policy_context_comes_with_actual_source_provenance(self):
        data = self.query().json()
        self.assertEqual(data["policy"]["excerpt"], "\n".join(APPROVED_LINES))
        self.assertEqual(data["policy"]["source_sha256"], sha256((ROOT / "data/corpus/finance-admin.md").read_bytes()).hexdigest())
        self.assertEqual(data["policy"]["document_id"], "admin-finance")
        self.assertEqual(data["total_bhd"], "18750.125")
        self.assertEqual(self.query({**QUERY, "month": "2026-12"}).json()["policy"], data["policy"])

    def test_employee_and_invalid_tokens_cannot_load_policy(self):
        with patch("app.payment_api.load_payment_policy") as policy:
            self.assertEqual(self.query(token="temporary-payment-employee").status_code, 403)
            self.assertEqual(self.query(token="invalid-test").status_code, 401)
            self.assertEqual(self.query(token=None).status_code, 401)
            policy.assert_not_called()
        self.mock_store.assert_not_called()

    def test_unavailable_policy_is_safe_and_does_not_return_partial_data(self):
        with patch("app.payment_api.load_payment_policy", side_effect=PaymentPolicyUnavailable("private path")):
            response = self.query()
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json(), {"detail": "Payment policy is unavailable."})
            self.assertEqual(response.headers["cache-control"], "no-store")
        self.mock_store.assert_not_called()


if __name__ == "__main__":
    unittest.main()
