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

## CS-1373

### Acceptance

Phase 5, tier 2, open before v1. A selected schematic plans its cost items' rates through
`clockspeed/progress/milestones.py::milestone_requirement` as one request and one route, on a
concrete `SchematicSource`, which CS-1046 also names; an arm on a synthetic catalog reads that
route's card. Measured route solve: 39 of 42 milestones sinkable, 11 balanced, 16 above the cap.

### Filed 2026-11-03 (session 155) by the CS-1371 clause ruling

**LOWERING** against `CLAUDE.md` section 7 and `BOOTSTRAP.md` pillar 4, by CS-1371 offering items and no
schematic on its selector; ground build cost and a missing concrete source.

## CS-1374

### Acceptance

Phase 5, tier 2. A redesign card names the schematic and tech tier for each locked recipe, its route
prefers what a milestone unlocks over a hard-drive alternate, and an arm grades ascending tech tier.
Measured: whole-path join 291 of 291 automated recipes, 19 by more than one schematic. After the machine join, one 11-recipe world's route to Desc_IronPlateReinforced_C takes hard-drive Recipe_Alternate_ReinforcedIronPlate_2_C though the world holds the plain recipe: both count 1 locked.

### Filed 2026-11-03 (session 155) by the CS-1371 clause ruling

**LOWERING** against "several tiers" in the CS-1371 clause 2 as first filed, whose arm now grades locked
stages by count; ground mUnlocks unread.

## CS-1375

### Acceptance

Phase 5, tier 2. A redesign is compared with what is built, dependency-ordered, and separates
needing more from replacing; an arm on a synthetic world with machines built reads both. Not a
lowering of the CS-1371 clause: a `BOOTSTRAP.md` pillar 4 residual.

### Filed 2026-11-03 (session 155) by the CS-1371 clause ruling

Filed by the rulings recorded under CS-1371, so that what CS-1371 did not deliver is a row.

## CS-1376

### Acceptance

Phase 5, tier 2. The plan panel gains accept, dismiss, snooze and pin controls through the state
route (`BOOTSTRAP.md` section 5.2), each with an arm on a stated-target card. Not a lowering.

### Filed 2026-11-03 (session 155) by the CS-1371 clause ruling

Filed by the rulings recorded under CS-1371, so that what CS-1371 did not deliver is a row.

## CS-1378

### Acceptance

Phase 5, tier 2. On a synthetic registry whose target's derived route leaves a byproduct that a
recipe off the route consumes, a stated balanced request reads a plan.redesign card whose tier 3
carries that consumer's machine count, where at CS-1371 it reads route-refused. A byproduct nothing
consumes still reads route-refused, with its own arm. The closing ledger record reads back the count
on one library save, the save unnamed; zero is not required. Measured: 7 of the 142 arm 2 targets on
one save, Plastic and Rubber among them. Not a lowering: CS-1371 arm 3 states the refusal.

### Filed 2026-11-03 (session 155) by the CS-1371 clause ruling

Filed by the rulings recorded under CS-1371, so that what CS-1371 did not deliver is a row.

## CS-1379

### Acceptance

On a synthetic registry whose item carries a display name, tier 1 and tier 2 of plan.adopt and plan.redesign name the target by that display name, the subject key and the card id
unchanged, and an item with no display name reads its ClassName. Tier 3 keeps ClassNames, each with its own arm. Measured on one docs build: Desc_SteelPlate_C reads as a Steel Beam to a
player, while the selector already labels by display name.

### Filed 2026-11-04 (session 155) by the CS-1371 close

Filed by the adjudicator that graded CS-1371, so that what the close did not deliver is a row.

### Filed 2026-11-04 (session 155) by the /done that stopped its candidate

Still OPEN. A built candidate sits unlanded on a local worktree branch: find it with `git log --all --grep=CS-1379`. Its
three commits cherry-picked clean in a dry run with the CS-1380 landing beneath them.

RULED, a distinct adjudicator, before code, for the close to carry, on "Tier 3 keeps ClassNames": Tier 3 keeps every
ClassName in its steps; Advice and Because quote tiers 1 and 2. Non-negotiable 8 holds because those two lines quote the
recommendation. Lost: a field on `clockspeed/advisor/cards.py::Card`. Reversed by: an arm finding a ClassName only in a
header. The clause says tier 2 of plan.redesign names the target, and at the first build it named none, so that sentence
now opens "This route to", on the merger's order and with no clause amendment.

WHY IT DID NOT LAND. A surface lens returned REFUTED, LOW, in two opposite directions, both on names the pinned docs do
not hold. The first build spliced a display name undelimited, so a mod's name could hold a clause, a comma that reads as a
second target, or 200000 characters. The repair reads a name holding a semicolon or a comma, or over 64 characters, by its
ClassName through the existing fallback step, 0 of 142 selectable targets falling back; and an item named `A, B` then
reads its ClassName, against the clause's "name the target by that display name". A residual on the same lens: a name
equal to a recipe key prints that key in tier 1 beside "name none of them", 0 pinned names equal to a key. NEXT: a ruling
between delimiting the name, for instance quoting it, and that fallback, with any clause change through an adjudicator;
then the lens re-run, a verifier, an adjudicator on the built item, and landing.

WHAT THE CANDIDATE HELD. A real-world lens on 8 unlock sets of the stack that also held CS-1382: card ids equal to the
parent's with 0 mismatches, Desc_SteelPlate_C reads Steel Beam with its ClassName kept in the steps, rule errors 0. On 19
hostile names the id held and an unprintable name fell back; the ledger holds no name and a dismissal survives a rename.
Not reached: a browser, a re-read on a save without CS-1382, the whole suite. Its printable test is a copy of the one in
`clockspeed/advisor/trace.py`, as `clockspeed/advisor/rules/fuel.py` keeps one.

## CS-1381

### Acceptance

In `clockspeed/solve/strategy.py::rank_plans`, plans tied on the asked direction's score break by the other two rung scores before registry order, the documented tie-break corrected in the
same commit; an arm on a synthetic fixture reddens where a dominated plan tops the ranking today. Measured by badge scores on one world: Desc_Motor_C asked by raw has a top dominated by
both other rung tops, 1 of 46 ranked targets; another world read 0 of 28. Out of the CS-1371 repair round because the badge is honest and the card true.

### Filed 2026-11-04 (session 155) by the CS-1371 close

Filed by the adjudicator that graded CS-1371, so that what the close did not deliver is a row.

## CS-1382

### Acceptance

A raw input is supplied only when the world holds the build recipe of a machine the docs say extracts it, read from data and never a hardcoded list, an item with no known extractor
flagged and never fatal. Unsupplied, plan.adopt reads no card and plan.redesign counts that machine as locked, so this route needs no unlock cannot read beside it. plan.adopt and
plan.redesign join the generated-worlds property test over generated unlock sets, asserting every stage with a machine and one machine for it are in requires. Measured at the CS-1371
close, unproven until this row's first step settles the join: 0 of 17 library unlock sets hold a recipe eating a raw item with no extractor held; a constructed set fires a plan.adopt card;
189 of 478 sampled plan.redesign rows run a raw item with no extractor held and their tier 2 is true but not exhaustive. A library world reaching that state moves this row to the head of
the queue.

### Filed 2026-11-04 (session 155) by the CS-1371 close

Filed by the adjudicator that graded CS-1371, so that what the close did not deliver is a row.

### Filed 2026-11-04 (session 155) by the /done that stopped its candidate

Still OPEN. A built candidate sits unlanded on a local worktree branch: find it with `git log --all --grep=CS-1382`.

THE JOIN IS SETTLED, FROM DATA. The shipped docs publish it: `mAllowedResources` under `mOnlyAllowCertainResources`,
else `mAllowedResourceForms` over the forms of the resource group's items. Every resource item on the pinned docs has a
modeled machine. The portable miner entry is no modeled building, so it supplies nothing. No adjudicator was needed for
the join, nothing is hardcoded and nothing is lifted. Any-of is ruled on the Resource Well pair: both build recipes sit
in one schematic, and pairing them in code would be a hardcoded list; file a line with a re-pin that splits them as its
trigger.

RULINGS, a distinct adjudicator, before code, for the close to carry:
- Reading, not amendment: literal is self-contradictory for plan.redesign. Over generated unlock sets, the oracle
  importing no join: plan.adopt, every stage with a machine and one held machine for it in requires; plan.redesign, the
  same for held stages, no locked stage's recipe key in requires, each consumed raw a held extractor key in requires or
  its machine on plan.redesign.locked_extractors; a locked route fires. Reversed by: the engine not gating requires.
- Held extractor keys join plan.redesign's requires. Reversed by: re-ruling the reading above.
- Search raw: the stated items with a held extractor plus any that is a target. Route raw: those with a known extractor.
  An item with neither reads plan.raw_unknown. Reversed by: a real-world refutation.
- An unsupplied raw byproduct refuses balanced where a supplied one passes, accepted as a pillar 1 matter; the wording
  beside it was not ruled and is the first finding below.
- THE ROUTE'S COUNT, REVERSED BY THAT CLAUSE. An unsupplied raw item counted (1, 0) was ruled, and a real-world lens
  refuted it: 7 early-world targets went route-refused under sinkable, InfeasibleChain with Recipe_Silica_C run backwards
  beside Recipe_AluminaSolution_C, and the charge is per leaf, so 6 of 8 changed routes asked for more locked recipes.
  The branch has removed it, so a route that runs now does not win a tie on raw supply; the clause does not ask that.
  That removal's re-read on a save, the same lens at the branch's tip: NOT REFUTED, early world, sinkable, nine targets,
  cards 9 of 9 with ids, routes and locked counts equal to the parent's, rule errors 0, the no-unlock sentence 0 of 9, the
  locked machine named on all 9. Other targets, policies and worlds were not re-run.

MUST BE REPAIRED BEFORE THIS LANDS:
- MEDIUM, tier 2 false. Resources Ore and Water, a held extractor for Ore alone, recipe Ore to A plus Water, recipe and
  machine held, balanced, target A: no-plan, routed, nothing trimmed, and the reason says the capped search did not find
  the route. Nothing was capped, and the parent ranks this. The clause's condition itself holds. The builder's fixture
  reads it 4 times in 1000 cases, and its oracle matches only the sentence's prefix.
- LOW. The docstring sentence that a world supplying none reads a no-plan is false beside a held zero-input recipe, which
  ranks. The sentence that an item the registry does not hold yields nothing is false for a restricted list naming a
  token with no descriptor, reachable only by a hand-built request.
- LOW. A mod display name may hold words: `this route needs no unlock` as a name reads beside a locked extractor,
  as CS-1379's section says. The branch repairs a non-printable machine or extractor path into plan.unchecked and
  plan.raw_unknown; its sentence "no known extractor" is loose there. A loop W to A plus W with no extractor held fires
  plan.adopt, as its docstring accepts.
- `docs/ARCHITECTURE.md` near line 81 needs the raw-supply join once this lands.

WHAT THE CANDIDATE HELD, on its first frozen commit. Correctness: 7600 requests against an independent oracle, 0
mismatches and 0 rule errors, two hash seeds identical, 39 plants with no survivor. The property test's oracle imports no
join, and it shares one registry and one docs shape with its fixture. Real world: 43 saves, 17 unlock sets, Mk1 16,
Mk2 4, water 10, oil 3, Mk3 and the Resource Well pair 0; a built extractor without its recipe on 0 of 40 and 0 of 31
saves; the set holding none is a true absence, adopt 0 on both commits; the rich world moved 0 of 123 targets; 4
constructed sets over 58 rows, 0 rule errors. Not reached: the rest of the unlock sets compared in full, Mk3 and the
Resource Well paths on a real save. The adjudicator's common-mode risk stands: a held build recipe is taken as supply,
with no node, power or built check.

STILL OWED AT THE CLOSE: an adjudicator on the built candidate, which /done stopped before it ran, and a verifier. On the
first frozen commit a verifier read 17604 passed, 14 skipped, 0 failed at 94 percent, killed at its budget, so its top
level census guards went unread there. Whole suite not run on the branch.
