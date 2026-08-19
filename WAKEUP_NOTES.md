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
