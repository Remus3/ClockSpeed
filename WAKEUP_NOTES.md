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
## Session 136 - 2026-10-10 - five slices cleared their adversaries onto one unpushed landing branch, its integration suite read red on a third-party save in the live save directory, and the SUBAGENT-FIRST hook switched to deny

- Shipped: no code landed on main; main stayed at f8e30bf until the /done. CS-1284 CLOSED: its deny switch was made at 07:19 (the mode file reads deny); the /done recorded the per-session row counts, an adjudicator ruled the lane-exemption re-read after the switch meets the clause, and two acceptance passes refuted only counts, corrected in the record. Housekeeping after the 10:02 reboot killed the first half: a stale `.git/index.lock` (about 9400 s old) cleared by the kit under the tree lock, 3 dead claims released, 4 orphaned progress files set failed. Channel: the gitlock stale-limit defect note to MAIN (outbox 2026-10-10-0718, REVIEW) delivered 1/1, and the 1315 and 2304 answers read 1/1 in MAIN's inbox (agent-reported). CI read: tier1 and the first tier2 nightly after 319cd8a both green at f8e30bf. The /done filed CS-1308 and removed four scratch worktrees whose heads are on branches.
- In flight: the landing branch `s136-land` on f8e30bf, tip subject "CS-1292 - the replace-ref control binds the blob before asserting on it", NOT PUSHED. Each slice on it cleared a distinct adversary (verifier where run): TIER2-RED with CS-1300 (fixes b, c, d, e, g; the concurrency adversary NOT REFUTED on the repaired tip); CS-1302; CS-1280 (verifier CONFIRMED; adversary REFUTED, fixed, narrow re-refute NOT REFUTED; measured on 41 saves: 3005 built, 2993 considered, 469 priced at class default, 12 omitted - MinerMk1 10, WaterPump 2 - against the parent's 2524 considered and 481 omitted; the re-publish of that omitted count is a LEDGER act at its landing); CS-1285 slice A (3 rounds, NOT REFUTED, verifier confirmed with corrections); CS-1292 (4 fix rounds; acceptance and leak lenses NOT REFUTED; a landing fix for an env-echo scan line, NOT REFUTED). A landing fix moved `tests/surface/test_advice_source.py` to expect 1 unpriced machine per the 2026-10-08 ruling. Its integration whole suite (agent-reported) read RED: 84 failed, 14980 passed, 114 skipped, 17 errors - 67 because the agent shell's PATH lacked Git's usr/bin (openssl, sh; they pass with it), 2 real (both fixed on the branch), and 31 save tests that are red on main too. A builder on `s136-savefallback` (from the CS-1292 leak-lens round 4 commit) is making the save layer fall back past a parser-refused newest save, TDD, uncommitted in its worktree at the /done.
- Decisions: CS-1284's lane re-read after the switch meets its clause (adjudicator, ruling A; docs/LEDGER.md). CS-1308 (the checkout root still spelled in tracked files outside CS-1292's scrub) is filed in ROADMAP as a public-flip blocker and absorbs BACKLOG CS-1306. No ADR.
- Surprises: the newest file in the live save directory is a third-party re-encoded save - not written by the game, its header save time float-truncated, its body 11,081 bytes shorter; the parser refuses it with ObjectFormatError and the library sweeps go red on main too. Clockspeed never writes there; moving it is an operator act. An agent shell without Git's usr/bin on PATH turns 67 tests red. A reboot leaves a stale index.lock and running progress files nobody owns. Agents of one session overwrote each other's scratchpad prog.py, msg.txt and possibly freeze.json (BACKLOG).
- Failed paths: the first integration suite, run from an agent shell without Git's usr/bin on PATH - its 67 PATH failures are environmental. A worktree agent cannot fast-forward the main checkout; land with `git push origin s136-land:main` through the git lock, then fast-forward main.
- Next action: finish and refute `s136-savefallback`, cherry-pick it onto `s136-land`, run ONE whole suite with Git's usr/bin on PATH through the suite gate, and on green push to origin main and close the five items.

## Session 135 - 2026-10-09 - CS-959 and CS-1301 closed, FLEET-KIT v15 landed by the responder, four rulings recorded, and three repairs left on unmerged branches short of a surviving adversary pass

- Shipped: CS-959 closed (the community profile complete while the repository is private; adjudicator CLOSE-NOW, HOLD rejected) and CS-1301 closed (the canary arms' leaky controls cut collection at their own tmp dir, and every child failure names itself). The responder landed CS-1303 (FLEET-KIT v15), pushed, its answer delivered 1/1. Filed CS-1304 (ROADMAP), CS-1305 and CS-1306 (BACKLOG), and at the /done CS-1307. Pushed through 032fa77; tier1 at 032fa77 green, all 5 jobs. Detail in docs/LEDGER.md.
- In flight: three unmerged branches, named by tip subject. TIER2-RED with CS-1300 ("CS-815 - the env-echo wrapper arms wait at the foot of their module"): the first candidate refuted four ways; the repair refuted on minor points only - (a) filed as CS-1307, (b) a stale "exit 2" comment, (c) the CS-1300 red test is Windows-only - and a concurrency adversary's verdict was UNKNOWN at the /done. CS-1302 ("CS-1302 - the dev extra pins mypy to the one release this box runs"): the code survived its adversary; it closes only on a green tier1 after the push. CS-1292 ("CS-1292 - hash-pinned binaries, full path scrub, live tests" at the /done): the first candidate refuted by two lenses, six fixes applied and rebased, its suite rerunning at the /done; both lenses re-run next. Plan of record: one batch merge and ONE push once each survives.
- Decisions: CS-1302 pins mypy 2.1.0; CS-1304 retry-once DENIED as masking; CS-1292's holder string, install-detail owner and hash-pinned binary allowlist; the TIER2-RED wait bound 2520 s; CS-959 CLOSE-NOW; the CS-1301 cross-drive sibling in tests/save/test_synthetic.py files nothing. All in docs/LEDGER.md. No ADR.
- Surprises: a crafted .png (PNG magic, a NUL, then text citing an unpublished commit) passed the extension-and-magic binary exemption, exit 0. The TIER2-RED 400 s bound was false: an 804 s wait was measured inside a 1251.6 s whole suite. Two worktree agents shared one scratchpad progress helper and cross-wrote each other's progress files - one was set done falsely, then reset. Free memory fell to 747 MB with three gated suites live, and one child died of the paging-file status.
- Failed paths: the first TIER2-RED candidate and the first CS-1292 candidate, each refuted; a CS-1304 retry-once, denied as masking.
- Next action: read CI (the first tier2 nightly after 319cd8a), then finish the three branches - the outstanding adversary verdicts, the fixes, a re-refute - and land them in one batch push.

## Session 134 - 2026-10-09 - four items closed and CS-1288 half shipped, CS-1285 slice B refuted four times and re-ruled fluid-only, a tier2 load flake fixed on a branch, and the CS-G03 full re-walk found owed

- Shipped: CS-1281, CS-1293, CS-1294 and CS-1296 closed; CS-1288 slices A (`version.changelist_of`, `GAME_CHANGELIST`) and B (the standalone `audit/build.py` BuildCheck) merged, slice C open. Detail in docs/LEDGER.md and the CS-1288 item note. Outside this session's own work the responder landed CS-1290 (FLEET-KIT v13, folding v12, before this session's first commit), CS-1297 (MAIN FIX TEMP-1) and CS-1299 (FLEET-KIT v14). Pushed 94b9318..476ca8f, then 476ca8f..319cd8a; tier1 at 319cd8a green. Filed CS-1298 (the merger) and, at the /done, CS-1300, CS-1301 and CS-1302. CS-1284: session 3 of 3 of rows recorded. Channel: the notes 2026-10-09-0305 (v12 and v13 answer) and 2026-10-08-2120 (v11 answer) each read back in MAIN's inbox, 1/1, SHA-256 equal.
- In flight: TIER2-RED - tier2 37919155122 attempt 1 failed on the windows guards shard, a load flake (attempt 2 green); the fix (branch tip subject "CS-815 - the quiet barrier keeps its file, bounds its wait, fails loud") is unmerged, its first commit refuted for a directory race, and unverified on the 30x loop, the CS-1233 sibling users and the 400 s bound. CS-1285 slice B (tip subject "CS-1285 - slice B fix 3: an unregistered class is never assumed inert") refuted four times, unmerged; the binding v2 ruling is in its item note; build order A, B v2 on that candidate, C, D. CS-1288 slice C waits for CS-1280 and CS-1285, which share its files.
- Decisions: CS-1288 is a standalone BuildCheck (adjudicated); CS-1285 v2 is fluid-only (adjudicated; runner-up, solids measured unless a non-buildable record exists, lost because every real save holds a player); TIER2-RED is a load flake and no budget is raised; the CS-1294 and CS-1288 slice A adversary loops stopped by cost against risk; builders run targeted tests only and the merger runs ONE integration suite. No ADR.
- Surprises: tier1 at 476ca8f went red on mypy version skew - CI resolved mypy 2.4.0 over the `>=1.11` floor, this box runs 2.1.0, and the two code a positional call to a keyword-only parameter differently; b64b41a repaired the site and CS-1302 files the skew. The /done found the CS-G03 escalation FIRED: CS-1290 changed `.githooks/commit-msg` and `.githooks/pre-push` after the walk tip, so a FULL re-walk is owed before S7a (docs/LEDGER.md CS-G03 record). fleet_gitlock's 15-minute stale limit is shorter than a pre-push suite: other owners broke this session's push lock twice (11:53, 12:24) mid-push.
- Failed paths: the suite gate starved - seven builders each ran a serial whole suite on the 2 machine-wide slots, 60+ min each, waiters near their 3600 s timeout; builders now run targeted tests only. The first TIER2-RED fix was refuted (a directory race in the two-waiter arm).
- Next action: TIER2-RED - the 30x loop, the CS-1233 sibling users 5x and the 400 s bound against the tier2 windows guards shard; then an adversary pass and merge.
