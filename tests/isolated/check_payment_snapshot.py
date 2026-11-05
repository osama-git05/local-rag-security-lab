"""Verify snapshot compatibility across payment dataset activations."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.paths import ROOT
from app.payment_store import active_dataset, activate_payment_csv
from evaluation.run_regression import check_payment_dataset


class PaymentSnapshotTests(unittest.TestCase):
    def test_same_csv_reactivation_invalidates_snapshot(self):
        data = (ROOT / "tests/fixtures/supplier-payments.csv").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "payments.sqlite3"
            with patch("evaluation.run_regression.active_dataset",
                       side_effect=lambda: active_dataset(database)):
                check_payment_dataset({"active_payment_dataset": None})
                self.assertFalse(database.exists())
                first = activate_payment_csv(data, database)
                snapshot = {"active_payment_dataset": first}
                check_payment_dataset(snapshot)
                second = activate_payment_csv(data, database)
                self.assertEqual(first["source_sha256"], second["source_sha256"])
                with self.assertRaisesRegex(ValueError, "Active payment dataset changed"):
                    check_payment_dataset(snapshot)

    def test_legacy_snapshot_requires_recapture(self):
        with self.assertRaisesRegex(ValueError, "lacks payment dataset metadata"):
            check_payment_dataset({})

    def test_unreadable_database_reports_safe_error(self):
        with patch("evaluation.run_regression.active_dataset",
                   side_effect=sqlite3.DatabaseError("private path")):
            with self.assertRaisesRegex(ValueError, "^Cannot read active payment dataset metadata"):
                check_payment_dataset({"active_payment_dataset": None})


if __name__ == "__main__":
    unittest.main()
