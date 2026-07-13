"""Machine-computed phase gates — turn the 12 checkpoints from asserted verdicts into gates
that actually RUN the checks, and hard-block manufacturing export until they pass AND a human
has recorded approval.

A gate does not *store* a judgement; it *computes* one by running the phase's real checks
(ERC on the netlist, DFM/DRC on the board, spacing on the placement) and folding the harmonized
findings (pcbflow.findings) into a single GateOutcome. Outcomes compose with an explicit status
hierarchy so a project only PASSES when every gate passes.

Status hierarchy (which status wins when combining), most-dominant first:
    BLOCKED  — a tool/environment problem: the check could not run
    EMPTY    — the artifact to check is missing (nothing to judge)
    FAIL     — a real design violation (error-severity finding)
    WARN     — advisory only (warnings, no errors)
    PASS     — clean

Safety: export NEVER signs off a DRC and NEVER orders a board. It refuses unless (a) every gate
is PASS and (b) a human approval-evidence file exists — approval is *recorded*, not automated.
Pure Python 3 standard library.
"""
from dataclasses import dataclass, field
from pathlib import Path

from . import dfm, erc, findings
from .enet import Enet

# most-dominant first — the combined status is the first present in this order
_PRECEDENCE = ("BLOCKED", "EMPTY", "FAIL", "WARN", "PASS")


@dataclass
class GateOutcome:
    name: str
    status: str                       # one of _PRECEDENCE
    summary: str
    details: list = field(default_factory=list)

    @property
    def passed(self):
        return self.status == "PASS"


def combine(outcomes):
    """Fold gate outcomes into one status (worst-dominant). No outcomes → EMPTY."""
    present = {o.status for o in outcomes}
    for s in _PRECEDENCE:
        if s in present:
            return s
    return "EMPTY"


def _from_findings(name, fs):
    """error → FAIL, warning-only → WARN, clean → PASS. The gate judgement is *computed* here."""
    rep = findings.report(fs)
    status = "FAIL" if rep["errors"] else ("WARN" if rep["warnings"] else "PASS")
    details = [f"[{f['severity']}] {f['rule_id']} {f['where']}: {f['summary']}"
               for f in findings.sort_findings(fs)]
    return GateOutcome(name, status, f"{rep['errors']} error(s), {rep['warnings']} warning(s)",
                       details)


# ── per-phase gates (each RUNS the check) ───────────────────────────
def gate_schematic(enet_path):
    """Phase 5: structural verify + ERC on the .enet netlist."""
    net = Enet.load(enet_path)
    struct = net.verify()
    fs = erc.run_erc(net)
    outcome = _from_findings("schematic", fs)
    if struct:                                    # structural problems are hard errors
        outcome.status = "FAIL" if outcome.status != "BLOCKED" else outcome.status
        outcome.details = [f"structure: {s}" for s in struct] + outcome.details
        outcome.summary = f"{len(struct)} structure issue(s); " + outcome.summary
    return outcome


def gate_placement(placement_json):
    """Phases 6/9: real-geometry pad-spacing audit."""
    import json
    doc = json.loads(Path(placement_json).read_text())
    fs = findings.spacing_findings(doc.get("parts", []), min_gap=doc.get("min_gap", 0.5),
                                   whitelist=doc.get("whitelist", []))
    return _from_findings("placement", fs)


def gate_dfm(board_features_json):
    """Phase 11/12 (offline): DFM against the JLCPCB profile from a board-features JSON."""
    import json
    design = json.loads(Path(board_features_json).read_text())
    b = design.get("board", {})
    rs = dfm.RuleSet.jlcpcb(layers=b.get("layers", 2), copper_oz=b.get("copper_oz", "1oz"))
    return _from_findings("dfm", dfm.run_dfm(design, rs))


def gate_drc(board_path, drc_runner):
    """Phase 12: DRC in KiCad (the ground truth). `drc_runner(board)->dict` is injected so this
    stays testable and gates.py never shells out itself. Missing runner/tool → BLOCKED, not a
    silent pass."""
    if drc_runner is None:
        return GateOutcome("drc", "BLOCKED", "no DRC runner available (kicad-cli)", [])
    res = drc_runner(str(board_path))
    if res.get("ok"):
        return GateOutcome("drc", "PASS", f"DRC clean → {res.get('report','')}", [])
    if res.get("violations"):
        return GateOutcome("drc", "FAIL", f"DRC violations → {res.get('report','')}", [])
    return GateOutcome("drc", "BLOCKED", res.get("reason", "DRC could not run"), [])


# ── project-level gate + the export hard-block ──────────────────────
def _find(project_dir, pattern):
    hits = sorted(Path(project_dir).rglob(pattern))
    return hits[0] if hits else None


def project_gate(project_dir, drc_runner=None):
    """Run every gate whose artifact is present in the project. Returns a list of GateOutcome.
    A missing netlist is EMPTY (not silently skipped) — export must not clear an unverifiable board."""
    outcomes = []
    enet = _find(project_dir, "*.enet")
    outcomes.append(gate_schematic(enet) if enet
                    else GateOutcome("schematic", "EMPTY", "no .enet netlist found", []))
    place = _find(project_dir, "placement*.json")
    if place:
        outcomes.append(gate_placement(place))
    bf = _find(project_dir, "board_features*.json")
    if bf:
        outcomes.append(gate_dfm(bf))
    board = _find(project_dir, "*.kicad_pcb")
    if board:
        outcomes.append(gate_drc(board, drc_runner))
    return outcomes


def compute_phase_gate(project_dir, phase, drc_runner=None):
    """Compute the gate for a single phase by running its check against the project's artifacts.
    Phases with no automatable check (or a missing artifact) return EMPTY — the human records
    those verdicts explicitly (never a silent auto-pass)."""
    if phase == 5:
        enet = _find(project_dir, "*.enet")
        return gate_schematic(enet) if enet else \
            GateOutcome("schematic", "EMPTY", "no .enet netlist found", [])
    if phase in (6, 7, 8, 9):
        place = _find(project_dir, "placement*.json")
        return gate_placement(place) if place else \
            GateOutcome("placement", "EMPTY", "no placement*.json found", [])
    if phase in (11, 12):
        board = _find(project_dir, "*.kicad_pcb")
        if board:
            return gate_drc(board, drc_runner)
        bf = _find(project_dir, "board_features*.json")
        if bf:
            return gate_dfm(bf)
        return GateOutcome("manufacturability", "EMPTY", "no board (.kicad_pcb / board_features*.json)", [])
    return GateOutcome(f"phase{phase}", "EMPTY", "no computed gate for this phase — record manually", [])


# gate status → the project verdict vocabulary (project.py: PASS/CONDITIONAL/FAIL/PENDING)
_VERDICT = {"PASS": "PASS", "WARN": "CONDITIONAL", "FAIL": "FAIL", "EMPTY": "PENDING",
            "BLOCKED": "PENDING"}


def status_to_verdict(status):
    return _VERDICT.get(status, "PENDING")


def approval_error(approval_path):
    """Validate the human approval-evidence file. Returns an error string, or None if valid.
    Required fields: approved_by, approved_at_utc, scope — all non-empty."""
    import json
    if not approval_path:
        return ("no approval evidence — manufacturing export is blocked until a human records "
                "approval (a JSON file with approved_by, approved_at_utc, scope)")
    p = Path(approval_path)
    if not p.exists():
        return f"approval file not found: {p}"
    try:
        doc = json.loads(p.read_text())
    except ValueError as e:
        return f"approval file is not valid JSON: {e}"
    missing = [k for k in ("approved_by", "approved_at_utc", "scope") if not doc.get(k)]
    return f"approval evidence missing fields: {', '.join(missing)}" if missing else None


def export_check(project_dir, approval_path, drc_runner=None):
    """The manufacturing-export gate. Returns (cleared: bool, outcomes, reasons).

    HARD-BLOCKS unless (a) every project gate is PASS and (b) valid human approval exists. It
    never signs a DRC and never orders a board — it only clears the human to produce the files.
    """
    outcomes = project_gate(project_dir, drc_runner=drc_runner)
    blocking = [o for o in outcomes if o.status != "PASS"]
    reasons = [f"gate '{o.name}' is {o.status}: {o.summary}" for o in blocking]
    ap_err = approval_error(approval_path)
    if ap_err:
        reasons.append(ap_err)
    return (not reasons), outcomes, reasons
