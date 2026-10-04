"""CS-500 slice S2: card identity and the three explain tiers.

Graded here (BOOTSTRAP.md sections 5.1 and 5.2, phase 5 acceptance A3 and A4):

- a card id is sha256 over canonical ASCII of ``(rule_id, subject_key,
  target_milestone)`` and NOTHING volatile, so it survives a save reload whose
  input values moved;
- a card takes no tier text from anyone: its only constructor parameter is the
  trace, and all three tiers are projections of it;
- tier 3 renders every step of the trace - every input read with its source,
  every computed value through ``display_decimal``, every rejected alternative
  with its reason - so it changes whenever the trace does;
- a trace with no recommendation yields no card;
- the text is ASCII and identical under two string-hash seeds.

Every rule, name and value here is synthetic.
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import os
import subprocess
import sys
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.advisor.cards import (
    CARD_ID_SCHEME,
    Card,
    card_for,
    card_id,
    cards_for,
)
from clockspeed.advisor.trace import (
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
)
from tests.advisor.worlds import SYNTHETIC_RULES, UNLOCK_UNIVERSE, generate_worlds

_CHILD_TIMEOUT_S: Final = 120
_SHA256_HEX_LEN: Final = 64
_MIN_CANONICAL_CARDS: Final = 10
_OVERCLOCK: Final = SYNTHETIC_RULES[0]


def _world(values: dict[str, tuple[object, str]], unlocks: tuple[str, ...] = ()) -> WorldInputs:
    return WorldInputs(
        values={name: InputValue(value, source) for name, (value, source) in values.items()},
        unlocks=frozenset(unlocks),
    )


def _power_world(headroom: Fraction, draw: Fraction) -> WorldInputs:
    return _world(
        {
            "synthetic.headroom": (headroom, "synthetic.power.headroom"),
            "synthetic.draw": (draw, "synthetic.power.draw"),
        },
        unlocks=("feature:synthetic-overclock",),
    )


def _spec(
    evaluate: Callable[[RuleContext], Recommendation | None],
    inputs: tuple[str, ...] = (),
    rule_id: str = "synthetic.card-rule",
) -> RuleSpec:
    return RuleSpec(rule_id=rule_id, domain="power", inputs=inputs, unlocks=(), evaluate=evaluate)


def _card(trace: Trace) -> Card:
    card = card_for(trace)
    if card is None:
        pytest.fail("the trace carried a recommendation and still yielded no card")
    return card


# ---------------------------------------------------------------------------
# A3 - identity


def test_card_id_ignores_volatile_inputs() -> None:
    """The same advice on a reloaded save with moved numbers keeps its id."""
    before = run_rule(_OVERCLOCK, _power_world(Fraction(900), Fraction(300)))
    after = run_rule(_OVERCLOCK, _power_world(Fraction(1250, 3), Fraction(7, 2)))
    first, second = _card(before), _card(after)

    # Control: the two traces really differ, so equal ids are not vacuous.
    assert before.steps != after.steps
    assert first.tier3 != second.tier3
    assert first.id == second.id
    assert first.id == card_id("synthetic.overclock", "synthetic-grid", None)


def test_card_id_is_sha256_over_canonical_ascii_of_the_identity_triple() -> None:
    canonical = json.dumps(
        [CARD_ID_SCHEME, "synthetic.rule", "synthetic-subject", "synthetic-milestone"],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    expected = hashlib.sha256(canonical).hexdigest()

    assert card_id("synthetic.rule", "synthetic-subject", "synthetic-milestone") == expected
    assert len(expected) == _SHA256_HEX_LEN


def test_card_id_separates_every_field_unambiguously() -> None:
    ids = (
        card_id("synthetic.a", "bc", None),
        card_id("synthetic.ab", "c", None),
        card_id("synthetic.a", "bc", "None"),
        card_id("synthetic.a", "bc", ""),
        card_id("synthetic.a", "bc", "milestone"),
        card_id("synthetic.b", "bc", None),
    )
    assert len(frozenset(ids)) == len(ids)


def test_card_id_changes_with_the_target_milestone() -> None:
    def rule(milestone: str) -> RuleSpec:
        def evaluate(_ctx: RuleContext) -> Recommendation:
            return Recommendation(
                subject_key="synthetic-subject",
                action="Build it",
                reason="because",
                target_milestone=milestone,
            )

        return _spec(evaluate)

    world = _world({})
    near = _card(run_rule(rule("synthetic-tier-two"), world))
    far = _card(run_rule(rule("synthetic-tier-five"), world))
    assert near.id != far.id
    assert near.id == card_id("synthetic.card-rule", "synthetic-subject", "synthetic-tier-two")


# ---------------------------------------------------------------------------
# A4 - tiers are projections of the trace, never authored


def test_card_accepts_no_authored_tier_text() -> None:
    trace = run_rule(_OVERCLOCK, _power_world(Fraction(900), Fraction(300)))

    assert tuple(inspect.signature(Card).parameters) == ("trace",)
    for name in ("tier1", "tier2", "tier3", "id", "headline", "reason", "derivation"):
        with pytest.raises(TypeError):
            Card(trace, **{name: "authored by hand"})
    card = Card(trace)
    for name in ("tier1", "tier2", "tier3", "id"):
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            setattr(card, name, "authored by hand")
    assert "authored by hand" not in card.tier3


def test_a_card_refuses_a_trace_with_no_recommendation() -> None:
    trace = run_rule(_OVERCLOCK, _power_world(Fraction(1), Fraction(5)))
    assert trace.recommendation is None
    with pytest.raises(ValueError, match="no recommendation"):
        Card(trace)


def test_a_trace_with_no_recommendation_yields_no_card() -> None:
    declined = run_rule(_OVERCLOCK, _power_world(Fraction(1), Fraction(5)))
    gated = run_rule(_OVERCLOCK, _world({}))
    fired = run_rule(_OVERCLOCK, _power_world(Fraction(5), Fraction(1)))

    assert card_for(declined) is None
    assert card_for(gated) is None
    assert card_for(fired) is not None  # control: the same rule can yield one


def test_tier1_and_tier2_project_the_recommendation_on_one_line() -> None:
    def evaluate(_ctx: RuleContext) -> Recommendation:
        return Recommendation(
            subject_key="synthetic-subject",
            # Space runs only: the engine refuses a tab or newline in a
            # recommendation as a rule-error, so no card ever sees one.
            action="Build   the  synthetic thing",
            reason="the line    is saturated",
        )

    card = _card(run_rule(_spec(evaluate), _world({})))
    assert card.tier1 == "Build the synthetic thing"
    assert card.tier2 == "the line is saturated"
    assert card.domain == "power"
    assert card.rule_id == "synthetic.card-rule"
    assert card.subject_key == "synthetic-subject"
    assert card.target_milestone is None


def test_tier3_changes_when_the_trace_changes() -> None:
    low = _card(run_rule(_OVERCLOCK, _power_world(Fraction(900), Fraction(300))))
    high = _card(run_rule(_OVERCLOCK, _power_world(Fraction(1250, 3), Fraction(7, 2))))

    assert low.tier3 != high.tier3
    assert "900.00" in low.tier3
    assert "600.00" in low.tier3  # computed spare
    assert "416.67 (exactly 1250/3)" in high.tier3
    assert "3.50" in high.tier3


def test_tier3_names_every_rejected_alternative() -> None:
    def evaluate(ctx: RuleContext) -> Recommendation:
        ctx.reject("synthetic-truck", "the route is too long for a truck")
        ctx.reject("synthetic-belt", "a belt cannot carry the rate")
        ctx.reject("synthetic-drone", "drones are not unlocked")
        return Recommendation(
            subject_key="synthetic-route", action="Lay a train line", reason="rate and distance"
        )

    tier3 = _card(run_rule(_spec(evaluate), _world({}))).tier3
    for alternative, reason in (
        ("synthetic-truck", "the route is too long for a truck"),
        ("synthetic-belt", "a belt cannot carry the rate"),
        ("synthetic-drone", "drones are not unlocked"),
    ):
        assert f"Rejected {alternative}: {reason}" in tier3
    # Order is the trace's order, not sorted.
    assert tier3.index("synthetic-truck") < tier3.index("synthetic-belt")
    assert tier3.index("synthetic-belt") < tier3.index("synthetic-drone")


def test_tier3_renders_every_input_read_with_its_source() -> None:
    tier3 = _card(run_rule(_OVERCLOCK, _power_world(Fraction(900), Fraction(300)))).tier3
    assert "Read synthetic.headroom = 900.00 from synthetic.power.headroom" in tier3
    assert "Read synthetic.draw = 300.00 from synthetic.power.draw" in tier3
    assert "Computed spare = 600.00" in tier3
    assert "Rule synthetic.overclock fired for synthetic-grid" in tier3


def test_tier3_renders_every_step_kind_with_every_field() -> None:
    """A hand-built trace carrying one step of EVERY kind, each field planted."""
    steps = []
    expected = []
    # The rule-fired step goes last, as a consistent trace requires.
    kinds = [k for k in StepKind if k is not StepKind.RULE_FIRED] + [StepKind.RULE_FIRED]
    for index, kind in enumerate(kinds):
        subject = f"subject-{index}"
        source = f"source-{index}"
        reason = f"reason-{index}"
        value = Fraction(index * 4 + 1, 4)
        steps.append(
            TraceStep(kind=kind, subject=subject, source=source, value=value, reason=reason)
        )
        needles = [subject]
        if kind is StepKind.INPUT_READ:
            needles += [source, f"{index}.25"]
        elif kind is StepKind.COMPUTED:
            needles += [f"{index}.25"]
        elif kind is StepKind.RULE_FIRED:
            needles += ["synthetic.every-kind"]
        else:
            needles += [reason]
        expected.append((kind, needles))
    trace = Trace(
        rule_id="synthetic.every-kind",
        domain="power",
        steps=tuple(steps),
        recommendation=Recommendation(
            subject_key=f"subject-{len(kinds) - 1}", action="Act", reason="why"
        ),
    )
    lines = _card(trace).tier3.splitlines()
    step_lines = [line for line in lines if line.lstrip()[:1].isdigit()]

    assert len(step_lines) == len(StepKind)
    for (kind, needles), line in zip(expected, step_lines, strict=True):
        missing = [needle for needle in needles if needle not in line]
        assert missing == [], f"step kind {kind.value} rendered without {missing}"


def test_computed_values_render_through_display_decimal() -> None:
    def evaluate(ctx: RuleContext) -> Recommendation:
        ctx.compute("third", Fraction(1, 3))
        ctx.compute("half-tie", Fraction(1, 8))
        ctx.compute("negative", Fraction(-15, 2))
        ctx.compute("whole", Fraction(780))
        return Recommendation(subject_key="synthetic-subject", action="Act", reason="why")

    tier3 = _card(run_rule(_spec(evaluate), _world({}))).tier3
    assert "Computed third = 0.33 (exactly 1/3)" in tier3
    assert "Computed half-tie = 0.12 (exactly 1/8)" in tier3  # half-even, once
    assert "Computed negative = -7.50" in tier3
    assert "exactly -15/2" not in tier3
    assert "Computed whole = 780.00" in tier3
    assert "exactly 780" not in tier3


@dataclasses.dataclass(frozen=True, slots=True)
class _Node:
    purity: str
    rate: Fraction


def test_tier3_renders_structured_inputs_deterministically() -> None:
    def evaluate(ctx: RuleContext) -> Recommendation:
        for name in ("synthetic.nodes", "synthetic.flags", "synthetic.label", "synthetic.none"):
            ctx.read(name)
        return Recommendation(subject_key="synthetic-subject", action="Act", reason="why")

    inputs = ("synthetic.nodes", "synthetic.flags", "synthetic.label", "synthetic.none")
    world = _world(
        {
            "synthetic.nodes": (
                (_Node("pure", Fraction(120)), _Node("normal", Fraction(1, 3))),
                "synthetic.map",
            ),
            "synthetic.flags": (
                MappingProxyType({"zeta": True, "alpha": 3}),
                "synthetic.flags",
            ),
            "synthetic.label": ("caf\xe9\nline", "synthetic.text"),
            "synthetic.none": (None, "synthetic.text"),
        }
    )
    tier3 = _card(run_rule(_spec(evaluate, inputs), world)).tier3

    assert '(_Node(purity="pure", rate=120.00), ' in tier3
    assert '_Node(purity="normal", rate=0.33 (exactly 1/3)))' in tier3
    assert '{"alpha": 3, "zeta": true}' in tier3  # keys sorted, not insertion order
    assert '"caf\\u00e9\\nline"' in tier3
    assert "Read synthetic.none = none from synthetic.text" in tier3
    assert tier3.isascii()


def _rendered_value(value: object) -> str:
    """The text tier 3 renders for one input value read by a real rule."""

    def evaluate(ctx: RuleContext) -> Recommendation:
        ctx.read("synthetic.value")
        return Recommendation(subject_key="synthetic-subject", action="Act", reason="why")

    world = _world({"synthetic.value": (value, "synthetic.src")})
    tier3 = _card(run_rule(_spec(evaluate, ("synthetic.value",)), world)).tier3
    prefix, suffix = "Read synthetic.value = ", " from synthetic.src"
    line = next(line for line in tier3.splitlines() if prefix in line)
    return line.split(prefix, 1)[1].removesuffix(suffix)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("900.00", Fraction(900)),
        ("none", None),
        ("a\nb", "a\\nb"),
        ("true", True),
        ("3", 3),
        ("0.33 (exactly 1/3)", Fraction(1, 3)),
        ("(1, 2)", (1, 2)),
    ],
)
def test_tier3_renders_a_string_distinctly_from_every_lookalike(
    left: object, right: object
) -> None:
    rendered_left, rendered_right = _rendered_value(left), _rendered_value(right)
    assert rendered_left != rendered_right


def test_tier3_quotes_a_string_and_leaves_none_bare() -> None:
    assert _rendered_value("none") == '"none"'
    assert _rendered_value(None) == "none"
    assert _rendered_value("a\nb") == '"a\\nb"'
    assert _rendered_value("a\\nb") == '"a\\\\nb"'


def test_target_milestone_header_quotes_a_string_and_leaves_none_bare() -> None:
    def rule(milestone: str | None) -> RuleSpec:
        def evaluate(_ctx: RuleContext) -> Recommendation:
            return Recommendation(
                subject_key="synthetic-subject",
                action="Act",
                reason="why",
                target_milestone=milestone,
            )

        return _spec(evaluate)

    named = _card(run_rule(rule("none"), _world({}))).tier3
    absent = _card(run_rule(rule(None), _world({}))).tier3
    assert 'Target milestone: "none"' in named
    assert "Target milestone: none" in absent
    assert named != absent


def test_card_text_is_ascii_even_for_a_hand_built_trace() -> None:
    trace = Trace(
        rule_id="synthetic.ascii",
        domain="power",
        steps=(
            TraceStep(
                kind=StepKind.INPUT_READ,
                subject="synthetic.name",
                source="synthetic.\u2014source",
                value="\u201cquoted\u201d",
            ),
            TraceStep(kind=StepKind.INPUT_READ, subject="synthetic.set", value=frozenset({"a"})),
            TraceStep(kind=StepKind.RULE_FIRED, subject="s"),
        ),
        recommendation=Recommendation(subject_key="s", action="Act\u2013now", reason="why"),
    )
    card = _card(trace)
    for text in (card.tier1, card.tier2, card.tier3):
        assert text.isascii()
    # A set is never iterated: its rendering names only the type.
    assert "<frozenset>" in card.tier3


# ---------------------------------------------------------------------------
# refusals - a card is never built from a trace it cannot honestly project


def _forged(
    *,
    action: object = "Act",
    reason: object = "why",
    subject: object = "synthetic-subject",
    milestone: object = None,
    rule_id: object = "synthetic.forged",
    steps: tuple[TraceStep, ...] | None = None,
) -> Trace:
    """A hand-built trace; by default one well-formed rule-fired step for ``subject``."""
    fired = (TraceStep(kind=StepKind.RULE_FIRED, subject=str(subject)),)
    return Trace(
        rule_id=rule_id,  # type: ignore[arg-type]
        domain="power",
        steps=fired if steps is None else steps,
        recommendation=Recommendation(
            subject_key=subject,  # type: ignore[arg-type]
            action=action,  # type: ignore[arg-type]
            reason=reason,  # type: ignore[arg-type]
            target_milestone=milestone,  # type: ignore[arg-type]
        ),
    )


def test_a_well_formed_forged_trace_is_accepted() -> None:
    # Control for every refusal below: the forging helper itself is not refused.
    assert Card(_forged()).tier1 == "Act"


@pytest.mark.parametrize(("action", "reason"), [("   ", "why"), ("Act", "\t"), ("\n", " \t ")])
def test_a_card_refuses_an_empty_headline_or_reason(action: str, reason: str) -> None:
    with pytest.raises(ValueError, match="empty"):
        Card(_forged(action=action, reason=reason))


def test_card_id_refuses_a_non_str_identity_field() -> None:
    # A tuple and a list serialise to the same JSON array; neither may reach the hash.
    for subject in (("a",), ["a"]):
        with pytest.raises(TypeError):
            card_id("synthetic.rule", subject, None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        card_id(("synthetic.rule",), "a", None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        card_id("synthetic.rule", "a", ["m"])  # type: ignore[arg-type]

    class _Str(str):
        __slots__ = ()

    with pytest.raises(TypeError):
        card_id("synthetic.rule", _Str("a"), None)
    assert len(card_id("synthetic.rule", "a", None)) == _SHA256_HEX_LEN  # control


@pytest.mark.parametrize(
    "fields",
    [
        {"subject": ("a",)},
        {"subject": ["a"]},
        {"milestone": ("m",)},
        {"rule_id": ("synthetic.forged",)},
        {"action": ("Act",)},
        {"reason": 7},
    ],
)
def test_a_card_refuses_a_non_str_identity_or_tier_field(fields: dict[str, object]) -> None:
    with pytest.raises(TypeError):
        Card(_forged(**fields))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "steps",
    [
        (),
        (TraceStep(kind=StepKind.RULE_FIRED, subject="another-subject"),),
        (
            TraceStep(kind=StepKind.RULE_FIRED, subject="synthetic-subject"),
            TraceStep(kind=StepKind.COMPUTED, subject="late", value=Fraction(1)),
        ),
        (
            TraceStep(kind=StepKind.RULE_FIRED, subject="synthetic-subject"),
            TraceStep(kind=StepKind.RULE_FIRED, subject="synthetic-subject"),
        ),
        (TraceStep(kind=StepKind.COMPUTED, subject="only", value=Fraction(1)),),
    ],
    ids=["no-fired", "fired-for-another", "fired-not-last", "fired-twice", "computed-only"],
)
def test_a_card_refuses_a_trace_whose_firing_disagrees_with_its_recommendation(
    steps: tuple[TraceStep, ...],
) -> None:
    with pytest.raises(ValueError, match="rule-fired"):
        Card(_forged(steps=steps))


def test_cards_for_keeps_input_order_between_equal_ids() -> None:
    first = _forged(
        steps=(
            TraceStep(kind=StepKind.COMPUTED, subject="first", value=Fraction(1)),
            TraceStep(kind=StepKind.RULE_FIRED, subject="synthetic-subject"),
        )
    )
    second = _forged(
        steps=(
            TraceStep(kind=StepKind.COMPUTED, subject="second", value=Fraction(2)),
            TraceStep(kind=StepKind.RULE_FIRED, subject="synthetic-subject"),
        )
    )
    forward = cards_for((first, second))
    backward = cards_for((second, first))

    assert forward[0].id == forward[1].id  # control: the ids really tie
    assert [c.trace for c in forward] == [first, second]
    assert [c.trace for c in backward] == [second, first]


# ---------------------------------------------------------------------------
# privacy and determinism


def test_card_repr_is_redacted() -> None:
    marker = "PLANTED-MARKER-7f3a"

    def evaluate(ctx: RuleContext) -> Recommendation:
        ctx.read("synthetic.value")
        ctx.reject(f"alt-{marker}", f"reason-{marker}")
        return Recommendation(
            subject_key=f"subject-{marker}",
            action=f"Act {marker}",
            reason=f"why {marker}",
            target_milestone=f"m-{marker}",
        )

    world = _world({"synthetic.value": (f"value-{marker}", f"source-{marker}")})
    card = _card(run_rule(_spec(evaluate, ("synthetic.value",)), world))
    rendered = repr(card)
    leaked = marker in rendered or marker in str(card)

    assert marker in card.tier3  # control: the marker is really in the card
    assert not leaked
    assert card.id in rendered
    assert "domain=power" in rendered
    assert "steps=3" in rendered
    assert "rejected=1" in rendered


def test_card_repr_never_raises_or_leaks_when_the_constructor_was_bypassed() -> None:
    marker = "PLANTED-MARKER-9c1e"
    card = object.__new__(Card)
    object.__setattr__(card, "trace", marker)
    rendered = repr(card)
    leaked = marker in rendered

    assert not leaked
    assert rendered == "Card(<not built from a recommending trace>)"


def test_cards_for_drops_silent_traces_and_orders_by_rule_then_id() -> None:
    world = _world(
        {
            "synthetic.headroom": (Fraction(900), "synthetic.power"),
            "synthetic.draw": (Fraction(300), "synthetic.power"),
            "synthetic.purity": (Fraction(4), "synthetic.nodes"),
            "synthetic.distance": (Fraction(1), "synthetic.nodes"),
        },
        unlocks=UNLOCK_UNIVERSE,
    )
    traces = run_rules(SYNTHETIC_RULES, world)
    silent = Trace("synthetic.aaa-silent", "power", (), None)
    cards = cards_for((*reversed(traces), silent))

    assert [c.rule_id for c in cards] == sorted(c.rule_id for c in cards)
    assert "synthetic.aaa-silent" not in [c.rule_id for c in cards]
    assert len(cards) == len(SYNTHETIC_RULES)  # control: every synthetic rule fired here


def canonical_cards() -> str:
    """Every card over a seeded population, rendered to one ASCII string."""
    parts = [
        "\n".join((card.id, card.domain, card.tier1, card.tier2, card.tier3))
        for world in generate_worlds(seed=500, count=40)
        for card in cards_for(run_rules(SYNTHETIC_RULES, world))
    ]
    return "\n----\n".join(parts)


def test_card_output_is_identical_across_hash_seeds() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (
        "import sys; from tests.advisor.test_cards import canonical_cards;"
        " sys.stdout.buffer.write(canonical_cards().encode('ascii'))"
    )
    outputs = []
    for seed in ("1", "4242"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        run = subprocess.run(
            [sys.executable, "-c", script],
            cwd=root,
            env=env,
            capture_output=True,
            check=False,
            timeout=_CHILD_TIMEOUT_S,
        )
        exit_code = run.returncode
        assert exit_code == 0, "the child process failed"
        outputs.append(run.stdout)

    local = canonical_cards()
    assert local.count("\n----\n") > _MIN_CANONICAL_CARDS  # control: the population is not empty
    same = outputs[0] == outputs[1] == local.encode("ascii")
    assert same, "card text differed between hash seeds"
