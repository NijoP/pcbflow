# PCB Flow Reliability & Self-Healing

This section is an **audit and a design**, not implemented code (yet). It maps every
way the workspace can fail, judges how well the system currently detects and recovers,
designs a self-healing architecture, and lays out a prioritized roadmap to build it.

**Goal:** the workspace should behave like a senior software engineer running in the
background — **detect, diagnose, recover from, and explain problems automatically**,
so an electronics engineer almost never has to debug software.

## The self-healing loop (target behaviour)

```
   a step runs
       │
       ▼
   ┌─ DETECT ──► LOG ──► DIAGNOSE ──► RECOVER ──► EXPLAIN ──► RESUME ─┐
   │  (did it   (struct-  (classify   (retry /    (plain-     (continue │
   │   fail?)    ured)     the fault)  fallback)   English)   from last │
   │                                     │                    good step)│
   │                                     ▼                              │
   └──────────────  escalate to human ONLY if recovery impossible ──────┘
```

## What's in here

| Doc | What it gives you |
|---|---|
| [`VULNERABILITY_REPORT.md`](VULNERABILITY_REPORT.md) | every failure point, per subsystem, ranked by severity + whether we can currently detect/recover it |
| [`SELF_HEALING.md`](SELF_HEALING.md) | the architecture: logging schema, failure→recovery matrix, retry rules, autonomous resume, human-friendly errors |
| [`DEPENDENCY_VALIDATION.md`](DEPENDENCY_VALIDATION.md) | the "preflight doctor" that checks the environment before work starts |
| [`RECOVERY_PLAYBOOKS.md`](RECOVERY_PLAYBOOKS.md) | step-by-step recovery for each subsystem (EasyEDA, KiCad, Chrome, Node, Python, Git, VS Code…) |
| [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | engineer-friendly "you saw X → here's what it means → do this" |
| [`ROADMAP.md`](ROADMAP.md) | weaknesses prioritized by severity + a phased plan to build the self-healing system |

## Severity scale (used throughout)

| Sev | Meaning | Example |
|---|---|---|
| **S1** | Blocks all work, or risks losing work | uncommitted board lost on crash; renderer hard-hang |
| **S2** | Blocks the current phase | EasyEDA login expired; KiCad import fails |
| **S3** | Degrades quality or forces a manual step | schematic misalignment; a flaky retry |
| **S4** | Cosmetic / minor | a noisy log line |

**Likelihood:** High / Med / Low. **Detectable now?** does the current system notice
the failure. **Auto-recoverable now?** can the AI fix it without a human today.

## Status

Audit + design complete. **Nothing here is implemented in the live workflow yet** —
the build order is in [`ROADMAP.md`](ROADMAP.md). Recommended first build: the
**preflight doctor** + **structured logging** (Phase 1), which together eliminate the
majority of "why did it break?" moments for a non-software engineer.
