"""Public UI assets must not expose private repository files."""
import unittest
from hashlib import sha256
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.auth import Principal
from app.main import app
from app.ui import STATIC


class AssistantInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_public_interface_and_assets(self):
        for path, content_type in (
            ("/", "text/html"),
            ("/assets/assistant.css", "text/css"),
            ("/assets/assistant.js", "text/javascript"),
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(content_type, response.headers["content-type"])

    def test_private_files_are_not_served(self):
        for path in (
            "/.env", "/data/manifest.json", "/.chroma/chroma.sqlite3",
            "/assets/auth.py", "/assets/../auth.py", "/assets/%2e%2e/auth.py",
            "/results/", "/docs/screenshots/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_interface_uses_current_asset_versions_without_browser_caching(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["cache-control"], "no-store")
        for filename in ("assistant.css", "assistant.js"):
            version = sha256((STATIC / filename).read_bytes()).hexdigest()[:16]
            url = f"/assets/{filename}?v={version}"
            self.assertIn(url, response.text)
            asset = self.client.get(url)
            self.assertEqual(asset.status_code, 200)
            self.assertEqual(asset.headers["cache-control"], "no-store")
            self.assertEqual(asset.content, (STATIC / filename).read_bytes())

    def test_query_still_requires_authentication(self):
        with patch("app.main.answer_question") as pipeline:
            response = self.client.post("/query", json={"question": "Leave policy?"})
            self.assertEqual(response.status_code, 401)
            pipeline.assert_not_called()

    def test_verified_role_still_controls_query(self):
        temporary_token = "isolated-interface-test-token-000000000000"
        employee = Principal("isolated-employee", "employee")
        accounts = ((sha256(temporary_token.encode()).digest(), employee),)
        with patch("app.auth.ACCOUNTS", accounts), patch("app.main.answer_question") as pipeline:
            response = self.client.post(
                "/query", headers={"Authorization": f"Bearer {temporary_token}"},
                json={"question": "Leave policy?", "role": "admin"},
            )
            self.assertEqual(response.status_code, 422)
            pipeline.assert_not_called()
            identity = self.client.get("/whoami", headers={"Authorization": f"Bearer {temporary_token}"})
            self.assertEqual(identity.json(), {"user_id": "isolated-employee", "role": "employee"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
