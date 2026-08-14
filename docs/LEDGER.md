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

### 2026-08-14 - CS-203 - tools/facts_probe.py has a test module; the default output is proven to carry no PII
Verification: `tests/test_facts_probe.py`, 13 tests. The load-bearing pair is
`test_default_payload_carries_no_account_id_no_world_name_and_no_home_path` and
`test_unredacted_payload_emits_the_account_ids_the_world_name_and_the_home_path` - the
second is what stops every "absent" assertion in the first passing against an empty
payload. Redaction is proven POSITIONAL, not prefix-only, by
`test_default_output_redacts_an_account_segment_sitting_mid_path`, parametrized over
hex-token, braceless-GUID and seventeen-digit account shapes and asserting the path TAIL
survives, so truncation cannot pass as redaction. Non-negotiable 1 is covered by a
before/after `(is_dir, size, mtime_ns)` snapshot of the save tree.
The oracle is deliberately NOT the redactor: every value is synthetic and planted by the
test's own fixture, so it is known present as ground truth. `redact(x) != x` as the test for
"x holds PII" is blind exactly where the redactor is blind, and that mistake was made and
caught in session 2.
Proven to detect by mutation on scratchpad copies, five independent breaks. The one that
matters: with `locate`'s positional account rule removed but the digit-run backstop left
intact, the hex-token and braceless-GUID cases go red while the seventeen-digit case still
PASSES - which is precisely the "fixed for one shape, silent for the other three" defect,
and proof the non-digit cases are not vacuous.

### 2026-08-14 - CS-202 - Every exception rendering in scripts/verify_env.py and tools/precommit_gate.py is redacted per type
Verification: `tests/test_verify_env.py` and `tests/test_precommit_gate.py`.
`scripts/verify_env.py::_exc_reason` and `tools/precommit_gate.py::safe_exc_text` are
per-type ALLOWLISTS that never fall through to `str(exc)`. Nine renderings were fixed, not
the seven the item named: the sweep was done by AST rather than by text search, which is
what found `verify_env.py:358` (a bare `str(exc)`, outside the `f"...{exc}"` shape the
original acceptance specified) and gate lines 704 (`%`-format) and 959 (`.format()`, which
also interpolated the git argv - and in `--files` mode that argv carries caller-supplied
paths).
Per-TYPE is the load-bearing condition and not a stylistic one: `_exc_text` in
`tools/drift_guard.py` redacts via `strerror`, which only `OSError` carries, so a single
OSError-shaped helper silently falls back to the full `str(exc)` for the `ValueError` at
:708 and the `subprocess.SubprocessError` at :868 - reintroducing the leak it was written
to close. Diagnostic value is preserved deliberately: errno, decoder reason, line and
column are kept; anything derived from a discovered path is dropped; an unrecognised type
renders as its class name only, failing closed.
RESCOPED, and the rescope is itself the finding: this item's title claimed to complete the
sweep and its acceptance named two files. Four more carry the same shape - one of them also
frozen - so the remainder is CS-205 rather than being quietly absorbed. See the grant entry
below. `traceback.print_exc()` in the gate's crash handler is a further residual, recorded
on CS-205.

### 2026-08-14 - CS-201 - The commit gate detects world names and world tokens by VALUE, and no longer filters account directories on .isdigit()
Verification: `tools/precommit_gate.py` plus `tests/test_precommit_gate.py`. Proven END TO
END rather than by unit test, per `CLAUDE.md` section 2.2 - hook presence is never proof of
hook firing: with a SYNTHETIC world value declared via `CLOCKSPEED_WORLD_NAMES`, a file
carrying it was staged and a real `git commit` attempted, giving exit 1, `PII a world name
discovered on this machine appears as a whole word`, and HEAD unchanged. The negative half
was proven in the same way: a file carrying `Build_ConstructorMk1_C`,
`Recipe_SteelWall_8x4_C`, `DedicatedServerAPIDocs` and `most-recently-modified` commits
CLEANLY with no world declared. No real world value was ever staged into any repository.
Detection is VALUE-based - environment override, then gitignored local config, then `.sav`
basenames read under the discovered account directory - and never shape-based, for the
measured reason in the grant entry below. The C10 blast-radius rehearsal (the exact tier-1
CI invocation over every tracked file) passes at exit 0 with discovery genuinely live on
this machine.
HONEST LIMIT, recorded at the mechanism and printed as a skip on every run: a world TOKEN
lives in the save header, this gate holds no header parser and must not grow one (CS-400 is
open), so an UNDECLARED TOKEN IS UNMATCHED AND WILL COMMIT. World names are recoverable
from filenames; tokens are not. A second limit: `.sav` discovery only sees worlds that have
been saved, so a world renamed since its last save matches under the old name.
The `.isdigit()` removal is scoped to the gate at `:517` and is deliberately NOT mirrored
into `clockspeed/data/locate.py:657` - see the C6 asymmetry in the grant entry.

### 2026-08-14 - CS-201 - Frozen-file GRANT WITH CONDITIONS: tools/precommit_gate.py may gain world-value detection and lose the .isdigit() account filter
Verification: grant adjudicated under `CLAUDE.md` section 6 by an agent that authored no
part of the proposal; recorded here BEFORE any edit, per that section. The frozen list is
unchanged and no agent self-granted. Ten conditions carry the grant, each stated as a
testable requirement; the load-bearing ones are C1, C2 and C10.
Blast-radius finding, measured over all 99 tracked files rather than assumed: a shape-only
22-character world-token detector is NOT VIABLE. A naive unanchored `[A-Za-z0-9_-]{22}`
matches 2082 times; anchored exact-22 matches 183; anchored exact-22 additionally requiring
a digit, an upper and a lower still matches 5, every one of them a game class name of the
`Build_ConstructorMk1_C` shape - and `clockspeed/data/registry.py` grows that population.
The adjudication also REFUTED the premise it was handed: `clockspeed/data/version.py:352`
`integrity` is a 64-char lowercase hex sha256, not a base64-like string, and the tree
carries ZERO 40-character git SHAs, so neither is the false-positive source. Detection is
therefore value-based (C2: env override, gitignored local config, or `.sav` basenames read
under the discovered account directory) and never shape-based, and it never embeds a
literal world value in the tracked gate (non-negotiable 3).
C6 is a deliberate ASYMMETRY, recorded so it is not "fixed" later: the `.isdigit()` filter
at `clockspeed/data/locate.py:657` is NOT removed. That site SELECTS which world to read,
and widening selection makes the resolver silently pick the wrong world; the gate at
`tools/precommit_gate.py:517` only widens what it refuses to commit. The gate must be wider
than the resolver, so treating the two sites identically is a bug rather than consistency.

### 2026-08-14 - CS-202 - Frozen-file GRANT WITH CONDITIONS: tools/precommit_gate.py exception renderings may be redacted
Verification: same adjudication, same section 6 route, recorded before any edit. Separate
grant from CS-201 and standing independently of it. Materially lower risk than CS-201: it
changes message TEXT, never a verdict.
The item's own acceptance criterion was found DEFECTIVE and is corrected as a condition of
the grant. Its stated `f"...{exc}"` shape matches five of the seven exception renderings in
the file; it misses `tools/precommit_gate.py:704`, a `%`-format, and `:959`, a `.format()`
that also interpolates the git argv - and in `--files` mode that argv carries
caller-supplied paths. The sweep and its test must therefore be formatting-agnostic. A
second condition forbids reusing one OSError-shaped helper for all of them: `_exc_text` in
`tools/drift_guard.py` redacts via `strerror`, which `ValueError` at :708 and
`subprocess.SubprocessError` at :868 do not carry, so the remedy is per exception TYPE.
Scope ruling recorded because it changes what CS-202 may claim: closing CS-202 against its
two named files does NOT satisfy its own title. Four further files carry the same shape -
`scripts/install_hooks.py` (ALSO FROZEN), `tools/edit_lint_check.py`, `tools/memory_sync.py`
and `clockspeed/data/version.py:815` - plus `scripts/verify_env.py:358`, which sits in a
named file but is a bare `str(exc)` outside the stated shape. CS-202 is rescoped to its two
files and the remainder is filed as CS-205 rather than being quietly absorbed.

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
