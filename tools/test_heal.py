#!/usr/bin/env python3
"""Tests for Phase-3 self-healing: heal(), humanize(), and the pure recovery checks.
Run: python3 tools/test_heal.py"""
import tempfile
import heal as H
import recovery
from pcbflow_log import PhaseLogger


def _logger(root):
    return PhaseLogger("p", "ph", root=root)


def test_humanize():
    d = {"title": "X frozen", "why": "because Z", "class": "EDA-7",
         "retryable": True, "human_message": "do Y"}
    failed = H.humanize(d, "tried a reset", False)
    assert "What happened: X frozen" in failed and "Why: because Z" in failed
    assert "What you need to do: do Y" in failed
    ok = H.humanize(d, "tried a reset", True)
    assert "Recovered automatically" in ok and "What you need to do" not in ok


def test_heal_success():
    with tempfile.TemporaryDirectory() as t:
        r = H.heal(_logger(t), "step", lambda: 5)
        assert r["ok"] and r["v"] == 5


def test_heal_recovers_after_fix():
    # first call fails (session expired), the recovery fixes it, the retry succeeds
    with tempfile.TemporaryDirectory() as t:
        state = {"n": 0}
        def action():
            state["n"] += 1
            if state["n"] == 1:
                raise Exception("HTTP 401 Unauthorized")
            return "wired"
        r = H.heal(_logger(t), "step", action, recoveries={"session": lambda: True})
        assert r["ok"] and r.get("recovered") and r["v"] == "wired" and state["n"] == 2
        assert "Recovered automatically" in r["human"]


def test_heal_escalates_when_no_recovery():
    # KI-5 (kicad missing) has no automatic recovery → escalate with a human message
    with tempfile.TemporaryDirectory() as t:
        def action():
            raise Exception("kicad-cli: command not found")
        r = H.heal(_logger(t), "step", action, recoveries={})
        assert r["ok"] is False
        assert r["diagnosis"]["class"] == "KI-5"
        assert "install kicad" in r["human"].lower()


def test_heal_non_idempotent_does_not_rerun():
    # a non-idempotent live write is fixed but NOT auto-re-run (asks the engineer)
    with tempfile.TemporaryDirectory() as t:
        state = {"n": 0}
        def action():
            state["n"] += 1
            raise Exception("HTTP 429 Too Many Requests")
        r = H.heal(_logger(t), "step", action,
                   recoveries={"backoff": lambda: True}, idempotent=False)
        assert r["ok"] is False and r.get("env_fixed") and state["n"] == 1
        assert "say 'retry'" in r["human"]


def test_kicad_import_checks():
    assert recovery.verify_kicad_import(113, 113)["ok"]
    res = recovery.verify_kicad_import(113, 109)
    assert res["ok"] is False and res["dropped"] == 4
    assert recovery.missing_mounting_holes(["H1", "H2", "H3"], ["H1", "H3"]) == ["H2"]


if __name__ == "__main__":
    test_humanize()
    test_heal_success()
    test_heal_recovers_after_fix()
    test_heal_escalates_when_no_recovery()
    test_heal_non_idempotent_does_not_rerun()
    test_kicad_import_checks()
    print("PASS — heal: engine, humanize, escalation, non-idempotent guard, KiCad checks (6/6).")
