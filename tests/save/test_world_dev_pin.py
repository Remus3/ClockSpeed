"""The CS-913.1 PREP arms: the gitignored dev-world pin and the corpus distinction.

Split out of ``tests/save/test_world.py`` to hold that module under the
tests-tree size ceiling. Every arm is unchanged; only the imports and the
reach-guard declarations moved with them.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import traceback
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest
from _pytest._io.saferepr import saferepr

from clockspeed.data.locate import ENV_LOCAL_CONFIG
from clockspeed.save import world
from tests.save import test_world

#: world.py's own path, owned by the sibling module that already resolves it.
_WORLD_SOURCE_PATH: Final = test_world._WORLD_SOURCE_PATH  # noqa: SLF001

#: No helper here consumes a real save path, so nothing is graded.
_GRADED_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})

#: Reaches or touches a primitive without being a grader-able library helper,
#: name to why. Asserted still reaching, so none outlives its reason.
_EXEMPT_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_frame_locals_hold": (
            "Path(...).resolve() on a traceback frame's code filename, to select "
            "world.py's own frames; it resolves a TRACKED SOURCE FILE, never a "
            "save directory"
        ),
        "_snapshot": (
            "rglob and read_bytes under a tmp_path root supplied by the caller, "
            "never a discovered save directory"
        ),
        "test_the_dev_world_pin_path_defaults_under_the_gitignored_data_directory": (
            "a test rather than a helper: Path(world.__file__).resolve() builds "
            "this repo's own root from a TRACKED SOURCE FILE, never a save "
            "directory"
        ),
    }
)

# ---------------------------------------------------------------------------
# CS-913.1 PREP: the gitignored dev-world pin and the corpus-distinction check
# ---------------------------------------------------------------------------
#
# THIS IS THE PREP HALF OF CS-913 ONLY. It places no save and records no pin;
# the DRAIN half stays gated on CS-G06. Every arm below is synthetic: worlds are
# invented ``Clockspeed...`` tokens digested through ``world.world_digest``,
# every file lives under tmp_path, and identification is a stub, so no save
# byte, no real world token and no real library is ever read (non-negotiables
# 3, 11 and 12). Every new name is reached as ``world.<name>`` so each arm
# fails on its own, with AttributeError, before the code exists.

_CORPUS_TOKEN_A: Final = "ClockspeedCorpusWorldA"  # noqa: S105
_CORPUS_TOKEN_B: Final = "ClockspeedCorpusWorldB"  # noqa: S105
_CORPUS_TOKEN_C: Final = "ClockspeedCorpusWorldC"  # noqa: S105
_CORPUS_TOKEN_D: Final = "ClockspeedCorpusWorldD"  # noqa: S105
_CORPUS_TOKEN_E: Final = "ClockspeedCorpusWorldE"  # noqa: S105
_PIN_CONTENT_MARKER: Final = "ClockspeedPinContentMarker"
_PIN_PATH_MARKER: Final = "ClockspeedPinPathMarker"
_HEX_RUN: Final = re.compile(r"[0-9a-f]{64}")


def _digest_of(token: str) -> str:
    """The world digest of an invented token, as the ledger keys it."""
    return world.world_digest(token)


def _local_config_with(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, entries: dict[str, str]
) -> None:
    """Point the local configuration at a tmp file holding ``entries``."""
    config = tmp_path / "local-config.json"
    config.write_bytes(json.dumps(entries).encode("ascii"))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(config))


def _pin_file_with(tmp_path: Path, payload: bytes, name: str = "pin.json") -> Path:
    """A pin file holding exactly ``payload``, under tmp_path."""
    target = tmp_path / name
    target.write_bytes(payload)
    return target


def test_the_dev_world_pin_path_defaults_under_the_gitignored_data_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))

    pin = world.dev_world_pin_path()

    repo_root = Path(world.__file__).resolve().parents[2]
    name_is_the_constant = pin.name == world.DEV_WORLD_PIN_FILENAME
    parent_is_data = pin.parent.name == "data"
    root_is_the_repo = pin.parent.parent == repo_root
    assert name_is_the_constant
    assert parent_is_data
    assert root_is_the_repo

    git = shutil.which("git")
    assert git is not None, "git is required to grade the ignore rule"
    relative = "data/" + world.DEV_WORLD_PIN_FILENAME
    ignored = subprocess.run(
        [git, "check-ignore", "-q", "--no-index", relative],
        cwd=repo_root,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert ignored.returncode == 0


def test_the_dev_world_pin_path_honours_the_local_config_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    chosen = tmp_path / "elsewhere" / "my-pin.json"
    _local_config_with(monkeypatch, tmp_path, {world.CONFIG_DEV_WORLD_PIN: str(chosen)})

    resolved = world.dev_world_pin_path()

    assert resolved == chosen


def test_asking_for_the_dev_world_pin_path_creates_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    folder = tmp_path / "not-yet"
    chosen = folder / "pin.json"
    _local_config_with(monkeypatch, tmp_path, {world.CONFIG_DEV_WORLD_PIN: str(chosen)})

    world.dev_world_pin_path()

    assert not folder.exists()
    assert not chosen.exists()


def test_the_pin_text_round_trips_a_digest_and_carries_no_token(tmp_path: Path) -> None:
    digest = _digest_of(_CORPUS_TOKEN_A)

    text = world.dev_world_pin_text(digest)

    assert text.isascii()
    assert text.endswith("\n")
    assert "\r" not in text
    token_leaked = _CORPUS_TOKEN_A in text
    assert not token_leaked
    pin = _pin_file_with(tmp_path, text.encode("ascii"))
    read_back = world.read_dev_world_pin(pin)
    assert read_back == digest


def test_the_pin_text_is_the_documented_sorted_object() -> None:
    digest = _digest_of(_CORPUS_TOKEN_A)

    text = world.dev_world_pin_text(digest)

    assert text == '{"dev_world_digest": "' + digest + '", "schema": 1}\n'


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(_CORPUS_TOKEN_A, id="raw-token"),
        pytest.param(world.NO_WORLD, id="no-world"),
        pytest.param(hashlib.sha256(b"x").hexdigest().upper(), id="uppercase"),
        pytest.param(hashlib.sha256(b"x").hexdigest()[:63], id="short"),
        pytest.param("g" * 64, id="not-hex"),
    ],
)
def test_the_pin_serializer_refuses_anything_but_a_digest(bad: str) -> None:
    with pytest.raises(ValueError, match=r".") as caught:
        world.dev_world_pin_text(bad)

    if bad:
        leaked = bad in str(caught.value) or bad in repr(caught.value)
        assert not leaked


def test_an_absent_pin_file_reads_as_no_pin(tmp_path: Path) -> None:
    missing = tmp_path / "nowhere" / "pin.json"

    assert world.read_dev_world_pin(missing) is None


def _valid_pin_object(**extra: object) -> dict[str, object]:
    """A well-formed pin object, plus ``extra`` keys."""
    body: dict[str, object] = {
        "dev_world_digest": _digest_of(_CORPUS_TOKEN_A),
        "schema": 1,
    }
    body.update(extra)
    return body


def _bad_pin_cases() -> list[tuple[str, bytes, str]]:
    """(id, file bytes, a string that must reach no echo path)."""
    marker = _PIN_CONTENT_MARKER
    upper = _digest_of(_CORPUS_TOKEN_A).upper()
    good = json.dumps(_valid_pin_object(extra=marker)).encode("ascii")
    return [
        (
            "raw-token",
            json.dumps({"dev_world_digest": marker, "schema": 1}).encode("ascii"),
            marker,
        ),
        (
            "wrong-schema",
            json.dumps(
                {"dev_world_digest": _digest_of(_CORPUS_TOKEN_A), "schema": 2, "m": marker}
            ).encode("ascii"),
            marker,
        ),
        ("extra-key", good, marker),
        (
            "uppercase",
            json.dumps({"dev_world_digest": upper, "schema": 1}).encode("ascii"),
            upper,
        ),
        (
            "non-ascii",
            json.dumps(_valid_pin_object(m=marker)).encode("ascii") + b"\xc3\xa9",
            marker,
        ),
        ("truncated", good[:-6], marker),
        ("oversize", good + b" " * 5000, marker),
        ("not-an-object", json.dumps([marker]).encode("ascii"), marker),
        (
            "boolean-schema",
            b'{"dev_world_digest": "'
            + _digest_of(_CORPUS_TOKEN_A).encode("ascii")
            + b'", "schema": true}',
            _digest_of(_CORPUS_TOKEN_A),
        ),
        (
            "float-schema",
            b'{"dev_world_digest": "'
            + _digest_of(_CORPUS_TOKEN_A).encode("ascii")
            + b'", "schema": 1.0}',
            _digest_of(_CORPUS_TOKEN_A),
        ),
        ("deeply-nested", b"[" * 4000 + marker.encode("ascii"), marker),
    ]


def _frame_locals_hold(exc: BaseException, needle: str) -> bool:
    """Whether a world.py frame on the traceback holds ``needle`` in a str or bytes local.

    Only this layer's own frames are read: the test's frame holds the planted
    bytes by construction, and is not what is graded.
    """
    tb = exc.__traceback__
    while tb is not None:
        if Path(tb.tb_frame.f_code.co_filename).resolve() != _WORLD_SOURCE_PATH:
            tb = tb.tb_next
            continue
        for value in tb.tb_frame.f_locals.values():
            if isinstance(value, str) and needle in value:
                return True
            if isinstance(value, bytes) and needle.encode("ascii") in value:
                return True
        tb = tb.tb_next
    return False


@pytest.mark.parametrize(
    ("payload", "planted"),
    [pytest.param(p, m, id=i) for i, p, m in _bad_pin_cases()],
)
def test_a_malformed_pin_file_is_refused_without_echoing_it(
    tmp_path: Path, payload: bytes, planted: str
) -> None:
    pin = _pin_file_with(tmp_path, payload, name="pin-" + _PIN_PATH_MARKER + ".json")

    with pytest.raises(world.DevWorldPinError) as caught:
        world.read_dev_world_pin(pin)

    exc = caught.value
    rendered = "".join(traceback.format_exception(exc))
    surfaces = (str(exc), repr(exc), rendered)
    content_leaked = any(planted in s for s in surfaces)
    path_leaked = any(_PIN_PATH_MARKER in s or str(pin) in s for s in surfaces)
    frame_holds_it = _frame_locals_hold(exc, planted)
    assert not content_leaked
    assert not path_leaked
    assert not frame_holds_it
    assert exc.__cause__ is None
    assert exc.__context__ is None


def test_an_unreadable_pin_file_is_refused_without_echoing_its_path(tmp_path: Path) -> None:
    folder = tmp_path / ("dir-" + _PIN_PATH_MARKER)
    folder.mkdir()

    with pytest.raises(world.DevWorldPinError) as caught:
        world.read_dev_world_pin(folder)

    exc = caught.value
    rendered = "".join(traceback.format_exception(exc))
    surfaces = (str(exc), repr(exc), rendered)
    path_leaked = any(_PIN_PATH_MARKER in s for s in surfaces)
    assert not path_leaked
    assert exc.__cause__ is None
    assert exc.__context__ is None


def test_a_corpus_world_absent_from_every_library_world_is_distinct() -> None:
    a, b, c = (_digest_of(t) for t in (_CORPUS_TOKEN_A, _CORPUS_TOKEN_B, _CORPUS_TOKEN_C))

    result = world.compare_corpus_world(a, [b, c], None)

    assert result.verdict == world.CORPUS_DISTINCT_FROM_LIBRARY
    assert result.library_worlds == len((b, c))
    assert result.pin_recorded is False


def test_a_corpus_save_sharing_a_library_world_is_not_distinct() -> None:
    a, b = (_digest_of(t) for t in (_CORPUS_TOKEN_A, _CORPUS_TOKEN_B))

    result = world.compare_corpus_world(a, [a, b], None)

    assert result.verdict == world.CORPUS_NOT_DISTINCT


def test_a_corpus_world_differing_from_the_recorded_pin_is_distinct() -> None:
    a, d = (_digest_of(t) for t in (_CORPUS_TOKEN_A, _CORPUS_TOKEN_D))

    result = world.compare_corpus_world(a, [a, d], d)

    assert result.verdict == world.CORPUS_DISTINCT_FROM_PIN
    assert result.pin_recorded is True


def test_a_corpus_save_of_the_pinned_dev_world_is_never_distinct() -> None:
    b, d = (_digest_of(t) for t in (_CORPUS_TOKEN_B, _CORPUS_TOKEN_D))

    result = world.compare_corpus_world(d, [b], d)

    assert result.verdict == world.CORPUS_NOT_DISTINCT


def test_the_pin_vetoes_a_library_alternative_that_would_otherwise_hold() -> None:
    b, d = (_digest_of(t) for t in (_CORPUS_TOKEN_B, _CORPUS_TOKEN_D))

    result = world.compare_corpus_world(d, [b, None], d)

    assert result.verdict == world.CORPUS_NOT_DISTINCT


def test_an_empty_library_proves_nothing() -> None:
    a = _digest_of(_CORPUS_TOKEN_A)

    result = world.compare_corpus_world(a, [], None)

    assert result.verdict == world.CORPUS_UNPROVEN
    assert result.library_worlds == 0


def test_an_unread_library_save_blocks_the_library_alternative() -> None:
    a, b, e = (_digest_of(t) for t in (_CORPUS_TOKEN_A, _CORPUS_TOKEN_B, _CORPUS_TOKEN_E))

    without_pin = world.compare_corpus_world(a, [b, None], None)
    with_pin = world.compare_corpus_world(a, [b, None], e)

    assert without_pin.verdict == world.CORPUS_UNPROVEN
    assert without_pin.library_unread == 1
    assert with_pin.verdict == world.CORPUS_DISTINCT_FROM_PIN


def test_a_library_of_saves_naming_no_world_proves_nothing() -> None:
    a = _digest_of(_CORPUS_TOKEN_A)

    result = world.compare_corpus_world(a, [world.NO_WORLD], None)

    assert result.verdict == world.CORPUS_UNPROVEN
    assert result.library_worlds == 0


def test_an_unread_library_save_that_cannot_hide_the_corpus_world_still_blocks() -> None:
    a = _digest_of(_CORPUS_TOKEN_A)

    result = world.compare_corpus_world(a, [None], None)

    assert result.verdict == world.CORPUS_UNPROVEN


def test_a_library_save_naming_no_world_does_not_block_the_library_alternative() -> None:
    a, b = (_digest_of(t) for t in (_CORPUS_TOKEN_A, _CORPUS_TOKEN_B))

    result = world.compare_corpus_world(a, [b, world.NO_WORLD], None)

    assert result.verdict == world.CORPUS_DISTINCT_FROM_LIBRARY


def test_when_both_alternatives_hold_the_library_one_is_reported() -> None:
    a, b, d = (_digest_of(t) for t in (_CORPUS_TOKEN_A, _CORPUS_TOKEN_B, _CORPUS_TOKEN_D))

    result = world.compare_corpus_world(a, [b], d)

    assert result.verdict == world.CORPUS_DISTINCT_FROM_LIBRARY
    assert result.pin_recorded is True


@pytest.mark.parametrize(
    "corpus",
    [
        pytest.param(None, id="unread"),
        pytest.param(world.NO_WORLD, id="no-world"),
        pytest.param(_CORPUS_TOKEN_A, id="raw-token"),
        pytest.param(hashlib.sha256(b"x").hexdigest().upper(), id="uppercase"),
    ],
)
def test_a_corpus_naming_no_world_is_unproven(corpus: str | None) -> None:
    b, d = (_digest_of(t) for t in (_CORPUS_TOKEN_B, _CORPUS_TOKEN_D))

    result = world.compare_corpus_world(corpus, [b], d)

    assert result.verdict == world.CORPUS_UNPROVEN


@pytest.mark.parametrize(
    "pin",
    [
        pytest.param(_CORPUS_TOKEN_D, id="raw-token"),
        pytest.param("", id="empty"),
        pytest.param(hashlib.sha256(b"x").hexdigest().upper(), id="uppercase"),
    ],
)
def test_a_pin_that_is_not_a_digest_is_refused_by_the_comparison(pin: str) -> None:
    a, b = (_digest_of(t) for t in (_CORPUS_TOKEN_A, _CORPUS_TOKEN_B))

    with pytest.raises(ValueError, match=r".") as caught:
        world.compare_corpus_world(a, [b], pin)

    leaked = bool(pin) and pin in str(caught.value)
    assert not leaked


def _every_distinction() -> list[world.CorpusDistinction]:
    a, b, c, d, e = (
        _digest_of(t)
        for t in (
            _CORPUS_TOKEN_A,
            _CORPUS_TOKEN_B,
            _CORPUS_TOKEN_C,
            _CORPUS_TOKEN_D,
            _CORPUS_TOKEN_E,
        )
    )
    return [
        world.compare_corpus_world(a, [b, c], None),
        world.compare_corpus_world(a, [a, b], None),
        world.compare_corpus_world(a, [a, d], d),
        world.compare_corpus_world(d, [b], d),
        world.compare_corpus_world(a, [], None),
        world.compare_corpus_world(a, [b, None], None),
        world.compare_corpus_world(a, [b, None], e),
        world.compare_corpus_world(None, [b], d),
    ]


def test_the_corpus_distinction_renders_no_digest_or_token() -> None:
    distinctions = _every_distinction()

    assert len({d.verdict for d in distinctions}) == len(world.CORPUS_VERDICTS)
    for distinction in distinctions:
        assert distinction.verdict in world.CORPUS_VERDICTS
        for text in (repr(distinction), str(distinction), saferepr(distinction)):
            has_hex = _HEX_RUN.search(text) is not None
            has_mask = "world:" in text
            has_token = any(t in text for t in _PLANTED_CORPUS_TOKENS)
            assert not has_hex
            assert not has_mask
            assert not has_token
    assert "CorpusDistinction" in world.__all__


_PLANTED_CORPUS_TOKENS: Final = (
    _CORPUS_TOKEN_A,
    _CORPUS_TOKEN_B,
    _CORPUS_TOKEN_C,
    _CORPUS_TOKEN_D,
    _CORPUS_TOKEN_E,
)


def _snapshot(root: Path) -> dict[str, str]:
    """The sha256 of every file under ``root``, keyed by relative POSIX path."""
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_comparing_a_corpus_save_reads_worlds_only_through_identify(tmp_path: Path) -> None:
    saves = tmp_path / "saves"
    saves.mkdir()
    corpus = saves / "corpus-placeholder"
    live_one = saves / "live-one-placeholder"
    live_two = saves / "live-two-placeholder"
    for placeholder in (corpus, live_one, live_two):
        placeholder.write_bytes(b"placeholder")
    pin_digest = _digest_of(_CORPUS_TOKEN_D)
    pin = _pin_file_with(tmp_path, world.dev_world_pin_text(pin_digest).encode("ascii"))
    digests = {
        corpus: _digest_of(_CORPUS_TOKEN_A),
        live_one: _digest_of(_CORPUS_TOKEN_B),
        live_two: _digest_of(_CORPUS_TOKEN_C),
    }
    calls: list[Path] = []

    def identify(path: Path) -> str | None:
        calls.append(path)
        return digests[path]

    before = _snapshot(tmp_path)

    result = world.compare_corpus_save(corpus, [live_one, live_two], pin, identify=identify)

    assert result.verdict == world.CORPUS_DISTINCT_FROM_LIBRARY
    assert result.pin_recorded is True
    assert sorted(calls) == sorted([corpus, live_one, live_two])
    assert _snapshot(tmp_path) == before


def test_compare_corpus_save_defaults_its_pin_to_the_resolved_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pin = _pin_file_with(
        tmp_path, world.dev_world_pin_text(_digest_of(_CORPUS_TOKEN_A)).encode("ascii")
    )
    _local_config_with(monkeypatch, tmp_path, {world.CONFIG_DEV_WORLD_PIN: str(pin)})
    corpus = tmp_path / "corpus-placeholder"

    result = world.compare_corpus_save(
        corpus, [], identify=lambda _path: _digest_of(_CORPUS_TOKEN_A)
    )

    assert result.verdict == world.CORPUS_NOT_DISTINCT
    assert result.pin_recorded is True


def test_a_corrupt_pin_fails_the_corpus_comparison_closed(tmp_path: Path) -> None:
    pin = _pin_file_with(tmp_path, b"this is not json")
    corpus = tmp_path / "corpus-placeholder"

    with pytest.raises(world.DevWorldPinError):
        world.compare_corpus_save(
            corpus, [], pin, identify=lambda _path: _digest_of(_CORPUS_TOKEN_A)
        )


def test_an_absent_pin_file_leaves_the_comparison_to_the_library(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus-placeholder"
    live = tmp_path / "live-placeholder"
    digests = {corpus: _digest_of(_CORPUS_TOKEN_A), live: _digest_of(_CORPUS_TOKEN_B)}

    result = world.compare_corpus_save(
        corpus, [live], tmp_path / "absent-pin.json", identify=lambda path: digests[path]
    )

    assert result.verdict == world.CORPUS_DISTINCT_FROM_LIBRARY
    assert result.pin_recorded is False
