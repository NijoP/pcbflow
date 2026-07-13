#!/usr/bin/env python3
"""
pcbflow tidy-schematic — de-collide + grid-snap schematic blocks (roadmap Phase 5).

Addresses the known §7 limitation: script-drawn schematics are electrically correct
but not perfectly aligned. This is the PURE geometry: given block bounding boxes it
returns non-overlapping, grid-snapped positions. Pure Python 3 standard library.

A 'block' = {"id": str, "x": float, "y": float, "w": float, "h": float}
            (x, y = top-left corner; units are the schematic's own units).

Usage:
    python3 tools/tidy_schematic.py blocks.json --gap 1.0 --pitch 2.54

⚠️  The LIVE parts — measuring real bboxes (getPrimitivesBBox) and applying the new
    positions (setState) — need an EasyEDA session. This module is the algorithm they
    call; it is fully tested offline. Alignment is cosmetic and never electrical.
"""
import argparse, json, sys


def _overlap(a, b, gap=0.0):
    return not (a["x"] + a["w"] + gap <= b["x"] or b["x"] + b["w"] + gap <= a["x"]
                or a["y"] + a["h"] + gap <= b["y"] or b["y"] + b["h"] + gap <= a["y"])


def has_overlaps(blocks, gap=0.0):
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            if _overlap(blocks[i], blocks[j], gap):
                return True
    return False


def resolve_overlaps(blocks, gap=1.0, passes=100):
    """Push overlapping blocks apart with a stable top-left sweep. Returns a new list
    with no overlaps (within `passes`)."""
    bs = [dict(b) for b in blocks]
    for _ in range(passes):
        bs.sort(key=lambda b: (b["y"], b["x"], b["id"]))
        moved = False
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                if _overlap(bs[i], bs[j], gap):
                    dx = bs[i]["x"] + bs[i]["w"] + gap - bs[j]["x"]
                    dy = bs[i]["y"] + bs[i]["h"] + gap - bs[j]["y"]
                    if dx <= dy:            # smaller shift wins → tidier result
                        bs[j]["x"] += dx
                    else:
                        bs[j]["y"] += dy
                    moved = True
        if not moved:
            break
    return bs


def snap_to_grid(blocks, pitch=2.54):
    out = []
    for b in blocks:
        c = dict(b)
        c["x"] = round(b["x"] / pitch) * pitch
        c["y"] = round(b["y"] / pitch) * pitch
        out.append(c)
    return out


def tidy(blocks, gap=1.0, pitch=2.54):
    """De-collide, then snap to the grid. Snapping can reintroduce a tiny overlap, so
    resolve once more at gap 0 to guarantee separation on the grid."""
    stepped = snap_to_grid(resolve_overlaps(blocks, gap), pitch)
    return resolve_overlaps(stepped, gap=0.0) if has_overlaps(stepped, 0.0) else stepped


def main():
    ap = argparse.ArgumentParser(description="de-collide + grid-snap schematic block bboxes")
    ap.add_argument("json_in", help="JSON list of blocks {id,x,y,w,h}")
    ap.add_argument("--gap", type=float, default=1.0)
    ap.add_argument("--pitch", type=float, default=2.54)
    a = ap.parse_args()
    with open(a.json_in) as f:
        blocks = json.load(f)
    result = tidy(blocks, a.gap, a.pitch)
    print(json.dumps(result, indent=2))
    if has_overlaps(result, 0.0):
        print("warning: could not fully de-collide (increase --gap or board area)", file=sys.stderr)


if __name__ == "__main__":
    main()
