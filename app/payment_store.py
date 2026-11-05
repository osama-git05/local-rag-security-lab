"""Versioned payment datasets; activation and insertion share one transaction.

Local maintenance API only. Future HTTP callers must authorize before access.
"""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.paths import PAYMENTS_DB
from app.payments import validate_payment_csv

SCHEMA = (
    "CREATE TABLE datasets (version TEXT PRIMARY KEY, source_sha256 TEXT NOT NULL, "
    "imported_at_utc TEXT NOT NULL, row_count INTEGER NOT NULL, source_csv BLOB NOT NULL)",
    "CREATE TABLE payments (version TEXT NOT NULL REFERENCES datasets(version), "
    "payment_id TEXT NOT NULL, supplier_name TEXT NOT NULL, payment_date TEXT NOT NULL, "
    "amount_millibhd INTEGER NOT NULL CHECK(amount_millibhd > 0), source_line INTEGER NOT NULL, "
    "PRIMARY KEY(version, payment_id))",
    "CREATE TABLE active_dataset (singleton INTEGER PRIMARY KEY CHECK(singleton = 1), "
    "version TEXT NOT NULL REFERENCES datasets(version))",
    *(f"CREATE TRIGGER immutable_{table}_{action.lower()} BEFORE {action} ON {table} "
      "BEGIN SELECT RAISE(ABORT, 'Dataset versions are immutable'); END"
      for table in ("datasets", "payments") for action in ("UPDATE", "DELETE")),
)


def _initialize(connection):
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        existing = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if existing:
            raise sqlite3.DatabaseError("Unrecognized payment database schema.")
        for statement in SCHEMA:
            connection.execute(statement)
        connection.execute("PRAGMA user_version = 1")
    elif version != 1:
        raise sqlite3.DatabaseError("Unsupported payment database schema.")


def activate_payment_csv(content: bytes, database: Path = PAYMENTS_DB) -> dict:
    """Validate first, retain exact source bytes, then atomically activate a new version.

    Reimports create independent historical versions, even for identical bytes.
    A transaction failure leaves the previous active version and rows intact.
    """
    preview = validate_payment_csv(content)
    version = uuid4().hex
    imported = datetime.now(timezone.utc).isoformat()
    with closing(sqlite3.connect(database, timeout=10)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            _initialize(connection)
            connection.execute("INSERT INTO datasets VALUES (?, ?, ?, ?, ?)",
                               (version, preview.source_sha256, imported, len(preview.payments), content))
            connection.executemany("INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?)",
                ((version, p.payment_id, p.supplier_name, p.payment_date.isoformat(),
                  p.amount_millibhd, p.source_line) for p in preview.payments))
            connection.execute("INSERT INTO active_dataset VALUES (1, ?) "
                               "ON CONFLICT(singleton) DO UPDATE SET version=excluded.version", (version,))
    return {"version": version, "source_sha256": preview.source_sha256,
            "imported_at_utc": imported, "row_count": len(preview.payments)}


def active_dataset(database: Path = PAYMENTS_DB) -> dict | None:
    """Read active metadata without creating a database or altering it."""
    database = Path(database)
    if not database.exists():
        return None
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise sqlite3.DatabaseError("Unsupported payment database schema.")
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT d.version, d.source_sha256, d.imported_at_utc, d.row_count "
                                 "FROM datasets d JOIN active_dataset a ON d.version=a.version "
                                 "WHERE a.singleton=1").fetchone()
        return dict(row) if row else None


def payment_rows_for_month(first_day: str, last_day: str, database: Path = PAYMENTS_DB):
    """Read metadata and qualifying rows from one consistent read-only snapshot.

    Internal storage operation: the caller must authorize before calling it.
    Dates are validated by the approved API operation; SQL is never supplied by users.
    """
    database = Path(database)
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN")
        if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise sqlite3.DatabaseError("Unsupported payment database schema.")
        metadata = connection.execute(
            "SELECT d.version, d.source_sha256, d.imported_at_utc FROM datasets d "
            "JOIN active_dataset a ON d.version=a.version WHERE a.singleton=1"
        ).fetchone()
        if metadata is None:
            raise sqlite3.DatabaseError("No active payment dataset.")
        rows = connection.execute(
            "SELECT payment_id, supplier_name, payment_date, amount_millibhd, source_line "
            "FROM payments WHERE version=? AND payment_date>=? AND payment_date<=? "
            "AND amount_millibhd>? ORDER BY payment_date, payment_id",
            (metadata["version"], first_day, last_day, 5000000),
        ).fetchall()
        return dict(metadata), [dict(row) for row in rows]
