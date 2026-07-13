# knowledge/ — The Engineering Brain

The part of Tracewright that **compounds**. Everything here carries *across* projects: a
lesson learned on board B is available to board C before it makes B's mistake.

## What lives here

| File | Role | Grows? |
|---|---|---|
| [`principles.md`](principles.md) | the first principles (source of every design choice) | slowly |
| [`knowledge-graph.md`](knowledge-graph.md) | reusable heuristics — decisions, failures, quantified rules | slowly |
| [`design-standards.md`](design-standards.md) | hard engineering rules: IPC-2221, via ampacity, stackup, clearances | slowly |
| [`learning-db.md`](learning-db.md) | **append-only** failure→lesson log from every project | every project |
| [`knowledge-inheritance.md`](knowledge-inheritance.md) | how a new project inherits all of the above | — |

The deep prose (philosophy essays, patterns, bottleneck write-ups, the full lessons
ledger) is the **reference library** in [`../docs/`](../docs/). `knowledge/` is the
operational, machine-consulted layer; `docs/` is the stable theory behind it.

## The lifecycle of a lesson (why this compounds)

```
  a project hits a failure
        │
        ▼
  learning-db.md   ← append a  Heuristic → Why → Instance → Validation → Prevention  entry
        │  (seen again on another board?)
        ▼
  knowledge-graph.md   ← promote to a general heuristic
        │  (a hard, quantifiable limit?)
        ▼
  design-standards.md  ← becomes an enforceable rule
        │  (can it be made structurally impossible?)
        ▼
  a workflow/ phase gate   ← the strongest form: the mistake can't recur
```

## How agents use it

Every agent **reads** the relevant entries before acting and **writes back** new
lessons to `learning-db.md`. That write-back is not optional — it's how the
framework gets smarter. See
[`knowledge-inheritance.md`](knowledge-inheritance.md).
