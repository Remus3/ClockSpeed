"""Unmodelled content keyed by a STABLE id, and the save each id was first read in.

CS-1240. Two questions about content this project does not model, answered
over world models the save layer already built - this module reads no save,
no install and no docs file, and writes nothing.

1. WHAT IS IT? Every unmodelled class is keyed by :func:`stable_id`: the class
   path exactly as the save names it. That path is namespaced by its mount
   root - ``/Game/`` for shipped content, a mod's own root for a mod's - so two
   packages shipping one class name stay two ids (``CLAUDE.md`` section 7,
   namespaced identifiers). It is NOT a display name, which a registry load or
   a locale renames; NOT the record index, which moves on every save; and NOT
   the save it came from. The same content read from two saves, or checked
   against two property maps, keys to the same id.

2. SINCE WHEN? Per world, :class:`SightingHistory` remembers the distinct saves
   read so far, in the order they were read, and the first of them that
   carried each id. :func:`observe` grows it and :func:`report` answers from
   it. The history is an immutable value its holder replaces, so the merge is a
   pure function and an empty history is a restart.

THE SCOPE IS WHATEVER HOLDS THE HISTORY, AND IT IS ONE PROCESS (the CS-1240
adjudication, session 151). The dashboard's provider holds it in memory, so
"first seen" means the first save READ since the server started - a save
written while nothing was reading is never counted, and a restart forgets
everything. A persistent history would make a GET write; that was ruled out
and is recorded in ``docs/LEDGER.md``, not decided here.

NO FALLBACK, AND THAT IS A RULE OF THIS MODULE, NOT AN OMISSION. The id is
never case-folded, trimmed or reduced, and nothing here resolves one spelling
to another: two spellings are two ids, each flagged and listed verbatim. A
fallback would turn an unresolved class into a guessed one, which is the
"silently wrong" half of non-negotiable 7. The asset-path join in
``clockspeed/progress/milestones.py::purchase_state`` keeps its exact equality
for the same reason, and this module adds nothing to it.

PERSONAL DATA. A world is keyed by :func:`clockspeed.save.world.world_digest`,
never by its token. A save is keyed by a SHA-256 digest of what the game
stamped on it - the world digest, the header's save instant and play time -
plus the unmodelled census itself, so a copy of one save is the same save and
two saves sharing a stamp but not a census are two. Neither digest, the
instant nor the play time is ever published by :func:`report`: what leaves is
ordinals, counts, class paths and the reason the object walk recorded. Every
type here is a ``repr=False`` dataclass with no ``__repr__`` of its own, so it
renders as ``object.__repr__`` does - no field at all.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.save.world import WARN_NO_PROPERTY_MAP, world_digest

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.save.world import WorldModel

__all__ = [
    "EMPTY_HISTORY",
    "Sighting",
    "SightingHistory",
    "SightingReport",
    "observe",
    "report",
    "stable_id",
]

#: Separates the fields hashed into a save key. A class path never carries it.
_FIELD_SEPARATOR: Final = "\n"


def stable_id(type_path: str) -> str:
    """The stable id of one unmodelled class: its class path, verbatim.

    THE WHOLE DEFINITION, AND IT IS DELIBERATELY THE IDENTITY. The class path
    is the one name the save itself gives a class, it is namespaced by its
    mount root, and it does not move between saves or registry loads. Every
    alternative a reader might reach for is less stable: a display name is
    renamed by a locale or a patch, a record index moves on every save, a
    trailing class name collides across packages, and a case fold merges two
    spellings the save kept apart.

    Args:
        type_path: The class path as the object walk recorded it.

    Returns:
        The stable id.
    """
    return type_path


@dataclass(frozen=True, repr=False)
class Sighting:
    """One unmodelled class in the save reported on.

    Attributes:
        stable_id: The class's :func:`stable_id`.
        count: How many records in THIS save carried it.
        reason: The reason the object walk recorded for it, verbatim - one of
            ``clockspeed.save.objects.UNKNOWN_CLASS_REASONS``.
        first_seen: The ordinal, among the distinct saves of this world the
            history has read (1 is the first), of the first that carried it.
    """

    stable_id: str
    count: int
    reason: str
    first_seen: int


@dataclass(frozen=True, repr=False)
class SightingReport:
    """Every unmodelled class of one save, with when each was first read.

    Attributes:
        checked: Whether the save was checked against a property map at all.
            False when none was supplied, and then :attr:`sightings` is empty
            because NOTHING was checked - never because everything resolved.
        this_save: The ordinal of the save reported on.
        saves_read: How many distinct saves of this world the history has read.
        sightings: One entry per unmodelled class, ordered by stable id, so the
            order never moves with the record order of a save.
    """

    checked: bool
    this_save: int
    saves_read: int
    sightings: tuple[Sighting, ...]


@dataclass(frozen=True, repr=False)
class _WorldReads:
    """What one world's reads left behind.

    Attributes:
        saves: Each distinct save read, by its key, mapped to its ordinal.
        first_seen: Each stable id mapped to the ordinal of the first save read
            that carried it.
    """

    saves: Mapping[str, int]
    first_seen: Mapping[str, int]


@dataclass(frozen=True, repr=False)
class SightingHistory:
    """The distinct saves read so far, per world, and where each id was first read.

    Immutable: :func:`observe` returns a new history and never edits one. The
    keys are digests - see the module docstring - and are not public.

    Attributes:
        worlds: Each world's reads, keyed by its world digest.
    """

    worlds: Mapping[str, _WorldReads]


#: The history nothing has been read into - a fresh process.
EMPTY_HISTORY: Final = SightingHistory(worlds=MappingProxyType({}))


def _census(model: WorldModel) -> tuple[tuple[str, int, str], ...]:
    """The save's unmodelled classes as ``(stable id, count, reason)``, by id.

    Args:
        model: The world.

    Returns:
        The census, ordered by stable id.
    """
    return tuple(
        sorted(
            (stable_id(unknown.type_path), unknown.count, unknown.reason)
            for unknown in model.objects.unknown_classes
        )
    )


def _save_key(model: WorldModel) -> str:
    """One save's key: a digest of its own stamp and its unmodelled census.

    Args:
        model: The world.

    Returns:
        A 64-character hex digest. Never published.
    """
    header = model.header
    fields = [
        world_digest(model.token),
        str(header.datetime_ticks),
        str(header.play_duration),
    ]
    fields.extend(f"{key} {count}" for key, count, _reason in _census(model))
    return hashlib.sha256(_FIELD_SEPARATOR.join(fields).encode("utf-8")).hexdigest()


def observe(history: SightingHistory, model: WorldModel) -> SightingHistory:
    """Merge one read save into the history. Pure, and idempotent per save.

    A save already read changes nothing. A new one takes the next ordinal of
    its world, and every id it carries that this world has not seen is first
    seen in it; an id already seen keeps its earlier ordinal.

    Args:
        history: What was read before.
        model: The save just read.

    Returns:
        The history including ``model``. The same object when ``model`` was
        already read.
    """
    world = world_digest(model.token)
    reads = history.worlds.get(world)
    if reads is None:
        reads = _WorldReads(saves=MappingProxyType({}), first_seen=MappingProxyType({}))
    key = _save_key(model)
    if key in reads.saves:
        return history
    ordinal = len(reads.saves) + 1
    saves = dict(reads.saves)
    saves[key] = ordinal
    first_seen = dict(reads.first_seen)
    for sighted, _count, _reason in _census(model):
        first_seen.setdefault(sighted, ordinal)
    worlds = dict(history.worlds)
    worlds[world] = _WorldReads(
        saves=MappingProxyType(saves), first_seen=MappingProxyType(first_seen)
    )
    return SightingHistory(worlds=MappingProxyType(worlds))


def _checked(model: WorldModel) -> bool:
    """Whether the save was checked against a property map.

    Args:
        model: The world.

    Returns:
        False when the load carried ``WARN_NO_PROPERTY_MAP``.
    """
    return not any(warning.code == WARN_NO_PROPERTY_MAP for warning in model.warnings)


def report(history: SightingHistory, model: WorldModel) -> SightingReport:
    """Every unmodelled class of ``model``, keyed by stable id, with its first read.

    ``model`` is observed first, so a save the history has not read is
    answered as the next one read - the report never names a save that has no
    ordinal. Nothing is written back: the caller keeps its own history.

    Args:
        history: What was read before.
        model: The save to report on.

    Returns:
        The report.
    """
    seen = observe(history, model)
    reads = seen.worlds[world_digest(model.token)]
    return SightingReport(
        checked=_checked(model),
        this_save=reads.saves[_save_key(model)],
        saves_read=len(reads.saves),
        sightings=tuple(
            Sighting(
                stable_id=sighted,
                count=count,
                reason=reason,
                first_seen=reads.first_seen[sighted],
            )
            for sighted, count, reason in _census(model)
        ),
    )
