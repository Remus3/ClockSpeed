# Clockspeed - Architecture

**Owner file for:** the module map, the data flow, the seams, and which package owns
what.

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
  audit/          pillar 3 whole-world audit
  progress/       pillar 4 milestone routing
  advisor/        pillar 5
    rules/
    trace.py
    cards.py
    ledger.py
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
| `clockspeed/save/objects.py` | Actor and component deserialization against the property mapping. Owns the "unknown class is logged and skipped, never fatal" rule. |
| `clockspeed/save/world.py` | The world-state model. This is the only save-layer type any higher layer is allowed to hold. |
| `clockspeed/solve/exact.py` | Exact rational arithmetic primitives. Owns the invariant that no float enters the solve path. |
| `clockspeed/solve/ratio.py` | Pillar 1 target-rate solve, both directions, including recipe loops and byproduct feedback. |
| `clockspeed/solve/optimize.py` | Pillar 2 objective handling and the `OptimizerBackend` interface. Owns the interface, not any particular solver. |
| `clockspeed/solve/backends/` | Pluggable optimizer implementations behind that interface. Swapping one changes no caller. |
| `clockspeed/solve/power.py` | Power and clock mathematics, including the overclock scaling exponent taken from data rather than hardcoded. |
| `clockspeed/audit/` | Pillar 3: the diff between what is built and what should be, and the attribution of each finding to its binding constraint. |
| `clockspeed/progress/` | Pillar 4: milestone and phase routing against a freely selected target, emitting a dependency-ordered plan. |
| `clockspeed/advisor/rules/` | One module per rule family. Each rule declares its inputs and its required unlocks as data. |
| `clockspeed/advisor/trace.py` | The rule execution trace - the single record of what was read, what fired, what was computed and what was rejected. |
| `clockspeed/advisor/cards.py` | Card identity and the three rendering tiers, all projected from the trace. |
| `clockspeed/advisor/ledger.py` | Per-world card state and the global per-rule mute, written atomically, schema-versioned. |
| `clockspeed/surface/server.py` | The local HTTPS listener and static serving. Port allocation is recorded in `config/ports.json`; see `docs/OPERATIONS.md`. |
| `clockspeed/surface/api/` | JSON endpoints. Serialization only - no computation. |
| `clockspeed/surface/web/` | Dashboard assets. |
| `shell/` | The Electron companion window: frameless, resizable, remembers position and size, handles the self-signed certificate without disabling validation. Later, the in-game overlay is a flagged mode of this same shell. |
| `tools/` | Gates, guards, sync and probes. Not importable by `clockspeed/`. |
| `scripts/` | One-shot operator entry points: hook installation and environment verification. |
| `data/` (repo root) | Generated artifacts only. Gitignored. Nothing here is authored and nothing here is tracked. |

---

## 2. Data flow

Two independent ingest lanes converge at the advisor. Neither lane ever writes to its
source.

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
                            solve/ (registry only)   audit/, progress/ (registry + world)
                                                          |
                                                          v
                            advisor/rules -> advisor/trace.py -> advisor/cards.py
                                                          |
                                        advisor/ledger.py (card state, mutes)
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
- `advisor/` never reads the raw docs file. It takes the normalized registry and the
  world model.
- `surface/` never computes. It serializes what the layers below produced. A number that
  first exists in `surface/` is a number with no trace behind it.
- `audit/` and `progress/` consume the world model and the registry, never save bytes.
- `tools/` is never imported by `clockspeed/`. Gates depend on the product; the product
  never depends on the gates.

**A layer that reaches past its neighbor is a design bug.**

### 3.1 Why this is enforceable and not merely aspirational

The seam is stated as a model, and layering stated as models reduces to an allowed-import
matrix. That makes every one of the rules above mechanically checkable:

1. **Import direction is testable.** A test walks the import graph of `clockspeed/` and
   asserts each package imports only from its permitted set. A reach-past shows up as a
   failing test at the moment it is introduced, not at review time.
2. **The model is the contract.** Because each seam has a named type - the registry, the
   world model, the trace, the card - a layer cannot accidentally depend on a
   representation detail of the layer two below it. To cheat, it must import something it
   is not allowed to import, which is case 1.
3. **The rule suite runs with no game install and no save present.** `advisor/` and
   `solve/` are tested entirely against small synthetic fixtures. A hidden dependency on
   real save bytes or a real install fails immediately in that environment, and in CI.
4. **`surface/` computing nothing is checkable by the same test suite**, because any
   computation it wanted to do would require importing `solve/` internals rather than
   calling a produced result.

The payoff is direct: the highest-risk change in the project - a game patch - lands
entirely inside `data/`, and the seam is what confines it there.

---

## 4. The five pillars and their packages

All five ship. Pillars 1 and 2 are the engine, pillar 3 is the world reader's consumer,
pillars 4 and 5 are what the operator actually looks at.

### Pillar 1 - Target-rate ratio solve

Given a requested rate of an item, emit the complete production tree: every intermediate,
exact building counts, exact clock speeds, byproduct handling, raw input totals, total
power draw and total build cost. It solves both directions - "I want this much of X" and
"I have this raw input, what is the best output". Arithmetic is exact rational end to end
because floating-point drift in a ratio calculator is a correctness bug and not a
rounding nuisance. Recipe loops and byproducts that feed back into their own chain are
the hard case and are handled explicitly rather than assumed away.
**Implemented by:** `solve/exact.py`, `solve/ratio.py`, `solve/power.py`, over
`data/registry.py`.

### Pillar 2 - Alt-recipe selection under constraints

Given an objective and the set of genuinely unlocked recipes, choose the recipe set that
optimizes it. Objectives are individually selectable and combinable with weights:
minimize raw resource consumption, minimize power draw, minimize building count, minimize
footprint proxy, maximize sink points per unit of raw input. The implementation starts
dependency-free - exact ratio solve plus a branch-and-bound or weighted-greedy search -
behind a pluggable optimizer interface, and constrains by what is unlocked rather than by
what exists in the data. An external linear or integer programming library is a later and
gated decision that must slot behind the existing interface without changing a caller.
**Implemented by:** `solve/optimize.py` (the interface) and `solve/backends/` (the
implementations).

### Pillar 3 - Whole-world audit from the save

Diff what is actually built against what should be, and name the cause rather than the
symptom: idle or starved machines together with the upstream cause of the starvation,
overclock waste where a machine is clocked above what its supply can feed, belt and pipe
saturation with the binding segment identified, power headroom and brownout risk and fuel
chain sizing against real consumption, resource nodes claimed but under-extracted along
with extractor tier mismatches, and sink-point throughput actually achieved.
**Implemented by:** `audit/`, consuming `save/world.py` and `data/registry.py`, using
`solve/` for the arithmetic.

### Pillar 4 - Milestone and progression routing

Point the system at the current milestone or at any future milestone or phase target and
get what must be added, upgraded, redesigned or torn down to reach it from the current
world state. The target is a free selector and not a fixed pointer at "next"; selecting a
target several tiers out and getting a redesign plan is a required capability. Output is
a dependency-ordered plan rather than an unordered list of gaps, and it distinguishes
"you need more of this" from "you need to replace this" - the second is the expensive one
and is called out as such.
**Implemented by:** `progress/`, consuming `save/world.py` and `data/registry.py`, using
`solve/`.

### Pillar 5 - The advisor

The synthesizing layer that everything above feeds. It runs data-driven modular rules
over the registry and the world model, records one execution trace per firing, and emits
cards. Rules declare their inputs and their required unlocks explicitly, so no rule can
recommend an action whose preconditions are unmet - an invariant carried by a property
test over generated world states, not by code review. A game patch that changes recipes,
buildings or milestones is absorbed by re-running the extractor and updating the version
pin; if a patch forces a rule edit, that rule encoded a fact it should have read from
data.
**Implemented by:** `advisor/rules/`, `advisor/trace.py`, `advisor/cards.py`,
`advisor/ledger.py`, surfaced through `surface/`.

---

## 5. The advice card contract

Every piece of advice is a card with a stable identity and three rendering tiers.

| Tier | Content | Default |
|---|---|---|
| 1 - Headline | One line. Imperative. What to do. No reasoning. | Always shown |
| 2 - Reason | One line. The binding constraint or trigger. | Shown inline |
| 3 - Derivation | The complete chain: every input read with its source, every rule that fired, every number computed, every alternative considered and why each was rejected. | On expand only |

Tier 3 is a **learning surface, not a debug dump**. It is written to be read by a human
who wants to understand the how and the why well enough to reason it out themselves next
time.

### 5.1 The critical constraint: one trace, three projections

**All three tiers are projections of ONE rule execution trace. They are never three
hand-written renderings.**

This is a structural constraint, not a preference:

- The trace is produced by `advisor/trace.py` from each rule's declared inputs and its
  recorded decisions. `advisor/cards.py` projects tier 1, tier 2 and tier 3 out of that
  single object.
- Because there is one source, the tiers **cannot drift from each other**. A headline
  that disagrees with its own derivation is not a bug that can occur; it is a state the
  data model cannot represent.
- It is also why the advice path needs no language model. The derivation already exists
  as structured fact by the time anything is rendered - there is nothing left to
  summarize or explain.
- A rule that reads an input it did not declare produces an incomplete trace and
  therefore a lying tier 3. That is a bug and a test catches it.

The failure mode this forbids is specific: hand-authoring a nice-sounding tier 3 next to
a separately computed tier 1. That reads well on the day it is written and is wrong
forever after.

---

## 6. Card identity and persistence

### 6.1 Identity

**Card ID is a deterministic hash of `(rule_id, subject_key, target_milestone)`.**

- Recomputing on a changed save must produce the SAME id for the same underlying advice.
  If it does not, every piece of persisted state is lost on every reload, which makes
  dismiss, snooze and pin worthless.
- `subject_key` is the stable identity of the thing the advice is about - a node, a
  factory region, a recipe, a milestone. **It must not encode anything volatile.** A save
  filename, a timestamp, an array index or an in-memory object id are all disqualified.
- `target_milestone` is part of the identity because the same rule about the same subject
  is genuinely different advice under a different target.

### 6.2 Two persistence layers, both durable across sessions, reloads and patches

**Layer 1 - per-world ledger.** Keyed to the world token carried in the save header,
**never to a save filename** - filenames change on every save and autosaves rotate. Card
states are `new`, `accepted`, `dismissed`, `snoozed(until)`, `pinned` and `completed`.
`completed` is set automatically when the world state satisfies the advice, and that
transition is itself worth surfacing to the operator. The ledger tolerates a world token
it has never seen by treating it as a new world rather than failing.

**Layer 2 - global per-rule mute.** Any rule type can be silenced across all worlds,
permanently, from the card itself. This is the "stop telling me about power, I know"
control, and it is deliberately separate from per-world state: muting a rule everywhere
and dismissing one card are different intents.

Both layers live in a plain JSON file in the gitignored project data directory, written
atomically, carrying a schema version field from the first write. Owned by
`advisor/ledger.py`. Note that this is card state and is unrelated to `docs/LEDGER.md`,
which is the project's completion record.

---

## 7. Cross-references

- Commands, bootstrap order, runbooks, ports: `docs/OPERATIONS.md`
- Decisions and their fences: `docs/adr/README.md`
- Items blocked outside the repo: `docs/GATED.md`
- Completion records: `docs/LEDGER.md`
