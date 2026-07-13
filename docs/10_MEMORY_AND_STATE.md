# 10 · Memory & Cross-Session State

Context does not survive a session boundary, and a hardware project runs for months
across dozens of sessions. The answer is not a bigger context window — it is
**externalized, typed, dated, self-invalidating memory** plus a decision-based
status ledger. This is Layer 5 of the architecture.

---

## The memory system

**One fact per file.** A memory is a single `.md` file with YAML frontmatter:

```markdown
---
name: <kebab-slug matching the filename>
description: <one dense line — this is what a future session reads to judge relevance>
metadata:
  type: project | reference | feedback | user
---

<the fact. For feedback/project, follow with **Why:** and **How to apply:** lines.
Link related memories with [[their-name]].>
```

**Four types, each with a distinct lifetime:**

| Type | Holds | Lifetime |
|---|---|---|
| `project` | time-bound state: this board's placement, routing plan, swarm verdicts, feasibility | **decays** — age-warned, superseded by newer |
| `reference` | stable how-to: API recipes, DRC rules, migration pipelines | survives board pivots intact |
| `feedback` | how the AI should *work* — corrections & confirmed approaches, with the *why* | durable behavioral guidance |
| `user` | facts about the person/environment that would otherwise look like bugs | durable |

**The index.** `MEMORY.md` is one line per memory, loaded every session:

```
- [⭐⭐ ACTIVE: <headline>](file.md) — <150-char hook with the verdict>
```

Star priority is explicit: `⭐⭐ ACTIVE` (read first), `⭐ ACTIVE`, `⭐ PREF`,
`⭐ FEEDBACK`, unmarked (reference/historical). New entries prepend; stale ones sink.
Never put memory *content* in the index — one line, a pointer, a hook.

**The graph.** Memories link with `[[slug]]`. `project` nodes cite the `reference`
nodes (stable APIs) and predecessor `project` nodes (prior states) they depend on;
`feedback` nodes are cited but rarely cite. Acyclic by convention (no memory
references one that postdates it). Link liberally — a `[[slug]]` with no file yet
marks something worth writing.

---

## Staleness is built in, not bolted on

A recalled memory is a **point-in-time observation, not live state.** The harness
stamps each read with its age ("this memory is N days old"). The discipline:

- **If a memory names a file, function, value, or flag → verify it still exists
  before acting on it.** File paths rot; net names get renamed; parts get swapped.
- **When the live state and a memory diverge, the live state wins** — and you write
  a correction.
- **Update, don't duplicate.** A superseded plan's memory says "SUPERSEDED by
  [[newer]]"; you don't leave two competing plans. **Delete** memories proven wrong.

---

## The status ledger

The project's `CLAUDE.md` carries a **STATUS table** — one row per subsystem/phase,
each a dated verdict. It is the primary cross-session resume point. Read order for a
fresh session:

1. `MEMORY.md` index (starred first)
2. the `⭐⭐ READ FIRST` recovery/baseline memory, if one exists
3. the 1–2 most-recent `⭐⭐ ACTIVE` memories for the current frontier
4. `CLAUDE.md` body (personas, hard rules) — but treat old STATUS rows with the
   distrust the recovery memory assigns
5. the source-of-truth docs (`build_sheet.md` → `net_connection.md` → constraints)

---

## The one failure that shaped this whole layer

The origin project coupled its status ledger to **artifact paths**. A row said
"PRODUCTION-READY: SHIP → `board_v7.kicad_pcb`." That file was never committed and
was later deleted in a pivot. The ledger then asserted a finished board that did not
exist — and *kept* asserting it, session after session, because nothing checked.

Three fixes, now baked into Tracewright:

1. **Status references decisions, not paths.** "4-layer, In2=VSYS plane, 10-class
   ruleset frozen, routing not started" — every claim verifiable against the
   knowledge layer, none dependent on a volatile file.
2. **The recovery-baseline pattern.** When ledger and reality diverge, a swarm
   reconstructs true state into a pinned `⭐⭐ READ FIRST` memory that says *trust
   these sources, distrust these rows* — a correction layer over the ledger, not a
   silent rewrite (which would just move the drift).
3. **Commit geometry immediately** so "the file exists" is never a lie
   ([`05 §B2`](05_BOTTLENECKS.md)).

---

## What to write down (and what not to)

**Write:** a non-obvious decision and its *why*; a hard-won gotcha and its
workaround; a user preference with its rationale; a stable API recipe; the current
frontier and next action.

**Don't write:** what the repo already records (code structure, git history,
CLAUDE.md); what only matters to one conversation; geometry that belongs in a
committed file. If asked to "remember" one of those, capture *what was non-obvious
about it* instead.

**Before saving:** check for an existing file that already covers it and update
that one. A memory system's value is inversely proportional to its duplication.

---

## Generalization

Nothing here is PCB-specific. Any long-running AI-driven project — a codebase
migration, a research program, an ops runbook — inherits the same needs: typed
externalized facts, a dated index, a link graph, staleness handling, a
decision-based (not artifact-based) ledger, and a recovery pattern for when the
ledger drifts. Lift the whole layer wholesale.
