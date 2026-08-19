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
