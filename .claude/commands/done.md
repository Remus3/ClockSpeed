---
description: The end-of-session ritual, end to end - checks, ledger, roadmap, wakeup notes, drift guard, the next-session continuation prompt, one commit batch, ONE push, and the marker.
argument-hint: [item ids, e.g. CS-041 CS-042]
---

# /done - end-of-session ritual

## WHO RUNS THIS - ONE SUB-AGENT, NEVER THE MAIN SESSION

FLEET-KIT v10, carried at v11 (MAIN's 2026-10-08 08:39 ORDER, item 4; the FLEET-COMMON banner; CS-1282, CS-1287):
the main session does NOT run these steps. It dispatches the WHOLE of this command -
every step below, with this file's text and the arguments as the prompt - to ONE
sub-agent (the Agent tool, in the background by default), waits for that sub-agent's
completion notification, and relays ONLY its final line - `Done ritual complete, safe
to clear`, or the failure that stopped it - to chat. The sub-agent runs every step
itself and never re-dispatches the whole command. The kit's PreToolUse hook
`ops/fleet_kit/fleet_subagent_first.py` denies Bash, PowerShell, Read, Edit, Write, Grep,
Glob and NotebookEdit in the main thread once its mode is deny, so a step run there
stops at its first tool call.

The ritual's LAST act, step 10's `fleet_done.py mark`, stays inside the sub-agent's
run, after its own read-back - the main session runs nothing after the relay.

Run EVERY step. Do not skip a step because it "looks clean". Record the observed result of
each of steps 0 to 6 in the ledger and the hand-off file - NOT in chat; the results of step 8
onward (push, its suite counts, CI, timing) go only to the push log and the gitignored
`ops/loop/control/done_timing.json`, because nothing is committed after the push (CS-1321). FLEET-COMMON item 5: the ONLY
chat output of this ritual is the line `Done ritual complete, safe to clear`, or the
failure that stopped it. Items: $ARGUMENTS

FLEET-COMMON item 13 (kit v9, `CLAUDE.md` section 2.3.1): this ritual runs UNPROMPTED once
no checklist task remains - no operator prompt, no question.

**ONE GATED WHOLE SUITE, ONE PUSH (MAIN 2026-10-12 DONE-SLOW ORDER, CS-1321).** A /done
runs AT MOST ONE gated whole suite, and it is the pre-push hook of the ritual's ONE push
(step 8; a push the suite gate or the git lock REFUSED ran no suite - its GATE-REFUSAL PATH
says when it is retried). Every ritual edit - code, `docs/LEDGER.md`, `ROADMAP.md`, `WAKEUP_NOTES.md`, the
drift guard results, the hand-off `CS-NEXT-SESSION.txt` - is committed BEFORE that push,
and nothing is committed after it. A flake is never retried by a second whole suite: the
failing tests are re-run ALONE (step 8's flake path). Every whole suite goes through the
kit's suite gate; the pre-push hook already does. Why: MAIN measured the /done median
rising from 62 to 134 min while each ritual ran several gated whole suites through a
machine with ONE suite slot.

**THE CS-700 WINDOW - COMMIT NOTHING, RUN NO SUITE, PUSH NOTHING (CS-1323).** From the
hand-off's CS-700 flip block step b until S12a, no commit of any kind lands on the main tree's
`main` (session 131 Ruling Q1: a /done commit on top of the regeneration re-stales the citation
set). Step 0 reads the window signal: OPEN means HEAD's own commit touches
`tools/sha_citation_historical.json`. Earlier CS-700 preparation commits wrote that file too, so
the signal is not "the only writer": it is sound because step b's regeneration
(`--emit-historical`) writes the file and then nothing else commits until S12a, so inside the
window HEAD's own commit is that regeneration commit (or its S7a image). While the window is
OPEN, or the signal is UNKNOWN, the ritual commits nothing, runs no suite and pushes nothing:
step 1 runs no test suite (the window touches no Part 2 path - `tests/`, `clockspeed/`, `ops/`,
`tools/`); steps 2 to 6 write to disk only and obey the flip block's RECOVERY RULE; steps 7 and
8 do not run, and the DONE-SLOW measurement waits for the first /done that pushes. The hand-off
then orders NO push, and in place of step 6's push wording it and its report say: "CS-700
window: this hand-off and this ritual's records are UNCOMMITTED, on disk only; nothing was
committed, no suite ran, nothing was pushed". Step 9 reads the hand-off back on disk, not
against HEAD. OPEN: step 10 marks `--status done` (the mark hashes the hand-off on disk).
UNKNOWN: the hand-off also says the window signal was unreadable, and step 10 marks
`--status failed --reason "CS-700 window signal unreadable"`. UNKNOWN stops this ritual only
and is never carried forward as OPEN: the next session reads the signal again before any other
work, and a HEAD that still reads UNKNOWN (a merge HEAD) is resolved there by a distinct
adjudicator reading the flip block's state, never by a ritual. The hand-off it leaves on disk,
OPEN or UNKNOWN, carries the KEEP RULE below WORD FOR WORD, so the session that reaches S12a
has it.

**S12a KEEPS THE WINDOW'S RECORDS (CS-1323).** A window /done leaves its records uncommitted,
and S12a resets the main tree. KEEP RULE, in this order, each step only after the one before it:
(1) COPY - before any CS-700 S12a reset of the main tree, copy into a NEW, EMPTY folder of its
own under the tree's gitignored data directory at the tree root, named after the session
number - the number of the session that runs S12a and makes the copy - EVERY path
`git status --porcelain --untracked-files=all` lists, not only the records a window /done left
(the hand-off, `docs/LEDGER.md`, `WAKEUP_NOTES.md`, `ROADMAP.md`); a deleted path is recorded by
name in a list file in that folder. The copy fails, and S12a stops, if that folder already
exists; and before step (2), S12a stops if any listed path is missing from the folder.
(2) RESET - the S12a reset; a reset leaves ignored files alone, so never clean ignored files
then. (3) RESTORE - every copied path IMMEDIATELY after the reset, before any other S12a act,
and only from that folder, then re-apply the recorded deletions. (4) READ-BACK - byte-compare
each restored file against its copy in that folder, covering every copied path, and confirm
each recorded deletion is still absent; on any mismatch, S12a stops. (5) S12a's acts, in their
recorded order.
(6) The closing commit. (7) COMMIT READ-BACK - read the closing commit back: the restored
records are committed and their bytes match HEAD's. (8) RECYCLE - only then send that folder to
the Recycle Bin (FLEET item 9), by the method this tree used for CS-1275, in PowerShell:
`Add-Type -AssemblyName Microsoft.VisualBasic`, then
`[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory('<folder>', 'OnlyErrorDialogs', 'SendToRecycleBin')`.
If S12a halts at any point after the copy, keep the folder and hand the decision to a distinct
adjudicator, recorded in the hand-off. A crash between the reset and the restore leaves that
folder as the ONLY copy: the next session looks for it under the gitignored data directory
before anything else.

## 0. Preconditions

- [ ] RECORD THE RITUAL'S START wall-clock time (local ISO-8601, to the second) - it goes
      into the hand-off (step 6) for MAIN's DONE-SLOW measurement (CS-1321).
- [ ] READ THE CS-700 WINDOW SIGNAL (above) and record OPEN, CLOSED or UNKNOWN. Run, in order:
      - `git rev-list --parents -n 1 HEAD`: a non-zero exit reads UNKNOWN (no HEAD); more
        than two SHAs on its line reads UNKNOWN (a merge HEAD, whose own diff is empty).
      - `git diff-tree --root --no-commit-id --name-only -r HEAD`: a non-zero exit reads
        UNKNOWN; output that lists `tools/sha_citation_historical.json` reads OPEN; output
        that does not list it reads CLOSED.
      OPEN or UNKNOWN changes steps 1 and 6 to 10 exactly as the window paragraph says.
- [ ] PRE-FLIGHT: every checklist task done or carried into the hand-off.
- [ ] State the item IDs (`CS-nnn`) this session closed. An item with no ID gets one now.
- [ ] Classify each closed item into a tier: 0 cosmetic, 1 local logic, 2 schema / engine /
      core algorithm / version bump / public interface. The HIGHEST tier touched decides the
      checks you run.
- [ ] `git status` - list every modified and untracked path. Nothing unexpected, nothing
      containing game data, a save file, or a generated artifact.

## 1. Run the tier-appropriate checks - NO whole suite here - report counts observed THIS RUN

MAIN 2026-10-12 DONE-SLOW ORDER, CS-1321: this step NEVER runs a whole suite, at any tier.
The ritual's ONE gated whole suite is the pre-push hook of its ONE push (step 8) - the hook
already runs it through `ops/fleet_kit/fleet_suite_gate.py` and grades it from a junit
report - and the whole-suite counts are read from THAT push's log.

- [ ] Run from the REPO ROOT with an EXPLICIT target. Never a bare recursive invocation
      from the root - that can sweep runtime state directories and destroy live locks or
      data.
      - tier 0: syntax check plus `python -m ruff check <changed paths>` only.
      - tier 1: `python -m pytest tests/<module> -q` for each changed module.
      - tier 2: `python -m mypy` exactly as CI runs it (no target - its config names the
        package and the suite), `python -m ruff check .`, `python -m ruff format --check .`,
        and TARGETED `python -m pytest tests/<module> -q` for every changed module, plus any
        service restart and mirror sync. NOT the whole suite.
- [ ] Record each exact command, its EXIT CODE, and the pass / fail / skipped counts.
- [ ] **Report only counts observed THIS run. NEVER carry forward a prior count or a
      subagent-reported count.** A filed count is a hypothesis, not a fact.
- [ ] A skipped suite is not a passing suite. If anything was skipped, say what and why.
- [ ] Run each check ONCE and trust the exit code. Re-run only if you edited since. A
      failure that looks like a flake is re-run as the failing tests ALONE, never as a whole
      suite.

## 2. Append the per-item entry to `docs/LEDGER.md`

Append-only, NEWEST-FIRST, one entry per item:

- [ ] Item ID (`CS-nnn`), date, one-line what changed.
- [ ] The verification pointer: the merged FILE and the TEST NAME that proves it.
- [ ] Any decision made, and any license-gate result, stated explicitly.
- [ ] **Never append a per-item completion entry to `CLAUDE.md`** - it is auto-loaded every
      turn and size-budgeted. If the decision must NEVER be reopened, add a one-line
      `Settled` entry to `CLAUDE.md` stating what was decided AND what specifically not to
      re-pitch. Record the fence, not just the conclusion.
- [ ] The ledger cites the item ID, the merged file and the test name, NOT a slice SHA.
      Worktree-agent commits often do not survive cherry-pick.
- [ ] NO BARE IGNORED PATH (CS-1323): never write a gitignored path - this ritual's timing
      record, anything under `ops/loop/control/` or `data/`, the local config - in backticks
      into `docs/LEDGER.md`, `WAKEUP_NOTES.md` or the hand-off. Name it in words ("this
      ritual's timing record"). Arm `R2 declared untracked` of `tests/test_citation_tables.py`
      reads every backticked path in every tracked file outside `.claude/`, and one that
      `.gitignore` matches with no `DECLINED_AS_DECLARED_UNTRACKED` row turns the push suite
      red - CS-1321's first push.

## 3. Update `ROADMAP.md`

- [ ] Move every closed item OUT of `ROADMAP.md`. `ROADMAP.md` holds OPEN work only.
- [ ] An item blocked on a condition OUTSIDE the repo moves to `docs/GATED.md` with the exact
      unblocking condition. Merely unstarted is NOT gated.
- [ ] **Never close a gated item synthetically.** Substituting a proxy for the external
      condition and declaring it done is how a gated backlog gets falsely drained. Split it
      into a DRAIN half (needs the condition) and a PREP half (harness, assertions,
      fixtures) and work the PREP half.
- [ ] New work discovered this session gets an ID and one line, or goes to `BACKLOG.md` if
      aspirational. One line per item - no narrative.

## 4. Refresh `WAKEUP_NOTES.md`

- [ ] Add this session's note at full fidelity.
- [ ] Keep the last 2-3 sessions ONLY. Move everything older to `docs/history_notes.md`.
- [ ] Relocate, do not delete.
- [ ] NO BARE IGNORED PATH (step 2) holds here: a gitignored path is named in words, never
      in backticks.

## 5. Run the drift guard - EVERY `/done`, no exceptions

- [ ] `python tools/drift_guard.py` - record the exit code.
- [ ] `python tools/doc_budget.py` - record the exit code.
- [ ] `python tools/memory_sync.py` if any source doc changed. The markdown is the source of
      truth; the store is a mirror. Never fix a fact only in the mirror.
- [ ] Thirty seconds each time beats a cleanup session later.

## 6. WRITE `CS-NEXT-SESSION.txt` - THE NEXT-SESSION CONTINUATION PROMPT

**This is not a courtesy. It IS the continuity mechanism. Every session ends with one.**
Rediscovery - redoing closed work, re-pitching a refuted idea, acting on a stale doc - is
the dominant failure mode, and this prompt is the defence against it. It is written BEFORE
the push and committed with the session's other work (MAIN 2026-10-12 DONE-SLOW ORDER,
CS-1321), so it NEVER says "pushed". It records its own push in exactly these words:
"push of this commit pending at write time; push result and CI UNREAD - the next
session's first act reads the remote ref against this HEAD and the CI run". The wording
holds whatever the push then does - lands, is blocked by a flake, or is blocked by a real
failure that stops the ritual - because nothing is committed after the push. In the CS-700
window the hand-off is NOT committed and carries the window's UNCOMMITTED wording instead.

It must be complete and self-contained - the operator pastes it into a cold session with no
other context. WHAT GOES IN IT:

- [ ] READ the current `CS-NEXT-SESSION.txt` FIRST. CARRY FORWARD EVERY ITEM in it that
      this session did NOT act on, verbatim or tighter. An item is never dropped because
      the session worked on something else - FLEET-COMMON item 5.
- [ ] The `SESSION: <n+1>` line, where n is the number this session's checklist printed
      (read from the current hand-off's `SESSION: <n>` line). The next session prints
      `Session <n+1> checklist` from it - FLEET-COMMON item 13a.
- [ ] What this session closed, by item ID, one line each.
- [ ] The exact state of anything left half-done, including which files are dirty.
- [ ] The single next action, stated as an imperative. Its FIRST act is always: read the
      remote ref against this HEAD and the CI run for this HEAD's full SHA (the push is
      step 8), and read this ritual's timing record (named in words; step 8 names its
      path). If the remote ref does NOT equal this HEAD, the next session pushes FIRST,
      before any other work - that push is its one gated whole suite for the carried
      commits - and AFTER that push, if the timing record carries `blocked_by_flake`, files
      that test as a `ROADMAP.md` or `BACKLOG.md` item. The hand-off states its own push in the step 6
      wording above - push pending at write time, push result and CI UNREAD - never
      "pushed". When step 0 read the window OPEN or UNKNOWN, the next action orders NO push:
      its first act reads the window signal again, and OPEN keeps the flip block's no-commit
      rule.
- [ ] The open item IDs in priority order with their acceptance criteria.
- [ ] Every decision made this session that must not be re-litigated, with its fence.
- [ ] Any spike result that CONTRADICTED `BOOTSTRAP.md`. The spike wins - say so plainly and
      name the file that must be updated.
- [ ] The files the next session must read first: `CLAUDE.md`, `memory/MEMORY.md`,
      `ROADMAP.md`, `WAKEUP_NOTES.md`, `docs/ARCHITECTURE.md`.
- [ ] Any external condition being waited on.
- [ ] The final report (step 9's content): the step 1 commands and exit codes with the
      counts observed this run, the drift guard exit codes, the ritual's START time from
      step 0, the step 6 wording "push of this commit pending at write time; push result
      and CI UNREAD - the next session's first act reads the remote ref against this HEAD
      and the CI run" (its pre-push suite is the ritual's one gated whole suite), and
      anything you could not verify - labelled unverified rather than
      rounded up to done.

**HOW TO EMIT IT: A FILE, NOT A CHAT FENCE.** Operator directive, 2026-09-19. The fleet
kit requires `<CODE>-NEXT-SESSION.txt` at the repo root in every tree (FLEET item 5). A
fence in a transcript is gone the moment the session is cleared; a file survives.

- [ ] WRITE the whole prompt to `CS-NEXT-SESSION.txt` at the REPO ROOT, overwriting it.
      Whole file, every time - never appended to, never patched. It is a snapshot of one
      handoff, not a log of several.
- [ ] It is TRACKED and it is committed with the session's other work. `CLAUDE.md` section 4
      carries its topology row; `tools/drift_guard.py` exempts it from the tier-1 budget
      guard under `TIER1_NARRATIVE_RECORD` for the same reason `WAKEUP_NOTES.md` is exempt -
      it RECORDS a measurement rather than owning one. Adding a second statement of a tier-1
      duration to any OTHER file still fails guard (k).
- [ ] 7-bit ASCII and LF, per non-negotiable 4 and the line-ending rule. No em-dashes, no
      smart quotes. This is the most-pasted string the project emits and a pasted em-dash is
      how one enters a file in the first place.
- [ ] Emphasise with CAPS, not `**`. It is read as plain text in Notepad, where `**` is two
      literal asterisks.
- [ ] NO BARE IGNORED PATH (step 2) holds here: the hand-off is tracked, so a gitignored
      path - the timing record included - is named in words, never in backticks.
- [ ] NEVER print the hand-off, its path, or a next-session prompt into chat. The file is
      the mechanism; the operator starts the next session with "continue".

## 7. Commit everything - BEFORE the push

MAIN 2026-10-12 DONE-SLOW ORDER, CS-1321: every ritual edit from steps 1 to 6 - code,
`docs/LEDGER.md`, `ROADMAP.md`, `WAKEUP_NOTES.md`, any drift guard repair, the hand-off -
is committed in this step. Nothing is committed after the push (step 8). In the CS-700 window,
or on UNKNOWN (above), this step does not run: commit nothing.

- [ ] `python tools/precommit_gate.py --staged` before staging is even attempted, so a
      violation is caught before the git hook runs. Both layers run; neither alone is
      trusted.
- [ ] Stage deliberately. Never `git add -A` without reading `git status` first.
- [ ] Commit message: 7-bit ASCII, imperative, cites the item ID. For any message with
      special characters, write it to a temp file and use `git commit -F <file>`, or a
      SINGLE-quoted here-string. Never a double-quoted here-string and never a piped string.
- [ ] Every `git commit` runs through the kit's git lock (FLEET-COMMON 16a):
      `python ops/fleet_kit/fleet_gitlock.py run --owner <session_id>.<agent_id> --
      git commit -F <file>`. A bare commit is denied by the claims hook. The owner is the
      claims hook's own id; its deny reason names it.
- [ ] READ BACK: `git status` is clean and HEAD is the commit just made.
- [ ] CI is NOT read in this ritual: the push has not happened yet, and nothing may be
      committed after it to record CI. The hand-off already carries the step 6 wording -
      push pending at write time, push result and CI UNREAD - and makes reading the remote
      ref against its HEAD and CI for that full SHA (`gh run list --commit <full SHA>`) the
      next session's FIRST act. If that run is red, it is the next session's top item.

## 8. ONE push - the ritual's ONE gated whole suite

MAIN 2026-10-12 DONE-SLOW ORDER, CS-1321: exactly ONE `git push` in the ritual that runs a
suite - a push the suite gate or the git lock REFUSED ran none (GATE-REFUSAL PATH below). In
the CS-700 window, or on UNKNOWN (above), this step does not run: push nothing, take no MEASURE.

- [ ] In Git Bash, never PowerShell (PowerShell 5.1's `2>&1` writes UTF-16 and wraps stderr
      lines): `python ops/fleet_kit/fleet_gitlock.py run --owner <session_id>.<agent_id> --
      git push > <log> 2>&1`, stderr captured because the hook, the gate and the git lock
      write their verdict lines there. The log is a file outside the tree - in the session's
      scratch directory or the system temp directory - never a tracked or claimable path
      inside it. Read the log. A bare push is denied by the claims hook.
      Its pre-push hook runs the whole suite through the kit's suite gate with a junit
      verdict - that is the one gated whole suite; record its command, exit code and the
      pass / fail / skipped counts FROM THIS PUSH'S LOG, never from an earlier run.
- [ ] READ BACK after the push: the push log, the remote ref equals local HEAD by FULL SHA
      (`git ls-remote origin refs/heads/<branch>` against `git rev-parse HEAD`), and a clean
      `git status`. A blocked push can report exit 0 - the remote ref is the evidence, the
      exit code is not.
- [ ] GATE-REFUSAL PATH (CS-1323). A refused push ran no suite. The pre-push hook turns a
      suite gate refusal into its own exit 1 ("pytest exit status: [3]", no junit report), so
      the push's exit code never names a refusal: read it from the log, counting ONLY a line
      that STARTS with one of the patterns below - an indented or mid-line occurrence, such as
      pytest failure output quoting one, never counts; a suite that ran and echoed refusal
      lines from its own captured stderr also prints the hook's BLOCKED line, so a gate
      refusal needs that line ABSENT.
      - `^SUITE-GATE: no suite slot free` (the gate's wait limit, `WAIT_S` in
        `ops/fleet_kit/fleet_suite_gate.py`, ran out) together with the hook's no-report line
        `^clockspeed pre-push: pytest wrote no report` and no `^clockspeed pre-push: BLOCKED`
        line, or `^GITLOCK:` in a log with no
        `^clockspeed pre-push:` line (the kit's git lock refused the push and exited 3; the
        hook never ran): confirm the remote ref unmoved and retry the push exactly ONCE
        through the same command; that retry is the ritual's one gated whole suite. A second
        refusal stops the ritual with nothing pushed.
      - `^SUITE-GATE: .+ has uncommitted edits by another live agent` together with
        `^clockspeed pre-push: pytest wrote no report` and no `^clockspeed pre-push: BLOCKED`
        line: NO retry. Stop at once with nothing pushed.
      On either stop: commit nothing more and leave the commits local - the committed hand-off
      already says push pending, result UNREAD, so the next session pushes first - run MEASURE
      below and step 9, and step 10 marks `--status failed --reason "<the refusal>"`, either
      "push refused twice" or "push refused: uncommitted edits by another live agent". A red
      suite is not a refusal and never retries the push: its failing tests are re-run ALONE
      (the flake path below).
- [ ] FLAKE PATH (ii), adjudicated for CS-1321. If the push is BLOCKED by a test that
      passes when re-run ALONE (`python -m pytest <nodeid> -q`):
      - do NOT retry the push - a retry is a second whole suite and breaches the order;
        `--no-verify` never;
      - confirm from the push log AND from the remote ref NOT having moved that the push
        really was blocked;
      - leave the commits local; the next session's first act (the hand-off's next
        action, step 6) finds HEAD unpushed and pushes before any other work, so that
        push carries them through the full hook. The `CLAUDE.md` section 6.1 "nothing
        unpushed" rule is narrowed for this one session gap by the verified order;
      - commit NOTHING more - the no-commit-after-the-push rule has no exception. The
        committed hand-off already says push pending and result UNREAD, so the next
        session's first act (remote ref against HEAD) finds the commits unpushed. Record
        the blocking test's node id and its alone-run result as `blocked_by_flake` in the
        gitignored `ops/loop/control/done_timing.json` (step 8's timing record); the next
        session reads it, pushes first, and only then files the flake as a `ROADMAP.md`
        or `BACKLOG.md` item, carried by its own later push. Never re-push in this ritual. The ritual then
        runs MEASURE below and step 9, and step 10 marks `--status failed --reason
        "push blocked by flake"`, and the chat line is that failure, not the complete
        line.
      A test that FAILS when re-run alone is not a flake: it is the failure that stopped
      the ritual. The committed hand-off stays true - it said push pending and push result
      UNREAD, never "pushed" - and the next session's first act, reading the remote ref
      against its HEAD, finds the push did not land.
- [ ] MEASURE for MAIN's DONE-SLOW answer: record the ritual's END wall-clock time (after
      the read-back), and the push suite's gate `wait_s` and `hold_s` from the kit suite
      gate's `durations.jsonl` - its directory is `gate_dir()` in
      `ops/fleet_kit/fleet_suite_gate.py` (env FLEET_SUITE_DIR, else under LOCALAPPDATA) -
      reading the line whose `tree` is this checkout's folder name, whose `ts` falls
      inside the push and whose `exit` is not null - a refusal inside the gate's slot writes a
      line with `exit` null and `hold_s` 0, which is not the push suite. Because nothing is committed after the push, write these figures
      with the start time from step 0 atomically to the gitignored
      `ops/loop/control/done_timing.json` - MERGED into it, never replacing a
      `blocked_by_flake` key the flake path already wrote - and the next session carries them into its own
      hand-off. Never write an absolute path into tracked text - repo-relative only.

## 9. Final report - in the hand-off file, never in chat

The report was written into `CS-NEXT-SESSION.txt` in step 6 and committed in step 7, BEFORE
the push (MAIN 2026-10-12 DONE-SLOW ORDER, CS-1321). The push outcome, its suite counts, CI
and the timing figures are NOT committed in this ritual: they are in the push log and this
ritual's timing record (step 8 names its path), and the next session reads them, with CI, as its first
act. READ BACK the hand-off file on disk against the committed blob (`git diff --quiet
HEAD -- CS-NEXT-SESSION.txt`).

## 10. The /done marker - the LAST act (FLEET-COMMON item 15, kit v9)

- [ ] Only after the push and the hand-off are READ BACK, run
      `python ops/fleet_kit/fleet_done.py mark --session <n> --status done`, where `<n>` is
      THIS session's number - the one its checklist printed, not the `n+1` the new
      hand-off carries. The kit reads HEAD and hashes the hand-off itself and writes the
      gitignored `ops/loop/control/session_done.json`; its Stop hook then titles the tab.
      The mark writes no commit. Nothing is committed after it - a later commit or hand-off
      edit voids the marker.
- [ ] If a step failed and stopped the ritual, still call it, naming that step:
      `python ops/fleet_kit/fleet_done.py mark --session <n> --status failed --reason "<step>"`
- [ ] A mark that exits non-zero or prints `failed` after a `done` call is itself the
      failure that stopped the ritual.

Then print exactly one chat line and nothing else:

    Done ritual complete, safe to clear

If a step failed and stopped the ritual, print that failure instead of the line.
