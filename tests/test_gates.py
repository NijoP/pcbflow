"""Tests for pcbflow.gates — machine-computed phase gates + the hard-blocked export.
Proves gates RUN the checks (not stored assertions) and that export refuses without a PASS on
every gate AND a human approval file. Standalone or pytest:  python3 tests/test_gates.py"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow import cli, gates  # noqa: E402
from pcbflow.gates import GateOutcome  # noqa: E402


def _pin(num, net):
    return {"name": num, "number": num, "net": net}


def _comp(des, pins):
    return {"props": {"Designator": des}, "pinInfoMap": {p: _pin(p, n) for p, n in pins.items()}}


CLEAN_ENET = {"version": "2.0.0", "components": {
    "u": _comp("U1", {"1": "VBUS", "2": "GND", "3": "+3V3"}),
    "ci": _comp("C1", {"1": "VBUS", "2": "GND"}),
    "co": _comp("C2", {"1": "+3V3", "2": "GND"})}}
BAD_ENET = {"version": "2.0.0", "components": {"r": _comp("R1", {"1": "NET1", "2": ""})}}  # floating + no gnd


def _proj(enet_dict, extra=None):
    """Create a temp project dir with 04_schematic/netlist.enet (+ optional extra files)."""
    d = tempfile.mkdtemp()
    sub = os.path.join(d, "04_schematic")
    os.makedirs(sub)
    with open(os.path.join(sub, "netlist.enet"), "w") as f:
        json.dump(enet_dict, f)
    for rel, content in (extra or {}).items():
        with open(os.path.join(d, rel), "w") as f:
            f.write(content)
    return d


def test_combine_precedence():
    def g(s):
        return GateOutcome("x", s, "")
    assert gates.combine([g("PASS"), g("WARN")]) == "WARN"
    assert gates.combine([g("PASS"), g("FAIL"), g("WARN")]) == "FAIL"
    assert gates.combine([g("EMPTY"), g("FAIL")]) == "EMPTY"        # EMPTY dominates FAIL
    assert gates.combine([g("BLOCKED"), g("EMPTY")]) == "BLOCKED"   # BLOCKED dominates EMPTY
    assert gates.combine([g("PASS"), g("PASS")]) == "PASS"
    assert gates.combine([]) == "EMPTY"


def test_schematic_gate_computes_pass_and_fail():
    with tempfile.NamedTemporaryFile("w", suffix=".enet", delete=False) as f:
        json.dump(CLEAN_ENET, f); clean = f.name
    with tempfile.NamedTemporaryFile("w", suffix=".enet", delete=False) as f:
        json.dump(BAD_ENET, f); bad = f.name
    assert gates.gate_schematic(clean).status == "PASS"
    out = gates.gate_schematic(bad)
    assert out.status == "FAIL" and out.details          # floating pin + no ground -> real errors


def test_dfm_gate_computes():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"board": {"layers": 2, "size_mm": [40, 55]},
                   "tracks": [{"net": "VSYS", "width": 0.30, "layer": "F"}]}, f); good = f.name
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"board": {"layers": 2}, "tracks": [{"net": "SDA", "width": 0.10, "layer": "F"}]}, f)
        bad = f.name
    assert gates.gate_dfm(good).status == "PASS"
    assert gates.gate_dfm(bad).status == "FAIL"


def test_drc_gate_injected_runner():
    assert gates.gate_drc("b.kicad_pcb", lambda b: {"ok": True, "report": "r"}).status == "PASS"
    assert gates.gate_drc("b.kicad_pcb", lambda b: {"ok": False, "violations": True}).status == "FAIL"
    assert gates.gate_drc("b.kicad_pcb", lambda b: {"ok": False, "reason": "x"}).status == "BLOCKED"
    assert gates.gate_drc("b.kicad_pcb", None).status == "BLOCKED"    # no runner -> not a silent pass


def test_approval_error():
    assert "no approval" in gates.approval_error(None)
    assert "not found" in gates.approval_error("/no/such/file.json")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"approved_by": "Jane"}, f); partial = f.name          # missing 2 fields
    assert "missing fields" in gates.approval_error(partial)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"approved_by": "Jane", "approved_at_utc": "2026-07-14T00:00:00Z",
                   "scope": "rev A gerbers"}, f); ok = f.name
    assert gates.approval_error(ok) is None


def _approval(scope="rev A"):
    p = tempfile.mktemp(suffix=".json")
    with open(p, "w") as f:
        json.dump({"approved_by": "Jane", "approved_at_utc": "2026-07-14T00:00:00Z", "scope": scope}, f)
    return p


def test_export_hard_block_matrix():
    clean = _proj(CLEAN_ENET)
    bad = _proj(BAD_ENET)
    # clean gates + valid approval -> cleared
    cleared, outs, reasons = gates.export_check(clean, _approval())
    assert cleared and not reasons, reasons
    # clean gates + NO approval -> blocked (human sign-off required, never automated)
    cleared, _, reasons = gates.export_check(clean, None)
    assert not cleared and any("approval" in r for r in reasons)
    # FAILING gate + valid approval -> STILL blocked (you cannot approve past a failing gate)
    cleared, _, reasons = gates.export_check(bad, _approval())
    assert not cleared and any("schematic" in r for r in reasons)


def test_compute_phase_gate_and_verdict_mapping():
    clean = _proj(CLEAN_ENET)
    assert gates.compute_phase_gate(clean, 5).status == "PASS"
    assert gates.compute_phase_gate(clean, 6).status == "EMPTY"        # no placement artifact
    assert gates.compute_phase_gate(clean, 1).status == "EMPTY"        # no computed gate
    assert gates.status_to_verdict("PASS") == "PASS"
    assert gates.status_to_verdict("WARN") == "CONDITIONAL"
    assert gates.status_to_verdict("FAIL") == "FAIL"
    assert gates.status_to_verdict("BLOCKED") == "PENDING"


def test_cli_gate_records_and_export_blocks(monkeypatch=None):
    import pathlib
    proj = _proj(CLEAN_ENET)
    parent = pathlib.Path(proj).parent
    name = pathlib.Path(proj).name
    orig = cli.PROJECTS
    cli.PROJECTS = parent
    try:
        # `gate 5` runs the real check and records PASS
        assert cli.main(["gate", name, "5"]) == 0
        from pcbflow.project import Project
        assert Project(parent / name).latest_verdict(5)["verdict"] == "PASS"
        # export blocked without approval, cleared with it
        assert cli.main(["export", name]) == 1
        assert cli.main(["export", name, "--approval", _approval()]) == 0
    finally:
        cli.PROJECTS = orig


def _run():
    for nm, fn in sorted(globals().items()):
        if nm.startswith("test_") and callable(fn):
            fn()
    print("PASS — gates: precedence, computed schematic/dfm/drc gates, approval, export hard-block, CLI.")


if __name__ == "__main__":
    _run()
