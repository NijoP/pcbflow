# 16 · Version 2 — The Ideal AI-Native Electronics Workspace

> *If I rebuilt this entire workspace from zero today, with everything the origin
> project taught me and no obligation to backward-compatibility — this is what I'd
> build.*

The origin project arrived at the right ideas by walking into every wall. V1 (this
framework) is those ideas cleaned up. V2 is what you get when the ideas come *first*
and the tooling is designed around them from the start.

---

## The core inversion

V1 still thinks in files that happen to be well-organized. **V2 makes the knowledge
layer a real, queryable model and treats geometry as a pure build target of it.**

```
V1:  well-organized docs  →  scripts read them  →  geometry (manually verified)
V2:  a typed BOARD MODEL   →  `axon build`       →  geometry (verified by construction)
                └── one source object: parts, nets, rules, constraints, decisions
```

In V2 there is **one canonical board model** — a typed, validated object (think a
schema-checked YAML/JSON with a real type system behind it), not two markdown files
you keep in sync by hand. The `build_sheet` and `net_connection` become *views* of
that model, generated, never hand-edited into disagreement. The whole class of
"the two docs drifted" bugs disappears because there is one source.

---

## What I would REMOVE

- **The dual hand-maintained source docs.** Replaced by one model + generated views
  (kills net-name drift by construction).
- **Hard-coded artifact paths anywhere in governance.** The status ledger becomes a
  *derived* view of verified state, not a hand-written table that can lie. If the
  board file isn't committed, the status literally cannot say "shipped."
- **Copy-pasted engines.** The section generator, CDP driver, netlist reconstructor,
  placer, and audit suite become one installed package, versioned, tested — not
  duplicated per board.
- **Ad-hoc verdicts in prose.** Verdicts become structured records the tooling emits
  and gates on, not sentences a human greps for.
- **The EasyEDA-only assumption.** The pour/route API wall is an EasyEDA fact, not a
  law of nature. V2 is backend-agnostic from line one (see below).

---

## What I would SIMPLIFY

- **One board model, three phases of verification, one gate type.** The methodology
  stays 10 phases, but every gate emits the *same* structured verdict object, so the
  governance layer is uniform.
- **Memory becomes the model's changelog.** Instead of 40 loosely-linked memory
  files, decisions attach to the board model as typed, dated, authored records with
  rationale. The `[[wikilink]]` graph becomes real references between model nodes.
- **The learning KB feeds the type system.** A validated heuristic with an
  auto-checkable assertion becomes a *lint rule* on the board model. "0.5 oz inner
  plane as sole >5 A conductor" isn't a doc you hope someone read — it's a check that
  fails the build.

---

## What I would AUTOMATE (that V1 leaves manual)

- **The source-of-truth lint** — net parity, single-tie ground, decoupling
  completeness, IPC-2221 margins — as build-time checks, not review-time hopes.
- **Backend-appropriate routing.** On a KiCad backend, pours/zones/stitching are
  scriptable → automate phase 8 up to the fine-pitch tail. The Tier-4 wall moves
  from "all of routing" to "just the escapes."
- **Board recompile.** `axon build` regenerates schematic + placement + routing plan
  from the model. A lost board is a rebuild, not a catastrophe (directly fixes F2).
- **DRC-by-construction.** Because the model carries the ruleset and the widths, the
  generation layer emits geometry that already respects them — DRC becomes
  confirmation, not discovery.

---

## The V2 architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  THE BOARD MODEL   (one typed, validated, versioned source object)   │
│    parts · nets · net-classes · rules · constraints · decisions·log  │
│    every heuristic from the KG is a LINT RULE over this model         │
└─────────────────────────────────────────────────────────────────────┘
        │ views                    │ build                 ▲ verify-by-construction
        ▼                          ▼                        │
   build_sheet / net_connection    BACKEND ADAPTER          STRUCTURED VERDICTS
   (generated, read-only)          (EasyEDA | KiCad | …)    (the ledger is derived)
                                        │
                                        ▼
                                   GEOMETRY (regenerable build target)
```

Four properties fall out for free:

1. **No drift** — one source, generated views.
2. **No lying ledger** — status is derived from verified state + git presence.
3. **No copy-paste** — one installed engine package.
4. **No lost boards** — `axon build` recompiles from the model.

---

## Backend-agnostic from line one

The single biggest V1 constraint is that its most-costly wall (interactive routing)
is an *EasyEDA* limitation, not a universal one. V2 defines a thin **backend adapter
interface** — `place`, `route`, `pour`, `drc`, `export` — and implements it per tool:

- **EasyEDA adapter** — scriptable schematic + CDP readback; routing/pours emit a
  *plan* (the P4 pattern) because the API can't.
- **KiCad adapter** — `pcbnew` + `kicad-cli`; pours/zones/stitching are scriptable →
  routing is automatable to the fine-pitch tail.

The knowledge layer never changes. You choose the backend by which wall you're
willing to live with, and the framework tells you exactly where that backend's
Tier-4 boundary is.

---

## What stays exactly the same

The *ideas* are already right — V2 only makes them structural instead of
disciplinary:

- Knowledge is the source; geometry is the artifact. (Now enforced by the model.)
- Place nothing over wrong. (Now a failing build, not a violated habit.)
- Verify against reality. (Now verify-by-construction + confirmation DRC.)
- Autonomy by reversibility. (Unchanged — it's a policy, and it's correct.)
- The verdict is the unit of progress. (Now a typed object the tooling emits.)
- Two personas in tension. (Unchanged — it's how the AI should think.)

V2 isn't a different philosophy. It's the *same* philosophy with the discipline
compiled into the tooling, so the next project can't make the origin project's
mistakes even if it tries. That is the whole point of writing the manual: **encode
the lessons so hard that walking into the wall stops being possible.**
