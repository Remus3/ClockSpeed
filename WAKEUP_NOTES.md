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
## Session 134 - 2026-10-09 - four items closed and CS-1288 half shipped, CS-1285 slice B refuted four times and re-ruled fluid-only, a tier2 load flake fixed on a branch, and the CS-G03 full re-walk found owed

- Shipped: CS-1281, CS-1293, CS-1294 and CS-1296 closed; CS-1288 slices A (`version.changelist_of`, `GAME_CHANGELIST`) and B (the standalone `audit/build.py` BuildCheck) merged, slice C open. Detail in docs/LEDGER.md and the CS-1288 item note. Outside this session's own work the responder landed CS-1290 (FLEET-KIT v13, folding v12, before this session's first commit), CS-1297 (MAIN FIX TEMP-1) and CS-1299 (FLEET-KIT v14). Pushed 94b9318..476ca8f, then 476ca8f..319cd8a; tier1 at 319cd8a green. Filed CS-1298 (the merger) and, at the /done, CS-1300, CS-1301 and CS-1302. CS-1284: session 3 of 3 of rows recorded. Channel: the notes 2026-10-09-0305 (v12 and v13 answer) and 2026-10-08-2120 (v11 answer) each read back in MAIN's inbox, 1/1, SHA-256 equal.
- In flight: TIER2-RED - tier2 37919155122 attempt 1 failed on the windows guards shard, a load flake (attempt 2 green); the fix (branch tip subject "CS-815 - the quiet barrier keeps its file, bounds its wait, fails loud") is unmerged, its first commit refuted for a directory race, and unverified on the 30x loop, the CS-1233 sibling users and the 400 s bound. CS-1285 slice B (tip subject "CS-1285 - slice B fix 3: an unregistered class is never assumed inert") refuted four times, unmerged; the binding v2 ruling is in its item note; build order A, B v2 on that candidate, C, D. CS-1288 slice C waits for CS-1280 and CS-1285, which share its files.
- Decisions: CS-1288 is a standalone BuildCheck (adjudicated); CS-1285 v2 is fluid-only (adjudicated; runner-up, solids measured unless a non-buildable record exists, lost because every real save holds a player); TIER2-RED is a load flake and no budget is raised; the CS-1294 and CS-1288 slice A adversary loops stopped by cost against risk; builders run targeted tests only and the merger runs ONE integration suite. No ADR.
- Surprises: tier1 at 476ca8f went red on mypy version skew - CI resolved mypy 2.4.0 over the `>=1.11` floor, this box runs 2.1.0, and the two code a positional call to a keyword-only parameter differently; b64b41a repaired the site and CS-1302 files the skew. The /done found the CS-G03 escalation FIRED: CS-1290 changed `.githooks/commit-msg` and `.githooks/pre-push` after the walk tip, so a FULL re-walk is owed before S7a (docs/LEDGER.md CS-G03 record). fleet_gitlock's 15-minute stale limit is shorter than a pre-push suite: other owners broke this session's push lock twice (11:53, 12:24) mid-push.
- Failed paths: the suite gate starved - seven builders each ran a serial whole suite on the 2 machine-wide slots, 60+ min each, waiters near their 3600 s timeout; builders now run targeted tests only. The first TIER2-RED fix was refuted (a directory race in the two-waiter arm).
- Next action: TIER2-RED - the 30x loop, the CS-1233 sibling users 5x and the 400 s bound against the tier2 windows guards shard; then an adversary pass and merge.

## Session 133 - 2026-10-08 - three Phase 5 and flip-track rulings recorded, CS-1286 closed on its measured cause, two product builds left unmerged before their adversary pass, and FLEET-KIT v11 adopted by the unattended responder

- Shipped: CS-1286 closed - measurement only: the four 12 MW MinerMk2 records are one miner's first saves, written on older builds whose Mk2 nameplate was 12 MW. Detail in docs/LEDGER.md. DECISION RECORDS, nothing closed: CS-1280 (a tagless consumer is priced at its class default in its own counted group only when its payload read clean), CS-1285 (the D4 fuel rule's design, Q1 to Q3), CS-G03 (the re-walk scope: a delta re-walk, Part 2 alone, with an escalation clause). Filed CS-1285, CS-1286 and CS-1288. The unattended responder adopted FLEET-KIT v11 as CS-1287 in its own run under its own gates - three commits on main, its closure record in docs/LEDGER.md. CS-1284 rows: 2 of 3 sessions, with the positive control (docs/LEDGER.md CS-1284 record). Housekeeping: 7 landed builder worktrees recycled (CS-1264, CS-1265, CS-1266 with its 41 real-save copies, CS-1278, two CS-1279, CS-1282), branches kept; the CS-1280 measurement's 41 save copies under the gitignored work/cs1280/saves recycled by the /done and read back gone, its scripts and measure JSONs kept; four stale "running" progress files with no owning process (ins-d1, ins-d4, ins-d5, main-2155-inventory) set failed.
- In flight: CS-1281 is BUILT on its branch (tip subject "CS-1281 - read clock capability; non-clockable is never elided"), NOT merged: its full suite stopped at 46 percent with one known failure, tests/surface/test_registry.py::test_every_upstream_field_is_either_published_or_withheld_on_the_record - add "clockable" to WITHHELD_FIELDS["Building"] there; the two discharged Session 124 lines in BACKLOG.md still go to docs/history_notes.md. CS-1285 slice B is BUILT on its branch (tip subject "CS-1285 - slice B: the fuel supply audit, per built fuel generator class"), NOT merged: its full suite stopped at 8784 of 14904 with 0 failures, and an adjudicator still rules on its extra indeterminate reasons and on supply as flow net floored at zero. Neither has had the section 5 adversary pass, and every gate figure for both is builder-reported, unverified by the merger. CS-1280's build waits on CS-1281. MAIN's 2031 ORDER, FLEET-KIT v12, arrived unread; the responder handles an ORDER on its own tick. The CS-700 flip block did not start - it is interactive only.
- Decisions: the CS-1280, CS-1285 and CS-G03 rulings above, and CS-1287's three (the triage timeout, the removed exemptions, run_lane.ps1 left for CS-1231 slice C) - all in docs/LEDGER.md. No ADR.
- Surprises: CS-1286's cause was an older build's nameplate, not a pending clock, which exposed CS-1288 - a save from a build other than the pinned one is priced at the pinned nameplate with no warning. v11's ruling R2 UNHOLDS CS-1231 slice C, but CS-1287 left run_lane.ps1 unmoved: the kit command line prints its own usage line, not the result object queue_loop.py parses. The /done re-checked the CS-G03 escalation after v11 touched pyproject.toml again: it does not trigger (docs/LEDGER.md).
- Failed paths: two builders' full suites collided on ONE shared scratchpad full.log - one `>` truncated the other's log. Never run concurrent full suites; give each builder a unique gitignored log path. The inbox responder's `pytest -n auto` saturated the machine and builder full suites ran past 80 minutes - brief every builder for a loaded box.
- Next action: read CI and the inbox (the v12 ORDER); then land CS-1281 - the WITHHELD_FIELDS fix, the BACKLOG relocation, one full suite alone with a unique log, an adversary pass, merge.

## Session 132 - 2026-10-08 - FLEET-KIT v10 adopted with the SUBAGENT-FIRST hook in log mode, MAIN 0839 answered, the responder's refusals traced to a proxy listener that was down, and no product or flip work started

- Shipped: CS-1282 closed - FLEET-KIT v10 vendored 17 of 17 hash-equal to MAIN's bundle, the FLEET-COMMON block re-embedded, the SUBAGENT-FIRST PreToolUse hook wired under an adjudicator grant in log mode, lane workers exempted, the responder publishing the kit's REFUSED_TASK. Detail in docs/LEDGER.md (the CS-1282 grant, closure and addendum records). The operator's instruction: "sync inbox and reply and arm". Channel: ONE ANSWER to MAIN 0839, the 2026-10-08 16:23 note, delivered 1/1, re-hash equal, leak gate clean; inbox acknowledged, 0 unread. Filed CS-1283 (ORDER item 5 emit() ruling) and CS-1284 (the deny switch).
- In flight: CS-1231 slice C BLOCKED - v10's spawn command line passes no extra flag, so the lane's permission flag cannot ride it; MAIN asked for v11 or a ruling to call launch() or spawn(extra=) from Python; CS-1283 rides with it. CS-1284: the hook stays in log mode until on or after 2026-10-10 and three interactive sessions of rows; session 132 is session 1. The six session 131 builder worktrees and the CS-1282 one are unpruned. QUEUE_STOP holds the lanes; INBOX_STOP is absent. The CS-700 flip block was not started; no Phase 5 product item was started.
- Decisions: the CS-1282 frozen-file grant - the hook command anchored at the project dir with || true, timeout 10, the second PreToolUse entry, MAIN's literal cwd-relative command rejected; a refused responder start publishes the kit's REFUSED_TASK, never Halted; ORDER item 5 not applied to queue_loop._emit, routed for a ruling (CS-1283). No ADR.
- Surprises: tier1 at 7ab46df went red on lint alone - a ruff I001 in tests/test_claude_hook.py that the pre-push hook cannot catch, because it runs no ruff; b504a45 repaired it and tier1 read green. The responder logged kit_refused on every tick from 08:41 to 14:11 because the headless proxy listener was not running until 14:21; the refusals were fail-closed by design and every kit preflight passed after it. The hook's log holds sub-agent rows only - no main-thread row at all, so the main-thread half is unmeasured. v10 repaired none of the four kit defects this tree reported and added two render siblings (BACKLOG.md). The /done found that CS-1282's adoption touched pyproject.toml after the walk 2 tip 457d2b9, which fires the CS-G03 walk 2 ruling's own reversal clause: a FULL clean-machine re-walk, not Part 2 alone, is owed before S7a unless an adjudicator narrows it (docs/LEDGER.md CS-G03 record).
- Failed paths: none.
- Next action: read tier1 for the /done tip and the next tier2 nightly; then prune the session 131 and CS-1282 builder worktrees; then product CS-1281 and CS-1280; the CS-700 flip block last, interactive, with the operator present, its first act the CS-G03 re-walk ruling.
