# 12 · Design Patterns

The recurring shapes across the project, named so they can be reached for
deliberately. A pattern is a solution shape that showed up more than once and
generalizes. Grouped by where they apply.

---

## Generation patterns

**P1 · Engine + CONFIG.**
Separate a fixed, board-agnostic *engine* (the how) from a per-instance *CONFIG*
(the what). The section generator is an engine + PARTS/PASSIVES data; the placer is
an engine + zone/anchor data; the rule applier is an engine + net-class data. New
board = new data, same engine. → S1, S4, S5.

**P2 · Connect by name, not by geometry.**
Identity travels by a global name (net name), so physical placement of the
connecting artifact is free. Consequence: use *minimal* stubs (long ones collide).
The general lesson — *let a global namespace carry identity so local geometry stays
cheap* — recurs anywhere you're tempted to wire things by position. → KG-T5.

**P3 · Probe before assume; record the result.**
For any undocumented API, test **one** guarded call, never a loop, and write the
outcome into a tested-signatures table. Never re-probe a known result. This turns a
fragile, hang-prone surface into a stable, documented one. → [`06`](06_EASYEDA_INTEGRATION.md).

**P4 · Emit a plan when you can't emit a script.**
When the backend API can't do the thing (pours, routing), the generation layer's
output is a *human-executable plan* with the same rigor as code — literal polygons,
coordinates, ordered steps. Same contract (knowledge → instructions), different
executor. → Principle 7, `route_sequence.json`.

---

## Validation patterns

**P5 · Read reality back after every mutation.**
Never trust the in-memory model after a write. Re-dump in a fresh eval; compute from
real geometry; run DRC with the real ruleset. The single most repeated corrective in
the project. → Principle 3, [`09`](09_VALIDATION.md).

**P6 · Verdict as a gate.**
Work advances on a falsifiable, dated `PASS / CONDITIONAL / FAIL` (or a scored
threshold), never on "done." A CONDITIONAL carries numbered conditions that must be
*armed* before the next phase. → Principle 6.

**P7 · Adversarial verify.**
For every finding, spawn an independent skeptic prompted to *refute* it; keep only
what survives. Prevents plausible-but-wrong findings from propagating. → [`08 §Pattern A`](08_PROMPT_AND_AGENT_STRATEGY.md).

**P8 · Whitelist explicitly, never silently.**
A legitimate exception (a by-design pad gap, a single-pad net's unrouted flag) is
*named* in the verdict, not filtered out quietly. Silent truncation reads as "all
clean." → [`09 §R4`](09_VALIDATION.md).

---

## Placement / routing patterns

**P9 · Surgical re-place, not global re-tune.**
When an iterative optimizer oscillates (relaxation cycling 3→6→3→9), stop tuning
params and instead *re-place the few residual violators* directly. Converge by
fixing the exceptions, not by nudging the whole system. → S4, KG (placement).

**P10 · Promote, don't rebuild.**
To satisfy a new constraint (ampacity → 4 layers), *promote* a working artifact (add
planes + stitching to a routed 2-layer board) rather than regenerate from scratch.
Preserves the hard-won 0-unrouted state. → KG-L3.

**P11 · Rip-up the obstruction, don't move the part.**
A dense cluster's open nets are a *track* problem. Reroute the obstructing tracks;
don't relayout (every nudge trades one open for several shorts). → KG-L5.

**P12 · Hardest-first, pour-last ordering.**
Route the constrained nets first (diff pairs, fast SPI, dense escapes) while there's
freedom; pour ground *last* (pouring early strands opens). A general scheduling
insight: *spend your freedom on the hardest thing while you still have it.* → KG-L1,
S6.

---

## Governance / process patterns

**P13 · Decision-based ledger.**
Status references decisions and knowledge, never volatile artifact paths. → Principle
1, [`10`](10_MEMORY_AND_STATE.md).

**P14 · Recovery baseline.**
When the ledger drifts from reality, pin a "READ FIRST" correction that says *trust
these, distrust those* — a correction layer, not a rewrite. → [`10`](10_MEMORY_AND_STATE.md).

**P15 · One fact per file, typed, dated, linked.**
Externalized memory as a graph of single-fact files with staleness handling. → [`10`](10_MEMORY_AND_STATE.md).

**P16 · One unit at a time.**
Generate → review → fix → next, per section/region/phase. Small blast radius, cheap
re-review, bounded context. Both a quality and a token-cost pattern. → [`01`](01_METHODOLOGY.md).

**P17 · Reuse, don't re-derive.**
Point agents at settled analysis and forbid re-deriving it. Protects budget and
prevents divergence from closed verdicts. → [`08`](08_PROMPT_AND_AGENT_STRATEGY.md).

**P18 · Autonomy by reversibility.**
Full autonomy on replayable work; a go-ahead gate on live writes; a human on
irreversible acts. → Principle 4, [`04`](04_HUMAN_IN_THE_LOOP.md).

---

## The pattern behind the patterns

Most of these are one meta-pattern in different clothes: **separate the durable from
the disposable, and put a cheap honest check on the seam.** Engine vs config (P1),
name vs geometry (P2), knowledge vs artifact (P13), reality vs model (P5), verdict
vs vibe (P6), replayable vs irreversible (P18). Learn to see the seam and the right
pattern is usually obvious.
