"""Parts spec — the electrical parameters a netlist doesn't carry.

The `.enet` gives connectivity, net classes, and diff-pair/equal-length intent, but **not** pin
electrical types or component ratings — so ERC (drive conflicts), rating sanity, and power-tree
checks have nothing to reason over. This module adds a small, **optional** sidecar keyed by
designator that supplies exactly those parameters. Checks that need it **degrade gracefully**:
with no entry for a part, that check is skipped (reported, never silently guessed).

Sidecar `parts.json` (lives beside the netlist), example:

    {
      "U1": {"role": "ldo",
             "pins": {"1": "pwr_in", "2": "pwr_in", "3": "pwr_in", "5": "pwr_out"},
             "ratings": {"vin_max": 6.0, "vout": 3.3, "vdropout": 0.3, "iout_max": 0.5}},
      "R3": {"role": "resistor", "ratings": {"r_ohm": 1000, "p_max": 0.063}},
      "D1": {"role": "led",      "ratings": {"vf": 2.0, "i_typ": 0.01, "i_max": 0.02}},
      "C1": {"role": "cap",      "ratings": {"v_rating": 16.0}}
    }

Pin electrical types (schematic-ERC vocabulary):
    in · out · bidir · tri · passive · pwr_in · pwr_out · oc (open-collector) · nc · unspec

Pure Python 3 standard library.
"""
import json
from pathlib import Path

PIN_TYPES = ("in", "out", "bidir", "tri", "passive", "pwr_in", "pwr_out", "oc", "nc", "unspec")
# pins that actively drive a net (used for contention detection)
STRONG_DRIVERS = ("out", "pwr_out")


class Parts:
    """A parts spec: designator -> {role, pins{pin: type}, ratings{...}}. Missing = unknown."""

    def __init__(self, spec=None):
        self.spec = spec or {}

    @classmethod
    def from_dict(cls, d):
        return cls(dict(d or {}))

    @classmethod
    def load(cls, path):
        p = Path(path)
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else cls()

    @classmethod
    def beside(cls, netlist_path):
        """Load the `parts.json` sitting next to a netlist (or an empty spec if absent)."""
        return cls.load(Path(netlist_path).parent / "parts.json")

    def has(self, des):
        return des in self.spec

    def role(self, des):
        return (self.spec.get(des) or {}).get("role", "")

    def pin_type(self, des, pin):
        """Electrical type of a pin, or 'unspec' if unknown."""
        t = ((self.spec.get(des) or {}).get("pins") or {}).get(str(pin), "unspec")
        return t if t in PIN_TYPES else "unspec"

    def ratings(self, des):
        return (self.spec.get(des) or {}).get("ratings", {}) or {}

    def rating(self, des, key, default=None):
        return self.ratings(des).get(key, default)

    def designators(self):
        return list(self.spec.keys())
