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

## Session 56 - 2026-09-01 - Both rulings OVERTURNED THE PREMISE THEY WERE ASKED ON, then CS-878 and CS-879 closed - a leak putting two absolute paths on the excepthook, and the guard excluding that file on a frozenness claim that was false of it

- **Shipped: CS-878 and CS-879 CLOSED.** CS-857 and CS-858 got RULINGS and both STAY OPEN;
  their entries say NOT A COMPLETION RECORD. No acceptance clause was changed anywhere this
  session, which is the CS-858 ruling applied to itself. Filed CS-880, CS-881, CS-882, CS-883.
  Suite 4050 -> 4152. Chained-raise grading 25 sites -> 36, and all 60 now reach a named
  bucket. Detail in `docs/LEDGER.md`, not here.

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

- **Next action: BUILD THE CS-857 SWEEP, not a phrase search.** It must grade the
  proposition across the tree rather than across one mapping, and
  `memory/a-guard-can-measure-spelling.md` says what a spelling search produces. The census it
  would sweep is the one CS-879 just repaired, and CS-881 records a shape that population still
  misses. After that, CS-883 is the cheapest of the three new items.


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

## Session 54 - 2026-09-01 - CS-867 CLOSED and the push block cleared; three adversaries refuted it and all three were right; the UI work opened and its first audit returned BLOCKED. The same fault shape appeared FIVE times and I wrote three of them

- **Shipped: CS-867 and CS-617.** Detail in `docs/LEDGER.md`, not here. CS-600 stays OPEN and
  its entries say NOT A COMPLETION RECORD. CS-868 through CS-871 untouched, CS-864 and CS-865
  untouched. CS-829 stays GATED behind CS-G05 - untouched this session.

- **THE HEADLINE: AN ASSERTION CAN PASS OVER A POPULATION THAT IS NOT THE ONE IT NAMES, AND
  KNOWING THAT DOES NOT STOP YOU WRITING ONE.** Five instances this session, in one causal
  family. The grammar called a field constant because it is constant in every save the
  corpus was derived from. Session 53's note called a run a fixed structure because three
  samples agreed - three samples of ONE world, minutes apart. My non-negotiable-12 arm
  asserted `text not in repr(table)` against a repr hand-written to emit eight integers. The
  dashboard markup asserted "scrolls sideways" about a box whose overflow is a function of
  viewport width. And my own guard arm searched for a bare `syncScrollRegions();` in a slice
  of a file that contained a DIFFERENT call site - written after I had diagnosed the other
  four. **VIGILANCE DID NOT CATCH THE FIFTH; A MUTATION MATRIX DID.** Run the mutants.

- **CS-867 WAS A COUNT READ AS A CONSTANT, AND IT IS CS-482 ONE LEVEL UP.** The body's final
  int32 counts object references, each two length-prefixed strings; it is 0 on every save the
  grammar came from, so an empty list left nothing to read. Three real (14,60) saves declare
  1 and the 120 leftover bytes are that one reference. Both times the corpus was then built
  to WRITE the constant, so it could not refute the assumption it encoded.

- **THREE ADVERSARIES REFUTED THE FIX AND EVERY FINDING WAS REAL.** Four rival readings also
  land 20 of 20 saves exactly, and two are unfalsifiable from this corpus - `{0: 17, 1: 3}`
  from one world. The privacy arm could not fail. The ceiling was pinned by nothing, and THE
  EDGE ARM I WROTE IN RESPONSE HAD THE SAME DEFECT the sibling's docstring warns about in
  terms. The independent oracle still carried the refuted reading, so the second opinion was
  wrong while the differential arms went on agreeing - AN ORACLE THAT AGREES BY NOT LOOKING
  IS NOT AN ORACLE.

- **Surprises: CI CAUGHT A CLASS THE LOCAL GATE STRUCTURALLY CANNOT.** `ruff check` refused a
  compound assertion (PT018) 27 seconds in. The pre-commit gate lints from a temp copy of the
  index bytes, so project per-file-ignores do not apply and it reports a large standing
  population of non-blocking findings - a green gate is NOT evidence about that CI step. **Run
  `python -m ruff check .` directly before pushing.** Also: `git add -A` swept a Playwright
  artifact into a commit; amended out, and `/.playwright-mcp/` is now gitignored.

- **The dashboard would not render and that is a standing obstacle, not a one-off.** It is
  HTTPS-only with a self-signed pair and neither the in-app browser nor Playwright will load
  it; trusting the cert is a security-settings change and is off the table. A plain-HTTP
  proxy in front of it is what made the audit possible - scratchpad only, audit only.

- **CS-617 CLOSED LAST, ON OPERATOR INSTRUCTION, AND IT IS THE SAME FAULT AGAIN - A FILE'S
  OWN RATIONALE MEASURING FALSE.** The comment said a body `padding-top` "pushes the page
  clear, so the strip covers nothing"; the padding is DOCUMENT flow and the band is fixed to
  the VIEWPORT, so it held only at scroll 0. The repair moves the SCROLLPORT below the band -
  `html` stops scrolling, the body becomes a fixed inset scroller - which makes the overlap
  geometrically impossible rather than merely unlikely. `app-region` was deliberately not
  touched: the rival fix was `pointer-events: none`, and whether Chromium still honours a
  drag region on a pointer-transparent element is unanswerable here. A FIX THAT CANNOT BREAK
  DRAGGING BEAT ONE THAT MIGHT, and an arm now forbids `pointer-events` in that CSS.

- **THE NODE SUITE RUNS WITHOUT `shell/node_modules`** - it imports only node builtins plus
  the two local libs, which is the purity partition working as designed. `node --test
  shell/test/*.test.js` from the REPO ROOT; from inside `shell/` the PreToolUse hook resolves
  its own path from cwd and every shell call dies until the directory is moved back with a
  non-shell tool.

- **Decisions: none recorded as an ADR.** Nothing contradicted `BOOTSTRAP.md`.

- **Failed paths: `.claude/launch.json` was written and immediately removed** - it would have
  spelled the dashboard port into a tracked file, which is exactly the violation CS-604 is
  open about. The port guard does not read JSON; the rule still does.

- **Next action: A THIRD CS-600 AUDIT, dispatched to an agent that wrote none of it.** Both
  UI repairs and the shell fix were written by the session that also wrote the arms guarding
  them, which is the one thing section 5 forbids. Two of the three audits so far returned
  BLOCKED and the second found defects the first had not, so a third is expected to find
  something rather than rubber-stamp. AFTER that, the save-reader follow-ups CS-868 to
  CS-871.

- **STILL OUTSTANDING FROM SESSION 49:** the six manual checks in `docs/OPERATIONS.md`
  section 8.3 read NOT RUN, and `shell/node_modules` does not exist. CS-617's repair does not
  need them, but VERIFYING THE DRAG ITSELF against a real Electron does, and that is named in
  its ledger entry as owed rather than claimed.
