#!/usr/bin/env python3
"""
Cross-platform helpers so PCB Flow automation isn't Linux-only (roadmap Phase 4).

Locates Chrome, the Chrome profile, and lock files per OS, and holds the minimum
tool versions. Pure Python 3 standard library. All functions accept an injected
`system` (platform name) so the decision logic is testable on any host.
"""
import platform, os, shutil
from pathlib import Path

MIN_VERSIONS = {"node": (18, 0), "python": (3, 9), "kicad": (7, 0)}


def os_name(system=None):
    s = system or platform.system()
    return {"Linux": "linux", "Darwin": "macos", "Windows": "windows"}.get(s, s.lower())


def chrome_candidates(system=None):
    o = os_name(system)
    if o == "linux":
        return ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
    if o == "macos":
        return ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    if o == "windows":
        return [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
    return []


def find_chrome(system=None, which=shutil.which):
    for c in chrome_candidates(system):
        if os.path.sep in c or ":" in c:        # an absolute path candidate
            if Path(c).exists():
                return c
        else:                                    # a PATH command name
            p = which(c)
            if p:
                return p
    return None


def default_profile_dir(system=None, home=None):
    home = Path(home or Path.home())
    o = os_name(system)
    if o == "linux":
        return home / ".config" / "google-chrome"
    if o == "macos":
        return home / "Library" / "Application Support" / "Google" / "Chrome"
    if o == "windows":
        return home / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
    return home


def clone_profile_dir(home=None):
    return Path(home or Path.home()) / ".cache" / "axon-eda-chrome"


def lock_files():
    # Linux/macOS singleton locks; harmless to attempt on Windows (they won't exist).
    return ["SingletonLock", "SingletonCookie", "SingletonSocket"]
