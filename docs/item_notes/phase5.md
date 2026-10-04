# Clockspeed - live per-item detail, phase 5 - advisor and audit

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the leaf membership rule routing every OPEN item, the verbatim
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

## Wave 2 - the pre-dispatch spec check, filed 2026-09-14

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
Verified at four sites: `clockspeed/save/objects.py::ObjectTable` declares
`ObjectTable.collectables`, `clockspeed/save/objects.py::parse_body` populates it - the levelled
reader real saves take - and `world.py` publishes the whole `ObjectTable` as
`objects=table`. So `model.objects.collectables` is live TODAY. The idiom is already
established above the seam by `clockspeed/audit/footprint.py`, `clockspeed/audit/placement.py` and
`clockspeed/surface/api/world.py`, all reading `model.objects.<x>`. Reading a fourth attribute of
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
`tests/save/test_collectables.py`. An Optional, a flag and a count are each
individually INSUFFICIENT because each is ignorable. The requirement is a PARTITION WITH
CONSERVATION: every collectable row lands in exactly one bucket and the arm asserts
`joined + unjoinable == len(collectables)`, so a dropped row cannot be expressed. This is
CS-1042's to own - CS-1038 is CLOSED, and re-typing `Collectable` would relitigate it and
still not stop a drop. **The pair count is UNVERIFIED** - prose says 72 in
one place and 79 in another, and neither number exists in code. Measure it; do not repeat
either.

**CS-1043.** `clockspeed/progress/` holds only `__init__.py` - confirmed. The `FGSchematic`
exclusion is the frozenset `clockspeed/data/registry.py::UNMODELED_GROUP_SHORT_NAMES` and is correctly cited as NOT
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
against it: `clockspeed/audit/placement.py::WorldBounds` exists and is reachable via
`WorldPlacement.bounds`, so "reddens if a bounds field is read" is NOT vacuous. Split the
item or re-file the fog half; do not inject bytes and call it measured.

## CS-1058

### Filed 2026-09-14

**TWO CLOSED ITEMS DECLARE THIS ABSENCE AND NEITHER OWNS IT.** CS-1041's item LINE named
which belt feeds which machine and which connections share a power circuit; its ACCEPTANCE
graded neither, so an implementation answering two of its four questions satisfied the
filed criterion. It shipped `belt_topology_available` and `circuit_topology_available` as
hardcoded False with a warning. CS-1045 then had to DERIVE its own edge availability from
that flag, because there was no edge set to outline. An absence two items report and none
owns is how a gap becomes permanent.

**THE AVAILABILITY FLAGS MUST STOP BEING LITERALS.** Today both are written False. After
this item they must be derived from whether an edge set was actually built - a literal True
would pass every arm that only reads the flag, which is the vacuity shape this repo has
measured repeatedly. Grade the flag against the thing it describes, not against itself.

**PROXIMITY IS THE WRONG JOIN AND THE ARM MUST SAY SO.** A belt edge derived from
nearest-neighbour looks right on a tidy factory and is wrong wherever belts cross. The arm
reddens when the join is replaced by proximity - the same control CS-1041 used for the
miner-to-node join, and the reason that join survived review.

**WATCH THE POPULATION.** CS-1041 measured that the property a miner would use to name its
node DOES NOT EXIST - ADR 0003 found zero occurrences across three worlds and four builds -
and the join had to be name-agnostic over the typed reference population instead. Do not
assume a conveyor names its endpoints by a property either; measure before keying on one.

### Acceptance

a new arm module under `tests/audit/` builds a synthetic world of two machines joined by one conveyor and asserts the published edge set names that pair and no other, reddening when the join is replaced by proximity, and a second arm asserts two generators on one circuit share a circuit id while an unconnected third does not, and BOTH availability flags are derived from whether an edge set was actually built rather than written as literals

### Full headline

nothing can say which belt feeds which machine or which connections share a power circuit: CS-1041's line named both and its acceptance graded neither, and `clockspeed/audit/network.py` therefore hardcodes `belt_topology_available` and `circuit_topology_available` False, which CS-1045 then had to derive its own edge availability from - so two closed items both declare the same absence and no item owns it

## CS-1059

### Filed 2026-09-14

**THE PANEL IS A COMPARISON AND ONLY ONE SIDE EXISTS.** CS-1045 delivered the exact world
DRAW as a Fraction sum over built counts. Generated power has no `Building` field and no
extractor anywhere, so `production_available` is published False with a warning rather than
a zero. The headline the item promised - production versus consumption - currently has one
operand.

**THE REFUSAL TO PUBLISH A ZERO IS THE PRECEDENT TO COPY.** `DrawGap` declares no megawatts
field at all, so an unmodeled draw CANNOT be represented as zero; the impossibility is
structural and is graded off the dataclass's own fields. Generated power must be built the
same way. A zero that means "not modelled" is a number that looks like a measurement, which
is non-negotiable 7.

**THE FLAG IS PART OF THE ACCEPTANCE, NOT PLUMBING.** `production_available` must become True
only when a production figure was actually computed, and an arm must redden if it is written
as a literal. This is the same defect CS-1058 carries for the topology flags, and both were
created by the same habit of declaring an absence with a constant.

### Acceptance

a new arm module under `tests/audit/` asserts generated power is the exact Fraction sum over built generators, that a generator class the registry does not model contributes a NAMED gap rather than a zero exactly as `DrawGap` already refuses to carry one, and that the balance's own `production_available` flag becomes True only when a production figure was actually computed - reddening if it is written as a literal

### Full headline

the power panel is production versus consumption and only consumption exists: CS-1045 delivered the exact world draw but found NO `Building` field and no extractor for generated power anywhere, so it publishes `production_available` False with a warning rather than a zero, and the headline comparison the item promised has one side

## CS-1043

### Filed 2026-09-13

**REPAIRED 2026-09-14 (session 95).** The acceptance now NAMES the constant into
existence: it reads "reddens when the budget moves - which REQUIRES that budget to be a
NAMED `Fraction` constant in the new module, because a literal at the site makes this
clause unreddenable". The trap below is what the repair closes; it is kept because the
reasoning is what stops the next filing from repeating it.

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

### Acceptance

a new arm module under `tests/progress/` builds a synthetic schematic document and a synthetic unlock state, asserts each required rate is the exact Fraction cost over budget with no float anywhere, and reddens when the budget moves - which REQUIRES that budget to be a NAMED `Fraction` constant in the new module, because a literal at the site makes this clause unreddenable and that is the CS-1039 vacuity shape by name, and a second new arm module there asserts a phase cost renders machine, miner and resource as distinct keys and that a phase with no cost entry is null rather than zero

### Full headline

`clockspeed/data/registry.py` excludes `FGSchematic` and `clockspeed/progress/` holds no code at all, so the project cannot name one milestone, its cost, its tier or a space elevator phase cost, which is the whole of the milestone requirements panel

## CS-1048

### Filed 2026-09-13

**SPLIT 2026-09-14 (session 95), AND THE SPLIT LINE IS NOT WHERE THIS NOTE PROPOSED IT.**
The fog raster and the whole underlay - including the registration clause this note wanted
to keep here - moved to CS-1061. What remains in CS-1048 is the ANNOTATION half alone:
an annotated purity is never reported as derived, the annotation round-trips keyed by
instance name, and its published provenance reads operator rather than measured. Its
write-list narrows to a NEW `annotations` module under `clockspeed/advisor/` and a NEW
`tests/advisor/` package. The reasoning for moving the registration with the raster is recorded in
CS-1061's own section, not repeated here.

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

### Acceptance

a new arm module under `tests/advisor/` asserts an annotated purity is never reported as derived - the annotation round-trips keyed by instance name and its published provenance reads operator rather than measured

### Full headline

node purity is structurally absent from every save and the in-game map is rendered live rather than shipped, so the underlay and the purity variant have no derivation and the only dishonest move available is to invent one, and nothing records an operator's own knowledge of a node - THE FOG AND UNDERLAY HALF WAS SPLIT OUT TO CS-1061 IN SESSION 95 because its subject is absent from the code and its registration clause has nothing to register without it

## CS-1061

### Filed 2026-09-14, split out of CS-1048

**ITS SUBJECT IS ABSENT FROM THE CODE, AND THAT WAS VERIFIED RATHER THAN INHERITED.**
`mFogOfWarRawData` has ZERO hits in any `.py` file in the primary checkout. Its only
non-doc hit anywhere is a GENERATED header-index artifact under the gitignored `data/`
directory of a stale agent worktree - the artifact of the 2026-09-13 probe that proved the raster is exactly a 1024
by 1024 byte square. **The structural proof was real; it simply never landed in a
module.** A shipped reader does not exist and the raster does not cross the save seam.

**THE FENCE IS DELIBERATE AND IT IS GRADED.** `clockspeed/save/world.py` states that
neither published type declares a `bytes` or a `Path` field, and gives the reason: a
retained payload is the one thing no higher layer may hold. It is asserted by
`tests/save/test_world.py::test_no_published_world_type_annotates_a_carrier_field`. A
1024 by 1024 raster is 1048576 bytes of exactly that. So this is not an oversight to
route around.

**THE SEAM QUESTION COMES FIRST AND IT IS A DESIGN DECISION, NOT AN IMPLEMENTATION.**
Either the raster is carried by a published type that is not a world property value, or
the fence is amended for this one carrier with a named reason and its arm updated in the
same diff. **IT IS NEVER QUIETLY WIDENED.** Route the choice to an adjudicator before any
file is scaffolded.

**DO NOT INJECT SYNTHETIC BYTES PAST THE SEAM AND CALL IT MEASURED.** An arm over bytes
handed straight to the underlay module grades the fixture and says nothing about any
save. That is the shape session 94 caught reading zero records on every real save while
3153 tests stayed green.

**WHY THE REGISTRATION HALF CAME WITH IT RATHER THAN STAYING IN CS-1048.** The item note
at HEAD proposed keeping the bounds clause in CS-1048 on the grounds that `WorldBounds`
exists and is reachable - true, `clockspeed/audit/placement.py::WorldBounds` via
`WorldPlacement.bounds`. But the transform's whole SUBJECT is the underlay's own grid, so
without the raster that clause has nothing to register either. Splitting there would have
left CS-1048 carrying a second clause with no subject, which is the defect being repaired
rather than a smaller version of it.

**THE REGISTRATION FENCE SURVIVES THE SPLIT INTACT.** `WorldBounds` bounds THIS world's
placements and moves every time the operator builds anything, so a transform fitted to it
drifts under their own hands and must NEVER be built. The honest registration is the
raster's own fixed square grid plus a config-overridable world origin and scale, DECLARED
estimated. The arm must redden if a bounds field is read at all.

**ASSUMED, NOT MEASURED:** that the raster is spatial rather than an opaque blob that
happens to be that size. The structural proof shows only its LENGTH. Publish it as bytes
with declared dimensions and claim NO orientation and NO origin until one is measured.

**DEPENDS ON:** CS-1039. Phase 6 consumes this for the underlay and its registration -
see the panel item's `DEPENDS ON` line, which names this item rather than CS-1048 for
that half.

---

### Acceptance

the raster crosses the save seam by whichever route is adjudicated, a new arm module under `tests/audit/` asserts its declared dimensions are derived from its own byte length rather than stated, and asserts the published transform names a config origin and scale rather than any `WorldBounds` field and reddens if a bounds field is read at all - that box bounds THIS world's placements and moves whenever the operator builds, so a transform fitted to it drifts under their hands - and the orientation and origin stay DECLARED ESTIMATED until one is measured

### Full headline

the map underlay has no subject in the code: `mFogOfWarRawData` was proved structurally in a 2026-09-13 probe to be a 1024 by 1024 byte square but has ZERO hits in any shipped module, it does not cross the save seam, and `clockspeed/save/world.py` fences every published world type off `bytes` and `Path` fields with a stated reason - a retained payload is the one thing no higher layer may hold - graded by `tests/save/test_world.py::test_no_published_world_type_annotates_a_carrier_field`, so an arm over synthetic bytes injected past that seam would be a statement about the fixture and never about the save - THE SEAM QUESTION COMES FIRST AND IS A DESIGN DECISION FOR AN ADJUDICATOR, not an implementation: either the raster is carried by a published type that is not a world property value, or the fence is amended for this one carrier with a named reason and its arm updated in the same diff, and IT IS NEVER QUIETLY WIDENED

## CS-1064

### NOTE - filed 2026-09-14 under CS-301

The gap kinds `clockspeed/audit/balance.py` publishes are `power.py`'s own shape constants carried
verbatim, and two of them - `SHAPE_VARIABLE` and `SHAPE_RANGE_ONLY` - are no longer gaps in the sense
the tally means. They have bounds now. **Do not close this by deleting those two from `GAP_KINDS`**:
a bounded class still contributes no single number to a scalar total, so dropping it from the tally
without publishing an interval loses the load entirely and reads as a smaller gap count, which is the
opposite of what happened. The interval has to exist before the tally changes.

The measurement that makes the second acceptance arm necessary: on the shipped document the three
variable-power buildings declare ranges of 250 to 1500, 100 to 400 and 0 to 2000, so an interval over
any world holding one of them has ends that genuinely differ. An arm asserting only that the two ends
SUM correctly passes on a world where they are equal, and a world where they are equal is a world
this item changes nothing about.

### Acceptance

the balance publishes a bounded total whose low and high ends are the exact Fraction sums of every bounded contribution, a class that is bounded is no longer counted in the unmodeled-gap tally, and a class that is genuinely unmodeled still is - proven by an arm that reddens when a bounded class is folded back into the gap list and by an arm asserting the two ends DIFFER on a world holding one variable-power building, because equal ends would make the interval unreddenable

### Full headline

`clockspeed/audit/balance.py` still reports every variable-power and struct-range building as an unmodeled DRAW GAP, but CS-301 made both shapes BOUNDED, so the world consumption total drops three of the largest loads in the game while a narrower answer now exists

## CS-1236

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. FIT CHECKED 2026-10-04: `clockspeed/advisor/` holds no code, so the advice and tier-3 halves wait on CS-500's trace engine; the audit and power half can reuse CS-1235's materialiser. The overlay lives only in the per-world store; the save is never touched (non-negotiable 1).

### Acceptance

an overlay of edits (add N machines of a recipe at a clock, swap a recipe, remove a group, raise a target) round-trips through the API; the same save plus the same overlay gives byte-identical output on two runs; a test asserts no file under the save or install directory changes mtime during an overlay evaluation; once CS-500's trace exists the tier-3 derivation names each overlay edit as a trace step

### Core half measured 2026-10-04

MET: `clockspeed/audit/overlay.py` - add, remove, swap and set-demand edits applied as a pure
transform with one record per edit, flow and draw recomputed before and after, a wrong
building or an unknown recipe refused or skipped by name, never clamped; byte-identical
output across two processes with different hash seeds; and a no-write arm over a temp save
and install tree with every file entry point blocked, `tests/audit/test_overlay.py`. Two
adversary rounds, the first REFUTED and repaired. OPEN, and the only reasons this item is
not closed: (a) the API round trip - route handlers receive path parameters and no request
body (`clockspeed/surface/api/contract.py`), so accepting an overlay needs a decided handler
contract change, not a new route alone; (b) the tier-3 trace step and per-world overlay
storage, which wait on CS-500. A clock above the un-sharded base is FLAGGED rather than
refused because `clockspeed/solve/power.py::clock_ceiling` publishes no ceiling figure.

## CS-1238

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. FIT CHECKED 2026-10-04: the advisor rule registry does not exist yet, so the rule half rides CS-500; the audit half fits today - every `WARN_*` code `clockspeed/audit/__init__.py` re-exports. This is a product test over the product's own checks, not a new guard tool.

### Acceptance

enumerating the audit warning codes yields a minimal synthetic fixture for every code in which that code fires, asserted; a code without one is a failing test, and removing one fixture reddens exactly one test that names the code; the same holds for every advisor rule id once CS-500's registry exists

### Audit half measured 2026-10-04

The AUDIT HALF is met: `tests/audit/test_every_warning_fires.py` derives the audit warning
set from the package and fires every code from a synthetic fixture, and dropping one entry
reddens exactly the arm naming that code. It surfaced one code no test fired before,
`WARN_FOOTPRINT_EXTENT_UNAVAILABLE`. The ADVISOR-RULE half stays OPEN until CS-500's rule
registry exists; that is the only reason this item is not closed.

## CS-1240

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Key every registry and save join on the stable class identifier, never a display name; one case-and-punctuation fallback; then flag, skip and list.

### Acceptance

a fixture with one unknown class yields a flagged-and-skipped record with no exception and the panel lists it with a count and first-seen save; a display-name change in the fixture registry changes no output

## CS-1241

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. When the build pin moves, a rule whose meaning differs by build selects the pinned build's variant rather than assuming the newest.

### Acceptance

a synthetic two-build fixture where one recipe changed yields different solves per pinned build; the decisions table has no row without a test

## CS-1242

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Generated, never hand-written (section 4 rule on measured numbers). Sources are the shipped docs file and the save only.

### Acceptance

the census is generated by the extraction step and compared against the pinned build's census, a change being reported rather than absorbed; a fixture with a missing required field fails the build step naming the field

## CS-1243

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Coordinates come only from the save or extraction - never a wiki (section 7).

### Acceptance

a synthetic map fixture with three nodes and one gated region excludes the gated node until the unlock flag is set; distances are exact rationals or integers; claims rank by reachability band, then yield

## CS-1244

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Builds on `clockspeed/solve/optimize.py`'s exact objectives; player-tunable weights stay in `BACKLOG.md` until this lands.

### Acceptance

each named objective has golden cases; ties break on a documented stable key; switching objective changes ranking but never the plan arithmetic; a badge records the strongest threshold cleared in fixed ladder order

## CS-1245

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Stays behind `OptimizerBackend`; no external optimizer (section 7).

### Acceptance

a cap hit in a fixture produces a recorded step naming the cap and the trim rule; two runs choose the same candidate; the chosen candidate is the smallest that passes every validation check, not the first built

## CS-1246

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Waits on CS-500's ledger; aging is derived from the ledger's shown-and-deferred record, never from a timer.

### Acceptance

a fixture with one large and several small cards brings the large card to the top after the configured number of evaluations; the same ledger state gives the same order

## CS-1247

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. A pure function over the four advice domains.

### Acceptance

a fixture with ten power cards and two milestone cards shows both milestone cards in the top five; the interleave is a pure function with golden cases

## CS-1248

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Rates carry their unit in the model type; only rendering rounds, through CS-1239's one rounding function.

### Acceptance

a type-level or runtime check refuses adding two rates of different units; a per-cycle value fed where per-minute is expected is refused; raw and display values are distinct fields wherever they travel

## CS-1249

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. `clockspeed/solve/ratio.py` already solves the byproduct loop of the synthetic corpus exactly; this item makes cycle detection explicit and fences unsupported shapes.

### Acceptance

a two-recipe loop fixture solves to exact Fractions; an unsupported cycle shape is flagged and skipped, never fatal; any graph sorted topologically has a cycle test

## CS-1250

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. A product test, not a new guard tool (section 7, product before process).

### Acceptance

a synthetic world with one object reachable two ways (grouped structure, sub-object, linked inventory) reports it once in every audit total

## CS-1251

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Never lock or touch the file (non-negotiable 1).

### Acceptance

a test writes a fixture save in two chunks to a temp directory and the reader does not parse the partial file; the read path opens read-only; a burst of autosaves is debounced to the newest settled file

## CS-1252

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. The stamp carries the save timestamp and the build pin, never a world name or a path (non-negotiable 3).

### Acceptance

a fixture with a newer save on disk sets the stale flag in the API payload; a moved build pin sets it too; the stamp contains no world name or path

## CS-1253

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Both layers stay separate (section 7); writes stay atomic (non-negotiable 5). Waits on CS-500's ledger.

### Acceptance

a v1 fixture loads under v2 with declared defaults; a corrupt fixture is refused and its bytes are unchanged afterwards; each store records its schema version and the tool version that wrote it

## CS-1264

### Filed 2026-10-04 by CS-1263's adversary pass

`clockspeed/audit/balance.py::clocked_draw_of` prices an elided or tagged machine by its clock
alone and never checks a production boost, so the balance reason line is false for a boosted
machine. The 40-save library carries no boost tag, so no real save exercises it yet; the fix must
not invent a boost reading, it must refuse or name what it cannot read.

### Acceptance

a machine carrying a production-boost tag is either priced by the boosted power law or published as a named gap, never priced as unboosted; an arm with a synthetic boosted machine reddens when the boost is ignored; the elided-default count excludes a boosted machine

## CS-1265

### Filed 2026-10-04 by CS-1263's adversary pass

`clockspeed/audit/flow.py` returns `GAP_FLOW_CLOCK_UNREAD` for a machine with no clock tag, which
is most of the library, while `clockspeed/audit/balance.py` prices the same machine at the elided
default under CS-1263's ruling. Two audits over one world disagree about one fact. The CS-1263
decision governs: an untagged machine on a cleanly read payload is at the class default unless a
measured save shows otherwise.

### Acceptance

the flow audit reads the same `overclock_elided` mark the balance reads and treats an elided machine as at the class default, counted, while a refused or unread clock stays a named gap; one arm drives both audits over one synthetic world and asserts they classify every machine's clock the same way

## CS-1266

### Filed 2026-10-04 by CS-500's S4 adversary pass

`power.draw_incomplete` scopes "complete" to the audit's considered population, but the clocked
draw can report complete while omitting a built power consumer that has no clock, no recipe and no
producing tag. Nothing cross-checks the considered population against what is actually built.

### Acceptance

the audit publishes, like for like, the count of built power consumers and the count its clocked draw considered, and a consumer the draw omits is named; an arm with a synthetic world holding such a consumer reddens when the omission goes unnamed

## CS-1268

### Filed 2026-10-04 by CS-500's close

`BOOTSTRAP.md` section 5.2 requires that `completed` is set automatically when the world state
satisfies the advice, and calls that transition worth surfacing. It is never set:
`clockspeed/advisor/ledger.py` offers no listing of a world's recorded cards, so
`clockspeed/advisor/advise.py::advise` sees only the cards that fire now and cannot detect a
recorded card that has vanished; and `advise` writes neither store by design
(`tests/advisor/test_advise.py::test_advise_never_writes_either_store`), so the transition
needs a stated write path. A Phase 5 product item, not tooling.

`BOOTSTRAP.md` does NOT state what a completed card does when its rule fires again. Ruled here
on the section's own wording - `completed` means the world satisfies the advice, so a firing
rule means it no longer does: a completed card that fires again is surfaced as `new`, and a
card the player set `dismissed`, `snoozed` or `pinned` keeps that state and is never marked
`completed` over it. Recorded with this filing; an adjudicator may overrule it before build.

### Acceptance

red first: a synthetic world where a card is recorded `accepted` or `new` and shown, then a reload in which its rule stops firing, leaves that card `completed` in the per-world ledger, read back from disk, and the transition is surfaced in the result; the ledger can list one world's recorded cards; a `completed` card whose rule fires again is surfaced as `new`; a `dismissed`, `snoozed` or `pinned` card whose rule stops firing keeps its state; two runs over the same inputs give the same states

## CS-1270

### Filed 2026-10-04 by CS-500's close

CS-500 closed with `clockspeed/advisor/advise.py::advise` and `world_inputs(balance, unlocks)`,
but nothing builds the `WorldBalance` that `world_inputs` takes from a `WorldModel` and a
`Registry`. Doing it means calling `placement_of`, `machines_of`, `network_of` and `balance_of`
from `clockspeed/audit`. The surface may not do that. `tests/surface/test_map_vocabulary.py::test_no_shipped_surface_module_reaches_the_machines_model`
(CS-1189) refuses any surface module that reaches `clockspeed.audit.machines`, and an
adjudicator ruled on 2026-10-04 that the guard stays as it is: composing the audit models is
the advisor's job, because the advisor is the layer that consumes audit.

The surface half is already built and waits for this item.
`clockspeed/surface/api/advice.py` turns an `Advice` into the listing body (tiers 1 and 2,
with state, `snoozed_until`, `muted` and `visible`) and the derivation body (tier 3). Its
refusals are 503 `no_save`, `no_game_install` and `advice_store_unreadable`, and 400 for an
unknown parameter or card. It is graded in `tests/surface/test_advice.py` on a stub source,
and it is not in the route table yet, so both templates still answer 501 through
`clockspeed/surface/api/pending.py`. The concrete source does not exist yet: a
`clockspeed/surface/providers.py` class that reads both stores and takes an injected clock
belongs to this item, because a new provider class also enters the
`tests/test_repr_rendering.py` population and has to be recorded there.

**WRITE-LIST:** `clockspeed/advisor/advise.py` (the input builder),
`clockspeed/surface/api/routes.py`, `clockspeed/surface/api/pending.py`,
`clockspeed/surface/api/contract.py` (`OPEN_BLOCKERS` drops CS-1270),
`clockspeed/surface/providers.py` (the store-reading source), `tests/test_repr_rendering.py`
(that class's population row and forced construction), `tests/surface/audit_harness.py`
(a canned 200 for `/api/advice`), and the matching surface and advisor test modules.

### Acceptance

red first: an advisor function builds `WorldInputs` from one synthetic `WorldModel` and one synthetic `Registry` through the audit constructors, and no `clockspeed/surface` module imports `clockspeed.audit`; `routes.build_routes` publishes `advice.routes` bound to a provider source that reads the ledger and the mutes with an injected clock and uses that function, and the source answers None over a corrupt store; `GET /api/advice` answers 200 with the `advice.DATA_KEYS` body and `GET /api/advice/<id>/derivation` answers 200 with tier 3 for a listed card over the real route table; `pending.UNBACKED` and `pending.BLOCKERS` lose both templates and `contract.OPEN_BLOCKERS` loses CS-1270; the CS-1189 machines-seam guard stays unedited and green
