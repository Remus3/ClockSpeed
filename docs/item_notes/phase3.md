# Clockspeed - live per-item detail, phase 3 - solver core follow-ups

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the routing table over every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item ROADMAP.md files under its `Phase 3` heading.

**Bodies are relocated VERBATIM.** Every section below arrived from
`docs/item_notes.md` unedited when that file was split on 2026-08-25, and arrived
there from `ROADMAP.md` and `docs/history_notes.md` before that. A body therefore
still reads as it did when it was written, including the parts a later session
measured false and corrected in place rather than rewriting.

**When an item CLOSES its section moves to `docs/history_notes.md`**, not to another
leaf. That move is what keeps this file live.

---

## CS-301

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: phase 3 deliberately refused to invent this. The semantics of `mVariablePowerConsumptionConstant` and `mVariablePowerConsumptionFactor` are unmeasured anywhere in this project - the registry only carries them - so `power.py` hands all four operands back verbatim and applies no law (non-negotiable 7). The two uncovered branches are stated honestly in that module rather than implied to be tested: no fixture building declares a base below the reference clock, and no fixture recipe names two producers.

## CS-303

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: raised by the ADR 0006 adjudication on 2026-08-14 as a roadmap candidate and explicitly NOT as a condition of that acceptance. Nothing mechanical currently stops a caller reading the field directly and clamping without going through `clamp_to_unsharded_base`; the ADR claims the name and the docstring as the fence and claims no more. Note that `tests/solve/test_synthetic.py::test_every_building_carries_the_unsharded_clock_base` reads the field directly by design and is one of the exemptions.

## CS-302

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: that diagnosis costs O(rows) extra exact solves and runs only on the refusal path. It was reasoned acceptable for optimizer-sized recipe sets and NOT measured at real scale, which is a stated limit rather than a claim.

