# 0009 - CS-405: the serialized potential component's top level carries no slot count

## Status

`proposed` - 2026-08-23

Written by the slice that ran the experiment, which leaves it `proposed` because per
`CLAUDE.md` section 5 the producing agent does not grade its own output. An adjudicator
that did not run the sweep decides whether it reaches `accepted`.

**This ADR does not supersede ADR 0005 or ADR 0006 and changes no word of either.** 0005
decided WHERE the ceiling comes from and left one operand unmeasured. 0006 brought the one
operand that IS in the shipped data into the model. 0009 reports what happened when the
single route 0005 held open was actually followed, and it does not close that route.

## Context

ADR 0005 refuted option (b) - the save - as a source of the ceiling, with one narrow
survivor. `mInventoryPotential` at `FGBuildableFactory.h:663` is declared
`EditDefaultsOnly, SaveGame`, so the potential inventory component of a built overclockable
building IS serialized. If its serialized form carried the shard slot count, that would be
a direct measurement of the last operand. ADR 0005 labelled this **UNVERIFIED** in as many
words - the header proves the component is saved and does not prove the count survives
serialization - and filed it as a phase-4 experiment rather than a result.

**The outcomes available to this experiment were ruled, not chosen by the slice.** Three
were ruled by the operator on 2026-08-14:

- **YES** - the serialized component carries a slot count. A direct measurement of ADR
  0005's last operand.
- **NO** - it is serialized and carries no slot count. Fully refutes ADR 0005 option (b),
  and is worth as much as YES.
- **INCONCLUSIVE** - no world in the library has a built overclockable building with the
  component serialized at all, so the probe DID NOT RUN and the answer is "not yet
  measured". Filed as a re-run against the world growing, and never converted into either
  answer.

A **FOURTH** was ruled acceptable by the operator on 2026-08-23, after a read-only probe
measured that none of the three was reachable: the population EXISTS, the probe RAN, the
top level carries no count, and the residue sits behind an interior another item owns.
That is the state this experiment reached, and this ADR records it as its own outcome. It
is emphatically NOT `INCONCLUSIVE`: inconclusive means the probe did not run, and this
probe ran over the whole local library.

**Why the experiment was runnable now and not before.** Two shipped changes, both
consumed rather than graded here:

- **CS-831** shipped the resolver. `mInventoryPotential` decodes as an `ObjectProperty` -
  a level string and an object path - and not as a bare integer, so the naive reading of
  YES was already refuted. That refutation did not establish NO, because a count may live
  BEHIND the reference in the record the path names. Following the reference is what
  CS-831 made possible.
- **CS-830** made container elements decodable. This is the load-bearing one. Before it,
  every target carried tags of a type whose value encoding was unmeasured, and per
  non-negotiable 7 an unread tag is FLAGGED, never assumed absent. "The top level carries
  no count" was therefore not a sentence anyone could write. With the container words in
  `objects.MEASURED_VALUE_TYPES`, the unmeasured residue at the top level went to nothing,
  and the difference between "not yet measured" and "measured, and it is not there" became
  statable.

**Alternatives considered:**

- **File `INCONCLUSIVE`.** Rejected on the facts. The probe ran over every save of every
  version pair this project parses and found a large tag population. Filing inconclusive
  would mean reporting "not yet measured" about something that was measured, which is the
  collapse the operator's ruling exists to prevent.
- **File `NO` and close ADR 0005 option (b).** Rejected, and this is the tempting one
  because the top-level measurement is clean and complete. It is refused because the
  containers on the target bound struct elements this project deliberately does not read -
  `objects.ContainerElement` records that a `None` value means NOT DECODED HERE and never
  EMPTY - and a count inside one of those interiors would be invisible to this sweep. A NO
  asserted over a region that was never read is the same class of error as a ceiling
  silently defaulted to a number.
- **Read the struct interiors here and finish the job.** Rejected as a seam violation. The
  container element interior is CS-829's, and opening it inside an experiment slice would
  put an unadjudicated grammar underneath a decision record.
- **Take the arithmetic route now that the component is understood.** Rejected outright.
  It is fenced by ADR 0005 and it is restated in this ADR's own fence list below.

## Decision

**The outcome is `NO AT THE TOP LEVEL, UNREAD BELOW IT`, and it is one outcome, not a
hedge between two.**

Stated in full: the `mInventoryPotential` reference population exists and is large; every
tag in it is accounted for; the component the reference names is read completely at its
top level and carries no slot count there, under the names ADR 0005 fixes or under any
other name at all; the reference chain stops at that component; and the only thing left
unread is the interior of its container elements, which CS-829 owns.

Concretely, four parts:

1. **`OVERCLOCK_POTENTIAL_SHARD_SLOTS` in `clockspeed/data/version.py` stays `None`.** This
   ADR measured no value and supplies none. ADR 0005 consequence 3 is unchanged and the
   interim behaviour it specifies still governs: solve at or below the un-sharded base, and
   where a solve would benefit from overclocking, report the ceiling as UNMEASURED rather
   than assume one.
2. **`clockspeed/solve/power.py` publishes no ceiling on the strength of this ADR.** The
   outcome licenses nothing to be written into the solver. That is not a scheduling note -
   it is the decision.
3. **ADR 0005 option (b) is NOT closed.** It is narrowed, and the narrowing is written
   down: the count is not at the component's top level, and the remaining place it could
   be is a struct element interior. A future ADR closes it in either direction; this one
   does not.
4. **The evidence is reproducible on demand rather than transcribed.** The CS-405 sweep
   module under `tests/save/` ships as a skip-if-absent, counts-only suite that runs
   against whatever library the machine has and skips cleanly on a machine with no game
   installed. It is deliberately not named here by identifier; see the note on citations
   at the foot of this ADR.

**What would settle it, stated plainly.** CS-829 reading the struct element interior, then
a re-run of that sweep with the slot-count search extended into the interior. If a count is
there, this ADR is superseded by the reading and the YES outcome is available for the first
time. If the interior is read and carries no count either, the outcome hardens into the full
`NO` that ADR 0005 said was worth as much as YES, and option (b) closes. Nothing else
settles it - in particular no amount of further reading at the top level, which is already
complete.

## Consequences

**The evidence, as a dated snapshot.** Measured on 2026-08-23 by the CS-405 sweep module
under `tests/save/` against this machine's live save library at game
build `++FactoryGame+rel-main-anniversary-2026-CL-502094`. Nothing was written to the save
directory or the game install; every save was opened read-only and reduced to integers
inside the sweep's own frame before any value returned.

**These numbers are a snapshot of a library that grows whenever the operator plays, and
the SHAPE is what is load-bearing, not the magnitudes.** They are dated for exactly that
reason, and they are stated here rather than in any docstring, roadmap line or auto-loaded
file. The suite derives them again on every run.

| What | Snapshot | The shape that matters |
|---|---|---|
| Saves of a parsed version pair | 12 | more than one, across all three tagged pairs |
| Records the tag walk covered | 129,775 | the whole library, not a sample |
| `mInventoryPotential` tags | 962 | large and non-empty - the probe RAN |
| Version pairs contributing tags | (10,36), (13,42), (14,52) | every parsed pair, so not a single-pair artifact |
| Resolved / unresolved / undecoded | 946 / 16 / 0 | partitions exactly; nothing dropped |
| Distinct target records read | 946 | one per resolution |
| Decoded top-level keys on targets | 3,306 | non-zero, so the absence is not vacuous |
| Targets bearing a slot-count key | **0** | **the decider** |
| Integer-valued top-level properties | **0** | no count under ANY name, not just the fixed ones |
| Top-level tags of an unmeasured type | **0** | the top level is COMPLETELY read - this is CS-830 |
| Onward `ObjectProperty` tags on targets | **0** | the chain stops; the residue is not another hop |
| Container tags on targets | 2,634 | what CS-830 made readable |
| Container element halves bounded | 8,313 | every one bounded and typed |
| Element halves left unread | 2,633 | exactly the `StructProperty` elements |
| `StructProperty` element halves | 2,633 | equal to the unread count - the residue is wholly CS-829's |

Two figures deserve their own sentence because each defeats a tempting shortcut:

- **Zero integer-valued top-level properties.** The slot-count name vocabulary alone would
  have been too weak to support any absence, because a count could be serialized under a
  name ADR 0005 never saw. The stronger measurement is that not one decoded top-level value
  on any of the targets is an integer at all. A slot count has to be an integer, so the top
  level carries none whatever the names.
- **The unread elements are exactly the struct elements, and they are not zero.** That is
  what forbids reading this ADR as a full NO, and it is asserted in the suite so the limit
  cannot be quietly lost.

**One measured fact that is NOT this ADR's to record.** The sweep also measured that every
unresolved `mInventoryPotential` reference carries an EMPTY object path. That is a finding
about the unresolved bucket's semantics and it belongs to CS-833, which owns that
question; it is reported to that item rather than concluded here. What this ADR takes from
it is only that the 16 are accounted for and none of them is a target that failed to be
read.

**What this costs.** The experiment ADR 0005 scheduled has run and the ceiling is still
unknown, so every consequence ADR 0005 and ADR 0006 stated about unmeasured ceilings
remains in force with no relief. A reader who wanted this item to unblock overclock advice
gets a narrowed question instead of an answer, and the narrowing is the whole return.

**What must NOT be re-pitched.**

Every fence in ADR 0005's re-pitch list applies unchanged, and all eight are restated here
rather than referenced, because a fence one document away from the decision it guards is a
fence that gets walked past:

1. **Do not go back into `Headers.zip` looking for this number, or for any other balance
   number.** The reason is structural: `EditDefaultsOnly` puts the value in a data asset,
   and the zip ships headers with no `.cpp`. A future search finds the same declarations
   and the same absence. The asset path carries the `CONVENTIONS.md` section 14 licence
   gate already recorded in `docs/GATED.md`.
2. **Do not cite the `2.5` in the comment at `FGBuildableFactory.h:521` as the ceiling.**
   It is an illustration of the power formula, worked with the wrong building class's
   exponent, and citing a code comment as ground truth is what `CONVENTIONS.md` section 15
   forbids.
3. **Do not write `2.5`, `250`, or `250 percent` into the solver, a doc, a test or a
   fixture as a measured value.** It is not measured. This ADR did not measure it either.
4. **Do not read `mMaxPotential` as the achievable ceiling.** It is the un-sharded base and
   the header says so in as many words. ADR 0006 gave it a name that cannot be mistaken for
   a ceiling precisely so this stays hard to do by accident.
5. **Do not derive the ceiling from `mPowerConsumptionExponent`, and do not run the
   arithmetic backwards.** The overclockable production buildings carry `1.321929`, and
   `2 ** 1.321929 = 2.500002` - the exponent sits within rounding of `log2( 2.5 )`. That is
   a relation between two balance values, not a measurement. The same applies inverted: do
   NOT take an assumed `2.5` back through `ceiling = mMaxPotential + slots *
   mExtraPotential` to conclude `slots = ( 2.5 - 1.0 ) / 0.5 = 3`. **This is the fence most
   likely to be crossed by someone who believes they have complied with every other one**,
   because the arithmetic uses only values shipped in the docs data and therefore FEELS
   derived rather than assumed. It was added to ADR 0005 by adjudication rather than by the
   probe, for exactly that reason. The slot count is measured or it is UNKNOWN.
6. **Do not conflate the two shard mechanics.** `PST_Overclock` / `mExtraPotential` raises
   the clock. `PST_ProductionBoost` / `mExtraProductionBoost` on `Desc_WAT1_C` is a
   different mechanic with its own exponent and its own non-uniform multiplier. A solver
   that adds them together is wrong twice.
7. **Do not treat `mPotentialShardSlots = 0` as zero slots.** It means the override is off.
   The `EditCondition` on the declaration is the proof.
8. **Do not add a second constant.** If the ceiling needs more than one written-down
   number, the equation was misread.

ADR 0006's fences also stand unchanged: do not rename `unsharded_clock_base` to anything
that reads as an achievable maximum, do not default an absent base to 1, and do not add the
ceiling operands to `clockspeed/data/registry.py`.

**Three fences this ADR adds, because running the experiment created three new ways to get
the number wrong:**

- **Do not cite this ADR as a `NO`, and do not close ADR 0005 option (b) on it.** It is a
  measurement of the component's TOP LEVEL. The struct element interiors were never read.
  A reader who takes "carries no slot count" out of the title and drops "at the top level"
  has inverted the one distinction the document exists to hold.
- **Do not attribute any of the integer container elements to the shard slot count.** The
  containers on the targets do bound integer elements, and the temptation to point at one
  and call it the answer is real. An element's meaning comes from its container's own tag
  and from the struct interior beside it, and neither is established by anything read here.
  Picking one on shape is an inference of exactly the kind fence 5 forbids.
- **Do not read a container's declared `element_count` as the slot count.** This is the
  same trap as fence 5 wearing new clothes: a count that happens to match a number someone
  already believes is confirmation of the belief, not a measurement of the field. The slot
  count is `mDefaultPotentialShardSlots` on the buildable subsystem. Until something on
  this machine is read that carries THAT value, no other integer becomes it by resembling
  it.

**What must be revisited if a premise changes.** Three premises, each of them asserted by
the shipped sweep rather than merely written here, so a premise that stops holding turns
the suite red instead of leaving this document quietly wrong:

- **A slot count appears on a target** - because the operator builds something new, or
  because a patch changes the serialization. The sweep asserts the absence at both bounds,
  the fixed name vocabulary and the integer test, so either one failing is the signal to
  supersede this ADR with the reading rather than a defect in the suite.
- **CS-829 reads the struct element interior.** The sweep asserts that the unread element
  count equals the struct element count, which stops holding the moment the interior
  becomes readable. That is the trigger for the re-run this ADR schedules.
- **A container word leaves `objects.MEASURED_VALUE_TYPES`.** The sweep asserts that
  membership directly, because the top-level residue this ADR reports as empty would no
  longer be empty and the conclusion would lose its premise.

**Which assertion catches which of those is deliberately NOT written here.** ADR 0008
governs it: a detection claim is a measured fact about the suite, `CLAUDE.md` section 4
already forbids restating a measured fact in prose, and a sentence naming the test that
reddens under a given fault rots on the next rename. The premises above are stated; the
mapping from premise to assertion is left to be read off the suite, which is where it
cannot go stale. **The same rule is why no test in this repository is named by identifier
anywhere in this document**, including the sweep module that produced the evidence table -
`tests/save/` holds one CS-405 module and it is findable by that item ID.

**Honest limits of this ADR.**

- The slot count is **still not measured**, and this ADR supplies no value for it.
- The measurement covers the component's **top level only**. The struct element interiors
  are bounded, typed and unread, and a count inside one of them would not have been seen.
- Everything here rests on the shipped decoder being right about what it decoded. This
  slice graded none of that: it consumes the CS-830 container decode, the CS-831 resolver,
  the tag walk and the value decoder, and grades only the population and the shape built on
  top of them. Where those are graded is their own items' suites.
- Everything is measured on **one machine, one library, one game build, on one day**. The
  library grows whenever the operator plays. The version pairs and the structural shape are
  what this ADR relies on; the magnitudes are dated and will move.
- No save file was copied, committed, or placed in a fixture directory; no account id,
  world name, user name or home path appears in any file this slice wrote; and the sweep
  reduces every save to integers before any value leaves its frame.
