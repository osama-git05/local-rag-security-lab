"""Operator boundary and workflow failure tests, without live services."""
import json
from hashlib import sha256
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.auth import Principal
from scripts.lab_console_web import app, ORIGIN
from scripts import lab_workflow as workflow
from scripts.lab_console import application_server

EMPLOYEE = "temporary-console-employee-token-000000000000"
ADMIN = "temporary-console-administrator-token-000000000"
IDENTITIES = tuple((sha256(token.encode()).digest(), Principal(name, role)) for token, name, role in
                   ((EMPLOYEE, "test-employee", "employee"), (ADMIN, "test-admin", "admin")))
ID = "20261104T010203000001Z-1234abcd"


class OperatorBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.accounts = patch("app.auth.ACCOUNTS", IDENTITIES)
        self.accounts.start()
        self.addCleanup(self.accounts.stop)
        self.client = TestClient(app, base_url=ORIGIN)

    def headers(self, token=ADMIN):
        return {"Authorization": "Bearer " + token, "Origin": ORIGIN, "X-Lab-Console": "1"}

    def test_public_shell_but_no_private_paths(self):
        for path in ("/", "/assets/console.css", "/assets/console.js"):
            self.assertEqual(self.client.get(path).status_code, 200)
        for path in ("/.env", "/results/", "/assets/../lab_workflow.py", "/docs", "/openapi.json"):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_missing_and_employee_credentials_cannot_read_operator_data(self):
        for path in ("/api/session", "/api/readiness", "/api/runs", f"/api/runs/{ID}", f"/api/runs/{ID}/download"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)
                self.assertEqual(self.client.get(path, headers=self.headers(EMPLOYEE)).status_code, 403)

    def test_employee_cannot_start_jobs(self):
        with patch("scripts.lab_console_web.start_background") as start:
            self.assertEqual(self.client.post("/api/runs", json={"suite": "isolated"}, headers=self.headers(EMPLOYEE)).status_code, 403)
            start.assert_not_called()

    def test_verified_admin_can_start_only_known_suite(self):
        with patch("scripts.lab_console_web.start_background", return_value=ID) as start:
            response = self.client.post("/api/runs", json={"suite": "isolated"}, headers=self.headers())
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.json(), {"run_id": ID})
            start.assert_called_once_with("isolated")
            for body in ({"suite": "whoami"}, {"suite": "isolated", "command": "arbitrary"}, {"suite": "isolated; anything"}):
                self.assertEqual(self.client.post("/api/runs", json=body, headers=self.headers()).status_code, 422)
            self.assertEqual(start.call_count, 1)

    def test_cross_origin_and_missing_action_headers_are_rejected(self):
        with patch("scripts.lab_console_web.start_background") as start:
            for headers in ({"Authorization": "Bearer " + ADMIN},
                            dict(self.headers(), Origin="http://untrusted.example"),
                            {"Authorization": "Bearer " + ADMIN, "Origin": ORIGIN},
                            dict(self.headers(), **{"Sec-Fetch-Site": "cross-site"})):
                self.assertEqual(self.client.post("/api/runs", json={"suite": "isolated"}, headers=headers).status_code, 403)
            start.assert_not_called()

    def test_cross_origin_read_and_host_rebinding_are_rejected(self):
        self.assertEqual(self.client.get("/api/runs", headers=dict(self.headers(), Origin="http://untrusted.example")).status_code, 403)
        self.assertEqual(self.client.get("/", headers={"Host": "untrusted.example"}).status_code, 400)

    def test_busy_returns_conflict(self):
        with patch("scripts.lab_console_web.start_background", side_effect=workflow.WorkflowBusy):
            self.assertEqual(self.client.post("/api/runs", json={"suite": "chroma"}, headers=self.headers()).status_code, 409)

    def test_summary_excludes_diagnostics_and_raw_content(self):
        report = dict(run_id=ID, suite="isolated", status="pass", raw_token="private-test-value", stages=[dict(name="Test", status="pass", diagnostic_log="private.log", command=["sensitive-path"])])
        with patch("scripts.lab_console_web.read_report", return_value=report):
            response = self.client.get(f"/api/runs/{ID}/download", headers=self.headers())
            self.assertEqual(response.status_code, 200)
            for private in ("private-test-value", "private.log", "sensitive-path"):
                self.assertNotIn(private, response.text)
            self.assertIn("attachment", response.headers["content-disposition"])
            self.assertEqual(response.headers["cache-control"], "no-store")

    def test_invalid_report_id_is_not_a_file_path(self):
        self.assertEqual(self.client.get("/api/runs/.env", headers=self.headers()).status_code, 404)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def execute(self, suite, child):
        run = workflow.Workflow(suite, self.directory)
        run.acquire()
        with patch.object(workflow, "run_module", side_effect=child):
            result = run.execute()
        return result, workflow.read_report(run.run_id, self.directory)

    def test_invalid_suite_never_runs_a_child(self):
        with self.assertRaises(ValueError):
            workflow.Workflow("arbitrary", self.directory)

    def test_lock_serializes_and_releases_after_failure(self):
        first, second = workflow.RunLock(self.directory), workflow.RunLock(self.directory)
        first.acquire()
        with self.assertRaises(workflow.WorkflowBusy):
            second.acquire()
        first.release()
        second.acquire()
        second.release()

    def test_failed_isolated_stage_stops_later_stages(self):
        calls = []
        def child(module, timeout):
            calls.append(module)
            return subprocess.CompletedProcess([], 1, "Failed", "")
        result, report = self.execute("extended", child)
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(calls, ["tests.run_isolated"])
        self.assertNotIn("case_counts", report)

    def test_timeout_is_error_and_lock_is_released(self):
        def child(module, timeout):
            raise subprocess.TimeoutExpired(module, timeout)
        result, report = self.execute("isolated", child)
        self.assertEqual(result, 2)
        self.assertEqual(report["stages"][0]["status"], "error")
        lock = workflow.RunLock(self.directory)
        lock.acquire()
        lock.release()

    def test_tokens_are_redacted_from_local_diagnostics(self):
        secret = "temporary-test-secret-to-redact"
        with patch.object(workflow, "dotenv_values", return_value={"TOKEN": secret}):
            self.execute("isolated", lambda module, timeout: subprocess.CompletedProcess([], 0, secret, ""))
        self.assertNotIn(secret, next(self.directory.glob("lab-diagnostic-*.log")).read_text())

    def test_missing_live_prerequisite_does_not_capture_or_evaluate(self):
        calls = []
        def child(module, timeout):
            calls.append(module)
            return subprocess.CompletedProcess([], 0, "OK", "")
        with patch.object(workflow, "readiness", return_value=[{"status": "error"}]):
            result, report = self.execute("extended", child)
        self.assertEqual(result, 2)
        self.assertNotIn("scripts.capture_environment", calls)
        self.assertEqual(report["status"], "error")

    def fixture_child(self, mismatch=False, incomplete=False):
        snapshot = "environment-20261104T010203000001Z.json"
        casefile = "development-regression-20261104T010203000002Z.json"
        def child(module, timeout):
            if module == "scripts.capture_environment":
                (self.directory / snapshot).write_text("{}")
                return subprocess.CompletedProcess([], 0, "Saved: results/" + snapshot + "\n", "")
            if module == "evaluation.run_extended_regression":
                detail = {"environment_snapshot": "wrong.json" if mismatch else snapshot,
                          "counts": {"pass": 10, "fail": 2, "error": 0},
                          "results": [{"case_id": "original-failing-case", "outcome": "fail", "status": 502, "elapsed_ms": 12, "checks": {"expected_http_status": False}}]}
                if incomplete:
                    detail.pop("counts")
                (self.directory / casefile).write_text(json.dumps(detail))
                return subprocess.CompletedProcess([], 1, "Stopped" if incomplete else "Saved: results/" + casefile + "\n", "")
            return subprocess.CompletedProcess([], 0, "OK", "")
        return child

    def test_live_failures_keep_case_counts_timings_and_failed_checks(self):
        with patch.object(workflow, "readiness", return_value=[]):
            result, report = self.execute("extended", self.fixture_child())
        self.assertEqual(result, 1)
        self.assertEqual(report["case_counts"], {"pass": 10, "fail": 2, "error": 0})
        self.assertEqual(report["cases"][0]["elapsed_ms"], 12)
        self.assertEqual(report["cases"][0]["failed_checks"], ["expected_http_status"])

    def test_snapshot_mismatch_is_error_not_pass(self):
        with patch.object(workflow, "readiness", return_value=[]):
            result, report = self.execute("extended", self.fixture_child(mismatch=True))
        self.assertEqual(result, 2)
        self.assertEqual(report["status"], "error")

    def test_incomplete_evaluator_report_is_linked_without_invented_counts(self):
        with patch.object(workflow, "readiness", return_value=[]):
            result, report = self.execute("extended", self.fixture_child(incomplete=True))
        self.assertEqual(result, 1)
        self.assertTrue(report["evaluation_report"].startswith("development-regression-"))
        self.assertIsNone(report["case_counts"])

    def test_orphaned_report_recovers_after_process_lock_is_gone(self):
        run = workflow.Workflow("isolated", self.directory)
        run.acquire()
        self.assertEqual(workflow.read_report(run.run_id, self.directory)["status"], "running")
        run.lock.release()
        self.assertEqual(workflow.read_report(run.run_id, self.directory)["status"], "interrupted")


class CompanionServerTests(unittest.TestCase):
    def test_existing_listener_is_reused_without_starting_another_server(self):
        with patch("scripts.lab_console.socket.create_connection") as connection, patch("uvicorn.Server") as server:
            with application_server():
                pass
            connection.return_value.close.assert_called_once()
            server.assert_not_called()

    def test_uncertain_port_access_never_starts_a_second_server(self):
        with patch("scripts.lab_console.socket.create_connection", side_effect=TimeoutError), patch("uvicorn.Server") as server:
            with self.assertRaises(TimeoutError):
                with application_server():
                    pass
            server.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
