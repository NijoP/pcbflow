#!/usr/bin/env python3
"""
pcbflow diagnose — classify an automation failure into a known fault class.

Maps an error message / HTTP status to a VULNERABILITY_REPORT id, explains it in
plain English, says whether it's safe to retry, and gives the engineer-friendly
message. Pure Python 3 standard library.

Usage:
    python3 tools/diagnose.py "kicad-cli: command not found"
    python3 tools/diagnose.py --http 401 "Unauthorized"
    python3 tools/diagnose.py --log projects/<board>/.logs/<phase>.jsonl   # last failure

Design: reliability/SELF_HEALING.md §2 (failure→recovery) + §5 (human errors).
"""
import sys, re, json, argparse
from pathlib import Path

# (id, title, why, recovery, retryable, human_message, matchers{http, pat})
RULES = [
 ("EDA-1/2", "EasyEDA session expired", "Your EasyEDA login timed out.",
  "Prompt re-login, then retry the step.", False,
  "Your EasyEDA session expired. Please log back into EasyEDA; I'll continue from where we stopped — no work is lost.",
  dict(http=(401,), pat=r"unauthorized|session expired|not logged in|login required")),
 ("EDA-3", "EasyEDA access forbidden", "The request was refused (permission or bot block).",
  "Back off; if it persists, ask the engineer to check access.", False,
  "EasyEDA refused the request. Please make sure you're signed in and have access to this project.",
  dict(http=(403,), pat=r"forbidden")),
 ("EDA-5", "EasyEDA rate limit", "Too many requests too fast.",
  "Exponential backoff and slow the cadence.", True,
  "EasyEDA asked me to slow down. I'll wait and retry — no action needed.",
  dict(http=(429,), pat=r"rate limit|too many requests")),
 ("EDA-6", "EasyEDA/server error", "A temporary server-side error.",
  "Backoff and retry.", True,
  "EasyEDA had a temporary hiccup; I'll retry. No action needed.",
  dict(http=(500, 502, 503, 504), pat=r"server error|internal error|bad gateway|service unavailable")),
 ("EDA-7", "EasyEDA renderer hang", "The drawing window stopped responding (known glitch).",
  "Reset the browser tab, reopen the project, replay the last step.", True,
  "The EasyEDA window froze (a known glitch). I'll restart it and replay the last step.",
  dict(pat=r"renderer|eval timeout|page.*not respond|capturescreenshot.*timeout")),
 ("EDA-10", "Component not found", "The part search returned no usable match.",
  "Broaden the query, try the LCSC id, try an alternate package.", False,
  "I couldn't find a library match for that part — please give me an LCSC number or an exact part name.",
  dict(pat=r"part not found|no token match|no match for|component not found")),
 ("BR-2", "Can't attach to the browser", "The automation couldn't reach Chrome's debug port.",
  "Relaunch Chrome with the debug flag and re-attach.", True,
  "I couldn't connect to the EasyEDA window. Please make sure Chrome/EasyEDA is open and signed in, then say 'retry'.",
  dict(pat=r"econnrefused|:9222|connection refused|cannot connect.*debug")),
 ("BR-4", "Chrome lock file", "A previous Chrome instance left a lock.",
  "Remove Singleton* and relaunch.", True,
  "A leftover Chrome lock blocked startup; I cleared it and relaunched.",
  dict(pat=r"singleton|profile.*in use|already running")),
 ("BR-3", "Browser logged out", "The Chrome profile launched signed out.",
  "Re-clone the logged-in profile; prompt sign-in.", False,
  "The browser opened signed out of EasyEDA. Please sign in, then say 'retry'.",
  dict(pat=r"logged out|please sign in|login form")),
 ("KI-5", "kicad-cli missing", "KiCad's command-line tool isn't installed / on PATH.",
  "Ask the engineer to install KiCad.", False,
  "KiCad's command-line tool isn't installed. Please install KiCad (handbook step 2), then say 'retry'.",
  dict(pat=r"kicad-cli.*(not found|no such)|command not found.*kicad")),
 ("KI-6", "Phantom DRC risk", "DRC ran (or would run) without the ruleset sidecar.",
  "Run DRC only via drc.sh so the ruleset is present.", True,
  "I re-ran the design-rule check with the proper rule set to avoid a false 'all clear'.",
  dict(pat=r"no .*kicad_pro|phantom|missing ruleset|default rules")),
 ("SC-2", "Missing dependency", "A required software package isn't installed.",
  "Run the install step, then retry.", False,
  "A helper needs a package installed. I'll show you the exact command to run, then say 'retry'.",
  dict(pat=r"modulenotfounderror|no module named|cannot find module|importerror|command not found")),
 ("SC-3", "Timeout", "A step didn't finish in time.",
  "Retry once with a longer budget.", True,
  "A step took too long; I'll retry it. No action needed unless it repeats.",
  dict(pat=r"timeout|timed out|deadline exceeded")),
 ("GIT-AUTH", "GitHub sign-in needed", "Publishing needs your GitHub credentials.",
  "Not automatable — the human must authenticate.", False,
  "I saved everything locally but couldn't publish to GitHub — you need to sign in (a token or the VS Code GitHub login). Your work is safe and committed.",
  dict(pat=r"could not read username|authentication failed|permission.*denied|403.*github")),
]

FALLBACK = ("SC-1", "Unclassified error", "An unexpected error the classifier doesn't recognize yet.",
            "Log it, checkpoint, and escalate with the details.", False,
            "Something went wrong that I don't recognize yet. I've logged the details; here's what I know.")


def _mk(rid, title, why, rec, retry, human):
    return {"class": rid, "title": title, "why": why, "recovery": rec,
            "retryable": retry, "human_message": human}


def classify(text="", http=None):
    """Return the fault classification for an error message and/or HTTP status."""
    t = (text or "").lower()
    for rid, title, why, rec, retry, human, m in RULES:
        if http is not None and http in m.get("http", ()):
            return _mk(rid, title, why, rec, retry, human)
        pat = m.get("pat")
        if pat and re.search(pat, t):
            return _mk(rid, title, why, rec, retry, human)
    return _mk(*FALLBACK)


def _last_failure(logpath):
    last = None
    for line in Path(logpath).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") in ("failed", "escalated"):
            last = r
    return last


def main():
    ap = argparse.ArgumentParser(description="classify an automation failure")
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--http", type=int)
    ap.add_argument("--log", help="classify the last failure in a JSONL phase log")
    a = ap.parse_args()
    if a.log:
        rec = _last_failure(a.log)
        if not rec:
            print("no failure recorded in that log.")
            return
        res = classify((rec.get("error") or {}).get("message", ""), None)
    else:
        res = classify(a.text, a.http)
    print(f"[{res['class']}] {res['title']}")
    print(f"  why:      {res['why']}")
    print(f"  recovery: {res['recovery']}  (retryable: {res['retryable']})")
    print(f"  engineer: {res['human_message']}")


if __name__ == "__main__":
    main()
