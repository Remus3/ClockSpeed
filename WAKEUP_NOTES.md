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

## Session 74 - 2026-09-08 - the flip plan chose its branch, and CS-954's repair introduced the hang its own refutation caught

- Shipped: CS-954 CLOSED. CS-700's PLAN produced and CS-700 stays OPEN by design.
  ADR 0018 accepted. CS-955 filed. Detail in `docs/LEDGER.md`, not here.

- In flight: nothing. Tree clean, no worktrees, no stash.

- THE SESSION'S SHAPE WAS PLAN-THEN-REFUTE, TWICE, AND BOTH REFUTATIONS PAID.
  Each deliverable was committed to freeze it, graded by an agent that did not
  write it, and repaired. Both times the adversary found a defect in the
  author's own evidence rather than only in the artifact, which is the part
  worth carrying forward.

- CS-700's PLAN: the CONVENTIONS 17 clause is CONDITIONAL and its antecedent
  does not fire. The publishable graph is clean of CONTENT on six axes, so no
  rewrite is owed for the reason section 17 contemplates. What is dirty is
  off-main and never pushed. The exposure is what the FORGE accreted: 53
  `refs/wip` refs, 233 Actions run logs of which 21 are failed runs, 17
  artifacts, 534 MiB of caches - all surviving a force-push. ADR 0018 therefore
  recreates the remote and pushes `main` alone, which makes the deletion the
  verification.

- TWO OF MY OWN CLAIMS WERE FALSIFIED BY THE ADVERSARY, and both are kept
  visible in the documents rather than smoothed away. I asserted the wip refs
  were invisible to REST; paginated REST returns all 53, and my "11" came from
  an unpaginated query that answered short without erroring - trap (b) firing
  inside the evidence offered as proof trap (b) was handled. And the plan's
  first bundle step would have preserved nothing, because the wip refs exist
  only on the remote, so its control compared two empty local counts and 0 == 0
  would have passed green.

- THE FOURTH CHANNEL NOBODY HAD LOOKED AT: commit author and committer identity.
  520 of 521 commits carry a real personal email in both fields. CONVENTIONS 17
  gate item 2 does not reach it. The operator RULED: rewrite to noreply.

- CS-954: THE REPRODUCTION REFUTED THE FILED MECHANISM AND THE ITEM WAS REPAIRED
  ANYWAY. Two controlled runs - plain local path and `file://` - advanced the
  local ref mid-hook and BOTH shipped exactly the SHA the hook was handed, with
  a control proving the ref had really moved. The incident is nonetheless REAL:
  no CI run has ever existed for the SHA the hook graded, and one push-event run
  exists for the later commit created three seconds after the ref update. So the
  repair was built MECHANISM-AGNOSTIC on purpose.

- THE REPAIR INTRODUCED A HANG AND THE REFUTATION CAUGHT IT. Reading stdin
  unconditionally makes the hook wait forever for an EOF a terminal never sends,
  so hand-running it wedged where it used to exit. The arm meant to cover that
  asserted only CLOSED stdin while its docstring claimed to cover the debugging
  case - which is the terminal case, and was the one that hung. Also caught: a
  condition implemented but ungraded, proven by a mutant that survived all four
  arms while changing real behaviour.

- Next action: read the CS-700 plan section in `docs/item_notes/phase7.md`. It
  is the implementing session's brief and it is now step-by-step. Its step S0 is
  to write the needle set and the allowlist into the plan before S1 runs.

- Watch out for: `/clear` survival is STILL not measured across five repos. The
  three same-second lines in the invocation log are session 73 exercising the
  instrument by hand via `--source`, not hook fires. CS-952 is a hard blocker on
  the flip and needs a frozen-file grant. ROADMAP.md is over its soft budget.

## Session 73 - 2026-09-07 - the cross-project sync turned into two shipped items, four self-inflicted defects, and a queued plan

- Shipped: CS-949 (withdrawal reporting) and CS-950 (the invocation log). Detail
  in `docs/LEDGER.md`.
- In flight: nothing mid-edit. Two commits landed, `5d184c8` then `5192aaf`,
  the second repairing four defects the first introduced.
- Decisions: no ADR. The operator ruled three things on the channel - prose only
  is CS's standing default to every sibling, sibling names in a sibling's public
  history are fine for all projects at this time, and CS volunteers as RC's
  pairwise responder-trial partner with CS's end restricted to measure-and-reply
  actions, adopting a standing responder only after RC repairs or strikes A3
  and A4.
- Surprises: P4 (`/clear` survival) was not UNVERIFIED here, it was
  UNMEASURABLE - the watcher wrote no record of ever running. Four other repos
  were reading their own hook CONFIGURATION and calling it argued by
  construction. CS-950 makes the measurement possible and does not perform it.
  Separately: 19 outbound notes exist across the four sibling inboxes and ZERO
  are traceable in CS's own tracked content, so a cold session reading only this
  disk would correctly conclude CS has never replied to anyone. Filed as part of
  CS-951.
- Failed paths: the first push was REJECTED by pre-push, and correctly - the
  citation ladder caught CS-952's note citing a permanently untracked path. The
  comment written to buy that disclosure then cited the same path inside the
  guard's own file and was caught again. A disclosure written in the vocabulary
  of the thing it discloses becomes another instance of it. Also: a cap arm was
  sized from the constant under test, which RSC measured as an amplifier that
  wrote 492674 files under a mutation; fixed before it was ever run. AND the one
  that matters most - a commit reached the remote without pre-push ever running
  against it, because this session committed while a push was in flight. Filed
  as CS-954, tier 1, mechanism NOT established. The risk was flagged aloud
  earlier in the same session with the WRONG consequence predicted: a spurious
  red was expected, a skipped gate is what happened.
- Open, none started: CS-951 (outbound withdrawals), CS-952 (gitignored wiring,
  needs a frozen-file grant before `.claude/settings.json` is touched), CS-953
  (the HEAD-path scrub trap), CS-954 (the push race, tier 1 and the only tier 1
  here). The A1 output filter promised to RC before its trial window opens has
  no item and no code - it exists only as an outbound commitment in a note.
- Next action: **PRODUCE THE PUBLIC-FLIP PLAN AND EXECUTE NONE OF IT.** The
  scope, the four measured traps, the history-only checks and the one decision
  that needs an ADR are already written up as CS-700's detail in
  `docs/item_notes/phase7.md`. Read that section first. The session AFTER the
  plan implements it, so that the agent producing the plan is not the one
  grading its execution.

---

## Session 72 - 2026-09-07

**CS-940 and CS-934 closed together**, because they were one file and one
rewrite and doing them separately meant writing the seen-set key twice. The
completion record with every measurement is in `docs/LEDGER.md`.

**THE SESSION'S TRANSFERABLE FINDING, and it is about tests rather than code.**
AN ARM THAT VARIES CONTENT VARIES MTIME, SIZE AND CONTENT AT ONCE, SO IT PINS
NONE OF THEM. The first suite here had 22 green arms and could not distinguish a
content digest from `st_mtime_ns` or from `st_size`; both mutants passed
everything. To pin the content leg an arm must hold everything else constant -
edit in place and RESTORE the timestamp, and change content at CONSTANT BYTE
LENGTH. Every project on this channel shipped a digest key this round, so the
finding was sent to all four siblings.

Second half of the same finding: AN ASSERTION THAT ONE EXACT STRING IS ABSENT IS
DEFEATED BY TRUNCATION. A 16-character preview passed an arm looking for a
22-character sentence. Assert over every window.

**Both adversaries returned REFUTED, and both were right.** The candidate was
frozen at a digest before dispatch and neither agent wrote any of it. Twelve
arms were added in response. The cost of skipping that pass would have been a
watcher that looked finished and silently dropped four classes of deliverable.

**AN ADVERSARY CAUSED A REAL INCIDENT ON THIS BOX AND DISCLOSED IT.** While
probing the unbounded-read path it started a 400 GiB sparse-file write that
zero-filled 35 GB of C: before it noticed, and stopped it with a
`taskkill /F /IM python.exe` that terminated five python processes - which may
have killed another project's suite. Disk was fully reclaimed, 289 GB free
verified, and nothing was written inside the repository. Two standing lessons
were re-confirmed the hard way: a runaway command fills the disk, and a blanket
image kill on this machine is never local to one project. An adversary brief
should cap the size of any fixture it is invited to create.

**A trap paid for again: do not `cd` into an inbox subdirectory.** The
`PreToolUse` hook resolves its gate script relative to the working directory, so
one `cd` into a directory without a `tools/` bricked BOTH Bash and PowerShell -
they share one working directory - and `cd` back fails because the hook fires
first. Recovery was a non-shell directory tool. The handoff warned about this
and it still cost a turn.

**The channel.** Answered RC's `slots.py` rewording proposal with YES on the
operator's ruling, and corrected a premise while doing it: Clockspeed is NOT a
carrier of that file. It DERIVES `ops/loop/lanes.py` from it and never copies,
because vendoring would enrol this project in a machine-wide ProgramData token
bucket that other trees ration between themselves. So no bytes are re-pinned
here; the only consequence is that `lanes.py` records the upstream digest of
`slots.py` and a reword moves it, so the new digest is owed when the carriers
converge.

### The second half of the session - the channel, read whole

**EVERY FILE IN `moon_sync_inbox/` WAS READ, on an operator directive**: 73 notes,
a 7-file payload and one loose reference file, by seven read-only agents over
disjoint slices. The inbox was acknowledged ONLY after that - 75 items, 0
undigestible. An acknowledgement made before the reading would have been the
seven-hour failure with better manners.

**FOUR OPERATOR RULINGS, each filed with its cost rather than acted on bare.**
Charter v4 ADOPTED as written, including RC as final adjudicator on a deadlock.
The `cs` lane slot ACCEPTED, which reverses ADR-0017 and therefore needs a
superseding ADR before it binds. CAVEMAN ULTRA ADOPTED, needing an adjudicated
grant against the frozen settings file. Verbatim reciprocation AGREED, needing a
manifest producer and a scrub attestation. All four are CS-946, CS-947 and
CS-948; none is started.

**THREE DEFECTS IN THIS TREE FOUND BY READING OTHER PROJECTS' WORK**, not by
probing this one. `save_seen` lets an `OSError` escape as a traceback out of a
session-start hook, so a locked store crashes the watcher and the session
surfaces NOTHING - the outage this project warned four siblings about, one layer
down in its own code (CS-943). Ten test modules walk with `rglob` and one
excludes the worktree directory (CS-944). And 52 of 62 local branches are ahead
of `origin/main` on no remote, after this project told a sibling that gap was
fixed (CS-945).

**A RETRACTION PAID.** This project measured Lanternlight's hooks at `100644` and
broadcast it to four repos; both are `100755`, re-measured from their tree.
Corrected in this file beside the original rather than deleted, because the
finding that hook MODE is a silent-non-execution class still stands. One wrong
measurement reached four trees in about an hour, which is the broadcast rule
working in the wrong direction.

**A PAYLOAD TWO SIBLINGS BELIEVE THEY DELIVERED IS NOT HERE.** RC's notes name a
facts-probe module inside a verbatim payload directory of their own; the only
payload directory in this inbox belongs to a different sibling. The path is
deliberately not spelled here - a described path is a CITATION to the doc guard,
which is the same trap as describing a line pointer. Most likely RC's own URGENT
pull did what it said, which
means two senders spent a night reasoning about bytes the receiver did not have
and nothing on either side said so. That is the withdrawal property arguing for
itself, and it is why CS-941 exists.

**ROADMAP.md IS OVER ITS SOFT BUDGET** by about 1 KB at 161 open items. The
driver is item COUNT, not formatting: the file is item lines, and an acceptance
clause belongs on the line. `doc_budget.py` exits 0 and the suite is green, so
nothing is red - but the relocate pass it asks for has no honest target left, and
the fix is an operator decision rather than an edit.

