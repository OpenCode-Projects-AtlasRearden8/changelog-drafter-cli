import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from changelog_drafter import polish, review
from changelog_drafter.config import load_config

import pytest


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        self.rfile.read(0)
        # assert no auth header ever leaves the tool
        assert "Authorization" not in self.headers
        assert "api-key" not in {k.lower() for k in self.headers}
        bullets = [
            ln.strip().lstrip("- ")
            for ln in body["messages"][1]["content"].splitlines()
        ]
        out = {"choices": [{"message": {"content": "\n".join(
            f"Polished: {b}" for b in bullets
        )}}]}
        data = json.dumps(out).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def test_polish_sends_no_auth_headers_with_mock_server():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/v1"
    try:
        result = polish.polish_bullets(url, "test-model", ["Added dark mode.", "Fixed crash."])
        assert result == ["Polished: Added dark mode.", "Polished: Fixed crash."]
    finally:
        server.shutdown()


def test_polish_unreachable_returns_none():
    assert polish.polish_bullets("http://127.0.0.1:1", "m", ["b"], timeout=1) is None


def test_polish_wrong_bullet_count_returns_none(monkeypatch):
    import urllib.error

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "only one line"}}]}).encode()

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: FakeResp())
    result = polish.polish_bullets("http://x", "m", ["one", "two"])
    assert result is None


def test_config_loader_reads_polish_table(tmp_path: Path):
    f = tmp_path / "changelog.toml"
    f.write_text('[polish]\nbase_url = "http://localhost:9999/v1"\nmodel = "mini"\n')
    cfg = load_config([str(f)])
    assert cfg["polish.base_url"] == "http://localhost:9999/v1"
    assert cfg["polish.model"] == "mini"


def test_run_review_with_editor(monkeypatch):
    draft = "## 1.0.0 - 2026-10-27"
    monkeypatch.setattr(review, "edit_in_editor", lambda text: text + " EDITED")

    class FakeStdin(io.StringIO):
        def isatty(self):
            return True

    answers = iter(["e", ""])
    fake = FakeStdin()
    monkeypatch.setattr(review.sys, "stdin", fake)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    result = review.run_review(draft, assume_yes=False)
    assert result == draft + " EDITED"


def test_run_review_without_tty_without_yes_errors():
    class FakeStdin(io.StringIO):
        def isatty(self):
            return False

    assert FakeStdin().isatty() is False
    with pytest.raises(SystemExit):
        review.run_review("draft", assume_yes=False)

