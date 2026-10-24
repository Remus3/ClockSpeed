"""CS-1240: unmodelled content keyed by a STABLE id, and the save it was first read in.

THE CLAIM. :mod:`clockspeed.save.sightings` keys every unmodelled class by
:func:`~clockspeed.save.sightings.stable_id` - the class path exactly as the
save names it, namespaced by its mount root and never reduced, folded, renamed
by a display name, or tied to the record index or the save it came from - and
remembers, per world, which of the distinct saves read so far first carried
it. The same content read from two saves, or against two property maps, keys
to the same id; two spellings are two ids, never one guessed from the other.

THE FIRST-SEEN SCOPE IS ONE PROCESS (the CS-1240 adjudication, session 151).
The history is an immutable value a caller holds and grows with
:func:`~clockspeed.save.sightings.observe`; an empty history is a restart. A
save is "read" when it is observed, so "first seen" means FIRST READ: a save
written while nothing was reading is never counted.

Every class path, token and number here is invented, every save is built by
``tests.save.synthetic`` and loaded through the real loader with an explicit
property map - ``None`` would resolve the installed one, and this suite must
pass on a machine that has never had the game.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Final

from clockspeed.save import sightings, usmap, world
from clockspeed.save.objects import REASON_CLASS_NOT_MODELLED
from tests.save import synthetic

#: The one class every property map below models.
MODELLED_NAME: Final = "Build_SightModelled_C"
MODELLED_PATH: Final = f"/Game/Sight/{MODELLED_NAME[:-2]}.{MODELLED_NAME}"

#: A second modelled class, carried by one property map only.
EXTRA_NAME: Final = "Build_SightExtra_C"

#: The class no property map models - the fixture's one unknown class.
UNKNOWN_X: Final = "/SightMod/Parts/Build_SightX.Build_SightX_C"

#: A second unknown class, carried by the second save only.
UNKNOWN_Y: Final = "/SightMod/Parts/Build_SightY.Build_SightY_C"

#: A class path whose final segment differs from :data:`MODELLED_NAME` by case
#: alone. A case fold would resolve it; nothing may.
CASE_NEAR_MISS: Final = "/Game/Sight/Build_Sightmodelled.Build_Sightmodelled_C"

#: Two save stamps, so the two synthetic saves are two saves.
FIRST_TICKS: Final = 638_000_000_000_000_001
SECOND_TICKS: Final = 638_000_000_000_000_002


def property_map(*names: str) -> usmap.PropertyMap:
    """A mapping that models exactly ``names``, built in memory.

    Args:
        *names: The class names it models.

    Returns:
        The mapping.
    """
    return usmap.PropertyMap(
        names=names,
        enums={},
        schemas={name: usmap.Schema(name=name, super_name=None, properties=()) for name in names},
        warnings=(),
        container=usmap.UsmapContainer(
            magic=usmap.USMAP_MAGIC,
            version=0,
            compression_method=usmap.COMPRESSION_NONE,
            compressed_size=0,
            decompressed_size=0,
            header_size=0,
        ),
        body_consumed=0,
    )


def load(
    paths: tuple[str, ...],
    *,
    ticks: int,
    token: str = synthetic.SYNTHETIC_WORLD_TOKEN,
    mapping: usmap.PropertyMap | None = None,
) -> world.WorldModel:
    """Build a flat synthetic save carrying ``paths`` and load it for real.

    Args:
        paths: One record per entry, in file order.
        ticks: The header's save stamp.
        token: The world token.
        mapping: The property map, defaulting to one modelling
            :data:`MODELLED_NAME` only.

    Returns:
        The loaded world.
    """
    blob = synthetic.build_save(
        header_kwargs={"datetime_ticks": ticks, "world_token": token},
        objects=tuple(
            synthetic.SyntheticObject(path, "Persistent_Level", f"Persistent_Level.Thing_{index}")
            for index, path in enumerate(paths)
        ),
    )
    return world.load_world_from_bytes(
        blob,
        property_map=mapping if mapping is not None else property_map(MODELLED_NAME),
        body_layout=world.BODY_LAYOUT_FLAT,
    )


def first_save() -> world.WorldModel:
    """Save 1: the modelled class, then X once."""
    return load((MODELLED_PATH, UNKNOWN_X), ticks=FIRST_TICKS)


def second_save() -> world.WorldModel:
    """Save 2: Y once, the modelled class, then X twice at later indexes."""
    return load((UNKNOWN_Y, MODELLED_PATH, UNKNOWN_X, UNKNOWN_X), ticks=SECOND_TICKS)


def rows(report: sightings.SightingReport) -> tuple[tuple[str, int, int], ...]:
    """Each sighting as ``(stable id, count, first seen)``, in report order.

    Args:
        report: The report.

    Returns:
        Plain tuples.
    """
    return tuple((entry.stable_id, entry.count, entry.first_seen) for entry in report.sightings)


def test_the_stable_id_is_identical_across_two_saves_carrying_the_same_class() -> None:
    """The same class in two saves keys to one id, whatever its index and count."""
    one = first_save()
    two = second_save()
    index_one = next(u.first_index for u in one.objects.unknown_classes if u.type_path == UNKNOWN_X)
    index_two = next(u.first_index for u in two.objects.unknown_classes if u.type_path == UNKNOWN_X)
    # The control: the per-save facts really differ, so equal ids are not an
    # accident of two identical saves.
    assert index_one != index_two
    ids_one = {row[0] for row in rows(sightings.report(sightings.EMPTY_HISTORY, one))}
    ids_two = {row[0] for row in rows(sightings.report(sightings.EMPTY_HISTORY, two))}
    assert sightings.stable_id(UNKNOWN_X) in ids_one
    assert sightings.stable_id(UNKNOWN_X) in ids_two
    assert sightings.stable_id(UNKNOWN_X) == UNKNOWN_X


def test_the_stable_id_is_identical_across_two_property_map_loads() -> None:
    """Two registry loads that both lack the class key it to one id."""
    narrow = load((MODELLED_PATH, UNKNOWN_X), ticks=FIRST_TICKS)
    wide = load(
        (MODELLED_PATH, UNKNOWN_X),
        ticks=FIRST_TICKS,
        mapping=property_map(MODELLED_NAME, EXTRA_NAME),
    )
    found_narrow = rows(sightings.report(sightings.EMPTY_HISTORY, narrow))
    found_wide = rows(sightings.report(sightings.EMPTY_HISTORY, wide))
    assert found_narrow == ((UNKNOWN_X, 1, 1),)
    assert found_wide == found_narrow


def test_one_unknown_class_is_flagged_skipped_and_listed_with_count_and_first_seen() -> None:
    """Acceptance 1 at the save layer: no exception, one record, its count, its save."""
    model = load((MODELLED_PATH, UNKNOWN_X, UNKNOWN_X), ticks=FIRST_TICKS)
    assert model.contains_unmodeled_content is True
    found = sightings.report(sightings.EMPTY_HISTORY, model)
    assert rows(found) == ((UNKNOWN_X, 2, 1),)
    reasons = tuple(entry.reason for entry in found.sightings)
    assert reasons == (REASON_CLASS_NOT_MODELLED,)
    assert found.checked is True
    assert (found.this_save, found.saves_read) == (1, 1)


def test_first_seen_is_the_first_save_read_that_carried_the_class() -> None:
    """X rides both saves and is first seen in save 1; Y only in save 2."""
    history = sightings.observe(sightings.EMPTY_HISTORY, first_save())
    history = sightings.observe(history, second_save())
    found = sightings.report(history, second_save())
    assert rows(found) == ((UNKNOWN_X, 2, 1), (UNKNOWN_Y, 1, 2))
    assert (found.this_save, found.saves_read) == (2, 2)


def test_the_report_on_the_first_save_still_answers_from_the_same_history() -> None:
    """A report on save 1 after save 2 was read names save 1 as this save."""
    history = sightings.observe(sightings.EMPTY_HISTORY, first_save())
    history = sightings.observe(history, second_save())
    found = sightings.report(history, first_save())
    assert rows(found) == ((UNKNOWN_X, 1, 1),)
    assert (found.this_save, found.saves_read) == (1, 2)


def test_reading_the_same_save_again_reads_no_new_save() -> None:
    """Observing one save twice - a re-read, or a copy of it - is one save read."""
    history = sightings.observe(sightings.EMPTY_HISTORY, first_save())
    history = sightings.observe(history, first_save())
    found = sightings.report(history, first_save())
    assert (found.this_save, found.saves_read) == (1, 1)


def test_a_restart_forgets_every_sighting() -> None:
    """An empty history is a restart: save 2 alone is save 1 and first sees X."""
    remembered = sightings.observe(sightings.EMPTY_HISTORY, first_save())
    remembered = sightings.observe(remembered, second_save())
    restarted = sightings.report(sightings.EMPTY_HISTORY, second_save())
    assert rows(restarted) == ((UNKNOWN_X, 2, 1), (UNKNOWN_Y, 1, 1))
    assert (restarted.this_save, restarted.saves_read) == (1, 1)
    # The control: the remembered history really did say otherwise.
    assert rows(sightings.report(remembered, second_save()))[0] == (UNKNOWN_X, 2, 1)
    assert rows(sightings.report(remembered, second_save()))[1] == (UNKNOWN_Y, 1, 2)


def test_first_seen_is_first_read_not_first_written() -> None:
    """Reading the newer save first makes it save 1, and the older one save 2."""
    history = sightings.observe(sightings.EMPTY_HISTORY, second_save())
    history = sightings.observe(history, first_save())
    found = sightings.report(history, first_save())
    assert rows(found) == ((UNKNOWN_X, 1, 1),)
    assert (found.this_save, found.saves_read) == (2, 2)


def test_two_worlds_never_share_a_sighting() -> None:
    """The history is keyed per world: another world's reads advance nothing here."""
    other = load((UNKNOWN_X,), ticks=FIRST_TICKS, token=synthetic.SYNTHETIC_WORLD_TOKEN_B)
    history = sightings.observe(sightings.EMPTY_HISTORY, other)
    history = sightings.observe(history, second_save())
    found = sightings.report(history, second_save())
    assert rows(found) == ((UNKNOWN_X, 2, 1), (UNKNOWN_Y, 1, 1))
    assert (found.this_save, found.saves_read) == (1, 1)


def test_sightings_are_ordered_by_stable_id_never_by_record_order() -> None:
    """Y comes first in the file and second in the report."""
    model = second_save()
    in_file = tuple(entry.type_path for entry in model.objects.unknown_classes)
    assert in_file == (UNKNOWN_Y, UNKNOWN_X)
    found = tuple(e.stable_id for e in sightings.report(sightings.EMPTY_HISTORY, model).sightings)
    assert found == (UNKNOWN_X, UNKNOWN_Y)


def test_no_property_map_checks_nothing_and_lists_nothing() -> None:
    """A world read with no property map claims nothing either way."""
    model = load((MODELLED_PATH,), ticks=FIRST_TICKS)
    unchecked = replace(
        model,
        warnings=(
            *model.warnings,
            world.WorldWarning(
                source=world.SOURCE_USMAP,
                code=world.WARN_NO_PROPERTY_MAP,
                detail="no property map",
            ),
        ),
    )
    found = sightings.report(sightings.EMPTY_HISTORY, unchecked)
    assert found.checked is False
    assert found.sightings == ()
    checked = sightings.report(sightings.EMPTY_HISTORY, model)
    assert checked.checked is True


def test_a_case_only_near_miss_is_flagged_and_never_resolved_by_a_fallback() -> None:
    """No normalised fallback on the ClassName join, and none on the stable id.

    The near miss differs from the modelled class by case alone. A case fold
    anywhere - in the save walk's join or in the key this module builds - would
    resolve it, or merge it with a second spelling; it is listed verbatim, and
    the two spellings of X below are two entries.
    """
    folded_x = UNKNOWN_X.lower()
    model = load((MODELLED_PATH, CASE_NEAR_MISS, UNKNOWN_X, folded_x), ticks=FIRST_TICKS)
    found = rows(sightings.report(sightings.EMPTY_HISTORY, model))
    assert found == tuple(sorted(((CASE_NEAR_MISS, 1, 1), (UNKNOWN_X, 1, 1), (folded_x, 1, 1))))
    assert sightings.stable_id(CASE_NEAR_MISS) != sightings.stable_id(MODELLED_PATH)
