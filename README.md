# AXON — An AI-Native Electronics Engineering Workflow

> A reusable, open method for taking a hardware product from a client brief to a
> manufacturable PCB — where **an AI agent is the engineer, the EDA tool is the
> compiler, and a human gates everything irreversible.**
>
> Works for any board: IoT nodes, robotics, motor controllers, audio, sensors,
> power electronics, wearables. Swap the parts and net names; the method is the
> same.

**→ New here? Read [`DESIGN_WORKFLOW.md`](DESIGN_WORKFLOW.md) — the step-by-step
design method, written for electronics engineers who've never seen this flow.**

---

## Why this exists

Most PCB projects treat the *schematic* as the design. This one doesn't. It treats
two plain documents — a **build sheet** (every part, pin, net) and a **net
dictionary** (every net → every connected pin) — as the real source, and treats the
schematic, placement, and routed copper as **build output generated from them.**

```
        ┌─────────────────────────────────────────────────────────┐
        │  KNOWLEDGE  is the SOURCE.   GEOMETRY  is the ARTIFACT.  │
        └─────────────────────────────────────────────────────────┘

   build_sheet.md + net_connection.md + design_rules.json   ← the SOURCE of the board
      │
      │   generate  (deterministic scripts + AI reasoning; the EDA tool = compiler)
      ▼
   schematic → placement → routing → gerbers                ← BUILD OUTPUT (regenerable)
      │
      │   verify  (real geometry, real DRC — never the tool's own self-report)
      ▼
   PASS / CONDITIONAL / FAIL verdict  ← the gate that unlocks the next stage
```

That one inversion, plus a cheap verification gate after every stage, is the whole
framework. It was reverse-engineered from a real, multi-month PCB project (an
ESP32-based robotics board designed in EasyEDA Pro, driven by an AI agent over ~30
sessions) — **including the honest record of what went wrong**, so you inherit the
solutions without paying the tuition.

---

## The method in one screen

**Ten stages, each with a hard exit gate. You never start a stage until the
previous one passes review** ("place nothing over wrong"). Inside every stage:
*generate one unit → review → fix → next.*

| # | Stage | Exit gate |
|---|---|---|
| 0 | Capture requirements | every requirement quantified |
| 1 | Architecture & feasibility | size + layer count justified by density & current math |
| 2 | Components & sourcing | every part datasheet-verified & sourced |
| 3 | Source-of-truth docs | build sheet ↔ net dictionary agree net-for-net |
| 4 | Generate schematic (section by section) | every section wired, 0 unmatched pins |
| 5 | Verify schematic (headless, net-by-net) | reconstructed netlist == source docs, 0 shorts |
| 6 | Placement | 0 spacing violations (real geometry) + practical + approved |
| 7 | Routing plan | 0 unclassed nets, feasibility scored |
| 8 | Route the board | 0 unrouted, DRC-clean vs the board's own ruleset |
| 9 | DRC / DFM / handoff | fab DFM pass, package **committed**, order by a human |

Full walkthrough → [`DESIGN_WORKFLOW.md`](DESIGN_WORKFLOW.md). Deep reference →
[`docs/01_METHODOLOGY.md`](docs/01_METHODOLOGY.md).

---

## What's in this repo

```
.
├── DESIGN_WORKFLOW.md   ← START HERE: the step-by-step design method (for engineers)
├── README.md            ← this file
├── CLAUDE.md            ← the AI operating manual (drop into any project)
├── AGENTS.md            ← the agent roster + how AI agents use this repo
├── docs/                ← the deep reference
│   ├── 00_PHILOSOPHY.md            first principles & why it's shaped this way
│   ├── 01_METHODOLOGY.md           the 10 gated stages in full detail
│   ├── 02_ARCHITECTURE.md          the 5-layer system architecture
│   ├── 03_KNOWLEDGE_GRAPH.md       extracted engineering intelligence (heuristics)
│   ├── 04_HUMAN_IN_THE_LOOP.md     the autonomy ladder + task classification
│   ├── 05_BOTTLENECKS.md           every pain point → a reusable solution
│   ├── 06_EASYEDA_INTEGRATION.md   the EDA-tool API contracts & hard limits
│   ├── 07_BROWSER_AUTOMATION.md    driving a cloud EDA tool headlessly (CDP)
│   ├── 08_PROMPT_AND_AGENT_STRATEGY.md  personas, swarms, verdict-gating
│   ├── 09_VALIDATION.md            DRC ground truth & real-geometry audit
│   ├── 10_MEMORY_AND_STATE.md      cross-session memory & state persistence
│   ├── 11_REUSABLE_SYSTEMS.md      catalog of every tool (IO/deps/failure/reuse)
│   ├── 12_DESIGN_PATTERNS.md       the recurring patterns, named
│   ├── 13_LESSONS_LEARNED.md       the honest ledger (successes & failures)
│   ├── 14_CONTRIBUTING.md          human + AI contribution guide
│   ├── 15_ROADMAP.md               where this goes next
│   └── 16_VERSION_2.md             the ideal rebuild-from-zero design
└── templates/           ← fill-in-the-blank artifacts for a new board
    ├── build_sheet.template.md         the tick-sheet (parts, pins, nets)
    ├── net_connection.template.md      the net dictionary + membership oracle
    ├── design_rules.template.json      net-class DRC rulebook
    ├── route_sequence.template.json    the ordered, DRC-gated routing plan
    ├── trace_width_table.template.json IPC-2221 current→width table
    ├── placement.template.json         region plan + coordinates + refdes silk
    └── section_generator.template.js   the board-agnostic schematic-gen engine
```

---

## Quickstart on your own board

1. `cp -r templates/ my-board/` and rename.
2. Fill `build_sheet.template.md` and `net_connection.template.md` from your brief
   (stages 0–3). **These two files are your board.**
3. Point your AI agent at [`CLAUDE.md`](CLAUDE.md): *"follow the method, build the
   next section."*
4. Run the loop — generate one section → verify → fix → next. The AI runs the
   replayable work; you own the gates (placement approval, go-ahead to route, DRC
   sign-off, and placing the fab order).

---

## Status & provenance

Extracted from a real ESP32 robotics board (40×55 mm, 4-layer, EasyEDA Pro + KiCad,
AI-driven). Every heuristic in [`docs/`](docs/) traces to a real artifact, a real
failure, or a real code path. Where the origin project's own process was *wrong*,
that's recorded as a finding, not hidden — see
[`docs/13_LESSONS_LEARNED.md`](docs/13_LESSONS_LEARNED.md).

## License

[MIT](LICENSE). Use it, fork it, adapt it to your bench. If it saves you a lost
board or a re-routed layout, it did its job.
