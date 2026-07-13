# 00 · Philosophy & First Principles

This is the *why* behind every structural choice in Tracewright. If you understand this
page, the rest of the framework is obvious. If you skip it, you will eventually
re-derive it the expensive way — the origin project did, repeatedly.

---

## Principle 1 — Knowledge is the source; geometry is the build artifact

A PCB project accumulates two very different kinds of thing:

- **Knowledge** — requirements, the net list, why a part was chosen, the trace-width
  math, the DRC ruleset, the decision that this is a 4-layer board. This is
  *authored*, *reviewed*, *versioned*, and *hard to reproduce*.
- **Geometry** — the schematic, the placement coordinates, the routed copper, the
  gerbers. This is *generated*, *mechanical*, and — if the knowledge is intact —
  *reproducible on demand*.

Treat them accordingly. **Version and protect the knowledge. Regenerate the
geometry.** The single most damaging failure in the origin project was inverting
this: the governance file (`CLAUDE.md`) hard-coded geometry file paths as
proof-of-progress (`kicad/…/board_v7.kicad_pcb → PRODUCTION-READY: SHIP`). When
those files were deleted during a pivot, the knowledge layer went on asserting a
finished board that no longer existed. Three “delivered” boards; two lost forever
because they were never committed. See [`13_LESSONS_LEARNED.md`](13_LESSONS_LEARNED.md).

**Rule:** governance and status must reference *decisions and knowledge*, never
volatile artifact paths. A status line says “4-layer, In2=VSYS plane, 10-class
ruleset frozen” — not “see board_v7.kicad_pcb.”

---

## Principle 2 — Place nothing over wrong

Never build stage N+1 on an unverified stage N. Do not place parts over a
schematic with a short. Do not route over a placement that can't be assembled.
Do not pour ground over an un-closed routing.

The origin project violated this and paid for it: it started routing on a
schematic that had **22 pin shorts**, and it discarded multiple full layout
iterations because the *schematic underneath them* was wrong. Weeks of geometry,
thrown away, because the source was never gated. The corrective was structural:
**every phase has an exit gate, and a failing gate blocks forward motion.**

This is not bureaucracy. A cheap gate (a headless netlist diff, a pad-spacing
audit) that runs in seconds saves a layout that took hours.

---

## Principle 3 — Verify against reality, never against the tool's own model

Every automated tool maintains an internal model of the world, and that model
lies:

- EasyEDA's `getAll()` returns a **stale snapshot** right after you move parts.
- Pad-level `rotation` attributes stay stale after a component rotates.
- An autorouter reports “0 unrouted” while the *imported* board has 1091 real DRC
  violations.
- `kicad-cli` on a bare `.kicad_pcb` reports phantom-clean because the real rules
  live in the sibling `.kicad_pro`.
- A placer's own grid model shows 2 mm phantom overlaps that aren't in the copper.

**Ground truth is the real geometry and the real, correctly-configured DRC.**
Re-read the board after every mutation. Compute spacing from actual pad polygons.
Run DRC with the ruleset the board is actually manufactured against. Screenshot
and audit; never trust the placer's self-report. This principle has its own file:
[`09_VALIDATION.md`](09_VALIDATION.md).

---

## Principle 4 — Autonomy is bounded by reversibility, not by difficulty

The question “should the AI do this without asking?” is **not** answered by how
hard or how important the task is. It's answered by: **can it be replayed?**

- **Replayable** (analysis, planning, computation, doc generation, a schematic
  edit that can be re-derived from the source docs) → **fully autonomous.**
- **Live write to a shared cloud tool** (mutating the EDA board, applying a
  ruleset) → **needs a go-ahead**, because undo is expensive and state is shared.
- **Irreversible external act** (ordering the board, publishing to a fab) →
  **always human.**

This gives a clean, defensible line and — importantly — it means the AI runs at
full speed on the 90% of work that is safe to replay. The origin project's user
made this explicit as feedback: *“work autonomously, do not gate/ask, execute
the edits.”* The tiers are in [`04_HUMAN_IN_THE_LOOP.md`](04_HUMAN_IN_THE_LOOP.md).

---

## Principle 5 — Two personas, always on, in tension

Every decision passes through two minds held simultaneously:

- **The senior software engineer** — clean, structured automation; correct API
  contracts; deterministic scripts; good tooling; token discipline.
- **The senior hardware / PCB engineer** — rigorous net-by-net thinking,
  quantified verdicts (“T_j = 166 °C at 5 A — this FET dies”), honest
  FAIL calls, and a refusal to proceed over an electrical unknown.

They are a built-in peer review. The HW persona *blocks* forward motion on an
electrical fault the SW persona would happily automate past. Neither wins by
default. When they disagree, the disagreement is the signal.

---

## Principle 6 — The verdict is the unit of progress

Work does not advance by “I did some stuff.” It advances by a **verdict**:
`PASS`, `CONDITIONAL PASS` (with a numbered fix list), or `FAIL`. A verdict is
falsifiable, dated, and attached to an artifact. It is the currency the whole
methodology trades in. A phase is “done” when it has a PASS verdict, not when it
*feels* finished. Feasibility gets a **score** (e.g. 74/100) so “good enough to
proceed” is a number, not a vibe.

---

## Principle 7 — The hard wall is real; plan for it, don't fight it

Some steps genuinely cannot be automated with today's tools. In the origin
project the wall was **interactive routing**: EasyEDA's script API rejects every
copper-pour signature, its autorouter won't accept a scripted outline, and
fine-pitch escapes (0.5 mm USB-C fanout) defeat every maze router tried. Roughly
$300 was spent *learning* that you cannot brute-force past it.

The mature response is not to keep hitting the wall. It is to **generate a
maximally detailed plan that makes the human's unavoidable manual time short and
precise** — a `route_sequence.json` with literal pour polygons, via-farm
coordinates, and phase-by-phase instructions. Automate up to the wall; hand the
human a perfect map for the last mile. Know where your walls are
([`05_BOTTLENECKS.md`](05_BOTTLENECKS.md)) and design the workflow around them.

---

## Principle 8 — Cheap, honest, dated memory beats a perfect one

Context does not survive session boundaries. The answer is not a bigger context
window; it is **externalized, typed, dated, self-invalidating memory**:
one-fact-per-file, a one-line index, `[[wikilinks]]` for the graph, and an
explicit “trust this / distrust that” layer when the live state diverges from
what's written. A memory is a *point-in-time observation*, not live state — so
every recalled fact that names a file or a value must be re-verified before it's
acted on. [`10_MEMORY_AND_STATE.md`](10_MEMORY_AND_STATE.md).

---

## The through-line

All eight principles are the same instinct applied to different surfaces:
**separate the durable thing from the disposable thing, and gate the transition
between them with a cheap, honest check.** Knowledge vs geometry. Source vs build.
Reality vs model. Replayable vs irreversible. Verdict vs vibe. That instinct is
Tracewright.
