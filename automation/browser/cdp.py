#!/usr/bin/env python3
"""
CDP driver for the EasyEDA Pro editor tab — the proven, board-agnostic browser
driver behind PCB Flow's headless readback + verification.

It talks to a Chrome started with --remote-debugging-port (see launch_easyeda.py),
picks the tab whose URL contains 'easyeda.com/editor', and evaluates JavaScript in
it — returning the result as JSON. Every eval is wrapped in a try/catch that returns
{ok:true, v:<result>} or {ok:false, err:<message>}, so a page-side error comes back
as data (never a silent drop). Pure Python 3 standard library + `websockets`.

Usage:
    python3 cdp.py version                 # print the browser version
    python3 cdp.py tabs                     # list page targets (id | url | title)
    python3 cdp.py eval script.js           # run a JS file in the editor tab -> JSON
    python3 cdp.py eval -  < script.js       # run JS from stdin
    python3 cdp.py shot out.png             # screenshot the editor tab

Screenshots are for SANITY, not truth — verify geometry from real coordinates
(reconstruct + audit), never by eye. See reliability/... and docs/07_BROWSER_AUTOMATION.md.
"""
import asyncio, base64, json, os, sys, urllib.request
import websockets

PORT = int(os.environ.get("CDP_PORT", "9222"))
EDITOR_MATCH = os.environ.get("CDP_EDITOR_MATCH", "easyeda.com/editor")


def _http(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=5) as r:
        return json.loads(r.read().decode())


def pick_ws():
    """Return (webSocketDebuggerUrl, tab) for the EasyEDA editor tab (or the first page)."""
    pages = [t for t in _http("/json") if t.get("type") == "page"]
    editor = [t for t in pages if EDITOR_MATCH in t.get("url", "")]
    target = editor or pages
    if not target:
        raise SystemExit("no page target found — is Chrome running with --remote-debugging-port "
                         "and EasyEDA open? (see launch_easyeda.py)")
    return target[0]["webSocketDebuggerUrl"], target[0]


async def _eval(js, timeout=120):
    ws_url, _ = pick_ws()
    # open_timeout bounds the connect itself (an unresponsive tab won't hang forever)
    async with websockets.connect(ws_url, max_size=None, ping_interval=None,
                                  open_timeout=timeout) as ws:
        # double-async IIFE: catch everything, always return a JSON STRING
        wrapped = ("(async()=>{try{const __r=await (async()=>{%s})();"
                   "return JSON.stringify({ok:true,v:__r});}"
                   "catch(e){return JSON.stringify({ok:false,err:String(e&&e.stack||e)});}})()" % js)
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"})); await ws.recv()
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {
            "expression": wrapped, "awaitPromise": True, "returnByValue": True,
            "timeout": timeout * 1000}}))
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout + 5))
            if msg.get("id") == 2:
                res = msg.get("result", {})
                if "exceptionDetails" in res:
                    return {"ok": False, "err": json.dumps(res["exceptionDetails"])[:800]}
                val = res.get("result", {}).get("value")
                try:
                    return json.loads(val)
                except Exception:
                    return {"ok": True, "v": val}


async def _shot(outfile, timeout=60):
    ws_url, _ = pick_ws()
    async with websockets.connect(ws_url, max_size=None, ping_interval=None,
                                  open_timeout=timeout) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"})); await ws.recv()
        await ws.send(json.dumps({"id": 2, "method": "Page.captureScreenshot",
                                  "params": {"format": "png", "captureBeyondViewport": False}}))
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            if msg.get("id") == 2:
                data = msg.get("result", {}).get("data")
                if not data:
                    return {"ok": False, "err": str(msg)[:300]}
                raw = base64.b64decode(data)
                with open(outfile, "wb") as f:
                    f.write(raw)
                return {"ok": True, "file": outfile, "bytes": len(raw)}


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "version":
        print(json.dumps(_http("/json/version"), indent=2))
    elif cmd == "tabs":
        for t in _http("/json"):
            if t.get("type") == "page":
                print(t.get("id"), "|", t.get("url", "")[:90], "|", t.get("title", "")[:40])
    elif cmd == "eval":
        src = sys.stdin.read() if sys.argv[2] == "-" else open(sys.argv[2]).read()
        print(json.dumps(asyncio.run(_eval(src)), indent=2))
    elif cmd == "shot":
        print(json.dumps(asyncio.run(_shot(sys.argv[2]))))
    else:
        raise SystemExit(f"unknown cmd: {cmd}")


if __name__ == "__main__":
    main()
