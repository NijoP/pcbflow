"""Electrical Rule Check (ERC) — the schematic audit you run FIRST on any board.

Operates purely on the `.enet` netlist (pcbflow.enet) — no live tool, no geometry — so it
runs offline the moment you have a netlist, which is exactly when you're starting a fresh
board. It catches the connectivity mistakes that waste a layout: floating pins, dangling nets,
a power rail with no decoupling, a missing ground.

These are *topology* checks (what's inferable from connectivity alone). Pin-direction/type
conflict checking needs electrical pin types the netlist doesn't reliably carry — flagged as a
known limit rather than guessed. Pairs with pcbflow.dfm (manufacturability) and the phase-5 gate.
Pure Python 3 standard library.
"""
import re

from .design_index import _GND, _POWER
from .findings import finding
from .findings import report as report          # re-export the canonical rollup (DRY)

_CAP = re.compile(r"^C\d", re.I)      # capacitor designator (C1, C12…) → decoupling presence


def run_erc(enet):
    """Run ERC on an Enet. Returns a list of harmonized findings (pcbflow.findings)."""
    V = []
    nets = enet.nets()                       # net -> ['REF.pin(name)', ...]

    # E-GND: a board must have a ground net (topology-deterministic)
    if not any(_GND.match(n) for n in nets):
        V.append(finding(
            detector="erc", rule_id="no_ground", category="connectivity", severity="error",
            confidence="deterministic", evidence_source="topology", where="<board>",
            summary="no ground net found (expected GND/GNDA/AGND/DGND/PGND)",
            recommendation="add a ground net and connect returns to it"))

    # E-FLOAT: pins connected to nothing
    for fp in enet.floating_pins():
        V.append(finding(
            detector="erc", rule_id="floating_pin", category="connectivity", severity="error",
            confidence="deterministic", evidence_source="topology",
            where=f"{fp['des']}.{fp['pin']}", components=[fp["des"]],
            summary="pin is not connected to any net",
            recommendation="connect the pin or mark it no-connect"))

    # per-net checks
    for net, members in nets.items():
        refs = {m.split(".", 1)[0] for m in members}
        npins = len(members)
        is_power, is_gnd = bool(_POWER.match(net)), bool(_GND.match(net))

        # E-DANGLE: a named net that reaches only one pin (a wire to nowhere)
        if npins == 1 and not net.startswith("$"):
            sev = "error" if (is_power or is_gnd) else "warning"
            V.append(finding(
                detector="erc", rule_id="single_pin_net", category="connectivity", severity=sev,
                confidence="deterministic", evidence_source="topology", where=net, nets=[net],
                summary=f"net '{net}' connects only {members[0]} — dangling / unterminated",
                recommendation="terminate the net or remove the stub"))

        # E-DECOUPLE: a power rail with no capacitor anywhere on it (a heuristic expectation)
        if is_power and npins >= 2 and not any(_CAP.match(r) for r in refs):
            V.append(finding(
                detector="erc", rule_id="power_no_decoupling", category="connectivity",
                severity="warning", confidence="heuristic", evidence_source="heuristic_rule",
                where=net, nets=[net],
                summary=f"power rail '{net}' has no decoupling capacitor on it",
                recommendation="add a decoupling capacitor near the load"))

    return V
