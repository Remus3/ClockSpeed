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


## Wave 2 - verified against ground truth 2026-09-14, read before taking ANY item below

**THESE FIVE WERE SPEC-CHECKED BEFORE DISPATCH AND THE CHECK FOUND REAL DEFECTS.** Sibling
CS-1039 was checked the same way the same day and its filing carried three. Do NOT
re-derive what is recorded here; DO refuse to build past a defect it names.

**`docs/ARCHITECTURE.md` IS NOT ON ANY WRITE-LIST AND NO BUILDER MAY TOUCH IT.** It is
owned by a doc-sync pass the MERGER runs after the wave merges. The reason is measured:
`docs/ARCHITECTURE.md` lines 37 and 38 declare `progress/` and `advisor/` NOT BUILT, and
`tests/test_architecture_attributions.py::test_a_package_the_document_calls_not_built_really_is`
asserts a NOT-BUILT package binds NO public name. So CS-1043 and CS-1048 turn that arm RED
the moment they bind one. **THAT RED IS EXPECTED IN THOSE TWO WORKTREES AND IS NOT THE
BUILDER'S TO REPAIR** - repairing it locally means two worktrees editing one file and a
merge collision the wave was decomposed to avoid. `audit/` is already built and carries no
such gate, so CS-1041, CS-1042 and CS-1045 do not force the file at all; CS-1044 shipped
`footprint.py` touching neither it nor `audit/__init__.py`, which is the precedent.

**PER-ITEM DEFECTS FOUND. Each is a live instruction, not history.**

**CS-1041.** The LINE names FOUR questions - which belt feeds which machine, which node a
miner sits on, which connections share a power circuit, whether a machine is running - and
the acceptance grades only TWO. Belt-feeds-machine and circuit membership have no clause,
so an implementation answering two of four satisfies the filed acceptance. The LINE also
asserts as FACT the property name by which a miner names its node, which the note labels
ASSUMED; verify it before building on it. And the LINE's premise that `mCurrentRecipe` is
"decoded and then dropped" is OVERSTATED - the per-name value already reaches
`RecordProperties.values` at HEAD. What is genuinely missing is the TYPE-DISCRIMINATED,
tag-ordered reference population, which is CS-1039's half. Finally `mCurrentPotential` is a
FloatProperty and non-negotiable 6 forbids floats in the solve path: name the
float-to-Fraction bridge explicitly, because no clause currently requires one.

**CS-1042. NOT BLOCKED, AND THE BLOCKER FILED AGAINST IT WAS WRONG.** A spec check
reported that collectables do not cross the save seam because `WorldModel` carries no
`collectables` field. That read `WorldModel`'s own field list and MISSED THE NESTED MODEL.
Verified at four sites: `clockspeed/save/objects.py:1224` declares
`ObjectTable.collectables`, `objects.py:2831` populates it in `parse_body` - the levelled
reader real saves take - and `world.py:1753` publishes the whole `ObjectTable` as
`objects=table`. So `model.objects.collectables` is live TODAY. The idiom is already
established above the seam by `audit/footprint.py:1024`, `audit/placement.py:729` and
`surface/api/world.py:236`, all reading `model.objects.<x>`. Reading a fourth attribute of
the same published model is NOT reaching past `save/` - `ObjectTable` is the stated model.
CS-1042 therefore ships on its FILED write-list and needs no seam item in front of it.
**Do not re-file that blocker.** The lesson is narrower and worth keeping: a seam check
that reads only the top-level model's field list will report a live nested payload as
absent.

**CS-1042, the residual that IS real.** `collected_state_available` must be FALSE when
`parse_object_headers` was the reader. That path returns empty, and empty there means "saw
none", never "has none" - reporting it as a measured zero is non-negotiable 7's silently
wrong.

**CS-1042, the empty instance half, AND A COUNT OR A FLAG WILL NOT COVER IT.** It is published as `""` - no
Optional, no flag, no count - so a consumer joining on `instance_name` treats it as an
ordinary non-match and CANNOT DETECT that it dropped the row. Measured at
`tests/save/test_collectables.py:31-36`. An Optional, a flag and a count are each
individually INSUFFICIENT because each is ignorable. The requirement is a PARTITION WITH
CONSERVATION: every collectable row lands in exactly one bucket and the arm asserts
`joined + unjoinable == len(collectables)`, so a dropped row cannot be expressed. This is
CS-1042's to own - CS-1038 is CLOSED, and re-typing `Collectable` would relitigate it and
still not stop a drop. **The pair count is UNVERIFIED** - prose says 72 in
one place and 79 in another, and neither number exists in code. Measure it; do not repeat
either.

**CS-1043.** `clockspeed/progress/` holds only `__init__.py` - confirmed. The `FGSchematic`
exclusion is a frozenset at `clockspeed/data/registry.py:424` and is correctly cited as NOT
to be amended. Its carrier citations resolve only AFTER CS-1039 lands. The trap: NO budget
constant exists anywhere at HEAD, so the acceptance clause "reddens when the budget constant
moves" REQUIRES a named `Fraction` constant. A literal makes that clause unreddenable, which
is the CS-1039 defect shape exactly.

**CS-1045.** Its dependency on CS-1041 is PARTIAL, not total, and the note overstates it.
Arm one - the exact Fraction sum over built counts, and the NAMED gap for an unmodeled draw
- needs `placement.py` built counts and `solve/power.py` OUTCOME_UNMODELED and ZERO CS-1041
symbols. Only arm two, the producing flag and the published edge set, needs CS-1041. Arm one
may be built in parallel; only arm two must be sequenced.

**CS-1048.** ITS CENTRAL SUBJECT IS ABSENT FROM THE CODE. `mFogOfWarRawData` has ZERO hits
in any `.py` file at HEAD - it exists in docs and ADRs only. It does not cross the save seam,
and `RecordProperties` explicitly FORBIDS `bytes` fields on published world types, which is
exactly what a raster needs. The fog half therefore has no subject and cannot be built as
filed; the arm would grade synthetic bytes injected past the seam, which is a statement about
the fixture and not about the save. The BOUNDS half is sound and REFUTES the worry filed
against it: `WorldBounds` exists at `clockspeed/audit/placement.py:378` and is reachable via
`WorldPlacement.bounds`, so "reddens if a bounds field is read" is NOT vacuous. Split the
item or re-file the fog half; do not inject bytes and call it measured.

## CS-1041

### Filed 2026-09-13

**FOUR QUESTIONS, ONE CAUSE.** Which belt feeds which machine, which node a miner sits on,
which connections share a power circuit, and whether a machine is running are all answered
by references and per-machine properties that the decoder already recovers and the world
seam already drops. The mechanism is verified - an `ObjectProperty` value decodes, and
`RecordIndex.records_for` resolves an object path to every record bearing that name.

**WRITE-LIST:** NEW `network` and `machines` modules under `clockspeed/audit/`, and one
NEW arm module under `tests/audit/` for each of them. **DEPENDS ON:** CS-1039.
**TIER 2, NO GAME NEEDED.** **PUBLISHES:** `WorldNetwork` - mined node keys, belt and pipe
edges keyed by an INDEX into the placement population and NEVER by instance name, circuit
membership, and the counts that are its own denominators; `WorldMachines` - per-record
recipe, producing flag and overclock, each behind a declared availability flag.

**A PROXIMITY FALLBACK IS FORBIDDEN.** Non-negotiable 7 forbids it by name: nearest-neighbour
renders a wrong answer that reads like a right one. The acceptance arm must REDDEN when the
reference join is replaced by nearest-neighbour, or it grades nothing.

**ASSUMED, NOT MEASURED:** that a miner carries an ObjectProperty naming its node actor. The
MECHANISM is verified; the PROPERTY NAME is not. Measure it before building on it.

**A CORRECTION THIS ITEM CARRIES, BECAUSE IT IS A REFUTATION OF A SESSION-85 SPIKE CLAIM.**
A spike reported that CS-405 "probes the wrong field" because `mInventoryPotential` is an
ObjectProperty resolving to an inventory component rather than the overclock float. **That
correction was already known and the spike's claim is REFUTED.** Verified this session by
reading the module: `tests/save/test_inventory_potential.py`'s module docstring, under
its heading WHAT THE TAG WAS ALREADY MEASURED TO BE, already records that
`mInventoryPotential` decodes as an ObjectProperty - a level string and an object path - and
not as a bare integer, and states that this refutes the naive reading of YES without
establishing NO because a count may live BEHIND the reference; ADR 0009 records what the
experiment found and CS-831 shipped the reference following the module consumes. CS-405 is
CLOSED and its body is in `docs/history_notes.md`; no item is filed against it and nothing
in it needs repair. **The USEFUL half of the spike survives and lands here:** the live
overclock values are `mCurrentPotential` and `mPendingPotential`, measured 2026-09-13 at
five records each, and those are the fields this item reads. An ABSENT `mCurrentPotential`
is published as null and NEVER as 1.

**`mHasBeenLooted` IS SPARSE AND ITS ABSENCE MEANS DEFAULT-FALSE.** Read as "unknown" it
makes a plain unlooted pod unmeasurable; read as false it is correct. The model states which
reading it took rather than leaving it to a reader.

**BELT PATH GEOMETRY IS OUT OF SCOPE AND THAT IS NOT A DEFERRAL.** `mSplineData` and
`mSplinePoints` decode to zero elements today and are unblocked only by CS-1038. The
red-outline requirement needs the GRAPH, not the path. Belts render endpoint-to-endpoint and
the model declares `spline_geometry_available` false.

## CS-1042

### Filed 2026-09-13

**THE POLARITY IS COLLECTED, AND EVERY LATER READER MUST BE TOLD SO BEFORE THEY NAME A
FIELD.** The save's collectable section records what has ALREADY BEEN COLLECTED, as
(level, actor instance) pairs. Measured 2026-09-13: 72 pairs, none of which matches a live
record - which is exactly what identifies the polarity. **UNCOLLECTED is the live records
carrying transforms MINUS those pairs.** An agent that reads the section as a list of
uncollected items has it backwards. Live uncollected records carry transforms and are the
crystal classes and their marks, the spawnable pickups, the drop pods, the crash-site debris
and the resource deposits; the collected stems seen in the pairs are a different and
non-overlapping population.

**WRITE-LIST:** a NEW `collectibles` module under `clockspeed/audit/`, and one NEW arm
module for it under `tests/audit/`. **DEPENDS ON:** CS-1038 for the pairs and CS-1039 for the seam. **TIER 2, NO GAME NEEDED.**
**PUBLISHES:** `WorldCollectibles` - one row per uncollected item with its transform,
per-class counts, a skipped count, and a `collected_state_available` flag.

**THE ACCEPTANCE GRADES THE SUBTRACTION, NOT THE PLOTTING.** This is the single
highest-vacuity-risk arm in the session. An arm asserting only that three collectibles
render PASSES on an implementation that ignores the collected list entirely, which is the
whole defect. The arm must redden when the subtraction is removed.

**THE CLASS FILTER IS AN ALLOWLIST AND NEVER A DENYLIST**, authored from the measured stems,
with a PUBLISHED skipped count. A denylist on this project leaked four times - one defect
wore four spellings across four GREEN commits - and only an allowlist of good values held.
A skipped class is COUNTED, never silently dropped.

**ASSERT PER CLASS, NOT OVER THE POOL.** A threshold summed over a population is met by its
strongest member while the weakest goes unmeasured with the acceptance clause still passing.

**THE SAVE LIBRARY MOVES WHILE YOU WORK, so no acceptance here may state a hardcoded save
count.** The operator plays while agents run: the record total was probed twice inside one
session on 2026-09-13 and had moved between the two reads. A count written into a test is a
lie with a timestamp on it (`CLAUDE.md` section 4). Every equality below is over a
population DERIVED from the payload being read, compared against the reader's own output,
never against a literal.

## CS-1043

### Filed 2026-09-13

**THE HOLE IS AT THE BOTTOM.** `clockspeed/data/registry.py` excludes `FGSchematic` from the
modelled groups and `clockspeed/progress/` holds a docstring and a seam comment and no code
at all, so the project cannot name one milestone, its cost, its tier, or a space-elevator
phase cost. That is the whole of the milestone-requirements panel.

**WRITE-LIST:** NEW `milestones` and `phases` modules under `clockspeed/progress/`,
and a NEW `tests/progress/` package - its `__init__` plus one arm module for each of the
two modules above. **DEPENDS ON:** CS-1039 for `UnlockState`, including the HUB
tier from `mTradingPostLevel` and the phase from `mCurrentGamePhase`. **TIER 2, NO GAME
NEEDED** - a hand-authored synthetic schematic document; the rule suite must run with no
install.

**IT DOES NOT EDIT `clockspeed/data/registry.py`.** That module already rules that
`FGSchematic` belongs to the progression layer. This item FOLLOWS that ruling rather than
re-opening it, and consumes the shipped Document through a `SchematicSource` protocol
declared here and parameterised at the wiring site - the `WorldProvider` idiom.

**THE SCHEMATIC-TO-REGISTRY JOIN IS THE RESOLVED CONTENT ASSET PATH** of an
`mPurchasedSchematics` reference. That is the measured join key. **Do not invent a
name-matching heuristic beside it.**

**ELEVATOR ITEMS ALREADY DELIVERED ARE BLOCKED ON THE KEYSTONE.** They sit inside the space
elevator's input inventory and need CS-1038's container stacks. Until that lands the phase
model publishes `delivered_available` false and shows REQUIRED only. A phase with no cost
entry is null and never zero.

**NO FLOAT REACHES A RATE.** The two-hour completion budget is held as a `Fraction`, and the
every-machine-at-full-clock assumption is named ON THE MODEL rather than in a comment.

## CS-1045

### Filed 2026-09-13

**TWO REQUIREMENTS WITH NO NUMBER BEHIND THEM.** `/api/power` answers for ONE building
against the registry alone with no world bound into it, nothing multiplies a per-class draw
by a built count, and no rule anywhere compares a machine's input to its output.

**WRITE-LIST:** a NEW `balance` module under `clockspeed/audit/`, and one NEW arm
module for it under `tests/audit/`. **DEPENDS ON:** CS-1041. **TIER 2, NO GAME NEEDED** - synthetic registry and synthetic
world. **PUBLISHES:** `WorldBalance` - production and consumption, an unmodeled-contributor
count, the imbalanced record set, and the connected edge set the panel outlines red.

**THE CONFIDENT ZERO IS THE FAILURE MODE HERE.** `clockspeed/solve/power.py`'s unmodeled
cases must EACH contribute a NAMED gap to the total and never a zero. `contract.encode`
refuses a float; a zero it happily accepts, and a zero is a lie a power plan cannot detect.
This is the silently-wrong half of non-negotiable 7 wearing a number.

**ASSERT PER CONTRIBUTOR, NOT OVER THE POOL.** A total that is correct in aggregate can hide
a class whose draw was never modelled; the arm must name the gap rather than measure the sum
alone.

**THE WHOLE-WORLD PAIR DOES NOT NEED THE CIRCUIT GRAPH** and is what this item ships. The
per-circuit split does need it and is a stated stretch, recorded here so a later reader does
not mistake its absence for an oversight.

## CS-1048

### Filed 2026-09-13

**TWO OPERATOR REQUIREMENTS DIED THIS SESSION AND THIS ITEM IS THE HONEST SUBSTITUTE FOR
BOTH.** Node purity is structurally absent from every save - closed by declaration at
CS-1040, not by sampling - and the in-game map is RENDERED LIVE by a scene-capture actor
rather than shipped as a texture, so there is no underlay image to extract. The pressure to
ship something that merely LOOKS like those two is exactly how a silently wrong answer gets
built, and non-negotiable 7 forbids it.

**WHAT IS FREE AND IN HAND.** The save itself carries `mFogOfWarRawData`, proved
structurally on 2026-09-13 to be exactly a 1024 by 1024 byte square - reading that many
bytes lands exactly on the next property tag. That is a map-shaped raster of the player's
own explored area, in a file this project is already allowed to read.

**WRITE-LIST:** a NEW `underlay` module under `clockspeed/audit/` with one NEW arm
module for it under `tests/audit/`, a NEW `annotations` module under `clockspeed/advisor/`,
and a NEW `tests/advisor/` package - its `__init__` plus one arm module for that. **DEPENDS ON:** CS-1039. **TIER 2, NO GAME NEEDED** -
synthetic raster bytes and a synthetic annotation store.

**THE REGISTRATION FENCE, WHICH INVALIDATES THE OBVIOUS IMPLEMENTATION.**
`WorldBounds` (`clockspeed/audit/placement.py::WorldBounds`) bounds THIS WORLD'S
PLACEMENTS and moves
every time the operator builds anything. **A transform registered against it drifts under
the operator's own hands and must NEVER be built.** The honest registration without the
shipped constants is the raster's own fixed square grid plus a config-overridable world
origin and scale, DECLARED estimated, never derived from the placement box. The arm must
redden if a bounds field is read at all.

**ASSUMED, NOT MEASURED:** that the raster is spatial rather than an opaque blob that
happens to be that size. The structural proof shows only its LENGTH. Publish it as bytes
with declared dimensions and claim NO orientation and NO origin until one is measured.

**PURITY IS AN OPERATOR ANNOTATION AND NEVER A DERIVATION**, and the wire says which it is
on every row - `provenance = "operator"`. Plot every node unlabelled and shape-coded by
CLASS, the one thing actually known; label only scanned nodes and those linked by a built
extractor's own resource reference. Reuse the existing warning's wording VERBATIM:
"unmeasured rather than unremarkable".

**`mResourceDepositTableIndex` IS READ AS AN OPAQUE INDEX** with its lookup table declared
unavailable. It is a SaveGame property on the deposit records - the one exception to the
purity verdict. An index without its table is honest; an invented resource name is not.

**THE ANNOTATION STORE IS PERSONAL DATA.** It is keyed by the save header's world token,
lives under gitignored `data/`, is NEVER committed, and its instance names never reach the
wire - a row publishes the annotation and the node's INDEX in the served population, the
same substitution the world properties model already makes. It **writes atomically**
(non-negotiable 5); it is the first thing in this session's plan that writes a file another
process may read.
