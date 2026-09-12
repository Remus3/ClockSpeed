"""CS-979 - the extraction-rate vocabulary the registry lands out of the docs.

Every byte of the corpus below is hand-authored in THIS file. Nothing here
reads the real install, the real docs file or a save, so the whole module runs
on a machine that has never had the game on it - the CS-200 criterion
``tests/data/__init__.py`` states, and the same rule
``tests/data/synthetic.py`` exists to obey.

WHY THIS MODULE DOES NOT USE THE SHARED SYNTHETIC CORPUS
--------------------------------------------------------
``tests/data/synthetic.py`` carries no extractor entry at all, and this slice
does not own that file. A corpus authored here also keeps the KEY SPELLINGS
spelled out as literals beside the assertions that read them, which is the
guard ``tests/data/synthetic.py`` documents at length: a fixture importing the
registry's own constants stays green through a rename or a "corrected"
spelling, which is precisely the defect the fixture exists to catch.

THE MEASURED SHAPES THIS CORPUS REPRODUCES
------------------------------------------
Measured against the pinned build's shipped docs before any of this was
written. Each shape below breaks a reader that passes its own tests:

- ``mAllowedResourceForms`` is a PARENTHESIZED LIST, never a bare token:
  ``(RF_SOLID)`` and ``(RF_LIQUID,RF_GAS)``. A reader comparing the raw value
  against ``RF_SOLID`` matches nothing and reports every extractor as having
  no allowed form, which reads exactly like a document that stopped shipping
  the field.
- One measured value carries a NESTED, DIFFERENTLY SPELLED token:
  ``(RF_LIQUID,RF_GAS,(INVALID))``. It is NOT ``RF_INVALID``, and equating the
  two would be this layer inventing a form the document never named. It is
  kept verbatim and flagged instead (non-negotiable 7).
- Entries carry the allowed forms with NO RATE KEYS AT ALL. Publishing zero
  items per cycle for those is the confident-zero trap
  ``Building.power_consumption`` documents; they are None and flagged.
- ``mItemsPerCycle`` on a fluid extractor is in LITRES, and the item it will
  extract is not knowable here - the allowed forms are a SET and the node's
  resource is not in the save (ADR 0003). So the value stays verbatim and the
  litre conversion is the caller's, after it resolves a resource.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Iterator, Mapping
from fractions import Fraction
from typing import Any, Final

import pytest

from clockspeed.data.docs_extract import load_document
from clockspeed.data.registry import (
    EXTRACTION_MARKER_KEYS,
    FORM_GAS,
    FORM_INVALID,
    FORM_LIQUID,
    FORM_SOLID,
    KEY_ALLOWED_RESOURCE_FORMS,
    KEY_EXTRACT_CYCLE_TIME,
    KEY_ITEMS_PER_CYCLE,
    RESOURCE_FORMS,
    WARN_EMPTY_DISPLAY_NAME,
    WARN_MISSING_EXTRACTION_RATE,
    WARN_NON_STRING_VALUE,
    WARN_UNKNOWN_RESOURCE_FORM,
    WARN_UNPARSABLE_NUMBER,
    Extractor,
    Registry,
    build_registry,
)

# ---------------------------------------------------------------------------
# The key spellings, as LITERALS. See the module docstring.
# ---------------------------------------------------------------------------

LITERAL_ITEMS_PER_CYCLE: Final = "mItemsPerCycle"
LITERAL_EXTRACT_CYCLE_TIME: Final = "mExtractCycleTime"
LITERAL_ALLOWED_RESOURCE_FORMS: Final = "mAllowedResourceForms"

KEY_CLASS_NAME: Final = "ClassName"
KEY_DISPLAY_NAME: Final = "mDisplayName"
KEY_FORM: Final = "mForm"
KEY_NATIVE_CLASS: Final = "NativeClass"
KEY_CLASSES: Final = "Classes"
KEY_POWER_CONSUMPTION: Final = "mPowerConsumption"

# The group short names are REAL - they are the join keys the loader
# dispatches on, and a corpus using invented ones would exercise nothing.
GROUP_RESOURCE_EXTRACTOR: Final = "FGBuildableResourceExtractor"
GROUP_FRACKING_EXTRACTOR: Final = "FGBuildableFrackingExtractor"
GROUP_FRACKING_ACTIVATOR: Final = "FGBuildableFrackingActivator"
GROUP_WATER_PUMP: Final = "FGBuildableWaterPump"
GROUP_MINER_DISPENSER: Final = "FGPortableMinerDispenser"
GROUP_ITEM_DESCRIPTOR: Final = "FGItemDescriptor"

# Every ClassName below is invented.
SOLID_MINER: Final = "Build_SynthMinerMk1_C"
FASTER_MINER: Final = "Build_SynthMinerMk2_C"
LIQUID_PUMP: Final = "Build_SynthPump_C"
WELL_EXTRACTOR: Final = "Build_SynthWellExtractor_C"
WELL_ACTIVATOR: Final = "Build_SynthWellActivator_C"
DISPENSER: Final = "Equip_SynthDispenser_C"
BROKEN_RATE_MINER: Final = "Build_SynthBrokenRateMiner_C"
NON_STRING_MINER: Final = "Build_SynthNonStringMiner_C"
STOPPED_MINER: Final = "Build_SynthStoppedMiner_C"
RATE_ONLY_MINER: Final = "Build_SynthRateOnlyMiner_C"
PLAIN_ITEM: Final = "Desc_SynthOre_C"

#: The nested, differently spelled token measured inside one real value. Kept
#: verbatim rather than mapped onto RF_INVALID.
NESTED_INVALID_FORM: Final = "(INVALID)"


def group(short_name: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap entries in the ``{NativeClass, Classes}`` shape the document uses.

    Args:
        short_name: The real group short name.
        entries: The group's entries.

    Returns:
        The group as a plain dict, ready for :func:`json.dumps`.
    """
    inner = f"/Script/FactoryGame.{short_name}"
    return {
        KEY_NATIVE_CLASS: "/Script/CoreUObject.Class'" + inner + "'",
        KEY_CLASSES: entries,
    }


def extraction_docs() -> str:
    """Author the whole corpus this module is graded against.

    Returns:
        The docs text, as JSON. No group, key or value is read from disk.
    """
    document = [
        group(
            GROUP_RESOURCE_EXTRACTOR,
            [
                {
                    KEY_CLASS_NAME: SOLID_MINER,
                    KEY_DISPLAY_NAME: "Synth Miner Mk.1",
                    # A whole count per cycle and a whole-second cycle.
                    LITERAL_ITEMS_PER_CYCLE: "1",
                    LITERAL_EXTRACT_CYCLE_TIME: "1.000000",
                    LITERAL_ALLOWED_RESOURCE_FORMS: "(RF_SOLID)",
                    # Present so the join against Registry.buildings is real.
                    KEY_POWER_CONSUMPTION: "5.000000",
                },
                {
                    KEY_CLASS_NAME: FASTER_MINER,
                    KEY_DISPLAY_NAME: "Synth Miner Mk.2",
                    # A quarter-second cycle, exact as Fraction(1, 4).
                    LITERAL_ITEMS_PER_CYCLE: "1",
                    LITERAL_EXTRACT_CYCLE_TIME: "0.250000",
                    LITERAL_ALLOWED_RESOURCE_FORMS: "(RF_SOLID)",
                },
                {
                    KEY_CLASS_NAME: BROKEN_RATE_MINER,
                    KEY_DISPLAY_NAME: "Synth Broken Rate Miner",
                    LITERAL_ITEMS_PER_CYCLE: "1",
                    # Unparsable. Never zero, never one.
                    LITERAL_EXTRACT_CYCLE_TIME: "one second",
                    LITERAL_ALLOWED_RESOURCE_FORMS: "(RF_SOLID)",
                },
                {
                    KEY_CLASS_NAME: NON_STRING_MINER,
                    KEY_DISPLAY_NAME: "Synth Non String Miner",
                    # Present but not a string: a different fact from absent.
                    LITERAL_ITEMS_PER_CYCLE: ["1"],
                    LITERAL_EXTRACT_CYCLE_TIME: "1.000000",
                    LITERAL_ALLOWED_RESOURCE_FORMS: "(RF_SOLID)",
                },
                {
                    KEY_CLASS_NAME: STOPPED_MINER,
                    KEY_DISPLAY_NAME: "Synth Stopped Miner",
                    LITERAL_ITEMS_PER_CYCLE: "1",
                    # A DECLARED zero, which is a different fact from absent.
                    LITERAL_EXTRACT_CYCLE_TIME: "0.000000",
                    LITERAL_ALLOWED_RESOURCE_FORMS: "(RF_SOLID)",
                },
                {
                    KEY_CLASS_NAME: RATE_ONLY_MINER,
                    KEY_DISPLAY_NAME: "Synth Rate Only Miner",
                    # No allowed-forms key at all: still an extractor, on the
                    # same any-of rule POWER_MARKER_KEYS uses for a building.
                    LITERAL_ITEMS_PER_CYCLE: "3",
                    LITERAL_EXTRACT_CYCLE_TIME: "2.000000",
                },
            ],
        ),
        group(
            GROUP_WATER_PUMP,
            [
                {
                    KEY_CLASS_NAME: LIQUID_PUMP,
                    KEY_DISPLAY_NAME: "Synth Pump",
                    # LITRES per cycle, exactly as the document states it.
                    LITERAL_ITEMS_PER_CYCLE: "2000",
                    LITERAL_EXTRACT_CYCLE_TIME: "0.500000",
                    LITERAL_ALLOWED_RESOURCE_FORMS: "(RF_LIQUID)",
                },
            ],
        ),
        group(
            GROUP_FRACKING_EXTRACTOR,
            [
                {
                    KEY_CLASS_NAME: WELL_EXTRACTOR,
                    KEY_DISPLAY_NAME: "Synth Well Extractor",
                    LITERAL_ITEMS_PER_CYCLE: "1000",
                    LITERAL_EXTRACT_CYCLE_TIME: "1.000000",
                    # Two forms in one value.
                    LITERAL_ALLOWED_RESOURCE_FORMS: "(RF_LIQUID,RF_GAS)",
                },
            ],
        ),
        group(
            GROUP_FRACKING_ACTIVATOR,
            [
                {
                    KEY_CLASS_NAME: WELL_ACTIVATOR,
                    KEY_DISPLAY_NAME: "Synth Well Activator",
                    # The measured nested-token shape, and NO rate keys.
                    LITERAL_ALLOWED_RESOURCE_FORMS: (
                        "(RF_LIQUID,RF_GAS," + NESTED_INVALID_FORM + ")"
                    ),
                },
            ],
        ),
        group(
            GROUP_MINER_DISPENSER,
            [
                {
                    # No mDisplayName key at all, which is the measured shape.
                    KEY_CLASS_NAME: DISPENSER,
                    LITERAL_ALLOWED_RESOURCE_FORMS: "(RF_SOLID)",
                },
            ],
        ),
        group(
            GROUP_ITEM_DESCRIPTOR,
            [
                {
                    KEY_CLASS_NAME: PLAIN_ITEM,
                    KEY_DISPLAY_NAME: "Synth Ore",
                    KEY_FORM: FORM_SOLID,
                },
            ],
        ),
    ]
    return json.dumps(document)


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Build the registry once for the whole module.

    Returns:
        The registry built from the hand-authored corpus.
    """
    return build_registry(load_document(extraction_docs()))


def warned_subjects(built: Registry, code: str) -> set[str]:
    """Collect the subjects flagged under one warning code.

    Args:
        built: The built registry.
        code: One of the WARN_* constants.

    Returns:
        The set of subjects.
    """
    return {warning.subject for warning in built.warnings if warning.code == code}


def walk_values(value: Any) -> Iterator[Any]:
    """Yield every leaf value reachable from ``value``.

    Args:
        value: The root object.

    Yields:
        Each leaf value. A frozenset of form tokens is descended too, so a
        float hidden in one cannot pass.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for item in dataclasses.fields(value):
            yield from walk_values(getattr(value, item.name))
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from walk_values(item)
    elif isinstance(value, tuple | list | frozenset | set):
        for item in value:
            yield from walk_values(item)
    else:
        yield value


# ---------------------------------------------------------------------------
# The key spellings, and the fixture-parallel-to-implementation guard
# ---------------------------------------------------------------------------


def test_the_registry_key_constants_match_the_measured_spellings() -> None:
    assert KEY_ITEMS_PER_CYCLE == LITERAL_ITEMS_PER_CYCLE
    assert KEY_EXTRACT_CYCLE_TIME == LITERAL_EXTRACT_CYCLE_TIME
    assert KEY_ALLOWED_RESOURCE_FORMS == LITERAL_ALLOWED_RESOURCE_FORMS


def test_the_extraction_marker_keys_are_the_three_measured_fields() -> None:
    # Any-of, exactly as POWER_MARKER_KEYS is: an entry carrying only the rate
    # and an entry carrying only the forms are both extraction content.
    assert set(EXTRACTION_MARKER_KEYS) == {
        LITERAL_ITEMS_PER_CYCLE,
        LITERAL_EXTRACT_CYCLE_TIME,
        LITERAL_ALLOWED_RESOURCE_FORMS,
    }


def test_the_recognized_form_vocabulary_is_the_closed_four() -> None:
    # Sorted on both sides rather than compared as sets, so the assertion is a
    # call rather than a bare name and SIM300 has nothing to reverse.
    assert sorted(RESOURCE_FORMS) == sorted({FORM_SOLID, FORM_LIQUID, FORM_GAS, FORM_INVALID})


# ---------------------------------------------------------------------------
# The rates themselves, exact
# ---------------------------------------------------------------------------


def test_the_registry_publishes_an_extractors_mapping_keyed_by_class_name(
    registry: Registry,
) -> None:
    assert SOLID_MINER in registry.extractors
    assert isinstance(registry.extractors[SOLID_MINER], Extractor)
    assert registry.extractors[SOLID_MINER].key == SOLID_MINER


def test_a_whole_second_cycle_and_a_whole_count_are_exact(registry: Registry) -> None:
    miner = registry.extractors[SOLID_MINER]
    assert miner.items_per_cycle == Fraction(1)
    assert miner.extract_cycle_time == Fraction(1)


def test_a_fractional_cycle_time_is_an_exact_fraction_not_a_float(
    registry: Registry,
) -> None:
    # The TYPE is what this arm pins, because non-negotiable 6 is about the
    # type that reaches the solve path rather than about whether this one
    # decimal happens to be representable in binary.
    faster = registry.extractors[FASTER_MINER]
    assert faster.extract_cycle_time == Fraction(1, 4)
    # The isinstance is the load-bearing half: Fraction(1, 4) compares EQUAL to
    # the float 0.25, so the value assertion above passes just as happily on a
    # value that went through float(). The float exclusion across the whole
    # collection is test_no_value_anywhere_in_the_extractors_is_a_float; a
    # `not isinstance(..., float)` here is statically unreachable and mypy says
    # so, which is why it is not written.
    assert isinstance(faster.extract_cycle_time, Fraction)


def test_no_value_anywhere_in_the_extractors_is_a_float(registry: Registry) -> None:
    leaves = list(walk_values(registry.extractors))
    assert [leaf for leaf in leaves if isinstance(leaf, float)] == []
    # The positive half: "no floats" is also what a walk over nothing reports.
    assert any(isinstance(leaf, Fraction) for leaf in leaves)


def test_a_fluid_extractors_items_per_cycle_stays_verbatim_in_litres(
    registry: Registry,
) -> None:
    # The litre conversion is NOT done here and that is deliberate. The allowed
    # forms are a SET, and which resource an extractor will actually pull is a
    # property of the node it sits on - which ADR 0003 measured as absent from
    # the save. Dividing by LITRES_PER_CUBIC_METRE here would publish 2 items
    # per cycle for a pump the document says moves 2000 litres.
    assert registry.extractors[LIQUID_PUMP].items_per_cycle == Fraction(2000)


def test_a_declared_zero_cycle_time_is_kept_and_is_not_absent(registry: Registry) -> None:
    # Zero and None are different facts, exactly as they are for a recipe
    # duration and for a declared power draw of '0.000000'.
    assert registry.extractors[STOPPED_MINER].extract_cycle_time == Fraction(0)
    assert registry.extractors[STOPPED_MINER].extract_cycle_time is not None


# ---------------------------------------------------------------------------
# The allowed resource forms, including the token the document spells oddly
# ---------------------------------------------------------------------------


def test_a_single_form_is_unwrapped_from_its_parentheses(registry: Registry) -> None:
    # The raw value is '(RF_SOLID)'. A reader comparing it against 'RF_SOLID'
    # matches nothing and reports every extractor as formless.
    assert registry.extractors[SOLID_MINER].allowed_forms == frozenset({FORM_SOLID})


def test_two_forms_in_one_value_both_arrive(registry: Registry) -> None:
    assert registry.extractors[WELL_EXTRACTOR].allowed_forms == frozenset({FORM_LIQUID, FORM_GAS})


def test_allowed_forms_is_an_immutable_frozenset(registry: Registry) -> None:
    assert isinstance(registry.extractors[SOLID_MINER].allowed_forms, frozenset)


def test_a_nested_differently_spelled_token_is_kept_verbatim_and_flagged(
    registry: Registry,
) -> None:
    # The measured value is '(RF_LIQUID,RF_GAS,(INVALID))'. '(INVALID)' is not
    # 'RF_INVALID' and mapping one onto the other would invent a form the
    # document never named. It is kept verbatim, flagged, and left OUT of the
    # recognized set.
    activator = registry.extractors[WELL_ACTIVATOR]
    assert activator.allowed_forms == frozenset({FORM_LIQUID, FORM_GAS})
    assert activator.unrecognized_forms == (NESTED_INVALID_FORM,)
    assert FORM_INVALID not in activator.allowed_forms
    assert WELL_ACTIVATOR in warned_subjects(registry, WARN_UNKNOWN_RESOURCE_FORM)


def test_the_nested_token_does_not_split_on_a_comma_inside_it(
    registry: Registry,
) -> None:
    # A plain str.split(',') over the stripped value yields '(INVALID)' whole
    # only because the measured nesting holds one token. This arm pins the
    # depth-aware split, so a future '(A,B)' group arrives as one unrecognized
    # token rather than as two half-tokens that each look like content.
    assert all(
        token.count("(") == token.count(")")
        for token in registry.extractors[WELL_ACTIVATOR].unrecognized_forms
    )


def test_an_entry_with_no_forms_key_has_an_empty_form_set(registry: Registry) -> None:
    # Empty, not a guessed RF_SOLID.
    assert registry.extractors[RATE_ONLY_MINER].allowed_forms == frozenset()
    assert registry.extractors[RATE_ONLY_MINER].unrecognized_forms == ()


# ---------------------------------------------------------------------------
# Absent and unreadable are None and are flagged - never a number the game
# did not ship
# ---------------------------------------------------------------------------


def test_an_extractor_with_no_rate_keys_reports_none_rather_than_zero(
    registry: Registry,
) -> None:
    # The confident-zero trap Building.power_consumption documents: a rate of
    # zero is a claim, and it is not the claim the document made.
    activator = registry.extractors[WELL_ACTIVATOR]
    assert activator.items_per_cycle is None
    assert activator.extract_cycle_time is None


def test_an_extractor_with_no_rate_keys_is_flagged(registry: Registry) -> None:
    assert WELL_ACTIVATOR in warned_subjects(registry, WARN_MISSING_EXTRACTION_RATE)
    assert DISPENSER in warned_subjects(registry, WARN_MISSING_EXTRACTION_RATE)


def test_an_extractor_with_both_rate_keys_is_not_flagged_as_missing(
    registry: Registry,
) -> None:
    # The negative half, without which a warning that fired on every entry
    # would pass the arm above.
    assert SOLID_MINER not in warned_subjects(registry, WARN_MISSING_EXTRACTION_RATE)


def test_an_unparsable_cycle_time_is_none_and_is_flagged_twice_over(
    registry: Registry,
) -> None:
    # Two codes, exactly as an unreadable power draw produces two: the
    # unparsable number says why it could not be read, and the missing rate
    # says what the consequence is.
    assert registry.extractors[BROKEN_RATE_MINER].extract_cycle_time is None
    assert BROKEN_RATE_MINER in warned_subjects(registry, WARN_UNPARSABLE_NUMBER)
    assert BROKEN_RATE_MINER in warned_subjects(registry, WARN_MISSING_EXTRACTION_RATE)


def test_a_present_but_non_string_rate_is_flagged_as_such_not_as_absent(
    registry: Registry,
) -> None:
    assert registry.extractors[NON_STRING_MINER].items_per_cycle is None
    assert NON_STRING_MINER in warned_subjects(registry, WARN_NON_STRING_VALUE)
    assert NON_STRING_MINER in warned_subjects(registry, WARN_MISSING_EXTRACTION_RATE)


# ---------------------------------------------------------------------------
# What is and is not an extractor, and how it joins
# ---------------------------------------------------------------------------


def test_an_entry_carrying_only_a_rate_key_is_still_an_extractor(
    registry: Registry,
) -> None:
    assert RATE_ONLY_MINER in registry.extractors


def test_an_entry_carrying_only_the_forms_key_is_still_an_extractor(
    registry: Registry,
) -> None:
    assert DISPENSER in registry.extractors


def test_a_plain_item_descriptor_is_not_an_extractor(registry: Registry) -> None:
    assert PLAIN_ITEM not in registry.extractors
    assert PLAIN_ITEM in registry.items


def test_an_extractor_that_draws_power_is_in_both_collections_under_one_key(
    registry: Registry,
) -> None:
    # The join a throughput consumer needs: one ClassName, the rate on one side
    # and the draw on the other.
    assert SOLID_MINER in registry.extractors
    assert SOLID_MINER in registry.buildings
    assert registry.buildings[SOLID_MINER].power_consumption == Fraction(5)


def test_an_extractor_that_declares_no_power_is_still_an_extractor(
    registry: Registry,
) -> None:
    assert LIQUID_PUMP in registry.extractors
    assert LIQUID_PUMP not in registry.buildings


def test_a_display_name_absent_from_the_entry_is_empty_and_flagged(
    registry: Registry,
) -> None:
    # Never defaulted to the ClassName: a synthesized name is indistinguishable
    # from a real one downstream.
    assert registry.extractors[DISPENSER].display_name == ""
    assert GROUP_MINER_DISPENSER in warned_subjects(registry, WARN_EMPTY_DISPLAY_NAME)


def test_a_display_name_present_on_the_entry_is_read_verbatim(registry: Registry) -> None:
    assert registry.extractors[SOLID_MINER].display_name == "Synth Miner Mk.1"


def test_the_extractors_mapping_is_read_only(registry: Registry) -> None:
    with pytest.raises(TypeError):
        registry.extractors[STOPPED_MINER] = registry.extractors[SOLID_MINER]  # type: ignore[index]


def test_the_extractor_model_is_frozen(registry: Registry) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        registry.extractors[SOLID_MINER].items_per_cycle = Fraction(99)  # type: ignore[misc]
