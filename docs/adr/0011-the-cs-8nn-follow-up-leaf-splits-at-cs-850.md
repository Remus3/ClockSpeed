# 0011 - the `CS-8nn` follow-up leaf splits at CS-850

## Status

`proposed` - 2026-08-29

**FILED `proposed` DELIBERATELY, AND NOT AS AN OVERSIGHT.** It was written by the session
that performed the split, and `CLAUDE.md` section 5 says the agent that produced a thing
never grades it. It is not binding and nothing may cite it as settled until an adjudicator
that did not perform the split accepts it. ADR 0010 took the same route and was accepted
the same day by operator ruling; that is the route this one is waiting on, not a promise
about the outcome.

## Context

`docs/item_notes/phase4-followups.md` was created by the 2026-08-25 split recorded in
`docs/adr/0010-item-notes-is-an-index-over-per-phase-leaves.md`. It took the phase-4 items
whose ID sits in the `CS-8nn` follow-up block, and it carries the 128 KB budget every leaf
in the family carries.

**ADR 0010 PREDICTED THIS FILE FILLING AND SAID SO IN ITS OWN CONSEQUENCES.** It recorded
that newly filed items land overwhelmingly in the `CS-8nn` leaf, that 128 KB left roughly a
dozen more items' worth of detail at then-current sizes, and that closure is the only
designed shrink. Measured 2026-08-29, four sessions later: the leaf held 130138 bytes of a
131072-byte budget - 99 per cent, 934 bytes of headroom, about twelve lines - across 34
sections. Four items had been filed into it in the interval and none of the 34 had closed.

**The remedy the budget prescribes was exhausted again.** `tools/doc_budget.py` says
RELOCATE, DO NOT DELETE, and a closing item's section relocates to `docs/history_notes.md`.
Session 45 had already moved everything that closed. There was nothing left to move.

**Raising the budget was rejected for the reason ADR 0010 already recorded** - `ROADMAP.md`
is the worked example of what a budget raised to fit the file it measures teaches everyone
to do with budgets. That fence stands; it is cited here rather than re-argued.

**WHERE THE SEAM GOES WAS MEASURED, NOT ARGUED.** Cutting the 34 sections at each candidate
ID gives the shape below. The percentages are of the 128 KB leaf budget and are modelled on
the pre-split preamble, so they compare the candidates against each other rather than
predicting either final file exactly.

| Seam | Below the seam | Of budget | At or above | Of budget |
|---|---|---|---|---|
| CS-830 | 13 sections | 33 per cent | 21 sections | 67 per cent |
| CS-840 | 15 sections | 36 per cent | 19 sections | 64 per cent |
| CS-845 | 20 sections | 47 per cent | 14 sections | 54 per cent |
| CS-850 | 24 sections | 56 per cent | 10 sections | 44 per cent |
| CS-855 | 29 sections | 82 per cent | 5 sections | 19 per cent |

**BALANCE ALONE WOULD PICK CS-845, AND BALANCE ALONE IS THE WRONG CRITERION.** The two
halves are not symmetric in what happens to them next. A newly filed item takes the next ID
after the highest already allocated - CS-860 at the time of the split - so every future
filing lands ABOVE the seam, and the half below it can only shrink, by closure. Headroom is
therefore worth more above the seam than below it.

CS-850 is the first candidate at which the half that grows is the emptier one. CS-830 and
CS-840 invert exactly the property that matters, leaving the growing half carrying two
thirds of the content and the static half nearly empty. CS-855 overcorrects: it returns the
lower half to 82 per cent, which is a leaf that would need splitting again without ever
having grown. CS-845 is the most balanced by bytes and still puts the larger share on the
side that only shrinks.

**CS-850 also needs no new judgement to apply.** A round decade inside a decimal ID block
keeps membership computable from an ID alone, exactly as the `CS-8nn` seam above it is.
That property is what lets the routing rule stay a derivation instead of becoming a table
of which item lives where.

**THE REJECTED OPTION THAT COSTS THE MOST TO RE-PROPOSE IS THE SYMMETRIC RENAME.** Naming
the two halves `phase4-followups-800.md` and `phase4-followups-850.md` reads better, and it
was rejected on a measurement rather than on taste. **Measured at the base commit, before
this split landed:** the name `phase4-followups.md` was spelled FOURTEEN times across the
three docs that route a reader to per-item detail - nine in the two guarded ones, six in
`WAKEUP_NOTES.md` and three in `docs/LEDGER.md`, and five in `docs/history_notes.md`, the
recorded-unguarded deep archive. **Twelve spell the full path and two spell the bare
filename, and a rename kills both spellings**, so fourteen is the figure the rename is
priced against. It kills them as PATHS - the citation stops resolving at all. The present
tense would be wrong here and the past tense is deliberate: seven of the fourteen were
repointed by this split, for the reason the next paragraph gives.

**THE SPLIT BROKE SOMETHING SMALLER AND DIFFERENT, AND THE RULING ON IT IS REPOINT.**
Keeping the name left every path resolving, so nothing went dead. What it did leave was
SEVEN pointers whose PATH still resolves while naming the wrong leaf for the item they
cite - two in `docs/LEDGER.md`, three in `WAKEUP_NOTES.md` and two in
`docs/history_notes.md`, each sending a reader after a `CS-8nn` item at or above the
seam. **Only the two in `docs/LEDGER.md` were known before the split ran. The other five
were found afterwards, by reading**, and the count reached five in three steps because
each re-measurement found one the previous prose summary had mis-classified - which is
itself the evidence for the blind spot recorded in Consequences. The session-46 ruling
is that those
are repointed, following session 44's precedent of repointing a destination rather than
renumbering and leaving the drift visible in the text. **A pointer that routes a reader
to the wrong leaf is a defect wherever it lives**, and the fact that no guard can see it
is not a licence. What is NOT rewritten is the surrounding sentence's claims about what
that session did: the destination moves, the record of what was read does not.

**That is the measure of the two options rather than an argument against repointing.**
The asymmetry cost seven repointed destinations and one sentence in each leaf header. The
symmetry would have cost fourteen dead paths, several of them inside historical sentences
that no repoint can repair, because they record where a past session actually read a
block from. Do not re-propose the rename on the grounds that the names look uneven - the
unevenness is the receipt.

## Decision

**The `CS-8nn` follow-up block splits at CS-850, and phase 4 is three leaves.**

- **`docs/item_notes/phase4-followups.md` holds CS-800 through CS-849**, and
  **`docs/item_notes/phase4-followups-850.md` holds CS-850 through CS-899.**
- **The existing leaf keeps its name**, and the new one takes the suffix, because the new
  file is the one with no pointer to break. The seam number is in the name that had a free
  choice.
- **EACH LEAF STATES ITS OWN RANGE IN ITS HEADER, UNMISSABLY, because one filename does not
  say its range and the other says only where it starts.** That sentence is the whole
  remedy for the ambiguity the asymmetry buys, so it is part of the decision rather than a
  courtesy. A reader who trusts the filename over the header or the routing table will be
  wrong about half the block.
- **The membership rule stays a DERIVATION from the item number, and its ONE CODE OWNER
  is `tests/data/test_item_notes_index.py`.** That module grades every section in the
  family against the leaf the rule names, and it is the only place in the tree where the
  ID-to-leaf mapping is expressed. The seam is one constant there and the leaf's filename
  is spelled FROM that constant rather than typed beside it, so the number and the name
  have no way to disagree. **Do not add a second expression of this mapping anywhere** - a
  hand-listed table of which item lives where would be edited by the same hand that
  misplaces a body, and would therefore agree with the mistake.
- **Every section moved byte-for-byte, and it was proven rather than asserted.** The
  multiset of per-section SHA-256 digests taken before the split equals the multiset taken
  across both files after it, 34 sections to 34 sections. No body was reflowed, retitled,
  renumbered or tidied.
- **Nothing else in the family changed, because nothing else needed to.** The index guard
  in `tools/drift_guard.py`, the budget tool in `tools/doc_budget.py` and the
  documentation-citation module `tests/test_docs_citations.py` all DERIVE the leaf
  population by globbing `docs/item_notes/`, so the new leaf joined all three with no
  edit to any of them. That was ADR 0010's stated design paying out, and it is the reason
  this split touched a routing table and a rule rather than a topology.
- **This ADR is itself GUARDED, for the reason ADR 0008 and ADR 0010 are.** It names test
  modules, which makes it a citation carrier, and an ADR is written once and read for
  years - so a pointer that rots in one rots unobserved. It is listed in `GUARDED_DOCS`
  in `tests/test_docs_citations.py`. Citing the owner precisely and then guarding the
  citation is the whole point; an ADR about a mapping with one owner that declines to
  NAME that owner would be self-defeating.

## Consequences

**Easier.** Measured after the split, both leaves sit near half their budget - the lower at
57 per cent and the upper at 45 per cent - against 99 per cent for the single file. The
upper leaf, which is the one that grows, holds the larger share of the remaining headroom.
A session reading `CS-8nn` detail now loads roughly half of what it did.

**Harder.** A reader must know the seam. One leaf's filename does not state its range, so
finding an item costs reading its number against CS-850, or one hop through the routing
table in `docs/item_notes.md`. A grep across the follow-up block now spans two files rather
than one.

**A NEW BLIND SPOT, STATED BECAUSE NOTHING MACHINE-CHECKS IT.** Splitting a leaf while
keeping its name creates a pointer that is WRONG WITHOUT BEING DEAD: the path resolves,
so `tests/test_docs_citations.py` is green, while the leaf it names no longer holds the
item the sentence is about. Seven such pointers existed the moment the split landed, and
five of the seven were found by reading rather than by a guard. Any future split of a
leaf that keeps its name must sweep every doc for `under CS-nnn` pointers BY HAND, and
must enumerate them rather than summarise them - three successive prose counts of this
very population were wrong, each in a different way, and each was caught only by listing
the mentions with their line numbers instead of describing them.

**The final distribution, enumerated rather than counted.** Of the fourteen base-commit
mentions of the name, seven now name the suffixed leaf and seven still name the
unsuffixed one - and all seven of the latter are correct as written: three are budget
observations about the file itself, two are relocation provenance recording where a past
session cut a block FROM, and two discuss the CS-492 disposition constant, whose block
sits in CS-807 and stayed below the seam. This is the standing cost of the naming
decision above, and it is the honest half of the receipt.

**Foreclosed.** Renaming `docs/item_notes/phase4-followups.md` to gain a symmetric pair.
The measurement above is the fence, and it gets stronger with every session that spells the
current name.

**THE LIMIT, STATED RATHER THAN LEFT TO BE DISCOVERED, AND IT IS THE SAME LIMIT ADR 0010
STATED.** This split divides a population; it does not shrink it. **CLOSURE IS STILL THE
ONLY DESIGNED SHRINK.** ADR 0010 wrote that sentence about the split before this one, and
four sessions later this file existed anyway - so the sentence is repeated here as evidence
that stating the limit did not prevent it, rather than as a claim that stating it twice
will. A `CS-8nn` leaf at 99 per cent of budget with nothing closed is the shape to expect
again.

**Revisit if** the upper leaf fills the same way, which is the same decision one level down
and needs no new topology; or if `CS-8nn` reaches CS-900. The second is a `ROADMAP.md`
ID-block question rather than a doc-topology one, it is what created `CS-8nn` in the first
place, and it should not be answered by this ADR.
