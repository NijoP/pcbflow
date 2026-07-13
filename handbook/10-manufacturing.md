# 10 — Manufacturing

**Workflow step:** [Phase 12](../workflow/12-final-verification.md) · **For:** electronics engineers.

- **Purpose:** produce the files a factory needs, and order the board.
- **What you need:** a verified, signed-off design.
- **What you get:** a complete manufacturing package — and a board on its way.

## What the AI produces

The full set of factory files, saved in your project's `12_verification/manufacturing/`
folder and **saved to your project history** so they can never be lost:

- **Gerbers** (the copper/mask/silk layers, including inner layers),
- **drill** file,
- **CPL / pick-and-place** (where each part goes, for assembly),
- **BOM** (the parts list for assembly),
- **assembly renders** (pictures of the finished board),
- a **DFM report** (design-for-manufacturing check).

It can also run the fab's free DFM check for you and report anything the factory
would flag.

## What you do

- Review the package.
- **Place the order** at your fab (JLCPCB, PCBWay, your assembler, etc.). **This is
  always you — the AI never places an order.** It spends real money and it's
  irreversible.

## What good looks like

- A complete package that a fab accepts without questions.
- The fab's DFM check is clean.
- Everything is saved in your project (so a re-order later is trivial).

## Common mistakes

- Ordering before the package is saved to your project history — save first.
- Forgetting the assembly files (CPL + BOM) if you want the board assembled, not just
  fabricated.

## Validation checklist

- [ ] Gerbers (all layers), drill, CPL, BOM, renders produced.
- [ ] Fab DFM check passed.
- [ ] Package saved to the project history.
- [ ] I placed the order.

## You did it

That's a full board, from a client's idea to a manufacturing order, with the AI doing
the busywork and you making every real call.

**One last thing:** if anything surprised you or went wrong, tell the AI to record
the lesson. It writes it into [`../knowledge/learning-db.md`](../knowledge/learning-db.md)
so your **next** board avoids it. That's how Tracewright gets better with every project.

---
◀ [09 — Verification](09-verification.md) · [Handbook home](README.md)
