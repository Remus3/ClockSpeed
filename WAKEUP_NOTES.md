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

## Session 126 - 2026-10-04 - CS-G08 satisfied in Windows Sandbox, CS-1186 and CS-1187 closed by a never-seen walk, and four product items closed through adversaries

- Shipped: CS-1238, CS-1268, CS-1059, CS-1269, CS-1186, CS-1187 and CS-G08 closed. Detail in docs/LEDGER.md. CS-G03: check 7 and the human half of check 5 SATISFIED, recorded as a decision; the flip stays GATED. Filed CS-1271 (advise.py must pass generators= to balance_of - production is not live in the product until it does).
- In flight: the CS-700 flip, unblocked on its CS-G08 precondition: final-tip S3/S4/S5 bundle and S7q, S7a baseline and control, S8/S8a, then the operator's S9 own-words line. `advise_and_record` (CS-1268) has no caller in clockspeed/ or shell/ - GET /api/advice runs the read-only advise(). NO LANE WAS LOCKED OR ARMED at /done and INBOX_STOP stays in place; the operator ordered the next session headless-driven and away overnight.
- Decisions: CS-G03 partial satisfaction on the second Sandbox walk (rejected: a blind GitHub-clone re-walk, a re-walk at HEAD; why: every clause has a log line the adjudicator read). CS-1268 completes a card only on its rule's definite verdict, graded by the SETTLED_STEP_KINDS allowlist after a denylist missed INPUT_REFUSED. CS-1059 adversary loop stopped by cost against risk. No ADR.
- Surprises: the first Sandbox walk (logged as "walk 2" in the CS-1186 section) FAILED on six defects the override approximation never saw - openssl not on PATH, no Python/git/Node route, Windows timeout shadowing GNU timeout, MAX_PATH tmp names, the mypy-gate user-site control inside a venv. CS-1059's first cut read 75 MW against 2825 MW because placement's allowlist dropped fuel, nuclear and geothermal generators. CS-1238's first advisor drop arm reddened twice per drop.
- Failed paths: README's Python step was written and refuted twice; it now defers to the official Windows guide. An untracked progress file in a worktree ROOT reddened the drift walk, provenance and manifest arms - progress files belong in gitignored ops/loop/control/progress/. Four concurrent whole-suite runs lost xdist workers. A builder write-list without registry/audit/placement blocked CS-1059 until widened.
- Next action: headless: run CS-700 flip steps a-d, stop at step e and record the S9 ask for the operator; in parallel build CS-1271.
