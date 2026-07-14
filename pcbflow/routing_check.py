"""Routing checks against the routed board (R2) — enforce the rulebook (pcbflow.routing_rules) on
the `.kicad_pcb`. Emits harmonized findings.

Checks:
  - **pour required:** a net whose current ≥ the rulebook threshold (≥ 2.0 A or IPC-2152 width
    > 1.0 mm) that is on traces without a filled pour → error.
  - **trace under-width:** a net's minimum track width < the IPC-2152 width its current needs → error.
  - **over length:** a net longer than its net class's `max_length_mm` → warning.
  - **return path:** a high-speed (impedance-class) net with no GND reference plane pour → warning.

Net currents come from the power tree (`rails`) or an explicit `currents` override; net classes
from the `.enet` `netClass`. Pure Python 3 standard library.
"""
from . import ipc, kicad_sexp
from .design_index import _GND
from .findings import finding


def _f(rule_id, severity, summary, where, nets=None, prov=None, rec=""):
    return finding(detector="routing", rule_id=rule_id, category="routing", severity=severity,
                   confidence="deterministic", evidence_source="geometry", summary=summary,
                   where=where, nets=nets, provenance=prov, recommendation=rec)


def run(enet, board, rules, rails=None, currents=None):
    geo = kicad_sexp.read_pcb_geometry(board)
    zones = kicad_sexp.read_pcb_zones(board)
    lengths = kicad_sexp.net_lengths(geo)
    poured = kicad_sexp.poured_nets(zones)
    net_class = enet.net_class_map()
    rails, currents = rails or {}, currents or {}
    V = []

    def current(net):
        if net in currents:
            return currents[net]
        return (rails.get(net) or {}).get("i_load") or 0.0

    min_w = {}
    for t in geo["tracks"]:
        if t["net"] and t["width"] > 0:
            min_w[t["net"]] = min(min_w.get(t["net"], 1e9), t["width"])

    for net, w in min_w.items():
        i = current(net)
        if i <= 0:
            continue
        if rules.requires_pour(i) and net not in poured:
            V.append(_f("high_current_on_trace", "error",
                        f"net '{net}' carries {i} A (≥ pour threshold) but is routed on traces, "
                        "not a pour", net, [net], {"i_a": i},
                        "convert this net to a polygon pour with thermal relief"))
        req = ipc.ipc2152_width_mm(i, rules.delta_t(), rules.copper_oz("outer"))
        if w < req - 1e-6:
            V.append(_f("trace_underwidth", "error",
                        f"net '{net}' min width {w} mm < {req:.3f} mm needed for {i} A (IPC-2152)",
                        net, [net], {"width_mm": w, "required_mm": round(req, 3), "i_a": i},
                        "widen the trace or pour the net"))

    for net, cls in net_class.items():
        max_l = rules.net_class(cls).get("max_length_mm")
        if max_l and lengths.get(net, 0.0) > max_l + 1e-9:
            V.append(_f("over_length", "warning",
                        f"net '{net}' ({cls}) is {lengths[net]} mm > {max_l} mm max", net, [net],
                        {"length_mm": lengths[net], "max_mm": max_l}, "shorten or reroute"))

    hs_classes = {c for c, s in (rules.spec.get("net_classes") or {}).items() if "impedance_ohm" in s}
    has_gnd_plane = any(z["filled"] and _GND.match(z["net"] or "") for z in zones)
    if rules.emi().get("return_path_continuity") and hs_classes and not has_gnd_plane:
        for net, cls in net_class.items():
            if cls in hs_classes:
                V.append(_f("return_path_missing", "warning",
                            f"high-speed net '{net}' ({cls}) has no GND reference-plane pour",
                            net, [net], rec="add a GND plane on the adjacent layer"))
    return V
