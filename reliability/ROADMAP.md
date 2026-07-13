# Reliability Roadmap

Weaknesses prioritized by severity, then a phased plan to build the self-healing
system. Nothing here is implemented yet — this is the proposal for what to build and
in what order.

---

## Prioritized weaknesses (build the fixes in this order)

| # | Weakness | Sev | Fix | Effort |
|---|---|---|---|---|
| 1 | No environment check before work | S2×many | `pcbflow doctor` preflight | Med |
| 2 | Silent failures / swallowed errors (SC-7) | S1 | `{ok,err}` envelope everywhere + structured logging | Med |
| 3 | Phantom DRC ships bad boards (KI-6) | S1 | make `drc.sh` the only DRC path; hard-fail without ruleset | Low |
| 4 | Uncommitted work lost (ST-1) | S1 | auto-commit each phase output; manifest checkpoint | Low |
| 5 | Renderer hang undetectable (EDA-7) | S1 | hang-timeout + auto tab-reset + replay | Med |
| 6 | Session expiry blocks silently (EDA-1/2) | S2 | 401 detection + re-login prompt + resume | Med |
| 7 | No clean resume after crash (ST-2/5) | S2 | manifest-driven resume | Med |
| 8 | Linux-only automation (ENV-6) | S2 | cross-platform runner; PowerShell/mac recipes | High |
| 9 | Missing-dep crashes mid-task (ENV-*) | S2 | folded into `pcbflow doctor` (#1) | — |
| 10 | Schematic misalignment (§7) | S3 | measured-bbox tidy pass (optional) | Med |

---

## Phase 1 — See everything (highest value, lowest risk) · ✅ BUILT

> **Implemented** in [`../tools/`](../tools/): `doctor.py` (preflight environment
> check) + `pcbflow_log.py` (structured `{ok,err}` logging) + a passing test. Run
> `python3 tools/doctor.py`. See [`../tools/README.md`](../tools/README.md).

Build the two things that turn *invisible* failures into *handled* ones:

1. **`pcbflow doctor`** — the preflight dependency/OS/tool/EasyEDA/AI check
   ([`DEPENDENCY_VALIDATION.md`](DEPENDENCY_VALIDATION.md)). Cross-platform (Node or
   Python). Run manually and at each phase start; hard-gate on critical failures.
2. **Structured logging** — the `{ok,err}` envelope on every wrapped call + the JSONL
   log schema ([`SELF_HEALING.md` §1](SELF_HEALING.md)). One log file per phase.

Outcome: no more cryptic mid-task deaths; every failure is recorded and named.

## Phase 2 — Diagnose & recover the common faults · ✅ BUILT

> **Implemented** in [`../tools/`](../tools/): `diagnose.py` (fault classification),
> `recover.py` (backoff retry + idempotency guard), `state.py` (checkpoint + resume),
> and the KI-6 guard (`automation/kicad/drc.sh` now refuses to run without a ruleset).
> Tests pass. See [`../tools/README.md`](../tools/README.md).

3. **Fault classification** — map each caught error to a `VULNERABILITY_REPORT` id.
4. **Retry wrappers** — backoff for 429/5xx/timeouts, with idempotency guards
   ([`SELF_HEALING.md` §3](SELF_HEALING.md)).
5. **The high-value guards:** `drc.sh`-only DRC (#3), auto-commit per phase (#4).
6. **Autonomous resume** — manifest-driven ([`SELF_HEALING.md` §4](SELF_HEALING.md)).

Outcome: the top-5 S1 risks become auto-recovered or safely checkpointed.

## Phase 3 — Recover the hard cases + human-friendly layer · ✅ BUILT

> **Implemented** in [`../tools/`](../tools/): `heal.py` (the self-healing engine +
> the What/Why/Tried/Result/Action human-friendly layer + fault→strategy registry) and
> `recovery.py` (renderer reset, session re-auth, Chrome attach/singleton, edit-lock,
> KiCad import checks). Tests pass (`test_heal.py`, 6/6). **The browser/KiCad recovery
> logic needs validation against a live EasyEDA/KiCad session** before production use;
> the pure decision logic and KiCad checks are fully tested.

7. **Renderer-hang auto-reset** (EDA-7) and **session re-auth + resume** (EDA-1/2).
8. **Chrome/CDP recovery** (Singleton clear, relaunch, edit-lock resolution).
9. **KiCad import recovery** (footprint remap, hole restore).
10. **Human-friendly error layer** — the What/Why/Tried/Result/Action template
    ([`SELF_HEALING.md` §5](SELF_HEALING.md)) on every escalation.

Outcome: an engineer sees plain-English instructions, never a stack trace.

## Phase 4 — Cross-platform hardening · ✅ BUILT

> **Implemented** in [`../tools/`](../tools/): `platform_utils.py` (per-OS Chrome/
> profile/lock resolution + min versions), `launch_easyeda.py` (portable Chrome
> launcher replacing the bash rsync recipe; `--dry-run` testable anywhere), and
> `drc.py` (portable DRC with the KI-6 ruleset guard, replacing the bash `drc.sh`).
> Tests pass (`test_platform.py`). The launch itself still needs validation on
> macOS/Windows; the path logic and guards are tested cross-platform.

11. Port the Bash pieces (`drc.sh`, the Chrome launch recipe) to a cross-platform
    runner; add macOS + Windows/PowerShell recipes; the doctor selects per-OS.
12. Version pinning/checks for Chrome, KiCad, Node, Python.

Outcome: works on Ubuntu, macOS, and Windows, not just Linux.

## Phase 5 — Optional polish · ✅ BUILT

> **Implemented** in [`../tools/tidy_schematic.py`](../tools/tidy_schematic.py): the
> pure de-collision + grid-snap algorithm for the §7 alignment limitation, fully
> tested (`test_tidy.py`). The live measure (`getPrimitivesBBox`) and apply
> (`setState`) need an EasyEDA session; the geometry is done and tested offline.

13. Schematic **measured-bbox tidy pass** (the §7 alignment limitation) — de-collide
    symbols and snap blocks to a bus grid. Cosmetic; do only if engineers ask.

---

## Recommendations for robustness (for engineers with minimal software experience)

- **Build Phase 1 first, always.** The single biggest reliability win for a beginner
  is *never seeing a cryptic error* — the doctor + logging deliver that with low risk.
- **Make the safe path the only path.** `drc.sh`-only DRC and auto-commit-per-phase
  remove two S1 failure classes by construction, not by discipline.
- **Prefer auto-recovery; escalate in plain English.** Every escalation answers
  What/Why/Tried/Result/Action — an engineer should always know if *they* need to act.
- **Treat the manifest as the checkpoint and git as the safety net.** Commit each
  phase's output; then "closed VS Code" and "PC restarted" are non-events.
- **Be honest about limits.** Where automation is Linux-only or a schematic isn't
  perfectly tidy, say so up front (the troubleshooting guide already does) — surprises
  erode trust more than known limitations do.
- **Ship the doctor with the repo.** A new engineer's first command should be `pcbflow
  doctor`, and it should tell them exactly what to install before anything can fail.

---

## What was NOT changed

Per the brief, **no PCB features or automation were implemented** in this audit. This
is the design and the plan. Recommended next action: implement **Phase 1** (doctor +
structured logging) — the highest-value, lowest-risk step — on your go-ahead.
