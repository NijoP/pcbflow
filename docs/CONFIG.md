# Configuration reference

Every environment variable pcbflow reads, in one place. **You need none of these to start** —
they only tune the EasyEDA transport and tool timeouts. Defaults are chosen so the common case
(one EasyEDA window open, KiCad installed) works out of the box.

## Environment variables

| Variable | Used by | Default | Purpose |
|---|---|---|---|
| `EDA_BACKEND` | `automation/easyeda/session.py` | *(auto)* | Force the EasyEDA transport: `bridge` or `cdp`. Unset = auto-detect (Bridge if reachable, else CDP). |
| `EDA_BRIDGE_HOST` | `automation/easyeda/bridge.py` | `127.0.0.1` | Host of the official EasyEDA Bridge server. |
| `EDA_BRIDGE_PORT_START` | `automation/easyeda/bridge.py` | `49620` | First port scanned to discover the Bridge. |
| `EDA_BRIDGE_PORT_END` | `automation/easyeda/bridge.py` | `49629` | Last port scanned for the Bridge. |
| `EDA_BRIDGE_TIMEOUT` | `automation/easyeda/bridge.py` | `35` | Per-request Bridge `/execute` timeout (seconds). |
| `CDP_PORT` | `automation/browser/cdp.py` | `9222` | Chrome DevTools remote-debugging port (CDP fallback). |
| `CDP_EDITOR_MATCH` | `automation/browser/cdp.py` | `easyeda.com/editor` | Substring that identifies the EasyEDA editor tab. |

## Tool timeouts (not env-configurable; documented for transparency)

| Where | Value | Note |
|---|---|---|
| `tools/drc.py` `run_drc(timeout=…)` | 300 s | `kicad-cli` DRC ceiling; on timeout it returns a documented manual-fallback command. |
| `automation/browser/cdp.py` eval / screenshot | 120 s / 60 s | bounded by `open_timeout` + `asyncio.wait_for`. |
| Bridge port probe (`is_bridge`) | 1 s | fast discovery scan. |

## Honest limitations

- The **Bridge and CDP transports are unit-tested against mocks**; the live EasyEDA paths still
  need validation on a real session — tracked in [`../VALIDATION.md`](../VALIDATION.md).
- **`kicad-cli` is required** for the DRC and gerber steps (`pcbflow drc`, `make example`). The
  offline netlist / ERC / import-diff checks run without it.
- Cross-platform tooling is developed and unit-tested on Linux; macOS/Windows are built and
  unit-tested but need real-host validation (see VALIDATION.md).
- The two MCP servers (`pcbflow-mcp`, `pcbmunch`) require the optional `mcp` extra
  (`pip install .[mcp]`).
