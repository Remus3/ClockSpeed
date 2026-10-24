# 0016 - The unlock arrays' carriers, and their serialized grammar

## Status

`proposed` - 2026-09-05.

Written by the slice that measured it, which under `CLAUDE.md` section 5 may not also
grade it. An adjudicator that did not produce this measurement moves it to `accepted`.

---

## Context

ADR 0004 settled that unlock state IS recoverable from a save, and named the fields by
scanning a decompressed body for property-name strings. It deliberately did not measure
how those fields serialize. `clockspeed/save/world.py::UnlockState` says so on `UnlockState`
itself, and the load carries `WARN_UNLOCK_GRAMMAR_UNMEASURED` for that reason.

CS-913 was filed on the premise that the published unlock state is empty BECAUSE that
grammar was never measured. **That premise is wrong, and the code says so before any save
is opened.** `_read_unlocks` at `clockspeed/save/world.py::_read_unlocks` takes zero arguments - no
bytes, no `ObjectTable`, no `PropertyMap` - and its body returns
`EMPTY_UNLOCK_STATE` plus one warning unconditionally. Its only call site, in
`clockspeed/save/world.py::load_world_from_bytes`, is argument-free too. Nothing in scope could vary by save, so every world publishes
`is_empty` identically. The pinned development world's genuine emptiness is a coincidence
rather than the mechanism, and `/api/world` is innocent: it would publish real state the
moment the producer returned any.

Meanwhile the decoder those bytes would go through already exists.
`objects.read_properties` at `clockspeed/save/objects.py::read_properties` is a full tagged-property
reader. Grepping `read_properties|parse_properties` across `clockspeed/` outside
`objects.py` returns exactly two hits - `world.py:44` and `world.py:50` - and both are
docstring prose. **The decoder has no production caller.**

So the remaining unknown was narrow: which object carries each unlock array, and what
grammar does each use. This ADR answers that, and one measurement in the answer
contradicts a field this project has already committed to in a shipped type.

**The subject and the control.** ADR 0004's methodological warning is load-bearing and it
was obeyed. The subject is the most-progressed world in the local library, re-identified
by measurement this run rather than from a stale note - the local library changes whenever
the operator plays, and it has grown since ADR 0004. A second, low-progress world on the
same version pair serves as the control that discriminates "written" from "absent". The
pinned development world is the third, and it turned out to be unusable for this purpose
for a reason recorded below.

**Method, stated so the limits travel with the result.** Each save was copied out of the
save directory and the copy was read; nothing was written to the save directory or the
game install. The copies were deleted. Every figure below comes from
`objects.parse_body` followed by `objects.read_properties` and, for struct elements,
`objects.decode_struct_interior`. No count that identifies a world, no world name, no
filename and no unlocked content path is recorded here - only grammar.

---

## Decision

**Record the carriers and the grammar as measured, and re-specify CS-913 around them.**

### The carriers

| Property | Carrier type path |
|---|---|
| `mPurchasedSchematics` | `/Game/FactoryGame/Schematics/Progression/BP_SchematicManager.BP_SchematicManager_C` |
| `mAvailableRecipes` | `/Script/FactoryGame.FGRecipeManager` |
| `mCurrentGamePhase`, `mTargetGamePhase`, `mGamePhaseCosts` | `/Game/FactoryGame/Schematics/Progression/BP_GamePhaseManager.BP_GamePhaseManager_C` |
| `mUnlockedResearchTrees` | `/Game/FactoryGame/Recipes/Research/BP_ResearchManager.BP_ResearchManager_C` |
| `mScannableResourcesPairs`, `mScannableObjectData`, the five feature booleans | `/Game/FactoryGame/Unlocks/BP_UnlockSubsystem.BP_UnlockSubsystem_C` |
| `mHasGivenStartingRecipes` | `/Game/FactoryGame/-Shared/Blueprint/BP_GameState.BP_GameState_C` |

Each occurred exactly once per world. **The recipe set is `mAvailableRecipes`, not
`mUnlockedRecipes`** - the second name decoded on no carrier - and it sits on a different
actor from the schematics. The game state carries none of the arrays; it carries object
references naming the managers, so the managers are reachable from it without a class
scan.

### The grammar

- `mPurchasedSchematics`, `mAvailableRecipes`, `mAvailableCustomizationRecipes` and
  `mUnlockedResearchTrees` are each an **`ArrayProperty` whose element word is
  `ObjectProperty`**. Every element decoded, bounded by the self-delimiting shape - the
  falsifiable one of the three in `objects.ELEMENT_SHAPES`, not a derived partition. Each
  element's value is the two-string reference pair, and **the payload is an object
  reference to a GAME ASSET, not a struct interior and not a bare name**: the level
  reference is empty and the object path is a `/Game/FactoryGame/...` asset path. **Not
  one element joined a record's `instance_name`.** The unlock reader therefore matches
  these against the registry's asset paths, never against the record table.
- `mCurrentGamePhase` and `mTargetGamePhase` are **top-level `ObjectProperty` tags on
  `BP_GamePhaseManager_C`** - they appear in `PropertyResult.references`, which carries
  only that word. They are **NOT `IntProperty`, NOT on a game-state actor and NOT inside a
  struct.** Each names a `GP_*` asset. Across both readable worlds, **no `Phase`-named
  property anywhere in either record table decoded to an integer at all.**
- `mGamePhaseCosts`, `mScannableResourcesPairs` and `mScannableObjectData` are
  `ArrayProperty` whose element word is `StructProperty`, with inner struct words
  `PhaseCost`, `ScannableResourcePair` and `ScannableObjectData`. The container decoder
  bounds these elements and deliberately leaves them unread;
  `objects.decode_struct_interior` reads them.
- **`PhaseCost` interiors read, and carry `gamePhase` and `cost`.** `gamePhase` decodes to
  a one-string value - a THIRD representation of the phase, alongside the asset reference
  above - and `cost` is an `ArrayProperty` of `StructProperty` with inner word
  `ItemAmount`.
- **`ScannableResourcePair` and `ScannableObjectData` interiors read as EMPTY tag lists.**
  Every element of both arrays was exactly nine bytes, byte-identical to an `FString`
  spelling the terminator name, in both readable worlds. The elements are bounded by the
  self-delimiting shape and consume the tag's declared region exactly, so there is nowhere
  inside the region for content this reading missed.
- The five feature booleans are **`BoolProperty` tags on `BP_UnlockSubsystem_C`**, whose
  value rides in the tag rather than in a payload.

### The emptiness mechanism, confirmed independently

Confirmed from the code, before and independently of any save being opened, at the three
lines cited in the Context. **The published unlock state is empty because the producer is
argument-free and returns a constant - not because the grammar was unmeasured.** The
warning it emits is honest about the state being empty and inaccurate about the reason.

---

## Consequences

**`UnlockState.current_game_phase: int | None` is the wrong shape and must change.**
`clockspeed/save/world.py::UnlockState` declares an integer phase index. The save carries an asset
reference. An integer field can only be filled here by inventing one - deriving an index
from an asset path is exactly the fabrication `UnlockState`'s own docstring forbids. This
is the finding with a shipped consequence, and it is why CS-913 cannot be closed by
wiring the existing decoder into the existing type.

**The pinned development world cannot exercise the unlock reader at all, and neither can
any save on its version pair.** Every record in every `(14, 60)` save in the local library
decoded ZERO property tags; each carries `unparsed-property-payload`, which is the
already-known `(14, 60)` payload limit `world.py` records. All six carrier classes are
present in the record table and every one of them is unreadable. So the world this project
uses as its first parse target is the one world that can say nothing about unlock state,
and ADR 0004's control - reached by string scan, which does not care about the payload
grammar - is not reproducible through the decoder. **A low-progress world on a readable
pair is the control the reader's tests need instead.**

**The absent-array rule from ADR 0004 now has decoder-level evidence, and it extends to
the booleans.** On the low-progress control, `mPurchasedSchematics`, `mAvailableRecipes`
and `mUnlockedResearchTrees` are present but short, while `mScannableObjectData`,
`mAvailableCustomizationRecipes`, `mGamePhaseCosts` and **all five feature booleans are
absent outright**. An absent `BoolProperty` means FALSE, exactly as an absent array means
empty. A reader that treats an absent overclock flag as unknown, or as an error, will
refuse to advise on a world that simply has not unlocked it yet.

**The scanned-resource arrays yield a COUNT and nothing else.** Their interiors carry no
tagged properties, so which resources were scanned is not recoverable this way. ADR 0003's
degraded node mode D1 names `mScannableResourcesPairs` as its input; on this measurement
that input supplies a cardinality, not an identity. The same reader read `PhaseCost`
interiors in the same save on the same code path, so this is a fact about the data rather
than a reader failure - but it does NOT establish that the game stores the identity
nowhere, only that it is not in these tag lists. That is its own follow-up and should not
be rounded up into either conclusion.

**Four of the six carriers do not resolve against the shipped property mapping**, and the
reader must not gate on resolution. `FGRecipeManager` resolves; every `BP_*` carrier is
flagged `unresolved-schema` and decodes fully anyway, which is the independence
`read_properties` documents. A reader that required a resolved schema would recover the
recipe set and nothing else.

**A container's elements are absent from `PropertyResult.references`.** That population
counts top-level `ObjectProperty` TAGS, and every unlock reference is an array ELEMENT, so
the reference join and its diagnostics see none of them. A consumer reading unlock
references from `references` gets an empty answer and no warning. The values are in
`ContainerValue.elements`.

**Any test for this must build a synthetic `PropertyMap`.** `read_properties` took a
non-optional one when this was written, sourced from `usmap`, which requires the game
install. **CI has no install and neither does a fresh clone**, so a library-backed test is
not portable. AMENDED 2026-09-09 by CS-960: that signature now accepts an absent mapping
and decodes either way, so it is no longer what forces the synthetic map. The conclusion
is unchanged and now rests on the portability clause alone, plus the standing fixture
rule below.
`tests/save/test_properties.py::_synthetic_map` already builds a map from `usmap`'s own public types
with no file, and that is the pattern. It also satisfies the standing rule that fixtures
are hand-authored synthetic registries, never slices of real data.

**What a future run needs in order to reproduce this, stated plainly.** It needs a mature
world and a low-progress world on a readable version pair, plus a game install for the
property mapping. `.gitignore` reserves `/corpus/` and ADR 0004 recommended snapshotting a
mature world into it - **`corpus/` does not exist on disk, so this measurement has no
repeatable local home and the next run must re-identify its subject by measurement, as
this one did.** Creating that corpus is an OPERATOR action against a personal-data-bearing
artifact, not an agent action: a save file may not be committed, attached or placed in a
fixture directory, and an agent may not put one anywhere on the operator's behalf.

**What must be revisited if a premise changes.** The grammar above is a property of the
game build pinned in `clockspeed/data/version.py`. The local library holds saves on older
pairs whose bodies carry no `mCurrentGamePhase` string at all, which is direct evidence
that these names move between builds. A build change re-opens this ADR. Separately, the
subject world was identified by measurement rather than by name - the pinned development
world is INFERRED to be the `(14, 60)` group from its onboarding shape and from matching
ADR 0004's control, and that inference was not confirmed against a name, because a world
name may not be written into a tracked file.

---

## Amendment - what a `PhaseCost` amount means (CS-1340)

Measured 2026-10-23 (session 151) by the slice that wired the reader, which
under `CLAUDE.md` section 5 may not also grade it. Every save was read through
a WORK COPY made by `clockspeed/save/workdir.py`; nothing was written to the
save directory or the game install, and every copy but the pinned one was
discarded after its read. Worlds were told apart by the digest of the header's
world token and are named here by role only. Names and counts only.

**The library at measurement.** 43 saves in three worlds: the pinned
development world, 31 saves, every one `(14, 60)`, its pinned work copy the
newest save, file mtime 2026-10-18T16:11:14Z; a second world, 7 saves, all
`(14, 52)`; and a third world, 5 saves - one `(14, 52)`, one `(13, 42)` and
three `(10, 36)`. Every save of all three loaded through
`clockspeed/save/world.py::load_world_from_bytes`, and every
`BP_GamePhaseManager_C` payload read whole with no undecoded tag.

**The pinned development world writes no `mGamePhaseCosts` at all, on any of
its 31 saves.** Its phase manager carries exactly two tags,
`mCurrentGamePhase` and `mTargetGamePhase`, naming
`GP_Project_Assembly_Phase_0` and `_1` on the 3 oldest saves and
`GP_Project_Assembly_Phase_1` and `_2` on the 28 after its phase advanced. The
array is absent on both sides of that advance, so this world cannot say
whether an amount is a total or a remainder - only that a 1.0-native world at
this progress does not write it. The second world, at
`GP_Project_Assembly_Phase_0`, writes none either.

**The meaning was measured on the third world, the only one that writes the
array.** All 5 of its saves carry one array of 4 `PhaseCost` elements whose
decoded values are identical across all 5 saves and all three version pairs.
`gamePhase` is a `ByteProperty` naming an `EGamePhase` member - an `EGP_`
token - and `cost` an array of `ItemAmount` structs, each an `ObjectProperty`
`ItemClass` naming a `/Game/FactoryGame/...` asset with an empty level half,
and an `IntProperty` `Amount`.

| `gamePhase` | lines | amounts, in file order |
|---|---|---|
| `EGP_MidGame` | 1 | 0 |
| `EGP_LateGame` | 3 | 0, 0, 0 |
| `EGP_EndGame` | 3 | 2500, 500, 100 |
| `EGP_FoodCourt` | 4 | 4000, 4000, 1000, 1000 |

The items are `Desc_SpaceElevatorPart_1_C` through `_9_C`. The world's own
phase on its `(13, 42)` and `(10, 36)` saves is the legacy `mGamePhase`, a
`ByteProperty` reading `EGP_LateGame`; its `(14, 52)` save writes
`mCurrentGamePhase` naming `GP_Project_Assembly_Phase_2` instead.

**THE AMOUNT IS WHAT THE WORLD STILL OWES, NOT THE PHASE'S TOTAL.** Within one
save the zeros fall exactly on the phases up to and including the world's own
phase token, and every line past it is positive. Read as totals, a phase the
world reached would cost nothing on every one of its lines - four lines and
three distinct items listed at amount zero - so the total reading is refuted
by the save itself.

**WHAT WAS NOT MEASURED, AND IT IS THE RESIDUAL.** No save in the library holds
a phase PART paid, so "decremented as items are delivered" and "the full
figure until the phase is reached, then zero" are not told apart: both agree
with every observation above. The reader publishes the value as what is still
owed, which is exact on every measured save; under the second reading a part
paid phase would be overstated. A save holding a part paid phase re-opens
this, and the pinned development world cannot supply one, because it writes no
array.

**WHAT SHIPS ON IT.** `clockspeed/save/world.py::PHASE_COST_CARRIER` keys the
reader on the class this table already records, and
`clockspeed/save/world.py::PhaseCostReading` publishes each phase's lines as
exact Fractions, a zero kept. A world that writes no array publishes NO TABLE -
`WorldModel.phase_costs` is None, never an empty or zero reading - and so does
a world with two carriers of it. `clockspeed/progress/phases.py::SavePhaseCosts`
is the shipped phase-cost source under this meaning: it drops a paid line and
publishes a phase paid in full as an empty entry. On the pinned development
world, and on every 1.0-native save measured, `phase_costs_available` therefore
reads False. Whether a 1.0 world's phase costs are recoverable elsewhere - from
the shipped `GP_*` phase assets rather than the save - is unmeasured.
`tests/save/test_phase_costs.py` and `tests/progress/test_save_phase_source.py`
grade it on synthetic fixtures only.

---

## Amendment - the space elevator's input inventory carrier (CS-1348)

Measured 2026-10-23 (session 151) on the same work copies, by the same method
and with the same limits as the CS-1340 amendment above, by the slice that
wired the reader. Names and counts only.

**The carrier.** The elevator is one `Build_SpaceElevator_C` actor - exactly
one on each of the pinned development world's 28 newer saves (none on its 3
oldest) and on each of the third world's 5; the second world has none. Its
top-level `ObjectProperty` `mInputInventory` resolves through the published
reference join to exactly one component record of class
`FGInventoryComponent` on every one of those 33 saves; on
the four whose type paths were printed - the pinned work copy and three of the
third world's - that component's own parent path resolves back to the
elevator too, and its type path is `/Script/FactoryGame.FGInventoryComponent`.
It carries three tags:

- `mInventoryStacks`, an array of `InventoryStack` structs, 6 elements on
  every measured save, each an `Item` (`InventoryItem`) and a `NumItems`
  (`IntProperty`) - the spelling `clockspeed/audit/inventory.py` already reads;
- `mArbitrarySlotSizes`, present on every measured save - on the pinned work
  copy, the one save whose values were printed, 6 `IntProperty` elements,
  every one 0;
- `mAllowedItemDescriptors`, 6 `ObjectProperty` elements, every one an EMPTY
  reference.

On the pinned work copy the elevator's other inventory reference,
`mInventoryPotential`, lands on a second inventory component carrying 3 slot
sizes; it is not the input carrier.

| Property | Carrier type path |
|---|---|
| `mInputInventory` | `/Game/FactoryGame/Buildable/Factory/SpaceElevator/Build_SpaceElevator.Build_SpaceElevator_C` |

**Every measured slot is empty.** On all 33 elevator-bearing saves every one
of the 6 stacks is an empty slot - an empty item class and a count of 0. So
the carrier and its grammar are measured, and a NON-EMPTY reading is not: no
save in the library holds an item in the elevator's input. Whether an item
sitting there is already netted out of the `mGamePhaseCosts` amount the
CS-1340 amendment measured is unmeasured too.

**What ships on it.** `clockspeed/save/world.py::ELEVATOR_INPUT_CARRIER` keys
the reader on the class this table records, and
`clockspeed/save/world.py::ElevatorInput` publishes the input inventory as
exact Fraction counts by item ClassName. An elevator whose slots are all empty
publishes an EMPTY reading - nothing delivered, a reading - and None is kept
for no reading: no elevator, two of them, an input reference that does not land
on exactly one record, or a carrier with one stack that does not read.

**The seam, taken by this slice and left for an adjudicator to rule.** The
save layer publishes the carrier, because the inventory model lives in
`clockspeed/audit/` and that layer is not below `clockspeed/progress/`.
`clockspeed/progress/phases.py::SavePhaseCosts` reads it from the world model
and publishes it as `PhaseCostTable.delivered`, keyed by every item the
table's entries owe - so a cost item the elevator holds none of reads an exact
zero - plus any item it does hold. `tests/save/test_elevator_input.py` and
`tests/progress/test_save_phase_source.py` grade it on synthetic fixtures
only.
