"""CS-1235: the nominal item flow of a built world - per item, exact, per minute.

WHAT THIS MODULE OWNS
-----------------------
One pure function, :func:`flow_of`. Given the machines a world has built and
the recipes a caller supplies, it computes what every item's NOMINAL net rate
per minute is: the sum, over every machine, of that machine's recipe rate scaled
by that machine's clock. It then reports each item's gross production, gross
consumption and net, which items are short (DEFICITS) and which are over
(SURPLUSES), against whatever the caller declares raw and whatever net output
the caller demands.

"NOMINAL" IS THE WHOLE CLAIM AND IT IS A NARROW ONE. The answer is what the
built machines move IF EVERY ONE OF THEM RUNS AT ITS CONFIGURED CLOCK. It does
not consult the producing flag - a starved machine is
``clockspeed/audit/balance.py``'s finding, not this one's - and it knows nothing
about belts, so a world whose belts cannot carry the flow still reads balanced
here. Its use is the diff between what was built and what a plan asked for: a
built world that is short in NOMINAL terms is short no matter how its belts run.

The rate is LINEAR IN THE CLOCK. A machine at clock ``c`` completes ``c`` times
as many cycles per minute as one at the reference clock; only its POWER draw is
non-linear in the clock, and power is not this module's question.

THE CALLER SUPPLIES THE RECIPES, AS ``balance.py`` TAKES ITS BUILDINGS
-------------------------------------------------------------------------
``Recipe`` is imported for its type only. Nothing here builds a registry, reads
``clockspeed/data/`` or opens a save; the per-minute conversion is
``clockspeed/solve/exact.py`` ``per_minute``, the one owner of that arithmetic,
so the rate this module computes cannot drift from the one the solver solved.

FLAG AND SKIP, NEVER A CONFIDENT ZERO (NON-NEGOTIABLE 7)
---------------------------------------------------------
Every machine lands in EXACTLY ONE bucket. Either it flows - it carries a recipe
the mapping knows, whose rate is defined, no production-boost tag, and a clock
that is an exact non-negative ``Fraction`` - and is summed into a
:class:`RecipeGroup`; or it is
skipped into a :class:`FlowGap` of a NAMED kind, counted, and reported under a
``WARN_FLOW_*`` code. ``FlowGap`` has no rate field at all, for the reason
``balance.py`` ``DrawGap`` has no megawatts field: a skipped machine has no
number, and a zero would read as a measurement. The buckets conserve -
``sum(group.machine_count) + sum(gap.machine_count) == machines_considered``.

THE CHECKS RUN IN A FIXED ORDER, so a machine wrong in two ways is reported
under the first: no recipe, then a recipe the mapping does not carry, then a
recipe with no defined rate (a zero duration, or an amount that is not exactly a
Fraction), then a production boost, then an unread clock, then a refused clock.
Recipe-side faults come first because they hold for every machine on that recipe
whatever its clock or its boost. The boost comes next and BEFORE the clock - the
order ``clockspeed/audit/balance.py`` decides it in, after its registry side -
because no clock reading can rate a boosted machine.

A PRODUCTION BOOST IS A NAMED GAP, NEVER A CLOCK-ONLY RATE (CS-1278, on
CS-1264's terms). A boost multiplies output on top of the clock, and its saved
value is unmeasured - no save in the library carries the tag - so a machine whose
``MachineState.production_boost_tagged`` is set, by the tag's PRESENCE and
whether or not its value decoded, is :data:`GAP_FLOW_BOOST_UNMODELED` unless a
recipe-side fault wins first. The boost's value is never read, and neither are
the clock and the producing flag beside it: a read clock and the elided default
are equally the wrong rate, so a boosted machine never flows and never enters
the elided count.

WHAT THE TWO AUDITS AGREE ON IS NARROWER THAN ONE NAME. Neither audit ever
prices or flows a boosted machine - each names it a gap, or for a generator
class the balance counts it apart - so neither publishes a number for it. The
NAMES agree, boost-unmodeled in both, only where no earlier fault wins in either
audit's documented order. Each decides the boost after its own earlier side,
and neither reads the other's: a machine with no recipe, an unknown one or one
with no defined rate is a recipe-side gap here while the balance, which reads no
recipe, names the boost; a machine whose class the balance's registry does not
model is a registry gap there while this audit, which reads no registry, names
the boost.
``tests/audit/test_flow.py::test_the_flow_and_the_balance_classify_every_clock_alike``
holds the names to agree where no earlier fault exists, and
``tests/audit/test_flow.py::test_both_audits_name_a_boosted_machine_a_gap_when_an_earlier_fault_wins``
pins the disagreement on names where one does, and that both are gaps.

AN UNREAD CLOCK IS NEVER READ AS ONE. ``MachineState.overclock`` is None when
the reader saw no tag, and the game's default clock IS one - so substituting one
is right on every machine nobody overclocked and wrong on exactly the ones
somebody did. ``clockspeed/audit/machines.py`` states the same fence.

AN ELIDED CLOCK IS THE CLASS DEFAULT, COUNTED (CS-1265, under CS-1263's ruling).
The save serializer writes no clock tag for a machine at the class default, so
a None clock that ``MachineState.overclock_elided`` marks - a cleanly read
payload, no disagreeing tag, no clock tag at all - is a measured fact and not an
unknown. Such a machine flows at ``clockspeed/audit/balance.py``
``ELIDED_CLOCK_DEFAULT``, the one owner of that value, and is counted on its
:class:`RecipeGroup` and on :class:`WorldFlow`, so the default is never silent.
The predicate is the balance's own - the clock is None AND the mark is set - so
the two audits cannot disagree about the clock of a machine both of them price;
``tests/audit/test_flow.py::test_the_flow_and_the_balance_classify_every_clock_alike``
holds them to it. Their elided COUNTS are scoped to their own populations and
differ where one audit gaps a machine before its clock is read -
:attr:`WorldFlow.elided_clock_count` states the scope. A clock absent for ANY
other reason - refused, an unread payload, a disagreeing tag, or a hand-built
state nobody marked - stays :data:`GAP_FLOW_CLOCK_UNREAD`.

WHAT A DEFICIT IS
-------------------
An item is SHORT when its net rate falls below what the caller demands of it -
zero by default, so an intermediate consumed faster than it is made is short -
AND the caller has not declared it raw. A raw item is supplied from outside the
built machines (an extractor, a delivery) and its negative net is the world's
raw demand rather than a fault. A deficit NAMES the recipes that make the item
and the recipes that eat it, because "Plate is short" is half a finding and
"Plate is short and R_Plate is its only producer" is the whole one.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.audit.balance import ELIDED_CLOCK_DEFAULT
from clockspeed.audit.machines import MachineState, WorldMachines
from clockspeed.save.world import WorldWarning
from clockspeed.solve.exact import ExactArithmeticError, audit_exact, per_minute

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from clockspeed.data.registry import Recipe

__all__ = [
    "GAP_FLOW_BOOST_UNMODELED",
    "GAP_FLOW_CLOCK_REFUSED",
    "GAP_FLOW_CLOCK_UNREAD",
    "GAP_FLOW_KINDS",
    "GAP_FLOW_NO_RECIPE",
    "GAP_FLOW_RATE_UNDEFINED",
    "GAP_FLOW_RECIPE_UNKNOWN",
    "SOURCE_FLOW",
    "WARN_FLOW_BOOST_UNMODELED",
    "WARN_FLOW_CLOCK_REFUSED",
    "WARN_FLOW_CLOCK_UNREAD",
    "WARN_FLOW_NOTHING_FLOWING",
    "WARN_FLOW_NO_RECIPE",
    "WARN_FLOW_RATE_UNDEFINED",
    "WARN_FLOW_RECIPE_UNKNOWN",
    "FlowGap",
    "ItemFlow",
    "RecipeGroup",
    "WorldFlow",
    "flow_of",
]

#: Which layer noticed a warning raised here, for ``WorldWarning.source``.
SOURCE_FLOW: Final = "flow"

#: A machine carrying no recipe. Whatever it moves - an extractor's output
#: included - is outside this flow.
GAP_FLOW_NO_RECIPE: Final = "no-recipe"

#: A machine whose recipe the supplied mapping does not carry: modded content,
#: or content not modelled. There is no entry to ask for a rate.
GAP_FLOW_RECIPE_UNKNOWN: Final = "recipe-unknown"

#: A machine whose recipe has no defined per-minute rate: a measured zero
#: duration, or an amount or duration that is not exactly a Fraction.
GAP_FLOW_RATE_UNDEFINED: Final = "rate-undefined"

#: CS-1278. A machine whose payload carried a production-boost tag -
#: ``MachineState.production_boost_tagged``, decoded or not. NEVER FLOWED AT
#: ITS CLOCK ALONE: a boost multiplies output on top of the clock, and its saved
#: value is unmeasured, so neither a read clock nor the elided default is its
#: rate. The word is ``clockspeed/audit/balance.py`` ``GAP_BOOST_UNMODELED``'s
#: own; the two audits name one machine alike only where no earlier fault wins
#: in either, as the module docstring states.
GAP_FLOW_BOOST_UNMODELED: Final = "boost-unmodeled"

#: A machine whose clock never read - refused, or absent for any reason other
#: than the elided class default. Never substituted with one.
GAP_FLOW_CLOCK_UNREAD: Final = "clock-unread"

#: A machine whose clock is not exactly a non-negative Fraction. Refused rather
#: than converted, because a conversion here would be exact and wrong.
GAP_FLOW_CLOCK_REFUSED: Final = "clock-refused"

#: The closed vocabulary of gap kinds, so a consumer can branch on a full list.
GAP_FLOW_KINDS: Final = (
    GAP_FLOW_NO_RECIPE,
    GAP_FLOW_RECIPE_UNKNOWN,
    GAP_FLOW_RATE_UNDEFINED,
    GAP_FLOW_BOOST_UNMODELED,
    GAP_FLOW_CLOCK_UNREAD,
    GAP_FLOW_CLOCK_REFUSED,
)

#: This many machines carried no recipe and moved nothing in this flow.
WARN_FLOW_NO_RECIPE: Final = "flow-no-recipe"

#: This many machines named a recipe the supplied mapping does not carry.
WARN_FLOW_RECIPE_UNKNOWN: Final = "flow-recipe-unknown"

#: This many machines ran a recipe with no defined per-minute rate.
WARN_FLOW_RATE_UNDEFINED: Final = "flow-rate-undefined"

#: CS-1278. This many machines carried a production-boost tag, whose effect on
#: output is not modelled.
WARN_FLOW_BOOST_UNMODELED: Final = "flow-boost-unmodeled"

#: This many machines carried no readable clock.
WARN_FLOW_CLOCK_UNREAD: Final = "flow-clock-unread"

#: This many machines carried a clock that is not an exact non-negative Fraction.
WARN_FLOW_CLOCK_REFUSED: Final = "flow-clock-refused"

#: No machine contributed to the flow - an empty population, or one wholly
#: skipped. An empty item map then means nothing was measured, never that the
#: world is balanced.
WARN_FLOW_NOTHING_FLOWING: Final = "flow-nothing-flowing"

_WARNING_OF_GAP: Final[Mapping[str, str]] = MappingProxyType(
    {
        GAP_FLOW_NO_RECIPE: WARN_FLOW_NO_RECIPE,
        GAP_FLOW_RECIPE_UNKNOWN: WARN_FLOW_RECIPE_UNKNOWN,
        GAP_FLOW_RATE_UNDEFINED: WARN_FLOW_RATE_UNDEFINED,
        GAP_FLOW_BOOST_UNMODELED: WARN_FLOW_BOOST_UNMODELED,
        GAP_FLOW_CLOCK_UNREAD: WARN_FLOW_CLOCK_UNREAD,
        GAP_FLOW_CLOCK_REFUSED: WARN_FLOW_CLOCK_REFUSED,
    }
)

#: One fixed line per warning code. Keyed rather than formatted, so a detail can
#: never be built from something read out of a save.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_FLOW_NO_RECIPE: (
            "this many machines carry no recipe, so whatever they move - extraction"
            " included - is outside this flow; declare such items raw rather than"
            " read their absence as zero"
        ),
        WARN_FLOW_RECIPE_UNKNOWN: (
            "this many machines name a recipe the supplied mapping does not carry, so"
            " they contributed nothing; every item total is short by whatever they move"
        ),
        WARN_FLOW_RATE_UNDEFINED: (
            "this many machines run a recipe with no defined per-minute rate - a zero"
            " duration or an inexact amount - so they contributed nothing"
        ),
        WARN_FLOW_BOOST_UNMODELED: (
            "this many machines carry a production-boost tag, which multiplies output"
            " on top of the clock and whose value is not modelled, so they contributed"
            " nothing; flowing one at its clock alone, or at the elided default, would"
            " flow a boosted machine as unboosted"
        ),
        WARN_FLOW_CLOCK_UNREAD: (
            "this many machines carry no readable clock, so they contributed nothing;"
            " a clock absent for any reason other than the elided class default is"
            " never read as one, because one is right exactly where nobody overclocked"
            " and wrong everywhere else"
        ),
        WARN_FLOW_CLOCK_REFUSED: (
            "this many machines carry a clock that is not an exact non-negative"
            " Fraction, so it was refused rather than converted and they contributed"
            " nothing"
        ),
        WARN_FLOW_NOTHING_FLOWING: (
            "no machine contributed to the flow, so an empty item map means nothing"
            " could be measured and never that the world is balanced"
        ),
    }
)


@dataclass(frozen=True, repr=False)
class RecipeGroup:
    """The machines that flowed on one recipe, summed.

    Attributes:
        recipe_class_name: The recipe, as ``MachineState.recipe_class_name``
            names it and the supplied mapping keys it.
        machine_count: How many machines run it.
        machine_equivalents: The exact sum of their clocks - the number of
            reference-clock machines that would move the same flow. This is the
            figure a solver's ``PlanStep.machines`` is comparable to.
        elided_machine_count: CS-1265. How many of :attr:`machine_count` flowed
            at ``ELIDED_CLOCK_DEFAULT`` because their clock tag was elided,
            rather than at a clock read from the save.
    """

    recipe_class_name: str
    machine_count: int
    machine_equivalents: Fraction
    elided_machine_count: int

    def __repr__(self) -> str:
        """Render counts only.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(machine_count={self.machine_count}, "
            f"machine_equivalents={self.machine_equivalents}, "
            f"elided_machine_count={self.elided_machine_count})"
        )


@dataclass(frozen=True, repr=False)
class FlowGap:
    """Machines that contributed NO NUMBER to the flow, grouped by kind and recipe.

    **THERE IS DELIBERATELY NO RATE FIELD ON THIS TYPE**, on the terms
    ``clockspeed/audit/balance.py`` ``DrawGap`` states for its megawatts.

    Attributes:
        kind: One of :data:`GAP_FLOW_KINDS`.
        recipe_class_name: The recipe the machines name, or None for
            :data:`GAP_FLOW_NO_RECIPE`.
        machine_count: How many machines this gap holds.
    """

    kind: str
    recipe_class_name: str | None
    machine_count: int

    def __repr__(self) -> str:
        """Render the kind and count, and no recipe name.

        Returns:
            The safe rendering.
        """
        return f"{type(self).__name__}(kind={self.kind!r}, machine_count={self.machine_count})"


@dataclass(frozen=True, repr=False)
class ItemFlow:
    """One item's nominal flow, per minute, exact.

    Attributes:
        item_key: The item's class name.
        produced: Gross production over every flowing machine.
        consumed: Gross consumption over every flowing machine, positive.
        net: ``produced - consumed``. Negative means the built machines eat it
            faster than they make it.
        demand: The net output the caller asked of this item, zero when it
            asked none.
        raw: Whether the caller declared it raw - supplied from outside the
            built machines, so a negative net is demand rather than a fault.
        shortfall: ``demand - net`` when this item is a deficit, else zero.
        producers: The recipes that make it, sorted.
        consumers: The recipes that eat it, sorted.
    """

    item_key: str
    produced: Fraction
    consumed: Fraction
    net: Fraction
    demand: Fraction
    raw: bool
    shortfall: Fraction
    producers: tuple[str, ...]
    consumers: tuple[str, ...]

    @property
    def is_deficit(self) -> bool:
        """Whether this item is short: not raw, and below its demand.

        Returns:
            True for a deficit.
        """
        return not self.raw and self.net < self.demand

    @property
    def is_surplus(self) -> bool:
        """Whether this item is over its demand.

        Returns:
            True for a surplus.
        """
        return self.net > self.demand

    def __repr__(self) -> str:
        """Render the numbers and no name.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(net={self.net}, demand={self.demand}, raw={self.raw}, "
            f"producers={len(self.producers)}, consumers={len(self.consumers)})"
        )


@dataclass(frozen=True, repr=False)
class WorldFlow:
    """The nominal item flow of one world, with what was skipped named.

    Attributes:
        groups: One per recipe that flowed, sorted by recipe class name.
        gaps: One per (kind, recipe) that was skipped, in kind order then
            recipe order.
        items: Item key to its flow, sorted by key. Every item a flowing
            recipe touches, plus every demanded item.
        deficits: The items short of their demand and not raw, in key order.
        surpluses: The items over their demand, in key order.
        raw_items: What the caller declared raw, sorted.
        machines_considered: How many machines the input held.
        skipped_count: How many of them are in a gap.
        complete: Whether every machine flowed. False means every item total
            is short by whatever the skipped machines move.
        warnings: Everything flagged, in the ``WorldWarning`` idiom.
        elided_clock_count: CS-1265. How many FLOWING machines ran at
            ``ELIDED_CLOCK_DEFAULT`` because their clock tag was elided - the
            sum of every group's ``elided_machine_count``. SCOPED TO THIS
            AUDIT'S POPULATION, and NOT the figure
            ``clockspeed/audit/balance.py`` ``WorldClockedDraw.elided_clock_count``
            publishes: an elided machine is counted here only when its recipe
            flows, and there only when the balance prices its class. A machine
            with no recipe or an unknown one is a recipe-side gap here and still
            counted there; a machine whose class the balance does not model, or
            cannot price at the elided default (a power exponent that is not
            exactly a Fraction, which it names law-inexact), is the reverse. The
            two agree machine by machine wherever the flow flows the machine AND
            the balance prices it - ``tests/audit/test_flow.py`` grades both
            halves. CS-1278: neither audit prices or flows a boosted machine,
            so it is counted in neither, elided or not.
    """

    groups: tuple[RecipeGroup, ...]
    gaps: tuple[FlowGap, ...]
    items: Mapping[str, ItemFlow]
    deficits: tuple[ItemFlow, ...]
    surpluses: tuple[ItemFlow, ...]
    raw_items: tuple[str, ...]
    machines_considered: int
    skipped_count: int
    complete: bool
    warnings: tuple[WorldWarning, ...]
    elided_clock_count: int

    def __repr__(self) -> str:
        """Render counts and flags, and nothing about any member.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(groups={len(self.groups)}, gaps={len(self.gaps)}, "
            f"items={len(self.items)}, deficits={len(self.deficits)}, "
            f"surpluses={len(self.surpluses)}, "
            f"machines_considered={self.machines_considered}, "
            f"skipped_count={self.skipped_count}, complete={self.complete}, "
            f"elided_clock_count={self.elided_clock_count}, "
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
    return WorldWarning(source=SOURCE_FLOW, code=code, detail=_WARNING_DETAIL[code], count=count)


def _rates(recipe: Recipe) -> tuple[dict[str, Fraction], dict[str, Fraction]] | None:
    """One reference-clock machine's gross inputs and outputs per minute.

    Args:
        recipe: The recipe.

    Returns:
        Item to rate consumed, and item to rate produced, both positive; or None
        when the recipe has no defined rate.
    """
    consumed: dict[str, Fraction] = {}
    produced: dict[str, Fraction] = {}
    try:
        for io in recipe.inputs:
            consumed[io.item_key] = consumed.get(io.item_key, Fraction(0)) + per_minute(
                io.amount, recipe.duration
            )
        for io in recipe.outputs:
            produced[io.item_key] = produced.get(io.item_key, Fraction(0)) + per_minute(
                io.amount, recipe.duration
            )
    except ExactArithmeticError:
        return None
    return consumed, produced


def _clock_of(state: MachineState) -> tuple[Fraction | None, bool]:
    """The clock one machine flows at, and whether it is the elided default.

    THE BALANCE'S OWN PREDICATE, written to match
    ``clockspeed/audit/balance.py`` ``clocked_draw_of``: the default stands in
    only when the clock is None AND the elision mark is set, so a present clock
    is never overridden by the mark and an unmarked None is never priced.

    Args:
        state: The machine.

    Returns:
        ``(clock, elided)``: the default and True for an elided tag, otherwise
        the clock as read and False.
    """
    if state.overclock is None and state.overclock_elided:
        return ELIDED_CLOCK_DEFAULT, True
    return state.overclock, False


def _gap_kind(  # noqa: PLR0911 - one return per gap kind, in the fixed order, is the clearest surface
    state: MachineState,
    clock: Fraction | None,
    recipes: Mapping[str, Recipe],
    rates: Mapping[str, tuple[dict[str, Fraction], dict[str, Fraction]] | None],
) -> str | None:
    """Decide whether one machine is skipped, and under which kind.

    Args:
        state: The machine.
        clock: The clock :func:`_clock_of` read for it.
        recipes: The supplied recipes.
        rates: The per-recipe rate cache, filled for every known recipe.

    Returns:
        The gap kind, or None when the machine flows. See the module docstring
        for why the order is fixed.
    """
    recipe = state.recipe_class_name
    if recipe is None:
        return GAP_FLOW_NO_RECIPE
    if recipe not in recipes:
        return GAP_FLOW_RECIPE_UNKNOWN
    if rates[recipe] is None:
        return GAP_FLOW_RATE_UNDEFINED
    if state.production_boost_tagged:
        return GAP_FLOW_BOOST_UNMODELED
    if clock is None:
        return GAP_FLOW_CLOCK_UNREAD
    if type(clock) is not Fraction or clock < 0:
        return GAP_FLOW_CLOCK_REFUSED
    return None


def _partition(
    population: Sequence[MachineState],
    recipes: Mapping[str, Recipe],
    rates: Mapping[str, tuple[dict[str, Fraction], dict[str, Fraction]] | None],
) -> tuple[dict[str, int], dict[str, Fraction], dict[str, int], dict[tuple[str, str | None], int]]:
    """Put every machine in exactly one bucket: a recipe group or a named gap.

    Args:
        population: The machines.
        recipes: The supplied recipes.
        rates: The per-recipe rate cache, filled for every known recipe.

    Returns:
        Per flowing recipe its machine count, its clock sum and how many of its
        machines flowed at the elided default; and per ``(kind, recipe)`` gap
        its machine count.
    """
    counts: dict[str, int] = {}
    clocks: dict[str, Fraction] = {}
    elided_counts: dict[str, int] = {}
    gaps: dict[tuple[str, str | None], int] = {}
    for state in population:
        clock, elided = _clock_of(state)
        kind = _gap_kind(state, clock, recipes, rates)
        recipe = state.recipe_class_name
        if kind is not None:
            gaps[kind, recipe] = gaps.get((kind, recipe), 0) + 1
            continue
        if recipe is None or clock is None:  # pragma: no cover - _gap_kind's guard
            continue
        counts[recipe] = counts.get(recipe, 0) + 1
        clocks[recipe] = clocks.get(recipe, Fraction(0)) + clock
        elided_counts[recipe] = elided_counts.get(recipe, 0) + int(elided)
    return counts, clocks, elided_counts, gaps


def flow_of(
    machines: WorldMachines | Sequence[MachineState],
    recipes: Mapping[str, Recipe],
    *,
    raw_items: Iterable[str] = (),
    demands: Mapping[str, Fraction] | None = None,
) -> WorldFlow:
    """Compute the nominal per-item flow of a built world, exactly.

    PURE, AND TOTAL OVER THE WORLD: every machine population produces a model,
    and unknown content is a named gap rather than an exception. The CALLER's
    own demand is the one input refused outright when inexact, because it is a
    statement of intent rather than world content, on the terms
    ``clockspeed/solve/ratio.py`` refuses an inexact target.

    Args:
        machines: The machines, as a ``WorldMachines`` model or a bare sequence.
        recipes: The recipes, keyed by class name. Supplied by the caller.
        raw_items: Items supplied from outside the built machines.
        demands: Item to the net output asked of it per minute. Absent items
            are asked for zero.

    Returns:
        The flow, audited exact on the way out.

    Raises:
        InexactValueError: A demand is not exactly a Fraction.
    """
    population = machines.machines if isinstance(machines, WorldMachines) else tuple(machines)
    asked: dict[str, Fraction] = dict(demands or {})
    audit_exact(asked, path="demands")
    raw = tuple(sorted(set(raw_items)))

    rates = {key: _rates(recipe) for key, recipe in recipes.items()}

    group_counts, group_clocks, group_elided, gap_counts = _partition(population, recipes, rates)

    produced: dict[str, Fraction] = {}
    consumed: dict[str, Fraction] = {}
    producers: dict[str, set[str]] = {}
    consumers: dict[str, set[str]] = {}
    for recipe, equivalents in group_clocks.items():
        recipe_rates = rates[recipe]
        if recipe_rates is None:  # pragma: no cover - excluded by _gap_kind
            continue
        ins, outs = recipe_rates
        for item, rate in ins.items():
            consumed[item] = consumed.get(item, Fraction(0)) + rate * equivalents
            consumers.setdefault(item, set()).add(recipe)
        for item, rate in outs.items():
            produced[item] = produced.get(item, Fraction(0)) + rate * equivalents
            producers.setdefault(item, set()).add(recipe)

    raw_set = set(raw)
    items: dict[str, ItemFlow] = {}
    for item in sorted(set(produced) | set(consumed) | set(asked)):
        made = produced.get(item, Fraction(0))
        eaten = consumed.get(item, Fraction(0))
        net = made - eaten
        demand = asked.get(item, Fraction(0))
        is_raw = item in raw_set
        short = not is_raw and net < demand
        items[item] = ItemFlow(
            item_key=item,
            produced=made,
            consumed=eaten,
            net=net,
            demand=demand,
            raw=is_raw,
            shortfall=demand - net if short else Fraction(0),
            producers=tuple(sorted(producers.get(item, ()))),
            consumers=tuple(sorted(consumers.get(item, ()))),
        )

    gaps = tuple(
        FlowGap(kind=kind, recipe_class_name=recipe, machine_count=count)
        for (kind, recipe), count in sorted(
            gap_counts.items(),
            key=lambda entry: (GAP_FLOW_KINDS.index(entry[0][0]), entry[0][1] or ""),
        )
    )
    skipped = sum(gap.machine_count for gap in gaps)

    warnings: list[WorldWarning] = []
    for kind in GAP_FLOW_KINDS:
        count = sum(gap.machine_count for gap in gaps if gap.kind == kind)
        if count:
            warnings.append(_warning(_WARNING_OF_GAP[kind], count))
    if not group_counts:
        warnings.append(_warning(WARN_FLOW_NOTHING_FLOWING))

    result = WorldFlow(
        groups=tuple(
            RecipeGroup(
                recipe_class_name=recipe,
                machine_count=group_counts[recipe],
                machine_equivalents=group_clocks[recipe],
                elided_machine_count=group_elided[recipe],
            )
            for recipe in sorted(group_counts)
        ),
        gaps=gaps,
        items=MappingProxyType(items),
        deficits=tuple(entry for entry in items.values() if entry.is_deficit),
        surpluses=tuple(entry for entry in items.values() if entry.is_surplus),
        raw_items=raw,
        machines_considered=len(population),
        skipped_count=skipped,
        complete=skipped == 0 and bool(group_counts),
        warnings=tuple(warnings),
        elided_clock_count=sum(group_elided.values()),
    )
    audit_exact(result, path="flow")
    return result
