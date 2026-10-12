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
## Session 137 - 2026-10-11 - the landing branch landed with CS-1309, eight items closed, CS-1285 slice B v2 landed, five rulings recorded, and CS-1312 filed on a purge that deletes through a junction

- Shipped: pushed f8e30bf..1668710 through the pre-push suite on the second try (the first stopped at a relocated heading's state word; the second's log reads 15575 passed, 12 skipped); tier1 38185182369 at 1668710 SUCCESS on all five jobs. CLOSED: CS-1300, CS-1280 (its omitted count re-published), CS-1292, CS-1308 (kept set ruled first), CS-1309 (the newest-save fallback), CS-953 (MOOT, not satisfied - ADR 0018 amended, decision unchanged), CS-453 (superseded by CS-1312), and at the /done CS-1302 (bare mypy exit 0 in that tier1 run). CS-1285 slices A and B v2 LANDED; it stays open for C and D. Filed CS-1311 (moved to BACKLOG under Ruling 4's reversal) and CS-1312; the /done filed CS-1313 and CS-1314 from two BACKLOG triggers the CS-1280 close fired, closed the session 134 gitlock BACKLOG line on kit v16's 120-minute ceiling, and added the Ubuntu 26 line. Detail in docs/LEDGER.md.
- In flight: nothing dirty and no branch unlanded; every session 137 branch landed by cherry-pick and is KEPT for CS-1291 part 7 (s137-land, s137-cs1308, s137-cs1308b, s137-cs1285b, s137-cs1311, s136-savefallback and the session 136 slice branches). CS-1285 slices C and D, CS-1288 slice C and CS-1307 (its smallest remaining slice is in phase7.md) are open. Leftover adversary temp dirs (s137_r2c1309_*) sit under the system temp directory, one holding junctions that point only at temp dirs.
- Decisions: Ruling 1 (the flip session turns on private vulnerability reporting, secret scanning and push protection through the API, a fourth S12a act); Ruling 2 (CS-953 moot); Ruling 3 (CS-1308's kept set - the checkout root is not personal data); Ruling 4 (CS-1309's library sweeps are the correct alarm, no tolerance; CS-1311's content pin went to BACKLOG when the operator moved the save out); Ruling 5 (CS-1285 `supply-input-uncovered`; derating option C to BACKLOG). The merger's CS-1309 F2 design: a same-world fallback only when the token is known, else the distinct newest-save-unidentified flag. Adversary loops stopped by cost against risk: CS-1308 after round 4 plus a verifier, CS-1309 after round 3 plus a verifier, CS-1285 B v2 after round 2 plus a verifier. All in docs/LEDGER.md. No new ADR.
- Surprises: the operator moved the third-party re-encoded save to the Recycle Bin after the session's ask ("ok"); the library holds 41 saves, all of which parse, and the 42 library sweeps read green with no pin. The CS-1309 verifier found `purge_work_dir` deletes copy-suffixed files through a junction or symlink into a fake save directory on head and base alike (CS-1312, a non-negotiable 1 exposure with no production caller). The integration suite caught 5 failures no targeted run saw: shifted line pointers into edited files, the archive-rot census and an unbounded subprocess.Popen. The pre-push dated-headings test failed a relocated heading that put "superseded" before its date. The CS-1308 ruling counted 10 scrubbed files where 11 exist.
- Failed paths: the first CS-1308 candidate (scrub before the record; rebuilt with the record first, superseded by s137-cs1308b); the CS-1311 builder stopped at its precondition because the file had already left the library. Same-size source mutants reused stale .pyc until __pycache__ was cleared and the harness ran with `python -B`. A doc agent working in a worktree where another agent stages files risks a commit sweeping up the other's staged paths.
- Next action: CS-1312 - mirror discard_copy's forbidden-root and parent checks in purge_work_dir with junction and symlink tests, or remove it after a consumer check; then an adversary pass.

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
