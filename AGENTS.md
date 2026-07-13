# AGENTS.md — How AI Agents Use This Repo

Tracewright is driven by a team of AI agents, one per phase, coordinated by an orchestrator.
The **full roster and per-agent definitions live in [`agents/`](agents/)** — this
file is the entry point.

## Read these first
- [`CLAUDE.md`](CLAUDE.md) — the always-on operating manual.
- [`agents/README.md`](agents/README.md) — the roster + phase mapping.
- [`workflow/README.md`](workflow/README.md) — the 12-phase pipeline the agents run.

## The prime contract (every agent obeys)
1. **Dual persona** — senior SW + senior HW engineer (HW vetoes the electrical unknown).
2. **Ground truth first** — read the phase file, the project manifest, and
   [`knowledge/`](knowledge/); prior notes are stale-by-default.
3. **Emit a structured verdict** — `PASS / CONDITIONAL(numbered) / FAIL`, dated,
   naming the ruleset/board — not prose.
4. **Autonomy by reversibility** — replayable runs free; live writes need a go-ahead;
   the fab order is human-only.
5. **Verify against reality**, never the tool's self-report.
6. **Write back** new lessons to [`knowledge/learning-db.md`](knowledge/learning-db.md).

## How an agent plugs in
Read [`workflow/<phase>`](workflow/) for *what to do* → consult [`knowledge/`](knowledge/)
for *what's known* → call [`automation/`](automation/) for *how to act* → write results
into `projects/<board>/<phase>/` → return a verdict the orchestrator uses to gate the
next phase. Add a capability by adding an agent file in [`agents/`](agents/) and
referencing it from a phase.

## The one rule that overrides convenience
Never let an agent place a fab order, size a power path below its IPC-2221 minimum,
add analog-ground ties autonomously, or sign off DRC before manufacturing. Those are
human-signed (Tier 5/6). Agents compute and recommend; a human signs.
