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
## Session 97 - 2026-09-15 - CS-1073 closed on a remedy its own acceptance did not contain, and BOTH slices this session were refuted by the adversarial pass after every targeted suite was green

- Shipped: CS-1073 CLOSED. CS-1081, CS-1082, CS-1083 and CS-1084 filed. CS-G06 NOT
  discharged - a discharge was built and discarded unmerged. Detail in `docs/LEDGER.md`.
- In flight: nothing. `main` clean and pushed, whole suite green through the pre-push hook
  at 7771 passed 7 skipped, tier 1 green on three separate attempts.
- TWO OF TWO SLICES WERE REFUTED, AND IN BOTH CASES EVERY TARGETED SUITE, EVERY GATE AND
  THE BUILDER'S OWN WATCHED REDS WERE GREEN ON THE DEFECT. This is the session's main
  result. The adversarial pass is the only thing that caught either.
- THE MERGER'S OWN CONCLUSION WAS THE FIRST THING OVERTURNED. CS-G06 asks for a PROGRESSED
  world in `corpus/`; the merger measured non-empty unlock state and called it discharged.
  After CS-G05's decoder repair EVERY world decodes non-empty, so the measurement
  distinguished nothing. `.gitignore` labels `/corpus/` the pinned reference world's
  snapshot, the save is byte-identical to one still in the live library, and the session 96
  handoff said "development-world save" in plain words. Three cheap checks would each have
  caught it and none was run before a 45-minute slice was dispatched.
- A CORRECT FIXTURE DOES NOT MAKE A LIVE ARM, MEASURED AGAIN. CS-1073's first tier-2 rule
  permitted a deletion when a required tier-2 job named a CONTAINING target. Tier 2 runs
  bare `tests`, so every path beneath it was covered and the rule could refuse nothing it
  would ever face. `--ignore=tests/save` then left the whole directory in NO tier-1 shard
  with all 47 arms green, RED at base. The tell was in the author's own evidence: its
  potency plant had to be spelled `tools/...`. The shipped rule is an allowlist.
- A LOCAL PROFILE OF A CI SHARD IS INVALID AND LOOKS AUTHORITATIVE. The first profile ran
  where the save library exists, read `1559 passed, 0 skipped`, and was dominated by a
  256.89s census that SKIPS on the runner. A partition was computed from it by exact
  subset-sum to 0.0000 per cent imbalance, optimising a file CI never runs. The second
  profile counts only because an injected environment reproduced CI's `1454 passed, 105
  skipped` and then matched all SIXTEEN per-file skip groups, not just the total.
- Surprises: the adjudication's own arithmetic was wrong by about 2x. It predicted ~65s of
  pytest and ~235s of headroom by reading the 220s test as the critical path - the
  FOUR-worker answer. W is 2, now READ from the runner rather than modelled, and the shard
  was bound by total CPU over workers, so the step measured 141s. The lane's worst reading
  fell only 308 to 295 because `fast` was always close behind.
- Failed paths: do not re-attempt the CS-G06 discharge on unlock-state counts. Do not
  re-pitch containment as the tier-1 deletion rule. Do not profile the save shard without
  the injected-environment control.
- Next action: CS-1081 FIRST. It is a LIVE fail-open lever in `main` - the arm that claims
  to prove a classification line outside the sentinels classifies nothing plants a line
  carrying no `gate: ` prefix, so `_CLASSIFY_LINE` never matches it and the arm passes with
  the containment guard DELETED. Nine mutants confirmed it on both trees at 45 passed exit
  0. It is unrelated to either slice and it is the only item filed this session that is a
  defect in shipped behaviour rather than in a measurement or a clause.

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
