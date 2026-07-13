# Branding, Naming & Discoverability

This project's goal is **reach**: when an engineer searches GitHub for *pcb*,
*autonomous pcb*, *ai pcb design*, or *hardware design automation*, this repo should
surface. So the name and metadata are chosen for **search discoverability first**,
brandability second. This document is the source of truth for the name, the GitHub
metadata, and the project identity.

---

## How GitHub discoverability actually works (the strategy)

Stars follow *visibility × quality*. You control visibility through four fields,
roughly in order of impact for a repo that doesn't have many stars yet:

1. **Topics (tags)** — the single biggest lever you fully control. GitHub's "Explore
   topics" and topic search match these exactly. Set all of them.
2. **Description** — matched heavily in search; must be keyword-dense and readable.
3. **Repository name** — a strong keyword in the name ranks you for that keyword.
4. **README** — the H1 and first paragraph are indexed; put the keywords there.

A poetic brand name (e.g. "Tracewright") scores 0 on all four for someone searching
"autonomous pcb". A keyword-forward name + rich description + full topics scores on all
four. **That is why the name is `PCB Flow`, not a coined word.**

> Reality check: no repo ranks #1 for the bare term *pcb* (KiCad, etc. dominate with
> tens of thousands of stars). You win the **specific, less-contested** queries —
> *autonomous pcb*, *ai pcb design*, *llm pcb*, *ai eda*, *pcb design automation* —
> where keyword match + a handful of stars is enough to reach the top.

---

## Name proposals (scored for search + stars)

### 1. PCB Flow  ⭐ recommended (chosen)
- **Meaning:** **PCB** + **Flow** — the PCB design *flow* (workflow), automated.
- **Search value:** contains the top keyword *pcb* plus *flow* (workflow); ranks for
  "pcb flow", "pcbflow", "pcb workflow", and (via description/topics) "autonomous pcb".
- **Stars value:** short, memorable, pronounceable, easy to share and say aloud.
- **Advantages:** keyword-bearing **and** brandable — the rare combination; startup-able.
- **Disadvantages:** somewhat generic; verify `pcbflow` isn't already taken on GitHub.

### 2. PCB-Copilot
- **Meaning:** *pcb* + *copilot* (the now-standard word for an AI assistant).
- **Search/stars:** rides the huge "copilot" search trend + the "pcb" keyword; signals
  "AI assistant for PCBs" instantly, which attracts the AI crowd that gives stars.
- **Disadvantages:** "copilot" is heavily used (mild dilution) and Microsoft-adjacent.

### 3. autonomous-pcb
- **Meaning:** exact phrase match for the query "autonomous pcb".
- **Search:** the strongest pure ranking for that exact search.
- **Disadvantages:** reads as a slug, not a brand — weaker for word-of-mouth stars.

### 4. AI-PCB-Designer
- **Meaning:** matches "ai pcb design/designer".
- **Search:** strong for the "ai pcb" family.
- **Disadvantages:** long and descriptive rather than memorable.

### 5. PCBForge
- **Meaning:** *pcb* + *forge* (a place of making; common OSS suffix).
- **Search/stars:** carries *pcb*, brandable, OSS-native feel.
- **Disadvantages:** "forge" is crowded (SourceForge, many "*forge" repos).

---

## Recommendation: **PCB Flow**

It is the only option that is **both** keyword-bearing (ranks for pcb/auto/autonomous)
**and** brandable enough to earn word-of-mouth stars. `PCB-Copilot` is the strongest
alternative if you want to ride the "copilot" trend; `autonomous-pcb` if you want the
purest exact-match ranking for that one phrase.

**Rename the GitHub repo** `easyeda-plugin` → **`pcbflow`** (Settings → General →
Repository name; owner-only). *Verify `pcbflow` is free on GitHub first; if taken, use
`pcbflow-ai` or `ai-pcbflow`.*

---

## The GitHub metadata to set (copy-paste)

**Description** (About box — keyword-dense but readable):

> Autonomous, AI-assisted PCB design workflow — takes a hardware project from
> requirements to manufacturing-ready files. AI-driven schematic generation, component
> placement, and routing with human-in-the-loop review. Works with EasyEDA + KiCad and
> any AI coding agent (Claude Code, Codex, Cursor…).

**Topics** (Settings → Topics — add all; these are the #1 discoverability lever):

```
pcb  pcb-design  pcb-layout  pcb-automation  autonomous  ai  artificial-intelligence
llm  ai-agents  hardware  hardware-design  electronics  eda
electronic-design-automation  kicad  easyeda  schematic  routing  automation  embedded
```

**Set them via the API** (or the UI). With a token that has `repo` scope:

```bash
# description
curl -X PATCH -H "Authorization: Bearer <TOKEN>" \
  https://api.github.com/repos/<owner>/pcbflow \
  -d '{"description":"Autonomous, AI-assisted PCB design workflow — requirements to manufacturing (EasyEDA + KiCad)."}'
# topics
curl -X PUT -H "Authorization: Bearer <TOKEN>" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/<owner>/pcbflow/topics \
  -d '{"names":["pcb","pcb-design","pcb-layout","pcb-automation","autonomous","ai","llm","ai-agents","hardware","hardware-design","electronics","eda","kicad","easyeda","schematic","routing","automation","embedded"]}'
```

---

## More stars, beyond the name

- A clear README **hero** with the keywords in the first line (done).
- A short **demo GIF / screenshots** of a board going through the workflow (highest-ROI
  addition when the live pipeline is validated).
- Submit to **awesome-lists** (awesome-electronics, awesome-eda, awesome-ai-tools).
- A **"Show HN" / Reddit r/PrintedCircuitBoard / r/embedded** post when there's a live
  demo.
- Keep the topics current; add `good-first-issue` labels to invite contributors.

---

## Project identity

**Tagline:** *Autonomous AI PCB design — from requirements to manufacturing, with you in the loop.*

**Mission:** Automate the repetitive, error-prone work of PCB design — net-by-net wiring,
placement, routing, checking — so electronics engineers spend their time on judgment,
not busywork, while every engineering decision stays human.

**Vision:** Every electronics engineer works alongside a tireless, disciplined AI
collaborator that carries a design from requirements to manufacturing, learns from every
board, and never lets the engineer lose control of a decision that matters.

**Core principles:** knowledge is the source / geometry is the build artifact · place
nothing over wrong · verify against reality · autonomy by reversibility · the verdict is
the unit of progress · two engineers in one (SW + HW, HW can veto) · fail loud, heal
quietly · knowledge compounds.

**Design philosophy:** engineering-first, human-in-the-loop, tool-agnostic (EasyEDA +
KiCad today), AI-model-agnostic, honest about limits.

---

## Rename follow-up checklist

Docs are rebranded to **PCB Flow**. Remaining optional mechanical steps:
- [ ] Rename the GitHub repo `easyeda-plugin` → `pcbflow` (owner-only) + set the
      description & topics above.
- [ ] Rename internal module `tools/axon_log.py` → `tools/runlog.py` (+ imports in
      `test_axon_log.py`, `test_heal.py`).
- [ ] Rename the Chrome profile clone dir `axon-eda-chrome` (in `tools/platform_utils.py`).
