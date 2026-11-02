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
## Session 154 - 2026-11-01 - MAIN's closeout drive before the operator's reboot: both Fleet Insights ORDERS landed, no product slice

- Shipped: CS-1367, CS-1368, CS-1369 closed; scope product-slices committed, launch held. Detail in docs/LEDGER.md.
- In flight: CS-1366 stays open for its 7-day read on or after 2026-11-08. The push, CI, the ONE ANSWER and the acks follow this write: ops/loop/control/progress/closeout-cs.json owns them.
- Decisions: the 2026-10-26 tree_population worktree disposed unlanded by an adjudicator, branch kept for CS-1358. No ADR.
- Surprises: an adversary found a repin tool that silently re-pointed a reason to a swapped handler, and a kill arm whose planted hang ended inside the budget's scaled window; both fixed with tests. A pass that timed out left its commits safe on its branch. No spike contradicted BOOTSTRAP.md.
- Failed paths: gitlock refuses `git cherry-pick`; land with `cherry-pick -n`, then gitlock `git commit -C`.
- Next action: read the drive's progress file, then the remote ref against HEAD by full SHA and CI for that SHA.

## Session 153 - 2026-11-01 - the operator scoped the session to the inbox; no item closed; MAIN's 15:35 ORDER left in a live responder pass

- Shipped: nothing closed and no code changed. Worktree reap removed two clean trees whose commits are on main by patch, branches kept. Detail in docs/LEDGER.md.
- In flight: an unattended inbox-responder pass on MAIN's 2026-11-01 15:35 ORDER (CS-2, CS-3, FLEET-9), started 15:41:01, its order ceiling kills it near 18:41:01; outcome UNREAD at this /done. FLEET-9 partly done and unlanded on the pass's worktree (one commit, 16 uncommitted test files at the last read). CS-2 and CS-3 not started. The ORDER stays unread in the inbox on purpose; a retry depends on it.
- Decisions: the digest finding stays in the hand-off, unfiled, and no id is allocated while a pass that allocates ids is live. No ADR.
- Surprises: a responder pass that exits ok records its note's digest whether or not it handled the note, confirmed by reading `ops/loop/inbox_responder.py::_locked_pass`; an ok exit with no ANSWER never retries by itself. MAIN's ORDER holds the lanes ("CS's lanes stay not relaunched"). No spike contradicted BOOTSTRAP.md.
- Failed paths: none abandoned.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then how the pass ended (its log line, the digest, an ANSWER for the ORDER, its worktree). An ok exit with no ANSWER means the session answers the ORDER itself; ack the ORDER only after an ANSWER is sent and its reached-count read back.

## Session 152 - 2026-10-25 - the operator's worktree request: CS-1352 swept 21 worktrees, 16 orphan work folders and 7 spent branches by content; the hand-off's queue not started

- Shipped: CLOSED: CS-1352 (tier 0; the sweep changed no tracked file): 6 worktrees already in main removed, 2 stale locks held by a dead process unlocked, 11 superseded worktrees removed with their branches kept, 4 dirty worktrees and 16 orphan work folders sent to the Recycle Bin after patch backups and a consumer check, and 7 branches with an empty `git cherry` deleted; about 558 MB recycled; `git worktree list` 5 entries and `git branch --list` 90 heads when this /done read them. Detail in docs/LEDGER.md.
- In flight: nothing dirty. The hand-off's next action - the step 1 reads, the one batched operator ask, then the open items - was NOT acted on and is carried whole; the session-start status board push was not made. The sweep's backups and manifest are in the session 152 sweep archive folder under the gitignored work folder; one detached HEAD is kept at refs/archive/s152/s137_cs1308f2_land_wt. A second branch and worktree prune, on the operator's order, ran concurrently with the /done (refs and worktrees only); its outcome is in the second manifest in that archive folder, and the hand-off says to read it before any branch work.
- Decisions: kept on purpose - the two CS-1318 worktrees, the lane-0 tree, and the session 151 CS-1295 review tree (unique gitignored review data); a branch with any '+' line in `git cherry` is kept, never forced, because a squashed landing reads '+' too. No ADR.
- Surprises: none. No spike contradicted BOOTSTRAP.md.
- Failed paths: none abandoned.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then the carried next action - the step 1 reads, the one batched operator ask (host RAM for CS-1334, the CS-1295 operator-needing findings), then CS-1351 and the open items in order.
