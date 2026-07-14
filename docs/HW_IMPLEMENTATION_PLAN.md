# HW_IMPLEMENTATION_PLAN.md — codifying the hardware engineer (T1–T4)

How we turn a senior hardware engineer's judgement into automated, gated checks. Companion to
[`HW_GAP_ANALYSIS.md`](HW_GAP_ANALYSIS.md) (what's missing) — this is *how* we build it: the
tools a HW engineer uses, how each maps to code, and the **exact math/physics** each check runs.

Every check is a **detector → harmonized finding (`pcbflow/findings.py`) → gate
(`pcbflow/gates.py`)**. Same architecture as the software checks; same human-in-the-loop stance
(advisory + blocking, never auto-sign-off).

## 1. The tools a hardware engineer uses, and how we codify each

| HW engineer's tool | What it does | How we codify it (no GUI, pure Python) |
|---|---|---|
| **ERC** (schematic rule check) | pin-type conflicts, drive contention | a pin-type **conflict matrix** + per-net driver count (`erc_pins.py`) |
| **Datasheet + derating** | part ratings vs operating point | algebraic **rating checks** with derating factors (`ratings.py`) |
| **Power-budget spreadsheet** | rail sourcing + current sum | a rail **graph** + current summation (`power_tree.py`) |
| **Field solver** (impedance) | Z0 of a trace on a stack-up | closed-form **IPC-2141** microstrip/stripline (`si.py` + `stackup.py`) |
| **Length-tuning** | diff-pair skew, equal-length | tolerance check on trace lengths (consumes `.enet` `differentialPair`/`equalLengthNetGroup`) |
| **IPC-2152 current calc** | trace/via ampacity, IR drop | the IPC current + resistance formulas (`pdn.py`) |
| **Thermal calc** | junction temperature | `Tj = Ta + P·θJA` derating (`thermal.py`) |
| **Creepage/clearance table** | spacing vs voltage (safety) | IPC-2221 Table 6-1 lookup (`creepage.py`) |
| **DFM/DFA review** | tombstoning, fiducials, test points | asymmetry + presence rules (`dfa.py`) |
| **BOM/sourcing tool** | MPN, lifecycle, package match | field-completeness audit (`bom_audit.py`) |
| **Requirements sheet** | budget vs actual | machine compare feasibility ↔ BOM/board (`feasibility_check.py`) |

## 2. The data layer we must add first (the "software fix")

The `.enet` carries connectivity + net-class + diff-pair/equal-length intent, but **not** pin
electrical types or part ratings — so ERC/ratings/power-tree have nothing to reason over. The
enabling fix is a **parts spec** (`pcbflow/parts.py`): a small, optional sidecar
(`parts.json`/`.yaml`) keyed by designator that carries `pin_types`, `ratings`
(voltage/current/power/package), and a `role` (regulator/led/mosfet/…). Checks degrade
gracefully: with no spec they skip (report `EMPTY`/`info`), never guess silently.

Plus a **stack-up model** (`pcbflow/stackup.py`) that impedance + current calcs consume.

## 3. The math / physics per check

### Tier 1 — electrical correctness
- **HW1 ERC pin matrix:** classify each net's pins by type {IN, OUT, BIDIR, TRI, PASSIVE,
  PWR_IN, PWR_OUT, OC, NC, UNSPEC}. Rules: ≥2 strong drivers (OUT/PWR_OUT) on a net → **error**
  (contention); OUT + PWR_OUT → error; NC connected → error; net of only PASSIVE/IN with no
  driver → **warn** (undriven). Encoded as a symmetric pair-severity table + a driver counter.
- **HW2 ratings** (algebra, with margins):
  - Capacitor: `V_rating ≥ V_rail / derate` (ceramics derate ≈ 0.5 → want 2× rating).
  - LED resistor: `I = (V_rail − Vf)/R`; flag if `I ∉ [I_min, I_max]` or R missing.
  - Resistor power: `P = I²·R`; flag `P > P_package·derate` (derate 0.5).
  - MOSFET: `Vds_applied ≤ Vds_max·0.8`, `Vgs_drive ≤ Vgs_max`.
  - LDO dropout: `V_in − V_out ≥ V_dropout(load)` (else brownout — the learning-db failure).
- **HW3 power tree:** build rail→source graph; every IC `PWR_IN` pin must reach a rail with a
  source (regulator `PWR_OUT`/connector); voltage-domain consistency (part's rated V matches its
  rail); `Σ I_load(rail) ≤ I_rating(regulator)`.

### Tier 2 — integrity
- **HW0 stack-up:** layers with `{copper_oz, height_mm, Er}`; derive copper thickness
  `t = 0.0347 mm/oz · oz`.
- **HW5 impedance (IPC-2141 microstrip):** `Z0 = 87/√(Er+1.41) · ln(5.98·h / (0.8·w + t))` for
  `0.1 < w/h < 2.0`; stripline `Z0 = 60/√Er · ln(1.9·b/(0.8·w+t))`. Differential (edge-coupled):
  `Z_diff ≈ 2·Z0·(1 − 0.48·e^(−0.96·s/h))`. Flag |Z0 − Z_target| > tolerance (default ±10%).
  **Length-match:** for each `differentialPair`, `|len_P − len_N| ≤ skew_tol`; for each
  `equalLengthNetGroup`, `max−min ≤ tol`.
- **HW6 PDN:**
  - Trace resistance: `R = ρ·L/(w·t)`, `ρ_Cu = 1.72e−8 Ω·m` (×(1+0.0039·ΔT) for temp).
  - IR drop: `V = I·R`; flag `V > budget` (e.g. 3% of rail).
  - Via ampacity (IPC-2152 form): `I = k·ΔT^0.44·A^0.725`, barrel area
    `A = π·d·t_plating` (t_plating ≈ 0.025 mm); k≈0.048 (external)/0.024 (internal). Flag if the
    net's via count × per-via current < net current.
- **HW7 thermal:** `Tj = Ta + P·θJA`; flag `Tj > Tj_max·derate`. Copper-area spreading reduces
  effective θJA (first-order note).

### Tier 3 — manufacturing
- **HW12 creepage/clearance:** IPC-2221 Table 6-1 (bare board, internal/external, coated) as a
  breakpoint table of min spacing vs peak voltage; flag pad/track pairs on nets whose ΔV exceeds
  the spacing's rated voltage.
- **HW10 DFA:** tombstoning risk = asymmetric thermal mass on a 2-pad passive (one pad on a big
  copper pour, the other not); fiducials present (≥2–3 global); test-point coverage of key nets.
- **HW11 BOM audit:** each BOM line has MPN (or is DNP), package matches footprint, no duplicate
  designators, second-source flag.

### Tier 4 — requirements
- **HW13 feasibility gate:** compare declared `{power_budget_W, size_mm, layers, cost_target}`
  against `Σ P` (from ratings), board size (from `kicad_sexp`), layer count, and `Σ BOM cost`.
- **HW14 mechanical/3D:** deferred (needs a mechanical model) — logged, not built now.

## 4. Does the software layer already handle it? (evaluation + fixes)

| Need | Software layer today | Fix |
|---|---|---|
| Emit a finding | ✅ `pcbflow/findings.py` | none — reuse `finding()` |
| Gate a phase on it | ✅ `pcbflow/gates.py` | add HW detectors to `compute_phase_gate` (5 electrical, 11–12 integrity, 2 BOM) |
| Read board geometry | ✅ `pcbflow/kicad_sexp.py` (nets/pads) | **extend** to read **track segments + widths + via geometry** (needed for length, IR, ampacity) |
| Pin types / part ratings | ❌ not in `.enet` | **add** `pcbflow/parts.py` sidecar model |
| Stack-up | ❌ only layers+oz | **add** `pcbflow/stackup.py` |
| Net-class / diff-pair / equal-length intent | ✅ in `.enet`, unconsumed | wire into `si.py` |

**Net:** the findings/gates spine handles it; the two real software fixes are (a) the parts +
stack-up data models and (b) extending `kicad_sexp` to read track/via geometry. Both are built
as part of this work.

## 5. Build order (each = detector + tests + known-bad fixture, committed per tier)
Foundation (`parts.py`, `stackup.py`, `kicad_sexp` track/via read) →
**T1** (`erc_pins`, `ratings`, `power_tree`) → **T2** (`si`, `pdn`, `thermal`) →
**T3** (`creepage`, `dfa`, `bom_audit`) → **T4** (`feasibility_check`) →
wire all into a `hw` gate + `pcbflow hw` CLI verb + update `HW_GAP_ANALYSIS.md` status.
