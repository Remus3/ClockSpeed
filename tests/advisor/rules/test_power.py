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
- tier 3 of a fired card is the whole derivation, snapshot-checked;
- CS-1288: every rule declares the three build inputs and reads them first,
  and off the pin every card names both builds on tier 2 while its headline
  and every computed figure stay the on-pin run's own, and no run - firing or
  silent - settles its rule.

Every balance here is hand-built from the audit dataclasses. No save, no game
install, no registry slice: every number and every class name is invented.
The build inputs are the audit's own over a synthetic header whose build is
the pin read at test time, or the pin plus one off it - never a typed
changelist (the session 134 ruling, and the session 138 ruling F8).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from fractions import Fraction

import pytest

from clockspeed.advisor.advise import settled_rules
from clockspeed.advisor.build import BUILD_INPUTS
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
    InputValue,
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
from clockspeed.audit.build import WARN_BUILD_MISMATCH, WARN_BUILD_UNCOMPARED
from tests.advisor.build_fixtures import (
    build_check,
    game_pin,
    off_pin_build_inputs,
    pinned_build_inputs,
    uncompared_build_inputs,
)

#: One save's build inputs, as :mod:`tests.advisor.build_fixtures` builds them.
BuildInputs = dict[str, InputValue]


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
    omitted: int = 0,
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
        omitted_consumer_count=omitted,
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


def _offered(balance: WorldBalance, build: BuildInputs | None = None) -> WorldInputs:
    """Offer the balance through the adapter beside one save's build inputs (CS-1288).

    ``build`` defaults to a save written by the pinned build itself, the pin
    read at test time. The two name sets are asserted disjoint, so the build
    inputs never overwrite a balance input.
    """
    values = balance_inputs(balance)
    offered = pinned_build_inputs(game_pin()) if build is None else build
    overlap = sorted(set(values) & set(offered))
    assert overlap == []
    values.update(offered)
    return WorldInputs(values=values, unlocks=frozenset())


def _world(
    balance: WorldBalance, generation: Fraction | None, build: BuildInputs | None = None
) -> WorldInputs:
    """Offer the balance through the adapter (CS-1271), beside the build inputs.

    A complete production model of ``generation`` MW is attached when one is given.
    """
    if generation is not None:
        balance = replace(balance, production=_production(generation, complete=True))
    return _offered(balance, build)


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
    assert [s.subject for s in headroom.steps if s.kind is StepKind.VERDICT_INDETERMINATE] == [
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


@pytest.mark.parametrize(
    ("unread", "unmodeled", "omitted", "headline", "reason_tail"),
    [
        (
            2,
            1,
            3,
            "Resolve 6 unpriced machines before planning power",
            "2 clocks unread and 1 machine unmodeled, of 10;"
            " 3 built power consumers were never considered",
        ),
        (
            0,
            0,
            1,
            "Resolve 1 unpriced machine before planning power",
            "0 clocks unread and 0 machines unmodeled, of 10;"
            " 1 built power consumer was never considered",
        ),
    ],
    ids=["beside-gaps", "omission-alone"],
)
def test_an_omitted_consumer_is_counted_and_named_in_the_gap_card(
    unread: int, unmodeled: int, omitted: int, headline: str, reason_tail: str
) -> None:
    """CS-1266: a built consumer the draw never considered is unpriced and is said so.

    The draw is incomplete BY THE OMISSION ALONE in the second row, so a gap
    card that counted only unread clocks and unmodeled machines would tell the
    operator to resolve nothing.
    """
    world = _world(
        _balance(
            lower=Fraction(120),
            upper=Fraction(130),
            exact=False,
            complete=False,
            considered=10,
            unread=unread,
            unmodeled=unmodeled,
            omitted=omitted,
        ),
        Fraction(100),
    )
    trace = run_rule(GAP_RULE, world)
    card = card_for(trace)
    assert card is not None
    assert card.tier1 == headline
    assert card.tier2 == f"The clocked draw is a floor of 120.00 to 130.00 MW: {reason_tail}"
    computed = {s.subject: s.value for s in trace.steps if s.kind is StepKind.COMPUTED}
    unpriced = unread + unmodeled + omitted
    assert computed == {
        "unpriced machines": Fraction(unpriced),
        "priced share of machines": Fraction(10 + omitted - unpriced, 10 + omitted),
    }
    omitted_line = (
        f"Read {power_rules.IN_OMITTED} = {omitted} from"
        " audit.balance.clocked_draw.omitted_consumer_count"
    )
    assert omitted_line in card.tier3
    headroom = run_rule(HEADROOM_RULE, world)
    assert headroom.recommendation is None


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


def expected_tier3(pin: int) -> str:
    """The whole on-pin derivation of the overdraw card, the pin read at test time."""
    return "\n".join(
        [
            "Derivation of rule power.headroom (domain power)",
            "Advice: Add between 20.00 and 30.00 MW of generation",
            "Because: Clocked draw of 120.00 to 130.00 MW exceeds 100.00 MW of generation",
            "Target milestone: none",
            "Steps:",
            f"  1. Read build.save_changelist = {pin} from audit.build.save_changelist",
            f"  2. Read build.pinned_changelist = {pin} from audit.build.pinned_changelist",
            "  3. Read build.warnings = {} from audit.build.warnings",
            "  4. Read power.clocked_draw.complete = true from audit.balance.clocked_draw.complete",
            "  5. Read power.production_available = true from audit.balance.production_available",
            "  6. Read power.production_complete = true from"
            " audit.balance.production.production_complete",
            "  7. Read power.clocked_draw.lower_mw = 120.00 from"
            " audit.balance.clocked_draw.lower_megawatts",
            "  8. Read power.clocked_draw.upper_mw = 130.00 from"
            " audit.balance.clocked_draw.upper_megawatts",
            "  9. Read power.clocked_draw.exact = false from audit.balance.clocked_draw.exact",
            "  10. Read power.clocked_draw.elided_clock_count = 0 from"
            " audit.balance.clocked_draw.elided_clock_count",
            "  11. Read power.generation_mw = 100.00 from"
            " audit.balance.production.capacity_megawatts",
            "  12. Computed shortfall at the lower draw bound in MW = 20.00",
            "  13. Computed shortfall at the upper draw bound in MW = 30.00",
            "  14. Rejected hold generation as built: the draw exceeds generation"
            " at both ends of the clock bracket",
            "  15. Rejected quote one shortfall figure: the clock law brackets the draw,"
            " so the shortfall is a range",
            "  16. Rule power.headroom fired for power:generation-headroom",
        ]
    )


def test_tier3_snapshot_shows_the_whole_derivation() -> None:
    trace: Trace = run_rule(HEADROOM_RULE, _overdraw_world())
    card = Card(trace)
    assert card.tier3 == expected_tier3(game_pin())


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
    return _offered(balance)


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
    undecided = [
        (s.subject, s.reason) for s in trace.steps if s.kind is StepKind.VERDICT_INDETERMINATE
    ]
    assert missing == []
    assert trace.recommendation is None
    assert undecided == [
        (
            "compare the draw against generation",
            "some built generators have no modelled output, so the capacity is a floor"
            " and not a measurement",
        )
    ]


# CS-1271 refutation: a reject made only because an input is incomplete is NOT a
# verdict, so settled_rules must not count it and the ledger may not complete an
# earlier "Add N MW" card on it. A definite reject over complete inputs still is.


def _headroom_trace(
    *,
    lower: Fraction,
    upper: Fraction,
    capacity: Fraction | None,
    production_complete: bool = True,
    draw_complete: bool = True,
    unread: int = 0,
    build: BuildInputs | None = None,
) -> Trace:
    """Run the headroom rule over one balance carrying an optional production model."""
    base = _balance(
        lower=lower,
        upper=upper,
        exact=lower == upper,
        complete=draw_complete,
        unread=unread,
        production=capacity is not None,
    )
    if capacity is not None:
        base = replace(base, production=_production(capacity, complete=production_complete))
    return run_rule(HEADROOM_RULE, _offered(base, build))


def test_an_incomplete_production_reject_is_not_settled() -> None:
    trace = _headroom_trace(
        lower=Fraction(500), upper=Fraction(500), capacity=Fraction(75), production_complete=False
    )

    silent = trace.recommendation is None
    settled = HEADROOM_RULE.rule_id in settled_rules((trace,))
    assert silent
    assert not settled, "a floor of generation settled the headroom rule"


def test_an_incomplete_draw_reject_is_not_settled() -> None:
    trace = _headroom_trace(
        lower=Fraction(500),
        upper=Fraction(500),
        capacity=Fraction(75),
        draw_complete=False,
        unread=1,
    )

    silent = trace.recommendation is None
    settled = HEADROOM_RULE.rule_id in settled_rules((trace,))
    assert silent
    assert not settled, "a floor of draw settled the headroom rule"


def test_an_unmodelled_generation_reject_is_not_settled() -> None:
    trace = _headroom_trace(lower=Fraction(500), upper=Fraction(500), capacity=None)

    silent = trace.recommendation is None
    settled = HEADROOM_RULE.rule_id in settled_rules((trace,))
    assert silent
    assert not settled, "an absent generation figure settled the headroom rule"


def test_a_definite_reject_over_complete_inputs_is_still_settled() -> None:
    """Anti-vacuity control: covered generation is a verdict and settles the rule."""
    trace = _headroom_trace(lower=Fraction(120), upper=Fraction(130), capacity=Fraction(200))

    silent = trace.recommendation is None
    settled = HEADROOM_RULE.rule_id in settled_rules((trace,))
    assert silent
    assert settled


# CS-1288: every power card states an off-pin build (the session 138 rulings
# F1, F5 and F7). Every figure these rules state is priced from a registry
# nameplate - the clocked draw and the generation capacity both - so a save
# written by another build is priced at the pinned build's nameplate. Off the
# pin, tier 2 says so and names both builds, tier 1 and every computed figure
# stay exactly the on-pin run's, and the run - firing or silent - records one
# indeterminate step right after the three build reads, so it never settles
# its rule and the ledger never completes a card on it.

#: The alternative an off-pin run records as indeterminate, spelled here
#: independently of ``clockspeed/advisor/build.py``.
NAMEPLATE_ALTERNATIVE = "present a nameplate figure as the save build's own"


def _mismatch(pin: int) -> str:
    """The tier 2 suffix of a save written by the build after the pin."""
    return (
        f"; {WARN_BUILD_MISMATCH}: priced at the pinned build {pin}, not the save build {pin + 1}"
    )


def _detail(save: int, pin: int | None) -> str:
    """The audit's own fixed detail line for the one warning a check raises."""
    warnings = build_check(save, pin).warnings
    count = len(warnings)
    assert count == 1
    return warnings[0].detail


def _computed_steps(trace: Trace) -> list[tuple[str, object]]:
    return [(s.subject, s.value) for s in trace.steps if s.kind is StepKind.COMPUTED]


#: One world per ``Recommendation`` return site in ``power.py``, with the
#: headline words only that site writes, so each row provably reaches its own.
POWER_SITES: dict[str, tuple[RuleSpec, Callable[[BuildInputs], WorldInputs], str]] = {
    "headroom-brownout": (
        HEADROOM_RULE,
        lambda build: _world(
            _balance(lower=Fraction(90), upper=Fraction(110), exact=False), Fraction(100), build
        ),
        "Add up to 10.00 MW",
    ),
    "headroom-exact": (
        HEADROOM_RULE,
        lambda build: _world(
            _balance(lower=Fraction(120), upper=Fraction(120), exact=True), Fraction(100), build
        ),
        "Add 20.00 MW",
    ),
    "headroom-bracket": (
        HEADROOM_RULE,
        lambda build: _world(
            _balance(lower=Fraction(120), upper=Fraction(130), exact=False), Fraction(100), build
        ),
        "Add between 20.00 and 30.00 MW",
    ),
    "draw-incomplete": (
        GAP_RULE,
        lambda build: _world(
            _balance(
                lower=Fraction(120),
                upper=Fraction(130),
                exact=False,
                complete=False,
                unread=2,
                unmodeled=1,
            ),
            Fraction(100),
            build,
        ),
        "Resolve 3 unpriced machines",
    ),
}

#: One world per power rule in which it declines over complete inputs - a
#: definite verdict on the pin.
POWER_SILENT: dict[str, tuple[RuleSpec, Callable[[BuildInputs], WorldInputs]]] = {
    "headroom-covered": (
        HEADROOM_RULE,
        lambda build: _world(
            _balance(lower=Fraction(80), upper=Fraction(90), exact=False), Fraction(100), build
        ),
    ),
    "draw-complete": (
        GAP_RULE,
        lambda build: _world(
            _balance(lower=Fraction(120), upper=Fraction(130), exact=False), Fraction(100), build
        ),
    ),
}


@pytest.mark.parametrize("spec", RULES, ids=lambda spec: spec.rule_id)
def test_every_power_rule_declares_the_build_inputs_first(spec: RuleSpec) -> None:
    leading = spec.inputs[: len(BUILD_INPUTS)]
    assert leading == BUILD_INPUTS
    repeated = len(spec.inputs) != len(set(spec.inputs))
    assert not repeated


@pytest.mark.parametrize("site", sorted(POWER_SITES))
def test_an_off_pin_card_names_both_builds_and_moves_nothing_else(site: str) -> None:
    pin = game_pin()
    spec, make, headline = POWER_SITES[site]
    on = run_rule(spec, make(pinned_build_inputs(pin)))
    off = run_rule(spec, make(off_pin_build_inputs(pin)))
    on_card = card_for(on)
    off_card = card_for(off)
    assert on_card is not None
    assert off_card is not None

    assert on_card.tier1.startswith(headline)
    assert "build-" not in on_card.tier2
    assert off_card.tier1 == on_card.tier1
    assert off_card.tier2 == on_card.tier2 + _mismatch(pin)
    assert off_card.id == on_card.id
    assert _computed_steps(off) == _computed_steps(on)
    assert spec.rule_id in settled_rules((on,))
    assert spec.rule_id not in settled_rules((off,))


@pytest.mark.parametrize("site", sorted(POWER_SITES))
def test_the_off_pin_indeterminate_step_follows_the_three_build_reads(site: str) -> None:
    pin = game_pin()
    spec, make, _headline = POWER_SITES[site]
    trace = run_rule(spec, make(off_pin_build_inputs(pin)))

    kinds = [s.kind for s in trace.steps[:4]]
    assert kinds == [*[StepKind.INPUT_READ] * 3, StepKind.VERDICT_INDETERMINATE]
    assert tuple(s.subject for s in trace.steps[:3]) == BUILD_INPUTS
    build_steps = [
        (s.subject, s.reason)
        for s in trace.steps
        if s.kind is StepKind.VERDICT_INDETERMINATE and s.subject == NAMEPLATE_ALTERNATIVE
    ]
    assert build_steps == [(NAMEPLATE_ALTERNATIVE, _detail(pin + 1, pin))]


@pytest.mark.parametrize("site", sorted(POWER_SILENT))
def test_an_off_pin_silent_rule_is_not_settled(site: str) -> None:
    pin = game_pin()
    spec, make = POWER_SILENT[site]
    on = run_rule(spec, make(pinned_build_inputs(pin)))
    off = run_rule(spec, make(off_pin_build_inputs(pin)))

    assert on.recommendation is None
    assert off.recommendation is None
    rejected_on = [s.subject for s in on.steps if s.kind is StepKind.ALTERNATIVE_REJECTED]
    rejected_off = [s.subject for s in off.steps if s.kind is StepKind.ALTERNATIVE_REJECTED]
    assert rejected_off == rejected_on
    assert rejected_on != []
    assert spec.rule_id in settled_rules((on,))
    assert spec.rule_id not in settled_rules((off,))


def test_an_off_pin_silent_headroom_over_a_floor_records_both_reasons() -> None:
    """The draw floor's own indeterminate step survives beside the build's."""
    pin = game_pin()
    trace = _headroom_trace(
        lower=Fraction(500),
        upper=Fraction(500),
        capacity=Fraction(75),
        draw_complete=False,
        unread=1,
        build=off_pin_build_inputs(pin),
    )

    undecided = [s.subject for s in trace.steps if s.kind is StepKind.VERDICT_INDETERMINATE]
    assert trace.recommendation is None
    assert undecided == [NAMEPLATE_ALTERNATIVE, "compare the draw against generation"]
    assert HEADROOM_RULE.rule_id not in settled_rules((trace,))


@pytest.mark.parametrize("site", sorted(POWER_SITES))
def test_with_no_pin_a_card_names_the_uncompared_build_never_a_mismatch(site: str) -> None:
    pin = game_pin()
    spec, make, _headline = POWER_SITES[site]
    on_card = card_for(run_rule(spec, make(pinned_build_inputs(pin))))
    trace = run_rule(spec, make(uncompared_build_inputs(pin)))
    card = card_for(trace)
    assert on_card is not None
    assert card is not None

    expected = (
        f"; {WARN_BUILD_UNCOMPARED}: the save build {pin} was never compared,"
        " as no pinned build exists"
    )
    assert card.tier2 == on_card.tier2 + expected
    assert WARN_BUILD_MISMATCH not in card.tier2
    assert spec.rule_id not in settled_rules((trace,))


def test_an_off_pin_tier3_shows_both_builds_and_the_indeterminate_step() -> None:
    pin = game_pin()
    on = Card(run_rule(HEADROOM_RULE, _overdraw_world()))
    off_world = _world(
        _balance(lower=Fraction(120), upper=Fraction(130), exact=False),
        Fraction(100),
        off_pin_build_inputs(pin),
    )
    lines = Card(run_rule(HEADROOM_RULE, off_world)).tier3.splitlines()

    save_line = f"  1. Read build.save_changelist = {pin + 1} from audit.build.save_changelist"
    pin_line = f"  2. Read build.pinned_changelist = {pin} from audit.build.pinned_changelist"
    assert len(lines) == len(on.tier3.splitlines()) + 1
    assert lines[2] == f"Because: {on.tier2}{_mismatch(pin)}"
    assert lines[5] == save_line
    assert lines[6] == pin_line
    assert lines[7].startswith(f'  3. Read build.warnings = {{"{WARN_BUILD_MISMATCH}": ')
    assert lines[7].endswith(" from audit.build.warnings")
    assert lines[8] == f"  4. Indeterminate {NAMEPLATE_ALTERNATIVE}: {_detail(pin + 1, pin)}"
