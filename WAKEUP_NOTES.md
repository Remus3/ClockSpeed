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
## Session 158 - 2026-11-16 - the lane's two landings graded LAND, six product items closed through planner, adjudicator, builder, adversary and adjudicator, CS-1362 gated

- Shipped: CS-1247 and CS-1253 (the lane's two cycle landings, each graded by an adversary that did not refute it and a distinct adjudicator ruling LAND), CS-1400, CS-1394, CS-1395, CS-1360, CS-1390 and CS-484 closed; CS-1362 gated as CS-G11 on an operator ADR for a dev-only Node tool. Detail in docs/LEDGER.md.
- In flight: nothing dirty. The lane driver exited after its 2 of 2 cycles and no lane runs. CS-1401 (wire interleave_domains into the served list) is the next product action. CS-1366's earliest closing read is 2026-11-19 18:48:37 local. CS-1334 still waits on host RAM. CS-1295, CS-1231 and CS-1358 carried unworked.
- Decisions: no ADR. Two adjudicator rulings, each with its fence in the hand-off's SESSION 158 block: transport rates read from each class's own shipped description with an exact ratio check and no authored constant, proportional plan edges, CS-1390's line written by the inbox responder's tick; and CS-1360's bottleneck as the edge of greatest utilisation of the fastest known carrier of its unit, computed in solve and recorded in the trace, the surface transcribing only.
- Surprises: CS-1394's first build published 0 of 4 pipe rates live, because the shipped text separates its numbers with U+202F and U+00A0 while the fixture used ASCII spaces; the repair reads 16 of 16. CS-1360's first wave-2 build computed carriers and saturation inside surface, a seam breach the adjudicator re-routed into solve. A pre-push with the global python still fails on the conftest redactor (CS-1387), and one push was blocked by the provenance census on new test files. Each pre-push that ran to its end took 18 to 20 minutes at 19.5k to 19.7k tests. No spike contradicted BOOTSTRAP.md.
- Failed paths: a named one-half constant for belt rates (no sanctioned source; the docs state the rate); a highest-rate star as the flow view's mark (it identifies no limit); synthetic docs fixtures written with ASCII spaces; a builder's new files with no provenance row.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then build CS-1401 through planner, adjudicator, builder, adversary and adjudicator.

## Session 157 - 2026-11-15 - ten product items closed, each through planner, adjudicator, builder, adversary and adjudicator; kit v31 adopted; a lane's false close reopened and re-closed

- Shipped: CS-1384, CS-1381, CS-1378, CS-1373, CS-1376, CS-1374, CS-1397, CS-1246, CS-1375 and CS-1396 closed; kit v31 adopted, given CS-1399 at this /done. CS-1366's 22 rows classified, the item left open. Detail in docs/LEDGER.md.
- In flight: nothing dirty. A detached advisor-ranking lane driver is live at this /done (2 cycles, CS-1247 claimed first, about 4 h a cycle) and pushes straight to origin/main; the next session grades its landings after the fact. CS-1400 filed from the UI-157 browser audit of the advice panel, BLOCKED on 5 majors. CS-1360 stays open on CS-1394, CS-1395 and two adversary gaps. CS-1366's earliest closing read is 2026-11-19 18:48:37 local. CS-1334 still waits on host RAM.
- Decisions: no ADR. Seven decisions, each with its fence, in the hand-off's SESSION 157 block: an argued ceiling raise for a renamed target, a false LEDGER close corrected only by a later record, the act route's one-POST-one-act design, CS-1366's row rules, no correction note to MAIN, no default schematic source on the registry route, and no clause built before its gaps are adjudicated.
- Surprises: CS-1374's first build was inert in production until a read-only install probe found the object-reference wrapper. The lane closed CS-1246 on an aging guard that never fired in production. Two builders' narrower test runs missed a whole-directory red. Builder worktrees were cut at a stale base. One pre-push was blocked by memory pressure under load, another by the published-SHA citation gate. No spike contradicted BOOTSTRAP.md.
- Failed paths: citing a candidate by its slice SHA in landing text, which the citation gate refuses; cite candidates by role. Trusting a lane's own close record without grading it.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then the lane driver's exit and an adversary on CS-1247's landing.

## Session 156 - 2026-11-13 - the red baseline repaired, kit v30 adopted, and CS-1361, CS-1379 and CS-1382 landed after an account-limit recovery

- Shipped: CS-1383 (re-pin to the patched game build), CS-1389 (kit v30), CS-1385 (CI ubuntu jobs pinned to 24.04), CS-1361 (the companion window saved by display id), CS-1379 (quoted display-name targets in tiers 1 and 2), CS-1382 (raw supply only with a held extractor, a factual cap clause) closed; a CS-484 decision record; CS-1366's three exit-1 runs classified. Three notes to MAIN, each 1 of 1. Detail in docs/LEDGER.md.
- In flight: nothing dirty. CS-1366 stays open: 21 gated exit-nonzero rows after 2026-11-04 are unclassified (its phase7.md section). CS-1384 filed: the fuel cards splice names unquoted, and its fallback ruling goes through an adjudicator before build. CS-1334 waits on host RAM, 22.4 of 31.6 GB free at this /done. CS-1295 stays open on its PARTIAL answer. The one lane cycle MAIN's 2024 ORDER released ran (CS-1361); further cycles follow this tree's lane policy, CS-1360 next.
- Decisions: no ADR. CI pinned to ubuntu-24.04 with 39 duration rows relabelled; pushes run with CLOCKSPEED_PYTHON on the .venv interpreter, the global python left above the pins; CS-1382's cap clause states facts only; the owed library re-read does not block CS-1382 (CS-1388). Each in docs/LEDGER.md or the hand-off.
- Surprises: a game patch moved the build and reddened guard (h), blocking every push from 2026-11-08 to 2026-11-12. An installed ruff 0.17.3 against a declared range below 0.16 cost the precommit gate its file naming and raised 31 findings. The global python carries pytest 9.2.0 and mypy 2.4.1, which redden the pre-push canary and crash the conftest redactor (CS-1387). Every CI red from 2026-11-12 ran on ubuntu-26.04. The earlier attempt at this session on the second account stopped on its weekly limit mid-build. No spike contradicted BOOTSTRAP.md.
- Failed paths: for CS-1382's cap, the route-stage test (refuted by world K), causal wording on any trim (refuted by a 13-recipe world) and an uncapped counterfactual re-run (it defeats the cap). A precommit parser for both ruff output shapes was denied: one branch could not be exercised.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then classify CS-1366's 21 rows and rule CS-1384's fallback.
