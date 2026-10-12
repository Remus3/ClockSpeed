"""CS-1288 slice C0: the build inputs, and the build caveat every priced rule reads.

THE CLAIM. :func:`clockspeed.advisor.build.build_inputs` offers the audit's
``BuildCheck`` as exactly the three inputs
:data:`clockspeed.advisor.build.BUILD_INPUTS`, each sourced to its audit field,
and :func:`clockspeed.advisor.build.build_caveat` reads all three FIRST, then:

- on the pin, returns nothing and records nothing else, so a rule settles as it
  did before;
- off the pin, records ONE verdict-indeterminate step carrying the audit's
  fixed detail and returns a reason suffix naming ``build-mismatch``, the pin
  and the save build - the card still fires, and the rule never settles;
- with no pin, takes the same path under ``build-uncompared``, naming the save
  build and that no pin exists, and NEVER the mismatch wording;
- and raises - a ``rule-error``, no card - on any disagreement between the
  codes and the builds, or a value of the wrong exact type.

A PROBE RULE, NOT A SHIPPED ONE. Every registered rule reads the build inputs
first since CS-1288 slice C1-C3, and each rule family's own tests and
``tests/advisor/test_every_rule_fires.py`` grade that. The arms here grade the
caveat itself, apart from any rule's own figures, so every one runs a probe
defined here through an explicit rule tuple. The settlement arms run
:func:`clockspeed.advisor.advise.advise` with ``rules=`` and grade
:func:`clockspeed.advisor.advise.settled_rules`.

THE PIN IS READ AT TEST TIME, NEVER TYPED (the session 134 ruling): every
changelist here is :func:`tests.advisor.build_fixtures.game_pin` or the pin
plus or minus one, and every off-pin arm runs on both sides of the pin
(:data:`tests.advisor.build_fixtures.OFF_PIN_OFFSETS`, CS-1288 fix round 1).
The world token is an invented 22-character literal.
"""

from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor import build as advisor_build
from clockspeed.advisor.advise import advise, settled_rules
from clockspeed.advisor.build import BUILD_INPUTS, build_caveat, build_inputs
from clockspeed.advisor.cards import card_for
from clockspeed.advisor.ledger import Ledger, MuteStore
from clockspeed.advisor.rules import fuel, power
from clockspeed.advisor.rules.fuel import fuel_inputs
from clockspeed.advisor.trace import (
    NAME_PATTERN,
    InputValue,
    Recommendation,
    RuleContext,
    RuleSpec,
    StepKind,
    Trace,
    WorldInputs,
    run_rule,
)
from clockspeed.audit.balance import balance_of
from clockspeed.audit.build import WARN_BUILD_MISMATCH, WARN_BUILD_UNCOMPARED
from clockspeed.audit.fuel import fuel_supply_of
from clockspeed.audit.machines import machines_of
from clockspeed.audit.network import network_of
from clockspeed.audit.placement import placement_of
from clockspeed.data import version
from clockspeed.data.registry import Registry
from tests.advisor.build_fixtures import (
    OFF_PIN_OFFSETS,
    build_check,
    game_pin,
    off_pin_build_inputs,
    pinned_build_inputs,
    synthetic_world,
    uncompared_build_inputs,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from clockspeed.advisor.advise import Advice

# An invented 22-character base64url literal. Never a real world token.
TOKEN: Final = "BBBBsyntheticBuildBBBB"  # noqa: S105 - a synthetic world token, not a secret
NOW: Final = 1000

PROBE_ID: Final = "synthetic.build_probe"
PROBE_SUBJECT: Final = "synthetic:build-probe"
BASE_REASON: Final = "a synthetic binding constraint"

#: The alternative the caveat records as indeterminate off the pin.
NAMEPLATE_ALTERNATIVE: Final = "present a nameplate figure as the save build's own"

#: The three input names, spelled here independently of the module under test.
SAVE_IN: Final = "build.save_changelist"
PINNED_IN: Final = "build.pinned_changelist"
WARNINGS_IN: Final = "build.warnings"
NAMES: Final = (SAVE_IN, PINNED_IN, WARNINGS_IN)


def _probe(*, fires: bool = True, inputs: tuple[str, ...] = NAMES) -> RuleSpec:
    """A rule that reads the caveat first, then fires or stays silent."""

    def _evaluate(ctx: RuleContext) -> Recommendation | None:
        caveat = build_caveat(ctx)
        if not fires:
            return None
        return Recommendation(
            subject_key=PROBE_SUBJECT,
            action="Do the synthetic thing",
            reason=BASE_REASON + caveat,
        )

    return RuleSpec(
        rule_id=PROBE_ID, domain="synthetic", inputs=inputs, unlocks=(), evaluate=_evaluate
    )


def _world(values: dict[str, InputValue]) -> WorldInputs:
    return WorldInputs(values=values, unlocks=frozenset())


def _advise(directory: Path, values: dict[str, InputValue], *, fires: bool = True) -> Advice:
    return advise(
        TOKEN,
        _world(values),
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=NOW,
        rules=(_probe(fires=fires),),
    )


def _kinds(trace: Trace) -> list[StepKind]:
    return [step.kind for step in trace.steps]


def _indeterminate(trace: Trace) -> list[tuple[str, str]]:
    return [
        (step.subject, step.reason)
        for step in trace.steps
        if step.kind is StepKind.VERDICT_INDETERMINATE
    ]


def _only_trace(advice: Advice) -> Trace:
    count = len(advice.traces)
    assert count == 1
    return advice.traces[0]


def _only_tier2(advice: Advice) -> str:
    count = len(advice.cards)
    assert count == 1
    return advice.cards[0].card.tier2


def _detail(save: int, pin: int | None) -> str:
    """The audit's own fixed detail line for the one warning a check raises."""
    warnings = build_check(save, pin).warnings
    count = len(warnings)
    assert count == 1
    return warnings[0].detail


# --- the adapter ---------------------------------------------------------------


def test_the_build_input_names_are_pinned_and_pass_the_engine_name_pattern() -> None:
    assert BUILD_INPUTS == NAMES
    assert all(NAME_PATTERN.fullmatch(name) is not None for name in BUILD_INPUTS)
    spec = _probe(inputs=BUILD_INPUTS)
    assert spec.inputs == NAMES


@pytest.mark.parametrize("state", ["on-pin", "off-pin", "uncompared"])
def test_the_adapter_offers_exactly_the_build_inputs_each_sourced_to_its_audit_field(
    state: str,
) -> None:
    pin = game_pin()
    save, pinned = {"on-pin": (pin, pin), "off-pin": (pin + 1, pin), "uncompared": (pin, None)}[
        state
    ]
    check = build_check(save, pinned)
    offered = build_inputs(check)
    sources = {name: value.source for name, value in offered.items()}
    assert sources == {
        SAVE_IN: "audit.build.save_changelist",
        PINNED_IN: "audit.build.pinned_changelist",
        WARNINGS_IN: "audit.build.warnings",
    }
    assert type(offered[SAVE_IN].value) is int
    assert offered[SAVE_IN].value == check.save_changelist
    assert offered[PINNED_IN].value == check.pinned_changelist
    warnings = offered[WARNINGS_IN].value
    assert type(warnings) is MappingProxyType
    assert dict(warnings) == {w.code: w.detail for w in check.warnings}


def test_the_adapter_returns_a_fresh_dict_each_call() -> None:
    check = build_check(game_pin(), game_pin())
    first = build_inputs(check)
    first.pop(SAVE_IN)
    second = build_inputs(check)
    assert set(second) == set(NAMES)


@pytest.mark.parametrize("state", ["on-pin", "off-pin", "uncompared"])
def test_every_build_input_value_passes_the_exactness_walk(state: str) -> None:
    pin = game_pin()
    values = {
        "on-pin": pinned_build_inputs,
        "off-pin": off_pin_build_inputs,
        "uncompared": uncompared_build_inputs,
    }[state](pin)

    def _read_all(ctx: RuleContext) -> Recommendation | None:
        for name in NAMES:
            ctx.read(name)
        return None

    spec = RuleSpec(
        rule_id=PROBE_ID, domain="synthetic", inputs=NAMES, unlocks=(), evaluate=_read_all
    )
    trace = run_rule(spec, _world(values))
    assert _kinds(trace) == [StepKind.INPUT_READ] * len(NAMES)
    assert trace.refused == ()


# --- the caveat, on the pin ------------------------------------------------------


def test_on_the_pin_the_caveat_adds_nothing_and_the_probe_settles(tmp_path: Path) -> None:
    advice = _advise(tmp_path, pinned_build_inputs(game_pin()))
    trace = _only_trace(advice)
    assert _kinds(trace) == [StepKind.INPUT_READ] * 3 + [StepKind.RULE_FIRED]
    assert _only_tier2(advice) == BASE_REASON
    settled = PROBE_ID in settled_rules(advice.traces)
    assert settled


def test_on_the_pin_a_silent_probe_settles(tmp_path: Path) -> None:
    advice = _advise(tmp_path, pinned_build_inputs(game_pin()), fires=False)
    trace = _only_trace(advice)
    assert _kinds(trace) == [StepKind.INPUT_READ] * 3
    assert advice.cards == ()
    settled = PROBE_ID in settled_rules(advice.traces)
    assert settled


# --- the caveat, off the pin -----------------------------------------------------


def _side(offset: int) -> str:
    """A test id for an offset: the side of the pin the save sits on."""
    return "after" if offset > 0 else "before"


# Every off-pin arm runs on BOTH sides of the pin - the build after it and the
# build before it (CS-1288 fix round 1). A save OLDER than the pin is the
# item's motivating case, and a caveat comparing builds by order rather than by
# equality passes on one side alone.


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
def test_off_the_pin_the_reason_names_the_mismatch_and_both_builds(
    tmp_path: Path, offset: int
) -> None:
    pin = game_pin()
    advice = _advise(tmp_path, off_pin_build_inputs(pin, offset))
    expected = (
        f"{BASE_REASON}; {WARN_BUILD_MISMATCH}: priced at the pinned build {pin},"
        f" not the save build {pin + offset}"
    )
    assert _only_tier2(advice) == expected


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
def test_off_the_pin_one_indeterminate_step_follows_the_three_reads(
    tmp_path: Path, offset: int
) -> None:
    pin = game_pin()
    advice = _advise(tmp_path, off_pin_build_inputs(pin, offset))
    trace = _only_trace(advice)
    assert _kinds(trace) == [
        *[StepKind.INPUT_READ] * 3,
        StepKind.VERDICT_INDETERMINATE,
        StepKind.RULE_FIRED,
    ]
    assert [step.subject for step in trace.steps[:3]] == list(NAMES)
    assert _indeterminate(trace) == [(NAMEPLATE_ALTERNATIVE, _detail(pin + offset, pin))]
    settled = PROBE_ID in settled_rules(advice.traces)
    assert not settled


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
def test_off_the_pin_a_silent_probe_is_not_settled(tmp_path: Path, offset: int) -> None:
    pin = game_pin()
    advice = _advise(tmp_path, off_pin_build_inputs(pin, offset), fires=False)
    trace = _only_trace(advice)
    assert advice.cards == ()
    assert _indeterminate(trace) == [(NAMEPLATE_ALTERNATIVE, _detail(pin + offset, pin))]
    settled = PROBE_ID in settled_rules(advice.traces)
    assert not settled


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
def test_tier_3_shows_each_build_read_with_its_source(tmp_path: Path, offset: int) -> None:
    pin = game_pin()
    advice = _advise(tmp_path, off_pin_build_inputs(pin, offset))
    tier3 = advice.cards[0].card.tier3
    lines = tier3.splitlines()
    second = f"  2. Read {PINNED_IN} = {pin} from audit.build.pinned_changelist"
    assert f"  1. Read {SAVE_IN} = {pin + offset} from audit.build.save_changelist" in lines
    assert second in lines
    third = lines[lines.index(second) + 1]
    assert third.startswith(f'  3. Read {WARNINGS_IN} = {{"{WARN_BUILD_MISMATCH}": ')
    assert third.endswith(" from audit.build.warnings")
    detail = _detail(pin + offset, pin)
    assert f"  4. Indeterminate {NAMEPLATE_ALTERNATIVE}: {detail}" in lines


# --- the caveat, with no pin -----------------------------------------------------


def test_with_no_pin_the_reason_names_build_uncompared_never_the_mismatch(
    tmp_path: Path,
) -> None:
    save = game_pin()
    advice = _advise(tmp_path, uncompared_build_inputs(save))
    tier2 = _only_tier2(advice)
    assert tier2 == (
        f"{BASE_REASON}; {WARN_BUILD_UNCOMPARED}: the save build {save} was never"
        " compared, as no pinned build exists"
    )
    mismatch_named = WARN_BUILD_MISMATCH in tier2 or "priced at the pinned build" in tier2
    assert not mismatch_named


def test_with_no_pin_one_indeterminate_step_carries_the_uncompared_detail(
    tmp_path: Path,
) -> None:
    save = game_pin()
    advice = _advise(tmp_path, uncompared_build_inputs(save))
    trace = _only_trace(advice)
    assert _kinds(trace)[:4] == [*[StepKind.INPUT_READ] * 3, StepKind.VERDICT_INDETERMINATE]
    assert _indeterminate(trace) == [(NAMEPLATE_ALTERNATIVE, _detail(save, None))]
    settled = PROBE_ID in settled_rules(advice.traces)
    assert not settled
    lines = advice.cards[0].card.tier3.splitlines()
    assert f"  2. Read {PINNED_IN} = none from audit.build.pinned_changelist" in lines


def test_with_no_pin_a_silent_probe_is_not_settled(tmp_path: Path) -> None:
    save = game_pin()
    advice = _advise(tmp_path, uncompared_build_inputs(save), fires=False)
    assert advice.cards == ()
    assert _indeterminate(_only_trace(advice)) == [(NAMEPLATE_ALTERNATIVE, _detail(save, None))]
    settled = PROBE_ID in settled_rules(advice.traces)
    assert not settled


# --- forged and disagreeing inputs ----------------------------------------------


def _replaced(values: dict[str, InputValue], name: str, value: object) -> dict[str, InputValue]:
    """The inputs with one value forged, its source kept."""
    forged = dict(values)
    forged[name] = InputValue(value, values[name].source)
    return forged


def _codes(*codes: str) -> MappingProxyType[str, str]:
    return MappingProxyType(dict.fromkeys(codes, "a synthetic detail line"))


#: (id, builder over the pin, the exception type the caveat must raise).
FORGED: Final[tuple[tuple[str, Callable[[int], dict[str, InputValue]], str], ...]] = (
    (
        "mismatch-code-with-equal-builds",
        lambda pin: _replaced(pinned_build_inputs(pin), WARNINGS_IN, _codes(WARN_BUILD_MISMATCH)),
        "ValueError",
    ),
    (
        "no-code-with-unequal-builds",
        lambda pin: _replaced(off_pin_build_inputs(pin), WARNINGS_IN, _codes()),
        "ValueError",
    ),
    (
        "uncompared-code-with-a-pin",
        lambda pin: _replaced(
            off_pin_build_inputs(pin), WARNINGS_IN, _codes(WARN_BUILD_UNCOMPARED)
        ),
        "ValueError",
    ),
    (
        "mismatch-code-with-no-pin",
        lambda pin: _replaced(
            uncompared_build_inputs(pin), WARNINGS_IN, _codes(WARN_BUILD_MISMATCH)
        ),
        "ValueError",
    ),
    (
        "an-extra-code-beside-the-mismatch",
        lambda pin: _replaced(
            off_pin_build_inputs(pin),
            WARNINGS_IN,
            _codes(WARN_BUILD_MISMATCH, WARN_BUILD_UNCOMPARED),
        ),
        "ValueError",
    ),
    (
        "an-unknown-code-on-the-pin",
        lambda pin: _replaced(pinned_build_inputs(pin), WARNINGS_IN, _codes("build-synthetic")),
        "ValueError",
    ),
    (
        "a-bool-for-the-save-build",
        lambda pin: _replaced(off_pin_build_inputs(pin), SAVE_IN, True),
        "TypeError",
    ),
    (
        "a-bool-for-the-pinned-build",
        lambda pin: _replaced(off_pin_build_inputs(pin), PINNED_IN, True),
        "TypeError",
    ),
    (
        "a-fraction-for-the-save-build",
        lambda pin: _replaced(pinned_build_inputs(pin), SAVE_IN, Fraction(pin)),
        "TypeError",
    ),
    (
        "none-for-the-save-build",
        lambda pin: _replaced(uncompared_build_inputs(pin), SAVE_IN, None),
        "TypeError",
    ),
    (
        "a-str-for-the-pinned-build",
        lambda pin: _replaced(off_pin_build_inputs(pin), PINNED_IN, str(pin)),
        "TypeError",
    ),
    (
        "a-tuple-for-the-warnings",
        lambda pin: _replaced(off_pin_build_inputs(pin), WARNINGS_IN, (WARN_BUILD_MISMATCH,)),
        "TypeError",
    ),
    (
        "a-non-str-detail",
        lambda pin: _replaced(
            off_pin_build_inputs(pin), WARNINGS_IN, MappingProxyType({WARN_BUILD_MISMATCH: 7})
        ),
        "TypeError",
    ),
)


@pytest.mark.parametrize(
    ("forge", "raised"),
    [pytest.param(forge, raised, id=case) for case, forge, raised in FORGED],
)
def test_forged_or_disagreeing_build_inputs_are_a_rule_error_with_no_card(
    forge: Callable[[int], dict[str, InputValue]], raised: str
) -> None:
    trace = run_rule(_probe(), _world(forge(game_pin())))
    assert trace.recommendation is None
    assert card_for(trace) is None
    errors = [step.subject for step in trace.steps if step.kind is StepKind.RULE_ERROR]
    assert errors == [raised]
    assert _indeterminate(trace) == []
    assert settled_rules((trace,)) == frozenset()


def test_a_rule_that_does_not_declare_the_build_inputs_cannot_read_them() -> None:
    trace = run_rule(_probe(inputs=()), _world(off_pin_build_inputs(game_pin())))
    assert trace.recommendation is None
    assert trace.refused == (SAVE_IN,)


# --- the seam ----------------------------------------------------------------------


def _declared_names(module: object) -> set[str]:
    """The input-name constants an adapter module declares."""
    return {
        value
        for name, value in vars(module).items()
        if name.startswith("IN_") and type(value) is str
    }


def _offered_names() -> tuple[set[str], set[str]]:
    """The names the balance and fuel adapters actually offer over one synthetic world.

    The world is the build fixtures' empty one and the registry is empty, so
    every name here is one the adapter offers unconditionally.
    """
    model = synthetic_world(game_pin())
    registry = Registry(
        items=MappingProxyType({}),
        recipes=MappingProxyType({}),
        buildings=MappingProxyType({}),
        warnings=(),
        unknown_groups=(),
    )
    machines = machines_of(model)
    balance = balance_of(
        placement_of(model),
        registry.buildings,
        machines,
        network_of(model),
        generators=registry.generators,
    )
    offered_fuel = fuel_inputs(fuel_supply_of(machines, registry), registry)
    return set(power.balance_inputs(balance)), set(offered_fuel)


def test_the_build_inputs_never_collide_with_the_balance_or_fuel_inputs() -> None:
    """The three build names are disjoint from every name the OTHER adapters offer.

    ``clockspeed/advisor/advise.py::inputs_of`` merges the balance, fuel and
    build groups and refuses a shared name, so a collision would take every
    world down. Graded on each other adapter's declared name constants AND on
    the keys it actually offers - never on the registered rules' declared
    inputs, which carry the build names by design since every rule reads them
    first (CS-1288, the session 138 ruling F7 arm 1).
    """
    offered_balance, offered_fuel = _offered_names()
    others = _declared_names(power) | _declared_names(fuel) | offered_balance | offered_fuel
    populated = all(
        bool(names)
        for names in (_declared_names(power), _declared_names(fuel), offered_balance, offered_fuel)
    )
    assert populated
    disjoint = others.isdisjoint(NAMES)
    assert disjoint
    prefixed = any(name.startswith("build.") for name in others)
    assert not prefixed


def test_the_build_module_imports_neither_the_rules_nor_the_pin() -> None:
    source = Path(advisor_build.__file__).read_text(encoding="ascii")
    imported: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported.append(module)
            imported.extend(f"{module}.{alias.name}" for alias in node.names)
    assert "clockspeed.advisor.trace" in imported
    banned = ("clockspeed.advisor.rules", "clockspeed.data")
    reaching = [
        name for name in imported if any(name == b or name.startswith(b + ".") for b in banned)
    ]
    assert reaching == []


def test_the_fixture_pin_is_the_version_pin_read_at_test_time() -> None:
    assert version.GAME_CHANGELIST is not None
    assert game_pin() == version.GAME_CHANGELIST
    pin = game_pin()
    assert pinned_build_inputs(pin)[SAVE_IN].value == pin
    assert off_pin_build_inputs(pin)[SAVE_IN].value == pin + 1
    assert OFF_PIN_OFFSETS == (1, -1)
    for offset in OFF_PIN_OFFSETS:
        assert off_pin_build_inputs(pin, offset)[SAVE_IN].value == pin + offset
    assert pin - 1 > 0
    assert uncompared_build_inputs(pin)[PINNED_IN].value is None
