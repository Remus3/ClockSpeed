"""CS-1288: the save's build against the pinned build, held side by side.

Every fixture here is a hand-built synthetic ``WorldModel``. Nothing in this
module opens a save, a docs file or the install - see ``tests/audit/__init__.py``
for the four rules. Every changelist below is an invented integer, chosen so it
reads as synthetic at a glance; no real build number appears in this file.

THREE STATES, NOT TWO. The pin is a PARAMETER, and a pin that did not parse
arrives as None. A comparison against None is not a match, so the three arms
below grade three outcomes apart: a differing build raises the mismatch code
alone, an equal build raises nothing at all, and an absent pin raises the
uncompared code alone and reads as no match. An implementation that folds the
absent pin into "equal" passes the first two arms and is the silent-wrong
answer the third exists to refuse (non-negotiable 7).

BOTH BUILDS TRAVEL ON THE MODEL, NEVER IN THE DETAIL. The warning detail is one
fixed line per code, the idiom every audit module follows so a detail can never
be built from something read out of a save. So the arms assert the two builds
on the model's own fields, and assert separately that neither number reached
the detail text.
"""

from __future__ import annotations

from typing import Any, Final

import pytest

from clockspeed.audit import build
from clockspeed.save import objects
from clockspeed.save.header import SaveHeader
from clockspeed.save.world import EMPTY_UNLOCK_STATE, WorldModel

# An invented 22-character base64url literal. Never a real world token.
SYNTHETIC_TOKEN = "ClockspeedBuildToken22"  # noqa: S105 - an invented marker, not a secret

#: The build the synthetic save declares. Invented.
SAVE_BUILD: Final = 1_000_001

#: A pinned build that differs from it. Invented.
OTHER_BUILD: Final = 1_000_002


def header(build_changelist: int) -> SaveHeader:
    """Build a synthetic header carrying no operator-authored string at all.

    Args:
        build_changelist: The build the synthetic save declares.

    Returns:
        The header.
    """
    return SaveHeader(
        header_version=14,
        save_version=52,
        build_changelist=build_changelist,
        map_name="SyntheticMap",
        world_token=SYNTHETIC_TOKEN,
        play_duration=0,
        datetime_ticks=0,
        byte_after_datetime_ticks=0,
        editor_object_version=0,
        is_modded=0,
        body_offset=0,
        warnings=(),
    )


def world(build_changelist: int = SAVE_BUILD) -> WorldModel:
    """Build a synthetic world model whose header declares one build.

    Args:
        build_changelist: The build the header declares.

    Returns:
        The model, holding no record, no node and no warning.
    """
    return WorldModel(
        token=SYNTHETIC_TOKEN,
        header=header(build_changelist),
        objects=objects.ObjectTable(
            records=(),
            unknown_classes=(),
            warnings=(),
            declared_body_length=0,
            body_consumed=0,
            body_prefix_width=8,
            transform_delta=0,
            save_version=52,
            header_version=14,
        ),
        unlocks=EMPTY_UNLOCK_STATE,
        nodes=(),
        warnings=(),
    )


def codes(check: build.BuildCheck) -> list[str]:
    """The warning codes a check carries, in order, duplicates kept.

    Args:
        check: The published model.

    Returns:
        The codes.
    """
    return [warning.code for warning in check.warnings]


def test_a_differing_header_build_raises_the_mismatch_warning() -> None:
    check = build.build_check_of(world(SAVE_BUILD), pinned_changelist=OTHER_BUILD)
    assert codes(check) == [build.WARN_BUILD_MISMATCH]
    assert check.save_changelist == SAVE_BUILD
    assert check.pinned_changelist == OTHER_BUILD
    assert check.compared is True
    assert check.matches is False


def test_matching_builds_raise_nothing() -> None:
    check = build.build_check_of(world(SAVE_BUILD), pinned_changelist=SAVE_BUILD)
    assert check.warnings == ()
    assert check.save_changelist == SAVE_BUILD
    assert check.pinned_changelist == SAVE_BUILD
    assert check.compared is True
    assert check.matches is True


def test_equal_builds_held_in_distinct_objects_raise_nothing() -> None:
    """Equality is by VALUE, never by identity.

    The arm above passes one int object as both the header's build and the
    pin, so an identity comparison (``is not`` for ``!=``, ``is`` for ``==``)
    survives it. Here the two are built separately at run time, outside the
    small-int cache, and the first assertion is the discrimination control
    that they really are two objects.
    """
    save_build = int("1000000007")
    pinned = int("1000000007")
    assert save_build is not pinned, "the fixture no longer holds two distinct objects"
    check = build.build_check_of(world(save_build), pinned_changelist=pinned)
    assert check.warnings == ()
    assert check.matches is True


def test_an_unparsed_pin_is_uncompared() -> None:
    check = build.build_check_of(world(SAVE_BUILD), pinned_changelist=None)
    assert codes(check) == [build.WARN_BUILD_UNCOMPARED]
    assert check.save_changelist == SAVE_BUILD
    assert check.pinned_changelist is None
    assert check.compared is False
    assert check.matches is False, "an absent pin was read as a match"


@pytest.mark.parametrize(
    ("pinned", "code"),
    [(OTHER_BUILD, build.WARN_BUILD_MISMATCH), (None, build.WARN_BUILD_UNCOMPARED)],
    ids=["mismatch", "uncompared"],
)
def test_the_warning_is_sourced_here_and_its_detail_carries_no_build(
    pinned: int | None, code: str
) -> None:
    (warning,) = build.build_check_of(world(SAVE_BUILD), pinned_changelist=pinned).warnings
    assert warning.code == code
    assert warning.source == build.SOURCE_BUILD
    assert warning.subject is None
    assert warning.count == 1
    assert warning.detail
    assert warning.detail.isascii()
    assert str(SAVE_BUILD) not in warning.detail
    assert str(OTHER_BUILD) not in warning.detail


def test_the_pin_is_keyword_only() -> None:
    # Called through a name typed Any, so no type-ignore code is needed: mypy
    # versions disagree on which code a positional call to a keyword-only
    # parameter carries, and an ignore with the wrong one is itself an error.
    call: Any = build.build_check_of
    with pytest.raises(TypeError):
        call(world(), OTHER_BUILD)


@pytest.mark.parametrize("pinned", [str(SAVE_BUILD), True, 1.0], ids=["str", "bool", "float"])
def test_a_pin_that_is_not_an_int_is_refused(pinned: object) -> None:
    """A string pin would compare unequal to every build and read as a mismatch.

    The discrimination control is the string spelling of the save's OWN build:
    without the refusal it would raise the mismatch code over two equal builds.
    """
    with pytest.raises(TypeError):
        build.build_check_of(world(SAVE_BUILD), pinned_changelist=pinned)  # type: ignore[arg-type]


def test_the_repr_renders_both_builds_and_no_token() -> None:
    check = build.build_check_of(world(SAVE_BUILD), pinned_changelist=OTHER_BUILD)
    rendered = repr(check)
    assert str(SAVE_BUILD) in rendered
    assert str(OTHER_BUILD) in rendered
    assert SYNTHETIC_TOKEN not in rendered
    assert "warnings=1" in rendered
