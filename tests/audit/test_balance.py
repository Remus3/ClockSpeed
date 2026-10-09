"""CS-1045: the world power draw over built counts, and the starved-machine set.

Every fixture here is a hand-built synthetic literal. Nothing in this module
opens a save, a docs file or the install - see ``tests/audit/__init__.py`` for
the four rules that bind every module in this directory.

THE CONFIDENT ZERO IS THE DEFECT THIS MODULE EXISTS TO CATCH. A built class
whose draw the registry does not model contributes NO NUMBER to the world total,
and the arms below grade that three separate ways, because any one of them alone
passes on a near-miss.

- The class lands in :attr:`WorldDraw.gaps` under its own NAMED kind, asserted
  PER CONTRIBUTOR and never over the pool. A total that is right in aggregate
  can hide a class whose draw was never modelled, so summing alone grades
  nothing about which class went missing.
- ``DrawGap`` CARRIES NO MEGAWATTS FIELD AT ALL, so the zero is structurally
  unrepresentable rather than merely absent today. That is graded by
  ``test_a_gap_has_no_megawatts_field_to_read_a_zero_out_of``, which reads the
  dataclass' declared fields rather than one instance's values - an arm
  asserting ``gap.megawatts is None`` would pass the day somebody adds the
  field back and defaults it to zero.
- The two buckets PARTITION the built classes with conservation:
  ``len(contributions) + len(gaps) == len(built_counts)`` and the two class-name
  sets are disjoint. A dropped class cannot be expressed. That is the shape
  ``docs/item_notes/phase5.md`` records for CS-1042, applied to a different
  population: an Optional, a flag and a count are each individually ignorable,
  and a partition is not.

THE SUM IS GRADED WITH A VALUE NO FLOAT HOLDS. One fixture class draws
``Fraction(1, 3)``, so an implementation that accumulates in binary floating
point returns ``38.00000000000001 / 3``-shaped garbage and not ``Fraction(38, 3)``.
An arm asserting only ``isinstance(total, Fraction)`` would pass on the defect,
and an arm summing whole numbers would pass on it too.

WHAT ARM TWO'S FIXTURE IS BUILT TO REFUSE. The flagged set is exactly the
starved machine, and the arm that grades the producing flag uses a fixture whose
two machines are IDENTICAL in class, recipe and overclock and differ ONLY in
``producing``. No earlier check can refuse that fixture first, so nothing but the
producing clause can decide the answer: ignoring the flag yields either the empty
set or both machines, and neither equals the one-element set the arm asserts.
That is the masked-clause trap this session measured three times, headed off by
construction rather than by hope.
"""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from fractions import Fraction
from types import MappingProxyType

import pytest

from clockspeed.audit import balance, machines, network, placement
from clockspeed.data.registry import Building, Generator
from clockspeed.save import objects, world
from clockspeed.save.header import SaveHeader
from clockspeed.save.world import (
    EMPTY_UNLOCK_STATE,
    RecordProperties,
    WorldModel,
    WorldProperties,
)
from clockspeed.solve import exact, power
from tests.audit import test_machines as machines_fx
from tests.save import synthetic as save_synthetic
from tests.save import test_objects as objects_fx

# An invented 22-character base64url literal. Never a real world token.
SYNTHETIC_TOKEN = "ClockspeedBalanceTok1"  # noqa: S105 - an invented marker, not a secret

SYNTHETIC_LEVEL = "SyntheticLevel:SyntheticPersistent"

#: The machine's own instance path, and the marker the refusal sweep hunts.
MACHINE_INSTANCE = f"{SYNTHETIC_LEVEL}.SyntheticBalanceQx73_C_7301"

#: Two invented built classes whose entries declare a readable scalar draw.
FIXED_WHOLE = "Build_SyntheticWholeQx73_C"
FIXED_THIRD = "Build_SyntheticThirdQx73_C"

#: Four invented built classes, one per gap kind this module can produce.
DECLARED_VARIABLE = "Build_SyntheticVariableQx73_C"
DECLARED_RANGE = "Build_SyntheticRangeQx73_C"
DECLARED_NOTHING = "Build_SyntheticSilentQx73_C"
NOT_IN_REGISTRY = "Build_SyntheticStrangerQx73_C"
DECLARED_INEXACT = "Build_SyntheticInexactQx73_C"

#: The allowlisted spelling the one end-to-end arm needs, so that arm grades the
#: real ``placement_of`` filter rather than a built_counts mapping this module
#: wrote itself. Read off ``clockspeed/audit/placement.py``
#: ``BUILT_CLASS_ALLOWLIST``, which is the only list that admits a built record.
ALLOWLISTED_CLASS = "Build_SmelterMk1_C"

#: A shipped asset path under a permitted root: what a recipe reference is.
RECIPE_ASSET = "/Game/FactoryGame/Synthetic/Recipe_SyntheticQx73.Recipe_SyntheticQx73_C"
RECIPE_CLASS = "Recipe_SyntheticQx73_C"

MACHINE_CLASS = "Build_SyntheticBalanceQx73_C"

#: The scalar draw of :data:`FIXED_WHOLE`, and how many are built.
WHOLE_MEGAWATTS = Fraction(4)
WHOLE_BUILT = 3

#: The scalar draw of :data:`FIXED_THIRD`, and how many are built. THE THIRD IS
#: THE POINT - see the module docstring.
THIRD_MEGAWATTS = Fraction(1, 3)
THIRD_BUILT = 2

#: ``4 * 3 + (1/3) * 2``, which no binary float holds.
EXPECTED_CONSUMPTION = Fraction(38, 3)

#: How many built classes the modeled-only fixture carries.
MODELED_CLASS_COUNT = 2

#: The built counts of the four gap classes, chosen distinct so a swap shows.
VARIABLE_BUILT = 5
RANGE_BUILT = 7
SILENT_BUILT = 11
STRANGER_BUILT = 4

#: How many classes and how many BUILT ACTORS the whole-world fixture leaves
#: unmodeled. The second is the count the item filing names, and it is not the
#: first: four classes, eighteen buildings.
EXPECTED_GAP_CLASSES = 4
EXPECTED_GAP_CONTRIBUTORS = VARIABLE_BUILT + RANGE_BUILT + SILENT_BUILT + STRANGER_BUILT

#: How many built classes the whole-world fixture carries in total.
EXPECTED_CLASSES_CONSIDERED = MODELED_CLASS_COUNT + EXPECTED_GAP_CLASSES

#: How many machines the four-category starvation fixture carries.
CATEGORY_MACHINE_COUNT = 4

#: Where the one starved machine sits in that fixture.
STARVED_SLOT = 1

#: How many machines the producing-flag discriminator fixture carries.
DISCRIMINATOR_MACHINE_COUNT = 2

#: How many machines carry no producing flag in the unavailable fixture.
UNKNOWN_MACHINE_COUNT = 3


# ---------------------------------------------------------------------------
# Fixtures - every one a literal, and none built by the code under test
# ---------------------------------------------------------------------------


def building(
    key: str,
    *,
    consumption: Fraction | float | None = None,
    minimum: Fraction | None = None,
    maximum: Fraction | None = None,
    variable: bool = False,
    exponent: Fraction | float | None = Fraction(1),
) -> Building:
    """Build one synthetic registry entry.

    Args:
        key: The entry's ClassName, which is the token a built count is keyed by.
        consumption: The declared scalar draw, or None for no readable scalar.
        minimum: The low end of a declared range.
        maximum: The high end of a declared range.
        variable: Whether the entry declares an estimated maximum above zero.
        exponent: The declared clock exponent, or None for an entry that is not
            clock-scalable. Whole by default, so the CS-1045 arms above price
            nothing but the reference clock.

    Returns:
        The entry.
    """
    return Building(
        key=key,
        display_name=f"Synthetic {key}",
        power_consumption=consumption,  # type: ignore[arg-type]
        power_exponent=exponent,  # type: ignore[arg-type]
        estimated_min_power=minimum,
        estimated_max_power=maximum,
        is_variable_power=variable,
    )


def registry(*entries: Building) -> Mapping[str, Building]:
    """Build a registry mapping over the supplied entries.

    Args:
        entries: The entries, each keyed by its own ``key``.

    Returns:
        The mapping.
    """
    return MappingProxyType({entry.key: entry for entry in entries})


def modeled_registry() -> Mapping[str, Building]:
    """The registry the exact-sum arms use: two entries, both modeled.

    Returns:
        The mapping.
    """
    return registry(
        building(FIXED_WHOLE, consumption=WHOLE_MEGAWATTS),
        building(FIXED_THIRD, consumption=THIRD_MEGAWATTS),
    )


def whole_world_registry() -> Mapping[str, Building]:
    """The registry the partition arms use: two modeled, three unmodeled.

    :data:`NOT_IN_REGISTRY` is deliberately absent, which is the fourth gap kind.

    Returns:
        The mapping.
    """
    return registry(
        building(FIXED_WHOLE, consumption=WHOLE_MEGAWATTS),
        building(FIXED_THIRD, consumption=THIRD_MEGAWATTS),
        building(
            DECLARED_VARIABLE,
            consumption=Fraction(0),
            minimum=Fraction(0),
            maximum=Fraction(100),
            variable=True,
        ),
        building(
            DECLARED_RANGE,
            minimum=Fraction(0),
            maximum=Fraction(50),
            variable=True,
        ),
        building(DECLARED_NOTHING),
    )


def built(counts: Mapping[str, int]) -> placement.WorldPlacement:
    """Build a placement model carrying nothing but the built counts.

    THE OTHER FIELDS ARE EMPTY ON PURPOSE. This module grades the draw over the
    counts, and a placement list here would be fixture nobody reads.

    Args:
        counts: How many of each built class, keyed by bare class name.

    Returns:
        The placement model.
    """
    return placement.WorldPlacement(
        node_placements=(),
        node_counts=MappingProxyType({}),
        built_placements=(),
        built_counts=MappingProxyType(dict(counts)),
        bounds=None,
        coordinate_units=placement.COORDINATE_UNITS,
        node_semantics_available=False,
        node_orientation_available=True,
        warnings=(),
    )


def modeled_counts() -> Mapping[str, int]:
    """The built counts of the two modeled classes.

    Returns:
        The mapping.
    """
    return {FIXED_WHOLE: WHOLE_BUILT, FIXED_THIRD: THIRD_BUILT}


def whole_world_counts() -> Mapping[str, int]:
    """The built counts of every class in the partition fixture.

    Returns:
        The mapping.
    """
    return {
        FIXED_WHOLE: WHOLE_BUILT,
        FIXED_THIRD: THIRD_BUILT,
        DECLARED_VARIABLE: VARIABLE_BUILT,
        DECLARED_RANGE: RANGE_BUILT,
        DECLARED_NOTHING: SILENT_BUILT,
        NOT_IN_REGISTRY: STRANGER_BUILT,
    }


def machine(producing: bool | None, recipe: str | None) -> machines.MachineState:
    """Build one machine state.

    THE CLASS AND THE OVERCLOCK ARE FIXED FOR EVERY ENTRY, so no arm below can
    be decided by a field it does not name.

    Args:
        producing: The three-state producing flag.
        recipe: The recipe class name, or None for a machine with no recipe.

    Returns:
        The state.
    """
    return machines.MachineState(
        class_name=MACHINE_CLASS,
        producing=producing,
        recipe_class_name=recipe,
        overclock=Fraction(1),
    )


def world_machines(*states: machines.MachineState) -> machines.WorldMachines:
    """Build a machines model over the supplied states.

    Args:
        states: One state per machine, in population order.

    Returns:
        The model.
    """
    return machines.WorldMachines(
        machines=states,
        producing_available=any(state.producing is not None for state in states),
        recipe_available=any(state.recipe_class_name is not None for state in states),
        overclock_available=any(state.overclock is not None for state in states),
        records_considered=len(states),
        unread_payload_count=0,
        refused_overclock_count=0,
        refused_recipe_count=0,
        warnings=(),
    )


def world_network(*, belts: bool = False) -> network.WorldNetwork:
    """Build a network model declaring whether belt topology is available.

    Args:
        belts: What to declare for ``belt_topology_available``.

    Returns:
        The model.
    """
    return network.WorldNetwork(
        nodes=(),
        nodes_considered=0,
        records_considered=0,
        unread_payload_count=0,
        reference_tags_considered=0,
        instance_references_considered=0,
        belt_topology_available=belts,
        circuit_topology_available=False,
        warnings=(),
    )


def header() -> SaveHeader:
    """Build a synthetic header carrying no operator-authored string at all.

    Returns:
        The header.
    """
    return SaveHeader(
        header_version=14,
        save_version=52,
        build_changelist=0,
        map_name="SyntheticMap",
        world_token=SYNTHETIC_TOKEN,
        play_duration=0,
        datetime_ticks=0,
        byte_after_datetime_ticks=0,
        editor_object_version=0,
        is_modded=0,
        body_offset=0,
        warnings=(),
    )


def record(class_name: str, index: int) -> objects.ObjectRecord:
    """Build one synthetic built record of a given class.

    Args:
        class_name: The bare actor class the type path ends in.
        index: What to suffix the invented instance path with.

    Returns:
        The record.
    """
    instance = f"{MACHINE_INSTANCE}{index}"
    return objects.ObjectRecord(
        kind=objects.KIND_ACTOR,
        type_path=f"/Game/FactoryGame/Buildable/{class_name}.{class_name}",
        root_object=instance,
        instance_name=instance,
        transform=objects.Transform(
            rotation=(0.0, 0.0, 0.0, 1.0),
            translation=(float(index), 0.0, 0.0),
            scale=(1.0, 1.0, 1.0),
        ),
        parent=None,
        object_type=1,
        was_placed_in_level=0,
        body_offset=0,
        body_length=0,
    )


def world_of(*class_names: str) -> WorldModel:
    """Build a world model of one built record per supplied class name.

    Args:
        class_names: The class of each record, in file order.

    Returns:
        The model.
    """
    entries = {
        index: RecordProperties(
            values=MappingProxyType({}),
            schema_name="SyntheticSchema",
            resolved=None,
            payload_read=True,
            warning_codes=(),
            references=(),
        )
        for index in range(len(class_names))
    }
    return WorldModel(
        token=SYNTHETIC_TOKEN,
        header=header(),
        objects=objects.ObjectTable(
            records=tuple(
                record(class_name, index) for index, class_name in enumerate(class_names)
            ),
            unknown_classes=(),
            warnings=(),
            declared_body_length=0,
            body_consumed=0,
            body_prefix_width=8,
            transform_delta=0,
            save_version=52,
            header_version=14,
            level_count=1,
        ),
        unlocks=EMPTY_UNLOCK_STATE,
        nodes=(),
        warnings=(),
        properties=WorldProperties(by_record_index=MappingProxyType(entries)),
    )


def reachable(value: object, seen: set[int] | None = None) -> list[object]:
    """Every value reachable from one object, the object itself included.

    STRUCTURAL on purpose - see the same helper in ``test_machines.py``.

    Args:
        value: The root.
        seen: Identities already walked, to survive a cycle.

    Returns:
        Every reachable value.
    """
    seen = set() if seen is None else seen
    if id(value) in seen:
        return []
    seen.add(id(value))
    found: list[object] = [value]
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            found.extend(reachable(getattr(value, field.name), seen))
        return found
    if isinstance(value, (str, bytes, bytearray)):
        return found
    if isinstance(value, Mapping):
        for key, item in value.items():
            found.extend(reachable(key, seen))
            found.extend(reachable(item, seen))
        return found
    if isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            found.extend(reachable(item, seen))
    return found


# ---------------------------------------------------------------------------
# ARM ONE, first half: the world draw is the exact Fraction sum over built counts
# ---------------------------------------------------------------------------


def test_the_world_draw_is_the_exact_fraction_sum_over_built_counts() -> None:
    result = balance.draw_of(built(modeled_counts()), modeled_registry())

    assert result.consumption_megawatts == EXPECTED_CONSUMPTION
    assert type(result.consumption_megawatts) is Fraction


def test_the_sum_is_not_reachable_by_binary_floating_point() -> None:
    """The fixture's own control: the float sum and the exact sum disagree."""
    float_sum = float(WHOLE_MEGAWATTS) * WHOLE_BUILT + float(THIRD_MEGAWATTS) * THIRD_BUILT

    assert Fraction(float_sum) != EXPECTED_CONSUMPTION


def test_each_contributor_carries_its_own_count_and_its_own_product() -> None:
    result = balance.draw_of(built(modeled_counts()), modeled_registry())

    products = {
        item.class_name: (item.built_count, item.megawatts_each, item.megawatts_total)
        for item in result.contributions
    }
    assert products == {
        FIXED_WHOLE: (WHOLE_BUILT, WHOLE_MEGAWATTS, WHOLE_MEGAWATTS * WHOLE_BUILT),
        FIXED_THIRD: (THIRD_BUILT, THIRD_MEGAWATTS, THIRD_MEGAWATTS * THIRD_BUILT),
    }


def test_no_float_reaches_any_draw_output_field() -> None:
    entries = registry(building(DECLARED_INEXACT, consumption=0.1))
    counts = built({DECLARED_INEXACT: WHOLE_BUILT})

    control = [value for value in reachable(entries) if type(value) is float]
    assert control, "the walk cannot see a float in the INPUT, so its absence proves nothing"

    exact.audit_exact(balance.draw_of(counts, entries), path="draw")


def test_an_inexact_declared_draw_is_a_named_gap_and_never_a_summand() -> None:
    entries = registry(building(DECLARED_INEXACT, consumption=0.1))
    result = balance.draw_of(built({DECLARED_INEXACT: WHOLE_BUILT}), entries)

    assert result.consumption_megawatts == Fraction(0)
    assert [item.kind for item in result.gaps] == [balance.GAP_DRAW_INEXACT]


def test_a_world_with_nothing_built_says_so_rather_than_reporting_a_measured_zero() -> None:
    result = balance.draw_of(built({}), modeled_registry())

    assert result.consumption_megawatts == Fraction(0)
    assert balance.WARN_BALANCE_NOTHING_BUILT in {warning.code for warning in result.warnings}


def test_two_runs_over_one_input_return_equal_models() -> None:
    counts = built(whole_world_counts())
    entries = whole_world_registry()

    assert balance.draw_of(counts, entries) == balance.draw_of(counts, entries)


def test_the_draw_follows_through_the_real_placement_filter() -> None:
    """The one arm that does not write its own built_counts mapping."""
    entries = registry(building(ALLOWLISTED_CLASS, consumption=WHOLE_MEGAWATTS))
    counted = placement.placement_of(world_of(ALLOWLISTED_CLASS, ALLOWLISTED_CLASS))

    result = balance.draw_of(counted, entries)

    assert result.consumption_megawatts == WHOLE_MEGAWATTS * DISCRIMINATOR_MACHINE_COUNT


# ---------------------------------------------------------------------------
# ARM ONE, second half: an unmodeled draw is a NAMED GAP and never a zero
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("class_name", "expected_kind"),
    [
        (DECLARED_VARIABLE, power.SHAPE_VARIABLE),
        (DECLARED_RANGE, power.SHAPE_RANGE_ONLY),
        (DECLARED_NOTHING, power.SHAPE_UNDECLARED),
        (NOT_IN_REGISTRY, balance.GAP_NO_REGISTRY_ENTRY),
    ],
)
def test_each_unmodeled_shape_contributes_its_own_named_gap(
    class_name: str, expected_kind: str
) -> None:
    """One gap class beside one modeled class, so only the clause under test decides.

    A world holding all four at once would let a single wrong branch satisfy
    every row - see the module docstring on the masked clause.
    """
    counts = built({FIXED_WHOLE: WHOLE_BUILT, class_name: VARIABLE_BUILT})

    result = balance.draw_of(counts, whole_world_registry())

    assert [(item.class_name, item.kind) for item in result.gaps] == [(class_name, expected_kind)]
    assert result.consumption_megawatts == WHOLE_MEGAWATTS * WHOLE_BUILT


def test_an_unmodeled_class_never_appears_among_the_contributors() -> None:
    result = balance.draw_of(built(whole_world_counts()), whole_world_registry())

    contributing = {item.class_name for item in result.contributions}
    assert contributing == {FIXED_WHOLE, FIXED_THIRD}


def test_a_gap_has_no_megawatts_field_to_read_a_zero_out_of() -> None:
    """Structural, not by value: a re-added field defaulting to zero reddens here."""
    declared = {field.name for field in fields(balance.DrawGap)}

    assert not [name for name in declared if "megawatt" in name or "power" in name]


def test_the_two_buckets_partition_the_built_classes_with_conservation() -> None:
    counts = whole_world_counts()
    result = balance.draw_of(built(counts), whole_world_registry())

    contributing = {item.class_name for item in result.contributions}
    gapped = {item.class_name for item in result.gaps}
    assert not contributing & gapped
    assert contributing | gapped == set(counts)
    assert len(result.contributions) + len(result.gaps) == len(counts)


def test_the_unmodeled_counts_are_classes_and_contributors_apart() -> None:
    result = balance.draw_of(built(whole_world_counts()), whole_world_registry())

    assert result.unmodeled_class_count == EXPECTED_GAP_CLASSES
    assert result.unmodeled_contributor_count == EXPECTED_GAP_CONTRIBUTORS
    assert result.classes_considered == EXPECTED_CLASSES_CONSIDERED


def test_every_gap_carries_its_own_built_count_and_a_reason() -> None:
    result = balance.draw_of(built(whole_world_counts()), whole_world_registry())

    counted = {item.class_name: item.built_count for item in result.gaps}
    assert counted == {
        DECLARED_VARIABLE: VARIABLE_BUILT,
        DECLARED_RANGE: RANGE_BUILT,
        DECLARED_NOTHING: SILENT_BUILT,
        NOT_IN_REGISTRY: STRANGER_BUILT,
    }
    assert all(item.reason for item in result.gaps)


def test_every_published_gap_kind_is_on_the_closed_vocabulary() -> None:
    result = balance.draw_of(built(whole_world_counts()), whole_world_registry())

    assert {item.kind for item in result.gaps} <= balance.GAP_KINDS


def test_a_total_with_a_gap_behind_it_is_declared_incomplete() -> None:
    gapped = balance.draw_of(built(whole_world_counts()), whole_world_registry())
    clean = balance.draw_of(built(modeled_counts()), modeled_registry())

    assert gapped.consumption_complete is False
    assert clean.consumption_complete is True


def test_an_unmodeled_draw_raises_the_warning_that_names_how_many() -> None:
    result = balance.draw_of(built(whole_world_counts()), whole_world_registry())

    raised = {warning.code: warning for warning in result.warnings}
    assert balance.WARN_BALANCE_DRAW_UNMODELED in raised
    assert raised[balance.WARN_BALANCE_DRAW_UNMODELED].count == EXPECTED_GAP_CONTRIBUTORS


# ---------------------------------------------------------------------------
# ARM TWO: the flagged set is exactly the starved machine
# ---------------------------------------------------------------------------


def category_machines() -> machines.WorldMachines:
    """One machine per category, with the starved one at :data:`STARVED_SLOT`.

    Returns:
        The model.
    """
    return world_machines(
        machine(True, RECIPE_CLASS),
        machine(False, RECIPE_CLASS),
        machine(False, None),
        machine(None, RECIPE_CLASS),
    )


def test_the_flagged_set_is_exactly_the_starved_machine() -> None:
    result = balance.starvation_of(category_machines())

    assert result.starved_indices == (STARVED_SLOT,)


def test_the_flagged_set_reddens_when_the_producing_flag_is_ignored() -> None:
    """Two machines alike in every field but ``producing``.

    NOTHING ELSE CAN DECIDE THIS ONE. An implementation that ignores the flag
    returns the empty set or both slots, and neither is the one-element set.
    """
    result = balance.starvation_of(
        world_machines(machine(True, RECIPE_CLASS), machine(False, RECIPE_CLASS))
    )

    assert result.starved_indices == (STARVED_SLOT,)
    assert result.machines_considered == DISCRIMINATOR_MACHINE_COUNT


def test_a_machine_with_no_recipe_is_unconfigured_rather_than_starved() -> None:
    result = balance.starvation_of(
        world_machines(machine(False, None), machine(False, RECIPE_CLASS))
    )

    assert result.starved_indices == (STARVED_SLOT,)
    assert result.unconfigured_count == 1


def test_an_unread_producing_flag_is_counted_and_never_flagged_as_starved() -> None:
    result = balance.starvation_of(category_machines())

    assert result.unknown_state_count == 1
    assert result.starved_indices == (STARVED_SLOT,)


def test_the_four_categories_partition_the_machines_with_conservation() -> None:
    result = balance.starvation_of(category_machines())

    total = (
        len(result.starved_indices)
        + result.running_count
        + result.unconfigured_count
        + result.unknown_state_count
    )
    assert total == result.machines_considered
    assert result.machines_considered == CATEGORY_MACHINE_COUNT


def test_a_world_whose_producing_flag_never_read_says_so_rather_than_flagging_none() -> None:
    result = balance.starvation_of(
        world_machines(*(machine(None, RECIPE_CLASS) for _ in range(UNKNOWN_MACHINE_COUNT)))
    )

    assert result.starved_indices == ()
    assert result.producing_available is False
    assert balance.WARN_BALANCE_PRODUCING_UNAVAILABLE in {
        warning.code for warning in result.warnings
    }


def test_a_flagged_index_addresses_the_published_population_and_nothing_else() -> None:
    model = category_machines()
    result = balance.starvation_of(model)

    flagged = [model.machines[index] for index in result.starved_indices]
    assert [state.producing for state in flagged] == [False]


def test_no_record_instance_name_reaches_the_starvation_model() -> None:
    model = machines.machines_of(
        WorldModel(
            token=SYNTHETIC_TOKEN,
            header=header(),
            objects=objects.ObjectTable(
                records=(record(MACHINE_CLASS, 0),),
                unknown_classes=(),
                warnings=(),
                declared_body_length=0,
                body_consumed=0,
                body_prefix_width=8,
                transform_delta=0,
                save_version=52,
                header_version=14,
                level_count=1,
            ),
            unlocks=EMPTY_UNLOCK_STATE,
            nodes=(),
            warnings=(),
            properties=WorldProperties(
                by_record_index=MappingProxyType(
                    {
                        0: RecordProperties(
                            values=MappingProxyType({machines.PROPERTY_PRODUCING: False}),
                            schema_name="SyntheticSchema",
                            resolved=None,
                            payload_read=True,
                            warning_codes=(),
                            references=(
                                objects.ObjectReference(
                                    property_name=machines.PROPERTY_RECIPE,
                                    level_reference="",
                                    object_path=RECIPE_ASSET,
                                ),
                            ),
                        )
                    }
                )
            ),
        )
    )
    result = balance.starvation_of(model)

    assert result.starved_indices == (0,)
    leaked = [
        value for value in reachable(result) if isinstance(value, str) and MACHINE_INSTANCE in value
    ]
    assert not leaked


# ---------------------------------------------------------------------------
# The composite, and what it declares absent rather than reporting as zero
# ---------------------------------------------------------------------------


def test_the_composite_carries_both_halves_and_every_sub_warning() -> None:
    result = balance.balance_of(
        built(whole_world_counts()),
        whole_world_registry(),
        category_machines(),
        world_network(),
    )

    assert result.draw.consumption_megawatts == EXPECTED_CONSUMPTION
    assert result.starvation.starved_indices == (STARVED_SLOT,)
    codes = {warning.code for warning in result.warnings}
    assert balance.WARN_BALANCE_DRAW_UNMODELED in codes


def test_production_is_declared_unavailable_rather_than_reported_as_zero() -> None:
    result = balance.balance_of(
        built(modeled_counts()), modeled_registry(), category_machines(), world_network()
    )

    assert result.production_available is False
    assert balance.WARN_BALANCE_PRODUCTION_UNMODELED in {
        warning.code for warning in result.warnings
    }


def test_the_connected_edge_flag_is_derived_and_not_asserted() -> None:
    """It follows the network model, so it stops being false the day belts land."""
    without = balance.balance_of(
        built(modeled_counts()), modeled_registry(), category_machines(), world_network()
    )
    with_belts = balance.balance_of(
        built(modeled_counts()),
        modeled_registry(),
        category_machines(),
        world_network(belts=True),
    )

    assert without.connected_edges_available is False
    assert with_belts.connected_edges_available is True


def test_a_starved_finding_with_no_upstream_cause_says_it_is_half_an_audit() -> None:
    result = balance.balance_of(
        built(modeled_counts()), modeled_registry(), category_machines(), world_network()
    )

    assert balance.WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE in {
        warning.code for warning in result.warnings
    }


def test_an_unread_machine_state_raises_the_warning_that_names_how_many() -> None:
    result = balance.starvation_of(category_machines())

    raised = {warning.code: warning for warning in result.warnings}
    assert balance.WARN_BALANCE_MACHINE_STATE_UNREAD in raised
    assert raised[balance.WARN_BALANCE_MACHINE_STATE_UNREAD].count == 1


def test_no_balance_type_annotates_a_carrier_field() -> None:
    for declared in (
        balance.DrawContribution,
        balance.DrawGap,
        balance.WorldDraw,
        balance.WorldStarvation,
        balance.WorldBalance,
    ):
        for field in fields(declared):
            assert "bytes" not in str(field.type)
            assert "Path" not in str(field.type)


# ---------------------------------------------------------------------------
# CS-1263: the clocked draw reads each machine's clock
# ---------------------------------------------------------------------------
#
# THE SHIPPED EXPONENT IS NOT WHOLE, so the power law has no exact rational value
# away from the reference clock and the answer there is a NAMED BOUND. A whole
# exponent and the reference clock are the two places it does have one, and the
# arms below grade both sides of that line separately, because an implementation
# that bounds everything passes a bound-only arm and one that evaluates
# everything exactly passes an exact-only arm.

#: The shipped-shaped exponent, between one and two like the corpus's own.
BRACKETED_EXPONENT = Fraction(1321929, 1000000)

#: An underclock and an overclock, plus one no binary float holds.
HALF_CLOCK = Fraction(1, 2)
DOUBLE_CLOCK = Fraction(2)
THIRD_CLOCK = Fraction(1, 3)

#: How many machines the bracket arm builds per group.
BRACKET_MACHINES = 2


def clocked(class_name: str, clock: Fraction | float | None) -> machines.MachineState:
    """Build one producing machine of a given class at a given clock.

    Args:
        class_name: The built class.
        clock: The overclock as a potential, or None for a clock never read.

    Returns:
        The state.
    """
    return machines.MachineState(
        class_name=class_name,
        producing=True,
        recipe_class_name=RECIPE_CLASS,
        overclock=clock,  # type: ignore[arg-type]
    )


def bracketed_registry() -> Mapping[str, Building]:
    """One entry whose exponent is not whole, beside one whose exponent is.

    Returns:
        The mapping.
    """
    return registry(
        building(FIXED_WHOLE, consumption=WHOLE_MEGAWATTS),
        building(FIXED_THIRD, consumption=THIRD_MEGAWATTS, exponent=BRACKETED_EXPONENT),
    )


def test_an_unread_clock_is_a_named_gap_never_one() -> None:
    """A None clock beside a read one, alike in every other field.

    TREATING NONE AS ONE prices both machines at the reference draw and puts no
    gap in the answer, so this arm reddens on exactly that defect: the total is
    one machine's draw and not two, and the second machine is a named gap.
    """
    result = balance.clocked_draw_of(
        world_machines(clocked(FIXED_WHOLE, None), clocked(FIXED_WHOLE, Fraction(1))),
        modeled_registry(),
    )

    assert [(gap.class_name, gap.kind, gap.machine_count) for gap in result.gaps] == [
        (FIXED_WHOLE, balance.GAP_CLOCK_UNREAD, 1)
    ]
    assert result.lower_megawatts == WHOLE_MEGAWATTS
    assert result.upper_megawatts == WHOLE_MEGAWATTS
    assert result.unread_clock_count == 1
    assert result.complete is False
    raised = {warning.code: warning.count for warning in result.warnings}
    assert raised.get(balance.WARN_BALANCE_CLOCK_UNREAD) == 1


def test_a_clocked_gap_has_no_megawatts_field_to_read_a_one_out_of() -> None:
    declared = {field.name for field in fields(balance.ClockedGap)}

    assert not [name for name in declared if "megawatt" in name or "power" in name]


def test_the_reference_clock_is_exact_under_any_exponent() -> None:
    result = balance.clocked_draw_of(
        world_machines(clocked(FIXED_THIRD, Fraction(1)), clocked(FIXED_THIRD, Fraction(1))),
        bracketed_registry(),
    )

    (group,) = result.contributions
    assert group.bound == balance.BOUND_EXACT
    assert group.lower_total == group.upper_total == THIRD_MEGAWATTS * BRACKET_MACHINES
    assert result.exact is True


def test_a_whole_exponent_away_from_the_reference_clock_is_exact() -> None:
    result = balance.clocked_draw_of(
        world_machines(clocked(FIXED_WHOLE, HALF_CLOCK)), modeled_registry()
    )

    (group,) = result.contributions
    assert group.bound == balance.BOUND_EXACT
    assert group.lower_each == group.upper_each == WHOLE_MEGAWATTS * HALF_CLOCK
    assert result.exact is True


@pytest.mark.parametrize(
    ("clock", "lower_factor", "upper_factor"),
    [
        (HALF_CLOCK, HALF_CLOCK * HALF_CLOCK, HALF_CLOCK),
        (THIRD_CLOCK, THIRD_CLOCK * THIRD_CLOCK, THIRD_CLOCK),
        (DOUBLE_CLOCK, DOUBLE_CLOCK, DOUBLE_CLOCK * DOUBLE_CLOCK),
    ],
    ids=["underclock-half", "underclock-third", "overclock-double"],
)
def test_a_fractional_exponent_is_a_named_bound_bracketing_the_law(
    clock: Fraction, lower_factor: Fraction, upper_factor: Fraction
) -> None:
    """Below the reference the square is the floor; above it the order flips."""
    result = balance.clocked_draw_of(
        world_machines(*(clocked(FIXED_THIRD, clock) for _ in range(BRACKET_MACHINES))),
        bracketed_registry(),
    )

    (group,) = result.contributions
    assert group.bound == balance.BOUND_EXPONENT_BRACKET
    assert group.reason
    assert group.clock == clock
    assert group.machine_count == BRACKET_MACHINES
    assert group.lower_each == THIRD_MEGAWATTS * lower_factor
    assert group.upper_each == THIRD_MEGAWATTS * upper_factor
    assert group.lower_total == group.lower_each * BRACKET_MACHINES
    assert group.upper_total == group.upper_each * BRACKET_MACHINES
    assert result.exact is False
    assert result.complete is True
    raised = {warning.code: warning.count for warning in result.warnings}
    assert raised.get(balance.WARN_BALANCE_CLOCKED_DRAW_BOUNDED) == BRACKET_MACHINES


def test_the_bracket_contains_the_physical_draw() -> None:
    """The control that the bound is a bound: a float evaluation lands inside it.

    The float is the TEST's oracle and never the module's - it is read here
    only to show the two exact ends straddle the irrational value.
    """
    result = balance.clocked_draw_of(
        world_machines(clocked(FIXED_THIRD, HALF_CLOCK)), bracketed_registry()
    )
    (group,) = result.contributions
    physical = float(THIRD_MEGAWATTS) * float(HALF_CLOCK) ** float(BRACKETED_EXPONENT)
    low = float(group.lower_each)
    high = float(group.upper_each)

    assert low < physical < high


def test_a_zero_clock_is_exact_zero_under_a_positive_exponent() -> None:
    result = balance.clocked_draw_of(
        world_machines(clocked(FIXED_THIRD, Fraction(0))), bracketed_registry()
    )

    (group,) = result.contributions
    assert group.bound == balance.BOUND_EXACT
    assert group.upper_total == Fraction(0)


@pytest.mark.parametrize(
    ("entries", "clock", "expected_kind"),
    [
        (
            registry(building(FIXED_WHOLE, consumption=WHOLE_MEGAWATTS, exponent=None)),
            HALF_CLOCK,
            power.OUTCOME_NOT_SCALABLE,
        ),
        (modeled_registry(), Fraction(-1), power.OUTCOME_UNDEFINED),
        (modeled_registry(), 0.5, balance.GAP_LAW_INEXACT),
        (
            registry(building(FIXED_WHOLE, consumption=WHOLE_MEGAWATTS, exponent=1.5)),
            HALF_CLOCK,
            balance.GAP_LAW_INEXACT,
        ),
        (registry(), HALF_CLOCK, balance.GAP_NO_REGISTRY_ENTRY),
        (
            registry(building(FIXED_WHOLE, consumption=0.1)),
            HALF_CLOCK,
            balance.GAP_DRAW_INEXACT,
        ),
        (registry(building(FIXED_WHOLE)), HALF_CLOCK, power.SHAPE_UNDECLARED),
    ],
    ids=[
        "not-scalable",
        "negative-clock",
        "float-clock",
        "float-exponent",
        "no-entry",
        "inexact-draw",
        "undeclared",
    ],
)
def test_each_clocked_gap_kind_is_named_and_never_a_summand(
    entries: Mapping[str, Building], clock: Fraction | float, expected_kind: str
) -> None:
    result = balance.clocked_draw_of(world_machines(clocked(FIXED_WHOLE, clock)), entries)

    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [(expected_kind, 1)]
    assert all(gap.reason for gap in result.gaps)
    assert {gap.kind for gap in result.gaps} <= balance.CLOCKED_GAP_KINDS
    assert result.contributions == ()
    assert result.upper_megawatts == Fraction(0)
    exact.audit_exact(result, path="clocked")


def test_a_not_scalable_entry_is_still_exact_at_the_reference_clock() -> None:
    entries = registry(building(FIXED_WHOLE, consumption=WHOLE_MEGAWATTS, exponent=None))
    result = balance.clocked_draw_of(world_machines(clocked(FIXED_WHOLE, Fraction(1))), entries)

    assert result.gaps == ()
    assert result.upper_megawatts == WHOLE_MEGAWATTS


def test_the_clocked_buckets_partition_the_machines_with_conservation() -> None:
    population = world_machines(
        clocked(FIXED_WHOLE, Fraction(1)),
        clocked(FIXED_WHOLE, HALF_CLOCK),
        clocked(FIXED_WHOLE, HALF_CLOCK),
        clocked(FIXED_THIRD, HALF_CLOCK),
        clocked(FIXED_THIRD, None),
        clocked(NOT_IN_REGISTRY, Fraction(1)),
    )
    result = balance.clocked_draw_of(population, bracketed_registry())

    placed = sum(group.machine_count for group in result.contributions)
    gapped = sum(gap.machine_count for gap in result.gaps)
    assert placed + gapped == result.machines_considered == len(population.machines)
    assert result.unmodeled_machine_count + result.unread_clock_count == gapped
    assert result.lower_megawatts < result.upper_megawatts
    exact.audit_exact(result, path="clocked")


def test_two_clocked_runs_over_one_input_return_equal_models() -> None:
    population = world_machines(clocked(FIXED_THIRD, HALF_CLOCK), clocked(FIXED_WHOLE, None))
    first = balance.clocked_draw_of(population, bracketed_registry())
    second = balance.clocked_draw_of(population, bracketed_registry())

    assert first == second


def test_a_world_with_no_machines_says_so_rather_than_a_measured_zero() -> None:
    result = balance.clocked_draw_of(world_machines(), modeled_registry())

    assert result.upper_megawatts == Fraction(0)
    assert balance.WARN_BALANCE_NO_MACHINES_CLOCKED in {warning.code for warning in result.warnings}


def test_the_clocked_repr_names_no_built_class() -> None:
    result = balance.clocked_draw_of(
        world_machines(clocked(FIXED_THIRD, HALF_CLOCK), clocked(FIXED_WHOLE, None)),
        bracketed_registry(),
    )
    rendered = " ".join(repr(value) for value in (result, *result.contributions, *result.gaps))
    named = [name for name in (FIXED_THIRD, FIXED_WHOLE) if name in rendered]

    assert not named


def test_the_composite_carries_the_clocked_draw_and_its_warnings() -> None:
    population = world_machines(clocked(FIXED_THIRD, HALF_CLOCK), clocked(FIXED_WHOLE, None))
    result = balance.balance_of(
        built(modeled_counts()), bracketed_registry(), population, world_network()
    )
    alone = balance.clocked_draw_of(population, bracketed_registry())

    assert result.clocked_draw == alone
    codes = {warning.code for warning in result.warnings}
    assert balance.WARN_BALANCE_CLOCK_UNREAD in codes
    assert balance.WARN_BALANCE_CLOCKED_DRAW_BOUNDED in codes


# ---------------------------------------------------------------------------
# CS-1263: an ELIDED clock is the measured default, an UNREADABLE one a gap
# ---------------------------------------------------------------------------


def elided(class_name: str) -> machines.MachineState:
    """Build one producing machine whose clock tag the serializer elided.

    Args:
        class_name: The built class.

    Returns:
        The state, overclock None with the elision flag set.
    """
    return machines.MachineState(
        class_name=class_name,
        producing=True,
        recipe_class_name=RECIPE_CLASS,
        overclock=None,
        overclock_elided=True,
    )


def test_an_elided_clock_is_priced_exactly_at_the_default_and_counted() -> None:
    """Alike in every field but the flag, so only the flag decides.

    The elided machine prices at the declared draw; the unread one beside it
    stays a named gap, which is what keeps the default from becoming a guess.
    """
    result = balance.clocked_draw_of(
        world_machines(elided(FIXED_THIRD), clocked(FIXED_THIRD, None)), bracketed_registry()
    )

    (group,) = result.contributions
    assert group.bound == balance.BOUND_EXACT
    assert group.clock == balance.ELIDED_CLOCK_DEFAULT
    assert group.clock_elided is True
    assert group.upper_total == group.lower_total == THIRD_MEGAWATTS
    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [(balance.GAP_CLOCK_UNREAD, 1)]
    assert result.elided_clock_count == 1
    raised = {warning.code: warning.count for warning in result.warnings}
    assert raised.get(balance.WARN_BALANCE_CLOCK_ELIDED) == 1


def test_an_elided_group_never_merges_with_a_read_clock_of_one() -> None:
    result = balance.clocked_draw_of(
        world_machines(elided(FIXED_WHOLE), clocked(FIXED_WHOLE, Fraction(1))),
        modeled_registry(),
    )

    assert sorted((group.clock_elided, group.machine_count) for group in result.contributions) == [
        (False, 1),
        (True, 1),
    ]


def test_the_elided_default_is_the_reference_clock() -> None:
    assert balance.ELIDED_CLOCK_DEFAULT == power.REFERENCE_CLOCK


# ---------------------------------------------------------------------------
# CS-1263: the bracket reads the exponent's own floor and ceiling
# ---------------------------------------------------------------------------
#
# An exponent between one and two lets an implementation that hardcodes the two
# whole exponents to 1 and 2 pass every arm above. These sit elsewhere on the
# line, including below zero, so floor and ceiling are both exercised.


@pytest.mark.parametrize(
    ("exponent", "clock", "lower_factor", "upper_factor"),
    [
        (Fraction(5, 2), HALF_CLOCK, Fraction(1, 8), Fraction(1, 4)),
        (Fraction(5, 2), DOUBLE_CLOCK, Fraction(4), Fraction(8)),
        (Fraction(1, 2), HALF_CLOCK, Fraction(1, 2), Fraction(1)),
        (Fraction(1, 2), DOUBLE_CLOCK, Fraction(1), Fraction(2)),
        (Fraction(-3, 2), HALF_CLOCK, Fraction(2), Fraction(4)),
        (Fraction(-3, 2), DOUBLE_CLOCK, Fraction(1, 4), Fraction(1, 2)),
    ],
    ids=[
        "five-halves-under",
        "five-halves-over",
        "one-half-under",
        "one-half-over",
        "minus-three-halves-under",
        "minus-three-halves-over",
    ],
)
def test_the_bracket_uses_the_exponents_own_floor_and_ceiling(
    exponent: Fraction, clock: Fraction, lower_factor: Fraction, upper_factor: Fraction
) -> None:
    entries = registry(building(FIXED_THIRD, consumption=THIRD_MEGAWATTS, exponent=exponent))
    result = balance.clocked_draw_of(world_machines(clocked(FIXED_THIRD, clock)), entries)

    (group,) = result.contributions
    assert group.bound == balance.BOUND_EXPONENT_BRACKET
    assert group.lower_each == THIRD_MEGAWATTS * lower_factor
    assert group.upper_each == THIRD_MEGAWATTS * upper_factor
    physical = float(THIRD_MEGAWATTS) * float(clock) ** float(exponent)
    low = float(group.lower_each)
    high = float(group.upper_each)
    assert low < physical < high


def test_a_zero_clock_under_a_negative_exponent_is_a_named_gap() -> None:
    entries = registry(building(FIXED_THIRD, consumption=THIRD_MEGAWATTS, exponent=Fraction(-3, 2)))
    result = balance.clocked_draw_of(world_machines(clocked(FIXED_THIRD, Fraction(0))), entries)

    assert [gap.kind for gap in result.gaps] == [power.OUTCOME_UNDEFINED]
    assert result.contributions == ()


# ---------------------------------------------------------------------------
# CS-1264: a production-boost tag is a named gap, never priced as unboosted
# ---------------------------------------------------------------------------
#
# No save in the library carries a boost tag, so every arm here is synthetic.
# THE TEST OWNS THE SPELLING: the two tag names are written out below rather
# than read back off the module, so an implementation that drifts a spelling
# reddens here instead of agreeing with itself.

#: The live production boost and its pending sibling, as the game spells them.
BOOST_TAGS = ("mCurrentProductionBoost", "mPendingProductionBoost")


def test_the_boost_tag_vocabulary_is_the_two_seeded_names() -> None:
    assert frozenset(BOOST_TAGS) == machines.PRODUCTION_BOOST_PROPERTY_NAMES


@pytest.mark.parametrize("tag", BOOST_TAGS)
def test_a_boost_tag_on_the_payload_reaches_the_machine_state(tag: str) -> None:
    """The clock tag is absent, so the clock is elided AND the machine is boosted.

    The two flags are independent facts and both are published: the clock really
    is at the class default, and the boost is what makes that default the wrong
    price. Which one wins is the balance's decision, graded further down.
    """
    model = machines_fx.world(
        machines_fx.entry({machines.PROPERTY_PRODUCING: True, tag: machines_fx.as_float32("2")})
    )

    (state,) = machines.machines_of(model).machines
    assert state.production_boost_tagged is True
    assert state.overclock_elided is True


#: The level the decoder arms' one actor hangs from. Synthetic, no marker.
BOOST_LEVEL = "Persistent_Level:SyntheticBoostCellQx73_0"

#: A tag the decoder arms tear, so a payload carries a disagreement that is
#: NOT the boost tag. Invented.
TORN_NEIGHBOUR = "mSyntheticTornQx73"

#: The struct word an unmeasured boost tag is written under. Invented.
BOOST_STRUCT_WORD = "SyntheticBoostStructQx73"


def float_tag(name: str, value: float) -> bytes:
    """One FloatProperty tag whose four value bytes match its declared size.

    Args:
        name: The property name.
        value: The value, exactly representable in float32.

    Returns:
        The encoded tag.
    """
    return save_synthetic.property_tag(name, "FloatProperty", struct.pack("<f", value))


def torn_float_tag(name: str) -> bytes:
    """One FloatProperty tag declaring EIGHT value bytes, which the decoder refuses.

    Args:
        name: The property name.

    Returns:
        The encoded tag, counted as a disagreement and dropped from the values.
    """
    return save_synthetic.property_tag(name, "FloatProperty", struct.pack("<d", 2.0))


def producing_tag() -> bytes:
    """The producing flag, set, as a BoolProperty carries it in its tag data.

    Returns:
        The encoded tag.
    """
    return save_synthetic.property_tag(
        machines.PROPERTY_PRODUCING, "BoolProperty", b"", tag_extra=b"\x01"
    )


def decoded_world(*tags: bytes) -> WorldModel:
    """A whole synthetic save of one actor carrying these tags, through the REAL loader.

    THE DECODER DECIDES WHAT REACHES THE VALUES, not this fixture. A hand-built
    value map can hold shapes the decoder never produces for a dropped tag, and
    an arm over one grades nothing about the drop - which is how an earlier arm
    here planted an int and passed.

    Args:
        tags: The encoded tags, in file order.

    Returns:
        The world model ``load_world_from_bytes`` publishes.
    """
    return decoded_actors(tags)


def decoded_actors(*actors: tuple[bytes, ...]) -> WorldModel:
    """A whole synthetic save of one actor per tag tuple, through the REAL loader.

    Args:
        actors: One tuple of encoded tags per actor, in record order.

    Returns:
        The world model ``load_world_from_bytes`` publishes.
    """
    fixture = save_synthetic.SAVE_LEVELLED_DECODABLE
    head_bytes = save_synthetic.actor_payload_head(
        save_synthetic.MAP_NAME, save_synthetic.DECODABLE_ROOT, ()
    )
    body = save_synthetic.build_levelled_body(
        (
            save_synthetic.SyntheticLevel(
                name=BOOST_LEVEL,
                objects=tuple(
                    save_synthetic.SyntheticObject(
                        save_synthetic.DECODABLE_CLASS_PATH,
                        save_synthetic.DECODABLE_ROOT,
                        f"{save_synthetic.DECODABLE_INSTANCE}{position}",
                    )
                    for position in range(len(actors))
                ),
                payloads=tuple(
                    save_synthetic.tagged_property_payload(
                        tags, head=head_bytes, trailing=save_synthetic.DECODABLE_TRAILING_RUN
                    )
                    for tags in actors
                ),
            ),
        ),
        save_synthetic.SyntheticLevel(name=None),
        header_version=fixture.header_version,
        save_version=fixture.save_version,
        grids=save_synthetic.LEVELLED_GRIDS,
    )
    head = save_synthetic.build_header(
        header_version=fixture.header_version, save_version=fixture.save_version
    )
    prefixed = save_synthetic.body_with_prefix(body, fixture.header_version)
    framed = save_synthetic.build_chunks(
        prefixed, framing=save_synthetic.default_framing(fixture.header_version)
    )
    return world.load_world_from_bytes(head + framed)


def decoded_registry() -> Mapping[str, Building]:
    """The decoder arms' one class, modeled at :data:`WHOLE_MEGAWATTS`.

    Returns:
        The mapping.
    """
    return registry(
        building(
            objects.class_name_of(save_synthetic.DECODABLE_CLASS_PATH), consumption=WHOLE_MEGAWATTS
        )
    )


@pytest.mark.parametrize(
    ("boost_tag", "dropped_as"),
    [
        (torn_float_tag(BOOST_TAGS[0]), "disagreeing"),
        (
            save_synthetic.legacy_struct_tag(BOOST_TAGS[0], BOOST_STRUCT_WORD, bytes(8)),
            "unmeasured",
        ),
    ],
    ids=["torn-float", "struct-typed"],
)
def test_a_boost_tag_whose_value_never_decoded_still_marks_the_machine(
    boost_tag: bytes, dropped_as: str
) -> None:
    """Presence is the fact read, never the value - a boost the decoder dropped is a boost.

    THE PREMISE IS ASSERTED FIRST: the real decoder dropped the boost value and
    counted it, so the values carry no boost name at all. A read clock of one
    sits beside it, so ignoring the boost prices the machine at the reference
    draw and reports the draw complete.
    """
    model = decoded_world(float_tag(machines.PROPERTY_OVERCLOCK, 1.0), producing_tag(), boost_tag)
    (entry,) = model.properties.by_record_index.values()
    assert BOOST_TAGS[0] not in entry.values
    assert (entry.disagreeing_value_count, entry.unmeasured_value_count) == (
        (1, 0) if dropped_as == "disagreeing" else (0, 1)
    )

    population = machines.machines_of(model)
    assert [state.production_boost_tagged for state in population.machines] == [True]
    result = balance.clocked_draw_of(population, decoded_registry())
    assert result.upper_megawatts == Fraction(0)
    assert result.complete is False
    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [
        (balance.GAP_BOOST_UNMODELED, 1)
    ]


def test_a_boost_tag_beside_a_disagreeing_neighbour_still_marks_the_machine() -> None:
    """A payload carrying SOME disagreement is not a payload whose boost may be ignored.

    The boost itself decodes; a different tag is torn. A flag set only on a
    cleanly read payload would miss exactly this machine.
    """
    model = decoded_world(
        float_tag(machines.PROPERTY_OVERCLOCK, 1.0),
        producing_tag(),
        torn_float_tag(TORN_NEIGHBOUR),
        float_tag(BOOST_TAGS[0], 2.0),
    )
    (entry,) = model.properties.by_record_index.values()
    assert entry.disagreeing_value_count == 1
    assert BOOST_TAGS[0] in entry.values

    population = machines.machines_of(model)
    assert [state.production_boost_tagged for state in population.machines] == [True]
    result = balance.clocked_draw_of(population, decoded_registry())
    assert result.upper_megawatts == Fraction(0)
    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [
        (balance.GAP_BOOST_UNMODELED, 1)
    ]


def test_a_decodable_boost_of_exactly_one_still_marks_the_machine() -> None:
    """The VALUE is never read, so a boost of one is a boost tag like any other.

    One is the docs' own base boost, and reading it as "no boost" is a reading
    of a value whose saved encoding no save in the library has shown. The clock
    tag is absent, so the machine would otherwise land in the elided default.
    """
    model = decoded_world(producing_tag(), float_tag(BOOST_TAGS[0], 1.0))
    (entry,) = model.properties.by_record_index.values()
    assert entry.values[BOOST_TAGS[0]] == 1.0

    population = machines.machines_of(model)
    assert [state.production_boost_tagged for state in population.machines] == [True]
    result = balance.clocked_draw_of(population, decoded_registry())
    assert result.elided_clock_count == 0
    assert result.upper_megawatts == Fraction(0)
    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [
        (balance.GAP_BOOST_UNMODELED, 1)
    ]


def test_a_clock_tag_whose_value_never_decoded_is_not_an_elided_clock() -> None:
    """The sibling of the boost arms, one tag over: absent from the values is not absent.

    A clock tag of an unmeasured type is dropped and counted as unmeasured,
    which - unlike a disagreement - does not by itself distrust the payload. The
    tag WAS written, so the serializer did not elide it, and pricing the machine
    at the default would be the confident one CS-1263 refuses.
    """
    model = decoded_world(
        save_synthetic.legacy_struct_tag(machines.PROPERTY_OVERCLOCK, BOOST_STRUCT_WORD, bytes(8)),
        producing_tag(),
    )
    (entry,) = model.properties.by_record_index.values()
    assert machines.PROPERTY_OVERCLOCK not in entry.values
    assert (entry.disagreeing_value_count, entry.unmeasured_value_count) == (0, 1)

    population = machines.machines_of(model)
    assert [state.overclock_elided for state in population.machines] == [False]
    result = balance.clocked_draw_of(population, decoded_registry())
    assert result.elided_clock_count == 0
    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [(balance.GAP_CLOCK_UNREAD, 1)]


def torn_recipe_tag() -> bytes:
    """A recipe reference whose two strings do not account for its declared size.

    Returns:
        The encoded tag, counted as a disagreement and dropped from the values
        and from the reference population alike.
    """
    pair = save_synthetic.fstring(save_synthetic.MAP_NAME) + save_synthetic.fstring(RECIPE_ASSET)
    return save_synthetic.property_tag(machines.PROPERTY_RECIPE, "ObjectProperty", pair + b"\0")


@pytest.mark.parametrize(
    ("dropped", "expected_kind"),
    [
        (
            (torn_float_tag(machines.PROPERTY_OVERCLOCK), float_tag(BOOST_TAGS[0], 2.0)),
            balance.GAP_BOOST_UNMODELED,
        ),
        (
            (
                save_synthetic.legacy_struct_tag(
                    machines.PROPERTY_OVERCLOCK, BOOST_STRUCT_WORD, bytes(8)
                ),
                save_synthetic.legacy_struct_tag(BOOST_TAGS[0], BOOST_STRUCT_WORD, bytes(8)),
            ),
            balance.GAP_BOOST_UNMODELED,
        ),
        (
            (torn_float_tag(machines.PROPERTY_OVERCLOCK), torn_float_tag(BOOST_TAGS[0])),
            balance.GAP_BOOST_UNMODELED,
        ),
        ((torn_float_tag(machines.PROPERTY_OVERCLOCK),), balance.GAP_CLOCK_UNREAD),
        ((torn_recipe_tag(),), balance.GAP_CLOCK_UNREAD),
    ],
    ids=[
        "torn-clock-decoded-boost",
        "struct-clock-struct-boost",
        "torn-clock-torn-boost",
        "torn-clock-alone",
        "torn-recipe-alone",
    ],
)
def test_a_machine_whose_only_machine_tag_was_dropped_is_still_a_machine(
    dropped: tuple[bytes, ...], expected_kind: str
) -> None:
    """Membership is the third read of presence, and it reads the dropped names too.

    THE FIRST ACTOR'S EVERY MACHINE TAG WAS DROPPED by the real decoder; the
    second is an ordinary machine at the reference clock. Deciding membership off
    the decoded values alone publishes the second machine only, prices it, and
    calls the draw complete - with nothing anywhere naming the first.
    """
    model = decoded_actors(dropped, (float_tag(machines.PROPERTY_OVERCLOCK, 1.0), producing_tag()))
    assert [
        (entry.payload_read, bool(machines.MACHINE_PROPERTY_NAMES & set(entry.values)))
        for entry in model.properties.by_record_index.values()
    ] == [(True, False), (True, True)]

    population = machines.machines_of(model)
    assert len(population.machines) == len(model.properties.by_record_index)
    result = balance.clocked_draw_of(population, decoded_registry())
    assert result.complete is False
    assert result.upper_megawatts == WHOLE_MEGAWATTS
    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [(expected_kind, 1)]


def test_a_decoded_payload_with_no_boost_tag_is_priced() -> None:
    """The control for the three arms above: the same loader, no boost, a price."""
    model = decoded_world(float_tag(machines.PROPERTY_OVERCLOCK, 1.0), producing_tag())

    population = machines.machines_of(model)
    assert [state.production_boost_tagged for state in population.machines] == [False]
    result = balance.clocked_draw_of(population, decoded_registry())
    assert result.upper_megawatts == WHOLE_MEGAWATTS
    assert result.gaps == ()


def test_a_payload_with_no_boost_tag_is_not_marked_boosted() -> None:
    model = machines_fx.world(machines_fx.entry({machines.PROPERTY_PRODUCING: True}))

    (state,) = machines.machines_of(model).machines
    assert state.production_boost_tagged is False


def test_a_hand_built_state_never_claims_a_boost() -> None:
    assert clocked(FIXED_WHOLE, Fraction(1)).production_boost_tagged is False


def test_no_boost_value_reaches_the_machine_model_as_a_float() -> None:
    model = machines_fx.world(
        machines_fx.entry({machines.PROPERTY_PRODUCING: True, BOOST_TAGS[0]: 2.5})
    )
    result = machines.machines_of(model)

    control = [value for value in machines_fx.reachable(model) if type(value) is float]
    assert control, "the walk cannot see a float in the INPUT, so its absence proves nothing"
    assert not [value for value in machines_fx.reachable(result) if type(value) is float]


def boosted(
    class_name: str, clock: Fraction | None, *, clock_elided: bool = False
) -> machines.MachineState:
    """Build one producing machine carrying a production-boost tag.

    Args:
        class_name: The built class.
        clock: The overclock, or None for a clock tag that was absent.
        clock_elided: Whether that absent clock tag was elided.

    Returns:
        The state.
    """
    return machines.MachineState(
        class_name=class_name,
        producing=True,
        recipe_class_name=RECIPE_CLASS,
        overclock=clock,
        overclock_elided=clock_elided,
        production_boost_tagged=True,
    )


def test_a_boosted_machine_reddens_the_arm_when_the_boost_is_ignored() -> None:
    """Alike in every field but the boost tag, so only the boost decides.

    IGNORING THE BOOST prices both machines at the elided default: the upper end
    is two machines' declared draw and the elided count is two. The boosted one
    must instead be a named gap, leaving one machine priced and one counted.
    """
    result = balance.clocked_draw_of(
        world_machines(elided(FIXED_WHOLE), boosted(FIXED_WHOLE, None, clock_elided=True)),
        modeled_registry(),
    )

    assert result.upper_megawatts == WHOLE_MEGAWATTS
    assert result.lower_megawatts == WHOLE_MEGAWATTS
    assert result.elided_clock_count == 1
    assert [(gap.class_name, gap.kind, gap.machine_count) for gap in result.gaps] == [
        (FIXED_WHOLE, balance.GAP_BOOST_UNMODELED, 1)
    ]
    assert result.complete is False
    assert result.exact is False
    raised = {warning.code: warning.count for warning in result.warnings}
    assert raised.get(balance.WARN_BALANCE_CLOCK_ELIDED) == 1
    assert raised.get(balance.WARN_BALANCE_CLOCKED_DRAW_UNMODELED) == 1


@pytest.mark.parametrize(
    ("class_name", "clock"),
    [
        (FIXED_WHOLE, HALF_CLOCK),
        (FIXED_WHOLE, Fraction(1)),
        (FIXED_THIRD, HALF_CLOCK),
        (FIXED_THIRD, Fraction(1)),
    ],
    ids=[
        "whole-exponent-half",
        "whole-exponent-reference",
        "bracketed-half",
        "bracketed-reference",
    ],
)
def test_a_read_clock_never_prices_a_boosted_machine(class_name: str, clock: Fraction) -> None:
    """Every pricing path the clock law has - exact, reference and bracket - is refused.

    The reference clock is the masked case: the law returns early there before
    any exponent is asked for, so a boost check placed after that return would
    pass the half-clock rows and price this one.
    """
    result = balance.clocked_draw_of(
        world_machines(boosted(class_name, clock)), bracketed_registry()
    )

    assert result.contributions == ()
    assert result.upper_megawatts == Fraction(0)
    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [
        (balance.GAP_BOOST_UNMODELED, 1)
    ]
    assert result.bounded_machine_count == 0


@pytest.mark.parametrize(
    ("clock", "clock_elided"),
    [(None, False), (0.5, False)],
    ids=["unread-clock", "float-clock"],
)
def test_the_boost_is_named_before_the_clock_is_read(
    clock: Fraction | None, clock_elided: bool
) -> None:
    """No clock reading can price a boosted machine, so the boost is the gap it lands in.

    Each machine lands in exactly one bucket, so the unread-clock count does not
    also carry it.
    """
    result = balance.clocked_draw_of(
        world_machines(boosted(FIXED_WHOLE, clock, clock_elided=clock_elided)),
        modeled_registry(),
    )

    assert [gap.kind for gap in result.gaps] == [balance.GAP_BOOST_UNMODELED]
    assert result.unread_clock_count == 0
    assert result.unmodeled_machine_count == 1


def test_the_registry_side_is_named_before_the_boost() -> None:
    """The same order :func:`clockspeed.audit.balance.draw_of` decides in.

    With no entry there is nothing to ask.
    """
    result = balance.clocked_draw_of(
        world_machines(boosted(NOT_IN_REGISTRY, None, clock_elided=True)), modeled_registry()
    )

    assert [gap.kind for gap in result.gaps] == [balance.GAP_NO_REGISTRY_ENTRY]


def test_the_boost_gap_kind_is_clocked_only() -> None:
    assert balance.GAP_BOOST_UNMODELED in balance.CLOCKED_GAP_KINDS
    assert balance.GAP_BOOST_UNMODELED not in balance.GAP_KINDS


def test_boosted_machines_group_per_class_and_conserve() -> None:
    population = world_machines(
        boosted(FIXED_WHOLE, None, clock_elided=True),
        boosted(FIXED_WHOLE, HALF_CLOCK),
        boosted(FIXED_THIRD, Fraction(1)),
        elided(FIXED_WHOLE),
        clocked(FIXED_THIRD, HALF_CLOCK),
        clocked(FIXED_THIRD, None),
    )
    result = balance.clocked_draw_of(population, bracketed_registry())

    assert [(gap.class_name, gap.kind, gap.machine_count) for gap in result.gaps] == [
        (FIXED_THIRD, balance.GAP_BOOST_UNMODELED, 1),
        (FIXED_THIRD, balance.GAP_CLOCK_UNREAD, 1),
        (FIXED_WHOLE, balance.GAP_BOOST_UNMODELED, 2),
    ]
    placed = sum(group.machine_count for group in result.contributions)
    gapped = sum(gap.machine_count for gap in result.gaps)
    assert placed + gapped == result.machines_considered == len(population.machines)
    assert result.unmodeled_machine_count + result.unread_clock_count == gapped
    assert result.elided_clock_count == 1
    exact.audit_exact(result, path="clocked")


def test_a_boost_tag_on_a_real_payload_reaches_the_gap_and_not_the_elided_count() -> None:
    """End to end over the seam: a world model, the machines read, the clocked draw.

    The payload carries the boost tag and NO clock tag, so the machines layer
    marks the clock elided; the balance must still refuse it rather than count
    it at the default.
    """
    model = machines_fx.world(
        machines_fx.entry({machines.PROPERTY_PRODUCING: True, BOOST_TAGS[0]: 2.0}),
        machines_fx.entry({machines.PROPERTY_PRODUCING: True}),
    )
    entries = registry(building(machines_fx.MACHINE_CLASS, consumption=WHOLE_MEGAWATTS))
    result = balance.clocked_draw_of(machines.machines_of(model), entries)

    assert result.elided_clock_count == 1
    assert result.upper_megawatts == WHOLE_MEGAWATTS
    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [
        (balance.GAP_BOOST_UNMODELED, 1)
    ]


def test_the_composite_carries_a_boosted_machine_as_an_incomplete_draw() -> None:
    """The power rule reads ``complete``; a boosted machine must make it False."""
    population = world_machines(
        boosted(FIXED_WHOLE, Fraction(1)), clocked(FIXED_WHOLE, Fraction(1))
    )
    result = balance.balance_of(
        built(modeled_counts()), modeled_registry(), population, world_network()
    )

    assert result.clocked_draw.complete is False
    assert result.clocked_draw.upper_megawatts == WHOLE_MEGAWATTS
    assert balance.WARN_BALANCE_CLOCKED_DRAW_UNMODELED in {
        warning.code for warning in result.warnings
    }


def test_a_boosted_gap_repr_names_no_built_class() -> None:
    result = balance.clocked_draw_of(
        world_machines(boosted(FIXED_WHOLE, Fraction(1))), modeled_registry()
    )

    assert result.gaps
    assert FIXED_WHOLE not in " ".join(repr(gap) for gap in result.gaps)


# ---------------------------------------------------------------------------
# CS-1266: the considered population is cross-checked against what is built
# ---------------------------------------------------------------------------
#
# A built record of a power-consuming class that never entered the machines
# population - its payload never read, or it read and carried no clock, recipe
# or producing tag - contributed nothing to the clocked draw, and before this
# item nothing said so: the draw called itself complete over the population it
# was handed. Every arm here builds the world model and reads it through the
# REAL ``machines_of``, so the population and the census come from one walk.

#: The decoded values of a machine priced exactly: a clock of one, producing.
TAGGED: Mapping[str, object] = MappingProxyType(
    {machines.PROPERTY_OVERCLOCK: 1.0, machines.PROPERTY_PRODUCING: True}
)

#: An invented class whose entry declares a FIXED draw of exactly zero - the
#: shape every storage container and pipeline junction ships with.
ZERO_DRAW = "Build_SyntheticZeroDrawQx73_C"

#: An invented generator class. Its CONSUMER entry declares a positive draw on
#: purpose, so only the generator namespace can keep it out of the count.
GENERATOR_CLASS = "Build_SyntheticGeneratorQx73_C"

#: A declared size no synthetic payload is long enough to hold.
OVERRUN_SIZE = 1 << 20

#: How many consumer records the acceptance arm leaves out of the population.
ACCEPTANCE_OMITTED = 2

#: How many machines the like-for-like arm's population holds once its one
#: generator is set apart: a consumer, a fixed-zero machine and a stranger.
LIKE_FOR_LIKE_CONSIDERED = 3

#: The like-for-like arm's machines in no number: one stranger, two omissions.
LIKE_FOR_LIKE_UNPRICED = 3

#: The (header, save) version pair the save suite's mismatched body is written
#: in, read off that suite rather than restated.
MISMATCHED_PAIR = (objects_fx._HEADER_10, objects_fx._SAVE_36)  # noqa: SLF001

#: The record-count arm: two priced machines of one class, three untagged
#: records of another, so a count of classes and a count of records differ.
PRICED_MACHINES = 2
UNTAGGED_RECORDS = 3


def census_world(
    *rows: tuple[str, Mapping[str, object]], unread: tuple[str, ...] = ()
) -> WorldModel:
    """One built record per row on a read payload, then one unread record per class.

    EVERY ENTRY HAD A PAYLOAD - ``payload_present`` keeps its default - as every
    record a real levelled walk pairs does: a record the walk paired with no
    payload never had one read, whatever else its entry says, and is graded
    apart below.

    Args:
        rows: ``(class name, decoded values)`` per record, in file order.
        unread: The class of each trailing record whose payload never read.

    Returns:
        The model.
    """
    base = world_of(*(name for name, _ in rows), *unread)
    entries = dict(base.properties.by_record_index)
    for index, (_name, values) in enumerate(rows):
        entries[index] = replace(entries[index], values=MappingProxyType(dict(values)))
    for index in range(len(rows), len(rows) + len(unread)):
        entries[index] = replace(
            entries[index],
            payload_read=False,
            warning_codes=(objects.WARN_UNPARSED_PROPERTY_PAYLOAD,),
        )
    return replace(base, properties=WorldProperties(by_record_index=MappingProxyType(entries)))


def omitted_rows(result: balance.WorldClockedDraw) -> list[tuple[str, str, int]]:
    """Each named omission as ``(class, kind, count)``, in published order.

    Args:
        result: The clocked draw.

    Returns:
        The rows.
    """
    return [(item.class_name, item.kind, item.machine_count) for item in result.omissions]


def consumer_counts(result: balance.WorldClockedDraw) -> tuple[int, int, int]:
    """The three like-for-like counts, built then considered then omitted.

    Args:
        result: The clocked draw.

    Returns:
        The counts.
    """
    return (
        result.built_consumer_count,
        result.considered_consumer_count,
        result.omitted_consumer_count,
    )


def test_a_built_consumer_the_draw_never_considered_is_named() -> None:
    """CS-1266's acceptance arm: two built consumers carry no machine tag at all.

    ONE MACHINE IS PRICED AND TWO RECORDS OF CONSUMER CLASSES ARE NOT IN THE
    POPULATION. Without the cross-check the draw prices the one, carries no gap
    and calls itself complete; with it, both records are named by class and
    kind, the like-for-like counts disagree by exactly them, and the total is a
    floor.
    """
    model = census_world((FIXED_WHOLE, TAGGED), (FIXED_WHOLE, {}), (FIXED_THIRD, {}))
    result = balance.clocked_draw_of(machines.machines_of(model), modeled_registry())

    assert result.complete is False
    assert omitted_rows(result) == [
        (FIXED_THIRD, balance.GAP_NO_MACHINE_STATE, 1),
        (FIXED_WHOLE, balance.GAP_NO_MACHINE_STATE, 1),
    ]
    assert consumer_counts(result) == (3, 1, 2)
    assert result.gaps == ()
    assert result.upper_megawatts == result.lower_megawatts == WHOLE_MEGAWATTS
    assert result.exact is False
    raised = {warning.code: warning.count for warning in result.warnings}
    assert raised.get(balance.WARN_BALANCE_CLOCKED_DRAW_UNMODELED) == ACCEPTANCE_OMITTED


def like_for_like_registry() -> Mapping[str, Building]:
    """The modeled pair, a fixed-zero class, a variable class and the generator.

    Returns:
        The mapping.
    """
    return registry(
        building(FIXED_WHOLE, consumption=WHOLE_MEGAWATTS),
        building(FIXED_THIRD, consumption=THIRD_MEGAWATTS),
        building(ZERO_DRAW, consumption=Fraction(0)),
        building(
            DECLARED_VARIABLE,
            consumption=Fraction(0),
            minimum=Fraction(0),
            maximum=Fraction(100),
            variable=True,
        ),
        building(GENERATOR_CLASS, consumption=WHOLE_MEGAWATTS),
    )


def like_for_like_generators() -> Mapping[str, Generator]:
    """The one generator, with an exact scalar output.

    Returns:
        The mapping.
    """
    return MappingProxyType(
        {
            GENERATOR_CLASS: Generator(
                key=GENERATOR_CLASS,
                display_name=f"Synthetic {GENERATOR_CLASS}",
                power_production=Fraction(30),
                variable_production_constant=None,
                variable_production_factor=None,
                is_variable_production=False,
            )
        }
    )


def test_both_consumer_counts_read_one_predicate() -> None:
    """Like for like: a registry consumer, no generator, and not a fixed zero draw.

    EACH EXCLUSION HAS ITS OWN ROW ON EACH SIDE. In the population, a fixed-zero
    machine is priced and not counted, a no-entry machine is a gap and not
    counted, and a generator is set apart. Among the records that never entered
    it, the same three are not counted - while a VARIABLE class, whose declared
    scalar is also zero, is counted and named, and so is a modeled class whose
    payload never read. A predicate reading the scalar alone drops the variable
    row; one that skips the generator namespace counts the generator row.
    """
    model = census_world(
        (FIXED_WHOLE, TAGGED),
        (ZERO_DRAW, TAGGED),
        (NOT_IN_REGISTRY, TAGGED),
        (GENERATOR_CLASS, TAGGED),
        (ZERO_DRAW, {}),
        (NOT_IN_REGISTRY, {}),
        (GENERATOR_CLASS, {}),
        (DECLARED_VARIABLE, {}),
        unread=(FIXED_THIRD, ZERO_DRAW, NOT_IN_REGISTRY),
    )
    result = balance.clocked_draw_of(
        machines.machines_of(model),
        like_for_like_registry(),
        generators=like_for_like_generators(),
    )

    assert omitted_rows(result) == [
        (FIXED_THIRD, balance.GAP_PAYLOAD_UNREAD, 1),
        (DECLARED_VARIABLE, balance.GAP_NO_MACHINE_STATE, 1),
    ]
    assert consumer_counts(result) == (3, 1, 2)
    assert result.machines_considered == LIKE_FOR_LIKE_CONSIDERED
    assert result.generator_machine_count == 1
    assert [(gap.class_name, gap.kind) for gap in result.gaps] == [
        (NOT_IN_REGISTRY, balance.GAP_NO_REGISTRY_ENTRY)
    ]
    # One unmodeled machine BESIDE two omissions, so the warning's count is
    # graded as their sum and not as whichever of the two is non-zero.
    raised = {warning.code: warning.count for warning in result.warnings}
    assert raised.get(balance.WARN_BALANCE_CLOCKED_DRAW_UNMODELED) == LIKE_FOR_LIKE_UNPRICED
    exact.audit_exact(result, path="clocked")


def overrun_tag(name: str) -> bytes:
    """One IntProperty tag whose declared size runs past the end of its payload.

    THE REAL DECODER ABORTS THE WALK on it: the record's payload is unread and
    every value decoded before the tag is discarded with it.

    Args:
        name: The property name.

    Returns:
        The encoded tag.
    """
    word = "IntProperty"
    tag = save_synthetic.property_tag(name, word, struct.pack("<i", 7))
    at = len(save_synthetic.fstring(name)) + len(save_synthetic.fstring(word))
    return tag[:at] + struct.pack("<i", OVERRUN_SIZE) + tag[at + 4 :]


def test_a_built_consumer_whose_payload_never_read_is_a_named_omission() -> None:
    """CS-1264's round-2 residual, through the REAL loader.

    THE PREMISE IS ASSERTED FIRST: the first actor's producing tag sits ahead
    of a tag whose size runs past the end, so the walk aborts, its values are
    discarded and the machine never reaches ``machines_of``. The second actor is
    an ordinary machine at the reference clock. Before CS-1266 the draw priced
    the second, named nothing and called itself complete; only
    ``WorldMachines.unread_payload_count`` recorded the first, and nothing read it.
    """
    model = decoded_actors(
        (producing_tag(), overrun_tag(TORN_NEIGHBOUR)),
        (float_tag(machines.PROPERTY_OVERCLOCK, 1.0), producing_tag()),
    )
    assert [
        (entry.payload_read, len(entry.values))
        for entry in model.properties.by_record_index.values()
    ] == [(False, 0), (True, 2)]

    population = machines.machines_of(model)
    assert len(population.machines) == 1
    result = balance.clocked_draw_of(population, decoded_registry())

    assert result.complete is False
    assert omitted_rows(result) == [
        (
            objects.class_name_of(save_synthetic.DECODABLE_CLASS_PATH),
            balance.GAP_PAYLOAD_UNREAD,
            1,
        )
    ]
    assert consumer_counts(result) == (2, 1, 1)
    assert result.upper_megawatts == WHOLE_MEGAWATTS


def test_a_population_with_every_consumer_considered_stays_complete() -> None:
    """The control: the same loader and walk, every built consumer in the population."""
    model = census_world((FIXED_WHOLE, TAGGED), (FIXED_THIRD, TAGGED), (ZERO_DRAW, {}))
    result = balance.clocked_draw_of(machines.machines_of(model), like_for_like_registry())

    assert result.complete is True
    assert result.omissions == ()
    assert consumer_counts(result) == (2, 2, 0)


def test_a_hand_built_population_carries_no_census_and_omits_nothing() -> None:
    """A population with no record table behind it has nothing unadmitted to name."""
    result = balance.clocked_draw_of(
        world_machines(clocked(FIXED_WHOLE, Fraction(1))), modeled_registry()
    )

    assert result.omissions == ()
    assert consumer_counts(result) == (1, 1, 0)
    assert result.complete is True


def test_the_omission_kinds_are_their_own_closed_vocabulary() -> None:
    expected = {balance.GAP_PAYLOAD_UNREAD, balance.GAP_NO_MACHINE_STATE}
    assert expected == balance.OMISSION_KINDS
    assert not balance.OMISSION_KINDS & balance.CLOCKED_GAP_KINDS


def test_every_omission_carries_a_reason_and_its_repr_names_no_class() -> None:
    model = census_world((FIXED_WHOLE, {}), unread=(FIXED_THIRD,))
    result = balance.clocked_draw_of(machines.machines_of(model), modeled_registry())

    assert {item.kind for item in result.omissions} == balance.OMISSION_KINDS
    assert all(item.reason for item in result.omissions)
    rendered = " ".join(repr(value) for value in (result, *result.omissions))
    named = [name for name in (FIXED_WHOLE, FIXED_THIRD) if name in rendered]
    assert not named


def test_the_composite_carries_an_omitted_consumer_as_an_incomplete_draw() -> None:
    """The power rule reads ``complete``; an omitted consumer must make it False."""
    model = census_world((FIXED_WHOLE, TAGGED), (FIXED_THIRD, {}))
    result = balance.balance_of(
        built(modeled_counts()),
        modeled_registry(),
        machines.machines_of(model),
        world_network(),
    )

    assert result.clocked_draw.complete is False
    assert result.clocked_draw.omitted_consumer_count == 1
    assert balance.WARN_BALANCE_CLOCKED_DRAW_UNMODELED in {
        warning.code for warning in result.warnings
    }


def test_each_count_is_of_records_never_of_classes() -> None:
    """Two priced machines of one class, three untagged records of another.

    EVERY OTHER ARM HOLDS ONE RECORD PER (CLASS, KIND), so a count of classes
    and a count of records agree there and grade nothing between them. Here
    they differ on every count: considered is 2 and not 1, the one omission
    counts 3 and not 1, omitted is 3 and not 1, and built is 5.
    """
    model = census_world(
        *((FIXED_WHOLE, TAGGED) for _ in range(PRICED_MACHINES)),
        *((FIXED_THIRD, {}) for _ in range(UNTAGGED_RECORDS)),
    )
    result = balance.clocked_draw_of(machines.machines_of(model), modeled_registry())

    assert consumer_counts(result) == (
        PRICED_MACHINES + UNTAGGED_RECORDS,
        PRICED_MACHINES,
        UNTAGGED_RECORDS,
    )
    assert omitted_rows(result) == [(FIXED_THIRD, balance.GAP_NO_MACHINE_STATE, UNTAGGED_RECORDS)]
    assert result.upper_megawatts == WHOLE_MEGAWATTS * PRICED_MACHINES
    raised = {warning.code: warning.count for warning in result.warnings}
    assert raised.get(balance.WARN_BALANCE_CLOCKED_DRAW_UNMODELED) == UNTAGGED_RECORDS


def test_omissions_count_every_class_and_kind_in_their_sorted_order() -> None:
    """Two classes by two kinds, each with its own count, in (class, kind) order.

    THE CENSUS IS READ KIND BY KIND, unread first, so an omission list that
    is not sorted comes out with both unread rows ahead of both untagged ones;
    sorted, each class's two rows sit together, ``no-machine-state`` before
    ``payload-unread``. Every count is distinct, so a swap between rows shows.
    """
    model = census_world(
        *((FIXED_WHOLE, TAGGED) for _ in range(PRICED_MACHINES)),
        *((FIXED_THIRD, {}) for _ in range(UNTAGGED_RECORDS)),
        (FIXED_WHOLE, {}),
        unread=(FIXED_WHOLE, FIXED_WHOLE, FIXED_THIRD),
    )
    result = balance.clocked_draw_of(machines.machines_of(model), modeled_registry())

    expected = [
        (FIXED_THIRD, balance.GAP_NO_MACHINE_STATE, UNTAGGED_RECORDS),
        (FIXED_THIRD, balance.GAP_PAYLOAD_UNREAD, 1),
        (FIXED_WHOLE, balance.GAP_NO_MACHINE_STATE, 1),
        (FIXED_WHOLE, balance.GAP_PAYLOAD_UNREAD, 2),
    ]
    assert omitted_rows(result) == expected
    omitted = sum(count for _, _, count in expected)
    assert consumer_counts(result) == (PRICED_MACHINES + omitted, PRICED_MACHINES, omitted)


def test_a_record_the_walk_paired_with_no_payload_is_an_unread_omission() -> None:
    """A level whose record and payload counts disagree, through the REAL loader.

    THE SAVE LAYER ATTRIBUTES NOTHING in such a level - the pairing is
    undefined - so its record arrives with an entry marked read and no values:
    the property reader returns that shape for a record of no extent without
    reading a byte. Labelling it "payload read and carried no clock" would be a
    claim about a payload nobody read. The premise is asserted first.
    """
    model = mismatched_world()
    (record,) = model.objects.records
    (entry,) = model.properties.by_record_index.values()
    assert objects.WARN_PAYLOAD_COUNT_DISAGREEMENT in {w.code for w in model.objects.warnings}
    assert (entry.payload_read, len(entry.values), entry.payload_present) == (True, 0, False)

    class_name = objects.class_name_of(record.type_path)
    entries = registry(building(class_name, consumption=WHOLE_MEGAWATTS))
    result = balance.clocked_draw_of(machines.machines_of(model), entries)

    assert omitted_rows(result) == [(class_name, balance.GAP_PAYLOAD_UNREAD, 1)]
    assert result.complete is False


def mismatched_world() -> WorldModel:
    """The save-layer suite's one-record, zero-payload level, loaded whole.

    Returns:
        The world model ``load_world_from_bytes`` publishes.
    """
    header_version, save_version = MISMATCHED_PAIR
    head = save_synthetic.build_header(header_version=header_version, save_version=save_version)
    framed = save_synthetic.build_chunks(
        objects_fx._mismatched_entry_count_body(),  # noqa: SLF001
        framing=save_synthetic.default_framing(header_version),
    )
    return world.load_world_from_bytes(head + framed)


def test_every_record_of_a_flat_walk_is_an_unread_omission() -> None:
    """The sibling of the arm above: the flat walk attributes no payload to any record.

    Its every record arrives marked read with no values, through the same
    reader branch, so a consumer in a flat-walked world is unread, never
    "read and untagged".
    """
    blob = save_synthetic.build_save(
        objects=(
            save_synthetic.SyntheticObject(
                save_synthetic.DECODABLE_CLASS_PATH,
                save_synthetic.DECODABLE_ROOT,
                save_synthetic.DECODABLE_INSTANCE,
            ),
        )
    )
    model = world.load_world_from_bytes(blob, body_layout=world.BODY_LAYOUT_FLAT)
    (entry,) = model.properties.by_record_index.values()
    assert (entry.payload_read, len(entry.values), entry.payload_present) == (True, 0, False)

    result = balance.clocked_draw_of(machines.machines_of(model), decoded_registry())

    assert omitted_rows(result) == [
        (
            objects.class_name_of(save_synthetic.DECODABLE_CLASS_PATH),
            balance.GAP_PAYLOAD_UNREAD,
            1,
        )
    ]


# ---------------------------------------------------------------------------
# CS-1281: a class that cannot be clocked has no clock to elide
# ---------------------------------------------------------------------------
#
# The elided count says how many machines were priced at the class default
# BECAUSE their clock tag was elided. A class whose entry declares it cannot be
# clocked writes no tag because it has no clock, so counting it there inflates
# the count with machines whose price was never a default. It is still priced
# at the reference clock - the only clock it has - and exactly; it is simply not
# an elided one. A class whose capability is UNKNOWN stays elided: excluding it
# would read the registry's None as False.

#: An invented built class whose entry declares its clock cannot be changed.
#: Its exponent is NOT whole, so a price taken anywhere but the reference clock
#: would be a bracket and show.
FIXED_CLOCK_CLASS = "Build_SyntheticFixedClockQx73_C"

#: An invented built class whose entry declares nothing about its clock.
UNKNOWN_CLOCK_CLASS = "Build_SyntheticUnknownClockQx73_C"

#: How many machines of :data:`FIXED_CLOCK_CLASS` the reddening arm builds.
FIXED_CLOCK_MACHINES = 2


def clockability_registry() -> Mapping[str, Building]:
    """One clockable entry, one that cannot be clocked, one that does not say.

    Returns:
        The mapping.
    """
    return registry(
        replace(building(FIXED_WHOLE, consumption=WHOLE_MEGAWATTS), clockable=True),
        replace(
            building(FIXED_CLOCK_CLASS, consumption=THIRD_MEGAWATTS, exponent=BRACKETED_EXPONENT),
            clockable=False,
        ),
        building(UNKNOWN_CLOCK_CLASS, consumption=WHOLE_MEGAWATTS),
    )


def test_a_class_that_cannot_be_clocked_reddens_the_arm_when_counted_elided() -> None:
    """Alike in every machine field, so only the registry's capability decides.

    COUNTING THE NON-CLOCKABLE CLASS ELIDED makes the count three and the
    warning three, and marks its group elided; the clockable machine beside it
    is the control that the elided path still runs.
    """
    population = world_machines(
        *(elided(FIXED_CLOCK_CLASS) for _ in range(FIXED_CLOCK_MACHINES)), elided(FIXED_WHOLE)
    )
    result = balance.clocked_draw_of(population, clockability_registry())

    assert result.elided_clock_count == 1
    raised = {warning.code: warning.count for warning in result.warnings}
    assert raised.get(balance.WARN_BALANCE_CLOCK_ELIDED) == 1
    groups = {group.class_name: group for group in result.contributions}
    fixed = groups[FIXED_CLOCK_CLASS]
    assert fixed.clock_elided is False
    assert fixed.clock == power.REFERENCE_CLOCK
    assert fixed.bound == balance.BOUND_EXACT
    assert fixed.machine_count == FIXED_CLOCK_MACHINES
    assert fixed.lower_total == fixed.upper_total == THIRD_MEGAWATTS * FIXED_CLOCK_MACHINES
    assert groups[FIXED_WHOLE].clock_elided is True
    # The reason names a fixed clock, never the elided default's.
    assert fixed.reason
    assert fixed.reason != groups[FIXED_WHOLE].reason
    assert result.complete is True
    assert result.exact is True
    assert sum(group.machine_count for group in result.contributions) == len(population.machines)


def test_a_class_whose_clock_capability_is_unknown_stays_an_elided_clock() -> None:
    """The registry's None is a named unknown, so it is never read as False."""
    result = balance.clocked_draw_of(
        world_machines(elided(UNKNOWN_CLOCK_CLASS)), clockability_registry()
    )

    (group,) = result.contributions
    assert group.clock_elided is True
    assert result.elided_clock_count == 1


def test_a_class_that_cannot_be_clocked_keeps_an_unread_clock_a_named_gap() -> None:
    """Scope: only the elision mark is re-read; an unread clock is not a fixed one.

    An unread payload or a refused tag is a fact about this reader, and a class
    whose clock is fixed does not make that fact go away.
    """
    result = balance.clocked_draw_of(
        world_machines(clocked(FIXED_CLOCK_CLASS, None)), clockability_registry()
    )

    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [(balance.GAP_CLOCK_UNREAD, 1)]
    assert result.contributions == ()


def test_a_boosted_machine_of_a_class_that_cannot_be_clocked_is_still_a_boost_gap() -> None:
    result = balance.clocked_draw_of(
        world_machines(boosted(FIXED_CLOCK_CLASS, None, clock_elided=True)),
        clockability_registry(),
    )

    assert [(gap.kind, gap.machine_count) for gap in result.gaps] == [
        (balance.GAP_BOOST_UNMODELED, 1)
    ]
    assert result.elided_clock_count == 0


@pytest.mark.parametrize("class_name", [FIXED_WHOLE, FIXED_CLOCK_CLASS])
def test_a_present_clock_is_never_overridden_by_the_elision_mark(class_name: str) -> None:
    """The Session 124 residual: the overclock-is-None guard on the elided line.

    A hand-built state can carry a read clock AND the mark, which no reader
    produces. Dropping the guard prices it at the default and counts it elided.
    """
    state = replace(clocked(class_name, DOUBLE_CLOCK), overclock_elided=True)
    result = balance.clocked_draw_of(world_machines(state), clockability_registry())

    (group,) = result.contributions
    assert group.clock == DOUBLE_CLOCK
    assert group.clock_elided is False
    assert result.elided_clock_count == 0
