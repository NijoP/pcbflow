"""Tests for pcbflow.import_diff — the EasyEDA→KiCad import verifier. It must PASS on a matching
board and FAIL LOUDLY on an injected net/component mismatch. Standalone or pytest:
    python3 tests/test_import_diff.py"""
import copy
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow import cli, findings, import_diff, kicad_sexp  # noqa: E402
from pcbflow.enet import Enet  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "mini_board.kicad_pcb")


def _pin(num, net):
    return {"name": num, "number": num, "net": net}


def _comp(des, pins):
    return {"props": {"Designator": des}, "pinInfoMap": {p: _pin(p, n) for p, n in pins.items()}}


# an .enet whose named nets match mini_board.kicad_pcb exactly (U1.4 unconnected)
ENET = {"version": "2.0.0", "components": {
    "r": _comp("R1", {"1": "VBUS", "2": "+3V3"}),
    "c": _comp("C1", {"1": "VBUS", "2": "GND"}),
    "u": _comp("U1", {"1": "VBUS", "2": "GND", "3": "+3V3", "4": ""}),
}}


def _pcb():
    return kicad_sexp.read_pcb_netlist(FIXTURE)


def test_matching_netlist_passes():
    fs = import_diff.diff(Enet.from_dict(ENET), _pcb())
    assert fs == [], fs


def test_injected_net_mismatch_fails_loudly():
    pcb = _pcb()
    # move R1.2 from +3V3 to GND on the board only -> two named nets now disagree
    pcb["nets"]["+3V3"].remove("R1.2")
    pcb["nets"]["GND"] = sorted(pcb["nets"]["GND"] + ["R1.2"])
    fs = import_diff.diff(Enet.from_dict(ENET), pcb)
    mism = [f for f in fs if f["rule_id"] == "net_connectivity_mismatch"]
    assert {f["where"] for f in mism} == {"+3V3", "GND"}, fs
    assert findings.report(fs)["pass"] is False


def test_dropped_component_fails():
    pcb = _pcb()
    pcb["components"] = [c for c in pcb["components"] if c["ref"] != "U1"]
    pcb["nets"] = {n: [m for m in ms if not m.startswith("U1.")] for n, ms in pcb["nets"].items()}
    fs = import_diff.diff(Enet.from_dict(ENET), pcb)
    assert any(f["rule_id"] == "component_missing_in_board" and f["where"] == "U1" for f in fs)
    assert findings.report(fs)["pass"] is False


def test_findings_are_harmonized():
    pcb = _pcb()
    pcb["nets"]["GND"].append("R1.2")
    for f in import_diff.diff(Enet.from_dict(ENET), pcb):
        assert findings.validate(f) == [] and f["detector"] == "import_diff"


def test_cli_import_check_match_and_mismatch():
    with tempfile.TemporaryDirectory() as t:
        enet_path = os.path.join(t, "n.enet")
        with open(enet_path, "w") as f:
            json.dump(ENET, f)
        # matching board -> exit 0
        assert cli.main(["import-check", enet_path, FIXTURE]) == 0

        # write a mismatched board (R1 pad2 moved to GND) -> exit 1
        bad = copy.deepcopy(ENET)                       # reuse structure to synth a bad board
        bad_board = os.path.join(t, "bad.kicad_pcb")
        with open(bad_board, "w") as f:
            f.write('(kicad_pcb (version 1) (net 0 "") (net 1 "GND")'
                    '  (footprint "x" (property "Reference" "R1")'
                    '    (pad "1" smd (net 1 "GND")) (pad "2" smd (net 1 "GND"))))')
        assert cli.main(["import-check", enet_path, bad_board]) == 1


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("PASS — import_diff: match passes, injected mismatch + dropped component fail loudly, CLI.")


if __name__ == "__main__":
    _run()
