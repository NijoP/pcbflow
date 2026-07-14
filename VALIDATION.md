# VALIDATION.md — what is proven, and what still needs a live session

This file is the honest record of what pcbflow's tests and tooling actually verify, and what is
built but **not yet validated on live hardware/tools** this project could exercise. Every claim
here maps to a committed test or artifact, or to a `NEEDS-LIVE-VALIDATION` entry with exact
manual steps. Ground truth for the numbers is the test suite + `kicad-cli`, not prose.

## Automated tests (offline, cross-platform)

- **80 tests, 0 failures**, ~0.4 s, pure-offline (`python -m pytest`). Run on ubuntu + macOS +
  windows × Python 3.9/3.12 in CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
- **Pure-logic coverage ≈ 89%**, gated at ≥80% in CI. The two MCP servers require the optional
  `mcp` extra and are excluded from the core gate ([`.coveragerc`](.coveragerc)); they are
  integration surfaces, not pure logic.

| Area | Module | Coverage | Proven by |
|---|---|---|---|
| Harmonized findings | `pcbflow/findings.py` | 99% | `tests/test_findings.py` (schema, stable id, deterministic JSON, trust levels) |
| ERC | `pcbflow/erc.py` | 100% | `tests/test_erc.py` |
| DFM / DRC ruleset | `pcbflow/dfm.py` | 100% | `tests/test_dfm.py` (reference numbers, phantom guard, hole-to-hole) |
| KiCad S-expr reader | `pcbflow/kicad_sexp.py` | 93% | `tests/test_kicad_sexp.py` (golden parse + 3 pad-net forms) |
| Import diff | `pcbflow/import_diff.py` | 91% | `tests/test_import_diff.py` (match / injected mismatch / dropped part) |
| Phase gates + export | `pcbflow/gates.py` | 82% | `tests/test_gates.py`, `tests/test_fixtures.py` |
| Geometry / IPC / routing / congestion | `geometry/ipc/routing/congestion.py` | 93–100% | their `tests/test_*.py` |
| CLI wiring | `pcbflow/cli.py` | 74% | `tests/test_cli.py`, `tests/test_cli_commands.py` |

## Fixture corpus (gates block bad, pass good)

- **Known-good:** `projects/example-usb-c-3v3` passes every gate (schematic PASS, board matches
  netlist, DRC clean).
- **Known-bad:** `tests/fixtures/known_bad/` — 3 bad schematics (floating pin, no ground,
  dangling net) + 3 bad boards (thin track, hole-to-hole, tiny via). `tests/test_fixtures.py`
  asserts each is **blocked** by the right gate (status ≠ PASS) — proving the gates earn their keep.

## Reproducible worked example (offline → DRC-clean + gerbers)

`make example` (`tools/reproduce_example.py`) regenerates the board and runs the full chain. On a
host with `kicad-cli` it ends in a **DRC-clean board** and **22 gerber/drill files**; the
committed report is real:

- `projects/example-usb-c-3v3/12_verification/drc.rpt` → **`Found 0 DRC violations` /
  `Found 0 unconnected pads`** (this run's ground truth).
- `import-check` → board matches `netlist.enet` exactly at the ref-per-net level.

Verified locally on KiCad `kicad-cli` 10.0.4. CI runs the offline half (`--check`) without KiCad.

## NEEDS-LIVE-VALIDATION (built + unit-tested against mocks; needs a real session)

| Item | State | Manual verification |
|---|---|---|
| **EasyEDA Bridge transport** (`automation/easyeda/bridge.py`) | unit-tested vs a stdlib mock server | Install the `run-api-gateway` extension, run the bridge server, then `python3 automation/easyeda/session.py backend` should print `bridge`; `EdaSession().run("return 1+1")` returns `{ok:true, v:2}`. |
| **CDP fallback** (`automation/browser/cdp.py`) | proven in the origin project; no offline test | Start Chrome `--remote-debugging-port=9222` with an EasyEDA editor tab; `python3 automation/browser/cdp.py tabs` lists the editor; `eval` returns JSON. |
| **Live recovery strategies** (`tools/recovery.py`) | correct logic, unit-tested vs mocks | Trigger a renderer hang / session logout in a real EasyEDA session and confirm the strategy recovers (self-flagged in the file). |
| **Cross-platform launch** (`tools/launch_easyeda.py`) | path logic unit-tested on Linux | Run on a real macOS and Windows host; confirm Chrome launches with a cloned profile. |
| **Full `make example` with KiCad on macOS/Windows** | verified on Linux | Install KiCad, run `make example`, expect `VERDICT: PASS` + gerbers. |

Nothing above is claimed as "done" in the README; each is marked in-progress in
[`ROADMAP.md`](ROADMAP.md).
