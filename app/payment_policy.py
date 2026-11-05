"""Read the approved finance-policy excerpt from its authoritative corpus file.

This narrow adapter fails closed if the known policy paragraph changes. It does
not interpret arbitrary document instructions or alter general RAG permissions.
Call only after administrator authorization.
"""
import json
import re
from hashlib import sha256

from app.paths import ROOT

APPROVED_LINES = (
    "The finance team reviews supplier payments every Friday.",
    "Payments above 5000 BHD require approval from two administrators.",
)


class PaymentPolicyUnavailable(ValueError):
    pass


def load_payment_policy(root=ROOT):
    try:
        with (root / "data/manifest.json").open("rb") as source:
            manifest_bytes = source.read(100001)
        if len(manifest_bytes) > 100000:
            raise ValueError("Oversized manifest")
        manifest = json.loads(manifest_bytes.decode("utf-8-sig"))
        entries = [entry for entry in manifest["documents"] if entry["document_id"] == "admin-finance"]
        if len(entries) != 1:
            raise ValueError("Ambiguous policy")
        entry = entries[0]
        if entry["access_level"] != "admin" or entry["trust_level"] != "curated":
            raise ValueError("Policy classification changed")
        version = manifest["dataset_version"]
        if not isinstance(version, str) or not version.strip():
            raise ValueError("Missing corpus version")
        corpus = (root / "data/corpus").resolve()
        path = (corpus / entry["file"]).resolve()
        if path.parent != corpus or path.suffix.lower() != ".md":
            raise ValueError("Invalid policy path")
        with path.open("rb") as source:
            raw = source.read(20001)
        if len(raw) > 20000:
            raise ValueError("Oversized policy")
        text = raw.decode("utf-8-sig")
        lines = text.splitlines()
        # Require a complete approved paragraph, not a substring in new claims.
        expected = "\n".join(APPROVED_LINES)
        paragraphs = re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n"))
        if sum(paragraph.strip() == expected for paragraph in paragraphs) != 1:
            raise ValueError("Policy excerpt changed")
        matches = [index for index in range(len(lines) - 1)
                   if tuple(lines[index:index + 2]) == APPROVED_LINES]
        if len(matches) != 1:
            raise ValueError("Ambiguous policy lines")
        first = matches[0] + 1
        return {"document_id": "admin-finance", "source": path.name,
                "access_level": "admin", "trust_level": "curated",
                "dataset_version": version, "source_sha256": sha256(raw).hexdigest(),
                "manifest_sha256": sha256(manifest_bytes).hexdigest(),
                "excerpt": "\n".join(lines[first - 1:first + 1]),
                "start_line": first, "end_line": first + 1}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise PaymentPolicyUnavailable("Payment policy is unavailable.") from None
