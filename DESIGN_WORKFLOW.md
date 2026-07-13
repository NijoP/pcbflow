# The PCB Flow Design Method — 12 Phases, Step by Step

> **Want a gentler, hands-on walkthrough?** Use the
> **[handbook](handbook/README.md)** instead — it teaches the same 12 steps with
> tool setup, examples, and checklists. This page is the concise reference version.

> **For the electronics engineer reading this repo for the first time.**
> This is how we take a hardware product from a client conversation to a
> manufacturing-ready PCB. It's a rigorous EE flow — feasibility → BOM →
> schematic → placement → routing → verification — reorganized around one idea and
> driven by AI agents working under human supervision. Read this page and you
> understand the whole method; [`workflow/`](workflow/) is the gate-by-gate
> reference and [`ARCHITECTURE.md`](ARCHITECTURE.md) is the repo structure.

---

## The idea to grasp first

Two kinds of thing exist in a PCB project:

- **Knowledge** — requirements, the net list, part choices, design rules, the
  reasoning ("4-layer because of the 10 A motor rail"). Authored, reviewed,
  versioned. The **source code** of the board.
- **Geometry** — the schematic, placement, routed copper, gerbers. *Generated*
  from the knowledge, and regenerable if the knowledge is intact. The **build
  output**.

> **Knowledge is the source. Geometry is the build artifact.**

So the files that *are* the board aren't the schematic — they're the **build
sheet** (every part, pin, net), the **net dictionary** (every net → every pin),
and the **design rules**. Get those right and the rest is a build step.

## Who does what — and the rule for deciding

The AI runs the analysis, generation, and validation; the human owns judgment and
anything irreversible. The rule isn't "who's smarter" — it's **reversibility**: if
an action can be replayed (analysis, planning, a re-derivable edit) the AI just
does it; if it's a live change to the shared design or spends money, a human gates
it. (Full tiers: [`docs/04_HUMAN_IN_THE_LOOP.md`](docs/04_HUMAN_IN_THE_LOOP.md).)

## The tools

- **EasyEDA Pro** — schematic + placement, driven by its JavaScript API and read
  back headlessly through the browser (Chrome DevTools Protocol).
- **KiCad** — the **routing and verification engine.** Routing is done here, *not*
  in EasyEDA, because KiCad's `pcbnew`/`kicad-cli` API can script pours, zones,
  stitching, and DRC. EasyEDA's API cannot, so we hand the board to KiCad after
  placement.
- **PADS export** bridges EasyEDA → KiCad, carrying nets and placement intact.

## The golden rule

**You never start a phase until the previous phase passes review.** Every phase
ends in a written verdict — **PASS / CONDITIONAL (numbered fixes) / FAIL** — and a
failing verdict *blocks* the next phase ("place nothing over wrong"). Inside each
phase, the loop is always *generate one unit → review → fix → next.*

---

## Phase 1 — Requirement analysis & feasibility study
The workflow begins when a client provides requirements. **Before any schematic
work,** produce a feasibility study: functional analysis, technical feasibility,
cost estimate, manufacturing feasibility, power budget, hardware architecture,
risk assessment, and complexity estimate. A quick density check (component area ÷
board area) and a current check (any rail needing >~5 A ⇒ a plane ⇒ ≥4 layers)
catch "this won't fit / this can't be 2-layer" in minutes.
**Gate:** feasibility complete; no unquantified requirement. **Human:** approves
the project.

## Phase 2 — BOM planning
Once approved, generate the BOM. Every part is chosen by engineering rules:
**Indian-market availability, LCSC availability, cost optimization, long-term
availability, preferred manufacturers, package compatibility, electrical
compatibility, lead time, manufacturing constraints.** Verify each part by
decoding its manufacturer/LCSC ID against the spec (a fuzzy search once dropped a
12 pF cap and a 2.2 µH inductor into µF slots). **Gate:** BOM fully validated.
**Human:** signs cost/feature trades.

## Phase 3 — EasyEDA project initialization
Create the EasyEDA project, create the schematic **sheets** (one project, multiple
pages — never separate files, or nets won't merge), configure board parameters,
and **select the stackup** (2/4/6-layer) from the feasibility verdict. **Gate:**
project structure + stackup set.

## Phase 4 — Autonomous schematic generation
Using the approved BOM and the EasyEDA API + browser automation + Node.js scripts,
generate the schematic: create/place symbols, wire connections **by net name**,
organize blocks, verify interfaces, follow best practices. Parts are token-matched
(never blindly the first search result); array parts rejected. **Human
intervention only where an engineering decision needs approval.** **Gate:** every
block wired, 0 unmatched pins; run project-wide Annotate.

## Phase 5 — Schematic audit
Before any PCB work, audit the schematic completely: the AI reads the real board
back, **reconstructs the netlist** from wire coordinates, and checks **missing
nets, floating pins, shorts, ERC violations, power integrity, signal integrity,
net-naming consistency, interface validation, datasheet compliance, design
completeness.** This runs in seconds and catches what the eye misses. **Gate:**
all checks pass. *This cheap gate protects every hour of layout downstream.*

## Phase 6 — Component placement planning
PCB placement does **not** start yet. First the **client defines** the physical
constraints: board dimensions, board shape, connector locations, USB location,
sensor positions, MCU location, mounting holes, keep-out regions, mechanical
constraints, and any placement preferences. **Gate:** constraints captured.

## Phase 7 — Placement knowledge graph
Before placing anything, build a placement knowledge graph describing: functional
blocks, component relationships, placement priorities, thermal considerations,
high-current paths, analog/digital separation, EMI-sensitive regions, mechanical
constraints, routing complexity, manufacturing considerations. **Gate:** the graph
is complete — no component is placed before this.

## Phase 8 — Visual placement planning
Generate a **visual placement map** before writing any automation: functional
zones, power zones, signal flow, connector/sensor locations, high-speed regions,
thermal regions, ground strategy, future routing channels. Evaluate it against the
client's requirements and **iterate until it satisfies them.** **Gate:** placement
plan approved.

## Phase 9 — Automated component placement
Once the plan is approved: generate Node.js automation, inject it into EasyEDA,
place all components, and **validate on real pad geometry** (never the placer's own
model). If constraints are violated, repeat until the layout satisfies all of them.
**Gate:** 0 spacing violations + practical + approved. **Human:** approves.

## Phase 10 — Export to KiCad
Routing is **not** done in EasyEDA. Export the PCB in **PADS** (or another
compatible) format, import into KiCad, and **verify the imported board matches the
EasyEDA design** — placement preserved, 0 dropped footprints, sub-µm position
residual. (Mounting holes may not survive the export → restore and re-verify.)
**Gate:** import fidelity verified.

## Phase 11 — AI-assisted routing (in KiCad)
KiCad is the routing engine; routing is AI-assisted automation that considers **IPC
standards, trace-width/current capacity, differential pairs, high-speed signals,
ground returns, EMI reduction, thermal performance, manufacturability, layer
optimization.** Order: planes → hardest criticals first → constrained auto-route →
power pours → **ground pour + stitching last.** Iterate until all design rules are
satisfied. **Gate:** 0 unrouted; DRC-clean vs the board's ruleset (KiCad
`kicad-cli` with the `.kicad_pro` sibling — never a bare board file). **Human:**
go-ahead before routing begins.

## Phase 12 — Final verification
A complete engineering review: **DRC, ERC, manufacturing review, silkscreen
review, assembly review, mechanical review, BOM validation, final documentation.**
Export gerbers/drill/CPL/BOM and **commit the package** (an uncommitted board is one
mistake from gone). **Only then is the project manufacturing-ready.** **Human:**
signs the DFM report and **places the fab order** — the one thing the AI never does.

---

## What makes this different from a traditional EE flow

| Traditional | PCB Flow |
|---|---|
| The schematic *is* the design | Build sheet + net dictionary + rules are the design; geometry is generated |
| Progress = "I drew more" | Progress = a dated PASS/CONDITIONAL/FAIL verdict per phase |
| Verify at the end | A cheap verification gate after **every** phase |
| Trust the tool's "0 errors" | Verify against **real geometry + the correctly-configured DRC** |
| Route in the schematic tool | Placement in EasyEDA, **routing in KiCad** (scriptable pours/DRC) |
| Lose the board file → redo by hand | Regenerate geometry from the intact knowledge layer |
| One engineer, start to finish | AI on the replayable 90%; human owns judgment + the irreversible |
| Every project starts from zero | Every project **inherits** prior learnings (`knowledge/`) |

Nothing here replaces engineering judgment — the human gates exist precisely so the
calls that matter (safety, power sizing, DRC sign-off, ordering) stay with a
person. What the method removes is the *avoidable* waste: drift between spec and
board, layouts built on a wrong schematic, and boards lost because nobody committed
them.

Deep reference for every phase → [`workflow/`](workflow/). Why it's shaped this way
→ [`docs/00_PHILOSOPHY.md`](docs/00_PHILOSOPHY.md). The honest record of what went
wrong → [`docs/13_LESSONS_LEARNED.md`](docs/13_LESSONS_LEARNED.md).
