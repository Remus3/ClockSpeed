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

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from fractions import Fraction
from types import MappingProxyType

import pytest

from clockspeed.audit import balance, machines, network, placement
from clockspeed.data.registry import Building
from clockspeed.save import objects
from clockspeed.save.header import SaveHeader
from clockspeed.save.world import (
    EMPTY_UNLOCK_STATE,
    RecordProperties,
    WorldModel,
    WorldProperties,
)
from clockspeed.solve import exact, power

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
