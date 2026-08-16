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

