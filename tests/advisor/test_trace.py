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
import enum
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

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
