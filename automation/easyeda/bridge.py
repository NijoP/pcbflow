#!/usr/bin/env python3
"""
EasyEDA Bridge transport — the official, handshake-verified channel into EasyEDA Pro.

This is the primary replacement for driving the editor through a raw Chrome-DevTools
websocket (see ../browser/cdp.py, kept as the screenshot/fallback backend). It speaks
the HTTP contract of EasyEDA's official Bridge Server (github.com/easyeda/easyeda-api-skill,
scripts/bridge-server.mjs) paired with the `run-api-gateway` editor extension:

    GET  /health          -> {service:"easyeda-bridge", edaConnected, activeWindowId, ...}
    GET  /eda-windows     -> {windows:[{windowId,connected,active}], activeWindowId, count}
    POST /eda-windows/select {windowId} -> {success, activeWindowId}
    POST /execute {code[, windowId]}    -> {success:true, result} | {success:false, error}

The Bridge auto-picks a port in 49620-49629, so we DISCOVER it by scanning that range
and verifying the `service` handshake field. Every call returns the same envelope as
cdp.eval — {ok:True, v:<result>} or {ok:False, err:<message>} — so the reliability
layer (recover/heal) wraps either backend unchanged. Pure Python 3 standard library.

Usage:
    python3 bridge.py health              # discover the bridge, print /health
    python3 bridge.py windows             # list connected EDA windows
    python3 bridge.py port                # print the discovered port (empty if none)
    python3 bridge.py exec script.js      # run a JS file in the active EDA window
    python3 bridge.py exec -  < script.js # run JS from stdin

NOTE: unit-tested against a stdlib mock of the contract; needs a live EasyEDA session
with the run-api-gateway extension to validate end-to-end. Verify before claiming it works.
"""
import json
import os
import sys
import urllib.request
import urllib.error

SERVICE_ID = "easyeda-bridge"
PORT_START = int(os.environ.get("EDA_BRIDGE_PORT_START", "49620"))
PORT_END = int(os.environ.get("EDA_BRIDGE_PORT_END", "49629"))
HOST = os.environ.get("EDA_BRIDGE_HOST", "127.0.0.1")
DEFAULT_TIMEOUT = float(os.environ.get("EDA_BRIDGE_TIMEOUT", "35"))


def _base(port):
    return f"http://{HOST}:{port}"


def _get(port, path, timeout=1.0):
    """GET a bridge endpoint -> parsed JSON dict (raises on any transport/JSON error)."""
    with urllib.request.urlopen(_base(port) + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(port, path, payload, timeout=DEFAULT_TIMEOUT):
    """POST JSON to a bridge endpoint -> (http_status, parsed_json). Never raises on
    an HTTP error status — the bridge returns a JSON error body we want to read."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _base(port) + path, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, {"error": body or e.reason}


def is_bridge(port, timeout=0.8):
    """True iff a running service on `port` identifies as the EasyEDA bridge."""
    try:
        return _get(port, "/health", timeout).get("service") == SERVICE_ID
    except Exception:
        return False


def discover_port(prefer_connected=True):
    """Scan the port range for a live bridge. Returns a port, or None if none found.

    With prefer_connected, a bridge that already has an EDA window attached
    (edaConnected) wins over one that's up but has no editor connected yet."""
    found = None
    for port in range(PORT_START, PORT_END + 1):
        try:
            h = _get(port, "/health", 0.8)
        except Exception:
            continue
        if h.get("service") != SERVICE_ID:
            continue
        if prefer_connected and h.get("edaConnected"):
            return port
        if found is None:
            found = port
    return found


def health(port=None):
    """Return the bridge /health dict (discovers the port if not given). Raises if no bridge."""
    port = port or discover_port()
    if port is None:
        raise RuntimeError(f"no EasyEDA bridge found on {HOST}:{PORT_START}-{PORT_END}")
    return _get(port, "/health", 1.0)


def eda_windows(port=None):
    """List EDA windows connected to the bridge."""
    port = port or discover_port()
    if port is None:
        raise RuntimeError(f"no EasyEDA bridge found on {HOST}:{PORT_START}-{PORT_END}")
    return _get(port, "/eda-windows", 1.0)


def execute(code, port=None, window_id=None, timeout=DEFAULT_TIMEOUT):
    """Run JS in the EDA editor via the bridge. Returns {ok, v}|{ok, err} (+http on error).

    `code` runs in the extension runtime; use `return await eda.<...>` to return a value.
    Mirrors cdp.eval's envelope exactly so callers/backends are interchangeable."""
    if port is None:
        port = discover_port()
    if port is None:
        return {"ok": False, "err": f"no EasyEDA bridge on {HOST}:{PORT_START}-{PORT_END} "
                                    "(is run-api-gateway running + 'allow external interaction' ticked?)"}
    payload = {"code": code}
    if window_id:
        payload["windowId"] = window_id
    try:
        status, body = _post(port, "/execute", payload, timeout)
    except urllib.error.URLError as e:
        return {"ok": False, "err": f"bridge unreachable on port {port}: {e.reason}"}
    except Exception as e:  # noqa: BLE001 — surface transport failures as data, never swallow
        return {"ok": False, "err": f"bridge call failed on port {port}: {e}"}
    if status == 200 and body.get("success"):
        return {"ok": True, "v": body.get("result")}
    return {"ok": False, "err": body.get("error") or f"execute failed (HTTP {status})", "http": status}


# ─── CLI ────────────────────────────────────────────────────────────
def _read_js(arg):
    return sys.stdin.read() if arg == "-" else open(arg, "r", encoding="utf-8").read()


def main(argv):
    if not argv:
        print(__doc__.strip().split("\n\n")[0]); return 0
    cmd = argv[0]
    if cmd == "port":
        p = discover_port()
        print(p if p is not None else "")
        return 0 if p is not None else 1
    if cmd == "health":
        print(json.dumps(health(), indent=2)); return 0
    if cmd == "windows":
        print(json.dumps(eda_windows(), indent=2)); return 0
    if cmd == "exec":
        if len(argv) < 2:
            print("usage: bridge.py exec <file.js|->", file=sys.stderr); return 2
        res = execute(_read_js(argv[1]))
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 1
    print(f"unknown command: {cmd}", file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
