# 0003 - S4: resource-node actors in the save

## Status

`accepted` - 2026-08-13

## Decision in one line

**The save carries resource-node actors WITH world coordinates - but not what those nodes
contain.** Geometry: yes. Semantics: no.

## Context

`BOOTSTRAP.md` section 3 marks S4 as "the one that matters" and section 8.3 makes the
whole node-data strategy hang off it. The acceptance test stated there is specific: parse
a save, enumerate actor class names, grep for resource-node classes, and check for a
transform on each. Class names alone are necessary but not sufficient - a class name with
no transform gives no siting advice.

The pinned reference world is an ideal target precisely because nothing is built in it:
anything reported as a built object is either a level-baked actor or a bug.

Two obstacles were hit and are worth recording, because both will recur:

1. The body is chunked and zlib-compressed and had to be framed before anything could be
   read. Settled: chunks are framed by magic `0x9E2A83C1` followed by marker `0x22222222`,
   an int64 max chunk size of 131072, an int8 compression algorithm of 3 (zlib), then the
   compressed and uncompressed sizes each written twice. The decompressed body opens with
   an int64 length. This closes the remaining unmeasured part of S5.
2. **The actor header layout is save-version dependent.** A first pass using one fixed
   layout produced 626 class-name matches and zero valid transforms on current saves while
   working on an old one. The transform block sits at a different offset per version.

## Evidence

Measured against the pinned reference world at the current build, with a normalized
quaternion, a plausible scale and in-map coordinates as the validity test:

- **626 node actors, 626 with a valid transform.** Zero failures.
- Class breakdown: 459 `BP_ResourceNode_C`, 118 `BP_FrackingSatellite_C`,
  31 `BP_ResourceNodeGeyser_C`, 17 `BP_FrackingCore_C`, 1 `BP_ResourceDeposit_C`.
- Transform block after the instance-name string: `float rot[4]`, `float pos[3]`,
  `float scale[3]`. Quaternion norm measures 1.0000. Coordinates fall inside the map
  extent.
- Offset of that block after the instance name is **+8 on save versions 52 and 60, +4 on
  save version 36**. Version dispatch is confirmed as a day-one requirement, exactly as
  `BOOTSTRAP.md` section 2.4 predicted.

**The negative result, which matters as much as the positive one:**

- Each node instance name occurs **exactly once** in the decompressed body - in the
  object-header section only. There is no second occurrence, so these actors carry **no
  serialized property payload**.
- `mPurity`, `mResourceNodeType`, `mResourceClass`, `EResourcePurity` and
  `mExtractResourceNode` occur **zero times** in any save examined, across three worlds and
  four game builds.

The mechanism is ordinary Unreal behavior: a save stores deltas from level defaults. A
resource node's resource type and purity are level-asset defaults that never change, so
they are never written to the save.

## Consequences

- **`BOOTSTRAP.md` section 8.3 step 1 is now known to be incomplete.** It reads "if the
  save carries resource-node actors with transforms, done - zero external dependency". That
  is true for placement and false for the data D1 actually needs. Positions without
  resource type and purity cannot order a node-claim list. Section 8.3 must be updated.
- The node semantics layer needs the asset-extraction path (section 8.3 step 2), which
  carries the `CONVENTIONS.md` section 14 license gate. That gate is now a real, scheduled
  obligation rather than a contingency, and it is recorded in `docs/GATED.md`.
- **The cost of that extraction is bounded by ADR 0002.** Because placement is map-fixed
  and not seed-derived, the resulting table is a one-time artifact per game build, shared
  by every world. It is not per-world work.
- Section 8.3 step 3 still stands: do not lift a community-compiled node dataset.
- Interim position is section 8.3 step 4: **D1 ships degraded**, restricted to nodes the
  player has already scanned or discovered, and it says so loudly rather than shipping
  quiet partial coverage. `mScannableResourcesPairs` in the save (see ADR 0004) is the
  input that makes even the degraded mode possible.
- The save reader must dispatch on save version from day one. A single-layout parser is
  wrong on the operator's own library, which spans four builds and three header versions.
- Node geometry is free and exact. Whatever solves the semantics problem, positions never
  need to come from an external dataset.
