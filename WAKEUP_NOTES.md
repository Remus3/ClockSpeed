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

## Session 57 - 2026-09-03 - FOUR ITEMS CLOSED and every one of them was REFUTED FIRST; the round's own repairs reproduced three of the four filed faults one level up, and EVERY repair builder corrected the merger

- **Shipped: CS-880, CS-881 and CS-886 CLOSED; CS-882 CLOSED AS AN HONEST PARTIAL** against an
  operator ruling. Filed CS-887, CS-888, CS-889 and CS-890. Suite 4571 -> 4665, all gates green
  at the close: mypy 143 files, ruff, ruff format, drift guard 10 of 10, doc budget.

- **NOTHING SHIPPED ON ITS FIRST VERSION. All four slices went green, passed a 4629-test
  authoritative run, and were then REFUTED by three adversary lenses and an adjudicator.** The
  green suite established that the arms RUN; it established nothing about what they MEASURE,
  and those are different properties. A repair round followed and all four were repaired.

- **THE FINDING OF THE SESSION: CS-880's ARM WAS GREEN WHILE ITS OWN DEFECT WAS LIVE.**
  `form_disagreements` tested the claim against derived forms by set INTERSECTION, so a leak at
  one of two sites was laundered by its clean sibling. Reintroducing the exact CS-857 defect at
  `clockspeed/save/workdir.py` line 585 left the arm reporting `DISAGREEMENTS: ()`. Repaired to
  subset containment. **AN ADJUDICATOR HAD GRADED THAT CLAUSE MET** - it perturbed the REASON
  where the adversary perturbed a SITE. Both directions are in the clause; only one worked. A
  single grader would have closed this item with the hole in it.

- **THREE OF THE FOUR SLICES REPRODUCED THEIR OWN FILED FAULT ONE LEVEL UP.** CS-880 was filed
  because a correction shipped a false claim, and its repair shipped a comment ("EACH SET IS
  NARROWER THAN THE CLAIM AND NEVER WIDER") that its own next sentence refutes. CS-881 was filed
  because an empty population satisfied a zero, and its denominator was satisfiable by the
  census's own control fixtures with both live subjects gone. CS-882 was filed against a listed
  exit-code table and shipped a listed outcome table under a docstring claiming three derived
  populations. **Expect this. Grade the repair as adversarially as the defect.**

- **EVERY REPAIR BUILDER CORRECTED THE MERGER, AND ALL FOUR WERE RIGHT.** R1 caught the merger
  citing `memory/pooled-guard-hides-its-worst-member.md`, which does NOT exist in the repo - it
  is HARNESS-SIDE ONLY and no tracked file may cite it; the repo owns the same shape at
  `memory/a-guard-can-be-green-by-accident.md` line 40. R2 REFUSED the merger's instruction to
  reuse `_TARGETED_STATEMENTS` wholesale, because it contains `ast.AugAssign` and `last += exc`
  stores what `__iadd__` returned - deriving it would INVENT a finding. R3 corrected the
  attribution of a false-red to `filename2` rather than a section reference, making it PERMANENT
  rather than incidental, and measured six affected counts where the brief said two. R4 found two
  dead citations beyond the three it was given.

- **Decisions: one operator ruling, and it is a fence.** `scripts/make_cert.py --help` EXITS 0.
  POSIX convention outranks the distinctness universal for that one pair. `EXIT_HELP = 0` is kept
  as a DECLARED constant so the outcome is not an anonymous code, and the exemption's membership
  is asserted by EQUALITY rather than containment so a second collision still reddens. **CS-882's
  acceptance clause is therefore NOT MET as a universal and the ledger says so.** The clause was
  NOT rewritten to read as satisfied - that is the session-56 decision holding for a seventh time.

- **In flight: nothing.** No worktree holds unlanded work. Four repair commits and four slice
  commits are merged; the round is closed.

- **Surprises: the census did NOT move under a merge that changed 14 files.** CS-882 shifted every
  line number in `scripts/make_cert.py` by +44 and not one derived value moved, because
  `Site.key` and `Copy.key` omit line numbers - a CS-857 decision absorbing a collision two
  sessions later. Nothing this round earned that.

- **Failed paths: none abandoned, but two dead ends worth naming.** The merger MANDATED that
  CS-880 import the census to avoid becoming an unrecorded adjudicator; that import bought the
  module BLANKET PERMANENT IMMUNITY from the adjudicator census, growing the immune set from four
  modules to six. Filed as CS-888. **Do not "fix" it by deleting the import** - unrecorded is
  worse than immune. Separately, a placeholder written `<module>::<symbol>` in a new item's prose
  was read by the citation resolver as a real citation and reddened two arms; write about a
  citation form without writing one.

- **WORKTREES OPENED STALE FOUR OF FOUR in the repair round**, on top of seven of nine in session
  56. This is not intermittent. Order verify-and-fast-forward on EVERY dispatch, every time.

- **Next action: CS-857 and CS-858 still need the OPERATOR** - see the two fences carried forward.
  The ordinary agent-completable work is CS-888, CS-889 and CS-890, all filed this session with
  their measurements attached.

## Session 56 - 2026-09-01 - FIVE ITEMS CLOSED, both requested rulings OVERTURNED THE PREMISE THEY WERE ASKED ON, and the items that moved CS-857 furthest were the ones that attacked the INSTRUMENT rather than the sites

- **Shipped: CS-878, CS-879, CS-883, CS-884 and CS-885 CLOSED. CS-857 and CS-858 got RULINGS
  and STAY OPEN**, their entries saying NOT A COMPLETION RECORD. **No acceptance clause was
  changed anywhere this session**, which is the CS-858 ruling applied to itself. Filed CS-880,
  CS-881 and CS-882, all still open. Suite 4050 -> 4571. Chained-raise grading 25 -> 39 sites
  with every one in a named bucket, `measured-leak` in the graded layer 3 -> ZERO, `unproven`
  24 -> 16, and the note census 38 -> 139 modules.

- **CS-884 AND CS-885 WERE FILED FROM MEASUREMENTS TAKEN WHILE DOING SOMETHING ELSE, AND THEY
  MOVED CS-857 FURTHER THAN THE SITE REPAIRS DID.** CS-884 gave the census a verdict that MEANS
  repaired - `closed-pathless`, resting on what a callee CONSTRUCTS, never on a name, placed
  THIRD in the order behind `measured-leak` and argued from a REAL collision. Every site
  CS-857 ever repaired had been sitting in `unproven`, a bucket that also holds three no-op
  shapes that leak. CS-885 then made the four copies of `_pathless_cause` compare on every run;
  it chose an arm over a shared owner because routing through an import would drop all eight
  `closed-pathless` sites at once, which would mean WIDENING the predicate that ISSUES a
  clearance on the privacy channel. CS-883 aligned the note census with the same taxonomy.

- **THE PROOF TECHNIQUE THAT KEPT WORKING, AND IT IS THE REAL CARRY-FORWARD: NOTHING WAS
  ESTABLISHED BY READING.** Every finding came from a plant, a control, a mutation or an
  execution. That includes every correction TO ME - the adjudicator EXECUTED a callee raise to
  turn "unproven" into "unestablished", and CS-885's builder MEASURED that a shared owner would
  silently drop eight clearances, the opposite of what my brief assumed.

- **CS-857 - two conjuncts MET, and the third is not merely unproven but UNESTABLISHED.** An
  adjudicator that built none of it planted a raise two levels down inside a callee of a
  handler, derived a population of ZERO, then EXECUTED it and watched the marker render
  through one chain link. It also executed the `UNPROVEN` shapes instead of reading them: a
  keyword no-op and a two-step forward BOTH RENDER while grading `unproven`, and 24 of 38
  graded sites carry that verdict backed only by hand reading - the method the clause forbids.
  **NEXT STEP IS CS-884**, whose sound form is already specified: every return in the callee's
  own scope a builtin-OSError call with two positional args, each an attribute read of
  `errno`/`strerror` off its own parameter. Then a frozen-file grant. Neither alone closes it.

- **THREE THINGS I GOT WRONG, corrected by the adjudicator and recorded so they are not
  carried forward.** CS-881 does NOT block CS-857 - a value stored in a local and raised after
  its handler exits measures ZERO chain links, so it is not a chained raise. The "33 wholly
  opaque callees" figure was pre-slice; it is 31. And **"shipped" DOES reach the four frozen
  `measured-leak` sites**: `tests/chained_cause_guard.py` calls its frozen bucket "Shipped
  code" and says the graded bucket is NOT shipped, so the narrow reading is refuted by the
  instrument I was quoting.

- **In flight: nothing.** No worktree holds work. The rulings are recorded; the ARMS they
  call for are not built, and that is the next session's work rather than an omission.

- **Decisions: two rulings, neither recorded as an ADR - that is the operator's call and
  was NOT taken.** (1) CS-857's `deliberately never rendered` conjunct STAYS. (2) No census
  count on an item line, AND no acceptance clause rewritten to avoid one; the enforceable
  artifact is a two-sided arm. The second binds CS-847, CS-860 and CS-807 as the operator
  asked. Both are in `docs/LEDGER.md` dated this day.

- **Surprises: the handoff's premise was wrong on BOTH items, and in the same direction.**
  CS-857's conjunct grades zero only inside the ONE mapping session 44 corrected;
  `tests/test_exception_rendering.py` and `tests/test_verify_env.py` each assert the same
  proposition in other words, the second with an ARM that asserts the shape is not flagged,
  so it DEFENDS the false claim and argues against the remedy this item shipped. Both were
  filed 2026-08-14 and survived two CS-857 commits, one of which edited the first file.
  Separately, CS-807's "fifteen" was measured WRONG ON ARRIVAL - the table held nineteen on
  the very commit that wrote the number - so the handoff's "stale in the wrong direction"
  framing is refuted and a revert would restore something that was never true.

- **Failed paths: rewriting an acceptance clause to make it falsifiable. SIX FOR SIX.** A
  doctrine was derived, and its own three applications were then REFUTED by an adversary
  that wrote none of them, each having dropped a condition - matching CS-854's three
  rewrites last session. A second adversary refuted the doctrine itself on four grounds; the
  decisive one is that an emptiness test cannot see an ANCHOR-SIZED population. Do NOT
  retry a clause rewrite. Also measured: a name in a doc is no more falsifiable than a
  count - the citation resolver stays GREEN when the binding it names becomes `pass`.

- **Second half, and the lesson that generalises: AN ARM THAT IS GREEN PROVES NOTHING UNTIL
  A MUTATION REDDENS IT.** CS-879's first version was green at 220 tests and was REFUTED by an
  adversary that wrote none of it: its sensitivity arm planted its only probe OUTSIDE the swept
  roots, where "unclassified" and "in neither population" are the SAME predicate, so one line in
  the helper it shared put a real site in neither population with the suite still green. Two
  further defects fell out of the same pass - the excluded bucket's stated reason was false of
  five of its seven modules, worse than the two-of-four CS-879 was filed against, and relabelling
  `clockspeed/save/` as fixtures dropped the header parser from grading with no arm objecting.
  All repaired; eight mutations, eight caught. CS-878's first version shipped TWO NEW RENDERING
  CHANNELS inside its own test and was caught by two tree-wide guards at the merge, not by a
  reviewer - the merger's instruction to skip the full suite on that slice is what let it through.

- **PROCESS FAULTS WORTH MORE THAN THE ITEMS.** (1) I handed the adjudicator an UNCOMMITTED
  WORKING TREE; `CLAUDE.md` section 5 requires a SHA or a worktree. It hashed five files before
  and after to prove the tree held still, so its ruling describes a definite state - that was
  its diligence covering my error. **PIN THE CANDIDATE.** (2) It named a COMMON-MODE RISK
  nobody else had: `tests/chained_cause_guard.py` is the SOLE enumerator of this population and
  was itself uncommitted-modified in the candidate, so two agents agreeing on the counts shows
  only that the instrument was reported faithfully. Nothing independently enumerates it.
  (3) **SEVEN OF SEVEN worktrees opened one commit stale** across both rounds. That is not an
  intermittent fault - order the verify-and-fast-forward every time.

- **THE PATTERN THAT MADE THIS ROUND WORK: every builder found the defect in its own work, and
  the tree's guards caught what they missed.** One nearly shipped a detector whose positive
  signal was an artifact and killed it by isolation; one's lint fix rendered a caught exception;
  one tripped a guard a SIBLING had built hours earlier by naming a field `cause`. Never let a
  repair be the last word on its own fault - it held four times out of four.

- **Next action: TAKE CS-880, CS-881 AND CS-882 - they are ordinary and need no ruling.**
  CS-880 is two exemption reasons asserting `from exc` where every site uses
  `from _pathless_cause(exc)`; CS-881 is a value stored in a local and raised AFTER its handler
  exits, which derives NOTHING (proven by planting the shape) and is NOT a CS-857 blocker
  because it measures zero chain links; CS-882 is argparse exiting 2 into the documented
  `EXIT_OPENSSL_FAILED`. **EVERYTHING ELSE LEFT NEEDS THE OPERATOR, NOT AN AGENT** - see the
  two fences below.


## Session 55 - 2026-09-01 - The third CS-600 audit found a MUST-FIX the first two missed, and every refuter that followed returned something real. CS-873, CS-874 and CS-875 closed. CS-872 stays open with the CSS-only space MEASURED closed rather than argued closed

- **Shipped: CS-873, CS-874, CS-875.** Detail in `docs/LEDGER.md`, not here. **CS-600 STAYS
  OPEN** and its entry says NOT A COMPLETION RECORD. CS-872 and CS-876 were filed this
  session and are OPEN. CS-829 stays GATED behind CS-G05, untouched. CS-868 to CS-871,
  CS-864 and CS-865 untouched.

- **THE HEADLINE: THE THIRD AUDIT WAS WORTH RUNNING, AND SO WAS EVERY REFUTATION AFTER IT.**
  Session 54 wrote the dashboard repairs, the shell repair AND the arms guarding all three,
  which is the one thing section 5 forbids. A `ui-auditor` that authored none of it returned
  BLOCKED on a defect two prior audits missed. Four read-only refuters then ran; **every one
  returned something real** - a confirmed regression, a second regression nobody had filed,
  an acceptance clause met by neither branch, and four arms blind to mutants that restore
  the exact defect they were written for.

- **CS-872 IS A NEGATIVE RESULT, AND ITS FIRST WRITE-UP OVER-STATED IT.** The composed page
  opens with no default keyboard scrolling, because a non-root scroller is not the default
  scroll target. Seven shapes were driven through one harness with perfect anti-correlation
  - every shape that scrolled on a cold PageDown put real content back under the band, and
  every one that kept the strip clear was keyboard-dead. **That is seven samples, not a
  closed space, and it was first written as `measured closed`.** What generalizes is
  STRUCTURAL and is an ARGUMENT rather than a measurement: in standards mode the root's
  `scrollTop`, `scrollHeight` and `clientHeight` ARE the viewport's, so positioning it out
  of flow leaves nothing in flow to scroll. **The harness is also not checked in, so nothing
  tracked here can re-run the seven shapes** - which makes the claim unprobeable by a later
  session, in a code comment where it reads as settled. An adjudicator caught all of this
  and the wording is now hedged. The cure remains a drag region the OS draws outside the web
  contents - a window option, not a stylesheet - and nothing here can grade it.

- **THE ADJUDICATOR FOUND A FIFTH DODGE INSIDE THE REPAIR THAT REMOVED FOUR.** A conditional
  group nested in the `body` rule - `@media (min-width: 1px) { top: 0; }` - survives the
  rewritten CS-874 grader green, because the declaration split takes the first colon and
  swallows the nested block, and at-rule preludes are collected at depth 0 only. Under CSS
  Nesting that restores the CS-617 defect. **CS-874 was filed for an arm claiming more than
  it enforced, and its own repair shipped a narrower enforcement than its comment claimed.**

- **A FILED FINDING'S SEVERITY WAS PARTLY REFUTED AND THE CORRECTED VERSION IS WHAT SHIPPED
  INTO THE RECORD.** The audit said 2472px was unreachable. False: a click anywhere or the
  wheel restores scrolling and a real scrollbar renders. Its figures were harness-local too.
  What survives is narrower and still MUST-FIX - the page OPENS keyboard-dead and every
  recovery route is mouse-only. **A confirmed finding can still carry a false sub-claim.**

- **CS-617 CLOSED WITH NEITHER BRANCH OF ITS OWN ACCEPTANCE MET.** Its line offered two
  routes - run the composed 5-phase audit, or record the composition as outstanding under
  CS-600. Neither happened, and deleting the item line took the obligation with it. A
  correction record is filed. **The item is NOT reopened and the repair is NOT withdrawn** -
  the band genuinely no longer covers content, re-measured at 4340 hit-test points.

- **THE SAME FAULT FAMILY AGAIN, AND MY OWN DISPATCH CARRIED IT.** I pointed an adversary at
  `tests/shell/test_shell_assets.py`, a file never modified in the range I asked it about.
  It re-derived the population from `git diff` and graded `shell/test/window.test.js`
  instead. **The failure mode showed up inside the dispatch hunting the failure mode**, and
  only survived because the brief told it not to trust a handed list.

- **FOUR BLIND ARMS, EACH REPRODUCED BY THE MERGER RATHER THAN RELAYED.** Indentation is not
  scope - a four-space call after the closing brace satisfies a `finally` check. A substring
  is not a call site. A substring is not a comparison - `===` to `!==` left an arm green. An
  oracle that consumes bytes without comparing its final offset agrees by not looking, which
  is the fault its own comment condemns; that is CS-876 and it is still OPEN.

- **Filing five item lines tipped `ROADMAP.md` over its soft budget, and the RELOCATE PASS
  THEN RAN.** The bytes were not where I first said. They were in phase 4, not phase 6: 29
  lines over 500 bytes held 31 per cent of all item bytes, and **26 of those 29 already
  carried a `detail:` pointer.** So the detail had been relocated long ago and the LINE was
  keeping a copy - CS-861's leaf runs to thousands of bytes and already stated everything
  its 1201-byte line repeated. **The pass was therefore mostly deleting a duplicate whose
  owner already held it**, which is the anti-drift rule working rather than a size cut. 30
  lines rewritten, and phase 6 got the leaf it had never had, with routing rows in both
  directions because guard (j) fails on either half missing.

- **THE PASS REFUSED TO HIT ITS OWN SIZE TARGET, WHICH WAS THE RIGHT CALL.** It stopped at
  95 per cent rather than the 91 it was asked for, because the remaining bulk is ACCEPTANCE
  text and shortening an acceptance clause changes what a test must prove. CS-401 is nine
  distinct assertions and was left whole. **A budget is not a reason to weaken a grading
  criterion.** Two adversaries then refuted the pass's own output and found four real
  defects in it, including one phrase DELETED rather than relocated and one acceptance
  clause that had gone vacuous - all four repaired before it landed.

- **ONE ACCEPTANCE CLAUSE WAS REWRITTEN THREE TIMES, EACH REWRITE WEAKENED IT, AND THE FIX
  WAS TO REVERT.** CS-854's original named three sites. The pass replaced them with `PROVEN
  NON-EMPTY` - a floor of ONE where the original was three. My repair replaced that with
  `CONTAINING EVERY SIBLING SITE THE DETAIL RECORDS`, and a third adversary refuted that too:
  `swept population` is defined nowhere in the repo, `sibling` is overloaded - shipped source
  at `tests/save/test_struct_interior.py` calls another group's members siblings - and both
  near-misses my parenthetical excluded are set-membership tests, **as is one of the three
  siblings**, so the obvious shape predicate drops it along with them. **The exclusion clause
  supplied the alibi.** The line is now byte-identical to its pre-pass wording, which names
  the three sites and says DERIVED rather than transcribed FROM THESE THREE LINE NUMBERS - the
  derive-versus-list reconciliation both rewrites broke. **When three attempts at a shorter
  wording each lower the bar, the wording was not the problem.** Cost of reverting: 36 bytes,
  against 3 KB of headroom. A budget is never a reason to weaken a grading criterion.

- **FOUR THINGS THE SWEEP SURFACED THAT NEED A RULING, NOT A REWRITE.** (1) CS-807's floor is
  now a parametrize table the closing change itself edits, and the old literal it replaced was
  stale in the wrong direction, so neither a revert nor the status quo is obviously right.
  (2) CS-857's `deliberately never rendered` conjunct grades ZERO records - it was discharged
  in session 44 - so it can never fail; delete it as discharged or re-point it. (3) CS-858 sits
  in direct tension with `CLAUDE.md` section 4: a hardcoded count in a doc is a lie with a
  timestamp, yet a numeric floor is what makes a graded line falsifiable. Decide once, then
  apply it to CS-847 and CS-860 as well. (4) CS-852's headline is STALE - it says the dataclass
  ships no `__repr__` and `clockspeed/save/chunks.py` defines one. That one predates this pass.

- **TWO THINGS THE PASS FLAGGED AND DID NOT RESOLVE.** `ROADMAP.md`'s header still carries
  correction history that belongs in `docs/history_notes.md` - relocating it was off that
  slice's write-list, and deleting it would break relocate-don't-delete. And **CS-840 now
  reads closable**: its line was left byte-identical rather than reworded into something
  true, because laundering a stale item into a current-looking one is worse than leaving it
  visibly stale. The measurement sits in its leaf where it is greppable.

- **A WORKTREE CAME UP THREE COMMITS STALE AGAIN, AND THE BRIEF IS WHAT CAUGHT IT.** The
  third builder was dispatched against a named base and its worktree opened at the
  session's starting commit instead, missing both commits its task was built on. It reset
  and said so, because the brief ordered a verify-and-fast-forward and a report of the SHA
  actually worked from. **Keep ordering that in every dispatch** - the two earlier builders
  opened at the right commit, so this fails INTERMITTENTLY rather than always, which is
  worse than a reliable fault.

- **Decisions: none recorded as an ADR.** Nothing contradicted `BOOTSTRAP.md`.

- **NEXT ACTION, BY OPERATOR INSTRUCTION AT THE END OF THIS SESSION: TAKE CS-857 AND
  CS-858.** Both surfaced in the acceptance sweep and both need a RULING before a repair,
  which is why they were not touched here. CS-857's `deliberately never rendered` conjunct
  grades ZERO records - discharged in session 44, so it can never fail; decide whether to
  delete it as discharged or re-point it. CS-858 sits in direct tension with `CLAUDE.md`
  section 4 - a hardcoded count in a doc is a lie with a timestamp, yet a numeric floor is
  what makes a graded line falsifiable; decide once and apply the same answer to CS-847,
  CS-860 and CS-807.

- **AFTER THOSE: CS-876, CS-868 to CS-871, CS-864 and CS-865 - and take them as ONE family
  rather than six items.** All six are arms grading a narrower population than they name,
  and the two closed this session make eight. A systemic answer is likely worth more than
  eight point repairs. **CS-872 needs a real Electron and cannot be closed here.**

- **STILL OUTSTANDING FROM SESSION 49:** the six manual checks in `docs/OPERATIONS.md`
  section 8.3 all read NOT RUN, and `shell/node_modules` does not exist in this clone. The
  drag itself has still never been exercised against a real Electron.

---
