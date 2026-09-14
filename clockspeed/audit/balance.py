"""CS-1045: the world power balance - draw over built counts, and starved machines.

WHAT THIS MODULE OWNS
-----------------------
Two pure functions and one that composes them. The first multiplies a per-class
declared draw by how many of that class are BUILT and sums exactly; the second
flags the machines that have work to do and are not doing it. Neither reads a
save, a docs file or the install. Their inputs are the models the layer below
already publishes: ``clockspeed/audit/placement.py`` ``WorldPlacement`` for the
built counts, ``clockspeed/audit/machines.py`` ``WorldMachines`` for the
producing flag, ``clockspeed/audit/network.py`` ``WorldNetwork`` for what the
topology half cannot yet answer, and ``clockspeed/solve/power.py`` for what a
building's entry declares.

THIS IS THE FIRST MODULE IN ``audit/`` TO CONSUME ``solve/``, and that is the
seam the package's own ``__init__`` docstring already declares: "Below this
layer are two stated models: the world model from clockspeed.save.world and the
results of clockspeed.solve." ``Building`` is imported for its TYPE ONLY, under
``TYPE_CHECKING``. Nothing here builds one, reads one out of ``data/``, or
touches the registry: a caller supplies the mapping, which keeps the runtime
dependency exactly one layer deep.

THE CONFIDENT ZERO IS THE FAILURE MODE THIS MODULE IS BUILT AGAINST
---------------------------------------------------------------------
Non-negotiable 7 says unknown content is flagged and skipped, never silently
wrong. A built class whose draw the registry does not model, contributing ZERO
to a world total, produces a number that LOOKS like a measurement and is not
one - and unlike a float, which ``contract.encode`` refuses outright, a zero is
accepted everywhere and detected nowhere. ``clockspeed/data/registry.py``
``Building.power_consumption`` states the same thing about its own None:
"Publishing zero for the None cases is the one unacceptable option, because a
confident zero is exactly what a power plan cannot detect."

So the answer here is a PARTITION rather than a total. Every built class lands
in exactly one of two buckets:

- :class:`DrawContribution`, which carries a count and two exact Fractions, and
  which ONLY a class with a modeled scalar draw may enter; or
- :class:`DrawGap`, which carries a count, a NAMED kind and a reason, and
  **which declares no megawatts field at all**.

THE ZERO IS THEREFORE STRUCTURALLY UNREPRESENTABLE, not merely absent today.
There is no field on a gap for a consumer to read a zero out of and no field for
a later change to default to zero, which is a stronger guarantee than an
Optional that happens to be None - an Optional is one careless ``or 0`` away
from the defect, and a missing field is a ``AttributeError``. The buckets
conserve: ``len(contributions) + len(gaps) == len(built_counts)``, asserted by
``tests/audit/test_balance.py::test_the_two_buckets_partition_the_built_classes_with_conservation``,
so a class this module dropped cannot be expressed. That is the shape
``docs/item_notes/phase5.md`` records for CS-1042 - an Optional, a flag and a
count are each individually ignorable, and a partition with conservation is not.

AND THE GAP IS NAMED PER CONTRIBUTOR, NEVER POOLED. A total that is correct in
aggregate can still hide a class whose draw was never modelled, so each gap
carries the class it is about, how many are built, and WHICH of the four ways
the draw went missing. The three registry-side kinds are
``clockspeed/solve/power.py``'s own ``SHAPE_*`` constants carried VERBATIM,
along with that module's reason line, so the vocabulary has exactly one owner
and this module cannot drift a second spelling of "the entry declares a range".

THE FOURTH AND FIFTH KINDS ARE THIS MODULE'S OWN, because they are facts about
the JOIN rather than about a declaration. :data:`GAP_NO_REGISTRY_ENTRY` is a
built class the supplied registry does not carry - modded content, or content
this project has not modelled - and it is the one case that would otherwise
vanish silently, since there is no entry to ask. :data:`GAP_DRAW_INEXACT` is a
declared scalar that is not exactly a ``Fraction``: non-negotiable 6 forbids a
float in the solve path, and the right response to one is a named gap rather
than an exception, because a single bad entry must not cost a world its whole
power answer.

WHAT IS DECLARED ABSENT RATHER THAN REPORTED AS ZERO
-------------------------------------------------------
**PRODUCTION IS NOT MODELLED ANYWHERE IN THIS PROJECT AT HEAD.**
``clockspeed/data/registry.py`` ``Building`` carries ``power_consumption`` and
no production field, and no extractor of one exists - a generator's output is
not read out of the docs file by ``clockspeed/data/docs_extract.py``. So
:attr:`WorldBalance.production_available` is False and
:data:`WARN_BALANCE_PRODUCTION_UNMODELED` says why. Publishing a production
total of zero beside a real consumption total would render every world in
permanent brownout, which is the same confident zero one field over. Inventing a
generator class list here would be worse still: a second list to keep current,
and ``clockspeed/audit/machines.py`` records why this package refuses those.

**THE CONNECTED EDGE SET IS DERIVED, NOT ASSERTED.**
:attr:`WorldBalance.connected_edges_available` is read off
``WorldNetwork.belt_topology_available`` rather than hardcoded False, so it
starts answering True on its own the day belt topology lands, and an arm can
force the input flag and watch the output follow. CS-1041 shipped that flag
false on purpose - which belt feeds which machine is one of the two questions
its own acceptance does not grade - so the red outline a panel would draw over
a starved machine's upstream segment has no edge set behind it yet, and this
module says so instead of drawing one from proximity.

WHAT "STARVED" MEANS HERE, AND WHAT IT DELIBERATELY DOES NOT
---------------------------------------------------------------
A machine is STARVED when it carries a recipe and is not producing. The two
clauses are both load-bearing and neither is decoration.

- Without the producing flag there is no finding at all, which is why
  ``tests/audit/test_balance.py::test_the_flagged_set_reddens_when_the_producing_flag_is_ignored``
  grades a fixture of two machines alike in every other field.
- Without the recipe clause an unconfigured machine - one nobody has set a
  recipe on - reads as starved, and a fresh factory full of them would bury the
  one finding that matters.

A MACHINE WHOSE PRODUCING FLAG NEVER READ IS NEVER FLAGGED AND ALWAYS COUNTED.
``MachineState.producing`` is three-state and None means this reader saw no such
tag; treating None as False would flag every machine in a world whose payloads
did not decode. It is counted in :attr:`WorldStarvation.unknown_state_count`,
and the four categories conserve against
:attr:`WorldStarvation.machines_considered` for the same reason the draw buckets
do.

A FINDING HERE IS HALF AN AUDIT AND THIS MODULE SAYS SO. The package
``__init__`` states the whole rule: "This machine is idle" is half an audit;
"this machine is idle because the segment upstream is saturated" is the whole
one. The upstream cause needs the edge set, which does not exist yet, so
:data:`WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE` travels with every balance that
has no topology behind it rather than letting a bare symptom read as a complete
finding.

A FLAGGED INDEX IS A POSITION IN A PUBLISHED POPULATION AND NOTHING ELSE. It
indexes ``WorldMachines.machines``, which ``MachineState``'s own docstring
declares the join key for exactly this purpose. It is not a record index, not a
byte offset and not a path, and it names nothing an operator built.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.save.world import WorldWarning
from clockspeed.solve.power import (
    SHAPE_RANGE_ONLY,
    SHAPE_UNDECLARED,
    SHAPE_VARIABLE,
    declared_draw,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.audit.machines import WorldMachines
    from clockspeed.audit.network import WorldNetwork
    from clockspeed.audit.placement import WorldPlacement
    from clockspeed.data.registry import Building

__all__ = [
    "GAP_DRAW_INEXACT",
    "GAP_KINDS",
    "GAP_NO_REGISTRY_ENTRY",
    "SOURCE_BALANCE",
    "WARN_BALANCE_DRAW_UNMODELED",
    "WARN_BALANCE_MACHINE_STATE_UNREAD",
    "WARN_BALANCE_NOTHING_BUILT",
    "WARN_BALANCE_PRODUCING_UNAVAILABLE",
    "WARN_BALANCE_PRODUCTION_UNMODELED",
    "WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE",
    "DrawContribution",
    "DrawGap",
    "WorldBalance",
    "WorldDraw",
    "WorldStarvation",
    "balance_of",
    "draw_of",
    "starvation_of",
]

#: Which layer noticed a warning raised here, for ``WorldWarning.source``.
SOURCE_BALANCE: Final = "balance"

#: A built class the supplied registry does not carry at all. THE ONE GAP THAT
#: HAS NO DECLARATION BEHIND IT - there is no entry to ask, so without this kind
#: the class would leave no trace anywhere in the answer.
GAP_NO_REGISTRY_ENTRY: Final = "no-registry-entry"

#: A declared scalar draw that is not exactly a ``Fraction``. Non-negotiable 6
#: forbids a float in the solve path, and a gap is the right refusal here rather
#: than an exception: one bad entry must not cost a world its power answer.
GAP_DRAW_INEXACT: Final = "draw-inexact"

#: The closed vocabulary of gap kinds. Three are ``clockspeed/solve/power.py``'s
#: own shape constants carried verbatim so that module stays their one owner;
#: two are this module's, and are facts about the join rather than about a
#: declaration. Published so a consumer can branch on a complete list.
GAP_KINDS: Final = frozenset(
    {
        SHAPE_RANGE_ONLY,
        SHAPE_VARIABLE,
        SHAPE_UNDECLARED,
        GAP_NO_REGISTRY_ENTRY,
        GAP_DRAW_INEXACT,
    }
)

#: This many BUILT ACTORS - not classes - contributed no number to the world
#: draw. The consumption total below them is a lower bound and nothing more.
WARN_BALANCE_DRAW_UNMODELED: Final = "balance-draw-unmodeled"

#: The placement model carried no built class at all, so the world draw is zero
#: because there was nothing to sum. Flagged rather than reported as a measured
#: zero: a world with nothing built and a world whose built actors were all
#: filtered out produce the identical number.
WARN_BALANCE_NOTHING_BUILT: Final = "balance-nothing-built"

#: No machine in this world carried a readable producing flag, so the empty
#: starved set means "nothing could be measured" and never "nothing is starved".
WARN_BALANCE_PRODUCING_UNAVAILABLE: Final = "balance-producing-unavailable"

#: This many machines carried no producing flag and were neither flagged nor
#: counted as running. The starved set is short by whatever they hold.
WARN_BALANCE_MACHINE_STATE_UNREAD: Final = "balance-machine-state-unread"

#: Power PRODUCTION is not modelled anywhere in this project - see the module
#: docstring. Raised on every balance, because a consumption total with no
#: production beside it is half a graph and must not read as a whole one.
WARN_BALANCE_PRODUCTION_UNMODELED: Final = "balance-production-unmodeled"

#: No belt topology, so a starved machine's upstream cause cannot be named.
#: Raised whenever the network model declares the edge set unavailable.
WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE: Final = "balance-upstream-cause-unavailable"

#: One fixed line per gap kind this module OWNS. The other three kinds carry
#: ``clockspeed/solve/power.py``'s own reason verbatim instead, so no line is
#: written twice anywhere.
_GAP_REASON: Final[Mapping[str, str]] = MappingProxyType(
    {
        GAP_NO_REGISTRY_ENTRY: (
            "the supplied registry carries no entry for this built class, so nothing"
            " declares a draw for it; the class is counted here rather than dropped,"
            " because a built actor nobody modelled is the one this total is most"
            " wrong about"
        ),
        GAP_DRAW_INEXACT: (
            "the entry declares a draw that is not exactly a Fraction, and a float in"
            " the solve path is forbidden outright; the value is refused rather than"
            " converted, because a conversion here would be exact and wrong"
        ),
    }
)

#: One fixed line per warning code raised here. Keyed rather than formatted, so
#: a detail can never be built from something read out of a save - the idiom
#: ``clockspeed/save/world.py`` established for the same reason.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_BALANCE_DRAW_UNMODELED: (
            "this many built actors contributed no number to the world draw because"
            " their class' draw is not modelled; the consumption total is a LOWER"
            " BOUND and never a measurement, and every one of them is named in the"
            " gap list with the kind of gap it is"
        ),
        WARN_BALANCE_NOTHING_BUILT: (
            "the placement model carried no built class at all, so the world draw is"
            " zero because there was nothing to sum; a world with nothing built and a"
            " world whose built actors were all filtered out produce the same number"
        ),
        WARN_BALANCE_PRODUCING_UNAVAILABLE: (
            "no machine in this world carried a readable producing flag, so the empty"
            " starved set means nothing could be measured and never that nothing is"
            " starved"
        ),
        WARN_BALANCE_MACHINE_STATE_UNREAD: (
            "this many machines carried no producing flag, so they were neither"
            " flagged nor counted as running; the starved set is short by whatever"
            " those machines hold"
        ),
        WARN_BALANCE_PRODUCTION_UNMODELED: (
            "power production is not modelled anywhere in this project, so this"
            " balance carries consumption alone; a production total of zero beside a"
            " real consumption total would render every world in permanent brownout"
        ),
        WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE: (
            "the network model declares no belt topology, so a starved machine's"
            " upstream cause cannot be named and the finding is a symptom rather than"
            " a whole audit; no proximity fallback is used, because a nearest"
            " neighbour renders a wrong answer that reads like a right one"
        ),
    }
)


@dataclass(frozen=True)
class DrawContribution:
    """One built class' contribution to the world draw, with a number behind it.

    ONLY A CLASS WITH A MODELED SCALAR DRAW MAY ENTER THIS BUCKET, so both
    Fractions are always populated and neither is ever None. A class whose draw
    is unmodeled is a :class:`DrawGap` instead - see the module docstring for
    why the two are separate types rather than one type with nullable fields.

    NO INSTANCE NAME, NO INDEX, NO OFFSET, NO PATH. A bare class name is
    publisher content on the terms ``clockspeed/audit/placement.py``
    ``Placement`` states.

    Attributes:
        class_name: The built actor class, as ``WorldPlacement.built_counts``
            keys it.
        built_count: How many of that class are built.
        megawatts_each: The declared draw of ONE, at the reference clock.
        megawatts_total: ``megawatts_each * built_count``, exactly.
    """

    class_name: str
    built_count: int
    megawatts_each: Fraction
    megawatts_total: Fraction


@dataclass(frozen=True)
class DrawGap:
    """One built class that contributed NO NUMBER to the world draw.

    **THERE IS DELIBERATELY NO MEGAWATTS FIELD ON THIS TYPE.** A zero is not
    merely absent here, it is unrepresentable: there is nothing for a consumer
    to read a zero out of and nothing for a later change to default to zero.
    ``tests/audit/test_balance.py::test_a_gap_has_no_megawatts_field_to_read_a_zero_out_of``
    grades that structurally, off the declared fields, because an arm checking
    one instance's value would pass the day the field came back.

    Attributes:
        class_name: The built actor class this gap is about.
        built_count: How many of that class are built. The gap is COUNTABLE in
            actors and not merely in classes, which is the difference between
            "four classes went unmodelled" and "eighteen buildings did".
        kind: One of :data:`GAP_KINDS`. Named rather than reduced to a boolean,
            because the five ways a draw goes missing are five different facts
            and a caller renders them differently.
        reason: One line naming why. Carried verbatim from
            ``clockspeed/solve/power.py`` for the three declaration-side kinds,
            so that module stays the single owner of those words.
    """

    class_name: str
    built_count: int
    kind: str
    reason: str


@dataclass(frozen=True, repr=False)
class WorldDraw:
    """The whole-world power draw, partitioned into what is known and what is not.

    ``repr`` renders counts and flags only, for the reason
    ``clockspeed/audit/inventory.py`` ``WorldInventory`` gives.

    Attributes:
        contributions: One entry per built class with a modeled draw, in sorted
            class-name order so two runs agree.
        gaps: One entry per built class without one, in the same order.
        consumption_megawatts: The exact Fraction sum over
            :attr:`contributions`. A LOWER BOUND whenever :attr:`gaps` is
            non-empty, which :attr:`consumption_complete` is how a consumer
            learns without walking the list.
        consumption_complete: Whether every built class had a number. False
            means the total above is a floor and not a measurement.
        classes_considered: How many built classes were partitioned. Equal to
            ``len(contributions) + len(gaps)`` by construction, and worth asking
            rather than deriving, for the reason ``WorldProperties.total`` gives.
        unmodeled_class_count: ``len(gaps)``.
        unmodeled_contributor_count: The sum of :attr:`DrawGap.built_count` over
            the gaps. THE COUNT THE ITEM FILING NAMES, and deliberately not the
            one above it: they are different numbers and only one of them says
            how much of the factory is missing from the total.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
    """

    contributions: tuple[DrawContribution, ...]
    gaps: tuple[DrawGap, ...]
    consumption_megawatts: Fraction
    consumption_complete: bool
    classes_considered: int
    unmodeled_class_count: int
    unmodeled_contributor_count: int
    warnings: tuple[WorldWarning, ...]

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(contributions={len(self.contributions)}, "
            f"gaps={len(self.gaps)}, "
            f"consumption_complete={self.consumption_complete}, "
            f"classes_considered={self.classes_considered}, "
            f"unmodeled_class_count={self.unmodeled_class_count}, "
            f"unmodeled_contributor_count={self.unmodeled_contributor_count}, "
            f"warnings={len(self.warnings)})"
        )


@dataclass(frozen=True, repr=False)
class WorldStarvation:
    """Which machines have work to do and are not doing it, and what was unreadable.

    THE FOUR CATEGORIES PARTITION THE POPULATION AND CONSERVE against
    :attr:`machines_considered`, so a machine this module dropped cannot be
    expressed - the same control :class:`WorldDraw` puts on its own two buckets.

    Attributes:
        starved_indices: Positions into ``WorldMachines.machines``, ascending.
            A position and nothing else - see the module docstring.
        running_count: How many machines report producing.
        unconfigured_count: How many are not producing and carry no recipe. NOT
            STARVED: a machine nobody has set a recipe on has no work to be
            short of, and flagging it would bury the finding that matters.
        unknown_state_count: How many carried no producing flag at all. Never
            flagged and never counted as running, because None means this reader
            saw no such tag and never means the game's default.
        machines_considered: How many machines the input population held.
        producing_available: Carried verbatim from
            ``WorldMachines.producing_available``. False over a non-empty
            population means the empty starved set is a fact about this reader.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
    """

    starved_indices: tuple[int, ...]
    running_count: int
    unconfigured_count: int
    unknown_state_count: int
    machines_considered: int
    producing_available: bool
    warnings: tuple[WorldWarning, ...]

    def __repr__(self) -> str:
        """Render counts and flags, and none that a member could make raise.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(starved={len(self.starved_indices)}, "
            f"running_count={self.running_count}, "
            f"unconfigured_count={self.unconfigured_count}, "
            f"unknown_state_count={self.unknown_state_count}, "
            f"machines_considered={self.machines_considered}, "
            f"producing_available={self.producing_available}, "
            f"warnings={len(self.warnings)})"
        )


@dataclass(frozen=True, repr=False)
class WorldBalance:
    """Both halves of the power balance over one world, with what is absent named.

    Attributes:
        draw: The consumption half.
        starvation: The inefficiency half.
        production_available: ALWAYS FALSE TODAY, and a FIELD rather than an
            omission - see the module docstring. Nothing in this project models
            a generator's output, so there is no production number to publish
            and a zero would be a lie.
        connected_edges_available: Whether a starved machine's upstream segment
            can be named. DERIVED from ``WorldNetwork.belt_topology_available``
            rather than asserted, so it answers True on its own the day belt
            topology lands.
        warnings: Every sub-model's warnings followed by this level's own, so a
            consumer holding this object never has to reach into a sub-model to
            find a flag.
    """

    draw: WorldDraw
    starvation: WorldStarvation
    production_available: bool
    connected_edges_available: bool
    warnings: tuple[WorldWarning, ...]

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(consumption_complete={self.draw.consumption_complete}, "
            f"starved={len(self.starvation.starved_indices)}, "
            f"production_available={self.production_available}, "
            f"connected_edges_available={self.connected_edges_available}, "
            f"warnings={len(self.warnings)})"
        )


def _warning(code: str, count: int = 1) -> WorldWarning:
    """Build one warning from this module's own fixed detail table.

    Args:
        code: One of this module's ``WARN_*`` constants.
        count: How many occurrences it aggregates.

    Returns:
        The warning.
    """
    return WorldWarning(
        source=SOURCE_BALANCE,
        code=code,
        detail=_WARNING_DETAIL[code],
        count=count,
    )


def _classify(class_name: str, count: int, entry: Building | None) -> DrawContribution | DrawGap:
    """Put one built class in exactly one bucket, and never in neither or both.

    ONE FUNCTION RETURNING ONE OF THE TWO BUCKET TYPES, rather than a predicate
    beside a separate value lookup. A predicate would leave the caller to
    re-derive the number for the classes it admitted, which is the same decision
    taken twice and the classic way two branches drift apart.

    THREE INDEPENDENT REFUSALS, AND THE ORDER IS LOAD-BEARING FOR ONE PAIR. An
    absent entry is decided first because there is nothing to ask otherwise. The
    exactness refusal comes AFTER the declaration is read, so an entry that
    declares no scalar at all is reported as undeclared rather than as inexact -
    None is not a float, and calling it one would name the wrong fault. The
    three declaration shapes are then whatever ``clockspeed/solve/power.py``
    says they are.

    Args:
        class_name: The built actor class.
        count: How many of it are built.
        entry: The registry entry, or None when the registry carries none.

    Returns:
        A contribution when the class has a modeled exact draw, and a gap of the
        kind that names what went missing otherwise.
    """
    if entry is None:
        return DrawGap(
            class_name=class_name,
            built_count=count,
            kind=GAP_NO_REGISTRY_ENTRY,
            reason=_GAP_REASON[GAP_NO_REGISTRY_ENTRY],
        )

    draw = declared_draw(entry)
    if not draw.modeled or draw.megawatts is None:
        return DrawGap(
            class_name=class_name,
            built_count=count,
            kind=draw.shape,
            reason=draw.reason,
        )

    if type(draw.megawatts) is not Fraction:
        return DrawGap(
            class_name=class_name,
            built_count=count,
            kind=GAP_DRAW_INEXACT,
            reason=_GAP_REASON[GAP_DRAW_INEXACT],
        )

    return DrawContribution(
        class_name=class_name,
        built_count=count,
        megawatts_each=draw.megawatts,
        megawatts_total=draw.megawatts * count,
    )


def draw_of(placement: WorldPlacement, buildings: Mapping[str, Building]) -> WorldDraw:
    """Compute the world power draw as the exact sum over the built counts.

    PURE, AND TOTAL. Every input produces a model: an empty world, a registry
    that models nothing, and a registry carrying a float draw all return a valid
    :class:`WorldDraw` carrying the flags and the named gaps that say so.
    Nothing here raises, because a power answer that refuses to render is
    strictly worse than one that reports what it has and names what it lost.

    Args:
        placement: The placement model whose ``built_counts`` this sums over.
            Read only; nothing here reads a save.
        buildings: The registry, keyed by the same bare class name the built
            counts are keyed by. Supplied by the caller - this module never
            builds one and never reads ``clockspeed/data/``.

    Returns:
        The draw, partitioned. The consumption total is the exact Fraction sum
        over the modeled contributors alone, and is a LOWER BOUND whenever any
        gap exists.
    """
    contributions: list[DrawContribution] = []
    gaps: list[DrawGap] = []
    total = Fraction(0)

    for class_name in sorted(placement.built_counts):
        count = placement.built_counts[class_name]
        bucket = _classify(class_name, count, buildings.get(class_name))
        if isinstance(bucket, DrawGap):
            gaps.append(bucket)
            continue
        contributions.append(bucket)
        total += bucket.megawatts_total

    unmodeled_contributors = sum(gap.built_count for gap in gaps)

    warnings: list[WorldWarning] = []
    if not placement.built_counts:
        warnings.append(_warning(WARN_BALANCE_NOTHING_BUILT))
    if unmodeled_contributors:
        warnings.append(_warning(WARN_BALANCE_DRAW_UNMODELED, unmodeled_contributors))

    return WorldDraw(
        contributions=tuple(contributions),
        gaps=tuple(gaps),
        consumption_megawatts=total,
        consumption_complete=not gaps,
        classes_considered=len(placement.built_counts),
        unmodeled_class_count=len(gaps),
        unmodeled_contributor_count=unmodeled_contributors,
        warnings=tuple(warnings),
    )


def starvation_of(machines: WorldMachines) -> WorldStarvation:
    """Flag every machine that carries a recipe and is not producing.

    PURE, AND TOTAL, on the same terms :func:`draw_of` states.

    Args:
        machines: The machines model. Read only.

    Returns:
        The starvation model, whose four categories partition the population.
    """
    starved: list[int] = []
    running = 0
    unconfigured = 0
    unknown = 0

    for index, state in enumerate(machines.machines):
        if state.producing is None:
            unknown += 1
        elif state.producing:
            running += 1
        elif state.recipe_class_name is None:
            unconfigured += 1
        else:
            starved.append(index)

    warnings: list[WorldWarning] = []
    if machines.machines and not machines.producing_available:
        warnings.append(_warning(WARN_BALANCE_PRODUCING_UNAVAILABLE))
    if unknown:
        warnings.append(_warning(WARN_BALANCE_MACHINE_STATE_UNREAD, unknown))

    return WorldStarvation(
        starved_indices=tuple(starved),
        running_count=running,
        unconfigured_count=unconfigured,
        unknown_state_count=unknown,
        machines_considered=len(machines.machines),
        producing_available=machines.producing_available,
        warnings=tuple(warnings),
    )


def balance_of(
    placement: WorldPlacement,
    buildings: Mapping[str, Building],
    machines: WorldMachines,
    network: WorldNetwork,
) -> WorldBalance:
    """Compute both halves of one world's power balance.

    Args:
        placement: The placement model, for the built counts.
        buildings: The registry, keyed by bare class name.
        machines: The machines model, for the producing flag.
        network: The network model, for whether an upstream cause can be named.

    Returns:
        The balance, carrying every sub-model's warnings plus this level's own.
    """
    draw = draw_of(placement, buildings)
    starvation = starvation_of(machines)

    warnings = [*draw.warnings, *starvation.warnings, _warning(WARN_BALANCE_PRODUCTION_UNMODELED)]
    if not network.belt_topology_available:
        warnings.append(_warning(WARN_BALANCE_UPSTREAM_CAUSE_UNAVAILABLE))

    return WorldBalance(
        draw=draw,
        starvation=starvation,
        production_available=False,
        connected_edges_available=network.belt_topology_available,
        warnings=tuple(warnings),
    )
