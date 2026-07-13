# Windows Setup — for Hardware Engineers on Windows

**Most hardware engineers use Windows, and PCB Flow runs on Windows.** This page
covers the small differences from the Linux/macOS instructions. Everything else in the
[handbook](README.md) applies unchanged.

## The three differences to remember

1. **Use `python` (or `py`) instead of `python3`.** Everywhere the docs say
   `python3 tools/doctor.py`, on Windows type:
   ```
   python tools\doctor.py
   ```
   (If `python` isn't found, use `py tools\doctor.py`.)
2. **Backslashes in paths** (`tools\doctor.py`) — though PowerShell also accepts `/`.
3. **Use the `.py` tools, not the `.sh` scripts.** The Bash helpers (`drc.sh`, the
   Chrome launch recipe) are Linux/macOS only. On Windows use their Python versions:
   | Instead of… | On Windows use |
   |---|---|
   | `automation/kicad/drc.sh board.kicad_pcb rules.kicad_pro` | `python tools\drc.py board.kicad_pcb rules.kicad_pro` |
   | the bash `rsync + Singleton` Chrome recipe | `python tools\launch_easyeda.py` |

## Install the tools (same as everyone)

VS Code · an AI assistant (Claude Code / Codex / Cursor / …) · EasyEDA Pro · KiCad ·
Git · Chrome · **Python 3.9+** (during install, tick **"Add Python to PATH"**) · Node.js.
See [handbook step 2](02-installing-tools.md) for links.

Then check everything at once:
```
python tools\doctor.py
```
The doctor detects Windows and tells you exactly what (if anything) to fix.

## The one Windows-specific step: the EasyEDA browser

For phases 3–9, the AI reads your **live** EasyEDA board through Chrome. On Windows:

- **Close Chrome first.** Windows locks profile files while Chrome is open, so the
  browser launcher clones a fresh copy first — close all Chrome windows, then run:
  ```
  python tools\launch_easyeda.py
  ```
  (Run `python tools\launch_easyeda.py --dry-run` first to see what it will do.)
- If it reports that some profile files were locked, **close every Chrome window and
  retry.**
- **Manual fallback (works on any OS):** you don't have to use the automated browser at
  all. You can paste the AI's generated scripts into EasyEDA yourself
  (*Settings → Extensions → Standalone Script*), and the AI guides you and verifies from
  what you paste back.

## What's fully supported on Windows

| Part | Windows |
|---|---|
| VS Code + AI assistant, all docs & handbook | ✅ |
| Phases 1–2 (feasibility, BOM) | ✅ |
| All the Python helpers (`doctor`, logging, diagnosis, retry, recovery, `drc.py`, `tidy`) | ✅ (pure Python, path-aware) |
| Phases 10–12 (KiCad routing + DRC via `drc.py`) | ✅ |
| Phases 3–9 automated EasyEDA browser readback | ✅ *by design* — validate on your machine; manual fallback always works |

## Windows troubleshooting

- **`python` is not recognized** → reinstall Python and tick "Add to PATH", or use `py`
  instead of `python`.
- **A `.sh` script won't run** → use the `.py` version (see the table above).
- **The browser launcher can't copy the profile** → close all Chrome windows and retry;
  Windows locks files that Chrome has open.
- **Anything else** → tell the AI *"something went wrong on Windows — read the log and
  fix it."* It reads the log, explains in plain English, and recovers where it can.

---
◀ [Handbook home](README.md) · related: [02 — Installing the tools](02-installing-tools.md)
