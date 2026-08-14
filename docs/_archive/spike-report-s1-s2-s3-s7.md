# Spike report - S1, S2, S3, S7 (docs data layer)

**Date of probe run: 2026-08-13. Phase 1, session 1.**
Target: `CommunityResources\Docs\en-US.json` in the local Satisfactory install,
game build `++FactoryGame+rel-main-anniversary-2026-CL-502094` (CL 502094).

All numbers below were observed on THIS run. Nothing is carried forward from a prior
measurement and nothing is estimated. All probes were read-only: nothing under the game
install was created, modified or deleted. No game data was copied into this repository;
the probe scripts live in a scratch directory outside the repo. The excerpts quoted below
are the minimum needed to pin down a grammar that downstream code must parse verbatim.

Non-ASCII source strings found in the game data are referred to by codepoint, never
reproduced, so this file stays 7-bit ASCII.

---

## S1 - encoding of `en-US.json`

**Assumption as stated (BOOTSTRAP section 3):** "`en-US.json` is UTF-16 LE with a BOM."
BOOTSTRAP adds a hint: `io.json` at 5,181,010 bytes against the family's roughly 10.64 MB
"is what a UTF-8 sibling among UTF-16 files looks like".

**Method.** Opened each file in binary, read the first 4 bytes, and classified strictly
from the byte pattern (BOM first, then null-placement inference). Then confirmed by
attempting a strict decode under `utf-16`, `utf-16-le`, `utf-8-sig` and `utf-8`, and
separately by decoding the whole 10.6 MB file and handing it to `json.loads`, which
succeeded. Then classified all 55 files in the directory by BOM.

**Raw evidence.**

```
docs dir entries: 55   json entries: 55   non-json entries: []
size min=5181010  max=10754312  median=10641892
files under 8 MB: [('io.json', 5181010)]

en-US.json  size=10640180  first 4 bytes = FF FE 5B 00
            first 16 bytes = b'\xff\xfe[\x00\r\x00\n\x00\t\x00{\x00\r\x00\n\x00'
            decode utf-16    -> OK
            decode utf-8     -> FAIL (0xff at position 0 is not a valid start byte)

io.json     size=5181010   first 4 bytes = 5B 0D 0A 09
            first 16 bytes = b'[\r\n\t{\r\n\t\t"Native'
            decode utf-8     -> OK
            decode utf-16    -> "OK" but yields mojibake

BOM census over all 55 files:
  UTF-16 LE + BOM   54
  UTF-8  / no BOM    1   (io.json, 5181010 bytes)
```

**BINARY ANSWER: YES.** `en-US.json` is UTF-16 LE with a BOM (`FF FE`, then `5B 00` =
`[`). BOOTSTRAP S1 is confirmed as stated.

**Per-file encodings measured:**

| File | Bytes | Encoding |
|---|---|---|
| `en-US.json` | 10,640,180 | UTF-16 LE with BOM |
| `en-GB.json` | 10,633,658 | UTF-16 LE with BOM |
| `de.json` | 10,678,564 | UTF-16 LE with BOM |
| `ja.json` | 10,472,338 | UTF-16 LE with BOM |
| `zh-Hans.json` | 10,433,152 | UTF-16 LE with BOM |
| `io.json` | 5,181,010 | UTF-8, no BOM |

**Must the encoding be sniffed per file at read time? YES - the family is MIXED, 54 of 55
against 1.** The BOOTSTRAP hint about `io.json` was correct and the measurement confirms
it rather than merely being consistent with it.

**Engineering consequence for the data layer.**

- Clockspeed only ever reads `en-US.json`, so the reader could hardcode `utf-16`. Do not.
  Sniff, because the cost is four bytes and the failure mode of not sniffing is a silent
  garbage parse on any locale swap.
- **Sniff on the BOM bytes, never by trial decode.** Measured trap: Python's `utf-16`
  codec decodes the UTF-8 `io.json` WITHOUT raising - it returns mojibake. A
  try-decode-and-fall-back sniffer therefore reports success on the wrong encoding. Only
  the leading-bytes test is sound. `utf-8` decoding of a UTF-16 file does fail loudly, so
  the failure is asymmetric and a naive sniffer ordered UTF-16-first is silently wrong.
- Read the file as bytes and decode explicitly. Do not rely on `open(..., encoding=...)`
  defaults, and do not use `utf-16-le` for a BOM-bearing file - that leaves a U+FEFF as
  the first character of the decoded text. Use `utf-16` (BOM-consuming) or strip the BOM.
- The 10.6 MB on disk is about 5.3 million characters; a whole-file decode plus
  `json.loads` completes without incident and is the simplest correct approach for the
  one-shot extractor.

---

## S2 - top-level structure and the real field names

**Assumption as stated (BOOTSTRAP section 3):** "The docs file is a JSON array of
`{NativeClass, Classes[]}` groups, with recipes carrying ingredient/product/duration/
produced-in fields and descriptors carrying display name, form, energy and sink-point
values."

**Method.** Decoded and parsed the whole file, then enumerated the top-level container
type and length, the distinct key-sets of every group, the `NativeClass` value of every
group with its `Classes` length, and dumped every key of one representative entry per
class of interest. Then swept all 2,868 entries for key presence per field.

**Raw evidence.**

```
top-level python type : list
top-level length      : 114
distinct group keysets: {('Classes', 'NativeClass'): 114}   <- all 114 groups, same 2 keys
group 0 NativeClass   : "/Script/CoreUObject.Class'/Script/FactoryGame.FGResourceDescriptor'"
TOTAL entries across all groups: 2868
distinct ClassName values: 2868   (ClassName is unique document-wide; 0 collisions)
entries lacking a ClassName key: 0
entries carrying FullName: 1552   (FullName is NOT universal)
distinct key names across the whole document: 988
```

Group sizes for the groups the data layer cares about, this run:

| NativeClass (short) | Entries | Keys per entry |
|---|---|---|
| `FGRecipe` | 872 | 13 |
| `FGCustomizationRecipe` | 106 | 13 |
| `FGBuildingDescriptor` | 547 | 30 |
| `FGSchematic` | 574 | 23 |
| `FGItemDescriptor` | 122 | 30 |
| `FGResourceDescriptor` | 13 | 34 |
| `FGBuildableManufacturer` | 8 | 95 |
| `FGBuildableManufacturerVariablePower` | 3 | 103 |
| `FGBuildableResourceExtractor` | 4 | 98 |
| `FGBuildableGeneratorFuel` | 3 | 99 |

**BINARY ANSWER: YES, the structure matches** - the file is a JSON array of exactly 114
`{NativeClass, Classes[]}` groups and nothing else, and recipes do carry ingredient,
product, duration and produced-in fields. **Two sub-claims of the assumption are wrong in
detail and are called out below.**

### Real schema - `FGRecipe`, exactly 13 keys, verbatim

```
ClassName
FullName
mDisplayName
mIngredients
mProduct
mManufacturingMenuPriority
mManufactoringDuration
mManualManufacturingMultiplier
mProducedIn
mGameplayTags
mRelevantEvents
mVariablePowerConsumptionConstant
mVariablePowerConsumptionFactor
```

Note the spelling: **`mManufactoringDuration`** (the game data misspells "Manufacturing"
here) sits alongside the correctly spelled `mManufacturingMenuPriority` in the SAME entry.
Downstream code must use the misspelled key verbatim. Also note there is no
`mProducedInBuildings` or similar - the field is `mProducedIn`, singular.

**Every value on every `FGRecipe` key is a Python `str`.** Measured over all 872 entries:
durations, priorities, multipliers and power factors are all strings such as
`'2.000000'`, never JSON numbers. Parse them; do not assume numeric types anywhere in the
document.

Duration distribution this run: 27 distinct values of `mManufactoringDuration`, most
common `'1.000000'` (565 entries), then `'6.000000'` (58), `'12.000000'` (48).

### Real schema - descriptor entries, verbatim key names

The relevant fields on `FGItemDescriptor` / `FGResourceDescriptor`:

```
ClassName                mDisplayName             mDescription
mAbbreviatedDisplayName  mStackSize               mCachedStackSize
mEnergyValue             mRadioactiveDecay        mForm
mGasType                 mResourceSinkPoints      mFluidColor / mGasColor
```

`FGResourceDescriptor` adds raw-resource-only fields: `mDecalSize`, `mPingColor`,
`mCollectSpeedMultiplier`, `mManualMiningAudioName`.

Field coverage measured across the whole document:

| Field | Entries carrying it | Groups carrying it |
|---|---|---|
| `mDisplayName` | 2848 | 99 |
| `mDescription` | 1870 | 97 |
| `mForm` | 750 | 13 |
| `mEnergyValue` | 750 | 13 |
| `mStackSize` / `mCachedStackSize` | 750 | 13 |
| `mResourceSinkPoints` | 191 | 11 |
| `mPowerConsumption` | 68 | 38 |

`mForm` value histogram over the 750 form-bearing entries this run:
`RF_INVALID` 555, `RF_SOLID` 180, `RF_LIQUID` 10, `RF_GAS` 5.

### Two ways the assumption is wrong in detail

1. **Building descriptors carry NO display name.** All 547 `FGBuildingDescriptor`
   entries have `mDisplayName == ""` (measured: 547 of 547 empty). The human-readable
   building name lives on the `FGBuildable*` entry instead - for example
   `FGBuildableManufacturer` / `Build_ConstructorMk1_C` has
   `mDisplayName = "Constructor"`. A normalizer that reads building names from
   `FGBuildingDescriptor` will produce 547 nameless buildings and pass its own tests.
2. **Sink points are not a general descriptor field.** `mResourceSinkPoints` is present
   on only 191 entries across 11 groups. `FGBuildingDescriptor` does not have it at all,
   and 4 of the 122 `FGItemDescriptor` entries lack it. Treat it as optional.

**Engineering consequence for the data layer.**

- Index by `ClassName`: it is unique across all 2,868 entries this run, so it is a valid
  primary key for the normalized registry. Do not key on `FullName` - only 1,552 entries
  have one.
- The registry must join across groups: recipe -> item descriptor (for form, sink points,
  energy) and recipe -> `FGBuildable*` (for display name, power). There is no single
  "descriptor" group.
- There are 114 groups, not a handful. Building the registry by whitelisting a few
  `NativeClass` names is correct and cheap, but the whitelist must be data-driven and the
  extractor must log any unrecognized group rather than dropping it silently
  (BOOTSTRAP non-negotiable 7).
- **Hazard for the 7-bit ASCII gate:** the en-US strings contain 10 distinct non-ASCII
  codepoints this run, including U+2014 EM DASH (1 occurrence), U+2019/U+201C/U+201D
  smart quotes (7 total), U+202F NARROW NO-BREAK SPACE (1,305), U+00A0 (73), U+2122 (15),
  U+00B3 (12), U+2082 (2) and one stray U+FEFF embedded inside a `mDescription`. The
  normalized registry is a generated, gitignored artifact so it may hold them, but any
  tracked doc, test or fixture that quotes a display name or description must
  transliterate to ASCII or the pre-commit character gate will fire - correctly.

---

## S3 - are numeric fields embedded in string blobs?

**Assumption as stated (BOOTSTRAP section 3):** "Numeric fields are embedded in string
blobs needing a secondary parse (Unreal serializes struct arrays as text)."

**Method.** Read `mIngredients`, `mProduct` and `mProducedIn` off named recipes and
printed the raw Python string with `repr`. Then swept all 872 `FGRecipe` entries for
grammar variance: paren wrapping, backslash escapes, inner key tokens, and whether a
strict regex matches every chunk. Then joined every `ItemClass` back to its descriptor's
`mForm` to settle the units question by measurement.

**Raw evidence - the actual values (grammar evidence, not a data slice).**

`Recipe_IngotIron_C`:

```
mIngredients = ((ItemClass="/Script/Engine.BlueprintGeneratedClass'/Game/FactoryGame/Resource/RawResources/OreIron/Desc_OreIron.Desc_OreIron_C'",Amount=1))
mProduct     = ((ItemClass="/Script/Engine.BlueprintGeneratedClass'/Game/FactoryGame/Resource/Parts/IronIngot/Desc_IronIngot.Desc_IronIngot_C'",Amount=1))
mManufactoringDuration = 2.000000
mProducedIn  = ("/Game/FactoryGame/Buildable/Factory/SmelterMk1/Build_SmelterMk1.Build_SmelterMk1_C","/Game/FactoryGame/Buildable/-Shared/WorkBench/BP_WorkBenchComponent.BP_WorkBenchComponent_C","/Script/FactoryGame.FGBuildableAutomatedWorkBench")
```

`Recipe_Plastic_C` (fluid in, solid plus fluid byproduct out), abbreviated to the shape:

```
mIngredients = ((ItemClass="...Desc_LiquidOil.Desc_LiquidOil_C'",Amount=3000))
mProduct     = ((ItemClass="...Desc_Plastic.Desc_Plastic_C'",Amount=2),(ItemClass="...Desc_HeavyOilResidue.Desc_HeavyOilResidue_C'",Amount=1000))
mManufactoringDuration = 6.000000
```

**BINARY ANSWER: YES.** `mIngredients`, `mProduct` and `mProducedIn` are opaque strings
containing Unreal's text serialization of a struct array. They need their own parser and
their own test suite. Every scalar in the document is a string too
(`mManufactoringDuration` is `'2.000000'`, not `2.0`), so a secondary parse is universal,
not just for the struct arrays. BOOTSTRAP S3 is confirmed as stated.

### Exact grammar of the item-amount blob (`mIngredients`, `mProduct`)

```
blob        := "" | "(" entry { "," entry } ")"
entry       := "(ItemClass=" qpath ",Amount=" integer ")"
qpath       := '"' typename "'" objectpath "." classname "'" '"'
typename    := "/Script/Engine.BlueprintGeneratedClass"     (the ONLY value observed)
integer     := decimal digits, no sign observed, no decimal point
```

Measured properties, over all 872 recipes:

- **2,440** `(ItemClass=...,Amount=...)` pairs total.
- A strict regex `\(ItemClass="([^"]*)",Amount=([-0-9]+)\)` matched **2,440 of 2,440**
  chunks; **0** chunks failed to match. The grammar has no observed variance.
- Only two inner key tokens exist: `ItemClass` (2,440) and `Amount` (2,440). There is no
  optional third field.
- **0** of the three fields contain a backslash. There is NO escaping inside the blob
  after JSON decoding. The backslashes visible in a Python `repr` of these values are
  `repr`'s own quoting of the embedded single quote, not data.
- **Nesting is exactly two levels** and no deeper: an outer paren wrapping a
  comma-separated list of paren-wrapped entries. 0 of 2,616 non-empty field values were
  not paren-wrapped.
- The double quote is the field delimiter and the **single quote appears INSIDE** the
  quoted value as part of Unreal's `Type'Path'` object reference syntax. A parser that
  splits on `'` before splitting on `"` will corrupt every path. Split on `"` first.
- Empty is a real value: **6** recipes have `mIngredients == ""`
  (`Recipe_VehiclePath_Universal_C`, `Recipe_VehiclePath_FactoryCart_C`,
  `Recipe_QuantumEnergy_C`, `Recipe_VehiclePath_Explorer_C`,
  `Recipe_VehiclePath_Truck_C`, `Recipe_VehiclePath_Tractor_C`). **0** recipes have an
  empty `mProduct`.
- `ItemClass` path prefixes seen: `/Script/Engine.BlueprintGeneratedClass` for all 2,440.
  The item key is the trailing token after the final `.`, with the closing `'` stripped -
  e.g. `Desc_OreIron_C`. All 2,440 resolved to a descriptor entry present in this file;
  there were zero dangling references.

### Exact grammar of `mProducedIn` - a DIFFERENT grammar, do not reuse the parser

```
producedin  := "" | "(" qstring { "," qstring } ")"
qstring     := '"' objectpath '"'
```

`mProducedIn` entries are bare quoted paths with **no** `Type'...'` wrapper and **no**
`ItemClass=`/`Amount=` keys. Measured this run:

- Entry-count histogram: 5 empty, 791 with 1 entry, 25 with 2, 51 with 3.
- 17 distinct tokens. The top ones are `BP_BuildGun_C` (549), `Build_AssemblerMk1_C`
  (66), `BP_WorkBenchComponent_C` (58), `FGBuildableAutomatedWorkBench` (50),
  `Build_ConstructorMk1_C` (48), `BP_WorkshopComponent_C` (44).
- **Not every token is a buildable.** `FGBuildableAutomatedWorkBench` and `FGBuildGun`
  are `/Script/FactoryGame.<Class>` engine references with no `.` separator and no
  corresponding `Build_*` entry. The normalizer must tolerate a token that does not
  resolve to a building.
- Only **291 of 872** recipes name an automated production building (constructor,
  smelter, foundry, assembler, manufacturer, refinery, packager, blender, particle
  accelerator, converter, quantum encoder). The other 581 are build-gun, workbench,
  workshop or equipment recipes. Pillar 1 must filter on `mProducedIn`, not on group
  membership - all 872 sit in the same `FGRecipe` group.
- The 5 recipes with an empty `mProducedIn` are `Recipe_SteelWall_8x4_C`,
  `Recipe_Wall_Window_8x4_03_Steel_C`, `Recipe_PillarTop_C`, `Recipe_JumpPad_C`,
  `Recipe_JumpPadTilted_C`.

### Units - measured, not assumed

Every `ItemClass` was joined to its descriptor's `mForm` and the amounts bucketed:

| `mForm` | Pairs | Multiples of 1000 | Min | Max |
|---|---|---|---|---|
| `RF_SOLID` | 1749 | 0 | 1 | 1500 |
| `RF_LIQUID` | 100 | 98 | 1000 | 20000 |
| `RF_GAS` | 36 | 36 | 2000 | 25000 |
| `RF_INVALID` | 555 | 0 | 1 | 1 |

**Fluids and gases ARE scaled differently from solids.** Liquid and gas amounts are in
thousandths of a cubic metre (litres); solids are plain item counts. Divide a fluid or gas
amount by 1000 to get the cubic metres the game UI shows. Worked check:
`Recipe_Plastic_C` consumes `Amount=3000` crude oil over `mManufactoringDuration=6.000000`
seconds, which is 3 cubic metres per 6 s = 30 per minute, matching the in-game rate.

**Two traps inside the units question, both measured:**

1. **Fluid amounts are NOT always whole cubic metres.** 2 of the 100 liquid pairs are not
   multiples of 1000, both in `Recipe_Battery_C`. Any code that divides by 1000 into an
   `int` loses 0.5 m3 per cycle silently. This is exactly the case BOOTSTRAP section 4
   pillar 1 requires `fractions.Fraction` for - use `Fraction(amount, 1000)`, never a
   float and never integer division.

   > **CORRECTION, 2026-08-13 session 2, from a live re-probe of the same build.** This
   > paragraph originally read that the recipe "takes" sulfuric acid at 2500 AND water at
   > 1500, placing both fractional amounts on the ingredient side. **That is wrong about
   > the side.** Re-measured: `mIngredients` is sulfuric acid 2500, alumina solution 2000,
   > aluminum casing 1; `mProduct` is battery 1 and **water 1500**. The water is a
   > BYPRODUCT. The counts in this report are unaffected - there really are 2 such pairs -
   > but they sit one per side, not two on the input side. This matters because a fixture
   > written from the original sentence exercises ingredient rounding only and never
   > touches the product side, which is where the document's only other fractional fluid
   > actually lives. `BOOTSTRAP.md` section 3.2 carries the corrected statement and is
   > authoritative over this line.
2. **The scale factor is a property of the ITEM, not of the recipe.** `mForm` lives on the
   descriptor, in a different group. The blob parser cannot determine units on its own;
   normalization must happen after the descriptor join. `RF_INVALID` (555 pairs, all
   `Amount=1`) is the building-descriptor case in build-gun recipes and is neither a solid
   nor a fluid.

**Engineering consequence for the data layer.**

- `clockspeed/data/docs_extract.py` needs a dedicated blob parser module with its own
  test suite, per BOOTSTRAP S3's "if false" clause - which here fires on "yes, it is a
  blob", not on falsification.
- Two grammars, two parsers, two test suites: the item-amount grammar and the
  path-list grammar. They look similar and are not.
- Tests must be hand-authored synthetic strings in this grammar (BOOTSTRAP 8.1), which is
  cheap because the grammar is tiny and has zero observed variance. Cover at minimum:
  empty string, single entry, multi entry, byproduct (two products), a fluid amount that
  is not a multiple of 1000, a `/Script/...` token with no `.` in it, and an unresolvable
  `ItemClass`.
- Assert the strict-regex match count equals the `(ItemClass=` occurrence count at
  extraction time and fail loudly on a mismatch. That single assertion turns a future
  patch's grammar change into a red build instead of a silently short ingredient list.

---

## S7 - the overclock power-consumption exponent

**Assumption as stated (BOOTSTRAP section 3):** "Power-consumption scaling under overclock
follows a fixed exponent found in the docs data."

**Method.** Per CONVENTIONS 15.1, an empty grep is a claim about the pattern. So rather
than testing one guessed key, the probe collected **every distinct key name in the whole
document (988 of them)** and ran a case-insensitive substring sweep for the candidate
tokens `exponent`, `expo`, `power`, `potential`, `overclock`, `clock`, `boost`, `shard`,
`curve`, `scaling`. Then it counted values per key, per group, with examples, and listed
which groups carry `mPowerConsumption` without an exponent.

**Raw evidence.**

```
distinct key names across the whole document: 988

token 'exponent'  -> 2 matching key names
      mPowerConsumptionExponent                  occurrences=62  groups=34
      mProductionBoostPowerConsumptionExponent   occurrences=62  groups=34
token 'curve'     -> 0 matching key names
token 'overclock' -> 6 matching key names, all audio/VFX (mAlienOverClocking*)
token 'potential' -> 12 matching key names (mMinPotential, mMaxPotential,
                     mCanChangePotential, mPotentialShardSlots, ...)

KEY: mPowerConsumptionExponent
  entries carrying the key : 62
  groups carrying the key  : 34
  distinct values          : 2
     value='1.321929'  count=20   e.g. FGBuildableManufacturer/Build_ConstructorMk1_C
     value='1.600000'  count=42   e.g. FGBuildableStorage, FGBuildableTradingPost

KEY: mProductionBoostPowerConsumptionExponent
  entries carrying the key : 62   groups: 34   distinct values: 1
     value='2.000000'  count=62
```

**BINARY ANSWER: YES, the exponent is present in the data.** The key is
**`mPowerConsumptionExponent`** and its value is a string, e.g. `'1.321929'`. A second,
related key **`mProductionBoostPowerConsumptionExponent`** carries `'2.000000'` uniformly.

**Is it uniform across buildings? NO - it varies.** This contradicts the word "fixed" in
the BOOTSTRAP S7 assumption. Two distinct values across 62 entries in 34 groups this run:

| Value | Entries | Which buildings |
|---|---|---|
| `1.321929` | 20 | The overclockable production buildings: all 8 `FGBuildableManufacturer`, all 3 `FGBuildableManufacturerVariablePower`, all 4 `FGBuildableResourceExtractor`, `FGBuildableFrackingExtractor`, `FGBuildableFrackingActivator`, `FGBuildableWaterPump`, `FGBuildablePortal`, `FGBuildablePortalSatellite` |
| `1.600000` | 42 | Everything else: storage, pipeline pumps and junctions, generators (fuel, nuclear, geothermal), train platforms, docking stations, drone station, radar tower, resource sink, space elevator, power storage, jump pads, trading post, elevator |

The split is not arbitrary: `1.321929` is carried by the buildings whose clock speed the
player can change and whose rate scales with it, `1.600000` by fixed-draw infrastructure.
`mCanChangePotential` correlates but is **not** a reliable selector - measured this run,
of the 20 entries at `1.321929`, 18 are `mCanChangePotential=True` and 2 are `False`; of
the 42 at `1.600000`, 6 are `True` and 36 are `False`. **Read the exponent per building
class; never infer it from a category.**

Representative per-building base draws (all values are strings in the data):

```
Build_ConstructorMk1_C   mPowerConsumption=4.000000   mPowerConsumptionExponent=1.321929
Build_SmelterMk1_C       mPowerConsumption=4.000000   mPowerConsumptionExponent=1.321929
Build_AssemblerMk1_C     mPowerConsumption=15.000000  mPowerConsumptionExponent=1.321929
Build_ManufacturerMk1_C  mPowerConsumption=55.000000  mPowerConsumptionExponent=1.321929
Build_MinerMk1_C         mPowerConsumption=5.000000   mPowerConsumptionExponent=1.321929
Build_Blender_C          mPowerConsumption=75.000000  mPowerConsumptionExponent=1.321929
```

**Four things that are NOT in this file and must not be invented:**

1. **The maximum clock speed.** Every one of the 62 entries reports
   `mMinPotential='0.010000'` and `mMaxPotential='1.000000'`, and every one reports
   `mPotentialShardSlots='0'` with `mOverridePotentialShardSlots='False'`. The real
   250 percent ceiling comes from power shards via a global default that is not in this
   document. `mMaxPotential` here is the un-sharded base, not the achievable maximum.
   Reading it as a clock ceiling would cap every solve at 100 percent.
2. **The variable-power buildings have `mPowerConsumption='0.000000'`.** All 3
   `FGBuildableManufacturerVariablePower` entries do. Their draw comes from
   `mEstimatedMininumPowerConsumption` and `mEstimatedMaximumPowerConsumption` on the
   building (note the misspelling **`Mininum`** - use it verbatim) combined with
   `mVariablePowerConsumptionConstant` and `mVariablePowerConsumptionFactor` on the
   RECIPE. Measured: `Build_HadronCollider_C` 250 to 1500, `Build_Converter_C` 100 to
   400, `Build_QuantumEncoder_C` 0 to 2000. A solver that reads `mPowerConsumption` alone
   reports 0 MW for these three and will look correct.
3. **The production-boost exponent is a separate mechanic.**
   `mProductionBoostPowerConsumptionExponent='2.000000'` is uniform across all 62 entries.
   Do not conflate it with the overclock exponent.
4. **Four building groups carry `mPowerConsumption` with no exponent at all:**
   `FGVehicleDescriptor` (1), `FGBuildableLightSource` (2), `FGBuildableFloodlight` (2),
   `FGHoverPack` (1). The power model must treat a missing exponent as "not
   clock-scalable" rather than defaulting to a constant.

**Engineering consequence for the data layer.**

- `clockspeed/solve/power.py` reads `mPowerConsumptionExponent` off the building record in
  the normalized registry per building class. **No literal 1.321929 anywhere in the code**,
  per BOOTSTRAP S7 and non-negotiable 7. The registry extractor is the only place that
  string is ever converted, and it converts to `Fraction` from the decimal string, not
  through a float.
- Add a drift-guard assertion at extraction: if the set of distinct
  `mPowerConsumptionExponent` values changes, or a production building's exponent changes,
  the guard goes red. That is the patch-detection story BOOTSTRAP 8.1 asks for, applied to
  the one constant most likely to be balance-patched.
- The clock ceiling (shard-derived, currently 250 percent) is NOT derivable from this file.
  It must come from one of: (a) `Headers.zip`, the local first-party C++ headers, which is
  the authoritative place to look next and costs nothing; (b) the save file, if the
  per-building potential is stored there (phase 4 can confirm); or (c) an explicitly
  named, version-pinned config constant in the registry with a comment stating it is NOT
  from the docs data and must be re-checked on every game patch. Option (c) is the
  fallback, and if taken it must be a single named constant with a drift-guard entry, not
  a literal buried in the solver.

---

## Contradictions with BOOTSTRAP.md

Recorded for the orchestrator to apply. **This report does not edit BOOTSTRAP.md.**

1. **Section 3, S7 - "follows a FIXED exponent".** Refuted on the "fixed" half. The
   exponent is present in the data under `mPowerConsumptionExponent`, but it takes **two**
   distinct values this run: `1.321929` on 20 entries (overclockable production buildings)
   and `1.600000` on 42 entries (fixed-draw infrastructure), across 34 groups. Suggested
   rewording: "carries a per-building-class exponent found in the docs data". The "never
   hardcode a magic number" instruction is not merely upheld, it is strengthened - a
   single hardcoded constant would be wrong for 42 of the 62 buildings.

2. **Section 3, S7 - implied completeness of the docs data for the power model.** The
   overclock CEILING (the 250 percent shard limit) is absent from `en-US.json`. Every
   entry reports `mMaxPotential='1.000000'` and `mPotentialShardSlots='0'`. BOOTSTRAP
   should record that S7 is answered YES for the exponent and OPEN for the ceiling, with
   `Headers.zip` as the next place to look before any constant is written down.

3. **Section 3, S2 - "descriptors carrying display name".** True for item and resource
   descriptors, false for building descriptors: all **547 of 547** `FGBuildingDescriptor`
   entries have an empty `mDisplayName`. Building names live on the `FGBuildable*` entries.

4. **Section 3, S2 - "descriptors carrying ... sink-point values".** `mResourceSinkPoints`
   is on only **191** entries across 11 groups, not on descriptors generally, and 4 of the
   122 `FGItemDescriptor` entries lack it. It is an optional field.

5. **Section 2.1 finding 2 - "It is 10.6 MB and it must be parsed once".** Not a
   contradiction; confirmed exactly (10,640,180 bytes, 114 groups, 2,868 entries). Noted
   only because the count of NativeClass groups (114) is new information that section 2
   does not carry and that the extractor design depends on.

**Not contradicted, confirmed as stated:** S1 (UTF-16 LE with BOM, and the `io.json`
half-size hint was correct - it is the single UTF-8 file among 55), S3 (blobs need a
secondary parse), and the top-level `{NativeClass, Classes[]}` array shape of S2.

---

## Probe provenance

Probe scripts were written to and run from a session scratch directory outside the
repository, not from `C:\Clockspeed`. They are throwaway; nothing in the data layer
depends on them. Every probe opened game files in binary or text READ mode only. The game
install was not modified. No game data file, slice, sample or fixture was copied into this
repository.
