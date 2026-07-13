# Knowledge Inheritance — How Future Projects Start Ahead

The long-term payoff of PCB Flow: **every project makes the framework smarter, and every
new project inherits everything learned before it.** This is deliberate mechanism,
not aspiration.

---

## The two-way flow

```
   knowledge/ + workflow/ + agents/ + automation/ + templates/   (the shared framework)
        │  a new board INHERITS all of this on day one
        ▼
   projects/<new-board>/     ← starts with every prior lesson already in force
        │  discovers a new failure/lesson
        ▼
   knowledge/learning-db.md  ← the lesson flows back UP into the shared framework
        │  seen again / hardened
        ▼
   knowledge-graph.md → design-standards.md → a workflow gate   (promoted)
```

## What a new project inherits (for free)

1. **The process** — the 12 gated phases in `workflow/`. It doesn't reinvent the flow.
2. **The workers** — the agent roster in `agents/`. It doesn't re-specify roles.
3. **The tools** — the engines in `automation/`. It doesn't rewrite the generator,
   the CDP driver, the router, or `drc.sh`.
4. **The hard rules** — `design-standards.md` (IPC widths, via ampacity, DFM floor).
5. **Every prior lesson** — `learning-db.md`. Board C literally cannot repeat board
   B's blind-via shorts, because L3 is read before the router acts.

## How a lesson is promoted (the ratchet)

A lesson gets *stronger* each time it's confirmed:

| Stage | Where it lives | Force |
|---|---|---|
| First seen | `learning-db.md` | an entry agents read |
| Seen again | `knowledge-graph.md` | a general heuristic |
| Quantifiable limit | `design-standards.md` | an enforceable number |
| Can be made structural | a `workflow/` gate | the mistake becomes *impossible* |

The strongest form is a phase gate — e.g. "commit the package" is a Phase-12 exit
condition, so the lost-board failure (L7) can't recur no matter who runs the project.

## How agents participate

- **Before acting:** an agent reads the relevant `knowledge/` entries for its phase.
- **After discovering something:** it appends a `Heuristic → Why → Instance →
  Validation → Prevention` entry to `learning-db.md`. This is part of the agent
  contract, not optional.
- **Periodically:** a maintainer (human or a dedicated agent) promotes repeated
  `learning-db.md` entries up the ratchet.

## Why board-specific work stays out of the framework

Board geometry, net names, and one-off decisions live only in `projects/<board>/`.
If board-specific facts leaked into `knowledge/`, the framework would stop being
reusable. The discipline — *general rule in `knowledge/`, specific instance in the
project* — is what lets one framework serve every future board.
