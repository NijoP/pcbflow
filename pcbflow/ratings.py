"""Component rating & value sanity (HW2) — the algebra that keeps a board from smoking.

Consumes the parts spec (`pcbflow.parts`) and the rail voltages from `pcbflow.power_tree`:

  - **Capacitor** across a rail: `V_rating ≥ V_rail / 0.5` (ceramics lose capacitance under DC
    bias — derate to ~2× the rail). Under-rated cap → error.
  - **LED**: `I = (V_rail − Vf) / R_series`; flag over/under the datasheet current, or a missing
    series resistor (no current limit).
  - **Resistor**: `P = I²·R`; flag `P > P_package · 0.5`.
  - **LDO/regulator dropout**: `V_in − V_out ≥ V_dropout` — else brownout (the learning-db bug).
  - **MOSFET**: `V_ds ≤ V_ds(max)·0.8`, `V_gs ≤ V_gs(max)`.

Everything degrades gracefully — a check runs only when the parts spec gives it the numbers.
Pure Python 3 standard library.
"""
from .findings import finding

DERATE_CAP = 0.5      # ceramic DC-bias derating → want ~2× the rail
DERATE_R = 0.5        # resistor power derating
DERATE_FET_VDS = 0.8  # keep Vds ≤ 80% of the rated max


def _f(rule_id, severity, summary, where, comps=None, nets=None, prov=None, rec=""):
    return finding(detector="ratings", rule_id=rule_id, category="reliability", severity=severity,
                   confidence="datasheet-backed", evidence_source="datasheet", summary=summary,
                   where=where, components=comps, nets=nets, provenance=prov, recommendation=rec)


def _rail_v(net, rails):
    r = rails.get(net) or {}
    return r.get("voltage")


def _led_current(des, pins, enet, parts, rails):
    """I = (V_rail − Vf)/R through the series resistor on the LED's anode. Returns (I, R) or (None, R)."""
    vf = parts.rating(des, "vf")
    if vf is None:
        return None, None
    nets = enet.nets()
    anode = next((n for n in pins.values() if _rail_v(n, rails) is None), None)  # non-rail = anode side
    # look for a series resistor sharing one of the LED's nets
    for rdes in parts.designators():
        if parts.role(rdes) != "resistor":
            continue
        rohm = parts.rating(rdes, "r_ohm")
        if not rohm:
            continue
        rpins = enet.comp_pin_nets().get(rdes, {})
        shared = set(rpins.values()) & set(pins.values())
        if not shared:
            continue
        other = next((n for n in rpins.values() if n not in pins.values()), None)
        vr = _rail_v(other, rails) if other else None
        if vr is not None:
            return (vr - vf) / rohm, rohm
        return None, rohm
    return None, None


def run(enet, parts, rails=None):
    """Run rating sanity over an Enet + Parts (+ optional rail voltages). Harmonized findings."""
    rails = rails or {}
    V = []
    pin_nets = enet.comp_pin_nets()
    for des in parts.designators():
        role, r, pins = parts.role(des), parts.ratings(des), pin_nets.get(des, {})

        if role == "cap":
            vr = r.get("v_rating")
            rail_v = max((v for v in (_rail_v(n, rails) for n in pins.values()) if v is not None),
                         default=None)
            if vr is not None and rail_v is not None and vr < rail_v / DERATE_CAP - 1e-9:
                V.append(_f("cap_underrated", "error",
                            f"{des}: {vr} V rating on a {rail_v} V rail (want ≥ {rail_v/DERATE_CAP:.1f} V)",
                            des, [des], prov={"v_rating": vr, "v_rail": rail_v},
                            rec="use a cap rated ≥ 2× the rail (DC-bias derating)"))

        elif role == "led":
            i, rohm = _led_current(des, pins, enet, parts, rails)
            imax, imin = r.get("i_max"), r.get("i_min")
            if rohm is None:
                V.append(_f("led_no_series_r", "warning", f"{des}: no series resistor found (no current limit)",
                            des, [des], rec="add a series resistor"))
            elif i is not None and imax is not None and i > imax + 1e-9:
                V.append(_f("led_overcurrent", "error",
                            f"{des}: I≈{i*1000:.1f} mA > {imax*1000:.0f} mA max",
                            des, [des], prov={"i_a": round(i, 4), "i_max": imax},
                            rec="increase the series resistor"))
            elif i is not None and imin is not None and i < imin - 1e-9:
                V.append(_f("led_undercurrent", "warning",
                            f"{des}: I≈{i*1000:.1f} mA < {imin*1000:.0f} mA (may be dim)", des, [des]))

        elif role == "resistor":
            pmax, iapp, rohm = r.get("p_max"), r.get("i_applied"), r.get("r_ohm")
            if pmax and iapp and rohm:
                p = iapp * iapp * rohm
                if p > pmax * DERATE_R + 1e-12:
                    V.append(_f("resistor_power", "error",
                                f"{des}: P≈{p*1000:.0f} mW > {pmax*DERATE_R*1000:.0f} mW (derated)",
                                des, [des], prov={"p_w": round(p, 4), "p_max": pmax},
                                rec="use a higher-wattage package"))

        elif role in ("ldo", "regulator"):
            vout, vdo = r.get("vout"), r.get("vdropout")
            vin = max((_rail_v(n, rails) for n in pins.values()
                       if parts.pin_type(des, next((p for p, nn in pins.items() if nn == n), "")) == "pwr_in"
                       and _rail_v(n, rails) is not None), default=None)
            if vin is not None and vout is not None and vdo is not None and (vin - vout) < vdo - 1e-9:
                V.append(_f("ldo_dropout", "error",
                            f"{des}: Vin−Vout = {vin-vout:.2f} V < dropout {vdo} V (brownout)",
                            des, [des], prov={"vin": vin, "vout": vout, "vdropout": vdo},
                            rec="raise Vin or use a lower-dropout regulator"))

        elif role in ("mosfet", "fet"):
            vds, vds_app = r.get("vds_max"), r.get("vds_applied")
            vgs, vgs_app = r.get("vgs_max"), r.get("vgs_applied")
            if vds and vds_app and vds_app > vds * DERATE_FET_VDS + 1e-9:
                V.append(_f("fet_vds_margin", "error",
                            f"{des}: Vds {vds_app} V > 80% of rated {vds} V", des, [des]))
            if vgs and vgs_app and vgs_app > vgs + 1e-9:
                V.append(_f("fet_vgs_over", "error",
                            f"{des}: Vgs {vgs_app} V exceeds rated {vgs} V", des, [des]))
    return V
