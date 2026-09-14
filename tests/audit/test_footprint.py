"""CS-1044: the footprint model over one world - category, extent, elevation, skips.

Every fixture here is a hand-built synthetic ``WorldModel``. Nothing in this
module opens a save, a docs file or the install, and nothing here needs the game
to be present - see ``tests/audit/__init__.py`` for the four rules.

THE CATEGORY ARM DERIVES ITS EXPECTATION FROM THE MODEL'S OWN DECLARED FIELD.
A test that retyped the twelve category names would assert that the author can
copy a list, and would stay green on the day a category is declared and wired to
nothing - which is precisely the defect the acceptance names. So the fixture is
built by walking ``footprint.CATEGORY_OF_CLASS``, one record per allowlisted
class, and the expectation is read off ``WorldFootprint.categories_declared``.

THE CATEGORY COUNTS ARE ASSERTED PER CATEGORY AND NEVER OVER THE POOL. A
threshold summed over every category is satisfied by its largest member while
the smallest goes entirely unmeasured - this project has measured that failure.
``awesome_sink`` carries two classes and ``foundation`` carries two hundred and
thirty one, so a pooled count would be decided by the foundations alone.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Final

from clockspeed.audit import footprint
from clockspeed.save import objects
from clockspeed.save.header import SaveHeader
from clockspeed.save.world import EMPTY_UNLOCK_STATE, WorldModel

# An invented 22-character base64url literal. Never a real world token.
SYNTHETIC_TOKEN = "ClockspeedAuditToken2"  # noqa: S105 - an invented marker, not a secret

# The markers the refusal arms hunt for. Each is a value a correct model can
# never carry, planted in the INPUT so the walk has a control.
INSTANCE_NAME_MARKER = "SyntheticInstanceNameMarkerQx73"
PATH_MARKER = "SyntheticPathMarkerQx73"
BODY_OFFSET_MARKER = 987654326
BODY_LENGTH_MARKER = 987654327

#: The orientation every fixture carries unless it says otherwise. Exactly
#: representable in float32, so a rendered expectation is exact rather than
#: approximately right.
IDENTITY_ROTATION: Final = (0.0, 0.0, 0.0, 1.0)
IDENTITY_SCALE: Final = (1.0, 1.0, 1.0)

#: A distinctive per-axis scale, every component exactly representable. Chosen
#: so an arm that asserted unity by accident would fail.
PLANTED_SCALE: Final = (2.0, 0.5, -1.5)

#: A spelling that does not exist and never has, chosen to CONTAIN the word a
#: substring rule would match on. A denylist wearing a disguise categorises this
#: as a conveyor; an allowlist skips it and says so.
UNMEASURED_CONVEYOR_LOOKALIKE: Final = "Build_ConveyorBeltMk9_C"

#: A buildable spelling off the allowlist entirely, with nothing in its name for
#: any rule to latch onto.
UNLISTED_BUILDABLE: Final = "Build_NotOnTheFootprintList_C"

#: EVERY MEASURED NON-COAL POWER SOURCE, NAMED HERE AND NOT READ OFF THE MODULE.
#: This list is the one place in this file that deliberately retypes spellings,
#: and the reason is an ORACLE failure caught by mutation: the first cut of the
#: generator arm iterated ``CLASSES_BY_CATEGORY[CATEGORY_GENERATOR]``, so a
#: mutant that DELETED a generator from that set also deleted it from the arm's
#: subject and survived with 17 passed. An arm whose oracle cannot observe the
#: value it names passes for that reason alone. Retyping the category SET would
#: still be a test that asserts the author can copy; retyping the handful of
#: class names the ruling is about is the independent oracle that kills the
#: mutant.
MEASURED_NON_COAL_GENERATORS: Final = (
    "Build_AlienPowerBuilding_C",
    "Build_GeneratorBiomass_Automated_C",
    "Build_GeneratorFuel_C",
    "Build_GeneratorGeoThermal_C",
    "Build_GeneratorIntegratedBiomass_C",
    "Build_GeneratorNuclear_C",
)

#: How many off-allowlist buildables the skip arm plants. Named so the assertion
#: states an expectation rather than comparing a number to itself.
EXPECTED_SKIPPED: Final = 2

#: The three elevations the ordering arm plants, deliberately out of order.
PLANTED_ELEVATIONS: Final = (300.0, 100.0, 200.0)

#: Their ranks once ordered ascending, in the order the fixture plants them.
EXPECTED_ELEVATION_ORDER: Final = (2, 0, 1)

#: Component counts, named so an arm states its expectation rather than
#: comparing two collections that are both empty.
EXTENT_COMPONENTS: Final = 3


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


def actor(
    type_path: str,
    translation: tuple[float, float, float] | None,
    *,
    instance_name: str = INSTANCE_NAME_MARKER,
    rotation: tuple[float, float, float, float] = IDENTITY_ROTATION,
    scale: tuple[float, float, float] = IDENTITY_SCALE,
) -> objects.ObjectRecord:
    """Build one synthetic actor record.

    Args:
        type_path: The class path, namespaced or bare.
        translation: The placement, or None for a record carrying no transform.
        instance_name: The instance name. Defaults to the refusal marker, so
            EVERY fixture in this module plants it without having to say so.
        rotation: The quaternion, in file order. Defaults to the identity.
        scale: The per-axis scale. Defaults to unity.

    Returns:
        The record.
    """
    transform = (
        None
        if translation is None
        else objects.Transform(
            rotation=rotation,
            translation=translation,
            scale=scale,
        )
    )
    return objects.ObjectRecord(
        kind=objects.KIND_ACTOR,
        type_path=type_path,
        root_object=PATH_MARKER,
        instance_name=instance_name,
        transform=transform,
        parent=None,
        object_type=1,
        was_placed_in_level=0,
        body_offset=BODY_OFFSET_MARKER,
        body_length=BODY_LENGTH_MARKER,
    )


def table(records: tuple[objects.ObjectRecord, ...]) -> objects.ObjectTable:
    """Build a synthetic object table around the given records.

    Args:
        records: The records, in order.

    Returns:
        The table.
    """
    return objects.ObjectTable(
        records=records,
        unknown_classes=(),
        warnings=(),
        declared_body_length=0,
        body_consumed=0,
        body_prefix_width=8,
        transform_delta=0,
        save_version=52,
        header_version=14,
        level_count=1,
    )


def world(records: tuple[objects.ObjectRecord, ...] = ()) -> WorldModel:
    """Build a synthetic world model holding exactly what a test needs.

    Args:
        records: The object records.

    Returns:
        The model.
    """
    return WorldModel(
        token=SYNTHETIC_TOKEN,
        header=header(),
        objects=table(records),
        unlocks=EMPTY_UNLOCK_STATE,
        nodes=(),
        warnings=(),
    )


def reachable(value: object, seen: set[int] | None = None) -> list[object]:
    """Every value reachable from one object, the object itself included.

    Walks dataclass fields, mappings and sequences. STRUCTURAL on purpose: an
    assertion that named today's field list would pass unchanged the day a field
    is added, which is the defect these arms exist to catch.

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


def one_record_per_allowlisted_class() -> tuple[objects.ObjectRecord, ...]:
    """Build a world holding exactly one actor of EVERY allowlisted class.

    DERIVED FROM THE MODULE'S OWN MAPPING rather than from a list retyped here.
    A category declared and wired to no class shows up as a category the served
    set cannot contain, which is exactly what the acceptance arm grades.

    Each record gets a distinct x so no two are coincident, and every record
    carries the instance-name and path markers the refusal arms hunt for.

    Returns:
        One record per allowlisted class, in sorted class-name order.
    """
    return tuple(
        actor(class_name, (float(index), 0.0, 0.0))
        for index, class_name in enumerate(sorted(footprint.CATEGORY_OF_CLASS))
    )


def codes(model: footprint.WorldFootprint) -> dict[str, int]:
    """Index a model's warnings by code.

    Args:
        model: The computed footprint model.

    Returns:
        Code to occurrence count.
    """
    return {warning.code: warning.count for warning in model.warnings}


def test_every_published_category_is_reachable_from_a_synthetic_world() -> None:
    """The served category set EQUALS the set the model itself declares.

    THE CATEGORY SET IS THE CONTRACT. The map draws each category as its own
    visual class, so a category the model advertises and can never serve is a
    legend entry for a layer that does not exist - and a category served but not
    declared is a layer no consumer knows to draw. Both are set inequalities and
    neither is visible from a count.

    The expectation is read off ``categories_declared`` on the returned model,
    never from a list retyped in this file, because a retyped list is a test
    that asserts the author can copy.

    The per-category counts are then asserted ONE CATEGORY AT A TIME. A total
    over the pool is decided by ``foundation`` alone and would leave
    ``awesome_sink``, with two classes against two hundred and thirty one,
    entirely unmeasured.
    """
    model = footprint.footprint_of(world(one_record_per_allowlisted_class()))

    served = {placed.category for placed in model.footprints}
    declared = set(model.categories_declared)
    assert served == declared

    expected_per_category = Counter(footprint.CATEGORY_OF_CLASS.values())
    per_category = {
        category: model.category_counts.get(category, 0) for category in model.categories_declared
    }
    wrong = {
        category: count
        for category, count in per_category.items()
        if count != expected_per_category[category]
    }
    assert wrong == {}


def test_a_skipped_class_is_counted_and_never_silently_dropped() -> None:
    """An uncategorised buildable moves the skip count, in both halves.

    NON-NEGOTIABLE 7. A view that filters in silence renders a fraction of a
    factory and says nothing about the remainder, which is the silently-wrong
    half of "flagged and skipped" wearing a filter. The count is the difference
    between a view that is filtered and a view that is wrong.

    The control is the SAME world with the two unlisted records removed: without
    it, a model that reported a constant would pass this arm.
    """
    listed = actor("Build_ConveyorBeltMk1_C", (0.0, 0.0, 0.0))
    control = footprint.footprint_of(world((listed,)))
    assert control.skipped_class_count == 0
    assert footprint.WARN_FOOTPRINT_CLASS_NOT_CATEGORISED not in codes(control)

    model = footprint.footprint_of(
        world(
            (
                listed,
                actor(UNLISTED_BUILDABLE, (1.0, 0.0, 0.0)),
                actor(UNMEASURED_CONVEYOR_LOOKALIKE, (2.0, 0.0, 0.0)),
            )
        )
    )
    assert model.skipped_class_count == EXPECTED_SKIPPED
    assert codes(model)[footprint.WARN_FOOTPRINT_CLASS_NOT_CATEGORISED] == EXPECTED_SKIPPED


def test_a_lookalike_spelling_is_skipped_rather_than_matched_by_substring() -> None:
    """A plausible unmeasured spelling is NOT categorised by the word in it.

    A SUBSTRING RULE IS A DENYLIST WEARING A DISGUISE. "If the name contains
    Conveyor it is a conveyor" is a claim about every name that does not exist
    yet, and this project has measured one defect wearing four different
    spellings across four green commits before an allowlist of good values held
    it. The lookalike below shares every character of a real belt but its mark
    number, so a substring rule plots it and an allowlist counts it.
    """
    model = footprint.footprint_of(world((actor(UNMEASURED_CONVEYOR_LOOKALIKE, (0.0, 0.0, 0.0)),)))

    assert model.footprints == ()
    assert model.skipped_class_count == 1


def test_an_extent_is_published_from_scale_and_withheld_when_it_is_not_derivable() -> None:
    """The extent flag is False whenever the scale did not survive, never absent.

    NEVER INVENT AN EXTENT. The model carries the per-axis scale it read and
    nothing more; where the stored scale holds a non-finite component the block
    is withheld WHOLE and the flag says so, so a consumer branches on a declared
    capability instead of sniffing a row for a null and guessing what it meant.
    """
    derivable, withheld = footprint.footprint_of(
        world(
            (
                actor("Build_ConveyorBeltMk1_C", (0.0, 0.0, 0.0), scale=PLANTED_SCALE),
                actor(
                    "Build_ConveyorBeltMk2_C",
                    (1.0, 0.0, 0.0),
                    scale=(1.0, math.inf, 1.0),
                ),
            )
        )
    ).footprints

    assert derivable.extent_available is True
    assert derivable.extent is not None
    assert (derivable.extent.x, derivable.extent.y, derivable.extent.z) == ("2.0", "0.5", "-1.5")

    assert withheld.extent_available is False
    assert withheld.extent is None


def test_an_extent_is_a_multiple_and_the_model_refuses_to_call_it_a_size() -> None:
    """No absolute footprint size is claimed, and the model says so itself.

    A SCALE IS A MULTIPLIER OF A BASE MESH THIS PROJECT HAS NEVER MEASURED. The
    base extent lives in the shipped assets and no path in this layer reads
    them, so publishing a scale as though it were centimetres would be wrong by
    a factor nothing in the numbers reveals - the exact failure
    ``COORDINATE_UNITS`` exists to prevent one model over.
    """
    model = footprint.footprint_of(world((actor("Build_MinerMk1_C", (0.0, 0.0, 0.0)),)))

    assert model.absolute_extent_available is False
    assert model.extent_units == footprint.EXTENT_UNITS
    assert footprint.WARN_FOOTPRINT_ABSOLUTE_EXTENT_UNAVAILABLE in codes(model)


def test_water_regions_are_declared_unavailable_rather_than_implied_from_pumps() -> None:
    """The water flag is False and is accompanied by the reason it is False.

    ADR 0019 MEASURED WATER VOLUME GEOMETRY AS LEVEL DATA WITH ZERO PATHS IN A
    SAVE. Publishing the built pumps as "water coverage" would imply that every
    unmarked shoreline is unusable, which is a confident wrong answer rather
    than a missing one - the silently-wrong half of non-negotiable 7. The flag
    is the honest answer and the warning is why.
    """
    model = footprint.footprint_of(world((actor("Build_WaterPump_C", (0.0, 0.0, 0.0)),)))

    assert model.water_regions_available is False
    assert footprint.WARN_FOOTPRINT_WATER_REGIONS_UNAVAILABLE in codes(model)


def test_overlapping_footprints_carry_a_total_elevation_order() -> None:
    """Every footprint gets an ascending rank, so layers draw instead of merging.

    THE REQUIREMENT IS READABILITY, NOT GEOMETRY. Three footprints sharing one
    ground position and differing only in elevation must come back as three
    layers a painter can order; without a rank a consumer must sort on a string
    it was handed and reintroduce the float this layer refuses to publish.
    """
    records = tuple(
        actor("Build_Foundation_Metal_8x1_C", (0.0, 0.0, elevation))
        for elevation in PLANTED_ELEVATIONS
    )
    model = footprint.footprint_of(world(records))

    assert model.elevation_ordering_available is True
    assert tuple(placed.elevation_order for placed in model.footprints) == (
        EXPECTED_ELEVATION_ORDER
    )
    assert tuple(placed.z for placed in model.by_elevation) == ("100.0", "200.0", "300.0")


def test_an_elevation_is_declared_as_a_world_coordinate_and_not_as_a_storey() -> None:
    """The model names what z is, so nobody reads a rank as a floor number.

    WHAT THIS DATA CARRIES IS THE TRANSFORM ORIGIN'S VERTICAL COORDINATE. It is
    not a storey index, not the building's underside and not its height, and
    where the origin sits inside a mesh is unmeasured - so two classes at equal
    z are not necessarily standing on the same floor. A consumer told only
    "elevation" would draw exactly that claim.
    """
    model = footprint.footprint_of(world((actor("Build_MinerMk1_C", (0.0, 0.0, 0.0)),)))

    assert model.elevation_meaning == footprint.ELEVATION_MEANING
    assert model.coordinate_units == footprint.COORDINATE_UNITS


def test_a_record_with_no_transform_is_skipped_rather_than_placed_at_an_invented_origin() -> None:
    """An allowlisted class with no transform never becomes a footprint at zero.

    A DEFAULTED ORIGIN IS A CONFIDENT WRONG ANSWER. A building drawn at the
    world origin because its transform did not read is indistinguishable, on the
    map, from a building that is genuinely there.
    """
    model = footprint.footprint_of(world((actor("Build_MinerMk1_C", None),)))

    assert model.footprints == ()
    assert codes(model)[footprint.WARN_FOOTPRINT_TRANSFORM_ABSENT] == 1


def test_a_non_finite_coordinate_is_refused_rather_than_published() -> None:
    """One infinite coordinate removes the footprint and raises its own code.

    ``repr(float("inf"))`` is ``'inf'``, which is not a decimal string any
    consumer can parse as a position, and one such value poisons every extent
    computed beside it.
    """
    model = footprint.footprint_of(world((actor("Build_MinerMk1_C", (0.0, math.nan, 0.0)),)))

    assert model.footprints == ()
    assert codes(model)[footprint.WARN_FOOTPRINT_COORDINATE_NON_FINITE] == 1


def test_no_float_and_no_authored_string_reaches_the_published_model() -> None:
    """Graded STRUCTURALLY, with the input fixture as the control.

    An assertion naming the fields that are safe today passes unchanged the day
    a field is added, so the walk covers everything reachable from the returned
    model. The control proves the walk can SEE a float and a marker when one is
    there - without it a walk that returned nothing would pass.
    """
    records = one_record_per_allowlisted_class()
    model = footprint.footprint_of(world(records))

    control = reachable(records)
    assert any(isinstance(value, float) for value in control)
    assert INSTANCE_NAME_MARKER in control
    assert PATH_MARKER in control
    assert BODY_OFFSET_MARKER in control

    walked = reachable(model)
    assert [value for value in walked if isinstance(value, float)] == []
    assert INSTANCE_NAME_MARKER not in walked
    assert PATH_MARKER not in walked
    assert BODY_OFFSET_MARKER not in walked
    assert BODY_LENGTH_MARKER not in walked
    assert SYNTHETIC_TOKEN not in walked
    assert [value for value in walked if isinstance(value, Path)] == []


def test_an_empty_world_says_so_rather_than_returning_a_silent_empty_model() -> None:
    """Nothing built is indistinguishable from nothing plotted unless it is said.

    A model that answers an empty tuple and raises no flag cannot be told apart
    from one whose every record was refused, which is the whole of
    non-negotiable 7's second clause.
    """
    model = footprint.footprint_of(world())

    assert model.footprints == ()
    assert model.skipped_class_count == 0
    assert footprint.WARN_FOOTPRINT_NOTHING_PLOTTED in codes(model)


def test_a_namespaced_mod_path_reduces_to_the_bare_class_name_before_matching() -> None:
    """An allowlisted class survives being spelled as a full asset path.

    A record's ``type_path`` is namespaced in a real save, so a matcher keyed on
    the raw path would admit nothing at all and a world would render empty with
    every class counted as skipped. The reduction is the save layer's own rule,
    imported rather than rewritten.
    """
    model = footprint.footprint_of(
        world(
            (actor("/Game/FactoryGame/Buildable/Build_MinerMk1.Build_MinerMk1_C", (0.0, 0.0, 0.0)),)
        )
    )

    assert tuple(placed.class_name for placed in model.footprints) == ("Build_MinerMk1_C",)
    assert model.skipped_class_count == 0


def test_every_declared_category_has_at_least_one_measured_class_behind_it() -> None:
    """No category is advertised with nothing wired to it, checked one at a time.

    THE ALLOWLIST AND THE DECLARED SET ARE TWO HALVES OF ONE CONTRACT and this
    arm grades the halves against each other WITHOUT building a world at all, so
    a category wired to nothing fails here even if a future change stops
    ``footprint_of`` from ever being reached.
    """
    behind = Counter(footprint.CATEGORY_OF_CLASS.values())
    empty = [category for category in footprint.FOOTPRINT_CATEGORIES if behind[category] == 0]
    assert empty == []

    undeclared = sorted(set(behind) - set(footprint.FOOTPRINT_CATEGORIES))
    assert undeclared == []


def test_a_non_coal_generator_is_drawn_and_never_falls_into_the_skip_bucket() -> None:
    """Every power SOURCE gets a layer, and coal keeps its own one.

    ADJUDICATED, session 85. The first cut of this module left every generator
    but the coal plant uncategorised, and a power view that silently omits a
    power source is the non-negotiable-7 failure - the count said how much was
    missing but not that what was missing generates megawatts. So each spelling
    below is asserted INDIVIDUALLY: a pooled check is satisfied by whichever
    generator happens to be listed while the rest go unmeasured, which is the
    exact shape of the defect this arm replaces.

    ``coal_plant`` is asserted to stay its OWN category in the same breath. The
    operator named it because that is the tier they are at, and a repair that
    merged it into ``generator`` would discharge this arm by erasing the thing
    the map was asked to show.
    """
    assert (
        "Build_GeneratorCoal_C" not in footprint.CLASSES_BY_CATEGORY[footprint.CATEGORY_GENERATOR]
    )

    misfiled = {
        class_name: footprint.CATEGORY_OF_CLASS.get(class_name)
        for class_name in MEASURED_NON_COAL_GENERATORS
        if footprint.CATEGORY_OF_CLASS.get(class_name) != footprint.CATEGORY_GENERATOR
    }
    assert misfiled == {}

    skipped = {}
    for class_name in [*MEASURED_NON_COAL_GENERATORS, "Build_GeneratorCoal_C"]:
        model = footprint.footprint_of(world((actor(class_name, (0.0, 0.0, 0.0)),)))
        if model.skipped_class_count or not model.footprints:
            skipped[class_name] = model.skipped_class_count
    assert skipped == {}

    coal = footprint.footprint_of(world((actor("Build_GeneratorCoal_C", (0.0, 0.0, 0.0)),)))
    assert coal.footprints[0].category == footprint.CATEGORY_COAL_PLANT


def test_a_power_store_is_not_filed_as_a_generator() -> None:
    """A battery does not produce, so it is not drawn in the producing layer.

    THE RULING WAS "EVERY POWER SOURCE", NOT "EVERY POWER BUILDING". A store and
    a switch both carry power in their class name and neither generates any, so
    a repair that reached for the word rather than the measured spelling would
    inflate a megawatt figure a reader takes off the map. That repair is exactly
    the substring rule this module refuses, aimed at the new category.
    """
    model = footprint.footprint_of(world((actor("Build_PowerStorageMk1_C", (0.0, 0.0, 0.0)),)))

    assert model.footprints == ()
    assert model.skipped_class_count == 1


def test_no_class_is_filed_under_two_categories() -> None:
    """A spelling in two categories collapses into one and takes a count with it.

    ``CATEGORY_OF_CLASS`` is a flattening, so a class named twice silently loses
    whichever category was flattened first - and BOTH the acceptance arm's
    expectation and its measurement are derived from that same flattening, so
    the collision cancels itself out of every other arm in this file. It is
    therefore graded here against the UNFLATTENED mapping, which is the only
    place the duplicate is still visible.
    """
    members = [
        class_name
        for category in footprint.FOOTPRINT_CATEGORIES
        for class_name in footprint.CLASSES_BY_CATEGORY[category]
    ]
    duplicated = sorted({name for name in members if members.count(name) > 1})
    assert duplicated == []
    assert len(footprint.CATEGORY_OF_CLASS) == len(members)
