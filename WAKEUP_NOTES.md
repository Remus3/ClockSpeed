# Wakeup notes

**The last two to three sessions at full fidelity, newest first. Nothing older.** When a
fourth session lands, the oldest entry is moved to `docs/history_notes.md` - relocated,
never deleted.

This file is read at session start, alongside `CLAUDE.md`, the memory index, `ROADMAP.md`
and `docs/ARCHITECTURE.md`. It is refreshed by the `/done` ritual at the end of every
session, not written incrementally during one.

It holds what a fresh session cannot recover from the code and the git log: what was
actually in flight, what was tried and abandoned, and what the very next action is. It
does not hold per-item completion records - those are ledger entries and belong in
`docs/LEDGER.md`.

## Entry format

```
## Session <n> - <YYYY-MM-DD> - <one-line focus>

- Shipped: item IDs closed this session. Detail in docs/LEDGER.md, not here.
- In flight: what was left mid-work, where it stands, and what it is blocked behind.
- Decisions: ADRs recorded this session, by id. Detail in docs/adr/.
- Surprises: anything that contradicted a spec, and which file was updated as a result.
- Failed paths: what was tried and abandoned, and why - so it is not retried next session.
- Next action: the single first thing the next session does.
```

Keep every entry to that shape. If an item needs a paragraph, it needs its own file and
the line becomes a pointer.

---

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
