# Changelog

All notable changes to PCB Flow are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project aims to follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Routing checks against the board** (R2) — `pcbflow/routing_check.py` enforces the rulebook on
  the routed `.kicad_pcb`: **pour required** (a net ≥ the pour threshold on traces, not a filled
  pour → error), **trace under-width** (min track width < the IPC-2152 width its current needs →
  error), **over-length** (net longer than its class max → warning), and **return-path missing**
  (a high-speed impedance-class net with no GND reference plane → warning). Backed by a new
  `kicad_sexp.read_pcb_zones()` copper-pour reader.
- **Codified routing rulebook + IPC-2152 width driver** (R1) — `pcbflow/routing_rules.py` loads a
  `routing_rules.json` the routing phase must obey: per-net-class widths (**derived from current
  via IPC-2152**, `pcbflow/ipc.ipc2152_width_mm`), the high-current **pour threshold** (≥ 2.0 A
  or width > 1.0 mm, ΔT = 10 °C default + per-project override), **EMI** rules, and pour settings.
  **Every rule carries a citation** (`$cite`) and `validate()` rejects any uncited number.
  IPC-2152 is the driver (area-based + layer-copper-aware: JLCPCB 1 oz outer / **0.5 oz inner** →
  ~2× the width); IPC-2221 kept as the (more conservative) reference with the "why 2152" note.
- **Codified placement via visual mapping** (`pcbflow place-plan`, P1) — placement is planned and
  scored before it executes, never placed blind:
  - `pcbflow/placement_intent.py`: a `placement_intent.json` sidecar capturing board outline,
    connector→edge assignments, functional clusters, keep-outs, decoupling pairs, and sizes.
  - `pcbflow/placer.py`: a deterministic force-directed optimizer that **minimizes HPWL**
    (half-perimeter wirelength — the trace-length proxy), snaps decaps to their IC, pins
    connectors to their edge, then legalizes courtyard overlaps. On the example: HPWL 240 → 42 mm.
  - `pcbflow/render_svg.py`: a pure-Python SVG **visual map** (outline, courtyards, ratsnest) —
    the artifact the engineer approves **before** placement executes (human checkpoint #1).
  - `pcbflow/placement_check.py`: the placement gate — decoupling proximity (≤2 mm ok / 2–4 mm
    WARN / >4 mm FAIL), connectors-on-edge, courtyard spacing (0.15 mm fab floor), keep-out
    intrusion, and the HPWL metric. Every check has a known-bad test.
- **Hardware Tiers 3 & 4 — manufacturing + requirements** (`pcbflow hw`):
  - **creepage/clearance** (`pcbflow/creepage.py`): IPC-2221 spacing-vs-voltage — flags a board
    whose clearance is below what its peak voltage needs (safety).
  - **DFA/DFT** (`pcbflow/dfa.py`): fiducials, test-point coverage, and tombstoning risk (advisory).
  - **BOM audit** (`pcbflow/bom_audit.py`): every BOM line must be orderable (MPN/LCSC).
  - **feasibility traceability** (`pcbflow/feasibility_check.py`): the declared power/size/layer/
    cost/part-count budgets are machine-checked against the actuals (catches silent scope drift).
  All wired into `pcbflow hw`; the example runs clean (2 advisory info items for a minimal board).
  Completes the hardware roadmap T1→T4 from `docs/HW_IMPLEMENTATION_PLAN.md`.
- **Hardware Tier 2 — integrity checks** (`pcbflow hw --board`) — real physics on the routed board:
  - **signal integrity** (`pcbflow/si.py`): IPC-2141 microstrip impedance + differential-pair skew
    and equal-length matching — consuming the `.enet` `differentialPair`/`equalLengthNetGroup`/
    `netClass` intent that nothing read before.
  - **power distribution** (`pcbflow/pdn.py`): IR drop `V=I·R` (R=ρL/wt) vs a rail budget, and via
    ampacity (IPC-2221 barrel-wall law) vs the net current.
  - **thermal** (`pcbflow/thermal.py`): `Tj = Ta + P·θJA`, with LDO power `(Vin−Vout)·Iout`.
  - Enabled by extending `pcbflow/kicad_sexp.py` to read **track/via geometry** (per-net length,
    width, layer) — validated on the real example board.
- **Hardware Tier 1 — electrical-correctness checks** (`pcbflow hw`) — the first real
  electrical (not just geometric) checks, each emitting harmonized findings:
  - **pin-type ERC** (`pcbflow/erc_pins.py`): driver contention, output-on-power-rail,
    no-connect-wired, undriven inputs — the drive conflicts a topology ERC can't see.
  - **power-tree integrity** (`pcbflow/power_tree.py`): unsourced rails, voltage-domain
    mismatch, and current-budget (Σ load > regulator rating).
  - **component ratings** (`pcbflow/ratings.py`): capacitor DC-bias derating, LED current
    `(V−Vf)/R`, resistor `I²R` power, **LDO dropout/brownout**, MOSFET Vds/Vgs margin — the
    exact failure classes `knowledge/learning-db.md` already paid for.
  - Enabled by two new data models — `pcbflow/parts.py` (optional `parts.json` sidecar carrying
    pin electrical types + ratings) and `pcbflow/stackup.py` (physical stack-up for the Tier-2
    integrity math). Checks degrade gracefully with no parts spec. Scoped in
    [`docs/HW_IMPLEMENTATION_PLAN.md`](docs/HW_IMPLEMENTATION_PLAN.md); the example ships a
    `parts.json` that passes clean.
- **Docs truthing + claims linter** (WS8) — the README now reflects the proven reality: CI /
  license / coverage badges, the worked example described as a **complete, one-command
  reproducible** board, and the "Built now" list updated with machine gates, harmonized
  findings, import-diff, the fixture corpus, and CI. New `tools/check_claims.py` (run in the
  test suite) fails if any documented Markdown link points at a missing artifact — enforcing
  "no aspirational documentation."
- **CI + VALIDATION.md** (WS5) — GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))
  runs the suite + a ≥80% coverage gate on **ubuntu + macOS + windows × Python 3.9/3.12**, plus
  an offline worked-example check. New [`VALIDATION.md`](VALIDATION.md) records exactly what is
  proven (80 tests, ~89% pure-logic coverage, the fixture corpus, the DRC-clean example) and a
  `NEEDS-LIVE-VALIDATION` ledger (EasyEDA Bridge/CDP, cross-platform launch, live recovery) with
  manual steps — nothing unproven is claimed as done.
- **Per-agent entry files** (WS9) — `GEMINI.md`, `.cursor/rules/pcbflow.mdc`, and `llms.txt`
  join the existing `CLAUDE.md` / `AGENTS.md`, each a thin pointer to the one shared core
  (workflow + knowledge + CLI). The "works with Claude Code / Codex / OpenCode / Cursor /
  Gemini" claim is now backed by an entry file per agent.
- **Packaging + config discipline** (WS7) — `pyproject.toml` gains authors, keywords, PyPI
  classifiers, project URLs, bounded deps, and a pinned `dev` extra; the package installs
  cleanly (`pip install -e .`, `pcbflow --version`) and exposes all 22 CLI verbs. New
  [`docs/CONFIG.md`](docs/CONFIG.md) documents every environment variable in one table with
  its default, and [`install-guidance.md`](install-guidance.md) captures the platform quirks
  for the AI agent (Bridge ports, CDP profile, `kicad-cli`, Windows `.py` vs `.sh`).
- **Worked example is now end-to-end + reproducible in one command** (WS1) — `make example`
  (`tools/reproduce_example.py`) regenerates the board, runs every offline check, writes the
  phase reports, and exports gerbers: netlist structure → ERC → **import-check (board matches
  netlist)** → **`kicad-cli` DRC (0 violations / 0 unconnected)** → 22 gerber/drill files → BOM.
  The routed board is produced by a documented generator (`tools/gen_example_board.py`) and is
  the phase-10 deliverable; committed reports under the project's phase folders show real output.
  Every phase folder is now filled (03/05/06/07/08/09/10/11/12).
- **Known-bad fixture corpus** (`tests/fixtures/known_bad/`, WS6) — 3 bad schematics + 3 bad
  boards, each with a `defect_class` and expected gate status; `tests/test_fixtures.py` proves
  every gate BLOCKS its bad design (status ≠ PASS) and PASSES the clean example, plus a
  phases↔agents consistency check. Coverage config (`.coveragerc`) + more CLI tests raise the
  pure-logic coverage to ~89% (MCP servers, which need the optional `mcp` extra, excluded).
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
