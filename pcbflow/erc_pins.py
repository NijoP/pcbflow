"""Pin-type ERC (HW1) — the drive-conflict checks a topology-only ERC can't do.

Given pin electrical types (from `pcbflow.parts`), this catches the classic schematic errors:
two outputs fighting over a net, an output tied to a power rail, a no-connect that got wired,
and inputs with nothing driving them. Emits the harmonized finding schema.

Degrades gracefully: a net whose pins are all `unspec` (no parts spec) is skipped — never guessed.
Pure Python 3 standard library.
"""
from .findings import finding


def _pin(member):
    """'R1.2(NAME)' -> '2'."""
    return member.split(".", 1)[1].split("(", 1)[0] if "." in member else "?"


def _f(rule_id, severity, summary, where, comps=None, nets=None, rec=""):
    return finding(detector="erc_pins", rule_id=rule_id, category="connectivity",
                   severity=severity, confidence="deterministic", evidence_source="topology",
                   summary=summary, where=where, components=comps, nets=nets, recommendation=rec)


def run(enet, parts):
    """Run pin-type ERC over an Enet using a Parts spec. Returns harmonized findings."""
    V = []
    for net, members in enet.nets().items():
        typed = [(m.split(".", 1)[0], _pin(m), parts.pin_type(m.split(".", 1)[0], _pin(m)))
                 for m in members]
        types = [t for *_, t in typed]
        if all(t == "unspec" for t in types):
            continue                                    # nothing typed on this net → skip
        refs = sorted({r for r, _, _ in typed})
        n_out, n_pwrout, n_in = types.count("out"), types.count("pwr_out"), types.count("in")
        has_source = any(t in ("out", "pwr_out", "bidir", "passive", "tri", "oc") for t in types)

        for r, p, t in typed:
            if t == "nc":
                V.append(_f("nc_connected", "error",
                            f"no-connect pin {r}.{p} is wired into net '{net}'",
                            f"{r}.{p}", [r], [net], "leave the NC pin unconnected"))
        if n_out >= 2:
            V.append(_f("driver_contention", "error",
                        f"net '{net}' has {n_out} output pins driving it (contention)",
                        net, refs, [net], "only one active driver per net"))
        if n_out >= 1 and n_pwrout >= 1:
            V.append(_f("output_on_power", "error",
                        f"net '{net}' ties an output pin to a power-output pin",
                        net, refs, [net], "do not drive a power rail from a logic output"))
        if n_pwrout >= 2:
            V.append(_f("multiple_supplies", "warning",
                        f"net '{net}' has {n_pwrout} power-output pins (parallel supplies?)",
                        net, refs, [net], "confirm the supplies are meant to be paralleled"))
        if n_in >= 1 and not has_source:
            V.append(_f("undriven_input", "warning",
                        f"net '{net}' reaches {n_in} input pin(s) with nothing driving it",
                        net, refs, [net], "add a driver, pull-up/down, or mark no-connect"))
    return V
