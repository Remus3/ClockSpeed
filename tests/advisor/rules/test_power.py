"""CS-500 slice S4: the D4 power rule family and the rule registry.

Graded here (BOOTSTRAP.md sections 5.3 and 5.4, CS-500 acceptance):

- the headroom rule fires on a synthetic overdraw, naming the shortfall as an
  exact figure or an exact bracket, and stays silent with spare generation;
- the headroom rule compares against the CLOCK-CORRECT draw - the clocked
  bracket - and never against the clock-blind reference-clock total;
- an incomplete clocked draw is NAMED by the gap rule and never advised on as
  if its total were a measurement;
- every rule declares every input it reads, and reads every input it declares;
- the registry is sorted by rule id and refuses a duplicated id;
- tier 3 of a fired card is the whole derivation, snapshot-checked.

Every balance here is hand-built from the audit dataclasses. No save, no game
install, no registry slice: every number and every class name is invented.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from clockspeed.advisor.cards import Card, card_for
from clockspeed.advisor.rules import build_registry, registered_rules
from clockspeed.advisor.rules import power as power_rules
from clockspeed.advisor.rules.power import (
    GAP_RULE,
    HEADROOM_RULE,
    IN_ELIDED,
    IN_GENERATION,
    IN_LOWER,
    IN_UPPER,
    RULES,
    balance_inputs,
)
from clockspeed.advisor.trace import (
    RuleSpec,
    StepKind,
    Trace,
    WorldInputs,
    run_rule,
    run_rules,
)
from clockspeed.audit.balance import (
    WorldBalance,
    WorldClockedDraw,
    WorldDraw,
    WorldProduction,
    WorldStarvation,
)


def _balance(  # noqa: PLR0913 - one keyword per field the rules read
    *,
    lower: Fraction,
    upper: Fraction,
    exact: bool,
    complete: bool = True,
    considered: int = 10,
    unread: int = 0,
    unmodeled: int = 0,
    elided: int = 0,
    blind: Fraction = Fraction(1),
    production: bool = True,
) -> WorldBalance:
    """Hand-build one synthetic balance. ``blind`` is the clock-blind total."""
    draw = WorldDraw(
        contributions=(),
        gaps=(),
        consumption_megawatts=blind,
        consumption_complete=True,
        classes_considered=0,
        unmodeled_class_count=0,
        unmodeled_contributor_count=0,
        warnings=(),
    )
    clocked = WorldClockedDraw(
        contributions=(),
        gaps=(),
        lower_megawatts=lower,
        upper_megawatts=upper,
        exact=exact,
        complete=complete,
        machines_considered=considered,
        bounded_machine_count=0,
        unread_clock_count=unread,
        elided_clock_count=elided,
        unmodeled_machine_count=unmodeled,
        warnings=(),
    )
    starvation = WorldStarvation(
        starved_indices=(),
        running_count=0,
        unconfigured_count=0,
        unknown_state_count=0,
        machines_considered=0,
        producing_available=False,
        warnings=(),
    )
    return WorldBalance(
        draw=draw,
        clocked_draw=clocked,
        starvation=starvation,
        production_available=production,
        connected_edges_available=False,
        warnings=(),
    )


def _world(balance: WorldBalance, generation: Fraction | None) -> WorldInputs:
    """Offer the balance through the adapter (CS-1271).

    A complete production model of ``generation`` MW is attached when one is given.
    """
    if generation is not None:
        balance = replace(balance, production=_production(generation, complete=True))
    return WorldInputs(values=balance_inputs(balance), unlocks=frozenset())


def _overdraw_world() -> WorldInputs:
    return _world(
        _balance(lower=Fraction(120), upper=Fraction(130), exact=False),
        Fraction(100),
    )


def test_headroom_rule_fires_on_synthetic_overdraw() -> None:
    trace = run_rule(HEADROOM_RULE, _overdraw_world())
    recommendation = trace.recommendation
    assert recommendation is not None
    assert recommendation.action == "Add between 20.00 and 30.00 MW of generation"
    computed = {s.subject: s.value for s in trace.steps if s.kind is StepKind.COMPUTED}
    assert computed == {
        "shortfall at the lower draw bound in MW": Fraction(20),
        "shortfall at the upper draw bound in MW": Fraction(30),
    }


def test_headroom_rule_names_an_exact_shortfall_as_one_figure() -> None:
    world = _world(
        _balance(lower=Fraction(301, 3), upper=Fraction(301, 3), exact=True), Fraction(100)
    )
    recommendation = run_rule(HEADROOM_RULE, world).recommendation
    assert recommendation is not None
    assert recommendation.action == "Add 0.33 (exactly 1/3) MW of generation"


def test_headroom_rule_flags_a_bracket_straddling_generation_as_a_risk() -> None:
    world = _world(_balance(lower=Fraction(90), upper=Fraction(110), exact=False), Fraction(100))
    recommendation = run_rule(HEADROOM_RULE, world).recommendation
    assert recommendation is not None
    assert recommendation.action == "Add up to 10.00 MW of generation"


@pytest.mark.parametrize(
    ("lower", "upper", "generation"),
    [
        (Fraction(80), Fraction(90), Fraction(100)),
        (Fraction(100), Fraction(100), Fraction(100)),
    ],
)
def test_headroom_rule_is_silent_with_spare_generation(
    lower: Fraction, upper: Fraction, generation: Fraction
) -> None:
    world = _world(_balance(lower=lower, upper=upper, exact=lower == upper), generation)
    trace = run_rule(HEADROOM_RULE, world)
    assert trace.recommendation is None
    rejected = [s.subject for s in trace.steps if s.kind is StepKind.ALTERNATIVE_REJECTED]
    assert rejected == ["add generation"]


def test_an_exact_flag_over_a_split_bracket_never_quotes_one_figure() -> None:
    world = _world(_balance(lower=Fraction(120), upper=Fraction(130), exact=True), Fraction(100))
    recommendation = run_rule(HEADROOM_RULE, world).recommendation
    assert recommendation is not None
    assert recommendation.action == "Add between 20.00 and 30.00 MW of generation"


def test_generation_equal_to_the_lower_bound_is_a_brownout_risk() -> None:
    world = _world(_balance(lower=Fraction(100), upper=Fraction(110), exact=False), Fraction(100))
    recommendation = run_rule(HEADROOM_RULE, world).recommendation
    assert recommendation is not None
    assert recommendation.action == "Add up to 10.00 MW of generation"
    assert recommendation.reason == (
        "Generation of 100.00 MW sits inside the clocked draw of 100.00 to 110.00 MW,"
        " a brownout risk"
    )


ELISION_WORDS = "assumes the default clock for 2 machines whose save omits the clock tag"


@pytest.mark.parametrize("rule", [HEADROOM_RULE, GAP_RULE], ids=lambda spec: spec.rule_id)
@pytest.mark.parametrize("elided", [0, 2])
def test_an_elided_clock_is_named_in_tier2_and_tier3(rule: RuleSpec, elided: int) -> None:
    world = _world(
        _balance(
            lower=Fraction(120),
            upper=Fraction(130),
            exact=False,
            complete=rule is HEADROOM_RULE,
            unread=0 if rule is HEADROOM_RULE else 2,
            unmodeled=0 if rule is HEADROOM_RULE else 1,
            elided=elided,
        ),
        Fraction(100),
    )
    card = card_for(run_rule(rule, world))
    assert card is not None
    elided_line = f"Read {IN_ELIDED} = {elided} from audit.balance.clocked_draw.elided_clock_count"
    assert elided_line in card.tier3
    if elided:
        assert ELISION_WORDS in card.tier2
        assert ELISION_WORDS in card.tier3
    else:
        assert "default clock" not in card.tier2
        assert "default clock" not in card.tier3


def test_headroom_rule_is_silent_when_production_is_not_modelled() -> None:
    world = _world(
        _balance(lower=Fraction(120), upper=Fraction(130), exact=False, production=False), None
    )
    trace = run_rule(HEADROOM_RULE, world)
    assert trace.recommendation is None
    assert [s.kind for s in trace.steps if s.kind is StepKind.INPUT_MISSING] == []


def test_headroom_rule_reads_the_clocked_draw_not_the_clock_blind_one() -> None:
    world = _world(
        _balance(lower=Fraction(120), upper=Fraction(130), exact=False, blind=Fraction(50)),
        Fraction(100),
    )
    reads = {s.subject: s for s in run_rule(HEADROOM_RULE, world).steps}
    assert reads[IN_UPPER].value == Fraction(130)
    assert reads[IN_UPPER].source == "audit.balance.clocked_draw.upper_megawatts"
    assert reads[IN_LOWER].value == Fraction(120)
    assert reads[IN_LOWER].source == "audit.balance.clocked_draw.lower_megawatts"
    assert run_rule(HEADROOM_RULE, world).recommendation is not None


def _all_inputs_world(*, complete: bool) -> WorldInputs:
    return _world(
        _balance(
            lower=Fraction(120),
            upper=Fraction(130),
            exact=False,
            complete=complete,
            unread=0 if complete else 2,
            unmodeled=0 if complete else 1,
        ),
        Fraction(100),
    )


@pytest.mark.parametrize("spec", RULES, ids=lambda spec: spec.rule_id)
def test_rule_declares_every_input_it_reads(spec: RuleSpec) -> None:
    traces = [run_rule(spec, _all_inputs_world(complete=flag)) for flag in (True, False)]
    read: set[str] = set()
    for trace in traces:
        assert trace.refused == ()
        assert [s for s in trace.steps if s.kind is StepKind.RULE_ERROR] == []
        read.update(s.subject for s in trace.steps if s.kind is StepKind.INPUT_READ)
    declared_unread = sorted(set(spec.inputs) - read)
    undeclared = sorted(read - set(spec.inputs))
    assert declared_unread == []
    assert undeclared == []
    assert any(trace.recommendation is not None for trace in traces)


def test_an_incomplete_draw_is_named_never_advised_as_exact() -> None:
    world = _world(
        _balance(
            lower=Fraction(120),
            upper=Fraction(130),
            exact=False,
            complete=False,
            considered=10,
            unread=2,
            unmodeled=1,
        ),
        Fraction(100),
    )
    headroom = run_rule(HEADROOM_RULE, world)
    assert headroom.recommendation is None
    assert [s.subject for s in headroom.steps if s.kind is StepKind.ALTERNATIVE_REJECTED] == [
        "compare the draw against generation"
    ]
    gap_card = card_for(run_rule(GAP_RULE, world))
    assert gap_card is not None
    assert gap_card.tier1 == "Resolve 3 unpriced machines before planning power"
    assert gap_card.tier2 == (
        "The clocked draw is a floor of 120.00 to 130.00 MW: "
        "2 clocks unread and 1 machine unmodeled, of 10"
    )
    headline_and_reason = f"{gap_card.tier1} {gap_card.tier2}".lower()
    assert "exact" not in headline_and_reason


def test_the_gap_rule_is_silent_on_a_complete_draw() -> None:
    trace = run_rule(GAP_RULE, _all_inputs_world(complete=True))
    assert trace.recommendation is None
    reasons = [s.reason for s in trace.steps if s.kind is StepKind.ALTERNATIVE_REJECTED]
    assert reasons == ["every machine the audit considered has a priced draw"]


def test_registry_is_sorted_and_refuses_duplicates() -> None:
    ids = [spec.rule_id for spec in registered_rules()]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    assert {HEADROOM_RULE.rule_id, GAP_RULE.rule_id} <= set(ids)
    with pytest.raises(ValueError, match="more than one rule"):
        build_registry(((HEADROOM_RULE,), (GAP_RULE, HEADROOM_RULE)))
    assert build_registry(((HEADROOM_RULE,), (GAP_RULE,))) == tuple(
        sorted((HEADROOM_RULE, GAP_RULE), key=lambda spec: spec.rule_id)
    )


def test_registry_runs_through_the_engine_in_rule_id_order() -> None:
    traces = run_rules(registered_rules(), _overdraw_world())
    assert [trace.rule_id for trace in traces] == sorted(t.rule_id for t in traces)


EXPECTED_TIER3 = "\n".join(
    [
        "Derivation of rule power.headroom (domain power)",
        "Advice: Add between 20.00 and 30.00 MW of generation",
        "Because: Clocked draw of 120.00 to 130.00 MW exceeds 100.00 MW of generation",
        "Target milestone: none",
        "Steps:",
        "  1. Read power.clocked_draw.complete = true from audit.balance.clocked_draw.complete",
        "  2. Read power.production_available = true from audit.balance.production_available",
        "  3. Read power.production_complete = true from"
        " audit.balance.production.production_complete",
        "  4. Read power.clocked_draw.lower_mw = 120.00 from"
        " audit.balance.clocked_draw.lower_megawatts",
        "  5. Read power.clocked_draw.upper_mw = 130.00 from"
        " audit.balance.clocked_draw.upper_megawatts",
        "  6. Read power.clocked_draw.exact = false from audit.balance.clocked_draw.exact",
        "  7. Read power.clocked_draw.elided_clock_count = 0 from"
        " audit.balance.clocked_draw.elided_clock_count",
        "  8. Read power.generation_mw = 100.00 from audit.balance.production.capacity_megawatts",
        "  9. Computed shortfall at the lower draw bound in MW = 20.00",
        "  10. Computed shortfall at the upper draw bound in MW = 30.00",
        "  11. Rejected hold generation as built: the draw exceeds generation"
        " at both ends of the clock bracket",
        "  12. Rejected quote one shortfall figure: the clock law brackets the draw,"
        " so the shortfall is a range",
        "  13. Rule power.headroom fired for power:generation-headroom",
    ]
)


def test_tier3_snapshot_shows_the_whole_derivation() -> None:
    trace: Trace = run_rule(HEADROOM_RULE, _overdraw_world())
    card = Card(trace)
    assert card.tier3 == EXPECTED_TIER3


# CS-1271: the adapter offers the audit's own generation figure and its
# completeness whenever a production model was computed, so the headroom rule
# reaches a definite verdict over a real balance with no synthetic injection.

AUDIT_CAPACITY_SOURCE = "audit.balance.production.capacity_megawatts"
AUDIT_PRODUCTION_COMPLETE_SOURCE = "audit.balance.production.production_complete"


def _production(capacity: Fraction, *, complete: bool) -> WorldProduction:
    """Hand-build one production model. An incomplete one carries one gap's count."""
    return WorldProduction(
        contributions=(),
        gaps=(),
        capacity_megawatts=capacity,
        production_complete=complete,
        classes_considered=0,
        non_generator_class_count=0,
        unmodeled_class_count=0 if complete else 1,
        unmodeled_contributor_count=0 if complete else 1,
        warnings=(),
    )


def _produced(capacity: Fraction, *, complete: bool) -> WorldInputs:
    """A complete 120-130 MW clocked draw over an audit-computed production model."""
    base = _balance(lower=Fraction(120), upper=Fraction(130), exact=False)
    balance = replace(base, production=_production(capacity, complete=complete))
    return WorldInputs(values=balance_inputs(balance), unlocks=frozenset())


def test_the_adapter_offers_generation_and_its_completeness() -> None:
    values = _produced(Fraction(100), complete=False).values

    offered = IN_GENERATION in values
    assert offered, "the adapter offers no generation input"
    generation = values[IN_GENERATION]
    assert generation.value == Fraction(100)
    assert type(generation.value) is Fraction
    assert generation.source == AUDIT_CAPACITY_SOURCE
    complete = values[power_rules.IN_PRODUCTION_COMPLETE]
    assert complete.value is False
    assert complete.source == AUDIT_PRODUCTION_COMPLETE_SOURCE


def test_the_adapter_offers_no_generation_without_a_production_model() -> None:
    values = balance_inputs(
        _balance(lower=Fraction(1), upper=Fraction(1), exact=True, production=False)
    )

    offered = sorted({IN_GENERATION, power_rules.IN_PRODUCTION_COMPLETE} & set(values))
    assert offered == []


def test_a_complete_production_figure_gives_a_definite_verdict() -> None:
    trace = run_rule(HEADROOM_RULE, _produced(Fraction(100), complete=True))

    missing = [s.subject for s in trace.steps if s.kind is StepKind.INPUT_MISSING]
    assert missing == []
    assert trace.refused == ()
    card = card_for(trace)
    assert card is not None
    assert card.tier1 == "Add between 20.00 and 30.00 MW of generation"


def test_an_incomplete_production_figure_is_rejected_never_compared() -> None:
    trace = run_rule(HEADROOM_RULE, _produced(Fraction(100), complete=False))

    missing = [s.subject for s in trace.steps if s.kind is StepKind.INPUT_MISSING]
    rejected = [
        (s.subject, s.reason) for s in trace.steps if s.kind is StepKind.ALTERNATIVE_REJECTED
    ]
    assert missing == []
    assert trace.recommendation is None
    assert rejected == [
        (
            "compare the draw against generation",
            "some built generators have no modelled output, so the capacity is a floor"
            " and not a measurement",
        )
    ]
