# Wakeup notes

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

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

## Session 40 - 2026-08-25 - a LIVE tier-1 leak found on main and closed; four items build, all four are REFUTED, all four are repaired, and NOTHING CLOSES; the finding is that an empty population satisfies every assertion of zero

- **Shipped: NOTHING CLOSED.** CS-829, CS-846, CS-850 and CS-851 all merged as improvements
  after a build round AND a repair round, and every one STAYS OPEN. Filed CS-852 through
  CS-855. Detail in `docs/LEDGER.md` and `docs/item_notes.md`, not here.

- **A LIVE TIER-1 PRIVACY LEAK WAS ON `main` AND IS NOW CLOSED.**
  `tests/save/test_world.py` rendered the RAW world token and map name into a failure report
  **under default flags** - pre-push hook and both CI lanes - because assertion rewriting
  renders the ARGUMENT of an inline `len()`. The test whose purpose is proving the world
  model reprs without leaking, leaked. Found by an adversary sent to grade a different item.

- **THE HEADLINE FINDING: AN EMPTY POPULATION SATISFIES EVERY ASSERTION OF ZERO.**
  `assert count == 0` passes when the property holds AND when nothing was measured, and the
  two produce byte-identical output. Five instances in one session, filed as
  `memory/an-empty-population-satisfies-every-zero.md`. The worst: a second reading of the
  save grammar omitted a 16-byte guid step, desynchronised at the FIRST struct tag, found
  ZERO struct sites in 87302 accepted records, and satisfied its `== 0` arm for roughly
  forty sessions while being sold in prose as independent corroboration.
  **This is the mirror of session 39's finding** - that one was green because the defect was
  present; this one is green because the DETECTOR IS SILENT.

- **FIVE ADVERSARIAL PASSES: FOUR REFUTATIONS, ONE CONFIRMATION.** Not one finding would
  have come from the agent that built the thing. Two refutations landed on the same shape -
  a guard green because its detector is blind, not because the property holds.

- **A DEFECT REPAIRED AT ITS SITE RELOCATES - CS-829's IS NOW ON ITS FOURTH SITE**, having
  moved to `objects.parse_body`, the record table BOTH readings share. The independence
  audit is clean and the module DISCLOSES the shared substrate; disclosure is not a guard.

- **NEW, AND IT IS THE GOOD KIND OF SURPRISE: A REPAIR WAS REFUTED BY ITS OWN VALIDATION.**
  The slice instructed to make a fitted ceiling SKIP built it, measured that the skip let a
  real defect survive, REVERTED its own instructed fix, and recorded the attempt and its
  refutation at the constant. Three of four repair slices pushed back on the merger's brief
  with measurements, and all three were right.

- **Decisions: none recorded as an ADR.** One operator round at the start, taking all four
  units and ruling CS-844 HELD for a third session.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But the binding census in the CS-851
  guard was blind to `ast.Try` ENTIRELY - `except-target` went 0 to 115 named handlers - so
  every count derived from it before this session was an UNDER-count, including an
  adversary's own false-negative analysis.

- **Failed paths: none abandoned.** CS-844 remains held, its worktree and three commits
  intact.

- **Next action: NONE IS FORCED.** CS-829 remains the head of the product path and now needs
  a denominator independent of the RECORD TABLE, not merely of the tag-list reader.

- **A COUNT IN THE LAST NOTE WAS FALSE.** It recorded 99 open items; `d813e22` carried 97.
  Do not restate counts here - read them from the tool.

- **DOC BUDGET IS THE BINDING CONSTRAINT NOW.** `docs/item_notes.md` finished at 96 per cent
  after 6.5 KB was relocated to `docs/history_notes.md`, and it holds ZERO closed-item
  sections, so relocation is nearly exhausted. Four merged-without-closing items plus four
  new ones is what 96 per cent looks like. **This needs an operator decision next session** -
  split the file per phase with an index, raise the budget, or accept that a session can add
  at most one or two item blocks.

---

## Session 39 - 2026-08-25 - CS-845 CLOSES on END-TO-END proof after 40 sessions of a gate that never once worked; three items merge REFUTED-then-repaired; the finding is proofs that require the defect

- **Shipped: CS-845 CLOSED.** CS-829, CS-846 and CS-850 merged as IMPROVEMENTS and all three
  STAY OPEN. Detail in `docs/LEDGER.md`, not here.

- **THE CLOSURE BROKE A FIVE-SESSION STREAK, AND IT WAS PROVEN THE ONLY WAY THAT COUNTS.**
  The PostToolUse edit check had never once succeeded in roughly 40 sessions - zero
  successes, zero non-empty stdout - while printing a failure on every edit. After the merge
  the harness itself spawned the merged tool against a real edited path and the derived
  census reported ONE record with exit 0 and non-empty stdout out of 961. Hook presence is
  not hook firing; only end to end counts, and this is the first time this project has had
  it. Its adversary tried five over-correction mutants and an eighteen-case hostile battery
  and could not make it fail.

- **THE HEADLINE FINDING, NEW AND FOUND IN THREE ITEMS INDEPENDENTLY: A PROOF THAT MEASURES
  ITSELF AGAINST TODAY'S TREE ENCODES TODAY'S DEFECTS AS ITS PASSING CONDITION.** CS-850's
  proof went RED when leaks were repaired - green certified that three modules still leaked.
  CS-829's bound was fitted to this machine's save library, and autosave rotation alone would
  break it. CS-846's rules were chosen BECAUSE they scored zero on today's tree. The previous
  five sessions found acceptance clauses too WEAK; this session found proofs ANTI-CORRELATED
  WITH SUCCESS.

- **A DEFECT REPAIRED AT ITS SITE RELOCATES RATHER THAN DYING.** CS-829's central defect was
  refuted at `_container_element_words`, then at `_read_tag_header`, then at `_payload_text`
  - three times, each after a repair. CS-850's anti-monotone defect moved one function and
  stayed in the module. **Sweep the whole structure after a repair; do not re-test the site.**
  CS-850's final round swept its whole module against a zero-live tree and that is why it
  merged.

- **A THIRD ECHO PATH FOR PERSONAL DATA.** After the assertion channel and the source-echo
  channel there is the LOCALS channel: a save-derived frozenset in a local renders under
  `-l` even when every asserted expression is a scalar. Live on main, 6 of 12 struct words.
  Two sites closed by removing the BINDING. The merger's own sweep found one site more than
  the adversary named.

- **A MERGE VALIDATED A FIX THAT WOULD OTHERWISE HAVE BEEN UNTESTABLE.** CS-850's residual
  record asserts in BOTH directions, so merging CS-829 turned it RED with "these residuals
  were repaired; delete their entries". And zero live findings is now a GREEN state - before
  the anti-monotone repair, the CS-829 merge could not have been made green at all.

- **Decisions: none recorded as an ADR.** One operator round, at the start, selecting all
  four units and ruling CS-844 held.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But a disposition in this project's own
  notes is REVERSED: version 60's arithmetic refusal is NOT evidence that CS-G05 is
  unimplicated - 23529 struct type-word occurrences sit inside the refused records, 13.25 per
  cent of the census. Two agents disagreed on the number and BOTH were right; they measured
  at different offsets. Corrected in `docs/LEDGER.md` and `docs/item_notes.md`.

- **Failed paths: none abandoned.** CS-844 remains held by operator ruling, its worktree and
  three commits intact.

- **Next action: NONE IS FORCED.** CS-829 remains the head of the product path with the
  dependence now precisely located at `_payload_text`'s terminator verdict; the adversary's
  proposed route is to take the denominator from `_census_hits`, which no tag-list reader can
  shorten.

- **A MERGER MISTAKE WORTH KEEPING.** A `git push ... | tail` reported exit 0 while the push
  had been BLOCKED by the pre-push hook on a mypy error - the same pipeline-exit-code trap
  this project already records for `pytest` and `gh run watch`. And that mypy error reached
  main because the slice's verification table listed six checks and omitted mypy: A
  VERIFICATION TABLE PROVES WHAT IT LISTS, AND ITS POWER IS IN WHAT IT OMITS. A long table
  reads as a complete one.

- **The suite is 555s, NOT the 815-860s the last note projected.** The "more than doubling
  each session" projection did not hold; last session's figure was taken with several agents
  running concurrently. A trend extrapolated across different machine loads is not a trend.

- **DISK: the session-36 unknown is CLOSED.** Nothing is unaccounted for. Clockspeed is 0.1 GB
  of drive C:; the bulk is the user profile, a game install and a sibling project. Measured,
  not deleted.

---

## Session 38 - 2026-08-24 - the operator takes ALL FOUR units again; SIX items are graded by adversaries and SIX are REFUTED; four merge as improvements and NOTHING CLOSES

- **Shipped: NOTHING CLOSED, and that is the result rather than a shortfall.** CS-829, CS-839,
  CS-840, CS-841 and CS-842 MERGED as improvements and every one STAYS OPEN. CS-844 did NOT
  merge. Filed CS-845 through CS-850 and WIDENED CS-846 the same day. Detail in
  `docs/LEDGER.md` and `docs/item_notes.md`, not here.

- **THE HEADLINE: SIX OF SIX GRADED ITEMS WERE REFUTED, ALL ON ONE SHAPE.** The acceptance
  clause was satisfiable without achieving the thing the item exists for, every time. CS-842 is
  the cleanest specimen - deleting the criterion DID redden a test exactly as its acceptance
  demanded, and replacing that criterion with prose stating no criterion is recorded left 204
  tests green. **FIFTH CONSECUTIVE SESSION OF CLAUSES MET AND PROSE FALSE, and the first where
  it was caught on six items before anything reached the ledger.** Not one would have been
  caught by the agent that built it.

- **A GUARD WHOSE ERROR MESSAGE TEACHES THE ATTACK.** CS-840's red advised moving the date
  after a provenance verb; doing exactly that laundered a terminal verb and turned the heading
  green with its section still marked historical. **A guard that explains how to satisfy it is
  explaining how to defeat it wherever the two differ.** Rewrite the diagnostic, not only the
  check.

- **FIXED IN THE OWNER, ALIVE IN THE CONSUMER - the population defect's most consequential
  form yet.** The dated-heading rule was narrowed in the two files that STATE it and left
  verbatim in three files agents ACT on. The next doc-sync run would have skipped every live
  per-item note: CS-840's own defect relocated into the doc-sync agent's instructions.

- **A CORRECT REJECTION DOES NOT MAKE THE ALTERNATIVE CORRECT.** CS-841 refused a bait location
  on a sound measurement and moved it somewhere unmeasured - trading a loud CI flake for a
  quiet hole in the tripwire. The remedy is not to move it back; every property that made the
  new home invisible to CI also made it invisible to an arming predicate.

- **THE SUITE'S VERDICT DEPENDS ON HOW IT IS INVOKED, TWICE OVER.** On which shell runs it, and
  on whether it runs in parallel - the pre-push hook is serial and CI is not, so a whole class
  of defect is green locally and red nightly.

- **AN ADVERSARY SUPPLIED THE FIX, NOT ONLY THE REFUTATION.** CS-829's independent
  classification criterion - a tag list is one terminator wide when empty and otherwise at
  least one minimal tag plus a terminator - came from the lens that destroyed its predecessor.
  Adversaries are not only demolition.

- **THREE DEFECTS FIXED THAT BELONGED TO NO ITEM.** The CS-813 fourth leak, salvaged from an
  inherited worktree and RE-DERIVED rather than imported - and the re-derivation found that the
  oracle this project's own note PRESCRIBES cannot observe the leak it prescribes for. A ledger
  entry head that parsed to ZERO ids. A slash-command example wired to real closed ids, caught
  by a bound the merger had asked for and which fired on its first run.

- **Decisions: none recorded as an ADR.** Nine operator rulings across six rounds, every one
  changing the work. Asking remains how the session steers.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** Two things the MERGER stated were
  measured wrong and both are corrected in tracked files rather than quietly: CS-493 was never
  orphaned (only CS-494 was), and CS-829's repair changes no production behaviour at all - the
  decoder lines came from its predecessor.

- **Failed paths: none abandoned.** CS-844 is held rather than failed; its guard is good and
  its classifier is over-broad by one predictable case.

- **Next action: NONE IS FORCED.** CS-829 remains the head of the product path and its central
  defect is unsolved and now precisely stated: the criterion is arithmetic, but the population
  it grades is still chosen by the decoder. CS-850 is tier 1 and live on main.

- **WORKTREES: THE SEVEN INHERITED ONES ARE RESOLVED** after seven sessions. Every one had HEAD
  equal to its base with ZERO commits, so all their work was uncommitted - which is exactly why
  they kept reading as prunable. All committed to their own branches, all deregistered, nothing
  discarded. **`docs/item_notes.md` is at 86 per cent, up from 77**: six items filed, none
  closed, and closure is its only designed shrink.
