# Clockspeed - Ledger

**Append-only, NEWEST FIRST. One record per closed work item.**

**This file owns:** the per-item completion record - what closed, when, and how to verify
it independently.

**This file never contains:** rules, open work, aspirational items, or architecture. Open
work lives in `ROADMAP.md`, aspirational work in `BACKLOG.md`, externally blocked work in
`docs/GATED.md`, and settled decisions in `docs/adr/` plus the `Settled` section of
`CLAUDE.md`.

Nothing in this file is ever edited or deleted once written. A record that turns out to
be wrong gets a **new, later** record that corrects it and says so. Pruned records move
to `docs/history_notes.md`; they are never dropped.

---

## Entry shape

Newest entry goes directly under the `## Entries` heading. Each entry is:

```
### YYYY-MM-DD - <ITEM-ID> - <one line: what closed>
Verification: <pointer>
```

| Field | Rule |
|---|---|
| Date | `YYYY-MM-DD`, the date the item actually closed. |
| Item ID | The permanent `CS-` ID from `ROADMAP.md`. Never invented at close time, never reused, never renumbered. |
| One line | What closed. One line. If it needs a paragraph it needs its own file and this line becomes a pointer to it. |
| Verification pointer | How someone else confirms it, independently, without asking you. Mandatory. |

An entry may add an `ADR:` line citing `docs/adr/NNNN-*.md` when the item settled a
decision. An entry that closes a gated item states which external condition was met and
who or what observed it.

---

## The verification pointer - what makes one valid

**Cite the item ID, the merged file, and the test name. Do not cite the slice SHA.**

A ledger entry whose only evidence is a commit SHA is **fragile**. The reason is
mechanical, not stylistic: work is produced in worktree-isolated agent slices, and those
slice commits frequently do not survive the cherry-pick into the main line. The SHA in
the entry then refers to an object that is unreachable, or reachable but not the version
that shipped. The entry looks precise and verifies nothing.

The item ID, the merged file path and the test name all survive the merge, because they
are properties of the shipped tree rather than of the branch that produced it.

**Valid pointers**

- `tests/save/test_header.py::test_world_token_stable_across_reload`
- `clockspeed/solve/exact.py` plus `tests/solve/test_exact.py::test_no_float_in_path`
- `tools/drift_guard.py` red-then-green transcript recorded under the item ID
- A named CI job on the tier-1 lane, plus the file it asserts on

**Invalid pointers**

- A bare commit SHA
- "tests pass" or "CI green" with nothing named
- A count of tests with no file and no test name behind it
- A link to a transcript or a chat message

Counts are never restated here as prose. If a count is worth citing, cite the
machine-checked artifact that produces it.

---

## Entries

<!-- Newest first. Append new entries immediately below this line. -->

### 2026-08-14 - CS-200 - Phase 2 data layer: extraction, blob grammars, normalized registry, version pin, data drift guard
Verification, all three acceptance criteria checked independently of the agents that built
them. (1) Registry builds from the LIVE install: `clockspeed/data/registry.py::build_registry`
over `clockspeed/data/docs_extract.py::load_document` yields 114 groups, 2868 entries, 872
recipes, 291 automated, 750 items, 68 buildings, 0 unknown groups. (2) Synthetic-fixture
suite green with NO game installed: `python -m pytest tests` exits 0 with every
`CLOCKSPEED_*` override pointed at a nonexistent path, and
`tests/data/test_phase2_gate.py::test_the_data_layer_suite_passes_with_the_install_unresolvable`
enforces it as a gate rather than leaving it a property the suite happens to have.
(3) Drift guard red-then-green: guard `h` in `tools/drift_guard.py`, proven on a COPY of the
tree at exit 0 clean, exit 1 with a hand-corrupted pin, exit 0 after `--re-extract`. The pin
carries its OWN integrity checksum, which is what makes corruption detectable on a runner
with no install - the only environment where tier-1 CI grades this.
Modules: `clockspeed/data/{locate,blobs,docs_extract,registry,version}.py`.
Tests: `tests/data/test_{locate,blobs,docs_extract,registry,version,drift_guard_data,phase2_gate}.py`.

Adversarial review REFUTED the first cut on two independent lenses and the defects were real,
not stylistic. Recorded because the fixes are the substance of this item:
- The registry published litres where its contract said cubic metres, on the operator's
  install, for three biofuel recipes - a whitelist of four descriptor groups missed
  `FGItemDescriptorBiomass`. Fixed by MECHANISM: the item namespace is now derived from
  `mForm` presence and the building namespace from power-field presence, so the next patch
  that adds a descriptor group cannot silently reintroduce it. 60 unresolvable item
  references went to 0, and 93 stock groups falsely reported as unknown went to 0.
- The blob-grammar canary was UNREACHABLE - `marker_count >= len(parsed)` holds always, and
  the parse ran before the comparison, so an ordinary patch-shaped grammar change produced
  an empty registry silently at exit 0. Now the count is taken before the parse and two
  document-level signals are fatal. `RegistryIntegrityError` deliberately does not subclass
  `ValueError` so the flag-and-skip handler cannot swallow it.
- 7 of 8 mutants survived the first test suite; all 7 are now killed.
- A latent PII leak was fixed in `redact()`: it stripped home prefixes but not the account-id
  path segment, and the fix was then found to cover only the 17-digit Steam shape. Redaction
  is now POSITIONAL, covering Epic hex, MS-store GUID and mixed-character directories, plus
  the Windows 8.3 short-path form. The `str(exc)` sibling sweep that had been applied to
  three sites was completed across all 16 in `tools/drift_guard.py`.
ADR: `docs/adr/0005-overclock-ceiling-source.md`

### 2026-08-14 - CS-103 - Ingredient and product blobs confirmed as struct blobs; dedicated parser shipped
Verification: `clockspeed/data/blobs.py` implements the two DISTINCT grammars - the
item-amount grammar and the `mProducedIn` path-list grammar - with `tests/data/test_blobs.py`
as its own test module, per the item's "if true" clause. Mutation-checked: flipping the
parser to split on the single quote before the double quote fails 11 tests.

### 2026-08-14 - CS-102 - NativeClass groups dumped and the normalizer authored against the dump
Verification: `clockspeed/data/docs_extract.py::load_document` derives every group short name
at runtime rather than from a hardcoded table, and `clockspeed/data/version.py::census`
records the pinned build's whole 114-group census. The normalizer was written against the
MEASURED schema in `BOOTSTRAP.md` section 3.2 - misspelled keys `mManufactoringDuration` and
`mEstimatedMininumPowerConsumption` used verbatim, asserted by
`tests/data/test_registry.py::test_the_misspelled_keys_are_used_verbatim_not_autocorrected`.

### 2026-08-14 - CS-101 - Docs-file encoding settled by BOM bytes, both encodings handled
Verification: `clockspeed/data/docs_extract.py::sniff_encoding` classifies from the leading
BOM BYTES only. The load-bearing test is
`tests/data/test_docs_extract.py::test_sniff_encoding_classifies_by_bom_bytes_not_by_trial_decode`,
which demonstrates by construction that decoding UTF-8 bytes as `utf-16` does NOT raise -
so a trial-decode sniffer returns mojibake and reports success. Only the byte test is sound.

### 2026-08-14 - CS-100 - Phase 1 gate met: a written spike report with a binary answer per spike
Verification: `docs/_archive/spike-report-s1-s2-s3-s7.md` carries a binary verdict for S1,
S2, S3 and S7; S5-body is recorded under CS-104 and `BOOTSTRAP.md` section 3.1. No phase 2
work was merged before it landed - phase 2 is this session, the report is session 1.
Correction applied to that report this session: it stated the fractional-fluid recipe "takes"
water at 1500. A live re-probe refuted the SIDE - the water is a PRODUCT, not an ingredient.
Counts in the report were correct; only the side was wrong. `BOOTSTRAP.md` section 3.2 now
carries the corrected statement and is authoritative over that line.

### 2026-08-13 - CS-007 - Frozen-file grant: LICENSE copyright holder set to "Clockspeed contributors" by operator decision
Verification: LICENSE line 3 reads `Copyright (c) 2026 Clockspeed contributors`;
`tests/test_scaffold.py::test_license_names_a_real_copyright_holder` passes; grant
adjudicated under `CLAUDE.md` section 6 - operator-sourced, no agent self-grant, frozen
list unchanged. Blast radius is one line in `LICENSE`: `pyproject.toml` deliberately
declines to restate the holder, and `git grep -I "Moonbeam"` returned exactly one tracked
hit, `LICENSE:3`, before the edit.
Adjudicator's common-mode finding, recorded because it survives this item: the change does
NOT deliver the pseudonymity that was offered as its rationale. Every commit is authored
under a real-identity email address, which publishes with the history at the CS-G03 flip
and which this edit does not touch. The holder change stands on its own merits - a
collective holder is routine MIT practice and drifts from nothing - but "protects identity
at phase 7" is NOT its effect. The author-identity question is carried by CS-G03.

### 2026-08-13 - CS-104 - S5 body framing settled; the save body decompresses end to end
Verification: run the phase-1 spike scripts against a COPY of any save; chunk framing is
magic `0x9E2A83C1`, marker `0x22222222`, int64 max chunk size 131072, int8 algorithm 3
(zlib), then compressed and uncompressed sizes each written TWICE, and the decompressed
body opens with an int64 length. Measured on the pinned world: 11 chunks, 102 KB on disk
to 1,440,651 bytes. Recorded in `BOOTSTRAP.md` section 3.1. The header was NOT re-derived.

### 2026-08-13 - CS-005 - S6 settled YES: unlock state is recoverable from the save
Verification: `docs/adr/0004-s6-unlock-state-recoverability.md`. A mature world carries
`mPurchasedSchematics`, 246 distinct `/Schematics/` paths including alt-recipes, 360
`/Recipes/` paths, `mCurrentGamePhase`, `mUnlockedResearchTrees`, `mScannableResourcesPairs`
and the feature-unlock booleans. The pinned onboarding world exposes 14 unlock properties
against the mature world's 30, which is why S6 was NOT settled on it.
ADR: `docs/adr/0004-s6-unlock-state-recoverability.md`

### 2026-08-13 - CS-004 - S4 settled: YES for node geometry, NO for node semantics
Verification: `docs/adr/0003-s4-node-actors-in-save.md`. 626 resource-node actors, 626 with
a valid transform (normalized quaternion, in-map coordinates). No node carries a property
payload and no purity or resource-type field appears in any save examined. This CONTRADICTS
`BOOTSTRAP.md` section 8.3 step 1 as originally written; section 8.3 has been corrected.
ADR: `docs/adr/0003-s4-node-actors-in-save.md`

### 2026-08-13 - CS-003 - S8 settled NO: node placement is not seed-dependent
Verification: `docs/adr/0002-s8-node-data-seed-dependence.md`. Two distinct worlds on build
463028, grouped by the header world token rather than by filename, have byte-identical node
sets: 626 shared positions, zero differences either way. Section 8.3 steps 2 and 3 therefore
remain valid and S4 is not load-bearing.
ADR: `docs/adr/0002-s8-node-data-seed-dependence.md`

### 2026-08-13 - CS-002 - Tier-0 commit gate PROVEN to fire end to end
Verification: re-runnable. Stage any of the nine violation classes and attempt a real
commit; HEAD must not move. Measured this session: 9/9 blocked - U+2014, U+2019, U+00A0,
PEM private key, absolute home path, a `.sav` forced with `git add -f`, a Python syntax
error, an AWS key id and a GitHub token. The commit-msg hook independently rejected a
non-ASCII message. HEAD before and after both `10ca0cf`. Presence was NOT accepted as
proof; the gate was made to actually reject a real commit. See `tests/test_precommit_gate.py`.

### 2026-08-13 - CS-001 - Phase 0 scaffold complete and committed
Verification: `git log --oneline` shows the root commit; `python scripts/verify_env.py`
exits zero with HARD 7/7; `python tools/drift_guard.py` runs clean; `python -m pytest tests`
passes. `.gitignore` landed in the same commit that created history, so no game data, save
file, extracted asset, generated cache or local config has ever been tracked. See
`tests/test_scaffold.py`.

### 2026-08-13 - CS-006 - Section 2 ground truth re-probed; four corrections applied
Verification: `python scripts/verify_env.py` reports the live values. Corrections written
into `BOOTSTRAP.md`: locale file count is 55 not 57; the save library holds three worlds
not one; header version is not stable at 14 (it is 10 on the oldest saves) and the library
spans four builds; and a new section 2.5 records that `py -3` resolves to a DIFFERENT
3.14.4 install carrying no pytest, ruff or mypy. Build string, install path, save location
and the 8900-8911 port band all re-confirmed unchanged.
