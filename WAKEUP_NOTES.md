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
## Session 99 - 2026-09-15 - the handoff's single next action was the FOURTH filing over one wall, and the clause guarding it forbade its own remedy

- Shipped: CS-1085 and CS-1066 CLOSED on their own work; CS-1057 and CS-1088 CLOSED AS
  SUPERSEDED; CS-898 NARROWED. CS-1089, CS-1090, CS-1091, CS-1092, CS-1093 and CS-1094
  filed. `main` at 1471779, clean and pushed, whole suite green through the pre-push hook
  and again at `/done` - 7791 passed, 7 skipped, exit 0, `python -m mypy` exit 0.
- In flight: nothing. Tree clean, local equals origin.
- THE SESSION'S ONE RESULT: `tests/test_docs_citations.py` came off its ceiling, 100 per
  cent to 73.94, headroom 21 bytes to about 68000. The ceiling was NOT raised, no
  disposition row deleted, no pin forgiven.
- THE HANDOFF'S SINGLE NEXT ACTION WAS NOT SAFE TO DISPATCH AS WRITTEN. CS-1088 was the
  FOURTH open filing over one file and one ceiling - CS-1057, CS-1066, CS-1088 and
  CS-898 - and two of them carried DIFFERENT triggers for the same guard, 96.875 per cent
  against 90. Grepping the roadmap for siblings before dispatching an item cost minutes
  and saved building the wrong guard twice.
- AN ACCEPTANCE CLAUSE FORBADE ITS OWN REMEDY. "Collected-arm count EQUAL before and
  after" is unreachable for ANY relocation into a new file, because a census arm is
  parametrized over the tracked-module population and gains one node for any new module.
  AMENDED under CLAUDE.md section 8 to a full node-id comparison in both directions,
  which is strictly stronger: a simultaneous loss and gain passes a scalar and fails it.
- A LEDGER SENTENCE WENT STALE INSIDE THE COMMIT THAT CARRIED IT. A slice recorded
  CS-1057's detail relocation as an undischarged seam because those files were off its
  write-list; the merger discharged it minutes later in the same commit. The file is
  append-only so the sentence stands, and it had ALREADY MISLED AN ADJUDICATOR before the
  correction was written. A slice that leaves a seam must have its record checked by
  whoever closes the seam.
- ESTIMATES LOST TO MEASUREMENT THREE TIMES. Dead citations: a planner said 6 names over
  8 sites, an adjudicator said 3 over 4 after filtering to uppercase names and missing
  three FUNCTION citations, and the in-slice measurement was 5 over 7. Self-spelled
  sites: estimated 60 to 28, measured 60 to 37. NEVER carry a count across a slice
  boundary - the acceptance now says so in words.
- A TREE-WIDE GUARD SHIPS RED, and that is the finding not the obstacle. The approach
  band was red on THREE files the item never touched, at 99.9, 95.9 and 95.0 per cent.
  The answer was a baseline residual pinned in BOTH directions with a spelled shrink-only
  ceiling and an item id per row, not a hand-list of one - a hand-list of one is a
  threshold met by its strongest member.
- A PLANT KILLED INSTEAD OF DEGRADING, found by mutation and not by review. A non-ASCII
  byte planted to prove the ASCII arm raised an unnamed `UnicodeDecodeError` that
  destroyed the `closure` fixture, so the arm DIED rather than reporting.
  `namespace_closure` now decodes with `errors="replace"`.
- THE HARNESS WRITES CRLF THROUGH `Path.write_text`. A relocation script silently
  converted three tracked docs to CRLF. It was caught by BYTE ARITHMETIC - the routing
  index grew 203 bytes while a row was being REMOVED - not by a CR check, because
  `grep -c $'\r'` returns the TOTAL line count on a pure-LF file and reads as "all CRLF"
  either way. Pass `newline="\n"` and assert on the bytes.
- Decisions: no ADR recorded. Two acceptances amended under CLAUDE.md section 8 - CS-1066's
  collected-count clause, and CS-1088's approach-arm clause folded into it. CS-898's
  stated-policy half struck as discharged.
- Surprises: no spike contradicted `BOOTSTRAP.md`.
- Failed paths: none abandoned. The widening of `derived_bound_problems` to `ast.Attribute`
  was adjudicated PERMITTED rather than a breach of "the same guard", because the clause
  names the guard's IDENTITY and its two-way property, not its node-type set.
- Next action: work CS-1087 - the unreadable-header residue CS-1083 declined. Do NOT
  close it by simply making an unreadable header block; that declination was adjudicated
  SOUND under non-negotiable 7.

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
