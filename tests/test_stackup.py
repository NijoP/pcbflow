"""Tests for pcbflow.stackup — the physical stack-up model (foundation for the Tier-2 impedance
and current calcs). Standalone or pytest:  python3 tests/test_stackup.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow import stackup  # noqa: E402


def test_copper_thickness():
    assert abs(stackup.copper_thickness_mm(1.0) - 0.0347) < 1e-9
    assert abs(stackup.copper_thickness_mm(2.0) - 0.0694) < 1e-9


def test_two_layer_dielectric_to_reference():
    s = stackup.Stackup.two_layer(thickness_mm=1.6, copper_oz=1.0)
    assert [ly.name for ly in s.signal_layers()] == ["F.Cu", "B.Cu"]
    h, er = s.dielectric_to_reference("F.Cu")
    assert h == 1.6 and abs(er - stackup.FR4_ER) < 1e-9


def test_four_layer_finds_nearest_plane():
    s = stackup.Stackup.four_layer(copper_oz=1.0)
    # F.Cu references the In1.Cu GND plane 0.2 mm below it (microstrip geometry)
    h, er = s.dielectric_to_reference("F.Cu")
    assert abs(h - 0.2) < 1e-9 and er == stackup.FR4_ER
    assert s.dielectric_to_reference("does-not-exist") is None


if __name__ == "__main__":
    test_copper_thickness()
    test_two_layer_dielectric_to_reference()
    test_four_layer_finds_nearest_plane()
    print("PASS — stackup: copper thickness, 2-layer + 4-layer dielectric-to-reference.")
