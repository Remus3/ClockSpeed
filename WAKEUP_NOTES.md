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


## Session 35 - 2026-08-23 - CS-421 AND CS-413 both CLOSE on operator rulings; eight review agents refuse four drafts and the transferable finding is that I fix the instance instead of the population

- **Shipped: CS-421 and CS-413 CLOSED. Filed CS-825, CS-826, CS-827, CS-828, CS-829, CS-830,
  CS-831, CS-832.** Three commits: `cb468e4`, `09344f4`, `a812690`. Detail in `docs/LEDGER.md`,
  not here. **PHASE 5 IS OPEN.** The advisor is no longer blocked on a decode-evidence question.

- **THE SESSION OPENED ON A QUESTION AND THE QUESTION WAS THE PRODUCT.** The operator asked what
  was gated on THEM. Enumerating it truthfully surfaced two acceptance clauses that no agent
  could amend, and both amendments closed an item that had been open for ten and eight sessions
  respectively. **Neither close needed new evidence.** What they needed was a ruling, and nobody
  had asked for one.

- **BOTH CLOSES WERE REFUSED BY REVIEW, AND BOTH TIMES THE SUBSTANCE WAS FINE AND THE RECORD WAS
  WRONG.** Two panels, eight agents, two DO-NOT-CLOSE and six REFUTED verdicts across four
  drafts. Every round the acceptance clauses graded MET against the real library, verified
  independently. Every round the prose around them carried a false sentence.

- **THE TRANSFERABLE FINDING, AND IT IS MECHANICAL RATHER THAN A KNOWLEDGE GAP: I FIX THE
  INSTANCE IN FRONT OF ME INSTEAD OF DERIVING THE POPULATION.** It happened four times in one
  session, in three different shapes. CS-421's close named the SMALLEST unsettled population as
  "the residual" and left 106454 values unfiled. CS-413's close named the LARGEST and left three
  regions unfiled. A false sentence about the walk was fixed at one of six sites, twice. The
  answer each time was a thirty-second grep or an `import` and a set difference, and I ran it
  only after an agent ran it for me. **BEFORE EDITING ANY INSTANCE OF A PHRASE, SWEEP THE TREE
  FOR EVERY INSTANCE. BEFORE FILING ANY RESIDUAL, ENUMERATE THE TABLE.**

- **I GAVE THE OPERATOR A FALSE PREMISE AND IT MOVED A RULING.** I stated that a building's
  inventory lives inside `StructProperty`'s interior. **MEASURED over the real library: no
  building record carries an `InventoryStack`.** A building holds an `ObjectProperty` REFERENCE
  to a separate inventory component; the stacks sit there inside an array. Inventory is behind
  THREE layers - CS-831, then CS-830, then CS-829. The operator had ruled CS-400's clause 1 on
  the one-layer map, was told, and re-ruled it BY SUBSTANCE: clause 1 waits until a building's
  inventory is actually readable. **That form is immune to my decomposition being wrong again,
  which is why it is worth copying.**

- **FOUR RESIDUALS WERE FILED AS LIVENESS FLOORS - the exact defect that held CS-413 open for
  eight days - inside the entry that congratulates itself for escaping it.** CS-829 asked for
  one decoded value, CS-831 had no floor at all and could be satisfied by resolving nothing,
  CS-832 could close by editing one string in a table, and CS-830 asked for one decoded
  element. An adjudicator caught three. **THE REPAIR PASS THEN FIXED THOSE THREE AND SKIPPED
  THE FOURTH**, and a late adversary caught that - this session's own transferable finding
  landing a fourth time, inside the fix for it. All four now carry equalities or explicit
  non-zero clauses. **THE POPULATION WAS THE FIVE ACCEPTANCE LINES AND I ENUMERATED THREE.**

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** Ground truth beat several things that were
  written down, all of them mine or inherited, and every correction is in a tracked file.

- **Failed paths: the repair passes.** Each of the first two generated new false sentences at
  roughly the rate it fixed old ones, because they were written under the same
  fix-what-you-can-see habit. The third worked because it started with a tree-wide sweep.

- **Next action: NONE IS FORCED.** CI must be read for `a812690`. Then the head of the queue is
  the ROADMAP budget ruling, which is the operator's, and the worktree salvage.


---

## Session 34 - 2026-08-23 - the held push LANDS; TWO of CS-421's own headline claims are measured FALSE; a SECOND independent int32 oracle ships

- **Shipped: NOTHING CLOSED, and that is the result rather than a shortfall.** CS-421 STAYS OPEN
  with a ledger record that closes nothing and grades no clause. Detail in `docs/LEDGER.md`, not
  here. The session's product is two measured corrections and the refutation of a stated CI risk.

- **THE PUSH SESSION 33 HELD IS DONE, AND THE REASON FOR HOLDING WAS REFUTED FIRST.** Session 33
  held on one stated risk: the new pre-commit guard's `tr -d` and anchored `case` had never run on
  dash, and CI tier2 runs ubuntu where `/bin/sh` IS dash. MEASURED before deciding, not after:
  the whole hook driven end to end under dash in a sandbox with real staged bytes is BYTE-IDENTICAL
  to bash on all three arms - clean file accepts with the banner at 0 bytes of stderr, a staged em
  dash blocks at exit 1 and 272 bytes, and a gate truncated to ONE LINE is caught by the CS-823
  repair at exit 1 and 1187 bytes - plus 15 of 15 banner-logic cases identical. Pre-push then ran
  the whole suite as its own gate at 2480 passed, 3 skipped, and tier1 `32620243989` is GREEN in
  4m31s on the pushed head. **The risk was real to state and false to act on, and only measurement
  could tell those apart.**

- **CS-421's FRAMING WAS STALE IN TWO PLACES AND A SESSION TAKING IT ON THE WRITTEN FRAMING WOULD
  HAVE REBUILT MACHINERY THAT EXISTS.** This is the session's real finding. FIRST, the "60.1 per
  cent backed by a declared width and nothing else" headline: a census re-derived from the live
  library reproduces every archived figure DIGIT FOR DIGIT, so the population never moved - the
  EVIDENCE TABLE did. CS-469 gave `IntProperty` and `FloatProperty` a second oracle, and width-only
  is now `objects.WIDTH_ONLY_VALUE_TYPES` alone at 4910 of 185382, **2.6 per cent**. SECOND, the
  one-command demonstration that the `">i"` flip "reddens only synthetic-fixture tests": FALSE.
  13 tests fail and **FIVE ARE LIBRARY-BACKED**, each confirmed by its own skip guard rather than
  by its name. **THE FALSE SENTENCE WAS SITTING IN THE DOCSTRING OF ONE OF THE TESTS THAT REFUTES
  IT** - the ADR 0008 shape, where a reader checking the claim by running the named mutant finds
  the thing it denies.

- **THE MUTANT WAS GRADED THE WAY THIS PROJECT REQUIRES, WHICH IS WHY THE RESULT IS BELIEVABLE.**
  Asserted live in the LOADED module rather than merely written to the file; floored against a
  full-suite green run at the same tree; and the same 13 names re-run 13 of 13 AFTER the revert, so
  a save library that moved mid-session could not be mistaken for the mutant's effect. The revert
  went through `git checkout --` rather than a rewrite, because the mutation script had already
  turned the file CRLF - the known harness trap arriving through my own tooling.

- **Decisions: no ADR. One fence.** Do not cite the `">i"` flip as an open gap without re-running
  it. Recorded as an eleventh entry in `memory/test-quality-failure-classes.md`: **A RECORDED
  DEMONSTRATION OF A GAP CAN OUTLIVE THE GAP.** The count was removed from that file's description
  and from its index hook at the same time - it had already drifted once, and `CLAUDE.md` section 4
  forbids restating a measured number in prose.

- **Surprises: nothing contradicted `BOOTSTRAP.md`. Two things contradicted CS-421's own docs**, and
  both corrections are in tracked files per `CLAUDE.md` section 8 - `docs/history_notes.md` under
  **CS-421 - detail**, the docstring in `tests/save/test_properties.py`, and the `ROADMAP.md` title,
  where the restated "60 per cent" was DELETED rather than updated so it cannot drift a third time.

- **Failed paths, so they are not retried.** A `pytest | tail` pipeline reports TAIL's exit code,
  not pytest's - it read 0 over a run that failed, which is the CS-703 shape arriving in my own
  harness. Capture `PYTEST_EXIT` explicitly. And the LEDGER citation guard caught a bare
  `test_properties.py::...` that does not resolve from the repo root; guarded docs need the full
  path.

- **THE CLOSE WENT TO AN ADJUDICATOR ON THE OPERATOR'S INSTRUCTION AND CAME BACK DO-NOT-CLOSE, AND
  IT REFUTED MY OWN ENTRY TWICE.** It graded none of its own work and ran its mutation in an
  OUT-OF-TREE copy so it never touched this tree. FIRST, MY LEDGER ENTRY COULD NOT COUNT: "five
  library-backed, six synthetic, one gate" is TWELVE, and the split is 5 + 7 + 1. SECOND, AND THIS
  IS THE ONE THAT MATTERS, **"five library-backed places" OVERSTATES INDEPENDENCE - it is ONE
  predicate at five sites.** `_int_oracle_holds` is single-owner by its own docstring and feeds the
  anchor, permutation and separability sweeps alike, and the fifth red spells the same conjunction
  inline; FOUR OF THE FIVE DISCLAIM THEIR OWN RESULT IN THEIR FAILURE TEXT, reporting that their
  baseline is red so the comparison means nothing. So my stated reason for adding no test - that it
  would be redundant against five arms - rests on a FALSE PREMISE. All of it re-verified here before
  it reached `docs/LEDGER.md`. The decisive ground was simpler than any of that:
  `objects.BYTE_ORDER_STATUSES` HAS NO WORD MEANING SETTLED, and every four-byte type ships one that
  denies it - so closing clause 3 would put the ledger in contradiction with the module, and clause 2
  is the clause that gave the module that fact. Fence 1 was CROSSED by my `UInt32Property` bullet.

- **THE SECOND ORACLE WAS BUILT ON THE OPERATOR'S INSTRUCTION, AND AN ADVERSARY THEN REFUTED ITS
  HEADLINE CLAIM - MINE, WRITTEN THE SAME DAY.** The artifact is a CONTINUITY oracle over
  `IntProperty` in `tests/save/test_value_anchoring.py`: it matches the same field across two saves
  and asks only whether it MOVED LESS as stored than read backwards, touching `_int_oracle_holds`
  nowhere. Measured: 12 snapshots, 34820 matched keys, 145 changed, **145 closer as stored against 0
  reversed**, inverting completely to 0 and 145 under the real `">i"` mutant. **THEN THE REFUTATION,
  RE-DERIVED HERE WITH AN INDEPENDENTLY WRITTEN PREDICATE: a rule inspecting NO MOVEMENT AT ALL -
  the magnitude prior applied to the pair's two endpoints - reproduces that verdict on 145 OF 145
  pairs, ZERO disagreements.** It is a second IMPLEMENTATION, not a second SIGNAL, and my
  "narrows three shared inputs to two" was unsupported.

- **THE FINDING WORTH KEEPING IS WHY NO PREDICATE COULD HAVE FIXED IT.** ZERO of the 145 changed
  values carry a non-zero as-read high byte at BOTH ends, and 135 of 145 differ only in their lowest
  byte. Every changed value in this corpus is small at one end, so EVERY correct byte-order oracle
  must agree with the magnitude prior on it. **Evidential independence is not a predicate-design
  problem here - it needs data this world does not contain.** Do not read a second oracle's
  existence as having supplied it.

- **THREE MORE SENTENCES OF MINE WERE MEASURED FALSE AND ARE CORRECTED IN THE TREE.** That time was
  the only symmetry-breaker - FALSE by construction, the adversary built a within-one-save SPACING
  statistic scoring 98 against 0. That the whole pattern histogram is invariant under reversal -
  FALSE, 202 patterns change count; what is invariant is the MULTISET OF COUNTS, and read literally
  the stronger sentence denied `_int_oracle_holds` can work. And "repeated saves of ONE world" -
  there are THREE world tokens here and 8 pairs match across two of them.

- **TEN OF THIRTEEN MUTANTS SURVIVED THE FIRST DRAFT; FIVE ARE NOW KILLED and each kill was
  re-verified with the mutation asserted to have LANDED.** Dropping the MAJORITY conjunct, never
  incrementing `closer_swapped`, stripping the sign from `_as_read_int32`, reversing only the OUTER
  two bytes, and caching a `None`. Three LIBRARY-FREE arms were added, which also give this work its
  first arms that RUN ON CI. **One survivor is an EQUIVALENT mutant and chasing it was refused** -
  the buckets partition, so the minority conjunct is implied; my docstring claimed the opposite and
  is corrected. Three others are population mutants whose only kill is a corpus-coupled floor, and
  all four are listed in the module.

- **A CORPUS-COUPLED RED WAS ALREADY LIVE AND IS CLOSED.** Both arms went RED - not skipped - on a
  library holding saves this grammar cannot read, and SEVEN of the nineteen files here are already
  at a save version outside `TAGGED_PAIRS`. Playing the game would have reddened the suite with no
  defect. No-evidence states now route to the same skip a missing library takes, which also stops a
  degenerate sweep reaching the cache.

- **WORKTREE PRUNE: ONE REMOVED, SIX KEPT, AND THE INHERITED NOTE THAT SENT ME THERE WAS WRONG IN A
  WAY THAT WOULD HAVE DESTROYED WORK.** The note said "FOUR WORKTREES REMAIN MERGED AND PRUNABLE"
  and then named THREE. Measured instead of trusted: **only `agent-a8f0774be4d10c1fe` was clean, and
  it is the only one removed.** Of the other two the note named, `agent-a1d0d1c85dd5bc8fc` holds
  1567 uncommitted insertions across `.githooks/commit-msg` - a FROZEN file - `docs/GATED.md` and
  `tests/test_commit_msg_gate.py`, and `agent-ac95f3565beb2209d` holds 1049 across
  `docs/history_notes.md` and `tests/test_docs_citations.py`. Both carry content that is NOT in
  main, checked file by file rather than inferred.

- **THE TRAP IS GENERAL AND IS THE REASON THIS IS WRITTEN DOWN.** `git merge-base --is-ancestor`
  reports ALL SEVEN of these worktrees as "merged into main", and that verdict is WORTHLESS here:
  their checked-out HEAD is the BASE commit the agent started from, which of course is in main,
  while the work sits UNCOMMITTED in the working tree. **A worktree is prunable only if it is
  ancestor-merged AND clean.** Six of the seven are dirty, so the six that remain - the four CS-492
  and spike worktrees plus those two - are ALL still holding work and none is prunable. Branch
  `worktree-agent-ab7fcd5c63f9193ea` (32a982c) is genuinely merged and its worktree is already gone,
  so only the branch is left to delete; `cs807-attribute-half` is NOT merged and stays.

- **Next action: THE REMAINING ROUTE IS THE OPERATOR'S ALONE.** Amend clause 3 to say what it now
  means - settled JOINTLY over the scored populations against the real library, with the per-type
  residual in shipped data - and file the `UInt32Property` residual as its own item. An adjudicator
  CANNOT grant that narrowing; narrowing an acceptance clause is fence 1's forbidden move. **What
  the build did NOT change is the evidence:** the common-mode signal is unnarrowed, and this corpus
  cannot separate two correct oracles at all. Otherwise take CS-817 / CS-821 / CS-824, which are
  smaller and independent.
