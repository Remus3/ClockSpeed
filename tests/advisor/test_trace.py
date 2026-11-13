"""CS-500 slice S1: the rule trace engine.

Graded here, each against a control that shows the arm can see the defect:

- a rule reading an input it did not declare is REFUSED and the read is
  RECORDED in the trace (BOOTSTRAP.md section 5.4);
- a rule whose required unlock is unmet emits no recommendation and is never
  evaluated;
- over generated world states, no recommendation carries an unmet
  precondition - the property-test invariant of section 5.4;
- CS-1382: over generated unlock sets, the two plan rules as they ship, read by an oracle
  that imports no join, hold the same invariant, the arm that names a stage or a raw item with
  a machine held and the arm that names only what the world holds;
- a float input is refused (non-negotiable 6);
- a declared input the world does not carry is flagged and skipped, never
  raised (non-negotiable 7).
"""

from __future__ import annotations

import contextlib
import enum
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from fractions import Fraction
from types import MappingProxyType, SimpleNamespace
from typing import Final

import pytest

from clockspeed.advisor.plans import plan_offer, plan_parameters, plan_request_from
from clockspeed.advisor.rules.plan import RULES as PLAN_RULES
from clockspeed.advisor.trace import (
    InputRefusedError,
    InputValue,
    Recommendation,
    RuleContext,
    RuleSpec,
    StepKind,
    Trace,
    TraceStep,
    WorldInputs,
    run_rule,
    run_rules,
    unlock_keys,
)
from clockspeed.data.registry import Registry
from clockspeed.save.world import EMPTY_UNLOCK_STATE, UnlockState
from clockspeed.solve.optimize import MAX_EXHAUSTIVE_CANDIDATES
from clockspeed.solve.ratio import ExclusionNote, PlanStep, ProductionPlan
from clockspeed.solve.strategy import (
    NOT_CLEARED_OVER_BOUND,
    RUNG_WITHIN_BUILDINGS,
    RUNG_WITHIN_POWER,
    RUNG_WITHIN_RAW,
    StrategyBadge,
    ThresholdCheck,
)
from tests.advisor.build_fixtures import game_pin, pinned_build_inputs
from tests.advisor.worlds import (
    PLAN_WORLD_BUILD_PATHS,
    PLAN_WORLD_EXTRACTORS,
    PLAN_WORLD_RECIPES,
    SYNTHETIC_RULES,
    UNLOCK_UNIVERSE,
    PlanWorldCase,
    generate_plan_world_cases,
    generate_worlds,
    plan_world_registry,
)

_OVERCLOCK = "feature:synthetic-overclock"


def _world(unlocks: tuple[str, ...] = (), **values: object) -> WorldInputs:
    return WorldInputs(
        values={
            name.replace("_", "."): InputValue(value, "synthetic.fixture")
            for name, value in values.items()
        },
        unlocks=frozenset(unlocks),
    )


def _recommend(subject: str = "synthetic-subject") -> Recommendation:
    return Recommendation(subject_key=subject, action="Do the synthetic thing", reason="because")


def _kinds(trace: Trace) -> tuple[StepKind, ...]:
    return tuple(step.kind for step in trace.steps)


def _subjects_of(trace: Trace, kind: StepKind) -> tuple[str, ...]:
    return tuple(step.subject for step in trace.steps if step.kind is kind)


def _reads(*names: str) -> RuleSpec:
    """A rule declaring only ``a.declared`` that reads every name in ``names``."""

    def evaluate(ctx: RuleContext) -> Recommendation | None:
        for name in names:
            ctx.read(name)
        return _recommend()

    return RuleSpec(
        rule_id="synthetic.reader",
        domain="power",
        inputs=("a.declared",),
        unlocks=(),
        evaluate=evaluate,
    )


# --- undeclared reads -----------------------------------------------------


def test_an_undeclared_input_read_is_refused_and_recorded() -> None:
    world = _world(a_declared=Fraction(1), b_undeclared=Fraction(2))

    control = run_rule(_reads("a.declared"), world)
    assert control.recommendation is not None
    assert _subjects_of(control, StepKind.INPUT_READ) == ("a.declared",)

    trace = run_rule(_reads("a.declared", "b.undeclared"), world)
    assert trace.recommendation is None
    assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("b.undeclared",)
    assert StepKind.RULE_ERROR not in _kinds(trace)
    assert _subjects_of(trace, StepKind.INPUT_READ) == ("a.declared",)
    assert StepKind.RULE_FIRED not in _kinds(trace)


def test_an_undeclared_read_the_rule_swallows_still_suppresses_the_recommendation() -> None:
    def evaluate(ctx: RuleContext) -> Recommendation | None:
        with contextlib.suppress(InputRefusedError):
            ctx.read("b.undeclared")
        return _recommend()

    spec = RuleSpec(
        rule_id="synthetic.swallower",
        domain="power",
        inputs=("a.declared",),
        unlocks=(),
        evaluate=evaluate,
    )
    trace = run_rule(spec, _world(b_undeclared=Fraction(2)))
    assert trace.recommendation is None
    assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("b.undeclared",)


# --- unmet unlocks --------------------------------------------------------


def test_a_rule_with_an_unmet_unlock_emits_no_recommendation() -> None:
    calls: list[str] = []

    def evaluate(ctx: RuleContext) -> Recommendation | None:
        calls.append(ctx.rule_id)
        return _recommend()

    spec = RuleSpec(
        rule_id="synthetic.gated",
        domain="power",
        inputs=(),
        unlocks=(_OVERCLOCK,),
        evaluate=evaluate,
    )

    control = run_rule(spec, _world(unlocks=(_OVERCLOCK,)))
    assert control.recommendation is not None
    assert StepKind.RULE_FIRED in _kinds(control)
    assert calls == ["synthetic.gated"]

    trace = run_rule(spec, _world())
    assert trace.recommendation is None
    assert _subjects_of(trace, StepKind.PRECONDITION_UNMET) == (_OVERCLOCK,)
    assert StepKind.RULE_FIRED not in _kinds(trace)
    assert calls == ["synthetic.gated"], "a gated rule must not be evaluated"


def test_a_recommendation_requiring_an_unmet_unlock_is_dropped() -> None:
    needed = "recipe:/Synthetic/Recipe_AltPlate"

    def evaluate(_ctx: RuleContext) -> Recommendation | None:
        return Recommendation(
            subject_key="synthetic-recipe",
            action="Switch recipe",
            reason="synthetic",
            requires=(needed,),
        )

    spec = RuleSpec(
        rule_id="synthetic.data-gated",
        domain="transport",
        inputs=(),
        unlocks=(),
        evaluate=evaluate,
    )
    assert run_rule(spec, _world(unlocks=(needed,))).recommendation is not None
    trace = run_rule(spec, _world())
    assert trace.recommendation is None
    assert _subjects_of(trace, StepKind.PRECONDITION_UNMET) == (needed,)


def test_no_recommendation_has_an_unmet_precondition_over_generated_worlds() -> None:
    worlds = generate_worlds(seed=500, count=400)
    assert worlds == generate_worlds(seed=500, count=400), "the generator must be reproducible"

    by_id = {spec.rule_id: spec for spec in SYNTHETIC_RULES}
    recommended = 0
    gated = 0
    for world in worlds:
        for trace in run_rules(SYNTHETIC_RULES, world):
            spec = by_id[trace.rule_id]
            if trace.recommendation is None:
                if StepKind.PRECONDITION_UNMET in _kinds(trace):
                    gated += 1
                continue
            recommended += 1
            needed = (*spec.unlocks, *trace.recommendation.requires)
            unmet_count = sum(1 for key in needed if key not in world.unlocks)
            assert unmet_count == 0, trace.rule_id
            assert StepKind.PRECONDITION_UNMET not in _kinds(trace), trace.rule_id

    # Anti-vacuity: the population must exercise both sides of the gate.
    assert recommended > 0
    assert gated > 0


def test_the_generated_rules_would_recommend_without_the_gate() -> None:
    """Control for the property test: the naive rules DO try to recommend when locked."""
    values = {
        "synthetic.headroom": InputValue(Fraction(10), "synthetic.power"),
        "synthetic.draw": InputValue(Fraction(3), "synthetic.power"),
        "synthetic.purity": InputValue(Fraction(9), "synthetic.nodes"),
        "synthetic.distance": InputValue(Fraction(2), "synthetic.nodes"),
    }
    unlocked = WorldInputs(values=values, unlocks=frozenset(UNLOCK_UNIVERSE))
    locked = WorldInputs(values=values, unlocks=frozenset())
    full = [t.rule_id for t in run_rules(SYNTHETIC_RULES, unlocked) if t.recommendation]
    none = [t.rule_id for t in run_rules(SYNTHETIC_RULES, locked) if t.recommendation]
    assert full == sorted(spec.rule_id for spec in SYNTHETIC_RULES)
    assert none == ["synthetic.rebalance"]


# --- the plan rules, over generated unlock sets (CS-1382) --------------------

#: How many unlock sets the property test draws, and from what. Past the 400 the ruling asks
#: for, because a route with nothing locked is the rarest thing it counts.
PLAN_WORLD_SEED: Final = 1382
PLAN_WORLD_COUNT: Final = 1000

#: The input each rule reads its plan from, by rule.
_PLAN_INPUT: Final = {"plan.adopt": "plan.production", "plan.redesign": "plan.redesign.plan"}

#: The sentence the ruling lets read only with both of a route's lists empty.
_NO_UNLOCK: Final = "this route needs no unlock"

#: That clause whole, as a search the cap cut nothing from reads it, which in a world with no
#: more recipes than the cap is every search. Read whole, never by its prefix alone, so a
#: clause that blamed a cap nothing cut reddens (CS-1382 F1).
_UNCAPPED_NO_UNLOCK: Final = (
    "; this route needs no unlock and the search, which dropped no recipe on this route to fit"
    " its cap, did not find it from the raw items a held extractor supplies"
)

#: Each recipe by name, read off the fixture's own table.
_PLAN_WORLD_BY_NAME: Final = {recipe.name: recipe for recipe in PLAN_WORLD_RECIPES}


def _read_value(trace: Trace, name: str) -> object:
    """What a trace read for one input, which it must have read exactly once."""
    (value,) = (
        step.value
        for step in trace.steps
        if step.kind is StepKind.INPUT_READ and step.subject == name
    )
    return value


def _names_read(trace: Trace, name: str) -> tuple[str, ...]:
    """A tuple of names a trace read, typed so the oracle can compare it."""
    value = _read_value(trace, name)
    if type(value) is not tuple:
        raise TypeError(name)
    return value


def _plan_read(trace: Trace) -> ProductionPlan:
    """The plan a rule's trace read, whichever rule it was."""
    value = _read_value(trace, _PLAN_INPUT[trace.rule_id])
    if type(value) is not ProductionPlan:
        raise TypeError(trace.rule_id)
    return value


def _held_keys(machines: tuple[str, ...], unlocked: tuple[str, ...]) -> frozenset[str]:
    """The unlock keys of those of these machines the world holds, from the fixture's table."""
    return frozenset(
        f"recipe:{PLAN_WORLD_BUILD_PATHS[name]}"
        for name in machines
        if PLAN_WORLD_BUILD_PATHS[name] in unlocked
    )


def _is_held(recipe_name: str, unlocked: tuple[str, ...]) -> bool:
    """Whether the world holds a recipe's path and one of its machines, off the fixture's tables."""
    recipe = _PLAN_WORLD_BY_NAME[recipe_name]
    return recipe.path in unlocked and bool(_held_keys(recipe.machines, unlocked))


def _stage_faults(
    plan: ProductionPlan, requires: tuple[str, ...], unlocked: tuple[str, ...]
) -> list[str]:
    """Grade every stage with a machine against what a route or a plan requires.

    A plan's every such stage must be held, because the search takes no other. A route's may be
    locked, which its rule then answers for by naming no key of it.

    Args:
        plan: The plan the rule read.
        requires: The keys its recommendation requires.
        unlocked: The world's paths.

    Returns:
        What is wrong, by name, in plan order.
    """
    faults: list[str] = []
    for step in plan.steps:
        if step.machines == 0:
            continue
        recipe = _PLAN_WORLD_BY_NAME[step.recipe_key]
        machines = _held_keys(recipe.machines, unlocked)
        key = f"recipe:{recipe.path}"
        if _is_held(recipe.name, unlocked):
            if key not in requires:
                faults.append(f"a held stage's key is not required: {recipe.name}")
            if not machines & set(requires):
                faults.append(f"a held stage's machine is not required: {recipe.name}")
        elif key in requires:
            faults.append(f"a locked stage's key is required: {recipe.name}")
    return faults


def _adopt_faults(trace: Trace, unlocked: tuple[str, ...]) -> list[str]:
    """Grade one fired plan.adopt against the fixture's own tables.

    Args:
        trace: The trace, which fired.
        unlocked: The world's paths.

    Returns:
        What is wrong, by name.
    """
    assert trace.recommendation is not None
    requires = trace.recommendation.requires
    plan = _plan_read(trace)
    faults = _stage_faults(plan, requires, unlocked)
    for step in plan.steps:
        recipe = _PLAN_WORLD_BY_NAME[step.recipe_key]
        if step.machines != 0 and f"recipe:{recipe.path}" not in requires:
            faults.append(f"a plan's stage is not required: {recipe.name}")
    for item, rate in plan.raw_inputs.items():
        if rate > 0 and not _held_keys(PLAN_WORLD_EXTRACTORS[item], unlocked) & set(requires):
            faults.append(f"a consumed raw item has no held extractor required: {item}")
    return faults


def _route_faults(trace: Trace, unlocked: tuple[str, ...]) -> list[str]:
    """Grade one fired plan.redesign against the fixture's own tables.

    Args:
        trace: The trace, which fired.
        unlocked: The world's paths.

    Returns:
        What is wrong, by name.
    """
    assert trace.recommendation is not None
    requires = trace.recommendation.requires
    plan = _plan_read(trace)
    locked = _names_read(trace, "plan.redesign.locked")
    extractors = _names_read(trace, "plan.redesign.locked_extractors")
    faults = _stage_faults(plan, requires, unlocked)
    for item, rate in plan.raw_inputs.items():
        if rate <= 0:
            continue
        known = PLAN_WORLD_EXTRACTORS[item]
        held = _held_keys(known, unlocked)
        if held and not held & set(requires):
            faults.append(f"a held extractor is not required: {item}")
        if not held and not set(known) & set(extractors):
            faults.append(f"a consumed raw item names no machine: {item}")
    for name in extractors:
        if f"recipe:{PLAN_WORLD_BUILD_PATHS[name]}" in requires:
            faults.append(f"a locked machine is required: {name}")
    # Read off the tables too, and not off the rule's own lists, or a rule that forgot a machine
    # would agree with itself.
    needs_a_stage = any(
        step.machines != 0 and not _is_held(step.recipe_key, unlocked) for step in plan.steps
    )
    needs_a_machine = any(
        rate > 0 and not _held_keys(PLAN_WORLD_EXTRACTORS[item], unlocked)
        for item, rate in plan.raw_inputs.items()
    )
    says_none = _NO_UNLOCK in trace.recommendation.reason
    if says_none and (needs_a_stage or needs_a_machine or locked or extractors):
        faults.append("the no-unlock sentence reads beside something locked")
    if not says_none and not (needs_a_stage or needs_a_machine):
        faults.append("the no-unlock sentence is missing with nothing locked")
    if says_none and _UNCAPPED_NO_UNLOCK not in trace.recommendation.reason:
        faults.append("the no-unlock sentence blames a cap that cut nothing")
    return faults


def _plan_world_faults(trace: Trace, world: WorldInputs, unlocked: tuple[str, ...]) -> list[str]:
    """Grade one plan rule's trace, which reads nothing but the fixture's tables and the trace.

    THE ORACLE IMPORTS NO JOIN. No helper of ``clockspeed/advisor/plans.py``, no
    ``build_cost`` and no ``extractors_of``: the tables say what a machine's unlock is and which
    machine digs what, so a join that got either wrong cannot grade itself.

    Args:
        trace: The trace of one rule.
        world: The world it ran over, whose unlocks the engine's own gate read.
        unlocked: The world's paths.

    Returns:
        What is wrong, by name. Empty for a rule that fired nothing.
    """
    if trace.recommendation is None:
        return []
    faults = (
        _adopt_faults(trace, unlocked)
        if trace.rule_id == "plan.adopt"
        else _route_faults(trace, unlocked)
    )
    faults.extend(
        f"a required key is not held: {key}"
        for key in trace.recommendation.requires
        if key not in world.unlocks
    )
    return faults


def _plan_world_offer(
    registry: Registry, case: PlanWorldCase, *, extra: tuple[str, ...] = ()
) -> Mapping[str, InputValue]:
    """The offer one case reads, through the published doors, on these paths and any extra."""
    parameters = plan_parameters(rate="10", direction=case.direction, byproduct_policy=case.policy)
    assert parameters is not None
    request = plan_request_from(registry, case.target, parameters)
    assert request is not None
    state = replace(EMPTY_UNLOCK_STATE, recipes=frozenset((*case.unlocked, *extra)))
    return plan_offer(state, registry, request)


def _plan_world_world(case: PlanWorldCase, offered: Mapping[str, InputValue]) -> WorldInputs:
    """The world a rule reads for one case: that offer, on the pin, over the case's own paths."""
    state = replace(EMPTY_UNLOCK_STATE, recipes=frozenset(case.unlocked))
    return WorldInputs(
        values={**pinned_build_inputs(game_pin()), **offered}, unlocks=unlock_keys(state)
    )


def _holds_a_stage_and_no_extractor(case: PlanWorldCase) -> bool:
    """The clause's constructed set: a recipe making the target held with its machine, nothing dug.

    Args:
        case: The case.

    Returns:
        True when some recipe making the target is held with a machine and holds no extractor
        of anything it eats, and the world holds no extractor of any raw item at all.
    """
    if any(
        PLAN_WORLD_BUILD_PATHS[name] in case.unlocked
        for machines in PLAN_WORLD_EXTRACTORS.values()
        for name in machines
    ):
        return False
    return any(
        case.target in recipe.makes
        and recipe.path in case.unlocked
        and _held_keys(recipe.machines, case.unlocked)
        and set(recipe.eats) <= set(PLAN_WORLD_EXTRACTORS)
        for recipe in PLAN_WORLD_RECIPES
    )


def test_the_plan_rules_hold_the_precondition_over_generated_unlock_sets() -> None:
    """CS-1382 reading, not amendment: literal is self-contradictory for plan.redesign.

    Over generated unlock sets, the oracle importing no join: plan.adopt, every stage with a
    machine and one held machine for it in requires; plan.redesign, the same for held stages, no
    locked stage's recipe key in requires, each consumed raw a held extractor key in requires or
    its machine on plan.redesign.locked_extractors; a locked route fires. Plus: plan.adopt, a held
    extractor's key in requires per raw with rate above zero; and no-unlock reads only with both
    lists empty, and whole, naming no cap in a world no cap can cut (CS-1382 F1). The rules run as
    they ship, on the offer :func:`plan_offer` makes.
    """
    cases = generate_plan_world_cases(seed=PLAN_WORLD_SEED, count=PLAN_WORLD_COUNT)
    assert cases == generate_plan_world_cases(seed=PLAN_WORLD_SEED, count=PLAN_WORLD_COUNT)
    registry = plan_world_registry()
    # What lets the oracle read the uncapped clause whole: no search here can drop a recipe.
    assert len(PLAN_WORLD_RECIPES) <= MAX_EXHAUSTIVE_CANDIDATES

    seen: Counter[str] = Counter()
    for case in cases:
        world = _plan_world_world(case, _plan_world_offer(registry, case))
        traces = run_rules(PLAN_RULES, world)
        for trace in traces:
            errors = [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]
            assert errors == [], case.target
            faults = _plan_world_faults(trace, world, case.unlocked)
            assert faults == [], case.target
            assert StepKind.PRECONDITION_UNMET not in _kinds(trace), case.target
        adopt, route = traces
        if adopt.recommendation is not None:
            seen["adopt fired"] += 1
        elif _holds_a_stage_and_no_extractor(case):
            seen["no adopt card with a stage held and no extractor held"] += 1
        if route.recommendation is not None:
            if _names_read(route, "plan.redesign.locked"):
                seen["route fired with a locked stage"] += 1
            if _names_read(route, "plan.redesign.locked_extractors"):
                seen["route fired with a locked extractor"] += 1
            if _NO_UNLOCK in route.recommendation.reason:
                seen["the no-unlock sentence read"] += 1

    # Anti-vacuity, by name: the population must reach each side the clause speaks of.
    for reached in (
        "adopt fired",
        "no adopt card with a stage held and no extractor held",
        "route fired with a locked stage",
        "route fired with a locked extractor",
        "the no-unlock sentence read",
    ):
        assert seen[reached] > 0, reached


def _fired_faults(
    cases: tuple[PlanWorldCase, ...],
    offer: Callable[[PlanWorldCase], Mapping[str, InputValue]],
) -> list[str]:
    """Every fault the oracle reads over these cases, with each case's offer as given."""
    faults: list[str] = []
    for case in cases:
        world = _plan_world_world(case, offer(case))
        for trace in run_rules(PLAN_RULES, world):
            faults.extend(_plan_world_faults(trace, world, case.unlocked))
    return faults


def _with_requires_filtered(
    offered: Mapping[str, InputValue], keep: Callable[[str], bool]
) -> dict[str, InputValue]:
    """The same offer with each rule's requires holding only the keys kept."""
    changed = dict(offered)
    for name in ("plan.requires", "plan.redesign.requires"):
        if name in changed and changed[name].value is not None:
            value = changed[name].value
            assert type(value) is tuple
            changed[name] = InputValue(
                tuple(key for key in value if keep(key)), changed[name].source
            )
    return changed


def test_the_plan_oracle_sees_a_bypassed_extractor_join() -> None:
    """The control: every extractor read held, and nothing required of them, is the defect.

    This is what the search did before CS-1382: it drew from every raw item, and no key said so.
    The engine has nothing to refuse, so the card fires, and only the oracle can object.
    """
    registry = plan_world_registry()
    extractors = tuple(
        PLAN_WORLD_BUILD_PATHS[name] for names in PLAN_WORLD_EXTRACTORS.values() for name in names
    )
    keys = frozenset(f"recipe:{path}" for path in extractors)

    def bypassed(case: PlanWorldCase) -> dict[str, InputValue]:
        offered = _plan_world_offer(registry, case, extra=extractors)
        return _with_requires_filtered(offered, lambda key: key not in keys)

    faults = _fired_faults(
        generate_plan_world_cases(seed=PLAN_WORLD_SEED, count=PLAN_WORLD_COUNT), bypassed
    )

    wrong = sorted({fault.partition(":")[0] for fault in faults})
    assert "a consumed raw item has no held extractor required" in wrong


def test_the_plan_oracle_sees_a_requires_that_lost_a_machine() -> None:
    """The control: the join's own offer, with every machine's key taken off what it requires."""
    registry = plan_world_registry()
    machines = frozenset(f"recipe:{path}" for path in PLAN_WORLD_BUILD_PATHS.values())

    faults = _fired_faults(
        generate_plan_world_cases(seed=PLAN_WORLD_SEED, count=PLAN_WORLD_COUNT),
        lambda case: _with_requires_filtered(
            _plan_world_offer(registry, case), lambda key: key not in machines
        ),
    )

    machine_faults = sum(1 for fault in faults if "machine is not required" in fault)
    assert machine_faults > 0


def test_the_plan_oracle_sees_a_no_unlock_sentence_beside_a_locked_extractor() -> None:
    """The control: a route whose locked extractors are planted empty reads the sentence."""
    registry = plan_world_registry()

    def forgotten(case: PlanWorldCase) -> dict[str, InputValue]:
        offered = dict(_plan_world_offer(registry, case))
        name = "plan.redesign.locked_extractors"
        if offered[name].value is not None:
            offered[name] = InputValue((), offered[name].source)
        return offered

    faults = _fired_faults(
        generate_plan_world_cases(seed=PLAN_WORLD_SEED, count=PLAN_WORLD_COUNT), forgotten
    )

    wrong = sorted({fault.partition(":")[0] for fault in faults})
    assert wrong == [
        "a consumed raw item names no machine",
        "the no-unlock sentence reads beside something locked",
    ]


# --- exactness ------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Holder:
    rate: object


def test_a_float_input_is_refused() -> None:
    control = run_rule(_reads("a.declared"), _world(a_declared=Fraction(3, 2)))
    assert control.recommendation is not None

    for bad in (1.5, (Fraction(1), 2.5), _Holder(rate=0.25), {"k": 0.5}):
        trace = run_rule(_reads("a.declared"), _world(a_declared=bad))
        assert trace.recommendation is None, type(bad).__name__
        assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("a.declared",)
        assert _subjects_of(trace, StepKind.INPUT_READ) == ()


def test_a_float_computation_is_refused() -> None:
    def evaluate(ctx: RuleContext) -> Recommendation | None:
        ctx.compute("half", 0.5)  # type: ignore[arg-type]
        return _recommend()

    spec = RuleSpec(
        rule_id="synthetic.float-compute",
        domain="power",
        inputs=(),
        unlocks=(),
        evaluate=evaluate,
    )
    trace = run_rule(spec, _world())
    assert trace.recommendation is None
    assert StepKind.COMPUTED not in _kinds(trace)


def test_read_exact_refuses_a_non_fraction() -> None:
    def evaluate(ctx: RuleContext) -> Recommendation | None:
        ctx.read_exact("a.declared")
        return _recommend()

    spec = RuleSpec(
        rule_id="synthetic.exact",
        domain="power",
        inputs=("a.declared",),
        unlocks=(),
        evaluate=evaluate,
    )
    assert run_rule(spec, _world(a_declared=Fraction(7, 3))).recommendation is not None
    for bad in ("synthetic-text", 3, True):
        trace = run_rule(spec, _world(a_declared=bad))
        assert trace.recommendation is None, type(bad).__name__
        assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("a.declared",)
        # The provisional read step is withdrawn, never left beside the refusal.
        assert _subjects_of(trace, StepKind.INPUT_READ) == (), type(bad).__name__


def test_the_inexact_reason_is_deterministic_across_several_bad_parts() -> None:
    """The smallest reason wins, never the first one iteration happens to reach."""
    for bad in ((0.5, 1j), (1j, 0.5), (Fraction(1), (0.5,), 1j)):
        trace = run_rule(_reads("a.declared"), _world(a_declared=bad))
        reasons = [s.reason for s in trace.steps if s.kind is StepKind.INPUT_REFUSED]
        assert reasons == ["a complex is not an exact type"], type(bad).__name__


class _Colour(enum.Enum):
    RED = "red"


@dataclass(frozen=True, slots=True)
class _Nested:
    inner: _Holder
    flags: tuple[str, ...]


@dataclass(frozen=True)
class _Unslotted:
    rate: Fraction


@dataclass(slots=True)
class _SlottedMutable:
    rate: Fraction


@dataclass
class _Mutable:
    rate: Fraction


def test_an_immutable_exact_value_is_accepted() -> None:
    goods = (
        True,
        None,
        MappingProxyType({"k": Fraction(1, 3), "flag": False}),
        _Nested(inner=_Holder(rate=Fraction(2)), flags=("a",)),
        (Fraction(1), "x", 4),
    )
    for good in goods:
        trace = run_rule(_reads("a.declared"), _world(a_declared=good))
        assert trace.recommendation is not None, type(good).__name__
        assert _subjects_of(trace, StepKind.INPUT_READ) == ("a.declared",)


def test_a_mutable_value_is_refused_even_when_every_part_is_exact() -> None:
    bads = (
        {"k": Fraction(1)},
        [Fraction(1)],
        {Fraction(1)},
        _Mutable(rate=Fraction(1)),
        (Fraction(1), [Fraction(2)]),
        _Holder(rate={"k": Fraction(1)}),
        _Colour.RED,
        _Unslotted(rate=Fraction(1)),
        _SlottedMutable(rate=Fraction(1)),
    )
    for bad in bads:
        trace = run_rule(_reads("a.declared"), _world(a_declared=bad))
        assert trace.recommendation is None, type(bad).__name__
        assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("a.declared",)


def test_a_rule_mutating_what_it_read_alters_neither_the_trace_nor_the_next_rule() -> None:
    def vandal(ctx: RuleContext) -> Recommendation | None:
        value = ctx.read("a.declared")
        value["k"] = 0.5  # type: ignore[index]
        return _recommend()

    vandal_spec = RuleSpec(
        rule_id="synthetic.a-vandal",
        domain="power",
        inputs=("a.declared",),
        unlocks=(),
        evaluate=vandal,
    )
    world = _world(a_declared=MappingProxyType({"k": Fraction(1)}))
    first, second = run_rules((vandal_spec, _reads("a.declared")), world)
    assert first.recommendation is None
    read_values = [s.value for s in first.steps if s.kind is StepKind.INPUT_READ]
    assert read_values == [MappingProxyType({"k": Fraction(1)})]
    assert second.recommendation is not None
    assert _subjects_of(second, StepKind.INPUT_REFUSED) == ()
    assert world.values["a.declared"].value == MappingProxyType({"k": Fraction(1)})


# --- CS-1346: the solve-layer plan and badge types ---------------------------


def _check(name: str, *, cleared: bool, score: object, reference: object) -> ThresholdCheck:
    """One invented rung verdict at the identity bound."""
    return ThresholdCheck(
        strategy=name,
        cleared=cleared,
        score=score,  # type: ignore[arg-type]
        reference=reference,  # type: ignore[arg-type]
        bound=Fraction(1),
        reason="" if cleared else NOT_CLEARED_OVER_BOUND,
    )


def _badge(power_score: object = Fraction(45)) -> StrategyBadge:
    """An invented badge: raw over its bound, buildings and power cleared."""
    return StrategyBadge(
        strongest=RUNG_WITHIN_POWER,
        cleared=(RUNG_WITHIN_BUILDINGS, RUNG_WITHIN_POWER),
        checks=(
            _check(RUNG_WITHIN_RAW, cleared=False, score=Fraction(120), reference=Fraction(60)),
            _check(RUNG_WITHIN_BUILDINGS, cleared=True, score=Fraction(3), reference=Fraction(6)),
            _check(RUNG_WITHIN_POWER, cleared=True, score=power_score, reference=Fraction(436, 3)),
        ),
    )


def _plan() -> ProductionPlan:
    """An invented plan: one fractional step, one exclusion, exact rates."""
    return ProductionPlan(
        steps=(PlanStep(recipe_key="Recipe_Synthetic_C", machines=Fraction(10, 3)),),
        targets=MappingProxyType({"Desc_Synthetic_C": Fraction(50)}),
        raw_inputs=MappingProxyType({"Desc_SyntheticOre_C": Fraction(50)}),
        byproducts=MappingProxyType({}),
        excluded=(ExclusionNote(recipe_key="Recipe_SyntheticExcluded_C", reason="synthetic"),),
        byproduct_policy="synthetic-policy",
    )


def _read_values(trace: Trace) -> list[object]:
    return [step.value for step in trace.steps if step.kind is StepKind.INPUT_READ]


def test_a_solve_plan_and_its_badge_are_read_as_exact_values() -> None:
    """CS-1346: the five solve types cross though none is declared with slots."""
    plan = _plan()
    badge = _badge()
    goods = (plan, badge, plan.steps[0], plan.excluded[0], badge.checks[0], (plan, badge))
    for good in goods:
        trace = run_rule(_reads("a.declared"), _world(a_declared=good))
        name = type(good).__name__
        refused = _subjects_of(trace, StepKind.INPUT_REFUSED)
        assert refused == (), name
        assert trace.recommendation is not None, name
        read = _read_values(trace)
        assert read == [good], name


def test_a_plan_type_carrying_an_undeclared_attribute_is_refused() -> None:
    """An instance attribute outside the declared fields is state the walk never sees."""
    control = run_rule(_reads("a.declared"), _world(a_declared=_badge()))
    assert control.recommendation is not None

    for planted in (0.5, Fraction(1)):
        for good in (_badge(), _plan(), _plan().steps[0]):
            object.__setattr__(good, "planted", planted)
            trace = run_rule(_reads("a.declared"), _world(a_declared=good))
            name = type(good).__name__
            assert trace.recommendation is None, name
            assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("a.declared",), name
            assert _read_values(trace) == [], name


def test_a_plan_type_holding_an_inexact_value_is_refused() -> None:
    """The walk descends into an admitted type's fields; a float anywhere refuses it."""
    control = run_rule(_reads("a.declared"), _world(a_declared=_badge(Fraction(45))))
    assert control.recommendation is not None

    trace = run_rule(_reads("a.declared"), _world(a_declared=_badge(45.0)))
    assert trace.recommendation is None
    reasons = [s.reason for s in trace.steps if s.kind is StepKind.INPUT_REFUSED]
    assert reasons == ["a float is not an exact type"]


def test_a_plan_type_is_admitted_only_while_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    """The class-level frozen flag is read on every walk; an unfrozen one refuses."""
    control = run_rule(_reads("a.declared"), _world(a_declared=_badge()))
    assert control.recommendation is not None

    monkeypatch.setattr(StrategyBadge, "__dataclass_params__", SimpleNamespace(frozen=False))
    trace = run_rule(_reads("a.declared"), _world(a_declared=_badge()))
    assert trace.recommendation is None
    assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("a.declared",)


class _BadgeSubclass(StrategyBadge):
    """A subclass of an admitted type: matched by exact type, so refused."""


def test_a_subclass_of_a_plan_type_is_refused() -> None:
    base = _badge()
    control = run_rule(_reads("a.declared"), _world(a_declared=base))
    assert control.recommendation is not None

    sub = _BadgeSubclass(strongest=base.strongest, cleared=base.cleared, checks=base.checks)
    trace = run_rule(_reads("a.declared"), _world(a_declared=sub))
    assert trace.recommendation is None
    assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("a.declared",)


def test_a_rule_assigning_into_a_read_badge_alters_neither_the_trace_nor_the_next_rule() -> None:
    def vandal(ctx: RuleContext) -> Recommendation | None:
        value = ctx.read("a.declared")
        value.strongest = None  # type: ignore[attr-defined]
        return _recommend()

    vandal_spec = RuleSpec(
        rule_id="synthetic.a-vandal",
        domain="power",
        inputs=("a.declared",),
        unlocks=(),
        evaluate=vandal,
    )
    world = _world(a_declared=_badge())
    first, second = run_rules((vandal_spec, _reads("a.declared")), world)
    assert first.recommendation is None
    assert _subjects_of(first, StepKind.RULE_ERROR) == ("FrozenInstanceError",)
    assert _read_values(first) == [_badge()]
    assert second.recommendation is not None
    assert _read_values(second) == [_badge()]


# --- the context is the only door, as far as Python lets it be --------------


def test_tampering_with_the_context_does_not_unrefuse() -> None:
    seen: list[object] = []

    def tamper(ctx: RuleContext) -> Recommendation | None:
        with contextlib.suppress(InputRefusedError):
            ctx.read("b.undeclared")
        seen.append(getattr(ctx, "_world", None))
        with contextlib.suppress(AttributeError):
            ctx._refusals = 0  # type: ignore[attr-defined]  # noqa: SLF001 - the tamper under test
        with contextlib.suppress(AttributeError):
            ctx._steps.clear()  # type: ignore[attr-defined]  # noqa: SLF001 - the tamper under test
        return _recommend()

    spec = RuleSpec(
        rule_id="synthetic.tamper",
        domain="power",
        inputs=("a.declared",),
        unlocks=(),
        evaluate=tamper,
    )
    trace = run_rule(spec, _world(b_undeclared=Fraction(2)))
    assert trace.recommendation is None
    assert trace.refused == ("b.undeclared",)
    assert seen == [None], "the context must not hand the rule the world"


# --- rule bugs are recorded, never raised -----------------------------------


def _returning(rec: object) -> RuleSpec:
    def evaluate(_ctx: RuleContext) -> Recommendation | None:
        return rec  # type: ignore[return-value]

    return RuleSpec(
        rule_id="synthetic.returner",
        domain="power",
        inputs=(),
        unlocks=(),
        evaluate=evaluate,
    )


def test_recommendation_text_must_be_ascii_strings() -> None:
    assert run_rule(_returning(_recommend()), _world()).recommendation is not None
    bads = (
        Recommendation(subject_key=1.5, action="Do", reason="r"),  # type: ignore[arg-type]
        Recommendation(subject_key="s", action="Do", reason=0.25),  # type: ignore[arg-type]
        Recommendation(subject_key="s", action="Do \u2014 now", reason="r"),
        Recommendation(subject_key="s", action="Do", reason="at 0.5/min", target_milestone=0.5),  # type: ignore[arg-type]
        Recommendation(subject_key="s", action="Do", reason="r", requires=("x", 1.5)),  # type: ignore[arg-type]
        Recommendation(subject_key="s", action="Do", reason="r", requires=["x"]),  # type: ignore[arg-type]
        Recommendation(subject_key="", action="Do", reason="r"),
        "not a recommendation",
    )
    for bad in bads:
        trace = run_rule(_returning(bad), _world())
        assert trace.recommendation is None, type(bad).__name__
        assert StepKind.RULE_ERROR in _kinds(trace), type(bad).__name__
        assert StepKind.RULE_FIRED not in _kinds(trace)


def test_rejected_alternative_text_must_be_ascii_strings() -> None:
    for alternative, reason in ((0.25, "r"), ("alt", "costs \u2013 more"), ("alt", 1.5)):

        def evaluate(
            ctx: RuleContext, a: object = alternative, r: object = reason
        ) -> Recommendation | None:
            ctx.reject(a, r)  # type: ignore[arg-type]
            return _recommend()

        spec = RuleSpec(
            rule_id="synthetic.rejecter",
            domain="power",
            inputs=(),
            unlocks=(),
            evaluate=evaluate,
        )
        trace = run_rule(spec, _world())
        assert trace.recommendation is None, repr(reason)
        assert StepKind.ALTERNATIVE_REJECTED not in _kinds(trace)
        assert StepKind.RULE_ERROR in _kinds(trace)


def test_a_rule_exception_is_recorded_by_type_and_never_raised() -> None:
    def divide(ctx: RuleContext) -> Recommendation | None:
        ctx.compute("ratio", Fraction(1) / ctx.read_exact("a.declared"))
        return _recommend()

    spec = RuleSpec(
        rule_id="synthetic.divider",
        domain="power",
        inputs=("a.declared",),
        unlocks=(),
        evaluate=divide,
    )
    assert run_rule(spec, _world(a_declared=Fraction(2))).recommendation is not None
    trace = run_rule(spec, _world(a_declared=Fraction(0)))
    assert trace.recommendation is None
    errors = [s for s in trace.steps if s.kind is StepKind.RULE_ERROR]
    assert [s.subject for s in errors] == ["ZeroDivisionError"]
    assert errors[0].value is None


def test_duplicate_rule_ids_are_refused_identically_in_either_order() -> None:
    first = RuleSpec(
        rule_id="synthetic.twin",
        domain="power",
        inputs=(),
        unlocks=(),
        evaluate=lambda _ctx: _recommend("one"),
    )
    second = RuleSpec(
        rule_id="synthetic.twin",
        domain="nodes",
        inputs=(),
        unlocks=(),
        evaluate=lambda _ctx: _recommend("two"),
    )
    other = _returning(_recommend())
    forward = run_rules((first, second, other), _world())
    backward = run_rules((other, second, first), _world())
    assert forward == backward
    by_id = {t.rule_id: t for t in forward}
    assert [t.rule_id for t in forward] == ["synthetic.returner", "synthetic.twin"]
    assert by_id["synthetic.twin"].recommendation is None
    assert _subjects_of(by_id["synthetic.twin"], StepKind.RULE_ERROR) == ("synthetic.twin",)
    assert by_id["synthetic.returner"].recommendation is not None


# --- unknown content ------------------------------------------------------


def test_a_missing_declared_input_is_flagged_and_skipped_never_raised() -> None:
    trace = run_rule(_reads("a.declared"), _world())
    assert trace.recommendation is None
    assert _subjects_of(trace, StepKind.INPUT_MISSING) == ("a.declared",)


# --- the trace itself -----------------------------------------------------


def test_the_trace_records_every_kind_in_execution_order() -> None:
    def evaluate(ctx: RuleContext) -> Recommendation | None:
        a = ctx.read_exact("a.declared")
        doubled = ctx.compute("doubled", a * 2)
        ctx.reject("synthetic-alternative", "costs more")
        return _recommend() if doubled > 0 else None

    spec = RuleSpec(
        rule_id="synthetic.full",
        domain="power",
        inputs=("a.declared",),
        unlocks=(_OVERCLOCK,),
        evaluate=evaluate,
    )
    world = _world(unlocks=(_OVERCLOCK,), a_declared=Fraction(5, 4))
    trace = run_rule(spec, world)
    assert _kinds(trace) == (
        StepKind.INPUT_READ,
        StepKind.COMPUTED,
        StepKind.ALTERNATIVE_REJECTED,
        StepKind.RULE_FIRED,
    )
    read, computed, rejected, _ = trace.steps
    assert read.source == "synthetic.fixture"
    assert read.value == Fraction(5, 4)
    assert computed.value == Fraction(5, 2)
    assert rejected.reason == "costs more"
    assert trace == run_rule(spec, world), "the same inputs must give the same trace"


def test_run_rules_orders_traces_by_rule_id() -> None:
    world = generate_worlds(seed=7, count=1)[0]
    ids = [t.rule_id for t in run_rules(tuple(reversed(SYNTHETIC_RULES)), world)]
    assert ids == sorted(spec.rule_id for spec in SYNTHETIC_RULES)


def test_unlock_keys_prefixes_each_carrier() -> None:
    state = UnlockState(
        purchased_schematics=frozenset({"/Synthetic/Schematic_TierTwo"}),
        recipes=frozenset({"/Synthetic/Recipe_AltPlate"}),
        current_game_phase=None,
        feature_flags={"synthetic-overclock": True, "synthetic-map": False},
        scanned_resources=frozenset(),
    )
    assert unlock_keys(state) == frozenset(
        {
            "schematic:/Synthetic/Schematic_TierTwo",
            "recipe:/Synthetic/Recipe_AltPlate",
            "feature:synthetic-overclock",
        }
    )


# --- addendum: set ordering, redacted reprs, strict ids ---------------------


def test_a_set_valued_input_is_refused_because_its_order_is_seed_dependent() -> None:
    for bad in (frozenset({Fraction(1)}), (Fraction(1), frozenset({"a"}))):
        trace = run_rule(_reads("a.declared"), _world(a_declared=bad))
        assert trace.recommendation is None, type(bad).__name__
        reasons = [s.reason for s in trace.steps if s.kind is StepKind.INPUT_REFUSED]
        assert reasons == ["a frozenset is not an exact type"], type(bad).__name__


_SENTINELS = ("synthetic-sentinel-subject", "synthetic-sentinel-source", "synthetic-sentinel-value")


def test_the_reprs_render_types_never_values_subjects_or_sources() -> None:
    subject, source, value = _SENTINELS
    step = TraceStep(kind=StepKind.INPUT_READ, subject=subject, source=source, value=value)
    offered = InputValue(value, source)
    world = WorldInputs(values={"a.declared": offered}, unlocks=frozenset({subject}))
    trace = Trace("synthetic.reader", "power", (step,), None)
    rendered = [repr(step), repr(offered), repr(world), repr(trace)]
    leaked = sum(1 for text in rendered for sentinel in _SENTINELS if sentinel in text)
    assert leaked == 0
    assert "input-read" in rendered[0]
    assert "str" in rendered[1]


def test_rule_ids_and_input_names_must_match_the_strict_pattern() -> None:
    def evaluate(_ctx: RuleContext) -> Recommendation | None:
        return None

    good = RuleSpec(
        rule_id="synthetic.ok_1:x-y",
        domain="power",
        inputs=("a.declared",),
        unlocks=("recipe:/Synthetic/Recipe_AltPlate",),
        evaluate=evaluate,
    )
    assert good.rule_id == "synthetic.ok_1:x-y"
    bads = (
        {"rule_id": "Synthetic World Name"},
        {"rule_id": "synthetic.\u2014"},
        {"rule_id": ""},
        {"inputs": ("a declared",)},
        {"inputs": ("A.Declared",)},
        {"domain": "Power Domain"},
        {"unlocks": ("recipe with space",)},
    )
    refused = 0
    for override in bads:
        fields: dict[str, object] = {
            "rule_id": "synthetic.ok",
            "domain": "power",
            "inputs": ("a.declared",),
            "unlocks": (),
            "evaluate": evaluate,
        }
        fields.update(override)
        try:
            RuleSpec(**fields)  # type: ignore[arg-type]
        except ValueError:
            refused += 1
    assert refused == len(bads)


# --- round 2: exact types, bounded work, names that cannot carry data -------


class _Tuple(tuple):
    pass


class _Str(str):
    __slots__ = ()


class _Int(int):
    __slots__ = ()


class _Fraction(Fraction):
    __slots__ = ()


def test_a_subclass_of_an_exact_type_is_refused() -> None:
    escaped = _Tuple((Fraction(1),))
    escaped.extra = [0.5]  # type: ignore[attr-defined]
    for bad in (escaped, _Str("text"), _Int(3), _Fraction(1, 2)):
        trace = run_rule(_reads("a.declared"), _world(a_declared=bad))
        assert trace.recommendation is None, type(bad).__name__
        assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("a.declared",)


def test_an_unshaped_read_name_is_a_rule_error_that_never_records_the_name() -> None:
    bad_names = (_Str("a.declared"), "Synthetic Bad Name", 7)
    for bad in bad_names:

        def evaluate(ctx: RuleContext, name: object = bad) -> Recommendation | None:
            ctx.read(name)  # type: ignore[arg-type]
            return _recommend()

        spec = RuleSpec(
            rule_id="synthetic.badname",
            domain="power",
            inputs=("a.declared",),
            unlocks=(),
            evaluate=evaluate,
        )
        trace = run_rule(spec, _world(a_declared=Fraction(1)))
        assert trace.recommendation is None, type(bad).__name__
        assert _subjects_of(trace, StepKind.RULE_ERROR) == ("read",)
        assert _subjects_of(trace, StepKind.INPUT_READ) == ()
        named = sum(1 for st in trace.steps if "Synthetic Bad Name" in (st.subject, st.reason))
        assert named == 0


def _raiser(exc_type: type[Exception]) -> RuleSpec:
    def evaluate(_ctx: RuleContext) -> Recommendation | None:
        raise exc_type

    return RuleSpec(
        rule_id="synthetic.raiser",
        domain="power",
        inputs=(),
        unlocks=(),
        evaluate=evaluate,
    )


def test_an_exception_type_name_is_recorded_only_when_it_is_an_identifier() -> None:
    spaced = type("Synthetic Spaced Name", (Exception,), {})
    accented = type("SyntheticErr" + chr(0xE9), (Exception,), {})
    for exc_type in (spaced, accented):
        trace = run_rule(_raiser(exc_type), _world())
        assert trace.recommendation is None
        assert _subjects_of(trace, StepKind.RULE_ERROR) == ("unnamed-exception",)
    control = run_rule(_raiser(LookupError), _world())
    assert _subjects_of(control, StepKind.RULE_ERROR) == ("LookupError",)


def test_a_rule_raising_its_own_refusal_is_a_rule_error() -> None:
    def evaluate(_ctx: RuleContext) -> Recommendation | None:
        raise InputRefusedError

    spec = RuleSpec(
        rule_id="synthetic.self-refuser",
        domain="power",
        inputs=(),
        unlocks=(),
        evaluate=evaluate,
    )
    trace = run_rule(spec, _world())
    assert trace.recommendation is None
    assert _subjects_of(trace, StepKind.RULE_ERROR) == ("InputRefusedError",)


def test_a_world_entry_that_is_not_an_input_value_is_refused_at_construction() -> None:
    refused = 0
    for bad in (Fraction(1), ("x", "synthetic.fixture"), None):
        try:
            WorldInputs(values={"a.declared": bad}, unlocks=frozenset())  # type: ignore[dict-item]
        except TypeError:
            refused += 1
    assert refused == 3  # noqa: PLR2004 - one per bad entry above


def _refusal_reasons(value: object) -> list[str]:
    trace = run_rule(_reads("a.declared"), _world(a_declared=value))
    return [st.reason for st in trace.steps if st.kind is StepKind.INPUT_REFUSED]


def test_shared_subtree_nesting_is_bounded_by_work_not_depth() -> None:
    value: object = Fraction(1)
    for _ in range(24):
        value = (value, value)
    assert _refusal_reasons(value) == ["too many parts to prove exact"]


def test_the_node_guard_refuses_a_wide_value_and_admits_one_under_the_cap() -> None:
    assert _refusal_reasons(tuple(Fraction(i) for i in range(20000))) == [
        "too many parts to prove exact"
    ]
    assert _refusal_reasons(tuple(Fraction(i) for i in range(9000))) == []


def test_the_depth_guard_refuses_a_deep_narrow_value() -> None:
    value: object = Fraction(1)
    for _ in range(40):
        value = (value,)
    assert _refusal_reasons(value) == ["nested too deeply to prove exact"]
    shallow: object = Fraction(1)
    for _ in range(20):
        shallow = (shallow,)
    assert _refusal_reasons(shallow) == []


# --- text must carry a visible character and no control character ----------

#: Whitespace-only and control-bearing text, built with chr() so this source
#: stays printable ASCII.
_BAD_TEXT = (
    "   ",
    chr(9),
    "Do" + chr(10) + "now",
    "Do" + chr(13),
    "Do" + chr(9) + "now",
    "Do" + chr(0),
    "Do" + chr(127),
)


def _rule(evaluate: object) -> RuleSpec:
    return RuleSpec(
        rule_id="synthetic.text",
        domain="power",
        inputs=(),
        unlocks=(),
        evaluate=evaluate,  # type: ignore[arg-type]
    )


def test_blank_or_control_text_is_a_rule_error_everywhere_text_is_taken() -> None:
    control = Recommendation(subject_key="s", action="Do it now", reason="spare power")
    assert run_rule(_returning(control), _world()).recommendation is not None

    for bad in _BAD_TEXT:
        recs = (
            Recommendation(subject_key=bad, action="Do", reason="r"),
            Recommendation(subject_key="s", action=bad, reason="r"),
            Recommendation(subject_key="s", action="Do", reason=bad),
            Recommendation(subject_key="s", action="Do", reason="r", target_milestone=bad),
            Recommendation(subject_key="s", action="Do", reason="r", requires=(bad,)),
        )
        for rec in recs:
            trace = run_rule(_returning(rec), _world())
            assert trace.recommendation is None, len(bad)
            assert StepKind.RULE_ERROR in _kinds(trace), len(bad)

        def reject_alt(ctx: RuleContext, text: str = bad) -> Recommendation | None:
            ctx.reject(text, "costs more")
            return _recommend()

        def reject_reason(ctx: RuleContext, text: str = bad) -> Recommendation | None:
            ctx.reject("alt", text)
            return _recommend()

        def label(ctx: RuleContext, text: str = bad) -> Recommendation | None:
            ctx.compute(text, Fraction(1))
            return _recommend()

        for evaluate in (reject_alt, reject_reason, label):
            trace = run_rule(_rule(evaluate), _world())
            assert trace.recommendation is None, len(bad)
            assert _kinds(trace) == (StepKind.RULE_ERROR,), len(bad)
