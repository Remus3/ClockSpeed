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
## Session 105 - 2026-09-18 - both CI lanes were red on COST and on a TIMING TOLERANCE, not on a defect, and an adversary refuted the merger's own diagnosis

**BOTH LANES WERE RED AT HANDOFF AND THE HANDOFF ONLY KNEW ABOUT ONE.** tier 1 had
failed on cost for two consecutive tips. tier 2 had ALSO failed on `d28e4a5` - a run
was dispatched and never read - with `full suite (windows-latest)` red at
`tests/test_tier1_budget.py`, `reported 393 for a staged 390`. Reading a dispatched
run with the FULL sha was the first action and it found a second red lane.

**CS-1145 CLOSED - the duration arms allowed a fixed two seconds for a gap that
belongs to the runner.** The step computes `$(date +%s) - TIER1_STARTED`, so the
reading carries the wall clock between the harness staging a start and the shell
reading its clock. Windows CI spent three seconds there. The arms now BRACKET the
reading between clocks they read themselves either side of the spawn: `floor` is
monotonic, so a slower runner widens the bracket instead of breaking it, and no
constant sizes it. A third guessed band was available and was refused - CS-1133 and
CS-1134 exist because that guess was made twice already.

**TIER 1 WENT GREEN BY DELETING WORK, NOT BY MOVING A LEVEL.**
`test_a_within_heading_compensating_swap_is_reported_at_every_entry`, which arrived
with CS-1121 the session before, posed a swap per entry and handed the WHOLE corpus
and the WHOLE table to the grader each time, keeping one entry's findings and
discarding 37. 38 x 38 gradings over 38 x 392 documents to read 38 answers. It is
handed one document and one entry now. The fast shard went 495s to 435s, then 430s.
The ceiling was NOT touched; guard (k) ratchets it both ways and CS-1133 records the
ruling that raising a level to meet a slow lane is the move CS-896 exists to refuse.

**THE ADVERSARY REFUTED THE MERGER AND WAS RIGHT, ON THREE OF FIVE ATTACKS.** The
merger's record claimed the module-free baseline was 377-391s; that was 2 of 9
readings already sitting in `tools/tier1_readings.json`, whose true range is
240-410s. The regression was 85s worst-to-best against a jitter of 129s that
`tools/tier1_growth.py` measures for that very job - the signal was INSIDE the
noise, and three post-change samples could not carry the attribution. The mechanism
survived; the conclusion "returns the lane to green WITH HEADROOM" did not. Corrected
statement: it returns the lane to its prior MARGINAL state. AN AGREEING NUMBER IS NOT
A MEASURED ONE - the merger reached its baseline by tabulating the readings it had
already looked at rather than the record it already had.

**THE LOCAL RATIO DID NOT TRANSFER, AND THE PESSIMISTIC ESTIMATE WON.** Locally the
arm fell 10.7x (61.70s to 5.79s); on the runner 7.5x (158.74s to 21.30s); and the
STEP fell only 62s against a 137s CPU saving, because `-n auto --dist loadfile` had
been overlapping that file with other work. The merger projected ~144s from the local
ratio and was wrong by more than 2x in the optimistic direction; the builder's flat
local delta (~57s) predicted the runner (62s) better. CS-900's note already says a
local profile is the wrong instrument - this is a SECOND mechanism for that, distinct
from the subprocess one it records. Recorded as a CS-900 MEASUREMENT RECORD; THE ITEM
STAYS OPEN, because its acceptance also wants a STATED share and no threshold is
declared or graded anywhere.

**TWO AGENTS ENDED THEIR TURNS WAITING ON A SUITE AND RETURNED A PROMISE.** Both were
resumed by agentId, never re-dispatched. Both then delivered in full. One of them had
restarted its own full suite twice because the earlier runs straddled its own edit,
and froze the tree by md5 for the third - which is the rule applied correctly without
being told.

**A BUILDER CITED THE WRONG ITEM IN ITS COMMIT SUBJECT** - slice A wrote `CS-1145`,
which is slice B's row, for work that belongs to CS-900. Caught by the merger at
merge time by reading the subject rather than trusting it, and amended before the
merge. A commit subject is a claim like any other.

**THE MERGER'S OWN FILING TRIPPED A GUARD, AND THE PRE-PUSH HOOK CAUGHT IT.** The
CS-1147 note cited `tests/ops/test_suite_ration.py` by LINE, and
`test_no_line_pointer_names_a_tracked_python_module_without_a_record` refused it:
cite the symbol form, which an edit above it cannot invalidate. This is CS-937's
lesson from the previous session, re-learned by the session that had just read it.
THE HOOK IS THE REASON IT DID NOT SHIP.

**A `write_text` ON WINDOWS PUT CRLF THROUGH A TRACKED FILE.** `pathlib.write_text`
uses platform newline translation, so ROADMAP.md came back fully CRLF while git
normalised the blob and reported the tree clean. Use `newline=""` on every write.
AND the obvious check is a trap: a grep counting lines that match a CR returns
the TOTAL line count on a pure-LF file, which invites a fix for absent damage.
Count the CR LF byte pair in the BYTES instead.

**FILED, NOT FIXED.** CS-1146 - the tier 1 guard shard's worst reading is 464s against
a 420s budget and 16s under the ceiling, and `tools/tier1_growth.py` grades only ONE of
CS-896's three conditions (jitter vs band), so it prints PASS for a job that fails
`B >= M` by 44s. CS-1147 - the ration blocking-protocol arm races the child it
measures: the child frees the slot and THEN writes its released marker, so a parent
that acquires in that window legitimately sees no marker. Measured on tier 2 run
35385454932; `ops/` and `tests/ops/` are untouched since `d28e4a5`, so it is not this
session's work.

**A CAVEAT THE MERGER PUT IN WRITING AGAINST ITSELF.** CS-1146 was reported to the
operator as "one ordinary run from reddening". The very next tier 1 run had the guard
shard at 230s - less than half its recorded worst. The 464s reading is real and the
tool's blind spot is real, but the URGENCY was not earned by the evidence, and that
job's spread is plainly wider than the 28s jitter figure computed for it.

## Session 104 - 2026-09-17/18 - three items closed, each refuted at least once, and two writers collided on the same item ids

- Shipped: CS-1123, CS-1132, CS-1121, all closed through builder, adversary on a frozen SHA,
  repair loop, then an adjudicated stop condition. FILED, NOT FIXED: CS-1135, CS-1136, CS-1137,
  CS-1141, CS-1142, CS-1143. Detail in `docs/LEDGER.md`, not here.
- In flight: nothing half-done. The tree is clean, pushed, and the whole suite is green on the
  merged tip. The `queue` lane ran throughout and closed CS-917's measurement record, CS-920 and
  CS-937 alongside; its work is merged.
- Decisions: no ADR recorded. One adjudication: CS-1121 does NOT close on an anchor-granularity
  identity, ruled Option B on a counter-example in the candidate's own file. Its fence is in the
  ledger entry, not here.
- Surprises: the LANE AND THE MAIN SESSION ALLOCATED THE SAME IDS. Both filed CS-1133 and CS-1134
  for different items within one hour. `ROADMAP.md` auto-merged cleanly with two of each and
  `tools/drift_guard.py` still exited 0 - guard (i) grades id collisions BETWEEN owner files, and
  two lines under one id in the SAME file are not that shape. The writer whose row reached
  `origin/main` first keeps the number; this session renumbered to CS-1135 and CS-1136. Checking
  the remote before filing caught the second near-collision, where the lane had already taken
  CS-1138 to CS-1140. No spike contradicted `BOOTSTRAP.md`.
- Failed paths: a bulk worktree prune driven by a zero-commits-zero-dirty inventory TARGETED BOTH
  LIVE BUILDER WORKTREES and was stopped only by git's own agent lock - a freshly cut agent tree is
  indistinguishable from an abandoned one by content. Do not classify worktrees by content alone;
  exclude this session's agentIds and anything git reports as locked. Separately, a case-SENSITIVE
  verifying grep produced a false correction that a builder had to push back on with evidence: the
  string was `Nothing above it`, capital N.
- Next action: read CI for the pushed tip with the FULL sha, then take CS-1129 - the leaf
  membership rule grammar - as the next `tools/drift_guard.py` item, since CS-1130 and CS-1131 are
  in the same file and must run one at a time.

---
## Session 103 - 2026-09-17 - the acceptance moved off the ROADMAP line, the mypy arms stopped inheriting their environment, and CI stopped starting jobs

- CLOSED BY THE MAIN SESSION, each through builder, adversary on a distinct lens, repair loop,
  then a verifier or an adjudicated stop condition: CS-1079, CS-971, CS-1033, CS-1125. FILED, NOT
  FIXED: CS-1129, CS-1130, CS-1131, CS-1132. Detail in `docs/LEDGER.md`, not here.
- CLOSED BY THE `queue` LANE while this ran: CS-1127, CS-1128. The lane also filed nothing new
  this session. Both collided with a main-session merge and are recorded under "at merge" in the
  two merge commits.
- **THE RULE CHANGE THAT OUTLIVES THE SESSION: AN ITEM'S ACCEPTANCE NOW LIVES IN ITS
  `docs/item_notes/` SECTION, NOT ON ITS `ROADMAP.md` LINE.** The line carries its id, a COMPLETE
  short title, the literal `acceptance: in detail`, its tier and its `detail:` field; the original
  headline is filed in the section under `### Full headline`. `docs/adr/0022-*` is the fence.
  The arithmetic that forced it: the acceptance clauses alone outweighed the whole soft budget, so
  no arrangement that kept them on the lines could fit. CS-1033 asked for the opposite and was
  closed as delivered with that one clause superseded.
- **THE FIRST CS-971 DESIGN WAS REJECTED AFTER AN ADVERSARY READ THE DIFF, NOT AFTER A GUARD
  REDDENED.** Cutting the clause at 90 bytes "at a clause break" changed what items required, item
  after item, and left lines ending on a dangling word. No test in the tree could see it. The
  lesson is the one CS-1105 already filed: a relocation needs a proof that RECONSTRUCTS the
  original, not a proof that the bytes went somewhere.
- **A GUARD WRITTEN IN ONE SESSION WAS DEFEATED FOUR TIMES IN THE SAME SESSION.** The headline
  check went: literal `startswith` (one trailing character defeats it), then token-wise but
  crashing on a headline that normalises to nothing (non-negotiable 7), then accepting any cut
  before a conjunction, then accepting a title with no predicate. Each round was found by an
  adversary crafting inputs, never by the live tree. A guard is not closed because its arms are
  green; it is closed when someone has tried to walk past it.
- **FILING A ROW EXPOSED A DEFECT THE MERGE HAD JUST SHIPPED.** The filed headline was read up to
  the next HEADING, so the `---` between sections joined it, and CS-1122 - whose line carries its
  WHOLE filed headline - read as cut part-way the moment it stopped being the last section in its
  leaf. A section's correctness depended on an unrelated item not being filed after it.
- **CI STOPPED STARTING JOBS MID-SESSION** - GitHub Actions refused every run for about two hours
  with "recent account payments have failed or your spending limit needs to be increased". Jobs
  read as `failure` with no steps, in six seconds. The `queue` lane read those as a red tree and
  STOPPED ITSELF, which is the behaviour its prompt asks for. Do not diagnose a six-second job
  failure as a test failure: read the annotation.
- **UBUNTU PROVED A WINDOWS-GREEN ARM VACUOUS.** The CS-1125 `FORCE_COLOR` plant broke the
  inheriting run on Windows and proved nothing on Linux, where mypy colours only when `setupterm`
  finds a terminfo entry and the runner sets no `TERM`. The repair was to make the HAZARD complete
  (plant `TERM` too), never to guard the platform. Every plant now derives its paths from `site`
  and `sysconfig` rather than a Windows layout.
- **A SCOPED-ONLY RUN HID A REPO-WIDE GUARD FOR THE FOURTH TIME.** The subprocess-timeout guard
  reddened on CI because two new `subprocess.run` calls carried no `timeout=`. Builders now run the
  whole-tree guard modules before reporting, not just their own file.
- MEASURED, NOT FIXED: the tier-1 guard shard ran 454s and then 426s against a 420s budget and a
  480s ceiling, WITH the warm mypy cache in place. It passes and it has almost no headroom left.
  That belongs to the rows that own tier-1 cost and its growth rate.
