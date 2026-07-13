# 09 · Validation Methodology

Validation is a first-class architectural layer, not a step. Its one job:
**compare real geometry against authored intent and emit a verdict.** It never
trusts a generator's self-report. Principle 3 ("verify against reality, never the
tool's model") made operational.

---

## The three ground-truth mechanisms (one per phase)

| Phase | Mechanism | Against |
|---|---|---|
| 5 · Schematic | reconstructed netlist (pin→net from wire coords) | `net_connection.md` §membership |
| 6 · Placement | real-geometry pad-spacing audit | hand-solder minimum gap |
| 8 · Routing | DRC in the board's own tool + own ruleset | manufacturer's DFM limits |

---

## Mechanism 1 — Reconstructed netlist (schematic)

The EDA tool's own netlist API hangs headless, so rebuild it from primitives: wires
carry `.net`, pins don't → match each pin to the wire endpoint at its `(x,y)` (code
in [`06 §Netlist reconstruction`](06_EASYEDA_INTEGRATION.md)). Then **diff** the
reconstructed net membership against `net_connection.md` §19.

Checks: 0 shorts (two intended-different nets merged), 0 single-pin nets, 0 floating
pins, analog ground ties to ground at exactly one point. A swarm can parallelize
this — one reviewer per subsystem — each returning a PASS/CONDITIONAL/FAIL with a
numbered finding list.

> This gate is *seconds* and headless. It found 22 pin shorts, 2 wrong-value parts,
> and 73 blank values in one pass. Run it before **any** layout — never after.

---

## Mechanism 2 — Real-geometry spacing audit (placement)

Never trust the placer's grid model — it shows phantom overlaps (stale snapshot)
and misses real ones (origin ≠ centroid). Read the **actual pad polygons** back
from the live board and compute axis-aligned bbox gaps:

```python
for a, b in combinations(components, 2):
    if a.layer != b.layer: continue                 # only same-layer pairs collide
    g = bbox_gap(padbbox(a), padbbox(b))            # real pads, connector inflation applied
    limit = 0.40 if both_hand_solder else 0.50      # DFM minimum
    if g < limit - 1e-6: violations.append((a, b, g))
```

Also check: M2/mounting keepout intrusion (hole-centre to nearest pad corner),
board-outline containment (with per-type edge overhang for connectors), and any RF
keepout. Emit a JSON audit + a heat-map. The passing condition is **0 violations on
real geometry** — plus the *practical* review (edge parts open outward; sensors
share an axis) that no metric captures.

Two bugs this mechanism exists to defeat:
- **Origin ≠ centroid** — a component's `(x,y)` is its footprint origin; compute the
  centroid from the pad union or you audit the wrong point.
- **Pad rotation stale** — derive pad orientation from the *component* rotation,
  never the pad attribute.

---

## Mechanism 3 — DRC ground truth (routing)

**The board's own tool, with the board's own ruleset. Never cross tools.** This is
the single most important toolchain rule; violating it produces phantom-clean
results and shipped the origin project's worst near-misses.

**KiCad boards:** `kicad-cli pcb drc` reads the ruleset from the *sibling*
`.kicad_pro`. A bare `.kicad_pcb` reports the weak built-in defaults. Wrap it so
the ruleset is always beside the board:

```bash
# drc.sh — copy the operative ruleset next to the board, THEN run kicad-cli
cp "$RULESET_PRO" "${BOARD%.kicad_pcb}.kicad_pro"
kicad-cli pcb drc --severity-error --exit-code-violations "$BOARD"
```

**EDA-native boards** (EasyEDA): use *that tool's* DRC against the named ruleset
(e.g. `<project>-4L-JLC`). Do **not** run KiCad DRC on an EasyEDA-native board —
the tool-mismatch is a phantom-DRC trap.

A ruleset config (`design_rules.json`) that carries the manufacturer's DFM floor —
copper-edge clearance, track/space, hole-to-copper, via drill/pad, annular ring,
per-net-class widths — is in [`templates/design_rules.template.json`](../templates/design_rules.template.json).

---

## Cross-cutting rules

**R1 · Re-read after every mutation.** `getAll()` is stale in the same eval as a
move; pad rotation is stale after a rotate; the net resolver lags after bulk wire
create. Always re-dump in a fresh eval.

**R2 · An autorouter's "0 unrouted" is not DRC.** Validate the *imported* board with
the real DRC. One instance: router said 0; real DRC said 1091.

**R3 · Verify import fidelity on any tool-to-tool migration.** Assert 0 dropped
footprints and a sub-µm max position residual before trusting a migrated board.
Mounting holes often *don't* survive an export → restore and re-verify.

**R4 · Whitelist known-legitimate exceptions explicitly** (a channel-pitch pad gap;
a single-pad net's "unrouted" flag) so they don't drown real findings — but *name*
each one; silent truncation reads as "all clean."

**R5 · The verdict is dated and attached to an artifact.** `PASS` / `CONDITIONAL
(numbered fixes)` / `FAIL`, with the ruleset and board it was run against. A verdict
with no ruleset named is not a verdict.

---

## What a verdict looks like

```
VERDICT: CONDITIONAL PASS  ·  board=board_revD  ·  ruleset=Proj-4L-JLC  ·  2026-07-13
  0 shorts · 0 unrouted · DRC 0 errors / 6 warnings
  CONDITIONS (must arm before ship):
    1. GND↔VSYS bypass cap ≤3 mm at each fast-SPI F↔B via (11 sites)
    2. hand-finish the U1-south escape tail (interactive; ~10 min)
  WHITELIST (not violations):
    - D1–D4 channel-pitch pad gap 0.42 mm (by design)
```

Falsifiable, dated, tool-and-ruleset-named, with conditions and whitelist explicit.
That is the currency the whole methodology trades in.
