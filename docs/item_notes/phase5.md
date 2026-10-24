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

## CS-1240

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Key every registry and save join on the stable class identifier, never a display name; one case-and-punctuation fallback; then flag, skip and list.

### Acceptance

a fixture with one unknown class yields a flagged-and-skipped record with no exception and the panel lists it with a count and first-seen save; a display-name change in the fixture registry changes no output; AMENDED on the adjudicator route: any normalised fallback applies to ClassName-keyed lookups only, never to an asset-path join - `clockspeed/progress/milestones.py::purchase_state` keeps CS-1343's exact asset-path equality, no fallback is added in `clockspeed/progress/milestones.py`, and no path is reduced with `clockspeed/data/schematics.py::class_name_of_path` to feed one; `tests/progress/test_milestones.py::test_purchased_is_the_asset_path_join_not_the_trailing_token` and `::test_a_near_miss_of_an_asset_path_is_not_a_purchase_and_is_counted` stay green and unedited

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

## CS-1340

### Filed 2026-10-21 (session 150), split out of CS-1043 by its adjudicator

**THE HOLE.** A space-elevator phase cost is a fact the save carries, and nothing reads
it. `docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md` found
`mGamePhaseCosts` on `BP_GamePhaseManager_C` in a mature world and absent outright in a
low-progress one; its `PhaseCost` interiors carry `gamePhase` and `cost`, and whether a
`cost` is the phase's total or its remainder is unmeasured. `clockspeed/save/world.py`
publishes no phase cost and does not name the array in `UNLOCK_CARRIERS_UNREAD`. CS-1043
therefore ships `clockspeed/progress/phases.py` with an unmeasured `PhaseCostSource`, and
every phase publishes null.

**IT NEEDS THE GAME, AND READS THE SAVE READ-ONLY** - a work copy through
`clockspeed/save/workdir.py`, never the save directory (non-negotiable 1), and names and
counts only in every record (non-negotiable 12).

### Acceptance

whether each `PhaseCost` entry's `cost` in `mGamePhaseCosts` is the phase's total or its remainder is measured read-only on a work copy of the pinned development world and recorded in `docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md` with names and counts only; `mGamePhaseCosts` is named in `clockspeed/save/world.py::UNLOCK_CARRIERS_UNREAD` for as long as the reader does not publish it; `clockspeed/save/world.py` is then wired to publish it, with a synthetic arm under `tests/save/` asserting each decoded cost amount is an exact Fraction and that a world without the array publishes no table rather than an empty or zero one; and a `PhaseCostSource` built from it under the measured meaning replaces the unmeasured shipped source in `clockspeed/progress/phases.py`, so `phase_costs_available` reads True on a world that carries the array

## CS-1346

### Filed 2026-10-22 by the CS-1244 close

**THE BADGE REACHES NO CARD, AND THE SCOPE SAID IT WOULD.** CS-1244 shipped
`clockspeed/solve/strategy.py::StrategyBadge`, and `config/lane_scopes.json`'s
`advisor-ranking` description had credited `clockspeed/advisor/cards.py` with carrying it.
Measured on the code at that close: `clockspeed/advisor/cards.py::Card` is frozen with
exactly ONE field, `trace`, and one-parameter construction is load-bearing - the trace is
the only constructor parameter and tier text cannot be supplied; and
`clockspeed/advisor/advise.py` is built from audit models and unlock state, so NO PLAN
REACHES IT and a badge field on the card would have had no producer. Both files are
therefore UNCHANGED by CS-1244, and the scope clause was corrected rather than satisfied.

**WHAT IS ALREADY DONE, SO THIS ITEM DOES NOT REDO IT.**
`clockspeed/advisor/cards.py::render_value` renders a frozen dataclass field by field, so a
badge placed on a trace reaches the tier-3 derivation with no change to the renderer. What
is missing is the PRODUCER: a rule that reads a plan, which is what gives a trace a badge
to carry. Non-negotiable 8 binds the tier-3 half - the derivation is generated from the
trace, never hand-written - and that is why the clause below says so rather than leaving it
to the builder.

### Acceptance

a rule trace carries a `clockspeed/solve/strategy.py::StrategyBadge`, produced by a rule that reads a plan, and the card's tier-3 derivation renders that badge FROM the trace, generated and never hand-written; a synthetic fixture world whose rule reads a plan shows the badge in the tier-3 derivation and shows nothing of it in tier 1; and no constructor parameter is added to `clockspeed/advisor/cards.py::Card`, whose single `trace` field stays the only one

## CS-1347

### Filed 2026-10-22 by the CS-1244 close

**THE SHARED KEY BREAKS A TIE AND DOES NOT RANK A RESULT.** CS-1244 promoted the one
documented ranking key to `clockspeed/solve/optimize.py` as `ranking_key` and
`result_ranking_key`, and both backends now break a TIE with it
(`tests/solve/test_optimize.py::test_both_backends_break_a_tie_with_the_same_documented_key`).
A tie-break is not a ranking. `clockspeed/solve/backends/greedy.py::GreedyBackend.optimize`
documents its own return as "the first selection that solves the real request, in canonical
form", and its class docstring says the walk commits to each step and never backtracks, so
on a problem where a worse first step leads to a better factory it returns the worse
factory. It never re-ranks the canonical selections its walk actually reached through the
shared key, so nothing requires its result to be the lowest-ranking one it saw.

**THE SHIPPED FIXTURES DO NOT DISTINGUISH THE TWO BACKENDS**, which is why this was found
by reading rather than by a red arm:
`tests/solve/test_optimize.py::test_c5_the_two_backends_produce_structurally_identical_plans`
and `::test_c3_the_two_backends_agree_on_the_loop` both hold. CS-1244's close touched this
module with a COMMENT ONLY - a verifier parsed it with docstrings stripped and found the AST
byte-identical to HEAD's - so nothing about the walk changed and the finding is about
behaviour that predates it.

**WHETHER TO CORRECT THE WALK OR AMEND ITS GUARANTEE IS THIS ITEM'S TO SETTLE**, on the
adjudicator route, never by quietly reading the no-backtracking sentence as something else.
Re-ranking what the walk reached is not backtracking, so the two may both hold; the clause
below requires the choice to be written down either way.

### CORRECTION - recorded 2026-10-22 (session 150) by the CS-1244 re-close

**THE FILING ABOVE SAYS BOTH BACKENDS BREAK A TIE WITH THE SHARED KEY, AND GREEDY DOES NOT.**
Only `clockspeed/solve/backends/exhaustive.py`, through
`clockspeed/solve/optimize.py::result_ranking_key`, and the strategy ladder's
`clockspeed/solve/strategy.py::rank_plans` use the key. `clockspeed/solve/backends/greedy.py`
scores a relaxed probe plan, which has no canonical selection to read positions from, and
resolves a tie through registry-ordered pool iteration and a strict less-than - the same
registry ordering, reached by a different route, as its own comment states.
`tests/solve/test_optimize.py::test_both_backends_break_a_tie_with_the_same_documented_key`
grades both backends' outcome on the C8 twins, not which rule produced it. That greedy never
consults the key is this item's own subject. The filing stays as written and this block
corrects it; the same correction to the CS-1244 record is in `docs/LEDGER.md`.

### Acceptance

the result `clockspeed/solve/backends/greedy.py` returns is the lowest-ranking of the canonical selections its walk actually reached, by `clockspeed/solve/optimize.py::result_ranking_key`; a synthetic fixture in which the first selection that solves is not the lowest-ranking one reddens on the old behaviour and passes on the new, so the arm is not vacuous; and the heuristic's no-backtracking guarantee is restated or AMENDED explicitly in that module's docstring, with an amendment recorded in `docs/LEDGER.md` under this ID, never changed in silence

## CS-1348

### Filed 2026-10-21 (session 150), split out of CS-1343 on its close

**THE HOLE.** CS-1343 closed with its clause 3 amended on the adjudicator route: the phase model
publishes `delivered_available` False, derived from
`clockspeed/progress/phases.py::PhaseCostTable`'s delivered mapping, because no layer below
`clockspeed/progress/` publishes a delivered reading. Items already delivered into the space
elevator sit in its input inventory, nothing reads that inventory into the table, and so every
phase shows REQUIRED only.

**WAITS ON:** CS-1340, and a seam ruling on which layer below `clockspeed/progress/` publishes
the delivered reading. The inventory model sits in `clockspeed/audit/`, which
`clockspeed/progress/__init__.py` does not list below it.

**IT NEEDS A REAL SAVE, AND READS IT READ-ONLY** - a work copy through
`clockspeed/save/workdir.py`, never the save directory (non-negotiable 1), and names and counts
only in every record (non-negotiable 12).

### Acceptance

the elevator input inventory's carrier is measured read-only on a work copy and recorded in `docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md` with names and counts only; the layer the seam ruling names publishes it as `PhaseCostTable.delivered`, exact Fraction counts; a synthetic arm under `tests/progress/` shows `delivered_available` True from that producer, including a zero count, and False for a world with no reading, published as None, never zero.

## CS-1350

### Filed 2026-10-23 by the CS-1245 close

**THE DIVERGENCE IS DOCUMENTED RATHER THAN HIDDEN, WHICH IS WHY IT IS A ROW AND NOT A BUG
REPORT.** `clockspeed/solve/bound.py`'s ascent builds the nested prefixes S_1 to S_K and starts
at k = 1, so a request whose usable set is EMPTY has no prefix at all and is refused with
`BoundExhaustedError` having tried nothing. `clockspeed/solve/backends/exhaustive.py` enumerates
the empty subset deliberately - its docstring says the empty selection is a real selection and
is the answer to a target rate of zero - so `optimize_plan` ANSWERS exactly the request
`optimize_within_bound` refuses. The module docstring states the divergence under THE
CONSEQUENCE, STATED PLAINLY; this row is to remove it.

**IT IS NARROW AND IT IS LOUD.** The refusal is an exception, never a wrong plan, and it is
reachable only when the door leaves nothing usable. That is why it shipped rather than held the
CS-1245 close: no measured arm of CS-1245's acceptance touches it.

**DO NOT FIX IT BY SPECIAL-CASING AN EMPTY USABLE SET.** Starting the chain at k = 0 covers it
with the chain the module already proves things about, and S_0 is a subset of every other
prefix so the smallest-passing proof still holds. A special case is a second rule that the
cost-bound arithmetic and the nestedness proof in that docstring would both then have to
exempt.

### Acceptance

`clockspeed/solve/bound.py::optimize_within_bound` on a request whose usable candidate set is
empty and whose targets are all zero returns the same plan `clockspeed/solve/optimize.py::optimize_plan` returns for it, with `chosen_size` 0 and no trim record, and an arm in
`tests/solve/test_bound.py` reddens on the shipped refusal; the cost-bound arithmetic and the
k = 1 sentences in that module's docstring are corrected in the same commit, so no docstring
claim outlives the behaviour it described
