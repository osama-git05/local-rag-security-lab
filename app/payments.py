"""Bounded, all-or-nothing validation of supplier-payment CSV bytes.

No persistence or HTTP exposure: callers must authorize before supplying data.
"""
import csv
import io
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256

MAX_BYTES = 1024 * 1024
MAX_ROWS = 1000
COLUMNS = ("payment_id", "supplier_name", "payment_date", "amount_bhd")


class PaymentValidationError(ValueError):
    """Safe validation failure, without echoing supplied data."""


@dataclass(frozen=True)
class Payment:
    payment_id: str
    supplier_name: str
    payment_date: date
    amount_millibhd: int
    source_line: int

    @property
    def amount_bhd(self):
        return format(Decimal(self.amount_millibhd) / 1000, ".3f")


@dataclass(frozen=True)
class PaymentPreview:
    source_sha256: str
    byte_count: int
    payments: tuple[Payment, ...]


def validate_payment_csv(content: bytes) -> PaymentPreview:
    """Return every validated row or raise; never return partial results.

    Columns may be reordered. Values are not silently trimmed or coerced.
    source_line is the physical starting line, including the header.
    """
    if len(content) > MAX_BYTES:
        raise PaymentValidationError("CSV exceeds the 1 MiB limit.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise PaymentValidationError("CSV must be UTF-8.") from None
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    payments = []
    seen = set()
    try:
        header = next(reader, None)
        if header is None or len(header) != len(COLUMNS) or set(header) != set(COLUMNS):
            raise PaymentValidationError("CSV must contain exactly the required columns.")
        while True:
            line = reader.line_num + 1
            row = next(reader, None)
            if row is None:
                break
            if len(payments) >= MAX_ROWS:
                raise PaymentValidationError("CSV exceeds the 1000-row limit.")
            if len(row) != len(COLUMNS):
                raise PaymentValidationError(f"Invalid column count at line {line}.")
            values = dict(zip(header, row))
            identifier = values["payment_id"]
            supplier = values["supplier_name"]
            day = values["payment_date"]
            amount = values["amount_bhd"]
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", identifier):
                raise PaymentValidationError(f"Invalid payment ID at line {line}.")
            if identifier in seen:
                raise PaymentValidationError(f"Duplicate payment ID at line {line}.")
            if not 1 <= len(supplier) <= 120 or not supplier.strip() or any(ord(c) < 32 or ord(c) == 127 for c in supplier):
                raise PaymentValidationError(f"Invalid supplier name at line {line}.")
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", day):
                raise PaymentValidationError(f"Invalid payment date at line {line}.")
            try:
                parsed_day = date.fromisoformat(day)
            except ValueError:
                raise PaymentValidationError(f"Invalid payment date at line {line}.") from None
            # 15 integer digits bound arithmetic and downstream storage safely.
            if not re.fullmatch(r"[0-9]{1,15}(?:\.[0-9]{1,3})?", amount):
                raise PaymentValidationError(f"Invalid BHD amount at line {line}.")
            millibhd = int(Decimal(amount) * 1000)
            if millibhd <= 0:
                raise PaymentValidationError(f"BHD amount must be positive at line {line}.")
            seen.add(identifier)
            payments.append(Payment(identifier, supplier, parsed_day, millibhd, line))
    except csv.Error:
        raise PaymentValidationError("Malformed CSV.") from None
    if not payments:
        raise PaymentValidationError("CSV must contain payment records.")
    return PaymentPreview(sha256(content).hexdigest(), len(content), tuple(payments))
