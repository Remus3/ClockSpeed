"""The hand-authored synthetic docs corpus the data-layer tests build on.

WHY THIS FILE EXISTS AT ALL
---------------------------
The CS-200 acceptance criterion is that the data-layer suite runs green on a
machine that has never had the game installed. A fixture cut from the real
``en-US.json`` fails that gate on the first line, and it fails two more rules
besides: publisher-owned data assets are never tracked (CONVENTIONS.md section
14) and the real display strings carry U+2014, smart quotes and U+202F, which
the character-set gate would correctly block. So every byte below is invented.

WHY THE GROUP NAMES ARE REAL BUT NOTHING ELSE IS
------------------------------------------------
``NativeClass`` short names are the join keys the registry dispatches on, so a
corpus using invented group names would exercise the dispatch against nothing
and pass. They are also not content: ``FGRecipe`` is a class name in the
game's own code, carries no personal data and appears already in
``clockspeed/data/docs_extract.py``. Every ClassName, path, display name and
number below is synthetic.

WHY THE KEY SPELLINGS ARE LITERALS HERE AND NOT IMPORTED FROM THE REGISTRY
--------------------------------------------------------------------------
Two of the keys are MISSPELLED in the shipped game data -
``mManufactoringDuration`` (sitting beside the correctly spelled
``mManufacturingMenuPriority`` in the same record) and
``mEstimatedMininumPowerConsumption``. Importing the registry's own constants
into this corpus would mean an autocomplete-driven "correction" in the
registry silently corrected the fixture too, and the suite would stay green
through exactly the defect it exists to catch. CONVENTIONS.md section 7.2:
fixtures built parallel to the implementation stay green through the real
defect. So the keys are spelled out here, and
``tests/data/test_registry.py`` asserts the registry's constants match these
literals.

WHAT THE CORPUS DELIBERATELY CONTAINS
-------------------------------------
Every shape measured in BOOTSTRAP.md section 3.2 that breaks a normalizer
which passes its own tests:

- a solid-only recipe, and one carrying a fractional fluid on BOTH sides -
  an ingredient at 2500 and a byproduct at 1500, which is where the only two
  non-multiples of 1000 in the whole document actually live;
- a fractional GAS amount as well, because a corpus whose only gas amount is a
  whole multiple of 1000 cannot tell exact division from integer division;
- a variable-power building reporting ``mPowerConsumption`` of zero, whose
  real draw is an estimated min/max range, and a second one whose estimated
  maximum is a real zero and which is therefore NOT variable-power;
- a building carrying power with NO exponent at all, which means "not
  clock-scalable" rather than any default;
- a building descriptor with an EMPTY display name whose real name lives on
  the ``FGBuildable*`` entry;
- an item with no ``mResourceSinkPoints`` key beside one whose value is "0",
  so None and zero can be told apart, and one whose value is FRACTIONAL and
  therefore not a whole number of points;
- a recipe with an empty ingredient blob and an empty produced-in blob, both
  of which are real values rather than absent ones;
- a recipe produced only in a build gun, one naming a manufacturer AND a
  hand-craft token, and one naming only unresolvable ``/Script/`` tokens;
- an RF_INVALID pair, which is neither solid nor fluid;
- an ``FGCustomizationRecipe`` entry with a keyset identical to an
  ``FGRecipe`` entry, which any shape-based recipe detector will swallow;
- a duplicate ClassName in the ITEM namespace and another in the BUILDING
  namespace, an entry with NO ClassName at all, an entry whose FullName
  differs from its ClassName, an unknown group, and a malformed group;
- a descriptor group and a power-bearing group that are stock content but sit
  outside any name a registry is likely to hand-list, because the measured
  document carries thirteen ``mForm``-bearing groups and thirty-eight
  power-bearing ones and a four-name and a fifteen-name whitelist both miss
  most of them;
- a descriptor with NO ``mForm`` key, an entry whose number is unparsable, and
  an entry whose value is present but is NOT a string - the document carries
  1152 non-string values, so "every scalar is a string" is false;
- a ``mPowerConsumption`` carried as a STRUCT string rather than a scalar,
  which is a third power shape and must never publish as a confident zero.

Two entries in the recipe group are DESIGNED TO BE SKIPPED by a correct
registry - one with a malformed ingredient blob and one with no duration key -
so a consumer of this corpus should not expect every recipe ClassName below to
appear in a built registry.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

from clockspeed.data.docs_extract import DocsDocument, load_document

# ---------------------------------------------------------------------------
# Document keys, spelled out - see the module docstring on why these are not
# imported from the module under test
# ---------------------------------------------------------------------------

KEY_NATIVE_CLASS: Final = "NativeClass"
KEY_CLASSES: Final = "Classes"
KEY_CLASS_NAME: Final = "ClassName"
KEY_FULL_NAME: Final = "FullName"
KEY_DISPLAY_NAME: Final = "mDisplayName"
KEY_FORM: Final = "mForm"
KEY_ENERGY_VALUE: Final = "mEnergyValue"
KEY_SINK_POINTS: Final = "mResourceSinkPoints"
KEY_INGREDIENTS: Final = "mIngredients"
KEY_PRODUCT: Final = "mProduct"
KEY_PRODUCED_IN: Final = "mProducedIn"

#: Misspelled in the shipped game data. Verbatim, deliberately.
KEY_DURATION: Final = "mManufactoringDuration"

#: Correctly spelled, and measured sitting in the SAME record as the
#: misspelled duration key. Present here so a fixture cannot be "tidied" into
#: consistency without the mismatch being visible.
KEY_MENU_PRIORITY: Final = "mManufacturingMenuPriority"

KEY_POWER_CONSUMPTION: Final = "mPowerConsumption"
KEY_POWER_EXPONENT: Final = "mPowerConsumptionExponent"

#: Misspelled in the shipped game data ("Mininum"). Verbatim, deliberately.
KEY_ESTIMATED_MIN_POWER: Final = "mEstimatedMininumPowerConsumption"
KEY_ESTIMATED_MAX_POWER: Final = "mEstimatedMaximumPowerConsumption"

KEY_VARIABLE_POWER_CONSTANT: Final = "mVariablePowerConsumptionConstant"
KEY_VARIABLE_POWER_FACTOR: Final = "mVariablePowerConsumptionFactor"

#: Present on all 62 power-bearing entries with the value "1.000000" and it is
#: NOT the overclock ceiling (ADR 0005). It is in the corpus so a registry that
#: reads it as one can be caught doing so.
KEY_MAX_POTENTIAL: Final = "mMaxPotential"

# ---------------------------------------------------------------------------
# Group short names
# ---------------------------------------------------------------------------

ITEM_GROUP: Final = "FGItemDescriptor"
RESOURCE_GROUP: Final = "FGResourceDescriptor"
BUILDING_DESCRIPTOR_GROUP: Final = "FGBuildingDescriptor"
VEHICLE_GROUP: Final = "FGVehicleDescriptor"
MANUFACTURER_GROUP: Final = "FGBuildableManufacturer"
VARIABLE_POWER_GROUP: Final = "FGBuildableManufacturerVariablePower"
FLOODLIGHT_GROUP: Final = "FGBuildableFloodlight"
RECIPE_GROUP: Final = "FGRecipe"
CUSTOMIZATION_GROUP: Final = "FGCustomizationRecipe"
SCHEMATIC_GROUP: Final = "FGSchematic"

#: A stock descriptor group whose entries carry mForm, and which no short
#: four-name descriptor whitelist contains. The measured document carries 750
#: mForm-bearing entries across THIRTEEN groups; a whitelist of the four
#: obvious ones publishes the other groups' fluids in litres.
BIOMASS_GROUP: Final = "FGItemDescriptorBiomass"

#: A stock power-bearing group outside any short building whitelist. The
#: measured document carries 68 mPowerConsumption-bearing entries across
#: THIRTY-EIGHT groups and 62 exponent-bearing entries across thirty-four.
GENERATOR_GROUP: Final = "FGBuildableGeneratorNuclear"

#: Carried as a MALFORMED group (its Classes value is not a list), so the
#: registry's flag-and-skip path for a broken group is exercised.
MALFORMED_GROUP: Final = "FGBuildableStorage"

#: Outside the docs_extract whitelist entirely - game content this build has
#: never seen, standing in for a patch or a mod.
UNKNOWN_GROUP: Final = "FGSynthNewContent"

# ---------------------------------------------------------------------------
# Class names
# ---------------------------------------------------------------------------

WIDGET_ITEM: Final = "Desc_Widget_C"
GADGET_ITEM: Final = "Desc_Gadget_C"
ORE_ITEM: Final = "Desc_Ore_C"
ACID_ITEM: Final = "Desc_Acid_C"
WATER_ITEM: Final = "Desc_Water_C"
VAPOR_ITEM: Final = "Desc_Vapor_C"

#: The Widget's sink-point value, as the document carries it - a STRING, like
#: every other scalar in the file. Named so a test can assert the conversion
#: without restating the number, which would make the corpus and the test two
#: independent copies of one fact.
WIDGET_SINK_POINTS: Final = "11"

#: The building DESCRIPTOR: empty display name, form RF_INVALID.
SYNTHESIZER_ITEM: Final = "Desc_Synthesizer_C"

#: Referenced by a recipe and given no descriptor anywhere in the corpus, so
#: its form - and therefore its unit - is unknowable.
GHOST_ITEM: Final = "Desc_Ghost_C"

#: The one descriptor in UNKNOWN_GROUP. It carries an mForm, so it is exactly
#: what a registry dispatching on field presence would model if it ever looked
#: at unrecognized groups - which it must not.
FUTURE_ITEM: Final = "Desc_FromTheFuture_C"

#: An FGVehicleDescriptor entry: an item that also draws power, so it is both
#: an item and a power consumer, and it carries no exponent.
HAULER_ITEM: Final = "Desc_Hauler_C"

#: A LIQUID whose descriptor lives in BIOMASS_GROUP. Its amounts are litres
#: exactly like any other liquid's, and a registry that only looks in a
#: hand-listed set of descriptor groups cannot know that.
SLURRY_ITEM: Final = "Desc_Slurry_C"

#: Deliberately damaged in two independent ways: NO mForm key at all, so its
#: unit is unknowable, and a FRACTIONAL mResourceSinkPoints, which is not a
#: whole number of points and must not be truncated into one.
FORMLESS_ITEM: Final = "Desc_Formless_C"

#: A second vehicle, whose mPowerConsumption is a STRUCT string rather than a
#: scalar. Measured on one entry in the shipped document.
RAILCAR_ITEM: Final = "Desc_Railcar_C"

SYNTHESIZER_BUILDING: Final = "Build_Synthesizer_C"
BLENDER_BUILDING: Final = "Build_Blender_C"
ACCELERATOR_BUILDING: Final = "Build_Accelerator_C"
FLOODLIGHT_BUILDING: Final = "Build_Floodlight_C"

#: In GENERATOR_GROUP: carries the OTHER measured exponent value, and declares
#: an estimated maximum of a real zero - so it is not a variable-power
#: building, which is what a guard that only checks "is the key present"
#: cannot tell.
GENERATOR_BUILDING: Final = "Build_Generator_C"

#: In GENERATOR_GROUP: its exponent is not a number at all.
BROKEN_BUILDING: Final = "Build_Broken_C"

#: In MANUFACTURER_GROUP: carries an exponent and NO mPowerConsumption, so a
#: model that defaults an absent draw to zero reports a confident zero.
CHARGER_BUILDING: Final = "Build_Charger_C"

#: In MANUFACTURER_GROUP: its exponent is present but is a JSON NUMBER rather
#: than a string, which is a different fact from the key being absent.
NUMERIC_BUILDING: Final = "Build_Numeric_C"

WIDGET_RECIPE: Final = "Recipe_Widget_C"
BLEND_RECIPE: Final = "Recipe_Blend_C"
BUILD_GUN_RECIPE: Final = "Recipe_Synthesizer_C"
BOTH_TOKENS_RECIPE: Final = "Recipe_Both_C"
EMPTY_RECIPE: Final = "Recipe_Empty_C"
SCRIPT_ONLY_RECIPE: Final = "Recipe_ScriptToken_C"
GHOST_RECIPE: Final = "Recipe_Ghost_C"
ACCELERATED_RECIPE: Final = "Recipe_Accelerated_C"

#: Consumes the liquid whose descriptor is in BIOMASS_GROUP, at a fractional
#: number of cubic metres.
SLURRY_RECIPE: Final = "Recipe_Slurry_C"

#: Produces a GAS at an amount that is not a multiple of 1000.
GAS_RECIPE: Final = "Recipe_Vapor_C"

#: Designed to be flagged and SKIPPED by a correct registry.
MALFORMED_BLOB_RECIPE: Final = "Recipe_Malformed_C"
NO_DURATION_RECIPE: Final = "Recipe_NoDuration_C"

#: Lives in FGCustomizationRecipe with a keyset identical to a real recipe.
CUSTOMIZATION_RECIPE: Final = "Recipe_Paint_C"

SCHEMATIC: Final = "Schematic_Synth_C"

# ---------------------------------------------------------------------------
# mProducedIn tokens
# ---------------------------------------------------------------------------

SYNTHESIZER_PATH: Final = "/Game/Synth/Build_Synthesizer.Build_Synthesizer_C"
BLENDER_PATH: Final = "/Game/Synth/Build_Blender.Build_Blender_C"
ACCELERATOR_PATH: Final = "/Game/Synth/Build_Accelerator.Build_Accelerator_C"

#: The build gun. Measured as by far the most common token, and it resolves to
#: no buildable at all.
BUILD_GUN_PATH: Final = "/Game/Synth/BP_SynthBuildGun.BP_SynthBuildGun_C"
BUILD_GUN_CLASS: Final = "BP_SynthBuildGun_C"

#: A hand-craft bench component: also unresolvable, and measured appearing
#: ALONGSIDE a real manufacturer on 76 recipes, which is why "has a
#: non-manufacturer token" is not a valid exclusion test.
WORKBENCH_PATH: Final = "/Game/Synth/BP_SynthWorkBench.BP_SynthWorkBench_C"
WORKBENCH_CLASS: Final = "BP_SynthWorkBench_C"

#: A /Script/ engine reference: it has a "." but no buildable behind it.
ENGINE_CLASS_PATH: Final = "/Script/SynthGame.FGSynthAutomatedWorkBench"
ENGINE_CLASS_NAME: Final = "FGSynthAutomatedWorkBench"

#: A /Script/ token carrying NO "." separator at all, so there is no trailing
#: token to cut and the whole path is the only thing a resolver can try.
DOTLESS_PATH: Final = "/Script/SynthGame"
DOTLESS_CLASS_NAME: Final = "/Script/SynthGame"

# ---------------------------------------------------------------------------
# Field values that are the thing under test, named so a test asserts against
# the corpus rather than against a second copy of the same literal
# ---------------------------------------------------------------------------

#: The THIRD power shape: a struct string, not a scalar. Measured on one entry
#: of the shipped document. Neither float() nor Fraction() accepts it, so a
#: model that treats an unparsable draw as absent and an absent draw as zero
#: publishes a confident zero for a building that draws a real range.
RAILCAR_POWER_STRUCT: Final = "(Min=25.000000,Max=110.000000)"

#: The exponent value the corpus lacked. Two distinct values are measured
#: across the 62 exponent-bearing entries and only 20 carry the other one, so a
#: corpus with one value cannot catch a hardcoded constant.
SECOND_EXPONENT: Final = "1.600000"

#: Not a number in any base. Fraction() raises on it, and swallowing that
#: silently is indistinguishable from the field being absent.
UNPARSABLE_NUMBER: Final = "not-a-number"

#: PRESENT but not a string. 1152 measured values are non-strings - two
#: FGSchematic list fields and mFuel on two generator groups - so "every scalar
#: in the document is a string" is false, and a reader that routes a
#: non-string to "absent" loses the difference between "the game shipped
#: something new here" and "the game shipped nothing here".
NON_STRING_EXPONENT: Final = 1.6

#: Sink points that are not a whole number of points. Truncating this into an
#: int invents a value the document never carried.
FRACTIONAL_SINK_POINTS: Final = "1.500000"

# ---------------------------------------------------------------------------
# Blob construction
# ---------------------------------------------------------------------------

# The one blob written out character for character rather than composed. It is
# the anchor for every blob this module builds: it pins the delimiter ORDER -
# the DOUBLE quote delimits the field and a SINGLE quote sits inside the value
# as part of Unreal's Type'Path' syntax - and it pins the comma separation
# between entries. tests/data/test_registry.py asserts that amount_blob()
# reproduces this exact string, so the helper below is verified against a
# hand-written literal rather than trusted.
ANCHOR_INGREDIENTS_BLOB: Final = (
    '((ItemClass="'
    "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/Desc_Ore.Desc_Ore_C'"
    '",Amount=3),(ItemClass="'
    "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/Desc_Gadget.Desc_Gadget_C'"
    '",Amount=1))'
)

#: The ingredients of WIDGET_RECIPE, as (class name, verbatim amount) pairs.
ANCHOR_INGREDIENT_PAIRS: Final = ((ORE_ITEM, 3), (GADGET_ITEM, 1))

#: A path containing the literal marker text ``(ItemClass=``. The parser reads
#: one entry from it; ``marker_count`` naively counts two. Nothing in the
#: measured corpus looks like this - it exists to drive the cross-check that
#: turns a future grammar change into a red build.
EMBEDDED_MARKER_PATH: Final = (
    "/Script/Engine.BlueprintGeneratedClass'/Game/Synth/(ItemClass=/Desc_Odd.Desc_Odd_C'"
)
EMBEDDED_MARKER_BLOB: Final = f'((ItemClass="{EMBEDDED_MARKER_PATH}",Amount=1))'

MARKER_MISMATCH_RECIPE: Final = "Recipe_MarkerMismatch_C"


def item_path(class_name: str) -> str:
    """Build the Unreal object path an item-amount entry carries.

    Args:
        class_name: An item ClassName, e.g. ``Desc_Widget_C``.

    Returns:
        The path exactly as it appears between the double quotes of a blob,
        embedded single quote included.
    """
    stem = class_name.removesuffix("_C")
    return f"/Script/Engine.BlueprintGeneratedClass'/Game/Synth/{stem}.{class_name}'"


def amount_blob(pairs: Sequence[tuple[str, int]], *, extra_field: bool = False) -> str:
    """Build an item-amount blob - the ``mIngredients`` and ``mProduct`` grammar.

    Args:
        pairs: ``(class name, verbatim amount)`` pairs, in source order.
            Amounts are written exactly as given; fluids are in litres and
            nothing here converts them.
        extra_field: Give every entry ONE extra field, which is the most
            ordinary shape a game patch could take. The measured grammar
            cannot account for it, so a document built this way is a grammar
            change rather than a damaged row - see
            :func:`grammar_change_document`.

    Returns:
        The blob, or the empty string for no pairs - which is a real and valid
        value in the measured document, not an absent one.
    """
    if not pairs:
        return ""
    tail = ",Extra=0)" if extra_field else ")"
    entries = ",".join(
        f'(ItemClass="{item_path(key)}",Amount={amount}{tail}' for key, amount in pairs
    )
    return f"({entries})"


def class_path_blob(paths: Sequence[str]) -> str:
    """Build a class-path blob - the ``mProducedIn`` grammar.

    A DIFFERENT grammar from :func:`amount_blob`: bare quoted paths, no type
    wrapper and no keys.

    Args:
        paths: Object paths, in source order.

    Returns:
        The blob, or the empty string for no paths.
    """
    if not paths:
        return ""
    return "(" + ",".join(f'"{path}"' for path in paths) + ")"


def _group(short_name: str, entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Wrap entries in the ``{NativeClass, Classes}`` shape the document uses.

    Args:
        short_name: The group's trailing class token, e.g. ``FGRecipe``.
        entries: The group's Classes entries. Typed on ``Any`` values rather
            than on ``str`` because the corpus deliberately carries one
            non-string value, matching the 1152 measured in the shipped
            document.

    Returns:
        The group as a plain dict, ready for :func:`json.dumps`.
    """
    return {
        KEY_NATIVE_CLASS: f"/Script/CoreUObject.Class'/Script/FactoryGame.{short_name}'",
        KEY_CLASSES: list(entries),
    }


def _recipe_entry(
    class_name: str,
    display_name: str,
    duration: str | None,
    ingredients: str,
    product: str,
    produced_in: str,
    variable_power: tuple[str, str] = ("0.000000", "0.000000"),
) -> dict[str, str]:
    """Build one recipe entry.

    Args:
        class_name: The entry's ClassName.
        display_name: Its mDisplayName.
        duration: Its mManufactoringDuration, or None to OMIT the key
            entirely - which a correct registry flags and skips rather than
            defaulting to zero.
        ingredients: The mIngredients blob, possibly empty.
        product: The mProduct blob.
        produced_in: The mProducedIn blob, possibly empty.
        variable_power: The (constant, factor) pair carried on the recipe.

    Returns:
        The entry mapping. Every value is a string, as in the real document.
    """
    constant, factor = variable_power
    entry = {
        KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: display_name,
        KEY_INGREDIENTS: ingredients,
        KEY_PRODUCT: product,
        KEY_PRODUCED_IN: produced_in,
        KEY_MENU_PRIORITY: "0.000000",
        KEY_VARIABLE_POWER_CONSTANT: constant,
        KEY_VARIABLE_POWER_FACTOR: factor,
    }
    if duration is not None:
        entry[KEY_DURATION] = duration
    return entry


# ---------------------------------------------------------------------------
# The groups
# ---------------------------------------------------------------------------

_ITEM_ENTRIES: Final = [
    {
        KEY_CLASS_NAME: WIDGET_ITEM,
        KEY_DISPLAY_NAME: "Widget",
        KEY_FORM: "RF_SOLID",
        KEY_ENERGY_VALUE: "0.000000",
        KEY_SINK_POINTS: WIDGET_SINK_POINTS,
    },
    {
        # FullName differs from ClassName. Only 1552 of 2868 entries carry a
        # FullName, so nothing may key on it; ClassName is the unique key.
        KEY_CLASS_NAME: GADGET_ITEM,
        KEY_FULL_NAME: "BlueprintGeneratedClass /Game/Synth/Desc_Gadget.Desc_Gadget_C",
        KEY_DISPLAY_NAME: "Gadget",
        KEY_FORM: "RF_SOLID",
        KEY_SINK_POINTS: "23",
    },
    {
        KEY_CLASS_NAME: ACID_ITEM,
        KEY_DISPLAY_NAME: "Synthetic Acid",
        KEY_FORM: "RF_LIQUID",
        KEY_ENERGY_VALUE: "0.000000",
        KEY_SINK_POINTS: "55",
    },
    {
        # No mResourceSinkPoints key at all: measured on 4 of 122
        # FGItemDescriptor entries. A .get(key, 0) default reports these as
        # worthless to the sink, which is a different claim from "unknown".
        KEY_CLASS_NAME: WATER_ITEM,
        KEY_DISPLAY_NAME: "Synthetic Water",
        KEY_FORM: "RF_LIQUID",
        KEY_ENERGY_VALUE: "0.000000",
    },
    {
        # Sink points of exactly zero, so None and 0 can be told apart.
        KEY_CLASS_NAME: VAPOR_ITEM,
        KEY_DISPLAY_NAME: "Synthetic Vapor",
        KEY_FORM: "RF_GAS",
        KEY_ENERGY_VALUE: "2.500000",
        KEY_SINK_POINTS: "0",
    },
    {
        # A DUPLICATE ClassName. ClassName is unique across all 2868 measured
        # entries, so a duplicate is patch or mod content: it is flagged and
        # the FIRST entry is kept. Last-wins would turn the solid Widget into
        # a fluid and quietly divide every Widget amount by 1000.
        KEY_CLASS_NAME: WIDGET_ITEM,
        KEY_DISPLAY_NAME: "Widget Impostor",
        KEY_FORM: "RF_LIQUID",
        KEY_SINK_POINTS: "99",
    },
    {
        # NO mForm key, so no unit is knowable for any amount referencing it,
        # AND a fractional mResourceSinkPoints, which is not a whole number of
        # points. Both must be flagged; neither may be defaulted. A silent
        # default to RF_SOLID and a silent truncation to 1 both produce a
        # confident number of exactly the right type.
        KEY_CLASS_NAME: FORMLESS_ITEM,
        KEY_DISPLAY_NAME: "Formless",
        KEY_SINK_POINTS: FRACTIONAL_SINK_POINTS,
    },
    {
        # NO ClassName. ClassName is the document-wide key, so an entry
        # without one cannot be keyed or referenced: flagged and skipped.
        KEY_DISPLAY_NAME: "Nameless",
        KEY_FORM: "RF_SOLID",
    },
]

_BIOMASS_ENTRIES: Final = [
    {
        # A LIQUID in a stock descriptor group that no short whitelist names.
        # This is the measured 4000-litres-published-as-4000 defect in
        # miniature: the descriptor is right there in the document, in a group
        # a hand-listed set skipped, so the join finds nothing and the amount
        # is published in litres under a contract that promises cubic metres.
        KEY_CLASS_NAME: SLURRY_ITEM,
        KEY_DISPLAY_NAME: "Synthetic Slurry",
        KEY_FORM: "RF_LIQUID",
        KEY_ENERGY_VALUE: "4.000000",
        KEY_SINK_POINTS: "3",
    },
]

_RESOURCE_ENTRIES: Final = [
    {
        KEY_CLASS_NAME: ORE_ITEM,
        KEY_DISPLAY_NAME: "Synthetic Ore",
        KEY_FORM: "RF_SOLID",
        KEY_ENERGY_VALUE: "0.000000",
        KEY_SINK_POINTS: "1",
    },
]

_BUILDING_DESCRIPTOR_ENTRIES: Final = [
    {
        # An EMPTY display name, exactly as all 547 measured FGBuildingDescriptor
        # entries carry. The real name is on the FGBuildable* entry below.
        # This group has no mResourceSinkPoints at all.
        KEY_CLASS_NAME: SYNTHESIZER_ITEM,
        KEY_DISPLAY_NAME: "",
        KEY_FORM: "RF_INVALID",
        KEY_ENERGY_VALUE: "0.000000",
    },
]

_VEHICLE_ENTRIES: Final = [
    {
        # Both an item and a power consumer, and it carries NO exponent - one
        # of the 6 measured power-bearing entries with no mPowerConsumptionExponent.
        KEY_CLASS_NAME: HAULER_ITEM,
        KEY_DISPLAY_NAME: "Hauler",
        KEY_FORM: "RF_SOLID",
        KEY_SINK_POINTS: "7",
        KEY_POWER_CONSUMPTION: "5.000000",
    },
    {
        # The THIRD power shape: a struct string. Measured on one shipped
        # entry. Nothing that parses a decimal accepts it, so a model with two
        # branches - a number, or absent-and-therefore-zero - reports this
        # building at 0 MW with no range and no warning a caller can act on.
        KEY_CLASS_NAME: RAILCAR_ITEM,
        KEY_DISPLAY_NAME: "Railcar",
        KEY_FORM: "RF_INVALID",
        KEY_POWER_CONSUMPTION: RAILCAR_POWER_STRUCT,
    },
]

# Annotated rather than inferred: one entry below carries a non-string value on
# purpose, and an inferred list[object] would say the corpus is heterogeneous
# by accident rather than by design.
_MANUFACTURER_ENTRIES: Final[list[dict[str, Any]]] = [
    {
        KEY_CLASS_NAME: SYNTHESIZER_BUILDING,
        KEY_DISPLAY_NAME: "Synthesizer",
        KEY_POWER_CONSUMPTION: "4.000000",
        KEY_POWER_EXPONENT: "1.321929",
        KEY_MAX_POTENTIAL: "1.000000",
    },
    {
        KEY_CLASS_NAME: BLENDER_BUILDING,
        KEY_DISPLAY_NAME: "Blender",
        KEY_POWER_CONSUMPTION: "75.000000",
        KEY_POWER_EXPONENT: "1.321929",
        KEY_MAX_POTENTIAL: "1.000000",
    },
    {
        # An exponent and NO mPowerConsumption at all. Absent is not zero: a
        # building whose declared draw is missing is a gap in the model, and
        # publishing Fraction(0) for it is the same confident-zero failure the
        # variable-power buildings produce.
        KEY_CLASS_NAME: CHARGER_BUILDING,
        KEY_DISPLAY_NAME: "Charger",
        KEY_POWER_EXPONENT: SECOND_EXPONENT,
        KEY_MAX_POTENTIAL: "1.000000",
    },
    {
        # The exponent is PRESENT and is a JSON number rather than a string.
        # Routing it to "absent" loses the distinction between new content and
        # no content, and absence is this model's load-bearing signal for
        # "not clock-scalable".
        KEY_CLASS_NAME: NUMERIC_BUILDING,
        KEY_DISPLAY_NAME: "Numeric",
        KEY_POWER_CONSUMPTION: "9.000000",
        KEY_POWER_EXPONENT: NON_STRING_EXPONENT,
    },
]

_GENERATOR_ENTRIES: Final = [
    {
        # A stock power-bearing group outside any short whitelist, carrying the
        # exponent value the rest of the corpus lacks. Its estimated maximum is
        # a REAL zero, which is not the shape of a variable-power building - a
        # guard that only asks whether the key is present calls it one.
        KEY_CLASS_NAME: GENERATOR_BUILDING,
        KEY_DISPLAY_NAME: "Generator",
        KEY_POWER_CONSUMPTION: "100.000000",
        KEY_ESTIMATED_MAX_POWER: "0.000000",
        KEY_POWER_EXPONENT: SECOND_EXPONENT,
        KEY_MAX_POTENTIAL: "1.000000",
    },
    {
        # An exponent that is not a number. Treating it as absent without
        # saying so is indistinguishable from "this building is not
        # clock-scalable", which is a real and different fact.
        KEY_CLASS_NAME: BROKEN_BUILDING,
        KEY_DISPLAY_NAME: "Broken Coupler",
        KEY_POWER_CONSUMPTION: "12.000000",
        KEY_POWER_EXPONENT: UNPARSABLE_NUMBER,
    },
    {
        # A DUPLICATE ClassName in the BUILDING namespace, declaring a draw
        # twenty-five times the real one. The item namespace has its own
        # duplicate above; a first-wins rule proven in one namespace says
        # nothing about the other.
        KEY_CLASS_NAME: SYNTHESIZER_BUILDING,
        KEY_DISPLAY_NAME: "Synthesizer Impostor",
        KEY_POWER_CONSUMPTION: "100.000000",
        KEY_POWER_EXPONENT: SECOND_EXPONENT,
    },
]

_VARIABLE_POWER_ENTRIES: Final = [
    {
        # mPowerConsumption is ZERO here and that is not the draw. The real
        # range is on the two estimated keys, one of which is misspelled in
        # the game data. A model reading mPowerConsumption alone reports 0 MW
        # for the most power-hungry building in the game and looks correct.
        KEY_CLASS_NAME: ACCELERATOR_BUILDING,
        KEY_DISPLAY_NAME: "Accelerator",
        KEY_POWER_CONSUMPTION: "0.000000",
        KEY_ESTIMATED_MIN_POWER: "250.000000",
        KEY_ESTIMATED_MAX_POWER: "1500.000000",
        KEY_POWER_EXPONENT: "1.321929",
        KEY_MAX_POTENTIAL: "1.000000",
    },
]

_FLOODLIGHT_ENTRIES: Final = [
    {
        # Power but NO exponent: not clock-scalable. A default of 1.6 - or of
        # anything - would be an invented number.
        KEY_CLASS_NAME: FLOODLIGHT_BUILDING,
        KEY_DISPLAY_NAME: "Floodlight",
        KEY_POWER_CONSUMPTION: "10.000000",
    },
]

_RECIPE_ENTRIES: Final = [
    # Solids only, on both sides, produced in one real manufacturer.
    _recipe_entry(
        WIDGET_RECIPE,
        "Widget",
        "2.000000",
        ANCHOR_INGREDIENTS_BLOB,
        amount_blob([(WIDGET_ITEM, 2)]),
        class_path_blob([SYNTHESIZER_PATH]),
    ),
    # THE recipe that matters: a fractional fluid on BOTH sides. 2500 litres
    # of acid in, 1500 litres of water out as a byproduct. Those are the only
    # two amounts in the entire measured document that are not multiples of
    # 1000, and they sit in one recipe, one per side. Integer division loses
    # half a cubic metre per cycle on each.
    _recipe_entry(
        BLEND_RECIPE,
        "Blended Gadget",
        "6.000000",
        amount_blob([(ACID_ITEM, 2500), (WIDGET_ITEM, 2)]),
        amount_blob([(GADGET_ITEM, 1), (WATER_ITEM, 1500)]),
        class_path_blob([BLENDER_PATH]),
    ),
    # The build-gun case: produced only in a token that resolves to nothing,
    # its product is a building descriptor at Amount=1 with form RF_INVALID,
    # and its duration is a real zero.
    _recipe_entry(
        BUILD_GUN_RECIPE,
        "Synthesizer",
        "0.000000",
        amount_blob([(WIDGET_ITEM, 10)]),
        amount_blob([(SYNTHESIZER_ITEM, 1)]),
        class_path_blob([BUILD_GUN_PATH]),
    ),
    # Names a real manufacturer AND a hand-craft token. Measured on 76 of the
    # 291 automated recipes, so "has a non-manufacturer token" excludes 76
    # genuinely automated recipes.
    _recipe_entry(
        BOTH_TOKENS_RECIPE,
        "Hand Or Machine",
        "4.000000",
        amount_blob([(ORE_ITEM, 1)]),
        amount_blob([(GADGET_ITEM, 1)]),
        class_path_blob([SYNTHESIZER_PATH, WORKBENCH_PATH]),
    ),
    # Empty ingredients AND empty produced-in. Both are real values: 6 recipes
    # have no ingredients and 5 name no building. Treating either as absent
    # and skipping drops the recipe.
    _recipe_entry(
        EMPTY_RECIPE,
        "Vapor From Nothing",
        "1.000000",
        "",
        amount_blob([(VAPOR_ITEM, 1000)]),
        "",
    ),
    # Only unresolvable /Script/ tokens - one with a ".", one without.
    _recipe_entry(
        SCRIPT_ONLY_RECIPE,
        "Script Token",
        "3.000000",
        amount_blob([(ORE_ITEM, 2)]),
        amount_blob([(WIDGET_ITEM, 1)]),
        class_path_blob([ENGINE_CLASS_PATH, DOTLESS_PATH]),
    ),
    # References an item with no descriptor anywhere, at a fluid-looking
    # amount. Its form is unknowable, so its unit is unknowable.
    #
    # It also repeats the hand-craft token that BOTH_TOKENS_RECIPE carries, so
    # that one unresolvable token occurs TWICE across the corpus. Without a
    # repeat, warning aggregation is a code path no test would exercise - and
    # on the real document one token occurs 549 times.
    _recipe_entry(
        GHOST_RECIPE,
        "Ghost Input",
        "5.000000",
        amount_blob([(GHOST_ITEM, 2500)]),
        amount_blob([(WIDGET_ITEM, 1)]),
        class_path_blob([SYNTHESIZER_PATH, WORKBENCH_PATH]),
    ),
    # The variable-power coefficients live on the RECIPE, not the building.
    _recipe_entry(
        ACCELERATED_RECIPE,
        "Accelerated Gadget",
        "12.000000",
        amount_blob([(WIDGET_ITEM, 1)]),
        amount_blob([(GADGET_ITEM, 1)]),
        class_path_blob([ACCELERATOR_PATH]),
        variable_power=("250.000000", "1.000000"),
    ),
    # Consumes 2500 litres of the liquid whose descriptor lives in a group
    # outside every short whitelist. Two and a half cubic metres, or 2500 of
    # something - the two answers differ by a factor of a thousand and both
    # render as a plausible rate.
    _recipe_entry(
        SLURRY_RECIPE,
        "Slurry Feed",
        "8.000000",
        amount_blob([(SLURRY_ITEM, 2500)]),
        amount_blob([(WIDGET_ITEM, 1)]),
        class_path_blob([BLENDER_PATH]),
    ),
    # A GAS at an amount that is not a multiple of 1000. The corpus's other
    # gas amount is 1000, where exact division and integer division agree, so
    # without this one an integer-dividing gas branch survives every test.
    _recipe_entry(
        GAS_RECIPE,
        "Vapor Tap",
        "7.000000",
        amount_blob([(ORE_ITEM, 1)]),
        amount_blob([(VAPOR_ITEM, 2500)]),
        class_path_blob([SYNTHESIZER_PATH]),
    ),
    # A blob the measured grammar cannot account for end to end. Returning the
    # one entry it managed would be a silent short list, so the recipe is
    # flagged and skipped instead - and the rest of the build survives.
    _recipe_entry(
        MALFORMED_BLOB_RECIPE,
        "Malformed",
        "1.000000",
        f'((ItemClass="{item_path(ORE_ITEM)}",Amount=1)junk)',
        amount_blob([(WIDGET_ITEM, 1)]),
        class_path_blob([SYNTHESIZER_PATH]),
    ),
    # No duration key at all. A default of zero would be an infinite
    # production rate reported with total confidence.
    _recipe_entry(
        NO_DURATION_RECIPE,
        "No Duration",
        None,
        amount_blob([(ORE_ITEM, 1)]),
        amount_blob([(WIDGET_ITEM, 1)]),
        class_path_blob([SYNTHESIZER_PATH]),
    ),
]

_CUSTOMIZATION_ENTRIES: Final = [
    # Keyset identical to a real recipe, and it even names a real manufacturer
    # in mProducedIn. Any detector keying on field presence or on shape rather
    # than on NativeClass swallows this one and inflates the recipe count.
    _recipe_entry(
        CUSTOMIZATION_RECIPE,
        "Paint",
        "1.000000",
        amount_blob([(ORE_ITEM, 1)]),
        amount_blob([(GADGET_ITEM, 1)]),
        class_path_blob([SYNTHESIZER_PATH]),
    ),
]

_SCHEMATIC_ENTRIES: Final = [
    {
        KEY_CLASS_NAME: SCHEMATIC,
        KEY_DISPLAY_NAME: "Synthetic Milestone",
    },
]

_UNKNOWN_ENTRIES: Final = [
    {
        # It carries an mForm, which is exactly the field the item namespace
        # dispatches on - so a registry that scanned every well-formed group
        # rather than only the recognized ones would model content from a group
        # no probe has ever seen. Flagged and skipped means skipped.
        KEY_CLASS_NAME: FUTURE_ITEM,
        KEY_DISPLAY_NAME: "From The Future",
        KEY_FORM: "RF_SOLID",
    },
]


def _document() -> list[Any]:
    """Assemble the whole synthetic document.

    Returns:
        The top-level group list, including one group whose ``Classes`` value
        is not a list - a malformed group, which is flagged and skipped rather
        than being fatal.
    """
    return [
        _group(ITEM_GROUP, _ITEM_ENTRIES),
        _group(RESOURCE_GROUP, _RESOURCE_ENTRIES),
        _group(BIOMASS_GROUP, _BIOMASS_ENTRIES),
        _group(BUILDING_DESCRIPTOR_GROUP, _BUILDING_DESCRIPTOR_ENTRIES),
        _group(VEHICLE_GROUP, _VEHICLE_ENTRIES),
        _group(MANUFACTURER_GROUP, _MANUFACTURER_ENTRIES),
        _group(GENERATOR_GROUP, _GENERATOR_ENTRIES),
        _group(VARIABLE_POWER_GROUP, _VARIABLE_POWER_ENTRIES),
        _group(FLOODLIGHT_GROUP, _FLOODLIGHT_ENTRIES),
        _group(RECIPE_GROUP, _RECIPE_ENTRIES),
        _group(CUSTOMIZATION_GROUP, _CUSTOMIZATION_ENTRIES),
        _group(SCHEMATIC_GROUP, _SCHEMATIC_ENTRIES),
        _group(UNKNOWN_GROUP, _UNKNOWN_ENTRIES),
        {
            KEY_NATIVE_CLASS: (f"/Script/CoreUObject.Class'/Script/FactoryGame.{MALFORMED_GROUP}'"),
            KEY_CLASSES: "not a list",
        },
    ]


#: The corpus as docs TEXT, which is what ``load_document`` consumes. Built
#: once at import: the corpus is data and nothing mutates it in place.
DOCS_TEXT: Final = json.dumps(_document())


def docs_json() -> list[Any]:
    """Return a fresh mutable copy of the corpus.

    For a test that needs a variant - a key removed, a value corrupted -
    without disturbing the shared corpus.

    Returns:
        A newly parsed copy of the top-level group list.
    """
    parsed = json.loads(DOCS_TEXT)
    if not isinstance(parsed, list):
        raise TypeError("the synthetic corpus is not a JSON list")
    return parsed


def synthetic_document() -> DocsDocument:
    """Load the corpus through the real docs_extract seam.

    Loaded rather than hand-constructed on purpose: the registry consumes what
    docs_extract actually produces, so testing over the real seam is what
    catches a mismatch between the two.

    Returns:
        The loaded document, unknown and malformed groups included.
    """
    return load_document(DOCS_TEXT)


def document_from(groups: Iterable[Any]) -> DocsDocument:
    """Load an arbitrary group list through the same seam.

    Args:
        groups: Top-level groups, as :func:`_group` builds them.

    Returns:
        The loaded document.
    """
    return load_document(json.dumps(list(groups)))


def _patched_recipe(index: int, *, extra_field: bool) -> dict[str, str]:
    """Build one well-formed recipe, optionally with the grammar mutated.

    Args:
        index: Distinguishes the ClassNames. ClassName is the document-wide
            key, so repeating one would make the entries collapse into a
            duplicate-flag test instead of a grammar test.
        extra_field: Give every item-amount entry one extra field.

    Returns:
        The recipe entry.
    """
    return _recipe_entry(
        f"Recipe_Patched{index}_C",
        "Patched",
        "1.000000",
        amount_blob([(ORE_ITEM, 1)], extra_field=extra_field),
        amount_blob([(WIDGET_ITEM, 1)], extra_field=extra_field),
        class_path_blob([SYNTHESIZER_PATH]),
    )


def grammar_change_document(count: int = 3) -> DocsDocument:
    """Build a document in which the item-amount grammar itself has changed.

    Every entry grows ONE extra field, which is the most ordinary shape a game
    patch could take and is exactly what the naive marker count cannot see:
    the ``(ItemClass=`` marker is still there on every entry, so marker and
    parser never disagree - the parser simply refuses every blob. Flag-and-skip
    applied per recipe turns that into an EMPTY registry and a zero exit, which
    is the silently thinner factory plan the cross-check exists to prevent.

    Args:
        count: How many recipes to mutate.

    Returns:
        A document whose every recipe carries the mutated grammar.
    """
    return document_from(
        [
            _group(ITEM_GROUP, _ITEM_ENTRIES),
            _group(
                RECIPE_GROUP, [_patched_recipe(index, extra_field=True) for index in range(count)]
            ),
        ]
    )


def mostly_malformed_document(broken: int, intact: int) -> DocsDocument:
    """Build a document where most recipes are malformed but some survive.

    Distinguishes the two signals: a handful of damaged rows is ordinary
    unknown content and is flagged and skipped, while a burst of them is the
    grammar moving underfoot even though a recipe or two still happens to
    parse.

    Args:
        broken: How many recipes carry the mutated grammar.
        intact: How many parse cleanly.

    Returns:
        The document.
    """
    entries = [_patched_recipe(index, extra_field=True) for index in range(broken)]
    entries += [_patched_recipe(broken + index, extra_field=False) for index in range(intact)]
    return document_from([_group(ITEM_GROUP, _ITEM_ENTRIES), _group(RECIPE_GROUP, entries)])


def marker_mismatch_document() -> DocsDocument:
    """Build a document whose only recipe trips the marker cross-check.

    Its ingredient blob parses cleanly to ONE entry while the naive literal
    marker count sees TWO, because the item path itself contains the marker
    text. That disagreement is the canary for a future grammar change and it
    is deliberately kept OUT of the main corpus, which must build.

    Returns:
        A one-group document carrying that single recipe.
    """
    return document_from(
        [
            _group(
                RECIPE_GROUP,
                [
                    _recipe_entry(
                        MARKER_MISMATCH_RECIPE,
                        "Marker Mismatch",
                        "1.000000",
                        EMBEDDED_MARKER_BLOB,
                        amount_blob([(WIDGET_ITEM, 1)]),
                        class_path_blob([SYNTHESIZER_PATH]),
                    )
                ],
            )
        ]
    )
