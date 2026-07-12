# 14 · Contributing — for Humans and AI Agents

AXON is meant to be used by both humans and AI agents, and to grow as each new
board teaches new lessons. This guide covers both audiences.

---

## For AI agents picking up a project

1. **Read the operating manual first:** [`../CLAUDE.md`](../CLAUDE.md) →
   [`01_METHODOLOGY.md`](01_METHODOLOGY.md) → [`04_HUMAN_IN_THE_LOOP.md`](04_HUMAN_IN_THE_LOOP.md).
   Adopt both personas (Principle 5). You are a senior SW *and* senior HW engineer.
2. **Establish ground truth before acting.** Read the source-of-truth docs and the
   `⭐⭐ READ FIRST` memory. Treat any prior-session summary as **stale-by-default**
   — verify file paths, net names, and values against git/live state before you act
   on them.
3. **Find the frontier.** The status ledger and the top `⭐⭐ ACTIVE` memories tell
   you the current phase and next action.
4. **Run the loop:** generate ONE unit → senior review (`PASS/CONDITIONAL/FAIL`) →
   fix → next. Never generate the whole board and review at the end.
5. **Respect the autonomy tiers.** Execute replayable work at full speed; stop for a
   go-ahead only on live writes and phase transitions; never place a fab order.
6. **Verify against reality, never the tool's model.** Re-read after every mutation;
   run DRC with the correct ruleset.
7. **Record what you learn.** New gotcha → a `reference`/`feedback` memory + a
   `Heuristic → Why → Instance → Validation → Prevention` entry in the learning KB.
   New decision → a decision-based status update (not an artifact path).
8. **Commit geometry the moment it exists.** Uncommitted = gone.

---

## For human engineers

- You own the **source of truth** (build sheet, net dictionary) and the **sign-offs**
  (client/cost/BOM decisions, DRC before manufacturing, the fab order).
- You run the **Tier-4 manual steps** (interactive routing, Annotate, Check Nets)
  and paste results back so the AI can verify against them.
- You are the **veto on the electrical unknown** — if the HW-engineer persona's
  verdict feels wrong, it's a conversation, not an override.
- Keep the client in the loop on anything that changes cost, size, or usability.

---

## Contributing to the framework itself

**What a good contribution looks like:**

- A new **template** (a `.template.json`/`.md`) generalized from a real board, with
  the SPECIFIC vs GENERAL fields marked.
- A new **KG node** in [`03_KNOWLEDGE_GRAPH.md`](03_KNOWLEDGE_GRAPH.md): stated as a
  reusable rule first, with the instance as evidence, and an auto-checkable
  validation.
- A new **bottleneck + solution** in [`05_BOTTLENECKS.md`](05_BOTTLENECKS.md) — a real
  pain point, its root cause, and the reusable fix.
- A **tool-integration** entry (a new EDA tool's channel + tested-signatures table)
  following the shape in [`06`](06_EASYEDA_INTEGRATION.md).

**Rules:**

1. **Every claim traces to a real artifact, failure, or code path.** No aspirational
   heuristics — if it wasn't earned, it isn't a lesson.
2. **State the reusable rule, not the anecdote.** "Route thin first, pour last" — not
   "on the Light Dome board we poured last." The instance is evidence *under* the
   rule.
3. **Mark SPECIFIC vs GENERAL** in every template so the next person knows what to
   swap.
4. **Prefer updating over adding.** If a doc already covers the topic, extend it. The
   value of this framework is inversely proportional to its duplication.
5. **Keep files focused** (one concern each) and **under ~350 lines** of dense
   markdown.
6. **Honesty over polish.** A recorded failure is worth more than a success story.
   [`13_LESSONS_LEARNED.md`](13_LESSONS_LEARNED.md) is the model.

---

## The style of the framework

Dense, quantified, honest, cross-linked. Verdicts not vibes. Numbers not
adjectives ("T_j = 166 °C", not "runs hot"). Every doc links to its neighbours so
the reader can traverse the graph. If your contribution reads like marketing, it's
in the wrong repo.
