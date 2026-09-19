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
## Session 107 - 2026-09-19 - an operator-directed machine stray-work sweep, and the one defect it turned up

- Shipped: CS-1154, closed. CS-1153 filed and left OPEN. Detail in `docs/LEDGER.md`, not here.
- In flight: nothing half-done. The sweep report is delivered to all four sibling inboxes as
  `2026-09-19-1430-from-CS-REVIEW-e085b4a92ab2-machine-stray-work-sweep.md`; RC merges the five
  reports and the operator adjudicates before any deletion pass. NOTHING was deleted, moved or
  renamed anywhere on this box by this session.
- Decisions: no ADR. The sweep proposed a PRUNE / MOVE / KEEP / UNKNOWN class per row and
  actioned none of them; that is the operator's call after the merge.
- Surprises: THE SWEEP FOUND A LIVE DEFECT IN THE SUITE, not in the tree it was inventorying.
  `git -c core.hooksPath=.githooks push` exports its override through `GIT_CONFIG_PARAMETERS`,
  every git child inherits it, and a command-line override OUTRANKS repository configuration -
  so every throwaway repo in `tests/test_precommit_gate.py` lost the `core.hooksPath` it had
  just set and NO HOOK RAN. The world-name PII arm accepted the commit it exists to block,
  three pushes running, with `returncode=0` and an EMPTY stderr. The empty stderr is what
  settled it: that gate prints a PASS line on every run it completes, so silence is a hook that
  never fired, not a gate that approved. CS-1154 is the repair.
- Failed paths: the FIRST diagnosis was wrong and the ledger entry says so rather than quietly
  replacing it. The failure was attributed to a contended box - 21 python and 47 node processes
  from concurrent sibling sweeps - purely because it did not reproduce standalone. It
  reproduced three pushes running and never once outside the hook, which contention does not
  explain. Do not reach for load as an explanation before checking what the hook environment
  carries. Also measured and discarded: GIT_DIR contamination, both relative and absolute, and
  `-n auto` over `tests/test_precommit_gate.py` alone. None reproduce it.
- Next action: read `docs/item_notes/phase7.md` section CS-1153 and prune the gitignored and
  PII-bearing roots in `tools/drift_guard.py::_walk` by rule rather than by never being reached.

---

## Session 106 - 2026-09-19 - two rows ran, one closed and one was refuted by an adversary, and the publication gate got its first real closure scan

**CLOSED: CS-1147, CS-1146. REFUTED AND STILL OPEN: CS-900. FILED: CS-1152.**

**CS-1147 - the ration arm no longer races the child it measures.** The child called
`ration.release()` and THEN wrote its released marker, so a parent acquiring in that
window saw two of three protocol signals. Reproduced FIRST by widening the gap to 0.5s,
which gave the byte-identical CI assertion; the same widening passes after the reorder.
Then an adversary refuted my own done-claim on the first commit: I had verified teeth with
a LIVE never-releasing child (red in 124.89s) and called the clause discharged, but the
CANONICAL mutant - delete the release call, change nothing else - was GREEN in 0.15s both
before and after. The child EXITED the instant it stopped holding and the ration correctly
reclaims a dead holder's slot, so nothing in the arm told a release from a death. The child
now waits for a `parent_done` dismissal written after the measurement, so it is alive across
the parent's acquire. That mutant now fails in 120.33s. The same pass found a SECOND race of
the same family: `_await_file` returned the instant a path existed, and `write_text`
truncates before it writes, so both process arms could read an empty marker and die in
`int()` with an uncaught ValueError. It waits for a byte now.

**CS-1146 - and session 105's caveat against itself was WRONG ON ITS OWN NUMBER.** That
caveat de-ranked the row because "the very next tier 1 run had the guard shard at 230s".
Measured from the jobs API: that run was 413s and the next was 441s. With the record's 11
readings at 426-464, that is 12 of 13 known readings at or over the 420s budget, spread 38s.
The caveat's METHOD was right - measure the spread before ranking - and following it
reversed its own conclusion. `tools/tier1_growth.py` now grades `B >= M` per job as a verdict
distinct from the band-versus-jitter one, names each job with its own margin, and prints
BUDGET BREACHED by 44s over the shipped record. No level moved.

**CS-900 SHIPPED ITS TOOL AND STILL FAILED, on an adversary and not on my reading.** Two
counter-examples. (1) The save shard WARNS at both ends of the profile with the SAME top
test across four commits that touched only another job, so branch one closes only by
electing the LOOSER of two stated shares - and the 18.9 per cent concentration that FILED
the item passes the 50 per cent hard level. A level under which the filed defect passes
cannot be the level the close rests on. (2) The hard level's derivation was FALSE: the
`t_max <= T/W` criterion is against the SERIAL TOTAL and the tool divides by the STEP WALL
CLOCK, which agree only at one worker. Corrected in the docstring, not dropped. `T` is not
obtainable from a block printing only the top 15 phases over 5s, so that criterion cannot be
graded by this tool at all.

**THE PUBLICATION GATE GOT ITS FIRST REAL CLOSURE SCAN, and six of seven axes are CLEAR.**
Over everything reachable from `main`: 1059 commits, 3255 blobs, 461 DISTINCT HISTORICAL
PATH STRINGS - 42 more than HEAD, which is the half that leaks. No account id, no standalone
world name, no home paths, no save bytes, no game assets, no `data/` or inbox payload, in
ANY commit. The one finding is the plan's own credential allowlist drifting against its own
synthetic canaries, and the plan sentence asserting the real token prefixes return zero is
now the only carrier of those prefixes. The pre-rewrite safety bundle is taken, lives outside
the tree, and was graded by RESTORING rather than by verifying.

**PROCESS FINDINGS - MEASURED, DO NOT REDISCOVER.**

- A CONTENDED xdist SUITE REPORTS A SHORT GREEN, NOT A CRASH. Beside a running lane,
  `-n 4` reported 6407 passed and EXIT 0 while `--collect-only` said 9055 collected: 2641
  tests silently never ran, no MemoryError, no non-zero exit. The memory note predicted a
  MemoryError; the real signature this time was a clean short pass. A SERIAL run beside the
  same lane returned the full 9048. Check the count against a collect, always.
- THE PATTERN-LANGUAGE TRAP FIRED TWICE BEFORE THE SCAN EVEN STARTED. `git for-each-ref`
  with a globbed `refs/backup/*` returned 0 where the bare prefix `refs/backup` returned 71,
  and `git bundle list-heads` reported 242 refs where a bare `git clone` restored 144 and
  ZERO of the 53 wip refs. A bundle that VERIFIES is not a bundle that RESTORES.
- THE REPOSITORY'S OWN PII GUARD CAUGHT A PII DEFECT INSIDE PUBLICATION-PREP WORK. The
  pre-push hook refused the register slice because it rendered a caught exception OBJECT
  into an f-string, which is an echo path under non-negotiable 12.
- A NEW TEST MODULE CITED IN A GUARDED DOC READS AS A DEAD BARE PATH until it is at least
  intent-added, because `tests/test_docs_citations.py` resolves against the tracked file
  list. It cost a false red once.
- THE COMMUNITY-PROFILE ENDPOINT READS THE DEFAULT BRANCH ONLY, so a community-health
  acceptance cannot be graded from a slice branch. Its `issue_template` row reads null even
  though `.github/ISSUE_TEMPLATE/` exists with two files.

**A CORRECTION I OWE THE RECORD.** I told the operator mid-session that the publication
decision was "publish from a fresh squashed or orphan history". That is the 2026-08-13
record. The LATER ruling - CS-700 section 6, 2026-09-08, with ADR 0018 - is that the commit
graph is KEPT, IDENTITY ALONE is rewritten to the noreply address, the remote is deleted and
recreated, and `main` alone is pushed. Squash and accept-as-is were both put and DECLINED.

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
