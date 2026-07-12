# 04 · Human-in-the-Loop — The Autonomy Ladder

The governing question is **not** “is this hard?” or “is this important?” It is:
**can this action be replayed if it's wrong?** Autonomy is bounded by
reversibility. That single axis produces a clean, defensible classification that
lets the AI run at full speed on the safe 90% and stop precisely where undo is
expensive.

```
  REPLAYABLE ───────────────────────────────────────────► IRREVERSIBLE
  (analysis, planning, computation,      (live cloud write,      (spend money,
   doc gen, re-derivable edits)           phase transition)       publish, order)
  ────────────────────────────────       ─────────────────       ──────────────
  FULLY AUTONOMOUS                        GO-AHEAD GATE            ALWAYS HUMAN
```

---

## Tier 1 — Fully autonomous (do it, don't ask)

The action is pure analysis or produces an artifact that can be regenerated from
the source of truth. Report results; don't request permission.

- Requirement analysis, architecture studies, feasibility scoring.
- BOM cost/sourcing research; datasheet verification.
- Placement **computation** (region plan, courtyard sizing, relaxation, scoring).
- Routing **planning** (rulebooks, sequence, congestion grid, feasibility).
- Netlist extraction and DRC *reading* via headless automation.
- Schematic **edits when scope is clearly stated** and the edit is re-derivable
  from the source docs (add a decap, fix a net, swap a part per a written decision).
- Wrong-part / short detection and its fix.
- All documentation, reports, and memory writes.

> Explicit user feedback in the origin project: *“work autonomously, do not
> gate/ask, execute the edits.”* Stopping to ask “should I proceed?” on a
> replayable task reads as stalling, not safety. Make firm engineering calls with
> written justification; surface only genuine **technical** blockers (e.g. no
> authenticated session), never preference questions.

---

## Tier 2 — Semi-autonomous (execute, then report for confirmation)

The AI produces a complete result but a human confirms before it becomes the
basis for the next phase. Used for proposals that gate downstream work.

- A **placement proposal** — generated in full, then reviewed before routing.
- A **routing plan** — produced and self-reviewed (findings triaged), then gated
  on a go-ahead before execution.
- A schematic **section script** — the AI writes it; the human runs it in the EDA
  tool and returns the log (generation autonomous, live write human-triggered).
- **Swarm verdicts** — the swarm delivers PASS/CONDITIONAL/FAIL; the human confirms
  before proceeding.

---

## Tier 3 — Human-approval-required (explicit go-ahead before acting)

A **live, semi-permanent write** to the shared cloud tool, or a **phase
transition**. State is shared and undo is expensive, so cross the line only on an
explicit go-ahead. The recurring phrase in the origin project: *“NEXT (needs
go-ahead).”*

- **Applying a DRC ruleset** to the live board (the one “optional live write”
  before routing).
- **Drawing copper** — starting routing.
- **Any phase transition** that mutates the live board (schematic→placement,
  placement→routing, plan→execution).

The rule: *if it can be replayed from source, Tier 1; if it's a live write to the
cloud tool, Tier 3.*

---

## Tier 4 — Manual engineering (human performs in the UI; cannot be automated)

Hard tool limits. The AI's job here is to make the manual step **short and
precisely guided**, not to attempt it. From the origin EDA tool:

- **Interactive routing** — the pour-create API rejects every signature; routing is
  UI-only.
- **Project-wide Annotate** — no scriptable equivalent; UI-only.
- **Check Nets / Update PCB** (schematic→PCB sync) — UI-only.
- **Fine-pitch hand-routing** — 0.5 mm escapes, chip flips; maze routers miss by
  ~0.1 mm.
- **Part/footprint swap on the PCB** — “Replace Part” is UI-only (schematic
  swap via delete-recreate-rewire *is* automatable).
- **Final decap fine-placement** — automation gets close; the last ≤2 mm is manual.

---

## Tier 5 — Client sign-offs (copper-independent release gates)

Business/UX/BOM decisions the engineer surfaces but does not own. Track them as
explicit open gates that block *release*, not *layout*:

- Cost/feature trades (fuel-gauge IC vs ADC; include/omit a break-out header).
- Final BOM part choices where alternates exist.
- Any spec relaxation (board size up for routability).
- Confirmation of the actual motor / mechanical parts (drives power sizing).

---

## Tier 6 — Safety-critical / never-automate

The AI may compute and recommend, but a human signs, and some acts are never
automated at all.

- **DRC sign-off before manufacturing** — a human confirms the clean verdict on the
  correct ruleset.
- **Power-path widths / plane sizing** — never draw a power trace narrower than the
  IPC-2221 minimum; a >~5 A path must be a plane.
- **Battery/polarity, protection topology** — visually verify before fab.
- **Analog-ground star-tie integrity** — never add island ties autonomously.
- **Placing the fab order** — irreversible, external, spends money. **Always
  human.** Automated *DFM checking* (loginless portals) is fine; *ordering* is not.

---

## The classification table (quick reference)

| Task | Tier | Why |
|---|---|---|
| Feasibility / architecture study | 1 | replayable analysis |
| BOM sourcing research | 1 | replayable |
| Placement computation | 1 | replayable; output is data |
| Routing plan authoring | 1 | replayable; output is data |
| Netlist / DRC *reading* | 1 | read-only |
| Schematic edit (scoped, re-derivable) | 1 | replayable from source |
| Placement *proposal* for approval | 2 | gates downstream |
| Section generator script | 2 | AI writes, human runs |
| Apply ruleset to live board | 3 | live cloud write |
| Start routing (draw copper) | 3 | live, semi-permanent |
| Interactive fine-pitch routing | 4 | tool limit |
| Project-wide Annotate | 4 | tool limit |
| Cost/feature/BOM choice | 5 | client's to make |
| Power-width / plane sizing | 6 | safety-critical |
| Place the fab order | 6 | irreversible, external |

**Design implication for the whole framework:** because Tier 4 (interactive
routing) is unavoidable, the framework's highest-value output at the boundary is
a *plan detailed enough that the human's manual time is minutes, not hours* —
literal pour polygons, via coordinates, phase-by-phase steps. Automate to the
wall; hand off a perfect map.
