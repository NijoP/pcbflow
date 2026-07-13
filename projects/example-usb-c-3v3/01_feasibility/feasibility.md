# Feasibility — USB-C → 3.3 V supply + status LED

*Phase 1 · technical feasibility with real numbers, before any design. Verdict: **GO**.*

## Power budget
| Item | Value | Note |
|---|---|---|
| Input | 5.0 V (USB-C VBUS) | bus-powered |
| Output | 3.3 V | LDO regulated |
| Max load | 300 mA | MCU + LED headroom |
| LDO dropout | ~0.1 V @ 300 mA | ME6211 is low-dropout; 5 V→3.3 V has ample margin |
| Dissipation | (5.0−3.3) × 0.3 ≈ **0.51 W** | SOT-23-5 θ_JA ~250 °C/W → ΔT ~128 °C at full load |

**Finding:** 0.51 W in a SOT-23-5 is the one thing to watch — fine intermittently, warm at
sustained 300 mA. Acceptable for a reference board; a real 300 mA continuous design would use a
buck or a larger package. *Documented, not hidden.*

## Electrical feasibility
- **USB-C sink:** CC1/CC2 each need a 5.1 kΩ pull-down (Rd) or the source won't apply VBUS. ✅ in BOM.
- **Decoupling:** 10 µF in + 10 µF out satisfies the ME6211 datasheet. ✅
- **LED:** (3.3 − 2.0 V_f) / 1 kΩ ≈ 1.3 mA — visible, low power. ✅

## Manufacturing feasibility
- 2-layer, 1 oz, ~25×15 mm, all 0402/0603/SOT-23 → trivially within JLCPCB capability.
- Trace currents ≤0.3 A → 0.3 mm traces are >10× the IPC-2221 minimum. ✅ (see `pcbflow.ipc`).

## Verdict
🟢 **GO.** Only caveat: LDO thermals at sustained max load — noted for the BOM/placement phases.
