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

## Session 131 - 2026-10-08 - the C: cutover read back, the CS-G03 walk failed then passed on repair, four Phase 5 items and the walk repair closed, and the CS-700 flip block's order ruled but not started

- Shipped: CS-1265, CS-1279, CS-1264, CS-1266 and CS-1278 closed. Detail in docs/LEDGER.md. The C: cutover completed: the C:\Clockspeed junction read back to E:\Clockspeed, and the cutover task lifted INBOX_STOP. 29 stale worktrees recycled. CS-G03 re-walk: walk 1 FAILED at ed0b03f; CS-1279 repaired it at 457d2b9; walk 2 PASSED at 457d2b9 and was adjudicated - check 7 and the human half of check 5 satisfied again, a Part 2 re-run owed before S7a (CS-G03 decision record). Filed CS-1278 (closed the same session), CS-1279 (closed), CS-1280 and CS-1281.
- In flight: the CS-700 flip block - NOT started; the operator left before it, so no regeneration commit, no S3, S7q or S7a ran. MAIN 0839 ORDER FLEET-KIT v10 is unread-acted: it arrived 08:39 and the responder's state read refused/Halted.
- Decisions: the walk 2 ruling (CS-G03 decision record); the CS-700 flip-block rulings Q1 to Q5 - order, Part 2, shape, two mains, the S7q responder check (CS-700 decision record; docs/item_notes/phase7.md CS-700); the CS-1265 counted-group ruling; the CS-1266 seam ruling (the audit never reads a record extent; the save layer publishes payload_present). Adversary loops on CS-1264, CS-1265, CS-1266 and CS-1278 stopped by cost against risk. No ADR.
- Surprises: walk 1's suite was red from setup - Git's usr\bin was not on PATH, and paths broke MAX_PATH with Windows long paths off. The clocked draw omits 481 of 3005 built consumers on the save library (CS-1280). The adversaries' save-library sweeps left real-save copies in the session scratchpad; the merger recycled them (BACKLOG.md Session 131 residuals).
- Failed paths: three pushes BLOCKED by pre-push census guards the builder briefs did not list - the bare python -m mypy gate over tests, tests/test_sphinx_roles.py, and tests/test_provenance_manifest.py for a new file. Builder briefs must list all three.
- Next action: adopt FLEET-KIT v10 per MAIN 0839 (the frozen .claude/settings.json needs an adjudicator grant first); then, interactive with the operator present, the CS-700 flip block in the adjudicated order.
