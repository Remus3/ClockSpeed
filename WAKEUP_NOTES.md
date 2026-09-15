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
## Session 98 - 2026-09-15 - five items closed, and THREE of them were arms that named a lever they could not move

- Shipped: CS-1081, CS-1084, CS-1082, CS-1062 and CS-1083 CLOSED. CS-1085, CS-1086,
  CS-1087 and CS-1088 filed. `main` at c090bc5, clean and pushed, whole suite green
  through the pre-push hook at 7788 passed 7 skipped.
- In flight: tier 1 CI on c090bc5 was IN PROGRESS at session end. Read it first.
- THE SESSION'S ONE RESULT: THREE SEPARATE ARMS WERE GRADING NOTHING, each found by a
  different route, and in every case the arm's STATED purpose was intact while its
  discriminating power was gone. CS-1081's fixture planted a line the parser could never
  match. CS-1082's control asserted emptiness, which the very defect it guards against
  satisfies. CS-1083's arms asserted `exit 1` plus a substring that the NEW coverage
  diagnostic also produces. Targeted suites were green on all three.
- A MUTATION APPLIED AS A PAIR GRADES THE PAIR, NEVER EACH HALF. Reached TWICE by
  different routes. On CS-1081 an adversary changed both sentinel comparisons together,
  the BEGIN arm caught the pair, and `==` to `in` on END ALONE still read 46 passed exit 0.
  On CS-1083 the same shape hid a THIRD half-hollowed arm that only the full 18-arm
  enumeration found. Sweep each half separately or the pair's death is the pair's alibi.
- THE 320 SECOND FIGURE BINDS NOTHING AND CS-1073's MARGIN SENTENCE IS MEASURED AGAINST IT.
  The live tier-1 levels are 420 warn, 480 fail, 600 cancel, PER SHARD. 320 is the
  feasibility precondition for a wall-clock gate nobody has built, and
  `docs/history_notes.md` says in its own words that the item owning it "DETECTS NOTHING BY
  ITSELF". M = 295 against 480 is 185 seconds clear.
- MY OWN FIRST PASS AT THE CI DISTRIBUTION WAS WRONG TWICE AND AN ADJUDICATOR CAUGHT BOTH.
  Reading all 54 runs made the lane look catastrophic - those readings are the TWO-shard
  era where `fast` carried the modules now in `guards`. Then my 13-run figure of 310 was a
  PRE-CS-1073 save reading, and save is no longer a worst-job candidate at all. SEGMENT BY
  WORKFLOW GENERATION BEFORE QUOTING ANY CI DISTRIBUTION.
- RUNNER CLASS IS NOT OBSERVABLE. The jobs API gives `labels: [ubuntu-latest]` and an
  ephemeral `runner_name` with no machine identity. Any acceptance requiring readings that
  span both classes is unfalsifiable and must be retired, not satisfied.
- THE HANDOFF'S SWEEP FIGURES DID NOT REPRODUCE. Session 97 recorded the least progressed
  world at 8 schematics and 37 recipes; first-hand it reads 6 and 22. The operator plays
  while sessions run, so a library-backed number is a READING, not a constant. Build
  clauses that depend on no live count.
- TWO SIZE GATES ARE NOW NEAR-BLOCKERS OF THE SAME SHAPE - a hand-maintained table that
  grows one row per event, living in the file that reads it. `docs/item_notes.md` hit
  ELEVEN bytes free (CS-1062, closed, now 79 per cent with an approach arm at 90).
  `tests/test_docs_citations.py` is at TWENTY-ONE bytes free (CS-1088, open).
- CS-971 IS BLOCKED BEHIND CS-1086 AND THE HANDOFF ORDER DID NOT KNOW THAT. Post-CS-1062
  headroom is about 32 index rows; CS-971 would create up to 51. Do CS-1086 first or
  relocate as you go.
- A GATE THAT DEGRADED TO SILENCE NOW SPEAKS. Every commit before CS-1083 printed
  `skipped <pii:world>` and `PASS`; the merge commit printed `PASS - 4 checked, 0 skipped`.
  The privacy check for non-negotiables 11 and 12 had not run on any commit made while the
  library was over the 24-file cap.


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
