"""Tests for pcbflow.dfm — the data-driven DRC/DFM RuleSet. Standalone or pytest:
    python3 tests/test_dfm.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow.dfm import RuleSet, run_dfm, report  # noqa: E402


def test_profile_matches_reference_numbers():
    rs = RuleSet.jlcpcb(layers=4, copper_oz="1oz")
    assert rs.name == "JLCPCB-4L-1oz" and rs.profile["vendor"] == "JLCPCB"
    # numbers must match knowledge/design-standards.md §DFM
    assert rs.limit("min_track_width") == 0.15
    assert rs.limit("copper_to_edge") == 0.25
    assert rs.limit("hole_to_copper") == 0.20
    assert rs.limit("min_via_drill") == 0.20
    assert rs.limit("min_via_pad") == 0.50
    assert rs.limit("min_annular_ring") == 0.10


def test_clean_board_passes():
    rs = RuleSet.jlcpcb(2)
    design = {"board": {"layers": 2, "size_mm": [40, 55]},
              "tracks": [{"net": "VSYS", "width": 0.30, "layer": "F"}],
              "vias": [{"net": "GND", "drill": 0.30, "pad": 0.60, "x": 0, "y": 0}],
              "silk": [{"ref": "R1", "width": 0.20, "height": 1.0}]}
    v = run_dfm(design, rs)
    assert v == [], v
    assert report(v)["pass"] is True


def test_threshold_violations_flagged():
    rs = RuleSet.jlcpcb(2)
    design = {"board": {"size_mm": [600, 55]},                    # 600 > max_board_edge
              "tracks": [{"net": "SDA", "width": 0.10, "layer": "F"}],   # < 0.15
              "vias": [{"net": "A", "drill": 0.15, "pad": 0.30, "x": 0, "y": 0}],  # drill<0.20,pad<0.50,ann<0.10
              "silk": [{"ref": "U1", "width": 0.10, "height": 0.6}]}    # both < min
    v = run_dfm(design, rs)
    rules = {x["rule"] for x in v}
    assert {"max_board_edge", "min_track_width", "min_via_drill", "min_via_pad",
            "min_annular_ring", "min_silk_width", "min_silk_height"} <= rules, rules
    rep = report(v)
    assert rep["errors"] >= 5 and rep["warnings"] >= 2 and rep["pass"] is False
    # every violation carries a coordinate/ref location + reason (DFM 'coord+reason' pattern)
    assert all(x["where"] and x["reason"] for x in v)


def test_hole_to_hole_true_distance_and_same_net_skip():
    rs = RuleSet.jlcpcb(2)
    # two 0.3mm-drill holes, centres 0.6mm apart -> edge gap 0.6-0.3 = 0.30 >= 0.50? no -> violation
    design = {"vias": [{"net": "A", "drill": 0.30, "x": 0, "y": 0},
                       {"net": "B", "drill": 0.30, "x": 0.6, "y": 0}]}
    assert any(x["rule"] == "min_hole_to_hole" for x in run_dfm(design, rs))
    # same net -> skipped (no spacing rule between same-net copper)
    design["vias"][1]["net"] = "A"
    assert not any(x["rule"] == "min_hole_to_hole" for x in run_dfm(design, rs))


def test_phantom_drc_guard():
    try:
        run_dfm({}, None)
        assert False, "should refuse to check without a ruleset"
    except ValueError as e:
        assert "phantom" in str(e).lower()


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("PASS — dfm: reference numbers, clean pass, threshold viols, hole-to-hole+same-net, phantom guard.")


if __name__ == "__main__":
    _run()
