"""Tests for the Tier-1 hardware checks (pin-type ERC, power tree, component ratings). Proves the
electrical-correctness detectors fire on real failures and stay clean on the good example.
Standalone or pytest:  python3 tests/test_hw.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow import findings, hw  # noqa: E402
from pcbflow.enet import Enet  # noqa: E402
from pcbflow.parts import Parts  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _enet(comps):
    return Enet.from_dict({"version": "2.0.0", "components": {
        cid: {"props": {"Designator": des},
              "pinInfoMap": {p: {"number": p, "name": p, "net": n} for p, n in pins.items()}}
        for cid, (des, pins) in comps.items()}})


def _rules(fs):
    return {f["rule_id"] for f in fs}


def test_clean_example_passes_hw():
    path = os.path.join(REPO, "projects", "example-usb-c-3v3", "04_schematic", "netlist.enet")
    if os.path.exists(path):
        fs = hw.run(path)
        assert findings.report(fs)["pass"], [f["summary"] for f in fs]


def test_driver_contention():
    e = _enet({"u": ("U1", {"1": "D"}), "v": ("U2", {"1": "D"}), "r": ("R1", {"1": "D", "2": "GND"})})
    p = Parts.from_dict({"U1": {"pins": {"1": "out"}}, "U2": {"pins": {"1": "out"}}})
    assert "driver_contention" in _rules(hw.run(e, p))


def test_output_on_power_rail():
    e = _enet({"u": ("U1", {"1": "N"}), "reg": ("U2", {"1": "N"})})
    p = Parts.from_dict({"U1": {"pins": {"1": "out"}}, "U2": {"pins": {"1": "pwr_out"}}})
    assert "output_on_power" in _rules(hw.run(e, p))


def test_cap_underrated():
    e = _enet({"j": ("J1", {"1": "VBUS", "2": "GND"}), "c": ("C1", {"1": "VBUS", "2": "GND"})})
    p = Parts.from_dict({"J1": {"pins": {"1": "pwr_out"}, "ratings": {"v_nominal": 5.0}},
                         "C1": {"role": "cap", "ratings": {"v_rating": 6.0}}})   # 6 < 2*5
    assert "cap_underrated" in _rules(hw.run(e, p))


def test_ldo_dropout_brownout():
    e = _enet({"src": ("J1", {"1": "VIN"}), "u": ("U1", {"1": "VIN", "2": "VOUT"})})
    p = Parts.from_dict({"J1": {"pins": {"1": "pwr_out"}, "ratings": {"v_nominal": 3.3}},
                         "U1": {"role": "ldo", "pins": {"1": "pwr_in", "2": "pwr_out"},
                                "ratings": {"vout": 3.3, "vdropout": 0.3}}})   # 3.3-3.3 < 0.3
    assert "ldo_dropout" in _rules(hw.run(e, p))


def test_led_overcurrent():
    e = _enet({"j": ("J1", {"1": "V5"}), "r": ("R1", {"1": "V5", "2": "A"}), "d": ("D1", {"1": "A", "2": "GND"})})
    p = Parts.from_dict({"J1": {"pins": {"1": "pwr_out"}, "ratings": {"v_nominal": 5.0}},
                         "R1": {"role": "resistor", "ratings": {"r_ohm": 100}},   # (5-2)/100 = 30 mA
                         "D1": {"role": "led", "ratings": {"vf": 2.0, "i_max": 0.02}}})
    assert "led_overcurrent" in _rules(hw.run(e, p))


def test_unsourced_rail():
    e = _enet({"u": ("U1", {"1": "P3V3", "2": "GND"})})
    p = Parts.from_dict({"U1": {"pins": {"1": "pwr_in", "2": "passive"}}})   # sink, no source
    assert "unsourced_rail" in _rules(hw.run(e, p))


def test_current_budget_exceeded():
    e = _enet({"reg": ("U1", {"1": "R"}), "load": ("U2", {"1": "R"})})
    p = Parts.from_dict({"U1": {"pins": {"1": "pwr_out"}, "ratings": {"vout": 3.3, "iout_max": 0.5}},
                         "U2": {"pins": {"1": "pwr_in"}, "ratings": {"i_load": 0.8}}})   # 0.8 > 0.5
    assert "current_budget" in _rules(hw.run(e, p))


def test_hw_findings_are_harmonized():
    e = _enet({"u": ("U1", {"1": "D"}), "v": ("U2", {"1": "D"})})
    p = Parts.from_dict({"U1": {"pins": {"1": "out"}}, "U2": {"pins": {"1": "out"}}})
    for f in hw.run(e, p):
        assert findings.validate(f) == [] and f["detector"] in ("erc_pins", "power_tree", "ratings")


def _run():
    for nm, fn in sorted(globals().items()):
        if nm.startswith("test_") and callable(fn):
            fn()
    print("PASS — hw: clean example, contention, output-on-power, cap derating, LDO dropout, "
          "LED overcurrent, unsourced rail, current budget.")


if __name__ == "__main__":
    _run()
