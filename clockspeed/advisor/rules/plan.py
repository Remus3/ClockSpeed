"""CS-1346 and CS-1351: the plan family - a rule that reads a plan, so a trace carries its badge.

WHAT THIS MODULE OWNS. One rule and the adapters that feed it:

- :data:`ADOPT_RULE` (``plan.adopt``) reads one ranked plan - the
  :class:`~clockspeed.solve.ratio.ProductionPlan` and the
  :class:`~clockspeed.solve.strategy.StrategyBadge` that one
  :func:`~clockspeed.solve.strategy.rank_plans` call published for it - and,
  when the badge records at least one cleared rung, recommends building the
  plan for its targets. A plan that cleared NO rung against its reference is
  worse than that reference on every claim the ladder grades, so it is
  rejected, never advised, and the rejection settles the rule.
- :func:`plan_inputs` offers one :class:`~clockspeed.solve.strategy.RankedPlan`
  as the rule's inputs, each sourced to the ranked-plan field it came from,
  beside the unlock keys its recipes need and what the search left out.
  :func:`status_inputs` and :func:`refused_inputs` say why no plan is offered.
  ``clockspeed/advisor/plans.py`` ranks the plan and calls them; this module
  solves nothing.

THE BADGE IS TIER 3 ONLY. The rule reads the badge through the engine, so the
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
and no card. From ``advise_world`` no locked recipe reaches the rule, because the
search excludes it first; the engine's check is the second gate, and it does not
trust the first. The rule itself declares no unlock: "build this plan" needs only
what the plan's own recipes need.

EVERY FIGURE IS PRICED AT THE PINNED BUILD (CS-1288). A plan's machine counts
are solved from registry recipes, and the registry is the pinned build's. So
the rule declares :data:`clockspeed.advisor.build.BUILD_INPUTS` ahead of its
own inputs and calls :func:`clockspeed.advisor.build.build_caveat` FIRST, on
every path: off the pin its reason names both builds and it settles nothing,
exactly as every registered rule does.

REGISTERED, AND IT FIRES ONLY WHERE A CALLER STATES A TARGET (CS-1351). The family
is in ``clockspeed/advisor/rules/__init__.py::_FAMILIES``, and
``clockspeed/advisor/advise.py::inputs_of`` offers its inputs on every world, so
the CS-1285 slice C ruling G6 holds: no registered rule runs on a world that lacks
them. A caller states a target through ``plan_request``. No surface passes one yet,
so on a served world the rule records why it is silent and yields no card.

NO TARGET IS NOT A MISSING INPUT, AND NO PLAN IS NOT A VERDICT. Every world offers
:data:`IN_STATUS`. A status other than :data:`STATUS_RANKED` records one
``verdict-indeterminate`` step with a reason from a closed vocabulary and no card,
never an ``input-missing`` step, and never a rejection, which would settle the rule
and let ``Ledger.reconcile`` complete a card whose target was merely cleared. A
status outside the vocabulary is a rule error.

THE FIRING PATH SETTLES NOTHING EITHER. A plan is ranked for a stated target and
never compared with the world, so its card going away says nothing about the world:
the player may only have asked about something else. So firing records one
indeterminate step too, as :func:`clockspeed.advisor.build.build_caveat` does off the
pin, and a recorded card is never completed by a target that moved. Only the
rejection of a plan that cleared no rung settles the rule, and from a world that path
is unreachable, because the top plan is one rung's own optimum.

NO WORLD TOKEN, NO SAVE PATH, NO FLOAT. Every source names the field a value came
from, every unlock key is built from the registry's string rather than a save's, and
every number is an exact ``Fraction``.
"""

from __future__ import annotations

from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.build import BUILD_INPUTS, build_caveat
from clockspeed.advisor.cards import render_value
from clockspeed.advisor.trace import InputValue, Recommendation, RuleContext, RuleSpec
from clockspeed.solve.ratio import ProductionPlan
from clockspeed.solve.strategy import STRATEGY_LADDER, StrategyBadge

if TYPE_CHECKING:
    from clockspeed.solve.strategy import RankedPlan

#: The advice domain of this family.
DOMAIN: Final = "plan"

#: The one input every world offers: why a plan is or is not on offer.
IN_STATUS: Final = "plan.status"

#: What the join left out, offered wherever a join ran.
IN_UNCHECKED: Final = "plan.unchecked"
IN_UNMATCHED: Final = "plan.unmatched_unlocks"

#: Input names, each offered by :func:`plan_inputs`.
IN_PLAN: Final = "plan.production"
IN_BADGE: Final = "plan.badge"
IN_REQUIRES: Final = "plan.requires"
IN_TRIMMED: Final = "plan.trimmed"

#: Every input this family adds to the build inputs, in the order it reads them.
PLAN_INPUTS: Final = (
    IN_STATUS,
    IN_UNCHECKED,
    IN_UNMATCHED,
    IN_PLAN,
    IN_BADGE,
    IN_REQUIRES,
    IN_TRIMMED,
)

#: A plan was ranked and is on offer.
STATUS_RANKED: Final = "ranked"

#: The caller stated no target. Every served world, today.
STATUS_NO_TARGET: Final = "no-target"

#: The question cannot be asked: a bad rate, direction or policy, or a refusal
#: that says the request is malformed rather than unanswerable.
STATUS_REQUEST_MALFORMED: Final = "request-malformed"

#: No selection of the unlocked automated recipes reaches the target.
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

#: The label of the one number the rule computes.
LABEL_MACHINES: Final = "plan machine equivalents"

#: The alternative a plan that cleared no rung loses as, and the one a status
#: other than ranked leaves undecided.
_ADOPT_ALTERNATIVE: Final = "build the ranked plan"

#: Why each status but ranked offers no plan: the closed vocabulary a trace reads.
_STATUS_REASONS: Final = MappingProxyType(
    {
        STATUS_NO_TARGET: "no target was stated, so no plan was ranked",
        STATUS_REQUEST_MALFORMED: "the stated target cannot be asked as a question",
        STATUS_NO_PLAN: "no selection of the unlocked automated recipes reaches the target",
        STATUS_SOLVE_REFUSED: "the search refused, which says nothing about the target",
        STATUS_POWER_NOT_COMPARABLE: "the power search reached a recipe with no exact draw",
    }
)

#: The two statuses reached before any join, which offer nothing else to read.
_UNJOINED_STATUSES: Final = (STATUS_NO_TARGET, STATUS_REQUEST_MALFORMED)

#: The comparison the firing path records as undecided.
_COMPARE_ALTERNATIVE: Final = "compare the plan with what is built"
_COMPARE_REASON: Final = "a plan is ranked for a stated target and never compared with the world"

#: Subject keys are this prefix and the plan's sorted target items, so a card's
#: identity names WHAT the plan makes and never a figure that may move.
SUBJECT_PREFIX: Final = "plan:"

#: The rung names in ladder order, which every badge's checks must follow.
_LADDER_NAMES: Final = tuple(strategy.name for strategy in STRATEGY_LADDER)


def status_inputs(status: str) -> dict[str, InputValue]:
    """Offer a status reached before any join ran: nothing else exists to offer.

    Args:
        status: One word of the closed vocabulary.

    Returns:
        A fresh dict holding the status alone.
    """
    return {IN_STATUS: InputValue(status, _OFFER_SOURCE_PREFIX + "status")}


def refused_inputs(
    status: str, *, unchecked: tuple[str, ...], unmatched_unlocks: int
) -> dict[str, InputValue]:
    """Offer a status a search reached without a plan, and what its join left out.

    A world can read no-plan only because the one route was never asked about, so
    the trace says what was left out on this path as well.

    Args:
        status: One word of the closed vocabulary.
        unchecked: The automated recipes carrying no asset path, by ClassName.
        unmatched_unlocks: How many of the world's unlocked paths joined no recipe.
            A count, because each one is a string read out of a save.

    Returns:
        A fresh dict, so a caller may add inputs from another layer.
    """
    return {
        **status_inputs(status),
        IN_UNCHECKED: InputValue(unchecked, _OFFER_SOURCE_PREFIX + "unchecked"),
        IN_UNMATCHED: InputValue(unmatched_unlocks, _OFFER_SOURCE_PREFIX + "unmatched_unlocks"),
    }


def plan_inputs(
    ranked: RankedPlan,
    *,
    requires: tuple[str, ...],
    trimmed: tuple[str, ...],
    unchecked: tuple[str, ...],
    unmatched_unlocks: int,
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

    Returns:
        A fresh dict, so a caller may add inputs from another layer.
    """
    return {
        **refused_inputs(STATUS_RANKED, unchecked=unchecked, unmatched_unlocks=unmatched_unlocks),
        IN_PLAN: InputValue(ranked.plan, _SOURCE_PREFIX + "plan"),
        IN_BADGE: InputValue(ranked.badge, _SOURCE_PREFIX + "badge"),
        IN_REQUIRES: InputValue(requires, _REQUIRES_SOURCE),
        IN_TRIMMED: InputValue(trimmed, _TRIMMED_SOURCE),
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
    if status not in _UNJOINED_STATUSES:
        unchecked = _names(ctx.read(IN_UNCHECKED), "a plan's unchecked recipes")
        if type(ctx.read(IN_UNMATCHED)) is not int:
            raise TypeError("a plan's unmatched unlock count is not an int")
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
    trimmed = _names(ctx.read(IN_TRIMMED), "a plan's trimmed recipes")
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
    missed = (
        f"; {len(unchecked)} automated recipe(s) carry no asset path and were never planned"
        if unchecked
        else ""
    )
    return Recommendation(
        subject_key=SUBJECT_PREFIX + "+".join(targets),
        action="Build the planned production chain for " + ", ".join(targets),
        reason=(
            f"It makes {rates} with {render_value(machines)} machine equivalents"
            f"{trim}{missed}{caveat}"
        ),
        requires=requires,
    )


ADOPT_RULE: Final = RuleSpec(
    rule_id="plan.adopt",
    domain=DOMAIN,
    inputs=(*BUILD_INPUTS, *PLAN_INPUTS),
    unlocks=(),
    evaluate=_evaluate_adopt,
)

#: Every rule in this family, registered in ``_FAMILIES``.
RULES: Final = (ADOPT_RULE,)
