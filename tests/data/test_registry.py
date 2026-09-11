"""Tests for clockspeed.data.registry - the normalized item, recipe and building model.

This is the layer where being WRONG and being GREEN are easiest to combine.
The parsers below it either return a value or raise; the registry instead
performs joins and unit conversions, and every one of its failure modes
produces a confident number of the right type. A building reported at 0 MW, an
ingredient list short by one, a fluid rate off by a factor of a thousand and a
recipe count inflated by 106 all look exactly like success.

So the tests below are organized by MEASURED TRAP rather than by function.
Each one names the specific wrong-but-plausible implementation it exists to
kill, and each trap in BOOTSTRAP.md section 3.2 that this layer can get wrong
has at least one test here. The corpus they run against is
``tests/data/synthetic.py`` - hand-authored, no game install required, which
is the CS-200 acceptance criterion.

Three assertion habits are deliberate:

- **Pin the SET, not the count.** ``len(recipes) == 8`` passes for eight wrong
  recipes. Comparing the whole key set cannot.
- **Pin what IS there.** CONVENTIONS.md section 7.2: a negative assertion
  rules out without pinning down. "No float anywhere" is paired with proof
  that the walk actually reached a value.
- **Compare against the CORPUS constants, never against a second copy of the
  implementation's own literals.** Where a spelling is the thing under test -
  the two misspelled game keys - it is asserted against the fixture's literal
  AND against the misspelled fragment itself.
"""

from __future__ import annotations

import ast
import dataclasses
from collections.abc import Iterator, Mapping
from dataclasses import FrozenInstanceError
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from clockspeed.data import registry as registry_module
from clockspeed.data.blobs import BlobParseError, marker_count, parse_item_amounts
from clockspeed.data.docs_extract import REASON_CLASSES_NOT_A_LIST
from clockspeed.data.registry import (
    FORM_GAS,
    FORM_SOLID,
    MAX_MALFORMED_BLOBS,
    WARN_DUPLICATE_CLASS_NAME,
    WARN_EMPTY_DISPLAY_NAME,
    WARN_MALFORMED_BLOB,
    WARN_MALFORMED_GROUP,
    WARN_MISSING_CLASS_NAME,
    WARN_MISSING_DURATION,
    WARN_MISSING_FORM,
    WARN_MISSING_POWER,
    WARN_NON_STRING_VALUE,
    WARN_UNKNOWN_GROUP,
    WARN_UNKNOWN_ITEM,
    WARN_UNPARSABLE_NUMBER,
    WARN_UNRESOLVED_PRODUCED_IN,
    Building,
    Item,
    Recipe,
    RecipeIO,
    Registry,
    RegistryIntegrityError,
    RegistryWarning,
    automated_recipes,
    build_registry,
)
from clockspeed.data.version import (
    CENSUS_KEY_BUILDING_FIELD_PRESENCE,
    is_registry_building_entry,
    pin,
)
from tests.data import synthetic
from tests.data.synthetic import (
    ACCELERATED_RECIPE,
    ACCELERATOR_BUILDING,
    ACID_ITEM,
    BLEND_RECIPE,
    BLENDER_BUILDING,
    BOTH_TOKENS_RECIPE,
    BROKEN_BUILDING,
    BUILD_GUN_CLASS,
    BUILD_GUN_RECIPE,
    CHARGER_BUILDING,
    CUSTOMIZATION_GROUP,
    CUSTOMIZATION_RECIPE,
    DOTLESS_CLASS_NAME,
    EMPTY_RECIPE,
    ENGINE_CLASS_NAME,
    FLOODLIGHT_BUILDING,
    FORMLESS_ITEM,
    FUTURE_ITEM,
    GADGET_ITEM,
    GAS_RECIPE,
    GENERATOR_BUILDING,
    GHOST_ITEM,
    GHOST_RECIPE,
    HAULER_ITEM,
    MALFORMED_BLOB_RECIPE,
    NO_DURATION_RECIPE,
    NUMERIC_BUILDING,
    ORE_ITEM,
    RAILCAR_ITEM,
    SCHEMATIC,
    SCHEMATIC_GROUP,
    SCRIPT_ONLY_RECIPE,
    SLURRY_ITEM,
    SLURRY_RECIPE,
    SYNTHESIZER_BUILDING,
    SYNTHESIZER_ITEM,
    UNKNOWN_GROUP,
    VAPOR_ITEM,
    WATER_ITEM,
    WIDGET_ITEM,
    WIDGET_RECIPE,
    WORKBENCH_CLASS,
)

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def registry() -> Registry:
    """The registry built once from the whole synthetic corpus.

    Returns:
        The built registry.
    """
    return build_registry(synthetic.synthetic_document())


def warnings_with(registry: Registry, code: str) -> tuple[RegistryWarning, ...]:
    """Select every published warning carrying ``code``.

    Args:
        registry: The built registry.
        code: One of the WARN_* codes.

    Returns:
        The matching warnings, in published order.
    """
    return tuple(warning for warning in registry.warnings if warning.code == code)


def warned_subjects(registry: Registry, code: str) -> set[str]:
    """Return the subjects warned about under ``code``.

    Args:
        registry: The built registry.
        code: One of the WARN_* codes.

    Returns:
        The set of subjects.
    """
    return {warning.subject for warning in warnings_with(registry, code)}


def walk_values(value: Any) -> Iterator[Any]:
    """Yield every leaf value reachable from ``value``.

    Descends dataclasses, mappings, tuples and lists. A string is a leaf, not
    a sequence to walk into.

    Args:
        value: The root object.

    Yields:
        Each leaf value.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for item in dataclasses.fields(value):
            yield from walk_values(getattr(value, item.name))
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from walk_values(item)
    elif isinstance(value, tuple | list):
        for item in value:
            yield from walk_values(item)
    else:
        yield value


def code_string_constants(module: ModuleType) -> set[str]:
    """Return every string literal in ``module`` that is not a docstring.

    Parsed from the AST rather than grepped from the text, so a rule about
    what the CODE may read cannot be tripped by the prose explaining it -
    and cannot be evaded by a comment either, since comments never reach the
    AST at all.

    Args:
        module: The imported module to inspect.

    Returns:
        The string constants appearing in code.
    """
    tree = ast.parse(Path(str(module.__file__)).read_text(encoding="utf-8"))
    documented = {
        docstring
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and (docstring := ast.get_docstring(node, clean=False)) is not None
    }
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in documented
    }


def registry_with_building_key(class_name: str, key: str, value: str | None) -> Registry:
    """Rebuild the corpus with one field of one entry set or removed.

    Every measured value of some fields is identical across the whole shipped
    document, so a test asserting that value cannot tell a READ from a folded
    constant. Mutating the corpus is what separates them.

    Args:
        class_name: The ClassName of the entry to patch. It must appear exactly
            once, so a name the corpus deliberately duplicates cannot be used
            here without the assertion below saying so.
        key: The document key to set or remove.
        value: The verbatim value to set, or None to remove the key entirely.

    Returns:
        A registry built from the patched copy, through the real docs_extract
        seam. The shared corpus is untouched - ``docs_json`` hands back a fresh
        parse.
    """
    groups = synthetic.docs_json()
    patched = 0
    for group in groups:
        classes = group.get(synthetic.KEY_CLASSES)
        if not isinstance(classes, list):
            continue
        for entry in classes:
            if entry.get(synthetic.KEY_CLASS_NAME) != class_name:
                continue
            patched += 1
            if value is None:
                entry.pop(key, None)
            else:
                entry[key] = value
    assert patched == 1, f"{class_name} appears {patched} times in the corpus, not once"
    return build_registry(synthetic.document_from(groups))


def io_for(recipe: Recipe, item_key: str, *, outputs: bool = False) -> RecipeIO:
    """Return the single input or output of ``recipe`` naming ``item_key``.

    Args:
        recipe: The recipe to look in.
        item_key: The item's ClassName.
        outputs: Look on the product side instead of the ingredient side.

    Returns:
        The matching RecipeIO.

    Raises:
        AssertionError: If it is not there exactly once - which would itself
            be the short-list failure these tests exist to catch.
    """
    side = recipe.outputs if outputs else recipe.inputs
    matches = [entry for entry in side if entry.item_key == item_key]
    assert len(matches) == 1, f"{item_key} appears {len(matches)} times in {recipe.key}"
    return matches[0]


# ---------------------------------------------------------------------------
# Trap 13 - the two keys misspelled in the shipped game data
# ---------------------------------------------------------------------------


def test_the_misspelled_game_keys_are_used_verbatim_not_autocorrected() -> None:
    # The single most likely edit anyone makes to this module is "fixing"
    # these. mManufactoringDuration sits beside the correctly spelled
    # mManufacturingMenuPriority in the same record, so the misspelling looks
    # like a typo in our code rather than in the game's.
    assert registry_module.KEY_DURATION == synthetic.KEY_DURATION
    assert registry_module.KEY_ESTIMATED_MIN_POWER == synthetic.KEY_ESTIMATED_MIN_POWER
    assert "Manufactoring" in registry_module.KEY_DURATION
    assert "Mininum" in registry_module.KEY_ESTIMATED_MIN_POWER


def test_every_document_key_the_registry_reads_matches_the_corpus_spelling() -> None:
    assert registry_module.KEY_DISPLAY_NAME == synthetic.KEY_DISPLAY_NAME
    assert registry_module.KEY_FORM == synthetic.KEY_FORM
    assert registry_module.KEY_ENERGY_VALUE == synthetic.KEY_ENERGY_VALUE
    assert registry_module.KEY_SINK_POINTS == synthetic.KEY_SINK_POINTS
    assert registry_module.KEY_INGREDIENTS == synthetic.KEY_INGREDIENTS
    assert registry_module.KEY_PRODUCT == synthetic.KEY_PRODUCT
    assert registry_module.KEY_PRODUCED_IN == synthetic.KEY_PRODUCED_IN
    assert registry_module.KEY_POWER_CONSUMPTION == synthetic.KEY_POWER_CONSUMPTION
    assert registry_module.KEY_POWER_EXPONENT == synthetic.KEY_POWER_EXPONENT
    assert registry_module.KEY_ESTIMATED_MAX_POWER == synthetic.KEY_ESTIMATED_MAX_POWER
    assert registry_module.KEY_VARIABLE_POWER_CONSTANT == synthetic.KEY_VARIABLE_POWER_CONSTANT
    assert registry_module.KEY_VARIABLE_POWER_FACTOR == synthetic.KEY_VARIABLE_POWER_FACTOR
    # Added when the un-sharded clock base became a read field (ADR 0006).
    # This test's name is a claim about EVERY key the registry reads, so a key
    # left out of it turns the name into a lie.
    assert registry_module.KEY_MAX_POTENTIAL == synthetic.KEY_MAX_POTENTIAL


# ---------------------------------------------------------------------------
# Trap 14 - ClassName is the key; FullName is on barely half the entries
# ---------------------------------------------------------------------------


def test_entries_are_keyed_by_class_name_and_never_by_full_name(registry: Registry) -> None:
    assert set(registry.items) == {
        WIDGET_ITEM,
        GADGET_ITEM,
        ORE_ITEM,
        ACID_ITEM,
        WATER_ITEM,
        VAPOR_ITEM,
        SYNTHESIZER_ITEM,
        HAULER_ITEM,
        FORMLESS_ITEM,
        SLURRY_ITEM,
        RAILCAR_ITEM,
    }
    # The Gadget entry carries a FullName that differs from its ClassName.
    # Only 1552 of 2868 measured entries have one at all, so a registry keyed
    # on it silently loses nearly half the document.
    assert not any(" " in key for key in registry.items)


def test_duplicate_class_name_keeps_the_first_entry_and_flags_it(registry: Registry) -> None:
    # The corpus carries a second Desc_Widget_C declaring itself a LIQUID.
    # Last-wins would divide every solid Widget amount by 1000 and report a
    # perfectly plausible rate.
    widget = registry.items[WIDGET_ITEM]
    assert widget.display_name == "Widget"
    assert widget.is_fluid is False
    assert WIDGET_ITEM in warned_subjects(registry, WARN_DUPLICATE_CLASS_NAME)


# ---------------------------------------------------------------------------
# Trap 2 - no floats, anywhere, ever
# ---------------------------------------------------------------------------


def test_no_value_anywhere_in_the_registry_is_a_float(registry: Registry) -> None:
    # Every scalar in the document is a STRING - '2.000000', '1.321929',
    # '2500'. float() succeeds on all of them and poisons exactness silently,
    # which non-negotiable 6 exists to prevent.
    leaves = list(walk_values(registry))
    assert [leaf for leaf in leaves if isinstance(leaf, float)] == []
    # Paired with proof the walk actually reached numbers: "no floats found"
    # is also what a walk over nothing at all reports.
    assert any(isinstance(leaf, Fraction) for leaf in leaves)


def test_decimal_strings_convert_to_exact_fractions_not_through_float(
    registry: Registry,
) -> None:
    # 1.321929 is not representable in binary floating point. Going through
    # float() and back yields a Fraction with a denominator in the quadrillions
    # that is merely CLOSE to this one.
    assert registry.buildings[SYNTHESIZER_BUILDING].power_exponent == Fraction(1321929, 1000000)
    assert registry.items[VAPOR_ITEM].energy_value == Fraction(5, 2)
    assert registry.recipes[WIDGET_RECIPE].duration == Fraction(2)


# ---------------------------------------------------------------------------
# Trap 1 - the fractional fluid is on BOTH sides of one recipe
# ---------------------------------------------------------------------------


def test_fractional_fluid_is_exact_on_the_ingredient_side(registry: Registry) -> None:
    # 2500 litres of a liquid is two and a half cubic metres. Integer division
    # loses half a cubic metre per cycle, silently.
    assert io_for(registry.recipes[BLEND_RECIPE], ACID_ITEM).amount == Fraction(5, 2)


def test_fractional_fluid_is_exact_on_the_product_side_too(registry: Registry) -> None:
    # The trap that a fixture written from the original spike wording misses
    # entirely: the OTHER non-multiple of 1000 in the whole document is a
    # BYPRODUCT, at 1500 litres. A normalizer that converts ingredients and
    # forgets products passes every ingredient-side test ever written.
    assert io_for(registry.recipes[BLEND_RECIPE], WATER_ITEM, outputs=True).amount == Fraction(3, 2)


def test_both_sides_of_the_fractional_recipe_are_pinned_whole(registry: Registry) -> None:
    # Pinning the whole tuple is the only shape that cannot pass a short list.
    recipe = registry.recipes[BLEND_RECIPE]
    assert recipe.inputs == (
        RecipeIO(item_key=ACID_ITEM, amount=Fraction(5, 2)),
        RecipeIO(item_key=WIDGET_ITEM, amount=Fraction(2)),
    )
    assert recipe.outputs == (
        RecipeIO(item_key=GADGET_ITEM, amount=Fraction(1)),
        RecipeIO(item_key=WATER_ITEM, amount=Fraction(3, 2)),
    )


def test_solid_amounts_are_whole_items_and_are_never_divided(registry: Registry) -> None:
    recipe = registry.recipes[WIDGET_RECIPE]
    assert recipe.inputs == (
        RecipeIO(item_key=ORE_ITEM, amount=Fraction(3)),
        RecipeIO(item_key=GADGET_ITEM, amount=Fraction(1)),
    )
    assert recipe.outputs == (RecipeIO(item_key=WIDGET_ITEM, amount=Fraction(2)),)


def test_a_gas_is_normalized_by_the_same_rule_as_a_liquid(registry: Registry) -> None:
    # 36 measured pairs are RF_GAS. A conversion keyed on RF_LIQUID alone
    # leaves every gas rate a thousand times too large.
    assert registry.items[VAPOR_ITEM].form == FORM_GAS
    assert registry.items[VAPOR_ITEM].is_fluid is True
    assert io_for(registry.recipes[EMPTY_RECIPE], VAPOR_ITEM, outputs=True).amount == Fraction(1)


def test_a_fractional_gas_amount_is_exact_and_not_integer_divided(registry: Registry) -> None:
    # The gas assertion above uses 1000 litres, where exact division and
    # integer division agree exactly - so it passes for a gas branch that
    # divides into an int, and passed for one measurably. 2500 litres is two
    # and a half cubic metres, and // loses half of one every cycle.
    amount = io_for(registry.recipes[GAS_RECIPE], VAPOR_ITEM, outputs=True).amount
    assert amount == Fraction(5, 2)
    # Integer division cannot produce a non-unit denominator, so this pins the
    # mechanism rather than only the value.
    assert amount.denominator != 1


# ---------------------------------------------------------------------------
# Trap 11 - mForm lives in a different group, and RF_INVALID is a third thing
# ---------------------------------------------------------------------------


def test_rf_invalid_pair_is_neither_solid_nor_fluid_and_is_not_divided(
    registry: Registry,
) -> None:
    # 555 of 2440 measured pairs are RF_INVALID at Amount=1: the build-gun
    # building-descriptor case. Dividing them by 1000 is as wrong as treating
    # them as ordinary items, so the form is preserved verbatim for a caller
    # that needs to tell them apart.
    descriptor = registry.items[SYNTHESIZER_ITEM]
    assert descriptor.form == "RF_INVALID"
    assert descriptor.is_fluid is False
    product = io_for(registry.recipes[BUILD_GUN_RECIPE], SYNTHESIZER_ITEM, outputs=True)
    assert product.amount == Fraction(1)


def test_form_is_resolved_by_the_descriptor_join_not_guessed_from_the_amount(
    registry: Registry,
) -> None:
    # The blob parser cannot know a unit; only the join can. Acid at 2500 and
    # the Widget at 2 come out of the SAME blob and must be scaled differently.
    assert registry.items[ACID_ITEM].is_fluid is True
    assert registry.items[WIDGET_ITEM].is_fluid is False


def test_unknown_item_reference_leaves_the_amount_unconverted_and_is_flagged(
    registry: Registry,
) -> None:
    # No descriptor means no form, which means no unit. Inventing one is the
    # silently-wrong path; the amount stays verbatim and the gap is published.
    assert GHOST_ITEM not in registry.items
    assert io_for(registry.recipes[GHOST_RECIPE], GHOST_ITEM).amount == Fraction(2500)
    assert GHOST_ITEM in warned_subjects(registry, WARN_UNKNOWN_ITEM)


# ---------------------------------------------------------------------------
# The item namespace is decided by FIELD PRESENCE, not by a list of group names
# ---------------------------------------------------------------------------
#
# The measured document carries 750 mForm-bearing entries across THIRTEEN
# groups. A whitelist of the four obvious descriptor groups reaches 690 of them
# and misses ten RF_LIQUID items outright, so every recipe touching one takes
# the "no descriptor, no knowable unit" branch and publishes litres under a
# contract that says cubic metres - a factor of a thousand, in the right type,
# with a warning that looks like ordinary unmodeled content.


def test_a_descriptor_group_outside_any_name_list_still_yields_items(
    registry: Registry,
) -> None:
    # The corpus puts a liquid in a stock group no short whitelist names. The
    # descriptor is present, well formed and joinable; only a hand-maintained
    # list of group names could make it invisible.
    slurry = registry.items[SLURRY_ITEM]
    assert slurry.form == "RF_LIQUID"
    assert slurry.is_fluid is True
    # The whole descriptor is read, not just the field that admitted it.
    assert slurry.display_name == "Synthetic Slurry"
    assert slurry.energy_value == Fraction(4)


def test_a_fluid_from_an_unlisted_descriptor_group_is_cubic_metres_not_litres(
    registry: Registry,
) -> None:
    # THE defect this section exists for. 2500 litres is two and a half cubic
    # metres; the number a whitelist-driven registry publishes is 2500, and
    # nothing downstream can tell one from the other.
    amount = io_for(registry.recipes[SLURRY_RECIPE], SLURRY_ITEM).amount
    assert amount == Fraction(5, 2)
    assert SLURRY_ITEM not in warned_subjects(registry, WARN_UNKNOWN_ITEM)


def test_a_descriptor_with_no_form_key_is_flagged_and_never_defaulted_to_solid(
    registry: Registry,
) -> None:
    # Defaulting an absent mForm to RF_SOLID is silent and plausible: the item
    # appears, its amounts are counts, and every existing test still passes.
    # Absent form means absent unit, and that has to be visible.
    formless = registry.items[FORMLESS_ITEM]
    assert formless.form == ""
    assert formless.form != FORM_SOLID
    assert formless.is_fluid is False
    assert synthetic.ITEM_GROUP in warned_subjects(registry, WARN_MISSING_FORM)


# ---------------------------------------------------------------------------
# Trap 3 - the variable-power buildings report zero
# ---------------------------------------------------------------------------


def test_variable_power_building_reports_its_range_not_the_zero_it_declares(
    registry: Registry,
) -> None:
    # mPowerConsumption is '0.000000' on the three hungriest buildings in the
    # game. A model reading that field alone reports 0 MW and looks correct.
    accelerator = registry.buildings[ACCELERATOR_BUILDING]
    assert accelerator.power_consumption == Fraction(0)
    assert accelerator.estimated_min_power == Fraction(250)
    assert accelerator.estimated_max_power == Fraction(1500)
    assert accelerator.is_variable_power is True


def test_a_fixed_draw_building_is_not_reported_as_variable_power(registry: Registry) -> None:
    synthesizer = registry.buildings[SYNTHESIZER_BUILDING]
    assert synthesizer.power_consumption == Fraction(4)
    assert synthesizer.is_variable_power is False
    assert synthesizer.estimated_max_power is None


def test_variable_power_coefficients_come_from_the_recipe_not_the_building(
    registry: Registry,
) -> None:
    # The constant and the factor are RECIPE fields. Looking for them on the
    # building finds nothing and yields a flat draw for every recipe.
    accelerated = registry.recipes[ACCELERATED_RECIPE]
    assert accelerated.variable_power_constant == Fraction(250)
    assert accelerated.variable_power_factor == Fraction(1)


# ---------------------------------------------------------------------------
# Trap 4 - the exponent is per building class, and 6 entries have none
# ---------------------------------------------------------------------------


def test_power_exponent_is_read_per_building_class(registry: Registry) -> None:
    # Two distinct values are measured across 62 entries. A hardcoded constant
    # is wrong for 42 of them.
    assert registry.buildings[BLENDER_BUILDING].power_exponent == Fraction(1321929, 1000000)
    assert registry.buildings[ACCELERATOR_BUILDING].power_exponent == Fraction(1321929, 1000000)


def test_a_building_with_no_exponent_is_none_and_never_defaulted(registry: Registry) -> None:
    # A missing exponent means NOT clock-scalable. Defaulting it to 1.6, to
    # 1.321929, or to 1.0 all invent a number the game never shipped.
    assert registry.buildings[FLOODLIGHT_BUILDING].power_exponent is None
    assert registry.buildings[FLOODLIGHT_BUILDING].power_consumption == Fraction(10)
    assert registry.buildings[HAULER_ITEM].power_exponent is None


# ---------------------------------------------------------------------------
# The building namespace is decided by FIELD PRESENCE too
# ---------------------------------------------------------------------------
#
# 68 measured entries carry mPowerConsumption across THIRTY-EIGHT groups and 62
# carry an exponent across thirty-four. A fifteen-name whitelist models 29 of
# the 62 exponent-bearing entries and leaves both fuel-burning generator groups
# out of the model entirely, which is not a partial answer to a power question -
# it is a missing one.


def test_a_power_bearing_group_outside_any_name_list_still_yields_buildings(
    registry: Registry,
) -> None:
    generator = registry.buildings[GENERATOR_BUILDING]
    assert generator.display_name == "Generator"
    assert generator.power_consumption == Fraction(100)


def test_the_second_measured_exponent_value_is_read_rather_than_a_constant(
    registry: Registry,
) -> None:
    # Two distinct exponents are measured and the corpus previously carried
    # only one, so a hardcoded 1.321929 survived every test in this file.
    assert registry.buildings[GENERATOR_BUILDING].power_exponent == Fraction(8, 5)
    assert registry.buildings[SYNTHESIZER_BUILDING].power_exponent == Fraction(1321929, 1000000)


def test_an_estimated_maximum_of_zero_is_not_a_variable_power_building(
    registry: Registry,
) -> None:
    # The variable-power shape is an estimated maximum ABOVE zero. Dropping the
    # comparison and asking only whether the key is present calls this building
    # variable-power, and every clock calculation then reads a range of zero to
    # zero instead of its declared draw.
    generator = registry.buildings[GENERATOR_BUILDING]
    assert generator.estimated_max_power == Fraction(0)
    assert generator.is_variable_power is False


def test_a_building_with_no_declared_power_reports_none_and_is_flagged(
    registry: Registry,
) -> None:
    # Absent is not zero. Fraction(0) is a claim the document never made, it is
    # the right type, and it is indistinguishable from a building that really
    # draws nothing.
    charger = registry.buildings[CHARGER_BUILDING]
    assert charger.power_consumption is None
    assert charger.estimated_max_power is None
    assert CHARGER_BUILDING in warned_subjects(registry, WARN_MISSING_POWER)


def test_an_unparsable_number_is_flagged_rather_than_silently_treated_as_absent(
    registry: Registry,
) -> None:
    # Swallowing the failure leaves None, which this model uses to mean "not
    # clock-scalable" - a real and different fact. The value must come back
    # None AND the gap must be published.
    assert registry.buildings[BROKEN_BUILDING].power_exponent is None
    assert BROKEN_BUILDING in warned_subjects(registry, WARN_UNPARSABLE_NUMBER)


def test_a_present_but_non_string_value_is_flagged_distinctly_from_an_absent_one(
    registry: Registry,
) -> None:
    # "Every scalar in the document is a string" is false: 1152 measured values
    # are not. Routing a non-string to "absent" collapses new content into no
    # content, and absence is load bearing here.
    assert registry.buildings[NUMERIC_BUILDING].power_exponent is None
    assert NUMERIC_BUILDING in warned_subjects(registry, WARN_NON_STRING_VALUE)
    # The distinction is the whole point: the building whose exponent key is
    # genuinely absent must NOT collect this warning.
    assert FLOODLIGHT_BUILDING not in warned_subjects(registry, WARN_NON_STRING_VALUE)


# ---------------------------------------------------------------------------
# Trap 3 again - a THIRD power shape, measured after the model was written
# ---------------------------------------------------------------------------


def test_a_struct_shaped_power_field_is_a_range_and_never_a_confident_zero(
    registry: Registry,
) -> None:
    # mPowerConsumption is a struct string on one measured entry. A model with
    # two branches - parse a decimal, or treat it as absent and therefore zero -
    # publishes 0 MW, is_variable_power False and no range at all, which is
    # trap 3's exact failure mode arriving through a different door.
    railcar = registry.buildings[RAILCAR_ITEM]
    assert railcar.power_consumption != Fraction(0)
    assert railcar.power_consumption is None
    assert railcar.estimated_min_power == Fraction(25)
    assert railcar.estimated_max_power == Fraction(110)
    assert railcar.is_variable_power is True
    # A struct that IS understood is not an unparsable number.
    assert RAILCAR_ITEM not in warned_subjects(registry, WARN_UNPARSABLE_NUMBER)


def test_the_struct_bounds_are_exact_fractions_taken_from_the_corpus_literal(
    registry: Registry,
) -> None:
    # Asserted against the corpus's own literal rather than against a second
    # copy of the numbers, so the fixture and the expectation cannot drift into
    # agreeing with each other.
    low, high = (
        part.split("=", 1)[1] for part in synthetic.RAILCAR_POWER_STRUCT.strip("()").split(",")
    )
    railcar = registry.buildings[RAILCAR_ITEM]
    assert railcar.estimated_min_power == Fraction(low)
    assert railcar.estimated_max_power == Fraction(high)


# ---------------------------------------------------------------------------
# Trap 5 - mMaxPotential is the UN-SHARDED BASE, and it is not the clock ceiling
# ---------------------------------------------------------------------------
#
# ADR 0006 decides how the base enters the model; ADR 0005 decides where the
# ceiling comes from, and its answer is "not from this document". Both halves
# are load bearing and they pull in opposite directions, which is why the fence
# here is two-sided rather than a flat ban:
#
#   READ the base. ADR 0005 consequence 1 requires mMaxPotential per building
#   class off the registry precisely so that no literal 1.0 is ever written
#   into the solver - the same reason a literal 1.321929 is banned.
#
#   Do NOT read, name or publish a ceiling. The ceiling needs a slot count that
#   is in no file on this machine, so a model carrying three of the four
#   operands would publish a ceiling silently missing its multiplier. Reading
#   the base AS the ceiling caps every solve at 100 percent and is the exact
#   trap ADR 0005 exists to foreclose.

#: The operands of the ADR 0005 ceiling equation OTHER than the un-sharded
#: base. Every one is a real key in the shipped document, and the previous
#: version of this fence checked none of them - it forbade mMaxPotential alone,
#: so a registry could have read all four of these in silence.
CEILING_OPERAND_KEYS = (
    "mPotentialShardSlots",
    "mExtraPotential",
    "mDefaultPotentialShardSlots",
    "mOverridePotentialShardSlots",
)

#: Fragments no published field name may contain. "potential" and "ceiling"
#: carry over from the fence this section replaces; the rest are the words a
#: later "helpful" wiring-up would reach for.
CEILING_NAME_FRAGMENTS = ("ceiling", "overclock", "max_clock", "potential", "shard")


def ceiling_flavoured(name: str) -> bool:
    """Report whether a field name claims to be a clock ceiling.

    "unsharded" is the ONE approved use of the shard root and it is trimmed
    before the test, because that word is a NEGATION - it names the base
    measured with no shards installed. Trimming can only ever join neighbouring
    characters into a fragment, never hide one, so the allowance cannot produce
    a false negative.

    Args:
        name: A dataclass field name.

    Returns:
        True when the name contains a forbidden fragment.
    """
    trimmed = name.replace("unsharded", "")
    return any(fragment in trimmed for fragment in CEILING_NAME_FRAGMENTS)


def test_the_unsharded_clock_base_is_read_per_building_and_absence_is_never_defaulted(
    registry: Registry,
) -> None:
    # ADR 0005 consequence 1. The base is a document value, so it is read from
    # the document - and an entry that declares none HAS none. Defaulting the
    # absent case to 1 is the same invention as defaulting a missing exponent:
    # it publishes a number the game never shipped, in the right type, and
    # nothing downstream can tell it from a measured one.
    assert registry.buildings[BLENDER_BUILDING].unsharded_clock_base == Fraction(1)
    assert registry.buildings[FLOODLIGHT_BUILDING].unsharded_clock_base is None


def test_the_unsharded_clock_base_comes_from_the_data_not_from_a_folded_constant() -> None:
    # mMaxPotential is '1.000000' on every measured entry and on every corpus
    # entry that carries it, so `unsharded_clock_base = Fraction(1)` hardcoded
    # passes the test above and every other test in this file. Only mutating
    # the corpus can tell a read from a constant - and the removal half proves
    # the same for the None branch, which a `.get(key, 1)` default would pass.
    raised = registry_with_building_key(BLENDER_BUILDING, synthetic.KEY_MAX_POTENTIAL, "2.000000")
    assert raised.buildings[BLENDER_BUILDING].unsharded_clock_base == Fraction(2)
    removed = registry_with_building_key(BLENDER_BUILDING, synthetic.KEY_MAX_POTENTIAL, None)
    assert removed.buildings[BLENDER_BUILDING].unsharded_clock_base is None


def test_the_absent_max_potential_branch_is_grounded_in_the_shipped_document() -> None:
    # CS-210. The two tests above prove the BEHAVIOUR - an entry that declares
    # no base gets None rather than an invented 1. They prove nothing about the
    # PREMISE, because both read the same hand-authored corpus, and a corpus
    # entry only demonstrates what a corpus author chose to write. The pin is
    # measured from the shipped document by tools/drift_guard.py --re-extract,
    # so it is the one artifact in the repository that can say the shipped game
    # really ships such a building.
    field = synthetic.KEY_MAX_POTENTIAL
    counted = pin()["census"][CENSUS_KEY_BUILDING_FIELD_PRESENCE][field]
    assert counted["absent"] > 0, (
        f"the shipped document records no published building without {field}, "
        "so the None branch below is exercised by the corpus alone"
    )
    assert (
        registry_with_building_key(BLENDER_BUILDING, synthetic.KEY_MAX_POTENTIAL, None)
        .buildings[BLENDER_BUILDING]
        .unsharded_clock_base
        is None
    )


def test_the_census_building_predicate_agrees_with_the_registrys() -> None:
    # clockspeed/data/version.py and this module are peers over
    # clockspeed/data/docs_extract.py, and the allowed-import matrix in
    # tests/data/test_phase2_gate.py forbids either importing the other. So the
    # census states the published-building predicate a second time on purpose,
    # and this table is the fence that stops the two statements drifting apart.
    # A shared import would have been the other answer and is the one the
    # matrix rules out.
    cases: list[dict[str, object]] = [
        {},
        {synthetic.KEY_CLASS_NAME: "Build_SynthNothing_C"},
        {synthetic.KEY_POWER_CONSUMPTION: "10.000000"},
        {synthetic.KEY_POWER_EXPONENT: "1.321929"},
        {
            synthetic.KEY_POWER_CONSUMPTION: "10.000000",
            synthetic.KEY_POWER_EXPONENT: "1.321929",
        },
        {synthetic.KEY_MAX_POTENTIAL: "1.000000"},
        {synthetic.KEY_FORM: FORM_SOLID},
    ]
    verdicts = [registry_module._is_building_entry(entry) for entry in cases]  # noqa: SLF001
    # Positive and negative halves both present, so an agreement between two
    # predicates that both answered False everywhere cannot pass this.
    assert any(verdicts)
    assert not all(verdicts)
    assert [is_registry_building_entry(entry) for entry in cases] == verdicts


def test_the_base_is_read_and_every_other_ceiling_operand_stays_unread() -> None:
    # The check is on the module's string CONSTANTS rather than on its text, so
    # the docstring may explain what the field is not - which is the thing that
    # stops it being wired into a ceiling later - while the operands themselves
    # stay unreadable by the code. A comment never reaches the AST either.
    literals = code_string_constants(registry_module)
    # Positive half first: prove the extractor really sees the module's key
    # literals, so the absences asserted below are evidence rather than an
    # empty set agreeing with anything.
    assert synthetic.KEY_FORM in literals
    assert synthetic.KEY_MAX_POTENTIAL in literals
    for key in CEILING_OPERAND_KEYS:
        assert not any(key in literal for literal in literals), key


def test_no_published_field_names_itself_a_ceiling_and_the_base_field_is_present() -> None:
    # A negative assertion needs its positive half twice over: the detector has
    # to detect, and the field the fence permits has to exist. Without the
    # first, a helper that always returned False would pass; without the
    # second, deleting the base field entirely would pass too.
    assert ceiling_flavoured("max_potential")
    assert ceiling_flavoured("potential_shard_slots")
    assert ceiling_flavoured("clock_ceiling")
    assert not ceiling_flavoured("unsharded_clock_base")
    field_names = {
        item.name
        for model in (Item, Building, Recipe, RecipeIO)
        for item in dataclasses.fields(model)
    }
    assert "unsharded_clock_base" in field_names
    assert [name for name in field_names if ceiling_flavoured(name)] == []


# ---------------------------------------------------------------------------
# Trap 6 - all 547 building descriptors have an empty display name
# ---------------------------------------------------------------------------


def test_building_names_come_from_the_buildable_entry_not_the_descriptor(
    registry: Registry,
) -> None:
    assert registry.buildings[SYNTHESIZER_BUILDING].display_name == "Synthesizer"
    assert registry.items[SYNTHESIZER_ITEM].display_name == ""


def test_every_building_in_the_registry_has_a_non_empty_display_name(
    registry: Registry,
) -> None:
    # The assertion that would have caught 547 nameless buildings. An empty
    # string is a valid string, so a normalizer reading names off the
    # descriptor passes every test it wrote for itself.
    #
    # The building SET is pinned first, and that is not decoration: "zero
    # nameless buildings" is also true of zero buildings, and this test
    # measurably passed against an inert stub until the set was pinned
    # (CONVENTIONS.md section 7.2 - a count of bad rows is relative to a set,
    # so state the set).
    assert set(registry.buildings) == {
        SYNTHESIZER_BUILDING,
        BLENDER_BUILDING,
        CHARGER_BUILDING,
        NUMERIC_BUILDING,
        GENERATOR_BUILDING,
        BROKEN_BUILDING,
        ACCELERATOR_BUILDING,
        FLOODLIGHT_BUILDING,
        HAULER_ITEM,
        RAILCAR_ITEM,
    }
    assert [key for key, building in registry.buildings.items() if not building.display_name] == []


def test_an_empty_display_name_is_flagged_rather_than_silently_accepted(
    registry: Registry,
) -> None:
    assert synthetic.BUILDING_DESCRIPTOR_GROUP in warned_subjects(registry, WARN_EMPTY_DISPLAY_NAME)


# ---------------------------------------------------------------------------
# Trap 7 - automation is a property of mProducedIn, not of group membership
# ---------------------------------------------------------------------------


def test_automated_recipes_are_exactly_those_naming_a_production_building(
    registry: Registry,
) -> None:
    # All 872 measured recipes sit in one group and only 291 name a
    # manufacturer, so group membership answers the wrong question entirely.
    assert {recipe.key for recipe in automated_recipes(registry)} == {
        WIDGET_RECIPE,
        BLEND_RECIPE,
        BOTH_TOKENS_RECIPE,
        GHOST_RECIPE,
        ACCELERATED_RECIPE,
        SLURRY_RECIPE,
        GAS_RECIPE,
    }


def test_a_recipe_naming_both_a_manufacturer_and_a_hand_craft_token_is_automated(
    registry: Registry,
) -> None:
    # 76 of the 291 automated recipes also carry a hand-craft token, so
    # "excludes anything with a non-manufacturer token" loses 76 real recipes.
    recipe = registry.recipes[BOTH_TOKENS_RECIPE]
    assert recipe.produced_in == (SYNTHESIZER_BUILDING,)
    assert recipe.unresolved_produced_in == (WORKBENCH_CLASS,)
    assert recipe in automated_recipes(registry)


def test_a_build_gun_only_recipe_is_kept_but_is_not_automated(registry: Registry) -> None:
    # The build gun alone accounts for 549 of the 703 measured tokens. Those
    # recipes are real and stay in the registry; they are simply not built by
    # a machine.
    recipe = registry.recipes[BUILD_GUN_RECIPE]
    assert recipe.produced_in == ()
    assert recipe.unresolved_produced_in == (BUILD_GUN_CLASS,)
    assert recipe not in automated_recipes(registry)


# ---------------------------------------------------------------------------
# Trap 8 - FGCustomizationRecipe has a keyset identical to FGRecipe
# ---------------------------------------------------------------------------


def test_customization_recipes_are_excluded_despite_an_identical_keyset(
    registry: Registry,
) -> None:
    # 978 entries doc-wide carry mIngredients across exactly two groups. Any
    # field-presence or shape-based detector inflates 872 recipes into 978 and
    # every one of them looks well formed.
    assert CUSTOMIZATION_RECIPE not in registry.recipes
    assert set(registry.recipes) == {
        WIDGET_RECIPE,
        BLEND_RECIPE,
        BUILD_GUN_RECIPE,
        BOTH_TOKENS_RECIPE,
        EMPTY_RECIPE,
        SCRIPT_ONLY_RECIPE,
        GHOST_RECIPE,
        ACCELERATED_RECIPE,
        SLURRY_RECIPE,
        GAS_RECIPE,
    }


def test_the_customization_entry_would_have_passed_a_shape_based_detector() -> None:
    # Proof the exclusion above is load-bearing rather than incidental: the
    # customization entry carries the same keys as a real recipe AND names a
    # real manufacturer, so nothing about its shape distinguishes it.
    document = synthetic.synthetic_document()
    groups = {group.short_name: group for group in document.groups}
    recipe_keys = set(groups[synthetic.RECIPE_GROUP].entries[0])
    customization_keys = set(groups[CUSTOMIZATION_GROUP].entries[0])
    assert customization_keys == recipe_keys


# ---------------------------------------------------------------------------
# Trap 9 - 6 of 17 produced-in tokens resolve to nothing
# ---------------------------------------------------------------------------


def test_unresolvable_tokens_are_flagged_and_the_recipe_survives(registry: Registry) -> None:
    # Two of the measured tokens are /Script/ references with no buildable
    # behind them, and one carries no "." separator at all. Crashing on one
    # loses the build; dropping the recipe loses real content.
    recipe = registry.recipes[SCRIPT_ONLY_RECIPE]
    assert recipe.produced_in == ()
    assert recipe.unresolved_produced_in == (ENGINE_CLASS_NAME, DOTLESS_CLASS_NAME)
    assert {ENGINE_CLASS_NAME, DOTLESS_CLASS_NAME} <= warned_subjects(
        registry, WARN_UNRESOLVED_PRODUCED_IN
    )


def test_unresolved_tokens_are_aggregated_by_token_with_a_count(registry: Registry) -> None:
    # The token identity is the actionable fact; one warning per occurrence
    # would bury it under 703 lines on the real document, where a single token
    # accounts for 549 of them.
    #
    # The corpus deliberately repeats the workbench token across two recipes,
    # because a corpus where every token occurs once cannot tell an
    # aggregating implementation from one that simply emits one warning each.
    counts = {
        item.subject: item.count for item in warnings_with(registry, WARN_UNRESOLVED_PRODUCED_IN)
    }
    assert counts == {
        BUILD_GUN_CLASS: 1,
        WORKBENCH_CLASS: 2,
        ENGINE_CLASS_NAME: 1,
        DOTLESS_CLASS_NAME: 1,
    }


# ---------------------------------------------------------------------------
# Trap 10 - sink points are optional, and absent is not zero
# ---------------------------------------------------------------------------


def test_absent_sink_points_are_none_and_zero_sink_points_are_zero(
    registry: Registry,
) -> None:
    # A .get(key, 0) default reports the 4 measured FGItemDescriptor entries
    # that lack the key as worthless to the sink, which is a claim the data
    # never made.
    assert registry.items[WATER_ITEM].sink_points is None
    assert registry.items[VAPOR_ITEM].sink_points == 0
    # The document carries every scalar as a string, so the int is a
    # conversion this layer performs rather than a value it copies.
    assert registry.items[WIDGET_ITEM].sink_points == int(synthetic.WIDGET_SINK_POINTS)


def test_absent_energy_value_is_none_rather_than_zero(registry: Registry) -> None:
    assert registry.items[GADGET_ITEM].energy_value is None
    assert registry.items[WIDGET_ITEM].energy_value == Fraction(0)


# ---------------------------------------------------------------------------
# Trap 12 - empty is a real value, not an absent one
# ---------------------------------------------------------------------------


def test_a_recipe_with_an_empty_ingredient_blob_is_kept_with_no_inputs(
    registry: Registry,
) -> None:
    # 6 measured recipes have mIngredients == "". Treating empty as absent and
    # skipping drops all six.
    recipe = registry.recipes[EMPTY_RECIPE]
    assert recipe.inputs == ()
    assert recipe.outputs == (RecipeIO(item_key=VAPOR_ITEM, amount=Fraction(1)),)


def test_an_empty_produced_in_blob_is_a_real_value_and_not_an_error(
    registry: Registry,
) -> None:
    # 5 measured recipes name no building at all.
    recipe = registry.recipes[EMPTY_RECIPE]
    assert recipe.produced_in == ()
    assert recipe.unresolved_produced_in == ()
    assert recipe not in automated_recipes(registry)


# ---------------------------------------------------------------------------
# The marker cross-check handed over by the blob parser
# ---------------------------------------------------------------------------


def test_marker_count_mismatch_fails_loudly_instead_of_shortening_a_recipe() -> None:
    # marker_count is a naive literal count sharing no code with the parser,
    # so a disagreement between the two is a real signal rather than two
    # implementations of the same grammar agreeing with each other. A future
    # game patch that changes the grammar becomes a red build here instead of
    # a quietly thinner factory plan.
    with pytest.raises(RegistryIntegrityError):
        build_registry(synthetic.marker_mismatch_document())


def test_the_integrity_error_cannot_be_swallowed_by_the_flag_and_skip_path() -> None:
    # A malformed blob is flagged and skipped; a marker mismatch is fatal. If
    # the integrity error were a BlobParseError, the skip handler would catch
    # it and the canary would never sing.
    assert not issubclass(RegistryIntegrityError, BlobParseError)
    assert not issubclass(RegistryIntegrityError, ValueError)


# ---------------------------------------------------------------------------
# The signal that actually catches a grammar change
# ---------------------------------------------------------------------------
#
# The marker cross-check above cannot catch one, and reasoning from its
# mechanism says so: the marker literal "(ItemClass=" is part of the parser's
# own pattern, so on any blob the parser ACCEPTS the two counts agree by
# construction. It fires only on the known false positive - a marker embedded
# inside a path - which is exactly what the corpus feeds it. On a real grammar
# change the parser refuses the blob instead, flag-and-skip drops the recipe,
# and a document of 872 recipes builds into a registry of none with a zero
# exit: the quietly thinner factory plan, arrived at one clean skip at a time.
#
# So the loud signal has to be taken over the whole document rather than per
# recipe: too many refusals, or a recipe group that produced no recipes at all.


def test_a_one_extra_field_grammar_change_is_fatal_rather_than_an_empty_registry() -> None:
    # One extra field per item-amount entry is the most ordinary shape a patch
    # could take, and it is invisible to the marker count. Nothing here is
    # damaged data: every blob is internally consistent, and that is precisely
    # why per-recipe flag-and-skip accepts all of it.
    with pytest.raises(RegistryIntegrityError):
        build_registry(synthetic.grammar_change_document())


def test_the_grammar_change_document_really_does_keep_its_markers() -> None:
    # Proof the test above exercises the new signal rather than the old one.
    # If the mutation removed the marker, the cross-check would catch it and
    # the aggregate signal would still be untested.
    document = synthetic.grammar_change_document(count=1)
    groups = {group.short_name: group for group in document.groups}
    blob = groups[synthetic.RECIPE_GROUP].entries[0][synthetic.KEY_INGREDIENTS]
    assert isinstance(blob, str)
    assert marker_count(blob) == 1
    with pytest.raises(BlobParseError):
        parse_item_amounts(blob)


def test_a_burst_of_malformed_blobs_is_fatal_even_when_a_recipe_survives() -> None:
    # The other half of the aggregate: a document that still produces recipes
    # is not evidence the grammar held. Pinning it above the threshold rather
    # than at a literal keeps the test and the constant from drifting apart.
    with pytest.raises(RegistryIntegrityError):
        build_registry(
            synthetic.mostly_malformed_document(broken=MAX_MALFORMED_BLOBS + 1, intact=2)
        )


def test_malformed_blobs_below_the_threshold_stay_flag_and_skip(registry: Registry) -> None:
    # The negative half. Non-negotiable 7 is that unknown content is flagged
    # and skipped rather than fatal, so the escalation must not swallow the
    # ordinary case - and the whole corpus, which carries one malformed blob,
    # has to keep building.
    assert MAX_MALFORMED_BLOBS >= 1
    intact = MAX_MALFORMED_BLOBS
    below = build_registry(synthetic.mostly_malformed_document(broken=1, intact=intact))
    assert len(below.recipes) == intact
    assert registry.recipes


# ---------------------------------------------------------------------------
# Unknown content is flagged and skipped, never fatal (non-negotiable 7)
# ---------------------------------------------------------------------------


def test_a_malformed_blob_flags_and_skips_one_recipe_without_killing_the_build(
    registry: Registry,
) -> None:
    assert MALFORMED_BLOB_RECIPE not in registry.recipes
    assert MALFORMED_BLOB_RECIPE in warned_subjects(registry, WARN_MALFORMED_BLOB)
    assert registry.recipes[WIDGET_RECIPE].key == WIDGET_RECIPE


def test_a_recipe_with_no_duration_is_flagged_and_skipped_not_defaulted_to_zero(
    registry: Registry,
) -> None:
    # A zero duration is an infinite production rate. The corpus separately
    # carries a recipe whose duration is zero, and that one is KEPT - so this
    # is about the key being absent, not about the value.
    #
    # That zero is an INVENTED shape, not a measured one, and saying so is the
    # point: a census over all 978 recipe-shaped entries of the pinned build
    # finds zero entries with no duration key and zero durations of zero. Both
    # shapes here are future-proofing against a patch, and labelling either as
    # measured would put a false provenance claim in the suite - which is worse
    # than the gap it papers over, because the next reader would build on it.
    assert NO_DURATION_RECIPE not in registry.recipes
    assert NO_DURATION_RECIPE in warned_subjects(registry, WARN_MISSING_DURATION)
    assert registry.recipes[BUILD_GUN_RECIPE].duration == Fraction(0)


def test_fractional_sink_points_are_refused_and_flagged_rather_than_truncated(
    registry: Registry,
) -> None:
    # int(Fraction("1.500000")) is 1 and looks like a perfectly ordinary sink
    # value. The field is a whole number of points in the measured document, so
    # a fractional one is content this build does not understand.
    assert registry.items[FORMLESS_ITEM].sink_points is None
    assert FORMLESS_ITEM in warned_subjects(registry, WARN_UNPARSABLE_NUMBER)


def test_a_duplicate_class_name_in_the_building_namespace_keeps_the_first(
    registry: Registry,
) -> None:
    # First-wins proven in the item namespace says nothing about the building
    # namespace - they are separate dictionaries filled by separate passes. The
    # impostor declares twenty-five times the real draw, which is a plausible
    # number for a power plan and a wrong one.
    synthesizer = registry.buildings[SYNTHESIZER_BUILDING]
    assert synthesizer.display_name == "Synthesizer"
    assert synthesizer.power_consumption == Fraction(4)
    assert SYNTHESIZER_BUILDING in warned_subjects(registry, WARN_DUPLICATE_CLASS_NAME)


def test_an_entry_with_no_class_name_is_flagged_and_skipped(registry: Registry) -> None:
    # ClassName is the document-wide key: an entry without one cannot be keyed
    # and cannot be referenced, so it is dropped. The warning is what keeps
    # that from being a silent loss, and it is aggregated by GROUP because the
    # entry has no name to aggregate by.
    assert synthetic.ITEM_GROUP in warned_subjects(registry, WARN_MISSING_CLASS_NAME)
    assert "" not in registry.items


def test_an_unknown_group_is_published_and_flagged_rather_than_dropped(
    registry: Registry,
) -> None:
    assert registry.unknown_groups == (UNKNOWN_GROUP,)
    assert UNKNOWN_GROUP in warned_subjects(registry, WARN_UNKNOWN_GROUP)


def test_an_unknown_groups_entries_are_skipped_even_though_they_carry_the_markers(
    registry: Registry,
) -> None:
    # The corpus's unknown group carries a descriptor with an mForm, which is
    # the exact field the item namespace now dispatches on. Flagged and skipped
    # means SKIPPED (non-negotiable 7): a build that quietly modeled unknown
    # content would be publishing numbers from a group nobody has ever probed,
    # which is a different failure from the one that made field presence the
    # rule in the first place.
    assert FUTURE_ITEM not in registry.items
    assert FUTURE_ITEM not in registry.buildings


def test_a_malformed_group_is_published_as_a_warning_and_the_build_continues(
    registry: Registry,
) -> None:
    assert [item.detail for item in warnings_with(registry, WARN_MALFORMED_GROUP)] == [
        REASON_CLASSES_NOT_A_LIST
    ]


def test_known_but_deliberately_unmodeled_groups_are_not_reported_as_unknown(
    registry: Registry,
) -> None:
    # Reporting a deliberate exclusion as unknown on every build trains the
    # operator to ignore the field, which is how the one real unknown gets
    # missed. The positive half is asserted first so this cannot pass by
    # reporting nothing at all.
    assert registry.unknown_groups == (UNKNOWN_GROUP,)
    assert {SCHEMATIC_GROUP, CUSTOMIZATION_GROUP} <= set(
        registry_module.UNMODELED_GROUP_SHORT_NAMES
    )
    assert SCHEMATIC_GROUP not in registry.unknown_groups
    assert CUSTOMIZATION_GROUP not in registry.unknown_groups
    assert SCHEMATIC not in registry.items
    assert SCHEMATIC not in registry.buildings


# ---------------------------------------------------------------------------
# The published seam
# ---------------------------------------------------------------------------


def test_building_the_same_document_twice_yields_an_identical_registry() -> None:
    # Determinism is the first of the four properties in CLAUDE.md section 1:
    # two runs over the same input that disagree are a bug, and warning order
    # is part of the output.
    first = build_registry(synthetic.synthetic_document())
    second = build_registry(synthetic.synthetic_document())
    # Two empty registries are equal too, so prove there is something to
    # compare before comparing it.
    assert first.items
    assert first.recipes
    assert first.buildings
    assert first.warnings
    assert first == second
    assert first.warnings == second.warnings


def test_the_published_models_reject_mutation(registry: Registry) -> None:
    attribute = "amount"
    entry = registry.recipes[WIDGET_RECIPE].inputs[0]
    with pytest.raises(FrozenInstanceError):
        setattr(entry, attribute, Fraction(0))


def test_the_registry_mappings_reject_mutation(registry: Registry) -> None:
    with pytest.raises(TypeError):
        registry.items[WIDGET_ITEM] = registry.items[GADGET_ITEM]  # type: ignore[index]


def test_automated_recipes_returns_a_tuple_of_recipes(registry: Registry) -> None:
    result = automated_recipes(registry)
    assert isinstance(result, tuple)
    assert result
    assert all(isinstance(recipe, Recipe) for recipe in result)


# ---------------------------------------------------------------------------
# The corpus itself
# ---------------------------------------------------------------------------


def test_the_corpus_blob_helper_reproduces_the_hand_written_anchor() -> None:
    # The corpus composes most of its blobs, so the composer is verified
    # against one blob written out character for character - the double quote
    # delimits the field and the single quote sits INSIDE the value.
    assert (
        synthetic.amount_blob(list(synthetic.ANCHOR_INGREDIENT_PAIRS))
        == synthetic.ANCHOR_INGREDIENTS_BLOB
    )
