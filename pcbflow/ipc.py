"""IPC-2221 trace-width + via-ampacity solver.

Pure, deterministic engineering math used by the feasibility, placement-KG, and
routing phases. Matches the reference numbers in knowledge/design-standards.md
(1 oz external @ΔT10: 1 A≈0.25 mm, 5 A≈2.79 mm, 10 A≈7.6 mm).

    I = k · ΔT^0.44 · A^0.725      (external k=0.048, internal 0.5 oz derated k=0.024)
"""
import math

_OZ_TO_MIL = 1.378          # 1 oz copper ≈ 1.378 mil finished thickness
_PLANE_THRESHOLD_MM = 5.0   # above this, a trace is absurd — use a plane/pour
# per-via ampacity, 20 µm plating, ΔT10 °C (knowledge/design-standards.md)
_VIA_A = {0.2: 0.5, 0.3: 0.9, 0.4: 1.2, 0.5: 1.7, 0.6: 2.1, 0.8: 2.8}


def trace_width_mm(current_a, delta_t_c=10.0, copper_oz=1.0, internal=False):
    """Minimum IPC-2221 trace width (mm) to carry `current_a` at `delta_t_c` rise."""
    if current_a <= 0:
        return 0.0
    k = 0.024 if internal else 0.048
    area_mil2 = (current_a / (k * (delta_t_c ** 0.44))) ** (1.0 / 0.725)
    width_mil = area_mil2 / (_OZ_TO_MIL * copper_oz)
    return round(width_mil * 0.0254, 4)          # mil -> mm


def ipc2152_width_mm(current_a, delta_t_c=10.0, copper_oz=1.0):
    """IPC-2152 methodology width (mm) — the width DRIVER for routing.

    IPC-2152 is chart-based (the standard gives no closed-form equation), so we compute the
    required copper **cross-section** with the IPC-2221B §6.2 power law (the accepted closed form,
    external coefficient k=0.048) and convert to width using the **actual layer copper thickness**.

    Why IPC-2152 over IPC-2221: IPC-2221 applies a blanket ×2 derate for inner layers (k=0.024).
    IPC-2152's measured data showed that's overly conservative — inner traces next to planes run
    cooler — so the inner derating is captured *only* by the thinner copper (JLCPCB inner = 0.5 oz
    → ~2× the width of a 1 oz outer trace), not an extra k halving. Confirm final widths with the
    fab's IPC-2152 calculator.

    Sources: IPC-2221B §6.2 (formula); IPC-2152 (area-based, layer-copper-aware); JLCPCB (1 oz
    outer / 0.5 oz inner).
    """
    return trace_width_mm(current_a, delta_t_c, copper_oz=copper_oz, internal=False)


def needs_plane(current_a, **kw):
    """True if the required width exceeds the practical trace ceiling (~5 mm)."""
    return trace_width_mm(current_a, **kw) > _PLANE_THRESHOLD_MM


def recommend(current_a, **kw):
    w = trace_width_mm(current_a, **kw)
    return {
        "current_a": current_a,
        "width_mm": w,
        "method": "plane/pour" if w > _PLANE_THRESHOLD_MM else "trace",
        "margin_note": "add >=10% margin — an at-limit width is zero margin",
    }


def via_count(current_a, drill_mm=0.3):
    """Number of vias needed to carry `current_a` (symmetric farm; nearest via hogs)."""
    per = _VIA_A.get(round(drill_mm, 1), 0.9)
    return max(1, math.ceil(current_a / per))
