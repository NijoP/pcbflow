#!/usr/bin/env python3
"""Claims linter — every relative Markdown link in the key docs must resolve to a real file.

This is the enforcement behind "no aspirational documentation": if a doc points at an artifact
(a file, a report, a tool), that artifact must exist in the repo. External links (http/https),
pure anchors (#section), and mailto: are skipped; an anchor on a real file is checked by file.

Usage:
    python3 tools/check_claims.py        # exit 0 if all links resolve, 1 (+ list) otherwise
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = ["README.md", "VALIDATION.md", "CHANGELOG.md", "ROADMAP.md", "install-guidance.md",
        "llms.txt", "GEMINI.md", "AGENTS.md", "CONTRIBUTING.md", "docs/CONFIG.md",
        "projects/example-usb-c-3v3/README.md", "pcbflow/README.md"]
_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def broken_links():
    """Return a list of (doc, target) for every relative link that doesn't resolve."""
    out = []
    for rel in DOCS:
        f = REPO / rel
        if not f.exists():
            continue
        for m in _LINK.finditer(f.read_text(encoding="utf-8")):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = target.split("#", 1)[0]
            if not path:
                continue
            if not (f.parent / path).resolve().exists():
                out.append((rel, target))
    return out


def main():
    broken = broken_links()
    for rel, t in broken:
        print(f"BROKEN LINK: {rel} -> {t}")
    print(f"{'FAIL' if broken else 'OK'}: {len(broken)} broken link(s) across "
          f"{sum((REPO / d).exists() for d in DOCS)} docs")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
