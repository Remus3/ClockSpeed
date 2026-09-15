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
## Session 96 - 2026-09-14 - tier 1 went 583s to a worst job of 310s, and every defect that shipped was caught by a gate or an adversary AFTER the targeted suites were green

- Shipped: CS-1060 CLOSED by adjudication, CS-1072 FILED AND CLOSED in one record. CS-1070,
  CS-1071 and CS-1073 filed. Detail in `docs/LEDGER.md`, not here.
- THE MEASUREMENT KILLED THE OBVIOUS REPAIR. Tier 1's fast shard was bound by TOTAL CPU
  divided by worker count, not by any one slow file - 607.7 CPU-seconds against a 108.7s
  wall, and `607.7 x 3.4 / 4` predicted 517s against the 540s the runner spent. So trimming
  the largest test buys a QUARTER of its own cost in wall time. A third shard was the only
  lever, which is what CS-1060 said and why it forbade tuning a threshold.
- READ THE CLASS POLARITY BEFORE JUDGING A SPREAD. The merger believed three readings
  spanning 43s meant the slow runner class had been missed. BACKWARDS: a 49-reading class
  model puts the slow class at about 78 per cent of draws, so a tight cluster at the TOP of
  the distribution IS the slow class. Three readings alone would NOT have discharged the
  clause and the ledger entry says so.
- A VERDICT CUTS BACKWARDS AS WELL AS FORWARDS. An adjudicator ruled that
  `tests/solve/test_phase3_gate.py` be repaired inside CS-1060 on an 87s runner figure. That
  figure was measured BEFORE the CS-302 trim landed in the same commit it was grading. The
  gate now falls out of the slowest-15 by itself and the child sweep is flat at n=2/4/8. NO
  CHANGE WAS MADE, and that is the result. Re-check a ruling's own range, not just later
  commits.
- THE TOKEN ARMS COULD NOT SEE COLLECTION. Two counter-examples passed every partition arm
  at 143 green: a node-id target paired with a byte-identical `--ignore=` ran one test in TWO
  shards, because `--ignore` matches a path and silently no-ops on a node id; and a
  `-m 'not slow'` in pyproject addopts, workflow untouched, left 12 tests in NO shard. Both
  found by an adversary after a green suite, a green CI run and four green slices.
- A COMMENT SAYING MUST NOT IS NOT A GUARD. `assert _ORACLE_GROWTH_CHAIN > _SMALL_CHAIN`
  could not fail in any source state, while the one regression its own comment forbade in
  capitals - reverting CS-1060's trim - was GREEN.
- REMOVING AN APOLOGY IS NOT THE SAME EDIT AS REMOVING THE FACT IT APOLOGISED FOR. The
  README rewrite was briefed to drop self-deprecation and introduced THREE overclaims doing
  it, all caught by a UI/UX audit before commit. Worst: `clockspeed/progress/` and
  `advisor/` were listed beside `audit/` under one heading, and the empty two - ZERO defs
  between them against 92 - borrowed the full one's credibility.
- THE SAVE SHARD IS NOW THE BINDING READING at 306-310s against the 320s figure CS-1060
  closed on. It was never partitioned. CS-1073 must land BEFORE CS-1068, which is open and
  grows that directory. TEN SECONDS OF MARGIN.
- Doc budgets are now BLOCKING rather than warning: the item-notes leaf had 1115 bytes free
  before CS-1060's closed note was relocated, and `docs/item_notes.md` has about 70. CS-1062
  and CS-971 own these and the next filing session hits the wall.

## Session 95 - 2026-09-14 - CI was red for the RUNNER rather than the tree, and every defect this session shipped was caught by a gate after the targeted suites were green

- Shipped: nothing CLOSED. Three items FILED - CS-1060, CS-1061, CS-1062 - and three
  filings REPAIRED: CS-1012, CS-1043, CS-1048. Detail in the item notes, not here.
- In flight: nothing. Tree clean at `c307948`, everything pushed, whole suite green
  through the pre-push hook at 7668 passed. CI on `c307948` was in progress at close.
- Decisions: no ADR. One adjudication, recorded in CS-1012's own section where it binds.
- THE SESSION OPENED ON A RED CI AND THE RED WAS NOT ABOUT THE TREE. Tier 1 failed its
  duration gate on `8165c35` at 505s against a 480s ceiling. That commit is TWO MARKDOWN
  FILES. A rerun of the same SHA passed at 289s. Two attempts differing in nothing a
  commit can express, 222 seconds apart.
- THE CONTROL THAT SETTLED IT RUNS NO REPO CODE. `Install toolchain` is a pinned pip
  install with byte-identical input; it moved 7s to 12s across those attempts. A cache-miss
  explanation was raised against it and CHECKED rather than waved off - both attempts print
  `Using cached` for the same twelve packages and `Downloading` for the same one.
- AND THE SAME CONTROL CHOSE THE REPAIR. Toolchain moved 1.714x while the unit step moved
  1.774x - agreeing to 3.4 per cent. A step that runs none of this repo's code predicts the
  suite's own slowdown, which is an in-job calibration divisor measured rather than argued.
- Surprises: CS-1012's OWN PREMISE WAS FALSE. Its line said the spread on one tree is about
  20s, from a single rerun pair. A second pair reads 23s apart against this one's 222s, so
  the pool is TWO-CLASS rather than continuously noisy and a sigma-banded threshold grades
  which class it landed on. The published feasibility rule on M=511, N=222 returns an EMPTY
  window: wall-clock gating is INFEASIBLE at this lane length, not mis-tuned. That is
  CS-1060, and CS-1012 cannot be built before it.
- Surprises, second, AND IT IS THE REUSABLE ONE: THE INDEX SAID THE OPPOSITE OF THE RULE.
  `docs/item_notes.md` routed the `CS-10nn` block to `phase4.md`. The membership rule sends
  every phase 4 ID at 900 or higher to the `CS-9nn` leaf, which that leaf's own header
  states and which every existing `CS-105x` row already did. One sentence disagreed with
  the code, with the leaf and with its own table - and a session that checked the phase
  carefully still got the leaf wrong by trusting it. A restated rule is a rule that drifts.
- THE PRE-PUSH GATE BLOCKED ONCE AND IT WAS RIGHT, and the targeted runs were green on the
  same tree: the citation suites and the drift guard both passed the misrouted sections.
  Only `test_every_section_sits_in_the_leaf_the_membership_rule_names` saw it. THE HARNESS
  REPORTED EXIT CODE 0 FOR THAT BLOCKED PUSH - fifth measurement across two sessions, now
  in harness memory. Read the log the command wrote and confirm the remote SHA moved.
- THE CITATION GUARD CAUGHT FOUR OF MY OWN CITATIONS AND WAS RIGHT FOUR TIMES: a future
  test name binding nowhere, a line pointer at a tracked module, a module that does not
  exist yet, and a gitignored artifact. All four were repaired by REPHRASING - not one
  disposition entry, not one ceiling raise, because `tests/test_docs_citations.py` still
  has four bytes free.
- Failed paths: do not keep CS-1048's registration clause with the annotation half. The
  item note at HEAD proposed exactly that on the grounds `WorldBounds` exists, which it
  does - but the transform's subject is the underlay's own grid, so the clause has no
  subject without the raster either. It went to CS-1061 with the fog.
- Watch - `docs/item_notes.md` reached 16338 of 16384 bytes THIS SESSION, 46 free, and was
  trimmed back to 134 only by shortening this session's own addition. That is a reprieve,
  not a repair. The next session to file an item cannot add its routing row without
  unrelated surgery first. CS-1062 carries it.
- Watch, second - `ROADMAP.md` is at 201 percent of its soft budget, up from 196.
- Watch, third - TEN stale agent worktrees remain, still reading as merged because a
  worktree's HEAD is its base while work sits uncommitted. Classify by content.
- Next action: confirm CI on `c307948`, then CS-1062 FIRST - the index relocation - because
  every other item in flight needs to file a routing row and cannot. After it, CS-1043 and
  CS-1048 are both repaired and dispatchable; they still force `docs/ARCHITECTURE.md` and
  still run in sequence with a merger doc-sync, never beside each other. CS-1061 opens on
  an ADJUDICATED SEAM DECISION and no file is scaffolded before that ruling.

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

