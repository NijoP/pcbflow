#!/usr/bin/env python3
"""
pcbflow drc — cross-platform DRC runner for KiCad (roadmap Phase 4).

Ports automation/kicad/drc.sh to Python so it works on Windows/macOS/Linux, and
keeps the KI-6 guard: it REFUSES to run on a bare board with no ruleset sibling
(a bare board reports default rules as clean = phantom DRC). Pure Python 3 stdlib.

Usage:
    python3 tools/drc.py <board.kicad_pcb> <ruleset.kicad_pro>
    python3 tools/drc.py <board.kicad_pcb>          # only if a sibling .kicad_pro exists
"""
import argparse, shutil, subprocess, sys
from pathlib import Path


def run_drc(board, ruleset=None, run=subprocess.run, which=shutil.which, timeout=300):
    board = Path(board)
    if not board.exists():
        return {"ok": False, "reason": f"board not found: {board}"}
    if not which("kicad-cli"):
        return {"ok": False, "reason": "kicad-cli not found — install KiCad (KI-5)"}
    pro = board.with_suffix(".kicad_pro")
    if ruleset:
        r = Path(ruleset)
        if not r.exists():
            return {"ok": False, "reason": f"ruleset not found: {r}"}
        shutil.copyfile(r, pro)              # put the ruleset beside the board (the point)
    if not pro.exists():
        return {"ok": False, "reason": ("no ruleset (.kicad_pro) beside the board — refusing "
                                        "to run: a bare board reports DEFAULT rules as clean "
                                        "(phantom DRC, KI-6). Pass a ruleset.")}
    report = str(board.with_suffix(".drc.rpt"))
    cmd = ["kicad-cli", "pcb", "drc", "--severity-error", "--exit-code-violations",
           "--schematic-parity", "--output", report, str(board)]
    manual = " ".join(cmd)
    try:
        p = run(cmd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "violations": None, "report": report,
                "reason": f"kicad-cli DRC timed out after {timeout}s — run it manually: {manual}"}
    rc = getattr(p, "returncode", 0)
    return {"ok": rc == 0, "violations": rc != 0, "report": report, "manual": manual}


def main():
    ap = argparse.ArgumentParser(description="KiCad DRC with the phantom-DRC guard")
    ap.add_argument("board")
    ap.add_argument("ruleset", nargs="?")
    a = ap.parse_args()
    res = run_drc(a.board, a.ruleset)
    if not res["ok"] and "reason" in res:
        print("drc: " + res["reason"], file=sys.stderr)
        sys.exit(3)
    print(f"drc: report → {res['report']}  ({'VIOLATIONS' if res.get('violations') else 'clean'})")
    sys.exit(1 if res.get("violations") else 0)


if __name__ == "__main__":
    main()
