# pcbflow — the CLI / harness

One command-line entry point that ties the 12-phase workflow, the reliability layer,
and the automation tools together. Pure Python 3 standard library at the core (the only
dependency, `websockets`, is used solely by the headless EasyEDA driver).

## Install

```bash
pip install -e .          # from the repo root — gives you the `pcbflow` command
# or, with nothing installed at all:
python3 -m pcbflow <command>
```
On Windows use `python` instead of `python3` (see `handbook/windows-setup.md`).

## Commands

**Project (the harness):**
```bash
pcbflow init my-board --description "USB-C LED blinker"   # create a project
pcbflow status my-board                                   # current phase + verdict
pcbflow verdict my-board 1 PASS --note "feasible"          # record a phase verdict
pcbflow advance my-board                                   # -> next phase (REQUIRES a PASS)
pcbflow phases                                             # list the 12 phases
pcbflow gate my-board 5                                    # COMPUTE a gate (runs the checks) + record it
pcbflow export my-board --approval approval.json           # manufacturing export — HARD-BLOCKED
```
`gate` doesn't store an opinion — it *runs* the phase's real checks (ERC on the netlist, DFM/DRC
on the board, spacing on the placement) and records the computed verdict. `export` **refuses**
to produce fab files unless every gate PASSES **and** a human approval-evidence file exists
(`approved_by` / `approved_at_utc` / `scope`). It never signs off a DRC and **never orders a
board** — you do. `advance` refuses to move on without a `PASS` — *place nothing over wrong*, enforced.
Project state lives in `projects/<name>/pcbflow_state.json` (JSON, so a crash never
loses your place).

**Engineering:**
```bash
pcbflow ipc 10                 # IPC-2221: 10 A -> 7.19 mm [plane/pour] + ~12 vias
pcbflow ipc 2 --oz 2           # 2 A on 2 oz copper
pcbflow ipc 3 --internal       # inner-layer (0.5 oz) derating
```

**Placement & routing planning:**
```bash
pcbflow widths nets.json         # IPC-2221 trace-width table (net -> width / plane)
pcbflow stitch-pitch 0.7         # λ/20 ground-stitch pitch from an edge rise time (ns)
pcbflow spacing placement.json   # pad-spacing audit on real geometry (exit 1 on violations)
pcbflow congestion nets.json     # predict where routing will need via-fans
```

**Audit (offline checks — the moment you have a netlist, no live tool needed):**
```bash
pcbflow enet netlist.enet            # parse + structural verify of an EasyEDA .enet
pcbflow erc  netlist.enet            # electrical rule check (floating pins, ground, decoupling)
pcbflow dfm  board.json              # DRC/DFM vs the JLCPCB profile
pcbflow verify netlist.enet --board board.json   # phase-5 audit: structure + ERC (+ DFM)
pcbflow import-check netlist.enet board.kicad_pcb # phase-10: does the KiCad board match the netlist?
pcbflow erc  netlist.enet --json     # harmonized findings as JSON (also on dfm/verify/import-check)
```
`import-check` reads the `.kicad_pcb` directly (no KiCad running, `pcbflow/kicad_sexp.py`) and
**fails loudly** if a component or named net drifted during the EasyEDA→KiCad import — so a
layout is never built on a corrupted netlist.
Every check emits the **harmonized finding schema** (`pcbflow/findings.py`): each finding
carries a stable id, detector, rule_id, severity, **confidence**, **evidence_source**,
components/nets, recommendation, and provenance — so reports are git-diffable and each claim
carries its own evidence. `--json` output is deterministic and schema-validated.

**Tools (delegates to the automation):**
```bash
pcbflow doctor                 # check the environment
pcbflow launch                 # open EasyEDA in Chrome (cross-platform)
pcbflow dump dump.json         # dump the live schematic
pcbflow recon dump.json net.json   # rebuild the netlist (phase-5 audit)
pcbflow drc board.kicad_pcb rules.kicad_pro   # KiCad DRC (phantom-guard)
```

## How it maps to the framework

| Layer | Where |
|---|---|
| Phase order + gating | `pcbflow/phases.py`, `pcbflow/project.py`, `pcbflow/gates.py` |
| IPC-2221 solver | `pcbflow/ipc.py` |
| Offline checks (ERC / DFM / spacing) | `pcbflow/erc.py`, `pcbflow/dfm.py`, `pcbflow/geometry.py` |
| KiCad file reader + import diff | `pcbflow/kicad_sexp.py`, `pcbflow/import_diff.py` |
| Harmonized finding schema | `pcbflow/findings.py` |
| CLI dispatch | `pcbflow/cli.py` |
| Reliability (logging, diagnose, retry, heal) | `tools/` (used by the workflow) |
| EDA automation | `automation/` (driven by `pcbflow dump`/`recon`/`drc`/`launch`) |

## Tests

```bash
python3 -m pytest            # if pytest is installed
# or standalone (no deps):
python3 tests/test_ipc.py && python3 tests/test_project.py \
  && python3 tests/test_phases.py && python3 tests/test_cli.py
```
