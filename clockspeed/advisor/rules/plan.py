"""CS-1346, CS-1351 and CS-1371: the plan family - two rules that read a plan.

WHAT THIS MODULE OWNS. Two rules and the adapters that feed them:

- :data:`ADOPT_RULE` (``plan.adopt``) reads one ranked plan - the
  :class:`~clockspeed.solve.ratio.ProductionPlan` and the
  :class:`~clockspeed.solve.strategy.StrategyBadge` that one
  :func:`~clockspeed.solve.strategy.rank_plans` call published for it - and,
  when the badge records at least one cleared rung, recommends building the
  plan for its targets. A plan that cleared NO rung against its reference is
  worse than that reference on every claim it could be compared on, so it is
  rejected, never advised, and the rejection settles the rule. Its trace carries the
  badge.
- :data:`REDESIGN_RULE` (``plan.redesign``) reads the one route a no-plan derives and
  solves, and recommends planning toward its targets. See THE MARKED ROUTE below.
- :func:`plan_inputs` offers one :class:`~clockspeed.solve.strategy.RankedPlan`
  as ``plan.adopt``'s inputs, each sourced to the ranked-plan field it came from,
  beside the unlock keys its recipes need, the backend that ran the search and
  what the search left out. :func:`status_inputs` and :func:`refused_inputs` say
  why no plan is offered. :func:`redesign_inputs` and :func:`redesign_status_inputs`
  offer the route, or why there is none, and :func:`plan_outcome_of` projects the offer
  for a surface to transcribe. ``clockspeed/advisor/plans.py`` ranks the plan, solves
  the route and calls them; this module solves nothing.

THE BADGE IS TIER 3 ONLY. ``plan.adopt`` reads the badge through the engine, so the
trace carries it as an ``input-read`` step, and
:func:`clockspeed.advisor.cards.render_value` renders it field by field into
the derivation - the strongest rung, every cleared rung, and each rung's
verdict with both scores and the bound - generated from the trace and never
hand-written (non-negotiable 8). The headline is built from the plan's target
items alone and the reason from its target rates, its machine total, what the
search left out and, always last, the build caveat, so tier 1 carries nothing of
the badge and a different badge on the same plan moves tier 3 alone.
``clockspeed/advisor/cards.py::Card`` gains no field: the badge reaches the card
only through the trace it is built from.

THE BACKEND IS TIER 3 ONLY, THE SAME WAY. A derivation differs by backend, and a rung
cleared against a heuristic's reference is not the claim an exact one makes, so
``plan.adopt`` reads ``plan.backend`` on the ranked path. It is the name the result itself
carries, never the environment value, and a name outside the closed vocabulary is a
rule error. It never reaches tier 1, tier 2 or the card id: on one plan the name moves
none of them; a different backend can rank a different plan, which moves tier 2.

WHY THE ENGINE ADMITS THESE TYPES. The solve layer declares its plan and badge
dataclasses frozen but without slots, which
:meth:`clockspeed.advisor.trace.RuleContext.read` refused outright before this
item. The engine admits exactly the five named in
:data:`clockspeed.advisor.trace.PLAN_TYPES`, by exact type, and only when an
instance holds nothing beyond its declared fields - see that module's
docstring.

ONE RANKING, ONE PAIR. The adapter takes a ``RankedPlan``, never a loose plan
and badge: :func:`~clockspeed.solve.strategy.rank_plans` publishes the two
together, so a caller passing its entries straight through cannot pair one
plan with another plan's badge. That stays true when the ranking grades each
rung against a reference of its own. A hand-built ``RankedPlan`` is not checked
against a ranking here; the badge's own consistency is (below).

A BADGE THAT DISAGREES WITH ITSELF IS A RULE ERROR. Its checks must name
every rung of :data:`~clockspeed.solve.strategy.STRATEGY_LADDER` in ladder
order, ``cleared`` must be exactly the cleared checks' rung names in that
order, and ``strongest`` the last of them or None - the shape
:func:`~clockspeed.solve.strategy.badge_for` publishes. A badge that breaks
any of these raises, which the engine records as a ``rule-error`` and no
card: advice is never built on a forged claim.

UNLOCKS TRAVEL THROUGH THE ENGINE. A plan names recipes by registry ClassName,
and the unlock state holds asset paths. The join between the two is
``clockspeed/advisor/plans.py``, which fills ``plan.requires``, and that is why
it is a REQUIRED keyword of :func:`plan_inputs` with no default: inventing an
empty tuple here would advise a plan over recipes nobody checked. The rule reads
the keys and hands them to ``Recommendation.requires``, where
:func:`clockspeed.advisor.trace.run_rule` checks each against the world's
unlocks, so a plan over a locked recipe yields a ``precondition-unmet`` step
and no card. From ``advise_world`` no locked recipe reaches ``plan.adopt``, because
the search excludes it first; the engine's check is the second gate, and it does not
trust the first. The rule itself declares no unlock: "build this plan" needs only
what the plan's own recipes need.

THE MARKED ROUTE (CS-1371). A no-plan speaks only for what the search kept, so
``clockspeed/advisor/plans.py`` then derives one route over every automated recipe
carrying a path and solves it once. :data:`REDESIGN_RULE` reads the result. Its action
is doable now, because its ``requires`` holds only the held recipes the solve gives a
machine, so the engine's check still applies. Locked recipes do reach this rule, by
ClassName, under :data:`IN_REDESIGN_LOCKED`, an input of their own: tier 3 reads them,
and tier 1, tier 2 and ``requires`` name none of them, so no locked stage reads as
buildable. Tier 2 gives counts and says what the route is: the stated direction did not
choose it, and it was never compared with what is built. The card carries no badge,
because no ranking saw the route. A list that disagrees with the plan's own machines, a
status outside the closed vocabulary, and a status that disagrees with ``plan.status`` are
each a rule error. Its inputs stay out of :data:`PLAN_INPUTS`, so the ranked path and the
route never share a name.

EVERY FIGURE IS PRICED AT THE PINNED BUILD (CS-1288). A plan's machine counts
are solved from registry recipes, and the registry is the pinned build's. So
each rule declares :data:`clockspeed.advisor.build.BUILD_INPUTS` ahead of its
own inputs and calls :func:`clockspeed.advisor.build.build_caveat` FIRST, on
every path: off the pin its reason names both builds, last, and it settles nothing,
exactly as every registered rule does.

REGISTERED, AND THEY FIRE ONLY WHERE A CALLER STATES A TARGET (CS-1351). The family
is in ``clockspeed/advisor/rules/__init__.py::_FAMILIES``, and
``clockspeed/advisor/advise.py::inputs_of`` offers its inputs on every world, so
the CS-1285 slice C ruling G6 holds: no registered rule runs on a world that lacks
them. A caller states a target through ``plan_request``, as the advice routes of
``clockspeed/surface/api/advice.py`` do when asked (CS-1371). With none stated each
rule records why it is silent and yields no card.

NO TARGET IS NOT A MISSING INPUT, AND NO PLAN IS NOT A VERDICT. Every world offers
:data:`IN_STATUS` and :data:`REDESIGN_INPUTS`. A status other than :data:`STATUS_RANKED`
records one ``verdict-indeterminate`` step with a reason from a closed vocabulary and no
``plan.adopt`` card, and a route status other than :data:`REDESIGN_ROUTED` does the same
for ``plan.redesign``, never an ``input-missing`` step, and never a rejection, which would
settle the rule and let ``Ledger.reconcile`` complete a card whose target was merely
cleared. A status outside its vocabulary is a rule error.

THE FIRING PATH SETTLES NOTHING EITHER. A plan is ranked for a stated target, and a route
derived for one, and neither is compared with the world, so a card going away says
nothing about the world: the player may only have asked about something else. So firing
records one indeterminate step too, as :func:`clockspeed.advisor.build.build_caveat` does
off the pin, and a recorded card is never completed by a target that moved. Only a
rejection settles either rule: of a plan that cleared no rung, and of a route with no
machine on any step. From a world both are unreachable, because the top plan is one rung's
own optimum and a stated rate is above zero.

NO WORLD TOKEN, NO SAVE PATH, NO FLOAT. Every source names the field a value came
from, every unlock key is built from the registry's string rather than a save's, and
every figure is a ``Fraction``, the one count an ``int``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.build import BUILD_INPUTS, build_caveat
from clockspeed.advisor.cards import render_value
from clockspeed.advisor.trace import InputValue, Recommendation, RuleContext, RuleSpec
from clockspeed.solve.backends import available_backends
from clockspeed.solve.ratio import ProductionPlan
from clockspeed.solve.strategy import STRATEGY_LADDER, StrategyBadge

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.solve.strategy import RankedPlan

#: The advice domain of this family.
DOMAIN: Final = "plan"

#: Why a plan is or is not on offer. Every world offers it.
IN_STATUS: Final = "plan.status"

#: What the join and the bound left out, offered wherever a join ran.
IN_UNCHECKED: Final = "plan.unchecked"
IN_UNMATCHED: Final = "plan.unmatched_unlocks"
IN_TRIMMED: Final = "plan.trimmed"

#: Input names offered only beside a ranked plan, by :func:`plan_inputs`.
IN_PLAN: Final = "plan.production"
IN_BADGE: Final = "plan.badge"
IN_REQUIRES: Final = "plan.requires"
IN_BACKEND: Final = "plan.backend"

#: Every input :data:`ADOPT_RULE` adds to the build inputs, in the order it reads them.
PLAN_INPUTS: Final = (
    IN_STATUS,
    IN_UNCHECKED,
    IN_UNMATCHED,
    IN_TRIMMED,
    IN_PLAN,
    IN_BADGE,
    IN_REQUIRES,
    IN_BACKEND,
)

#: Input names of the marked route, offered on every world and read by
#: :data:`REDESIGN_RULE` alone.
IN_REDESIGN_STATUS: Final = "plan.redesign.status"
IN_REDESIGN_PLAN: Final = "plan.redesign.plan"
IN_REDESIGN_HELD: Final = "plan.redesign.held"
IN_REDESIGN_LOCKED: Final = "plan.redesign.locked"
IN_REDESIGN_REQUIRES: Final = "plan.redesign.requires"
IN_REDESIGN_UNMADE: Final = "plan.redesign.unmade"

#: Every input the marked route offers, in the order the rule reads them. Apart from
#: :data:`PLAN_INPUTS`: the ranked path and the route never share a name.
REDESIGN_INPUTS: Final = (
    IN_REDESIGN_STATUS,
    IN_REDESIGN_PLAN,
    IN_REDESIGN_HELD,
    IN_REDESIGN_LOCKED,
    IN_REDESIGN_REQUIRES,
    IN_REDESIGN_UNMADE,
)

#: The search did not read no-plan, so no route was derived. Every world but a no-plan.
REDESIGN_NOT_REACHED: Final = "not-reached"

#: The route was derived and pillar 1 solved it, so it is on offer.
REDESIGN_ROUTED: Final = "routed"

#: The count found no route to some target, over every automated recipe with a path.
REDESIGN_NO_ROUTE: Final = "no-route"

#: A route was derived and pillar 1 refused it, under the stated byproduct policy.
REDESIGN_ROUTE_REFUSED: Final = "route-refused"

#: A plan was ranked and is on offer.
STATUS_RANKED: Final = "ranked"

#: The caller stated no target, which is every request that does not name the four.
STATUS_NO_TARGET: Final = "no-target"

#: The question cannot be asked: bad targets, a bad rate, direction, policy or raw
#: items, or a refusal that says the request is malformed rather than unanswerable.
STATUS_REQUEST_MALFORMED: Final = "request-malformed"

#: The search found no plan over the unlocked automated recipes it kept, under the
#: stated byproduct policy. Nothing beyond that set: what the cap dropped is on
#: :data:`IN_TRIMMED`, and a capped no-plan and an uncapped one are this one status.
STATUS_NO_PLAN: Final = "no-plan"

#: The search refused for a reason that is no statement about the target.
STATUS_SOLVE_REFUSED: Final = "solve-refused"

#: Asked for by power, and some recipe the search reached has no exact draw.
STATUS_POWER_NOT_COMPARABLE: Final = "power-not-comparable"

_SOURCE_PREFIX: Final = "solve.strategy.ranked_plan."

#: The source of the status and of what the join left out.
_OFFER_SOURCE_PREFIX: Final = "advisor.plans."

#: The source of the unlock keys: the join, never a solve field.
_REQUIRES_SOURCE: Final = _OFFER_SOURCE_PREFIX + "recipe_unlock_join"

#: The source of what the bound dropped.
_TRIMMED_SOURCE: Final = "solve.bound.trim_record.removed"

#: The source of the backend's name: the result's own field, never the environment.
_BACKEND_SOURCE: Final = "solve.optimize.optimize_result.backend"

#: The label of the one number the rule computes.
LABEL_MACHINES: Final = "plan machine equivalents"

#: The alternative a plan that cleared no rung loses as, and the one a status
#: other than ranked leaves undecided.
_ADOPT_ALTERNATIVE: Final = "build the ranked plan"

#: Why each status but ranked offers no plan: the closed vocabulary a trace reads.
_STATUS_REASONS: Final = MappingProxyType(
    {
        STATUS_NO_TARGET: "no target was stated, so no plan was ranked",
        STATUS_REQUEST_MALFORMED: "the stated request cannot be asked as a question",
        STATUS_NO_PLAN: (
            "the search found no plan over the unlocked automated recipes it kept,"
            " under the stated byproduct policy"
        ),
        STATUS_SOLVE_REFUSED: "the search refused, which says nothing about the target",
        STATUS_POWER_NOT_COMPARABLE: "the power search reached a recipe with no exact draw",
    }
)

#: The two statuses whose reason needs nothing else read. No target is reached before
#: any join; a malformed request is too, unless a refusal after the join says so, as a
#: target declared raw does, and then what is offered beside it stays unread.
_UNJOINED_STATUSES: Final = (STATUS_NO_TARGET, STATUS_REQUEST_MALFORMED)

#: The comparison the firing path records as undecided.
_COMPARE_ALTERNATIVE: Final = "compare the plan with what is built"
_COMPARE_REASON: Final = "a plan is ranked for a stated target and never compared with the world"

#: Subject keys are this prefix and the plan's sorted target items, so a card's
#: identity names WHAT the plan makes and never a figure that may move.
SUBJECT_PREFIX: Final = "plan:"

#: The rung names in ladder order, which every badge's checks must follow.
_LADDER_NAMES: Final = tuple(strategy.name for strategy in STRATEGY_LADDER)

#: The source of the marked route's status and of the two lists it sorts its stages into.
_REDESIGN_SOURCE_PREFIX: Final = _OFFER_SOURCE_PREFIX + "redesign."

#: The source of the route's plan: the function that solved it, which no ranking touched.
_ROUTE_PLAN_SOURCE: Final = "solve.ratio.solve_for_targets"

#: The source of the route's unlock keys: the join, as on the ranked path.
_ROUTE_REQUIRES_SOURCE: Final = _REDESIGN_SOURCE_PREFIX + "recipe_unlock_join"

#: The source of what the route's closure reached that nothing makes.
_ROUTE_UNMADE_SOURCE: Final = "solve.bound.derived_route.unmade"

#: The alternative the marked route records as undecided or, with no machine, as lost.
_REDESIGN_ALTERNATIVE: Final = "offer the derived route"

#: Why each status but routed offers no route: the closed vocabulary a trace reads.
_REDESIGN_REASONS: Final = MappingProxyType(
    {
        REDESIGN_NOT_REACHED: "the search did not read no-plan, so no route was derived",
        REDESIGN_NO_ROUTE: (
            "the count found no route to the target from the raw items, over every"
            " automated recipe with a path, which does not prove no plan exists"
        ),
        REDESIGN_ROUTE_REFUSED: (
            "pillar 1 refused the derived route, solved once under the stated byproduct policy"
        ),
    }
)

#: The comparison the firing path records as undecided.
_ROUTE_COMPARE_ALTERNATIVE: Final = "compare the route with what is built"
_ROUTE_COMPARE_REASON: Final = (
    "a route is derived for a stated target and never compared with the world"
)

#: The rejection only a hand-built offer reaches: a stated rate is above zero.
_NO_MACHINE_REASON: Final = "the route gives no recipe a machine"

#: What a route's reason says about unlocking, by whether any stage is locked.
_MUST_UNLOCK_CLAUSE: Final = "; the locked recipes must unlock first on this route"
_NO_UNLOCK_CLAUSE: Final = "; this route needs no unlock and the capped search did not find it"

#: What a route's reason says on every path: a count chose it, and no comparison did.
_NOT_CHOSEN_CLAUSE: Final = (
    "; the stated direction did not choose this route and it was never compared with what is built"
)


@dataclass(frozen=True)
class PlanOutcome:
    """What one stated request came to, as a surface may transcribe it (CS-1371).

    A refused trace yields no card, so this is the only word a reader gets when nothing
    fired. Built from the offer alone by :func:`plan_outcome_of`. Every field is the
    closed vocabulary's or the registry's, never a string read out of a save.

    Attributes:
        status: The ``plan.status`` word.
        reason: Why that status offers no plan, or None on ``ranked``.
        redesign: The ``plan.redesign.status`` word.
        trimmed: What the bound dropped, by ClassName, or None when this offer carries no
            such word because no search ran. Empty says the bound dropped nothing.
        unmade: What the target's closure reached that no recipe in it makes and the raw
            items lack, on ``no-route`` alone, and None on every other status. Empty on
            ``no-route`` where the gap is a loop no raw item enters.
    """

    status: str
    reason: str | None
    redesign: str
    trimmed: tuple[str, ...] | None
    unmade: tuple[str, ...] | None


def _status_input(status: str) -> dict[str, InputValue]:
    """Offer the one status word.

    Args:
        status: One word of the closed vocabulary.

    Returns:
        A fresh dict holding that word.
    """
    return {IN_STATUS: InputValue(status, _OFFER_SOURCE_PREFIX + "status")}


def redesign_status_inputs(status: str, *, unmade: tuple[str, ...] | None) -> dict[str, InputValue]:
    """Offer a marked-route status that carries no route.

    Args:
        status: One word of the marked route's closed vocabulary, never routed.
        unmade: What the closure reached that nothing makes, on no-route. REQUIRED, with
            no default: None says this status has no such word, and an empty tuple says
            the closure found no such item, which is a different claim.

    Returns:
        A fresh dict of every input of :data:`REDESIGN_INPUTS`. What was never solved
        reads None, because empty would read as a route with nothing locked on it.
    """
    return {
        IN_REDESIGN_STATUS: InputValue(status, _REDESIGN_SOURCE_PREFIX + "status"),
        IN_REDESIGN_PLAN: InputValue(None, _ROUTE_PLAN_SOURCE),
        IN_REDESIGN_HELD: InputValue(None, _REDESIGN_SOURCE_PREFIX + "held"),
        IN_REDESIGN_LOCKED: InputValue(None, _REDESIGN_SOURCE_PREFIX + "locked"),
        IN_REDESIGN_REQUIRES: InputValue(None, _ROUTE_REQUIRES_SOURCE),
        IN_REDESIGN_UNMADE: InputValue(unmade, _ROUTE_UNMADE_SOURCE),
    }


def redesign_inputs(
    plan: ProductionPlan,
    *,
    held: tuple[str, ...],
    locked: tuple[str, ...],
    requires: tuple[str, ...],
) -> dict[str, InputValue]:
    """Offer one solved route as rule inputs, each sourced to where it came from.

    Args:
        plan: The plan pillar 1 solved for the route.
        held: The route's recipes the solve gives a machine and the world holds, by
            ClassName. REQUIRED, with no default: empty says none is held.
        locked: The route's recipes the solve gives a machine and the world does not
            hold, by ClassName. REQUIRED, with no default: empty says none is locked.
        requires: The unlock keys of ``held``. REQUIRED, for the reason
            :func:`plan_inputs` gives: an invented empty tuple would advise recipes
            nobody checked.

    Returns:
        A fresh dict of every input of :data:`REDESIGN_INPUTS`.
    """
    return {
        **redesign_status_inputs(REDESIGN_ROUTED, unmade=None),
        IN_REDESIGN_PLAN: InputValue(plan, _ROUTE_PLAN_SOURCE),
        IN_REDESIGN_HELD: InputValue(held, _REDESIGN_SOURCE_PREFIX + "held"),
        IN_REDESIGN_LOCKED: InputValue(locked, _REDESIGN_SOURCE_PREFIX + "locked"),
        IN_REDESIGN_REQUIRES: InputValue(requires, _ROUTE_REQUIRES_SOURCE),
    }


def status_inputs(status: str) -> dict[str, InputValue]:
    """Offer a status reached before any join ran: no search, so no route either.

    Args:
        status: One word of the closed vocabulary.

    Returns:
        A fresh dict holding the status, and the marked route's inputs reading
        :data:`REDESIGN_NOT_REACHED`, so a world with no target still offers them.
    """
    return {
        **_status_input(status),
        **redesign_status_inputs(REDESIGN_NOT_REACHED, unmade=None),
    }


def refused_inputs(
    status: str, *, trimmed: tuple[str, ...], unchecked: tuple[str, ...], unmatched_unlocks: int
) -> dict[str, InputValue]:
    """Offer a status a search reached without a plan, and what the search left out.

    A no-plan speaks only for what the search kept, and the one route may be among
    what the join or the bound left out, so the trace says what was left out on this
    path as well.

    Args:
        status: One word of the closed vocabulary.
        trimmed: The recipes the bound dropped, by ClassName in registry order.
            REQUIRED, with no default: empty says the cap dropped nothing.
        unchecked: The automated recipes carrying no asset path, by ClassName.
        unmatched_unlocks: How many of the world's unlocked paths joined no recipe.
            A count, because each one is a string read out of a save.

    Returns:
        A fresh dict, so a caller may add inputs from another layer. The caller adds the
        marked route's: the search ran, so only the caller knows what it read.
    """
    return {
        **_status_input(status),
        IN_UNCHECKED: InputValue(unchecked, _OFFER_SOURCE_PREFIX + "unchecked"),
        IN_UNMATCHED: InputValue(unmatched_unlocks, _OFFER_SOURCE_PREFIX + "unmatched_unlocks"),
        IN_TRIMMED: InputValue(trimmed, _TRIMMED_SOURCE),
    }


def plan_inputs(
    ranked: RankedPlan,
    *,
    requires: tuple[str, ...],
    trimmed: tuple[str, ...],
    unchecked: tuple[str, ...],
    unmatched_unlocks: int,
    backend: str,
) -> dict[str, InputValue]:
    """Offer one ranked plan as rule inputs, each sourced to the field it came from.

    Args:
        ranked: One entry of a :func:`~clockspeed.solve.strategy.rank_plans`
            result. Its plan and its badge are offered together.
        requires: The unlock keys the plan's recipes need, in the form
            :func:`clockspeed.advisor.trace.unlock_keys` builds. REQUIRED, with no
            default: ``clockspeed/advisor/plans.py`` holds the join from a recipe
            ClassName to its asset path, and inventing an empty tuple here would
            advise a plan over recipes nobody checked.
        trimmed: The recipes the bound dropped to reach the plan, by ClassName.
        unchecked: The automated recipes carrying no asset path, by ClassName.
        unmatched_unlocks: How many of the world's unlocked paths joined no recipe.
            A count, because each one is a string read out of a save.
        backend: The name of the backend that ran the search, as the result
            carries it. REQUIRED, with no default: a derivation differs by backend,
            so one that names none cannot be reproduced from what it shows.

    Returns:
        A fresh dict, so a caller may add inputs from another layer.
    """
    return {
        **refused_inputs(
            STATUS_RANKED,
            trimmed=trimmed,
            unchecked=unchecked,
            unmatched_unlocks=unmatched_unlocks,
        ),
        IN_PLAN: InputValue(ranked.plan, _SOURCE_PREFIX + "plan"),
        IN_BADGE: InputValue(ranked.badge, _SOURCE_PREFIX + "badge"),
        IN_REQUIRES: InputValue(requires, _REQUIRES_SOURCE),
        IN_BACKEND: InputValue(backend, _BACKEND_SOURCE),
    }


def _check_badge(badge: StrategyBadge) -> None:
    """Refuse a badge whose summary disagrees with its own checks.

    Raises:
        ValueError: The checks do not name every ladder rung in ladder order,
            ``cleared`` is not exactly the cleared checks' names in order, or
            ``strongest`` is not the last of them (None when none cleared).
    """
    if tuple(check.strategy for check in badge.checks) != _LADDER_NAMES:
        raise ValueError("a badge's checks do not follow the strategy ladder")
    cleared = tuple(check.strategy for check in badge.checks if check.cleared is True)
    if badge.cleared != cleared:
        raise ValueError("a badge's cleared rungs disagree with its checks")
    if badge.strongest != (cleared[-1] if cleared else None):
        raise ValueError("a badge's strongest rung is not the last one it cleared")


def _names(value: object, what: str) -> tuple[str, ...]:
    """Refuse a value that is not exactly a tuple of str.

    Args:
        value: The value read.
        what: The fixed name the refusal uses, never a value.

    Returns:
        The tuple.

    Raises:
        TypeError: It is anything else.
    """
    if type(value) is not tuple or not all(type(key) is str for key in value):
        raise TypeError(what + " are not a tuple of str")
    return value


def _evaluate_adopt(ctx: RuleContext) -> Recommendation | None:
    caveat = build_caveat(ctx)
    status = ctx.read(IN_STATUS)
    if type(status) is not str:
        raise TypeError("a plan status is not a str")
    if status != STATUS_RANKED and status not in _STATUS_REASONS:
        raise ValueError("a plan status is outside the closed vocabulary")
    unchecked: tuple[str, ...] = ()
    trimmed: tuple[str, ...] = ()
    if status not in _UNJOINED_STATUSES:
        unchecked = _names(ctx.read(IN_UNCHECKED), "a plan's unchecked recipes")
        if type(ctx.read(IN_UNMATCHED)) is not int:
            raise TypeError("a plan's unmatched unlock count is not an int")
        trimmed = _names(ctx.read(IN_TRIMMED), "a plan's trimmed recipes")
    if status != STATUS_RANKED:
        ctx.indeterminate(_ADOPT_ALTERNATIVE, _STATUS_REASONS[status])
        return None
    plan = ctx.read(IN_PLAN)
    if type(plan) is not ProductionPlan:
        raise TypeError("a plan input is not a ProductionPlan")
    badge = ctx.read(IN_BADGE)
    if type(badge) is not StrategyBadge:
        raise TypeError("a badge input is not a StrategyBadge")
    _check_badge(badge)
    requires = _names(ctx.read(IN_REQUIRES), "a plan's unlock keys")
    if ctx.read(IN_BACKEND) not in available_backends():
        raise ValueError("a plan's backend is outside the closed vocabulary")
    targets = tuple(sorted(plan.targets))
    if not targets:
        raise ValueError("a plan names no target")
    machines = ctx.compute(
        LABEL_MACHINES, sum((step.machines for step in plan.steps), start=Fraction(0))
    )
    if badge.strongest is None:
        ctx.reject(_ADOPT_ALTERNATIVE, "the plan cleared no strategy rung against its reference")
        return None
    ctx.indeterminate(_COMPARE_ALTERNATIVE, _COMPARE_REASON)
    rates = ", ".join(
        f"{render_value(plan.targets[item])} per minute of {item}" for item in targets
    )
    # Counts only: tier 3 names them. The caveat stays last, whatever precedes it.
    trim = f"; the search dropped {len(trimmed)} recipe(s) to fit its cap" if trimmed else ""
    return Recommendation(
        subject_key=SUBJECT_PREFIX + "+".join(targets),
        action="Build the planned production chain for " + ", ".join(targets),
        reason=(
            f"It makes {rates} with {render_value(machines)} machine equivalents"
            f"{trim}{_unchecked_clause(unchecked)}{caveat}"
        ),
        requires=requires,
    )


def _check_no_route_offered(
    status: str, *, offered: tuple[object, object, object, object], unmade: object
) -> None:
    """Refuse a status with no route that nonetheless carries one.

    Args:
        status: The marked route's status, never routed.
        offered: The plan, held, locked and requires values read.
        unmade: The unmade value read.

    Raises:
        TypeError: Anything was offered beside it but what that status says, which is
            nothing, and on no-route the items.
    """
    if any(value is not None for value in offered):
        raise TypeError("a plan.redesign status with no route carries a route")
    if status == REDESIGN_NO_ROUTE:
        _names(unmade, "a route's unmade items")
    elif unmade is not None:
        raise TypeError("a plan.redesign status other than no-route names unmade items")


def _check_stages(plan: ProductionPlan, held: tuple[str, ...], locked: tuple[str, ...]) -> None:
    """Refuse lists that are not exactly the plan's stages with a machine, each once.

    Args:
        plan: The route's plan.
        held: The stages offered as held.
        locked: The stages offered as locked.

    Raises:
        ValueError: A machine count is negative, or the two lists disagree with the plan.
            A count of stages that are not the plan's is a forged claim.
    """
    if any(step.machines < 0 for step in plan.steps):
        raise ValueError("a route's plan runs a recipe backwards")
    stages = sorted(step.recipe_key for step in plan.steps if step.machines != 0)
    if sorted((*held, *locked)) != stages:
        raise ValueError("a route's held and locked recipes disagree with its plan")


def _unchecked_clause(unchecked: tuple[str, ...]) -> str:
    """Say how many automated recipes no plan could be asked about, or nothing.

    Args:
        unchecked: The automated recipes carrying no asset path.

    Returns:
        A count and no name, because tier 3 names them, or the empty string.
    """
    if not unchecked:
        return ""
    return f"; {len(unchecked)} automated recipe(s) carry no asset path and were never planned"


def _evaluate_redesign(ctx: RuleContext) -> Recommendation | None:
    caveat = build_caveat(ctx)
    status = ctx.read(IN_REDESIGN_STATUS)
    if type(status) is not str:
        raise TypeError("a plan.redesign status is not a str")
    if status != REDESIGN_ROUTED and status not in _REDESIGN_REASONS:
        raise ValueError("a plan.redesign status is outside the closed vocabulary")
    plan = ctx.read(IN_REDESIGN_PLAN)
    held = ctx.read(IN_REDESIGN_HELD)
    locked = ctx.read(IN_REDESIGN_LOCKED)
    requires = ctx.read(IN_REDESIGN_REQUIRES)
    unmade = ctx.read(IN_REDESIGN_UNMADE)
    if (ctx.read(IN_STATUS) == STATUS_NO_PLAN) == (status == REDESIGN_NOT_REACHED):
        raise ValueError("a plan.redesign status disagrees with the plan status")
    if status != REDESIGN_ROUTED:
        _check_no_route_offered(status, offered=(plan, held, locked, requires), unmade=unmade)
        ctx.indeterminate(_REDESIGN_ALTERNATIVE, _REDESIGN_REASONS[status])
        return None
    if type(plan) is not ProductionPlan:
        raise TypeError("a route's plan is not a ProductionPlan")
    held = _names(held, "a route's held recipes")
    locked = _names(locked, "a route's locked recipes")
    requires = _names(requires, "a route's unlock keys")
    if unmade is not None:
        raise TypeError("a routed offer names unmade items")
    unchecked = _names(ctx.read(IN_UNCHECKED), "a plan's unchecked recipes")
    targets = tuple(sorted(plan.targets))
    if not targets:
        raise ValueError("a route's plan names no target")
    _check_stages(plan, held, locked)
    ctx.compute(LABEL_MACHINES, sum((step.machines for step in plan.steps), start=Fraction(0)))
    if not held and not locked:
        ctx.reject(_REDESIGN_ALTERNATIVE, _NO_MACHINE_REASON)
        return None
    ctx.indeterminate(_ROUTE_COMPARE_ALTERNATIVE, _ROUTE_COMPARE_REASON)
    # Counts only, so no locked recipe reads as buildable: tier 3 names them under an input
    # of their own. The caveat stays last, whatever precedes it.
    unlock = _MUST_UNLOCK_CLAUSE if locked else _NO_UNLOCK_CLAUSE
    return Recommendation(
        subject_key=SUBJECT_PREFIX + "+".join(targets),
        action="Plan toward " + ", ".join(targets),
        reason=(
            f"This route runs {len(locked)} locked and {len(held)} held recipe(s)"
            f"{unlock}{_NOT_CHOSEN_CLAUSE}{_unchecked_clause(unchecked)}{caveat}"
        ),
        requires=requires,
    )


def plan_outcome_of(values: Mapping[str, InputValue]) -> PlanOutcome:
    """Project one offer's inputs into what a surface may transcribe (CS-1371).

    Args:
        values: A world's inputs, as :func:`clockspeed.advisor.plans.plan_offer` offers
            them. Read by name; nothing else in them is touched.

    Returns:
        The outcome.

    Raises:
        ValueError: Either status is outside its closed vocabulary. The message names no
            value.
    """
    status = values[IN_STATUS].value
    if type(status) is not str or (status != STATUS_RANKED and status not in _STATUS_REASONS):
        raise ValueError("a plan status is outside the closed vocabulary")
    redesign = values[IN_REDESIGN_STATUS].value
    if type(redesign) is not str or (
        redesign != REDESIGN_ROUTED and redesign not in _REDESIGN_REASONS
    ):
        raise ValueError("a plan.redesign status is outside the closed vocabulary")
    trimmed = values.get(IN_TRIMMED)
    unmade = values[IN_REDESIGN_UNMADE].value
    return PlanOutcome(
        status=status,
        reason=None if status == STATUS_RANKED else _STATUS_REASONS[status],
        redesign=redesign,
        trimmed=None if trimmed is None else _names(trimmed.value, "a plan's trimmed recipes"),
        unmade=None if unmade is None else _names(unmade, "a route's unmade items"),
    )


ADOPT_RULE: Final = RuleSpec(
    rule_id="plan.adopt",
    domain=DOMAIN,
    inputs=(*BUILD_INPUTS, *PLAN_INPUTS),
    unlocks=(),
    evaluate=_evaluate_adopt,
)

REDESIGN_RULE: Final = RuleSpec(
    rule_id="plan.redesign",
    domain=DOMAIN,
    inputs=(*BUILD_INPUTS, *REDESIGN_INPUTS, IN_STATUS, IN_UNCHECKED),
    unlocks=(),
    evaluate=_evaluate_redesign,
)

#: Every rule in this family, registered in ``_FAMILIES``.
RULES: Final = (ADOPT_RULE, REDESIGN_RULE)
