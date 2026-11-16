"""CS-1351, CS-1371, CS-1373, CS-1374, CS-1382: answer a stated target with a plan or a route.

WHAT THIS MODULE OWNS. :class:`PlanRequest`, the question a caller states;
:func:`plan_parameters` and :func:`plan_request_from`, the door a stated rate, direction,
policy and target come in through; and :func:`plan_offer`, which answers the question with
the rule inputs :mod:`clockspeed.advisor.rules.plan` reads.
:func:`clockspeed.advisor.advise.inputs_of` calls it on every world; with no request it does
no work beyond naming the status.

THE TARGET IS THE CALLER'S. Nothing here chooses what to plan for: a world has no single
target, and the milestone target is a free selector (CLAUDE.md section 7). The advice routes
of ``clockspeed/surface/api/advice.py`` state one through
:func:`plan_parameters` and :func:`plan_request_from`. A request carries one direction from
:data:`clockspeed.solve.optimize.OBJECTIVES` and no weighted objective, so the top
plan is always one rung's own optimum and clears that rung.

A SCHEMATIC IS A TARGET THE CATALOG STATES (CS-1373). :func:`schematic_parameters` and
:func:`schematic_request_from` are the door a stated schematic, direction and policy come in
through: no rate is stated, because each cost item's rate is the one
``clockspeed.progress.milestones.milestone_requirement`` publishes, its cost over the
completion budget, and it is read from that requirement and never recomputed, scaled or
rounded here. The request is ONE :class:`SchematicRequest`, a :class:`PlanRequest` whose targets
are all the cost items at those rates, so the search and a no-plan's route each run once for the
whole schematic. A schematic whose requirement publishes no rates, an empty cost, or a cost item
off :func:`clockspeed.data.registry.plan_targets` is still a request, carrying no targets and the
reason, and :func:`plan_offer` answers it with
:data:`clockspeed.advisor.rules.plan.STATUS_SCHEMATIC_UNPLANNABLE` before any join: an item is
named, never dropped to make the rest plannable. :func:`plan_offer` offers the statement beside
every other input, None where none was stated, so the rules read it on every world.

THE JOIN. A plan names recipes by registry ClassName and a save names unlocked
recipes by asset path. The registry publishes each recipe's path, the path half of
its docs ``FullName``, on :attr:`clockspeed.data.registry.Recipe.asset_path`, and
:func:`plan_offer` compares that with each member of
:attr:`clockspeed.save.world.UnlockState.recipes` by WHOLE STRING. It is never cut
to a trailing token (CS-1343) and never rebuilt from a ClassName. A recipe joins
only if it is automated too: a recipe no machine runs cannot be built by a plan,
and a raw search picks one wherever it is cheapest, because raw consumption never
asks what runs a recipe.

A RECIPE IS HELD ONLY WITH A MACHINE TO RUN IT (``BOOTSTRAP.md`` section 5.4). A world can
hold a recipe and no machine in its ``produced_in``, and advice to build that chain could
not be followed. A machine unlocks the way a recipe does, by the build-gun recipe
:func:`clockspeed.data.registry.build_cost` names for it, so the same whole-string
comparison reads that recipe's path. A recipe is HELD when the world holds its whole path
and that path of at least one of its machines. One it holds with no machine held counts as
locked, on the search and on the route alike. The unlock keys a plan requires are each
recipe's own and, for each, the key of the first of its machines the world holds, every
key once, in the order first seen.

A RAW ITEM IS SUPPLIED ONLY WITH A MACHINE TO EXTRACT IT (``BOOTSTRAP.md`` section 5.4,
CS-1382). The resource group says what the game has, not what this world can reach, and advice
to run a chain on an item nothing here extracts could not be followed.
:func:`clockspeed.data.registry.extractors_of` reads which modeled buildings the docs say
extract an item, from data and never from a list here, and the same whole-string comparison
reads each one's build recipe. A raw item is SUPPLIED when the world holds that path of at
least one of them. That is all it means: a held build recipe says the machine can be placed,
and nothing here asks after a node, power or a machine already built.

The search starts from the stated raw items that are supplied, in the stated order, and from
any stated item that is a target, so pillar 1 still refuses that question as malformed
whatever the world holds. A world supplying none, a target stated raw aside, narrows to no raw
items at all, and the search runs as on any other: a plan can rank only if it consumes no raw
item, fed by held recipes eating nothing or by a loop giving back what it eats, within the
stated byproduct policy, and where the kept set holds no such plan the bound answers a
no-plan. Only the stated tuple can make a request malformed. An item taken out of the raw
items this way is an ordinary item to the search, so a held recipe making it can still rank,
and one a plan leaves over meets the stated byproduct policy. A ranked plan's
unlock keys gain, after its recipes' and machines', the key of the first machine the world
holds for each raw item the plan consumes, every key once. ``raw_inputs`` is net and published
sorted by key, so that order is sorted, and a loop giving back what it eats needs no extractor.

WHAT THE JOIN LEAVES OUT IS SAID, NOT DROPPED (non-negotiable 7). A path that is not
printable ASCII counts here as no path, because no unlock key can carry it: the engine would
refuse the whole recommendation as a rule error. An automated
recipe with no path, or no machine of which joins a build recipe with a path, can never be
shown held. Treating it as held would be silently wrong and as locked would state a lock
nothing lifts, so it never enters a search or a route and is named on ``plan.unchecked``,
so no plan can cover a recipe nobody checked. A stated raw item no extractor joining a
build recipe with a path can extract enters neither the search nor the route, because nothing
could show it supplied or say what to unlock, and is named on ``plan.raw_unknown``. An unlocked
path that joins no recipe is COUNTED on ``plan.unmatched_unlocks``, and that count is all that
crosses: a save's own
path never reaches an input, a step, a card, a repr or an exception (non-negotiables 11
and 12). The unlock keys a plan requires are built from the REGISTRY's string, which a
reader may see, and never from the member it compared equal to.

THE SEARCH, IN ORDER.

1. The request is checked: one known direction, one known byproduct policy, raw
   items as stated exactly a non-empty tuple of str, and a mapping of at least one target,
   every key exactly a str and every rate exactly a Fraction above zero. A zero-rate Build card
   is absurd, an unknown policy or a str of raw items reaches pillar 2 as no selection
   at all, which would read as a false no-plan, no raw items at all is a search with
   nothing to start from, and targets of any other shape raise.
2. :func:`clockspeed.solve.bound.optimize_within_bound` answers feasibility over the
   kept set, and the trim. A real world joins more recipes than the exhaustive
   backend's cap, so a whole-set search would refuse. ``plan.trimmed`` names what the
   bound dropped, on every status a search reached: a no-plan speaks only for the
   kept set, and what the cap drops is a rule over the targets, the raw items, the
   joined recipes and the registry, ranking a target's derived route first, so it
   stays true however the search then ends.
3. :func:`clockspeed.solve.optimize.optimize_plan` runs once per ladder rung over
   the kept set, each under that rung's one direction. The kept set is the same for
   all three because the trim reads the targets, the raw items, the joined recipes
   and the registry, never the objective.
4. :func:`clockspeed.solve.strategy.rank_plans` ranks those optima once under the
   asked direction, with each rung's optimum as that rung's reference, and the top
   entry is the offer. Graded against its own ranking the top plan would clear every
   rung it can be priced on; graded this way its badge says what the plan really
   gives up.

THE MARKED ROUTE, ON A NO-PLAN AND ON NOTHING ELSE (CS-1371). A no-plan speaks only for
what the search kept, and a target is a free selector, so a world holding none of a chain
would otherwise read nothing at all. :func:`_redesign_offer`, the whole of the route the
item ruled and swappable as one function, takes
:func:`clockspeed.solve.bound.derived_route` over every automated recipe the join could
check, counting what the world does not hold first and all recipes second, so a recipe held
with no machine held cannot tie a route that runs now, and solves that route once with
:func:`clockspeed.solve.ratio.solve_for_targets` under the stated policy. It makes no second
bound call and no rung search, so no direction chooses the route and no badge can grade it.
WHERE PILLAR 1 REFUSES THAT ROUTE UNDER THE BALANCED POLICY (CS-1378),
:func:`clockspeed.solve.bound.route_with_consumers` adds one consumer per leftover byproduct
from the same pool, the route's own checked recipes, and the route plus those is solved once
more. A refusal of some other kind is refused again, and reads as the first did. A consumer the
world has not unlocked is offered locked, as any stage is, and a route solved on the first try
never reaches that step.
WHAT UNLOCKS A LOCKED STAGE (CS-1374). A schematic source handed to :func:`plan_offer` is asked
on this path alone, and its catalog does two things, both by WHOLE-STRING equality of an unlocked
recipe path with :attr:`clockspeed.data.registry.Recipe.asset_path` and never by a trailing token.
It names the PREFERRED recipes, those some schematic unlocking them carries a read ``mType`` token
that is not the hard-drive alternate's, and hands only that membership set to
:func:`clockspeed.solve.bound.derived_route`, never the catalog, so the route breaks a tie in
locked count toward them and no further. And it names, for each locked stage of the solved route,
every schematic unlocking it with its tech tier: the recipe's own where the world does not hold the
recipe, and where the world holds the recipe and no machine that runs it, the schematics
unlocking the first such machine's build recipe. The stages list in ascending order of the lowest
tier naming each, a stage naming no known tier last, then the plan's registry order, on
``plan.redesign.locked`` and ``plan.redesign.unlocks`` alike. A stage no schematic unlocks reads
``none``, or ``unknown`` where some schematic's unlocks could not be read in full, and an unlocked
path that joins no recipe is counted, never dropped. With no source, or one that publishes no
catalog, the route is today's and no reading is offered.

A stage the solve gives no machine count is neither held nor locked. ITS RAW ITEMS ARE NOT THE
SEARCH'S: it starts from every stated item some extractor joining a build recipe with a path
can extract, supplied or not, so a world missing a machine reads what to unlock rather than
nothing. For each raw item the route consumes, the first machine the world holds goes in the route's
unlock keys, and where it holds none the first that joins goes on
``plan.redesign.locked_extractors``, once each, sorted as ``raw_inputs`` is. The result goes to
``plan.redesign``, never to ``plan.adopt``: this is the one path where a recipe the world does
not hold reaches a rule as a stage of a plan, and it is named in the derivation alone.

THE NAMES OF THE TARGETS (CS-1379). A rule reads no registry, so :func:`_target_names` reads
each target's display name off ``registry.items`` and the offer carries it beside the plan
and beside the route, for tiers 1 and 2 to say a target by. An item the registry does not hold
and an empty name are each offered as None, and whether any other name can be printed is the
rule's to say. No join, no search and no card identity reads a name.

A POWER REFUSAL COSTS ONE RUNG, UNLESS POWER WAS ASKED. A recipe with no exact draw,
reached by the power search, makes that rung's reference None, which reads as not
comparable there and
leaves the other two rungs graded. Asked for by power there is no order to publish,
so the status is ``power-not-comparable``.

A DEAD-ENDED RUNG SEARCH IS A REFUSED SEARCH, NEVER NO-PLAN AND NEVER NOT COMPARABLE.
Under the greedy backend, a heuristic that never backtracks, the bound can solve and a
rung's own search over the kept set then find nothing, although the bound has just
shown a plan exists. No-plan would be false, and so would a None reference, which
arises from a power refusal alone and says a rung has no exact figure to compare, when a dead end
says only that this search found nothing to compare with. So any rung's dead end is
``solve-refused``, which says nothing about the target. Only the bound's own refusal
is ``no-plan``.

A REFUSAL IS A STATUS, NEVER A CRASH AND NEVER TEXT. Every refusal the solve layer
raises becomes one word of the closed vocabulary in
:mod:`clockspeed.advisor.rules.plan`. No exception's message is read: it can name a
recipe, a rate or an environment value (non-negotiable 13). A real world's search
costs seconds, and only a stated request pays it.

SEAMS. This module reads no file, no clock and no environment value of its own; the
one environment read is pillar 2's backend selection, and it renders nothing:
``plan.backend`` is the result's own field, never that value. It takes the unlock
state and never the world model, so the world token cannot reach it. NO FLOAT: every
rate and figure is an exact Fraction.
"""

from __future__ import annotations

import heapq
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, TypeGuard

from clockspeed.advisor.rules.plan import (
    BUILT_ENOUGH,
    BUILT_MORE,
    BUILT_REPLACE,
    BUILT_UNMEASURED,
    REASON_EMPTY_COST,
    REASON_ITEM_NOT_PLANNABLE,
    REDESIGN_NO_ROUTE,
    REDESIGN_NOT_REACHED,
    REDESIGN_ROUTE_REFUSED,
    STATUS_NO_PLAN,
    STATUS_NO_TARGET,
    STATUS_POWER_NOT_COMPARABLE,
    STATUS_REQUEST_MALFORMED,
    STATUS_SCHEMATIC_UNPLANNABLE,
    STATUS_SOLVE_REFUSED,
    UNLOCK_NAMED,
    UNLOCK_NONE,
    UNLOCK_UNKNOWN,
    UNPLANNABLE_REASONS,
    BuiltRow,
    LockedUnlock,
    RedesignBuilt,
    RedesignUnlocks,
    SchematicStatement,
    UnlockingSchematic,
    plan_inputs,
    redesign_inputs,
    redesign_status_inputs,
    refused_inputs,
    schematic_inputs,
    status_inputs,
)
from clockspeed.advisor.trace import RECIPE_UNLOCK_PREFIX, InputValue
from clockspeed.data.registry import (
    Registry,
    automated_recipes,
    build_cost,
    extractors_of,
    plan_targets,
)
from clockspeed.data.schematics import is_preferred, unlockers_by_path
from clockspeed.progress.milestones import milestone_requirement
from clockspeed.solve.bound import (
    BoundExhaustedError,
    derived_route,
    optimize_within_bound,
    route_with_consumers,
    trim_record,
)
from clockspeed.solve.carry import carry_of
from clockspeed.solve.exact import ExactArithmeticError, InexactValueError, to_exact
from clockspeed.solve.optimize import (
    OBJECTIVES,
    NoFeasibleSelectionError,
    Objective,
    ObjectiveUndefinedError,
    OptimizeError,
    OptimizeRequest,
    PowerNotComparableError,
    optimize_plan,
)
from clockspeed.solve.ratio import (
    BYPRODUCT_BALANCED,
    BYPRODUCT_POLICIES,
    ProductionPlan,
    RatioError,
    RatioRequest,
    solve_for_targets,
)
from clockspeed.solve.strategy import STRATEGY_LADDER, RankedPlan, Strategy, rank_plans

if TYPE_CHECKING:
    from clockspeed.audit.machines import MachineState, WorldMachines
    from clockspeed.data.schematics import Schematic, SchematicCatalog
    from clockspeed.progress.milestones import MilestoneRequirement, SchematicSource
    from clockspeed.save.world import UnlockState
    from clockspeed.solve.bound import TrimRecord

__all__ = [
    "PlanParameters",
    "PlanRequest",
    "SchematicParameters",
    "SchematicRequest",
    "plan_offer",
    "plan_offer_with_schematics",
    "plan_parameters",
    "plan_request_from",
    "schematic_parameters",
    "schematic_request_from",
]

#: The weight a search scores its one direction at.
_UNIT_WEIGHT: Final = Fraction(1)

#: A stated rate's spellings: an integer, an exact decimal or ``num/den``, in ASCII digits.
#: These are an ASCII-digit subset of the spellings ``clockspeed/surface/api/solve.py`` admits,
#: which this layer may not import, less its minus sign, because a rate at or below zero is
#: refused anyway. THE EXPONENT FORM IS ABSENT for the reason that module states. Applied with
#: ``fullmatch``, so a trailing newline cannot smuggle anything past it.
_RATE_SPELLING: Final = re.compile(r"[0-9]+(?:\.[0-9]+|/[0-9]+)?")

#: The longest stated rate read at all, so a caller cannot hand the parse an arbitrarily
#: long string. Far longer than any rate a machine counts to.
_MAX_RATE_TEXT: Final = 64


class _RungDeadEndError(OptimizeError):
    """The bound solved, and one rung's own search then found nothing.

    Not a no-plan: the bound has just found one. Raised and caught in this module,
    and it holds no text, so nothing it carries can reach a reader.
    """


@dataclass(frozen=True)
class _RecipeJoin:
    """What one world's unlocks make of the automated recipes: the join the module states.

    Holds the REGISTRY's strings alone, so nothing read out of a save reaches a repr.

    Attributes:
        held: The recipes the world holds, each with a machine to run it, in registry order.
        checked: The recipes the join could ask about, held or not, in registry order. The
            pool the marked route is derived from.
        unchecked: The rest, in registry order, which no search and no route sees.
        machine_of: For each held recipe, the whole path of the build recipe of the first of
            its machines the world holds. Read by key only.
        machine_locked: For each checked recipe the world holds and holds no machine of, the
            ClassName of the first machine that runs it and joins a build recipe with a path,
            and that build recipe's whole path (CS-1374). Read by key only.
    """

    held: tuple[str, ...]
    checked: tuple[str, ...]
    unchecked: tuple[str, ...]
    machine_of: Mapping[str, str]
    machine_locked: Mapping[str, tuple[str, str]] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(frozen=True)
class _RawSupply:
    """What one world's unlocks make of a request's raw items: the supply the module states.

    Holds the REGISTRY's strings alone, as :class:`_RecipeJoin` does. Every tuple keeps the
    stated order.

    Attributes:
        search: The raw items the search starts from: each one supplied, and any that is a
            target.
        route: The raw items the marked route starts from: each one an extractor joining a
            build recipe with a path can extract, supplied or not.
        unknown: The stated items no such extractor exists for, which neither of those holds
            unless the item is a target.
        machine_of: For each supplied item, the whole path of the build recipe of the first of
            its extractors the world holds. Read by key only.
        locked_machine_of: For each item on the route that is not supplied, the ClassName of
            the first of its extractors that joins. Read by key only.
    """

    search: tuple[str, ...]
    route: tuple[str, ...]
    unknown: tuple[str, ...]
    machine_of: Mapping[str, str]
    locked_machine_of: Mapping[str, str]


@dataclass(frozen=True)
class PlanRequest:
    """One stated question: what to make, out of what, and judged how.

    Every field is required, for the reason
    :class:`clockspeed.solve.optimize.OptimizeRequest` states: a default here would
    be this module saying something the caller never said.

    Attributes:
        targets: A mapping of item key to the wanted net rate per minute. Every key
            must be exactly a str and every rate exactly a Fraction above zero.
        raw_items: The items a world may draw without bound once it can extract them,
            exactly a tuple of str. What a world can extract is the join's to say, never the
            caller's.
        byproduct_policy: One of pillar 1's byproduct policies.
        direction: One member of :data:`clockspeed.solve.optimize.OBJECTIVES`. A
            direction and never a weighted objective: a weighted optimum may clear
            no rung, and then there is nothing true to advise.
    """

    targets: Mapping[str, Fraction]
    raw_items: tuple[str, ...]
    byproduct_policy: str
    direction: str


@dataclass(frozen=True)
class PlanParameters:
    """A stated rate, direction and byproduct policy, each already checked.

    Attributes:
        rate: The wanted net rate per minute, exactly a Fraction above zero.
        direction: One member of :data:`clockspeed.solve.optimize.OBJECTIVES`.
        byproduct_policy: One of pillar 1's byproduct policies.
    """

    rate: Fraction
    direction: str
    byproduct_policy: str


@dataclass(frozen=True)
class SchematicParameters:
    """A stated direction and byproduct policy for a schematic, each already checked.

    A schematic states no rate: each cost item's rate is its requirement's (CS-1373).

    Attributes:
        direction: One member of :data:`clockspeed.solve.optimize.OBJECTIVES`.
        byproduct_policy: One of pillar 1's byproduct policies.
    """

    direction: str
    byproduct_policy: str


@dataclass(frozen=True)
class SchematicRequest(PlanRequest):
    """One stated question about a whole schematic: its cost items as one route (CS-1373).

    A :class:`PlanRequest`, so every door that takes one takes this. ``targets`` are the cost
    items at the requirement's rates, and EMPTY on an unplannable statement, which
    :func:`plan_offer` answers before any join.

    Attributes:
        statement: What the schematic is, what it costs and what its requirement published.
    """

    statement: SchematicStatement


def _stated_rate(rate: object) -> Fraction | None:
    """Read a stated rate as an exact value, or refuse it.

    Args:
        rate: The rate as stated. Only exactly a str can pass.

    Returns:
        The exact value, handed to :class:`~fractions.Fraction` as text and never through
        a float, or None when it is not one of the admitted spellings or not above zero.
    """
    if type(rate) is not str or len(rate) > _MAX_RATE_TEXT:
        return None
    if _RATE_SPELLING.fullmatch(rate) is None:
        return None
    try:
        exact = to_exact(rate)
    except (ValueError, ZeroDivisionError):
        return None
    return exact if exact > 0 else None


def plan_parameters(*, rate: str, direction: str, byproduct_policy: str) -> PlanParameters | None:
    """Check what a caller stated, before any registry or provider is read.

    A refusal is None and only None: it carries no text and raises nothing, so nothing a
    caller typed can come back out of it (non-negotiable 12 applies to every echo path).

    Args:
        rate: An integer, an exact decimal or ``num/den``, in ASCII digits, above zero.
        direction: One member of :data:`clockspeed.solve.optimize.OBJECTIVES`.
        byproduct_policy: One of pillar 1's byproduct policies.

    Returns:
        The checked parameters, or None when any of the three is refused.
    """
    if not _known_mode(direction, byproduct_policy):
        return None
    exact = _stated_rate(rate)
    if exact is None:
        return None
    return PlanParameters(rate=exact, direction=direction, byproduct_policy=byproduct_policy)


def _known_mode(direction: object, byproduct_policy: object) -> bool:
    """Whether a direction and a byproduct policy are each exactly a known str.

    Args:
        direction: As stated.
        byproduct_policy: As stated.

    Returns:
        True for a member of :data:`clockspeed.solve.optimize.OBJECTIVES` and a member of
        pillar 1's policies, each exactly a str.
    """
    return (
        type(direction) is str
        and direction in OBJECTIVES
        and type(byproduct_policy) is str
        and byproduct_policy in BYPRODUCT_POLICIES
    )


def schematic_parameters(*, direction: str, byproduct_policy: str) -> SchematicParameters | None:
    """Check what a caller stated beside a schematic, before any provider is read (CS-1373).

    A refusal is None and only None, as :func:`plan_parameters` refuses.

    Args:
        direction: One member of :data:`clockspeed.solve.optimize.OBJECTIVES`.
        byproduct_policy: One of pillar 1's byproduct policies.

    Returns:
        The checked parameters, or None when either is refused.
    """
    if not _known_mode(direction, byproduct_policy):
        return None
    return SchematicParameters(direction=direction, byproduct_policy=byproduct_policy)


def plan_request_from(
    registry: Registry, target: str, parameters: PlanParameters
) -> PlanRequest | None:
    """Build the one request a stated target and checked parameters ask (CS-1371).

    The only place a stated request gets its raw items: they are the docs' published
    resource group, so no surface module chooses a raw item. An empty group is passed on
    as it stands, and :func:`plan_offer` reads that as a malformed request.

    Args:
        registry: The normalized registry.
        target: The item to plan for. Refused unless it is exactly a str that
            :func:`clockspeed.data.registry.plan_targets` lists.
        parameters: The checked rate, direction and policy.

    Returns:
        The request, or None when the target is not on the list. Reads the registry and
        runs no solve.
    """
    if type(target) is not str or target not in plan_targets(registry):
        return None
    return PlanRequest(
        targets=MappingProxyType({target: parameters.rate}),
        raw_items=registry.resource_items,
        byproduct_policy=parameters.byproduct_policy,
        direction=parameters.direction,
    )


def _statement_of(
    registry: Registry, schematic: str, requirement: MilestoneRequirement
) -> SchematicStatement | None:
    """State a schematic from its requirement, naming why it is unplannable where it is.

    Reads the requirement's cost and rates as published and derives neither.

    Args:
        registry: The normalized registry, whose ``plan_targets`` the cost items are tested
            against.
        schematic: The ClassName the caller stated.
        requirement: What ``milestone_requirement`` published for it.

    Returns:
        The statement, or None when the requirement names a reason outside the closed
        vocabulary, which includes the target being unknown to the catalog.
    """
    cost = None if requirement.cost is None else MappingProxyType(dict(requirement.cost))
    rates = None if requirement.rates is None else MappingProxyType(dict(requirement.rates))

    def stated(reason: str | None, items: tuple[str, ...] = ()) -> SchematicStatement:
        return SchematicStatement(
            schematic=schematic,
            tech_tier=requirement.tech_tier,
            cost=cost,
            budget_minutes=requirement.budget_minutes,
            rates=None if reason is not None else rates,
            unplannable=reason,
            unplannable_items=items,
        )

    if requirement.reason is not None:
        return stated(requirement.reason) if requirement.reason in UNPLANNABLE_REASONS else None
    if rates is None or not rates:
        return stated(REASON_EMPTY_COST)
    # A set, and ONLY as a membership test: the sort decides the order of what is named.
    listed = frozenset(plan_targets(registry))
    off = tuple(sorted(item for item in rates if item not in listed))
    if off:
        return stated(REASON_ITEM_NOT_PLANNABLE, off)
    return stated(None)


def schematic_request_from(
    catalog: SchematicCatalog,
    registry: Registry,
    unlocks: UnlockState,
    schematic: str,
    parameters: SchematicParameters,
) -> SchematicRequest | None:
    """Build the one request a stated schematic asks (CS-1373).

    Every cost item's rate is the requirement's, read and never recomputed or scaled, and every
    item is one target of the one request.

    Args:
        catalog: The normalized schematic catalog.
        registry: The normalized registry, whose published raw items the request takes and whose
            ``plan_targets`` the cost items are tested against.
        unlocks: The world's unlock state, which the requirement reads the HUB tier from and
            nothing else.
        schematic: The schematic's ClassName. Refused unless exactly a str the catalog holds.
        parameters: The checked direction and policy.

    Returns:
        The request, or None when the catalog does not hold the schematic. An unplannable
        schematic is a request carrying its reason and no targets. Runs no solve.
    """
    if type(schematic) is not str or schematic not in catalog.schematics:
        return None
    requirement = milestone_requirement(catalog, registry, unlocks, schematic)
    statement = _statement_of(registry, schematic, requirement)
    if statement is None:
        return None
    return SchematicRequest(
        targets=MappingProxyType({} if statement.rates is None else dict(statement.rates)),
        raw_items=registry.resource_items,
        byproduct_policy=parameters.byproduct_policy,
        direction=parameters.direction,
        statement=statement,
    )


def _well_formed(request: PlanRequest) -> bool:
    """Whether a request can be asked at all.

    Args:
        request: The request.

    Returns:
        True for one known direction, one known byproduct policy, raw items exactly a
        non-empty tuple of str and a mapping of at least one target, each key exactly a
        str and each rate exactly a Fraction above zero.
    """
    if request.direction not in OBJECTIVES or request.byproduct_policy not in BYPRODUCT_POLICIES:
        return False
    raw_items = request.raw_items
    if type(raw_items) is not tuple or not raw_items:
        return False
    if not all(type(item) is str for item in raw_items):
        return False
    targets = request.targets
    if not isinstance(targets, Mapping) or not all(type(item) is str for item in targets):
        return False
    rates = tuple(targets.values())
    return bool(rates) and all(type(rate) is Fraction and rate > 0 for rate in rates)


def _direction_objective(direction: str) -> Objective:
    """The objective scoring one direction at one and nothing else.

    Args:
        direction: A member of :data:`clockspeed.solve.optimize.OBJECTIVES`.

    Returns:
        The objective.
    """
    return Objective(weights=MappingProxyType({direction: _UNIT_WEIGHT}))


def _rung_optimum(
    registry: Registry, request: OptimizeRequest, strategy: Strategy, *, asked: str
) -> ProductionPlan | None:
    """The best plan over the kept set under one rung's own direction.

    Args:
        registry: The built registry.
        request: The search, over the kept set.
        strategy: The rung.
        asked: The direction the caller asked for.

    Returns:
        The plan, or None when the power search refused and the caller asked another
        direction: the rung has no exact figure to compare.

    Raises:
        PowerNotComparableError: The rung is the direction the caller asked for,
            so there is no order to publish.
        _RungDeadEndError: The rung's own search found nothing, on a set the bound
            has already solved.
        OptimizeError, ExactArithmeticError, ValueError: As
            :func:`clockspeed.solve.optimize.optimize_plan` raises them.
    """
    objective = _direction_objective(strategy.objective_name)
    try:
        return optimize_plan(registry, replace(request, objective=objective)).plan
    except PowerNotComparableError:
        if strategy.objective_name == asked:
            raise
        return None
    except NoFeasibleSelectionError:
        raise _RungDeadEndError from None


def _removed(record: TrimRecord | None) -> tuple[str, ...]:
    """Every recipe a record says the bound dropped.

    Args:
        record: The record, or None when nothing was dropped.

    Returns:
        The recipes in registry order, empty when nothing was dropped.
    """
    if record is None:
        return ()
    return tuple(name for step in record.steps for name in step.removed)


def _ranked_top(
    registry: Registry, request: PlanRequest, search: OptimizeRequest
) -> tuple[RankedPlan, str]:
    """Run the search of the module docstring over the joined recipes.

    Args:
        registry: The built registry.
        request: The request, already checked.
        search: The request as pillar 2 takes it, over the joined recipes.

    Returns:
        The top ranked entry, and the name the bound's result carries for the
        backend that ran.

    Raises:
        OptimizeError, ExactArithmeticError, ValueError, KeyError: Whatever the
            solve layer refuses with. :func:`plan_offer` reads each as a status.
    """
    bounded = optimize_within_bound(registry, search)
    kept = search
    if bounded.record is not None:
        survivors = bounded.record.steps[-1].kept
        kept = replace(search, candidates=survivors, unlocked=survivors)

    references = {
        strategy.name: _rung_optimum(registry, kept, strategy, asked=request.direction)
        for strategy in STRATEGY_LADDER
    }
    # A list and an equality scan, so the order is the ladder's and no set decides it.
    distinct: list[ProductionPlan] = []
    for plan in references.values():
        if plan is not None and plan not in distinct:
            distinct.append(plan)
    ranked = rank_plans(registry, distinct, objective=search.objective, references=references)
    return ranked[0], bounded.result.backend


def _keyable(path: str | None) -> TypeGuard[str]:
    """Whether an unlock key can carry a path: the engine's own test of a recommendation's text.

    Args:
        path: A recipe's asset path, or None when it carries none.

    Returns:
        True when it is printable ASCII with a visible character.
    """
    return path is not None and path.strip(" ") != "" and all(" " <= ch <= "~" for ch in path)


def _machine_paths(registry: Registry, machines: Iterable[str]) -> dict[str, str]:
    """Read the whole path of each machine's build recipe, once per machine.

    The name join :func:`clockspeed.data.registry.build_cost` publishes, which walks the
    registry on every call, so each machine is asked about once. A ``produced_in`` and
    :func:`clockspeed.data.registry.extractors_of` both name modeled buildings alone, so its
    refusal of an unmodeled one cannot arise here.

    Args:
        registry: The normalized registry.
        machines: The machines, in any order, each any number of times.

    Returns:
        Machine ClassName to path, the REGISTRY's string, for each machine with both a build
        recipe and a path on it that an unlock key can carry. Read by key only, so its insertion
        order decides nothing.
    """
    paths: dict[str, str] = {}
    for building in dict.fromkeys(machines):
        cost = build_cost(registry, building)
        path = None if cost is None else registry.recipes[cost.recipe_key].asset_path
        if _keyable(path):
            paths[building] = path
    return paths


def _recipe_join(registry: Registry, unlocks: UnlockState) -> _RecipeJoin:
    """Join the automated recipes against one world's unlocks, as the module docstring states.

    Args:
        registry: The normalized registry.
        unlocks: The world's unlock state. Its paths are compared by whole string, and none
            of them is kept.

    Returns:
        The join.
    """
    automated = automated_recipes(registry)
    machine_paths = _machine_paths(
        registry, (name for recipe in automated for name in recipe.produced_in)
    )
    held: list[str] = []
    checked: list[str] = []
    unchecked: list[str] = []
    machine_of: dict[str, str] = {}
    machine_locked: dict[str, tuple[str, str]] = {}
    for recipe in automated:
        # In produced_in's own order, so the first one held is read off the recipe.
        joined = tuple(
            (name, machine_paths[name]) for name in recipe.produced_in if name in machine_paths
        )
        if not _keyable(recipe.asset_path) or not joined:
            unchecked.append(recipe.key)
            continue
        checked.append(recipe.key)
        machine = next((path for _name, path in joined if path in unlocks.recipes), None)
        if machine is not None and recipe.asset_path in unlocks.recipes:
            held.append(recipe.key)
            machine_of[recipe.key] = machine
        elif machine is None and recipe.asset_path in unlocks.recipes:
            machine_locked[recipe.key] = joined[0]
    return _RecipeJoin(
        held=tuple(held),
        checked=tuple(checked),
        unchecked=tuple(unchecked),
        machine_of=MappingProxyType(machine_of),
        machine_locked=MappingProxyType(machine_locked),
    )


def _raw_supply(registry: Registry, request: PlanRequest, unlocks: UnlockState) -> _RawSupply:
    """Sort a request's raw items by what one world can extract, as the module docstring states.

    Args:
        registry: The normalized registry.
        request: The request, already checked, whose raw items and targets are read.
        unlocks: The world's unlock state. Its paths are compared by whole string, and none of
            them is kept.

    Returns:
        The supply.
    """
    extractors = {item: extractors_of(registry, item) for item in request.raw_items}
    machine_paths = _machine_paths(
        registry, (name for names in extractors.values() for name in names)
    )
    search: list[str] = []
    route: list[str] = []
    unknown: list[str] = []
    machine_of: dict[str, str] = {}
    locked_machine_of: dict[str, str] = {}
    for item in request.raw_items:
        # In extractors_of's own order, so the first one held is the docs' first.
        joined = tuple(name for name in extractors[item] if name in machine_paths)
        if joined:
            route.append(item)
        else:
            unknown.append(item)
        held = next(
            (machine_paths[name] for name in joined if machine_paths[name] in unlocks.recipes), None
        )
        if held is not None:
            machine_of[item] = held
        elif joined:
            locked_machine_of[item] = joined[0]
        if held is not None or item in request.targets:
            search.append(item)
    return _RawSupply(
        search=tuple(search),
        route=tuple(route),
        unknown=tuple(unknown),
        machine_of=MappingProxyType(machine_of),
        locked_machine_of=MappingProxyType(locked_machine_of),
    )


def _consumed(plan: ProductionPlan) -> tuple[str, ...]:
    """Name the raw items a plan consumes, which a loop giving back what it eats does not.

    Args:
        plan: A solved plan.

    Returns:
        The items with a rate above zero, in ``raw_inputs``'s own order, which pillar 1
        publishes sorted by key.
    """
    return tuple(item for item, rate in plan.raw_inputs.items() if rate > 0)


def _unlock_keys(
    registry: Registry, recipes: tuple[str, ...], join: _RecipeJoin
) -> tuple[str, ...]:
    """Name what some held recipes need unlocked: each one's key and its machine's.

    Args:
        registry: The normalized registry.
        recipes: Held recipes, in the order to read them.
        join: The join that found them held.

    Returns:
        The keys, each built from the REGISTRY's string and each once, in the order first
        seen. A mapping dedupes them, so no set decides that order.
    """
    return tuple(
        dict.fromkeys(
            f"{RECIPE_UNLOCK_PREFIX}{path}"
            for key in recipes
            for path in (registry.recipes[key].asset_path, join.machine_of[key])
        )
    )


def _plan_keys(
    registry: Registry,
    recipes: tuple[str, ...],
    plan: ProductionPlan,
    join: _RecipeJoin,
    supply: _RawSupply,
) -> tuple[str, ...]:
    """Name what a plan needs unlocked: its recipes' keys, then its supplied raw items' machines'.

    Args:
        registry: The normalized registry.
        recipes: The plan's held recipes, in the order to read them.
        plan: The plan, whose raw inputs say what it consumes.
        join: The join that found the recipes held.
        supply: The supply. A consumed item it holds no machine for names no key, which on the
            ranked path cannot arise, because the search starts from no such item.

    Returns:
        The keys, each built from the REGISTRY's string and each once, in the order first seen.
    """
    extractors = (
        f"{RECIPE_UNLOCK_PREFIX}{supply.machine_of[item]}"
        for item in _consumed(plan)
        if item in supply.machine_of
    )
    return tuple(dict.fromkeys((*_unlock_keys(registry, recipes, join), *extractors)))


def _target_names(
    registry: Registry, targets: Mapping[str, Fraction]
) -> MappingProxyType[str, str | None]:
    """Read each target's display name off the registry, which no rule can read itself.

    Args:
        registry: The normalized registry.
        targets: A plan's targets. Their rates are not read.

    Returns:
        Target ClassName to its display name, verbatim, read by key only. An item the
        registry does not hold and an empty display name each read None. Whether a name can
        be printed is the rule's to say.
    """
    items = registry.items
    return MappingProxyType(
        {key: (items[key].display_name or None) if key in items else None for key in targets}
    )


def _tier_rank(tier: int | None) -> tuple[bool, int]:
    """Order a tech tier ascending with an unknown tier after every known one.

    Args:
        tier: A schematic's tier, or None when none was read.

    Returns:
        ``(unknown, tier)``. An unknown tier is never treated as zero.
    """
    return (tier is None, 0 if tier is None else tier)


def _naming(
    unlockers: Mapping[str, tuple[Schematic, ...]], path: str | None
) -> tuple[UnlockingSchematic, ...]:
    """Name every schematic unlocking one recipe path, lowest tier first.

    Args:
        unlockers: As :func:`clockspeed.data.schematics.unlockers_by_path` builds them, keyed by
            whole path.
        path: The recipe's whole asset path, or None when it has none.

    Returns:
        Each schematic with its tier, in ascending tier, an unknown tier last, then ClassName.
        Empty when none unlocks it.
    """
    if path is None:
        return ()
    named = (UnlockingSchematic(s.class_name, s.tech_tier) for s in unlockers.get(path, ()))
    return tuple(sorted(named, key=lambda item: (*_tier_rank(item.tech_tier), item.schematic)))


def _route_unlocks(
    registry: Registry,
    catalog: SchematicCatalog,
    join: _RecipeJoin,
    locked: tuple[str, ...],
) -> RedesignUnlocks:
    """Name what unlocks each locked stage of a route, and count what joins no recipe.

    Args:
        registry: The normalized registry.
        catalog: The schematic catalog.
        join: The world's join, whose ``machine_locked`` says which stages are locked by their
            machine alone.
        locked: The route's locked stages, in the plan's registry order.

    Returns:
        One entry per stage, ordered by the lowest known tier among the schematics naming it,
        a stage naming none last, ties kept in ``locked``'s own order.
    """
    unlockers = unlockers_by_path(catalog)
    # A set, and ONLY as a membership test: a path any recipe carries is matched, and the count
    # is of the distinct paths no recipe carries.
    known = frozenset(recipe.asset_path for recipe in registry.recipes.values())
    unmatched = sum(1 for path in unlockers if path not in known)
    incomplete = any(not schematic.unlocks_complete for schematic in catalog.schematics.values())
    entries: list[LockedUnlock] = []
    for key in locked:
        by_machine = join.machine_locked.get(key)
        machine = None if by_machine is None else by_machine[0]
        path = registry.recipes[key].asset_path if by_machine is None else by_machine[1]
        named = _naming(unlockers, path)
        reading = UNLOCK_NAMED if named else UNLOCK_UNKNOWN if incomplete else UNLOCK_NONE
        entries.append(LockedUnlock(key, machine, reading, named))

    def lowest(index: int) -> tuple[bool, int, int]:
        tiers = [item.tech_tier for item in entries[index].schematics if item.tech_tier is not None]
        return (*_tier_rank(min(tiers) if tiers else None), index)

    order = sorted(range(len(entries)), key=lowest)
    return RedesignUnlocks(locked=tuple(entries[index] for index in order), unmatched=unmatched)


def _route_inputs(
    registry: Registry,
    plan: ProductionPlan,
    join: _RecipeJoin,
    supply: _RawSupply,
    catalog: SchematicCatalog | None = None,
    machines: WorldMachines | None = None,
) -> dict[str, InputValue]:
    """Sort a solved route's stages into held and locked, and offer it.

    A stage the solve gives no machine count is neither: nothing has to be built or unlocked
    for it, however the route's count reached it. Every list follows the plan's registry
    order.

    Args:
        registry: The normalized registry.
        plan: What pillar 1 solved for the route.
        join: The world's join.
        supply: The world's supply.
        catalog: The schematic catalog, or None where none was read, which offers no unlock
            reading and leaves the locked stages in the plan's registry order.
        machines: The audit machines model, or None where none was handed to the offer, which
            offers no comparison with what is built (CS-1375).

    Returns:
        The marked route's inputs. Its unlock keys are built as on the ranked path, of the
        held recipes and the supplied raw items alone, so a recipe locked by its machine and
        a raw item nothing here extracts name no key, and the latter's machine is named on
        its own input, once each.
    """
    # A set, and ONLY as a membership test: the plan's order decides every order here.
    holds = frozenset(join.held)
    stages = tuple(step.recipe_key for step in plan.steps if step.machines != 0)
    held = tuple(key for key in stages if key in holds)
    locked = tuple(key for key in stages if key not in holds)
    unlocks = None if catalog is None else _route_unlocks(registry, catalog, join, locked)
    return redesign_inputs(
        plan,
        held=held,
        locked=locked if unlocks is None else tuple(entry.recipe for entry in unlocks.locked),
        locked_extractors=tuple(
            dict.fromkeys(
                supply.locked_machine_of[item]
                for item in _consumed(plan)
                if item in supply.locked_machine_of
            )
        ),
        requires=_plan_keys(registry, held, plan, join, supply),
        target_names=_target_names(registry, plan.targets),
        unlocks=unlocks,
        built=None if machines is None else _compare_built(registry, plan, machines),
    )


def _capacity_of(state: MachineState) -> Fraction | None:
    """Read one built machine's capacity, which is its exact overclock where that is known.

    Args:
        state: The machine, as the audit publishes it.

    Returns:
        None when a production boost is tagged, whatever the clock, because a boost changes what
        a clock means and none is modeled; the exact overclock where one was read; 1 where the
        overclock was elided, which is the shape the serializer writes for the class default;
        and None where it was never read. An overclock that is not exactly a non-negative
        Fraction is unknown, never coerced.
    """
    if state.production_boost_tagged:
        return None
    clock = state.overclock
    if clock is not None:
        return clock if type(clock) is Fraction and clock >= 0 else None
    return Fraction(1) if state.overclock_elided else None


def _components(successors: list[list[int]]) -> list[list[int]]:
    """Group a graph's nodes into strongly connected components, each sorted ascending.

    Iterative Tarjan, so a long chain cannot overflow the stack.

    Args:
        successors: For each node, the nodes it points at.

    Returns:
        The components, a single node on none of its own cycles being a component of one.
    """
    size = len(successors)
    number = [-1] * size
    low = [0] * size
    open_ = [False] * size
    stack: list[int] = []
    found: list[list[int]] = []
    counter = 0
    for root in range(size):
        if number[root] != -1:
            continue
        work = [(root, 0)]
        while work:
            node, start = work.pop()
            if start == 0:
                number[node] = low[node] = counter
                counter += 1
                stack.append(node)
                open_[node] = True
            descended = False
            for position in range(start, len(successors[node])):
                nxt = successors[node][position]
                if number[nxt] == -1:
                    work.append((node, position + 1))
                    work.append((nxt, 0))
                    descended = True
                    break
                if open_[nxt]:
                    low[node] = min(low[node], number[nxt])
            if descended:
                continue
            if low[node] == number[node]:
                members: list[int] = []
                while True:
                    member = stack.pop()
                    open_[member] = False
                    members.append(member)
                    if member == node:
                        break
                found.append(sorted(members))
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
    return found


def _producers_first(
    registry: Registry, stages: tuple[str, ...]
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    """Order a route's stages so each precedes every stage consuming one of its outputs.

    A stage consuming its own output is no edge: it precedes nothing by it. Ties go to the
    stage listed first in ``stages``, which is the route's registry order. A loop's members
    stay together, in that same order, after every stage outside the loop that feeds it.

    Args:
        registry: The normalized registry, whose recipes name each stage's items.
        stages: The stages, in registry order.

    Returns:
        The stages producers first, then each loop of more than one stage, its members in
        registry order, in the order the loops appear in the first.
    """
    # Sets, and ONLY as a membership test: an intersection is read for being empty or not.
    makes = [frozenset(io.item_key for io in registry.recipes[key].outputs) for key in stages]
    eats = [frozenset(io.item_key for io in registry.recipes[key].inputs) for key in stages]
    successors = [
        [other for other in range(len(stages)) if other != node and makes[node] & eats[other]]
        for node in range(len(stages))
    ]
    components = _components(successors)
    owner = {member: number for number, members in enumerate(components) for member in members}
    # Sorted, so the order never rests on a hash.
    edges = sorted(
        {
            (owner[node], owner[other])
            for node, others in enumerate(successors)
            for other in others
            if owner[node] != owner[other]
        }
    )
    waiting = [0] * len(components)
    follows: list[list[int]] = [[] for _ in components]
    for before, after in edges:
        waiting[after] += 1
        follows[before].append(after)
    ready = [
        (components[number][0], number) for number in range(len(components)) if not waiting[number]
    ]
    heapq.heapify(ready)
    order: list[int] = []
    while ready:
        _first, number = heapq.heappop(ready)
        order.append(number)
        for after in follows[number]:
            waiting[after] -= 1
            if not waiting[after]:
                heapq.heappush(ready, (components[after][0], after))
    keys = tuple(stages[member] for number in order for member in components[number])
    loops = tuple(
        tuple(stages[member] for member in components[number])
        for number in order
        if len(components[number]) > 1
    )
    return keys, loops


def _compare_built(
    registry: Registry, plan: ProductionPlan, machines: WorldMachines
) -> RedesignBuilt:
    """Read a solved route against the machines the world has built (CS-1375).

    A stage is a step of the route with a nonzero machine count. Its built capacity is the sum
    of the exact capacities of the machines naming its recipe, and the route's count is at clock
    1, so the shortfall is the one minus the other. ``solve/`` sees no machine: this runs after
    the route is solved, on its result.

    Args:
        registry: The normalized registry.
        plan: What pillar 1 solved for the route.
        machines: The audit machines model. Read, never kept.

    Returns:
        The rows, replace first and then the stages producers first, and the counts of what was
        read and not compared. With no recipe tag on any machine every stage reads unmeasured
        and no recipe reads replace: nothing is known of what is built, and an empty answer
        would read as a world with nothing built.
    """
    built: dict[str, list[Fraction | None]] = {}
    untagged = 0
    unregistered = 0
    for state in machines.machines:
        name = state.recipe_class_name
        if name is None:
            untagged += 1
        elif name not in registry.recipes:
            unregistered += 1
        else:
            built.setdefault(name, []).append(_capacity_of(state))
    measured = untagged < len(machines.machines)
    counts = {step.recipe_key: step.machines for step in plan.steps if step.machines != 0}
    ordered, loops = _producers_first(registry, tuple(counts))
    # A set, and ONLY as a membership test: registry order decides every order here.
    outputs = frozenset(io.item_key for key in ordered for io in registry.recipes[key].outputs)
    rows: list[BuiltRow] = []
    for key, recipe in registry.recipes.items():
        if (
            key in built
            and key not in counts
            and any(io.item_key in outputs for io in recipe.outputs)
        ):
            rows.append(BuiltRow(key, BUILT_REPLACE, None, len(built[key]), None, None, 0))
    for key in ordered:
        capacities = built.get(key, [])
        unknown = sum(1 for capacity in capacities if capacity is None)
        count = counts[key]
        if not measured or unknown:
            rows.append(
                BuiltRow(key, BUILT_UNMEASURED, count, len(capacities), None, None, unknown)
            )
            continue
        capacity = sum((c for c in capacities if c is not None), start=Fraction(0))
        shortfall = count - capacity
        if shortfall > 0:
            rows.append(BuiltRow(key, BUILT_MORE, count, len(capacities), capacity, shortfall, 0))
        else:
            rows.append(BuiltRow(key, BUILT_ENOUGH, count, len(capacities), capacity, None, 0))
    return RedesignBuilt(
        rows=tuple(rows),
        measured=measured,
        cycles=loops,
        refused_recipe_tags=machines.refused_recipe_count,
        unregistered_machines=unregistered,
        untagged_machines=untagged,
    )


def _solve_route(
    registry: Registry, search: OptimizeRequest, members: tuple[str, ...], supply: _RawSupply
) -> ProductionPlan:
    """Solve these recipes once, for the search's targets and policy, from the route's raw items.

    Args:
        registry: The normalized registry.
        search: The request the search ran on, whose targets and policy are read.
        members: The recipes to solve, in the order to hand pillar 1.
        supply: The world's supply: the solve starts from its route items.

    Returns:
        What pillar 1 solved.

    Raises:
        RatioError: Pillar 1 refuses the recipes, as :func:`solve_for_targets` raises it.
    """
    return solve_for_targets(
        registry,
        RatioRequest(
            targets=search.targets,
            recipes=members,
            raw_items=supply.route,
            byproduct_policy=search.byproduct_policy,
        ),
    )


def _preferred(registry: Registry, catalog: SchematicCatalog, join: _RecipeJoin) -> frozenset[str]:
    """Name the checked recipes to prefer: some schematic unlocking each carries a read other token.

    Args:
        registry: The normalized registry.
        catalog: The schematic catalog.
        join: The world's join, whose checked recipes are the pool.

    Returns:
        The membership set :func:`derived_route` takes, joined by whole path.
    """
    unlockers = unlockers_by_path(catalog)
    return frozenset(
        key
        for key in join.checked
        if (path := registry.recipes[key].asset_path) is not None
        and is_preferred(unlockers.get(path, ()))
    )


def _redesign_offer(
    registry: Registry,
    search: OptimizeRequest,
    *,
    join: _RecipeJoin,
    supply: _RawSupply,
    schematics: SchematicSource | None = None,
    machines: WorldMachines | None = None,
) -> dict[str, InputValue]:
    """Derive one route over every automated recipe the join could check, and solve it.

    The route CS-1371 ruled, kept whole in this function so it stays swappable: the marked
    route of the module docstring. It reads what :func:`plan_offer` searched for, and makes
    no second bound call and no rung search. Where pillar 1 refuses that route under the
    balanced policy it solves once more, over the route and one consumer per leftover
    byproduct (CS-1378); any other route is solved the once.

    Args:
        registry: The normalized registry.
        search: The request the search ran on, whose targets and policy the route takes.
            Its rates are exact: :func:`_well_formed` has checked them. Its raw items are the
            supplied ones alone, so the route never reads them.
        join: The world's join: its checked recipes are the pool, and the route's count
            prefers its held ones, each of which has a machine the world holds.
        supply: The world's supply: the route starts from its route items, supplied or not.
        schematics: Where the schematic catalog comes from, or None. Asked here and nowhere
            else, once. Its catalog yields the preferred set the route breaks a tie by and the
            reading of what unlocks each locked stage; none yields neither (CS-1374).
        machines: The audit machines model the route is compared with, or None for no
            comparison (CS-1375). Read, never kept.

    Returns:
        The marked route's inputs. Every refusal is a status, read by no message: no route
        when the count misses some target, and refused when pillar 1 refuses the route, or
        refuses it again with its consumers, or the consumer step finds none. The catches
        are :func:`plan_offer`'s, for the reason it gives, and ``RatioError`` beside them,
        because this calls pillar 1 itself where the search reaches it through pillar 2,
        which reads that refusal as no selection.
    """
    try:
        asked = replace(
            search, candidates=join.checked, unlocked=join.checked, raw_items=supply.route
        )
        held = frozenset(join.held)
        catalog = None if schematics is None else schematics.catalog()
        preferred = None if catalog is None else _preferred(registry, catalog, join)
        route = derived_route(registry, asked, held=held, preferred=preferred)
        if not route.complete:
            return redesign_status_inputs(REDESIGN_NO_ROUTE, unmade=route.unmade)
        try:
            plan = _solve_route(registry, search, route.members, supply)
        except RatioError:
            if search.byproduct_policy != BYPRODUCT_BALANCED:
                raise
            # CS-1378: one consumer per leftover byproduct, then one more solve.
            members = route_with_consumers(registry, asked, route, held=held, preferred=preferred)
            plan = _solve_route(registry, search, members, supply)
    except (RatioError, OptimizeError, ExactArithmeticError, ValueError, KeyError):
        return redesign_status_inputs(REDESIGN_ROUTE_REFUSED, unmade=None)
    return _route_inputs(registry, plan, join, supply, catalog, machines)


def plan_offer(
    unlocks: UnlockState, registry: Registry, request: PlanRequest | None
) -> dict[str, InputValue]:
    """Answer one request as :func:`plan_offer_with_schematics` does, with no schematic source.

    The unchanged three-argument door: it offers no unlock reading, prefers no recipe and
    compares nothing with what is built, so the route is the one CS-1371 ruled.

    Args:
        unlocks: The world's unlock state.
        registry: The normalized registry.
        request: The question, or None when the caller stated none.

    Returns:
        As :func:`plan_offer_with_schematics` returns it with None for the source.
    """
    return plan_offer_with_schematics(unlocks, registry, request, None)


def plan_offer_with_schematics(
    unlocks: UnlockState,
    registry: Registry,
    request: PlanRequest | None,
    schematics: SchematicSource | None,
    *,
    machines: WorldMachines | None = None,
) -> dict[str, InputValue]:
    """Answer one request with the inputs the plan family reads, and the schematic it names.

    A :class:`SchematicRequest` is answered as the :class:`PlanRequest` it is, or, where its
    statement is unplannable, with the status that says so and no join (CS-1373). Every answer
    carries :data:`clockspeed.advisor.rules.plan.IN_SCHEMATIC`, None where none was stated.

    Args:
        unlocks: The world's unlock state.
        registry: The normalized registry.
        request: The question, or None when the caller stated none.
        schematics: Where the schematic catalog comes from, or None for none. Asked only where
            a route is derived (CS-1374), so a ranked plan, a refusal and a request with no
            target never read it.
        machines: The audit machines model the marked route is compared with (CS-1375), or None
            for no comparison. ``solve/`` never sees it: the comparison is made here, after the
            route is solved.

    Returns:
        As :func:`_offer` returns, beside the schematic input.
    """
    statement = request.statement if isinstance(request, SchematicRequest) else None
    if statement is not None and statement.unplannable is not None:
        offered = status_inputs(STATUS_SCHEMATIC_UNPLANNABLE)
    else:
        offered = _offer(unlocks, registry, request, schematics, machines)
    return {**offered, **schematic_inputs(statement)}


def _offer(
    unlocks: UnlockState,
    registry: Registry,
    request: PlanRequest | None,
    schematics: SchematicSource | None,
    machines: WorldMachines | None = None,
) -> dict[str, InputValue]:
    """Answer one request with the inputs the plan family reads.

    Reads no file and no clock. Never raises for a solve refusal: each one is a
    status. So is a KeyError or ValueError from anywhere in the search, even one
    that is a bug in this tree, because neither can be told from a refusal; only a
    type outside the catches raises.

    Args:
        unlocks: The world's unlock state. Its paths are compared and counted, and
            none of them is kept or rendered.
        registry: The normalized registry.
        request: The question, or None when the caller stated none.
        schematics: Where the schematic catalog comes from, or None. Passed to the route and
            asked nowhere else.
        machines: The audit machines model, passed to the route and read nowhere else.

    Returns:
        A fresh dict of rule inputs: the status alone when no join ran, the status
        and what the join and the bound left out when no plan was ranked, and all of
        it beside the plan and its targets' names when one was. Every path offers the
        marked route's inputs beside those, reading not reached on every status but
        no-plan, which alone runs the route.
    """
    if request is None:
        return status_inputs(STATUS_NO_TARGET)
    if not _well_formed(request):
        return status_inputs(STATUS_REQUEST_MALFORMED)

    join = _recipe_join(registry, unlocks)
    supply = _raw_supply(registry, request, unlocks)
    # A set, and ONLY as a membership test. A path joining any recipe, automated or
    # not, is not unmatched: the count is of paths the docs do not know.
    known = frozenset(recipe.asset_path for recipe in registry.recipes.values())
    unmatched = sum(1 for path in unlocks.recipes if path not in known)

    trimmed: tuple[str, ...] = ()
    try:
        search = OptimizeRequest(
            targets=MappingProxyType(dict(request.targets)),
            candidates=join.held,
            unlocked=join.held,
            raw_items=supply.search,
            byproduct_policy=request.byproduct_policy,
            objective=_direction_objective(request.direction),
        )
        trimmed = _removed(trim_record(registry, search))
        top, backend = _ranked_top(registry, request, search)
    except BoundExhaustedError as refused:
        status = STATUS_NO_PLAN
        trimmed = _removed(refused.record)
    except NoFeasibleSelectionError:
        status = STATUS_NO_PLAN
    except PowerNotComparableError:
        status = STATUS_POWER_NOT_COMPARABLE
    except (ObjectiveUndefinedError, InexactValueError, ValueError):
        status = STATUS_REQUEST_MALFORMED
    except (OptimizeError, ExactArithmeticError, KeyError):
        status = STATUS_SOLVE_REFUSED
    else:
        return {
            **plan_inputs(
                top,
                requires=_plan_keys(
                    registry,
                    tuple(step.recipe_key for step in top.plan.steps),
                    top.plan,
                    join,
                    supply,
                ),
                trimmed=trimmed,
                unchecked=join.unchecked,
                raw_unknown=supply.unknown,
                unmatched_unlocks=unmatched,
                backend=backend,
                target_names=_target_names(registry, top.plan.targets),
                carry=carry_of(top.plan.edges, registry.transports),
            ),
            **redesign_status_inputs(REDESIGN_NOT_REACHED, unmade=None),
        }
    route = (
        _redesign_offer(
            registry,
            search,
            join=join,
            supply=supply,
            schematics=schematics,
            machines=machines,
        )
        if status == STATUS_NO_PLAN
        else redesign_status_inputs(REDESIGN_NOT_REACHED, unmade=None)
    )
    return {
        **refused_inputs(
            status,
            trimmed=trimmed,
            unchecked=join.unchecked,
            raw_unknown=supply.unknown,
            unmatched_unlocks=unmatched,
        ),
        **route,
    }
