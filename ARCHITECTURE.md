# Tracewright Repository Architecture

> **New to Tracewright?** Don't start here — start with the
> **[handbook](handbook/README.md)**. This document is a deeper structural reference
> for when you want to understand *how the workspace is organized* (useful for
> contributors and the curious, not required to use Tracewright).

This document explains the *shape* of the repository: why each directory exists,
who uses it, how the AI agents plug into it, where engineering knowledge lives,
and how a new project inherits everything learned before it.

Read this once and the whole repo becomes navigable.

---

## The mental model

Tracewright separates four things that most PCB repos tangle together:

| Concern | Lives in | Nature |
|---|---|---|
| **The process** — the 12 gated phases | `workflow/` | stable, versioned, reused every project |
| **The workers** — AI agent roles | `agents/` | stable definitions the orchestrator invokes |
| **The tools** — the code that touches EDA | `automation/` | reusable engines (EasyEDA / browser / KiCad / shared) |
| **The learnings** — engineering knowledge | `knowledge/` + `docs/` | compounds across every project |
| **The work** — an actual board | `projects/<name>/` | disposable build artifacts + that board's decisions |
| **The blanks** — source-of-truth templates | `templates/` | copied into each project |

The governing principle behind the split (see
[`knowledge/principles.md`](knowledge/principles.md) →
[`docs/00_PHILOSOPHY.md`](docs/00_PHILOSOPHY.md)): **knowledge is the source,
geometry is the build artifact.** The first four rows are the durable source; the
`projects/` row is the regenerable build output. That is why they are physically
separated — you protect and version the source, and you can throw away and
regenerate the build.

```
   knowledge/ + docs/   ─┐
   workflow/            ─┤   the DURABLE FRAMEWORK  (one copy, reused for every board)
   agents/  automation/ ─┤   → improves with every project
   templates/           ─┘
          │  copied + driven
          ▼
   projects/<board>/     the BUILD  (per-board; schematic, placement, routing, gerbers)
          │  new lessons flow back up
          └───────────────────────────────► knowledge/learning-db.md
```

That last arrow is the point of the whole design: **every project makes the
framework smarter.**

---

## Directory by directory

### `workflow/` — the 12-phase pipeline (the process)

The canonical, gated engineering process, one file per phase
(`01-requirement-analysis.md` … `12-final-verification.md`) plus a
[`README`](workflow/README.md) with the pipeline overview and gate table.

Each phase file states, in the same shape: **objective · inputs · outputs ·
validation · deliverables · engineering checklist · automation · human review ·
exit gate · owning agent.** A phase does not start until the previous phase's exit
gate passes ("place nothing over wrong").

- **Contributors** refine a phase by editing its file — the improvement applies to
  every future project automatically.
- **AI agents** read the current phase's file to know exactly what to produce and
  what gate to satisfy.
- **Engineers** read it to understand the method without touching any AI.

> This is where your 12-phase workflow becomes executable structure rather than a
> description. It supersedes the older 10-phase conceptual view in
> [`docs/01_METHODOLOGY.md`](docs/01_METHODOLOGY.md), which is retained as
> background reading.

### `agents/` — the AI worker roles

One definition per agent role (`feasibility-analyst`, `bom-planner`,
`schematic-generator`, `schematic-auditor`, `placement-planner`, `router`,
`verification-engineer`) plus an `orchestrator` and a [`README`](agents/README.md)
mapping agents → phases. Each definition states the agent's mission, the phase it
owns, its tools, its inputs/outputs, its **autonomy tier**, and its output
contract (a structured verdict, not prose).

- **AI agents** are *instantiated* from these files — the orchestrator dispatches
  the right agent for the current phase.
- **Contributors** add a new capability by adding an agent definition; the
  workflow references it by name.

### `automation/` — the tools that touch the EDA world

The reusable engines, split by backend because each backend has different
strengths and hard limits:

- [`easyeda/`](automation/easyeda/) — schematic generation + placement via the
  Standalone-Script API. Holds the board-agnostic generator engine.
- [`browser/`](automation/browser/) — the headless CDP driver + netlist
  reconstruction that lets agents read the *real* board back.
- [`kicad/`](automation/kicad/) — **the routing + verification engine.** Routing is
  done here, not in EasyEDA, because KiCad's `pcbnew`/`kicad-cli` API can script
  pours, zones, stitching, and DRC (EasyEDA's cannot). Holds `drc.sh` (DRC ground
  truth), the stitcher, and the router.
- [`shared/`](automation/shared/) — backend-agnostic math: IPC-2221 trace widths,
  unit conversion, congestion grid.

- **AI agents** call these tools; they don't reinvent them per project.
- **Contributors** improve a tool once and every project benefits.

### `knowledge/` — the engineering brain (the part that compounds)

The living, growing, machine-usable knowledge that carries *across* projects:

- [`principles.md`](knowledge/principles.md) — the first principles.
- [`knowledge-graph.md`](knowledge/knowledge-graph.md) — reusable heuristics
  (decisions, failures, quantified rules).
- [`design-standards.md`](knowledge/design-standards.md) — IPC-2221 widths, via
  ampacity, stackup selection, clearance floors — the hard engineering rules.
- [`learning-db.md`](knowledge/learning-db.md) — **append-only.** Every new
  failure→lesson from any project lands here in a fixed format and becomes
  available to all future projects.
- [`knowledge-inheritance.md`](knowledge/knowledge-inheritance.md) — the mechanism
  by which a new project starts with all prior learnings.

The deep prose reference (philosophy essays, patterns, bottleneck write-ups,
lessons) lives in [`docs/`](docs/) — the **reference library**. `knowledge/` is
the operational, growing layer; `docs/` is the stable theory it's built on.

- **AI agents** consult `knowledge/` before acting and *write back* to
  `learning-db.md` when they discover something.
- **Contributors** promote a repeated project-specific lesson into a general
  heuristic here.

### `projects/` — per-board workspaces (the build)

Each real board is a folder under `projects/` scaffolded from
[`_template/`](projects/_template/): one directory per phase (`00_brief` …
`12_verification`) plus a `project.yaml` manifest (board params, chosen stackup,
current phase, verdicts). This is the **only** place board-specific geometry and
decisions live — the framework itself stays board-agnostic.

- **Engineers** work a board here, phase by phase.
- **AI agents** read the manifest to know the current phase and drive it.
- Geometry here is **committed immediately** (an uncommitted board is one mistake
  from gone) but is understood to be regenerable from the phase artifacts.

### `templates/` — source-of-truth blanks

The fill-in-the-blank artifacts copied into each project: `build_sheet`,
`net_connection`, `design_rules`, `route_sequence`, `trace_width_table`,
`placement`. These define a board completely; the schematic/placement/routing are
generated from them. (The generator *engine* lives in `automation/`, not here —
templates are data, engines are code.)

### `docs/` — the reference library

The stable, deep engineering essays: philosophy, the 5-layer system architecture,
validation methodology, memory/state, human-in-the-loop tiers, design patterns,
the honest lessons-learned ledger, and the V2 vision. The operational layers
(`workflow/`, `agents/`, `automation/`, `knowledge/`) link into these for the
"why." Contributors keep them evergreen; they change slowly.

### Root files

- [`README.md`](README.md) — the front door.
- [`DESIGN_WORKFLOW.md`](DESIGN_WORKFLOW.md) — the 12-phase method for engineers.
- [`CLAUDE.md`](CLAUDE.md) / [`AGENTS.md`](AGENTS.md) — the AI operating manuals.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — for humans and agents.

---

## How the pieces interact (one project's life)

```
  client brief
      │
      ▼
  projects/myboard/  ← scaffolded from templates/ + projects/_template/
      │
      │  the ORCHESTRATOR walks workflow/01 … workflow/12
      ▼
  for each phase:
     agents/<owner>  reads  workflow/<phase>  +  knowledge/*  +  the project manifest
         │  uses  automation/<backend>  to act on the board
         │  emits a structured VERDICT  (PASS / CONDITIONAL / FAIL)
         ▼
     verdict gates entry to the next phase   ← human signs the irreversible ones
      │
      ▼
  new lessons  ──►  knowledge/learning-db.md   (the framework gets smarter)
```

EasyEDA hosts phases 3–9 (schematic + placement); KiCad hosts phases 10–12
(routing + verification); the browser layer verifies the real board at every step.

---

## How future projects inherit past learnings

This is the long-term payoff and it is deliberate, not incidental:

1. **The framework is shared, the board is not.** `workflow/`, `agents/`,
   `automation/`, `knowledge/`, `templates/` are one copy used by every project in
   `projects/`. Improve any of them once and the next board starts ahead.
2. **Lessons flow upward.** When an agent hits a new failure on board B, it writes
   a `Heuristic → Why → Instance → Validation → Prevention` entry to
   `knowledge/learning-db.md`. Board C's agents read it before they act — so C
   cannot repeat B's mistake.
3. **Heuristics get promoted.** A lesson seen on multiple boards graduates from
   `learning-db.md` into `knowledge/knowledge-graph.md` (a general rule) or
   `knowledge/design-standards.md` (a hard limit), sometimes into a `workflow/`
   phase gate — the strongest form, where the mistake becomes structurally
   impossible.
4. **Verdicts are the audit trail.** Every phase's dated verdict stays in the
   project, so a future engineer (or agent) can see exactly why the board is the
   way it is.

See [`knowledge/knowledge-inheritance.md`](knowledge/knowledge-inheritance.md) for
the full mechanism.

---

## Why this is a redesign, not a rearrangement

The old layout was a flat pile of docs and templates — good reference, but it
described the method without *operationalizing* it. This architecture adds the
four layers that were missing: an executable **process** (`workflow/`), the
**workers** that run it (`agents/`), the **tools** they use (`automation/`), and a
place for the work that keeps the framework board-agnostic (`projects/`) — all
wired to a knowledge base that **compounds**. The method didn't change; it became
a machine you can run.
