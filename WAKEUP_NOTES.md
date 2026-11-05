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
## Session 155 - 2026-11-04 - a stated target reaches plan.adopt on a real world; eight items closed, and the operator's /done stopped CS-1379 and CS-1382 built and unlanded

- Shipped: CS-1350, CS-1351, CS-1370, CS-1359, CS-1344, CS-1372, CS-1371, CS-1380 closed; the bound.py byproduct docstring corrected; two decision records, CS-1344 clause 2 and CS-1295's nine findings; two notes to MAIN, 1 of 1 each. Detail in docs/LEDGER.md.
- In flight: CS-1379 and CS-1382 are built on one kept local worktree branch, each with an adversary's refutation unrepaired, unlanded: `git log --all --grep=CS-1382` finds it, and each item's section in docs/item_notes/phase5.md says what is owed. CS-1334 waits on host RAM, 21.7 of 31.6 GB free at this /done against its 24 GB gate. CS-1295 stays open with its result ANSWER owed to MAIN. The lanes stay held by MAIN's 1535 and 2006 ORDERS, though the machine quiesce reads lifted with no MAIN note saying so.
- Decisions: no ADR. The rulings are in docs/LEDGER.md and the item sections. CS-1380 landed on its adversary pass and a verifier that stopped at its budget, with no adjudicator on the built item, because the operator's /done came first.
- Surprises: a parent agent's completion notice waits on its live children, and one straggling adversary hid a finished report for 8.5 hours. A read-back in a sent note read a path no run claims, so the note went out wrong and a correction followed. The carried hand-off called nine CS-1295 findings operator-needing, and a reader and an adjudicator found none is. The hand-off's CS-1359 evidence run was a workflow_dispatch, not nightly. No spike contradicted BOOTSTRAP.md.
- Failed paths: CS-1379's ClassName fallback for undelimited names was refuted in the opposite direction, since `A, B` then reads its ClassName; the next attempt rules on quoting the name. CS-1382's ruled (1, 0) raw-supply count was reversed by its own real-world clause: 7 early-world targets went false route-refused.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then rule CS-1379's naming, land it, and repair CS-1382's F1.

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
