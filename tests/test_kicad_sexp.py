"""Tests for pcbflow.kicad_sexp — the zero-dep KiCad S-expression reader. Golden-file test
locks the parse of a realistic .kicad_pcb. Standalone or pytest:  python3 tests/test_kicad_sexp.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pcbflow import kicad_sexp  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "mini_board.kicad_pcb")

# the GOLDEN expected netlist for mini_board.kicad_pcb (locks the reader's output)
GOLDEN_NETS = {
    "VBUS": ["C1.1", "R1.1", "U1.1"],
    "GND":  ["C1.2", "U1.2"],
    "+3V3": ["R1.2", "U1.3"],
}


def test_golden_pcb_netlist():
    board = kicad_sexp.read_pcb_netlist(FIXTURE)
    assert board["nets"] == GOLDEN_NETS, board["nets"]
    refs = sorted(c["ref"] for c in board["components"])
    assert refs == ["C1", "R1", "U1"]
    u1 = next(c for c in board["components"] if c["ref"] == "U1")
    assert u1["footprint"] == "Package_TO_SOT_SMD:SOT-23-5"
    # pad 4 is on net 0 ("") -> unconnected -> absent from the nets view
    assert {p["pad"]: p["net"] for p in u1["pads"]}["4"] == ""


def test_pad_net_resolution_all_three_forms():
    """Real KiCad emits pad nets three ways; the reader must handle all (verified vs real files)."""
    # (net <id> "<name>") inline  +  (net <id>) id-only via the top-level table  +  (net "<name>")
    pcb = ('(kicad_pcb (version 1) (net 0 "") (net 1 "VBUS") (net 2 "GND")'
           '  (footprint "F" (property "Reference" "U1")'
           '    (pad "1" smd (net 1 "VBUS"))'      # inline id+name
           '    (pad "2" smd (net 2))'             # id only -> resolved to GND via table
           '    (pad "3" smd (net "SDA"))))')      # name only
    b = kicad_sexp.read_pcb_netlist(pcb)
    assert b["nets"] == {"VBUS": ["U1.1"], "GND": ["U1.2"], "SDA": ["U1.3"]}, b["nets"]


def test_parse_quoted_string_with_parens():
    # a quoted net name containing parens must NOT be mistaken for structure
    tree = kicad_sexp.parse('(net 1 "Net-(R1-Pad2)")')
    assert tree == ["net", "1", "Net-(R1-Pad2)"]


def test_parse_escapes_and_nesting():
    tree = kicad_sexp.parse('(a (b "x\\"y") (c 1 2))')
    assert tree == ["a", ["b", 'x"y'], ["c", "1", "2"]]


def test_unbalanced_raises():
    for bad in ("(a (b)", "(a))", ""):
        try:
            kicad_sexp.parse(bad)
            assert False, f"should reject {bad!r}"
        except ValueError:
            pass


def test_not_a_pcb_raises():
    try:
        kicad_sexp.read_pcb_netlist("(kicad_sch (version 1))")
        assert False, "should reject a non-pcb top tag"
    except ValueError:
        pass


def test_read_sch_components():
    sch = ('(kicad_sch (version 20240108)'
           '  (symbol (lib_id "Device:R") (property "Reference" "R1"))'
           '  (symbol (lib_id "power:GND") (property "Reference" "#PWR01")))')
    comps = kicad_sexp.read_sch_components(sch)
    assert comps == [{"ref": "R1", "lib_id": "Device:R"}]     # power pseudo-symbol skipped


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("PASS — kicad_sexp: golden pcb netlist, quoted parens, escapes, unbalanced, sch components.")


if __name__ == "__main__":
    _run()
