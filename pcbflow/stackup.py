"""Stack-up model — the physical layer geometry that impedance and current calcs consume.

`dfm` knows layer count + copper weight, but controlled-impedance and IR-drop math need the real
stack: copper thickness per layer and the dielectric height + permittivity (Er) around each
signal layer. Copper thickness follows the standard `t = 0.0347 mm per oz` (1 oz ≈ 35 µm).

Pure Python 3 standard library.
"""
from dataclasses import dataclass, field

OZ_TO_MM = 0.0347            # copper thickness per ounce (1 oz ≈ 35 µm)
FR4_ER = 4.3                 # typical FR-4 relative permittivity


def copper_thickness_mm(oz):
    return OZ_TO_MM * oz


@dataclass
class Layer:
    name: str
    kind: str                # "signal" | "plane" | "core" | "prepreg"
    copper_oz: float = 0.0
    height_mm: float = 0.0    # dielectric height below this layer (to the next copper)
    er: float = FR4_ER


@dataclass
class Stackup:
    name: str
    layers: list = field(default_factory=list)

    def signal_layers(self):
        return [ly for ly in self.layers if ly.kind in ("signal", "plane")]

    def dielectric_to_reference(self, layer_name):
        """(height_mm, er) from a signal layer down to its nearest reference plane below —
        the geometry a microstrip/stripline impedance formula needs. Falls back to the layer's
        own dielectric if no plane is found."""
        idx = next((i for i, ly in enumerate(self.layers) if ly.name == layer_name), None)
        if idx is None:
            return None
        for j in range(idx + 1, len(self.layers)):
            if self.layers[j].kind == "plane":
                h = sum(self.layers[k].height_mm for k in range(idx, j))
                return (h or self.layers[idx].height_mm, self.layers[idx].er)
        ly = self.layers[idx]
        return (ly.height_mm, ly.er)

    @classmethod
    def two_layer(cls, thickness_mm=1.6, copper_oz=1.0):
        """A simple 2-layer board: outer signal over a 1.6 mm core to the bottom copper."""
        return cls("2L-1oz-FR4", [
            Layer("F.Cu", "signal", copper_oz, thickness_mm, FR4_ER),
            Layer("B.Cu", "signal", copper_oz, 0.0, FR4_ER)])

    @classmethod
    def four_layer(cls, copper_oz=1.0):
        """A typical 4-layer JLCPCB stack: sig / GND plane / PWR plane / sig (0.2 mm to plane)."""
        return cls("4L-1oz-FR4", [
            Layer("F.Cu", "signal", copper_oz, 0.2, FR4_ER),
            Layer("In1.Cu", "plane", copper_oz, 1.065, FR4_ER),
            Layer("In2.Cu", "plane", copper_oz, 0.2, FR4_ER),
            Layer("B.Cu", "signal", copper_oz, 0.0, FR4_ER)])
