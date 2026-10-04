"""CS-400 clause 1 through the BUILDING PATH, on the real save library.

WHAT THE GAP WAS. The operator ruled that clause 1 ("a real world parses")
waits until a building's inventory is ACTUALLY READABLE
(``docs/item_notes/phase4.md`` under CS-400). The library half of
``tests/save/test_phase4_gate_depth.py`` sums every ``mInventoryStacks`` array
the model publishes, wherever it sits; it never walks FROM a building. The
building -> component -> stacks -> item path was proven on a synthetic fixture
only. This module is that path on every real save.

WHAT IS GRADED, PER SAVE AND NEVER POOLED.

  (a) Through ``clockspeed.audit.inventory`` on the published ``WorldModel``,
      every building's view - its carrier count, its stack count and its item
      rows by key - equals a view DERIVED HERE from the carriers attributed to
      that building and to no other actor. The derivation is this module's own
      walk over the published values, the published reference join
      (``RecordProperties.reference_targets``), the published parent join
      (``WorldModel.parents``) and the published record kind.
  (b) The four-way invariant: buildings + non-building + unattributed +
      conflict == world total, exactly, for stacks and for items alike.
  (c) The ``mInventoryStacks`` items reached from buildings plus non-building
      plus unattributed carriers equal the S4 INDEPENDENT TAG-WALK population,
      imported from ``tests/save/test_phase4_gate_depth.py`` and never
      re-derived from the decoder. "Item count" here is the number of item
      entries - the population counts ``Item`` tags, one per stack element -
      and not the sum of ``NumItems``. The stacks the audit reaches through
      those three categories equal the stacks the derivation reaches through
      the same categories, which is what ties the population to the audit.
  (d) No unattributed carrier is of the BUILDING FAMILY - a carrier whose own
      class, or whose parent path's last segment, carries the buildable prefix.
      The derived unattributed count also equals the audit's.
  (e) At least one building shows a non-empty decoded item, on every save
      whose building-family carriers hold any non-empty stack. NOT on every
      save with any non-empty stack: a fresh world measured one non-empty
      stack, the player's, and no building at all - a player's pocket is not a
      building's inventory, and requiring one there would grade the world, not
      the reader.

NO NAME, PATH OR SAVE BYTE CROSSES AN ASSERTION. Every helper that touches a
record, a key or a path returns integers; the test bodies hold integer-only
tallies; a failure renders through ``_fail_on`` with ``pytrace=False``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from functools import lru_cache
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.audit import inventory
from clockspeed.audit.placement import class_name_of_path
from clockspeed.save import chunks, header, objects, world
from tests.save.test_phase4_gate_depth import (
    _TYPE_TREE_PAIRS,
    _fail_on,
    _item_tag_population,
    _library_save_paths,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

#: The words the derivation keys on, spelled here rather than imported from the
#: module under test, so a rename there is red here instead of carried along.
_STACKS_NAME: Final = "mInventoryStacks"
_ITEM_NAME: Final = "Item"
_COUNT_NAME: Final = "NumItems"
_BUILDING_PREFIX: Final = "build_"

#: Where a derived carrier lands - private words.
_BUILDING: Final = "building"
_NON_BUILDING: Final = "non_building"
_UNATTRIBUTED: Final = "unattributed"
_CONFLICT: Final = "conflict"
_REACHED: Final = (_BUILDING, _NON_BUILDING, _UNATTRIBUTED)


# ---------------------------------------------------------------------------
# The derivation - this module's own walk over the published model
# ---------------------------------------------------------------------------


@dataclass
class _Carrier:
    """One derived carrier. PRIVATE, never bound in an asserting scope.

    Attributes:
        rows: Item key to summed count, over decoded rows. ``repr=False``: the
            keys are read out of the save.
        stacks: Structs carrying an ``Item`` or a ``NumItems`` tag.
        array_items: Elements of an ``mInventoryStacks`` array whose ``Item``
            decoded - the population's own unit.
        unread_items: Stacks whose ``Item`` is neither a decoded item nor
            absent - counted, so a form this walk does not read is visible.
    """

    rows: dict[str, int] = field(default_factory=dict, repr=False)
    stacks: int = 0
    array_items: int = 0
    unread_items: int = 0


def _fold_stack(struct: objects.StructValue, carrier: _Carrier, *, in_array: bool) -> None:
    """Fold one stack-shaped struct into a carrier.

    Args:
        struct: A struct carrying ``Item`` or ``NumItems``.
        carrier: Filled in place.
        in_array: Whether the struct is an element of an ``mInventoryStacks`` array.
    """
    carrier.stacks += 1
    item = struct.properties.get(_ITEM_NAME)
    count = struct.properties.get(_COUNT_NAME)
    if isinstance(item, objects.InventoryItem):
        carrier.array_items += int(in_array)
        if item.class_path and type(count) is int and count > 0:
            key = class_name_of_path(item.class_path)
            carrier.rows[key] = carrier.rows.get(key, 0) + count
    elif item is not None:
        carrier.unread_items += 1


def _carrier_of(named: Iterable[tuple[str, object]]) -> _Carrier:
    """Walk one record's published values into a carrier.

    ITERATIVE, on the audit's reason: the nesting depth is a property of a file
    this test did not write. A value is flagged when it sits directly under a
    property named ``mInventoryStacks``, and a container passes that flag to
    its elements.

    Args:
        named: The record's top-level ``(name, value)`` pairs.

    Returns:
        The carrier; ``stacks == 0`` means the record is not one.
    """
    carrier = _Carrier()
    work: list[tuple[object, bool]] = [(value, name == _STACKS_NAME) for name, value in named]
    while work:
        value, in_array = work.pop()
        if isinstance(value, world.ContainerContents):
            work.extend((entry.value, in_array) for entry in value.entries)
        elif isinstance(value, objects.StructValue):
            if _ITEM_NAME in value.properties or _COUNT_NAME in value.properties:
                _fold_stack(value, carrier, in_array=in_array)
            work.extend((nested, name == _STACKS_NAME) for name, nested in value.properties.items())
    return carrier


def _absorb(into: _Carrier, part: _Carrier) -> None:
    """Add one carrier's tallies into another.

    Args:
        into: Filled in place.
        part: Read only.
    """
    for key, count in part.rows.items():
        into.rows[key] = into.rows.get(key, 0) + count
    into.stacks += part.stacks
    into.array_items += part.array_items
    into.unread_items += part.unread_items


def _is_actor(model: world.WorldModel, index: int) -> bool:
    """Whether the table holds an actor at this index.

    Args:
        model: The world.
        index: A record index.

    Returns:
        The answer; False outside the table.
    """
    records = model.objects.records
    return 0 <= index < len(records) and records[index].kind == objects.KIND_ACTOR


def _names_a_building(path: str | None) -> bool:
    """Whether a path's last segment carries the buildable prefix, any case.

    Args:
        path: A class path or an object path, or None.

    Returns:
        The answer.
    """
    return bool(path) and class_name_of_path(path or "").casefold().startswith(_BUILDING_PREFIX)


def _claimants(model: world.WorldModel, carriers: Iterable[int]) -> dict[int, set[int]]:
    """Every actor naming each carrier by reference, by parent, or by being it.

    Args:
        model: The world.
        carriers: The carrier indices.

    Returns:
        Carrier index to its claimant actor indices.
    """
    claims: dict[int, set[int]] = {index: set() for index in carriers}
    for index, entry in model.properties.by_record_index.items():
        if not _is_actor(model, index) or len(entry.reference_targets) != len(entry.references):
            continue
        for target in entry.reference_targets:
            landed = target.record_index
            if target.state == world.TARGET_RESOLVED and landed in claims:
                claims[landed].add(index)
    for index, claimed in claims.items():
        parent = model.parents.by_record_index.get(index)
        landed = None if parent is None else parent.record_index
        # `record_index` is None unless the parent RESOLVED to exactly one
        # record, so an unresolved or ambiguous parent claims nothing.
        if landed is not None and _is_actor(model, landed):
            claimed.add(landed)
        if _is_actor(model, index):
            claimed.add(index)
    return claims


def _category(model: world.WorldModel, claimed: set[int]) -> str:
    """Which derived category one claimant set puts its carrier in.

    Args:
        model: The world.
        claimed: The claimants.

    Returns:
        One of the private category words.
    """
    if not claimed:
        return _UNATTRIBUTED
    if len(claimed) > 1:
        return _CONFLICT
    (owner,) = claimed
    owner_class = model.objects.records[owner].type_path
    return _BUILDING if _names_a_building(owner_class) else _NON_BUILDING


@dataclass(frozen=True)
class _SaveTally:
    """One save's verdict inputs. INTEGERS ONLY - never a name, key or path.

    Attributes:
        header_version: The pair's header half.
        save_version: The pair's save half.
        ordinal: The save's position in sorted order.
        population: The S4 tag walk's item population.
        world_stacks: The audit's world stack count.
        world_items: The audit's world item total.
        building_stacks: Stacks summed over the audit's building views.
        building_items: Items summed over the audit's building views.
        non_building_stacks: The audit's non-building stacks.
        non_building_items: The audit's non-building items.
        unattributed_stacks: The audit's unattributed stacks.
        unattributed_items: The audit's unattributed items.
        conflict_stacks: The audit's conflict stacks.
        conflict_items: The audit's conflict items.
        audit_buildings: Building views the audit published.
        derived_buildings: Building owners the derivation found.
        view_mismatches: Building positions whose audit view differs from the
            derived one, plus the length difference.
        derived_reached_stacks: Stacks in derived building, non-building and
            unattributed carriers.
        derived_array_items: ``mInventoryStacks`` items in those carriers.
        derived_unread_items: Stacks whose ``Item`` the derivation did not read.
        audit_unattributed_carriers: The audit's unattributed carrier count.
        derived_unattributed_carriers: The derivation's.
        unattributed_building_family: Derived unattributed carriers of the
            building family.
        family_nonempty_rows: Non-empty rows in building-family carriers.
        nonempty_buildings: Audit building views holding at least one item row.
    """

    header_version: int
    save_version: int
    ordinal: int
    population: int
    world_stacks: int
    world_items: int
    building_stacks: int
    building_items: int
    non_building_stacks: int
    non_building_items: int
    unattributed_stacks: int
    unattributed_items: int
    conflict_stacks: int
    conflict_items: int
    audit_buildings: int
    derived_buildings: int
    view_mismatches: int
    derived_reached_stacks: int
    derived_array_items: int
    derived_unread_items: int
    audit_unattributed_carriers: int
    derived_unattributed_carriers: int
    unattributed_building_family: int
    family_nonempty_rows: int
    nonempty_buildings: int


def _is_building_family(model: world.WorldModel, index: int) -> bool:
    """Whether a carrier's own class, or its parent path, names a building.

    Read off the record's own strings, NOT off either join, so a join that
    failed to land cannot also hide the carrier from this test.

    Args:
        model: The world.
        index: The carrier's record index.

    Returns:
        The answer.
    """
    record = model.objects.records[index]
    return _names_a_building(record.type_path) or _names_a_building(record.parent)


def _view_mismatches(
    model: world.WorldModel,
    audited: inventory.WorldInventory,
    owned: dict[int, list[int]],
    carriers: dict[int, _Carrier],
) -> int:
    """How many building views the audit and the derivation disagree on.

    Args:
        model: The world.
        audited: The audit's answer.
        owned: Derived building owner to its carriers, any order.
        carriers: Carrier index to its derived tallies.

    Returns:
        Positions that differ, plus the difference in length.
    """
    derived: list[tuple[int, int, tuple[tuple[str, int], ...], str]] = []
    for owner in sorted(owned):
        held = _Carrier()
        for index in owned[owner]:
            _absorb(held, carriers[index])
        name = class_name_of_path(model.objects.records[owner].type_path)
        derived.append((len(owned[owner]), held.stacks, tuple(sorted(held.rows.items())), name))
    published = [
        (
            view.carriers_reached,
            view.stack_count,
            tuple((row.item_key, row.count) for row in view.items),
            view.class_name,
        )
        for view in audited.buildings
    ]
    differing = sum(1 for one, two in zip(published, derived, strict=False) if one != two)
    return differing + abs(len(published) - len(derived))


def _tally_save(data: bytes, ordinal: int) -> _SaveTally:
    """Measure one whole save. NO ASSERTION: integers out, nothing else.

    Args:
        data: The save's bytes.
        ordinal: Its position in the sweep.

    Returns:
        The tally.
    """
    parsed = header.parse_header(data)
    pair = (parsed.header_version, parsed.save_version)
    body = chunks.decompress_body(
        data, parsed.body_offset, header_version=parsed.header_version
    ).payload
    population = _item_tag_population(body, type_tree=pair in _TYPE_TREE_PAIRS)
    model = world.load_world_from_bytes(data)
    audited = inventory.inventory_of(model)

    carriers: dict[int, _Carrier] = {}
    for index in sorted(model.properties.by_record_index):
        carrier = _carrier_of(model.properties.by_record_index[index].values.items())
        if carrier.stacks:
            carriers[index] = carrier
    claims = _claimants(model, carriers)
    owned: dict[int, list[int]] = {}
    by_category: dict[str, list[int]] = {word: [] for word in (*_REACHED, _CONFLICT)}
    for index in sorted(carriers):
        word = _category(model, claims[index])
        by_category[word].append(index)
        if word == _BUILDING:
            (owner,) = claims[index]
            owned.setdefault(owner, []).append(index)
    reached = [index for word in _REACHED for index in by_category[word]]
    family = [index for index in carriers if _is_building_family(model, index)]

    return _SaveTally(
        header_version=pair[0],
        save_version=pair[1],
        ordinal=ordinal,
        population=population,
        world_stacks=audited.stack_count,
        world_items=audited.total_count,
        building_stacks=sum(view.stack_count for view in audited.buildings),
        building_items=sum(row.count for view in audited.buildings for row in view.items),
        non_building_stacks=audited.non_building_stack_count,
        non_building_items=audited.non_building_item_count,
        unattributed_stacks=audited.unattributed_stack_count,
        unattributed_items=audited.unattributed_item_count,
        conflict_stacks=audited.conflict_stack_count,
        conflict_items=audited.conflict_item_count,
        audit_buildings=len(audited.buildings),
        derived_buildings=len(owned),
        view_mismatches=_view_mismatches(model, audited, owned, carriers),
        derived_reached_stacks=sum(carriers[index].stacks for index in reached),
        derived_array_items=sum(carriers[index].array_items for index in reached),
        derived_unread_items=sum(carrier.unread_items for carrier in carriers.values()),
        audit_unattributed_carriers=audited.unattributed_carrier_count,
        derived_unattributed_carriers=len(by_category[_UNATTRIBUTED]),
        unattributed_building_family=sum(
            1 for index in by_category[_UNATTRIBUTED] if _is_building_family(model, index)
        ),
        family_nonempty_rows=sum(len(carriers[index].rows) for index in family),
        nonempty_buildings=sum(1 for view in audited.buildings if view.items),
    )


# ---------------------------------------------------------------------------
# The library sweep - skip-if-absent, counts only
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Sweep:
    """What the sweep observed. INTEGERS AND TYPE NAMES ONLY.

    Attributes:
        tallies: One per loaded save, in sorted order.
        failures: The type names of any unexpected failure.
    """

    tallies: tuple[_SaveTally, ...]
    failures: tuple[str, ...]


@lru_cache(maxsize=1)
def _sweep_library() -> _Sweep | None:
    """Tally every save of a measured pair, COUNTS ONLY.

    Discovery is the S4 module's own contained helper. Every read sits inside a
    broad ``try`` so nothing unwinds through a frame holding a path.

    Returns:
        The sweep, or None when no save library is reachable.
    """
    saves = _library_save_paths()
    if not saves:
        return None
    tallies: list[_SaveTally] = []
    failures: list[str] = []
    for ordinal, path in enumerate(saves):
        try:
            data = path.read_bytes()
            parsed = header.parse_header(data)
        except (OSError, header.HeaderError):
            continue
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
        if (parsed.header_version, parsed.save_version) not in objects.MEASURED_BODY_LAYOUTS:
            continue
        try:
            tallies.append(_tally_save(data, ordinal))
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
    return _Sweep(tallies=tuple(tallies), failures=tuple(sorted(set(failures))))


def _sweep_or_skip() -> _Sweep:
    """The sweep, or a skip when this machine has no save library.

    Returns:
        The sweep.
    """
    sweep = _sweep_library()
    if sweep is None:
        pytest.skip("no save library on this machine")
    return sweep


def _rows(sweep: _Sweep, observed: str, expected: str) -> list[tuple[int, int, int, int, int]]:
    """Offending saves for one integer equality, in ``_fail_on``'s row shape.

    Args:
        sweep: The sweep.
        observed: A ``_SaveTally`` field name.
        expected: Another.

    Returns:
        ``(header, save, ordinal, observed, expected)`` per offending save.
    """
    return [
        (t.header_version, t.save_version, t.ordinal, getattr(t, observed), getattr(t, expected))
        for t in sweep.tallies
        if getattr(t, observed) != getattr(t, expected)
    ]


# ---------------------------------------------------------------------------
# The claims
# ---------------------------------------------------------------------------


def test_the_tally_type_holds_integers_only() -> None:
    """Non-negotiables 11-12: nothing a failure renders can carry a world string."""
    for kind in (_SaveTally, _Sweep):
        texty = sorted(
            one.name for one in fields(kind) if "str" in str(one.type) and one.name != "failures"
        )
        assert texty == []


def test_the_library_sweep_loads_and_reaches_buildings() -> None:
    """NON-VACUITY: saves loaded, no unexpected failure, and buildings were reached."""
    sweep = _sweep_or_skip()
    failures = len(sweep.failures)
    names = ", ".join(sweep.failures)
    if failures:
        pytest.fail(f"{failures} unexpected failure types: {names}", pytrace=False)
    loaded = len(sweep.tallies)
    assert loaded > 0, "no save of a measured pair loaded"
    reaching = sum(1 for t in sweep.tallies if t.audit_buildings > 0)
    assert reaching > 0, "no save reached a single building inventory"


def test_a_every_building_view_is_exactly_its_attributed_carriers() -> None:
    """(a) Per save: every audit building view equals the derived one, by key."""
    sweep = _sweep_or_skip()

    count = [
        (t.header_version, t.save_version, t.ordinal, t.audit_buildings, t.derived_buildings)
        for t in sweep.tallies
        if t.audit_buildings != t.derived_buildings
    ]
    views = [
        (t.header_version, t.save_version, t.ordinal, t.view_mismatches, 0)
        for t in sweep.tallies
        if t.view_mismatches
    ]
    unread = [
        (t.header_version, t.save_version, t.ordinal, t.derived_unread_items, 0)
        for t in sweep.tallies
        if t.derived_unread_items
    ]
    _fail_on(count, "audit building views equal derived building owners")
    _fail_on(views, "every building view equals its derived carriers")
    _fail_on(unread, "every Item the derivation met decoded or was absent")


def test_b_the_four_way_partition_is_exact_for_stacks_and_items() -> None:
    """(b) Per save: buildings + non-building + unattributed + conflict == world."""
    sweep = _sweep_or_skip()

    stacks = [
        (
            t.header_version,
            t.save_version,
            t.ordinal,
            t.building_stacks + t.non_building_stacks + t.unattributed_stacks + t.conflict_stacks,
            t.world_stacks,
        )
        for t in sweep.tallies
        if t.building_stacks + t.non_building_stacks + t.unattributed_stacks + t.conflict_stacks
        != t.world_stacks
    ]
    items = [
        (
            t.header_version,
            t.save_version,
            t.ordinal,
            t.building_items + t.non_building_items + t.unattributed_items + t.conflict_items,
            t.world_items,
        )
        for t in sweep.tallies
        if t.building_items + t.non_building_items + t.unattributed_items + t.conflict_items
        != t.world_items
    ]
    _fail_on(stacks, "the four stack buckets sum to the world")
    _fail_on(items, "the four item buckets sum to the world")


def test_c_items_reached_through_owners_equal_the_tag_walk_population() -> None:
    """(c) Per save: reached ``mInventoryStacks`` items == the S4 tag-walk population.

    And the stacks the audit reaches through the three non-conflict categories
    equal the stacks the derivation reaches through them, so the population is
    tied to the audit and not only to this module's walk.
    """
    sweep = _sweep_or_skip()

    population = _rows(sweep, "derived_array_items", "population")
    reached = [
        (
            t.header_version,
            t.save_version,
            t.ordinal,
            t.building_stacks + t.non_building_stacks + t.unattributed_stacks,
            t.derived_reached_stacks,
        )
        for t in sweep.tallies
        if t.building_stacks + t.non_building_stacks + t.unattributed_stacks
        != t.derived_reached_stacks
    ]
    _fail_on(population, "reached stack-array items equal the tag-walk population")
    _fail_on(reached, "audit reached stacks equal derived reached stacks")


def test_d_no_building_family_carrier_is_unattributed() -> None:
    """(d) Per save: unattributed building-family carriers == 0."""
    sweep = _sweep_or_skip()

    family = [
        (t.header_version, t.save_version, t.ordinal, t.unattributed_building_family, 0)
        for t in sweep.tallies
        if t.unattributed_building_family
    ]
    agreed = _rows(sweep, "derived_unattributed_carriers", "audit_unattributed_carriers")
    _fail_on(family, "no building-family carrier is unattributed")
    _fail_on(agreed, "derived unattributed equals audited unattributed")


def test_e_a_building_shows_a_decoded_item_wherever_one_is_held() -> None:
    """(e) Per save: building-family carriers hold a non-empty stack => a view shows one.

    The premise must hold on at least one save, or the clause grades nothing.
    """
    sweep = _sweep_or_skip()

    premised = sum(1 for t in sweep.tallies if t.family_nonempty_rows)
    assert premised > 0, "no save holds a non-empty stack in a building-family carrier"
    offenders = [
        (t.header_version, t.save_version, t.ordinal, t.nonempty_buildings, 1)
        for t in sweep.tallies
        if t.family_nonempty_rows and t.nonempty_buildings < 1
    ]
    _fail_on(offenders, "a building view shows a non-empty decoded item")
