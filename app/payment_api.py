"""Approved administrator-only payment operation; no model or arbitrary SQL."""
import calendar
import sqlite3
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, field_validator

from app.auth import Principal, get_principal
from app.payment_store import payment_rows_for_month
from app.payment_policy import load_payment_policy, PaymentPolicyUnavailable

router = APIRouter()
NO_STORE = {"Cache-Control": "no-store"}


def require_payment_admin(principal: Principal = Depends(get_principal)):
    if principal.role != "admin":
        raise HTTPException(403, "Access denied.", headers=NO_STORE)
    return principal


class PaymentQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: Literal["supplier_payments_above_threshold"]
    month: str

    @field_validator("month")
    @classmethod
    def valid_month(cls, value):
        import re
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", value):
            raise ValueError("Month must use YYYY-MM.")
        try:
            date.fromisoformat(value + "-01")
        except ValueError:
            raise ValueError("Month must be a valid calendar month.") from None
        return value


class PaymentRow(BaseModel):
    payment_id: str
    supplier_name: str
    payment_date: str
    amount_bhd: str
    source_line: int


class DatasetReference(BaseModel):
    version: str
    source_sha256: str
    imported_at_utc: str


class PaymentPolicyReference(BaseModel):
    document_id: Literal["admin-finance"]
    source: str
    access_level: Literal["admin"]
    trust_level: Literal["curated"]
    dataset_version: str
    source_sha256: str
    manifest_sha256: str
    excerpt: str
    start_line: int
    end_line: int


class PaymentResult(BaseModel):
    operation: Literal["supplier_payments_above_threshold"]
    month: str
    currency: Literal["BHD"]
    threshold_bhd: str
    row_count: int
    total_bhd: str
    rows: list[PaymentRow]
    dataset: DatasetReference
    policy: PaymentPolicyReference


def format_bhd(millibhd: int) -> str:
    whole, fraction = divmod(millibhd, 1000)
    return f"{whole}.{fraction:03d}"


@router.post("/payments/query", response_model=PaymentResult)
def query_payments(request: PaymentQuery, response: Response,
                   principal: Principal = Depends(require_payment_admin)):
    year, month = map(int, request.month.split("-"))
    first = request.month + "-01"
    last = request.month + f"-{calendar.monthrange(year, month)[1]:02d}"
    try:
        policy = load_payment_policy()
        metadata, records = payment_rows_for_month(first, last)
    except PaymentPolicyUnavailable:
        raise HTTPException(503, "Payment policy is unavailable.", headers=NO_STORE) from None
    except (OSError, sqlite3.Error):
        raise HTTPException(503, "Payment data is unavailable.", headers=NO_STORE) from None
    response.headers.update(NO_STORE)
    return PaymentResult(
        operation=request.operation, month=request.month, currency="BHD",
        threshold_bhd="5000.000", row_count=len(records),
        total_bhd=format_bhd(sum(row["amount_millibhd"] for row in records)),
        rows=[PaymentRow(payment_id=row["payment_id"], supplier_name=row["supplier_name"],
                         payment_date=row["payment_date"], amount_bhd=format_bhd(row["amount_millibhd"]),
                         source_line=row["source_line"]) for row in records],
        dataset=DatasetReference(**metadata),
        policy=PaymentPolicyReference(**policy),
    )
