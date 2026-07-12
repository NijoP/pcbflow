# 08 · Prompt & Agent Strategy

How the AI is organized to think — the personas, the swarm patterns, the
verdict-gating, and the token discipline. This is the "how AI collaborates with
itself and the engineer" layer.

---

## The dual persona (always on, in tension)

Every task is held in two minds at once (Principle 5):

- **Senior software engineer** — clean automation, correct API contracts,
  deterministic scripts, token discipline, tooling.
- **Senior hardware / PCB engineer** — net-by-net rigor, quantified verdicts, honest
  FAIL calls, refusal to proceed over an electrical unknown.

They are an internal peer review. The HW persona has a **veto**: it blocks forward
motion on an electrical fault the SW persona would automate straight past. Encode
this in the system prompt (see [`CLAUDE.md`](../CLAUDE.md)) so it's always active,
not summoned.

**Register:** firm, quantified, direct. "T_j = 166 °C at 5 A — this FET dies at
sustained stall; parallel two or soft-start" — not "you may want to consider the
thermal margin." Verdicts are `PASS / CONDITIONAL / FAIL`, never "looks okay."

---

## When to swarm vs. when to go solo

| Situation | Approach |
|---|---|
| Planning / audit / review (breadth + adversarial coverage) | **Swarm** — parallel agents, one lens each, orchestrated |
| Execution (a schematic edit, a placement run, a DRC read) | **Solo** — targeted, cheap, small context |
| A single fact lookup | **Solo, direct** — don't spin up an agent to read one file |

Swarms cost tokens; reserve them for phases where breadth and independent
perspectives genuinely raise quality. Execution is a scalpel, not a committee.

---

## Swarm patterns that worked

**Pattern A — Dimensioned review (find → verify).**
Fan out N reviewers, each owning one dimension (one subsystem, or one lens:
correctness / SI / manufacturability). Each returns a structured finding list. Then
**adversarially verify** each finding with an independent skeptic before it's
accepted — kill findings a majority can refute. This is how 22 real shorts were
found *and* how plausible-but-wrong findings were filtered out.

**Pattern B — Orchestrated planning swarm.**
A set of specialist analysts (stackup, power distribution, ground integrity,
SI/PI, DRC/manufacturability, congestion, math-optimizer) each produce a partial;
an **orchestrator** merges them, resolves conflicts against a shared knowledge
graph, scores competing proposals, and issues one verdict + the machine-readable
rulebooks. Used to produce every routing plan.

**Pattern C — Validate → recover → verify.**
Parallel validators find defects → a recovery agent fixes them → independent
verifiers confirm the fix really landed. (Origin: 6 validate → 1 recover → 2
verify. The verify step matters — an early "fixed" claim was wrong; the verifiers
caught it.)

**Pattern D — Recovery / reconciliation swarm.**
Read-only auditors reconstruct *true* state when the ledger has drifted, and emit a
"trust this / distrust that" baseline. Produced the recovery document that
corrected a status table describing boards that no longer existed.

**Pattern E — Continuous-learning agent.**
One agent's job is to write discovered lessons to the learning DB
(`routing_learning_db.md`) in the `Heuristic → Why → Instance → Validation →
Prevention` format, and append them to the relevant agent definitions so the next
invocation inherits them. Learning compounds instead of evaporating.

---

## Verdict-gating (how swarms move the project)

Every swarm ends in a **gating verdict**, and no phase transition happens without
one:

```
analysis  →  verdict (PASS / CONDITIONAL-with-fixes / FAIL / score)  →  fix  →  re-verify  →  proceed
```

- Schematic section: only `PASS` advances.
- Feasibility: a **score** (e.g. 74/100) with a threshold — "good enough" is a
  number, and CONDITIONAL carries named conditions that must be *armed* before
  execution.
- Placement: client rejection triggers a full redo; only approval unlocks routing.

The verdict is the unit of progress (Principle 6). A swarm that produces prose but
no verdict has not moved the project.

---

## Prompt-authoring rules (for the tasks you hand agents)

1. **State the role and the two personas** explicitly.
2. **Point at the source of truth** (`build_sheet.md`, `net_connection.md`, the
   relevant docs/memories) and say *reuse it, don't re-derive it* — re-deriving
   settled analysis wastes budget and risks diverging from a closed verdict.
3. **Demand structured output** — a schema, a finding list, a verdict — not an
   essay. Downstream code consumes it.
4. **Scope hard.** "SCHEMATIC ONLY — PCB place/route/DRC are a later phase" prevents
   scope creep and mis-bundled blockers.
5. **Ask for firm calls with written justification**, not options. The user's
   documented preference: execute the decision, surface only genuine technical
   blockers — never preference questions.
6. **Give the failure library.** Hand the agent the relevant KG-nodes
   ([`03_KNOWLEDGE_GRAPH.md`](03_KNOWLEDGE_GRAPH.md)) so it doesn't re-walk a known
   trap.

---

## Model-tier discipline (cost is a design constraint)

- **Cheap/fast tier** — extraction, search, readback, bulk mechanical edits.
- **Top tier** — architecture decisions, adversarial verification, the orchestrator,
  anything where being wrong is expensive.

A long Opus-only swarm is a real bill (one dead-end cost ~$300). Match the tier to
the task; reserve the expensive reasoning for where it changes the answer.

---

## The token-discipline loop

The "one unit at a time" loop ([`01_METHODOLOGY.md`](01_METHODOLOGY.md)) is also the
token strategy: small blast radius, small context, cheap re-review. Combined with
"reuse, don't re-derive" and externalized memory
([`10_MEMORY_AND_STATE.md`](10_MEMORY_AND_STATE.md)), it keeps a multi-month project
inside a sane budget without losing state at session boundaries.
