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
## Session 152 - 2026-10-25 - the operator's worktree request: CS-1352 swept 21 worktrees, 16 orphan work folders and 7 spent branches by content; the hand-off's queue not started

- Shipped: CLOSED: CS-1352 (tier 0; the sweep changed no tracked file): 6 worktrees already in main removed, 2 stale locks held by a dead process unlocked, 11 superseded worktrees removed with their branches kept, 4 dirty worktrees and 16 orphan work folders sent to the Recycle Bin after patch backups and a consumer check, and 7 branches with an empty `git cherry` deleted; about 558 MB recycled; `git worktree list` 5 entries and `git branch --list` 90 heads when this /done read them. Detail in docs/LEDGER.md.
- In flight: nothing dirty. The hand-off's next action - the step 1 reads, the one batched operator ask, then the open items - was NOT acted on and is carried whole; the session-start status board push was not made. The sweep's backups and manifest are in the session 152 sweep archive folder under the gitignored work folder; one detached HEAD is kept at refs/archive/s152/s137_cs1308f2_land_wt. A second branch and worktree prune, on the operator's order, ran concurrently with the /done (refs and worktrees only); its outcome is in the second manifest in that archive folder, and the hand-off says to read it before any branch work.
- Decisions: kept on purpose - the two CS-1318 worktrees, the lane-0 tree, and the session 151 CS-1295 review tree (unique gitignored review data); a branch with any '+' line in `git cherry` is kept, never forced, because a squashed landing reads '+' too. No ADR.
- Surprises: none. No spike contradicted BOOTSTRAP.md.
- Failed paths: none abandoned.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then the carried next action - the step 1 reads, the one batched operator ask (host RAM for CS-1334, the CS-1295 operator-needing findings), then CS-1351 and the open items in order.

## Session 151 - 2026-10-24 - seven items and the lane's CS-1245 shipped, CS-1349 and CS-1344 landed open, the first CS-1295 review run landed partial, and the CS-1334 re-walk never launched on host RAM

- Shipped: CLOSED: CS-1328 (every PUBREPO done criterion re-derived by a distinct verifier), CS-1345 (the push identity step for an outsider's fork, docs/OPERATIONS.md section 1.3), CS-1346 (plan.adopt carries the strategy badge into tier 3; its follow-up filed as CS-1351), CS-1347 (greedy returns the lowest-ranking selection it reached; acceptance amended), CS-1340 and CS-1348 (closed with residual, acceptances amended; the 1.0 phase-cost source gated as CS-G10) and CS-1240 (stable-id unmodelled content and its panel; acceptance amended). The headless queue lane closed CS-1245 in one cycle of about 3h44m (clockspeed/solve/bound.py) and filed CS-1350. LANDED, still open: CS-1349 (the pre-push suite command is stable across pushes, under an adjudicated frozen-file grant; its Sandbox walk clause pends CS-1334) and CS-1344 (a test run removes its own cs-pt output on any exit; tools/scratch_sweep.py wired into the /done ritual). Two pushes landed green. C13: the nine session 150 builder worktrees retired by content. Detail in docs/LEDGER.md.
- In flight: nothing dirty. CS-1334's re-walk never launched: host free RAM stayed 15.5 to 20.6 GB over two attempts and 150 minutes of checks against its 24 GB gate; the harness and gate logs are in the gitignored data directory. CS-1344 closes on its ONE ANSWER to MAIN, drafted, carrying this /done's scratch sweep result. CS-1295's first review run is a PARTIAL record: 1,041 rows skimmed, CS-1292 and CS-1293 not folded in, its ANSWER to MAIN owed. Eight session 151 builder and review worktrees are landed and retirable by content (their list is in the data directory).
- Decisions: CS-1291's R6 frozen-file grant DENIED again; CS-815 kept open with its kit-hook half deferred to MAIN (gated as CS-G09, the FIX note delivered 1 of 1); CS-1231 kept open until MAIN's next kit version, its gate committed alone before the lift; CS-1295 counts every file on disk and spawned review-only; CS-1240 rules first-seen as first read since the server started; the forgiven line-pointer ceiling raised from 72 to 73 for CS-1344. No ADR; ADR 0016 amended for CS-1340 and CS-1348.
- Surprises: a cleanup mutant run with the real conftest emptied every live run's cs-pt folder and errored another builder's whole suite (37 errors); the queue lane's progress file sat stale about 3.5 hours while its builder ran; python.org does publish installer sha256 values, through its release API; CI runs Python 3.14 only, never the 3.13 floor; the CS-1295 spawn needed four switches beyond its ruled command. A push from the main checkout no longer exports GIT_DIR to other worktrees (CS-968). No spike contradicted BOOTSTRAP.md.
- Failed paths: the CS-1334 re-walk, twice, on host RAM (not retried at a smaller Sandbox: the first walk stalled under memory pressure).
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record (with the scratch sweep's result); then CS-1351, the advisor-ranking lane rows, CS-1334's walk after the operator frees host RAM, CS-1344's ONE ANSWER and close, and CS-1295's remainder.

## Session 150 - 2026-10-22 - S12a's closing sequence finished and the hold lifted, CS-700, CS-1043 and CS-1244 among the items closed, one scoped queue lane cycle shipped CS-1244, and the first public-clone Sandbox walk read PARTIAL

- Shipped: CLOSED: CS-1332, CS-1317, CS-G03, CS-700, CS-1307, CS-1333, CS-1234 and CS-1335; then CS-1043 (MAIN's version, adjudicated over the lane's), CS-1339 (retargeted to MAIN's code, three guard tests), CS-1341 (the lane reads its starting HEAD after the launch makes the tree, runbook 10.6 rows 8 to 11), CS-1336 (Conventional Commits in .github/CONTRIBUTING.md section 4, document-only), CS-1337 (the README build section), CS-1342 (QUEUE_STOP a per-call halt file, MAIN's 1508 RULING), CS-1343 (SchematicSource, the exact asset-path join, delivered_available; clause 3 amended), CS-1338 (CodeQL default setup, alerts 1 to 3 fixed by the TLS 1.2 pins, alert 4 dismissed as a false positive) and CS-1244 (closed by the lane, reopened by an independent verifier, repaired, closed again). LANDED, not closed: CS-1231 slice C and CS-1328 (b). S12a's closing sequence: W1, C5 R', C6, C7 (the v0.1.0 tag and release), C8 (the ONE CS-1328 ANSWER), C9 (filed as CS-1335 to CS-1338), C11, C12, C13's third pass, the HOLD lift and KEEP (8). FILED: CS-1340, CS-1344, CS-1345, CS-1346, CS-1347, CS-1348 and CS-1349. Detail in docs/LEDGER.md.
- In flight: nothing dirty. CS-1334 stays OPEN: the first fresh-Sandbox walk read PARTIAL, clause 11's suite counts missing because the suite stalled near 70 percent with 0 failures; re-walk after CS-1349 or MAIN's kit fix, or with a Sandbox of at least 20480 MB. CS-1328 and CS-1231 owe distinct closure verifiers. The nine session 150 builder worktrees are landed by content and retirable, by content, never by bulk prune (their list is in the data directory). MAIN's 0647 FIX note (suite-gate commit admission) awaits a kit version.
- Decisions: CS-1043 took MAIN's version over the lane's; CS-1336 is document-only, no hook enforcement; CS-1240's acceptance amended to rule out any fallback in the asset-path join; CS-1343 clause 3 amended on the adjudicator route; the forgiven line-pointer ceiling raise from 70 to 72 ratified after the fact; CS-1318 on HOLD under cost against risk; CodeQL alert 4 dismissed after an adversary's check; the lane scopes keep main's in-progress items out. No ADR.
- Surprises: the lane and main both filed CS-1346 (the unpublished one renumbered to CS-1348); the main session cannot claim a lane row, the root of the CS-1043 collision; a missing pytest target ran a bare whole suite twice; a LEDGER body line opening with a hash sign displaced 7 forgiven citations; the Sandbox walk's suite stalled, inferred to be the suite gate's commit admission (CS-1349). No spike contradicted BOOTSTRAP.md.
- Failed paths: the lane's own CS-1043 (superseded by adjudication); the lane's first CS-1244 closure (reopened on clause 2, then repaired).
- Next action: read the remote ref against this HEAD by full SHA, this ritual's timing record and CI; then read back the operator-ordered deletions and work the hand-off's open items in order, CS-1334 first.
