# automation/ — The Tools That Touch the EDA World

Reusable engines, split by backend. Agents *call* these; they don't reinvent them
per project. Improve a tool once and every board benefits.

| Sub-dir | Role | Used in phases |
|---|---|---|
| [`easyeda/`](easyeda/) | schematic generation + placement (Standalone-Script API) | 3, 4, 9 |
| [`browser/`](browser/) | headless CDP driver + netlist reconstruction (read the real board) | 4, 5, 9 |
| [`kicad/`](kicad/) | **routing + verification engine** (pours, zones, stitching, DRC) | 10, 11, 12 |
| [`shared/`](shared/) | backend-agnostic math: IPC-2221, units, congestion grid | 1, 7, 11 |

## The backend split — why it matters

The single most important tooling decision in Tracewright: **placement happens in EasyEDA,
routing happens in KiCad.**

- EasyEDA's Standalone-Script API can create/place/wire components and set
  placement, but its copper-pour / auto-route API rejects every signature and its
  netlist API hangs headless — so routing there is UI-only.
- KiCad's `pcbnew` + `kicad-cli` API *can* script pours, zones, stitching vias, and
  DRC. So the board is exported to KiCad (Phase 10) and routed there (Phase 11).

The browser layer bridges both: it drives EasyEDA headlessly and reads the real
board back for verification at every step. Deep reference:
[`../docs/06_EASYEDA_INTEGRATION.md`](../docs/06_EASYEDA_INTEGRATION.md),
[`../docs/07_BROWSER_AUTOMATION.md`](../docs/07_BROWSER_AUTOMATION.md),
[`../docs/11_REUSABLE_SYSTEMS.md`](../docs/11_REUSABLE_SYSTEMS.md).

## Contract for every tool here

- **Board-agnostic:** reads its board-specific data from the project, not hard-coded.
- **Re-runnable:** running it twice from the same source produces the same result.
- **Reality-verifying:** reads state back after mutating; never trusts its own model.
