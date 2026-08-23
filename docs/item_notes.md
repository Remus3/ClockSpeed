# Clockspeed - live per-item detail

**This file owns the LIVE per-item detail for OPEN work.** One section per item ID.
A block here is a LIVE INSTRUCTION: read an item's section BEFORE taking that item.

`ROADMAP.md` owns the item LINE and nothing else - the ID, the headline, the acceptance
criterion and the tier. Everything that used to trail that line as a NOTE body lives
here, and every live instruction block that had accumulated in `docs/history_notes.md`
lives here too.

**This file NEVER contains:** the item line itself, a completion record (`docs/LEDGER.md`
owns those), an aspirational item (`BACKLOG.md` owns those), the external condition
blocking a gated item (`docs/GATED.md` owns that), or history. **When an item CLOSES its
section moves to `docs/history_notes.md`**, because at that point it IS history - that
move is what keeps this file live and that file's header true.

**Bodies are relocated VERBATIM.** They are not edited, summarised, trimmed or
re-ordered. A body therefore still reads as it did when it was written, including the
parts a later session measured false and corrected in place rather than rewriting.

**ONE EXCEPTION TO VERBATIM, AND IT IS THE ONLY ONE.** The relocation FALSIFIED every
pointer that sent a reader to `docs/history_notes.md` for a block the same relocation moved
into THIS file - usually into the same section as the pointer naming it. Those pointers were
repointed at this file on 2026-08-23, as one mechanical substitution over the whole derived
population, and nothing else in any body was touched. THE FIRST SWEEP OF THAT POPULATION WAS
INCOMPLETE: it keyed on the block name `<ITEM> - detail` and so walked straight past
**CS-454 - status detail**, which is the same defect in miniature - a population derived from
the shape in front of you rather than from the shape itself. A pointer that still names
`docs/history_notes.md` names a block that is genuinely still there.

`docs/upstream_watch.md` owns the CS-486 upstream watch list, which is a standing watch
rather than per-item detail, and CS-486's section below points at it.

---

## CS-210

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-210 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

this is the COMMON-MODE RISK named by the ADR 0006 adjudication on 2026-08-14. Both fences that ADR relies on read the SAME hand-authored corpus, so the registry-layer and solve-layer tests are one fixture read twice rather than two independent confirmations. That a registry-published `Building` can lack `mMaxPotential` AT ALL is asserted nowhere against the shipped data: the version pin records per-value counts (`"1.000000": 62`) but not WHICH entries carry the key, and ADR 0005 measured 62 entries carrying it while `clockspeed/data/registry.py:84-85` states 6 power-bearing entries carry no exponent - whether those sets overlap is unknown. It fails safe, because None cannot invent a number, so this is a premise risk rather than a correctness bug.

## CS-301

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: phase 3 deliberately refused to invent this. The semantics of `mVariablePowerConsumptionConstant` and `mVariablePowerConsumptionFactor` are unmeasured anywhere in this project - the registry only carries them - so `power.py` hands all four operands back verbatim and applies no law (non-negotiable 7). The two uncovered branches are stated honestly in that module rather than implied to be tested: no fixture building declares a base below the reference clock, and no fixture recipe names two producers.

## CS-303

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: raised by the ADR 0006 adjudication on 2026-08-14 as a roadmap candidate and explicitly NOT as a condition of that acceptance. Nothing mechanical currently stops a caller reading the field directly and clamping without going through `clamp_to_unsharded_base`; the ADR claims the name and the docstring as the fence and claims no more. Note that `tests/solve/test_synthetic.py::test_every_building_carries_the_unsharded_clock_base` reads the field directly by design and is one of the exemptions.

## CS-302

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: that diagnosis costs O(rows) extra exact solves and runs only on the refusal path. It was reasoned acceptable for optimizer-sized recipe sets and NOT measured at real scale, which is a stated limit rather than a claim.

## CS-400

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**CS-400 STAYS OPEN ON DEPTH.** **RULED BY THE OPERATOR 2026-08-23: CLAUSE 1 WAITS UNTIL A BUILDING'S INVENTORY IS ACTUALLY READABLE**, and CS-413's closure does NOT close it. The ruling is stated by SUBSTANCE and not by item id because its first version named an item on a premise measured false the same day. Detail relocated 2026-08-23 to this file under **CS-400 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

**CS-400 STAYS OPEN ON DEPTH, NOT ON COVERAGE.** Clause 1's coverage half is MET and clauses 2,
3 and 4 remain MET, all gated by `tests/save/test_phase4_gate.py`. **RULED BY THE OPERATOR
2026-08-15 (session 6): a skeleton walk does NOT satisfy clause 1.** The superseded session-5
coverage STATUS and the skeleton-grammar paragraph are relocated here too. Pillar 3, the
whole-world audit this phase exists to feed, needs inventory, clock speed and connection state,
and every one of those lives in the payload. The honest reading is that phase 4 can now
enumerate a world but not inspect it.

The ruling had two mechanical consequences. The object payload grammar was filed as **CS-413**,
its own item and the natural successor to CS-407 - **CS-413 CLOSED 2026-08-23**. And phase 5
did not open until a record's properties could be READ - **SUPERSEDED 2026-08-23** by a later
operator ruling recorded under CS-500, which opens phase 5.

**THE LINKAGE SENTENCE WAS MEASURABLY TOO STRONG, AND THE OPERATOR HAS SINCE RULED ON IT.** It read "Clause 1 closes when CS-413 closes, not before". CS-413 has closed on its
three acceptance clauses, every one of them graded against the real library. **CLAUSE 1 IS NOT
THEREBY SATISFIED**, and closing it on that sentence alone would be the error CS-421 was caught
making one level down - honouring the letter of an acceptance while the thing it existed for is
unmet. Of the three fields this item names as pillar 3's needs, INVENTORY is not readable.
**IT IS NOT INSIDE A STRUCT INTERIOR** - a draft of this block said so and it was measured
false the same day; the chain is CS-831, then CS-830, then CS-829. Clock speed is decoded.
**RULED BY THE OPERATOR 2026-08-23, ASKED DIRECTLY: CLAUSE 1 WAITS UNTIL A BUILDING'S INVENTORY
IS ACTUALLY READABLE.** CS-413's closure does not close it. The reasoning ABOVE is the author's
and was put to the operator; what the operator ruled is the conclusion, and a draft of this
block wrongly presented the reasoning as theirs.

**THE RULING IS STATED BY SUBSTANCE AND NOT BY ITEM ID, AND THAT IS THE WHOLE LESSON.** Its
first version read "waits on CS-829", on the author's statement that inventory sits inside
`StructProperty`'s interior. **THAT WAS MEASURED FALSE THE SAME DAY** - no building record
carries an `InventoryStack`; a building holds an `ObjectProperty` reference to a separate
inventory component. The operator was given a one-blocker map when there are three, so the
ruling was re-put and restated in a form that does not depend on the author's decomposition
being right. The chain today is CS-831, then CS-830, then CS-829.

**DO NOT re-derive whether clause 1 closes with CS-413 - it is ruled.** What IS open is the
work in that chain.

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

## CS-829

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-23 as a residual of CS-413's close, REWRITTEN twice the same day. **THE FIRST WORDING WAS UNSATISFIABLE** - it asked for `InventoryStack` off a real BUILDING and no building record carries one. **THE SECOND WAS A LIVENESS FLOOR**, satisfiable by decoding `LinearColor` and never touching inventory - which is the exact defect that held CS-413 open for eight days, so an adjudicator refused it. **DISTINCT FROM CS-456**, which asks about the framing rather than the contents. Detail in this file under **CS-829 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-23 as a residual of CS-413's close; the item stays OPEN in `ROADMAP.md`. This
block is a LIVE instruction, not history.

**THIS ITEM WAS FILED ON A FALSE PREMISE AND REWRITTEN THE SAME DAY. READ THIS FIRST.** Its
first acceptance asked for `InventoryStack` to yield a decoded inventory off a real BUILDING.
**MEASURED over the real library: no building record carries an `InventoryStack` at all.** A
building holds an `ObjectProperty` REFERENCE to a separate inventory component, and the stacks
live over there inside a container property. Inventory is therefore behind THREE layers - the
cross-record join (CS-831), the container element framing (CS-830), and only then this item.
An operator ruling on CS-400's clause 1 was obtained on that false premise and has been
restated by SUBSTANCE rather than by item id as a result. **DO NOT re-pitch this as the
inventory item.**

**WHAT IT IS: the largest opaque region by count, and read by nothing.**
`StructProperty` is the largest opaque region by count in `UNMEASURED_PAYLOAD_REGIONS`. The
tag's declared size DOES bound it, so it is stepped over exactly and costs no synchronisation -
**the INTERIOR is what is unmeasured**. The struct's own type word is present in the tag, and
the shipped record names `InventoryStack` as the one pillar 3 needs for inventory.

**WHY IT IS FILED SEPARATELY FROM CS-456.** CS-456 asks whether a WRONG tag-extra width is
discriminated for the four types that ship one. That is a question about the FRAMING. This item
is about the CONTENTS of one of them. Closing either leaves the other open.

**WHERE IT SITS AMONG PILLAR 3's THREE NEEDS.** CS-400 names inventory, clock speed and
connection state. Clock speed is `FloatProperty` and decodes today. Connection state is
`ObjectProperty` and decodes today AS A VALUE, though FOLLOWING one to the record it names is
CS-831. Inventory is behind all three layers above. This item is the LAST of the three rather
than the first, which is the opposite of what its first draft said.

**DO NOT hand-write a struct vocabulary.** The observed type words are led by a handful of
names, and transcribing them is the hand-maintained list this project has repeatedly recorded
as the thing that rots. Derive the population.

## CS-830

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-23 and REWRITTEN the same day. **IT WAS THE FOURTH LIVENESS FLOOR AND THE REPAIR PASS THAT FIXED THE OTHER THREE SKIPPED IT** - an adversary caught that, which is this session's own transferable finding landing a fourth time. Its first wording asked for `an element` to decode, closeable by three single decodes while the 19910 `ArrayProperty`-of-`StructProperty` instances that hold the inventory stayed unmeasured. **THE THREE WORDS ARE NAMED RATHER THAN DERIVED, DELIBERATELY:** no shipped table equals that triple - every candidate over-includes `StructProperty` (CS-829) or `TextProperty` (CS-832) - so the second acceptance arm guards the transcription instead of pretending it is derived. **DISTINCT FROM CS-426 AND CS-456**, which cover the tag-extra WIDTH, and from CS-489, which grades PROSE.

## CS-833

### NOTE - filed 2026-08-23 by the CS-831 close

Filed as a residual of CS-831, which shipped the gloss rather than introducing it. THREE
SHIPPED SITES state it as a UNIVERSAL over the unresolved bucket: `ReferenceResolution`'s
class docstring, `resolve_references`'s docstring, and the CS-831 test module's header.
The sentence is that a reference resolving to nothing names an ASSET, and that
non-negotiable 7 therefore licenses skipping it.

MEASURED 2026-08-23 against the real library by two agents independently, and the counts
differ because their shape heuristics differ: SIXTEEN unresolved references carry an
EMPTY object path, and roughly one hundred more are save-object-shaped and carry a level
head that IS a known root of the same save. Neither is an asset. A null reference is not
content shipped with the game.

**THE COUNTS ARE NOT THE DEFECT - THE UNIVERSAL IS.** CS-831's partition is right and its
buckets are right; what is wrong is a causal explanation attached to a whole bucket that
is false for part of it. An adjudicator considered DO-NOT-CLOSE on non-negotiable 7 for
exactly this and ruled it a documentation defect rather than a handling defect, because
the references ARE flagged in a named counted bucket and NN7 does not require the flag to
carry a correct reason. Do not re-litigate that ruling; fix the sentence and split the
count.

## CS-834

### NOTE - filed 2026-08-23 by the CS-831 close

CS-831 resolves TOP-LEVEL `ObjectProperty` tags - the ones its property walk steps over.
That boundary is real, is correct for CS-831, and is stated NOWHERE a reader of
`resolve_references` would find it.

MEASURED 2026-08-23: a raw byte scan for the length-prefixed type word finds far more
occurrences than the walk reports, and the merger independently confirmed that ZERO of
them fall outside every record extent - so the excess is entirely INSIDE payloads, in
regions the top-level walk steps over as opaque bytes. Those regions are `StructProperty`,
`ArrayProperty` and `MapProperty` values, which `MEASURED_VALUE_TYPES` excludes. A first
attempt to split that excess into nested-versus-outside was INVENTED and shipped as
measurement; the split is one number, not two, and the reason it looked measured is that
the two invented halves summed to the correct total.

**WHY THIS MATTERS BEYOND TIDINESS:** the inventory path runs through exactly those
containers. CS-830 and CS-829 own DECODING those interiors. Neither owns RE-SCOPING
CS-831's population, so when they land, a test still named
`test_every_object_property_reference_in_the_library_resolves_or_is_flagged` silently
becomes a statement about a subset. A THIRD class is also unowned: the actor head's
component list is stepped over by `_skip_actor_head` and never returned, so those
references are not unresolved - they are never decoded at all.

## CS-835

### NOTE - filed 2026-08-23 by the CS-831 close, raised by its adjudicator as the largest risk in the comparison

CS-831's confidence rests on two passes agreeing. THEY ARE NOT INDEPENDENT READERS.
Measured 2026-08-23: both share `_payload_text`, `_read_tag_header`,
`_MAX_TAGS_PER_PAYLOAD`, `_decode_value`, `_as_reference` and `_skip_actor_head`; both
abandon a payload on the same conditions; and the CS-831 repair deliberately tied
`objects.REFERENCE_TYPE_WORD` to the oracle module's own copy of the word, which kills
drift and GUARANTEES that one wrong word makes both passes wrong identically.

Every synthetic case in the module derives from ONE fixture builder in
`tests/save/test_properties.py`, so a wrong belief encoded in that tag builder is
invisible to all of them.

**SO THE REFERENCE COUNTS ARE ONE READER'S OPINION STATED TWICE.** The second join is
genuine evidence about the JOIN and is NOT evidence about the DECODER. The only thing
standing against a wrong grammar is the length-prefix redundancy argument. The module
states all of this plainly rather than hiding it, which is why it did not block the close.
A grammar-free count is measured IMPOSSIBLE without a second reader this project has
declined to build - see the CS-831 ledger entry - so the honest form of this item may well
be the recorded-limit arm rather than the second-count arm.

## CS-836

### NOTE - filed 2026-08-23 by the CS-831 repair adversary

MEASURED 2026-08-23 on a simulated no-game machine: making `resolve_references` skip a
reference whose object path is empty, instead of bucketing it, SURVIVES - the module
reports passed with the library cases skipped, while the skipped references vanish from
the partition. Only the library-backed cases catch it, and those skip on a clean clone,
which is the CS-426 shape all over again: the protection exists only on the one machine
that has the game installed.

The CS-831 module's own stated standard says a defect of this class must die on a bare box
too. This item is that test.

## CS-837

### NOTE - filed 2026-08-23 by the CS-831 repair adversary

`tests/save/test_absolute_claims.py`'s `FENCED_MODULES` holds `test_absolute_claims.py`
and `test_decode_oracles.py` and nothing else, so the CS-831 test module's prose is
ungoverned by the CS-420 quantifier fence. `clockspeed/save/objects.py` is not in it
either. That is how a false universal survived in `objects.py` across a whole repair pass
whose write-list included that file: nothing was watching the prose.

This is ADR 0008's unguarded tier, the same class as CS-437 and CS-422.

## CS-838

### NOTE - filed 2026-08-23 by the merger, against its own commit

MEASURED 2026-08-23, not reasoned. A commit was made in this session carrying a
`ruff format` violation. `tools/precommit_gate.py --staged` reported PASS on it, and the
FULL suite passed with the violation present - only an explicit `ruff format --check .`
found it. So neither tier-0 gate nor the suite enforces formatting, and the only thing
that caught it was a human running the checker by hand.

**THE FILE IS FROZEN.** An adjudicator grant recorded in `docs/LEDGER.md` comes BEFORE any
edit, per `CLAUDE.md` section 6. Note the standing constraint that applies to every change
to this gate: coverage may not be reduced to buy anything, and the only valid proof the
gate still blocks is end to end - stage a real violation, attempt a real `git commit`,
assert exit 1 and HEAD unchanged.

## CS-832

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-23, headline CORRECTED the same day: `Int64Property` is NOT in `DECLINED_VALUE_READINGS` - it is named by the `ArrayProperty` entry as an inner type and recorded in `UNMEASURED_PAYLOAD_REGIONS`, so 'declined' was the wrong word for it. **THE TEST CLAUSE IS LOAD-BEARING:** without it this closes by editing one string in a table, which is what the first wording allowed. `TextProperty` had ZERO mentions across `ROADMAP.md`, `BACKLOG.md` and `docs/GATED.md` before this item. Neither blocks pillar 3.

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
demands a word that MEANS SETTLED and says outright that `BYTE_ORDER_STATUSES` ships none today.
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

## CS-426

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-15 by the CS-420 adjudicator as the item it would take next, and independently confirmed by the control-validity adversary. FULL ENTRY relocated to this file under **CS-426 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-15 by the CS-420 adjudicator as the item it would take next, and independently confirmed by the control-validity adversary. **EVERY DISCRIMINATING TEST CS-420 SHIPPED IS LIBRARY-BACKED AND SKIPS WITH NO GAME INSTALLED.** Measured: with the new modules removed, the entire pre-existing suite exits 0 under `SetProperty 1 to 0` - it is blind to it - and `MapProperty 2 to 1` is caught by exactly one test, `tests/save/test_properties.py::test_every_measured_type_the_library_exercises_yields_at_least_one_value`, which is itself library-backed and therefore also skips on CI. So on a clone with no game, BOTH widths are unguarded. The one width evidence that runs everywhere is `test_both_tag_grammar_transcriptions_agree`, which compares the two TRANSCRIPTIONS and is blind by construction to a fault they share. **This is the CI half of the common-mode question and it is genuinely open**, unlike the real-library half, which session 8 measured to be already guarded - see the corrected note in `WAKEUP_NOTES.md`. Do NOT close this by asserting the fixture round-trips through our own loader: session 6 measured that a round trip cannot distinguish "matches the game" from "matches our reader", and a fixture packed with the same belief the reader unpacks with agrees by construction. **AMENDED 2026-08-16 (session 9): the scope GREW.** CS-420 shipped test_every_tag_width_is_caught_by_a_library_backed_oracle, which derives the whole width-to-detector relation and is ALSO library-backed, so it skips on a clone too. The CI gap is now the width discriminators AND the artifact that grades them. Note also the defect CS-420 found and fixed while here: those tests gated their skip on the SAVE library while the usmap comes from the INSTALL, so on a machine with saves and no install they FAILED rather than skipped - check any fixture built for this item against that configuration, not just against a bare box.

## CS-432

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-420 builder as a stated residual of its own work, which is the correct place for it. FULL ENTRY relocated to this file under **CS-432 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-420 builder as a stated residual of its own work, which is the correct place for it. TWO SEPARATE PROBLEMS SHARING A FILE. FIRST, `_JOIN_WORD_FLOOR = 13` sits exactly at the pristine observed distinct-word count, and the join oracle's own liveness assertion still reads it. If this operator's world ever spans enough joined type words that no single-width mutant falls below 13, that assertion goes RED ON A CORRECT GRAMMAR. It is a FALSE RED and loud rather than a false green, which is why it ships rather than blocks, and the attribution test already avoids it by comparing against a pristine baseline measured in the same run - a single sweep has no baseline to compare against, which is why the fix is not simply copying that. SECOND, and structural: the cross-section oracle detects 0 of 6 widths, so `test_every_tag_width_is_caught_by_a_library_backed_oracle` cannot protect it - an oracle that detects nothing is indistinguishable from one gutted to a green no-op, and gutting it was measured to leave the suite passing. Its guard has to come from the fault class it IS sensitive to, the value-start rotation, not from the width attribution. **SHARPENED 2026-08-16 by the final audit, and it is worse than filed: the FLOOR'S JUSTIFICATION IS ITSELF FALSE.** Per-save distinct joined type words across the live library run 8 to 12 and NOT ONE SAVE REACHES 13 - the 13 is a UNION over a growing library, never the engine constant the docstring claims. Within the SAME version pair, 1239 records gives 8 words and 19837 gives 11, so "playing the game moves the tag count and leaves this alone" is exactly backwards. `NameProperty` is contributed by only 3 of the 12 tagged saves, so autosave rotation retiring those three turns `assert sweep.join.words >= 13` RED ON A CORRECT GRAMMAR - a live fragility, not a hypothetical. The companion claim "measured at the full observed width, so a thinned join cannot satisfy it" is refuted by a join thinned 3447 tags that satisfies it. **AMENDED 2026-08-16 (session 10) with a CLEANER counter-example and a NEW measured hazard, both re-derived by two agents independently.** FIRST, the cap-4 thinning already recorded here is beaten by `_MAX_TAGS_PER_PAYLOAD = 8`: it rots 1550 payloads with `join.tags` **IDENTICAL** at 55496 and `join.words` unmoved at 13 - a strictly cleaner demonstration that the distinct-word count does not track the thinning, because the tag count does not move at all. Note the pairing for whoever writes the replacement prose: cap 8 supports "a mutant rots payloads with the count unmoved" and does NOT support "drops thousands of tags", while cap 4 supports the second and not the first. Per-save distinct joined word counts measured across the library are `[8,8,8,8,8,8,8,11,11,12,12,12]`, every one below the floor of 13, which is the corpus-coupling this item exists to remove. SECOND AND NEW: **the floor's hazard is not confined to the join oracle.** Setting `_JOIN_WORD_FLOOR = 14` - which simulates autosave rotation retiring a rare word, the exact hazard - turns TWO tests red, not one: the join oracle at `assert 13 >= 14`, AND `test_every_tag_width_is_caught_by_a_library_backed_oracle`, which calls the join oracle inside its `already_red` check and dies with a message about mutants that never mentions the floor. So the attribution test does not avoid the hazard, it INHERITS it, and it fails misleadingly. The sentence claiming otherwise was deleted in session 10 rather than rewritten, per ADR 0008; the replacement is a detection claim and belongs to whoever closes this item.

## CS-425

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: **FROZEN-FILE GRANT ISSUED BY THE OPERATOR 2026-08-15 for `.claude/settings.json`, recorded in `docs/LEDGER.md` BEFORE any edit.** NOTE: the cause is MEASURED rather than reasoned. FULL ENTRY relocated to this file under **CS-425 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

**FROZEN-FILE GRANT ISSUED BY THE OPERATOR 2026-08-15 for `.claude/settings.json`, recorded in `docs/LEDGER.md` BEFORE any edit.** NOTE: the cause is MEASURED rather than reasoned. The `PreToolUse` hook runs `python tools/precommit_gate.py --text-stdin` on matcher `Bash|PowerShell`, so it spawns a console-subsystem `python.exe` on EVERY shell tool call, timed at ~106 ms per spawn; Claude Code is a GUI parent holding no console, so Windows allocates a fresh one per child and it flashes for the life of the process. `PostToolUse` (`tools/edit_lint_check.py`) and the wired git hooks - `core.hooksPath` resolves to `.githooks` - are the same mechanism at lower frequency. **THE DEFECT IS COSMETIC AND THE FILE IS A TIER-0 PROTECTION PATH, so the ordering of those two facts is the whole item:** coverage may NOT be reduced to buy a cosmetic win, which specifically forbids narrowing the matcher or the scanned surface. `pythonw.exe` is the candidate worth testing first because it allocates no console, but it is NOT obviously safe - the hook reports through stdout and an exit code, and whether both survive a parent-supplied pipe under `pythonw` must be PROVEN rather than argued, since the failure mode is a gate that silently stops reporting. **A legitimate outcome of this item is that the file is left byte-identical**, because the real fix may be the parent's `CREATE_NO_WINDOW` spawn flag, which belongs to Claude Code and not to this repo. Record that as the finding rather than reaching for a worse in-repo change; an unused grant is a fine result and a weakened gate is not. **AMENDED 2026-08-15 (session 8) - THE ITEM IS NO LONGER COSMETIC, AND THE MERGER CONDITION "COVERAGE MAY NOT BE REDUCED" IS VOID BECAUSE THERE IS NO COVERAGE ON THAT PATH TO REDUCE.** Three measurements, each executed, established that the Claude-side hook cannot DENY (the protocol denies on exit code 2 and the gate exits 1), probably cannot SEE the command (the JSON envelope escapes a non-ASCII byte into a pure-ASCII sequence the charset scan cannot find, and the flag expects raw text), and demonstrably did NOT block end to end. **THE AUTHORITATIVE GATE IS UNAFFECTED AND WAS PROVEN GOOD** by a real staged violation and a real commit attempt, so the repo is not exposed and CLAUDE.md's "the Claude hooks are a convenience layer" is exactly right. What is wrong is that the convenience layer provides no convenience while costing a process spawn per shell call. The measurement detail is relocated to `docs/history_notes.md`. **OPERATOR RULING 2026-08-15: make it actually work** - parse the envelope so it sees the real command, and exit 2 so it genuinely denies. **Stated consequence, accepted deliberately:** shell commands carrying an em-dash, a smart quote or a secret will be REFUSED mid-session. **Do NOT take the `pythonw` route as a substitute** - it was measured a faithful drop-in (identical rc 3/0/1, identical stdout, identical BLOCKED diagnostic through a real pipe-and-wait, the earlier PowerShell result being an artifact of PowerShell not waiting on a GUI-subsystem binary), but shipping it ALONE would kill the flash while preserving a hook that silently does nothing, which is the false-guarantee class this project rates worse than the bug.

## CS-405

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: **UNBLOCKED 2026-08-15, BOTH BLOCKERS GONE, AND THE EXPERIMENT IS PARTLY ANSWERED ALREADY.** The object walk reaches real buildings across the whole local library and CS-413's decode half landed, so the superseded revision of this note - ... FULL ENTRY relocated to this file under **CS-405 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

**UNBLOCKED 2026-08-15, BOTH BLOCKERS GONE, AND THE EXPERIMENT IS PARTLY ANSWERED ALREADY.** The object walk reaches real buildings across the whole local library and CS-413's decode half landed, so the superseded revision of this note - which said the walk was a skeleton and no property VALUE was readable - is relocated to `docs/history_notes.md`. Measured in passing by the CS-413 builder and NOT adjudicated by it, which is the correct boundary: **`mInventoryPotential` decodes, 962 instances across three version pairs, as an OBJECT REFERENCE - a 2-tuple - and not as an integer slot count.** Read that carefully before mapping it onto the three outcomes, because it is not any of them yet: it refutes the naive form of YES (the component does not carry a bare count) without establishing NO (a count may live behind the reference, in the referenced record). Resolving that is this item's own slice. Note also that ObjectProperty is one of the type words backed by the cross-section oracle rather than by width alone, so the 2-tuple reading is among the better-evidenced parts of CS-413's decode - see CS-421 for which types are not. THREE outcomes, not two, and the third is the one a careless agent collapses into NO: YES, the serialized component carries a slot count, which is a direct measurement of ADR 0005's last operand and licenses a LATER slice writing `OVERCLOCK_POTENTIAL_SHARD_SLOTS` into `clockspeed/data/version.py` WITH the four-invariant drift-guard entry ADR 0005 requires - it does NOT license `power.py` publishing a ceiling in the same slice; NO, it is serialized and carries no slot count, which fully refutes ADR 0005 option (b) and is worth as much as YES; or INCONCLUSIVE, meaning no world in the library has a built overclockable building with that component serialized at all, in which case the probe DID NOT RUN and the answer is "not yet measured" - the operator ruled on 2026-08-14 that this is an acceptable outcome and is filed as a re-run against the world growing, NOT converted into either answer. Do NOT derive the number any other way: ADR 0005 fences four routes and the arithmetic one, `slots = (2.5 - 1.0) / 0.5 = 3`, FEELS derived because it uses only shipped values and is not.

## CS-412

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: raised 2026-08-15 by the CS-407 result. FULL ENTRY relocated to this file under **CS-412 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: raised 2026-08-15 by the CS-407 result. The prior session's resume note for header 13 / save 42 said "the grid preamble is measured", and that measurement was recorded NOWHERE in the tree - not in `objects.py`, not in `synthetic.py`, not in the ledger - so the slice resuming it had to re-derive it from scratch. **A partial recorded as an adjective is not resumable.** The successor structure already exists as `LEVELLED_LAYOUT_OPAQUE_SPANS`; this item is about proving it COMPLETE against what the parser actually skips, so a later slice inherits evidence rather than a sentence. ADDED 2026-08-15: fold in `tests/save/synthetic.py:1079-1082`, which claims count equality for "2945 of 2945 levels on the (14,52) corpus". That is TRUE but narrower than reality - it holds on 6171 of 6171 levels across all four pairs, measured under CS-413. Found by the CS-413 builder and left alone because the file was outside its write-list, which is the boundary working as intended. A claim that is true and understated still rots, because the next reader treats its scope as the measured limit. Two precedents this session argue for generating such counts rather than writing them: CS-413's own first revision put a WRONG level count into a shipped docstring with a TRUE claim attached to it, and CS-404's evidence table now records which widths are measured versus merely uncontradicted rather than asserting a number.

## CS-401

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-401 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

REWRITTEN 2026-08-14. The original acceptance ended "and the ledger treats an unknown token as a new world rather than failing", which is NOT SATISFIABLE IN PHASE 4: the ledger is `clockspeed/advisor/ledger.py`, which is phase 5 and does not exist. That clause moves to CS-500's acceptance, where the ledger exists. What remains here is the half phase 4 can actually prove, and it is the half that matters - the token is stable and the parser tolerates an unseen one.

## CS-439

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16. FULL ENTRY relocated to this file under **CS-439 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16. FIVE INSTANCES NOW - CS-417, CS-419, CS-430, CS-435, CS-438 - each a docstring promising a report over code that drops the value silently. **THE KEY IS MEASURED, NOT PROPOSED, and the first key tried FAILED the measurement, which is why this entry states both.** Key A, a reporting verb anywhere in scope, matches 292 of 298 functions on prose alone and the conjunction with the code half is also 54, so the prose half buys NOTHING - house style puts a reporting verb in nearly every module docstring. Key B, the verb in the function's OWN docstring minus a documented None-return contract, goes 298 to 106 to 25 to **12 candidates**, which is reviewable. **THE EVIDENCE THAT B IS REAL RATHER THAN PLAUSIBLE: it surfaces `clockspeed/save/workdir.py::_save_files` as a candidate, which is CS-438, FILED INDEPENDENTLY BY A DIFFERENT AGENT that did not build the key.** It also correctly classifies the CS-435 repair's own `usmap.text` and `usmap.resolve` as CONTRACT rather than candidates. Two known members to fold in: `workdir._mtime_ns` swallows `OSError` and returns 0, and `clockspeed/data/locate.py:531` reads the Steam library index with `errors="replace"` so a replaced byte silently drops a library and the install reads as absent. STATED LIMITS, from the agent that measured it: CS-430's real content - a warning that FIRES but whose SENTENCE is false - is not statically decidable and needs the runtime discipline instead; the CS-419 aggregation-key collision is detectable but on a DIFFERENT key and is a second, cheaper guard; and an UNDOCUMENTED silent loss is invisible to B by construction, because anchoring on the promise is exactly what buys the reduction.

## CS-440

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. The code shipped and the acceptance is met on NEITHER clause** - the subject delivered is a usmap POSITION, not a class, and the reason is a per-LOAD flag rendered as a per-ENTRY attribute. FULL ENTRY relocated to this file under **CS-440 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 as the stated remainder of CS-435, whose ledger entry names it. CS-435 closed on its written acceptance and its STATED DEFECT is not fully closed: a MODELLED class whose usmap name is undecodable STILL reports as unmodelled, and what changed is only that it is no longer silent. Two measured sites, both outside CS-435's write-list and neither touched: `clockspeed/save/world.py:919` builds `WorldWarning(source, code, detail, count)` and DROPS THE SUBJECT, so `name-0` never reaches a consumer and the world layer learns "some name did not decode" without learning which; and `clockspeed/save/objects.py:588` sets `REASON_CLASS_NOT_MODELLED`, "is not a class the supplied registry models", which is FALSE for this input and is the only member of `UNKNOWN_CLASS_REASONS`. This is a confident wrong answer surviving behind a correct warning, which is the non-negotiable 7 failure rather than the tolerated one. **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE - THE ACCEPTANCE IS NOT MET ON EITHER CLAUSE.** The wiring is not vacuous - forcing the registry-loss flag constant reddens 3 tests and dropping the subject reddens 5, both byte-verified - and no CS-419 aggregation regression was introduced, because the world layer does no dedup at all. **CLAUSE 1 FAILS: THE SUBJECT IS A USMAP POSITION, NOT A CLASS.** The subjects delivered are `name-0` and `schema-0`; the name at that position is the empty placeholder and the schema was dropped, so a consumer learns WHICH POSITION failed and still cannot name the class. The class name is precisely the datum destroyed, and no amount of threading recovers it. **CLAUSE 2 FAILS BY TOTAL COLLAPSE:** the reason is a per-LOAD flag rendered as a per-ENTRY attribute, so injecting ONE unresolved-name warning into the real mapping gave the weaker reason to 1152 of 1152 entries and the stronger to none. On real data the new reason never fires at all - the branch is synthetic-only today. **AND THE KEY IS UNDER-INCLUSIVE IN THE DANGEROUS DIRECTION, which is this item's own defect class reappearing:** two further real conditions drop a declared class while the flag stays False, so the world still ships the exact false sentence. An unknown PROPERTY TYPE leaves the cursor mid-entry rather than skipping the payload; and **a newer usmap version - the realistic one, a game patch bumping the schema layout - needs no alignment luck**, which is one of the two routes the builder excluded untested while saying "if either can drop a class, my key misses it". It does. A sibling is worse: the unknown-property-type path can INVENT a name the file never declared, which is then reported MODELLED with no warning at all. Five false sentences, one of them ASSERTED into a control that pins the false claim.

## CS-441

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY.** The narrow mechanism works and 26 of 46 spliced shapes escaped it. Measured against 7165 annotations, 0 real helpers sit in the blind spot today, so this is COVERAGE, not a live leak. FULL ENTRY relocated to this file under **CS-441 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 from the CS-438 adversary and CONFIRMED by the CS-438 repair with three byte-verified mutants. `tests/test_exception_rendering.py`'s `RenderVisitor` is scoped BY DESIGN to `except ... as NAME` handler bodies, and its own docstring states that `safe_exc_text(exc)` takes the exception as a parameter so its `str(exc)` sits outside every handler. Measured against `workdir._listing_problem(code, exc)`: `detail=str(exc)` gives 0 findings GREEN, `detail=exc.filename` gives 0 findings GREEN, and the same `str(exc)` inside a real handler gives 1 finding RED. The runtime behaviour is clean today, so this is a COVERAGE gap rather than a live leak - but the module that relied on it had ZERO direct tests until CS-438's repair added them, and the sweep is the enumerating guard the project trusts precisely because it has no list. Note the shape generalises: any helper reached from a handler and handed the bound exception is invisible, and nobody has counted how many exist. **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE.** The narrow mechanism works - a suffix-annotated parameter rendered whole IS now flagged, and the sanctioned-helper half SURVIVED every attack including two combined mutants aimed at the non-vacuity proofs, which are genuinely live. **WHAT FAILED: of 46 spliced shapes 26 ESCAPED, and seven whole-object leaks in one file left the suite green.** Three families, all measured: the annotation predicate is a NAME SUFFIX, so it misses 19 builtin exception types, `subprocess.TimeoutExpired` - which this project's own gate names as a leak type - and **five exception classes this repo already defines carrying `noqa: N818`**, so the predicate's foundation is already deliberately breached in-tree; an UNANNOTATED parameter is invisible; and the exemption is reachable by `not isinstance(...)`, by `isinstance(...) or flag`, and by a locally-defined `OSError` SUBCLASS whose `__str__` appends the filename, which refutes the stated reason that a module defining a type can promise its message. **THE ITEM'S OWN "no list to keep up to date" CLAIM IS FALSE:** three dicts in that file are keyed by PATH, so a brand-new leak appended to an already-listed file is absorbed silently - demonstrated in `tools/drift_guard.py` and again in a waived test file, both green. Four false sentences and seven behaviour-changing green mutants against unbacked detection claims are recorded against ADR 0008. Measured against 7165 annotations in the tree: **0 real helpers sit in the blind spot today**, so this is coverage, not a live leak - one keystroke deep.

## CS-443

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: **THE UNFROZEN HALF WAS BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY.** Three claims survived hard attack; the acceptance itself failed - the reporting channel has ZERO production consumers, so end to end a bad config is still silent. NEEDS ITS OWN FROZEN-FILE GRANT for `tools/precommit_gate.py`. FULL ENTRY relocated to this file under **CS-443 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NEEDS ITS OWN FROZEN-FILE GRANT for `tools/precommit_gate.py`; the 2026-08-16 CS-436 grant is SPENT and covers CS-436 alone. NOTE: filed 2026-08-16 by the CS-436 builder, MEASURED and deliberately not fixed because it is outside CS-436's three enumerated parts. With a malformed `config/local.json`, `discover_world_names` recovered 0 declared names and emitted NO skip about the config; the only line printed advises the operator to "add world_names to config/local.json", WHICH THEY HAD ALREADY DONE. That is the CS-436 false-statement class one layer up - not silence, an instruction to do the thing that is already done and is being discarded. `local_config` takes no `report` argument at all, so there is no channel to report on. Fold in the CS-436 residual its repair flagged and did not widen into: when the header reader is unimportable and the root is NOT truncated, "no world token is discoverable" still prints beside "the save-header reader is not importable", which is the same two-lines-that-disagree defect the CS-436 repair fixed for the cap case. **THE UNFROZEN HALF WAS BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE.** Three claims SURVIVED hard attack: all six loss paths report, each code is pinned by its own reddening test, and absence plus a valid file stayed silent across 1500 measured invocations. A SEVENTH loss path that CRASHED rather than discarded was found and fixed - `UnicodeDecodeError` is a `ValueError`, not an `OSError`, and escaped a function whose docstring promises it never raises; confirmed independently against the pre-fix blob. **WHAT FAILED, and the first one is the acceptance itself.** (1) **THE CHANNEL HAS ZERO PRODUCTION CONSUMERS.** No caller in `clockspeed/`, `tools/` or `scripts/` passes the collector, so `scripts/verify_env.py` against a malformed config still exits 0 printing nothing about it. The acceptance says a bad config "is REPORTED rather than returning `{}` in silence"; against every shipped entry point it still returns `{}` in silence. A resolver fix is not a consumer fix, and CS-452 carries the seam. (2) **THE `detail` SENTENCE - the entire operator-facing content - HAS NO CONTROL:** replacing all six with a nonsense sentence left the module suite green, and giving the malformed case the oversize sentence also stayed green. Only truthiness is asserted. That is the CS-430 class exactly. (3) **THE SUBJECT'S REDACTION FAILS OPEN TWICE** - it reads only the environment, and `_RESOLVED_ACCOUNT_NAMES` is lazily seeded so the same input redacts or does not depending on call order, with the config read running FIRST in the resolve chain. Its control is structurally blind because the oracle and the redactor share their only input. (4) Four sentences measured false, one of them the merger's. (5) FOUR further silent paths remain: an empty or whitespace value dropped later by `_override`, a duplicate key, and - the most likely operator error of all - a mis-typed or mis-cased key, returned faithfully and read by nobody.

## CS-444

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY by a security adversary.** The fail-open is closed only INSIDE `_forbidden_roots`; see CS-449 for the seam below it and CS-454 for the personal-data echo path it added. FULL ENTRY relocated to this file under **CS-444 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-438 builder, which found it while sweeping its own file and reported rather than widened. **THIS ONE IS SECURITY-RELEVANT AND SITS DIRECTLY ON A NON-NEGOTIABLE.** The guard is `if resolved is not None`, so a save root that fails to resolve NEVER REACHES THE REFUSE LIST, and a copy could then land inside it. Non-negotiable 1 is never write to the game install or the save directory, and `clockspeed/save/workdir.py` is by deliberate design THE ONLY MODULE IN THE PACKAGE WITH A WRITE - `docs/ARCHITECTURE.md` records that this is what makes the invariant statically checkable rather than a rule reviewers must remember. A fail-open in the refuse list is therefore a hole in the one mechanism the architecture relies on. Same silent-loss family as CS-439 and it should be fixed whether or not CS-439 lands, because the failure direction here is a WRITE rather than a missing report. **BUILT 2026-08-16 (session 12) AND REFUTED THE SAME DAY BY A SECURITY ADVERSARY THAT WROTE NONE OF IT. THE CODE SHIPPED AND THE ITEM DOES NOT CLOSE.** `ForbiddenRoot` now carries a nullable resolved path so "present but unresolvable" is representable, and the refusal fires on it. Two claims SURVIVED byte-verified mutation: reverting only the producer reddens 5 tests, reverting only the consumer reddens 4, and the harness control discriminates rather than passing for the pre-existing destination check. **TWO CLAIMS DID NOT.** (1) "The fail-open is closed" is TOO WIDE and must read "closed INSIDE `_forbidden_roots`" - see CS-449, whose reachability the adversary MEASURED rather than left open. (2) **THE REFUSAL MESSAGE IS A NEW PERSONAL-DATA ECHO PATH AND ITS CONTROL IS VACUOUS** - see CS-454. Gutting the redactor out of the new branch left the whole workdir suite green, because the control's own fixture uses an all-digit account name, which is the one shape the backstop catches unconditionally. That is a fixture built parallel to the implementation, and it is this project's own named failure class.

## CS-445

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 from the CS-438 repair, which measured them and correctly declined to make a unilateral prose edit inside a repair commit. FULL ENTRY relocated to this file under **CS-445 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 from the CS-438 repair, which measured them and correctly declined to make a unilateral prose edit inside a repair commit. ADR 0008 is now `accepted` and binds LIVING TEXT REPOSITORY-WIDE, while its mechanical fence is scoped to two modules in `tests/save/` - so these are in scope for the RULE and out of scope for the CHECK, which is exactly the breadth question the ADR's SCOPE clause reserves as separate work. **THIS ENTRY IS THE MEASURED POPULATION FOR THAT WORK, so a later slice inherits evidence rather than an argument.** `clockspeed/save/objects.py:890` documents `body_length` with a corpus-scoped universal, "never zero-length in any real save on this machine", RESTATED at `objects.py:2809` and again at `tests/save/test_objects.py:776` with no live guard - one measured fact in three places, which is CLAUDE.md section 4's own failure mode. Two "the only one" superlatives sit at `objects.py:1066` and `objects.py:1609`. Note the tension with CS-412, which wants unmeasured spans recorded AS DATA: the fix for a corpus-scoped universal is probably to derive it, not delete it.

## CS-446

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-446 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-16 by the CS-438 adversary and CONFIRMED by the CS-438 repair. `tests/save/test_phase4_gate.py:2089` declares `WRITER_WRITE_SURFACE` as a `frozenset[tuple[str, str]]`, so a sixth write duplicating an existing `(function, construct)` pair moves the raw site count from 5 to 6 and the test STAYS GREEN - measured by adding a second `open(mode="wb")` inside `_stream_copy`. The pin's own docstring claims a fifth mutating call is red, so the module contradicts itself about its own guard, which is the ADR 0008 shape outside `tests/save/`'s two fenced modules. Severity is real but bounded: the pin still catches a write in a NEW function, which is the more likely regression, and `clockspeed/save/workdir.py` remains the package's only writer. A set was the right shape for "which functions may write" and the wrong shape for "how many writes exist".

## CS-447

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 as CS-428's stated residual, measured rather than assumed, and deliberately kept out of that item because neither is a forced-failure render. FULL ENTRY relocated to this file under **CS-447 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 as CS-428's stated residual, measured rather than assumed, and deliberately kept out of that item because neither is a forced-failure render. **THE SESSION HEADER IS THE LIVE ONE AND ONLY ON LINUX:** pytest's `rootdir:` line prints the checkout path on EVERY run, pass or fail, and on a Linux CI runner the checkout sits beneath the runner account's home directory, so a home path is printed on every CI run of every lane. **THE LITERAL RUNNER PATH IS DELIBERATELY NOT WRITTEN HERE: the commit gate BLOCKED the first version of this entry for exactly that, which is CONVENTIONS section 10 and non-negotiable 3 doing their job on the entry that describes the leak.** It is harmless on this operator's machine because `C:\Clockspeed` is not under a home directory - which is LAYOUT LUCK and not a property of anything. The warnings summary is inside the region CS-428's own oracle scans but outside what its remedy can rewrite; CS-428 resolved that contradiction toward the statement and left the gap named and tested rather than implied. Also uncovered and confirmed by measurement: a collection error exiting rc 2, and `--co`.

## CS-448

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-22 (session 32) to this file under **CS-448 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

### Relocated 2026-08-22 (session 32) from `ROADMAP.md` - the CS-448 NOTE, verbatim

Moved for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`, which now
carries a one-line pointer here.

**ROOT-CAUSED 2026-08-16 (session 12) AND STILL OPEN.** The mechanism is the CHECKOUT LOCATION, not contention: a checkout sharing a large ancestor with the temp root makes pytest's rootdir climb, so collection walks the whole temp tree. Still open: whether tier-2 CI is actually exposed - measure `rootdir` inside a real job. **ONE ATTEMPT MADE AND IT FAILED FOR A NAMED REASON 2026-08-16, recorded so the next session does not repeat it:** a tier-2 `workflow_dispatch` on `8620238` went green on all five jobs INCLUDING both `full suite` jobs, which run under `-n auto` when xdist is available - so the flake did not fire that run. But the log carries **ZERO** occurrences of `rootdir` across 332 KB, because the lane invokes `pytest tests -q` and `-q` suppresses the header line that prints it. **A GREEN RUN IS NOT THE MEASUREMENT THIS ITEM ASKS FOR.** To actually measure it, the job needs a step that prints the rootdir the innermost probe computes - not a rerun of the suite. FULL ENTRY relocated to this file under **CS-448 - detail**; read it before taking this item.


NOTE: filed 2026-08-16 by the final adversary auditing merged main, and it is a LIVE TIER-2 CI RISK. **IT IS PRE-EXISTING AND NOT INTRODUCED BY THIS SESSION, WHICH IS ESTABLISHED RATHER THAN ASSUMED:** measured 1 failure in 3 runs at `76f6c82` AND 1 in 3 at `ee36d0d`, the same test both times, and `git diff --name-only 76f6c82 ee36d0d -- tests/save/test_synthetic.py` is empty. The tier-2 lane runs `-n auto`, so this is the lane that flakes. Mechanism as far as it was traced: the gate spawns a nested child pytest run, and that child fails at `tests/save/test_synthetic.py::test_a_failing_builder_call_renders_its_arguments` with a collection error in its own SUB-subprocess, taking 61 seconds against 28 warm. So it is a three-level process nest under parallel load, and the honest reading is contention rather than a logic fault. DO NOT close this by raising a timeout or by marking the test flaky - a nested run that fails under load is telling you the nesting is the cost, and CS-426 already wants a no-install path that runs everywhere. Note the interaction to check first: this session's CS-428 added report hooks that fire in every worker AND controller-side, so re-measure at a revision before and after that commit even though the flake predates it. **SOLVED 2026-08-16 (session 12). THE MECHANISM IS MEASURED AND IT IS NOT CONTENTION - IT IS THE CHECKOUT LOCATION.** The merger first reported 32 runs with 0 failures and concluded it did not reproduce. **AN ADVERSARY REFUTED THAT AND REPRODUCED IT SIX TIMES**, at BOTH cited revisions, with a signature byte-identical to the original evidence: 3 failures in 10 runs at `a267705`, 3 of 4 at `ee36d0d`. **THE MERGER'S 32 RUNS WERE ALL EXECUTED IN THE TWO LOCATIONS ON THIS MACHINE WHERE THE FAILURE IS STRUCTURALLY IMPOSSIBLE**, so they were a control rather than a null result - as were a further 460 runs the adversary took there, junit-verified to confirm the gate testcase actually ran in 20 of 20. **THE CHAIN, each link measured.** When the checkout shares a large ancestor with `tempfile.gettempdir()`, pytest's rootdir for the innermost probe climbs to the TEMP ROOT, and collection then walks the whole temp tree: the same probe with only the cwd varied took 0.4s from three ordinary locations and **42.7s from a clone under the temp root, 107x from checkout location alone**. During that walk a sibling xdist worker creates and destroys `%TEMP%\clockspeed_gate_*` directories through `tools/precommit_gate.py`, `os.lstat` on the vanished entry raises `FileNotFoundError`, collection is Interrupted, the sentinel is never printed, the level-2 child exits 1 and the gate goes red. **xdist supplies only the concurrent creator and deleter - it is NOT CPU contention, and the 42.7s walk happens single-process with nothing else running.** THE MERGER'S FIRST MECHANISM STORY WAS WRONG in both halves and its fixture count was wrong too - that file defines 12 sandbox spawns, not the seven the merger wrote. **WHAT SURVIVED THE REFUTATION:** the CI-history reading is confirmed independently - 7 tier-2 runs is the COMPLETE history rather than a first page, the one red was a different test, and the gate is NOT skipped on hosted runners. **WHAT IS STILL OPEN, and it is the only thing left:** whether tier-2 CI is actually exposed is UNSETTLED, because a hosted workspace probably does not share a large ancestor with its temp directory - but that is inference from this machine, which is the same species of inference this entry criticised. **Measure `rootdir` inside a real tier-2 job before closing.** Housekeeping that feeds the defect and should be fixed regardless: the temp tree held hundreds of stale `pytest-of-*` entries, and the bigger it grows the longer the walk and the wider the race window. Do not close by raising a timeout; the fix is to stop the rootdir climbing, which also removes the 100-second walk.

## CS-449

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-444 builder, which found it sweeping its own file and REPORTED rather than widened. FULL ENTRY relocated to this file under **CS-449 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-444 builder, which found it sweeping its own file and REPORTED rather than widened. **SECURITY-RELEVANT, SAME DIRECTION AS CS-444 - a WRITE.** `resolve_save_root()` returns None when its directory test is False, and a None root never becomes a candidate in `workdir._forbidden_roots()` at all, so CS-444's fix never sees this one: the hole is one layer below the layer just patched. **REACHABILITY IS EXPLICITLY UNMEASURED AND MUST NOT BE ASSUMED EITHER WAY** - it turns on which errnos the directory test swallows rather than re-raises, and the builder measured the SHAPE, not the exploitability, on 3.14/Windows only. Do not declare it unreachable without measuring on 3.13: CS-438 shipped exactly that error. **UPGRADED 2026-08-16 THE SAME DAY IT WAS FILED - THE REACHABILITY IS NO LONGER OPEN, IT IS MEASURED, AND IT REPRODUCES END TO END.** A security adversary drove a save root that is genuinely on disk, where the directory entry lists and `lstat` succeeds while `stat` fails: `is_dir()` answered False, `resolve_save_root()` returned None, `_forbidden_roots()` returned EMPTY, and a destination INSIDE that save root DID NOT REFUSE. `Path.is_dir()` applies no errno filter at all on 3.14, and the 3.12 filter already lists the same error, so the declared floor between them swallows it under either implementation. **HONEST LIMIT, STATED BECAUSE IT BOUNDS THE SEVERITY:** in that particular instance the destination is also unwritable, so the check is gone but the write would not land. The live variant is the transient one - the same call swallows sharing violations, access denials and not-ready errors identically, so a stat that fails at CHECK time and succeeds at WRITE time is the shape to fear, and the adversary could NOT construct a simultaneously-stat-denied-and-writable directory on this machine. A demonstrated MISSING CHECK, not a demonstrated write.

## CS-450

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-441 builder as a stated residual of its own work. Measured with byte-verified mutants: `exc.filename` yields no finding in a parameter-taking helper AND none inside a real handler, so it is not a parameter-scope gap at all but a named-field gap sitting identically on BOTH sides of the handler boundary, predating CS-441. It is genuinely undecided rather than merely unfixed - `tests/test_exception_rendering.py` ships a test asserting named-field renderings are NOT flagged, so a fix contradicts a shipped assertion and the two need ONE rule rather than a denylist. Same shape as CS-422: one file applying two evidence standards to itself with no stated rule.

## CS-451

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-441 builder, reported and not touched as outside its write-list. A THIRD redaction helper, and unlike the two the sweep knows about it contains by WRAPPER rather than a per-type allowlist: it renders the object whole and wraps the result. **Containment-by-wrapper is not AST-readable**, so the sweep cannot grade it and an exemption would be an assertion rather than a check. Fold in that redactor's recorded limit - it rewrites paths under a home directory and leaves an absolute path NOT under one untouched - so the containment is itself partial. Do not close this by adding the helper to an exemption list; a hand-maintained list is what rots.

## CS-452

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-443 builder, reported and not widened into because the return types are consumed outside its write-list. `resolve_game_dir()` returns a labelled pair carrying a reason such as "set but not a directory", while `resolve_save_root()` and `resolve_account_dir()` return a bare optional path and discard the reason. That discarded reason is exactly what CS-449 needs and exactly what CS-443 had to invent a channel to carry, so this is the seam under both rather than a tidiness item. Consumers: `clockspeed/save/workdir.py`, `scripts/verify_env.py`, `tools/facts_probe.py`. Note `workdir.py` also calls `local_config()` without CS-443's collector, so a discarded declaration is still silent there.

## CS-453

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-453 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-16 by the CS-444 security adversary, and **DELIBERATELY FILED AT TIER 2 RATHER THAN TIER 1 BECAUSE THE ADVERSARY'S FRAMING WAS WIDER THAN THE CODE.** Verified by the merger at `clockspeed/save/workdir.py:796`: `purge_work_dir` deletes through `_remove_quietly` with no refuse-list consultation, so a work root pointed inside the save tree is not refused on the way out the way it is on the way in. **WHAT BOUNDS IT, and this is why it is not tier 1:** `_is_module_copy` requires the entry to sit in this module's own copies directory AND carry this module's suffix, so it removes only files this module made; and `copy_save` refusing to write inside a forbidden root means such files should not exist there to begin with. The real defect is the ASYMMETRY and the fact that nothing states it - the write path is guarded, the delete path is not, and the module's own docstring explains the two naming conditions without ever saying the refuse list is skipped. Non-negotiable 1 covers writes to the save directory, and a delete is a write.

## CS-454

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-444 security adversary. FULL ENTRY relocated to this file under **CS-454 - detail**; read it before taking this item. **STATUS 2026-08-16 (session 15): BUILT, MERGED, ADJUDICATED, AND IT DOES NOT CLOSE. CLAUSE 2 MET, CLAUSE 3 MET, CLAUSE 1 NOT MET.** **The detail is RELOCATED 2026-08-18 (session 19), and is in this file under **CS-454 - status detail**, for the file's WARN budget. Relocated, not deleted, and it must be read before taking this item - it records which commits shipped, what the adjudicator ruled, and why clause 1 is the one still open.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-444 security adversary. **THIS IS A PRE-EXISTING LIVE LEAK, NOT ONE CS-444 INTRODUCED** - the adversary demonstrated it on an unpatched path as well - but CS-444 added a second echo path carrying it plus a green assertion saying it does not, which is worse than the bare leak. Measured in one supported configuration: the operator relocates saves via the env override and leaves the account directory undeclared. All three redaction rules then fall together - the positional rule needs a marker the relocation removed, the remembered-account list is fed only by an all-digit directory scan, and the digit backstop misses a hex token, a GUID and an operator-renamed directory. Epic-like, MS-Store-like and renamed account directories all rendered in plaintext; an all-digit one redacted. `clockspeed/data/locate.py` already names exactly those platforms as the reason not to rely on the digit rule. **THE CONTROL IS VACUOUS AND THAT IS THE HALF TO FIX FIRST:** removing the redactor from the new refusal branch entirely left the whole workdir suite green, for two independent reasons - the fixture's destination contains no account id at all, and its account name is all digits. Non-negotiables 3 and 12.

### status detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated 2026-08-18 (session 19) from CS-454's `ROADMAP.md` entry, which carried the file over its WARN budget. The item is OPEN and tier 1; its clause verdict stays in `ROADMAP.md` and only the supporting detail is here. Read it before taking the item.

The code shipped in `60068a9` and `02523f9` and STAYS - the relocated-path form is closed in all four resolution states, the 8.3 form is closed, and three independent vacuity reasons were removed from the controls. Full record in `docs/LEDGER.md` under the 2026-08-16 CS-454 non-closure entry. **FOUR THINGS REMAIN AND ALL FOUR ARE INSIDE THIS ITEM - do not file them as follow-ups, because a follow-up does not satisfy the clause it was filed against, which is what kept CS-422 open.** (1) **THE JUNCTION DEFECT, and it is in the NEW design rather than pre-existing:** `_remember_save_root` stores `_path_forms(str(path))` and never resolves, while `clockspeed/save/workdir.py`'s `_resolved()` deliberately does, so a save root reached through a junction can never match an anchor and a hex account directory rendered WHOLE through the production refusal in `_refuse_if_forbidden`. Reproduced with a real `mklink /J`. (2) **PLACEHOLDER INJECTION DEFEATS POSITION:** the environment pass runs first and rewrites a matching needle to a token, injecting `<` into the account segment; `_PATH_SEGMENT_CLASS` excludes `<>` so position cannot match and the name pass hunts a literal that is gone. With `USERNAME=Ada` and account directory `Ada4f3a...`, 30 of 33 characters render in plaintext WITH THE MARKER PRESENT. Pre-existing, unchanged from `bb7a236`, and a pre-existing instance of the defect this item names does NOT excuse it - this item's own detail entry opens by calling the leak pre-existing. (3) **THE WHITESPACE TAIL:** `My Backup Copy` renders `<account-dir> Backup Copy`. Three widenings of the segment class were measured and ALL THREE ARE WORSE - one eats the diagnostic prose, one leaves the terminal segment fully intact. Do NOT close this by widening the class; the adjudicator verified that decline was correct. The cheap route it names is feeding the matched segment into the name memory after position fires. (4) **THE BARE-SEGMENT FORM** must be closed or recorded as a STATED exemption bounded by `tests/test_redaction_scope.py`'s fence, which currently bounds it without any exemption being written down.

## CS-455

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: THE FULL NOTE IS RELOCATED to this file under **CS-455 - detail** and MUST be read before taking this item; it carries the measurements this entry rests on.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted. The item
itself stays OPEN in `ROADMAP.md`.

filed 2026-08-16 (session 13) by the CS-421 builder as a MEASURED residual of its own work, and it is this project's own circularity one layer along. Measured with byte-verified mutants: replacing the whole fixed-width decode with a constant 1 leaves the two new byte-order oracles GREEN, because a small positive constant carries a zero high byte exactly as a real small value does. **THE ORIGINAL NOTE THEN SAID "constant 0 and a large constant both go red, so the blind spot is narrow" AND THAT WAS MEASURED FALSE 2026-08-16 (session 14), one process per constant so no memoised sweep carries a result forward: 0 red, 1 / 255 / 1000 / 65535 / 1000000 ALL GREEN, 16777216 red.** The accepting band is every constant with a zero high byte and a nonzero low byte - not narrow, and the acceptance above is widened accordingly. **THE RANGE FRAMING THAT USED TO SIT HERE - "roughly 1 to 16777215" - WAS MEASURED FALSE 2026-08-17 (session 16), one process per constant: 256 sits inside that range and goes RED, because its low byte is zero.** The two-part rule is the correct statement and the range was an approximation of it that is wrong at every multiple of 256. Deleted rather than re-fitted; do not write a range here. Do not re-derive this by looping mutants inside one process; the sweep is memoised and every later iteration silently reports the first mutant's verdict. **THE FIRST DRAFT OF THE DOCSTRING ATTRIBUTED THIS GAP TO THE ROTATION CONTROL AND THAT WAS FALSE** - under the constant-1 mutant 8 tests red, 7 of them synthetic-fixture tests and the eighth the nested gate that runs them, while `tests/save/test_properties.py::test_the_decode_collapses_when_the_payload_start_is_rotated` stayed green. It could not have done otherwise: it perturbs the WALK, and a fabricated value does not move the walk. So on the real library nothing catches this; only fixtures packed from the same belief the reader unpacks with do, which is CS-421's stated circularity reappearing. Do NOT close this with a synthetic fixture.

## CS-456

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-456 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-16 (session 13) by the CS-422 builder against `TextProperty` alone, and **REWRITTEN TO THE FAMILY 2026-08-16 (session 14) after the CS-422 adversary measured that `TextProperty` is not the one honest exception but the one that happened to get transcribed.** Four type words ship a tag-extra width while their value reading is unmeasured - `ArrayProperty`, `MapProperty`, `SetProperty`, `StructProperty` - and only `ArrayProperty` is recorded in `DECLINED_VALUE_READINGS`. The other three are declined in `UNMEASURED_PAYLOAD_REGIONS` on SAMPLE SIZE, the criterion the rule disclaims, at 81, 72 and 45208 instances respectively; `TextProperty` sits in the new table on the same criterion at 10. Whether a wrong width is discriminated for ANY of them is UNMEASURED. Note the population must be derived: listing four names here recreates the hand-written scope that CS-458 exists to remove.

## CS-457

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-457 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-16 (session 13) by the CS-422 builder against its own work. Measured: citations written into `#:` doc-comments in `clockspeed/save/objects.py` resolved to TRUNCATED names and the checker PASSED - the underscore-wrap rejoin applies inside column-0 `#` blocks and not to `#:`, so four citations naming real tests were read as four dead names and nothing went red. Worked around by moving those citations into the adjacent `#` commentary block, where a planted dead name IS caught; the blind channel itself is untouched and is what this item covers. **THIS IS THE CS-442 FAMILY, one file along** - the verification pointer is the field that makes a claim trustworthy, and a channel the checker cannot read is a channel where a pointer rots silently. Note the failure direction is the dangerous one: an unreadable citation reads as no citation at all rather than as an error.

## CS-458

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: THE FULL NOTE IS RELOCATED to this file under **CS-458 - detail** and MUST be read before taking this item; it carries the measurements this entry rests on.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted. The item
itself stays OPEN in `ROADMAP.md`.

filed 2026-08-16 (session 14) by the CS-422 adversary and confirmed by the merger from source, no mutation needed. `tests/save/test_properties.py` builds its `shipped` set as `_TAG_EXTRA_STRINGS | _FIXED_WIDTH_VALUES | {GUID_BYTES, _SOFT_OBJECT_TAIL_BYTES}` and `CURSOR_WIDTHS | EXTENT_WIDTHS` equals that same union, so `ungoverned` and `phantom` are empty for any edit to either TABLE. **THAT PHRASING USED TO READ "structurally empty set differences" AND IT OVERSTATES, MEASURED 2026-08-17 (session 16):** the test transcribes `GUID_BYTES` and `_SOFT_OBJECT_TAIL_BYTES` as its own literals while `objects.py` spells them inline, so the two literals do NOT cancel and renaming `GUID_BYTES` in `CURSOR_WIDTHS` alone turns `ungoverned` RED. The acceptance below is unaffected - the table half is what needs independent sources - but the test was kept and re-docstringed rather than deleted, because deleting it would have removed a live transcription check. Five cursor-advancing widths in the same walk are covered by nothing: `_TAG_INDEX_FIELD_BYTES` (`clockspeed/save/objects.py:2608`), `INT32_SIZE`, `UTF16_CHAR_SIZE`, the guid-flag byte literal and the `BoolProperty` in-tag byte literal. **THE ASYMMETRY IS WHAT REMOVES THE "PRIVATE CONSTANTS ARE OUT OF SCOPE" DEFENCE:** `_SOFT_OBJECT_TAIL_BYTES` is private and IS classified while `_TAG_INDEX_FIELD_BYTES` is private and is not, and nothing distinguishes them but who typed which literal. Mis-stating `_TAG_INDEX_FIELD_BYTES` reddens two census tests on their BASELINE with messages naming an innocent width, which is collateral collapse rather than grading.

## CS-459

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 (session 14) independently by BOTH the CS-421 adjudicator and the CS-421 adversary. **THIS ITEM OWNS THE TRUTH GAP UNDER CS-421 CLAUSES 1 AND 2** - it records that `WIDTH_ONLY_VALUE_TYPES` can become a lie in shipped data with nothing red, and a 2026-08-23 adversary reproduced exactly that. Detail relocated 2026-08-23 to this file under **CS-459 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-16 (session 14) independently by BOTH the CS-421 adjudicator and the CS-421 adversary, which is why it is filed rather than argued. The guard compares `EVIDENCE_FOR_VALUE_TYPE` to `_MAGNITUDE_SCORED_TYPES`, a hand-authored literal in `tests/save/test_properties.py`, never to what the oracles actually score - so the tie is between two transcriptions. Adding `EVIDENCE_MAGNITUDE` to `UInt32Property` IS caught; making the tally also score `UInt32Property` with the table untouched is NOT, and moves `int32_values` silently while `WIDTH_ONLY_VALUE_TYPES` becomes a lie in shipped data with nothing red. Neutering the `FloatProperty` scoring branch also leaves the coupling test green - only a separate emptiness floor catches it, so the docstring claiming the table is tied to the running controls overstates by one link, which is the ADR 0008 shape inside the control that grades ADR 0008 compliance.

**CONFIRMED AGAIN 2026-08-23 by the CS-421 control-validity adversary and re-checked by the merger.**
Moving `BoolProperty` off `declared_width` in `EVIDENCE_FOR_VALUE_TYPE` silently drops it from
`WIDTH_ONLY_VALUE_TYPES`, and the whole of `tests/save` stays green. The only non-module reader of
that set asserts it is non-empty and disjoint from the magnitude-scored set, and never that any
particular type is in it. **THIS ITEM ALREADY OWNED THAT FINDING** - the NOTE above names it in terms -
which is why no duplicate item was filed for it. The sibling gap on the vocabulary STRINGS is
different and is CS-827.

## CS-827

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-23 by the CS-421 control-validity adversary, reproduced by the merger. Every reader outside `clockspeed/save/objects.py` selects by SYMBOL, so the yardstick moves with the data and the swap is invisible. **THE WORKED EXAMPLE IS ALREADY IN THE TREE AND IS THE POINT OF THE ITEM:** `tests/save/test_byte_order_status.py::test_the_status_words_are_pinned_and_distinct` does exactly this for the byte-order words and its docstring gives the reason - shipping status as DATA means something outside this repository reads the STRING. The evidence words have no such control.

## CS-460

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-460 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-16 (session 14) by the CS-420 clause-5 adversary and CONFIRMED PRE-EXISTING by the merger - both the sentence and the `any()` it denies are present at 550d383, so no CS-420 commit introduced it. The comment claims the loop below it has "no any(), no short-circuit, no early exit"; there is an `any()` 33 lines below, inside that loop, and two asserts that exit it. **THE UNDERLYING PROPERTY IS SOUND AND THAT IS WHY THIS IS TIER 2:** the list comprehension that builds `fired` calls every oracle with no short-circuit, and the `any()` does string membership over that already-complete list, so no oracle goes uninvoked. The sentence is wrong about the code and right about the property, which is the ADR 0008 shape at its most deceptive - a reader checking the claim by reading the named loop finds the thing it denies. It survives the CS-420 fence because "no any()" carries no listed marker, which is that fence's declared under-detection direction working exactly as documented rather than a hole in it.

## CS-461

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 (session 14) by the CS-420 clause-5 adversary as the stated residual of a pass it otherwise could not break. `string_census` and `string_position_mutants` both derive their population from `_string_literals`, so narrowing it shrinks BOTH sides and the equality still holds - measured green under a helper that drops literals over 200 characters, and under one that drops the whole assert-kind population of 43 of 74. ASYMMETRIC narrowing of either side alone IS caught, which is the defect class the item was refuted on and is genuinely repaired. **NOT A LIVE DEFECT:** the shipped helper walks all 74 and catches both a long and a short planted claim, verified. This is a limit on the guard's self-defence rather than on what shipped, which is why it is filed rather than reopening CS-420.

## CS-462

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 (session 15). MEASURED: on a relocated save root holding only a hex-named account directory and no override, `resolve_account_dir` returns None, because `numeric_account_dirs`' `child.name.isdigit()` filter at `clockspeed/data/locate.py:796` is the ONLY auto-detection arm. `locate.py`'s own comments name Epic and the Microsoft Store explicitly as shapes that occur, so the module documents a case it cannot then resolve. **THIS IS SELECTION, NOT REDACTION, and it is deliberately NOT part of CS-454** - fixing it would incidentally cause the directory to be remembered and would close one CS-454 form as a side effect, and a side effect does not satisfy a redaction clause.

## CS-465

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-465 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-16 (session 15) by the CS-454 vacuity adversary and CONFIRMED by the merger using the fence's OWN helper. The walk is unbounded in DEPTH but grades against `RESOLVER_NAMES`, which is `locate`'s PUBLIC surface of six names, while the cycle it exists to prevent - `redact` to `resolve_save_root` to `_override` to `local_config` to `_read_local_config` to `_note` to `redact` - passes through FOUR private hops. Measured: a public-hop plant closes the cycle and reports two offenders, RED; a private-hop plant closes the identical cycle and reports NONE, GREEN, while the same tree raises `RecursionError` at runtime. **The comment above the test claims it reads the transitive closure precisely because "a single private wrapper would defeat a body-only check", so the module contradicts itself about its own guard** - the ADR 0008 shape inside a fence built to enforce ADR 0008. Note the fence declares no scope limit at all, unlike its sibling in `tests/test_redaction_scope.py`.

## CS-466

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 (session 15). MEASURED by a breadth adversary and confirmed by the adjudicator: `tests/conftest.py` never imports `clockspeed` at all, and every one of its account references is the logged-in WINDOWS account, not the save-tree account DIRECTORY - two different things. On a save-shaped path it leaves the account directory AND the world name standing where `locate.redact` yields `<account-dir>/<save-file>`. **LATENT RATHER THAN LIVE, and the bound is what makes it tier 2:** the real-library tests report COUNTS ONLY, their discovery sits inside a `try`, and there is no `--showlocals` in `addopts` - so no real save path reaches a failure report today. That bound is guaranteed by discipline and by no check at all.

## CS-467

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-467 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-16 (session 15). `test_no_planted_string_reaches_any_world_load_error_surface` already asserts over FIVE surfaces including the formatted traceback, which is the right design; but `_FAILURE_CASES` holds six CONTENT and parse failures only, all on files that exist with malformed bytes, and `_PLANTED_TOKENS` are all content markers. The one failure mode whose chained cause carries a path - a missing or unreadable save, where `OSError.filename` is the full save path - appears only in the message-shape test, which formats no traceback. **THE LEAK IS NOT LIVE and that is why this is tier 2:** the adjudicator measured that `workdir.py` builds `SourceUnreadableError` already-redacted, so the traceback renders `<account-dir>/<save-file>`. This is coverage, not behaviour - but the surface is guarded by another module's redaction rather than by this sweep.

## CS-468

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-468 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-16 (session 15) by the CS-454 vacuity adversary. `tests/data/test_locate.py` skips when there is no distinct 8.3 rendering, and `clockspeed/data/locate.py`'s `_win_path_form` returns None off Windows, while the tier-1 lane is `ubuntu-latest` and runs on every push. So the ONLY control that catches that mutant is skipped on every tier-1 run and graded solely by tier 2's Windows matrix job. Severity is coverage rather than correctness - there is no 8.3 leak where there are no 8.3 names - but a control that skips on the lane everyone watches is a control most readers will believe is running. **OBSERVED ON A REAL RUNNER 2026-08-16, so this is no longer a simulation:** the tier-2 `workflow_dispatch` on `8620238` skipped `tests/data/test_locate.py:858` on `ubuntu-latest` with the reason "this volume has no distinct 8.3 rendering", and the two operating systems differ by exactly four tests - `ubuntu-latest` 1977 passed 44 skipped against `windows-latest` 1981 passed 40 skipped, on an identical collected total of 2021. Do not re-measure this; measure instead which FOUR tests make up the gap, since only one of them is named above.

## CS-464

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 (session 15). Same defect as the one CS-454 deleted from `tests/data/test_locate.py`, one file along and untouched because it was outside that slice's write-list: the test builds its "relocated" path as `local.joinpath(*locate.SAVE_ROOT_PARTS) / account_dir / "Backup"`, so the marker is still in the string and the positional rule catches every shape. **The test whose docstring names the relocation case is the one test that cannot fail for it.**

## CS-470

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-470 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-17 (session 16). The census reaches its terminator on more payloads under the identity than under any other of the 24 orderings, but the runner-up swaps only the two HIGH size bytes, which are both zero for any small declared size, so the two are separated only on the payloads carrying a size at or above the 16-bit boundary - a small population that the operator's play can remove entirely. **The test is gated to SKIP rather than to fail when that population is empty**, which is what keeps it out of the CS-432 false-red shape, and the gate is a stated bound rather than a fix. Note the asymmetry that produced this item: the session shipped the VALUE result as a candidate set of two and very nearly shipped this one as "exactly one of its twenty-four byte orders", on a smaller discriminating population than the one it had just called disqualifying.

## CS-472

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-472 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-17 (session 16) by the CS-422 builder against its own work and reproduced by a verifier against the landed constants with the exception set re-derived: 4 of 5 per-entry deletions are caught and 1 is not. The uncaught word ships no tag-extra width, so it is outside the derived population and its entry is optional by construction. **The obvious derived closure is FALSE against the shipped tables** - requiring a decline for every word `UNMEASURED_PAYLOAD_REGIONS` records as unmeasured fails on two counts, because that table's keys are not all type words and a word recorded as unmeasured is not thereby a declined VALUE READING. So this needs a seam that separates those cases, not another assertion over the tables as they stand. The limit is recorded in `tests/save/test_width_rule.py` rather than left as an adjective. Adjudicated as NOT blocking CS-422, on the ground that a word shipping no width is outside a clause about when a width may ship.

## CS-473

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-17 (session 16). FULL ENTRY relocated to this file under **CS-473 - detail**, including three separate enlargement measurements; read it before taking this item. **SCOPE SPLIT 2026-08-20 (session 25): CS-495 moved the reach guard's prose out of that module into `tests/save/reach_guard.py`, so this item's subject is now three modules, not one. Nothing was deleted and the prose is unfenced in all three; re-measure the population before quoting any figure from the detail block.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` on 2026-08-19 (session 21) under its soft doc budget, whole and unedited. The item itself stays OPEN in `ROADMAP.md`; this is its NOTE.

NOTE: filed 2026-08-17 (session 16). Measured, not inferred: `FENCED_MODULES` is a hand-written 2-tuple that excludes `test_properties.py`, and a claim carrying eight unbounded quantifiers was spliced into that module with both fence modules staying green at 25 passed, then restored from a byte copy. So ADR 0008 compliance in the project's largest test module is an author obligation with no mechanism behind it. The emptiness half is the same shape one file along: the two guards between them now catch a `pass` body, a docstring-only body and an `assert True` on a literal, and three shapes remain - and a body that is only `pytest.skip()` is the dangerous one, because it is camouflaged among the legitimate skips of a library-backed module. **ENLARGED AGAIN 2026-08-18 (session 20):** CS-480 took that same module from 70 unbacked absolute sentences to 113, measured with this repo's own `unbacked_absolutes` over both trees. No sample repair was made: a partial hand repair with no mechanism is the register of pardons that tool's own docstring forbids. **SURFACE ENLARGED 2026-08-18 (session 18), measured rather than estimated:** CS-476 shipped `tests/save/test_byte_order_status.py`, a new module that is NOT in `FENCED_MODULES`, so it ships unfenced by default - which is this item's own claim reproducing itself one module along. Running the fence's contract 1 against it via `unbacked_absolutes` reports **24** unbacked quantified sentences, spread across the docstring, comment and assert-message channels. That figure is a measurement of that module on that date and is NOT a budget - re-run the scan rather than carrying it forward. Bringing the module inside the fence is a prose rewrite, which is why it was recorded here instead of being folded into CS-476. **ENLARGED AGAIN 2026-08-18 (session 21):** CS-482 added 9 unbacked quantified sentences across the three modules it touched, measured with this repo's own `unbacked_absolutes` over both trees - `clockspeed/save/objects.py` 216 to 219, `tests/save/synthetic.py` 113 to 115, `tests/save/test_objects.py` 179 to 183. Two of the three in `objects.py` are statements of what is NOT measured, which is the tool's known coarseness rather than an overclaim, and that is a reason to fix the tool and not a reason to exempt the sentences. One sentence WAS backed by citing a resolving test rather than by rewording it. No sample repair was made, for the reason recorded above.

## CS-474

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-17 (session 16) by a control-validity adversary. The module imports the two TALLIES and then transcribes the two PIVOTS - the majority and minority comparisons the shipped oracles assert - so the derivation grades a copy of the judgement rather than the judgement. It is faithful today, verified against both shipped assertions. **The module's own import comment says a transcription of either would grade a copy instead of the shipped judgement**, so the file contradicts itself about its own method, which is the ADR 0008 shape inside a control built to escape circularity. The builder reduced the damage to one transcription per predicate with a single owner each, which is where an import would land.

## CS-477

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-18 (session 18) by the THIRD refutation of CS-476, after the second refutation's repair was believed final. **THE THREE MEASUREMENTS THIS ITEM RESTS ON - all at `tests/save` 1040 passed, exit 0 - ARE RELOCATED to this file under **CS-477 - detail** and MUST be read before taking this item;** they name the two open routes and the inert probe shapes exactly. **THE PATTERN THIS ITEM IS REALLY ABOUT:** each repair moved the hand-written seam up one level rather than removing it - label set, then site list. A fix that names a population is the defect; derive the population or state the bound.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-18 (session 20) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`.

**MEASURED, all at `tests/save` 1040 passed, exit 0.** (1) `_DISPATCH_SITES` in `tests/save/test_byte_order_status.py` is a hand-written 2-tuple; deleting one entry drops every oracle that entry owns and costs the probe NOTHING, because `_coarseness_observation` reaches its dispatch directly rather than through the tuple - so two line deletions inside that one module restore the zero-coarseness-call state the second refutation closed. (2) An ordinary extract-method refactor - moving `_tally_mantissa_coarseness` behind a helper called from the census - takes the call out of the scanned body while the oracle still runs, and EVERY control passes, which is stealthier than an alias because the neutering patch still bites. A rename dropping the `_tally_` prefix IS caught, but only by `monkeypatch.setattr` raising on a missing attribute, not by the derivation. (3) `_PROBE_VALUE_PAIRS` is graded by nothing: emptying it leaves the module green at 8 passed, and 3 of its 5 shapes cannot move anything under any combination, because both dispatch sites key on IntProperty and FloatProperty alone.

## CS-479

### NOTE - relocated from `ROADMAP.md` 2026-08-23

**NOTE RELOCATED for budget, never deleted: read this file under **CS-479 - detail** BEFORE TAKING THIS ITEM.**

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 27) for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`. This block is a LIVE instruction, not history.

NOTE: filed 2026-08-18 (session 19) by the CS-421 correctness refutation and re-measured by the merger before filing. **MEASURED:** displacing `tests/save/test_value_anchoring.py::_census_stored_patterns`'s read of `UInt32Property` leaves the derived set unchanged at 5 of the 7 offsets in [-3, +3] - the displaced bytes still carry the small-magnitude signature under both readings - and the universal predicate kills only +1 and -2. This is CS-421's own recorded circularity one layer along: the derivation establishes what the oracle SAYS, not that it was said about this type's bytes. **WHAT ALREADY HOLDS AND MUST NOT BE RE-DERIVED:** `test_no_fixed_width_value_depends_on_a_byte_outside_its_declared_extent` grades every fixed-width tag through `_anchored`, `UInt32Property` included, and reddens when the shipped reader's value start moves - so the SUITE holds the anchor and this control does not. What is open is a displacement applied to this derivation alone.

## CS-490

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-19 (session 23) as CS-487's measured residual. **IT IS NOT CS-488, AND THE MEASUREMENTS, THE LINE COUNTS AND THE FENCES ARE IN this file under **CS-490 - detail** and MUST BE READ BEFORE TAKING THIS ITEM** - relocated for budget, never deleted.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-19 (session 23) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-19 (session 23) as CS-487's measured residual, by two independent refutation
passes and re-measured by the merger on the tree carrying CS-487's two arms. **IT IS NOT
CS-488.** CS-488's acceptance is scoped to a WIDTH-TABLE entry and neither route here touches a
width table, so satisfying CS-488 need not red either; an earlier draft of CS-487's control
handed this residual to CS-488 and a refutation pass measured that assignment wrong.

TWO ROUTES, BOTH TAKEN ALL THE WAY TO GREEN RATHER THAN LEFT AT THE FIRST RED, both with
`tests/save` green on a machine with no game. SEVEN EDITED LINES - five in
`clockspeed/save/objects.py`, two in `tests/save/test_properties.py` - by taking a word ALREADY
in `MEASURED_VALUE_TYPES`, severing it from the shape table that reads it, re-declaring it
measured, widening both tag-carried sites and writing the status entry, then moving its fixture
tag and expected value. And EIGHT EDITED LINES for a word the module has never named. A line
count is EDITED lines, added and modified alike - counting only additions understated one route
by two.

THE PRICE AND THE ROUTES ARE OWNED BY
`tests/save/test_byte_order_status.py::test_no_word_the_exemption_admits_is_one_the_module_declines_to_measure`.
Read that docstring before taking this item and DO NOT RESTATE ITS COUNTS here or anywhere -
two counts in the first draft of this work were wrong precisely because they were written
twice.

NOTE THE HARD PART BEFORE STARTING. Every control on this exemption is keyed on the module
CONTRADICTING itself - a status against a region the module records as unclaimed, a tag-carried
word the module also reads out of the payload, a decoded word the measured set declines to
name. A module edited to claim a type in every table at once contradicts itself nowhere, and no
library-free check can tell a false width or a false shape from a true one, which is CS-426's
gap. So the acceptance cannot rest on another contradiction; it needs either a fixture that
costs more than one `struct.pack` call, or evidence from outside this module's own tables.

## CS-499

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-20 (session 25) as CS-498's disclosed residual, MEASURED: with `if module_path == Path(__file__): return` in `_assert_library_reach_is_declared` and an undeclared reaching helper appended to that same file, `tests/save` is GREEN at 1116 passed. CS-498's control compares two copies under different names in `tmp_path`, and a path-keyed exemption treats both as ordinary files, so they agree and it says nothing. **THE CANDIDATE NOBODY HAS MEASURED:** make the guard RETURN what it examined rather than None, and assert a non-empty examination for the real file - an early return then shows as an empty result instead of as silence. That changes the guard's signature and every call site, which is why it is filed rather than folded into CS-498. Do not close it by naming a path anywhere.

## CS-492

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: nine rounds, nine refutations, every one on a real defect; the ESCAPE direction only, with rounds seven to nine BUILT and UNCOMMITTED. Detail relocated 2026-08-22 (session 32) to this file under **CS-492 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

### Relocated 2026-08-22 (session 32) from `ROADMAP.md` - the CS-492 NOTE, verbatim

Moved for budget, not deleted. The item itself stays OPEN in `ROADMAP.md`, which now
carries a one-line pointer here.

**NINE ROUNDS, NINE REFUTATIONS, every one on a real defect.** s27 graded round six (REFUTED), built and graded rounds seven and eight (both REFUTED on both lenses), and dispatched round nine, which is UNGRADED. **THE ROOT CAUSE IS LOCATED AND IT IS A CHOSEN CONTRACT: the evidence rule is VALUE-AGNOSTIC** - it asks whether a bare name is bound at module scope, never what to - so `stat = "chunks"` certifies `stat` as a filesystem primitive and a neighbouring `def get(self, stat): return stat` manufactures EIGHT declarations on the real `tests/save/test_phase4_gate.py`. That row is measured on rounds SIX, SEVEN AND EIGHT alike, so it predates every repair and round six's defect has been DISPLACED TWICE AND REPAIRED ZERO TIMES. **Rounds seven and eight are UNCOMMITTED in worktrees by operator decision** - no build is strictly best, r7 has the cleaner false-flag direction and three silent module-scope escapes, r8 fixes those and regresses three false-flag rows. **Do not close this by widening the name list alone** - CS-491's note said so and nine rounds have now tested it to destruction. **THE FALSE-FLAG DIRECTION IS NOW CS-807, TIER 1, AND IT OUTRANKS THIS ITEM** - operator decision 2026-08-22. This acceptance is ESCAPE-SHAPED and says nothing about flagging a module that reaches nothing, which is what actually refuted all nine rounds; read CS-807's detail block before taking either. **THE BARE-NAME CONFLICT IS MEASURED IRREDUCIBLE - do NOT spend a tenth round on it.** Two narrowing spikes, five-site and two-site, each take every manufactured-declaration payload to zero, each cost the SAME twelve controls, and narrowing the site count retires none: telling a caption from a locator on the same bare token needs the type resolution this repo has declined. Full measurement table, both failed fix shapes and the next action are in `WAKEUP_NOTES.md` session 27; the filing history is in this file **CS-492 - detail**.


Relocated from `ROADMAP.md` 2026-08-20 (session 24) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

CS-492 - Close the reach routes that travel through an OBJECT rather than a name binding - acceptance: a module holding a primitive on an instance attribute, or serving one from a module-level `__getattr__`, and calling it from a function that names no primitive, turns a test RED on a machine with NO GAME INSTALLED - tier: 2 - NOTE: filed 2026-08-20 (session 24) as CS-491's disclosed residual, MEASURED by two refutation passes and re-measured by the merger. Two shapes, both green against the shipped guard: `self.finder = locate.resolve_save_root` bound in `__init__` and called from a sibling method or off a module-scope instance, and `def __getattr__(name): return locate.resolve_save_root` at module scope. **THE REASON THEY ARE NOT IN CS-491:** `_aliases_bound_in` deliberately holds module scope and function-local scope APART, because a local `finder` in one function says nothing about a name `finder` in the next - and an attribute bound inside `__init__` is a function-local binding whose CONSUMER is a different function. Making it module-visible re-opens the inversion the keying note records, and the correct fix is a per-CLASS scope that does not exist yet. **Both were ranked CONTRIVED by the adversary that found them**, and an AST scan of `tests/save` finds zero instances of either, so this is latent rather than live. Do not close it by making function-local bindings module-visible without measuring what that flags. **ALSO HERE, and NOT contrived:** a body held in a CONTAINER field - `parts: list` holding `[source.read_bytes()]`, or a helper returning `dict` whose value is the body - is not walked as a wrapper. That one sits close to CS-491's stated residual (the type is written nowhere) but is not identical to it.

## CS-501

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: detail relocated 2026-08-23 for budget to this file under **CS-501 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-23 for budget, not deleted. The item stays OPEN in
`ROADMAP.md`. This block is a LIVE instruction, not history.

filed 2026-08-20 (session 25), reproduced by the merger: a planted module with two module-scope locator calls and one sentinel exemption is SILENT. Named as bound 4 in CS-493's detail block and outside that item's acceptance. Three tracked modules declare the sentinel today, so any fix has to say what a per-site key looks like - a line number is not stable across an edit, which is why this is filed rather than guessed at. **ID NOTE: this sits in the CS-5nn block because the CS-4nn block is FULL** - 98 of 100 used, and the only two unused are gaps, which CLAUDE.md forbids backfilling. It was first filed as CS-500 and collided with the phase 5 gate, which has held that ID far longer; the older item keeps it. **Which block phase-4 follow-ups continue into is an OPERATOR DECISION and is not settled by this line.**

## CS-488

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-19 (session 22) by a refutation pass on CS-481 and re-measured by the merger. **THE MEASUREMENTS, THE LINE COUNTS AND THE FENCES ARE IN this file under **CS-488 - detail** and MUST BE READ BEFORE TAKING THIS ITEM** - relocated for budget, never deleted.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-19 (session 22) for budget, not deleted. The item
itself stays OPEN in `ROADMAP.md`.

filed 2026-08-19 (session 22) by TWO independent refutation passes on CS-481 and re-measured by the merger. CS-481's contradiction arm reads `UNMEASURED_PAYLOAD_REGIONS`, so a word the module never mentions has nothing to intersect with. SIX LINES - three in `objects.py` (width entry, shipping grounds, evidence entry, with the region entry deleted where one exists) and three in `tests/save/test_properties.py` (the measured-set transcription, a `_scalar_tag` fixture line, an expected-value line) - ship `vacuous_one_byte` for an EIGHT-byte type with `tests/save` GREEN with no game. WHAT CS-481 DID CLOSE IS WORD-AGNOSTIC ON THE OTHER LINE and that is measured: a never-named type declared one byte wide and severed from `MEASURED_VALUE_TYPES` reds the walk control and nothing else. NOTE THE HARD PART BEFORE STARTING: no library-free check can tell a false width from a true one - that is CS-426's gap - so the acceptance has to rest on the module's own coherence or on a fixture that costs more than a `struct.pack` call, not on the width being right.

## CS-489

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-19 (session 22) by two refutation passes independently, on the same tree. The `ArrayProperty` entry reads "THREE OF THOSE FOUR WORDS ARE IN MEASURED_VALUE_TYPES AND Int64Property IS NOT, which is why it has its own entry below". On a tree that moves `Int64Property` into the measured set and deletes its region entry that sentence is FALSE and its pointer dangles, with the whole suite green. `tests/save/test_properties.py::test_the_region_table_holds_no_key_nothing_justifies` reads other entries' prose to JUSTIFY a key; nothing grades what the prose SAYS.

## CS-483

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-18 (session 21) by CS-482's mutation-grading pass, which found it INCIDENTALLY rather than as part of its brief and reported it against itself: the pass saw it fail once inside the phase-4 gate's nested subprocess while a mutant was being graded, then pass 3 of 3 standalone, and the full suite re-ran clean. It asserts on pytest's own frame-argument rendering from inside a sub-subprocess, which is the shape that goes load-sensitive. THE COST IS NOT A RED SUITE, IT IS A MISATTRIBUTION: a flaky test inside a mutation battery reads as a mutant DETECTED when the mutant is actually alive, and that error is silent and points the wrong way. Any future mutation work over `tests/save` is exposed to it.

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

## CS-801

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: this file **CS-801 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 26) for budget, not deleted. The
item itself stays OPEN in `ROADMAP.md`.

CS-801 - A `__getattr__` serving a locator is closed only where it is defined at MODULE scope and consumed in the SAME file - acceptance: a class-level `__getattr__` returning a locator, and a module-level one consumed from a sibling as `other.anything()`, each turn a test RED on a machine with NO GAME INSTALLED - tier: 2

filed 2026-08-21 (session 26) as CS-492's disclosed residual, both measured green and both classed SILENT, so the suite-wide guard never runs on the module at all. A `__getattr__` makes EVERY attribute of its namespace a locator, and neither vocabulary can express that today: `_reaching_attributes` learns the attribute name `__getattr__` itself and stops, and `_reaching_names_of` exports NAMES, so a wildcard cannot cross the module seam as one. Ranked ORDINARY by the pass that found it - a proxy or lazy-attribute class is the ordinary reason to write either. **A fix has to say what a wildcard looks like in a set of names**; the file's own `MODULE_SCOPE_REACH` sentinel is the precedent for a member that is not an identifier.

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

## CS-803

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: this file **CS-803 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 26) for budget, not deleted. The
item itself stays OPEN in `ROADMAP.md`.

CS-803 - A closure built by a nested `def` is not read as serving what it closes over - acceptance: a module whose factory returns a nested function that reaches the library, and whose consumer calls the factory's result, turns a test RED on a machine with NO GAME INSTALLED even when the factory itself is declared - tier: 2

filed 2026-08-21 (session 26) by a refutation pass on CS-492 round two, measured: the consumer HOLDS THE REAL SAVE ROOT and is accepted. `_returned_values` excludes nested definitions deliberately - an inner helper's returns are not the outer function's - so the factory is never a serve. The IDENTICAL idiom spelled with a `lambda` IS caught and names the consumer, which is what makes this one mechanism applied to part of its population rather than a stated bound. Ranked ORDINARY. **Do not close it by deleting the nested-definition exclusion in `_returned_values`** - that exclusion is load-bearing for the opposite case and its reason is in the docstring.

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

## CS-805

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: this file **CS-805 - detail**.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-21 (session 26) for budget, not deleted. The
item itself stays OPEN in `ROADMAP.md`.

CS-805 - The container-FIELD personal-data shape is not walked as a wrapper, and the footprint is wider than CS-492's detail block records - acceptance: a class holding a save body in a CONTAINER field, and a helper whose return annotation is a container of bodies or of stringified real save paths, each turn a test RED on a machine with NO GAME INSTALLED - tier: 2

filed 2026-08-21 (session 26). This is the PERSONAL-DATA half of the guard, `reach_guard._body_wrapping_classes` and `_returns_personal_data`, not the reach half CS-492 closed, which is why it is a separate item rather than that item's acceptance. Named in this file under **CS-492 - detail** as "ALSO HERE, and NOT contrived". A refutation pass measured all of it open and found one shape the note does not mention: a return annotated `-> list[str]` carrying stringified real save paths passes strict typing and propagates nothing. Measured caught for contrast: `-> bytes` and a `bytes`-typed field.

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

## CS-808

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: found 2026-08-22 (session 29) by the CS-807 permissive-failure refuter, OUTSIDE its brief, and reproduced independently on `main` by the merger: a planted sibling read as harmless, rewritten at the same path to reach the library, still answered `[]` until `cache_clear()`, which then answered `['sweep']`. **IT IS LATENT TODAY, NOT LIVE** - pytest's per-test `tmp_path` gives each control a fresh path, which is exactly why no existing test sees it. It becomes real the moment a control plants two sibling versions at one path, which is a natural thing to write and would fail in the direction that reads as SAFE.

## CS-484

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed earlier; **the FULL entry, including the MEASURED version gap (CI resolves ruff 0.16.3, this machine 0.15.12, extracted from the tier1 log on `76fac74`), is in this file under **CS-484 - detail** and MUST BE READ BEFORE TAKING THIS ITEM** - relocated for budget 2026-08-20 (session 25), never deleted.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-20 (session 25) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

CS-484 - The local lint gate cannot reproduce CI's, because `pyproject.toml` pins `ruff>=0.13` with no upper bound and CI installs whatever is newest - acceptance: running the documented local gate set on a tree CI will reject turns something RED locally first, with the reproduction recorded - tier: 2 - NOTE: filed 2026-08-19 (session 21). MEASURED, not inferred: CI run 32211377535 failed `ruff check` on FURB192 at `tests/save/test_byte_order_status.py:878`, a line shipped in `e86f84d` (session 20) and never seen by CI because that session's push was blocked. Locally the same command passes and `ruff check --select FURB192` answers `Selection FURB192 has no effect because preview is not enabled` - the rule is PREVIEW on ruff 0.15.12 here and STABLE on the newer ruff CI resolves. **THIS IS SESSION 19's LESSON IN A NEW FORM AND THE OLD FIX DOES NOT COVER IT.** That session learned to run `ruff format --check` as well as `ruff check`; running BOTH still does not reproduce CI, because the divergence is now the ruff VERSION rather than the command. An unpinned linter means the gate's ruleset changes under the project with no commit, so a tree that is green today is red tomorrow for reasons no diff explains - and the failure lands AFTER the push, which is the expensive place. Pinning an exact version and bumping it deliberately is the obvious candidate; enabling preview locally is NOT, it would over-approximate CI in the other direction. `pyproject.toml` is not a frozen file, but the toolchain pin is asserted by `scripts/verify_env.py`, so any change goes with it. **THE DIVERGENCE IS NOW MEASURED RATHER THAN INFERRED, 2026-08-20 (session 24).** The entry rested on a version gap nobody had extracted from a CI log, and three sessions carried it as UNVERIFIED. Taken from the tier1 run on `76fac74`: CI resolved **ruff 0.16.3**; this machine has **0.15.12**. That is the premise confirmed, not the item closed - both linters passed the shipped tree on that run, so the gap cost nothing this time. What is still missing is the acceptance's own half: a tree CI rejects and the local gate does not. **DO NOT read the passing run as evidence the gap is harmless;** it is evidence that this tree happens not to touch a rule the two versions disagree on.

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

## CS-701

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-427 adversary, which hit it while scanning that slice's diff for leaked personal data and correctly classified it as a PRE-EXISTING FALSE POSITIVE rather than a finding against the slice. FULL ENTRY relocated to this file under **CS-701 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-427 adversary, which hit it while scanning that slice's diff for leaked personal data and correctly classified it as a PRE-EXISTING FALSE POSITIVE rather than a finding against the slice. Measured: the operator git author line coincides with one 4-character world name on this machine, and it is present identically on `8b3fb9d` and `1009681` - `author-line hits: 1, body hits: 0` on every revision checked. **NOTHING IS LEAKED BY THIS TODAY** - the world name is not disclosed by the author line, the coincidence runs the other way. The problem is mechanical and arrives later: **a world-name-keyed PII scan will trip on EVERY COMMIT IN THE REPO**, and a scan that is red on correct history is a scan someone switches off. CS-700's checklist includes a full-history PII scan across tracked files and commit messages, so settle the exemption rule before that gate runs rather than while it is failing. Note the CS-209 precedent: narrowing a PII blocklist by default to pre-empt a collision was DENIED BY MEASUREMENT, so an exemption here must be a named, recorded exception rather than a shortened matcher.

## CS-704

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-704 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) by the CS-702 bypass adversary, each route confirmed with a real commit. `git rebase` on BOTH backends, `git am`, `git cherry-pick`, `git revert` and `git commit --no-verify` all land a trailer git itself recognises while the hook stays silent - `git revert` was MISSED by the first enumeration and found later by an adversary, which is worth noting because it is a sequencer sibling of cherry-pick and the list was built by naming routes rather than by asking which hooks each route fires, and an unbootstrapped fresh clone runs no hook at all because `core.hooksPath` is machine-local and is never cloned. Remapping `core.commentChar` or `core.commentString` also defeats the comment-stripping premise. REBASE IS MORE ROUTINE THAN CHERRY-PICK in a worktree-slice workflow, so this class is reachable by accident rather than by evasion. CS-702 is forward-only and single-command by construction; this is the class it cannot cover. A range scan on pre-push or a check on the CI side is the route, and the first **NEEDS A FROZEN-FILE GRANT for `.githooks/pre-push`**.

## CS-811

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-811 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) by the verifier of the CS-809 repair, MEASURED with proven-landed mutants. The walk is `name.endswith("_RE") and isinstance(value, re.Pattern)` over module globals, so it sees ONE shape; a pattern named without the suffix, held in a dict or a list, compiled at call time, or an arm judging by substring all escape it, and all five were measured green. Its docstring claims it sees anything the module compiles, which is wider than what it enforces. SECOND HALF, same file: `carries_a_citation` decides carrier-hood by SHAPE, so a doc that merely names a tracked test module becomes a carrier and must be guarded or recorded even when nothing in it can rot - 31 currently-clean tracked docs are one pytest-invocation line away, and `docs/OPERATIONS.md` is the likeliest next. That is the intended forcing function but it is an undisclosed recurring hand edit.

## CS-812

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-812 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) as the CS-810 repair's disclosed residual plus one PRE-EXISTING defect its verifier found. The arms de-duplicate by name and cannot say which site is new, which is why the site pin sits in a contract test; the consequence is that `bare_name_problems` and `unresolved_citations` return empty on a genuinely new dead citation of a forgiven name. LATENT rather than live - this module is imported by nothing today, measured. SEPARATELY AND PRE-EXISTING, inherited unchanged from `f938062`: a BARE disposition whose forgiven name later becomes LIVE is never reported stale, because the now-resolves-on-its-own branch is gated on the key containing a path separator and so never fires for a bare key. Four bare-keyed entries are affected. Proven by resurrecting a forgiven name as a real def and observing the module stay green.

## CS-813

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-813 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

**A THIRD AXIS, added 2026-08-22 (session 32) by the fourth CS-703 adversary. The
acceptance text names cleanup mode and commit path; `core.commentChar` is a third and the
matrix is wider than filed.** Measured: with `core.commentChar` remapped, a line led by the
ordinary comment character is NOT a comment to git, survives cleanup into the stored
message, and the hook's pre-filter still drops it - a byte above 0x7E landed in the stored
message with HEAD moved and the hook silent. This does not change the item's direction, it
widens the matrix any acceptance suite has to cover.


Filed 2026-08-22 (session 31); the item stays OPEN in `ROADMAP.md`.

Filed 2026-08-22 (session 31) by the adjudicator of the widened CS-702 grant, which MEASURED the subject-cap escape that nothing else had named.

**THE ROOT FACT: cleanup runs AFTER the commit-msg hook.** On the editor path the hook sees the full
template while the stored message has it stripped, so every check in that hook PREDICTS the stored
bytes and never observes them. The pre-filter drops comment lines and truncates at the scissors
token unconditionally, so it models one mode out of five.

**MEASURED, with real commits and clean controls.** A 200-character comment line as the first line
becomes a 215-character STORED subject with the hook exiting 0 and HEAD moving. A comment line
carrying an em dash lands three bytes above 0x7E in the stored message. Both need only a comment
line - no scissors marker, no flags, no configuration.

**THE CLEANUP TABLE, measured.** `verbatim` and `whitespace` keep comments and keep everything below
the scissors marker. `strip` removes comments and KEEPS what is below the marker. `scissors`
truncates only on the editor path. `default` is `strip` when edited and `whitespace` when not.
Note the consequence: today's unconditional break is wrong on the ordinary editor path too.

**THE OBSERVABLE EXISTS.** Git sets `GIT_EDITOR` to the no-op colon in the hook environment exactly
when the editor was not used. `commit.cleanup` is readable too. What is NOT observable is an
explicit cleanup override combined with an editor, which is the admitted residual.

**WHY 78 GREEN TESTS COEXISTED WITH THREE FAIL-OPENS,** which is the transferable part: every arm
drove one commit path, and one arm ASSERTED THE ESCAPE AS INTENDED BEHAVIOUR. The defective mode
was simultaneously the only mode tested and the mode declared correct. Any suite for this item must
parameterize over cleanup mode by commit path, and must use GIT AS THE ORACLE FOR THE STORED BYTES
- read `git log -1` back from the landed commit and assert the gate blocked if and only if the
stored message violates - rather than asserting against its own model of what git will do.

The trailer half of the same defect is CS-702 and the routes no client-side hook can cover are
CS-704. This item owns the cleanup model, the ASCII escape and the subject-cap escape.

## CS-814

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-814 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 31); the item stays OPEN in `ROADMAP.md`.

Filed 2026-08-22 (session 31). Found by an adjudicator that dumped the hook environment during an
unrelated probe, and CONFIRMED by the merger without echoing any value.

**MEASURED: five live credentials sit in the environment every git hook inherits** - a GitHub
personal access token, three third-party API keys and a harness messaging token. Confirmed by name
and length only. NOTHING IS COMMITTED: no tracked file and no git configuration key carries any of
them, checked. The exposure was into a session transcript, not into the repository.

**THE RULE THIS PROJECT ALREADY OWNS, ONE DOMAIN OVER.** Non-negotiable 12 rules that any code path
echoing raw header bytes leaks personal data, and that error messages, debug dumps, hex previews,
log lines and exception context ALL COUNT AS ECHO PATHS. A hook or a debug path that renders the
environment is exactly that shape for credentials. The reasoning is written down for save headers
and nowhere for the hooks, which is the gap.

**THIS IS THE CS-806 PATTERN AGAIN** - a rule already decided, never carried across to the place it
also applies. That makes three in three sessions, so treat the pattern as the finding rather than
the instance.

**WHAT THIS ITEM IS NOT.** It is not a request to rotate a credential - that is an operator action
and was raised directly. It is not a claim that any shipped hook echoes the environment today;
proving that none does is half the acceptance. The other half is writing the rule where the next
author of a hook will read it, so the third repetition of this pattern is the last.

**ASKED AGAIN AND ANSWERED 2026-08-23. The answer sits with the operator and is deliberately
NOT written here.** What this file records is only that the question has been PUT, so it stops
being carried forward every session as though unasked.

**THE ROTATION STATE OF A LIVE CREDENTIAL IS NEVER WRITTEN INTO A TRACKED FILE.** CS-G03 makes
this repository public eventually, and a tracked sentence asserting the current state of a live
credential is an adversary-useful standing fact that no phase-7 check would strip. A first
version of this paragraph wrote that state down; an adversary caught it and was right.

**THIS CHANGES NOTHING ABOUT THIS ITEM'S ACCEPTANCE**, which was never about rotation: the code
half is still to write the env-echo rule where the next author of a hook will read it, and to
prove no shipped hook path echoes the environment.

## CS-815

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32); FROZEN FILE, needs its own grant. Detail in this file under **CS-815 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Filed by the CS-703 adjudicator as the FOURTH site of that defect class, found by grepping for the
shape rather than by reasoning about it. `.claude/settings.json` names `pythonw tools/pretooluse_gate.py`
and `python tools/edit_lint_check.py` with NO resolution ladder and NO probe of any kind. By that
gate's own stated protocol - exit 2 denies and every other status is non-blocking - a missing or
substituted interpreter yields a non-2 status and the gate FAILS OPEN.

**IT IS MILDER THAN THE GIT HOOKS AND THAT IS RECORDED SO NOBODY RE-RATES IT UPWARDS.** CLAUDE.md
section 2.2 makes the Claude hooks a convenience layer and `.githooks` authoritative, so the tier-0
guarantee does not rest on this file. **IT IS ALSO NOT FIXABLE THE WAY CS-703 WAS,** because JSON
cannot express a probe: the fix has to live in the tools the JSON names, or in a wrapper.

`.claude/settings.json` is on the CLAUDE.md section 6 frozen list, so this needs its own operator
grant and its own adjudication. It was explicitly OUT of the CS-703 grant and is not claimed closed
by it.

## CS-816

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32), PRE-EXISTING in the old probe too. Detail in this file under **CS-816 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

**A THIRD HANG SHAPE, added 2026-08-22 (session 32) by the fourth CS-703 adversary.**
A wrapper of the form `exec python "$@" < /dev/null` answers BOTH probe halves exactly -
the token, then 97 - and then hangs `commit-msg` forever, measured at 124 under a 30 second
cap with HEAD unmoved. Root cause measured: under MSYS bash `/dev/null` maps to Windows
`NUL`, a CHARACTER DEVICE, so `isatty()` reports true, `python -` goes interactive, and the
3.14 REPL spins on an invalid handle. It is DISTINCT from the two shapes above - this
candidate spawns nothing and sets no environment variable - and it is further evidence that
the answer is a BOUND rather than an enumeration of causes.


Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

TWO SHAPES, both measured, one pre-existing and one introduced by CS-819's capture.

**Shape one, PRE-EXISTING in the old probe and unchanged by the repair.** `PYTHONINSPECT=1` makes the
candidate enter interactive mode after running the program, and it never returns. Measured at a
bounded six seconds returning 124 - **WITH stdin already redirected from `/dev/null`**, so closing
stdin does NOT close this. Neither the old probe nor the new one is timeout-bounded, and a hung hook
looks like frozen git rather than a refusal.

**Shape two, introduced by the CS-819 capture and disclosed in its grant.** Command substitution
waits for EOF on the pipe rather than for the child to exit, so a program that spawns a background
process holding stdout stalls the hook for that process's whole lifetime. Measured at 124 under a
bound. LATENT today: the program the hook delivers spawns nothing.

**The route, and its cost.** `timeout` exists at `/usr/bin/timeout` here and on a POSIX runner, but
adding it makes the hooks depend on a binary they currently do not need, and `CONVENTIONS.md` section
16 says such findings are version-specific. Whatever ships must FAIL CLOSED on a timeout - a probe
that times out and then proceeds is the CS-703 defect wearing a clock.

## CS-817

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32); the residual CS-703 explicitly did not close. Detail in this file under **CS-817 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

**This is the residual CS-703 explicitly did not close, and it is recorded so the two are never
confused.** CS-703's probe proves the candidate is a python that runs a program and can report a
failure. It proves NOTHING about what that python can import.

Measured: `py -3` PASSES the repaired probe and `py -3 -c "import pytest"` raises
`ModuleNotFoundError`. That is exactly the `BOOTSTRAP.md` section 2.5 trap - two installations both
reporting the same version, one carrying the toolchain and one not - arriving at a different door
from the one CS-806 closed.

**The exposure differs per hook and that is the part worth carrying.** `pre-push` DOES check
`import pytest` after resolution, and that check is sound now that the interpreter is proven. But
`pre-commit` never checks ruff at all, and `tools/precommit_gate.py` treats a missing ruff as
LINT SKIPPED rather than blocking - so a resolved python without ruff silently degrades the
character-set gate's sibling checks rather than refusing.

## CS-818

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32); the CS-806 shape one door along. Detail in this file under **CS-818 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Filed by the CS-703 adjudicator. `scripts/verify_env.py` asserts properties of `sys.executable` - the
interpreter RUNNING IT - and never reads `CLOCKSPEED_PYTHON` or performs the hooks' four-rung
resolution. So `verify_env` can pass while the hooks resolve a DIFFERENT interpreter, and a green
environment report is not evidence about the thing that will actually gate a commit.

**THIS IS THE CS-806 SHAPE ONE DOOR ALONG.** CS-806 closed by making this file assert the RESOLVED
interpreter instead of trusting a name; the assertion was never extended to the resolution the HOOKS
perform. Recorded that way deliberately: the pattern is now the finding rather than the instance,
and this is its fourth appearance.

The cheap route is for `verify_env` to run the same ladder and report the winner, failing when that
winner is not the interpreter it just graded.

## CS-820

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32), MEASURED. Detail in this file under **CS-820 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

**MEASURED, and reported as counts rather than values throughout - the finding is that this class of
output leaks, so the check for it must not leak in turn.** `tests/conftest.py` carries a redaction
hook that covers home paths and account names. It has NO rule for a secret, a token or a credential
of any shape. pytest renders a failing test's ARGUMENTS at the top of its report, so any test taking
an environment mapping as a parameter prints that mapping's values.

One forced failure of one arm rendered an Anthropic API-key-shaped credential IN FULL, together with
several other long opaque tokens. In CI that output goes to the run log.

**THIS IS CS-814's SHAPE ARRIVING THROUGH A SECOND DOOR.** Non-negotiable 12 already rules that error
messages, debug dumps, log lines and exception context ALL COUNT as echo paths; it is written for
save headers and, again, was never carried across. CS-814 records five live credentials in the hook
environment and an outstanding rotation; this item is the reason a test failure is also an exposure.

**THE POPULATION IS UNMEASURED AND THAT IS STATED RATHER THAN GUESSED.** One narrow scan matched two
tracked modules; a broader scan by a different agent reported more. Measuring it is part of the work.
The module that surfaced it, `tests/test_hook_interpreter_ladder.py`, was fixed in place at
`CS-703`'s merge by routing the mapping through a carrier whose repr withholds its contents - so the
instance is closed and the CLASS is this item.

## CS-821

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32), measured with a real push that landed a RED suite. Detail in this file under **CS-821 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

**A SECOND SHAPE, added 2026-08-22 (session 32) by the fourth CS-703 adversary and proven
with a real push that reached the remote: a suite that is 100 percent SKIPPED passes.**
The hook guards exit 5 - nothing collected - and nothing else, so tests that are collected
and then all skipped report 0 and the push proceeds. The hook's own header cites
`CONVENTIONS.md` section 7.2, "a skipped suite is not a passing suite", which is exactly
the sentence this misses. Any fix must judge what the run actually EXECUTED rather than the
code pytest chose to return.


Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Filed by the CS-703 escape adversary and confirmed with a real push that landed a RED suite on a
remote. `.githooks/pre-push` decides pytest is available with `cs_python -c "import pytest"`, judging
the EXIT CODE alone. A directory on `PYTHONPATH` holding a one-comment `pytest.py` satisfies that:
the import succeeds, and `-m pytest` then runs the stub, exits **0**, and collects nothing.

**THE INTERPRETER IS GENUINE, WHICH IS WHY THIS IS NOT CS-703.** The repaired probe correctly accepts
it - it is a real python that runs programs and reports failures. This is TOOLCHAIN SHADOWING, a
sibling of CS-817 rather than the same item: CS-817 is the tool being ABSENT, this is the tool being
REPLACED.

**THE EXISTING GUARD DOES NOT FIRE.** The hook treats exit 5 as "collected zero tests" and blocks on
it. The stub returns 0, not 5, so the empty-suite guard never runs. Any fix must refuse a run that
collected nothing whether it reports 5 or 0, rather than trusting the code pytest chose to return.

## CS-822

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32) by the CS-819 adjudicator; PRE-EXISTING and excluded from that grant. Detail in this file under **CS-822 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Noticed by the CS-819 adjudicator while reading the offender test, and confirmed to exit 0 under bash
with a real message. The commit-msg byte check builds its offender list with `b > 0x7E` only, so it
catches every byte ABOVE printable ASCII and nothing BELOW it. NUL and the rest of the C0 control
range are accepted into a commit message.

PRE-EXISTING, unrelated to CS-819, and EXPLICITLY EXCLUDED from that grant so the fix is not smuggled
in beside it. Any repair has to permit tab and newline deliberately rather than by omission, which is
the reason this is its own item rather than a one-character change to a comparison.

## CS-824

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 33) by the CS-823 adjudicator as the SIBLING it found and was told not to widen into. The CS-823 shape does NOT transfer: pytest comes from site-packages, not the working tree, so there is no truncatable file, and the zero-collection case is already refused by the exit-5 guard. What is open is the analogue one level up - pytest exits 0 having run ONE test exactly as it does having run the whole suite, and the hook never reads the count. FROZEN FILE, needs its own grant. Distinct from CS-821, which is about a STUBBED pytest satisfying the presence check; this is about a REAL pytest doing almost nothing.
