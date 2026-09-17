# Clockspeed - which leaf an item lands in

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This file is an ANNEX to `docs/item_notes.md`, not a phase leaf.** It carries no item
section and no `## CS-nnn` heading, so `tools/drift_guard.py` guard (j) neither routes to
it nor reads a section out of it. The leaf table - the leaf membership rule itself - is in
the index; this file holds the seam reasoning that explains it.

**Relocated 2026-09-15 for CS-1062, verbatim.** The index had ELEVEN BYTES of headroom
against its 16384-byte ceiling, so the next session to file an item could not add its
routing row without doing unrelated surgery first. RELOCATED, NOT DELETED - every word in
the NEXT SECTION stood in `docs/item_notes.md` before the move, with exactly two later
exceptions, both made by CS-1112 when it moved the leaf table back to the index: that
section's heading, which read `## Which leaf an item lands in`, and its first line, the
pointer to where the table went. **Two of its paragraphs are no longer there:** CS-1079
made them false - one said phase 4 is four leaves, one that `CS-10nn` took no leaf of its
own - and moved them verbatim to `docs/history_notes.md` under `CS-1079 - retired prose`.
The section after it, written for CS-1079 and not covered by this promise, carries what
replaced them.

## Why the seams sit where they do

**The leaf table moved back to `docs/item_notes.md` by CS-1112, verbatim** - read it there.

**`CS-9nn` IS THE THIRD SEAM AND IT IS A BLOCK BOUNDARY, NOT A SIZE SPLIT.** `CS-8nn`
filled up at 100 of 100, measured 2026-09-05, so the next block was opened by operator
decision on 2026-09-05 rather than by a session allocating an ID in passing -
`docs/adr/0011-the-cs-8nn-follow-up-leaf-splits-at-cs-850.md` anticipated reaching CS-900
and declined to answer it. **CS-901 THROUGH CS-905 ARE NOT ALLOCATABLE**: they are
synthetic fixture IDs in the drift-guard test corpus. The block runs CS-900, then CS-906
onward, and the leaf states the measurement rather than restating the range here.

**THE TWO `CS-8nn` LEAF NAMES ARE NOT SYMMETRIC, SO READ THE TABLE AND NEVER THE
FILENAME.** `phase4-followups.md` does not spell its range and is NOT the whole block -
it is the CS-800 to CS-849 half, and `phase4-followups-850.md` holds the rest. The
unsuffixed name was kept because pointers in `WAKEUP_NOTES.md` and `docs/LEDGER.md`
already spell it; renaming it to gain a symmetric pair would have killed every one of
those to buy what one sentence buys for nothing. Each leaf also states its own range in
its header.

**Relocated 2026-08-25.** This file held all 97 sections until then and had reached 96
per cent of its size budget with no closed sections left to relocate. The split divides
the population; it does not shrink it. **Closure is still the only designed shrink**, and
a leaf that fills has the same remedy this one had.

## What CS-1079 changed

**Written for CS-1079, not relocated.** It replaces the two paragraphs CS-1079 retired from
the section above.

**Phase 4 is six leaves and no seam is arbitrary** - it was five when this paragraph was
written for CS-1079, and CS-1132 split the `CS-9nn` block in two; the next section is that
seam's reasoning. `CS-8nn` is the follow-up block,
created because `CS-4nn` filled up at 98 of 100 - operator decision 2026-08-21, recorded in
`ROADMAP.md`. An ID therefore still says which phase it came from, and membership needs no
judgement. The `CS-8nn` block then split again at CS-850, and the reasoning - including why
the seam sits there rather than at CS-830 or CS-840 - is in
`docs/adr/0011-the-cs-8nn-follow-up-leaf-splits-at-cs-850.md`. `CS-501` is the one stated
exception: it predates the block, keeps its ID, and `ROADMAP.md` files it under phase 4, so
it sits in `phase4.md`. A phase with no OPEN item carrying detail has no leaf, which is why
phase 6 had none until its first sections were written.

**PHASE 4 IDS AT CS-1000 OR ABOVE ARE THEIR OWN LEAF.** Before CS-1079 the `CS-9nn` leaf was
an open-ended floor: its row read as the block while a clause on the `phase4.md` row sent
every higher phase 4 id there too. That leaf then went over its soft doc budget holding ids
its own selector did not name, so a split on the declared selector would have moved
nothing. The seam sits at CS-1000 because that is the first id that selector did not
describe. The new leaf's row spells a FLOOR - `ID at or above CS-1000` - rather than a
block, so `CS-11nn` needs no further decision. The "sends up" clause went with it: the
closed grammar in `tools/drift_guard.py` no longer carries it, every block row is bounded
by its block, and a leading zero in an id number is refused while the `CS-0nn` block
spelling is accepted.

**IN EVERY OTHER PHASE `CS-10nn` TAKES NO LEAF OF ITS OWN, AND THAT IS A DECISION RATHER
THAN AN OMISSION.** The earlier seams exist because a block FILLED UP. The phase leaves
outside phase 4 holding `CS-10nn` sections are inside their budgets, so there the block
routes by PHASE like every other id, and a further leaf would be a seam nobody decided.

**The prose CS-1079 retired is in `docs/history_notes.md`** under `CS-1079 - retired prose`.

## What CS-1132 changed

**Written for CS-1132, not relocated.**

**THE `CS-9nn` BLOCK IS TWO LEAVES, SPLIT AT CS-960, AND THIS IS THE FIRST SEAM THAT IS
NOT A BLOCK BOUNDARY.** Every seam above it exists because a block FILLED UP, so the id
itself said which side of the seam an item fell on and no judgement was needed. CS-960
divides ONE block, and the honest name for what decided it is BYTES: the leaf had come
close enough to its item-notes leaf ceiling in `tools/doc_budget.py` that the next routine
filing pass would have tipped it over, and the session that filed that item would have
paid for a split it did not cause. That is the same condition CS-1079 was filed for.

**THE SEAM WAS MEASURED BEFORE IT WAS CHOSEN, NOT DEFENDED AFTER.** Every section of the
leaf was sized first; CS-960 is the most even division the block offers, and the block
midpoint CS-950 would have left the upper leaf holding two thirds of the bytes on the day
it was created. The figures sit beside the seam constant in `tools/drift_guard.py`, which
OWNS the seam, and are not restated in any leaf.

**BALANCE WAS THE RIGHT THING TO BUY BECAUSE NEITHER HALF GAINS A NEW SECTION.** The
`CS-9nn` block is spent and filing has long since moved past it, so unlike the `CS-8nn`
split - where the upper leaf was the one that would grow - neither half here grows except
as the sections already in it are added to. A seam placed to leave room at the top of the
block would have bought room nothing was going to use.

**THE TWO LEAF NAMES ARE HONEST AND THE PAIR IS STILL NOT SYMMETRIC.**
`phase4-followups-900.md` keeps its name and now holds only the block below CS-960, so its
name reads as a floor that its range no longer reaches to the top of - the same trap the
`CS-8nn` pair sets, for the same reason: the name is spelled in pointers that already
exist. Read the leaf table in `docs/item_notes.md`, never a filename.

**CLOSURE IS STILL THE ONLY DESIGNED SHRINK**, and this split divides a population without
shrinking it, exactly as the 2026-08-25 split did.
