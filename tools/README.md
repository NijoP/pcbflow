# tools/ — Reliability Tools (Phase 1)

The first pieces of the [self-healing system](../reliability/README.md). Pure
Python 3 standard library — **nothing to install**. These make failures *visible* and
*explained* instead of cryptic.

## `doctor.py` — the preflight environment check

Run it before starting work (or any time something feels off). It checks your OS,
tools, and AXON setup, and tells you in plain English how to fix anything missing.

```bash
python3 tools/doctor.py           # readiness to get started (phases 1–2)
python3 tools/doctor.py --phase 4 # readiness up to a given workflow phase
python3 tools/doctor.py --all     # readiness for the whole pipeline (needs KiCad)
python3 tools/doctor.py --json    # machine-readable (for the AI)
python3 tools/doctor.py --ascii   # plain symbols if your terminal lacks emoji
```

It checks: operating system · Python · Git (+ identity) · AXON config files · Node.js ·
Chrome · rsync · VS Code · EasyEDA reachability · KiCad. Tools you don't need yet
(e.g. KiCad before phase 10) show as a note, not a blocker. **Exit code 0 = ready;
1 = a required tool is missing** — so the AI can gate on it automatically.

Design: [`../reliability/DEPENDENCY_VALIDATION.md`](../reliability/DEPENDENCY_VALIDATION.md).

## `axon_log.py` — structured logging

Gives every automation step two safeguards:

- **The `{ok, err}` envelope** — a step's success or failure is returned as *data* and
  logged, so an error is never silently swallowed.
- **The JSONL schema** — one record per attempt (timestamp, phase, step, command,
  error class, stack, recovery, human message) written to
  `projects/<board>/.logs/<phase>.jsonl`, readable by both the AI and you.

Read a phase log in plain English:
```bash
python3 tools/axon_log.py render projects/<board>/.logs/<phase>.jsonl
```

Design: [`../reliability/SELF_HEALING.md`](../reliability/SELF_HEALING.md) §1.

## `test_axon_log.py` — proof it works

```bash
python3 tools/test_axon_log.py    # PASS = envelope never swallows, schema correct
```

## `diagnose.py` — classify a failure (Phase 2)

Turns a raw error into a known fault class + plain-English explanation + whether it's
safe to retry.
```bash
python3 tools/diagnose.py "kicad-cli: command not found"
python3 tools/diagnose.py --http 401 "Unauthorized"
python3 tools/diagnose.py --log projects/<board>/.logs/<phase>.jsonl   # last failure
```

## `recover.py` — retry safely (Phase 2)

`retry(fn, ...)` retries transient faults (rate limits, timeouts, server hiccups) with
backoff, but **refuses to re-run a non-idempotent live write** (a failed write must not
double-apply). `safe_run(logger, step, fn)` combines retry + structured logging.

## `state.py` — checkpoint & resume (Phase 2)

```bash
python3 tools/state.py checkpoint <project> <phase>   # commit a phase's work (ST-1)
python3 tools/state.py resume <project>               # find where to pick up (ST-2/5)
```
`checkpoint` commits so work can never be lost; `resume` reads the manifest + git and
tells you the exact next step without repeating completed work.

Plus a hardened guard: `automation/kicad/drc.sh` now **refuses to run without a
ruleset** (`.kicad_pro`), making the phantom-DRC failure (KI-6) impossible by
construction.

## Tests

```bash
python3 tools/test_axon_log.py       # Phase 1: logging envelope + schema
python3 tools/test_reliability.py    # Phase 2: diagnose + retry + idempotency
```

## `heal.py` + `recovery.py` — self-healing engine (Phase 3)

`heal(logger, step, action, recoveries=...)` runs a step and, on failure, diagnoses it,
runs the mapped recovery, and either recovers-and-retries or **escalates with a
plain-English message** (What happened / Why / What I tried / Result / What you need to
do). `recovery.py` provides the per-subsystem strategies (renderer reset, session
re-auth, Chrome attach/singleton, edit-lock, KiCad import checks) with injectable live
operations, so an engineer never sees a stack trace.

> The browser/KiCad recovery **logic** is tested with injected dependencies; the **live
> operations** (CDP tab reset, Chrome relaunch, pcbnew edits) need validation against a
> real EasyEDA/KiCad session before you rely on them.

## Tests

```bash
python3 tools/test_axon_log.py       # Phase 1: logging envelope + schema
python3 tools/test_reliability.py    # Phase 2: diagnose + retry + idempotency
python3 tools/test_heal.py           # Phase 3: heal engine + humanize + recovery checks
```

## What's next

Phases 1–3 are built. Phases 4–5 (cross-platform hardening for Windows/macOS; the
optional schematic-alignment tidy pass) are in
[`../reliability/ROADMAP.md`](../reliability/ROADMAP.md).
