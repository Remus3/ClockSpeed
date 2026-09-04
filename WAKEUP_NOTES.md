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

## Session 60 - 2026-09-04 - CS-891 CLOSED AS AN HONEST PARTIAL after FIVE refutations; the round's repair reproduced its own filed fault a FIFTH consecutive session and its own adversaries caught every instance, and the repair then would not fit under a data-hygiene ceiling

- **Shipped: CS-891 CLOSED AS AN HONEST PARTIAL**, the unmet conjunct named in the ledger in
  those words. Filed CS-897, CS-898 and CS-899, each measured before filing. Suite 4721 -> 4887;
  the citation guard alone went 162 -> 326 arms across two modules. **No acceptance clause was rewritten - an ELEVENTH consecutive session.**

- **THE PATTERN HELD A FIFTH TIME AND THE ROUND CAUGHT IT ITSELF.** The bare-path arm
  shipped green at 302 passed and was then refuted five ways: a unique suffix hit resolved a
  dead citation into `tests/` and into `.claude/` while DOCUMENTING that it needed no
  ratchet; the reason ceiling could be written as the length of its own table, making the
  budget a tautology with no number left in the diff; a forgiveness table named with a
  leading double underscore escaped the walk written to make escaping impossible; three
  non-vacuity floors could each be set to zero with nothing going red; and two legs the
  shape's own prose NAMES could be deleted without an arm noticing. All five repaired, each
  original mutant now dies.

- **THE SHARPEST ONE IS THAT THE SOURCE DENIED THE HOLE RATHER THAN OMITTING IT.** The
  suffix rung was documented as "a RESOLUTION rather than a forgiveness, so it needs no
  ratchet". Exactly one hit proves a path names A file and never THE intended file, which is
  the property the module's own trap 2 says a bare path does not carry. A false clearance is
  worse than a silence, and this one left no trace in a diff.

- **THE REPAIR DID NOT FIT.** It took `tests/test_docs_citations.py` to 273753 bytes against
  a 262144 ceiling that exists to catch a trimmed real game-data file. The builder REFUSED
  to raise it, correctly. The module was split into a derivation and its arms with the
  collected test-id list identical across the split, and the class-closing walks now run
  over a DERIVED module closure - a table relocated into the new module without registration
  reddens, while the old single-module walk stays blind. That is filed as CS-898 because the
  gate's own claim that it never trips on ordinary test code is now false and a second
  module sits at 96 per cent of the same ceiling.

- **Decisions: the guarded doc set went 21 -> 39 and it was a merger call, ruled legitimate
  by an adjudicator that verified the mechanism rather than the argument.** It is FORCED,
  not chosen: a new judged pattern must join the membership contract, which widens what
  counts as a carrier. Measured cost zero, and the seven flagship docs it adds - `CLAUDE.md`
  and `BOOTSTRAP.md` among them - carry no citation at all under the four pre-existing
  shapes. The standing consequence is real: a dead backticked path in `CLAUDE.md` now
  reddens the suite.

- **Surprises: THE ROADMAP BUDGET IS A WARN, NOT A HARD FAIL.** The previous handoff said
  the next item line breaks it. `tools/doc_budget.py` returns non-zero only on a HARD
  failure and says why in its own header - a warn that blocks a commit gets disabled and
  then enforces nothing. So three items were filed and the relocate pass is handed forward
  as measurably owed rather than suppressed to protect a soft number.

- **Failed paths, and four of them are mine.** My "independent" ladder control IMPORTED the
  module it graded and consumed its population boundary, so it was independent only in the
  rungs - which is exactly why it and the shipped arm agreed on seven AND both missed the
  same dead citation. I dismissed that citation early as out of population without asking
  whether the exemption's stated reason covered it; it does not, and it is now CS-897. I
  briefed a builder that a path root was untracked when the package carries it nested, and
  the builder measured me wrong and said so. And my own sweep regex made backticks OPTIONAL
  while I was arguing in the same session that the backtick was load-bearing.

- **In flight: nothing uncommitted.** Do NOT prune worktrees on a dirty reading - the count
  grew again this session and every sampled file in a dirty worktree is byte-identical to
  main at a stale base. Only a diff against main decides.

- **The repair was RE-ADJUDICATED from a frozen SHA and STANDS.** A first adjudicator ruled
  at `c5c3947`, I kept building, and it correctly refused to certify repairs it had not
  watched land - so a second pass was dispatched scoped to the three commits it could not
  see. Thirteen of thirteen filed mutants now die, each against a pre-repair control proving
  it was genuinely silent before. Tier 1 CI on the pushed head: SUCCESS in 8m44s.

- **THE SIGNATURE FAULT REPRODUCED A SEVENTH TIME, INSIDE THE SPLIT.** A ceiling in the
  module the split created can be rewritten as the length of its own table and survives -
  the exact tautology the repair closed two commits earlier. It is LATENT, not live, and it
  is recorded with three other residuals in `docs/LEDGER.md` under the session 60 entry.

- **THE NEXT ITEM ID FORCES A DECISION NOBODY HAS MADE, and that is why those four residuals
  carry no `CS-` id.** CS-899 was the last id the `CS-8nn` block holds. ADR 0011 says
  reaching CS-900 is "a `ROADMAP.md` ID-block question rather than a doc-topology one" and
  explicitly declines to answer it. **SETTLE THE ID BLOCK BEFORE FILING ANYTHING ELSE** -
  allocating CS-900 in passing answers by accident a question the project deferred on
  purpose.

- **Next action: settle the `CS-8nn` id-block question**, because it blocks every later
  filing, then CS-897 - small, and the SIXTH instance of the exact class CS-891 repaired
  five of. `ROADMAP.md` is 1305 bytes over its soft budget and the relocate pass is owed.

## Session 59 - 2026-09-03 - THREE ITEMS CLOSED and every one was REFUTED FIRST; every repair reproduced its own filed fault one level up, and CS-889's ratchet caught its own closure within minutes of shipping

- **Shipped: CS-888, CS-889 and CS-890 CLOSED** - CS-889 as an HONEST PARTIAL, stated in
  those words. Filed CS-892, CS-893, CS-894, CS-895, each from an adversary finding and each
  verified by the merger before filing. Also: CS-G05's payload independence MEASURED at n = 9
  after five sessions of that measurement going untaken, and CS-852's stale note corrected
  after three handoffs named it. Suite 4665 -> 4712. All gates green at the close: drift guard
  10 of 10, doc budget PASS with nothing over, ruff, ruff format, mypy 143 files.

- **NO ACCEPTANCE CLAUSE WAS REWRITTEN - a NINTH consecutive session.** CS-888 closed on the
  SECOND disjunct of its clause and the ledger says which, because the first disjunct - the
  consumption route - was REFUTED BY MEASUREMENT: three of the six immune modules already
  call the census `classify` and would have kept blanket cover, leaving 3 of 5 plants green.

- **EVERY REPAIR REPRODUCED ITS OWN FILED FAULT ONE LEVEL UP. Expect this; it is now three
  sessions running.** CS-888 abolished immunity-by-import and then granted module-wide
  immunity to anything holding a reason written about a different read. CS-889 built an arm
  against ungraded pointers and shipped a grandfather list with NO RATCHET - an adversary
  silenced every one of its findings with five table appends and got 153 passed, exit 0.
  CS-890 replaced a parity toggle with CommonMark fences and invented a new false positive
  while leaving inline code spans entirely unhandled.

- **THE SHARPEST FINDING: CS-889's PIN FOLLOWED THE ROT.** It froze `(carrier, path, line)`
  and nothing about what the line SAID, so a pinned pointer stays in range, stays non-blank,
  and is grandfathered forever while naming a different declaration. Those 48 sites were not
  "unverified pending review", they were immunised against detection - and a sibling then
  measured the base rate by content-checking five of them: ALL FIVE WERE WRONG. Repaired with
  a landing-line digest, chosen over an enclosing-symbol anchor BY MEASUREMENT: over twelve
  commits a digest catches 1 of 48 drifted sites and the anchor catches 0. The builder
  measured its own preference losing and said so.

- **CS-889's RATCHET CAUGHT ITS OWN CLOSURE.** Closing the item relocated its note to
  `docs/history_notes.md`, which took the last quoting-not-citing site out of the guarded set.
  The stale-entry contract reported the orphaned disposition on the next run; removing that
  reddened the budget arm, because the budget must be spent EXACTLY rather than merely be
  under it. Ceiling 55 -> 54.

- **THE ROUND'S OWN MERGE ROTTED A POINTER AND THE NEW ARM CAUGHT IT.** The CS-890 slice's 735
  insertions into `tools/drift_guard.py` pushed a cited line onto a blank one, minutes after
  shipping, in a file nobody thought was related. That is CS-889's thesis demonstrated on a
  case the round created rather than one it inherited.

- **THE CITATION GUARD READ MARKDOWN ONLY AND NOW READS EVERY TRACKED FILE** - 231 carriers,
  deliberately not a suffix list. That widening surfaced seven structurally invisible dead
  citations in `pyproject.toml` and two shell JavaScript files, five pointing at wrong
  content. The same pointer had been inside the population from one carrier and outside it
  from another.

- **Decisions: one ruling, and the LEDGER had already made it twice.** An adversary and the
  planner both recommended repairing dead line pointers inside CLOSED `docs/LEDGER.md`
  entries. I ruled NO: that file declares itself append-only and has settled this exact
  question twice in its own text, and its stated forward rule - "cite that module BY NAME,
  not by line" - is CS-889's forbid leg written down as practice a session before the item
  was filed. Those five take recorded dispositions instead. It makes the partial weaker and
  honest rather than stronger and invented.

- **Surprises: the handoff carried a STALE FACT as live.** It said
  `test_every_real_save_of_a_measured_pair_walks_to_the_end_of_its_body` is red on this
  machine because of an unmodelled 120-byte body tail. It PASSES; CS-867 closed on 2026-08-31
  and modelled that run. `docs/GATED.md` said the same in three places and is corrected.

- **Failed paths: three errors of mine, all caught by the agents I dispatched.** I told S2 to
  expect nine live instances when the ten stood - it derived ten and said so. I accused S2 of
  opening stale when `origin/main` genuinely was `dce2d0f` at its fetch, because my push was
  still in flight and I had written the brief as though local and origin were the same thing.
  And I told S6 main was RED on its seven when the widening had not landed, so its acceptance
  test would have passed whether or not it did the work - it built its own harness and got a
  real baseline instead.

- **In flight: nothing uncommitted.** No worktree holds unlanded work. **Do NOT prune
  worktrees on a dirty reading:** 23 of 34 show uncommitted changes and every sampled file is
  BYTE-IDENTICAL to main - they sit at stale bases. Only a diff against main decides.

- **Next action: CS-891, the bare-path citation form.** It was deliberately sequenced after
  CS-889 and they share a file, so it is now unblocked. Its five filed instances still cite a
  harness-side memory path that has never existed in this repo, and two further mentions of
  that path must be LEFT ALONE because they discuss it as the subject of a correction.


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
