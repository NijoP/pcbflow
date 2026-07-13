# Tracewright — Product Roadmap

Where the project is and where it's going. (This is the *product* roadmap; the
internal reliability build plan lives in
[`reliability/ROADMAP.md`](reliability/ROADMAP.md).)

## ✅ Current capabilities

- **The 12-phase engineering workflow** — client requirement → feasibility → BOM →
  EasyEDA project → AI schematic generation → schematic audit → placement planning →
  placement knowledge graph → automated placement → KiCad export → AI-assisted routing
  → verification → manufacturing, each with a hard checkpoint.
- **AI agent roster** — one defined role per phase, coordinated by an orchestrator.
- **Automation** — EasyEDA schematic + placement (Standalone-Script engine), headless
  browser readback (CDP), KiCad routing + DRC, and a shared IPC-2221 / congestion layer.
- **Engineering knowledge base** — first principles, a heuristics graph, hard design
  standards (IPC widths, via ampacity, DFM floor), and an append-only learning log that
  compounds across projects.
- **Reliability & self-healing (Phases 1–5, built + tested)** — a preflight environment
  `doctor`, structured logging, automatic fault diagnosis, safe retry, a self-healing
  recovery engine with plain-English errors, checkpoint/resume, a phantom-DRC guard, and
  cross-platform tooling.
- **Engineer handbook** — a 12-step onboarding path plus a glossary, written for
  electronics engineers with no software background.

## 🚧 In progress / needs real-world validation

- **Live-session validation** of the recovery strategies (renderer-hang reset, session
  re-auth, Chrome/CDP recovery) against a real EasyEDA session.
- **Non-Linux validation** of the cross-platform launcher and DRC runner on macOS and
  Windows (logic is written and unit-tested; the live launch needs a real host).
- **A worked reference project** end-to-end in `projects/` as a public example.

## 🔭 Planned

- A branded CLI wrapper (`tracewright doctor`, `tracewright route`, …) over the `tools/`.
- A source-of-truth linter (auto-check `build_sheet.md` ↔ `net_connection.md`).
- Deeper KiCad-native routing automation (pours/zones/stitching scripted end-to-end).
- More AI-agent adapters and an explicit adapter interface.

## 🧪 Future research

- **Board recompile** — regenerate schematic → placement → routing from the knowledge
  layer with one command (making "geometry is a build artifact" literally executable).
- A **cross-project knowledge graph** that promotes board-specific lessons into general
  engineering rules automatically.
- Additional EDA backends behind a common adapter.

## 🌟 Long-term vision

Every electronics engineer has a disciplined AI collaborator that carries a design from
brief to manufacturing, gets smarter with every board, and never takes an irreversible
decision out of human hands. See [`BRANDING.md`](BRANDING.md) for the full vision.

> Status legend: ✅ built & tested · 🚧 in progress / needs validation · 🔭 planned ·
> 🧪 research · 🌟 vision.
