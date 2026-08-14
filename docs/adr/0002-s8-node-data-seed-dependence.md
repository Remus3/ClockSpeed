# 0002 - S8: seed dependence of resource-node data

## Status

`accepted` - 2026-08-13

## Context

The game's session menu exposes a "Show Seed" control, which proves a per-world seed
exists. What that seed actually varies was unknown. The question is load-bearing for the
data layer, not cosmetic:

- If node placement or purity is seed-derived, then node data is a property of the WORLD,
  a static node table is wrong for any given world, and `BOOTSTRAP.md` section 8.3 steps 2
  and 3 are invalid. The save becomes the only correct source, and S4 stops being merely
  important and becomes load-bearing with no fallback.
- If node data is fixed across worlds, node data is a property of the MAP, the section 8.3
  fallback survives, and S4 has an alternative if it fails.

Because the answer gates the fallback, `BOOTSTRAP.md` section 8.3 step 0 requires S8 to be
answered before committing to any S4 fallback path.

Available evidence on this machine: a local save library containing several save files.
Grouping them by filename is unsound - autosaves rotate and timestamped saves of one world
look like distinct worlds to a filename heuristic, and an early grouping attempt in this
session produced exactly that error, inflating three worlds into six. The correct identity
key is the 22-character base64url world token in the save header (`BOOTSTRAP.md` section
2.4), which is filename-independent.

Comparing worlds on different game builds confounds seed variation with patch variation,
so a same-build pair is required for a clean test.

## Decision

**Resource-node placement is NOT seed-dependent. It is a fixed property of the map.**

Measured, keyed on the header world token rather than the filename:

- The local library contains exactly **3 distinct worlds** by token.
- Exactly one game build (`463028`) holds saves from **two different world tokens**, which
  is the only clean same-build cross-world pair available.
- Both worlds yield **626 resource-node actors** across the same five classes with the
  same per-class counts.
- The `(class, x, y, z)` sets are **identical**: 626 shared, zero present in one and absent
  from the other, in either direction.

A separate cross-build comparison of the same node sets differs only in small z values on
a minority of nodes, consistent with terrain adjustment between patches rather than with
different placement - the x and y coordinates match.

## Consequences

- `BOOTSTRAP.md` section 8.3 steps 2 and 3 remain valid. A static node table is a
  legitimate data source because the map is fixed.
- S4 is therefore **not load-bearing**. It has a real fallback. See ADR 0003, which finds
  S4 succeeds for geometry regardless.
- Any node table extracted once is valid for every world on the same game build, so the
  extraction is a one-time cost per patch, not a per-world cost.
- **Stated limit, deliberately not overclaimed:** this measures PLACEMENT. Purity was not
  measured directly, because purity turns out not to be serialized in the save at all
  (ADR 0003). Purity is expected to be fixed by the same mechanism - it is a level-asset
  default that never changes - but that is inference from the mechanism, not measurement.
  If a future probe finds per-world purity variation, this ADR's decision still holds for
  placement and a new ADR supersedes only the purity inference.
- The sample is two worlds at one build. It is a clean test of the question asked, but it
  is two worlds. A third world on the same build would strengthen it and costs nothing but
  the operator creating one.
- What the seed actually varies remains unknown and is now known not to matter for node
  data. It is not worth further investigation unless a downstream feature depends on it.
