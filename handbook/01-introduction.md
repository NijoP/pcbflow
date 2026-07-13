# 01 — Introduction

**For:** electronics engineers · **Software knowledge needed:** none.

## What Tracewright is

Tracewright is a **workspace** you open in a code editor, plus an **AI assistant** that
helps you design a PCB. Think of the AI as a very fast junior engineer who has read
every datasheet and never gets tired of checking nets — but who always asks you
before making a real decision.

You don't run a program or write code. You **talk to the AI in plain English**, and
it drives the design tools (EasyEDA and KiCad) for you.

## The one idea that makes Tracewright work

A PCB project has two kinds of thing:

- **Knowledge** — the requirements, the parts list, the net list, the design rules,
  and *why* each choice was made. This is the real "source" of your board.
- **Geometry** — the schematic drawing, the placed components, the routed copper.
  This is *produced* from the knowledge, and can be produced again if needed.

Tracewright keeps the **knowledge** safe and organized, and lets the AI **generate the
geometry** from it. If a drawing is ever lost, it can be regenerated. Your thinking
is what's protected.

You don't have to manage this — it's just why the workspace is organized the way it
is.

## Who does what

| You decide | The AI does |
|---|---|
| What the product must do | The feasibility study and the math |
| Which parts to use (final say) | Part research, availability, datasheets |
| Board size, shape, connectors | Drawing the schematic, placing parts |
| Whether a layout is practical | Checking the schematic and placement |
| Go-ahead to route | Routing and design-rule checks |
| **Ordering the board** | Preparing the manufacturing files |

**The rule of thumb:** if a task can be re-done when it's wrong (analysis, drawing,
checking), the AI just does it. If it changes the live design or can't be undone,
the AI stops and asks you. **The AI never orders a board.**

## Which tool does what

- **EasyEDA** — draws the **schematic** and holds the **component placement**.
- **KiCad** — does the **routing** and the final **design checks**.
- The AI moves your board from EasyEDA to KiCad at the right time and keeps them
  matched. You don't manage this handoff.

## What a session feels like

1. You tell the AI what you're building.
2. It produces the next step (say, a feasibility study or a schematic block).
3. It shows you the result and its own check of that result.
4. You approve, or ask for a change.
5. It moves to the next step.

That loop repeats from requirements to manufacturing.

## Common misunderstandings

- *"I need to learn to code."* — No. You talk in plain English.
- *"The AI designs the whole board unsupervised."* — No. It stops at every real
  decision and waits for you.
- *"If I close VS Code I lose my work."* — No. Everything is saved in your project
  folder and you can pick up exactly where you left off (see
  [step 03](03-vscode-and-ai.md)).

## Checklist before moving on

- [ ] I understand Tracewright is a workspace + an AI assistant, not a program I run.
- [ ] I understand the AI does the busywork and I make the decisions.
- [ ] I understand EasyEDA = schematic + placement, KiCad = routing + checks.

---
◀ [Handbook home](README.md) · Next ▶ [02 — Installing the tools](02-installing-tools.md)
