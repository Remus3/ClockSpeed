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

## Session 45 - 2026-08-29 - CS-857 residuals 1 and 3 closed in TWO rounds, the first refuted by its own adversary; the item's severity framing measured FALSE and filed as CS-860

- **Shipped: NOTHING CLOSED. CS-857 STAYS OPEN.** Residuals 1 and 3 are closed, residuals 2
  and 4 are untouched, and the acceptance quantifies over a population that provably misses
  a shape. CS-860 filed. Detail in `docs/LEDGER.md` and
  `docs/item_notes/phase4-followups.md`, not here.

- **ROUND 1 REPAIRED THE FALSE CLEARANCE AND WAS ONE.** It gated the clearance on
  `raised == handler_name`, a COMPARISON OF SPELLINGS, and adversary L2 measured 15 shapes
  that name the same exception another way and still cleared while rendering the path. The
  fix for a guard that measured spelling measured a different spelling. Round 2 gates the
  clearance on a POSITIVE fact - the raise CONSTRUCTS a class the module declares - and no
  live graded verdict changes. **A NAIVE REORDER WOULD HAVE FALSELY REDDENED FIVE SITES**,
  one of them shipped, which is why both halves of the repair were required.

- **THE SEVERITY FRAMING IS MEASURED FALSE AND THAT IS THE SESSION'S BIGGEST RESULT.**
  Adversary L3 forced the measurement three agents had only read, under the project's own
  pytest configuration. The redactor emits two rule families - home path and account NAME -
  and the PLATFORM ACCOUNT ID AND WORLD NAME RENDER IN FULL. `OSError.__str__` renders
  `filename` through `%r`, doubling backslashes, so the home-path rule CANNOT FIRE on a
  chained cause at all. Containment on this machine is a naming accident. Filed as CS-860.

- **7 OF 7 MUTANTS KILLED**, including a true revert to round 1's own gate. In round 1 the
  census-reporter mutant SURVIVED and was reported as surviving rather than rounded up; the
  arm that kills it now exists.

- **Decisions: none recorded as an ADR.** The operator chose CS-857 residuals 1 and 3 as the
  unit and authorised `gh auth refresh`, which did not take - GitHub still reports no `user`
  scope, so the CI cause stays INFERRED.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But a sibling guard's `_verdict` names
  `ast.BoolOp` in a positive branch; measured and CLEARED - the channel splitter decomposes
  it upstream, so session 43's closure holds and nothing was filed.

- **Failed paths: the naive `classify` reorder** (5 false reds) and **round 1's spelling
  gate** (15 escapes). Both measured, both abandoned, both recorded.

- **THE PROCESS DEFECT THIS SESSION SURFACED: THE CANDIDATE WAS NEVER FROZEN FOR THE
  ADJUDICATOR.** The tree moved under it four times - 2 files, then 3, then 8, then 9, then
  11 - so four of its adverse findings were repaired WHILE IT WAS WRITING THE RULING THAT
  NAMED THEM, and no ruling it gave describes the tree that was committed. Section 5 makes
  the adjudicator's independence the point of the role, and independence is worth little
  against a target that edits itself mid-verdict. It also cost a whole-suite run: one
  straddled a guard rewrite, so collection read one guard and the census executed against
  another, and an exit 0 spanning four tree states says nothing about any of them. **FREEZE
  THE CANDIDATE FIRST, or dispatch the adjudicator against a worktree at a fixed SHA** - the
  read-only adversaries WERE pinned that way this session and none of them had the problem.
  Not filed as an item; it is a section 5 rule and section 5 owns it.

- **Next action: CS-857 residual 2** - a raise in a CALLEE of a handler is invisible to the
  population, and it is what blocks the acceptance. Derive a population that can see it.
  `docs/item_notes/phase4-followups.md` is at 99 per cent of budget with the split still due.

---

## Session 44 - 2026-08-28 - CS-857's channel shut at all five shipped sites; the census built to prove it carries a FALSE CLEARANCE, and three of four adversaries never reported

- **Shipped: NOTHING CLOSED. CS-857 STAYS OPEN.** The remedy, the derived census and the two
  corrected exemption reasons all merged. CS-858 and CS-859 were filed. Detail in
  `docs/LEDGER.md` and `docs/item_notes/phase4-followups.md`, not here.

- **THE CHANNEL IS SHUT WHERE IT WAS MEASURED LEAKING.** The five OSError-rooted sites chain
  `_pathless_cause(exc)` - an `OSError(exc.errno, exc.strerror)` clone with no `filename`.
  `tests/test_chained_cause.py` went `6 failed, 10 passed` to `16 passed` across that repair,
  and reintroducing `exc.filename` returns it to the original failure signature exactly.

- **THE HEADLINE: THE GUARD'S ONE POSITIVE VERDICT IS REACHABLE WHILE THE PATH RENDERS.**
  `classify` tests `FORM_SUPPRESSED` above `MEASURED_LEAK`, so `raise exc from None` inside
  `except OSError as exc` is graded `closed-suppressed` and the traceback still prints the
  filename - because `from None` suppresses the CONTEXT and the exception being raised is the
  binding itself. Latent, not live. The guard's own docstring says `from None` "genuinely
  closes the channel"; that is measured FALSE. **This project has now produced a false
  clearance in three consecutive sessions, each time inside the guard written to prevent the
  last one.**

- **A REPAIR CAN MAKE ITS OWN SITES UNPROVABLE.** `from _pathless_cause(exc)` is a `Call` the
  static rule cannot resolve, so the five sites moved from `measured-leak` to `unproven`, not
  to anything positive - and an adversary's no-op `from _identity(exc)` grades IDENTICALLY.
  The runtime module proves the repair; the census cannot see that it is genuine. Two halves,
  neither sufficient alone, and the leaks-reported-every-run warning silently stopped firing.

- **A LINE-NUMBER LIST DRIFTED THREE TIMES IN ONE SESSION** - stale at filing, broken by a
  re-derivation matching the closing `) from exc` line instead of the statement line, then
  moved by this item's own repair. Deleted from the note; `tests/chained_cause_guard.py` is
  now its owner. `CLAUDE.md` section 4 had the answer the whole time.

- **Decisions: none recorded as an ADR.** Four operator rounds: CS-857 as the unit; the
  section 5 shape; that the acceptance's disjunction does NOT permit closing with no
  `clockspeed/` change, so the remedy ships; and filing CS-858 plus CS-859.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But `tests/test_redaction_scope.py`'s
  chained-cause pointer was REPOINTED rather than renumbered: its successor line is the
  STAGE_HEADER raise, where the sentence it carries is FALSE, because `parse_header` takes
  bytes and its `HeaderError` has no filename to carry.

- **Failed paths: none abandoned.** Two merger claims were withdrawn under measurement - that
  four `workdir.py` pointers were stale, when the note had them right and a grep convention
  broke them; and that the census figures described the merged tree, when they described
  `209ce05`.

- **THREE OF FOUR ADVERSARIES NEVER REPORTED.** Two died on an expired OAuth token mid-run,
  one was stopped. The population lens returned REFUTED and found everything above. The
  false-clearance, does-it-reproduce and privacy lenses are UNRUN and their briefs stand.

- **Next action: RE-DISPATCH THE THREE REFUTERS THAT DIED.** Their briefs are in the session
  44 transcript and the lenses are named in the CS-857 note. The does-it-reproduce brief
  carries the one measurement three agents have now read and none has forced - whether
  `tests/conftest.py:665` actually scrubs a chained cause.

- **DOC BUDGET.** `docs/item_notes/phase4-followups.md` crossed 90 per cent this session and
  the residual record pushed it further. The next phase-4 round should expect to relocate.

---

## Session 43 - 2026-08-28 - the exception channel graded from both ends; BOTH guards refuted on the SAME defect, independently, in one session - a syntactic bare-name match sold as a population zero

- **Shipped: NOTHING CLOSED. CS-852 AND CS-855 BOTH STAY OPEN.** Both guards merged as
  improvements after adversarial refutation and repair. CS-857 is newly filed. Detail in
  `docs/LEDGER.md` and `docs/item_notes/phase4-followups.md`, not here.

- **THE HEADLINE: TWO GUARDS, BUILT INDEPENDENTLY BY DIFFERENT AGENTS AGAINST DIFFERENT
  CHANNELS, FAILED THE SAME WAY IN THE SAME SESSION.** CS-855's detector keyed on a bare
  name, so `kept = exc` defeated it. CS-852's `proven-vocabulary` resolved a callee by bare
  name, so a function merely NAMED `_checked_field` earned the proof. Neither author saw
  it; both adversaries found it inside twenty minutes. **A SYNTACTIC MATCH STANDING IN FOR
  A SEMANTIC PROPERTY, THEN REPORTED AS A POPULATION ZERO** is now the dominant failure
  shape in this project, and it is the case for the producer-never-grades rule made twice
  over in one sitting.

- **CS-852's FAILURE WAS WORSE IN KIND AND THE DISTINCTION IS WORTH KEEPING.** CS-855
  reported SILENCE; CS-852 returned POSITIVE FALSE PROOFS. A `proven-*` verdict is a
  clearance a later session will cite as evidence. Nine such paths existed, one of them
  grading `', '.join(free) or 'no recipe'` - LIVE HOUSE STYLE at four sites in
  `clockspeed/solve/` - as an annotation whose whole value space is numbers and flags.

- **A REAL SAVE-DERIVED VALUE REACHED `args` IN A REAL SHIPPED CLASS WITH THE GUARD GREEN
  AND THE REPORT BYTE-IDENTICAL.** `instance_name` off the save body at
  `clockspeed/save/objects.py:1747` into `ObjectFormatError`. That plant is now mutant M9
  and is killed.

- **A NEW CHANNEL WAS FOUND AND FILED RATHER THAN ABSORBED - CS-857.** `raise X(...) from
  exc` puts the CAUSE's text in the formatted traceback: the graded message renders
  redacted while the chained `OSError` renders the raw path beside it. **SEVERITY IS SPLIT
  AND THE SPLIT WAS MEASURED** - under pytest the CS-428 redactor at `tests/conftest.py:665`
  scrubs it, so it does NOT leak in the suite or either CI lane; it leaks on every
  rendering path that is not a pytest report. 7 of 11 CS-852 exemption keys sit on a
  chained raise, and two of their reasons call the cause "deliberately never rendered",
  true of `args` and false of the interpreter.

- **A THIRD ECHO MECHANISM NOBODY HAD RECORDED: THE FRAME ARGUMENT.** An exception handed
  to a callee renders in that callee's frame header under default flags, surviving
  `raise ... from None`. It is the construct `tests/test_exception_rendering.py:75` names
  as "the FIX" for CS-205. NOT a live leak - `repr()` of an OSError omits `filename` - but
  the remedy and the echo path are the same construct.

- **Decisions: none recorded as an ADR.** Two operator rounds: CS-852 gap 1 plus CS-855
  chosen as the unit, and the `chunks.py`/`usmap.py` vocabulary gate ruled REPAIR IT NOW.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But `clockspeed/save/world.py`'s
  safety paragraph was FALSE WHEN WRITTEN - it claimed all four parsers pin the
  closed-vocabulary guarantee with a planted-marker test. The obvious repair would have
  made it false in a NEW way, because header.py and objects.py have no refusal test either.
  Corrected to state per module what is actually pinned.

- **Failed paths: none abandoned.** Two merger claims were withdrawn under measurement -
  that the CS-855 acceptance is unsatisfiable, and that the long-carried 115 was a category
  error. 115 was correct when filed at `f19d1f2` and drifted to 117.

- **THREE MERGER ERRORS, ALL CAUGHT BY SOMEONE ELSE, ALL WORTH REPEATING.** A brief said
  "five ChunkError subclasses"; the slice MEASURED four and corrected it. A `grep "planted"`
  was offered as evidence of an absent control - a WORD search, not a PROPERTY search, and
  the file already pinned three other clauses. And an item-note anchor assumed the leaf's
  sections run in ID order; they do not, and the note would have landed in the wrong item.

- **Next action: NONE IS FORCED.** If CS-852 is resumed, the cheapest real gain is residual
  3 - replace the transcribed `ARGS_ROOTS` with a runtime census; an adversary already ran
  it and measured 47 == 47. CS-857 is unstarted and is the only tier-1 item here with a
  measured live rendering path.

- **DOC BUDGET IS TIGHTENING AGAIN.** `docs/item_notes/phase4-followups.md` finished at 90
  per cent. The ADR 0010 split bought one session of room and this session spent most of it.

---
