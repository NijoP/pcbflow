"""Tests for R1 — the routing rulebook + IPC-2152 width driver. Standalone or pytest:
    python3 tests/test_routing_rules.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow import ipc  # noqa: E402
from pcbflow.routing_rules import DEFAULT, RoutingRules  # noqa: E402


# ── IPC-2152 width math ────────────────────────────────────────────
def test_ipc2152_width_plausible_and_inner_derating():
    outer = ipc.ipc2152_width_mm(2.0, delta_t_c=10.0, copper_oz=1.0)
    inner = ipc.ipc2152_width_mm(2.0, delta_t_c=10.0, copper_oz=0.5)
    assert 0.5 < outer < 1.2                                 # ~0.78 mm for 2 A @ ΔT10 on 1 oz
    assert abs(inner - 2 * outer) < 1e-6                     # 0.5 oz inner needs ~2× the width
    assert ipc.ipc2152_width_mm(0) == 0.0


def test_ipc2221_reference_still_available():
    # IPC-2221 reference kept; its blanket inner-halving is MORE conservative than IPC-2152's
    assert ipc.trace_width_mm(2.0, 10.0, copper_oz=1.0, internal=True) > \
        ipc.ipc2152_width_mm(2.0, 10.0, copper_oz=1.0)


# ── the rulebook ───────────────────────────────────────────────────
def test_default_rulebook_validates_clean():
    assert RoutingRules().validate() == []                  # every default rule is cited


def test_class_widths_derive_from_ipc2152():
    r = RoutingRules()
    assert abs(r.class_width_mm("POWER") - ipc.ipc2152_width_mm(2.0, 10.0, 1.0)) < 1e-9
    assert r.class_width_mm("SIGNAL") == 0.25               # explicit width
    assert abs(r.class_width_mm("POWER", "inner") - 2 * r.class_width_mm("POWER", "outer")) < 1e-6


def test_pour_threshold_current_and_width():
    r = RoutingRules()
    assert r.requires_pour(2.5) is True                     # ≥ 2 A current threshold
    assert r.requires_pour(0.5) is False
    assert r.requires_pour(1.5, "inner") is True            # width branch: 1.5 A on 0.5 oz > 1 mm


def test_validation_rejects_uncited_rule():
    bad = {"net_classes": {"HV": {"width_mm": 0.8}},         # numeric rule, no $cite
           "pour": {"current_threshold_a": 3.0}}            # also uncited
    problems = RoutingRules.from_dict(bad).validate()
    assert any("HV" in p for p in problems) and any("pour" in p for p in problems)


def test_default_rulebook_cites_standards():
    assert "IPC-2152" in DEFAULT["$standard"] and "IPC-2221" in DEFAULT["$standard"]


def _run():
    for nm, fn in sorted(globals().items()):
        if nm.startswith("test_") and callable(fn):
            fn()
    print("PASS — routing rules: IPC-2152 width + inner derating, IPC-2221 reference, rulebook "
          "validate, class-width derivation, pour threshold, uncited-rule rejection.")


if __name__ == "__main__":
    _run()
