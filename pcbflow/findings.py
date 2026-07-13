"""Harmonized finding schema — one traceable shape for every check in the harness.

Every analyzer (ERC, DFM, placement spacing, import-diff, …) emits the *same* record so a
report is diffable, a claim carries its own evidence, and a consumer can weigh trust. The
schema is deliberately small and JSON-native (a plain dict), matching the rest of pcbflow.

A finding carries:
  id             stable sha256 locator (same inputs → same id across runs; enables diffs)
  detector       which analyzer produced it        (e.g. "erc", "dfm", "geometry.spacing")
  rule_id        stable rule code                   (e.g. "floating_pin", "min_track_width")
  category       "connectivity" | "manufacturability" | "placement" | …
  severity       "error" | "warning" | "info"
  confidence     "deterministic" | "heuristic" | "datasheet-backed"   (how sure are we)
  evidence_source "topology" | "geometry" | "ruleset" | "bom" | "heuristic_rule" | …
  summary        one-line human-readable statement
  where          location string (REF.pin, net, coord, "<board>")
  components     sorted list of refs
  nets           sorted list of net names
  recommendation actionable fix (may be "")
  provenance     dict of the raw numbers behind the call (value, limit, …)

The confidence/evidence-source taxonomies and a stable, hash-derived finding id are
well-established patterns for traceable EDA review output. Pure Python 3 standard library.
"""
import hashlib
import json

SEVERITIES = ("error", "warning", "info")
CONFIDENCES = ("deterministic", "heuristic", "datasheet-backed")
EVIDENCE_SOURCES = ("topology", "geometry", "ruleset", "bom", "heuristic_rule",
                    "datasheet", "symbol_footprint", "api_lookup")

_SEV_RANK = {"error": 0, "warning": 1, "info": 2}
# the canonical field order (also the schema the CLI --json output must satisfy)
FIELDS = ("id", "detector", "rule_id", "category", "severity", "confidence",
          "evidence_source", "summary", "where", "components", "nets",
          "recommendation", "provenance")


def _stable_id(detector, rule_id, components, nets, where):
    """A deterministic 12-hex id from the finding's locator — no time, no randomness, so the
    same problem gets the same id on every run (git-diffable reports)."""
    locator = "|".join([detector, rule_id, ",".join(components), ",".join(nets), where])
    return hashlib.sha256(locator.encode("utf-8")).hexdigest()[:12]


def finding(*, detector, rule_id, category, severity, confidence, evidence_source,
            summary, where="", components=None, nets=None, recommendation="", provenance=None):
    """Build one harmonized finding (a fresh dict — never mutates its inputs).

    Fails fast on an out-of-taxonomy severity/confidence/evidence_source (boundary validation).
    """
    if severity not in SEVERITIES:
        raise ValueError(f"severity {severity!r} not in {SEVERITIES}")
    if confidence not in CONFIDENCES:
        raise ValueError(f"confidence {confidence!r} not in {CONFIDENCES}")
    if evidence_source not in EVIDENCE_SOURCES:
        raise ValueError(f"evidence_source {evidence_source!r} not in {EVIDENCE_SOURCES}")
    comps = sorted(components or [])
    ns = sorted(nets or [])
    return {
        "id": _stable_id(detector, rule_id, comps, ns, where),
        "detector": detector,
        "rule_id": rule_id,
        "category": category,
        "severity": severity,
        "confidence": confidence,
        "evidence_source": evidence_source,
        "summary": summary,
        "where": where,
        "components": comps,
        "nets": ns,
        "recommendation": recommendation,
        "provenance": dict(provenance or {}),
    }


def validate(f):
    """Return a list of schema problems for one finding ([] = valid). Used to prove --json
    output conforms to the schema."""
    problems = []
    for k in FIELDS:
        if k not in f:
            problems.append(f"missing field: {k}")
    if f.get("severity") not in SEVERITIES:
        problems.append(f"bad severity: {f.get('severity')!r}")
    if f.get("confidence") not in CONFIDENCES:
        problems.append(f"bad confidence: {f.get('confidence')!r}")
    if f.get("evidence_source") not in EVIDENCE_SOURCES:
        problems.append(f"bad evidence_source: {f.get('evidence_source')!r}")
    return problems


def sort_findings(fs):
    """Deterministic order: errors first, then by rule/location/id — byte-stable across runs."""
    return sorted(fs, key=lambda f: (_SEV_RANK.get(f["severity"], 9),
                                     f["rule_id"], f["where"], f["id"]))


def report(fs):
    """Pass/fail rollup (a design PASSES iff it has no error-severity findings)."""
    errors = sum(1 for f in fs if f["severity"] == "error")
    warnings = sum(1 for f in fs if f["severity"] == "warning")
    infos = sum(1 for f in fs if f["severity"] == "info")
    by_rule = {}
    for f in fs:
        by_rule[f["rule_id"]] = by_rule.get(f["rule_id"], 0) + 1
    return {"total": len(fs), "errors": errors, "warnings": warnings, "infos": infos,
            "by_rule": by_rule, "pass": errors == 0}


def trust_summary(fs):
    """How much to trust this result: the confidence + evidence mix, and a level derived from
    the heuristic fraction (all-deterministic → high; mostly-heuristic → low; else mixed)."""
    by_conf = {c: 0 for c in CONFIDENCES}
    by_ev = {}
    for f in fs:
        by_conf[f["confidence"]] = by_conf.get(f["confidence"], 0) + 1
        by_ev[f["evidence_source"]] = by_ev.get(f["evidence_source"], 0) + 1
    n = len(fs)
    heuristic_pct = (by_conf["heuristic"] / n) if n else 0.0
    level = "high" if heuristic_pct == 0 else ("low" if heuristic_pct > 0.5 else "mixed")
    return {"total": n, "by_confidence": by_conf, "by_evidence_source": by_ev,
            "heuristic_pct": round(heuristic_pct, 3), "level": level}


def to_json(fs):
    """Deterministic JSON: sorted findings + rollup + trust. Same findings → identical bytes."""
    ordered = sort_findings(fs)
    return json.dumps({"findings": ordered, "report": report(ordered),
                       "trust": trust_summary(ordered)}, indent=2, sort_keys=True)


def to_markdown(fs, title="Findings"):
    """A human report table, findings grouped by severity (errors first)."""
    ordered = sort_findings(fs)
    rep, trust = report(ordered), trust_summary(ordered)
    lines = [f"# {title}", "",
             f"**{rep['errors']} error · {rep['warnings']} warning · {rep['infos']} info** — "
             f"verdict **{'PASS' if rep['pass'] else 'FAIL'}** · trust **{trust['level']}**", ""]
    if not ordered:
        lines.append("_No findings._")
        return "\n".join(lines)
    lines += ["| sev | rule | where | finding | confidence |",
              "|---|---|---|---|---|"]
    for f in ordered:
        lines.append(f"| {f['severity']} | `{f['rule_id']}` | {f['where']} | "
                     f"{f['summary']} | {f['confidence']} |")
    return "\n".join(lines)


def spacing_findings(parts, min_gap=0.5, whitelist=()):
    """Adapter: run the placement pad-spacing audit (pcbflow.geometry) and emit harmonized
    findings. Keeps geometry a dependency-free leaf while giving placement a schema-native check."""
    from . import geometry
    out = []
    for v in geometry.spacing_audit(parts, min_gap=min_gap, whitelist=whitelist):
        out.append(finding(
            detector="geometry.spacing", rule_id="spacing", category="placement",
            severity="error", confidence="deterministic", evidence_source="geometry",
            summary=f"same-layer gap {v['gap']} mm < {v['limit']} mm between {v['a']} and {v['b']}",
            where=f"{v['a']}<->{v['b']}", components=[v["a"], v["b"]],
            recommendation="increase spacing or relocate one part",
            provenance={"gap_mm": v["gap"], "limit_mm": v["limit"]}))
    return out
