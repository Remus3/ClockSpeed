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

## Session 42 - 2026-08-25 - CS-852's repr-channel guard ships and four live leaks close; four adversaries all REFUTE the closure; the finding is that the guard reproduced the very blindness it was built against

- **Shipped: NOTHING CLOSED. CS-852 STAYS OPEN.** The guard merged, three shipped classes
  were repaired and a fourth leak was closed, and four adversaries with distinct lenses all
  returned REFUTED. Detail in `docs/LEDGER.md` and
  `docs/item_notes/phase4-followups.md`, not here.

- **THE DERIVATION FOUND TWICE WHAT THE ITEM NAMED.** CS-852 named `DecompressedBody`.
  Deriving the population from shipped field annotations also found `SaveListing.saves` -
  a tuple of `.sav` paths, so the account id and the home directory - and
  `ForbiddenRoot.resolved`, in a class whose own docstring says `label` exists so a refusal
  need not render a path. Both were named in no note, no doc and no guard.

- **REPAIRING THEM EXPOSED A FOURTH LEAK NO GUARD COULD SEE.** Giving `DecompressedBody` a
  `__repr__` moved it into CS-850's population - which is derived from classes SHIPPING one
  - and CS-851 immediately flagged the raw decompressed body held in a local at an assert.
  A class that declares nothing is invisible to the guards, not merely to readers. That is
  the item's own thesis turned on the guards themselves.

- **THE HEADLINE FINDING: THE GUARD BUILT AGAINST A BLIND POPULATION WAS ITSELF BLIND, IN
  FOUR PLACES.** `BaseException.__repr__` is NOT `object.__repr__` - it renders `args` - so
  the `KIND_INHERITED` grade silenced 24 save-layer error classes, and an adversary added a
  save-derived field to one, interpolated it into the message, and stayed green. The forced
  arms had NO POSITIVE CONTROL, so `assert MARKER not in rendered` passed equally when the
  marker was never planted. The exemption reasons were graded by LENGTH, so forty literal
  characters passed. And the population was pinned for 14 of 43 members, so the other 29
  could leave one at a time. All four are now closed or recorded; the exception channel is
  recorded rather than graded, and that is why the item stays open.

- **A REPAIR OF MINE MADE THE TREE WORSE AND AN ADVERSARY CAUGHT IT.** I hoisted a
  loop-invariant assert out of a per-save loop to clear a CS-851 finding. The original sat
  under `except (Exception, SystemExit)`, which CATCHES `AssertionError` - so it could never
  render anything and the finding was a STATIC FALSE POSITIVE - while my hoisted copy
  unwound through a frame holding the real library save paths. One marker occurrence
  hoisted, zero inside the try. **Check what a frame HOLDS before moving an assert into
  it.** It now lives in its own test whose frame holds two dicts of width names.

- **Decisions: none recorded as an ADR.** One operator round chose CS-852 as the unit, and a
  second ruled that adversaries be dispatched before any closure - the section 5 shape,
  since the merger produced the work and may not grade it.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But two names I wrote were fabricated:
  an exemption cited a private helper that has never existed in this repository, and a
  corrected reason then cited a function name copied from an adversary's report without
  checking it. The new identifier check caught the second on its first run.

- **Failed paths: one, abandoned on measurement.** Grading a hand-written `__repr__` for
  every disclosing `str` field, not just carriers, reported six correctly redacting classes
  including `ResourceNode`, whose repr shows the game `class_name` on purpose. The seam is
  that a GENERATED repr made no per-field decision and is CS-852's; a hand-written one did
  and is CS-850's.

- **Next action: NONE IS FORCED.** If CS-852 is resumed, start at the exception channel -
  it needs the message-building CODE PATH, not field annotations, which is a different
  analysis from the one this session built.

---

## Session 41 - 2026-08-25 - `docs/item_notes.md` SPLIT per phase with an index; CS-856 closes; guard (j) ships; two controls were one edit away from grading an empty population

- **Shipped: CS-856 CLOSES.** `docs/item_notes.md` is now an index over `docs/item_notes/`,
  six leaves, 97 bodies moved byte-for-byte. Detail in `docs/LEDGER.md`, not here.
- **In flight: NOTHING.** No half-done work, no dirty file, no held branch beyond the four
  already preserved. **ADR 0010 was ACCEPTED by operator ruling the same day**, so the split
  is settled and binding. ADR 0009 remains `proposed` with no roadmap item.
- **Decisions: ADR 0010.** Three operator choices, each with its fence: split at the
  `CS-4nn`/`CS-8nn` seam rather than one 182 KB phase-4 leaf; ROADMAP item lines point at
  the INDEX and never at a leaf; record it as an ADR plus both topology tables.
- **Surprises: none contradicted `BOOTSTRAP.md`.** The measurement that DID change the
  design was that a literal per-phase split leaves 84 per cent of the content in one file,
  which was taken before any file was written and is why phase 4 is two leaves.
- **Failed paths: two, both mine, both caught by a contract rather than by review.** A
  byte-conservation check summed `for v in written` - the KEYS, not the values - and read as
  a catastrophic loss; and the `CS-492` disposition key was repointed at `phase4.md` by
  reasoning from the item id when the pointer actually sits in `phase4-followups.md`. Do not
  infer a body's leaf from the item id it names.
- **Next action: NONE IS FORCED.** CS-829 remains the head of the product path.

---

## Session 40 - 2026-08-25 - a LIVE tier-1 leak found on main and closed; four items build, all four are REFUTED, all four are repaired, and NOTHING CLOSES; the finding is that an empty population satisfies every assertion of zero

- **Shipped: NOTHING CLOSED.** CS-829, CS-846, CS-850 and CS-851 all merged as improvements
  after a build round AND a repair round, and every one STAYS OPEN. Filed CS-852 through
  CS-855. Detail in `docs/LEDGER.md` and `docs/item_notes.md`, not here.

- **A LIVE TIER-1 PRIVACY LEAK WAS ON `main` AND IS NOW CLOSED.**
  `tests/save/test_world.py` rendered the RAW world token and map name into a failure report
  **under default flags** - pre-push hook and both CI lanes - because assertion rewriting
  renders the ARGUMENT of an inline `len()`. The test whose purpose is proving the world
  model reprs without leaking, leaked. Found by an adversary sent to grade a different item.

- **THE HEADLINE FINDING: AN EMPTY POPULATION SATISFIES EVERY ASSERTION OF ZERO.**
  `assert count == 0` passes when the property holds AND when nothing was measured, and the
  two produce byte-identical output. Five instances in one session, filed as
  `memory/an-empty-population-satisfies-every-zero.md`. The worst: a second reading of the
  save grammar omitted a 16-byte guid step, desynchronised at the FIRST struct tag, found
  ZERO struct sites in 87302 accepted records, and satisfied its `== 0` arm for roughly
  forty sessions while being sold in prose as independent corroboration.
  **This is the mirror of session 39's finding** - that one was green because the defect was
  present; this one is green because the DETECTOR IS SILENT.

- **FIVE ADVERSARIAL PASSES: FOUR REFUTATIONS, ONE CONFIRMATION.** Not one finding would
  have come from the agent that built the thing. Two refutations landed on the same shape -
  a guard green because its detector is blind, not because the property holds.

- **A DEFECT REPAIRED AT ITS SITE RELOCATES - CS-829's IS NOW ON ITS FOURTH SITE**, having
  moved to `objects.parse_body`, the record table BOTH readings share. The independence
  audit is clean and the module DISCLOSES the shared substrate; disclosure is not a guard.

- **NEW, AND IT IS THE GOOD KIND OF SURPRISE: A REPAIR WAS REFUTED BY ITS OWN VALIDATION.**
  The slice instructed to make a fitted ceiling SKIP built it, measured that the skip let a
  real defect survive, REVERTED its own instructed fix, and recorded the attempt and its
  refutation at the constant. Three of four repair slices pushed back on the merger's brief
  with measurements, and all three were right.

- **CI CAUGHT WHAT THE WHOLE LOCAL SUITE COULD NOT, AND THE LESSON IS THE SESSION'S THEME
  AGAIN.** The pre-push hook ran the full suite green - 2892 passed - and tier1 FAILED on the
  same commit with 33 findings. The new source-echo rule ran the runtime redactor over each
  whole source line; this machine's account name appears in no source at all,
  while CI's is `runner`, an ordinary English substring inside identifiers everywhere.
  **A CHECK THAT READS THE MACHINE IT RUNS ON REPORTS ABOUT THE MACHINE, NOT THE TREE** - and
  its note claimed it "cannot false-positive, because it fires on an actual value rather than
  on a shape". An actual value is still a SHAPE when the value is a common word. Reproduced
  locally with a CI-shaped redactor: 70 hits over 33 files before, 0 after, still firing on a
  planted home path. **Do not read a green local suite as evidence about the tree** - this is
  CS-839 generalised from which SHELL to which MACHINE.

- **Decisions: none recorded as an ADR.** One operator round at the start, taking all four
  units and ruling CS-844 HELD for a third session.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But the binding census in the CS-851
  guard was blind to `ast.Try` ENTIRELY - `except-target` went 0 to 115 named handlers - so
  every count derived from it before this session was an UNDER-count, including an
  adversary's own false-negative analysis.

- **Failed paths: none abandoned.** CS-844 remains held, its worktree and three commits
  intact.

- **Next action: NONE IS FORCED.** CS-829 remains the head of the product path and now needs
  a denominator independent of the RECORD TABLE, not merely of the tag-list reader.

- **A COUNT IN THE LAST NOTE WAS FALSE.** It recorded 99 open items; `d813e22` carried 97.
  Do not restate counts here - read them from the tool.

- **DOC BUDGET IS THE BINDING CONSTRAINT NOW.** `docs/item_notes.md` finished at 96 per cent
  after 6.5 KB was relocated to `docs/history_notes.md`, and it holds ZERO closed-item
  sections, so relocation is nearly exhausted. Four merged-without-closing items plus four
  new ones is what 96 per cent looks like. **This needs an operator decision next session** -
  split the file per phase with an index, raise the budget, or accept that a session can add
  at most one or two item blocks.
