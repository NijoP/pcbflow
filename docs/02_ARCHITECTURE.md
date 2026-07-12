# 02 · System Architecture

AXON is a five-layer architecture. Data flows **down** (knowledge compiles into
geometry) and verdicts flow **up** (reality gates what's allowed to proceed).
Each layer has one job and a clean contract with its neighbours.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  5. GOVERNANCE & MEMORY LAYER                                              │
│     CLAUDE.md status ledger · typed memory files · session resume         │
│     "what is true, what to trust, what to do next" — decisions not paths   │
└──────────────────────────────────────────────────────────────────────────┘
        ▲ verdicts, state, "distrust row X"          │ policy, next-action
┌──────────────────────────────────────────────────────────────────────────┐
│  4. VERIFICATION LAYER                                                     │
│     real-geometry audit · reconstructed netlist · DRC ground truth        │
│     emits PASS / CONDITIONAL / FAIL — the only thing that unlocks a phase  │
└──────────────────────────────────────────────────────────────────────────┘
        ▲ real state read back                       │ gate
┌──────────────────────────────────────────────────────────────────────────┐
│  3. GEOMETRY LAYER  (the build artifact — regenerable)                     │
│     schematic · placement · routed copper · gerbers                       │
│     lives in the EDA tool (cloud) + exported files (committed)             │
└──────────────────────────────────────────────────────────────────────────┘
        ▲ readback (CDP / file)                       │ mutate (scripts / UI)
┌──────────────────────────────────────────────────────────────────────────┐
│  2. GENERATION LAYER  (deterministic + AI reasoning)                       │
│     section generators · placer · routing planner · rule applier          │
│     turns knowledge into geometry; the EDA tool is the "compiler backend"  │
└──────────────────────────────────────────────────────────────────────────┘
        ▲ reads templates + schemas                   │ reads source-of-truth
┌──────────────────────────────────────────────────────────────────────────┐
│  1. KNOWLEDGE LAYER  (the source code of the board — authored & protected)  │
│     build_sheet.md · net_connection.md · design_rules.json · trace table   │
│     requirements · constraint verdicts · BOM · datasheet notes             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Knowledge (the source of truth)

**Contract:** two human-readable documents plus a set of machine-readable JSON
rulebooks define the board completely. Everything below is derivable from them.

| Artifact | Role | Template |
|---|---|---|
| `build_sheet.md` | The **tick-sheet**: per-block, per-pin net assignments, passive values, build order, final checklist | [`templates/build_sheet.template.md`](../templates/build_sheet.template.md) |
| `net_connection.md` | The **net dictionary** + net-membership oracle (§ “every net → every connected pin”) | [`templates/net_connection.template.md`](../templates/net_connection.template.md) |
| `design_rules.json` | Net classes, per-class widths/clearances, diff pairs, keepouts | [`templates/design_rules.template.json`](../templates/design_rules.template.json) |
| `trace_width_table.json` | Per-net IPC-2221 current → width mapping | [`templates/trace_width_table.template.json`](../templates/trace_width_table.template.json) |

**Invariant:** the two docs must agree net-for-net; on conflict, the net
dictionary wins. This dual-doc + “dictionary wins” pattern is board-agnostic and
is the whole reason the schematic generator can be dumb and deterministic.

---

## Layer 2 — Generation (knowledge → geometry)

**Contract:** every generator reads Layer 1, emits geometry into Layer 3, and is
**re-runnable** — running it twice from the same source produces the same board.
Generators are a mix of deterministic scripts and AI reasoning:

- **Section generators** — one script per functional block. A shared, board-agnostic
  *engine* (part search, passive picking, wire-by-net-name, stub direction) plus a
  per-block *CONFIG* (PARTS + PASSIVES). See [`06_EASYEDA_INTEGRATION.md`](06_EASYEDA_INTEGRATION.md).
- **Placer** — region plan + demand-sized courtyards + spiral-hug decap placement +
  relaxation, scored against a routing-congestion prediction.
- **Routing planner** — turns the netlist + rules into an ordered, DRC-gated
  `route_sequence.json`.
- **Rule applier** — writes `design_rules.json` into the EDA tool's DRC config.

The key architectural idea: **the EDA tool is the compiler backend.** The
generation layer is a front-end that emits “instructions” (scripts, or a plan a
human executes) which the backend turns into copper. When the backend's API is
too weak (pours, routing), the generation layer emits a *plan for a human* instead
of a script — same contract, different executor.

---

## Layer 3 — Geometry (the build artifact)

**Contract:** this layer is **disposable and regenerable**. It lives in two
places: the live cloud EDA project (authoritative while editing) and exported
files committed to git (the recovery checkpoint). It is never the source of
truth for *intent* — only for *current realized state*.

Two hard rules earned in blood:
1. **Commit every manufacturing output immediately.** Uncommitted geometry is
   one pivot away from gone. (Origin project lost two finished boards this way.)
2. **The live cloud board is ground truth for realized state; JSON snapshots and
   models are working copies that may be hours stale.** Always read back.

---

## Layer 4 — Verification (the gate)

**Contract:** verification reads *real* geometry (Layer 3), compares against
*intent* (Layer 1), and emits a verdict that Layer 5 uses to unlock the next
phase. It never trusts a generator's self-report.

Three ground-truth mechanisms, each matched to its phase:
- **Reconstructed netlist** (schematic) — pin→net rebuilt from wire coordinates,
  because the EDA tool's own netlist API hangs headless. Diffed against
  `net_connection.md`.
- **Real-geometry spacing audit** (placement) — pad-to-pad gaps from actual pad
  polygons, connector inflation applied, on real component rotation.
- **DRC ground truth** (routing) — run the DRC that matches the board's authoring
  tool, with the correct ruleset loaded. Never cross tools.

Full detail: [`09_VALIDATION.md`](09_VALIDATION.md).

---

## Layer 5 — Governance & Memory (the brain across time)

**Contract:** this layer holds *what is true, what to trust, and what to do next*
— across session boundaries, in terms of **decisions**, not artifact paths.

- **Status ledger** (`CLAUDE.md`) — one row per subsystem/phase, each a dated
  verdict. References knowledge, not geometry paths.
- **Typed memory** — one fact per file (`project` / `reference` / `feedback` /
  `user`), a one-line index, a `[[wikilink]]` graph, explicit staleness handling.
- **The recovery-baseline pattern** — when the ledger and reality diverge, a
  pinned “READ FIRST” memory declares which rows to distrust rather than silently
  rewriting history.

Full detail: [`10_MEMORY_AND_STATE.md`](10_MEMORY_AND_STATE.md).

---

## Why five layers, and why in this order

Each boundary is a place where the origin project got burned, and the layering is
the fix:

| Boundary | The failure it prevents |
|---|---|
| Knowledge ↔ Generation | Hand-drawing schematics that can't be regenerated when the spec changes |
| Generation ↔ Geometry | Treating the EDA tool as the source; losing intent when files are lost |
| Geometry ↔ Verification | Trusting the tool's self-report (“0 unrouted”) over real DRC |
| Verification ↔ Governance | Advancing on vibes instead of a falsifiable, dated verdict |
| Governance coupling to paths | Status claiming “SHIP” while the file it points to is gone |

The architecture is, quite literally, the shape of the mistakes made once and
never again.
