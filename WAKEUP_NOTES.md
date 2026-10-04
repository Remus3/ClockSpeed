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
## Session 124 - 2026-10-04 - tier2 green again, CS-1263 closed, CS-500 built through S4 with the D4 power rules, slots C4 adopted, and the CS-700 flip rehearsed

- Shipped: CS-1263 closed (the audit draw reads each machine's clock; an untagged clock is the elided default, measured over the 40-save library). Detail in docs/LEDGER.md. PROGRESS records, nothing closed: CS-400 tier2 repair (the phase 4 gate's nested save-suite run sharded in three, timeout not raised; tier2 green at c30e347 and at 69d44c5); CS-500 S1 trace engine, S2 cards, S3 ledger store, S4 rule registry plus the D4 power rules; CS-700 undici 7.29.1 (Dependabot open alerts read 0); CS-1216 slots C4 adopted, grade owed; CS-1234 graded KEEP OPEN (the kit writes task name "Refused"). Adjudication records, already in the ledger: CS-704 two-SHA accept set, CS-700 S7a/S10/S11, CS-701 identity axis. Filed CS-1264..CS-1267.
- In flight: the CS-700 flip. Rehearsal S1..S8 all PASS (refs 71=71=71, bundle restorable, rewrite deterministic). Before S9: an adversary pass on the pre-S7a batch (accept set, identity axis, recorded S7a script), fix CS-1267 (flip_checks clone hard links), probe whether the plan allows branch protection on a private repo, then the operator's own-words confirmation. CS-500 next: S5 every-rule-fires, S6 advise() wiring and the reload half of A3, S9 overlay trace; S7/S8 blocked on CS-1043/CS-1048/CS-1058/CS-1243.
- Decisions: CS-1263 elided clock priced at the default, reversed by a measured save where an untagged machine runs off-default. CS-700/CS-701/CS-704 rulings (ledger). The S1-S3 adversary loops stopped by cost against risk, residual in the trace.py docstring. No ADR.
- Surprises: about 86 percent of library machines carry no clock tag - the save elides the default; the flow audit still reads that as unread (CS-1265). Tier2's clean-checkout probe crossed 300s because the nested child ran tests/save as one call.
- Failed paths: none abandoned. The flip_checks S1 run exited 1 from scratch-dir cleanup alone (0 of 9 checks failed) - a hard-linked commit-graph held by concurrent git; filed as CS-1267, not worked around.
- Next action: confirm tier1 on the pushed tip, then the pre-S7a adversary pass and CS-1267, then the protection probe, then the operator ask.

## Session 123 - 2026-10-04 - the operator session (the other writer of session 122): inspiration ingest filed and partly built, public-readiness prepared, the flip procedure fixed

- Shipped: nothing closed by this /done. The operator session filed the inspiration ingest as CS-1235..CS-1263; directives D1, D3 and D5 closed as CS-1235, CS-1237 and CS-1239 (ledger records 2026-10-04). D2 (CS-1236, what-if overlay) and D4 (CS-1238, every check proves it can go red) are PARTIAL - the rest of each waits on CS-500. CS-1263 filed: the audit's power figure ignores clocks.
- In flight: the public flip (CS-700). Ruled: do NOT use the GitHub visibility switch. Order: tier1 green, run CS-700 (operator confirmation in own words before the remote recreate), re-apply settings from docs/public-readiness.md, enable secret scanning, push protection and private vulnerability reporting, upload the social preview from data/social-preview.png. A cloud-session kit exists OUTSIDE the repo (operator's Documents\cloud-session-kits\clockspeed-*); any cloud PR must merge before the CS-700 flip.
- Decisions: the flip is a recreate under CS-700, never a visibility toggle. No ADR.
- Surprises: tier2 schedule run 37193626407 at 07fcc61 is RED on one job - clean-checkout probe (windows-latest, save shard): tests/save/test_phase4_gate.py::test_the_save_suite_passes_with_no_install_and_no_save, nested suite TimeoutExpired at 300s (1 failed, 1934 passed, 125 skipped in 735.76s). Tier1 run 37191537735 at 07fcc61 is green.
- Failed paths: push-gate suites fail when several run concurrently on this box (OOM, timeouts); filed to BACKLOG.md under Push gate.
- Next action: repair the tier2 windows save-shard probe red without raising the 300s timeout (shard or trim), then the CS-700 flip sequence.

## Session 122 - 2026-10-04 - tier1 and tier2 back to green, four tier2 items closed, the CS-815 nonce fold landed, and CS-400 built through S4 with a parent join

- Shipped: CS-1228, CS-1229, CS-1230, CS-1233 closed on one green tier2 run at d1775ca; a CORRECTION record for CS-1232 discharges its "POSIX untested" residual. Detail in docs/LEDGER.md. LANDED NOT CLOSED: CS-815 (the probe folded into one interpreter start with a per-run nonce; open on the operator's by-eye check of the REFUSED line), CS-1234 (status file plus the 120 per 24h start cap), CS-1231 slice C half (the inbox responder spawns through the kit; `ops/loop/run_lane.ps1` stays the named exception).
- In flight: CS-400, the Phase 4 gate. Built this session: the plan; S0 measurement (two InventoryItem forms, so try both and accept exactly one); an adjudicator (ADJ-G) ruling on 13 questions; S1 decoder; S2 reference join; S3 per-building inventory; S2b parent join plus a non-building bucket, so water pumps, miners and truck stations are no longer unattributed; S4 depth gate. A clean-clone independent byte counter matched the shipped decoder on 40 of 40 saves. Its residuals are in BACKLOG.md under Session 122 residuals.
- Decisions: the CS-815 frozen-file grant was adjudicated, then AMENDED to a per-run nonce (both records in docs/LEDGER.md under CS-815). ADJ-G's CS-400 ruling. No ADR.
- Surprises: tier1 and tier2 were both red at session start. The ubuntu provenance arms failed on inode reuse, now fixed. The windows CS-815 median was 1.297s. Another writer committed CS-959 (README, public-readiness) and CS-1235..1262 (inspiration ingest) on main during the session; the ingest reddened tests/ops/test_lane_scope.py, fixed by excluding CS-1254..1262 from the dashboard lane scope.
- Failed paths: the fixed-token probe fold - an adversary showed it accepted `printf token; exit 97`. S3's first attribution through connection components - refuted for over-reach, replaced by attribution through actor references. Four pushes were blocked before the fifth landed at d1775ca (13330 passed, 12 skipped): by the citation guard, the repr census, the nested no-install suite and the locals-rendering guard. Traps: census guards (repr population, locals binding, the REFERENCE_COUNT_COMMON_MODE closure, the 72-char commit subject) are not hit by targeted runs; the worktree isolation sandbox blocks writing shared progress files.
- Next action: read CI on the /done push, then carry CS-400 to its Phase 4 gate close.
