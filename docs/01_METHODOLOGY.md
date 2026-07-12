# 01 · The Methodology — Idea to Manufacturing

A repeatable, gated pipeline. Ten phases (0–9). Each phase is a self-contained
unit with the same nine fields, so an AI agent or a human can execute any phase
without re-reading the whole document.

**The prime directive:** you do not enter phase N+1 until phase N has a **PASS**
verdict from the verification layer. A failing gate blocks forward motion. This
is “place nothing over wrong” made structural.

**The inner loop, inside every generation phase (3–8):**

```
   read source-of-truth  →  generate ONE unit  →  senior review  →  fix  →  next unit
```

“One unit” = one schematic section, one placement region, one routing phase.
Never generate the whole board and review at the end; the blast radius of a bug
found late is the whole board.

---

## Phase 0 — Capture & Requirements

- **Objective:** convert an ambiguous brief (call, sketch, PDF, chat) into a
  quantified, cross-referenced requirement register with an explicit constraint
  verdict.
- **Inputs:** client brief, call transcript, reference photos, any hard
  constraints (size, cost, battery, certifications).
- **Outputs:** `01_Requirement_Analysis.md`, `16_Constraints_Verdict.md` (each
  constraint tagged C-n with a feasibility call).
- **Validation:** every requirement has a number and a source; conflicting
  requirements are surfaced, not silently reconciled.
- **Deliverables:** requirement register; a red/amber/green constraint table.
- **Engineering checklist:** power budget sketched? size vs component-area sanity
  checked? any single requirement that makes the board infeasible flagged?
- **Automation opportunities:** transcribe audio → structured requirements
  (Whisper + extraction); auto-flag any dimensional constraint against a
  first-order component-area estimate.
- **Human review:** the client confirms the register captures intent; the
  engineer signs the constraint verdict.
- **Exit criteria:** no unquantified requirement; no unaddressed hard conflict.

> Origin lesson: the first spec (25×25 mm) was **infeasible** — component bodies
> alone were 640 mm² against a ~1100–1300 mm² real need. Catching that in phase 0
> is a five-minute calculation; catching it in phase 6 is a wasted layout.

---

## Phase 1 — Architecture & Feasibility

- **Objective:** decide the system partition, the power architecture, the board
  size, and the layer count — with the math that forces each.
- **Inputs:** requirement register; component power/current draws.
- **Outputs:** block diagram, rail tree (e.g. VBUS→VSYS→+3V3), the **size/layer
  decision** with its supporting math.
- **Validation:** density math and current math both close (see below).
- **Deliverables:** `02_System_Architecture.md`, `05_Power_Architecture.md`, a
  one-line stackup decision.
- **Engineering checklist:** peak current on the worst rail? does any net need
  more copper than a trace can carry? does the RF module choice impose a keep-out?
- **Automation opportunities:** density estimator (courtyard area ÷ board area ×
  2); IPC-2221 solver flagging any net whose min width > ~5 mm (⇒ plane mandatory).
- **Human review:** client signs off board size (it is a cost/UX decision); the
  engineer signs the layer count.
- **Exit criteria:** size, layer count, and stackup are decided with quantified
  justification.

**Two decision frameworks that generalize to any board:**

*Density → size.* `density = component_courtyard_area / (board_side_area) × 2`
(×2 = double-sided). Empirical thresholds from the origin project: ≤25% routes
comfortably on 2-layer; ~35% is tight; >45% needs 4-layer or an interactive
finish. If the client's size gives >45% density, that is a phase-1 conversation,
not a phase-6 surprise.

*Current → layer count.* Compute the peak current on the heaviest rail. If any
path exceeds what a manufacturable trace can carry at your copper weight
(IPC-2221: ~5 A is the practical ceiling for a 1 oz trace before widths get
absurd), that current must ride a **plane**, which forces ≥4 layers. In the
origin project a ~10.5 A motor rail forced 4-layer with a dedicated VSYS plane —
**not** for routability, purely for ampacity. Knowing *why* you added layers
tells you how to use them.

---

## Phase 2 — Component Selection & Sourcing

- **Objective:** lock a BOM where every part is datasheet-verified, sourcable in
  your region, and has a known second source.
- **Inputs:** architecture; target region/distributor; cost target.
- **Outputs:** BOM with LCSC/distributor IDs, datasheet notes, second-source
  column.
- **Validation:** each part's footprint, pinout, and electricals verified against
  its datasheet — not against a search-result guess.
- **Deliverables:** `04_BOM_Selection.md`, `datasheets/` notes per critical part.
- **Engineering checklist:** module variant correct (e.g. onboard-antenna vs
  external — decisive on a compact board)? every regulator's dropout adequate at
  min battery voltage? any “cheap clone” trap (a genuine part at 30× the
  module-clone price)?
- **Automation opportunities:** datasheet Q&A extraction; distributor availability
  search (note: some sites 403 automated fetchers → use web *search* not fetch);
  cost roll-up.
- **Human review:** client signs cost-vs-feature trades (e.g. a fuel-gauge IC vs
  an ADC divider is a UX/cost call, not an engineering mandate).
- **Exit criteria:** 0 parts un-sourced; every critical part datasheet-verified;
  cost target met or the gap justified.

> Origin lessons: verify a part by **decoding its manufacturer ID**, not by the
> search string — a “22 µF” slot was silently filled with a 12 pF cap and another
> with a 2.2 µH inductor because a bad LCSC ID resolved to the wrong device. And:
> confirm the regulator survives a depleted cell (an AMS1117 browns out on a 1S
> LiPo at low SoC; a low-dropout LDO does not).

---

## Phase 3 — Source-of-Truth Documents

- **Objective:** author the two documents that ARE the board — `build_sheet.md`
  (tick-sheet) and `net_connection.md` (net dictionary) — in lockstep.
- **Inputs:** locked BOM; architecture; pinouts.
- **Outputs:** the two docs, agreeing net-for-net.
- **Validation:** a net named in the dictionary appears in the build sheet and
  vice-versa; the net-membership table (every net → every connected `refdes.pin`)
  is complete.
- **Deliverables:** `build_sheet.md`, `net_connection.md`.
- **Engineering checklist:** analog ground defined as a separate net with exactly
  one tie point? open-drain buses have pull-ups? boot-strap pins assigned? every
  IC decoupled in the sheet?
- **Automation opportunities:** cross-lint the two docs for net-name mismatches;
  auto-generate the net-membership oracle from the pin maps.
- **Human review:** engineer confirms the net list is electrically correct before
  a single part is placed.
- **Exit criteria:** zero net-name disagreements; net-membership table complete.

> This is the highest-leverage phase. A correct net dictionary lets the schematic
> generator be **dumb and deterministic** — it just wires each pin to its named
> net. Every downstream generator reads these two files.

---

## Phase 4 — Schematic Generation (section by section)

- **Objective:** realize the schematic in the EDA tool, one functional block at a
  time, via re-runnable scripts.
- **Inputs:** `build_sheet.md` (PARTS + PASSIVES per section), the section's
  pin→net map.
- **Outputs:** one generator script per block; parts placed & wired in the EDA
  tool with net labels.
- **Validation:** script LOG shows 0 unmatched pins, 0 skipped parts; connect
  **by net name**, never by drawn wire between ICs.
- **Deliverables:** `usb.js`, `mcu.js`, … (one per block); a single schematic with
  multiple **pages** (never separate files — nets must merge, refdes must be
  unique).
- **Engineering checklist:** every part token-matched (never `search()[0]`);
  array parts rejected; passives value-verified; stub direction from pin rotation.
- **Automation opportunities:** the whole phase — a board-agnostic engine + a
  per-section CONFIG. Designators are the one exception: the script API can't set
  them reliably → run project-wide **Annotate** in the UI afterward.
- **Human review:** the human runs each script in the EDA tool and pastes the log
  back (the generation is autonomous; the *live write* is human-triggered).
- **Exit criteria:** every section placed & wired; 0 unmatched pins; Annotate done.

---

## Phase 5 — Schematic Verification

- **Objective:** prove the realized schematic matches intent, net-for-net.
- **Inputs:** the live schematic; `net_connection.md` §membership.
- **Outputs:** a reconstructed netlist + a diff report + ERC results.
- **Validation:** reconstruct pin→net from wire coordinates (the tool's own
  netlist API hangs headless); diff against the membership oracle; 0 shorts, 0
  single-pin nets, 0 floating pins.
- **Deliverables:** `verification/` report set with a PASS/CONDITIONAL/FAIL verdict.
- **Engineering checklist:** analog ground ties to ground at exactly one point?
  no two pins accidentally merged (watch for collinear-wire auto-merge)? every
  power pin actually on its rail?
- **Automation opportunities:** headless CDP extraction + coordinate matching +
  automatic diff; a swarm of reviewers each taking one subsystem.
- **Human review:** engineer signs the verdict; client confirms any part/topology
  question the verdict surfaces.
- **Exit criteria:** net membership == source docs; 0 shorts; verdict = PASS.

> This gate is cheap (seconds, headless) and it is the one that protects every
> hour of layout downstream. Run it *before* any PCB work — never as an
> afterthought.

---

## Phase 6 — Placement

- **Objective:** a region-planned, **practically assemblable**, spacing-clean
  placement with full refdes silkscreen.
- **Inputs:** verified schematic; board outline; the region/zone plan.
- **Outputs:** per-designator `{x, y, rot, layer}`; a refdes silk plan.
- **Validation:** all same-layer pad gaps ≥ the hand-solder minimum, measured on
  **real** pad geometry; no silk overlaps; connectors open to the board edge.
- **Deliverables:** `placement.json`, `refdes_silk_plan.json`, screenshots.
- **Engineering checklist:** edge-critical parts (USB, connectors, button,
  antenna, battery) at the correct edge, opening **outward**? decaps ≤2 mm from
  their IC pin? sensors that must share an axis placed with identical rotation?
  motors/noisy power partitioned away from quiet logic?
- **Automation opportunities:** region plan → demand-sized courtyards →
  spiral-hug decap placement → relaxation → surgical re-place of residual
  violators (do **not** re-tune relaxation params; it oscillates).
- **Human review:** **client sign-off** — placement is judged by usability, not by
  a metric. A DRC-clean board that can't be plugged in is a FAIL.
- **Exit criteria:** 0 spacing violations (real geometry); practical layout
  approved; refdes silk 0 overlaps.

> Origin lesson: the first placement was rejected for “looking autorouted.” The
> client judges by *can I assemble and use this*, not by wirelength. Edge parts
> open outward; sensors share an axis; put nothing over wrong.

---

## Phase 7 — Routing Plan

- **Objective:** a DRC-classed, ordered, feasibility-scored routing plan — before
  any copper is drawn.
- **Inputs:** frozen placement; netlist with per-net current; the rules template.
- **Outputs:** `design_rules.json` (net classes) + `route_sequence.json` (ordered
  phases) + `trace_width_table.json` + a congestion prediction.
- **Validation:** **0 nets on the `default` class**; every class rule matches a
  live net name; feasibility scored (proceed only above threshold).
- **Deliverables:** the three JSON rulebooks + a routing strategy doc + a frozen
  input snapshot.
- **Engineering checklist:** planes assigned (solid GND; power plane for the heavy
  rail)? analog-ground island single-tied? diff pairs specced (width/gap/Z)?
  high-current pads have via-farm budgets? λ/20 stitch frequency = edge-rate knee,
  not clock? asymmetric-plane return paths handled (a via that changes reference
  plane needs a bypass cap, not a ground stitch)?
- **Automation opportunities:** the entire plan — a swarm of analysts (stackup,
  power, SI/PI, ground, DRC, congestion) → orchestrated into the rulebooks.
- **Human review:** engineer signs the plan; client signs any copper-independent
  part questions the plan surfaces.
- **Exit criteria:** 0 unclassed nets; feasibility ≥ threshold; plan frozen.

---

## Phase 8 — Routing Execution

- **Objective:** a fully routed board, DRC-clean against its own manufacturing
  ruleset.
- **Inputs:** the routing plan; the applied ruleset in the EDA tool.
- **Outputs:** routed copper: planes → criticals → constrained autoroute → power
  pours → **GND pour + stitch LAST**.
- **Validation:** 0 unrouted; DRC-clean against the *board's own* ruleset in the
  *board's own* tool (never cross tools — that is the phantom-DRC trap).
- **Deliverables:** the routed board file (committed) + a routing report.
- **Engineering checklist:** GND pour is the final pass (earlier strands opens)?
  stitching collision-checked and excluding the analog island? high-current pads
  reach their pour through via arrays? no via on the USB diff pair?
- **Automation opportunities:** partial — auto-route the bulk; **the last mile
  (fine-pitch escapes, pours) is interactive** in every tool tried. Generate a
  precise plan so the manual time is short.
- **Human review:** **explicit go-ahead** before drawing copper (a live,
  semi-permanent write); engineer signs the DRC-clean verdict.
- **Exit criteria:** 0 unrouted; DRC = 0 errors vs the correct ruleset; board
  committed to git.

---

## Phase 9 — DRC / DFM / Manufacturing Handoff

- **Objective:** a fabricatable, committed manufacturing package.
- **Inputs:** the routed, DRC-clean board.
- **Outputs:** gerbers (incl. inner layers), drill, CPL (pick-and-place), BOM,
  assembly renders, a DFM report.
- **Validation:** fab DFM check passes (loginless DFM portals can be automated);
  import fidelity verified if migrating tools (0 dropped footprints, sub-µm
  position residual).
- **Deliverables:** a `manufacturing/` folder + a zipped package, **all committed
  to git**.
- **Engineering checklist:** mounting holes present (they may not survive a
  tool-to-tool export)? silk legible? every layer exported? BOM matches the
  placed parts?
- **Automation opportunities:** gerber/drill/CPL export; automated DFM upload;
  BOM/CPL cross-check against the placement.
- **Human review:** engineer signs the DFM report; **the human places the fab
  order** (irreversible, external, spends money — never automated).
- **Exit criteria:** DFM pass; complete package **committed** (uncommitted =
  doesn't exist); order placed by a human.

---

## The gate summary

| Phase | The one thing that must be true to leave |
|---|---|
| 0 | No unquantified requirement, no unaddressed conflict |
| 1 | Size & layer count justified by density & current math |
| 2 | Every part datasheet-verified & sourced |
| 3 | The two source docs agree net-for-net |
| 4 | Every section placed & wired, 0 unmatched pins |
| 5 | Reconstructed netlist == source docs, 0 shorts |
| 6 | 0 spacing violations (real geometry) + practical + approved |
| 7 | 0 unclassed nets, feasibility ≥ threshold |
| 8 | 0 unrouted, DRC-clean vs correct ruleset, **committed** |
| 9 | DFM pass, package **committed**, order by a human |

Two words appear twice in that table on purpose: **committed**. The geometry is
disposable *only if* the knowledge is safe — and once a board is finished, the
board file becomes knowledge worth protecting. Commit it the moment it exists.
