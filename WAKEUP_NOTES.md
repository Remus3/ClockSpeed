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
## Session 125 - 2026-10-04 - CS-500 closed with the Phase 5 advisor gate, the advice reads live, the pre-S7a batch refuted and repaired, and the citation gate made to survive the rewrite

- Shipped: CS-500 (S5 every-rule-fires with its tier-3 arm repaired after an adversary left M7/M8 surviving; S6 advise() wiring plus the reload half of A3; verifier CONFIRMED all five clauses; adversary S6 21/22 killed, residual a discarded clock read with no behaviour), CS-1216 (verifier CONFIRMED 3/3, size and SHA match the pin), CS-1267 (flip_checks clones with --no-hardlinks; the leak arm matches the home path in every spelling after an as_posix survivor), CS-1270 (GET /api/advice and its derivation answer 200 through advise_world/inputs_of and StoreAdviceSource; import clause amended so the pre-existing api/map.py audit import is pinned). Detail in docs/LEDGER.md. PROGRESS records: CS-704 (accept-set test REFUTED - a short or upper-case third member passed - repaired to token-set equality), CS-701 (identity check REFUTED - replace refs and a shallow cut bypassed it, 4 mutants survived - repaired in tools/flip_checks.py and tools/trailer_census.py with GIT_NO_REPLACE_OBJECTS, a cut-history refusal and multi-commit tests), CS-700 (citation gate design (d): tools/sha_citation_historical.json, 377 tokens, witnessed PRE c6f3687 / POST b7b4a2c4b71c942bb759aa2b4f3b9ba906ddc1ec; adversary REFUTED POST laundering and witness tamper, repaired by a HISTORICAL_SHA256 digest pin plus witness compare; --flip-readiness READY on main), CS-1186 (walk 1 PASS every step, README fixed for 9 defects), CS-959 (legacy .github/ISSUE_TEMPLATE.md added for the profile's null issue_template row). Filed CS-1268, CS-1269. Slots C4 channel reply delivered 6/6 hash-matched.
- In flight: the CS-700 flip. The S7a script adversary HELD (two runs reproduce the 389fe4a tip and c6f3687 -> b7b4a2c4b71c942bb759aa2b4f3b9ba906ddc1ec). Branch protection probed AVAILABLE on the private repo (404 not protected, rulesets 200 []), so S11 stays at S11. CS-G03 adjudicated: the CS-1186 walk may be done by a context-free agent, CS-1187 is NOT waivable post-flip, and the flip waits for a CS-G08 environment. Windows Sandbox was Disabled with firmware virtualization on; the operator is rebooting to enable it and a Linux VM. CS-1186 still owes a clean repeat walk by a different agent and the no-game clause in that environment; CS-959 closes only when the profile row reads non-null after push (PVR endpoint 404, enable post-flip).
- Decisions: CS-700 citation gate design (d) with digest and witness pins (residual: a hand edit of the pin line launders, visible as a gate change). The S7a identity-oracle residual adjudicated ACCEPT and confirmed in the operator's own words. CS-1187 not waivable post-flip. Legacy ISSUE_TEMPLATE.md for the profile row. CS-1270 import clause amended. No ADR.
- Surprises: the planner found the S7a rewrite changes about 332 cited SHAs, so the citation gate would have gone red on the published tree - a new CS-700 blocker. GitHub's community profile counts only the legacy single-file issue template. Closing a gate or blocker item reddens arms that cite it: surface OPEN_BLOCKERS, headless-queue FENCE 1 and the lane scope partition.
- Failed paths: two pushes BLOCKED by pre-push - the closed CS-500 still cited by surface OPEN_BLOCKERS, then the lane gate fence and CS-1269 scope - fixed; the third push 8792278 passed (14296 passed, 12 skipped), tier1 37242415726 SUCCESS. S7a's clone must be --no-local; --no-hardlinks aborts filter-repo.
- Next action: after the reboot, verify Windows Sandbox is Enabled and launches, then run the CS-1187 never-seen walk and the CS-1186 clean repeat plus no-game clause in it by a different context-free agent.

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
