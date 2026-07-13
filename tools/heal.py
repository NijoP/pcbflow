#!/usr/bin/env python3
"""
axon heal — the self-healing engine.

Runs an automation step; if it fails, it DIAGNOSES the fault, attempts the mapped
RECOVERY, and either recovers-and-retries or ESCALATES with a plain-English
explanation (the What / Why / Tried / Result / Action message). This is the loop
from reliability/SELF_HEALING.md, wiring together diagnose + recover + the recovery
strategies. Pure Python 3 standard library.

Usage in an automation step:

    from axon_log import PhaseLogger
    from heal import heal
    import recovery

    log = PhaseLogger("door-sensor", "04-schematic-generation")
    result = heal(log, "wire block U3", action=wire_u3,
                  recoveries={"session": recovery.session_reauth(reload, signed_in)})
    if not result["ok"]:
        print(result["human"])   # the engineer sees plain English, never a stack trace
"""
from diagnose import classify

# fault class -> recovery strategy name (see recovery.py). Faults not listed have no
# automatic recovery (they need a human, e.g. KI-5 install KiCad, GIT-AUTH sign in);
# KI-6 is PREVENTED by drc.sh, so it needs no runtime recovery here.
STRATEGY = {
    "EDA-1/2": "session",
    "EDA-3": "session",
    "EDA-5": "backoff",
    "EDA-6": "backoff",
    "EDA-7": "renderer",
    "BR-2": "chrome_attach",
    "BR-3": "session",
    "BR-4": "chrome_singleton",
    "BR-5": "edit_lock",
    "KI-2": "kicad_import",
}


def humanize(diagnosis, tried, recovered, action_needed=None):
    """The five-part engineer-facing message (SELF_HEALING.md §5)."""
    parts = [
        f"• What happened: {diagnosis['title']}.",
        f"• Why: {diagnosis['why']}",
        f"• What I tried: {tried}.",
        f"• Result: {'Recovered automatically — nothing lost.' if recovered else 'Could not fix it automatically.'}",
    ]
    if not recovered:
        parts.append(f"• What you need to do: {action_needed or diagnosis['human_message']}")
    return "\n".join(parts)


def heal(logger, step, action, recoveries=None, idempotent=True):
    """Run action(); on failure, diagnose → attempt the mapped recovery → retry (if
    idempotent) → recover or escalate.

    action:      callable doing the work (raises on failure).
    recoveries:  dict {strategy_name: callable()->bool} — the fixes available here.
    idempotent:  if False, the action is NOT auto-re-run after a fix (a live write
                 must not double-apply); instead the engineer is asked to say 'retry'.

    Returns {"ok": True, "v": ...} | {"ok": True, "v": ..., "recovered": True, "human": ...}
         |  {"ok": False, "err": ..., "human": ..., "diagnosis": ...}.
    Always logs (ok / recovered / escalated).
    """
    recoveries = recoveries or {}
    try:
        value = action()
        logger.ok(step)
        return {"ok": True, "v": value}
    except Exception as exc:
        diag = classify(str(exc))
        strat = STRATEGY.get(diag["class"])
        tried = "no automatic recovery is available for this fault"
        fixed = False

        if strat and strat in recoveries:
            tried = f"ran the '{strat}' recovery"
            try:
                fixed = bool(recoveries[strat]())
            except Exception:
                fixed = False

        if fixed and not idempotent:
            human = humanize(diag, tried + " (the environment is fixed)", False,
                             "The problem is fixed — say 'retry' to safely re-run this step.")
            logger.escalated(step, diag["class"], str(exc), human)
            return {"ok": False, "err": str(exc), "human": human,
                    "diagnosis": diag, "env_fixed": True}

        if fixed and idempotent:
            try:
                value = action()
                human = humanize(diag, tried, True)
                logger.recovered(step, diag["class"], tried, 2, human)
                return {"ok": True, "v": value, "recovered": True, "human": human}
            except Exception:
                pass  # recovery didn't hold → escalate below

        human = humanize(diag, tried, False)
        logger.escalated(step, diag["class"], str(exc), human)
        return {"ok": False, "err": str(exc), "human": human, "diagnosis": diag}
