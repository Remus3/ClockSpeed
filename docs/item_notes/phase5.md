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

## CS-1371

### Acceptance

CS-1372 lands first, because this item reads its route. A new panel module, one new file in
`PANEL_MODULES` and `ASSET_NAMES` with one registration and no fetch of its own, states a target, a
rate, a direction and a byproduct policy through one bench of labelled controls and one button, no
form element, each required and none prefilled, through new doors in
`clockspeed/surface/web/app.js`. The three routes of `clockspeed/surface/api/advice.py` take those
four, and `clockspeed/surface/providers.py::StoreAdviceSource` hands
`clockspeed/advisor/advise.py::advise_world` the `clockspeed/advisor/plans.py::PlanRequest` an
advisor function builds from them. `clockspeed/data/registry.py` publishes the docs'
FGResourceDescriptor group as a new fact and that function takes it as raw_items, so no surface
module chooses a raw item. That group absent or empty is flagged in the registry's warnings and
reads plan.status request-malformed, never a search over no raw items, because
`clockspeed/advisor/plans.py::_well_formed` then refuses an empty raw tuple;
`tests/advisor/test_plan_world.py::test_no_raw_items_at_all_is_request_malformed` pins the opposite
and is rewritten and renamed in the same change. An item a recipe consumes that is neither in the
group nor made by an automated recipe is never treated as raw. Each of the following has its own
arm.

(1) On a synthetic fixture world a stated target on `/api/advice` returns a plan.adopt card, the
same four parameters on `/api/advice/<id>/derivation` return its tier 3 carrying its
`clockspeed/solve/strategy.py::StrategyBadge`, and the same four on the state route record that
card; without them the derivation and state routes answer as they do at the parent commit.

(2) The selector is FREE, per `CLAUDE.md` section 7: a new function plan_targets in
`clockspeed/data/registry.py` returns every `RecipeIO.item_key` on the outputs of
`clockspeed/data/registry.py::automated_recipes` except the published group, whose members pillar 1
refuses as targets. Each is selectable whatever the world's progress, the list served as one new key
of `/api/registry` so the panel computes nothing, with no default target and no fixed pointer at the
next milestone. An output no automated recipe makes is not selectable, because no machine makes it;
`BACKLOG.md` records what that drops. When plan.status reads no-plan, and on no other status,
`clockspeed/advisor/plans.py::plan_offer` takes derived_route, the CS-1372 function in
`clockspeed/solve/bound.py`, over every usable automated recipe that carries a path, handed the held
recipes through a new keyword the trim does not pass, counting locked recipes on the tree first and
all recipes second, solves that route once with `clockspeed/solve/ratio.py::solve_for_targets` under
the stated policy, makes no second call of `clockspeed/solve/bound.py::optimize_within_bound` and no
rung search, and offers the plan to a new rule, plan.redesign, never to plan.adopt. An arm selects a
target whose every route runs at least three stages of recipes the fixture world has not unlocked
and reads a plan.redesign card rendered from the trace: action `Plan toward <target>`; tier 2 gives
the locked and held counts, says, when any is locked, that the locked recipes must unlock first on
this route and, when none is, that this route needs no unlock and the capped search did not find it,
says the stated direction did not choose this route and it was never compared with what is built,
and, when plan.unchecked holds any recipe, gives their count as plan.adopt's reason does; requires
holds only the held recipes the solve gives a machine, by the whole-path join on
`clockspeed/data/registry.py::Recipe`, and the arm asserts the world's held keys cover it; tier 3
carries every stage's machine count and reads the locked recipes by ClassName under an input of
their own, so no locked stage reads as buildable, and tier 1, tier 2 and requires name none of them;
it carries no StrategyBadge; its subject key has plan.adopt's plan: form, so its id moves with no
count, rate, policy or direction; every path a world reaches records an indeterminate step, firing
included, and settles nothing, and an arm shows a recorded card is not completed when the target
clears or moves. Separate arms: a hand-built offer with a locked key in requires yields
precondition-unmet and no card; a target ranked over unlocked recipes reaches no route solve and
gets no plan.redesign card; a route longer than `MAX_EXHAUSTIVE_CANDIDATES` fires, and wholly held
it reads the no-unlock wording; a longer held route beats a shorter locked one; a stage the solve
gives zero machines counts as neither held nor locked; a pathless recipe stays off the route and is
counted in tier 2. A fixture shows no tier, so this arm grades locked stages by count.

(3) A refused trace yields no card, so an advisor projection the surface transcribes carries what
was refused, under one key of the listing body present exactly when a target is stated: plan.status
always, with its closed-vocabulary reason on every status but ranked; plan.trimmed on every status
whose offer carries it; the plan.redesign status, one of not-reached, routed, no-route or
route-refused; on no-route, the items the target's backward closure over the arm 2 recipe set
reached that no member of it makes and the group lacks. One arm per plan.redesign status, and: a
no-plan arm reads its reason scoped to the kept set and plan.trimmed, a no-route arm reads the item
named, and a route-refused arm's same request under the other policy fires.

(4) With no target stated the advice body is byte-same, through
`clockspeed/surface/api/contract.py::encode`, as a golden captured at the parent commit over a
synthetic world at a fixed clock, and
`tests/advisor/test_plan_world.py::test_the_surface_passes_no_target` is rewritten in the same
change to pin that half beside the new stated-target arm.

(5) A target outside the arm 2 list, a rate at or below zero or malformed, a direction or policy
outside its closed vocabulary, or any of the four stated without the other three answers that
route's own 400 shape, echoes nothing and reaches no solve, which a spy shows. A rate, direction,
policy or partial set is refused before any provider is read, as `clockspeed/surface/api/solve.py`
does; the membership test runs after the no_save and no_game_install refusals and before the source,
so a missing save or install still answers its 503. The membership test reads the registry model and
no surface module chooses a value; this route refuses an unknown key on purpose, which
`clockspeed/surface/api/solve.py` leaves to the solve layer.

(6) Two requests with the same world, the same four parameters, a fixed clock and no ledger write
between them return byte-same bodies, and so do two processes under differing PYTHONHASHSEED.

(7) The panel renders the visible cards data.advice already holds, tiers 1 and 2, before any
request, then the stated request's cards and the (3) key after one, and a button on a card reads
tier 3 through the derivation route. A null data.advice or data.registry renders a named refusal and
no bench. `tests/surface/test_web_assets.py` and `tests/surface/test_panel_seam.py` grade the new
file as they grade every panel.

(8) The docstrings and comments of `clockspeed/advisor/plans.py`,
`clockspeed/advisor/rules/plan.py`, `clockspeed/advisor/advise.py` and
`clockspeed/surface/api/advice.py` saying no surface states a target, the listing accepts no
parameter, an empty raw tuple is a question, the family is one rule or no locked recipe reaches a
rule are corrected.
`tests/advisor/rules/test_plan.py::test_the_family_declares_the_build_inputs_ahead_of_its_own`
widens its pin of the family's rules.
`tests/advisor/test_plan_world.py::test_every_producer_locked_is_no_plan_no_adopt_card_and_fires_the_route` then
sits on a world firing a plan.redesign card and is renamed; a test renamed under this item has its
citation here moved in the same change. `tests/advisor/test_every_rule_fires.py` gains
plan.redesign, named in `tests/advisor/test_every_rule_fires.py::NEVER_SETTLES_ON_FIRING`, whose
silent fixture is a hand-built plan with no machine on any step, rejected and settling, which no
world reaches because a stated rate is above zero. The closing ledger record reads back on one
library save, the save unnamed, per byproduct policy, how many of the arm 2 list read a plan.adopt
card, a plan.redesign card and neither. A synthetic fixture cannot show that reach and the record
says so; zero neither is not required. The record names each filed row and each `BACKLOG.md` line
this ruling ordered as what this item did not deliver.

### Filed 2026-11-03 (session 155) by the CS-1351 close

**MOVED FROM `BACKLOG.md` BECAUSE IT IS PRODUCT WORK.** CS-1351 made plan.adopt run on every world and
fire on none: `clockspeed/surface/providers.py` passes no plan_request and the advice endpoint takes
no parameter. `BOOTSTRAP.md` D3 calls the target selector a first-class control. No open row covers
it: CS-1046 publishes the `/api/plan` and `/api/audit` bodies, CS-1254 renders a matrix for a target
it is handed, and neither states one.

**WHAT THE CS-1351 RECORD SETTLED, SO THIS ITEM DOES NOT RE-ARGUE IT.** The target source is a caller
keyword; the world's phase table, built output and the next milestone were each rejected as a source.
Its reversal clause, a selector shipping, is this item. Read `docs/LEDGER.md`, 2026-11-03, CS-1351.

**MEASURED, ONE SAVE, AND THE SAVE LIBRARY CAN CHANGE.** With a stated target, one adjudicator's probe
read 21 of 33 targets firing a card and 0 rule errors. Two lines in `BACKLOG.md` wait on this row being
taken: the unpriceable power rung and the score tie.

### Filed 2026-11-03 (session 155) by the CS-1371 clause ruling

**THE RULING THIS ITEM NEEDED BEFORE CODE IS TAKEN: A MARKED ROUTE, NEW RULE plan.redesign.** A distinct
adjudicator ruled the source, its criteria fixed before any candidate: the non-negotiables and
`BOOTSTRAP.md` section 5.4; `CLAUDE.md` section 7 on a real world and not only a fixture; truth; run-time
and build cost; reuse. On a no-plan, one derived route over every automated recipe with a path, counting
locked recipes first, solved once by pillar 1, offered to a new rule whose action is doable now and whose
requires holds held recipes alone. Rejected: pillar 4 alone, which prices a cost and never says what to
build, with mUnlocks unread, no implementer of its source and the hub tier None on every load; a hybrid
naming the schematic, whose second half is CS-1374. RUNNER-UP, a marked bound and rung search over the whole
automated list. Its best argument: it honours the stated direction, carries a badge, reuses the ranking and
reaches 7 balanced targets the route refuses. It lost because on the sinkable policy its reach is a strict
subset of the route's, its badge is a claim about an arbitrary 12 of 291, and it costs seconds on the GET.
Measured on prototypes, one docs build, two saves: 108 of 142 targets read a card on a 42-recipe save
(28 ranked, 80 routed) and 112 of 142 on a 116-recipe save, sinkable; 61 of 142 balanced. Reversed by a
closing read-back where the bound reaches more sinkable targets than the route, a recorded need for a
direction-graded locked plan, or the operator's word. THE ADJUDICATOR ADDED THIS CANDIDATE ITSELF AND
RECUSED, so a distinct adversary tried to refute it: NOT REFUTED on false plans, a wholly held route, the
direction, section 5.4, the ledger, balanced reach, unlock honesty or walk termination. It reproduced the
reach, and found the words this clause now carries. Its residuals stand: on 42 of 86 locked routes on one
save, must-unlock-first names a hard-drive recipe the target did not need, which CS-1374 carries; a free
byproduct loop can give a stage zero machines, shared with the ranked path.

**THE CLAUSE WAS AMENDED BEFORE CODE, EVERY CHANGE THROUGH AN ADJUDICATOR.** A distinct adversary tested the
first-filed text and REFUTED most arms as untestable or impossible: the derivation and state routes refused a
target, so the card could not be read; no slot on the wire; no named source for raw items; no page element
rendering advice. A second adjudicator, not the one that wrote this text, ruled the second read. RAISED: the
panel, the three routes, the raw set, the projection, the golden. LOWERED, each stated: a schematic is not on
the selector, ground build cost and a missing concrete source, CS-1373; several tiers grades by locked-stage
count, ground mUnlocks unread, CS-1374; any item the registry produces became machine-made outputs, ground no
machine makes the rest, `BACKLOG.md`.

## CS-1372

### Acceptance

`clockspeed/solve/bound.py::_trim_ranking` ranks by a new rule, TRIM_ROUTE_FIRST in
`clockspeed/solve/bound.py`, built on a new public function derived_route there. By exact integer
arithmetic over the usable candidates and the request's raw items, a raw item counts zero and any
other item counts the least, over its usable producers, of one plus the counts of that producer's
inputs, a tie going to the lower registry position; the count is that rule's least fixed point, so
an item no usable recipe reaches from raw items has no count and no chosen producer, and every
chosen producer's inputs count strictly below the item it was chosen for; walking those chosen
producers back from the targets in sorted order, stopping at raw items, gives the derived route. The
ranking is the route's members in breadth-first walk order, each recipe's inputs as listed, then the
rest of the targets' backward closure stopping at raw items, by walk depth then registry position,
then everything else by registry position. So a derived route within
`clockspeed/solve/optimize.py::MAX_EXHAUSTIVE_CANDIDATES` is wholly kept even inside a larger
closure, and a closure within the cap is wholly kept. The count is of recipes on a tree, so the
route is deterministic and no claim of the fewest distinct recipes. The closure does not follow
byproducts, so under the balanced policy a route whose byproduct nothing kept consumes reads
no-plan, scoped to the kept set and the stated policy. Each of the following has its own arm.

(1) On a synthetic registry with every member unlocked, a target's chain of at least four stages,
one item on it having two producers and only the second feasible, the closure above the cap and the
derived route within it, while both `clockspeed/solve/bound.py::TRIM_TARGET_PRODUCERS_FIRST` and a
keep by walk depth then registry position drop a route member past the cap:
`clockspeed/solve/bound.py::optimize_within_bound` returns a plan and
`clockspeed/advisor/plans.py::plan_offer` reads a ranked plan. That arm in
`tests/solve/test_bound.py` reddens on the shipped order, and the route is named by hand, never read
back from the ranking.

(2) `MAX_EXHAUSTIVE_CANDIDATES` is pinned at 12: the cap does not move.

(3) The order reads the request's targets, raw items and usable candidates and the registry, never
the objective, the byproduct policy, a solve, a clock or a float: a spy sees no solve in
`clockspeed/solve/bound.py::trim_record`, one request yields one ranking under every direction and
both policies, two targets in either mapping order rank alike, two processes under differing
PYTHONHASHSEED agree, and a recipe cycle ends and names no recipe twice.

(4) `clockspeed/solve/bound.py::TRIM_RULES` gains the new rule and keeps the shipped name, which no
path emits any more and a comment says so; `TrimStep.rule` on a returned record and
`BoundExhaustedError.rule` on a refusal both name the new rule.

(5) A chain of more than the cap's count of recipes, one producer per item, every member required,
still reads no-plan, its reason scoped to the kept set and plan.trimmed naming what the bound
dropped, each with its own arm.
`tests/advisor/test_plan_world.py::test_a_capped_no_plan_names_what_the_bound_dropped` is rebuilt on
that chain, because its two-recipe route now ranks, and keeps its control through
`clockspeed/solve/ratio.py::solve_for_targets`, because
`clockspeed/solve/optimize.py::optimize_plan` refuses a route over the cap.

(6) `tests/solve/test_bound.py::test_an_under_cap_request_is_not_recorded_as_trimmed`,
`::test_the_chosen_prefix_is_the_smallest_that_passes` and
`::test_the_ascent_visits_the_empty_prefix_first_on_every_request` pin the shipped order's first
prefix and are re-derived by hand in the same change, each still grading what it names.
`::test_a_cap_hit_records_the_cap_the_rule_and_a_conserving_partition`,
`::test_a_request_no_prefix_can_solve_refuses_and_names_the_cap_and_the_rule`,
`::test_a_refusal_over_the_cap_carries_what_the_bound_dropped` and
`::test_the_refusal_says_what_a_greedy_exhaustion_does_not_prove` pin the shipped name and are
re-pinned to the new rule.

(7) The nested-prefix proof, the first-tier argument and the cost bound in that module's docstring,
the docstrings of `_trim_ranking`, `trim_record` and `optimize_within_bound`, and
`clockspeed/advisor/plans.py` items 2 and 3 are re-read and corrected in the same commit and read
back by the closing adversary, so no docstring claim outlives the behaviour. No test grades prose.

(8) The no-plan count before and after, over every output of the save's unlocked automated recipes
that no one of them makes from raw items alone, on one library save, the save unnamed, under the raw
set and raw rule stated in the record, and the same count over the whole automated list, is recorded
in the closing ledger record. Zero is not required, and the record says a synthetic fixture cannot
show this.

### Filed 2026-11-03 (session 155) by the CS-1351 close

**MOVED FROM `BACKLOG.md` BECAUSE IT IS PRODUCT WORK.** The trim ranks direct producers of a requested
item first and everything else in registry order, so a producer of an intermediate can fall past the
cap, and `clockspeed/advisor/plans.py::plan_offer` then reads no-plan where an unlocked chain exists.
MEASURED by the CS-1351 run on one save: 11 of 12 no-plans, half the multi-stage targets. The no-plan
reason is scoped to the kept set, so it is loud and true, not cured. No open row covers it.

### Filed 2026-11-03 (session 155) by the CS-1371 clause ruling

**THE ORDER IS RULED: ROUTE FIRST, AND THE CLAUSE WAS AMENDED BEFORE CODE.** A distinct adjudicator ruled it,
its criteria fixed first: the clause and the nested-prefix proof stay true; targets cured on a world's unlocked
recipes and on the whole automated list; simplicity and run-time. Measured, sinkable, ranked: whole list 30
shipped, 51 closure by depth, 92 route first, of 142; 116-recipe save 22, 47, 57 of 79; 42-recipe save 18, 28,
28 of 33; neither other order ranked anything route first missed. RUNNER-UP, closure by depth then registry
position. Its best argument: simpler, equal on the 42-recipe save, fewer tests flipped. It lost because cure
outranks simplicity and the fixed point costs a millisecond. Rejected: route first with byproduct consumers
next, balanced 52 against 54. Reversed by a library world where the closure order ranks more, or the
operator's word. LOWERED, stated: the closure follows no byproduct, ground `clockspeed/solve/ratio.py` and that
measurement, and the player states the policy; a multi-producer closure with a route above the cap states no
outcome beyond the closed vocabulary, ground such routes solve through plan.redesign. A distinct adversary
REFUTED most of the first-filed sentences: chain undefined with several producers, and the targets and the
registry alone false at the first line of the trim. A second adjudicator ruled the second read.

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
Measured: whole-path join 291 of 291 automated recipes, 19 by more than one schematic.

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
