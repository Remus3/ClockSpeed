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
## Session 93 - 2026-09-13 - four items closed, a fifth given an id at closure, and the pre-push gate was right both times it refused

- Shipped: CS-1038, CS-1040, CS-1044 and CS-1049 CLOSED. The lane-start repair closed with NO
  id and was allocated CS-1050 at closure, so it has exactly one owner file. Detail in
  `docs/LEDGER.md`, not here.
- NOTE ON THE SESSION NUMBER, because it is a genuine conflict and was not resolved by
  picking: the operator named this session 85 in the closing brief. `WAKEUP_NOTES.md`'s own
  sequence ran 90, 91, 92, and `docs/history_notes.md` already holds a Session 85 dated
  2026-09-11. Writing 85 would have put two different sessions under one number, so this
  entry takes the successor of the file's own sequence and the conflict is recorded here
  rather than silently decided.
- In flight: nothing. Tree clean at `0ade931`, everything pushed.
- Decisions: ADR 0019 was adjudicated this session and is already committed - read it there,
  it is not restated here. Two rulings ride with it. FIRST, the map underlay: the map ships
  as a schematic ground plane with NO underlay. The save's fog-of-war raster - 1024x1024,
  proved structurally - may become a toggled layer ONLY after held-out containment of built
  placements, a sign-flip negative control that reddens, and cross-save invariance. Do NOT
  re-pitch a screen-captured or OBS-captured underlay as shipped data; an underlay registered
  to `WorldBounds`, which moves whenever the operator builds; or a fitted transform accepted
  on visual plausibility with no negative control. SECOND, node purity is NOT obtainable and
  is REPLACED rather than approximated: nodes plot unlabelled and shape-coded by class, and
  purity may become an OPERATOR ANNOTATION keyed by instance name. It is never presented as a
  measurement. CS-1040's ledger entry carries the declaration evidence that closes it.
- Surprises, and it is the finding of the session: THE PRE-PUSH GATE BLOCKED THE BATCH TWICE
  AND BOTH REFUSALS WERE CORRECT, and neither fault was visible to any targeted run. The
  first: the new classification block put an id at COLUMN ZERO, which is HEAD POSITION, so the
  work-item scan read it as an entry head it could not parse and reported UNACCOUNTED. That is
  a classifier that blinds the scan to itself - the file gets cleaner-looking by being less
  readable. The second: a correction record named an OPEN item in its HEAD without saying it
  was not a closure, which gave one id two owner files. A whole-suite gate caught both; every
  scoped run this session was green across both.
- Surprises, second: THE HARNESS REPORTED "exit code 0" FOR A BACKGROUNDED RUN WHOSE OWN LOG
  RECORDED `PYTEST_EXIT=1`. No exit code arriving from OUTSIDE the command is evidence about
  the command. Read the log the command wrote.
- Surprises, third: TWO subagents reported a slice GREEN and then corrected themselves to RED
  on a later read of their own logs. The correction came from the log, not from the claim.
- Watch - BYTE CEILINGS ARE NEARLY SPENT AND WANT A DELIBERATE RELOCATE, NOT A TRIM.
  `tests/test_docs_citations.py` has 4 bytes free under its ratchet. `docs/item_notes.md` has
  26 bytes free under its 16 KB budget. `ROADMAP.md` is at 193 percent of its 60 KB soft
  budget even after this session's closed rows came out. The next filing of any size hits one
  of the three. Relocate, never delete.
- Watch, second: FIVE line pointers had drifted and NOT ONE was re-cut at its new offset. Each
  was located by recomputing the frozen line's digest across the file and then converted to
  its ENCLOSING SYMBOL, which is what stops the next edit re-breaking it. One of the five had
  named the WRONG DECLARATION FROM BIRTH rather than merely going stale, so a pointer that
  resolves is not evidence the pointer was ever right.
- Failed paths: do not re-pitch narrowing the gated scan to headings or to a declared field -
  it is the denylist shape this project has measured leaking four times, and it fails OPEN on
  CS-G06. Do not re-pitch rewriting gate prose to unfence a row; that lever is now pinned shut
  by explicit MENTIONED entries. Do not re-derive node purity from a miner's rate or from a
  class name; CS-1040 closed it BY DECLARATION and the ledger records the specifier.
- Next action: CS-1042 - the uncollected set is the live records carrying transforms MINUS the
  collectable pairs CS-1038 now carries up, a SUBTRACTION and not a lookup, and the two halves
  of a pair are not both always present.

## Session 92 - 2026-09-13 - two anti-vacuity repairs closed, and the adversaries found the class in four more places

- Shipped: CS-1025 and CS-1020 CLOSED. Detail in docs/LEDGER.md, not here.
- In flight: nothing. Tree clean, whole suite green at the merge.
- Decisions: no ADR. One correction recorded inside the CS-1025 ledger entry: the filed
  acceptance was insufficient as worded - it demanded a needle be refused above count one,
  while the post-repair defeat mode is count ZERO, so the delivered arm enforces unique AND
  present and the disjoint constants are load-bearing rather than cosmetic.
- Surprises: nothing contradicted BOOTSTRAP.md. What did surprise, and it is the finding of
  the session: with the pre-fix constants the uniqueness helper makes the PRISTINE tree red
  and the MUTATED tree green. The arm's polarity is inverted, so the natural repair for that
  red is to drop a colliding value off the wire - which is the defect. An arm that rewards
  the defect was one fixture edit away from shipping.
- Failed paths: do not treat a uniqueness helper as the whole of CS-1025's fix - it was
  measured insufficient alone, in both the reasoning and a run. Do not repeat the "91 arms"
  figure from CS-1020's filed line as measurement; it appears once in the repository, has no
  collection behind it, and the floor measured at closure was 40 over a narrower population.
- Watch: FOUR privacy arms are structurally incapable of failing - `test_health.py` twice,
  `test_world.py` and `test_registry.py` - because the encoder doubles every backslash and
  the needle is a raw home-shaped path. A body that genuinely reflects a refused path passes
  all four. Filed as CS-1034, tier 1. This is the same trap session 91 hit once, in four more
  places, and it guards non-negotiables 3 and 12.
- CI WENT RED AND THEN GREEN ACROSS A DOC-ONLY COMMIT, WHICH IS THE POINT. The tip e2aff7a
  is GREEN - both jobs success. The commit before it, 9378975, was RED. Run 34791962600 on 9378975
  failed ONLY the "Duration against the budget" step: tier 1 took 491s against a 480s
  ceiling and a 420s budget. Every other step passed - character-set gate, ruff check,
  format check, doc budgets, drift guard, markdown links, type check AND unit tests. The
  ceiling was NOT raised; CS-1012's line forbids that by name. The measurement is worth
  more than the red: the same gate took 355s on 73f4e36 one session earlier and 493s and
  470s on the CS-1009 tree, so the observed spread on this workflow is now 355s to 493s -
  about 140 seconds, far wider than the roughly 20s spread CS-1012 was filed with. A
  ceiling 60s above budget cannot survive that spread whatever the tree does, which is
  evidence for the runner-side hypothesis CS-1012 already names as the first to test.
  THE STRONGEST POINT IS THE PAIR: 9378975 failed the gate and e2aff7a passed it, and the
  two differ by ONE DOC-ONLY COMMIT that adds no test and no code. A gate whose verdict
  flips across a change that cannot affect runtime is measuring the runner, not the tree.
  Do not read the green tip as the problem having gone away.
- Next action: CS-1034 - give every path-shaped privacy needle an oracle proven potent by a
  planted positive the arm FINDS, and redden the four arms on a reflecting body.

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
