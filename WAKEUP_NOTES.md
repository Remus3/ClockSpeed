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

## Session 85 - 2026-09-11 - the operator asked for a map, and the save reader turned out to be the thing in the way

- Shipped: CS-977 (the `/api/map` endpoint and the Map panel), CS-978 (the placement and
  inventory models in `clockspeed/audit/`), CS-979 (extraction rates in the registry),
  CS-980 (the `(14,60)` property tag grammar, plus the license gate that ran before it).
  Detail in `docs/LEDGER.md`.
- Filed: CS-981 (route the three items gated behind a gate that is now discharged) and
  CS-982 (two flags bits pinned on almost no evidence).
- In flight: nothing mid-edit. The tree is committed.

- THE OPERATOR SUPPLIED GROUND TRUTH THAT REFUTED A DOCUMENTED GATE, AND THAT IS THE
  SESSION. `docs/GATED.md` recorded under CS-G05 that a `(14,60)` save decodes zero
  property tags and "cannot exercise the decoder at all - it is the CONTROL". The operator
  showed a third-party interactive map rendering container contents out of a save on this
  machine. Same file, same pair. The zero was real and reproduced on demand; the inference
  from it was wrong. A save that decodes nothing under ONE grammar is not a save that
  carries nothing. `CLAUDE.md` section 8 decided it: the probe wins, the gate is corrected.

- Surprises: the wall was BOTH candidates at once, which is why neither alone closed it -
  a lead byte the reader did not skip AND a tag grammar it did not know. Four readings were
  driven against the whole population before one read every record with no breaks. A
  plausible fix and a correct one look identical on a single record.

- Surprises: an adversary was dispatched to refute the zero-properties finding and did not
  refute it - but corrected its WORDING in the way that mattered. The finding had been
  stated as a defect on the production dashboard path; it was neither path-specific nor
  novel, and `docs/GATED.md` already held it. Being right about the fact and wrong about
  its standing is the failure mode to watch for here.

- Surprises: the built-class allowlist was seeded from the only `Build_*_C` spellings in
  the tree, which came out of an ARCHIVED spike report - and three of those nine were the
  only ones present in the operator's world. The map plotted 37 of 698 built actors. A
  read-only census of the world's own classes fixed it to 68 across 15 classes, and what is
  still skipped is counted and published rather than dropped.

- Surprises: a REAL BROWSER found three defects that no arm could see, including one that
  would have fired on every real save - the account-id leak detector matching the fractional
  tail of a coordinate. Nothing had driven a browser at this page since session 78. The
  instrument that worked was `tests/surface/audit_harness.py` over plain HTTP with
  Playwright; the in-app browser pane cannot scroll - programmatic and synthetic scrolls
  both leave `window.scrollY` at zero - so it can only ever screenshot the top viewport.

- Failed paths: filtering the panel's warning explainer on the endpoint's own source. It
  dropped exactly the warnings that explain an empty answer, because the emptiness and its
  reason arrive from different layers. The endpoint deliberately does NOT remap a warning's
  source; that field names the layer that flagged it.

- Failed paths: a positional pin. The seam's network-detector baseline was
  `PANEL_MODULES[0]`, ordered by `sorted()` over the server's asset names and stated
  nowhere. A new panel module sorted ahead of it and took the baseline. The arm that caught
  it was doing its job; the repair was to give the baseline a name.

- Decisions: the license gate ran BEFORE any format knowledge was acted on and its verdicts
  are in `docs/LEDGER.md`. The tool the operator demonstrated is the one source that may
  NOT be read - no LICENSE file, private manifest, and a README forbidding reuse in any
  case. Nothing was copied from anywhere; the grammar came from the bytes.

- Next action: CS-981. Route CS-829, CS-830 and CS-831 out of `docs/GATED.md` now that
  their condition is discharged, READING CS-829's fences first - inventory is three items
  and not one, and an operator ruling was once obtained on the premise that it was one.

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
