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
## Session 161 - 2026-11-25 - wave 0 run to its exit and wave 1 group 1 begun: CS-1408, CS-1416 and CS-1401 closed, THE PLAN's rows filed as CS-1409 to CS-1440, CS-1366's read FAIL

- Shipped: CS-1408 (the game build re-pinned to CL-520140), CS-1416 (ADR numbers by one writer, OPERATIONS 10.9) and CS-1401 (the advice list served domain-interleaved, visible cards first) closed; THE PLAN's rows filed as CS-1409 to CS-1440 in the phase 7, phase 5 and phase 6 batches, 60 rows staged unfiled; U-158's citation line; the wave 0 exit record. Detail in docs/LEDGER.md.
- In flight: nothing dirty. The next merger unit is U-138.5, then U-138.6 and the wave 1 group 1 order the hand-off lists. CS-1366's closing read FAILED (31 gated exit-nonzero rows after the window opened have no failing-id log), so its window restarts; the earliest next read is 2026-11-26 15:29 local. CS-1334 is blocked twice: free RAM 23.0 to 23.3 of 31.62 GB against the 24 GB gate, and U-152 (CS-1418) not landed. The queue stop file was removed at this /done; no lane runs.
- Decisions: no ADR. Fences in the hand-off's SESSION 161 block: U-052 and U-145 not filed; staging under a leaf budget follows wave order, staged rows recorded in the batch record; filed acceptance respells a line-number citation as "path line N"; tracked text cites no unpublished SHA; a closed item's leaf section is deleted when its LEDGER record carries it; CS-1401 serves visible cards first, then hidden; D51's wording governs over spec clause 6.
- Surprises: U-151's entry check failed (U-157 clauses 1 to 5 not met), so U-151 was filed as CS-1419 carrying U-157's clauses as 13 to 21. Free RAM stayed under the CS-1334 gate after the operator freed RAM and two orphaned browser trees were closed. No spike contradicted BOOTSTRAP.md.
- Failed paths: a U-138 batch gate without tests/test_citation_guard_shapes.py, which let a red reach a pre-push and blocked one push; one interleave over all cards for CS-1401 (rejected for visible first, then hidden).
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then THE PLAN's wave 1 group 1 from U-138.5.

## Session 160 - 2026-11-19 - THE PLAN adopted and wave 0's W0a run to completion; the session 159 push landed and CS-1404 closed

- Shipped: CS-1404 (the secret-sweep blob floor counts distinct tree blobs), CS-1406 (the open-row disposition sweep, re-grade FINAL), CS-914 (per-write staging names, then a 10 s retry budget on the pin replace) and CS-1248.1 (unit-tagged exact Quantity, CS-1248 clauses 1 and 2) closed; the twelve-close wave 0 sweep; CS-913.1 PREP recorded with CS-913 still gated; U-151 graded MET; CS-1405 and CS-1407 filed in BACKLOG; the U-145 frozen-file pre-screen docket (not a grant). Detail in docs/LEDGER.md.
- In flight: nothing dirty. W0b NOT STARTED: U-138.1 is the next merger unit, then U-158's waiting citation line, U-138.2 and the wave 0 exit record. QUEUE_STOP is absent and no lane runs. CS-1366's closing read is due on or after 2026-11-19 18:48:37 local and was not done. CS-1334 still waits on host RAM and U-152.
- Decisions: no ADR. The wave 0 rulings are in docs/LEDGER.md and THE PLAN's rulings; the hand-off's wave 0 block carries the stop point.
- Surprises: the session 159 push was red on test_secret_sweep because a depth-1 CI checkout holds fewer blobs than the tracked paths it counted (CS-1404). write_pin's five instant retries were spent at once under load, so a concurrent replace still escaped after the CS-914 close. The CS-913.1 tests pushed test_world.py over the tests-tree size cap. No spike contradicted BOOTSTRAP.md.
- Failed paths: counting tracked paths as the secret-sweep blob floor; a fixed retry count with no time budget for the pin replace.
- Next action: read the remote ref against this HEAD by full SHA, CI tier1 for that SHA and this ritual's timing record; then THE PLAN's wave 0 W0b from U-138.1.

## Session 159 - 2026-11-19 - planning only: THE PLAN delivered, no item closed, the /done push blocked by one red test

- Shipped: nothing closed and no id allocated. THE PLAN (the master plan on the operator's Desktop) was delivered with its one batched operator ask. Detail in the session 160 ledger records for CS-1401 and U-151.
- In flight: the /done push was blocked by one failed test (10746 passed, 2 skipped); session 160 filed it as CS-1404 and pushed. The ledger record and this entry followed in session 160.
- Decisions: no ADR. Hand-off blocks are relocated only verbatim into a text fence at the end of docs/history_notes.md (Route B); the hand-off's SESSION 159 block carries the fence.
- Surprises: a workflow resume after usage-limit refusals re-ran finished calls, so continuation scripts replaced it. The first account sat at its weekly limit. No spike contradicted BOOTSTRAP.md.
- Failed paths: resuming a workflow across usage-limit refusals.
- Next action: the push, then THE PLAN's Part 0 and wave 0.
