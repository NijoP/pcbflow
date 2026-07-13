# BOM — USB-C → 3.3 V supply + status LED

*Phase 2 · validated parts list. All JLCPCB-stockable. Mirrors `04_schematic/netlist.enet`.*

| Ref | Qty | Value | Device | Footprint | LCSC | Notes |
|---|---|---|---|---|---|---|
| J1 | 1 | USB-C 16P | TYPE-C-31-M-12 | TYPE-C-SMD | C165948 | power-only usage |
| U1 | 1 | ME6211C33 | ME6211C33M5G-N | SOT-23-5 | C82942 | 3.3 V LDO, low-dropout, 300 mA |
| C1 | 1 | 10 µF | C_0603 | C0603 | C19702 | LDO input decoupling |
| C2 | 1 | 10 µF | C_0603 | C0603 | C19702 | LDO output decoupling |
| R1 | 1 | 5.1 kΩ | Res_0402 | R0402 | C25905 | CC1 pull-down (Rd) |
| R2 | 1 | 5.1 kΩ | Res_0402 | R0402 | C25905 | CC2 pull-down (Rd) |
| R3 | 1 | 1 kΩ | Res_0402 | R0402 | C11702 | LED current limit (~1.3 mA) |
| D1 | 1 | Green LED | LED_0603 | LED0603 | C72043 | power-on indicator |

**8 placements · 6 unique BOM lines** (C1/C2 and R1/R2 share parts).

## Validation notes
- All parts JLCPCB Basic/Extended → low assembly cost, no special sourcing.
- Second sources trivial (jellybean passives + generic SOT-23 LDO). No single-source risk.
- Cross-checked 1:1 against the netlist:
  `python3 -m pcbflow.enet 04_schematic/netlist.enet` → `bom_lines: 6`, `verify_issues: []`.
