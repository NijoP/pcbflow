"""PCB Flow CLI — one entry point for the whole harness.

In-package commands (pure, fast): init, status, verdict, advance, phases, ipc.
Pass-through commands (delegate to the tools, so there's one front door):
doctor, launch, dump, recon, drc.

Run from the cloned repo (the pass-throughs resolve tool paths relative to it).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import (__version__, congestion, dfm, enet as enet_mod, erc, findings, gates, geometry,
               hw, import_diff, ipc, phases, routing)
from .project import Project

REPO = Path(__file__).resolve().parent.parent
PROJECTS = REPO / "projects"


def _run(rel, *args):
    """Run a repo tool with the current interpreter (handles python vs python3)."""
    return subprocess.run([sys.executable, str(REPO / rel), *args]).returncode


# --- pass-throughs ---
def cmd_doctor(a):
    return _run("tools/doctor.py", *a.passthrough)


def cmd_launch(a):
    return _run("tools/launch_easyeda.py", *a.passthrough)


def cmd_drc(a):
    return _run("tools/drc.py", *([a.board] + ([a.ruleset] if a.ruleset else [])))


def cmd_recon(a):
    return _run("automation/browser/recon.py", *([a.dump] + ([a.out] if a.out else [])))


def cmd_dump(a):
    r = subprocess.run(
        [sys.executable, str(REPO / "automation/browser/cdp.py"), "eval",
         str(REPO / "automation/easyeda/dump_schematic.js")],
        capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[:800] + "\n")
        return r.returncode
    Path(a.out).write_text(r.stdout)
    print(f"dumped live schematic -> {a.out}  (now: pcbflow recon {a.out} netlist.json)")
    return 0


# --- in-package ---
def cmd_init(a):
    p = Project.init(PROJECTS, a.name, a.description or "")
    print(f"initialized project '{a.name}' at {p.path.relative_to(REPO)}  (phase 1: "
          f"{phases.phase_name(1)})")
    return 0


def cmd_status(a):
    p = Project(PROJECTS / a.name)
    try:
        s = p.status()
    except FileNotFoundError as e:
        print(e)
        return 2
    lv = s["latest_verdict"]
    print(f"Project: {s['name']}")
    print(f"  Phase {s['current_phase']:>2}: {s['phase_name']}  (agent: {s['owning_agent']})")
    print(f"  Latest verdict: {lv['verdict'] if lv else 'PENDING'}")
    print(f"  Advance allowed: {'yes' if p.can_advance() else 'no — needs a PASS verdict'}")
    return 0


def cmd_verdict(a):
    p = Project(PROJECTS / a.name)
    p.record_verdict(a.phase, a.verdict, a.note or "")
    print(f"recorded {a.verdict.upper()} for '{a.name}' phase {a.phase} ({phases.phase_name(a.phase)})")
    return 0


def cmd_advance(a):
    p = Project(PROJECTS / a.name)
    try:
        nxt = p.advance()
    except RuntimeError as e:
        print(e)
        return 1
    print(f"advanced '{a.name}' -> phase {nxt} ({phases.phase_name(nxt)})")
    return 0


def cmd_phases(a):
    for n, name, agent in phases.PHASES:
        print(f"{n:>2}  {name:<28} {agent}")
    return 0


def cmd_ipc(a):
    r = ipc.recommend(a.current, delta_t_c=a.delta_t, copper_oz=a.oz, internal=a.internal)
    print(f"{a.current} A  ->  {r['width_mm']} mm  [{r['method']}]   ({r['margin_note']})")
    if r["method"] == "plane/pour":
        print(f"    plane + via farm: ~{ipc.via_count(a.current, 0.3)} x 0.3 mm vias")
    return 0


def cmd_widths(a):
    nets = json.loads(Path(a.nets).read_text())
    table = routing.trace_width_table(nets, delta_t_c=a.delta_t)
    for row in table:
        print(f"{row['net']:<16} {row['i_peak_a']:>6} A  {row['width_mm']:>7} mm  [{row['method']}]")
    if a.out:
        Path(a.out).write_text(json.dumps(table, indent=2))
        print(f"-> {a.out}")
    return 0


def cmd_stitch_pitch(a):
    print(f"edge knee: {routing.edge_knee_mhz(a.t_rise)} MHz  ->  "
          f"λ/20 stitch pitch: {routing.stitch_pitch_mm(a.t_rise, a.er)} mm")
    return 0


def cmd_spacing(a):
    doc = json.loads(Path(a.placement).read_text())
    v = geometry.spacing_audit(doc["parts"], min_gap=doc.get("min_gap", 0.5),
                               whitelist=doc.get("whitelist", []))
    if not v:
        print("spacing: 0 violations (real geometry).")
        return 0
    print(f"spacing: {len(v)} violation(s):")
    for x in v:
        print(f"  {x['a']} <-> {x['b']}: gap {x['gap']} mm < {x['limit']} mm")
    return 1


def cmd_congestion(a):
    doc = json.loads(Path(a.input).read_text())
    g = congestion.grid(doc["nets"], doc["w"], doc["h"], bin_mm=doc.get("bin_mm", 2.0))
    hot = congestion.saturated(g)
    print(f"congestion: {g['nx']}x{g['ny']} bins @ {g['bin_mm']}mm; "
          f"{len(hot)} saturated bin(s) need a via-fan to the other layer")
    for h in hot[:20]:
        print(f"  bin {h['bin']}: demand {h['demand']} > cap {h['cap']}")
    return 0


def _print_violations(items):
    for v in findings.sort_findings(items):
        print(f"  [{v['severity']:<7}] {v['rule_id']:<20} {v.get('where','')}: {v['summary']}")


def _print_trust(items):
    if items:
        t = findings.trust_summary(items)
        print(f"  trust: {t['level']} — {t['by_confidence']}")


def cmd_enet(a):
    net = enet_mod.Enet.load(a.file)
    issues = net.verify()
    print(json.dumps({"stats": net.stats(), "verify_issues": issues}, indent=2))
    return 0 if not issues else 1


def cmd_erc(a):
    net = enet_mod.Enet.load(a.file)
    v = erc.run_erc(net)
    if getattr(a, "json", False):
        print(findings.to_json(v))
        return 0 if findings.report(v)["pass"] else 1
    rep = findings.report(v)
    print(f"ERC {net.stats()['components']} comps: {rep['errors']} error(s), {rep['warnings']} warning(s)"
          f"  -> {'PASS' if rep['pass'] else 'FAIL'}")
    _print_violations(v)
    _print_trust(v)
    return 0 if rep["pass"] else 1


def cmd_dfm(a):
    design = json.loads(Path(a.design).read_text())
    board = design.get("board", {})
    rs = dfm.RuleSet.jlcpcb(layers=a.layers or board.get("layers", 2),
                            copper_oz=a.copper or board.get("copper_oz", "1oz"))
    v = dfm.run_dfm(design, rs)
    if getattr(a, "json", False):
        print(findings.to_json(v))
        return 0 if findings.report(v)["pass"] else 1
    rep = findings.report(v)
    print(f"DFM [{rs.name}]: {rep['errors']} error(s), {rep['warnings']} warning(s)"
          f"  -> {'PASS' if rep['pass'] else 'FAIL'}")
    _print_violations(v)
    _print_trust(v)
    return 0 if rep["pass"] else 1


def cmd_verify(a):
    """Offline phase-5 audit: structural netlist verify + ERC (+ DFM if a board is given)."""
    net = enet_mod.Enet.load(a.file)
    struct = net.verify()
    ev = erc.run_erc(net)
    dv = []
    if a.board:
        design = json.loads(Path(a.board).read_text())
        b = design.get("board", {})
        rs = dfm.RuleSet.jlcpcb(layers=b.get("layers", 2), copper_oz=b.get("copper_oz", "1oz"))
        dv = dfm.run_dfm(design, rs)
    all_findings = ev + dv
    ok = not struct and findings.report(all_findings)["pass"]

    if getattr(a, "json", False):
        payload = {"file": a.file, "structure_issues": struct,
                   "findings": findings.sort_findings(all_findings),
                   "report": findings.report(all_findings),
                   "trust": findings.trust_summary(all_findings),
                   "verdict": "PASS" if ok else "FAIL"}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if ok else 1

    erep = findings.report(ev)
    print(f"== verify {a.file} ==")
    print(f"  netlist structure : {'clean' if not struct else str(len(struct)) + ' issue(s)'}")
    for s in struct:
        print(f"    - {s}")
    print(f"  ERC               : {erep['errors']} error(s), {erep['warnings']} warning(s)")
    _print_violations(ev)
    if a.board:
        drep = findings.report(dv)
        print(f"  DFM               : {drep['errors']} error(s), {drep['warnings']} warning(s)")
        _print_violations(dv)
    print(f"  VERDICT           : {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def _cli_drc_runner(board):
    """DRC runner for the gates layer: shells to tools/drc.py (the phantom-guarded kicad-cli
    runner) and maps its exit code to the {ok, violations, reason} contract gates.gate_drc reads."""
    p = subprocess.run([sys.executable, str(REPO / "tools/drc.py"), board],
                       capture_output=True, text=True)
    rpt = board + ".drc.rpt"
    if p.returncode == 0:
        return {"ok": True, "report": rpt}
    if p.returncode == 1:
        return {"ok": False, "violations": True, "report": rpt}
    return {"ok": False, "reason": (p.stderr or p.stdout or "DRC could not run").strip()}


def cmd_gate(a):
    """Compute a phase gate by RUNNING its checks, and record the resulting verdict."""
    proj_dir = PROJECTS / a.name
    out = gates.compute_phase_gate(proj_dir, a.phase, drc_runner=_cli_drc_runner)
    print(f"gate phase {a.phase} ({phases.phase_name(a.phase)}): {out.status} — {out.summary}")
    for d in out.details[:20]:
        print(f"    {d}")
    if not a.no_record:
        proj = Project(proj_dir)
        if not proj.state_file.exists():          # allow gating a project dir not yet `init`ed
            proj = Project.init(PROJECTS, a.name)
        verdict = gates.status_to_verdict(out.status)
        proj.record_verdict(a.phase, verdict, note=f"computed gate {out.status}: {out.summary}")
        print(f"  recorded verdict: {verdict}"
              + ("  (advance allowed)" if verdict == "PASS" else "  (advance still blocked)"))
    return 0 if out.status == "PASS" else 1


def cmd_export(a):
    """Manufacturing export — HARD-BLOCKED until every gate PASSES and a human approval file exists.
    Never signs off a DRC; never orders a board."""
    proj_dir = PROJECTS / a.name
    cleared, outcomes, reasons = gates.export_check(proj_dir, a.approval, drc_runner=_cli_drc_runner)
    print(f"export {a.name}:")
    for o in outcomes:
        print(f"  gate {o.name:<15} {o.status:<8} {o.summary}")
    if not cleared:
        print("  BLOCKED — manufacturing export refused:")
        for r in reasons:
            print(f"    - {r}")
        print("  (no DRC is auto-signed, no board is ordered — resolve the above, then re-run)")
        return 1
    print("  CLEARED — every gate PASSES and human approval is on file.")
    print("  → produce the manufacturing files; YOU place the order (PCB Flow never orders).")
    return 0


def cmd_hw(a):
    """Hardware-correctness checks (Tier 1): pin-type ERC, power tree, component ratings.
    Needs a parts.json beside the netlist (electrical types + ratings)."""
    fs = hw.run(a.netlist)
    if getattr(a, "json", False):
        print(findings.to_json(fs))
        return 0 if findings.report(fs)["pass"] else 1
    rep = findings.report(fs)
    print(f"hw checks: {rep['errors']} error(s), {rep['warnings']} warning(s)"
          f"  -> {'PASS' if rep['pass'] else 'FAIL'}")
    _print_violations(fs)
    _print_trust(fs)
    from .parts import Parts
    if not Parts.beside(a.netlist).designators():
        print("  (no parts.json beside the netlist — add one with pin types + ratings to enable "
              "the electrical checks)")
    return 0 if rep["pass"] else 1


def cmd_import_check(a):
    """Phase-10 gate: does the KiCad board match the .enet netlist? (fails loudly on drift)."""
    fs, rep = import_diff.check(a.netlist, a.board)
    if getattr(a, "json", False):
        print(findings.to_json(fs))
        return 0 if rep["pass"] else 1
    verdict = "MATCH" if rep["pass"] else "MISMATCH"
    print(f"import-check {a.netlist} vs {a.board}: "
          f"{rep['errors']} error(s), {rep['warnings']} warning(s)  -> {verdict}")
    _print_violations(fs)
    return 0 if rep["pass"] else 1


def build_parser():
    ap = argparse.ArgumentParser(prog="pcbflow", description="AI-assisted PCB design harness")
    ap.add_argument("--version", action="version", version=f"pcbflow {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="check the environment before working")
    d.add_argument("passthrough", nargs="*"); d.set_defaults(fn=cmd_doctor)

    i = sub.add_parser("init", help="create a new project")
    i.add_argument("name"); i.add_argument("--description", default=""); i.set_defaults(fn=cmd_init)

    s = sub.add_parser("status", help="show a project's current phase + verdict")
    s.add_argument("name"); s.set_defaults(fn=cmd_status)

    v = sub.add_parser("verdict", help="record a phase verdict (PASS/CONDITIONAL/FAIL)")
    v.add_argument("name"); v.add_argument("phase", type=int); v.add_argument("verdict")
    v.add_argument("--note", default=""); v.set_defaults(fn=cmd_verdict)

    adv = sub.add_parser("advance", help="advance to the next phase (requires a PASS)")
    adv.add_argument("name"); adv.set_defaults(fn=cmd_advance)

    sub.add_parser("phases", help="list the 12 phases").set_defaults(fn=cmd_phases)

    ic = sub.add_parser("ipc", help="IPC-2221 trace width / plane call for a current")
    ic.add_argument("current", type=float)
    ic.add_argument("--delta-t", dest="delta_t", type=float, default=10.0)
    ic.add_argument("--oz", type=float, default=1.0)
    ic.add_argument("--internal", action="store_true")
    ic.set_defaults(fn=cmd_ipc)

    ln = sub.add_parser("launch", help="launch EasyEDA in Chrome (cross-platform)")
    ln.add_argument("passthrough", nargs="*"); ln.set_defaults(fn=cmd_launch)

    dm = sub.add_parser("dump", help="dump the live EasyEDA schematic to JSON")
    dm.add_argument("out"); dm.set_defaults(fn=cmd_dump)

    rc = sub.add_parser("recon", help="reconstruct a netlist from a schematic dump")
    rc.add_argument("dump"); rc.add_argument("out", nargs="?"); rc.set_defaults(fn=cmd_recon)

    dr = sub.add_parser("drc", help="run KiCad DRC (guarded against phantom-clean)")
    dr.add_argument("board"); dr.add_argument("ruleset", nargs="?"); dr.set_defaults(fn=cmd_drc)

    wd = sub.add_parser("widths", help="IPC-2221 trace-width table from a nets JSON")
    wd.add_argument("nets"); wd.add_argument("out", nargs="?")
    wd.add_argument("--delta-t", dest="delta_t", type=float, default=10.0)
    wd.set_defaults(fn=cmd_widths)

    sp = sub.add_parser("stitch-pitch", help="λ/20 ground-stitch pitch from an edge rise time (ns)")
    sp.add_argument("t_rise", type=float); sp.add_argument("--er", type=float, default=4.3)
    sp.set_defaults(fn=cmd_stitch_pitch)

    sc = sub.add_parser("spacing", help="placement spacing audit from a placement JSON")
    sc.add_argument("placement"); sc.set_defaults(fn=cmd_spacing)

    cg = sub.add_parser("congestion", help="routing congestion prediction from a nets JSON")
    cg.add_argument("input"); cg.set_defaults(fn=cmd_congestion)

    en = sub.add_parser("enet", help="parse + structurally verify an .enet netlist")
    en.add_argument("file"); en.set_defaults(fn=cmd_enet)

    er = sub.add_parser("erc", help="electrical rule check on an .enet netlist")
    er.add_argument("file")
    er.add_argument("--json", action="store_true", help="emit harmonized findings as JSON")
    er.set_defaults(fn=cmd_erc)

    df = sub.add_parser("dfm", help="DRC/DFM check on a board-features JSON (JLCPCB profile)")
    df.add_argument("design")
    df.add_argument("--layers", type=int, default=None)
    df.add_argument("--copper", default=None)
    df.add_argument("--json", action="store_true", help="emit harmonized findings as JSON")
    df.set_defaults(fn=cmd_dfm)

    vf = sub.add_parser("verify", help="offline phase-5 audit: netlist verify + ERC (+ DFM)")
    vf.add_argument("file", help="the .enet netlist")
    vf.add_argument("--board", default=None, help="optional board-features JSON for DFM")
    vf.add_argument("--json", action="store_true", help="emit the full audit as JSON")
    vf.set_defaults(fn=cmd_verify)

    hwp = sub.add_parser("hw", help="hardware checks: pin-type ERC, power tree, component ratings")
    hwp.add_argument("netlist", help="the .enet netlist (with a parts.json beside it)")
    hwp.add_argument("--json", action="store_true", help="emit harmonized findings as JSON")
    hwp.set_defaults(fn=cmd_hw)

    ck = sub.add_parser("import-check",
                        help="verify a KiCad board matches its .enet netlist (fails loudly)")
    ck.add_argument("netlist", help="the .enet netlist")
    ck.add_argument("board", help="the .kicad_pcb")
    ck.add_argument("--json", action="store_true", help="emit harmonized findings as JSON")
    ck.set_defaults(fn=cmd_import_check)

    gt = sub.add_parser("gate", help="compute a phase gate by RUNNING its checks + record the verdict")
    gt.add_argument("name")
    gt.add_argument("phase", type=int)
    gt.add_argument("--no-record", action="store_true", help="compute only; don't record a verdict")
    gt.set_defaults(fn=cmd_gate)

    ex = sub.add_parser("export",
                        help="manufacturing export — HARD-BLOCKED until gates pass + human approval")
    ex.add_argument("name")
    ex.add_argument("--approval", default=None,
                    help="approval-evidence JSON (approved_by / approved_at_utc / scope)")
    ex.set_defaults(fn=cmd_export)

    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
