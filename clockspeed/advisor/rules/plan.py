"""CS-1346: the plan family - a rule that reads a plan, so a trace carries its badge.

WHAT THIS MODULE OWNS. One rule and the adapter that feeds it:

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
  beside the unlock keys its caller says the plan's recipes need.

THE BADGE IS TIER 3 ONLY. The rule reads the badge through the engine, so the
trace carries it as an ``input-read`` step, and
:func:`clockspeed.advisor.cards.render_value` renders it field by field into
the derivation - the strongest rung, every cleared rung, and each rung's
verdict with both scores and the bound - generated from the trace and never
hand-written (non-negotiable 8). The headline is built from the plan's target
items alone and the reason from its target rates, its machine total and the
build caveat, so tier 1 carries nothing of the badge and a different badge on
the same plan moves tier 3 alone. ``clockspeed/advisor/cards.py::Card`` gains no field: the badge
reaches the card only through the trace it is built from.

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
plan with another plan's badge. A hand-built ``RankedPlan`` is not checked
against a ranking here; the badge's own consistency is (below).

A BADGE THAT DISAGREES WITH ITSELF IS A RULE ERROR. Its checks must name
every rung of :data:`~clockspeed.solve.strategy.STRATEGY_LADDER` in ladder
order, ``cleared`` must be exactly the cleared checks' rung names in that
order, and ``strongest`` the last of them or None - the shape
:func:`~clockspeed.solve.strategy.badge_for` publishes. A badge that breaks
any of these raises, which the engine records as a ``rule-error`` and no
card: advice is never built on a forged claim.

UNLOCKS TRAVEL THROUGH THE ENGINE. A plan names recipes by registry ClassName,
and the unlock state holds asset paths; no join between the two ships here, so
the CALLER that ranked the plan supplies the unlock keys its recipes need, a
REQUIRED keyword of :func:`plan_inputs` with no default. The rule reads them and
hands them to ``Recommendation.requires``, where
:func:`clockspeed.advisor.trace.run_rule` checks each against the world's
unlocks, so a plan over a locked recipe yields a ``precondition-unmet`` step
and no card. The rule itself declares no unlock: "build this plan" needs only
what the plan's own recipes need.

EVERY FIGURE IS PRICED AT THE PINNED BUILD (CS-1288). A plan's machine counts
are solved from registry recipes, and the registry is the pinned build's. So
the rule declares :data:`clockspeed.advisor.build.BUILD_INPUTS` ahead of its
own inputs and calls :func:`clockspeed.advisor.build.build_caveat` FIRST, on
every path: off the pin its reason names both builds and it settles nothing,
exactly as every registered rule does.

NOT REGISTERED (the CS-1285 slice C ruling G6). ``clockspeed/advisor/advise.py``
offers no plan, because no caller ranks plans for a world yet. A family joins
``clockspeed/advisor/rules/__init__.py::_FAMILIES`` in the same change that has
the advisor offer its inputs, so no registered rule runs on a world that lacks
them. Until then the rule runs through
:func:`clockspeed.advisor.trace.run_rule`, or through ``advise(..., rules=RULES)``
over a world carrying :func:`plan_inputs`.

NO WORLD TOKEN, NO PATH, NO FLOAT. Every source names the ranked-plan field or
the caller argument a value came from; every number is an exact ``Fraction``.
"""

from __future__ import annotations

from fractions import Fraction
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

#: Input names, each offered by :func:`plan_inputs`.
IN_PLAN: Final = "plan.production"
IN_BADGE: Final = "plan.badge"
IN_REQUIRES: Final = "plan.requires"

#: Every input this family adds to the build inputs, in the order it reads them.
PLAN_INPUTS: Final = (IN_PLAN, IN_BADGE, IN_REQUIRES)

_SOURCE_PREFIX: Final = "solve.strategy.ranked_plan."

#: The source of the unlock keys: the caller's own argument, never a solve field.
_REQUIRES_SOURCE: Final = "caller.plan_unlock_keys"

#: The label of the one number the rule computes.
LABEL_MACHINES: Final = "plan machine equivalents"

#: The alternative a plan that cleared no rung loses as.
_ADOPT_ALTERNATIVE: Final = "build the ranked plan"

#: Subject keys are this prefix and the plan's sorted target items, so a card's
#: identity names WHAT the plan makes and never a figure that may move.
SUBJECT_PREFIX: Final = "plan:"

#: The rung names in ladder order, which every badge's checks must follow.
_LADDER_NAMES: Final = tuple(strategy.name for strategy in STRATEGY_LADDER)


def plan_inputs(ranked: RankedPlan, *, requires: tuple[str, ...]) -> dict[str, InputValue]:
    """Offer one ranked plan as rule inputs, each sourced to the field it came from.

    Args:
        ranked: One entry of a :func:`~clockspeed.solve.strategy.rank_plans`
            result. Its plan and its badge are offered together.
        requires: The unlock keys the plan's recipes need, in the
            ``recipe:<path>`` form :func:`clockspeed.advisor.trace.unlock_keys`
            builds. REQUIRED, with no default: the caller holds the join from a
            recipe ClassName to its asset path, and inventing an empty tuple here
            would advise a plan over recipes nobody checked.

    Returns:
        A fresh dict, so a caller may add inputs from another layer.
    """
    return {
        IN_PLAN: InputValue(ranked.plan, _SOURCE_PREFIX + "plan"),
        IN_BADGE: InputValue(ranked.badge, _SOURCE_PREFIX + "badge"),
        IN_REQUIRES: InputValue(requires, _REQUIRES_SOURCE),
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


def _evaluate_adopt(ctx: RuleContext) -> Recommendation | None:
    caveat = build_caveat(ctx)
    plan = ctx.read(IN_PLAN)
    if type(plan) is not ProductionPlan:
        raise TypeError("a plan input is not a ProductionPlan")
    badge = ctx.read(IN_BADGE)
    if type(badge) is not StrategyBadge:
        raise TypeError("a badge input is not a StrategyBadge")
    _check_badge(badge)
    requires = ctx.read(IN_REQUIRES)
    if type(requires) is not tuple or not all(type(key) is str for key in requires):
        raise TypeError("a plan's unlock keys are not a tuple of str")
    targets = tuple(sorted(plan.targets))
    if not targets:
        raise ValueError("a plan names no target")
    machines = ctx.compute(
        LABEL_MACHINES, sum((step.machines for step in plan.steps), start=Fraction(0))
    )
    if badge.strongest is None:
        ctx.reject(_ADOPT_ALTERNATIVE, "the plan cleared no strategy rung against its reference")
        return None
    rates = ", ".join(
        f"{render_value(plan.targets[item])} per minute of {item}" for item in targets
    )
    return Recommendation(
        subject_key=SUBJECT_PREFIX + "+".join(targets),
        action="Build the planned production chain for " + ", ".join(targets),
        reason=f"It makes {rates} with {render_value(machines)} machine equivalents{caveat}",
        requires=requires,
    )


ADOPT_RULE: Final = RuleSpec(
    rule_id="plan.adopt",
    domain=DOMAIN,
    inputs=(*BUILD_INPUTS, *PLAN_INPUTS),
    unlocks=(),
    evaluate=_evaluate_adopt,
)

#: Every rule in this family. NOT in ``_FAMILIES`` yet - see the module docstring.
RULES: Final = (ADOPT_RULE,)
