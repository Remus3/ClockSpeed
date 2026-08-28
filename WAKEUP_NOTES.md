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

## Session 43 - 2026-08-28 - the exception channel graded from both ends; BOTH guards refuted on the SAME defect, independently, in one session - a syntactic bare-name match sold as a population zero

- **Shipped: NOTHING CLOSED. CS-852 AND CS-855 BOTH STAY OPEN.** Both guards merged as
  improvements after adversarial refutation and repair. CS-857 is newly filed. Detail in
  `docs/LEDGER.md` and `docs/item_notes/phase4-followups.md`, not here.

- **THE HEADLINE: TWO GUARDS, BUILT INDEPENDENTLY BY DIFFERENT AGENTS AGAINST DIFFERENT
  CHANNELS, FAILED THE SAME WAY IN THE SAME SESSION.** CS-855's detector keyed on a bare
  name, so `kept = exc` defeated it. CS-852's `proven-vocabulary` resolved a callee by bare
  name, so a function merely NAMED `_checked_field` earned the proof. Neither author saw
  it; both adversaries found it inside twenty minutes. **A SYNTACTIC MATCH STANDING IN FOR
  A SEMANTIC PROPERTY, THEN REPORTED AS A POPULATION ZERO** is now the dominant failure
  shape in this project, and it is the case for the producer-never-grades rule made twice
  over in one sitting.

- **CS-852's FAILURE WAS WORSE IN KIND AND THE DISTINCTION IS WORTH KEEPING.** CS-855
  reported SILENCE; CS-852 returned POSITIVE FALSE PROOFS. A `proven-*` verdict is a
  clearance a later session will cite as evidence. Nine such paths existed, one of them
  grading `', '.join(free) or 'no recipe'` - LIVE HOUSE STYLE at four sites in
  `clockspeed/solve/` - as an annotation whose whole value space is numbers and flags.

- **A REAL SAVE-DERIVED VALUE REACHED `args` IN A REAL SHIPPED CLASS WITH THE GUARD GREEN
  AND THE REPORT BYTE-IDENTICAL.** `instance_name` off the save body at
  `clockspeed/save/objects.py:1747` into `ObjectFormatError`. That plant is now mutant M9
  and is killed.

- **A NEW CHANNEL WAS FOUND AND FILED RATHER THAN ABSORBED - CS-857.** `raise X(...) from
  exc` puts the CAUSE's text in the formatted traceback: the graded message renders
  redacted while the chained `OSError` renders the raw path beside it. **SEVERITY IS SPLIT
  AND THE SPLIT WAS MEASURED** - under pytest the CS-428 redactor at `tests/conftest.py:665`
  scrubs it, so it does NOT leak in the suite or either CI lane; it leaks on every
  rendering path that is not a pytest report. 7 of 11 CS-852 exemption keys sit on a
  chained raise, and two of their reasons call the cause "deliberately never rendered",
  true of `args` and false of the interpreter.

- **A THIRD ECHO MECHANISM NOBODY HAD RECORDED: THE FRAME ARGUMENT.** An exception handed
  to a callee renders in that callee's frame header under default flags, surviving
  `raise ... from None`. It is the construct `tests/test_exception_rendering.py:75` names
  as "the FIX" for CS-205. NOT a live leak - `repr()` of an OSError omits `filename` - but
  the remedy and the echo path are the same construct.

- **Decisions: none recorded as an ADR.** Two operator rounds: CS-852 gap 1 plus CS-855
  chosen as the unit, and the `chunks.py`/`usmap.py` vocabulary gate ruled REPAIR IT NOW.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But `clockspeed/save/world.py`'s
  safety paragraph was FALSE WHEN WRITTEN - it claimed all four parsers pin the
  closed-vocabulary guarantee with a planted-marker test. The obvious repair would have
  made it false in a NEW way, because header.py and objects.py have no refusal test either.
  Corrected to state per module what is actually pinned.

- **Failed paths: none abandoned.** Two merger claims were withdrawn under measurement -
  that the CS-855 acceptance is unsatisfiable, and that the long-carried 115 was a category
  error. 115 was correct when filed at `f19d1f2` and drifted to 117.

- **THREE MERGER ERRORS, ALL CAUGHT BY SOMEONE ELSE, ALL WORTH REPEATING.** A brief said
  "five ChunkError subclasses"; the slice MEASURED four and corrected it. A `grep "planted"`
  was offered as evidence of an absent control - a WORD search, not a PROPERTY search, and
  the file already pinned three other clauses. And an item-note anchor assumed the leaf's
  sections run in ID order; they do not, and the note would have landed in the wrong item.

- **Next action: NONE IS FORCED.** If CS-852 is resumed, the cheapest real gain is residual
  3 - replace the transcribed `ARGS_ROOTS` with a runtime census; an adversary already ran
  it and measured 47 == 47. CS-857 is unstarted and is the only tier-1 item here with a
  measured live rendering path.

- **DOC BUDGET IS TIGHTENING AGAIN.** `docs/item_notes/phase4-followups.md` finished at 90
  per cent. The ADR 0010 split bought one session of room and this session spent most of it.

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
