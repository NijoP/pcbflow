#!/usr/bin/env python3
"""Tests for Phase-4 cross-platform tools: platform_utils + the DRC ruleset guard.
Pure logic (no launching, no real KiCad). Run: python3 tools/test_platform.py"""
import tempfile
from pathlib import Path
import platform_utils as P
import drc


def test_os_and_paths():
    assert P.os_name("Linux") == "linux"
    assert P.os_name("Darwin") == "macos"
    assert P.os_name("Windows") == "windows"
    assert any("chrom" in c.lower() for c in P.chrome_candidates("Linux"))
    assert str(P.default_profile_dir("macos", home="/Users/x")).endswith("Google/Chrome")
    win = str(P.default_profile_dir("windows", home="C:/Users/x")).replace("\\", "/")
    assert win.endswith("User Data")


def test_find_chrome_injected():
    got = P.find_chrome("Linux", which=lambda n: "/usr/bin/google-chrome" if n == "google-chrome" else None)
    assert got == "/usr/bin/google-chrome"
    assert P.find_chrome("Linux", which=lambda n: None) is None


def test_drc_refuses_without_ruleset():
    with tempfile.TemporaryDirectory() as t:
        b = Path(t, "board.kicad_pcb"); b.write_text("x")
        res = drc.run_drc(str(b), run=lambda *a, **k: None, which=lambda n: "/usr/bin/kicad-cli")
        assert res["ok"] is False and "phantom" in res["reason"].lower()


def test_drc_runs_with_ruleset():
    with tempfile.TemporaryDirectory() as t:
        b = Path(t, "board.kicad_pcb"); b.write_text("x")
        pro = Path(t, "rules.kicad_pro"); pro.write_text("{}")
        class R:  # fake completed process
            returncode = 0
        res = drc.run_drc(str(b), str(pro), run=lambda *a, **k: R(), which=lambda n: "/usr/bin/kicad-cli")
        assert res["ok"] and Path(t, "board.kicad_pro").exists()


def test_drc_needs_kicad():
    with tempfile.TemporaryDirectory() as t:
        b = Path(t, "board.kicad_pcb"); b.write_text("x")
        res = drc.run_drc(str(b), which=lambda n: None)
        assert res["ok"] is False and "kicad-cli" in res["reason"]


def test_drc_timeout_returns_manual_fallback():
    import subprocess
    with tempfile.TemporaryDirectory() as t:
        b = Path(t, "board.kicad_pcb"); b.write_text("x")
        pro = Path(t, "rules.kicad_pro"); pro.write_text("{}")

        def boom(*a, **k):
            raise subprocess.TimeoutExpired(cmd="kicad-cli", timeout=1)
        res = drc.run_drc(str(b), str(pro), run=boom, which=lambda n: "/usr/bin/kicad-cli")
        assert res["ok"] is False and "timed out" in res["reason"] and "run it manually" in res["reason"]


if __name__ == "__main__":
    test_os_and_paths()
    test_find_chrome_injected()
    test_drc_refuses_without_ruleset()
    test_drc_runs_with_ruleset()
    test_drc_needs_kicad()
    test_drc_timeout_returns_manual_fallback()
    print("PASS — platform: OS/paths, Chrome discovery, DRC ruleset guard + timeout fallback.")
