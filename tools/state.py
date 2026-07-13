#!/usr/bin/env python3
"""
pcbflow state — checkpoint (auto-commit a phase) and resume (find where we left off).

Enforces two reliability guards from the roadmap:
  - ST-1: commit a phase's work the moment it's done, so it can never be lost.
  - ST-2/5: resume from the manifest + git, never repeating completed work.

Pure Python 3 standard library + git.

Usage:
    python3 tools/state.py checkpoint <project> <phase> [--message "..."]
    python3 tools/state.py resume <project>
"""
import sys, subprocess, argparse, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*args):
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def checkpoint(project, phase, message=""):
    pdir = f"projects/{project}"
    if not (ROOT / pdir).exists():
        print(f"checkpoint: no such project — {pdir}")
        return 2
    git("add", pdir)
    rc, _ = git("diff", "--cached", "--quiet")   # rc==1 means there ARE staged changes
    if rc == 0:
        print(f"checkpoint: nothing new to commit for '{project}' (phase {phase}).")
        return 0
    msg = f"checkpoint({project}): phase {phase}" + (f"\n\n{message}" if message else "")
    rc, out = git("commit", "-m", msg)
    print(f"checkpoint: committed '{project}' phase {phase}." if rc == 0 else f"checkpoint: commit failed — {out}")
    return rc


def _current_phase(project):
    man = ROOT / f"projects/{project}/project.yaml"
    if not man.exists():
        return None
    m = re.search(r"current_phase:\s*(\d+)", man.read_text(encoding="utf-8"))
    return int(m.group(1)) if m else None


def _last_committed_phase(project):
    _, out = git("ls-files", f"projects/{project}")
    best = 0
    for f in out.splitlines():
        m = re.search(rf"projects/{re.escape(project)}/(\d\d)_", f)
        if m and not f.endswith(".gitkeep"):
            best = max(best, int(m.group(1)))
    return best


def resume(project):
    cur = _current_phase(project)
    if cur is None:
        print(f"resume: no manifest — projects/{project}/project.yaml")
        return 2
    last = _last_committed_phase(project)
    print(f"Project: {project}")
    print(f"  Manifest current phase:          {cur}")
    print(f"  Last phase with committed work:  {last if last else 'none yet'}")
    _, dirty = git("status", "--porcelain", f"projects/{project}")
    if dirty.strip():
        print("  ⚠️  Uncommitted changes present — checkpoint them before resuming:")
        print(f"        python3 tools/state.py checkpoint {project} {cur}")
    else:
        print("  ✅ Working tree clean for this project.")
    print(f"  ▶ Resume at phase {cur}. Completed, committed work is not repeated.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="checkpoint / resume a project")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("checkpoint")
    c.add_argument("project"); c.add_argument("phase"); c.add_argument("--message", default="")
    r = sub.add_parser("resume")
    r.add_argument("project")
    a = ap.parse_args()
    if a.cmd == "checkpoint":
        sys.exit(checkpoint(a.project, a.phase, a.message))
    sys.exit(resume(a.project))


if __name__ == "__main__":
    main()
