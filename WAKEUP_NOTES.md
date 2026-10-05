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

## Session 125 - 2026-10-04 - CS-500 closed with the Phase 5 advisor gate, the advice reads live, the pre-S7a batch refuted and repaired, and the citation gate made to survive the rewrite

- Shipped: CS-500 (S5 every-rule-fires with its tier-3 arm repaired after an adversary left M7/M8 surviving; S6 advise() wiring plus the reload half of A3; verifier CONFIRMED all five clauses; adversary S6 21/22 killed, residual a discarded clock read with no behaviour), CS-1216 (verifier CONFIRMED 3/3, size and SHA match the pin), CS-1267 (flip_checks clones with --no-hardlinks; the leak arm matches the home path in every spelling after an as_posix survivor), CS-1270 (GET /api/advice and its derivation answer 200 through advise_world/inputs_of and StoreAdviceSource; import clause amended so the pre-existing api/map.py audit import is pinned). Detail in docs/LEDGER.md. PROGRESS records: CS-704 (accept-set test REFUTED - a short or upper-case third member passed - repaired to token-set equality), CS-701 (identity check REFUTED - replace refs and a shallow cut bypassed it, 4 mutants survived - repaired in tools/flip_checks.py and tools/trailer_census.py with GIT_NO_REPLACE_OBJECTS, a cut-history refusal and multi-commit tests), CS-700 (citation gate design (d): tools/sha_citation_historical.json, 377 tokens, witnessed PRE c6f3687 / POST b7b4a2c4b71c942bb759aa2b4f3b9ba906ddc1ec; adversary REFUTED POST laundering and witness tamper, repaired by a HISTORICAL_SHA256 digest pin plus witness compare; --flip-readiness READY on main), CS-1186 (walk 1 PASS every step, README fixed for 9 defects), CS-959 (legacy .github/ISSUE_TEMPLATE.md added for the profile's null issue_template row). Filed CS-1268, CS-1269. Slots C4 channel reply delivered 6/6 hash-matched.
- In flight: the CS-700 flip. The S7a script adversary HELD (two runs reproduce the 389fe4a tip and c6f3687 -> b7b4a2c4b71c942bb759aa2b4f3b9ba906ddc1ec). Branch protection probed AVAILABLE on the private repo (404 not protected, rulesets 200 []), so S11 stays at S11. CS-G03 adjudicated: the CS-1186 walk may be done by a context-free agent, CS-1187 is NOT waivable post-flip, and the flip waits for a CS-G08 environment. Windows Sandbox was Disabled with firmware virtualization on; the operator is rebooting to enable it and a Linux VM. CS-1186 still owes a clean repeat walk by a different agent and the no-game clause in that environment; CS-959 closes only when the profile row reads non-null after push (PVR endpoint 404, enable post-flip).
- Decisions: CS-700 citation gate design (d) with digest and witness pins (residual: a hand edit of the pin line launders, visible as a gate change). The S7a identity-oracle residual adjudicated ACCEPT and confirmed in the operator's own words. CS-1187 not waivable post-flip. Legacy ISSUE_TEMPLATE.md for the profile row. CS-1270 import clause amended. No ADR.
- Surprises: the planner found the S7a rewrite changes about 332 cited SHAs, so the citation gate would have gone red on the published tree - a new CS-700 blocker. GitHub's community profile counts only the legacy single-file issue template. Closing a gate or blocker item reddens arms that cite it: surface OPEN_BLOCKERS, headless-queue FENCE 1 and the lane scope partition.
- Failed paths: two pushes BLOCKED by pre-push - the closed CS-500 still cited by surface OPEN_BLOCKERS, then the lane gate fence and CS-1269 scope - fixed; the third push 8792278 passed (14296 passed, 12 skipped), tier1 37242415726 SUCCESS. S7a's clone must be --no-local; --no-hardlinks aborts filter-repo.
- Next action: after the reboot, verify Windows Sandbox is Enabled and launches, then run the CS-1187 never-seen walk and the CS-1186 clean repeat plus no-game clause in it by a different context-free agent.
