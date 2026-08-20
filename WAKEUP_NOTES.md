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

- **THE HARNESS HEREDOC ATE MY BACKSLASHES THREE TIMES**, twice on small payloads with quoted
  delimiters. Write such payloads with the Write tool; this is the third session it has bitten.
