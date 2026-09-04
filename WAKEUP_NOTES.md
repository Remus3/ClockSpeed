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

## Session 58 - 2026-09-03 - NO ITEM CLOSED AND NO CODE WRITTEN; a pre-dispatch measurement pass REFUTED the filed premise of two of the three items it was setting up, including one whose obvious repair would have shipped green with its own defect live

- **Shipped: NOTHING. Zero items closed, zero lines of product code, working tree was clean at
  the start and the only commit is documentation.** This was a Phase 0-to-2 session that never
  reached dispatch. Filed CS-891. Corrected the notes on CS-888, CS-889 and CS-890 in place.

- **WHY IT STOPPED: THE PLANNER WAS STOPPED, NOT COMPLETED.** One `planner` was dispatched in
  the background with the full measured brief and never returned a spec. Its transcript is
  saved and resumable by agent id. NO DECOMPOSITION EXISTS, so no builder was dispatched -
  starting slices without the disjointness proof is the decomposition error that produced
  CS-888 in the first place, and repeating it to look productive would have been the worse
  call.

- **THE SESSION'S ACTUAL PRODUCT IS THAT TWO OF THREE FILED PREMISES ARE NOW REFUTED, BEFORE
  ANY CODE WAS WRITTEN AGAINST THEM.** All three items were filed last session WITH their
  measurements attached, and two of those measurements did not survive re-derivation. That is
  the case for measuring a brief before building on it even when the brief is one session old
  and was itself written from measurement.

- **CS-889 IS THE IMPORTANT ONE: ITS OBVIOUS REPAIR WOULD HAVE SHIPPED GREEN WITH ITS OWN
  FILED DEFECT LIVE.** The item says the guard "grades only the module-and-symbol form". FALSE
  - `JUDGED_SHAPES` declares four and one already resolves line numbers. The arm judges the
  pointer's RANGE only, by explicit documented design, and declines bare basenames because
  doing otherwise once manufactured six phantom findings. `scripts/make_cert.py` is 546 lines,
  so all three make_cert pointers the item was filed on RESOLVE IN RANGE - they were dead by
  pointing at the wrong CONTENT. EXTENDING THE GUARD TO PYTHON MODULES, WHICH IS THE OBVIOUS
  READING OF THE ITEM, WOULD LEAVE ALL FIVE FILED INSTANCES GREEN. That is CS-880's exact
  failure shape caught one phase earlier than last session caught it.

- **AND THE GUARDED SET IS NOT LEAKING - I NEARLY FILED A FINDING THAT WAS NOT ONE.** Sweeping
  all 114 line pointers in tracked markdown outside code fences showed 22 non-resolving inside
  GUARDED docs with the suite green. Every one is correct behaviour: a declined bare basename,
  or an in-range pointer landing on a blank line. I checked six file lengths directly against
  their pointers rather than trusting the sweep. ZERO real violations.

- **CS-890's filed instance is ALREADY REPAIRED and its last dangling wikilink is not a link
  at all** - it is a TOML array-of-tables header inside a FENCED CODE BLOCK. So the clause is
  closeable as a universal, not the honest partial I first assumed and said so in writing to
  the planner before checking the fence. But the guard is broken WIDER than filed, proven by
  execution against a temp copy: a dangling wikilink in a leaf PASSES, and a ghost link in
  `MEMORY.md` ITSELF also PASSES, while the positive control - a real leaf unindexed - FAILS.
  The index may cite a leaf that does not exist and guard (b) is green.

- **CS-888 CONFIRMED AND SHARPENED, PROVEN BY EXECUTION WITH NO FILE WRITES.**
  `adjudicators_in_sources` takes a sources mapping, so plants pass in memory. Identical bytes:
  unrecorded names the module in a non-importer, and unrecorded is EMPTY in all five immune
  ones. The graded population is TWO. The sharpest fact is not in the filing: the one module
  immunity actually removes from grading, `tests/pathless_clone_guard.py`, imports six PRIVATE
  names and its own docstring says it MIRRORS the census predicate deliberately. Mirroring is
  the opposite of deferring, so a consumption rule SPLITS the six rather than clearing them.

- **Decisions: two, both applications of standing rules rather than new ones.** (1) CS-889's
  item LINE still carries the refuted premise and CS-890's still says tier 1. NEITHER WAS
  REWRITTEN - session 56's no-clause-rewrite decision holding for an eighth time; the
  corrections are in the item notes and the drift is recorded here. (2) The bare-path citation
  class was filed as CS-891 rather than folded into CS-889, because CS-889's clause is about
  the line-number form and widening an item past its own clause is how a clause stops being
  falsifiable.

- **In flight: nothing uncommitted.** No worktree holds work. The three items are open and
  unstarted; the planner's transcript is the only unlanded artifact and it is resumable.

- **Failed paths: one, and it was mine.** I wrote to the planner that CS-890 could only close
  as an honest partial, then found the code fence and corrected myself to it in a second
  message. Read the fence before pricing the item.

- **Next action: re-dispatch the planner for the decomposition, then run the round.** CS-888
  needs no worktree - its harness is a sources mapping. CS-889 must be graded against its own
  five filed instances before anything else. CS-890 needs two directions and a fenced-code
  exclusion, and should be re-tiered at dispatch.

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
