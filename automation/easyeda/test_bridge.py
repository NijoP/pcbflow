#!/usr/bin/env python3
"""Hermetic test for bridge.py + session.py against a stdlib mock of the official
EasyEDA Bridge HTTP contract (no live editor, no network). Run:

    python3 automation/easyeda/test_bridge.py     # PASS on success

Proves: port discovery + handshake, /health, the {ok,v}/{ok,err} envelope on
success / 500 / 503 / no-bridge, and that EdaSession selects and routes correctly."""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge          # noqa: E402
import session         # noqa: E402


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def _json(self, status, obj):
        b = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"service": "easyeda-bridge", "status": "ok",
                             "edaConnected": True, "edaWindowCount": 1,
                             "activeWindowId": "win1", "pendingRequests": 0, "timestamp": 0})
        elif self.path == "/eda-windows":
            self._json(200, {"windows": [{"windowId": "win1", "connected": True, "active": True}],
                             "activeWindowId": "win1", "count": 1})
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        if self.path != "/execute":
            return self._json(404, {"error": "Not found"})
        code = payload.get("code")
        if not code or not isinstance(code, str):
            return self._json(400, {"error": 'Missing "code" field (string)'})
        if "NOEDA" in code:
            return self._json(503, {"success": False, "error": "No EDA window connected."})
        if "FAIL" in code:
            return self._json(500, {"success": False, "error": "boom"})
        self._json(200, {"success": True, "result": {"echo": code}, "windowId": "win1"})


def _serve():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


def main():
    srv, port = _serve()
    # Point the discovery range at exactly the mock port.
    bridge.HOST, bridge.PORT_START, bridge.PORT_END = "127.0.0.1", port, port

    # 1) discovery + handshake
    assert bridge.is_bridge(port), "handshake failed"
    assert bridge.discover_port() == port, "discovery missed the mock"

    # 2) /health
    h = bridge.health()
    assert h["service"] == "easyeda-bridge" and h["edaConnected"] is True

    # 3) /eda-windows
    assert bridge.eda_windows()["count"] == 1

    # 4) execute success -> {ok, v}
    r = bridge.execute("return 1+1;")
    assert r == {"ok": True, "v": {"echo": "return 1+1;"}}, r

    # 5) execute 500 -> {ok:False, err, http}
    r = bridge.execute("FAIL now")
    assert r["ok"] is False and r["err"] == "boom" and r["http"] == 500, r

    # 6) execute 503 (no EDA) -> surfaced, never swallowed
    r = bridge.execute("NOEDA")
    assert r["ok"] is False and "No EDA" in r["err"] and r["http"] == 503, r

    # 7) envelope parity with cdp: only these keys
    ok_keys = set(bridge.execute("return 2;").keys())
    assert ok_keys == {"ok", "v"}, ok_keys
    err_keys = set(bridge.execute("FAIL").keys())
    assert err_keys == {"ok", "err", "http"}, err_keys

    # 8) EdaSession selects + routes to bridge when the mock is up
    s = session.EdaSession()
    assert s.backend == "bridge", s.backend
    assert session.EdaSession(backend="bridge").run("return 3;") == {"ok": True, "v": {"echo": "return 3;"}}

    # 9) no bridge -> honest failure, not a crash
    bridge.PORT_START = bridge.PORT_END = port + 1  # nothing listening here
    assert bridge.discover_port() is None
    r = bridge.execute("return 1;")
    assert r["ok"] is False and "no EasyEDA bridge" in r["err"], r

    srv.shutdown()
    print("PASS — bridge+session: discovery, handshake, /health, envelope (ok/500/503/no-bridge), routing.")


if __name__ == "__main__":
    main()
