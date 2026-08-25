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

---

## Session 37 - 2026-08-23 - the operator takes ALL FOUR units; CS-830 is CLOSED, REFUTED and re-closed NARROWED, and an adversary is the only thing that caught it

- **Shipped: CS-830 (narrowed), CS-405, CS-833, CS-834, CS-835, CS-836, CS-837 and CS-838 CLOSED.
  Filed CS-839 through CS-844.** The proactive relocate pass STOOD DOWN on measurement rather than
  shipping. Detail in `docs/LEDGER.md`, not here.

- **THE OPERATOR ANSWERED NINE QUESTIONS ACROSS FOUR ROUNDS AND EVERY ROUND CHANGED THE WORK.**
  Session 36's finding applied deliberately again, and the compounding is the point: the first round
  set the scope, the second corrected a premise I had given wrong, the third ruled on a refutation
  that arrived mid-session. **Asking is not a phase at the start. It is how the session steers.**

- **THE HEADLINE: AN ADVERSARY REFUTED THE HEAD OF THE PRODUCT PATH AFTER IT HAD ALREADY MERGED.**
  CS-830's acceptance clause was MET - equality over every instance of all three container words,
  not a floor - and the thing the item existed for was NOT achieved for `SetProperty`. A mutant
  substituting a provably WRONG partition kept every library-backed test green. **THAT IS FOUR
  CONSECUTIVE SESSIONS OF CLAUSES MET AND PROSE FALSE, and the first time it was caught before the
  ledger entry rather than after.** Never let a close stand without an adversary behind it.

- **THE STRUCTURAL CAUSE IS REUSABLE AND WORTH MORE THAN THE ITEM: A POOLED GUARD HIDES ITS WORST
  MEMBER.** The evidence-strength check summed shapes across all three container words, so a word
  that was one hundred per cent derived vanished behind another word's self-delimiting bulk. Any
  guard that aggregates over a population it does not also grade PER MEMBER can be satisfied by its
  strongest member alone. The repair grades per word.

- **AND THE HONEST CLOSE IS A TEST THAT ASSERTS ITS OWN LIMIT SURVIVES.** No test can redden on the
  wrong partition without encoding a struct width whose only source is the module's own belief -
  the circularity the adversary caught in the synthetic fixture. So the narrowing SHIPS THE
  SURVIVAL AS AN ASSERTION, which gives the limit a failure direction: the day the corpus
  discriminates it, that test goes red and forces the record to narrow. Prefer this to a silent
  caveat.

- **THE POPULATION DEFECT HIT TWICE MORE AND BOTH TIMES IT WAS IN A BRIEF I WROTE.** I named three
  sites of the asset gloss and there were four. I gave an exclusion set covering one citation arm
  when the guard ships four. Session 36 recorded that the warning does not immunise the person
  writing it; this session it happened to the person QUOTING that warning into the brief.
  **THE TECHNIQUE THAT ACTUALLY WORKED: the builder loaded the guard AS A MODULE and used its own
  compiled patterns, instead of deriving the population by hand.** Do that.

- **A PERCENTAGE IS NOT PRESSURE UNTIL YOU READ THE BUDGET'S OWN RATIONALE.** I framed
  `docs/item_notes.md` at 75 per cent as urgent and cited ROADMAP.md as precedent. `tools/doc_budget.py`
  says the opposite in its own comment: the ceiling was chosen roughly 37 per cent above the file's
  landing size, THE HEADROOM IS THE POINT, and ROADMAP.md's failure is what this file's headroom
  exists to RELIEVE. The builder refused to ship and routed it back. **Closing eight items this
  session moved the file from 78 to 77 per cent - item CLOSURE is its designed shrink mechanism,
  and relocation cannot substitute for it** because every section is a live instruction for an OPEN
  item and `CLAUDE.md` forbids the archive from holding those.

- **CI WENT RED ON THE FIRST PUSH AND THE FAILURE HAD BEEN PREDICTED, LOCATED AND WRITTEN
  DOWN BEFORE IT.** CS-838's adversary measured that the newer ruff reworded the line the format
  check reads, and named the CI step where it would surface. Both went into the grant as
  disclosed risks; the SILENT half was filed as an item and the LOUD half was left as prose.
  **A measured, located, predicted failure is a work item with a due date, not a residual.**
  Fixed by PINNING ruff below 0.16 in `pyproject.toml` - not frozen, no grant needed - because
  the gate was correct on both versions and an unbounded dependency is what made the two
  toolchains differ. tier1 READ GREEN on the fix. **The gate BLOCKED correctly throughout**,
  because the grant put the verdict on ruff's EXIT CODE and never on its message.

- **Decisions: ADR 0009 recorded** - the `mInventoryPotential` FOURTH state. Detail in `docs/adr/`.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** Two measured facts contradicted BRIEFS I wrote,
  and both are recorded above rather than quietly corrected.

- **Failed paths: the relocate pass.** Attempted, refused by its own builder on a topology
  contradiction, and stood down by operator ruling. NOT retried - the finding is that it cannot
  work, not that it was done badly.

- **Next action: NONE IS FORCED.** CS-829 is now the head of the product path - the THIRD layer under
  CS-400's clause 1, and the one CS-405's fourth state names as its blocker. CS-843 is its natural
  companion: all 81 undiscriminated sets are of `StructProperty`, so CS-829 may settle both.

- **WORKTREES: FIVE OF SIX AGENTS THIS SESSION WERE CUT BEHIND THEIR STATED BASE.** One had no grant
  commit in history and would have edited a frozen file without authorisation had it not checked.
  Every dispatch ordered verify-and-fast-forward and every one that needed it said so. **Keep
  ordering it.** Six inherited worktrees remain untouched and unsalvaged; this session added its own,
  listed in the continuation prompt.
---
