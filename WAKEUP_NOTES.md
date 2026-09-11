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

## Session 84 - 2026-09-11 - the lane's refusal got a name, and a green suite was refuted four times

- Shipped: CS-970. Five commits, `aa5a828` through `03bcf1c`. Detail in docs/LEDGER.md.
- Filed: CS-974 (the `_CI_ROLLUP_BAD` denylist) and CS-975 (nothing reads the driver's
  exit code), both split out of CS-970 on an operator ruling rather than absorbed into it.
- In flight: nothing. The lane is still STOPPED by `ops/loop/control/lanes/QUEUE_STOP`,
  deliberately - see Next action.
- Decisions: two acceptance clauses AMENDED, both recorded in the CS-970 ledger entry
  because an adjudicator required the amendment be written rather than inferred. The
  dirty-worktree precondition does not exist in the code and was refused, not built; the
  eleven-failure threshold became three.
- Surprises: the suite was GREEN at every single refuted commit - 6224, 6241 and 6256
  passes against trees that each still held a live defect. Four adversarial rounds found
  the SAME defect wearing a different field each time, and the fourth was a regression
  this session's own fix had introduced. An allowlist over what counts as progress was
  the only shape that held; every denylist leaked.
- Surprises: `docs/LEDGER.md`'s own 2026-09-11 record is CORRECTED by the new entry. The
  eleven failures were not "a launcher meeting a bare repository" - every failing cycle
  left a worker log, and a bare-repo fault raises before any worker is spawned.
- Surprises: another session committed and PUSHED main mid-work, so three CS-970 commits
  reached `origin/main` before their repairs existed. Main is shared; unpushed is not a
  state this session controlled.
- Failed paths: keying progress on whether `origin/main` moved. It reads a worker that
  pushed the LANE BRANCH, which `tools/headless-queue.md` explicitly instructs on a
  rejected push, as a dead night and killed it at cycle 3. Do not retry that signal.
- Next action: the lane is STILL NOT SAFE TO RE-ARM BLIND, but for a new reason. The
  2026-09-11 trigger is still UNDIAGNOSED, and the row it will now print most likely reads
  `runner_exited_early` or `spawn_failed`, which names the proximate mechanism and points
  at the runner rather than at whatever actually refused. Decide whether one instrumented
  arming to READ that row is worth a night, knowing the row may mislead.


## Session 83 - 2026-09-11 - the lane was armed and worked, and three claims made about other people's trees were wrong

- Shipped from here: NOTHING CLOSED. A frozen-file GRANT for CS-972 was recorded
  (`docs/LEDGER.md`, newest entry but one) and CS-973 was filed. Neither is a closure.
- Shipped by the LANE: CS-303 CLOSED, commit `13cef40`, which the worker pushed to
  `origin/main` itself. tier1 run 34632821764 COMPLETED SUCCESS. The merged file is
  `tests/solve/test_ceiling_fence.py` and the ADR is 0006.

- THE CS-968 FIX IS CONFIRMED IN THE FIELD, not just by its own arm. Three pushes from a
  LINKED WORKTREE this session - the configuration that caused it - each ran the whole
  suite under an exported `GIT_DIR`, and the shared `.git/config` came through byte
  identical but for an expected tracking block. Snapshot the config before a worktree push
  and diff it after; that is the whole measurement and it costs nothing.

- THE LANE WAS ARMED AND IT WORKED, and the handoff's explanation of CS-970 IS WRONG.
  The handoff says CS-970's trigger is "explained by CS-968". CS-968 is fixed and verified,
  and the 1-of-12 pattern REPRODUCED ANYWAY on the first arming after the fix: cycle 1
  completed, cycle 2 failed `LaneLaunchError` in 2.091s with `pid=None`. CS-970 has its own
  live cause and it is still unidentified. Do not close it on the CS-968 story.
  A HYPOTHESIS, NOT A FINDING: a `claude.exe` started at 13:02:03 and the failure landed
  2.091s later, which fits `ops/loop/lane_launcher.py` line 534, where a failed lock
  repoint KILLS the worker it just spawned. The obvious alternative was ruled out - the
  lock file present during cycle 2 was released on failure, so the lane lock is not
  leaking.

- A LANE WORKER KEPT WORKING FOR 15 MINUTES AFTER THE DRIVER WROTE IT OFF. Cycle 1 was
  recorded `ok: true, worker_ok: true` at 13:01:09 with `ci=no-push`, and at 13:02 the
  worktree was DIRTY with the whole CS-303 row uncommitted. The commit landed at 13:17:05,
  after the driver had exited and after cycle 2's worker was supposedly killed. So a
  cycle's completion row says nothing about whether that cycle's work has landed.
  THE DRIVER HAD THE EVIDENCE AND DID NOT USE IT: `ci=no-push` is on the row that says
  `ok: true`.
  MEASURING THE LANE MID-RUN IS MEASURING A MOVING TREE. This session read the worktree at
  13:02, reported "cycle 1 shipped nothing", and was wrong fifteen minutes later. Read the
  lane's state only after the driver has exited, or state the time of the reading.

- THREE CLAIMS ABOUT OTHER PEOPLE'S TREES WERE WRONG, ALL IN ONE DAY, AND THE HABIT IS THE
  FINDING. Two were the withdrawals CS already owed - that a fix was "the one RC already
  has and CS does not", and that "at least three of you have a pre-push hook". The third
  was made THIS session: LW was resolved to Lanternlight and the plugin request delivered
  there. LW IS LEGION WALLPAPER. LW's own note names Lanternlight as a separate repo it
  measured, so one line of the note would have shown it. All three are the same shape: an
  assertion about a tree nobody read. Corrected at both ends and put on the record rather
  than quietly fixed.

- THE CHANNEL IS ANSWERED. Four notes delivered through `tools/outbound_send.py`, gate
  CLEAN with all six classes MEASURED, and every destination copy verified BY DIGEST rather
  than by the sender's own report. The two withdrawals and the Q1-Q5 positions went to all
  four siblings; the plugin request went to Legion Wallpaper and a misdelivery notice to
  Lanternlight. The Q1-Q5 note states its own standing in its first paragraph: where CS
  answers it is REPORTING recorded doctrine, and anything that would be a new commitment is
  marked AWAITING RULING. Nothing commits this project to build anything.

- LW'S FINDING AGAINST THIS REPO IS REAL AND WAS REPRODUCED HERE - 23 real-save copies in
  the live work directory - but its attribution to two named modules WAS NOT ADOPTED. CS
  confirmed the count and that the named files exist, not that they are the writers.
  CS-973's acceptance therefore requires the arm to DISCOVER the writers. Adopting a
  sibling's attribution unmeasured would bank someone else's finding as this project's own.

- Next action: triage whether the lane is re-armed, and read CS-970's own cause rather than
  CS-968's.

---

## Session 82 - 2026-09-11 - the handoff's diagnosis was right, my refutation of it was wrong, and a green push shipped a red commit

CS-968 IS CLOSED AND PROVEN END TO END. `git push` exports `GIT_DIR` to the pre-push
hook WHEN AND ONLY WHEN the push comes from a LINKED WORKTREE. The hook runs
`pytest tests`, so the suite ran holding a pointer at the real repository, and a
throwaway `git init --bare` re-initialised it - putting `core.bare` and a fixture
`[user]` block into the config every worktree SHARES. The full record is in
`docs/LEDGER.md` under CS-968.

THE THING WORTH CARRYING FORWARD IS HOW I GOT IT WRONG, TWICE, THE SAME WAY.

FIRST: I measured a push from the MAIN CHECKOUT, found no `GIT_DIR`, and reported the
handoff's mechanism REFUTED. That is the one arrangement in which the bug cannot fire.
I then cited a sibling tree's note as independent corroboration - it has the identical
blind spot, so two measurements agreed because both were taken in the wrong
configuration. A NEGATIVE IS ONLY AS BROAD AS THE CONFIGURATION IT WAS MEASURED IN, and
agreement between two agents is not evidence when they share a setup.

SECOND: I called a failing arm a probe artifact because it "did not fail in either real
worktree push". Those runs used `-x` and stopped on an earlier failure, so it never
executed. ABSENCE UNDER `-x` IS NOT EVIDENCE OF PASSING. I read a gap in the data as a
result.

AND A THIRD, THE MOST EXPENSIVE: I SHIPPED A RED COMMIT TO `origin/main` AND REPORTED
IT GREEN. The command was `git add`, then `git commit -q -F -` with a heredoc, then
`git push`, all on one compound line. The commit FAILED - the commit-msg gate rejected a
74-character subject - `-q` swallowed the message, and my grep only read the push
markers. `git push` then ran with HEAD at the PREVIOUS commit while the working tree
held the repair. The hook graded the WORKING TREE, found 6198 passed, and pushed a
commit containing the version that fails `tests/test_archive_rot.py`. `origin/main` was
red from `66c707f` until `77a43e2`. Caught by reading the PUSHED BLOB, not the exit
code. FILED AS CS-972.

A GREEN PUSH PROVES THE WORKING TREE WAS GREEN WHEN THE HOOK RAN. It proves nothing
about the pushed commit unless the tree was clean, and nothing checked that.

WHAT FOUND THE LEAKS THAT GREP MISSED: a DECOY. Plant `GIT_DIR` at a throwaway
repository, run the suite, then ask THE DECOY what reached it. My first fix patched
three helpers I had noticed and looked complete on a green suite; the decoy immediately
found two more, including a NESTED `pytest` whose child inherits the pointer and hands
it to everything beneath it. Grep tests whether your search was complete; the decoy
tests the property.

CS-968 HAS TWO INDEPENDENT HALVES and fixing only the first looks finished. The
CHILD-SIDE half is the damaging one, fixed by `tests/git_env.py` at five spawn sites.
The IN-PROCESS half is silent - `load_gate()` imports the gate in process and reads
`os.environ` at call time - and no child-side measurement can see it. Fixed at the FOOT
of `tests/conftest.py`, at import, because module-level code in a test module runs
during COLLECTION before any fixture.

THE SCRUB WENT AT THE FOOT OF THE FILE FOR A MEASURED REASON. Placed mid-file it
inserted about thirty-five lines above every existing one, and the deep archive pins
LINE NUMBERS into `tests/conftest.py`. One pointer changed bucket, `_ROT_FORM` 13 to 12
and `_ROT_EMPTY` 4 to 5, and the guard offered to let me re-pin both counts. Re-pinning
would have banked rot the change itself produced. EDITING A CITED FILE IS A LINE-NUMBER
CHANGE BEFORE IT IS A CONTENT CHANGE - it bit twice this session.

THE SHARED CONFIG WAS ALSO CARRYING A STRANDED FIXTURE IDENTITY and the handoff's claim
that nothing was misattributed was FALSE. Three unpushed commits were authored
`Gate Test <gate@example.invalid>`. Re-authored on an explicit operator ruling; tree
hashes byte-identical across the rewrite, so only authorship changed.

FOUR DEAD DOC CITATIONS were red at `57d70e4` and would have blocked the first push on
their own - the handoff's "0 failed" was wrong about that too. Three were abbreviated
module paths.

BOTH BRANCHES ARE ON ORIGIN. `main` at `77a43e2`, tier1 CI SUCCESS. `cs964-seam` at
`aa30cd5`, 6209 passed, CI was still running when this note was written.

CS-964 IS STILL OPEN AND IS ONE ARM OF FIFTEEN. Pushing the branch published work in
progress; it did not finish it.
