# workflow/ — The 12-Phase Engineering Pipeline

This is the canonical, gated process every PCB Flow project follows. One file per
phase, each in the same shape so an agent or engineer can pick up any phase
without re-reading the rest.

## How to use it

- **An AI agent** driving a board reads the current phase file to know exactly what
  to produce and which gate to satisfy, then hands off to the next phase only on a
  PASS.
- **An engineer** reads it to run (or audit) the process by hand.
- **A contributor** improves the method by editing a phase file — the change
  applies to every future project.

## The prime rule

**You do not enter phase N+1 until phase N's exit gate passes.** Every phase ends
in a dated verdict — `PASS / CONDITIONAL(numbered fixes) / FAIL`. Inside each
phase, the loop is *generate one unit → review → fix → next.*

## The pipeline

| # | Phase | Owning agent | Tool | Exit gate |
|---|---|---|---|---|
| 1 | [Requirement analysis & feasibility](01-requirement-analysis.md) | feasibility-analyst | — | feasibility study complete |
| 2 | [BOM planning](02-bom-planning.md) | bom-planner | — | BOM fully validated |
| 3 | [EasyEDA initialization](03-easyeda-initialization.md) | schematic-generator | EasyEDA | sheets + stackup set |
| 4 | [Schematic generation](04-schematic-generation.md) | schematic-generator | EasyEDA | 0 unmatched pins |
| 5 | [Schematic audit](05-schematic-audit.md) | schematic-auditor | browser | 0 shorts, netlist == source |
| 6 | [Placement planning](06-placement-planning.md) | placement-planner | — | client constraints captured |
| 7 | [Placement knowledge graph](07-placement-knowledge-graph.md) | placement-planner | — | graph complete |
| 8 | [Visual placement planning](08-visual-placement.md) | placement-planner | — | plan approved |
| 9 | [Automated placement](09-automated-placement.md) | placement-planner | EasyEDA | 0 spacing violations |
| 10 | [Export to KiCad](10-export-to-kicad.md) | router | EasyEDA→KiCad | import verified |
| 11 | [AI-assisted routing](11-ai-routing.md) | router | KiCad | 0 unrouted, DRC-clean |
| 12 | [Final verification](12-final-verification.md) | verification-engineer | KiCad | manufacturing-ready |

Phases 1–2 are analysis (no EDA). 3–9 run in EasyEDA (schematic + placement).
10–12 run in KiCad (routing + verification). The browser layer verifies the real
board throughout. Agents are defined in [`../agents/`](../agents/); tools in
[`../automation/`](../automation/); the knowledge each phase consults in
[`../knowledge/`](../knowledge/).
