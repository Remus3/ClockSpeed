# Roadmap - OPEN work only

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

One line per item. No narrative. Shape:

```
CS-nnn - <one line> - acceptance: in detail - tier: <0|1|2> - detail: `docs/item_notes.md`
```

**THE ACCEPTANCE CLAUSE LIVES IN THE ITEM'S SECTION, UNDER ITS `### Acceptance` HEADING,
AND THAT SECTION IS ITS SOLE OWNER.** The line carries the literal pointer `in detail` in
the acceptance field and nothing else about what the item requires. CS-971 measured why: a
line cut to fit this file's budget changed what 91 items required, because a clause and its
truncation are indistinguishable once the rest is gone. A clause split across the line and
the section is two owners, and `tools/drift_guard.py` guard (j) fails it either way - a
pointer whose section carries no acceptance, or a clause on a line whose section carries
one. An item filed with its WHOLE clause on the line is still well-formed; a PART of one
never is.

Closed work lives in `docs/LEDGER.md`. Aspirational and conditional-trigger items live in
`BACKLOG.md`. Items blocked on something outside the repo live in `docs/GATED.md`. An item
is in exactly one of those four places.

**THE DETAIL DOES NOT GO ON THE ITEM LINE. IT GOES IN THE `docs/item_notes.md` FAMILY.**
That file is the INDEX; the bodies live in `docs/item_notes/`, one leaf per phase and one
section per item ID, and the index's leaf membership rule says which leaf holds which item. This
file owns the LINE alone - the ID, a short headline, the acceptance pointer and the tier.
Filing an item means writing the line here and the acceptance clause plus the reasoning
THERE, with a short pointer on the line. A headline too long for a readable line is cut to a
COMPLETE short title and the whole original is filed in the section under `### Full
headline`; a title is never a sentence broken off part-way.

**A LINE POINTS AT THE INDEX, NEVER AT A LEAF, AND THAT IS DELIBERATE.** The phase headings
in THIS file are the single owner of which phase an item belongs to, which is what decides
its leaf. Spelling the leaf on the item line would restate that mapping once per item, and a
restated fact is a fact that will drift. One hop through the index is the cost of keeping one
owner.

**Read an item's section BEFORE taking that item**, via the leaf membership rule in
`docs/item_notes.md`. Those sections
are live instructions, not background - several record a wording measured false, a fence
against a re-pitch, or a first attempt that an adversary refuted. When an item CLOSES its section moves to `docs/history_notes.md` with the
ledger entry, which is what keeps that header true.

**ID blocks.** IDs are permanent and never reused. `CS-0nn` is the phase 0 scaffold block
and is closed - those entries are in `docs/LEDGER.md`, not here. Open items are numbered
in the hundreds block matching their phase: `CS-1nn` phase 1, `CS-2nn` phase 2, and so on
through `CS-7nn`. Gaps are expected and are never backfilled.

**`CS-8nn` IS THE FOLLOW-UP BLOCK, because `CS-4nn` FILLED UP** - 98 of 100 used, the two
free being gaps the rule above forbids backfilling. A phase-4 residual goes here, not in
`CS-5nn`, so an ID still says which phase it came from. Operator decision 2026-08-21.
`CS-501` keeps its ID; it predates the block.

**`CS-9nn` IS THE NEXT FOLLOW-UP BLOCK, because `CS-8nn` FILLED UP** - 100 of 100 used,
measured 2026-09-05. Operator decision 2026-09-05, taken deliberately: ADR 0011
anticipated reaching CS-900 and declined to answer it, so the block was opened by the
operator rather than by a session allocating an ID in passing. **CS-901 THROUGH CS-905 ARE
NOT ALLOCATABLE** - they are synthetic fixture IDs in the drift-guard test corpus and
allocating one would collide with a corpus that asserts on them by name. The block runs
CS-900, then CS-906 onward. Gaps are expected and are never backfilled.

**Not listed here:** phase 0, and spikes S4, S6 and S8. All are CLOSED - phase 0 into
`docs/LEDGER.md`, the three spikes as ADRs 0003, 0004 and 0002 respectively. This paragraph
described them as in progress until 2026-08-16, which had been false for eight sessions.

**SIZE.** This file's budget is severity **WARN**: it prints loudly and exits 0, and does
NOT fail CI - both consumers go non-zero only on a HARD budget or a FAIL. The sentence
previously here claimed the opposite and was measured false on 2026-08-16. Act on the warn
anyway; a warn nobody acts on enforces nothing. Relocate, never delete. Do not restate the
budget or this file's size here - read both from the tool.

**Do not advance past a phase whose acceptance criterion is unmet.**

---

## Phase 3 - solver core follow-ups



## Phase 4 - save reader

CS-400 - Phase 4 gate: header, chunks, usmap, objects and world model, unknown classes skipped - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-828 - The trailing run before a payload's declared final byte is unexplained - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-829 - `StructProperty`'s interior is the largest opaque region by count and is read by nothing - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-896 - tier 1 CI was cancelled by its runaway cutoff with nothing failing - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-917 - tier 1's duration is watched but its GROWTH RATE is owned by nobody - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1128 - `_SEPARATE_GUARD_CEILING` bounds a table the derived-bound check cannot see - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-900 - tier 1's cost is concentrated in a few tests, so `-n auto` buys little - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-907 - tier-0 pre-push runs the whole suite while its header claims the sanctioned fast subset - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-920 - this project's own measurements carry provenance at document scope, never row scope - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-938 - the CS-932 inbox watcher is wired only in an untracked file, so a fresh clone runs no watcher - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-937 - a line pointer checked only for non-blankness certified a pointer naming the wrong rule - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-936 - the 2026-08-14 PII scrub edited files forward, so removed world names remain in earlier blobs - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-941 - the watcher is SILENT on a WITHDRAWAL, so a deliverable that leaves the channel simply stops appearing - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-942 - the watcher runs only at `SessionStart`, which fires ONCE, so a note arriving mid-session is invisible until the next start - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-943 - the inbox watcher's seen-store save returns nothing and a write error crashes the session-start hook - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-944 - a leftover worktree lets a tree-walking existence guard pass green on the deletion it exists to catch - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-945 - local branches hold single-copy work that is on no remote - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-946 - charter v4 is adopted and the cs lane slot accepted, reversing ADR-0017 - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-947 - CAVEMAN ULTRA is ADOPTED and needs an adjudicated grant against the frozen `.claude/settings.json` plus a stated interaction with `CLAUDE.md` 2.3 - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-948 - CS owes a reciprocal verbatim payload and has no manifest producer, and an unscrubbed outbound payload is unrecoverable once sent - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-965 - four shipped repr methods render a quantity derived from the player's save - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-966 - CS-210's census of registry-published buildings can drift from what the registry actually publishes - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-967 - a worker running the whole suite locally with -n auto gets a red tree the push hook does not reproduce - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

CS-964 - every save-layer privacy arm hunts an ASCII marker while Unreal writes non-ASCII header strings as UTF-16-LE - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-969 - two live negative-count UTF-16-LE branches in the save reader are driven by no planted-marker arm - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-971 - `ROADMAP.md` is over its soft doc budget - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-972 - the pre-push hook grades the working tree while git ships the commit - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-974 - the queue driver rolls up a cycle's CI verdict against a two-verdict denylist - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-975 - nothing reads the queue driver's exit code, so every number it returns is decorative - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-993 - nothing rations the suite step across concurrent lanes - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-995 - the converse leg of the unpinned eligibility check is ungraded for breadth - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-998 - membership of the independent case-count table is uncertified - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1001 - the CS-1000 repair rests on exactly one lanes module object per process and nothing asserts it - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1002 - the lanes module keeps its ownership entry on a refused release and a refused repoint - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1003 - the by-path lane modules are published under dotted names with no parent package loaded - acceptance: in detail - tier: 3 - detail: `docs/item_notes.md`
CS-1004 - the launch-reason vocabulary is graded by set equality, so a duplicate-valued reason is invisible - acceptance: in detail - tier: 3 - detail: `docs/item_notes.md`
CS-1006 - the claim store's reclaim still has a restore window a filesystem cannot arbitrate - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1007 - the pre-push hook's xdist suite is outside every ration and cannot be brought inside one - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1010 - a lane lock's pid and start-time holder proof fails in both halves together - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1012 - tier 1's unit step cost 133 seconds more after CS-1009: 493s against a 480s ceiling and a 420s budget - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1063 - the memory sync tool defers frontmatter problems to a drift guard check that does not exist - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1092 - the self-spelled citation floor kept its filed value after CS-1066 halved its population - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1094 - the derived-bound check in the bare path guard reports only a narrow set of module-scope shapes - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1067 - the ratio solver's no-single-row-isolates fallback is reachable and untested through its caller - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1069 - a reference-count reach derivation is read from two functions' direct attributes, and a graded reading can still be a cache hit - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1070 - two test modules run a nested child pytest serially under a parent holding -n auto - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1071 - the tier 1 workflow is parsed by two independent hand-rolled readers that never check each other - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1074 - the struct controls revert assertion is only a net while its message presents as the grade - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1075 - the Sphinx role guard grades three of the six role spellings its corpus contains - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1076 - the independent table's no-dynamic-case-reuse check enumerates only its own module's bodies - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1077 - the Sphinx role guard accepts a dotted role target whole once its head is a bound name - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1078 - the two arms stopping the memory sync tool regrowing the link derivation each have a blind spelling - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1129 - the leaf membership rule grammar is closed only at the positions its residue plants perturb - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1119 - two trailing-run remainder shapes are left after CS-828's reference-pair reading - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1121 - the citation Disposition table keys each forgiveness by a site count, never by the sites - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1123 - the CS-898 planting arm proves the tests-tree size ceiling fires but not where it sits - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1125 - the mypy gate's exclude test reports on the ambient environment rather than on its subject - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1089 - `tests/save/test_struct_interior.py` sits above the approach band of the `_MAX_TEST_FILE_BYTES` ceiling in `tests/data/test_phase2_gate.py` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1090 - `tests/save/test_properties.py` sits above the approach band of the `_MAX_TEST_FILE_BYTES` ceiling in `tests/data/test_phase2_gate.py` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1091 - `tests/save/test_world.py` sits above the approach band of the `_MAX_TEST_FILE_BYTES` ceiling in `tests/data/test_phase2_gate.py` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`

CS-962 - the dashboard is a self-diagnostic rather than a player's tool - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-976 - the four panel modules share one global with the app script and one publishes 26 names into it - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-958 - the outbound gate graded nothing because nothing called it, and the channel had no sender - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-959 - GitHub's community-standards checklist for this repository is four of eight - acceptance: in detail - tier: 2 - NOT a CS-700 step, but a precondition of its irreversible one - detail: `docs/item_notes.md`
CS-951 - nobody watches their own outbound withdrawals on the channel - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-877 - no arm enumerates the shell's `insertCSS` call sites, so a second injection is invisible - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-876 - no caller reads the independent oracle's final offset, so a stale reading passes it - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-864 - the static seam arms in `tests/save/test_independent_table.py` scan syntax, not reach - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-865 - `_UNEXPLAINED_WORD_CEILING` is a fitted bound with zero headroom and no skip - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-839 - the suite's verdict depends on which shell invokes it - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-840 - `CLAUDE.md` and `docs/item_notes.md` conflict on the dated-heading rule - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-841 - `tools/edit_lint_check.py` passes `root=None`, so CS-838's check skips - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-842 - CS-837's recorded exclusion criterion is deletable with the suite green - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-843 - an element region with no grammar is partitioned by the declared count alone - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-844 - an owner recorded against a shipped table is checked for the `CS-` prefix only - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-846 - a control whose body becomes an early return stays green - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-847 - an ownership hand-off written as prose is invisible to the owner-id guard - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-848 - the CS-841 tripwire is evaded by any narrower arming predicate - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-849 - the CS-841 fixture creates the repository's work directory on every machine - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-850 - the pytest assertion channel renders values past a counts-only message - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-851 - a save-derived local renders under `--showlocals` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-852 - a shipped dataclass carrying save bytes ships no `__repr__` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-853 - pytest renders a fixture's value in the failure header - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-855 - a caught exception reaches a report by three channels a handler-keyed guard misses - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-857 - `raise X(...) from exc` renders the cause's raw text - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-858 - the CS-857 chained-raise sites in FROZEN files are asserted by nothing - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-859 - `tests/test_redaction_scope.py` is governed by no prose fence - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-860 - the pytest report redactor covers neither the account id nor the world name - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-861 - `clockspeed/data/locate.py`'s `redact()` misses the `%r`-escaped account id - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-854 - Three siblings of the select-by-reader-word defect are unswept - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-832 - `TextProperty` and `Int64Property` are refused on no stated criterion - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-825 - `UInt32Property`'s byte order is recorded as inseparable by any oracle - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-826 - `IntProperty` and `FloatProperty` carry `anchored_not_unique`, not a settlement - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-426 - Give the width discriminators a synthetic payload fixture so they run on a machine with no game - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-432 - Remove the corpus-coupled false red in the usmap join oracle - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-425 - Stop the hook configuration spawning a visible console window on every shell tool call - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-412 - Record the nine remaining opaque spans as resumable DATA rather than as prose - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-401 - Assert world-token stability across a save and reload cycle, and tolerate an unseen token - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`


CS-439 - Detect the silent-loss family mechanically instead of hand-fixing a sixth instance - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-440 - Close the downstream half of CS-435 - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-441 - Extend the exception-rendering sweep to a helper that takes the exception as a PARAMETER - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-443 - Stop `local_config()` silently discarding every operator declaration - acceptance: an oversize, unreadable, malformed or non-dict `config/local.json` is REPORTED through the skip channel rather than returning `{}` in silence, proven by a test that fails against today's code - tier: 1 - detail: `docs/item_notes.md`
CS-444 - Stop `workdir._forbidden_roots()` silently dropping a forbidden root it cannot resolve - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-445 - Bring the ADR 0008 tier-1 violations outside the fenced modules under a rule - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-446 - Make the writer write-surface pin detect a DUPLICATE mutating call, not only a new one - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-447 - Close or bound the two report channels CS-428's redaction does not reach - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

CS-448 - Find the root cause of the `-n auto` flake in the no-install save-suite gate - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`

CS-449 - Close the same fail-open one seam BELOW CS-444, in `locate.resolve_save_root()` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-450 - Decide whether a named FIELD of a caught exception is a rendering - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-451 - Bring `tools/drift_guard.py`'s exception rendering under the same rule as the rest of the tree - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-452 - Give `locate`'s resolvers one return shape instead of two - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

CS-453 - Apply the refuse list to the DELETE path, not only the write path - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-454 - Close the account-directory redaction hole, which is live on `main` today - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`

CS-455 - Close the fixed-width fabrication blind spot - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-456 - Settle the FAMILY of declines recorded on a criterion `WIDTH_SHIPPING_RULE` does not recognise - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-457 - Read `#:` doc-comments in the citation checker, which is blind to them today - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-458 - Bring the ungoverned cursor-advancing widths under the width rule - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-459 - Make the evidence table's tie to the oracles bidirectional, since only over-claiming is caught - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-827 - the evidence vocabulary is not pinned by literal the way byte-order's is - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-460 - Narrow the `any()` claim in `tests/save/test_decode_oracles.py` - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-461 - Give the CS-420 census and its probe an ABSOLUTE floor instead of a relative one - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

CS-462 - Auto-detect an account directory whose name is not all digits - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-465 - Grade the redact-cycle fence against the PRIVATE hops the cycle actually passes through - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-466 - Give the test-harness redactor an account-directory rule - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-467 - Grade the world-load traceback surface for a PATH, not only for planted content markers - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-468 - Stop the 8.3 redaction control skipping on the every-push CI lane - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-464 - Delete the discrimination claim in `tests/test_facts_probe.py` - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-470 - Separate the declared-size census's two surviving orderings - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-472 - Close the decline table's deletion direction, which reaches only the derived population - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-473 - Bring `tests/save/test_properties.py`'s prose under a fence - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-474 - Stop `tests/save/test_value_anchoring.py` transcribing the two shipped oracle pivots - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-477 - Close the reach control's seam, where required oracles are derived but bodies listed - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`


CS-479 - Anchor the byte-order separability derivation to the bytes it claims to read - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-490 - Bound the tag-carried exemption against a consistently CLAIMING module - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-499 - A self-exemption keyed on the guard's FULL PATH is undetected - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-492 - Close the reach routes that travel through an OBJECT rather than a name binding - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-501 - `MODULE_SCOPE_REACH` is one sentinel per file and absorbs further reach - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-488 - Bound the fixed-width table for a type word the module has never NAMED - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-489 - Grade the PROSE inside `objects.UNMEASURED_PAYLOAD_REGIONS` entries - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-483 - `tests/save/test_synthetic.py::test_a_failing_builder_call_renders_its_arguments` is load-sensitive - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-800 - A hand-back resolves a SPELLING only - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-801 - A `__getattr__` serving a locator is closed only at MODULE scope and only in the SAME file - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-802 - A store whose attribute NAME is not a literal is not read - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-803 - A closure built by a nested `def` is not read as serving what it closes over - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-804 - The cross-module EXPORT SET carries only names a sibling's functions CALL - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-805 - The container-FIELD personal-data shape is not walked as a wrapper - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-807 - No ordinary module gains a reach declaration it does not need - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-808 - the reach and wrap name caches are keyed on a `Path`, so a stale parse answers - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-484 - The local lint gate cannot reproduce CI's unbounded `ruff` pin - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-981 - CS-G05 is discharged and CS-829 is still filed as gated behind it, so the chain that answers "what am I holding" is unrouted - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-983 - `CS-G05` is decided out of `docs/GATED.md` and its body has not moved - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-984 - a decoded struct interior reaches no consumer, because the world model publishes none - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-985 - the suite writes copies of the operator's real saves into the live `work/saves/` rather than into a temp root - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-986 - a `StructProperty` tag carrying `TAG_FLAG_NATIVE_SERIALIZE` whose interior still decodes as a tag list is unmeasured - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-982 - two bits of the `(14,60)` property tag flags byte are pinned on almost no evidence - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1052 - nothing records which save record carries the trading post level, though it is declared SaveGame - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1055 - the conftest live-copies teardown infers authorship from a wall-clock count over a shared directory - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1056 - the struct interior independent tag walk expressed only the legacy grammar and read zero sites - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1053 - ADR 0016 is status proposed and carries two statements already measured false - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1122 - our own Python renderer from a hand-authored architecture IR to a static module diagram - acceptance: in detail - tier: 3 - detail: `docs/item_notes.md`


## Phase 5 - advisor and audit

CS-500 - Phase 5 gate: trace engine first, then rules, cards, the ledger, then pillars 3 and 4 - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1043 - the registry excludes schematics and the progress layer holds no code, so no milestone can be named - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1058 - nothing can say which belt feeds which machine or which connections share a power circuit - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1059 - the power panel is production versus consumption and only consumption exists - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1048 - node purity is absent from every save and the in-game map is rendered live, so neither has a derivation - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1061 - the map underlay has no subject in the code - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1064 - the audit balance still reports variable-power and struct-range buildings as unmodeled draw gaps - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

## Phase 6 - surfaces

CS-600 - Phase 6 gate: dashboard first, then the companion - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-603 - `tests/test_scaffold.py`'s `clockspeed/surface/web` exclusion has expired - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-604 - `docs/OPERATIONS.md` restates the ports `config/ports.json` owns, and is unmeasured - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-606 - `clockspeed/surface/__main__.py`'s success path is unexercised - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-607 - `tests/test_mypy_gate.py`'s discovered-set arm fails intermittently in a full-suite run - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-608 - `tests/surface/test_web_assets.py`'s sweep matches Windows shapes only - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-609 - `_spellings_of()` collapses its spellings where the path carries no backslash - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-610 - `tests/conftest.py` leaves a skip report unredacted - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-611 - `allow_reuse_address = False` rests on a Windows measurement and is untested on POSIX - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-612 - `test_the_generated_key_is_restricted_to_this_account` may be tautological - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-613 - every TLS arm sits behind `cert_pair`, so no openssl means no coverage - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-614 - a bind-failure arm asserts over every thread whose name contains `serve` - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-615 - the tier-2 count floor is pooled, so one-test stubs leave every lane green - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-616 - three shipped statements about `callback(0)` cannot all hold - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-618 - `shell/lib/state.js` interpolates untrusted state into its fault strings - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-619 - `shell/main.js` and `shell/preload.js` are executed by no test - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-620 - the Node behaviour suite runs only in tier 2 - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-621 - the tier-2 syntax step and the Python guard enumerate `shell/` differently - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-622 - the forbidden-token sweep is a substring test over eleven literals - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-623 - two arms grade the same 7-bit-ASCII property with different boundaries - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-872 - the composed page opens with no default keyboard scrolling - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-887 - `python -m clockspeed.surface` overloads exit 2 - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-909 - the companion has no desktop entry point that `docs/OPERATIONS.md` permits - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-910 - `tools/toolpath.py` covers seven spawn sites; the item asks it of every external tool - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-913 - unlock state is EMPTY for every save and the cause filed with it is REFUTED - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-914 - `clockspeed/save/workdir.py` stages through a shared partial and can truncate - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-915 - two guards report zero findings for a reason that is not the absence of findings - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-916 - three separate features are gated on ONE unfiled prerequisite in the published model - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`


CS-988 - a value deciding what a population measures is narrowable at its use site while its floor holds - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1046 - the plan and audit endpoints still answer 501 blocked by CS-500 while the layers beneath them exist - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1047 - the map draws bare dots with no underlay, category or elevation ordering, and has no plan or power panel - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

CS-1051 - the audit harness hand-builds the published world dict and hardcodes the game phase as an integer - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`

CS-1065 - the power endpoint serves only the variable power inputs, so the dashboard still reads modeled false - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

## Phase 7 - public flip gate

CS-701 - Resolve the collision between the operator git identity and a world name - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-704 - The trailer gate is client-side, and six git commands route around it - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-811 - The citation guard's pattern-derivation check is a CONVENTION - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-812 - Three citation-guard guarantees live in contract tests, not the arms - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-813 - The commit-msg pre-filter models a cleanup mode git is not using - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-814 - Every git hook inherits the session's live API credentials - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-815 - `.claude/settings.json` hardcodes its interpreter with no probe - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-816 - The interpreter probe is bounded neither in time nor in output - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-817 - The interpreter probe asserts PYTHONHOOD but not TOOLCHAIN - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-818 - `scripts/verify_env.py` never evaluates `CLOCKSPEED_PYTHON` - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-820 - `tests/conftest.py` has NO secret rule - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-821 - `pre-push` decides pytest is available from an exit code alone - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-822 - The commit-msg byte check tests only for bytes ABOVE 0x7E - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-824 - `.githooks/pre-push` proves pytest RAN but not that it DID ANY WORK - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-700 - Phase 7 gate: the tier-3 flip checklist from CONVENTIONS section 17 - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-953 - a history scrub keyed on paths at HEAD leaves every pre-move path unrenamed - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-955 - the pre-commit gate grades the index at hook time, so a stage landing mid-hook commits ungraded - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-956 - three hook properties this project relies on are unmeasured anywhere in it - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1014 - the queue loop's holder-pid type guard is ungraded and its removal survives every arm - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1015 - the lane refusal vocabulary is an unpinned cross-module string contract - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1016 - no arm drives a real lane worktree collision into a cycle end to end - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1017 - a lane cycle row records neither the seconds the wait consumed nor the refusal reason - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1018 - a lane run on the 2026-09-10 night started late and left no worker log - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1019 - the world model's node rotation and scale carry-through has no arm in its own layer - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1021 - the rotation constants in three test modules are non-unit quaternions documented as real values - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1022 - the map panel test body claims the frozen contract shape and binds to neither contract nor endpoint - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1023 - the audit package re-exports an arbitrary subset of the placement warning codes - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1024 - the audit Placement dataclass carries a generated repr invisible to both PII censuses - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1026 - three panel scripts declare their helpers in the page's shared global scope - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1027 - the panel division detectors miss two real spellings - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1028 - the decimal approximation helper exists in four panel files and only one copy is graded - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1029 - the web assets one-post test's name states one post while the test now asserts two - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1030 - the power endpoint restates the shipped exponent and its measured float in prose - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1031 - the audit harness power data binds one reason string to its owner and hand-authors four - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1032 - the panel harness DOM stand-in has no known-good browser control anywhere in the repo - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1033 - `ROADMAP.md` is over its soft budget and has been for some time - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1034 - four anti-leak privacy arms hunt a needle the encoder can never produce - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1035 - the audit inventory module carries CS-1020's ungraded-count shape - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1036 - CS-1025 and CS-1020 enforce their sweeps over a hand-enumerated population - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1037 - the fixture collision CS-1025 was filed over survives in two places the repair did not reach - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
