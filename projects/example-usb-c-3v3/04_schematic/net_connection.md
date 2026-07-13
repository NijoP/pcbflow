# Net connection list — USB-C → 3.3 V supply + status LED

*Phase 3–4 · the exact net-by-net connection list — the human-readable view of
[`netlist.enet`](netlist.enet). The audit (phase 5) checks the schematic against this.*

## Nets (6)

| Net | Members | Purpose |
|---|---|---|
| `VBUS` | J1.1, U1.1 (VIN), U1.3 (EN), C1.1 | 5 V USB input rail; EN tied high = always-on |
| `+3V3` | U1.5 (VOUT), C2.1, R3.1 | regulated 3.3 V output rail |
| `GND` | J1.2, R1.2, R2.2, U1.2, C1.2, C2.2, D1.2 (K) | ground |
| `CC1` | J1.3, R1.1 | USB-C config, 5.1 kΩ Rd to GND |
| `CC2` | J1.4, R2.1 | USB-C config, 5.1 kΩ Rd to GND |
| `LED_A` | R3.2, D1.1 (A) | LED anode via 1 kΩ limit resistor |

## Invariants the audit enforces
- `+3V3` and `VBUS` are the two power nets (net class `POWER`).
- Every LDO pin accounted for: VIN←VBUS, GND←GND, EN←VBUS (always-on), VOUT→+3V3.
- CC1/CC2 each terminate in exactly one 5.1 kΩ pull-down to GND (USB-C sink requirement).
- No floating pins (`floating_pins: 0`), no unnamed nets (`unnamed_nets: 0`).

> Source of truth is `netlist.enet`; this table is generated from it and must stay in sync.
> Verify: `python3 -m pcbflow.enet netlist.enet`.
