# 0022 - an item's acceptance lives in its item-notes section, with a pointer on the line

## Status

`accepted` - 2026-09-17

**ACCEPTED BY ADJUDICATOR RULING 2026-09-17**, on the CS-971 rebuild. The ruling was made by
an agent that did not perform the relocation, which is the condition `CLAUDE.md` section 5
puts on grading; the session that moved the clauses wrote this file and did not grade it.
ADR 0010 and ADR 0011 took the same route for the two splits before it.

This ADR is IN FORCE and binding. Cite it freely.

## Context

`ROADMAP.md` had been over its soft budget for many sessions - read the sizes and the
budget from `tools/doc_budget.py`, which prints both and says RELOCATE, DO NOT DELETE. The
detail that made the file large was the acceptance clause on each item line: clauses run to
paragraphs because they are the testable condition a verifier grades against.

**THE FIRST ATTEMPT CUT THE CLAUSES ON THE LINE, AND AN ADVERSARY REFUTED IT.** Each line
was truncated at a clause break and the remainder relocated verbatim. Nothing was deleted
and the relocation was proven byte-exact - and the result still changed what those items
REQUIRED, because the line is what a grader reads: CS-400's never-write proof fell off its
line, CS-499's ended mid-phrase, and line after line ended on a dangling word. The counts
are in that adversary's finding and in this item's ledger entry, cited to a rerunnable
measurement, rather than restated here. **A truncation and a
whole clause read identically once the rest is gone.** No guard could tell them apart
either, so the defect was invisible to the tree that shipped it.

**SPLITTING THE CLAUSE ACROSS TWO FILES IS THE SAME DEFECT WEARING A POINTER.** Half a
clause on the line and half in the note gives an item two owners, and the half a lane reads
is the half that decides whether the row closes.

**THE ALTERNATIVES, AND WHAT EACH COST.** Raising the budget was rejected on the fence ADR
0010 and ADR 0011 already recorded: a budget raised to fit the file it measures teaches
everyone what budgets are worth. Deleting detail is forbidden by the budget tool's own
instruction. Splitting `ROADMAP.md` into per-phase files was rejected because its phase
headings are the single owner of which phase an item belongs to and the lane reads ONE
queue file top to bottom (`tools/headless-queue.md` section 5), so a split would multiply
both.

**THE FORECLOSED PREMISE WAS WRITTEN DOWN, WHICH IS WHY THIS ADR EXISTS RATHER THAN A
RULE.** CS-1033 - the earlier item over the same budget - required in its own acceptance
that "the item LINE for each open item still carries its own acceptance so the roadmap
stays readable without following a pointer". That clause is the per-line arrangement stated
as a requirement, and it is exactly what the measurement above refutes. It is SUPERSEDED by
this decision rather than met; CS-1033 closes as delivered by CS-971 on its other four
clauses, and its record is the ledger entry.

## Decision

**An OPEN item's acceptance clause lives in that item's section under `docs/item_notes/`,
under a single `### Acceptance` heading, and that section is its SOLE owner.**

- **The line carries the literal pointer `acceptance: in detail`** plus the trailing
  `detail:` field that routes the item, so `ROADMAP.md` keeps the ID, a short headline, the
  pointer and the tier.
- **A WHOLE clause on the line is still well-formed. A PART of one never is.** An item may
  be filed with its clause inline; what is banned is the split, in either direction.
- **A headline too long for a readable line is cut to a COMPLETE short title**, and the
  original headline is filed whole in the same section under `### Full headline`. A title is
  never a sentence broken off part-way - that is the refuted shape at one remove.
- **`tools/drift_guard.py` guard (j) grades the ownership, and `tests/data/test_item_notes_index.py`
  grades the guard.** A pointer whose section carries no acceptance heading, two headings, an
  empty one, a clause on a line whose section carries a heading, and a line with neither a
  clause nor the pointer are each a FAIL.
- **A verifier and a lane worker grade a row against the section's clause**, which
  `tools/headless-queue.md` states at the three places it describes grading, the queue and
  the wrap.

## Consequences

**Easier.** `ROADMAP.md` is inside its budget with room to file into - read the figures from
`tools/doc_budget.py`. An acceptance clause has one owner, so amending it is one edit in one
place, and a grader reads the whole condition or fails a guard trying.

**Harder.** Reading what an item requires costs one hop through the leaf membership rule.
A reader who greps `ROADMAP.md` alone now sees the subject of an item and not its condition,
which is the price of the line staying short.

**Bodies written before this decision** say an item's line carries its acceptance. They are
verbatim-locked, and `docs/item_notes.md` repoints them en bloc rather than editing each; a
body that DEMANDS the clause be readable on the line is contradicted rather than repointed,
and is amended on the adjudicator route.

**A KNOWN GAP, STATED RATHER THAN IMPLIED.** Guard (j) grades WHERE the clause lives, never
that a relocated clause still equals the one the item was filed with. The byte-exactness of
this move was proven once, by a script, at the commit that made it; a later truncation
inside a section is not detectable by any guard in the tree. That is filed as its own row.

**Foreclosed.** Acceptance on the item line as the arrangement - per-line clauses, a clause
summarised on the line with the full text in the note, or any "readable without following a
pointer" requirement. CS-1033's clause was the last statement of that premise and it is
superseded here. Do not re-pitch it on readability grounds: the measurement above is what a
readable line cost, and it cost the meaning of the items it cut.

**Revisit if** the section family itself stops being the home of per-item detail, which is
ADR 0010's decision and not this one.
