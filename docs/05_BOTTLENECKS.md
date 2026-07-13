# 05 · Bottlenecks & Reusable Solutions

Every pain point that cost real time or money in the origin project, paired with
the reusable solution. If you adopt PCB Flow, you inherit the solutions without paying
the tuition. Ordered roughly by cost.

---

### B1 · Context loss + status drift across sessions — *the most expensive*

**Symptom:** the governance file grew to describe boards that no longer existed;
a “PRODUCTION-READY: SHIP” row pointed at files never committed and since deleted.
Multiple board sizes (32×32 → 70×35 → 100×50 → 55×35 → 40×55) coexisted in one
status table as successive pivots, contradicting each other.

**Root cause:** status coupled to **artifact paths** instead of **decisions**.
When artifacts vanish, the ledger asserts facts with no backing.

**Reusable solution:**
- Status references *decisions and knowledge* (“4-layer, In2=VSYS, 10-class ruleset
  frozen”), never file paths.
- When ledger and reality diverge, pin a **`⭐⭐ READ FIRST` recovery memory** that
  explicitly lists which rows to distrust — a correction layer, not a rewrite.
- Treat any prior-session summary as **stale-by-default**; verify against git/live
  before acting. → [`10_MEMORY_AND_STATE.md`](10_MEMORY_AND_STATE.md).

---

### B2 · Board files lost forever (uncommitted geometry)

**Symptom:** three separately “delivered” boards; two permanently unrecoverable —
`kicad/`, `build/`, `lab/` were never git-tracked.

**Solution:** **commit every geometry artifact the moment it exists.** A finished
board is knowledge now, not disposable geometry. Add a phase-9 exit gate:
“package committed” — uncommitted means it doesn't exist. Keep a recoverable
export (gerbers or a native project) *in the repo* as a checkpoint even mid-flight.

---

### B3 · The interactive-routing wall (~$300 to learn)

**Symptom:** the EDA script API rejects every copper-pour signature; the
autorouter won't accept a scripted outline; fine-pitch (0.5 mm) escapes defeat
every maze router. Roughly $300 was spent in long agent sessions *discovering*
you cannot brute-force past it.

**Solution:** stop fighting the wall. **Automate up to it, then emit a maximally
detailed plan for the human** — a `route_sequence.json` with literal pour
polygons, via-farm coordinates, and phase-by-phase steps — so the unavoidable
manual time is minutes, not hours. Know your walls
([`04 §Tier 4`](04_HUMAN_IN_THE_LOOP.md)) and design around them.

---

### B4 · Browser / OAuth / profile instability (headless EDA)

**Symptom:** Chrome refuses remote-debugging on the default profile; a copied
profile launches *logged out* (cookies bound to the OS keyring); Google OAuth
blocks automation-controlled Chrome; the profile clone is wiped on reboot; the
generic devtools MCP spawns its **own** browser and won't attach to :9222; two
open sessions cause a cloud edit-lock that fails all writes.

**Solution (the working recipe):** `rsync` a clone of the *logged-in* Chrome
profile (excluding caches) → `rm Singleton*` → launch on the clone with
`--remote-debugging-port=9222` → drive via a **raw CDP websocket client**, not an
MCP. The clone carries cookies/localStorage → stays authenticated. One session at
a time. → [`07_BROWSER_AUTOMATION.md`](07_BROWSER_AUTOMATION.md).

---

### B5 · Stale snapshots (getAll / pad rotation / net lag)

**Symptom:** `getAll()` returns pre-move coordinates in the same eval → phantom
2 mm overlaps in audits; pad `rotation` attrs stay stale after a component
rotates; right after a bulk wire create, every pin reads `net=""` (FLOAT).

**Solution:** **re-read in a fresh eval after every mutation.** Audit real geometry
from the *component* rotation, not pad attributes. After bulk wire ops, wait / re-
dump before trusting FLOAT status. Cache canonical reads to a `live_geo.json`.
(This is Principle 3 made operational.)

---

### B6 · Phantom DRC (wrong tool / missing ruleset)

**Symptom:** `kicad-cli pcb drc` on a bare `.kicad_pcb` reports clean because the
real rules live in the sibling `.kicad_pro`; an internal EDA check is weaker than
the real DRC (0 → 1091 when checked properly); a stale MCP pointed at the wrong
board file entirely.

**Solution:** **DRC ground truth = the board's own tool + its own ruleset.** For
KiCad, always run with the `.kicad_pro` sibling present (wrap it in a `drc.sh`
that copies the ruleset beside the board). For an EDA-native board, use that
tool's DRC against the named ruleset. **Never cross tools** — that is the
phantom-DRC trap. → [`09_VALIDATION.md`](09_VALIDATION.md).

---

### B7 · Renderer hard-hangs from a wrong API signature

**Symptom:** probing a `*.create` signature in a loop triggered a blocking modal
that froze the renderer JS thread; even `1+1` evals and screenshots then time out;
same-document navigation is a no-op; the JS-dialog handler doesn't clear a DOM
modal.

**Solution:** never probe `*.create` signatures in a loop on the live doc — test
**one guarded call**. Keep a **tested-signatures table** so you never re-probe.
Recover at the **browser (tab) level**: create a fresh target, close the hung
target. **Save frequently.** Avoid the known-fatal calls entirely.

---

### B8 · Designator drift between sessions

**Symptom:** live-editor designators ≠ the script's designators (project-wide
Annotate renumbered by position); `final.js`'s `U7` is a different part than the
live `U7`.

**Solution:** **never key on designators across tools.** Identify parts by
device/footprint/part-number from the property panel. Maintain a live↔intended
designator map as an artifact; it's required to cross-reference DRC errors back to
schematic-section docs.

---

### B9 · Token cost of long multi-agent sessions

**Symptom:** long Opus swarm sessions are expensive; one dead-end (headless EDA
before the profile fix was found) cost ~$300.

**Solution:** the **one-unit-at-a-time loop is a token-management strategy**, not
just a quality one — small blast radius, small context. Reserve multi-agent swarms
for **planning** phases; use targeted CDP reads for execution. Explicit rule:
**reuse existing analysis, don't re-derive** what a prior doc/memory already
settled. Pick the model tier by task (cheap models for extraction/search, top tier
for architecture and adversarial verification).

---

### B10 · Collinear-wire auto-merge silently shorts pins

**Symptom:** the generator fanned IC pins with long horizontal stubs at each pin's
y-coordinate; when two ICs shared a y, the stubs became collinear and the tool
merged them into one net — a real short. Only the first device per row was clean.

**Solution:** because net-name is globally resolved, **stub length is irrelevant to
connectivity → use short (minimal) stubs.** This removes the collinear overlap
entirely. (A generation-layer fix, not a review-layer catch.)

---

## The meta-pattern

Nine of these ten reduce to one instinct: **the tool's model of the world is not
the world.** Snapshots go stale (B5), self-reports lie (B6), status decouples from
reality (B1, B2), and APIs fail in ways the happy path hides (B4, B7). The
framework's constant answer is **read reality back and verify against intent** —
which is exactly why the verification layer exists as its own tier of the
architecture.
