"""Validate a local synthetic payment CSV and print a JSON preview; never import it."""
import argparse
import json
from pathlib import Path

from app.payments import MAX_BYTES, PaymentValidationError, validate_payment_csv


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args(argv)
    try:
        with args.csv_file.open("rb") as source:
            preview = validate_payment_csv(source.read(MAX_BYTES + 1))
    except (OSError, PaymentValidationError) as error:
        message = str(error) if isinstance(error, PaymentValidationError) else "Could not read the CSV file."
        print(json.dumps({"status": "invalid", "error": message}))
        return 1
    print(json.dumps({
        "status": "valid", "persisted": False,
        "source_sha256": preview.source_sha256,
        "byte_count": preview.byte_count, "row_count": len(preview.payments),
        "rows": [{"payment_id": p.payment_id, "supplier_name": p.supplier_name,
                  "payment_date": p.payment_date.isoformat(), "amount_bhd": p.amount_bhd,
                  "source_line": p.source_line} for p in preview.payments],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
