# Self-Healing Architecture

The design for making Tracewright recover from failures on its own. Four parts: a **logging
schema**, a **failure→recovery matrix**, **retry rules**, and **autonomous resume** —
plus the **human-friendly error** layer that sits on top so an engineer always
understands what happened.

---

## The loop

```
  run a step ─► wrap it ─► did it fail?
                              │ no ──► record success, advance
                              │ yes
                              ▼
        LOG (structured) ─► DIAGNOSE (classify) ─► consult knowledge/learning-db
                              │
                              ▼
        is it safe & known to auto-recover?
             │ yes ─► RECOVER (retry / fallback) ─► worked? ─► resume
             │                                        │ no
             │ no  ─────────────────────────────────►│
             ▼                                        ▼
        EXPLAIN in plain English  +  say exactly what manual action is needed
```

The principle: **the AI is a background senior engineer.** It only interrupts the
electronics engineer when recovery is genuinely impossible — and even then it hands
over a plain-English explanation, not a stack trace.

---

## 1. Logging schema

Every automated step emits one **structured log record** (JSON Lines, appendable) to
`projects/<board>/.logs/<phase>.jsonl`, plus a human-readable mirror. One record per
attempt captures exactly the fields an audit needs:

```json
{
  "ts": "2026-07-13T18:04:12Z",       // timestamp
  "project": "door-sensor",
  "phase": "04-schematic-generation",  // current workflow stage
  "step": "wire block U3 (IMU)",
  "command": "cdp eval clean_engine.js + s04.js",  // what was executed
  "script": "s04_imu.js",              // generated script (path/name)
  "stdout_tail": "...OK U3 <- LSM6DS3TR-C",
  "status": "recovered",               // ok | failed | recovered | escalated
  "error": {                            // present only on failure
    "class": "EDA-1",                  // maps to VULNERABILITY_REPORT id
    "http": 401,
    "message": "Unauthorized",
    "stack": "…"                       // full trace for the AI
  },
  "recovery": {
    "attempted": "re-auth prompt + retry",
    "attempts": 1,
    "result": "success"
  },
  "human_message": "The EasyEDA session had expired; you logged back in and the step continued."
}
```

**Two audiences, one record:** the AI reads `error.class`/`stack`; the engineer reads
`human_message` and `status`. A rendered log line looks like:

```
18:04:12  door-sensor · schematic · wire U3   ✅ recovered
          → EasyEDA session had expired; re-authenticated and continued (1 retry).
```

Design rules: **never swallow an error** (every wrapped call returns `{ok,err}` — see
SC-7); log *before* attempting recovery (so a hang still leaves a trace); one file per
phase so resume can find the last good step.

---

## 2. Failure → recovery matrix

The core table the healing engine acts on. (Full per-subsystem steps in
[`RECOVERY_PLAYBOOKS.md`](RECOVERY_PLAYBOOKS.md).)

| Failure | Detection | Auto-recovery | Retry | Fallback | Notify human? |
|---|---|---|---|---|---|
| EDA-1/2 session expired (401) | HTTP 401 / login DOM | prompt re-login, then retry | 1 after login | pause phase, resume on login | **Yes** (login) |
| EDA-5 rate limit (429) | HTTP 429 | exponential backoff | 3× (1s,4s,16s) | slow the part-search cadence | only if exhausted |
| EDA-6 / 500 server | HTTP 5xx | backoff + retry | 3× | wait & resume | only if exhausted |
| EDA-7 renderer hang | eval timeout > N s | `Target.createTarget`+`closeTarget`, reload, resume | 1 | reopen project, replay unsaved step | only if reload fails |
| EDA-10 part not found | empty search / no token match | broaden query; try LCSC id; try alt package | 2 | ask engineer to pick a part | if no match |
| EDA-12 unsaved lost | save失败 / no `done()` ack | save immediately; re-run last block | 1 | replay from manifest checkpoint | only if replay fails |
| EDA-13/14 stale read | FLOAT nets / same-eval read | wait, re-`getAll()` in fresh eval | 2 | — | no |
| BR-2 can't attach | no `:9222` socket | relaunch Chrome with debug flags | 2 | full profile re-clone | if relaunch fails |
| BR-3 logged out | login DOM on load | re-rsync logged-in profile; prompt login | 1 | ask engineer to sign in | **Yes** |
| BR-4 Singleton lock | launch error | `rm Singleton*`, relaunch | 1 | kill stray Chrome, retry | no |
| BR-5 edit-lock | write rejected / lock banner | close the other session, retry | 1 | ask engineer to close duplicates | if unresolved |
| KI-2 dropped footprints | count mismatch | remap known footprints; restore holes | 1 | list missing for engineer | if unmapped remain |
| KI-6 phantom DRC | no `.kicad_pro` sibling | copy ruleset via `drc.sh`, re-run | 1 | — | no |
| SC-2 missing dep | import error | run the install step | 1 | print exact install cmd | if install fails |
| SC-3 timeout | no result in N s | retry once with longer budget | 1 | escalate | if 2nd times out |
| SC-6 retry exhausted | max attempts hit | — | — | stop, checkpoint, explain | **Yes** |
| ST-1 uncommitted | dirty tree at phase end | auto-commit the phase output | — | — | no |
| ST-2 interrupted | manifest phase ≠ done | resume from last good step | — | replay pending step | no |

---

## 3. Retry rules

- **Exponential backoff** for transient/network faults (429, 5xx, timeouts): 1s → 4s
  → 16s, max 3 attempts, with jitter.
- **Idempotency first.** Only auto-retry a step that is safe to repeat. Generation and
  placement scripts must be **re-runnable without duplicating** (guard: check if the
  block already exists before creating). Non-idempotent steps (SC-8) get a
  *checkpoint-and-replay*, not a blind retry.
- **Never auto-retry a live write that could double-apply** without an idempotency
  guard — that turns one failure into two problems.
- **Cap and escalate.** After max attempts, stop, write a checkpoint, and explain.
  Silent infinite retry (SC-4) is banned — every loop has a max and a timeout.

---

## 4. Autonomous resume

State that survives a crash lives in two places already: the committed **git history**
(geometry) and the **`project.yaml` manifest** (current phase + per-phase verdicts +
open steps). Resume is therefore deterministic:

1. On start, read `project.yaml` → the current phase and the last `PASS` verdict.
2. Compare against the live board / committed files to find the **last completed
   step** (the manifest is the checkpoint; the board is the ground truth — verify,
   don't trust blindly, per ST-4).
3. Identify **pending** work (a phase started but not `PASS`) and any **temp files**
   (`.logs/*.jsonl`, generated scripts) that indicate an in-flight step.
4. **Replay only the incomplete step** — never redo completed, committed work.
5. Announce: *"Resuming door-sensor at Phase 6, step 'place motor block' — the
   previous step (schematic audit) passed and is committed."*

The rule that makes this safe: **commit each phase's output when it passes** (ST-1
mitigation). Then "what's committed" == "what's done," and resume can trust it.

---

## 5. Human-friendly errors

Every escalation is translated from a technical fault into the five things an engineer
needs. The template:

> **What happened** · **Why** · **What I tried** · **Did it work** · **What you need
> to do** (if anything).

Examples:

| Raw error | What the engineer sees |
|---|---|
| `HTTP 401 Unauthorized` | *"Your EasyEDA session expired. I paused the schematic step. **Please log back into EasyEDA;** I'll continue automatically from where we stopped — no work is lost."* |
| `ECONNREFUSED :9222` | *"I couldn't connect to the EasyEDA window. I tried relaunching it twice. **Please make sure EasyEDA is open and you're signed in,** then say 'retry'."* |
| `kicad-cli: command not found` | *"KiCad's command-line tool isn't installed or isn't on the PATH. I can't run the design-rule check without it. **Install KiCad (handbook step 2)**, then say 'retry'."* |
| renderer eval timeout | *"The EasyEDA drawing window stopped responding (a known glitch). I restarted it and replayed the last step — **it recovered, nothing lost.**"* |
| `429 Too Many Requests` | *"EasyEDA asked me to slow down. I waited and retried; it's continuing now. No action needed."* |

The engineer **never** sees `401`, a stack trace, or a script path unless they ask —
those go to the log for the AI.

---

## What this buys a non-software engineer

Almost every S1/S2 failure becomes either an **invisible auto-recovery** or a **single
plain-English instruction** ("log back in", "install KiCad", "close the other EasyEDA
tab"). The engineer debugs electronics, not software. The build order to make it real
is in [`ROADMAP.md`](ROADMAP.md).
