#!/usr/bin/env python3
"""
axon_log — structured logging for Tracewright automation.

Implements the two things Phase 1 of the reliability roadmap needs:

  1. The {ok, err} envelope  — every wrapped step returns success-or-error as DATA,
     so a failure is never silently swallowed (vulnerability SC-7).
  2. The JSONL log schema     — one record per attempt, readable by both the AI and
     the engineer, written to  projects/<board>/.logs/<phase>.jsonl

See reliability/SELF_HEALING.md §1 for the schema design.

Use in a Python automation step:

    from axon_log import PhaseLogger
    log = PhaseLogger("door-sensor", "04-schematic-generation")
    result = log.run("wire block U3 (IMU)", lambda: wire_imu())
    if not result["ok"]:
        ...   # the failure is logged; decide recovery

Render a phase log for a human:

    python3 tools/axon_log.py render projects/door-sensor/.logs/04-schematic-generation.jsonl
"""
import json, sys, traceback, datetime
from pathlib import Path


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class PhaseLogger:
    """Append-only structured log for one project phase."""

    def __init__(self, project, phase, root="projects"):
        self.project = project
        self.phase = phase
        self.dir = Path(root) / project / ".logs"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / f"{phase}.jsonl"

    def _write(self, rec):
        rec = {"ts": _now(), "project": self.project, "phase": self.phase, **rec}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    # --- the four record types (SELF_HEALING.md §1) ---
    def ok(self, step, **extra):
        return self._write({"step": step, "status": "ok", **extra})

    def failed(self, step, error_class, message, stack=None, **extra):
        return self._write({"step": step, "status": "failed",
                            "error": {"class": error_class, "message": message, "stack": stack},
                            **extra})

    def recovered(self, step, error_class, attempted, attempts=1, human_message="", **extra):
        return self._write({"step": step, "status": "recovered",
                            "error": {"class": error_class},
                            "recovery": {"attempted": attempted, "attempts": attempts, "result": "success"},
                            "human_message": human_message, **extra})

    def escalated(self, step, error_class, message, human_message, **extra):
        return self._write({"step": step, "status": "escalated",
                            "error": {"class": error_class, "message": message},
                            "human_message": human_message, **extra})

    def run(self, step, fn, error_class="SC-1"):
        """Execute fn() with the {ok, err} envelope. Never swallows: on success
        returns {"ok": True, "v": <result>} and logs ok; on exception returns
        {"ok": False, "err": <msg>} and logs the failure with a full stack."""
        try:
            value = fn()
            self.ok(step)
            return {"ok": True, "v": value}
        except Exception as exc:
            self.failed(step, error_class, str(exc), traceback.format_exc())
            return {"ok": False, "err": str(exc)}


_SYM = {"ok": "✅", "failed": "❌", "recovered": "♻️ ", "escalated": "⛔"}


def render(path):
    """Print the human-readable mirror of a JSONL phase log."""
    p = Path(path)
    if not p.exists():
        print(f"no log at {path}")
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        t = r.get("ts", "")[11:19]
        sym = _SYM.get(r.get("status"), "· ")
        head = f"{t}  {r.get('project','')} · {r.get('phase','')} · {r.get('step','')}"
        print(f"{head}  {sym}{r.get('status','')}")
        msg = r.get("human_message")
        if msg:
            print(f"          → {msg}")
        err = r.get("error") or {}
        if r.get("status") == "failed" and err.get("message"):
            print(f"          → [{err.get('class','?')}] {err.get('message')}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "render":
        render(sys.argv[2])
    else:
        print(__doc__)
