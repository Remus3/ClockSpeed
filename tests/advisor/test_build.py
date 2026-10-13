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

CS-1315: THE REGISTRY'S SOURCE IS READ BESIDE THE BUILD. The caveat also reads
the three registry inputs :data:`clockspeed.advisor.build.REGISTRY_INPUTS` -
the registry's source hash, the pinned docs hash and the audit's registry
warnings - and cross-checks them the same way: a registry built from other
bytes records ONE more indeterminate step under ``registry-mismatch``, a
registry with no byte source does so under ``registry-unverified``, and a
build-only difference with equal bytes raises no registry code at all. A
disagreement between those codes and the two hashes is a ``rule-error``.

THE PIN IS READ AT TEST TIME, NEVER TYPED (the session 134 ruling): every
changelist here is :func:`tests.advisor.build_fixtures.game_pin` or the pin
plus or minus one, and every off-pin arm runs on both sides of the pin
(:data:`tests.advisor.build_fixtures.OFF_PIN_OFFSETS`, CS-1288 fix round 1).
The world token is an invented 22-character literal.
"""

from __future__ import annotations

import ast
import dataclasses
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.advisor import build as advisor_build
from clockspeed.advisor.advise import (
    advise,
    advise_and_record,
    advise_world,
    inputs_of,
    settled_rules,
)
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
from clockspeed.audit.build import (
    WARN_BUILD_MISMATCH,
    WARN_BUILD_UNCOMPARED,
    WARN_REGISTRY_MISMATCH,
    WARN_REGISTRY_UNVERIFIED,
    registry_check_of,
)
from clockspeed.audit.fuel import fuel_supply_of
from clockspeed.audit.machines import machines_of
from clockspeed.audit.network import network_of
from clockspeed.audit.placement import placement_of
from clockspeed.data import version
from clockspeed.data.registry import Registry
from tests.advisor import test_world_advice as world_fixtures
from tests.advisor.build_fixtures import (
    OFF_PIN_DOCS_SHA256,
    OFF_PIN_OFFSETS,
    build_check,
    docs_pin,
    game_pin,
    mismatched_registry_inputs,
    off_pin_build_inputs,
    pinned_build_inputs,
    registry_check,
    synthetic_world,
    uncompared_build_inputs,
    unverified_registry_inputs,
    verified_registry_inputs,
)
from tests.audit import test_balance as balance_fixtures

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

#: The alternative the caveat records as indeterminate over an unchecked registry.
REGISTRY_ALTERNATIVE: Final = "present a nameplate figure as the pinned build's own"

#: The six input names, spelled here independently of the module under test:
#: the build check's three, then the registry check's three (CS-1315).
SAVE_IN: Final = "build.save_changelist"
PINNED_IN: Final = "build.pinned_changelist"
WARNINGS_IN: Final = "build.warnings"
REGISTRY_SHA_IN: Final = "build.registry_sha256"
PINNED_DOCS_IN: Final = "build.pinned_docs_sha256"
REGISTRY_WARNINGS_IN: Final = "build.registry_warnings"
CHECK_NAMES: Final = (SAVE_IN, PINNED_IN, WARNINGS_IN)
REGISTRY_NAMES: Final = (REGISTRY_SHA_IN, PINNED_DOCS_IN, REGISTRY_WARNINGS_IN)
NAMES: Final = (*CHECK_NAMES, *REGISTRY_NAMES)

#: How many reads open every trace the caveat runs in.
READS: Final = len(NAMES)


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
    assert set(second) == set(CHECK_NAMES)


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
    assert _kinds(trace) == [StepKind.INPUT_READ] * READS + [StepKind.RULE_FIRED]
    assert _only_tier2(advice) == BASE_REASON
    settled = PROBE_ID in settled_rules(advice.traces)
    assert settled


def test_on_the_pin_a_silent_probe_settles(tmp_path: Path) -> None:
    advice = _advise(tmp_path, pinned_build_inputs(game_pin()), fires=False)
    trace = _only_trace(advice)
    assert _kinds(trace) == [StepKind.INPUT_READ] * READS
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
def test_off_the_pin_one_indeterminate_step_follows_the_build_reads(
    tmp_path: Path, offset: int
) -> None:
    pin = game_pin()
    advice = _advise(tmp_path, off_pin_build_inputs(pin, offset))
    trace = _only_trace(advice)
    assert _kinds(trace) == [
        *[StepKind.INPUT_READ] * READS,
        StepKind.VERDICT_INDETERMINATE,
        StepKind.RULE_FIRED,
    ]
    assert [step.subject for step in trace.steps[:READS]] == list(NAMES)
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
    assert f"  {READS + 1}. Indeterminate {NAMEPLATE_ALTERNATIVE}: {detail}" in lines


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
    assert _kinds(trace)[: READS + 1] == [
        *[StepKind.INPUT_READ] * READS,
        StepKind.VERDICT_INDETERMINATE,
    ]
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


# --- the registry's source (CS-1315) ---------------------------------------------


def _registry_detail(source: str | None, pinned: str | None) -> str:
    """The audit's own fixed detail line for the one warning a registry check raises."""
    warnings = registry_check(source, pinned).warnings
    count = len(warnings)
    assert count == 1
    return warnings[0].detail


def _with_registry(pin: int, registry: dict[str, InputValue]) -> dict[str, InputValue]:
    """The on-pin build inputs with the registry's three replaced."""
    return pinned_build_inputs(pin) | registry


#: The reason suffix over a registry built from other bytes.
MISMATCH_SUFFIX: Final = (
    f"; {WARN_REGISTRY_MISMATCH}: priced from a registry whose docs differ from the pinned build's"
)

#: The reason suffix over a registry with no byte source.
UNVERIFIED_SUFFIX: Final = (
    f"; {WARN_REGISTRY_UNVERIFIED}: priced from a registry never checked against the pinned docs"
)


def test_the_registry_input_names_are_pinned_and_follow_the_build_names() -> None:
    assert advisor_build.REGISTRY_INPUTS == REGISTRY_NAMES
    assert BUILD_INPUTS[: len(CHECK_NAMES)] == CHECK_NAMES
    assert BUILD_INPUTS[len(CHECK_NAMES) :] == REGISTRY_NAMES
    assert all(NAME_PATTERN.fullmatch(name) is not None for name in REGISTRY_NAMES)


@pytest.mark.parametrize("state", ["verified", "mismatched", "unverified"])
def test_the_registry_adapter_offers_exactly_its_inputs_each_sourced_to_its_audit_field(
    state: str,
) -> None:
    docs = docs_pin()
    source = {"verified": docs, "mismatched": OFF_PIN_DOCS_SHA256, "unverified": None}[state]
    check = registry_check(source, docs)
    offered = advisor_build.registry_inputs(check)
    sources = {name: value.source for name, value in offered.items()}
    assert sources == {
        REGISTRY_SHA_IN: "audit.build.registry.source_sha256",
        PINNED_DOCS_IN: "audit.build.registry.pinned_sha256",
        REGISTRY_WARNINGS_IN: "audit.build.registry.warnings",
    }
    assert offered[REGISTRY_SHA_IN].value == check.source_sha256
    assert offered[PINNED_DOCS_IN].value == docs
    warnings = offered[REGISTRY_WARNINGS_IN].value
    assert type(warnings) is MappingProxyType
    assert dict(warnings) == {w.code: w.detail for w in check.warnings}


def test_the_registry_adapter_returns_a_fresh_dict_each_call() -> None:
    check = registry_check(docs_pin(), docs_pin())
    first = advisor_build.registry_inputs(check)
    first.pop(REGISTRY_SHA_IN)
    second = advisor_build.registry_inputs(check)
    assert set(second) == set(REGISTRY_NAMES)


def test_a_registry_from_other_bytes_names_the_mismatch_on_the_reason(tmp_path: Path) -> None:
    advice = _advise(tmp_path, _with_registry(game_pin(), mismatched_registry_inputs(docs_pin())))
    assert _only_tier2(advice) == BASE_REASON + MISMATCH_SUFFIX


def test_a_registry_from_other_bytes_records_one_indeterminate_step(tmp_path: Path) -> None:
    docs = docs_pin()
    advice = _advise(tmp_path, _with_registry(game_pin(), mismatched_registry_inputs(docs)))
    trace = _only_trace(advice)
    assert _kinds(trace) == [
        *[StepKind.INPUT_READ] * READS,
        StepKind.VERDICT_INDETERMINATE,
        StepKind.RULE_FIRED,
    ]
    detail = _registry_detail(OFF_PIN_DOCS_SHA256, docs)
    assert _indeterminate(trace) == [(REGISTRY_ALTERNATIVE, detail)]
    settled = PROBE_ID in settled_rules(advice.traces)
    assert not settled


def test_a_registry_with_no_byte_source_names_itself_unverified(tmp_path: Path) -> None:
    docs = docs_pin()
    advice = _advise(tmp_path, _with_registry(game_pin(), unverified_registry_inputs(docs)))
    tier2 = _only_tier2(advice)
    assert tier2 == BASE_REASON + UNVERIFIED_SUFFIX
    mismatch_named = WARN_REGISTRY_MISMATCH in tier2
    assert not mismatch_named
    trace = _only_trace(advice)
    assert _indeterminate(trace) == [(REGISTRY_ALTERNATIVE, _registry_detail(None, docs))]
    settled = PROBE_ID in settled_rules(advice.traces)
    assert not settled


def test_no_pinned_docs_hash_is_unverified_too(tmp_path: Path) -> None:
    advice = _advise(tmp_path, _with_registry(game_pin(), unverified_registry_inputs(None)))
    assert _only_tier2(advice) == BASE_REASON + UNVERIFIED_SUFFIX
    lines = advice.cards[0].card.tier3.splitlines()
    assert f"  5. Read {PINNED_DOCS_IN} = none from audit.build.registry.pinned_sha256" in lines


@pytest.mark.parametrize("registry", ["mismatched", "unverified"])
def test_a_silent_probe_over_an_unchecked_registry_is_not_settled(
    tmp_path: Path, registry: str
) -> None:
    docs = docs_pin()
    offered = {"mismatched": mismatched_registry_inputs, "unverified": unverified_registry_inputs}[
        registry
    ](docs)
    advice = _advise(tmp_path, _with_registry(game_pin(), offered), fires=False)
    assert advice.cards == ()
    count = len(_indeterminate(_only_trace(advice)))
    assert count == 1
    settled = PROBE_ID in settled_rules(advice.traces)
    assert not settled


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
def test_a_build_only_difference_with_equal_bytes_raises_no_registry_code(
    tmp_path: Path, offset: int
) -> None:
    """The session 140 ruling: content hash only, so a moved build alone is the build's."""
    pin = game_pin()
    advice = _advise(tmp_path, off_pin_build_inputs(pin, offset))
    tier2 = _only_tier2(advice)
    registry_named = WARN_REGISTRY_MISMATCH in tier2 or WARN_REGISTRY_UNVERIFIED in tier2
    assert not registry_named
    alternatives = [subject for subject, _ in _indeterminate(_only_trace(advice))]
    assert alternatives == [NAMEPLATE_ALTERNATIVE]


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
def test_an_off_pin_save_over_other_bytes_names_both_build_first(
    tmp_path: Path, offset: int
) -> None:
    pin = game_pin()
    docs = docs_pin()
    advice = _advise(tmp_path, off_pin_build_inputs(pin, offset) | mismatched_registry_inputs(docs))
    build_suffix = (
        f"; {WARN_BUILD_MISMATCH}: priced at the pinned build {pin},"
        f" not the save build {pin + offset}"
    )
    assert _only_tier2(advice) == BASE_REASON + build_suffix + MISMATCH_SUFFIX
    assert _indeterminate(_only_trace(advice)) == [
        (NAMEPLATE_ALTERNATIVE, _detail(pin + offset, pin)),
        (REGISTRY_ALTERNATIVE, _registry_detail(OFF_PIN_DOCS_SHA256, docs)),
    ]


def test_tier_3_shows_each_registry_read_with_its_source(tmp_path: Path) -> None:
    docs = docs_pin()
    advice = _advise(tmp_path, _with_registry(game_pin(), mismatched_registry_inputs(docs)))
    lines = advice.cards[0].card.tier3.splitlines()
    fourth = (
        f'  4. Read {REGISTRY_SHA_IN} = "{OFF_PIN_DOCS_SHA256}"'
        " from audit.build.registry.source_sha256"
    )
    fifth = f'  5. Read {PINNED_DOCS_IN} = "{docs}" from audit.build.registry.pinned_sha256'
    assert fourth in lines
    assert lines[lines.index(fourth) + 1] == fifth
    sixth = lines[lines.index(fifth) + 1]
    assert sixth.startswith(f'  6. Read {REGISTRY_WARNINGS_IN} = {{"{WARN_REGISTRY_MISMATCH}": ')
    assert sixth.endswith(" from audit.build.registry.warnings")
    detail = _registry_detail(OFF_PIN_DOCS_SHA256, docs)
    assert f"  7. Indeterminate {REGISTRY_ALTERNATIVE}: {detail}" in lines


def test_the_fixture_docs_pin_is_the_version_pin_read_at_test_time() -> None:
    assert version.DOCS_SHA256
    assert docs_pin() == version.DOCS_SHA256
    assert docs_pin() != OFF_PIN_DOCS_SHA256
    assert verified_registry_inputs(docs_pin())[REGISTRY_SHA_IN].value == docs_pin()
    assert pinned_build_inputs(game_pin())[REGISTRY_SHA_IN].value == docs_pin()


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
    # CS-1315: the registry's three, cross-checked against the two hashes.
    (
        "registry-mismatch-code-with-equal-hashes",
        lambda pin: _replaced(
            pinned_build_inputs(pin), REGISTRY_WARNINGS_IN, _codes(WARN_REGISTRY_MISMATCH)
        ),
        "ValueError",
    ),
    (
        "no-registry-code-with-differing-hashes",
        lambda pin: _replaced(
            _with_registry(pin, mismatched_registry_inputs(docs_pin())),
            REGISTRY_WARNINGS_IN,
            _codes(),
        ),
        "ValueError",
    ),
    (
        "unverified-code-with-both-hashes",
        lambda pin: _replaced(
            _with_registry(pin, mismatched_registry_inputs(docs_pin())),
            REGISTRY_WARNINGS_IN,
            _codes(WARN_REGISTRY_UNVERIFIED),
        ),
        "ValueError",
    ),
    (
        "registry-mismatch-code-with-no-source",
        lambda pin: _replaced(
            _with_registry(pin, unverified_registry_inputs(docs_pin())),
            REGISTRY_WARNINGS_IN,
            _codes(WARN_REGISTRY_MISMATCH),
        ),
        "ValueError",
    ),
    (
        "a-build-code-in-the-registry-warnings",
        lambda pin: _replaced(
            pinned_build_inputs(pin), REGISTRY_WARNINGS_IN, _codes(WARN_BUILD_MISMATCH)
        ),
        "ValueError",
    ),
    (
        "a-registry-code-in-the-build-warnings",
        lambda pin: _replaced(
            pinned_build_inputs(pin), WARNINGS_IN, _codes(WARN_REGISTRY_MISMATCH)
        ),
        "ValueError",
    ),
    (
        "a-bool-for-the-registry-hash",
        lambda pin: _replaced(pinned_build_inputs(pin), REGISTRY_SHA_IN, True),
        "TypeError",
    ),
    (
        "a-one-tuple-of-the-pinned-hash-for-the-registry-hash",
        lambda pin: _replaced(pinned_build_inputs(pin), REGISTRY_SHA_IN, (docs_pin(),)),
        "TypeError",
    ),
    (
        "an-int-for-the-pinned-docs-hash",
        lambda pin: _replaced(pinned_build_inputs(pin), PINNED_DOCS_IN, pin),
        "TypeError",
    ),
    (
        "a-tuple-for-the-registry-warnings",
        lambda pin: _replaced(
            pinned_build_inputs(pin), REGISTRY_WARNINGS_IN, (WARN_REGISTRY_MISMATCH,)
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


# --- the composition carries the registry check (CS-1315) ------------------------
#
# The real path a surface takes: ``inputs_of`` composes the registry check over
# the very registry it prices from, against the pinned docs hash it is handed,
# and ``advise_world`` runs every registered rule over it. The worlds and their
# registries are the CS-1270 composition suite's; only the registry's source
# hash is varied here. Every assertion over served advice binds a count first.


def _sourced(registry: Registry, source: str | None) -> Registry:
    """The registry with its source hash replaced, everything else kept."""
    return dataclasses.replace(registry, source_sha256=source)


def _source_of(case: str) -> str | None:
    """The source hash each registry case carries against :func:`docs_pin`."""
    return {"verified": docs_pin(), "mismatched": OFF_PIN_DOCS_SHA256, "unverified": None}[case]


#: The code each unchecked registry case must put on every card.
UNCHECKED: Final = {"mismatched": WARN_REGISTRY_MISMATCH, "unverified": WARN_REGISTRY_UNVERIFIED}


def _served_over(
    directory: Path, world_name: str, source: str | None, *, save_offset: int = 0
) -> Advice:
    make_world, make_registry = world_fixtures.WORLDS[world_name]
    model = make_world()
    if save_offset:
        header = dataclasses.replace(model.header, build_changelist=game_pin() + save_offset)
        model = dataclasses.replace(model, header=header)
    return advise_world(
        model,
        _sourced(make_registry(), source),
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=NOW,
    )


@pytest.mark.parametrize("case", ["verified", "mismatched", "unverified"])
def test_inputs_of_offers_the_registry_check_of_the_registry_it_prices(case: str) -> None:
    docs = docs_pin()
    registry = _sourced(world_fixtures.synthetic_registry(), _source_of(case))

    built = inputs_of(
        world_fixtures.gap_world(),
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs,
    )

    expected = advisor_build.registry_inputs(registry_check_of(registry, pinned_docs_sha256=docs))
    same = {name: built.values[name] for name in REGISTRY_NAMES} == expected
    assert same, case


@pytest.mark.parametrize("world_name", sorted(world_fixtures.WORLDS))
@pytest.mark.parametrize("case", sorted(UNCHECKED))
def test_every_served_card_over_an_unchecked_registry_names_its_code_and_nothing_settles(
    tmp_path: Path, case: str, world_name: str
) -> None:
    code = UNCHECKED[case]
    served = _served_over(tmp_path, world_name, _source_of(case))

    cards = len(served.cards)
    unnamed = sum(
        1
        for advised in served.cards
        if code not in advised.card.tier2 or code not in advised.card.tier3
    )
    settled = len(settled_rules(served.traces))
    assert cards > 0
    assert unnamed == 0
    assert settled == 0


@pytest.mark.parametrize("world_name", sorted(world_fixtures.WORLDS))
def test_over_the_pinned_bytes_no_served_card_names_a_registry_code(
    tmp_path: Path, world_name: str
) -> None:
    served = _served_over(tmp_path, world_name, docs_pin())

    cards = len(served.cards)
    naming = sum(
        1
        for advised in served.cards
        for code in UNCHECKED.values()
        if code in advised.card.tier2 or code in advised.card.tier3
    )
    assert cards > 0
    assert naming == 0


@pytest.mark.parametrize("offset", OFF_PIN_OFFSETS, ids=_side)
def test_a_served_off_pin_save_over_the_pinned_bytes_names_the_build_alone(
    tmp_path: Path, offset: int
) -> None:
    """The acceptance's build-only case, end to end: the build moved, the bytes did not."""
    served = _served_over(tmp_path, "gap", docs_pin(), save_offset=offset)

    cards = len(served.cards)
    build_named = sum(1 for advised in served.cards if WARN_BUILD_MISMATCH in advised.card.tier2)
    registry_named = sum(
        1
        for advised in served.cards
        for code in UNCHECKED.values()
        if code in advised.card.tier2 or code in advised.card.tier3
    )
    assert cards > 0
    assert build_named == cards
    assert registry_named == 0


@pytest.mark.parametrize("case", ["verified", "mismatched", "unverified"])
def test_advise_and_record_completes_nothing_over_an_unchecked_registry(
    tmp_path: Path, case: str
) -> None:
    """A gap card recorded over the pinned bytes; then the gap is gone.

    Over the pinned bytes the gap rule settles silent and its card is
    completed - the control. Over an unchecked registry the same silence is
    priced from a registry nobody verified, so nothing is completed.
    """
    docs = docs_pin()
    verified = _sourced(world_fixtures.synthetic_registry(), docs)
    first = advise_and_record(
        world_fixtures.gap_world().token,
        inputs_of(
            world_fixtures.gap_world(),
            verified,
            pinned_changelist=game_pin(),
            pinned_docs_sha256=docs,
        ),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=NOW,
    )
    gap_id = next(a.card.id for a in first.cards if a.card.rule_id == power.GAP_RULE.rule_id)
    resolved = balance_fixtures.world_of(balance_fixtures.FIXED_WHOLE)

    second = advise_and_record(
        resolved.token,
        inputs_of(
            resolved,
            _sourced(world_fixtures.synthetic_registry(), _source_of(case)),
            pinned_changelist=game_pin(),
            pinned_docs_sha256=docs,
        ),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=NOW,
    )

    gap_fires = any(a.card.rule_id == power.GAP_RULE.rule_id for a in second.cards)
    completed_gap = second.completed == (gap_id,)
    completed_none = second.completed == ()
    assert not gap_fires
    if case == "verified":
        assert completed_gap
    else:
        assert completed_none


def test_the_docs_pin_is_a_required_keyword_of_both_composition_calls(tmp_path: Path) -> None:
    """A caller that forgets the docs pin fails to call rather than pricing silently."""
    compose: Any = inputs_of
    serve: Any = advise_world
    model = world_fixtures.gap_world()
    registry = world_fixtures.synthetic_registry()
    with pytest.raises(TypeError):
        compose(model, registry, pinned_changelist=game_pin())
    with pytest.raises(TypeError):
        serve(
            model,
            registry,
            pinned_changelist=game_pin(),
            ledger=Ledger(tmp_path),
            mutes=MuteStore(tmp_path),
            now=NOW,
        )


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
