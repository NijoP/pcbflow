# automation/easyeda/ — Schematic + Placement Engine

The board-agnostic engine that drives EasyEDA Pro's Standalone-Script API. Used in
phases 3 (init), 4 (schematic generation), and 9 (placement).

## Transport — how JS reaches the editor

Two backends, one `{ok, v}`/`{ok, err}` envelope, chosen automatically by
[`session.py`](session.py) (`EdaSession().run(js)`; override with `EDA_BACKEND`):

- [`bridge.py`](bridge.py) — **primary.** Binds to EasyEDA's *official* Bridge Server
  (`POST /execute`, port range 49620-49629, handshake `service:"easyeda-bridge"`) paired
  with the `run-api-gateway` editor extension. No Chrome-profile cloning, no OAuth
  workaround — the user ticks "allow external interaction" and the gateway connects out.
  Contract mirrored from `easyeda/easyeda-api-skill` (see
  [`../../docs/17_UPSTREAM_TOOLING_VERDICT.md`](../../docs/17_UPSTREAM_TOOLING_VERDICT.md)).
- [`../browser/cdp.py`](../browser/cdp.py) — **fallback + screenshots.** Raw Chrome
  DevTools eval into a logged-in profile. Used when the gateway isn't installed.

> Unit-tested against a stdlib mock ([`test_bridge.py`](test_bridge.py)); the live
> Bridge path needs a real EasyEDA session with `run-api-gateway` to validate.

## Files

- [`section_generator.template.js`](section_generator.template.js) — the reusable
  engine (part search, passive picking, wire-by-net-name, stub direction) plus a
  per-block CONFIG. Copy it, fill the CONFIG from `build_sheet.md`, run it in
  *EasyEDA ▸ Settings ▸ Extensions ▸ Standalone Script*.
- [`api_probe.js`](api_probe.js) — **run this first.** Discovers the real library-search
  method, the `create()` return shape, and the pin field names on *your* EasyEDA build
  (the Pro API varies by build), so the other scripts use the right names.
- [`dump_schematic.js`](dump_schematic.js) — dumps the live schematic to JSON
  (`{components, wires}`) for headless verification; feed it to
  [`../browser/recon.py`](../browser/recon.py) via the CDP driver.

## The API contracts (that work)

| Call | Purpose |
|---|---|
| `sch_PrimitiveWire.create([x1,y1,x2,y2], net)` | wire a pin — **net is arg 2**; connect by name |
| `pcb_PrimitiveLine.create('', 11, x1,y1,x2,y2)` | board outline (layer 11) |
| `pcb_PrimitiveVia.create(net, x, y)` | via (collision-check first) |
| `setState_X/Y/Rotation/Layer + done()` | place a component (NOT `modify({x,y})`) |

## Hard rules & limits

- **Connect by net name**, short stubs (long collinear stubs auto-merge → shorts).
- **Never `search()[0]`** — token-match, reject array parts, verify by
  `manufacturerId`. Passives: `"<value> 0603 resistor|capacitor"` + EIA-code match.
- **One project, multiple pages.** Designators via UI **Annotate** (not scriptable).
- **Units:** 1 mm = 39.3700787 internal units; Y increases downward (negate).
- **Cannot do (UI-only):** copper pours, auto-route, Annotate, Check-Nets. Probe an
  unknown `*.create` with **one guarded call**, never a loop (a loop of wrong
  signatures hard-hangs the renderer).
- **Re-read after every mutation** (`getAll()` is stale in the same eval).

Full API reference + the tested-signatures table:
[`../../docs/06_EASYEDA_INTEGRATION.md`](../../docs/06_EASYEDA_INTEGRATION.md).
