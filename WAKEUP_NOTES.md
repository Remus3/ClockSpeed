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

- **THREE RESIDUALS WERE FILED AS LIVENESS FLOORS - the exact defect that held CS-413 open for
  eight days - inside the entry that congratulates itself for escaping it.** CS-829 asked for
  one decoded value, CS-831 had no floor at all and could be satisfied by resolving nothing,
  CS-832 could close by editing one string in a table. An adjudicator caught all three. They now
  carry equalities and explicit non-zero clauses.

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

## Session 33 - 2026-08-22 - CS-823 CLOSES and takes a SECOND, unfiled escape with it; then an adversary refuted this session's own suite and SIX wrong hooks passed it

- **Shipped: CS-823 CLOSED. Filed CS-824.** Three commits. Detail in `docs/LEDGER.md`, not here.
  One frozen-file grant was issued, adjudicated and recorded in its OWN commit BEFORE any edit.

- **THE ITEM WAS FILED AS ONE ESCAPE AND CLOSED TWO.** `.githooks/pre-commit` ran the gate and took
  its whole decision from `$?`. Re-measured rather than inherited: truncated to 2368 lines, to 1
  line, and emptied, a staged em dash COMMITTED every time - exit 0, HEAD moved, ZERO bytes of
  stderr - against an intact control refusing with exit 1 and 576 bytes. 1020 of 2396 line-boundary
  prefixes compile, because the gate ends in a `__main__` guard.

- **THE SECOND ESCAPE WAS LIVE ON `main` AND NOBODY HAD FILED IT.** The CS-703 probe validates the
  `-c` invocation shape; the gate is invoked as a FILE. A four-line `sh` wrapper that delegates `-c`
  and exits 0 otherwise answers BOTH probe halves HONESTLY - it prints the computed token and
  returns 97, both measured - and never runs the gate. With it set, the em dash COMMITTED through
  the tracked hook. **Found by the ADJUDICATOR, not the builder, and believed only after being
  reproduced here.** It is the pre-commit twin of CS-819's silent-interpreter defect, and CS-703
  neither closed it nor claimed to.

- **THEN AN ADVERSARY REFUTED MY OWN SUITE AND THAT IS THE SESSION'S REAL LESSON.** The claim was
  that no wrong implementation could pass the 14 arms. SIX did. The sharpest -
  `grep -F "$CS_GATE_PASS" | tail -n 1` - keeps the declared pattern BYTE-IDENTICAL and changes only
  which line it is applied to. It has NO DEAD CODE and is exactly what a "make it less brittle" edit
  looks like. **The hook's own comment asserted the property that mutant violates, and no arm
  exercised that sentence.** Two arms were added and PROVEN to kill the survivors in a mirror, each
  mutation asserted to have LANDED first. **A GUARD'S COMMENT IS NOT A TEST, and a suite written by
  the person who wrote the guard tests the guard they MEANT to write.**

- **Decisions: no ADR. Fenced.** The banner check is an ANCHORED `case` pattern, both ends, only the
  two counts wild - NOT a prefix and NOT containment; the prefix version was built first and three
  of five adversarial gates passed it. Exact equality is unavailable rather than declined, because
  the counts vary and the gate is frozen, so the CS-703 exact-equality fence is untouched and still
  governs the PROBE. The captured stdout is RE-EMITTED rather than consumed - the opposite of
  CS-819 - because it carries the CS-209 coverage-skip lines, the channel that says detection was
  REDUCED. The CR strip stays even though it is an EQUIVALENT MUTANT on this toolchain.

- **Surprises: nothing contradicted `BOOTSTRAP.md`. Three things contradicted ME.** The designed fix
  I inherited said "require the banner" and a plain prefix test was too weak - measured. My section
  banner called the `gate_compiles` assertions "why these arms mean anything"; ablation says they are
  INERT today, and the sentence is rewritten in the tree. And I told the operator CS-413 was the
  item that makes a save's properties readable; its detail says the decode ALREADY LANDED and what is
  open is evidence quality. All three corrections are in tracked files.

- **Failed paths, so they are not retried.** A PREFIX test on the last line - refuted by measurement.
  Judging that stdout is non-empty, or counting its bytes, or matching the gate's NAME - all three
  are live survivors an adversary demonstrated, and all three are now killed. And the harness bash
  heredoc ate backslash escapes AGAIN, on a python payload this time; the Write tool is the answer,
  every time, and this is the SIXTH session it has cost.

- **THE PRODUCT PATH IS SHORTER THAN THE ROADMAP MAKES IT LOOK, and this is the most useful thing
  here for the next session.** CS-500 - the advisor - is blocked on CS-413; CS-413's own detail says
  CS-420, CS-421 and CS-422 carry its acceptance; CS-420 and CS-422 are CLOSED. **CS-421 is the ONLY
  item between this repo and the advisor.** Its open clause is the endianness question settled
  against something that is not this project's own writer. It is NOT small - 5712 lines of
  byte-order and value-anchoring machinery already exist across
  `tests/save/test_byte_order_status.py` and `tests/save/test_value_anchoring.py`, it carries FOUR
  fences, and route (b) shipped without closing it.

- **In flight: NOTHING half-done, but THE SESSION'S COMMITS ARE UNPUSHED and that is
  deliberate.** The operator DECLINED the push, so `main` is ahead of `origin/main` and NO CI
  RUN EXISTS for any commit this session produced. The count and the head SHA are deliberately
  not written here - read them with `git log --oneline origin/main..HEAD`, which cannot go
  stale the way a number in prose does. Working tree clean. The four
  pre-existing worktrees (CS-492 rounds seven to nine and the two-site spike) and branch
  `cs807-attribute-half` are UNTOUCHED, exactly as sessions 31 and 32 left them.

- **Next action: read `docs/history_notes.md` under CS-421 - detail, - status history and - fences
  BEFORE touching anything, then take CS-421.** Or ask the operator to revise the 2026-08-15 ruling:
  it says phase 5 waits until a record's properties can be READ, and they can be - the blocker has
  quietly become decode CORRECTNESS, which is a different claim and theirs to weigh.
