"""CS-1041: per-machine state - the producing flag, the recipe, and the overclock.

Every fixture here is a hand-built synthetic ``WorldModel``. Nothing in this
module opens a save, a docs file or the install - see ``tests/audit/__init__.py``
for the four rules.

THE ARM THE ACCEPTANCE NAMES IS THE ABSENT ONE. A missing ``mCurrentPotential``
must read null and never 1. Defaulting it to 1 is not a rounding choice: the
game's own default clock IS 1, so the wrong answer is indistinguishable from the
right one on every machine nobody has overclocked, and the first time it matters
is the one machine where it is false. So an absence arm and a presence arm are
separate here, and a third arm grades that FALSE is not ABSENT for the producing
flag - the same collapse wearing a bool.

THE FLOAT BRIDGE IS GRADED, AND NO ACCEPTANCE CLAUSE ASKED FOR IT.
``mCurrentPotential`` is a ``FloatProperty`` and non-negotiable 6 forbids a float
in the solve path, so something must convert - and the obvious conversion is the
wrong one. ``Fraction(1.2999999523162842)`` is an EXACT reading of a binary
approximation and a WRONG reading of the decimal the game wrote, and being exact
it is invisible to every downstream exactness check. That is the trap
``clockspeed/solve/exact.py`` ``to_exact`` refuses a float outright to avoid.
The arms below therefore assert the recovered value EQUALS the authored decimal,
not merely that it is a Fraction - an arm asserting the type alone passes on the
defect.

STRUCTURE AND MEMBERSHIP ARE GRADED APART, for the reason ``test_network.py``
gives: one entry per machine record in file order is one arm, and what each
entry HOLDS is another.
"""

from __future__ import annotations

import copy
import struct
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from fractions import Fraction
from types import MappingProxyType

from clockspeed.audit import machines
from clockspeed.save import objects
from clockspeed.save.header import SaveHeader
from clockspeed.save.objects import ObjectReference
from clockspeed.save.world import (
    EMPTY_UNLOCK_STATE,
    RecordProperties,
    WorldModel,
    WorldProperties,
)

# An invented 22-character base64url literal. Never a real world token.
SYNTHETIC_TOKEN = "ClockspeedMachineTok1"  # noqa: S105 - an invented marker, not a secret

SYNTHETIC_LEVEL = "SyntheticLevel:SyntheticPersistent"

#: The machine's own instance path, and the marker the refusal sweep hunts.
MACHINE_INSTANCE = f"{SYNTHETIC_LEVEL}.SyntheticMachineQx72_C_7101"

#: A shipped asset path under a permitted root: what a recipe reference looks like.
RECIPE_ASSET = "/Game/FactoryGame/Synthetic/Recipe_SyntheticQx72.Recipe_SyntheticQx72_C"

#: The bare class name the path above reduces to.
RECIPE_CLASS = "Recipe_SyntheticQx72_C"

#: A shipped-looking path under NO permitted root.
FOREIGN_ASSET = "/SyntheticMod/Recipes/Recipe_ForeignQx72.Recipe_ForeignQx72_C"

#: A RECORD INSTANCE path that ALSO passes the permitted-root check, because the
#: level it names begins with one. THE MASKING CONTROL, and it is not
#: hypothetical: with an ordinary instance path the root clause refuses first and
#: the instance clause is graded by nothing at all. Measured this session -
#: disabling the instance clause left all 29 arms green until this fixture
#: existed. ``clockspeed/save/world.py`` names the same case in prose.
PERMITTED_ROOT_INSTANCE = f"/Game/{SYNTHETIC_LEVEL}.SyntheticMachineQx72_C_7102"

MACHINE_CLASS = "Build_SyntheticSmelterQx72_C"

#: How many records the file-order structure arm builds.
ORDERED_RECORD_COUNT = 2

#: A decimal no binary float can hold. Reading it through ``Fraction(float)``
#: yields a 50-odd digit ratio; reading it as the authored decimal yields 13/10.
AUTHORED_OVERCLOCK = "1.3"


def as_float32(text: str) -> float:
    """Round one decimal string through float32, the way a save carries it.

    Args:
        text: The authored decimal.

    Returns:
        The float32 value, widened to a Python float.
    """
    return float(struct.unpack("<f", struct.pack("<f", float(text)))[0])


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


def record(instance_name: str = MACHINE_INSTANCE) -> objects.ObjectRecord:
    """Build one synthetic machine record.

    Args:
        instance_name: The instance path.

    Returns:
        The record.
    """
    return objects.ObjectRecord(
        kind=objects.KIND_ACTOR,
        type_path=f"/Game/FactoryGame/Buildable/{MACHINE_CLASS}.{MACHINE_CLASS}",
        root_object=instance_name,
        instance_name=instance_name,
        transform=None,
        parent=None,
        object_type=1,
        was_placed_in_level=0,
        body_offset=0,
        body_length=0,
    )


def entry(
    values: Mapping[str, object],
    *references: ObjectReference,
    payload_read: bool = True,
) -> RecordProperties:
    """Build one record's published properties.

    Args:
        values: The decoded per-name values.
        references: The typed, tag-ordered references.
        payload_read: Whether the payload read under the measured grammar.

    Returns:
        The properties.
    """
    return RecordProperties(
        values=MappingProxyType(dict(values)),
        schema_name="SyntheticSchema",
        resolved=None,
        payload_read=payload_read,
        warning_codes=() if payload_read else (objects.WARN_UNPARSED_PROPERTY_PAYLOAD,),
        references=references,
    )


def recipe_reference(object_path: str = RECIPE_ASSET) -> ObjectReference:
    """Build the typed reference a current-recipe tag decodes to.

    Args:
        object_path: The value's second string.

    Returns:
        The reference.
    """
    return ObjectReference(
        property_name=machines.PROPERTY_RECIPE,
        level_reference="",
        object_path=object_path,
    )


def world(*entries: RecordProperties) -> WorldModel:
    """Build a synthetic world model of one record per supplied property entry.

    Args:
        entries: One entry per record, in file order.

    Returns:
        The model.
    """
    return WorldModel(
        token=SYNTHETIC_TOKEN,
        header=header(),
        objects=objects.ObjectTable(
            records=tuple(record(f"{MACHINE_INSTANCE}{index}") for index in range(len(entries))),
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
        properties=WorldProperties(by_record_index=MappingProxyType(dict(enumerate(entries)))),
    )


def reachable(value: object, seen: set[int] | None = None) -> list[object]:
    """Every value reachable from one object, the object itself included.

    STRUCTURAL on purpose - see the same helper in ``test_inventory.py``.

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
# The three values reaching the model
# ---------------------------------------------------------------------------


def test_the_producing_flag_reaches_the_model() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: True})))

    assert result.machines[0].producing is True


def test_a_producing_flag_of_false_is_false_and_not_absent() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: False})))

    assert result.machines[0].producing is False


def test_an_absent_producing_flag_is_null_and_not_false() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_OVERCLOCK: 1.0})))

    assert result.machines[0].producing is None


def test_the_current_recipe_reaches_the_model_as_its_class_name() -> None:
    result = machines.machines_of(world(entry({}, recipe_reference())))

    assert result.machines[0].recipe_class_name == RECIPE_CLASS


def test_an_absent_recipe_is_null() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: True})))

    assert result.machines[0].recipe_class_name is None


# ---------------------------------------------------------------------------
# THE acceptance arm - an absent overclock is null and never 1
# ---------------------------------------------------------------------------


def test_an_absent_overclock_is_null_rather_than_one() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: True})))

    assert result.machines[0].overclock is None


def test_an_absent_overclock_is_not_reported_as_available() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: True})))

    assert result.overclock_available is False


def test_a_present_overclock_of_one_is_distinguishable_from_an_absent_one() -> None:
    present = machines.machines_of(world(entry({machines.PROPERTY_OVERCLOCK: 1.0})))
    absent = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: True})))

    assert present.machines[0].overclock == Fraction(1)
    assert absent.machines[0].overclock is None


# ---------------------------------------------------------------------------
# The float-to-Fraction bridge
# ---------------------------------------------------------------------------


def test_the_bridge_recovers_the_authored_decimal_not_the_binary_reading() -> None:
    stored = as_float32(AUTHORED_OVERCLOCK)

    assert machines.exact_from_float32(stored) == Fraction(AUTHORED_OVERCLOCK)
    assert machines.exact_from_float32(stored) != Fraction(stored)


def test_a_stored_overclock_crosses_as_that_exact_fraction() -> None:
    result = machines.machines_of(
        world(entry({machines.PROPERTY_OVERCLOCK: as_float32(AUTHORED_OVERCLOCK)}))
    )

    assert result.machines[0].overclock == Fraction(AUTHORED_OVERCLOCK)


def test_the_bridge_refuses_a_non_finite_value() -> None:
    assert machines.exact_from_float32(float("inf")) is None
    assert machines.exact_from_float32(float("nan")) is None


def test_the_bridge_refuses_a_value_no_float32_holds() -> None:
    """0.1 as a DOUBLE is not a float32 value, and guessing which one it meant is a lie."""
    assert machines.exact_from_float32(0.1) is None


def test_the_bridge_refuses_a_non_float() -> None:
    assert machines.exact_from_float32(1) is None
    assert machines.exact_from_float32("1.3") is None
    assert machines.exact_from_float32(True) is None


def test_a_refused_overclock_is_counted_rather_than_dropped() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_OVERCLOCK: 0.1})))

    assert result.machines[0].overclock is None
    assert result.refused_overclock_count == 1
    codes = {warning.code for warning in result.warnings}
    assert machines.WARN_MACHINES_OVERCLOCK_REFUSED in codes


# ---------------------------------------------------------------------------
# Which population a recipe reference is in
# ---------------------------------------------------------------------------


def test_a_recipe_reference_naming_a_record_instance_is_refused() -> None:
    """The path passes the ROOT check, so ONLY the instance clause can refuse it."""
    result = machines.machines_of(world(entry({}, recipe_reference(PERMITTED_ROOT_INSTANCE))))

    assert result.machines[0].recipe_class_name is None
    assert result.refused_recipe_count == 1


def test_a_recipe_reference_under_no_permitted_root_is_refused() -> None:
    result = machines.machines_of(world(entry({}, recipe_reference(FOREIGN_ASSET))))

    assert result.machines[0].recipe_class_name is None
    assert result.refused_recipe_count == 1


def test_a_refused_recipe_is_flagged() -> None:
    result = machines.machines_of(world(entry({}, recipe_reference(FOREIGN_ASSET))))

    codes = {warning.code for warning in result.warnings}
    assert machines.WARN_MACHINES_RECIPE_REFUSED in codes


def test_a_reference_of_another_name_is_not_read_as_the_recipe() -> None:
    other = ObjectReference(
        property_name="mSyntheticOtherQx72",
        level_reference="",
        object_path=RECIPE_ASSET,
    )
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: True}, other)))

    assert result.machines[0].recipe_class_name is None
    assert result.refused_recipe_count == 0


# ---------------------------------------------------------------------------
# Structure - the SHAPE of the published population, graded apart
# ---------------------------------------------------------------------------


def test_one_entry_is_published_per_machine_record_in_file_order() -> None:
    result = machines.machines_of(
        world(
            entry({machines.PROPERTY_PRODUCING: True}),
            entry({machines.PROPERTY_PRODUCING: False}),
        )
    )

    assert len(result.machines) == ORDERED_RECORD_COUNT
    assert [machine.producing for machine in result.machines] == [True, False]


def test_a_record_carrying_no_machine_property_yields_no_entry() -> None:
    result = machines.machines_of(world(entry({"mSyntheticUnrelatedQx72": 7})))

    assert result.machines == ()
    assert result.records_considered == 1


def test_every_entry_carries_its_own_records_class_name() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: True})))

    assert result.machines[0].class_name == MACHINE_CLASS


def test_two_runs_over_one_model_return_equal_models() -> None:
    model = world(entry({machines.PROPERTY_PRODUCING: True}, recipe_reference()))

    assert machines.machines_of(model) == machines.machines_of(model)


# ---------------------------------------------------------------------------
# The availability flags, declared per field
# ---------------------------------------------------------------------------


def test_each_field_carries_its_own_availability_flag() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: True})))

    assert result.producing_available is True
    assert result.recipe_available is False
    assert result.overclock_available is False


def test_a_world_with_no_machine_state_at_all_says_so() -> None:
    result = machines.machines_of(world(entry({"mSyntheticUnrelatedQx72": 7})))

    codes = {warning.code for warning in result.warnings}
    assert machines.WARN_MACHINES_NONE_READ in codes


def test_the_unread_payload_count_travels_as_the_honest_denominator() -> None:
    result = machines.machines_of(
        world(entry({machines.PROPERTY_PRODUCING: True}, payload_read=False))
    )

    assert result.unread_payload_count == 1
    codes = {warning.code for warning in result.warnings}
    assert machines.WARN_MACHINES_PAYLOAD_UNREAD in codes


# ---------------------------------------------------------------------------
# Refusals, asserted structurally
# ---------------------------------------------------------------------------


def test_no_record_instance_name_reaches_the_machines_model() -> None:
    model = world(
        entry({machines.PROPERTY_PRODUCING: True}, recipe_reference(PERMITTED_ROOT_INSTANCE))
    )
    result = machines.machines_of(model)

    control = [
        value for value in reachable(model) if isinstance(value, str) and MACHINE_INSTANCE in value
    ]
    assert control, "the walk cannot see the marker in the INPUT, so its absence proves nothing"

    leaked = [
        value for value in reachable(result) if isinstance(value, str) and MACHINE_INSTANCE in value
    ]
    assert not leaked


def test_no_float_reaches_any_machine_output_field() -> None:
    model = world(entry({machines.PROPERTY_OVERCLOCK: as_float32(AUTHORED_OVERCLOCK)}))
    result = machines.machines_of(model)

    control = [value for value in reachable(model) if type(value) is float]
    assert control, "the walk cannot see a float in the INPUT, so its absence proves nothing"

    assert not [value for value in reachable(result) if type(value) is float]


def test_a_non_bool_producing_value_is_refused_rather_than_coerced() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: 1})))

    assert result.machines[0].producing is None


def test_no_machines_type_annotates_a_carrier_field() -> None:
    for declared in (machines.MachineState, machines.WorldMachines):
        for field in fields(declared):
            assert "bytes" not in str(field.type)
            assert "Path" not in str(field.type)


# ---------------------------------------------------------------------------
# CS-1263: an ELIDED clock is told apart from an UNREADABLE one
# ---------------------------------------------------------------------------
#
# The serializer writes no ``mCurrentPotential`` tag for a machine at the class
# default, so an absent tag on a cleanly read payload is a measured fact and not
# an unknown. Every arm below keeps ``overclock`` None - CS-1041's clause above
# stands - and grades only the flag that says WHY it is None.


def test_an_absent_overclock_on_a_cleanly_read_payload_is_marked_elided() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_PRODUCING: True})))

    assert result.machines[0].overclock is None
    assert result.machines[0].overclock_elided is True


def test_a_refused_overclock_is_not_marked_elided() -> None:
    result = machines.machines_of(world(entry({machines.PROPERTY_OVERCLOCK: 0.1})))

    assert result.machines[0].overclock is None
    assert result.machines[0].overclock_elided is False


def test_a_present_overclock_is_not_marked_elided() -> None:
    result = machines.machines_of(
        world(entry({machines.PROPERTY_OVERCLOCK: as_float32(AUTHORED_OVERCLOCK)}))
    )

    assert result.machines[0].overclock_elided is False


def test_an_absent_overclock_on_an_unread_payload_is_not_marked_elided() -> None:
    result = machines.machines_of(
        world(entry({machines.PROPERTY_PRODUCING: True}, payload_read=False))
    )

    assert result.machines[0].overclock_elided is False


def test_an_absent_overclock_beside_a_disagreeing_tag_is_not_marked_elided() -> None:
    """A measured tag whose bytes disagreed may have been the clock itself."""
    disagreeing = replace(entry({machines.PROPERTY_PRODUCING: True}), disagreeing_value_count=1)
    result = machines.machines_of(world(disagreeing))

    assert result.machines[0].overclock_elided is False


def test_a_hand_built_state_never_claims_an_elided_clock() -> None:
    state = machines.MachineState(
        class_name="Build_SyntheticQx73_C",
        producing=True,
        recipe_class_name=None,
        overclock=None,
    )

    assert state.overclock_elided is False


# ---------------------------------------------------------------------------
# CS-1266: every walked record lands in exactly one population
# ---------------------------------------------------------------------------
#
# The clocked draw cross-checks the machines it considered against what is
# built, and it can only do that if the records this module did NOT admit are
# counted rather than dropped. They are counted per class, split by whether the
# payload read: a read payload with no machine tag is a fact about the record,
# an unread one is a fact about this reader.

#: An invented property no machine reader knows.
UNRELATED_PROPERTY = "mSyntheticUnrelatedQx72"


def test_every_walked_record_lands_in_exactly_one_population() -> None:
    model = world(
        entry({machines.PROPERTY_PRODUCING: True}),
        entry({UNRELATED_PROPERTY: 7}),
        entry({}),
        entry({}, payload_read=False),
    )
    result = machines.machines_of(model)

    assert len(result.machines) == 1
    assert dict(result.unadmitted_read_counts) == {MACHINE_CLASS: 2}
    assert dict(result.unadmitted_unread_counts) == {MACHINE_CLASS: 1}
    unadmitted = sum(count for _, count in result.unadmitted_read_counts) + sum(
        count for _, count in result.unadmitted_unread_counts
    )
    assert len(result.machines) + unadmitted == len(model.objects.records)


def test_an_unread_payload_that_still_carries_a_machine_tag_is_admitted_not_counted() -> None:
    """Admission is decided first: a machine is never also an unadmitted record."""
    result = machines.machines_of(
        world(entry({machines.PROPERTY_PRODUCING: True}, payload_read=False))
    )

    assert len(result.machines) == 1
    assert dict(result.unadmitted_unread_counts) == {}


def test_a_record_no_property_pass_reached_is_counted_unread() -> None:
    """A table with no property entry at all was never read, so its records are unread."""
    model = replace(
        world(entry({machines.PROPERTY_PRODUCING: True}), entry({})),
        properties=WorldProperties(by_record_index=MappingProxyType({})),
    )
    result = machines.machines_of(model)

    assert result.machines == ()
    assert dict(result.unadmitted_unread_counts) == {MACHINE_CLASS: 2}
    assert dict(result.unadmitted_read_counts) == {}


def test_a_hand_built_model_has_nothing_unadmitted() -> None:
    result = machines.WorldMachines(
        machines=(),
        producing_available=False,
        recipe_available=False,
        overclock_available=False,
        records_considered=0,
        unread_payload_count=0,
        refused_overclock_count=0,
        refused_recipe_count=0,
        warnings=(),
    )

    assert dict(result.unadmitted_read_counts) == {}
    assert dict(result.unadmitted_unread_counts) == {}


def test_the_machines_repr_names_no_unadmitted_class() -> None:
    result = machines.machines_of(world(entry({}), entry({}, payload_read=False)))

    assert MACHINE_CLASS not in repr(result)


def test_a_model_carrying_a_census_deep_copies_equal() -> None:
    """A caller snapshots this model to prove nothing mutated it, so it must copy."""
    result = machines.machines_of(world(entry({}), entry({}, payload_read=False)))

    assert copy.deepcopy(result) == result


def test_a_record_paired_with_no_payload_is_unread_whatever_its_entry_says() -> None:
    """No payload means none was read, so "read and untagged" would be false.

    The property reader returns a read, empty entry for a record the walk paired
    with no payload without reading a byte - the flat walk's every record, and a
    levelled record whose level declared fewer payloads than records - and the
    save layer says so in ``payload_present``. The entry beside it is alike in
    every other field, so only that flag decides between the two buckets.
    """
    result = machines.machines_of(world(replace(entry({}), payload_present=False), entry({})))

    assert result.unadmitted_unread_counts == ((MACHINE_CLASS, 1),)
    assert result.unadmitted_read_counts == ((MACHINE_CLASS, 1),)
