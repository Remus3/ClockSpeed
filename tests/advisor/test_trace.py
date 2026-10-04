"""CS-500 slice S1: the rule trace engine.

Graded here, each against a control that shows the arm can see the defect:

- a rule reading an input it did not declare is REFUSED and the read is
  RECORDED in the trace (BOOTSTRAP.md section 5.4);
- a rule whose required unlock is unmet emits no recommendation and is never
  evaluated;
- over generated world states, no recommendation carries an unmet
  precondition - the property-test invariant of section 5.4;
- a float input is refused (non-negotiable 6);
- a declared input the world does not carry is flagged and skipped, never
  raised (non-negotiable 7).
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from fractions import Fraction

from clockspeed.advisor.trace import (
    InputRefusedError,
    InputValue,
    Recommendation,
    RuleContext,
    RuleSpec,
    StepKind,
    Trace,
    WorldInputs,
    run_rule,
    run_rules,
    unlock_keys,
)
from clockspeed.save.world import UnlockState
from tests.advisor.worlds import SYNTHETIC_RULES, UNLOCK_UNIVERSE, generate_worlds

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


# --- exactness ------------------------------------------------------------


@dataclass(frozen=True)
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
    trace = run_rule(spec, _world(a_declared="synthetic-text"))
    assert trace.recommendation is None
    assert _subjects_of(trace, StepKind.INPUT_REFUSED) == ("a.declared",)


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
