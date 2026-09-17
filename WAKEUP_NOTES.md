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
## Session 102 - 2026-09-16 - the lane was killing its own suite, and adversaries refuted nearly every first pass

- Shipped: CLOSED by the main session, each through builder, adversary on a distinct lens,
  repair loop, then a verifier or a stop-condition pass: CS-1096, CS-1101, CS-1102, CS-1104,
  CS-1110, CS-1086, CS-1097, CS-1107, CS-1111, CS-1113, CS-1115, CS-1116, CS-1109. CLOSED
  by the headless lane: CS-894 (649ed65), CS-1068 (69b77a8). CLOSED LATER IN THE SESSION:
  CS-1117, CS-1118, CS-1120, CS-1114 and CS-1106 by the main session, CS-893 by the lane
  (768f2b8). FILED: CS-1105 through CS-1118; CS-1119 and
  CS-1121 by the lane. Detail in `docs/LEDGER.md`.
- **CS-1108 IS CLOSED.** It WAS graded - adversary NOT REFUTED at 3491540, merged at
  925329d, CI follow-up c6a41f3 - but the merger never recorded the closure. Recorded after
  the session: its `docs/LEDGER.md` entry is written and its `ROADMAP.md` line removed.
- **THE BIG FINDING: EVERY LANE CYCLE SINCE 2026-09-06 THAT BACKGROUNDED ITS SUITE WAS
  KILLED.** `claude -p` kills background shells about five seconds after the final reply,
  and `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` covers subagents only. CS-1108 disables
  background tasks and raises the Bash timeout in `ops/loop/run_lane.ps1`; the first cycles
  relaunched under it committed with `ci=success`. CS-1110 discarded the killed cycles'
  CS-893 work after a hash-checked snapshot under the gitignored `data/lane-snapshots/`;
  the lane later closed CS-893 afresh at 768f2b8, so that snapshot is superseded.
- **FROZEN-FILE GRANT RECORDED BEFORE THE EDIT.** CS-1096's two comment lines in
  `tools/precommit_gate.py`, granted by an adjudicator and committed at dc88c08 ahead of the
  change. CS-1106's three lines, same route, recorded at 4289e5c ahead of the change.
- **CS-1114 WAS REFUTED AS A PRIVACY LEAK.** Its first tip's false-positive fix dropped a
  world token from the blocklist in three synthetic refused headers. MERGER RULING, fenced:
  the scan is a fail-safe blocklist, so a false positive (a manual unblock) is never traded
  for a false negative (a leak). The repair skips slot 0 on measured versions only.
- Decisions (adjudicated, no ADR): CS-1086 KEEP-AND-CHECK the routing table, with removal
  filed as CS-1112 and sequenced before CS-971. CS-1110 DISCARD over SALVAGE. The stale
  dead-pid claim records were left for `try_claim_row` to clear, because a hand release is
  a no-op. CS-1104's merger ruled prompt-paraphrase evasions out of scope.
- Surprises: **THE ADVERSARY REFUTED A GREEN FIRST PASS ON NEARLY EVERY SLICE** - CS-1101
  and CS-1104 three times each, CS-1096 twice. **REPO-WIDE GUARDS CAUGHT WHAT SCOPED SUITES
  DID NOT** - exception rendering, liveness, bare mypy, and the assertion-rendering echo
  guard on ubuntu - so the whole suite ran before every push. CS-1106's verifier plants
  tripped the arm's own anchor checks, which failed closed; ruled a weakness, not a defect.
- CI reds and causes: 0dbf309, a cmd.exe control not skipped on ubuntu (fixed at c6a41f3);
  c1d7517, a synthetic `class Runner:` string matched the CI runner account name in the echo
  guard (fixed at 3ff40e1); 645663c, tier1, the memory reachability walk followed `INDEX_*`
  routing children only on a case-insensitive filesystem - pre-existing, exposed by a CS-1120
  plant (fixed at 0cd4e66, merged at ea944a2). All green after the fix. The lane STOPPED
  ITSELF on the 645663c red (`stopped_by=ci_red`) and was relaunched after green.
- Failed paths: removing the routing table outright (a planner's proposal, rejected by
  adjudication - see CS-1112); salvaging the killed lane's CS-893 diff (red, and its
  ROADMAP hunk allocated an id main had since given to another item).
- In flight: one `queue` lane under the fixed launcher, reading the channel through CS-1104
  (driver line `queue-loop inbox (cycle N): ...`). Inbox: nothing unread, nothing owed, as
  printed by `tools/inbox_watch.py` when these notes were written. Many
  `.claude/worktrees/agent-*` from this session are merged; none removed - classify by
  content before pruning.
- STILL OPEN worth naming: CS-971 (behind CS-1112 and CS-1079), CS-1079, CS-1098, CS-1099
  and CS-1100 (with the CS-1098 licence fence), CS-1105, CS-1112, CS-1119 and CS-1121.
- Next action: the lane keeps draining under the relaunched launcher; the main session takes
  CS-1105, then CS-1112 -> CS-1079 -> CS-971.

## Session 101 - 2026-09-16 - the moon-sync adoption, and three of three slices refuted before merge

CLOSED: CS-1095 (the cross-repo channel contract, all nine items of the operator's
adoption instruction), CS-1103 (a blind inbox read that wrote).
FILED: CS-1101, CS-1102, CS-1103, CS-1104.

**EVERY SLICE WAS REFUTED ON ITS FIRST PASS. THREE OF THREE.** Not one survived its
adversary, and none of the findings was a matter of taste - each was measured. The
spawn-site arm's own docstring claimed a property it did not have, and five spawn shapes
passed it blind including one whose expression evaluates to zero. Arm 7 of the channel pin
did not grade the table it names as the grammar's vector source: a flipped verdict and two
swapped vectors both passed. The watcher's highest-consequence invariant - SHOWING NEVER
ACKNOWLEDGES - was graded one layer below the door the hook enters, so an acknowledgement
added at the entry point survived a green suite.

**ONE SHIPPED DEFECT, FOUND BY AN ADVERSARY AND BY NO ARM.** An inbox that exists but
cannot be listed printed the affirmative clean line with notes sitting in it. A sibling
then reproduced it under a real access-control denial, found it was THREE defects rather
than one, and the two CS had missed were the WRITE halves - a fabricated withdrawal, and
an acknowledgement that erased the watermark. That became CS-1103.

**THE WHOLE SUITE CAUGHT WHAT SCOPED SUITES COULD NOT, THREE TIMES, AND IT WAS RUN BEFORE
THE PUSH FOR THAT REASON.** Session 100 recorded the opposite ordering as a merger error.
Two stale toolpath exemptions, an unbounded subprocess child, and one arm that was
NON-DETERMINISTIC ACROSS CHECKOUTS.

**THE ARM THAT PASSED WHERE IT WAS WRITTEN AND FAILED WHERE IT WAS MERGED.** Arm 6 recorded
a gitignored directory as non-resolving - true in a worktree, false in the primary
checkout. Existence is the wrong property to assert about a gitignored path; being IGNORED
is the right one. THE TRAILING SLASH ON THAT CHECK IS LOAD-BEARING: the rule is a
directory-only pattern, so `git check-ignore` without the slash answers from the filesystem
and reproduces the defect it was written to remove. Measured 5 of 5 each way.

**THE HARNESS REPORTED EXIT 0 OVER A RED SUITE TWICE.** Both times the log said
`PYTEST_EXIT=1`. The log is the evidence; the notification is not.

**THE CHANNEL ROUND: four notes out, four replies back, full reciprocity.** Both published
findings reproduced in every tree holding the core. Two divergences came back that neither
side would have found alone, and BOTH structural arms of the portable core now differ
materially between trees that ported the same prose - which is a statement about porting by
description, not about two arms.

**TWO CONCESSIONS MADE TO THIS TREE, not by it.** The "not urgent while the digest pin
holds" framing is FALSE for any tree porting the arms without the document. And a sibling
refused the same document at its licence gate for naming no licence - a refusal that
applied to this copy, because THIS TREE HAD SKIPPED ITS OWN SECTION 14 GATE. It has now
been run, trap by trap, and CLEARED. The lesson filed with it: AN OPERATOR INSTRUCTION
MOVES THE DECISION, NOT THE GATE.

**A LINE-PIN FAMILY WENT STALE FOR THE SECOND TIME IN TWO SESSIONS**, moved by an edit
ABOVE a site rather than at it. Re-cited by symbol where possible; CS-1102 carries the rest.

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
