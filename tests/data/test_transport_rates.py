"""Tests for the transport rates the registry publishes (CS-1394).

The shipped docs STATE each conveyor belt, conveyor lift and pipeline class's
per-minute capacity in its own ``mDescription``, next to a numeric speed field
(``mSpeed`` for belts and lifts, ``mFlowLimit`` for pipes). The registry
publishes the STATED rate, and only when the description and the numeric field
both read and the stated-to-numeric ratio is one exact value across the whole
group. There is no authored conversion factor anywhere on the path, so every
ratio in the fixtures below is a deliberately NON-game value: a hand-written
1/2 or 60 in the implementation would publish a wrong number for all of them.

Everything here is hand-authored. No game install is read and no value below is
a game value (CLAUDE.md section 7: fixtures are synthetic registries).
"""

from __future__ import annotations

import ast
import dataclasses
from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any

from clockspeed.data import registry as registry_module
from clockspeed.data.docs_extract import DocsDocument, DocsGroup
from clockspeed.data.registry import (
    TRANSPORT_GROUP_SHORT_NAMES,
    WARN_DUPLICATE_CLASS_NAME,
    WARN_INCONSISTENT_TRANSPORT_RATE,
    WARN_MISSING_TRANSPORT_RATE,
    WARN_NON_STRING_VALUE,
    Registry,
    Transport,
    build_registry,
)

BELT_GROUP = "FGBuildableConveyorBelt"
LIFT_GROUP = "FGBuildableConveyorLift"
PIPE_GROUP = "FGBuildablePipeline"

#: Separators the shipped docs put inside a stated rate, spelled as escapes so
#: this file stays 7-bit ASCII: NO-BREAK SPACE, NARROW NO-BREAK SPACE, and the
#: cube sign.
NBSP = "\u00a0"
NNBSP = "\u202f"
CUBE = "\u00b3"


def _belt_text(rate: str) -> str:
    return f"Synthetic belt.{NBSP}Transports up to{NBSP}{rate}{NNBSP}resources per minute."


def _pipe_text(rate: str) -> str:
    return f"Synthetic pipe.{NBSP}Capacity:{NBSP}{rate}{NNBSP}m{CUBE} of fluid per minute."


def _real_pipe_text(rate: str) -> str:
    # The measured shipped shape, with synthetic numbers: an ordinary space after
    # the colon, a NARROW NO-BREAK SPACE before the unit and a NO-BREAK SPACE
    # between the cube sign and "of".
    return f"Capacity: {rate}{NNBSP}m{CUBE}{NBSP}of fluid per minute."


def _entry(class_name: str | None, **fields: Any) -> dict[str, Any]:
    entry: dict[str, Any] = dict(fields)
    if class_name is not None:
        entry["ClassName"] = class_name
    return entry


def _belt(class_name: str, speed: str | None, rate: str | None) -> dict[str, Any]:
    entry = _entry(class_name)
    if speed is not None:
        entry["mSpeed"] = speed
    if rate is not None:
        entry["mDescription"] = _belt_text(rate)
    return entry


def _pipe(class_name: str, flow: str | None, rate: str | None) -> dict[str, Any]:
    entry = _entry(class_name)
    if flow is not None:
        entry["mFlowLimit"] = flow
    if rate is not None:
        entry["mDescription"] = _pipe_text(rate)
    return entry


def _group(short_name: str, entries: Sequence[Mapping[str, Any]]) -> DocsGroup:
    native = f"/Script/CoreUObject.Class'/Script/FactoryGame.{short_name}'"
    return DocsGroup(native, short_name, tuple(entries))


def _registry(*groups: DocsGroup) -> Registry:
    return build_registry(DocsDocument(tuple(groups), (), ()))


def _warning_rows(registry: Registry) -> set[tuple[str, str]]:
    return {(warning.code, warning.subject) for warning in registry.warnings}


# Belt ratio 1/3, lift ratio 1/3, pipe ratio 20: none is a game value, so a
# hand-authored 1/2 or 60 cannot pass by coincidence.
GOOD_BELTS = (
    _belt("Build_SynthBeltA_C", "30.000000", "10"),
    _belt("Build_SynthBeltB_C", "60.000000", "20"),
    _belt("Build_SynthBeltC_C", "90.000000", "30"),
)
GOOD_LIFTS = (
    _belt("Build_SynthLiftA_C", "45.000000", "15"),
    _belt("Build_SynthLiftB_C", "90.000000", "30"),
)
GOOD_PIPES = (
    _pipe("Build_SynthPipeA_C", "0.250000", "5"),
    _pipe("Build_SynthPipeB_C", "0.500000", "10"),
)

EXPECTED_RATES = {
    "Build_SynthBeltA_C": (BELT_GROUP, "belt", "item", Fraction(30), Fraction(10)),
    "Build_SynthBeltB_C": (BELT_GROUP, "belt", "item", Fraction(60), Fraction(20)),
    "Build_SynthBeltC_C": (BELT_GROUP, "belt", "item", Fraction(90), Fraction(30)),
    "Build_SynthLiftA_C": (LIFT_GROUP, "belt", "item", Fraction(45), Fraction(15)),
    "Build_SynthLiftB_C": (LIFT_GROUP, "belt", "item", Fraction(90), Fraction(30)),
    "Build_SynthPipeA_C": (PIPE_GROUP, "pipe", "m3", Fraction(1, 4), Fraction(5)),
    "Build_SynthPipeB_C": (PIPE_GROUP, "pipe", "m3", Fraction(1, 2), Fraction(10)),
}


def _good_registry() -> Registry:
    return _registry(
        _group(BELT_GROUP, GOOD_BELTS),
        _group(LIFT_GROUP, GOOD_LIFTS),
        _group(PIPE_GROUP, GOOD_PIPES),
    )


def test_every_declared_belt_and_pipe_class_publishes_an_exact_per_minute_rate() -> None:
    registry = _good_registry()
    assert set(registry.transports) == set(EXPECTED_RATES)
    for key, (group, kind, unit, numeric, rate) in EXPECTED_RATES.items():
        transport = registry.transports[key]
        assert isinstance(transport, Transport), key
        assert transport.key == key
        assert transport.group == group, key
        assert transport.kind == kind, key
        assert transport.unit == unit, key
        assert transport.numeric == numeric, key
        assert transport.per_minute == rate, key
        assert type(transport.per_minute) is Fraction, key
    # Nothing is flagged on a clean group.
    flagged = {
        code
        for code, _subject in _warning_rows(registry)
        if code
        in {
            WARN_MISSING_TRANSPORT_RATE,
            WARN_INCONSISTENT_TRANSPORT_RATE,
            WARN_NON_STRING_VALUE,
            WARN_DUPLICATE_CLASS_NAME,
        }
    }
    assert flagged == set()


def test_the_published_rate_is_the_stated_one_not_a_constant_times_the_field() -> None:
    # Same numeric field, different stated rates, in two groups: the published
    # rate follows the DESCRIPTION. A hand-written factor would give both the
    # same answer for the same field.
    one = _registry(_group(BELT_GROUP, [_belt("Build_S_C", "30", "10")]))
    other = _registry(_group(BELT_GROUP, [_belt("Build_S_C", "30", "15")]))
    assert one.transports["Build_S_C"].per_minute == Fraction(10)
    assert other.transports["Build_S_C"].per_minute == Fraction(15)


def test_the_included_transport_groups_are_pinned() -> None:
    assert set(TRANSPORT_GROUP_SHORT_NAMES) == {BELT_GROUP, LIFT_GROUP, PIPE_GROUP}
    # Classes of every neighbouring transport-like group are NOT published, even
    # when they carry a speed field and a stated description.
    strays = (
        "FGBuildableConveyorMonitor",
        "FGBuildablePipelinePump",
        "FGBuildablePipelineJunction",
        "FGBuildablePipeHyper",
        "FGBuildableAttachmentSplitter",
    )
    groups = [_group(name, [_belt("Build_Stray_" + name + "_C", "30", "10")]) for name in strays]
    registry = _registry(_group(BELT_GROUP, GOOD_BELTS), *groups)
    assert set(registry.transports) == {
        "Build_SynthBeltA_C",
        "Build_SynthBeltB_C",
        "Build_SynthBeltC_C",
    }


def test_a_missing_operand_is_unknown_never_zero() -> None:
    belts = (
        *GOOD_BELTS,
        _belt("Build_NoSpeed_C", None, "10"),
        _belt("Build_NoText_C", "30", None),
        _belt("Build_BothGone_C", None, None),
    )
    pipes = (
        *GOOD_PIPES,
        _pipe("Build_NoFlow_C", None, "5"),
        _pipe("Build_NoPipeText_C", "1", None),
    )
    registry = _registry(_group(BELT_GROUP, belts), _group(PIPE_GROUP, pipes))
    unknown = (
        "Build_NoSpeed_C",
        "Build_NoText_C",
        "Build_BothGone_C",
        "Build_NoFlow_C",
        "Build_NoPipeText_C",
    )
    for key in unknown:
        transport = registry.transports[key]
        assert transport.per_minute is None, key
        assert transport.per_minute != 0, key
        assert (WARN_MISSING_TRANSPORT_RATE, key) in _warning_rows(registry), key
    # The operand that WAS present is kept verbatim, and absent is None.
    assert registry.transports["Build_NoSpeed_C"].numeric is None
    assert registry.transports["Build_NoText_C"].numeric == Fraction(30)
    # An unknown neighbour does not poison the classes that read cleanly.
    assert registry.transports["Build_SynthBeltB_C"].per_minute == Fraction(20)
    assert registry.transports["Build_SynthPipeB_C"].per_minute == Fraction(10)


def test_an_unreadable_description_is_unknown_and_flagged() -> None:
    unreadable = {
        "Build_Prose_C": "A belt that carries things.",
        "Build_Locale_C": f"Transporte hasta{NBSP}10{NNBSP}recursos por minuto.",
        "Build_Grouped_C": f"Transports up to{NBSP}1{NNBSP}200{NNBSP}resources per minute.",
        "Build_Wrong_C": f"Transports up to{NBSP}10{NNBSP}resources per hour.",
        "Build_Empty_C": "",
    }
    belts = [
        *GOOD_BELTS,
        *({"ClassName": k, "mSpeed": "30", "mDescription": v} for k, v in unreadable.items()),
    ]
    registry = _registry(_group(BELT_GROUP, belts))
    for key in unreadable:
        assert registry.transports[key].per_minute is None, key
        assert (WARN_MISSING_TRANSPORT_RATE, key) in _warning_rows(registry), key
    assert registry.transports["Build_SynthBeltA_C"].per_minute == Fraction(10)


def test_a_zero_negative_or_unparsable_operand_is_unknown() -> None:
    belts = (
        *GOOD_BELTS,
        _belt("Build_ZeroSpeed_C", "0.000000", "10"),
        _belt("Build_NegSpeed_C", "-30", "10"),
        _belt("Build_ZeroRate_C", "30", "0"),
        _belt("Build_BadSpeed_C", "fast", "10"),
    )
    registry = _registry(_group(BELT_GROUP, belts))
    for key in ("Build_ZeroSpeed_C", "Build_NegSpeed_C", "Build_ZeroRate_C", "Build_BadSpeed_C"):
        assert registry.transports[key].per_minute is None, key
        assert (WARN_MISSING_TRANSPORT_RATE, key) in _warning_rows(registry), key


def test_a_non_string_operand_is_unknown_and_flagged_as_non_string() -> None:
    entry = {
        "ClassName": "Build_Odd_C",
        "mSpeed": 30,
        "mDescription": _belt_text("10"),
    }
    registry = _registry(_group(BELT_GROUP, [*GOOD_BELTS, entry]))
    assert registry.transports["Build_Odd_C"].per_minute is None
    rows = _warning_rows(registry)
    assert (WARN_NON_STRING_VALUE, "Build_Odd_C") in rows
    assert (WARN_MISSING_TRANSPORT_RATE, "Build_Odd_C") in rows


def test_disagreeing_ratios_in_a_group_publish_nothing_and_warn() -> None:
    # Two classes whose stated/numeric ratios differ (1/3 versus 1/2): one of
    # the two texts is stale on a patch and nothing says which, so the WHOLE
    # group is unknown and flagged. The other groups are untouched.
    belts = (
        _belt("Build_SynthBeltA_C", "30", "10"),
        _belt("Build_SynthBeltB_C", "60", "30"),
    )
    registry = _registry(_group(BELT_GROUP, belts), _group(PIPE_GROUP, GOOD_PIPES))
    for key in ("Build_SynthBeltA_C", "Build_SynthBeltB_C"):
        transport = registry.transports[key]
        assert transport.per_minute is None, key
        assert transport.per_minute != 0, key
        assert (WARN_INCONSISTENT_TRANSPORT_RATE, key) in _warning_rows(registry), key
    # The verbatim operands survive, so the disagreement stays inspectable.
    assert registry.transports["Build_SynthBeltA_C"].numeric == Fraction(30)
    assert registry.transports["Build_SynthPipeA_C"].per_minute == Fraction(5)
    assert registry.transports["Build_SynthPipeB_C"].per_minute == Fraction(10)


def test_the_disagree_arm_holds_for_every_transport_group() -> None:
    for short_name, builder in (
        (BELT_GROUP, _belt),
        (LIFT_GROUP, _belt),
        (PIPE_GROUP, _pipe),
    ):
        entries = [builder("Build_A_C", "10", "5"), builder("Build_B_C", "10", "6")]
        registry = _registry(_group(short_name, entries))
        assert registry.transports["Build_A_C"].per_minute is None, short_name
        assert registry.transports["Build_B_C"].per_minute is None, short_name
        assert (WARN_INCONSISTENT_TRANSPORT_RATE, "Build_A_C") in _warning_rows(registry)


def test_the_ratio_is_checked_within_a_group_not_across_groups() -> None:
    # Belts at 1/3 and lifts at 1/2 are each consistent inside their own group.
    registry = _registry(
        _group(BELT_GROUP, [_belt("Build_B_C", "30", "10")]),
        _group(LIFT_GROUP, [_belt("Build_L_C", "30", "15")]),
    )
    assert registry.transports["Build_B_C"].per_minute == Fraction(10)
    assert registry.transports["Build_L_C"].per_minute == Fraction(15)


def test_a_class_with_a_missing_operand_does_not_break_the_group_agreement() -> None:
    belts = (
        _belt("Build_SynthBeltA_C", "30", "10"),
        _belt("Build_SynthBeltB_C", "60", "20"),
        _belt("Build_NoText_C", "99", None),
    )
    registry = _registry(_group(BELT_GROUP, belts))
    assert registry.transports["Build_SynthBeltA_C"].per_minute == Fraction(10)
    assert registry.transports["Build_SynthBeltB_C"].per_minute == Fraction(20)
    assert registry.transports["Build_NoText_C"].per_minute is None


def test_a_duplicate_class_name_keeps_the_first_and_flags() -> None:
    belts = (_belt("Build_Dup_C", "30", "10"), _belt("Build_Dup_C", "60", "99"))
    registry = _registry(_group(BELT_GROUP, belts))
    assert registry.transports["Build_Dup_C"].per_minute == Fraction(10)
    assert (WARN_DUPLICATE_CLASS_NAME, "Build_Dup_C") in _warning_rows(registry)


def test_the_decimal_parse_is_exact() -> None:
    registry = _registry(_group(PIPE_GROUP, [_pipe("Build_P_C", "0.100000", "2")]))
    transport = registry.transports["Build_P_C"]
    assert transport.numeric == Fraction(1, 10)
    assert transport.per_minute == Fraction(2)


def test_an_empty_document_publishes_an_empty_read_only_mapping() -> None:
    registry = _registry()
    assert len(registry.transports) == 0
    assert isinstance(registry.transports, MappingProxyType)
    bare = Registry(items={}, recipes={}, buildings={}, warnings=(), unknown_groups=())
    assert len(bare.transports) == 0
    names = [field.name for field in dataclasses.fields(Registry)]
    assert names[-1] == "transports"


def test_no_published_rate_is_a_float() -> None:
    registry = _good_registry()
    assert registry.transports
    for key, transport in registry.transports.items():
        assert isinstance(transport.numeric, Fraction), key
        assert isinstance(transport.per_minute, Fraction), key
        for field in dataclasses.fields(transport):
            assert not isinstance(getattr(transport, field.name), float), (key, field.name)


def test_the_rate_path_source_has_no_float_and_no_authored_factor() -> None:
    source = Path(registry_module.__file__).read_text(encoding="ascii")
    tree = ast.parse(source)
    targets = {
        "_stated_rate",
        "_transport",
        "_build_transports",
        "_reconcile_group",
    }
    found = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name in targets
    }
    assert found == targets
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name in targets):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Constant):
                # No float literal, and no bare 60 or 1/2 factor.
                assert not isinstance(sub.value, float), node.name
                assert sub.value not in (60, 1000), (node.name, sub.value)
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                assert sub.func.id != "float", node.name


# ---------------------------------------------------------------------------
# The measured shipped shape, and the robustness arms (CS-1394 repair)
# ---------------------------------------------------------------------------


def test_the_measured_pipe_shape_with_a_no_break_space_before_of_publishes() -> None:
    # Ratio 20 again, never a game value. The text carries U+202F before the unit
    # and U+00A0 between the cube sign and "of"; a pattern that wants a plain space
    # there reads every real pipeline class as unknown.
    pipes = [
        {"ClassName": "Build_RealA_C", "mFlowLimit": "0.25", "mDescription": _real_pipe_text("5")},
        {"ClassName": "Build_RealB_C", "mFlowLimit": "0.5", "mDescription": _real_pipe_text("10")},
    ]
    registry = _registry(_group(PIPE_GROUP, pipes))
    assert registry.transports["Build_RealA_C"].per_minute == Fraction(5)
    assert registry.transports["Build_RealB_C"].per_minute == Fraction(10)
    assert (WARN_MISSING_TRANSPORT_RATE, "Build_RealA_C") not in _warning_rows(registry)


def test_every_unicode_space_and_ascii_space_spelling_publishes_the_same_rate() -> None:
    for gap in (" ", NBSP, NNBSP, " " + NBSP):
        belt = f"Transports up to{gap}10{gap}resources per minute."
        pipe = f"Capacity:{gap}5{gap}m{CUBE}{gap}of fluid per minute."
        registry = _registry(
            _group(BELT_GROUP, [{"ClassName": "Build_B_C", "mSpeed": "30", "mDescription": belt}]),
            _group(
                PIPE_GROUP, [{"ClassName": "Build_P_C", "mFlowLimit": "1", "mDescription": pipe}]
            ),
        )
        assert registry.transports["Build_B_C"].per_minute == Fraction(10), repr(gap)
        assert registry.transports["Build_P_C"].per_minute == Fraction(5), repr(gap)


def test_a_thousands_separator_is_unknown_and_flagged_never_a_wrong_number() -> None:
    belts = [
        {"ClassName": "Build_Comma_C", "mSpeed": "30", "mDescription": _belt_text("1,200")},
        {
            "ClassName": "Build_Thin_C",
            "mSpeed": "30",
            "mDescription": _belt_text("1" + NNBSP + "200"),
        },
    ]
    pipes = [
        {"ClassName": "Build_PComma_C", "mFlowLimit": "1", "mDescription": _real_pipe_text("1,200")}
    ]
    registry = _registry(_group(BELT_GROUP, belts), _group(PIPE_GROUP, pipes))
    for key in ("Build_Comma_C", "Build_Thin_C", "Build_PComma_C"):
        assert registry.transports[key].per_minute is None, key
        assert (WARN_MISSING_TRANSPORT_RATE, key) in _warning_rows(registry), key


def test_a_description_with_two_rate_phrases_is_refused_not_first_matched() -> None:
    # Decision: REFUSE. Two stated rates in one text means the prose is not the
    # measured one-sentence form, and picking the first would publish a number the
    # text contradicts. Unknown plus the warning, for belts and pipes alike.
    two_belt = _belt_text("10") + " " + _belt_text("20")
    two_pipe = _real_pipe_text("5") + " " + _real_pipe_text("7")
    registry = _registry(
        _group(
            BELT_GROUP, [{"ClassName": "Build_Two_C", "mSpeed": "30", "mDescription": two_belt}]
        ),
        _group(
            PIPE_GROUP, [{"ClassName": "Build_PTwo_C", "mFlowLimit": "1", "mDescription": two_pipe}]
        ),
    )
    for key in ("Build_Two_C", "Build_PTwo_C"):
        assert registry.transports[key].per_minute is None, key
        assert (WARN_MISSING_TRANSPORT_RATE, key) in _warning_rows(registry), key
