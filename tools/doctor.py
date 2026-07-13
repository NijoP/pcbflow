#!/usr/bin/env python3
"""
pcbflow doctor — preflight environment check for the PCB Flow workspace.

Run this before any design work. It verifies the tools, the OS, and the PCB Flow
config, explains any problem in plain English, and tells you exactly how to fix it.
Pure Python 3 standard library — nothing to install.

Usage:
    python3 tools/doctor.py             # readiness for getting started (phases 1-2)
    python3 tools/doctor.py --phase 4   # readiness up to a given workflow phase
    python3 tools/doctor.py --all       # readiness for the whole pipeline (needs KiCad)
    python3 tools/doctor.py --json      # machine-readable output (for the AI)

Exit code: 0 = ready for the requested phase; 1 = a required tool is missing.
See reliability/DEPENDENCY_VALIDATION.md for the design behind this.
"""
import sys, os, shutil, subprocess, platform, json, argparse, socket
from pathlib import Path

OK, WARN, FAIL, SKIP = "OK", "WARN", "FAIL", "SKIP"
SYM = {OK: "OK ", WARN: "!! ", FAIL: "XX ", SKIP: "-- "}
EMOJI = {OK: "✅", WARN: "⚠️ ", FAIL: "❌", SKIP: "➖"}

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cmd(args, timeout=6):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()
    except Exception as e:
        return 127, str(e)


def which(name):
    return shutil.which(name)


def mk(name, present, detail, fix, needed_from, warn=False):
    """present: True=ok, False=missing/bad, None=not applicable. needed_from: the
    workflow phase at/after which this becomes required (None = optional)."""
    return {"name": name, "present": present, "detail": detail,
            "fix": fix, "needed_from": needed_from, "warn": warn}


# ---- individual checks -------------------------------------------------------

def check_os():
    s = platform.system()
    if s in ("Linux", "Darwin"):
        return mk("Operating system", True, f"{s} (supported)", "", None)
    if s == "Windows":
        return mk("Operating system", True,
                  "Windows (supported — use 'python'/'py' and the .py tools)",
                  "See handbook/windows-setup.md", None, warn=True)
    return mk("Operating system", True, s, "", None)


def check_python():
    v = sys.version_info
    ok = v >= (3, 9)
    return mk("Python", ok, f"{v.major}.{v.minor}.{v.micro}" + ("" if ok else " (need >=3.9)"),
              "Install Python 3.9+ from python.org", 0)


def check_git():
    if not which("git"):
        return mk("Git", False, "not found", "Install Git from git-scm.com", 0)
    _, ver = run_cmd(["git", "--version"])
    _, name = run_cmd(["git", "config", "--global", "user.name"])
    _, email = run_cmd(["git", "config", "--global", "user.email"])
    detail = ver.replace("git version", "").strip()
    if not (name.strip() and email.strip()):
        return mk("Git", False, detail + " (identity not set)",
                  'git config --global user.name "Your Name"; '
                  'git config --global user.email "you@example.com"', 0)
    return mk("Git", True, detail, "", 0)


def check_node():
    if not which("node"):
        return mk("Node.js", False, "not found", "Install Node LTS from nodejs.org", 3)
    _, out = run_cmd(["node", "-v"])
    ver = out.strip().lstrip("v")
    major = int(ver.split(".")[0]) if ver[:1].isdigit() else 0
    ok = major >= 18
    return mk("Node.js", ok, ver + ("" if ok else " (need >=18)"),
              "Install Node 18+ from nodejs.org", 3)


def check_chrome():
    for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        if which(n):
            return mk("Chrome (for EasyEDA automation)", True, n, "", 3)
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(mac):
        return mk("Chrome (for EasyEDA automation)", True, "macOS app", "", 3)
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
        if os.path.exists(p):
            return mk("Chrome (for EasyEDA automation)", True, "Windows install", "", 3)
    return mk("Chrome (for EasyEDA automation)", False, "not found",
              "Install Google Chrome (needed so the AI can read your EasyEDA board)", 3)


def check_rsync():
    if platform.system() == "Windows":
        return mk("rsync (EasyEDA profile clone)", None, "N/A on Windows",
                  "Windows uses a different EasyEDA launch method (roadmap Phase 4)", None)
    ok = bool(which("rsync"))
    return mk("rsync", ok, "found" if ok else "not found",
              "Install rsync: Ubuntu 'sudo apt install rsync', macOS 'brew install rsync'", 3)


def check_kicad():
    ok = bool(which("kicad-cli"))
    return mk("KiCad (kicad-cli)", ok, "found" if ok else "not found (needed from phase 10)",
              "Install KiCad from kicad.org/download", 10)


def check_vscode():
    ok = bool(which("code"))
    return mk("VS Code (code command)", ok, "found" if ok else "not found (optional)",
              "Install VS Code and enable its shell command", None)


def check_ai_config():
    ok = (REPO_ROOT / "CLAUDE.md").exists() and (REPO_ROOT / "AGENTS.md").exists()
    return mk("PCB Flow config (CLAUDE.md / AGENTS.md)", ok, "present" if ok else "missing",
              "Open the PCB Flow folder in VS Code (or re-clone the repository)", 0)


def check_easyeda():
    try:
        socket.create_connection(("easyeda.com", 443), timeout=3).close()
        return mk("EasyEDA reachable", True, "reachable (sign-in checked at runtime)", "", 3)
    except Exception:
        return mk("EasyEDA reachable", False, "no connection",
                  "Check your internet, then sign in to EasyEDA in the browser", 3)


CHECKS = [check_os, check_python, check_git, check_ai_config, check_node,
          check_chrome, check_rsync, check_vscode, check_easyeda, check_kicad]


# ---- evaluation & rendering --------------------------------------------------

def effective(chk, target_phase):
    if chk["present"] is None:
        return SKIP
    if chk["present"]:
        return WARN if chk["warn"] else OK
    nf = chk["needed_from"]
    if nf is None:
        return WARN                      # optional and missing
    return FAIL if target_phase >= nf else WARN  # missing: blocking now, or needed later


def main():
    ap = argparse.ArgumentParser(description="PCB Flow environment preflight check")
    ap.add_argument("--phase", type=int, default=1, help="check readiness up to this workflow phase (1-12)")
    ap.add_argument("--all", action="store_true", help="check the whole pipeline (implies --phase 12)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--ascii", action="store_true", help="plain symbols (no emoji)")
    args = ap.parse_args()
    target = 12 if args.all else args.phase
    sym = SYM if args.ascii else EMOJI

    results = []
    for fn in CHECKS:
        try:
            chk = fn()
        except Exception as e:                       # a doctor must never crash
            chk = mk(fn.__name__, False, f"check errored: {e}", "report this", None)
        results.append((chk, effective(chk, target)))

    if args.json:
        print(json.dumps([{**c, "status": s} for c, s in results], indent=2))
        sys.exit(1 if any(s == FAIL for _, s in results) else 0)

    fails = sum(1 for _, s in results if s == FAIL)
    warns = sum(1 for _, s in results if s == WARN)
    print(f"PCB Flow environment check  (readiness for phase {target}) "
          + "─" * 20)
    for chk, s in results:
        print(f"  {sym[s]} {chk['name']:<34} {chk['detail']}")
        if s in (FAIL, WARN) and chk["fix"]:
            lead = "→ fix: " if s == FAIL else "→ note: "
            print(f"       {lead}{chk['fix']}")
    print("─" * 54)
    if fails:
        print(f"  {fails} required item(s) missing for phase {target} — fix the ❌ items above before starting.")
    elif warns:
        print(f"  Ready for phase {target}. {warns} optional/later item(s) noted (⚠️).")
    else:
        print(f"  All good — ready for phase {target}.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
