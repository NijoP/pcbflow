# Build Sheet — <PROJECT NAME>

> The **tick-sheet**: one section per functional block, with per-pin net
> assignments and passives. This is one of the two source-of-truth documents.
> On any conflict with `net_connection.md`, **the net dictionary wins.**
> Apply a dated `🔄 <date> — <what changed>` banner to any section you edit.

**Board:** `<W×H mm>` · `<N layers, stackup>` · **Rev:** `<X>` · **Updated:** `<date>`

**Build order** (power in, logic, actuation, verify — reorder to your board):
`Power rails → USB/charge → Protection → Latch → LDO → Fuel gauge → (Expander) →
MCU → RF → Sensor 1..n → Actuators → LEDs → Headers → DRC`

---

## 1. <Block name> — <PART TYPE> (<designator>)

**`[ ] U1` — <Full part name>** · *Lib:* `<EDA search term>` · *LCSC:* `<Cxxxxxx>`

| Pin | NET |
|-----|-----|
| `<PIN_NAME>` | `<NET_NAME>` |
| `<PIN_NAME>` | `<NET_NAME>` |
| `<NC pin>`   | `—` (intentionally unconnected) |

Passives: `[ ] R1` `<value>` `<netA>`–`<netB>` · `[ ] C1` `<value>` `<netA>`–`<netB>`

> Notes: decoupling ≤2 mm from pin; boot-strap/pull-ups present; open-drain pulled.

---

## 2. <Block name> — …

*(repeat one section per functional block)*

---

## <N>. VERIFY — final checklist before PCB conversion

- [ ] ERC clean: no floating pins, no single-pin nets
- [ ] Net membership matches `net_connection.md` §membership, net-for-net
- [ ] Analog ground (`GNDA`) ties to `GND` at **exactly one** point (star)
- [ ] Every IC decoupled; every regulator has in/out caps
- [ ] Actuators boot-safe (gate pulldowns + flyback/protection present)
- [ ] USB CC resistors + boot/EN straps correct
- [ ] Every power pin on its intended rail (spot-check against §membership)
- [ ] Designators annotated project-wide (UI Annotate — not scriptable)

---

### Fields to fill (SPECIFIC) vs keep (GENERAL)

| SPECIFIC — replace per board | GENERAL — keep the structure |
|---|---|
| block names, part names, LCSC IDs, pin names, net names, passive values | the per-block layout, the §VERIFY checklist, the build order skeleton, "net dictionary wins" |
