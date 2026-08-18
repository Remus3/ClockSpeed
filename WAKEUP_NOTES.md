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

