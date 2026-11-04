"""CS-1351: rank a plan for a stated target over the recipes a world has unlocked.

WHAT THIS MODULE OWNS. :class:`PlanRequest`, the question a caller states, and
:func:`plan_offer`, which answers it with the rule inputs
:mod:`clockspeed.advisor.rules.plan` reads. :func:`clockspeed.advisor.advise.inputs_of`
calls it on every world; with no request it does no work beyond naming the status.

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
recipe with no path can never be shown unlocked, so it never enters a search and
is named on ``plan.unchecked``, so no plan can cover a recipe nobody checked. An
unlocked path that joins no recipe is COUNTED on ``plan.unmatched_unlocks``, and
that count is all that crosses: a save's own path never reaches an input, a step,
a card, a repr or an exception (non-negotiables 11 and 12). The unlock keys a plan
requires are built from the REGISTRY's string, which a reader may see, and never
from the member it compared equal to.

THE SEARCH, IN ORDER.

1. The request is checked: one known direction, one known byproduct policy, raw
   items exactly a tuple of str, and at least one target, every rate exactly a
   Fraction above zero. A zero-rate Build card is absurd, and an unknown policy or a
   str of raw items reaches pillar 2 as no selection at all, which would read as a
   false no-plan.
2. :func:`clockspeed.solve.bound.optimize_within_bound` answers feasibility over the
   kept set, and the trim. A real world joins more recipes than the exhaustive
   backend's cap, so a whole-set search would refuse. ``plan.trimmed`` names what the
   bound dropped, on every status a search reached: a no-plan speaks only for the
   kept set, and what the cap drops is a rule over the targets and registry order, so
   it stays true however the search then ends.
3. :func:`clockspeed.solve.optimize.optimize_plan` runs once per ladder rung over
   the kept set, each under that rung's one direction. The kept set is the same for
   all three because the trim reads the targets and registry order, never the
   objective.
4. :func:`clockspeed.solve.strategy.rank_plans` ranks those optima once under the
   asked direction, with each rung's optimum as that rung's reference, and the top
   entry is the offer. Graded against its own ranking the top plan would clear every
   rung it can be priced on; graded this way its badge says what the plan really
   gives up.

A POWER REFUSAL COSTS ONE RUNG, UNLESS POWER WAS ASKED. A recipe with no exact draw,
reached by the power search, makes that rung's reference None, which reads as not
comparable there and
leaves the other two rungs graded. Asked for by power there is no order to publish,
so the status is ``power-not-comparable``.

A DEAD-ENDED RUNG SEARCH COSTS ONE RUNG TOO, AND NEVER READS AS NO-PLAN. Under the
greedy backend, a heuristic that never backtracks, the bound can solve and a rung's
own search over the kept set then find nothing, although the bound has just shown a
plan exists. So a rung other than the asked direction takes the power refusal's
shape, its reference None, and the asked rung itself is ``solve-refused``, which says
nothing about the target. Only the bound's own refusal is ``no-plan``.

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

from dataclasses import dataclass, replace
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.rules.plan import (
    STATUS_NO_PLAN,
    STATUS_NO_TARGET,
    STATUS_POWER_NOT_COMPARABLE,
    STATUS_REQUEST_MALFORMED,
    STATUS_SOLVE_REFUSED,
    plan_inputs,
    refused_inputs,
    status_inputs,
)
from clockspeed.advisor.trace import RECIPE_UNLOCK_PREFIX, InputValue
from clockspeed.data.registry import Registry, automated_recipes
from clockspeed.solve.bound import BoundExhaustedError, optimize_within_bound, trim_record
from clockspeed.solve.exact import ExactArithmeticError, InexactValueError
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
from clockspeed.solve.ratio import BYPRODUCT_POLICIES, ProductionPlan
from clockspeed.solve.strategy import STRATEGY_LADDER, RankedPlan, Strategy, rank_plans

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.save.world import UnlockState
    from clockspeed.solve.bound import TrimRecord

__all__ = ["PlanRequest", "plan_offer"]

#: The weight a search scores its one direction at.
_UNIT_WEIGHT: Final = Fraction(1)


class _AskedRungDeadEndError(OptimizeError):
    """The bound solved, and the asked direction's own search then found nothing.

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
        targets: Item key to the wanted net rate per minute. Every rate must be
            exactly a Fraction above zero.
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


def _well_formed(request: PlanRequest) -> bool:
    """Whether a request can be asked at all.

    Args:
        request: The request.

    Returns:
        True for one known direction, one known byproduct policy, raw items exactly a
        tuple of str and at least one target, each rate exactly a Fraction above zero.
    """
    if request.direction not in OBJECTIVES or request.byproduct_policy not in BYPRODUCT_POLICIES:
        return False
    raw_items = request.raw_items
    if type(raw_items) is not tuple or not all(type(item) is str for item in raw_items):
        return False
    rates = tuple(request.targets.values())
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
        The plan, or None when the rung has no exact figure to compare, or its own
        search dead-ended on a set the bound has already solved.

    Raises:
        PowerNotComparableError: The rung is the direction the caller asked for,
            so there is no order to publish.
        _AskedRungDeadEndError: The rung is the direction the caller asked for, and
            its own search dead-ended.
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
        if strategy.objective_name == asked:
            raise _AskedRungDeadEndError from None
        return None


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


def plan_offer(
    unlocks: UnlockState, registry: Registry, request: PlanRequest | None
) -> dict[str, InputValue]:
    """Answer one request with the inputs the plan family reads.

    Reads no file and no clock. Never raises for a solve refusal: each one is a
    status. So does a KeyError or ValueError from anywhere in the search, even one
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
        it beside the plan when one was.
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
        return plan_inputs(
            top,
            requires=requires,
            trimmed=trimmed,
            unchecked=unchecked,
            unmatched_unlocks=unmatched,
            backend=backend,
        )
    return refused_inputs(status, trimmed=trimmed, unchecked=unchecked, unmatched_unlocks=unmatched)
