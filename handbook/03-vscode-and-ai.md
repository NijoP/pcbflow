# 03 — VS Code & Your AI Assistant

**For:** electronics engineers · **Software knowledge needed:** a little, explained here.

This page shows how to open the workspace and how to work with the AI. This is the
core skill in Tracewright — everything else is engineering you already know.

## Open the workspace

1. Get a copy of Tracewright on your computer (the AI can do this for you, or use VS Code's
   *Clone Repository* with the repository address).
2. In VS Code: **File → Open Folder →** choose the Tracewright folder.
3. Open the AI assistant panel (Claude Code / Codex / OpenCode — however your
   assistant opens; usually a side panel or a command).

That's it. The assistant automatically reads the instruction files in the repo
(`CLAUDE.md`, `AGENTS.md`) and the step files in `workflow/`, so it already knows the
Tracewright method.

## How the AI actually works (in plain terms)

The AI reads **Markdown documents** (the `.md` files in this repo) the way you'd read
a lab manual. Those documents tell it the engineering process, the rules, and what
each step should produce. When you give it a task, it:

1. reads the relevant step in [`workflow/`](../workflow/) and the rules in
   [`knowledge/`](../knowledge/),
2. does the work (research, drawing, checking) using the tools,
3. shows you the result **and its own check of that result**,
4. waits for your approval before doing anything that changes the live design.

You never see APIs or scripts unless you ask. You see engineering results and
decisions.

## How you talk to it

Just write in plain English, like briefing a colleague. Good messages are specific:

- 👍 *"Start a new project called door-sensor. It's a battery-powered PIR sensor that
  sends BLE. Do the feasibility study."*
- 👍 *"The 3.3 V regulator you picked is out of stock — choose an in-stock
  alternative and update the BOM."*
- 👍 *"Approve the placement, but move the USB connector to the short edge."*
- 👎 *"Do the board."* (too vague — say what and which stage)

## Approving decisions

At each checkpoint the AI presents a result and a **verdict** — PASS, or CONDITIONAL
(with a numbered list of things to fix), or FAIL. You either:

- say *"approved, continue"*, or
- point at the item you want changed.

The AI will **stop and ask** before it draws copper, changes the live board, or does
anything it can't undo. It will **never** place a manufacturing order.

## Continuing after you close VS Code

Your work is saved in your **project folder** (`projects/<your-board>/`) and in the
project's `project.yaml` file, which records the current step and every decision. To
resume, just re-open the folder and tell the AI *"continue where we left off on
projects/<your-board>."* It reads the record and picks up the exact next step.

## Reusing a past project

Because each board's decisions are saved, and because the AI writes lessons into
[`knowledge/`](../knowledge/), your next board starts smarter. To reuse a design as a
starting point, tell the AI *"start a new project based on projects/<old-board>."*

## Common mistakes

- Expecting the AI to guess vague requirements — be specific.
- Approving a checkpoint without reading the AI's verdict — read the numbered items.
- Editing files by hand that the AI manages — let it drive; you review.

## Checklist

- [ ] I opened the Tracewright folder in VS Code.
- [ ] My AI assistant is open and responding.
- [ ] I know how to give a task and how to approve a checkpoint.
- [ ] I know how to resume: re-open the folder and say "continue."

---
◀ [02 — Installing the tools](02-installing-tools.md) · Next ▶ [04 — Creating your first project](04-your-first-project.md)
