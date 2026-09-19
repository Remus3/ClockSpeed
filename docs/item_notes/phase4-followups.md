# Clockspeed - live per-item detail, phase 4 - save reader, CS-800 to CS-849

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**THIS LEAF HOLDS CS-800 THROUGH CS-849 AND NOTHING ELSE.** Its sibling
`docs/item_notes/phase4-followups-850.md` holds CS-850 through CS-899. **THE TWO NAMES
ARE NOT SYMMETRIC AND THIS ONE DOES NOT SPELL ITS RANGE**, so trust this sentence and the
leaf membership rule in `docs/item_notes.md`, never the filename: an ID at or above CS-850 is in
the sibling and is not here. The unsuffixed name was kept deliberately - pointers in
`WAKEUP_NOTES.md` and `docs/LEDGER.md` already spell it, and renaming to gain a symmetric
pair would have killed every one of them to buy nothing a sentence cannot buy.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the leaf membership rule routing every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item ROADMAP.md files under its `Phase 4` heading whose ID is in
the `CS-8nn` block and BELOW CS-850. That block exists because `CS-4nn` filled up at 98 of 100;
an ID still says which phase it came from. Operator decision 2026-08-21. The CS-850 seam
inside the block, and why it sits there rather than at CS-830 or CS-840, is recorded in
`docs/adr/0011-the-cs-8nn-follow-up-leaf-splits-at-cs-850.md`.

**NEWLY FILED WORK DOES NOT LAND HERE.** A new CS-8nn item takes the next ID after the
highest already allocated, which is above CS-850, so it lands in the sibling. The only
designed change to this file is a section LEAVING it when its item closes.

**Bodies are relocated VERBATIM.** Every section below arrived from
`docs/item_notes.md` unedited when that file was split on 2026-08-25, and arrived
there from `ROADMAP.md` and `docs/history_notes.md` before that. A body therefore
still reads as it did when it was written, including the parts a later session
measured false and corrected in place rather than rewriting.

**When an item CLOSES its section moves to `docs/history_notes.md`**, not to another
leaf. That move is what keeps this file live.

---

## CS-828

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-23 as a residual of CS-413's close, which would otherwise have ORPHANED it. **SCOPED TO THREE PAIRS ON PURPOSE AND THE FOURTH IS NOT AN OVERSIGHT:** (14,60) is a MEASURED pair but reaches a property terminator on NO payload, so this region is undefined there; that half is GATED as CS-G05 and `docs/GATED.md` rules that filing both as one item would hide a blocked half behind a workable one. A first draft of this line did exactly that. **This is NOT a defect in the body walk**, which is boundary-exact. Detail in this file under **CS-828 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-23 as a residual of CS-413's close; the item stays OPEN in `ROADMAP.md`. This
block is a LIVE instruction, not history.

**THIS REGION WAS ASSIGNED TO CS-413 BY `docs/GATED.md` AND WOULD HAVE BEEN ORPHANED BY ITS
CLOSE.** That file rules that the save-60 half of the payload question is gated and moves to
CS-G05, while the variable trailing run **on the other three pairs** is a grammar question that
more saves will not fix. CS-413 closed on its three acceptance clauses, none of which is this,
so filing it here is what keeps that ruling true. **THE POINTER IN `docs/GATED.md` IS UPDATED
IN THE SAME CHANGE**, which is why this block paraphrases it rather than quoting it - a first
draft quoted the pre-edit wording verbatim and the quotation was dead on arrival.

**WHAT IS MEASURED, and it is recorded in shipped data rather than here** - the `trailing_run`
entry of `UNMEASURED_PAYLOAD_REGIONS` in `clockspeed/save/objects.py` owns the figures. In
words, and with no figure restated here because the module owns them: the run sits between a
payload's property terminator and its declared final byte; on the THREE pairs this item covers
it is universal, a small fixed floor holds, and above that the width varies widely.
**DO NOT WRITE 'EVERY PAYLOAD IN THE LIBRARY'** - a draft of this block did, and it is false:
the (14,60) pair reaches a terminator on NO payload, so it has no trailing run to speak of, and
it is scoped OUT of this item and stays in CS-G05.

**WHY THIS DOES NOT MAKE CS-413's CLAUSE 2 FALSE, because the two are easy to confuse and one
draft of this project's notes already did.** The BODY walk is boundary-exact: every real save
walks its framing to the final byte with nothing left over, because payloads are stepped over
by their declared length. The PROPERTY walk inside a payload is terminator-exact: it stops at
the terminator and the declared length carries it the rest of the way. This item is the second
one. Do not restate it as a defect in the body walk.

**DO NOT close this by widening the declared-length step.** Stepping over a region is what
makes the body walk exact today; the question is what the region CONTAINS, and a step is not a
reading.

### Partial ship recorded 2026-09-14 - the lead field reads, the remainder does not

**THE ITEM STAYS OPEN AND ITS ACCEPTANCE IS UNCHANGED.** The clause asks for the run's
contents on EVERY payload of the three pairs. What shipped reads the field the run OPENS
with on every payload of those pairs, and nothing past it. That is a narrowing, not a
close, and `docs/LEDGER.md` records it as a measurement rather than a closure.

**WHAT IS NOW READ.** `clockspeed/save/objects.read_trailing_run` decodes the int32 at the
run's first byte and reports it on `PropertyResult.trailing_run`, with everything past it
carried as `TrailingRun.unread`. The old sentence in `UNMEASURED_PAYLOAD_REGIONS` - that
whether the 4-byte floor is one field or the head of a longer structure is not claimed,
and that no reading of the interior is offered - is answered for the payloads whose run IS
that field, and `tests/save/test_trailing_run.py` holds the entry against the reading so
the two cannot drift apart.

**THE FLOOR'S VALUE IS READ. ITS PRESENCE IS STILL ARITHMETIC, AND SAYING SO IS THE WHOLE
POINT OF THIS PARAGRAPH.** A first draft of this block claimed the floor was no longer
arithmetic at all, and a verifier refuted it on the day it was written. What is true:
`read_trailing_run` returns a lead exactly when the run is at least `TRAILING_RUN_LEAD_BYTES`
wide, and that width is still `declared_end - terminator_end`. So the field's VALUE is
decoded from the bytes and its PRESENCE is the subtraction the clause names. **DO NOT READ
THIS ITEM AS HALF-ARITHMETIC-FREE** - the arithmetic half is exactly what is left open.

**WHAT IS GENUINELY STRONGER THAN BEFORE** is that the denominator the library arms grade
against is taken from the WALK - a payload that did not raise the unparsed-payload warning
- and not from the reader, so a reader that declined a whole class cannot shrink numerator
and denominator together. That is a property of the TEST, not of the reading, and it is
what makes the measurement above worth anything.

**WHAT REMAINS, AND WHY IT IS A SEPARATE ROW RATHER THAN THE REST OF THIS ONE.** The
remainder is class-keyed rather than pair-keyed: one class writes a count prefix and that
many records, another writes length-prefixed reference strings, another writes neither. It
is CS-1068, and its note carries the fence that matters - a partition of the remainder
that sums to the declared end closes by arithmetic and cannot fail, which is the defect
that refuted CS-830 after it had merged.

**DO NOT CLOSE THIS ITEM ON THE STRENGTH OF THE LEAD FIELD.** The clause says every
payload and it means the whole run. Reading four bytes of it universally is progress on
the clause and is not the clause. If a later session wants the item to close on a narrower
population than it names, that is a re-wording and needs its own record - not a reading of
this block.

### Second partial ship recorded 2026-09-16 - the reference-pair class reads, two shapes remain

**THE ITEM STAYS OPEN AND ITS ACCEPTANCE IS UNCHANGED.** This is the third reading of the
run and the second one recorded here as a measurement rather than a closure. What shipped
reads the remainder of ONE further derived class set - the one whose remainder is TWO
OBJECT REFERENCES - and nothing else.

**WHAT IS NOW READ.** `clockspeed/save/objects.read_reference_pair` walks four
length-prefixed strings as two references and reports them on `TrailingRun.references`,
with `unread` falling by the width they consumed.
`derive_reference_pair_classes` picks the carrying classes off the body being read.

**THE PROSE CS-1068 LEFT BEHIND WAS MEASURED AND IS HALF FALSE, AND THAT IS THE MOST
REUSABLE THING THIS CYCLE PRODUCED.** Its ledger entry describes this shape as two
references "followed by a 24-byte tail". Across this project's library the tail is present
on ONE schema and ABSENT on two others, which write the same two references and stop. The
partition is exact, with no payload on either side crossing over, and it is corroborated
by a second signal from a different source: every tail-bearing record lacks the two
wire-geometry properties and every tail-free record carries them - the newer schema moved
that geometry out of the run and into properties. **A READER BUILT FROM THAT SENTENCE
WOULD HAVE OVER-READ EVERY TAIL-FREE PAYLOAD BY THE WIDTH `REFERENCE_PAIR_TAIL_BYTES`
NAMES** - the figure lives in `clockspeed/save/objects.py` and is not restated here. Do
not take a prose
description of a region in this tree as a specification for a reader; re-measure it.

**SO THE FORM IS DERIVED, NOT TRANSCRIBED, AND NOT VERSION-KEYED EITHER.** A class is
admitted only when EVERY one of its remainder-bearing records in that body reads at the
SAME tail width. That consistency requirement is the anti-vacuity property: a reader
taking each record at whichever width happened to fit would admit any mixture, which is
arithmetic wearing a derivation's clothes. A version table would have worked on today's
library and would have been a transcription, which CS-829's note forbids by name.

**THE WEAKEST CASE, STATED RATHER THAN ROUNDED UP, because an adversary found it and a
caveat said in a cycle report is not a caveat in the artifact.** The consistency
requirement contributes NOTHING when a class has exactly ONE remainder-bearing record in
the body: one record agrees with itself, and the class is admitted at whichever of the two
widths that record read at. The READING is still not vacuous there - the four prefixes must
walk exactly onto the derived landing point and empty strings are refused, so a run that is
not a pair still derives nothing - but the FORM, at n=1, is as good as observed. On this
project's library the carrier's n is in the thousands, so nothing shipped rests on it. A
later cycle strengthening this should require a floor on n rather than re-deriving the
consistency rule, which already holds.

**WHAT REMAINS, AND IT IS CS-1119 RATHER THAN THE REST OF THIS ONE.** Two shapes, neither
reachable by this grammar. The first is a four-byte all-zero residual that is
BYTE-IDENTICAL to an empty item list - CS-1068's root cause seen from the other side, and
the reason it cannot be closed by trying harder. The second is one class whose remainder
is a large nested structure that nothing in the run describes.

**DO NOT CLOSE THIS ITEM ON THE STRENGTH OF THE REFERENCE PAIR.** The same sentence as the
block above, for the same reason. The clause says every payload of the three pairs.

### Third partial ship recorded 2026-09-19 - the proof instrument was grading a reader nobody ships

**THE ITEM STAYS OPEN AND ITS ACCEPTANCE IS UNCHANGED.** Nothing new is read out of
the run this cycle. What changed is the instrument the clause names as its proof:
`tests/save/test_trailing_run.py`'s library sweep swept with BOTH shipped remainder
readings switched off, so every figure it published about the open region was a
claim about a reader configuration no consumer of `clockspeed/save/objects.py` uses.

**THE DEFECT, and it is a seam defect rather than a reading one.** The item-list
reading and the reference-pair reading are each GATED on a vocabulary the caller
passes to `read_properties` - `item_list_classes` and `reference_pair_classes` - and
both parameters DEFAULT TO EMPTY. That default is correct for the module (a caller
with no derived vocabulary must not have remainders read for it) and it is exactly
what made the omission silent: the sweep called `read_properties` with neither, got
a reader that declines every remainder, and counted each one as `unread`. No arm
could catch it, because every arm in the module read its numbers from that same
sweep. **A DEFAULT THAT MEANS "READ LESS" IS INVISIBLE TO A TEST THAT MEASURES ONLY
WHAT WAS READ.**

**THE DIRECTION OF THE ERROR MATTERS AND IS RECORDED RATHER THAN THE FIGURES.** The
sweep OVERSTATED the open region on every one of the three pairs, and by a wide
margin on one of them - so the two partial ships recorded above were, on this
instrument, invisible. The counts themselves are deliberately not written here: they
move with the operator's library and `tests/save/test_trailing_run.py` is their only
owner, which is the rule `CLAUDE.md` section 4 states.

**WHAT NOW HOLDS IT SHUT.** `_run_of_record` takes both vocabularies as REQUIRED
keywords with no default, `_sweep_trailing_runs` derives both off each body it walks
- never transcribed, never carried between saves - and `_RunSweep.read_by_derivation`
counts the payloads whose remainder a derivation read.
`test_the_sweep_reads_the_remainder_with_the_derived_vocabularies` requires that
count non-zero on every pair this item covers, and it is not a tautology of the
branch feeding it: `items` and `references` are two fields `read_trailing_run` never
sets, so nothing in the lead-field path can satisfy it.

**DO NOT READ THIS AS PROGRESS ON THE CLAUSE.** The clause asks for the run's
contents, and no byte is read this cycle that was not read before it. What is true is
that the population the clause leaves open is now REPORTED at its real size instead of
a larger one. A later session that finds the remaining figure smaller than the earlier
entries imply is reading a corrected instrument, not a regression.

**WHAT THE CORRECTED INSTRUMENT SAYS IS LEFT, re-derived this cycle and NOT taken from
any filed line.** The remainder past the lead falls into two shapes, and `CS-1119`
owns reading both. Its filed headline calls the second one "one class"; measured on
the three pairs this item covers, it is carried by TEN classes, and over every
measured layout by eleven. That is a correction to a filed characterisation and it is
filed rather than applied here, because the row that owns the reading owns the
sentence describing it.

### Fourth partial ship recorded 2026-09-19 - the zero-valued residual reads, the nested structure does not

**THE ITEM STAYS OPEN AND ITS ACCEPTANCE IS UNCHANGED.** This is the fourth reading of
the run and the third recorded here as a measurement rather than a closure. What shipped
reads the remainder shape that carried the LARGE MAJORITY of what the corrected
instrument reported open, and nothing else.

**WHAT IS NOW READ.** `clockspeed/save/objects.read_zero_remainder` reads a remainder
that is exactly `ZERO_REMAINDER_BYTES` wide and carries `ZERO_REMAINDER_VALUE`, and
reports it on `TrailingRun.zero_remainder` with `unread` falling to zero.
`derive_zero_remainder_classes` picks the carrying classes off the body being read.
The figures move with the operator library and `tests/save/test_trailing_run.py` is
their only owner, so none is written here.

**THE WIDTH IS WHAT KEEPS THIS OFF THE CS-830 DEFECT, AND A FIRST DRAFT OF THIS BLOCK
SAID IT WAS THE VALUE.** The cycle's verifier measured that draft false and it is
corrected rather than quietly dropped. The CS-830 defect is a width taken FROM the
observation, which closes on every payload and cannot fail. This width is the shipped
constant `ZERO_REMAINDER_BYTES`, so every residual of another width is REFUSED - and
residuals of many other widths are exactly what remains open on all three pairs.
`tests/save/test_zero_remainder.py` holds it through the stretched-end arm CS-828's
clause names.

**THE WEAKEST CASE, STATED RATHER THAN ROUNDED UP.** The verifier re-derived the
vocabulary over every body of the library with the VALUE condition deleted and admitted
exactly the same classes. On this corpus that condition refuses no real record and is
exercised only by the synthetic arms. It is kept because the shape it names is a claim
about the bytes and a non-zero int32 at the same width is a different region - and
`derive_zero_remainder_classes` carries it, so a class disagreeing on width OR on value
derives nothing. **DO NOT CITE THE VALUE CONDITION AS THE ANTI-ARITHMETIC PROPERTY.**

**WHAT THIS READING DOES NOT CLAIM, AND THE DISCLAIMER IS LOAD-BEARING RATHER THAN
MODEST.** Four zero bytes are BYTE-IDENTICAL to an empty count-prefixed item list.
Nothing shipped here says which the region IS, and no reading of the run can: that is
CS-1068's root cause seen from the other side and CS-1119 owns it. What is read is the
VALUE at a derived landing point, exactly as the lead field is. **DO NOT LATER READ
`TrailingRun.zero_remainder` AS A CLAIM THAT THE CLASS CARRIES AN EMPTY LIST** - the
field name says zero, not empty, for that reason.

**WHAT REMAINS, AND IT IS STILL CS-1119.** One shape: a remainder that is a large nested
structure nothing in the run describes. It is what the residual population on all three
pairs is now made of. The correction the block above filed is CS-1148 and it still
stands - CS-1119's filed headline calls that shape ONE class and it is carried by more -
and the shipped `UNMEASURED_PAYLOAD_REGIONS` entry now says so too rather than repeating
the false characterisation.

**WHAT THIS DOES TO CS-1119, SHARPENED BY THE VERIFIER BECAUSE THE SOFTER WORDING WAS THE
MISLEADING ONE.** That row's ACCEPTANCE is satisfied by EITHER shape being read, and
every element of it is met by this change: the width is a shipped constant, the carriers
are derived off the body, the library test reports counts only, and the
moved-declared-end refusal arm exists. What is NOT met is that row's HEADLINE framing -
whether the zero-valued residual IS an empty item list or a class carrying no list at all
is undecided and undecidable from the run. **THE ROW IS LEFT OPEN RATHER THAN CLOSED FROM
HERE**, because one row per cycle means a row this cycle did not claim is not one it may
close. The cycle that takes CS-1119 should read this block first.

**DO NOT CLOSE THIS ITEM ON THE STRENGTH OF THE ZERO REMAINDER.** The same sentence as
the three blocks above, for the same reason. The clause says every payload of the three
pairs, and a residual population survives on every one of them.

### Fifth partial ship recorded 2026-09-19 - the count-prefixed reference list reads, the chain does not

**THE ITEM STAYS OPEN AND ITS ACCEPTANCE IS UNCHANGED.** This is the fifth
reading of the run and the fourth recorded here as a measurement rather than a
closure. What shipped reads one further derived class set - the one whose
remainder is a COUNT followed by that many object references - and nothing else.

**WHAT IS NOW READ.** `clockspeed/save/objects.read_reference_list` reads the
int32 count the remainder opens with and walks that many entries, each an
optional fixed-width scalar followed by two length-prefixed strings, and reports
them on `TrailingRun.reference_list` with `unread` falling to zero.
`derive_reference_list_classes` picks the carrying classes off the body being
read and answers the FORM with them. The figures move with the operator library
and `tests/save/test_trailing_run.py` is their only owner, so none is written
here.

**THE PER-ENTRY SCALAR IS NOT AN UNCONDITIONAL FIELD, WHICH IS THE SAME LESSON
THE REFERENCE PAIR'S TAIL TAUGHT AND IS RESTATED BECAUSE IT WAS RE-MEASURED
RATHER THAN ASSUMED.** Measured over this library one carrying class writes a
scalar ahead of every reference and two write the reference alone. A reader
built on either form alone would refuse every body of the other, and one built
on `declared_end - terminator_end` would read both and could not fail - the
CS-830 defect. Every width this reader consumes comes from the count, from a
string's own length prefix, or from `REFERENCE_LIST_ENTRY_PREFIX_WIDTHS`.

**AMBIGUITY IS DECLINED RATHER THAN RESOLVED BY ORDER, AND THIS READER CANNOT
MAKE THE CLAIM `read_reference_pair` MAKES.** That reader can argue at most one
tail width reaches the declared end, because its string walk is fixed and only
the tail moves. Here the two forms begin their walks at DIFFERENT offsets, so
nothing structural forbids both landing, and taking the first would make the
answer a property of the order the widths happen to be listed in.
`_reference_list_form_of` therefore returns nothing when more than one width
reads, and `tests/save/test_reference_list.py` holds it against a run
CONSTRUCTED to read at both - the shipped reader, not the fixture, is what
asserts the run is ambiguous.

**A COUNT OF ZERO IS REFUSED, AND THAT IS A THIRD SIDE OF THE CS-1068
COLLISION.** Four zero bytes are an empty count-prefixed list AND an empty
string AND the zero-valued residual `read_zero_remainder` reads. Nothing in the
run tells those apart, so this reader claims none of them and requires at least
one entry it can walk. **DO NOT LATER READ THE ORDERING OF THE FOUR READERS AS
WHAT KEEPS THEM APART** - the refusal is what does, and the ordering only
guarantees no region is counted twice.

**WHAT REMAINS, AND IT IS NOT ONE SHAPE.** Four blocks above this one - and the
shipped region entry until this cycle - describe the residual as one shape, a
large nested structure. Re-measured on the three pairs this item covers, the
residual splits into SEVERAL distinct grammars, of which the nested one carries
the large majority and this cycle's reading carried none of it. The number is
deliberately not written here - CS-1149 exists because no file owns that census
and a figure in prose is the thing that rotted. That
correction is filed as CS-1149 rather than fixed by editing a sentence, because
a sentence is what was wrong: no file owns a census of the residual, and the
library test reports it as one number per pair. CS-1119 still owns reading the
nested shape itself.

**DO NOT CLOSE THIS ITEM ON THE STRENGTH OF THE REFERENCE LIST.** The same
sentence as the four blocks above, for the same reason. The clause says every
payload of the three pairs, and a residual population survives on every one of
them - larger, this cycle, than what was read.

### Sixth partial ship recorded 2026-09-19 - the named-transform list reads, the nested structure does not

**THE ITEM STAYS OPEN AND ITS ACCEPTANCE IS UNCHANGED.** This is the sixth
reading of the run and the fifth recorded here as a measurement rather than a
closure. What shipped reads one further derived class set - the one whose
remainder is a COUNT followed by that many NAMED TRANSFORMS - and nothing else.

**WHAT IS NOW READ.** `clockspeed/save/objects.read_transform_list` reads the
int32 count the remainder opens with and walks that many entries, each a
length-prefixed NAME followed by `TRANSFORM_LIST_SCALARS` fixed-width scalars
and one flag byte, and reports them on `TrailingRun.transform_list` with
`unread` falling to zero. `derive_transform_list_classes` picks the carrying
classes off the body being read and answers the SCALAR WIDTH with them. The
figures move with the operator library and `tests/save/test_transform_list.py`
is their only owner, so none is written here.

**WHAT THE SCALARS DENOTE IS NOT CLAIMED, AND THE RESTRAINT IS THE POINT RATHER
THAN A GAP.** Their COUNT and their WIDTH are what the walk consumes and both
are derived; what each one means is a second claim this reading does not carry.
A draft of this block named them, and the name was a guess dressed as a
measurement. **DO NOT LATER READ `TransformListEntry.scalars` AS A TRANSFORM OF
ANY PARTICULAR SHAPE** - the field name says the list is of named transforms
because that is what the carrier writes, and the tuple says thirteen scalars
because that is what the bytes hold.

**THE SCALAR WIDTH IS NOT A CONSTANT OF THE FORMAT, WHICH IS THE SAME LESSON THE
REFERENCE PAIR'S TAIL AND THE REFERENCE LIST'S PER-ENTRY SCALAR BOTH TAUGHT.**
Measured over this library the carrying class writes the narrow block on one of
the three pairs and the wide block on the other two. A reader built on either
width alone would refuse every body of the other, and one built on
`declared_end - terminator_end` would read both and could not fail - the CS-830
defect. Every width this reader consumes comes from the count, from a name's own
length prefix, or from `TRANSFORM_LIST_SCALAR_WIDTHS` and its two companions.
A version table keyed on the layout would have worked on today's library and
would have been a transcription, which CS-829's note forbids by name.

**AMBIGUITY IS DECLINED RATHER THAN RESOLVED BY ORDER**, exactly as
`read_reference_list` declines it and for the same structural reason: the two
widths make the walk reach each entry's length prefix at DIFFERENT offsets, so
nothing forbids both landing on the declared end. `_transform_list_width_of`
returns nothing when more than one width reads, and
`tests/save/test_transform_list.py` holds it against a run CONSTRUCTED to read
at both - the shipped reader, not the fixture, is what asserts the run is
ambiguous.

**A COUNT OF ZERO IS REFUSED, AND THAT IS A FOURTH SIDE OF THE CS-1068
COLLISION.** Four zero bytes are an empty count-prefixed item list AND an empty
string AND the zero-valued residual AND an empty list of this shape. Nothing in
the run tells those apart, so this reader claims none of them.

**THE WEAKEST CASE, AND IT IS WEAKER HERE THAN ON ANY EARLIER READING OF THIS
RUN.** The consistency requirement that admits a class contributes nothing when
that class has exactly ONE remainder-bearing record in the body, and re-derived
PER BODY over this whole library that is EVERY derived carrier on EVERY one of
the three pairs. The requirement therefore refuses nothing on this corpus, and
the derived WIDTH is as good as OBSERVED on all three pairs. **A DRAFT OF THIS
BLOCK SAID IT HELD ON TWO PAIRS OF THREE AND THAT THE THIRD PAIR'S RECORDS
AGREED WITH EACH OTHER; the cycle's verifier measured both halves false** and
they are corrected rather than quietly dropped. What still refuses real input is
the READING - a positive count, non-empty names and an exact landing, none of
which the leftover supplies - and a later cycle strengthening this should
require a floor on n rather than re-deriving the consistency rule.

**THE POPULATION IS SMALL AND IS NOT ROUNDED UP EITHER.** This shape carries a
small fraction of what the corrected instrument reports open on the three pairs;
the nested structure still carries the large majority. This cycle read the
largest residual grammar that was BOTH derivable and free of the disclosure
problem CS-1150 records, which is a different claim from reading the largest one.

**WHAT REMAINS.** The nested structure CS-1119 owns, plus two shapes this cycle
measured and declined: one that [[CS-1150]] fences on disclosure grounds, and one
too narrow for any grammar to claim. [[CS-1149]]'s census still owns the
breakdown, and [[CS-1151]] records a sentence in the blocks above that this
cycle measured false.

**DO NOT CLOSE THIS ITEM ON THE STRENGTH OF THE TRANSFORM LIST.** The same
sentence as the five blocks above, for the same reason. The clause says every
payload of the three pairs, and a residual population survives on every one of
them.

### Acceptance

the run's contents are read, or its width is DERIVED from something in the payload rather than OBSERVED as `declared_end - terminator_end`, on every payload of the (10,36), (13,42) and (14,52) pairs, proven by a skip-if-absent real-library test reporting COUNTS ONLY


## CS-829

### Relocated 2026-09-12 from `docs/GATED.md` by session 86

**WHY IT MOVED, AND WHAT DID NOT HAPPEN.** CS-829 sat in `docs/GATED.md` with its unblocking
condition stated as "CS-G05 clearing". That condition no longer holds - the STATUS block at
the head of CS-G05's section in `docs/GATED.md` records that gate as discharged - and
`docs/GATED.md`'s own opening rule says an item that is merely unstarted is not gated. So
the item LINE is routed back to `ROADMAP.md` under Phase 4 and its body comes here, which is
the leaf `docs/item_notes.md` routes a Phase 4 item in the `CS-8nn` block below CS-850 to.

**NOTHING ABOUT THE ITEM CHANGED IN THE MOVE.** It is NOT closed, its population is NOT
narrowed, and its acceptance clause is carried into `ROADMAP.md` word for word as it stood
before it was gated. Whether that clause is satisfiable AS WRITTEN is a measurement that had
not been taken when this block was filed; taking it is the first thing the item asks for,
and it is not something a routing pass may assume in either direction.

**THE FENCES BELOW ARE LIVE INSTRUCTIONS AND TRAVEL WITH THE ITEM.** The body is relocated
VERBATIM under the family rule in `docs/item_notes.md`, so its DRAIN and PREP split still
reads as it did while the item was gated. Read "blocked, untouchable until CS-G05 clears" as
a record of the state the item was in, not as a current claim about it. Everything the
fences forbid - re-pitching this as the inventory item, hand-writing a struct vocabulary,
defining the population by the decoder's own success, grading over the pool, skipping
`_UNEXPLAINED_WORD_CEILING`, restating the clause without an operator ruling and its own
record - is forbidden exactly as before. The gate going away removed a blocker, not a fence.

### CS-829 - StructProperty's interior, gated behind CS-G05

**One line:** Read the interior of every `StructProperty` the shipped vocabulary names, and
grade it as an EQUALITY over that population.

**Unblocked by:** CS-G05 clearing. Operator ruling, session 50, taken on an adjudicator's
verdict against the item's own acceptance clause.

**WHY IT IS GATED AND NOT MERELY HARD.** The acceptance clause names "EVERY record carrying
a struct type word the shipped vocabulary names". **23529 struct type words sit in the bytes
of records NO reading opens** - they belong to the version pair whose payload grammar is
exactly what CS-G05 exists to measure. The clause's literal population therefore contains a
class this repo cannot grade at all, and no amount of work inside the repo changes that
while CS-G05 stands. The item was rewritten twice for unsatisfiability in one day at filing;
this is the same fault surviving in a third form, and dispatching a sixth build against the
present wording produces a sixth refutation for the first draft's reason.

**THE ITEM IS NOT MOVED HERE TO PARK IT.** It is moved because the gate is real and was
being paid for in refutations instead of being named. Four rounds were spent relocating a
shared substrate; the fifth relocated it again and is filed as CS-863. None of that work
touches the 23529.

**DRAIN - blocked, untouchable until CS-G05 clears:**

- The equality the clause demands over its literal population. The 23529 unreached words are
  in it and cannot be reached.
- `compatible_decoded == size_compatible` with no ceiling. `_COMPATIBLE_REFUSAL_CEILING` is
  64 against an observed residue of 12, so the shipped grade is a floor plus a ceiling with
  52 of headroom where the clause says "an EQUALITY over that population and not as a floor".
  The 12 residual refusals are not explained. Whether they can be, without the gated pair's
  grammar, is itself unmeasured.
- Any restatement of the clause's population. **A restated clause is a scope change and
  closes as one**, with its own record - it is not this gate clearing. The rule at the top
  of `docs/GATED.md` - "The rule that protects this file" - covers exactly this move.
  THAT POINTER WAS RELATIVE AND IS MADE ABSOLUTE HERE: this bullet was written while the
  item lived in that file, and "this file" meant it. Nothing else in the bullet is changed.

**PREP - workable now, and mostly already built:**

- `tests/save/independent_table.py` reads the record framing without calling one shipped
  reader, and its output equals the shipped table element-for-element across the library.
  Merged session 50.
- The record-table anti-monotone control. Its limits were CS-862, which CLOSED
  2026-08-31 - see `docs/LEDGER.md`. The control's own claim is now narrowed to the one
  bit of wiring it grades, and the second reading is separated from the shipped record
  table by dynamic arms that redden for a wrapper, including through the `getattr` route
  no static arm sees.
- The follow-ups CS-864 and CS-865 are PREP and still OPEN. CS-866 CLOSED 2026-08-31.
  CS-868, CS-869, CS-870 and CS-871 joined the PREP set the same day - the first three from
  an adversarial pass that REFUTED CS-863's two arms, the fourth from the adjudication of
  CS-866. They are the harness that will grade the DRAIN half when the gate clears, and
  every one of them is worth doing before it does. THREE OF THAT FOUR HAVE SINCE CLOSED -
  CS-868, CS-869 and CS-870, each with its own entry in `docs/LEDGER.md` - so CS-871 is the
  only one of them still OPEN. The sentence above records when they JOINED the set, not
  what is left in it.
- CS-862, CS-863 and CS-866 are done - see `docs/LEDGER.md`, INCLUDING THE CORRECTIONS.
  CS-862's record is corrected twice and CS-863's once, and all three corrections narrow
  what the arms are shown to grade rather than widening it. Read the corrections before
  trusting any scope claim in the entries beneath them.

**WHAT WOULD BE A SYNTHETIC CLOSE HERE**, named so it is recognised: narrowing the graded
population to the reachable, size-compatible sites and declaring the clause met. That is
the proxy substitution the opening rule of `docs/GATED.md` describes - again a relative
pointer made absolute, for the reason the bullet above states. The narrowing may well be the
right ENGINEERING answer - it is what the shipped arms already do - but it is a scope change
and it needs the operator's ruling and its own record, not a green suite.

**THE FENCES, CARRIED FORWARD FROM THE ITEM NOTE.** The rounds-1-to-5 record is archived at
`docs/history_notes.md` under **CS-829**, and that file holds nothing current by its own
header - so the standing instructions live here, where the item now does:

- **DO NOT re-pitch this as the inventory item.** Its first acceptance asked for
  `InventoryStack` off a real BUILDING and MEASURED over the real library: no building record
  carries one. A building holds an `ObjectProperty` REFERENCE to a separate inventory
  component and the stacks live over there inside a container property, so inventory sits
  behind the cross-record join (CS-831), the container element framing (CS-830), and only
  then this item. An operator ruling on CS-400 clause 1 was obtained on that false premise
  and has been restated by SUBSTANCE rather than by item id as a result.
- **DO NOT hand-write a struct vocabulary.** Derive the population. A transcribed list of
  observed type words is the hand-maintained list this project has repeatedly recorded as
  the thing that rots.
- **DO NOT define the population by the decoder's own success.** That is an identity: a
  decoder refusing a word outright does not fail, the word merely leaves the class and is
  relabelled. It was proven mechanically against two hundred thousand arbitrary wrong
  decoders, none of which it caught. The population is every site whose DECLARED SIZE could
  hold a tag list, which never calls the decoder.
- **DO NOT grade over the pool.** Every quantifier ranging over a set is asserted per member
  of that set. Pooling three container words is exactly how CS-830 shipped a word with no
  element-grammar evidence behind one that had plenty.
- **DO NOT skip `_UNEXPLAINED_WORD_CEILING`.** The skip was built, measured and REVERTED: an
  in-process mutant refusing the weakest reading word at `objects._decode_struct_interior` is
  caught by that arm and NO OTHER, so the skip that spares the subset spares a real defect.
  Its own residual work is CS-865.
- **DISTINCT FROM CS-456**, which asks whether a WRONG tag-extra width is discriminated for
  the four types that ship one. That is a question about the FRAMING; this item is about the
  CONTENTS. Closing either leaves the other open.
- **DO NOT re-pitch `BODY_LAYOUT_BY_PAIR` as the next shared substrate.** Measured session
  50: 53 of 56 layout plants make `parse_body` raise and `assert not sweep.failures` catches
  them, 3 are equivalent mutants, silent loss is zero. The shared SCALARS were the live
  hole after it and they were CS-863, which CLOSED 2026-08-31: the second tag reading no
  longer consults the shipped tag ceiling, and every shipped symbol it still shares is
  enumerated at the point of use rather than sampled in prose. The measurement of what a
  plant on each of those does is in that item's ledger entry - two of the three ceilings
  KILL rather than degrade, so they are recorded UNESTABLISHED rather than safe, and one
  shared width moves nothing at all.

### Acceptance

EVERY record carrying a struct type word the shipped vocabulary names yields a decoded interior, asserted as an EQUALITY over that population and not as a floor, with the vocabulary DERIVED from the library rather than transcribed, proven by a skip-if-absent real-library test reporting COUNTS ONLY


## CS-839

### NOTE - filed 2026-08-23 by the merger

MEASURED 2026-08-23 on one commit, not reasoned. The same tree, the same pytest
invocation, two shells:

- Git Bash - `tests/test_hook_interpreter_ladder.py` green.
- PowerShell - 6 failed, 75 passed, 6 skipped, exit 1.

The cause is a module-scope constant: `DEFAULT_SHELL` is resolved from the interpreter's
PATH at import time, and PowerShell's PATH lacks the directory that carries `sh`, so it
resolves to nothing and every arm that needs a shell asserts instead of skipping. The
module was UNTOUCHED between the session's base commit and the measurement, so this is a
standing property of the repo rather than session damage.

**WHY IT IS TIER 1 AND NOT COSMETIC.** The failures name a missing shell, which reads as a
broken machine rather than as a harness artifact. An operator or an agent checking their
work from the wrong shell sees six red and hunts a regression that does not exist - and
the reverse is worse, because a green run proves less than it appears to. This is the
standing "a green local suite is evidence about ONE toolchain" trap made concrete and
reproducible.

**DO NOT FIX IT BY WIDENING THE PATH.** That makes the measurement agree by changing the
machine, not by changing the property. The two honest routes are in the acceptance: make
the sets identical, or make the dependency a declared skip that names its requirement. A
skip that says why is evidence; an assertion failure that says `no /bin/sh on this
machine` is not.

### Acceptance

the pass/fail SET is identical under Git Bash and PowerShell on one commit, or the dependency is recorded as a shipped SKIP criterion naming what it requires, proven by a test that goes RED when the interpreter cannot resolve the shell and the module reports FAILURES instead of skips


## CS-840

### NOTE - filed 2026-08-23 by the merger, on an operator ruling

**RULED BY THE OPERATOR 2026-08-23, ASKED DIRECTLY: file it, do not resolve it.** The
relocate slice that surfaced it was told to leave every dated heading exactly as it stood,
and did.

The contradiction, both sides tracked and both live: `CLAUDE.md` states that a doc heading
carrying an explicit date marks its own section HISTORICAL. `docs/item_notes.md` states
that a block in it is a LIVE INSTRUCTION. The drift guard's dated-heading arm reports the
population in that file rather than failing on it, so nothing is red and both sentences
stay shipped.

**THE REPORT-ONLY ARM IS WHY THIS SURVIVED.** A guard that reports cannot lose, so the
contradiction has no cost until someone acts on the wrong half of it. The acceptance asks
for an arm that FAILS, because that is the only version that settles which sentence is
true.

### Measured 2026-09-01, and NOT acted on

**BOTH HALVES OF THE CONTRADICTION ABOVE READ AS RESOLVED ON THE SHIPPED TREE, AND
THIS ITEM WAS STILL LEFT OPEN.** `guard_dated` in `tools/drift_guard.py` returns
FAIL - not a report - when a file carrying dated headings declares no status, when a
status date sits inside a file declaring itself LIVE, or when a heading fits neither
idiom. `CLAUDE.md` section 4 now states the position rule and names guard (g) as the
owner of the closed idiom vocabulary, which is the stated criterion this item's
acceptance asks for. So the sentence above - that the arm reports rather than fails -
is stale, and the paragraph is kept unedited because bodies here are verbatim.

**WHY IT IS STILL OPEN.** Closing needs a `docs/LEDGER.md` entry, and the doc-sync
pass that measured this had no write access to that file. Rewording the ROADMAP line
to something true would have laundered a stale item into a current-looking one, so
the line was left exactly as it stood. **WHOEVER CLOSES THIS MUST RE-MEASURE RATHER
THAN TRUST THIS BLOCK**, and must check the acceptance's second half - a guard arm
that goes RED when a section is dated under whichever rule survives.

**DO NOT RESOLVE IT BY DATING FEWER HEADINGS.** Stripping a date from a section changes
what an outside reader believes about that section's status, which is a semantic change
wearing a formatting hat. Whichever rule survives, it is a ruling about the topology and
belongs to whoever makes it, not to a sweep.

### Acceptance

the two agree - either the rule carves out that file against a stated criterion, or the file stops dating live headings - proven by a guard arm that FAILS rather than reports, and that goes RED when a section is dated under whichever rule survives


## CS-841

### NOTE - filed 2026-08-23 by the merger, required by CS-838's grant

**FILED BECAUSE CONDITION FOURTEEN OF CS-838's FROZEN-FILE GRANT REQUIRES IT.** That grant
is recorded in `docs/LEDGER.md`. The implementer reported the condition as only PARTIALLY
met precisely because this item did not exist and none of the files that could hold it
were on its write-list. This section is the discharge.

MEASURED during CS-838, by two agents independently: `tools/edit_lint_check.py` builds its
work unit without a disk path and passes no root, so every unit is staged to a temporary
directory where ruff discovers no project configuration. Line length then falls back to
ruff's default instead of the project's, and the great majority of this repo's tracked
Python "would be reformatted" - a false positive on nearly every file. CS-838 therefore
SKIPS its format check when no configuration resolves. That mitigation is correct and
shipping without it would have been worse than the defect it fixes.

**THE RESIDUAL HAS TWO PROPERTIES AND BOTH MATTER.**

It is SILENT: notes print only under a verbose flag, and the hook entry that invokes this
path passes none. So on the one path the mitigation targets, the skip is never rendered.
This is NOT a coverage reduction - there is no format coverage there today - but it is a
permanent disablement that no output discloses.

It is SELF-ARMING: `tools/edit_lint_check.py` is NOT a frozen file. A later one-line change
passing a root would activate a blocking check on that path with no grant and no review,
and the first sign of it would be an operator's edit being refused.

**DO NOT ABSORB THIS INTO CS-838.** The grant says so, and the reason is that the repair
belongs to a file the grant does not cover.

### Acceptance

that path either resolves a config and blocks a genuine format violation, or its skip is visible without `--verbose`, proven by a test that goes RED when a `root` reaches it and arms a blocking check on a non-frozen file with no grant


## CS-843

### NOTE - filed 2026-08-23 by the CS-830 narrowing builder, from an adversary that wrote none of the code

**CS-830 WAS MERGED AND THEN REFUTED, AND THIS IS THE PART OF IT THAT DID NOT SURVIVE.**
The item is narrowed on an operator ruling rather than reopened: what it decodes is kept,
what it could not prove is recorded, and the unproven remainder is this item.

**THE DISTINCTION THE WHOLE ITEM TURNS ON IS EXTENT VERSUS PARTITION.** A container's
element region is bounded - the tag declares its size, the walk requires the elements to
consume it exactly, and a region that does not close is refused rather than truncated.
That is real and it is kept. What is NOT established is the PARTITION: where inside that
region one element ends and the next begins.

**WHY THE REGION CLOSING IS NOT EVIDENCE FOR THE PARTITION.** Where the element word has
no grammar of its own, the region is divided by the DECLARED count and admitted because
the division came out even. Under a forced width the walk returns `at + width` after a
bounds check that cannot fail while slots remain, so it closes by arithmetic - the walk
CANNOT fail once the division is exact, and a check that cannot fail is not a check.

**MEASURED, NOT ARGUED.** A partition giving the first element the whole span less one
byte per remaining slot and every other element exactly one byte was run through every
library-backed equality this project has. All of them stayed green. That measurement now
ships as a test - `tests/save/test_container_elements.py::test_a_provably_wrong_partition_survives_every_library_backed_equality` -
which ASSERTS the survival, so the day anything in the corpus does discriminate the
partition, that test is what says so. **A RED THERE IS GOOD NEWS AND IS THIS ITEM
PROGRESSING.**

**THE SECOND EQUALITY CANNOT HELP AND IT IS WORTH KNOWING WHY.** `_walk_elements` appends
exactly one entry per `count x words` step or returns None, so the bounded total equals
the declared total identically, for every width tuple that closes. Both sides are computed
from the same declared count. It grades the fold's accounting, never the widths.

**THE DECLARED COUNT IS NOT CROSS-CHECKED EITHER, AND THIS IS CS-830'S OWN FIRST-DRAFT
DEFECT ALIVE IN THE SHAPE ITS REPAIR PERMITS.** A region truly holding a few wide elements,
declared as one slot per byte, divides exactly and is published as that many one-byte
elements with nothing refused. The case ships as
`test_a_uniform_region_is_partitioned_by_a_declared_count_nothing_cross_checks`, which
records the behaviour and does not endorse it.

**THE POPULATION IS TWO SHAPES, NOT ONE WORD, AND READING IT AS ONE WORD IS THE ERROR TO
AVOID.** `SetProperty` is the whole-word case: not one instance in the corpus was bounded
by the element's own grammar, so its framing has never once been tested against a reading
that could have failed, and it is named in
`objects.CONTAINER_WORDS_WITHOUT_ELEMENT_GRAMMAR_EVIDENCE`. But the STRUCT-SHAPED ARRAYS
carry the same limit while sitting inside a word that is overwhelmingly self-delimiting,
so they are invisible to any per-word record. **THE SHAPE IS THE PROPERTY** -
`objects.UNDISCRIMINATED_ELEMENT_SHAPES` is the table that generalises, and the per-word
one records only where a whole word rests on it.

**NO POPULATION FIGURE IS WRITTEN HERE - CLAUDE.md section 4.** The operator plays this
game and every count moves on the next autosave. Which words and which shapes is a
classification and is shipped as data; how many instances each holds is derived on every
run.

**DO NOT CLOSE THIS BY DELETING THE DECODE.** The elements are bounded and the region
closes; the unproven claim is narrower than the decode, and deleting it would give up
something real to avoid admitting something unproven.

**DO NOT CLOSE THIS WITH A SYNTHETIC FIXTURE ALONE.** A hand-authored set of struct
elements is packed from the same belief the reader unpacks it with, so it grades the
fixture author's assumption and not the format - the adversary's finding was precisely
that the only red the wrong partition produced came from such a fixture. The evidence has
to come from somewhere that could have disagreed: the struct's own interior grammar
(CS-829), an element width the shipped assets state, or a cross-check between the declared
count and the region that a misdeclaration would break.

### Acceptance

the partition is derived from evidence that could have refuted it, or the shipped record narrows to exactly what the extent buys, proven by a test that goes RED when a deliberately wrong partition is substituted and by the corpus-survives control being deleted in the same change


## CS-844

### SALVAGE NOTE - MEASURED 2026-09-04 (session 60) by the merger, and the work already exists

**1524 LINES OF WORK ON THIS ITEM ARE SITTING ON AN UNLANDED BRANCH AND WOULD BE REBUILT
FROM NOTHING.** Found while measuring worktrees, not while working this item. Preserved as
the tag `salvage/cs-844-session-46` so it survives branch deletion; the branch is
`worktree-agent-abccd667b38e14135`, three commits, dated 2026-08-24, adding ONE new test
module under `tests/` that has never existed in main. Its name is deliberately not
spelled here: the citation guard shipped this session reported it as a dead identifier
on this very paragraph, which is the item's own subject demonstrating itself. Read the
tag.

**WHY IT NEVER LANDED, IN ITS OWN WORDS: "THIS COMMIT IS DELIBERATELY RED."** It was not
abandoned because it broke. It was abandoned because it FOUND things its own write-list
could not repair. That is a reason to read it, not to discard it.

**IT STILL RUNS.** Copied onto today's tree in a throwaway worktree: **26 passed, 2 failed,
exit 1**. Eleven days of drift did not break it.

**WHAT IT GETS RIGHT, AND BOTH FINDINGS ARE STILL LIVE.**

- **The dual-item ledger heading.** `docs/LEDGER.md` line 4502 opens an entry
  `### 2026-08-20 - CS-493, CS-494 - ...`, declaring TWO ids in one heading, so a reader
  parsing an entry head gets the id "CS-493, CS-494" and CS-494 is declared by nothing.
  Its four citations sit at lines 4506, 4543, 4765 and 4854 - **exactly the "four citations
  stranded" the 2026-08-24 commit body predicted**, still stranded today.
- **Owner records naming CLOSED items.** `tests/chained_exemption_guard.py` records CS-888
  as its owner and CS-888 closed LAST SESSION; `tests/data/test_item_notes_index.py` records
  CS-402, CS-403 and CS-404, all closed. That is the second half of this item's acceptance -
  "a closed owner is distinguished from an open one" - already demonstrated on live sites.

**WHAT IT GETS WRONG, AND IT MUST NOT LAND UNTIL THIS IS FIXED.**

- **Synthetic fixture ids are reported as findings.** CS-999, CS-997, CS-996, CS-4000,
  CS-901, CS-902 and CS-99999 are all deliberate test fixtures. The guard flags CS-99999 at
  the very site whose sentence explains that it is an id naming nothing - so it manufactures
  a finding on the prose documenting the concept it grades.
- **A real closed item is reported as naming nothing.** CS-617 has a well-formed
  `### 2026-09-01 - CS-617 - CLOSED.` entry at `docs/LEDGER.md` line 1015 AND a correction
  record at line 888. The resolver handles neither the second entry nor the correction form,
  and reports seven shell sites against it. **A false clearance is worse than a silence and
  a false FINDING is worse than both when it blocks a push.**
- **Prose about a future id is read as a record.** ADR 0011 discusses CS-900 as a question
  to answer; the guard records it as an id naming nothing.

**THE PART THAT MAKES THIS CHEAP NOW, AND IT WAS NOT CHEAP IN AUGUST.** Every one of those
faults is the boundary problem CS-891 spent session 60 solving, and CS-891 SHIPPED THE
MACHINERY: an AST partition that declines a path inside a non-docstring string literal
(which is where nearly all the fixture noise lives), a metasyntactic-placeholder decline, a
decline ladder whose every rung states its price, and a reason table keyed on identity
rather than a count with a two-way ratchet over it. Read `tests/bare_path_guard.py` before
rebuilding any of that here.

**DO NOT START THIS ITEM BY WRITING A NEW MODULE.** Start by reading the tag.


### NOTE - filed 2026-08-23 by the CS-830 narrowing builder

**MEASURED, from the same adversarial pass.** `objects.CONTAINER_ADJACENT_OWNERS` records
which item owns a container-shaped word this module does not decode, and the guard over it
in `tests/save/test_container_elements.py` asserts only `item.startswith("CS-")`. So
`CS-99999` - an id naming nothing anywhere in the work-item files - satisfies it, and the
guard's own failure message calls a non-id "a sentence rather than a route" while
accepting a route that leads nowhere.

**THE FAILURE MODE IS NOT THE TYPO, IT IS THE CLOSE.** The realistic way this bites is an
owner id that WAS real: the owning item closes, its section relocates to
`docs/history_notes.md`, and the entry goes on naming it forever with every guard green.
The word then has a recorded owner that cannot be acted on, which is the same class of
defect as a region entry recording a measurement nobody made.

**IT IS NOT CONFINED TO THIS ONE TABLE.** Look for the sibling cases before repairing the
one - any shipped table recording a `CS-` id as an owner, a route or a hand-off has the
same weakness unless something resolves the id. Grep for the prefix in shipped data rather
than assuming the container table is the only site; the CS-830 pass found four sites of one
gloss by doing exactly that.

**AN OPEN OWNER AND A CLOSED OWNER ARE DIFFERENT ANSWERS AND THE ACCEPTANCE ASKS FOR BOTH.**
A closed owner is not a broken pointer - it means the hand-off has ALREADY HAPPENED and the
entry is stale rather than wrong - so a check that treats the two alike would force a false
choice between deleting live records and keeping dead ones.

### NOT MERGED - recorded 2026-08-24 by the merger, after a trial merge

**THE WORK EXISTS AND IS GOOD. IT IS ON BRANCH `worktree-agent-abccd667b38e14135`,
THREE COMMITS, AND IT DID NOT LAND.** The guard was widened from six sites to a derived
population across four channels - literals, docstrings, comments reached by `tokenize`, and
lines in tracked non-`.py` files - and it shipped the ownership-prose refutation as a record
that re-measures itself every run rather than as an adjective. None of that is in question.

**IT DID NOT LAND BECAUSE ITS SUITE IS RED ON A FALSE POSITIVE, AND A RED SUITE BLOCKS THE
PRE-PUSH HOOK.** Measured by trial merge on 2026-08-24, then backed out: of the four findings
the guard raised, THREE WERE REAL AND ARE NOW FIXED ON MAIN - the orphaned ledger entry head,
the four citations downstream of it, and a slash-command example wired to real closed ids.
Exactly one finding remained, and it is not a defect in the tree:

    tests/test_hook_interpreter_ladder.py::ITEM_ID records CS-703 as the owner, and it is CLOSED

**IT IS A PIN, NOT A ROUTE.** `.githooks/commit-msg` renders that id inside its own refusal
text, and the same module asserts that the hook's rendered output CITES it. The constant
exists so an arm can pin WHICH rule refused. Following the guard's own advice - "redirect it
to the item carrying the remainder, or delete it if nothing is left" - WOULD BREAK A TRUE
ASSERTION, because the frozen hook still says it.

**THIS WAS PREDICTED BY THE ITEM'S OWN ADVERSARY AND IT IS THE PREDICTION LANDING.** That
grading measured that signal B - the binding name declaring it records owners - does no work
against the real tree, so the effective classifier is signal A alone: the constant IS a whole
work-item id. A pin on text an external process emits satisfies signal A and is not an owner.
The classifier is over-broad, which is a defect in the guard rather than in the code it
grades.

**WHAT WOULD CLOSE IT.** A derived distinction between a ROUTE and a PIN. A pin is an id
constant that a test asserts appears in output produced by something outside this repo's
control - a frozen hook, a subprocess, a shipped asset. That is AST-detectable and does not
require reading English, so it does not reopen the prose route the item already refuted. The
merger deliberately did NOT author that exclusion, because an exclusion written by the person
merging it is graded by nobody, which is the exact pattern this session spent itself
demonstrating.

**DO NOT close this by editing `ITEM_ID`.** It is correct as written and the assertion that
consumes it is true.

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

An owner recorded against a shipped table is checked for the `CS-` PREFIX only, so an id naming no item satisfies every guard and an entry keeps pointing at nothing once its owner closes

### Acceptance

a recorded owner resolves to an item that actually exists in the work-item files, and a closed owner is distinguished from an open one, proven by a test that goes RED for a well-formed id naming no item


## CS-846

### NOTE - filed 2026-08-24 by the merger, on the CS-842 builder's recommendation

**MEASURED by the adversary grading CS-842, and the builder DECLINED to fix it inside that
item - correctly.** Its reasoning is the reason this is its own item: CS-842's acceptance
takes that control as a given, so strengthening it there would be the builder grading
something it had just changed; and the defect is not specific to one control - every control
in that cluster has the same shape, so repairing the instance and leaving the population is
the exact error this project keeps paying for.

**THE DEFECT.** A control's body replaced by an early return before its only assertion -
`if corpus: return` - leaves the whole guard cluster green. The control stops grading and
nothing reports it.

**IT IS THE SAME SHAPE AS A STANDING FINDING, WHICH IS WHY IT IS WORTH GENERALISING.** A
mutant that never applied and one that survived produce identical output; an early return and
a pass produce identical output. In both cases the absence of a signal is being read as the
presence of a negative result.

**THE POPULATION IS THE DELIVERABLE, NOT THE INSTANCE.** Do not close this by adding a
liveness check to the one control that was measured. Derive the set of shipped controls and
grade every member, or record an exemption per member with its own reason.

### WIDENED - recorded 2026-08-24, same day, on a SECOND measured instance in a DIFFERENT structure

Filed against a CONTROL. Hours later the CS-839 builder reported the identical shape in a
GUARD: gutting its body to a bare `return` leaves the module green, and it declined to build
one-arm protection on the grounds that a per-arm version is the hand-maintained thing this
repo keeps recording as the thing that rots. It was right, and it could not file the item
because `ROADMAP.md` was not on its write-list.

**TWO AGENTS FOUND THE SAME DEFECT IN TWO DIFFERENT STRUCTURES WITHOUT KNOWING OF EACH
OTHER.** That is the evidence the population is wider than the word this item was filed with,
so the acceptance now says control AND guard and derives the set from the shipped assertions
rather than from either word. Anyone taking it should assume the real population is wider
still and derive it rather than trust this sentence.

### REFUTED TWICE, MERGED NARROWED - recorded 2026-08-25

**THE MOTIVATION IS INDEPENDENTLY REPRODUCED AND IS THE BEST EVIDENCE THIS ITEM HAS EVER
HAD:** planting an early return one guard at a time, 2 OF 9 SHIPPED GUARDS SURVIVED with the
whole consuming set green while `tools/drift_guard.py` printed VERDICT: CLEAN. All 9 die now.

**FIRST REFUTATION:** the check keyed on a literal `ast.Return` while 1855 of 1857 members
contain no return statement at all - a detector for ONE mutation operator over a population
that mostly could not exhibit it.

**SECOND REFUTATION, AND IT IS THIS SESSION'S THEME:** the replacement rules were SELECTED
BECAUSE THEY SCORED ZERO ON TODAY'S TREE. Four of eight genuinely correct idioms reddened,
and `match` scored zero only because this tree contains no `match` statement. See
`memory/a-proof-can-require-the-defect.md`.

**WHAT IS NOT COVERED, and this is now enumerated in the module rather than implied away -
ELEVEN shapes covered, FIVE not:** a non-constant tautology (the shape this repo actually
shipped and removed this session); a gutting branch whose condition is genuinely unknown; a
grader RENAMED out of the vocabulary; a value-returning grader gutted to `return None`; and
ANYTHING AT ALL about whether an assertion actually RAN. **The acceptance word is "every",
so the item stays open on the gap between eleven and every.**

**DO NOT RE-PITCH** choosing a rule by its false-positive count on the current tree. Choose
by stated semantics and REPORT the cost - the strict end-of-function rule reports 129 correct
bodies and that number is disclosed rather than designed around.

### REFUTED AGAIN, THEN SUBSTANTIALLY REPAIRED - recorded 2026-08-25 (session 40)

**THE ADVERSARY REPRODUCED THE PREDICTED FAILURE MODE, AND IT WAS THE SAME ONE AS LAST
TIME, ONE LEVEL DOWN.** Four new rules each scoring zero false positives was the pattern
this item was refuted for; the refusal of two WIDER variants on soundness was genuine, but
the four ADOPTED rules did not survive:

- **Rule 1's stated semantics was not what the code implemented.** It excluded only
  `ast.Call`, while attribute access runs `__get__`, subscription runs `__getitem__`, and
  the comparison operator itself runs `__eq__`/`__ge__`. Demonstrated live: a
  `functools.cached_property` memoization test and an ordering-reflexivity test both FAIL
  when the code under test breaks, and both were flagged "cannot discriminate". They scored
  zero only because this tree ships neither idiom.
- **Rule 3 had false positives on a very ordinary shape** - grade the non-empty case, return
  a count unconditionally.
- **Rule 2 was a two-spelling blocklist** claiming a semantic class; eight always-true
  respellings were missed, including `0 <= len(x)`.
- **Rule 4 added ZERO members** (1986 with routes, 1986 without) and its fixture was the
  fixture trap recurring - a two-module corpus with no live analogue.

**THE REPAIR, AND IT WENT FURTHER THAN THE REFUTATION ASKED.**

- Rule 1 narrowed to `is` between two identical bare `Name` loads - the only genuinely
  language-decided form, since `is` never dispatches and a `Name` load runs nothing. `==`
  was NOT kept: `x == x` fails for NaN and a non-reflexive `__eq__` exactly as `v >= v`
  does, so drawing the line at `==` would have been score-driven. The removed shapes go to
  a counted bound, `Survey.self_comparisons`, still credited as grading. Cost bounded
  rather than argued away: ruff `PLR0124` already catches the bare-`Name` shape tree-wide.
- **Rule 3 WITHDRAWN - after its stated justification was refuted.** The claim that
  `dead_grading` already reports every genuinely dead assert is FALSE as stated: measured,
  two true positives were reported by rule 3 and by nothing else. The real cause was that
  `dead_grading` propagated deadness INSIDE a folded branch but never PAST one. That hole
  is closed (`always_leaves`), after which rule 3 added only its three false positives, and
  it was withdrawn. Both true positives now report as `unreachable grading`.
- Rule 2 widened to a normalised semantic class with the two refused spellings named.
- Loops now fold through `never_iterates()`, matching the `if` handling the module already
  claimed - `while False:` was a constant its own `_literal_truth` decided.

**SILENT GUTTINGS: 8 of 20 -> 1 of 20**, measured in memory against the real shipped control
`tests/test_doc_budget.py::test_a_tree_git_cannot_answer_for_states_its_degradation`.
Newly reported: log-swallow, `contextlib.suppress`, `for _ in []`, `for _ in range(0)`,
`while False`, empty-literal `parametrize`, and the collection rename - the last closed on a
narrower decidable ground than collection itself, reading the prefix from
`[tool.pytest.ini_options] python_functions` rather than hardcoding it.

**THE TWO GUARD MODULES ARE NOW COVERED.** `detector_modules()` is DERIVED - a module under
`tests/` that is not `test_*`, not `__init__.py`, and ships no grading statement. 6 derived,
0 unreached. `conftest.py` carries a stated exemption with a reachability reason, which was
a latent false positive in the new rule, closed rather than banked.

**9 OF 9 drift_guard GUARDS STILL DIE** - re-verified independently twice this session,
pristine floor first, every plant landed and reported, 0 collateral, `tools/drift_guard.py`
sha256 unchanged.

**WHY IT STAYS OPEN.** The acceptance word is "every". Gutting #18 - every assertion
deleted - remains silent, bounded by the module's own outside-the-population census; and
`observed_grading` is still a MECHANISM rather than a population property, because applying
it needs a collection hook in `tests/conftest.py`. **The tree also gained 8 `match`
statements this session**, so the shape the second refutation said scored zero only for want
of a population now has one.

### Acceptance

every shipped control and every shipped guard is covered by a liveness check or recorded against a stated exemption, with the population DERIVED from the shipped assertions rather than listed, proven by a planted early return that turns a test RED in each of one control and one guard that survive one today


## CS-847

### NOTE - filed 2026-08-24 by the merger, from the CS-844 widening

**THE RESIDUAL CS-844 COULD NOT REACH, AND ITS BUILDER SAID SO RATHER THAN WIDENING INTO
GUESSWORK.** CS-844's guard now grades ownership records across four channels. It still
cannot hold a hand-off written as PROSE inside a binding whose NAME does not declare it
records owners.

**TWO SITES ARE LIVE TODAY AND BOTH HAND OFF TO THE SAME GATED ITEM.**
`objects.UNMEASURED_PAYLOAD_REGIONS["trailing_run"]` says a case is scoped out of one item
and into `CS-G05`; a second site on `_TAG_EXTRA_STRINGS` hands off to `CS-G05` as well. Both
read as citations, so neither is held to actionability. **They are harmless only while
`CS-G05` stays GATED. If it closed while those sentences stood, the module would stay
green.**

**PROSE CANNOT DECIDE THIS AND THAT IS MEASURED, NOT ASSUMED.** The CS-844 builder tried:
the ownership idiom and the history idiom are the same words in this repo. Every candidate
pattern reddens on correct history about closed items, at hundreds of sites for the loosest
and at least one for the narrowest. That refutation SHIPS as a re-measured record, so it
cannot rot and will announce itself if a pattern ever becomes usable.

**SO THE LIKELY CLOSE IS RELOCATION, NOT DETECTION.** Move the hand-off into an owner-named
binding where the existing guard already reaches it. Do NOT re-pitch widening the guard into
reading English - that route is refuted in shipped data, not merely untried.

### Acceptance

a hand-off naming an item is held to actionability wherever it is recorded, or the record is relocated into an owner-named binding, proven by a test that goes RED when a hand-off names a CLOSED item, covering the sites that hand off to `CS-G05` today


## CS-848

### NOTE - filed 2026-08-24 by the merger, from the CS-841 round-three adversary

**MEASURED, WITH A CONTROL THAT ISOLATES THE CAUSE.** Arming the format check only for
files `git check-ignore` does NOT ignore SURVIVES the whole suite at exit 0 with the bait at
its current home, and is KILLED at the previous home. A pristine-tool control at the previous
home passes, so the red is caused by the mutant and not by the relocation.

**THE CRITERION THE BAIT WAS CHOSEN AGAINST IS THE CRITERION THAT DEFEATS IT.** The home was
selected for four properties, all of which are reasons it is INVISIBLE TO CI - outside the
would-be-tracked inventory, outside the formatter sweep, gitignored. Invisible to CI and
invisible to an arming predicate are the same property. A second mutant keyed on project
source roots also survives, and was shown blocking a real edit while the suite stayed green.

**DO NOT CLOSE THIS BY MOVING THE BAIT BACK.** The previous home reddened the mypy gate in
three of five parallel runs, which is what the move fixed. The adversary's own conclusion is
that NO in-repo home a one-line predicate can distinguish from a real edit target will do -
the guard needs an assertion keyed on the root argument reaching the linter for an arbitrary
in-source path, rather than on the fate of one file in one directory.

### Acceptance

an arming condition keyed on whether the edited file is gitignored, or on whether it sits under a project source root, turns a test RED, proven by both mutants, and WITHOUT reintroducing the parallel-run contamination the current bait home was chosen to escape


## CS-849

### NOTE - filed 2026-08-24 by the merger, from the CS-841 round-three adversary

**THE TEST SUITE NOW DOES WHAT THE PRODUCTION MODULE IS FORBIDDEN FROM DOING.**
`clockspeed/save/workdir.py` goes out of its way not to create the work directory merely
because something imported it and asked a question - its own prose says a module doing that
would create a directory on every machine including one with no game and no save - and
`tests/save/test_workdir.py` ships the test that pins it. The CS-841 fixture creates that
directory unconditionally and its teardown removes only the inner temporary directory.

**A SECOND-ORDER HAZARD, READ FROM THE CODE AND NOT REPRODUCED.** There is no autouse
work-root isolation, so the pinning test resolves the REAL work directory and samples whether
it exists. On a checkout where it does not yet exist - every fresh clone and every CI run -
a fixture creating it between that test's two checks would turn it red naming a defect that
is not there. Recorded as a code-read hazard because the directory already existed on the
machine where this was found, so it could not be reproduced there.

**THE WORK DIRECTORY IS PII-BEARING.** It is where save copies live. That is why it is
gitignored and why its consumers are careful. Anything writing there needs to be as careful.

### Acceptance

running the rule suite on a checkout with no work directory leaves none behind, proven by a test that goes RED when a fixture creates one, with the work-root consumers DERIVED rather than listed


## CS-842

### NOTE - filed 2026-08-23 by the merger, from CS-837's adversary

MEASURED by the adversary that graded CS-837, and recorded here rather than repaired,
because the item's acceptance was MET and this is a property of the record it produced.

CS-837 closed on its second acceptance arm: the exclusion of a module from the CS-420
quantifier fence is recorded against a derived criterion rather than the module being
fenced. The criterion itself - the literal deliverable of that arm - is prose in
`tests/save/test_absolute_claims.py`.

**THE COUPLING RUNS ONE WAY ONLY.** Deleting the live TEST does not go quiet: the criterion
prose backs its own quantifiers with a citation naming that exact test, so the citation
stops resolving and a different arm turns red. Deleting the criterion PROSE leaves the
suite green. The record is guarded against the test disappearing and not against itself
disappearing.

**THE SECOND HALF OF THE ACCEPTANCE IS THE HARDER HALF, AND IT IS WHY THIS IS NOT A
ONE-LINE FIX.** The same adversary measured that the LIVE test alone cannot tell a derived
qualifying set from a restatement of the list it is compared against - substituting the
fenced tuple for the derivation leaves the live test green, and only a synthetic control
catches it. That control is load-bearing. Any repair that couples the prose in must not
weaken it, or this item trades one unguarded direction for another.

Two further residuals from the same grading, recorded so they are not rediscovered: a
PARTIAL repair of the excluded module leaves the criterion green, so the obligation is
all-or-nothing and is releasable by writing one quantifier back; and the first red will
most likely fire on a package docstring nobody associates with this item, because the
nearest unfenced modules are boilerplate `__init__.py` files a single future sweep would
flip.

### Acceptance

deleting the recorded criterion turns a test RED, proven by that deletion, WITHOUT weakening the synthetic control that is currently the only guard against the derivation being replaced by a restatement of the list it is compared against


## CS-832

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-23, headline CORRECTED the same day: `Int64Property` is NOT in `DECLINED_VALUE_READINGS` - it is named by the `ArrayProperty` entry as an inner type and recorded in `UNMEASURED_PAYLOAD_REGIONS`, so 'declined' was the wrong word for it. **THE TEST CLAUSE IS LOAD-BEARING:** without it this closes by editing one string in a table, which is what the first wording allowed. `TextProperty` had ZERO mentions across `ROADMAP.md`, `BACKLOG.md` and `docs/GATED.md` before this item. Neither blocks pillar 3.

**BOTH CLAUSES OF THAT CORRECTION WERE THEMSELVES MEASURED FALSE 2026-08-23 (session 37), and the cause is CS-830's merge rather than a mis-reading.** The sentence above says `Int64Property` "is named by the `ArrayProperty` entry as an inner type and recorded in `UNMEASURED_PAYLOAD_REGIONS`". Neither holds today. CS-830 PROMOTED the three container words out of that table, so there is no `ArrayProperty` entry left to name anything, and it DELETED the `Int64Property` entry outright. **THAT DELETION WAS FORCED AND IT STANDS.** `tests/save/test_properties.py::test_the_region_table_holds_no_key_nothing_justifies` refuses a key the library does not justify, and the library holds no top-level `Int64Property` tag at all - so an entry there would record a measurement nobody was ever in a position to make. **DO NOT RESTORE THE ENTRY AND DO NOT WEAKEN THAT TEST** to make room for one; that is the disposition an operator ruled on the same day.

**THE CRITERION NOW HAS A HOME THAT IS NOT THAT TABLE**, added by the CS-830 narrowing so this item has a reachable route: `objects.VALUE_READING_CRITERIA` records a type word whose TOP-LEVEL value is declined, against the EVIDENCE that would settle the reading. It is independent of `UNMEASURED_PAYLOAD_REGIONS` by construction - that table records regions the library PRODUCES, this one records a refusal and what would end it - so a word with zero top-level instances can legitimately live in it. `Int64Property` is entered there already, with the criterion phrased as an observation (one top-level tag, of any provenance, read against the element width the arrays already close on) rather than as a sample size. **THIS ITEM'S ACCEPTANCE IS UNCHANGED** and is NOT satisfied by that entry existing: what is still owed is `TextProperty`'s own criterion - its `UNMEASURED_PAYLOAD_REGIONS` entry still turns on an instance count, which is the exact phrasing the acceptance rejects - and the test that goes RED when a criterion is replaced by a sample-size one. **DO NOT CLOSE THIS BY MOVING `TextProperty` ACROSS:** it has real top-level instances, so its region entry is legitimate where it is and the criterion is what needs rewriting, not the table it sits in.

### Acceptance

each is decoded off a real record, or its refusal carries a criterion that names what evidence would settle it rather than how many instances exist, proven by a test that goes RED when that criterion is replaced by a sample-size one


## CS-825

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-23 as the SMALL of the two residuals of CS-421's close. **`unscored` DOES NOT SATISFY THIS** - it is a regression dressed as an acceptance. Detail in this file under **CS-825 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-23 as the SMALL of the two residuals of CS-421's close; the item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

`UInt32Property` is the one measured type whose byte-order status reads
`oracle_cannot_separate_readings`: a shipped oracle was applied to this type's own values and
came back unable to tell the as-stored reading from its reversal. The module documents that
word where it is derived and states in terms that it IS NOT A SETTLEMENT and must never be read
as one.

**TWO ACCEPTANCE HOLES WERE CLOSED AT FILING TIME, BOTH FOUND BY REVIEW RATHER THAN BY THE
AUTHOR, AND BOTH ARE THE REASON THE WORDING IS AWKWARD.** The first draft asked for "a status
other than `oracle_cannot_separate_readings`" - which `unscored` satisfies, and `unscored` means
NOTHING LOOKED. That is a regression that reads as an acceptance, and it is why the item now
demands a word that MEANS SETTLED. **THE LINE NO LONGER SPELLS THE SECOND HALF** - that
`BYTE_ORDER_STATUSES` ships no such word today is recorded HERE, as of 2026-09-01, and
the acceptance requires the word regardless of whether one exists yet.
The second draft asked for the missing ingredient to be "named in shipped data", which its own
NOTE then named in prose - transcribing a NOTE into a module constant is not a measurement, and
it is the trivially-satisfiable shape already recorded against CS-413.

**THE int32 FENCE IS NOT TRANSFERRED TO THIS ITEM.** The finding that every changed matched
value is small at one end, and therefore that no cleverer predicate can separate two correct
oracles, was measured over the int32 population. `UInt32Property` sits in NO scored population,
so that finding has never been measured on it. Carrying it across would be the population carry
`clockspeed/save/objects.py` refuses in writing for the joint result. The fence lives on CS-826.

**WHAT IS NOT KNOWN AND SHOULD BE MEASURED FIRST:** whether this type's own values can support
any oracle at all. Derive its population before designing anything.

### Acceptance

the type's entry in `VALUE_BYTE_ORDER_STATUS` records a SETTLED order derived against the real save library, by a status word that MEANS settled, or the corpus is recorded as unable to settle it with the missing ingredient DERIVED in shipped data rather than transcribed from the detail


## CS-826

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-23 as the LARGE of the two residuals of CS-421's close, and UNFILED until an adversary measured it. These two types are inventory counts and clock speeds, so CS-500's pillar 3 sits on exactly this population rather than on CS-825's. Detail in this file under **CS-826 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-23 as the LARGE of the two residuals of CS-421's close; the item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

`IntProperty` and `FloatProperty` both carry `anchored_not_unique`. The module states where that
word is derived that it is NOT a settlement - a candidate set was narrowed and no single type
has a uniquely pinned order.

**THIS ITEM EXISTED AS AN UNFILED RESIDUAL AND WAS FOUND BY AN ADVERSARY, WHICH IS THE FINDING
WORTH CARRYING.** CS-421's close was first drafted filing only the `UInt32Property` residual,
and asserted that "the unsettled part is now a named item rather than an unmeasured majority".
The majority was this population, and it had no item at all. The shape of the error is worth
more than the instance: a residual was named after the SMALLEST unsettled population because
that was the one the prior adjudication happened to mention by name.

**WHY THIS IS THE ONE THAT MATTERS FOR THE PRODUCT.** `IntProperty` and `FloatProperty` are
inventory counts and clock speeds. CS-500's pillar 3 reads exactly these, so this item and not
CS-825 is the decode-correctness question sitting under the advisor.

**THE FENCE, MEASURED ON THIS POPULATION AND CARRIED BY THIS ITEM.** Every changed matched value
in the local library is small at one end, so every CORRECT byte-order oracle must agree with the
magnitude prior on it. The continuity oracle built on 2026-08-23 is therefore a second
IMPLEMENTATION and not a second SIGNAL. **DO NOT SPEND A SESSION DESIGNING A CLEVERER
PREDICATE.** What separates two correct oracles is a save carrying LARGE integers that CHANGE,
which is an operator action rather than a design problem. The counts are in `docs/LEDGER.md`
under the 2026-08-23 CS-421 entries.

**DO NOT close this by carrying the joint result across.** `BYTE_ORDER_SURVIVING_CANDIDATES` is
a singleton, and the module refuses in writing to carry it to any single type: that carry needs
the premise that this format uses one byte order for every int32 field, and the module records
that premise as an assumption and not a measurement.

### Acceptance

both types' entries in `VALUE_BYTE_ORDER_STATUS` record a SETTLED order derived against the real save library, or the corpus is recorded as unable to settle them with the missing ingredient DERIVED in shipped data


## CS-827

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-23 by the CS-421 control-validity adversary, reproduced by the merger. Every reader outside `clockspeed/save/objects.py` selects by SYMBOL, so the yardstick moves with the data and the swap is invisible. **THE WORKED EXAMPLE IS ALREADY IN THE TREE AND IS THE POINT OF THE ITEM:** `tests/save/test_byte_order_status.py::test_the_status_words_are_pinned_and_distinct` does exactly this for the byte-order words and its docstring gives the reason - shipping status as DATA means something outside this repository reads the STRING. The evidence words have no such control.

### Acceptance

changing the STRING value of any member of the evidence vocabulary turns a test RED, proven by a mutant that renames one while leaving every symbol reference untouched


## CS-800

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: this file **CS-800 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 26) for budget, not deleted. The
item itself stays OPEN in `ROADMAP.md`.

CS-800 - A CONTAINER handed back by a function is not read as serving what it holds, while the same container at module scope is - acceptance: a module whose helper returns a container of locators, and whose consumer indexes that container and calls the result, turns a test RED on a machine with NO GAME INSTALLED, without flagging a helper that returns a container of computed strings - tier: 2

filed 2026-08-21 (session 26) as CS-492's disclosed residual, measured green three times. `reach_guard._hands_back_a_primitive` REFUSES a container and says so; `_stands_for_a_primitive` WALKS one, so `_TABLE = {"save": prim}` with `_TABLE["save"]()` is caught and `return {"save": prim}` with `_locators()["save"]()` is not. **THE REFUSAL IS NOT AN OVERSIGHT AND MUST NOT BE UNDONE BY SIMPLY TURNING THE ARM ON:** it was on, and it manufactured a FALSE REACHER on this tree twice, from two different channels - `test_phase4_gate._child_pytest_args` returns argv holding `str(SAVE_TESTS)`, and `test_workdir._child_pytest_args` returns argv holding the bare name `_MODULE_NODE_ID`. Both are path CONSTANTS, which the vocabulary holds under `_stands_for_a_primitive`'s deliberate over-approximation, and both flagged tests that reach nothing. The root cause is that the vocabulary does not distinguish a callable from a value, and any real fix says how it will. A generator-expression serve and a list-index serve are the same gap one shape further out. `tests/save/test_reach_guard.py::test_the_object_routed_widening_does_not_flag_a_module_that_reaches_nothing[argv-built-from-a-path-constant]` is the control that reds if the arm is turned back on naively.



**ROUND FOUR WIDENED THIS ITEM.** It was filed as the served-container gap. By the time
CS-492 closed, the hand-back rule had been narrowed three more times, each time because the
previous shape manufactured a FALSE REACHER on the real tree, and the residual is now every
one of them:

- a CALL is not read at all, so `functools.partial(prim)`, `operator.methodcaller("glob")`
  and `getattr(account, "glob")` are not read as handing a locator back;
- a CONTAINER is not read;
- a SUBSCRIPT, a CONDITIONAL and an OVERRIDE-WITH-FALLBACK are not read - those arms existed
  and were deleted, because a mutation pass could not tell them from `return False` and they
  carried the same hazard as the rest.

**THE ROOT CAUSE IS ONE SENTENCE AND ANY FIX HAS TO ANSWER IT:** `_stands_for_a_primitive`
treats the RESULT of a primitive as standing for one, so the vocabulary holds path CONSTANTS
- `THIS_MODULE`, `SAVE_TESTS`, `_MODULE_NODE_ID` - alongside locators, and nothing syntactic
separates `partial(prim)` from `str(SAVE_TESTS)`. Four rounds of tuning arms is the evidence
that no arm will. **Do not reopen any arm without first splitting the vocabulary into
callables and values**, which is a change to that function's contract.

### Acceptance

a module serving a locator in any of those shapes, whose consumer calls it, turns a test RED with NO GAME INSTALLED, without flagging a helper serving a computed string or a path constant


## CS-801

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: this file **CS-801 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 26) for budget, not deleted. The
item itself stays OPEN in `ROADMAP.md`.

CS-801 - A `__getattr__` serving a locator is closed only where it is defined at MODULE scope and consumed in the SAME file - acceptance: a class-level `__getattr__` returning a locator, and a module-level one consumed from a sibling as `other.anything()`, each turn a test RED on a machine with NO GAME INSTALLED - tier: 2

filed 2026-08-21 (session 26) as CS-492's disclosed residual, both measured green and both classed SILENT, so the suite-wide guard never runs on the module at all. A `__getattr__` makes EVERY attribute of its namespace a locator, and neither vocabulary can express that today: `_reaching_attributes` learns the attribute name `__getattr__` itself and stops, and `_reaching_names_of` exports NAMES, so a wildcard cannot cross the module seam as one. Ranked ORDINARY by the pass that found it - a proxy or lazy-attribute class is the ordinary reason to write either. **A fix has to say what a wildcard looks like in a set of names**; the file's own `MODULE_SCOPE_REACH` sentinel is the precedent for a member that is not an identifier.

### Acceptance

a class-level `__getattr__` returning a locator, and a module-level one consumed from a sibling as `other.anything()`, each turn a test RED on a machine with NO GAME INSTALLED


## CS-802

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: this file **CS-802 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 26) for budget, not deleted. The
item itself stays OPEN in `ROADMAP.md`.

CS-802 - A store whose attribute NAME is not a literal is not read - acceptance: `setattr(self, _NAME, locate.resolve_save_root)` with `_NAME` a module constant, and `self.__dict__.update(finder=locate.resolve_save_root)`, each turn a test RED on a machine with NO GAME INSTALLED - tier: 2

filed 2026-08-21 (session 26) as CS-492's disclosed residual and stated as a bound in `reach_guard._attribute_stores`. The three-argument store shape and the subscript store both key on a string LITERAL; resolving a name that arrives through a variable is the alias analysis this repo has declined, and `_module_scope_values` is the machinery that would have to do it. The keyword form is a fourth store spelling rather than a variable key and is the cheaper half.



**ROUND SIX RETIRED TWO SHIPPED CONTROLS INTO THIS ITEM, and the reason is the one thing
worth reading here.** `setattr(self, "finder", locate.resolve_save_root)` and a store through
a three-argument helper of one's own were both CS-492 controls, both measured open at HEAD,
and both are now accepted. What removed them was the THREE-ARGUMENT STORE SHAPE, which read
`f(target, "name", value)` as a store.

That shape is what `setattr` is. It is equally what `getattr(spec, "reader", open)`,
`re.sub(pattern, "count", text)` and `OSError(13, "denied", path)` are, and none of those
stores anything. It produced a FALSE REACHER in three separate refutation rounds, with a
different payload each time, and the last one defeated this package's own exclusion map:
`monkeypatch.setattr(os, "walk", os.scandir)` put `walk` into the attribute vocabulary, and
`walk` is excluded BY NAME because `ast.walk` is how every AST guard here reads a tree. One
ordinary three-line helper appended to `tests/save/test_phase4_gate.py` took it from nine
flagged functions to twenty - eleven functions that reach nothing, each forced into a written
claim about where personal data flows.

`_attribute_stores` had read 160 stores on the shipped tree; 127 of them were this shape. It
now reads 33.

**WHAT A FIX HAS TO ANSWER:** the shape cannot separate a store from a read, and keying on
the callee instead was measured too - it leaves every other store helper open while reading
as though it did not. Anything that reopens this door needs a way to tell `setattr` from
`getattr` that is not a vocabulary of callee names, or it needs the exclusion map to govern
the attribute namespace hard enough that a false entry cannot propagate. The second half
shipped in round six regardless: `_reaching_attributes` now refuses any name in
`_NOT_LIBRARY_REACH`.

### Acceptance

`setattr(self, _NAME, locate.resolve_save_root)` with `_NAME` a module constant, and `self.__dict__.update(finder=locate.resolve_save_root)`, each turn a test RED on a machine with NO GAME INSTALLED


## CS-803

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: this file **CS-803 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 26) for budget, not deleted. The
item itself stays OPEN in `ROADMAP.md`.

CS-803 - A closure built by a nested `def` is not read as serving what it closes over - acceptance: a module whose factory returns a nested function that reaches the library, and whose consumer calls the factory's result, turns a test RED on a machine with NO GAME INSTALLED even when the factory itself is declared - tier: 2

filed 2026-08-21 (session 26) by a refutation pass on CS-492 round two, measured: the consumer HOLDS THE REAL SAVE ROOT and is accepted. `_returned_values` excludes nested definitions deliberately - an inner helper's returns are not the outer function's - so the factory is never a serve. The IDENTICAL idiom spelled with a `lambda` IS caught and names the consumer, which is what makes this one mechanism applied to part of its population rather than a stated bound. Ranked ORDINARY. **Do not close it by deleting the nested-definition exclusion in `_returned_values`** - that exclusion is load-bearing for the opposite case and its reason is in the docstring.

### Acceptance

a module whose factory returns a nested function that reaches the library, and whose consumer calls the factory's result, turns a test RED on a machine with NO GAME INSTALLED even when the factory itself is declared


## CS-804

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: this file **CS-804 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 26) for budget, not deleted. The
item itself stays OPEN in `ROADMAP.md`.

CS-804 - A sibling's graded `Class.method` declaration can never match a callee, so the cross-module export is keyed on a spelling nothing resolves - acceptance: an importer calling a sibling's declared reaching METHOD turns a test RED on a machine with NO GAME INSTALLED - tier: 2

filed 2026-08-21 (session 26) by a refutation pass on CS-492 round two. `_scanned_functions` keys a method `Class.method` and `_reaching_names_of` exports that key verbatim; `_callee_resolves` tests `func.attr`, a bare attribute name, which can never equal a dotted key. Latent rather than live - no tracked module declares a dotted graded name today - and it sits at the same module seam CS-492 round two repaired for functions, which is why it is filed rather than folded in.



**ROUND FIVE WIDENED THIS ITEM FROM ONE SPELLING TO THE WHOLE EXPORT SET.** It was filed as
the dotted-key mismatch. A refutation pass then measured two more holes at the same seam, both
ORDINARY, both with the sibling GREEN and the importer classed SILENT:

- **The sibling's SERVER.** `_reaching_names_of` returns `graded & (direct | indirect)`, and a
  function that HANDS BACK a locator calls nothing, so it can never be in `direct`. Worse, the
  sibling **cannot declare it**: adding it to `_GRADED_LIBRARY_REACH` reds the sibling with
  `a graded helper no longer reaches the library`. There is no declaration that fixes this.
- **The sibling's HELD ATTRIBUTE.** The export is a set of NAMES; the attribute vocabulary is
  never exported at all, so an importer calling `sibling._Holder().finder()` resolves nothing.

Measured side by side against a consumer spelling the same reach directly, which IS named.
CS-492 round two repaired the vocabulary INSIDE `_reaching_names_of` and left the EXPORT SET
unrepaired - one mechanism applied to part of its population, at the module seam, for the
second time in the same item.

**THIS SUBSUMES WHAT CS-801 SAYS ABOUT A CROSS-MODULE `__getattr__`:** that is one instance of
the server hole, not a `__getattr__`-specific one. Whichever item is taken first should say so.

**ALSO MEASURED AND NOT FILED SEPARATELY, both CONTRIVED:** `(await holder.finder)()` and
`(finder := locate.resolve_save_root)()` are accepted - `_callee_resolves` has no `ast.Await`
and no `ast.NamedExpr` arm. The ordinary spellings of both are caught by the inner call.

### Acceptance

an importer reaching through a sibling's server, through a locator the sibling holds on an attribute, or through its declared reaching METHOD, each turn a test RED with NO GAME INSTALLED


## CS-805

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: this file **CS-805 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 26) for budget, not deleted. The
item itself stays OPEN in `ROADMAP.md`.

CS-805 - The container-FIELD personal-data shape is not walked as a wrapper, and the footprint is wider than CS-492's detail block records - acceptance: a class holding a save body in a CONTAINER field, and a helper whose return annotation is a container of bodies or of stringified real save paths, each turn a test RED on a machine with NO GAME INSTALLED - tier: 2

filed 2026-08-21 (session 26). This is the PERSONAL-DATA half of the guard, `reach_guard._body_wrapping_classes` and `_returns_personal_data`, not the reach half CS-492 closed, which is why it is a separate item rather than that item's acceptance. Named in this file under **CS-492 - detail** as "ALSO HERE, and NOT contrived". A refutation pass measured all of it open and found one shape the note does not mention: a return annotated `-> list[str]` carrying stringified real save paths passes strict typing and propagates nothing. Measured caught for contrast: `-> bytes` and a `bytes`-typed field.

### Acceptance

a class holding a save body in a CONTAINER field, and a helper returning a container of bodies or of stringified save paths, each turn a test RED with NO GAME INSTALLED


## CS-807

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-807 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 27) by operator decision, splitting the FALSE-FLAG direction out of
CS-492. Every measurement below was taken by the merger or reproduced by it independently, on a
machine with no game installed.

**WHY IT IS ITS OWN ITEM.** CS-492's acceptance is ESCAPE-SHAPED - it asks that a route through
an object turn a test RED - and says nothing about flagging a module that reaches nothing. Yet
the false-flag direction is what refuted ALL NINE of its rounds. A direction that keeps doing the
refuting needs an owner, or it goes on being fought inside an item whose acceptance cannot record
whether it was won.

**A DECLARATION IS A WRITTEN CLAIM ABOUT WHERE PERSONAL DATA FLOWS.** Manufacturing one is worse
than missing a route. That is the whole reason this direction outranks the escape direction, and
it is why this item is tier 1 while CS-492 is tier 2.

**FOUR FALSE DECLARATIONS ARE LIVE ON THE SHIPPED TREE TODAY.** `tests/save/test_oracle_citations.py`
carries seven exemptions; four of them read, in their own reason strings, "matched by NAME and not
by a filesystem call: it uses this module's own citation resolver, which is spelled resolve ... It
opens no file and touches no path at all". Those four exist ONLY because the guard falsely flags
them. The guard was not repaired; the false flags were written down and shipped. Measured: with
either narrowing spike below, dropping those four leaves the module clean, and the only functions
still flagged are the three that genuinely `rglob` this repo's own sources.

**THE SENTINEL IS THE LARGEST SOURCE BY A FACTOR OF THIRTY AND ITS MAGNITUDE APPEARED NOWHERE IN
THE TREE.** `_ANY_ATTRIBUTE` has been carried as a disclosed residual since round seven. Measured
by the merger, five ordinary lines of PEP 562 - a deprecation alias serving the save-root finder
under its pre-rename spelling - planted into six real modules:

| module | flagged before | after | manufactured |
|---|---|---|---|
| `test_phase4_gate.py` | 10 | 78 | 68 |
| `test_properties.py` | 5 | 69 | 64 |
| `test_workdir.py` | 18 | 77 | 59 |
| `test_value_anchoring.py` | 4 | 43 | 39 |
| `test_absolute_claims.py` | 3 | 28 | 25 |
| `test_oracle_citations.py` | 7 | 20 | 13 |
| TOTAL | 47 | 315 | **268** |

The bare-name class that consumed nine rounds manufactures EIGHT. "Disclosed" was doing more work
than it can bear.

**THE BARE-NAME CONFLICT IS MEASURED IRREDUCIBLE - do not spend a tenth round on it.** Two spikes
were measured against round nine, both leaving the receiver rule, the attribute path and
`_LIBRARY_LOCATORS` untouched:

- FIVE-SITE (`_bare_resolves` at every bare-`ast.Name` vocabulary site) and TWO-SITE (only
  `_hands_back_a_primitive`'s bare arm and `_callee_resolves`' bare arm).
- BOTH take every manufactured-declaration payload to ZERO, including `import stat` plus the
  exec-bit constants, which is verbatim real repo code at `scripts/install_hooks.py:44` and `:206`.
- BOTH cost the SAME TWELVE controls. Narrowing the site count retires NONE of them. The
  mechanism was verified rather than inferred: the patched arm is the ONLY consumer of evidence
  for a bare vocabulary word, so leaving the other arms reading bare names buys nothing.
- BOTH leave the sentinel's 268 untouched.
- TWO-SITE DOMINATES FIVE-SITE: same kills, same reds, a smaller diff, and it keeps one route the
  five-site loses (`stat = os.stat; _alias = stat; _alias()`).

**THE CONFLICT, STATED.** `test_a_parameter_spelled_like_a_primitive_binds_nothing_and_serves_nothing`
demands BOTH that `stat` as a PARAMETER manufacture nothing AND that `stat = os.stat` at module
scope BE CAUGHT. Same token, name-keyed guard. Telling them apart requires knowing what the name
is BOUND TO, which is the type resolution this repo has declined - see CS-491's note, "do not
close this by widening the name list alone". Nine rounds were attempts to split that hair. The
measurement says it does not split. **Any acceptance here must say which side it buys, and pay for
it in the open.**

**DO NOT close this by deleting the twelve controls.** They were written to assert bare-name reach
is caught, and one of them exists specifically to defeat a guard that passes the caption case by
accepting nothing. Deleting them to go green removes the only instrument that distinguishes this
repair from a vacuous one, which is a worse repository than one with eight manufactured
declarations in it.

**THE SWEEP IS TAKEN - 2026-08-22, session 29. THE ANSWER IS SIX, NOT FOUR, AND THEY SIT IN TWO
MODULES RATHER THAN ONE.** The population is every `_EXEMPT_LIBRARY_REACH` and
`_GRADED_LIBRARY_REACH` mapping under `tests/save`, read by AST at module scope so payloads
planted inside string literals are not counted. No consumer of the guard exists anywhere else in
the tracked tree - the only other copies are the four uncommitted worktrees.

| channel | entries | modules | false |
|---|---|---|---|
| `_EXEMPT_LIBRARY_REACH` | 45 (42 are functions, 3 are the module-scope sentinel) | 11 | **6** |
| `_GRADED_LIBRARY_REACH` | 20 | 7 | 0 |

The graded channel is CLEAN: all twenty entries genuinely read the save library, so every false
declaration on this tree is an exemption. The two NEW ones are `backing_citations` and
`dead_full_citations` in `tests/save/test_absolute_claims.py`, carrying the same reason string as
the four already recorded. **Both are HELPERS rather than tests**, which the four are not, so the
false-flag population is not confined to test functions the way the first finding suggested.

**TWO INDEPENDENT METHODS AGREE ON THE SAME SIX, and the second never reads a reason string.**
The first sweeps reason strings for a self-report that the function touches nothing. The second
takes the call node the guard actually trips on - `_call_reaches_a_primitive` under the module's
own `_reach_vocabulary`, per the granularity rule - resolves the callee ONE HOP to a def in this
repo, and asks `_calls_any` whether THAT def reaches. A function all of whose trips resolve to a
target reaching nothing is false whatever its prose claims.

**THE MECHANISM SPLITS, AND ONLY ONE HALF IS THE IRREDUCIBLE CONFLICT.** Measured per call node:

- FOUR trip on a bare `resolve()` at `test_oracle_citations.py` lines 653, 752, 764 and 775. That
  is the module's own module-scope `def resolve`, and `resolve` is in the NAME half of the
  vocabulary because `Path.resolve` is a primitive. This is the value-agnostic bare-name class,
  the one measured irreducible above.
- TWO trip on `citations.resolve()` at `test_absolute_claims.py` lines 656 and 717 - an ATTRIBUTE
  callee. `_callee_resolves` (`tests/save/reach_guard.py:1504`) answers the `Attribute` arm with
  `func.attr in effective or func.attr in attributes` and DISCARDS the receiver. The receiver is
  `citations`, bound at `test_absolute_claims.py:192` by
  `from tests.save import test_oracle_citations as citations` - a module alias resolvable from the
  import table without any type resolution.

**THE ATTRIBUTE HALF HAS A DISCRIMINATOR THE BARE-NAME HALF LACKS, AND IT IS UNMEASURED.** Do not
read this as a proposed fix. `_callee_resolves`' own docstring records that a receiver WALK was
tried and reverted because it put a library-reach requirement on thirteen functions that reach
nothing - but that walk WIDENED, counting any mention of a primitive-ish thing anywhere in the
callee. Using the receiver to NARROW, exonerating a call whose receiver resolves to a repo module
that owns no primitive, is the opposite direction and was never measured. It is a candidate, not
an answer, and CS-807's rule stands: any acceptance must say which side it buys and pay for it in
the open.

**WHAT THE SWEEP DOES NOT DECIDE, stated as a floor rather than a total.** The one-hop pass treats
a callee it cannot resolve in one hop - an object receiver, a two-hop alias - as genuine. Six is
therefore a floor on the false population, not a ceiling, and the reason-string pass is a floor on
the SELF-REPORTED false population only. A false flag whose reason string was written to read like
a genuine reach evades the first pass and is caught by the second only when it resolves in one
hop.

**THE ATTRIBUTE HALF WAS ATTEMPTED AND REFUTED THREE WAYS - 2026-08-22, session 29. DO NOT READ
THE SPLIT ABOVE AS "ONE HALF IS TRACTABLE".** That was this session's claim on the strength of the
receiver being resolvable from the import table, and three independent grading lenses refuted the
build it produced. The build is on branch `cs807-attribute-half`, base `77336e5`, NOT merged.

**BOTH NARROWINGS DIED THE SAME DEATH: AN ABSENCE READ AS EVIDENCE OF SAFETY.**

- VERSION ONE exonerated any attribute the sibling did not EXPORT as reaching. An export set is
  empty for many reasons that are not safety - an unreadable declaration is one, and this package
  has already shipped two modules in that state. It silenced a planted sibling binding
  `latest_save = workdir.latest_save` at module scope, which the shipped guard catches, and the
  whole `tests/save` suite stayed GREEN at 1204 passed across the change.
- VERSION TWO exonerated a name only when the sibling DEFINES it as a def measured not to reach.
  The measurement is `_calls_any` on the def's own body - the DIRECT half alone - while
  `_reaching_names_of` and `_assert_library_reach_is_declared` both carry an indirect half. The
  file therefore contradicts itself on one sibling: `_reaching_names_of` says `latest_save`
  reaches, `_harmless_defs_of` says it is measured not to, and the Attribute arm believes the
  second.

### Relocated from `ROADMAP.md` 2026-09-01

**THE OBJECT-ROUTED ESCAPE-ROUTE COUNT LIVED ONLY ON THE ITEM LINE, AND IT WAS
ALREADY STALE.** The line read "the fifteen object-routed escape routes recorded in
the detail block STAY CAUGHT". FIFTEEN is not a figure this section ever carried, and
`_OBJECT_ROUTED_REACHES` in `tests/save/test_reach_guard.py` holds NINETEEN labelled
routes today. **DERIVE THE POPULATION FROM THAT TABLE; do not carry either number
forward.** The acceptance now says "the object-routed escape routes recorded in the
detail block", which is this paragraph plus that table.

**THE ESCAPES, all caught on the parent commit and silent on the build.** The discovery hoisted one
line up behind a def wrapper; one more local hop; a decorator applying the reach; a held attribute,
which is CS-492's own recorded shape reopened at the new seam; and a sibling that DECLARES the
reach in its own `_GRADED_LIBRARY_REACH` being exonerated anyway. With any ordinary second reacher
present the module is classed reaching, the guard runs, and it passes GREEN with an undeclared
function that hands back the world name - so there is not even a vacuity hint.

**TWO DEFECTS WORTH CARRYING FORWARD WHATEVER HAPPENS TO THIS DIRECTION.**

- THE EXONERATION WAS KEYED ON A BARE RECEIVER NAME WITH NO SCOPE CHECK. A PARAMETER spelled like
  a module handle silences a plain `Path.resolve()` on a real account directory.
  `tests/save/test_absolute_claims.py:192` already binds `citations` as a module handle, so this
  is a name collision away rather than a contrived shape.
- A FOURTH SITE ASKS THE SAME REACH QUESTION. `_module_scope_reaches` was not given the new
  vocabulary, so the identical call at module scope MANUFACTURES a `<module scope>` declaration on
  a module that reaches nothing. Its own docstring already memorialises this shape as "one
  mechanism applied to one of two populations, for the fourth time in this item" - and the repair
  made it the fifth. **Count the sites from the source before claiming all of them are covered;
  `grep -n "_calls_any(" ` finds three and misses this one.**

**THE CONTROL LESSON, WHICH IS THE MOST TRANSFERABLE THING HERE. A control written to defeat
vacuity was itself vacuous.** It swallowed the guard's "vacuous" message through an
`if "vacuous" in said: return` branch, so on the repaired tree it passed WITHOUT EVER OBSERVING THE
GUARD REACH A VERDICT - and it passed with `_assert_library_reach_is_declared` gutted to a bare
`return`. Against a 16-mutant battery derived from the diff it had ZERO unique detection and was
strictly weaker than a test already in the file. **The symmetric instrument it declined to use is
`assert not _module_reaches(consumer)`**, which is not satisfiable by a gutted guard and kills two
of the mutants that survived. The companion escape control, by contrast, graded as a real
instrument with a clean unique kill.

**WHAT SURVIVED GRADING, and is therefore reusable.** The two exemption deletions in
`tests/save/test_absolute_claims.py` are CORRECT - verified by reading `backing_citations`,
`dead_full_citations`, `citations.resolve` and `prose_paragraphs` end to end rather than by running
the guard - and no shipped module goes silent on the build today. Every escape above is
prospective.

### Acceptance

on a machine with NO GAME INSTALLED, a module-scope `__getattr__` that genuinely serves a locator flags NO function that reaches nothing; the false exemptions the sweep measured in `tests/save/test_oracle_citations.py` and `tests/save/test_absolute_claims.py` are DELETED with both modules still clean; and the object-routed escape routes recorded in the detail block STAY CAUGHT, so the acceptance cannot be met by a guard that accepts everything


## CS-808

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: found 2026-08-22 (session 29) by the CS-807 permissive-failure refuter, OUTSIDE its brief, and reproduced independently on `main` by the merger: a planted sibling read as harmless, rewritten at the same path to reach the library, still answered `[]` until `cache_clear()`, which then answered `['sweep']`. **IT IS LATENT TODAY, NOT LIVE** - pytest's per-test `tmp_path` gives each control a fresh path, which is exactly why no existing test sees it. It becomes real the moment a control plants two sibling versions at one path, which is a natural thing to write and would fail in the direction that reads as SAFE.

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`_reaching_names_of` and `_wrapping_names_of` are `@cache`d on a `Path`, so a stale parse answers for a changed file at the same path

### Acceptance

a probe planting two different sibling versions at ONE path gets the SECOND version's answer, with a reproduction recorded either way

