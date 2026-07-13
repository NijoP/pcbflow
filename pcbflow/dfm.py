"""Data-driven DRC/DFM RuleSet — one rule model unifying KiCad's DRC engine and EasyEDA's
DFM checker (roadmap Phase 3, architecture/02 + /03).

Both mature tools converge on the same shape: a rule = a **constraint** (min/max limit) with a
**severity**, evaluated against board geometry; manufacturer capability is **data**, not code.
So a RuleSet is a table of numbers you select by (layers, copper), and the checker is a small
fixed set of constraint kinds — exactly KiCad's model, with EasyEDA's manufacturer-aware
threshold selection.

The JLCPCB profile numbers match this repo's own reference standards
(knowledge/design-standards.md §DFM): edge 0.25, track/space 0.15, hole-to-copper 0.20,
via drill ≥0.20 (prefer 0.30 sig / 0.40 pwr), via pad 0.50/0.60, annular ≥0.10.

Design input (tool-neutral; produced by a CAD backend's read_board):
    {"board": {"layers": 2|4, "copper_oz": "1oz", "size_mm": [w, h]},
     "tracks": [{"net","width","layer"}],
     "vias":   [{"net","drill","pad","x","y"[,"layer"]}],
     "silk":   [{"width","height"[,"ref"]}]}

Correctness details carried from real fabrication (F5/KG-L4, docs/13): pairwise checks skip
**same-net** features; via hole-to-hole uses **true edge distance**. Pure Python 3 stdlib.

NOTE: capability numbers are the well-known JLCPCB values; verify against the current JLCPCB
capability sheet / the official jlc-order-dfm-checker before a real order.
"""
import math
from dataclasses import dataclass


@dataclass
class Rule:
    name: str
    kind: str            # "min" | "max"
    limit: float         # mm
    severity: str = "error"   # "error" | "warning"
    note: str = ""

    def violated(self, value):
        return value < self.limit - 1e-6 if self.kind == "min" else value > self.limit + 1e-6


# ── Manufacturer capability profiles (DATA) ─────────────────────────
_JLCPCB = {
    "min_track_width":  (0.15, "error", "track/space capable to 0.09; 0.15 = safe floor"),
    "min_clearance":    (0.15, "error", "copper-to-copper, different nets"),
    "copper_to_edge":   (0.25, "error", "copper to board outline"),
    "hole_to_copper":   (0.20, "error", ""),
    "min_via_drill":    (0.20, "error", "prefer 0.30 signal / 0.40 power"),
    "min_via_pad":      (0.50, "error", "signal; 0.60 power"),
    "min_annular_ring": (0.10, "error", "(pad - drill) / 2"),
    "min_hole_to_hole": (0.50, "error", "hole edge to hole edge"),
    "min_silk_width":   (0.15, "warning", "silkscreen line/stroke"),
    "min_silk_height":  (1.00, "warning", "silkscreen character height"),
    "max_board_edge":   (500.0, "error", "single-panel max dimension"),
}


class RuleSet:
    """A named table of Rules + the board profile that selected them."""
    def __init__(self, name, rules, profile=None):
        self.name = name
        self.rules = {r.name: r for r in rules}
        self.profile = profile or {}

    def rule(self, name):
        return self.rules.get(name)

    def limit(self, name):
        r = self.rules.get(name)
        return r.limit if r else None

    @classmethod
    def jlcpcb(cls, layers=2, copper_oz="1oz"):
        rules = [Rule(k, "max" if k.startswith("max_") else "min", lim, sev, note)
                 for k, (lim, sev, note) in _JLCPCB.items()]
        return cls(f"JLCPCB-{layers}L-{copper_oz}", rules,
                   {"layers": layers, "copper_oz": copper_oz, "vendor": "JLCPCB"})


# ── The checker (fixed constraint kinds; limits come from the RuleSet) ──
def _v(rule, value, where, extra=""):
    return {"rule": rule.name, "severity": rule.severity, "value": round(value, 4),
            "limit": rule.limit, "where": where,
            "reason": f"{rule.name} {value:.4g} < {rule.limit} mm{(' — ' + rule.note) if rule.note else ''}"
                      if rule.kind == "min" else
                      f"{rule.name} {value:.4g} > {rule.limit} mm{(' — ' + extra) if extra else ''}"}


def _hole_edge_gap(a, b):
    """True edge-to-edge distance between two circular holes (drill diameters)."""
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"]) - (a["drill"] + b["drill"]) / 2.0


def run_dfm(design, ruleset):
    """Evaluate a design against a RuleSet. Returns a list of violation dicts, each with
    a coordinate/ref location and a human reason (the EasyEDA-DFM 'coord + reason' pattern)."""
    if ruleset is None:
        raise ValueError("run_dfm needs an explicit RuleSet — never DRC a board without its "
                         "ruleset (phantom-DRC guard, docs/13 F7).")
    V = []
    R = ruleset
    board = design.get("board", {})

    # board size
    r = R.rule("max_board_edge")
    for i, dim in enumerate(board.get("size_mm", []) or []):
        if r and r.violated(dim):
            V.append(_v(r, dim, f"board.size[{i}]", "exceeds panel max"))

    # tracks: min width
    rw = R.rule("min_track_width")
    for t in design.get("tracks", []):
        if rw and rw.violated(t.get("width", 0)):
            V.append(_v(rw, t["width"], f"track@{t.get('net','?')}/{t.get('layer','?')}"))

    # vias: drill, pad diameter, annular ring
    rd, rp, ra = R.rule("min_via_drill"), R.rule("min_via_pad"), R.rule("min_annular_ring")
    for vi in design.get("vias", []):
        loc = f"via@({vi.get('x','?')},{vi.get('y','?')}) net={vi.get('net','?')}"
        if rd and rd.violated(vi.get("drill", 0)):
            V.append(_v(rd, vi["drill"], loc))
        if rp and "pad" in vi and rp.violated(vi["pad"]):
            V.append(_v(rp, vi["pad"], loc))
        if ra and "pad" in vi and "drill" in vi:
            ann = (vi["pad"] - vi["drill"]) / 2.0
            if ra.violated(ann):
                V.append(_v(ra, ann, loc))

    # vias: hole-to-hole (pairwise, same-net skipped, true edge distance)
    rh = R.rule("min_hole_to_hole")
    vias = design.get("vias", [])
    if rh:
        for i in range(len(vias)):
            for j in range(i + 1, len(vias)):
                if vias[i].get("net") and vias[i].get("net") == vias[j].get("net"):
                    continue  # same-net: no spacing rule
                gap = _hole_edge_gap(vias[i], vias[j])
                if rh.violated(gap):
                    V.append(_v(rh, gap, f"holes {i}<->{j}"))

    # silk
    rsw, rsh = R.rule("min_silk_width"), R.rule("min_silk_height")
    for s in design.get("silk", []):
        where = f"silk@{s.get('ref','?')}"
        if rsw and "width" in s and rsw.violated(s["width"]):
            V.append(_v(rsw, s["width"], where))
        if rsh and "height" in s and rsh.violated(s["height"]):
            V.append(_v(rsh, s["height"], where))
    return V


def report(violations):
    """Summarize violations by severity + rule (mirrors the DFM extension's results table)."""
    by_sev = {"error": 0, "warning": 0}
    by_rule = {}
    for v in violations:
        by_sev[v["severity"]] = by_sev.get(v["severity"], 0) + 1
        by_rule[v["rule"]] = by_rule.get(v["rule"], 0) + 1
    return {"total": len(violations), "errors": by_sev["error"], "warnings": by_sev["warning"],
            "by_rule": by_rule, "pass": by_sev["error"] == 0}
