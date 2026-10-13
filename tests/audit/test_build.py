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

import hashlib
import inspect
from types import MappingProxyType
from typing import Any, Final

import pytest

from clockspeed.audit import build
from clockspeed.data.registry import Registry
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


# ---------------------------------------------------------------------------
# CS-1315: the registry's source bytes against the pinned docs hash
# ---------------------------------------------------------------------------
#
# The sibling one layer down from the build check: not which build wrote the
# save, but whether the registry every figure is priced from was built from the
# pinned build's docs at all. The comparison is of CONTENT HASHES only (the
# session 140 ruling): a build-only difference with equal bytes is not a
# mismatch, so no build string reaches this check. Both hashes are invented
# digests of invented bytes, and the pin is a parameter here as it is above.

#: The sha256 of the bytes a synthetic registry was built from. Invented.
SOURCE_HASH: Final = hashlib.sha256(b"synthetic docs bytes, first edition").hexdigest()

#: A pinned docs hash that differs from it. Invented.
OTHER_HASH: Final = hashlib.sha256(b"synthetic docs bytes, second edition").hexdigest()


def registry(source_sha256: str | None = SOURCE_HASH) -> Registry:
    """An empty synthetic registry carrying one source hash, or none.

    Args:
        source_sha256: The hash of the bytes it claims to be built from, or
            None for a registry with no byte source.

    Returns:
        The registry.
    """
    return Registry(
        items=MappingProxyType({}),
        recipes=MappingProxyType({}),
        buildings=MappingProxyType({}),
        warnings=(),
        unknown_groups=(),
        source_sha256=source_sha256,
    )


def registry_codes(check: build.RegistryCheck) -> list[str]:
    """The warning codes a registry check carries, in order, duplicates kept.

    Args:
        check: The published model.

    Returns:
        The codes.
    """
    return [warning.code for warning in check.warnings]


def test_a_registry_built_from_other_bytes_raises_the_registry_mismatch() -> None:
    check = build.registry_check_of(registry(SOURCE_HASH), pinned_docs_sha256=OTHER_HASH)
    assert registry_codes(check) == [build.WARN_REGISTRY_MISMATCH]
    assert check.source_sha256 == SOURCE_HASH
    assert check.pinned_sha256 == OTHER_HASH
    assert check.compared is True
    assert check.matches is False


def test_a_registry_built_from_the_pinned_bytes_raises_nothing() -> None:
    check = build.registry_check_of(registry(SOURCE_HASH), pinned_docs_sha256=SOURCE_HASH)
    assert check.warnings == ()
    assert check.compared is True
    assert check.matches is True


def test_equal_hashes_held_in_distinct_objects_raise_nothing() -> None:
    """Equality is by VALUE: the two digests are built apart at run time."""
    source = "".join(list(SOURCE_HASH))
    pinned = "".join(list(SOURCE_HASH))
    assert source is not pinned, "the fixture no longer holds two distinct objects"
    check = build.registry_check_of(registry(source), pinned_docs_sha256=pinned)
    assert check.warnings == ()
    assert check.matches is True


def test_a_registry_with_no_byte_source_is_unverified_never_a_match() -> None:
    check = build.registry_check_of(registry(None), pinned_docs_sha256=SOURCE_HASH)
    assert registry_codes(check) == [build.WARN_REGISTRY_UNVERIFIED]
    assert check.source_sha256 is None
    assert check.compared is False
    assert check.matches is False, "a registry with no byte source was read as a match"


@pytest.mark.parametrize("pinned", [None, ""], ids=["none", "empty"])
def test_no_pinned_docs_hash_is_unverified_never_a_mismatch(pinned: str | None) -> None:
    """An absent pin names no hash to differ from, so the mismatch code is wrong.

    The empty arm is ``clockspeed/data/version.py::DOCS_SHA256`` as it reads
    when the pin carries no docs hash.
    """
    check = build.registry_check_of(registry(SOURCE_HASH), pinned_docs_sha256=pinned)
    assert registry_codes(check) == [build.WARN_REGISTRY_UNVERIFIED]
    assert check.compared is False
    assert check.matches is False


def test_an_empty_source_hash_is_unverified() -> None:
    check = build.registry_check_of(registry(""), pinned_docs_sha256=SOURCE_HASH)
    assert registry_codes(check) == [build.WARN_REGISTRY_UNVERIFIED]


def test_a_build_only_difference_with_equal_bytes_is_not_a_registry_mismatch() -> None:
    """The session 140 ruling: content hash only.

    The save's build differs from the pinned build, which the build check
    names, and the registry's bytes equal the pin's, which this check passes.
    No build parameter exists on the registry check for a build to reach.
    """
    builds = build.build_check_of(world(SAVE_BUILD), pinned_changelist=OTHER_BUILD)
    sources = build.registry_check_of(registry(SOURCE_HASH), pinned_docs_sha256=SOURCE_HASH)
    assert codes(builds) == [build.WARN_BUILD_MISMATCH]
    assert sources.warnings == ()
    parameters = inspect.signature(build.registry_check_of).parameters
    assert sorted(parameters) == ["pinned_docs_sha256", "registry"]


@pytest.mark.parametrize(
    ("source", "pinned", "code"),
    [
        (SOURCE_HASH, OTHER_HASH, build.WARN_REGISTRY_MISMATCH),
        (None, SOURCE_HASH, build.WARN_REGISTRY_UNVERIFIED),
        (SOURCE_HASH, None, build.WARN_REGISTRY_UNVERIFIED),
    ],
    ids=["mismatch", "no-source", "no-pin"],
)
def test_the_registry_warning_is_sourced_here_and_its_detail_carries_no_hash(
    source: str | None, pinned: str | None, code: str
) -> None:
    (warning,) = build.registry_check_of(registry(source), pinned_docs_sha256=pinned).warnings
    assert warning.code == code
    assert warning.source == build.SOURCE_BUILD
    assert warning.subject is None
    assert warning.count == 1
    assert warning.detail
    assert warning.detail.isascii()
    assert SOURCE_HASH not in warning.detail
    assert OTHER_HASH not in warning.detail


def test_the_registry_codes_are_distinct_from_the_build_codes() -> None:
    registry_side = (build.WARN_REGISTRY_MISMATCH, build.WARN_REGISTRY_UNVERIFIED)
    build_side = {build.WARN_BUILD_MISMATCH, build.WARN_BUILD_UNCOMPARED}
    assert len(set(registry_side)) == len(registry_side)
    assert build_side.isdisjoint(registry_side)


def test_the_docs_pin_is_keyword_only() -> None:
    call: Any = build.registry_check_of
    with pytest.raises(TypeError):
        call(registry(), OTHER_HASH)


@pytest.mark.parametrize(
    "pinned",
    [SOURCE_HASH.encode("ascii"), True, 7],
    ids=["bytes", "bool", "int"],
)
def test_a_docs_pin_that_is_not_text_is_refused(pinned: object) -> None:
    """The bytes spelling of the source's OWN hash is the discrimination control."""
    with pytest.raises(TypeError):
        build.registry_check_of(registry(SOURCE_HASH), pinned_docs_sha256=pinned)  # type: ignore[arg-type]


def test_a_source_hash_that_is_not_text_is_refused() -> None:
    forged = registry(None)
    object.__setattr__(forged, "source_sha256", SOURCE_HASH.encode("ascii"))
    with pytest.raises(TypeError):
        build.registry_check_of(forged, pinned_docs_sha256=SOURCE_HASH)


def test_the_registry_check_repr_renders_both_hashes_and_the_warning_count() -> None:
    check = build.registry_check_of(registry(SOURCE_HASH), pinned_docs_sha256=OTHER_HASH)
    rendered = repr(check)
    assert SOURCE_HASH in rendered
    assert OTHER_HASH in rendered
    assert "warnings=1" in rendered
