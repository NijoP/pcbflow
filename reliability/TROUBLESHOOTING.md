# Troubleshooting — For the Engineer

Plain-English answers when something goes wrong. You should rarely need this — the AI
handles most problems automatically and tells you if it needs you. But if you're
stuck, find your symptom below.

**The golden rule:** if something breaks, just tell the AI *"something went wrong —
read the log and fix it."* It will read the log, diagnose, try to recover, and tell
you in plain words what happened and whether you need to do anything.

---

## "The AI says my EasyEDA session expired"
**What it means:** you were signed out of EasyEDA (sessions time out).
**Do this:** log back into EasyEDA in the browser. Then tell the AI *"retry."* It
continues from where it stopped. **Nothing is lost.**

## "It can't connect to EasyEDA / the drawing window"
**What it means:** EasyEDA isn't open, isn't signed in, or a second copy is open.
**Do this:** make sure **one** EasyEDA editor window is open and signed in; close any
extras. Say *"retry."*

## "EasyEDA froze / stopped responding"
**What it means:** the drawing window hit a known glitch.
**Do this:** usually nothing — the AI restarts it automatically and replays the last
step. If it asks, close and reopen EasyEDA and say *"resume."*

## "It says KiCad isn't installed"
**What it means:** the routing/checking tool isn't found.
**Do this:** install KiCad (handbook step 2). You can keep doing everything up to
placement without it. Say *"retry"* once installed.

## "The design-rule check looks too clean / I don't trust it"
**What it means:** a DRC run without the proper rule file reports false "all clear."
**Do this:** the AI always uses the guarded check (`drc.sh`). If in doubt, ask *"re-run
the DRC with the ruleset and show me the report."* Never trust a bare "0 errors."

## "A part couldn't be found"
**What it means:** the library search didn't match your part.
**Do this:** give the AI an **LCSC number** or an exact part name: *"use LCSC C2040
for the regulator."*

## "It says a helper needs something installed" (Node/Python/rsync)
**What it means:** a small software tool is missing.
**Do this:** the AI prints the **exact** command to run — copy it into VS Code's
terminal, run it, and say *"retry."*

## "I closed VS Code / my PC restarted — did I lose work?"
**What it means:** nothing. Your work is saved in your project folder and its history.
**Do this:** re-open the Tracewright folder and say *"continue where we left off on
projects/<your-board>."* The AI resumes at the exact next step.

## "It couldn't publish to GitHub"
**What it means:** your work is saved locally, but the upload needs your sign-in.
**Do this:** sign in to GitHub (a token or the VS Code GitHub login) and say *"push."*
Your work is safe either way.

## "The schematic looks messy / parts aren't neatly aligned"
**What it means:** this is a known, cosmetic limitation of script-drawn schematics —
**it does not affect correctness** (the audit guarantees the wiring). See
[`VULNERABILITY_REPORT.md` §7](VULNERABILITY_REPORT.md).
**Do this:** nudge blocks by hand in EasyEDA if you want it tidier, or continue —
placement and routing are unaffected.

## "Two parts won't fit where I asked"
**What it means:** a mechanical constraint conflicts with the parts.
**Do this:** the AI will ask you to approve moving a part or resizing the board — a
normal engineering trade-off, your call.

## Still stuck?
Tell the AI: *"open the log for this phase and explain the last error to me in plain
terms, then tell me the options."* Every automated step writes a log the AI can read
back (`projects/<board>/.logs/`), so it can always reconstruct what happened.

---
See also: [`RECOVERY_PLAYBOOKS.md`](RECOVERY_PLAYBOOKS.md) (what the AI does behind the
scenes) · [`DEPENDENCY_VALIDATION.md`](DEPENDENCY_VALIDATION.md) (`axon doctor` — run
it if anything feels off).
