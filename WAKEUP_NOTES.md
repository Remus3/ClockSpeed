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

## Session 41 - 2026-08-25 - `docs/item_notes.md` SPLIT per phase with an index; CS-856 closes; guard (j) ships; two controls were one edit away from grading an empty population

- **Shipped: CS-856 CLOSES.** `docs/item_notes.md` is now an index over `docs/item_notes/`,
  six leaves, 97 bodies moved byte-for-byte. Detail in `docs/LEDGER.md`, not here.
- **In flight: NOTHING.** No half-done work, no dirty file, no held branch beyond the four
  already preserved. **ADR 0010 was ACCEPTED by operator ruling the same day**, so the split
  is settled and binding. ADR 0009 remains `proposed` with no roadmap item.
- **Decisions: ADR 0010.** Three operator choices, each with its fence: split at the
  `CS-4nn`/`CS-8nn` seam rather than one 182 KB phase-4 leaf; ROADMAP item lines point at
  the INDEX and never at a leaf; record it as an ADR plus both topology tables.
- **Surprises: none contradicted `BOOTSTRAP.md`.** The measurement that DID change the
  design was that a literal per-phase split leaves 84 per cent of the content in one file,
  which was taken before any file was written and is why phase 4 is two leaves.
- **Failed paths: two, both mine, both caught by a contract rather than by review.** A
  byte-conservation check summed `for v in written` - the KEYS, not the values - and read as
  a catastrophic loss; and the `CS-492` disposition key was repointed at `phase4.md` by
  reasoning from the item id when the pointer actually sits in `phase4-followups.md`. Do not
  infer a body's leaf from the item id it names.
- **Next action: NONE IS FORCED.** CS-829 remains the head of the product path.

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

- **CI CAUGHT WHAT THE WHOLE LOCAL SUITE COULD NOT, AND THE LESSON IS THE SESSION'S THEME
  AGAIN.** The pre-push hook ran the full suite green - 2892 passed - and tier1 FAILED on the
  same commit with 33 findings. The new source-echo rule ran the runtime redactor over each
  whole source line; this machine's account name appears in no source at all,
  while CI's is `runner`, an ordinary English substring inside identifiers everywhere.
  **A CHECK THAT READS THE MACHINE IT RUNS ON REPORTS ABOUT THE MACHINE, NOT THE TREE** - and
  its note claimed it "cannot false-positive, because it fires on an actual value rather than
  on a shape". An actual value is still a SHAPE when the value is a common word. Reproduced
  locally with a CI-shaped redactor: 70 hits over 33 files before, 0 after, still firing on a
  planted home path. **Do not read a green local suite as evidence about the tree** - this is
  CS-839 generalised from which SHELL to which MACHINE.

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

