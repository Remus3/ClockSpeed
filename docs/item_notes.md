# Clockspeed - live per-item detail, index

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This file owns the INDEX and the family rules. The per-item bodies live in the
leaves under `docs/item_notes/`.** One leaf per phase, one section per item ID inside
it. A block in a leaf is a LIVE INSTRUCTION: read an item's section BEFORE taking that
item, and use the leaf membership rule below to find which leaf holds it.

`ROADMAP.md` owns the item LINE and nothing else - the ID, the headline, the acceptance
criterion and the tier. Its lines point at THIS file rather than at a leaf, deliberately:
ROADMAP's own phase headings are the single owner of which phase an item belongs to, and
repeating that mapping on every item line would be a restated fact with somewhere to
drift to. One hop through the leaf table below is the cost of keeping one owner.

**This family NEVER contains:** the item line itself, a per-item routing row, a completion record
(`docs/LEDGER.md` owns those), an aspirational item (`BACKLOG.md` owns those), the
external condition blocking a gated item (`docs/GATED.md` owns that), or history.
**When an item CLOSES its section moves to `docs/history_notes.md`**, because at that
point it IS history - that move is what keeps these files live and that file's header
true. A closing item's section does NOT move to another leaf.

**THIS FILE HOLDS NO ITEM BODIES.** It carries no `## CS-nnn` section and never will;
that is asserted by `tools/drift_guard.py` guard (j), not merely intended. A body
written here instead of in its leaf is invisible to every reader who follows the rule.

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
| `docs/item_notes/leaf-membership-rule.md` | ANNEX, not a phase leaf - the seam reasoning behind the leaf membership rule in this table, relocated there by CS-1062. A declared departure on the same grounds as the two rows above: it is routing DOCTRINE rather than an item body |

**This table is the single hop, and it is the leaf membership rule.** It moved back here
VERBATIM from `docs/item_notes/leaf-membership-rule.md` when CS-1112 removed the per-item
routing rows, and only the annex's own row was reworded, because it had called the annex
the rule itself; the reasoning behind each seam stayed in that annex. An item is ROUTED when
its `ROADMAP.md` line's LAST field is a `detail:` field, and its leaf is the row above
whose phase and ID range hold it - no per-item row exists, and none may be added.

`tools/drift_guard.py` guard (j) grades that derivation rather than trusting it: a routed
item with no section in its derived leaf, a section no `detail:` field routes, a
`| CS-nnn |` routing row in this file, a leaf file no row names, and any disagreement
between this table and the rule's code owner at a seam are each a FAIL. A family holding
NO routed item and NO section is a WARN carrying a skip record, not a pass - every
equality here is satisfied for free by an empty population.

## Rules every leaf obeys

**Bodies are relocated VERBATIM.** They are not edited, summarised, trimmed or
re-ordered. A body therefore still reads as it did when it was written, including the
parts a later session measured false and corrected in place rather than rewriting. The
2026-08-25 split moved all 97 sections byte-for-byte and changed no body.

**ONE EXCEPTION TO VERBATIM EXISTS AND IT IS THE ONLY ONE** - the 2026-08-23
repointing of pointers this family's own relocation falsified, including the sweep that
missed `CS-454 - status detail`. Relocated to `docs/history_notes.md` 2026-09-14 under
its own heading; it is a record of one mechanical substitution, not a live rule. **A
pointer that still names `docs/history_notes.md` names a block genuinely still there.**

**A WRITE-LIST NAMES A FILE IT WILL CREATE BY DIRECTORY AND STEM, NEVER AS A PATH.** An
unbuilt path is a dead citation to `tests/test_docs_citations.py`, whose only routes are
ratcheted budgets.

**A pointer inside a body saying "this file" means the leaf that body sits in.** Every
one of those was measured before the 2026-08-25 split and every one is a self-reference
into its own section, so the split falsified none of them.

`docs/upstream_watch.md` owns the CS-486 upstream watch list, which is a standing watch
rather than per-item detail, and CS-486's section points at it.
