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
## Session 156 - 2026-11-13 - the red baseline repaired, kit v30 adopted, and CS-1361, CS-1379 and CS-1382 landed after an account-limit recovery

- Shipped: CS-1383 (re-pin to the patched game build), CS-1389 (kit v30), CS-1385 (CI ubuntu jobs pinned to 24.04), CS-1361 (the companion window saved by display id), CS-1379 (quoted display-name targets in tiers 1 and 2), CS-1382 (raw supply only with a held extractor, a factual cap clause) closed; a CS-484 decision record; CS-1366's three exit-1 runs classified. Three notes to MAIN, each 1 of 1. Detail in docs/LEDGER.md.
- In flight: nothing dirty. CS-1366 stays open: 21 gated exit-nonzero rows after 2026-11-04 are unclassified (its phase7.md section). CS-1384 filed: the fuel cards splice names unquoted, and its fallback ruling goes through an adjudicator before build. CS-1334 waits on host RAM, 22.4 of 31.6 GB free at this /done. CS-1295 stays open on its PARTIAL answer. The one lane cycle MAIN's 2024 ORDER released ran (CS-1361); further cycles follow this tree's lane policy, CS-1360 next.
- Decisions: no ADR. CI pinned to ubuntu-24.04 with 39 duration rows relabelled; pushes run with CLOCKSPEED_PYTHON on the .venv interpreter, the global python left above the pins; CS-1382's cap clause states facts only; the owed library re-read does not block CS-1382 (CS-1388). Each in docs/LEDGER.md or the hand-off.
- Surprises: a game patch moved the build and reddened guard (h), blocking every push from 2026-11-08 to 2026-11-12. An installed ruff 0.17.3 against a declared range below 0.16 cost the precommit gate its file naming and raised 31 findings. The global python carries pytest 9.2.0 and mypy 2.4.1, which redden the pre-push canary and crash the conftest redactor (CS-1387). Every CI red from 2026-11-12 ran on ubuntu-26.04. The earlier attempt at this session on the second account stopped on its weekly limit mid-build. No spike contradicted BOOTSTRAP.md.
- Failed paths: for CS-1382's cap, the route-stage test (refuted by world K), causal wording on any trim (refuted by a 13-recipe world) and an uncapped counterfactual re-run (it defeats the cap). A precommit parser for both ruff output shapes was denied: one branch could not be exercised.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then classify CS-1366's 21 rows and rule CS-1384's fallback.

## Session 155 - 2026-11-04 - a stated target reaches plan.adopt on a real world; eight items closed, and the operator's /done stopped CS-1379 and CS-1382 built and unlanded

- Shipped: CS-1350, CS-1351, CS-1370, CS-1359, CS-1344, CS-1372, CS-1371, CS-1380 closed; the bound.py byproduct docstring corrected; two decision records, CS-1344 clause 2 and CS-1295's nine findings; two notes to MAIN, 1 of 1 each. Detail in docs/LEDGER.md.
- In flight: CS-1379 and CS-1382 are built on one kept local worktree branch, each with an adversary's refutation unrepaired, unlanded: `git log --all --grep=CS-1382` finds it, and each item's section in docs/item_notes/phase5.md says what is owed. CS-1334 waits on host RAM, 21.7 of 31.6 GB free at this /done against its 24 GB gate. CS-1295 stays open with its result ANSWER owed to MAIN. The lanes stay held by MAIN's 1535 and 2006 ORDERS, though the machine quiesce reads lifted with no MAIN note saying so.
- Decisions: no ADR. The rulings are in docs/LEDGER.md and the item sections. CS-1380 landed on its adversary pass and a verifier that stopped at its budget, with no adjudicator on the built item, because the operator's /done came first.
- Surprises: a parent agent's completion notice waits on its live children, and one straggling adversary hid a finished report for 8.5 hours. A read-back in a sent note read a path no run claims, so the note went out wrong and a correction followed. The carried hand-off called nine CS-1295 findings operator-needing, and a reader and an adjudicator found none is. The hand-off's CS-1359 evidence run was a workflow_dispatch, not nightly. No spike contradicted BOOTSTRAP.md.
- Failed paths: CS-1379's ClassName fallback for undelimited names was refuted in the opposite direction, since `A, B` then reads its ClassName; the next attempt rules on quoting the name. CS-1382's ruled (1, 0) raw-supply count was reversed by its own real-world clause: 7 early-world targets went false route-refused.
- Next action: read the remote ref against this HEAD by full SHA, CI for that SHA and this ritual's timing record; then rule CS-1379's naming, land it, and repair CS-1382's F1.

## Session 154 - 2026-11-01 - MAIN's closeout drive before the operator's reboot: both Fleet Insights ORDERS landed, no product slice

- Shipped: CS-1367, CS-1368, CS-1369 closed; scope product-slices committed, launch held. Detail in docs/LEDGER.md.
- In flight: CS-1366 stays open for its 7-day read on or after 2026-11-08. The push, CI, the ONE ANSWER and the acks follow this write: ops/loop/control/progress/closeout-cs.json owns them.
- Decisions: the 2026-10-26 tree_population worktree disposed unlanded by an adjudicator, branch kept for CS-1358. No ADR.
- Surprises: an adversary found a repin tool that silently re-pointed a reason to a swapped handler, and a kill arm whose planted hang ended inside the budget's scaled window; both fixed with tests. A pass that timed out left its commits safe on its branch. No spike contradicted BOOTSTRAP.md.
- Failed paths: gitlock refuses `git cherry-pick`; land with `cherry-pick -n`, then gitlock `git commit -C`.
- Next action: read the drive's progress file, then the remote ref against HEAD by full SHA and CI for that SHA.
