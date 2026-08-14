# 0004 - S6: unlock-state recoverability from the save

## Status

`accepted` - 2026-08-13

## Decision in one line

**Unlock state is recoverable from the save. The advisor can ship.**

## Context

`BOOTSTRAP.md` section 3 states the stakes plainly: the advisor cannot ship without this,
because everything in section 5 is gated on knowing what the player has unlocked. A rule
that cannot tell what is unlocked can only recommend things the player may be unable to
build, which violates the section 5.4 precondition invariant.

The stated fallback was a manual unlock-state entry surface as a stopgap, which would be a
permanent tax on the operator - exactly the cost the whole project exists to avoid.

**One methodological trap had to be avoided.** `BOOTSTRAP.md` section 2.3 warns that the
pinned reference world has onboarding ACTIVE and that its early unlock and schematic state
will look unusual, so S6 must not be settled on it. That warning proved correct and load-
bearing: settling S6 on the pinned world alone would have produced the wrong answer.

## Evidence

Two worlds compared - the pinned onboarding world and the most-progressed world in the
local library.

**Mature world - unlock state is fully present:**

- `mPurchasedSchematics` present.
- **246 distinct `/Schematics/` paths**, including `Schematic_Alternate_*` entries, which
  is the alt-recipe purchase state pillar 2 is built on.
- **360 distinct `/Recipes/` paths**, including `Recipe_Alternate_*`.
- `mCurrentGamePhase`, `mTargetGamePhase` and `mGamePhaseCosts` - milestone and phase
  progression.
- `mUnlockedResearchTrees`, `mResearchManager`, `mRecipeManager`, `mSchematicManager`.
- `mScannableResourcesPairs` and `mScannableObjectData` - the scanned-resource state, which
  is also the input that keeps degraded-mode D1 viable under ADR 0003.
- Feature-level unlocks as discrete booleans: `mIsBlueprintsUnlocked`,
  `mIsBuildingOverclockUnlocked`, `mIsBuildingEfficiencyUnlocked`, `mIsMapUnlocked`,
  `mIsCustomizerUnlocked`. Overclock availability in particular is a direct precondition
  for power and clock advice.

**Pinned onboarding world - the control, and the warning made concrete:**

- 14 unlock-related property names against the mature world's 30.
- `mPurchasedSchematics`: absent. Distinct `/Schematics/` paths: zero.
- Only 11 recipe paths, all starting recipes, plus `mHasGivenStartingRecipes` and
  `mCurrentOnboardingStep`.

The difference is not corruption and not a parser failure. It is the same
default-not-serialized mechanism found in ADR 0003: arrays that are still empty are not
written.

## Consequences

- S6 passes. **No manual unlock-entry stopgap is needed** and none should be built.
- Pillar 2 can constrain by what is genuinely unlocked rather than by what exists in the
  data, which is what `BOOTSTRAP.md` section 4 requires.
- **The unlock reader must treat an absent array as "empty", never as "missing" and never
  as an error.** This is the single most important engineering consequence. A reader that
  assumes presence will either crash on a fresh world or silently report a mature world's
  state for a new one. Both failures are severe: the second produces confident wrong
  advice, which section 9's invariant forbids outright.
- **Every unlock-reading test must run against BOTH shapes** - a fresh onboarding world and
  a mature world. A fixture built only from a mature save will stay green through exactly
  the defect above. This is the `CONVENTIONS.md` section 7.2 class "fixtures built parallel
  to the implementation stay green through the real defect", and it is now a known,
  specific risk rather than a general caution.
- Feature booleans are read as unlock preconditions directly. A rule requiring overclock
  declares `mIsBuildingOverclockUnlocked` as a required unlock and cannot fire without it.
- The pinned reference world remains the right first parse target for the save reader, but
  it is the WRONG fixture for unlock logic. Both worlds are needed, and the mature world
  should be snapshotted into the gitignored corpus for that purpose.
