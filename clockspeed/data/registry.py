"""The normalized item, recipe and building model - the seam every layer above sees.

Per docs/ARCHITECTURE.md, this module owns the cross-group joins and the unit
normalization, and nothing else in the system re-derives either. It does not
read a file and it does not locate an install: ``clockspeed/data/locate.py``
owns the install and ``clockspeed/data/docs_extract.py`` owns the read, which
is why :func:`build_registry` takes an already-loaded
:class:`~clockspeed.data.docs_extract.DocsDocument` and imports no path
machinery at all. That is what lets the whole model be proven against a
hand-authored synthetic corpus on a machine with no game installed.

PROVENANCE (CS-1315). :func:`build_registry_from_bytes` takes the docs file's
raw BYTES - still never a path - and records their sha256 on
:attr:`Registry.source_sha256`, computed exactly as
``clockspeed/data/version.py::build_pin`` computes the pin's ``docs_sha256``,
so a consumer can compare the registry's source with the pin like for like. A
registry built from a document or by hand has no byte source and carries None.
This layer records the hash and never compares it: the comparison is the
audit's (``clockspeed/audit/build.py::registry_check_of``), which takes the pin
as a parameter.

WHY THIS LAYER IS THE DANGEROUS ONE
-----------------------------------
The parsers below it either return a value or raise. This layer JOINS and
CONVERTS, and every one of its failure modes produces a confident number of
the right type. The measured cases below all break an implementation that
passes its own tests, so each is handled explicitly and each has a named test.

- **Units are a property of the ITEM, not of the amount or the recipe.**
  ``mForm`` lives on the descriptor, in a different group from the recipe, so
  the blob parser cannot know a unit and this layer must resolve it after the
  join. Solids are counts; liquids and gases are litres and become cubic
  metres. Exactly two amounts in the whole measured document are not multiples
  of 1000, and they sit in ONE recipe, one per side - an acid at 2500 as an
  ingredient and water at 1500 as a byproduct. Integer division loses half a
  cubic metre per cycle on each, so every amount becomes a
  :class:`~fractions.Fraction` and nothing here ever divides into an int.
  ``RF_INVALID`` is a THIRD case, not a synonym for solid: 555 measured pairs
  carry it at Amount=1 and they are the build-gun building-descriptor case.
  They are neither divided nor treated as ordinary items; the form is kept
  verbatim so a caller can tell.

- **An ITEM is an entry carrying ``mForm``, and a BUILDING is an entry
  carrying a power field. Neither is a list of group names.** 750 measured
  entries carry ``mForm``, across THIRTEEN groups; 68 carry
  ``mPowerConsumption`` across THIRTY-EIGHT and 62 carry the exponent across
  thirty-four. A hand-listed set of the obvious groups was measured missing ten
  shipped RF_LIQUID descriptors and both fuel-burning generator groups, and the
  missing descriptors did not read as an error: the amounts referencing them
  simply took the "no descriptor, no knowable unit" branch and were published
  in litres under a contract that says cubic metres. Field presence is derived
  from the document, so the next patch that adds a descriptor group cannot
  silently reintroduce that. The measured descriptor groups survive only as a
  FLOOR, for the opposite case - an entry in one of them that has no ``mForm``
  is still a real referent some recipe names, so it is kept and flagged rather
  than dropped. There is no equivalent floor for buildings, because power IS
  the whole content of a Building: an entry with no power field has nothing to
  model, and keeping it would publish a zero the document never stated.

- **No floats, anywhere (non-negotiable 6).** ``float()`` succeeds on every
  decimal string in the document and silently poisons exactness, and no
  shipped exponent (the pin in ``clockspeed/data/version.py`` owns the
  values) is representable in binary floating point. Every conversion here goes
  straight from the decimal STRING to a Fraction. There is no ``float(`` in
  this file and there must never be one.

- **"Every scalar is a string" is FALSE, and a non-string is not an absent
  one.** 1152 measured values are not strings - two ``FGSchematic`` list fields
  and ``mFuel`` on both generator groups that carry it, the fuel and the
  nuclear group, each of which yields :class:`Generator` entries. Absence is
  this model's load-bearing signal for "not clock-scalable" and for "no sink
  value", so routing a present-but-wrong-type value to absent would collapse
  "the game shipped something new here" into "the game shipped nothing here".
  Present-but-wrong-type gets its own warning code. ``mFuel`` is the one
  non-string this module READS: its measured shape is a list of objects, so a
  list there is the expected type rather than a flag, and anything else
  present is an unreadable value with a warning code of its own - see
  :attr:`Generator.accepted_fuels`.

- **``mPowerConsumption`` has THREE shapes, not two.** A decimal string, an
  absent key, and - on one measured entry - a STRUCT string,
  ``'(Min=25.000000,Max=110.000000)'``. A model with two branches parses the
  first, treats the struct as unparsable, treats unparsable as absent and
  absent as zero, and publishes a confident 0 MW with no range. The struct is
  parsed here into the same estimated min/max the variable-power buildings
  carry, and a draw that genuinely cannot be read is None rather than zero.

- **A zero in ``mPowerConsumption`` is not a zero draw.** The three
  variable-power buildings declare ``'0.000000'`` there and carry their real
  range on ``mEstimatedMininumPowerConsumption`` and
  ``mEstimatedMaximumPowerConsumption``, combined with the constant and factor
  that live on the RECIPE. A model reading ``mPowerConsumption`` alone reports
  0 MW for the hungriest buildings in the game and looks perfectly correct.
  The estimated maximum must also be compared against zero rather than merely
  tested for presence: an entry declaring a maximum of ``'0.000000'`` is a
  fixed-draw building, not a variable one.

- **The clock exponent is per building CLASS, and its absence is meaningful.**
  Two distinct values are measured across 62 entries, so a hardcoded constant
  is wrong for 42 of them. Six entries carry power with NO exponent at all;
  that means NOT clock-scalable, so it is modeled as None and never defaulted.

- **``mMaxPotential`` is the un-sharded BASE. The ceiling is not read, and
  neither is any other operand of it.** The base IS read, per ADR 0005: it is
  a per-building-class document value, and reading it here is what keeps a
  literal ``1.0`` out of the solver for exactly the reason a literal exponent
  is banned - a balance patch moves it, and a literal turns that into silently
  wrong advice instead of a red build. It is ``'1.000000'`` on every measured
  entry, which is what makes a folded constant pass every test that does not
  mutate the corpus. Its absence is never defaulted to 1, on the same rule as
  the exponent above.

  What is NOT read is the CEILING. The game's own header declares the base as
  the maximum **not accounting for installed power shards**, and the ceiling as
  that base plus a shard slot count times the per-shard extra potential. The
  slot count lives on a subsystem that this document does not export at all, so
  the ceiling is UNKNOWN and per non-negotiable 7 an unknown is flagged and
  skipped rather than guessed. None of ``mPotentialShardSlots``,
  ``mExtraPotential``, ``mDefaultPotentialShardSlots`` or
  ``mOverridePotentialShardSlots`` is read here either: a ceiling assembled
  from three of the four operands is silently missing its multiplier, which is
  the original failure with more arithmetic in front of it. Reading the base as
  an achievable maximum caps every solve at 100 percent while looking correct
  on every un-overclocked building in the world, and that is the trap the
  python name exists to foreclose - nobody misreads "unsharded clock base" as
  "the ceiling". ADR 0005 owns where the ceiling comes from; ADR 0006 owns how
  the base enters this model.

- **``mAllowedResourceForms`` is a parenthesized LIST, and one of its tokens
  is spelled differently from every form constant in this file.** The measured
  values are ``(RF_SOLID)``, ``(RF_LIQUID)``, ``(RF_LIQUID,RF_GAS)`` and
  ``(RF_LIQUID,RF_GAS,(INVALID))``. A reader comparing the raw value against
  RF_SOLID matches none of the 8 entries that carry the field and reports every
  extractor as formless, which is indistinguishable from a document that
  stopped shipping it. The nested ``(INVALID)`` is NOT RF_INVALID, so it is
  kept verbatim and flagged rather than mapped onto a form the document never
  named - an allowlist of good tokens, never a denylist of bad ones.

- **An extraction rate has two operands and the document omits both on some
  entries.** 6 measured entries carry ``mItemsPerCycle`` and
  ``mExtractCycleTime``; 8 carry ``mAllowedResourceForms``. The two extras are
  real extraction content whose rate this document does not state, so they are
  modeled with a rate of None and flagged. A zero there would be a throughput
  of nothing published about buildings that extract, which is
  ``mPowerConsumption``'s confident zero with a different unit on it.

- **Recipes are whitelisted on NativeClass, never detected by shape.**
  ``FGCustomizationRecipe`` has a keyset byte-identical to ``FGRecipe``'s, so
  any field-presence or shape-based detector silently inflates 872 recipes
  into 978, and every one of the extras looks well formed.

- **Automation is a property of ``mProducedIn``.** All 872 recipes live in one
  group and only 291 name a production building, so group membership answers
  the wrong question. Nor is "has a non-manufacturer token" an exclusion test:
  76 of those 291 name a hand-craft token ALONGSIDE a real manufacturer. The
  test is whether at least one token resolves to a modeled building.

- **Building names are not on building descriptors.** All 547
  ``FGBuildingDescriptor`` entries have an empty ``mDisplayName``; the name is
  on the ``FGBuildable*`` entry. Reading the descriptor yields 547 nameless
  buildings and passes every test its author wrote, because an empty string is
  a valid string.

- **``mResourceSinkPoints`` is optional.** A ``.get(key, 0)`` default reports
  the entries that lack it as worthless to the sink, which is a claim the data
  never made. Absent is None; zero is 0; they are different facts.

- **Two keys are misspelled in the shipped game data** -
  ``mManufactoringDuration`` and ``mEstimatedMininumPowerConsumption`` - and
  both are used verbatim. The first sits beside the correctly spelled
  ``mManufacturingMenuPriority`` in the same record, so the misspelling reads
  like a typo in this file rather than in the game's.

- **``ClassName`` is the key.** It is unique across all 2868 measured entries.
  ``FullName`` is on barely half of them, so nothing may key on it.

FLAG AND SKIP, NEVER FATAL AND NEVER SILENT (non-negotiable 7)
--------------------------------------------------------------
An unknown group, an unmodeled group, an unresolvable produced-in token, an
item reference with no descriptor, a malformed blob and a recipe with no
duration key are all FLAGGED on :attr:`Registry.warnings` and skipped. None of
them stops the build, and none of them vanishes. Warnings are aggregated by
subject with a count, because one line per occurrence would bury the six
distinct unresolvable tokens under 703 lines and train the reader to skip the
field.

THE FATAL CASES, and why flag-and-skip is not enough for them
-------------------------------------------------------------
A short ingredient list is a wrong production ratio that nothing downstream can
distinguish from a right one, so a game patch that changes the shipped grammar
has to produce a RED BUILD rather than a quietly thinner factory plan. Three
signals do that, and it takes all three because the obvious one does not reach
as far as it looks.

1. **Parser versus marker count, per blob.** ``marker_count(blob)`` is taken
   BEFORE the parse and compared against ``len(parse_item_amounts(blob))``; a
   disagreement raises. The count is a deliberately naive literal count that
   shares no code with the parser, so it is a real cross-check rather than a
   second implementation wrong in the same way. Its REACH is narrow and saying
   so is the point: the marker literal is part of the parser's own pattern, so
   on any blob the parser accepts the two agree by construction. This signal
   catches the marker appearing where the parser does not expect it - and
   nothing else.

2. **Too many refused blobs.** The ordinary patch shape - one extra field per
   entry - keeps every marker in place and simply makes the parser refuse the
   blob. Per-recipe flag-and-skip then does exactly what it is supposed to do,
   once per recipe, and a document of 872 recipes builds into a registry of
   none with a zero exit. So the refusals are counted, and more than
   ``MAX_MALFORMED_BLOBS`` of them is a grammar change rather than damaged
   content.

3. **No recipe survived a non-empty recipe group.** The end state of signal 2
   even when the threshold does not catch it, and the one shape that is never
   a legitimate reading of a document that carries recipe entries at all.

Signals 2 and 3 are the reason this module can promise a red build; signal 1
alone was measured passing a whole grammar change through in silence. All three
raise :class:`RegistryIntegrityError`, which deliberately does NOT subclass
ValueError, so the flag-and-skip handler for a malformed blob cannot swallow
the canary.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from types import MappingProxyType
from typing import Final

from clockspeed.data.blobs import (
    BlobParseError,
    ItemAmount,
    marker_count,
    parse_class_paths,
    parse_item_amounts,
)
from clockspeed.data.docs_extract import (
    KEY_CLASS_NAME,
    DocsDocument,
    DocsGroup,
    decode_docs_bytes,
    load_document,
)

__all__ = [
    "EQUIPMENT_GROUP_SHORT_NAMES",
    "EXTRACTION_MARKER_KEYS",
    "FLUID_FORMS",
    "FORM_GAS",
    "FORM_INVALID",
    "FORM_LIQUID",
    "FORM_SOLID",
    "GENERATION_MARKER_KEYS",
    "ITEM_GROUP_SHORT_NAMES",
    "KEY_ALLOWED_RESOURCES",
    "KEY_ALLOWED_RESOURCE_FORMS",
    "KEY_CAN_CHANGE_POTENTIAL",
    "KEY_DISPLAY_NAME",
    "KEY_DURATION",
    "KEY_ENERGY_VALUE",
    "KEY_ESTIMATED_MAX_POWER",
    "KEY_ESTIMATED_MIN_POWER",
    "KEY_EXTRACT_CYCLE_TIME",
    "KEY_FORM",
    "KEY_FUEL",
    "KEY_FUEL_CLASS",
    "KEY_INGREDIENTS",
    "KEY_ITEMS_PER_CYCLE",
    "KEY_MAX_POTENTIAL",
    "KEY_ONLY_ALLOW_CERTAIN_RESOURCES",
    "KEY_POWER_CONSUMPTION",
    "KEY_POWER_EXPONENT",
    "KEY_POWER_PRODUCTION",
    "KEY_PRODUCED_IN",
    "KEY_PRODUCT",
    "KEY_SINK_POINTS",
    "KEY_VARIABLE_POWER_CONSTANT",
    "KEY_VARIABLE_POWER_FACTOR",
    "KEY_VARIABLE_PRODUCTION_CONSTANT",
    "KEY_VARIABLE_PRODUCTION_FACTOR",
    "LITRES_PER_CUBIC_METRE",
    "MAX_MALFORMED_BLOBS",
    "POWER_MARKER_KEYS",
    "RECIPE_GROUP_SHORT_NAMES",
    "RESOURCE_FORMS",
    "UNMODELED_GROUP_SHORT_NAMES",
    "WARN_DUPLICATE_CLASS_NAME",
    "WARN_EMPTY_DISPLAY_NAME",
    "WARN_MALFORMED_BLOB",
    "WARN_MALFORMED_GROUP",
    "WARN_MISSING_CLASS_NAME",
    "WARN_MISSING_DURATION",
    "WARN_MISSING_EXTRACTION_RATE",
    "WARN_MISSING_FORM",
    "WARN_MISSING_POWER",
    "WARN_MISSING_PRODUCTION",
    "WARN_NON_STRING_VALUE",
    "WARN_UNKNOWN_GROUP",
    "WARN_UNKNOWN_ITEM",
    "WARN_UNKNOWN_RESOURCE_FORM",
    "WARN_UNPARSABLE_FLAG",
    "WARN_UNPARSABLE_NUMBER",
    "WARN_UNREADABLE_ALLOWED_RESOURCES",
    "WARN_UNREADABLE_FUELS",
    "WARN_UNRESOLVED_PRODUCED_IN",
    "Building",
    "Extractor",
    "Generator",
    "Item",
    "Recipe",
    "RecipeIO",
    "Registry",
    "RegistryError",
    "RegistryIntegrityError",
    "RegistryWarning",
    "automated_recipes",
    "build_registry",
    "build_registry_from_bytes",
]

# ---------------------------------------------------------------------------
# Document keys
# ---------------------------------------------------------------------------

KEY_DISPLAY_NAME: Final = "mDisplayName"
KEY_FORM: Final = "mForm"
KEY_ENERGY_VALUE: Final = "mEnergyValue"
KEY_SINK_POINTS: Final = "mResourceSinkPoints"
KEY_INGREDIENTS: Final = "mIngredients"
KEY_PRODUCT: Final = "mProduct"
KEY_PRODUCED_IN: Final = "mProducedIn"

#: MISSPELLED IN THE SHIPPED GAME DATA, and used verbatim. It sits beside the
#: correctly spelled mManufacturingMenuPriority in the SAME record. Correcting
#: this spelling silently drops the duration off every recipe.
KEY_DURATION: Final = "mManufactoringDuration"

KEY_POWER_CONSUMPTION: Final = "mPowerConsumption"
KEY_POWER_EXPONENT: Final = "mPowerConsumptionExponent"

#: MISSPELLED IN THE SHIPPED GAME DATA ("Mininum"), and used verbatim.
#: Correcting it reports the three variable-power buildings at zero draw.
KEY_ESTIMATED_MIN_POWER: Final = "mEstimatedMininumPowerConsumption"
KEY_ESTIMATED_MAX_POWER: Final = "mEstimatedMaximumPowerConsumption"

KEY_VARIABLE_POWER_CONSTANT: Final = "mVariablePowerConsumptionConstant"
KEY_VARIABLE_POWER_FACTOR: Final = "mVariablePowerConsumptionFactor"

#: CS-1059. The generation fields, measured read-only on the pinned build. A
#: fuel or nuclear generator carries a scalar mPowerProduction; the
#: geothermal generator declares that scalar as '0.000000' and carries its
#: real output on the two variable fields, the same trap the variable-power
#: consumers set one field over. See :class:`Generator`.
KEY_POWER_PRODUCTION: Final = "mPowerProduction"
KEY_VARIABLE_PRODUCTION_CONSTANT: Final = "mVariablePowerProductionConstant"
KEY_VARIABLE_PRODUCTION_FACTOR: Final = "mVariablePowerProductionFactor"

#: The UN-SHARDED clock base, kept under the game's own spelling so the
#: provenance stays greppable while the python name it feeds says what it
#: actually means. It is NOT the overclock ceiling - see the module docstring
#: and ADR 0005 - and the other operands of the ceiling equation are
#: deliberately absent from this file.
KEY_MAX_POTENTIAL: Final = "mMaxPotential"

#: CS-1281. Whether the player can change this building's clock AT ALL, read
#: into :attr:`Building.clockable`. MEASURED on the pinned build before this was
#: written: every published building that carries it carries exactly ``'True'``
#: or ``'False'``, and the ones that omit it are exactly the ones with no
#: exponent. Not an operand of the ADR 0005 ceiling - it says whether a clock
#: exists, never how high one goes - and its python name avoids the game's
#: spelling because the ceiling fence forbids that word in a field name.
KEY_CAN_CHANGE_POTENTIAL: Final = "mCanChangePotential"

#: The document's two boolean spellings, and ONLY these - an allowlist, on the
#: rule RESOURCE_FORMS states. A case-folding or truthiness reader would admit
#: the next differently spelled value as a confident bool; this one flags it.
_FLAG_SPELLINGS: Final[Mapping[str, bool]] = MappingProxyType({"True": True, "False": False})

#: The three extraction fields, measured on the pinned build before any of
#: this was written. mItemsPerCycle and mExtractCycleTime sit on 6 entries
#: across 3 groups; mAllowedResourceForms reaches 8 entries across 5, and the
#: two extra groups carry NO rate at all. That asymmetry is why the marker
#: set below is any-of rather than all-of, and why an extractor with no
#: readable rate is a modeled fact rather than a dropped entry.
KEY_ITEMS_PER_CYCLE: Final = "mItemsPerCycle"
KEY_EXTRACT_CYCLE_TIME: Final = "mExtractCycleTime"
KEY_ALLOWED_RESOURCE_FORMS: Final = "mAllowedResourceForms"

#: CS-1285 slice A. An extractor's resource restriction, measured read-only on
#: the pinned build: every measured extractor that carries the flag carries
#: 'True' or 'False', the restricted ones carry their resources as a
#: class-path list in the mProducedIn grammar, each quoted entry wrapped in a
#: Type'Path' pair, and the unrestricted miners carry the empty string. The
#: list is read ONLY when the flag reads 'True' - see
#: :attr:`Extractor.allowed_resources`.
KEY_ONLY_ALLOW_CERTAIN_RESOURCES: Final = "mOnlyAllowCertainResources"
KEY_ALLOWED_RESOURCES: Final = "mAllowedResources"

#: CS-1285 slice A. A generator's accepted fuels, measured read-only on the
#: pinned build as a JSON ARRAY of objects - never a string - on the fuel and
#: the nuclear generator groups, and absent on the geothermal one. Each object
#: carries exactly four keys; only the fuel's ClassName is read. The
#: supplemental resource and the byproduct are out of scope, so their keys are
#: deliberately not named here.
KEY_FUEL: Final = "mFuel"
KEY_FUEL_CLASS: Final = "mFuelClass"

# ---------------------------------------------------------------------------
# Forms and units
# ---------------------------------------------------------------------------

FORM_SOLID: Final = "RF_SOLID"
FORM_LIQUID: Final = "RF_LIQUID"
FORM_GAS: Final = "RF_GAS"

#: A third case, not a synonym for solid and not an error: 555 measured pairs
#: carry it at Amount=1, all of them build-gun building descriptors.
FORM_INVALID: Final = "RF_INVALID"

#: The forms whose amounts are litres. Everything else is a plain count.
FLUID_FORMS: Final = frozenset({FORM_LIQUID, FORM_GAS})

#: The CLOSED vocabulary of form tokens this build recognizes. It exists for
#: mAllowedResourceForms, which is a parenthesized LIST of tokens rather than
#: a single form, and one measured value carries a token spelled '(INVALID)' -
#: NOT RF_INVALID. An allowlist of good values is what keeps that token out of
#: the recognized set: a denylist would admit the next differently spelled one
#: silently. Unrecognized tokens are kept verbatim and flagged instead.
RESOURCE_FORMS: Final = frozenset({FORM_SOLID, FORM_LIQUID, FORM_GAS, FORM_INVALID})

#: The fluid scale factor. Applied as a Fraction DENOMINATOR, never as integer
#: division: two measured amounts are not multiples of it.
LITRES_PER_CUBIC_METRE: Final = 1000

# ---------------------------------------------------------------------------
# Group roles
# ---------------------------------------------------------------------------

# The RECIPE role is assigned by group name and the other two are not, and that
# asymmetry is measured rather than stylistic. FGCustomizationRecipe has a
# keyset byte-identical to FGRecipe's, so no field-presence test can separate
# 872 recipes from 978 - only the NativeClass can. Items and buildings have the
# opposite problem: their marker fields appear across thirteen and thirty-eight
# groups respectively, so any list of names is a list that goes stale on the
# next patch, silently and in the direction of publishing wrong numbers.

#: The recipe group, and deliberately ONLY this one.
RECIPE_GROUP_SHORT_NAMES: Final = frozenset({"FGRecipe"})

#: The fields whose presence makes an entry a power consumer. Either one is
#: enough: 68 measured entries carry a draw and 62 carry an exponent, and an
#: entry carrying only the exponent is a gap in the document rather than a
#: reason to drop the building.
POWER_MARKER_KEYS: Final = (KEY_POWER_CONSUMPTION, KEY_POWER_EXPONENT)

#: The fields whose presence makes an entry an extractor. Any ONE is enough,
#: on the same measured grounds as POWER_MARKER_KEYS above: the two rate keys
#: reach 6 entries and the forms key reaches 8, and the two entries carrying
#: only the forms are real extraction content whose rate this document does
#: not state. Requiring all three would drop them; requiring only the forms
#: would drop an entry a patch ships with a rate and no forms. There is no
#: group floor, for the reason _is_building_entry states: a list of group
#: names goes stale on the next patch, silently.
EXTRACTION_MARKER_KEYS: Final = (
    KEY_ITEMS_PER_CYCLE,
    KEY_EXTRACT_CYCLE_TIME,
    KEY_ALLOWED_RESOURCE_FORMS,
)

#: The fields whose presence makes an entry a power GENERATOR (CS-1059). Any
#: ONE is enough, on the rule EXTRACTION_MARKER_KEYS states: an entry carrying
#: only the variable factor is generation content whose scalar the document
#: does not state, and requiring the scalar would drop it. No group floor,
#: for the reason _is_building_entry gives.
GENERATION_MARKER_KEYS: Final = (
    KEY_POWER_PRODUCTION,
    KEY_VARIABLE_PRODUCTION_CONSTANT,
    KEY_VARIABLE_PRODUCTION_FACTOR,
)

#: The measured descriptor groups, kept ONLY as a floor beneath the mForm test.
#: Their purpose is the entry that a future patch ships into one of them with
#: no mForm at all: it is still a real item some recipe names, so it is kept
#: and flagged rather than dropped. Nothing here narrows the item namespace -
#: an entry in any other group carrying mForm is an item too. FGBuildingDescriptor
#: is listed even though every one of its display names is empty: its entries
#: are the PRODUCTS of build-gun recipes, so losing them loses the product side
#: of 549 recipes.
ITEM_GROUP_SHORT_NAMES: Final = frozenset(
    {
        "FGItemDescriptor",
        "FGResourceDescriptor",
        "FGBuildingDescriptor",
        "FGVehicleDescriptor",
    }
)

#: How many recipes may be flagged and skipped for a malformed blob before the
#: build stops calling it damaged content and starts calling it a grammar
#: change. See the module docstring: one bad row is ordinary and is skipped,
#: while a burst of them means the shipped grammar moved and every ratio in the
#: registry is now a guess.
MAX_MALFORMED_BLOBS: Final = 4

#: Groups this build recognizes, could plausibly be read as content, and
#: deliberately is not reading. FGCustomizationRecipe is recipe-shaped down to
#: the byte and is excluded by RECIPE_GROUP_SHORT_NAMES above;
#: FGSchematic belongs to the progression layer and carries neither marker
#: field. Neither is reported as unknown, and that is the point: reporting a
#: deliberate exclusion on every build trains the reader to ignore the unknown
#: list, which is exactly how a real unknown gets missed.
UNMODELED_GROUP_SHORT_NAMES: Final = frozenset({"FGCustomizationRecipe", "FGSchematic"})

#: CS-1313. The groups whose entries are EQUIPMENT - a thing the player wears or
#: carries, never a building on the power grid - and deliberately a CLOSED list
#: of group names. The session 138 ruling (A1, docs/LEDGER.md) marks equipment
#: by its docs group, and a group offers nothing else to be read by: the
#: document carries no class hierarchy, and the equipment groups share no name
#: family - the hover pack's is FGHoverPack, only two of these begin
#: FGEquipment, and a "not FGBuildable" test would sweep in the hypertube
#: entrance and the dimensional depot, whose groups sit outside that family
#: while their entries are buildings. A class-name prefix is the shape test the
#: module docstring forbids, and it fails open.
#:
#: THE CLOSED-WORLD ASSUMPTION, stated: a group not named here is not equipment.
#: It holds for the pinned build, where the property every equipment class
#: inherits, mEquipmentSlot, is carried by every entry of these groups and by no
#: entry of any other - tests/data/test_registry.py checks that against an
#: installed document. It holds for a group the build has never seen, because an
#: unrecognized group never reaches this module. What it does not cover is a NEW
#: equipment group once docs_extract learns its name, and that drift is what the
#: installed-document arm reddens on. Listed whole rather than as the one group
#: that carries a power field today, so a patch giving any other equipment class
#: one is already marked. A vehicle descriptor is NOT equipment under the ruling
#: and is not listed.
EQUIPMENT_GROUP_SHORT_NAMES: Final = frozenset(
    {
        "FGChainsaw",
        "FGChargedWeapon",
        "FGConsumableEquipment",
        "FGEquipmentStunSpear",
        "FGEquipmentZipline",
        "FGGasMask",
        "FGGolfCartDispenser",
        "FGHoverPack",
        "FGJetPack",
        "FGJumpingStilts",
        "FGObjectScanner",
        "FGParachute",
        "FGPortableMinerDispenser",
        "FGSuitBase",
        "FGWeapon",
    }
)

#: The struct shape of mPowerConsumption. Measured on exactly one entry, which
#: is why a model written from the other 67 has two branches and publishes a
#: confident zero for this one. Anchored end to end so a shape this pattern
#: does not fully explain stays an unparsable number rather than half-parsing
#: into a plausible bound.
_POWER_STRUCT_RE: Final = re.compile(r"^\(Min=([^,()]+),Max=([^,()]+)\)$")

# ---------------------------------------------------------------------------
# Warning codes
# ---------------------------------------------------------------------------

WARN_DUPLICATE_CLASS_NAME: Final = "duplicate-class-name"
WARN_EMPTY_DISPLAY_NAME: Final = "empty-display-name"
WARN_MALFORMED_BLOB: Final = "malformed-blob"
WARN_MALFORMED_GROUP: Final = "malformed-group"
WARN_MISSING_CLASS_NAME: Final = "missing-class-name"
WARN_MISSING_DURATION: Final = "missing-duration"
WARN_MISSING_EXTRACTION_RATE: Final = "missing-extraction-rate"
WARN_MISSING_FORM: Final = "missing-form"
WARN_MISSING_POWER: Final = "missing-power"
WARN_MISSING_PRODUCTION: Final = "missing-production"
WARN_NON_STRING_VALUE: Final = "non-string-value"
WARN_UNKNOWN_GROUP: Final = "unknown-group"
WARN_UNKNOWN_ITEM: Final = "unknown-item-reference"
WARN_UNKNOWN_RESOURCE_FORM: Final = "unknown-resource-form"
WARN_UNPARSABLE_NUMBER: Final = "unparsable-number"
WARN_UNRESOLVED_PRODUCED_IN: Final = "unresolved-produced-in"
#: CS-1281. A boolean field present as a string that is neither spelling.
WARN_UNPARSABLE_FLAG: Final = "unparsable-flag"
#: CS-1285 slice A. mFuel is present and cannot be read WHOLE. Its subject is
#: the generator's ClassName, and it is the only thing that tells such a
#: generator's None apart from the None of one that declares no fuel at all.
WARN_UNREADABLE_FUELS: Final = "unreadable-fuels"
#: CS-1285 slice A. A restricted extractor whose resource list cannot be read,
#: subject its ClassName. Distinct from WARN_MALFORMED_BLOB on purpose: that
#: code is counted toward the recipe grammar canary, and this one is not a
#: recipe.
WARN_UNREADABLE_ALLOWED_RESOURCES: Final = "unreadable-allowed-resources"


class RegistryError(Exception):
    """Base class for every failure this module raises."""


class RegistryIntegrityError(RegistryError):
    """The blob parser and the independent marker count disagree.

    Deliberately NOT a :class:`ValueError`, and therefore not catchable as a
    :class:`~clockspeed.data.blobs.BlobParseError`. The flag-and-skip handler
    for a malformed blob catches that one, and if this were in the same
    hierarchy the handler would swallow the only independent signal that the
    grammar has changed.
    """


@dataclass(frozen=True)
class RegistryWarning:
    """One piece of content that was flagged and skipped, and why.

    Attributes:
        code: One of the module's WARN_* constants.
        subject: What was flagged - a class name, a group short name, an
            unresolvable token, or a group index for a malformed group.
        detail: One line naming the consequence, never echoing document
            content.
        count: How many occurrences this warning aggregates. Aggregation by
            subject is what keeps six distinct unresolvable tokens from
            arriving as 703 separate lines.
    """

    code: str
    subject: str
    detail: str
    count: int = 1


@dataclass(frozen=True)
class Item:
    """One item, resolved from its descriptor.

    Attributes:
        key: The entry's ClassName, which is unique document-wide.
        display_name: The verbatim mDisplayName. Genuinely EMPTY for every
            building descriptor; the real name is on the buildable entry.
        form: The verbatim mForm, e.g. ``RF_SOLID``, or the empty string when
            the entry carries none. Kept verbatim rather than reduced to
            ``is_fluid`` alone so that RF_INVALID - which is neither solid nor
            fluid - stays distinguishable.
        energy_value: mEnergyValue as an exact Fraction, or None when absent.
        sink_points: mResourceSinkPoints, or None when absent. None and 0 are
            different facts: the field is measured on only 191 entries.
        is_fluid: True for RF_LIQUID and RF_GAS only. This is what decides
            whether an amount is litres.
    """

    key: str
    display_name: str
    form: str
    energy_value: Fraction | None
    sink_points: int | None
    is_fluid: bool


@dataclass(frozen=True)
class RecipeIO:
    """One side of one recipe, unit normalized.

    Attributes:
        item_key: The referenced item's ClassName. It may name an item the
            registry has no descriptor for; that is flagged rather than
            dropped.
        amount: The amount per cycle as an exact Fraction - whole items for a
            solid, cubic metres for a fluid. Never a float and never the
            result of integer division.
    """

    item_key: str
    amount: Fraction


@dataclass(frozen=True)
class Building:
    """One power-consuming buildable.

    Attributes:
        key: The entry's ClassName. This is the token an mProducedIn path
            resolves to.
        display_name: The verbatim mDisplayName from the BUILDABLE entry, not
            from the building descriptor.
        power_consumption: mPowerConsumption as an exact Fraction, or None when
            the entry declares no readable scalar draw - an absent key, an
            unparsable value, or the struct shape, whose real content is on the
            estimated range below. A declared ``'0.000000'`` is Fraction(0) and
            is a different fact from None: the variable-power buildings state
            that zero deliberately. Publishing zero for the None cases is the
            one unacceptable option, because a confident zero is exactly what a
            power plan cannot detect.
        power_exponent: mPowerConsumptionExponent, or None when the entry
            carries none - which means NOT clock-scalable and is never
            defaulted to a value the game did not ship.
        estimated_min_power: The low end of a variable draw, or None. Carries
            the struct shape's Min bound when mPowerConsumption held one.
        estimated_max_power: The high end of a variable draw, or None. Carries
            the struct shape's Max bound when mPowerConsumption held one.
        is_variable_power: True when the entry declares an estimated maximum
            ABOVE zero, which is the measured shape of a building whose draw
            is a range rather than a constant. A declared maximum of zero is a
            fixed-draw building, so presence of the key alone is not the test.
        unsharded_clock_base: mMaxPotential as an exact Fraction, or None when
            the entry declares none. It is the maximum clock with NO power
            shards installed, which is what the game's own header calls it, and
            it is NOT the overclock ceiling - the ceiling adds a shard slot
            count that no file on this machine carries (ADR 0005, ADR 0006).
            A caller that clamps a clock to this value is clamping to the
            un-sharded base and has to say so rather than report it as the
            ceiling. Absent is None and is never defaulted to 1, for the same
            reason a missing exponent is not defaulted.
        clockable: CS-1281. mCanChangePotential - True when the player can
            change this building's clock, False when the class has no clock to
            change, and None when the entry declares neither: the key absent,
            a non-string value, or a string outside the document's two
            spellings (the last two flagged). NONE IS A NAMED UNKNOWN AND IS
            NEVER DEFAULTED to either bool. True would count a class with no
            clock as one whose clock tag was elided; False would assert a
            class cannot be clocked on no evidence. A consumer that needs a
            bool decides what None means itself, and says so.
        is_equipment: CS-1313. True when the entry's docs group is one of
            EQUIPMENT_GROUP_SHORT_NAMES: a thing the player wears or carries,
            which sits in this namespace only because its entry declares a
            power field, and which is never a building on the grid. Decided by
            the GROUP the entry came from, never by the shape of its class
            name. The entry keeps every other field as declared; it is the
            audit balance that refuses to count it as a built power consumer.
    """

    key: str
    display_name: str
    power_consumption: Fraction | None
    power_exponent: Fraction | None
    estimated_min_power: Fraction | None
    estimated_max_power: Fraction | None
    is_variable_power: bool
    # Appended, and with a default, deliberately: a required field inserted
    # mid-class breaks every positional construction of a Building at once.
    unsharded_clock_base: Fraction | None = None
    # CS-1281. Appended with a default for the same reason. None is the
    # unknown, so the default asserts nothing about a hand-built entry.
    clockable: bool | None = None
    # CS-1313. Appended with a default for the same reason. A group is always
    # in hand, so there is no unknown to name; False is what every hand-built
    # entry has always meant - a building on the grid.
    is_equipment: bool = False


@dataclass(frozen=True)
class Extractor:
    """One buildable that pulls a raw resource out of the world.

    Throughput is ``items_per_cycle / extract_cycle_time`` per second, and
    NEITHER operand may be assumed. Both are None on the two measured entries
    that carry only the allowed forms, and a caller that substitutes a number
    for a None here publishes a confident rate the game never stated - the
    exact failure :attr:`Building.power_consumption` documents at length.

    WHAT THIS MODEL DELIBERATELY DOES NOT DO
    ----------------------------------------
    - **It does not convert litres.** ``mItemsPerCycle`` is 1 on a solid miner
      and 2000 on a fluid extractor, and the second number is LITRES. The
      conversion cannot happen here because the resource is not known here:
      :attr:`allowed_forms` is a SET, sometimes of two forms, and which
      resource a given extractor actually pulls is a property of the node it
      sits on, which ADR 0003 measured as absent from the save. Dividing by
      LITRES_PER_CUBIC_METRE at this layer would publish 2 items per cycle for
      a pump the document says moves 2000 litres. The caller converts, once it
      has resolved a form.
    - **It does not apply a purity multiplier.** Purity scales the rate in the
      game and no purity value is exported by this document or stored in a
      save, so a per-purity rate is the CALLER's, computed from a stated
      multiplier it owns and can be held to.
    - **It does not read the pressurizer's own extraction field.** One measured
      entry carries ``mDefaultPotentialExtractionPerMinute``, and its value is
      ``'0.000000'``. Reading it would publish a rate of zero per minute for a
      building that genuinely extracts, which is a wrong number wearing the
      right type. It is left unread, and the entry reports its rate as unknown.

    Attributes:
        key: The entry's ClassName, which is unique document-wide and is the
            same token :class:`Building` is keyed by - the join a throughput
            consumer needs, because an extractor also draws power.
        display_name: The verbatim mDisplayName from the buildable entry. It is
            genuinely ABSENT on one measured entry, which yields the empty
            string and a flag rather than a name synthesized from the key.
        items_per_cycle: mItemsPerCycle as an exact Fraction, or None when the
            entry declares none or declares something unreadable. In the
            document's own units - a count for a solid, litres for a fluid.
        extract_cycle_time: mExtractCycleTime in seconds as an exact Fraction,
            or None on the same terms. A DECLARED zero is Fraction(0) and is a
            different fact from None, on the rule :attr:`Recipe.duration`
            states; a consumer dividing by it guards the division itself
            rather than having this layer silently rewrite the document.
        allowed_forms: The recognized FORM_* tokens from
            mAllowedResourceForms, which is a parenthesized LIST rather than a
            single token. Empty when the entry declares none - never a guessed
            RF_SOLID.
        unrecognized_forms: Tokens inside that list which are outside
            RESOURCE_FORMS, kept verbatim and in source order. One measured
            value carries ``'(INVALID)'``, which is not ``RF_INVALID``:
            treating the two as the same would invent a form the document never
            named, and dropping the token would erase the evidence that it was
            ever there (non-negotiable 7).
        allowed_resources: CS-1285. The resource ClassNames from
            ``mAllowedResources``, in source order and deduplicated, read ONLY
            when ``mOnlyAllowCertainResources`` reads exactly ``'True'``; None
            otherwise. NONE MEANS UNRESTRICTED OR UNKNOWN, never "extracts
            nothing", and this field is never an empty tuple: the measured oil
            pump is restricted to crude alone while its forms admit every
            liquid, so a caller resolving what an extractor can yield takes
            this list when it is present and falls back to the items of
            :attr:`allowed_forms` when it is None. A flag that is neither
            spelling is flagged as unparsable; a restricted entry whose list is
            absent, empty, not a string or not the class-path grammar is
            flagged as unreadable. A token naming no item descriptor is kept
            verbatim and flagged as an unknown item.
    """

    key: str
    display_name: str
    items_per_cycle: Fraction | None
    extract_cycle_time: Fraction | None
    allowed_forms: frozenset[str]
    unrecognized_forms: tuple[str, ...] = ()
    # CS-1285. Appended with a default, for the reason
    # Building.unsharded_clock_base states; None asserts no restriction.
    allowed_resources: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Generator:
    """One buildable that GENERATES power (CS-1059).

    A SEPARATE namespace from :class:`Building`, joined by key, on the terms
    :attr:`Registry.extractors` states: every measured generator also declares
    an ``mPowerConsumption`` of ``'0.000000'``, so the same ClassName lands in
    both, and which role a caller wants is the caller's to pick by namespace.

    THE DECLARED SCALAR IS NOT ALWAYS THE OUTPUT. The geothermal generator
    declares ``mPowerProduction`` as ``'0.000000'`` and carries its real output
    on the variable fields. That zero is kept VERBATIM here - this layer
    reports the document and never rewrites it - and :attr:`is_variable_production`
    is what tells a consumer not to sum it. Summing it is the confident zero
    :attr:`Building.power_consumption` documents.

    Attributes:
        key: The entry's ClassName, the token a built count is keyed by.
        display_name: The verbatim mDisplayName from the buildable entry.
        power_production: mPowerProduction in megawatts as an exact Fraction,
            or None when the entry declares none or declares something
            unreadable. Never a defaulted zero.
        variable_production_constant: mVariablePowerProductionConstant, or
            None.
        variable_production_factor: mVariablePowerProductionFactor, or None.
        is_variable_production: True when either variable field is declared
            ABOVE zero, which is the measured shape of a generator whose output
            cycles rather than holds. A declared zero on both is not variable,
            for the reason :attr:`Building.is_variable_power` gives.
        accepted_fuels: CS-1285. The fuel ClassNames from ``mFuel``, in
            document order and deduplicated, or None - NEVER an empty tuple.
            None covers two different facts: an ABSENT ``mFuel``, which is
            silent and is the geothermal shape, and a present value that
            cannot be read WHOLE - not a list, an empty list, or any object
            whose fuel class is not a non-empty string - which is flagged
            ``WARN_UNREADABLE_FUELS`` under this generator's key. All or
            nothing, because a fuel dropped from a partly read list is supply
            a fuel audit never counts. A fuel naming no item descriptor is kept
            verbatim and flagged as an unknown item. The supplemental resource
            and the byproduct each object also carries are out of scope and
            are not read.
    """

    key: str
    display_name: str
    power_production: Fraction | None
    variable_production_constant: Fraction | None
    variable_production_factor: Fraction | None
    is_variable_production: bool
    # CS-1285. Appended with a default, for the reason
    # Building.unsharded_clock_base states; None asserts no fuel.
    accepted_fuels: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Recipe:
    """One production recipe, joined against items and buildings.

    Attributes:
        key: The entry's ClassName.
        display_name: The verbatim mDisplayName.
        duration: mManufactoringDuration as an exact Fraction, in seconds per
            cycle. A measured zero is kept; an ABSENT key causes the recipe to
            be flagged and skipped instead, because a defaulted zero is an
            infinite production rate reported with confidence.
        inputs: The normalized ingredient side, in source order.
        outputs: The normalized product side, in source order. Byproducts are
            here, and one of the two fractional fluid amounts in the whole
            document is one.
        produced_in: The ClassNames of the modeled buildings this recipe can
            be produced in, deduplicated, in source order. Empty means no
            automated producer - a hand-craft or build-gun recipe.
        variable_power_constant: mVariablePowerConsumptionConstant, or None.
            A RECIPE field, not a building field.
        variable_power_factor: mVariablePowerConsumptionFactor, or None.
        unresolved_produced_in: Tokens that named nothing this registry
            models, kept verbatim. Six of the seventeen measured tokens
            resolve to nothing, and erasing them would erase the evidence that
            the recipe was ever producible at all.
    """

    key: str
    display_name: str
    duration: Fraction
    inputs: tuple[RecipeIO, ...]
    outputs: tuple[RecipeIO, ...]
    produced_in: tuple[str, ...]
    variable_power_constant: Fraction | None
    variable_power_factor: Fraction | None
    unresolved_produced_in: tuple[str, ...] = ()


#: The empty, read-only extractor mapping :class:`Registry` defaults to.
#: Module-level so every default-constructed Registry shares one immutable
#: object rather than a fresh mutable dict.
_NO_EXTRACTORS: Final[Mapping[str, Extractor]] = MappingProxyType({})

#: The empty, read-only generator mapping, on the terms _NO_EXTRACTORS states.
_NO_GENERATORS: Final[Mapping[str, Generator]] = MappingProxyType({})


@dataclass(frozen=True)
class Registry:
    """The normalized model, plus everything the build refused to guess at.

    Attributes:
        items: Items by ClassName. Read-only.
        recipes: Production recipes by ClassName. Read-only.
        buildings: Power-consuming buildables by ClassName. Read-only.
        extractors: Resource extractors by ClassName, read-only. A SEPARATE
            namespace from ``buildings`` rather than a subset of it: an
            extractor is detected by its own fields and most extractors also
            draw power, so the same ClassName appears in both and the join is
            the key. One measured extractor entry carries no power field at
            all, which is why membership in one cannot be derived from the
            other.
        generators: Power generators by ClassName, read-only (CS-1059). A
            separate namespace joined by key, for the reason ``extractors``
            gives: every measured generator also declares a zero draw.
        warnings: Everything flagged and skipped, aggregated by subject and
            ordered deterministically so two builds of one document produce
            byte-identical output.
        unknown_groups: Short names of groups this build did not recognize.
            Deliberately excluded groups are NOT listed here.
        declared_classes: CS-1285. Every non-empty ClassName an entry of a
            RECOGNIZED group carries, whether or not any namespace models it -
            a schematic, a skipped recipe and a belt are declared too. An
            unknown group's entries are NOT declared: that group is flagged
            and skipped, and declaring its classes would vouch for content no
            probe has seen. A class outside this set is one the pinned docs
            do not know, which is the test a save-side consumer needs; the
            registry models only the classes that draw power, extract,
            generate, or are items or recipes.
        source_sha256: CS-1315. The lowercase hex sha256 of the docs bytes
            this registry was built from, computed as the pin computes its
            ``docs_sha256``, or None when it had no byte source - built from
            a loaded document or by hand. Recorded, never compared here.
    """

    items: Mapping[str, Item]
    recipes: Mapping[str, Recipe]
    buildings: Mapping[str, Building]
    warnings: tuple[RegistryWarning, ...]
    unknown_groups: tuple[str, ...]
    # Appended, and with a default, for the reason Building.unsharded_clock_base
    # states: a required field inserted mid-class breaks every positional
    # construction of a Registry at once. The default is an empty READ-ONLY
    # mapping, so a caller cannot mutate a shared default into existence.
    extractors: Mapping[str, Extractor] = _NO_EXTRACTORS
    generators: Mapping[str, Generator] = _NO_GENERATORS
    # CS-1285. Appended with a default on the same terms; a frozenset is
    # immutable, so one shared default is safe.
    declared_classes: frozenset[str] = frozenset()
    # CS-1315. Appended with a default on the same terms: None is "no byte
    # source", which the audit reads as unverified, never as a match.
    source_sha256: str | None = None


class _WarningLog:
    """Accumulates warnings, aggregating repeats by ``(code, subject)``."""

    def __init__(self) -> None:
        """Start an empty log."""
        self._counts: dict[tuple[str, str], int] = {}
        self._details: dict[tuple[str, str], str] = {}

    def add(self, code: str, subject: str, detail: str) -> None:
        """Record one occurrence.

        Args:
            code: One of the WARN_* constants.
            subject: What is being flagged.
            detail: One line naming the consequence. The first detail recorded
                for a subject is the one published; repeats only bump the
                count.
        """
        pair = (code, subject)
        self._counts[pair] = self._counts.get(pair, 0) + 1
        self._details.setdefault(pair, detail)

    def total(self, code: str) -> int:
        """Count every occurrence recorded under one code.

        Args:
            code: One of the WARN_* constants.

        Returns:
            The sum of the counts across every subject, which is the number of
            occurrences rather than the number of published warning rows.
        """
        return sum(count for (item, _subject), count in self._counts.items() if item == code)

    def emit(self) -> tuple[RegistryWarning, ...]:
        """Publish the accumulated warnings.

        Returns:
            One warning per ``(code, subject)``, sorted. Sorted rather than
            insertion-ordered because determinism is a product property: two
            runs over the same input must not differ, warnings included.
        """
        return tuple(
            RegistryWarning(code, subject, self._details[(code, subject)], count)
            for (code, subject), count in sorted(self._counts.items())
        )


def _text(entry: Mapping[str, object], key: str, subject: str, log: _WarningLog) -> str | None:
    """Read one field as a string, flagging a value that is present but is not one.

    1152 measured values are NOT strings, so this is a real branch rather than
    defensive decoration. The two outcomes must stay distinguishable: an absent
    key is silent, because most fields here are genuinely optional and absence
    is a meaningful reading, while a present non-string is content this build
    does not understand and is flagged. Collapsing the two would hide new game
    content behind the model's own "not present, therefore not applicable".

    Args:
        entry: The entry mapping.
        key: The field name.
        subject: The owning ClassName or group short name, for the warning.
        log: The warning log.

    Returns:
        The value, or None if the key is absent or its value is not a string.
    """
    value = entry.get(key)
    if isinstance(value, str):
        return value
    if value is not None:
        log.add(
            WARN_NON_STRING_VALUE,
            subject,
            f"{key} is present but is not a string; treated as unreadable, not as absent",
        )
    return None


def _fraction(text: str) -> Fraction | None:
    """Convert a decimal string straight to an exact Fraction.

    Straight, meaning never via ``float``. ``float`` of a shipped exponent
    string succeeds and silently substitutes the nearest binary approximation, which is a
    correctness bug in a ratio calculator rather than a rounding nuisance
    (non-negotiable 6).

    Args:
        text: The verbatim field value.

    Returns:
        The exact value, or None if the string is not a number.
    """
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        return None


def _optional_fraction(
    entry: Mapping[str, object],
    key: str,
    subject: str,
    log: _WarningLog,
) -> Fraction | None:
    """Read an optional numeric field.

    Args:
        entry: The entry mapping.
        key: The field name.
        subject: The owning ClassName, for the warning.
        log: The warning log.

    Returns:
        The exact value, or None when the key is absent or unparsable. An
        absent key is silent - most numeric fields here are genuinely
        optional - while an unparsable one is flagged.
    """
    text = _text(entry, key, subject, log)
    if text is None:
        return None
    value = _fraction(text)
    if value is None:
        log.add(WARN_UNPARSABLE_NUMBER, subject, f"{key} is not a number; treated as absent")
    return value


def _optional_flag(
    entry: Mapping[str, object],
    key: str,
    subject: str,
    log: _WarningLog,
) -> bool | None:
    """Read an optional boolean field against the document's two spellings (CS-1281).

    Args:
        entry: The entry mapping.
        key: The field name.
        subject: The owning ClassName, for the warning.
        log: The warning log.

    Returns:
        True or False for exactly ``'True'`` or ``'False'``, and None
        otherwise. An absent key is silent, on the rule
        :func:`_optional_fraction` states; a present non-string is flagged by
        :func:`_text`, and any other string is flagged here. Never a default.
    """
    text = _text(entry, key, subject, log)
    if text is None:
        return None
    value = _FLAG_SPELLINGS.get(text)
    if value is None:
        log.add(
            WARN_UNPARSABLE_FLAG,
            subject,
            f"{key} is neither True nor False; treated as unknown, never as either",
        )
    return value


def _sink_points(entry: Mapping[str, object], subject: str, log: _WarningLog) -> int | None:
    """Read mResourceSinkPoints, distinguishing absent from zero.

    Args:
        entry: The entry mapping.
        subject: The owning ClassName, for the warning.
        log: The warning log.

    Returns:
        The whole number of points, or None when the field is absent - which
        is measured on 191 of 2868 entries and on 4 of 122 item descriptors,
        and is a different fact from zero points.
    """
    text = _text(entry, KEY_SINK_POINTS, subject, log)
    if text is None:
        return None
    value = _fraction(text)
    if value is None or value.denominator != 1:
        log.add(
            WARN_UNPARSABLE_NUMBER,
            subject,
            f"{KEY_SINK_POINTS} is not a whole number; treated as absent",
        )
        return None
    return int(value)


def _class_name_from_path(path: str) -> str:
    """Reduce an Unreal object path to its trailing class token.

    Args:
        path: A path exactly as ``mProducedIn`` carried it.

    Returns:
        The token after the final ``.`` with any trailing single quote
        stripped, or the whole path when it carries no ``.`` at all. Two of
        the measured tokens have no separator, and returning the whole path
        keeps them visible as unresolvable rather than inventing a token.
    """
    return path.rsplit(".", 1)[-1].removesuffix("'")


def _display_name(
    entry: Mapping[str, object],
    group_name: str,
    log: _WarningLog,
) -> str:
    """Read mDisplayName, flagging an empty one.

    Args:
        entry: The entry mapping.
        group_name: The group's short name, which is the aggregation subject -
            all 547 building descriptors share one cause, and one warning per
            entry would bury every other finding.
        log: The warning log.

    Returns:
        The verbatim display name, or the empty string.
    """
    name = _text(entry, KEY_DISPLAY_NAME, group_name, log) or ""
    if not name:
        log.add(
            WARN_EMPTY_DISPLAY_NAME,
            group_name,
            f"{KEY_DISPLAY_NAME} is empty; a buildable's name is on its FGBuildable entry",
        )
    return name


def _entry_key(
    entry: Mapping[str, object],
    group_name: str,
    built: Mapping[str, object],
    log: _WarningLog,
) -> str | None:
    """Resolve the key one entry will be stored under, or refuse it.

    Args:
        entry: The entry mapping.
        group_name: The group's short name, for the warning.
        built: What has been built so far in this namespace, for the duplicate
            check.
        log: The warning log.

    Returns:
        The ClassName, or None when the entry has none or repeats one already
        taken. ClassName is unique across all 2868 measured entries, so a
        repeat is patch or mod content: the FIRST wins, matching
        ``index_by_short_name``. Last-wins would let mod content silently
        replace real content - and a redeclared form would rescale every
        amount referencing it.
    """
    key = _text(entry, KEY_CLASS_NAME, group_name, log)
    if not key:
        log.add(
            WARN_MISSING_CLASS_NAME,
            group_name,
            f"entry has no {KEY_CLASS_NAME}; it cannot be keyed or referenced",
        )
        return None
    if key in built:
        log.add(
            WARN_DUPLICATE_CLASS_NAME,
            key,
            "ClassName is declared more than once; keeping the first",
        )
        return None
    return key


def _item(entry: Mapping[str, object], key: str, group_name: str, log: _WarningLog) -> Item:
    """Build one item from its descriptor entry.

    Args:
        entry: The entry mapping.
        key: Its ClassName.
        group_name: The group's short name.
        log: The warning log.

    Returns:
        The item. A missing mForm is flagged because without it no amount
        referencing this item can be unit-normalized.
    """
    form = _text(entry, KEY_FORM, group_name, log)
    if form is None:
        log.add(
            WARN_MISSING_FORM,
            group_name,
            f"{KEY_FORM} is absent; amounts of these items cannot be unit-normalized",
        )
        form = ""
    return Item(
        key=key,
        display_name=_display_name(entry, group_name, log),
        form=form,
        energy_value=_optional_fraction(entry, KEY_ENERGY_VALUE, key, log),
        sink_points=_sink_points(entry, key, log),
        is_fluid=form in FLUID_FORMS,
    )


def _declared_power(
    entry: Mapping[str, object],
    subject: str,
    log: _WarningLog,
) -> tuple[Fraction | None, Fraction | None, Fraction | None]:
    """Read mPowerConsumption in all three of its measured shapes.

    Args:
        entry: The entry mapping.
        subject: The owning ClassName, for the warning.
        log: The warning log.

    Returns:
        ``(scalar draw, struct minimum, struct maximum)``. Exactly one of the
        first and the pair is ever populated: a decimal string yields the
        scalar, the struct string yields the bounds, and anything else yields
        three Nones and a flag. Never a zero - a draw that could not be read is
        not a draw of nothing, and the two are indistinguishable downstream.
    """
    text = _text(entry, KEY_POWER_CONSUMPTION, subject, log)
    if text is None:
        return None, None, None
    struct = _POWER_STRUCT_RE.match(text)
    if struct is not None:
        low = _fraction(struct.group(1))
        high = _fraction(struct.group(2))
        if low is None or high is None:
            log.add(
                WARN_UNPARSABLE_NUMBER,
                subject,
                f"{KEY_POWER_CONSUMPTION} is a range whose bounds are not numbers; "
                "treated as absent",
            )
            return None, None, None
        return None, low, high
    value = _fraction(text)
    if value is None:
        log.add(
            WARN_UNPARSABLE_NUMBER,
            subject,
            f"{KEY_POWER_CONSUMPTION} is not a number; treated as absent",
        )
    return value, None, None


def _building(entry: Mapping[str, object], key: str, group_name: str, log: _WarningLog) -> Building:
    """Build one building from its buildable entry.

    Args:
        entry: The entry mapping.
        key: Its ClassName.
        group_name: The group's short name.
        log: The warning log.

    Returns:
        The building. A declared scalar draw is reported as-is - it is
        genuinely zero on the variable-power buildings - and the estimated
        range beside it is what carries their real draw. A draw that is absent
        or unreadable is None rather than zero, and the struct shape supplies
        the range it names. The un-sharded clock base is read here too, and it
        is a base rather than a ceiling - see the module docstring. The group
        decides whether the entry is equipment (CS-1313).
    """
    power, struct_min, struct_max = _declared_power(entry, key, log)
    minimum = _optional_fraction(entry, KEY_ESTIMATED_MIN_POWER, key, log)
    maximum = _optional_fraction(entry, KEY_ESTIMATED_MAX_POWER, key, log)
    # Explicit None tests, never `or`: an estimated bound of Fraction(0) is
    # falsy and is a real measured value, so `minimum or struct_min` would
    # overwrite a declared zero with the struct's bound.
    if minimum is None:
        minimum = struct_min
    if maximum is None:
        maximum = struct_max
    if power is None and maximum is None:
        log.add(
            WARN_MISSING_POWER,
            key,
            f"no readable {KEY_POWER_CONSUMPTION} and no {KEY_ESTIMATED_MAX_POWER}; "
            "the draw is published as unknown rather than as zero",
        )
    return Building(
        key=key,
        display_name=_display_name(entry, group_name, log),
        power_consumption=power,
        power_exponent=_optional_fraction(entry, KEY_POWER_EXPONENT, key, log),
        estimated_min_power=minimum,
        estimated_max_power=maximum,
        is_variable_power=maximum is not None and maximum > 0,
        # Read through the same optional-numeric path as every other numeric
        # field, so a present-but-non-string value and an unparsable number are
        # flagged here exactly as they are everywhere else, rather than
        # collapsing into the "declared none" reading that None carries.
        unsharded_clock_base=_optional_fraction(entry, KEY_MAX_POTENTIAL, key, log),
        clockable=_optional_flag(entry, KEY_CAN_CHANGE_POTENTIAL, key, log),
        # CS-1313. By the GROUP the entry came from - see
        # EQUIPMENT_GROUP_SHORT_NAMES - and never by its class name's shape.
        is_equipment=group_name in EQUIPMENT_GROUP_SHORT_NAMES,
    )


def _flag_unknown_items(
    keys: Sequence[str],
    items: Mapping[str, Item],
    field: str,
    log: _WarningLog,
) -> None:
    """Flag every key that names no item descriptor (CS-1285).

    The same code a recipe side raises for the same gap, aggregated by the
    item's key, so one missing descriptor reads as one finding wherever it is
    referenced.

    Args:
        keys: Item ClassNames a field referenced.
        items: The items built so far.
        field: The referencing document key, for the detail.
        log: The warning log.
    """
    for key in keys:
        if key not in items:
            log.add(
                WARN_UNKNOWN_ITEM,
                key,
                f"no descriptor for this item; {field} keeps it verbatim with no knowable form",
            )


def _fuel_classes(value: object) -> tuple[str, ...] | None:
    """Read one mFuel value whole, or not at all (CS-1285).

    Args:
        value: The value exactly as the document carried it.

    Returns:
        The fuel ClassNames in document order, deduplicated, when ``value`` is
        a non-empty list of objects each carrying a non-empty string fuel
        class; None for every other shape. A partly readable list is None, not
        its readable subset.
    """
    if not isinstance(value, list | tuple) or not value:
        return None
    names: list[str] = []
    for fuel in value:
        if not isinstance(fuel, Mapping):
            return None
        name = fuel.get(KEY_FUEL_CLASS)
        if not isinstance(name, str) or not name:
            return None
        if name not in names:
            names.append(name)
    return tuple(names)


def _accepted_fuels(
    entry: Mapping[str, object],
    key: str,
    items: Mapping[str, Item],
    log: _WarningLog,
) -> tuple[str, ...] | None:
    """Read a generator's accepted fuels out of mFuel (CS-1285).

    Not read through :func:`_text`: a list is mFuel's measured shape, so the
    present-but-not-a-string flag every scalar field raises would be a false
    alarm here. Presence is tested on the KEY, so a value present as JSON null
    is unreadable rather than absent.

    Args:
        entry: The entry mapping.
        key: The generator's ClassName, the warning subject.
        items: The items built so far, for the unknown-item flag.
        log: The warning log.

    Returns:
        The fuels, or None when mFuel is absent (silent) or unreadable
        (flagged). Never an empty tuple.
    """
    if KEY_FUEL not in entry:
        return None
    fuels = _fuel_classes(entry[KEY_FUEL])
    if fuels is None:
        log.add(
            WARN_UNREADABLE_FUELS,
            key,
            f"{KEY_FUEL} is present but is not a non-empty list of objects each naming a "
            f"{KEY_FUEL_CLASS}; the accepted fuels are published as unknown, never as none",
        )
        return None
    _flag_unknown_items(fuels, items, KEY_FUEL, log)
    return fuels


def _generator(
    entry: Mapping[str, object],
    key: str,
    group_name: str,
    items: Mapping[str, Item],
    log: _WarningLog,
) -> Generator:
    """Build one generator from its buildable entry (CS-1059).

    Args:
        entry: The entry mapping.
        key: Its ClassName.
        group_name: The group's short name.
        items: The items built so far, for the accepted fuels' join.
        log: The warning log.

    Returns:
        The generator. A scalar that is absent or unreadable is None and is
        flagged unless the entry is variable, whose output the scalar never
        carried anyway. Its accepted fuels are read on the terms
        :attr:`Generator.accepted_fuels` states.
    """
    production = _optional_fraction(entry, KEY_POWER_PRODUCTION, key, log)
    constant = _optional_fraction(entry, KEY_VARIABLE_PRODUCTION_CONSTANT, key, log)
    factor = _optional_fraction(entry, KEY_VARIABLE_PRODUCTION_FACTOR, key, log)
    variable = any(value is not None and value > 0 for value in (constant, factor))
    if production is None and not variable:
        log.add(
            WARN_MISSING_PRODUCTION,
            key,
            f"no readable {KEY_POWER_PRODUCTION} and no variable production; "
            "the output is published as unknown rather than as zero",
        )
    return Generator(
        key=key,
        display_name=_display_name(entry, group_name, log),
        power_production=production,
        variable_production_constant=constant,
        variable_production_factor=factor,
        is_variable_production=variable,
        accepted_fuels=_accepted_fuels(entry, key, items, log),
    )


def _unwrap_outer_parens(text: str) -> str:
    """Remove ONE enclosing layer of parentheses, and only a real one.

    The measured mAllowedResourceForms values are wrapped end to end -
    ``(RF_SOLID)``, ``(RF_LIQUID,RF_GAS)`` - so the wrapper has to come off
    before anything can be split. The depth scan is what makes this safe on a
    value whose first ``(`` closes before the end: a blind ``text[1:-1]`` on a
    hypothetical ``(A),(B)`` yields ``A),(B``, which then splits into two
    tokens that are each half of a group and look like content.

    Args:
        text: The verbatim field value.

    Returns:
        The stripped body when the leading parenthesis is closed by the
        trailing one, and the whitespace-stripped value verbatim otherwise -
        including when the parentheses are unbalanced, which is content this
        build does not understand rather than content to repair.
    """
    body = text.strip()
    if not (body.startswith("(") and body.endswith(")")):
        return body
    depth = 0
    for index, character in enumerate(body):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return body[1:-1] if index == len(body) - 1 else body
    return body


def _split_form_tokens(text: str) -> tuple[str, ...]:
    """Split one mAllowedResourceForms value into its tokens.

    Depth-aware, so a nested group stays ONE token. The only measured nesting
    holds a single token - ``(INVALID)`` - which a plain ``str.split(",")``
    also gets right, by luck rather than by rule; a nested ``(A,B)`` would
    arrive as ``(A`` and ``B)``, two unbalanced fragments that each look like a
    form token nobody recognizes. Keeping the group whole is what lets the
    caller report one unknown token instead of two invented ones.

    Args:
        text: The verbatim field value.

    Returns:
        The tokens, in source order, each whitespace-stripped. Empty tokens are
        dropped: a trailing separator is punctuation rather than content.
    """
    tokens: list[str] = []
    current: list[str] = []
    depth = 0
    for character in _unwrap_outer_parens(text):
        if character == "," and depth == 0:
            tokens.append("".join(current))
            current = []
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            # Clamped, never negative: an unbalanced value must still terminate
            # this scan with every later comma treated as a separator.
            depth = max(depth - 1, 0)
        current.append(character)
    tokens.append("".join(current))
    return tuple(stripped for token in tokens if (stripped := token.strip()))


def _resource_forms(
    entry: Mapping[str, object],
    subject: str,
    log: _WarningLog,
) -> tuple[frozenset[str], tuple[str, ...]]:
    """Read mAllowedResourceForms against the closed form vocabulary.

    Args:
        entry: The entry mapping.
        subject: The owning ClassName, for the warning.
        log: The warning log.

    Returns:
        A ``(recognized, unrecognized)`` pair. The first holds only tokens in
        RESOURCE_FORMS; the second holds every other token verbatim, in source
        order and deduplicated, and each occurrence is flagged. An absent key
        yields two empties and no flag - an entry that declares no form
        declares none - while a token this build does not know is new content
        and is never guessed at (non-negotiable 7).
    """
    text = _text(entry, KEY_ALLOWED_RESOURCE_FORMS, subject, log)
    if text is None:
        return frozenset(), ()
    recognized: list[str] = []
    unrecognized: list[str] = []
    for token in _split_form_tokens(text):
        if token in RESOURCE_FORMS:
            recognized.append(token)
            continue
        # The detail names the field and the consequence and never the token -
        # diagnostics in this module do not echo document content.
        log.add(
            WARN_UNKNOWN_RESOURCE_FORM,
            subject,
            f"{KEY_ALLOWED_RESOURCE_FORMS} carries a token outside the recognized form "
            "vocabulary; it is kept verbatim and excluded from the allowed set",
        )
        if token not in unrecognized:
            unrecognized.append(token)
    return frozenset(recognized), tuple(unrecognized)


def _allowed_resources(
    entry: Mapping[str, object],
    key: str,
    items: Mapping[str, Item],
    log: _WarningLog,
) -> tuple[str, ...] | None:
    """Read a restricted extractor's resource list (CS-1285).

    Args:
        entry: The entry mapping.
        key: The extractor's ClassName, the warning subject.
        items: The items built so far, for the unknown-item flag.
        log: The warning log.

    Returns:
        The resource ClassNames in source order, deduplicated, when the flag
        reads exactly 'True' and the list reads whole; None otherwise. The flag
        gates the list: an unrestricted extractor's list is not read at all,
        so a non-empty one beside a 'False' asserts nothing. A restricted entry
        whose list is absent, empty, not a string, outside the class-path
        grammar or carrying an empty token is flagged and is None - never an
        empty tuple, which would claim the extractor yields nothing. The
        parse error's text is not echoed: it quotes document content.
    """
    if _optional_flag(entry, KEY_ONLY_ALLOW_CERTAIN_RESOURCES, key, log) is not True:
        return None
    text = _text(entry, KEY_ALLOWED_RESOURCES, key, log)
    try:
        paths = parse_class_paths(text) if text else ()
    except BlobParseError:
        paths = ()
    tokens = [_class_name_from_path(path) for path in paths]
    if not tokens or not all(tokens):
        log.add(
            WARN_UNREADABLE_ALLOWED_RESOURCES,
            key,
            f"{KEY_ONLY_ALLOW_CERTAIN_RESOURCES} restricts this extractor but "
            f"{KEY_ALLOWED_RESOURCES} names no readable resource list; the restriction is "
            "published as unknown, never as none",
        )
        return None
    resources = tuple(dict.fromkeys(tokens))
    _flag_unknown_items(resources, items, KEY_ALLOWED_RESOURCES, log)
    return resources


def _extractor(
    entry: Mapping[str, object],
    key: str,
    group_name: str,
    items: Mapping[str, Item],
    log: _WarningLog,
) -> Extractor:
    """Build one extractor from its buildable entry.

    Args:
        entry: The entry mapping.
        key: Its ClassName.
        group_name: The group's short name.
        items: The items built so far, for the resource list's join.
        log: The warning log.

    Returns:
        The extractor. Either rate operand may be None - absent, unparsable or
        present-but-not-a-string - and a None is never replaced by a number,
        because a rate of zero is a throughput claim the document did not make.
        Both operands are needed for a throughput, so either one missing is
        flagged, which is the same shape as WARN_MISSING_POWER firing alongside
        the unparsable-number flag that explains it. Its resource restriction
        is read on the terms :attr:`Extractor.allowed_resources` states.
    """
    items_per_cycle = _optional_fraction(entry, KEY_ITEMS_PER_CYCLE, key, log)
    cycle_time = _optional_fraction(entry, KEY_EXTRACT_CYCLE_TIME, key, log)
    allowed, unrecognized = _resource_forms(entry, key, log)
    if items_per_cycle is None or cycle_time is None:
        log.add(
            WARN_MISSING_EXTRACTION_RATE,
            key,
            f"no readable {KEY_ITEMS_PER_CYCLE} and {KEY_EXTRACT_CYCLE_TIME} pair; the "
            "throughput is published as unknown rather than as zero",
        )
    return Extractor(
        key=key,
        display_name=_display_name(entry, group_name, log),
        items_per_cycle=items_per_cycle,
        extract_cycle_time=cycle_time,
        allowed_forms=allowed,
        unrecognized_forms=unrecognized,
        allowed_resources=_allowed_resources(entry, key, items, log),
    )


def _recipe_io(amount: ItemAmount, items: Mapping[str, Item], log: _WarningLog) -> RecipeIO:
    """Normalize one parsed item-amount against the item's form.

    Args:
        amount: The verbatim parsed entry.
        items: The items built so far.
        log: The warning log.

    Returns:
        The normalized side. A fluid's litres become exact cubic metres. A
        solid and an RF_INVALID building descriptor are counts and are not
        divided. An item with no descriptor has no knowable unit, so its
        amount is left verbatim and the gap is flagged rather than guessed.
    """
    item = items.get(amount.item_key)
    if item is None:
        log.add(
            WARN_UNKNOWN_ITEM,
            amount.item_key,
            "no descriptor for this item; its amount is left unconverted",
        )
        return RecipeIO(item_key=amount.item_key, amount=Fraction(amount.amount))
    if item.is_fluid:
        return RecipeIO(
            item_key=amount.item_key,
            amount=Fraction(amount.amount, LITRES_PER_CUBIC_METRE),
        )
    return RecipeIO(item_key=amount.item_key, amount=Fraction(amount.amount))


def _recipe_side(
    entry: Mapping[str, object],
    key: str,
    field: str,
    items: Mapping[str, Item],
    log: _WarningLog,
) -> tuple[RecipeIO, ...]:
    """Parse and normalize one side of a recipe, cross-checking the parse.

    Args:
        entry: The recipe entry.
        key: The recipe's ClassName.
        field: KEY_INGREDIENTS or KEY_PRODUCT.
        items: The items built so far.
        log: The warning log.

    Returns:
        The normalized side, in source order. An empty blob yields an empty
        tuple: 6 measured recipes genuinely have no ingredients, so empty is a
        real value rather than an absent one. A missing key is treated the
        same way, since nothing downstream could act on the difference.

    Raises:
        BlobParseError: The blob does not match the measured grammar end to
            end. The caller flags and skips the whole recipe rather than
            accepting a short ingredient list, and counts the refusal - see
            :func:`_assert_grammar_intact`.
        RegistryIntegrityError: The parser and the independent marker count
            disagree. Signal 1 of the three in the module docstring.
    """
    blob = _text(entry, field, key, log) or ""
    # The count is taken BEFORE the parse, so it is a reading of the raw blob
    # rather than of whatever survived parsing it.
    markers = marker_count(blob)
    parsed = parse_item_amounts(blob)
    if markers != len(parsed):
        raise RegistryIntegrityError(
            f"{key} {field}: the item-amount parser accounted for {len(parsed)} entries "
            f"while the independent marker count found {markers}; the shipped grammar "
            "has changed and a silently short ingredient list is the alternative"
        )
    return tuple(_recipe_io(amount, items, log) for amount in parsed)


def _produced_in(
    entry: Mapping[str, object],
    key: str,
    buildings: Mapping[str, Building],
    log: _WarningLog,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Resolve mProducedIn tokens against the modeled buildings.

    Args:
        entry: The recipe entry.
        key: The recipe's ClassName, for the warning.
        buildings: The buildings built so far.
        log: The warning log.

    Returns:
        A ``(resolved, unresolved)`` pair, each deduplicated and in source
        order. Six of the seventeen measured tokens resolve to nothing - the
        build gun, two bench components and two ``/Script/`` engine references,
        one of which carries no ``.`` separator - and every one of them is
        tolerated, flagged and preserved rather than dropped.

    Raises:
        BlobParseError: The blob does not match the class-path grammar.
    """
    resolved: list[str] = []
    unresolved: list[str] = []
    for path in parse_class_paths(_text(entry, KEY_PRODUCED_IN, key, log) or ""):
        token = _class_name_from_path(path)
        if token in buildings:
            if token not in resolved:
                resolved.append(token)
            continue
        log.add(
            WARN_UNRESOLVED_PRODUCED_IN,
            token,
            "produced-in token names no modeled building; the recipe is kept unautomated",
        )
        if token not in unresolved:
            unresolved.append(token)
    return tuple(resolved), tuple(unresolved)


def _recipe(
    entry: Mapping[str, object],
    key: str,
    items: Mapping[str, Item],
    buildings: Mapping[str, Building],
    log: _WarningLog,
) -> Recipe | None:
    """Build one recipe, or refuse it and say why.

    Args:
        entry: The recipe entry.
        key: Its ClassName.
        items: The items built so far.
        buildings: The buildings built so far.
        log: The warning log.

    Returns:
        The recipe, or None when it was flagged and skipped. Two conditions
        skip: a duration key that is absent or unparsable, because a defaulted
        zero is an infinite production rate; and a blob that does not match the
        measured grammar, because the alternative is a short ingredient list
        that no downstream test can tell from a correct one.

    Raises:
        RegistryIntegrityError: The parser and the marker count disagree.
    """
    duration_text = _text(entry, KEY_DURATION, key, log)
    duration = _fraction(duration_text) if duration_text is not None else None
    if duration is None:
        log.add(
            WARN_MISSING_DURATION,
            key,
            f"{KEY_DURATION} is absent or not a number; skipped rather than defaulted to zero",
        )
        return None
    try:
        inputs = _recipe_side(entry, key, KEY_INGREDIENTS, items, log)
        outputs = _recipe_side(entry, key, KEY_PRODUCT, items, log)
        produced_in, unresolved = _produced_in(entry, key, buildings, log)
    except BlobParseError:
        # The message carries a blob excerpt, so it is deliberately not echoed
        # into the warning - diagnostics here name fields and counts, never
        # document content.
        log.add(
            WARN_MALFORMED_BLOB,
            key,
            "a blob did not match the measured grammar; the whole recipe is skipped",
        )
        return None
    return Recipe(
        key=key,
        display_name=_text(entry, KEY_DISPLAY_NAME, key, log) or "",
        duration=duration,
        inputs=inputs,
        outputs=outputs,
        produced_in=produced_in,
        variable_power_constant=_optional_fraction(entry, KEY_VARIABLE_POWER_CONSTANT, key, log),
        variable_power_factor=_optional_fraction(entry, KEY_VARIABLE_POWER_FACTOR, key, log),
        unresolved_produced_in=unresolved,
    )


def _is_item_entry(entry: Mapping[str, object], group_name: str) -> bool:
    """Decide whether one entry is an item descriptor.

    Args:
        entry: The entry mapping.
        group_name: Its group's short name.

    Returns:
        True when the entry carries mForm - which is what makes it a descriptor
        and is what makes its unit knowable - or when it sits in one of the
        measured descriptor groups. The second half is a floor and never a
        filter: an entry in a group nobody listed is still an item if it
        carries the field, and an entry in a listed group is still an item if a
        patch ships it without one, in which case :func:`_item` flags the gap.
    """
    return KEY_FORM in entry or group_name in ITEM_GROUP_SHORT_NAMES


def _is_building_entry(entry: Mapping[str, object]) -> bool:
    """Decide whether one entry is a power-consuming buildable.

    Args:
        entry: The entry mapping.

    Returns:
        True when the entry carries either power field. There is deliberately
        no group floor here: power is the entire content of a Building, so an
        entry carrying neither field has nothing to model, and admitting one
        would publish a draw the document never stated. Nothing is lost by
        leaving it out - the same entry is still an item if it carries mForm,
        and a recipe naming it still reports it as an unresolved producer.
    """
    return any(marker in entry for marker in POWER_MARKER_KEYS)


def _is_extractor_entry(entry: Mapping[str, object]) -> bool:
    """Decide whether one entry is a resource extractor.

    Args:
        entry: The entry mapping.

    Returns:
        True when the entry carries ANY of EXTRACTION_MARKER_KEYS. Any-of
        rather than all-of is measured, not lenient: 2 of the 8 entries that
        declare allowed resource forms declare no rate at all, and requiring
        the rate would drop them from a model whose whole subject is which
        buildings extract what. There is no group floor here either, for the
        reason :func:`_is_building_entry` states.
    """
    return any(marker in entry for marker in EXTRACTION_MARKER_KEYS)


def _is_generator_entry(entry: Mapping[str, object]) -> bool:
    """Decide whether one entry is a power generator (CS-1059).

    Args:
        entry: The entry mapping.

    Returns:
        True when the entry carries ANY of GENERATION_MARKER_KEYS.
    """
    return any(marker in entry for marker in GENERATION_MARKER_KEYS)


def _build_items(groups: Sequence[DocsGroup], log: _WarningLog) -> dict[str, Item]:
    """Build every item, in document order.

    Args:
        groups: The recognized groups.
        log: The warning log.

    Returns:
        Items by ClassName.
    """
    items: dict[str, Item] = {}
    for group in groups:
        for entry in group.entries:
            if not _is_item_entry(entry, group.short_name):
                continue
            key = _entry_key(entry, group.short_name, items, log)
            if key is not None:
                items[key] = _item(entry, key, group.short_name, log)
    return items


def _build_buildings(groups: Sequence[DocsGroup], log: _WarningLog) -> dict[str, Building]:
    """Build every power-consuming buildable, in document order.

    Args:
        groups: The recognized groups.
        log: The warning log.

    Returns:
        Buildings by ClassName.
    """
    buildings: dict[str, Building] = {}
    for group in groups:
        for entry in group.entries:
            if not _is_building_entry(entry):
                continue
            key = _entry_key(entry, group.short_name, buildings, log)
            if key is not None:
                buildings[key] = _building(entry, key, group.short_name, log)
    return buildings


def _build_extractors(
    groups: Sequence[DocsGroup],
    items: Mapping[str, Item],
    log: _WarningLog,
) -> dict[str, Extractor]:
    """Build every resource extractor, in document order.

    Args:
        groups: The recognized groups.
        items: The built items, for the resource lists' join.
        log: The warning log.

    Returns:
        Extractors by ClassName. This is its own namespace, so an entry that is
        both a power consumer and an extractor is built twice, once per model,
        under one key - and a duplicate ClassName inside THIS namespace is
        flagged by :func:`_entry_key` exactly as it is for the others.
    """
    extractors: dict[str, Extractor] = {}
    for group in groups:
        for entry in group.entries:
            if not _is_extractor_entry(entry):
                continue
            key = _entry_key(entry, group.short_name, extractors, log)
            if key is not None:
                extractors[key] = _extractor(entry, key, group.short_name, items, log)
    return extractors


def _build_generators(
    groups: Sequence[DocsGroup],
    items: Mapping[str, Item],
    log: _WarningLog,
) -> dict[str, Generator]:
    """Build every power generator, in document order (CS-1059).

    Args:
        groups: The recognized groups.
        items: The built items, for the accepted fuels' join.
        log: The warning log.

    Returns:
        Generators by ClassName, in their own namespace.
    """
    generators: dict[str, Generator] = {}
    for group in groups:
        for entry in group.entries:
            if not _is_generator_entry(entry):
                continue
            key = _entry_key(entry, group.short_name, generators, log)
            if key is not None:
                generators[key] = _generator(entry, key, group.short_name, items, log)
    return generators


def _declared_classes(groups: Sequence[DocsGroup]) -> frozenset[str]:
    """Collect every ClassName the recognized groups declare (CS-1285).

    No warning is raised here: an entry with no usable ClassName is flagged by
    the namespace pass that would have keyed it, and this pass adds no second
    count of the same entry.

    Args:
        groups: The recognized groups ONLY - the unknown ones are flagged and
            skipped, and declaring their classes would vouch for them.

    Returns:
        Every non-empty string ClassName, modeled by a namespace or not.
    """
    return frozenset(
        name
        for group in groups
        for entry in group.entries
        if isinstance(name := entry.get(KEY_CLASS_NAME), str) and name
    )


def _build_recipes(
    groups: Sequence[DocsGroup],
    items: Mapping[str, Item],
    buildings: Mapping[str, Building],
    log: _WarningLog,
) -> dict[str, Recipe]:
    """Build every production recipe, in document order.

    Args:
        groups: The recognized groups.
        items: The built items.
        buildings: The built buildings.
        log: The warning log.

    Returns:
        Recipes by ClassName. Only groups named in RECIPE_GROUP_SHORT_NAMES
        are read - FGCustomizationRecipe carries the same 13 keys and would
        pass any shape test.
    """
    recipes: dict[str, Recipe] = {}
    for group in groups:
        if group.short_name not in RECIPE_GROUP_SHORT_NAMES:
            continue
        for entry in group.entries:
            key = _entry_key(entry, group.short_name, recipes, log)
            if key is None:
                continue
            recipe = _recipe(entry, key, items, buildings, log)
            if recipe is not None:
                recipes[key] = recipe
    return recipes


def _recipe_entry_count(groups: Sequence[DocsGroup]) -> int:
    """Count the entries the recipe pass was offered.

    Args:
        groups: The recognized groups.

    Returns:
        How many entries live in the recipe groups, before any of them was
        parsed. Counted from the document rather than inferred from what
        survived, because the whole question below is how many did not.
    """
    return sum(
        len(group.entries) for group in groups if group.short_name in RECIPE_GROUP_SHORT_NAMES
    )


def _assert_grammar_intact(offered: int, built: int, log: _WarningLog) -> None:
    """Escalate a pattern of skipped recipes into a fatal grammar change.

    Signals 2 and 3 of the three in the module docstring, and the two that
    actually reach the ordinary patch shape. Per-recipe flag-and-skip is
    correct for damaged content and is exactly wrong for a moved grammar: it
    turns 872 refusals into 872 orderly skips and an empty registry with a zero
    exit. Neither test can be made per-recipe, because at that scale every
    single refusal still looks like one bad row.

    The threshold is a NOISE FLOOR, not a tolerance: the pinned build produces
    zero malformed blobs and the synthetic corpus produces one, while a grammar
    change produces every recipe in the document at once. There is no measured
    shape in between that is not itself a finding.

    Args:
        offered: How many entries the recipe groups carried.
        built: How many recipes survived.
        log: The warning log, read for the malformed-blob count.

    Raises:
        RegistryIntegrityError: Too many blobs were refused, or a non-empty
            recipe group produced nothing at all.
    """
    refused = log.total(WARN_MALFORMED_BLOB)
    if refused > MAX_MALFORMED_BLOBS:
        raise RegistryIntegrityError(
            f"{refused} recipe blobs did not match the measured grammar, over a threshold of "
            f"{MAX_MALFORMED_BLOBS}; that is the shipped grammar changing rather than a few "
            "damaged entries, and every ratio built from the survivors would be a guess"
        )
    if offered and not built:
        raise RegistryIntegrityError(
            f"the recipe groups carried {offered} entries and produced no recipes at all; "
            "an empty registry from a non-empty document is a grammar change, and publishing "
            "it would be a factory plan with nothing in it and a zero exit code"
        )


def _unknown_groups(document: DocsDocument, log: _WarningLog) -> tuple[str, ...]:
    """Collect the groups this build did not recognize, and flag them.

    Args:
        document: The loaded document.
        log: The warning log.

    Returns:
        The unrecognized short names in document order. Groups this build
        recognizes and deliberately does not model are NOT included; see
        UNMODELED_GROUP_SHORT_NAMES for why.
    """
    names = tuple(document.unknown_short_names)
    for name in names:
        log.add(
            WARN_UNKNOWN_GROUP,
            name,
            "group is outside every known role; parsed, published and not modeled",
        )
    return names


def build_registry(document: DocsDocument) -> Registry:
    """Join a loaded docs document into the normalized model.

    The join order is forced: items first, because a recipe amount cannot be
    unit-converted before the item's form is known; buildings next, because a
    produced-in token cannot be resolved before they exist; recipes last.

    Args:
        document: A document already loaded by
            :func:`~clockspeed.data.docs_extract.load_document`. This module
            never opens a file and never locates an install, which is what
            lets the whole model be tested with no game present.

    Returns:
        The registry, including everything that was flagged and skipped.

    Raises:
        RegistryIntegrityError: The shipped item-amount grammar has changed.
            Three signals raise it - a blob whose parse disagrees with the
            independent marker count, more than MAX_MALFORMED_BLOBS refused
            blobs, and a non-empty recipe group that produced no recipes - and
            the module docstring says why one of them is not enough.
    """
    log = _WarningLog()
    for skipped in document.malformed:
        log.add(WARN_MALFORMED_GROUP, str(skipped.index), skipped.reason)
    unknown = _unknown_groups(document, log)
    items = _build_items(document.groups, log)
    buildings = _build_buildings(document.groups, log)
    extractors = _build_extractors(document.groups, items, log)
    generators = _build_generators(document.groups, items, log)
    recipes = _build_recipes(document.groups, items, buildings, log)
    _assert_grammar_intact(_recipe_entry_count(document.groups), len(recipes), log)
    return Registry(
        items=MappingProxyType(items),
        recipes=MappingProxyType(recipes),
        buildings=MappingProxyType(buildings),
        warnings=log.emit(),
        unknown_groups=unknown,
        extractors=MappingProxyType(extractors),
        generators=MappingProxyType(generators),
        declared_classes=_declared_classes(document.groups),
    )


def build_registry_from_bytes(raw: bytes) -> Registry:
    """Build the registry from the docs file's raw bytes, recording their sha256.

    PURE: no file is opened and no install is located - the caller hands the
    bytes over. The decode and the load are ``docs_extract``'s own, so the
    model is exactly :func:`build_registry`'s over the same document, plus
    :attr:`Registry.source_sha256`.

    Args:
        raw: The complete docs file contents, exactly ``bytes``.

    Returns:
        The registry, carrying the sha256 of ``raw`` - the bytes, never the
        decoded text, as the pin hashes them.

    Raises:
        TypeError: ``raw`` is not exactly ``bytes``. A decoded text has no byte
            source to hash, and a mutable buffer could change between the
            hash and the decode.
        DocsDecodeError: The bytes did not decode under their sniffed encoding.
        DocsStructureError: The decoded text is not a JSON list of groups.
        RegistryIntegrityError: As :func:`build_registry` raises it.
    """
    if type(raw) is not bytes:
        raise TypeError("docs bytes must be exactly bytes, not " + type(raw).__name__)
    built = build_registry(load_document(decode_docs_bytes(raw)))
    return replace(built, source_sha256=hashlib.sha256(raw).hexdigest())


def automated_recipes(registry: Registry) -> tuple[Recipe, ...]:
    """Select the recipes an automated production building can make.

    The filter is on mProducedIn, never on group membership: all 872 measured
    recipes are in one group and only 291 name a production building. Nor is
    it an exclusion test on hand-craft tokens - 76 of those 291 name one
    alongside a real manufacturer, so excluding them would lose 76 genuinely
    automated recipes. A recipe qualifies when at least one of its tokens
    resolved to a modeled building.

    Args:
        registry: The built registry.

    Returns:
        The automated recipes, in registry order.
    """
    return tuple(recipe for recipe in registry.recipes.values() if recipe.produced_in)


#: The substring every measured build-gun producer token carries. It is a
#: MARKER rather than a transcription on purpose: the pinned build ships
#: ``BP_BuildGun_C`` on 549 recipes and ``FGBuildGun`` on exactly one, and a
#: selector written against the common spelling alone loses that recipe and
#: reports the building it costs as one the game ships no cost for. CS-930
#: measured that miss before the seam below was written.
BUILD_GUN_MARKER: Final = "BuildGun"

#: The class-name prefix a modeled buildable usually carries.
BUILDABLE_PREFIX: Final = "Build_"

#: The class-name prefix the building DESCRIPTOR carries - the item a build-gun
#: recipe actually produces.
DESCRIPTOR_PREFIX: Final = "Desc_"


@dataclass(frozen=True)
class BuildCost:
    """What one buildable costs to place, and where that came from.

    Attributes:
        building_key: The modeled buildable's ClassName.
        recipe_key: The build-gun recipe the cost was read off. Carried rather
            than discarded so a caller can cite the join instead of asserting
            it - the descriptor entry holds no pointer back to the buildable,
            so this seam is a name join and its provenance is the only thing
            that makes it auditable.
        ingredients: The recipe's ingredient side verbatim, in source order,
            with exact Fraction amounts.
    """

    building_key: str
    recipe_key: str
    ingredients: tuple[RecipeIO, ...]


def _descriptor_key(building_key: str) -> str:
    """Name the descriptor a build-gun recipe would produce for a buildable.

    ``Build_X_C`` takes ``Desc_X_C``. Anything else takes ITSELF, and that
    branch is measured rather than a fallback: two modeled buildables carry
    neither prefix, and one of them is already spelled ``Desc_`` with a recipe
    producing exactly that key. The other reaches nothing, which is the honest
    answer - the document ships no build recipe for it under any spelling.

    Args:
        building_key: The modeled buildable's ClassName.

    Returns:
        The product ClassName to look for.
    """
    if building_key.startswith(BUILDABLE_PREFIX):
        return DESCRIPTOR_PREFIX + building_key[len(BUILDABLE_PREFIX) :]
    return building_key


def build_gun_recipes(registry: Registry) -> tuple[Recipe, ...]:
    """Select the recipes placed with the build gun rather than by a machine.

    The filter is on the UNRESOLVED producer tokens, because the build gun is
    not a modeled building and never resolves. It is the complement of
    :func:`automated_recipes` in practice - no measured build-gun recipe also
    names a modeled producer - but it is not defined as one: a recipe naming
    both would be automated AND buildable, and defining this by subtraction
    would silently pick a side.

    Args:
        registry: The built registry.

    Returns:
        The build-gun recipes, in registry order.

    """
    return tuple(
        recipe
        for recipe in registry.recipes.values()
        if any(BUILD_GUN_MARKER in token for token in recipe.unresolved_produced_in)
    )


def build_cost(registry: Registry, building_key: str) -> BuildCost | None:
    """Read what a modeled buildable costs to place.

    Args:
        registry: The built registry.
        building_key: A ClassName that MUST name a modeled building.

    Returns:
        The cost, or None when no build-gun recipe produces this buildable's
        descriptor. None is not an empty cost and must never be rendered as a
        free building: the measured misses are a descriptor shipped under a
        third name and a buildable the document carries no build recipe for,
        and neither means the game charges nothing.

    Raises:
        KeyError: If ``building_key`` names no modeled building. That is a
            different answer from "no cost known" and does not share its
            return value.
    """
    if building_key not in registry.buildings:
        raise KeyError(building_key)
    wanted = _descriptor_key(building_key)
    for recipe in build_gun_recipes(registry):
        if any(product.item_key == wanted for product in recipe.outputs):
            return BuildCost(
                building_key=building_key,
                recipe_key=recipe.key,
                ingredients=recipe.inputs,
            )
    return None


def buildings_without_build_cost(registry: Registry) -> tuple[str, ...]:
    """List the modeled buildables no build-gun recipe reaches.

    This is the flag half of :func:`build_cost` (non-negotiable 7): a caller
    that wants a total has to know which members it could not price, and a
    None returned one at a time is easy to swallow silently.

    Args:
        registry: The built registry.

    Returns:
        The unpriced buildables' ClassNames, in registry order.
    """
    return tuple(key for key in registry.buildings if build_cost(registry, key) is None)
