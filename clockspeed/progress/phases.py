"""CS-1043 - what one space-elevator phase COSTS, read from a table handed in.

WHAT THIS MODULE OWNS
-----------------------
One pure function over a phase asset path and a cost table, returning a frozen
:class:`PhaseCost`: one entry per item the phase requires, keyed by the SHIPPED
item key, plus the warnings the read raised. It opens no save, no docs file and
no install. It computes no rate and declares no budget - the milestone half of
this item owns the completion budget and the rate arithmetic, and nothing here
imports it or restates it. No value in this module is a rate, so no
``Fraction`` appears in it either.

THE COST TABLE ARRIVES AS AN ARGUMENT BECAUSE NOTHING SHIPS ONE
------------------------------------------------------------------
``clockspeed.save.world`` publishes ``UnlockState.current_game_phase`` - the
ASSET PATH of the phase a world is in, a string and not an index - and
publishes nothing at all about what that phase costs. The absent producer is
measured and named rather than left as a shrug: the carrier is
``mGamePhaseCosts`` on ``BP_GamePhaseManager_C``, an ``ArrayProperty`` whose
elements are ``PhaseCost`` structs carrying ``gamePhase`` and a ``cost`` array
of ``ItemAmount``, and
``docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md`` records that
grammar from a reading of real worlds. No module in this project reads that
carrier, so THE FOLLOW-UP IS THAT READER, and this module is written to be
wired to it with no change to its own shape.

A PROTOCOL FOR THE TABLE IS DELIBERATELY NOT DECLARED. A seam with no
implementer is a seam nobody can grade, and a reader arriving later would be
free to satisfy it by accident rather than by design. The table is a plain
mapping argument until something real produces one.

WHAT IS DELIVERED IS NOT AVAILABLE TO THIS LAYER, AND THE REASON IS THE SEAM
-------------------------------------------------------------------------------
Items already handed to the space elevator sit in its input inventory, and the
per-building item totals that would answer "how much is already in" are
published by ``clockspeed/audit/inventory.py``. THAT IS NOT A LAYER THIS
PACKAGE MAY READ. ``clockspeed/progress/__init__.py`` names the layers below
this one as ``clockspeed.save.world``, ``clockspeed.data`` and
``clockspeed.solve``; ``clockspeed.audit`` is not among them, and a layer that
reaches past its neighbour is a design bug (CLAUDE.md section 2.1). So every
entry's delivered count is None today and :attr:`PhaseCost.delivered_available`
is DERIVED from the entries rather than stored. A stored False is a claim
nothing can redden; a derived one reads False while no entry carries a count
and turns True the first time a sanctioned route to that count exists, with no
edit here.

A DUPLICATED ITEM KEY KEEPS THE FIRST AMOUNT AND IS FLAGGED
--------------------------------------------------------------
:attr:`PhaseCost.required_by_item` is keyed by ``ItemAmount.item_key`` - the
shipped key rule, never a local re-derivation of it - and two paths under
different directories can share a trailing token. SUMMING THEM IS NOT THE
CHOICE MADE HERE: no reader in this project has ever read a real cost table, so
whether the game writes a repeated item as two rows meaning a total or as a
re-declaration is unmeasured, and a sum would be an arithmetic invented to
cover that gap. The mapping keeps the FIRST amount,
:data:`WARN_PHASE_COST_ITEM_DUPLICATED` is raised, and
:attr:`PhaseCost.entries` keeps BOTH entries whole - so a consumer that later
measures the grammar can do its own arithmetic over the entries without this
module having guessed on its behalf, and the flag is what stops the shortened
mapping from reading as the whole truth.

AN UNMODELLED ELEMENT IS FLAGGED AND SKIPPED, NEVER FATAL
------------------------------------------------------------
Non-negotiable 7. The element type of the table is annotated ``object`` rather
than ``ItemAmount``, and that is load-bearing rather than loose: under the
stricter annotation the type checker proves the refusal branch unreachable and
``warn_unreachable`` deletes the only code path standing between a wrong
element and a crash. There is no shipped producer to make the stricter promise
true, so the check is live code and the annotation says so out loud.

THE ARMS
----------
``tests/progress/test_phases.py::test_a_phase_cost_renders_machine_miner_and_resource_as_distinct_keys``
``tests/progress/test_phases.py::test_a_phase_with_no_cost_entry_is_null_rather_than_zero``
``tests/progress/test_phases.py::test_the_delivery_flag_is_derived_from_the_entries_rather_than_written``
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.data.blobs import ItemAmount
from clockspeed.save.world import WorldWarning

if TYPE_CHECKING:  # pragma: no cover - import-time typing only
    from collections.abc import Mapping, Sequence

__all__ = [
    "SOURCE_PHASES",
    "WARN_PHASE_COST_ITEM_DUPLICATED",
    "WARN_PHASE_COST_ITEM_UNREADABLE",
    "PhaseCost",
    "PhaseCostEntry",
    "phase_cost_of",
]

#: Which layer noticed a warning raised here, for ``WorldWarning.source``.
SOURCE_PHASES: Final = "phases"

#: This many elements of the cost sequence were not an item amount this module
#: can read, so they were skipped. Flagged rather than dropped: a cost whose
#: entries are short and whose warnings are empty is indistinguishable from a
#: phase that genuinely requires less, and those are different facts.
WARN_PHASE_COST_ITEM_UNREADABLE: Final = "phase-cost-item-unreadable"

#: This many entries repeated an item key an earlier entry already claimed.
#: Separate from the code above because an element nothing could read and an
#: element read perfectly well whose key collided are different facts, and one
#: code would make them indistinguishable - the collapse
#: ``clockspeed/audit/network.py`` refuses between its own two empty-join
#: reasons, one layer over.
WARN_PHASE_COST_ITEM_DUPLICATED: Final = "phase-cost-item-duplicated"

#: One fixed line per warning code raised here. Keyed rather than formatted, so
#: a detail can never be built from something read out of a save - the idiom
#: ``clockspeed/save/world.py`` established for the same reason.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_PHASE_COST_ITEM_UNREADABLE: (
            "this many elements of the phase cost sequence were not an item amount this"
            " reader models, so each was skipped and the required amounts below are short"
            " by whatever they named; an unmodelled element is flagged and carried, never"
            " fatal and never silently absent"
        ),
        WARN_PHASE_COST_ITEM_DUPLICATED: (
            "this many cost entries repeated an item key an earlier entry already claimed;"
            " the per-item mapping keeps the FIRST amount because no reader in this project"
            " has measured whether the game means a total or a re-declaration, and the"
            " entries themselves are published whole so a consumer can decide for itself"
        ),
    }
)


def _warning(code: str, count: int) -> WorldWarning:
    """Build one warning raised by this module.

    Args:
        code: One of the ``WARN_PHASE_COST_*`` constants.
        count: How many occurrences this aggregates.

    Returns:
        The warning, carrying the fixed detail registered for ``code``.
    """
    return WorldWarning(
        source=SOURCE_PHASES,
        code=code,
        detail=_WARNING_DETAIL[code],
        count=count,
    )


@dataclass(frozen=True)
class PhaseCostEntry:
    """One item a phase requires, and how much of it is already in.

    Frozen because an entry is a reading of a table handed in, not a working
    value. ``raw_path`` is withheld from the rendering: it is an asset path, and
    an asset path may cross this seam and may not reach a repr, a log line or an
    exception (non-negotiable 12). It is kept whole anyway, on the terms
    ``clockspeed/data/blobs.py`` ``ItemAmount`` keeps its own - it is the only
    evidence available if ``item_key`` ever fails to resolve.

    Attributes:
        item_key: The shipped item key, read straight off
            ``ItemAmount.item_key`` and never re-derived here.
        raw_path: The full item path exactly as the table carried it.
        required: The amount the phase requires, verbatim from the table and
            never unit converted - units are not knowable at this seam.
        delivered: How much is already in, or None when that count was never
            available. ALWAYS None today, and honestly so: the count lives in
            the space elevator's input inventory, which the module docstring
            records as a layer this one may not read.
    """

    item_key: str
    raw_path: str = field(repr=False)
    required: int
    delivered: int | None = None


@dataclass(frozen=True, repr=False)
class PhaseCost:
    """What one phase costs, as this layer can honestly state it.

    ``repr`` IS HAND WRITTEN AND RENDERS COUNTS ONLY. ``phase`` is an asset path
    and so is every entry's ``raw_path``, and a test runner reprs a value before
    a human chooses what to print, so neither may appear (non-negotiables 11 and
    12). The phase is withheld ENTIRELY rather than rendered as a presence flag:
    one of these exists only for a phase the table named, so its presence is
    already implied by the object existing at all and a flag would add a field
    that can never read False.

    Attributes:
        phase: The phase asset path this cost is for, as
            ``UnlockState.current_game_phase`` publishes it.
        entries: One entry per readable element of the cost sequence, in source
            order, INCLUDING entries whose item key a sibling already claimed.
        warnings: What the read flagged and carried.
    """

    phase: str = field(repr=False)
    entries: tuple[PhaseCostEntry, ...] = field(repr=False)
    warnings: tuple[WorldWarning, ...]

    @property
    def delivered_available(self) -> bool:
        """Whether any entry carries a delivered count.

        DERIVED AND NEVER STORED, which is the whole of this property. A stored
        False would read correctly today and could not be reddened by any
        change - the unreddenable vacuity shape - while this reads False
        exactly while no entry carries a count and turns True the moment one
        does, with no edit to this module.

        Returns:
            True when at least one entry's delivered count is present. A count
            of zero IS present, so presence is tested and never truthiness.
        """
        return any(entry.delivered is not None for entry in self.entries)

    @property
    def required_by_item(self) -> Mapping[str, int]:
        """The required amount per item key, first amount winning a collision.

        Keyed by the shipped ``ItemAmount.item_key``. On a repeated key the
        FIRST amount is kept and :data:`WARN_PHASE_COST_ITEM_DUPLICATED` sits
        in :attr:`warnings` - the module docstring records why that is not a
        sum - and :attr:`entries` still carries every entry, so nothing is lost
        by this mapping being the short view.

        Returns:
            A read-only mapping from item key to required amount.
        """
        required: dict[str, int] = {}
        for entry in self.entries:
            required.setdefault(entry.item_key, entry.required)
        return MappingProxyType(required)

    def __repr__(self) -> str:
        """Render counts only, and withhold every asset path.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(entries={len(self.entries)}, warnings={len(self.warnings)})"


def phase_cost_of(phase: str | None, costs: Mapping[str, Sequence[object]]) -> PhaseCost | None:
    """What one phase costs, or None when the table names no cost for it.

    NULL IS NOT ZERO, AND THE TWO ANSWERS ARE BOTH REAL. A phase the table does
    not name is None - this reader has nothing to say about it. A phase the
    table DOES name, with an empty cost sequence, is a :class:`PhaseCost`
    carrying no entry - the table says it costs nothing. Collapsing the first
    into a zero-valued cost would publish a confident answer about a phase
    nothing was ever read for.

    Args:
        phase: The phase asset path, as ``UnlockState.current_game_phase``
            publishes it, or None when no carrier named one.
        costs: The cost table, keyed by phase asset path. The element type is
            annotated ``object`` on purpose - see the module docstring.

    Returns:
        The cost of ``phase``, or None when ``phase`` is not a key of ``costs``,
        which includes ``phase`` being None.
    """
    if phase is None or phase not in costs:
        return None

    entries: list[PhaseCostEntry] = []
    claimed: set[str] = set()
    unreadable = 0
    duplicated = 0
    for element in costs[phase]:
        if not isinstance(element, ItemAmount):
            unreadable += 1
            continue
        if element.item_key in claimed:
            duplicated += 1
        claimed.add(element.item_key)
        entries.append(
            PhaseCostEntry(
                item_key=element.item_key,
                raw_path=element.raw_path,
                required=element.amount,
            )
        )

    warnings: list[WorldWarning] = []
    if unreadable > 0:
        warnings.append(_warning(WARN_PHASE_COST_ITEM_UNREADABLE, unreadable))
    if duplicated > 0:
        warnings.append(_warning(WARN_PHASE_COST_ITEM_DUPLICATED, duplicated))
    return PhaseCost(phase=phase, entries=tuple(entries), warnings=tuple(warnings))
