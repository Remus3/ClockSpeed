"""CS-1346: a rule that reads a plan, so a trace carries its strategy badge.

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
    IN_BADGE,
    IN_PLAN,
    IN_REQUIRES,
    PLAN_INPUTS,
    RULES,
    plan_inputs,
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
) -> WorldInputs:
    """A synthetic world offering the build inputs and one ranked plan."""
    offered = pinned_build_inputs(game_pin()) if build is None else build
    values = offered | plan_inputs(_ranked() if ranked is None else ranked, requires=requires)
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
            "  7. Read plan.production = ProductionPlan(steps=("
            'PlanStep(recipe_key="Recipe_SyntheticGadget_C", machines=3.00), '
            'PlanStep(recipe_key="Recipe_SyntheticPlate_C", machines=1.33 (exactly 4/3))), '
            'targets={"Desc_SyntheticGadget_C": 30.00}, '
            'raw_inputs={"Desc_SyntheticOre_C": 120.00}, byproducts={}, excluded=(), '
            'byproduct_policy="balanced") from solve.strategy.ranked_plan.plan',
            '  8. Read plan.badge = StrategyBadge(strongest="within-power", '
            'cleared=("within-buildings", "within-power"), checks=('
            'ThresholdCheck(strategy="within-raw", cleared=false, score=120.00, '
            'reference=60.00, bound=1.00, reason="over-bound"), '
            'ThresholdCheck(strategy="within-buildings", cleared=true, score=3.00, '
            'reference=6.00, bound=1.00, reason=""), '
            'ThresholdCheck(strategy="within-power", cleared=true, score=45.00, '
            'reference=145.33 (exactly 436/3), bound=1.00, reason=""))) '
            "from solve.strategy.ranked_plan.badge",
            "  9. Read plan.requires = "
            '("recipe:/Game/Synthetic/Recipe_SyntheticGadget.Recipe_SyntheticGadget_C") '
            "from caller.plan_unlock_keys",
            "  10. Computed plan machine equivalents = 4.33 (exactly 13/3)",
            "  11. Rule plan.adopt fired for plan:Desc_SyntheticGadget_C",
        ]
    )


# --- the acceptance ----------------------------------------------------------


def test_the_trace_carries_the_badge_read_by_a_rule_that_reads_a_plan() -> None:
    ranked = _ranked()
    trace = run_rule(ADOPT_RULE, _world(ranked))
    assert trace.recommendation is not None
    reads = [step for step in trace.steps if step.kind is StepKind.INPUT_READ]
    read_names = tuple(step.subject for step in reads)
    assert read_names == (*BUILD_INPUTS, IN_PLAN, IN_BADGE, IN_REQUIRES)
    plan_value = reads[len(BUILD_INPUTS)].value
    badge_value = reads[len(BUILD_INPUTS) + 1].value
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
    assert moved_lines[0].startswith("  8. Read plan.badge = StrategyBadge(")


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


def test_the_adapter_offers_the_ranked_plan_its_badge_and_the_callers_unlock_keys() -> None:
    ranked = _ranked()
    offered = plan_inputs(ranked, requires=(GADGET_UNLOCK,))
    assert tuple(offered) == PLAN_INPUTS
    assert offered[IN_PLAN].value is ranked.plan
    assert offered[IN_BADGE].value is ranked.badge
    assert offered[IN_REQUIRES].value == (GADGET_UNLOCK,)
    sources = tuple(offered[name].source for name in PLAN_INPUTS)
    assert sources == (
        "solve.strategy.ranked_plan.plan",
        "solve.strategy.ranked_plan.badge",
        "caller.plan_unlock_keys",
    )


def test_the_family_declares_the_build_inputs_ahead_of_its_own() -> None:
    assert RULES == (ADOPT_RULE,)
    assert ADOPT_RULE.inputs == (*BUILD_INPUTS, *PLAN_INPUTS)
    assert ADOPT_RULE.unlocks == ()


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
    """Unregistered, the family still runs through ``advise(..., rules=...)``."""
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
    assert settled
