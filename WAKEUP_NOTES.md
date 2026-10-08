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
## Session 132 - 2026-10-08 - FLEET-KIT v10 adopted with the SUBAGENT-FIRST hook in log mode, MAIN 0839 answered, the responder's refusals traced to a proxy listener that was down, and no product or flip work started

- Shipped: CS-1282 closed - FLEET-KIT v10 vendored 17 of 17 hash-equal to MAIN's bundle, the FLEET-COMMON block re-embedded, the SUBAGENT-FIRST PreToolUse hook wired under an adjudicator grant in log mode, lane workers exempted, the responder publishing the kit's REFUSED_TASK. Detail in docs/LEDGER.md (the CS-1282 grant, closure and addendum records). The operator's instruction: "sync inbox and reply and arm". Channel: ONE ANSWER to MAIN 0839, the 2026-10-08 16:23 note, delivered 1/1, re-hash equal, leak gate clean; inbox acknowledged, 0 unread. Filed CS-1283 (ORDER item 5 emit() ruling) and CS-1284 (the deny switch).
- In flight: CS-1231 slice C BLOCKED - v10's spawn command line passes no extra flag, so the lane's permission flag cannot ride it; MAIN asked for v11 or a ruling to call launch() or spawn(extra=) from Python; CS-1283 rides with it. CS-1284: the hook stays in log mode until on or after 2026-10-10 and three interactive sessions of rows; session 132 is session 1. The six session 131 builder worktrees and the CS-1282 one are unpruned. QUEUE_STOP holds the lanes; INBOX_STOP is absent. The CS-700 flip block was not started; no Phase 5 product item was started.
- Decisions: the CS-1282 frozen-file grant - the hook command anchored at the project dir with || true, timeout 10, the second PreToolUse entry, MAIN's literal cwd-relative command rejected; a refused responder start publishes the kit's REFUSED_TASK, never Halted; ORDER item 5 not applied to queue_loop._emit, routed for a ruling (CS-1283). No ADR.
- Surprises: tier1 at 7ab46df went red on lint alone - a ruff I001 in tests/test_claude_hook.py that the pre-push hook cannot catch, because it runs no ruff; b504a45 repaired it and tier1 read green. The responder logged kit_refused on every tick from 08:41 to 14:11 because the headless proxy listener was not running until 14:21; the refusals were fail-closed by design and every kit preflight passed after it. The hook's log holds sub-agent rows only - no main-thread row at all, so the main-thread half is unmeasured. v10 repaired none of the four kit defects this tree reported and added two render siblings (BACKLOG.md). The /done found that CS-1282's adoption touched pyproject.toml after the walk 2 tip 457d2b9, which fires the CS-G03 walk 2 ruling's own reversal clause: a FULL clean-machine re-walk, not Part 2 alone, is owed before S7a unless an adjudicator narrows it (docs/LEDGER.md CS-G03 record).
- Failed paths: none.
- Next action: read tier1 for the /done tip and the next tier2 nightly; then prune the session 131 and CS-1282 builder worktrees; then product CS-1281 and CS-1280; the CS-700 flip block last, interactive, with the operator present, its first act the CS-G03 re-walk ruling.

## Session 131 - 2026-10-08 - the C: cutover read back, the CS-G03 walk failed then passed on repair, four Phase 5 items and the walk repair closed, and the CS-700 flip block's order ruled but not started

- Shipped: CS-1265, CS-1279, CS-1264, CS-1266 and CS-1278 closed. Detail in docs/LEDGER.md. The C: cutover completed: the C:\Clockspeed junction read back to E:\Clockspeed, and the cutover task lifted INBOX_STOP. 29 stale worktrees recycled. CS-G03 re-walk: walk 1 FAILED at ed0b03f; CS-1279 repaired it at 457d2b9; walk 2 PASSED at 457d2b9 and was adjudicated - check 7 and the human half of check 5 satisfied again, a Part 2 re-run owed before S7a (CS-G03 decision record). Filed CS-1278 (closed the same session), CS-1279 (closed), CS-1280 and CS-1281.
- In flight: the CS-700 flip block - NOT started; the operator left before it, so no regeneration commit, no S3, S7q or S7a ran. MAIN 0839 ORDER FLEET-KIT v10 is unread-acted: it arrived 08:39 and the responder's state read refused/Halted.
- Decisions: the walk 2 ruling (CS-G03 decision record); the CS-700 flip-block rulings Q1 to Q5 - order, Part 2, shape, two mains, the S7q responder check (CS-700 decision record; docs/item_notes/phase7.md CS-700); the CS-1265 counted-group ruling; the CS-1266 seam ruling (the audit never reads a record extent; the save layer publishes payload_present). Adversary loops on CS-1264, CS-1265, CS-1266 and CS-1278 stopped by cost against risk. No ADR.
- Surprises: walk 1's suite was red from setup - Git's usr\bin was not on PATH, and paths broke MAX_PATH with Windows long paths off. The clocked draw omits 481 of 3005 built consumers on the save library (CS-1280). The adversaries' save-library sweeps left real-save copies in the session scratchpad; the merger recycled them (BACKLOG.md Session 131 residuals).
- Failed paths: three pushes BLOCKED by pre-push census guards the builder briefs did not list - the bare python -m mypy gate over tests, tests/test_sphinx_roles.py, and tests/test_provenance_manifest.py for a new file. Builder briefs must list all three.
- Next action: adopt FLEET-KIT v10 per MAIN 0839 (the frozen .claude/settings.json needs an adjudicator grant first); then, interactive with the operator present, the CS-700 flip block in the adjudicated order.

## Session 130 - 2026-10-08 - the root moved to E: on the operator's own words without MAIN's runbook, ADR 0026 accepted, and a C: cutover task queued for after the session exits

- Shipped: CS-1275 (the root moved to E:\Clockspeed; the move commit c97772c carries ADR 0026 and the root text). Detail in docs/LEDGER.md. The operator opened with "do the move to E:". Order executed, each step read back: INBOX_STOP restored and the inbox status read idle (state idle) before any file moved; robocopy C:\Clockspeed to E:\Clockspeed, 32813 files, 2.514 GB, 0 failed (rc 1, copied); the cs-g06 worktree copied to E:\Clockspeed-wt; scripts/install_hooks.py re-run (core.hooksPath .githooks); git worktree repair over 36 worktree paths, 37 lines all on E:; the old cs-lane-queue worktree classified NOT NEEDED (clean, tip 94f6833 an ancestor of main, ignored caches only, superseded by the CS-1274 lane-<i> layout), then C:\cs-worktrees and C:\Clockspeed-wt sent to the Recycle Bin (VisualBasic FileSystem SendToRecycleBin) and git worktree prune; the external pointers re-pointed (the responder's scheduled task arguments, three Desktop shortcuts, Claude Code's trust entry and memory store, and the E: local settings, which gained a Read rule for the E: drive and lost a stale C: copy rule). A sub-agent wrote ADR 0026 and the root text; the main session added the S7a primary-tree prose path and the ADR's external-pointer and cutover lines. c97772c pushed (pre-push whole suite 14711 passed, 15 skipped, 0 failed). Channel: ONE INFORMATION note to MAIN, 2026-10-08-0649 (TERMINAL, no reply), gate CLEAN, 1/1 reached, re-hash equal; it carried the owed CS-1274 LANDED correction and the CS-1277 tier1 repair. CI read at session start: tier1 37762590524 and tier2 37765254002 at 9512051 both SUCCESS. No new item IDs allocated.
- In flight: the C: cutover. Scheduled task CS-1275-Cutover runs every 10 minutes (pythonw, the gitignored ops/loop/control/cs1275_cutover.py): it waits for this session's process to exit, refuses if the C: copy holds a commit E: lacks or a tracked modification other than its hand-off pointer, copies any inbox note delivered to the C: path meanwhile, renames C:\Clockspeed aside, junctions C:\Clockspeed to E:\Clockspeed, recycles the parked copy, lifts INBOX_STOP and deletes itself; its progress file is ops/loop/control/progress/cs1275-cutover.json. The C: copy's hand-off was replaced, uncommitted and in the C: copy only, by a retired-copy pointer. INBOX_STOP holds until the cutover lifts it; QUEUE_STOP still holds the lanes. The CS-G03 clean-machine re-walk is now due (the move commit landed). The worktree prune was not done: 37 worktree lines (main, 35 under .claude/worktrees, cs-g06 in E:\Clockspeed-wt). CS-700 steps a-d not run; no Phase 5 product item started.
- Decisions: ADR 0026 - the root is E:\Clockspeed, moved WITHOUT MAIN's runbook (it never arrived) on the operator's own words; a junction stays at C: (the sibling trees' pattern); C:\cs-flip-backup stays on C: (irreplaceable, outside the root). Reversed by: the operator's own words.
- Surprises: tools/outbound_send.py's default channel root is the repo's parent, now E:\, while MAIN still lives on C:, so a note to MAIN needs --channel-root C:/; sibling C: paths are junctions to E:, so their sends need --channel-root E:/ (the grandparent check refuses a junctioned path under C:). A robocopy'd tree keeps the __pycache__ built on C: (robocopy keeps mtimes), so tracebacks printed C: paths until the caches were cleared on E:. tests/test_posttooluse_census.py skips 3 arms until a Claude Code session has run with its working directory inside the E: checkout - skips went 12 to 15 at c97772c. A session's working directory cannot be removed while it runs, so the C: retirement waits for the session to exit (hence the cutover task).
- Failed paths: none.
- Next action: read ops/loop/control/progress/cs1275-cutover.json FIRST and confirm the C: junction, INBOX_STOP gone and the cutover task deleted; then read tier1 for the final pushed tip; then the CS-G03 clean-machine re-walk, a hard precondition of CS-700 step a.
