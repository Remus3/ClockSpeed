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
