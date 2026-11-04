"""CS-1351 and CS-1371: answer a stated target, with a ranked plan or a marked route.

WHAT THIS MODULE OWNS. :class:`PlanRequest`, the question a caller states;
:func:`plan_parameters` and :func:`plan_request_from`, the door a stated rate, direction,
policy and target come in through; and :func:`plan_offer`, which answers the question with
the rule inputs :mod:`clockspeed.advisor.rules.plan` reads.
:func:`clockspeed.advisor.advise.inputs_of` calls it on every world; with no request it does
no work beyond naming the status.

THE TARGET IS THE CALLER'S, AND NO SURFACE STATES ONE YET. Nothing here chooses
what to plan for: a world has no single target, and the milestone target is a free
selector (CLAUDE.md section 7). A request carries one direction from
:data:`clockspeed.solve.optimize.OBJECTIVES` and no weighted objective, so the top
plan is always one rung's own optimum and clears that rung.

THE JOIN. A plan names recipes by registry ClassName and a save names unlocked
recipes by asset path. The registry publishes each recipe's path, the path half of
its docs ``FullName``, on :attr:`clockspeed.data.registry.Recipe.asset_path`, and
:func:`plan_offer` compares that with each member of
:attr:`clockspeed.save.world.UnlockState.recipes` by WHOLE STRING. It is never cut
to a trailing token (CS-1343) and never rebuilt from a ClassName. A recipe joins
only if it is automated too: a recipe no machine runs cannot be built by a plan,
and a raw search picks one wherever it is cheapest, because raw consumption never
asks what runs a recipe.

WHAT THE JOIN LEAVES OUT IS SAID, NOT DROPPED (non-negotiable 7). An automated
recipe with no path can never be shown unlocked, so it never enters a search or a
route and is named on ``plan.unchecked``, so no plan can cover a recipe nobody checked. An
unlocked path that joins no recipe is COUNTED on ``plan.unmatched_unlocks``, and
that count is all that crosses: a save's own path never reaches an input, a step,
a card, a repr or an exception (non-negotiables 11 and 12). The unlock keys a plan
requires are built from the REGISTRY's string, which a reader may see, and never
from the member it compared equal to.

THE SEARCH, IN ORDER.

1. The request is checked: one known direction, one known byproduct policy, raw
   items exactly a non-empty tuple of str, and a mapping of at least one target, every
   key exactly a str and every rate exactly a Fraction above zero. A zero-rate Build card
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
:func:`clockspeed.solve.bound.derived_route` over every automated recipe carrying a path,
counting what the world has not joined first and all recipes second, and solves that route
once with
:func:`clockspeed.solve.ratio.solve_for_targets` under the stated policy. It makes no second
bound call and no rung search, so no direction chooses the route and no badge can grade it.
A stage the solve gives no machine is neither held nor locked. The result goes to
``plan.redesign``, never to ``plan.adopt``: this is the one path where a recipe the world has
not unlocked reaches a rule as a stage of a plan, and it is named in the derivation alone.

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

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.rules.plan import (
    REDESIGN_NO_ROUTE,
    REDESIGN_NOT_REACHED,
    REDESIGN_ROUTE_REFUSED,
    STATUS_NO_PLAN,
    STATUS_NO_TARGET,
    STATUS_POWER_NOT_COMPARABLE,
    STATUS_REQUEST_MALFORMED,
    STATUS_SOLVE_REFUSED,
    plan_inputs,
    redesign_inputs,
    redesign_status_inputs,
    refused_inputs,
    status_inputs,
)
from clockspeed.advisor.trace import RECIPE_UNLOCK_PREFIX, InputValue
from clockspeed.data.registry import Registry, automated_recipes, plan_targets
from clockspeed.solve.bound import (
    BoundExhaustedError,
    derived_route,
    optimize_within_bound,
    trim_record,
)
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
    BYPRODUCT_POLICIES,
    ProductionPlan,
    RatioError,
    RatioRequest,
    solve_for_targets,
)
from clockspeed.solve.strategy import STRATEGY_LADDER, RankedPlan, Strategy, rank_plans

if TYPE_CHECKING:
    from clockspeed.save.world import UnlockState
    from clockspeed.solve.bound import TrimRecord

__all__ = [
    "PlanParameters",
    "PlanRequest",
    "plan_offer",
    "plan_parameters",
    "plan_request_from",
]

#: The weight a search scores its one direction at.
_UNIT_WEIGHT: Final = Fraction(1)

#: A stated rate's spellings: an integer, an exact decimal or ``num/den``, in ASCII digits.
#: These are the spellings ``clockspeed/surface/api/solve.py`` admits, which this layer
#: may not import, less its minus sign, because a rate at or below zero is refused anyway.
#: THE EXPONENT FORM IS ABSENT for the reason that module states. Applied with
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
class PlanRequest:
    """One stated question: what to make, out of what, and judged how.

    Every field is required, for the reason
    :class:`clockspeed.solve.optimize.OptimizeRequest` states: a default here would
    be this module saying something the caller never said.

    Attributes:
        targets: A mapping of item key to the wanted net rate per minute. Every key
            must be exactly a str and every rate exactly a Fraction above zero.
        raw_items: Items available without bound, exactly a tuple of str.
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
    if type(direction) is not str or direction not in OBJECTIVES:
        return None
    if type(byproduct_policy) is not str or byproduct_policy not in BYPRODUCT_POLICIES:
        return None
    exact = _stated_rate(rate)
    if exact is None:
        return None
    return PlanParameters(rate=exact, direction=direction, byproduct_policy=byproduct_policy)


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


def _route_inputs(
    registry: Registry, plan: ProductionPlan, joined: tuple[str, ...]
) -> dict[str, InputValue]:
    """Sort a solved route's stages into held and locked, and offer it.

    A stage the solve gives no machine is neither: nothing has to be built or unlocked for
    it, however the route's count reached it. Every list follows the plan's registry order.

    Args:
        registry: The normalized registry.
        plan: What pillar 1 solved for the route.
        joined: The recipes the world holds.

    Returns:
        The marked route's inputs. Its unlock keys are built from the REGISTRY's string by
        the whole path, as on the ranked path, and of the held recipes alone.
    """
    # A set, and ONLY as a membership test: the plan's order decides every order here.
    holds = frozenset(joined)
    stages = tuple(step.recipe_key for step in plan.steps if step.machines != 0)
    held = tuple(key for key in stages if key in holds)
    return redesign_inputs(
        plan,
        held=held,
        locked=tuple(key for key in stages if key not in holds),
        requires=tuple(f"{RECIPE_UNLOCK_PREFIX}{registry.recipes[key].asset_path}" for key in held),
    )


def _redesign_offer(
    registry: Registry, search: OptimizeRequest, *, joined: tuple[str, ...]
) -> dict[str, InputValue]:
    """Derive one route over every automated recipe with a path, and solve it once.

    The route CS-1371 ruled, kept whole in this function so it stays swappable: the marked
    route of the module docstring. It reads what :func:`plan_offer` searched for, and makes
    no second bound call and no rung search.

    Args:
        registry: The normalized registry.
        search: The request the search ran on, whose targets, raw items and policy the
            route takes. Its rates are exact: :func:`_well_formed` has checked them.
        joined: The recipes the world holds, which the route's count prefers.

    Returns:
        The marked route's inputs. Every refusal is a status, read by no message: no route
        when the count reaches no target, and refused when pillar 1 refuses the route.
        The catches are :func:`plan_offer`'s, for the reason it gives, and ``RatioError``
        beside them, because this calls pillar 1 itself where the search reaches it through
        pillar 2, which reads that refusal as no selection.
    """
    pathed = tuple(
        recipe.key for recipe in automated_recipes(registry) if recipe.asset_path is not None
    )
    try:
        route = derived_route(
            registry,
            replace(search, candidates=pathed, unlocked=pathed),
            held=frozenset(joined),
        )
        if not route.complete:
            return redesign_status_inputs(REDESIGN_NO_ROUTE, unmade=route.unmade)
        plan = solve_for_targets(
            registry,
            RatioRequest(
                targets=search.targets,
                recipes=route.members,
                raw_items=search.raw_items,
                byproduct_policy=search.byproduct_policy,
            ),
        )
    except (RatioError, OptimizeError, ExactArithmeticError, ValueError, KeyError):
        return redesign_status_inputs(REDESIGN_ROUTE_REFUSED, unmade=None)
    return _route_inputs(registry, plan, joined)


def plan_offer(
    unlocks: UnlockState, registry: Registry, request: PlanRequest | None
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

    Returns:
        A fresh dict of rule inputs: the status alone when no join ran, the status
        and what the join and the bound left out when no plan was ranked, and all of
        it beside the plan when one was. Every path offers the marked route's inputs
        beside those, reading not reached on every status but no-plan, which alone
        runs the route.
    """
    if request is None:
        return status_inputs(STATUS_NO_TARGET)
    if not _well_formed(request):
        return status_inputs(STATUS_REQUEST_MALFORMED)

    automated = automated_recipes(registry)
    joined = tuple(recipe.key for recipe in automated if recipe.asset_path in unlocks.recipes)
    unchecked = tuple(recipe.key for recipe in automated if recipe.asset_path is None)
    # A set, and ONLY as a membership test. A path joining any recipe, automated or
    # not, is not unmatched: the count is of paths the docs do not know.
    known = frozenset(recipe.asset_path for recipe in registry.recipes.values())
    unmatched = sum(1 for path in unlocks.recipes if path not in known)

    trimmed: tuple[str, ...] = ()
    try:
        search = OptimizeRequest(
            targets=MappingProxyType(dict(request.targets)),
            candidates=joined,
            unlocked=joined,
            raw_items=request.raw_items,
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
        requires = tuple(
            f"{RECIPE_UNLOCK_PREFIX}{registry.recipes[step.recipe_key].asset_path}"
            for step in top.plan.steps
        )
        return {
            **plan_inputs(
                top,
                requires=requires,
                trimmed=trimmed,
                unchecked=unchecked,
                unmatched_unlocks=unmatched,
                backend=backend,
            ),
            **redesign_status_inputs(REDESIGN_NOT_REACHED, unmade=None),
        }
    route = (
        _redesign_offer(registry, search, joined=joined)
        if status == STATUS_NO_PLAN
        else redesign_status_inputs(REDESIGN_NOT_REACHED, unmade=None)
    )
    return {
        **refused_inputs(status, trimmed=trimmed, unchecked=unchecked, unmatched_unlocks=unmatched),
        **route,
    }
