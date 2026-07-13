#!/usr/bin/env python3
"""
EdaSession — one interface over the two EasyEDA transports, so callers never care which.

    from session import EdaSession
    eda = EdaSession()          # auto-detects: official Bridge if up, else raw CDP
    r = eda.run("return await eda.dmt_Project.getCurrentProjectInfo();")
    if r["ok"]: use(r["v"])

Backend selection (override with EDA_BACKEND=bridge|cdp):
  1. `bridge`  — official Bridge Server /execute (../easyeda/bridge.py). Primary: robust,
                 handshake-verified, no Chrome-profile cloning. Preferred when reachable.
  2. `cdp`     — raw Chrome DevTools eval (../browser/cdp.py). Fallback + screenshots.

Both backends return the identical {ok, v}|{ok, err} envelope, so the reliability layer
(recover/heal) and every caller stay backend-agnostic. Pure Python 3 standard library;
the CDP fallback shells out to cdp.py (which owns the async websocket) as a subprocess.

NOTE: transport is unit-tested with a mock; end-to-end needs a live EasyEDA session.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge  # noqa: E402

_CDP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "browser", "cdp.py")


class EdaSession:
    def __init__(self, backend=None):
        """backend: 'bridge' | 'cdp' | None(auto). Env EDA_BACKEND overrides None."""
        self.backend = backend or os.environ.get("EDA_BACKEND") or self._detect()

    @staticmethod
    def _detect():
        """Pick the best available backend without a live editor requirement."""
        try:
            if bridge.discover_port() is not None:
                return "bridge"
        except Exception as e:
            # never swallow silently: say WHY we fell back so a broken Bridge is diagnosable
            sys.stderr.write(f"[pcbflow] Bridge discovery failed ({e!r}); falling back to CDP.\n")
        return "cdp"

    def run(self, js, timeout=bridge.DEFAULT_TIMEOUT):
        """Execute JS in the EDA editor; return {ok, v}|{ok, err}. Backend-agnostic."""
        if self.backend == "bridge":
            return bridge.execute(js, timeout=timeout)
        return self._run_cdp(js, timeout)

    def _run_cdp(self, js, timeout):
        """Fallback: hand the JS to cdp.py's `eval -` CLI (it owns the async socket)."""
        try:
            p = subprocess.run(
                [sys.executable, _CDP, "eval", "-"],
                input=js, capture_output=True, text=True, timeout=timeout + 5,
            )
        except FileNotFoundError:
            return {"ok": False, "err": f"cdp backend not found at {_CDP}"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "err": f"cdp eval timed out after {timeout}s"}
        out = (p.stdout or "").strip()
        if not out:
            return {"ok": False, "err": (p.stderr or "cdp produced no output").strip()}
        try:
            return json.loads(out)
        except ValueError:
            return {"ok": False, "err": f"cdp returned non-JSON: {out[:200]}"}


def main(argv):
    eda = EdaSession()
    if argv and argv[0] == "backend":
        print(eda.backend); return 0
    js = sys.stdin.read() if (not argv or argv[0] == "-") else open(argv[0], encoding="utf-8").read()
    r = eda.run(js)
    print(json.dumps(r, indent=2))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
