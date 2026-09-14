# 0019 - The map underlay, and purity closed by declaration

## Status

`accepted` - 2026-09-13. Adjudicated by an agent that produced none of the work it ruled on.

Relates to `0003` - this ADR does not supersede it. 0003's measurement stands and was
correct. What changes is the REASON: 0003 recorded an absence measured by sampling, and
this ADR records the same absence measured by declaration, which is a stronger result and
closes a question 0003 had to leave open.

## Decision in one line

**The dashboard ships a schematic ground plane drawn from save-exact placements and NO
underlay raster; node purity is not obtainable from any sanctioned source and is replaced
by an honest substitute rather than a derivation.**

## Context

The operator asked for a game map rendered under the node overlay, node icons carrying
both type and purity, and outlined water regions for extractors. A read-only spike this
session measured all three against the install and the live save.

**Purity is structurally absent, not merely unobserved.** The install ships
`CommunityResources/Headers.zip` - 1144 publisher-authored C++ headers sitting beside the
`Docs` file this project already reads, and nothing in this tree had ever read it.
`FGResourceNode.h` declares:

```
UPROPERTY(EditInstanceOnly, Category = "Resources")
TEnumAsByte<EResourcePurity> mPurity;
```

There is no `SaveGame` specifier. A property without `SaveGame` is structurally incapable
of being serialized into a save on any build, which is a different and far stronger claim
than "we did not find it". `mResourceClass` and `mResourceNodeType` are the same. A
re-grep of the live save for 23 spellings, in both ASCII and UTF-16LE, plus every member
of the enum, returned zero on every one. The class name does not carry the resource as a
fallback: 459 of 1065 nodes share `BP_ResourceNode_C`. Deriving purity from a miner's rate
fails as well - `mItemsPerCycle` and `mExtractCycleTime` measure zero and are machine-side
properties in any case.

One exception is real and worth a slice of its own: `mResourceDepositTableIndex` IS a
`SaveGame` property and is present on 440 records, matching the 440 `BP_ResourceDeposit_C`
deposits exactly. Deposits carry a resource index; the table that index points into lives
in the assets.

**There is no map image to extract.** `AFGMinimapCaptureActor` derives from
`ASceneCapture2D`: the in-game map is rendered live, not shipped as a texture.
`FGMapAreaTexture` carries `mUpperLeftWorld`, `mWorldToMapScale` and `mDataWidth` - which
is precisely the world-to-pixel transform a correct registration needs - but it lives
inside `.ucas`.

**The install ships no callable Oodle Data codec.** The pak index is unencrypted and all
13,576 entries were enumerated in pure stdlib, but 6,993 of them are Oodle-compressed. The
only shipped DLL is OodleNetwork, a different codec. Oodle Data is proprietary RAD and
Epic code.

**Water volumes are level geometry.** `FGWaterVolume` declares `mCanPlaceExtractor`, which
is exactly the flag the requirement wants, but it is `EditDefaultsOnly` and there are zero
water-volume type paths in the save.

**One thing came free.** `mFogOfWarRawData` in the SAVE decodes to exactly 1024x1024 bytes,
proved structurally rather than assumed - reading 1048576 bytes lands exactly on the next
property tag. That is a map-shaped raster of the player's own explored world, inside a file
this project already parses and is already licensed to read.

## Decision

**1. The map ships with no underlay.** Node and built placements are drawn at exact save
coordinates, shape-coded by class. The view extent is labelled as THIS WORLD'S PLACEMENT
BOUNDS and not as the map extent, because `WorldBounds` (`clockspeed/audit/placement.py`)
bounds placements and therefore moves whenever the operator builds. Rendering the same save
twice yields byte-identical geometry.

**2. The fog-of-war raster is a separately toggled layer, and only after its registration
is PROVED.** The transform is fitted, not read, and non-negotiable 7 forbids being silently
wrong. The proof has three parts and all three are required:

- **Held-out containment.** Every built placement sits where the player has stood, so its
  world position must land on a REVEALED texel. Fit on a random half of built placements,
  assert on the held-out half. Hundreds of samples, falsifiable, and independent of any
  asset.
- **A potency control, mandatory.** A deliberately wrong transform - Y sign flipped, scale
  off by ten per cent - must FAIL that same assertion. Without the control the arm is blind
  to its own subject.
- **Cross-save invariance.** The same constants must satisfy containment on a second save
  and on an autosave. Constants fitted per world are disqualifying.

If the sign-flip control does not redden, the layer ships only behind a visible
`registration unverified` flag. If cross-save invariance fails, the layer does not ship and
the no-underlay plane is the permanent answer.

**3. Purity is replaced, not approximated.** All nodes plot unlabelled and shape-coded by
class, which is the one thing actually known. Only scanned nodes and the sixteen
`mExtractableResource`-linked ones carry a resource label. The existing warning's wording
is reused verbatim - "unmeasured rather than unremarkable". Purity may be recorded as an
OPERATOR ANNOTATION keyed by node instance name, and an annotation is never presented as a
measurement.

**4. Oodle Data adoption stays GATED at `docs/GATED.md` CS-G01** pending a written
`CONVENTIONS.md` section 14 verdict that reads the LICENSE, the copyright line AND the
provenance claim. The reverse-engineered Kraken family could not be confirmed from this
machine as permissively licensed; section 14's rule that the absence of a LICENSE file is
not permission makes that unresolved, not cleared.

**5. Screen capture is permitted as a local calibration instrument and never as shipped
data.** The underlay is PRESENTATION, not advice - nothing is computed, ranked or explained
from it - so the determinism rule does not by itself bar a captured image. It loses on two
other grounds: the pixels are publisher-owned and may never be committed, and the artifact
is not reproducible from the save, so the product would depend on an unreproducible manual
step. A local, uncommitted, one-shot capture whose only output is a pass or fail on the
fitted transform is allowed.

## Consequences

- The operator's stated purity requirement is NOT met and is not going to be. The honest
  substitute above is what ships. This is recorded so it is not re-attempted as though it
  were an unsolved problem rather than a closed one.
- `Headers.zip` is a sanctioned, already-on-disk, authoritative source for property names,
  enum members and `SaveGame` specifiers, and it was unread for the whole life of this
  project. One query against it would have answered 0003. Indexing it is now its own work
  item, and every future "is this field in the save" question is a lookup rather than a
  grep and a guess.
- The common-mode risk is named rather than hidden: all of these options assume
  `mFogOfWarRawData` is registered to the same world-to-pixel space as `FGMapAreaTexture`.
  The spike proved the array's SIZE structurally, not its registration. Only reading the
  shipped constants would settle it and that path is gated - so the held-out containment
  oracle is the cheapest available attack on the assumption, and it needs no asset at all.

## Do not re-pitch

- A screen-captured or OBS-captured map underlay as SHIPPED data.
- An underlay registered to `WorldBounds`, which moves whenever the operator builds.
- A fitted transform accepted on visual plausibility without the negative control.
- Any Oodle-dependent extraction slice before CS-G01 rules in writing.
- Purity derived from a miner's output rate, from the node class name, or from any
  heuristic presented to the operator as a measurement.
- Any lifted map tile, table, dataset or image from a wiki or community source, official or
  not. CS-485 is the licence verdict and `CLAUDE.md` section 7 is the fence.
