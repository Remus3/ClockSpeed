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
## Session 91 - 2026-09-13 - three disjoint tracks merged, and every one of them was refuted before it was right

- Shipped: CS-1008, CS-1011, CS-1013 CLOSED. CS-962 ADVANCED, NOT CLOSED - it stays open on
  one clause, that the page state which panels are registry-derived and name what it cannot
  show. Detail in docs/LEDGER.md.
- In flight: nothing. Tree clean at the release tip, all three worktrees merged and their
  branches still present for reference.
- Decisions: no ADR. BOOTSTRAP.md section 7.1 gained `/api/power` under the word "minimum",
  the third arrival in the shape CS-912 set and CS-977 followed - adjudicated legitimate and
  proven load-bearing rather than decorative.
- Surprises: nothing contradicted BOOTSTRAP.md. Three measurement traps did fire, and all
  three are the reason this session's arms look as they do. A privacy arm's ORACLE WAS BLIND
  because `{holder!r}` doubles backslashes, so it reported clean on a row carrying an account
  name. A scoped suite reported green over a population that EXCLUDED the six new untracked
  files, because every `git ls-files` guard was blind to them - `git add -N` must precede the
  measurement. And the lane diagnosis's own nominated evidence was refuted: `duration_s` is
  the driver-cycle clock while the 2.0s liveness grace is a `proc.wait` timeout, so the two
  cannot be compared, and eleven of the twelve pooled rows were from the WRONG NIGHT.
- Failed paths: do not rebuild the lane duration argument - it is recorded under a REFUTED
  heading in the diagnosis with all three of its faults. Do not re-pitch skipping the whole
  suite in favour of a scoped one for a merge claim; the collision arm that blocked slice A
  lives in `tests/` and `tests/surface` could never have seen it.
- Next action: pick up CS-1025 and CS-1020, both tier 1 and both cheap - a defeatable
  anti-vacuity needle and an ungraded counter line, each with a stated mutant that must die.

## Session 90 - 2026-09-13 - the claim store measured against the way a worker actually calls it, and three release designs refuted before one held

- Shipped: CS-1009 and CS-1009's blocked dependent CS-991. Detail in docs/LEDGER.md, not here.
- In flight: nothing. The tree is clean and the merge is one commit.
- Decisions: no ADR. One adjudicated ruling, recorded inside the CS-1009 ledger entry: a lane lock
  that reads RUNNING anchors its claim whether or not its holder can be proven, because
  `lanes.holder_is_a_stranger` already ruled that trade one layer down and a row is a smaller unit
  than a lane.
- Surprises: nothing contradicted BOOTSTRAP.md, so no update is owed. What did surprise: a sha256
  receipt over a record's own bytes is not a credential, because every lane can read every claim
  file - and the worker prompt's only documented recovery path WAS the attack.
- Failed paths: authenticating a release with a caller-supplied run id (run ids are policed nowhere);
  authenticating it with a receipt (forgeable by any reader); and requiring a lock to prove its holder
  before anchoring a claim (inverts the item wherever a start time cannot be read, handing a live
  cycle's row to the other lane). None is to be retried.
- Watch: CI is GREEN on main, but tier 1's duration gate is marginal - 470s and 493s on one
  tree against a 480s ceiling, 360s in session 89. Filed as CS-1012 and UNATTRIBUTED: the
  whole suite on this box is flat across the same delta, so the cost is runner-side. The
  next commit of any size can flip that gate red on arrival. Do not raise the ceiling.
- Next action: CS-1008 - `tests/test_queue_loop.py`'s `_drive` injects neither the permit seam nor the
  claim-states seam, so those arms read the LIVE store and flip non-deterministically against a real
  lane. It is tier 1 and it is the last thing reading live state in a suite.

## Session 89 - 2026-09-13 - the dashboard lane's five prerequisites, and five new instances of the class they were built to avoid

- Shipped: CS-1000, CS-992, CS-994, CS-1005 CLOSED. CS-988's sweep landed as a measurement and the
  item STAYS OPEN. CS-991 and CS-993 merged but STAY OPEN, each blocked on a residual its own slice
  disclosed. Detail in `docs/LEDGER.md`, not here.
- In flight: nothing. Tree clean. Eleven worktrees remain and are prunable except
  `C:/cs-worktrees/cs-lane-queue`, which is live lane infrastructure.
- Decisions: no ADR. **The operator granted the frozen-file exception on `.githooks/pre-push` and an
  adjudicator ruled DENY on the EDIT, so the grant is recorded GRANTED AND UNSPENT** - the CS-972
  shape on the same file. Two grounds: no wait ceiling is both useful and non-hanging, and the only
  working mechanics move a tier-0 gate's exit-code fidelity into a non-frozen module.
- Surprises, and it is the session's substance. **FIVE new instances of the CS-988 class were found,
  every one of them inside a repair built to catch that class**, and one landed in a slice whose
  brief forbade a floor BY NAME. The class is not caught by knowing about it. What caught all five
  was measurement: narrow the knob, run the suite, watch it stay green.
- Surprises, second: **two independent slices rooted worker-side state at the importing file**, so
  each lane's worker read its own private store and the two lanes were structurally blind to each
  other. One shipped a claim store where both lanes granted the same row. `lanes.REPO_ROOT` already
  resolved the indirection and neither used it. The driver-side / worker-side asymmetry is now
  recorded in the modules themselves.
- Surprises, third: **an arm written to prove exclusion hardcoded the defect away** by passing the
  very root the production path derives. Every arm was green, every mutation killed its target, and
  the feature was inert in production.
- Failed paths: the frozen-file edit (denied, grounds recorded); `PYTEST_ADDOPTS` injection to reach
  the hook's pytest (fails open and silent); holding the suite ration across the whole worker cycle
  (45:1 against the window it protects, and it would undo CS-992).
- Next action: CS-1009. Establish whether a claim survives the exit of the process that made it.

---
