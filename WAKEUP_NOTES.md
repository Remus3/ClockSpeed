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

## Session 36 - 2026-08-23 - the operator answers four questions; CS-486 and CS-831 both CLOSE, and the adjudicator-versus-adversary SPLIT is the finding

- **Shipped: CS-486 and CS-831 CLOSED. Filed CS-833 through CS-838**, plus seven smaller CS-831
  residuals and one Node 20 CI-action item in `BACKLOG.md`. Detail in `docs/LEDGER.md`, not here.
  The ROADMAP budget ruling landed too, so `ROADMAP.md` went from about a kilobyte of headroom to
  roughly a third of its budget used - and absorbed six new items without moving off that.

- **THE SESSION OPENED BY ASKING THE OPERATOR FOUR QUESTIONS AND ALL FOUR PAID.** This is session
  35's finding applied deliberately rather than rediscovered. Two answers closed items - the doc
  topology ruling and CS-486's home - and one AMENDED CS-831's acceptance mid-flight, which no
  agent may do. **CS-486 had sat since session 21 waiting on one decision nobody had asked for.**

- **THE TRANSFERABLE FINDING: AN ADJUDICATOR AND AN ADVERSARY ON THE SAME ARTIFACT RETURNED
  OPPOSITE VERDICTS, AND BOTH WERE RIGHT.** The adjudicator graded the six acceptance clauses and
  returned CLOSE, all MET. The adversary graded the RECORD around them and returned REFUTED on four
  blockers, two of which were live defects nothing in the suite caught. **The clauses were met and
  the prose was false, for the THIRD session running.** Never let a CLOSE stand without an
  adversary behind it - the two are not redundant, they read different things.

- **THE POPULATION DEFECT RECURRED TWICE INSIDE ONE ITEM, AND ONCE IT WAS MINE.** The first repair
  corrected a false claim in the test and left it standing at FOUR sites in `objects.py`, a file on
  its own write-list. I then wrote the repair brief naming THREE of those four sites, having warned
  it in the same brief about fixing the instance instead of the population. The second repair found
  my missing site. **The warning does not immunise the person writing it.**

- **THREE OF EIGHT NEW CORPUS NUMBERS IN A DOCSTRING WERE FALSE**, including a split invented to
  explain a total that was itself correct. The systemic fix, and it held: `CLAUDE.md` section 4
  already forbids restating a measured number in prose, so the second repair DELETED the figures
  and stated the shape. Neither file now carries a hardcoded corpus figure.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** A grammar-free reference count was measured
  IMPOSSIBLE without a second reader this project has declined to build; that is filed as CS-835
  rather than recorded as an adjective.

- **Failed paths: none abandoned.** Two repair passes were needed and both were kept.

- **THE MACHINE'S DISK FILLED DURING THE CLOSING RITUAL - 954G, 100 per cent, zero free.** Even a
  pipe write failed, so the ritual's suite step could not run at first. NOT CAUSED BY THIS REPO:
  the checkout is a few hundred megabytes. The harness temp tree measured 182G across roughly five
  thousand entries from six projects. **The operator scoped the cleanup to this session's own
  files**, which freed about 147M - four full repo copies the CS-831 adversaries made for
  out-of-tree mutation testing, which should never have outlived the session. **A mutation harness
  that copies the repo must delete the copy when it is done.** The suite then ran clean.

- **Next action: NONE IS FORCED. CI WAS READ AND IS GREEN** on all three pushed heads, so do NOT
  spend the first action re-checking it. Check FREE DISK SPACE first - roughly 772G is consumed
  outside the harness temp tree and was never measured. Then CS-830 is the head of the product
  path - the SECOND of the three layers under CS-400's clause 1, and the one holding the inventory
  arrays.

- **WORKTREES: SIX remain, the inherited ones, UNTOUCHED and still unsalvaged.** A seventh,
  `agent-a8b7284852bf73422`, was created this session and REMOVED on the operator's instruction
  before the session ended, along with its branch. It was safe to remove and the check is worth
  copying rather than the outcome: its work was already merged - the merger applied its patch and
  TWO repair passes then corrected the result - and a set difference over the test names proved
  main was a STRICT SUPERSET, three tests added by the repairs and none lost. What it still held
  was a superseded `objects.py` carrying the false prose both repairs removed, so keeping it was
  the live hazard: a later merge from it would have reintroduced every corrected sentence.
  **`--force` was required because the worktree was dirty, and dirty is exactly why the set
  difference came first.**
