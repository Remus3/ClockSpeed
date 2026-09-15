# Clockspeed - which leaf an item lands in

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This file is an ANNEX to `docs/item_notes.md`, not a phase leaf.** It carries no item
section and no `## CS-nnn` heading, so `tools/drift_guard.py` guard (j) neither routes to
it nor reads a section out of it. The routing TABLE stays in the index; this file holds the
rule that explains it.

**Relocated 2026-09-15 for CS-1062, verbatim.** The index had ELEVEN BYTES of headroom
against its 16384-byte ceiling, so the next session to file an item could not add its
routing row without doing unrelated surgery first. RELOCATED, NOT DELETED - every word
below stood in `docs/item_notes.md` before the move.

## Which leaf an item lands in

An item's leaf follows from the phase heading `ROADMAP.md` files it under, so the
mapping has one owner and this file only reports it:

| Leaf | Holds |
|---|---|
| `docs/item_notes/phase4.md` | ROADMAP `Phase 4`, ID BELOW the `CS-8nn` block. NOT the `CS-10nn` block - the rule sends every phase 4 ID at 900 or higher to the `CS-9nn` leaf |
| `docs/item_notes/phase4-followups.md` | ROADMAP `Phase 4`, ID in the `CS-8nn` block below CS-850 |
| `docs/item_notes/phase4-followups-850.md` | ROADMAP `Phase 4`, ID in the `CS-8nn` block at or above CS-850 |
| `docs/item_notes/phase4-followups-900.md` | ROADMAP `Phase 4`, ID in the `CS-9nn` block |
| `docs/item_notes/phase5.md` | ROADMAP `Phase 5` |
| `docs/item_notes/phase6.md` | ROADMAP `Phase 6` |
| `docs/item_notes/phase7.md` | ROADMAP `Phase 7` |
| `docs/item_notes/cs988-sweep-record.md` | ANNEX, not a phase leaf - CS-988's per-site sweep measurements. A declared departure from one-leaf-per-phase, because it is measurement data for an OPEN item rather than an item body |
| `docs/item_notes/lane-start-failure-record.md` | ANNEX, not a phase leaf - the read-only diagnosis of the 2026-09-11 lane start failure, feeding CS-1017, CS-1018 and CS-1001. A declared departure, on the same grounds as the row above |
| `docs/item_notes/leaf-membership-rule.md` | ANNEX, not a phase leaf - the leaf membership rule itself, relocated here by CS-1062. A declared departure on the same grounds as the two rows above: it is routing DOCTRINE rather than an item body |

**Phase 4 is four leaves and no seam is arbitrary.** `CS-8nn` is the follow-up
block, created because `CS-4nn` filled up at 98 of 100 - operator decision 2026-08-21,
recorded in `ROADMAP.md`. An ID therefore still says which phase it came from, and
membership needs no judgement. The `CS-8nn` block then split again at CS-850, and the
reasoning - including why the seam sits there rather than at CS-830 or CS-840 - is in
`docs/adr/0011-the-cs-8nn-follow-up-leaf-splits-at-cs-850.md`. `CS-501` is the one
stated exception: it predates the block, keeps its ID, and `ROADMAP.md` files it under
phase 4, so it sits in `phase4.md`. A phase with no OPEN item carrying detail has no
leaf, which is why phase 6 had none until its first sections were written.

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

**`CS-10nn` TOOK NO LEAF OF ITS OWN, AND THAT IS A DECISION RATHER THAN AN OMISSION.**
The earlier seams exist because a block FILLED UP. The phase leaves now holding the first
`CS-10nn` sections are inside their budgets, so the block routes by PHASE like every other
id and a fourth phase-4 leaf would be a seam nobody decided.
