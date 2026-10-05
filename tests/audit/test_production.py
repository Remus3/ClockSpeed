"""CS-1059: generated power as the exact sum over built generators.

Every fixture here is a hand-built synthetic literal. Nothing in this module
opens a save, a docs file or the install - see ``tests/audit/__init__.py`` for
the four rules that bind every module in this directory.

THE THREE CLAUSES THIS MODULE GRADES, and how each is built to redden.

- THE SUM IS EXACT. One fixture generator produces ``Fraction(1, 3)``, so an
  implementation accumulating in binary floating point cannot return the
  asserted ``Fraction(26, 3)``, and the walk over the output refuses a float
  anywhere in it.
- AN UNMODELED GENERATOR IS A NAMED GAP, NEVER A ZERO, exactly as ``DrawGap``
  refuses one: ``ProductionGap`` DECLARES NO MEGAWATTS FIELD, graded off the
  dataclass's own fields. The geothermal shape - a declared scalar zero beside a
  variable factor - is the fixture that matters, because summing its declared
  zero yields a total that is right in aggregate and wrong in meaning. Each gap
  is asserted PER CONTRIBUTOR with its own kind and count.
- THE FLAG IS COMPUTED. ``WorldBalance.production_available`` is asserted False
  over one input and True over another that differs ONLY in whether the
  generator namespace was supplied, so a literal of either value reddens one
  of the pair; and it is asserted equal to whether a production model exists,
  so it cannot drift from the figure it describes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields
from fractions import Fraction
from types import MappingProxyType
from typing import Final

from clockspeed.audit import balance, machines, placement
from clockspeed.data.registry import Building, Generator
from tests.audit import test_balance as balance_fx

#: Invented generator classes, one per shape.
GEN_WHOLE: Final = "Build_SyntheticGenWholeQx59_C"
GEN_THIRD: Final = "Build_SyntheticGenThirdQx59_C"
GEN_CYCLING: Final = "Build_SyntheticGenCyclingQx59_C"
GEN_SILENT: Final = "Build_SyntheticGenSilentQx59_C"
GEN_INEXACT: Final = "Build_SyntheticGenInexactQx59_C"

#: A built class that neither namespace carries - it may generate, and nothing
#: here can say it does not.
STRANGER: Final = "Build_SyntheticStrangerQx59_C"

WHOLE_MEGAWATTS: Final = Fraction(75)
WHOLE_BUILT: Final = 1
THIRD_MEGAWATTS: Final = Fraction(1, 3)
THIRD_BUILT: Final = 2
#: 75 * 1 + 1/3 * 2 = 227/3. No binary float holds it.
EXPECTED_CAPACITY: Final = Fraction(227, 3)

CYCLING_BUILT: Final = 3
SILENT_BUILT: Final = 5
INEXACT_BUILT: Final = 7
STRANGER_BUILT: Final = 4


def generator(
    key: str,
    *,
    production: Fraction | float | None,
    variable: bool = False,
) -> Generator:
    """Build one synthetic generator entry.

    Args:
        key: The entry's ClassName.
        production: The declared scalar output, or None for no readable one.
        variable: Whether the entry declares a variable output.

    Returns:
        The entry.
    """
    return Generator(
        key=key,
        display_name=f"Synthetic {key}",
        power_production=production,  # type: ignore[arg-type]
        variable_production_constant=Fraction(0) if variable else None,
        variable_production_factor=Fraction(200) if variable else None,
        is_variable_production=variable,
    )


def generators(*entries: Generator) -> Mapping[str, Generator]:
    """Build a generator mapping over the supplied entries.

    Args:
        entries: The entries, each keyed by its own ``key``.

    Returns:
        The mapping.
    """
    return MappingProxyType({entry.key: entry for entry in entries})


def modeled_generators() -> Mapping[str, Generator]:
    """Two generators, both with an exact scalar output.

    Returns:
        The mapping.
    """
    return generators(
        generator(GEN_WHOLE, production=WHOLE_MEGAWATTS),
        generator(GEN_THIRD, production=THIRD_MEGAWATTS),
    )


def whole_world_generators() -> Mapping[str, Generator]:
    """Every generator shape: two modeled, three not.

    Returns:
        The mapping.
    """
    return generators(
        generator(GEN_WHOLE, production=WHOLE_MEGAWATTS),
        generator(GEN_THIRD, production=THIRD_MEGAWATTS),
        # The geothermal shape: a DECLARED zero that is not its output.
        generator(GEN_CYCLING, production=Fraction(0), variable=True),
        generator(GEN_SILENT, production=None),
        generator(GEN_INEXACT, production=0.5),
    )


def generator_consumers() -> Mapping[str, Building]:
    """The consumer namespace, carrying every generator at its declared zero draw.

    Measured: every shipped generator also declares ``mPowerConsumption`` as
    ``'0.000000'``, so the registry lands each in ``buildings`` too.

    Returns:
        The two consumers of the balance fixture plus every generator.
    """
    entries = dict(balance_fx.modeled_registry())
    for key in (GEN_WHOLE, GEN_THIRD, GEN_CYCLING, GEN_SILENT, GEN_INEXACT):
        entries[key] = balance_fx.building(key, consumption=Fraction(0))
    return MappingProxyType(entries)


def modeled_world_counts() -> Mapping[str, int]:
    """Two modeled generators and the two consumers.

    Returns:
        The built counts.
    """
    return {
        **balance_fx.modeled_counts(),
        GEN_WHOLE: WHOLE_BUILT,
        GEN_THIRD: THIRD_BUILT,
    }


def whole_world_counts() -> Mapping[str, int]:
    """Every generator shape, the two consumers, and a stranger.

    Returns:
        The built counts.
    """
    return {
        **modeled_world_counts(),
        GEN_CYCLING: CYCLING_BUILT,
        GEN_SILENT: SILENT_BUILT,
        GEN_INEXACT: INEXACT_BUILT,
        STRANGER: STRANGER_BUILT,
    }


def production(counts: Mapping[str, int], gens: Mapping[str, Generator]) -> balance.WorldProduction:
    """Compute the production model over one fixture.

    Args:
        counts: The built counts.
        gens: The generator namespace.

    Returns:
        The model.
    """
    return balance.production_of(balance_fx.built(counts), gens, generator_consumers())


# ---------------------------------------------------------------------------
# Clause one - the exact sum over built generators
# ---------------------------------------------------------------------------


def test_the_capacity_is_the_exact_fraction_sum_over_built_generators() -> None:
    result = production(modeled_world_counts(), modeled_generators())

    assert type(result.capacity_megawatts) is Fraction
    assert result.capacity_megawatts == EXPECTED_CAPACITY
    assert result.production_complete is True


def test_each_generator_carries_its_own_count_and_its_own_product() -> None:
    result = production(modeled_world_counts(), modeled_generators())

    by_class = {item.class_name: item for item in result.contributions}
    assert set(by_class) == {GEN_WHOLE, GEN_THIRD}
    assert by_class[GEN_THIRD].built_count == THIRD_BUILT
    assert by_class[GEN_THIRD].megawatts_each == THIRD_MEGAWATTS
    assert by_class[GEN_THIRD].megawatts_total == THIRD_MEGAWATTS * THIRD_BUILT


def test_no_float_reaches_any_production_output_field() -> None:
    # The input carries a float, which is the control that the walk sees one.
    assert any(type(value) is float for value in balance_fx.reachable(whole_world_generators()))
    result = production(whole_world_counts(), whole_world_generators())

    assert not [value for value in balance_fx.reachable(result) if type(value) is float]


def test_a_consumer_is_never_counted_as_a_generator() -> None:
    result = production(modeled_world_counts(), modeled_generators())

    named = {item.class_name for item in result.contributions} | {
        item.class_name for item in result.gaps
    }
    assert not named & set(balance_fx.modeled_counts())
    assert result.non_generator_class_count == len(balance_fx.modeled_counts())


# ---------------------------------------------------------------------------
# Clause two - an unmodeled generator is a NAMED gap, never a zero
# ---------------------------------------------------------------------------


def test_a_production_gap_has_no_megawatts_field_to_read_a_zero_out_of() -> None:
    """Structural, exactly as ``DrawGap`` is graded in ``test_balance.py``."""
    declared = {field.name for field in fields(balance.ProductionGap)}

    assert not [name for name in declared if "megawatt" in name or "power" in name]


def test_each_unmodeled_generator_contributes_its_own_named_gap() -> None:
    result = production(whole_world_counts(), whole_world_generators())

    by_class = {gap.class_name: gap for gap in result.gaps}
    assert by_class[GEN_CYCLING].kind == balance.GAP_PRODUCTION_VARIABLE
    assert by_class[GEN_CYCLING].built_count == CYCLING_BUILT
    assert by_class[GEN_SILENT].kind == balance.GAP_PRODUCTION_UNDECLARED
    assert by_class[GEN_SILENT].built_count == SILENT_BUILT
    assert by_class[GEN_INEXACT].kind == balance.GAP_PRODUCTION_INEXACT
    assert by_class[GEN_INEXACT].built_count == INEXACT_BUILT
    assert by_class[STRANGER].kind == balance.GAP_NO_REGISTRY_ENTRY
    assert by_class[STRANGER].built_count == STRANGER_BUILT
    assert all(gap.reason for gap in result.gaps)
    assert {gap.kind for gap in result.gaps} <= balance.PRODUCTION_GAP_KINDS


def test_the_declared_zero_of_a_variable_generator_is_never_a_summand() -> None:
    result = production(whole_world_counts(), whole_world_generators())

    contributing = {item.class_name for item in result.contributions}
    assert contributing == {GEN_WHOLE, GEN_THIRD}
    assert result.capacity_megawatts == EXPECTED_CAPACITY
    assert result.production_complete is False


def test_the_production_buckets_partition_the_built_classes_with_conservation() -> None:
    counts = whole_world_counts()
    result = production(counts, whole_world_generators())

    assert (
        len(result.contributions) + len(result.gaps) + result.non_generator_class_count
        == result.classes_considered
        == len(counts)
    )
    assert result.unmodeled_class_count == len(result.gaps)
    assert result.unmodeled_contributor_count == (
        CYCLING_BUILT + SILENT_BUILT + INEXACT_BUILT + STRANGER_BUILT
    )
    codes = {warning.code: warning.count for warning in result.warnings}
    assert codes[balance.WARN_BALANCE_GENERATION_UNMODELED] == result.unmodeled_contributor_count


def test_every_production_model_names_its_figure_a_reference_clock_capacity() -> None:
    result = production(modeled_world_counts(), modeled_generators())

    assert balance.WARN_BALANCE_PRODUCTION_NAMEPLATE in {w.code for w in result.warnings}


def test_the_production_repr_renders_counts_and_no_class_name() -> None:
    rendered = repr(production(whole_world_counts(), whole_world_generators()))

    assert GEN_WHOLE not in rendered
    assert STRANGER not in rendered


# ---------------------------------------------------------------------------
# Generators are not consumers
# ---------------------------------------------------------------------------


def test_a_supplied_generator_namespace_takes_generators_out_of_the_draw() -> None:
    placed = balance_fx.built(modeled_world_counts())
    result = balance.draw_of(placed, generator_consumers(), generators=modeled_generators())

    named = {item.class_name for item in result.contributions} | {
        item.class_name for item in result.gaps
    }
    assert named == set(balance_fx.modeled_counts())
    assert result.generator_class_count == len(modeled_generators())
    assert result.consumption_megawatts == balance_fx.EXPECTED_CONSUMPTION


def test_without_the_namespace_the_draw_is_unchanged() -> None:
    """The control: the exclusion above is the namespace's doing and nothing else."""
    result = balance.draw_of(balance_fx.built(modeled_world_counts()), generator_consumers())

    named = {item.class_name for item in result.contributions}
    assert GEN_WHOLE in named
    assert result.generator_class_count == 0


def test_a_generator_machine_is_not_priced_as_a_consumer() -> None:
    states = (
        machines.MachineState(
            class_name=GEN_WHOLE, producing=True, recipe_class_name=None, overclock=Fraction(1)
        ),
        machines.MachineState(
            class_name=balance_fx.FIXED_WHOLE,
            producing=True,
            recipe_class_name=None,
            overclock=Fraction(1),
        ),
    )
    world = balance_fx.world_machines(*states)

    with_gens = balance.clocked_draw_of(
        world, generator_consumers(), generators=modeled_generators()
    )
    without = balance.clocked_draw_of(world, generator_consumers())

    assert {group.class_name for group in with_gens.contributions} == {balance_fx.FIXED_WHOLE}
    assert with_gens.generator_machine_count == 1
    assert {group.class_name for group in without.contributions} == {
        GEN_WHOLE,
        balance_fx.FIXED_WHOLE,
    }
    assert without.generator_machine_count == 0


# ---------------------------------------------------------------------------
# Clause three - production_available is computed, never a literal
# ---------------------------------------------------------------------------


def composite(gens: Mapping[str, Generator] | None) -> balance.WorldBalance:
    """The composite balance over one modelled world, with or without generators.

    Args:
        gens: The generator namespace, or None to supply none.

    Returns:
        The balance.
    """
    return balance.balance_of(
        balance_fx.built(modeled_world_counts()),
        generator_consumers(),
        balance_fx.world_machines(),
        balance_fx.world_network(),
        generators=gens,
    )


def test_the_flag_is_true_only_when_a_production_figure_was_computed() -> None:
    computed = composite(modeled_generators())
    omitted = composite(None)

    assert computed.production_available is True
    assert computed.production is not None
    assert computed.production.capacity_megawatts == EXPECTED_CAPACITY
    assert omitted.production_available is False
    assert omitted.production is None


def test_an_empty_generator_namespace_computes_no_figure() -> None:
    """A registry that models no generator has nothing to sum - not a zero."""
    result = composite(generators())

    assert result.production_available is False
    assert result.production is None


def test_the_flag_always_agrees_with_the_presence_of_the_figure() -> None:
    for gens in (None, generators(), modeled_generators(), whole_world_generators()):
        result = composite(gens)
        assert result.production_available is (result.production is not None)


def test_the_unmodeled_advisory_travels_only_when_no_figure_was_computed() -> None:
    computed = {w.code for w in composite(modeled_generators()).warnings}
    omitted = {w.code for w in composite(None).warnings}

    assert balance.WARN_BALANCE_PRODUCTION_UNMODELED not in computed
    assert balance.WARN_BALANCE_PRODUCTION_UNMODELED in omitted
    assert balance.WARN_BALANCE_PRODUCTION_NAMEPLATE in computed


def test_the_composite_draw_excludes_generators_once_the_namespace_is_supplied() -> None:
    result = composite(modeled_generators())

    assert result.draw.generator_class_count == len(modeled_generators())
    assert result.draw.consumption_megawatts == balance_fx.EXPECTED_CONSUMPTION


# ---------------------------------------------------------------------------
# End to end through the REAL placement filter - the arms above write their own
# built_counts and so never met placement's allowlist, which is how a dropped
# generator class read as a complete capacity.
# ---------------------------------------------------------------------------

#: Real built-class spellings, measured as ClassName in the shipped docs.
COAL: Final = "Build_GeneratorCoal_C"
FUEL: Final = "Build_GeneratorFuel_C"
NUCLEAR: Final = "Build_GeneratorNuclear_C"
GEOTHERMAL: Final = "Build_GeneratorGeoThermal_C"

COAL_MEGAWATTS: Final = Fraction(75)
FUEL_MEGAWATTS: Final = Fraction(250)
NUCLEAR_MEGAWATTS: Final = Fraction(2500)


def real_generators() -> Mapping[str, Generator]:
    """The four generator shapes under their real built-class spellings.

    Returns:
        The mapping.
    """
    return generators(
        generator(COAL, production=COAL_MEGAWATTS),
        generator(FUEL, production=FUEL_MEGAWATTS),
        generator(NUCLEAR, production=NUCLEAR_MEGAWATTS),
        generator(GEOTHERMAL, production=Fraction(0), variable=True),
    )


def real_consumers() -> Mapping[str, Building]:
    """Every real generator at its declared zero draw, as the registry lands it.

    Returns:
        The mapping.
    """
    return MappingProxyType(
        {key: balance_fx.building(key, consumption=Fraction(0)) for key in real_generators()}
    )


def through_placement(*class_names: str) -> balance.WorldBalance:
    """Run a world of one record per class through placement_of, then balance_of.

    Args:
        class_names: The built class of each record.

    Returns:
        The balance.
    """
    placed = placement.placement_of(balance_fx.world_of(*class_names))
    return balance.balance_of(
        placed,
        real_consumers(),
        balance_fx.world_machines(),
        balance_fx.world_network(),
        generators=real_generators(),
    )


def test_every_fuel_and_nuclear_generator_survives_placement_into_the_capacity() -> None:
    result = through_placement(COAL, FUEL, NUCLEAR)

    assert result.production is not None
    assert result.production.capacity_megawatts == (
        COAL_MEGAWATTS + FUEL_MEGAWATTS + NUCLEAR_MEGAWATTS
    )
    assert result.production.production_complete is True


def test_a_geothermal_generator_survives_placement_as_a_named_variable_gap() -> None:
    result = through_placement(COAL, GEOTHERMAL)

    assert result.production is not None
    gaps = {gap.class_name: gap.kind for gap in result.production.gaps}
    assert gaps == {GEOTHERMAL: balance.GAP_PRODUCTION_VARIABLE}
    assert result.production.production_complete is False
    assert result.production.capacity_megawatts == COAL_MEGAWATTS
