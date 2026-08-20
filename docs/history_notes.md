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
| Blocked outside the repo | `docs/GATED.md` |
| Module map and seams | `docs/ARCHITECTURE.md` |
| Commands and runbooks | `docs/OPERATIONS.md` |

---

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

## CS-473 - detail

Relocated from `ROADMAP.md` on 2026-08-19 (session 21) under its soft doc budget, whole and unedited. The item itself stays OPEN in `ROADMAP.md`; this is its NOTE.

NOTE: filed 2026-08-17 (session 16). Measured, not inferred: `FENCED_MODULES` is a hand-written 2-tuple that excludes `test_properties.py`, and a claim carrying eight unbounded quantifiers was spliced into that module with both fence modules staying green at 25 passed, then restored from a byte copy. So ADR 0008 compliance in the project's largest test module is an author obligation with no mechanism behind it. The emptiness half is the same shape one file along: the two guards between them now catch a `pass` body, a docstring-only body and an `assert True` on a literal, and three shapes remain - and a body that is only `pytest.skip()` is the dangerous one, because it is camouflaged among the legitimate skips of a library-backed module. **ENLARGED AGAIN 2026-08-18 (session 20):** CS-480 took that same module from 70 unbacked absolute sentences to 113, measured with this repo's own `unbacked_absolutes` over both trees. No sample repair was made: a partial hand repair with no mechanism is the register of pardons that tool's own docstring forbids. **SURFACE ENLARGED 2026-08-18 (session 18), measured rather than estimated:** CS-476 shipped `tests/save/test_byte_order_status.py`, a new module that is NOT in `FENCED_MODULES`, so it ships unfenced by default - which is this item's own claim reproducing itself one module along. Running the fence's contract 1 against it via `unbacked_absolutes` reports **24** unbacked quantified sentences, spread across the docstring, comment and assert-message channels. That figure is a measurement of that module on that date and is NOT a budget - re-run the scan rather than carrying it forward. Bringing the module inside the fence is a prose rewrite, which is why it was recorded here instead of being folded into CS-476. **ENLARGED AGAIN 2026-08-18 (session 21):** CS-482 added 9 unbacked quantified sentences across the three modules it touched, measured with this repo's own `unbacked_absolutes` over both trees - `clockspeed/save/objects.py` 216 to 219, `tests/save/synthetic.py` 113 to 115, `tests/save/test_objects.py` 179 to 183. Two of the three in `objects.py` are statements of what is NOT measured, which is the tool's known coarseness rather than an overclaim, and that is a reason to fix the tool and not a reason to exempt the sentences. One sentence WAS backed by citing a resolving test rather than by rewording it. No sample repair was made, for the reason recorded above.

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


## CS-455 - detail

Relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted. The item
itself stays OPEN in `ROADMAP.md`.

filed 2026-08-16 (session 13) by the CS-421 builder as a MEASURED residual of its own work, and it is this project's own circularity one layer along. Measured with byte-verified mutants: replacing the whole fixed-width decode with a constant 1 leaves the two new byte-order oracles GREEN, because a small positive constant carries a zero high byte exactly as a real small value does. **THE ORIGINAL NOTE THEN SAID "constant 0 and a large constant both go red, so the blind spot is narrow" AND THAT WAS MEASURED FALSE 2026-08-16 (session 14), one process per constant so no memoised sweep carries a result forward: 0 red, 1 / 255 / 1000 / 65535 / 1000000 ALL GREEN, 16777216 red.** The accepting band is every constant with a zero high byte and a nonzero low byte - not narrow, and the acceptance above is widened accordingly. **THE RANGE FRAMING THAT USED TO SIT HERE - "roughly 1 to 16777215" - WAS MEASURED FALSE 2026-08-17 (session 16), one process per constant: 256 sits inside that range and goes RED, because its low byte is zero.** The two-part rule is the correct statement and the range was an approximation of it that is wrong at every multiple of 256. Deleted rather than re-fitted; do not write a range here. Do not re-derive this by looping mutants inside one process; the sweep is memoised and every later iteration silently reports the first mutant's verdict. **THE FIRST DRAFT OF THE DOCSTRING ATTRIBUTED THIS GAP TO THE ROTATION CONTROL AND THAT WAS FALSE** - under the constant-1 mutant 8 tests red, 7 of them synthetic-fixture tests and the eighth the nested gate that runs them, while `tests/save/test_properties.py::test_the_decode_collapses_when_the_payload_start_is_rotated` stayed green. It could not have done otherwise: it perturbs the WALK, and a fabricated value does not move the walk. So on the real library nothing catches this; only fixtures packed from the same belief the reader unpacks with do, which is CS-421's stated circularity reappearing. Do NOT close this with a synthetic fixture.


## CS-458 - detail

Relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted. The item
itself stays OPEN in `ROADMAP.md`.

filed 2026-08-16 (session 14) by the CS-422 adversary and confirmed by the merger from source, no mutation needed. `tests/save/test_properties.py` builds its `shipped` set as `_TAG_EXTRA_STRINGS | _FIXED_WIDTH_VALUES | {GUID_BYTES, _SOFT_OBJECT_TAIL_BYTES}` and `CURSOR_WIDTHS | EXTENT_WIDTHS` equals that same union, so `ungoverned` and `phantom` are empty for any edit to either TABLE. **THAT PHRASING USED TO READ "structurally empty set differences" AND IT OVERSTATES, MEASURED 2026-08-17 (session 16):** the test transcribes `GUID_BYTES` and `_SOFT_OBJECT_TAIL_BYTES` as its own literals while `objects.py` spells them inline, so the two literals do NOT cancel and renaming `GUID_BYTES` in `CURSOR_WIDTHS` alone turns `ungoverned` RED. The acceptance below is unaffected - the table half is what needs independent sources - but the test was kept and re-docstringed rather than deleted, because deleting it would have removed a live transcription check. Five cursor-advancing widths in the same walk are covered by nothing: `_TAG_INDEX_FIELD_BYTES` (`clockspeed/save/objects.py:2608`), `INT32_SIZE`, `UTF16_CHAR_SIZE`, the guid-flag byte literal and the `BoolProperty` in-tag byte literal. **THE ASYMMETRY IS WHAT REMOVES THE "PRIVATE CONSTANTS ARE OUT OF SCOPE" DEFENCE:** `_SOFT_OBJECT_TAIL_BYTES` is private and IS classified while `_TAG_INDEX_FIELD_BYTES` is private and is not, and nothing distinguishes them but who typed which literal. Mis-stating `_TAG_INDEX_FIELD_BYTES` reddens two census tests on their BASELINE with messages naming an innocent width, which is collateral collapse rather than grading.


## CS-477 - detail

Relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`.

**MEASURED, all at `tests/save` 1040 passed, exit 0.** (1) `_DISPATCH_SITES` in `tests/save/test_byte_order_status.py` is a hand-written 2-tuple; deleting one entry drops every oracle that entry owns and costs the probe NOTHING, because `_coarseness_observation` reaches its dispatch directly rather than through the tuple - so two line deletions inside that one module restore the zero-coarseness-call state the second refutation closed. (2) An ordinary extract-method refactor - moving `_tally_mantissa_coarseness` behind a helper called from the census - takes the call out of the scanned body while the oracle still runs, and EVERY control passes, which is stealthier than an alias because the neutering patch still bites. A rename dropping the `_tally_` prefix IS caught, but only by `monkeypatch.setattr` raising on a missing attribute, not by the derivation. (3) `_PROBE_VALUE_PAIRS` is graded by nothing: emptying it leaves the module green at 8 passed, and 3 of its 5 shapes cannot move anything under any combination, because both dispatch sites key on IntProperty and FloatProperty alone.


## CS-490 - detail

Relocated from `ROADMAP.md` 2026-08-19 (session 23) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-19 (session 23) as CS-487's measured residual, by two independent refutation
passes and re-measured by the merger on the tree carrying CS-487's two arms. **IT IS NOT
CS-488.** CS-488's acceptance is scoped to a WIDTH-TABLE entry and neither route here touches a
width table, so satisfying CS-488 need not red either; an earlier draft of CS-487's control
handed this residual to CS-488 and a refutation pass measured that assignment wrong.

TWO ROUTES, BOTH TAKEN ALL THE WAY TO GREEN RATHER THAN LEFT AT THE FIRST RED, both with
`tests/save` green on a machine with no game. SEVEN EDITED LINES - five in
`clockspeed/save/objects.py`, two in `tests/save/test_properties.py` - by taking a word ALREADY
in `MEASURED_VALUE_TYPES`, severing it from the shape table that reads it, re-declaring it
measured, widening both tag-carried sites and writing the status entry, then moving its fixture
tag and expected value. And EIGHT EDITED LINES for a word the module has never named. A line
count is EDITED lines, added and modified alike - counting only additions understated one route
by two.

THE PRICE AND THE ROUTES ARE OWNED BY
`tests/save/test_byte_order_status.py::test_no_word_the_exemption_admits_is_one_the_module_declines_to_measure`.
Read that docstring before taking this item and DO NOT RESTATE ITS COUNTS here or anywhere -
two counts in the first draft of this work were wrong precisely because they were written
twice.

NOTE THE HARD PART BEFORE STARTING. Every control on this exemption is keyed on the module
CONTRADICTING itself - a status against a region the module records as unclaimed, a tag-carried
word the module also reads out of the payload, a decoded word the measured set declines to
name. A module edited to claim a type in every table at once contradicts itself nowhere, and no
library-free check can tell a false width or a false shape from a true one, which is CS-426's
gap. So the acceptance cannot rest on another contradiction; it needs either a fixture that
costs more than one `struct.pack` call, or evidence from outside this module's own tables.


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


## CS-488 - detail

Relocated from `ROADMAP.md` 2026-08-19 (session 22) for budget, not deleted. The item
itself stays OPEN in `ROADMAP.md`.

filed 2026-08-19 (session 22) by TWO independent refutation passes on CS-481 and re-measured by the merger. CS-481's contradiction arm reads `UNMEASURED_PAYLOAD_REGIONS`, so a word the module never mentions has nothing to intersect with. SIX LINES - three in `objects.py` (width entry, shipping grounds, evidence entry, with the region entry deleted where one exists) and three in `tests/save/test_properties.py` (the measured-set transcription, a `_scalar_tag` fixture line, an expected-value line) - ship `vacuous_one_byte` for an EIGHT-byte type with `tests/save` GREEN with no game. WHAT CS-481 DID CLOSE IS WORD-AGNOSTIC ON THE OTHER LINE and that is measured: a never-named type declared one byte wide and severed from `MEASURED_VALUE_TYPES` reds the walk control and nothing else. NOTE THE HARD PART BEFORE STARTING: no library-free check can tell a false width from a true one - that is CS-426's gap - so the acceptance has to rest on the module's own coherence or on a fixture that costs more than a `struct.pack` call, not on the width being right.


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

**THIS IS THE PHASE-4 DEPTH GATE.** Filed 2026-08-15 by the operator ruling recorded in CS-400: CS-400's clause 1 closes when this closes, and phase 5 does not open before it. It is the natural successor to CS-407, which closed the SKELETON. NOTE THE TWO LAYERS, because they are not the same problem and only the second is what most readers picture. **Layer 1 - the data section is located and walked; what was missing is ATTRIBUTION.** **Layer 2 - the property grammar inside one payload**, then value decoding per type. Prior knowledge of how Unreal serializes properties is a HYPOTHESIS GENERATOR and never evidence here; the phase's stated common-mode risk is a corpus that only ever agrees with whoever wrote it, and for layer 1 the corpus can say nothing at all because no fixture builds a data section. Record the grammar as DATA, per CS-412 - a partial recorded as an adjective is not resumable. **The session-6 STATUS, which recorded the attribution half being MET and the four independent oracles that proved the payload pairing, is relocated to `docs/history_notes.md` along with this entry's own correction record.** **STATUS 2026-08-15 (session 7): THE DECODE LANDED AND THIS STILL DOES NOT CLOSE.** `read_properties` now returns real property values across the local library, every unmeasured type flagged rather than guessed, and a hand-authored synthetic payload fixture means the decoder is covered on a machine with no game installed. The save-60 half of this item has MOVED OUT to `docs/GATED.md` CS-G05, because no work inside this repo can close it. **WHY IT STAYS OPEN, ruled by the merger and confirmed by an adjudicator that did not produce the work.** Two independent reasons, both measured. FIRST, THE ACCEPTANCE CLAUSE IS TRIVIALLY SATISFIABLE: "returns at least one decoded property VALUE off a real building" is a liveness floor, and a decoder that reads ZERO value bytes clears it, because a `BoolProperty`'s value rides in the tag with `size` 0. This project already recorded that a `> 0` liveness control is not a control; an acceptance clause the shipped rotation control is designed to defeat cannot be the thing that closes the item. SECOND, THE EVIDENCE IS UNEVEN AND THE UNEVENNESS FALLS EXACTLY ON WHAT PILLAR 3 NEEDS: a majority of the decoded values are backed by a declared width and nothing else, a check the module ITSELF records as "defensive rather than measured", while byte order and signedness are checked by NOTHING EXECUTABLE - flipping an integer type to big-endian reddens only synthetic-fixture tests whose own fixture packs with the same byte order the reader unpacks with. `IntProperty` and `FloatProperty` are inventory counts and clock speeds, so pillar 3 sits inside exactly that unbacked majority. **CS-421 OWNS THAT SPLIT AND CARRIES THE PER-TYPE FIGURES. They are deliberately not restated here: one measured fact living in two entries is the drift CLAUDE.md section 4 exists to stop, and this entry was doing it.** What is evidenced is "the values were produced and are self-consistent with our own writer". What closing would assert is "correctly decoded". The gap between those sentences is CS-420, CS-421 and CS-422, and those three carry the acceptance criteria that close this properly.

### CS-420 - detail

**The session-9 REOPENED block is relocated to `docs/history_notes.md`** - its F1, F2 and dead-paragraph-citation findings were all fixed in session 10 and re-verified by an adversary that wrote none of the repair, so it is a record rather than a state. **DO NOT HAND-REPAIR THE PROSE AGAIN.** Four rounds, fourteen-plus false sentences, several written by the commit correcting the previous one. ADR 0008 gives the rule and the artifacts now exist to enforce it; what is missing is a MECHANICAL check that a declarative sentence in this module is backed by execution. Build that, or delete the sentences it cannot back. **STATUS 2026-08-16 (session 10): THE FENCE SHIPPED, ROUND FIVE STILL SHIPPED FALSE SENTENCES, AND THE ITEM STAYS OPEN ON THE FENCE'S POROSITY.** F1, F2 and the dead paragraph citation ARE fixed and were re-verified by an adversary that wrote none of the repair. `tests/save/test_absolute_claims.py` now reads prose from docstrings via `ast`, comments via `tokenize` AND assert messages via `ast.Assert.msg`, and requires an unbounded quantifier to name a resolving test; it is proven to fire against the real tree by re-inserting `IT NEVER RAISES`, and gutting it IS visible. What it does NOT do is the acceptance. **MEASURED BY THE ADVERSARY, AND BY THE MERGER INDEPENDENTLY: three genuine ADR-0008 tier-1 universal claims were inserted into the fenced module, byte-verified applied, and the full suite stayed byte-identically green.** 19 of 22 real universal phrasings carry no listed marker - `at no point`, `no other test`, `without exception`, `not a single`, `invariably` and 14 more all return ZERO findings - and TEN prose channels are never read at all: `pytest.skip` reasons, `pytest.fail` messages, an assert message held in a `Name` rather than a literal, PEP-224 attribute docstrings, bare mid-function strings, parametrize ids, `raise AssertionError`, `pytest.raises(match=)`, module-level string constants, and `pytest.mark.skip(reason=)`. That last class is the sharp one: "an assignment is not prose" is what keeps the control corpora inert AND is a universal write-anything channel. **AN ELEVENTH CHANNEL WAS FOUND 2026-08-16 AND IT IS ARGUABLY THE MOST CONSEQUENTIAL OF ALL: A WARNING DETAIL STRING IS A CALL ARGUMENT, AND NO PROSE KIND THE FENCE READS COVERS ONE.** It is not a docstring, not a comment and not an assert message. It is also the sentence SHIPPED TO THE OPERATOR to explain a loss, so it is the highest-consequence prose in the tree and the least guarded. This is not hypothetical: CS-435's first build shipped a false universal in exactly that position - "every index resolving to it is flagged unresolved" - which was false at FOUR measured sites, and the fence flagged none of it because it cannot see the string at all. CS-435's repair built two derived fences for its own module, one deriving every warning detail from the AST and refusing site-quantifiers, the other resolving every sibling symbol the module cites; both derive their population at runtime. **Those two are a WORKED EXAMPLE of what clause (2) of this item's acceptance asks for and are worth reading before the next attempt** - they are also, being in `clockspeed/save/usmap.py`, evidence for the breadth question rather than the depth one. `FENCED_MODULES` is a hand-written 2-tuple whose deletion - removing this item's own subject - leaves the suite green, which is a scope allowlist with the sign flipped. **The overwhelming majority of sentences in the fenced modules carry no marker and are unread by the rule; DERIVE that ratio with the fence module's own `sentence_count` rather than reading a number here.** The figures that used to sit in this sentence had themselves drifted - the item's thesis landing on the item - and the incident is recorded in `docs/history_notes.md` rather than restated. Contract 4's tree scan has NO FLOOR on its reference population and there are ZERO anchored paragraph references in the tree, so it cannot go red on tree content today. **THE ACCEPTANCE TENSION WAS A MISDIAGNOSIS, IS SETTLED, AND DOES NOT REOPEN.** ADR 0008 SCOPE governs BREADTH, this item's acceptance governs DEPTH in the one module named in its own title, that module is already in `FENCED_MODULES`, and the two texts never disagreed. ADR 0008's SCOPE clause is UNAMENDED. Five rounds were spent building against a dilemma that was not there; the adjudication is recorded in `docs/history_notes.md`. **DO NOT hand-repair prose again and DO NOT hand-extend the marker list** - a hand-maintained list is the thing that rots, and that is the failure this artifact was built to stop, re-shipped inside it.

### CS-421 - detail

NOTE: filed 2026-08-15 by the measurement-validity adversary. Its split of the 185382 decoded values: redundancy-oracle-backed by a string's own length prefix - ObjectProperty 52457, ByteProperty 5359, NameProperty 9804, EnumProperty 6245, SoftObjectProperty 116, StrProperty 37 = **74018**; cross-section-backed 26146, a strict SUBSET of the ObjectProperty 52457; and **backed by a declared width and nothing else - IntProperty 75136, FloatProperty 31318, BoolProperty 4077, Int8Property 824, UInt32Property 9 = 111364, which is 60.1 per cent of the total.** The width check carrying that 60.1 per cent is the one the module ITSELF records as "defensive rather than measured", and loosening it survives the whole suite. **The endianness half is the sharper problem and has a one-command demonstration:** patching `"IntProperty": (4, "<i")` to `">i"` turns all 75136 IntProperty values into byte-swapped garbage, and the ONLY tests that go red are synthetic-fixture tests whose own section comment states they are not evidence about the game's format. A fixture built from the same belief as the reader agrees with the reader by construction - the session-6 mutant incident in a new costume. What survives today is "185382 values were produced and are self-consistent with our own writer"; what is claimed is "correctly decoded", and the gap between those two sentences is this item.

### CS-422 - detail

NOTE: filed 2026-08-15 by the measurement-validity adversary, which found the module holding opposite standards in one file. `_SOFT_OBJECT_TAIL_BYTES = 4` SHIPS on "exact consumption on all 116 instances" - consumption at the shipped alignment, n=116, never rotation-controlled - while ArrayProperty is DECLINED on exactly that evidence class at **n=11976**. On sample size the inconsistency reverses: TextProperty is declined at n=10 as too few, and UInt32Property ships at **n=9**. Neither call is obviously wrong; having both in one file with no stated rule is. Also fold in the adversary's measurement that the module's claim "mis-stating any one of them desynchronises the walk immediately" is FALSE AS WRITTEN: terminator reached out of 129775 payloads is 129775 shipped, 129695 with SetProperty 1 to 0, and 129744 with MapProperty 2 to 1 - so SetProperty's width is discriminated on 80 payloads and MapProperty's on 31. "Immediately" overstates a real but narrow discriminator. **AMENDED 2026-08-15 (session 8): the clause "and no test reads either signal" WAS TRUE WHEN WRITTEN AND IS NOW FALSE** - a shipped oracle reads both and reddens on both mutants, confirmed independently by an adjudicator and an adversary; detail in `docs/history_notes.md`. **NONE OF CS-422'S ACCEPTANCE MOVES**, which is the point of amending rather than closing: this item is ONE STATED RULE governing when a width may ship, and nothing has touched `_SOFT_OBJECT_TAIL_BYTES`, ArrayProperty, TextProperty or UInt32Property. Note also that `_TAG_EXTRA_STRINGS`'s own docstring still carries the false-as-written "immediately" sentence - session 8 edited the commentary block directly above it and deliberately left this one, because it is CS-422's to fix. **AMENDED 2026-08-16 (session 9): the 'immediately' sentence is now QUANTIFIED, and it is still in the shipped docstring.** CS-420 measured every width at -1 in the shipped copy alone: the terminator reach breaks on 6 of 6, but ByteProperty -1 still leaves 124416 of 129775 payloads reaching. So the walk desynchronises on a MINORITY of payloads for that width, not immediately, and the honest replacement is a per-width statement the suite derives rather than one adverb. CS-420 deliberately left this docstring untouched because it is CS-422 property; the measurement is recorded here so the next slice inherits evidence rather than re-deriving it.

### CS-426 - detail

NOTE: filed 2026-08-15 by the CS-420 adjudicator as the item it would take next, and independently confirmed by the control-validity adversary. **EVERY DISCRIMINATING TEST CS-420 SHIPPED IS LIBRARY-BACKED AND SKIPS WITH NO GAME INSTALLED.** Measured: with the new modules removed, the entire pre-existing suite exits 0 under `SetProperty 1 to 0` - it is blind to it - and `MapProperty 2 to 1` is caught by exactly one test, `tests/save/test_properties.py::test_every_measured_type_the_library_exercises_yields_at_least_one_value`, which is itself library-backed and therefore also skips on CI. So on a clone with no game, BOTH widths are unguarded. The one width evidence that runs everywhere is `test_both_tag_grammar_transcriptions_agree`, which compares the two TRANSCRIPTIONS and is blind by construction to a fault they share. **This is the CI half of the common-mode question and it is genuinely open**, unlike the real-library half, which session 8 measured to be already guarded - see the corrected note in `WAKEUP_NOTES.md`. Do NOT close this by asserting the fixture round-trips through our own loader: session 6 measured that a round trip cannot distinguish "matches the game" from "matches our reader", and a fixture packed with the same belief the reader unpacks with agrees by construction. **AMENDED 2026-08-16 (session 9): the scope GREW.** CS-420 shipped test_every_tag_width_is_caught_by_a_library_backed_oracle, which derives the whole width-to-detector relation and is ALSO library-backed, so it skips on a clone too. The CI gap is now the width discriminators AND the artifact that grades them. Note also the defect CS-420 found and fixed while here: those tests gated their skip on the SAVE library while the usmap comes from the INSTALL, so on a machine with saves and no install they FAILED rather than skipped - check any fixture built for this item against that configuration, not just against a bare box.

### CS-432 - detail

NOTE: filed 2026-08-16 by the CS-420 builder as a stated residual of its own work, which is the correct place for it. TWO SEPARATE PROBLEMS SHARING A FILE. FIRST, `_JOIN_WORD_FLOOR = 13` sits exactly at the pristine observed distinct-word count, and the join oracle's own liveness assertion still reads it. If this operator's world ever spans enough joined type words that no single-width mutant falls below 13, that assertion goes RED ON A CORRECT GRAMMAR. It is a FALSE RED and loud rather than a false green, which is why it ships rather than blocks, and the attribution test already avoids it by comparing against a pristine baseline measured in the same run - a single sweep has no baseline to compare against, which is why the fix is not simply copying that. SECOND, and structural: the cross-section oracle detects 0 of 6 widths, so `test_every_tag_width_is_caught_by_a_library_backed_oracle` cannot protect it - an oracle that detects nothing is indistinguishable from one gutted to a green no-op, and gutting it was measured to leave the suite passing. Its guard has to come from the fault class it IS sensitive to, the value-start rotation, not from the width attribution. **SHARPENED 2026-08-16 by the final audit, and it is worse than filed: the FLOOR'S JUSTIFICATION IS ITSELF FALSE.** Per-save distinct joined type words across the live library run 8 to 12 and NOT ONE SAVE REACHES 13 - the 13 is a UNION over a growing library, never the engine constant the docstring claims. Within the SAME version pair, 1239 records gives 8 words and 19837 gives 11, so "playing the game moves the tag count and leaves this alone" is exactly backwards. `NameProperty` is contributed by only 3 of the 12 tagged saves, so autosave rotation retiring those three turns `assert sweep.join.words >= 13` RED ON A CORRECT GRAMMAR - a live fragility, not a hypothetical. The companion claim "measured at the full observed width, so a thinned join cannot satisfy it" is refuted by a join thinned 3447 tags that satisfies it. **AMENDED 2026-08-16 (session 10) with a CLEANER counter-example and a NEW measured hazard, both re-derived by two agents independently.** FIRST, the cap-4 thinning already recorded here is beaten by `_MAX_TAGS_PER_PAYLOAD = 8`: it rots 1550 payloads with `join.tags` **IDENTICAL** at 55496 and `join.words` unmoved at 13 - a strictly cleaner demonstration that the distinct-word count does not track the thinning, because the tag count does not move at all. Note the pairing for whoever writes the replacement prose: cap 8 supports "a mutant rots payloads with the count unmoved" and does NOT support "drops thousands of tags", while cap 4 supports the second and not the first. Per-save distinct joined word counts measured across the library are `[8,8,8,8,8,8,8,11,11,12,12,12]`, every one below the floor of 13, which is the corpus-coupling this item exists to remove. SECOND AND NEW: **the floor's hazard is not confined to the join oracle.** Setting `_JOIN_WORD_FLOOR = 14` - which simulates autosave rotation retiring a rare word, the exact hazard - turns TWO tests red, not one: the join oracle at `assert 13 >= 14`, AND `test_every_tag_width_is_caught_by_a_library_backed_oracle`, which calls the join oracle inside its `already_red` check and dies with a message about mutants that never mentions the floor. So the attribution test does not avoid the hazard, it INHERITS it, and it fails misleadingly. The sentence claiming otherwise was deleted in session 10 rather than rewritten, per ADR 0008; the replacement is a detection claim and belongs to whoever closes this item.

### CS-425 - detail

**FROZEN-FILE GRANT ISSUED BY THE OPERATOR 2026-08-15 for `.claude/settings.json`, recorded in `docs/LEDGER.md` BEFORE any edit.** NOTE: the cause is MEASURED rather than reasoned. The `PreToolUse` hook runs `python tools/precommit_gate.py --text-stdin` on matcher `Bash|PowerShell`, so it spawns a console-subsystem `python.exe` on EVERY shell tool call, timed at ~106 ms per spawn; Claude Code is a GUI parent holding no console, so Windows allocates a fresh one per child and it flashes for the life of the process. `PostToolUse` (`tools/edit_lint_check.py`) and the wired git hooks - `core.hooksPath` resolves to `.githooks` - are the same mechanism at lower frequency. **THE DEFECT IS COSMETIC AND THE FILE IS A TIER-0 PROTECTION PATH, so the ordering of those two facts is the whole item:** coverage may NOT be reduced to buy a cosmetic win, which specifically forbids narrowing the matcher or the scanned surface. `pythonw.exe` is the candidate worth testing first because it allocates no console, but it is NOT obviously safe - the hook reports through stdout and an exit code, and whether both survive a parent-supplied pipe under `pythonw` must be PROVEN rather than argued, since the failure mode is a gate that silently stops reporting. **A legitimate outcome of this item is that the file is left byte-identical**, because the real fix may be the parent's `CREATE_NO_WINDOW` spawn flag, which belongs to Claude Code and not to this repo. Record that as the finding rather than reaching for a worse in-repo change; an unused grant is a fine result and a weakened gate is not. **AMENDED 2026-08-15 (session 8) - THE ITEM IS NO LONGER COSMETIC, AND THE MERGER CONDITION "COVERAGE MAY NOT BE REDUCED" IS VOID BECAUSE THERE IS NO COVERAGE ON THAT PATH TO REDUCE.** Three measurements, each executed, established that the Claude-side hook cannot DENY (the protocol denies on exit code 2 and the gate exits 1), probably cannot SEE the command (the JSON envelope escapes a non-ASCII byte into a pure-ASCII sequence the charset scan cannot find, and the flag expects raw text), and demonstrably did NOT block end to end. **THE AUTHORITATIVE GATE IS UNAFFECTED AND WAS PROVEN GOOD** by a real staged violation and a real commit attempt, so the repo is not exposed and CLAUDE.md's "the Claude hooks are a convenience layer" is exactly right. What is wrong is that the convenience layer provides no convenience while costing a process spawn per shell call. The measurement detail is relocated to `docs/history_notes.md`. **OPERATOR RULING 2026-08-15: make it actually work** - parse the envelope so it sees the real command, and exit 2 so it genuinely denies. **Stated consequence, accepted deliberately:** shell commands carrying an em-dash, a smart quote or a secret will be REFUSED mid-session. **Do NOT take the `pythonw` route as a substitute** - it was measured a faithful drop-in (identical rc 3/0/1, identical stdout, identical BLOCKED diagnostic through a real pipe-and-wait, the earlier PowerShell result being an artifact of PowerShell not waiting on a GUI-subsystem binary), but shipping it ALONE would kill the flash while preserving a hook that silently does nothing, which is the false-guarantee class this project rates worse than the bug.

### CS-405 - detail

**UNBLOCKED 2026-08-15, BOTH BLOCKERS GONE, AND THE EXPERIMENT IS PARTLY ANSWERED ALREADY.** The object walk reaches real buildings across the whole local library and CS-413's decode half landed, so the superseded revision of this note - which said the walk was a skeleton and no property VALUE was readable - is relocated to `docs/history_notes.md`. Measured in passing by the CS-413 builder and NOT adjudicated by it, which is the correct boundary: **`mInventoryPotential` decodes, 962 instances across three version pairs, as an OBJECT REFERENCE - a 2-tuple - and not as an integer slot count.** Read that carefully before mapping it onto the three outcomes, because it is not any of them yet: it refutes the naive form of YES (the component does not carry a bare count) without establishing NO (a count may live behind the reference, in the referenced record). Resolving that is this item's own slice. Note also that ObjectProperty is one of the type words backed by the cross-section oracle rather than by width alone, so the 2-tuple reading is among the better-evidenced parts of CS-413's decode - see CS-421 for which types are not. THREE outcomes, not two, and the third is the one a careless agent collapses into NO: YES, the serialized component carries a slot count, which is a direct measurement of ADR 0005's last operand and licenses a LATER slice writing `OVERCLOCK_POTENTIAL_SHARD_SLOTS` into `clockspeed/data/version.py` WITH the four-invariant drift-guard entry ADR 0005 requires - it does NOT license `power.py` publishing a ceiling in the same slice; NO, it is serialized and carries no slot count, which fully refutes ADR 0005 option (b) and is worth as much as YES; or INCONCLUSIVE, meaning no world in the library has a built overclockable building with that component serialized at all, in which case the probe DID NOT RUN and the answer is "not yet measured" - the operator ruled on 2026-08-14 that this is an acceptable outcome and is filed as a re-run against the world growing, NOT converted into either answer. Do NOT derive the number any other way: ADR 0005 fences four routes and the arithmetic one, `slots = (2.5 - 1.0) / 0.5 = 3`, FEELS derived because it uses only shipped values and is not.

### CS-412 - detail

NOTE: raised 2026-08-15 by the CS-407 result. The prior session's resume note for header 13 / save 42 said "the grid preamble is measured", and that measurement was recorded NOWHERE in the tree - not in `objects.py`, not in `synthetic.py`, not in the ledger - so the slice resuming it had to re-derive it from scratch. **A partial recorded as an adjective is not resumable.** The successor structure already exists as `LEVELLED_LAYOUT_OPAQUE_SPANS`; this item is about proving it COMPLETE against what the parser actually skips, so a later slice inherits evidence rather than a sentence. ADDED 2026-08-15: fold in `tests/save/synthetic.py:1079-1082`, which claims count equality for "2945 of 2945 levels on the (14,52) corpus". That is TRUE but narrower than reality - it holds on 6171 of 6171 levels across all four pairs, measured under CS-413. Found by the CS-413 builder and left alone because the file was outside its write-list, which is the boundary working as intended. A claim that is true and understated still rots, because the next reader treats its scope as the measured limit. Two precedents this session argue for generating such counts rather than writing them: CS-413's own first revision put a WRONG level count into a shipped docstring with a TRUE claim attached to it, and CS-404's evidence table now records which widths are measured versus merely uncontradicted rather than asserting a number.

### CS-439 - detail

NOTE: filed 2026-08-16. FIVE INSTANCES NOW - CS-417, CS-419, CS-430, CS-435, CS-438 - each a docstring promising a report over code that drops the value silently. **THE KEY IS MEASURED, NOT PROPOSED, and the first key tried FAILED the measurement, which is why this entry states both.** Key A, a reporting verb anywhere in scope, matches 292 of 298 functions on prose alone and the conjunction with the code half is also 54, so the prose half buys NOTHING - house style puts a reporting verb in nearly every module docstring. Key B, the verb in the function's OWN docstring minus a documented None-return contract, goes 298 to 106 to 25 to **12 candidates**, which is reviewable. **THE EVIDENCE THAT B IS REAL RATHER THAN PLAUSIBLE: it surfaces `clockspeed/save/workdir.py::_save_files` as a candidate, which is CS-438, FILED INDEPENDENTLY BY A DIFFERENT AGENT that did not build the key.** It also correctly classifies the CS-435 repair's own `usmap.text` and `usmap.resolve` as CONTRACT rather than candidates. Two known members to fold in: `workdir._mtime_ns` swallows `OSError` and returns 0, and `clockspeed/data/locate.py:531` reads the Steam library index with `errors="replace"` so a replaced byte silently drops a library and the install reads as absent. STATED LIMITS, from the agent that measured it: CS-430's real content - a warning that FIRES but whose SENTENCE is false - is not statically decidable and needs the runtime discipline instead; the CS-419 aggregation-key collision is detectable but on a DIFFERENT key and is a second, cheaper guard; and an UNDOCUMENTED silent loss is invisible to B by construction, because anchoring on the promise is exactly what buys the reduction.

### CS-440 - detail

NOTE: filed 2026-08-16 as the stated remainder of CS-435, whose ledger entry names it. CS-435 closed on its written acceptance and its STATED DEFECT is not fully closed: a MODELLED class whose usmap name is undecodable STILL reports as unmodelled, and what changed is only that it is no longer silent. Two measured sites, both outside CS-435's write-list and neither touched: `clockspeed/save/world.py:919` builds `WorldWarning(source, code, detail, count)` and DROPS THE SUBJECT, so `name-0` never reaches a consumer and the world layer learns "some name did not decode" without learning which; and `clockspeed/save/objects.py:588` sets `REASON_CLASS_NOT_MODELLED`, "is not a class the supplied registry models", which is FALSE for this input and is the only member of `UNKNOWN_CLASS_REASONS`. This is a confident wrong answer surviving behind a correct warning, which is the non-negotiable 7 failure rather than the tolerated one. **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE - THE ACCEPTANCE IS NOT MET ON EITHER CLAUSE.** The wiring is not vacuous - forcing the registry-loss flag constant reddens 3 tests and dropping the subject reddens 5, both byte-verified - and no CS-419 aggregation regression was introduced, because the world layer does no dedup at all. **CLAUSE 1 FAILS: THE SUBJECT IS A USMAP POSITION, NOT A CLASS.** The subjects delivered are `name-0` and `schema-0`; the name at that position is the empty placeholder and the schema was dropped, so a consumer learns WHICH POSITION failed and still cannot name the class. The class name is precisely the datum destroyed, and no amount of threading recovers it. **CLAUSE 2 FAILS BY TOTAL COLLAPSE:** the reason is a per-LOAD flag rendered as a per-ENTRY attribute, so injecting ONE unresolved-name warning into the real mapping gave the weaker reason to 1152 of 1152 entries and the stronger to none. On real data the new reason never fires at all - the branch is synthetic-only today. **AND THE KEY IS UNDER-INCLUSIVE IN THE DANGEROUS DIRECTION, which is this item's own defect class reappearing:** two further real conditions drop a declared class while the flag stays False, so the world still ships the exact false sentence. An unknown PROPERTY TYPE leaves the cursor mid-entry rather than skipping the payload; and **a newer usmap version - the realistic one, a game patch bumping the schema layout - needs no alignment luck**, which is one of the two routes the builder excluded untested while saying "if either can drop a class, my key misses it". It does. A sibling is worse: the unknown-property-type path can INVENT a name the file never declared, which is then reported MODELLED with no warning at all. Five false sentences, one of them ASSERTED into a control that pins the false claim.

### CS-441 - detail

NOTE: filed 2026-08-16 from the CS-438 adversary and CONFIRMED by the CS-438 repair with three byte-verified mutants. `tests/test_exception_rendering.py`'s `RenderVisitor` is scoped BY DESIGN to `except ... as NAME` handler bodies, and its own docstring states that `safe_exc_text(exc)` takes the exception as a parameter so its `str(exc)` sits outside every handler. Measured against `workdir._listing_problem(code, exc)`: `detail=str(exc)` gives 0 findings GREEN, `detail=exc.filename` gives 0 findings GREEN, and the same `str(exc)` inside a real handler gives 1 finding RED. The runtime behaviour is clean today, so this is a COVERAGE gap rather than a live leak - but the module that relied on it had ZERO direct tests until CS-438's repair added them, and the sweep is the enumerating guard the project trusts precisely because it has no list. Note the shape generalises: any helper reached from a handler and handed the bound exception is invisible, and nobody has counted how many exist. **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE.** The narrow mechanism works - a suffix-annotated parameter rendered whole IS now flagged, and the sanctioned-helper half SURVIVED every attack including two combined mutants aimed at the non-vacuity proofs, which are genuinely live. **WHAT FAILED: of 46 spliced shapes 26 ESCAPED, and seven whole-object leaks in one file left the suite green.** Three families, all measured: the annotation predicate is a NAME SUFFIX, so it misses 19 builtin exception types, `subprocess.TimeoutExpired` - which this project's own gate names as a leak type - and **five exception classes this repo already defines carrying `noqa: N818`**, so the predicate's foundation is already deliberately breached in-tree; an UNANNOTATED parameter is invisible; and the exemption is reachable by `not isinstance(...)`, by `isinstance(...) or flag`, and by a locally-defined `OSError` SUBCLASS whose `__str__` appends the filename, which refutes the stated reason that a module defining a type can promise its message. **THE ITEM'S OWN "no list to keep up to date" CLAIM IS FALSE:** three dicts in that file are keyed by PATH, so a brand-new leak appended to an already-listed file is absorbed silently - demonstrated in `tools/drift_guard.py` and again in a waived test file, both green. Four false sentences and seven behaviour-changing green mutants against unbacked detection claims are recorded against ADR 0008. Measured against 7165 annotations in the tree: **0 real helpers sit in the blind spot today**, so this is coverage, not a live leak - one keystroke deep.

### CS-442 - detail

NOTE: filed 2026-08-16. `docs/LEDGER.md:128` cites `tests/save/test_absolute_claims.py::test_the_scanned_prose_carries_no_unbacked_absolute_claim`, which occurs ZERO times; the real name is `test_the_fenced_prose_carries_no_unbacked_absolute_claim`. Corrected by a new record, because this file is append-only. **THE STRUCTURAL FACT IS THE ITEM AND IT IS SHARPER THAN THE TYPO: NOTHING IN THIS REPOSITORY READS `docs/`.** `tests/save/test_oracle_citations.py` scans `clockspeed/`, `tests/save/test_absolute_claims.py` scans `tests/`, and neither looks at `docs/` at all - so the VERIFICATION POINTER, which is the one field `docs/LEDGER.md` declares MANDATORY and the entire reason that file is trustworthy, is unguarded. Note the append-only tension to solve rather than inherit: a correct citation can be invalidated by a later legitimate rename, so the rule must distinguish a pointer that was WRONG WHEN WRITTEN from one the tree moved out from under, and the second is not a defect in the record. **SHARPENED 2026-08-16 (session 12) BY A CENSUS RATHER THAN AN ANECDOTE - the population is bigger than the one typo this entry was filed on, and it is FIVE, not one.** Re-derive rather than trusting these figures, but as measured that day: of the `path::name` citations in `docs/`, five resolved to no name defined anywhere in the tree, in `docs/LEDGER.md` alone, spanning entries written across several sessions rather than clustering in one. **THREE DESIGN FACTS THE CENSUS TURNED UP, each of which a naive checker gets wrong.** FIRST, the dead name this entry already names occurs at a SECOND site that a `path::name` scanner structurally CANNOT see: it sits inside a `grep -c <bare name>` command in the MANDATORY `Verification:` field, as a bare identifier with no path attached. That is the single most important shape to cover, because the Verification pointer is the entire reason the ledger is trustworthy, and it is the shape most likely to be missed. SECOND, **a `file:line` citation into `docs/LEDGER.md` rots BY CONSTRUCTION**: the ledger is append-only NEWEST-FIRST, so every existing line number shifts down whenever an entry is prepended - which is why this entry's own `docs/LEDGER.md:128` pointer no longer names the line it was written for. A rule that treats a drifted ledger line number as a defect will be red on correct history. THIRD, and this is a warning about the checker rather than about the tree: the census's own `file:line` arm reported six dead targets and **all six were ARTIFACTS** - bare basenames like `objects.py:1666` which the checker resolved repo-relative and then declared missing. An unqualified citation is not a dead one. Discarding that number was the right call and the next checker must not re-earn it.

### CS-443 - detail

NEEDS ITS OWN FROZEN-FILE GRANT for `tools/precommit_gate.py`; the 2026-08-16 CS-436 grant is SPENT and covers CS-436 alone. NOTE: filed 2026-08-16 by the CS-436 builder, MEASURED and deliberately not fixed because it is outside CS-436's three enumerated parts. With a malformed `config/local.json`, `discover_world_names` recovered 0 declared names and emitted NO skip about the config; the only line printed advises the operator to "add world_names to config/local.json", WHICH THEY HAD ALREADY DONE. That is the CS-436 false-statement class one layer up - not silence, an instruction to do the thing that is already done and is being discarded. `local_config` takes no `report` argument at all, so there is no channel to report on. Fold in the CS-436 residual its repair flagged and did not widen into: when the header reader is unimportable and the root is NOT truncated, "no world token is discoverable" still prints beside "the save-header reader is not importable", which is the same two-lines-that-disagree defect the CS-436 repair fixed for the cap case. **THE UNFROZEN HALF WAS BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE.** Three claims SURVIVED hard attack: all six loss paths report, each code is pinned by its own reddening test, and absence plus a valid file stayed silent across 1500 measured invocations. A SEVENTH loss path that CRASHED rather than discarded was found and fixed - `UnicodeDecodeError` is a `ValueError`, not an `OSError`, and escaped a function whose docstring promises it never raises; confirmed independently against the pre-fix blob. **WHAT FAILED, and the first one is the acceptance itself.** (1) **THE CHANNEL HAS ZERO PRODUCTION CONSUMERS.** No caller in `clockspeed/`, `tools/` or `scripts/` passes the collector, so `scripts/verify_env.py` against a malformed config still exits 0 printing nothing about it. The acceptance says a bad config "is REPORTED rather than returning `{}` in silence"; against every shipped entry point it still returns `{}` in silence. A resolver fix is not a consumer fix, and CS-452 carries the seam. (2) **THE `detail` SENTENCE - the entire operator-facing content - HAS NO CONTROL:** replacing all six with a nonsense sentence left the module suite green, and giving the malformed case the oversize sentence also stayed green. Only truthiness is asserted. That is the CS-430 class exactly. (3) **THE SUBJECT'S REDACTION FAILS OPEN TWICE** - it reads only the environment, and `_RESOLVED_ACCOUNT_NAMES` is lazily seeded so the same input redacts or does not depending on call order, with the config read running FIRST in the resolve chain. Its control is structurally blind because the oracle and the redactor share their only input. (4) Four sentences measured false, one of them the merger's. (5) FOUR further silent paths remain: an empty or whitespace value dropped later by `_override`, a duplicate key, and - the most likely operator error of all - a mis-typed or mis-cased key, returned faithfully and read by nobody.

### CS-444 - detail

NOTE: filed 2026-08-16 by the CS-438 builder, which found it while sweeping its own file and reported rather than widened. **THIS ONE IS SECURITY-RELEVANT AND SITS DIRECTLY ON A NON-NEGOTIABLE.** The guard is `if resolved is not None`, so a save root that fails to resolve NEVER REACHES THE REFUSE LIST, and a copy could then land inside it. Non-negotiable 1 is never write to the game install or the save directory, and `clockspeed/save/workdir.py` is by deliberate design THE ONLY MODULE IN THE PACKAGE WITH A WRITE - `docs/ARCHITECTURE.md` records that this is what makes the invariant statically checkable rather than a rule reviewers must remember. A fail-open in the refuse list is therefore a hole in the one mechanism the architecture relies on. Same silent-loss family as CS-439 and it should be fixed whether or not CS-439 lands, because the failure direction here is a WRITE rather than a missing report. **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY BY A SECURITY ADVERSARY THAT WROTE NONE OF IT. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE.** `ForbiddenRoot` now carries a nullable resolved path so "present but unresolvable" is representable, and the refusal fires on it. Two claims SURVIVED byte-verified mutation: reverting only the producer reddens 5 tests, reverting only the consumer reddens 4, and the harness control discriminates rather than passing for the pre-existing destination check. **TWO CLAIMS DID NOT.** (1) "The fail-open is closed" is TOO WIDE and must read "closed INSIDE `_forbidden_roots`" - see CS-449, whose reachability the adversary MEASURED rather than left open. (2) **THE REFUSAL MESSAGE IS A NEW PERSONAL-DATA ECHO PATH AND ITS CONTROL IS VACUOUS** - see CS-454. Gutting the redactor out of the new branch left the whole workdir suite green, because the control's own fixture uses an all-digit account name, which is the one shape the backstop catches unconditionally. That is a fixture built parallel to the implementation, and it is this project's own named failure class.

### CS-445 - detail

NOTE: filed 2026-08-16 from the CS-438 repair, which measured them and correctly declined to make a unilateral prose edit inside a repair commit. ADR 0008 is now `accepted` and binds LIVING TEXT REPOSITORY-WIDE, while its mechanical fence is scoped to two modules in `tests/save/` - so these are in scope for the RULE and out of scope for the CHECK, which is exactly the breadth question the ADR's SCOPE clause reserves as separate work. **THIS ENTRY IS THE MEASURED POPULATION FOR THAT WORK, so a later slice inherits evidence rather than an argument.** `clockspeed/save/objects.py:890` documents `body_length` with a corpus-scoped universal, "never zero-length in any real save on this machine", RESTATED at `objects.py:2809` and again at `tests/save/test_objects.py:776` with no live guard - one measured fact in three places, which is CLAUDE.md section 4's own failure mode. Two "the only one" superlatives sit at `objects.py:1066` and `objects.py:1609`. Note the tension with CS-412, which wants unmeasured spans recorded AS DATA: the fix for a corpus-scoped universal is probably to derive it, not delete it.

### CS-447 - detail

NOTE: filed 2026-08-16 as CS-428's stated residual, measured rather than assumed, and deliberately kept out of that item because neither is a forced-failure render. **THE SESSION HEADER IS THE LIVE ONE AND ONLY ON LINUX:** pytest's `rootdir:` line prints the checkout path on EVERY run, pass or fail, and on a Linux CI runner the checkout sits beneath the runner account's home directory, so a home path is printed on every CI run of every lane. **THE LITERAL RUNNER PATH IS DELIBERATELY NOT WRITTEN HERE: the commit gate BLOCKED the first version of this entry for exactly that, which is CONVENTIONS section 10 and non-negotiable 3 doing their job on the entry that describes the leak.** It is harmless on this operator's machine because `C:\Clockspeed` is not under a home directory - which is LAYOUT LUCK and not a property of anything. The warnings summary is inside the region CS-428's own oracle scans but outside what its remedy can rewrite; CS-428 resolved that contradiction toward the statement and left the gap named and tested rather than implied. Also uncovered and confirmed by measurement: a collection error exiting rc 2, and `--co`.

### CS-448 - detail

NOTE: filed 2026-08-16 by the final adversary auditing merged main, and it is a LIVE TIER-2 CI RISK. **IT IS PRE-EXISTING AND NOT INTRODUCED BY THIS SESSION, WHICH IS ESTABLISHED RATHER THAN ASSUMED:** measured 1 failure in 3 runs at `76f6c82` AND 1 in 3 at `ee36d0d`, the same test both times, and `git diff --name-only 76f6c82 ee36d0d -- tests/save/test_synthetic.py` is empty. The tier-2 lane runs `-n auto`, so this is the lane that flakes. Mechanism as far as it was traced: the gate spawns a nested child pytest run, and that child fails at `tests/save/test_synthetic.py::test_a_failing_builder_call_renders_its_arguments` with a collection error in its own SUB-subprocess, taking 61 seconds against 28 warm. So it is a three-level process nest under parallel load, and the honest reading is contention rather than a logic fault. DO NOT close this by raising a timeout or by marking the test flaky - a nested run that fails under load is telling you the nesting is the cost, and CS-426 already wants a no-install path that runs everywhere. Note the interaction to check first: this session's CS-428 added report hooks that fire in every worker AND controller-side, so re-measure at a revision before and after that commit even though the flake predates it. **SOLVED 2026-08-16 (session 12). THE MECHANISM IS MEASURED AND IT IS NOT CONTENTION - IT IS THE CHECKOUT LOCATION.** The merger first reported 32 runs with 0 failures and concluded it did not reproduce. **AN ADVERSARY REFUTED THAT AND REPRODUCED IT SIX TIMES**, at BOTH cited revisions, with a signature byte-identical to the original evidence: 3 failures in 10 runs at `a267705`, 3 of 4 at `ee36d0d`. **THE MERGER'S 32 RUNS WERE ALL EXECUTED IN THE TWO LOCATIONS ON THIS MACHINE WHERE THE FAILURE IS STRUCTURALLY IMPOSSIBLE**, so they were a control rather than a null result - as were a further 460 runs the adversary took there, junit-verified to confirm the gate testcase actually ran in 20 of 20. **THE CHAIN, each link measured.** When the checkout shares a large ancestor with `tempfile.gettempdir()`, pytest's rootdir for the innermost probe climbs to the TEMP ROOT, and collection then walks the whole temp tree: the same probe with only the cwd varied took 0.4s from three ordinary locations and **42.7s from a clone under the temp root, 107x from checkout location alone**. During that walk a sibling xdist worker creates and destroys `%TEMP%\clockspeed_gate_*` directories through `tools/precommit_gate.py`, `os.lstat` on the vanished entry raises `FileNotFoundError`, collection is Interrupted, the sentinel is never printed, the level-2 child exits 1 and the gate goes red. **xdist supplies only the concurrent creator and deleter - it is NOT CPU contention, and the 42.7s walk happens single-process with nothing else running.** THE MERGER'S FIRST MECHANISM STORY WAS WRONG in both halves and its fixture count was wrong too - that file defines 12 sandbox spawns, not the seven the merger wrote. **WHAT SURVIVED THE REFUTATION:** the CI-history reading is confirmed independently - 7 tier-2 runs is the COMPLETE history rather than a first page, the one red was a different test, and the gate is NOT skipped on hosted runners. **WHAT IS STILL OPEN, and it is the only thing left:** whether tier-2 CI is actually exposed is UNSETTLED, because a hosted workspace probably does not share a large ancestor with its temp directory - but that is inference from this machine, which is the same species of inference this entry criticised. **Measure `rootdir` inside a real tier-2 job before closing.** Housekeeping that feeds the defect and should be fixed regardless: the temp tree held hundreds of stale `pytest-of-*` entries, and the bigger it grows the longer the walk and the wider the race window. Do not close by raising a timeout; the fix is to stop the rootdir climbing, which also removes the 100-second walk.

### CS-449 - detail

NOTE: filed 2026-08-16 by the CS-444 builder, which found it sweeping its own file and REPORTED rather than widened. **SECURITY-RELEVANT, SAME DIRECTION AS CS-444 - a WRITE.** `resolve_save_root()` returns None when its directory test is False, and a None root never becomes a candidate in `workdir._forbidden_roots()` at all, so CS-444's fix never sees this one: the hole is one layer below the layer just patched. **REACHABILITY IS EXPLICITLY UNMEASURED AND MUST NOT BE ASSUMED EITHER WAY** - it turns on which errnos the directory test swallows rather than re-raises, and the builder measured the SHAPE, not the exploitability, on 3.14/Windows only. Do not declare it unreachable without measuring on 3.13: CS-438 shipped exactly that error. **UPGRADED 2026-08-16 THE SAME DAY IT WAS FILED - THE REACHABILITY IS NO LONGER OPEN, IT IS MEASURED, AND IT REPRODUCES END TO END.** A security adversary drove a save root that is genuinely on disk, where the directory entry lists and `lstat` succeeds while `stat` fails: `is_dir()` answered False, `resolve_save_root()` returned None, `_forbidden_roots()` returned EMPTY, and a destination INSIDE that save root DID NOT REFUSE. `Path.is_dir()` applies no errno filter at all on 3.14, and the 3.12 filter already lists the same error, so the declared floor between them swallows it under either implementation. **HONEST LIMIT, STATED BECAUSE IT BOUNDS THE SEVERITY:** in that particular instance the destination is also unwritable, so the check is gone but the write would not land. The live variant is the transient one - the same call swallows sharing violations, access denials and not-ready errors identically, so a stat that fails at CHECK time and succeeds at WRITE time is the shape to fear, and the adversary could NOT construct a simultaneously-stat-denied-and-writable directory on this machine. A demonstrated MISSING CHECK, not a demonstrated write.

### CS-454 - detail

NOTE: filed 2026-08-16 by the CS-444 security adversary. **THIS IS A PRE-EXISTING LIVE LEAK, NOT ONE CS-444 INTRODUCED** - the adversary demonstrated it on an unpatched path as well - but CS-444 added a second echo path carrying it plus a green assertion saying it does not, which is worse than the bare leak. Measured in one supported configuration: the operator relocates saves via the env override and leaves the account directory undeclared. All three redaction rules then fall together - the positional rule needs a marker the relocation removed, the remembered-account list is fed only by an all-digit directory scan, and the digit backstop misses a hex token, a GUID and an operator-renamed directory. Epic-like, MS-Store-like and renamed account directories all rendered in plaintext; an all-digit one redacted. `clockspeed/data/locate.py` already names exactly those platforms as the reason not to rely on the digit rule. **THE CONTROL IS VACUOUS AND THAT IS THE HALF TO FIX FIRST:** removing the redactor from the new refusal branch entirely left the whole workdir suite green, for two independent reasons - the fixture's destination contains no account id at all, and its account name is all digits. Non-negotiables 3 and 12.

### CS-701 - detail

NOTE: filed 2026-08-16 by the CS-427 adversary, which hit it while scanning that slice's diff for leaked personal data and correctly classified it as a PRE-EXISTING FALSE POSITIVE rather than a finding against the slice. Measured: the operator git author line coincides with one 4-character world name on this machine, and it is present identically on `8b3fb9d` and `1009681` - `author-line hits: 1, body hits: 0` on every revision checked. **NOTHING IS LEAKED BY THIS TODAY** - the world name is not disclosed by the author line, the coincidence runs the other way. The problem is mechanical and arrives later: **a world-name-keyed PII scan will trip on EVERY COMMIT IN THE REPO**, and a scan that is red on correct history is a scan someone switches off. CS-700's checklist includes a full-history PII scan across tracked files and commit messages, so settle the exemption rule before that gate runs rather than while it is failing. Note the CS-209 precedent: narrowing a PII blocklist by default to pre-empt a collision was DENIED BY MEASUREMENT, so an exemption here must be a named, recorded exception rather than a shortened matcher.

---


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

### CS-454 - status detail

Relocated 2026-08-18 (session 19) from CS-454's `ROADMAP.md` entry, which carried the file over its WARN budget. The item is OPEN and tier 1; its clause verdict stays in `ROADMAP.md` and only the supporting detail is here. Read it before taking the item.

The code shipped in `60068a9` and `02523f9` and STAYS - the relocated-path form is closed in all four resolution states, the 8.3 form is closed, and three independent vacuity reasons were removed from the controls. Full record in `docs/LEDGER.md` under the 2026-08-16 CS-454 non-closure entry. **FOUR THINGS REMAIN AND ALL FOUR ARE INSIDE THIS ITEM - do not file them as follow-ups, because a follow-up does not satisfy the clause it was filed against, which is what kept CS-422 open.** (1) **THE JUNCTION DEFECT, and it is in the NEW design rather than pre-existing:** `_remember_save_root` stores `_path_forms(str(path))` and never resolves, while `clockspeed/save/workdir.py`'s `_resolved()` deliberately does, so a save root reached through a junction can never match an anchor and a hex account directory rendered WHOLE through the production refusal in `_refuse_if_forbidden`. Reproduced with a real `mklink /J`. (2) **PLACEHOLDER INJECTION DEFEATS POSITION:** the environment pass runs first and rewrites a matching needle to a token, injecting `<` into the account segment; `_PATH_SEGMENT_CLASS` excludes `<>` so position cannot match and the name pass hunts a literal that is gone. With `USERNAME=Ada` and account directory `Ada4f3a...`, 30 of 33 characters render in plaintext WITH THE MARKER PRESENT. Pre-existing, unchanged from `bb7a236`, and a pre-existing instance of the defect this item names does NOT excuse it - this item's own detail entry opens by calling the leak pre-existing. (3) **THE WHITESPACE TAIL:** `My Backup Copy` renders `<account-dir> Backup Copy`. Three widenings of the segment class were measured and ALL THREE ARE WORSE - one eats the diagnostic prose, one leaves the terminal segment fully intact. Do NOT close this by widening the class; the adjudicator verified that decline was correct. The cheap route it names is feeding the matched segment into the name memory after position fires. (4) **THE BARE-SEGMENT FORM** must be closed or recorded as a STATED exemption bounded by `tests/test_redaction_scope.py`'s fence, which currently bounds it without any exemption being written down.

### CS-421 - status history


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
