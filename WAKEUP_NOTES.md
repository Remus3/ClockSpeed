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
