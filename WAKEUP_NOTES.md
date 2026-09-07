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

## Session 71 - 2026-09-07 - CS-928 and CS-935 CLOSED; the inbox channel turned into the session, and probing a watcher refuted the docstring defending its own bug

- **Shipped:** **CS-928, CS-935 CLOSED.** **Filed:** CS-934, CS-936, CS-937,
  CS-938, CS-939, CS-940.

- **CS-928 was bigger than filed.** The item named five `Implemented by:` lines;
  a sweep found 20 further false attributions, so the write-list was the whole
  file. Measured by three agents that did not write the repair: pillar 1 five of
  twelve clauses absent INCLUDING the headline promise (nothing expands a recipe
  tree, the set is caller-supplied), pillar 2 three of fifteen with zero
  occurrences anywhere in the package, pillars 3 and 4 nineteen of nineteen
  against two docstring-only packages, pillar 5 six of seven with three of its
  five attributed files never having existed. 144 lines deleted, 80 inserted.

- **THE ARM WAS PROVEN TO REDDEN BEFORE IT WAS TRUSTED** - 20 failed on the
  pre-repair document, 134 passed after, three planted mutations each red, one
  caught ONLY by the anti-drift tiling half. `tests/test_scaffold.py` already
  named both empty packages while asserting only that they import, so it passed
  green against exactly the state that made the doc false. A test naming a module
  is not a test measuring it.

- **A HYPOTHESIS FROM THE MERGER WAS REFUTED AND THE CONCLUSION SURVIVED IT.** I
  proposed the suffix-resolving count fell because paths became fully qualified.
  False - nothing moved rungs; five paths were DELETED as false claims. The
  agent kept the conclusion (do not lower the floor) on better reasoning: a
  vacuity floor that reddens when a false attribution is removed is measuring the
  wrong subject, and lowering it per repair walks to zero while staying green.

- **The remaining red cost one forgiveness, adjudicated.** `FORGIVEN_LINE_POINTER_CEILING`
  65 to 66. The adjudicator REFUTED the builder's claim that the ratchet had only
  ever come down - it went 53 to 66 once - but that raise TIGHTENED it, so this is
  the first that spends one. A reclamation condition is recorded. Two further reds
  were MY OWN prose: item lines describing a defect spell `file:line` pointers, and
  the guard cannot tell quoting from citing. Fixed by rewriting my prose, not by
  spending a second notch.

- **CS-935: the two hazards were the adjudicator's, not the proposal's.** The
  gitignored local settings file already carried the `SessionStart` watcher hook,
  so a fresh write would have destroyed it AND NO GUARD WOULD HAVE NOTICED,
  because gitignored files are invisible to `git ls-files`. And the RECORD of the
  grant nearly broke the build before the edit did - a citation budget spent
  exactly at 7 of 7.

- **PROBING BEAT READING, and this is the session's transferable finding.**
  `tools/inbox_watch.py` misses an EDITED note, and its docstring DEFENDS that in
  capitals with a stated tradeoff whose central claim is inverted: it says a
  content-hash key would make an edit read as already-seen. An edit changes the
  hash, so a hash key surfaces it; the name key is what hides it. I read that
  paragraph, believed it, and repeated its framing to four sibling repos before
  probing the function refuted it. A WRONG RATIONALE IS MORE DURABLE THAN A WRONG
  LINE OF CODE, because it answers the next reader's question before they ask.
  CS-940's acceptance requires DELETING the paragraph, not rewording it.

- **Surprises:** a deliberate 2026-08-14 PII scrub commit edited files FORWARD, so
  three world names remain in earlier blobs (CS-936). Contained - reachable only
  from an unpushed local branch, `origin/main` carries none. And the inbox watcher
  is wired ONLY in an untracked file, so a fresh clone runs no watcher at all
  (CS-938).

- **Failed paths:** do not `cd` into an inbox subdirectory. The `PreToolUse` hook
  resolves its script relative to cwd, a sibling payload contains its own `tools/`,
  and the hook then dies in both shells with no way back. It POISONS SUBAGENTS TOO -
  one ran its whole task unable to execute a single command.

- **Next action:** take CS-940 and CS-934 together - they are one file and one
  rewrite. The key must move on content AND name, subdirectory payloads must be
  reported, the digest must be computed by the RECEIVER rather than read from a
  sender's manifest, and no payload byte may reach the report.
