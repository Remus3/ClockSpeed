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
## Session 94 - 2026-09-14 - five items closed, eight filed, and every defect that mattered was found by a gate or a mutation rather than by a green suite

- Shipped: CS-1039, CS-1054, CS-1041, CS-1042 and CS-1045 CLOSED. Detail in `docs/LEDGER.md`,
  not here. Eight items FILED - CS-1051 through CS-1059 - every one found by doing the work.
- In flight: nothing. Tree clean at `1b652b0`, everything pushed. CI green on `d24fd39`; the
  run on `1b652b0` was in progress at close and is the first thing to confirm.
- Decisions: no ADR. Four adjudications, each recorded where it binds. The wire may carry a
  GAME ASSET path - shipped content identical on every install, and the surface already
  published class paths on that justification - but guarded at the save seam by an ALLOWLIST,
  because `ObjectReference.object_path` is also the join key against a record's instance name
  and nothing structurally separates the two. `mTradingPostLevel` was RE-SITED to CS-1052 with
  its evidence bar raised rather than dropped from CS-1039's acceptance; rewriting an
  acceptance to match a delivery was refused by name.
- Surprises, and it is the finding of the session: THE WHOLE SUITE RAN GREEN - 3153 tests -
  OVER A READER THAT MATCHED ZERO RECORDS ON EVERY REAL SAVE. CS-1039's first candidate keyed
  the unlock carriers on C++ DECLARING class names taken from the shipped headers. A save is
  joined on the SAVE-SIDE type path, which UE writes without the A/U prefix and spells
  `BP_*_C` for a blueprint carrier. Not one key matched. Every synthetic arm passed.
- Surprises, second, AND THE REASONING ERROR IS THE REUSABLE PART: the wrong keys came from a
  note THIS SESSION wrote, which also said DO NOT RE-VERIFY. ADR 0016 was found to carry two
  false statements and that was taken as licence to prefer the headers over it wholesale. It
  is not. A header answers WHAT C++ DECLARES; a save answers WHAT IS IN THE FILE. **A document
  with false statements in it is not a document with no true measurements in it.**
- Surprises, third: THE SUITE WAS UNDER-MEASURING THE SAVE FORMAT THE OPERATOR PLAYS ON. A
  test-side tag walk expressed the legacy grammar only and read ZERO sites across all 80801
  records of version pair (60,14), which the shipped reader reads correctly at 400 of 400
  sampled records - and it reported that as EVIDENCE DESTROYED. A test oracle blind to a
  format accuses production loudly. A control had also silently degraded to a SKIP for the
  same cause. CS-1056 carries the unmeasured half forward.
- Surprises, fourth: a control PASSED inside the pre-push run and FAILED on the same commit,
  clean tree, 25 minutes later. One autosave landing between them changed WHICH version pair
  was graded, by a 3538-record margin. The operator plays while sessions run: a library-backed
  RED must be re-checked against the base commit before it is blamed on the work in hand, and
  a library-backed GREEN is evidence only about the library that existed when it ran.
- TWO BUILDERS REFUSED AN INSTRUCTION AND WERE RIGHT BOTH TIMES. One declined to invent a
  carrier key where the ADR records none - the exact defect that had refused its own first
  candidate. The other, handed a defect in its own merged work, wrote a tracer from scratch,
  proved its module called `copy_for_read` ZERO times, and refused to repair it; the writer was
  a `clockspeed.surface` process up 24 hours. That guard infers authorship from a wall-clock
  directory delta and is CS-1055 - and the write tracer its own message tells you to run DOES
  NOT EXIST in this repo.
- THREE MASKED CLAUSES, each found by mutation and none by review: a guard whose separator
  check was shadowed by its root check, a recipe-path refusal shadowed the same way, and a
  conservation arm that stayed green under a confident-zero mutant because zero gaps still
  conserves. If removing a check leaves every arm green, an earlier check is refusing the
  fixture first and your clause is graded by nothing.
- THE PRE-PUSH GATE BLOCKED FOUR TIMES AND ALL FOUR REFUSALS WERE CORRECT, and not one fault
  was visible to any targeted run: a closed item still declared in a lane scope, a citation
  broken across a line wrap reading as a truncated symbol, a redundant assertion mypy called
  unreachable, and a test file 10274 bytes over the ceiling that guards against a real-save
  slice being committed. The harness reported "exit code 0" for every one of those blocked
  pushes - read the log the command wrote, never the notification.
- Failed paths: do not re-file CS-1042 as blocked on a missing seam - collectables have crossed
  it all along via the NESTED `ObjectTable`, and the check that said otherwise read only
  `WorldModel`'s own field list. Do not raise the 262144-byte ceiling on any file under
  `tests/` - it is the only mechanical thing between this repo and a committed save.
- Watch - ANCHORING A NEW ROADMAP LINE ON A NEIGHBOURING ID INHERITS THAT ID'S PHASE. Done
  twice this session, caught twice by the membership rule. Anchor on the phase heading.
- Watch, second - `tests/test_docs_citations.py` has FOUR BYTES free and it has stopped being
  a warning: it forced a worse split of `test_struct_interior.py` because the clean three-way
  seam needed one dispositions entry that did not fit. That is CS-1057. `ROADMAP.md` is at 195
  percent of its soft budget and `docs/item_notes.md` hit its ceiling mid-session and needed a
  relocate to keep filing.
- Watch, third - TEN stale agent worktrees at eight distinct SHAs. Every one reads as merged
  because a worktree's HEAD is its base while work sits uncommitted. Classify by content; do
  not prune on that signal, and never delete the one the shell is standing in.
- Next action: confirm CI on `1b652b0`, then repair the CS-1043 and CS-1048 FILINGS before
  dispatching either - CS-1048's fog half has no subject in the code at all
  (`mFogOfWarRawData` has zero hits in any shipped module and `RecordProperties` forbids the
  bytes it needs), and CS-1043's budget-constant clause cannot redden while the constant is a
  literal. CS-1043 and CS-1048 are also the two that force `docs/ARCHITECTURE.md`, so they run
  in sequence with a merger doc-sync, never beside each other.

## Session 93 - 2026-09-13 - four items closed, a fifth given an id at closure, and the pre-push gate was right both times it refused

- Shipped: CS-1038, CS-1040, CS-1044 and CS-1049 CLOSED. The lane-start repair closed with NO
  id and was allocated CS-1050 at closure, so it has exactly one owner file. Detail in
  `docs/LEDGER.md`, not here.
- NOTE ON THE SESSION NUMBER, because it is a genuine conflict and was not resolved by
  picking: the operator named this session 85 in the closing brief. `WAKEUP_NOTES.md`'s own
  sequence ran 90, 91, 92, and `docs/history_notes.md` already holds a Session 85 dated
  2026-09-11. Writing 85 would have put two different sessions under one number, so this
  entry takes the successor of the file's own sequence and the conflict is recorded here
  rather than silently decided.
- In flight: nothing. Tree clean at `0ade931`, everything pushed.
- Decisions: ADR 0019 was adjudicated this session and is already committed - read it there,
  it is not restated here. Two rulings ride with it. FIRST, the map underlay: the map ships
  as a schematic ground plane with NO underlay. The save's fog-of-war raster - 1024x1024,
  proved structurally - may become a toggled layer ONLY after held-out containment of built
  placements, a sign-flip negative control that reddens, and cross-save invariance. Do NOT
  re-pitch a screen-captured or OBS-captured underlay as shipped data; an underlay registered
  to `WorldBounds`, which moves whenever the operator builds; or a fitted transform accepted
  on visual plausibility with no negative control. SECOND, node purity is NOT obtainable and
  is REPLACED rather than approximated: nodes plot unlabelled and shape-coded by class, and
  purity may become an OPERATOR ANNOTATION keyed by instance name. It is never presented as a
  measurement. CS-1040's ledger entry carries the declaration evidence that closes it.
- Surprises, and it is the finding of the session: THE PRE-PUSH GATE BLOCKED THE BATCH TWICE
  AND BOTH REFUSALS WERE CORRECT, and neither fault was visible to any targeted run. The
  first: the new classification block put an id at COLUMN ZERO, which is HEAD POSITION, so the
  work-item scan read it as an entry head it could not parse and reported UNACCOUNTED. That is
  a classifier that blinds the scan to itself - the file gets cleaner-looking by being less
  readable. The second: a correction record named an OPEN item in its HEAD without saying it
  was not a closure, which gave one id two owner files. A whole-suite gate caught both; every
  scoped run this session was green across both.
- Surprises, second: THE HARNESS REPORTED "exit code 0" FOR A BACKGROUNDED RUN WHOSE OWN LOG
  RECORDED `PYTEST_EXIT=1`. No exit code arriving from OUTSIDE the command is evidence about
  the command. Read the log the command wrote.
- Surprises, third: TWO subagents reported a slice GREEN and then corrected themselves to RED
  on a later read of their own logs. The correction came from the log, not from the claim.
- Watch - BYTE CEILINGS ARE NEARLY SPENT AND WANT A DELIBERATE RELOCATE, NOT A TRIM.
  `tests/test_docs_citations.py` has 4 bytes free under its ratchet. `docs/item_notes.md` has
  26 bytes free under its 16 KB budget. `ROADMAP.md` is at 193 percent of its 60 KB soft
  budget even after this session's closed rows came out. The next filing of any size hits one
  of the three. Relocate, never delete.
- Watch, second: FIVE line pointers had drifted and NOT ONE was re-cut at its new offset. Each
  was located by recomputing the frozen line's digest across the file and then converted to
  its ENCLOSING SYMBOL, which is what stops the next edit re-breaking it. One of the five had
  named the WRONG DECLARATION FROM BIRTH rather than merely going stale, so a pointer that
  resolves is not evidence the pointer was ever right.
- Failed paths: do not re-pitch narrowing the gated scan to headings or to a declared field -
  it is the denylist shape this project has measured leaking four times, and it fails OPEN on
  CS-G06. Do not re-pitch rewriting gate prose to unfence a row; that lever is now pinned shut
  by explicit MENTIONED entries. Do not re-derive node purity from a miner's rate or from a
  class name; CS-1040 closed it BY DECLARATION and the ledger records the specifier.
- Next action: CS-1042 - the uncollected set is the live records carrying transforms MINUS the
  collectable pairs CS-1038 now carries up, a SUBTRACTION and not a lookup, and the two halves
  of a pair are not both always present.

## Session 92 - 2026-09-13 - two anti-vacuity repairs closed, and the adversaries found the class in four more places

- Shipped: CS-1025 and CS-1020 CLOSED. Detail in docs/LEDGER.md, not here.
- In flight: nothing. Tree clean, whole suite green at the merge.
- Decisions: no ADR. One correction recorded inside the CS-1025 ledger entry: the filed
  acceptance was insufficient as worded - it demanded a needle be refused above count one,
  while the post-repair defeat mode is count ZERO, so the delivered arm enforces unique AND
  present and the disjoint constants are load-bearing rather than cosmetic.
- Surprises: nothing contradicted BOOTSTRAP.md. What did surprise, and it is the finding of
  the session: with the pre-fix constants the uniqueness helper makes the PRISTINE tree red
  and the MUTATED tree green. The arm's polarity is inverted, so the natural repair for that
  red is to drop a colliding value off the wire - which is the defect. An arm that rewards
  the defect was one fixture edit away from shipping.
- Failed paths: do not treat a uniqueness helper as the whole of CS-1025's fix - it was
  measured insufficient alone, in both the reasoning and a run. Do not repeat the "91 arms"
  figure from CS-1020's filed line as measurement; it appears once in the repository, has no
  collection behind it, and the floor measured at closure was 40 over a narrower population.
- Watch: FOUR privacy arms are structurally incapable of failing - `test_health.py` twice,
  `test_world.py` and `test_registry.py` - because the encoder doubles every backslash and
  the needle is a raw home-shaped path. A body that genuinely reflects a refused path passes
  all four. Filed as CS-1034, tier 1. This is the same trap session 91 hit once, in four more
  places, and it guards non-negotiables 3 and 12.
- CI WENT RED AND THEN GREEN ACROSS A DOC-ONLY COMMIT, WHICH IS THE POINT. The tip e2aff7a
  is GREEN - both jobs success. The commit before it, 9378975, was RED. Run 34791962600 on 9378975
  failed ONLY the "Duration against the budget" step: tier 1 took 491s against a 480s
  ceiling and a 420s budget. Every other step passed - character-set gate, ruff check,
  format check, doc budgets, drift guard, markdown links, type check AND unit tests. The
  ceiling was NOT raised; CS-1012's line forbids that by name. The measurement is worth
  more than the red: the same gate took 355s on 73f4e36 one session earlier and 493s and
  470s on the CS-1009 tree, so the observed spread on this workflow is now 355s to 493s -
  about 140 seconds, far wider than the roughly 20s spread CS-1012 was filed with. A
  ceiling 60s above budget cannot survive that spread whatever the tree does, which is
  evidence for the runner-side hypothesis CS-1012 already names as the first to test.
  THE STRONGEST POINT IS THE PAIR: 9378975 failed the gate and e2aff7a passed it, and the
  two differ by ONE DOC-ONLY COMMIT that adds no test and no code. A gate whose verdict
  flips across a change that cannot affect runtime is measuring the runner, not the tree.
  Do not read the green tip as the problem having gone away.
- Next action: CS-1034 - give every path-shaped privacy needle an oracle proven potent by a
  planted positive the arm FINDS, and redden the four arms on a reflecting body.

