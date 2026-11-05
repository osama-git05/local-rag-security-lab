import unittest
from unittest.mock import patch

from app import retrieve
from app.auth import Principal


EMPLOYEE = Principal("employee-01", "employee")
ADMIN = Principal("admin-01", "admin")
QUESTION = "How much annual leave do employees receive?"


def record(access):
    return {
        "id": "test-document",
        "text": "Synthetic test document.",
        "metadata": {
            "access_level": access,
        },
    }


class AuthorizationTests(unittest.TestCase):
    def test_employee_filter(self):
        matches = [record("employee")]

        with patch.object(
            retrieve,
            "_retrieve",
            return_value=matches,
        ) as database:
            result = retrieve.retrieve_authorized(
                QUESTION,
                EMPLOYEE,
            )

            self.assertEqual(result, matches)
            database.assert_called_once_with(
                QUESTION,
                2,
                where={
                    "access_level": {
                        "$in": ["employee"],
                    }
                },
            )

    def test_admin_filter(self):
        matches = [
            record("employee"),
            record("admin"),
        ]

        with patch.object(
            retrieve,
            "_retrieve",
            return_value=matches,
        ) as database:
            result = retrieve.retrieve_authorized(
                QUESTION,
                ADMIN,
            )

            self.assertEqual(result, matches)
            database.assert_called_once_with(
                QUESTION,
                2,
                where={
                    "access_level": {
                        "$in": ["employee", "admin"],
                    }
                },
            )

    def assert_access_denied(self, principal, matches):
        with patch.object(
            retrieve,
            "_retrieve",
            return_value=matches,
        ):
            with self.assertRaises(PermissionError):
                retrieve.retrieve_authorized(
                    QUESTION,
                    principal,
                )

    def test_employee_rejects_admin_record(self):
        self.assert_access_denied(
            EMPLOYEE,
            [record("admin")],
        )

    def test_employee_rejects_missing_label(self):
        self.assert_access_denied(
            EMPLOYEE,
            [{"id": "test-document", "metadata": {}}],
        )

    def test_employee_rejects_invalid_label(self):
        self.assert_access_denied(
            EMPLOYEE,
            [record("public")],
        )

    def test_admin_rejects_missing_label(self):
        self.assert_access_denied(
            ADMIN,
            [{"id": "test-document", "metadata": {}}],
        )

    def test_rejects_none_metadata(self):
        self.assert_access_denied(
            EMPLOYEE,
            [{"id": "test-document", "metadata": None}],
        )

    def test_unknown_role_never_queries_database(self):
        # Deliberately invalid role to test rejection.
        unknown = Principal("unknown-01", "guest")

        with patch.object(retrieve, "_retrieve") as database:
            with self.assertRaises(PermissionError):
                retrieve.retrieve_authorized(
                    QUESTION,
                    unknown,
                )

            database.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)