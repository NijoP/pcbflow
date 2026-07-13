# Contributing to PCB Flow

PCB Flow is used by **both humans and AI agents**, and it's designed to get better
with every board that runs through it. This guide covers both audiences.

---

## The three ways to contribute

1. **Improve the process** — refine a phase in [`workflow/`](workflow/). A better
   gate or checklist applies to every future project automatically.
2. **Improve a tool** — fix or extend an engine in [`automation/`](automation/).
   Fix it once; every project benefits.
3. **Grow the knowledge** — add a lesson to
   [`knowledge/learning-db.md`](knowledge/learning-db.md), promote a repeated
   lesson into [`knowledge/knowledge-graph.md`](knowledge/knowledge-graph.md) or
   [`knowledge/design-standards.md`](knowledge/design-standards.md), or add a new
   agent role in [`agents/`](agents/).

Board-specific work goes in [`projects/<board>/`](projects/) — **never** in the
framework layers. The framework stays board-agnostic; that's what makes it reusable.

---

## For AI agents

1. **Read before acting:** the current phase file in `workflow/`, the project
   manifest (`project.yaml`), and the relevant `knowledge/` entries. Treat any
   prior-session note as **stale-by-default** — verify file paths, net names, and
   values against the live/committed state first.
2. **Adopt both personas** — senior software engineer *and* senior hardware/PCB
   engineer (the HW persona vetoes any electrical unknown). See [`CLAUDE.md`](CLAUDE.md).
3. **Emit a structured verdict** — `PASS / CONDITIONAL(numbered) / FAIL`, dated,
   naming the ruleset/board it was checked against. Not prose.
4. **Respect the autonomy tiers** — run replayable work at full speed; stop for a
   go-ahead on live writes and phase transitions; never place a fab order. See
   [`docs/04_HUMAN_IN_THE_LOOP.md`](docs/04_HUMAN_IN_THE_LOOP.md).
5. **Verify against reality**, never the tool's self-report (re-read after every
   mutation; run DRC with the correct ruleset in the correct tool).
6. **Write back what you learn** to `knowledge/learning-db.md` in the standard
   five-field format.

---

## For human engineers

- You own the **source of truth** (build sheet, net dictionary) and the
  **sign-offs**: client/cost/BOM calls, placement approval, go-ahead to route, DRC
  before manufacturing, and **placing the fab order** (never the AI).
- You run the few genuinely-manual EDA steps and paste results back so the AI can
  verify against them.
- If the HW-engineer persona's verdict feels wrong, that's a conversation, not an
  override.

---

## Rules for framework contributions

1. **Every claim traces to a real artifact, failure, or code path.** No
   aspirational heuristics.
2. **State the reusable rule, not the anecdote.** The project instance is evidence
   *under* the rule.
3. **Mark SPECIFIC vs GENERAL** in templates and tools so the next person knows
   what to swap.
4. **Prefer updating over adding.** Value is inversely proportional to duplication.
5. **Keep files focused** (one concern) and **dense** — verdicts not vibes, numbers
   not adjectives.
6. **Honesty over polish.** A recorded failure is worth more than a success story.

---

## Commit style

Conventional commits (`feat:`, `docs:`, `fix:`, `refactor:`, `chore:`). Describe
the *engineering* change, not just the file change. Commit board geometry the
moment it exists — an uncommitted board is one mistake from gone.
