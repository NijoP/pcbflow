#!/usr/bin/env python3
"""Minimal test for pcbflow_log — proves the {ok,err} envelope never swallows errors
and that the JSONL schema is written correctly. Run: python3 tools/test_pcbflow_log.py"""
import tempfile, json
from pathlib import Path
import pcbflow_log


def _boom():
    raise ValueError("boom")


def test_envelope_and_schema():
    with tempfile.TemporaryDirectory() as d:
        log = pcbflow_log.PhaseLogger("t", "04-x", root=d)

        # success path: envelope carries the value, logs "ok"
        r1 = log.run("good step", lambda: 42)
        assert r1["ok"] is True and r1["v"] == 42

        # failure path: error returned as DATA, not raised; logged as "failed"
        r2 = log.run("bad step", _boom, error_class="SC-1")
        assert r2["ok"] is False and "boom" in r2["err"]

        # recovery record
        log.recovered("retry step", "EDA-5", "exponential backoff", attempts=2,
                      human_message="EasyEDA throttled; waited and continued.")

        lines = Path(d, "t", ".logs", "04-x.jsonl").read_text().strip().splitlines()
        assert len(lines) == 3, f"expected 3 records, got {len(lines)}"
        recs = [json.loads(l) for l in lines]
        assert recs[0]["status"] == "ok"
        assert recs[1]["status"] == "failed" and recs[1]["error"]["class"] == "SC-1"
        assert recs[1]["error"]["stack"]                       # stack captured for the AI
        assert recs[2]["status"] == "recovered" and recs[2]["recovery"]["attempts"] == 2
        for r in recs:                                          # every record has the schema core
            assert r["ts"] and r["project"] == "t" and r["phase"] == "04-x" and r["step"]

    print("PASS — pcbflow_log: envelope never swallows, JSONL schema correct (3/3 records).")


if __name__ == "__main__":
    test_envelope_and_schema()
