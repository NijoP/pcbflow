"""Tests for pcbflow.erc — netlist electrical rule check. Standalone or pytest:
    python3 tests/test_erc.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow.enet import Enet    # noqa: E402
from pcbflow import erc          # noqa: E402


def _pin(num, net):
    return {"name": num, "number": num, "net": net, "props": {}}


def _comp(des, pins):
    return {"props": {"Designator": des}, "pinInfoMap": {p: _pin(p, n) for p, n in pins.items()}}


# clean: LDO + input/output caps on power rails, real ground, nothing dangling
CLEAN = {"version": "2.0.0", "components": {
    "u": _comp("U1", {"1": "VBUS", "2": "GND", "3": "+3V3"}),
    "ci": _comp("C1", {"1": "VBUS", "2": "GND"}),
    "co": _comp("C2", {"1": "+3V3", "2": "GND"}),
}}


def test_clean_passes():
    v = erc.run_erc(Enet.from_dict(CLEAN))
    assert v == [], v
    assert erc.report(v)["pass"] is True


def test_floating_pin_is_error():
    d = {"version": "2.0.0", "components": {"r": _comp("R1", {"1": "NET1", "2": ""})}}
    v = erc.run_erc(Enet.from_dict(d))
    assert any(x["rule_id"] == "floating_pin" and x["severity"] == "error" and x["where"] == "R1.2"
               for x in v), v


def test_no_ground_is_error():
    d = {"version": "2.0.0", "components": {
        "u": _comp("U1", {"1": "VBUS", "2": "AGND_TYPO"}),      # not a recognized ground name
        "c": _comp("C1", {"1": "VBUS", "2": "AGND_TYPO"})}}
    # AGND matches _GND? _GND = GND|GNDA|AGND|DGND|PGND -> "AGND_TYPO" won't ^match fully
    v = erc.run_erc(Enet.from_dict(d))
    assert any(x["rule_id"] == "no_ground" for x in v), v


def test_single_pin_net_dangling():
    d = {"version": "2.0.0", "components": {
        "u": _comp("U1", {"1": "SDA", "2": "GND"}),            # SDA reaches only U1.1
        "c": _comp("C1", {"1": "V", "2": "GND"})}}
    v = erc.run_erc(Enet.from_dict(d))
    assert any(x["rule_id"] == "single_pin_net" and x["where"] == "SDA" for x in v), v


def test_power_rail_without_decoupling_warns():
    d = {"version": "2.0.0", "components": {
        "u": _comp("U1", {"1": "+3V3", "2": "GND"}),
        "r": _comp("R1", {"1": "+3V3", "2": "GND"})}}         # power rail, no cap
    v = erc.run_erc(Enet.from_dict(d))
    w = [x for x in v if x["rule_id"] == "power_no_decoupling"]
    assert w and w[0]["severity"] == "warning" and w[0]["where"] == "+3V3", v


def test_erc_findings_are_harmonized():
    """Every ERC finding conforms to the harmonized schema (pcbflow.findings)."""
    from pcbflow import findings
    d = {"version": "2.0.0", "components": {"r": _comp("R1", {"1": "NET1", "2": ""})}}
    v = erc.run_erc(Enet.from_dict(d))
    assert v, "expected at least one finding"
    for f in v:
        assert findings.validate(f) == [], (f, findings.validate(f))
        assert f["detector"] == "erc" and f["id"] and f["confidence"] in findings.CONFIDENCES


def test_example_project_passes_erc():
    """The shipped worked example must be electrically clean."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "projects", "example-usb-c-3v3", "04_schematic", "netlist.enet")
    if os.path.exists(path):
        v = erc.run_erc(Enet.load(path))
        assert erc.report(v)["pass"] is True, v


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("PASS — erc: clean pass, floating pin, no-ground, dangling net, decoupling, example board.")


if __name__ == "__main__":
    _run()
