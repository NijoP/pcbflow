# Brief — USB-C → 3.3 V supply + status LED

*Phase 0/1 · the captured requirement (what a client hands you, cleaned up).*

## Ask
A tiny, cheap board that takes USB-C 5 V and gives a clean **3.3 V** rail for a small MCU
project, with a **power-on LED** so you can see it's alive.

## Requirements
- **Input:** USB-C, bus-powered (5 V, no PD negotiation needed).
- **Output:** 3.3 V, up to ~300 mA continuous.
- **Indicator:** one green status LED on the 3.3 V rail.
- **Size:** as small as practical; hand-solderable (0402/0603, SOT-23).
- **Cost:** minimal; all parts JLCPCB-stockable (Basic/Extended).
- **Manufacturing:** 2-layer, 1 oz, JLCPCB.

## Explicitly out of scope
USB data, PD/QC fast charge, battery, reverse-polarity protection. Keep it minimal — this is a
reference board.

## Open questions (would be client sign-offs on a real job)
- LDO vs buck? → LDO chosen (5 V→3.3 V @ 300 mA = ~0.5 W dissipation, acceptable; simpler, cheaper).
