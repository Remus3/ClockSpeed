# Roadmap - OPEN work only

One line per item. No narrative. Shape:

```
CS-nnn - <one line> - acceptance: <testable condition> - tier: <0|1|2>
```

Closed work lives in `docs/LEDGER.md`. Aspirational and conditional-trigger items live in
`BACKLOG.md`. Items blocked on something outside the repo live in `docs/GATED.md`. An item
is in exactly one of those four places.

**ID blocks.** IDs are permanent and never reused. `CS-0nn` is the phase 0 scaffold block
and is closed - those entries are in `docs/LEDGER.md`, not here. Open items are numbered
in the hundreds block matching their phase: `CS-1nn` phase 1, `CS-2nn` phase 2, and so on
through `CS-7nn`. Gaps are expected and are never backfilled.

**Not listed here:** phase 0, which is being completed now and closes into
`docs/LEDGER.md`. Spikes S4, S6 and S8 are also absent - they are being settled in this
session and their results land as ADRs in `docs/adr/` with the decisions recorded in
`docs/LEDGER.md`. If any of the three comes back unsettled, it is filed here as a new item
rather than left implicit.

**Do not advance past a phase whose acceptance criterion is unmet.**

---

## Phase 1 - spikes

CS-105 - S7: read the overclock power exponent from building class data instead of a constant - acceptance: the value is read from the registry and a test fails if a literal exponent appears anywhere in the power path - tier: 1 - NOTE: the data half landed in phase 2; `clockspeed/data/registry.py` reads `mPowerConsumptionExponent` per building class and models all 62 exponent-bearing entries. The remaining half is the guard, which cannot exist until `clockspeed/solve/power.py` does, because "the power path" is the thing it asserts about. Closes with phase 3.

## Phase 2 - data layer follow-ups

CS-201 - Teach the commit gate to detect world names, world tokens and non-digit account directories - acceptance: staging a file containing a world name or a 22-char world token is BLOCKED end to end (stage a violation, attempt a real commit, assert HEAD is unchanged), and account-directory discovery no longer filters on `.isdigit()` - tier: 1 - NOTE: `tools/precommit_gate.py` is FROZEN. Route through an adjudicator and record the grant in `docs/LEDGER.md` before editing. This gap is why world names and tokens reached HEAD unblocked.
CS-202 - Complete the `str(exc)` sibling sweep outside `tools/drift_guard.py` - acceptance: no `f"...{exc}"` interpolation of an exception remains in `scripts/verify_env.py` or `tools/precommit_gate.py`, and a test asserts the rendered message omits the filename - tier: 1 - NOTE: `scripts/verify_env.py:329` is a one-line fix; the `precommit_gate.py` instance is frozen and needs the CS-201 grant.
CS-203 - Give `tools/facts_probe.py` a test module - acceptance: a test asserts the default output carries no account id, no world name and no home path, and that the `--unredacted` opt-in is the only path that emits them - tier: 1 - NOTE: the probe was migrated onto `clockspeed/data/locate.py` and its schema bumped to 2 during phase 2 with no automated coverage; it is currently verified only by execution.

## Phase 3 - solver core

CS-300 - Phase 3 gate: pillar 1 exact ratio solve, then pillar 2 behind the pluggable optimizer interface - acceptance: hand-verified ratios for a set of known chains including one with a byproduct loop, an assertion proving no floating-point arithmetic anywhere in the solve path, and the optimizer swappable by config with identical results on a degenerate case - tier: 2

## Phase 4 - save reader

CS-400 - Phase 4 gate: header, chunks, usmap, objects and world model, with unknown actor classes skipped and logged - acceptance: a real world parses, a corrupted save and a truncated save each produce a clean error rather than a crash, and a test proves the save directory is never opened for write - tier: 2
CS-401 - Assert world-token stability across a save and reload cycle, and tolerate an unseen token - acceptance: a test asserts the same token across two saves of one world, and the ledger treats an unknown token as a new world rather than failing - tier: 2
CS-402 - Version-dispatch the save parser across the save versions present in the operator's own library - acceptance: both save versions parse through the same entry point and a test covers each, with header version handled independently of save version - tier: 2

## Phase 5 - advisor and audit

CS-500 - Phase 5 gate: trace engine first, then rules, cards, the ledger, then pillars 3 and 4 - acceptance: every rule has a synthetic-fixture test, the unmet-precondition invariant holds under a property test over generated world states, a card id is stable across a save reload, and tier 3 is generated from the trace and cannot be authored by hand - tier: 2

## Phase 6 - surfaces

CS-600 - Phase 6 gate: dashboard first, then the companion - acceptance: the 5-phase visual audit from CONVENTIONS section 13.2 passes before the page is committed - tier: 2
CS-601 - Local HTTPS dashboard and JSON API on the allocated base port - acceptance: every endpoint listed in BOOTSTRAP section 7.1 responds, and the self-signed certificate is generated by a tracked script into a gitignored location - tier: 2
CS-602 - Electron companion window loading the local dashboard - acceptance: frameless, optionally always-on-top, resizable, remembers position and size, and handles the self-signed certificate without disabling certificate validation wholesale - tier: 2

## Phase 7 - public flip gate

CS-700 - Phase 7 gate: the tier-3 flip checklist from CONVENTIONS section 17 - acceptance: every item on that checklist passes, including the full-history secret scan, the PII scan across tracked files and commit messages, the third-party license audit, and the clean-checkout probe on a machine that has never seen the project - tier: 2
