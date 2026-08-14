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

## Phase 2 - data layer follow-ups

CS-204 - Redact the diagnostic LABEL channel in `tools/precommit_gate.py` and `tools/edit_lint_check.py` - acceptance: a `--files` run over a path outside the repository emits no home path in ANY of the three output channels - diagnostics, `report.checked`, `report.skipped` - and a test asserts it on both tools - tier: 1 - NEEDS ITS OWN FROZEN-FILE GRANT: the CS-201/CS-202 grant was ruled NOT to extend, because `label` is verdict-bearing at six call sites (it feeds `check_path`, becomes `SyntaxError.filename` via `compile`, builds a staging-copy filename, keys the ruff output mapping, and builds a `git show :<label>` argument), so this is a different risk class from CS-202's text-only change. The adjudicator that found it RECUSED itself from granting it; route to a second adjudicator or the operator. Conditions to attach, from that handoff: redact at the render boundary (`emit`) and NEVER in `label_for` or `Unit.label`; keep the basename and repo-relative tail verbatim and strip only the directory prefix above the repo root or home; fail closed to a withheld token if the redactor is unimportable; fix all three `emit` channels at once or the leak moves rather than closes; leave `--text-stdin`'s literal `<stdin>` label alone; and cover `tools/edit_lint_check.py` in the SAME item, by test rather than by inspection, since it builds its own labels but emits through the same `gate.emit`. Expect ZERO tests to turn red - the only assertion pinning label shape is `tests/test_precommit_gate.py::test_verbose_lists_every_checked_unit`, which pins a basename; a red test there means the redaction went too far, so fix the redaction rather than the test.
CS-205 - Redact the remaining exception renderings outside the two CS-202 files - acceptance: a MECHANIZED repo-wide test, not a hand-maintained instance list, asserts that no tracked module renders an exception into a message without redaction, covering `scripts/install_hooks.py`, `tools/edit_lint_check.py`, `tools/memory_sync.py` and `clockspeed/data/version.py` - tier: 1 - NOTE: `scripts/install_hooks.py` is FROZEN and this item carries its own grant request. The acceptance is mechanized deliberately: CS-202's hand-listed instance set went stale between being written and being worked, which is what produced its rescope. Also carries the residual left by CS-202: `traceback.print_exc()` in the gate's top-level crash handler still renders exception messages unredacted, which is not a formatting rendering and so fell outside CS-202's sweep.
CS-206 - Route `hooks_path` in `tools/facts_probe.py` through `redact()` - acceptance: a probe run in a checkout under a home directory emits no home path on the DEFAULT path, and a test plants a synthetic home segment and asserts its absence - tier: 1 - NOTE: found 2026-08-14 while building the CS-203 test module, and demonstrated empirically rather than inferred: `_git_facts()` puts `git config --get core.hooksPath` straight into the default payload and it is the ONLY path the probe emits that never passes through `locate.redact()`. Harmless on the current machine because the checkout is at the repo root, and a leak on any checkout under a user profile - and this payload is injected at every session start, so non-negotiable 12 applies. `tests/test_facts_probe.py` records the gap in its "what this file does not cover" block; it deliberately carries no xfail, because a strict-xfail would turn the suite red for whoever fixes it.
CS-207 - `scripts/verify_env.py` reports `core.hooksPath` MISSING when the hook path is absolute - acceptance: a `core.hooksPath` of `<repo>/.githooks` in absolute form is reported FOUND, the relative form still is, and a value pointing anywhere else is still reported MISSING - tier: 1 - NOTE: found 2026-08-14 and confirmed PRE-EXISTING - the check is byte-identical to HEAD, so CS-202 did not introduce it. The config holds an absolute `<repo>\.githooks` while the check compares against the literal `.githooks`, so the script reports a HARD dependency missing while the hooks demonstrably fire - proven end to end this session by staging an em-dash violation, attempting a real commit, and observing exit 1 with HEAD unchanged. This is the `hook-presence-is-not-hook-firing` failure class inverted, and it is the more corrosive direction: a false red on the one script that verifies the safety net trains the operator to ignore it.
CS-208 - Raise the world-name matchability floor above the measured shortest real world name - acceptance: the floor is derived or configured rather than a bare literal, and a test proves a world name at the floor length does not blocklist ordinary prose - tier: 1 - NOTE: found 2026-08-14 by the CS-201 builder, which implemented the adjudicated 3-character floor as specified rather than quietly raising it. The shortest world name discoverable on this machine is 4 characters, which clears that floor but is short enough to collide with ordinary English in a future commit. A collision blocks every commit until the operator finds the cause, and the gate is the worst place to learn that lesson.

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
