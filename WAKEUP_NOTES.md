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
## Session 116 - 2026-09-26 - CI back to green, three withheld-path and timing items closed, a fifth tier-1 job, and the env scan inverted but not closed

- Shipped: CS-1209 (measured on ubuntu via a throwaway branch: PYTHONINSPECT turns sys.exit(97) into status 1, so pre-commit refuses with no usable python; the arm names one path per platform), CS-1195 (drift_guard guard (c) withholds withheld-class paths - four adversary rounds), CS-1210 (the same for guard_dated, which is guard (g) not (e)), CS-1201 (probe-bound arms graded by a per-call shim log and a window from the hang; base went red under a 24-spinner load, candidate green), CS-1198 (fifth tier-1 job `fill` plus `--no-loadscope-reorder` on the hook job; slow-mode hook reading 355). Detail in docs/LEDGER.md.
- In flight: CS-1207 LANDED NOT CLOSED at db87fff - the env scan is an allowlist of permitted readers per site, but adversary round three still got synthetic markers out live through str.format field walks, __import__/exec bound as values, match class patterns and reaching os through a scanned repo module (listed in its item note). CS-1208 has a spec (session scratchpad, not tracked - the next session re-plans from the item note) and depends on CS-1207's permitted-site table; the merger ruled its driven module runs in the fill shard.
- Decisions: CS-1198 by adjudicator (Route N, then re-ruled after S0's NO-GO): fifth job fill, reorder flag on the hook job only, pytest-xdist>=3.8. CS-1207 by adjudicator: the Python-scope command rule is a program allowlist; resolve/absolute/sys.executable/sys.path graded per site; the pathlib method list is a pinned literal with a guard test; six must-pass lines retired to must-flag (ledger). No ADR.
- Surprises: pytest-xdist 3.8 dispatches loadfile work by descending test count, so a file NAMED first does not START first - the hook shard's 160s canary always ran last and alone (CS-1213 files the save shard's identical false claim). tests/test_flip_checks.py pins that no workflow names its tool, so it cannot be moved into a named shard - the first CS-1198 push blocked on it. The guard shard read 443 on a slow runner (CS-1214). The gate echoes git's stderr, home path included, when run by hand (CS-1215, frozen).
- Failed paths: a fifth job alone for CS-1198 (S0 projected hook 402-413, NO-GO). A static scanner reaching closure on Python env reads in one round - three rounds each found a new class; the next builder should close CLASSES (str.format fields, any builtin bound as a value, any attribute chain through a repository module) not shapes.
- Next action: read CI at the /done push; then continue CS-1207 from its item note's round-three list, closing each CLASS with an allowlist, and send the result to a fresh adversary before CS-1208.

## Session 115 - 2026-09-25 - the companion launches again, CS-815 landed pending one look, and CS-814 closed after five adversary rounds

- Shipped: CS-1203 (per-identity world memo in clockspeed/surface/providers.py; the operator's "the app doesnt launch" - health took 2.5s against a 2.0s probe; end-to-end launch opened the window in 7s), CS-814 (CLAUDE.md non-negotiable 13; tests/test_hook_env_echo.py), CS-1200 (137 accepted by the probe self-check; tests/test_probe_refusal_output.py), and a CS-1199 repair (the plant sat in saferepr's elided middle on ubuntu). Detail in docs/LEDGER.md.
- In flight: CS-815 LANDED at fd3c167 but STAYS OPEN on one check only the operator can make - does the desktop app visibly show a "REFUSED (CS-815)" hook-error line? The transcript records it as a hook_non_blocking_error attachment; computer use cannot capture Claude's own window. Filed and open: CS-1201, CS-1202, CS-1204 to CS-1208.
- Decisions: CS-814's rule lives ONLY in CLAUDE.md rule 13 (no hook-header pointers). One frozen re-pin served CS-814 and CS-1200 together. CS-814 closed on the adjudicated bar with obfuscation, non-Python env= children, the tests tree and PYTEST_ADDOPTS declared residual.
- Surprises: a settings.local.json env key reaches the live session on reload but deleting it does NOT unset it - the gate failed open for three calls until the key was set empty. The pre-push suite counts real-save copies, so running the dashboard during a push blocks it. The verifier's module list missed tests/test_liveness.py, which refused the first CS-814 push.
- Failed paths: a blocklist env scan (refuted three times) - replaced by an allowlist; a save-shard home for the CS-815 tests (no room) - moved to the guard shard.
- Next action: read CI at the /done push; ask nothing, but record the operator's answer on the CS-815 hook-error line if they give one; then CS-1195.

## Session 114 - 2026-09-25 - the trailer gate moved to CI, environment values left every assert rendering, and CS-815 was built but not landed

- Shipped: CS-704 (CI trailer census step in the tier-1 save job, tests/test_trailer_routes.py) and CS-1199 (filed and closed: the assert-rendering guard for process-environment values, tests/test_assertion_rendering.py). Detail in docs/LEDGER.md. The 33 owed inbox asks were answered in two outbox notes (moon_sync_outbox/2026-09-25-1409 and -1410); the inbox is still NOT acknowledged.
- In flight: CS-815 - the operator said "go CS-815" in their own words this session. Built in worktree .claude/worktrees/agent-a4f0885163222ba12, branch worktree-agent-a4f0885163222ba12, commits ecb7b53 (the wrapper script and its test module, the two settings.json command strings, save-shard routing, provenance rows) and 8186634 (resolve sh from any launching shell, write-list widened by the merger to tests/test_pretooluse_gate.py). NOT adversaried, NOT landed. The builder was stopped at /done mid full suite; its PowerShell-launched failure classification (23 failures incl. test_pre_push_ref_race, test_precommit_index_race) was never reported.
- Decisions: none new at ADR level. Merger ruling: CS-1199's unresolved-call default treats a lower-case callable given env= as RUNNING under it, not returning it (without it: 2107 findings on 1039 lines); an adversary found no live counter-example. Merger ruling: a suite that goes red by which shell launched pytest is a defect, not an operating rule.
- Surprises: every first build was refuted again - CS-704 on an untested exit-2 path, CS-1199 twice on LIVE leaks (imported tests/git_env.py helpers; a HookLayout parameter). `assert "X" not in os.environ` renders the WHOLE environment, measured. The inbox answer agent's five extraction subagents never returned to it.
- Failed paths: none abandoned.
- Next action: read CI on the /done push, then take CS-815 to the adversary pass at 8186634 and land it with the condition-6 live check.
