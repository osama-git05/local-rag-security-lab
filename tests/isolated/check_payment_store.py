"""Version retention, exact provenance and transactional activation checks."""
import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

from app.payment_store import active_dataset, activate_payment_csv
from app.paths import ROOT, PAYMENTS_DB
from app.payments import PaymentValidationError
from scripts.import_payments import main

RAW = (ROOT / "tests" / "fixtures" / "supplier-payments.csv").read_bytes()


class PaymentStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "payments.sqlite3"

    def test_first_activation_preserves_exact_source_and_rows(self):
        metadata = activate_payment_csv(RAW, self.db)
        self.assertEqual(active_dataset(self.db), metadata)
        self.assertEqual(metadata["source_sha256"], sha256(RAW).hexdigest())
        self.assertEqual(metadata["row_count"], 8)
        self.assertTrue(metadata["imported_at_utc"].endswith("+00:00"))
        with contextlib.closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT source_csv FROM datasets").fetchone()[0], RAW)
            row = connection.execute("SELECT amount_millibhd, source_line FROM payments WHERE payment_id='PAY-003'").fetchone()
            self.assertEqual(row, (7250125, 4))

    def test_reimport_retains_history_and_activates_new_version(self):
        first = activate_payment_csv(RAW, self.db)
        second = activate_payment_csv(RAW, self.db)
        self.assertNotEqual(first["version"], second["version"])
        self.assertEqual(active_dataset(self.db), second)
        with contextlib.closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM datasets").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT count(*) FROM payments").fetchone()[0], 16)

    def test_invalid_import_does_not_create_or_change_database(self):
        with self.assertRaises(PaymentValidationError):
            activate_payment_csv(b"bad", self.db)
        self.assertFalse(self.db.exists())
        first = activate_payment_csv(RAW, self.db)
        before = self.db.read_bytes()
        with self.assertRaises(PaymentValidationError):
            activate_payment_csv(RAW + b"bad row\n", self.db)
        self.assertEqual(active_dataset(self.db), first)
        self.assertEqual(self.db.read_bytes(), before)

    def test_failure_during_activation_rolls_back_inserted_version_and_rows(self):
        first = activate_payment_csv(RAW, self.db)
        with contextlib.closing(sqlite3.connect(self.db)) as connection:
            connection.execute("CREATE TRIGGER simulated_failure BEFORE UPDATE ON active_dataset BEGIN SELECT RAISE(ABORT, 'interrupted activation'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            activate_payment_csv(RAW.replace(b"5500.000", b"5501.000"), self.db)
        self.assertEqual(active_dataset(self.db), first)
        with contextlib.closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM datasets").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM payments").fetchone()[0], 8)

    def test_historical_versions_cannot_be_updated_or_deleted(self):
        activate_payment_csv(RAW, self.db)
        with contextlib.closing(sqlite3.connect(self.db)) as connection:
            for table in ("datasets", "payments"):
                for sql in (f"DELETE FROM {table}", f"UPDATE {table} SET version='changed'"):
                    with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                        connection.execute(sql)

    def test_unknown_schema_is_not_overwritten(self):
        with contextlib.closing(sqlite3.connect(self.db)) as connection:
            connection.execute("CREATE TABLE unrelated (value TEXT)")
        with self.assertRaises(sqlite3.DatabaseError):
            activate_payment_csv(RAW, self.db)
        with contextlib.closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(), [("unrelated",)])

    def test_concurrent_imports_produce_complete_versions(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            versions = list(pool.map(lambda _: activate_payment_csv(RAW, self.db), range(2)))
        self.assertIn(active_dataset(self.db)["version"], [v["version"] for v in versions])
        with contextlib.closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM datasets").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT count(*) FROM payments").fetchone()[0], 16)

    def test_missing_read_does_not_create_database_and_default_is_root_relative(self):
        self.assertIsNone(active_dataset(self.db))
        self.assertFalse(self.db.exists())
        self.assertEqual(PAYMENTS_DB, ROOT / "data" / "payments.sqlite3")

    def test_cli_activation_and_safe_errors(self):
        source = Path(self.temporary.name) / "fixture.csv"
        source.write_bytes(RAW)
        output = io.StringIO()
        real_activate = activate_payment_csv
        with patch("scripts.import_payments.activate_payment_csv", side_effect=lambda raw: real_activate(raw, self.db)):
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([str(source)]), 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "active")
        for error in (sqlite3.OperationalError("private database path"), OSError("private path")):
            output = io.StringIO()
            with patch("scripts.import_payments.activate_payment_csv", side_effect=error), contextlib.redirect_stdout(output):
                self.assertEqual(main([str(source)]), 1)
            self.assertNotIn("private", output.getvalue())


if __name__ == "__main__":
    unittest.main()
