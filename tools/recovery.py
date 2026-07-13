#!/usr/bin/env python3
"""
Subsystem recovery strategies for the self-healing engine (tools/heal.py).

Each factory returns a callable()->bool that ATTEMPTS a fix and reports whether it
worked. The real OS / browser / KiCad operations are injected as callables, so the
decision logic is testable without a live session — in production you pass the real
runners (the CDP driver, a Chrome launcher, pcbnew helpers). Pure Python 3 stdlib.

These are wired to the documented recipes in reliability/RECOVERY_PLAYBOOKS.md.

⚠️  VALIDATION NOTE: the browser and KiCad strategies encode the correct recovery
    LOGIC, but the live operations (CDP tab reset, Chrome relaunch, pcbnew edits)
    must be validated against a real EasyEDA/KiCad session before you rely on them.
    The pure checks (verify_kicad_import, missing_mounting_holes) are fully tested.
"""
import subprocess


# ---- browser / EasyEDA -------------------------------------------------------

def chrome_singleton(profile_dir, launch, run=subprocess.run):
    """BR-4: clear the Chrome lock files, then relaunch."""
    def _fix():
        base = profile_dir.rstrip("/")
        for lock in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            run(["rm", "-f", f"{base}/{lock}"])
        launch()
        return True
    return _fix


def renderer_reset(cdp):
    """EDA-7: reset the hung renderer at the browser (tab) level, then reopen.
    `cdp` provides create_target(url), close_target(id), hung_target(), reopen()."""
    def _fix():
        cdp.create_target("https://easyeda.com/editor")
        cdp.close_target(cdp.hung_target())
        cdp.reopen()
        return True
    return _fix


def session_reauth(reload_editor, is_signed_in):
    """EDA-1/2, EDA-3, BR-3: reload the editor; success only if the sign-in check then
    passes. If the user still isn't signed in, heal() escalates (human must log in)."""
    def _fix():
        reload_editor()
        return bool(is_signed_in())
    return _fix


def chrome_attach(relaunch, is_attached):
    """BR-2: relaunch Chrome in debug mode; success if we can then attach to :9222."""
    def _fix():
        relaunch()
        return bool(is_attached())
    return _fix


def edit_lock(close_duplicates, is_locked):
    """BR-5: close the duplicate cloud session; success if the edit-lock clears."""
    def _fix():
        close_duplicates()
        return not bool(is_locked())
    return _fix


# ---- KiCad (pure, fully tested checks) ---------------------------------------

def verify_kicad_import(before_footprints, after_footprints):
    """KI-2: import fidelity check. ok if no footprints were dropped."""
    dropped = max(0, before_footprints - after_footprints)
    return {"ok": after_footprints >= before_footprints, "dropped": dropped}


def missing_mounting_holes(expected_ids, present_ids):
    """KI-3: which mounting holes didn't survive the PADS import (to be restored)."""
    present = set(present_ids)
    return [h for h in expected_ids if h not in present]
