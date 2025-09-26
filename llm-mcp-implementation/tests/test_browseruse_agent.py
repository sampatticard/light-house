import json
import threading
import time
import socket
import http.server
import socketserver
import pytest
import app.browseruse_agent as bua
from app.browseruse_agent import (
    generate_browser_actions,
    run_browser_actions,
    validate_navigate_domains,
    NavigateAction,
    ExtractAction,
)


# 1. Unit tests for generate_browser_actions

class DummyQuery:
    """
    Helper to simulate query_ollama returning first invalid JSON, then valid.
    """
    def __init__(self, responses):
        # responses: list of strings to return on successive calls
        self._responses = responses.copy()
    def __call__(self, prompt: str):
        # pop first if available, else last
        if self._responses:
            return self._responses.pop(0)
        return self._responses[-1]

@pytest.fixture(autouse=True)
def patch_query(monkeypatch):
    # By default, patch query_ollama to a dummy that returns a simple valid JSON.
    def fake_query(prompt: str):
        # A simple valid JSON array with one navigate action to example.com
        return '[{"action":"navigate","url":"https://google.com"}]'
    monkeypatch.setattr(bua, "query_ollama", fake_query)
    yield

def test_generate_browser_actions_valid():
    prompt = "Dummy prompt"
    actions = generate_browser_actions(prompt)
    # Expect a single NavigateAction
    assert isinstance(actions, list) and len(actions) == 1
    act = actions[0]
    assert isinstance(act, NavigateAction)
    assert str(act.url).rstrip("/") == "https://google.com"

def test_generate_browser_actions_invalid_then_valid(monkeypatch):
    # Simulate first response invalid JSON, second valid
    responses = [
        'Not a JSON',
        '[{"action":"navigate","url":"https://google.com"}]'
    ]
    dummy = DummyQuery(responses)
    monkeypatch.setattr(bua, "query_ollama", dummy)
    prompt = "Prompt causing invalid first"
    actions = generate_browser_actions(prompt, max_attempts=2)
    # Should return valid NavigateAction with url valid.com
    assert len(actions) == 1
    assert isinstance(actions[0], NavigateAction)
    assert str(actions[0].url).rstrip("/") == "https://google.com"

def test_generate_browser_actions_fail(monkeypatch):
    # Both attempts return invalid JSON
    responses = ["bad1", "still bad"]
    dummy = DummyQuery(responses)
    monkeypatch.setattr(bua, "query_ollama", dummy)
    with pytest.raises(RuntimeError) as exc:
        generate_browser_actions("any", max_attempts=2)
    assert "Failed to generate valid browser actions" in str(exc.value)

# 2. Test validate_navigate_domains

def test_validate_navigate_domains_ok():
    actions = [NavigateAction(action="navigate", url="https://allowed.com/path")]
    # Should pass when allowed_domains includes allowed.com
    validate_navigate_domains(actions, allowed_domains=["allowed.com"])

def test_validate_navigate_domains_fail():
    actions = [NavigateAction(action="navigate", url="https://notallowed.com/")]
    with pytest.raises(ValueError):
        validate_navigate_domains(actions, allowed_domains=["allowed.com"])

# 3. Integration-like test for run_browser_actions
# Serve a minimal HTML page locally, then run Navigate+Extract actions against it.

@pytest.fixture(scope="module")
def http_server():
    """
    Start a simple HTTP server in a separate thread serving a minimal HTML page.
    Returns the port used.
    """
    # Find a free port
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()

    # Minimal HTML content
    html = b"""
    <html>
      <body>
        <div id="test">Hello World</div>
        <a id="link" href="/next">Next</a>
      </body>
    </html>
    """

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.send_header("Content-length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
            else:
                # 404 for other paths
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            # Silence logs
            return

    httpd = socketserver.TCPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    # Give it a moment
    time.sleep(0.1)
    yield port
    httpd.shutdown()
    thread.join(timeout=1)

def test_run_browser_actions_extract(http_server):
    port = http_server
    base_url = f"http://127.0.0.1:{port}"
    # Actions: navigate to server root, then extract #test
    actions = [
        NavigateAction(action="navigate", url=base_url + "/"),
        ExtractAction(action="extract", selector="#test")
    ]
    results = run_browser_actions(actions, headless=True, timeout_ms=5000)
    # Expect one result with text "Hello World"
    # result dict: {"action":"extract","selector":"#test","text":"Hello World"}
    assert isinstance(results, list) and len(results) == 1
    res = results[0]
    assert res.get("selector") == "#test"
    assert "Hello" in res.get("text", "")

def test_run_browser_actions_timeout(http_server):
    port = http_server
    base_url = f"http://127.0.0.1:{port}"
    # WaitAction on a non-existent selector should timeout and produce an error entry
    from app.browseruse_agent import WaitAction
    actions = [
        NavigateAction(action="navigate", url=base_url + "/"),
        WaitAction(action="wait", selector="#nonexistent", timeout=1000)
    ]
    results = run_browser_actions(actions, headless=True, timeout_ms=2000)
    # Expect an error entry in results
    assert any("Timeout" in r.get("error", "") for r in results)

