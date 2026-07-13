# 15 · Roadmap

Where Tracewright goes next, ordered by leverage. Each item names the gap it closes and the
smallest useful version.

---

## Near-term (harden what exists)

**RM1 · Ship the templates as runnable code.**
The `templates/` are currently schemas + a JS engine skeleton. Turn the engine into
an installable package (`axon-eda`) with the board-agnostic core (`pick`,
`pickPassive`, `wirePins`, `pinDir`, `cdp.py`, `recon.py`) so a new board imports it
instead of copy-pasting.

**RM2 · A `drc.sh`-style wrapper per supported tool.**
Codify "the board's own tool + its own ruleset" as a script (KiCad done; add an
EasyEDA-DRC driver) so the phantom-DRC trap is structurally impossible.

**RM3 · A source-of-truth linter.**
Cross-check `build_sheet.md` ↔ `net_connection.md` automatically: net-name parity,
membership completeness, single-tie analog ground, every IC decoupled. A phase-3
gate that runs in CI.

**RM4 · Congestion + IPC-2221 as a library.**
Extract the trace-width solver and 2 mm-bin congestion grid into a callable module
that emits `trace_width_table.json` + `congestion_grid.json` from a netlist.

---

## Mid-term (widen coverage)

**RM5 · Multi-tool backends.**
Generalize the "EDA tool = compiler backend" idea to a pluggable backend interface:
EasyEDA (scriptable + CDP), KiCad (`pcbnew` + `kicad-cli`), and a KiCad-native
schematic path that sidesteps the pour/route API wall entirely. Same knowledge
layer, swappable backend.

**RM6 · A placement backend that closes the practical-usability gap.**
Encode the "edge parts open outward, sensors share axis, noisy/quiet partition"
constraints as first-class placement objectives so the *practical* review is fewer
surprises.

**RM7 · Learning KB → agent-definition sync.**
Automate appending new learning-KB entries into the relevant agent system prompts so
lessons propagate to future invocations without manual copy.

**RM8 · Feasibility scoring as a standard rubric.**
Turn the ad-hoc "74/100" into a documented rubric (density, congestion, current
margin, layer fit, fine-pitch count) so scores are comparable across boards.

---

## Long-term (the ambition)

**RM9 · Close the routing loop where the tool allows it.**
KiCad's scriptable pours/zones make the pour+stitch phase automatable in a way
EasyEDA's API does not. A KiCad-native routing-execution backend could push the
Tier-4 boundary back to just the fine-pitch escapes.

**RM10 · A board "recompile" command.**
Given intact knowledge (`build_sheet`, `net_connection`, rules, placement), regenerate
the schematic and re-derive geometry end-to-end — making Principle 1 ("geometry is
regenerable") literally executable, and turning a lost board into a `make` away.

**RM11 · Cross-project knowledge graph.**
The KG in [`03`](03_KNOWLEDGE_GRAPH.md) is currently one project's distillation. As
more boards run through Tracewright, promote board-specific instances into a shared,
queryable engineering knowledge graph — the world model behind the framework.

---

## Explicitly out of scope

- **Autonomous fab ordering** — always human (Tier 6). Never automate spending money
  on physical goods.
- **Replacing the engineer's judgment on safety-critical calls** — the AI computes
  and recommends; a human signs power-path, protection, and DRC-before-manufacturing.

The north star: **make the knowledge layer so complete that geometry is a build
step you can re-run — and make the human's remaining work only the judgment and the
irreversible acts that should stay human.**
