"""CS-1244 - a named strategy ladder for ranking plans, with a threshold per rung.

Pillar 2 answers "which selection is best under THIS objective". A player asks
a different question: "is the thing I built close enough to the best, and in
what respect". This module answers the second one without re-solving anything.
It re-SCORES a plan it was handed, under each named objective in turn, against
a reference plan the caller names, and publishes a badge recording the
strongest claim the plan cleared. The badge is the data a later advisor rule
trace projects into prose; nothing here renders prose for a player.

WHY THIS IS A SIBLING MODULE RATHER THAN MORE OF optimize.py
--------------------------------------------------------------
``clockspeed/solve/optimize.py`` states that it owns the OBJECTIVE and the
INTERFACE and deliberately owns no search. Ranking SEVERAL plans against each
other, and grading one against a reference, is neither of those: it consumes
the objective arithmetic and the one documented tie-break key that module
publishes, and adds a policy on top of them. ``clockspeed/solve/relax.py`` is
the standing precedent for a consumer sibling inside ``clockspeed/solve/`` -
one data table, a fixed order, and a structured record of what the table
decided.

Nothing here imports ``clockspeed/solve/backends/``. The tie-break rule lives
one layer up in ``optimize.py`` on purpose, and a module in ``clockspeed/solve/``
reaching into ``clockspeed/solve/backends/`` for a rule is the CLAUDE.md
section 2.1 reach-past-your-neighbor bug. :func:`~clockspeed.solve.optimize.ranking_key`
takes a score rather than a result for exactly this caller's sake, so a plan can
be ranked under an objective it was never solved under.

WHAT A THRESHOLD MEANS, AND WHY IT IS A RELATIVE PRODUCT
----------------------------------------------------------
A rung is cleared when, for that rung's single objective::

    score(plan)  <=  bound * score(reference)

with ``bound`` an exact Fraction at or above 1. Four reasons this is the form,
each from this tree's own arithmetic rather than from taste:

1. MULTIPLICATION, NEVER DIVISION. ``int / int`` is a float and one inexact
   operand converts every value derived from it while looking correct - the
   measurement ``clockspeed/solve/exact.py`` records. The ratio spelling
   ``score(plan) / score(reference) <= bound`` would also need a guard for a
   zero reference. The product spelling needs neither: a reference score of
   zero clears only a plan score of zero, exactly and by itself, and no
   division appears anywhere in this module.
2. AN ABSOLUTE BOUND IS REFUSED. Every term the objectives total scales with
   the requested rate - raw consumption is items per minute, power is
   megawatts, machines are machine equivalents. The C3 fixture at 20 Gadget per
   minute draws 60 Ore per minute and the same chain at 40 draws 120. A bound
   stated as an absolute number therefore encodes the fixture's target rate and
   measures nothing about the plan.
3. A PER-UNIT RATIO IS ALSO REFUSED, even though dividing a score by the total
   target rate is scale-free. Its bound would have to be a number like four or
   one fifth, and nothing in this project derives such a number from anything -
   so it would be FITTED to whichever fixtures happened to exist when it was
   written. A threshold with no derivation is the CONVENTIONS.md section 7.2
   unrun gate wearing a number: it passes, and it graded nothing.
4. THE RELATIVE FORM NEEDS NO FITTED CONSTANT AT ALL. Every rung in
   :data:`STRATEGY_LADDER` carries ``bound`` of one - the multiplicative
   identity rather than a tuned figure - and that alone already separates the
   shipped fixtures: C5 against C3 clears two rungs and fails the third, which
   is the non-monotone case the badge rule below turns on.

WHY THE REFERENCE IS A REQUIRED ARGUMENT WITH NO DEFAULT
----------------------------------------------------------
``optimize.py`` sets the precedent for its ``unlocked`` field: inventing the
value here would mean this module defaulting to something the caller never
said. The obvious default - solve the request again and compare against the
winner - is worse than absent. It would make a badge cost a whole search, and
it would REFUSE outright above ``optimize.py``'s exhaustive candidate cap, so a
plan's badge would depend on how many candidates were in play rather than on
the plan. :func:`rank_plans` has a reference it did not have to invent, its own
top-ranked member, and passes it explicitly, unless its caller states one per
rung through ``references``.

A RANKING'S OWN TOP MEMBER GRADES ITSELF, WHICH IS WHY A CALLER MAY STATE ONE PER RUNG
----------------------------------------------------------------------------------------
Graded against its own ranking, rank one clears every rung it can be priced on,
whatever else is in the ranking: it scores no more than itself on each, so its
badge claims nothing a reader can use. A caller about to advise that plan holds
the better question, whether it is within the best plan each rung's own direction
allows. So :func:`rank_plans` takes keyword-only ``references``, one plan per rung, the
caller having solved them. Every entry stays a published plan-and-badge pair,
nothing here solves, and an unstated ``references`` is the self-graded ranking
above, unchanged. A rung's reference of None says that rung had nothing exact to
compare with, and reads as :data:`NOT_CLEARED_UNPRICEABLE`. A missing rung is
refused rather than read as None: absent is the caller's oversight, and grading
it would publish a verdict nobody asked for.

THE LADDER ORDER IS WEAKEST CLAIM FIRST
-----------------------------------------
:data:`STRATEGY_LADDER`, in order:

1. ``within-raw`` - clearing it says the plan eats no more input than the
   reference. The weakest of the three, and ``optimize.py`` states its own
   limit: the raw objective totals rates across raw items WITHOUT weighting
   them, so the comparison is like for like only where the raws are
   commensurate. A caller trading ore against oil is asking a question the
   objective does not model.
2. ``within-buildings`` - clearing it constrains the build-out, in machine
   equivalents. Stronger than input rate alone because it is a claim about what
   the player must actually construct, and it prices no power at all.
3. ``within-power`` - clearing it says the plan draws no more than the
   reference at each building's own un-sharded clock base. It CAN ONLY CLEAR if
   every recipe either plan uses is exactly priceable there, so its clearance
   carries strictly more evidence than either rung above it: an unmodeled
   building, a recipe naming none, and a recipe naming several all make it
   refuse rather than clear.

WHERE THIS DIFFERS FROM relax.py, AND IT IS THE LOAD-BEARING DECISION HERE
----------------------------------------------------------------------------
``relax.py`` stops at the FIRST rung that fires and its record is a cumulative
PREFIX of the ladder. That is correct there because loosening a constraint is
monotone in severity: a request answered after two rungs was not answered after
one.

Threshold clearance across DIFFERENT objectives is NOT monotone, and the
shipped fixtures prove it rather than merely suggesting it. C5 against C3 at
bound one fails ``within-raw`` (120 against 60) and clears both
``within-buildings`` (3 against 6) and ``within-power`` (45 against 436/3). So:

- :attr:`StrategyBadge.strongest` is the HIGHEST-INDEX cleared rung, never the
  end of the longest cleared prefix. The acceptance clause says "the strongest
  threshold cleared in fixed ladder order", and a longest-prefix reading would
  publish NO badge at all for that plan - a weaker claim than the plan earned,
  and weaker on the exact case the ladder exists to describe.
- :attr:`StrategyBadge.checks` carries one entry per rung, always, in ladder
  order. A gap is therefore VISIBLE in the record rather than hidden by a
  summary field, which is what lets a reader see that the power claim was
  earned while the raw claim was not.

NON-NEGOTIABLE 7 - FLAGGED AND SKIPPED, NEVER FATAL, AND EXACTLY ONE REFUSAL
------------------------------------------------------------------------------
:func:`check_threshold` absorbs
:class:`~clockspeed.solve.optimize.PowerNotComparableError` and reports that
rung as not cleared with :data:`NOT_CLEARED_UNPRICEABLE` and no score. Unknown
content is flagged and skipped: a plan using a recipe this registry cannot
price for power still earns whatever the other two rungs say about it, and the
power rung says plainly that it could not be compared rather than scoring a
confident zero.

That is the ONLY refusal absorbed, on exactly the rule ``relax.py`` states.
:class:`~clockspeed.solve.optimize.ObjectiveUndefinedError` PROPAGATES, because
it does not say the threshold failed - it says the question was malformed, and
absorbing it would publish "not cleared" for a rung that was never evaluated.
So does every other exception, including the ``KeyError`` raised for a plan
naming a recipe this registry does not model. That is not unknown content to
flag: the registry has no entry for the recipe at all, so the fault is a
mismatch between the plan and the registry it was handed with, and recording
it as "power-not-comparable" would misreport that mismatch as a pricing gap.
Among the rungs, the KeyError comes only from the power rung, the one rung
whose arithmetic looks a recipe up in the registry; the raw and buildings rungs
read only the plan's own rates and machine counts and grade such a plan
normally. :func:`badge_for` reaches it through its power rung, and
:func:`rank_plans` reaches it whatever the objective, because the position half
of its key looks up every step even where the scoring looked none up.

WHY rank_plans RE-SCORES AND NEVER RE-SOLVES
----------------------------------------------
:func:`rank_plans` reaches no solve ENTRY POINT. It re-SCORES through
:func:`~clockspeed.solve.optimize.score_plan`, and that call is the only plan
arithmetic anywhere in this module: the only field this module reads off a plan
itself is a step's recipe KEY, so no machine count, raw rate or draw is
recomputed here and no plan is rebuilt. It never calls ``solve_for_targets``,
``evaluate_selection`` or ``optimize_plan``, it imports none of them, and
``tests/solve/test_strategy.py`` asserts both the absence from this module's
source and the absence at runtime. That is what makes the acceptance's third
clause provable rather than asserted: switching the objective changes the ORDER
and cannot change the plan arithmetic, because the plan arithmetic is not
reachable from here. Every published number goes through
:func:`~clockspeed.solve.exact.audit_exact` on the way out, as ``relax.py``
does.

A bare plan carries no ``selection`` field, so the key's position half is taken
from the plan's own step keys in plan order - pillar 1 publishes steps in
REGISTRY order, and ``optimize.py`` guarantees a canonical result's selection
equals its plan's step keys in that same order. The residual, stated rather
than left implied: the key is a total order on DISTINCT selections, so two
plans with the same selection AND the same score are indistinguishable here and
keep their input order. Nothing exact and order-free separates them, and
inventing a second tie-break would be a second statement of a rule
``optimize.py`` owns.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final

from clockspeed.data.registry import Registry
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.optimize import (
    OBJECTIVE_BUILDINGS,
    OBJECTIVE_POWER,
    OBJECTIVE_RAW,
    OBJECTIVES,
    Objective,
    OptimizeError,
    PowerNotComparableError,
    ranking_key,
    registry_positions,
    score_plan,
)
from clockspeed.solve.ratio import ProductionPlan

__all__ = [
    "NOT_CLEARED_OVER_BOUND",
    "NOT_CLEARED_UNPRICEABLE",
    "RUNG_WITHIN_BUILDINGS",
    "RUNG_WITHIN_POWER",
    "RUNG_WITHIN_RAW",
    "STRATEGY_LADDER",
    "RankedPlan",
    "Strategy",
    "StrategyBadge",
    "StrategyError",
    "StrategyUndefinedError",
    "ThresholdCheck",
    "badge_for",
    "check_strategy",
    "check_threshold",
    "rank_plans",
]

#: The rung graded on input rate alone - the weakest of the three.
RUNG_WITHIN_RAW: Final = "within-raw"

#: The rung graded on machine equivalents, which prices no power.
RUNG_WITHIN_BUILDINGS: Final = "within-buildings"

#: The rung graded on draw at each building's own un-sharded clock base. The
#: strongest, because it can only clear where every used recipe is priceable.
RUNG_WITHIN_POWER: Final = "within-power"

#: The reason recorded for a rung whose arithmetic is exact and whose score is
#: above the bound times the reference. An ordinary, informative failure.
NOT_CLEARED_OVER_BOUND: Final = "over-bound"

#: The reason for a rung with no exact evaluation: a used recipe, or one its reference's search
#: reached, has no exact draw. Flagged and skipped, never fatal.
NOT_CLEARED_UNPRICEABLE: Final = "power-not-comparable"

#: The weight every rung scores its single objective at. One, because a rung
#: names ONE direction - the trade-off between directions is the caller's
#: objective to state, not the ladder's to assume.
_RUNG_WEIGHT: Final = Fraction(1)

#: The identity bound. See the module docstring, point 4: it is the
#: multiplicative identity rather than a tuned figure, which is the whole
#: reason the ladder carries no fitted constant.
_IDENTITY_BOUND: Final = Fraction(1)


@dataclass(frozen=True)
class Strategy:
    """One rung: a named objective, the bound it is graded at, and its claim.

    Attributes:
        name: The rung's stable name, as :data:`STRATEGY_LADDER` lists it and as
            every :class:`ThresholdCheck` it produces records.
        objective_name: The single member of
            :data:`~clockspeed.solve.optimize.OBJECTIVES` this rung scores by.
            One name rather than a weighting, because a rung that traded two
            directions off against each other would carry a ratio nothing in
            this project derives.
        bound: The multiplier applied to the reference score. Exact, at or above
            one, and checked by type IDENTITY - an int is exact and still
            manufactures a float the moment it is divided, and
            ``isinstance(True, int)`` is True.
        claims: One authored sentence saying what clearing this rung PROVES,
            for a reader of the table and for the advisor layer that will quote
            it. Never generated from the name, which would restate the name.
    """

    name: str
    objective_name: str
    bound: Fraction
    claims: str


@dataclass(frozen=True)
class ThresholdCheck:
    """One rung's verdict on one plan, with the two numbers it compared.

    Attributes:
        strategy: The rung's name.
        cleared: Whether the plan is within the bound on this rung.
        score: The plan's exact score under the rung's objective, or None when
            the objective has no exact value for this plan or for the reference
            - which today means only an unpriceable power term.
        reference: The reference plan's exact score under the same objective, or
            None on the same condition. Published alongside ``score`` so a
            reader can see WHY the verdict came out as it did without
            re-deriving either number.
        bound: The bound this rung was graded at, carried so the check can be
            read without its :class:`Strategy`.
        reason: Empty when cleared. Otherwise one of the module's
            ``NOT_CLEARED_*`` constants, so a consumer branches on a closed
            vocabulary rather than on prose.
    """

    strategy: str
    cleared: bool
    score: Fraction | None
    reference: Fraction | None
    bound: Fraction
    reason: str


@dataclass(frozen=True)
class StrategyBadge:
    """The strongest claim a plan earned, and every rung's verdict behind it.

    Attributes:
        strongest: The HIGHEST-INDEX cleared rung's name, or None when no rung
            cleared. Not the end of the longest cleared prefix - see the module
            docstring for why the distinction is load-bearing and which fixture
            separates the two readings.
        cleared: Every cleared rung's name, in ladder order. Possibly with a gap
            in it, which is the point.
        checks: One entry per member of :data:`STRATEGY_LADDER`, in ladder
            order, always complete. A rung that could not be evaluated appears
            here as not cleared with a reason rather than being omitted.
    """

    strongest: str | None
    cleared: tuple[str, ...]
    checks: tuple[ThresholdCheck, ...]


@dataclass(frozen=True)
class RankedPlan:
    """One plan's place in a ranking, with the key that put it there.

    Attributes:
        rank: The one-based place in the ranking, one being best.
        plan: The plan, exactly as it was handed in. Never re-solved and never
            rebuilt, which is what makes the third acceptance clause provable.
        score: The plan's exact score under the objective the ranking ran at.
        key: The full :func:`~clockspeed.solve.optimize.ranking_key` this plan
            sorted on - the score paired with its selection's registry
            positions. Published because the position half is invisible in a
            plan's own fields, so a reader cannot otherwise see why two plans
            with equal scores came out in the order they did.
        badge: The plan's badge against the top-ranked member of this same
            ranking or, when the ranking was handed ``references``, against
            each rung's own reference.
    """

    rank: int
    plan: ProductionPlan
    score: Fraction
    key: tuple[Fraction, tuple[int, ...]]
    badge: StrategyBadge


class StrategyError(OptimizeError):
    """Base class for every refusal this module raises.

    A subclass of :class:`~clockspeed.solve.optimize.OptimizeError` for the
    reason that class states: a caller already handling "the answer is not
    computable" from pillar 2 handles this without change, and neither is a
    :class:`ValueError`.
    """


class StrategyUndefinedError(StrategyError):
    """A rung does not state a threshold that can be evaluated.

    Covers a bound below one, a bound that is not exactly a
    :class:`~fractions.Fraction`, a rung naming an objective outside
    :data:`~clockspeed.solve.optimize.OBJECTIVES`, and a ``references`` mapping
    that does not name exactly the ladder's rungs. Each produces a check that
    grades nothing: a bound below one asks a plan to BEAT the reference while
    the rung's prose says "within", an inexact bound converts every value
    derived from it, an unmodeled objective name has no arithmetic at all, and a
    rung with no stated reference has nothing to be graded against.
    """


#: THE ladder. One table, fixed order, weakest claim first; see the module
#: docstring for the order's reasoning and for why every bound is the identity.
#: ``tests/solve/test_strategy.py`` pins this order and reddens on a reorder.
STRATEGY_LADDER: Final[tuple[Strategy, ...]] = (
    Strategy(
        name=RUNG_WITHIN_RAW,
        objective_name=OBJECTIVE_RAW,
        bound=_IDENTITY_BOUND,
        claims="the plan consumes no more raw input per minute than the reference does",
    ),
    Strategy(
        name=RUNG_WITHIN_BUILDINGS,
        objective_name=OBJECTIVE_BUILDINGS,
        bound=_IDENTITY_BOUND,
        claims="the plan asks the player to build no more machine equivalents than the reference",
    ),
    Strategy(
        name=RUNG_WITHIN_POWER,
        objective_name=OBJECTIVE_POWER,
        bound=_IDENTITY_BOUND,
        claims=(
            "the plan draws no more megawatts than the reference at every building's own "
            "un-sharded clock base, and every recipe either plan uses is priceable there"
        ),
    ),
)


def check_strategy(strategy: Strategy) -> None:
    """Refuse a rung that does not state an evaluable threshold.

    Applied by :func:`check_threshold` at the point of use, so a hand-assembled
    :class:`Strategy` cannot reach the arithmetic unchecked - the discipline
    ``optimize.py`` applies to a hand-assembled
    :class:`~clockspeed.solve.optimize.Objective`.

    Args:
        strategy: The rung to check.

    Raises:
        StrategyUndefinedError: Its objective name is not one
            :data:`~clockspeed.solve.optimize.OBJECTIVES` models, or its bound
            is not exactly a Fraction, or its bound is below one.
    """
    if strategy.objective_name not in OBJECTIVES:
        raise StrategyUndefinedError(
            f"the rung {strategy.name!r} names {strategy.objective_name!r}, which is not an "
            f"objective this project models, so it has no arithmetic to grade a plan with. "
            f"Known: {', '.join(OBJECTIVES)}"
        )
    if type(strategy.bound) is not Fraction:
        raise StrategyUndefinedError(
            f"the bound on rung {strategy.name!r} is {type(strategy.bound).__name__} "
            f"{strategy.bound!r}, not a Fraction; one inexact operand converts every value "
            "derived from it while looking correct"
        )
    if strategy.bound < _IDENTITY_BOUND:
        raise StrategyUndefinedError(
            f"the bound on rung {strategy.name!r} is {strategy.bound}, below one, so clearing it "
            "would require the plan to BEAT the reference rather than to be within it - a "
            "different claim from the one the rung's name and prose make"
        )


def _single_objective(strategy: Strategy) -> Objective:
    """Build the one-direction objective a rung scores by.

    Derived from the rung rather than read out of a second table keyed by
    objective name: a parallel table of the same fact drifts, and
    :func:`check_strategy` has already refused a name
    :data:`~clockspeed.solve.optimize.OBJECTIVES` does not hold.

    Args:
        strategy: The rung, already checked.

    Returns:
        The objective weighting that rung's direction at one and nothing else.
    """
    return Objective(weights=MappingProxyType({strategy.objective_name: _RUNG_WEIGHT}))


def _unpriceable_check(strategy: Strategy) -> ThresholdCheck:
    """The verdict of a rung with no exact figure to compare.

    Args:
        strategy: The rung, already checked.

    Returns:
        The rung not cleared under :data:`NOT_CLEARED_UNPRICEABLE`, with no
        score. Audited exact.
    """
    unpriceable = ThresholdCheck(
        strategy=strategy.name,
        cleared=False,
        score=None,
        reference=None,
        bound=strategy.bound,
        reason=NOT_CLEARED_UNPRICEABLE,
    )
    audit_exact(unpriceable, path="check")
    return unpriceable


def check_threshold(
    registry: Registry,
    plan: ProductionPlan,
    reference: ProductionPlan,
    strategy: Strategy,
) -> ThresholdCheck:
    """Grade one plan against one reference on one rung.

    The comparison is ``score(plan) <= bound * score(reference)``, a product and
    never a quotient - see the module docstring for the four reasons.

    Args:
        registry: The built registry.
        plan: The plan being graded.
        reference: The plan it is graded against. REQUIRED, with no default -
            see the module docstring.
        strategy: The rung.

    Returns:
        The verdict, with both scores when they exist. Audited exact.

    Raises:
        StrategyUndefinedError: The rung states no evaluable threshold.
        ObjectiveUndefinedError: Propagates from
            :func:`~clockspeed.solve.optimize.score_plan`, never absorbed - a
            malformed objective is not a failed threshold. Every rung that
            passes :func:`check_strategy` builds a well-formed objective, so
            this is the guard behind that check rather than a path such a rung
            reaches.
        KeyError: The rung scores by power and pricing either plan reaches a
            step naming a recipe this registry does not model. Propagates,
            never absorbed; a raw or buildings rung looks no recipe up and
            grades such a plan normally.
    """
    check_strategy(strategy)
    objective = _single_objective(strategy)
    try:
        score = score_plan(registry, plan, objective)
        reference_score = score_plan(registry, reference, objective)
    except PowerNotComparableError:
        return _unpriceable_check(strategy)

    cleared = score <= strategy.bound * reference_score
    check = ThresholdCheck(
        strategy=strategy.name,
        cleared=cleared,
        score=score,
        reference=reference_score,
        bound=strategy.bound,
        reason="" if cleared else NOT_CLEARED_OVER_BOUND,
    )
    audit_exact(check, path="check")
    return check


def _badge_of(checks: tuple[ThresholdCheck, ...]) -> StrategyBadge:
    """Publish the badge one verdict per rung adds up to.

    The one statement of the rule, shared by :func:`badge_for` and a ranking
    graded against ``references``, so the two cannot disagree on what strongest
    means.

    Args:
        checks: One verdict per member of :data:`STRATEGY_LADDER`, in ladder
            order.

    Returns:
        The badge, its ``strongest`` the highest-index cleared rung. Audited
        exact.
    """
    cleared = tuple(check.strategy for check in checks if check.cleared)
    badge = StrategyBadge(
        strongest=cleared[-1] if cleared else None,
        cleared=cleared,
        checks=checks,
    )
    audit_exact(badge, path="badge")
    return badge


def badge_for(registry: Registry, plan: ProductionPlan, reference: ProductionPlan) -> StrategyBadge:
    """Grade a plan on every rung and record the strongest claim it cleared.

    Args:
        registry: The built registry.
        plan: The plan being graded.
        reference: The plan it is graded against. REQUIRED, with no default.

    Returns:
        The badge. ``checks`` holds one entry per rung in ladder order and
        ``strongest`` is the highest-index cleared rung - NOT the end of the
        longest cleared prefix, which the module docstring argues at length.
        Audited exact.

    Raises:
        StrategyUndefinedError: Some rung states no evaluable threshold.
        ObjectiveUndefinedError: Propagates, as :func:`check_threshold`
            documents.
        KeyError: The power rung's pricing reaches a recipe this registry does
            not model, as :func:`check_threshold` documents.
    """
    return _badge_of(
        tuple(check_threshold(registry, plan, reference, strategy) for strategy in STRATEGY_LADDER)
    )


def _check_references(references: Mapping[str, ProductionPlan | None]) -> None:
    """Refuse a ``references`` mapping that does not name exactly the ladder's rungs.

    Args:
        references: Rung name to the plan that rung is graded against.

    Raises:
        StrategyUndefinedError: A rung has no entry, or an entry names no rung.
            The message names rungs, never a plan.
    """
    ladder = tuple(strategy.name for strategy in STRATEGY_LADDER)
    missing = [name for name in ladder if name not in references]
    if missing:
        raise StrategyUndefinedError(
            f"references names no plan for {', '.join(missing)}. None states that a rung has "
            "nothing exact to compare with, and an absent rung states nothing"
        )
    strays = sorted(name for name in references if name not in ladder)
    if strays:
        raise StrategyUndefinedError(
            f"references names {', '.join(strays)}, which the ladder does not hold, so nothing "
            "would ever read it"
        )


def _badge_against(
    registry: Registry,
    plan: ProductionPlan,
    references: Mapping[str, ProductionPlan | None],
) -> StrategyBadge:
    """Grade a plan on every rung against that rung's own reference.

    Args:
        registry: The built registry.
        plan: The plan being graded.
        references: Rung name to its reference, already checked. None reads as
            :data:`NOT_CLEARED_UNPRICEABLE` for that rung.

    Returns:
        The badge, as :func:`badge_for` publishes one. Audited exact.

    Raises:
        StrategyUndefinedError, ObjectiveUndefinedError, KeyError: As
            :func:`check_threshold` raises them.
    """
    checks: list[ThresholdCheck] = []
    for strategy in STRATEGY_LADDER:
        reference = references[strategy.name]
        if reference is None:
            check_strategy(strategy)
            checks.append(_unpriceable_check(strategy))
        else:
            checks.append(check_threshold(registry, plan, reference, strategy))
    return _badge_of(tuple(checks))


def _plan_selection(plan: ProductionPlan) -> tuple[str, ...]:
    """Recover the recipe keys a bare plan uses, in registry order.

    A plan carries no ``selection`` field; pillar 1 publishes its steps in
    registry order, and ``optimize.py`` guarantees a canonical result's
    selection equals its plan's step keys in that order. So reading the steps
    in plan order reaches the same tuple a result would have published, without
    this module having to re-sort anything or consult the registry a second
    time.

    Args:
        plan: The plan.

    Returns:
        The step recipe keys, in plan order.
    """
    return tuple(step.recipe_key for step in plan.steps)


def _plan_rank_key(
    registry_index: Mapping[str, int], plan: ProductionPlan, score: Fraction
) -> tuple[Fraction, tuple[int, ...]]:
    """Build one plan's ranking key under a score it was handed.

    Args:
        registry_index: A position mapping, as
            :func:`~clockspeed.solve.optimize.ranking_key` documents it.
        plan: The plan.
        score: Its exact score under the ranking's objective.

    Returns:
        The key. Lower wins.
    """
    return ranking_key(score, _plan_selection(plan), registry_index)


def rank_plans(
    registry: Registry,
    plans: Sequence[ProductionPlan],
    *,
    objective: Objective,
    references: Mapping[str, ProductionPlan | None] | None = None,
) -> tuple[RankedPlan, ...]:
    """Rank plans under one objective by RE-SCORING them, never by re-solving.

    The reference for every badge is this ranking's own top-ranked member,
    which is the one reference this function does not have to invent, unless
    the caller states one per rung through ``references``. The module docstring
    holds why a caller about to advise a plan states them.

    Args:
        registry: The built registry.
        plans: The plans to rank, in any order. Not mutated and not rebuilt;
            each :attr:`RankedPlan.plan` is the object that was handed in.
        objective: What to rank by. Switching it changes the ORDER and nothing
            else, because no plan arithmetic is reachable from here.
        references: Rung name to the plan that rung grades every entry against,
            None for a rung with nothing exact to compare with. It moves the
            badges and nothing else. Left None, every badge is graded against
            the top-ranked member.

    Returns:
        The plans in rank order, best first, each with its score, its full
        ranking key and its badge. Empty for an empty input - a badge needs a
        reference and an empty ranking has none, so there is nothing to invent.
        Audited exact.

    Raises:
        StrategyUndefinedError: ``references`` does not name exactly the ladder's
            rungs. Refused whatever ``plans`` holds, the empty input included.
        ObjectiveUndefinedError: The objective names no usable direction.
        PowerNotComparableError: The objective weights power and some used
            recipe has no exact draw. NOT absorbed here: the caller asked for a
            RANKING by power and there is no order to publish. The per-rung
            absorption in :func:`check_threshold` is a different question.
        KeyError: Some plan names a recipe this registry does not model.
            Whatever the objective, unless a refusal above is reached first:
            an objective whose scoring looks no recipe up is still followed by
            the position half of the key, which looks every step up in
            :func:`~clockspeed.solve.optimize.registry_positions`.
    """
    if references is not None:
        _check_references(references)
    if not plans:
        return ()

    registry_index = registry_positions(registry)
    scored = [(score_plan(registry, plan, objective), plan) for plan in plans]
    ordered = sorted(scored, key=lambda entry: _plan_rank_key(registry_index, entry[1], entry[0]))
    reference = ordered[0][1]

    ranked = tuple(
        RankedPlan(
            rank=place,
            plan=plan,
            score=score,
            key=_plan_rank_key(registry_index, plan, score),
            badge=(
                badge_for(registry, plan, reference)
                if references is None
                else _badge_against(registry, plan, references)
            ),
        )
        for place, (score, plan) in enumerate(ordered, start=1)
    )
    audit_exact(ranked, path="ranked")
    return ranked
