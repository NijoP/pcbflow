#!/usr/bin/env python3
"""
pcbflow launch-easyeda — cross-platform EasyEDA launcher (roadmap Phase 4).

Clones the logged-in Chrome profile (minus caches), clears the lock files, and
launches Chrome with remote debugging on :9222 — on Linux, macOS, and Windows.
Replaces the Linux-only bash recipe (rsync + rm Singleton*). Pure Python 3 stdlib.

Usage:
    python3 tools/launch-easyeda.py            # clone profile + launch with debug port
    python3 tools/launch_easyeda.py --dry-run  # show what it would do (safe)
    python3 tools/launch_easyeda.py --port 9333

⚠️  The launch itself needs a real machine with Chrome + a signed-in EasyEDA account;
    validate on your OS. --dry-run and the path logic are testable anywhere.
"""
import argparse, os, shutil, subprocess, sys
from pathlib import Path
import platform_utils as P

_IGNORE = shutil.ignore_patterns("Cache", "Code Cache", "GPUCache", "*Cache*",
                                 "Singleton*", "*.log")
EDITOR_URL = "https://easyeda.com/editor"


def plan(port=9222, url=EDITOR_URL, system=None, home=None):
    return {"chrome": P.find_chrome(system),
            "src": str(P.default_profile_dir(system, home)),
            "dst": str(P.clone_profile_dir(home)),
            "port": port, "url": url, "locks": P.lock_files()}


def launch(port=9222, url=EDITOR_URL, system=None, home=None, dry_run=False, run=subprocess.run):
    pl = plan(port, url, system, home)
    if not pl["chrome"]:
        print("Chrome not found — install it (handbook step 2).")
        return 2
    cmd = [pl["chrome"], f"--user-data-dir={pl['dst']}",
           f"--remote-debugging-port={pl['port']}", pl["url"]]
    if dry_run:
        print("would clone profile:", pl["src"], "→", pl["dst"], "(excluding caches)")
        print("would clear locks:", ", ".join(pl["locks"]))
        print("would launch:", " ".join(cmd))
        return 0
    dst = Path(pl["dst"])
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    try:
        shutil.copytree(pl["src"], dst, ignore=_IGNORE, dirs_exist_ok=True)
    except shutil.Error:
        # Windows locks profile files while Chrome is open; copytree copies the rest
        # and raises at the end listing what it skipped. Warn and continue.
        print("note: some profile files were locked and skipped — for a complete "
              "clone, CLOSE all Chrome windows before running this.")
    except Exception as e:
        print(f"could not clone the Chrome profile: {e}\n"
              "Close all Chrome windows and try again (Windows locks the profile "
              "while Chrome is open).")
        return 2
    for lk in pl["locks"]:
        try:
            os.remove(dst / lk)
        except OSError:
            pass
    run(cmd)
    print(f"launched EasyEDA with remote debugging on :{pl['port']} "
          f"(profile clone: {pl['dst']})")
    return 0


def main():
    ap = argparse.ArgumentParser(description="cross-platform EasyEDA/Chrome launcher")
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sys.exit(launch(port=a.port, dry_run=a.dry_run))


if __name__ == "__main__":
    main()
