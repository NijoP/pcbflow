# docs/ — The Reference Library

The stable, deep engineering essays behind PCB Flow. The operational layers
(`workflow/`, `agents/`, `automation/`, `knowledge/`) link *into* these for the
"why." They change slowly; contributors keep them evergreen.

| Doc | Topic |
|---|---|
| [`00_PHILOSOPHY.md`](00_PHILOSOPHY.md) | first principles & why the framework is shaped this way |
| [`01_METHODOLOGY.md`](01_METHODOLOGY.md) | the methodology in prose *(conceptual 10-phase view — the canonical operational pipeline is now [`../workflow/`](../workflow/), a 12-phase refinement)* |
| [`02_ARCHITECTURE.md`](02_ARCHITECTURE.md) | the 5-layer system architecture (knowledge/generation/geometry/verification/governance) |
| [`03_KNOWLEDGE_GRAPH.md`](03_KNOWLEDGE_GRAPH.md) | the full heuristics graph (indexed by [`../knowledge/knowledge-graph.md`](../knowledge/knowledge-graph.md)) |
| [`04_HUMAN_IN_THE_LOOP.md`](04_HUMAN_IN_THE_LOOP.md) | the autonomy ladder + task classification |
| [`05_BOTTLENECKS.md`](05_BOTTLENECKS.md) | every pain point → a reusable solution |
| [`06_EASYEDA_INTEGRATION.md`](06_EASYEDA_INTEGRATION.md) | the EDA-tool API contracts & hard limits |
| [`07_BROWSER_AUTOMATION.md`](07_BROWSER_AUTOMATION.md) | driving a cloud EDA tool headlessly (CDP) |
| [`08_PROMPT_AND_AGENT_STRATEGY.md`](08_PROMPT_AND_AGENT_STRATEGY.md) | personas, swarms, verdict-gating |
| [`09_VALIDATION.md`](09_VALIDATION.md) | DRC ground truth & real-geometry audit |
| [`10_MEMORY_AND_STATE.md`](10_MEMORY_AND_STATE.md) | cross-session memory & state persistence |
| [`11_REUSABLE_SYSTEMS.md`](11_REUSABLE_SYSTEMS.md) | catalog of every tool (IO/deps/failure/reuse) |
| [`12_DESIGN_PATTERNS.md`](12_DESIGN_PATTERNS.md) | the recurring patterns, named |
| [`13_LESSONS_LEARNED.md`](13_LESSONS_LEARNED.md) | the honest ledger (successes & failures) |
| [`14_CONTRIBUTING.md`](14_CONTRIBUTING.md) | (superseded by root [`../CONTRIBUTING.md`](../CONTRIBUTING.md)) |
| [`15_ROADMAP.md`](15_ROADMAP.md) | where this goes next |
| [`16_VERSION_2.md`](16_VERSION_2.md) | the ideal rebuild-from-zero design (largely realized in this redesign) |

New to PCB Flow? Don't start here — start with [`../DESIGN_WORKFLOW.md`](../DESIGN_WORKFLOW.md)
and [`../ARCHITECTURE.md`](../ARCHITECTURE.md). Come here for depth on a specific topic.
