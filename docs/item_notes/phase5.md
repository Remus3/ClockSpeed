# Clockspeed - live per-item detail, phase 5 - advisor and audit

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the routing table over every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item ROADMAP.md files under its `Phase 5` heading.

**Bodies are relocated VERBATIM.** Every section below arrived from
`docs/item_notes.md` unedited when that file was split on 2026-08-25, and arrived
there from `ROADMAP.md` and `docs/history_notes.md` before that. A body therefore
still reads as it did when it was written, including the parts a later session
measured false and corrected in place rather than rewriting.

**When an item CLOSES its section moves to `docs/history_notes.md`**, not to another
leaf. That move is what keeps this file live.

---

## CS-500

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**UNBLOCKED 2026-08-23 BY AN OPERATOR RULING that supersedes their own ruling of 2026-08-15: PHASE 5 OPENS.** **DECODE CORRECTNESS IS NOT THEREBY SETTLED**, and reading this line as saying so is the error it is worded to prevent: it is tracked by CS-825, CS-826, CS-426, CS-432, CS-459 and CS-479, of which **CS-826 carries the population pillar 3 actually reads** - inventory counts and clock speeds. Detail, including the 2026-08-15 reason that still governs WHAT this gate needs and the clause moved here from CS-401, is in this file under **CS-500 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

**THE 2026-08-15 RULING AND WHY IT WAS SUPERSEDED.** The operator ruled on 2026-08-15 that phase
5 does not open until a real record's properties can be READ. They can be, and have been since
session 7. What had quietly become the blocker was decode CORRECTNESS, which is a different
claim from readability, and the operator was asked to weigh that difference on 2026-08-23 and
ruled that phase 5 opens now.

**THE 2026-08-15 REASON STILL GOVERNS WHAT THIS GATE NEEDS, rather than when it starts.** Pillars
3 and 4 are IN this gate, and pillar 3 needs inventory, clock speed and connection state, all
three of which live in the payload CS-413 measured before it closed on 2026-08-23. A rule written against a field no reader
populates is still the failure to avoid; what changed is that a reader populates them.

**CORRECTION 2026-08-23, SAME DAY, TO THE SENTENCE THIS PARAGRAPH USED TO CARRY.** It said
CS-413's second acceptance clause - the object data section walking to its exact final byte -
was UNMET, and that the walk is terminator-exact rather than boundary-exact. **THAT IS FALSE
AND THE BLAME FOR IT WAS ALSO MISPLACED, WHICH IS THE MORE USEFUL HALF.** A first version of
this correction said the sentence came from an adversary report and was never checked. It came
from THIS MODULE. `clockspeed/save/objects.py` SAID at the top of the file that the walk was
terminator-exact and not boundary-exact, without saying WHICH walk, in a module containing
two. The adversary quoted it accurately and the author then blamed the adversary. **THE ROOT
CAUSE WAS THAT UNQUALIFIED SENTENCE**, which misled two independent readers before it was
fixed. **IT IS FIXED NOW**, in the same change as this block - that module and
`tests/save/test_properties.py` now name which walk at every site a sweep could find, so do
not go looking for it. Measured:
`tests/save/test_objects.py::test_every_real_save_of_a_measured_pair_walks_to_the_end_of_its_body`
passes against the real library, and asserts in terms that every real save walks its framing
to the final byte with nothing left over. **THE BODY WALK IS BOUNDARY-EXACT.** What IS
terminator-exact is the PROPERTY walk INSIDE a payload - the trailing run - which is a
different region, is not clause 2, and is filed as its own item.

**ALSO CARRIES A CLAUSE MOVED HERE FROM CS-401**, which could not satisfy it in phase 4 because
`clockspeed/advisor/ledger.py` does not exist yet: the ledger treats a world token it has never
seen as a new world rather than failing.

