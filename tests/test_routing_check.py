"""Tests for R2 — routing checks against the routed board (pour required, IPC-2152 width, max
length, return path). Standalone or pytest:  python3 tests/test_routing_check.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow import findings, routing_check  # noqa: E402
from pcbflow.enet import Enet  # noqa: E402
from pcbflow.routing_rules import RoutingRules  # noqa: E402


def _enet(net_class=None):
    return Enet.from_dict({"version": "2.0.0", "netClass": net_class or {}, "components": {
        "u": {"props": {"Designator": "U1"}, "pinInfoMap": {"1": {"number": "1", "name": "1", "net": "X"}}}}})


def _board(tracks, zones=()):
    """tracks = [(net, width_mm, length_mm)]; zones = [(net, filled_bool)]. Horizontal segments."""
    names = sorted({t[0] for t in tracks} | {z[0] for z in zones})
    idmap = {n: i + 1 for i, n in enumerate(names)}
    lines = ['(kicad_pcb (version 1)', '(net 0 "")']
    lines += [f'(net {i} "{n}")' for n, i in idmap.items()]
    for net, w, length in tracks:
        lines.append(f'(segment (start 0 0) (end {length} 0) (width {w}) (layer "F.Cu") '
                     f'(net {idmap[net]}))')
    for net, filled in zones:
        fp = '(filled_polygon (layer "B.Cu") (pts (xy 0 0)))' if filled else ''
        lines.append(f'(zone (net {idmap[net]}) (net_name "{net}") (layer "B.Cu") {fp})')
    return "\n".join(lines) + "\n)"


def _rules(fs):
    return {f["rule_id"] for f in fs}


R = RoutingRules()


def test_high_current_on_trace_fires():
    board = _board([("PWR", 0.5, 5)])                       # 3 A on a trace, no pour
    fs = routing_check.run(_enet(), board, R, currents={"PWR": 3.0})
    assert "high_current_on_trace" in _rules(fs)


def test_poured_high_current_net_is_ok_for_pour_rule():
    board = _board([("PWR", 2.0, 5)], zones=[("PWR", True)])   # wide + poured
    fs = routing_check.run(_enet(), board, R, currents={"PWR": 3.0})
    assert "high_current_on_trace" not in _rules(fs)


def test_trace_underwidth_fires():
    board = _board([("SIG", 0.1, 5)])                        # 1 A needs ~0.30 mm, only 0.1
    fs = routing_check.run(_enet(), board, R, currents={"SIG": 1.0})
    assert "trace_underwidth" in _rules(fs)


def test_over_length_fires():
    e = _enet({"CLK": {"nets": ["CK"], "$cite": "x"}})
    board = _board([("CK", 0.25, 60)])                       # 60 mm > CLK max 50 mm
    assert "over_length" in _rules(routing_check.run(e, board, R))


def test_return_path_missing_fires():
    e = _enet({"USB_DIFF": {"nets": ["DP"], "$cite": "x"}})
    board = _board([("DP", 0.25, 10)])                       # impedance class, no GND plane
    assert "return_path_missing" in _rules(routing_check.run(e, board, R))


def test_return_path_ok_with_gnd_plane():
    e = _enet({"USB_DIFF": {"nets": ["DP"], "$cite": "x"}})
    board = _board([("DP", 0.25, 10)], zones=[("GND", True)])
    assert "return_path_missing" not in _rules(routing_check.run(e, board, R))


def test_routing_findings_harmonized():
    board = _board([("PWR", 0.1, 5)])
    for f in routing_check.run(_enet(), board, R, currents={"PWR": 3.0}):
        assert findings.validate(f) == [] and f["detector"] == "routing"


def _run():
    for nm, fn in sorted(globals().items()):
        if nm.startswith("test_") and callable(fn):
            fn()
    print("PASS — routing checks: pour required, poured-ok, under-width, over-length, "
          "return-path missing/ok.")


if __name__ == "__main__":
    _run()
