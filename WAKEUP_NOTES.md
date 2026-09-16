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
## Session 100 - 2026-09-15/16 - CS-1093, CS-1086's domain half, CS-1087

**CLOSED.** CS-1093 - the 7-bit walk names every offending module rather than the
first, the count bound to a scalar so pytest's rewriting cannot render the
population. CS-1087 - a world token carried only by an unparseable header is
matchable WITHOUT parsing that header, by scanning the FRAMING the engine writes
around it.

**DISCHARGED, NOT CLOSED.** CS-1086's domain half. All nine `detail:`-field
disagreements resolved under ONE rule rather than nine judgements: the field is
present exactly when the item has a routing row AND a section in the leaf that
row names. Both directions now measure zero. What remains open is deriving the
leaf half. This unblocks CS-971's blocker by half.

**FILED.** CS-1095 (BACKLOG, the inbox watcher `--strict` flip), CS-1096 (the
bounds enumeration nothing grades), CS-1097 (the save-name false positive),
CS-1098 archify, CS-1099 context-mode, CS-1100 the skills pack.

**GRANTS RECORDED BEFORE THE EDIT.** Two, both in `docs/LEDGER.md`. CS-1087's
frozen-file grant for `tools/precommit_gate.py`, with `.githooks/pre-commit`
DENIED because the hook maps every non-zero status to BLOCKED, which is the wedge
the item forbids. And the console-flash grant for the same file, operator-granted
and recorded AS A DEPARTURE from section 6.1's adjudicator route so no later agent
cites it as precedent.

### What the graders changed, which is the session's real result

CS-1087's shipped fix is materially different from the one first written, and
every difference came from an agent that did not produce the work.

- An ADJUDICATOR sent the first cut back: a bound truncated the world-token
  population without reaching the exit status - CS-1083's defect class recurring
  inside CS-1087's own fix.
- An ADVERSARY found the cap SILENTLY LOSING REAL TOKENS two ways: it counted raw
  hits BEFORE de-duplication, so a value repeated to the cap followed by a
  DIFFERENT value discarded the second; and `hits` was shared across both
  framings, so a full narrow population starved the wide scan entirely.
- The same adversary broke clause 6: `scan_framed_tokens` bound the prefix BARE -
  the first bare holder of a save prefix in the module - and the arm claiming
  otherwise monkeypatched THE VERY FUNCTION HOLDING THE BUFFER, so it was blind by
  construction.
- On RE-GRADE it caught the repair to the bounds sentence PRESERVING the off-by-one:
  "All four" over five became "All FIVE" over six. Incrementing was mistaken for
  correcting because nothing grades that sentence. CS-1096 files the arm.

### Process findings that cost real time

- A NARROWED DEFINITION EMPTIES THE POPULATION. Measuring CS-1086's marker by its
  TARGET string instead of its FIELD POSITION gave 8 disagreements against the
  filed 9. The filed count was right and reproduces at every commit since filing;
  the missing member was CS-1026, whose field points at prose. Keep the count in an
  acceptance - it is the anti-narrowing control - and enumerate the roster beside
  it, because ids go absent where a count miscounts. Memory written.
- THE WHOLE SUITE CAUGHT WHAT THE SCOPED SUITE COULD NOT. Three failures landed
  after the CS-1087 merge, in `tests/test_toolpath.py` and
  `tests/test_assertion_rendering.py`, both outside the scope the merger gave the
  builder. One was a PII LEAK IN THE ARM THAT PROVED THE READER ALIVE: asserting on
  `read_header(readable).world_token` renders a field whose class withholds it. A
  change to a file as widely referenced as the gate needs the WHOLE suite before
  the merge, not after.
- A LINE-PINNED REFERENCE BROKE THREE TIMES IN ONE SESSION - the docs-citation
  guard rejected six line pointers in a ledger entry the merger wrote, and two
  toolpath exemptions went stale when the gate grew 233 lines. Cite by SYMBOL.
- TWO RUNNERS LIED ABOUT A SUITE. One reported exit code 0 over `3 failed`; another
  died silently at 98 per cent with no verdict and zero surviving processes. Write
  `PYTEST_EXIT=` INTO the log and read the log, never the status line.
- `Path.write_text` and the harness heredoc both corrupt payloads - the heredoc
  collapses `\n` inside a quoted body. Write payload scripts with the Write tool.

### Measured, and worth keeping

On the live library this run: 31 save files, ONE unreadable header, and it
recovered NOTHING - it is the truncated-before-the-identifier shape. CS-1083 cited
0 of 28; the grant ordered the re-measure and this is it. So CS-1087's coverage
limb is 0-for-1 on real data today. That is a floor on the item's value, not a
defect in it.

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
