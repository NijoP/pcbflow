"""Tests for pcbflow.findings — the harmonized finding schema. Standalone or pytest:
    python3 tests/test_findings.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow import findings  # noqa: E402


def _f(**kw):
    base = dict(detector="erc", rule_id="floating_pin", category="connectivity",
                severity="error", confidence="deterministic", evidence_source="topology",
                summary="pin floats", where="R1.2", components=["R1"])
    base.update(kw)
    return findings.finding(**base)


def test_finding_has_full_schema():
    f = _f()
    assert findings.validate(f) == []
    for k in findings.FIELDS:
        assert k in f


def test_stable_id_is_deterministic():
    # same locator -> same id across calls (no time, no randomness)
    assert _f()["id"] == _f()["id"]
    # a different locator -> a different id
    assert _f(where="R9.1", components=["R9"])["id"] != _f()["id"]


def test_components_and_nets_are_sorted():
    f = findings.finding(detector="d", rule_id="r", category="c", severity="info",
                         confidence="heuristic", evidence_source="heuristic_rule",
                         summary="s", components=["U2", "R1", "C3"], nets=["Z", "A"])
    assert f["components"] == ["C3", "R1", "U2"] and f["nets"] == ["A", "Z"]


def test_bad_taxonomy_values_are_rejected():
    for bad in (dict(severity="critical"), dict(confidence="guess"),
                dict(evidence_source="vibes")):
        try:
            _f(**bad)
            assert False, f"should reject {bad}"
        except ValueError:
            pass


def test_validate_flags_missing_and_bad_fields():
    good = _f()
    broken = {k: v for k, v in good.items() if k != "severity"}
    problems = findings.validate(broken)
    assert any("missing field: severity" in p for p in problems)
    assert findings.validate({**good, "confidence": "nope"})  # non-empty


def test_sort_findings_errors_first_and_deterministic():
    fs = [_f(severity="info", rule_id="z", where="a"),
          _f(severity="error", rule_id="m", where="b"),
          _f(severity="warning", rule_id="a", where="c")]
    order = [f["severity"] for f in findings.sort_findings(fs)]
    assert order == ["error", "warning", "info"]
    # stable: sorting twice gives the identical id sequence
    ids1 = [f["id"] for f in findings.sort_findings(fs)]
    ids2 = [f["id"] for f in findings.sort_findings(list(reversed(fs)))]
    assert ids1 == ids2


def test_report_pass_fail_and_counts():
    fs = [_f(severity="error"), _f(severity="warning", where="X"), _f(severity="info", where="Y")]
    rep = findings.report(fs)
    assert rep["errors"] == 1 and rep["warnings"] == 1 and rep["infos"] == 1
    assert rep["total"] == 3 and rep["pass"] is False
    assert findings.report([])["pass"] is True


def test_trust_summary_levels():
    # all deterministic -> high
    det = [_f(confidence="deterministic", where=str(i)) for i in range(4)]
    assert findings.trust_summary(det)["level"] == "high"
    # majority heuristic -> low
    heur = [_f(confidence="heuristic", evidence_source="heuristic_rule", where=str(i))
            for i in range(3)] + [_f(where="x")]
    assert findings.trust_summary(heur)["level"] == "low"
    # even mix -> mixed
    mix = [_f(where="a"), _f(confidence="heuristic", evidence_source="heuristic_rule", where="b")]
    assert findings.trust_summary(mix)["level"] == "mixed"


def test_to_json_is_deterministic_and_valid():
    fs = [_f(severity="warning", where="b"), _f(severity="error", where="a")]
    j1 = findings.to_json(fs)
    j2 = findings.to_json(list(reversed(fs)))
    assert j1 == j2                              # byte-identical regardless of input order
    doc = json.loads(j1)
    assert doc["report"]["errors"] == 1 and doc["report"]["total"] == 2 and "trust" in doc
    for f in doc["findings"]:
        assert findings.validate(f) == []


def test_to_markdown_renders_table_and_empty():
    md = findings.to_markdown([_f(severity="error", where="a")], title="ERC")
    assert md.startswith("# ERC") and "FAIL" in md and "`floating_pin`" in md
    empty = findings.to_markdown([])
    assert "PASS" in empty and "No findings" in empty


def test_spacing_findings_wraps_geometry():
    parts = [{"ref": "R1", "layer": "TOP", "bbox": [0, 0, 1, 1]},
             {"ref": "R2", "layer": "TOP", "bbox": [1.2, 0, 2, 1]}]   # gap 0.2 < 0.5
    fs = findings.spacing_findings(parts, min_gap=0.5)
    assert len(fs) == 1
    f = fs[0]
    assert f["detector"] == "geometry.spacing" and f["rule_id"] == "spacing"
    assert f["components"] == ["R1", "R2"] and findings.validate(f) == []
    assert f["provenance"]["gap_mm"] == 0.2


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("PASS — findings: schema, stable id, sort, report, trust levels, deterministic JSON, spacing.")


if __name__ == "__main__":
    _run()
