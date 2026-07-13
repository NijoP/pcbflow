# Documentation Gap Analysis

A pre-rewrite audit comparing what the repository *does* against what its
documentation *said*, treating the code and folders as the source of truth. This
motivated the README rewrite and the branding/roadmap work.

## Method

Inventoried the actual repository — `workflow/` (12 phases), `agents/`, `automation/`
(easyeda / browser / kicad / shared), `knowledge/`, `templates/`, `projects/`,
`docs/`, `reliability/` (6 audit docs), `tools/` (17 files: doctor, logging,
diagnosis, retry, self-healing, recovery, checkpoint/resume, cross-platform launcher +
DRC, schematic tidy, 5 test suites), and the `handbook/` (12 pages + glossary) — then
compared it to the then-current `README.md`.

## Gaps found (what the docs missed or got wrong)

| # | Gap | Severity | Fixed by |
|---|---|---|---|
| G1 | **Branding wrong** — docs said "AXON" (unsuitable codename); repo named "easyeda-plugin" (it is neither an EasyEDA plugin nor well-named) | High | [`../BRANDING.md`](../BRANDING.md) + rebrand to **PCB Flow** |
| G2 | **The reliability/self-healing system was undocumented in the README** — `tools/` (doctor, structured logging, auto-diagnosis, retry, recovery, resume) and `reliability/` existed but weren't surfaced | High | README §Notes + §Roadmap; `tools/README.md` |
| G3 | **No "Supported AI tools" section** — the framework is AI-model-agnostic but the README implied a single assistant | High | README §5 (Claude Code, Codex, OpenCode, Cursor, Gemini CLI, …) |
| G4 | **No Vision section** — the "AI assists, doesn't replace" thesis wasn't stated at the top level | Medium | README §2 + `BRANDING.md` |
| G5 | **No product Roadmap** — only the internal `reliability/ROADMAP.md` existed; no current/planned/future view | Medium | [`../ROADMAP.md`](../ROADMAP.md) + README §8 |
| G6 | **No Notes/limitations section** — known EasyEDA limits, browser-automation caveats, platform support, and human-review requirements weren't collected in one place | Medium | README §9 |
| G7 | **Cross-platform status stale** — docs implied Linux-only; the Phase-4 tools (`launch_easyeda.py`, `drc.py`, `platform_utils.py`) made it portable | Medium | README §Notes (Supported platforms) |
| G8 | **Getting-started scattered** — no single "install → clone → open → first project" flow at the top level | Medium | README §7 + `handbook/` |
| G9 | **Lifecycle not shown as one picture** at the top level | Low | README §3 (the 12-phase flow) |
| G10 | **Contribution path** referenced but not summarized in the README | Low | README §10 + `../CONTRIBUTING.md` |

## What was already good (kept)

- The `handbook/` onboarding path (12 pages + glossary) is strong and engineer-first.
- `ARCHITECTURE.md` explains the modular structure well.
- `workflow/`, `agents/`, `knowledge/`, and `templates/` each carry clear READMEs.
- `reliability/` is a complete audit + design, now with all five phases built in `tools/`.

## Outcome

The README was rewritten from scratch (engineer-first, 10 sections), the project was
rebranded to **PCB Flow**, and a product [`ROADMAP.md`](../ROADMAP.md) was added. The
deep reference docs remain accurate and were rebranded in place.
