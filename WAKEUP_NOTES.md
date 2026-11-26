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
## Session 163 - 2026-11-25 - wave 1 group 1: CS-1410 and CS-1261 closed, CS-454.1, CS-1411 and CS-1414 landed, CS-1413's stanza written by the /done, the serial track halted at CS-1415

- Shipped: CS-1410 (the README disclaimer names the studio and the publisher and ends with one trademark sentence) and CS-1261 (local API hardening: loopback by construction, no query-string or header token, a closed set of logged refusal causes, a per-mint random cert subject) closed. Landed and not closed: CS-454.1 (a part of CS-454: the four remaining account-directory redaction defects), CS-1411 (OPERATIONS 10.8, the wave runbook), CS-1414 (the landing stamps paragraph and one New files spelling in the annex) and CS-1413 (the WAVE STATE stanza and its rule line, written into the hand-off by this /done). CS-1441 filed in BACKLOG. Detail in docs/LEDGER.md.
- In flight: nothing dirty. CS-1415 stopped at its clause 7 CHECK with nothing written: three fill rows precede ready product rows in the filed annex, so session 164 first re-places those rows by a ruled unit-step and then resumes CS-1415. CS-1417, CS-1419 part 2 with U-157 and CS-1418 wait behind it on the serial track. CS-1413's binding dry-resume read (S4) and its close adjudication open session 164. CS-1366's read is on or after 2026-11-26 15:29 local; CS-1334 still waits on host RAM (22.0 GB free at this /done) and CS-1418. The queue stop file this session placed was removed at this /done.
- Decisions: ADR 0027 (CS-1261), accepted. Seven adjudicator rulings, S163-R1 to R7, and CS-1413's gap rulings G1 to G19, each fenced in the hand-off's decision block.
- Surprises: the first push was blocked by the SHA citation gate reading a joined RFC 2253 literal in a test file as a SHA; splitting the literal fixed it. CS-454.1's code change moved four pinned locate.py lines and reddened the line-pin citation arms until a pin repair landed. Session 162's CS-1412 adversary processes were still running, one a runaway, and were killed by ruling. The worktree reap deleted CS-1415's builder branch, merged by ancestry, and this /done restored it at the same tip. A targeted test of verify_env failed with the .venv interpreter not first on PATH and passed alone with it first. No spike contradicted BOOTSTRAP.md.
- Failed paths: CS-1415's clause 7 against the filed annex as packed; landing a code change without re-running the line-pin citation tests; a hex-shaped literal joined to letters in a tracked test file.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then CS-1413's S4 read beside the read-only planner of the CS-1415 fill-row re-placement.

## Session 162 - 2026-11-25 - wave 1 group 1 merger track: U-138.5 and U-138.6 filed under CS-1409, CS-1412's chain column landed and left open by ruling, the serial track halted for /done

- Shipped: nothing closed and no id allocated. Landed: U-138.5 (THE PLAN's BACKLOG, phase 6, phase 4 follow-up and phase 7 batches, under CS-1409), U-138.6 (the 552-row wave table in docs/item_notes/wave-plan.md, its hand-off line filed by this /done) and CS-1412 (the Write-list column moved to docs/item_notes/wave-plan-write-lists.md, then the hub chain column and its key table). Still closed and carried for U-151.1 (CS-1419 part 1): the README refresh for v0.1.0 (MAIN 2005, answered 2026-11-16 20:37), CS-1402 (scratch is never authored at a drive root) and CS-1403 (kit v32 adopted). Detail in docs/LEDGER.md.
- In flight: nothing dirty. The serial track halted after CS-1412 by ruling. CS-1413 (U-142) is next, then CS-1411, CS-1414, CS-1415, CS-1417, CS-1419 part 2 with U-157, CS-1418 and CS-1366's read (on or after 2026-11-26 15:29 local). CS-1409 stays open on clause 6 (no rows for U-071 and U-045), the CS-1439 re-placement and a re-grade of all 17 clauses. CS-1412 stays open on clause 5 (no doc-slice rows), clause 6 (the shell/main.js entry read, owed at CS-619's first wave entry) and clause 8 (graded on 29 items only). CS-1334 still waits on host RAM and CS-1418. The queue stop file was removed at this /done.
- Decisions: no ADR. Three adjudicator rulings, each fenced in the hand-off's SESSION 162 block: CS-1412 proceeds because it reads only the wave table; the serial track halts after CS-1412 for this /done, and CS-1411 is never moved ahead; U-151.1, dropped from the session 161 hand-off's order, is applied by this /done and put back in the order.
- Surprises: the U-138.6 hand-off line did not fit (24954 + 79 against 25000), so it waited for this /done's D80 route: the session 156 and 157 decision blocks became one line, and the /done report block became one line pointing at its ledger record. The wave table brought its annex near the leaf budget, so CS-1412 first moved the Write-list column to a sibling annex. No spike contradicted BOOTSTRAP.md.
- Failed paths: CS-1412's first CHECK compared spellings instead of files and hid a fault (the mutation adversary refuted it, and the CHECK was hardened); a hand-off order that left out U-151.1.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then CS-1413 (U-142).

## Session 161 - 2026-11-25 - wave 0 run to its exit and wave 1 group 1 begun: CS-1408, CS-1416 and CS-1401 closed, THE PLAN's rows filed as CS-1409 to CS-1440, CS-1366's read FAIL

- Shipped: CS-1408 (the game build re-pinned to CL-520140), CS-1416 (ADR numbers by one writer, OPERATIONS 10.9) and CS-1401 (the advice list served domain-interleaved, visible cards first) closed; THE PLAN's rows filed as CS-1409 to CS-1440 in the phase 7, phase 5 and phase 6 batches, 60 rows staged unfiled; U-158's citation line; the wave 0 exit record. Detail in docs/LEDGER.md.
- In flight: nothing dirty. The next merger unit is U-138.5, then U-138.6 and the wave 1 group 1 order the hand-off lists. CS-1366's closing read FAILED (31 gated exit-nonzero rows after the window opened have no failing-id log), so its window restarts; the earliest next read is 2026-11-26 15:29 local. CS-1334 is blocked twice: free RAM 23.0 to 23.3 of 31.62 GB against the 24 GB gate, and U-152 (CS-1418) not landed. The queue stop file was removed at this /done; no lane runs.
- Decisions: no ADR. Fences in the hand-off's SESSION 161 block: U-052 and U-145 not filed; staging under a leaf budget follows wave order, staged rows recorded in the batch record; filed acceptance respells a line-number citation as "path line N"; tracked text cites no unpublished SHA; a closed item's leaf section is deleted when its LEDGER record carries it; CS-1401 serves visible cards first, then hidden; D51's wording governs over spec clause 6.
- Surprises: U-151's entry check failed (U-157 clauses 1 to 5 not met), so U-151 was filed as CS-1419 carrying U-157's clauses as 13 to 21. Free RAM stayed under the CS-1334 gate after the operator freed RAM and two orphaned browser trees were closed. No spike contradicted BOOTSTRAP.md.
- Failed paths: a U-138 batch gate without tests/test_citation_guard_shapes.py, which let a red reach a pre-push and blocked one push; one interleave over all cards for CS-1401 (rejected for visible first, then hidden).
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then THE PLAN's wave 1 group 1 from U-138.5.
