# Clockspeed - Architecture

**Owner file for:** the module map, the tooling map, the data flow, the seams, and which
package owns what.

**This file never contains:** commands, restart procedure or runbooks (those are
`docs/OPERATIONS.md`), decisions and their fences (those are `docs/adr/`), or any
measured number (counts, sizes, versions, port state - each of those has exactly one
machine-checked source and is cited, not restated).

---

## 1. Package topology

Paths are relative to the repo root.

```
clockspeed/
  data/           game data extraction and normalization
    locate.py
    docs_extract.py
    registry.py
    version.py
  save/           save file reading
    header.py
    chunks.py
    usmap.py
    objects.py
    world.py
  solve/          the deterministic engine
    exact.py
    ratio.py
    optimize.py
    backends/
    power.py
  audit/          pillar 3 whole-world audit - PLACEMENT AND INVENTORY ONLY
  progress/       pillar 4 - milestone and phase requirement models, no router yet
  advisor/        pillar 5 - trace, cards, ledger and the D4 power and fuel rule families
    trace.py
    cards.py
    ledger.py
    rules/
  surface/
    server.py
    api/
    web/
shell/            Electron companion window
tests/
tools/            gates, guards, sync, probes
scripts/          install_hooks.py, verify_env.py
docs/
memory/
data/             generated artifacts - GITIGNORED
```

### 1.1 What each module owns

| Module | Owns |
|---|---|
| `clockspeed/data/locate.py` | Auto-detection of the game install, the save root and the account directory - every one of them discovered at runtime, never hardcoded, and overridable by config. |
| `clockspeed/data/docs_extract.py` | Reading the English locale docs file out of the install once, sniffing its encoding, and emitting the normalized registry artifact. Nothing else in the system reads that file. |
| `clockspeed/data/registry.py` | The normalized item, recipe, building and milestone model - the single in-memory shape every consumer above the data layer sees. |
| `clockspeed/data/version.py` | The tracked build-string pin and content hash, patch detection, and the drift guard's data-side check. |
| `clockspeed/save/workdir.py` | Copying a save out to a work directory before anything parses it, and the lifetime of that copy. **This is the only module in the package with a write.** That is a deliberate design choice, not an accident of where the code landed: confining the single write to one named module turns "no other save module can write" into a STATIC, machine-checkable assertion rather than a rule reviewers have to remember. |
| `clockspeed/save/header.py` | Save header parse: the version fields, the string block, and the world token. Owns redaction: **every header string is redacted by default**, because the string ORDER is version dependent and a redactor targeting a named field is defeated by a reordered one. See `docs/adr/0007`. |
| `clockspeed/save/chunks.py` | Decompression and the chunk walk over the save body after the header. |
| `clockspeed/save/usmap.py` | Loading and caching the parsed `FactoryGame.usmap` property mapping from the install. |
| `clockspeed/save/objects.py` | Actor and component deserialization, and the property payload grammar. Owns the "unknown class is logged and skipped, never fatal" rule. The payload is tagged serialization, so this module decodes from the save's own bytes rather than from the property mapping; the mapping is an oracle and a class-name resolver. That module owns the measurement. |
| `clockspeed/save/world.py` | The world-state model, and the eager property decode that fills it. This is the only save-layer type any higher layer is allowed to hold. The body is walked TWICE inside one stage: once for the record table, then once more to decode every record's properties into published values keyed by RECORD INDEX and never by a body offset, so following one needs nothing this layer withheld. The decode is EAGER because a lazy entry would keep the decompressed body reachable for as long as any consumer held the model, and dropping that buffer at the end of the walk is the bound `tests/save/test_world.py::test_no_published_world_type_annotates_a_carrier_field` grades; the end-to-end witness is `tests/save/test_world.py::test_a_synthetic_world_publishes_one_decoded_property_value_end_to_end`. What the second pass costs is measured once, in `docs/LEDGER.md` under the CS-961 MEASUREMENT RECORD, and no figure is restated here. That pointer named a live item-notes leaf until CS-961 closed and its section left the family; the ledger entry is the record a closed item keeps. |
| `clockspeed/solve/exact.py` | Exact rational arithmetic primitives. Owns the invariant that no float enters the solve path. |
| `clockspeed/solve/ratio.py` | Pillar 1 target-rate solve, both directions, including recipe loops and byproduct feedback. |
| `clockspeed/solve/optimize.py` | Pillar 2 objective handling and the `OptimizerBackend` interface. Owns the interface, not any particular solver. |
| `clockspeed/solve/backends/` | Pluggable optimizer implementations behind that interface. Swapping one changes no caller. |
| `clockspeed/solve/power.py` | Power and clock mathematics, including the overclock scaling exponent taken from data rather than hardcoded. |
| `clockspeed/audit/` | TWO MODULES, AND THE PILLAR ITSELF IS STILL UNBUILT. `clockspeed/audit/placement.py` turns one `WorldModel` into node and built placements with exact decimal-string coordinates, per-class counts and world bounds; `clockspeed/audit/inventory.py` aggregates container contents into per-item totals and carries its own denominators. Both are what the map surface consumes, and neither is the diff-against-intent the pillar is specified as in `BOOTSTRAP.md` section 4. |
| `clockspeed/progress/` | MODELS ONLY, AND THE PILLAR ITSELF IS STILL UNBUILT. `clockspeed/progress/milestones.py` turns the shipped schematic entries and one `UnlockState` into per-milestone costs, pricing each required amount against a named exact budget held as a `Fraction`; `clockspeed/progress/phases.py` turns one phase cost table into distinct per-item requirements, and answers null rather than zero for a phase the table does not name. Both PRICE a target; neither ROUTES to it, which is what the pillar is specified as in `BOOTSTRAP.md` section 4. |
| `clockspeed/audit/balance.py` | The clocked power draw: `clocked_draw_of` prices each machine at its own clock - exact where the power law allows, otherwise an exact named bracket - and names a gap for an unread clock rather than pricing it at the default. |
| `clockspeed/advisor/trace.py` | The rule execution trace: declared inputs, the unlock gate, exact reads, and the one engine-held record every explain tier projects from. A faulting rule becomes a `rule-error` step, never a crash. |
| `clockspeed/advisor/cards.py` | The advice card: a sha256 identity over rule, subject and target, and three read-only tiers projected from one trace. |
| `clockspeed/advisor/ledger.py` | The per-world ledger, keyed by a digest of the world token, and the global per-rule mute store - two atomically written files. |
| `clockspeed/advisor/rules/` | One module per rule family, each listed by hand in `clockspeed/advisor/rules/__init__.py::_FAMILIES`. The D4 families ship: power in `clockspeed/advisor/rules/power.py` and fuel in `clockspeed/advisor/rules/fuel.py`. A rule reads only the inputs it declares, handed to it by the trace engine, and opens no file. D1 to D3 have no rule yet; what they will own is specified in `BOOTSTRAP.md` sections 4 and 5. |
| `clockspeed/surface/server.py` | The local HTTPS listener and static serving. Port allocation is recorded in `config/ports.json`; see `docs/OPERATIONS.md`. |
| `clockspeed/surface/api/` | JSON endpoints. Serialization only - no computation. |
| `clockspeed/surface/web/` | Dashboard assets. |
| `shell/` | The Electron companion window: frameless, resizable, remembers position and size, handles the self-signed certificate without disabling validation. Later, the in-game overlay is a flagged mode of this same shell. |
| `tools/` | Gates, guards, sync and probes. Not importable by `clockspeed/`. |
| `scripts/` | One-shot operator entry points: hook installation and environment verification. |
| `data/` (repo root) | Generated artifacts only. Gitignored. Nothing here is authored and nothing here is tracked. |

---

## 2. Data flow

Two independent ingest lanes. They are designed to converge at the advisor and today
converge at the surface, because pillars 3, 4 and 5 are not built. Neither lane ever
writes to its source.

```
game install (read-only)
    -> data/locate.py        find it
    -> data/docs_extract.py  parse once
    -> data/registry.py      normalized registry  --------+
    -> data/version.py       tracked pin + hash           |
                                                          |
save file (read-only at its source)                       |
    -> save/workdir.py       copy out first - THE ONLY    |
                             WRITE IN THE PACKAGE         |
    -> save/header.py        header + world token         |
    -> save/chunks.py        body framing                 |
    -> save/usmap.py         property mapping             |
    -> save/objects.py       actors and components        |
    -> save/world.py         world model  ----------------+
                                                          |
                                                          v
                            solve/ (registry only)        |
                                                          |
                            [pillars 3, 4 and 5 - NOT     |
                             BUILT. Nothing above         |
                             save/world.py consumes       |
                             the world model yet.]        |
                                                          |
                                                          v
                                        surface/api -> surface/web, shell/
```

Two flow rules that are not negotiable:

- The save is copied to a work directory before parsing, and `save/workdir.py` owns that
  copy. The game holds handles during autosave, so parsing in place eventually meets a
  locked or half-written file. Because that module is the package's only writer, the
  never-write-to-the-save-directory invariant is checkable by import graph and by write
  surface rather than by reviewer vigilance.
- The registry is built once into the gitignored `data/` directory. Downstream code
  consumes the registry, never the raw docs file.

---

## 3. Seam discipline

**Each layer consumes only the layer below it, through a stated model.**

Concretely, and each of these is a bug when violated, not a style note:

- `solve/` never reads a save. It takes a registry and a request. It has no import path
  to `save/` and no reason to acquire one.
- `surface/` never computes. It serializes what the layers below produced. A number that
  first exists in `surface/` is a number with no trace behind it.
- `tools/` is never imported by `clockspeed/`. Gates depend on the product; the product
  never depends on the gates.

One rule on this list constrains code that does not exist yet, and is marked so rather
than stated in the present tense alongside the four above: when `advisor/`, `audit/` and
`progress/` are built, they will take the normalized registry and the world model, never
the raw docs file and never save bytes.

**A layer that reaches past its neighbor is a design bug.**

### 3.1 Why this is enforceable and not merely aspirational

The seam is stated as a model, and layering stated as models reduces to an allowed-import
matrix. That makes every one of the rules above mechanically checkable:

1. **Import direction is testable, one layer at a time.** `tests/data/test_phase2_gate.py`,
   `tests/save/test_phase4_gate.py` and `tests/solve/test_phase3_gate.py` each declare the
   permitted-import set for their own layer and assert it, so a reach-past inside `data/`,
   `save/` or `solve/` shows up as a failing test at the moment it is introduced, not at
   review time. There is no whole-package matrix: `surface/` and the three unbuilt
   packages are not graded as importers by any gate today.
2. **The model is the contract.** Because each seam has a named type - the registry, the
   world model, the trace, the card - a layer cannot accidentally depend on a
   representation detail of the layer two below it. To cheat, it must import something it
   is not allowed to import, which is case 1.
3. **The suite runs with no game install and no save present.** `solve/` is tested
   entirely against small synthetic fixtures - `tests/solve/synthetic.py`. A hidden
   dependency on real save bytes or a real install fails immediately in that environment,
   and in CI. `advisor/` is tested the same way, against synthetic worlds in `tests/advisor/`.
4. **`surface/` computing nothing is checkable by the same test suite**, because any
   computation it wanted to do would require importing `solve/` internals rather than
   calling a produced result.

The payoff is direct: the highest-risk change in the project - a game patch - lands
entirely inside `data/`, and the seam is what confines it there.

---

## 4. The five pillars and their packages

All five are in scope for v1. Pillars 1 and 2 are the engine and are built; pillar 3 is
the world reader's consumer and pillars 4 and 5 are what the operator will actually look
at, and none of those three is complete. Each section below states which it is. A section that
names an implementing module is claiming shipped code, and
`tests/test_architecture_attributions.py` reddens when a named module does not carry the
capability the sentence attributes to it.

### Pillar 1 - Target-rate ratio solve

Given a requested rate of an item, emit exact building counts, byproduct handling and raw
input totals. It solves both directions - "I want this much of X" and "I have this much of
a raw input, what rate of the named item does it buy". Arithmetic is exact rational end to
end because floating-point drift in a ratio calculator is a correctness bug and not a
rounding nuisance. Recipe loops and byproducts that feed back into their own chain are the
hard case and are handled explicitly rather than assumed away.
**Implemented by:** `solve/exact.py` and `solve/ratio.py`, over `data/registry.py`.

### Pillar 2 - Alt-recipe selection under constraints

Given an objective and the set of unlocked recipes, choose the recipe set that optimizes
it. Objectives are individually selectable and combinable with weights: minimize raw
resource consumption, minimize power draw, minimize building count. The implementation
starts dependency-free - exact ratio solve plus a weighted-greedy search - behind a
pluggable optimizer interface, and constrains by what is unlocked rather than by what
exists in the data. An external linear or integer programming library is a later and gated
decision that must slot behind the existing interface without changing a caller.
**Implemented by:** `solve/optimize.py` (the interface) and `solve/backends/` (the
implementations).

### Pillar 3 - Whole-world audit from the save

**Status:** PARTLY BUILT, AND THE PART THAT EXISTS IS NOT THE PILLAR. `audit/` now holds
`clockspeed/audit/placement.py` and `clockspeed/audit/inventory.py`, landed under CS-978 because the map surface needed a
layer that computes and `surface/` never computes. They DESCRIBE a world - where things
are, and how much of what is held. Specified in `BOOTSTRAP.md` section 4.

Intent, still unmet: diff what is actually built against what should be, and name the cause
rather than the symptom. Describing is not diffing, and nothing here compares a world to an
intent yet.

### Pillar 4 - Milestone and progression routing

**Status:** PARTLY BUILT, AND THE PART THAT EXISTS IS NOT THE PILLAR. `progress/` holds
`clockspeed/progress/milestones.py` and `clockspeed/progress/phases.py`, landed under
CS-1043. They PRICE a target and route to none. Specified in `BOOTSTRAP.md` section 4.

Intent, still unmet: a dependency-ordered plan rather than a gap list. Relocated from
`README.md` by CS-1333: the plan's steps are add, upgrade, redesign and tear down, toward the
next milestone or one several tiers out, and `/api/plan` answers 501 today and names the work
item that builds it.

### Pillar 5 - The advisor

**Status:** PARTLY BUILT. The trace engine, the card, the ledger, the composition in
`clockspeed/advisor/advise.py` and the D4 power and fuel rule families ship in `advisor/`;
D1 to D3 - node siting and claim order, onsite processing versus transport, and the milestone
gap, relocated from `README.md` by CS-1333 - have no rule yet. Specified in `BOOTSTRAP.md`
sections 4 and 5.
`clockspeed/surface/api/advice.py` serves the advice endpoints, while the audit and plan
endpoints still answer 501 - see `clockspeed/surface/api/pending.py`.

Intent: the synthesizing layer that everything above feeds, running data-driven modular
rules over the registry and the world model.

---

## 5. The advice card contract

**Status:** BUILT. `advisor/` ships the trace, the card, the ledger and the rules of the D4
power and fuel families, in `clockspeed/advisor/rules/`.
Specified in `BOOTSTRAP.md` sections 5.1, 5.2 and 5.4, which own the tier definitions,
the card identity and the rule-engine constraints.

The contract, in one line each: advice is a card with a stable identity and three rendering tiers; all three
tiers are projections of ONE rule execution trace rather than three hand-written
renderings; the card carries a per-world state and a global per-rule mute, both durable
across sessions, reloads and patches.

Nothing in this repository implements any of that. There is no card type, no trace, no
tier renderer, no identity hash and no ledger store. The three files an earlier revision
of this section named as their owners have never existed on disk, which is the defect
CS-928 records; the detail they described lives in `BOOTSTRAP.md` and is reproduced here
only when there is code to attribute it to.

---

## 6. Tooling map

The gates, guards, probes and lane drivers beside the product packages. Relocated from
`CLAUDE.md` section 2.2 under its section 4 relocate-do-not-delete rule by CS-1272; the
`tools/inbox_watch.py` row and the `.githooks/` row stay in `CLAUDE.md`, where tests and
gates cite them.

| Path | Does |
|---|---|
| `scripts/install_hooks.py` | Sets `core.hooksPath`, installs `.githooks/`. Idempotent. Fails loudly if it cannot set the path |
| `scripts/verify_env.py` | Asserts interpreter, toolchain, paths and ports. Prints found/missing, exits non-zero on a missing hard dependency |
| `tools/precommit_gate.py` | Character-set gate, secret scan, staged-line lint, syntax check |
| `tools/edit_lint_check.py` | `PostToolUse` syntax and lint check on an edited file |
| `tools/drift_guard.py` | Doc and pin drift detection |
| `tools/doc_budget.py` | File-size budget enforcement |
| `tools/facts_probe.py` | Live-state fact set. Run BY HAND from `/drift-guard` and `/sync-docs`; NOT a hook |
| `tools/memory_sync.py` | Mirrors markdown memory into the recall store, idempotent |
| `tools/provenance_stamp.py` | Stamps each new tracked file into `tools/provenance.tsv`; the manifest arm reddens any file it lacks - CS-1165 |
| `tools/dashboard_probe.py` | The SCRIPTED answer to "does the dashboard run". Launch, poll, assert a JSON key and a DOM node, one screenshot, exit code decides |
| `tools/headless-queue.md` | The `queue` lane worker's prompt. TRACKED, because a worktree is a fresh checkout and carries no gitignored file |
| `ops/loop/queue_loop.py` | The lane driver. Repeats the one-row worker AND owns every wait, so nothing can cancel a run mid-grade |
| `ops/loop/launch_queue_loop.ps1` | Starts the driver detached. Refuses over a stop sentinel and prints no banner over a no-op |

---

## 7. Cross-references

- Commands, bootstrap order, runbooks, ports: `docs/OPERATIONS.md`
- Decisions and their fences: `docs/adr/README.md`
- Items blocked outside the repo: `docs/GATED.md`
- Completion records: `docs/LEDGER.md`
