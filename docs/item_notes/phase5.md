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

## CS-1397

### Filed 2026-11-15 by the CS-1246 close

`clockspeed/advisor/advise.py::advise_and_record` is the stated write path for the
per-world ledger (CS-1268) and NOTHING in the product calls it: every served world goes
through `::advise_world` to the read-only `::advise`, and `clockspeed/surface/providers.py`
calls only that. So `completed`, `reopened` and CS-1246's deferral count are recorded in
tests alone, and the aging guard - which reads the counts on every read - never has a
count above zero to read in production. Whether a GET may write a store at all is the
decision this item has to make first; a read endpoint that mutates the ledger is a
different thing from a surface act that does.

### Acceptance

a served world records what the run implies exactly once per advice act, through a stated
act rather than a read, and a fixture proves a card shown below the top card on three
successive acts reaches the aging threshold in the store; no read-only path writes either
store

## CS-1398

### Filed 2026-11-15 by the CS-1246 close

`clockspeed/advisor/ranking.py::EFFORT_BY_RULE` declares effort per RULE ID, so
`power.headroom` is LARGE whether it asks for 3 MW or 300, and one rule's cheap and
expensive advice cannot be told apart. The declaration is honest at the rule level and the
census arm keeps it complete, but the magnitude the player actually faces lives in the
recommendation. A per-recommendation effort needs a quantity that carries its unit, which
is CS-1248's model, so this waits on it rather than adding a second unit convention.

### Acceptance

two cards from ONE rule whose actions differ in magnitude carry different effort, derived
from a declared quantity on the recommendation rather than from a rule-level table; the
census arm still reddens on an undeclared producer; the three-class scale is unchanged or
its widening carries an ADR

## CS-1243

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Coordinates come only from the save or extraction - never a wiki (section 7).

### Acceptance

a synthetic map fixture with three nodes and one gated region excludes the gated node until the unlock flag is set; distances are exact rationals or integers; claims rank by reachability band, then yield

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

## CS-1396

### Acceptance

Phase 5, tier 2. The plan panel offers the catalog's schematics as a second free selector beside
plan_targets: `/api/registry` serves `plan_schematics`, every ClassName the CS-1373
`SchematicSource` catalog holds, sorted, and the empty list when the source publishes none.
`clockspeed/surface/web/panel_advice.js` lists it in served order, starts empty, and a press with a
schematic chosen sends `schematic`, `direction` and `byproduct_policy` through data.actions, never a
rate; the panel computes nothing. Each reddens on its own arm first on a synthetic catalog: the
served list equals the catalog's sorted keys; no catalog serves the empty list and the panel names
that; a schematic and an item chosen together leave the press inert and name both fields; the sent
query carries no rate. Waits on CS-1373 and CS-1360; not concurrent with CS-1376.

### Filed 2026-11-14 (session 157) by the CS-1373 adjudication

Split out of CS-1373 so a finished core is not held behind the CS-1360 lane.

## CS-1374

### Acceptance

Phase 5, tier 2. `clockspeed/data/schematics.py` reads `mUnlocks`: each element whose keyset and
class token match the measured recipe-unlock shape publishes its recipe paths whole, in source
order, on `Schematic.unlocked_recipes`; an element of another measured shape is read past; an
element of an unknown shape carrying a recipe list, or any unreadable element, is flagged and sets
`Schematic.unlocks_complete` False, never a short list passing for the whole. A recipe joins a
schematic by whole-string equality of an unlocked path with `Recipe.asset_path`, never by trailing
token; an unlocked path joining no recipe is counted, never dropped. A recipe is a hard-drive
alternate when every schematic unlocking it carries the alternate `mType` token, named once as a
constant in that module; it is preferred when at least one schematic unlocking it carries a read
token that is not that one. `clockspeed/solve/bound.py::derived_route` takes the preferred set as a
membership-only frozenset beside `held`, never the catalog, and counts
`(locked, locked and not preferred, recipes)`, so preference breaks only a tie in locked count; None
keeps today's count. The plan.redesign card's tier 3, generated from the trace, names for each
locked recipe every schematic unlocking it with its tech tier - for a recipe the world holds with no
machine held, the schematics unlocking that machine's build recipe - in ascending tech tier, an
unknown tier last, then ClassName, and lists the locked recipes in ascending order of their lowest
naming tier, unknown last, then the route's registry order. A locked recipe no schematic unlocks
reads none, or unknown when any schematic's unlocks are incomplete. On a synthetic catalog and
registry each case reddens on its own arm first: two locked producers of a target tie on locked
count with the alternate first in registry order, and the route takes the preferred one; an
alternate with fewer locked recipes is still taken; a recipe two schematics unlock names both, lower
tier first; the locked list orders by ascending tier with unknown last; a stage held with its
machine locked names the machine's schematic; an unknown-shape element carrying recipes flags and
reads unknown; an unlocked path joining no recipe is counted. The closing ledger record reads back
on the installed catalog the joined-recipe count, how many recipes more than one schematic unlocks
and how many schematics carry the alternate token; no value is required. Waits on CS-1373's concrete
SchematicSource.

### Filed 2026-11-03 (session 155) by the CS-1371 clause ruling

**LOWERING** against "several tiers" in the CS-1371 clause 2 as first filed, whose arm now grades locked
stages by count; ground mUnlocks unread.

Ruled 2026-11-14 (session 157 adjudicator): name every unlocking schematic, lowest tier first; a hard-drive alternate is identified by its schematics' mType token (a named constant; the token confirmed at close); ascending orders the tier-3 unlock list only; solve/ receives a membership-only preferred frozenset, preference breaking only a locked-count tie. Rejected: picking one schematic; a Recipe_Alternate_ name prefix; ranking the route by tier; preference ahead of locked count.

## CS-1375

### Acceptance

Phase 5, tier 2. The plan.redesign card compares its route with what is built, from the audit
machines model `clockspeed/advisor/advise.py` already composes, handed to the plan offer beside the
unlock state; `solve/` sees no machine. A machine's capacity is its exact overclock, 1 when its
overclock was elided, and unknown when unread or when production_boost_tagged. For each route stage
with a nonzero machine count the card reads `more` with the exact shortfall, the stage's machine
count minus the built capacity on that recipe, when it is above zero, `enough` when it is not, and
`unmeasured` when any machine on that recipe has unknown capacity. A recipe off the route that built
machines run and that makes an output of a route stage reads `replace` with its machine count,
listed before every `more` and named as the expensive change. With no recipe tag on any machine the
whole comparison reads unmeasured; refused recipe tags, and machines naming no registry recipe, are
counted, never dropped. Stages are listed producers first: a stage precedes every stage consuming
one of its outputs, ties in the route's registry order, and a cycle's members in registry order
after their predecessors, the cycle named. Tier 3 carries the rows, generated from the trace; tier 2
states how many stages read more and how many recipes read replace. All arithmetic is exact
Fraction. On a synthetic registry and a hand-built machines model each case reddens on its own arm
first: a shortfall at clock 1; an overclocked machine closing it; an elided overclock as 1; an
unread overclock as unmeasured; a boosted machine as unmeasured; an off-route producer of a stage
output as replace; no recipe tag as unmeasured whole; producers-first order on a three-stage chain;
a two-stage loop named. Not a lowering of the CS-1371 clause: a `BOOTSTRAP.md` pillar 4 residual.

### Filed 2026-11-03 (session 155) by the CS-1371 clause ruling

Filed by the rulings recorded under CS-1371, so that what CS-1371 did not deliver is a row.

Ruled 2026-11-14 (session 157 adjudicator): made concrete, not re-scoped - built is WorldMachines by recipe at exact overclock; more is an exact shortfall, replace is an off-route producer of a route-stage output listed first; producers-first order. Rejected: machine-tier upgrades; target-first order.
