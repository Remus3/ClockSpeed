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
line cut to fit this file's budget changed what its item required, item after item, because
a clause and its truncation are indistinguishable once the rest is gone. A clause split across the line and
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
CS-900 - tier 1's cost is concentrated in a few tests, so `-n auto` buys little - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1152 - the save shard's most expensive test warns at both ends of the CS-900 profile and no mechanism is named for it - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-907 - tier-0 pre-push runs the whole suite while its header claims the sanctioned fast subset - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-938 - the CS-932 inbox watcher is wired ONLY in an untracked file, so a fresh clone runs no watcher - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-936 - the 2026-08-14 PII scrub edited the files FORWARD, so three world names it removed remain in earlier blobs - CONTAINED, measured - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-941 - the watcher is SILENT on a WITHDRAWAL, so a deliverable that leaves the channel simply stops appearing - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-942 - the watcher runs only at `SessionStart`, which fires ONCE, so a note arriving mid-session is invisible until the next start - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-943 - `save_seen` returns nothing and an `OSError` on write escapes as a traceback out of a session-start hook, so a locked store crashes the watcher - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-944 - ten test modules walk the tree with `rglob` and one excludes the worktree directory - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-945 - local branches hold single-copy work that is on no remote and one `git branch -D` from loss, and a sibling was told this was fixed - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-946 - charter v4 is ADOPTED and the `cs` lane slot ACCEPTED, reversing ADR-0017 - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-947 - CAVEMAN ULTRA is ADOPTED and needs an adjudicated grant against the frozen `.claude/settings.json` plus a stated interaction with `CLAUDE.md` 2.3 - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-948 - CS owes a reciprocal verbatim payload and has no manifest producer, and an unscrubbed outbound payload is unrecoverable once sent - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-965 - four shipped `__repr__` methods render a QUANTITY derived from the player's save while withholding its bytes - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-966 - CS-210's census claims to count the REGISTRY-PUBLISHED buildings, and two independent routes let that population drift from what `clockspeed/data/registry.py` actually publishes without any arm reddening - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-967 - a worker told to pay the whole suite locally reaches for `-n auto` and gets a RED tree that the push hook does not reproduce - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

CS-964 - every privacy arm in the save layer hunts an ASCII marker inside `repr(value)` - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-969 - `clockspeed/save/objects.py::_payload_text` and `clockspeed/save/objects.py::_Cursor.string` both carry a live negative-count UTF-16-LE branch that NO planted-marker arm in `tests/save/` drives, measured 2026-09-11 by reading the wide spelling back through both readers by hand - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-972 - `.githooks/pre-push` grades the WORKING TREE while git ships the COMMIT - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-974 - `ops/loop/queue_loop.py` decides a cycle's `ok` roll-up against `_CI_ROLLUP_BAD`, a DENYLIST of two verdicts - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-975 - nothing reads the `queue` driver's exit code, so every number it returns is decorative - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-993 - nothing rations the suite step across concurrent lanes, and the failure is already measured on this box rather than predicted - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-995 - the converse leg of `unpinned_eligibility_faults` is itself ungraded for BREADTH in both detection and naming - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-998 - `INDEPENDENT_CASE_COUNTS` membership is uncertified: the header asserts that every entry re-derives its size from a DIFFERENT source than the mark reads - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1001 - the CS-1000 repair's correctness rests entirely on there being exactly ONE `lanes` module object in a process - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1002 - `ops/loop/lanes.py` keeps its ownership entry on a REFUSED release and changes no state on a REFUSED repoint - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1003 - `sys.modules.setdefault` publishes the by-path `lanes`, `lane_launcher` and `winmutex` modules under their canonical DOTTED names - acceptance: in detail - tier: 3 - detail: `docs/item_notes.md`
CS-1004 - the launch-reason vocabulary is graded by SET equality, so a duplicate-VALUED `REASON_*` constant is invisible - acceptance: in detail - tier: 3 - detail: `docs/item_notes.md`
CS-1006 - `ops/loop/claims.py`'s `_reclaim` still has a RESTORE window a filesystem cannot arbitrate - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1007 - the pre-push hook's xdist suite is outside every ration and cannot be brought inside one - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1010 - a lane lock proves its holder with a (pid, start time) pair, and both halves fail together: `lanes.proc_started` returns None when psutil is absent - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1012 - tier 1's unit step cost 133 seconds more after CS-1009 than before it and the duration gate is now marginal rather than comfortable: the step went 316.16s over 5719 tests to 449.16s over 5740, the job total ran 493s against a 480s CEILING and a 420s budget, and a re-run of the IDENTICAL commit came in at 470s - AND THAT 20s FIGURE IS MEASURED FALSE, session 95: two same-tree rerun pairs read 222s and 23s apart, so the runner pool is TWO-CLASS rather than continuously noisy, and the repo's own feasibility arithmetic run on those numbers returns an EMPTY window - wall-clock gating is INFEASIBLE at this lane length rather than mis-tuned, which is a different item and it is CS-1060 - but the growth is NOT attributed and that is the finding rather than a caveat: it is spread evenly across tree-walking sweeps that have nothing to do with the change, `test_locals_rendering` 17.9s to 26.1s, the mypy-gate oracle 16.7s to 25.6s, `test_liveness` 15.8s to 24.6s, `test_toolpath` 8.6s to 11.9s, roughly plus 45 pct each, while the delta added about 85 KB to a multi-megabyte tree and the same suites measured LOCALLY at base and at head differ by under 12s in the noise - the WHOLE suite on this box is FLAT across the same delta - 411.54s at the base commit, 404.19s at the merged tip, both through the pre-push hook - so the 133s exists only on the runner and the first hypothesis to test is the environment rather than the tree, and CS-1009's own arms are 4.2s locally for the whole file and none reaches the CI slowest-15 - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1063 - `tools/memory_sync.py` prints FRONTMATTER PROBLEMS and then says they "do not change this exit code, because `tools/drift_guard.py` is the gate that fails on them", and that gate DOES NOT IMPLEMENT THE CHECK - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1092 - `_SELF_SPELLED_FLOOR` in `tests/test_docs_citations.py` stayed at its filed value while CS-1066 halved the population it bounds - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1094 - `derived_bound_problems` in `tests/bare_path_guard.py` reports a bound computed from the table it bounds only for a module-scope `Assign` - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1067 - `ratio._name_unsatisfiable_item`'s no-single-row-isolates fallback is reachable and no test through the caller reaches it - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1069 - a reference-count reach derivation is read from two functions' direct attributes, and a graded reading can still be a cache hit - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1070 - `tests/data/test_phase2_gate.py` and `tests/save/test_workdir.py` each run a nested child pytest SERIALLY - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1071 - `.github/workflows/tier1.yml` is parsed by TWO independently hand-rolled readers that never check each other - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1074 - `test_struct_controls.py`'s revert assertion is only a net and its message presents as the grade, which is the wording CS-870 had to correct next door - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1075 - `tests/sphinx_role_guard.py` grades three of the six Sphinx role spellings its corpus contains and DECLARES the other three rather than reading them - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1076 - `tests/save/test_independent_table.py::_bodies_no_dynamic_case_may_reuse` enumerates only the bodies its own module builds - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1077 - `tests/sphinx_role_guard.py::unresolved_roles` accepts a dotted role target whole as soon as its HEAD is a name the citing module binds - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1078 - the two arms that stop `tools/memory_sync.py` re-growing a copy of the link derivation each have a spelling they cannot see, MEASURED by the CS-892 verifier rather than argued - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1129 - the leaf membership rule grammar in `tools/drift_guard.py` is closed only at the positions its residue plants perturb - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1130 - a relocated acceptance clause is never compared against what its line carried, so a later truncation of a section's `### Acceptance` body is undetectable - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1131 - guard (i) is blind to an id that exists in NO state - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1119 - two trailing-run remainder shapes are left after CS-828's reference-pair reading and neither is derivable by that grammar - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1089 - `tests/save/test_struct_interior.py` sits above the approach band of the `_MAX_TEST_FILE_BYTES` ceiling in `tests/data/test_phase2_gate.py` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1090 - `tests/save/test_properties.py` sits above the approach band of the `_MAX_TEST_FILE_BYTES` ceiling in `tests/data/test_phase2_gate.py` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1091 - `tests/save/test_world.py` sits above the approach band of the `_MAX_TEST_FILE_BYTES` ceiling in `tests/data/test_phase2_gate.py` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1133 - the tier 1 fast shard's warn band is narrower than its own run-to-run jitter - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1134 - the tier 1 jitter figure can UNDERSTATE by two routes the CS-917 verifier found after the candidate was frozen - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1135 - `_oversized_over_the_ceiling` in `tests/data/test_phase2_gate.py` is closed only at its lower edge - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1136 - no guard grades a live document's pointer into an item-notes leaf - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1137 - two arms in `tests/data/test_item_notes_index.py` bind only their constant's MEMBERSHIP in the probe tuple and are blind to its VALUE - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1138 - a survives-next-reading verdict reads `survived` on a pair whose basis is `unproven` - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1139 - a measurement reading's `commit` is regex-checked and never resolved, so a fabricated reading grades clean - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1140 - every tier 1 reading carries an unresolved worker count, so CS-917's figure can never reach a `comparable` basis - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1141 - the per-entry unanchored refusal never proves that the entries after it are still graded - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1142 - the ratchet's head sentence in `tests/test_citation_tables.py` states a composition the tables no longer have - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1143 - the citation site identity derives a markdown heading chain from files that have no headings - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1144 - `docs/LEDGER.md` cites `.github/workflows/tier1.yml` by a line the workflow has since grown past, and the carrier is append-only - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`

CS-962 - the dashboard is a SELF-DIAGNOSTIC rather than a player's tool: it renders its own health, its own route table, six world version scalars, five counts and the unmodelled-class list - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-976 - the four panel modules are classic scripts sharing ONE global with `app.js`, and three of them scope themselves - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-958 - the outbound gate graded nothing because nothing called it, and the channel had no sender at all - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-959 - GitHub's community-standards checklist for this repository is four of eight, and CS-700 flips it public - acceptance: in detail - tier: 2 - NOT a CS-700 step, but a precondition of its irreversible one - detail: `docs/item_notes.md`
CS-951 - nobody watches their own OUTBOUND withdrawals, so a drop this repo pulls from a sibling's inbox is invisible to every watcher on the channel including this one - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
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
CS-1052 - `mTradingPostLevel` is declared `SaveGame` on `AFGTutorialIntroManager` so it CAN be in a save - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1055 - `tests/conftest.py`'s live-copies teardown infers AUTHORSHIP from a wall-clock before/after count over a directory any process may write to, so a long-running `python -m clockspeed.surface` holding that workdir gets its copies attributed to whatever suite happens to be running - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1056 - `tests/save/test_struct_interior.py`'s independent tag walk expressed the LEGACY grammar only - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1053 - `docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md` is status `proposed`, carries two statements already measured FALSE - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1122 - our own Python renderer from a hand-authored architecture IR to a static SVG/HTML module diagram, the re-implementation the CS-1098 decline in `docs/LEDGER.md` filed in place of adopting archify - acceptance: in detail - tier: 3 - detail: `docs/item_notes.md`
CS-1148 - CS-1119's filed headline calls the trailing run's second remainder shape "one class" and it is carried by ten - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1149 - the trailing run's residual population is recorded as ONE shape and is measured to be at least five - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1150 - one residual carrier class's trailing run carries platform account strings in plaintext, so any reader of that region is an echo path - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1151 - CS-828's note says the (14,60) pair reaches a property terminator on NO payload and the walk reaches one on six figures of them - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`


## Phase 5 - advisor and audit

CS-500 - Phase 5 gate: trace engine first, then rules, cards, the ledger, then pillars 3 and 4 - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1043 - `clockspeed/data/registry.py` excludes `FGSchematic` and `clockspeed/progress/` holds no code at all - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1058 - nothing can say which belt feeds which machine or which connections share a power circuit - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1059 - the power panel is production versus consumption and only consumption exists: CS-1045 delivered the exact world draw but found NO `Building` field - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1048 - node purity is structurally absent from every save and the in-game map is rendered live rather than shipped - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1061 - the map underlay has no subject in the code: `mFogOfWarRawData` was proved structurally in a 2026-09-13 probe to be a 1024 by 1024 byte square - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1064 - `clockspeed/audit/balance.py` still reports every variable-power and struct-range building as an unmodeled DRAW GAP - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1235 - plan round-trip proof: a solved plan, materialised as a synthetic world, must audit clean - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1236 - what-if overlay: virtual edits over the real world, recomputed, never written back - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1237 - a fixed-order constraint-relaxation ladder when the planner finds no feasible plan - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1238 - every check proves it can go red: a planted firing fixture per audit warning, and per advisor rule - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1239 - golden-case corpus for ratio, clock and power math, and one pinned display-rounding policy - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1240 - unknown content: stable-id keying, one normalised fallback, and an Unmodelled Content panel - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1241 - build-aware registry variants, and a tracked table of every ambiguous normalisation choice - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1242 - an extraction census: counts per category, a zero-tolerance missing-field audit, docs-versus-save agreement - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1243 - reachability bands and unlock-gated traversal for node siting and claim order - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1244 - a named strategy ladder for ranking plans and cards, each objective an exact formula with a threshold - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1245 - bounded candidate enumeration with deterministic trimming, keeping the smallest passing candidate - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1246 - quick-win card ordering with an aging guard computed from the per-world ledger - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1247 - a deterministic domain interleave in the top-N card list - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1248 - unit-tagged quantities and a single raw-versus-display boundary - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1249 - recipe-graph cycles detected explicitly, with a test that reddens on a new unhandled cycle shape - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1250 - no-double-count invariant: each built object contributes to audit totals exactly once - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1251 - a save-settle grace period: parse only the newest save whose size and mtime are stable - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1252 - a freshness stamp and a stale marker on every card, API response and companion view - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1253 - a versioned per-world ledger and mute store: forward migration, refuse before touch - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

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


CS-988 - a value that decides what a POPULATION MEASURES is narrowable at its use site while the floor guarding it stays satisfied - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1046 - `/api/plan` and `/api/audit` are published in the endpoint table and answer 501 blocked by CS-500 while the layers beneath them now exist - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1047 - the map draws bare dots on no underlay with no category, no elevation ordering, no need-vibrance - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

CS-1051 - `tests/surface/audit_harness.py::SYNTHETIC_UNLOCKS` hand-builds the published world dict and hardcodes `current_game_phase` to the integer 2 - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`

CS-1065 - the power endpoint serves `variable_power_inputs` and nothing else, so a dashboard reading it still sees `modeled` false - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1254 - a coverage matrix for a milestone target: required parts by production line, plus a shortfall row - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1255 - numeric inputs keep what is typed, validate on blur or submit, and accept fraction forms - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1256 - every numeric API field carries the exact rational and the display string side by side - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1257 - shareable view state in the URL fragment, with no personal field ever encoded - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1258 - an accessibility baseline for dashboard and companion - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1259 - the dashboard is one self-contained page with no network fetch at runtime - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1260 - one design-token source consumed by both the dashboard and the companion - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1261 - local API hardening: loopback-only bind, header-only tokens, private refusals, per-install cert subject - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1262 - a privacy-filtered local diagnostics bundle with a preview before writing - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`

## Phase 7 - public flip gate

CS-701 - Resolve the collision between the operator git identity and a world name - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-815 - `.claude/settings.json` hardcodes its interpreter with no probe - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-700 - Phase 7 gate: the tier-3 flip checklist from CONVENTIONS section 17 - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-953 - a history scrub keyed on paths as they exist at HEAD leaves every PRE-MOVE path unrenamed - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1032 - `tests/surface/panel_harness.py`'s DOM stand-in has no known-good browser control anywhere in the repo - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1186 - README.md has never been walked from zero to a first result - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1194 - drift_guard prints a non-numeric player-named directory that holds no sensitive file - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1196 - the provenance manifest's history walk miscounts first-adds across a merge commit - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1197 - `tests/save/test_trailing_run.py` sweeps every real save, so its run time grows with the save library - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1215 - the pre-commit gate run by hand echoes git's own stderr, home path included, through its GitError crash line - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1216 - the slots release fallback docstring says a torn in-place write reads stale; its fresh mtime makes it read held - acceptance: in detail - tier: 3 - detail: `docs/item_notes.md`
CS-1217 - with ruff off PATH the gate runs `python -m ruff` from the staging directory, so a staged `ruff.py` runs in ruff's place - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1218 - a ruff config the gate cannot load makes the gate report PASS while lint did not run - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1211 - `tests/test_hook_probe_bound.py::hangs` reads a slow-but-returning interpreter as hung under load, un-skipping an arm that then fails - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1212 - `tests/test_hook_toolchain.py` kills its commit at a fixed bound plus slack that counts pre-hang start-up under load, the CS-1201 defect one module over - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1213 - the save shard's named-first arm in `tests/test_tier1_budget.py` asserts a dispatch order that pytest-xdist 3.8 reorders away - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1202 - the PostToolUse lint hook's `--files "$CLAUDE_FILE_PATHS"` argument may always be empty under the live harness - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1204 - `/api/health` still waits on a full save parse on a cold start - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1205 - pre-push does not scrub `PYTEST_ADDOPTS`, so an operator `-l` renders test locals - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1206 - a test run by pre-push can print an environment value outside any assert - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1207 - the hook environment allowlist lists known readers, so an unlisted reader such as `os.path.expandvars` escapes it - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1208 - a personal value the hook allowlist lets a program read can still reach a print, log or report - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1228 - the nightly tier2 full suite is shallow-checked-out and its windows legs outrun a 30-minute cutoff, so the lane has not been green since 2026-09-24 - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1229 - the tier2 full suite is one job per OS, so suite growth outruns its measured cutoff within days - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1230 - `tools/flip_checks.py` names a child tool and a clone source by a path relative to the cwd, which raises across Windows drives - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1231 - adopt MAIN's FLEET-KIT (vendor the kit, embed the common block in CLAUDE.md, route every headless spawn through it) - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
CS-1233 - the CS-815 latency arm read over budget on windows tier2 because xdist siblings contend; it now times after siblings go quiet - acceptance: in detail - tier: 2 - detail: `docs/item_notes.md`
CS-1234 - the inbox responder publishes its inbox-status file (MAIN 0915) and caps headless starts at 120 per rolling 24 hours - acceptance: in detail - tier: 1 - detail: `docs/item_notes.md`
