"""Zero-dependency KiCad S-expression reader — parse a saved `.kicad_pcb` / `.kicad_sch`
directly, no running KiCad, no pcbnew.

Why: to verify the EasyEDA→KiCad hand-off (pcbflow.import_diff) and to run offline checks in
CI, we need the board's netlist from the file itself. KiCad stores everything as Lisp-style
S-expressions; this module tokenizes and parses them into nested Python lists, then extracts
the post-layout netlist (component → pad → net) from a `.kicad_pcb`.

The approach — a pure-Python S-expression parser that reads saved EDA files directly instead
of driving a GUI — is a standard, well-proven technique for offline EDA analysis. Pure Python 3
standard library.

Public API:
    parse(text)                       -> nested list (the S-expr tree)
    read_pcb_netlist(path_or_text)    -> {"components": [...], "nets": {net: ["REF.pad", ...]}}
    read_sch_components(path_or_text) -> [{"ref", "lib_id"}]  (components only; see note)
"""
import os

_OPEN = object()          # structural token sentinels (distinct from any string value, so a
_CLOSE = object()         # quoted string that happens to contain "(" is never mis-parsed)


def _tokenize(text):
    """Yield _OPEN, _CLOSE, or a string value. Handles quoted strings with \\-escapes."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "(":
            i += 1
            yield _OPEN
        elif c == ")":
            i += 1
            yield _CLOSE
        elif c == '"':
            i += 1
            buf = []
            while i < n:
                c = text[i]
                if c == "\\" and i + 1 < n:
                    nxt = text[i + 1]
                    buf.append({"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}.get(nxt, nxt))
                    i += 2
                elif c == '"':
                    i += 1
                    break
                else:
                    buf.append(c)
                    i += 1
            yield "".join(buf)
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()"':
                j += 1
            yield text[i:j]
            i = j


def parse(text):
    """Parse S-expression text into a nested list. Returns the single top-level node."""
    stack = [[]]
    for tok in _tokenize(text):
        if tok is _OPEN:
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif tok is _CLOSE:
            if len(stack) < 2:
                raise ValueError("unbalanced ')' in S-expression")
            stack.pop()
        else:
            stack[-1].append(tok)
    if len(stack) != 1:
        raise ValueError("unbalanced '(' in S-expression")
    if not stack[0]:
        raise ValueError("empty S-expression")
    return stack[0][0]


# ── tree helpers ────────────────────────────────────────────────────
def _tag(node):
    return node[0] if isinstance(node, list) and node and isinstance(node[0], str) else None


def _children(node, tag):
    if not isinstance(node, list):
        return []
    return [c for c in node if isinstance(c, list) and _tag(c) == tag]


def _first(node, tag):
    for c in (node or []):
        if isinstance(c, list) and _tag(c) == tag:
            return c
    return None


def _load(path_or_text):
    """Accept either a path to a file or the S-expr text itself."""
    if isinstance(path_or_text, str) and os.path.exists(path_or_text):
        with open(path_or_text, "r", encoding="utf-8") as f:
            return f.read()
    return path_or_text


def _footprint_ref(fp):
    """Reference designator of a footprint: '(property "Reference" "R1")' (KiCad 7+) or the
    legacy '(fp_text reference "R1" ...)' (KiCad 6)."""
    for prop in _children(fp, "property"):
        if len(prop) >= 3 and prop[1] == "Reference":
            return prop[2]
    ft = _first(fp, "fp_text")
    if ft and len(ft) >= 3 and ft[1] == "reference":
        return ft[2]
    return None


def _pad_net_name(netnode, nettable):
    """Resolve a pad's net name across the three forms KiCad emits (verified against real files):
        (net <id> "<name>")   standard kicad-cli output      -> the inline name
        (net <id>)            id only, name in the net table  -> table[id]
        (net "<name>")        name only (some tools/fixtures) -> the name
    """
    if not netnode or len(netnode) < 2:
        return ""
    if len(netnode) >= 3:
        return netnode[2]
    tok = netnode[1]
    return nettable.get(tok, "") if tok.isdigit() else tok      # digit => id (look up), else name


def read_pcb_netlist(path_or_text):
    """Extract the post-layout netlist from a `.kicad_pcb`.

    Returns {"components": [{"ref", "footprint", "pads": [{"pad", "net"}]}],
             "nets": {net_name: ["REF.pad", ...]}}.
    A pad with no net (or net "") is treated as unconnected and omitted from `nets`.
    """
    root = parse(_load(path_or_text))
    if _tag(root) != "kicad_pcb":
        raise ValueError(f"not a .kicad_pcb (top tag is {_tag(root)!r})")
    # net-id -> name table from the top-level (net <id> "<name>") entries
    nettable = {net[1]: net[2] for net in _children(root, "net") if len(net) >= 3}
    components, nets = [], {}
    for fp in _children(root, "footprint"):
        ref = _footprint_ref(fp)
        pads = []
        for pad in _children(fp, "pad"):
            padname = pad[1] if len(pad) > 1 else "?"
            net = _pad_net_name(_first(pad, "net"), nettable)
            pads.append({"pad": padname, "net": net})
            if net and ref:
                nets.setdefault(net, []).append(f"{ref}.{padname}")
        components.append({"ref": ref, "footprint": fp[1] if len(fp) > 1 else "", "pads": pads})
    return {"components": components, "nets": {n: sorted(m) for n, m in nets.items()}}


def read_sch_components(path_or_text):
    """List components in a `.kicad_sch` (reference + lib_id). NOTE: this does NOT trace nets —
    schematic net inference needs the wire/label graph; use `kicad-cli sch export netlist` for
    that. Kept lightweight and honest: component set only (useful for a BOM/placement cross-check)."""
    root = parse(_load(path_or_text))
    if _tag(root) != "kicad_sch":
        raise ValueError(f"not a .kicad_sch (top tag is {_tag(root)!r})")
    out = []
    for sym in _children(root, "symbol"):
        lib = _first(sym, "lib_id")
        ref = None
        for prop in _children(sym, "property"):
            if len(prop) >= 3 and prop[1] == "Reference":
                ref = prop[2]
        if ref and not ref.startswith("#"):        # skip power/graphic pseudo-symbols
            out.append({"ref": ref, "lib_id": lib[1] if lib and len(lib) > 1 else ""})
    return out


def _num(node, default=0.0):
    try:
        return float(node[1])
    except (TypeError, ValueError, IndexError):
        return default


def read_pcb_geometry(path_or_text):
    """Read routed copper from a `.kicad_pcb`: track segments (with width, layer, length) and
    vias (with size, drill). Net is resolved through the top-level net table (segments/vias carry
    `(net <id>)`). Returns {"tracks": [...], "vias": [...]} — feeds the Tier-2 SI/PDN checks."""
    import math
    root = parse(_load(path_or_text))
    if _tag(root) != "kicad_pcb":
        raise ValueError(f"not a .kicad_pcb (top tag is {_tag(root)!r})")
    nettable = {net[1]: net[2] for net in _children(root, "net") if len(net) >= 3}
    tracks, vias = [], []
    for seg in _children(root, "segment"):
        s, e = _first(seg, "start"), _first(seg, "end")
        if s and e and len(s) >= 3 and len(e) >= 3:
            length = math.hypot(float(e[1]) - float(s[1]), float(e[2]) - float(s[2]))
        else:
            length = 0.0
        layer = _first(seg, "layer")
        tracks.append({"net": _pad_net_name(_first(seg, "net"), nettable),
                       "width": _num(_first(seg, "width")),
                       "layer": layer[1] if layer and len(layer) >= 2 else "",
                       "length": round(length, 4)})
    for via in _children(root, "via"):
        at = _first(via, "at")
        vias.append({"net": _pad_net_name(_first(via, "net"), nettable),
                     "x": _num(at), "y": (float(at[2]) if at and len(at) >= 3 else 0.0),
                     "size": _num(_first(via, "size")), "drill": _num(_first(via, "drill"))})
    return {"tracks": tracks, "vias": vias}


def net_lengths(geometry):
    """net name -> total routed track length (mm), summed over its segments."""
    out = {}
    for t in geometry["tracks"]:
        if t["net"]:
            out[t["net"]] = out.get(t["net"], 0.0) + t["length"]
    return {n: round(v, 4) for n, v in out.items()}


def read_pcb_zones(path_or_text):
    """Read copper pours from a `.kicad_pcb`: [{"net", "layer", "filled"}]. `filled` is True when
    the zone actually has poured copper (a `(filled_polygon …)`), not just a defined outline —
    which is what the pour-requirement check needs. Feeds the routing checks (R2)."""
    root = parse(_load(path_or_text))
    if _tag(root) != "kicad_pcb":
        raise ValueError(f"not a .kicad_pcb (top tag is {_tag(root)!r})")
    nettable = {net[1]: net[2] for net in _children(root, "net") if len(net) >= 3}
    zones = []
    for z in _children(root, "zone"):
        net = _pad_net_name(_first(z, "net"), nettable)
        nname = _first(z, "net_name")
        if not net and nname and len(nname) >= 2:
            net = nname[1]
        layer = _first(z, "layer")
        zones.append({"net": net,
                      "layer": layer[1] if layer and len(layer) >= 2 else "",
                      "filled": _first(z, "filled_polygon") is not None})
    return zones


def poured_nets(zones):
    """Set of nets that have an actually-filled pour."""
    return {z["net"] for z in zones if z["filled"] and z["net"]}
