# Install & environment guidance (for the AI agent)

This file is written **for the AI assistant** driving pcbflow, not (only) for humans — it lists
the platform quirks and setup checks the agent should know before running the automation. The
human-facing walkthrough is the [handbook](handbook/README.md).

## First move, every session

Run the environment check and read what's missing:

```bash
python3 tools/doctor.py        # ✅ / ⚠️ / ❌ per tool, with the fix for each
```

`doctor` is the source of truth for readiness. Do not start phase work with a ❌ on a tool that
phase needs (e.g. `kicad-cli` for routing/verification).

## Install

```bash
pip install -e .            # dev: editable, gives the `pcbflow` command
# or, run without installing anything:
python3 -m pcbflow <command>
# or, one-off:
pipx install pcbflow        # (once published)  ·  uvx pcbflow --version
```

Core is **Python 3.9+ standard library**; the only runtime dependency (`websockets`) is used
solely by the CDP EasyEDA driver. Tests need the `dev` extra (`pip install -e .[dev]`).

## Platform quirks the agent must handle

| Platform | Quirk | What to do |
|---|---|---|
| **Windows** | No `bash`; `.sh` scripts don't run; Chrome locks its profile. | Use the `.py` tools (`tools/drc.py`, `python3 -m pcbflow …`), not `automation/kicad/drc.sh`. Use `python`/`py`, not `python3`. |
| **macOS** | Chrome path differs; profile under `~/Library/Application Support/Google/Chrome`. | `platform_utils.py` resolves it; if launch fails, check the profile path. |
| **Linux** | Primary/validated platform. | Nothing special. |

## EasyEDA transport (phases 3–9)

Two backends, auto-selected by `EdaSession` (override with `EDA_BACKEND`):

1. **Bridge (preferred)** — install the `run-api-gateway` extension in EasyEDA Pro, tick
   *"allow external interaction"*, and run the bridge server (needs Node.js 18+). It listens on
   ports **49620–49629**; discovery handshakes on `service:"easyeda-bridge"`. No Chrome profile
   cloning.
2. **CDP fallback** — start Chrome with `--remote-debugging-port=9222` and one signed-in EasyEDA
   editor tab open. `session._detect()` logs *why* it fell back if the Bridge isn't found.

Keep exactly **one** EasyEDA editor window open and signed in. All config knobs:
[`docs/CONFIG.md`](docs/CONFIG.md).

## KiCad (phases 10–12)

`kicad-cli` must be on PATH (it is the DRC/gerber ground truth). Verify with `kicad-cli version`.
`pcbflow drc` **refuses** to run on a board without a ruleset sibling (phantom-DRC guard) — always
pass or place a `.kicad_pro` next to the board.

## Reproduce the reference to sanity-check the toolchain

```bash
make example        # or: python3 tools/reproduce_example.py
```

Should end in `VERDICT: PASS` with a DRC-clean board and 22 gerber/drill files. If a step is
`skip`, the tool it needs (usually `kicad-cli`) isn't installed.
