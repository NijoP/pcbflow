# Principles — The Source of Every Design Choice

The eight first principles Tracewright is built on. Full essay:
[`../docs/00_PHILOSOPHY.md`](../docs/00_PHILOSOPHY.md).

1. **Knowledge is the source; geometry is the build artifact.** Version and protect
   the knowledge; regenerate the geometry. Never couple status to artifact paths.
2. **Place nothing over wrong.** Never build stage N+1 on an unverified stage N.
3. **Verify against reality, never the tool's own model.** Re-read after every
   mutation; run DRC with the correct ruleset in the correct tool.
4. **Autonomy is bounded by reversibility, not difficulty.** Replayable → autonomous;
   live write → go-ahead; irreversible → human.
5. **Two personas, always on, in tension.** Senior software engineer + senior
   hardware engineer; the HW persona vetoes the electrical unknown.
6. **The verdict is the unit of progress.** `PASS / CONDITIONAL / FAIL`, dated,
   falsifiable — not "done."
7. **The hard wall is real; plan for it.** Automate to the tool's limit, then hand
   the human a precise map for the last mile.
8. **Cheap, honest, dated memory beats a perfect one.** Externalized, typed, self-
   invalidating knowledge that compounds across projects.

The through-line: **separate the durable thing from the disposable thing, and gate
the transition between them with a cheap, honest check.**
