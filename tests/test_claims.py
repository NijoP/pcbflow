"""Guard: every relative Markdown link in the key docs must resolve (no aspirational docs).
Runs the tools/check_claims.py linter. Standalone or pytest:  python3 tests/test_claims.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import check_claims  # noqa: E402


def test_no_broken_doc_links():
    broken = check_claims.broken_links()
    assert broken == [], f"broken doc links (a doc points at a missing artifact): {broken}"


if __name__ == "__main__":
    test_no_broken_doc_links()
    print("PASS — claims: all documented links resolve to real files.")
