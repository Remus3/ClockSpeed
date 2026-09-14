# 0020 - Shipped-asset extraction, and where each of the four requirements is recoverable from

## Status

`accepted` - filed 2026-09-13 under CS-1040.

Relates to `0003` and to `0019`; supersedes neither. 0003 measured node purity's absence by
SAMPLING a save. 0019 ruled on what the dashboard therefore ships - no underlay raster, an
honest substitute for purity, Oodle gated - and this ADR does not re-rule any of that. What
this ADR adds is the ASSET-SIDE evidence underneath those rulings, and the instrument that
produced it: `clockspeed/data/assets.py`, which turns the shipped C++ headers into a
queryable index so the next "is this field in the save" question is a LOOKUP.

## Decision in one line

**The install's `CommunityResources/Headers.zip` is adopted as the project's
declaration-grade oracle for reflected property names, types and `UPROPERTY` specifiers;
of the operator's four requirements exactly one - building extent - turns out to be
RECOVERABLE from a source this project already reads.**

## Context

Unreal serializes a property into a save if and only if its `UPROPERTY` macro carries the
`SaveGame` specifier. The install has always shipped the publisher's own C++ headers beside
the `Docs` file `clockspeed/data/docs_extract.py` reads, and nothing in this tree had ever
opened them. That archive is plain deflate - every entry, no exception - so it needs
nothing but the standard library and touches none of the Oodle question that 0019 gated.

Measured this session by the new module against the pinned build: 1112 headers parsed, 32
non-header entries flagged and skipped, 8024 reflected property declarations, 993 of them
carrying `SaveGame`, and 227 reflected enumerations. The lookup is three-valued on purpose
- declared with `SaveGame`, declared without it, or NOT DECLARED AT ALL - because
collapsing the third into "no" is exactly the confident wrong answer about unknown game
content that non-negotiable 7 forbids, and exactly what a grep does.

A save-side control run accompanied every verdict below, on the most recent save of the
pinned development world, counting tokens in the decompressed body. The control is
load-bearing: `mResourcesLeft` returned 794 hits and `ResourceNode` 1483, so a zero
elsewhere is a measurement rather than a broken probe.

## Decision

### 1. Node purity - NOT RECOVERABLE, and the reason is stronger than 0003's

`FGResourceNode.h` declares `mPurity` as `EditInstanceOnly`, with no `SaveGame` specifier.
A property without it is structurally incapable of reaching a save on any build, which
settles by DECLARATION what 0003 could only bound by sampling.

The index also surfaces something a grep of that header would have made worse rather than
better, and this is the single clearest argument for having it. The same class declares
`TEnumAsByte<EResourcePurity> mPurityOverride`, and that one IS `SaveGame, Replicated`,
defaulting to `RP_MAX`. A future reader grepping the archive for `Purity` beside `SaveGame`
hits it and concludes 0019 was wrong. It does not reopen anything: the field is an
OVERRIDE, unset in a vanilla world, and the save-side count for it is 0 against the control
above. Even set, it would carry what an author overrode purity TO and not what the node is.

### 2. Building extent - RECOVERABLE, from a file this project already reads

The extent requirement is the one with a clean answer, and it needs no new source and no
gate. `FGBuildable.h` declares `TArray<FFGClearanceData> mClearanceData` as
`EditDefaultsOnly`, so it is a CLASS DEFAULT rather than per-instance state - the save-side
count is 0, as the declaration predicts. Class defaults are exactly what the shipped `Docs`
file publishes, and `mClearanceData` is present there on 501 buildable classes across 66
groups, carrying a full `ClearanceBox` with `Min`, `Max` and a `RelativeTransform`.

So building extent is: the per-class box from `Docs`, transformed by the per-instance
placement the save already gives. Both halves are already inside this project's sanctioned
reach. The parsing of that blob is follow-on work, not this slice.

### 3. The map underlay - 0019's ruling stands; here is the asset-side evidence under it

0019 decided the map ships with no underlay raster and that a fog-of-war layer is gated
behind a proved registration. Two header facts sharpen the second half of that.

`mFogOfWarRawData` in `FGMapManager.h` is declared `UPROPERTY( SaveGame )` - so 0019's
structural proof that the array is in the save is now also a declaration, and the save-side
count is 1.

The sharper fact runs the other way. `mUpperLeftWorld` and `mWorldToMapScale` in
`FGMapAreaTexture.h`, the two constants a correct registration needs, carry **no
`UPROPERTY` macro at all**, and that class overrides no `Serialize`, `PostLoad` or
`PostInitProperties`. An unreflected member is not serialized into a cooked asset either.
The two constants therefore live in the compiled binary, not in any `.uasset` - so even a
cleared Oodle gate would not hand them over. 0019's decision to FIT the transform and prove
it by held-out containment is not a workaround for a gated path; it is the only path.

### 4. Water region geometry - NOT RECOVERABLE from any currently sanctioned source

`FGWaterVolume.h` declares `mCanPlaceExtractor` - the exact flag the requirement wants -
as `EditDefaultsOnly`, and the whole class declares zero `SaveGame` properties. Its shape
is inherited volume brush geometry, which is level data rather than a reflected member, so
no header carries it and the `Docs` file ships no water-volume group at all.

One refinement on 0019, offered as a correction rather than a contradiction: the save is
not entirely silent. It carries three references to a single named level actor,
`FGWaterVolume30_0`, reached as an object reference from a built extractor. That is a
POINTER to the one volume the operator has built in, by name, with no geometry and no
enumeration of the world's other water regions. It is enough to say "this extractor sits in
that volume" and nothing more; it cannot answer "where may an extractor go".

The geometry itself is cooked level data and therefore sits behind the Oodle question
`docs/GATED.md` CS-G01 holds. **Nothing in this slice touches that gate**, and no
Oodle-dependent work starts before it rules in writing.

### 5. The index is the deliverable, and it is regenerated rather than committed

`clockspeed/data/assets.py` opens the archive read-only, never passes any path under the
install to a writing call, and writes its index only to the gitignored `data/` directory
via an atomic replace. On a machine with no game it returns a REASON and no exception, so
the whole suite runs where the game is absent -
`tests/data/test_assets.py::test_the_extraction_reads_only_and_skips_cleanly_with_no_install`
is the arm that holds all three claims, and it measures the read-only claim with a
recording spy that carries its own potency control.

Two defects in the scan were found by auditing the generated index against the live
archive rather than by any assertion, and both are recorded here because both were live
rather than hypothetical. A commented-out declaration was being indexed as a live one -
one of them a `SaveGame` property inside a block comment, which is the FALSE TRUE this
module must never produce - and the `final` specifier defeated the owner scan, leaving
nineteen properties, five of them `SaveGame`, owned by no type. Both now have their own
arm. A residual of four properties in one deprecated plugin class still resolves to an
empty owner and is recorded in the module rather than chased, because the widening that
would capture it would also make a forward declaration an owner.

## Consequences

- **"Is this field in the save" is now a lookup with a citable declaration.** Any future
  claim of that shape that is made from a grep instead should be treated as unverified.
- **The purity requirement stays closed.** 0019 is the ruling; this ADR removes the last
  loose thread by naming the `SaveGame` field that a later grep would otherwise have
  mistaken for a reopening.
- **Building extent moves from unknown to a parsing task.** The follow-on is a `Docs`-side
  `mClearanceData` blob parser in `clockspeed/data/blobs.py`'s family, keyed by buildable
  class - no new source, no gate, and the registry seam is where it belongs.
- **Water geometry is recorded as gated, not as unstarted.** It has no answer under the
  present rules, and the only path to one runs through CS-G01.
- **The archive is a build-pinned artifact like the `Docs` file.** A game update can change
  a specifier, and a stale committed index would be a lie with a timestamp on it. That is
  why the index is generated into `data/` on demand and never tracked.
- **What is NOT claimed.** The index reads declarations, not the engine. It says a property
  is eligible for serialization, not that any particular save contains it - a `SaveGame`
  property equal to its class default is commonly written as nothing at all, which is
  precisely why `mPurityOverride` counts zero. Presence still has to be measured.

## Do not re-pitch

- Purity derived, defaulted, or inferred from `mPurityOverride`. It is an override, it is
  unset, and it would not answer the question even when set.
- Re-measuring a "is this field in the save" question by grepping a save when the headers
  declare it. Sampling is the weaker instrument and is now the redundant one.
- Committing the generated index, or any extracted header text, into the repository.
- Lifting a water-region or node dataset from a wiki or community source in place of the
  gated path. `CLAUDE.md` section 7 and CS-485 are the fence.
- Any Oodle-dependent extraction of level geometry or map textures before CS-G01 rules.
