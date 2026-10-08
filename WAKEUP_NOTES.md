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
## Session 129 - 2026-10-08 - FLEET-KIT v9 adopted with the unattended responder live, tier2 green, three queue lanes landed, tier1 brought back under its ceiling, and the E: move authorized

- Shipped: CS-1273 (the held commit-graph arm skips by name where its hold does not take; tier2 37733300151 green on all 23 jobs), CS-1272 (FLEET-KIT v9 in one commit plus the H3 fix-forward; INBOX_STOP lifted; the responder's own reply closed MAIN 0830 and FLEET-1), CS-1274 (three queue lanes, a worktree per lane index, the hardcoded C: worktree root gone), CS-1276 (tier2 headroom record retaken with --runs 6, the pending table retired) and CS-1277 (tier1 shard rebalance plus the toolpath scan cache, under the ceiling again). CS-1276 and CS-1277 were allocated at /done for work landed without an ID. Detail in docs/LEDGER.md. Decision record: FLEET-KIT v9, the Stop-hook grant and the Q1/Q2/Q4 scope rulings, filing CS-1274 and CS-1275. Channel: ONE ANSWER to MAIN 2354, 2155 and 1927 (gate CLEAN 6/6, 1/1 reached, re-hash equal), carrying MIG-1 (worktree list 77 lines to 29, 48 to the Recycle Bin then pruned, branch refs 219 = 219) and the MAIN 2155 path inventory (HARDCODED 3, EXTERNAL 22 rows / 164 paths, DOC 62, FIXTURE 37; detail in the gitignored progress directory's mig1-inventory-129 note). 75 inbox items acknowledged (--ack-keys, source session-129-triage), leaving MAIN 0830 for the responder; 0 unread after its run.
- In flight: CS-1275, the E: move - operator-authorized, waiting on MAIN's runbook; the move restores INBOX_STOP and reads the inbox status idle before any file moves. The CS-G03 re-walk is one walk at a tip at or after the move commit, before CS-700 step a. CS-700 flip steps a-d not run. The 0230 ANSWER told MAIN CS-1274 was BUILT NOT LANDED; it landed afterwards - owed in the next batched note. About 20 builder worktrees of this session under .claude/worktrees are NOT NEEDED (content landed or squashed) and were not pruned. The queue lane stays held by QUEUE_STOP. The tier1 read for the final tip was not taken by this record.
- Decisions: FLEET-KIT v9 vendored directly ("rather v9"; reversed by the operator's words or a MAIN kit v10), superseding the session 128 v8 fence. The E: move authorized in the operator's own words for the root half of the CLAUDE.md section 7 entry; the ADR is owed with the move commit (CS-1275). CS-G03 re-walk deferred to after the move (Q2). Adversary loops on the responder's retired-sender rule and on lane lifetime stopped by cost against risk. Tier2 headroom taken with --runs 6. The 420/480 tier-1 pin was not raised. No ADR.
- Surprises: tier1 went red on budget once tier2's record landed - the save shard was dominated by one uncached repository scan (tests/test_toolpath.py 134.61s serial, 10.72s cached), not by its file count. A test literal spelling the CI host's account name failed the personal-data rendering guard on CI only. Three adversary rounds on the responder and two on the lanes each found a real defect. The push gate's concurrency failure fired once: test_probe_refusal_output.py's stubborn-sleep arm got 124 not 137 under concurrent builder load, and passed alone and on retry.
- Failed paths: the first CS-1272 squash (REFUTED twice) and H2 (REFUTED); the first CS-1274 cut (four points) and r2 (the missing /T). A squash removed slice SHAs that eight comments cited, failing the citation gate until reworded. Shard moves alone could not fix the save shard's per-file floor.
- Next action: read tier1 and tier2 for the final pushed tip FIRST; then, while CS-1275 waits on MAIN's runbook, take the next Phase 5 product item (CS-1264, CS-1265, CS-1266 or the D4 fuel rule) and prune this session's builder worktrees.

## Session 128 - 2026-10-07 - MAIN 1927 and MAIN 0310 answered in one note with v8 provenance verified 14 of 14, the v6/v7 vendoring deferral reversed by its own clause, and tier2 red read and filed

- Shipped: no item closed and no code changed. One ANSWER (HOP 2) to MAIN 1927 FIX and MAIN 0310 FLEET-KIT v8 ORDER, sent through tools/outbound_send.py: gate CLEAN, 1/1 reached, destination copy re-hashed equal. Provenance before answering: the 1927 note, the 0310 note and all 12 v8 bundle files hash-equal to MAIN's outbox copies and tracked clean in MAIN's git, 14 of 14. Decision record FLEET-KIT v8 (docs/LEDGER.md). CS-1272 re-worded to v8 now; CS-1273 filed (tier2 red); MAIN 0300 filed as one BACKLOG.md line.
- In flight: CS-1272 v8 vendoring, due 2026-10-08 (session 129), then the v8 adoption ANSWER. RESPONDER still paused by INBOX_STOP; MAIN 0830 and FLEET-1 close only when the unattended responder replies after the v8 commit. 72 inbox notes were UNREAD at session start and were not triaged (none acknowledged). The CS-700 flip steps a-d were not run.
- Decisions: the v6 record's reversal clause (the S9 confirmation still absent at the next attended session) fired, so v8 (carrying v6 and v7) is vendored now in one commit with a CS-G03 re-walk; fence - never re-defer to after S12a without the operator's words or a MAIN ruling. MAIN 0300 supply chain stays in BACKLOG.md under CLAUDE.md section 7, which a MAIN note does not reverse. No ADR.
- Surprises: tier2 failed its three scheduled runs on ef45ed0 (10-05, 10-06, 10-07) on one test, test_flip_checks.py's commit-graph hold control raising no PermissionError on the windows-latest image - the test landed with CS-1267 after the last green tier2 run, so it was never green there. The responder's spawn() passes no note label and no kind, so its usage line would be unattributed. The usage log has never been written: no kit spawn has run since INBOX_STOP.
- Failed paths: none.
- Next action: read tier2 CS-1273 and fix it test-first, then land CS-1272 (v8 vendoring) in one commit, then send the v8 adoption ANSWER to MAIN.

## Session 127 - 2026-10-05 - CS-1271 closed through an adjudicator and two adversaries, FLEET-KIT v6/v7 provenance verified with a partial v7 adoption, and the inbox triaged

- Shipped: CS-1271 closed (generated power is live in the product; a skip on an incomplete input records verdict-indeterminate, outside SETTLED_STEP_KINDS). Detail in docs/LEDGER.md. Decision records, nothing closed: FLEET-KIT v7 decision C and the CS-1225 relocation of the 6.1 MAIN grant quote (both in docs/LEDGER.md, committed in d5f05de). Filed CS-1272 (v7 full adoption straight after CS-700 S12a). MAIN 0905: two memory facts added (memory/concurrent-agents-share-one-scratchpad.md, memory/bare-python3-is-the-store-stub.md). MAIN 0020: no action.
- In flight: session 126's open CI read is DONE - tier1 37262760914 at c6b7ba4 and tier1 37264699918 at 5a7d151 both SUCCESS, read at session start. The CS-700 flip - steps a-d were NOT run; the operator ordered inbox work plus /done, and any commit to main after S7a voids it. Inbox: 63 unread at triage, all classified in the gitignored ops/loop/control/progress/inbox-triage-127.md, NOT acknowledged. MAIN 0830: the unattended reply is STILL OWED while INBOX_STOP holds. The ANSWER to MAIN 0215/2237 is written in the gitignored outbox and is delivered after the push.
- Decisions: FLEET-KIT v7 decision C (partial adoption now; vendoring, block re-embed and headless/lane paths in one commit after S12a; reversed by S12a aborting, a MAIN ruling, or the operator's words). CS-1271: no ledger schema bump, because step kinds are not persisted. No ADR.
- Surprises: a reject made only because a floor was incomplete was counted as settled, so the ledger could complete an "Add N MW" card while the shortfall was unknown - the draw-incomplete reject carried the same flaw before the session. The first CS-1271 cut halted the headroom rule input-missing, visible through GET /api/advice.
- Failed paths: the first CS-1271 cut (adjudicator: REPAIR FIRST) and the second (adversary: REFUTED, plus a false docstring). The repair HELD a second adversary with mutants killed.
- Next action: run CS-700 flip steps a-d, stop at step e and present the S9 own-words line.
