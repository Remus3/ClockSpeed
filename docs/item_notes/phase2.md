# Clockspeed - live per-item detail, phase 2 - data layer follow-ups

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the routing table over every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item ROADMAP.md files under its `Phase 2` heading.

**Bodies are relocated VERBATIM.** Every section below arrived from
`docs/item_notes.md` unedited when that file was split on 2026-08-25, and arrived
there from `ROADMAP.md` and `docs/history_notes.md` before that. A body therefore
still reads as it did when it was written, including the parts a later session
measured false and corrected in place rather than rewriting.

**When an item CLOSES its section moves to `docs/history_notes.md`**, not to another
leaf. That move is what keeps this file live.

---

## CS-210

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-210 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

this is the COMMON-MODE RISK named by the ADR 0006 adjudication on 2026-08-14. Both fences that ADR relies on read the SAME hand-authored corpus, so the registry-layer and solve-layer tests are one fixture read twice rather than two independent confirmations. That a registry-published `Building` can lack `mMaxPotential` AT ALL is asserted nowhere against the shipped data: the version pin records per-value counts (`"1.000000": 62`) but not WHICH entries carry the key, and ADR 0005 measured 62 entries carrying it while `clockspeed/data/registry.py:84-85` states 6 power-bearing entries carry no exponent - whether those sets overlap is unknown. It fails safe, because None cannot invent a number, so this is a premise risk rather than a correctness bug.

