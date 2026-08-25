# 0010 - `docs/item_notes.md` is an index over per-phase leaves

## Status

`proposed` - 2026-08-25

Written by the session that performed the split, which leaves it `proposed` because per
`CLAUDE.md` section 5 the producing agent does not grade its own output. An adjudicator
that did not perform the split decides whether it reaches `accepted`.

## Context

`docs/item_notes.md` was created 2026-08-23 under an operator ruling that moved every NOTE
body out of `ROADMAP.md` and every live-instruction block out of `docs/history_notes.md`. It
landed at 163.7 KB and was given a 224 KB budget - the round number roughly 37 per cent
above its landing size, sized so the warn would still mean something when it finally
printed.

It printed. The file finished session 40 at 96 per cent of that budget.

**The remedy the budget prescribes was already exhausted.** `tools/doc_budget.py` says
RELOCATE, DO NOT DELETE, and the file's own designed shrink is an item CLOSING - a closed
item's section moves to `docs/history_notes.md`. But the file held ZERO closed sections:
6.5 KB had already been relocated that session, four items had merged as improvements
without closing, and four new items had been filed. There was nothing left to move.

The operator was given three options and chose the split. The other two are recorded here
so they are not re-proposed as though they had never been weighed:

- **Raise the budget.** Rejected. `ROADMAP.md` is the worked example of what that produces:
  its budget was raised, it returned to its ceiling, and it needed two relocate passes in
  one day at 9 then 97 bytes of margin. A budget raised to fit the file it measures teaches
  everyone to ignore it.
- **Accept one or two item blocks per session.** Rejected. It converts a doc-size problem
  into a cap on how much work a session may record, which prices the wrong thing.

**A LITERAL PER-PHASE SPLIT DOES NOT RELIEVE THE PRESSURE, and this was measured before the
split was designed.** Grouping the 97 sections by the phase heading `ROADMAP.md` files each
item under gives phase 2 at 1.1 KB, phase 3 at 1.4 KB, phase 5 at 3.3 KB, phase 7 at 24.7 KB
- and **phase 4 at 181.9 KB across 78 items, 84 per cent of the content**. Every item filed
in session 40 was phase 4, so the one file that stayed large would also have been the only
one that grew.

Phase 4 already carries an internal seam that the operator decided on 2026-08-21 for an
unrelated reason: `CS-4nn` filled up at 98 of 100, so `CS-8nn` became the phase-4 follow-up
block, chosen precisely so an ID would still say which phase it came from. Splitting phase 4
there needs no new judgement and yields 48 items at 91.2 KB and 30 items at 90.8 KB.

## Decision

**`docs/item_notes.md` holds no item bodies. It is the index over `docs/item_notes/`, which
holds one leaf per phase, one section per item ID.**

- **An item's leaf follows from the phase heading `ROADMAP.md` files it under**, so that
  mapping keeps exactly one owner. Phase 4 splits at the `CS-8nn` block. `CS-501` is the one
  stated exception - it predates that block, keeps its ID, and `ROADMAP.md` files it under
  phase 4.
- **The index keeps the path every pointer already names.** Measured 2026-08-25: all 97
  `ROADMAP.md` item lines, two test constants, one tool path, and every doc that points a
  reader at per-item detail name `docs/item_notes.md`. Making the index that file rather
  than `docs/item_notes/README.md` cost zero pointer churn, and left no window in which a
  stale pointer resolved to nothing.
- **A `ROADMAP.md` item line points at the index, never at a leaf.** Spelling the leaf on
  each line would restate the item-to-phase mapping 97 times, and a restated fact is a fact
  that will drift. One hop is the price of one owner.
- **The routing table is machine-checked in both directions** by `tools/drift_guard.py`
  guard (j): a routed item with no section, a section with no row, and a row naming the
  wrong leaf are each a FAIL. A family holding no row and no section is a WARN carrying a
  skip record - not a pass - because every equality the guard asserts is satisfied for free
  by an empty population.
- **Budgets are per leaf, not per family.** The index gets 16 KB; each leaf gets 128 KB,
  which is the same roughly-37-per-cent margin above the largest measured leaf that the
  224 KB single-file budget was chosen with. A budget summed over a population is met by
  its strongest member while the weakest goes unmeasured.
- **All 97 bodies moved VERBATIM**, proven byte-for-byte against the committed copy rather
  than asserted.

## Consequences

**Easier.** A session reads one leaf instead of a 220 KB file. The two large leaves sit at
72 per cent of their budget against 96 per cent before. A new leaf can be added by a later
relocate pass without another topology change - `tools/doc_budget.py` and
`tests/test_docs_citations.py` both derive the leaf population from the directory rather
than listing it.

**Harder.** Finding an item costs one hop through the routing table. A grep across per-item
detail now spans a directory rather than a file.

**Foreclosed.** Writing an item body into `docs/item_notes.md` - guard (j) fails on it, and
a body there would be invisible to every reader following the table.

**THE LIMIT, STATED RATHER THAN LEFT TO BE DISCOVERED. This split divides the population; it
does not shrink it.** Newly filed items land overwhelmingly in the `CS-8nn` follow-up leaf,
so that leaf is the one that grows, and 128 KB leaves it roughly a dozen more items' worth
of detail at session-40 sizes. **CLOSURE IS STILL THE ONLY DESIGNED SHRINK.** Reading this
split as a permanent fix is the error this paragraph exists to prevent.

**Revisit if** the item-to-phase mapping stops living in `ROADMAP.md`'s headings, or if a
phase other than 4 grows past one leaf - the second is a new leaf under the existing rule,
not a new decision.
