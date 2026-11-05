"""Observed whole-message refusals normalize without accepting uncited additions."""
from hashlib import sha256
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.auth import Principal
from app.main import app
from app.output_validation import CitationValidationError, NO_ANSWER, validate_citations
from app.rag import OLLAMA_URL

REFUSALS = (
    "There are no finance administration notes in the provided documents. "
    "The available documents do not contain the answer.",
    "The available documents do not contain the synthetic secret marker "
    "from the finance administration notes.",
)
ALLOWED = {"policy-security", "policy-leave"}


class RefusalNormalizationTests(unittest.TestCase):
    def test_observed_messages_return_the_canonical_refusal(self):
        for answer in REFUSALS:
            with self.subTest(answer=answer):
                self.assertEqual(validate_citations(answer, ALLOWED), NO_ANSWER)

    def test_full_message_whitespace_and_case_normalization(self):
        for answer in REFUSALS:
            self.assertEqual(validate_citations("\n  " + answer.upper().replace(" ", " \n ") + "\t", ALLOWED), NO_ANSWER)

    def test_added_uncited_claims_at_any_position_are_rejected(self):
        for refusal in REFUSALS:
            first, _, rest = refusal.partition(".")
            for answer in (
                "Employees receive 99 days. " + refusal,
                refusal + " Employees receive 99 days.",
                first + ". Employees receive 99 days." + rest,
            ):
                with self.subTest(answer=answer):
                    with self.assertRaises(CitationValidationError):
                        validate_citations(answer, ALLOWED)

    def test_refusal_with_extra_uncited_marker_is_rejected(self):
        for refusal in REFUSALS:
            with self.assertRaises(CitationValidationError):
                validate_citations(refusal + " LAB_SECRET_FINANCE_7F2C9A", ALLOWED)

    def test_unknown_refusal_is_not_accepted_by_prefix_or_similarity(self):
        for answer in ("I cannot provide that information.", REFUSALS[1][:-1], REFUSALS[0] + " Additional text."):
            with self.assertRaises(CitationValidationError):
                validate_citations(answer, ALLOWED)

    def test_unknown_or_malformed_citations_are_not_normalized_away(self):
        for refusal in REFUSALS:
            for ending in (" [admin-finance]", " [invented-source]", " [policy-security"):
                with self.assertRaises(CitationValidationError):
                    validate_citations(refusal + ending, ALLOWED)

    def route_response(self, answer):
        token = "temporary-refusal-route-employee-token-0000000"
        accounts = ((sha256(token.encode()).digest(), Principal("test-employee", "employee")),)
        matches = [{"id": "policy-security", "text": "Synthetic employee policy.",
                    "metadata": {"source": "security-policy.md", "access_level": "employee"}}]
        simulated = httpx.Response(200, json={"response": answer, "done_reason": "stop"},
                                   request=httpx.Request("POST", OLLAMA_URL))
        with TestClient(app) as client:
            with patch("app.auth.ACCOUNTS", accounts), patch("app.rag.retrieve_authorized", return_value=matches), patch("app.rag.httpx.Client") as model:
                model.return_value.__enter__.return_value.post.return_value = simulated
                return client.post("/query", headers={"Authorization": "Bearer " + token},
                                   json={"question": "What information is available?"})

    def test_http_pipeline_returns_canonical_answer_and_permitted_sources(self):
        for refusal in REFUSALS:
            response = self.route_response(refusal)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["answer"], NO_ANSWER)
            self.assertEqual(response.json()["sources"], [{"document_id": "policy-security", "source": "security-policy.md", "access_level": "employee"}])

    def test_http_pipeline_still_rejects_refusal_plus_uncited_claim(self):
        for refusal in REFUSALS:
            response = self.route_response(refusal + " Employees receive 99 days.")
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json(), {"detail": "Could not complete the local RAG request."})


if __name__ == "__main__":
    unittest.main(verbosity=2)
