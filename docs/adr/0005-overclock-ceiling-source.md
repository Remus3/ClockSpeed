# 0005 - S7: where the overclock clock ceiling comes from

## Status

`accepted` - 2026-08-13

Written by the slice that ran the probe, which correctly left it `proposed` because per
`CLAUDE.md` section 5 the producing agent does not grade its own output.

**Flipped to `accepted` by an adjudicator that did not run the probe.** That adjudication
independently re-derived every factual claim here against the live install and found zero
numeric discrepancies, then returned REVISE rather than ACCEPT for one reason: the fence had
a hole on its load-bearing side. Two amendments were required and are now applied - the
`log2( 2.5 )` bullet in the re-pitch list below, and the label marking the equation as
inferred rather than observed. The adjudicator also ran a strictly broader token sweep than
the probe did, including the bare forms `Shard` (108 hits across 9 files) and `ShardSlot`,
plus `GetSlotsForPowerShardType` and `mDefaultProductionShardSlotSize` which this document
does not name; all are bodiless declarations carrying no numeric, so the binary answer is
unchanged.

Two imprecisions found and left standing as harmless: the "10.6 MB" figure below is the
on-disk UTF-16 LE byte count rather than the decoded character count, and `mInventoryPotential`
is cited at the `UPROPERTY` line rather than the declaration line beneath it. Neither affects
a conclusion.

## Decision in one line

**The clock ceiling is NOT in `Headers.zip` - but `Headers.zip` gives the exact equation and
the exact field names, and following them recovers two of the three operands from the docs
data, leaving ONE unknown integer to pin.**

## Context

`docs/_archive/spike-report-s1-s2-s3-s7.md` section S7 answered S7 YES for the power
exponent and left the ceiling OPEN. Every one of the 62 entries in `en-US.json` that carries
`mMaxPotential` reports `1.000000`, and every one reports `mPotentialShardSlots` of `0`.
Reading `mMaxPotential` as the clock ceiling would cap every solve at 100 percent and look
correct while being wrong on every overclocked building in the world.

That spike named three candidate sources in priority order:

- **(a) `Headers.zip`** - the first-party C++ headers shipped in the local install, free to
  read, authoritative, and the obvious next place to look.
- **(b) the save file** - if the per-building potential is stored there.
- **(c) an explicitly named, version-pinned constant** stated to be NOT from the docs data,
  re-checked every game patch, carrying a drift-guard entry. Named as the fallback.

This ADR settles which one the project takes. The temptation it exists to foreclose is
specific: writing `2.5` or `250 percent` into the solver from general knowledge of the game
and calling it measured. That number is widely known. It was not, before this probe,
measured from anything on this machine, and a widely-known number is still a magic number.

## Evidence

All values below were observed on a single read-only probe run on 2026-08-13 against the
local install at game build `++FactoryGame+rel-main-anniversary-2026-CL-502094`, resolved at
runtime by `scripts/verify_env.py` `resolve_game_dir()` via the Steam library index. The
install path is not recorded here and is never hardcoded. Nothing under the install was
created, modified or deleted. The zip was opened read-only and its members were decoded in
memory; nothing was extracted into this repository.

`CommunityResources/Headers.zip`, 1,949,168 bytes, 1,144 members, all 1,144 decoded with
zero decode failures. Extension census: 1,112 `.h`, 24 `.cs`, 7 `.uplugin`, 1 `.csproj`.

### BINARY ANSWER: NO. The ceiling number is not in `Headers.zip`.

The mechanism is structural, not accidental, and it generalizes: every property involved is
declared `UPROPERTY( EditDefaultsOnly, ... )`. In Unreal that means the value is authored in
the editor and lives in a data asset, never in C++. The zip additionally ships declarations
only - 1,112 headers and no `.cpp` - so no initializer and no function body is present
either. **`Headers.zip` is a schema oracle. It is not, and cannot be, a value oracle for any
balance number.**

### What `Headers.zip` DID give - the equation and the field names

Four declarations, cited by identifier, type and member path, with no publisher source
reproduced:

| Identifier | Member path inside the zip | Type | In-header numeric default |
|---|---|---|---|
| `mMaxPotential` | `Source/FactoryGame/Public/Buildables/FGBuildableFactory.h:621` | `float` | none |
| `mPotentialShardSlots` | `Source/FactoryGame/Public/Buildables/FGBuildableFactory.h:629` | `int32` | none |
| `mDefaultPotentialShardSlots` | `Source/FactoryGame/Public/FGBuildableSubsystem.h:615` | `int32` | none |
| `mExtraPotential` | `Source/FactoryGame/Public/Resources/FGPowerShardDescriptor.h:32` | `float` | none |

Their documented roles, paraphrased rather than quoted: `mMaxPotential` is the default
maximum on the buildable **not accounting for installed power shards** - which independently
confirms the S7 reading that the docs-data `1.000000` is the un-sharded base.
`mPotentialShardSlots` is the per-building shard slot count and is gated by
`meta = (EditCondition = "mOverridePotentialShardSlots")`, so a docs-data value of `0`
alongside `mOverridePotentialShardSlots` of `False` means **no override**, not zero slots.
`mDefaultPotentialShardSlots` is the subsystem-wide default used by every buildable without
an override. `mExtraPotential` is the potential a single shard of that type unlocks.

Two accessors confirm the shape without exposing arithmetic:
`AFGBuildableFactory::GetMaxPotential()` at `FGBuildableFactory.h:240` returns the un-sharded
base, while `GetCurrentMaxPotential()` at `FGBuildableFactory.h:244` and the protected
`GetCurrentMaxPotentialForType( EPowerShardType, float minValue, float maxValue, float
boostPerShardMultiplier = 1.0f )` at `FGBuildableFactory.h:363` are separate calls that
account for shards. The only numeric literal in any of them is the `1.0f` default argument
for the production-boost multiplier, which is a different mechanic.

The recovered equation, per building - INFERRED from declarations and signatures, never
executed or observed. Note in particular that `GetCurrentMaxPotentialForType` carries
`minValue` and `maxValue` parameters that this equation silently drops:

```
slots   = mPotentialShardSlots            if mOverridePotentialShardSlots
        = mDefaultPotentialShardSlots     otherwise
ceiling = mMaxPotential + slots * mExtraPotential( the PST_Overclock shard )
```

### Following those field names into the docs data - two of three operands, measured

`mExtraPotential` is a field name this project would not have known to look for without the
header. It is present in `en-US.json`. The `FGPowerShardDescriptor` group holds exactly two
entries, and both were read this run:

| ClassName | `mPowerShardType` | `mExtraPotential` | `mExtraProductionBoost` |
|---|---|---|---|
| `Desc_CrystalShard_C` | `PST_Overclock` | `0.500000` | `0.000000` |
| `Desc_WAT1_C` | `PST_ProductionBoost` | `0.000000` | `1.000000` |

Sweeping every entry in `en-US.json` this run: `mMaxPotential` is `1.000000` on all 62,
`mMinPotential` is `0.010000` on all 62, `mPotentialShardSlots` is `0` on all 62, and
`mOverridePotentialShardSlots` is `False` on all 62. **Every overclockable building takes the
subsystem default; not one overrides it.**

So two operands are measured and one is missing:

- `mMaxPotential` = `1.000000` - measured, per building, in the docs data.
- `mExtraPotential` = `0.500000` for the `PST_Overclock` shard - measured, in the docs data.
- `mDefaultPotentialShardSlots` = **UNKNOWN.** Not in `Headers.zip` (declared, no default)
  and not in `en-US.json`: `0` raw occurrences of `mDefaultPotentialShardSlots` and `0` of
  `DefaultPotentialShard` across the whole decoded 10.6 MB document, and `0` of the 114
  `NativeClass` groups is a subsystem class at all. The subsystem is simply not exported to
  the docs file.

**The ceiling number is not in the file, and this ADR does not supply it.** With the two
measured operands the unknown collapses from a magic float to a single small non-negative
integer. It is not filled in here, because filling it in from general knowledge of the game
is precisely the failure this ADR exists to prevent.

### The one `2.5` in the entire zip, and why it is not evidence

A whole-zip sweep for `2.5` or `250` on a line also containing `overclock`, `potential`,
`shard` or `clockspeed` returned **exactly one hit**: a documentation comment attached to
`mPowerConsumptionExponent` at `FGBuildableFactory.h:521`, illustrating the power formula
with a worked example at 2.5x overclock.

It is not a declaration, and it is not self-consistent with the shipped data: the example is
worked with an exponent of 1.6, which the S7 spike measured as the value carried by
**fixed-draw infrastructure**, while the overclockable production buildings carry 1.321929.
A comment illustrating a formula with the wrong building class's exponent is a stale
illustration. Citing it as a measurement of the ceiling would be citing a code comment as
ground truth, which is what `CONVENTIONS.md` section 15 forbids. It is recorded here only so
the next reader who finds it does not mistake it for the answer.

### Tokens that returned ZERO hits, and what was swept

Per `CONVENTIONS.md` section 15.1, an empty grep is a claim about the pattern, so the
patterns are stated. Two independent sweeps ran: over all 1,144 member NAMES, and over the
decoded CONTENT of all 1,144 members, both case-insensitive.

**Zero hits in member NAMES** (8 of 11 requested tokens): `mMaxPotential`, `MaxPotential`,
`PotentialShard`, `mPotentialShardSlots`, `mCurrentPotential`,
`mMaxPotentialIncreasePerCrystal`, `DefaultMaxPotential`, `mPotential`. Only three requested
tokens matched a filename: `OverClock` and `Overclock` both matched
`Source/FactoryGame/Public/Unlocks/FGUnlockBuildOverclock.h` (a 22-line file that unlocks the
ability and carries no number), and `PowerShard` matched
`Source/FactoryGame/Public/Resources/FGPowerShardDescriptor.h`.

**Zero hits in member CONTENT:** `mMaxPotentialIncreasePerCrystal` and `DefaultMaxPotential`.
These two do not exist anywhere in the zip under any casing.

**Hardening sweeps, added because two zero-hit tokens are a weak claim on their own** - all
case-insensitive over all content, all returning zero: `PerCrystal`, `IncreasePer`,
`SlotCount`, `NumShard`, `PotentialIncrease`, `MAX_POTENTIAL`, `MaxClock`, `ClockSpeed`,
`MAX_OVERCLOCK`, `kMaxPotential`.

**Zero hits in `en-US.json`:** `mDefaultPotentialShardSlots` and `DefaultPotentialShard`, as
raw case-insensitive substrings of the fully decoded document, and `mCurrentPotential` and
`mPendingPotential` as keys.

The tokens that did hit, for completeness: `mMaxPotential` 2 occurrences in 1 file,
`MaxPotential` 5 in 1, `PotentialShard` 4 in 2, `mPotentialShardSlots` 1 in 1, `OverClock`
124 in 13, `mCurrentPotential` 5 in 3, `PowerShard` 46 in 6, `mPotential` 5 in 4.

### Option (b), the save - settled by the header, not deferred

The `UPROPERTY` specifiers answer this directly and it no longer needs a phase-4 experiment
to rule out:

- `mCurrentPotential` at `FGBuildableFactory.h:670` and `mPendingPotential` at
  `FGBuildableFactory.h:609` are both `SaveGame`.
- `mMaxPotential` at `FGBuildableFactory.h:621`, `mPotentialShardSlots` at
  `FGBuildableFactory.h:629` and
  `mDefaultPotentialShardSlots` at `FGBuildableSubsystem.h:615` are `EditDefaultsOnly` and
  **not** `SaveGame`.

**A save therefore records what a building IS clocked at, never what it CAN be clocked at.**
Option (b) is refuted as a source of the ceiling.

One narrow use survives: `mInventoryPotential` at `FGBuildableFactory.h:663` is
`EditDefaultsOnly, SaveGame`, so the potential inventory component of a built overclockable
building is serialized. If its serialized form carries its slot count, that is a direct
measurement of the missing operand from a save. **This is UNVERIFIED.** The header proves the
component is saved; it does not prove the slot count survives serialization, and no save was
parsed for this ADR. It is a phase-4 experiment, not a result.

## Consequences

**The project adopts option (c), narrowed by the option (a) finding**, with option (b) held
as the scheduled route to retire it.

Concretely, three parts:

1. **Both measured operands come from the docs data at extraction time and are never
   hardcoded.** `mMaxPotential` is read per building class off the normalized registry, and
   `mExtraPotential` is read off the `PST_Overclock` entry in the `FGPowerShardDescriptor`
   group. No literal `1.0` and no literal `0.5` in the solver, for the same reason S7 banned
   a literal `1.321929`: a balance patch moves them and a literal turns that into silently
   wrong advice instead of a red build.
2. **Exactly one version-pinned constant is written down**, and it is the slot count, not the
   ceiling:
   - Name: `OVERCLOCK_POTENTIAL_SHARD_SLOTS`
   - Type: a non-negative `int`
   - Home: `clockspeed/data/version.py`, which `CLAUDE.md` section 4 already names as the
     owner of the game build pin. The constant is version-pinned, so it belongs beside the
     pin and nowhere else. That file does not exist yet; a different slice owns
     `clockspeed/` and this ADR only specifies.
   - It is **NOT from the docs data.** It corresponds to `mDefaultPotentialShardSlots` on the
     buildable subsystem, which is absent from `en-US.json` entirely, and it must carry a
     comment saying so.
   - It **must be re-checked on every game patch**, alongside the build pin.
   - It **needs a `tools/drift_guard.py` entry.** The guard cannot check the value itself -
     there is no source to check it against, which is the whole reason it is a constant. What
     the guard must assert is the surrounding invariants that would silently invalidate it:
     that `mOverridePotentialShardSlots` is still `False` on every entry (the moment one
     building overrides, a single global constant is wrong for that building), that
     `mExtraPotential` on the `PST_Overclock` shard has not changed, that `mMaxPotential` is
     unchanged across the entry set, and that the `FGPowerShardDescriptor` group still holds
     exactly the two shard types. Any of those moving goes red.
3. **The constant ships with no measured value.** This ADR does not supply one and no slice
   may invent one. Until the slot count is measured, the ceiling above `mMaxPotential` is
   UNKNOWN, and per non-negotiable 7 unknown content is flagged and skipped, never silently
   wrong. The interim behaviour is: solve at or below `mMaxPotential`, and where a solve
   would benefit from overclocking, say the ceiling is unmeasured rather than assume one.
   A ceiling silently defaulted to 1.0 and a ceiling silently defaulted to 2.5 are the same
   class of bug.

**What must NOT be re-pitched:**

- **Do not go back into `Headers.zip` looking for this number, or for any other balance
  number.** The reason is structural and stated above: `EditDefaultsOnly` puts the value in a
  data asset, and the zip ships headers with no `.cpp`. A future search will find the same
  declarations and the same absence. If a later probe wants a balance constant, the asset
  path is the place to look, and that path carries the `CONVENTIONS.md` section 14 license
  gate already recorded in `docs/GATED.md`.
- **Do not cite the `2.5` in the comment at `FGBuildableFactory.h:521` as the ceiling.** It is
  an illustration of the power formula, worked with the wrong building class's exponent.
- **Do not write `2.5`, `250`, or `250 percent` into the solver, a doc, a test or a fixture
  as a measured value.** It is not measured. If it later turns out to be right, it will be
  right because something on this machine was read, and the ADR that records that reading
  supersedes this one.
- **Do not read `mMaxPotential` as the achievable ceiling.** It is the un-sharded base and
  the header says so in as many words. This is the trap S7 flagged and the header confirms.
- **Do not derive the ceiling from `mPowerConsumptionExponent`.** The overclockable
  production buildings carry `1.321929`, and `2 ** 1.321929 = 2.500002` - the exponent sits
  within rounding of `log2( 2.5 )`. That is a relation between two balance values, not a
  measurement of the ceiling, and it is not a source. The same applies inverted: do not take
  an assumed `2.5` back through the equation above to conclude `slots = ( 2.5 - 1.0 ) / 0.5
  = 3`. The slot count is measured or it is UNKNOWN.
  This fence was added by adjudication, not by the probe. It is here because it is the one
  route to the number that a future agent could take while sincerely believing it had
  complied with every other bullet in this list - the arithmetic uses only values shipped in
  the docs data, so it FEELS derived rather than assumed. It is not.
- **Do not conflate the two shard mechanics.** `PST_Overclock` / `mExtraPotential` raises the
  clock. `PST_ProductionBoost` / `mExtraProductionBoost` on `Desc_WAT1_C` is a different
  mechanic with its own exponent (`mProductionBoostPowerConsumptionExponent`) and its own
  multiplier (`mProductionShardBoostMultiplier`, which is not uniform: 54 entries at
  `1.000000`, 4 at `0.500000`, 4 at `0.250000` this run). A solver that adds them together is
  wrong twice.
- **Do not treat `mPotentialShardSlots = 0` as zero slots.** It means the override is off.
  The `EditCondition` on the declaration is the proof.
- **Do not add a second constant.** If the ceiling needs more than one written-down number,
  the equation was misread.

**LICENSE position - stated plainly.**

`Headers.zip` is publisher-owned first-party material. Every header in it carries a Coffee
Stain Studios all-rights-reserved copyright notice: no grant, no permissive license, nothing
that would make it vendorable. `CONVENTIONS.md` section 14 covers exactly this case and its
rule is the operative one - techniques and protocol facts are not copyrightable, source is.

- **Reading it locally, at runtime, from the install, to learn a field name and a number is
  fine.** That is what this probe did, read-only, with nothing extracted into the repo.
- **Vendoring, copying, extracting into the working tree, committing, or quoting a block of
  it is not fine**, and no claimed purpose changes that. Not into `tests/`, not into a
  fixture directory, not into `docs/`, not "just the one file".

**What from this investigation MAY be committed:** the identifiers (`mMaxPotential`,
`mPotentialShardSlots`, `mDefaultPotentialShardSlots`, `mExtraPotential`,
`mOverridePotentialShardSlots`, `mPowerShardType`), the member paths and line numbers cited
above as provenance, the paraphrased semantics, the equation, and the measured numeric values
`1.000000` and `0.500000`. Those are facts about a data format, of the same kind as every
field name already recorded in ADR 0003 and the S7 spike report.

**What MAY NOT be committed:** `Headers.zip` itself, any member of it, any extracted copy,
any verbatim excerpt of its source beyond the short declaration fragments already quoted
here, and any slice of `en-US.json`. This ADR is deliberately written so that removing the
game install does not make it wrong and does not make it a redistribution of anything.

**Honest limits of this ADR.**

- The ceiling value is **not determined**. One integer operand is missing and no source on
  this machine has yet been found that carries it.
- Whether a save exposes the potential-inventory slot count is **unverified**. No save was
  parsed for this ADR.
- Everything here is measured at one game build,
  `++FactoryGame+rel-main-anniversary-2026-CL-502094`, on one install, on one run. The field
  names are unlikely to move; the numbers are exactly what a balance patch moves.
- No test was written and no code was changed by this slice. This ADR specifies; another
  slice implements.
