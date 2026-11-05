"""Activate a validated local synthetic CSV in the separate payment database."""
import argparse
import json
import sqlite3
from pathlib import Path

from app.payment_store import activate_payment_csv
from app.payments import MAX_BYTES, PaymentValidationError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args(argv)
    try:
        with args.csv_file.open("rb") as source:
            metadata = activate_payment_csv(source.read(MAX_BYTES + 1))
    except (OSError, PaymentValidationError, sqlite3.Error) as error:
        message = str(error) if isinstance(error, PaymentValidationError) else "Could not activate the payment dataset. Previous active data was retained."
        print(json.dumps({"status": "error", "error": message}))
        return 1
    print(json.dumps({"status": "active", **metadata}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
