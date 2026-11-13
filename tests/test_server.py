import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ledger_suite.server import LedgerHandler
from ledger_suite.store import LedgerStore


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        store = LedgerStore(Path(self.temp_dir.name) / "ledger.sqlite3")
        handler = type("TestLedgerHandler", (LedgerHandler,), {"store": store})
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp_dir.cleanup()

    def post_json(self, path, payload):
        request = Request(
            self.base_url + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return urlopen(request)

    def test_project_creation_and_summary_api(self):
        with self.post_json("/api/projects", {"name": "Suite test"}) as response:
            project = json.load(response)
            self.assertEqual(response.status, 201)
        with urlopen(self.base_url + "/api/summary") as response:
            summary = json.load(response)

        self.assertEqual(project["name"], "Suite test")
        self.assertEqual(summary["projects"], 1)

    def test_dashboard_and_assets_are_served_without_external_dependencies(self):
        with urlopen(self.base_url + "/") as response:
            page = response.read().decode("utf-8")
            self.assertIn("BUILDER'S LEDGER", page)
            self.assertIn('class="skip-link"', page)
            self.assertIn('id="refresh-data"', page)
            self.assertIn('id="app-status"', page)
            self.assertEqual(response.headers["Content-Security-Policy"].split(";")[0], "default-src 'self'")
        with urlopen(self.base_url + "/app.js") as response:
            self.assertIn("/api/summary", response.read().decode("utf-8"))

    def test_invalid_api_input_returns_actionable_client_error(self):
        with self.assertRaises(HTTPError) as error:
            self.post_json("/api/projects", {"monthly_budget": -1})

        self.assertEqual(error.exception.code, 400)
        detail = json.load(error.exception)
        error.exception.close()
        self.assertIn("name", detail["error"])


if __name__ == "__main__":
    unittest.main()
