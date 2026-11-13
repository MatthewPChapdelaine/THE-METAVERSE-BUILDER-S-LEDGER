import json
import logging
import mimetypes
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .store import LedgerStore, NotFoundError, ValidationError


_WEB_ROOT = Path(__file__).with_name("web")
_MAX_BODY_BYTES = 1_000_000
_LOGGER = logging.getLogger("ledger_suite")


class LedgerHandler(BaseHTTPRequestHandler):
    store = None

    def _json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValidationError("invalid Content-Length header") from None
        if length < 0 or length > _MAX_BODY_BYTES:
            raise ValidationError("request body is too large")
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValidationError("request body must contain valid UTF-8 JSON") from None

    def _dispatch_api(self, method):
        path = unquote(urlsplit(self.path).path)
        parts = path.strip("/").split("/")
        try:
            if parts == ["api", "summary"] and method == "GET":
                self._json(200, self.store.summary())
                return
            if len(parts) == 2 and parts[0] == "api":
                resource = parts[1]
                if method == "GET":
                    self._json(200, self.store.list(resource))
                    return
                if method == "POST":
                    self._json(201, self.store.create(resource, self._body()))
                    return
            if len(parts) == 3 and parts[:2] == ["api", "tasks"] and method == "PATCH":
                self._json(200, self.store.update_task(parts[2], self._body()))
                return
            self._json(404, {"error": "API route not found"})
        except ValidationError as error:
            self._json(400, {"error": str(error)})
        except NotFoundError as error:
            self._json(404, {"error": str(error)})
        except (ValueError, TypeError) as error:
            self._json(400, {"error": str(error)})
        except sqlite3.IntegrityError:
            self._json(400, {"error": "A referenced project or contributor does not exist"})
        except sqlite3.Error:
            _LOGGER.exception("Unhandled API error for %s %s", method, path)
            self._json(500, {"error": "Internal server error; see server log"})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path.startswith("/api/"):
            self._dispatch_api("GET")
            return
        files = {
            "/": _WEB_ROOT / "index.html",
            "/app.js": _WEB_ROOT / "app.js",
            "/styles.css": _WEB_ROOT / "styles.css",
        }
        file_path = files.get(path)
        if file_path is None:
            self._json(404, {"error": "Not found"})
            return
        try:
            body = file_path.read_bytes()
        except OSError:
            _LOGGER.exception("Unable to read web asset %s", file_path)
            self._json(500, {"error": "Unable to load application asset"})
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self._dispatch_api("POST")

    def do_PATCH(self):
        self._dispatch_api("PATCH")

    def log_message(self, format_string, *args):
        _LOGGER.info("%s - %s", self.address_string(), format_string % args)


def serve(database, host="127.0.0.1", port=8000):
    store = LedgerStore(database)
    handler = type("BoundLedgerHandler", (LedgerHandler,), {"store": store})
    server = ThreadingHTTPServer((host, port), handler)
    _LOGGER.info("Ledger Suite listening on http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _LOGGER.info("Ledger Suite stopped")
    finally:
        server.server_close()
