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

- **Next action: CS-876, then CS-868 to CS-871, CS-864 and CS-865 - and take them as ONE
  family rather than six items.** All six are arms grading a narrower population than they
  name, and the two closed this session make eight. A systemic answer is likely worth more
  than eight point repairs. **CS-872 needs a real Electron and cannot be closed here.**

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

---

## Session 53 - 2026-08-31 - CS-866 CLOSED and adjudicated ACCEPT WITH NAMED RESIDUE. An adversarial pass REFUTED CS-863's arms the day after they shipped, and a real save written mid-session turned the suite red on a body tail nothing models

- **Shipped: CS-866.** Detail in `docs/LEDGER.md`, not here. CS-867, CS-868, CS-869, CS-870
  and CS-871 filed. CS-864 and CS-865 untouched. CS-829 stays GATED behind CS-G05 - this was
  PREP and PREP never closes a gated item.

- **THE HEADLINE: A CACHE CAN ONLY RETURN AN ANSWER IT WAS GIVEN, SO ASK A QUESTION NEVER
  ASKED BEFORE.** Every CS-866 dynamic case now builds its body from a nonce derived from its
  own case identity, and the nonce moves the payload SIZES so it moves the REPORTED EXTENTS
  rather than only the bytes - which is what also defeats a cache keyed on the version pair
  alone. Two arms assert the freshness instead of leaving it arranged, and they build bytes
  without calling the second reading, because calling it would populate the very cache they
  guard.

- **THE ANTI-MONOTONE CONTROL IS WHAT MAKES THE CLAIM CHECKABLE.** Flatten the nonce to a
  constant 0 - strictly worse, and it reproduces the old head exactly - and the memo mutant
  scores 2 failed, 68 passed with ALL 20 dynamic cases GREEN. The two failures are the
  freshness arms. The nonce is doing the work and nothing else is.

- **THE ADJUDICATOR PUT SIX CACHE SHAPES THROUGH THE ARMS AND NONE SURVIVED** - keyed on the
  body triple, on the pair alone, on `len(body)`, on both, an `lru_cache`, and one placed on
  the shipped `objects.parse_body` itself. THE DECISIVE FACT IS NOT THE COUNT: the memo's
  FAILURE SET is byte-identical to the plain wrapper's, so a memo is now indistinguishable
  from no memo. It also broke the guard's circularity from OUTSIDE, by instrumenting
  `independent_records` and censusing every body handed to it - 31 enumerated, 20 dynamic, 0
  unaccounted synthetic bodies, 0 overlap.

- **Surprises: CS-863'S ARMS ARE REFUTED, ONE DAY AFTER THEY SHIPPED, by the pass its own
  session recorded as owed.** A memo over `_independent_sites_of` that reaches the shared tag
  ceiling through `tests/save/test_decode_oracles.py`'s `_walk_with_the_shipped_reader`
  leaves ALL 37 arms of `tests/save/test_struct_interior.py` green; delete the memo and it
  goes red. Two mechanisms and both need fixing: `_shared_tag_symbols` parses only its own
  module's source, so a ceiling read in ANOTHER module is invisible to the guard that
  asserts its absence BY NAME - which was the record's own reason for calling the surface
  derived; and `_run_ceiling_control` reads pristine and degraded over ONE body object, so
  under a memo the degraded call is always a cache hit. THE MEMO ALONE IS INVISIBLE AND THE
  CROSS-MODULE CALL ALONE IS CAUGHT - only the composition is lethal, which is why it is a
  hole and not a curiosity. Reproduced by a verifier that built its own mutants and never
  opened the adversary's directory. Filed as CS-868, CS-869 and CS-870.

- **AND THE SUITE IS RED ON SOMETHING NOBODY WROTE.** The operator played the pinned world
  forward while the session ran. Three saves of pair (14,60) written in the last quarter hour
  leave 120 bytes of their body unconsumed, and THE LEFTOVER RUN IS BYTE-IDENTICAL ACROSS ALL
  THREE while their record counts differ - 3226, 3299 and 3287 records over 455, 457 and 453
  levels. A run that does not move while the world around it does is a FIXED STRUCTURE, not
  world content. `objects.parse_body` already raises `WARN_UNPARSED_DATA_SECTION` for it, so
  non-negotiable 7 holds; what is red is the arm asserting exact consumption. Reproduced at
  the SESSION-52 head in three independent clean extractions, so it is nobody's regression.
  Filed as CS-867. **IT IS THE BODY TAIL AND NOT A PROPERTY PAYLOAD, so it is NOT CS-G05 and
  does not clear it** - `docs/GATED.md` carries a dated status saying so.

- **A DEAD CROSS-REFERENCE SHIPPED INSIDE THE COMMIT THAT REPAIRS THAT FAULT CLASS.** Two
  `:func:` roles named a function bound nowhere. `tests/test_docs_citations.py` matches
  `<path>.py::<name>` and NOT a Sphinx role, so no guard saw it - an adjudicator did. FIXED,
  not filed; the guard gap is CS-871. Two other sentences were narrowed: a process-scope
  freshness claim down to the module scope its guard actually measures, and the word "closed"
  down to "separated" where only the per-call route is closed.

- **Decisions: none recorded as an ADR.** Nothing contradicted `BOOTSTRAP.md`.

- **Failed paths: none abandoned.** One measurement was thrown away as wrong: a first library
  probe used `body_consumed == len(body)` where the arm uses
  `body_consumed == len(body) - body_prefix_width`, and reported all 20 saves short. The
  corrected predicate found the real 3.

- **Next action: OPEN THE UI AND UX WORK.** Operator instruction, given this session. The
  save-reader follow-ups CS-864, CS-865 and CS-867 through CS-871 stay OPEN and are not the
  next thing.

- **STILL OUTSTANDING FROM SESSION 49, UNTOUCHED:** the six manual checks in
  `docs/OPERATIONS.md` section 8.3 all still read NOT RUN, and `shell/node_modules` still
  does not exist in this clone.

---
