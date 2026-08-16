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

## Session 9 - 2026-08-16 - four items close, and every single first build was refuted

- **Shipped: CS-419, CS-420, CS-424, CS-427 CLOSED.** ADR 0008 recorded (`proposed`). Filed
  CS-428, CS-429, CS-430, CS-431, CS-432, CS-701. Suite 1619 -> **1674 passed, 7 skipped**, exit 0.
  mypy 75 files 0 errors, drift guard CLEAN 8/8, doc budget PASS. Detail in `docs/LEDGER.md`.

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

- **In flight, and NEITHER IS FINISHED - do not assume either result:**
  - **CS-425** was dispatched and had not reported when this note was written. Its worktree is
    `worktree-agent-ac8907b95df03dfee`, correctly based at `667a9a9`. Design constraint given to
    it: a NEW unfrozen file under `tools/` parses the hook envelope, reuses the gate's scan BY
    IMPORT, and exits 2; `.claude/settings.json` is repointed at it. **`tools/precommit_gate.py`
    must stay byte-identical** - see Decisions.
  - **A FINAL PROSE ADVERSARY** was reading merged `main` at `667a9a9` against ADR 0008 and had
    not reported. It exists because the builders repaired their own prose and then SELF-AUDITED
    it, which is precisely the failure mode that has beaten four consecutive rounds. If it
    returns findings, they are new work under ADR 0008 rather than a reopening of the four
    closed items, whose stated acceptance was independently verified.

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

- **Next action:** land **CS-425** and the final prose adversary, both in flight. Then **CS-403,
  CS-209, CS-204** as ONE slice under the recorded `tools/precommit_gate.py` grant - they all edit
  that one file, so they are one slice and not three, and the binding condition is that no edit
  may introduce a new way for the gate to FAIL TO START, proven end to end with a real `git
  commit` rather than by passing flags explicitly.

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
