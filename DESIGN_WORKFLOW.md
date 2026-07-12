# The AXON Design Method — Step by Step

> **For the electronics engineer reading this repo for the first time.**
> This is how we actually take a hardware product from a client conversation to a
> manufacturable PCB. It's a normal, rigorous EE flow — schematic → placement →
> routing → gerbers — but reorganized around one idea and driven by an AI agent
> working alongside a human engineer. Read this page and you'll understand the
> whole process; the `docs/` folder is the deep reference behind each step.

---

## The one idea to understand first

We treat a PCB project as having two kinds of thing:

- **Knowledge** — the requirements, the net list, the part choices, the design
  rules, the "this is a 4-layer board because of the 10 A motor rail" reasoning.
  This is *authored, reviewed, and version-controlled.* It is the **source code**
  of the board.
- **Geometry** — the schematic drawing, the placement coordinates, the routed
  copper, the gerbers. This is *generated* from the knowledge, and — if the
  knowledge is intact — it can be **regenerated on demand.** It is the **build
  output.**

> **Knowledge is the source. Geometry is the build artifact.**

So the two files that *are* the board are not the schematic — they're two plain
documents: a **build sheet** (every part, every pin, every net) and a **net
dictionary** (every net → every pin that touches it). Get those right and the
schematic, placement, and routing become a build step over them.

Everything else in the method follows from this. (Full rationale:
[`docs/00_PHILOSOPHY.md`](docs/00_PHILOSOPHY.md).)

---

## Who does what

| The **AI agent** does | The **human engineer** does |
|---|---|
| Requirements analysis, architecture, feasibility math | Confirms the brief; signs the constraint verdict |
| BOM research + datasheet verification | Makes cost/feature/UX calls |
| Writes the two source-of-truth docs | Reviews them electrically |
| Generates the schematic (scripts) | Runs the scripts in the EDA tool; runs Annotate |
| Verifies the schematic net-by-net (headless) | Confirms the verdict |
| Computes the placement + routing plan | Approves placement (usability); gives the go-ahead to route |
| Guides routing + runs DRC | Does the interactive routing; signs DRC before fab |
| Packages gerbers/BOM/CPL | **Places the fab order** (never the AI) |

The rule for *who* decides is not "who's smarter" — it's **reversibility**. If an
action can be replayed (analysis, planning, a re-derivable edit), the AI just does
it. If it's a live change to the shared design or spends money, a human gates it.
(Full tiers: [`docs/04_HUMAN_IN_THE_LOOP.md`](docs/04_HUMAN_IN_THE_LOOP.md).)

---

## The tools

- **EasyEDA Pro** — the schematic/PCB tool. It has a JavaScript API (paste-and-run
  "Standalone Scripts") we use to generate schematics, and it can be driven
  headlessly through the browser (Chrome DevTools Protocol) so the AI can read the
  real board back and verify it.
- **Scripts** — a small, board-agnostic engine (part search, passive picking,
  wire-by-net-name) plus a per-board data block. See
  [`templates/section_generator.template.js`](templates/section_generator.template.js).
- **KiCad `kicad-cli`** — used as an independent DRC ground-truth and for
  manufacturing export when needed.

Any of these is swappable — the method is the constant, the tool is the backend.
(Integration details: [`docs/06_EASYEDA_INTEGRATION.md`](docs/06_EASYEDA_INTEGRATION.md),
[`docs/07_BROWSER_AUTOMATION.md`](docs/07_BROWSER_AUTOMATION.md).)

---

## The golden rule of the flow

**You never start a stage until the previous stage passes review.** Every stage
ends in a written verdict — **PASS / CONDITIONAL (with a numbered fix list) /
FAIL** — and a failing verdict *blocks* the next stage. We call this *"place
nothing over wrong."* It sounds obvious; violating it (routing over a schematic
that still had 22 shorts) cost the origin project weeks of thrown-away layout.

And the inner loop inside every stage is always the same:

```
   generate ONE unit  →  review it  →  fix it  →  next unit
```

One unit = one schematic section, one placement region, one routing phase. We
never generate the whole board and review at the end — a bug found late costs the
whole board; a bug found per-section costs one section.

---

## The 10 steps

### Step 0 — Capture the requirements
Turn the brief (a call, a sketch, a PDF) into a **numbered requirement register**.
Every requirement gets a number and a source. Conflicts are surfaced, not quietly
reconciled. **Gate:** nothing left unquantified.
*Watch for:* a dimensional spec that's already impossible — a quick
component-area estimate catches "this won't fit" in five minutes instead of at
layout.

### Step 1 — Architecture & feasibility
Decide the block partition, the power rails, the **board size**, and the **layer
count** — each with the math that forces it. Two calculations do most of the work:
- **Density → size:** `courtyard area ÷ board area × 2`. Below ~25% routes easily on
  2-layer; above ~45% you need 4-layer or an interactive finish.
- **Current → layers:** if any rail's peak current can't be carried by a
  manufacturable trace (~5 A on 1 oz copper), that current must ride a **copper
  plane**, which means ≥4 layers. *You add layers for amps, then use them for
  routing — not the other way around.*

**Gate:** size and layer count justified by numbers. **Human:** signs off board
size (it's a cost/UX call).

### Step 2 — Components & sourcing
Build a BOM where every part is **datasheet-verified** and sourcable, with a second
source noted. Verify a part by decoding its **manufacturer/LCSC ID**, not the
search string (a fuzzy search once dropped a 12 pF cap and a 2.2 µH inductor into
µF slots). Check the boring things that bite: does the module have the right
antenna variant? does the regulator survive a depleted battery? **Human:** makes
the cost/feature trades.

### Step 3 — Write the two source-of-truth docs
Author the **build sheet** and the **net dictionary** in lockstep — they must agree
net-for-net; on conflict, the net dictionary wins. The net dictionary's membership
table (every net → every connected pin) becomes the oracle we verify against later.
**Gate:** the two docs agree; analog ground has exactly one tie point; every IC is
decoupled. *This is the highest-leverage step — get it right and the schematic
generator can be dumb and deterministic.*
(Templates: [`build_sheet.template.md`](templates/build_sheet.template.md),
[`net_connection.template.md`](templates/net_connection.template.md).)

### Step 4 — Generate the schematic, section by section
For each functional block (USB, charger, MCU, each sensor, motors, …), fill a small
CONFIG block — the parts and passives from the build sheet — and run the generator
script in EasyEDA. It searches the library (token-matched, never blindly the first
result), places the parts, and **wires each pin to its net by name.** The human runs
each script and runs project-wide **Annotate** afterward (designators aren't
scriptable). **Gate:** every section placed and wired, zero unmatched pins.

### Step 5 — Verify the schematic (the cheap gate that saves everything)
The AI reads the *real* board back headlessly, **reconstructs the netlist** from the
wire coordinates, and **diffs it against the net dictionary.** Zero shorts, zero
single-pin nets, zero floating pins. This runs in seconds and catches what the eye
misses. **Run it before any PCB work — never as an afterthought.**
(How: [`docs/09_VALIDATION.md`](docs/09_VALIDATION.md).)

### Step 6 — Placement
Partition the board (quiet logic / sensors in the centre / noisy power+motors),
size each part's real courtyard, hug decoupling caps to their IC (≤2 mm), orient
parts to current flow, and put edge parts (USB, connectors, button, battery,
antenna) **on the edge, opening outward.** Then audit spacing on **real pad
geometry** (not the tool's model). **Gate:** zero spacing violations *and* the
layout is practically assemblable — a client judges a board by "can I build and
use this," not by wirelength. **Human:** approves the placement.

### Step 7 — Plan the routing (before drawing any copper)
Produce three machine-readable rulebooks:
- **Design rules** — every net sorted into a class (GND plane, power, motor, USB
  diff pair, gate, analog, signal…) with its width and clearance. *Zero nets left
  unclassed.*
- **Trace-width table** — each net's IPC-2221 current→width; anything needing
  >~5 mm becomes a plane/pour, not a trace.
- **Route sequence** — the **order** of routing: define planes → route the hardest
  critical nets first (diff pairs, fast SPI) → constrained auto-route the bulk →
  and pour ground **last** (pouring early strands open nets).

**Gate:** feasibility scored above threshold; plan frozen.
(Templates in [`templates/`](templates/); strategy in
[`docs/01_METHODOLOGY.md`](docs/01_METHODOLOGY.md).)

### Step 8 — Route the board
Apply the ruleset, then route in the sequence above. The AI drives everything it
can and hands the human a **precise plan** for the parts the tool's API can't
automate (copper pours and fine-pitch escapes are interactive in EasyEDA). Ground
pour and stitching vias go in **last**, collision-checked. **Gate:** zero unrouted,
and **DRC clean against the board's own ruleset in the board's own tool** — never
cross tools (that's a phantom-clean trap). **Human:** gives the go-ahead to start
drawing copper.

### Step 9 — DRC, DFM & manufacturing handoff
Export gerbers (including inner layers), drill, pick-and-place, and BOM; run the
fab's DFM check; **commit the whole package to git** (an uncommitted board is one
mistake away from gone — the origin project lost two finished boards this way).
**Human:** signs the DFM report and **places the fab order** — the one thing the AI
never does.

---

## What makes this different from a traditional EE flow

| Traditional | AXON |
|---|---|
| The schematic *is* the design | Two text docs are the design; the schematic is generated from them |
| Progress = "I drew more" | Progress = a dated PASS/CONDITIONAL/FAIL verdict per stage |
| Verify at the end (ERC/DRC) | A cheap verification gate after **every** stage |
| Trust the tool's "0 errors" | Verify against **real geometry + the correctly-configured DRC** |
| Lose a board file = redo it by hand | Regenerate geometry from the intact knowledge layer |
| One engineer, start to finish | AI on the replayable 90%; human on judgment + the irreversible |

Nothing here replaces engineering judgment — the whole point of the human gates is
that the calls that matter (safety, power sizing, DRC sign-off, ordering) stay with
a person. What the method removes is the *avoidable* waste: drift between the spec
and the board, layouts built on a wrong schematic, and boards lost because nobody
committed them.

---

## Try it on your own board

1. Copy [`templates/`](templates/) into a new project folder.
2. Fill the build sheet and net dictionary from your brief (Steps 0–3).
3. Point an AI agent at [`CLAUDE.md`](CLAUDE.md) and say *"follow the method, build
   the next section."*
4. Work the loop: generate one section → verify → fix → next. Let the AI run the
   replayable work; you own the gates.

The deep reference for every step is in [`docs/`](docs/). If you only read two more
pages, read [`docs/00_PHILOSOPHY.md`](docs/00_PHILOSOPHY.md) (why it's shaped this
way) and [`docs/13_LESSONS_LEARNED.md`](docs/13_LESSONS_LEARNED.md) (the honest
account of what went wrong and how the method fixes it).
