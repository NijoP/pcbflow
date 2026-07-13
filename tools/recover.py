#!/usr/bin/env python3
"""
pcbflow recover — retry with backoff + idempotency guard, wired to the diagnoser.

Turns transient failures (rate limits, timeouts, server hiccups) into automatic
recoveries, while refusing to blindly re-run a non-idempotent live write. Pure
Python 3 standard library.

Design: reliability/SELF_HEALING.md §3 (retry rules).
"""
import time
from diagnose import classify


def retry(fn, attempts=3, backoff=(1, 4, 16), retry_on=None, idempotent=True, sleep=time.sleep):
    """Run fn() with retries.

    - retry_on(exc) -> bool decides retryability; default asks the diagnoser.
    - idempotent=False means a failure is NOT retried (a failed live write must not
      be blindly re-applied — one failure shouldn't become two problems).
    - backoff: seconds to wait between attempts (last value repeats).
    Returns {"ok": True, "v": ..., "attempts": n}
         or {"ok": False, "err": ..., "attempts": n, "diagnosis": {...}}.
    """
    if retry_on is None:
        retry_on = lambda e: classify(str(e)).get("retryable", False)
    last = None
    tries = 0
    for i in range(attempts):
        tries = i + 1
        try:
            return {"ok": True, "v": fn(), "attempts": tries}
        except Exception as e:
            last = e
            can_retry = idempotent and retry_on(e) and i < attempts - 1
            if not can_retry:
                break
            sleep(backoff[min(i, len(backoff) - 1)])
    return {"ok": False, "err": str(last), "attempts": tries, "diagnosis": classify(str(last))}


def safe_run(logger, step, fn, error_class="SC-1", **retry_kwargs):
    """retry() + structured logging: logs 'recovered' on eventual success after a
    retry, 'escalated' (with the human-friendly message) on final failure."""
    r = retry(fn, **retry_kwargs)
    if r["ok"]:
        if r.get("attempts", 1) > 1:
            logger.recovered(step, error_class, "retry with backoff", r["attempts"],
                             "Recovered automatically after a transient error.")
        else:
            logger.ok(step)
    else:
        d = r.get("diagnosis") or classify(r["err"])
        logger.escalated(step, d["class"], r["err"], d["human_message"])
    return r
