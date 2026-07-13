# 13 · Lessons Learned — The Honest Ledger

This is the audit's most valuable page: what actually happened, including the
failures, told straight. The origin project's own governance was, at points,
*wrong* — and that wrongness is recorded here as a finding, not hidden. A framework
built on a sanitized history teaches nothing.

---

## What succeeded (and the transferable reason)

**W1 · Promote a proven board to satisfy a new constraint.**
Going from a working 0-unrouted 2-layer board to 4-layer for ampacity by *adding*
planes + collision-checked stitching — not re-routing — worked where from-scratch
4-layer never converged (1091 DRC). *Reason: preserve hard-won convergence; change
the minimum.* → P10.

**W2 · Rip-up-reroute the obstruction beats re-floorplanning.**
A dense cluster's open tail closed by ripping the *obstructing tracks*, not moving
parts (2 agents spent 30 min moving parts: 0 successful moves). *Reason: at high
density the problem is tracks, not placement.* → P11.

**W3 · Thin-route-first, pour-last.**
Route every net thin so all pads connect, then pour planes as reinforcement, GND
last. *Reason: a pour is capacity, not the primary connection; pouring early strands
opens.* → P12.

**W4 · `kicad-cli` + sibling `.kicad_pro` as the single DRC truth.**
The most important toolchain fix — it turned a phantom "0 DRC" into the real 1091
and made every later verdict trustworthy. *Reason: verify against reality with the
real ruleset.* → Principle 3.

**W5 · Headless CDP schematic verification.**
Reconstructing the netlist from wire coordinates through a logged-in profile made
the phase-5 gate cheap and repeatable. *Reason: a cheap gate before expensive work
pays for itself many times over.*

**W6 · Adversarial swarms find real bugs.**
9-agent validate→recover→verify swarms consistently found what single passes missed
(22 shorts, 2 wrong parts, 73 blank values) *and* filtered plausible-but-wrong
findings. *Reason: breadth + independent refutation.* → P7.

**W7 · PADS export for EDA→KiCad migration.**
PADS export carries nets intact; Altium export is unusable ASCII. *Reason: pick the
interchange format that survives the round-trip; verify import fidelity.*

---

## What failed (and the root cause)

**F1 · Governance coupled to artifact paths.** *The most expensive mistake.*
Status rows hard-coded geometry file paths as proof-of-progress; when files were
deleted the ledger asserted a finished board that didn't exist. *Root cause:
confusing the disposable (geometry) with the durable (knowledge).* → Principle 1,
B1.

**F2 · Three delivered boards, two lost forever.**
`kicad/`, `build/`, `lab/` were never git-tracked; permanently unrecoverable after a
pivot. *Root cause: uncommitted geometry + no "commit the artifact" gate.* → B2.

**F3 · Routing started over a schematic with 22 shorts.**
Multiple full layout iterations discarded because the *source* underneath was wrong.
*Root cause: no phase-5 gate the first time — "place nothing over wrong" violated.*
→ Principle 2.

**F4 · From-scratch dense 4-layer never converged.**
A small outline packed to ~46% density (~120 parts) → 1091 DRC / 40 unrouted,
autorouter timing out. *Root cause: density above the autoroutable threshold; the
spec size was infeasible.* → KG-D1.

**F5 · Blind via-per-pad → 250–815 shorts.**
Adding a stitch via at every power pad without collision-checking. *Root cause: a
mutation applied without checking the geometry it lands in.* → KG-L4.

**F6 · Pour-first fragmentation.**
Pouring before routing left signal channels unusable. *Root cause: wrong phase
order.* → KG-L1.

**F7 · Phantom DRC.**
A bare board file with no ruleset sidecar, and an internal check weaker than real
DRC, reported clean while 1091 violations existed. *Root cause: trusting the tool's
own weak self-check.* → B6.

**F8 · ~$300 learning the interactive-routing wall.**
Long agent sessions trying to script pours/routing that the API simply cannot do.
*Root cause: fighting a hard tool limit instead of mapping it and routing around
it.* → B3, Principle 7.

**F9 · Wrong-value passives from fuzzy search.**
A 12 pF cap and a 2.2 µH inductor placed into µF slots via a bad LCSC ID. *Root
cause: accepting a search result without decoding the manufacturer ID.* → KG-T6.

**F10 · The two-week pivot with no board progress.**
Correctly stopping PCB to re-verify the schematic (finding 2 criticals), then
re-climbing all the way back — cost weeks. *Root cause: the schematic gate should
have been the phase-5 checkpoint the first time; doing it late is expensive even
when the decision is right.* → F3.

---

## The tradeoffs made (and how to present them honestly)

**T1 · Size for routability.** The spec size didn't route; a larger board did. The
honest framing: state it up front as a *constrained optimization* — "a clean,
working, manufacturable board at the larger size beats a broken board at the spec
size" — not as a late failure. → KG-D6.

**T2 · 2-layer solid-GND vs zero-unrouted.** You can't have both on a dense net
list. The chosen relaxation (via-stitched GND pour on both layers) is the right
trade; pretending you can have a perfect plane *and* full routing on 2-layer is the
error. → KG-L2.

**T3 · Manufacturable-but-imperfect DRC residue.** A handful of starved thermals or
sub-0.13 mm fine-pitch grazes that the fab *will* build are acceptable to ship if
named and understood — but they must be *named*, not silently passed. → P8.

---

## The recovery-baseline discrepancy (a case study in F1)

At one point a project's origin `CLAUDE.md` / `README` claimed, variously, several
different board sizes and "delivered" boards — while the **live board was a
different size and layer count, with a different latch IC, a swapped IMU, and a
different ToF part** than the source docs described. A recovery swarm reconstructed
true state into a pinned "READ FIRST" baseline listing exactly which rows to distrust.

The lesson is not "someone was sloppy." It is **structural**: a ledger that
references volatile artifacts *will* drift, because artifacts change faster than
prose gets updated. PCB Flow's fix (decision-based ledger + recovery-baseline pattern +
commit-immediately) removes the class of failure, not the instance.

---

## If you read only one page of this framework

Read this one, then Principle 1. Almost every failure above is the same failure —
**confusing the durable thing with the disposable thing** — and almost every success
is the same success — **verifying against reality with a cheap, honest check before
committing to expensive work.** Internalize those two and you have the framework.
