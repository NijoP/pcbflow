# Net Connection — <PROJECT NAME>

> The **net dictionary** + the **membership oracle**. This is the authoritative
> source of truth for connectivity. On conflict with `build_sheet.md`, **this file
> wins.** The membership table (last section) is the single verification oracle the
> phase-5 gate diffs against.

**Board:** `<W×H mm>` · `<layers>` · **Rev:** `<X>` · **Updated:** `<date>`

---

## §0 · Net Dictionary

### Power & ground
| Net | Meaning |
|-----|---------|
| `VBUS` | USB input (5 V) |
| `BAT+` | Protected cell positive |
| `VSYS` | System rail (post-switch/protection) |
| `+3V3` | Logic rail (LDO out) |
| `GND`  | System ground |
| `GNDA` | Analog ground island → single-point tie to `GND` |

### Buses & control
| Net | Meaning |
|-----|---------|
| `<SCL/SDA>` | I²C (pull-ups where?) |
| `<SCK/MISO/MOSI/CSn>` | SPI |
| `<IRQn>` | sensor interrupts |
| `<PWMn>` | actuator drive |

*(organize into: Power & ground / interface bus / control / actuation)*

---

## §1 · MCU pin/GPIO assignment

| MCU pin | Net | Function | Notes (strapping? ADC? boot?) |
|---|---|---|---|
| `<GPIOn>` | `<NET>` | `<role>` | `<constraint>` |

> Track spare GPIO count here — it drives the "do we need an I/O expander?"
> decision. A spare-GPIO count of 0 forces an expander; ample spares delete it.

---

## §membership · Net → every connected pin (the oracle)

> Every net, with **all** connected `<refdes>.<pin>` pairs. This is what
> verification reconstructs from the live board and diffs against. Completeness
> here is the phase-5 gate.

| Net | Members (`refdes.pin`, …) |
|-----|---------------------------|
| `GND` | `U1.GND`, `C1.2`, `J1.SHELL`, … |
| `+3V3` | `U_LDO.VOUT`, `U1.VDD`, `C2.1`, … |
| `<NET>` | … |

---

### Hard invariants (assert these, don't hope them)

- `GNDA` connects to `GND` at **exactly one** node (the star). *Verify by deleting
  the tie and checking `GNDA`'s connected-node count == its own pin count.*
- No net appears in this table with only one member (single-pin net = error).
- Every net named in `build_sheet.md` appears here and vice-versa.

| SPECIFIC — replace | GENERAL — keep |
|---|---|
| all net names, pin maps, GPIO assignments, membership rows | the §0/§1/§membership structure, the invariants, "this file wins" |
