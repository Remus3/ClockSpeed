"""CS-1059 - the generator namespace the registry lands out of the docs.

Every byte of the corpus below is hand-authored in THIS file. Nothing here
reads the real install, the real docs file or a save, so the whole module runs
on a machine that has never had the game on it - the rule
``tests/data/__init__.py`` states and ``tests/data/synthetic.py`` obeys.

THE MEASURED SHAPES THIS CORPUS REPRODUCES
------------------------------------------
Measured read-only against the shipped docs before any of this was written,
and recorded in ``docs/item_notes/phase5.md`` under CS-1059:

- Every fuel and nuclear generator carries a scalar ``mPowerProduction`` as a
  decimal string. It is read STRAIGHT to an exact Fraction, never via float.
- The geothermal generator declares ``mPowerProduction`` as ``'0.000000'`` and
  carries its real output on ``mVariablePowerProductionConstant`` and
  ``mVariablePowerProductionFactor``. That declared zero is NOT its output. The
  registry keeps the declaration verbatim and marks the entry variable, so the
  balance layer can refuse it as a named gap rather than sum a confident zero.
- Every generator ALSO declares ``mPowerConsumption`` as ``'0.000000'``, so the
  same entry lands in ``Registry.buildings`` too. The two namespaces are joined
  by key, exactly as ``Registry.extractors`` is.

The key spellings are LITERALS here, for the reason
``tests/data/test_extraction_rates.py`` gives: a fixture importing the
registry's own constants stays green through a misspelling.
"""

from __future__ import annotations

import json
from fractions import Fraction
from typing import Any, Final

import pytest

from clockspeed.data.docs_extract import load_document
from clockspeed.data.registry import (
    GENERATION_MARKER_KEYS,
    KEY_POWER_PRODUCTION,
    KEY_VARIABLE_PRODUCTION_CONSTANT,
    KEY_VARIABLE_PRODUCTION_FACTOR,
    WARN_MISSING_PRODUCTION,
    WARN_NON_STRING_VALUE,
    WARN_UNPARSABLE_NUMBER,
    Generator,
    Registry,
    build_registry,
)

LITERAL_POWER_PRODUCTION: Final = "mPowerProduction"
LITERAL_VARIABLE_CONSTANT: Final = "mVariablePowerProductionConstant"
LITERAL_VARIABLE_FACTOR: Final = "mVariablePowerProductionFactor"

KEY_CLASS_NAME: Final = "ClassName"
KEY_DISPLAY_NAME: Final = "mDisplayName"
KEY_NATIVE_CLASS: Final = "NativeClass"
KEY_CLASSES: Final = "Classes"
KEY_POWER_CONSUMPTION: Final = "mPowerConsumption"
KEY_POWER_EXPONENT: Final = "mPowerConsumptionExponent"

# The group short names are REAL - they are the join keys the loader dispatches
# on, and a corpus using invented ones would exercise nothing.
GROUP_FUEL: Final = "FGBuildableGeneratorFuel"
GROUP_GEOTHERMAL: Final = "FGBuildableGeneratorGeoThermal"
GROUP_MANUFACTURER: Final = "FGBuildableManufacturer"

# Every ClassName below is invented.
WHOLE_GENERATOR: Final = "Build_SynthGenWhole_C"
HALF_GENERATOR: Final = "Build_SynthGenHalf_C"
CYCLING_GENERATOR: Final = "Build_SynthGenCycling_C"
BROKEN_GENERATOR: Final = "Build_SynthGenBroken_C"
NON_STRING_GENERATOR: Final = "Build_SynthGenNonString_C"
FACTOR_ONLY_GENERATOR: Final = "Build_SynthGenFactorOnly_C"
PLAIN_CONSUMER: Final = "Build_SynthConsumer_C"


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


def generation_docs() -> str:
    """Author the whole corpus this module is graded against.

    Returns:
        The docs text, as JSON. No group, key or value is read from disk.
    """
    document = [
        group(
            GROUP_FUEL,
            [
                {
                    KEY_CLASS_NAME: WHOLE_GENERATOR,
                    KEY_DISPLAY_NAME: "Synth Whole Generator",
                    LITERAL_POWER_PRODUCTION: "75.000000",
                    KEY_POWER_CONSUMPTION: "0.000000",
                    KEY_POWER_EXPONENT: "1.600000",
                },
                {
                    KEY_CLASS_NAME: HALF_GENERATOR,
                    KEY_DISPLAY_NAME: "Synth Half Generator",
                    # Exact as Fraction(25, 2); a float path still gets this one
                    # right, so the float refusal is graded in the balance arms.
                    LITERAL_POWER_PRODUCTION: "12.500000",
                    KEY_POWER_CONSUMPTION: "0.000000",
                },
                {
                    KEY_CLASS_NAME: BROKEN_GENERATOR,
                    KEY_DISPLAY_NAME: "Synth Broken Generator",
                    # Unparsable. Never zero.
                    LITERAL_POWER_PRODUCTION: "lots",
                    KEY_POWER_CONSUMPTION: "0.000000",
                },
                {
                    KEY_CLASS_NAME: NON_STRING_GENERATOR,
                    KEY_DISPLAY_NAME: "Synth Non String Generator",
                    # Present but not a string: a different fact from absent.
                    LITERAL_POWER_PRODUCTION: ["75.000000"],
                },
            ],
        ),
        group(
            GROUP_GEOTHERMAL,
            [
                {
                    # The measured geothermal shape: a DECLARED scalar zero
                    # beside a variable factor that carries the real output.
                    KEY_CLASS_NAME: CYCLING_GENERATOR,
                    KEY_DISPLAY_NAME: "Synth Cycling Generator",
                    LITERAL_VARIABLE_CONSTANT: "0.000000",
                    LITERAL_VARIABLE_FACTOR: "200.000000",
                    LITERAL_POWER_PRODUCTION: "0.000000",
                    KEY_POWER_CONSUMPTION: "0.000000",
                },
                {
                    # No scalar at all, only the factor: still a generator, on
                    # the any-of rule the other marker tuples use.
                    KEY_CLASS_NAME: FACTOR_ONLY_GENERATOR,
                    KEY_DISPLAY_NAME: "Synth Factor Only Generator",
                    LITERAL_VARIABLE_FACTOR: "50.000000",
                },
            ],
        ),
        group(
            GROUP_MANUFACTURER,
            [
                {
                    KEY_CLASS_NAME: PLAIN_CONSUMER,
                    KEY_DISPLAY_NAME: "Synth Consumer",
                    KEY_POWER_CONSUMPTION: "4.000000",
                    KEY_POWER_EXPONENT: "1.321929",
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
    return build_registry(load_document(generation_docs()))


def warned_subjects(built: Registry, code: str) -> set[str]:
    """Collect the subjects flagged under one warning code.

    Args:
        built: The built registry.
        code: One of the WARN_* constants.

    Returns:
        The set of subjects.
    """
    return {warning.subject for warning in built.warnings if warning.code == code}


def test_the_registry_key_constants_match_the_measured_spellings() -> None:
    assert KEY_POWER_PRODUCTION == LITERAL_POWER_PRODUCTION
    assert KEY_VARIABLE_PRODUCTION_CONSTANT == LITERAL_VARIABLE_CONSTANT
    assert KEY_VARIABLE_PRODUCTION_FACTOR == LITERAL_VARIABLE_FACTOR


def test_the_generation_marker_keys_are_the_three_measured_fields() -> None:
    assert set(GENERATION_MARKER_KEYS) == {
        LITERAL_POWER_PRODUCTION,
        LITERAL_VARIABLE_CONSTANT,
        LITERAL_VARIABLE_FACTOR,
    }


def test_every_generator_entry_and_no_consumer_lands_in_the_namespace(
    registry: Registry,
) -> None:
    assert set(registry.generators) == {
        WHOLE_GENERATOR,
        HALF_GENERATOR,
        CYCLING_GENERATOR,
        BROKEN_GENERATOR,
        NON_STRING_GENERATOR,
        FACTOR_ONLY_GENERATOR,
    }


def test_a_scalar_production_is_read_as_an_exact_fraction(registry: Registry) -> None:
    whole = registry.generators[WHOLE_GENERATOR]
    half = registry.generators[HALF_GENERATOR]

    assert type(whole.power_production) is Fraction
    assert whole.power_production == Fraction(75)
    assert type(half.power_production) is Fraction
    assert half.power_production == Fraction(25, 2)
    assert whole.is_variable_production is False


def test_the_geothermal_shape_is_variable_and_keeps_its_declared_zero_verbatim(
    registry: Registry,
) -> None:
    cycling = registry.generators[CYCLING_GENERATOR]

    assert cycling.is_variable_production is True
    assert cycling.variable_production_factor == Fraction(200)
    assert cycling.variable_production_constant == Fraction(0)
    # Verbatim, and a DIFFERENT fact from its output - the balance refuses it.
    assert cycling.power_production == Fraction(0)


def test_a_factor_only_entry_is_variable_and_declares_no_scalar(registry: Registry) -> None:
    entry = registry.generators[FACTOR_ONLY_GENERATOR]

    assert entry.is_variable_production is True
    assert entry.power_production is None


def test_an_unreadable_production_is_none_and_flagged_never_zero(registry: Registry) -> None:
    broken = registry.generators[BROKEN_GENERATOR]
    non_string = registry.generators[NON_STRING_GENERATOR]

    assert broken.power_production is None
    assert non_string.power_production is None
    assert BROKEN_GENERATOR in warned_subjects(registry, WARN_UNPARSABLE_NUMBER)
    assert NON_STRING_GENERATOR in warned_subjects(registry, WARN_NON_STRING_VALUE)
    missing = warned_subjects(registry, WARN_MISSING_PRODUCTION)
    assert missing == {BROKEN_GENERATOR, NON_STRING_GENERATOR}


def test_a_generator_still_joins_the_consumer_namespace_by_key(registry: Registry) -> None:
    # The two namespaces are separate and joined by key, as extractors are.
    assert WHOLE_GENERATOR in registry.buildings
    assert PLAIN_CONSUMER in registry.buildings
    assert PLAIN_CONSUMER not in registry.generators


def test_the_generator_model_declares_no_float_typed_field() -> None:
    # Construction with exact values is the control that the type is usable.
    entry = Generator(
        key=WHOLE_GENERATOR,
        display_name="Synth",
        power_production=Fraction(1, 3),
        variable_production_constant=None,
        variable_production_factor=None,
        is_variable_production=False,
    )
    assert entry.power_production == Fraction(1, 3)


def test_a_default_registry_carries_an_empty_read_only_generator_namespace() -> None:
    empty = Registry(items={}, recipes={}, buildings={}, warnings=(), unknown_groups=())

    assert dict(empty.generators) == {}
    with pytest.raises(TypeError):
        empty.generators["x"] = None  # type: ignore[index]
