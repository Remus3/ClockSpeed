"""CS-1240: ``/api/world`` lists unmodelled content by stable id, with its first-read save.

THE CLAIM. The world body carries an ``unmodelled`` object: whether the save
was checked at all, which save this is and how many distinct saves of this
world were read since the server started, and one entry per unmodelled class -
its stable id (the class path), its record count in this save, its reason and
the ordinal of the save it was first read in. The ordinals come from
:class:`clockspeed.save.sightings.SightingHistory`, held in memory by
:class:`clockspeed.surface.providers.SaveWorldProvider`, so a restart - a new
provider - forgets them, and the body says so in its ``scope`` word.

WHAT IS GRADED, through the provider's injectable ``find_saves`` and ``load``
seams: two synthetic saves loaded through the REAL loader, each served by a
ranking that names a few planted bytes in ``tmp_path`` only so the provider's
identity read has a file to stat. Every assertion is on a key, a count, an
ordinal or a synthetic class path; none renders a path.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from clockspeed.save import world
from clockspeed.surface import providers
from clockspeed.surface.api import contract
from clockspeed.surface.api import world as endpoint
from tests.save import test_sightings as fixtures

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

#: A modification time for the first planted file, and a later one for the second.
FIRST_MTIME_NS: Final = 1_700_000_000_000_000_000
SECOND_MTIME_NS: Final = 1_700_000_001_000_000_000

#: A 64-character hex digest - the shape of a world digest or a save key.
DIGEST_SHAPE: Final = re.compile(r"[0-9a-f]{64}")


class _Fixed:
    """A world provider with no history: it hands back one world."""

    def __init__(self, model: world.WorldModel) -> None:
        """Hold the world.

        Args:
            model: The world.
        """
        self._model = model

    def world(self) -> world.WorldModel | None:
        """Answer with the held world.

        Returns:
            The world.
        """
        return self._model


def plant(path: Path, mtime_ns: int) -> Path:
    """Write a few synthetic bytes and pin the modification time.

    Args:
        path: Where to write.
        mtime_ns: The modification time.

    Returns:
        The same path.
    """
    path.write_bytes(b"synthetic")
    os.utime(path, ns=(mtime_ns, mtime_ns))
    return path


def unmodelled(provider: object) -> Mapping[str, object]:
    """Ask the world endpoint once and return its ``unmodelled`` object.

    Args:
        provider: The world provider to bind.

    Returns:
        The decoded ``unmodelled`` object.
    """
    handler = endpoint.make_handler(provider)  # type: ignore[arg-type]
    response = handler({})
    assert response.http_status == contract.HTTP_OK
    body = json.loads(contract.encode(response.payload))
    found: Mapping[str, object] = body["data"]["unmodelled"]
    return found


def classes(found: Mapping[str, object]) -> list[tuple[object, ...]]:
    """Each listed class as ``(stable id, count, first seen)``.

    Args:
        found: The ``unmodelled`` object.

    Returns:
        Plain tuples, in body order.
    """
    listed = found["classes"]
    assert isinstance(listed, list)
    return [(entry["stable_id"], entry["count"], entry["first_seen"]) for entry in listed]


def two_save_provider(tmp_path: Path) -> tuple[providers.SaveWorldProvider, list[Path]]:
    """A provider over a ranking the arm moves, loading the two fixture saves.

    Args:
        tmp_path: Scratch directory.

    Returns:
        The provider, and the ranking list the arm edits in place.
    """
    older = plant(tmp_path / "first.sav", FIRST_MTIME_NS)
    newer = plant(tmp_path / "second.sav", SECOND_MTIME_NS)
    by_name = {older.name: fixtures.first_save(), newer.name: fixtures.second_save()}
    ranking = [older]
    provider = providers.SaveWorldProvider(
        find_saves=lambda _dir: tuple(ranking),
        load=lambda path: by_name[path.name],
    )
    return provider, ranking


def test_the_body_lists_one_unknown_class_with_its_count_and_first_seen_save() -> None:
    """Acceptance 1 on the wire: one record, its stable id, count, and save."""
    found = unmodelled(_Fixed(fixtures.first_save()))
    # The wire encoder sorts keys, so the shape is compared as a set.
    assert sorted(found) == sorted(endpoint.UNMODELLED_KEYS)
    assert found["scope"] == endpoint.FIRST_SEEN_SCOPE
    assert found["checked"] is True
    assert found["keyed"] is True
    assert (found["this_save"], found["saves_read"]) == (1, 1)
    assert classes(found) == [(fixtures.UNKNOWN_X, 1, 1)]
    listed = found["classes"]
    assert isinstance(listed, list)
    shapes = sorted({tuple(sorted(entry)) for entry in listed})
    assert shapes == [tuple(sorted(endpoint.UNMODELLED_CLASS_KEYS))]


def test_the_provider_remembers_the_save_each_class_was_first_read_in(tmp_path: Path) -> None:
    """X is first read in save 1 and Y in save 2, across two reads of the ranking."""
    provider, ranking = two_save_provider(tmp_path)
    first = unmodelled(provider)
    assert classes(first) == [(fixtures.UNKNOWN_X, 1, 1)]
    ranking.insert(0, tmp_path / "second.sav")
    second = unmodelled(provider)
    assert classes(second) == [(fixtures.UNKNOWN_X, 2, 1), (fixtures.UNKNOWN_Y, 1, 2)]
    assert (second["this_save"], second["saves_read"]) == (2, 2)


def test_asking_again_for_an_unchanged_save_reads_no_new_save(tmp_path: Path) -> None:
    """A repeated request on the same newest save is still one save read."""
    provider, _ranking = two_save_provider(tmp_path)
    unmodelled(provider)
    again = unmodelled(provider)
    assert (again["this_save"], again["saves_read"]) == (1, 1)


def test_a_new_provider_is_a_restart_and_forgets_every_sighting(tmp_path: Path) -> None:
    """A fresh provider over save 2 alone first reads both classes in save 1."""
    remembered, ranking = two_save_provider(tmp_path)
    unmodelled(remembered)
    ranking.insert(0, tmp_path / "second.sav")
    unmodelled(remembered)
    restarted = providers.SaveWorldProvider(
        find_saves=lambda _dir: (tmp_path / "second.sav",),
        load=lambda _path: fixtures.second_save(),
    )
    found = unmodelled(restarted)
    assert classes(found) == [(fixtures.UNKNOWN_X, 2, 1), (fixtures.UNKNOWN_Y, 1, 1)]
    assert (found["this_save"], found["saves_read"]) == (1, 1)


def test_the_unmodelled_object_names_no_save_stamp_and_no_digest(tmp_path: Path) -> None:
    """The save stamp keys the history and never crosses the wire, nor does a digest."""
    provider, ranking = two_save_provider(tmp_path)
    unmodelled(provider)
    ranking.insert(0, tmp_path / "second.sav")
    text = json.dumps(unmodelled(provider), sort_keys=True)
    stamps = sum(1 for ticks in (fixtures.FIRST_TICKS, fixtures.SECOND_TICKS) if str(ticks) in text)
    digests = len(DIGEST_SHAPE.findall(text))
    assert (stamps, digests) == (0, 0)
    planted = len(DIGEST_SHAPE.findall(text + world.world_digest("planted-control")))
    assert planted == 1


def test_a_world_with_no_property_map_is_reported_unchecked() -> None:
    """No property map: nothing listed, and the body says nothing was checked."""
    model = fixtures.first_save()
    # What the real loader builds with no property map: no class is flagged,
    # because none was checked, and the usmap stage says why.
    unchecked = replace(
        model,
        objects=replace(model.objects, unknown_classes=()),
        warnings=(
            world.WorldWarning(
                source=world.SOURCE_USMAP, code=world.WARN_NO_PROPERTY_MAP, detail="none"
            ),
        ),
    )
    found = unmodelled(_Fixed(unchecked))
    assert found["checked"] is False
    assert classes(found) == []


def test_a_save_naming_no_world_is_answered_unkeyed_with_its_ordinals_withheld() -> None:
    """No world, no count: the ordinals are null and the body says why."""
    model = fixtures.load(
        (fixtures.UNKNOWN_X,), ticks=fixtures.FIRST_TICKS, token=fixtures.NO_TOKEN
    )
    found = unmodelled(_Fixed(model))
    assert found["keyed"] is False
    assert (found["this_save"], found["saves_read"]) == (None, None)
    assert classes(found) == [(fixtures.UNKNOWN_X, 1, None)]


def test_the_provider_never_pools_two_saves_naming_no_world(tmp_path: Path) -> None:
    """Two token-less saves read in turn are never "save 2 of 2"."""
    older = plant(tmp_path / "first.sav", FIRST_MTIME_NS)
    newer = plant(tmp_path / "second.sav", SECOND_MTIME_NS)
    by_name = {
        older.name: fixtures.load(
            (fixtures.UNKNOWN_X,), ticks=fixtures.FIRST_TICKS, token=fixtures.NO_TOKEN
        ),
        newer.name: fixtures.load(
            (fixtures.UNKNOWN_Y, fixtures.UNKNOWN_X),
            ticks=fixtures.SECOND_TICKS,
            token=fixtures.NO_TOKEN,
        ),
    }
    ranking = [older]
    provider = providers.SaveWorldProvider(
        find_saves=lambda _dir: tuple(ranking),
        load=lambda path: by_name[path.name],
    )
    unmodelled(provider)
    ranking.insert(0, newer)
    second = unmodelled(provider)
    assert second["keyed"] is False
    assert (second["this_save"], second["saves_read"]) == (None, None)
    assert classes(second) == [(fixtures.UNKNOWN_X, 1, None), (fixtures.UNKNOWN_Y, 1, None)]
