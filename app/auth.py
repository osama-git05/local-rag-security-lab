from app.paths import ROOT
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from secrets import compare_digest
from typing import Literal

from dotenv import dotenv_values
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: Literal["employee", "admin"]


def load_accounts():
    values = dotenv_values(ROOT / ".env")
    accounts = []
    seen = set()

    definitions = [
        ("EMPLOYEE_TOKEN", Principal("employee-01", "employee")),
        ("ADMIN_TOKEN", Principal("admin-01", "admin")),
    ]

    for variable, principal in definitions:
        token = values.get(variable)

        if not token or len(token) < 32:
            raise RuntimeError(f"Missing or invalid {variable} in .env.")

        digest = sha256(token.encode("utf-8")).digest()

        if digest in seen:
            raise RuntimeError(
                "Employee and administrator tokens must differ."
            )

        seen.add(digest)
        accounts.append((digest, principal))

    return tuple(accounts)


ACCOUNTS = load_accounts()


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Principal:
    if credentials is not None:
        supplied = sha256(
            credentials.credentials.encode("utf-8")
        ).digest()

        for expected, principal in ACCOUNTS:
            if compare_digest(supplied, expected):
                return principal

    raise HTTPException(
        status_code=401,
        detail="Missing or invalid authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )