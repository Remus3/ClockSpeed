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
## Session 122 - 2026-10-04 - tier1 and tier2 back to green, four tier2 items closed, the CS-815 nonce fold landed, and CS-400 built through S4 with a parent join

- Shipped: CS-1228, CS-1229, CS-1230, CS-1233 closed on one green tier2 run at d1775ca; a CORRECTION record for CS-1232 discharges its "POSIX untested" residual. Detail in docs/LEDGER.md. LANDED NOT CLOSED: CS-815 (the probe folded into one interpreter start with a per-run nonce; open on the operator's by-eye check of the REFUSED line), CS-1234 (status file plus the 120 per 24h start cap), CS-1231 slice C half (the inbox responder spawns through the kit; `ops/loop/run_lane.ps1` stays the named exception).
- In flight: CS-400, the Phase 4 gate. Built this session: the plan; S0 measurement (two InventoryItem forms, so try both and accept exactly one); an adjudicator (ADJ-G) ruling on 13 questions; S1 decoder; S2 reference join; S3 per-building inventory; S2b parent join plus a non-building bucket, so water pumps, miners and truck stations are no longer unattributed; S4 depth gate. A clean-clone independent byte counter matched the shipped decoder on 40 of 40 saves. Its residuals are in BACKLOG.md under Session 122 residuals.
- Decisions: the CS-815 frozen-file grant was adjudicated, then AMENDED to a per-run nonce (both records in docs/LEDGER.md under CS-815). ADJ-G's CS-400 ruling. No ADR.
- Surprises: tier1 and tier2 were both red at session start. The ubuntu provenance arms failed on inode reuse, now fixed. The windows CS-815 median was 1.297s. Another writer committed CS-959 (README, public-readiness) and CS-1235..1262 (inspiration ingest) on main during the session; the ingest reddened tests/ops/test_lane_scope.py, fixed by excluding CS-1254..1262 from the dashboard lane scope.
- Failed paths: the fixed-token probe fold - an adversary showed it accepted `printf token; exit 97`. S3's first attribution through connection components - refuted for over-reach, replaced by attribution through actor references. Four pushes were blocked before the fifth landed at d1775ca (13330 passed, 12 skipped): by the citation guard, the repr census, the nested no-install suite and the locals-rendering guard. Traps: census guards (repr population, locals binding, the REFERENCE_COUNT_COMMON_MODE closure, the 72-char commit subject) are not hit by targeted runs; the worktree isolation sandbox blocks writing shared progress files.
- Next action: read CI on the /done push, then carry CS-400 to its Phase 4 gate close.

## Session 121 - 2026-10-03 - FLEET-KIT v4 vendored under a cleared licence gate, the bundle provenance check rebuilt on file identity, the tier2 latency red diagnosed, and the operator turned the project back to product

- Shipped: CS-1232 (a MAIN kit bundle file is verified at its bundle-relative path, placed by file identity against a census of the inbox; eight builder rounds, seven adversary refutations repaired; the merger stopped on cost against risk with residuals recorded). Detail in docs/LEDGER.md. LANDED NOT CLOSED: CS-1231 slices A and B at FLEET-KIT v4 in one commit after a gate entry recorded CLEARED before the lift; CS-1233 (the CS-815 latency arm times only after its xdist siblings go quiet). Filed CS-1233, CS-1234.
- In flight: CS-1234 (inbox_status.json writer plus the 120-per-24h start cap) is a WIP commit on its own worktree branch (find it: `git log --all --oneline --grep "CS-1234 - WIP"`), suite NOT green (failures and a hang the builder had not named when stopped). CS-1231 slice C (route the responder and run_lane.ps1 through the kit spawn, floors_in_hooks=True) and the v4 ANSWER to MAIN are not started.
- Decisions: CLAUDE.md is NOT condensed - the condensation moved binding rules into a non-binding history file and was dropped; each Settled entry gained a Reversed-by clause satisfied only by the operator's own words. Operator directive filed as a Settled entry: product before process. No ADR.
- Surprises: tier1 never runs on windows, so the CS-815 latency arm was only ever exercised on windows by tier2, where it failed three legs running. The provenance check fell to a new path SPELLING five rounds in a row until placement moved to file identity. Last two weeks: 8 of 371 commits touched product code.
- Failed paths: comparing note path spellings for placement (8.3, trailing dot, junction, extended-length and admin-share spellings each bypassed it). Condensing CLAUDE.md to fit the FLEET block - unnecessary, the full text plus the block is under budget.
- Next action: read the push and tier2 results; then start CS-400 (the Phase 4 gate), not a tooling item.

## Session 120 - 2026-10-03 - three provenance and citation items closed, the tier2 nightly repaired and sharded, FLEET-KIT v3 built but held at the licence gate

- Shipped: CS-1227 (`tools/main_provenance.py` `verify_main_note`; MAIN's root from gitignored local config only; committed-blob compare with `--no-replace-objects`; three adversary rounds plus a CRLF fail-closed ruling), CS-1223 (seed escape pinned by whole-row digest; local clean needs a re-derived freeze witness; ci_run pinned to this repo, one run one full commit; five rounds), CS-1224 (sha gate reads code files, judges every 5-6 run, strict BOM decode plus byte view, not-read is exit 2; five rounds). Detail in docs/LEDGER.md. LANDED NOT CLOSED: CS-1228 (tier2 full history, loadfile, freeze_witness auto-maintenance race), CS-1229 (tier2 sharded by tier1's partition per OS; adversary NOT REFUTED), CS-1230 (cross-drive relpath fallback as an allowlist; two rounds). Each closes only on a green tier2 run at the landed tip.
- In flight: CS-1231 FLEET-KIT v3 - slice A (vendor + guard exemptions) and slice B (condensed CLAUDE.md with block, /done) each on its own worktree branch - find both with `git log --all --oneline --grep CS-1231`. Both UNMERGED, held: an adjudicator ruled the THIRD_PARTY gate must run before the lift, and MAIN's kit commit carries no licence. Only slice B's /done command change landed. Reply delivered to MAIN asking for a v4 with a licence and naming three kit gaps. The responder stays paused (INBOX_STOP).
- Decisions: CS-1227 CRLF refusal accepted fail-closed (adjudicator ruling A). FLEET-KIT licence: adjudicator ruling B-then-C - MAIN's git objects read once for licence evidence (none found), so hold. No ADR.
- Surprises: the tier2 nightly had been red since 2026-09-24 unnoticed - shallow checkout plus windows timeouts; once windows finished, it exposed a cross-drive relpath bug. A loaded box failed a hook-timing test and blocked one push.
- Failed paths: raising the tier2 timeout to 50 (windows probe still cut at 99 percent) - sharding is the repair. A working-tree compare for MAIN provenance (bypassed four ways).
- Next action: dispatch a tier2 run on the pushed tip and read every shard; close CS-1228, CS-1229, CS-1230 on green.
