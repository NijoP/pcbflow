# Changelog

All notable changes to PCB Flow are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project aims to follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Machine-computed phase gates + hard-blocked export** (`pcbflow/gates.py`, WS3) — the 12
  checkpoints become gates that *run* the checks instead of storing an asserted verdict:
  `compute_phase_gate` executes ERC (schematic), DFM/DRC (board), or spacing (placement) and
  folds the harmonized findings into a `GateOutcome` with an explicit status hierarchy
  (`BLOCKED > EMPTY > FAIL > WARN > PASS`). New verbs: **`pcbflow gate <proj> <phase>`** computes
  a gate and records the verdict; **`pcbflow export <proj>`** hard-blocks manufacturing output
  until every gate PASSES **and** a human approval-evidence file (`approved_by` /
  `approved_at_utc` / `scope`) exists. Export never signs off a DRC and never orders a board —
  human-in-the-loop is enforced in code (you cannot approve past a failing gate).
- **Offline KiCad S-expression reader** (`pcbflow/kicad_sexp.py`, WS4) — zero-dependency parser
  that reads a saved `.kicad_pcb` / `.kicad_sch` directly (no running KiCad, no pcbnew) and
  extracts the post-layout netlist. Handles all three pad-net encodings KiCad emits
  (`(net id "name")`, id-only via the net table, and name-only) — a bug found and fixed by
  validating against real boards, not just a hand-written fixture.
- **Import diff** (`pcbflow/import_diff.py`) + **`pcbflow import-check`** — verifies the
  EasyEDA→KiCad hand-off (phase 10): compares the `.enet` netlist against the netlist read
  back from the `.kicad_pcb` and **fails loudly** on a dropped component or a named-net
  connectivity mismatch, so a layout is never built on a corrupted import.
- **Harmonized finding schema** (`pcbflow/findings.py`, WS2) — one traceable record for every
  check: stable sha256 id, detector, rule_id, category, severity, **confidence**
  (deterministic/heuristic/datasheet-backed), **evidence_source**, components/nets,
  recommendation, and provenance. Ships `sort_findings` (deterministic), `report` (pass/fail
  rollup), `trust_summary` (confidence/evidence mix → level), and deterministic `to_json` /
  `to_markdown` emitters.
- **`--json` output** on `pcbflow erc` / `dfm` / `verify` / `import-check` — deterministic,
  schema-validated harmonized findings for machine consumption.

### Changed
- **External-tool call hardening (WS4)** — `tools/drc.py` now bounds `kicad-cli` with a timeout
  and returns a documented manual-fallback command on timeout; `cdp.py` bounds the browser
  connect with `open_timeout`; `EdaSession._detect` no longer swallows a Bridge-discovery
  failure silently — it logs why it fell back to CDP.
- **ERC engine** (`pcbflow/erc.py`) — offline electrical rule check on an `.enet` netlist:
  floating pins, dangling (single-pin) nets, missing ground, and power rails without
  decoupling. Runs the moment you have a netlist — no live tool needed.
- **CLI commands** wiring the netlist/rules tooling into `pcbflow`: `enet` (parse + verify),
  `erc` (electrical rule check), `dfm` (DRC/DFM vs the JLCPCB profile), and **`verify`** — the
  offline phase-5 audit (structure + ERC, plus DFM when a board-features JSON is given) with a
  single PASS/FAIL verdict.

### Changed
- **Docs truthing (WS0)** — corrected two overstated claims to match the code: the worked
  example is now described as the **front half** of the workflow (end-to-end build landing
  next), and the "complete self-healing reliability layer" as a reliability layer whose
  structured logging + self-healing recovery engine are built/unit-tested but **opt-in** (not
  yet wired into every phase). Also fixed the CDP-fallback path in the README (`automation/
  browser/cdp.py`) and the phase-usage note in `automation/easyeda/README.md`.

### Added
- Production-hardening initiative docs: `AUDIT.md` (claims-vs-evidence + tech-debt) and
  `IMPROVEMENT_PLAN.md` (ordered workstreams to the 10/10 bar).

## [0.1.0-beta] — 2026-07-13

First public **Beta**. An AI-assisted electronics engineering workspace that takes a board
from requirements to manufacturing-ready files, with EasyEDA (schematic + placement) and
KiCad (routing + verification) and the engineer in the loop.

### Added
- **12-phase engineering workflow** (`workflow/`) with per-phase gates and AI agent roster
  (`agents/`), plus the engineering knowledge base (`knowledge/`) and templates.
- **`pcbflow` package + CLI** — project phase-gating, IPC-2221 solver, placement geometry,
  routing width/stitch math, congestion analysis.
- **`.enet` v2.0.0 netlist IR** (`pcbflow/enet.py`) — parse/emit/verify EasyEDA's official
  netlist, engineering views (nets, BOM, floating pins, net classes), and a bridge into the
  design-intelligence index.
- **Data-driven DRC/DFM RuleSet** (`pcbflow/dfm.py`) — JLCPCB capability profile with the
  phantom-DRC guard and true hole-to-hole / same-net-skip geometry.
- **MCP servers** — `pcbflow-mcp` (compute/orchestration) and `pcbmunch` (design intelligence).
- **EasyEDA automation** — official Bridge transport (`automation/easyeda/bridge.py`) with a
  unified `EdaSession` (Bridge primary, raw-CDP fallback), plus recon/dump.
- **KiCad integration** — `kicad-cli` DRC runner as the verification ground truth.
- **Reliability layer** (`tools/`) — environment `doctor`, structured logging, diagnosis,
  retry/recovery, and self-healing; all unit-tested and cross-platform.
- **Architecture audit** (`architecture/`) — EasyEDA/KiCad teardown, target architecture,
  and knowledge graph; upstream-tooling verdict (`docs/17`) + catalog (`knowledge/upstream/`).
- **Worked example** — `projects/example-usb-c-3v3/` (a real, machine-checkable board).
- **Handbook** for engineers, incl. Windows and macOS setup guides.

### Known limitations (Beta)
- The EasyEDA Bridge/CDP transport, KiCad routing, and placement automation are unit-tested
  against mocks; **end-to-end paths need validation on a live EDA session**, and the
  cross-platform tooling is validated on Linux (Windows/macOS built + unit-tested, not yet
  host-validated).
- The `enet`/`dfm`/`bridge` modules are library-complete but not yet wired as first-class CLI
  subcommands.

[Unreleased]: https://github.com/NijoP/pcbflow/compare/v0.1.0-beta...HEAD
[0.1.0-beta]: https://github.com/NijoP/pcbflow/releases/tag/v0.1.0-beta
