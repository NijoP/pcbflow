# <Board name> — Project Workspace

Scaffolded from the Tracewright `_template`. One folder per phase; fill each as you pass its
gate. Start with `project.yaml` and Phase 1.

## Phase folders

| Folder | Phase | Holds |
|---|---|---|
| `00_brief/` | — | the raw client brief, call notes, sketches, PDF |
| `01_feasibility/` | 1 | feasibility study, constraint table, power budget |
| `02_bom/` | 2 | validated BOM + datasheet notes |
| `03_easyeda_init/` | 3 | EasyEDA project ID, sheet UUIDs, stackup note |
| `04_schematic/` | 3–4 | `build_sheet.md`, `net_connection.md`, generator scripts |
| `05_schematic_audit/` | 5 | audit report + verdict |
| `06_placement_plan/` | 6 | client mechanical constraints |
| `07_placement_kg/` | 7 | placement knowledge graph |
| `08_visual_placement/` | 8 | approved placement map |
| `09_placement_exec/` | 9 | `placement.json`, refdes silk, real-geometry audit |
| `10_kicad_export/` | 10 | `board.kicad_pcb` + `.kicad_pro` + fidelity report |
| `11_routing/` | 11 | routed board + routing report |
| `12_verification/` | 12 | `manufacturing/` package + final report |

## How to run it

Do not enter a phase until the previous phase's gate passes (see
[`../../workflow/`](../../workflow/)). Keep `project.yaml` current — it's the
orchestrator's source of truth for where the board stands. Commit each phase's
deliverables as you finish it.
