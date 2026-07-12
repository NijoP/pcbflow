# 03 · The Engineering Knowledge Graph

This is the extracted, reusable *engineering intelligence* — the hidden knowledge
that lived scattered across 500+ docs, 40+ memory files, and 30 sessions, pulled
into one navigable graph. Nodes are **heuristics, decisions, failures, and
gotchas**. Edges are `→ leads to`, `⊣ blocks`, `≈ generalizes`.

Each node is stated as a **reusable rule** first, with the origin-project instance
as evidence. Use it as a checklist and as a “have we seen this before?” lookup.

---

## A. Decision heuristics (how to make the big calls)

**KG-D1 · Density drives board size.**
`density = courtyard_area / board_area × 2`. ≤25% → 2-layer comfortable; ~35% →
tight; >45% → 4-layer or interactive finish. *Instance:* 70×35=46% (failed),
100×50=23% (clean). → feeds KG-D2.

**KG-D2 · Current drives layer count, not routability.**
If peak current on any rail exceeds a manufacturable trace's ampacity (~5 A on
1 oz), that rail needs a **plane** → ≥4 layers. Add layers for *amps*, then
exploit them for routing. *Instance:* ~10.5 A motor rail → In2 = solid VSYS plane.
⊣ the mistake of adding layers hoping routing gets easier (it doesn't, on its own).

**KG-D3 · The module variant is the highest-leverage RF decision on a compact board.**
Onboard-antenna vs external-connector variant decides whether you lose ~100 mm² to
a keep-out. *Instance:* ESP32-C3-MINI-**1U** (IPEX, no keep-out) over -1 (PCB
antenna). ≈ any RF module with an antenna-variant choice.

**KG-D4 · A UX feature is a client call; a safety function is an engineering mandate.**
Fuel-gauge IC vs ADC divider = client cost/UX decision. Over-discharge cutoff =
non-negotiable. Keep the two categories separate when presenting trades.

**KG-D5 · Prefer the IC that bundles a safety function over a discrete rebuild.**
*Instance:* a discrete power-latch failed on three independent causes (a MΩ timing
node dominated by comparator bias current; an over-volted pull-up; a boot timing
race). The single-chip latch bundles all four functions and can't repeat those
bugs. ⊣ rebuilding safety-critical analog discretely to save a few cents.

**KG-D6 · Size-vs-routability is a first-class, statable trade — not a failure.**
“A clean working board at the larger size beats a broken board at the spec size.”
State it as a constrained optimization up front. *Instance:* spec 45×35 never
routed; delivered 100×50 did.

---

## B. Layout & routing heuristics

**KG-L1 · Route thin first, pour last.**
Route every net as a thin trace so every pad is connected, *then* pour planes as
capacity/return reinforcement. GND pour is the **final** pass — pouring early
strands opens. ⊣ pour-first (fragmentation).

**KG-L2 · On 2-layer you cannot have both a solid bottom GND and zero unrouted on a
dense net list.** Demanding a perfect B.Cu plane = single-layer routing = doesn't
close above ~25% density. Relax to a via-stitched GND *pour* on both layers.

**KG-L3 · Promote, don't re-route.** To go from a working 2-layer board to 4-layer
for ampacity, *promote* the proven routing (add planes + collision-checked stitch
vias) rather than re-routing from scratch. *Instance:* from-scratch 4-layer never
converged (1091 DRC); promotion gave 0 unrouted.

**KG-L4 · Never a blind via per pad.** Stitching/plane-tie vias must be
collision-checked against all copper on all layers before insertion. *Instance:* a
via at every power pad → 250–815 net-to-net shorts.

**KG-L5 · A dense cluster's open nets are a track problem, not a placement problem.**
When an autorouter plateaus at a ~5–12 unrouted tail in a tight cluster, moving
parts makes it worse (every nudge trades one open for several shorts). Rip-up and
reroute the **obstructing tracks** instead. *Instance:* 2 agents, 0 successful
moves; ripping Q4_G/I2C_SCL tracks closed it.

**KG-L6 · Autorouters plateau; budget an interactive finish tail.**
At >~30% density on 4-layer, expect 85–95% auto-completion and a fine-pitch tail
(0.5 mm escapes) that no maze router closes. Plan for it; don't fight it.

**KG-L7 · Analog-ground island: single star-tie, proven as an invariant.**
Exactly one GND↔GNDA tie. Verify by deleting the tie and asserting the island's
connected-node count equals its own pin count. The stitch generator must *exclude*
the island polygon. Do **not** slot the main GND plane to isolate it — the pour
boundary does the isolation; a slot creates a return discontinuity.

**KG-L8 · Asymmetric-plane return paths need a cap, not a ground stitch.**
On an `F=GND / B=VSYS` stackup, a signal that vias F↔B changes its reference
plane. A GND stitch via does nothing (GND↔GND). The fix is a **GND↔VSYS bypass cap
≤2–3 mm** at each transition. *Instance:* fast-SPI on B.Cu.

**KG-L9 · Fine-pitch mask bridging is geometry, not a rule.**
At ≤0.5 mm pad pitch compute the mask web: `web ≈ pitch − pad_width −
2×mask_expansion`. If `web < ~0.15 mm` it bridges and no clearance rule fixes it.
Mitigate with an explicit F.Cu+mask **keepout zone** at the connector mouth.

**KG-L10 · Predict IC-edge congestion with a 2 mm-bin grid; solve with vias.**
A many-pin IC escaping on one edge saturates its channels. Predict with a
congestion grid (`demand > capacity` ⇒ via-fan). Solve by fanning to the other
layer, not by moving the IC.

**KG-L11 · Sensors that fuse must share an axis.** IMU and optical-flow placed with
identical rotation, or firmware needs a correction transform. Placement constraint,
not a nicety.

---

## C. Electrical / physics heuristics (quantified)

**KG-E1 · IPC-2221 trace width.** `I = k·ΔT^0.44·A^0.725` (k=0.048 external 1 oz,
0.024 internal). 1 oz external @ΔT10: 1 A=0.25 mm, 5 A=2.79 mm, 10 A=7.62 mm.
**>~5 mm ⇒ use a plane, a trace is absurd.** Treat an at-limit width as zero
margin; add ≥10%.

**KG-E2 · Via ampacity.** 0.3 mm drill ≈ 0.9 A; 0.5 mm ≈ 1.7 A (20 µm plating,
ΔT10). 10 A ⇒ 15–18× 0.3 mm or 5–7× 0.5 mm vias. The via nearest the source hogs
current → symmetric farms.

**KG-E3 · 0.5 oz inner plane ≈ half the ampacity of 1 oz outer.** Never let a
0.5 oz inner plane be the *sole* conductor for a path above ~5 A — add an outer
1 oz parallel bridge + via farm.

**KG-E4 · Decoupling is dominated by loop inductance.** ≤2 mm from pin (≤3 mm and
via-at-pad above 100 MHz). “A 100 nF cap 5 cm away is useless at 100 MHz.” Thick
inner-core stackups give too little interplane capacitance (~10 pF) to help — all
bulk decoupling must be discrete and close.

**KG-E5 · Regulator dropout must survive a depleted cell.** On 1S LiPo, VSYS sags
to ~3.0 V at low SoC; a 1 V-dropout LDO browns out. Use a low-dropout part with
adequate current margin (Wi-Fi TX bursts + sensors can exceed a 500 mA LDO).

**KG-E6 · FET thermal reality.** SOT-23 R_ds(on)≈30–45 mΩ at Vgs=3.3 V; P=I²R
puts T_j at destruction near ~4.5 A sustained. For 2 motors/channel under stall,
parallel two FETs (halves I²R per device) + firmware soft-start.

**KG-E7 · Published stall currents vary 3×.** Motor datasheets disagree wildly
(5 A listing vs 12–15 A bench). The true worst case (simultaneous stall) can be
40–100 A. Confirming the *actual* motor is a hard blocker for all power sizing.

**KG-E8 · λ/20 stitch frequency = edge-rate knee `0.35/t_rise`, not the clock.**
A 3.3 V/8 ns edge has content to ~44 MHz regardless of a 1 MHz clock.

**KG-E9 · Diff-pair impedance at low speed is best-practice, not a functional
gate.** USB-FS on a ~15–20 mm run is electrically short; match it, but 0 vias on
the pair and a solid reference plane matter more than the exact Ω.

---

## D. Tooling & automation gotchas (the “don't get burned again” set)

**KG-T1 · The EDA tool's live state is ground truth; snapshots lie.** Re-read after
every mutation. *Instances:* `getAll()` stale after moves; pad rotation stale;
net-resolver lags after bulk wire create.

**KG-T2 · DRC ground truth must match the board's authoring tool + correct
ruleset.** Cross-tool DRC = phantom results. A bare board file without its ruleset
sidecar reports the weak defaults as “clean.”

**KG-T3 · An autorouter's self-report is not DRC.** “0 unrouted” from the router ≠
0 DRC on the imported board (one instance: 0 → 1091 when checked properly).

**KG-T4 · Origin ≠ centroid.** An EDA component's `(x,y)` is its footprint origin,
not its pad centroid. Compute the centroid from the pad union or parts land 1–3 mm
off.

**KG-T5 · Connect by net name, never by drawn wire.** Net name is globally
resolved; stub length is irrelevant to connectivity — so use *short* stubs (long
collinear stubs from adjacent parts auto-merge into a short).

**KG-T6 · Verify a part by decoding its manufacturer ID, not the search string.**
A fuzzy search returns wrong-value/wrong-type parts that pass visually.

**KG-T7 · Some APIs are absent or fatal.** In the origin EDA tool: copper-pour
create rejects every signature; the autorouter won't take a scripted outline; one
primitive-create call *hard-hangs the renderer*. Probe before assuming; keep a
tested-signatures table; recover a hung renderer at the browser (tab) level.

**KG-T8 · Some sites 403 automated fetchers.** Use web *search* to confirm
availability; ground prices on cross-distributor twins and mark ESTIMATE.

---

## E. Governance & process gotchas

**KG-G1 · Never couple status to artifact paths.** Status references decisions.
*Instance:* “SHIP” pointing at an uncommitted, later-deleted file.

**KG-G2 · Commit every manufacturing output immediately.** Uncommitted = one pivot
from gone. *Instance:* three finished boards, two lost.

**KG-G3 · A prior-session summary is stale-by-default.** Verify against git/live
state before acting on it.

**KG-G4 · When the ledger and reality diverge, pin a “READ FIRST” correction** that
declares which rows to distrust — don't silently rewrite.

**KG-G5 · Schematic verification is cheap; run it before any layout, not after.**
The July pivot (stop PCB, re-verify schematic, find 2 criticals) was correct but
would have cost nothing if done as the phase-5 gate the first time.

---

## Reading the graph

Start at a decision you're facing → follow `→` for consequences, `⊣` for what it
forbids, `≈` for where it generalizes. The most-referenced nodes (KG-D1/D2,
KG-L1/L7/L8, KG-E1, KG-T1/T2, KG-G1/G2) are the load-bearing ones — internalize
those first.
