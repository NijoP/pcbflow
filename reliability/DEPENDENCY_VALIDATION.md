# Dependency Validation — The Preflight "Doctor"

A design for `pcbflow doctor`: a single check the engineer (or the AI) runs **before any
work starts**, which verifies the whole environment, explains any problem in plain
English, and refuses to start if something critical is missing. This closes every
`ENV-*` and most `BR-*` first-run failures.

> **Status: ✅ built** — implemented as [`../tools/doctor.py`](../tools/doctor.py).
> Run `python3 tools/doctor.py`. The check table below is the spec it implements.

---

## What it does

```
$ pcbflow doctor
PCB Flow environment check ───────────────────────────────
  ✅ Operating system     Linux (supported)
  ✅ Git                   2.43.0
  ✅ Node.js               v20.11 (need ≥18)
  ✅ Python                3.11 (need ≥3.9)
  ✅ Chrome                126 — remote debugging OK
  ⚠️  KiCad                not found on PATH
      → Routing & DRC need KiCad. Install: https://kicad.org/download
        (you can still do phases 1–9 without it.)
  ✅ VS Code + AI agent    Claude Code detected
  ✅ EasyEDA               reachable, signed in
  ❌ rsync                 not installed
      → Needed to open EasyEDA for automation.
        Ubuntu: sudo apt install rsync
─────────────────────────────────────────────────────
  1 critical issue — fix it before starting. 1 warning.
```

**Green** = ready. **Yellow** = works but limited (e.g. no KiCad yet — fine until
routing). **Red** = blocks work; execution stops with the exact fix.

---

## The check table

| Check | Critical? | Pass condition | If it fails, tell the engineer |
|---|---|---|---|
| **OS** | — | Linux / macOS / Windows detected | which OS; which recipe applies (see OS matrix below) |
| **Git** | Yes | `git --version` ≥ 2.x, identity set | install Git; run the two `git config` lines (handbook 02) |
| **Node.js** | Yes* | `node -v` ≥ 18 | install Node LTS from nodejs.org |
| **Python** | Yes* | `python3 --version` ≥ 3.9 | install Python 3; note `python` vs `python3` |
| **Node deps** | Yes* | install step run | run the one-line install the doctor prints |
| **Python deps** | Yes* | install step run | run the one-line install the doctor prints |
| **Chrome** | Yes | binary found | install Chrome |
| **Chrome debug** | Yes | can bind `--remote-debugging-port` | close other Chrome; the doctor offers to launch it correctly |
| **rsync** | Yes | present (Linux/macOS) | `apt/brew install rsync`; on Windows use the alt profile method |
| **KiCad** | No (until ph.10) | `kicad-cli version` works | install KiCad; phases 1–9 still fine |
| **VS Code + AI** | Yes | an AI assistant responds | install/sign into Claude Code / Codex / OpenCode |
| **EasyEDA reachable** | Yes (from ph.3) | editor URL loads | check network |
| **EasyEDA signed in** | Yes (from ph.3) | no login DOM on the editor tab | sign into EasyEDA |
| **AI config** | Yes | `CLAUDE.md`/`AGENTS.md` present & readable | you're in the PCB Flow folder? re-clone if missing |

\* required once automation actually runs (phases 3+). Phases 1–2 (feasibility, BOM)
need only VS Code + the AI.

---

## OS compatibility matrix

The single biggest portability gap (ENV-6). The doctor detects the OS and selects the
right recipe; where a recipe doesn't exist yet, it says so honestly.

| Capability | Linux | macOS | Windows |
|---|---|---|---|
| Chrome profile clone (`rsync`) | ✅ recipe exists | ⚠️ path differs (`~/Library/Application Support/Google/Chrome`) | ❌ no `rsync`/Singleton model — needs a PowerShell recipe |
| `rm Singleton*` lock clear | ✅ | ✅ | ❌ (different lock model) |
| `--remote-debugging-port` launch | ✅ | ✅ (app path differs) | ✅ (path/quoting differ) |
| `drc.sh` (Bash) | ✅ | ✅ | ❌ needs a `.ps1` equivalent |
| Path handling | `/`, spaces | `/`, spaces | `\`, drive letters, PowerShell quoting |

**Recommendation:** ship the doctor as **cross-platform from day one** (Node or Python,
not Bash) so it runs everywhere, and have it clearly report "this automation step is
currently Linux/macOS-only" rather than failing cryptically on Windows. Porting the
Bash pieces (`drc.sh`, the launch recipe) to a cross-platform runner is a Phase-4
roadmap item.

---

## Where it plugs in

- **Manually:** the engineer runs `pcbflow doctor` (handbook step 2 ends with it).
- **Automatically:** the AI runs the relevant subset **at the start of each phase**
  (e.g. it checks KiCad only when entering Phase 10, so a beginner isn't blocked early
  by a tool they don't need yet).
- **As a gate:** if a *critical* check for the current phase fails, the AI **stops**
  and explains — it does not push forward into a guaranteed failure.

## Why this matters most for beginners

Every `ENV-*` failure today shows up as a cryptic mid-task error. The doctor turns all
of them into a checklist with fixes, **before** any work is attempted — which is
exactly the "senior engineer checks the bench before starting" behaviour the user
wants. It is the highest-value, lowest-risk thing to build first.
