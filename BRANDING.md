# Branding & Project Identity

This document proposes the project's name, evaluates the options, and defines the
full identity (tagline, mission, vision, principles, philosophy, goals). It is the
source of truth for how the project presents itself for open-source release.

---

## The naming problem

The working codename **AXON** was unsuitable (it collides with well-known companies —
Axon Enterprise — and several dev tools), and the repository name **easyeda-plugin**
is both generic and *wrong*: this is not an EasyEDA plugin. It's a tool-agnostic,
AI-assisted electronics engineering workspace that spans EasyEDA **and** KiCad and is
designed to outlive either.

**Naming conventions in the space** (studied for style): EDA/CAD tools favor coined or
craft words (KiCad, Fritzing, LibrePCB, Horizon, Flux); AI dev tools favor short,
punchy, ownable names (Cursor, Zed, Warp, Codeium, Devin, Continue). The sweet spot for
this project: a name rooted in the **craft of building circuits**, short enough to own,
professional enough for a startup, and not bound to any one EDA tool.

---

## Name proposals

### 1. Tracewright  ⭐ recommended
- **Meaning:** *trace* (the copper connections of a PCB) + *wright* (a skilled maker —
  as in shipwright, wheelwright, playwright). "A craftsman of circuits."
- **Why it fits:** the product's entire philosophy is *an AI craftsman doing the skilled,
  repetitive work while the engineer stays the master.* "Wright" encodes that exactly.
  "Trace" is universal to PCB work and tied to no single EDA tool.
- **Advantages:** distinctive and likely available; professional; memorable; carries a
  built-in story; scales to a startup; not EDA-specific.
- **Disadvantages:** "wright" can be misheard as "write/right"; 11 characters.

### 2. Boardsmith
- **Meaning:** *board* + *smith* (a maker: blacksmith, wordsmith). "A smith who forges
  boards."
- **Why it fits:** warm, instantly clear, evokes craftsmanship and the AI-as-smith.
- **Advantages:** immediately understood; friendly; memorable; easy to pronounce.
- **Disadvantages:** "-smith" is a common suffix (less unique); "board" is a touch literal.

### 3. Cuprum
- **Meaning:** Latin for *copper* (the source of the symbol **Cu**) — the material every
  PCB is made of.
- **Why it fits:** premium, elegant, short; copper is the essence of a board.
- **Advantages:** 6 letters, punchy, ownable, sophisticated.
- **Disadvantages:** meaning isn't obvious to a layperson; a few existing uses.

### 4. Voltaic
- **Meaning:** of/producing electric current (from Volta, inventor of the battery).
- **Why it fits:** broadly electronic, energetic, professional.
- **Advantages:** pronounceable, familiar, positive.
- **Disadvantages:** somewhat generic; several products already use "Voltaic".

### 5. Netforge
- **Meaning:** *net* (electrical nets) + *forge* (a place of making).
- **Why it fits:** captures nets → fabricated board; "forge" is at home in OSS.
- **Advantages:** clear making metaphor; strong sound.
- **Disadvantages:** "forge" is heavily used (SourceForge, etc.); "net" is ambiguous.

### 6. Padstack
- **Meaning:** the PCB term for the stack of pads/vias through the board's layers.
- **Why it fits:** deeply electronics-native, unique, technical.
- **Advantages:** memorable to engineers; ownable.
- **Disadvantages:** jargon; opaque outside the field.

---

## Recommendation: **Tracewright**

It is the only option that captures the *product's actual identity* — an AI craftsman
of circuits working under the engineer's judgment — while being distinctive, ownable,
professional, pronounceable, tool-agnostic, and startup-ready. Boardsmith is the safest
runner-up (most instantly understood); Cuprum is the premium alternative.

> **Before committing:** verify availability of the GitHub org/repo, an npm/PyPI name if
> relevant, a domain (tracewright.dev / .io), and do a light trademark check. This
> document recommends the name; availability is a quick confirmation step for the owner.

**Repository name:** rename `easyeda-plugin` → **`tracewright`** (GitHub → Settings →
General → Repository name; only the owner can do this).

---

## Project identity

**Tagline (primary):** *Your AI bench engineer — from client brief to manufacturing-ready board.*
Alternates: *"Design boards, not scripts."* · *"The AI craftsman for electronics engineers."*

**Mission:** Automate the repetitive, error-prone work of PCB design — net-by-net wiring,
placement, routing, checking — so electronics engineers spend their time on judgment, not
busywork, while every engineering decision stays human.

**Vision:** Every electronics engineer works alongside a tireless, disciplined AI
collaborator that carries a design from requirements to manufacturing, learns from every
board, and never lets the engineer lose control of a single decision that matters.

**Core principles** (the non-negotiables the whole system is built on):
1. **Knowledge is the source; geometry is the build artifact** — protect the thinking,
   regenerate the drawings.
2. **Place nothing over wrong** — never build a stage on an unverified one.
3. **Verify against reality, never the tool's own report.**
4. **Autonomy by reversibility** — the AI runs free on replayable work; a human gates
   anything irreversible; the fab order is always human.
5. **The verdict is the unit of progress** — PASS / CONDITIONAL / FAIL, not "done."
6. **Two engineers in one** — the AI holds a software-engineer and a hardware-engineer
   persona at once, and the hardware persona can veto.
7. **Fail loud, heal quietly** — surface problems in plain English; recover automatically
   where safe.
8. **Knowledge compounds** — every project makes the framework smarter.

**Design philosophy:** engineering-first (start from the objective, not the code),
human-in-the-loop by default, tool-agnostic (EasyEDA + KiCad today, more later),
AI-model-agnostic, and honest about its limits.

**Long-term goals:** a fully documented, self-healing, cross-platform workspace; a
growing shared knowledge base across projects; support for more EDA backends and AI
agents; and — eventually — a board you can *recompile* from its knowledge with one
command.

---

## Rename follow-up checklist (mechanical, low-risk)

Documentation is rebranded to **Tracewright** in this release. Remaining optional
mechanical steps, safe to do anytime:
- [ ] Rename the GitHub repo `easyeda-plugin` → `tracewright` (owner-only).
- [ ] Rename internal Python module `tools/axon_log.py` → e.g. `tools/runlog.py` (+ its
      imports in `test_axon_log.py`, `test_heal.py`).
- [ ] Rename the Chrome profile clone dir `axon-eda-chrome` → `tracewright-eda-chrome`
      (in `tools/platform_utils.py`).
- [ ] Optionally add a `tracewright` CLI wrapper so tools run as `tracewright doctor`
      instead of `python3 tools/doctor.py`.
