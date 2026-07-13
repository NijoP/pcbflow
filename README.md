# Tracewright

**Your AI bench engineer — from client brief to manufacturing-ready board.**

Tracewright is an AI-assisted electronics engineering workspace. You bring the PCB and
electronics knowledge; an AI assistant does the repetitive, error-prone work — wiring
schematics, placing parts, routing, running checks — while **you make every engineering
decision that matters.** You never have to write software.

> 👉 **New here? Start with the [handbook](handbook/README.md)** — a step-by-step guide
> for electronics engineers, from installing the tools to shipping a board.

---

## 1. What is this?

Tracewright is a **workspace and a method**, not a program you run. You open it in a code
editor (VS Code), and an **AI assistant** reads the instructions in this repository and
helps you design a PCB — doing the busywork and the checking, and stopping to ask you
whenever a real engineering decision comes up.

**Why it was created:** PCB design is full of careful, repetitive, mistake-prone work —
every net wired, every pin checked, every part placed, every trace sized, every rule
verified. That work is perfect for a tireless assistant and wasteful for a skilled
engineer. Tracewright hands it to an AI that follows a fixed set of engineering rules,
and keeps *you* as the decision-maker.

**What it solves:** drift between the spec and the board, layouts built on a wrong
schematic, boards lost because nobody saved them, and hours spent on mechanical work an
assistant could do — while never taking a safety, sizing, or ordering decision out of
your hands.

**Who it's for:** electronics engineers who know PCB design, schematics, BOMs, and
manufacturing — and who do **not** need to know programming, APIs, or automation.

## 2. Vision

**AI assists the engineer; it does not replace them.** The goal is to automate the
repetitive engineering work while keeping human judgment central. The AI is a fast,
disciplined junior engineer who has read every datasheet and never tires of checking
nets — but who always defers to you on the decisions that carry real risk. It never
sizes a power path below its limit, never signs off a design-rule check, and **never
orders a board.** As you build more boards, it gets smarter: every lesson learned on one
project is carried into the next.

## 3. High-level workflow

Twelve phases, each with a checkpoint. You never start a phase until the previous one is
confirmed correct.

```
  Client requirement → Feasibility study → BOM planning → EasyEDA project →
  AI-assisted schematic generation → Engineering review → Placement planning →
  Automated component placement → KiCad export → AI-assisted routing →
  Verification → Manufacturing
```

1. **Client requirement** — capture what the product must do.
2. **Feasibility study** — the AI checks technical feasibility, cost, power budget,
   board size, and layer count with real math before any design starts.
3. **BOM planning** — build and validate the parts list (availability, cost, package,
   electrical fit, second sources).
4. **EasyEDA project** — create the project, sheets, and stack-up.
5. **AI-assisted schematic generation** — the AI draws the schematic block by block,
   wiring every net; you review and run Annotate.
6. **Engineering review** — the schematic is audited (shorts, floating pins, ERC, net
   list match). Nothing proceeds until it's clean.
7. **Placement planning** — you define board size, shape, connectors, keep-outs, and
   mounting; the AI builds a placement knowledge graph and a visual plan for approval.
8. **Automated component placement** — the AI places all parts and checks real spacing;
   you approve the layout.
9. **KiCad export** — the placed board moves to KiCad (which is the routing engine) and
   the import is verified faithful.
10. **AI-assisted routing** — the AI routes to IPC standards (widths, current, diff
    pairs, return paths, EMI) and iterates until the design-rule check is clean.
11. **Verification** — a full review: DRC, ERC, manufacturing, silkscreen, assembly,
    mechanical, BOM.
12. **Manufacturing** — the AI produces the factory files; **you place the order.**

Full detail per phase: [`workflow/`](workflow/) and the [handbook](handbook/README.md).

## 4. Repository overview

| Folder | What it's for |
|---|---|
| [`handbook/`](handbook/) | **Start here** — the step-by-step guide for engineers. |
| [`workflow/`](workflow/) | The 12 design phases, each with its checkpoint. |
| [`agents/`](agents/) | The "job descriptions" for the AI helpers (one per phase). |
| [`automation/`](automation/) | The tools the AI uses to drive EasyEDA and KiCad. *You don't touch these.* |
| [`knowledge/`](knowledge/) | The engineering rules and lessons the AI follows (IPC widths, design standards, learnings). |
| [`templates/`](templates/) | Blank forms you fill in for a new board (parts list, net list, rules). |
| [`projects/`](projects/) | **Your boards live here** — one folder per project, with all its files and outputs. |
| [`tools/`](tools/) | Reliability helpers: the environment check (`doctor`), logging, and self-healing recovery. |
| [`reliability/`](reliability/) | How the workspace detects and recovers from problems + the [troubleshooting guide](reliability/TROUBLESHOOTING.md). |
| [`docs/`](docs/) | Deep reference material. *Optional — for later, or for contributors.* |

Why the structure: the **method** (`workflow/`), the **workers** (`agents/`), the
**tools** (`automation/`, `tools/`), and the **knowledge** (`knowledge/`) are shared and
reused for every board; only the board itself lives in `projects/`. Full explanation:
[`ARCHITECTURE.md`](ARCHITECTURE.md).

## 5. Supported AI tools

Tracewright is **AI-model-agnostic.** It works with any AI coding assistant that can read
Markdown instructions and run tools inside VS Code:

- **Claude Code** (Anthropic) — recommended
- **OpenAI Codex**
- **OpenCode**
- **Cursor**
- **Gemini CLI**
- …and future compatible AI coding agents.

The framework does not depend on a single AI provider. The instructions live in plain
Markdown (`CLAUDE.md`, `AGENTS.md`, `workflow/`), which any capable agent can follow.

## 6. Software requirements

| Tool | For | Required |
|---|---|---|
| **VS Code** | the workspace you open this in | yes |
| **An AI assistant** (any from §5) | the assistant that helps you | yes |
| **EasyEDA Pro** (free) | schematic + placement | yes (from phase 3) |
| **KiCad** (free) | routing + verification | yes (from phase 10) |
| **Git** | saves & publishes your work | yes |
| **Chrome** | so the AI can read your live EasyEDA board | yes (from phase 3) |
| **Python 3.9+** | runs the reliability helpers | yes |
| **Node.js 18+** | some automation scripts | when automation runs |

**Skills required:** electronics and PCB knowledge. **No programming required.**

## 7. Getting started

1. **Install the software** — [`handbook/02`](handbook/02-installing-tools.md).
2. **Clone this repository** and open the folder in VS Code
   ([`handbook/03`](handbook/03-vscode-and-ai.md)).
3. **Check your environment:** run `python3 tools/doctor.py` — it lists each tool with
   ✅ / ⚠️ / ❌ and tells you how to fix anything missing.
4. **Create your first project** — [`handbook/04`](handbook/04-your-first-project.md):
   ```
   cp -r projects/_template projects/my-board
   ```
   Then tell your AI assistant: *"follow the workflow, start phase 1 for
   projects/my-board — it's a [describe your product]."*
5. **Work the phases** — generate the schematic, review it, place, route, verify. The AI
   runs the repetitive work; you approve the checkpoints.

That's it. From here you talk to the AI in plain English and it walks you through the
rest.

## 8. Roadmap

- **✅ Built now:** the 12-phase workflow, the AI agent roster, EasyEDA + KiCad
  automation, the engineering knowledge base, and a complete self-healing reliability
  layer (environment check, logging, auto-diagnosis, retry, recovery, resume,
  cross-platform tools).
- **🚧 In progress:** live-session validation of the recovery strategies; macOS/Windows
  validation; a public end-to-end example project.
- **🔭 Planned:** a branded CLI, a source-of-truth linter, deeper KiCad routing
  automation, more AI-agent adapters.
- **🧪 Research:** one-command "board recompile" from the knowledge layer; a
  cross-project knowledge graph; more EDA backends.

Full detail: [`ROADMAP.md`](ROADMAP.md).

## 9. Notes

**Please read these — they set honest expectations.**

- **Human review is required.** The AI stops for your approval before drawing copper,
  and always leaves safety-critical calls (power sizing, DRC sign-off) and the **fab
  order** to you.
- **Known EasyEDA limitations:** script-drawn schematics are electrically correct but not
  perfectly aligned (a cosmetic limitation; the audit guarantees the wiring). Copper
  pours and routing can't be scripted in EasyEDA — which is why routing happens in KiCad.
- **Browser automation:** the AI reads your *live* EasyEDA board through Chrome; keep one
  EasyEDA window open and signed in. Details:
  [`reliability/TROUBLESHOOTING.md`](reliability/TROUBLESHOOTING.md).
- **Supported platforms:** developed and validated on **Linux**; cross-platform tooling
  for **macOS/Windows** is built and unit-tested but still needs real-world validation on
  those hosts.
- **Engineering assumptions:** DRC ground truth is always the board's own tool with its
  own ruleset (never a bare board file); high-current paths use copper planes, not
  traces; grounds return cleanly. These are enforced in
  [`knowledge/design-standards.md`](knowledge/design-standards.md).
- **Recommended workflow:** one phase at a time, review each checkpoint, commit your work
  as you go. The AI's reliability layer auto-recovers common failures and explains the
  rest in plain English.
- **If something breaks:** just tell the AI *"something went wrong — read the log and fix
  it."* See [`reliability/TROUBLESHOOTING.md`](reliability/TROUBLESHOOTING.md).

## 10. Contributing

Contributions are welcome — from engineers and AI agents alike. In short: improve a
**phase** (`workflow/`), a **tool** (`automation/`, `tools/`), or the **knowledge**
(`knowledge/`); keep board-specific work inside `projects/`; every claim should trace to
a real artifact; prefer updating over duplicating. Full guide:
[`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Provenance & license

Tracewright was extracted from a real ESP32 robotics board designed with EasyEDA Pro +
KiCad and an AI assistant, **including the honest record of what went wrong** — see
[`docs/13_LESSONS_LEARNED.md`](docs/13_LESSONS_LEARNED.md) and
[`knowledge/learning-db.md`](knowledge/learning-db.md). You inherit the solutions without
paying the tuition.

Naming, identity, and vision: [`BRANDING.md`](BRANDING.md).
License: [MIT](LICENSE).
