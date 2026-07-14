"""Hardware checks — the electrical-correctness + integrity detectors, folded into harmonized
findings behind one entry point.

Tier 1 (electrical correctness) is wired now: pin-type ERC (drive conflicts), power-tree
integrity, and component-rating sanity. Tiers 2–4 (signal/power integrity, DFM/DFA, requirements)
are scoped in docs/HW_IMPLEMENTATION_PLAN.md and land next. All checks need the optional parts
spec (pcbflow.parts) — with none present, they report nothing (never guess).

Pure Python 3 standard library.
"""
from . import erc_pins, power_tree, ratings
from .enet import Enet
from .parts import Parts


def run(netlist, parts=None):
    """Run the hardware checks. `netlist` is a path (parts.json auto-loaded beside it) or an Enet
    (pass `parts` explicitly). Returns a flat list of harmonized findings."""
    if isinstance(netlist, Enet):
        enet, parts = netlist, (parts or Parts())
    else:
        enet = Enet.load(netlist)
        parts = parts or Parts.beside(netlist)
    fs = []
    fs += erc_pins.run(enet, parts)
    pt_findings, rails = power_tree.run(enet, parts)
    fs += pt_findings
    fs += ratings.run(enet, parts, rails)
    return fs
