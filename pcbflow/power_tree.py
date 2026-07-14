"""Power-tree integrity (HW3) — every rail sourced, voltage domains consistent, current budgeted.

Builds the power tree from the netlist + parts spec: a **rail** is a net carrying power pins; its
voltage comes from the part that sources it (an LDO's `vout`, a connector's `v_nominal`, a
regulator's `vout`). Then it checks:
  - **unsourced rail:** a net with power-input pins but no power-output source → error;
  - **voltage-domain mismatch:** a part rated for Vx sitting on a rail at Vy → error;
  - **current budget:** Σ load current on a rail > its source's `iout_max` → error.

Returns (findings, rails) so downstream checks (ratings) can reuse the rail voltages.
Pure Python 3 standard library.
"""
from .findings import finding


def _pin(member):
    return member.split(".", 1)[1].split("(", 1)[0] if "." in member else "?"


def _f(rule_id, severity, summary, where, comps=None, nets=None, rec=""):
    return finding(detector="power_tree", rule_id=rule_id, category="power", severity=severity,
                   confidence="deterministic", evidence_source="topology", summary=summary,
                   where=where, components=comps, nets=nets, recommendation=rec)


def _source_voltage(parts, des):
    """The voltage a part sources, if it is a source (ldo/regulator/connector/battery)."""
    r = parts.ratings(des)
    for k in ("vout", "v_nominal", "v_out", "voltage"):
        if k in r:
            return r[k]
    return None


def build_rails(enet, parts):
    """rail net -> {voltage, source, sinks[], i_load}. A rail is any net with a power pin."""
    rails = {}
    for net, members in enet.nets().items():
        srcs, sinks, i_load = [], [], 0.0
        for m in members:
            des, pin = m.split(".", 1)[0], _pin(m)
            t = parts.pin_type(des, pin)
            if t == "pwr_out":
                srcs.append(des)
            elif t == "pwr_in":
                sinks.append(des)
                i_load += parts.rating(des, "i_load", 0.0) or 0.0
        if srcs or sinks:
            v = next((_source_voltage(parts, s) for s in srcs if _source_voltage(parts, s) is not None), None)
            rails[net] = {"voltage": v, "source": srcs[0] if srcs else None,
                          "sources": srcs, "sinks": sinks, "i_load": round(i_load, 4)}
    return rails


def run(enet, parts):
    """Returns (findings, rails). Rails map is reused by pcbflow.ratings for voltage-aware checks."""
    rails = build_rails(enet, parts)
    V = []
    for net, r in rails.items():
        # unsourced rail: sinks with no source
        if r["sinks"] and not r["sources"]:
            V.append(_f("unsourced_rail", "error",
                        f"power rail '{net}' feeds {len(r['sinks'])} part(s) but has no source",
                        net, sorted(r["sinks"]), [net], "connect the rail to a regulator/connector"))
        # current budget: Σ load > source rating
        for s in r["sources"]:
            imax = parts.rating(s, "iout_max")
            if imax is not None and r["i_load"] > imax + 1e-9:
                V.append(_f("current_budget", "error",
                            f"rail '{net}' draws {r['i_load']} A > {s} rating {imax} A",
                            net, [s], [net], "raise the regulator rating or cut the load"))
        # voltage-domain mismatch: a sink rated for a different voltage than the rail
        if r["voltage"] is not None:
            for des in r["sinks"]:
                vr = parts.rating(des, "v_rail") or parts.rating(des, "vdd")
                if vr is not None and abs(vr - r["voltage"]) > 0.15 * max(vr, r["voltage"]):
                    V.append(_f("voltage_domain", "error",
                                f"{des} is rated {vr} V but sits on the {r['voltage']} V rail '{net}'",
                                f"{des}@{net}", [des], [net], "match the part to its rail voltage"))
    return V, rails
