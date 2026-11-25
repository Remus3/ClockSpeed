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
CS-1061's own section (now in `docs/history_notes.md` under CS-1061, the row in `BACKLOG.md`), not repeated here.

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

## CS-1432

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-049. Class: product. Lane flag: false (not eligible: hub files app.js, server.py, __main__.py; a real-browser arm; an adjudicated doctrine edit). Planned minutes: 710 (8 parts (60 + 95 + 120 + 50 + 120 + 120 + 95 + 50)).
Depends on: CS-1251.2; CS-1252.4; U-074.3 (unfiled, by plan key); U-115.4 (staged, by plan key); CS-1204; U-107.3 (unfiled, by plan key); U-053.2 (unfiled, by plan key); U-119 (unfiled, by plan key).
Wave: W12, W13, W15, W16, W17 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-049.2 in W13: `tests/surface/` `test-watch` 1/2; U-049.4 in W13: `clockspeed/surface/__main__.py` 1/2, `tests/surface/` `test-watch` 2/2; U-049.5 in W15: `tests/surface/test_web_assets.py` 2/2; U-049.6 in W16: `clockspeed/surface/web/app.js` 2/2, `clockspeed/surface/web/index.html` 2/2, `tests/surface/test_web_assets.py` 2/2.
Write-list:
- U-049.1 (W12-G2-S1, 60 min): `tools/measurements.json`
- U-049.2 (W13-G1-S1, 95 min): `clockspeed/surface/` `watch`, `tests/surface/` `test-watch`
- U-049.3 (W13-G2-S1, 120 min): `clockspeed/surface/api/` `events`, `tests/surface/` `test-events`, `clockspeed/surface/server.py`, `tests/surface/test_server.py`
- U-049.4 (W13-G3-S1, 50 min): `clockspeed/surface/__main__.py`, `tests/surface/` `test-watch`
- U-049.5 (W15-G1-S1, 120 min): `clockspeed/surface/web/app.js`, `clockspeed/surface/web/index.html`, `clockspeed/surface/web/app.css`, `tests/surface/test_web_assets.py`, `tests/surface/` `test-freshness_strip`
- U-049.6 (W16-G1-S2, 120 min): `clockspeed/surface/web/app.js`, `clockspeed/surface/web/index.html`, `clockspeed/surface/web/app.css`, `clockspeed/surface/web/` `panel_play`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/surface/` `test-freshness_strip`, `tests/surface/` `test-panel_play`, `tests/surface/test_web_assets.py`
- U-049.7 (W17-G1-S2, 95 min): `tests/surface/test_web_assets.py`, `tests/surface/` `test-event_focus`, `clockspeed/surface/web/app.js`
- U-049.8 (W17-G2-S2, 50 min): `README.md`

### Acceptance

1. STAGE 0 (D97 line 2, D3) is recorded in `docs/LEDGER.md` before any product commit: an EventSource through the real stdlib TLS server into (i) the pinned shell's certificate-pinned session and (ii) a plain browser. GO needs all three in both: the on-connect data arrives; one change event arrives; while a stream is held another request answers inside `PROBE_TIMEOUT_MS` (2000, shell/lib/supervisor.js:310). NOT RUN (the shell half needs a visible window and runs only with the game closed) is neither GO nor NO-GO: the unit waits. NO-GO: record it, build no file of parts .2 to .8, and return the unit to an adjudicator with D3's fallback text as the brief.
2. `SaveWatcher` is stat-only and names no filesystem read of its own: over N injected ticks it calls `request_reload()` N times, calls `world()` zero times and opens no file; its wait is the one constant `WATCH_INTERVAL_S == 2.0`, passed to the injected `wait` (`test-the_watcher_ticks_request_reload_and_never_loads` in `tests/surface/` test_watch.py, spy provider plus a patched `open`).
3. Emission is keyed on the PAIR the provider publishes, (`generation()`, `reload_in_flight()`): after `request_reload()` each tick reads both and calls `on_change` exactly once when the pair differs from the last pair emitted, and never when it is equal. So a load seen in flight emits one settling event, its end emits one generation event, and a load that starts and ends between two ticks emits one. Three rewrites inside 200 ms followed by settle give one load and exactly one generation event (``test-an_in_flight_flip_emits_exactly_one_event``, ``test-one_generation_move_emits_exactly_one_event``, ``test-an_unchanged_pair_emits_nothing``, ``test-three_rewrites_inside_200_ms_give_one_load_and_one_generation_event``).
4. No public attribute and no `repr` of the watcher or the hub contains a path (``test-no_public_attribute_or_repr_names_a_path``, planted canary directory name).
5. A save directory absent at start then created moves the generation 0 to 1 and the next `/api/world` is 200 with no restart; deleting the save moves it and `/api/world` answers 503; removing the directory again answers 503 with no `Traceback` on stderr (``test-a_save_directory_created_after_start_is_served_without_a_restart``).
6. Under `--no-world` (clockspeed/surface/__main__.py line 76) the provider is `_NoWorld` (clockspeed/surface/__main__.py line 92), which has no `generation()`: no watcher is constructed, no watcher thread is started, and the hub is still built so the stream answers (clause 9). After shutdown no thread named `clockspeed-save-watcher` is alive inside `SHUTDOWN_TIMEOUT` (``test-no_world_starts_no_watcher_and_the_hub_still_answers``, ``test-the_watcher_stops_inside_the_shutdown_bound``).
7. `server.STREAM_ROUTES` is a third closed table holding exactly `/api/events`, matched before the routing table, and named by none of `health.ENDPOINT_TEMPLATES`, the built route table or `app.js` `ROUTES` (`test-the_stream_table_holds_exactly_one_route_and_no_published_table_names_it` in `tests/surface/` test_events.py). `git diff --stat <base> -- clockspeed/surface/api/routes.py clockspeed/surface/api/health.py tests/surface/test_health.py` prints nothing, where `<base>` is the tip U-049.3 starts from (its brief's stated base, D99 clause 9), never the planning HEAD: U-115.3 and CS-1252.2 edit those files first.
8. `GET /api/events` answers 200 `text/event-stream` with no save, under `--no-world` and while a load is held blocked; any other method is the static 405; a query string is never parsed and no typed byte is reflected (``test-the_stream_answers_200_event_stream_in_every_world_state``, ``test-any_other_method_is_the_static_405``, ``test-a_query_is_ignored_and_never_reflected``).
9. The stream writes one `data:` line on connect and one per change. When a world is served the data is byte-equal to the CS-1252 freshness member served on a body for the same state: an integer ordinal plus closed ASCII words, no path, world name, account id, digest or time (``test-the_event_data_is_the_served_freshness_member_and_nothing_else``, canary sweep). With no save and under `--no-world` no body carries a member (D5 G5), so the data is the same member shape with ordinal 0 and one closed word taken from CS-1252's frozen reason vocabulary (``test-the_data_with_no_save_and_with_no_world_is_ordinal_zero_and_one_closed_word``). This unit mints no word: if the landed vocabulary has none for these two states, stop and return to an adjudicator.
10. A comment line goes out every `KEEPALIVE_S == 15.0` on an injected clock, and `KEEPALIVE_S < server.CONNECTION_TIMEOUT` (30.0, clockspeed/surface/server.py line 358) is asserted from the two constants (``test-a_comment_line_goes_out_every_15_seconds``).
11. `STREAM_MAX == 4`: a fifth stream evicts the oldest; with four held another request still answers; `EventHub.close()` ends every stream inside `SHUTDOWN_TIMEOUT` (5.0, clockspeed/surface/server.py line 353) and `serve()` calls it first in its `finally` (``test-a_fifth_stream_evicts_the_oldest``, ``test-a_request_answers_while_four_streams_are_held``, ``test-shutdown_ends_every_stream_inside_the_bound``, ``test-serve_closes_the_hub_before_it_stops_the_listener``). If U-090 has landed, `STREAM_MAX <= MAX_CONNECTIONS - 8` is pinned here from the two constants.
12. STAGE A page: exactly one `new EventSource(` exists across all assets, in app.js, on the literal `/api/events`; `tests/surface/test_web_assets.py::test_the_page_repaints_on_a_button_and_never_on_a_timer` (:540) and `::test_the_timer_detector_fires_on_each_planted_timer` (:559) stay green with every assertion unedited (new arm ``test-exactly_one_asset_opens_exactly_one_event_stream``, with a planted second opener as the control).
13. The strip is one `role=status` element, `id="freshness-strip"`, present in index.html before any script runs and never removed (no reflow). It IS the fixed-slot one-line marker CS-1252.3 built (D5 G7), widened in place: part .5 reads the landed marker's id, keeps that one node and gives it this id (updating CS-1252.3's own arms in tests/surface/test_web_assets.py that name the old id); the page never holds two freshness indicators (`test-the_page_holds_exactly_one_freshness_element` in `tests/surface/` test-freshness_strip.py, with a planted second one as the control). For each of the six states a synthetic input makes its text START with exactly that word; no state text holds a path, world name or account id; no asset names `Date` or reads a clock (``test-each_state_makes_the_strip_start_with_its_word``, parametrized over LIVE, UPDATING, HELD, STALE, OFFLINE, NO SAVE; ``test-the_page_formats_no_time_and_reads_no_clock``).
14. A closed stream reads OFFLINE and keeps the last cards (container child count and ids unchanged, each card carrying a text mark); the next Refresh press re-subscribes exactly once (``test-offline_keeps_the_cards_and_marks_each``, ``test-a_refresh_press_after_a_closed_stream_resubscribes_once``).
15. STAGE A is the strip alone (D3: badge-only). With `QUIET_UPDATE` false `onSaveEvent` never calls `refresh()` and issues no fetch, whatever the ordinal and on every stream re-open: an equal ordinal leaves the strip as it is, a member carrying the `reading` word reads UPDATING, and a changed ordinal reads STALE until the next Refresh press paints it (``test-with_the_flag_false_no_event_and_no_reopen_issues_a_fetch``, a fetch count of zero and the Refresh button's attributes unchanged; ``test-a_changed_ordinal_reads_stale_until_refresh_is_pressed``). An event whose ordinal equals the painted ordinal issues no fetch in either flag state (``test-an_event_with_the_painted_ordinal_issues_no_fetch``).
16. STAGE B, built behind `QUIET_UPDATE` (false until clause 19): with no input event, a settling event (the member carries the `reading` word, clause 3) then a generation event make the strip read UPDATING then LIVE and repaint the cards once, with no reading state, the Refresh button's attributes unchanged, unchanged panels keeping node identity and a changed panel swapped in one operation from a subtree built detached; `syncScrollRegions()` (clockspeed/surface/web/app.js:371) runs after every quiet swap; a stream re-open after an error runs the quiet update exactly once (``test-a_settling_then_a_generation_event_reads_updating_then_live_and_repaints_once``, ``test-the_scroll_regions_are_synced_after_a_quiet_swap``, ``test-a_stream_reopen_updates_exactly_once``).
17. The quiet update is the ONLY path from `onSaveEvent` to a fetch, and it runs only when `repainting` (clockspeed/surface/web/app.js:1178) is false and no element inside a panel holds focus; otherwise only the strip changes (UPDATING) and one pending flag is consumed when the running refresh settles or at the next event - no timer, no focus listener (``test-a_focused_panel_control_defers_the_update_and_only_the_strip_changes``; static arm `test-the_event_handler_reaches_a_repaint_only_through_the_focus_guard` in `tests/surface/test_web_assets.py`, proved red on a mutant that drops the guard and on one that calls `refresh()` from the handler).
18. Hold is a `<button type="button" id="hold">` with `aria-pressed`; while pressed a generation event changes only the strip, to HELD; release repaints once (``test-hold_stops_automatic_repaints_and_release_repaints_once``).
19. STAGE B GATE: `test-focus_survives_an_event_driven_update_on_refresh_and_on_a_scroller` in `tests/surface/` test-event_focus.py holds focus on Refresh and on a scroller across an event-driven update in a real browser and finds `document.activeElement` unchanged AND a node of an unchanged panel, held from before the event, still connected. Driver: no CDP or DOM-dump driver exists in tools/ or tests/ (tools/dashboard_probe.py lines 85-92 only captures a screenshot), so the test's own forwarder serves the page with one test-only script appended; that script focuses the control, holds the panel node, asks the forwarder to publish one change, and after the update writes the two verdict words into one attribute; the browser is launched headless with a DOM dump and the test reads that attribute. Whether a headless dump gives real focus semantics is UNVERIFIED: an unreadable verdict is red, never green. Where no automation browser exists the test skips with the exact reason `no automation browser found`, asserted by name; a skip is NOT RUN, reported as a counted line in the part's report and in the LEDGER record, and never passes the gate. Only on a green run observed in the building session does part .7 set `QUIET_UPDATE = true`, edit docs/hud_doctrine.md section 2 (:63-64) and section 4 first bullet (:99-102) through an adjudicator, and re-scope the :540 arm's DOCSTRING only to `repaints on a button or a guarded server event, never on a timer`. NOT RUN or red: the flag stays false, the doctrine is untouched and the LEDGER record says badge-only shipped (true by clause 15).
20. Docs: docs/ARCHITECTURE.md section 2 names `GET /api/events` and section 1.1 the two new modules; README.md gains this product's own properties only (no comparative claim, no tool named) and `tests/test_readme_audit.py` stays green (212 lines at HEAD, `README_LINE_BUDGET` 220 at :49); the CS-1047 note in docs/item_notes/phase6.md says its refresh consumes this stream's stamp, so the tree carries one liveness token.

## CS-1420

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-020. Class: product. Lane flag: false (not eligible: D66: one serial builder owns clockspeed/advisor/plans.py and rules/plan.py; this unit is chain commit 1 of 5). Planned minutes: 660 (10 parts (65, 70, 80, 45, 95, 70, 60, 90, 45, 40)).
Depends on: CS-1256.4.
Wave: W29, W30, W31, W32, W33 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-020.2 in W29: `clockspeed/solve/` `staging` 1/2, `tests/solve/` `test-staging` 1/2; U-020.3 in W29: `clockspeed/solve/` `staging` 2/2, `tests/solve/` `test-staging` 2/2; U-020.5 in W30: `clockspeed/advisor/rules/plan.py` 1/2, `tests/advisor/rules/test_plan.py` 1/2, `tests/advisor/test_plan_redesign.py` 1/2, `tests/advisor/test_plan_world.py` 1/2; U-020.6 in W30: `clockspeed/advisor/rules/plan.py` 2/2, `tests/advisor/rules/test_plan.py` 2/2, `tests/advisor/test_plan_redesign.py` 2/2, `tests/advisor/test_plan_world.py` 2/2; U-020.8 in W32: `clockspeed/surface/web/panel_advice.js` 2/3, `tests/surface/test_panel_advice.py` 2/3, `tests/surface/test_panel_advice_ui157.py` 2/2; U-020.9 in W32: `tests/surface/audit_harness.py` 2/2.
Write-list:
- U-020.1 (W29-G1-S1, 65 min): `clockspeed/data/registry.py`, `tests/data/test_registry.py`, `tests/surface/test_registry.py`
- U-020.2 (W29-G2-S1, 70 min): `clockspeed/solve/` `staging`, `tests/solve/` `test-staging`, `tests/solve/test_phase3_gate.py`
- U-020.3 (W29-G3-S1, 80 min): `clockspeed/solve/` `staging`, `tests/solve/` `test-staging`
- U-020.4 (W30-G1-S1, 45 min): `clockspeed/advisor/trace.py`, `tests/advisor/test_trace.py`
- U-020.5 (W30-G2-S2, 95 min): `clockspeed/advisor/rules/plan.py`, `tests/advisor/rules/test_plan.py`, `clockspeed/advisor/plans.py`, `tests/advisor/test_plan_redesign.py`, `tests/advisor/test_plan_world.py`, `tests/solve/test_plan_edges.py`, `tests/advisor/test_every_rule_fires.py`, `tests/surface/test_flow_view.py`
- U-020.6 (W30-G3-S2, 70 min): `clockspeed/advisor/rules/plan.py`, `tests/advisor/rules/test_plan.py`, `tests/advisor/test_plan_redesign.py`, `tests/advisor/test_plan_world.py`, `tests/surface/test_advice_source.py`
- U-020.7 (W31-G2-S2, 60 min): `clockspeed/surface/api/flow_view.py`, `tests/surface/test_flow_view.py`
- U-020.8 (W32-G2-S2, 90 min): `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/surface/test_panel_advice_ui157.py`
- U-020.9 (W32-G3-S1, 45 min): `tests/surface/audit_harness.py`, `tests/surface/test_advice_golden.py`
- U-020.10 (W33-G1-S2, 40 min): `tests/test_architecture_attributions.py`

### Acceptance

1. `Building.minimum_clock: Fraction | None = None` is appended LAST on `Building` and filled by `_optional_fraction(entry, KEY_MIN_POTENTIAL, key, log)` with `KEY_MIN_POTENTIAL: Final = "mMinPotential"` (in `__all__`). A synthetic entry carrying `"0.050000"` reads `Fraction(1, 20)`; an absent key reads None with no warning; an unparsable value reads None and is flagged exactly as `mMaxPotential` is. No literal minimum exists anywhere in `clockspeed/` (grep for `Fraction(1, 100)` in `clockspeed/solve/` staging.py returns nothing). The field is withheld from the wire on the record: `tests/surface/test_registry.py` names `"minimum_clock"` in `WITHHELD_FIELDS["Building"]` with a comment in the CS-1281 style and `FRACTION_BEARING_WITHHELD` moves from 7 to 8 (`tests/surface/test_registry.py` lines 979-1010), or `test_every_upstream_field_is_either_published_or_withheld_on_the_record` reddens.
2. `clockspeed.solve.staging.stage_plan(registry, plan) -> StagedPlan` returns one `Stage` per step with `machines != 0`, in `plan.steps` order; a zero step is omitted; a negative `machines` raises ValueError. `StagedPlan` = `stages: tuple[Stage, ...]` and nothing else. `Stage` = `building_key: str | None, recipe_key: str, machines: Fraction, whole: int, forms: tuple[StageForm, ...], withheld: str`. `whole` is `-((-machines.numerator) // machines.denominator)`. All four types are `@dataclass(frozen=True, slots=True)`.
3. `forms[0]` is always `StageForm(kind="whole", groups=(StageGroup(count=whole, clock=REFERENCE_CLOCK, ...),), surplus=whole - machines, megawatts=...)`. `megawatts` is `whole * draw.megawatts` when `draw_at_clock(building, REFERENCE_CLOCK).outcome` is the exact outcome, else None. `StageGroup` = `count: int, clock: Fraction, rate_item: str | None, rate: Fraction | None, draw: ClockedDraw | None`; `rate` is `per_minute(outputs[0].amount, duration) * clock` for the recipe's FIRST declared output and `rate_item` is that item key (a two-output fixture pins it). Both are None when the recipe declares no output or a zero duration: `per_minute` raises `UndefinedRateError` there (`clockspeed/solve/exact.py` line 559) and is not called, and `stage_plan` never raises for either case.
4. Fixture building with `minimum_clock=Fraction(1, 20)`, `clockable=True`: machines 10/3 gives whole 4 and exactly three forms in this order: `whole` (4 at 1, surplus 2/3), `uniform` (4 at 5/6), `remainder` (3 at 1 then 1 at 1/3), `withheld == ""`. Machines 3001/1000 gives `whole` and `uniform` (4 at 3001/4000) and NO `remainder` (1/1000 is below 1/20), `withheld == WITHHELD_REMAINDER_BELOW_MINIMUM`. Machines exactly 3 gives `(whole,)` only and `withheld == ""`. Machines 1/3 gives `whole` and `uniform` (1 at 1/3) and no `remainder` (it would be the uniform form). Machines 1/100 gives `(whole,)` and `withheld == WITHHELD_BELOW_MINIMUM`.
5. Negative cases, each `(whole,)` only: `minimum_clock is None` gives `WITHHELD_NO_MINIMUM`; `clockable is not True` gives `WITHHELD_NOT_CLOCKABLE`; a clock that `clamp_to_unsharded_base(building, clock).clamped` reports True is never emitted (fixture base 1/2 with machines 10/3 gives `WITHHELD_ABOVE_BASE`); a recipe naming no building, more than one, or one absent from `registry.buildings` gives `building_key=None`, `megawatts=None`, `WITHHELD_NO_BUILDING`, and never raises. `withheld` is the FIRST reason that applies in this order: no building, not clockable, no minimum, above base, below minimum, remainder below minimum. The `whole` form is never clamped or withheld (D66 fixes it at the reference clock). Underclock forms have `surplus == 0`. The reason strings are fixed ASCII: WITHHELD_NO_BUILDING = "no single modelled building runs this recipe"; WITHHELD_NOT_CLOCKABLE = "this building has no clock setting"; WITHHELD_NO_MINIMUM = "the shipped data states no minimum clock for this building"; WITHHELD_ABOVE_BASE = "the clock would exceed the unsharded base of this building"; WITHHELD_BELOW_MINIMUM = "the clock would fall below the shipped minimum clock"; WITHHELD_REMAINDER_BELOW_MINIMUM = "the remainder machine would fall below the shipped minimum clock".
6. Away from the reference clock `StageGroup.draw` is the object `draw_at_clock(building, clock)` returned, unchanged (coefficient plus `DeferredPowerTerm`), and `StageForm.megawatts` is None. `audit_exact(stage_plan(...))` passes; a test that plants a float in a stage sees `InexactValueError`.
7. `git diff --stat <base> -- clockspeed/solve/exact.py tests/solve/test_display_rounding.py` prints nothing: no ceiling-at-places primitive and no second rounding mode (D66). `tests/solve/test_ceiling_fence.py` stays green (staging.py never reads `unsharded_clock_base`).
8. `tests/solve/test_phase3_gate.py`: `SOLVE_SOURCES` gains `"staging.py"` and `SOLVE_TEST_SOURCES` gains `"test_staging.py"`, each in sorted position, in the SAME commit as the two new files; the whole module is green.
9. `trace.PLAN_TYPES` gains `ClockedDraw` and `DeferredPowerTerm`; `RuleContext.read` admits a `StagedPlan`; one holding a float, or a `ClockedDraw` carrying an undeclared attribute, is refused.
10. `plan_inputs` takes a REQUIRED keyword `stages: StagedPlan` offered as `IN_STAGES = "plan.stages"` from source `"solve.staging.stage_plan"`. `IN_STAGES` is appended to `PLAN_INPUTS` AFTER `IN_CARRY` (`clockspeed/advisor/rules/plan.py` lines 245-257), so the two last-input pins move to it (`tests/advisor/rules/test_plan.py` line 1015, `tests/surface/test_flow_view.py` line 859) and the hand-built adopt world in `tests/advisor/test_every_rule_fires.py` lines 330-350 gains a `plan.IN_STAGES` value matching its one step. The call sits in the `else` branch outside every handler (`clockspeed/advisor/plans.py` line 1528), so it must not raise for a plan the solver returned. `plans.py` passes `stage_plan(registry, top.plan)` with its stages re-ordered by `_producers_first`. `plan.adopt` raises ValueError (a rule-error step, no card) when the stages' `(recipe_key, machines)` pairs are not exactly the plan's nonzero steps, when a `whole` is not the ceiling, or when `forms[0].kind != "whole"`. Tier 3 gains `Read plan.stages = StagedPlan(...) from solve.staging.stage_plan` after the `plan.carry` read and `Computed plan whole machines = <n>.00` directly after `Computed plan machine equivalents` (which stays). Two rule-level arms pin the card: a fixture building with `minimum_clock=Fraction(1, 20)` and a 10/3-machine step gives a tier 3 containing `render_value(Fraction(5, 6))` (expected text `0.83 (exactly 5/6)`) and the rendered per-machine `rate` of that group; the standing fixture (no minimum clock) gives a tier 3 containing the WITHHELD_NO_MINIMUM text. The render is the generic frozen-dataclass path (`clockspeed/advisor/cards.py` line 161), unchanged.
11. Tier 2 becomes exactly `f"It makes {rates} with {n} machine(s) in {k} stage(s)"` followed by the unchanged trim, unchecked, raw-unknown and caveat clauses in today's order; `n` is the sum of `whole`, `k` the stage count. The `tests/advisor/rules/test_plan.py` fixture (3 and 4/3 machines) reads `with 5 machine(s) in 2 stage(s)`. No tier-2 string in `tests/` contains `machine equivalents` afterwards. `PLAN_TIER2_BUDGET: Final` is declared once in `clockspeed/advisor/rules/plan.py`; one arm renders the reason for a PINNED fixture - exactly one target at rate `Fraction(20)` whose label is `display_names.MAX_NAME_LENGTH` characters long, 99 trimmed recipes, 99 unchecked, 99 raw-unknown, and the build caveat present - and asserts `len(reason) <= PLAN_TIER2_BUDGET` and `PLAN_TIER2_BUDGET - len(reason) < 10` (the value is that fixture's length rounded up to the next ten). The constant pins that fixture only and is no runtime cap: the target count and the three counts are unbounded (`clockspeed/advisor/rules/plan.py` line 1194), and the caps are U-079's.
12. `flow_view.view_of` adds `"stages"`: a list, in the recorded order, of `{"building", "recipe", "machines", "whole", "surplus", "megawatts"}` built from `forms[0]` only; numbers go through the same contract helper `nodes[].machines` uses, `whole` is an int, a None stays null; the key is null when the trace records no `plan.stages` read. `view_of` holds no arithmetic of its own. One arm binds the spelling as `tests/surface/test_flow_view.py` line 854 does for carry: `flow_view.STAGES_SUBJECT == plan_rules.IN_STAGES == "plan.stages"`.
13. The page renders `stages` inside the existing derivation press as one first-stage line (`Stage 1 of <k>: build <whole> x <building> running <recipe>`) followed by an `ol` with one `li` per stage; it creates no checkbox, shows no underclock form, divides nothing, and uses no innerHTML. The stage block is its own element placed after the derivation `pre` and before the flow label, shown whenever the derivation is shown and independent of `flowLines` (which is null for a flow with no edges, `clockspeed/surface/web/panel_advice.js:837-846`): the existing flow label, `pre` and legend keep their order and their hidden rule. A null flow, or a null or empty `stages`, leaves one sentinel line of class `note` (the existing dim line class, `clockspeed/surface/web/panel_advice.js:793`; `app.css` has no line-level dim class and is not edited), not a missing element.
14. The same registry and plan give a byte-identical `StagedPlan` render and flow body on two runs.
15. `python tools/provenance_stamp.py check` exits 0 with rows for the two new files, `tests/test_provenance_manifest.py` is green (D99 point 9), and `tests/test_architecture_attributions.py` is green with the pillar 2 sibling note for `clockspeed/solve/` staging.py. Close: clauses 1 to 14 are cited by test name in `docs/LEDGER.md`, the `ROADMAP.md` line and the leaf section are gone, and `python tools/drift_guard.py` exits 0.

## CS-1421

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-023. Class: product. Lane flag: false (not eligible: hub files clockspeed/advisor/plans.py and clockspeed/advisor/rules/plan.py; one serial owner, D66). Planned minutes: 120 (1 part).
Depends on: CS-1254.7.
Wave: W37, group 1, slice W37-G1-S1.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-023 in W37: `clockspeed/advisor/plans.py` 1/2, `clockspeed/advisor/rules/plan.py` 1/2, `tests/advisor/rules/test_plan.py` 1/2, `tests/solve/test_plan_edges.py` 1/2.
Write-list:
- U-023 (W37-G1-S1, 120 min): `clockspeed/advisor/plans.py`, `clockspeed/advisor/rules/plan.py`, `clockspeed/surface/api/flow_view.py`, `clockspeed/surface/web/panel_advice.js`, `tests/advisor/test_plan_world.py`, `tests/advisor/rules/test_plan.py`, `tests/surface/test_flow_view.py`, `tests/surface/test_panel_advice.py`, `tests/surface/test_advice_golden.py`, `tests/solve/test_plan_edges.py`, `tests/surface/golden/advice_no_target.json`

### Acceptance

1. `_ranked_top` (clockspeed/advisor/plans.py line 713) returns `(ranked, references, backend)`: the whole `rank_plans` tuple, the rung-name to optimum mapping it already builds at :737, and the backend name. `_offer` (:1463) uses `ranked[0]` as the top. Test: `test-ranked_top_returns_the_whole_ranking_and_its_references` in `tests/advisor/test_plan_world.py`.
2. The offer carries `plan.alternatives`: a tuple of exactly 3 `AlternativeRow`, in `STRATEGY_LADDER` order (within-raw, within-buildings, within-power; clockspeed/solve/strategy.py line 417). NOT the order of `OBJECTIVES`. Test: `test-alternatives_are_three_rows_in_ladder_order` in `tests/advisor/rules/test_plan.py`.
3. Row readings are a closed vocabulary `ALT_READINGS = ("plan", "equals", "unpriced")`. "plan": the rung's optimum, with `machines`, `raw`, `power` and `power_priced` read ONLY from that plan's `RankedPlan.key` (clockspeed/solve/strategy.py line 386): `key[0]` is the asked direction's score, `key[1]` holds the unweighted rungs in ladder order as `(flag, score)`; flag 1 gives `power_priced False` and `power None`, never 0. "equals": the optimum equals the plan of an EARLIER rung in ladder order; `equals` names that rung and every figure is None. "unpriced": `references[rung]` is None (the power search refused under another asked direction, clockspeed/advisor/plans.py lines 691-694); every figure is None. Tests: `test-a_rung_equal_to_an_earlier_one_is_a_sentinel_row_naming_it` in `tests/advisor/rules/test_plan.py`, `test-an_unpriced_rung_keeps_its_row_and_carries_no_zero`, `test-row_figures_equal_the_ranked_key_entries`.
4. Exactly one row has `top True`: the earliest rung whose optimum is `ranked[0].plan`. `only_here` lists the row plan's step recipe keys absent from the top plan (row plan step order); `only_top` lists the top plan's keys the row lacks (top plan step order); both empty on the top row. Test: `test-exactly_one_row_is_the_top_plan_and_differences_are_step_ordered`.
5. `plan.adopt` declares and reads `plan.alternatives`; a value that is not a 3-tuple of `AlternativeRow` in ladder order, a reading outside the vocabulary, an "equals" naming a later or non-"plan" rung, or zero or two top rows raises (a rule error, as `_check_carry` does at clockspeed/advisor/rules/plan.py line 939). For each non-top "plan" row the rule records `ctx.compute` lines for machines, raw and (only when priced) draw, so tier 3 lists them. Tier 1, tier 2, the card id and `requires` do not change. Tests: `test-a_malformed_alternatives_input_is_a_rule_error` (parametrized over the five faults), `test-alternatives_move_no_headline_reason_or_card_id`.
6. No extra solve: `test-the_compare_rows_cost_no_extra_optimize_plan_call` in `tests/advisor/test_plan_world.py` wraps `clockspeed.advisor.plans.optimize_plan` in a counter and asserts the count for one `plan_offer` is `len(STRATEGY_LADDER)` both with the rows read and without; `rank_plans` is called once.
7. `flow_view.view_of` (clockspeed/surface/api/flow_view.py line 296) serves `"alternatives"`: always a list of exactly 3 dicts in ladder order with keys `rung, reading, equals, top, machines, raw, power, power_priced, only_here, only_top`; numbers are `contract.rational` objects or null. A trace with a plan but no `plan.alternatives` step serves 3 rows with reading "unrecorded" and nulls, never a short or missing list. Tests: `test-alternatives_are_always_three_rows_in_ladder_order` in `tests/surface/test_flow_view.py`, `test-a_trace_without_the_input_serves_three_unrecorded_rows`, `test-the_alternatives_subject_is_the_rules_input_name`.
8. The page shows the rows only under the existing derivation press (clockspeed/surface/web/panel_advice.js:784-848): three `p` elements `advice-compare-<position>-0..2` under a label `advice-compare-label-<position>`, created with the card, hidden until a body carries `flow.alternatives`, never added or removed afterwards. Sentinel rows carry the existing `note` class and read `<rung>: same plan as <equals>`, `<rung>: no exact draw to compare` or `<rung>: not recorded`. The page does no arithmetic. Tests: `test-compare_rows_are_three_fixed_nodes_hidden_until_the_derivation_is_read` in `tests/surface/test_panel_advice.py`, `test-a_sentinel_row_is_dim_text_and_never_a_missing_node`, `test-the_card_shows_no_compare_row_before_the_press`.
9. Negative: on every non-ranked status (`no-target`, `no-plan`, `power-not-comparable`, ...) no `plan.alternatives` input is offered and the rule does not read it. Test: `test-a_refused_offer_carries_no_alternatives` in `tests/advisor/test_plan_world.py`.
10. `.venv/Scripts/python.exe -m pytest tests/advisor tests/solve/test_plan_edges.py tests/surface/test_flow_view.py tests/surface/test_panel_advice.py tests/surface/test_advice_golden.py -q` exits 0 (read PYTEST_EXIT from a log, never through a pipe).

## CS-1422

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-024. Class: product. Lane flag: false (not eligible: hub files clockspeed/advisor/plans.py and clockspeed/advisor/rules/plan.py; one serial owner, D66). Planned minutes: 300 (3 parts (60 + 120 + 120)).
Depends on: CS-1064.2; CS-1421 (U-023).
Wave: W35, W37, W38 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-024.2 in W37: `clockspeed/advisor/plans.py` 2/2, `clockspeed/advisor/rules/plan.py` 2/2, `tests/advisor/rules/test_plan.py` 2/2, `tests/solve/test_plan_edges.py` 2/2.
Write-list:
- U-024.1 (W35-G2-S2, 60 min): `clockspeed/solve/optimize.py`, `tests/solve/test_optimize.py`
- U-024.2 (W37-G2-S1, 120 min): `clockspeed/advisor/plans.py`, `clockspeed/advisor/rules/plan.py`, `tests/advisor/rules/test_plan.py`, `tests/solve/test_plan_edges.py`
- U-024.3 (W38-G1-S1, 120 min): `tests/surface/test_advice_golden.py`, `tests/advisor/` `test-plan_power`, `tests/advisor/test_plan_world.py`, `tests/surface/golden/advice_no_target.json`

### Acceptance

1. `clockspeed.solve.optimize.plan_draw(registry, plan) -> PlanDraw` is public and exported. `PlanDraw(lower, upper, unpriced, bracketed, clamped, bound_proven)`: per step, an exact draw (the pricing `_recipe_draw` does at clockspeed/solve/optimize.py line 572) adds `machines * megawatts` to both bounds; else a single modeled building whose `bounded_draw(building, recipe).modeled` is True (clockspeed/solve/power.py line 812, ADR 0021) adds `machines * minimum` to `lower` and `machines * maximum` to `upper` and lists the recipe key in `bracketed`; else the recipe key goes to `unpriced` and adds nothing. Tests: `test-plan_draw_equals_the_power_score_when_every_recipe_is_exact` in `tests/solve/test_optimize.py` (`lower == upper == score_plan(...)` under the power objective), `test-a_variable_power_step_contributes_its_two_bounds`, `test-an_unpriceable_step_is_listed_and_adds_nothing`, `test-plan_draw_passes_the_exact_audit`.
2. `bound_proven` is True only when `unpriced` and `bracketed` are empty and every used building has `power_exponent` (clockspeed/data/registry.py line 831) present and at least 1. `clamped` lists, in step order, the buildings `clamp_to_unsharded_base(building, REFERENCE_CLOCK)` clamped. Tests: `test-bound_proven_needs_an_exponent_of_at_least_one_on_every_building` (parametrized: 1, above 1, below 1, None), `test-a_building_priced_below_the_reference_clock_is_named`.
3. The offer carries `plan.power_mw` (a `PlanDraw`, source `solve.optimize.plan_draw`) on the ranked status only, through a required `power=` keyword on `plan_inputs`. Test: `test-a_ranked_offer_carries_the_plans_draw_and_a_refused_one_does_not` in `tests/advisor/test_plan_world.py`.
4. `plan.adopt` reads it. With `unpriced` empty it records the figure by `ctx.compute`: one line labelled "plan draw in MW, fractional machines at the reference clock" when `lower == upper`, else two lines ending "low end of the variable-power bracket" and "high end of the variable-power bracket". Where `clamped` is non-empty the label says "at each building's own clock base" instead of "at the reference clock". The words "upper bound" appear only when `bound_proven`, and only as "an upper bound for the uniform-clock form". Tests: `test-the_draw_is_recorded_as_one_figure_or_as_a_bracket` in `tests/advisor/rules/test_plan.py`, `test-upper_bound_is_said_only_where_it_is_proven`, `test-a_clamped_building_changes_the_label`.
5. With `unpriced` non-empty the rule records no draw figure and one `ctx.indeterminate("state the plan's draw", ...)` naming the count; tier 3 names the recipes; no 0 is ever computed and the slot is never absent. Test: `test-an_unpriced_recipe_reads_indeterminate_never_zero`.
6. Grid verdict, closed vocabulary `POWER_VERDICTS = ("within", "exceeds", "may-exceed", "indeterminate")`. The rule compares only when the plan draw is priced AND `power.clocked_draw.complete` is True AND `power.production_available` is True AND `power.production_complete` is True (the refusal order of `_evaluate_headroom`, clockspeed/advisor/rules/power.py lines 234-244); otherwise it records `ctx.indeterminate("compare the plan's draw with the grid", <which input is a floor or absent>)` and reads no generation figure. Test: `test-each_incomplete_input_reads_indeterminate_never_spare` in `tests/advisor/` test-plan_power.py (parametrized over the four refusals).
7. When it compares: `excess_low = plan.lower + power.clocked_draw.lower_mw - power.generation_mw` and `excess_high = plan.upper + power.clocked_draw.upper_mw - power.generation_mw`, both recorded by `ctx.compute`. `excess_high <= 0` is "within"; `excess_low > 0` is "exceeds"; otherwise "may-exceed". Tests: `test-the_verdict_matrix_on_exact_figures` (within at exactly 0, exceeds by 1/3 MW), `test-a_bracket_straddling_generation_reads_may_exceed`.
8. Tier 2 gains a power clause ONLY on "exceeds": `; it exceeds grid headroom by <y> MW`, or `by <a> to <b> MW` when `excess_low != excess_high`, rendered through `render_value`. It takes the one shared slot ahead of the built clause; "within", "may-exceed", "indeterminate" and the figure itself are tier 3 only. Tests: `test-tier_two_states_power_only_when_the_plan_exceeds_headroom` in `tests/advisor/rules/test_plan.py`, `test-the_power_clause_displaces_the_built_clause_in_the_one_slot`, and the chain's tier-2 budget arm stays green with the clause present.
9. Tier 1, the card id and `requires` do not move on any verdict. Test: `test-the_power_verdict_moves_no_headline_or_card_id`.
10. `BACKLOG.md` lines 1160-1162 (the session-155 power-figure row) is replaced by one line pointing at this item's LEDGER close; no second row restates it.
11. `.venv/Scripts/python.exe -m pytest tests/solve tests/advisor tests/surface/test_advice_golden.py -q` exits 0, and tests/solve/test_golden.py is unchanged.

## CS-1425

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-030. Class: product. Lane flag: false (not eligible). Planned minutes: 360 (4 parts (120, 70, 100, 70)).
Depends on: CS-1401; CS-1398.5.
Wave: W44, W45, W46 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-030.3 in W46: `tests/advisor/test_world_advice.py` 1/2; U-030.4 in W46: `tests/advisor/test_world_advice.py` 2/2.
Write-list:
- U-030.1 (W44-G1-S2, 120 min): `clockspeed/advisor/rules/` `production`, `tests/advisor/rules/` `test-production`
- U-030.2 (W45-G3-S2, 70 min): `clockspeed/advisor/advise.py`, `tests/advisor/rules/` `test-production`, `tests/advisor/test_world_advice.py`
- U-030.3 (W46-G1-S2, 100 min): `clockspeed/advisor/ranking.py`, `tests/advisor/test_ranking.py`, `tests/advisor/test_every_rule_fires.py`, `clockspeed/advisor/rules/__init__.py`, `tests/advisor/test_world_advice.py`, `tests/surface/golden/advice_no_target.json`
- U-030.4 (W46-G3-S2, 70 min): `tests/advisor/worlds.py`, `tests/advisor/test_world_advice.py`

### Acceptance

Leaf section `## CS-NEW` in `docs/item_notes/phase5.md`, heading `### Acceptance`. Every arm below is in `tests/advisor/rules/` test_production.py unless a file is named.

1. A synthetic world whose machines consume an intermediate at 60 per minute and produce it at 30 yields ONE `production.item_deficit` card: tier 1 names the producing building and the exact whole count n; tier 2 states produced and consumed per minute and names the recipe; tier 3 lists every deficit with produced, consumed and net as exact rationals. ``test-a_sixty_thirty_world_yields_one_deficit_card_with_an_exact_whole_count``.
2. n is the ceiling of the deficit over the per-machine output per minute at clock 1 of the built recipe with the MOST machines for that item, ties broken by recipe key ascending; `requires` holds that recipe's unlock key; the quantity is n in the machines unit, and n is recorded by a `ctx.compute` step (the ceiling itself), so the quantity is a figure its own trace carries (CS-1398 clause 8, `test-a_fired_quantity_is_a_figure_its_own_trace_carries` in `tests/advisor/test_every_rule_fires.py`). A most-built recipe whose `asset_path` is None (`clockspeed/data/registry.py` line 1070) has no unlock key: the item is `verdict-indeterminate`, never a card with an empty `requires`. ``test-n_is_the_ceiling_over_the_most_built_recipe_at_clock_one``, ``test-a_machine_count_tie_is_broken_by_recipe_key``, ``test-the_machine_count_is_a_computed_step_of_the_trace``, ``test-a_most_built_recipe_with_no_asset_path_is_indeterminate``.
3. One card per rule (D44): the worst deficit (most negative net, ties by item key ascending) is tier 1; subject key `production:<item key>`; the card id is equal across two synthetic saves where the same item stays worst. ``test-the_worst_deficit_leads_and_the_card_id_holds_across_two_saves``.
4. Never fired: a raw item (`registry.resource_items`) with a negative net; an item consumed with NO built producer (listed in tier 3 with the reason `no-producer-built`, and it never fires even alone); an item whose producer or consumer recipe sits in a flow gap (recorded `verdict-indeterminate`); an item that any registry recipe makes or consumes in a building class named in `WorldFlow.unadmitted` (`clockspeed/audit/flow.py` line 502; such records keep `complete` False at `clockspeed/audit/flow.py` line 812 but are outside `ItemFlow.producers` and `.consumers`, so a missing producer OVERSTATES the deficit) - also `verdict-indeterminate`. UNVERIFIED: how an unadmitted class name maps to a `produced_in` key; read `unadmitted_census_of` in `clockspeed/audit/balance.py` and match as it does. ``test-a_raw_item_with_a_negative_net_yields_no_card``, ``test-an_item_with_no_built_producer_never_fires_and_is_listed``, ``test-an_item_touched_by_a_flow_gap_is_indeterminate_and_never_fired``, ``test-an_item_whose_recipe_runs_in_an_unadmitted_class_is_indeterminate_and_never_fired``.
5. Every item that is both made and consumed netting at or above zero, with no gap and no unadmitted record touching one, yields no card and a DEFINITE verdict, so a shown card completes through `Ledger.reconcile`; with a gap or an unadmitted record touching one the rule is not settled. ``test-a_balanced_world_settles_silent``, ``test-a_gapped_world_with_no_deficit_does_not_settle``.
6. Wording: tier 1 and tier 2 each contain the word `nominal`; tier 2 contains `storage`, `hand feeding`, `vehicles` and `sinks`; when `WorldFlow.complete` is False tier 2 says the list of deficits is `a floor` and gives the gap count and the unadmitted record count. The floor is the LIST (items a gap or an unadmitted record touches are left out, clause 4), never a fired figure: a fired item is touched by neither. ``test-both_tiers_say_nominal_and_tier_two_names_the_unseen_supplies``, ``test-an_incomplete_flow_reads_as_a_floor_with_its_gap_and_unadmitted_counts``.
7. Property: over generated unlock states no fired production card needs a locked recipe; with the built recipe's key withheld the card is not produced. ``test-no_fired_card_requires_a_locked_recipe``.
8. `production.idle_machines` fires only when `producing_available` is True and the starved set is non-empty; its reason says the upstream cause is unavailable while `connected_edges_available` is False; `producing_available` False is `verdict-indeterminate`. An empty starved set is a definite silence ONLY when `WorldStarvation.indeterminate_record_count` is 0 and `.unadmitted` is empty (`clockspeed/audit/balance.py` lines 1031-1035, `clockspeed/audit/balance.py` line 1046, `clockspeed/audit/balance.py` line 1048: the starved set is short by whatever those hold); otherwise it is `verdict-indeterminate`, so that silence never settles the rule and never completes a shown card through `Ledger.reconcile`. ``test-idle_machines_fires_only_on_an_available_non_empty_starved_set``, ``test-idle_machines_says_the_upstream_cause_is_unavailable``, ``test-an_empty_starved_set_beside_indeterminate_or_unadmitted_records_does_not_settle``.
9. No float in any offered input, every offered name starts `production.`, and each is sourced to its audit field. ``test-every_offered_input_is_exact_prefixed_and_sourced``.
10. The raw set reaches only the family's own `flow_of` call: the fuel inputs `inputs_of` offers equal `fuel_inputs(fuel_supply_of(machines, registry), registry)`. ``test-the_fuel_inputs_are_unchanged_by_the_production_flow``.
11. Registration: both ids have a firing and a silent fixture and an `EFFORT_BY_RULE` entry (`production.item_deficit` MIDDLE, `production.idle_machines` QUICK); `production.item_deficit` is in `MAGNITUDE_RULES`, and the expected set of CS-1398's census arm `test-exactly_the_magnitude_rules_fire_with_a_quantity` in `tests/advisor/test_every_rule_fires.py` grows by that id in the same commit; the census stays empty. `tests/advisor/test_every_rule_fires.py::test_every_registered_rule_has_a_firing_fixture`, `tests/advisor/test_ranking.py::test_the_effort_table_names_no_rule_that_is_not_registered`, ``test-a_deficit_of_nine_machines_ranks_large_and_of_two_middle``.
12. End to end over the real composition: `test-a_deficit_world_serves_a_production_card_in_its_own_domain_turn` in `tests/advisor/test_world_advice.py` (domain `production`, interleaved with a power card) and ``test-a_deficit_card_completes_when_the_deficit_is_closed``.

## CS-1426

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-031. Class: product. Lane flag: false (not eligible: shares advise.py, ledger.py and the advice endpoint with five other units; ledger privacy arms). Planned minutes: 310 (3 parts (120 + 115 + 75)).
Depends on: CS-1257.11; CS-1251.2; CS-1252.4; CS-1401.
Wave: W31, W32 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-031.1 in W31: `tests/advisor/test_every_rule_fires.py` 1/2, `tests/surface/test_advice.py` 2/2; U-031.2 in W32: `clockspeed/surface/web/panel_advice.js` 3/3, `tests/surface/test_panel_advice.py` 3/3.
Write-list:
- U-031.1 (W31-G1-S2, 120 min): `clockspeed/advisor/ledger.py`, `tests/advisor/test_ledger.py`, `clockspeed/advisor/advise.py`, `tests/advisor/test_advise.py`, `clockspeed/surface/api/advice.py`, `tests/surface/test_advice.py`, `tests/surface/test_advice_act.py`, `tests/surface/test_advice_golden.py`, `tests/surface/golden/advice_no_target.json`, `tests/advisor/test_every_rule_fires.py`
- U-031.2 (W32-G1-S2, 115 min): `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `clockspeed/surface/web/app.css`
- U-031.3 (W32 merger landing after U-031.2, 75 min): `BOOTSTRAP.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`, `ROADMAP.md`, `docs/item_notes/phase5.md`, `docs/history_notes.md`

### Acceptance

1. Wire: `advice.DATA_KEYS` (clockspeed/surface/api/advice.py line 285) becomes `{"new_world", "cards", "completed", "reopened"}` on BOTH GET /api/advice and POST /api/advice/act, so the act body stays exactly the listing. Both are lists, present and empty (never absent) when nothing changed; on GET both are always `[]`. Tests: `test-a_get_listing_carries_empty_completed_and_reopened` in `tests/surface/test_advice.py`, `test-the_act_body_key_set_is_the_listing_key_set` in `tests/surface/test_advice_act.py`.
2. Entry shape: `TRANSITION_KEYS = ("id", "rule_id", "headline")`. A completed entry's headline is the STORED tier-1 headline or null; a reopened entry's headline is the tier-1 headline of the card firing in this run, never the store. No tier 2 or tier 3 text in either.
3. Store: the ledger records, for each card an act shows, its tier-1 headline and the registry content pin the run was given (`pinned_docs_sha256`). A run with no pin stores no headline. A stored empty headline is refused with StoreCorruptError on read. Documents of versions 1 to 4 still read and their completed entries carry null headlines. Tests in tests/advisor/test_ledger.py: `test-an_act_stores_the_headline_and_the_pin_it_was_worded_under`, `test-a_stored_empty_headline_is_refused`, `test-a_version_4_document_reads_and_yields_no_headline`.
4. Pin rule: a stored headline is served only when its stored pin equals the current run's pin; otherwise null (the line is then count-only). Test: `test-a_headline_stored_under_another_pin_is_withheld` in `tests/advisor/test_advise.py`.
5. Sequence: `test-a_fixed_card_is_completed_once_with_its_headline` in `tests/surface/test_advice_act.py` - one synthetic world acted on, the deficit fixed, acted on twice more: the second act serves the card under `completed` with its headline, the third serves `[]`. `test-a_rule_that_raised_completes_nothing`.
6. Filters: no completed entry for a muted rule (`MuteStore.is_muted`), none for a rule in `EVENT_RULES`. Tests: `test-a_muted_rules_completion_is_not_a_transition` in `tests/advisor/test_advise.py`, `test-an_event_rules_completion_is_not_a_transition` (plants a rule id into a patched `EVENT_RULES`).
7. No GET writes: `test-two_reads_leave_both_stores_byte_identical` in `tests/surface/test_advice.py` (ledger document and mute store bytes compared before and after).
8. Privacy: `test-a_stored_headline_reaches_no_log_line_and_no_exception_text` in `tests/advisor/test_ledger.py` (caplog and every StoreError message searched for the planted headline; found 0); `test-no_world_identity_canary_reaches_any_rules_tier_1` in `tests/advisor/test_every_rule_fires.py` plants canaries in the fixture world token and every header string (a world name, an account-like digit run, a home-like path) and finds none in any registered rule's tier 1. D36's own arm: `test-no_world_identity_canary_reaches_a_stored_headline` in `tests/advisor/test_ledger.py` acts on that canary-world fixture, reads the stored ledger document back and finds 0 canary substrings in every headline field; the world-token key that keys the document is excluded from the search, the headline values are not.
9. Page: `test-the_done_line_shows_a_count_and_at_most_one_headline` in `tests/surface/test_panel_advice.py` - one element `id="advice-done-line"`, `aria-live="polite"`, text `"<n> done"` or `"<n> done: <headline>"` using the first completed entry with a non-null headline; `test-the_done_line_is_set_only_by_an_act_response` (a GET repaint leaves it; the next act replaces it); `test-the_done_line_has_no_control_and_starts_no_timer`; `test-the_done_line_slot_is_reserved` (app.css gives `.advice-done` a fixed min-height so nothing reflows); `test-a_build_mismatch_appends_the_fixed_words` - when the listing's CS-1252 freshness member reads stale for a build reason the text ends with the constant `DONE_LINE_BUILD_WORDS = " (game build differs from the pin)"`.
10. Golden: tests/surface/golden/advice_no_target.json gains `"completed": []` and `"reopened": []`; tests/surface/test_advice_golden.py passes.
11. Records: docs/LEDGER.md holds the D36 ruling record BEFORE any code commit; BOOTSTRAP.md section 7.1 and docs/ARCHITECTURE.md describe the two keys and the done line.

## CS-1427

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-037. Class: product. Lane flag: false (not eligible: R-feat-zone-2: the id is allocated by the session merger, never a lane; the hub commit stays out of the advisor-ranking lane scope). Planned minutes: 420 (over 5 live parts (.1 90, .5 60, .2 110, .3 120, .8 40); .4, .6 and .7 are void (0 minutes), see Data corrections).
Depends on: CS-1401; CS-1398.5; CS-1425 part 4 (U-030.4); CS-1243.3; U-037.2 also waits on stage 0 (plan key U-046, the block below; D47).
Wave: W5, W48, W49, W52 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-037.1 in W48: `tests/solve/test_phase3_gate.py` 2/2.
Write-list:
- U-037.1 (W48-G2-S2, 90 min): `clockspeed/solve/` `haul`, `tests/solve/` `test-haul`, `tests/solve/test_phase3_gate.py`
- U-037.2 (W49-G1-S2, 110 min): `clockspeed/advisor/rules/` `transport`, `tests/advisor/rules/` `test-transport`
- U-037.3 (W52-G1-S1, 120 min): `clockspeed/advisor/rules/__init__.py`, `clockspeed/advisor/advise.py`, `clockspeed/advisor/ranking.py`, `tests/advisor/test_every_rule_fires.py`, `tests/advisor/worlds.py`, `tests/advisor/test_advise.py`, `tests/advisor/test_world_advice.py`
- U-037.5 (W5-G3-S2, 60 min): `clockspeed/data/registry.py`, `tests/data/test_transport_rates.py`
- U-037.8 (W52 merger landing after U-037.3, 40 min): `docs/ARCHITECTURE.md`, `docs/item_notes/phase5.md`
Parts U-037.4, U-037.6 and U-037.7 are void (0 minutes; the plan's Data corrections and D47, D138).

### Acceptance

Stage a only; every test below is new unless marked existing. Run each file by path with `.venv/Scripts/python.exe -m pytest <file> -q` (expect exit 0, read from a log, never through a pipe).
1. `test-a_sole_consumer_raw_item_yields_exact_rates_and_integer_carrier_counts` in `tests/solve/` test_haul.py - `haul_of(edges, transports, unlocked)` returns per raw-supplied item (an edge with `producer is None`) the exact raw rate, the exact refined rate (the summed edges of the sole consuming recipe's one product) and `raw_carriers` / `refined_carriers` as `int`, each the ceiling of rate over the fastest UNLOCKED carrier of that unit, by integer arithmetic; fixture rates such as 1/3 and 200/3 that do not terminate.
2. `test-haul_refuses_a_float` in `tests/solve/` test_haul.py and `test-the_module_names_no_float_or_rounding` - a float operand raises `InexactValueError` through `audit_exact(report, path="haul")`; an AST arm finds no `float`, `round`, `math` or `/ 1.0` in `clockspeed/solve/` haul.py.
3. Negative, `test-an_ineligible_item_is_flagged_and_never_compared` in `tests/solve/` test_haul.py (parametrized over the six codes) - a row with `ineligible` set has both counts None and can never be `worst`: `no-consumer` (every raw edge of the item has `consumer is None`: it goes straight to a sink), `split-sink` (one consuming recipe AND a raw edge with `consumer is None`: part of the supply is delivered raw, so the raw rate is not the recipe's intake; its own case in the parametrization), `multi-consumer` (more than one consuming recipe), `multi-input` and `multi-product` (the sole consumer has more than one input item or more than one product among the plan edges: "the product" has no single referent, non-negotiable 7), `no-carrier` (unit unknown, no published rate, or no unlocked carrier for either unit). A row that fits several codes takes the FIRST in the order just listed, and one arm pins that order.
4. `test-no_locked_carrier_is_ever_named` in `tests/solve/` test_haul.py and `test-a_locked_carrier_never_reaches_a_card` in `tests/advisor/rules/` test-transport.py - seeded property (200 unlocked subsets, `random.Random(159)`): every carrier ClassName in a report or on a card is in the subset; with the empty subset every row not already flagged by an earlier code is `no-carrier` and no card issues.
5. `test-the_rule_fires_refine_when_the_refined_form_needs_fewer_carriers` in `tests/advisor/rules/` test-transport.py and `test-the_rule_fires_ship_when_the_raw_item_needs_fewer_carriers` - one `Recommendation` per run (D44 point 5), `domain == "transport"`, `rule_id == "transport.ship_or_refine"`, `subject_key == "transport:" + raw item ClassName`; tier 1 is one line with no newline and opens `Refine ` or `Ship `; the worst case (greatest absolute count difference, first in plan edge order among equals) is the one named. Settlement, new arm `test-a_fired_card_records_the_plan_was_never_compared_with_the_world`: before its `Recommendation` a firing run records exactly ONE `ctx.indeterminate` step saying the plan was never compared with the built world (precedent clockspeed/advisor/rules/plan.py line 1182; clockspeed/advisor/advise.py line 462), so a fired transport card never settles on the pin.
6. Negative, `test-equal_counts_issue_no_card_and_record_why`, `test-no_ranked_plan_issues_no_card_and_records_the_status` (parametrized over every `STATUS_*` in clockspeed/advisor/rules/plan.py lines 306-350 except `STATUS_RANKED`) and `test-a_ranked_plan_with_no_eligible_row_is_undecided` - no card, and the step kind is fixed per case: equal counts on every eligible row record `REASON_EQUAL` through `ctx.reject` and nothing indeterminate (a definite verdict: the rule settles on the pin); a non-ranked status records `REASON_NO_PLAN` plus the status through `ctx.indeterminate` (precedent clockspeed/advisor/rules/plan.py line 1154) and never settles; a ranked plan whose rows are all ineligible records `REASON_NO_ELIGIBLE` through `ctx.indeterminate` (it could not decide over flagged content, non-negotiable 7) and never settles.
7. `test-every_fired_card_carries_the_not_weighed_line`, `test-the_card_names_the_methods_considered` and `test-the_build_caveat_is_the_last_text_of_tier_2` - tier 2 of every fired card contains `LINE_NOT_WEIGHED == "Transport power cost and build cost are not weighed."` and `LINE_METHODS == "Methods considered: belts and pipes."`; every `LINE_*` sentence comes BEFORE the build caveat, which is appended last (off the pin tier 2 ends with the mismatch text, tests/advisor/test_every_rule_fires.py line 870), and on the pin no tier 2 text contains `build-` (tests/advisor/test_every_rule_fires.py line 842).
8. `test-the_not_modelled_line_appears_exactly_when_a_station_class_is_held` - tier 2 contains `LINE_NOT_MODELLED == "Trains, trucks and drones are not modelled."` when `transport.stations_held` is True and does not contain it when False.
9. `test-requires_names_each_cited_carriers_unlock_key`, `test-tier3_lists_every_row_with_its_reason`, `test-two_runs_are_byte_identical`, `test-the_rule_does_no_carrier_arithmetic` - `requires` is a `tuple[str, ...]` (clockspeed/advisor/trace.py line 246) of the `recipe:` keys of the carriers tier 1 names, raw-side carrier first, DEDUPLICATED: a pair that names one carrier for both sides yields a one-key tuple (one arm each for the two-key and the one-key form); tier 3 comes from the trace and shows each row, eligible or not; an AST arm finds no `//`, `/` or `*` BinOp in `clockspeed/advisor/rules/` transport.py (D138).
10. `test-every_carrier_class_joins_its_build_gun_recipe_by_descriptor` in `tests/data/test_transport_rates.py`, `test-buildable_recipe_refuses_an_undeclared_class` (KeyError), `test-a_carrier_with_no_build_gun_recipe_reads_none_never_free`, `test-haul_stations_lists_every_station_class_in_document_order`, `test-the_new_public_names_are_published` (`buildable_recipe` and `HAUL_STATION_GROUP_SHORT_NAMES` are in `registry.__all__`, as tests/data/test_registry.py lines 2423-2426 does for its names).
11. Census, existing arms that must go red at registration and green at the end: tests/advisor/test_ranking.py::test_every_registered_rule_declares_an_effort and ::test_the_effort_table_names_no_rule_that_is_not_registered; tests/advisor/test_every_rule_fires.py::test_every_registered_rule_has_a_firing_fixture, ::test_every_registered_rule_has_a_silent_fixture, ::test_every_registered_rule_lives_in_a_covered_module, ::test_the_recommendation_calls_are_pinned_to_the_fixture_count, ::test_every_registered_rule_declares_the_build_inputs. Also existing and red until re-pinned in the same commit: tests/advisor/test_world_advice.py::test_inputs_of_is_the_audit_composition_over_one_world (its `by_hand` oracle, tests/advisor/test_world_advice.py line 207, must merge the transport group) and tests/solve/test_phase3_gate.py::test_the_scanned_module_set_is_exactly_the_solve_package and ::test_the_scanned_solve_test_set_is_exactly_the_solve_test_package (part .1).
12. `test-inputs_of_offers_the_transport_inputs_beside_the_plan_offer` in `tests/advisor/test_advise.py` and `test-a_world_with_no_plan_request_keeps_the_transport_rule_silent` - `inputs_of` offers the five `transport.*` inputs on every world; with `plan_request=None` no transport card. This clause needs the inputs OFFERED over a plan that ranks, not a fired card: the PLAN_WORLD recipes are one in, one out at one duration (tests/advisor/worlds.py lines 421-423), so raw and refined rates are equal there; the FIRING world of clause 11 is hand-built `WorldInputs` with unequal counts.
13. Whole suite green through `ops/fleet_kit/fleet_suite_gate.py run --owner <id> -- <suite cmd>`; `.venv/Scripts/python.exe tools/drift_guard.py` exits 0; `git diff --stat` shows no change to clockspeed/advisor/plans.py and no file under clockspeed/audit/.

### Stage 0 - plan key U-046, its acceptance and filing record (D47: no row of its own)

Filed 2026-11-24 by the session 161 wave 0 filing inside the D2 row's section: D47 rules one row for the D2 family and U-046 is its stage 0, so it takes no line and no section of its own. The block `### Stage 0 - vehicle field spike (R-feat-zone-8)` its acceptance names is written by the merger at the spike's landing; this block is not it.
Plan key: U-046. Class: product. Lane flag: false (not eligible: needs the local game install; one read-only research agent plus the merger). Planned minutes: 45 (1 part (the unit record says 90)).
Depends on: none as a unit key; it lands only after this D2 section is filed (P4F-5).
Wave: W1, merger landing.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): none; no part shares a file with another unit of its wave.
Write-list:
- U-046 (W1 merger landing, 45 min): `docs/item_notes/phase5.md`; only on a no-go: `BACKLOG.md`
Stage 0 acceptance (U-046, verbatim):

0. Entry check (D93): this stage WAITS in its one part. The merger lands it at the W1 landing, only after this D2 section is filed (ruling P4F-5); its research agent is read-only and writes only to scratch.
1. An untracked report `<sidecars>/CS/Scratch/d2-vehicle-fields.md` lists, for each ENTRY SET of the class table below: present in the shipped docs (yes or no), the field NAMES whose value parses as a number on every entry of that set, and the quantities a rate would still need. It carries no entry count (D47: names and presence only). It also prints the unknown-group count of the document, and presence is read from `DocsDocument.all_groups`, never from the recognised groups alone. Groups (all in the census at clockspeed/data/docs_extract.py lines 134-252): `FGBuildableDockingStation` (:150), `FGBuildableDroneStation` (:152), `FGBuildableRailroadStation` (:195), `FGBuildableTrainPlatformCargo` (:209), `FGBuildableTrainPlatformEmpty` (:210), `FGVehicleDescriptor` (:246), plus every other group in the file whose short name contains Vehicle, Locomotive, Wagon, Drone or Truck.
   Class table (literal; names checked on the pinned docs). A station group is one entry set (all its entries). `FGVehicleDescriptor` mixes all three classes, so each of its entries is its own entry set, keyed by ClassName:
   - train: `FGBuildableRailroadStation`, `FGBuildableTrainPlatformCargo`, `FGBuildableTrainPlatformEmpty`; `Desc_Locomotive_C`, `Desc_FreightWagon_C`.
   - truck: `FGBuildableDockingStation`; `Desc_Truck_C`, `Desc_FluidTruck_C`, `Desc_Tractor_C`, `Desc_Explorer_C`.
   - drone: `FGBuildableDroneStation`; `Desc_DroneTransport_C`.
   - Any other entry or matching group (at this pin `Desc_CyberWagon_C` and `FGVehiclePathSegment`) is listed and graded for no class. A table name absent from the file is `present: no` (clause 8); a new unmatched entry is listed as unassigned and the adjudicator of clause 3 assigns it.
2. Control, run FIRST: the same script lists `FGBuildableConveyorBelt` (:145) and must report `mSpeed` (clockspeed/data/registry.py line 648) as numeric. If it does not, the reader is wrong and no verdict is written.
3. Verdict rule, per carrier class (train, truck, drone): GO only when the docs export all three of (a) cargo capacity per trip, (b) travel speed, (c) load and unload time or rate; distance is never a docs field. Any one absent is NO-GO for that class, and the block names the absent quantities. Which field NAME counts as which quantity is NOT decided by the script or its author: before any VERDICT line is written, a distinct adjudicator rules, from the names-only report, a literal mapping table with one row per (class, entry set, field name, quantity a, b or c), and the block carries that table. A quantity is exported for a class only when a row maps a field that is numeric on every entry of its set; a field with no row counts for nothing. Candidates the adjudicator must rule in or out, names only and none pre-mapped: `mInventorySize` (on every descriptor entry except `Desc_Locomotive_C`), `mTimeToCompleteLoad`, `mItemTransferRate`, `mLoadUnloadCycleLength`, `mTransferSpeed`, `mStackTransferSize`. The block carries one line per class: `VERDICT <class>: GO` or `VERDICT <class>: NO-GO - missing <quantities>`.
4. Names and presence only (T3): the report and the leaf block contain no numeric value read from the docs and no description text. Check: the adjudicator reads the field list against the generated registry and confirms no `name = value` pair appears.
5. On any NO-GO, exactly one line is added to BACKLOG.md by the merger, under a heading the merger writes after the last one (BACKLOG.md line 1365), `## Session 159 residuals - filed <date> under product before process` (if that heading already exists, the line goes under it), in the file's existing form: `- D2 vehicle model (<classes>): a round-trip throughput for <classes>, its model in \`clockspeed/solve/\` - TRIGGER: the shipped docs export <missing quantities> for <classes>. The spike: \`docs/item_notes/phase5.md\`, the D2 section, stage 0.` On GO for all three classes no BACKLOG line is written.
6. No code lands: after the research agent, `git status --porcelain` prints nothing. The doc slice is conditional: docs/item_notes/phase5.md has no D2 section at HEAD, so when the D2 row's section is still absent as the spike finishes, the merger HOLDS the scratch report and writes the block in the same commit that files the D2 row (D47); the unit is not done until the block is in the leaf. After the merger's doc slice, `git diff --stat` names only docs/item_notes/phase5.md (plus the row-filing files when the two land together), plus BACKLOG.md on a no-go.
7. Two runs of the script over the same install produce byte-identical reports; `tools/drift_guard.py` exits 0 after the doc slice.
8. Negative: a group or entry absent from `DocsDocument.all_groups` (recognised and unknown groups together) is reported `present: no` and makes its class NO-GO; it is never guessed from another group or from a wiki.

## CS-1428

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-038. Class: product. Lane flag: false (not eligible: interactive session only; shares routes.py and health.py with CS-1046). Planned minutes: 315 (3 parts (120 + 100 + 95)).
Depends on: CS-1046.4; U-107.3 (unfiled, by plan key).
Wave: W44, W47, W48 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-038.1 in W44: `tests/surface/audit_harness.py` 1/2, `tests/surface/test_web_assets.py` 1/2; U-038.3 in W48: `clockspeed/surface/web/app.css` 1/3, `clockspeed/surface/web/panel_advice.js` 1/3, `tests/surface/test_panel_advice.py` 1/3.
Write-list:
- U-038.1 (W44-G2-S2, 120 min): `clockspeed/surface/api/advice.py`, `tests/surface/test_advice.py`, `clockspeed/surface/api/routes.py`, `clockspeed/surface/api/health.py`, `clockspeed/surface/providers.py`, `clockspeed/surface/web/app.js`, `tests/surface/test_advice_source.py`, `tests/surface/test_health.py`, `tests/surface/test_routes.py`, `tests/surface/test_acceptance.py`, `tests/surface/test_pending.py`, `tests/surface/test_web_assets.py`, `tests/surface/audit_harness.py`
- U-038.2 (W47-G2-S1, 100 min): `clockspeed/surface/providers.py`, `tests/surface/test_panel_advice.py`, `clockspeed/surface/api/advice.py`, `clockspeed/surface/web/app.js`, `tests/surface/test_advice.py`, `tests/surface/test_advice_source.py`, `tests/surface/audit_harness.py`, `tests/surface/golden/advice_no_target.json`, `tests/surface/test_web_assets.py`
- U-038.3 (W48-G2-S1, 95 min): `clockspeed/surface/web/panel_advice.js`, `clockspeed/surface/web/app.css`, `tests/surface/test_panel_advice.py`

### Acceptance

1. `POST /api/advice/mute?rule=<id>&muted=true` with the same-origin proof answers 200 with body keys exactly `MUTE_KEYS` = {`rule`, `muted`}; `mutes.json` then holds the id; `muted=false` removes it; each admitted request calls the store's write exactly once (`test-a_mute_post_writes_the_mute_store_exactly_once` in `tests/surface/test_advice_source.py`, a recording spy on `MuteStore._save`).
2. The same request without the proof is 403 `cross_origin_refused` before the handler runs and both store files are byte-identical (`test-a_mute_post_without_the_proof_is_refused_and_writes_nothing` in `tests/surface/test_advice_source.py`); `NON_SAFE_ROUTES` gains `("POST", "/api/advice/mute", True)` and the guarded set at `tests/surface/test_advice_source.py` lines 714-720 holds three pairs (rename that arm: its name states two, CS-1029).
3. `GET /api/advice/mute` is 405 `method_not_allowed`; `tests/surface/test_pending.py` `METHOD_BOUNDARY_ROUTES` gains `("GET", "/api/advice/mute")`.
4. A `rule` outside `registered_rules()` is 400 `invalid_parameter`, the body does not contain the typed value (canary string arm) and the store is unchanged; `muted` outside the closed tokens `true`/`false` is 400 `invalid_parameter`; a missing `rule` or `muted` is 400 `missing_parameter`; any other name is 400 `unknown_parameter` (`test-an_unregistered_rule_is_refused_and_nothing_typed_is_reflected` in `tests/surface/test_advice.py`, ``test-a_mute_request_with_a_wrong_or_missing_name_is_refused``). The refusals hold one order, the first that applies wins and every 400 is decided before the store is read: unknown name, missing name, `muted` outside its tokens, unregistered `rule`, and only then the store's 503. So `?foo=1` alone is `unknown_parameter`, a bad `muted` beside an unregistered `rule` is `invalid_parameter` for the token, and an unregistered `rule` over a corrupt `mutes.json` is 400, not 503 (`test-the_mute_refusals_hold_one_order` in `tests/surface/test_advice.py`, one parametrised arm per adjacent pair).
5. The `GET /api/advice` body, and so the act body, gains `muted_rules`: the sorted ids in the store, listed whether or not the rule fires, `[]` when none. `advice.DATA_KEYS` == {`new_world`, `cards`, `muted_rules`} (`test-the_listing_names_a_muted_rule_that_does_not_fire` in `tests/surface/test_advice_source.py`).
6. A corrupt `mutes.json` answers 503 `advice_store_unreadable`; an unwritable one answers 503 `advice_store_unwritable`; in both cases `ledger.json` and `mutes.json` are byte-identical before and after (`test-a_mute_over_an_unreadable_or_unwritable_store_is_503_and_changes_no_byte` in `tests/surface/test_advice_source.py`).
7. Muting never writes `ledger.json` (bytes identical, an absent file stays absent) and changes no card's `state`; the muted rule's cards list `muted` true and `visible` false; unmuting restores `visible` true (`test-mute_then_unmute_restores_visibility_and_never_touches_the_ledger` in `tests/surface/test_advice_source.py`).
8. No GET writes: after `GET /api/advice` and `GET /api/advice/mute` both store files are byte-identical (`test-no_get_writes_either_store` in `tests/surface/test_advice_source.py`).
9. Table bindings: `health.ENDPOINT_TEMPLATES` names `/api/advice/mute` directly after `/api/advice/act`; the BOOTSTRAP.md section 7.1 "Endpoints, minimum:" sentence names it in the same place; the page route table gains `{ template: "/api/advice/mute", method: "POST", probe: null }`; the three count pins move 13 to 14 (`tests/surface/test_health.py` `EXPECTED_ENDPOINTS`, `tests/surface/test_routes.py` `PUBLISHED_ENDPOINTS`, `tests/surface/test_acceptance.py` `PUBLISHED_ENDPOINTS` plus its two transcribed lists); `tests/surface/test_route_table_binding.py` is green and unedited.
10. Page door: `app.js` publishes `requestMute(rule, muted, onSettled)` beside `requestState`; it sends `"/api/advice/mute?" + query` as a POST with header `X-Clockspeed-Request: 1` and no body; `EXPECTED_NON_GET_FETCHES` moves 4 to 5 and `NON_GET_TARGETS` gains that target (`tests/surface/test_web_assets.py::test_the_page_issues_exactly_the_pinned_posts_and_no_form`).
11. Every rendered card has a button, id `advice-mute-<position>`, text `Mute this rule`, aria-label `Mute this rule: <headline>`; one press calls the door once with the card's `rule_id` and `true` (`test-each_card_offers_mute_this_rule_and_a_press_calls_the_door_once` in `tests/surface/test_panel_advice.py`).
12. When `muted_rules` is non-empty a region id `advice-muted-rules` shows each id with a button, id `advice-unmute-<index>`, text `Unmute`, aria-label `Unmute: <rule id>`; it is absent when the list is empty and present when zero cards are listed (``test-the_muted_line_offers_unmute_with_no_card_on_screen``).
13. After a settled mute or unmute `document.activeElement` is the pressed control if still connected, otherwise the element id `advice-status`; never `body` (``test-a_mute_or_unmute_never_drops_focus_to_the_document``). A page with no `requestMute` says `this page published no mute door; nothing was sent.` and sends nothing (``test-a_page_with_no_mute_door_says_so_at_the_press``).
14. Green and unedited: `tests/surface/test_web_assets.py::test_the_page_offers_exactly_one_kind_of_clickable_target` and `::test_the_page_repaints_on_a_button_and_never_on_a_timer`.
15. A settled mute or unmute re-reads the listing through `requestAdvice` with the statement the standing answer was asked under (none when it was unstated), so a stated answer stays that stated answer. The muted-rules line is redrawn from the re-read's `muted_rules` on BOTH repaint paths: after `reconcileInPlace` (clockspeed/surface/web/panel_advice.js:1046) returns true, which is the path that drops the muted rule's boxes while another visible card remains, and inside the full `fillAnswer` redraw (:975) taken when no visible card remains or an unmute adds a card (`test-a_mute_under_a_stated_answer_keeps_that_answer_and_redraws_the_muted_line` in `tests/surface/test_panel_advice.py`, with one arm per path).
16. `/api/health` reads the route live: `routes.ENDPOINT_STATUS[advice_endpoint.MUTE_ENDPOINT] == health.LIVE`, as the state route's arm at tests/surface/test_advice_source.py line 685 does (`test-the_mute_route_reads_live_in_health` in `tests/surface/test_advice_source.py`).
17. The source seam is optional: a source that is not a `MutingAdviceSource` lists `muted_rules` `[]` and answers a mute 503 `advice_store_unwritable`, and no existing fake gains a method (`test-a_source_with_no_mute_door_lists_none_and_answers_a_mute_as_unwritable` in `tests/surface/test_advice.py`).
18. The stand-in server answers the route: `audit_harness.CANNED` holds a `("POST", advice_endpoint.MUTE_ENDPOINT)` row with exactly `MUTE_KEYS` (`tests/surface/test_web_assets.py::test_the_harness_answers_every_route_it_publishes_as_live`, green and unedited).

## CS-1429

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-039. Class: product. Lane flag: false (not eligible: edits advise.py and the aging tests beside CS-1401; adversary pass required). Planned minutes: 300 (3 parts (100 + 100 + 100)).
Depends on: CS-1401; CS-1257.11; CS-1204; CS-1426 part 2 (U-031.2); CS-1251.2; CS-1432 part 8 (U-049.8); U-107.3 (unfiled, by plan key).
Wave: W33 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-039.1 in W33: `tests/advisor/test_advise.py` 2/2, `tests/advisor/test_ledger.py` 2/2.
Write-list:
- U-039.1 (W33-G1-S1, 100 min): `clockspeed/advisor/advise.py`, `tests/advisor/test_advise.py`, `clockspeed/advisor/ledger.py`, `tests/advisor/test_ledger.py`
- U-039.2 (W33-G2-S2, 100 min): `clockspeed/surface/providers.py`, `clockspeed/surface/api/advice.py`, `tests/surface/test_advice_act.py`, `tests/surface/test_advice_source.py`, `tests/surface/test_advice_aging.py`, `tests/surface/test_advice.py`, `tests/surface/audit_harness.py`
- U-039.3 (W33-G3-S2, 100 min): `clockspeed/surface/web/app.js`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`, `tests/surface/test_web_assets.py`

### Acceptance

1. `POST /api/advice/act?form=reconcile` with the same-origin proof is one act in RECONCILE form: completed and reopened transitions are recorded, newly shown cards are recorded `new` at zero, and `Ledger.reconcile` is called with `shown=()` (`test-a_reconcile_only_act_passes_no_showing_order` in `tests/advisor/test_advise.py`, a recording spy on `Ledger.reconcile`).
2. N = 5 reconcile acts on one unchanged world leave every shown-and-deferred count unchanged and `ledger.json` byte-identical after the first (`test-n_reconcile_acts_on_one_save_leave_the_ledger_byte_identical_after_the_first` in `tests/surface/test_advice_act.py`; control: the same five PRESSED acts do move a count).
3. `form` is a closed parameter with the one token `reconcile`: any other value is 400 `invalid_parameter` and reflects nothing typed; `form=reconcile` beside any statement name (`target`, `rate`, `direction`, `byproduct_policy`, `schematic`) is 400 `unknown_parameter`; without the proof it is 403 as today (`test-the_reconcile_form_is_a_closed_token_and_takes_no_statement` in `tests/surface/test_advice_act.py`). Order: the form check runs BEFORE `_stated_plan`. A `form` outside `ACT_FORMS` is `invalid_parameter` whatever else the query holds (`form=bogus&target=x` is `invalid_parameter`); `form=reconcile` beside ANY other name is `unknown_parameter`, so a partial plan beside it never reaches the `missing_parameter` branch (clockspeed/surface/api/advice.py lines 558-560); a query with no `form` goes to `_stated_plan` exactly as at HEAD (``test-the_form_check_runs_before_the_statement_check``, one arm per case).
4. An act with no `form` is the pressed act exactly as at HEAD, showing order included. The existing arms of `tests/surface/test_advice_aging.py` pass with not one assertion edited, and one arm is ADDED: reconcile acts interleaved between pressed acts do not change which pressed act reaches `AGING_EVALUATIONS` (``test-reconcile_acts_between_presses_do_not_move_the_aging_threshold``).
5. A card the world now satisfies is recorded `completed` by a reconcile act (read back through `Ledger(directory)` and named on the act's `Advice.completed`); a card whose rule raised or lacked an input is untouched (`test-a_reconcile_act_completes_a_satisfied_card_and_skips_an_undecided_rule` in `tests/surface/test_advice_act.py`).
6. Nothing new is stored: after reconcile acts the ledger document's key set equals the key set a pressed act writes, a stored `standing` statement is byte-identical before and after, and no value derives from the header save instant or play time, in clear or as a digest (`test-a_reconcile_without_a_showing_order_stores_no_new_key` in `tests/advisor/test_ledger.py`). Every GET, the world provider and `/api/health` stay write-free: `tests/surface/test_server.py` no-write sweep green and unedited.
7. The page sends exactly one reconcile act before its first listing read, and exactly one per new save generation announced by U-049; a Refresh press under an unchanged generation sends none (`test-first_paint_sends_one_reconcile_act_and_a_same_generation_repaint_sends_none` in `tests/surface/test_panel_advice.py`, ``test-a_new_save_generation_sends_exactly_one_reconcile_act``).
8. A reconcile act refused because a request was in flight is retried when that request settles; nothing is queued on a timer (``test-a_reconcile_act_refused_in_flight_is_sent_when_the_running_request_settles``). `tests/surface/test_web_assets.py::test_the_page_repaints_on_a_button_and_never_on_a_timer` and `::test_the_page_issues_exactly_the_pinned_posts_and_no_form` stay green and unedited (the act reuses the pinned target).
9. The generation the page last reconciled under is a script variable only: no asset names `localStorage`, `sessionStorage`, `indexedDB` or `document.cookie` (`test-no_asset_persists_the_reconciled_generation` in `tests/surface/test_panel_advice.py`, with a planted-positive control).
10. An automatic act never moves focus and never replaces a standing stated answer; its outcome reaches the panel as `data.reconciled` (``test-an_automatic_act_keeps_focus_and_a_standing_stated_answer``).
11. The source seam is optional and the pressed call is unchanged: with no `form` the handler calls `source.act(model, registry, plan_request=...)` with no new keyword, so the fake at tests/surface/test_advice.py line 1140 stays green unedited; with `form=reconcile` it calls `reconcile_act` on a `ReconcilingAdviceSource`, and a source that is not one answers 503 `advice_store_unwritable` (`test-a_pressed_act_calls_the_source_exactly_as_before` in `tests/surface/test_advice.py`, ``test-a_source_with_no_reconcile_door_answers_the_form_as_unwritable``).
12. The stand-in server answers the form: `POST /api/advice/act?form=reconcile` to `audit_harness` is the unstated canned act body, not 400 (`test-the_stand_in_answers_a_reconcile_act_with_the_unstated_body` in `tests/surface/test_advice.py`).
13. The page door admits the name: `REQUESTS.act.optional` holds `form` beside the statement names, and the builder refuses any `form` value but `reconcile` and any `form` beside another name (false returned, nothing sent) (`test-the_act_door_admits_form_only_as_reconcile_and_alone` in `tests/surface/test_web_assets.py`).
14. `docs/LEDGER.md` carries, dated before the first code commit, the D37 and D38 readings: one aged act is one PRESSED act (session 157 D3 kept), and the reconcile form re-opens none of the CS-1240 FS-A grounds. Check: `grep -n "FS-A" docs/LEDGER.md` shows the new entry.

## CS-1430

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-040. Class: product. Lane flag: false (not eligible: per the unit record (two new files, disjoint from every other unit; safe beside any lane)). Planned minutes: 75 (1 part).
Depends on: none.
Wave: W20, group 3, slice W20-G3-S2.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): none; no part shares a file with another unit of its wave.
Write-list:
- U-040 (W20-G3-S2, 75 min): `clockspeed/progress/` `delta`, `tests/progress/` `test-delta`

### Acceptance

All tests are in NEW `tests/progress/` test_delta.py, on hand-authored synthetic catalogs, registries and unlock states.

1. `snapshot_of(unlocks, catalog, registry, *, world)` returns a frozen `ProgressSnapshot` with exactly these fields: `world` (the caller's opaque 64-hex world digest), `schematics` (bought schematic ClassNames), `recipes` (unlocked recipe registry keys), `phase_digest` (str or None), `unmatched_schematic_paths` (int), `unmatched_recipe_paths` (int), `comparable` (bool), `digest` (64-hex content digest of the other seven) (``test-a_snapshot_holds_exactly_the_published_fields``).
2. The join is exact whole-string asset-path equality: a purchased path that equals a `Schematic.asset_path` yields that ClassName; a path sharing only the trailing class token joins nothing and is counted in `unmatched_schematic_paths`; the same for `UnlockState.recipes` against `Recipe.asset_path` (``test-a_path_sharing_only_its_trailing_token_joins_nothing_and_is_counted``). A schematic or recipe whose `asset_path` is None is never listed.
3. The phase is an equality fact only: `phase_digest` is `sha256(b"clockspeed.progress.phase\0" + path.encode("utf-8")).hexdigest()` of `UnlockState.current_game_phase`, None when that field is None; no phase key, name or order is published (``test-the_phase_is_published_as_a_one_way_digest_only``).
4. `comparable` is False when `catalog` is None or `unlocks.is_empty()`; such a snapshot holds empty tuples, zero counts and `phase_digest` None, even when `UnlockState.current_game_phase` is set (``test-a_snapshot_with_no_catalog_or_an_empty_unlock_state_is_not_comparable``, with a phase-bearing arm).
5. `delta_of(before, after)` returns a frozen `ProgressDelta` (`gained_schematics`, `gained_recipes`, `phase_changed`, `verdict`); `verdict` is a member of `VERDICTS` = (`advanced`, `unchanged`, `regressed`, `incomparable`), decided in this order: `incomparable` when either side is not comparable or the `world` values differ; `regressed` when `after` lacks any schematic or recipe `before` holds; `advanced` when a member was gained or the phase changed; else `unchanged` (``test-each_verdict_is_reached_by_its_own_fixture``, four cases).
6. `phase_changed` is True only when both sides hold a digest and the digests differ; a side with no phase gives False. A phase change with no gained member is `advanced` (``test-a_phase_change_alone_is_advanced``).
7. Only `advanced` carries members: for the other three verdicts both gained tuples are empty and `phase_changed` is False (``test-only_an_advanced_delta_carries_members``).
8. Determinism: every tuple is sorted by ClassName or registry key; a second process run with `PYTHONHASHSEED=0` and another with `PYTHONHASHSEED=1` print byte-identical `digest` values and delta fields for the same inputs (``test-two_hash_seeds_give_byte_identical_output``, the subprocess pattern of `tests/advisor/test_cards.py` line 622).
9. No path leaks: with a canary substring planted in every asset path of the fixture, the canary appears in no field of either model and in neither `repr`; each `repr` renders counts and the verdict only (``test-no_field_and_no_repr_holds_an_asset_path``). Negative control: the canary IS present in the fixture's `UnlockState.purchased_schematics`.
10. Both models pass `clockspeed.solve.exact.audit_exact` and hold no float (``test-both_models_pass_the_exact_audit``; control: a planted float is refused).
11. The module imports nothing from `clockspeed.advisor`, `clockspeed.surface` or `clockspeed.audit`, opens no file and reads no clock (``test-the_module_imports_only_the_layers_below_it``, an AST import census).
12. `tools/provenance_stamp.py check` exits 0 with one stamped row for each new file.

## CS-1431

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-041. Class: product. Lane flag: false (not eligible: edits advise.py and ranking.py behind CS-1401; adversary pass on the event-last order). Planned minutes: 315 (3 parts (115 + 100 + 100)).
Depends on: CS-1430 (U-040); CS-1428 part 3 (U-038.3); CS-1401; CS-1426 part 2 (U-031.2).
Wave: W49, W51, W53 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-041.1 in W49: `clockspeed/advisor/advise.py` 1/2, `clockspeed/save/world.py` 1/2, `tests/advisor/test_every_rule_fires.py` 1/2, `tests/save/test_world.py` 1/2; U-041.3 in W53: `clockspeed/surface/providers.py` 1/2.
Write-list:
- U-041.1 (W49-G1-S1, 115 min): `clockspeed/advisor/rules/` `progress`, `tests/advisor/rules/` `test-progress`, `clockspeed/advisor/rules/__init__.py`, `clockspeed/advisor/ranking.py`, `tests/advisor/test_ranking.py`, `clockspeed/advisor/advise.py`, `clockspeed/save/world.py`, `tests/save/test_world.py`, `tests/advisor/test_world_advice.py`, `tests/advisor/test_every_rule_fires.py`
- U-041.2 (W51-G2-S2, 100 min): `clockspeed/save/sightings.py`, `tests/save/test_sightings.py`, `clockspeed/surface/providers.py`, `clockspeed/progress/` `delta`, `tests/progress/` `test-delta`, `tests/surface/test_world_provider_memo.py`
- U-041.3 (W53-G3-S2, 100 min): `clockspeed/surface/api/advice.py`, `clockspeed/surface/providers.py`, `tests/surface/test_advice.py`, `tests/surface/test_advice_source.py`, `tests/surface/audit_harness.py`, `tests/surface/golden/advice_no_target.json`, `clockspeed/surface/web/panel_advice.js`, `tests/surface/test_panel_advice.py`

### Acceptance

1. `clockspeed.save.sightings.save_key(model)` is public and returns what the private `_save_key` returns; it is never stored or served (`test-the_public_save_key_tells_two_saves_of_one_world_apart` in `tests/save/test_sightings.py`).
2. `SaveWorldProvider` keeps, per world digest, the unlock states of the last `NOTICE_WINDOW_SAVES + 1` = 4 distinct saves it handed up, in memory, through the pure `delta.observe_progress`; a re-read of the same save adds nothing; a fifth distinct save drops the oldest; nothing is written and a new provider starts empty (`test-the_progress_window_holds_four_distinct_saves_and_forgets_on_restart` in `tests/surface/test_world_provider_memo.py`; the no-write sweep in `tests/surface/test_server.py` green and unedited).
3. The baseline is a declared, traced input: `advise_world` and `advise_world_and_record` take `progress_baseline: UnlockState | None = None`; tier 3 of a progress card renders the baseline snapshot's content digest and no path; the same (save, baseline) pair under `PYTHONHASHSEED=0` and `=1` gives byte-identical cards (`test-one_save_and_one_baseline_give_byte_identical_cards_in_two_processes` in `tests/advisor/test_world_advice.py`).
4. With no baseline the rule records `StepKind.INPUT_MISSING`, fires nothing, and the listing carries `progress_baseline` = `none`; the vocabulary is closed: `none`, `held`, `incomparable`. The word is a function of the baseline and the delta verdict, one arm per row: no baseline is `none`; `advanced` is `held`; `unchanged` is `held`; `incomparable` (which covers a baseline of another world and a missing catalog) is `incomparable`; `regressed` is `incomparable` (`test-the_listing_names_the_progress_baseline_from_a_closed_vocabulary` in `tests/surface/test_advice.py`, five rows). A world provider that is not a `ProgressBaselineProvider` hands baseline None, so the word is `none` (``test-a_world_provider_with_no_baseline_door_lists_none``). The page words `none` and `incomparable` inside the existing status line, id `advice-status`, and adds no element (`test-the_baseline_state_is_worded_in_the_existing_status_line` in `tests/surface/test_panel_advice.py`).
5. `progress.unlocked` fires at most one card; its subject key is the CURRENT snapshot's `digest`; ten schematics gained yield one card; tier 1 states the count gained and the count of recipes opened; tier 2 names at most `NAMED_SCHEMATICS` = 3 by quoted display label, then the count beyond, then `game phase changed` when flagged, never naming the phase (`test-ten_gained_schematics_yield_one_card_naming_three` in `tests/advisor/rules/` test-progress.py).
6. A `regressed` or `incomparable` delta records `StepKind.VERDICT_INDETERMINATE` and fires nothing (``test-a_regressed_or_incomparable_delta_fires_nothing``). The catalog is a declared input: `inputs_of` offers the rule `schematics.catalog()` (None when no source is given), both snapshots are built with it, and a None catalog therefore reads `incomparable` (``test-a_missing_catalog_records_incomparable_and_fires_nothing``).
7. Every progress card's tier 2 ENDS with the unvalidated-read clause, unconditionally. It is generated: `clockspeed.save.world.UNLOCK_READ_VALIDATED` is False, the advisor offers it as a declared input, the rule records it as a trace step, and the clause equals that step's tier-3 line (``test-tier2_ends_with_the_trace_generated_unvalidated_clause``; negative: no fixture warning makes it appear or vanish).
8. The rule id is in the closed `EVENT_RULES` set: its card follows every non-event card in `Advice.ranked` and `Advice.ranked_shown` after the CS-1401 interleave; the aging guard never promotes it at any deferral count; a pressed act leaves its deferral count at zero, because `advise_and_record` drops every `EVENT_RULES` card id from the `shown` order it hands `Ledger.reconcile`, so the ledger neither ages the card nor treats it as the top spot (the arm reads the count back through `Ledger.deferrals` after two pressed acts, and a mutant that passes the unfiltered order reddens it); it never holds the first place while another visible card exists (`test-an_event_card_is_last_and_is_never_promoted_by_aging` in `tests/advisor/test_ranking.py`).
9. `domain` is `plan`; `interleave_domains` sees no fifth key from it (`test-the_rule_is_filed_under_the_plan_domain` in `tests/advisor/rules/` test-progress.py).
10. Dismissing the card hides that card id only; a later purchase yields a new id; muting `progress.unlocked` through U-038's route hides the family and changes no ledger byte (`test-dismiss_hides_one_progress_card_and_mute_hides_the_family` in `tests/surface/test_advice_source.py`).
11. Lifetime: over saves S0..S4 of one synthetic world where S1 adds one schematic, the card fires on S1, S2 and S3 with one id, a re-read of S1 gives the same id and no second card, and S4 fires nothing; the card then completes silently - U-031's completed list does not name it (`test-a_progress_card_lives_three_distinct_saves_and_expires_silently` in `tests/surface/test_advice_source.py`).
12. Census: `EFFORT_BY_RULE["progress.unlocked"]` is `EffortClass.QUICK`; `tests/advisor/test_every_rule_fires.py` holds a firing and a silent fixture for it and its arms are green.

## CS-1433

### Filed 2026-11-24 by the session 161 wave 0 filing

Plan key: U-050. Class: product. Lane flag: false (not eligible). Planned minutes: 360 (4 parts (90, 90, 120, 60)).
Depends on: CS-1425 part 4 (U-030.4); CS-1398.5.
Wave: W47, W49, W50 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-050.2 in W49: `clockspeed/advisor/advise.py` 2/2; U-050.3 in W50: `clockspeed/advisor/ranking.py` 2/2, `tests/advisor/test_every_rule_fires.py` 2/2, `tests/advisor/test_plan_world.py` 1/2; U-050.4 in W50: `tests/advisor/test_plan_world.py` 2/2.
Write-list:
- U-050.1 (W47-G2-S2, 90 min): `clockspeed/advisor/rules/` `materials`, `tests/advisor/rules/` `test-materials`
- U-050.2 (W49-G2-S1, 90 min): `clockspeed/advisor/advise.py`, `tests/advisor/rules/` `test-materials`, `tests/advisor/test_display_name_keying.py`
- U-050.3 (W50-G1-S1, 120 min): `clockspeed/advisor/ranking.py`, `clockspeed/advisor/rules/__init__.py`, `tests/advisor/test_every_rule_fires.py`, `tests/advisor/rules/` `test-materials`, `tests/surface/test_schematic_source.py`, `tests/advisor/test_plan_world.py`, `tests/advisor/test_display_name_keying.py`, `tests/surface/test_advice_act.py`, `tests/surface/test_advice_source.py`
- U-050.4 (W50-G3-S1, 60 min): `tests/advisor/test_plan_world.py`

### Acceptance

Leaf section `## CS-NEW` (the allocated id) in `docs/item_notes/phase5.md`, heading `### Acceptance`. Every arm is in `tests/advisor/rules/` test-materials.py unless a file is named. "Rows" are `MaterialRow(item, cost, held, short)`: `item` a str, `cost` a Fraction, `held` and `short` an int and never a bool. `plan.materials.machines`, `.undecoded_entries` and `.unread_payloads` are an int and never a bool.

1. A hand-built world whose one row costs 240 and holds 180 yields ONE `plan.materials` card: tier 1 starts `Gather 60 more`, tier 2 contains `cost 240` and `the save holds 180`, tier 3 carries a computed step `short of <item key>` of 60. ``test-a_world_holding_180_of_a_240_cost_yields_one_card_naming_the_60_short``.
2. The adapter prices WHOLE machines: over `plan_world_registry()` (each build recipe costs one plate) a plan step of 240 machines and an inventory of 180 plates give `rows == (MaterialRow(PLAN_WORLD_PLATE, Fraction(240), 180, 60),)` and machines the int 240; a step of 479/2 machines also prices 240; a zero-machine step prices nothing; an item the inventory lacks is held 0. ``test-the_adapter_prices_whole_machines_against_the_held_total``, ``test-a_fractional_machine_count_rounds_up_and_a_zero_step_costs_nothing``.
3. Holding everything: every row's held at or above its cost and nothing unpriced yields no card, one `alternative-rejected` step, and the rule IS in `settled_rules` - also when stacks were excluded, because the held total only undercounts. ``test-a_world_holding_everything_settles_silent``, ``test-a_covered_cost_settles_even_over_an_incomplete_read``.
4. Exclusions are counted and named: a short world with excluded `(("count_unread", 1), ("item_absent", 2))`, 4 undecoded entries and 1 unread payload fires with tier 2 containing `held is a floor: 3 stack(s) excluded (count_unread 1, item_absent 2), 4 container entries undecoded, 1 payload(s) unread`, and the rule is NOT settled. The floor clause names ONLY the nonzero figures, in that fixed order, joined by a comma and a space; one arm per single figure pins the exact text: `held is a floor: 3 stack(s) excluded (count_unread 1, item_absent 2)`, `held is a floor: 4 container entries undecoded`, `held is a floor: 1 payload(s) unread`, each NOT settled. With all three figures zero tier 2 has no `floor` and the fired rule IS settled. ``test-excluded_and_undecoded_stacks_are_counted_and_named_in_tier_two``, ``test-a_single_nonzero_floor_figure_is_named_alone``, ``test-a_short_card_over_a_complete_read_settles``.
5. No ranked plan: status `no-ranked-plan` yields no card and one `verdict-indeterminate` step whose reason is `no ranked plan is on offer, so no build cost was priced`; the rule is not settled and reads no other `plan.materials.` input. ``test-no_ranked_plan_records_why_the_rule_is_silent``.
6. One card per world: with three items short the largest shortfall leads (ties by item key ascending) and tier 1 ends `and 2 other item(s) for the planned chain`; tier 3 has one computed step per cost item, covered ones at 0; the subject key is `plan-materials:<target keys sorted, joined by +>`, `target_milestone` is None, and the card id is equal across two worlds where a different item leads. ``test-the_worst_shortfall_leads_and_the_card_id_holds_when_the_leader_changes``, ``test-tier_three_lists_every_cost_item``.
7. Never a free machine: a step whose recipe names no modeled building, or whose building's `build_cost` is None, adds its recipe key to the unpriced tuple and charges nothing. Nothing short plus something unpriced yields no card and a `verdict-indeterminate` step (not settled); a short world with one unpriced recipe has tier 2 containing `1 planned recipe(s) have a machine with no build recipe and are not priced`. ``test-a_machine_with_no_build_recipe_is_unpriced_and_never_free``, ``test-an_unpriced_machine_keeps_a_covered_world_undecided``.
8. Scope wording: every fired tier 2 contains `machines only: extractors, belts, pipes, power and foundations are not priced`, `machines already built are priced again` and `held counts every inventory the save read`. ``test-tier_two_names_what_the_cost_and_the_held_total_leave_out``.
9. No float in any offered input, every offered name starts `plan.materials.`, each is sourced; an item with a usable display name reads quoted, one without reads by ClassName and records a rejected step. A cost item ABSENT from `registry.items` (a `RecipeIO.item_key` may name an item with no descriptor, `clockspeed/data/registry.py` lines 758-766) is named None by the adapter, reads by ClassName, records a rejected step, and `materials_inputs` and `inputs_of` do not raise. ``test-every_offered_input_is_exact_prefixed_and_sourced``, ``test-an_item_with_no_usable_name_reads_by_its_class_name``, ``test-a_cost_item_the_registry_has_no_descriptor_for_is_named_by_class_name_and_never_fatal``.
10. Refusals, each ending in a `rule-error` step and no card, the message naming the field and never a value: a status outside the three words; a row that is not a `MaterialRow`; a row whose short is not `max(0, ceil(cost) - held)`; rows not sorted by item key or holding one item twice; `item_names` keys that are not exactly the rows' items; a negative held; a bool or a float where an int is required (held, short, machines, the two counts). ``test-a_row_whose_short_disagrees_with_its_cost_and_held_is_a_rule_error``, ``test-unsorted_or_duplicated_rows_are_a_rule_error``, ``test-item_names_that_do_not_match_the_rows_are_a_rule_error``, ``test-a_negative_held_or_a_bool_where_an_int_is_required_is_a_rule_error``.
11. Composition: `inputs_of` on a ranked stated world whose badge cleared a rung offers all nine inputs with status `priced`; with no target, and on a routed (no-plan) world, it offers `plan.materials.status` alone reading `no-ranked-plan` and never calls `inventory_of`. ``test-inputs_of_prices_a_ranked_plan_against_the_world_inventory``, ``test-inputs_of_walks_no_inventory_without_a_ranked_plan``. A rename moves `plan.materials.item_names` and no other new input: `tests/advisor/test_display_name_keying.py::test_a_rename_on_a_stated_world_moves_its_name_input_alone` (adopt world 2 moved, redesign world 1).
12. Registration: `plan.materials` is registered in domain `plan`, `EFFORT_BY_RULE` reads MIDDLE, it fires with NO quantity and is not in `MAGNITUDE_RULES`; it has a firing fixture, a silent fixture that settles, and one return site `short` whose headline starts `Gather 60 more`. ``test-the_rule_is_registered_in_the_plan_domain_at_the_middle_effort_with_no_quantity``; `tests/advisor/test_every_rule_fires.py::test_every_registered_rule_has_a_firing_fixture`, `::test_the_recommendation_calls_are_pinned_to_the_fixture_count`; `tests/advisor/test_ranking.py::test_the_effort_table_names_no_rule_that_is_not_registered`.
13. End to end: `test-a_ranked_world_with_an_empty_inventory_serves_a_materials_card_beside_the_plan_card` in `tests/advisor/test_plan_world.py` (both rule ids, both domain `plan`) and ``test-the_materials_card_completes_once_the_world_holds_the_cost`` (second run over a model whose containers hold the cost: the card id is in `Advice.completed`).
14. Never without the plan card: a ranked plan whose badge cleared no rung (`plan.adopt` rejects it and returns no card, `clockspeed/advisor/rules/plan.py` lines 1179-1181) is offered as `plan.materials.status` alone reading `plan-not-recommended`; the rule yields no card and one `verdict-indeterminate` step whose reason is `the ranked plan cleared no strategy rung, so no build cost was priced`, is not settled, and `inventory_of` is never called. ``test-a_ranked_plan_that_cleared_no_rung_prices_nothing``, ``test-inputs_of_walks_no_inventory_for_a_plan_that_cleared_no_rung``.
15. The aging arms do not move (D37): `tests/surface/test_advice_aging.py` is byte-unchanged by this unit (`git diff --stat` over the unit's commits names no such path) and passes whole after part 3.
