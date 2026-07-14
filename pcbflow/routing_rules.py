"""Routing rulebook (R1) — the codified rules the routing phase MUST load and obey.

Loads/validates a `routing_rules.json`. **Every numeric rule carries a citation (`$cite`)** —
`validate()` rejects any that don't (no uncited numbers). Derives per-net-class trace widths from
current via **IPC-2152** (`pcbflow.ipc.ipc2152_width_mm`), and defines the high-current **pour**
threshold, **EMI** rules, and pour settings. A project overrides the built-in default by shipping
its own `routing_rules.json` beside the netlist.

Pure Python 3 standard library.
"""
import json
from pathlib import Path

from . import ipc

# Built-in default rulebook — JLCPCB, every number cited. A project may override any of it.
DEFAULT = {
    "$standard": "IPC-2152 (width driver) · IPC-2221B §6.2 (formula) · IPC-2221 §6 (EMI) · "
                 "JLCPCB capability sheet",
    "fab": "JLCPCB",
    "delta_t_c": 10.0,                       # assumed temperature rise for all width math
    "copper_oz": {"outer": 1.0, "inner": 0.5},   # $cite JLCPCB (1 oz outer / 0.5 oz inner on 4-layer)
    "pour": {"current_threshold_a": 2.0, "width_threshold_mm": 1.0,
             "thermal_relief": True, "clearance_mm": 0.2,
             "$cite": "IPC-2152 (area-based) / JLCPCB pour capability"},
    "net_classes": {
        "POWER":    {"current_a": 2.0, "$cite": "IPC-2152 @ ΔT=10 °C"},
        "SIGNAL":   {"width_mm": 0.25, "$cite": "JLCPCB min 0.09 mm; 0.25 mm practical floor"},
        "USB_DIFF": {"impedance_ohm": 90.0, "length_match_mm": 0.15,
                     "$cite": "USB 2.0 spec — 90 Ω differential ±10%"},
        "CLK":      {"max_length_mm": 50.0, "$cite": "SI practice — bound clock stub length"},
    },
    "emi": {"no_route_over_plane_split": True, "return_path_continuity": True,
            "clock_isolation_mm": 0.5, "$cite": "IPC-2221 §6; return-path SI practice"},
}


class RoutingRules:
    def __init__(self, spec=None):
        self.spec = spec if spec is not None else DEFAULT

    @classmethod
    def from_dict(cls, d):
        return cls(dict(d) if d is not None else dict(DEFAULT))

    @classmethod
    def load(cls, path):
        p = Path(path)
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else cls()

    @classmethod
    def beside(cls, netlist_path):
        return cls.load(Path(netlist_path).parent / "routing_rules.json")

    def delta_t(self):
        return self.spec.get("delta_t_c", 10.0)

    def copper_oz(self, layer="outer"):
        return (self.spec.get("copper_oz") or {}).get(layer, 1.0 if layer == "outer" else 0.5)

    def pour(self):
        return self.spec.get("pour", {})

    def emi(self):
        return self.spec.get("emi", {})

    def net_class(self, name):
        return (self.spec.get("net_classes") or {}).get(name, {})

    def class_width_mm(self, name, layer="outer"):
        """Derived trace width for a net class: an explicit `width_mm`, else IPC-2152 from `current_a`."""
        c = self.net_class(name)
        if "width_mm" in c:
            return c["width_mm"]
        if "current_a" in c:
            return ipc.ipc2152_width_mm(c["current_a"], self.delta_t(), self.copper_oz(layer))
        return None

    def requires_pour(self, current_a, layer="outer"):
        """A net needs a polygon pour (not a trace) if its current ≥ threshold OR the IPC-2152
        width it would need exceeds the width threshold."""
        p = self.pour()
        if current_a >= p.get("current_threshold_a", 2.0):
            return True
        return ipc.ipc2152_width_mm(current_a, self.delta_t(), self.copper_oz(layer)) \
            > p.get("width_threshold_mm", 1.0)

    def validate(self):
        """Every numeric rule must carry a `$cite`. Returns a list of problems ([] = valid)."""
        problems = []
        for name, c in (self.spec.get("net_classes") or {}).items():
            if any(k in c for k in ("width_mm", "current_a", "impedance_ohm", "max_length_mm",
                                    "length_match_mm")) and "$cite" not in c:
                problems.append(f"net_class {name}: numeric rule without a $cite")
        for key in ("pour", "emi"):
            block = self.spec.get(key)
            if block and "$cite" not in block:
                problems.append(f"{key}: block has numeric rules without a $cite")
        return problems
