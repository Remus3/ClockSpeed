# Clockspeed - live per-item detail, index

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This file owns the INDEX and the family rules. The per-item bodies live in the
leaves under `docs/item_notes/`.** One leaf per phase, one section per item ID inside
it. A block in a leaf is a LIVE INSTRUCTION: read an item's section BEFORE taking that
item, and use the routing table below to find which leaf holds it.

`ROADMAP.md` owns the item LINE and nothing else - the ID, the headline, the acceptance
criterion and the tier. Its lines point at THIS file rather than at a leaf, deliberately:
ROADMAP's own phase headings are the single owner of which phase an item belongs to, and
repeating that mapping on every item line would be a restated fact with somewhere to
drift to. One hop through the table below is the cost of keeping one owner.

**This family NEVER contains:** the item line itself, a completion record
(`docs/LEDGER.md` owns those), an aspirational item (`BACKLOG.md` owns those), the
external condition blocking a gated item (`docs/GATED.md` owns that), or history.
**When an item CLOSES its section moves to `docs/history_notes.md`**, because at that
point it IS history - that move is what keeps these files live and that file's header
true. A closing item's section does NOT move to another leaf.

**THIS FILE HOLDS NO ITEM BODIES.** It carries no `## CS-nnn` section and never will;
that is asserted by `tools/drift_guard.py` guard (j), not merely intended. A body
written here instead of in its leaf is invisible to every reader who follows the table.

## Which leaf an item lands in

An item's leaf follows from the phase heading `ROADMAP.md` files it under, so the
mapping has one owner and this file only reports it:

| Leaf | Holds |
|---|---|
| `docs/item_notes/phase3.md` | ROADMAP `Phase 3` |
| `docs/item_notes/phase4.md` | ROADMAP `Phase 4`, ID outside the `CS-8nn` block |
| `docs/item_notes/phase4-followups.md` | ROADMAP `Phase 4`, ID in the `CS-8nn` block below CS-850 |
| `docs/item_notes/phase4-followups-850.md` | ROADMAP `Phase 4`, ID in the `CS-8nn` block at or above CS-850 |
| `docs/item_notes/phase4-followups-900.md` | ROADMAP `Phase 4`, ID in the `CS-9nn` block |
| `docs/item_notes/phase5.md` | ROADMAP `Phase 5` |
| `docs/item_notes/phase6.md` | ROADMAP `Phase 6` |
| `docs/item_notes/phase7.md` | ROADMAP `Phase 7` |

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

## Routing table

Derived from the leaves, checked in BOTH directions by `tools/drift_guard.py` guard (j):
a routed item with no section, a section with no row, and a row naming the wrong leaf are
each a FAIL. A family holding NO row and NO section is a WARN carrying a skip record, not
a pass - every equality here is satisfied for free by an empty population.

| Item | Leaf |
|---|---|
| CS-301 | `docs/item_notes/phase3.md` |
| CS-302 | `docs/item_notes/phase3.md` |
| CS-303 | `docs/item_notes/phase3.md` |
| CS-400 | `docs/item_notes/phase4.md` |
| CS-401 | `docs/item_notes/phase4.md` |
| CS-412 | `docs/item_notes/phase4.md` |
| CS-425 | `docs/item_notes/phase4.md` |
| CS-426 | `docs/item_notes/phase4.md` |
| CS-432 | `docs/item_notes/phase4.md` |
| CS-439 | `docs/item_notes/phase4.md` |
| CS-440 | `docs/item_notes/phase4.md` |
| CS-441 | `docs/item_notes/phase4.md` |
| CS-443 | `docs/item_notes/phase4.md` |
| CS-444 | `docs/item_notes/phase4.md` |
| CS-445 | `docs/item_notes/phase4.md` |
| CS-446 | `docs/item_notes/phase4.md` |
| CS-447 | `docs/item_notes/phase4.md` |
| CS-448 | `docs/item_notes/phase4.md` |
| CS-449 | `docs/item_notes/phase4.md` |
| CS-450 | `docs/item_notes/phase4.md` |
| CS-451 | `docs/item_notes/phase4.md` |
| CS-452 | `docs/item_notes/phase4.md` |
| CS-453 | `docs/item_notes/phase4.md` |
| CS-454 | `docs/item_notes/phase4.md` |
| CS-455 | `docs/item_notes/phase4.md` |
| CS-456 | `docs/item_notes/phase4.md` |
| CS-457 | `docs/item_notes/phase4.md` |
| CS-458 | `docs/item_notes/phase4.md` |
| CS-459 | `docs/item_notes/phase4.md` |
| CS-460 | `docs/item_notes/phase4.md` |
| CS-461 | `docs/item_notes/phase4.md` |
| CS-462 | `docs/item_notes/phase4.md` |
| CS-464 | `docs/item_notes/phase4.md` |
| CS-465 | `docs/item_notes/phase4.md` |
| CS-466 | `docs/item_notes/phase4.md` |
| CS-467 | `docs/item_notes/phase4.md` |
| CS-468 | `docs/item_notes/phase4.md` |
| CS-470 | `docs/item_notes/phase4.md` |
| CS-472 | `docs/item_notes/phase4.md` |
| CS-473 | `docs/item_notes/phase4.md` |
| CS-474 | `docs/item_notes/phase4.md` |
| CS-477 | `docs/item_notes/phase4.md` |
| CS-479 | `docs/item_notes/phase4.md` |
| CS-483 | `docs/item_notes/phase4.md` |
| CS-484 | `docs/item_notes/phase4.md` |
| CS-488 | `docs/item_notes/phase4.md` |
| CS-489 | `docs/item_notes/phase4.md` |
| CS-490 | `docs/item_notes/phase4.md` |
| CS-492 | `docs/item_notes/phase4.md` |
| CS-499 | `docs/item_notes/phase4.md` |
| CS-500 | `docs/item_notes/phase5.md` |
| CS-501 | `docs/item_notes/phase4.md` |
| CS-609 | `docs/item_notes/phase6.md` |
| CS-614 | `docs/item_notes/phase6.md` |
| CS-615 | `docs/item_notes/phase6.md` |
| CS-616 | `docs/item_notes/phase6.md` |
| CS-618 | `docs/item_notes/phase6.md` |
| CS-619 | `docs/item_notes/phase6.md` |
| CS-872 | `docs/item_notes/phase6.md` |
| CS-701 | `docs/item_notes/phase7.md` |
| CS-704 | `docs/item_notes/phase7.md` |
| CS-800 | `docs/item_notes/phase4-followups.md` |
| CS-801 | `docs/item_notes/phase4-followups.md` |
| CS-802 | `docs/item_notes/phase4-followups.md` |
| CS-803 | `docs/item_notes/phase4-followups.md` |
| CS-804 | `docs/item_notes/phase4-followups.md` |
| CS-805 | `docs/item_notes/phase4-followups.md` |
| CS-807 | `docs/item_notes/phase4-followups.md` |
| CS-808 | `docs/item_notes/phase4-followups.md` |
| CS-811 | `docs/item_notes/phase7.md` |
| CS-812 | `docs/item_notes/phase7.md` |
| CS-813 | `docs/item_notes/phase7.md` |
| CS-814 | `docs/item_notes/phase7.md` |
| CS-815 | `docs/item_notes/phase7.md` |
| CS-816 | `docs/item_notes/phase7.md` |
| CS-817 | `docs/item_notes/phase7.md` |
| CS-818 | `docs/item_notes/phase7.md` |
| CS-820 | `docs/item_notes/phase7.md` |
| CS-821 | `docs/item_notes/phase7.md` |
| CS-822 | `docs/item_notes/phase7.md` |
| CS-824 | `docs/item_notes/phase7.md` |
| CS-953 | `docs/item_notes/phase7.md` |
| CS-700 | `docs/item_notes/phase7.md` |
| CS-825 | `docs/item_notes/phase4-followups.md` |
| CS-826 | `docs/item_notes/phase4-followups.md` |
| CS-827 | `docs/item_notes/phase4-followups.md` |
| CS-828 | `docs/item_notes/phase4-followups.md` |
| CS-832 | `docs/item_notes/phase4-followups.md` |
| CS-839 | `docs/item_notes/phase4-followups.md` |
| CS-840 | `docs/item_notes/phase4-followups.md` |
| CS-841 | `docs/item_notes/phase4-followups.md` |
| CS-842 | `docs/item_notes/phase4-followups.md` |
| CS-843 | `docs/item_notes/phase4-followups.md` |
| CS-844 | `docs/item_notes/phase4-followups.md` |
| CS-846 | `docs/item_notes/phase4-followups.md` |
| CS-847 | `docs/item_notes/phase4-followups.md` |
| CS-848 | `docs/item_notes/phase4-followups.md` |
| CS-849 | `docs/item_notes/phase4-followups.md` |
| CS-850 | `docs/item_notes/phase4-followups-850.md` |
| CS-851 | `docs/item_notes/phase4-followups-850.md` |
| CS-852 | `docs/item_notes/phase4-followups-850.md` |
| CS-853 | `docs/item_notes/phase4-followups-850.md` |
| CS-854 | `docs/item_notes/phase4-followups-850.md` |
| CS-855 | `docs/item_notes/phase4-followups-850.md` |
| CS-857 | `docs/item_notes/phase4-followups-850.md` |
| CS-858 | `docs/item_notes/phase4-followups-850.md` |
| CS-859 | `docs/item_notes/phase4-followups-850.md` |
| CS-860 | `docs/item_notes/phase4-followups-850.md` |
| CS-861 | `docs/item_notes/phase4-followups-850.md` |
| CS-864 | `docs/item_notes/phase4-followups-850.md` |
| CS-865 | `docs/item_notes/phase4-followups-850.md` |
| CS-868 | `docs/item_notes/phase4-followups-850.md` |
| CS-869 | `docs/item_notes/phase4-followups-850.md` |
| CS-870 | `docs/item_notes/phase4-followups-850.md` |
| CS-871 | `docs/item_notes/phase4-followups-850.md` |
| CS-887 | `docs/item_notes/phase6.md` |
| CS-892 | `docs/item_notes/phase4-followups-850.md` |
| CS-893 | `docs/item_notes/phase4-followups-850.md` |
| CS-894 | `docs/item_notes/phase4-followups-850.md` |
| CS-895 | `docs/item_notes/phase4-followups-850.md` |
| CS-896 | `docs/item_notes/phase4-followups-850.md` |
| CS-898 | `docs/item_notes/phase4-followups-850.md` |
| CS-899 | `docs/item_notes/phase4-followups-850.md` |
| CS-900 | `docs/item_notes/phase4-followups-900.md` |
| CS-907 | `docs/item_notes/phase4-followups-900.md` |
| CS-917 | `docs/item_notes/phase4-followups-900.md` |
| CS-919 | `docs/item_notes/phase4-followups-900.md` |
| CS-920 | `docs/item_notes/phase4-followups-900.md` |
| CS-929 | `docs/item_notes/phase4-followups-900.md` |
| CS-930 | `docs/item_notes/phase4-followups-900.md` |
| CS-933 | `docs/item_notes/phase4-followups-900.md` |
| CS-936 | `docs/item_notes/phase4-followups-900.md` |
| CS-941 | `docs/item_notes/phase4-followups-900.md` |
| CS-942 | `docs/item_notes/phase4-followups-900.md` |
| CS-943 | `docs/item_notes/phase4-followups-900.md` |
| CS-944 | `docs/item_notes/phase4-followups-900.md` |
| CS-945 | `docs/item_notes/phase4-followups-900.md` |
| CS-946 | `docs/item_notes/phase4-followups-900.md` |
| CS-947 | `docs/item_notes/phase4-followups-900.md` |
| CS-948 | `docs/item_notes/phase4-followups-900.md` |
| CS-951 | `docs/item_notes/phase4-followups-900.md` |
| CS-958 | `docs/item_notes/phase4-followups-900.md` |
| CS-965 | `docs/item_notes/phase4-followups-900.md` |
| CS-964 | `docs/item_notes/phase4-followups-900.md` |
| CS-962 | `docs/item_notes/phase4-followups-900.md` |
| CS-937 | `docs/item_notes/phase4-followups-900.md` |
| CS-938 | `docs/item_notes/phase4-followups-900.md` |
| CS-939 | `docs/item_notes/phase4-followups-900.md` |
| CS-909 | `docs/item_notes/phase6.md` |
| CS-910 | `docs/item_notes/phase6.md` |
| CS-876 | `docs/item_notes/phase4-followups-850.md` |
| CS-877 | `docs/item_notes/phase4-followups-850.md` |
| CS-604 | `docs/item_notes/phase6.md` |
| CS-606 | `docs/item_notes/phase6.md` |
| CS-607 | `docs/item_notes/phase6.md` |
| CS-610 | `docs/item_notes/phase6.md` |
| CS-611 | `docs/item_notes/phase6.md` |
| CS-612 | `docs/item_notes/phase6.md` |
| CS-620 | `docs/item_notes/phase6.md` |
| CS-621 | `docs/item_notes/phase6.md` |
| CS-622 | `docs/item_notes/phase6.md` |
| CS-623 | `docs/item_notes/phase6.md` |
| CS-913 | `docs/item_notes/phase6.md` |
| CS-914 | `docs/item_notes/phase6.md` |
| CS-915 | `docs/item_notes/phase6.md` |
| CS-916 | `docs/item_notes/phase6.md` |
| CS-603 | `docs/item_notes/phase6.md` |
| CS-608 | `docs/item_notes/phase6.md` |
| CS-613 | `docs/item_notes/phase6.md` |

## Rules every leaf obeys

**Bodies are relocated VERBATIM.** They are not edited, summarised, trimmed or
re-ordered. A body therefore still reads as it did when it was written, including the
parts a later session measured false and corrected in place rather than rewriting. The
2026-08-25 split moved all 97 sections byte-for-byte and changed no body.

**ONE EXCEPTION TO VERBATIM, AND IT IS THE ONLY ONE.** The 2026-08-23 relocation
FALSIFIED every pointer that sent a reader to `docs/history_notes.md` for a block the
same relocation moved into this family - usually into the same section as the pointer
naming it. Those pointers were repointed at this family on 2026-08-23, as one mechanical
substitution over the whole derived population, and nothing else in any body was touched.
THE FIRST SWEEP OF THAT POPULATION WAS INCOMPLETE: it keyed on the block name
`<ITEM> - detail` and so walked straight past **CS-454 - status detail**, which is the
same defect in miniature - a population derived from the shape in front of you rather
than from the shape itself. A pointer that still names `docs/history_notes.md` names a
block that is genuinely still there.

**A pointer inside a body saying "this file" means the leaf that body sits in.** Every
one of those was measured before the 2026-08-25 split and every one is a self-reference
into its own section, so the split falsified none of them.

`docs/upstream_watch.md` owns the CS-486 upstream watch list, which is a standing watch
rather than per-item detail, and CS-486's section points at it.
