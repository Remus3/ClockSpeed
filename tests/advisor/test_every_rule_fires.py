"""CS-500 slice S5: every registered advisor rule proves it can fire and stay silent.

THE CLAIM (CS-500 acceptance clause A1, and the advisor-rule half of CS-1238).
For every rule id :func:`clockspeed.advisor.rules.registered_rules` returns,
this module holds TWO minimal synthetic worlds: one in which the rule fires,
and one in which it declines for a reason it records. A rule no fixture can
fire is advice nobody has seen given; a rule no fixture can silence is advice
nobody has seen withheld. Either is indistinguishable from a rule wired to
nothing - the silently-wrong half of non-negotiable 7, one layer up.

THE RULE SET IS DERIVED, NEVER LISTED. The ids come from the registry itself,
so a rule family added to ``_FAMILIES`` reddens
:func:`test_every_registered_rule_has_a_firing_fixture` and
:func:`test_every_registered_rule_has_a_silent_fixture` by name until a fixture
here covers it. The two tables below are hand-written because they must be - a
fixture is fixture code - and those arms are what grade them.

ONE RULE, ONE TEST ID PER TABLE. The firing and silent arms are parametrised
over their table with the rule id as the test id, so a fixture that stops
firing, or stops being silent, reddens exactly the test naming its rule.

REMOVING A FIXTURE REDDENS EXACTLY ONE NAME. :func:`test_dropping_any_one_fixture_is_named_alone`
drops each entry of each table in turn and asserts the completeness predicate
names that rule id and nothing else.

WHAT "FIRES" MEANS HERE, AND WHAT "SILENT" MEANS. A firing trace carries a
recommendation, ends in its one ``rule-fired`` step, reads EVERY input the rule
declares, and carries no refused, missing, unmet or rule-error step. A silent
trace carries no recommendation for a LEGITIMATE reason: it records at least
one rejected alternative and no refused, missing, unmet or rule-error step - a
rule that went quiet because it crashed or was starved of input is a fault,
not silence.

TIER 3 IS GENERATED FROM THE TRACE, PER RULE. Every firing fixture's card has
exactly one numbered derivation line per trace step and renders identically on
a second run of the same world. And EACH LINE IS GENERATED FROM ITS OWN STEP'S
CONTENT: :func:`test_each_tier3_line_carries_its_own_steps_content` replaces,
one at a time, every field a step carries - subject, source, value, reason -
with a fresh marker in the TRACE (never in the rule), and asserts that exactly
that step's line changes and now carries the marker. A former arm that only
dropped a step was vacuous: with the line count pinned, any drop changes the
text, so a ``_step_line`` returning a constant or only the step kind survived
it (adversary mutants M7 and M8, CS-500 S5 repair).

EVERY WORLD IS SYNTHETIC. Each is a :class:`clockspeed.advisor.trace.WorldInputs`
built by hand from invented exact values under ``synthetic.`` sources; nothing
here reads a save, a docs file or a game install. Generated power is supplied
directly because no audit model publishes it yet (CS-1059). The fuel family's
worlds (CS-1285) are one invented burner class burning one invented liquid,
every figure the rules recompute worked by hand in :func:`_fuel` so the
recomputation agrees with it; a fixture that disagreed would end in a
``rule-error``, which the firing and silent arms both refuse.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Iterable, Mapping
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Final

import pytest

from clockspeed.advisor.cards import Card, card_for
from clockspeed.advisor.rules import fuel, power, registered_rules
from clockspeed.advisor.trace import (
    InputValue,
    RuleSpec,
    StepKind,
    Trace,
    TraceStep,
    WorldInputs,
    run_rule,
)
from clockspeed.audit.fuel import (
    REASON_FLOW_INCOMPLETE,
    UNIT_CUBIC_METRE,
    VERDICT_FIRE,
    VERDICT_INDETERMINATE,
    VERDICT_REJECT,
)

#: One zero-argument builder per rule id: the synthetic world to run it on.
WorldBuilder = Callable[[], WorldInputs]

#: Step kinds that mark a fault, never a legitimate firing or a legitimate silence.
_FAULT_KINDS: Final = frozenset(
    {
        StepKind.INPUT_REFUSED,
        StepKind.INPUT_MISSING,
        StepKind.PRECONDITION_UNMET,
        StepKind.RULE_ERROR,
    }
)

#: The line that opens the numbered derivation in tier 3.
_STEPS_HEADER: Final = "Steps:"

#: Markers planted into one trace field at a time. Each is absent from every
#: fixture's tier 3 before the plant - asserted, never assumed.
_TEXT_MARKER: Final = "zqplantedmarker"
_VALUE_MARKER: Final = 918273645


def _world(values: Mapping[str, object], unlocks: Iterable[str] = ()) -> WorldInputs:
    """Wrap invented values as a world, each under a ``synthetic.`` source."""
    offered = {name: InputValue(value, "synthetic." + name) for name, value in values.items()}
    return WorldInputs(values=offered, unlocks=frozenset(unlocks))


def _power(
    *,
    complete: bool,
    lower: Fraction,
    upper: Fraction,
    exact: bool,
    generation: Fraction,
    considered: int = 10,
    unread: int = 0,
    unmodeled: int = 0,
) -> WorldInputs:
    """One synthetic power world offering every input the D4 family declares."""
    return _world(
        {
            power.IN_COMPLETE: complete,
            power.IN_EXACT: exact,
            power.IN_LOWER: lower,
            power.IN_UPPER: upper,
            power.IN_CONSIDERED: considered,
            power.IN_UNREAD: unread,
            power.IN_UNMODELED: unmodeled,
            power.IN_ELIDED: 0,
            power.IN_OMITTED: 0,
            power.IN_PRODUCTION_AVAILABLE: True,
            power.IN_PRODUCTION_COMPLETE: True,
            power.IN_GENERATION: generation,
        }
    )


#: The invented burner class and liquid fuel every fuel world names.
_BURNER: Final = "Build_SyntheticBurnerQx91_C"
_OIL: Final = "Desc_SyntheticOilQx91_C"

#: The liquid's energy per cubic metre, so one cubic metre a minute is 10 MW.
_OIL_MJ_PER_M3: Final = Fraction(600)

#: The fixed line the fixtures hand the rules for an indeterminate reason.
_UNDECIDED_LINE: Final = "synthetic: the flow is incomplete"

#: The out-of-scope lines the fixtures hand the rules.
_OUT_OF_SCOPE: Final = ("synthetic: supplemental water", "synthetic: byproducts")


def _fuel(
    *,
    verdict: str,
    supply: Fraction,
    shortfall: Fraction | None = None,
    reasons: tuple[str, ...] = (),
) -> WorldInputs:
    """One synthetic fuel world: one burner class of two at clock one, one liquid.

    Worked by hand: the demand is 2 x 100 MW = 200 MW, so the burn is
    200 x 60 / 600 = 20 m3 a minute; a supply of ``s`` m3 a minute yields
    ``s`` x 600 / 60 = 10 ``s`` MW, which is also the pool. A shortfall of
    ``d`` MW is ``d`` x 60 / 600 = ``d`` / 10 m3 of the liquid alone.
    """

    def one(value: object) -> MappingProxyType[str, object]:
        return MappingProxyType({_BURNER: value})

    def per_fuel(value: object) -> MappingProxyType[str, object]:
        return one(MappingProxyType({_OIL: value}))

    rate = None if shortfall is None else shortfall / 10
    return _world(
        {
            fuel.IN_CLASSES: (_BURNER,),
            fuel.IN_VERDICTS: one(verdict),
            fuel.IN_REASONS: one(reasons),
            fuel.IN_DEMAND_REASONS: one(()),
            fuel.IN_REASON_DETAILS: MappingProxyType(dict.fromkeys(reasons, _UNDECIDED_LINE)),
            fuel.IN_INSTANCES: one(2),
            fuel.IN_ELIDED: one(0),
            fuel.IN_NAMEPLATE: one(Fraction(100)),
            fuel.IN_CLOCK_SUM: one(Fraction(2)),
            fuel.IN_DEMAND: one(Fraction(200)),
            fuel.IN_FUELS: one((_OIL,)),
            fuel.IN_MJ: MappingProxyType({_OIL: _OIL_MJ_PER_M3}),
            fuel.IN_UNITS: MappingProxyType({_OIL: UNIT_CUBIC_METRE}),
            fuel.IN_SUPPLY: per_fuel(supply),
            fuel.IN_SUPPLY_MW: per_fuel(supply * 10),
            fuel.IN_POOLED: one(supply * 10),
            fuel.IN_SHORTFALL: one(shortfall),
            fuel.IN_SHORTFALL_RATES: per_fuel(rate),
            fuel.IN_BURNS: per_fuel(Fraction(20)),
            fuel.IN_EXCLUSIONS: _OUT_OF_SCOPE,
            fuel.IN_CLASS_NAMES: one("Synthetic Burner"),
            fuel.IN_FUEL_NAMES: MappingProxyType({_OIL: "Synthetic Oil"}),
        }
    )


def _fuel_short() -> WorldInputs:
    """Ten m3 a minute is 100 MW against a 200 MW demand: 100 MW short over a complete flow."""
    return _fuel(verdict=VERDICT_FIRE, supply=Fraction(10), shortfall=Fraction(100))


def _fuel_covered() -> WorldInputs:
    """Thirty m3 a minute is 300 MW, covering the 200 MW demand over a complete flow."""
    return _fuel(verdict=VERDICT_REJECT, supply=Fraction(30))


def _fuel_undecided() -> WorldInputs:
    """An incomplete flow: the 100 MW supply is a floor, so no supply verdict is drawn."""
    return _fuel(
        verdict=VERDICT_INDETERMINATE, supply=Fraction(10), reasons=(REASON_FLOW_INCOMPLETE,)
    )


#: A world in which each registered rule FIRES.
FIRING: Final[dict[str, WorldBuilder]] = {
    # The burner's supply has no verdict, so its 20 m3 a minute burn is stated.
    fuel.DEMAND_RULE.rule_id: _fuel_undecided,
    # The burner is 100 MW short: 10 m3 a minute of the liquid alone.
    fuel.SUPPLY_RULE.rule_id: _fuel_short,
    # Three unpriced machines out of ten: the draw is a floor.
    power.GAP_RULE.rule_id: lambda: _power(
        complete=False,
        lower=Fraction(50),
        upper=Fraction(60),
        exact=False,
        generation=Fraction(100),
        unread=2,
        unmodeled=1,
    ),
    # An exact clocked draw of 120 MW against 100 MW of generation.
    power.HEADROOM_RULE.rule_id: lambda: _power(
        complete=True,
        lower=Fraction(120),
        upper=Fraction(120),
        exact=True,
        generation=Fraction(100),
    ),
}

#: A world in which each registered rule DECLINES for a reason it records.
SILENT: Final[dict[str, WorldBuilder]] = {
    # The supply rule decides the burner (it fires), so no burn is stated.
    fuel.DEMAND_RULE.rule_id: _fuel_short,
    # The pooled supply covers the demand over a complete flow.
    fuel.SUPPLY_RULE.rule_id: _fuel_covered,
    # Every considered machine is priced, so there is no gap to name.
    power.GAP_RULE.rule_id: lambda: _power(
        complete=True,
        lower=Fraction(50),
        upper=Fraction(60),
        exact=False,
        generation=Fraction(100),
    ),
    # Generation of 200 MW covers the whole 120 to 150 MW clocked bracket.
    power.HEADROOM_RULE.rule_id: lambda: _power(
        complete=True,
        lower=Fraction(120),
        upper=Fraction(150),
        exact=False,
        generation=Fraction(200),
    ),
}


def _registry_ids() -> list[str]:
    return [spec.rule_id for spec in registered_rules()]


def _spec(rule_id: str) -> RuleSpec:
    matches = [spec for spec in registered_rules() if spec.rule_id == rule_id]
    count = len(matches)
    assert count == 1, rule_id
    return matches[0]


def uncovered(table: Iterable[str], derived: Iterable[str]) -> list[str]:
    """The registered rule ids the table holds no fixture for, sorted."""
    return sorted(set(derived) - set(table))


def orphaned(table: Iterable[str], derived: Iterable[str]) -> list[str]:
    """The table's rule ids the registry no longer carries, sorted."""
    return sorted(set(table) - set(derived))


def _fault_count(trace: Trace) -> int:
    return sum(1 for step in trace.steps if step.kind in _FAULT_KINDS)


def _derivation_lines(card: Card) -> list[str]:
    """The numbered step lines of a card's tier 3, after the steps header."""
    lines = card.tier3.split("\n")
    return lines[lines.index(_STEPS_HEADER) + 1 :]


def test_the_registry_is_not_vacuous() -> None:
    ids = _registry_ids()
    count = len(ids)
    assert count > 1, "a registry of fewer than two rules makes the drop arm grade nothing"


def test_every_registered_rule_has_a_firing_fixture() -> None:
    missing = uncovered(FIRING, _registry_ids())
    assert missing == [], "no firing fixture: " + ", ".join(missing)


def test_every_registered_rule_has_a_silent_fixture() -> None:
    missing = uncovered(SILENT, _registry_ids())
    assert missing == [], "no silent fixture: " + ", ".join(missing)


def test_every_fixture_names_a_registered_rule() -> None:
    stale = orphaned(FIRING, _registry_ids()) + orphaned(SILENT, _registry_ids())
    assert stale == [], "fixture for a rule the registry does not carry: " + ", ".join(stale)


@pytest.mark.parametrize("table_name", ["FIRING", "SILENT"])
def test_dropping_any_one_fixture_is_named_alone(table_name: str) -> None:
    """Each drop adds exactly its own rule id to what the completeness arm reports.

    RELATIVE TO THE TABLE AS IT STANDS, so a real gap reddens the completeness
    arm alone and never this one beside it.

    THE ANTI-VACUITY GUARD GRADES THE FULL REGISTERED SET, NEVER THE TABLE. A
    guard on the table's own size reddened here too whenever one fixture of a
    two-rule registry was dropped - a second failure that did not name the
    rule. The registry is what the drop is measured against, so its size is
    what must exceed one.
    """
    table = FIRING if table_name == "FIRING" else SILENT
    derived = _registry_ids()
    baseline = uncovered(table, derived)
    stale = orphaned(table, derived)
    registered = len(derived)
    assert registered > 1, "a drop over a one-rule registry proves nothing about the others"
    for name in sorted(set(table) & set(derived)):
        remaining = [other for other in table if other != name]
        assert uncovered(remaining, derived) == sorted({*baseline, name}), name
        assert orphaned(remaining, derived) == stale, name


@pytest.mark.parametrize("rule_id", sorted(FIRING), ids=sorted(FIRING))
def test_the_firing_fixture_fires_its_rule(rule_id: str) -> None:
    spec = _spec(rule_id)
    trace = run_rule(spec, FIRING[rule_id]())
    fired = trace.recommendation is not None
    assert fired, f"{rule_id} did not fire on its firing fixture"
    faults = _fault_count(trace)
    assert faults == 0, f"{rule_id} fired through {faults} fault steps"
    last_is_fired = trace.steps[-1].kind is StepKind.RULE_FIRED
    assert last_is_fired, rule_id
    read = sorted({step.subject for step in trace.steps if step.kind is StepKind.INPUT_READ})
    unread = sorted(set(spec.inputs) - set(read))
    assert unread == [], f"{rule_id} fired without reading: " + ", ".join(unread)


@pytest.mark.parametrize("rule_id", sorted(SILENT), ids=sorted(SILENT))
def test_the_silent_fixture_keeps_its_rule_silent(rule_id: str) -> None:
    trace = run_rule(_spec(rule_id), SILENT[rule_id]())
    silent = trace.recommendation is None and card_for(trace) is None
    assert silent, f"{rule_id} recommended on its silent fixture"
    faults = _fault_count(trace)
    assert faults == 0, f"{rule_id} went silent through {faults} fault steps, not a decision"
    rejected = sum(1 for step in trace.steps if step.kind is StepKind.ALTERNATIVE_REJECTED)
    assert rejected > 0, f"{rule_id} went silent without recording why"


@pytest.mark.parametrize("rule_id", sorted(FIRING), ids=sorted(FIRING))
def test_tier3_of_the_firing_card_is_generated_from_its_trace(rule_id: str) -> None:
    spec = _spec(rule_id)
    trace = run_rule(spec, FIRING[rule_id]())
    card = card_for(trace)
    built = card is not None
    assert built, rule_id
    assert card is not None
    lines = len(_derivation_lines(card))
    steps = len(trace.steps)
    assert lines == steps, f"{rule_id}: {lines} derivation lines for {steps} steps"
    again = card_for(run_rule(spec, FIRING[rule_id]()))
    same = again is not None and again.tier3 == card.tier3
    assert same, f"{rule_id}: two runs on one world rendered different derivations"


def _carried_fields(step: TraceStep) -> list[str]:
    """The fields this step actually carries - the ones its line must render."""
    carried = ["subject"]
    if step.source:
        carried.append("source")
    if step.value is not None:
        carried.append("value")
    if step.reason:
        carried.append("reason")
    return carried


def _planted(trace: Trace, index: int, field: str) -> Card:
    """The card of ``trace`` with one field of step ``index`` replaced by a marker.

    The rule-fired step's subject must equal the recommendation's subject key
    or the card refuses the trace, so that plant moves both together; the
    subject key renders nowhere else in tier 3.
    """
    marker: object = _VALUE_MARKER if field == "value" else _TEXT_MARKER
    step = trace.steps[index]
    steps = list(trace.steps)
    change: dict[str, Any] = {field: marker}
    steps[index] = dataclasses.replace(step, **change)
    recommendation = trace.recommendation
    if step.kind is StepKind.RULE_FIRED and field == "subject" and recommendation is not None:
        recommendation = dataclasses.replace(recommendation, subject_key=_TEXT_MARKER)
    return Card(Trace(trace.rule_id, trace.domain, tuple(steps), recommendation))


@pytest.mark.parametrize("rule_id", sorted(FIRING), ids=sorted(FIRING))
def test_each_tier3_line_carries_its_own_steps_content(rule_id: str) -> None:
    """Planting a marker in one step field changes that step's line and no other."""
    trace = run_rule(_spec(rule_id), FIRING[rule_id]())
    card = card_for(trace)
    assert card is not None, rule_id
    before = card.tier3.split("\n")
    marker_texts = (_TEXT_MARKER, str(_VALUE_MARKER))
    clean = not any(marker in card.tier3 for marker in marker_texts)
    assert clean, f"{rule_id}: a marker already appears in the unplanted tier 3"
    offset = before.index(_STEPS_HEADER) + 1
    plants = 0
    for index, step in enumerate(trace.steps):
        for field in _carried_fields(step):
            after = _planted(trace, index, field).tier3.split("\n")
            same_length = len(after) == len(before)
            assert same_length, f"{rule_id}: step {index} {field} changed the line count"
            pairs = enumerate(zip(before, after, strict=True))
            changed = [n for n, (old, new) in pairs if old != new]
            expected = [offset + index]
            assert changed == expected, f"{rule_id}: step {index} {field} moved other lines"
            marker = str(_VALUE_MARKER) if field == "value" else _TEXT_MARKER
            carried = marker in after[offset + index]
            assert carried, f"{rule_id}: step {index} line does not render its {field}"
            plants += 1
    steps = len(trace.steps)
    assert plants > steps, f"{rule_id}: {plants} plants over {steps} steps grades only subjects"
