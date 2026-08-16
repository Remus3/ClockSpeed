"""The world model and ``load_world`` - the one save-layer type a higher layer holds.

WHAT THIS MODULE PROVES, AND WHAT IT CANNOT
---------------------------------------------
``clockspeed/save/world.py`` composes five modules that were each proven
separately. Everything asserted here is therefore about the SEAM rather than
about any one of them, and three seam defects are what the module exists to
catch.

1. **The two version scalars are threaded from the header into the object
   walk.** ``chunks.decompress_body`` discards both and ``objects`` needs both,
   so ``world.py`` is the only place that holds them together. A composer that
   read the transform delta off the header version passes every real-shaped
   fixture, because header 10 covaries with save 36 and header 14 with save 60
   across the whole real library. ``synthetic.SAVE_CROSS`` - header 14 with save
   36 - is the only fixture that separates them, and
   ``test_save_cross_proves_the_composer_threads_both_scalars`` asserts the
   PAIR, because either half alone is satisfied by a single-field composer.

2. **An absent property map is a warning, not a crash.** ``cached_usmap()``
   returns None on a machine with no install and never raises for absence, so
   the no-install path is the DEFAULT path in CI and on any fresh clone.
   ``objects.parse_properties`` takes a non-optional ``PropertyMap``, which is
   the trap: a composer that calls it unconditionally is a ``TypeError`` on
   every machine that has never had the game installed.

3. **Wrapping widens the leak surface.** ``raise ... from exc`` makes the
   CAUSE's text part of the wrapper's formatted traceback. A save is a
   personal-data-bearing artifact (non-negotiables 11 and 12), so the planted
   marker test below asserts over five surfaces rather than over the message.

WHAT IS NOT PROVEN HERE, STATED PLAINLY
-----------------------------------------
Almost every byte parsed below is built by ``tests/save/synthetic.py``, and a
corpus can only ever agree with whoever wrote it. **A green run here is NOT
evidence that ``load_world`` can read a real save**, with exactly two
exceptions: the two skip-if-absent tests at the end of this module, whose
subject was produced by the game rather than by this repo.

Nor is a green run evidence that saves in general are readable. CS-409 routes
the default load to ``objects.parse_body``, which reads only a body whose
``(header version, save version)`` pair is in ``objects.MEASURED_BODY_LAYOUTS``.
THAT SET IS NOT RESTATED HERE. It grew under CS-407 and this paragraph did not
follow it - it went on naming a single readable pair and refusing the rest long
after every real pair had been measured, which is the same drift CS-418 removed
from ``world.py`` and from this sentence in one pass. The refusal is asserted
against the constant rather than against a list written down here, by
``test_every_fixture_pair_outside_the_measured_set_is_refused``. What a measured
pair buys is a SKELETON walk, whose limits ``clockspeed/save/world.py``'s module
docstring states; a reader who takes a green run here for "the save reader reads
saves" is making a larger mistake than any pair count could express.

The flat-bodied corpus is therefore loaded through ``_load_flat``, which names
``world.BODY_LAYOUT_FLAT`` at every call site. That verbosity is the point: a
silent fallback from the levelled reader to the flat one would keep all of this
green while returning a wrong record count for a real world, which is precisely
the defect CS-409 removed.

Unlock state is NOT parsed by anything in this project. ADR 0004 measured which
FIELDS exist; it did not measure their serialized grammar, and ``world.py``'s
one producer of the published state returns its empty constant with no read of
its own. So the assertions below pin an HONESTLY EMPTY unlock state carrying a
warning that says that grammar is unmeasured, per non-negotiable 7. An empty
unlock set that says so is correct; a fabricated one is not, and ADR 0004
requires both a fresh-shaped and a mature-shaped world be asserted because a
fixture built only from a mature world stays green through exactly the defect
that reports a mature world's state for a fresh one.

THE TRACEBACK RENDERING BELOW IS THE ASSERTION, NOT AN EMISSION
------------------------------------------------------------------
``test_no_planted_string_reaches_any_world_load_error_surface`` formats the
traceback of every wrapped error precisely so it can assert that no planted
marker reaches it. That is the same shape ``tests/save/test_header.py`` and
``tests/save/test_objects.py`` already carry, and all three - this module
included - are now recorded in ``tests/test_exception_rendering.py`` as
redaction-ASSERTION waivers, asserted live by
``test_every_waiver_is_still_live``. Deleting the traceback rendering below
would delete the only check of that channel AND strand that waiver.

THE ONE SURFACE THAT IS NOT THIS MODULE'S OWN CODE
-----------------------------------------------------
pytest renders a failing frame's ARGUMENTS. The frame that raises inside
``load_world_from_bytes`` holds a whole save's BYTES, so on a REAL save an
escaping ``WorldLoadError`` prints the header options string - platform,
account id and player display name in plaintext - into the test log. That is
non-negotiable 12 by way of the test runner rather than the parser, and it was
OBSERVED in this module's own red run rather than theorised. The two real-save
tests therefore load through ``_load_real_save_or_skip``, which catches the
refusal and re-reports it as closed-vocabulary field values with no exception in
flight and ``pytrace`` suppressed.

Every helper here that reaches the real library is contained on BOTH halves -
the discovery and the read - and every one of them is graded by forcing a
failure through it, in the CS-427 section at the foot of this module. An
ungraded containment is a claim; two helpers being contained was never evidence
about a third.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import re
import traceback
from collections.abc import Callable
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.data.locate import ENV_ACCOUNT_DIR, ENV_GAME_DIR, ENV_LOCAL_CONFIG, ENV_SAVE_ROOT
from clockspeed.save import chunks, header, objects, usmap, workdir, world

# IMPORTED, NEVER COPIED, for the reason ``tests/save/test_decode_oracles.py``
# states at its own import of this module: ``_library_save_paths`` closes the
# discovery leak its docstring describes, and each of ``_explode``,
# ``_raise_memory_error``, ``_contained_call`` and ``_assert_sweep_declines``
# is a piece of a containment grader. A third transcription of either is a
# third place to get it subtly wrong. The module is imported whole so every use
# site says out loud where the value came from.
from tests.save import synthetic, test_properties, test_usmap

# ---------------------------------------------------------------------------
# Local constants, so no assertion compares against a bare literal
# ---------------------------------------------------------------------------

_HEADER_10: Final = 10
_HEADER_13: Final = 13
_HEADER_14: Final = 14
_UNSUPPORTED_HEADER_VERSION: Final = 99

_SAVE_36: Final = 36
_SAVE_42: Final = 42
_SAVE_60: Final = 60

#: A save version in no real file and in no measured table. The refusal cases
#: below need one, and 42 stopped being one when CS-407 measured its delta.
_UNMEASURED_SAVE_VERSION: Final = 97

_NARROW_PREFIX: Final = 4
_WIDE_PREFIX: Final = 8

_DELTA_36: Final = 4
_DELTA_42: Final = 4

_TRIPLE: Final = 3

#: Enough records that the body exceeds a deliberately tiny chunk size, so two
#: fixtures can differ in CHUNK COUNT without needing a hundred kilobytes.
_TINY_CHUNK_BYTES: Final = 96

#: A mature-shaped world under ADR 0004 - many records rather than the handful
#: a fresh onboarding world carries. The NUMBER is arbitrary; the SHAPE is not.
_MATURE_RECORD_COUNT: Final = 40

_ROOT: Final = "Persistent_Level:PersistentLevel"

#: The keyword the caller picks a body layout with, and a value that is not one.
#: The bad value is asserted ABSENT from the refusal's message: a layout string
#: is caller-supplied rather than save-read, but echoing an argument back is the
#: habit that eventually echoes one holding save content.
_LAYOUT_PARAMETER: Final = "body_layout"
_NOT_A_LAYOUT: Final = "NotALayoutMarker"

_KNOWN_CLASS_PATH_A: Final = "/Synthetic/Parts/Build_SyntheticSmelter.Build_SyntheticSmelter_C"
_KNOWN_CLASS_NAME_A: Final = "Build_SyntheticSmelter_C"
_KNOWN_CLASS_NAME_B: Final = "Build_SyntheticBelt_C"

#: A resource-node class path. The CLASS NAME is the one ADR 0003 measured -
#: 459 of them in the pinned world, every one carrying a valid transform. The
#: namespace in front of it is synthetic.
_NODE_CLASS_PATH: Final = "/Synthetic/World/BP_ResourceNode.BP_ResourceNode_C"
_NODE_CLASS_NAME: Final = "BP_ResourceNode_C"
_NODE_TRANSLATION: Final = (128.0, 256.0, 0.5)

#: A second measured node class, so the CS-430 count below cannot be satisfied
#: by a helper that de-duplicates on the class name.
_SECOND_NODE_CLASS_PATH: Final = "/Synthetic/World/BP_ResourceDeposit.BP_ResourceDeposit_C"
_SECOND_NODE_CLASS_NAME: Final = "BP_ResourceDeposit_C"

#: A class that is NOT a measured node class. Used as the unmodelled record the
#: CS-430 acceptance requires the flagged one to be distinguishable from.
_NON_NODE_CLASS_PATH: Final = "/Synthetic/Parts/Build_SyntheticInput.Build_SyntheticInput_C"

# ---------------------------------------------------------------------------
# Planted markers. Invented, obviously synthetic, and asserted ABSENT from
# every exception surface - so naming them here is the test, not a leak.
# ---------------------------------------------------------------------------

_PLANTED_SAVE_NAME: Final = "PlantedSaveNameMarker"
_PLANTED_OPTIONS: Final = "?PlantedOptionsMarker=1"
_PLANTED_SESSION: Final = "PlantedSessionMarker"
_PLANTED_CLASS_PATH: Final = (
    "/Synthetic/Planted/Build_PlantedClassMarker.Build_PlantedClassMarker_C"
)
_PLANTED_ROOT: Final = "PlantedRootMarker:PersistentLevel"
_PLANTED_INSTANCE: Final = "PlantedInstanceMarker_0"
#: Three INVENTED world tokens. Bandit sees a token-shaped literal and cannot
#: tell an invented one from a real secret, so S105 is suppressed with its code
#: rather than blanket-ignored - PGH bans a bare noqa. What keeps these honest
#: is the same rule the corpus uses: every one starts with ``Clockspeed``, which
#: a real world token never would. No real token is ever written into this repo
#: (non-negotiable 3, CLAUDE.md section 7).
_PLANTED_TOKEN_VALUE: Final = "ClockspeedPlantedTok0"  # noqa: S105
_UNSEEN_TOKEN: Final = "ClockspeedNeverSeen01"  # noqa: S105
_MUTATED_TOKEN: Final = "ClockspeedMutated0001"  # noqa: S105
_PLANTED_TOKENS: Final = (
    "PlantedSaveNameMarker",
    "PlantedOptionsMarker",
    "PlantedSessionMarker",
    "PlantedClassMarker",
    "PlantedRootMarker",
    "PlantedInstanceMarker",
    "ClockspeedPlantedTok0",
)

#: Call names that can write, delete or move a file. Acceptance 8: workdir.py
#: is the package's only writer, so NONE of these may appear in world.py.
#: ``os.open`` is on the list because a flags-based write is invisible to a
#: mode-string scan - CS-400 records that a text-level scan returns empty for
#: ``os.open(p, os.O_WRONLY)``.
_WRITE_CAPABLE_CALLS: Final = frozenset(
    {
        "chmod",
        "copy",
        "copy2",
        "copyfile",
        "copytree",
        "hardlink_to",
        "link",
        "makedirs",
        "mkdir",
        "mkstemp",
        "move",
        "remove",
        "removedirs",
        "rename",
        "replace",
        "rmdir",
        "rmtree",
        "symlink_to",
        "touch",
        "truncate",
        "unlink",
        "write",
        "write_bytes",
        "write_text",
        "writelines",
    }
)

#: Every mode character that opens a file for anything but reading.
_WRITE_MODE_CHARACTERS: Final = frozenset("wax+")

#: Packages world.py must never import. ``tools/`` is on the list for the same
#: reason: gates depend on the product and the product never depends on a gate.
_FORBIDDEN_IMPORT_ROOTS: Final = (
    "clockspeed.advisor",
    "clockspeed.audit",
    "clockspeed.progress",
    "clockspeed.solve",
    "clockspeed.surface",
    "tools",
)

_WORLD_SOURCE_PATH: Final = Path(__file__).resolve().parents[2] / "clockspeed" / "save" / "world.py"


# ---------------------------------------------------------------------------
# Fixture builders. Every one of them uses only the PUBLIC helpers in
# tests/save/synthetic.py - that module is owned by a concurrent slice and is
# not edited from here.
# ---------------------------------------------------------------------------


def _records(
    count: int, class_path: str = _KNOWN_CLASS_PATH_A
) -> tuple[synthetic.SyntheticObject, ...]:
    """Build ``count`` structurally identical records."""
    return tuple(
        synthetic.SyntheticObject(class_path, _ROOT, f"SyntheticInstance_{index}")
        for index in range(count)
    )


def _blob(
    *,
    header_version: int = _HEADER_14,
    save_version: int = _SAVE_60,
    objects_: tuple[synthetic.SyntheticObject, ...] = (),
    max_chunk_size: int = synthetic.MAX_CHUNK_SIZE,
    **header_kwargs: object,
) -> bytes:
    """Assemble a whole save from the public synthetic primitives.

    ``synthetic.build_save`` does not expose ``max_chunk_size`` and
    ``_assemble`` is private, so the three public primitives are composed here
    instead of widening a file outside this slice's write-list.
    """
    kwargs: dict[str, object] = {
        "header_version": header_version,
        "save_version": save_version,
    }
    kwargs.update(header_kwargs)
    head = synthetic.build_header(**kwargs)  # type: ignore[arg-type]
    body = synthetic.build_body(objects_, save_version=save_version)
    payload = synthetic.body_with_prefix(body, header_version)
    framing = synthetic.default_framing(header_version)
    return head + synthetic.build_chunks(payload, framing=framing, max_chunk_size=max_chunk_size)


def _planted_blob(**overrides: object) -> bytes:
    """A save whose header strings and record strings are all planted markers."""
    kwargs: dict[str, object] = {
        "save_name": _PLANTED_SAVE_NAME,
        "options": _PLANTED_OPTIONS,
        "session_name": _PLANTED_SESSION,
        "world_token": _PLANTED_TOKEN_VALUE,
        "objects_": (
            synthetic.SyntheticObject(_PLANTED_CLASS_PATH, _PLANTED_ROOT, _PLANTED_INSTANCE),
            synthetic.SyntheticObject(_PLANTED_CLASS_PATH, _PLANTED_ROOT, _PLANTED_INSTANCE + "_1"),
        ),
    }
    kwargs.update(overrides)
    return _blob(**kwargs)  # type: ignore[arg-type]


def _property_map(*class_names: str) -> usmap.PropertyMap:
    """A minimal parsed mapping that models exactly the named classes.

    Constructed directly rather than round-tripped through
    ``synthetic.build_usmap``: CS-404 records that the builder's schema section
    writes a placeholder grammar the real loader does not read, and the shipped-
    grammar builder lives inside ``tests/save/test_usmap.py``. What this test
    needs is a ``PropertyMap`` whose ``schemas`` mapping has known keys, and the
    type is a frozen dataclass, so building one is exact rather than modelled.
    """
    return usmap.PropertyMap(
        names=class_names,
        enums={},
        schemas={
            name: usmap.Schema(name=name, super_name=None, properties=()) for name in class_names
        },
        warnings=(),
        container=usmap.UsmapContainer(
            magic=usmap.USMAP_MAGIC,
            version=0,
            compression_method=usmap.COMPRESSION_NONE,
            compressed_size=0,
            decompressed_size=0,
            header_size=0,
        ),
        body_consumed=0,
    )


def _no_install(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point all four CLOCKSPEED_* overrides at paths that do not exist.

    The same helper ``tests/save/test_usmap.py`` uses. This is the DEFAULT
    environment in CI and on a fresh clone, not an edge case.
    """
    missing = tmp_path / "absent"
    for variable in (ENV_GAME_DIR, ENV_SAVE_ROOT, ENV_ACCOUNT_DIR):
        monkeypatch.setenv(variable, str(missing))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    usmap.clear_cache()


def _install_with_broken_usmap(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An install whose mapping file is PRESENT but unreadable.

    Distinct from absence on purpose: ``cached_usmap`` returns None for "no
    install" and RAISES for "the shipped format changed", and collapsing the two
    would hide a format change behind the value that means no install.
    """
    game_dir = tmp_path / "install"
    mapping = game_dir.joinpath(*usmap.USMAP_RELATIVE)
    mapping.parent.mkdir(parents=True)
    mapping.write_bytes(b"not a property mapping at all")
    monkeypatch.setenv(ENV_GAME_DIR, str(game_dir))
    monkeypatch.setenv(ENV_SAVE_ROOT, str(tmp_path / "absent"))
    monkeypatch.setenv(ENV_ACCOUNT_DIR, str(tmp_path / "absent"))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    usmap.clear_cache()


@pytest.fixture
def isolated_work_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Send workdir's copies under tmp_path so no test writes into the repo."""
    root = tmp_path / "work-root"
    monkeypatch.setenv(workdir.ENV_WORK_ROOT, str(root))
    return root


def _write_save(directory: Path, name: str, blob: bytes) -> Path:
    """Drop a synthetic save on disk. Synthetic bytes only - never a real save."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    target.write_bytes(blob)
    return target


# ---------------------------------------------------------------------------
# CS-409: the corpus is FLAT-BODIED, and every load of it says so.
#
# Almost every fixture in tests/save/synthetic.py is built by ``build_body``,
# which writes the single flat record table CS-407 measured to be a shape NO
# REAL BODY HAS. ``SAVE_LEVELLED_V36`` is the only one built by
# ``build_levelled_body``. So the corpus loads below are not the default path
# and must not silently become it - they name the flat reader, once, here.
#
# THE TWO HELPERS DO NOT DEFAULT ANYTHING. They pass the layout explicitly, so
# the module's own coverage of the DEFAULT lives entirely in the CS-409 section
# further down, where it is asserted on the signature rather than inherited from
# a helper a later test author copies without reading.
# ---------------------------------------------------------------------------


def _load_flat(data: bytes, **kwargs: object) -> world.WorldModel:
    """Load a FLAT-bodied corpus fixture from bytes, saying so at the call site."""
    return world.load_world_from_bytes(
        data,
        body_layout=world.BODY_LAYOUT_FLAT,
        **kwargs,  # type: ignore[arg-type]
    )


def _load_flat_path(path: Path, **kwargs: object) -> world.WorldModel:
    """Load a FLAT-bodied corpus fixture from disk, saying so at the call site."""
    return world.load_world(
        path,
        body_layout=world.BODY_LAYOUT_FLAT,
        **kwargs,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# 1 - all four version fixtures load through the one entry point (CS-402)
# ---------------------------------------------------------------------------

_LOADABLE_FIXTURES: Final = (
    synthetic.SAVE_V36,
    synthetic.SAVE_V52,
    synthetic.SAVE_V60,
    synthetic.SAVE_CROSS,
)


@pytest.mark.parametrize("fixture", _LOADABLE_FIXTURES, ids=lambda save: save.name)
def test_every_version_fixture_loads_through_the_one_entry_point(
    fixture: synthetic.SyntheticSave,
) -> None:
    """Acceptance 1. SAVE_V42 is absent because save 42's delta is UNMEASURED.

    That absence is a property of the format record, not an oversight:
    ``objects.transform_delta`` raises for 42 rather than interpolating one from
    36 and 52, and ``test_a_save_version_with_no_measured_delta_is_refused``
    pins the refusal.
    """
    model = _load_flat(fixture.blob)

    assert isinstance(model, world.WorldModel)
    assert model.header.header_version == fixture.header_version
    assert model.header.save_version == fixture.save_version
    assert model.token == model.header.world_token
    assert len(model.objects.records) == len(fixture.objects)


def test_save_cross_proves_the_composer_threads_both_scalars() -> None:
    """The sharpest assertion in the module - the PAIR, never either half.

    Header 14 with save 36 exists in no real file. Its measured pair is a WIDE
    body prefix with a NARROW transform delta, so a composer that threaded one
    scalar and derived the other passes every other fixture here.
    """
    model = _load_flat(synthetic.SAVE_CROSS.blob)

    assert (model.objects.body_prefix_width, model.objects.transform_delta) == (
        _WIDE_PREFIX,
        _DELTA_36,
    )
    assert (model.objects.header_version, model.objects.save_version) == (_HEADER_14, _SAVE_36)


def test_the_narrow_prefix_fixture_is_dispatched_on_the_header_version() -> None:
    """The other side of the same seam: header 10 is the narrow-prefix branch."""
    model = _load_flat(synthetic.SAVE_V36.blob)

    assert (model.objects.body_prefix_width, model.objects.transform_delta) == (
        _NARROW_PREFIX,
        _DELTA_36,
    )
    assert model.objects.header_version == _HEADER_10


def test_a_multi_chunk_save_loads_as_one_body() -> None:
    """A real save is multi-chunk. A composer that read one chunk reports a truncated world."""
    blob = _blob(objects_=_records(_MATURE_RECORD_COUNT), max_chunk_size=_TINY_CHUNK_BYTES)

    model = _load_flat(blob)

    assert len(model.objects.records) == _MATURE_RECORD_COUNT


# ---------------------------------------------------------------------------
# 2 - the world token half of CS-401
# ---------------------------------------------------------------------------


def test_two_saves_sharing_an_identifier_yield_the_same_token() -> None:
    """Acceptance 2. Four things differ and the token does not.

    Name, play duration, chunk count and body content all change. The token is
    the header's saveIdentifier and nothing else, which is exactly why the
    advice ledger keys on it rather than on a filename that rotates on every
    autosave.
    """
    first = _blob(save_name="SyntheticNameOne", play_duration=0, objects_=_records(1))
    second = _blob(
        save_name="SyntheticNameTwo",
        play_duration=999_999,
        objects_=_records(_MATURE_RECORD_COUNT),
        max_chunk_size=_TINY_CHUNK_BYTES,
    )

    one = _load_flat(first)
    two = _load_flat(second)

    # Every one of the four differences is ASSERTED, not assumed. A stability
    # test whose two inputs are accidentally identical asserts nothing at all.
    assert one.header.play_duration != two.header.play_duration
    assert len(one.objects.records) != len(two.objects.records)
    assert _chunk_count(first) != _chunk_count(second)
    assert first != second  # the save name differs, and is never decoded to check it
    assert one.token == two.token


def _chunk_count(blob: bytes) -> int:
    """How many frames a blob's body is spread across."""
    parsed = header.parse_header(blob)
    return chunks.decompress_body(
        blob, parsed.body_offset, header_version=parsed.header_version
    ).chunk_count


def test_a_different_identifier_yields_a_different_token() -> None:
    """The other half of acceptance 2 - the control for the test above."""
    same = _load_flat(_blob(world_token=synthetic.SYNTHETIC_WORLD_TOKEN))
    other = _load_flat(_blob(world_token=synthetic.SYNTHETIC_WORLD_TOKEN_B))

    assert same.token != other.token


def test_a_token_never_seen_before_returns_a_normal_world_model(
    tmp_path: Path, isolated_work_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Acceptance 2, final clause. An unseen token is a NEW WORLD, never a failure."""
    _no_install(monkeypatch, tmp_path)
    assert isolated_work_root  # the fixture is what keeps the copy out of the repo
    source = _write_save(tmp_path / "saves", "synthetic.sav", _blob(world_token=_UNSEEN_TOKEN))

    model = _load_flat_path(source)

    assert isinstance(model, world.WorldModel)
    assert model.token == _UNSEEN_TOKEN


def test_the_token_is_the_header_identifier_and_not_a_derived_value() -> None:
    """Pinned because a composer that hashed or normalised the token would still be stable."""
    model = _load_flat(synthetic.SAVE_V60.blob)

    assert model.token == synthetic.SYNTHETIC_WORLD_TOKEN


# ---------------------------------------------------------------------------
# 3 - unlock state: absent means EMPTY, on BOTH world shapes (ADR 0004)
# ---------------------------------------------------------------------------

#: The two world shapes ADR 0004 requires every unlock test to cover. A fresh
#: onboarding world carries 14 unlock-related property names against a mature
#: world's 30, and ``mPurchasedSchematics`` is ABSENT on the fresh one.
_UNLOCK_SHAPES: Final = (
    pytest.param(0, id="fresh"),
    pytest.param(_MATURE_RECORD_COUNT, id="mature"),
)


@pytest.mark.parametrize("record_count", _UNLOCK_SHAPES)
def test_an_absent_unlock_array_is_an_empty_set_rather_than_an_error(record_count: int) -> None:
    """Acceptance 3, on both shapes ADR 0004 requires.

    ADR 0004's single most important engineering consequence: an absent array is
    EMPTY, never missing and never an error. A reader that assumes presence
    either crashes on a fresh world or reports a mature world's state for a new
    one, and the second failure produces confident wrong advice.

    A fixture built only from a mature world stays green through exactly that
    defect, which is why both shapes are parametrized rather than one asserted.
    """
    model = _load_flat(_blob(objects_=_records(record_count)))

    assert model.unlocks.purchased_schematics == frozenset()
    assert model.unlocks.recipes == frozenset()
    assert model.unlocks.scanned_resources == frozenset()
    assert dict(model.unlocks.feature_flags) == {}
    assert model.unlocks.current_game_phase is None


def test_the_empty_unlock_state_says_the_grammar_is_unmeasured() -> None:
    """Non-negotiable 7: unknown content is FLAGGED and skipped, never silently wrong.

    An empty unlock set with no warning is indistinguishable from a world that
    genuinely has nothing unlocked. The warning is what makes the emptiness
    honest rather than a fabricated answer.
    """
    model = _load_flat(synthetic.SAVE_V60.blob)

    codes = {warning.code for warning in model.warnings}
    assert world.WARN_UNLOCK_GRAMMAR_UNMEASURED in codes


def test_no_unlock_field_is_ever_fabricated() -> None:
    """The fence. Every unlock collection is empty because nothing reads one today.

    ``world._read_unlocks`` is the only producer of the published state and
    returns the empty constant with no read of its own, so there is no path by
    which a purchased schematic could have arrived. A non-empty collection here
    would mean an invented one.
    """
    for fixture in _LOADABLE_FIXTURES:
        unlocks = _load_flat(fixture.blob).unlocks
        assert not unlocks.purchased_schematics
        assert not unlocks.recipes
        assert not unlocks.scanned_resources
        assert not unlocks.feature_flags
        assert unlocks.is_empty


# ---------------------------------------------------------------------------
# 4 - every sibling error family surfaces as one WorldLoadError
# ---------------------------------------------------------------------------


def _header_failure() -> object:
    """An unsupported header version - header.UnsupportedHeaderVersionError."""
    return _load_flat(
        _planted_blob(header_version=_UNSUPPORTED_HEADER_VERSION, with_save_name=True)
    )


def _header_truncation_failure() -> object:
    """A file that ends inside the header - header.HeaderTruncatedError."""
    return _load_flat(_planted_blob()[:24])


def _chunk_magic_failure() -> object:
    """A corrupted chunk magic - chunks.ChunkFramingError."""
    blob = _planted_blob()
    at = _chunk_offset(blob)
    return _load_flat(blob[:at] + b"\x44\x33\x22\x11" + blob[at + 4 :])


def _chunk_stream_failure() -> object:
    """A corrupted zlib stream - chunks.ChunkDecompressError."""
    blob = _planted_blob()
    at = _chunk_offset(blob) + synthetic.ZLIB_OFFSET_WITH_ALGO
    return _load_flat(blob[:at] + bytes([blob[at] ^ 0xFF]) + blob[at + 1 :])


def _object_version_failure() -> object:
    """A save version with no measured transform delta - objects.UnsupportedSaveVersionError.

    THE VERSION USED HERE CHANGED WHEN 42 WAS MEASURED. It used to be save 42,
    because 42 was the version this project could not read. CS-407 measured its
    delta at 4 against a real body, so 42 no longer refuses anything and a case
    still using it would have gone on asserting a refusal that had quietly
    become a successful parse.

    The replacement is a version that exists in NO real save and in no measured
    table, which is what this case is actually about: an absent key raises
    rather than defaulting to a plausible neighbour's value.
    """
    return _load_flat(
        _planted_blob(header_version=_HEADER_13, save_version=_UNMEASURED_SAVE_VERSION, objects_=())
    )


def _object_truncation_failure() -> object:
    """A body that ends inside the record table - objects.ObjectTruncatedError."""
    blob = _planted_blob()
    parsed = header.parse_header(blob)
    body = chunks.decompress_body(blob, parsed.body_offset, header_version=_HEADER_14).payload
    payload = body[: len(body) - 24]
    head = blob[: parsed.body_offset]
    framing = synthetic.default_framing(_HEADER_14)
    return _load_flat(head + synthetic.build_chunks(payload, framing=framing))


def _chunk_offset(blob: bytes) -> int:
    """Where the first chunk frame starts, read from the header rather than searched."""
    return header.parse_header(blob).body_offset


def _usmap_failure_factory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Callable[[], object]:
    """A present-but-unreadable mapping - usmap.UsmapFormatError.

    The environment is installed INSIDE the returned callable rather than at
    construction time. Setting it eagerly would leave a broken mapping in place
    for every other case in the table, and the usmap stage runs BEFORE the
    object stage - so two cases meant to prove the object family would quietly
    prove the usmap family instead and the table would still look green.
    """

    def call() -> object:
        _install_with_broken_usmap(monkeypatch, tmp_path)
        return _load_flat(_planted_blob())

    return call


_FAILURE_CASES: Final = (
    ("unsupported-header-version", _header_failure, header.HeaderError, "header"),
    ("header-truncated", _header_truncation_failure, header.HeaderError, "header"),
    ("chunk-magic", _chunk_magic_failure, chunks.ChunkError, "chunks"),
    ("chunk-stream", _chunk_stream_failure, chunks.ChunkError, "chunks"),
    ("unmeasured-save-version", _object_version_failure, objects.ObjectError, "objects"),
    ("object-truncated", _object_truncation_failure, objects.ObjectError, "objects"),
)

_FAILURE_PARAMS: Final = tuple(
    pytest.param(call, family, stage, id=name) for name, call, family, stage in _FAILURE_CASES
)


def test_the_failure_cases_all_actually_raise() -> None:
    """The positive control. A wrapping test over cases that succeed asserts nothing."""
    assert len(_FAILURE_CASES) > _TRIPLE
    for _name, call, _family, _stage in _FAILURE_CASES:
        with pytest.raises(world.WorldLoadError):
            call()


@pytest.mark.parametrize(("call", "family", "stage"), _FAILURE_PARAMS)
def test_every_sibling_error_family_surfaces_as_a_world_load_error(
    call: Callable[[], object], family: type[Exception], stage: str
) -> None:
    """Acceptance 4. One catch clause covers the whole layer, and the stage is named.

    The CAUSE is asserted too. A wrapper that swallowed the cause would look
    identical from the outside and would delete the only breadcrumb a debugger
    has.
    """
    with pytest.raises(world.WorldLoadError) as caught:
        call()

    assert isinstance(caught.value.__cause__, family)
    assert caught.value.stage == stage


def test_the_usmap_family_surfaces_as_a_world_load_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The fourth family. A mapping that is PRESENT and unreadable is not absence."""
    call = _usmap_failure_factory(monkeypatch, tmp_path)

    with pytest.raises(world.WorldLoadError) as caught:
        call()

    assert isinstance(caught.value.__cause__, usmap.UsmapError)
    assert caught.value.stage == world.STAGE_USMAP


def test_a_save_version_with_no_measured_delta_is_refused() -> None:
    """An unmeasured delta refuses, and the refusal is the format record.

    RESTATED UNDER CS-407, AND THE SUBJECT CHANGED. This asserted that SAVE_V42
    could not load. Save 42's transform delta has now been MEASURED at 4 - by a
    corroborator independent of the section arithmetic, since every actor
    rotation is a unit quaternion and 17763 of 17763 give one at shift 4 - so
    that fixture loads and the claim it carried is retired rather than loosened.

    What survives is the rule the old case existed to pin: a version with no
    measured delta RAISES instead of defaulting to a neighbour's value. That
    rule needs a version nobody has measured, so it is asserted against one.

    THE FLAT READER IS NAMED HERE ON PURPOSE. A missing TRANSFORM DELTA is a
    different unmeasured thing from a missing BODY LAYOUT, and the levelled
    reader refuses on the layout first - so under the default this test would
    still pass while no longer asserting what it says it asserts.
    """
    assert _UNMEASURED_SAVE_VERSION not in objects.TRANSFORM_DELTA_BY_SAVE_VERSION

    with pytest.raises(world.WorldLoadError) as caught:
        _load_flat(
            _planted_blob(
                header_version=_HEADER_13, save_version=_UNMEASURED_SAVE_VERSION, objects_=()
            )
        )

    assert isinstance(caught.value.__cause__, objects.UnsupportedSaveVersionError)


def test_the_previously_unreadable_save_version_now_loads() -> None:
    """The other half of the correction above, asserted rather than assumed.

    Retiring a refusal is only honest if the thing that used to be refused now
    works. SAVE_V42 was built with an EMPTY object section precisely because
    its delta was unmeasured, so this proves the version dispatch reaches the
    end of the walk - not that a populated header-13 body parses, which is what
    the levelled fixture and the real-save acceptance carry.
    """
    model = _load_flat(synthetic.SAVE_V42.blob)

    assert model.header.save_version == _SAVE_42
    assert model.objects.transform_delta == _DELTA_42
    assert model.objects.records == ()


def test_no_planted_string_reaches_any_world_load_error_surface(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Acceptance 4, the privacy half. Five surfaces, because a clean message is not enough.

    ``args`` can carry a value a message does not render, and ``raise ... from``
    makes the CAUSE's text part of the formatted traceback - which is the leak
    channel this module INTRODUCES and neither sibling has. Rendering the
    traceback here IS the assertion; suppressing it would delete the check.
    """
    cases = [call for _name, call, _family, _stage in _FAILURE_CASES]
    cases.append(_usmap_failure_factory(monkeypatch, tmp_path))

    for call in cases:
        with pytest.raises(world.WorldLoadError) as caught:
            call()
        error = caught.value

        surfaces = [
            str(error),
            repr(error),
            repr(error.args),
            "".join(getattr(error, "__notes__", []) or []),
            "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        ]
        for surface in surfaces:
            for token in _PLANTED_TOKENS:
                assert token not in surface
            assert surface.isascii()


def test_a_world_load_error_message_is_built_only_from_its_two_closed_fields(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Defence in depth. The planted-marker test CANNOT catch this, which is the point.

    A wrapper that appended ``str(cause)`` to its own message would leak nothing
    today, because every sibling guarantees its exception text carries only a
    field name, an offset, an expected and actual length, a version scalar and a
    fixed reason. So the planted-marker test above stays green through exactly
    that change - it was written, mutated and observed to survive it.

    The day a sibling relaxes its taxonomy, that appended text becomes a leak
    with no failing test in between. This pins the MESSAGE SHAPE instead of
    depending on a guarantee owned by another module: the rendering is exactly
    the two closed-vocabulary fields, the cause type is a bare identifier, and
    the attribute set is closed so no third channel can be added quietly.
    """
    cases = [call for _name, call, _family, _stage in _FAILURE_CASES]
    cases.append(_usmap_failure_factory(monkeypatch, tmp_path))
    cases.append(lambda: world.load_world(tmp_path / "there-is-no-such-save.sav"))

    for call in cases:
        with pytest.raises(world.WorldLoadError) as caught:
            call()
        error = caught.value

        assert error.args == (f"save load failed at the {error.stage} stage: {error.cause_type}",)
        assert error.cause_type.isidentifier()
        assert error.stage in world.STAGES
        assert set(vars(error)) == {"stage", "cause_type"}


def test_a_world_load_error_is_not_also_a_sibling_error() -> None:
    """One catch clause covers the layer, and catching it cannot swallow a sibling family."""
    assert issubclass(world.WorldLoadError, Exception)
    for _name, _call, family, _stage in _FAILURE_CASES:
        assert not issubclass(world.WorldLoadError, family)


def test_the_stage_vocabulary_is_closed() -> None:
    """A stage built from content would be an echo path. The set is pinned instead."""
    for _name, _call, _family, stage in _FAILURE_CASES:
        assert stage in world.STAGES
    assert world.STAGE_USMAP in world.STAGES
    assert world.STAGE_COPY in world.STAGES


# ---------------------------------------------------------------------------
# 5 - repr withholds the token, the names and the class paths
# ---------------------------------------------------------------------------


def test_the_world_model_repr_carries_no_token_no_name_and_no_class_path() -> None:
    """Acceptance 5. This is the widest repr in the layer - every consumer holds one.

    A test runner and most loggers repr an object before a human chooses what to
    print, so the rendering has to stay safe even when the parse is wrong.
    """
    blob = _planted_blob()
    model = _load_flat(blob)
    rendered = repr(model)

    for token in _PLANTED_TOKENS:
        assert token not in rendered
    assert synthetic.MAP_NAME not in rendered
    assert rendered.isascii()


def test_the_world_model_repr_renders_the_token_as_the_shared_mask() -> None:
    """``header.masked_token`` already exists. A second mask would be a second surface."""
    model = _load_flat(synthetic.SAVE_V60.blob)

    assert header.masked_token(model.token) in repr(model)
    assert model.token not in repr(model)


def test_the_world_model_repr_renders_counts_and_versions() -> None:
    """A repr that withheld everything would be safe and useless."""
    model = _load_flat(synthetic.SAVE_V60.blob)
    rendered = repr(model)

    assert f"header_version={_HEADER_14}" in rendered
    assert f"save_version={_SAVE_60}" in rendered
    assert f"objects={len(model.objects.records)}" in rendered


def test_the_resource_node_repr_withholds_its_strings() -> None:
    """A node's instance name is world content and is withheld for the same reason."""
    model = _load_flat(_blob(objects_=(_node_record(),)))

    rendered = repr(model.nodes[0])
    assert "SyntheticNode_0" not in rendered
    assert _NODE_CLASS_NAME in rendered


def _node_record() -> synthetic.SyntheticObject:
    """One record whose class name is a measured resource-node class (ADR 0003)."""
    return synthetic.SyntheticObject(_NODE_CLASS_PATH, _ROOT, "SyntheticNode_0")


# ---------------------------------------------------------------------------
# 6 - no install: cached_usmap() is None, and that is the DEFAULT path
# ---------------------------------------------------------------------------


def test_an_absent_property_map_warns_and_still_loads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Acceptance 6. ``cached_usmap`` returns None for absence and NEVER raises for it.

    ``objects.parse_properties`` takes a non-optional ``PropertyMap``, so a
    composer that called it unconditionally is a TypeError on every machine that
    has never had the game installed - which is CI, and every fresh clone.
    """
    _no_install(monkeypatch, tmp_path)

    model = _load_flat(synthetic.SAVE_V60.blob)

    codes = {warning.code for warning in model.warnings}
    assert world.WARN_NO_PROPERTY_MAP in codes
    assert len(model.objects.records) == len(synthetic.SAVE_V60.objects)


def test_an_absent_property_map_claims_nothing_about_unknown_content(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Absence of a registry is not evidence of unmodelled content.

    A walk that flagged every class when no registry was supplied would report a
    world of pure unknown content rather than a world it has not checked.
    """
    _no_install(monkeypatch, tmp_path)

    model = _load_flat(synthetic.unknown_actor_class().blob)

    assert model.objects.unknown_classes == ()
    assert model.contains_unmodeled_content is False


def test_a_supplied_property_map_suppresses_the_absent_map_warning() -> None:
    """The warning reports a real state rather than firing unconditionally."""
    model = _load_flat(
        synthetic.SAVE_V60.blob,
        property_map=_property_map(_KNOWN_CLASS_NAME_A, _KNOWN_CLASS_NAME_B),
    )

    codes = {warning.code for warning in model.warnings}
    assert world.WARN_NO_PROPERTY_MAP not in codes


# ---------------------------------------------------------------------------
# 7 - unmodelled content is a reported state, never a failure
# ---------------------------------------------------------------------------


def test_contains_unmodeled_content_is_true_when_a_class_is_not_modelled() -> None:
    """Acceptance 7, the true half. BOOTSTRAP.md section 9 requires the explicit report."""
    model = _load_flat(
        synthetic.unknown_actor_class().blob,
        property_map=_property_map(_KNOWN_CLASS_NAME_A),
    )

    assert model.contains_unmodeled_content is True
    assert len(model.objects.unknown_classes) == 1


def test_contains_unmodeled_content_is_false_when_every_class_is_modelled() -> None:
    """Acceptance 7, the false half. Without it, a hardcoded True passes."""
    model = _load_flat(
        synthetic.SAVE_V60.blob,
        property_map=_property_map(_KNOWN_CLASS_NAME_A, _KNOWN_CLASS_NAME_B),
    )

    assert model.contains_unmodeled_content is False
    assert model.objects.unknown_classes == ()


def test_an_unknown_class_does_not_stop_the_walk() -> None:
    """The release valve: the record is recorded, stepped over, and the walk finishes."""
    fixture = synthetic.unknown_actor_class()

    model = _load_flat(fixture.blob, property_map=_property_map(_KNOWN_CLASS_NAME_A))

    assert len(model.objects.records) == len(fixture.objects)


# ---------------------------------------------------------------------------
# Resource nodes - geometry yes, semantics no (ADR 0003)
# ---------------------------------------------------------------------------


def test_a_resource_node_actor_is_recovered_with_its_placement() -> None:
    """ADR 0003: 626 node actors, 626 valid transforms. Geometry is free and exact."""
    model = _load_flat(
        _blob(objects_=(_node_record(), synthetic.SyntheticObject(_KNOWN_CLASS_PATH_A, _ROOT, "x")))
    )

    assert len(model.nodes) == 1
    assert model.nodes[0].class_name == _NODE_CLASS_NAME
    assert model.nodes[0].translation == _NODE_TRANSLATION


def test_a_world_with_no_node_actors_has_no_nodes() -> None:
    """The control. Without it, a node list built from every record would pass above."""
    model = _load_flat(synthetic.SAVE_V60.blob)

    assert model.nodes == ()


def test_node_semantics_are_reported_as_unavailable_rather_than_guessed() -> None:
    """ADR 0003's negative result, which matters as much as the positive one.

    Purity and resource type are level-asset defaults that are never written to
    the save at all, so a node carries placement and nothing else. Reporting
    that is what keeps degraded mode honest instead of quietly partial.
    """
    model = _load_flat(_blob(objects_=(_node_record(),)))

    codes = {warning.code for warning in model.warnings}
    assert world.WARN_NODE_SEMANTICS_UNAVAILABLE in codes
    assert not hasattr(model.nodes[0], "purity")
    assert not hasattr(model.nodes[0], "resource_class")


# ---------------------------------------------------------------------------
# CS-430 - a measured node class carrying NO transform is FLAGGED, not dropped
#
# THE SKIP IS CORRECT AND IS NOT WHAT THIS SECTION CHANGES. ``world.py`` states
# that such a record is "skipped rather than published with invented
# coordinates", and publishing one would be the confident-wrong-answer outcome
# non-negotiable 7 rules out. Only the SILENCE was the defect: the record left
# the node list with nothing in the warning stream to say a measured node class
# had been lost, so a world short one node was indistinguishable from a world
# that genuinely has that many.
#
# THE ONLY PATH THAT PRODUCES ``transform is None`` TODAY IS A COMPONENT RECORD
# IN THE LEVELLED WALK - ``objects.parse_object_headers`` builds a transform
# unconditionally, and ``objects``' levelled reader builds one only on the ACTOR
# branch. So every fixture here is levelled, and the record under test is a
# component whose class name is one ADR 0003 measured.
#
# EVERY LOAD BELOW SUPPLIES A PROPERTY MAP. That is not decoration: it pins
# ``unknown_classes`` on both sides of the distinction the acceptance requires,
# and it keeps the world-source warning list identical on a machine with an
# install and on one without, where ``cached_usmap`` contributes warnings of its
# own.
# ---------------------------------------------------------------------------


def _levelled_blob(
    *,
    objects_: tuple[synthetic.SyntheticObject, ...] = (),
    components: tuple[synthetic.SyntheticComponent, ...] = (),
) -> bytes:
    """A whole save whose body uses the MEASURED levelled layout of one pair.

    Composed from the public synthetic primitives for the reason :func:`_blob`
    gives - ``synthetic._assemble_levelled`` is private and that module is
    outside this slice's write-list. Header 10 with save 36 is the pair
    ``synthetic.SAVE_LEVELLED_V36`` is built on, so the layout is a measured one
    and the load takes the DEFAULT levelled route rather than the flat one.

    Args:
        objects_: Actor records for the persistent level.
        components: Component records for the persistent level. These are the
            records that arrive carrying no transform.

    Returns:
        The save bytes.
    """
    persistent = synthetic.SyntheticLevel(
        name=None,
        objects=objects_,
        components=components,
        second_collectables=(synthetic.SyntheticCollectable(),),
    )
    body = synthetic.build_levelled_body(
        (),
        persistent,
        header_version=_HEADER_10,
        save_version=_SAVE_36,
    )
    head = synthetic.build_header(header_version=_HEADER_10, save_version=_SAVE_36)
    payload = synthetic.body_with_prefix(body, _HEADER_10)
    framing = synthetic.default_framing(_HEADER_10)
    return head + synthetic.build_chunks(payload, framing=framing)


def _untransformed_node(
    class_path: str, instance: str, *, parent: str | None = None
) -> synthetic.SyntheticComponent:
    """One component record - hence no transform - of the given class.

    Args:
        class_path: The record's class path.
        instance: Its instance name.
        parent: The parent path it closes with. Defaulted by the synthetic
            builder when omitted; supplied by the detail-truth oracle below,
            which needs the path to name a record in the SAME table.

    Returns:
        The component record.
    """
    if parent is None:
        return synthetic.SyntheticComponent(class_path, _ROOT, instance)
    return synthetic.SyntheticComponent(class_path, _ROOT, instance, parent_object_root=parent)


def _world_codes(model: world.WorldModel) -> list[str]:
    """The codes this MODULE raised, in order, with every carried one dropped.

    Filtered on the source rather than asserted over the whole stream, so the
    assertions below say the same thing on a machine with a game install as on
    one without - ``cached_usmap`` contributes warnings of its own on the first.
    """
    return [warning.code for warning in model.warnings if warning.source == world.SOURCE_WORLD]


def test_a_node_class_record_carrying_no_transform_is_flagged_rather_than_dropped() -> None:
    """CS-430. The loss is real, the skip is right, and the silence was the defect.

    The fixture asserts its own premise first: the record reaches the table, its
    class name IS one ADR 0003 measured, and its transform IS None. Without
    those three the test could pass against a walk that never produced the
    record at all, which is a different thing entirely and would prove nothing
    about the filter.
    """
    model = world.load_world_from_bytes(
        _levelled_blob(components=(_untransformed_node(_NODE_CLASS_PATH, "SyntheticNode_0"),)),
        property_map=_property_map(_NODE_CLASS_NAME),
    )

    # The premise: the record is here, it is a measured node class, and it
    # carries no transform.
    (record,) = model.objects.records
    assert objects.class_name_of(record.type_path) in world.NODE_CLASS_NAMES
    assert record.transform is None
    # The skip is PRESERVED. Publishing invented coordinates is the outcome
    # non-negotiable 7 forbids, and this item does not change it.
    assert model.nodes == ()
    # And the loss is now named.
    assert world.WARN_NODE_TRANSFORM_ABSENT in _world_codes(model)


def test_a_lost_node_is_distinguished_from_a_record_of_an_unmodelled_class() -> None:
    """CS-430 acceptance. Both are dropped by the same filter; only one is a LOSS.

    ``_node_or_none`` returns None for two unrelated reasons and the generator
    filter cannot tell them apart. A record of a class this project does not
    model is not a lost node - it is already reported through
    ``unknown_classes``, which is the channel that exists for it - so flagging
    it here would turn every non-node record in a world into a node warning.

    The two parses differ in ONE class path and are asserted to differ in the
    warning stream by EXACTLY the new code, which is what makes this a
    distinction rather than a pair of independent observations. A test that
    merely showed some warning fired would be satisfied by an implementation
    that flagged both.
    """
    lost_node = world.load_world_from_bytes(
        _levelled_blob(components=(_untransformed_node(_NODE_CLASS_PATH, "SyntheticNode_0"),)),
        property_map=_property_map(_NODE_CLASS_NAME),
    )
    unmodelled = world.load_world_from_bytes(
        _levelled_blob(components=(_untransformed_node(_NON_NODE_CLASS_PATH, "SyntheticInput_0"),)),
        property_map=_property_map(_NODE_CLASS_NAME),
    )

    # Neither yields a node, so the node list cannot be where they differ.
    assert lost_node.nodes == ()
    assert unmodelled.nodes == ()
    # The unmodelled one is reported through the channel that owns it, and the
    # lost node is NOT unmodelled content - its class is one this project names.
    assert unmodelled.contains_unmodeled_content is True
    assert lost_node.contains_unmodeled_content is False
    # Asserted as what IS there on both sides, not as an absence on one.
    assert _world_codes(lost_node) == [
        world.WARN_UNLOCK_GRAMMAR_UNMEASURED,
        world.WARN_NODE_TRANSFORM_ABSENT,
    ]
    assert _world_codes(unmodelled) == [world.WARN_UNLOCK_GRAMMAR_UNMEASURED]


def test_a_node_actor_that_does_carry_a_transform_raises_no_absence_warning() -> None:
    """The negative control. Without it, warning on every node class passes above.

    Same levelled fixture, same class, an ACTOR instead of a component - so the
    record carries a transform and the node is published. The two node warnings
    are mutually exclusive here, and asserting both directions is what stops a
    fix that flags the whole class.
    """
    model = world.load_world_from_bytes(
        _levelled_blob(objects_=(synthetic.SyntheticObject(_NODE_CLASS_PATH, _ROOT, "Node_0"),)),
        property_map=_property_map(_NODE_CLASS_NAME),
    )

    assert [node.class_name for node in model.nodes] == [_NODE_CLASS_NAME]
    assert _world_codes(model) == [
        world.WARN_UNLOCK_GRAMMAR_UNMEASURED,
        world.WARN_NODE_SEMANTICS_UNAVAILABLE,
    ]


def test_the_absence_warning_counts_every_lost_node_rather_than_firing_once() -> None:
    """The count is the only thing that says HOW MUCH geometry is missing.

    Two lost nodes of two DIFFERENT measured classes, so neither a hardcoded
    count of 1 nor a de-duplication on the class name survives. The published
    node in the same world is asserted intact, so the count cannot be read as
    covering it.
    """
    model = world.load_world_from_bytes(
        _levelled_blob(
            objects_=(synthetic.SyntheticObject(_NODE_CLASS_PATH, _ROOT, "Node_0"),),
            components=(
                _untransformed_node(_NODE_CLASS_PATH, "SyntheticNode_1"),
                _untransformed_node(_SECOND_NODE_CLASS_PATH, "SyntheticDeposit_0"),
            ),
        ),
        property_map=_property_map(_NODE_CLASS_NAME, _SECOND_NODE_CLASS_NAME),
    )

    assert [node.class_name for node in model.nodes] == [_NODE_CLASS_NAME]
    absent = [w for w in model.warnings if w.code == world.WARN_NODE_TRANSFORM_ABSENT]
    assert [warning.count for warning in absent] == [2]
    semantics = [w for w in model.warnings if w.code == world.WARN_NODE_SEMANTICS_UNAVAILABLE]
    assert [warning.count for warning in semantics] == [1]


def test_a_levelled_world_with_no_node_records_raises_neither_node_warning() -> None:
    """The silent control for the whole section.

    A component of a non-node class is the ordinary shape - every real body
    carries them - and a walk that flagged it would report a warning per
    component on every world ever loaded.

    ITS PREMISE IS ASSERTED because the payload of the test is two ABSENCES, and
    absences are what a fixture that stopped producing a record would deliver
    for free. A silent control that passes on an empty table controls for
    nothing: it would report both warnings quiet because there was nothing to
    warn about, which is the vacuous green rather than the property.
    """
    model = world.load_world_from_bytes(
        _levelled_blob(components=(_untransformed_node(_NON_NODE_CLASS_PATH, "SyntheticInput_0"),)),
        property_map=_property_map(_KNOWN_CLASS_NAME_A),
    )

    # The premise: the record IS here, it DOES carry no transform, and its class
    # is NOT a measured node class. Those three are what make the two absences
    # below a statement about the filter rather than about an empty table.
    (record,) = model.objects.records
    assert record.transform is None
    assert objects.class_name_of(record.type_path) not in world.NODE_CLASS_NAMES
    assert model.nodes == ()
    assert _world_codes(model) == [world.WARN_UNLOCK_GRAMMAR_UNMEASURED]


def test_the_absence_warning_detail_is_fixed_text_that_names_the_condition() -> None:
    """A code with a detail borrowed from another code names nothing.

    The three shipped world codes each carry their own fixed line, and the
    failure this guards is a new code wired to an existing detail - which reads
    as flagged and reports the wrong loss, the same true-sentence-replaced-by-a-
    false-one failure CS-419 shipped one module over.
    """
    model = world.load_world_from_bytes(
        _levelled_blob(components=(_untransformed_node(_NODE_CLASS_PATH, "SyntheticNode_0"),)),
        property_map=_property_map(_NODE_CLASS_NAME),
    )

    (absent,) = [w for w in model.warnings if w.code == world.WARN_NODE_TRANSFORM_ABSENT]
    others = {w.detail for w in model.warnings if w.code != world.WARN_NODE_TRANSFORM_ABSENT}
    assert absent.detail not in others
    assert absent.detail.isascii()
    assert "transform" in absent.detail


# ---------------------------------------------------------------------------
# CS-433 - the detail SENTENCE is graded against the record that raised it
#
# WHAT WAS MISSING, AND IT IS THE DEFECT CS-430 EXISTS TO REMOVE WEARING A
# DIFFERENT MECHANISM. Every check in the section above asks WHICH warning
# fired. None asks whether the warning's SENTENCE is true of the input that
# raised it - and the sentence CS-430 shipped was not. It closed "their
# placement is unrecoverable from this save", and a record reaching that branch
# carries a PARENT PATH: ``objects``' levelled reader builds a transform only on
# the ACTOR branch and closes a COMPONENT with ``parent_object_root`` instead,
# so the one record shape that arrives with no transform is the one shape that
# arrives WITH a route to a placement. Unrecovered by this reader, not
# unrecoverable from the save.
#
# THE DETAIL IS FINISHED OPERATOR-FACING TEXT rather than an internal note:
# ``_WARNING_DETAIL`` authors the sentence, ``_warning`` attaches it unaltered
# and it travels the stream verbatim, so the wording here is shipped text. The
# layer that will display it is a stub today, which changes where the sentence
# is read and not whether it is true.
#
# WHAT THE ORACLE BELOW BUYS, AT ITS REAL STRENGTH. It grades ONE claim class -
# unrecoverability - against ONE measured property of the raising record, on
# ONE warning code. It is not a general truth check on warning prose, and a
# false sentence of any other shape passes it. What it does deliver is that the
# specific claim CS-430 got wrong is now measured against the fixture rather
# than read approvingly, and the measurement is end to end: the route is built,
# parsed back out and asserted present before the sentence is scanned at all.
# ---------------------------------------------------------------------------

#: The instance name of the parent actor the oracle's component points at.
_PARENT_ACTOR_INSTANCE: Final = "Node_0"

#: Phrases asserting the placement cannot be got back OUT OF THE SAVE. A
#: measured parent route refutes the whole class, so the class is banned rather
#: than one wording of it - a detail narrowed to what this READER does needs
#: none of these words, and matching on the exact shipped string would pass the
#: moment someone reworded it and kept the claim.
_UNRECOVERABILITY_CLAIMS: Final = (
    "unrecoverable",
    "irrecoverable",
    "not recoverable",
    "cannot be recovered",
    "can not be recovered",
    "no way to recover",
    "lost for good",
    "gone for good",
)


def test_the_absence_warning_detail_claims_no_loss_the_raising_record_refutes() -> None:
    """CS-433. The sentence is graded against the record, not against itself.

    THE PREMISE IS MEASURED BEFORE THE SENTENCE IS READ, which is the whole
    point - a scan of the detail alone proves nothing about what the save holds.
    The fixture builds a node-class ACTOR carrying a transform and a node-class
    COMPONENT whose parent path names that actor, then asserts, off the parsed
    table: the raising record has no transform, it carries a parent path, and
    that path ends in the instance name of a record in the SAME table that DOES
    carry a transform. Only then is the shipped detail scanned.

    So the route out of the save is demonstrated rather than argued, and a
    detail calling the placement unrecoverable is refuted by the fixture that
    raised it. THIS READER DOES NOT FOLLOW THE ROUTE, and saying so is the
    honest sentence; the skip itself is untouched and is still correct.
    """
    model = world.load_world_from_bytes(
        _levelled_blob(
            objects_=(synthetic.SyntheticObject(_NODE_CLASS_PATH, _ROOT, _PARENT_ACTOR_INSTANCE),),
            components=(
                _untransformed_node(
                    _NODE_CLASS_PATH,
                    "SyntheticNode_1",
                    parent=f"{_ROOT}.{_PARENT_ACTOR_INSTANCE}",
                ),
            ),
        ),
        property_map=_property_map(_NODE_CLASS_NAME),
    )

    # Premise 1 - the raising record is here and it is the flagged condition.
    (raising,) = [
        record
        for record in model.objects.records
        if record.transform is None
        and objects.class_name_of(record.type_path) in world.NODE_CLASS_NAMES
    ]
    # Premise 2 - the save carried a parent path for it. This is the route.
    assert raising.parent, (
        "the record that raised the warning carried no parent path, so the "
        "oracle has not measured a recovery route and its verdict on the "
        "sentence would be vacuous."
    )
    # Premise 3 - that path names a record in the same table that IS placed.
    reachable = [
        record
        for record in model.objects.records
        if record.transform is not None and raising.parent.endswith(f".{record.instance_name}")
    ]
    assert reachable, (
        "the parent path named no placed record in the same table. The fixture "
        "is meant to demonstrate the route end to end, and without a placed "
        "parent it demonstrates only that a string was written."
    )

    (absent,) = [w for w in model.warnings if w.code == world.WARN_NODE_TRANSFORM_ABSENT]
    claimed = [phrase for phrase in _UNRECOVERABILITY_CLAIMS if phrase in absent.detail.lower()]
    assert not claimed, (
        f"the shipped detail claims {claimed} of a record whose placement the "
        f"save demonstrably still routes to, through the parent path asserted "
        f"present above. Detail: {absent.detail!r}. The skip is correct and is "
        "not what this grades - what the operator is told about the loss has to "
        "match the record, and 'this reader does not recover it' is the true "
        "form of the claim. A detail that says nothing about recoverability "
        "passes too."
    )


def test_both_node_warnings_keep_a_fixed_order_when_both_fire() -> None:
    """Mutant W7. The two node warnings are only orderable when both are present.

    The section above pins the order of each node warning against the unlock
    warning, and never with BOTH node warnings in one stream - so hoisting the
    absence warning above the semantics warning reordered the published stream
    and no test moved. One world carrying a placed node AND a lost one is the
    only fixture that can see it.
    """
    model = world.load_world_from_bytes(
        _levelled_blob(
            objects_=(synthetic.SyntheticObject(_NODE_CLASS_PATH, _ROOT, _PARENT_ACTOR_INSTANCE),),
            components=(_untransformed_node(_NODE_CLASS_PATH, "SyntheticNode_1"),),
        ),
        property_map=_property_map(_NODE_CLASS_NAME),
    )

    # The premise: both warnings really are in the stream, so the order below
    # is an ordering rather than a pair of absences agreeing with each other.
    codes = _world_codes(model)
    assert world.WARN_NODE_SEMANTICS_UNAVAILABLE in codes
    assert world.WARN_NODE_TRANSFORM_ABSENT in codes
    assert codes == [
        world.WARN_UNLOCK_GRAMMAR_UNMEASURED,
        world.WARN_NODE_SEMANTICS_UNAVAILABLE,
        world.WARN_NODE_TRANSFORM_ABSENT,
    ]


# ---------------------------------------------------------------------------
# 8 - this module is not the writer
# ---------------------------------------------------------------------------


def _world_ast() -> ast.Module:
    """Parse world.py from source. Read rather than imported - a scan, not a run."""
    return ast.parse(_WORLD_SOURCE_PATH.read_text(encoding="utf-8"))


def test_the_world_module_has_no_write_capable_call_site() -> None:
    """Acceptance 8. ADR 0007 decision item 6 made this a STATIC assertion, not a habit.

    Confining the package's single write to ``workdir.py`` is what turns "no
    other save module writes" into something a machine checks rather than
    something a reviewer remembers.
    """
    found: list[str] = []
    for node in ast.walk(_world_ast()):
        if not isinstance(node, ast.Call):
            continue
        name = _called_name(node)
        if name in _WRITE_CAPABLE_CALLS:
            found.append(f"{name} at line {node.lineno}")

    assert not found, f"world.py must not write: {found}"


def test_the_world_module_never_calls_os_open() -> None:
    """A flags-based write is invisible to a mode-string scan - CS-400 measured that."""
    for node in ast.walk(_world_ast()):
        if isinstance(node, ast.Call) and _called_name(node) == "open":
            assert not _is_os_open(node), f"os.open at line {node.lineno}"


def test_every_open_in_the_world_module_is_read_binary() -> None:
    """Acceptance 8. The mode is asserted LITERALLY, so a computed mode fails too."""
    modes: list[str] = []
    for node in ast.walk(_world_ast()):
        if not (isinstance(node, ast.Call) and _called_name(node) == "open"):
            continue
        mode = _literal_mode(node)
        assert mode is not None, f"open at line {node.lineno} has no literal mode"
        modes.append(mode)

    assert modes, "world.py must open the save it is asked to load"
    for mode in modes:
        assert mode == "rb"
        assert not (_WRITE_MODE_CHARACTERS & set(mode))


def _called_name(node: ast.Call) -> str:
    """The bare name of whatever is being called."""
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _is_os_open(node: ast.Call) -> bool:
    """Whether this call is ``os.open`` rather than the builtin."""
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and (func.value.id == "os")
    )


def _literal_mode(node: ast.Call) -> str | None:
    """The literal mode string of an open call, positional or keyword."""
    for keyword in node.keywords:
        if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
            value = keyword.value.value
            return value if isinstance(value, str) else None
    if node.args and isinstance(node.args[0], ast.Constant):
        first = node.args[0].value
        if isinstance(first, str):
            return first
    return None


def test_load_world_does_not_disturb_the_file_it_reads(
    tmp_path: Path, isolated_work_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The runtime half of acceptance 8. The static scan alone proves too little.

    A fingerprint over the whole pretend save directory - entry set, size,
    modification time in nanoseconds and content hash - because a composer could
    leave a lock file, a sidecar or a rewritten copy beside the save and pass a
    check that looked only at the save itself.
    """
    _no_install(monkeypatch, tmp_path)
    assert isolated_work_root
    save_dir = tmp_path / "saves"
    source = _write_save(save_dir, "synthetic.sav", synthetic.SAVE_V60.blob)
    before = _fingerprint(save_dir)

    model = _load_flat_path(source)

    assert model.token == synthetic.SYNTHETIC_WORLD_TOKEN
    assert _fingerprint(save_dir) == before


def _fingerprint(directory: Path) -> dict[str, tuple[int, int, str]]:
    """Size, mtime in nanoseconds and sha256 for every entry in a directory."""
    out: dict[str, tuple[int, int, str]] = {}
    for entry in sorted(directory.rglob("*")):
        if not entry.is_file():
            continue
        stat = entry.stat()
        digest = hashlib.sha256(entry.read_bytes()).hexdigest()
        out[str(entry.relative_to(directory))] = (stat.st_size, stat.st_mtime_ns, digest)
    return out


def test_load_world_copies_before_it_parses(
    tmp_path: Path, isolated_work_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The game holds handles during autosave, so parsing in place eventually fails.

    ``workdir.copy_for_read`` owns the copy and is the package's only writer.
    That the copy actually happened is asserted by its arrival on disk rather
    than by trusting the call.
    """
    _no_install(monkeypatch, tmp_path)
    source = _write_save(tmp_path / "saves", "synthetic.sav", synthetic.SAVE_V60.blob)

    _load_flat_path(source)

    copies = list(isolated_work_root.rglob("*" + workdir.COPY_SUFFIX))
    assert len(copies) == 1
    assert copies[0].read_bytes() == synthetic.SAVE_V60.blob


def test_a_source_that_cannot_be_read_surfaces_as_a_world_load_error(
    tmp_path: Path, isolated_work_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The copy stage is part of the seam, so its failures wear the same wrapper."""
    _no_install(monkeypatch, tmp_path)
    assert isolated_work_root

    with pytest.raises(world.WorldLoadError) as caught:
        world.load_world(tmp_path / "there-is-no-such-save.sav")

    assert isinstance(caught.value.__cause__, workdir.WorkDirError)
    assert caught.value.stage == world.STAGE_COPY


# ---------------------------------------------------------------------------
# Seam discipline and the warning stream
# ---------------------------------------------------------------------------


def test_the_world_model_carries_every_layer_s_warnings() -> None:
    """One stream, so a caller never has to reach into a sub-model to find a flag."""
    blob = _blob(header_version=_HEADER_14, save_version=_SAVE_36)

    model = _load_flat(blob)

    sources = {warning.source for warning in model.warnings}
    assert world.SOURCE_HEADER in sources
    codes = {warning.code for warning in model.warnings}
    assert header.WARN_UNMEASURED_VERSION_PAIR in codes


def _rendered_channels(warning: world.WorldWarning) -> str:
    """Every string-valued channel on one warning, DERIVED from the dataclass.

    Derived rather than listed, and CS-440 is why that is not academic: this
    type grew a ``subject`` field, and the hand-listed rendering that used to
    stand here went on reading three fields and reporting green about a fourth
    it could not see. A field added tomorrow is read here the day it is added.

    Args:
        warning: The warning to render.

    Returns:
        Every string field joined, with a None subject contributing nothing.
    """
    values = [getattr(warning, field.name) for field in fields(warning)]
    return " ".join(value for value in values if isinstance(value, str))


def test_no_world_warning_carries_a_string_read_out_of_the_save() -> None:
    """A warning is an echo path like any other. Every string channel is fixed text."""
    model = _load_flat(_planted_blob(header_version=_HEADER_14))

    assert model.warnings, "the fixture must raise a warning for this to grade anything"
    for warning in model.warnings:
        rendered = _rendered_channels(warning)
        for token in _PLANTED_TOKENS:
            assert token not in rendered
        assert rendered.isascii()


def test_the_warning_leak_guard_opens_the_subject_channel_too() -> None:
    """The control, without which the guard above passes for a helper reading nothing.

    A leak test is only worth what its rendering covers, and the way that test
    fails is silently: it keeps passing while a new channel goes unread. The
    planted marker goes in the field CS-440 added, so this is red if
    :func:`_rendered_channels` ever stops deriving.
    """
    planted = world.WorldWarning(
        source=world.SOURCE_USMAP,
        code=usmap.WARN_UNDECODABLE_NAME,
        detail="a synthetic detail that carries no marker of its own",
        subject=_PLANTED_INSTANCE,
    )

    assert _PLANTED_INSTANCE in _rendered_channels(planted)


def test_the_world_module_imports_no_layer_above_it() -> None:
    """Seam discipline. save/ consumes the layer below it and never reaches up."""
    source = _WORLD_SOURCE_PATH.read_text(encoding="utf-8")

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith(_FORBIDDEN_IMPORT_ROOTS)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(_FORBIDDEN_IMPORT_ROOTS)


def test_the_world_model_is_frozen() -> None:
    """A higher layer holds this object. A mutable one is a shared mutable world state."""
    model = _load_flat(synthetic.SAVE_V60.blob)

    with pytest.raises((AttributeError, TypeError)):
        model.token = _MUTATED_TOKEN  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 10 - CS-409: the body layout a REAL save has, and the refusal for every pair
# whose layout has not been measured
# ---------------------------------------------------------------------------


def _levelled_record_count() -> int:
    """How many records the levelled fixture's levels declare between them.

    Derived from the fixture rather than written down, because a literal here
    would have to be re-derived by hand every time the corpus grows a level.

    Returns:
        The record count, components included.
    """
    return sum(
        level.record_count for level in (*synthetic.LEVELLED_NAMED, synthetic.LEVELLED_PERSISTENT)
    )


def test_the_default_load_reads_the_levelled_body_a_real_save_actually_has() -> None:
    """CS-409 acceptance 1. The DEFAULT path reads the shape a real body has.

    CS-407 measured that no real body is a flat record table, so a composer
    whose default is the flat reader returns an empty or wrong world from a real
    save - the one outcome non-negotiable 7 forbids outright. This asserts the
    LEVEL COUNT as well as the record count: the flat reader reports level_count
    0 by construction, so the level count alone separates the two readers, and
    the record count alone would not.
    """
    model = world.load_world_from_bytes(synthetic.SAVE_LEVELLED_V36.blob)

    assert len(model.objects.records) == _levelled_record_count()
    assert model.objects.level_count == len(synthetic.LEVELLED_NAMED) + 1
    assert not [w for w in model.objects.warnings if w.code == objects.WARN_UNPARSED_DATA_SECTION]


def test_a_pair_with_no_measured_body_layout_is_refused_rather_than_guessed() -> None:
    """CS-409 acceptance 2, and the whole reason the item exists.

    THE FIXTURE CHANGED UNDER CS-407 BECAUSE THE MEASUREMENT DID. This used
    header 14 / save 60, which was then a real pair with no derived layout. Its
    layout has since been measured, so it is no longer evidence about a
    refusal, and pointing this test at it would have asserted a refusal that had
    become a successful parse.

    SAVE_CROSS is the honest remaining case and is a sharper one. Header 14 with
    save 36 occurs in NO real file, so there is no real body of that pair to
    have been measured and none can be manufactured - which is precisely when a
    parser is most tempted to derive a layout from a neighbour that shares one
    of its two version scalars. A refusal is the only honest answer: an empty
    world, a wrong count and a crash are all worse, and the first two are worse
    than the crash because nothing downstream can tell.
    """
    assert (
        synthetic.SAVE_CROSS.header_version,
        synthetic.SAVE_CROSS.save_version,
    ) not in objects.MEASURED_BODY_LAYOUTS

    with pytest.raises(world.WorldLoadError) as caught:
        world.load_world_from_bytes(synthetic.SAVE_CROSS.blob)

    assert isinstance(caught.value.__cause__, objects.UnsupportedBodyLayoutError)
    assert caught.value.stage == world.STAGE_OBJECTS


def test_every_fixture_pair_outside_the_measured_set_is_refused() -> None:
    """The sibling sweep. One refusal proves one branch; the table proves the rule.

    Every pair the corpus carries is checked against
    ``objects.MEASURED_BODY_LAYOUTS`` rather than against a list written here,
    so the day a pair is measured this test follows the measurement instead of
    contradicting it.

    RENAMED UNDER CS-418. It was ``..._and_the_measured_one_is_not``, which
    counted the measured pairs at ONE in its own name and kept saying so after
    the set grew - and a name is the part of a test nobody re-reads.
    The body was already tied to the constant and needed no change, which is the
    whole point: the tied half followed the measurement and the prose half did
    not.
    """
    for fixture in (*_LOADABLE_FIXTURES, synthetic.SAVE_LEVELLED_V36):
        pair = (fixture.header_version, fixture.save_version)
        if pair in objects.MEASURED_BODY_LAYOUTS:
            continue
        with pytest.raises(world.WorldLoadError) as caught:
            world.load_world_from_bytes(fixture.blob)
        assert isinstance(caught.value.__cause__, objects.ObjectError)


def test_the_default_body_layout_is_the_one_a_real_save_needs() -> None:
    """The safe path is the one a caller gets by not thinking about it.

    Asserted on the SIGNATURE rather than on behaviour, because a default is
    exactly the kind of thing a later edit flips while every behavioural test
    that passes the argument explicitly stays green.
    """
    for entry in (world.load_world, world.load_world_from_bytes):
        parameter = inspect.signature(entry).parameters[_LAYOUT_PARAMETER]
        assert parameter.default == world.BODY_LAYOUT_LEVELLED
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


def test_the_flat_layout_is_reachable_only_through_an_explicit_choice() -> None:
    """The corpus keeps working, and says so at every call site.

    A silent try-flat-then-levelled fallback would keep every fixture green and
    would hide exactly the wrong-shape defect this item removes, so the flat
    reader is opt-in and named.
    """
    model = world.load_world_from_bytes(synthetic.SAVE_V60.blob, body_layout=world.BODY_LAYOUT_FLAT)

    assert len(model.objects.records) == len(synthetic.SAVE_V60.objects)
    assert model.objects.level_count == 0


def test_an_unknown_body_layout_is_refused_before_a_byte_is_read() -> None:
    """A caller bug is not a bad save, so it is NOT a WorldLoadError.

    Raised eagerly and from both entry points. A check placed after the header
    parse would report a save defect for a typo in an argument, and a caller
    holding a genuinely broken save would never learn the argument was wrong.
    """
    for entry, argument in (
        (world.load_world_from_bytes, synthetic.SAVE_LEVELLED_V36.blob),
        (world.load_world, Path("there-is-no-such-save.sav")),
    ):
        with pytest.raises(ValueError) as caught:  # noqa: PT011 - the message IS asserted below
            entry(argument, body_layout=_NOT_A_LAYOUT)  # type: ignore[arg-type]
        assert not isinstance(caught.value, world.WorldLoadError)
        assert _NOT_A_LAYOUT not in str(caught.value)


def test_the_body_layout_vocabulary_is_closed() -> None:
    """Two layouts, both named, and nothing else reachable.

    Their DISTINCTNESS is deliberately not asserted here. Both are ``Final``
    string literals, so mypy resolves the comparison statically and rejects
    ``BODY_LAYOUT_LEVELLED != BODY_LAYOUT_FLAT`` as a non-overlapping equality
    check - the type checker proves it at every commit, which is stronger than
    a runtime assertion that only runs when the suite does.
    """
    assert set(world.BODY_LAYOUTS) == {world.BODY_LAYOUT_LEVELLED, world.BODY_LAYOUT_FLAT}
    assert len(world.BODY_LAYOUTS) == len(set(world.BODY_LAYOUTS))


def test_the_module_docstring_records_which_pairs_can_actually_be_read() -> None:
    """A green suite must not be mistaken for "the save reader reads saves".

    RESTATED UNDER CS-407, AND THE LIMIT MOVED RATHER THAN VANISHED. This
    asserted that exactly ONE pair was readable and three were refused. All
    four real pairs now have a measured body SKELETON, so that sentence is
    retired - but the thing it was defending against is not, and the docstring
    is required to carry the new limit instead of quietly dropping the old one.

    The new limit is a byte ratio, not a pair count: roughly three quarters of
    every real body is opaque property payload the walk steps over by declared
    length. A reader who takes "every pair parses" to mean "the format is
    understood" is making a larger mistake than the one this test used to
    catch, so the word SKELETON is asserted to be present.

    THE PAIR COUNT LEFT THIS TEST UNDER CS-418. It asserted ``len(measured) ==
    4``, a number this file restated about a constant it does not own, and one
    the loop below already covers with a better message: a newly measured pair
    fails on the docstring that does not name it rather than on an arithmetic
    mismatch. What remains is the non-empty guard, which is the assertion that
    actually has to be here - an empty set would make the loop vacuous and this
    test would pass while checking nothing.
    """
    docstring = world.__doc__ or ""
    measured = sorted(objects.MEASURED_BODY_LAYOUTS)

    assert measured, "MEASURED_BODY_LAYOUTS is empty, so the loop below checks nothing"
    for header_version, save_version in measured:
        assert f"header {header_version}" in docstring
        assert f"save {save_version}" in docstring
    assert "SKELETON" in docstring, (
        "the docstring no longer states that the measured grammar is a skeleton; "
        "a pair count without that word reads as a claim the format is understood"
    )
    assert "MEASURED_BODY_LAYOUTS" in docstring


# ---------------------------------------------------------------------------
# 11 - CS-418: every claim about another module derives from that module
# ---------------------------------------------------------------------------

#: The claim phrases CS-418 retired from ``world.py``. Each stated, in THIS
#: layer's voice, why no property value is available - a capability and a reason
#: that ``clockspeed/save/objects.py`` owns and that CS-413 moved without this
#: file noticing. They are quoted from the shipped text rather than paraphrased,
#: so this tuple records what was actually wrong instead of describing it.
#:
#: KNOW WHAT THIS HALF DOES NOT DO. It locks the retired WORDING, not the idea:
#: the same false claim in new words passes it, because an absent grep is a
#: claim about the pattern and not about the file. The mechanical half is the
#: AST check below - world.py calls neither reader - and that is what the
#: replacement prose actually rests on.
_RETIRED_PROPERTY_CLAIMS: Final = (
    "never been measured by this project",
    "no code in this project decodes a property value",
    "decodes no property value",
)

#: The two readers in ``objects`` whose capability world.py must not restate,
#: because what they decode is that module's fact and changes when it does.
_PROPERTY_READERS: Final = ("read_properties", "parse_properties")


def _world_docstrings(*, include_module: bool) -> list[tuple[str, str]]:
    """Every docstring in world.py, with the name of whatever carries it.

    Args:
        include_module: Whether to include the module docstring itself.

    Returns:
        ``(owner, text)`` pairs with each docstring's line wrapping collapsed.
        THE COLLAPSE IS LOAD-BEARING: a claim that wraps across two source lines
        is invisible to a substring check run against the raw text, and the
        claims retired here wrapped in the shipped text.
    """
    tree = _world_ast()
    module_doc = ast.get_docstring(tree) if include_module else None
    found = [("<module>", " ".join(module_doc.split()))] if module_doc is not None else []
    found.extend(
        (node.name, " ".join(doc.split()))
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and (doc := ast.get_docstring(node)) is not None
    )
    return found


def test_no_docstring_below_module_level_restates_a_measured_version_pair() -> None:
    """CS-418. The pair list has one home, and this file already proved which one.

    THE DIAGNOSIS IS SITTING IN THE SAME MODULE. The module docstring's pair
    list is checked against ``objects.MEASURED_BODY_LAYOUTS`` by
    ``test_the_module_docstring_records_which_pairs_can_actually_be_read``, and
    it followed CS-407 as that set grew.
    ``load_world_from_bytes`` carried the same list with NOTHING checking it,
    and went on saying a single pair was readable. The tied claim survived; the
    untied one rotted. So every docstring below module level names the constant
    and restates none of its numbers.

    The forbidden set is derived FROM the constant, so this test restates no
    number either - measure a fifth pair and its scalars join the ban with no
    edit here. That is the difference between a guard and a second copy.

    The module docstring is exempt BY NAME rather than by a pattern, because the
    sibling test above requires it to carry exactly what this one forbids
    everywhere else.
    """
    forbidden = {str(scalar) for pair in objects.MEASURED_BODY_LAYOUTS for scalar in pair}
    assert forbidden, "MEASURED_BODY_LAYOUTS is empty, so this test would check nothing"

    below_module = _world_docstrings(include_module=False)
    assert "load_world_from_bytes" in {owner for owner, _ in below_module}, (
        "the collector did not reach the entry point's docstring, so the loop below "
        "would sweep past the one claim this test was filed for"
    )

    for owner, docstring in below_module:
        restated = sorted(forbidden & set(re.findall(r"[0-9]+", docstring)))
        assert not restated, (
            f"the docstring of {owner} restates the version scalars {restated} that "
            "objects.MEASURED_BODY_LAYOUTS owns; name the constant instead"
        )

    entry = inspect.getdoc(world.load_world_from_bytes) or ""
    assert "MEASURED_BODY_LAYOUTS" in entry, (
        "the entry point must name the set that decides which bodies it reads, "
        "rather than describing that set in its own words"
    )


def test_the_world_layer_states_no_property_capability_it_does_not_own() -> None:
    """CS-418. Why this layer publishes no property value is ITS fact, not objects'.

    THE DANGEROUS SHAPE, and the one this test exists for: a REASON that has
    gone wrong carrying a CONCLUSION that is still right. world.py published no
    property value and said the cause was that the object data section's grammar
    had never been measured. CS-413 measured it, the conclusion stayed true, and
    so the sentence went on reading as current.

    THE GROUND TRUTH IS TAKEN FIRST AND FROM THE SYNTHETIC CORPUS, so the
    refutation runs on a machine with no game installed rather than only where a
    real library exists: the levelled walk attributes a payload extent to every
    record it returns, which is precisely what "never located, never measured"
    denies.

    What replaces the borrowed reason is a fact this module can prove about
    itself - it calls NEITHER property reader, so no property value can reach a
    ``WorldModel`` whatever those readers later learn to decode. Asserting that
    by AST is what keeps the replacement wording true if the decoding half of
    CS-413 lands: this layer's emptiness stops depending on the other module's
    capability entirely.
    """
    model = world.load_world_from_bytes(synthetic.SAVE_LEVELLED_V36.blob)

    assert model.objects.records, "no records, so this test would measure nothing"
    assert all(record.body_length > 0 for record in model.objects.records), (
        "the levelled walk attributed no payload extent, so this test cannot show that "
        "the data section is located and the retired claims below are not yet refuted"
    )

    called = {_called_name(node) for node in ast.walk(_world_ast()) if isinstance(node, ast.Call)}
    assert not called & set(_PROPERTY_READERS), (
        "world.py calls a property reader, so what it publishes now DOES depend on what "
        "that reader decodes and its docstrings may no longer say otherwise"
    )

    everywhere = _world_docstrings(include_module=True)
    assert "<module>" in {owner for owner, _ in everywhere}, (
        "the collector did not reach the module docstring, which is where two of the "
        "three retired claims lived"
    )

    for owner, docstring in everywhere:
        restated = [claim for claim in _RETIRED_PROPERTY_CLAIMS if claim in docstring]
        assert not restated, (
            f"the docstring of {owner} restates {restated}: a capability and a reason "
            "objects.py owns, contradicted by the extents measured above"
        )


# ---------------------------------------------------------------------------
# The real library - SKIP IF ABSENT, shapes only, never a value
# ---------------------------------------------------------------------------


def test_a_real_save_is_not_required_by_this_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CI runs with no install and no save. Everything above must still be green.

    Asserted rather than assumed: the whole corpus is re-loaded with all four
    overrides pointed at nothing, which is the environment the rule suite runs
    in. BOTH readers are exercised - the levelled one is the default path and
    therefore the one CI would fail on first.
    """
    _no_install(monkeypatch, tmp_path)

    for fixture in _LOADABLE_FIXTURES:
        assert _load_flat(fixture.blob).token
    assert world.load_world_from_bytes(synthetic.SAVE_LEVELLED_V36.blob).token


def _newest_real_save() -> Path | None:
    """The newest save on this machine, or None.

    IT HOLDS EVERY `Exception` AND EVERY `SystemExit`, stated that way rather
    than as "it never raises" because that absolute is false: a
    `KeyboardInterrupt` still unwinds, deliberately. See the module docstring.

    ``workdir.latest_save`` resolves the account directory, and its own
    docstring promises it never raises for an absent, empty or unresolvable
    one. That is a promise about three states rather than about every state,
    and a privacy claim this module makes cannot rest on another module's
    promise: a failure escaping it unwinds through frames holding the account
    directory, whose NAME is the platform account id (CLAUDE.md section 2,
    non-negotiable 3).

    Nothing is reported about the failure - not even a type name, for the
    reason ``test_properties._library_save_paths`` gives: a type name is safe,
    and a frame that has to unwind to produce one is not.

    Returns:
        The newest save, or None when there is none or the lookup failed.
    """
    try:
        return workdir.latest_save()
    except (Exception, SystemExit):  # a narrower catch lets the account dir unwind
        return None


def _object_stage_scalars_or_skip() -> tuple[int, int, int, int]:
    """Reach a body for the newest real save and return SCALARS ONLY.

    THE WHOLE READ IS INSIDE A GUARD. ``header.read_header`` takes a PATH and
    ``chunks.decompress_body`` takes the save's BYTES, and pytest renders a
    failing frame's arguments - so an escaping error from either publishes an
    absolute path under a home directory (non-negotiable 3) or the header
    options string (non-negotiable 12). The failure is re-reported as the
    error's class name, which is closed vocabulary, with no exception in flight
    and ``pytrace`` suppressed.

    Split out of its caller so the containment is REACHABLE BY A GRADER. While
    it sat inline in a test body nothing could force a failure through it
    without running the test, and an ungraded containment is the exact shape
    this module's siblings shipped and stayed green on.

    Returns:
        ``(header version, world token length, chunk count, payload length)``.
        Skips when there is no library and never returns on a refusal.
    """
    source = _newest_real_save()
    if source is None:
        pytest.skip("no save library on this machine")

    scalars: tuple[int, int, int, int] | None = None
    refusal: str | None = None
    try:
        parsed = header.read_header(source)
        body = chunks.decompress_body(
            source.read_bytes(), parsed.body_offset, header_version=parsed.header_version
        )
        scalars = (
            parsed.header_version,
            len(parsed.world_token),
            body.chunk_count,
            len(body.payload),
        )
    except (OSError, header.HeaderError, chunks.ChunkError) as exc:
        refusal = type(exc).__name__
    # THE BACKSTOP. The three families above are the failures somebody
    # predicted. `MemoryError` is an `Exception` and none of them; `SystemExit`
    # is a `BaseException`, so it is outside `Exception` as well and is named
    # beside it. Either unwinds through `header.read_header(source)` and
    # `source.read_bytes()` - frames whose argument and whose bound `self` are
    # the save path.
    except (Exception, SystemExit) as exc:
        refusal = type(exc).__name__

    if refusal is not None:
        pytest.fail(f"the newest real save did not reach a body: {refusal}", pytrace=False)
    assert scalars is not None
    return scalars


def test_the_real_library_reaches_the_object_stage_when_one_is_present(
    isolated_work_root: Path,
) -> None:
    """Skip-if-absent, and COUNTS ONLY, over the NEWEST save whatever its pair.

    Distinct from the end-to-end test below, which selects a save of a MEASURED
    pair. This one takes whatever ``workdir.latest_save`` returns - most often
    one of the three real pairs whose body layout is unmeasured - and proves
    that the header parse and the chunk walk still reach a body for it. Those
    two stages are version-correct for all four real pairs; only the object
    stage is not, which is why this stops at the payload.
    """
    assert isolated_work_root
    header_version, token_length, chunk_count, payload_length = _object_stage_scalars_or_skip()

    assert header_version in header.SUPPORTED_HEADER_VERSIONS
    assert token_length == header.WORLD_TOKEN_LENGTH
    assert chunk_count >= 1
    assert payload_length > 0


def _one_real_save_path_of_a_measured_pair() -> Path | None:
    """Find a real save whose whole-body layout this project has measured.

    IT HOLDS EVERY `Exception` AND EVERY `SystemExit` - not "it never raises",
    which is false while a `KeyboardInterrupt` still unwinds by design. The path
    is RETURNED and never rendered: ``load_world``
    needs one, and an absolute path under a home directory is personal data
    (non-negotiable 3). Every caller below binds it to a local and passes it
    straight on.

    Discovery goes through ``test_properties._library_save_paths``, which holds
    the locators and the glob inside its own ``try``. They used to run here,
    outside every ``try``, so a failure in any of them unwound through a frame
    holding the account directory - whose NAME is the platform account id.

    THE UNEXPECTED READ FAILURE IS SKIPPED SILENTLY, because this helper
    returns a path rather than a report and has nowhere to record a type name.
    The diagnostic is not lost: :func:`_object_stage_scalars_or_skip` sweeps the
    same library and FAILS on a refusal rather than skipping.

    Returns:
        The path, or None when no such file is reachable on this machine.
    """
    for path in test_properties._library_save_paths():  # noqa: SLF001
        try:
            parsed = header.parse_header(path.read_bytes())
        except (OSError, header.HeaderError):
            continue
        # THE BACKSTOP. `MemoryError` is an `Exception`, `SystemExit` is a
        # `BaseException`, and neither is one of the two above - which is why the
        # pair is named rather than `Exception` alone. Either unwinds through
        # `path.read_bytes()`, whose bound `self` IS the save path, and pytest
        # renders the arguments of every frame it unwinds with no opt-in flag.
        except (Exception, SystemExit):  # noqa: S112 - reporting it IS the leak
            continue
        if (parsed.header_version, parsed.save_version) in objects.MEASURED_BODY_LAYOUTS:
            return path
    return None


def _load_real_save_or_skip() -> world.WorldModel:
    """Load a real save of a measured pair end to end, or skip.

    THE EXCEPTION IS CAUGHT AND REDUCED TO TWO CLOSED-VOCABULARY FIELDS, AND
    THAT IS THE WHOLE POINT OF THIS HELPER. pytest renders a failing frame's
    ARGUMENTS, and the frame that raises inside ``load_world_from_bytes`` has a
    whole real save's bytes as its argument - so an escaping ``WorldLoadError``
    prints the header's options string, which carries the platform, the account
    id and the player display name in plaintext, straight into the test log.
    That is non-negotiable 12 by way of the test runner rather than by way of
    the parser, and it was OBSERVED in this module's own red run before the
    CS-409 fix landed, not theorised.

    The re-report runs with no exception in flight and with ``pytrace``
    suppressed, so neither the frame nor a ``__context__`` chain is rendered.

    Returns:
        The loaded model. Never returns on failure.
    """
    source = _one_real_save_path_of_a_measured_pair()
    if source is None:
        pytest.skip("no real save of a measured body-layout pair is present on this machine")

    model: world.WorldModel | None = None
    refusal: str | None = None
    try:
        model = world.load_world(source)
    except world.WorldLoadError as exc:
        refusal = f"{exc.stage}/{exc.cause_type}"
    # THE BACKSTOP. The family above is the failure somebody predicted.
    # `world.load_world(source)` takes the save path as its ARGUMENT, so any
    # other type renders an absolute path under a home directory on the way
    # out - pytest renders frame arguments with no opt-in flag. `SystemExit` is
    # named beside `Exception` because it is a `BaseException` and `except
    # Exception` does not hold it.
    except (Exception, SystemExit) as exc:
        refusal = type(exc).__name__

    if refusal is not None:
        pytest.fail(f"a real save of a measured pair did not load: {refusal}", pytrace=False)
    assert model is not None
    return model


def test_a_real_save_of_a_measured_pair_loads_end_to_end_into_a_world_model(
    isolated_work_root: Path,
) -> None:
    """THE PAYOFF. The first time anything in this project reads a real world.

    Everything above this line is synthetic, and a corpus can only ever agree
    with whoever wrote it. This is the one assertion in the module whose subject
    was produced by the game, and it runs the WHOLE composition - copy, header,
    chunks, property map, levelled body walk, model - through the single public
    entry point rather than through the stages one at a time.

    IT IS ALSO THE FIRST TEST THAT COULD LEAK A REAL WORLD. Every assertion
    below binds a COUNT or a SCALAR to a local and compares that, so a failure
    renders integers and booleans. No token, no level name, no class path, no
    instance name and no path reaches an assertion, a message or a skip reason,
    and the load itself goes through :func:`_load_real_save_or_skip` because a
    RAISING load renders the save's bytes without either.
    """
    assert isolated_work_root
    model = _load_real_save_or_skip()

    record_count = len(model.objects.records)
    level_count = model.objects.level_count
    token_length = len(model.token)
    pair = (model.objects.header_version, model.objects.save_version)
    unparsed = len(
        [w for w in model.objects.warnings if w.code == objects.WARN_UNPARSED_DATA_SECTION]
    )
    token_matches_header = model.token == model.header.world_token

    assert record_count > 0
    assert level_count > 1
    assert token_length == header.WORLD_TOKEN_LENGTH
    assert token_matches_header
    assert pair in objects.MEASURED_BODY_LAYOUTS
    assert unparsed == 0


def test_a_real_world_model_reprs_without_leaking_it(isolated_work_root: Path) -> None:
    """The repr guarantee, asserted against a REAL world rather than a fixture.

    A planted marker proves the repr withholds a string the fixture put there.
    It cannot prove the repr withholds a string only a real save has - and a
    test runner or a logger reprs an object before a human chooses what to
    print, so this is the surface that decides whether a crash discloses.
    """
    assert isolated_work_root
    model = _load_real_save_or_skip()
    rendered = repr(model)

    # An EMPTY string is in every string, so a blank field would make an
    # absence check pass or fail for a reason that has nothing to do with the
    # repr. Blanks are dropped and the count of what was actually checked is
    # asserted, so this cannot quietly degrade into checking nothing.
    strings = [model.token, model.header.map_name]
    strings.extend(r.type_path for r in model.objects.records)
    strings.extend(r.instance_name for r in model.objects.records)
    checked = [value for value in strings if value]
    leaked = len([value for value in checked if value in rendered])

    assert len(checked) > _TRIPLE
    assert leaked == 0
    assert rendered.isascii()


# ---------------------------------------------------------------------------
# CS-427 - the discovery and the read are contained, and every site is GRADED
#
# Several helpers above reach the real library, and until this section existed
# nothing forced a failure through any of them. Which ones they are is DERIVED
# rather than counted here - ``test_every_library_reaching_function_here_is_
# declared`` reads this module's own AST - so adding one cannot falsify this
# paragraph. Both halves of the containment have a MEASURED leak behind them
# rather than a theorised one:
#
#   THE DISCOVERY. ``locate.resolve_save_root``, ``locate.resolve_account_dir``,
#   the save glob and ``workdir.latest_save`` each sat outside every ``try``, so
#   a failure in any of them unwound through a frame holding the account
#   directory - whose NAME is the platform account id, in a path that also
#   carries the Windows account name (CLAUDE.md section 2, non-negotiable 3).
#
#   THE READ. A catch naming ``OSError`` and a sibling error family names the
#   failures somebody predicted and lets every other type through.
#   ``path.read_bytes()`` unwinds through a bound method whose ``self`` IS the
#   save path, and ``world.load_world(source)`` takes it as an ARGUMENT. pytest
#   renders the ARGUMENTS of every frame it unwinds with NO opt-in flag - so one
#   rendered line carries the Windows account name, the platform account id and
#   the world name together: non-negotiable 3 three times over and
#   non-negotiable 12 once, under completely default flags.
#
#   TWO TYPES FORCE IT, AND ONE HANDLER SHAPE DOES NOT HOLD BOTH. ``MemoryError``
#   is an ``Exception``; ``SystemExit`` is a ``BaseException`` and is not. A
#   containment written as ``except Exception`` holds the first and leaks on the
#   second, and a grader forcing only the first cannot tell those apart - which
#   is why every read grader below is parametrized over both.
#
# EVERY SUBJECT BELOW IS SYNTHETIC. The graders run on a machine with no game
# installed and never put a real path into the frame under test, and every
# assertion is reduced to a type NAME or a boolean first - a test that grades a
# leak must not be the leak.
# ---------------------------------------------------------------------------

#: The helpers whose containment the graders below force a failure through.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_newest_real_save": "wraps workdir.latest_save",
        "_object_stage_scalars_or_skip": "reads the newest save",
        "_one_real_save_path_of_a_measured_pair": "reads every save in the library",
        "_load_real_save_or_skip": "loads a real save through world.load_world",
    }
)

#: Reaches or touches a primitive without being a grader-able library helper,
#: name to why. Asserted still reaching, so none outlives its reason.
_EXEMPT_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_fingerprint": (
            "reads bytes under a tmp_path work root supplied by the caller, "
            "never a discovered save directory"
        ),
        "test_load_world_copies_before_it_parses": (
            "a test rather than a helper, and its read_bytes is on a synthetic "
            "fixture blob written into tmp_path"
        ),
    }
)


def _assert_contained_outcome(label: str, expected: str, call: Callable[[], object]) -> None:
    """Assert a helper ended in the named CONTAINED outcome rather than unwinding.

    Both operands are exception type NAMES, so a failure here renders two class
    names and the label and nothing else. That is deliberate: the helpers under
    test hold a save path, and a grader that rendered one would be the leak it
    grades.

    Args:
        label: What to call the helper in a failure message.
        expected: The type name of the outcome the containment must produce.
        call: The helper.
    """
    escaped, _value = test_properties._contained_call(call)  # noqa: SLF001
    assert escaped == expected, (
        f"the {label} ended in {escaped} rather than {expected}, so the failure was not "
        "contained and every frame it unwound through held a save path"
    )


def test_every_library_reaching_function_here_is_declared() -> None:
    """The reach guard, keyed on the RISKY primitives rather than the safe route.

    An earlier version of this test keyed on the two CONTAINED entry points, so
    a function using the raw locators never entered the flagged set and the
    subset assertion stayed true. It detected safe helpers and was blind to
    unsafe ones. The guard is owned by ``test_properties`` and consumed here, so
    the two sibling modules share one implementation rather than two
    transcriptions.
    """
    test_properties._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


def test_the_guard_catches_a_spliced_uncontained_helper(tmp_path: Path) -> None:
    """The guard's POWER, forced rather than asserted about.

    The splice is the pre-repair shape - the locators and the glob outside every
    ``try``, under a catch naming two families - wired in exactly as the real
    helpers here are. Run against a COPY in ``tmp_path``, so nothing tracked is
    mutated and no restore is needed.
    """
    spliced = tmp_path / "spliced.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + "\n\ndef _spliced_uncontained_helper():\n"
        '    """A helper carrying the known-bad shape."""\n'
        "    root = locate.resolve_save_root()\n"
        "    account = locate.resolve_account_dir(root)\n"
        '    for path in sorted(account.glob("*.sav")):\n'
        "        try:\n"
        "            return header.parse_header(path.read_bytes())\n"
        "        except (OSError, header.HeaderError):\n"
        "            continue\n"
        "    return None\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as caught:
        test_properties._assert_library_reach_is_declared(  # noqa: SLF001
            spliced, graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
        )
    assert "_spliced_uncontained_helper" in str(caught.value)

    # The positive control: the same guard on the unspliced source passes, so
    # the red above is the splice rather than the guard rejecting everything.
    test_properties._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_save_root_lookup_does_not_unwind_through_the_finder(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """The first of the finder's three discovery calls that sat outside its ``try``."""
    monkeypatch.setattr(locate, "resolve_save_root", raiser)
    test_properties._assert_sweep_declines(  # noqa: SLF001
        "measured-pair finder", _one_real_save_path_of_a_measured_pair
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_account_directory_lookup_does_not_unwind_through_the_finder(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """The second, and the one whose frame holds the platform account id."""
    monkeypatch.setattr(locate, "resolve_save_root", lambda: Path("synthetic-root"))
    monkeypatch.setattr(locate, "resolve_account_dir", raiser)
    test_properties._assert_sweep_declines(  # noqa: SLF001
        "measured-pair finder", _one_real_save_path_of_a_measured_pair
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_save_glob_does_not_unwind_through_the_finder(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """The third - it was in the ``for`` statement itself, outside any ``try``."""
    monkeypatch.setattr(Path, "glob", raiser)
    test_properties._assert_sweep_declines(  # noqa: SLF001
        "measured-pair finder", _one_real_save_path_of_a_measured_pair
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_READ_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_read_failure_does_not_unwind_through_the_finder(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., bytes]
) -> None:
    """The narrow catch at the finder's read, forced under BOTH failures.

    ``SystemExit`` is the second parameter because it derives from
    ``BaseException``: a handler written as ``except Exception`` holds
    ``MemoryError`` and lets ``SystemExit`` straight through, and one forced
    failure cannot tell those two containments apart.

    The finder has nowhere to record a type name - it returns a path or None -
    so containment here means declining. ``_object_stage_scalars_or_skip``
    sweeps the same library and fails on a refusal rather than skipping.
    """
    monkeypatch.setattr(
        test_properties,
        "_library_save_paths",
        lambda: (test_properties._SYNTHETIC_SAVE,),  # noqa: SLF001
    )
    monkeypatch.setattr(Path, "read_bytes", raiser)
    test_properties._assert_sweep_declines(  # noqa: SLF001
        "measured-pair finder", _one_real_save_path_of_a_measured_pair
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001,
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_newest_save_lookup_does_not_unwind_through_the_object_stage(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """``workdir.latest_save`` resolves the account directory and sat outside the ``try``.

    Its own docstring promises it never raises for an absent, empty or
    unresolvable directory - which is a promise about those three states and not
    about every state, and this module cannot rest a privacy claim on another
    module's promise.
    """
    monkeypatch.setattr(workdir, "latest_save", raiser)
    test_properties._assert_sweep_declines("newest-save lookup", _newest_real_save)  # noqa: SLF001
    _assert_contained_outcome(
        "object-stage helper", pytest.skip.Exception.__name__, _object_stage_scalars_or_skip
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_READ_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_read_failure_does_not_unwind_through_the_object_stage(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., bytes]
) -> None:
    """``header.read_header`` takes the PATH, so its frame renders one on the way out.

    Forced through ``read_header`` rather than through ``read_bytes`` because
    ``read_header`` runs first and opens the file itself: a synthetic path makes
    it raise ``HeaderReadError`` before the ``read_bytes`` line is ever reached,
    so patching ``read_bytes`` here would grade nothing.
    """
    monkeypatch.setattr(workdir, "latest_save", lambda: test_properties._SYNTHETIC_SAVE)  # noqa: SLF001
    monkeypatch.setattr(header, "read_header", raiser)
    _assert_contained_outcome(
        "object-stage helper", pytest.fail.Exception.__name__, _object_stage_scalars_or_skip
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_READ_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_load_failure_does_not_unwind_through_the_real_save_loader(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., bytes]
) -> None:
    """``except world.WorldLoadError`` is the third narrow catch, and the widest gap.

    ``world.load_world(source)`` takes the save path as its ARGUMENT, so any
    type outside that one family renders an absolute path under a home
    directory the moment pytest unwinds the call.
    """
    monkeypatch.setattr(
        "tests.save.test_world._one_real_save_path_of_a_measured_pair",
        lambda: test_properties._SYNTHETIC_SAVE,  # noqa: SLF001
    )
    monkeypatch.setattr(world, "load_world", raiser)
    _assert_contained_outcome(
        "real-save loader", pytest.fail.Exception.__name__, _load_real_save_or_skip
    )


# ---------------------------------------------------------------------------
# CS-440 - WHICH thing was flagged, and how confident the answer about it is
#
# CS-435 closed on its written acceptance and left two downstream halves open,
# both of them here rather than in ``usmap.py``.
#
# THE FIRST IS THE SUBJECT. Every sub-warning that HAS a subject was carried up
# with the subject stripped off, so a consumer at this layer learned that some
# name did not decode and could not learn WHICH. ``header.HeaderWarning`` and
# ``usmap.UsmapWarning`` both declare one; ``chunks.ChunkWarning`` and
# ``objects.ObjectWarning`` declare none, and the difference is asserted below
# rather than assumed, because "no subject" and "an empty subject" are two
# different facts and collapsing them is the same class of defect as the
# substituted name CS-435 removed.
#
# THE SECOND IS THE REASON. A usmap schema whose own name index does not
# resolve is DROPPED from ``PropertyMap.schemas``, so the class it modelled
# reaches ``objects`` as a path absent from ``known_classes`` and was published
# as "is not a class the supplied registry models" - false for that input. This
# layer is the only one that can see both facts at once, so it is where the
# condition is derived and handed to the walk.
#
# THE KEY IS THE SUBJECT PAIR, AND IT IS A CROSS-MODULE CONTRACT RATHER THAN A
# LOCAL CONVENTION. ``usmap._read_schema`` gives its three failures three
# distinct subjects on purpose (CS-431), and only the bare ``schema-<N>`` one
# drops the schema. A fixture hand-built here would agree with whatever this
# module chose to key on and would prove nothing about the real parser, so
# ``test_a_real_usmap_whose_schema_name_did_not_decode_downgrades_the_reason``
# below runs the REAL ``usmap.parse_usmap`` over patched synthetic bytes and is
# the only test here that grades the key against its actual producer.
# ---------------------------------------------------------------------------

#: The subject shape the usmap layer uses for a schema DROPPED for want of a
#: resolvable name of its own, and the two neighbours that keep their schema.
_DROPPED_SCHEMA_SUBJECT: Final = "schema-0"
_SURVIVING_SCHEMA_SUBJECTS: Final = ("schema-0-super", "schema-0-property")

#: The subject the usmap layer uses when the schema section stops mid-entry and
#: the remaining schemas are never read.
_STOPPED_SECTION_SUBJECT: Final = "schemas"

#: usmap conditions that flag something real and lose no CLASS NAME. Each is
#: asserted NOT to downgrade, because a key that caught them would withdraw a
#: true claim from most mappings.
_COMPLETE_REGISTRY_CODES: Final = (
    usmap.WARN_DUPLICATE_SCHEMA,
    usmap.WARN_TRAILING_SECTION,
    usmap.WARN_UNKNOWN_PROPERTY_TYPE,
)

#: A subject the usmap layer really emits for an undecodable NAME-table entry.
_UNDECODABLE_NAME_SUBJECT: Final = "name-0"

#: Sources whose originating warning type declares no subject field at all.
_SUBJECTLESS_SOURCES: Final = (world.SOURCE_CHUNKS, world.SOURCE_OBJECTS, world.SOURCE_WORLD)


def _map_with_warning(code: str, subject: str, *class_names: str) -> usmap.PropertyMap:
    """A mapping that models ``class_names`` and carries one flagged condition.

    Args:
        code: A ``usmap.WARN_*`` constant.
        subject: The structural token the usmap layer would have flagged.
        *class_names: Class names the mapping still models.

    Returns:
        The mapping.
    """
    base = _property_map(*class_names)
    return usmap.PropertyMap(
        names=base.names,
        enums=base.enums,
        schemas=base.schemas,
        warnings=(
            usmap.UsmapWarning(
                code=code,
                subject=subject,
                detail="a synthetic condition, so no sentence from the usmap layer is copied here",
            ),
        ),
        container=base.container,
        body_consumed=base.body_consumed,
    )


def _reasons_of(model: world.WorldModel) -> set[str]:
    """The distinct reasons a loaded world publishes for its unmodelled classes.

    Args:
        model: The loaded world.

    Returns:
        The distinct reasons.
    """
    return {unknown.reason for unknown in model.objects.unknown_classes}


def test_a_carried_usmap_warning_keeps_the_subject_the_usmap_layer_flagged() -> None:
    """CS-440 acceptance, first clause, on the layer the item names.

    ``UsmapWarning`` declares a subject and the world stream dropped it, so
    ``name-0`` reached nobody. The assertion is on the PAIR - a subject carried
    onto the wrong code would be worse than no subject at all.
    """
    supplied = _map_with_warning(
        usmap.WARN_UNDECODABLE_NAME, _UNDECODABLE_NAME_SUBJECT, _KNOWN_CLASS_NAME_A
    )

    model = _load_flat(synthetic.SAVE_V60.blob, property_map=supplied)

    carried = [(w.code, w.subject) for w in model.warnings if w.source == world.SOURCE_USMAP]
    assert (usmap.WARN_UNDECODABLE_NAME, _UNDECODABLE_NAME_SUBJECT) in carried


def test_a_carried_header_warning_keeps_the_subject_the_header_layer_flagged() -> None:
    """The sibling type that also declares a subject, derived from the header itself.

    Expected pairs are read off ``model.header.warnings`` rather than written
    down, so a header fixture whose warnings change cannot leave this asserting
    nothing.
    """
    model = _load_flat(_blob(header_version=_HEADER_14, save_version=_SAVE_36))

    expected = [(w.code, w.subject) for w in model.header.warnings]
    carried = [(w.code, w.subject) for w in model.warnings if w.source == world.SOURCE_HEADER]
    assert expected, "the fixture must raise a header warning for this to grade anything"
    assert carried == expected


def test_a_source_whose_warning_type_declares_no_subject_carries_none() -> None:
    """A missing subject and an empty subject are different facts, kept different.

    ``ChunkWarning`` and ``ObjectWarning`` declare no subject field, and this
    module's own warnings have nothing structural to name. Rendering that as
    ``""`` would make a missing channel indistinguishable from a present but
    empty one - the same collapse ``usmap._NameTable`` refuses for a name that
    did not decode.
    """
    supplied = _map_with_warning(
        usmap.WARN_UNDECODABLE_NAME, _UNDECODABLE_NAME_SUBJECT, _KNOWN_CLASS_NAME_A
    )

    model = _load_flat(
        _blob(header_version=_HEADER_14, save_version=_SAVE_36), property_map=supplied
    )

    subjectless = [w for w in model.warnings if w.source in _SUBJECTLESS_SOURCES]
    assert subjectless, "the fixture must carry at least one subjectless warning"
    assert all(w.subject is None for w in subjectless)
    assert all(
        w.subject is not None
        for w in model.warnings
        if w.source in (world.SOURCE_HEADER, world.SOURCE_USMAP)
    )


def test_a_registry_that_dropped_a_schema_name_downgrades_the_unknown_class_reason() -> None:
    """CS-440 acceptance, second clause, through the composer that owns the seam.

    The mapping models nothing the save carries AND says one of its own schema
    names did not resolve. "Not modelled" is then a claim the mapping cannot
    support, and publishing it anyway is the confident wrong answer.
    """
    dropped = _map_with_warning(usmap.WARN_UNRESOLVED_NAME, _DROPPED_SCHEMA_SUBJECT)

    model = _load_flat(synthetic.unknown_actor_class().blob, property_map=dropped)

    assert model.contains_unmodeled_content is True
    assert _reasons_of(model) == {objects.REASON_REGISTRY_INCOMPLETE}


def test_a_registry_whose_schema_names_all_resolved_keeps_the_not_modelled_reason() -> None:
    """The control. Without it the test above passes for a walk that downgrades always.

    A downgrade that fired unconditionally would withdraw a TRUE claim from
    every world, which trades one wrong answer for a permanently useless one.
    """
    model = _load_flat(
        synthetic.unknown_actor_class().blob, property_map=_property_map(_KNOWN_CLASS_NAME_A)
    )

    assert model.contains_unmodeled_content is True
    assert _reasons_of(model) == {objects.REASON_CLASS_NOT_MODELLED}


def test_a_registry_whose_schema_section_stopped_early_downgrades_the_reason() -> None:
    """The sibling condition, found by grepping the root cause rather than the symptom.

    ``usmap._read_schemas`` catches a desynchronised entry, flags
    ``WARN_DESYNCHRONISED_SECTION`` against ``schemas`` and RETURNS WHAT IT HAS.
    Every schema after that entry is missing from the mapping, so "is not a
    class the supplied registry models" is false for all of them - the same
    false sentence as the dropped-name case, reached by a different route. A fix
    that keyed only on the unresolved NAME would leave this half of the defect
    standing, which is how CS-435 came to have a downstream half at all.
    """
    stopped = _map_with_warning(usmap.WARN_DESYNCHRONISED_SECTION, _STOPPED_SECTION_SUBJECT)

    model = _load_flat(synthetic.unknown_actor_class().blob, property_map=stopped)

    assert model.contains_unmodeled_content is True
    assert _reasons_of(model) == {objects.REASON_REGISTRY_INCOMPLETE}


@pytest.mark.parametrize("code", _COMPLETE_REGISTRY_CODES)
def test_a_usmap_condition_that_loses_no_class_name_does_not_downgrade(code: str) -> None:
    """The other side of the same grep, and the reason the key is a pair.

    A duplicate schema keeps the later definition under the SAME key, so no
    class name leaves the mapping. Trailing bytes sit past a schema section
    whose declared count was honoured. An unknown property type costs a
    property, not a class. None of the three makes "not modelled" unsupportable,
    and downgrading on them would withdraw a true claim from most real
    mappings.
    """
    supplied = _map_with_warning(code, _DROPPED_SCHEMA_SUBJECT)

    model = _load_flat(synthetic.unknown_actor_class().blob, property_map=supplied)

    assert _reasons_of(model) == {objects.REASON_CLASS_NOT_MODELLED}


@pytest.mark.parametrize("subject", _SURVIVING_SCHEMA_SUBJECTS)
def test_a_schema_subject_that_drops_no_schema_does_not_downgrade_the_reason(subject: str) -> None:
    """CS-431's three subjects exist because they are three different conditions.

    An unresolved SUPER index keeps the schema, and an unresolved PROPERTY name
    drops one property. Neither removes a class from ``schemas``, so neither
    makes "not modelled" unsupportable. Keying on the code alone - or on any
    prefix of the subject - would downgrade both and quietly withdraw a claim
    that was true.
    """
    supplied = _map_with_warning(usmap.WARN_UNRESOLVED_NAME, subject)

    model = _load_flat(synthetic.unknown_actor_class().blob, property_map=supplied)

    assert _reasons_of(model) == {objects.REASON_CLASS_NOT_MODELLED}


def test_a_real_usmap_whose_schema_name_did_not_decode_downgrades_the_reason() -> None:
    """The only test here that grades the key against its actual producer.

    Every other case in this section builds the ``UsmapWarning`` by hand, so it
    agrees with whatever this module decided to key on and is evidence about
    nothing else. This one patches five bytes of a synthetic mapping body,
    parses it with the REAL ``usmap.parse_usmap``, and feeds the result
    straight into the loader - so if the subject vocabulary ever moves, the
    world layer stops recognising it HERE rather than in a real world.

    Synthetic throughout: the bytes come from the shared builder in
    ``tests/save/test_usmap.py`` and no install and no save library is touched,
    which is what lets this run on a bare CI box.
    """
    names = list(test_usmap._UNDECODABLE_FIRST)  # noqa: SLF001
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]] = [
        (names[0], None, []),
    ]
    body = test_usmap._with_undecodable_name(  # noqa: SLF001
        test_usmap._shipped_body(names=names, enums=[], schemas=schemas),  # noqa: SLF001
        names,
        0,
    )
    parsed = test_usmap._parse_schema_body(body)  # noqa: SLF001

    # The premise, asserted rather than assumed: the real parser really did
    # drop the schema, and really did flag it under the pair keyed on.
    assert parsed.schemas == {}
    flagged = [(w.code, w.subject) for w in parsed.warnings]
    assert (usmap.WARN_UNDECODABLE_NAME, _UNDECODABLE_NAME_SUBJECT) in flagged
    assert (usmap.WARN_UNRESOLVED_NAME, _DROPPED_SCHEMA_SUBJECT) in flagged

    model = _load_flat(synthetic.unknown_actor_class().blob, property_map=parsed)

    assert _reasons_of(model) == {objects.REASON_REGISTRY_INCOMPLETE}
    carried = [(w.code, w.subject) for w in model.warnings if w.source == world.SOURCE_USMAP]
    assert (usmap.WARN_UNDECODABLE_NAME, _UNDECODABLE_NAME_SUBJECT) in carried
