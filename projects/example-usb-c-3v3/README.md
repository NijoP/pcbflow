# Example — USB-C → 3.3 V power supply + status LED

A small, complete **worked reference** board that shows what a PCB Flow project looks like
at each phase. It's deliberately simple (8 parts, 1 layer of logic) so you can read the whole
thing in a few minutes, then copy the *shape* for your own board.

> **This is a learning example, not a template.** To start your own board, copy
> [`../_template`](../_template) — not this folder. See [`handbook/04`](../../handbook/04-your-first-project.md).

## What the board does
Takes 5 V from **USB-C**, regulates it to **3.3 V** with an LDO, and lights a **status LED**.
CC pins have the mandatory 5.1 kΩ pull-downs so a USB-C source actually supplies VBUS.

## What's in here (front-half of the workflow, filled in)
| Phase | File | Shows |
|---|---|---|
| — | [`project.yaml`](project.yaml) | the decision/state manifest (never file paths) |
| 1 | [`00_brief/brief.md`](00_brief/brief.md) | the captured requirement |
| 1 | [`01_feasibility/feasibility.md`](01_feasibility/feasibility.md) | feasibility + power budget with real numbers |
| 2 | [`02_bom/bom.md`](02_bom/bom.md) | the validated BOM |
| 3–4 | [`04_schematic/net_connection.md`](04_schematic/net_connection.md) | the exact net-by-net connection list |
| 3–4 | [`04_schematic/netlist.enet`](04_schematic/netlist.enet) | the **machine-checkable** netlist (EasyEDA `.enet` v2.0.0) |
| 10 | [`11_routing/design_rules.json`](11_routing/design_rules.json) | the JLCPCB DRC/DFM ruleset for this board |

Placement (8–9), routing (11), and verification (12) happen **live** in EasyEDA/KiCad with your
AI assistant — those phases produce geometry, which this text repo intentionally doesn't vendor.

## Try the tooling against it
The netlist here is real — the shipped Python tools read it directly:

```bash
# Parse + structurally verify the netlist (0 issues expected)
python3 -m pcbflow.enet projects/example-usb-c-3v3/04_schematic/netlist.enet
#   → 8 components, 6 nets, 0 floating pins, 6 BOM lines, verify_issues: []
```

```python
# Turn it into queryable design intelligence (the pcbmunch core)
from pcbflow.enet import Enet
ix = Enet.load("projects/example-usb-c-3v3/04_schematic/netlist.enet").design_index()
print(ix.net("+3V3"))          # who is on the 3V3 rail, its net class, pin count
print(ix.component("U1"))      # the LDO's nets + neighbours
```

## How to use it as a reference
Read `brief → feasibility → bom → net_connection` in order — that's the discipline PCB Flow
applies to *every* board, scaled down. Then open the [handbook](../../handbook/README.md) and
run the same phases on your own copy of `_template`.
