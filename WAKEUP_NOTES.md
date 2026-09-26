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

## Session 113 - 2026-09-25 - three orchestrated waves toward the public flip, the frozen hooks rebuilt under adjudicator grants, and tier 1 split into four shards

- Shipped: 51 items closed, every one adversaried and adjudicated before its ledger entry. N0 flip decisions CS-1180, CS-1181, CS-1182 (ADR 0018 trailer strip, CS-G03 supersession, decide/confirm/act split, CLAUDE.md 6.1 irreversible-act floor). Wave 1: CS-1019, 1021, 1022, 1023, 1024, 1026, 1027, 1028, 1029, 1030, 1031, 1034, 1035, 1036, 1037, 1014, 1015, 1016, 1017, 1178, 1160, 811, 812, 1163, 820, 1177, 1168, 1158, 956, 1179. Wave 2: CS-1018, 1184, 1185, 1189, 1190, 1191, 1193. Wave 3 and frozen wave: CS-1183, 1188, 818, 816, 817, 813, 822, 821, 824, 955, 1174. Detail in docs/LEDGER.md.
- In flight: nothing mid-edit. Open Phase 7: CS-700, 701, 704, 814, 815, 953, 1032, 1186 (no-game half gated CS-G08), 1194, 1195, 1196, 1197, 1198. CS-1187 moved to docs/GATED.md as CS-G08.
- Decisions: ADR 0023 (a filename can be personal data, withheld by reason class), ADR 0024 (credential-scan boundary is publication; CS-1168 declined), ADR 0025 (tier-3 flip checks run locally, never CI). Frozen-file grants recorded in the ledger BEFORE each edit: G-816/G-817, G-813/G-822, G-821/G-824 (CS-704 pre-push route DENIED - CI route), G-955/G-1174 plus two G-955 addenda, and the CS-824 sandbox floor-substitution clarification. CS-815 (.claude/settings.json) was GRANTED but HELD for the operator - it rewrites what runs in every Claude session.
- Surprises: adversaries refuted almost every first build, often twice; the recurring shapes were oracles blind to their subject (leak checks matching one spelling), docstrings claiming more than the code, and guards failing OPEN on an error path. Merged slices repeatedly reddened repo-wide guards their builders never ran (rendering, liveness, pointer, citation) - wave 3 made those guards mandatory per builder. CI tier 1 overran twice (565s, 509s): runner variance explained a third; the rest was real growth; fixed by CS-1193's cache plus a fourth hook shard, never by raising the pin.
- Failed paths: shortening the hook probe bound in sandbox copies to save CI time (declined - saves ~25 worker-s on Linux, where only 5 arms wait, and leaves no safe fall-through window). Rewriting pytest node IDs to redact them (broke -k, --deselect and copied FAILED ids - redact at render time instead). A time-bounded full suite under the tool's 10-minute cap (use foreground halves or thirds, or the pre-push log).
- Next action: read CI on the /done push, then decide CS-815 with the operator and start CS-704 (the CI trailer census step, tools/trailer_census.py now exists).
