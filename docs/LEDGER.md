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

### 2026-08-14 - CS-205 - A MECHANIZED repo-wide sweep asserts no tracked module renders an exception OBJECT into a message
Verification: `tests/test_exception_rendering.py` plus `scripts/install_hooks.py`,
`tools/precommit_gate.py`, `tools/edit_lint_check.py`, `tools/memory_sync.py` and
`clockspeed/data/version.py`. Merged under the two frozen-file grants recorded above.
Suite 1067 -> 1088, exit 0.
The detector ENUMERATES tracked and untracked-but-not-ignored `*.py` rather than reading a
list. The enumeration was widened beyond `--cached` for a measured reason: `--cached` cannot
see a module until it is committed, INCLUDING THE DETECTOR ITSELF on the commit that adds it,
which the builder hit as a genuine red.
THE RED NAMED 13 REAL SITES IN THE REAL TREE, not a fixture, matching the adjudicator's
independent AST sweep on file and line. It matched only after the TREE CORRECTED THE BUILDER
TWICE, and both corrections are worth keeping: (1) the builder's first sweep found 12 and
missed `tools/edit_lint_check.py:82`, where the object is the DEFAULT of a
`getattr(exc, "problem", exc)` - it reads like a field access and renders the whole object
whenever the field is absent, so the adjudicator was right and the detector was too narrow.
That shape is now a positive-control case. (2) The builder found 3 sites the adjudicator did
not report, all in `tests/save/test_usmap.py`, where the rendering IS the subject under test -
recorded as the single waiver, with its reason, and ASSERTED STILL LIVE so it cannot rot.
Both controls are real. POSITIVE: 8 leaky shapes across 10 sites all caught, and separately a
leaky module was written into `tools/`, watched to go red, and deleted - which proves the
ENUMERATION catches a file that is on no list. NEGATIVE: `clockspeed/data/docs_extract.py` is
pinned BY NAME as not-flagged and the assertion is proven non-vacuous, because that module
renders `exc.reason`, `exc.msg` and `exc.lineno` and a naive detector flags it, after which
someone either "fixes" correct code or loosens the test.
The installer stays DEPENDENCY-FREE by duplication rather than import, proven by tests that
run it with `clockspeed/` and `tools/` absent AND syntactically broken - it is the first thing
a fresh clone runs. Idempotence held: two real runs, exit 0 both, stdout byte-identical at
1080 bytes. The builder captured and restored the machine's real `core.hooksPath`, which the
installer rewrites; the merger verified it afterwards as `C:\Clockspeed\.githooks` with
`verify_env.py` reporting FOUND and VERDICT PASS.
GRANT B implemented as ruled: the crash traceback is SUPPRESSED BY DEFAULT behind
`CLOCKSPEED_CRASH_TRACEBACK=1`, the exit code stays 1 on both paths, and the crash is provoked
FROM OUTSIDE by patching `argparse` before `runpy` re-executes the gate, so no test hook was
added inside the frozen file. `tests/test_precommit_gate.py` was not touched at all.
GRANT B'S CITED LINE NUMBER WAS STALE - it named `:1670` and the only `traceback.print_exc()`
was at `:1778`. The builder proceeded because "the single site" was unambiguous, and said so.
PROVEN END TO END BY THE MERGER AFTER THE MERGE, because hook presence is never proof of hook
firing and this change touched both the gate and the installer: an em-dash violation was
staged, a real `git commit` attempted, and the result was `precommit_gate: BLOCKED`, the
CHARSET diagnostic naming U+2014 at line and column, and HEAD UNCHANGED.
UNCLOSED AND CORRECTLY NOT SELF-GRANTED, now filed as CS-406: `scripts/install_hooks.py:310`
is a `traceback.print_exc()` of the same class as grant B, which grant A does not reach - the
adjudicator's own structure implies this, since it carved the gate's traceback into a separate
grant precisely because a traceback needs a different remedy from a redaction; and `:236`
prints the absolute repository root on the SUCCESS path, a third adjacent non-exception leak
the adjudicator did not name. Both are recorded in the sweep's live residual list, so a NEW
unguarded traceback anywhere already fails the suite while these two are grandfathered by name.
Also unverified and stated: the `:170` chmod branch is fixed but never EXECUTES on Windows,
so it is verified by inspection plus a direct probe of the redaction helper against a real
`OSError`, and by CI tier 2 rather than here.

### 2026-08-14 - CS-400 PARTIAL - Phase 4 waves 0 and 1: the spec correction, the synthetic corpus, and the four independent readers
Verification: `clockspeed/save/{header,chunks,usmap,workdir}.py` plus
`tests/save/{synthetic,test_synthetic,test_header,test_chunks,test_usmap,test_workdir}.py`.
Suite observed at close: 1067 passed, exit 0, from 734 at session start.
**CS-400 IS NOT CLOSED AND REMAINS OPEN ON THE ROADMAP.** Waves 2 and 3 are unstarted:
`objects.py`, `world.py`, the phase-4 acceptance gate and the `mInventoryPotential`
experiment. None of the four acceptance clauses is met yet, because none can be met without
`load_world`. This entry records the waves that DID land so the next session does not redo
them; it does not claim the phase.
WAVE 0. `BOOTSTRAP.md` sections 2.4 and 3.1 are now version qualified, and ADR 0007 records
why - see its own entry. The synthetic corpus is `tests/save/synthetic.py`, every byte built
in code, validated by an independent minimal reader written inside the test module rather
than by any production parser, and anchored against a real save by a shape-only test that RAN
on this machine rather than skipping. Three kill mutations proved the fixtures discriminate;
the sharpest - swapping the map-name and options slots - is caught by the ANCHOR ALONE, which
is the case no synthetic test can reach.
WAVE 1, four modules on disjoint write-lists, each graded against its own acceptance:
`header.py` carries NO field holding the save name, options string or session name. Not
redacted - ABSENT. The default parse never DECODES those bytes, asserted functionally (a
header carrying 0xFF in the session name parses while `reveal_strings` on the same bytes
raises) and structurally (an AST count pinning the parse to exactly two decoded strings).
`chunks.py` detects the framing from the MARKER and warns rather than raising on a
version disagreement, walks multi-chunk bodies to a clean end of file, and refuses a declared
decompression bomb BEFORE allocating.
`usmap.py` derives the inner grammar from the bytes and is verified against the shipped file:
57,985 names, 2,603 enums, 13,792 schemas landing exactly on a clean `CEXT` tag, with the
trailing extension container flagged and skipped and `body_consumed` reporting the gap.
`workdir.py` is the SOLE write-capable call site in the package - one `open("wb")` - which is
what makes the single-writer property a static assertion. Its refusal PREVENTS the write
rather than reporting it, isolated by mutation.
THREE MEASUREMENTS TAKEN BY THE MERGER AGAINST REAL SAVES, because no synthetic test could
settle them and two builders had reported fixture properties as format properties:
(1) The four int64 chunk sizes are `(c, u, c, u)`, NOT `(c, c, u, u)` - measured on all 14
saves across all three header versions. W1-CHK named this as its one genuine common-mode risk
and had guessed correctly, but it was a guess until measured.
(2) The decompressed body prefix is version scoped and THE CORPUS IS WHAT DIVERGES: real
header 13 and 14 bodies open with an int64 equal to body length minus 8, and real header 10
opens with an int32 equal to body length minus 4. A builder's "first int32 is 2" was a
measurement of the FIXTURE. `chunks.py` is unaffected because it never interprets the prefix;
W2-OBJ would have been. Filed as CS-404 before it could reach wave 2.
(3) Real bodies run to 138 chunks and just over 18 MB against 3 chunks in the largest
fixture.
CARRIED FORWARD TO THE PHASE GATE, verified by the merger rather than taken on trust: the
static single-writer scan returns `[]` for `os.open(p, os.O_WRONLY)`, so it cannot see
flag-based writes. The W3-GATE AST gate MUST cover `os.open`. The runtime audit hook does
check flags, so the two halves are complementary and neither is sufficient alone.
PROCESS FINDING, and it fired on FIVE of the seven builders dispatched: an isolation worktree
was cut from a STALE commit rather than from the stated HEAD. Every one of them detected it,
verified ancestry and reconciled before building, rather than reporting a baseline that was
real for the worktree and wrong for the tree. State the HEAD in every dispatch and require
the builder to check it.

### 2026-08-14 - ADR 0007 - The save header layout and the chunk framing are VERSION DEPENDENT
Verification: `docs/adr/0007-header-and-chunk-framing-are-version-dependent.md`, status
`accepted`, indexed at `docs/adr/README.md`. `BOOTSTRAP.md` sections 2.4 and 3.1 carry the
version-qualified tables and own those measurements.
ADR: `docs/adr/0007-header-and-chunk-framing-are-version-dependent.md`.
Measured across all 14 local saves, independently three times - by a planner, by the merger,
and by the adjudicator, each with its own read-only probe that reduced every string to a
boolean or a length before printing. Header version 14 carries FOUR leading strings and
header versions 10 and 13 carry THREE. Chunk framing on header 13 and 14 uses marker
`0x22222222` with an int8 algorithm byte and zlib at magic+49; header 10 uses marker
`0x00000000`, has NO algorithm byte at all, and zlib begins at magic+48. The header tail is
28 bytes on 13 and 14 and ZERO on 10.
THE PRIVACY MECHANISM IS THE REASON THIS IS AN ADR AND NOT A FOOTNOTE. On header 10 and 13
the THIRD string is the operator-chosen SESSION NAME; on header 14 it is the options string.
So a redactor targeting a NAMED FIELD is defeated by a version-dependent field ORDER. That
was demonstrated live rather than theorised: a planner probe in this session printed one such
value into its own agent transcript by labelling the third string "options". Nothing was
written to any file and nothing entered the repo.
THE ADJUDICATION RETURNED NEEDS-REVISION, NOT ACCEPT, and the four defects were fixed before
the status flipped. The load-bearing one was not about the save format at all:
`docs/adr/0003` is status `accepted` - binding, and citable freely - and its Context states
the refuted unqualified framing verbatim including the hex constants, so the STALE claim held
the HIGHER status and a reader searching for the framing would hit it first. Neither an
accepted ADR nor an append-only ledger entry may be edited, so the correction travels as a
pointer in both directions; see the CS-104 entry.
The other three: the int8 after the datetime ticks was labelled "session visibility" and is
not a flag - it reads `0x00` on header 10, 13 and 14/60 and one of `0x10`, `0x50`, `0x90` or
`0xD0` on the eight header-14/save-52 saves, so it is now recorded as measured in POSITION
and unverified in MEANING, its position anchored by the int32 after it reading 40 on all 14.
The opt-in PII path is now render-site only, because `locate.redact()` holds NO NEEDLE for a
session name read out of a header - that string is not knowable in advance, so the one
sanctioned accessor returns a value the project's own redactor cannot neutralize. And
Decision item 6 is restated as a COMMITMENT rather than a description, because
`clockspeed/save/` held only `__init__.py` when it was written.
UNDETERMINED AND RECORDED AS SUCH: whether the framing keys on header version, save version
or build changelist. All three predict it perfectly because they covary across every local
file, so no local file separates them. Detection from the marker is immune to which is right.
STATED LIMIT OF THE ACCEPTANCE: all 14 saves come from one machine, one account and one map,
with an empty mod metadata field on all 14. The version triple is an unproven discriminator
against a modded or another-platform save, which would present a KNOWN triple with an
unmeasured field shape and would NOT trip the unknown-combination guard.

### 2026-08-14 - CS-104 - CORRECTION: the chunk framing recorded by this item is VERSION DEPENDENT, and the entry as written is true only for header versions 13 and 14
Verification: `docs/adr/0007-header-and-chunk-framing-are-version-dependent.md` plus
`BOOTSTRAP.md` section 3.1. This ledger is append-only, so the original CS-104 entry is
left exactly as written and this entry is the correction pointer.
CS-104 recorded the body framing as magic `0x9E2A83C1`, marker `0x22222222`, int64 max chunk
size 131072, int8 compression algorithm 3, sizes written twice, and a decompressed body
opening with an int64 length. Measured this session against all 14 local saves and confirmed
independently by two agents plus the merger: that holds on header versions 13 and 14 and is
FALSE on header version 10, where the marker is `0x00000000`, there is NO compression
algorithm byte at all, the zlib stream begins at magic+48 rather than magic+49, and the
decompressed body does NOT open with an int64 length.
Proven rather than asserted: on the 11 header-13-and-14 saves zlib decompresses at +49 and
FAILS at +48; on the 3 header-10 saves it decompresses at +48 and FAILS at +49. The byte at
magic+16 on header 10 takes the values 2, 2 and 3 across those three saves - it VARIES,
which is positive evidence it is the low byte of the compressed size and not an algorithm
byte. Every chunk of every save was walked to a clean end of file with both duplicated size
pairs agreeing.
`docs/adr/0003-s4-node-actors-in-save.md` Context item 1 carries the same unqualified claim
and is status `accepted`, so the refuted text held the higher status until now. Per
`docs/adr/README.md` an accepted ADR's text is never edited; ADR 0007 NAMES it instead, so a
reader searching for the framing is routed forward rather than stopping at the stale copy.

### 2026-08-14 - CS-204 - The diagnostic label channel is redacted at the render boundary, across FOUR channels rather than the three the item named
Verification: `tools/precommit_gate.py` and `tests/test_precommit_gate.py`, plus a new
`tests/test_edit_lint_check.py` exercising the second tool as a subprocess. Merged under the
frozen-file grant recorded above, whose ten conditions were all discharged.
Re-verified by the merger independently of the builder: a `--files` run over a path under
the home directory emits no home path and no account name, the out-of-repo DIRECTORY name is
stripped, both basenames survive verbatim, the CHARSET diagnostic still fires and the exit
code is still 1. The tracked-tree rehearsal is unchanged at PASS, 118 checked, 1 skipped, 0
blocking, exit 0.
THE ACCEPTANCE CRITERION WAS WRONG AND WAS OVERRIDDEN BY ADJUDICATION. It named three
channels; there are FOUR, because `report.notes` also carries labels. All four are fixed and
each has its own test on both tools. The ruff-note test deliberately embeds the label
MID-STRING, so a fix that only redacts a leading label fails it.
Condition 1 was proven MECHANICALLY rather than by inspection: an AST byte-comparison against
HEAD shows `label_for`, `Unit`, `check_path`, `mode_files`, `mode_staged`, `stage_for_lint`,
`record_ruff_findings`, `check_python_syntax`, `check_charset` and `Diagnostic` are all
IDENTICAL, so nothing verdict-bearing moved. Every diff hunk sits inside `emit` or the new
render-boundary block above it.
Condition 7 was discharged by NOT importing rather than by a fail-closed test: zero imports
were added and `test_the_gate_imports_only_the_standard_library` asserts it by AST, so the
`except Exception` clause the grant required never becomes reachable.
Condition 4 was proven DISCRIMINATING by mutation: swapping in a home-keyed redactor turns
exactly one named test red and nothing else.
Condition 9's anti-vacuity repair was applied as authorised - `LEAK_MARKER` moved from a
directory component to the basename - and proven still non-vacuous by mutation: removing the
redaction fires the `<= 1` assertion on all three consuming tests.
`tools/edit_lint_check.py` REQUIRED NO EDIT. Fixing `gate.emit` covered it, and that is
proven by the new subprocess test rather than by inspection, which is what the grant demanded.
Verdict invariance was measured against a NON-VACUOUS corpus, which is the part that is easy
to fake: the tracked-tree run alone is a 0-versus-0 comparison and proves nothing, so a
six-file violation repository was built UNDER A HOME DIRECTORY carrying BINARY, CHARSET,
LINT, PII, SECRET and SYNTAX violations, and the exit code and the full diagnostic set are
byte-identical before and after, labels included.
The common-mode risk flagged at dispatch is CLOSED by a test that `git init`s a throwaway
repository with `HOME` and `USERPROFILE` pointed at a temporary directory. That test also
CORRECTED A CLAIM THE BUILDER HAD WRITTEN: it had asserted the test guards condition 4, and
mutation showed it does not, because labels in that repository are already relative so a
home-keyed rule leaves them alone. The docstring records the measured truth instead.
The gate caught the builder's own test file mid-slice with four `PII absolute POSIX home
path` diagnostics; the values are runtime-assembled now, and no literal entered a tracked file.
UNCLOSED AND EXPLICITLY NOT CLAIMED: `tools/edit_lint_check.py:113` renders
`f"could not read the file: {exc}"` raw where the gate uses `safe_exc_text`, so the label is
redacted and the REASON still leaks a path. That is CS-205's scope and is left to it rather
than colliding with a concurrent slice. Also unverified: POSIX behaviour, argued structurally
and pinned by the determinism test but never observed on a Linux runner; and `--staged` mode,
whose labels are always repo-relative so redaction is a no-op there by reasoning, not by
measurement.

### 2026-08-14 - CS-206 - tools/facts_probe.py redacts hooks_path, and a SECOND unredacted field found by the sweep
Verification: `tools/facts_probe.py` plus `tests/test_facts_probe.py`, ten new tests. Proven
by a planted SYNTHETIC home segment asserted absent from the emitted payload - never by
`redact(x) != x`, which is the redactor-as-its-own-oracle failure class and is blind exactly
where the redactor is blind.
Re-verified by the merger in the MAIN checkout, which the builder could not do because its
`repo_root()` was its worktree and relativization correctly did not fire there: the default
payload now renders `hooks_path` as `.githooks`, and the serialized payload contains neither
the `USERPROFILE` literal nor the Windows account name.
The fix goes REPO-RELATIVE FIRST and `locate.redact()` second. The first pass closes a class
`redact()` structurally CANNOT reach: it builds its home needles from the environment, so a
checkout under a directory the environment never names matches none of them.
A SECOND UNREDACTED FIELD was found by the mandated full-payload sweep and fixed in the same
change, as an addition to the item's stated scope: `git.branch`. It cannot BE a path - git's
ref format forbids backslash, colon and space - so it passes a literal "cannot carry a path"
test, but `<user>/wip` is an everyday branch convention and the Windows account name is
personal data of the same rank under non-negotiable 3.
TRADE-OFF ACCEPTED AND RECORDED RATHER THAN HIDDEN: `redact()`'s digit-run backstop will
rewrite a date-shaped branch such as `release/20260814` into `release/<account-dir>`. That
label is misleading - it names an account directory where a date stood. The over-redaction
direction was taken deliberately, per `locate.py`'s own stated principle and because
fail-closed beats fail-open on PII, and the misleading label is the price.
The `if not value` guard is load-bearing and is documented as such: `locate.redact()`
stringifies its argument, so the tempting `redact(x) or None` returns the truthy string
`"None"` and would turn an UNPROTECTED checkout into one that reads as protected.
When the data layer does not import there is no redactor, so values are WITHHELD rather than
emitted raw, and withheld is kept distinct from `None` so that "wired but suppressed" never
reads as "not wired". Those two guards were mutation-checked: replacing the withheld return
with the raw value turned both tests red via the independent leak assertion.
Swept and explicitly cleared: `game.build` and `game.build_via` were traced through every
probe and every emitted label enumerated - all fixed literals, none derived from a discovered
path. `git.sha` is deliberately left raw as machine-generated hex, because redacting it would
let the digit backstop eat an all-numeric abbreviation.
Honest limits: behaviour on the Linux CI runner is unverified - only Windows was run - and
the new tests require `git` on PATH and error rather than skip without it, which adds no new
dependency since the gate suite already requires it.

### 2026-08-14 - CS-207 - scripts/verify_env.py compares RESOLVED PATHS, so an absolute core.hooksPath is no longer a false MISSING
Verification: `scripts/verify_env.py` plus `tests/test_verify_env.py`, sixteen named tests.
Proven live rather than by unit test alone: before, `python scripts/verify_env.py` printed
`HARD core.hooksPath == .githooks MISSING` and `VERDICT: FAIL` at exit 1 while the hooks
demonstrably fired; after, it prints `core.hooksPath -> .githooks FOUND`, `HARD: 7/7`,
`VERDICT: PASS` at exit 0. Confirmed PRE-EXISTING before the fix: `git log -L 483,498` on
that file returns the initial commit alone, so the lines were never touched and CS-202 did
not introduce it.
All three acceptance halves are covered separately, and the third is the one that is easy to
lose: an absolute form is FOUND, the relative form is STILL FOUND, and a value pointing
anywhere else is STILL MISSING. The comparison is `os.path.normcase` over resolved paths,
chosen over a hand-rolled lowercase (wrong on a case-sensitive filesystem) and over
`Path.samefile` (whose `st_ino` can be 0 on some filesystems and would then equate different
directories). Existence is checked SEPARATELY and BEFORE identity, using `is_dir()` rather
than `exists()`, because `Path.resolve()` is non-strict and identity alone would report FOUND
for a hooks directory that was never created, and because a file there runs nothing.
FOUND AND FIXED BEYOND THE STATED SCOPE, and it would have defeated the fix: `core.hooksPath`
is SHARED git config, so inside a linked worktree it holds the MAIN checkout's absolute path.
Comparing only against `<root>/.githooks` would have RELOCATED the false red into every
worktree rather than removing it - and every builder in this project runs in a worktree.
`expected_hooks_dirs()` therefore also accepts the main checkout's `.githooks`, derived from
`git rev-parse --git-common-dir`. Criterion 3 is not weakened: both entries are specific
resolved directories, pinned by `test_a_linked_worktree_still_rejects_an_unrelated_hooks_dir`.
PII: the row and `facts["hooks_path"]` both go through `redact()` now. Fixing only the table
would have left `--json` publishing the home path. The module docstring already CLAIMED that
every path it prints goes through `redact()` first; that claim was false and is now true.
THE GUARD TESTS WERE PROVEN TO DISCRIMINATE rather than assumed to: four mutations were
applied to the fix in turn - matching on the trailing segment, dropping the existence check,
`exists()` for `is_dir()`, and dropping relative anchoring - and each turned a NAMED test red.
Honest limits, recorded rather than omitted: the drive-letter-case test is skipped off
Windows and was never observed to run; the `_resolved_key` `OSError` branch has no test and
fails closed by inspection rather than by measurement; and the builder verified the CHECK's
verdict, not that the hooks fire - that end-to-end proof remains session 3's.

### 2026-08-14 - CS-208 - Frozen-file grant DENIED, and the item is refuted by measurement rather than deferred
Verification: adjudicated under `CLAUDE.md` section 6 by an agent that authored no part of
the proposal and did not find the original defect. The grant sought an edit to
`tools/precommit_gate.py:570` (`MIN_ACCOUNT_NAME_CHARS = 3`), through which world names route
at `:852` and account names at `:960`. DENIED, and the denial rests on measurements that
refute the item's own premise rather than on a judgement call.
MEASURED, values never printed, lengths only: 16 distinct matchable world names are
discoverable on this machine, the shortest being 4 characters. A floor of 4 drops nothing; a
floor of 5, 6 or 8 drops EXACTLY ONE currently-matchable real world name, which then stops
being blocked and WILL COMMIT. The item as worded - raise the floor ABOVE the measured
shortest real world name - therefore SPECIFIES a fail-open hole.
MEASURED, and this is what refutes the premise: the feared false positive does not exist.
The gate over all 117 tracked files with live discovery exits 0 - "117 checked, 1 skipped, 0
blocking". Sixteen real world names, one of them 4 characters, collide with nothing in the
tree today. And when a collision does occur it is not a hunt: a planted synthetic
4-character world name against ordinary prose produces file, line, COLUMN, rule and
citation on the first block. `ROADMAP.md`'s "blocks every commit until the operator finds
the cause" was overstated.
MEASURED: a floor of 4, 5, 6 or 8 turns ZERO of the 65 gate tests red, because every world
value declared in the suite is either 16, 15 or 2 characters. "No tests break" is therefore
NOT evidence of safety here - it is proof the change is untested and the suite is blind to
it.
The (a)/(b) design question was ruled on rather than left open. (b), raising the single
shared floor, is rejected outright: two fail-open holes bought with one hypothetical false
positive, and it silently narrows ACCOUNT-name matching on every machine so that a 3- or
4-character login stops being matched with nothing in the suite noticing. (a), splitting the
constant, is sound hygiene but insufficient reason to edit a frozen file at equal values,
and a split whose purpose is to raise the world half is (b) with a tidier blast radius.
The governing asymmetry is already recorded in this file under CS-201: the gate must be
WIDER than the resolver. Narrowing a PII blocklist by default, on every machine, to pre-empt
a collision that has not occurred and that diagnoses itself to line and column when it does,
trades a certain fail-open for a diagnosable fail-closed.
SUPERSEDED BY CS-209, which carries the correct fix: a per-value exclusion surface applied
after discovery, a remedy clause in the world-name reason, and the separately-found defect
that `.githooks/pre-commit` passes neither `--verbose` nor `--list-skipped`, so the skip
channel that CONVENTIONS section 15.1 relies on to keep a drop visible does not print at all
on the authoritative path.

### 2026-08-14 - CS-205 - Frozen-file GRANT B WITH CONDITIONS: the single `traceback.print_exc()` site in tools/precommit_gate.py
Verification: adjudicated under `CLAUDE.md` section 6 by an agent that authored no part of
the proposal; recorded here BEFORE any edit. Scoped as its own grant line because it is a
different frozen file from grant A and because CS-205's own stated scope is "outside the two
CS-202 files", of which the gate is one - so it falls outside grant A twice over.
RULING: a traceback CANNOT be honestly redacted. It renders an absolute path per frame - a
home path on any checkout under a user profile - and its final line is `str(exc)`, the exact
rendering CS-202 removed everywhere else. Frame paths can be rewritten, but re-implementing
per-type redaction at the crash handler duplicates `safe_exc_text` at the least testable
point in the program.
The granted alternative is the pattern non-negotiable 12 already mandates for the save
header options string: SUPPRESS BY DEFAULT, opt in explicitly. Four conditions. (1) Default
crash output is the exception class name, `safe_exc_text(exc)`, the existing fail-closed
sentence, and the NAME of the flag that reveals the rest; a test provokes a crash and
asserts no absolute path in the default output. (2) EXIT CODE STAYS 1, proven by test,
together with the "gate itself raised / failing CLOSED" message - a gate that crashes open
is worse than no gate. (3) The opt-in is a `CLOCKSPEED_`-prefixed environment name,
documented in the module docstring beside the existing five, default OFF, and its ON path is
tested to still exit 1. (4) No new import into the gate.
The grant permits reformatting the crash report and NEVER swallowing it, and reaches nothing
in `tools/precommit_gate.py` other than that one site at `:1670` and its adjoining crash
message.

### 2026-08-14 - CS-205 - Frozen-file GRANT A WITH CONDITIONS: scripts/install_hooks.py may have its exception renderings redacted
Verification: adjudicated under `CLAUDE.md` section 6 by an agent that authored no part of
the proposal; recorded here BEFORE any edit. The frozen list is unchanged and no agent
self-granted.
The dispatch invited a NOT-NEEDED denial if `scripts/install_hooks.py` carried zero
unredacted renderings. It carries SIX - `:65`, `:67`, `:85`, `:170`, `:227` and `:240` - so
the grant is genuinely necessary. `:67` and `:227` are the argv-plus-exception shape CS-202
already fixed in the gate, and `:170` is on the POSIX-only branch that CI tier 2 executes.
FOUND ADJACENT AND NAMED RATHER THAN LEFT SILENT: `:70-76` renders git's decoded stderr
verbatim, and `:149` renders an absolute path directly. Both are the same leak class and
NEITHER is an exception rendering, so the mechanized sweep this item mandates will not see
them. Condition 8 requires they be fixed under this grant or recorded as an explicit named
residual.
THE ROADMAP'S OWN FILE LIST WAS ALREADY STALE, which is the exact failure the mechanized
acceptance was written to prevent. An independent AST sweep across all tracked `*.py` found
13 real object renderings in 4 files, and surfaced a fifth file -
`clockspeed/data/docs_extract.py:443` and `:589` - which is a FALSE POSITIVE: those render
`exc.reason`, `exc.msg` and `exc.lineno`, which are named fields rather than the object. A
naive detector will flag them, and someone will then either "fix" correct code or loosen the
test.
Nine conditions carry the grant; the load-bearing ones are 2, 4 and 5. (1) Per exception
TYPE allowlist, never a strerror-shaped helper, per the CS-202 precedent recorded above.
(2) THE INSTALLER STAYS DEPENDENCY-FREE - it is the first thing a fresh clone runs, so if
the builder imports rather than duplicates, a test must prove `install_hooks.py` still runs
and still exits correctly with `clockspeed/` and `tools/` absent or syntactically broken.
(3) The detector ENUMERATES tracked files and never hardcodes a module list. (4) The
detector distinguishes the exception OBJECT from a FIELD of it, with a NEGATIVE control
asserting the `docs_extract.py` shape is not flagged and a positive control asserting the
`{exc}` shape is. (5) A POSITIVE CONTROL IS MANDATORY - the mechanized test must be shown
capable of failing against a synthetic leaky module, or it is a green light with nothing
behind it. (6) No self-exemption; the detector covers its own module. (7) Exit codes
unchanged, the `core.hooksPath` readback check at `:154-159` untouched, and a second run
still prints byte-identical output. (8) The two adjacent non-exception leaks are fixed or
named. (9) The authoritative scope is the mechanized enumeration, NOT the four-file list on
the roadmap line.
The grant does NOT permit changing the installer's wiring logic, the readback check, the
hook inspection rules, or any exit code.

### 2026-08-14 - CS-204 - Frozen-file GRANT WITH CONDITIONS: tools/precommit_gate.py may redact the diagnostic LABEL channel at the render boundary
Verification: adjudicated under `CLAUDE.md` section 6 by an agent that authored no part of
the proposal and did not find the original defect; recorded here BEFORE any edit. The frozen
list is unchanged and no agent self-granted. The prior adjudicator's recusal is honoured -
it found the defect and did not grant it.
THE SIX VERDICT-BEARING CALL SITES ARE CONFIRMED AND UNDERSTATED. Enumerated at `:1471`,
`:1520` (`check_path` in staged and files mode), `:1136` (`compile` -> `SyntaxError.filename`),
`:1239` (the staging-copy filename ruff actually lints), `:1234`/`:1241` (the ruff output
mapping) and `:1477` (`git show :<label>`). TWO MORE were found: `:1469` and `:1518` derive
the EXTENSION from the label rather than from the given path, and that extension selects
WHICH CHECKS RUN - `classify_for_read`, the NUL rule, the `check_content` dispatch and ruff
target selection; and `:1111-1117` scans the label itself for non-ASCII and reports
`label.index(offending) + 1` as the column. The prior adjudicator's risk classification is
correct and if anything conservative.
THE ACCEPTANCE CRITERION WAS WRONG AND IS OVERRIDDEN HERE. It names three channels;
there are FOUR. `report.notes` carries labels at `:350`, `:360`, `:1268` and `:1346` and is
printed by `emit` at `:1605-1607` and `:1627-1631`. Demonstrated live: a `--files` run over
an out-of-repo path leaks the home path through checked, skipped, notes AND diagnostics.
Fixing exactly the three named channels MOVES the leak into notes, which is precisely what
the item's own "fix all channels at once" condition exists to prevent.
"ZERO TESTS TURN RED" IS ALSO REFUTED. `tests/test_precommit_gate.py:1174` is a SECOND
label-shape assertion - `LEAK_MARKER` is a DIRECTORY component of an out-of-repo path, and
any redaction stripping directory components above the repo root deletes it. Three tests
consume it, at `:1191`, `:1201` and `:1226`.
Ten conditions carry the grant. The load-bearing ones are 1, 2, 4, 7 and 9. (1) Redact
inside `emit` via a pure function of the label; `label_for` and `Unit.label` return
byte-identical values to HEAD, proven by test. (2) FOUR channels, one test each, each
provoked by an out-of-repo target. (3) Both tools covered by test, `tools/edit_lint_check.py`
exercised as a subprocess - inspection does not discharge it. (4) DETERMINISM: the rendered
label must not depend on where the machine's home directory is, because `tmp_path` is under
the home directory on Windows and under `/tmp` on Linux, so a home-keyed redactor is green
in CI and red locally. (5) The basename stays verbatim. (6) `--text-stdin`'s literal
`<stdin>` is untouched. (7) NO NEW DEPENDENCY - and if a shared redactor is imported, the
handler must catch `Exception`, NOT `ImportError`, because a staged em-dash in
`clockspeed/data/locate.py` raises `SyntaxError`, which `except ImportError` does not catch,
and the gate would crash instead of printing the CHARSET diagnostic it exists to print.
(8) Verdict invariance measured over every tracked file, not asserted. (9) THE ANTI-VACUITY
REPAIR IS EXPLICITLY AUTHORISED AND THE ROADMAP IS OVERRIDDEN ON THIS POINT: if `:1174` goes
red the correct repair is to re-point `LEAK_MARKER` at a component that survives redaction,
NOT to weaken the redaction; the roadmap's blanket "a red test there means the redaction
went too far" applies only to `test_verbose_lists_every_checked_unit`. (10) No literal
introduced.
The grant does NOT permit editing `label_for`, `Unit.label`, `check_path`, the `compile`
call, the staging-copy naming, the ruff mapping or the `git show` argument, changing any exit
code or diagnostic code/line/column, or adding a path allowlist.

### 2026-08-14 - CS-300 - Phase 3 gate: pillar 1 exact ratio solve, then pillar 2 behind the pluggable optimizer interface
Verification, all three acceptance criteria checked independently of the agents that built
them.
(1) HAND-VERIFIED RATIOS INCLUDING A BYPRODUCT LOOP. `tests/solve/synthetic.py` carries C1
to C9 with every expected value as a named constant. The load-bearing case is C3, where
Gadget needs Fluid, Fluid comes from Residue and Residue comes from Gadget, so naive
topological recursion does not terminate. Re-derived through the MERGED solver by the
merger, not read from a builder report: machines `R_Gadget=2, R_Recover=2/3, R_Fluid=2,
R_Plate=4/3`, raw Ore 60/min, every count exact `Fraction`, output identical across runs and
across a reversed recipe tuple. C4 solves the same loop in reverse and cross-checks C3
exactly via `Fraction(436,3) * Fraction(3,4) == Fraction(109)`. That there is no disguised
tree walk is asserted STATICALLY - `tests/solve/test_ratio.py` parses `ratio.py`'s own call
graph and requires it acyclic - because a memoizing recursive solver passes every value test.
(2) NO FLOATING-POINT ARITHMETIC ANYWHERE IN THE SOLVE PATH.
`tests/solve/test_phase3_gate.py`, 96 tests. A static AST walk over every module under
`clockspeed/solve/`, with the module set asserted EQUAL to a pinned tuple rather than merely
non-empty, so a rename cannot silently shrink coverage. Proven to DETECT rather than merely
to pass: each forbidden construct injected into the real module sources and caught at the
right line - float literal, `**`, `round`, `import math`, and a bare `float` reference. It
scans the AST and never the text, because `exact.py` and `power.py` quote the
`Fraction ** Fraction` measurement verbatim as evidence for the ban; a regex sweep reports
47 hits in `exact.py` alone, all prose. Two further independent signals cover what a static
check cannot see - `exact.audit_exact` asserts POSITIVELY (`type(x) is Fraction`) at every
public seam, and the strict mypy rung catches a `float` declared in a signature.
(3) THE OPTIMIZER SWAPPABLE BY CONFIG WITH IDENTICAL RESULTS ON A DEGENERATE CASE.
`clockspeed/solve/optimize.py` owns `OptimizerBackend`; `backends/exhaustive.py` and
`backends/greedy.py` implement it by genuinely different mechanisms - complete lattice
enumeration versus a reachability least fixed point that prunes on feasibility before
scoring. Fixture C5's feasible set is a SINGLETON by construction, with the
better-on-every-objective recipe declared first and infeasible, so a registry-order stub and
a score-before-feasibility greedy are both demonstrably wrong while any correct backend must
agree. THREE assertions ship, not one - each backend against the hand-verified absolute
(`Std_Gadget` x 3, Ore `Fraction(120)`, power `Fraction(45)` MW) and the two against each
other - because agreement between two implementations is not evidence on its own. Both are
reached only through `select_backend`; an unknown name refuses at all three precedence
levels rather than falling back, verified independently (`exhausitve` -> `UnknownBackendError`).
Determinism proven across two separate interpreter processes under differing PYTHONHASHSEED.
CS-G02's PREP half is now complete: the interface exists and is proven by two in-repo
backends, which is the stated precondition before an external LP/ILP dependency may be
considered. The DRAIN half remains gated - see `docs/GATED.md`.
A MERGER INSTRUCTION WAS REFUTED BY THE GATE AGENT AND THE REFUTATION WAS RIGHT. The wave-4
dispatch required that no solve module pull in `clockspeed.data.docs_extract`. That is
unsatisfiable: `registry.py:206` and `version.py` import it at module level, and
`tests/data/test_phase2_gate.py:775-781` REQUIRES those edges. `docs/ARCHITECTURE.md:136-138`
scopes the raw-docs prohibition to `advisor/`; the clause for this layer is "solve/ never
reads a save". The carve-out is self-verifying - a test measures each carrier in its own
child interpreter and fails if a carrier stops justifying it - and a DIRECT import of
`docs_extract` from solve remains forbidden with no carve-out at all.
Modules: `clockspeed/solve/{exact,ratio,power,optimize}.py`, `clockspeed/solve/backends/`.
Tests: `tests/solve/test_{exact,synthetic,ratio,power,optimize,phase3_gate}.py`.
ADR: `docs/adr/0006-unsharded-clock-base-and-the-ceiling-fence.md`

### 2026-08-14 - CS-105 - S7: the overclock power exponent is read from building class data, and a test fails if a literal appears in the power path
Verification: `clockspeed/solve/power.py` plus `tests/solve/test_power.py`. The data half
landed in phase 2 (`clockspeed/data/registry.py` reads `mPowerConsumptionExponent` per
building class); the guard half could not exist until there was a power path to assert
about, which is why this closed with phase 3 rather than phase 1.
The guard ships as TWO tests, and the reason is measured rather than defensive. A literal
scan over the module's constants catches `Fraction("1.321929")` - but a hardcoded
`Fraction(1321929, 1000000)` is two INT literals and passes it. Demonstrated on a
scratchpad copy: with the value hardcoded in the integer-pair spelling, the literal scan
PASSED while the mutation test FAILED. The durable half is therefore the mutation test -
two registries identical except for one building's exponent must produce DIFFERENT results,
which no spelling of a constant can satisfy - and it does not go stale when a balance patch
moves the number, which the literal blacklist does. The candidate values the scan checks
are read from the fixture and from the pin census, never restated in the test, or the test
would become the thing it forbids.
A third assertion covers what neither scan can see: `power_exponent is None` means NOT
clock-scalable and is never defaulted, so a floodlight is not silently clock-scaled.
The ceiling remains UNKNOWN per ADR 0005 and this item does not touch it:
`power.ClockCeiling` carries no field capable of holding a ceiling value, and
`version.OVERCLOCK_POTENTIAL_SHARD_SLOTS` is still None.

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
