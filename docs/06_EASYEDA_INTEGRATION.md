# 06 · EDA-Tool Integration (EasyEDA Pro reference)

AXON treats the EDA tool as a **compiler backend**: the generation layer emits
instructions, the tool turns them into geometry. This file documents the two
channels for driving EasyEDA Pro, the API contracts that work, and the hard limits
that don't — generalizable to any scriptable EDA tool.

> **Porting note.** The *shapes* here are universal (a scriptable channel + a
> headless channel; connect-by-net-name; probe-before-assume; a tested-signatures
> table). Only the exact method names are EasyEDA-specific. KiCad's equivalent is
> the `pcbnew` Python API + `kicad-cli`; see [`09_VALIDATION.md`](09_VALIDATION.md).

---

## The two channels

| Channel | Runtime | API root | Use for |
|---|---|---|---|
| **Standalone Script** | pasted into *Settings ▸ Extensions ▸ Standalone Script*, runs in-page as `eda.*` | `eda` | schematic section generation, placement, in-tool audits |
| **CDP / headless** | raw Chrome DevTools websocket into a logged-in profile | `window._EXTAPI_ROOT_` | netlist extraction, readback/audit, batch execution, screenshots |

Same underlying API surface, two entry points. Standalone scripts are how a human
runs a generator; CDP is how the AI reads reality back. Full CDP setup in
[`07_BROWSER_AUTOMATION.md`](07_BROWSER_AUTOMATION.md).

---

## Contract 1 — Connect by net name (never by drawn wire)

```js
// The 2nd argument IS the net. Nets merge globally by name across all pages.
await eda.sch_PrimitiveWire.create([pin.x, pin.y, pin.x + dx*OUT, pin.y + dy*OUT], netName);
```

Because connectivity is by name, **stub length is irrelevant** — so use *short*
stubs (long collinear stubs from adjacent parts auto-merge → shorts; see
[`05 §B10`](05_BOTTLENECKS.md)). One schematic with multiple **pages**, never
separate schematic files (separate files = nets don't merge, designators collide).

---

## Contract 2 — Part search: token-match, reject arrays, never `[0]`

```js
function hay(it){ return ((it.name||"")+" "+(it.symbolName||"")+" "+(it.manufacturer||"")
                          +" "+(it.manufacturerId||"")+" "+(it.description||"")).toLowerCase(); }

async function pick(query, token){                 // token = "a|b|c" disambiguation
  const r = await searchRetry(query);              // 4 retries, ~800ms backoff
  const arr = Array.isArray(r) ? r : (r.deviceList||r.list||r.items||r.result||r.data);
  for (const it of arr){
    const h = hay(it);
    for (const t of token.toLowerCase().split("|")) if (t && h.indexOf(t) >= 0) return it;
  }
  return null;                                      // NEVER fall through to arr[0] for ICs
}
```

- Return shape is unstable → unwrap `deviceList||list||items||result||data`.
- **Reject array/network parts:** `/^4d\d|cay16|cay10|exb[-_]|isolated|array|network|\brn\b/`.
- **Prefer `getByLcscIds([id])` when the part number is known** — more precise than
  search; fall back to token search only when no LCSC ID.
- **Verify the picked part by decoding its `manufacturerId`** against the spec
  (a fuzzy match returned a 12 pF cap and a 2.2 µH inductor into µF slots).

---

## Contract 3 — Passives: value-coded, wrong-type-rejected

```js
async function pickPassive(kind /* "R"|"C" */, val){
  const code = eiaCode(kind, val);                 // 100nF→104, 47Ω→470J : the discriminator
  const queries = [`${valStr(kind,val)} 0603 ${kind==="R"?"resistor":"capacitor"}`];
  if (kind==="R" && ohms(val) < 100) queries.unshift(`0603WAF${lowCode}T5E`); // exact vendor PN
  const clean = arr.filter(it => !isArray(it.name) && !isWrongType(it.name, kind));
  for (const it of clean) if ((it.name||"").indexOf(code) >= 0) return it;    // EIA match wins
  return clean[0] || null;
}
```

The EIA value-code is a secondary discriminator that catches a library returning a
*close-but-wrong-value* passive. Always carry it.

---

## Contract 4 — Stub direction from pin rotation + centroid

```js
function pinDir(pin, mx, my){                       // (mx,my) = component pad centroid
  const r = ((+pin.rotation||0)%360 + 360)%360;
  if (r===0 || r===180) return [Math.sign(pin.x-mx)||1, 0];  // horizontal pin → left/right
  return [0, Math.sign(pin.y-my)||1];                        // vertical pin   → up/down
}
```

Direction from the pin's own rotation; sign from which side of the centroid it sits
on. No hard-coded per-part table → board-agnostic.

---

## Contract 5 — Placement uses setState, not modify

```js
// PCB component placement — the modify({x,y,...}) form does NOT move parts.
c.setState_X(xMil); c.setState_Y(yMil); c.setState_Rotation(rot); c.setState_Layer(layer);
await c.done();                                     // auto-persists
```

Units are EasyEDA-internal (**1 mm = 39.3700787 units**; Y increases downward →
negate). After placement, **re-`getAll()` in a fresh eval** before auditing (stale
snapshot; [`05 §B5`](05_BOTTLENECKS.md)).

---

## The tested-signatures table (works / fails / fatal)

| Call | Status | Note |
|---|---|---|
| `sch_PrimitiveWire.create([x1,y1,x2,y2], net)` | ✅ works | net = arg 2 |
| `sch_PrimitiveComponent.getAllPinsByPrimitiveId(id)` | ✅ works | pins have **no** `.net` (see below) |
| `pcb_PrimitiveLine.create('', 11, x1,y1,x2,y2)` | ✅ works | layer 11 = board outline |
| `pcb_PrimitiveVia.create(net, x, y)` | ✅ works | collision-check before insert |
| `setState_X/Y/Rotation/Layer + done()` | ✅ works | placement path |
| `pcb_PrimitiveComponent.modify({x,y})` | ⚠️ no-op for move | use setState |
| designator via `modify({designator})` | ⚠️ unreliable | use UI **Annotate** |
| `pcb_PrimitivePour / Region / Fill .create(...)` | ❌ rejects every signature | pours are **UI-only** |
| autorouter with scripted outline | ❌ won't accept | needs UI-recognized outline |
| `sch_Net.getAllNets()` / `getNetlist()` | ❌ hangs headless | reconstruct from wires |
| `pcb_PrimitiveArc.create(...)` | ☠️ **hard-hangs renderer** | avoid; recover at tab level |

**Discipline:** probe an unknown `*.create` with **one guarded call**, never a loop
(a loop of wrong signatures froze the renderer). Record every result in a table
like this so you never re-probe.

---

## Hard limits → what must be a human/UI step

- Copper **pours/planes**, **auto-routing**, project-wide **Annotate**, **Check
  Nets / Update PCB**, PCB **part swap** — all UI-only. These define the Tier-4
  boundary in [`04_HUMAN_IN_THE_LOOP.md`](04_HUMAN_IN_THE_LOOP.md). The generation
  layer emits a *plan* for these, not a script.

---

## Netlist reconstruction (because the netlist API hangs headless)

Pins carry **no** net; **wires do.** Rebuild pin→net by coordinate match:

```python
vtx = defaultdict(set)                     # (x,y) -> {net}
for w in wires:                            # sch_PrimitiveWire.getAll() — wires HAVE .net
    for i in range(0, len(w["line"])-1, 2):
        vtx[(round(w["line"][i]), round(w["line"][i+1]))].add(w["net"])
for pin in pins:                           # match each pin to the wire endpoint at its (x,y)
    net = vtx.get((round(pin["x"]), round(pin["y"])))
```

This is the phase-5 verification oracle. Note the net-resolver **lags** after a
bulk wire create — re-dump before trusting a FLOAT reading.
