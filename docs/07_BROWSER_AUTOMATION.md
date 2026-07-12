# 07 · Browser Automation (headless EDA via CDP)

How the AI reads reality back out of a cloud EDA tool that has no offline API. The
recipe is fiddly and every step exists because a simpler approach failed. This is
the load-bearing infrastructure behind the verification layer.

---

## Why CDP at all

The EDA tool (EasyEDA Pro) is a cloud web app. There is no clean offline
project-file download and no server API for netlist/DRC. The only way to read the
*real* board state programmatically is to drive the running editor in a browser
and call its in-page API (`window._EXTAPI_ROOT_`). Chrome DevTools Protocol (CDP)
over a websocket is that channel.

---

## The launch recipe (and why each step is mandatory)

```bash
# 1. Clone the LOGGED-IN profile (excluding caches). A fresh profile launches logged out
#    — cookies are bound to the OS keyring and unreachable from a script-launched Chrome.
rsync -a --exclude '*/Cache' --exclude '*/Code Cache' \
      ~/.config/google-chrome/ ~/.cache/eda-chrome-profile/

# 2. Remove the singleton locks, or Chrome refuses a second instance on the profile.
rm -f ~/.cache/eda-chrome-profile/Singleton*

# 3. Launch on the CLONE with remote debugging. Never on the default profile
#    (Chrome refuses remote-debugging there) and never via OAuth login in an
#    automation-controlled Chrome (Google blocks it: "browser may not be secure").
google-chrome-stable --user-data-dir="$HOME/.cache/eda-chrome-profile" \
      --remote-debugging-port=9222 "https://easyeda.com/editor"
```

**Do NOT use a generic devtools MCP** — it spawns its *own* browser (about:blank)
and will not attach to `:9222`. Drive the port with a raw websocket client.

**One session at a time.** Two open sessions on the same cloud project trigger an
edit-lock that fails every write.

**The clone is wiped on reboot** → re-`rsync` each session (cheap; script it).

---

## The driver (raw CDP websocket)

```python
async def cdp_eval(js, timeout=120):
    ws_url = pick_ws("easyeda.com/editor")          # the editor tab's debugger URL
    async with websockets.connect(ws_url, max_size=None, ping_interval=None) as ws:
        # Wrap in a double-async IIFE: catch ALL exceptions, always return a JSON STRING
        # (returnByValue survives strings reliably; objects can silently drop).
        wrapped = ("(async()=>{try{const __r=await (async()=>{%s})();"
                   "return JSON.stringify({ok:true,v:__r});}"
                   "catch(e){return JSON.stringify({ok:false,err:String(e&&e.stack||e)});}})()") % js
        await ws.send(json.dumps({"id":1,"method":"Runtime.evaluate","params":{
            "expression":wrapped,"awaitPromise":True,"returnByValue":True,"timeout":timeout*1000}}))
        return json.loads((await ws.recv()))         # {ok, v} | {ok, err}
```

Two design points that matter:
- **Always return a JSON string** from the page, never a raw object — `returnByValue`
  is reliable for strings, flaky for large objects.
- **Wrap everything in try/catch** so a page-side error comes back as data (`{ok:false}`),
  not a dropped promise.

The API root in the CDP context is `window._EXTAPI_ROOT_` (the `eda` alias exists
only inside standalone scripts). Prepend `const eda = window._EXTAPI_ROOT_;` to
reuse standalone-script code paths over CDP.

---

## Batch execution pipeline

```python
# concat a board-agnostic ENGINE with a per-section CONFIG, run through the driver
src = "const eda = window._EXTAPI_ROOT_;\n" + read(ENGINE) + "\n" + read(section)
cdp_eval(src)
```

This is how a generator authored as a standalone script is executed headlessly for
batch/CI runs — same code, different executor.

---

## Hang recovery (renderer frozen)

Some calls freeze the renderer JS thread (a wrong `*.create` signature, a blocking
modal). Once frozen, even `1+1` evals and screenshots time out; same-document
navigation is a no-op; the JS-dialog handler won't clear a DOM modal. Recover at
the **browser level**, not the page level:

```python
# via the browser-level websocket (/json/version), not the tab:
Target.createTarget(url="https://easyeda.com/editor")   # fresh renderer tab
Target.closeTarget(targetId=hung_tab_id)                # kill the frozen one
```

Placement/outline survive (auto-persisted by `done()`); only unsaved vias are lost.
**Prevention beats recovery:** never probe `*.create` in a loop; keep the
tested-signatures table ([`06_EASYEDA_INTEGRATION.md`](06_EASYEDA_INTEGRATION.md));
save often.

---

## Screenshot gotcha

`zoomToAllPrimitives()` runs headless but **does not repaint** the canvas — a
screenshot taken immediately after shows the previous view. Add a small delay, or
accept that a truly reliable visual needs a human to zoom. Never *judge geometry
from a screenshot* anyway — audit the real coordinates
([`09_VALIDATION.md`](09_VALIDATION.md)); screenshots are for sanity, not truth.

---

## What lives where

| File (origin project) | Role |
|---|---|
| `cdp.py` | the raw websocket driver — fully generic, reusable as-is |
| `recon.py` | wire-vertex → pin-net netlist reconstruction |
| `dump_sch.js` / `probe_*.js` | readback + signature probing |
| `run.py` | engine+section concat → batch execution |

`cdp.py` and `recon.py` are board-agnostic and are the two files most worth
lifting verbatim into a new project.
