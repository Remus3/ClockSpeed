---
description: The end-of-session ritual, end to end - suite, commit, push, ledger, roadmap, wakeup notes, drift guard, CI, and the next-session continuation prompt.
argument-hint: [item ids, e.g. CS-041 CS-042]
---

# /done - end-of-session ritual

Run EVERY step. Do not skip a step because it "looks clean". Record the observed result of
each one in the ledger and the hand-off file - NOT in chat. FLEET-COMMON item 5: the ONLY
chat output of this ritual is the line `Done ritual complete, safe to clear`, or the
failure that stopped it. Items: $ARGUMENTS

## 0. Preconditions

- [ ] State the item IDs (`CS-nnn`) this session closed. An item with no ID gets one now.
- [ ] Classify each closed item into a tier: 0 cosmetic, 1 local logic, 2 schema / engine /
      core algorithm / version bump / public interface. The HIGHEST tier touched decides the
      suite you run.
- [ ] `git status` - list every modified and untracked path. Nothing unexpected, nothing
      containing game data, a save file, or a generated artifact.

## 1. Run the tier-appropriate suite - report counts observed THIS RUN

- [ ] Run from the REPO ROOT with an EXPLICIT target directory. Never a bare recursive
      invocation from the root - that can sweep runtime state directories and destroy live
      locks or data.
      - tier 0: syntax check plus `python -m ruff check <changed paths>` only.
      - tier 1: `python -m pytest tests/<module> -q`
      - tier 2: `python -m pytest tests -q` plus `python -m mypy clockspeed` plus any service
        restart and mirror sync.
- [ ] Record the exact command, its EXIT CODE, and the pass / fail / skipped counts.
- [ ] **Report only counts observed THIS run. NEVER carry forward a prior count or a
      subagent-reported count.** A filed count is a hypothesis, not a fact.
- [ ] A skipped suite is not a passing suite. If anything was skipped, say what and why.
- [ ] Run the suite ONCE and trust the exit code. Re-run only if you edited since.

## 2. Commit and push

- [ ] `python tools/precommit_gate.py --staged` before staging is even attempted, so a
      violation is caught before the git hook runs. Both layers run; neither alone is
      trusted.
- [ ] Stage deliberately. Never `git add -A` without reading `git status` first.
- [ ] Commit message: 7-bit ASCII, imperative, cites the item ID. For any message with
      special characters, write it to a temp file and use `git commit -F <file>`, or a
      SINGLE-quoted here-string. Never a double-quoted here-string and never a piped string.
- [ ] `git push`. Read the output - a push that printed an error is not a push.
- [ ] Record the resulting commit SHA, but remember: the LEDGER cites the item ID, the merged
      file and the test name, NOT the slice SHA. Worktree-agent commits often do not survive
      cherry-pick.

## 3. Append the per-item entry to `docs/LEDGER.md`

Append-only, NEWEST-FIRST, one entry per item:

- [ ] Item ID (`CS-nnn`), date, one-line what changed.
- [ ] The verification pointer: the merged FILE and the TEST NAME that proves it.
- [ ] Any decision made, and any license-gate result, stated explicitly.
- [ ] **Never append a per-item completion entry to `CLAUDE.md`** - it is auto-loaded every
      turn and size-budgeted. If the decision must NEVER be reopened, add a one-line
      `Settled` entry to `CLAUDE.md` stating what was decided AND what specifically not to
      re-pitch. Record the fence, not just the conclusion.

## 4. Update `ROADMAP.md`

- [ ] Move every closed item OUT of `ROADMAP.md`. `ROADMAP.md` holds OPEN work only.
- [ ] An item blocked on a condition OUTSIDE the repo moves to `docs/GATED.md` with the exact
      unblocking condition. Merely unstarted is NOT gated.
- [ ] **Never close a gated item synthetically.** Substituting a proxy for the external
      condition and declaring it done is how a gated backlog gets falsely drained. Split it
      into a DRAIN half (needs the condition) and a PREP half (harness, assertions,
      fixtures) and work the PREP half.
- [ ] New work discovered this session gets an ID and one line, or goes to `BACKLOG.md` if
      aspirational. One line per item - no narrative.

## 5. Refresh `WAKEUP_NOTES.md`

- [ ] Add this session's note at full fidelity.
- [ ] Keep the last 2-3 sessions ONLY. Move everything older to `docs/history_notes.md`.
- [ ] Relocate, do not delete.

## 6. Run the drift guard - EVERY `/done`, no exceptions

- [ ] `python tools/drift_guard.py` - record the exit code.
- [ ] `python tools/doc_budget.py` - record the exit code.
- [ ] `python tools/memory_sync.py` if any source doc changed. The markdown is the source of
      truth; the store is a mirror. Never fix a fact only in the mirror.
- [ ] Thirty seconds each time beats a cleanup session later.

## 7. Confirm CI is green

- [ ] Read the actual run status for the pushed commit. A claim that CI is green is not
      evidence; the run status is.
- [ ] If it is still running, say so. Do not predict the result.
- [ ] If it is red, that is the top item of the continuation prompt.

## 8. WRITE `CS-NEXT-SESSION.txt` - THE NEXT-SESSION CONTINUATION PROMPT

**This is not a courtesy. It IS the continuity mechanism. Every session ends with one.**
Rediscovery - redoing closed work, re-pitching a refuted idea, acting on a stale doc - is
the dominant failure mode, and this prompt is the defence against it.

It must be complete and self-contained - the operator pastes it into a cold session with no
other context. WHAT GOES IN IT:

- [ ] READ the current `CS-NEXT-SESSION.txt` FIRST. CARRY FORWARD EVERY ITEM in it that
      this session did NOT act on, verbatim or tighter. An item is never dropped because
      the session worked on something else - FLEET-COMMON item 5.
- [ ] What this session closed, by item ID, one line each.
- [ ] The exact state of anything left half-done, including which files are dirty.
- [ ] The single next action, stated as an imperative.
- [ ] The open item IDs in priority order with their acceptance criteria.
- [ ] Every decision made this session that must not be re-litigated, with its fence.
- [ ] Any spike result that CONTRADICTED `BOOTSTRAP.md`. The spike wins - say so plainly and
      name the file that must be updated.
- [ ] The files the next session must read first: `CLAUDE.md`, `memory/MEMORY.md`,
      `ROADMAP.md`, `WAKEUP_NOTES.md`, `docs/ARCHITECTURE.md`.
- [ ] Any external condition being waited on.

**HOW TO EMIT IT: A FILE, NOT A CHAT FENCE.** Operator directive, 2026-09-19. LL, LW and
RC each carry `<CODE>-NEXT-SESSION.txt` at their repo root with a Desktop shortcut pointing
at it, and this repository was the one that did not. A fence in a transcript is gone the
moment the session is cleared; a file survives, and the shortcut means the operator opens
it without finding the session it came from.

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
- [ ] CONFIRM the Desktop shortcut still resolves: `CS-NEXT-SESSION.lnk` must target
      `C:\Clockspeed\CS-NEXT-SESSION.txt`. A shortcut that lost its target is a handoff that
      silently stopped being delivered, and nothing else in the ritual would notice.
- [ ] NEVER print the hand-off, its path, or a next-session prompt into chat. The file and
      its shortcut are the mechanism; the operator starts the next session with "continue".

## 9. Final report - in the hand-off file, never in chat

Write into `CS-NEXT-SESSION.txt`: the suite command and exit code, the counts observed this
run, the commit SHA, the push result, the drift guard exit codes, the CI status you READ,
and anything you could not verify - labelled unverified rather than rounded up to done.
Then commit it, and print exactly one chat line and nothing else:

    Done ritual complete, safe to clear

If a step failed and stopped the ritual, print that failure instead of the line.
