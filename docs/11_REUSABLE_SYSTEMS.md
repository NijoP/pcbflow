# 11 · Reusable Systems Catalog

Every major workflow from the origin project, catalogued for reuse. Each entry:
**Purpose · Inputs · Outputs · Dependencies · Failure modes · Validation · Reusable
core · Generalize by · Automation upside.** The "reusable core" column is what you
lift; the "generalize by" column is what you swap.

---

## S1 · Section Schematic Generator

- **Purpose:** realize one functional block of a schematic (parts + wiring) from a
  spec, re-runnably.
- **Inputs:** a CONFIG block — `PARTS[]` (ref, search query, disambiguation token,
  grid pos, rotation, pin→net map) + `PASSIVES[]` (ref, kind, value, netA, netB).
- **Outputs:** placed & net-labelled parts in the live EDA tool.
- **Dependencies:** the EDA standalone-script API; an online component library.
- **Failure modes:** array-part false match; wrong-value passive; collinear-stub
  short; designator not settable via API.
- **Validation:** LOG shows 0 unmatched pins / 0 skips; phase-5 netlist diff.
- **Reusable core:** the board-agnostic **engine** — `pick()`, `pickPassive()`,
  `wirePins()`, `pinDir()`, retry/backoff, `isArray()`, `isWrongType()`, EIA-code
  discriminator.
- **Generalize by:** replacing the CONFIG (PARTS/PASSIVES/net names) — pure data.
- **Automation upside:** the whole phase; the engine is fixed, only data changes.
- **Template:** [`templates/section_generator.template.js`](../templates/section_generator.template.js)

---

## S2 · CDP Headless Driver

- **Purpose:** read/mutate the live cloud EDA board programmatically.
- **Inputs:** a JS expression; a logged-in Chrome profile clone on `:9222`.
- **Outputs:** a `{ok, v}` JSON result; screenshots.
- **Dependencies:** Chrome + CDP; the profile-clone recipe.
- **Failure modes:** logged-out clone; OAuth block; edit-lock (two sessions);
  renderer hang.
- **Validation:** the `{ok:false, err}` envelope surfaces page errors as data.
- **Reusable core:** `cdp.py` — the websocket driver — is generic **as-is**.
- **Generalize by:** changing the editor-tab URL match string.
- **Automation upside:** it's the backbone of the verification layer.
- **Ref:** [`07_BROWSER_AUTOMATION.md`](07_BROWSER_AUTOMATION.md)

---

## S3 · Netlist Reconstructor

- **Purpose:** rebuild pin→net when the tool's netlist API hangs headless.
- **Inputs:** a dump of wires (with `.net`) + component pins (without).
- **Outputs:** a pin→net map / net-membership table.
- **Dependencies:** S2 (readback).
- **Failure modes:** net-resolver lag after bulk create (pins read FLOAT).
- **Validation:** diff against `net_connection.md` §membership.
- **Reusable core:** `recon.py` — coordinate-matching inference — generic.
- **Generalize by:** nothing structural; it's board-agnostic.
- **Automation upside:** the phase-5 gate, in seconds, headless.

---

## S4 · Placement Engine

- **Purpose:** compute a region-planned, spacing-clean, practical placement.
- **Inputs:** a zone/region map, per-part courtyards (real pad bbox), a
  decap-adjacency graph, anchor overrides for edge parts.
- **Outputs:** `{designator: {x, y, rot, layer}}` + a refdes silk plan.
- **Dependencies:** a live board readback for real pad geometry.
- **Failure modes:** origin≠centroid offset; stale getAll; relaxation oscillation on
  clusters.
- **Validation:** real-geometry spacing audit + practical review (edge parts open
  outward; sensors share axis).
- **Reusable core:** region-shelf placement, demand-sized courtyards, spiral-hug
  decap placement, relaxation, **surgical re-place of residual violators** (don't
  re-tune relaxation params — it oscillates), MST congestion scoring.
- **Generalize by:** the zone map + anchor table + decap graph (all data).
- **Automation upside:** Tier-1 computation; only client sign-off is human.
- **Templates:** [`placement.template.json`](../templates/placement.template.json)

---

## S5 · Design-Rule / Net-Class Applier

- **Purpose:** turn `design_rules.json` into the EDA tool's DRC config.
- **Inputs:** the net-class rulebook; the live net list.
- **Outputs:** an applied ruleset; assertion of **0 nets on `default`**.
- **Dependencies:** the EDA rules API (or a documented UI apply sequence).
- **Failure modes:** a class keyed on a stale net name silently matches nothing and
  passes DRC — **fails silent, not loud**.
- **Validation:** diff the ruleset's net names against the live net list before
  apply; assert 0 unclassed.
- **Reusable core:** the probe→read→build→apply pattern + the 0-unclassed assertion.
- **Generalize by:** the net-class taxonomy (10 classes) + net names.
- **Template:** [`design_rules.template.json`](../templates/design_rules.template.json)

---

## S6 · Routing Planner

- **Purpose:** produce an ordered, DRC-gated routing plan before drawing copper.
- **Inputs:** frozen placement, netlist with per-net current, the rules template.
- **Outputs:** `route_sequence.json` (phases) + `trace_width_table.json` +
  `congestion_grid.json` + a feasibility score.
- **Dependencies:** IPC-2221 solver; a congestion model; the planning swarm.
- **Failure modes:** under-rating a 0.5 oz inner plane; a GND stitch where a
  GND↔VSYS cap is needed; fine-pitch mask bridging.
- **Validation:** 0 unclassed nets; via budget itemized; handoff conditions stated.
- **Reusable core:** the phase order (planes → criticals → constrained autoroute →
  power pours → **GND pour + stitch LAST**); the IPC-2221 width computation; the
  2 mm-bin congestion grid.
- **Generalize by:** net names, currents, coordinates, pour polygons.
- **Templates:** [`route_sequence.template.json`](../templates/route_sequence.template.json),
  [`trace_width_table.template.json`](../templates/trace_width_table.template.json)

---

## S7 · KiCad GND Stitcher / Migration Pipeline

- **Purpose:** migrate an EDA board to KiCad and complete GND planes + stitch vias.
- **Inputs:** the EDA board; a PADS export; layer/keepout definitions.
- **Outputs:** a KiCad board with pours + collision-checked stitch vias, DRC-clean.
- **Dependencies:** `kicad-cli`, `pcbnew` Python, a PADS export from the EDA tool.
- **Failure modes:** blind via-per-pad shorts; mounting holes dropped on import;
  phantom DRC without the `.kicad_pro`; `pcbnew` stale handles after mutation.
- **Validation:** import fidelity (0 dropped, sub-µm residual); `kicad-cli` DRC with
  the ruleset sibling; connectivity ratsnest = 0.
- **Reusable core:** PADS-export → `kicad-cli pcb import` (carries nets; Altium
  export is unusable); **collision-checked** via placement (never blind);
  one-shot-`pcbnew`-session discipline.
- **Generalize by:** layer IDs, keepout coordinates, mounting-hole positions.

---

## S8 · Real-Geometry Audit Suite

- **Purpose:** ground-truth validation independent of any generator's self-report.
- **Inputs:** a live board readback (pads, components, holes).
- **Outputs:** a spacing/keepout/containment violation list + heat-map + verdict.
- **Dependencies:** S2 (readback).
- **Failure modes:** auditing stale snapshots or pad rotation (defeated by re-read).
- **Validation:** *it is* the validation — its output is the gate.
- **Reusable core:** the bbox-gap computation, connector inflation, centroid-from-
  pad-union, M2 keepout check, board-containment with per-type overhang.
- **Generalize by:** the DFM minimum gap + per-type overhang constants.
- **Ref:** [`09_VALIDATION.md`](09_VALIDATION.md)

---

## S9 · Continuous-Learning KB

- **Purpose:** capture each failure→lesson so it's never re-walked.
- **Inputs:** a discovered failure + its root cause + fix.
- **Outputs:** an append-only entry: `Heuristic → Why → Instance → Validation →
  Prevention`.
- **Dependencies:** none; a markdown file + discipline.
- **Failure modes:** entries that stay project-specific (state the *heuristic*
  generically, the *instance* specifically).
- **Validation:** each entry carries an auto-checkable assertion.
- **Reusable core:** the five-field entry format; appending lessons to agent
  definitions so future invocations inherit them.
- **Generalize by:** it's already general — this is `routing_learning_db.md`
  distilled into [`03_KNOWLEDGE_GRAPH.md`](03_KNOWLEDGE_GRAPH.md).

---

## Lift order for a new project

Start with **S2 + S3** (readback + netlist reconstruction — pure infrastructure),
then **S1** (schematic gen), then **S8** (audit), then **S4–S6** (placement +
rules + routing plan). S7 only if you migrate to KiCad. S9 from day one — it's free
and it compounds.
