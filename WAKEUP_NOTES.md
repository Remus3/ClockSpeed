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

## Session 46 - 2026-08-29 - CS-860's first remedy REFUTED by five reviewers and BACKED OUT; the guard written to remove a naming accident was itself green by one, and it was caught before anything was claimed closed

- **Shipped: NOTHING CLOSED. CS-860 STAYS OPEN.** The home-path family widened, the two new
  shape rules were BACKED OUT, and the platform account id and the world name are now
  REGISTERED UNCOVERED with a stated reason each. The `CS-8nn` leaf split landed and CS-861
  was filed. Detail in `docs/LEDGER.md` and `docs/item_notes/phase4-followups-850.md`, not
  here.

- **THE HEADLINE: THE GUARD WAS GREEN BY ACCIDENT, INSIDE THE ITEM FILED TO REMOVE AN
  ACCIDENT.** Deleting the `quote` transform from the home spellings left the WHOLE SUITE
  GREEN, because the URL-quoted spellings were rescued by the ACCOUNT-NAME rule - the exact
  "naming accident, not a control" CS-860 exists to eliminate, reproduced one level up. Two
  reviewers found it independently, by different methods. **FIFTH CONSECUTIVE SESSION TO
  PRODUCE A FALSE CLEARANCE INSIDE THE GUARD BUILT TO PREVENT THE PREVIOUS ONE - AND THE
  FIRST CAUGHT BEFORE THE OPERATOR WAS TOLD ANYTHING HAD CLOSED.**

- **FIVE REVIEWERS, FIVE REFUTATIONS, ONE ROOT CAUSE.** The `account-id` and `world-name`
  shape rules were measured simultaneously TOO NARROW and TOO GREEDY: a world name with a
  space lost only its tail, one containing a quote or a question mark was untouched
  entirely, and a traceback frame line came back with the FUNCTION NAME ERASED. A repo test
  rendered `assert '<redacted-save>' == '<redacted-save>'` - two byte-identical sides. The
  segment character class was borrowed from `clockspeed/data/locate.py:187`, where it is
  correct because that redactor receives PATHS; this one receives arbitrary prose. **TOO
  NARROW AND TOO GREEDY ARE THE SAME KNOB, so it cannot be tuned.**

- **REGISTRATION MEANT NOTHING BEHAVIOURAL.** A class registered with a never-matching
  pattern and an empty arm satisfied every oracle arm, because the arms checked a TUPLE SLOT
  and a FUNCTION-NAME SUBSTRING and never whether a rule matches anything. Swapping two
  rules' class tags also left everything green. Both defects are closed: a covered class must
  now rewrite its own planted string into its own placeholder using only its own tagged
  rules, and each home spelling has its own arm.

- **THE NEW ARM LEAKED.** Its killing assertion rendered a value derived from the real home,
  because pytest renders the asserted EXPRESSION independently of the message - CS-850's
  defect, inside CS-860's own guard. Measured with both rule families hollowed: the report
  carried the bare account name VERBATIM. Fixed by binding scalars in three arms.

- **Decisions: ADR 0011 is ACCEPTED by operator ruling.** The operator also ruled CS-860's
  disposition: keep the home widening, back out the shape rules, register both classes
  uncovered with stated reasons, close the two grading defects.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But TWO sentences were measured false
  and were false at `afd85bd` as well, so they predate this session:
  `tests/assertion_rendering_guard.py` claimed the REPORT redactor recognises a MACHINE NAME,
  and `_ACCOUNT_VARIABLES` in `tests/conftest.py` reads `COMPUTERNAME` nowhere. ADR 0011
  carried two defects of its own - a leaf percentage that was wrong when written, and a
  byte-identity proof that does not reproduce without its hashing convention stated. All
  corrected.

- **Failed paths: the two shape rules, BACKED OUT rather than tuned.** Do not re-propose a
  character-class rule over a failure report. The two counter-examples that killed it are
  pinned as standing regression guards in `tests/test_report_redaction_classes.py`, and any
  rebuild must survive both: a redaction may rewrite a filename inside a frame line, it may
  never eat the frame around it, and it may never rewrite half a spaced name.

- **Next action: CS-860 NEEDS A MECHANISM THAT DOES NOT ASSUME ITS INPUT IS A PATH**, for the
  account id and the world name. Start from the two pinned counter-examples, not from the
  backed-out rules. **CS-861 IS OPEN AND UNSTARTED** - the same mechanism class in PRODUCTION
  code, in `clockspeed/data/locate.py`, with its reachability recorded UNVERIFIED and three
  of four tested account-directory shapes surviving the escaped rendering.

---

## Session 45 - 2026-08-29 - CS-857 residuals 1 and 3 closed in TWO rounds, the first refuted by its own adversary; the item's severity framing measured FALSE and filed as CS-860

- **Shipped: NOTHING CLOSED. CS-857 STAYS OPEN.** Residuals 1 and 3 are closed, residuals 2
  and 4 are untouched, and the acceptance quantifies over a population that provably misses
  a shape. CS-860 filed. Detail in `docs/LEDGER.md` and
  `docs/item_notes/phase4-followups-850.md`, not here.

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
  `docs/LEDGER.md` and `docs/item_notes/phase4-followups-850.md`, not here.

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
