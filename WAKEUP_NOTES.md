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

## Session 158 - 2026-11-16 - the lane's two landings graded LAND, six product items closed through planner, adjudicator, builder, adversary and adjudicator, CS-1362 gated

- Shipped: CS-1247 and CS-1253 (the lane's two cycle landings, each graded by an adversary that did not refute it and a distinct adjudicator ruling LAND), CS-1400, CS-1394, CS-1395, CS-1360, CS-1390 and CS-484 closed; CS-1362 gated as CS-G11 on an operator ADR for a dev-only Node tool. Detail in docs/LEDGER.md.
- In flight: nothing dirty. The lane driver exited after its 2 of 2 cycles and no lane runs. CS-1401 (wire interleave_domains into the served list) is the next product action. CS-1366's earliest closing read is 2026-11-19 18:48:37 local. CS-1334 still waits on host RAM. CS-1295, CS-1231 and CS-1358 carried unworked.
- Decisions: no ADR. Two adjudicator rulings, each with its fence in the hand-off's SESSION 158 block: transport rates read from each class's own shipped description with an exact ratio check and no authored constant, proportional plan edges, CS-1390's line written by the inbox responder's tick; and CS-1360's bottleneck as the edge of greatest utilisation of the fastest known carrier of its unit, computed in solve and recorded in the trace, the surface transcribing only.
- Surprises: CS-1394's first build published 0 of 4 pipe rates live, because the shipped text separates its numbers with U+202F and U+00A0 while the fixture used ASCII spaces; the repair reads 16 of 16. CS-1360's first wave-2 build computed carriers and saturation inside surface, a seam breach the adjudicator re-routed into solve. A pre-push with the global python still fails on the conftest redactor (CS-1387), and one push was blocked by the provenance census on new test files. Each pre-push that ran to its end took 18 to 20 minutes at 19.5k to 19.7k tests. No spike contradicted BOOTSTRAP.md.
- Failed paths: a named one-half constant for belt rates (no sanctioned source; the docs state the rate); a highest-rate star as the flow view's mark (it identifies no limit); synthetic docs fixtures written with ASCII spaces; a builder's new files with no provenance row.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then build CS-1401 through planner, adjudicator, builder, adversary and adjudicator.
