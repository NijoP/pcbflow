# agents/ — The AI Worker Roles

Tracewright is driven by a team of AI agents, one per phase, coordinated by an
orchestrator. Each file here is an **agent definition** — a role an AI is
instantiated into. They are stable; the board changes, the roles don't.

## The roster

| Agent | Owns phase(s) | Autonomy | Output contract |
|---|---|---|---|
| [`orchestrator`](orchestrator.md) | all — dispatch & gate | — | phase transitions on verdicts |
| [`feasibility-analyst`](feasibility-analyst.md) | 1 | Tier 1 | feasibility study + verdict |
| [`bom-planner`](bom-planner.md) | 2 | Tier 1 | validated BOM |
| [`schematic-generator`](schematic-generator.md) | 3, 4 | Tier 1/2 | generator scripts + live schematic |
| [`schematic-auditor`](schematic-auditor.md) | 5 | Tier 1 | audit report + verdict |
| [`placement-planner`](placement-planner.md) | 6, 7, 8, 9 | Tier 1/2 | KG + map + placement |
| [`router`](router.md) | 10, 11 | Tier 1/3 | routed board + DRC verdict |
| [`verification-engineer`](verification-engineer.md) | 12 | Tier 6 | mfg package + signed verdict |

## The prime contract (every agent obeys)

1. **Dual persona** — senior software engineer *and* senior hardware/PCB engineer
   (the HW persona vetoes any electrical unknown).
2. **Ground truth first** — read the phase file, the project manifest, and the
   relevant `../knowledge/` entries; treat prior notes as stale-by-default.
3. **Emit a structured verdict** — `PASS / CONDITIONAL(numbered) / FAIL`, dated,
   naming the ruleset/board — never prose.
4. **Autonomy by reversibility** — replayable work runs free; live writes need a
   go-ahead; irreversible acts (fab order) are human-only.
5. **Verify against reality**, never the tool's self-report.
6. **Write back** new lessons to [`../knowledge/learning-db.md`](../knowledge/learning-db.md).

## How agents interact with the repo

An agent reads [`../workflow/<phase>`](../workflow/) for *what to do*,
[`../knowledge/`](../knowledge/) for *what's known*, calls
[`../automation/`](../automation/) for *how to act*, writes results into the
project's phase folder under `../projects/<board>/`, and returns a verdict the
orchestrator uses to gate the next phase. Adding a capability = adding an agent
file here + referencing it from a phase.
