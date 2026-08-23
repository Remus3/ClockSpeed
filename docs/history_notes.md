# Clockspeed - History notes

**Deep archive. Pruned session notes and retired ledger entries live here.**

**This file holds NOTHING current.** Nothing in it may be cited as the present state of
the project, and nothing may be acted on without re-verifying it live against the source
of truth first. Everything here has already been superseded, pruned, or archived out of a
living file - that is the only reason a line is in this file at all.

Where current truth actually lives:

| Looking for | Read |
|---|---|
| Current rules, constraints, settled decisions | `CLAUDE.md` |
| The last few sessions at full fidelity | `WAKEUP_NOTES.md` |
| Closed work, newest first | `docs/LEDGER.md` |
| Open work | `ROADMAP.md` |
| Live detail for an OPEN item | `docs/item_notes.md` |
| Blocked outside the repo | `docs/GATED.md` |
| Module map and seams | `docs/ARCHITECTURE.md` |
| Commands and runbooks | `docs/OPERATIONS.md` |

---

## CS-486 - detail - CLOSED 2026-08-23

**CS-486 CLOSED 2026-08-23 - see `docs/LEDGER.md`. This block is the record of how it
was filed and is NO LONGER A LIVE INSTRUCTION.** It closed on an operator ruling that
the page-GROUP list plus the reading order is the watch list clause 1 asked for. The
standing watch itself did NOT move here and is not history: `docs/upstream_watch.md`
owns it, and that file is where the list is read.

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-486 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated to `docs/upstream_watch.md` 2026-08-23

The CS-486 watch list moved to its own file under the same operator ruling, because
it is a STANDING watch rather than per-item detail: it outlives the item that filed
it. `docs/upstream_watch.md` owns it - the page groups, the ordering that makes them
useful, and the standing refusal of any automated fetch. Read it before taking this
item; the verbatim block that used to sit here is its source-of-record section.


---

## Live per-item detail moved out - 2026-08-23

**Relocated, not deleted.** Under an operator ruling of 2026-08-23 every LIVE instruction
block in this file moved to `docs/item_notes.md`, which now owns live per-item detail.
This file's header says it holds nothing current; those blocks were the half that made
that false, and they are gone rather than the header.

A block for a CLOSED item stayed here, because a closed item's detail IS history.

Moved: CS-210, CS-400, CS-401, CS-405, CS-412, CS-425, CS-426, CS-432, CS-439, CS-440, CS-441, CS-443, CS-444, CS-445, CS-446, CS-447, CS-448, CS-449, CS-453, CS-454, CS-455, CS-456, CS-457, CS-458, CS-459, CS-460, CS-465, CS-467, CS-468, CS-470, CS-472, CS-473, CS-477, CS-479, CS-484, CS-486, CS-488, CS-490, CS-492, CS-500, CS-501, CS-701, CS-704, CS-800, CS-801, CS-802, CS-803, CS-804, CS-805, CS-807, CS-811, CS-812, CS-813, CS-814, CS-815, CS-816, CS-817, CS-818, CS-820, CS-821, CS-822, CS-825, CS-826, CS-828, CS-829.

Read `docs/item_notes.md` under the item ID. Do not re-add live detail to this file.

---

## Session 23 wakeup note - relocated 2026-08-21 (session 26)

Relocated from `WAKEUP_NOTES.md` for the two-to-three-session rule, not deleted. Session 26 also REORDERED that file to the newest-first order its header has always stated; sessions 23, 24 and 25 each recorded the contradiction and each declined to resolve it, and the operator ruled on 2026-08-21 that the entries were the wrong half.

## Session 23 - 2026-08-19 - CS-487, CS-478 and CS-471 CLOSE; every refutation pass succeeded and one refuted an acceptance clause outright

- **Shipped: CS-487 CLOSED.** Filed CS-490. Two arms landed in
  `tests/save/test_byte_order_status.py`, not one. Suite with the library
  **2142 passed, 3 skipped, exit 0**; `tests/save` with NO GAME **1059 -> 1060 passed, 49
  skipped, exit 0**. mypy clean 28 and 56, ruff check clean, ruff format clean 84, drift guard
  **CLEAN 9/9**, doc budget **PASS measured 16** after a relocate pass, precommit gate PASS.
  Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THAT ONE ARM WAS NOT ENOUGH AND I SHIPPED THE FIRST DRAFT BELIEVING IT
  WAS.** The `MEASURED_VALUE_TYPES` conjunct reds the filed three-line route and does NOTHING
  against an attacker who PICKS a word already in that table instead of adding one. A
  refutation pass measured that live: three shipped lines plus two test-side, naming a
  LENGTH-PREFIXED type, shipped `vacuous_one_byte` with the tree green - which is CS-480's own
  defect reached again. The fix was widening the derivation's saturation arm from the
  fixed-width table alone to every table the module reads a value out of the payload from.

- **FOUR OF MY OWN SENTENCES WERE MEASURED FALSE BY THE SECOND PASS AND ARE CORRECTED IN PLACE
  WITH THE REFUTATION BESIDE THEM.** Do not rewrite them back: an eight-line price measured on
  a tree WITHOUT the new arm and carrying the wrong tree's pass count; calling
  `MEASURED_VALUE_TYPES` hand-authored when it is DERIVED and the same test module already said
  so; handing the residual to CS-488, whose acceptance is scoped to a width-table entry neither
  surviving route touches; and a pointer chain in which three prose sites each said a different
  one of them owned the price.

- **THE PRICE IS THE RESULT, NOT THE CLOSURE.** The exemption cost three lines in one file and
  now costs seven across two. No route through it is closed, both survivors were taken all the
  way to GREEN rather than left at their first red, and they are CS-490. Read that item's
  detail before touching this area.

- **A COUNT CS-487 WAS FILED WITH DID NOT REPRODUCE.** Its detail block said `tests/save` 1058
  with no game; I measured 1059 four times, on two trees. The RELATION it asserted - forged
  tree byte-identical to clean - reproduced exactly. Corrected in place at
  `docs/history_notes.md` under **CS-487 - detail**.

- **THIS FILE'S STATED ORDER AND ITS ACTUAL ORDER DISAGREE, and I did not silently pick one.**
  The header says NEWEST FIRST; sessions 21, 22 and 23 run oldest first, and did before this
  session touched it. I appended to match the ACTUAL order rather than reorder three blocks
  under a rule I may be misreading. One of the two is wrong and it is an operator call which.

- **CS-478 ALSO CLOSED, later in the same session.** The two definitions of "an oracle scores
  this type" - tag-word in `test_properties._tally_decoded_values`, decoded-shape in
  `test_value_anchoring._score_population` - now meet in
  `test_the_two_admission_rules_for_the_int32_oracle_never_disagree_unrecorded`. Closed on the
  HOLD-THEM-APART route, not unification: the item's own fence forbids deleting either.

- **THE WORST MISTAKE OF THE SESSION WAS IN CS-478 AND BOTH REFUTATION PASSES CAUGHT IT
  INDEPENDENTLY: I ACCUSED A TRUE SENTENCE OF BEING FALSE.** A draft rewrote
  `test_the_cannot_separate_set_is_bounded_without_a_library`'s docstring to say that
  `test_no_type_an_oracle_scores_is_left_recorded_as_unscored` says nothing about the word the
  cannot-separate set names. Widening the dispatch to score that word reds that very test. The
  sentence GOVERNS THE TRANSITION while being silent on today's state; present non-membership
  of a runtime-computed population is not silence. Restored verbatim. **This project's method
  says corrected-in-place sentences must never be rewritten back - a false correction is the
  same defect pointing the other way.**

- **FOUR MORE CS-478 SENTENCES OF MINE WERE MEASURED FALSE and are corrected in place.** Do not
  rewrite them back: a probe constant said to move BOTH channels of the int32 oracle when its
  low byte is non-zero so only one fires; a subset arm whose stated route raises `TypeError`
  before the assertion and which NO edit to `objects.py` can fire; a reverse arm called hard to
  reach that fires three ways; and an absolute suite count that distinguished nothing.

- **CS-478's residual, stated as an adversary put it:** one more line turns the `unscored` lie
  into a `cannot_separate` lie. The control prices CONCEALMENT, not the lie. CS-426 owns it.

- **CS-471 ALSO CLOSED, on its THREE STATED CLAUSES and not on the channel being shut.** The
  parameter-and-locals channel stays open and its pinning test
  `test_the_entry_points_still_bind_the_raw_body_where_a_renderer_can_read_it` STILL PASSES and
  stays. Residuals filed as CS-491. Operator ruled the close on the three clauses.

- **A REFUTATION PASS REFUTED CLAUSE 1 OUTRIGHT AND IT WAS RIGHT.** The scan read module-body
  statements only, so a module-scope reach was invisible - and the classifier called that module
  SILENT, so the guard never ran on it. The proof of concept was the ordinary pytest idiom, a
  module-scope call feeding a parametrize list. Closed under a `MODULE_SCOPE_REACH` sentinel
  wired into BOTH the guard and the classifier. **Fixing a guard without fixing the thing that
  decides which files the guard runs on is half a fix that measures green.**

- **I SHIPPED A NON-NEGOTIABLE 12 VIOLATION WHILE CLOSING A PRIVACY ITEM.** An f-string rendered
  a caught exception object; `OSError.__str__` appends the path it failed on. Caught by
  `tests/test_exception_rendering.py`, which lives OUTSIDE `tests/save` - so a `tests/save` run
  was green while it was there. **Run the whole suite before believing a privacy change.**

- **EIGHT EXEMPT REASONS OF MINE WERE MEASURED FALSE, plus four more defects.** Do not rewrite
  them back: six reasons described filesystem work on functions matched only by a NAME COLLISION
  with a sibling's citation resolver; one described the game install for a synthetic usmap in
  tmp_path; one claimed tmp_path containment for a test passing no path, whose real containment
  is an autouse env fixture. Also: the wrapper walk missed a subclass; the clause-2 control was
  a tautology reporting every input undeclared; the package walk was narrowable to one module in
  silence; and a docstring said "third argument" of two.

- **Next action:** take CS-491 (tier 1), CS-471's filed residual - read its detail in
  `docs/history_notes.md` first. CS-488 and CS-490 are the other open tier-2 byte-order items.

## Session 18 - wakeup note, relocated

Relocated whole from `WAKEUP_NOTES.md` on 2026-08-19 (session 21), which keeps the last
two to three sessions only.

## Session 18 - 2026-08-18 - CS-476 closes after TWO refutations broke it; CS-421's population derived

- **Shipped: CS-476 CLOSED.** CS-421 STAYS OPEN, with its deciding population DERIVED this session
  and recorded on its ROADMAP entry. Suite 2065 -> **2073 passed, 3 skipped, exit 0**, serial AND
  under `-n auto`, baseline re-measured by me at `ed25c19` before any work. Drift guard **CLEAN 9/9**,
  doc budget **PASS measured 16**, mypy clean 28 and 84, ruff clean. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THAT THE GUARD WAS REFUTED TWICE, BY TWO DIFFERENT AGENTS, AND THE SECOND
  REFUTATION LANDED AFTER THE FIRST REPAIR WAS BELIEVED FINAL.** Six routes shipped an unbacked
  byte-order claim green. THREE were pre-state holes at 1032. **THREE WERE HOLES IN THE GUARD
  ITSELF** - the swallowed one-byte set member, the vocabulary swap, and a FOURTH STATUS WORD - all
  green with the guard already present. Do not report CS-476 as having caught six things; it caught
  three, and independent passes caught the three it shipped.

- **THE FOURTH-WORD ROUTE IS THE ONE WORTH REMEMBERING.** Pinning three status spellings does not
  BOUND the vocabulary. Adding `settled_uniquely` for `UInt32Property` - a type no oracle scores -
  ships a claim STRONGER than the over-claim CS-476 names, and every graded direction passes
  VACUOUSLY, because they all select by the one anchored symbol. `BYTE_ORDER_STATUSES` cannot close
  it: hand-written, same file, extended by the same edit. The mapping's VALUES are now bounded to
  three literals. **CS-421's route (b) will want a new word and WILL redden this** - that is the
  designed behaviour, not a bug: add the word together with whatever grades it.

- **CS-421's REMAINING HALF IS DECIDED BY A MEASUREMENT, AND IT IS ROUTE (b).** Derived from the
  library this session: `UInt32Property` yields **9 values carrying ONE distinct stored byte
  pattern**. The 9 matches the archived session-14 figure and that is a COINCIDENCE OF
  RE-MEASUREMENT, not a carry-forward. Every value has a ZERO HIGH BYTE UNDER BOTH READINGS, so the
  shipped int32 magnitude oracle - a CONJUNCTION needing a MINORITY under the swapped reading - is
  provably VACUOUS on this type's own population. That is threshold-free and it is what the status
  word should record. **Rest the close on the ORACLE being vacuous, never on the population being
  SMALL** - one pattern is not invariant under the group, so an oracle over it still returns a
  number, and "small population" is the `_JOIN_WORD_FLOOR` shape CS-432 exists to delete.

- **Surprises**, each measured:
  1. **A SUBAGENT'S REFUTATION WAS ITSELF WRONG AND I CAUGHT IT BY RE-MEASURING.** The second pass
     reported that nothing grades the BALANCE of the two byte probe pairs. An unbalanced pair
     reddens the neutering control, which requires the derived population to be EMPTY with the
     tallies dead. Recorded in the module and the ledger: an unchecked refutation is as bad as an
     unchecked claim.
  2. **I SHIPPED AN UNMEASURED "MEASURED" SENTENCE INTO THE LEDGER AND CAUGHT IT BEFORE COMMIT.**
     The entry said five routes were green BEFORE the module; I had measured four. Measuring the
     fifth exposed a worse error in the same sentence - two of the routes were green WITH the
     module present, so they were guard holes rather than pre-state holes.
  3. **MY OWN DERIVATION READ TWO OF THREE ORACLES AND CLAIMED THREE.** Both probe bytes had EQUAL
     interior bytes, which is exactly the population coarseness declines, and an early return ran
     the byte channel only for words the value channel had already declined. Zero coarseness calls.
     Every other test stayed green because the word coarseness scores is scored by magnitude too -
     right answer, wrong reason. A CALL COUNT closed it; a sentence would not have.
  4. **A HAND-WRITTEN LABEL SET INSIDE THE GUARD LET THE GUARD DISARM ITSELF.** Two lines - revert
     the probe pairs, drop one label - restored the exact previously-refuted state, suite green. The
     set is now derived by AST from the shipped dispatch bodies.
  5. **I CORRUPTED A MEASUREMENT BY DISPATCHING TWO MUTATING AGENTS AT ONE CHECKOUT.** One
     overwrote the other's in-flight mutant. BOTH agents detected it independently and neither
     reported the bad number; one rebuilt in a licensed clone. **RULE: concurrent agents may share a
     checkout only if NONE of them writes to it.** Every later pass ran in `git clone --no-hardlinks`
     with the live uncommitted files overlaid, licensed by reproducing the live count first.
  6. **A `git archive` REPLICA IS NOT A VALID MEASUREMENT TREE HERE** - a missing `.git` produces
     unrelated failures. Clone, then license the clone.
  7. **THE CITATION BLOCK MADE THE PRE-STATE RECIPE SELF-INVALIDATING.** `objects.py` now cites the
     new module by path, so moving the module aside to re-derive the old green reddens the
     package-wide citation resolver and the phase-4 gate behind it. Those failures are NOT the
     byte-order question. Take a pre-state at a commit before the block, or delete both together.

- **Failed paths - do not retry:**
  - **Pinning status spellings and calling the vocabulary closed.** It is a swap detector; it does
    not bound the value set.
  - **A hand-written label set inside a guard.** Derive it from the thing under test.
  - **A cheap `or` that short-circuits a probe channel.** It ran the unreached half only where it
    could not fire.
  - **Two agents mutating one checkout.**
  - **Taking a subagent refutation at face value.** One finding of three did not survive.

- **A THIRD REFUTATION LANDED AFTER THE SECOND REPAIR AND FOUND THREE MORE, TWO NOW CLOSED.** The
  fatal one used NO new status word, so nothing that grades words could fire: `vacuous_one_byte`
  against `StrProperty` - length-prefixed, carrying an int32 length - retires a byte-order question
  with zero evidence, green at `tests/save` 1040. **THE HOLE WAS MINE:** my key assertion admitted
  any `MEASURED_VALUE_TYPES` word. Keys are now bounded EXACTLY to the fixed-width table plus the
  one tag-carried one-byte value. Also closed: `BYTE_ORDER_STATUSES` is exported and was unbounded
  even though the mapping's VALUES were bounded - two artifacts, one bound.

- **THE REAL PATTERN, AND IT IS THE SESSION'S MOST TRANSFERABLE FINDING: EACH REPAIR MOVED THE
  HAND-WRITTEN SEAM UP ONE LEVEL RATHER THAN REMOVING IT.** Label set -> site list. The reach
  control's oracle NAMES are derived from the dispatch bodies, but WHICH BODIES is still a
  hand-written tuple, so two line deletions inside that one test module restore the
  zero-coarseness-call state, and an ordinary extract-method refactor hides a tally from the scan
  while every control passes. Filed as **CS-477**, with the third finding - `_PROBE_VALUE_PAIRS` is
  graded by nothing and 3 of its 5 shapes are inert. **A fix that names a population IS the defect.**

- **THREE REFUTATIONS, THREE SUCCESSES, AND THE COUNT IS THE POINT.** Nine routes shipped an
  unbacked byte-order claim green across the session. THREE were pre-state holes; **SIX were holes
  in the guard itself**, every one found by an independent pass rather than by the author. Do not
  record CS-476 as a clean build. The third pass also independently RE-MEASURED and CONFIRMED the
  correction that the probe-pair balance property IS graded, so that stands at two measurements.

- **Next action: CS-421's remaining half, route (b)**, using the derived census above. It needs a new
  status word plus a library-backed test deriving the vacuity, and adding that word WILL redden
  `test_the_status_words_are_pinned_and_distinct` until it is added to `_GRADED_STATUS_WORDS` with
  its grading - by design. `objects.py` cannot read the library without breaking the seam, so the
  module ships the word and the test derives the verdict, which is the CS-476 pattern. On a machine
  with no game that test skips - CS-426's gap. After it, **CS-471** (tier 1, privacy-adjacent);
  note `tests/save/test_byte_order_status.py` does NOT enlarge it - measured library-free by an
  audit hook - but it DOES enlarge **CS-473** by 24 unbacked quantified sentences.

## Session 17 wakeup note - relocated 2026-08-18 (session 20)

Moved out of `WAKEUP_NOTES.md` when session 20 landed and that file's two-to-three
session window closed over it. Relocated, not deleted.

## Session 17 - 2026-08-17 - CS-469 and CS-475 CLOSE; CS-421 stays open on the type nobody scored

- **Shipped: CS-469 CLOSED, CS-475 CLOSED.** CS-421 STAYS OPEN with a ledger record declaring the
  non-closure by name. Filed CS-476. Suite 2035 -> **2065 passed, 3 skipped, exit 0**, serial and
  under `-n auto`, baseline measured by the merger itself at `86c9e54` before any slice ran and the
  delta reconciling exactly as 22 + 8. Drift guard **CLEAN 9/9**, doc budget PASS, bare mypy clean
  over 83 files, ruff clean. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THAT BUILDERS REFUSED REVIEWER PRESCRIPTIONS THREE TIMES AND WERE RIGHT EVERY
  TIME.** Twice on CS-469 against the merger AND the verifier together, once on CS-475 against the
  merger. Each refusal was a MEASUREMENT, not an argument. The transferable rule: when a reviewer
  specifies HOW to fix rather than WHAT PROPERTY MUST HOLD, the specification is usually defeatable
  and the agent holding the code is the one who can see it.

- **CS-469's real difficulty was never the finding, it was grading it.** The answer - the identity
  `(0,1,2,3)` - was correct and stable from the first build and was re-derived by three independent
  routes. What failed, four times, was the control: a green displaced census. Bypasses ran 4 lines,
  then 6, then a nested-scope parameter shadow (`ast.arg` is not `ast.Name`), each found only
  because someone went looking after the previous closure was believed final. The shipped fence is
  three structural rules - one cut of the body, one offset expression, one binding of `value_at` -
  and the module now enumerates them rather than claiming an absolute, because it claimed one twice.

- **THE MERGER SEEDED A FALSE SENTENCE INTO ITS OWN DISPATCH, AGAIN, AND THEN PRODUCED TWO MORE
  WRONG VERSIONS OF IT.** "The middle swap moves only the exponent's LSB, so it can change a
  magnitude by at most a factor of two" was written by the merger, propagated to FOUR sites, and is
  false - 24% of values move by more than 2x on corpus, and off corpus the flip crosses the
  subnormal and infinity boundaries (ratio 256, finite -> inf). The merger's first correction,
  "bounded by approaching 4", was also false. The builder's replacement justification was false a
  third way: it cited `float32_plausible_if_swapped` (4425 of 31318, 14.13%) as showing the band
  admits both readings on most values, when that count is the WHOLE-WORD REVERSAL rather than the
  middle swap and the assertion beside it requires it to be a minority. **Delete was not enough;
  the fix was to forbid a number and point at the derivation.**

- **Surprises**, each measured:
  1. **A BUILDER'S OWN PRESCRIBED FIX WOULD HAVE SHIPPED THE HOLE OPEN.** Plumbing the offset into
     the tally makes slice and reference move together: `misread=0`, the value grade provably blind.
     Single-slice ownership is what makes a displacement collapse both magnitude oracles instead.
  2. **`git worktree remove` DELETES THE `.git` MARKER BEFORE THE FILES** - 8/8 rounds showed a
     populated, unmarked window. A boundary rule relying on the converse of its own statement is
     false for the duration of every teardown.
  3. **A TEST SUITE BECAME A WRITER OF SHARED GIT STATE.** CS-475's first control ran
     `git worktree add/remove/prune` against the real repo root three times per suite run - CS-448's
     own mechanism, automated, and it probably explains a `locked` file that vanished unexplained.
  4. **THE MERGER'S OWN MEMBERSHIP RULE REOPENED THE DEFECT.** tracked-or-not-ignored only worked
     because the harness directory happens to be gitignored; at an un-ignored path the teardown
     window reopens. The builder measured that rather than implementing it. Three rules were needed.
  5. **A pid in a plant path landed in the pytest NODE ID** and broke `-n auto` collection - the
     exact CI invocation the module's own docstring cited. `--collect-only -n auto` passes on both
     trees and does not catch it.
  6. **THE MERGER GENERALISED ONE AGENT REPORT INTO A STANDING LESSON WITHOUT MEASURING IT.** The
     claim that bare `mypy` catches what targeted `mypy` misses did not survive the verifier: the
     targeted form catches it too, and the suite catches it via `test_mypy_gate`'s repo-wide shell
     out. The true lesson is narrower - **ruff does not type-check** - and the gate test is what the
     suite inherits mypy through. It was caught before reaching the ledger.
  7. **CS-421's remaining work was on its own list since session 14 and nobody had struck it.**
     `UInt32Property` is a four-byte type the same reader decodes and no oracle scores.

- **Failed paths - do not retry:**
  - **Prescribing a fix mechanism to a builder without stating the property.** Three for three.
  - **Deleting a false measured sentence and letting someone write a replacement justification.**
    Forbid the number; point at a derived fact the suite reddens on.
  - **A grader sited beside a slice.** It can always be pointed at a different local. Remove the
    degree of freedom instead.
  - **Naming a harness directory, or relying on one being gitignored, to bound a walk.**
  - **Any `git worktree add/remove/prune` against the live repo from a test.** Build a repo in
    `tmp_path`.
  - **Verifying parallel safety with `--collect-only -n auto`.** It passes while the real run fails.

- **Next action: CS-476**, and take it BEFORE the `UInt32Property` half of CS-421, so the status
  artifact is fenced before anyone edits it. It is cheap, library-free and TDD-able: the failing
  test is the adjudicator's own mutant. Then CS-421's remaining half - either an oracle scoring
  `UInt32Property`, or a DERIVED status word distinguishing "no oracle written" from "population
  cannot separate", with the count derived at runtime and NOT the archived `9` from session 14.
  After that **CS-471** (tier 1, privacy-adjacent), whose surface this session ENLARGED: three
  library-reaching helpers were added to `tests/save/test_value_anchoring.py`, which still does not
  call `_assert_library_reach_is_declared`. Measured this session: 8 of 16 modules under
  `tests/save` reach the library and 5 declare.


## CS-496 - detail

Relocated from `ROADMAP.md` 2026-08-20 (session 24) for budget, not deleted.

**CS-496 CLOSED 2026-08-20 (session 25) - see `docs/LEDGER.md`. This block is the record of how
it was filed and is no longer a live instruction.** Both candidate fixes it names were taken,
and the cause turned out to be more specific than the block says: `git commit` DETACHES
`git maintenance run --auto`, so the template keeps a background process after its fixture has
returned.

CS-496 - `tests/test_doc_budget.py`'s scratch-repo fixture copies a LIVE git directory and races git's own background maintenance - acceptance: the fixture cannot fail because a file inside `.git` vanished between the walk and the copy, and the reproduction is recorded - tier: 2 - NOTE: filed 2026-08-20 (session 24). **MEASURED, not suspected:** CI run 32346100111 on `dc5237b` errored with `shutil.Error: ... '.git/objects/maintenance.lock' ... [Errno 2] No such file or directory`, at `tests/test_doc_budget.py:203`, where `shutil.copytree` copies a session-scoped template checkout. `copytree` stats the tree and then copies it, so any file git removes in between kills the fixture - and `maintenance.lock` is exactly such a file, created and deleted by git's own housekeeping. **THE COMMIT THAT HIT IT CHANGED TWO MARKDOWN FILES AND NO PYTHON**, so this is a property of the fixture rather than of any change. **RE-RUNNING THE SAME JOB PASSED**, which is what makes it a flake rather than a break, and is also why it will be tempting to ignore. It is the CS-483 shape - a test that fails for a reason unrelated to what it grades - and every such failure spends a session's trust in the suite. `ignore=shutil.ignore_patterns` over `.git` housekeeping files, or copying with `dirs_exist_ok` and a retry, are the obvious candidates; neither is measured.

## Session 24 - relocated from WAKEUP_NOTES.md

Relocated 2026-08-21 (session 27) because a fourth session landed and that file holds the last two to three at full fidelity. Relocated, never deleted.

## Session 24 - 2026-08-20 - CS-491 CLOSES after THREE rounds; two refutation passes refuted it and both were right

- **Shipped: CS-491 CLOSED.** Forty-seven controls, relocated into a new
  `tests/save/test_reach_guard.py`; one exemption in `tests/save/test_workdir.py`. Filed
  CS-492, CS-493, CS-494 and CS-495. `tests/save` with NO GAME **1064 -> 1111 passed, 49
  skipped, exit 0**. Detail in `docs/LEDGER.md`.

- **THE BASELINE REPRODUCED EXACTLY** before any of it: 1064 passed, 49 skipped with no game.

- **I CLOSED IT WRONG TWICE AND SHIPPED NEITHER.** Round one closed the seven filed routes;
  a refutation pass found ELEVEN more and was right about all eleven - I reproduced every
  one before touching anything. Round two closed those; a second pass found the TWELFTH and
  ten more, and was right again. Round three closed those. **The item is the guard's
  credibility, not the diff, and a green suite after round one would have been a lie.**

- **THE SAME DEFECT FOUR TIMES: ONE MECHANISM APPLIED TO ONE OF TWO POPULATIONS.** Aliases
  resolved to a fixpoint for PRIMITIVES and not for TYPES, so `_Body = bytes` switched the
  wrapper walk off. The module-handle import shape resolved for REACH and not for WRAPPERS.
  The sibling export keyed on the DIRECT set, so a graded-but-indirect helper never
  exported. **And the worst: `_module_scope_reaches` re-derived the callee name itself with
  the pre-CS-491 two-channel test while `_calls_any` had grown five channels - so every
  route I had closed reopened by moving it one indentation level out of its `def`.** This is
  the CS-477 pattern, found four times inside the repair for it.

- **THE FIX FOR THE LAST ONE IS THE SHAPE TO COPY.** I first replaced the callee node-type
  enumeration with `_stands_for_a_primitive(callee)` - a WALK - and it flagged thirteen
  innocent functions, because a RECEIVER is a mention: `THIS_MODULE.read_text()` reads as
  reach when `THIS_MODULE` is itself an alias. That would have manufactured thirteen false
  reasons. Replaced with `_callee_resolves`, a RECURSIVE STRUCTURAL question that asks the
  same thing of a smaller callee. **A guard that names a population is the defect; a guard
  that walks everything manufactures reasons. The answer is recursion, not either list.**

- **EIGHT SENTENCES OF MINE OR MY PREDECESSORS' WERE MEASURED FALSE AND ARE CORRECTED IN
  PLACE.** Do not rewrite them back: `_calls_any`'s claim that a bare-reference matcher
  "flags every forced-failure grader" (measured 1 of 31 - those graders name the primitive
  as a STRING, which is neither a Name nor an Attribute node); a citation to a test that
  does not exist; "eleven tracked modules import it this way" (measured EIGHT; eleven is the
  count of modules the classifier calls reaching, a real measurement of a different thing);
  `_DECLARED_COMPANION`'s present-tense claim that its presence is what makes the controls
  measure the route (true of the pre-CS-491 guard, false of the shipped one); the module-scope
  `lambda` recorded as invisible to the guard (it is VISIBLE and files under the sentinel,
  naming no function, which is worse in one way); and the `test_workdir` exemption's claim
  about which directory the test lists.

- **TWO OF MY CONTROLS WERE TAUTOLOGIES AND A REFUTATION PASS PROVED IT.** The personal-data
  vocabulary's positive half was `_carries_personal_data(f"{word} | None")`, which reduces to
  `word in word + " | None"` and is true for any string - a vocabulary naming nothing
  personal passed it. And the `vocabulary-constant` control claimed to hold the bound stated
  in `_resolves_by_string`; widening that predicate to walk its arguments left the whole
  suite green. Both replaced with assertions that fail: the first walks a synthetic class per
  word, the second asserts the bound of the predicate itself.

- **AN ENUMERATION NOBODY PINS CAN BE NARROWED IN SILENCE, AGAIN.** Dropping `memoryview`
  from `_PERSONAL_DATA_TYPES` AND its parallel entry from the defeat matrix left the suite
  green, one test lower, with CS-491's own wrapper defeat number two reopened. Pinned now
  with a second spelling, deliberately - a pin that reads the list it pins is not a pin.

- **THIRTY MUTANTS, AND TWO SURVIVED EARLIER PASSES.** Both were closed by adding the route
  that isolates the branch rather than deleting the branch: the `getattr`-through-a-NAME
  channel, live only where the primitive is handed back UNCALLED; and the store-annotation
  read, live only where the store's annotation is the sole statement of the type. **The first
  draft of that second route reddened on `_Wrapped.__init__` rather than the caller, because
  its value was itself a primitive call - a red for the wrong reason is not a measurement.**

- **THE PRIVACY PASS CAME BACK NOT REFUTED**, verified at runtime rather than by reading: an
  audit hook over 73 accessed paths, interception of 158 write events, and forced frame
  rendering. Zero reads of the save root, zero writes outside tmp_path, zero rendered paths.
  It handed over one real gap outside its own lens (the indirect-export hole, now closed) and
  one unenforced assumption: ten new f-strings interpolate a caught `AssertionError`, safe
  only because the guard formats function names, and `tests/test_exception_rendering.py`
  cannot see that shape. **Now enforced** - the mutant that adds `module_path` to a guard
  message reddens a control.

- **THE SIZE CEILING WAS 288 BYTES AWAY WHEN I ARRIVED.** `test_properties.py` tripped
  `tests/data/test_phase2_gate.py`'s 256 KiB cap, which exists to catch a trimmed slice of
  real game data. Relocated the controls per CLAUDE.md section 4 rather than raising the
  number, which would have falsified the comment justifying it. **It is still tight. That is
  CS-495 and the next session should expect to trip it.**

- **CS-484's PREMISE IS MEASURED AT LAST, and the item is still open.** Extracted from the tier1 log on `76fac74`: **CI resolves ruff 0.16.3, this machine has 0.15.12**. Three sessions carried that gap as UNVERIFIED because nobody had read it out of a CI log. Both linters passed this tree, so the gap cost nothing on this push - which is NOT evidence it is harmless, only that this tree does not touch a rule they disagree on. Pinning is now cheap because the number is known; it needs `scripts/verify_env.py` to move with `pyproject.toml`.

- **CI WENT RED ON A MARKDOWN-ONLY COMMIT AND IT WAS NOT MY CHANGE.** Run 32346100111 errored in `tests/test_doc_budget.py`'s scratch-repo fixture: `shutil.copytree` races git's own background maintenance, and `.git/objects/maintenance.lock` vanished between the walk and the copy. Re-running the same job passed. Filed as **CS-496**. It is the CS-483 shape - a test failing for a reason unrelated to what it grades - and the tempting response is to ignore it, which is how a suite stops being believed.

- **THE HARNESS HEREDOC ATE MY BACKSLASHES THREE TIMES**, twice on small payloads with quoted
  delimiters. Write such payloads with the Write tool; this is the third session it has bitten.

## Session 25 - relocated from WAKEUP_NOTES.md

## Session 25 - 2026-08-20 - CS-495 CLOSES; a refutation pass refuted the first close and was right, and the hole it found was older than the item

- **Shipped: CS-495 CLOSED.** The library-reach guard implementation moved out of
  `tests/save/test_properties.py` into a new NON-TEST module `tests/save/reach_guard.py`; five
  controls moved into `tests/save/test_reach_guard.py`. Filed CS-497 and CS-498. `tests/save`
  with NO GAME **1111 -> 1115 passed, 49 skipped, exit 0**. Detail in `docs/LEDGER.md`.

- **THE BASELINE REPRODUCED EXACTLY** before any of it: 1111 passed, 49 skipped with no game,
  and 2144 / 52 for the whole suite.

- **THE MOVE IS MACHINE-CHECKABLE AS A MOVE.** Fifty-six top-level definitions left
  `test_properties.py` and every one is BYTE-IDENTICAL to its pre-move source, verified by
  parsing both trees. The collected node-id set lost NOTHING - five tests changed module, four
  were added. Do the same diff on any future relocation; it is cheap and it is the only thing
  that distinguishes a move from a rewrite.

- **A REFUTATION PASS REFUTED THE FIRST CLOSE WITH A COUNTER-EXAMPLE AND IT WAS RIGHT.** A test
  planted in `reach_guard.py` runs ZERO TIMES and nothing says so - pytest does not collect a
  module that is not named `test_*`, and no gutting guard reads it. Pre-move the guard's owner
  WAS a collected test module, so the property was graded. **The class is older than the item**
  - the same plant in `tests/save/synthetic.py` survives on `1e05233` too - but the
  guard-owning file's membership in it is new. Closed by
  `test_no_module_the_collector_skips_defines_a_test`, which covers both modules and both
  shapes.

- **THE SECOND FINDING WAS A MARGIN, NOT A HOLE, AND IS WORTH THE SAME ATTENTION.** An
  undeclared reach planted in the guard's own file reddened ELEVEN tests before the move and
  ONE after, because `reach_guard.py` cannot carry the per-module splice control every consumer
  carries. The property was still graded and the margin was one test wide. Restored by
  `test_the_guard_catches_an_uncontained_helper_spliced_into_its_own_source`.

- **I DELETED A STALE COUNT ON A RULE AND AUTHORED A NEW ONE IN THE SAME FILE IN THE SAME
  COMMIT.** The prose pass measured it: I removed "five module constants of `test_properties`"
  citing CLAUDE.md section 4, and four hundred lines away wrote "in the name of sixteen" - the
  walk covers eighteen. **Knowing the rule is not applying it.** Both numbers are gone now.

- **THREE MORE SENTENCES OF MINE WERE MEASURED FALSE and are corrected in place.** Do not
  rewrite them back: a claim that each consuming module keeps three checks, when only TWO of
  the five call `_assert_no_test_is_gutted` at all; a `:func:` role that stopped resolving when
  the guard moved one file away; and "THIS MODULE'S OWN planted control" in a module that
  plants nothing.

- **TWO PRE-EXISTING HOLES WERE FOUND BY READING THE MOVED CODE, both measured on BOTH trees.**
  CS-497: the vocabulary partition is a TAUTOLOGY in its inclusion direction - `_LIBRARY_PRIMITIVES`
  is derived as locators plus vocabulary minus exclusions, so the assertion reduces to `A <= B | A`
  and an unclassified name is silently made a reach primitive. The suite DOES go red on that
  mutant, on two `test_workdir` tests that have nothing to do with the partition - a red for the
  wrong reason. CS-498: the guard cannot detect a self-exemption in its own source, because every
  control runs it against a `tmp_path` copy under a different filename.

- **THE MOVE CHANGED THE SUBJECT OF THREE OTHER RECORDS AND THEY ARE RE-POINTED.** CS-494's
  acceptance named a symbol that moved; CS-473's subject was one module's prose and is now
  three; and two earlier LEDGER entries cite tests at paths that changed - corrected by the new
  entry rather than by editing them, since that file is append-only. **When you relocate code,
  grep the open items and the ledger for its symbols before you close.**

- **A KILL IS NOT A MEASUREMENT UNTIL YOU KNOW WHICH TEST DID IT.** My first mutation battery
  ran with `-x` and every mutant reddened on
  `test_phase4_gate::test_the_save_suite_passes_with_no_install_and_no_save`, which reruns the
  suite in a CHILD process and so reddens on almost anything. Deselect it when attributing.

- **CS-496 ALSO CLOSED, later in the same session.** The cause is more specific than the item
  was filed with: `git commit` DETACHES `git maintenance run --auto`, so the session-scoped
  template keeps a background git process after its fixture returned, dropping lock files under
  `.git/objects` while later tests copy the directory. Fixed in two halves - housekeeping off in
  the template, and a copy that skips a file which has ceased to exist. **The race is reproduced
  DETERMINISTICALLY**, by deleting the lock from inside `copytree`'s own `ignore` callback, which
  fires after the walk and before the copy. Three mutants, all killed by the intended test.

- **CLOSING CS-496 REQUIRED WIDENING A GUARD, AND THE TEMPTING ROUTE WAS ONE THE GUARD ITSELF
  DOCUMENTS AS A HOLE.** `test_the_suite_never_mutates_this_repository_worktree_admin` demands
  every `_git` call target the identifier `repo`; binding `repo = repo_template` would have gone
  green and is bypass 1 in that guard's own list of what it cannot see. Widened in the open
  instead, with the reason on the constant.

- **CS-497 AND CS-498 ALSO CLOSED, both filed earlier in this same session.** CS-497: inclusion in
  the reach set is DECLARED now rather than derived by subtracting the exclusions, so a vocabulary
  name classified nowhere reaches nothing and is named in the red. **The assertion the fence
  protected was not deleted - the derivation was repaired under it, and it now bites.** The reach
  set is unchanged, checked directly. CS-498: two byte-identical spliced copies of the guard's own
  source, differing only in filename, must get the same verdict; the basename comes from the
  guard's code object and is named nowhere. Residual filed as CS-499.

- **A DERIVATION CANNOT BE GRADED BY ASKING IT ABOUT ITS OWN CONSTANT.** One that absorbs an
  unclassified name and one that rejects it give the same answer on the shipped vocabulary. Making
  `_reach_primitives` take the vocabulary as an ARGUMENT is what let a control hand it an invented
  name, and is what turned a tautology into a measurement.

- **I SHIPPED A NON-NEGOTIABLE 12 VIOLATION AGAIN, IN THE SAME SHAPE SESSION 23 RECORDED.** The
  first draft of the CS-498 control bound the guard's failure in an `except` handler and rendered
  it with `str(caught)`. `tests/test_exception_rendering.py` caught it and that module is OUTSIDE
  `tests/save`, so the `tests/save` run was green while it was there. **Use `pytest.raises`, whose
  AST shape that guard cannot see into, and RE-RUN THE MUTANTS after an idiom change** - a rewrite
  can cost a control its teeth.

- **CS-493 AND CS-494 ALSO CLOSED. CS-493 TOOK TWO ROUNDS AND THE REFUTATION PASS ON ROUND ONE WAS
  RIGHT.** Round one widened the declaration reader to walk the whole value for anything name-shaped
  and justified it with a sentence measured FALSE: "an over-read can never manufacture a reacher,
  because `_reaching_names_of` returns `graded & (direct | indirect)`". **THE INTERSECTION IS
  CIRCULAR** - `indirect` comes from `propagating`, which comes from `graded`, so widening `graded`
  widens the set it is intersected with. Reproduced: a module where NO function calls a primitive
  exported a reacher, and an importer was told to declare a reach for a function touching nothing.
  Round two reads KEY POSITIONS only and refuses what it cannot place.

- **A DATUM IS NOT A BOUND UNTIL A CONTROL SPENDS THE DEFAULT.** The hop-bound control passed
  `hops=` explicitly on both assertions, so a tree declaring a bound of two while every default
  spent one was FULLY GREEN. Fixed twice over: the control now takes the DEFAULT, and pins BOTH
  sides - a chain of exactly the declared length must resolve at the default, which no smaller
  default can do. **The same defect had already bitten this item once** as a fixed-length chain.

- **CS-493's clause 2 was LIVE, not latent.** The new cross-check reddened on arrival naming two
  tracked modules whose declarations the reader could not follow - one keyed on `f.__name__`, one
  built by a comprehension over a `(label, function)` table, which is literally the shape the
  acceptance names. Both spellings exist for good reasons; the reader was wrong.

- **CS-494 closed on the RECORD-AND-GRADE branch, and the coverage half turned out free.** Widening
  `_retained_body_attributes` to the tuple target, the `@property` accessor and the bytes-LIKE
  vocabulary adds NOTHING on the shipped save modules - measured before shipping it. Five of six
  disagreements went away; the item's detail block named three, the merger measured six. The
  survivor is a difference of SUBJECT and is recorded with its reason.

- **THE CS-4nn ID BLOCK IS FULL AND THE /done RITUAL CAUGHT ME COLLIDING WITH IT.** 98 of 100 used;
  the only two unused are GAPS, which CLAUDE.md forbids backfilling. I filed the sentinel residual
  as CS-500 and that ID has belonged to the PHASE 5 GATE for a long time. The older item keeps it
  and mine is renumbered CS-501. **Which block phase-4 follow-ups continue into is an OPERATOR
  DECISION and nothing in the tree settles it** - check the block before filing the next item.

- **Next action:** CS-492, the last of CS-491's residuals and the largest - three shapes reproduced
  ESCAPING this session with a declared companion beside each, so probe with one or every route
  reddens on the guard's vacuity assertion instead. Then CS-499, CS-500, and CS-484 whose premise is
  measured and whose pinning is now cheap.

## Session 26 - relocated from WAKEUP_NOTES.md

Relocated 2026-08-22 (session 27 continued) because a fourth session entry landed and that file holds the last two to three at full fidelity. Relocated, never deleted.

## Session 26 - 2026-08-21 - CS-492 is BUILT in full and does NOT close; six refutation rounds, five of them mine to answer

- **Shipped: NOTHING CLOSED, and that is the result rather than a shortfall.** CS-492's
  acceptance is built, controlled and mutation-covered, and the item stays OPEN because
  ROUND SIX IS UNGRADED. Six grading rounds ran; every one returned REFUTED and every one
  found something real. Closing on an ungraded round is the mistake this ledger keeps
  recording. Filed CS-800 through CS-805.

- **THE HEADLINE IS THAT THE GUARD WAS MANUFACTURING DECLARATIONS, not that it was missing
  routes.** A declaration is a written claim about where personal data flows, so a false
  reacher is worse than a missed one, and this item produced EIGHT of them across rounds
  three to five. The worst was measured on the real tree: `monkeypatch.setattr(os, "walk",
  os.scandir)` - three ordinary lines - took `tests/save/test_phase4_gate.py` from nine
  flagged functions to twenty. `walk` is excluded BY NAME in `_NOT_LIBRARY_REACH` precisely
  because `ast.walk` is how every AST guard here reads a tree, and CS-497 made
  `_reach_primitives` INTERSECT so an unclassified name reaches nothing. **The attribute
  vocabulary I added had no partition, no map and no intersection**, so the exclusion was
  bypassed by the back door. An exclusion that holds in one namespace and not the other is
  not an exclusion.

- **ONE DOOR ACCOUNTED FOR SIX OF THE EIGHT.** The three-argument store shape read
  `f(target, "name", value)` as a store - which is what `setattr` is, and equally what
  `getattr(spec, "reader", open)`, `re.sub(pattern, "count", text)` and `OSError(13,
  "denied", path)` are. It produced a false reacher in THREE separate rounds with a
  different payload each time. It is gone; `_attribute_stores` read 160 stores on this tree
  and 127 were that shape, so it now reads 33. Two shipped controls died with it and are
  recorded in CS-802 with the measurement, not quietly dropped.

- **THE ROOT CAUSE IS ONE SENTENCE AND IT IS NOT NEW.** `_stands_for_a_primitive` treats a
  primitive's RESULT as standing for one, and justifies it by saying that costs a flag "only
  where the bound name is itself CALLED, which no module in this package does". The
  vocabulary is therefore full of PATH CONSTANTS. A hand-back is exactly the place that
  justification fails. Four rounds were spent deleting arms - the call arm, the container
  arms, the subscript/conditional/fallback arms - before round six did the thing those
  deletions were substituting for: `_serving_names` builds a SECOND, narrower name set from
  the primitives outward by the hand-back rule itself. That is the callable-versus-value
  split, computed where it can be.

- **THREE OF MY OWN SENTENCES WERE MEASURED FALSE AND ARE CORRECTED IN PLACE.** Do not
  rewrite them back. `_reaching_attributes`'s stated cost bound ("costs a flag only where a
  module binds a locator to an attribute name and then calls something else of that name")
  was broken by a counter-example holding no locator at all. `_returned_values` claimed
  `yield from` walks "a container of spellings" while `_hands_back_a_primitive` refuses
  containers outright. And a `strings` switch documented as structural was set correctly at
  ONE of three call sites in the commit that introduced it.

- **THE MEASUREMENT THAT MATTERED MOST WAS THE ONE THAT SAID NOTHING HAPPENED.** The
  widening adds zero attributes, zero serve-aliases, zero newly-flagged functions and loses
  zero coverage across all 18 modules - re-measured after every round, with the harness
  proven able to report non-zero on a planted module first. That zero is real and it is also
  weak evidence: a refutation pass showed the tree sits ONE ORDINARY LINE from a false flag,
  and then produced the line.

- **A CONTROL STOPPED COVERING THE THING IT WAS WRITTEN FOR, silently.** Closing the
  attribute fixpoint in round six meant the hold-and-serve chain no longer needed a second
  round of the OUTER fixpoint, and a mutant setting that loop to `range(1)` went green. The
  mutant was proved non-equivalent and `an-alias-of-a-server` now carries that bound. A
  passing control is not evidence that the bound it was written for still has one.

- **Failed paths, so they are not retried:** keying the store shape on the callee (measured,
  leaves every other store helper open); turning the container arm back on (measured, two
  false reachers from two different channels); a per-caller `strings` switch (set wrong
  immediately); scoping the attribute vocabulary per CLASS (needs receiver typing that
  `_callee_resolves` refuses elsewhere).

- **Suite, no game: `tests` 2190 passed / 52 skipped / exit 0; `tests/save` 1155 passed / 49
  skipped / exit 0.** With the library, 2239 passed / 3 skipped / exit 0. mypy clean 86,
  ruff check and format clean repo-wide, drift guard CLEAN 9/9, doc budget PASS measured 16
  after four relocate passes, precommit gate PASS 5. 24 mutants, all killed, no survivors,
  against a green pristine floor. Controls in `test_reach_guard.py`: 63 at HEAD, 95 now.

- **Decisions: the operator opened the `CS-8nn` follow-up block** because `CS-4nn` is full
  (98 of 100, the two free being gaps the rule forbids backfilling), and ruled that
  `WAKEUP_NOTES.md`'s ENTRIES were the wrong half of its four-session contradiction. This
  file is now newest-first as its header always said; session 23 relocated to
  `docs/history_notes.md`.

- **Next action: GRADE ROUND SIX.** Dispatch a refutation pass against the working tree - not
  against HEAD, which is round zero - on both lenses at once: what still escapes, and what
  the widening falsely flags. If it comes back clean, CS-492 closes on its acceptance and the
  ledger entry cites `tests/save/test_reach_guard.py::test_a_primitive_reached_through_an_object_is_named_by_the_guard`
  plus `::test_the_object_routed_widening_does_not_flag_a_module_that_reaches_nothing`.

## Session 27, continued wakeup note - relocated 2026-08-22 (session 30)

## Session 27, continued - 2026-08-22 - CS-492 rounds seven to nine all REFUTED; the bare-name conflict is MEASURED IRREDUCIBLE and CS-807 takes the false-flag direction

**This entry is newer than session 28's below it.** Session 27 resumed after session 28 had
closed and pushed; its commits `6680182` and `31f0e2a` sit on top of `5a5de5f`. Nothing in
session 28's entry is superseded.

- **Shipped: NOTHING CLOSED, for the second session running, and it is the result rather than a
  shortfall.** CS-807 was FILED. Rounds seven, eight and nine of CS-492 were BUILT, each graded
  on two independent lenses, and every one returned REFUTED on a real defect. All three remain
  UNCOMMITTED in worktrees by operator decision so nothing unproven enters `main`. Zero `.py`
  files were touched in `main` across the whole session.

- **THE THREE NUMBERS THAT DECIDED EVERYTHING, all reproduced by the merger rather than taken
  from a builder.** The `_ANY_ATTRIBUTE` sentinel manufactures **268** false declarations across
  six real modules from FIVE ORDINARY LINES of PEP 562 - measured 47 flagged before, 315 after.
  The bare-name class that consumed nine rounds manufactures **EIGHT**. And **FOUR** false
  declarations are LIVE ON THE SHIPPED TREE in `tests/save/test_oracle_citations.py`, whose own
  reason strings say "It opens no file and touches no path at all". The guard was never
  repaired; the false flags were written down and shipped as exemptions.

- **THE BARE-NAME CONFLICT IS MEASURED IRREDUCIBLE. DO NOT SPEND A TENTH ROUND ON IT.** Two
  narrowing spikes were measured against round nine - FIVE-SITE and TWO-SITE. Both take every
  manufactured-declaration payload to ZERO, including `import stat` plus the exec-bit constants,
  which is verbatim real repo code at `scripts/install_hooks.py:44` and `:206`. Both cost the
  SAME TWELVE controls. **Narrowing five sites to two retires NONE of them**, and the mechanism
  was verified rather than inferred: the patched arm is the only consumer of evidence for a bare
  vocabulary word. Two-site DOMINATES five-site - same kills, same reds, smaller diff, one extra
  route kept - so if the hypothesis is ever adopted, adopt it at two sites.

- **THE CONFLICT, STATED ONCE SO IT IS NOT REDISCOVERED.**
  `test_a_parameter_spelled_like_a_primitive_binds_nothing_and_serves_nothing` demands BOTH that
  `stat` as a PARAMETER manufacture nothing AND that `stat = os.stat` at module scope BE CAUGHT.
  Same token, name-keyed guard. Telling them apart needs the type resolution this repo has
  declined. Nine rounds were attempts to split that hair and the measurement says it does not
  split.

- **ROUND NINE'S ENGINE SURVIVED CONTROL-VALIDITY GRADING; ITS PROSE DID NOT.** 38 mutants
  against the builder's 19 found NO new defect, no weakened assertion, no lost control, renames
  clean, the sole survivor proven genuinely equivalent, and termination LOUD rather than hanging
  - 252 `RuntimeError`s where round eight once hung. It was refuted on two documentation defects:
  it ships a provenance claim it declares false 345 lines later in the same file, and it left
  THREE citations to `_value_bound_names`, a function it deleted, one of them the opening
  sentence of a control it added in the same change. **The stale provenance claim is INHERITED
  and is live on `main` today**; the stranded citations are round nine's own.

- **THE PROGRESSION, so nobody re-derives it:** round six certified ANY binding; seven any
  MODULE-SCOPE binding; eight any binding STATEMENT; nine any binding whose value SPELLS a
  vocabulary word. The rule was never value-aware, only LITERAL-aware - `stat = "open"` certifies
  and `stat = "chunks"` does not, and the shipped control grades exactly the one literal that
  misses. Displaced four times, repaired zero times.

- **Failed paths, so they are not retried:** deleting the `def`/`class` admission from
  `_value_bound_names` - reds `a-hold-and-serve-chain-two-rounds-deep` at `2 failed, 1179 passed`;
  splitting locators from raw vocabulary - broken by `def resolve(): return locate.resolve_save_root`,
  a genuine server spelled with a vocabulary word; and the two-site narrowing as a cost reduction -
  it retires nothing.

- **METHOD, EARNED: GRADE A CLAIM AT THE GRANULARITY THE CLAIM IS MADE AT.** A module-level probe
  told the merger a subscript escape did NOT reproduce; it did. The planted `__getattr__` reached
  on its own account, so the module flagged either way. Only calling
  `_assert_library_reach_is_declared(path, graded={}, exempt={})` directly and reading
  `caught.args[0]` separated pristine from mutant.

- **A PROBE GOES STALE THE MOMENT THE RULE CHANGES.** The merger's `except_target` probe read
  SILENT on round nine and looked like a hole. It is not: `except ValueError as stat` binds the
  caught EXCEPTION INSTANCE, never a primitive, so declining it is correct under a value-aware
  rule. The probe was written to catch round seven's regression and outlived its premise.

- **TWO BUILDER CORRECTIONS TO THE MERGER'S OWN BRIEFS, both right.** The round-nine brief
  asserted "these 15 routes are all currently CAUGHT and I verified that myself" - `except_target`
  was not. And the seed control the merger specified for round nine had SILENTLY DECAYED INTO
  DECORATION: a different bound now blocked its mutant, so it separated nothing. Builders that
  implement the brief verbatim would have shipped both.

- **Suite at `31f0e2a`, no game, run this session from scratch: `tests` 2190 passed / 52 skipped /
  exit 0.** mypy clean 86 and 28, ruff check and format clean, drift guard CLEAN 9/9, doc budget
  PASS measured 16, precommit gate PASS non-vacuously via `--files`. Every skip is environmental -
  no game install or no save library - or the mypy gate's empty gap record.

- **Documentation: TWO relocate passes in ONE DAY.** `ROADMAP.md` went 9 bytes -> 2647 -> 97
  (session 28 filed into it) -> 5426 -> 4090. Nine notes relocated byte-identically across the two
  passes. The file is structurally at its ceiling and the budget is severity WARN so CI never says
  so; filed to `BACKLOG.md` with the `docs/history_notes.md` header contradiction beside it.

- **Next action: TAKE CS-807, and take the SWEEP first.** Whether those four false exemptions are
  the only ones on the shipped tree is UNMEASURED - they were found by following one control's
  failure, not by looking. Sweep every module under `tests/save` for an exemption whose reason
  string denies touching the filesystem, before any repair is designed. Then the sentinel, which
  is thirty times the bare-name class and untouched by every round and both spikes.

## CS-809 - detail

Relocated from `ROADMAP.md` 2026-08-22 (session 30) for budget, not deleted. The item itself stays
OPEN in `ROADMAP.md`.

Filed as CS-442's disclosed residual, MEASURED rather than assumed: `docs/history_notes.md` carries
17 distinct `path::name` citations, 4 of which do not resolve.

**THE REASON IT WAS EXCLUDED IS THE ITEM, not laziness.** That file is the deep archive, and its
detail blocks QUOTE dead names while discussing them - the CS-442 block quotes four of them, which
is most of the file's dead population. So quoting and citing are indistinguishable BY SHAPE there,
and a guard that cannot tell them apart is RED ON CORRECT HISTORY. That is the failure mode this
project has already named as the one that gets a guard switched off, and it is why the file was
left out rather than forced in.

**WHAT CLOSING IT ACTUALLY NEEDS**, so the next session does not rediscover it: a way to mark a
name as QUOTED rather than CITED. The CS-442 guard's `DELIBERATE` disposition is the nearest
existing mechanism - it already covers a citation that asserts an ABSENCE - but it is keyed per
citation, and a detail block quoting four names would need four entries that say nothing more than
"this is prose". A block-level marker is probably the right shape. Do not close this by adding the
whole archive to `GUARDED_DOCS` and dispositioning every quote: that trades one unguarded file for
a table of forgiveness entries nobody can audit, which is the CS-807 shape.

**SUPERSEDED 2026-08-22 - THE RECORDED-UNGUARDED ROUTE WAS BUILT, NOT THE BLOCK MARKER.** The
paragraphs above stay as the record of how the item was filed; their instruction half is no longer
live. This archive stays unguarded on the reason the paragraphs above already give and that the
recorded exemption now states in one line: its dead pointers sit inside detail blocks whose SUBJECT
is a pointer being dead, so quoting and citing cannot be told apart by shape here, and guarding it
would mean dispositioning every quote - a table of forgiveness entries nobody can audit, which is
the CS-807 shape. A marker would also have to be inserted into the deep archive, which exists to be
a faithful record rather than a place to keep guard machinery.

**ONE ARGUMENT MADE FOR THAT CHOICE WAS RETIRED THE SAME DAY IT WAS WRITTEN, and it is recorded
here because a retired argument left standing gets re-used.** The first draft of this block argued
that guarding the sink while the SOURCE stayed open would redden a pure doc-hygiene move, since
`WAKEUP_NOTES.md` feeds this file and was itself unguarded. `WAKEUP_NOTES.md` is now guarded, so
a block relocated here arrives already checked and that argument supports nothing. The
quoting-versus-citing reason is what carries the decision, and it is the only one the exemption
record states.

**WHAT WAS BUILT INSTEAD, and the weight is in the second half rather than the first.** This file
is named in `tests/test_docs_citations.py::UNGUARDED_DOCS` with its reason. Beside it,
`tests/test_docs_citations.py::guarded_set_problems` asks the question one level up from every
other contract in that module: not whether a citation resolves, but whether the file carrying it is
looked at by anything. Every in-domain markdown file carrying a pointer in ANY spelling that module
judges is either guarded or recorded, checked in BOTH directions - a record for a file that has
since been guarded, or that no longer carries a pointer, FAILS. So the unguarded set can neither
grow in silence nor linger after it stops being earned, and guarding this archive later is a
one-line change that the contract now FORCES rather than forbids.

**IN ANY SPELLING IS LOAD-BEARING, AND IT WAS WRONG ON THE FIRST BUILD.** The boundary asked the
PATH pattern alone, which needs a module name and a double colon in front of the identifier. A doc
carrying only an elided pointer, only a bare `grep -c` identifier or only a line pointer was
therefore not a carrier at all - never reported as unguarded, and, worse, a maintainer who
correctly recorded one was told the record was stale and to delete it. That is a right answer
turned into a wrong one by a guard. `tests/test_docs_citations.py::JUDGED_SHAPES` is the repair,
and it is not a hand-written list of four: a contract walks that module's own compiled patterns and
fails on any that the boundary does not read, so the NEXT arm cannot fall out the way the elided
one did.

**THE FIRST RUN OF THAT CONTRACT FOUND SOMETHING THIS ITEM DID NOT KNOW: the archive was NOT the
only unguarded carrier.** `WAKEUP_NOTES.md` was one too, and it was first RECORDED unguarded on the
stated reason that every citation in it resolved. THAT REASON WAS FALSE WHEN IT SHIPPED. The notes
spend the header-scan identifier from the CS-436 rename - the one whose live target is
`tests/test_precommit_gate.py::test_the_header_scan_time_bound_declares_the_scope_it_actually_has`
- and the tree binds the old spelling nowhere. The citation module's own disposition table already
recorded that exact name as dead under its ledger key, so the exemption contradicted, in prose, a
fact the same module held in a machine-checked table eighty lines away. It shipped inside the
module whose own comment says an exemption nothing verifies is how a false declaration ships. The
dead spelling is deliberately NOT written out here: this archive is unguarded precisely because
quoting a dead name and citing one cannot be told apart by shape in it, so every quote added is one
more forgiveness entry owed by whoever guards it later.

**IT WAS NOT REPAIRED IN PROSE.** Rewriting the reason would have left a record that still nothing
checks. `WAKEUP_NOTES.md` was moved into the guarded set instead, at a measured cost of exactly one
disposition pointing at the live target the ledger entry for the same rename already names; its
path and line-pointer arms were both clean. The recorded-unguarded set is now this archive alone,
and a contract keeps it that way, so a second exemption has to be a deliberate edit with a written
reason rather than a line that lands while the suite stays green. The residual the first draft left
open - whether a file rewritten whole each session should be guarded at all - is answered by the
measurement: the churn was never the risk, the unchecked claim was.

## CS-810 - detail

Relocated from `ROADMAP.md` 2026-08-22 (session 30) for budget, not deleted. The item itself stays
OPEN in `ROADMAP.md`.

Filed as CS-442's disclosed residual. A citation written as a bare `::name`, with no path in front
of the separator, falls between both arms of the CS-442 guard BY CONSTRUCTION rather than by
oversight:

- the `path::name` arm requires a `<path>.py` before the `::` and matches nothing;
- the bare arm's lookbehind deliberately excludes a name preceded by `:`, precisely so it does not
  re-judge the right half of a full citation under a second rule and report one defect twice.

**LIVE TODAY, NOT HYPOTHETICAL.** The CS-411 correction record spends
`::test_the_exclusion_is_discovery_only_not_containment` in exactly that form.

**NOTE THAT INSTANCE IS DELIBERATE** - the record cites the name to prove it is DEAD, and
`grep -c` returning 0 is its evidence. So closing this needs the same absence-versus-assertion
distinction the guard already draws, and a naive fix that simply widens the bare arm's lookbehind
would redden that correction record for doing the right thing.

**SUPERSEDED 2026-08-22 - THE SHAPE IS READ NOW, and it was not one instance.** The paragraphs
above stay as the record of how the item was filed. The arm is
`tests/test_docs_citations.py::ELIDED_RE`, and it does not stand beside the bare arm so much as
join it: both draw their population from `tests/test_docs_citations.py::judged_bare_names`, so the
elided spelling is judged by the same rule as the bare one and the two callers that need that
population cannot drift apart. The filing called this ONE live instance. It is not - the elided
form is the ledger's ordinary PATH-ELISION IDIOM, one full citation followed by `::name` for
further tests in the same file, and it is how most of that file's bare identifiers are written.
Nearly all of them name a live test, which is why the widening had to be measured before it was
believed rather than after.

**THE PATH IS NOT RECOVERED, and that is the design rather than a shortcut.** Resolving `::name`
against the last full citation seen manufactures findings on CORRECT records, because a paragraph
may interleave an unrelated full citation while the elisions that follow still mean the earlier
file. So an elided pointer is asked the question that needs no path at all - does the tree bind
this name - which is exactly what the bare arm already asks. That is also why the metasyntactic
`path::name` and `path::test_name` placeholders survive: they are below the same length floor that
keeps ordinary words out of the bare arm, so the documentation of the rule is not judged by it.

**THE DELIBERATE INSTANCE THIS BLOCK WARNS ABOUT SURVIVED UNTOUCHED, because the disposition is
keyed on the NAME and not on the spelling.** The first of the two names the CS-411 correction
record cites to prove them DEAD was already forgiven at its bare site inside a `grep -c`, and
inherited that forgiveness at its newly visible elided site with no new entry. Its sibling in the
same record needed one, for exactly the reason the paragraph above predicts: that name is spelled
ONLY in the elided form, so the guard had never once seen it. Neither is spelled out here, and the
omission is the point - in an archive where quoting and citing are indistinguishable by shape,
every dead name written down is one more entry owed by whoever guards this file later.

**A LATER REPAIR NARROWED THAT FORGIVENESS, and it is recorded here because the paragraph above
reads as an endorsement of it.** One key covering many sites is right for the two names above and
wrong in general: keyed on `(doc, name)` alone, a brand-new and genuinely dead citation at a NEW
site in the SAME doc was forgiven on arrival, measured on three planted ledger entries that left
the suite green. The disposition now records HOW MANY sites it answers, and a site that appears
after the record was written is reported. A line number would have been the obvious key and is the
wrong one - this ledger is append-only newest-first, so prepending one entry moves every site below
it.

## CS-806 - detail

**CS-806 CLOSED 2026-08-22 (session 30) - see `docs/LEDGER.md`. This block is the record of how it
was filed and is NO LONGER A LIVE INSTRUCTION.** One paragraph below is SUPERSEDED and the ledger
entry says so: the question it poses - whether verify_env's probe-by-name contract "is the right
one" - was already answered by `BOOTSTRAP.md` section 2.5 before any code was written, and that
answer was simply never implemented. Do not re-open it as a design choice.

filed 2026-08-22 (session 28) by the /done ritual, which tripped over it while running its own
documented step.

CS-806 - `py -3` and `python` resolve to DIFFERENT Python 3.14.4 installations on this machine, and the one the docs name has no `ruff` module - acceptance: the documented tier-0 lint command runs green AS WRITTEN, or the docs name the interpreter that works AND a check FAILS when the two diverge, proven by a control - tier: 1

**MEASURED.** `py -3` resolves to `...\Local\Python\pythoncore-3.14-64\python.exe` and `python`
to `...\Local\Programs\Python\Python314\python.exe`. Both report 3.14.4. Only the second has
`ruff`: `python -m ruff --version` gives 0.15.12, `py -3 -m ruff --version` gives "No module
named ruff", exit 1. The suite, mypy and every tool run this session went through `python`.

**WHY IT MATTERS AND WHY IT IS NOT COSMETIC.** `docs/OPERATIONS.md` and the `/done` ritual both
spell the tier-0 gate as `py -3 -m ruff check <paths>`. Run as written it exits 1 with a module
error. **THE FAILURE MODE IS NOT THE ERROR, IT IS THE MISREADING:** on a markdown-only change
the honest result of a real ruff run is "No Python files found under the given path(s)" plus
"All checks passed" - which looks close enough to a failure-to-run that a session can conclude
lint was not applicable and move on. That is the unrunnable-check-is-not-a-passed-check class
this project already fences in `.githooks/commit-msg`, arriving through the docs instead.

**`scripts/verify_env.py` DOES NOT CATCH IT AND IS NOT WRONG TO MISS IT.** It probes the
toolchain by NAME - `for name in ("pytest", "ruff")` - and `ruff` genuinely is on PATH, at the
Programs install's `Scripts\` directory. So it reports SOFT 15/15 present under BOTH
interpreters, correctly by its own contract. Whatever closes this item should decide whether
that contract is the right one, rather than treating the pass as a bug.

**RELATION TO CS-484, which is a DIFFERENT item and must not absorb this one.** CS-484 is a
VERSION gap - `pyproject.toml` pins `ruff>=0.13` with no upper bound and CI installs whatever is
newest. This is an INTERPRETER gap on one machine. They can be fixed independently and a fix for
either leaves the other live.

**DO NOT CLOSE THIS BY EDITING ONLY THE DOCS.** Changing `py -3` to `python` everywhere makes
the command work today and leaves nothing that notices when the two diverge again, which is how
this arrived. The acceptance asks for a check with a control for that reason.

## CS-493 - detail

Relocated from `ROADMAP.md` 2026-08-20 (session 24) for budget, not deleted.

**CS-493 CLOSED 2026-08-20 (session 25) - see `docs/LEDGER.md`. This block is the record of how it
was filed and is no longer a live instruction.** Bound 2 was LIVE rather than latent: two tracked
modules had declarations the reader could not follow. Bounds 3 and 4 are NOT closed - bound 4 is
filed as CS-500.

CS-493 - Bound the cross-module reach resolution, which is one hop and reads only a LITERAL declaration - acceptance: a module reaching the library through a two-hop sibling chain is reported, or the one-hop bound is recorded in shipped DATA rather than in prose; and a sibling whose `_GRADED_LIBRARY_REACH` is built by a call or a comprehension rather than a dict literal is not silently read as declaring nothing - tier: 2 - NOTE: filed 2026-08-20 (session 24) as CS-491's disclosed residual. `_reaching_names_of` scans a sibling with the base vocabulary and its own aliases, NOT with its own sibling imports, so a helper reaching the library only through a third module is not resolved. `_declared_graded_names` reads `ast.Dict` keys out of the assignment, so `MappingProxyType(dict(...))` or a comprehension yields an EMPTY graded set and the sibling exports nothing - **which fails SILENT, in the permissive direction**. Both bounds are stated in docstrings today, which is prose. **A third, from the privacy pass:** `_sibling_module_file` has no stated precondition on `source`; it reads and parses any `*.py` beside whatever directory it is handed. 2927 arguments were measured across a full run with ZERO outside the repo and tmp, so the bound holds today as a property of the CALL SITES rather than as an assertion. **A fourth, from the round-three pass:** `MODULE_SCOPE_REACH` is ONE sentinel per file, so a module that already declares it absorbs any additional module-scope reach with no new evidence. Three tracked modules declare it today.

## CS-494 - detail

Relocated from `ROADMAP.md` 2026-08-20 (session 24) for budget, not deleted.

**CS-494 CLOSED 2026-08-20 (session 25) - see `docs/LEDGER.md`. This block is the record of how it
was filed and is no longer a live instruction.** Closed on the second branch of its acceptance: the
walks are not merged, the coverage difference is gone, and the one that remains is a difference of
SUBJECT recorded with its reason and graded. This block names three disagreements; the merger
measured six.

CS-494 - Reconcile the two walks that read which attributes come to hold save bytes - acceptance: `tests/save/reach_guard._bound_parameter_annotations` and `tests/save/test_phase4_gate._retained_body_attributes` read one population through one owner, or their difference is recorded and graded - tier: 2 - NOTE: filed 2026-08-20 (session 24). Two hand-maintained walks over one kind of thing is exactly the defect `_FILESYSTEM_PRIMITIVES` was unified to repair, recreated inside the fix for CS-491 and found by the refutation pass on it. They already DISAGREE: `_retained_body_attributes` enumerates three shapes and covers neither the tuple target `self.body, self.count = body, count` nor a `@property` accessor, both of which CS-491 closed on the other side; and it is keyed on the word `bytes` rather than on a vocabulary, so `bytearray`, `memoryview` and `BytesIO` are outside it. The two guards grade different files - one the shipped save modules, one this test package - which is why the drift is invisible to both. **The residual CS-491 could NOT close either way:** a fully unannotated `def __init__(self, body): self.body = body` states the type nowhere, and no reader of either file can recover it.

## CS-498 - detail

Relocated from `ROADMAP.md` 2026-08-20 (session 25) for budget, not deleted.

**CS-498 CLOSED 2026-08-20 (session 25) - see `docs/LEDGER.md`. This block is the record of how
it was filed and is no longer a live instruction.** Closed on the three NAME-keyed shapes the acceptance states - `.name`, `.stem` and `endswith`. The FULL-PATH shape survives and is filed as CS-499.

CS-498 - The reach guard cannot detect a self-exemption in its own source, because every control runs it against a `tmp_path` copy under a different filename - acceptance: a guard that early-returns on its own file name turns a test RED on a machine with NO GAME INSTALLED, even when its own source also gains an undeclared reaching helper - tier: 2 - NOTE: filed 2026-08-20 (session 25) by the CS-495 silent-narrowing refutation pass and REPRODUCED BY THE MERGER ON BOTH TREES. **MEASURED: adding `if module_path.name == "<its own file>": return` to `_assert_library_reach_is_declared` AND appending an undeclared library-reaching helper to that same file leaves `tests/save` GREEN** - 1114 passed on the post-CS-495 tree, 1110 on `1e05233` with the guard still in `test_properties`. **THIS PREDATES CS-495 and the relocation neither caused nor worsened it**; it is recorded because the pass that found it was looking at the relocation. Do not close it by naming the guard's own filename anywhere - that is the same defect pointing the other way.

## CS-497 - detail

Relocated from `ROADMAP.md` 2026-08-20 (session 25) for budget, not deleted.

**CS-497 CLOSED 2026-08-20 (session 25) - see `docs/LEDGER.md`. This block is the record of how
it was filed and is no longer a live instruction.** Closed on the DECLARED-inclusion route, not by deleting the assertion: the derivation now intersects a declared reaching set instead of subtracting the exclusions, so the line the fence protected is what reports an unclassified name.

CS-497 - The filesystem-vocabulary partition is a TAUTOLOGY in its inclusion direction, so an unclassified name is silently made a reach primitive - acceptance: a name added to `tests/save/reach_guard._FILESYSTEM_PRIMITIVES` and classified in neither `_NOT_LIBRARY_REACH` nor the reach set turns a test RED on a machine with NO GAME INSTALLED, and the red NAMES that name - tier: 2 - NOTE: filed 2026-08-20 (session 25) by the CS-495 prose refutation pass and REPRODUCED BY THE MERGER. `_LIBRARY_PRIMITIVES` is derived as `_LIBRARY_LOCATORS | (_FILESYSTEM_PRIMITIVES - frozenset(_NOT_LIBRARY_REACH))`, so `test_the_reach_primitives_partition_the_filesystem_vocabulary`'s inclusion assertion reduces to `A <= B | A` and holds for any vocabulary whatever. **MEASURED: `fchmod` added to the vocabulary and classified nowhere leaves that test GREEN.** The whole suite does go red, on `tests/save/test_workdir.py::test_the_default_work_root_is_gitignored` and `::test_the_workdir_suite_passes_with_no_install_and_no_save` - which is a red for an unrelated reason and is not this property being graded. **THE EXCLUSION DIRECTION IS REAL** and so are both non-vacuity floors and the locator separation; only the inclusion half is vacuous. The comment and the docstring that claimed "a name can be excluded, but it cannot be forgotten" are corrected in place - do not rewrite them back. This predates CS-495, which only relocated the code; do not close it by deleting the assertion, which is what makes the exclusion direction hold.

## CS-495 - detail

Relocated from `ROADMAP.md` 2026-08-20 (session 24) for budget, not deleted.

**CS-495 CLOSED 2026-08-20 (session 25) - see `docs/LEDGER.md`. This block is the record of how
it was filed and is no longer a live instruction.** It closed on the relocation this block
names, and the objection this block says no longer holds was measured to be half-right: the
package walk does grade the guard's new module, but nothing graded whether that walk still
covers it, and nothing noticed that an uncollected module's tests never run. Both are closed;
residuals filed as CS-497 and CS-498.

CS-495 - `tests/save/test_properties.py` sits against a hard size ceiling with no margin - acceptance: the module is under its ceiling by a margin a session can spend, or the ceiling's owner records what the margin is meant to be - tier: 2 - NOTE: filed 2026-08-20 (session 24). `tests/data/test_phase2_gate.py::test_no_file_under_tests_is_large_enough_to_be_a_slice_of_real_game_data` caps any file under `tests/` at 256 KiB, a crude check whose whole job is catching a trimmed slice of real game data. **At the START of session 24 the module was 288 bytes under that ceiling** - any addition at all would have tripped it, and CS-491 did. Session 24 relocated the reach-guard CONTROLS into `tests/save/test_reach_guard.py` per CLAUDE.md section 4 (relocate, do not delete), which restored some margin but not much. **DO NOT CLOSE THIS BY RAISING THE NUMBER** without dealing with the comment that justifies it, which says the ceiling sits "well above the largest authored file" - raising it to fit makes that sentence false and puts a measured number in prose. **THE OBVIOUS RELOCATION IS THE GUARD IMPLEMENTATION**, and the objection that used to block it no longer holds: `test_every_library_reaching_function_here_is_declared` records that a guard whose owner is outside its own scope let a sweep ship ungraded, but CS-471's package-wide walk now applies the guard to every module including whichever one owns it, so moving it preserves that property rather than breaking it. It costs updating the sibling references that name `test_properties` for the guard.

## CS-491 - detail

Relocated from `ROADMAP.md` 2026-08-19 (session 23) for budget, not deleted.

**CS-491 CLOSED 2026-08-20 (session 24) - see `docs/LEDGER.md`. This block is the record of
how it was filed and is no longer a live instruction.** It took THREE rounds: the routes below
were closed first, then eleven more that a refutation pass measured past that close, then a
twelfth plus ten more that a second pass measured past the second. Residuals filed as CS-492,
CS-493, CS-494 and CS-495.

filed 2026-08-19 (session 23) as CS-471's residual. CS-471 closed on its three stated clauses
and the routes below were measured OPEN at that moment by two refutation passes, each with a
proof of concept run on a machine with no game. **Do not read CS-471's ledger entry as closing
any of them.**

**THE ALIASING ROUTES.** The reach guard is keyed on NAMES, which the module has always
recorded as a trade. Measured invisible to it: a module-scope `lambda` wrapping a locator;
`functools.partial(locate.resolve_save_root)`; `operator.methodcaller("glob", "*.sav")`; and
`getattr(account, _NAME)("*.sav")` where `_NAME` is a module constant. `_effective_primitives`
resolves an assignment of a bare Name or Attribute and stops there, and `_calls_any` reads a
`getattr` only when its second argument is a literal.

> **CORRECTION, session 24, 2026-08-20 - the LAMBDA clause above names the wrong mechanism,
> and the true one is worse in one direction.** Measured: the guard is NOT blind to a
> module-scope `lambda` wrapping a locator. An `ast.Lambda` body is not a function to
> `_module_scope_reaches`, so the call inside it reads as a MODULE-SCOPE call and the
> classifier does pick the module up. What the guard then does is file it under
> `MODULE_SCOPE_REACH` and name NO FUNCTION - so a module that legitimately declares that
> sentinel, as three tracked modules do, hides the reaching helper completely. The route is
> real; "invisible to it" is the wrong reason, and the true reason is harder to notice
> because the guard looks like it fired. The other three clauses reproduced exactly.
> Corrected in place per this project's method; do not rewrite it back.

**THE CROSS-MODULE ROUTE.** A module with no primitive call of its own is classed silent, so
importing a sibling's reaching helper and calling it is outside the guard entirely. CS-471's
suite-wide test proves the guard is APPLIED to every module in the package; it does not prove
every route into the library runs through a primitive that module names, and its docstring now
says so.

**THE WRAPPER DEFEATS.** `_body_wrapping_classes` reads field annotations and bases. Measured
NOT flagged: a field typed `bytearray`, `memoryview` or `BytesIO`; an unannotated
`self.body = body` bound in `__init__`; and a class imported from a sibling module. Measured
flagged: `NamedTuple`, a string annotation, a class nested in a function, and a subclass of a
wrapper.

**CLAUSE 3 IS INERT ON THE SHIPPED TREE AND THAT IS NOT A DEFECT IN THE WIDENING.** The
propagation half is consulted for GRADED helpers alone, and `tests/save/test_value_anchoring.py`
`_extents_of` calls no primitive, so it can never be graded - the guard refuses it with `a
graded helper no longer reaches the library`. Neutering the widening reds its own planted
control and nothing else in the suite. Any acceptance here has to move a verdict, not a
predicate.

NOTE THE HARD PART BEFORE STARTING: keying on names is what makes the guard cheap and total
over the shapes it does see. A route-based guard would need to resolve aliases across modules,
which is the analysis this repo has so far declined. Do not close this by widening the name
list alone - that leaves the next alias open and reads as though it did not.


## CS-487 - detail

Relocated from `ROADMAP.md` 2026-08-19 (session 22) for budget, not deleted. **CS-487 CLOSED
2026-08-19 (session 23) - see `docs/LEDGER.md`. This block is the record of how it was filed
and is no longer a live instruction.** Its residual is filed as CS-490, which is NOT CS-488.

**ONE COUNT BELOW WAS MEASURED WRONG AND IS CORRECTED HERE RATHER THAN REWRITTEN.** The
paragraph says the three-line route stands at `tests/save` **1058 passed 49 skipped with no
game, the same counts the clean tree gives**. Session 23 measured the clean tree at `8ec3dbb`
twice, and the forged tree twice, and got **1059 passed 49 skipped** every time. The internal
claim - that the route is byte-identical to the clean tree - reproduced exactly; the absolute
figure did not, and it disagreed with session 22's own wakeup note, which said 1059. Take the
relation, not the number.

filed 2026-08-19 (session 22) by a refutation pass on CS-481 and RE-MEASURED BY THE MERGER in a clone. THREE LINES, all in `clockspeed/save/objects.py` and with NO test-side line at all, ship `vacuous_one_byte` - the word asserting the byte-order question is retired BECAUSE THE VALUE IS ONE BYTE - for `DoubleProperty`, an EIGHT-byte Unreal type this repo names in no table at all, at `tests/save` **1058 passed 49 skipped with no game**, the same counts the clean tree gives. CS-480's own disclosure prices this residual as "an edit to both shipped sites" and never says how cheap both sites are; correcting that sentence is part of the work. DO NOT close it by naming `DoubleProperty` anywhere - the route is word-agnostic and any word the module has never named serves.


## Session 20 wakeup notes - relocated

Relocated from `WAKEUP_NOTES.md` 2026-08-19 (session 23) when the fourth session landed,
per that file's own rule. Relocated, never deleted.

## Session 20 - 2026-08-18 - CS-480 CLOSES after THREE refutations; the library grew and the push is blocked

- **Shipped: CS-480 CLOSED.** Filed CS-481 and CS-482; enlarged CS-473. **THE SUITE IS RED AT
  SESSION END AND IT IS NOT THIS SESSION'S WORK - THAT IS CS-482, READ IT FIRST.** Measured both
  ways: `12 failed, 2073 passed, 3 skipped, exit 1` on the working tree, and that same clone of `fd9e8dc`, with
  no working-tree changes at all, gives `12 failed, 2068 passed, 3 skipped` - the SAME twelve
  tests, the same 3 skips, and exactly the 5 tests this session added as the whole delta. With NO GAME INSTALLED the working tree is **2036 passed, 52 skipped, exit 0**. Session
  start was 2080 passed 3 skipped exit 0 at `fd9e8dc`, measured by me before any edit. Drift
  guard and doc budget below. mypy clean 28 and 84, ruff check clean, ruff format clean 84.
  Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THAT ALL THREE ADVERSARIES SUCCEEDED AND EACH BROKE THE FIX THE PREVIOUS ONE
  HAD FORCED.** None of the three findings was reachable from inside the work. The first artifact
  was right about its acceptance and wrong about its consequence; the second was right about its
  consequence and had a live hole in the arm that closed it; the third found the route that goes
  AROUND the whole mechanism, which is CS-481.

- **REFUTATION 1 - ASKING THE READER ONLY MOVED THE TRANSCRIPTION ACROSS THE SEAM.** Deriving the
  exemption from `objects._read_tag_header` alone LOOKS like a derivation and is not one: the
  reader picks its own population by a literal nothing grades. Widening it to `Int64Property`
  plus one mapping line ships `vacuous_one_byte` - the word asserting the byte-order question is
  retired BECAUSE THE VALUE IS ONE BYTE - for an EIGHT-byte type, at 32 passed, reproduced by me
  before acting. The old two-line edit had become a new two-line edit, both lines now in
  `objects.py`. **THE FIX WAS A SECOND SHIPPED SITE:** `objects._decode_value` must build the
  value out of that byte alone. The same pass also found an extract-method wrapper route caught
  only by library-backed anchors, so it was GREEN on a no-game machine; the library-free module
  catches it now.

- **REFUTATION 2 - FOUR PROSE CLAIMS MEASURED FALSE, ONE A LIVE HOLE.** A reader reading TWO
  bytes at the tag offset while ADVANCING ONE left every control green, cursor arm included,
  with `vacuous_one_byte` still shipped for a two-byte value. Closed by
  `_tag_byte_source_positions`, which counts how many body positions the returned tag byte
  depends on. The other three were prose, corrected in place and NOT to be rewritten: the cursor
  excess is what the BRANCH consumes and not the value's width (a padding byte in front of a
  one-byte value reports 2); zeros do NOT satisfy every branch (the guid-present path is
  unreachable from a zero-filled body, and a struct guid is stepped over unread); and the reader
  does not "always" walk to a value that fits.

- **REFUTATION 3 - THE ROUTE GOES AROUND THE EXEMPTION, NOT THROUGH IT.** The key bound subtracts
  the fixed-width table AND the exemption. CS-480 derived the exemption. The WIDTH TABLE IS
  SELF-AUTHORISING: three lines in `objects.py` ship `vacuous_one_byte` for an eight-byte type
  with `tests/save` at **1002 passed 49 skipped on a no-game machine, byte-identical to the clean
  tree there**. I verified in BOTH environments. With a library it is red - I measured 13 failed
  where the pass reported 1 - but all of those are library-backed width oracles in OTHER modules
  that skip without one. CS-480's acceptance is about a type NAMED AS TAG-CARRIED, so it closes;
  this is a different ungraded bound and it is CS-481.

- **MY OWN CONTROLS FAILED THEIR GRADING AND THAT WAS THE MOST USEFUL RESULT OF THE SESSION.**
  FOUR mutants of eleven came back MISSED, including deleting the decoder arm outright. The
  counters called the predicate DIRECTLY instead of exercising the derivation, so they graded the
  function and not its use; and the one shipped counter available was rejected by the wrong arm
  before the arms under test were consulted. **A COUNTER THAT FIRES THE WRONG ARM GRADES
  NOTHING.** Rebuilt as two controls that forge a word through each shipped site in turn, plus
  hand-authored fake decoders per arm. Final battery: **17 mutants, 16 DETECTED.**

- **Surprises**, each measured:
  1. **THE OPERATOR PLAYED THE GAME WHILE I WORKED AND IT TURNED THE SUITE RED.** Three saves
     were written to the library at 18:47, 18:52 and 18:57. The walk now raises
     `ObjectBudgetExceededError` on real bodies. **The pre-push hook runs the whole suite, so the
     commit is LOCAL-ONLY.** Do not bypass the hook; do not raise `MAX_OBJECTS` as a first move -
     a budget error is equally the signature of a desynchronised walk. That is CS-482.
  2. **THE PREDICATE SAMPLED TWO SLICES OF A CROSS PRODUCT AND CALLED IT A CROSS PRODUCT.**
     Payload-independence was probed only at tag byte 0 and tag-sensitivity only at filler 0x00,
     so a decoder returning a STORED byte for tag byte 1 and a constant for 0 was ACCEPTED. Both
     arms now run at every combination.
  3. **THE ONE MUTANT STILL MISSED IS THE ASSERTION GUTTED TO A TAUTOLOGY.** Nothing else in the
     module sees the dependence count, so weakening `== 1` to `>= 0` is invisible. That is
     CS-473's emptiness shape, recorded in the test's own docstring rather than papered over.
  4. **THE REPO'S OWN TOOL SAYS THIS MODULE GOT WORSE.** `unbacked_absolutes` reports 113
     sentences against 70 at `fd9e8dc`, and the module is not in `FENCED_MODULES`. I did NOT
     hand-repair a sample: a partial repair with no mechanism is the register of pardons that
     tool's docstring forbids. Recorded on CS-473.
  5. **A SUBAGENT'S NUMBER DID NOT REPRODUCE AND MINE IS THE ONE IN THE LEDGER.** The third pass
     reported the width-table route as 1 failed with a library; I measured 13. The no-library
     figure - the load-bearing one - reproduced exactly.
  6. **THE HARNESS BASH HEREDOC EATS BACKSLASHES**, not only on large payloads. `\x00` became a
     real NUL byte inside a source file and `\n` became a real newline inside a string literal,
     twice. Write the payload with the Write tool instead.
  7. **DOC BUDGET TOOK FIVE RELOCATIONS, NOT SIX TRIMS.** Two new entries put `ROADMAP.md` over
     its WARN twice. Micro-trimming prose recovered 11 bytes; relocating four NOTE blocks and one
     status block to `docs/history_notes.md` took it from 60.85 KiB to 57.86 KiB.

- **Failed paths - do not retry:**
  - **Deriving a bound from ONE shipped site.** If that site picks its own population by an
    ungraded literal, the derivation is a transcription with extra steps.
  - **Grading a predicate by calling it directly.** Grade the DERIVATION that uses it, or a
    mutant deleting the call comes back MISSED.
  - **A counter drawn from the shipped population when the arms already agree on it.** Forge one.
  - **Sampling two slices of a cross product.** The cross term is where the hole is.
  - **Micro-trimming prose to meet a doc budget.** Relocate.

- **Next action: CS-482**, because it blocks the push and the whole suite. Establish whether the
  new saves mean a genuinely larger world or a desynchronised walk BEFORE touching `MAX_OBJECTS`.
  Then **CS-481**, using the reproduction on its ROADMAP entry. Then **CS-478**, then **CS-471**
  (tier 1, privacy-adjacent), then CS-477 - whose measurements are now in `docs/history_notes.md`
  under **CS-477 - detail** - then CS-479, then CS-470/472/473/474.

## Session 19 wakeup notes - relocated

Relocated from `WAKEUP_NOTES.md` 2026-08-19 (session 22) when the fourth session landed,
per that file's own rule. Relocated, never deleted.

## Session 19 - 2026-08-18 - CS-421's route (b) SHIPS and the close is REFUSED; the privacy defect was mine

- **Shipped: NOTHING CLOSED, AND THAT IS THE RESULT RATHER THAN A SHORTFALL.** CS-421 STAYS OPEN
  with a ledger record declaring the non-closure by name. Filed CS-478 and CS-479; enlarged
  CS-471 and CS-480. Suite 2073 -> **2080 passed, 3 skipped, exit 0** serial AND under
  `-n auto`, `tests/save` 1040 -> 1047. **CI failed `07b5189` on `ruff format --check`, a gate
  that had never been run locally; fixed in a follow-up commit.** Drift guard
  **CLEAN 9/9**, doc budget **PASS measured 16** after a relocate pass, mypy clean 28 and 84, ruff
  clean. Detail in `docs/LEDGER.md`.

- **THE PUSH WAS NEVER A CREDENTIAL PROBLEM AND SESSION 18'S DIAGNOSIS WAS WRONG.** `a7cb400`
  pushed from this non-interactive session on the first real attempt with
  `git -c credential.interactive=false push`. What looks like a hung GUI dialog is the pre-push
  hook running the WHOLE suite for ~155 s. My own first attempt reproduced the false signal exactly
  by timing out at 60 s and printing a `send-pack` disconnect. **Do not carry "needs an interactive
  terminal" forward; give the push a timeout above 300 s.**

- **THE HEADLINE IS THAT ALL THREE ADVERSARIES SUCCEEDED AND THE THIRD ONE LANDED AFTER THE
  COMMIT WAS ALREADY PUSHED.** The build was finished, green at 2077, and every gate passed. Then
  a correctness pass showed the close was an anecdote, a privacy pass showed I had introduced a
  non-negotiable 12 exposure, and a guard-hole pass - which I had already reported as not having
  returned - broke the committed artifact two more ways. None of the three was reachable from
  inside the work.

- **I COMMITTED WHILE A DISPATCHED PASS WAS STILL OUT, SAID SO PLAINLY, AND IT STILL COST A SECOND
  COMMIT.** Reporting a lens as unexamined is honest and is NOT the same as being entitled to ship
  past it. **A pass that has been dispatched has not been declined; if its lens matters, the
  commit waits for it.** That is the most transferable thing in this session.

- **THE MEMOISED SWEEP POISONED PERMANENTLY AND ITS OWN DOCSTRING DENIED IT IN PROSE.**
  `_sweep_separability` was an `lru_cache` over a result that can be `None`, and NOTHING in the
  repo ever called `cache_clear` on it. One earlier call with `_library_save_paths` patched empty
  cached that `None`, and all four library-backed graders of the new status word then skipped for
  the whole session - green at exit 0 with four skips, the word graded by nothing, and **a skip
  reads as an ungraded machine rather than as a defect**, which is what makes it worse than a red.
  Sibling modules that collect earlier already patch that helper. Fixed by never caching a `None`.

- **CS-421 DOES NOT CLOSE BECAUSE THE VERDICT IS A FACT ABOUT ONE NUMBER.** `UInt32Property` yields
  9 values, ONE stored pattern, `00190000` - which is 6400. Over a population of that same size and
  shape, **65280 of the 65535 possible values drive the SAME shipped oracle to a GREEN endianness
  verdict; only the 255 multiples of 256 reach the undecided state recorded.** Re-measured by me
  before it reached the ledger. The artifact is right and is shipped; reading it as clause 3
  settled is what is refused.

- **FOUR SENTENCES I WROTE WERE MEASURED FALSE, AND ALL FOUR WERE CAUGHT BEFORE THE COMMIT:**
  that the derivation is THRESHOLD-FREE and "counts no values" (the applied clause is a count
  against zero); that accumulator INVARIANCE under the reversal is the right predicate (two
  counters are equal when both are ZERO as well as both total, and a read displaced by +1 produced
  exactly that and was admitted); the unqualified spelling `oracle_cannot_separate` (the oracle
  separates 12 of 24 orderings on this very population); and a draft ledger line asserting a
  containment control **that I had not actually applied yet**.

- **Surprises**, each measured:
  1. **THE SCORING PHASE SAT OUTSIDE EVERY HANDLER AND I DID NOT SEE IT.** The frame still bound
     the discovered path list, the last save's raw bytes and its parsed header, so a raise from the
     shipped decoder rendered a save path, the save-tree ACCOUNT DIRECTORY, a world name and the
     plaintext header options string. **One demonstrated route needed NO opt-in flag**, because
     `_score_population` takes the census as a PARAMETER and pytest renders a crashing frame's
     arguments by default - an ordinary rename in a sibling module was enough.
  2. **A MUTANT CAME BACK MISSED THAT SHOULD NOT HAVE, AND IT WAS THE MOST USEFUL RESULT OF THE
     SESSION.** Gutting my own tightened predicate to a tautology left both modules GREEN: on this
     corpus the universal and the reversal conjunct beside it admit the SAME single word, so no
     library-backed control can ever tell them apart. The fix was to name the predicate and grade
     it with HAND-AUTHORED counters, which runs on a machine with no game.
  3. **MY REPAIR KILLED A CONSTANT.** Tightening the predicate left `_REVERSAL` unreferenced, so
     the reading the status word is NAMED after was no longer scored by anything. ruff does not
     flag a dead module-level constant.
  4. **`FloatProperty` DERIVES AS "APPLIED AND UNDECIDED" ON 24-OF-24 AGREEMENT** unless an applied
     clause excludes it - its values decode to a float the int32 tally never sees, so its
     accumulator is empty and every ordering trivially matches every other.
  5. **THE EXTENT ANCHOR ALREADY COVERS `UInt32Property`**, which softened one refutation:
     `_anchor_one_save` grades every fixed-width tag through `_anchored`. The derivation inherits
     anchoring rather than lacking it - but a displacement applied to the derivation ALONE still
     leaves 5 of 7 offsets admitted. Filed as CS-479.
  6. **ADDING THE WORD REDDENED CS-476's VOCABULARY BOUND EXACTLY AS PREDICTED**, and stayed red
     until the grading landed beside it. The handover called this and it behaved.

- **Failed paths - do not retry:**
  - **Diagnosing the push as a credential dialog.** It is the pre-push suite; use a long timeout.
  - **Resting the CS-421 close on the oracle being undecided here.** It is undecided because of
    which number this type carries, and one new value with a nonzero low byte empties the set.
  - **An accumulator-invariance predicate.** Equal counters include both-zero.
  - **Doing the scoring phase outside the per-save handler**, or trusting a sweep's assertion
    messages to be counts-only while its FRAMES are not.
  - **Trusting my own mutation set to be complete.** Two of eight came back MISSED and one was a
    real gap in the control. An independent pass then found three more my set had no mutant for.
  - **Caching a `None` that means "this machine cannot grade it".** An absence memoised once
    disarms every grader downstream of it, silently, for the whole session.
  - **Treating `ruff check` as the whole of ruff.** It is NOT `ruff format --check`, and CI runs
    both. Every local gate passed all session and CI still failed `07b5189` in 24 seconds on two
    cosmetic format findings - an unwrapped `assert` and two missing blank lines before a
    top-level `def`, both artifacts of appending text programmatically. **The local gate set used
    all session was incomplete against CI's.** Run `python -m ruff format --check .` before every
    commit; it is instant.

- **A FOURTH ADVERSARY RAN ON THE CACHE FIX AND RETURNED NOT REFUTED**, which is the only
  unbroken done-claim of the session. It attacked four poisoning routes, proved the control
  non-vacuous with a mutant isolating the SEMANTICS rather than the data structure - keep the list,
  drop only the `is not None` guard - and checked six orderings. **It still found a prose
  overclaim of mine**, the third of the session: "caching only a real sweep removes the state" is
  false, because a NARROWED but real sweep still caches session-wide. Measured: patching discovery
  to one save of seventeen caches that sweep and every grader passes green off it, no skip, no red.
  The docstring states the bound now. **The green-with-skips outcome also stays reachable by a
  non-cache route the control cannot see, because the control skips too** - that is CS-426.

- **Next action: CS-480**, the last ungraded bound on which types may carry a byte-order status.
  `_TAG_CARRIED_ONE_BYTE_VALUES` in `tests/save/test_byte_order_status.py` is hand-written and read
  by NOTHING: two lines ship `vacuous_one_byte` for `StrProperty`, a LENGTH-PREFIXED type whose
  payload begins with an int32 length, with everything green. Reproduced at 31 passed before
  filing. The objects.py-only half of that edit IS caught, so the guard is exactly one tuple deep.
  Then **CS-478**, the two incompatible definitions of "an oracle scores this type", which is the
  coherence defect this session introduced. Then **CS-471** (tier 1, privacy-adjacent), whose
  surface this session enlarged in the exact channel its guard cannot see:
  `_collect_stored_patterns` and `_score_population` RECEIVE personal data as parameters and
  `_returns_personal_data` reads only `node.returns`. Then CS-477, then CS-479.


## Rules for this file

- **Relocate, never delete.** When a living file hits its size budget or a note ages out
  of `WAKEUP_NOTES.md`, the content moves here and the living file keeps a one-line
  pointer. Content is not dropped.
- **Append only, newest first.** Archived material is not edited after it lands. It is a
  record of what was believed at the time, including the parts that were wrong.
- **Every archived block carries the date it was archived and where it came from**, so a
  reader can tell how stale it is without reconstructing the history.
- **A dated heading marks its own section historical.** Every section in this file is
  dated for exactly that reason, and the drift guard treats dated sections as
  non-current so they are never audited as live truth.
- **Check a row's AGE before building on anything here.** An archived note may describe
  code that no longer exists, a decision since superseded, or a count long out of date.
- This file is excluded from searches for current truth. Do not resolve a question by
  grepping here.

---

## Archive

### 2026-08-16 - ROADMAP.md relocate pass, session 13

`ROADMAP.md` reached 119 per cent of its WARN budget and the cause was structural rather
than incidental: its entries had become essays while the doc topology table says one line
per item. The full body of every oversized entry is relocated here VERBATIM, newest state
included, and `ROADMAP.md` keeps the item line, its acceptance, its tier, a one-sentence
lead and a pointer to the entry below.

**These entries are OPEN work, not history.** They sit in this file only because of the
size budget, which makes them the one exception to this file's "nothing current" rule -
read them as the live detail of the matching `ROADMAP.md` line, and re-verify anything
load-bearing against the tree before acting on it.

### CS-413 - detail

**STATUS 2026-08-23: CS-413 IS CLOSED. EVERYTHING BELOW THIS BANNER IS HISTORY**, including
the sentences reading "WHY IT STAYS OPEN", "CS-400's clause 1 closes when this closes" and
"phase 5 does not open before it". They were true when written, are not edited, and all three
are superseded - phase 5 is OPEN, and clause 1 waits on inventory being readable rather than on
this item. The close is in `docs/LEDGER.md`. **THE RESIDUALS THIS ITEM LEFT ARE LIVE** and are
CS-828, CS-829, CS-830, CS-831 and CS-832. This banner exists because the CS-421 close earlier
the same day set the precedent and this close initially failed to follow it.

**THIS IS THE PHASE-4 DEPTH GATE.** Filed 2026-08-15 by the operator ruling recorded in CS-400: CS-400's clause 1 closes when this closes, and phase 5 does not open before it. It is the natural successor to CS-407, which closed the SKELETON. NOTE THE TWO LAYERS, because they are not the same problem and only the second is what most readers picture. **Layer 1 - the data section is located and walked; what was missing is ATTRIBUTION.** **Layer 2 - the property grammar inside one payload**, then value decoding per type. Prior knowledge of how Unreal serializes properties is a HYPOTHESIS GENERATOR and never evidence here; the phase's stated common-mode risk is a corpus that only ever agrees with whoever wrote it, and for layer 1 the corpus can say nothing at all because no fixture builds a data section. Record the grammar as DATA, per CS-412 - a partial recorded as an adjective is not resumable. **The session-6 STATUS, which recorded the attribution half being MET and the four independent oracles that proved the payload pairing, is relocated to `docs/history_notes.md` along with this entry's own correction record.** **STATUS 2026-08-15 (session 7): THE DECODE LANDED AND THIS STILL DOES NOT CLOSE.** `read_properties` now returns real property values across the local library, every unmeasured type flagged rather than guessed, and a hand-authored synthetic payload fixture means the decoder is covered on a machine with no game installed. The save-60 half of this item has MOVED OUT to `docs/GATED.md` CS-G05, because no work inside this repo can close it. **WHY IT STAYS OPEN, ruled by the merger and confirmed by an adjudicator that did not produce the work.** Two independent reasons, both measured. FIRST, THE ACCEPTANCE CLAUSE IS TRIVIALLY SATISFIABLE: "returns at least one decoded property VALUE off a real building" is a liveness floor, and a decoder that reads ZERO value bytes clears it, because a `BoolProperty`'s value rides in the tag with `size` 0. This project already recorded that a `> 0` liveness control is not a control; an acceptance clause the shipped rotation control is designed to defeat cannot be the thing that closes the item. SECOND, THE EVIDENCE IS UNEVEN AND THE UNEVENNESS FALLS EXACTLY ON WHAT PILLAR 3 NEEDS: a majority of the decoded values are backed by a declared width and nothing else, a check the module ITSELF records as "defensive rather than measured", while byte order and signedness are checked by NOTHING EXECUTABLE - flipping an integer type to big-endian reddens only synthetic-fixture tests whose own fixture packs with the same byte order the reader unpacks with. `IntProperty` and `FloatProperty` are inventory counts and clock speeds, so pillar 3 sits inside exactly that unbacked majority. **CS-421 OWNS THAT SPLIT AND CARRIES THE PER-TYPE FIGURES. They are deliberately not restated here: one measured fact living in two entries is the drift CLAUDE.md section 4 exists to stop, and this entry was doing it.** What is evidenced is "the values were produced and are self-consistent with our own writer". What closing would assert is "correctly decoded". The gap between those sentences is CS-420, CS-421 and CS-422, and those three carry the acceptance criteria that close this properly.

### CS-420 - detail

**The session-9 REOPENED block is relocated to `docs/history_notes.md`** - its F1, F2 and dead-paragraph-citation findings were all fixed in session 10 and re-verified by an adversary that wrote none of the repair, so it is a record rather than a state. **DO NOT HAND-REPAIR THE PROSE AGAIN.** Four rounds, fourteen-plus false sentences, several written by the commit correcting the previous one. ADR 0008 gives the rule and the artifacts now exist to enforce it; what is missing is a MECHANICAL check that a declarative sentence in this module is backed by execution. Build that, or delete the sentences it cannot back. **STATUS 2026-08-16 (session 10): THE FENCE SHIPPED, ROUND FIVE STILL SHIPPED FALSE SENTENCES, AND THE ITEM STAYS OPEN ON THE FENCE'S POROSITY.** F1, F2 and the dead paragraph citation ARE fixed and were re-verified by an adversary that wrote none of the repair. `tests/save/test_absolute_claims.py` now reads prose from docstrings via `ast`, comments via `tokenize` AND assert messages via `ast.Assert.msg`, and requires an unbounded quantifier to name a resolving test; it is proven to fire against the real tree by re-inserting `IT NEVER RAISES`, and gutting it IS visible. What it does NOT do is the acceptance. **MEASURED BY THE ADVERSARY, AND BY THE MERGER INDEPENDENTLY: three genuine ADR-0008 tier-1 universal claims were inserted into the fenced module, byte-verified applied, and the full suite stayed byte-identically green.** 19 of 22 real universal phrasings carry no listed marker - `at no point`, `no other test`, `without exception`, `not a single`, `invariably` and 14 more all return ZERO findings - and TEN prose channels are never read at all: `pytest.skip` reasons, `pytest.fail` messages, an assert message held in a `Name` rather than a literal, PEP-224 attribute docstrings, bare mid-function strings, parametrize ids, `raise AssertionError`, `pytest.raises(match=)`, module-level string constants, and `pytest.mark.skip(reason=)`. That last class is the sharp one: "an assignment is not prose" is what keeps the control corpora inert AND is a universal write-anything channel. **AN ELEVENTH CHANNEL WAS FOUND 2026-08-16 AND IT IS ARGUABLY THE MOST CONSEQUENTIAL OF ALL: A WARNING DETAIL STRING IS A CALL ARGUMENT, AND NO PROSE KIND THE FENCE READS COVERS ONE.** It is not a docstring, not a comment and not an assert message. It is also the sentence SHIPPED TO THE OPERATOR to explain a loss, so it is the highest-consequence prose in the tree and the least guarded. This is not hypothetical: CS-435's first build shipped a false universal in exactly that position - "every index resolving to it is flagged unresolved" - which was false at FOUR measured sites, and the fence flagged none of it because it cannot see the string at all. CS-435's repair built two derived fences for its own module, one deriving every warning detail from the AST and refusing site-quantifiers, the other resolving every sibling symbol the module cites; both derive their population at runtime. **Those two are a WORKED EXAMPLE of what clause (2) of this item's acceptance asks for and are worth reading before the next attempt** - they are also, being in `clockspeed/save/usmap.py`, evidence for the breadth question rather than the depth one. `FENCED_MODULES` is a hand-written 2-tuple whose deletion - removing this item's own subject - leaves the suite green, which is a scope allowlist with the sign flipped. **The overwhelming majority of sentences in the fenced modules carry no marker and are unread by the rule; DERIVE that ratio with the fence module's own `sentence_count` rather than reading a number here.** The figures that used to sit in this sentence had themselves drifted - the item's thesis landing on the item - and the incident is recorded in `docs/history_notes.md` rather than restated. Contract 4's tree scan has NO FLOOR on its reference population and there are ZERO anchored paragraph references in the tree, so it cannot go red on tree content today. **THE ACCEPTANCE TENSION WAS A MISDIAGNOSIS, IS SETTLED, AND DOES NOT REOPEN.** ADR 0008 SCOPE governs BREADTH, this item's acceptance governs DEPTH in the one module named in its own title, that module is already in `FENCED_MODULES`, and the two texts never disagreed. ADR 0008's SCOPE clause is UNAMENDED. Five rounds were spent building against a dilemma that was not there; the adjudication is recorded in `docs/history_notes.md`. **DO NOT hand-repair prose again and DO NOT hand-extend the marker list** - a hand-maintained list is the thing that rots, and that is the failure this artifact was built to stop, re-shipped inside it.

### CS-421 - detail

**STATUS 2026-08-23: CS-421 IS CLOSED. EVERYTHING IN THIS SECTION IS NOW HISTORY, the
sentences below saying the item stays OPEN included.** They were true when written and are not
edited, per this file's practice. The close is in `docs/LEDGER.md`.

**THE FENCES BELOW ARE STILL LIVE and travel with the two residual items the close filed.**
**CS-826** carries the int32 population and the fence against designing a cleverer predicate on
it. **CS-825** carries `UInt32Property`, to which that fence is NOT transferred, because it was
never measured on that type. Fence (4) - the non-negotiable-12 containment fence naming
`test_a_raise_in_the_scoring_phase_carries_nothing_out_of_the_walk` - is unconditional, survives
the close, and that test must not be deleted as redundant.

### Relocated 2026-08-22 (session 32) from `ROADMAP.md` - the CS-421 NOTE, verbatim

Moved for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`, which now
carries a one-line pointer here.

filed 2026-08-15 by the measurement-validity adversary. **THE FULL ENTRY AND THE STATUS HISTORY FOR SESSIONS 14 AND 16 THROUGH 18 ARE IN `docs/history_notes.md` under **CS-421 - detail** and **CS-421 - status history**, and MUST BE READ BEFORE TAKING THIS ITEM** - relocated for budget, never deleted. They carry the population derivation, the session-16 anchoring fix, the session-17 singleton result and the fence forbidding the data-blocked sentence, and each records a sentence measured FALSE that must not be rewritten. **STATUS: ROUTE (b) IS BUILT AND SHIPPED AND CS-421 STILL DOES NOT CLOSE - THE REFUSAL IS THE RESULT, NOT AN UNFINISHED ATTEMPT.** The session-19 status block is relocated to `docs/history_notes.md` under **CS-421 - status history**. **THE FOUR FENCES THIS ENTRY OWNS ARE RELOCATED to `docs/history_notes.md` under **CS-421 - fences** and MUST BE READ BEFORE TAKING THIS ITEM** - relocated for budget, never deleted. Residuals filed as CS-478 and CS-479.


NOTE: filed 2026-08-15 by the measurement-validity adversary. Its split of the 185382 decoded values: redundancy-oracle-backed by a string's own length prefix - ObjectProperty 52457, ByteProperty 5359, NameProperty 9804, EnumProperty 6245, SoftObjectProperty 116, StrProperty 37 = **74018**; cross-section-backed 26146, a strict SUBSET of the ObjectProperty 52457; and **backed by a declared width and nothing else - IntProperty 75136, FloatProperty 31318, BoolProperty 4077, Int8Property 824, UInt32Property 9 = 111364, which is 60.1 per cent of the total.** **THAT 60.1 PER CENT WAS MEASURED STALE 2026-08-23 (session 34) AND MUST NOT BE CARRIED FORWARD AS THE HEADLINE.** The POPULATION has not drifted - a census re-derived from the live library reproduces every figure in this sentence digit for digit, the 185382 total included - so what moved is the EVIDENCE TABLE above it: CS-469 (session 17) gave `IntProperty` and `FloatProperty` a second oracle, and `objects.EVIDENCE_FOR_VALUE_TYPE` now records `magnitude_distribution` beside `declared_width` for both. Width-only is owned by `objects.WIDTH_ONLY_VALUE_TYPES` - BoolProperty, Int8Property, UInt32Property - and carries **4910 of 185382, which is 2.6 per cent**, with the table tied to the running controls by `tests/save/test_properties.py::test_the_magnitude_oracle_covers_exactly_the_types_marked_with_it`. Read the share from that constant and the census, never from this sentence. The width check carrying the remaining 2.6 per cent is the one the module ITSELF records as "defensive rather than measured", and loosening it survives the whole suite. **THE ENDIANNESS HALF CARRIED A ONE-COMMAND DEMONSTRATION AND ITS VERDICT WAS MEASURED FALSE 2026-08-23 (session 34).** The demonstration itself still stands: patching `"IntProperty": (4, "<i")` to `">i"` turns all 75136 IntProperty values into byte-swapped garbage. What is FALSE is the sentence that followed it - that the ONLY tests going red are synthetic-fixture ones whose own section comment disclaims them as evidence about the game's format. **RE-MEASURED rather than inherited, with the mutant asserted live in the LOADED module rather than merely written to the file, a full-suite green floor taken at the same tree, and the same named tests re-run 13 of 13 after the revert so the reds cannot be a library that moved mid-session: 13 tests fail and FIVE ARE LIBRARY-BACKED** - `tests/save/test_properties.py::test_the_int32_byte_order_is_discriminated_by_the_stored_high_byte`, whose OWN docstring carried the false sentence, plus `test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate`, `test_the_int32_oracle_still_separates_a_type_it_can_separate`, `test_the_displacement_the_value_oracle_tolerates_is_the_one_the_anchor_catches` and `test_the_mantissa_coarseness_oracle_separates_the_middle_swap_from_the_identity` in `tests/save/test_value_anchoring.py`. Each was confirmed library-backed by its own skip guard, not by inspection of its name. The sentence was TRUE WHEN WRITTEN and was left standing while the magnitude oracle and CS-469's third oracle landed under it; nobody re-ran the demonstration. **Do not cite this flip as an open gap without re-running it first.** What the library evidence supports is accordingly narrower than the old closing sentence allowed: `objects.BYTE_ORDER_SURVIVING_CANDIDATES` is a SINGLETON derived from real saves by three oracles, and a wrong shipped byte order reddens in five library-backed places rather than none. Whether that MEETS clause 3 is a judgement this correction deliberately does not make - it records what was measured, and the close stays with the operator and an adjudicator that did not produce the measurement.

### CS-421 - fences

**STATUS 2026-08-23: CS-421 IS CLOSED - see `docs/LEDGER.md`. The sentences below saying it
stays OPEN are history and are not edited. The live fences travel with CS-825 and CS-826; read
the banner under `CS-421 - detail`.**

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md` and these fences are LIVE instructions rather than history - read them before taking CS-421.

**THE FENCES, WHICH ARE WHAT THIS ENTRY OWNS. (1) DO NOT RE-PITCH THE CLOSE ON THE ARTIFACT EXISTING** - it is right, graded and shipped; what is refused is reading it as clause 3 settled, because 65280 of the 65535 values a population of this size and shape could carry would drive the same oracle to a GREEN verdict and only 255 reach the state recorded here, so the verdict is a fact about this type carrying 6400. **(2) DO NOT REWRITE THE THREE SENTENCES MEASURED FALSE AND CORRECTED IN PLACE:** that the derivation is threshold-free; that accumulator INVARIANCE under the reversal is the right predicate (equal counters also mean both ZERO - the predicate is the universal now); and the unqualified spelling `oracle_cannot_separate`. **(3) DO NOT RE-DERIVE THE ANCHOR** - it is CS-479. **(4) A NON-NEGOTIABLE 12 EXPOSURE WAS INTRODUCED AND REPAIRED IN THE SAME SESSION;** `test_a_raise_in_the_scoring_phase_carries_nothing_out_of_the_walk` grades the containment and must not be deleted as redundant. Residuals filed as CS-478 and CS-479.

### CS-422 - detail

NOTE: filed 2026-08-15 by the measurement-validity adversary, which found the module holding opposite standards in one file. `_SOFT_OBJECT_TAIL_BYTES = 4` SHIPS on "exact consumption on all 116 instances" - consumption at the shipped alignment, n=116, never rotation-controlled - while ArrayProperty is DECLINED on exactly that evidence class at **n=11976**. On sample size the inconsistency reverses: TextProperty is declined at n=10 as too few, and UInt32Property ships at **n=9**. Neither call is obviously wrong; having both in one file with no stated rule is. Also fold in the adversary's measurement that the module's claim "mis-stating any one of them desynchronises the walk immediately" is FALSE AS WRITTEN: terminator reached out of 129775 payloads is 129775 shipped, 129695 with SetProperty 1 to 0, and 129744 with MapProperty 2 to 1 - so SetProperty's width is discriminated on 80 payloads and MapProperty's on 31. "Immediately" overstates a real but narrow discriminator. **AMENDED 2026-08-15 (session 8): the clause "and no test reads either signal" WAS TRUE WHEN WRITTEN AND IS NOW FALSE** - a shipped oracle reads both and reddens on both mutants, confirmed independently by an adjudicator and an adversary; detail in `docs/history_notes.md`. **NONE OF CS-422'S ACCEPTANCE MOVES**, which is the point of amending rather than closing: this item is ONE STATED RULE governing when a width may ship, and nothing has touched `_SOFT_OBJECT_TAIL_BYTES`, ArrayProperty, TextProperty or UInt32Property. Note also that `_TAG_EXTRA_STRINGS`'s own docstring still carries the false-as-written "immediately" sentence - session 8 edited the commentary block directly above it and deliberately left this one, because it is CS-422's to fix. **AMENDED 2026-08-16 (session 9): the 'immediately' sentence is now QUANTIFIED, and it is still in the shipped docstring.** CS-420 measured every width at -1 in the shipped copy alone: the terminator reach breaks on 6 of 6, but ByteProperty -1 still leaves 124416 of 129775 payloads reaching. So the walk desynchronises on a MINORITY of payloads for that width, not immediately, and the honest replacement is a per-width statement the suite derives rather than one adverb. CS-420 deliberately left this docstring untouched because it is CS-422 property; the measurement is recorded here so the next slice inherits evidence rather than re-deriving it.

### CS-442 - detail

**CS-442 CLOSED 2026-08-22 (session 30) - see `docs/LEDGER.md`. This block is the record of how
it was filed and is NO LONGER A LIVE INSTRUCTION.** Two of its figures were superseded by the
re-derivation it asked for: the population is EIGHT rather than seven, because the bare-identifier
shape this block correctly calls the most important one to cover was UNMEASURED when it was
written and yielded one more; and a ninth candidate was rejected as an artifact of resolving
`def` alone. The guard, the four dispositions and the corrections are in the ledger entry.

NOTE: filed 2026-08-16. `docs/LEDGER.md:128` cites `tests/save/test_absolute_claims.py::test_the_scanned_prose_carries_no_unbacked_absolute_claim`, which occurs ZERO times; the real name is `test_the_fenced_prose_carries_no_unbacked_absolute_claim`. Corrected by a new record, because this file is append-only. **THE STRUCTURAL FACT IS THE ITEM AND IT IS SHARPER THAN THE TYPO: NOTHING IN THIS REPOSITORY READS `docs/`.** `tests/save/test_oracle_citations.py` scans `clockspeed/`, `tests/save/test_absolute_claims.py` scans `tests/`, and neither looks at `docs/` at all - so the VERIFICATION POINTER, which is the one field `docs/LEDGER.md` declares MANDATORY and the entire reason that file is trustworthy, is unguarded. Note the append-only tension to solve rather than inherit: a correct citation can be invalidated by a later legitimate rename, so the rule must distinguish a pointer that was WRONG WHEN WRITTEN from one the tree moved out from under, and the second is not a defect in the record. **SHARPENED 2026-08-16 (session 12) BY A CENSUS RATHER THAN AN ANECDOTE - the population is bigger than the one typo this entry was filed on, and it is FIVE, not one.** Re-derive rather than trusting these figures, but as measured that day: of the `path::name` citations in `docs/`, five resolved to no name defined anywhere in the tree, in `docs/LEDGER.md` alone, spanning entries written across several sessions rather than clustering in one. **THREE DESIGN FACTS THE CENSUS TURNED UP, each of which a naive checker gets wrong.** FIRST, the dead name this entry already names occurs at a SECOND site that a `path::name` scanner structurally CANNOT see: it sits inside a `grep -c <bare name>` command in the MANDATORY `Verification:` field, as a bare identifier with no path attached. That is the single most important shape to cover, because the Verification pointer is the entire reason the ledger is trustworthy, and it is the shape most likely to be missed. SECOND, **a `file:line` citation into `docs/LEDGER.md` rots BY CONSTRUCTION**: the ledger is append-only NEWEST-FIRST, so every existing line number shifts down whenever an entry is prepended - which is why this entry's own `docs/LEDGER.md:128` pointer no longer names the line it was written for. A rule that treats a drifted ledger line number as a defect will be red on correct history. THIRD, and this is a warning about the checker rather than about the tree: the census's own `file:line` arm reported six dead targets and **all six were ARTIFACTS** - bare basenames like `objects.py:1666` which the checker resolved repo-relative and then declared missing. An unqualified citation is not a dead one. Discarding that number was the right call and the next checker must not re-earn it.

**RE-DERIVED 2026-08-22 (session 28) BY /insights, WHICH IS WHAT THE PARAGRAPH ABOVE ASKS FOR. The population is SEVEN, and it is a FLOOR rather than a total.** Method, so the next pass can reproduce or refute it: extract every `path::test_name` match from `docs/LEDGER.md`, drop the two that sit ABOVE the `## Entries` heading because those are the preamble's illustrative pointers and not citations, then for each remaining pair check that the file exists and that `def <name>(` occurs in it. As measured that day: 68 distinct citations inside entries, 61 resolve, 7 do not. **RE-DERIVE RATHER THAN TRUSTING THAT FIGURE.** The floor caveat is the important half and it is the SECOND design fact above restated as a limit: this census reads the `path::test_name` shape ONLY, so the bare-identifier-in-a-`grep -c` shape - which the paragraph above calls the single most important one to cover, and which a `path::name` scanner structurally cannot see - remains UNMEASURED, as does every `file:line` citation. Seven is what one shape yields, not what the ledger holds.

**THE SEVEN SPLIT INTO THREE REPAIR CLASSES, AND THE CLASSES MATTER MORE THAN THE COUNT, because the append-only rule prices them differently.**

**CLASS 1 - THE TREE MOVED, THE RECORD WAS RIGHT WHEN WRITTEN (three).** All three are CS-471's, at `docs/LEDGER.md` lines 431 to 433, and all three name `tests/save/test_properties.py` for tests that CS-495 relocated to `tests/save/test_reach_guard.py`, where all three are live today: `test_every_library_reaching_module_in_the_package_is_declared`, `test_the_suite_wide_guard_catches_a_module_that_declares_nothing`, `test_a_helper_handing_back_a_wrapped_body_is_flagged_as_propagating`. **This is exactly the case the acceptance already reserves a stated rule for, and it is NOT a defect in the record.** A checker that reddens on these reddens on correct history, which is the same trap the `file:line` fact above describes.

**CLASS 2 - WRONG WHEN WRITTEN, WITH ONE UNAMBIGUOUS LIVE TARGET (three).** Each is a one-word slip, and each was confirmed with `git log -S"def <name>(" -- '*.py'`, which returns NOTHING for the cited name against a control that returns two commits for a live one - so these names were never in any `.py` file in this repository's history, and the string occurs only inside `docs/LEDGER.md` itself.

| Cited | Real, measured live | Slip |
|---|---|---|
| `tests/save/test_absolute_claims.py::test_the_scanned_prose_carries_no_unbacked_absolute_claim` | `test_the_fenced_prose_carries_no_unbacked_absolute_claim` at `tests/save/test_absolute_claims.py:1182` | `scanned` for `fenced` - already named in the paragraph above and still unrepaired |
| `tests/data/test_registry.py::test_the_misspelled_keys_are_used_verbatim_not_autocorrected` | `test_the_misspelled_game_keys_are_used_verbatim_not_autocorrected` at `tests/data/test_registry.py:278` | the word `game` dropped |
| `tests/save/test_workdir.py::test_the_refusal_message_carries_no_non_digit_account_directory` | `test_the_refusal_message_carries_no_raw_account_directory_of_a_non_digit_shape` at `tests/save/test_workdir.py:421` | the word `raw` dropped and the shape suffix compressed |

The third one is an INFERENCE and is labelled as one rather than rounded up. Two live candidates share the prefix - `..._carries_no_raw_account_directory` at `test_workdir.py:401`, added 2026-08-14, and the `..._of_a_non_digit_shape` variant at `:421`, added 2026-08-16 in `60068a9`. The citation is CS-454's, CS-454 is about the non-digit shape specifically, the entry was written 2026-08-16, and the citing sentence reads "for what now passes" - so `:421` is the target on the evidence, but confirm it against the CS-454 entry before writing the correcting record.

**CLASS 3 - WRONG WHEN WRITTEN, NO UNAMBIGUOUS TARGET (one).** `docs/LEDGER.md:1855`, entry CS-433, cites `tests/save/test_properties.py::test_the_reach_guard_catches_every_spliced_shape`. Never in history by that name. `spliced` names a whole FAMILY of guard-gutting controls spread across eight test modules - `test_the_guard_catches_a_spliced_uncontained_helper` alone exists in five files - and none of them is a single obvious referent for "every spliced shape". **This one needs judgement, not a script**, and it is the case that decides what the stated rule does when no target can be identified at all.

**THE CONSTRAINT THAT SHAPES THE WHOLE ITEM, and the acceptance does not currently name it.** `docs/LEDGER.md` is append-only and its own preamble says a record that turns out to be wrong gets a NEW, LATER record. So the four in classes 2 and 3 CANNOT be repaired by editing the entries that carry them - each needs a correcting record, which is what the paragraph above did for the first one in prose and what nothing has yet done in the ledger. The three in class 1 need no ledger change at all; they need the checker's rule. **Note the live precedent for getting this wrong:** `4b2d04c` corrected the CS-500 to CS-501 collision by EDITING the CS-493 entry in place at `docs/LEDGER.md:131`, and the text it inserted claims the collision "is corrected here rather than by editing the entry that made it" - while sitting inside the entry that made it. Whatever rule this item states, it competes with a habit that has already reasserted itself once.

### CS-702 - detail

filed 2026-08-22 (session 28) by /insights, measured against the artifact rather than remembered.

CS-702 - The no-agent-trailer rule is recorded but UNENFORCED, and commits on `main` already carry the trailer it forbids - acceptance: a `Co-authored-by:` trailer naming an agent is BLOCKED end to end - stage a violation, attempt a real commit, assert HEAD is unchanged - and the overtaken claim in `docs/GATED.md`'s DATED operator-decision section is resolved by NEW text rather than by a rewrite of the dated record - tier: 1

**THE MEASUREMENT. RE-DERIVE RATHER THAN TRUSTING THESE FIGURES.** As measured that day: of 171 commits on `main`, EIGHTEEN carry `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` - seventeen dated 2026-08-14 and one dated 2026-08-15, oldest `e9af2df`, newest `5907d45`, and ZERO since. Method matters here and a naive census gets it wrong: match a body line whose stripped form STARTS WITH `co-authored-by:`, which is the trailer shape. A plain `grep -i co-authored` also matches prose ABOUT the rule - this block included - and inflates the count.

**WHAT IS FALSE AND WHAT IS NOT, because the distinction decides what the repair is.** `docs/GATED.md` lines 144 to 149 record the operator decision that no commit carries the trailer, and say "Measured at the time of the decision, no commit did - the trailer had never been added - so this is a standing rule going forward rather than a cleanup, and it costs nothing to keep true". **THE MEASUREMENT SENTENCE WAS PROBABLY TRUE WHEN WRITTEN AND MUST NOT BE REPORTED AS A LIE:** its section is headed `Operator decision 2026-08-13`, and every one of the eighteen postdates that by one or two days. What has been OVERTAKEN is the consequence drawn from it - the history now needs a cleanup for the rule to be true of it, and "costs nothing to keep true" was not borne out.

**THE ENTRY PREDICTED ITS OWN FAILURE MODE IN THE VERY NEXT SENTENCE AND SHIPPED NO MECHANISM.** It says it is recorded there "because a trailer is trivial to reintroduce by default and impossible to remove later without the rewrite this section exists to avoid". Seventeen were reintroduced by default the following day. That is the entire argument for this item: a rule kept by habit, against a tool whose default violates it, is a rule that fails on the first session nobody is watching - and this one failed on the next.

**NOTHING ENFORCES IT, MEASURED.** `grep -rniE 'co.?authored' .githooks/ tools/precommit_gate.py scripts/` returns no match, exit 1. `.githooks/commit-msg` checks the character set, a 72-byte subject cap and placeholder subjects; it does not look at trailers at all.

**THE PRESSURE IS CONTINUOUS, NOT HISTORICAL.** The harness driving most sessions appends the trailer BY DEFAULT unless it is suppressed, so every session is a fresh chance to reintroduce it and the count above is a snapshot rather than a closed set. This is why the acceptance asks for a blocking gate rather than a one-time scrub: a scrub leaves the next default untouched.

**TWO CONSTRAINTS ON THE REPAIR, both of which an eager slice will walk straight past.** FIRST, `.githooks/*` is on the `CLAUDE.md` section 6 frozen list, so the gate needs an explicit operator grant routed through an adjudicator and recorded in `docs/LEDGER.md` BEFORE the edit is made. No agent grants itself this one. SECOND, the `docs/GATED.md` section carrying the overtaken claim is DATED, and `CLAUDE.md` section 4 rules that a heading carrying an explicit date marks its own section historical - so the correction is NEW text stating the measurement and its date, not a rewrite of the 2026-08-13 record. Rewriting it would destroy the most useful thing that section now holds, which is the evidence that the rule was written down before it was broken.

**AND DO NOT CLOSE THIS BY ASSERTING THE HOOK EXISTS.** `CLAUDE.md` section 2.2 is explicit that a hook's presence is never proof it fires, and the only valid test is end to end. That is why the acceptance names the transcript rather than the file.

**WHAT THIS ITEM DOES NOT CLAIM.** CS-G03's flip is NOT breached by the eighteen. Its eighth precondition speaks of the PUBLISHED history, and that same section rules the published history is generated fresh from a squash or an orphan branch, which need not carry them. The live defects are the unenforced rule and the stale consequence, not the flip.

---


## CS-703 - detail

**CLOSED 2026-08-22 (session 32).** The item shipped; see `docs/LEDGER.md` for the closure
record and its residuals. Nothing below is a live instruction. The measurement it records is
still accurate except where the block itself already carries a correction.


Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) by the CS-702 bypass adversary, MEASURED with a real commit rather than reasoned. All three hooks carry a byte-identical `cs_probe` running `"$1" -c "raise SystemExit(0)"` and judging only the exit code, so `true`, `:` and `echo` all pass (**CORRECTED 2026-08-22, session 32, by two agents that RAN it rather than read it: this sentence first named `env`, which does NOT pass - GNU `env` rejects `-c` and exits 125 - and did not name `echo`, which does. The item is unaffected, because `true` is precisely the argument-ignoring program the acceptance names.**); the heredoc is then handed to that program, which ignores it and exits 0, and the hook reports success. THE BLAST RADIUS IS WIDER THAN PHASE 7 - the same ladder fronts the character-set gate, the secret scan and the whole-suite pre-push run. The hooks' own text says an unrunnable check is not a passed check: the no-interpreter branch honours that and the wrong-interpreter branch does not. THIS IS THE CS-806 SHAPE A SECOND TIME - that item closed by making the environment check assert the RESOLVED interpreter instead of trusting a name, and the same assertion was never made here. **NEEDS A FROZEN-FILE GRANT for all three hooks.**

### Archived 2026-08-23 from `WAKEUP_NOTES.md` - session 32 at full fidelity

Aged out when session 35 landed and `WAKEUP_NOTES.md` keeps only the last three sessions.
**Nothing here is current.**

## Session 32 - 2026-08-22 - CS-703 and CS-819 both CLOSE after FOUR refutations, and the transferable finding is that a probe validated one channel while every gate read another

- **Shipped: CS-703 and CS-819 CLOSED. Filed CS-815, CS-816, CS-817, CS-818, CS-820, CS-821,
  CS-822, CS-823.** Detail in `docs/LEDGER.md`, not here. **TWO ITEMS CLOSED AND EIGHT FILED, and
  seven of the eight are defects in things already green and already reported done.** Two frozen-file
  grants were issued, adjudicated and recorded BEFORE any edit, in their own commit.

- **THE HEADLINE IS NOT THE ITEM AS FILED. CS-703 was reported as an environment-variable problem
  and it never was one.** The repaired probe's FIRST build validated STDOUT while every gate decision
  in every hook reads `$?`. A wrapper that forwards stdout faithfully and drops the exit status
  therefore answered the probe with the exact token and turned all three tier-0 gates into no-ops -
  and it reached that through the ladder's own `python` rung **with no environment variable set at
  all**. Two ordinary shapes do it and neither knows the token: a POSIX wrapper ending in `| cat`,
  and a Windows `.cmd` using `setlocal`/`endlocal`. **A PROBE THAT VALIDATES ONE CHANNEL WHILE THE
  CONSUMER READS ANOTHER PROVES NOTHING**, and that is the sentence to carry forward.

- **FOUR REFUTATIONS, NOT ONE FROM READING THE CODE.** Every one came from an agent RUNNING it, with
  real commits and real pushes. Round one: the stdout/exit-code split above. Round two: the
  commit-msg hook FAILS OPEN under MSYS2 dash, which became CS-819. Round three attacked the SUITE
  rather than the hooks and killed three mutants. Round four found CS-823 and one message defect.

- **THE MERGER'S OWN ORACLE SHARED THE SUITE'S BLIND SPOT, TWICE, AND THAT IS THE METHOD LESSON.**
  It graded the first build 15/15 while four escapes were live, because every substitution arm used
  `true` - which fails at the stdout comparison and never reaches the exit-code question. It also
  drives real git, which on Windows is bash, the one shell where the dash fail-open is invisible.
  **A harness that cannot reach a channel cannot grade it.** Both gaps are closed; it now runs 23
  arms, 6 of which fail against the pre-repair hooks.

- **Decisions: no ADR. Four that must not be reopened.** The probe demands BOTH a computed token and
  a returned failure code; a set-but-broken `CLOCKSPEED_PYTHON` is REFUSED rather than silently
  replaced, which exceeds the filed acceptance and was an OPERATOR instruction, recorded as such.
  Exact equality beats containment because **a loud false refusal beats a silent false accept in a
  gate**. CS-819 ships a SENTINEL rather than moving the program into a file, because an empty file
  exits 0 just as silently - it removes a cause without establishing the invariant. And no heredoc
  size guard: 4096 is one dash build's property, so a size assertion is a proxy for the property
  rather than the property.

- **Surprises: nothing contradicted `BOOTSTRAP.md`. Two things contradicted ME, and both corrections
  are in tracked files rather than only here.** I reported CS-819 as affecting "most Linux
  developers"; that is REFUTED by this project's own CI - `tier1` run `32601774702` at `32a982c`
  ran on ubuntu-latest, where `/bin/sh` IS dash, with the over-threshold body, and 23 commit-msg
  tests with no skip markers passed every violation class. It is MSYS2-only and LATENT. Separately
  the CS-703 detail block named `env` as passing the old probe; it does not on this toolchain, and
  `echo` does and was unnamed. Both corrected per CLAUDE.md section 8.

- **Failed paths, so they are not retried.** A probe that reads only stdout - refuted by measurement,
  above. A byte-identity check scoped to the probe alone leaves the refusal block unpinned, and two
  mutants survived in exactly that gap. Message-content arms hardwired to ONE hook let a grant
  condition be deleted from the other two with the suite green. And the harness bash heredoc ate
  backslash continuations AGAIN, silently, on a patch script - the Write tool is the answer, every
  time, and this is the fifth session it has cost.

- **CI CAUGHT A DEFECT THAT THE LOCAL SUITE AND THE PRE-PUSH HOOK BOTH PASSED, and it is the last
  lesson of the session.** `be5cd81` was green locally at 2464 passed and green through the whole-suite
  pre-push run, and `tier1` was RED on it: six failures, one cause. Both dash platform arms encoded
  **"dash truncates the heredoc"**, which is false - the truncation is a property of the MSYS2 BUILD,
  not of dash. On `ubuntu-latest` the program ARRIVED, every rule fired correctly and reported its own
  reason, and the arms read CORRECT BEHAVIOUR as a broken premise. The hooks were never wrong on either
  shell; the acceptance was. **A PLATFORM PREMISE BAKED INTO A TEST IS THE SAME DEFECT CLASS AS A HOOK
  THAT TRUSTS A NAME** - an assumption asserted rather than measured - and the fix is the same: measure
  the property at run time and branch on it. Fixed in `a2a89ed`; both branches now assert something
  true and neither is a skip.

- **THAT FAILURE DISCHARGED A RECORDED RESIDUAL, which is the one good thing about it.** The CS-819
  grant listed "whether glibc dash delivers a heredoc above 4096 is INFERRED, not measured" as open.
  The CI log measures it: **4535 delivered bytes**, against 0 on the MSYS2 build. The delivered-bytes
  control the adjudicator insisted on is what measured it, by FAILING LOUDLY rather than passing
  quietly, on the first CI run after it shipped.

- **A PROCESS MISTAKE WORTH NOT REPEATING: I pruned the builder's worktree before CI was green.** When
  CI went red the agent that knew the module could not be resumed - its worktree was gone and the
  fallback directory was outside the session's fences. **Do not prune a worktree until CI is green on
  the commit that merged it.** The repair was done in the main checkout instead, which was fine here
  only because the diagnosis was precise and the change was one file.

- **A DEVIATION RECORDED RATHER THAN CLAIMED MET.** Both grants ask that `scripts/install_hooks.py`
  run clean. Its `inspect_hook` was run over all three hooks and passed; the WHOLE script was not,
  because `install()` writes `core.hooksPath` RELATIVE where this machine holds it ABSOLUTE - from a
  worktree that repoints hook resolution to that worktree's own copy, which would let an agent
  editing a hook disarm the gate judging its own commit. Changing the operator's git configuration
  was not a side effect these items were entitled to take.

- **In flight: NOTHING from this session.** Working tree clean. The four pre-existing worktrees
  (CS-492 rounds seven to nine and the two-site spike) and branch `cs807-attribute-half` are
  UNTOUCHED and still unmerged, exactly as session 31 left them. One NEW worktree,
  `agent-ab7fcd5c63f9193ea`, is fully merged and prunable.

- **Next action: CS-823.** It is tier 1, the fix is already designed and measured, and it needs a
  frozen-file grant for `.githooks/pre-commit` before a line is written. `pre-commit` runs the gate
  with no proof of execution, so an empty or truncated `tools/precommit_gate.py` passes it silently -
  and 1019 of 2395 truncation points still compile.

### Archived 2026-08-22 from `WAKEUP_NOTES.md` - session 28 at full fidelity

Aged out when session 31 landed and `WAKEUP_NOTES.md` keeps only the last three sessions.
**Nothing here is current.**

## Session 28 - 2026-08-22 - an /insights pass; NOTHING CLOSED and four findings filed, one of which reversed under its own evidence

- **Shipped: NOTHING CLOSED, and no code at all.** Zero `.py` files touched across four
  commits. This was a reporting session that turned into a filing session. CS-702 and CS-806
  are NEW items; CS-442 gained a re-derived measurement; CS-G01 and CS-G05 gained dated status
  blocks. Ledger entry for the session is a NON-CLOSURE record and says so in its heading.

- **THE FINDING THAT ORGANISES THE SESSION: the ledger's own verification pointers are
  unguarded, and 7 of 68 do not resolve.** CS-442 has been open on this since 2026-08-16 with a
  census of five; re-deriving it gives seven, in three repair classes that price differently.
  Three are stale PATHS from CS-495's relocation and are NOT defects in the record. Three are
  one-word slips whose real target is measured and named. One, CS-433's, has no identifiable
  target at all. **The four wrong-when-written ones cannot be repaired by editing the ledger,
  because it is append-only** - each needs a new correcting record, and `4b2d04c` has already
  broken that rule once by correcting the CS-500 collision inside the entry that caused it.
  **Seven is a FLOOR:** the census reads `path::test_name` only, and the bare-identifier shape
  that CS-442's own block calls the most important one is still unmeasured.

- **THE CORRECTION, AND IT IS THE ONE TO CARRY FORWARD.** CS-G01 was first written up as "S4
  succeeded, so this gated item should have been VOIDED and was not". **THAT IS BACKWARDS.** ADR
  0003's Consequences section refutes it: S4 SPLIT - geometry yes, semantics no. The save carries
  placement and provably does not carry purity, so the asset path is now LOAD-BEARING for the
  semantics half rather than a superseded fallback, and the ADR says so in terms. Condition 1 of
  CS-G01, read literally, would VOID an item that ADR makes necessary. **The dangerous direction
  on that item is the false void, not the missed one** - and this file's rule against synthetic
  closure runs in that direction too. Do not re-derive the first reading.

- **CS-702 is filed and it is not a paperwork item.** The no-agent-trailer rule recorded in
  `docs/GATED.md` is enforced by NOTHING - no hook, no gate - and 18 of the 171 commits on `main`
  already carry the trailer, all dated 2026-08-14 and 2026-08-15, none since. The GATED.md
  measurement sentence was probably TRUE when written on 2026-08-13; what is overtaken is its
  consequence, "a standing rule going forward rather than a cleanup". **The entry predicted its
  own failure mode in the very next sentence and shipped no mechanism, and seventeen trailers
  arrived by default the following day.** The harness default still adds one every session
  unless suppressed, so the pressure is continuous. `.githooks/*` is FROZEN, so the gate needs
  an adjudicator route and a ledger grant BEFORE the edit.

- **Surprises: the /done ritual tripped over its own documented command.** `py -3` and `python`
  are DIFFERENT Python 3.14.4 installations on this machine and only `python` has `ruff`, so the
  documented tier-0 gate `py -3 -m ruff check` exits 1 with a module error. Filed as CS-806.
  `scripts/verify_env.py` passes under both and is not wrong to - it probes the toolchain by NAME
  on PATH. Also observed: port 8901, this project's allocated dashboard port, has been held by an
  unrelated third-party process since 2026-08-16 and verify_env has been reporting it as a SOFT
  failure on every run. Filed in `BACKLOG.md`; nothing was killed or re-recorded.

- **Failed paths: none - but one method is worth not re-inventing.** Distinguishing a citation
  that was WRONG WHEN WRITTEN from one the tree moved out from under needs
  `git log -S"def <name>(" -- '*.py'` with a control on a live name, because a bare `grep` over
  the history matches the ledger prose that names the test and reports a false positive. The
  same trap bit the trailer census: `grep -i co-authored` matches prose ABOUT the rule, so the
  count must match a body line whose stripped form STARTS WITH the trailer key.

- **ROADMAP.md IS EFFECTIVELY FULL: 97 bytes of margin against its 60 KB budget.** Two items
  were filed into it this session and CS-442's note was already trimmed to a pointer once to make
  room. **The next session relocates before it files anything.** The budget is severity WARN and
  will not fail CI, which is exactly why it needs acting on.

- **Next action:** relocate ROADMAP.md notes into `docs/history_notes.md` until the file has
  real margin, then take CS-442 - the seven are enumerated with their targets, the three classes
  are stated, and the append-only constraint is written down, so the item is now a mechanism
  question rather than a discovery one.

<!-- Newest first. Each block: date archived, source file, then the content. -->

### Archived 2026-08-16 from `WAKEUP_NOTES.md` - session 9 at full fidelity

Aged out when session 12 landed and `WAKEUP_NOTES.md` keeps only the last three sessions.
**Nothing here is current.** Note in particular that this entry lists CS-425 as CLOSED; it is
NOT - its only ledger record is a frozen-file grant that declines to close it, and it remains
OPEN in `ROADMAP.md`. That error was inherited forward for three sessions.

## Session 10 - 2026-08-16 - eight items close; three of four slices refuted; CS-420 fails a fifth time

- **Shipped: CS-403, CS-209, CS-423, CS-429, CS-430, CS-431 CLOSED, plus CS-433 and CS-434 which
  are repairs of this session's own refuted work. CS-204's RECORD corrected - it had closed on
  2026-08-14 and its ROADMAP line outlived it by two days. CS-420 STAYS OPEN.** Filed CS-211,
  CS-435, CS-436, CS-437, CS-438. Suite 1733 -> **1846 passed, 3 skipped**, exit 0; skips fell
  from 7 to 3 because CS-423 removed four silent ones. mypy 78 files clean, ruff clean, drift
  guard CLEAN 8/8, doc budget PASS. Nine commits, `995cf0b..4e6b19a`. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THE HIT RATE AGAIN, AND IT DID NOT IMPROVE. THREE OF FOUR SLICES WERE REFUTED
  BY INDEPENDENT ADVERSARIES, EVERY FINDING INVISIBLE TO A GREEN 1819-TEST SUITE.** Not one was a
  style quibble:
  1. **The commit gate FAILED OPEN AT 513 ENTRIES.** `MAX_SAVE_ROOT_ENTRIES` truncated SILENTLY at
     two of its three sites, ALPHABETICALLY, before the newest-first sort - so the saves dropped
     were exactly the recently-played ones. At 511 and 512 the gate blocked an undeclared world
     token; at 513 it exited 0, the commit landed with the token in the blob, and the operator was
     told "no world token is discoverable on this machine". Not silence - a false statement. The
     function's own docstring said "Truncating alphabetically would silently drop the recent ones"
     while doing exactly that. Test coverage of the constant was zero. **It needs no attacker,
     only time**: autosave rotation grows one directory forever.
  2. **CS-423 SHIPPED A FALSE GUARANTEE.** `objects.py` was graded `retains-no-save-bytes` while
     `_Cursor.__init__` binds the decompressed body to `self._data`. The checker inspected only
     `@dataclass` fields. A green oracle asserting a property the module lacks is worse than the
     silent skip the item was filed to remove.
  3. **THE CONTAINMENT GUARD WAS BLIND TO ONE KEYWORD.** `ast.AsyncFunctionDef` is not a subclass
     of `ast.FunctionDef`, so an `async def` helper with a body BYTE-IDENTICAL to the existing
     splice control passed cleanly. Seven of eight spliced shapes escaped. **The same commit
     enumerated the path-bearing primitives in a neighbouring file** while the reach guard listed
     none of them - guard inversion re-shipping inside the guard built to prevent it, two sessions
     running.
  4. **CS-430's WARNING DETAIL WAS FALSE.** It said a skipped node record's "placement is
     unrecoverable from this save". `transform is None` implies a levelled COMPONENT, and a
     component closes with a parent path: 27865 of 27865 transform-less records carry a non-empty
     parent, 27420 of those naming a placed record. **The defect the item exists to fix, reproduced
     inside its own fix** - moved from the subject key to the detail text, where nothing looked.

- **CS-420 FAILED FOR THE FIFTH CONSECUTIVE ROUND, and the fence it shipped is why it stays open.**
  The mechanical check exists, reads three prose channels, is proven to fire against the real tree,
  and gutting it is visible. It still does not fence: an adversary inserted three genuine ADR-0008
  tier-1 universal claims into the fenced module, byte-verified, and the suite stayed
  byte-identically green. 19 of 22 real universal phrasings carry no listed marker; ten prose
  channels are unread; **571 of 573 sentences (99.7 per cent) are not read by the rule**;
  `FENCED_MODULES` is a hand-written tuple whose deletion leaves the suite green. Round five also
  shipped five false sentences, two contradicted by the module's own passing tests, and **the fence
  flagged 0 of the 5**. They were DELETED rather than rewritten, per ADR 0008's own remedy.

- **Decisions:** no new ADR. **ADR 0008 REMAINS `proposed` and STILL NEEDS AN ADJUDICATOR** - none
  was run this session. A NEW TENSION IS RECORDED FOR IT: ADR 0008 SCOPE says the mechanical fence
  "is scoped to where such claims actually cluster, and widening that scan is separate work", which
  the shipped fence matches word for word, while CS-420's acceptance says EVERY DECLARATIVE
  SENTENCE. Both readings are evidenced; neither was resolved. **A FROZEN-FILE GRANT WAS USED AND
  NOT WIDENED:** `tools/precommit_gate.py` under the 2026-08-15 grant, with zero exposure of any
  other frozen path, verified by diff on every merge.

- **Surprises**, each measured rather than reasoned about:
  1. **AN ITEM ON THE SESSION PLAN WAS ALREADY CLOSED, AND THE PLAN INHERITED THAT FROM A STALE
     LINE.** CS-204 closed 2026-08-14 in `e17ba59` - one commit carrying implementation, tests AND
     its own ledger entry - and its ROADMAP line was never removed. The 2026-08-15 operator grant
     then scoped itself to "the three OPEN items", which is exactly
     `grep -c "NEEDS ITS OWN FROZEN-FILE GRANT" ROADMAP.md` returning 3. **One stale line, read
     three times, by three readers who each had reason to think the previous one had checked.**
     Filed as CS-211: nothing in `tools/` reads ROADMAP.md's content at all.
  2. **SEVEN OF SEVEN WORKTREE AGENTS STARTED STALE**, up to five commits behind. Every one caught
     it only because the dispatch ORDERED the check. This is now unambiguous, not a fluke.
  3. **THE MERGER'S OWN `cd` PERSISTED AND PUT A MERGE ON THE WRONG BRANCH.** A squash-merge of
     slice D landed on slice B's branch. Nothing was lost - D's work was safe on its own branch and
     B's uncommitted work survived a `--mixed` reset plus a targeted checkout - but the fix cost a
     detour. Use `git -C <path>` for every git call; the shell's cwd is not a safe assumption.
  4. **AN ADVERSARY DISCARDED ITS OWN FIRST MEASUREMENT** after finding its extraction had silently
     produced head content in the base directory. A second discarded a gutting run after finding a
     stray `.git` in the control tree. Both caught it by hashing rather than by trusting the copy.
  5. **A BUILDER CHECKED THE MERGER AND WAS RIGHT TO.** Told a second sentence was probably also
     false, it measured, found it TRUE as written, and left it alone - noting that deleting a true
     sentence to be safe is its own defect.
  6. **A BUILDER'S FIRST SPLICE SHAPES DEFEATED THEMSELVES.** Four of eight named the locator, so
     the guard caught them on that rather than on the gap they were written for; it found and fixed
     that before reporting.
  7. **TWO REPAIRS SELF-ALLOCATED THE SAME NEW ID.** Both chose CS-433. Resolved by giving the
     merged one CS-433 and the other CS-434 at merge time. IDs are permanent and never reused, so
     an agent inventing one is a collision waiting to happen.
  8. **A PER-SITE MEASUREMENT NARROWED A RELAYED CLAIM.** "Both positional mutants survive" became
     three of five die, two survive - measured site by site rather than accepted.
  9. **THE MERGER STATED A SEVERITY THAT WAS WRONG AND A BUILDER CAUGHT THE SAME ERROR IN ITS OWN
     PROSE.** Both said CS-430's false detail is "rendered verbatim to the operator by the
     advisor". The advisor is a 32-line stub; that render path does not exist. The string reaches
     `WorldModel` verbatim and would surface once pillar 5 ships - latent, not live.

- **Failed paths - do not retry:**
  - **A hand-written marker list as a prose fence.** It misses 19 of 22 real universals. The list
    is the thing that rots, which is what the artifact was built to stop.
  - **Scoping a fence to a hand-written module tuple.** That is an allowlist with the sign flipped;
    deleting the entry deletes the coverage silently.
  - **Grading a module against a redaction oracle when no path reaches it.** It asserts something
    false. Name why absence-of-value is the mitigation and assert THAT.
  - **A blanket assertion over modules that do not share a justification.** Generalise the QUESTION,
    keep the ANSWERS distinct.
  - **Reading a verdict from an interpreter or a tree you did not verify.** Two adversaries lost a
    full pass to a silently wrong extraction this session.

- **Next action:** **CS-211**, the mechanical one-owner guard. It is cheap, it is tier 1, and it is
  the only item this session that would have PREVENTED a defect this session actually suffered -
  a builder dispatched to re-implement shipped work. Then **CS-435**, the fourth instance of the
  silent-loss family, which is the strongest argument that family needs mechanical detection rather
  than a fifth hand-fix. **Do NOT take CS-420 next** unless the ADR 0008 adjudication happens first:
  its acceptance and its governing ADR now disagree in writing, and building against an unresolved
  disagreement is how this item has failed five times.

## Session 9 - 2026-08-16 - four items close, and every single first build was refuted

- **Shipped: CS-419, CS-424, CS-425, CS-427 CLOSED. CS-420 WAS CLOSED AND THEN REOPENED THE SAME
  SESSION** - see the final audit below. ADR 0008 recorded (`proposed`). Filed CS-428, CS-429,
  CS-430, CS-431, CS-432, CS-701. Suite 1619 -> **1733 passed, 7 skipped**, exit 0. mypy clean,
  drift guard CLEAN 8/8, doc budget PASS. Detail in `docs/LEDGER.md`, including the CORRECTION
  entry that supersedes the CS-420 closure.

- **THE HEADLINE IS NOT A DELIVERABLE, IT IS A HIT RATE. FOUR OF FOUR FIRST BUILDS WERE REFUTED
  BY AN INDEPENDENT ADVERSARY, AND EVERY REFUTATION WAS INVISIBLE TO A GREEN SUITE.** Not one
  was a style quibble; each was a defect that would have shipped:
  1. **CS-420's derived test derived nothing.** Its attribution folded through `any()`, which
     short-circuits. With the reach oracle first and red on all six widths, the other two were
     consulted ONLY in the pristine control - invocation census 7/7/1/1 - and **gutting both to
     green no-ops left the suite passing.**
  2. **CS-419's fix introduced a behaviour regression.** The new warning reused the enum-name
     warning's `(code, subject)` key and was added first; `_WarningLog` keeps the FIRST detail,
     so a true "the enum was skipped" was REPLACED by a false "the enum is shorter than the file
     declares" while the enum was absent entirely.
  3. **CS-424 satisfied its acceptance against seven invented names**, and its tests said
     "shipped name" while meaning fixture name - **the acceptance READ as met because the test
     borrowed the acceptance's own word.** Its positive assertions were also a zero-iteration
     loop under an empty name table.
  4. **CS-427's new privacy guards were INVERTED.** They keyed on the CONTAINED routes, so a
     helper using an uncontained route never entered the graded set. Splicing the known-bad
     shape into a new helper left **13 graders passing while it leaked all three markers** - the
     ungraded-containment defect re-shipped inside the guard built to prevent it.

- **BOTH IN-FLIGHT AGENTS LANDED. Neither result was what the optimistic reading expected.**
  - **CS-425 CLOSED, and the main session proved the half the builder could not.** The builder built a
    NEW unfrozen `tools/pretooluse_gate.py` that parses the hook envelope, walks EVERY string in
    `tool_input` rather than an allowlist, and runs the frozen gate's charset and secret checks BY
    IMPORT. `tools/precommit_gate.py` is byte-identical - sha256 equal at base, worktree and HEAD, and
    `git diff --name-only` over every frozen path returns zero lines - so the grant it did NOT hold was
    never needed. **I then made the harness fire its own hook, which no subagent can do: a Bash call
    carrying a literal em dash was DENIED, naming the character and the column, and did not run.**
  - **`pythonw` IS PROVEN SAFE AND IS SHIPPED.** The builder measured it byte-identical across 13 probe
    cases but deliberately declined to ship it, because whether Claude Code's own spawn WAITS on a
    GUI-subsystem child was an inference rather than a measurement - and it was right to refuse. I
    settled it directly: under `pythonw` the em-dash probe is still DENIED with an identical diagnostic,
    and a clean ASCII call still runs. So the console flash goes away with the gate intact. **That
    judgement call - refusing to trade a verified gate for an unverified cosmetic win - was correct
    even though the answer came back favourable.**
  - **THE FINAL PROSE ADVERSARY RETURNED REFUTED, AND CS-420 IS REOPENED.** Six false sentences on
    merged `main`, THREE WRITTEN BY THIS SESSION'S OWN COMMITS. `IT NEVER RAISES` is false by execution
    on a forced `KeyboardInterrupt` - and CS-427 repaired that exact absolute in three sibling
    docstrings the same day while the fourth survived. The join mechanism sentence is false under both
    readings: `ByteProperty -1` rots 5359 payloads with `join.tags` at exactly 55496 and `join.words` at
    exactly 13, because **ByteProperty is not one of the 13 joined words at all**. And
    `_JOIN_WORD_FLOOR = 13` is a UNION over a growing library, not an engine constant - per-save counts
    run 8 to 12 and NOT ONE SAVE REACHES 13, so the floor can go red on a correct grammar. What the
    audit could NOT break: the derived test's structure, the two-copy common-mode claim, the
    bare-CI-box claim, the SystemExit residual, and the repaired no-install gating.

- **Decisions: ADR 0008, `proposed`** - a detection claim is DERIVED by the suite, never written.
  Three tiers by quantifier scope: universal claims DELETED (unverifiable by construction),
  existential claims DERIVED at runtime, mechanistic claims about adjacent code may stay prose.
  **It needs an adjudicator that wrote no part of it and no part of the implementing slices.**
  **A FROZEN-FILE BOUNDARY WAS ENFORCED RATHER THAN ASSUMED:** the recorded grant for
  `tools/precommit_gate.py` is scoped to CS-403/CS-209/CS-204 and **does NOT extend to CS-425**,
  per CS-204's own precedent. CS-425 was designed around it instead of self-granting.

- **Surprises**, each measured rather than reasoned about:
  1. **AN ADVERSARY WAS WRONG, AND I RELAYED IT AS FACT.** The CS-424 adversary reported a live
     invariant violation - `subject='post-schema-Object'` on the real usmap. The builder refuted
     it; I measured directly and the real file yields `subject='post-schema'`, with `names[0] ==
     'Object'` NOT a suffix of any subject. It had read its own name-interpolating mutant's
     output as pristine. **An adversary's quoted command output needs re-measurement exactly as
     much as a builder's claim.** I passed it on because it looked like evidence.
  2. **I CITED A DOCUMENT THAT DID NOT EXIST.** ADR 0008 was authored in the main checkout and
     left uncommitted, then cited as "in force" to three builders working in worktrees that
     could not see it. A builder ran `git log --all`, found nothing, and said so. Committed as
     `921e6d6`.
  3. **THE ADR CONTRADICTED ITSELF AND A BUILDER FOUND IT.** FORECLOSED banned superlatives in
     commit messages while SCOPE permitted recording "what a measurement found at a stated time"
     - and a power-control transcript is both. Resolved in `eeabbd2` on a principle: the ADR
     binds LIVING TEXT (read as describing the current tree, can rot) and not an IMMUTABLE
     TIMESTAMPED RECORD (commit message, ledger entry, wakeup note). The test is the tense the
     reader supplies - if deleting the sentence later would be a CORRECTION it was living text;
     if it would be FALSIFYING THE RECORD it was a record.
  4. **A BUILDER REFUSED MY GLOSS OF MY OWN ADR AS SELF-GRADING**, read the committed file, and
     audited against four requirements the gloss omitted. All four already passed - one of them
     only because an adversary had earlier forced it.
  5. **MY OWN DISPATCH SPECIFIED A VACUOUS ASSERTION.** I told a builder to assert "every width
     is caught by at least one detector". Taken literally that is TRUE BY ARITHMETIC, because
     `test_both_tag_grammar_transcriptions_agree` compares the two constant copies and reddens on
     any single-copy mutant without reading a byte of library. The builder excluded it and
     asserted its sensitivity separately.
  6. **A CLEVER ARGUMENT FOR WHY A CHECK COULD NOT BE BUILT WAS REFUTED BY BUILDING IT.** CS-424
     argued no sound install-gated repr oracle existed. An adversary wrote one in a single pass:
     **a withholding repr emits no string literal at all, so the oracle is "the rendering quotes
     nothing"** - neither substring nor skeleton, live against the real 57985-name table.
  7. **A MUTANT THAT FAILS TO APPLY LOOKS EXACTLY LIKE A TEST THAT FAILS TO CATCH.** A harness
     "reverted" a repr by deleting `repr=False`, which does NOT overwrite a `__repr__` defined in
     the class body, and reported three mutants SURVIVED when the mutation never landed. Harnesses
     must now prove the text actually changed before trusting a verdict.
  8. **`SystemExit` IS A NON-`OSError` AND WAS LIVE DISCLOSURE.** It escaped every repaired site
     and rendered the REAL Windows account name under `-q` alone. `KeyboardInterrupt` renders
     NOTHING without `--full-trace`. **The inherited residual note had the two exactly backwards,
     in the dangerous direction** - the abortability defence was protecting the type that does
     not disclose while the type that does got none.
  9. **A REAL BUG HID BEHIND FALSE PROSE.** Library-backed tests gated their skip on the SAVE
     library while the usmap comes from the INSTALL, so on a machine with saves and no install
     they FAILED rather than skipped. Nobody had run that configuration.
  10. **A FIX FALSIFIED PROSE IN TWO FILES IT DID NOT OWN.** CS-424's repr change made the stated
     reason for two `del` statements false. Both were REPORTED rather than widened into, and
     repaired by the merger once the owning slices had landed. This is ADR 0008 tier 3 behaving
     exactly as predicted - a mechanistic claim rots precisely when the code beside it changes.
  11. **THE BOUNDARY HELD EVERY TIME IT WAS TESTED.** Four separate builders found defects outside
     their write-lists and reported instead of widening. Every one became a filed item.

- **Failed paths - do not retry:**
  - **`any()` in a derived attribution.** It short-circuits, so a saturating first term hides
    every later one. Evaluate all members, then reduce.
  - **Keying a containment guard on the SAFE routes.** It detects safe helpers and is blind to
    unsafe ones - it is inverted by construction. Key on the RISKY primitives, plus a rule that
    follows return annotations for helpers that call no primitive themselves.
  - **A hand-maintained list of helpers to grade.** The list is what rots; derive it.
  - **Rewording a universal detection claim into a hedge.** ADR 0008 FORECLOSED names it: the
    hedge has the same falsification surface and reads as evidence.
  - **Substring matching to prove a repr withholds names.** Unsound - the shipped table contains
    the implementation's own field labels as standalone names.
  - **Repairing prose and self-auditing it.** Four consecutive rounds, fourteen false sentences.

- **Next action:** **CS-420, and NOT by hand.** Four rounds of prose repair have now each shipped a
  false sentence, several written by the commit correcting the previous one, and round four was caught
  only because an adversary read merged `main` after the items were closed and pushed. ADR 0008 states
  the rule and the artifacts exist to enforce it; what is missing is a MECHANICAL check that a
  declarative sentence in that module is backed by execution, plus a fix for the paragraph-citation gap
  that let a renamed heading go on being cited. Delete every sentence such a check cannot back. Then
  **CS-403, CS-209, CS-204** as ONE slice under the recorded `tools/precommit_gate.py` grant.

---

### Archived 2026-08-16 from `ROADMAP.md` - CS-420, CS-425 and CS-413 superseded detail

Second relocate pass of session 12, after four new items and two amendments pushed
`ROADMAP.md` back over its WARN budget. **Nothing here is current.** Each block was
superseded by a later dated block in its own entry, or by a closure elsewhere, before it
moved. Every item named below is still OPEN in `ROADMAP.md`, which remains its one owner.

**From CS-420 - the session-9 REOPENED block. F1, F2 and the dead paragraph citation were
all FIXED in session 10 and re-verified by an adversary that wrote none of the repair:**

> **REOPENED 2026-08-16 (session 9). THE ARTIFACTS ARE SOUND AND THE ORIGINAL FOUR
> SENTENCES ARE FIXED; THE REPAIR SHIPPED THREE NEW FALSE ONES.** A final adversary
> auditing merged `main` re-derived and CONFIRMED the derived test's structure, the
> two-copy common-mode claim, the bare-CI-box claim, the SystemExit residual and the
> repaired no-install gating - then refuted the prose. **F1: `IT NEVER RAISES` on
> `_sweep_decode_oracles` is FALSE** - a forced `KeyboardInterrupt` raises, and
> `_library_save_paths()` sits outside every `try` so a second site raises too; the same
> file states the opposite twice. CS-427 repaired this exact absolute in THREE sibling
> docstrings the same day and the fourth survived. **F2: the join mechanism sentence is
> false under both readings** - `ByteProperty -1` rots 5359 payloads while `join.tags`
> stays at exactly 55496 and `join.words` at exactly 13, because ByteProperty IS NOT ONE
> OF THE 13 JOINED WORDS; and thinning directly via `_MAX_TAGS_PER_PAYLOAD = 4` drops 3447
> tags with the word count unmoved. The causal account is wrong: the count measures whether
> the MUTATED WORD'S OWN TAGS still parse, not the thinning - MapProperty thins 0.12 per
> cent and costs two words, ByteProperty rots 4.1 per cent and costs none. **F3 is now
> CS-432's, sharpened there.** Also fix the DEAD PARAGRAPH CITATION this session created:
> `tests/save/test_oracle_citations.py` names the objects.py paragraph "beginning ``THAT
> JOIN IS NOT A CHECK ON THE TAG WIDTHS BELOW,``", which `662432d` renamed - the checker
> passes because it resolves `tests/<path>.py::<name>` citations and NOT paragraph names,
> which is a real gap in that checker.

**From CS-420 - the drifted sentence-count figures. These are archived as the RECORD OF A
DRIFT INCIDENT, not as numbers to reuse. Derive the ratio; do not read it here:**

> Sized - **AND THIS SENTENCE'S OWN NUMBERS DRIFTED, WHICH IS THE ITEM'S THESIS LANDING ON
> THE ITEM: it read "573 sentences ... 571 of 573" and BOTH FIGURES ARE WRONG.** Re-derived
> 2026-08-16 by the adjudicator and INDEPENDENTLY by the merger, using the fence module's
> own `sentence_count` against byte-identical files: `test_decode_oracles.py` holds 367
> sentences and `test_absolute_claims.py` holds 204, so the two fenced modules hold
> **571**, 2 carry a marker, and **569 of 571 are unread**. For THIS ITEM'S OWN SUBJECT,
> which is the single module named in its title, the figure is **366 of 367 unread**. A
> measured count restated in prose, drifted, inside the entry that exists to stop exactly
> that - CLAUDE.md section 4, live.

**From CS-420 - the acceptance-tension adjudication, settled and not to be reopened:**

> An adjudicator that wrote no part of ADR 0008 or of any implementing slice ruled that the
> two texts govern DIFFERENT AXES and that neither mentions the other's. ADR 0008 SCOPE
> governs BREADTH - which files the fence scans. This item's acceptance governs DEPTH -
> "every declarative sentence IN THE MODULE", singular, the one module named in this item's
> own title. **That module is ALREADY in `FENCED_MODULES`, so on breadth the two texts
> AGREE.** The apparent conflict was manufactured by the entry itself, which mixed the axes
> by sizing a TWO-module total against a ONE-module acceptance.

**From CS-425 - the session-8 measurement detail behind "the hook does nothing":**

> Three measurements, each executed. (1) **The hook cannot DENY.** Claude Code's
> `PreToolUse` protocol denies a tool call on exit code **2**; anything else is surfaced and
> non-blocking. The gate exits **1** on a violation. (2) **The hook probably cannot SEE the
> command.** Fed the JSON envelope a hook actually receives on stdin - `{"tool_name": ...,
> "tool_input": {"command": ...}}` - the gate returns **rc=0, PASS**, because JSON escapes a
> non-ASCII character to a `\uXXXX` sequence that is pure ASCII, so the charset scan finds
> nothing. It is named `--text-stdin` and expects raw text. (3) **END-TO-END PROOF, which is
> the only kind that counts here:** a PowerShell tool call carrying a literal em-dash RAN
> UNBLOCKED. Either of (1) or (2) alone is sufficient to cause that.

**From CS-422 - the session-8 amendment detail. The amendment's CONCLUSION stays in the
open entry; only the supporting detail moved:**

> `tests/save/test_decode_oracles.py::test_the_shipped_walker_reaches_a_terminator_on_every_real_payload`
> reads both, by asserting terminator-reach EQUALITY per pair, and goes red on both mutants
> - confirmed by an adjudicator and by an adversary independently.

**From CS-405 - the superseded revision of its own note, which the entry corrected:**

> A previous revision of this note said the walk was a SKELETON and `read_properties`
> decoded no property VALUE, so a slot count was unreadable. CS-413's decode half landed
> and that is no longer true. Its blocker was the object walk reaching a real building; the
> walk now reaches 131607 records across all 14 real saves.

**From CS-413 - the per-type evidence figures, which CS-421 OWNS. Archived because one
measured fact living in two open entries is the drift CLAUDE.md section 4 exists to stop:**

> of the 185382 values, 68659 are backed by a shipped redundancy - the value's own length
> prefix must equal the declared size - and 111364, or **60.1 per cent**, are backed by a
> declared width and nothing else, a check the module itself records as "defensive rather
> than measured". Byte order and signedness are checked by NOTHING EXECUTABLE: flipping
> `IntProperty` to big-endian turns 75136 real values into garbage and the only tests that
> go red are synthetic-fixture tests whose own fixture packs with the same byte order the
> reader unpacks with.

---

### Archived 2026-08-16 from `ROADMAP.md` - CS-400 and CS-413 superseded dated STATUS blocks

Relocated by the session-12 merger under the `tools/doc_budget.py` relocate guidance, with
`ROADMAP.md` at 98 per cent of its 60 KB budget. **Nothing here is current.** All of it was
superseded by a later dated STATUS block in the same entry before it was moved, and in one
case the entry's own text already said so. Both items remain OPEN in `ROADMAP.md`, which
is still their one owner file; these are the retired paragraphs, not the items.

**From CS-400 - the session-5 coverage STATUS, and the session-6 skeleton paragraph the
entry itself marked as no longer the state:**

> STATUS 2026-08-15 (session 5): clause 1's COVERAGE half is MET and clauses 2, 3 and 4
> remain MET, all gated by `tests/save/test_phase4_gate.py`. ALL FOUR real (header version,
> save version) pairs now parse and ALL 14 OF 14 real saves load end to end through
> `load_world` - verified by the merger against the live library rather than taken from a
> builder report: 14 found, 14 loaded, zero failures, zero warnings, 131607 records across
> 6171 levels, 3 distinct masked world tokens. It was 3 of 14 at the start of the session.
> **CS-400 STILL MUST NOT CLOSE, AND THE REASON HAS CHANGED FROM COVERAGE TO DEPTH.** What
> closed is a SKELETON grammar: measured by an adversary across all 8 save-52 bodies, 69.5
> to 77.7 per cent of every body is opaque property payload the grammar does not describe,
> and up to 81 per cent is skipped rather than described. `read_properties` resolved a
> record's class against the usmap and decoded NO property VALUE, so the reader reached
> every record and could read nothing INSIDE one. **THAT SENTENCE DESCRIBES SESSION 6 AND IS
> NO LONGER THE STATE - see CS-413's session-7 status.** The decode landed; what CS-413 and
> this gate now wait on is the EVIDENCE for it, not its existence. The stale REASON that
> used to sit here - "because the payload grammar has never been measured by this project" -
> was removed rather than corrected: it survived a session with its conclusion still true,
> which is precisely what makes a wrong reason read as current.

**From CS-413 - the session-6 STATUS, superseded by the session-7 STATUS that records the
decode landing, together with the correction record of the entry's own wrong unknown:**

> **THIS ENTRY FIRST SAID "UNLOCATED" AND THAT WAS WRONG - corrected 2026-08-15 by the
> slice that measured it, against the merger who wrote it.** The merger read the module
> docstring at `clockspeed/save/objects.py:114-120` ("`body_offset` and `body_length` are 0
> on every path today") and did not read the implementation 1500 lines below it, where
> `objects.py:1666-1672` says the extents "are located by the walk below" and the seam stays
> 0 because "the k-th payload belongs to the k-th record is an ASSUMPTION nothing has
> measured" - a deliberate refusal to ship a plausible pairing, not a missing walk. **The
> real unknown was ALIGNMENT.** This is the project's own recurring failure class landing on
> the merger: a docstring trusted over the code, and an inherited note naming the WRONG
> UNKNOWN, which is exactly what session 5 recorded about two of its three resume notes. The
> lesson generalises past this item - a summary at the top of a 2000-line module is a claim
> about the module, not a reading of it.

> **STATUS 2026-08-15 (session 6): the ATTRIBUTION half is MET and the DECODING half is
> not, so this stays OPEN and so does CS-400.** `body_offset` and `body_length` now locate a
> real payload on all four pairs and 131607 of 131607 records, and the data section walks
> byte-exact. The pairing was proven by FOUR independent oracles: the component reference
> list against the component `parent` field, read from different sections by different cursor
> passes, 9838 of 9838 at shift 0 and 0 at shifts -2, -1, +1, +2 and two within-level
> rotations; a **random within-level permutation holding the extent multiset and the tiling
> fixed and varying only the assignment - 0 of 29170 moved payloads match and 61 of 61
> permutation fixed points do**, which is what rules out agreement-by-construction
> empirically rather than by argument; `type_path` against property tag names, monotone on
> all three tagged pairs; and bidirectional set equality over all 103742 actors, where two
> failure categories are empty at the shipped alignment and populated at rotate-1.

## Session 1 - 2026-08-13 - phase 0 scaffold, then phase 1 spikes

- **Shipped:** CS-001 phase 0 scaffold, CS-002 tier-0 gate proven end to end, CS-003 S8,
  CS-004 S4, CS-005 S6, CS-006 ground-truth re-probe, CS-104 S5 body framing. S1, S2, S3
  and S7 also settled - report at `docs/_archive/spike-report-s1-s2-s3-s7.md`, so CS-101,
  CS-102, CS-103 and CS-105 are answered but their implementation work is still open.

- **In flight:** nothing blocking. Phase 2 has NOT been started, deliberately - the
  operator's instruction was to stop after phase 1 and report. No remote is configured, so
  nothing has been pushed; that is an operator decision, not an oversight.

- **Decisions:** ADR 0002 (S8, node data is not seed-dependent), ADR 0003 (S4, save carries
  node geometry but not node semantics), ADR 0004 (S6, unlock state is recoverable).

- **Surprises**, all four written back into the spec:
  1. `py -3` resolves to a DIFFERENT 3.14.4 install than `python`, with no pytest, ruff or
     mypy. Both report the same version, so a version check passes while the gate's lint
     step degrades and pre-push cannot run. Recorded as `BOOTSTRAP.md` section 2.5; hooks
     and `.claude/settings.json` now resolve `python` first and `py -3` last.
  2. S4 half-refuted: the save carries node transforms but NO purity or resource type, so
     `BOOTSTRAP.md` section 8.3 step 1 was wrong to call that "done". Section 8.3 corrected.
  3. S7 half-refuted: the overclock exponent IS in the data but is NOT fixed - two distinct
     values across 62 buildings. The overclock ceiling is absent from the docs entirely.
  4. Locale count is 55 not 57; the save library holds three worlds not one; header version
     is not stable at 14 (it is 10 on the oldest saves).

- **Failed paths - do not retry:**
  - Grouping saves by FILENAME to identify worlds. It inflated 3 worlds into 6 and would
    have produced a false S8 result. Group by the header world token, always.
  - A single fixed actor-header layout for the save parser. The transform offset is +8 on
    save versions 52 and 60 and +4 on version 36. Version-dispatch from day one.
  - Trial-decode encoding sniffing for the docs file. Python's `utf-16` codec decodes the
    UTF-8 `io.json` without raising and returns mojibake. Only the BOM-byte test is valid.
  - Using `AKIAIOSFODNN7EXAMPLE` as a secret-scanner test case. It is AWS's own documented
    example key and the placeholder allowlist correctly ignores it. A real-looking literal
    is blocked properly.

- **Next action:** operator ratifies the LICENSE copyright holder (currently the git author
  name), then decide the BOOTSTRAP.md PII question in `docs/GATED.md` before any public
  flip. After that, phase 2 (CS-200) begins with the docs extractor, written against the
  measured schema in `BOOTSTRAP.md` section 3.2 - NOT against the assumed one.

## Session 2 - 2026-08-14 - three operator decisions, then phase 2 data layer

- **Shipped:** CS-007 (LICENSE holder ratified), CS-100, CS-101, CS-102, CS-103 (phase 1
  implementation work), CS-200 (phase 2 gate, all three acceptance criteria met and verified
  independently). Detail in `docs/LEDGER.md`.

- **In flight:** nothing half-done. Working tree is committed. **No remote exists yet** - the
  operator chose a private GitHub repo named `Clockspeed` receiving a SQUASHED orphan commit
  from the clean tree, NOT the existing history. That push had not been performed when this
  note was written; check `git remote -v` before assuming.

- **Decisions:**
  - ADR 0005, `accepted` - the overclock ceiling is NOT in `Headers.zip`, and the mechanism
    says it never will be: every relevant property is `EditDefaultsOnly`, so the value lives
    in a data asset, and the zip ships headers with no `.cpp`. It IS a schema oracle. The
    probe recovered the equation and the field name `mExtraPotential` (0.5, in the docs data
    all along), reducing the unknown to one integer, `mDefaultPotentialShardSlots`.
  - Operator decision recorded in `docs/GATED.md` CS-G03: the public flip ships from a FRESH
    history, with three preconditions - PII, author identity, and no agent co-authorship
    trailer.

- **Surprises**, all written back into the spec:
  1. **The spike report was wrong about a SIDE.** It said the fractional-fluid recipe "takes"
     water at 1500. Live re-probe: the water is a PRODUCT. Counts were right, side was wrong.
     `BOOTSTRAP.md` section 3.2 corrected and made authoritative; the report carries a
     correction block. This mattered - a fixture written from the original wording tests
     ingredient rounding only and never touches the product side.
  2. **The registry shipped a wrong number before adversarial review caught it.** Three
     biofuel recipes published litres where the contract said cubic metres, because a
     four-group descriptor whitelist missed `FGItemDescriptorBiomass`. Fixed by deriving the
     namespace from field presence instead of a name list.
  3. **`redact()` had a latent PII leak** that predated this session - it stripped home
     prefixes but not the account-id path segment. Fixing it revealed the fix itself was
     scoped to the 17-digit Steam shape only.
  4. **Two misspelled game keys confirmed live** and used verbatim.

- **Failed paths - do not retry:**
  - **Skipping worktree isolation because write-lists were proven disjoint.** The proof
    bounds DECLARED writes and says nothing about transient ones. Two builders broke files
    outside their lists to watch a test go red - correct TDD, restored correctly - and turned
    an unrelated suite red mid-verification. If a shared tree is used again, the dispatch
    must say every break-revert-observe cycle happens on a scratchpad COPY.
  - **`git ls-files | xargs grep` as evidence that a scrub is complete.** It reads
    WORKING-TREE contents, so it goes clean the instant you edit and proves nothing about
    what git stores. Use `git grep <pattern> HEAD` or `git log -S`.
  - **Trusting per-file `ruff`/`mypy` green.** CI runs them repo-wide; per-file green is a
    weaker and different claim, and it produced a false green this session.
  - **A redactor used as its own test oracle.** `redact(x) != x` as the test for "x holds
    PII" is blind exactly where the redactor is blind.

- **Next action:** create the private GitHub repo `Clockspeed`, push a squashed orphan commit
  from the clean tree, and confirm the tier-1 CI run status on it - CI has never executed
  against a hosted branch, so the `--no-verify` mitigation is still unproven.

## Session 3 - 2026-08-14 - phase 2 follow-ups, then the phase 3 solver core

- **Shipped:** CS-105, CS-201, CS-202, CS-203 and **CS-300, the phase 3 gate**, all four
  waves. `solve/{exact,ratio,power,optimize}.py`, `solve/backends/`, the C1-C9 corpus, the
  registry seam plus ADR 0006, and the mypy ratchet. Detail in `docs/LEDGER.md`.

- **In flight:** nothing half-done; the working tree is committed and pushed. Phase 3 is
  CLOSED and phase 4 (CS-400, the save reader) is next and unblocked. Two phase-3 follow-ups
  were filed rather than absorbed: CS-301 (the variable-power law is unmeasured, so
  `power.py` refuses to model it, and two branches have no fixture to exercise them) and
  CS-302 (`ratio.py`'s refusal-path diagnosis is O(rows) extra solves and was never measured
  at real-registry scale). Five phase-2 follow-ups are also open, CS-204 to CS-208, all
  found by this session's own process rather than inherited.

- **Decisions:** ADR 0006, status `proposed`, needs an adjudicator to flip it. It records
  how the un-sharded clock base enters the model, which ADR 0005 specified but could not
  implement. It supersedes nothing and ADR 0005 is unedited.

- **Surprises**, each measured rather than reasoned about:
  1. **`strict = true` does not work in a mypy per-module override.** It is accepted with no
     complaint and applied GLOBALLY - the `clockspeed.solve.*` rung alone produced 25 errors
     in `tests/data/test_blobs.py`, a file its pattern cannot match. Written out as its
     twelve scoped constituents instead. Acceptance of a key is not evidence of scoping.
  2. **`Fraction ** Fraction` returns a FLOAT** for a non-integer exponent, and the defect is
     DATA-DEPENDENT: the same operator with `Fraction(2,1)` returns a Fraction, so a test
     written with a whole-number exponent passes while the shipped 1.321929 degrades
     silently. `**` is banned outright in `solve/`.
  3. **ADR 0005 contradicted the shipped registry** and a test enforced the contradiction.
     Resolved in data by S0-REG; see ADR 0006.
  4. **The planner's C5 chain shared C3's product**, which gave that item a second producer
     and destroyed C3's uniqueness - a rival plan satisfies every balance at 30 MW against
     C3's 436/3 MW, so a minimizing solver would have returned it and C3's hand-verified
     answer would have been wrong. Caught by the fixture slice, fenced with two tests.
  5. **A shape-only world-token detector is not viable.** Measured over all 99 tracked files:
     a naive 22-char regex matches 2082 times, and even at its tightest still matches 5 game
     class names. CS-201 detection is value-based as a result.
  6. **`.claude/worktrees/` was untracked but UNIGNORED** - one `git add -A` would have
     committed a duplicate tree - and it inflated local `ruff format` from 38 files to 187,
     reporting a builder's scratch copy as a main-tree failure. Now gitignored.

- **Failed paths - do not retry:**
  - **`git reset --hard` to undo a probe commit.** It discarded every tracked modification in
    the working tree in one step, including four merged slices. Recovered in full because the
    agent worktrees still held the builder output and the new files were untracked, but it
    cost a full recovery cycle. Use `git reset --soft HEAD~1`. A trailing `--` does NOT make
    `--hard` respect a pathspec; it is accepted as a whole-tree reset.
  - **Slicing `pyproject.toml` at the first literal `[[tool.mypy.overrides]]`.** That string
    appears in a COMMENT above the real blocks, so every generated test config was truncated
    mid-comment and silently set the option globally. Six bisect results were measuring the
    broken fixture rather than the thing under test.
  - **Trusting a builder's baseline count.** Worktrees are cut from HEAD, so a builder that
    started before a merge reports a baseline that is real for it and wrong for the tree.
    Two builders reported honestly that their dependencies were absent; re-run post-merge.
  - **Auditing a fence with a cruder check than the fence itself.** A first pass at the
    ADR-0006 audit walked ALL string constants including docstrings and reported four false
    failures, because the operand names legitimately appear in explanatory prose.

  7. **Flipping the mypy gate to blocking immediately caught a PRE-EXISTING CI failure that
     `continue-on-error` had been hiding.** mypy analyses for the platform it is RUNNING on,
     so `if sys.platform != "win32": return` makes the rest of the function unreachable on
     Linux and not on Windows - three `unreachable` errors in `clockspeed/data/locate.py`
     off identical source, green locally and red on the runner. The previous CI run reports
     `success` only because the failed step was allowed to pass the job. Fixed by pinning
     `platform = "win32"` in the mypy config so the config means the same thing everywhere;
     the cost, three unchecked non-Windows early returns, is stated in `pyproject.toml`
     rather than hidden. **A green local gate is not evidence about CI when the tool's
     behaviour depends on the host.**
  8. **A merger instruction was refuted by the agent executing it, and the refutation was
     right.** The wave-4 dispatch required that no solve module pull in
     `clockspeed.data.docs_extract`. That is unsatisfiable - `registry.py:206` and
     `version.py` import it at module level and `tests/data/test_phase2_gate.py:775-781`
     REQUIRES those edges - and `docs/ARCHITECTURE.md:136-138` scopes the raw-docs
     prohibition to `advisor/`, not to `solve/`, whose clause is "never reads a save".
     Writing it as dispatched would have made the phase red against correct code.

- **Next action:** get ADR 0006 adjudicated from `proposed` to `accepted` by an agent that
  did not write it - it is the only unadjudicated artifact from this session - then begin
  phase 4 (CS-400, the save reader). Phase 4 is unblocked and is where the two oldest
  deferred questions land: whether `mInventoryPotential` serialization carries the overclock
  slot count (ADR 0005's one remaining unknown, which would let `power.py` publish a real
  ceiling), and the world-token half of CS-201, which cannot work until a header parser
  exists. Note BOOTSTRAP.md section 3.1: the actor header layout is save-version dependent,
  +8 on save versions 52 and 60 and +4 on version 36, so version-dispatch from day one.

## Session 4 - 2026-08-14 - ADR 0006 adjudicated, four tier-1 fixes, phase 4 waves 0 and 1

- **Shipped:** ADR 0006 flipped to `accepted`; **CS-204**, **CS-206**, **CS-207** closed;
  **CS-208 DENIED** and replaced by CS-209; **ADR 0007** written and accepted; and
  **phase 4 waves 0 and 1** - the version-qualified spec, the synthetic save corpus, and
  `clockspeed/save/{header,chunks,usmap,workdir}.py`. Suite 734 -> 1067, exit 0. Detail in
  `docs/LEDGER.md`.

- **Also shipped, after the first `/done` ran:** CS-205, CS-404 part 1, and phase 4 waves 2
  and 3 in full - `objects.py`, `world.py`, the phase-4 acceptance gate, CS-407 and CS-409.
  Suite 734 -> **1462 passed, 5 skipped**, exit 0. CI green on `f3f26ba`.

- **A REAL WORLD PARSES.** Verified by the merger against the live library, not taken from a
  builder report: 3 of 14 real saves load end to end through `load_world` into a `WorldModel`
  - 25769, 25769 and 25725 records, 202 levels, 2774 nodes - and the other 11 are refused
  with a clean `WorldLoadError`. All three render the SAME masked token digest with DIFFERENT
  record counts, which is CS-401's token-stability claim confirmed on the game's own output.

- **In flight:** nothing half-done; the tree is committed and pushed. **CS-400 IS STILL NOT
  CLOSED, and the gate itself says so.** Clauses 2, 3 and 4 are MET and gated. Clause 1 is met
  for ONE of four version pairs only - three of the four real pairs cannot be read at all
  (CS-407), and CS-402 is separately unmet because save version 42's transform delta is
  unmeasured (CS-408). The open follow-ups are CS-406, CS-407, CS-408 and the remaining parts
  of CS-404.

- **Decisions:** ADR 0007, `accepted` - the save header layout and the chunk framing are
  version dependent. Its adjudication returned NEEDS-REVISION and four defects were fixed
  before the flip. Operator ruled that an INCONCLUSIVE `mInventoryPotential` result is an
  acceptable outcome, filed as CS-405 rather than converted into an answer.

- **Surprises**, every one measured rather than reasoned about:
  1. **The chunk framing in `BOOTSTRAP.md` was TRUE ONLY FOR HEADER VERSIONS 13 AND 14.** On
     header 10 the marker is `0x00000000` and there is NO compression-algorithm byte at all,
     with zlib at magic+48 rather than +49. A walker built from the unqualified fact fails on
     3 of 14 saves and looks correct on the other 11. The session prompt called this settled;
     the probe won. Section 3.1 corrected, ADR 0007 records it.
  2. **The header string ORDER is header-version dependent, and that is a PII mechanism.**
     Header 14 carries four leading strings, headers 10 and 13 carry three. So on 10 and 13
     the THIRD string is the operator's world name and on 14 it is the options string - a
     redactor targeting a NAMED FIELD is defeated by a version-dependent field ORDER. A
     planner probe demonstrated it by leaking one world name into its own agent transcript.
     `header.py` therefore makes the PII strings ABSENT from the returned type, not redacted.
  3. **`docs/adr/0003` is `accepted` and states the refuted framing verbatim**, so the stale
     claim held the HIGHER status and a reader searching for "chunk framing" hits it first.
     Found by the ADR 0007 adjudicator. Corrected by pointer in both directions, since
     neither an accepted ADR nor an append-only ledger entry may be edited.
  4. **CS-208 was REFUTED BY MEASUREMENT, not deferred.** 16 matchable world names exist here
     and the shortest is 4 characters, so any floor at or above 5 drops exactly one REAL name
     and it then commits. The false positive it feared does not exist - the gate over every
     tracked file exits 0. And a floor of 4, 5, 6 or 8 turns ZERO of the 65 gate tests red,
     which proves the suite is BLIND to the change rather than that the change is safe.
  5. **The int8 after the datetime ticks is not "session visibility".** It reads `0x00` on
     header 10, 13 and 14/60 and one of `0x10/0x50/0x90/0xD0` on the eight header-14/save-52
     saves. Position is anchored (the int32 after it reads 40 on all 14); meaning is not.
  6. **The synthetic corpus diverges from real bytes on the header-10 body prefix**, and a
     builder reported the FIXTURE value as a measurement. Real header 10 opens with an int32
     equal to body length minus 4. Filed as CS-404 before it could reach wave 2.
  7. **The size block is `(c, u, c, u)`, measured** - W1-CHK named the alternative as the one
     thing that could make its module wrong on every real save while every synthetic test
     passed. It had guessed right, but it was a guess until the merger measured it.
  8. **`os.open(p, os.O_WRONLY)` is invisible to a text-level write scan.** The static
     single-writer check returns empty for it, so the phase-4 AST gate must cover `os.open`
     and the runtime audit hook is what catches flag-based writes.

- **Failed paths - do not retry:**
  - **Trusting a builder's measurement of a FIXTURE as a measurement of the FORMAT.** Two
    separate builders did this, on the body prefix and nearly on the size order. The fix is
    not more review - it is that any claim about the byte format gets re-measured against a
    real save before anything is built on it.
  - **A shape-based check for a leaked token or world name.** A 22-character base64url regex
    matches `Build_SyntheticSmelter`, and a 3-character-run check against a whole `repr`
    matches the FIELD NAME `world_token=`. Both produced false positives for the merger this
    session. Scope the check to the value, never to the rendering.
  - **`grep -P` as a PII scan on this machine.** It errors with "supports only unibyte and
    UTF-8 locales", and a `||` fallback then prints a clean result for a grep that never ran.
    W0-DOC caught its own false pass and wrote a real scanner instead.

- **Two more surprises, both after the first `/done`:**
  9. **A real save body is a LIST OF LEVELS, not an object table.** Nothing downstream could
     ever have parsed a real world by fixing an offset - the shape was wrong, not the number.
     Header 10 / save 36 is now derived and confirmed on all three real files of that pair,
     each landing on its exact final byte. The other three pairs are refused eagerly.
  10. **pytest renders the ARGUMENTS of every frame in a failing traceback**, with no
     `--showlocals` and no opt-in. Measured with a planted marker: it appeared twice. So a
     test passing real save bytes into a frame that can raise prints the HEAD of the file,
     which is exactly the PII-bearing header. Three live sites found and guarded. This class
     is invisible to every green run BY CONSTRUCTION, because it only fires on failure.

- **Also failed and worth not retrying:** interpolating save version 42's transform delta.
  TWO separate builders reached a plausible number and BOTH discarded it - one because its
  method failed to recover the known deltas for 36 and 60 when validated against them, the
  other because the reading needed two unmeasured assumptions propping each other up. With 36
  giving 4 and 52 giving 8, the value 4 is exactly what "looks derived" produces.

- **Closing note, after the second `/done`:** the phase-4 gate's clause-1 test went from
  SKIPPED to PASSING. Lifting that skip surfaced a trap worth remembering - the gate author
  wrote "delete the skip marker and this becomes a real assertion with no other edit", and
  that would have FAILED, because the test used `latest_save()` and the newest save here is
  an UNMEASURED pair the reader refuses by design. A correct refusal would have read as a
  defect. It now selects the newest save of a MEASURED pair. Suite closed at 1463 passed,
  4 skipped, exit 0.

- **Next action:** **CS-407** - derive the body layout for the remaining three version pairs.
  Header 14 / save 52 is the nearest: all 134 named levels walk and the persistent level's
  FIRST COMPONENT record is the single blocker. Each unfinished pair has its stopping point
  recorded in `LEVELLED_LAYOUT_UNMEASURED` so a slice resumes from evidence rather than from
  scratch.

<!-- Relocated from WAKEUP_NOTES.md by the session 8 /done ritual, 2026-08-15. -->
## Session 5 - 2026-08-15 - CS-407 closes for all four pairs; the save reader reads the whole library

- **Shipped:** **CS-406**, **CS-407**, **CS-408** and **CS-402**. New items filed: CS-411
  (repo-wide mypy does not cover `scripts/`) and CS-412 (record the remaining opaque spans as
  data, not prose). Suite 1463 -> **1490 passed, 4 skipped**, exit 0. Detail in
  `docs/LEDGER.md`.

- **ALL 14 OF 14 REAL SAVES NOW LOAD END TO END.** It was 3 of 14. Verified by the merger
  against the live library, not taken from a builder report: 14 found, 14 loaded, zero
  failures, zero warnings, 131607 records across 6171 levels, 3 distinct masked world tokens -
  which independently confirms the recorded fact that this library holds exactly three worlds.

- **In flight:** nothing half-done; the tree is committed and pushed. **CS-400 STILL MUST NOT
  CLOSE, and the reason CHANGED from coverage to DEPTH.** Coverage is now complete; what
  closed is a SKELETON grammar. 69.5 to 77.7 per cent of every body is opaque property payload
  and `read_properties` decodes NO property value, so the reader reaches every record and can
  read nothing inside one. Pillar 3 needs inventory, clock speed and connection state, and all
  three live in the payload. **Whether "a real world parses" is satisfied by a skeleton walk
  is an OPERATOR DECISION and was deliberately not taken by the merger.**

- **Decisions:** no ADR this session. A frozen-file GRANT for `scripts/install_hooks.py` was
  adjudicated and recorded in `docs/LEDGER.md` BEFORE the edit, per CLAUDE.md section 6.

- **Surprises**, each measured rather than reasoned about:
  1. **The inherited resume notes named the WRONG UNKNOWN on two of three pairs.** Save 42's
     note blamed the transform delta; the delta was never wrong, its LEVEL GRAMMAR differed.
     Save 60's note described a fixed 78-byte separator; it is a variable-width counted
     structure taking three widths. Every prior attempt swept the parameter it had been told
     was unknown while holding the wrong thing fixed.
  2. **ALL THREE ADVERSARIES RETURNED REFUTED - AS WRITTEN, NOT IN SUBSTANCE.** No rival broke
     a byte landing or a skeleton. They killed over-claiming, and the shipped grammar is
     narrower and better than the measured one.
  3. **One narrowing was a REGRESSION AGAINST A SHIPPED ADR, caught just in time.** Actor
     pre-runs of 0, 4, 8 and 12 bytes ALL land 8 of 8 on save 52 - byte arithmetic is blind
     even to that run's width. `objects.py` already modelled it correctly as one opaque span
     per ADR 0003. Splitting it into named fields would have been a step backwards.
  4. **A recorded reason was refuted by RUNNING it.** `objects.py` said delta 4 was declined
     because it held only if save 42's declared header size also excluded the collectable
     count. That grammar stops inside level 0. One thing changed, not two.
  5. **A test was GREEN WHILE FALSE.** The corpus still named save 42 as its unmeasured save
     version, so a refusal test kept passing while its own example had stopped being true.
     Green because the corpus table was incomplete, not because the claim held.
  6. **`ROADMAP.md` claimed both CS-406 leak sites were on the sweep's live residual list.**
     Measured FALSE for the wiring line by running `scan_repo()` directly - it appears in
     neither list and was guarded by nothing at all.
  7. **`redact()` is a NO-OP on the pinned project root.** It maps `C:\Clockspeed` to itself,
     because that root is not under a home directory while the test oracle still matches it.
     A redaction-based CS-406 fix would have passed on a clone under a home directory and
     silently failed on this machine.
  8. **The stale-worktree problem RECURRED and the mandated check caught it.** The CS-407
     integration builder's worktree was cut from its base's parent; it reported ANCESTOR-FAIL,
     fast-forwarded, and re-measured before building.
  9. **18 of 28 commits carry an agent co-authorship trailer** although `docs/GATED.md` CS-G03
     records an operator decision against it. Operator reaffirmed on 2026-08-15: keep
     committing without it. The existing history is not worth rewriting - CS-G03 already
     generates a fresh history at the flip, which strips them.
  10. **THE PATH-LEAK ORACLE WAS INERT ON POSIX, and CI is what proved it.** `ABSOLUTE_PATH`
     in `tests/test_exception_rendering.py` was a DRIVE-LETTER regex, so on the Linux runner
     it could not match an absolute path at all - every `not ABSOLUTE_PATH.search(...)`
     assertion in that module had been passing VACUOUSLY on every CI run since it was
     written. **The thing that caught it was the NON-VACUITY assertion added by CS-406** -
     "the sandbox root really is a path the oracle WOULD match" - which went red on CI while
     every sibling assertion stayed green. That is exactly the job it exists to do. CI went
     RED on `a0da3b7` with a green local suite and GREEN on `1ad0db8` after the widening.
     `docs/LEDGER.md` had already recorded this residual under CS-205 - "POSIX behaviour
     unobserved, settled only by a Linux runner" - and the runner settled it.
     Known and deliberately NOT fixed: the Windows branch also matches the `s:/` inside
     `https:/`, so it over-fires on a URL. That is pre-existing and fail-closed, and
     tightening it can only make a `not search` assertion pass MORE easily, which is the
     direction that hides a leak.

- **Failed paths - do not retry:**
  - **The tag-driven collectable rule.** "Present iff the level's data entries are tagged 42"
    is UNDEFINED on 229 of 2244 levels of the very file it came from, and both outcomes occur
    among them. Use the SIZE-DRIVEN rule - and know that it is an a-priori delimiter argument
    rather than a measurement, because "always read a block" also lands byte-exact on 7 of 8
    save-52 files.
  - **Reading an 8-byte section size as an int64.** Undecidable now and permanently. An int64
    reader silently computes an astronomical size if that word ever goes non-zero, then
    misdiagnoses the WRONG FIELD.
  - **Claiming a breakdown inside a constant blob.** Save 60's 70-byte run has no observable
    boundary at all - not 4+6, not 8+2, not 16+10.
  - **Reading "8 real files" as an independence count.** The save-52 preamble is byte-identical
    across all 8 and is the static world-partition grid, so n=1 is a CEILING, not a sampling
    accident more saves would fix.

- **A measurement that leaves no artifact is not resumable.** The prior session's note said the
  (13,42) grid preamble "is measured"; that measurement was recorded NOWHERE in the tree, so
  the resuming slice re-derived it from scratch. Filed as CS-412. Record the GRAMMAR, never an
  adjective about it.

- **Next action:** get an operator ruling on **CS-400** - coverage is met and depth is not, and
  the merger deliberately did not take that decision. If CS-400 stays open, the natural
  successor to CS-407 is measuring the OBJECT PAYLOAD GRAMMAR, which is the three quarters of
  every body still opaque and the thing pillar 3 needs. **CS-405 is now UNBLOCKED** but note it
  may need the payload grammar first, and saying so is the correct outcome rather than forcing
  a YES or NO.

## Session 6 - 2026-08-15 - the operator rules CS-400 depth-bound; payload extents get attributed

- **Shipped:** **CS-411** and **CS-404** closed. **CS-413** filed and half-landed - attribution
  yes, decoding no. New items filed: CS-414, CS-415, CS-416, CS-417, CS-418. Suite 1490 ->
  **1551 passed, 4 skipped**, exit 0. Detail in `docs/LEDGER.md`.

- **THE OPERATOR RULED ON CS-400 AND IT STAYS OPEN ON DEPTH.** A skeleton walk does NOT satisfy
  "a real world parses". Two mechanical consequences, both recorded rather than implied: the
  payload grammar became **CS-413**, its own item and the phase-4 depth gate, and **phase 5
  does not open until a record's properties can be READ**, restated in CS-500's own entry so a
  reader arriving there does not have to find it in CS-400.

- **In flight:** nothing half-done; the tree is committed and pushed. CS-413 is the live thread.

- **Decisions:** no ADR. No frozen file was touched and no frozen-file grant was needed - the
  one believed necessary turned out not to be, see surprise 3.

- **Surprises**, each measured rather than reasoned about:
  1. **THE MERGER'S OWN FRAMING WAS WRONG AND THE BUILDER REFUTED IT.** The dispatch and the
     CS-413 roadmap entry both said the object data section was UNLOCATED. It was not:
     `objects.py:1666-1672` says the extents "are located by the walk below" and the seam
     stayed 0 because the k-th-payload-to-k-th-record pairing "is an ASSUMPTION nothing has
     measured" - a deliberate refusal to ship a plausible guess. **The real unknown was
     ALIGNMENT.** Cause: reading a summary at the top of a 2000-line module and not the
     implementation 1500 lines below it. Same class as session 5's inherited notes naming the
     wrong unknown; this time it was generated in-session, by the merger, in under an hour.
     Corrected in `e70598b`.
  2. **THE PERMUTATION CONTROL IS THE ONE THAT SETTLES ALIGNMENT.** Shifts of +/-1 and +/-2 all
     give 0, but so would a broken harness. A random WITHIN-LEVEL permutation holding the
     extent multiset and the tiling fixed and varying only the assignment gives **0 of 29170
     moved payloads matching and 61 of 61 permutation fixed points matching.** Agreement
     guaranteed by construction cannot survive that. The builder did not run it; the adversary
     did, and said plainly it was the control the builder should have run.
  3. **A FROZEN-FILE BLOCKER DISSOLVED IN CONFIG.** `tools/` was believed to need a grant for
     `tools/precommit_gate.py`. A scoped override for `ruff` and `yaml` removes the error with
     no edit to that file - **and the scoping was PROVEN, not assumed**: mypy reports the block
     as an unused section when it does not match, the opposite of `strict = true`, which is
     accepted silently and applied globally. The merger was one step from filing a grant item
     that was never needed.
  4. **AN EXCLUSION THAT BUYS NOTHING.** mypy's `exclude` governs DISCOVERY, not the import
     graph. `tools/drift_guard.py:312` and `tools/facts_probe.py:121` both `import verify_env`
     - an import that resolves only BECAUSE CS-411 made `scripts/` a source base dir. Measured:
     adding `tools/` gives 9 errors with the exclusion and 9 without. Filed as CS-414.
  5. **A MUTANT CONTRADICTING THE SHIPPED FILE IN 3113 PLACES PASSED ALL 1519 TESTS.** Writing
     the usmap type-26 name index before its inner descriptor lands on the IDENTICAL byte -
     the landing oracle is structurally blind to it - and the loader tolerates it because a
     small synthetic index leaves a valid payload-free type in the low byte. Killed only by
     comparing builder output against real shipped bytes. **This is the phase's stated
     common-mode risk arriving in person.**
  6. **A DOCSTRING NAMED THE CORRECT MECHANISM AND THEN CLAIMED A MITIGATION THAT MECHANISM
     DEFEATS.** `_usmap_index` said keeping a name out of the exception MESSAGE kept it out of
     the log. pytest renders frame ARGUMENTS and the name is an argument; it printed twice.
     Worse than silence under non-negotiable 12, because it teaches a pattern that fails on a
     frame carrying real save bytes.
  7. **A WRONG NUMBER WITH A TRUE CLAIM ATTACHED.** CS-413's first revision put "all 6173
     levels" into two SHIPPED docstrings. It is 6171 - three instrumentations and the per-pair
     sum 606+2244+2945+376 agree, and the repo already recorded 6171 in three places. The
     attached claim was true, which is exactly what would have made it read as verified
     forever. Deleted rather than corrected: "every level of every real save agrees" says
     everything the count said and cannot rot.
  8. **TWO TESTS COULD NOT FAIL FOR THE DEFECT THEY GUARDED**, including one whose own docstring
     called it "THE HONESTY CONTROL". Both passed with the implementation deleted AND with the
     alignment rotated. The fix needed EQUALITY, not `> 0`: measured, a `> 0` control still
     passes rotate-1 at 77257.
  9. **CI PROVES ALMOST NONE OF CS-413.** Simulated on a save-less box: all four
     `tests/save/test_properties.py` tests skip and 2 of 5 new `test_objects.py` tests skip.
     CI verifies seam arithmetic on the synthetic fixture; the alignment, the tag grammar and
     the zero-zero-length-payload result are this-machine-only.
  10. **AN ITEM CLOSED INCIDENTALLY BY A NEIGHBOURING COMMIT STAYED OPEN ON THE BOARD.**
     CS-404 part 3 landed in `44740e0` under CS-407 and nothing announced it, so it sat open
     and would have cost a slice. Found by the merger before dispatch.

- **Failed paths - do not retry:**
  - **A round trip through our own loader as proof a fixture matches the GAME.** It cannot
    distinguish "matches the game" from "matches our reader" - surprise 5 is the proof. Compare
    against shipped bytes.
  - **The usmap landing oracle as a discriminator for field ORDER.** Swapping `(slot,
    array_size)` lands byte-identically; it is settled ONLY by value distribution. Recording a
    width as "measured by landing" is wrong for that pair.
  - **A `> 0` liveness control on a real-library sweep.** Passes under a rotated alignment.
  - **Reading a module docstring as a statement of what the module does.** Surprise 1.

- **Next action:** decide whether to continue **CS-413**'s decode half or take the four cheap
  tier-1 items now filed. If continuing CS-413, the two open fronts are separate problems: the
  variable trailing run after the terminator is a GRAMMAR question that more saves will NOT
  fix and that needs per-type value decoding, and save 60 is the opposite - genuinely
  under-sampled at 2 byte-identical files, reaching a terminator on 0 of 1832 at every
  alignment tried.

## Session 7 - 2026-08-15 - the CS-413 decode lands and does NOT close; adversaries change the outcome twice

- **Shipped:** **CS-414, CS-415, CS-416, CS-417, CS-418** closed. **CS-413's decode half
  LANDED and the item STAYS OPEN.** Filed: CS-419, CS-420, CS-421, CS-422, CS-423, CS-424,
  plus **CS-G05** gated. Suite 1551 -> **1603 passed, 7 skipped**, exit 0. Five commits,
  `7cbcbac..5d11dc2`. Detail in `docs/LEDGER.md`.

- **THE DECODE WORKS AND THAT IS NOT ENOUGH TO CLOSE CS-413.** `read_properties` returns
  185382 real values, 11 measured types, every unmeasured type flagged, and a synthetic
  fixture means the decoder is covered with no game installed. It stays open on EVIDENCE -
  the merger's ruling, confirmed by an adjudicator that produced none of the work. Two
  measured reasons: the acceptance clause is a LIVENESS FLOOR that a zero-value-byte decoder
  clears, because a BoolProperty's value rides in the tag with `size` 0; and **111364 of
  185382 values, 60.1 per cent, are backed by a declared width and nothing else** - a check
  the module itself calls "defensive rather than measured". Byte order is checked by NOTHING
  EXECUTABLE: flipping IntProperty to big-endian ruins 75136 real values and only
  synthetic-fixture tests go red.

- **In flight:** nothing half-done. Tree committed and pushed, working tree clean.

- **Decisions:** no ADR. No frozen file touched and NO GRANT NEEDED - `tools/precommit_gate.py`
  came INSIDE the mypy gate with no edit to it, via a scoped override, verified byte-identical
  to its pre-session state by an adjudicator rather than asserted.

- **Surprises**, each measured rather than reasoned about:
  1. **THE ADVERSARIAL PASS CHANGED THE OUTCOME TWICE.** Without it this session commits a
     privacy leak that renders decoded world content in pytest frame arguments, AND closes
     CS-413 on evidence that does not support it. Both were invisible to a green 1572-test
     suite. The pass cost roughly what the building did.
  2. **THE USMAP GATE IN `read_properties` WAS A DEAD END, NOT CAUTION.** The shipped mapping
     holds ZERO `Build_` schemas of 13792, so every building record resolves to nothing
     PERMANENTLY, and buildings are exactly what pillar 3 needs. The payload is TAGGED
     serialization and carries its own names and type words. `docs/ARCHITECTURE.md` said
     objects.py deserializes "against the property mapping" - corrected; the mapping is an
     oracle and a class-name resolver, never the decode input.
  3. **TWO BUILDERS INDEPENDENTLY SHIPPED A TEST THAT MEASURED THE WRONG QUANTITY.** One
     non-vacuity assertion proved the LIBRARY holds unmeasured tags, not that its own oracle
     could ever fire. The other rebuilt an oracle against a run that BY CONSTRUCTION excludes
     what it checks, so it could only pass on a recorded zero. Neither is carelessness; both
     read as correct until a mutant runs.
  4. **A REPAIR CREATED A FALSE GUARANTEE, which is worse than the bug it fixed.** `del body`
     closed `read_properties` and left the exported `parse_properties` open, while the test
     asserted a GENERAL property ("a clockspeed frame") having exercised ONE entry point.
     Before: a known leak. After: a leak plus a green test whose own message denies it. Caught
     by the adjudicator - not by the builder, not by the suite.
  5. **A TEST WRITTEN TO GUARD NON-NEGOTIABLE 7 WAS A TAUTOLOGY.** Its oracle judged the
     PYTHON SHAPE of decoded values, which is a closed set for ANY implementation. A mutant
     fabricating 26950 StructProperty values from raw bytes left the entire suite green.
  6. **8 OF 11 TYPE DECODERS COULD BE DELETED WITH THE SUITE GREEN.** The equality control was
     at BUILDING granularity, so one property per building satisfied it. Only 3 types were
     genuinely covered, and only by accident of this operator's corpus.
  7. **TWO OF CS-413'S THREE ORACLES EXIST NOWHERE IN THE REPO** - prose only. An adversary
     re-derived both and they HOLD, and supplied the shift control one of them never had.
     Filed as CS-420. This is CS-412's failure class landing on CS-413's own evidence.
  8. **THE SHIPPED ROTATION CONTROL WAS TRIVIAL.** All 24314 buildings collapse inside
     `_skip_actor_head` before one property tag is read - zero lines of tag grammar and zero
     of value grammar. The genuine value-start control now ships beside it.
  9. **FIVE "STALE" WORKTREE BRANCHES CARRIED 9 COMMITS AND `git cherry` FLAGGED EVERY ONE AS
     NOT-UPSTREAM.** The session note said safe-to-delete; git's own signal said unmerged.
     CONTENT was the only sound test - every branch-only line was superseded BEFORE text.
  10. **A CITATION I WROTE MYSELF ROTTED WITHIN THE SAME SESSION.** CS-419 cited
     `usmap.py:605-607`; CS-416 added three `__all__` lines above it and the citation slid onto
     the enum NAME resolve - the working case the note contrasts against. A line citation rots
     exactly like a restated count. Cite the symbol.

- **Failed paths - do not retry:**
  - **`py -3` as the interpreter.** An adversary lost its ENTIRE executable pass to it and
    could only report static findings. BOOTSTRAP 2.5 records why; it is still catching agents.
  - **A synthetic fixture as evidence the grammar matches the GAME.** It packs with the same
    byte order the reader unpacks with. It proves self-consistency and nothing else.
  - **`git cherry` as proof a branch holds unmerged work.** This project reworks slices during
    merge, so neither SHA reachability nor patch-id survives.
  - **Putting a measured count into `docs/ARCHITECTURE.md`.** CLAUDE.md section 4 names it as
    a file that never contains counts. Done here while FIXING a fact-ownership violation, and
    caught by the adjudicator.

- **COMMON-MODE RISK - CORRECTED 2026-08-15 (session 8) BY MEASUREMENT. THE RISK WAS ALREADY
  GUARDED, AND THE PROPOSED FIX WAS NOT ONE.** What follows is the original claim and what
  measurement did to it, kept together because the correction is worth more than the claim.
  ORIGINALLY WRITTEN: `_TAG_EXTRA_STRINGS` is transcribed identically into
  `clockspeed/save/objects.py` and `tests/save/test_properties.py`; if any width is wrong BOTH
  walkers desynchronise identically, the join agrees perfectly, and the oracle reports perfect
  health - so CS-420's usmap join, the one oracle that never touches `value_at`, "is therefore
  the fix".
  **BOTH HALVES ARE FALSE, each refuted by a mutant observed red.** FIRST, the risk was already
  guarded and had been for a session: `tests/save/test_properties.py` carries its OWN EQUALITY
  reach oracle over the real library, so under a genuine common-mode fault the copy-based walker
  desynchronises against the REAL BYTES exactly as the shipped one does. Mutating each width in
  BOTH copies identically and deleting both new oracle modules leaves the pre-existing suite red
  on 7 of 7 widths, against a pristine control that exits 0. SECOND, the usmap join is not the
  fix and cannot be: its 13-to-13 bijection survives every width mutant with zero violations,
  byte-identically under `ByteProperty 1->0`. The mechanism is the whole lesson - **a wrong width
  BREAKS the walk, a broken walk contributes NO pairs, so a bijection computed over a shrinking
  population of correct pairs stays pristine while the grammar rots.** A join is evidence about
  the pairs it sees, never about the ones a fault removed.
  The "111 of 129775" figure is deleted rather than corrected, per CLAUDE.md section 4: it is now
  owned and re-derived by
  `tests/save/test_decode_oracles.py::test_the_shipped_walker_reaches_a_terminator_on_every_real_payload`.
  **THE GENERAL LESSON, which outlives this item: an inherited risk stated confidently in a
  resume note was never re-measured, and a whole item was scoped to solve it.** Re-measure the
  premise before building against it - that is cheaper than the item was.

- **Next action:** take **CS-420** - record CS-413's oracles and controls as executable
  artifacts. It is the cheaper of the two and a PRECONDITION for trusting CS-421's result,
  since CS-421's verdict depends on oracles that currently exist only as prose. CS-421 is what
  actually moves CS-413 toward closing. Both are required before CS-413 closes and phase 5
  opens.

## Session 8 - 2026-08-15 - CS-420's artifacts land; the inherited premise turns out to be false

- **Shipped: NO ITEM CLOSED.** CS-420's artifacts landed and it STAYS OPEN on four false prose
  sentences. Filed **CS-425**, **CS-426**, **CS-427**. Two FROZEN-FILE GRANTS recorded, neither
  file edited. Suite 1603 -> **1619 passed, 7 skipped**, exit 0. mypy 75 files, 0 errors.

- **THE HEADLINE IS A REFUTED PREMISE, NOT A DELIVERABLE.** Session 7 handed this session a
  common-mode risk described as UNRESOLVED and sitting underneath 100 per cent of the decoded
  values, and named CS-420's usmap join as "therefore the fix". **BOTH HALVES ARE FALSE.** The
  risk was ALREADY GUARDED and had been for a session - `tests/save/test_properties.py` carries
  its own EQUALITY reach oracle over the real library, and mutating each width in BOTH copies
  leaves the pre-existing suite red on 7 of 7 against a pristine control that exits 0. And the
  join cannot be a width guard: **a wrong width BREAKS the walk, a broken walk contributes NO
  pairs, so a bijection over a shrinking population of correct pairs stays pristine while the
  grammar rots.** An item was scoped to solve a solved problem. Re-measure an inherited premise
  before building against it; it is far cheaper than the item.

- **In flight:** nothing half-done in code. CS-420 is OPEN on PROSE only - four sentences listed
  verbatim in its `ROADMAP.md` entry. Tree clean, no worktrees, no stale branches.

- **Decisions:** no ADR. **TWO OPERATOR FROZEN-FILE GRANTS recorded in `docs/LEDGER.md` BEFORE
  any edit, per CLAUDE.md section 6, and NEITHER FILE WAS TOUCHED** - `tools/precommit_gate.py`
  (unblocking CS-403, CS-209, CS-204) and `.claude/settings.json` (CS-425). Recorded as coming
  from the OPERATOR directly rather than an adjudicator, so no reader mistakes either for an
  agent self-granting.

- **Surprises**, each measured rather than reasoned about:
  1. **THE ADVERSARIAL PASS CHANGED THE OUTCOME THREE TIMES.** An adjudicator ruled CS-420 CLOSES;
     three adversaries running in parallel returned REFUTED on privacy, on clause 4, and on
     control validity. The merger held both and overruled the close. Without the pass this session
     ships a privacy leak, three clause-4 escapes, and a module whose stated reason for existing
     is false.
  2. **A REAL PRIVACY LEAK UNDER DEFAULT FLAGS.** A narrow `except (OSError, HeaderError)` let a
     `MemoryError` escape and pytest rendered a `WindowsPath` carrying the Windows account name,
     the platform account id and a world name - three non-negotiable-3 items in one line, no `-l`,
     no `--tb=long`. Fixed. **It is an INHERITED pattern** - `test_objects.py` and `test_world.py`
     leak identically and are now CS-427.
  3. **NOTHING GRADED THE CONTAINMENT.** Splicing the known-bad discovery shape into the new sweep
     left the suite byte-identically green at 1610/7. After the repair it goes red. An
     equivalent-mutant test is the only thing that proves a containment claim.
  4. **A FIX FALSIFIED ITS OWN COMMIT'S PROSE.** Adding the `_JOIN_WORD_FLOOR = 13` diversity floor
     made the usmap join discriminate 5 of 6 widths, which falsified four sentences saying the
     reach test is the only width discriminator - sentences written in the SAME COMMIT. Three
     consecutive rounds of prose repair each shipped a false sentence, one written specifically to
     correct its predecessor. **The pattern is structural: this module states DETECTION CLAIMS in
     prose, and every assertion change silently invalidates them.**
  5. **A BUILDER REFUSED A FALSE SENTENCE THE MERGER GAVE IT, TWICE OVER TWO BUILDERS.** One
     declined to write a count into a module, citing CLAUDE.md section 4 - an adjudicator GRANTED
     the refusal. Another measured that the merger's replacement justification was itself false and
     wrote the measured claim instead. **Both times the merger had paraphrased an agent's measured
     claim into a stronger one.** A paraphrase is a new claim and needs its own measurement.
  6. **FIVE BUILDERS OUT OF FIVE WERE CUT FROM A STALE BASE**, 1 to 5 commits behind. All five
     caught it only because the dispatch ORDERED the check. Session 5 saw this once and read it as
     a fluke. Saved to harness memory as `worktree-agents-start-stale`.
  7. **THE PreToolUse HOOK CANNOT BLOCK AND CANNOT SEE THE COMMAND.** It exits 1 where the protocol
     requires 2, and fed the hook JSON envelope it returns PASS because JSON escapes non-ASCII to
     ASCII. Proven end to end: a tool call carrying an em-dash RAN UNBLOCKED. **The authoritative
     `.githooks` path was separately proven GOOD** - real commit attempt, BLOCKED, HEAD unchanged.
     CLAUDE.md's "the Claude hooks are a convenience layer" is exactly right; the layer just
     provides no convenience while costing a spawn per shell call. Filed CS-425.
  8. **CLAUSE 3 OF CS-420 WAS MET BY THE COMMIT THAT FILED CS-420.** The value-start rotation
     control shipped in `5d11dc2`, the same commit that wrote "the rotation control in the repo is
     TRIVIAL". An item created to convert stale prose into executable artifacts was itself stale
     prose at the instant it was committed.
  9. **A STALE `__pycache__` POISONED AN ADVERSARY'S FIRST RUN.** A mutant constant was
     byte-identical in LENGTH to the original, so the `.pyc` was reused and the restore looked
     clean. Use `PYTHONDONTWRITEBYTECODE=1` for all mutation work.
  10. **A VERIFIER CAUGHT ITS OWN TOOLING DEFECT.** Python's `write_text` emitted CRLF on Windows,
     so its restores were content-equal but byte-unequal, and its own `read_text` assertion was
     blind to it under universal newlines. Caught on an md5sum.

- **Failed paths - do not retry:**
  - **`pythonw.exe` alone as the CS-425 fix.** It IS a faithful drop-in - identical rc, stdout and
    BLOCKED diagnostic through a real pipe-and-wait - but shipping it alone kills the flash while
    preserving a hook that silently does nothing. That is the false-guarantee class.
  - **A PowerShell invocation as a test of a GUI-subsystem binary.** PowerShell does not wait on
    one, so it reports no output and no exit code. Use `subprocess` with pipes.
  - **A cross-save resolution control for the cross-section oracle.** Measured: 19834 against 26146
    own-index, ratio 1.32. It does NOT collapse, because the library is many snapshots of ONE world.
  - **Rewriting a false detection sentence in prose.** Three rounds, three false sentences. See
    surprise 4 - the next attempt should decide whether such a claim may be prose AT ALL.

- **COMMON-MODE RISK, named and STILL LIVE but correctly scoped:** the CI half. Every discriminating
  test CS-420 shipped is library-backed and skips with no game installed, so on a clone
  `SetProperty 1 to 0` is invisible to the ENTIRE suite. That is **CS-426** and it is genuinely
  open, unlike the real-library half, which was already guarded. Also live and unfixable in-repo:
  every number in this session comes from ONE operator's ONE world on ONE machine.

- **Next action:** take **CS-420**'s remaining prose work, and take it as a DESIGN question rather
  than an edit - decide whether a detection claim may live in prose at all, or must be
  machine-checked or deleted. Then **CS-425**, whose grant is recorded and whose operator ruling is
  "make it actually work" - parse the hook envelope and exit 2 - noting it WILL start refusing real
  tool calls. Then CS-403, CS-209, CS-204 under the recorded gate grant.

## Session 11 - 2026-08-16 - six items close; FIVE OF FIVE slices refuted; ADR 0008 accepted

- **Shipped: CS-211, CS-428, CS-435, CS-436, CS-437, CS-438 CLOSED.** ADR 0008 ACCEPTED with four
  conditions, all applied. CS-420's acceptance RESTATED. Filed CS-439 through CS-448. Suite
  1846 -> **1952 passed, 3 skipped**, exit 0, serial AND under `-n auto`. mypy 79 files clean, ruff
  clean, drift guard **CLEAN 9/9** (a ninth guard now exists), doc budget PASS. Eight commits,
  `76f6c82..b5cad1a`. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THE HIT RATE AND IT GOT WORSE: FIVE OF FIVE FIRST BUILDS WERE REFUTED, plus
  merged `main` itself.** But the useful finding is that FOUR OF THE FIVE HAD ONE SHAPE - a builder
  MEASURED SOMETHING TRUE AND STATED SOMETHING WIDER:
  1. **CS-436:** the budget cannot bound one slow open, therefore it is decorative. It is 5.0s and
     breaks the loop - at 0.4s/read it stops the scan at 13 of 24 while the removal read all 24.
     Removing it was a COVERAGE REDUCTION the grant forbids.
  2. **CS-438:** the handler is unreachable on 3.14, therefore it was unreachable. The DECLARED
     FLOOR is 3.13, where `PathBase.is_file` re-raises outside the ignored errnos, and CI pins 3.14
     at four sites so nothing here would catch it.
  3. **CS-435:** five happy-path indices are flagged, therefore every index is. False at FOUR sites,
     two of which make `parse_usmap` raise and publish NOTHING.
  4. **CS-211:** the parse works on the current sentence, therefore the set is derived. Its fixture
     restated the real doctrine sentence VERBATIM, so the derived and hardcoded paths agreed BY
     CONSTRUCTION and the mutant produced a byte-identical suite result.
  **THAT IS ADR 0008's OWN THESIS ARRIVING IN CODE RATHER THAN PROSE.** The ADR fences the
  sentences; nothing fences the INFERENCE, and the inference is where it landed five times.

- **CS-428's was different and is the one to remember: A PRIVACY CONTROL THAT FAILS OPEN, TRIGGERED
  BY THIS REPO'S OWN TEST SUITE.** Its redaction rules were `lru_cache`d and seeded LAZILY by the
  first report carrying content. `tests/data/test_locate.py:432` patches `USERPROFILE` to a temp dir
  named `home`, so "home" became a session-wide token AND THE REAL SPELLINGS WERE LOST. The grading
  module could not see it: every arm was a cold subprocess with an empty cache. Fixed by building
  the rules once at import.

- **A LIVE CI LEAK WAS FOUND AND CLOSED.** Tier-2 runs `-n auto`; xdist composes its worker line
  AFTER the worker's `makereport`, so the parallel lane leaked a home path on EVERY failure. Fixed
  controller-side - 259 force-failed tests give 259 worker lines and 0 markers against a control
  showing 518.

- **THE FINAL AUDIT REFUTED MERGED `main`, AND ONE FINDING WAS THE MERGER'S.** Three false sentences
  in `tests/conftest.py`. The count "195 test functions" measures **247** by AST and **341** by the
  claim's own wording, and was 325 when written - it was NEVER true, copied from a stale roadmap
  note. **THE MERGER THEN RESTATED IT A THIRD TIME in the ledger entry closing the item, in the same
  session in which it twice flagged other agents for exactly that.** A number arriving inside a
  well-evidenced report reads as evidence rather than as a claim needing its own measurement.
  Deleted, not corrected. The scope list was also wrong in the dangerous direction: it claimed a
  child process's output is NOT reached, and inherited stdout IS.

- **Decisions: ADR 0008 is `accepted`**, adjudicated by an agent that wrote no part of it, with four
  conditions all applied: tier 3's stated ground was REFUTED (two measured-false sentences that
  never rotted - they shipped false); `WAKEUP_NOTES.md` was misclassified as an immutable record and
  the rule now keys on a DATED HEADING, not a filename; the living-text refinement RELOCATES its
  residual to phrasing rather than dissolving it; and Consequences overstated and is narrowed.
  **CS-420's "tension" WAS A MISDIAGNOSIS - do not reopen it.** ADR 0008 SCOPE governs BREADTH,
  CS-420's acceptance governs DEPTH in one module, and that module is already fenced, so the two
  texts never disagreed. Five rounds were spent against a dilemma that was not there. Its acceptance
  is restated on a coverage axis, with its weakest clause LABELLED weaker.
  **A FROZEN-FILE GRANT was issued by the operator for CS-436 alone**, recorded BEFORE any edit;
  `git diff --name-only` confirms no other frozen path on every merge.

- **Surprises**, each measured:
  1. **THE NEW GUARD WENT RED ON THE MERGER'S OWN DOC EDIT, MINUTES AFTER MERGING.** CS-211's
     ownership guard read the CS-420 correction record as a closure, because a record that declines
     to close an item must say so BY NAME and that one did not. Its failure message prescribed the
     fix. Real input, not a planted duplicate.
  2. **THE COMMIT GATE BLOCKED THE MERGER** for writing a literal Linux home path into CS-447 - the
     entry describing a home-path leak. Recorded in the entry rather than quietly fixed.
  3. **THREE REPAIRS APPLIED ADR 0008 TO THEMSELVES**, each deleting detection claims or restated
     counts its OWN repair had just written, one of them three lines below the constants deciding
     the numbers.
  4. **A REPAIR FOUND ITS FINDING WORSE THAN THE ADVERSARY DID, TWICE.** CS-435 found two further
     counter-examples, which changed the fix from reordering to deletion. CS-438 found the same
     false-detail defect at a sibling site nobody had named. CS-211 found F2 covered three clauses,
     not one.
  5. **AN ADVERSARY WAS PARTLY WRONG AND THE REPAIR SAID SO.** CS-428's rule-count figures did not
     reproduce (6/4 not 4/2) while the substance was confirmed and SHARPENED. A "four control
     assertions" figure the merger ordered corrected turned out never to exist in a tracked file.
  6. **CS-435's KEY FOR MECHANICAL SILENT-LOSS DETECTION FAILED ITS FIRST MEASUREMENT AND SAID SO.**
     Keying on a reporting verb anywhere in scope matches 292 of 298 functions. The narrower key
     gets 298 -> 12 and independently rediscovers CS-438, filed by a DIFFERENT agent. That is
     CS-439 and it is evidence rather than argument.
  7. **THE WRITE-LIST BOUNDARY HELD ON EVERY SLICE.** Every agent that found a defect outside its
     list reported it; ten became filed items.

- **Failed paths - do not retry:**
  - **Generalising a narrow measurement into a universal.** Four of five. State the scope you
    measured, including the interpreter and the platform.
  - **A fixture that restates the real input verbatim.** It makes the derived and hardcoded paths
    agree by construction. Declare fixture values DISJOINT from the real ones and test that.
  - **Lazily caching a privacy rule set.** Whatever runs first defines it, and a test that patches
    the environment poisons it. Build at import.
  - **Grading a fence by a constant's NAME.** A renamed equivalent mutant walks through. Find the
    construct by AST and learn the name from it.
  - **Grading session state with cold subprocesses.** Structurally blind to it.
  - **Writing a measured count into prose.** Third instance this session, one of them the merger's.

- **HOUSEKEEPING THAT WILL BLOCK YOU: `ROADMAP.md` IS AT 97 PER CENT OF ITS HARD BUDGET.** It
  PASSES today and `tools/doc_budget.py` FAILS CI above 60 KB, so the next roadmap edit of any size
  goes red. Relocate before you file anything: the superseded dated STATUS blocks inside CS-400 and
  CS-413 are the candidates, and CS-400's entry already marks one of them as no longer the state.
  Relocate to `docs/history_notes.md`, never delete, and leave a one-line pointer.

- **Next action:** **CS-448**, the `-n auto` flake in the no-install save-suite gate - tier-2 CI
  runs that lane and it fails 1 run in 3, measured at BOTH this session's base and head, so it is
  pre-existing and unfiled rather than new. Then **CS-439**, mechanical silent-loss detection, whose
  key is already measured. **CS-420 is now takeable** - its acceptance is restated and its governing
  ADR is accepted, and the two never conflicted; read CS-435's two new derived fences in
  `clockspeed/save/usmap.py` first, they are a worked example of what its clause (2) asks for.

### Archived 2026-08-16 from `WAKEUP_NOTES.md` - session 12 at full fidelity

Aged out when session 15 landed and `WAKEUP_NOTES.md` keeps only the last three sessions.
**Nothing here is current.**

## Session 12 - 2026-08-16 - FOUR OF FOUR slices refuted, plus the merger; CS-448 root-caused

- **Shipped: NOTHING CLOSED, DELIBERATELY.** Four tier-1 slices were built, merged and then REFUTED
  by independent adversaries, so CS-440, CS-441, CS-443 and CS-444 all STAY OPEN, each with a ledger
  record declaring the non-closure BY NAME. The code stays: every slice is a net improvement and the
  suite is green. Filed CS-449 through CS-454. Suite 1952 -> **1993 passed, 3 skipped**, mypy clean
  over 79 files, ruff clean, drift guard 9 guards PASS 8 WARN 1 (the doc budget). Six commits,
  `0377a29..280eacc`. Detail in `docs/LEDGER.md`.

- **CS-448 IS THE SESSION, AND IT REFUTED THE MERGER'S OWN MEASUREMENT.** I measured 32 runs across
  four contention profiles - `-n auto`, `-n 32`, a 4-core affinity-confined tree, and the original
  SHA in its own verified worktree - got zero failures, and concluded it did not reproduce. **AN
  ADVERSARY REPRODUCED IT SIX TIMES at both cited revisions.** Every one of my 32 runs was taken in
  one of the two locations on this machine where the failure is STRUCTURALLY IMPOSSIBLE. They were a
  control that read like a null result, and I did not know the difference.
  **THE REAL CHAIN, and it is neither party's earlier story:** a checkout sharing a large ancestor
  with the system temp root makes pytest's rootdir for the innermost probe climb to that root, so
  collection walks the entire temp tree - **0.4s from three ordinary locations against 42.7s from a
  clone under the temp root, with only the cwd varied**. A sibling xdist worker deleting a
  `clockspeed_gate_*` temp directory mid-walk makes `os.lstat` raise, collection is Interrupted, the
  level-2 child exits 1. **xdist supplies only the concurrent deleter - it is NOT CPU contention, and
  the walk is single-process.** My contention account was wrong, and so was my count of the sandbox
  spawns in that file (12, not seven). What survived: the CI-history reading, independently
  confirmed. Still open: whether a hosted workspace shares that ancestor. Measure `rootdir` in a job.

- **THE INSTRUCTION I WAS GIVEN WAS FALSE AND I MEASURED IT RATHER THAN OBEYING IT.** The session
  prompt and `WAKEUP_NOTES` both said `ROADMAP.md` was at 97 per cent of "the budget that HARD-FAILS
  CI" and that any sizeable edit "goes red". `ROADMAP.md`'s budget is severity **WARN**:
  `doc_budget.py` returns non-zero only on a HARD failure and drift guard (a) returns WARN and exits
  0, and those two are the only CI consumers. It prints loudly and passes. I did the relocate pass
  anyway, and deleted the false sentence from the file rather than hedging it.

- **THE MERGER SHIPPED A FALSE UNIVERSAL AND AN ADVERSARY CAUGHT IT.** My own seam fix claimed every
  exempted class must be a frozen dataclass, "which a resolver is not". A planted frozen dataclass
  carrying `__call__` - an ordinary resolver shape, and one this codebase is actively moving toward -
  walked straight through. Deleted rather than hedged; the check now tests inertness too and is
  graded by the exact shape that broke it.

- **A SECOND MERGER ERROR, AND THE LESSON GENERALISES.** I reported "four of four worktrees cut from
  the correct base". The reflogs show ALL FOUR were cut STALE and each fast-forwarded itself because
  the dispatch ordered the check - nine of nine across sessions. **`git log -1` after the fact cannot
  distinguish "cut correctly" from "cut stale and self-corrected"; the two states are byte-identical
  at HEAD.** Only the reflog separates them. Committing before dispatch does NOT prevent it.

- **Surprises**, each measured:
  1. **A GENUINELY NEW CRASH FOUND BY A BUILDER SWEEPING ITS OWN FILE.** `local_config` raised
     `UnicodeDecodeError` on a non-UTF-8 config - a `ValueError`, not an `OSError`, so it escaped a
     function whose docstring promises it never raises. Confirmed independently against the pre-fix
     blob before it was accepted.
  2. **A SHIPPED CHANNEL WITH NO CONSUMER.** CS-443's reporting channel is passed by nothing in
     `clockspeed/`, `tools/` or `scripts/`, so `verify_env.py` against a malformed config still exits
     0 saying nothing. The acceptance says "reported rather than silent"; end to end it is silent.
  3. **AN OPERATOR-FACING SENTENCE WITH NO CONTROL.** Replacing all six of CS-443's `detail`
     sentences with a nonsense sentence left the module suite green. Only truthiness is asserted.
  4. **A PRIVACY CONTROL BLIND IN THE SAME PLACE AS ITS SUBJECT.** CS-443's redaction oracle reads
     the same and only sources the redactor reads, so it passes vacuously in exactly the environment
     where the redactor fails open. Separately, CS-444's redaction control has an all-digit fixture -
     the one shape the backstop catches unconditionally - so gutting the redactor left it green.
  5. **A LIVE PRE-EXISTING PII LEAK, filed as CS-454.** An account directory that is not all digits
     - Epic, MS Store, or operator-renamed - renders in plaintext once saves are relocated.
  6. **THE ITEM PLAN INHERITED A WRONG CLOSURE.** CS-425 is listed as closed in the session prompt
     and in session 9's notes; its only ledger record is a grant that says it does NOT close it, so
     it is OPEN. Session 10 recorded this class in the other direction.
  7. **AN ADVERSARY WAS PARTLY WRONG AND WAS NARROWED RATHER THAN RELAYED.** The `purge_work_dir`
     finding is real but bounded by two naming conditions, so it was filed at tier 2, not tier 1.

- **Failed paths - do not retry:**
  - **Measuring a location-dependent flake in one location.** 32 runs in an immune tree is a control,
    not a null result. Vary the thing the defect might depend on, including the checkout path.
  - **Running the authoritative suite while adversaries mutate the tree.** It produced five phantom
    failures that vanished on a clean re-run.
  - **`git log -1` as a staleness probe.** It cannot see a self-correction. Use the reflog.
  - **A fixture whose value is the one case the implementation handles.** Two separate privacy
    controls this session, both green while the thing they guard was gutted.

- **Next action:** **CS-454**, the live PII leak, then **CS-449**, whose reachability is now
  reproduced end to end. Both are tier 1 and both sit on non-negotiables. **BEFORE EITHER, do the
  `ROADMAP.md` relocate pass** - it is at 119 per cent of its WARN budget and the cause is structural
  rather than incidental: its entries have become essays while the topology table says one line per
  item. That is a real refactor, not a trim.

---

## Relocated from WAKEUP_NOTES.md on 2026-08-17 (session 16)

## Session 13 - 2026-08-16 - CS-421 and CS-422 land unadjudicated; ROADMAP.md refactored

- **Shipped: NOTHING CLOSED.** CS-421's clauses 1 and 2 are met and clause 3 is met for two of five
  types; CS-422's acceptance reads as met on every clause. **Neither was adjudicated and no adversary
  ran** - I built them and I graded them, which this project does not accept, so both STAY OPEN with
  ledger records declaring the non-closure by name. Filed CS-455, CS-456, CS-457. Suite
  1993 -> **2001 passed, 3 skipped**, mypy clean over 28 files, ruff check and format clean, drift
  guard 9 guards PASS 8 WARN 1 FAIL 0, doc budget **PASS** (was WARN). Detail in `docs/LEDGER.md`.

- **THE ROADMAP REFACTOR IS DONE AND IT WAS THE REFACTOR, NOT A TRIM.** 119 per cent of budget to 57.
  Every oversized entry keeps its line, acceptance, tier, a one-sentence lead and a pointer; 21 full
  bodies relocated VERBATIM to `docs/history_notes.md` with 21 matching anchors and zero dangling
  pointers. **The five entries whose CURRENT STATE is load-bearing - CS-440, CS-441, CS-443, CS-444,
  CS-448 - got hand-written leads**, because an algorithmic first-sentence lead rendered CS-440 as
  "filed as the remainder of CS-435" and buried "built and refuted". A cold session reading that would
  redo refuted work, which is the exact failure this file exists to prevent.

- **THE ENDIANNESS QUESTION IS SETTLED FOR THE TWO TYPES PILLAR 3 NEEDS, against the game's data rather
  than our own writer.** The premise is a fact about the GAME - save int32s are counts and indices, so
  the stored high byte is usually zero - so no fixture this project packs can satisfy it by
  construction. The pivot is half the population, so **no measured constant appears in any assertion**,
  which is deliberate: `_JOIN_WORD_FLOOR = 13` sitting at its observed value is why CS-432 exists.
  Mutants: `">i"` reddens the int oracle at 7926 of 75136 and leaves the float oracle green; `">f"`
  reverses it at 4425 of 31318. The counters EXCHANGE values rather than drifting.

- **A SHIPPED COMMENT CLAIMED THE ENCODING WAS MEASURED AND NOTHING EXECUTABLE CHECKED IT.** Four
  percentages in prose. Its int figures reproduced exactly; **its float figures did not**, because the
  predicate behind "plausible" was written down nowhere - unreproducible by construction. Deleted per
  ADR 0008 rather than corrected.

- **CS-422's INCONSISTENCY DISSOLVED RATHER THAN GOT EXCUSED.** Widths split into two classes needing
  two oracles: a CURSOR width moves `value_start`; an EXTENT width cannot move the cursor at all,
  because the walk advances by `at = value_start + size`. That is STRUCTURAL - I read the advance before
  letting the word "cannot" stand - not a corpus accident. **Sample size was never the operative
  criterion**, so shipping at n=9 and declining at n=11976 was never actually inconsistent.

- **Surprises**, each measured:
  1. **A SPELLING-KEYED TYPE DISPATCH.** `_decode_fixed_width` chose float-vs-int with `code == "<f"`,
     so a float in any other byte order fell into the integer branch where `int(NaN)` raises. Nothing
     was broken on the shipped table - the invariant "the float code is spelled exactly this way" was
     simply never stated. It is also what made the `">f"` mutant unreachable, so fixing it is what let
     the float oracle be proven at all.
  2. **MY OWN DOCSTRING SHIPPED A FALSE ATTRIBUTION AND MY OWN ADVERSARIAL PASS CAUGHT IT.** I wrote
     that the rotation control covers the constant-fabrication gap. Under a constant-1 mutant that
     control stays GREEN - it perturbs the WALK, and a fabricated value does not move the walk. 8 tests
     red, 7 synthetic plus the nested gate. Deleted and replaced with the measurement; the gap is
     CS-455.
  3. **THE CITATION CHECKER IS BLIND TO `#:` DOC-COMMENTS.** Four citations naming real tests resolved
     to TRUNCATED names and `test_oracle_citations.py` PASSED. The underscore-wrap rejoin applies to
     column-0 `#` blocks only. Failure direction is the dangerous one - unreadable reads as absent,
     not as an error. Worked around by moving them; the channel is CS-457.
  4. **A KEY COLLISION IN MY OWN FIRST DRAFT.** `ArrayProperty` ships a tag-extra width AND has its
     value reading declined, so keying the declined table by bare type word read as though the whole
     word were declined. Caught by printing the sets to look for exactly that.
  5. **`git checkout --` TO REVERT A MUTANT DESTROYED MY OWN FIX** in the same file. Invert mutants by
     targeted replace, never by checking out a file that also holds your work.

- **Failed paths - do not retry:**
  - **Trusting a measured number written in prose.** The float percentages did not reproduce and their
    predicate was unrecorded. Derive, or delete.
  - **Attributing a gap to a named control without running it.** The mechanism said it could not fire.
  - **Writing a `path::test_name` citation into a `#:` doc-comment.** It is not read.
  - **An algorithmic first-sentence lead for an entry whose state is the point.** It buried "refuted".

- **Next action:** **CS-420**, the last of the three CS-413 closes through, and the hardest - five
  failed rounds, acceptance restated on a coverage axis, ADR 0008 accepted. **Before building, read
  CS-435's two derived fences in `clockspeed/save/usmap.py`** - they are the worked example its clause
  (2) asks for. **Failing that, get CS-421 and CS-422 ADJUDICATED** - both are built, both are graded
  only by the agent that built them, and neither can close until an independent pass runs.


## Archived wakeup notes

## Session 14 - 2026-08-16 - CS-420 closes on the seventh round; CS-421 and CS-422 both REFUTED

- **Shipped: CS-420 CLOSED.** CS-421 and CS-422 were ADJUDICATED AND REFUTED and both STAY OPEN, each
  with a ledger record withdrawing the previous record's evidence by name. Filed CS-458, CS-459, CS-460,
  CS-461. CS-455's acceptance CORRECTED against a measurement; CS-456 rescoped from one type word to the
  family. Suite 2001 -> **2007 passed, 3 skipped, exit 0**, serial, observed this session. mypy clean
  over 28 files, ruff check and format clean, drift guard **CLEAN 9/9**, doc budget PASS. Detail in
  `docs/LEDGER.md`.

- **THE HEADLINE IS THAT INDEPENDENT GRADING CHANGED THE OUTCOME ON ALL THREE ITEMS, IN BOTH
  DIRECTIONS.** Two items that read as done were refuted; one item that had failed five rounds closed.
  The session prompt offered the adjudication as the CHEAPER alternative to CS-420. It was not cheaper
  and it was the more valuable half.

- **CS-421's int32 oracle passes green on bytes that are not the int32.** Displace the `IntProperty`
  value start by +4 - reading the next tag's name-length prefix - and it scores **75136 of 75136**
  against the correct read's 70669, because a name-length prefix is a small little-endian count and
  carries a CLEANER signature than real values do. Only synthetic fixtures notice. **The as-read
  majority survives at -2, -1, +2, +3 and +4**, so a rotation control testing only plus or minus one
  would pass and prove nothing. `FloatProperty` is NOT refuted - it collapses at every non-zero delta,
  and that asymmetry is a finding. Both cited mutants reproduced digit for digit and the
  non-circularity defence held under three attacks: what failed is ANCHORING, not independence.

- **CS-422's partition assertion compares a set with itself.** `CURSOR_WIDTHS | EXTENT_WIDTHS` is built
  from the same four sources the test builds its own `shipped` set from, so `ungoverned` and `phantom`
  are structurally empty. Confirmed by the merger from source with no mutation needed. Replacing
  `WIDTH_SHIPPING_RULE` with "ship any width you feel like, no evidence needed", emptying
  `DECLINED_VALUE_READINGS`, or gutting all three cited tests each leaves the save suite GREEN, and
  neither symbol has a production consumer. Two of the three tests do not run without a save library,
  so on CI the rule is graded by nothing at all. What survived: `at = value_start + size` is the only
  tag-walk advance in the package, so an extent width genuinely cannot move the cursor.

- **CS-420 WAS REFUTED AT ROUND SIX AND CLOSED AT ROUND SEVEN, and the shape of the failure is the
  item's own signature.** Clause 3's comment half had no liveness floor and could be reduced to probing
  nothing with the full suite green. The prose audit found two false sentences, **one of them CREATED
  by the commit whose stated purpose was stripping false measurements**. The repair DELETED rather than
  reworded, found a third false sentence nobody had listed, and tied both probes to the census
  population. The second clause-5 pass could not break clauses 1 to 4 across 25 injection shapes, 7
  deletion trials, 13 mutants and a 279-position attribution sweep.

- **Surprises**, each measured:
  1. **THE MERGER'S OWN MUTANT LOOP WAS INVALID AND CONTRADICTED TWO AGENTS.** Looping constants inside
     ONE process reported everything red, because the decode sweep is MEMOISED and every iteration after
     the first silently replays the first mutant's verdict. One process per constant: 0 red, **1 / 255 /
     1000 / 65535 / 1000000 GREEN**, 16777216 red. That falsified CS-455's stated premise that a large
     constant goes red, so its acceptance was rewritten.
  2. **THE HARNESS EDIT TOOL WRITES CRLF**, converting whole tracked files. `git status` stays CLEAN
     because `.gitattributes` normalises the blob on commit, so nothing catches it. `git checkout --`
     does NOT fix it - git thinks the file matches. Delete then check out. Recorded in the harness
     memory store as `edit-tool-writes-crlf`.
  3. **THE MERGER REPRODUCED CS-448's MECHANISM BY ACCIDENT.** Removing an agent worktree WHILE the
     authoritative suite was collecting starved that run past twice its normal wall clock. It is the
     concurrent-deleter half of CS-448 arriving from a hand rather than from xdist.
  4. **A BUILDER DISAGREED WITH ITS DISPATCH AND WAS RIGHT.** Told the `monkeypatch` symbol names were
     data, it read them as prose instead - over-reading costs nothing when the string carries no
     marker, and every exemption is a hole to defend. That collapsed the design to ONE string exemption
     class.
  5. **THE CLAUSE-5 ADVERSARY MISSED A FALSE SENTENCE THAT THE BUILDER THEN CAUGHT** - a suite outcome
     the builder had never measured, in its own new prose. Checking one flagged sentence also exposed a
     sibling of the same shape. Where one instance of a shape is found, the family is worth a sweep.
  6. **TextProperty WAS NOT THE ONE HONEST EXCEPTION.** Four type words share the split; three are
     declined in a DIFFERENT table on sample size. The admitted exception was simply the one that got
     transcribed.

- **Failed paths - do not retry:**
  - **Looping mutants inside one process against a memoised sweep.** The first verdict is the only one.
  - **Editing a tracked file with the harness Edit tool and trusting `git status`.** It reports clean
    on a working tree that violates the LF rule.
  - **Deleting a worktree while the authoritative suite runs.** That is CS-448's own mechanism.
  - **Re-wording a false measured sentence.** Every attempt in this project's history produced another
    false one, including one four hours old. Delete, or derive in the run that prints it.
  - **Reading a follow-up item as satisfying the clause it was filed against.** CS-456's existence does
    not make CS-422's exception clause met.

- **Next action:** **CS-454**, the live PII leak on `main` - tier 1, non-negotiables 3 and 12. Then
  **CS-449** (fail-open below CS-444, reachability measured and reproduced end to end, tier 1), then
  **CS-455**, whose acceptance was corrected this session and must NOT be closed with a synthetic
  fixture. **CS-421 and CS-422 both need real work, not re-grading** - CS-421 needs a value-start
  rotation control built knowing +4 does not collapse today, and CS-422 needs its partition derived
  from INDEPENDENT sources (that half is filed as CS-458).

Relocated from `WAKEUP_NOTES.md`, newest first. Never deleted.

## Relocated from ROADMAP.md on 2026-08-18 (session 18)

### Session 16 - relocated wakeup entry

Moved out of `WAKEUP_NOTES.md` 2026-08-18 (session 19), which holds the last two to three
sessions at full fidelity and nothing older. Relocated, never deleted.

## Session 16 - 2026-08-17 - CS-422 CLOSES; CS-421's anchoring half lands and clause 3 still fails

- **Shipped: CS-422 CLOSED.** CS-421 STAYS OPEN with its anchoring half fixed and a ledger record
  declaring the non-closure by name. Filed CS-469, CS-470, CS-471, CS-472, CS-473, CS-474. Suite
  2018 -> **2035 passed, 3 skipped, exit 0**, serial, baseline measured by the merger itself at
  `f20411c` before any slice ran. Drift guard **CLEAN 9/9**. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THAT THE GRADING PASS REFUTED THE MERGER THREE TIMES AND CHANGED THE RECORD EACH
  TIME.** Builders and graders were right against the merger on the seam, on the reason CS-421 cannot
  close, and on a repair instruction that would have destroyed a live check. Every one of those
  corrections landed BEFORE the ledger was written rather than after.

- **CS-421 IS NOT DATA-BLOCKED AND THE MERGER'S RULING THAT IT WAS IS THE SESSION'S WORST NEAR-MISS.**
  The merger ruled clause 3 unsettleable because only **17 of 75136** int32 values carry differing
  middle bytes, so no oracle over this corpus could separate the identity from the middle swap. An
  adjudicator took the measurement the merger had not: **30304 of 31318 FLOAT32 values do carry them.**
  The evidence is in the library in quantity and the shipped float oracle's magnitude band is simply
  too wide to use it - a weakness of the ORACLE. Had that reasoning reached the ledger it would have
  fenced off the one open route. Filed as CS-469 and it is the next action.

- **THE ANCHORING HALF IS REAL AND IT IS THE ITEM'S ONE SOLID GAIN.** `tests/save/test_value_anchoring.py`
  compares the shipped decoder reading in place against the same declared extent in a poison-padded
  buffer: 0 mismatches shipped, **75136 of 75136** under the +4 displacement that leaves the old
  oracle GREEN. The contrast is DERIVED rather than asserted - a test computes which displacements the
  old oracle tolerates and requires that set to be exactly the one this module controls at.

- **CS-422 CLOSED ON SIX EXECUTABLE CONSEQUENCES WHERE SESSION 14 MEASURED ZERO.** The E1 mutant that
  used to leave the whole save suite green now reddens, and with it applied the rest of `tests/save`
  still passes at 1014 - so the new module is the only thing that catches it. Library-free proven with
  an audit hook: 9 passed, 0 skipped, access count 0, with every discovery root pointed at an empty
  directory. `WIDTH_SHIPPING_GROUNDS` is hand-authored and injecting a fifth width turns it RED.

- **Surprises**, each measured:
  1. **THE MERGER SEEDED A FALSE SENTENCE INTO ITS OWN DISPATCH.** It told a builder that a
     plus-or-minus-one rotation control "would pass and prove nothing". The oracle is a CONJUNCTION
     and is RED at -2, -1, +2 and +3, GREEN only at +4. The upstream ROADMAP sentence was true of the
     majority half alone; the dispatch widened it, the builder shipped it at two sites, an adversary
     caught it, and the replacement is a derivation rather than another sentence.
  2. **THE MERGER'S VOCABULARY WIDENING DID NOT DO WHAT IT CLAIMED.** Widening the decline codes was
     meant to make `WIDTH_RULE_EXCEPTIONS` fail on a mis-classified entry. It guards RE-TRANSCRIPTION
     only: the shipped constant and the test evaluate the same comprehension over the same mapping.
  3. **A MODULE-LEVEL COMPREHENSION IS EVALUATED AT IMPORT, so mutating its source in process leaves
     the derived constant STALE** - which a real source edit does not. That flipped one mutant's
     verdict from DETECTED to MISSED and made a per-entry deletion sweep read 4 of 5, not 5 of 5.
  4. **THE ANCHOR CONTROL IS GREEN FOR ANY PURE FUNCTION OF THE DECLARED EXTENT.** A decoder zeroing
     one stored byte of every int32 leaves the whole module green with 4484 values wrong, and across
     the save suite the only catchers are SYNTHETIC-FIXTURE tests - CS-421's own circularity one layer
     along. It establishes WHICH BYTES are read, not WHAT FUNCTION they go through.
  5. **A BUILDER REFUTED A REPAIR INSTRUCTION AND SAVED A LIVE CHECK.** Told the partition assertions
     in `test_properties.py` compare a set with itself, it measured first: the two TABLES cancel but
     the test's own transcribed literals do NOT, so renaming `GUID_BYTES` turns `ungoverned` RED.
     Deleting them would have removed a real transcription check. CS-458's note is corrected.
  6. **THE FALSE SENTENCE WAS IN TWO PARAGRAPHS, NOT THE ONE THE ADVERSARY QUOTED.** The repair
     instruction named one site because that is what was quoted; the builder swept and found the
     duplicate, which a fix scoped to the quotation would have left standing.
  7. **A SUBAGENT'S "no save library on this machine" WAS THE NESTED GATE'S INNER RUN**, which forces
     discovery empty by design. `tests/save` on main is 1007 passed 0 skipped. Taken at face value it
     would have condemned a slice as unmeasurable.
  8. **WORKTREE STALENESS FIRED IN 3 OF 4 BUILDERS**, including one dispatched explicitly against a
     post-merge commit that found itself two merges behind.

- **Failed paths - do not retry:**
  - **Recording CS-421 clause 3 as blocked by the corpus.** The float32 population carries the
    evidence; the oracle cannot use it.
  - **Deleting the partition assertions in `test_properties.py`.** They still catch a literal rename.
  - **Mutating a table in process and reading a constant derived from it at import.** Re-derive, or
    the verdict is about a stale value.
  - **Leaving mutation harnesses in a gitignored directory.** A caveat in a destroyed scratch file is
    not a caveat in the artifact - the limits had to be re-derived by a verifier and then written into
    the module.
  - **Trusting a substring scan to grade prose.** A rule text naming every code while inverting the
    rule passes it, and so does one that names every code and governs nothing.

- **Next action: CS-469**, the float32 discriminator over the values whose middle stored bytes differ.
  It is the only open route to CS-421 clause 3, which is the last of the three items CS-413 closes
  through - and CS-413 is the phase-4 depth gate that CS-400, then CS-500, then the dashboard sit
  behind. **Do NOT close it with a band narrowed until it separates today's corpus** - that is the
  `_JOIN_WORD_FLOOR` shape CS-432 exists to remove. After it, CS-471 is tier 1 and privacy-adjacent.

### CS-421 - status history

**STATUS 2026-08-23: CS-421 IS CLOSED - see `docs/LEDGER.md`. The sentences below saying it
stays OPEN are history and are not edited. The live fences travel with CS-825 and CS-826; read
the banner under `CS-421 - detail`.**


**STATUS 2026-08-18 (session 19) - relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted.** ROUTE (b) IS BUILT AND SHIPPED AND CS-421 STILL DOES NOT CLOSE -
THE REFUSAL IS THE RESULT, NOT AN UNFINISHED ATTEMPT. The full record, every figure and the
five corrections that landed before it was written are in `docs/LEDGER.md` under the
2026-08-18 CS-421 entry; they are deliberately not restated here. The word
`oracle_cannot_separate_readings` ships for `UInt32Property` and is derived by
`tests/save/test_value_anchoring.py::test_the_cannot_separate_status_is_derived_from_the_oracle`.
The superseded STATUS blocks from CS-421's `ROADMAP.md` entry, moved here verbatim when that entry alone reached 7841 bytes and carried the file over its WARN budget. The item is OPEN; its current status stays in `ROADMAP.md`. Each block below records at least one sentence that a later session MEASURED FALSE, which is why they are relocated rather than dropped - a reader who does not know which claims were already refuted will rewrite them.

**RELOCATED 2026-08-18 (session 19): the session-18 STATUS and CENSUS blocks below joined them, for the same budget reason. The CENSUS is the derivation of the population CS-421's remaining half turns on, and its fence against recording the item as data-blocked is still binding. Session 19 built the route it sanctioned and REFUSED THE CLOSE - read the current STATUS in `ROADMAP.md` for why, and do not read the census below as licensing a close it does not.**

**STATUS 2026-08-18 (session 18): CS-476 CLOSED AND THE ARTIFACT IS NOW FENCED.** The per-type status data is graded against the population the oracles actually score, derived by execution, so the `UInt32Property` half of this item can now be edited without the edit being ungraded - which is the whole reason CS-476 was taken first. `VALUE_BYTE_ORDER_STATUS` still records `UInt32Property` as `unscored` and THAT IS STILL THE OPEN QUESTION; CS-476 changed what happens if someone writes a different word there, not what the word is. Do NOT read the fence as progress on clause 3. The two acceptable closes are unchanged, and the second is a legitimate result: an oracle scoring `UInt32Property`'s own population, or a DERIVED status word separating `no oracle written` from `population cannot separate`. DERIVE THE COUNT AT RUNTIME - the figure 9 is an archived session-14 number that was never re-measured. **CENSUS 2026-08-18 (session 18) - THE POPULATION IS DERIVED AND IT DECIDES WHICH CLOSE IS HONEST. Re-measured from the library this session, not carried:** across the saves walked, `UInt32Property` yields **9 values carrying exactly ONE distinct stored byte pattern**. The figure 9 matches the archived session-14 number, and that is a COINCIDENCE OF RE-MEASUREMENT rather than a carry-forward - it was derived again from scratch. **ROUTE (a) IS NOT AVAILABLE AND THE REASON IS THRESHOLD-FREE:** every one of those values carries a ZERO HIGH BYTE UNDER BOTH READINGS, so the shipped int32 magnitude oracle - a CONJUNCTION requiring a majority to carry the small-magnitude signature as read and a MINORITY to carry it swapped - is provably VACUOUS on this type's own population. That is a fact about the oracle applied to the population, not a tuned threshold, and it is the distinction route (b) asks the status word to record: an oracle EXISTS, was APPLIED, and returns no verdict here - which is not the same as no oracle having been written. **DO NOT WRITE THAT THIS ITEM IS DATA-BLOCKED AND DO NOT LET THIS CENSUS BE READ AS SAYING SO.** The forbidden sentence is about the CANDIDATE ORDERINGS over the joint IntProperty and FloatProperty populations, and it was measured FALSE - CS-469 found the evidence the corpus held all along. This is a different and much narrower claim about ONE type's OWN population. Conflating the two would re-fence the route CS-469 opened. **AND THE POPULATION OF ONE PATTERN IS NOT ITSELF AN ARGUMENT.** A single pattern is not invariant under the group, so an oracle over it would still return a number - an anecdote dressed as evidence. Any close resting on the population being SMALL rather than on the shipped oracle being VACUOUS is the `_JOIN_WORD_FLOOR` shape CS-432 exists to remove. Rest it on the vacuity, which needs no threshold. Derivation must be test-side and library-backed: `objects.py` cannot read the library without breaking the seam, so the module ships the word and a test derives the verdict, which is the pattern CS-476 established for this same artifact. On a machine with no game that test skips, which is CS-426's recorded gap.

**STATUS 2026-08-16 (session 14): ADJUDICATED AND REFUTED. THE INT32 HALF OF CLAUSE 3 DOES NOT HOLD.** Clauses 1 and 2 are MET and are not in question. Clause 3 is REFUTED for `IntProperty`: displacing its value start by +4, so the decode reads the next tag's name-length prefix and never touches the int32, leaves the oracle GREEN at 75136 of 75136 against the correct read's 70669, and only synthetic fixtures notice. The as-read majority survives at -2, -1, +2, +3 and +4, so **a rotation control testing only plus or minus one would pass and prove nothing.** The `FloatProperty` half is NOT refuted - it collapses at every non-zero delta, and that asymmetry is a finding. Both cited mutants reproduced digit for digit and the non-circularity defence survived three attacks, so what failed is the oracle's anchoring, not its independence. **REMAINING WORK IS SMALLER THAN IT LOOKS:** `Int8Property` and `BoolProperty` are one byte, so byte order is VACUOUS for both rather than open, leaving `UInt32Property` as the only live 4-byte question - but the shipped data does not distinguish vacuous from open. Full record in `docs/LEDGER.md` under the 2026-08-16 CS-421 refutation entry. **STATUS 2026-08-17 (session 16): THE ANCHORING HALF IS FIXED AND CLAUSE 3 IS STILL NOT MET.** `tests/save/test_value_anchoring.py` ships the anchor the old oracle lacked - 0 mismatches shipped, 75136 of 75136 under the +4 displacement that leaves the old oracle green - and `objects.VALUE_BYTE_ORDER_STATUS` now derives VACUOUS from a one-byte width so the shipped data no longer reads as three open questions where there is one. **TWO CORRECTIONS TO THE STATUS ABOVE, both measured.** First, "the as-read majority survives at -2, -1, +2, +3 and +4" is true of the MAJORITY half only; the oracle is a conjunction and is RED at -2, -1, +2 and +3, GREEN only at +4. That relation is now derived by a test rather than written down. Second, **THE QUESTION IS NOT DATA-BLOCKED AND MUST NOT BE RECORDED AS SUCH** - 17 of 75136 int32 values carry differing middle bytes but 30304 of 31318 FLOAT32 values do, so the library holds the evidence and the shipped float oracle's magnitude band is too wide to use it. The route out is CS-469. **STATUS 2026-08-17 (session 17): THE CANDIDATE SET NO LONGER LEAVES A CHOICE AND CLAUSE 3 IS STILL NOT MET.** CS-469 closed. The sentence this replaces - that two candidates stand, the identity and the middle swap - is FALSE from that work forward and must not be carried into any later entry; what survives the value oracles is owned by `objects.BYTE_ORDER_SURVIVING_CANDIDATES` and derived from the library by `tests/save/test_value_anchoring.py::test_the_shipped_candidate_set_is_what_the_value_oracles_cannot_separate`, which asserts the derivation against the shipped literal in the direction that reddens when the constant is narrowed without the evidence narrowing. Read the set there rather than from a count here. **WHAT REMAINS IS NOT THE ORDERING, IT IS THE TYPE NOBODY SCORED.** The narrowing is JOINT over `IntProperty` and `FloatProperty` values alone - the census skips every other type word - so `UInt32Property`, a four-byte member of `MEASURED_VALUE_TYPES` that the same reader decodes and ships, is scored by nothing and `objects.VALUE_BYTE_ORDER_STATUS` records it `unscored`. That is the live 4-byte question the session-14 refutation named under remaining work and no session has taken. Carrying the joint result across to it needs the premise that this format uses one byte order for every four-byte field, which `objects.py` refuses IN WRITING for the declared size field in the same docstring block. **AND THE PER-TYPE STATUS IS UNGRADED ABOVE ONE BYTE:** measured 2026-08-17 by the adjudicator, marking `UInt32Property` `anchored_not_unique` - claiming an oracle backs a type nothing scores - leaves the whole save suite green, because `_BYTE_ORDER_ANCHORED_VALUES` is a hand-written pair no test derives from what the oracles admit. Filed as CS-476; it is not CS-459, which is the evidence table and the opposite direction. Full record in `docs/LEDGER.md` under the 2026-08-17 CS-421 entry.

## Relocated from WAKEUP_NOTES.md on 2026-08-18 (session 18)

## Session 15 - 2026-08-16 - CS-454 built, merged, and REFUTED on clause 1; the fence it shipped is refuted too

- **Shipped: NOTHING CLOSED. CS-454 STAYS OPEN** with a ledger record declaring the non-closure by
  name. Clause 2 MET, clause 3 MET, **clause 1 NOT MET**. The code stays - it is a real improvement.
  Filed CS-462, CS-464, CS-465, CS-466, CS-467, CS-468. Suite 2007 -> **2018 passed, 3 skipped,
  exit 0**, serial, baseline measured by the merger at `bb7a236` in a real checkout BEFORE merging.
  Two commits, `60068a9` and `02523f9`, merged at `9c30fd9` and `758888d`. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THAT THE FIX WORKS AND THE ITEM STILL DOES NOT CLOSE.** The relocated-path form
  is closed in all four resolution states, the 8.3 form is closed, and three independent vacuity
  reasons were removed from the controls. Then an independent adversary found a leak the merger, the
  planner and the builder had all missed, and it is in the NEW design rather than pre-existing.

- **THE JUNCTION DEFECT, and it is the session's real result.** `_remember_save_root` stores
  `_path_forms(str(path))` and never resolves; `clockspeed/save/workdir.py`'s `_resolved()`
  deliberately DOES resolve, and its docstring says so. So whenever the save root is reached through
  a junction the two halves of the same package cannot agree on spelling, no anchor matches, and a
  hex account directory renders WHOLE through the production refusal in `_refuse_if_forbidden`.
  Reproduced by the merger with a real `mklink /J`, all self-checks passing first. Junctioning a save
  folder onto another drive is the ordinary way to relocate one.

- **PLACEHOLDER INJECTION DEFEATS THE POSITIONAL RULE, and it fires WITH THE MARKER PRESENT.** The
  environment pass runs first and rewrites a matching needle to a token, injecting `<` into the
  account segment; `_PATH_SEGMENT_CLASS` excludes `<>` so position cannot match, and the remembered
  name pass then hunts a literal the text no longer contains. `USERNAME=Ada`, account directory
  `Ada4f3a...` -> 30 of 33 characters in plaintext. Pre-existing, unchanged from `bb7a236`.
  **RULED: a pre-existing instance of the exact defect an item names does NOT excuse that item**, and
  the reason is in CS-454's own detail entry, which opens by calling the leak pre-existing.

- **THE FENCE THIS SESSION SHIPPED IS ITSELF REFUTED, filed as CS-465.** The redact-cycle pin walks
  the transitive closure to unbounded DEPTH but grades against `RESOLVER_NAMES`, `locate`'s PUBLIC
  surface, while four of the seven hops in the cycle are private. Confirmed by the merger with the
  fence's own helper: a private-hop plant closes the cycle and the fence reports GREEN while the same
  tree raises `RecursionError`. Its own comment says it reads the closure precisely because "a single
  private wrapper would defeat a body-only check".

- **Surprises**, each measured:
  1. **A NON-DIGIT FIXTURE ALREADY EXISTED AND PROVED NOTHING.** `ACCOUNT_DIR_SHAPES` shipped four
     shapes, three already non-digit - but every path carried the marker, so position caught all
     four. Neutering the DIGIT BACKSTOP left **0 of 4** leaking; neutering POSITION left 3 of 4. So
     clause 2 read naively was ALREADY SATISFIED while the leak was live. A control must be a
     CONJUNCTION: non-digit AND a layout where position cannot fire AND a named mutation.
  2. **THE CONTROLS WERE CARRIED BY A NEIGHBOUR TEST.** `test_workdir.py` had no reset of
     `_RESOLVED_ACCOUNT_NAMES`; one test seeded the needle for the whole process. Measured ON THE
     PRE-FIX TREE at `bb7a236` and quoted here only as session history - alone 1 failed, full module
     73 passed. **Neither figure reproduces at `758888d` and neither should be carried forward.**
     Under `-n auto` that made it vacuous NONDETERMINISTICALLY, which is the shape that survives.
  3. **THE NAIVE IMPLEMENTATION WOULD HAVE BEEN INERT ON THE ORDINARY MACHINE.** Appending the new
     pass after the env pass leaks everything, because the env pass has already rewritten the path
     out from under the needle. Live only in the relocated case - the inverse of the filed one. The
     builder demonstrated the counterfactual rather than asserting the three-form design was needed.
  4. **THE MERGER CITED A VACUOUS CONTROL.** "The recursion does not occur even with a collector
     wired through `_override`" tests only half the counterfactual: with the shipped code calling no
     resolver, wiring a collector cannot recurse, trivially. The adjudicator built the real one and
     got `RecursionError`. The conclusion held; the evidence did not.
  5. **THE MERGER'S OWN FOUR-STATE MATRIX WAS THE COMMON-MODE RISK.** It varies override,
     digit-neighbour and resolution order and varies NOTHING about link indirection, username
     collision or whitespace - so three surviving channels are invisible to it by construction, and
     the junction defect sits exactly in that blind spot. Every agent inherited those blind spots.
  6. **BOTH BUILDERS LEFT THEIR WORK UNCOMMITTED** on branches whose `git diff` against the base was
     EMPTY. Merging the branch names as reported would have merged nothing.

- **Failed paths - do not retry:**
  - **Reading "use a NON-digit fixture" as sufficient.** Three of four shipped shapes were already
    non-digit and the leak was live.
  - **Widening `_PATH_SEGMENT_CLASS` to close the whitespace tail.** Three variants measured, all
    worse; one eats the diagnostic prose, one leaves the terminal segment fully intact.
  - **Calling a resolver from inside `redact()`.** Latent infinite recursion that CS-443 detonates.
  - **Feeding `_RESOLVED_ACCOUNT_NAMES` from every save-root subdirectory.** Breaks a shipped
    assertion against the game's own `common` directory.
  - **Trusting a branch name from a builder.** Check the diff against the base before merging.

- **THE SAVE LIBRARY GREW THIS SESSION AND CS-G05 MOVED, THOUGH NOT ALL THE WAY.** The operator
  played the pinned world forward and saved. The version-60 pair went from two files that were
  byte-identical over the measured region - ONE observation - to FIVE files of differing sizes
  where 10 of 10 pairs diverge. **BUT the earliest divergence is at offset 12 and the latest at
  offset 30, which is header metadata, so what is proven is that they are distinct FILES and NOT
  that the property payload is independently sampled.** The merger's first probe treated five
  digests as five observations, which is precisely the file-count-as-independence-count error
  CS-G05's own entry warns about; a second probe caught it. Full status in `docs/GATED.md`.
  The PREP harness still passes, which is correct - it pins a negative.

- **Next action: OPERATOR-DIRECTED 2026-08-16 - TAKE CS-421 AND CS-422, NOT CS-454 AND NOT CS-465.**
  The reason is the critical path to a usable surface: `CS-413`'s own entry names CS-420, CS-421 and
  CS-422 as the gap between "the values were produced and are self-consistent with our own writer"
  and "correctly decoded". CS-420 closed in session 14, so CS-421 and CS-422 are the last two, and
  CS-413 is the phase-4 depth gate that CS-400, then CS-500, then the dashboard all sit behind.
  `IntProperty` and `FloatProperty` are inventory counts and clock speeds, which is exactly what
  pillar 3 reads, so this is the audit's own evidence base rather than abstract rigour.
  **CS-454 and CS-465 STAY OPEN and are deferred, not dropped** - CS-454 has four named blockers in
  its ROADMAP entry and CS-465 is this session's own porous fence.

## Wakeup notes - sessions 21 and 22

Relocated from `WAKEUP_NOTES.md` 2026-08-20 (session 24) under that file's own
two-to-three-session rule, verbatim and not summarised. A fourth session had landed.

**THE ORDER CONTRADICTION IS STILL OPEN AND IS NOT RESOLVED BY THIS MOVE.**
`WAKEUP_NOTES.md`'s header says NEWEST FIRST while its entries run oldest first, and did so
before session 23 touched it. Sessions 23 and 24 both declined to reorder three blocks under
a rule they might be misreading. It is an operator call which of the two is wrong.

## Session 21 - 2026-08-19 - CS-482 CLOSES; the walk was desynchronised and the same defect shipped twice

- **Shipped: CS-482 CLOSED, and CS-485's licence gate recorded.** Filed CS-483, CS-484, CS-486.
  Enlarged CS-471 and CS-473. Amended one `CLAUDE.md` Settled entry. Suite
  **12 failed 2073 passed 3 skipped -> 2137 passed 3 skipped exit 0** with a library, and
  **2036 -> 2088 passed 52 skipped exit 0** with no game, both measured by me this session.
  mypy clean 28 and 84, ruff check and ruff format clean 84, drift guard **CLEAN 9/9**, doc
  budget **PASS measured 16**, precommit gate PASS 150. Detail in `docs/LEDGER.md`.

- **THE ANSWER TO CS-482's QUESTION IS DESYNCHRONISED WALK, AND THE ITEM WAS RIGHT TO FORBID
  RAISING THE CEILING.** The declared count that tripped the bound decodes to four printable
  ASCII bytes - the walk was taking a count out of the middle of a string. **Two corrections to
  the item's own filing text, both measured:** the refusal was against `MAX_CUSTOM_VERSIONS`
  and NOT `MAX_OBJECTS`, and `test_save_60_refuses_the_grammar_the_other_pairs_accept` carried
  NO independent evidence - all seven `test_properties.py` failures arrive through one shared
  `_sweep_or_skip()` assertion, so it was one failure counted seven times rather than a second
  witness.

- **WHAT WAS WRONG, AND IT WAS WRONG IN TWO PLACES.** A named (14,60) level tail is an opaque
  word, a COUNT, that many string pairs, and a second opaque word; it was read as 12 constant
  bytes. The count is 0 on 1522 of the 1525 real level tails here, which is why 12 fitted every
  save the grammar came from. **The identical defect was shipped one function up the same call
  path** - the package summary's 70-byte "constant run" is a string, 22 opaque bytes and a
  second string - and its recorded justification was false: the search that found "no interior
  boundary - not 4+6, not 8+2, not 16+10" looked for a split into FIXED widths, and the
  boundary is a LENGTH PREFIX. The fixture wrote 70 zeros for the same stated reason, so it
  could never have failed the reader that read them.

- **THE TRANSFERABLE SENTENCE: A RUN EVERY SAVE IN A CORPUS FILLS IDENTICALLY IS NOT A
  CONSTANT.** It is a field nothing has varied yet, and the two are indistinguishable from
  inside the corpus. The second value arrives as a desynchronised walk. Both halves of this
  session's fix are that one sentence.

- **ALL THREE REFUTATION PASSES SUCCEEDED. Do not record CS-482 as a clean build.**
  1. **A PRIVACY PASS REFUTED ME ON A NON-NEGOTIABLE.** My own first-draft docstring put a
     positioned four-byte fragment of a decoded string from a real save into a TRACKED file, in
     decimal AND in ASCII. Removed. The same pass showed the four existing privacy controls had
     **ZERO REACH** into the new code - every planted failure went through the FLAT walk and the
     new readers are reachable only from `parse_body` - and proved it with a mutant whose
     exception message was the two decoded strings verbatim, green at 1056 tests.
  2. **A DERIVATION PASS DELETED A FALSE JUSTIFICATION AND FOUND THE SIBLING.** It measured that
     an unbounded entry count executes ZERO loop iterations over nine deliberate
     desynchronisations, because `_Cursor.string` refuses first - so my sentence claiming the
     ceiling prevents a long walk was false. It also narrowed my evidence base: the three
     entry-carrying tails are BYTE-IDENTICAL and all five (14,60) saves are one world, so the
     grammar rests on ONE observed entry.
  3. **A MUTATION PASS GRADED THE TESTS AND REFUTED THEM: 26 mutants, FIVE surviving.** All six
     now die in both configurations after repair, re-graded by me in a clone.

- **EVERY HOLE ALL THREE PASSES FOUND WAS A POPULATION THE TEST NEVER SUPPLIED.** Two entries, a
  second string length, a second escape route for a retained string, a ceiling probed only
  against itself. The corpus could supply none of them; the fixture could supply all of them for
  nothing. That is the session's method finding and it generalises past this item.

- **Surprises**, each measured:
  1. **THE LANDING ORACLE IS NECESSARY AND NOT SUFFICIENT.** Three rival tail grammars - a fixed
     80-byte blob, two parallel lists, a presence flag instead of a count - ALL land 17 real
     saves of 17 on the exact final byte. What actually separates the shipped reading is that
     two length prefixes tile a CLOSED interval with zero slack, each landing on its own
     terminator. Stop citing the final-byte oracle alone.
  2. **A CONSTANT CAN GRADE ITSELF AND LOOK FULLY TESTED.** `MAX_LEVEL_TAIL_ENTRIES` moved to
     `1 << 30` and to `1` with the whole suite green, because the test declared
     `MAX_LEVEL_TAIL_ENTRIES + 1` and asserted against `MAX_LEVEL_TAIL_ENTRIES`. The edge probe
     beside it had the same defect - it pinned the edge RELATIVE to the constant. It is bounded
     from above now by the smallest int32 four printable ASCII bytes can make, and from below by
     a two-entry walk.
  3. **CI RUNS A DIFFERENT RUFF THAN THIS MACHINE DOES, AND SESSION 19's FIX DOES NOT COVER IT.**
     The first push went red on FURB192 - PREVIEW on the local ruff, STABLE on CI's, because
     `pyproject.toml` pins `ruff>=0.13` with no upper bound. Running `ruff format --check` as
     well as `ruff check` does not reproduce CI when the divergence is the VERSION. `--preview`
     is not the local proxy either: 105 findings against CI's 1. Filed CS-484.
  4. **THE FAILING LINE WAS SESSION 20's, NOT MINE.** It shipped in `e86f84d` and CI had never
     seen it, because that session's push was blocked by the very suite CS-482 fixed. A blocked
     push hides a lint failure for a whole session.
  5. **THE OPERATOR PLAYED THROUGHOUT AND THE SAVE FILES WERE OVERWRITTEN IN PLACE, TWICE.** The
     three autosave slots moved 18:47/18:52/18:57 -> 19:02/19:07/19:12 -> 19:42/19:47/19:52
     while I worked, each rotation carrying a larger body. A per-save measurement is pinned to a
     moment, not to a path.
  6. **MY NEW FRAME-LOCALS CONTROL FOUND A PRE-EXISTING EXPOSURE AND I DID NOT WIDEN CS-482 TO
     FIX IT.** The parser's entry points bind the raw body as a PARAMETER and the flat walk binds
     each record's three strings as locals, so any renderer showing locals prints all of it. That
     is CS-471's class. The control is scoped to the strings that are supposed to be DISCARDED,
     and `test_the_entry_points_still_bind_the_raw_body_where_a_renderer_can_read_it` PINS the
     rest so the narrowing cannot be read as a claim of absence.
  7. **THE OPERATOR CORRECTED MY PROVENANCE FRAMING.** satisfactory.wiki.gg is the OFFICIAL
     wiki, so "no community-compiled datasets" was the wrong fence. The gate still refuses
     vendoring, now on the LICENCE - CC BY-NC-SA 4.0, copyleft plus non-commercial, conflicting
     with the frozen `LICENSE`. The `CLAUDE.md` Settled entry is amended to say so.

- **Failed paths - do not retry:**
  - **Citing the final-byte landing oracle as if it settled a grammar.** Three rivals land.
  - **Asserting a ceiling against itself**, or pinning an edge relative to the constant.
  - **Asserting "never retained" against the returned model's repr alone.** A module global and
    an attribute on the cursor both survive it, and a frame local survives all five older
    exception surfaces because `traceback.format_exception` renders none of them.
  - **Testing a counted list at 0 and 1.** `range(min(count, 1))` survives.
  - **A fixture that writes zeros into a run the parser reads structurally.** With an empty
    first name, `4 + 22` and `22 + 4` land on the same byte and a whole reorder class goes
    invisible without a save library - which is every CI run.
  - **`ruff check --preview` as a local proxy for CI.** It over-approximates 105 to 1.
  - **Trimming prose to meet a doc budget.** ROADMAP went over again; one relocation fixed it.

- **Next action: CS-481**, using the reproduction on its ROADMAP entry. It is the half of the
  byte-order key bound that was never derived, and the width table is SELF-AUTHORISING. **DO NOT
  close it by widening the tag-carried exemption - the route does not go through it.** Note that
  CS-482 changed `objects.py` around the level tail and the package summary, so re-read the
  module before assuming session 20's line numbers. Then **CS-478**, then **CS-471** (tier 1,
  privacy-adjacent, and this session added measured evidence to its entry plus a pinning test
  that FAILS when it closes), then CS-477, CS-479, CS-470/472/473/474. **CS-484 is cheap and
  blocks nothing but will bite again on the next push.**

## Session 22 - 2026-08-19 - CS-481 CLOSES on its acceptance; all three refutation passes succeeded and two found routes that still work

- **Shipped: CS-481 CLOSED.** Filed CS-487, CS-488, CS-489. Suite **2137 passed 3 skipped ->
  2141 passed 3 skipped exit 0** with a library, and `tests/save` **1055 -> 1059 passed, 49
  skipped exit 0** with no game, both measured by me this session. mypy clean 28 and 47, ruff
  check and ruff format clean 84, drift guard **CLEAN 9/9**, doc budget **PASS measured 16**
  after one relocate pass, precommit gate PASS 3. Detail in `docs/LEDGER.md`.

- **THE CLOSE IS ON THE STATED ACCEPTANCE AND NOT ON "THE WIDTH TABLE IS NOW BOUNDED", AND THE
  DIFFERENCE IS THE WHOLE ENTRY.** The three-line reproduction is dead: it reds two new controls
  plus the phase-4 gate with no game. Two refutation passes then measured WIDER routes still
  green, and I re-measured both in clones. Six lines make the module CLAIM the type outright and
  ship `vacuous_one_byte` for an eight-byte type, everything green - that is CS-488. Three lines,
  all in `objects.py` with NO test-side line at all, do it through the tag-carried exemption with
  no width entry involved - that is CS-487, and it is CS-480's disclosed residual priced properly
  for the first time.

- **ALL THREE ADVERSARIES SUCCEEDED AGAIN, AND ONE OF THEM BROKE MY OWN CONTROL RATHER THAN MY
  PROSE.** The probe could not build a tag for any word carrying tag-extra strings, so those words
  were filtered out of the CONTROL population while the GRADED arms iterated the width table raw
  with no such filter. Demonstrated on the shipped word `ByteProperty`. A later slice doing the
  honest thing would have been reddened by a message blaming the width table for a defect in my
  builder. **THE FIX WAS TO BUILD THE SHAPE, NOT TO ADD A SECOND FILTER** - the control population
  went from 2 words to 6.

- **SIX SENTENCES I WROTE WERE MEASURED FALSE.** That a constant probe would satisfy two of the
  three arms (at most one, enumerated). That without the control arm a broken builder would still
  be graded green (the agreeing arm reds on its own). That the citation checker is blind to a
  `#:` line (it resolves citations there and merely never REQUIRES one) - and that sentence was a
  RESTATEMENT of a false claim already in the file, which is the section 4 drift, so the fix was to
  delete my copy rather than correct it. A "reds three tests" count that invited the wrong mapping.
  A value-bytes rationale describing a discipline all three of its own call sites break. And a
  first draft of the residual paragraph that stopped at a red **two lines short of green**.

- **AN EQUIVALENT MUTANT SURVIVED THE FIRST BUILD.** Exchanging the string values of the two walk
  outcome words left every control green while INVERTING every rendered failure message, so a
  genuine desynchronisation would report itself as unmodelled content in the sentence a reader
  acts on. The module already had this exact defect and its exact pin for the STATUS words; the
  five new outcome words got none. Pinned now, and graded by me with that swap.

- **Surprises**, each measured:
  1. **A RED TWO LINES SHORT OF GREEN IS NOT A BOUND.** My corrected paragraph rested on
     `test_the_synthetic_fixture_exercises_every_measured_type_word` going red on the wide route.
     It does. Two passes then supplied the fixture tag and the expected-value line - for a width-1
     lie the "decodable instance" is one `struct.pack("<b", ...)` call - and it goes green.
     **Stopping at the first red and calling the route expensive is the same error as stopping at
     the first green and calling it safe.**
  2. **WHAT PUTS A WORD IN REACH OF THESE CONTROLS IS THAT THE MODULE NAMES IT.** Both new arms
     read tables keyed by type word. `DoubleProperty` - a real eight-byte Unreal type this repo
     names nowhere - walks past the claim arm because there is nothing to intersect with. Honesty
     about a word is what puts it in reach; silence keeps it out.
  3. **THE WALK ARM IS WORD-AGNOSTIC ON THE OTHER LINE, WHICH IS THE HALF THAT SURVIVED.** A
     never-named type declared one byte wide and severed from `MEASURED_VALUE_TYPES` reds it and
     nothing else in the suite.
  4. **BOTH ARMS OF THE WALK CONTROL ARE NARROWER THAN THEY READ.** The agreeing arm takes the
     width from the same table `_decode_fixed_width` tests against, so no self-consistent entry
     can fail it - an entry pairing width 1 with an eight-byte code passes. At width + 1 the
     disagreement arm reduces to asking whether the word is in `MEASURED_VALUE_TYPES`, which is
     DERIVED from the width table. The one edit either arm catches is an edit to that derivation.
  5. **GUTTING ALL FIVE NEW ASSERTIONS TO TAUTOLOGIES LEAVES THE CLEAN SUITE GREEN**, as does
     deleting all six emptiness guards. That is what a guard IS on a clean tree, and it is why the
     forgery - not the suite - is what grades these.
  6. **PROSE INSIDE A REGION-TABLE ENTRY IS READ BY NOTHING.** Two passes found the same dangling
     sentence independently. Filed as CS-489.

- **Failed paths - do not retry:**
  - **Filtering a population out of a CONTROL while leaving the graded arms unfiltered.** Build the
    shape the reader expects instead.
  - **Stopping at the first red when pricing an escape route.** Take it two lines further.
  - **Restating another file's sentence to explain a choice.** If the sentence is false, you have
    now shipped it twice.
  - **Shipping a new internal vocabulary without a spelling pin** when the module already carries
    one for the same defect class.
  - **Arguing a control's justification instead of measuring it.** Both sentences I argued were
    false and the arm was load-bearing for a third reason entirely.

- **Next action: CS-487**, which is the cheapest live route in the tree - three lines, no
  test-side line, and it needs no width entry at all. Then **CS-478**, then **CS-471** (tier 1,
  privacy-adjacent; `test_the_entry_points_still_bind_the_raw_body_where_a_renderer_can_read_it`
  PINS the exposure and FAILS when the item closes - widen the control and delete that test, do
  not delete it alone). Then CS-488, CS-477, CS-479, CS-470/472/473/474. **CS-484 is still cheap,
  still blocks nothing, and will bite again on the next push.** **CS-486 still needs an OPERATOR
  DECISION rather than work.**

## Session 27 - relocated from WAKEUP_NOTES.md

Relocated 2026-08-22 (session 29) because a fourth session entry landed and that file holds the last two to three at full fidelity. Relocated, never deleted.

## Session 27 - 2026-08-21 - CS-492 rounds seven, eight and nine; the ROOT CAUSE is finally located and it is a CONTRACT, not a bug

- **Shipped: NOTHING CLOSED. Again, and it is the result rather than a shortfall.** Round six
  was graded and REFUTED on both lenses. Round seven was built, graded, REFUTED on both.
  Round eight was built, graded, REFUTED on both. Round nine was dispatched against the
  located root cause and is UNGRADED at session end. Nine rounds, nine refutations, every
  one on a real defect. The only thing committed this session is a documentation relocate
  pass; rounds seven and eight remain UNCOMMITTED in their worktrees by operator decision,
  so that nothing unproven enters main.

- **THE HEADLINE, AND IT IS THE FIRST TIME THIS ITEM HAS HAD ONE SENTENCE: THE EVIDENCE
  RULE IS VALUE-AGNOSTIC.** It asks WHETHER a bare name is bound at module scope and never
  WHAT IT IS BOUND TO. So `stat = "chunks"` certifies the bare name `stat` as a filesystem
  primitive, and a class with `def get(self, stat): return stat` beside it manufactures
  EIGHT declarations on the real `tests/save/test_phase4_gate.py`, whose entire reach is
  `dict.get(...)`. The round-eight builder stated the contract explicitly - "the evidence
  set is value-agnostic by contract" - so this is a chosen design, not an oversight, which
  is why four rounds of widening never touched it.

- **THE MEASUREMENT THAT ORGANISES EVERYTHING ELSE, taken by the merger across all three
  builds.** `+` means eight manufactured declarations on the real `test_phase4_gate.py`:

  | payload | round 6 | round 7 | round 8 |
  |---|---|---|---|
  | `get(self, stat): return stat` alone | + | clean | clean |
  | module-scope binder alone | clean | clean | clean |
  | `stat = "chunks"` + that method | + | **+** | **+** |
  | `for stat in (...)` + that method | + | clean | **+** |
  | `with ... as stat` + that method | + | clean | **+** |
  | `except ... as stat` + that method | + | clean | **+** |

  **The `Assign` row is the one that matters: it predates round eight and was never
  closed.** Round six's defect has been DISPLACED TWICE AND REPAIRED ZERO TIMES. Rounds
  seven and eight each fixed the spelling a refuter happened to name.

- **NO BUILD IS STRICTLY BEST, and that is why neither was merged.** Round seven has the
  cleanest false-flag direction and three silent module-scope escapes plus three ungraded
  mutation survivors. Round eight fixed all three escapes, added 45 controls with ZERO
  removed and no weakening anywhere, and regressed three false-flag rows. Round eight is
  the better base and is still not shippable.

- **TWO REACH ESCAPES IN ROUND EIGHT ARE CONFIRMED UNGRADED, one of them by the merger at
  function granularity.** Reverting the subscript-key arm so the PEP 562 sentinel cannot
  answer for it turns `FLAGGED: ['_reads_the_served_entry']` into "no function here touches
  a library primitive, so the guard is vacuous" while the whole suite stays at 2235 passed,
  52 skipped, exit 0. The second is the serves-loop evidence site, pinned by nothing.

- **A COARSE PROBE GAVE THE MERGER A WRONG ANSWER FIRST, and the correction is the method
  point.** Asking the PACKAGE WALK whether the module is flagged said FLAGGED under both
  pristine and mutant, because the planted `__getattr__` itself reaches. Only a
  FUNCTION-GRANULARITY probe - calling `_assert_library_reach_is_declared` directly and
  reading `caught.args[0]` - separated them. **Grade a claim at the granularity the claim
  is made at.**

- **THE CEILING IS AN UNGRADEABLE NUMBER, WHICH IS THE DEFECT ROUND EIGHT CLAIMED TO
  REMOVE.** It deleted the old round budget saying a number nothing can grade "is an arm
  already deleted that does not know it", and replaced it with a `RuntimeError` ceiling
  having the identical property: everything from `len//2 + 2` to `2*len + 2` passes the
  whole suite. Measured over all 86 tracked `.py` files, the worst real module uses ONE
  round against a ceiling of six. **The repair relocated the ungradeable number rather than
  removing it.** The loud-failure arm itself is legitimate and must be kept - round eight's
  first battery HUNG before it existed.

- **`_serving_names` IS DEAD CODE AND ITS PROSE DEFENDS ITSELF WITH CONTROLS THAT DO NOT
  EXIST.** Defined, never called; deleting it changes zero verdicts. `_serving_vocabulary`'s
  docstring keeps it "because the controls that grade the serving set ask about names" and
  no such control exists, and `test_reach_guard.py:947` attributes a real control's bound to
  an inner fixpoint in a function that runs no loop and is never called. **That is this
  project's own "a mutant that never applied looks green" trap, written into a comment as
  evidence.**

- **FOURTEEN OF NINETEEN `_MUST_NOT_FLAG` ENTRIES HAVE UNVERIFIABLE PROVENANCE.** The
  standing claim says each was measured flagged by the build immediately before the bound
  that repairs it. Only five can be checked; the other fourteen were born whole inside
  `6f7aa3b`, and at `752d9c7` none of the machinery that could flag them exists. This is the
  same class the two removed entries were removed for. **Mitigating and measured:** reverting
  the hand-back narrowing fires 11 of the 19, so most do grade the narrowing they name - the
  defect is the SENTENCE, not the coverage.

- **THE SETTLED SEED RULE IS GRADED NOWHERE.** `serving = _LIBRARY_PRIMITIVES | attributes`
  survives all of `tests/save`; the `| bound` variant is killed, so one half of the rule is
  pinned and the other is not. A separating control was constructed and handed to round nine.

- **BATTERY SIZE IS A MEASURED FAILURE MODE, not a matter of taste.** Round eight ran 14
  mutants against 1368 changed lines and reported 13 killed, 1 survived. A grading pass that
  derived its targets from the diff ran 41 and found SEVEN survivors, two of them real reach
  escapes. **Size the battery to the change, never to the previous list.**

- **ROUND EIGHT BROKE THE TDD ORDER AND DISCLOSED IT UNPROMPTED** - implementation before
  controls, then controls verified red afterwards. That is exactly the provenance that
  produced the fourteen unverifiable entries. The disclosure was worth more than the
  deviation cost; round nine's brief requires the build each control was measured red
  against to be named in the report.

- **Failed paths, so they are not retried:** deleting the `def`/`class` admission from
  `_value_bound_names` to fix the false-flag class - it works and turns
  `a-hold-and-serve-chain-two-rounds-deep` RED at `2 failed, 1179 passed`, because
  `_HOLDER.second = _serves_the_first` names a module-scope `def` that legitimately serves;
  and splitting locators from raw vocabulary to carry the evidence rule, which the round-eight
  builder measured broken by `def resolve(): return locate.resolve_save_root`, a genuine
  server spelled with a vocabulary word. **Both counter-examples must be satisfied by any
  value-aware fix.**

- **Documentation: a relocate pass, COMMITTED.** `ROADMAP.md` had NINE BYTES of margin against
  its 61440 budget. CS-421's four fences and the NOTE bodies of CS-468 and CS-456 moved to
  `docs/history_notes.md`, byte-identical, leaving acceptance sentences and emphatic pointers;
  margin is now 2647 bytes. The relocation script REFUSES on ambiguity and that caught a real
  case - CS-448 already had a detail block, so its ROADMAP NOTE is a second body and merging
  the two needs judgement rather than a script. It was left alone.

- **Suite, no game, re-measured from scratch at session start and unchanged from session 26:**
  `tests` 2190 passed / 52 skipped / exit 0. Round seven measured 2216/52/0, round eight
  2235/52/0, both verified by the merger independently rather than taken from the builder.
  ruff 0.15.12 check and format clean, mypy clean 86 and 28, drift guard CLEAN 9/9, doc budget
  PASS measured 16, precommit gate PASS non-vacuously via `--files`.

- **A doc-topology contradiction worth an operator ruling:** `docs/history_notes.md` opens
  with "This file holds NOTHING current. Nothing in it may be cited as the present state of
  the project", and is already the home of CS-492's, CS-484's, CS-421's and now CS-468's and
  CS-456's LIVE instructions, which `ROADMAP.md` points at with "MUST BE READ BEFORE TAKING
  THIS ITEM". The file is doing two contradictory jobs. Same shape as the `WAKEUP_NOTES.md`
  contradiction ruled on in session 26.

- **Forward risk, structural rather than a defect:** `tests/save/test_reach_guard.py` is
  182026 bytes against the 262144 cap, having grown about 21 KB in round seven and 17 KB in
  round eight. CS-495 already settled the answer when it arrives - relocate, never raise the
  number, because the cap's stated premise is that every hand-authored file sits far below it.

- **Next action: GRADE ROUND NINE, on both lenses at once.** Its base is `6f7aa3b` plus round
  eight's two files, NOT HEAD - assert `git hash-object tests/save/reach_guard.py` is
  `9c16958af3168e19005ab1c257b529f399d2fdfa` before measuring anything. The false-flag lens
  owns the six-row table above; the control lens owns battery size, the ceiling constant, the
  standing claim and the seed rule. If round nine comes back clean, CS-492 closes on its
  acceptance; if it does not, the open question is no longer which spelling escaped but
  whether a name-keyed guard can satisfy this acceptance at all - CS-491's own note warned
  "do not close this by widening the name list alone", and nine rounds have now tested that
  warning to destruction.

## CS-823 - detail

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Filed by the FOURTH CS-703 adversary and re-derived by the merger with real commits. CS-819
established that a hook must PROVE its checking program ran. That principle was applied to
`.githooks/commit-msg`, whose program arrives by heredoc. **THE SIBLING SITE WAS LEFT OPEN, and the
commit-msg comment names it in passing without closing it.**

`.githooks/pre-commit` tests only that the gate file EXISTS and then runs it. There is no
proof-of-execution. A truncated or empty `tools/precommit_gate.py` in the WORKING TREE therefore
makes the hook report success.

**MEASURED, with real commits staging a forbidden byte, gate truncated in the working tree only:**

| gate state | exit | HEAD moved | hook stderr |
|---|---|---|---|
| intact (control) | 1 | no | 561 bytes |
| truncated to 2368 lines | 0 | **YES** | **0 bytes** |
| truncated to 1 line | 0 | **YES** | **0 bytes** |
| empty, 0 bytes | 0 | **YES** | **0 bytes** |

**IT IS CLOSE TO A COIN FLIP RATHER THAN A CORNER CASE.** Compiling every line-boundary prefix of the
tracked 2395-line gate, **1019 of 2395 truncation points are syntactically valid**. Line 2369 is the
`if __name__ == "__main__":` guard, so ANY truncation before it that compiles defines everything and
executes nothing - python exits 0 and the hook reads that as a pass.

**THE INDEX IS NO PROTECTION, and this is the part that makes it more than a curiosity.** The hook
loads the gate from the WORKING TREE while the gate reads the files under test from the INDEX. A
correct committed copy does not help; measured with index 99155 bytes against working tree 97982
during the escape.

**THE DESIGNED FIX, ready to build and NOT built here.** The gate already writes
`precommit_gate: PASS - ...` to STDOUT and its BLOCKED banner to STDERR - measured. So the hook can
capture stdout and, on a ZERO exit, require that banner; a gate that never ran yields exit 0 with
empty stdout and is refused. This needs NO change to `tools/precommit_gate.py`, which is separately
frozen, and it mirrors CS-819 exactly. The cost is a coupling between the hook and one line of the
gate's output format, which a contract test should pin from both sides the way CS-819's
sentinel-agreement arm does.

**`.githooks/pre-commit` IS FROZEN. This needs its own operator grant and its own adjudication.** It
was explicitly OUT of both the CS-703 and CS-819 grants, and the operator decided on 2026-08-22 to
FILE it rather than widen a third time in the same session.

### Archived 2026-08-22 from `WAKEUP_NOTES.md` - session 30 at full fidelity

Aged out when session 33 landed and `WAKEUP_NOTES.md` keeps only the last three sessions.
**Nothing here is current.**

## Session 30 - 2026-08-22 - CS-806 and CS-442 both CLOSE; each was larger than filed, and each closed an unimplemented clause rather than the typo it was reported as

- **Shipped: CS-806 and CS-442, both CLOSED, both tier 1, both pushed with tier1 CI SUCCESS
  READ rather than predicted.** `6e37a11` and `ae25547`. This ends three consecutive sessions
  that closed nothing. Detail in `docs/LEDGER.md`, not here.

- **BOTH ITEMS WERE BIGGER THAN THEIR FILING, AND IN THE SAME WAY: a rule was already written
  down and simply never implemented.** That is worth carrying forward as a pattern rather than
  as two anecdotes. CS-806 was filed as a docs typo; `BOOTSTRAP.md` section 2.5 has required
  since the FIRST COMMIT that `verify_env` assert the RESOLVED interpreter can import pytest and
  ruff and HARD-fail if it cannot, and nothing did. CS-442 was filed on one dead citation; the
  item was that NOTHING IN THE REPOSITORY READ `docs/` at all.

- **CS-806's detail block was SUPERSEDED and the ledger says so.** It told the closer to "decide
  whether that contract is the right one" - but the contract had already been decided in
  `BOOTSTRAP.md` 2.5 before any code existed, so it was not a live design question. Both detail
  blocks now carry a CLOSED marker in `docs/history_notes.md` so neither reads as a live
  instruction again.

- **CS-442's population is EIGHT, not the recorded seven, and the eighth is the shape the item
  itself predicted would be missed.** `test_the_header_scan_advertises_no_bound_it_cannot_enforce`
  is cited by the CS-436 entry BARE, with no path, so a `path::name` scanner is structurally
  blind to it. Its target is not an inference: `ee36d0d`, the CS-436 commit, added it alongside
  the live sibling the same Verification field cites. The "seven is a FLOOR" caveat is discharged.

- **A NINTH CANDIDATE WAS REJECTED, and the near-miss is the lesson.**
  `clockspeed/save/objects.py::_BYTE_ORDER_CANNOT_SEPARATE_VALUES` reads dead to any resolver
  that looks for `def` alone, and is a live module-level CONSTANT. It was briefly counted as an
  eighth dead citation off a TRUNCATED `grep` whose first ten hits were all worktree copies.
  Checking the tracked file directly is what reversed it. Same artifact class the item already
  recorded on the `file:line` arm, arriving on the other one.

- **A TRAP FOUND THIS SESSION THAT WAS RECORDED NOWHERE: a citation can assert an ABSENCE.** The
  CS-411 correction record cites a dead name ON PURPOSE - `grep -c` returning 0 IS its evidence -
  so a checker that reddens on every dead name reddens on a record doing exactly the right thing.
  That is the `DELIBERATE` disposition in `tests/test_docs_citations.py` and it is load-bearing.

- **Decisions: no ADR. Two dispositions recorded that must not be re-opened as questions.**
  CS-442's class-3 citation gets NO TARGET, because CS-441 records 26 of 46 spliced shapes still
  escaping - assigning one would launder an aspirational claim into a verified pointer. And
  `docs/history_notes.md` is deliberately NOT guarded, because its detail blocks QUOTE dead names
  while discussing them; that is CS-809, not an oversight.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** The opposite - `BOOTSTRAP.md` 2.5 was
  RIGHT and the code was behind it. Two tracked docs were corrected against ground truth per
  CLAUDE.md section 8: `docs/OPERATIONS.md` claimed "`py -3` is equivalent on this machine",
  which was false and contradicted 2.5; and CS-806's own detail block, above.

- **Failed paths, so they are not retried:** a naive `path::name` census that resolves only `def`
  manufactures a false finding on a live constant. A `file:line` arm that judges an unqualified
  basename manufactures six. Neither is a checker bug to fix later - both are DECLINED-and-printed
  by design now. Also: the harness bash heredoc ate backslash escapes FOUR separate times this
  session, silently corrupting patch scripts; the working answer is the Write tool, every time.

- **In flight: NOTHING.** Working tree clean, nothing unpushed, both CI runs green. The four
  pre-existing worktrees (CS-492 rounds seven to nine and the two-site spike) and branch
  `cs807-attribute-half` are UNTOUCHED and still unmerged.

- **Next action: CS-702, but it is BLOCKED ON AN OPERATOR GRANT and must not be started without
  one** - `.githooks/commit-msg` is frozen. If the grant is not forthcoming, take CS-809 or
  CS-810, which are CS-442's residuals and need no grant.

### Archived 2026-08-22 from `WAKEUP_NOTES.md` - session 29 at full fidelity

Aged out when session 32 landed and `WAKEUP_NOTES.md` keeps only the last three sessions.
**Nothing here is current.**

## Session 29 - 2026-08-22 - CS-807's sweep is TAKEN and sizes the item at SIX; an attribute-half repair was built and REFUTED by three independent lenses

- **Shipped: NOTHING CLOSED. Third session running.** CS-807 stays OPEN, CS-492 was not
  touched, and CS-808 was FILED. Two commits, `77336e5` and `6547f9f`, both DOCUMENTATION
  ONLY - zero `.py` files were touched in `main`. `docs/LEDGER.md` carries a NON-CLOSURE
  record and says so in its heading.

- **THE SWEEP IS TAKEN, and it was the right first action because it changed the item's
  size.** CS-807's detail block named it the cheapest next step and recorded the answer as
  unmeasured. The answer is **SIX false declarations, not four, in TWO modules rather than
  one**: `backing_citations` and `dead_full_citations` in `tests/save/test_absolute_claims.py`
  are the new pair, and **both are HELPERS rather than tests**, so the population is not
  confined to test functions the way the first finding implied. 45 exemptions in 11 modules,
  20 graded entries in 7; the graded channel is CLEAN. No consumer of the guard exists
  outside `tests/save`. **Six is a FLOOR, not a total.** Full tables in
  `docs/history_notes.md` under **CS-807 - detail**.

- **TWO INDEPENDENT METHODS AGREED ON THE SAME SIX and the second never reads a reason
  string** - it takes the call node the guard trips on, resolves the callee one hop, and asks
  whether that target reaches. One phrase match was REJECTED on inspection:
  `test_workdir::test_latest_save_returns_none_when_nothing_resolves` matches "no path at
  all" but genuinely calls the locator.

- **In flight: branch `cs807-attribute-half` at `72f0f2c`, base `77336e5`, REFUTED and NOT
  MERGED.** +242/-25 across three files. The working tree is CLEAN and nothing is unpushed;
  the branch is the only artifact. The four pre-existing worktrees (CS-492 rounds seven to
  nine and the two-site spike) are UNTOUCHED.

- **Failed paths - the whole of the repair attempt, and the framing that produced it.** The
  sweep showed the six splitting by mechanism: four on the bare-name arm already measured
  irreducible, two on the ATTRIBUTE arm where `_callee_resolves` discards a receiver the
  import table resolves without type resolution. **That was reported as the tractable half
  and it is not.** Two narrowings were built and both were refuted, both for reading an
  ABSENCE as evidence of safety - the first that the sibling exported no reach, the second
  that a def's own body names no primitive. **Do not take a third of the same shape without
  an answer to that root cause.**

- **THE GRADING WAS DONE BY THREE AGENTS THAT DID NOT PRODUCE THE BUILD, and all three
  returned REFUTED.** Permissive-failure found seven escapes, each caught on the parent
  commit and silent on the build. Control-validity found the build's anti-vacuity control
  passes with `_assert_library_reach_is_declared` gutted to a bare `return`, with ZERO unique
  detection against a 16-mutant battery. Claim-accuracy found `_module_handles`' docstring
  stating the polarity of the REFUTED first spike, and a FOURTH reach-computation site.

- **Surprises: NO SPIKE CONTRADICTED `BOOTSTRAP.md` this session.** But two measured facts
  contradicted a TRACKED DOC and the doc was corrected per CLAUDE.md section 8: ROADMAP's
  CS-807 acceptance said "the four exemptions in `test_oracle_citations`" and the sweep says
  six across two modules; and this session's own claim that the attribute half was tractable
  was refuted by its own grading and is now fenced in the detail block.

- **Two defects worth carrying forward whatever happens to the direction.** The exoneration
  was keyed on a bare receiver name with NO SCOPE CHECK, so a PARAMETER spelled like a module
  handle silences `Path.resolve()` on a real account directory - and
  `tests/save/test_absolute_claims.py:192` already binds `citations` as a handle, so that is
  a rename away rather than contrived. And `_module_scope_reaches` asks the same reach
  question as the three sites `grep -n "_calls_any("` finds, so the identical call at module
  scope MANUFACTURED a `<module scope>` declaration on a module reaching nothing - the CS-807
  defect inside the CS-807 repair. **Count the sites from the source, not from that grep.**

- **THE CONTROL LESSON IS THE MOST TRANSFERABLE THING HERE: a control written to defeat
  vacuity was itself vacuous.** It swallowed the guard's own "vacuous" message through an
  `if "vacuous" in said: return` branch and so passed WITHOUT EVER OBSERVING THE GUARD REACH
  A VERDICT. The symmetric instrument it declined to use is
  `assert not _module_reaches(consumer)`, which a gutted guard cannot satisfy and which kills
  two of the surviving mutants. The companion escape control graded as a REAL instrument with
  a clean unique kill, so the pair was half sound.

- **What survived grading, and is reusable.** The two exemption deletions are CORRECT,
  verified by reading `backing_citations`, `dead_full_citations`, `citations.resolve` and
  `prose_paragraphs` end to end rather than by running the guard. No shipped module goes
  silent on the build today; every escape found is prospective.

- **Decisions: no ADR was recorded.** The fences are in `docs/history_notes.md` under
  **CS-807 - detail** and in the ledger entry.

- **Next action: CS-442 or CS-806, NOT a third narrowing of the attribute arm.** CS-807 has
  now consumed a sweep and two refuted builds, and the direction needs an operator decision
  about which side its acceptance buys before more work goes into it.

## Relocated from WAKEUP_NOTES.md on 2026-08-23 (session 34)

## Session 31 - 2026-08-22 - THREE items close and SIX are filed; every first build was refuted, and the largest finding is that a substituted interpreter disarms every tier-0 gate

- **Shipped: CS-702, CS-809 and CS-810 CLOSED. Filed CS-703, CS-704, CS-811, CS-812, CS-813,
  CS-814.** Six commits, `f348d85..bfa64e7`. Suite 2393 passed, 3 skipped, exit 0 on the final
  bytes. Detail in `docs/LEDGER.md`, not here. **SIX NEW ITEMS CAME OUT OF TWO, and four of the six
  are defects in things that were already green and already reported done.**

- **EVERY FIRST BUILD THIS SESSION WAS REFUTED, and so was every second build of CS-702.** Not one
  refutation came from reading the code; every one came from an agent RUNNING it - real commits,
  proven-landed mutants, planted citations. Two builders reported green suites over live
  fail-opens. **The transferable form: a suite is evidence about the shapes it enumerates and about
  nothing else.** CS-702's suite was green through three fail-opens because every arm drove ONE
  commit path and one arm ASSERTED AN ESCAPE AS INTENDED BEHAVIOUR. CS-809's carrier check was
  blind to three of the four citation shapes its own module judges.

- **THE BIGGEST FINDING IS CS-703 AND IT IS NOT WHAT ANYONE WAS LOOKING FOR.** All three hooks
  share a byte-identical `cs_probe` that runs the candidate interpreter with `-c` and judges ONLY
  the exit code, so `true`, `:` and `env` all pass it. The heredoc is then handed to that program,
  which ignores it and exits 0, and the hook reports success. **`CLOCKSPEED_PYTHON=true` therefore
  disarms the character-set gate, the secret scan, the commit-msg checks and the whole-suite
  pre-push run, all at once.** Measured with a real commit that landed a forbidden trailer. This is
  the CS-806 shape a THIRD time - a rule already decided, never carried to where it also applies.

- **CS-702 CLOSED ON THE MATCHER ALONE, BY OPERATOR DECISION, AND THE PRE-FILTER REWRITE WAS
  DELIBERATELY NOT SHIPPED.** That is a result, not an unfinished attempt. The rewrite closed four
  escapes and was refuted anyway: reading the whole buffer is sound for a SCAN and unsound for a
  SELECTION, so it chose a different subject line from the one git stores, and it rejected
  `git commit --verbose` whenever the staged diff carried a byte above 0x7E - which blocks
  precisely the work of fixing such a byte. Its measurements are preserved against CS-813.

- **Decisions: no ADR. Four that must not be reopened as questions.** The trailer predicate is
  NAME-FREE and deliberately wider than the `docs/GATED.md` operator decision - adjudicated on the
  CS-209 precedent that narrowing a blocklist by default was DENIED BY MEASUREMENT. **A FENCE IS
  NOT A SHIELD** - git parses a fenced block whole when a generated trailer shares it, so skipping
  fences fails OPEN; indentation is the shield. `WAKEUP_NOTES.md` is now GUARDED rather than
  recorded unguarded, which is what makes CS-809's "stays the only one" clause literally true.
  Disposition SITES are pinned by COUNT, never by line number.

- **Surprises: nothing contradicted `BOOTSTRAP.md`. Two things contradicted an adjudicator and one
  contradicted a tracked file I wrote.** Ground truth won each time per CLAUDE.md section 8. The
  widened grant required reading `commit.cleanup` to license narrowing; measurement says a
  command-line `--cleanup=` outranks config and is INVISIBLE, so no observable can license it -
  worse, config `verbatim` plus flag `strip` makes the hook actively wrong in a direction it cannot
  detect. And **`docs/LEDGER.md` carried a wrong number I put there** - "215-character stored
  subject" where the measurement is 200 - corrected by a later record, never by a rewrite.

- **Failed paths, so they are not retried.** A resolver that inherits the last full citation seen
  manufactures 14 false findings. A config-driven cleanup prediction leaves 8 fail-open cells.
  `commit.verbose` as a truncation proxy reads `true` under `--no-verbose`. And a repair dispatched
  with worktree ISOLATION is pinned to a NEW worktree and cannot reach the one holding the work -
  it correctly refused rather than repairing the wrong copy.

- **A TRIPWIRE THE NEXT SESSION WILL HIT AND WILL NOT SEE COMING, and this bullet is deliberately
  written without spelling the name it is about.** `WAKEUP_NOTES.md` is GUARDED now, and
  `tests/test_docs_citations.py` carries a RENAMED disposition keyed to this file that pins its
  dead bare name at EXACTLY ONE site. Read the key out of the table rather than from here. That one
  site lives inside SESSION 30's entry below. **Archiving session 30 drops the count to zero and
  turns the suite RED on a correct doc-hygiene move.** When session 30 ages out, update that
  disposition in the SAME commit. Writing the name into a new session note also breaks it, by
  taking the count to two - which is how this bullet was first drafted, and the guard caught it.

- **OPERATOR ACTION OUTSTANDING, unrelated to the code: rotate the GitHub personal access token.**
  Five live credentials sit in the environment every git hook inherits, and an agent dumped that
  environment into a transcript during a probe. Nothing is committed and no git config key carries
  them, both checked. Filed as CS-814.

- **In flight: NOTHING from this session.** Working tree clean. The four pre-existing worktrees
  (CS-492 rounds seven to nine and the two-site spike) and branch `cs807-attribute-half` are
  UNTOUCHED and still unmerged, exactly as session 30 left them.

- **Next action: CS-703.** It needs a frozen-file grant for all three hooks, and it is tier 1 with
  a blast radius wider than the item that found it.
