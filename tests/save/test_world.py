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
``(header version, save version)`` pair is in ``objects.MEASURED_BODY_LAYOUTS``
- today the single pair header 10 with save 36. **Three of the four real pairs
are refused**, and ``test_every_unmeasured_real_pair_is_refused_and_the_measured
_one_is_not`` asserts that refusal rather than papering over it. A reader who
takes 60-odd green dots for "the save reader reads saves" has misread this
module by roughly a factor of four.

The flat-bodied corpus is therefore loaded through ``_load_flat``, which names
``world.BODY_LAYOUT_FLAT`` at every call site. That verbosity is the point: a
silent fallback from the levelled reader to the flat one would keep all of this
green while returning a wrong record count for a real world, which is precisely
the defect CS-409 removed.

Unlock state is NOT parsed by anything in this project. ADR 0004 measured which
FIELDS exist; it did not measure their serialized grammar, and
``objects.read_properties`` decodes no property value at all. So the assertions
below pin an HONESTLY EMPTY unlock state carrying a warning that says the
grammar is unmeasured, per non-negotiable 7. An empty unlock set that says so
is correct; a fabricated one is not, and ADR 0004 requires both a fresh-shaped
and a mature-shaped world be asserted because a fixture built only from a
mature world stays green through exactly the defect that reports a mature
world's state for a fresh one.

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
refusal and re-reports it as two closed-vocabulary fields with no exception in
flight and ``pytrace`` suppressed.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.data.locate import ENV_ACCOUNT_DIR, ENV_GAME_DIR, ENV_LOCAL_CONFIG, ENV_SAVE_ROOT
from clockspeed.save import chunks, header, objects, usmap, workdir, world
from tests.save import synthetic

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

_NARROW_PREFIX: Final = 4
_WIDE_PREFIX: Final = 8

_DELTA_36: Final = 4

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
    """The fence. Every unlock collection is empty because nothing decodes one today.

    ``objects.read_properties`` decodes NO property value - the payload grammar
    is unmeasured - so there is no path by which a purchased schematic could
    have been read. A non-empty collection here would mean an invented one.
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
    """A save version with no measured transform delta - objects.UnsupportedSaveVersionError."""
    return _load_flat(_planted_blob(header_version=_HEADER_13, save_version=_SAVE_42, objects_=()))


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
    """SAVE_V42 cannot load, and that refusal is the format record rather than a gap.

    THE FLAT READER IS NAMED HERE ON PURPOSE. Save 42's missing TRANSFORM DELTA
    is a different unmeasured thing from header 13 / save 42's missing BODY
    LAYOUT, and the levelled reader refuses on the layout first - so under the
    default this test would still pass while no longer asserting what it says it
    asserts. Naming the flat reader keeps the delta the subject.
    """
    with pytest.raises(world.WorldLoadError) as caught:
        _load_flat(synthetic.SAVE_V42.blob)

    assert isinstance(caught.value.__cause__, objects.UnsupportedSaveVersionError)


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


def test_no_world_warning_carries_a_string_read_out_of_the_save() -> None:
    """A warning is an echo path like any other. Every detail is fixed text."""
    model = _load_flat(_planted_blob(header_version=_HEADER_14))

    for warning in model.warnings:
        rendered = f"{warning.source} {warning.code} {warning.detail}"
        for token in _PLANTED_TOKENS:
            assert token not in rendered
        assert rendered.isascii()


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

    Header 14 / save 60 is a REAL pair whose whole-body layout has not been
    derived. Before CS-409 this returned a WorldModel: the flat reader walked a
    levelled body and reported whatever fell out. A refusal is the only honest
    answer - an empty world, a wrong count and a crash are all worse, and the
    first two are worse than the crash because nothing downstream can tell.
    """
    with pytest.raises(world.WorldLoadError) as caught:
        world.load_world_from_bytes(synthetic.SAVE_V60.blob)

    assert isinstance(caught.value.__cause__, objects.UnsupportedBodyLayoutError)
    assert caught.value.stage == world.STAGE_OBJECTS


def test_every_unmeasured_real_pair_is_refused_and_the_measured_one_is_not() -> None:
    """The sibling sweep. One refusal proves one branch; the table proves the rule.

    Every pair the corpus carries is checked against
    ``objects.MEASURED_BODY_LAYOUTS`` rather than against a list written here,
    so the day a pair is measured this test follows the measurement instead of
    contradicting it.
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

    Three of the four real pairs are refused. That is the single most important
    fact about this module today, so it is asserted rather than left to a
    reader's goodwill - and asserted against the live measured set, so the
    sentence cannot outlive the measurement it describes.
    """
    docstring = world.__doc__ or ""
    measured = sorted(objects.MEASURED_BODY_LAYOUTS)

    assert len(measured) == 1
    for header_version, save_version in measured:
        assert f"header {header_version}" in docstring
        assert f"save {save_version}" in docstring
    assert "MEASURED_BODY_LAYOUTS" in docstring


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

    THE WHOLE BODY IS INSIDE A GUARD. ``header.read_header`` takes a PATH and
    ``chunks.decompress_body`` takes the save's BYTES, and pytest renders a
    failing frame's arguments - so an escaping error from either publishes an
    absolute path under a home directory (non-negotiable 3) or the header
    options string (non-negotiable 12). The failure is re-reported as the
    error's class name, which is module-defined vocabulary, with no exception
    in flight and ``pytrace`` suppressed.
    """
    assert isolated_work_root
    source = workdir.latest_save()
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

    if refusal is not None:
        pytest.fail(f"the newest real save did not reach a body: {refusal}", pytrace=False)
    assert scalars is not None
    header_version, token_length, chunk_count, payload_length = scalars

    assert header_version in header.SUPPORTED_HEADER_VERSIONS
    assert token_length == header.WORLD_TOKEN_LENGTH
    assert chunk_count >= 1
    assert payload_length > 0


def _one_real_save_path_of_a_measured_pair() -> Path | None:
    """Find a real save whose whole-body layout this project has measured.

    The path is RETURNED and never rendered: ``load_world`` needs one, and an
    absolute path under a home directory is personal data (non-negotiable 3).
    Every caller below binds it to a local and passes it straight on.

    Returns:
        The path, or None when no such file is reachable on this machine.
    """
    root = locate.resolve_save_root()
    if root is None:
        return None
    account = locate.resolve_account_dir(root)
    if account is None:
        return None
    for path in sorted(account.glob("*.sav")):
        try:
            parsed = header.parse_header(path.read_bytes())
        except (OSError, header.HeaderError):
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
