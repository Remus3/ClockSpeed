"""CS-1346 and CS-1351: a rule that reads a plan, so a trace carries its strategy badge.

Graded here, against CS-1346's acceptance in ``docs/item_notes/phase5.md``:

- a rule trace carries a :class:`clockspeed.solve.strategy.StrategyBadge`,
  produced by a rule that reads a plan - ``plan.adopt`` reads the
  :class:`~clockspeed.solve.ratio.ProductionPlan` and the badge one
  :func:`~clockspeed.solve.strategy.rank_plans` call published together;
- the card's tier-3 derivation renders that badge FROM THE TRACE, generated and
  never hand-written: the whole derivation is pinned line by line, and a badge
  swapped into the TRACE (never into the rule or the world) moves exactly the
  badge's line and nothing else;
- the same synthetic fixture world shows nothing of the badge in tier 1: no
  rung name, no rung claim and no badge vocabulary, and a different badge on
  the same plan leaves tier 1 and the card id unchanged while tier 3 moves;
- ``clockspeed/advisor/cards.py::Card`` takes no new constructor parameter -
  its single ``trace`` field stays the only one, with a control showing the
  predicate sees a widened dataclass.

Beside the acceptance, the rule's own contract: a plan that cleared no rung is
rejected and settles the rule; a badge whose summary disagrees with its checks
is a rule error and no card; a plan's recipe unlocks travel in
``Recommendation.requires`` so the ENGINE refuses a plan over a locked recipe;
off the pin, tier 2 names both builds and the headline does not move. One arm
runs a REAL ranking over the synthetic solve corpus end to end.

CS-1351 adds the status: every world offers one, a status other than ranked
records one indeterminate step and no card, a status outside the vocabulary is a
rule error, and the firing path records one indeterminate step too, so only the
rejection of a plan that cleared no rung settles the rule. What the search left
out reaches tier 2 as a count, ahead of the build caveat, and tier 3 by name, and a
refused trace reads it too. The backend that ran reaches tier 3 and nothing else.
``tests/advisor/test_plan_world.py`` grades the same rule through ``advise_world``.
``tests/advisor/test_plan_redesign.py`` grades the family's second rule (CS-1371).

EVERY WORLD IS SYNTHETIC. The plans and badges are hand-built from invented
recipes, items and exact figures, or solved from ``tests/solve/synthetic.py``'s
invented registry; the build inputs are ``tests/advisor/build_fixtures.py``'s,
the pin read at test time. No save, docs file or install is read.
"""

from __future__ import annotations

import dataclasses
import inspect
from dataclasses import dataclass, replace
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor.advise import advise, settled_rules
from clockspeed.advisor.build import BUILD_INPUTS
from clockspeed.advisor.cards import Card, card_for, render_value
from clockspeed.advisor.ledger import Ledger, MuteStore
from clockspeed.advisor.rules.plan import (
    ADOPT_RULE,
    IN_BACKEND,
    IN_BADGE,
    IN_PLAN,
    IN_REQUIRES,
    IN_STATUS,
    IN_TRIMMED,
    IN_UNCHECKED,
    IN_UNMATCHED,
    PLAN_INPUTS,
    REDESIGN_INPUTS,
    REDESIGN_RULE,
    RULES,
    STATUS_NO_PLAN,
    STATUS_NO_TARGET,
    STATUS_POWER_NOT_COMPARABLE,
    STATUS_RANKED,
    STATUS_REQUEST_MALFORMED,
    STATUS_SOLVE_REFUSED,
    plan_inputs,
    refused_inputs,
    status_inputs,
)
from clockspeed.advisor.trace import InputValue, StepKind, Trace, WorldInputs, run_rule
from clockspeed.audit.build import WARN_BUILD_MISMATCH
from clockspeed.solve.optimize import weighted_objective
from clockspeed.solve.ratio import (
    BYPRODUCT_BALANCED,
    PlanStep,
    ProductionPlan,
    RatioRequest,
    solve_for_targets,
)
from clockspeed.solve.strategy import (
    NOT_CLEARED_OVER_BOUND,
    RUNG_WITHIN_BUILDINGS,
    RUNG_WITHIN_POWER,
    RUNG_WITHIN_RAW,
    STRATEGY_LADDER,
    RankedPlan,
    StrategyBadge,
    ThresholdCheck,
    rank_plans,
)
from tests.advisor.build_fixtures import (
    OFF_PIN_OFFSETS,
    docs_pin,
    game_pin,
    off_pin_build_inputs,
    pinned_build_inputs,
)
from tests.solve.synthetic import (
    C3_GADGET_TARGET,
    C5_TRINKET_TARGET,
    FLUID_RECIPE,
    GADGET_RECIPE,
    PLATE_RECIPE,
    RECOVER_RECIPE,
    SOLVE_GADGET_ITEM,
    SOLVE_ORE_ITEM,
    SOLVE_TRINKET_ITEM,
    STD_GADGET_RECIPE,
    solve_registry,
)

if TYPE_CHECKING:
    from pathlib import Path

#: The invented items and recipes of the hand-built plan.
GADGET_ITEM: Final = "Desc_SyntheticGadget_C"
ORE_ITEM: Final = "Desc_SyntheticOre_C"
GADGET_STEP: Final = "Recipe_SyntheticGadget_C"
PLATE_STEP: Final = "Recipe_SyntheticPlate_C"

#: The unlock key the hand-built plan's caller says its recipes need.
GADGET_UNLOCK: Final = "recipe:/Game/Synthetic/Recipe_SyntheticGadget.Recipe_SyntheticGadget_C"

#: An invented 22-character world token for the one advise() arm.
TOKEN: Final = "PPPPsyntheticTokenPPPP"  # noqa: S105 - a synthetic world token, not a secret

#: Words that would mean the badge leaked into a headline.
BADGE_WORDS: Final = ("badge", "strongest", "cleared", "rung", "within", "bound")

#: The backend names the rule may read, spelled here rather than imported.
EXHAUSTIVE: Final = "exhaustive"
GREEDY: Final = "greedy"


def _check(name: str, *, cleared: bool, score: Fraction, reference: Fraction) -> ThresholdCheck:
    """One invented rung verdict at the identity bound."""
    return ThresholdCheck(
        strategy=name,
        cleared=cleared,
        score=score,
        reference=reference,
        bound=Fraction(1),
        reason="" if cleared else NOT_CLEARED_OVER_BOUND,
    )


def _badge() -> StrategyBadge:
    """The non-monotone badge: raw over its bound, buildings and power cleared."""
    return StrategyBadge(
        strongest=RUNG_WITHIN_POWER,
        cleared=(RUNG_WITHIN_BUILDINGS, RUNG_WITHIN_POWER),
        checks=(
            _check(RUNG_WITHIN_RAW, cleared=False, score=Fraction(120), reference=Fraction(60)),
            _check(RUNG_WITHIN_BUILDINGS, cleared=True, score=Fraction(3), reference=Fraction(6)),
            _check(RUNG_WITHIN_POWER, cleared=True, score=Fraction(45), reference=Fraction(436, 3)),
        ),
    )


def _buildings_only_badge() -> StrategyBadge:
    """A second badge for the same plan: only the buildings rung cleared."""
    return StrategyBadge(
        strongest=RUNG_WITHIN_BUILDINGS,
        cleared=(RUNG_WITHIN_BUILDINGS,),
        checks=(
            _check(RUNG_WITHIN_RAW, cleared=False, score=Fraction(120), reference=Fraction(60)),
            _check(RUNG_WITHIN_BUILDINGS, cleared=True, score=Fraction(3), reference=Fraction(6)),
            _check(RUNG_WITHIN_POWER, cleared=False, score=Fraction(50), reference=Fraction(45)),
        ),
    )


def _no_rung_badge() -> StrategyBadge:
    """A badge that cleared nothing: the plan is worse than its reference on every rung."""
    return StrategyBadge(
        strongest=None,
        cleared=(),
        checks=(
            _check(RUNG_WITHIN_RAW, cleared=False, score=Fraction(120), reference=Fraction(60)),
            _check(RUNG_WITHIN_BUILDINGS, cleared=False, score=Fraction(9), reference=Fraction(6)),
            _check(RUNG_WITHIN_POWER, cleared=False, score=Fraction(50), reference=Fraction(45)),
        ),
    )


def _plan() -> ProductionPlan:
    """An invented two-step plan: 30 Gadget a minute from 13/3 machine equivalents."""
    return ProductionPlan(
        steps=(
            PlanStep(recipe_key=GADGET_STEP, machines=Fraction(3)),
            PlanStep(recipe_key=PLATE_STEP, machines=Fraction(4, 3)),
        ),
        targets=MappingProxyType({GADGET_ITEM: Fraction(30)}),
        raw_inputs=MappingProxyType({ORE_ITEM: Fraction(120)}),
        byproducts=MappingProxyType({}),
        excluded=(),
        byproduct_policy=BYPRODUCT_BALANCED,
    )


def _ranked(badge: StrategyBadge | None = None, plan: ProductionPlan | None = None) -> RankedPlan:
    """One ranking entry carrying the plan and its badge together."""
    return RankedPlan(
        rank=2,
        plan=_plan() if plan is None else plan,
        score=Fraction(120),
        key=(Fraction(120), (0, 1)),
        badge=_badge() if badge is None else badge,
    )


def _world(
    ranked: RankedPlan | None = None,
    *,
    build: dict[str, InputValue] | None = None,
    requires: tuple[str, ...] = (GADGET_UNLOCK,),
    unlocks: frozenset[str] = frozenset({GADGET_UNLOCK}),
    trimmed: tuple[str, ...] = (),
    unchecked: tuple[str, ...] = (),
    unmatched_unlocks: int = 0,
    backend: str = EXHAUSTIVE,
) -> WorldInputs:
    """A synthetic world offering the build inputs and one ranked plan."""
    offered = pinned_build_inputs(game_pin()) if build is None else build
    values = offered | plan_inputs(
        _ranked() if ranked is None else ranked,
        requires=requires,
        trimmed=trimmed,
        unchecked=unchecked,
        unmatched_unlocks=unmatched_unlocks,
        backend=backend,
    )
    return WorldInputs(values=values, unlocks=unlocks)


def _card(world: WorldInputs) -> Card:
    card = card_for(run_rule(ADOPT_RULE, world))
    assert card is not None
    return card


def _badge_index(trace: Trace) -> int:
    """The position of the one read step that carries the badge."""
    found = [
        index
        for index, step in enumerate(trace.steps)
        if step.kind is StepKind.INPUT_READ and step.subject == IN_BADGE
    ]
    assert len(found) == 1
    return found[0]


def expected_tier3(pin: int) -> str:
    """The whole on-pin derivation of the hand-built plan's card, the pin read at test time."""
    docs = docs_pin()
    return "\n".join(
        [
            "Derivation of rule plan.adopt (domain plan)",
            "Advice: Build the planned production chain for Desc_SyntheticGadget_C",
            "Because: It makes 30.00 per minute of Desc_SyntheticGadget_C with"
            " 4.33 (exactly 13/3) machine equivalents",
            "Target milestone: none",
            "Steps:",
            f"  1. Read build.save_changelist = {pin} from audit.build.save_changelist",
            f"  2. Read build.pinned_changelist = {pin} from audit.build.pinned_changelist",
            "  3. Read build.warnings = {} from audit.build.warnings",
            f'  4. Read build.registry_sha256 = "{docs}" from audit.build.registry.source_sha256',
            f'  5. Read build.pinned_docs_sha256 = "{docs}" from'
            " audit.build.registry.pinned_sha256",
            "  6. Read build.registry_warnings = {} from audit.build.registry.warnings",
            '  7. Read plan.status = "ranked" from advisor.plans.status',
            "  8. Read plan.unchecked = () from advisor.plans.unchecked",
            "  9. Read plan.unmatched_unlocks = 0 from advisor.plans.unmatched_unlocks",
            "  10. Read plan.trimmed = () from solve.bound.trim_record.removed",
            "  11. Read plan.production = ProductionPlan(steps=("
            'PlanStep(recipe_key="Recipe_SyntheticGadget_C", machines=3.00), '
            'PlanStep(recipe_key="Recipe_SyntheticPlate_C", machines=1.33 (exactly 4/3))), '
            'targets={"Desc_SyntheticGadget_C": 30.00}, '
            'raw_inputs={"Desc_SyntheticOre_C": 120.00}, byproducts={}, excluded=(), '
            'byproduct_policy="balanced") from solve.strategy.ranked_plan.plan',
            '  12. Read plan.badge = StrategyBadge(strongest="within-power", '
            'cleared=("within-buildings", "within-power"), checks=('
            'ThresholdCheck(strategy="within-raw", cleared=false, score=120.00, '
            'reference=60.00, bound=1.00, reason="over-bound"), '
            'ThresholdCheck(strategy="within-buildings", cleared=true, score=3.00, '
            'reference=6.00, bound=1.00, reason=""), '
            'ThresholdCheck(strategy="within-power", cleared=true, score=45.00, '
            'reference=145.33 (exactly 436/3), bound=1.00, reason=""))) '
            "from solve.strategy.ranked_plan.badge",
            "  13. Read plan.requires = "
            '("recipe:/Game/Synthetic/Recipe_SyntheticGadget.Recipe_SyntheticGadget_C") '
            "from advisor.plans.recipe_unlock_join",
            '  14. Read plan.backend = "exhaustive" from solve.optimize.optimize_result.backend',
            "  15. Computed plan machine equivalents = 4.33 (exactly 13/3)",
            "  16. Indeterminate compare the plan with what is built:"
            " a plan is ranked for a stated target and never compared with the world",
            "  17. Rule plan.adopt fired for plan:Desc_SyntheticGadget_C",
        ]
    )


# --- the acceptance ----------------------------------------------------------


def test_the_trace_carries_the_badge_read_by_a_rule_that_reads_a_plan() -> None:
    ranked = _ranked()
    trace = run_rule(ADOPT_RULE, _world(ranked))
    assert trace.recommendation is not None
    reads = [step for step in trace.steps if step.kind is StepKind.INPUT_READ]
    read_names = tuple(step.subject for step in reads)
    assert read_names == (*BUILD_INPUTS, *PLAN_INPUTS)
    plan_value = reads[read_names.index(IN_PLAN)].value
    badge_value = reads[read_names.index(IN_BADGE)].value
    assert type(plan_value) is ProductionPlan
    assert plan_value is ranked.plan
    assert type(badge_value) is StrategyBadge
    assert badge_value is ranked.badge


def test_tier3_renders_the_badge_generated_from_the_trace() -> None:
    card = _card(_world())
    derivation = card.tier3
    assert derivation == expected_tier3(game_pin())


def test_a_badge_swapped_into_the_trace_moves_exactly_its_own_tier3_line() -> None:
    """The rule never sees the swapped badge, so only a renderer reading the trace shows it."""
    trace = run_rule(ADOPT_RULE, _world())
    index = _badge_index(trace)
    swapped_badge = _buildings_only_badge()
    swapped_step = replace(trace.steps[index], value=swapped_badge)
    swapped = replace(trace, steps=(*trace.steps[:index], swapped_step, *trace.steps[index + 1 :]))

    before = Card(trace).tier3.splitlines()
    after = Card(swapped).tier3.splitlines()
    assert len(before) == len(after)
    changed = [
        number for number, (old, new) in enumerate(zip(before, after, strict=True)) if old != new
    ]
    header = 5
    assert changed == [header + index]
    line = after[header + index]
    rendered = render_value(swapped_badge)
    assert rendered in line
    assert 'strongest="within-buildings"' in line


def test_tier1_shows_nothing_of_the_badge() -> None:
    card = _card(_world())
    headline = card.tier1.lower()
    vocabulary = (
        *(strategy.name for strategy in STRATEGY_LADDER),
        *(strategy.claims for strategy in STRATEGY_LADDER),
        *BADGE_WORDS,
    )
    leaked = [word for word in vocabulary if word.lower() in headline]
    assert leaked == []

    # The control: the same predicate sees a headline that names a rung.
    trace = card.trace
    recommendation = trace.recommendation
    assert recommendation is not None
    naming = replace(recommendation, action=recommendation.action + " (" + RUNG_WITHIN_POWER + ")")
    forged = Card(replace(trace, recommendation=naming)).tier1.lower()
    seen = [word for word in vocabulary if word.lower() in forged]
    assert RUNG_WITHIN_POWER in seen


def test_a_different_badge_on_the_same_plan_moves_tier3_and_never_tier1() -> None:
    first = _card(_world(_ranked(_badge())))
    second = _card(_world(_ranked(_buildings_only_badge())))
    same_headline = first.tier1 == second.tier1
    assert same_headline
    same_id = first.id == second.id
    assert same_id
    moved = first.tier3 != second.tier3
    assert moved
    moved_lines = [
        old
        for old, new in zip(first.tier3.splitlines(), second.tier3.splitlines(), strict=True)
        if old != new
    ]
    assert len(moved_lines) == 1
    assert moved_lines[0].startswith("  12. Read plan.badge = StrategyBadge(")


def test_the_backend_moves_exactly_its_own_tier3_line_and_never_tier1_or_the_id() -> None:
    """CS-1351: on one plan the backend's name moves exactly its own tier 3 line."""
    first = _card(_world(backend=EXHAUSTIVE))
    second = _card(_world(backend=GREEDY))
    same_headline = first.tier1 == second.tier1
    assert same_headline
    same_reason = first.tier2 == second.tier2
    assert same_reason
    same_id = first.id == second.id
    assert same_id
    moved = [
        (old, new)
        for old, new in zip(first.tier3.splitlines(), second.tier3.splitlines(), strict=True)
        if old != new
    ]
    assert moved == [
        (
            '  14. Read plan.backend = "exhaustive" from solve.optimize.optimize_result.backend',
            '  14. Read plan.backend = "greedy" from solve.optimize.optimize_result.backend',
        )
    ]


def _constructor_names(cls: type) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """A dataclass's field names and its constructor's parameter names."""
    return (
        tuple(field.name for field in dataclasses.fields(cls)),
        tuple(inspect.signature(cls).parameters),
    )


def test_card_keeps_its_one_trace_field() -> None:
    assert _constructor_names(Card) == (("trace",), ("trace",))

    @dataclass(frozen=True)
    class _Widened:
        trace: Trace
        badge: StrategyBadge | None = None

    assert _constructor_names(_Widened) == (("trace", "badge"), ("trace", "badge"))


# --- the rule's own contract -------------------------------------------------


def test_a_plan_that_cleared_no_rung_is_rejected_and_settles_the_rule() -> None:
    trace = run_rule(ADOPT_RULE, _world(_ranked(_no_rung_badge())))
    assert trace.recommendation is None
    kinds = [step.kind for step in trace.steps]
    assert kinds.count(StepKind.ALTERNATIVE_REJECTED) == 1
    assert StepKind.RULE_ERROR not in kinds
    assert settled_rules((trace,)) == frozenset({ADOPT_RULE.rule_id})


@pytest.mark.parametrize(
    "forged",
    [
        replace(_badge(), strongest=RUNG_WITHIN_RAW),
        replace(_badge(), cleared=(RUNG_WITHIN_POWER,)),
        replace(_badge(), checks=tuple(reversed(_badge().checks))),
        replace(_badge(), checks=_badge().checks[:2]),
        replace(_no_rung_badge(), strongest=RUNG_WITHIN_POWER),
    ],
    ids=["strongest-not-last", "cleared-not-checks", "out-of-order", "a-rung-missing", "none"],
)
def test_a_badge_whose_summary_disagrees_with_its_checks_is_a_rule_error(
    forged: StrategyBadge,
) -> None:
    control = run_rule(ADOPT_RULE, _world(_ranked(_badge())))
    assert control.recommendation is not None

    trace = run_rule(ADOPT_RULE, _world(_ranked(forged)))
    assert trace.recommendation is None
    errors = [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]
    assert errors == ["ValueError"]


def test_an_input_of_the_wrong_type_is_a_rule_error() -> None:
    plan = _plan()
    badge = _badge()
    swapped = {IN_PLAN: badge, IN_BADGE: plan}
    for name, wrong in swapped.items():
        values = dict(_world().values)
        values[name] = InputValue(wrong, values[name].source)
        trace = run_rule(ADOPT_RULE, WorldInputs(values=values, unlocks=frozenset({GADGET_UNLOCK})))
        assert trace.recommendation is None, name
        errors = [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]
        assert errors == ["TypeError"], name


def test_a_plan_over_a_locked_recipe_is_refused_by_the_engine() -> None:
    held = run_rule(ADOPT_RULE, _world())
    assert held.recommendation is not None
    assert held.recommendation.requires == (GADGET_UNLOCK,)

    locked = run_rule(ADOPT_RULE, _world(unlocks=frozenset()))
    assert locked.recommendation is None
    assert locked.unmet == (GADGET_UNLOCK,)


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS)
def test_off_the_pin_tier2_names_both_builds_and_the_headline_holds(offset: int) -> None:
    pin = game_pin()
    on = _card(_world())
    off_trace = run_rule(ADOPT_RULE, _world(build=off_pin_build_inputs(pin, offset)))
    off = card_for(off_trace)
    assert off is not None
    same_headline = off.tier1 == on.tier1
    assert same_headline
    caveat = (
        f"; {WARN_BUILD_MISMATCH}: priced at the pinned build {pin},"
        f" not the save build {pin + offset}"
    )
    named = off.tier2 == on.tier2 + caveat
    assert named
    assert settled_rules((off_trace,)) == frozenset()


def test_the_adapter_offers_the_ranked_plan_its_badge_and_the_joined_unlock_keys() -> None:
    ranked = _ranked()
    offered = plan_inputs(
        ranked,
        requires=(GADGET_UNLOCK,),
        trimmed=(PLATE_STEP,),
        unchecked=(GADGET_STEP,),
        unmatched_unlocks=UNMATCHED_THREE,
        backend=GREEDY,
    )
    assert tuple(offered) == PLAN_INPUTS
    assert offered[IN_STATUS].value == STATUS_RANKED
    assert offered[IN_PLAN].value is ranked.plan
    assert offered[IN_BADGE].value is ranked.badge
    assert offered[IN_REQUIRES].value == (GADGET_UNLOCK,)
    assert offered[IN_TRIMMED].value == (PLATE_STEP,)
    assert offered[IN_UNCHECKED].value == (GADGET_STEP,)
    assert offered[IN_UNMATCHED].value == UNMATCHED_THREE
    assert offered[IN_BACKEND].value == GREEDY
    sources = tuple(offered[name].source for name in PLAN_INPUTS)
    assert sources == (
        "advisor.plans.status",
        "advisor.plans.unchecked",
        "advisor.plans.unmatched_unlocks",
        "solve.bound.trim_record.removed",
        "solve.strategy.ranked_plan.plan",
        "solve.strategy.ranked_plan.badge",
        "advisor.plans.recipe_unlock_join",
        "solve.optimize.optimize_result.backend",
    )


#: Unmatched unlock counts these arms offer, named so each reads as a plant.
UNMATCHED_THREE: Final = 3
UNMATCHED_TWO: Final = 2

#: Every status but ranked, and the words its one indeterminate reason carries.
REFUSED_STATUSES: Final = (
    (
        STATUS_NO_PLAN,
        "the search found no plan over the unlocked automated recipes it kept,"
        " under the stated byproduct policy",
    ),
    (STATUS_SOLVE_REFUSED, "the search refused, which says nothing about the target"),
    (STATUS_POWER_NOT_COMPARABLE, "the power search reached a recipe with no exact draw"),
)

#: The two statuses whose reason needs nothing else read, with those reasons.
UNJOINED_STATUSES: Final = (
    (STATUS_NO_TARGET, "no target was stated, so no plan was ranked"),
    (STATUS_REQUEST_MALFORMED, "the stated request cannot be asked as a question"),
)


def _status_world(offered: dict[str, InputValue]) -> WorldInputs:
    """A synthetic world offering the build inputs and one status adapter's inputs."""
    return WorldInputs(
        values=pinned_build_inputs(game_pin()) | offered, unlocks=frozenset({GADGET_UNLOCK})
    )


def _assert_undecided(trace: Trace, reason: str) -> None:
    """One indeterminate step with this reason, no card, no fault, and no settling."""
    assert card_for(trace) is None
    indeterminate = [s for s in trace.steps if s.kind is StepKind.VERDICT_INDETERMINATE]
    count = len(indeterminate)
    assert count == 1
    assert indeterminate[0].subject == "build the ranked plan"
    assert indeterminate[0].reason == reason
    kinds = {step.kind for step in trace.steps}
    assert kinds == {StepKind.INPUT_READ, StepKind.VERDICT_INDETERMINATE}
    settled = ADOPT_RULE.rule_id in settled_rules((trace,))
    assert not settled


@pytest.mark.parametrize(
    ("status", "reason"), UNJOINED_STATUSES, ids=[s for s, _ in UNJOINED_STATUSES]
)
def test_a_status_before_any_join_reads_the_status_alone(status: str, reason: str) -> None:
    trace = run_rule(ADOPT_RULE, _status_world(status_inputs(status)))
    _assert_undecided(trace, reason)
    reads = [step.subject for step in trace.steps if step.kind is StepKind.INPUT_READ]
    assert reads == [*BUILD_INPUTS, IN_STATUS]


@pytest.mark.parametrize(
    ("status", "reason"), REFUSED_STATUSES, ids=[s for s, _ in REFUSED_STATUSES]
)
def test_a_status_after_a_join_also_reads_what_the_join_left_out(status: str, reason: str) -> None:
    offered = refused_inputs(
        status,
        trimmed=(PLATE_STEP,),
        unchecked=(GADGET_STEP,),
        unmatched_unlocks=UNMATCHED_TWO,
    )
    trace = run_rule(ADOPT_RULE, _status_world(offered))
    _assert_undecided(trace, reason)
    reads = {step.subject: step.value for step in trace.steps if step.kind is StepKind.INPUT_READ}
    assert reads[IN_UNCHECKED] == (GADGET_STEP,)
    assert reads[IN_UNMATCHED] == UNMATCHED_TWO
    assert reads[IN_TRIMMED] == (PLATE_STEP,)
    # The ranked path's own inputs are not offered here, and a read of one would say so.
    assert IN_BACKEND not in reads
    assert IN_PLAN not in reads


def test_a_trimmed_of_the_wrong_shape_on_a_refused_path_is_a_rule_error() -> None:
    values = dict(
        refused_inputs(STATUS_NO_PLAN, trimmed=(), unchecked=(), unmatched_unlocks=0),
    )
    values[IN_TRIMMED] = InputValue(GADGET_STEP, values[IN_TRIMMED].source)
    trace = run_rule(ADOPT_RULE, _status_world(values))
    assert card_for(trace) is None
    errors = [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]
    assert errors == ["TypeError"]


def test_a_status_outside_the_vocabulary_is_a_rule_error() -> None:
    trace = run_rule(ADOPT_RULE, _status_world(status_inputs("synthetic-status")))
    assert trace.recommendation is None
    errors = [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]
    assert errors == ["ValueError"]


def test_a_status_that_is_not_text_is_a_rule_error() -> None:
    offered = {IN_STATUS: InputValue(Fraction(1), "synthetic.status")}
    trace = run_rule(ADOPT_RULE, _status_world(offered))
    errors = [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]
    assert errors == ["TypeError"]


@pytest.mark.parametrize(
    ("name", "wrong", "error"),
    [
        (IN_UNCHECKED, GADGET_STEP, "TypeError"),
        (IN_TRIMMED, GADGET_STEP, "TypeError"),
        (IN_REQUIRES, (Fraction(1),), "TypeError"),
        (IN_UNMATCHED, True, "TypeError"),
        (IN_BACKEND, "no-such-backend", "ValueError"),
        (IN_BACKEND, Fraction(1), "ValueError"),
    ],
    ids=[
        "unchecked",
        "trimmed",
        "requires",
        "unmatched",
        "backend-outside-the-vocabulary",
        "backend-not-text",
    ],
)
def test_a_left_out_input_of_the_wrong_shape_is_a_rule_error(
    name: str, wrong: object, error: str
) -> None:
    values = dict(_world().values)
    values[name] = InputValue(wrong, values[name].source)
    trace = run_rule(ADOPT_RULE, WorldInputs(values=values, unlocks=frozenset({GADGET_UNLOCK})))
    assert trace.recommendation is None
    errors = [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]
    assert errors == [error]


def test_firing_records_one_indeterminate_step_so_it_settles_nothing() -> None:
    """A plan is never compared with the world, so its card going says nothing about it."""
    trace = run_rule(ADOPT_RULE, _world())
    assert trace.recommendation is not None
    undecided = [s for s in trace.steps if s.kind is StepKind.VERDICT_INDETERMINATE]
    count = len(undecided)
    assert count == 1
    assert undecided[0].subject == "compare the plan with what is built"
    assert undecided[0].reason == (
        "a plan is ranked for a stated target and never compared with the world"
    )
    settled = ADOPT_RULE.rule_id in settled_rules((trace,))
    assert not settled


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS)
def test_what_the_search_left_out_precedes_the_caveat_and_never_reaches_tier1(offset: int) -> None:
    pin = game_pin()
    plain = _card(_world())
    card = _card(
        _world(
            build=off_pin_build_inputs(pin, offset),
            trimmed=(PLATE_STEP,),
            unchecked=(GADGET_STEP, PLATE_STEP),
            unmatched_unlocks=3,
        )
    )
    assert card.tier1 == plain.tier1
    assert card.tier2 == (
        plain.tier2
        + "; the search dropped 1 recipe(s) to fit its cap"
        + "; 2 automated recipe(s) carry no asset path and were never planned"
        + f"; {WARN_BUILD_MISMATCH}: priced at the pinned build {pin},"
        + f" not the save build {pin + offset}"
    )
    assert f'Read plan.trimmed = ("{PLATE_STEP}") from' in card.tier3
    assert f'Read plan.unchecked = ("{GADGET_STEP}", "{PLATE_STEP}") from' in card.tier3
    assert "Read plan.unmatched_unlocks = 3 from" in card.tier3
    # A count alone in tier 2: the unmatched count is tier 3's, and no name is tier 2's.
    assert "unmatched" not in card.tier2
    assert GADGET_STEP not in card.tier2


def test_a_plan_stating_its_targets_out_of_order_is_named_sorted() -> None:
    """Pillar 1 sorts a solved plan's targets, so only a hand-built plan grades this sort."""
    plan = replace(
        _plan(), targets=MappingProxyType({ORE_ITEM: Fraction(5), GADGET_ITEM: Fraction(30)})
    )

    card = _card(_world(_ranked(plan=plan)))

    assert card.subject_key == "plan:Desc_SyntheticGadget_C+Desc_SyntheticOre_C"
    assert card.tier1 == (
        "Build the planned production chain for Desc_SyntheticGadget_C, Desc_SyntheticOre_C"
    )


def test_the_family_declares_the_build_inputs_ahead_of_its_own() -> None:
    assert RULES == (ADOPT_RULE, REDESIGN_RULE)
    assert ADOPT_RULE.inputs == (*BUILD_INPUTS, *PLAN_INPUTS)
    assert ADOPT_RULE.unlocks == ()
    # CS-1371: the marked route reads the build inputs first too, its own next, and of the
    # ranked path's only the two a route's derivation states. No plan input is its own.
    assert REDESIGN_RULE.inputs == (*BUILD_INPUTS, *REDESIGN_INPUTS, IN_STATUS, IN_UNCHECKED)
    assert REDESIGN_RULE.unlocks == ()
    assert REDESIGN_RULE.domain == ADOPT_RULE.domain
    assert sorted(set(REDESIGN_INPUTS) & set(PLAN_INPUTS)) == []


# --- end to end over a real ranking --------------------------------------------


def _solve(item: str, rate: Fraction, recipes: tuple[str, ...]) -> ProductionPlan:
    return solve_for_targets(
        solve_registry(),
        RatioRequest(
            targets=MappingProxyType({item: rate}),
            recipes=recipes,
            raw_items=(SOLVE_ORE_ITEM,),
            byproduct_policy=BYPRODUCT_BALANCED,
        ),
    )


def test_a_real_ranking_reaches_tier3_through_the_rule_and_never_tier1() -> None:
    """C5 ranked against C3 by raw input: the non-monotone badge the ladder exists for."""
    c3_loop = (GADGET_RECIPE, RECOVER_RECIPE, FLUID_RECIPE, PLATE_RECIPE)
    c3 = _solve(SOLVE_GADGET_ITEM, C3_GADGET_TARGET, c3_loop)
    c5 = _solve(SOLVE_TRINKET_ITEM, C5_TRINKET_TARGET, (STD_GADGET_RECIPE,))
    ranked = rank_plans(solve_registry(), (c5, c3), objective=weighted_objective(raw=Fraction(1)))
    second = ranked[1]
    assert second.plan is c5
    assert second.badge.strongest == RUNG_WITHIN_POWER

    trace = run_rule(ADOPT_RULE, _world(second, requires=(), unlocks=frozenset()))
    card = card_for(trace)
    assert card is not None
    carried = trace.steps[_badge_index(trace)].value
    assert carried is second.badge
    badge_line = f"Read plan.badge = {render_value(second.badge)} from"
    assert badge_line in card.tier3
    assert 'cleared=("within-buildings", "within-power")' in card.tier3
    headline = card.tier1.lower()
    leaked = [s.name for s in STRATEGY_LADDER if s.name in headline]
    assert leaked == []


def test_advise_with_the_family_named_yields_the_badged_card(tmp_path: Path) -> None:
    """The family also runs through ``advise(..., rules=...)``, and a firing settles nothing."""
    advice = advise(
        TOKEN,
        _world(),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=0,
        rules=RULES,
    )
    shown = advice.shown
    assert len(shown) == 1
    card = shown[0].card
    derivation = card.tier3
    assert derivation == expected_tier3(game_pin())
    settled = ADOPT_RULE.rule_id in settled_rules(advice.traces)
    assert not settled
