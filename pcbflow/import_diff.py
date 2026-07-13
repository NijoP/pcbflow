"""Import diff — verify the EasyEDA→KiCad hand-off didn't silently corrupt the netlist.

Phase 10 (export-to-KiCad) is the point where a board most often drifts from its schematic:
a pad lands on the wrong net, a part gets dropped, a net vanishes. This module compares the
`.enet` netlist (the schematic contract) against the netlist read back from the `.kicad_pcb`
(pcbflow.kicad_sexp) and emits harmonized findings (pcbflow.findings) — so the check **fails
loudly** instead of a layout being built on a wrong import.

What it compares:
  - the component set (every part in the netlist must be on the board, and vice-versa);
  - **named** nets present on both sides — their component membership must match.
Auto-generated / anonymous nets ('$…' in EasyEDA, 'Net-(…)' / 'unconnected-…' in KiCad) can't
be matched by name across tools, so they're skipped by design (documented, not silently).

Comparison is at REF level (which components a net touches), which is the reliable invariant
across the pad/pin-naming differences between the two EDA tools. Pure Python 3 stdlib.
"""
from . import kicad_sexp
from .enet import Enet
from .findings import finding


def _is_auto_kicad_net(net):
    return (not net) or net.startswith("Net-(") or net.startswith("unconnected-")


def _enet_view(enet):
    comps = {c.designator or c.id for c in enet.components.values()}
    net_refs = {}
    for net, members in enet.nets().items():
        if net.startswith("$"):                      # EasyEDA auto/unnamed net — unmatchable
            continue
        net_refs[net] = {m.split(".", 1)[0] for m in members}
    return comps, net_refs


def _pcb_view(pcb):
    comps = {c["ref"] for c in pcb["components"] if c["ref"]}
    net_refs = {}
    for net, members in pcb["nets"].items():
        if _is_auto_kicad_net(net):
            continue
        net_refs[net] = {m.split(".", 1)[0] for m in members}
    return comps, net_refs


def _f(rule_id, severity, summary, where="", components=None, nets=None, provenance=None):
    return finding(detector="import_diff", rule_id=rule_id, category="import", severity=severity,
                   confidence="deterministic", evidence_source="topology", summary=summary,
                   where=where, components=components, nets=nets, provenance=provenance,
                   recommendation="re-run the KiCad import and re-check, or fix the mapping")


def diff(enet, pcb):
    """Compare an Enet against a pcb netlist dict (kicad_sexp.read_pcb_netlist). → list of findings."""
    ec, en = _enet_view(enet)
    pc, pn = _pcb_view(pcb)
    out = []

    # component set — a dropped or extra part is an error
    for ref in sorted(ec - pc):
        out.append(_f("component_missing_in_board", "error",
                      f"component {ref} is in the netlist but not on the board",
                      where=ref, components=[ref]))
    for ref in sorted(pc - ec):
        out.append(_f("component_extra_in_board", "error",
                      f"component {ref} is on the board but not in the netlist",
                      where=ref, components=[ref]))

    # named nets missing on one side
    for net in sorted(set(en) - set(pn)):
        out.append(_f("net_missing_in_board", "error",
                      f"named net '{net}' is in the netlist but not on the board",
                      where=net, nets=[net]))
    for net in sorted(set(pn) - set(en)):
        out.append(_f("net_extra_in_board", "warning",
                      f"named net '{net}' is on the board but not in the netlist "
                      "(possible rename or added net)", where=net, nets=[net]))

    # nets on both sides — component membership must match
    for net in sorted(set(en) & set(pn)):
        only_nl = en[net] - pn[net]
        only_bd = pn[net] - en[net]
        if only_nl or only_bd:
            out.append(_f("net_connectivity_mismatch", "error",
                          f"net '{net}' connects {sorted(en[net])} in the netlist but "
                          f"{sorted(pn[net])} on the board",
                          where=net, nets=[net],
                          components=sorted(only_nl | only_bd),
                          provenance={"only_in_netlist": sorted(only_nl),
                                      "only_on_board": sorted(only_bd)}))
    return out


def check(enet_path, board_path):
    """Load an `.enet` and a `.kicad_pcb`, diff them. Returns (findings, report-dict)."""
    from .findings import report
    enet = Enet.load(enet_path)
    pcb = kicad_sexp.read_pcb_netlist(board_path)
    fs = diff(enet, pcb)
    return fs, report(fs)
