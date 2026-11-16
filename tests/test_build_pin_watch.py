"""CS-1390 - warn the day the installed game build differs from the pin.

The check compares the installed build id with the pin in
`clockspeed/data/version.py` and, the day they differ, writes ONE marker-prefixed
line carrying the re-pin command into the hand-off file. A matching build writes
nothing, and so does a build that cannot be read.

EVERY ARM IS FIXTURE-ONLY. The installed-build reader is injected everywhere
except the arms that grade the real binding, and those patch the install
locator to raise, so no arm reads a live install, the live hand-off or the live
control files. Every hand-off here lives under `tmp_path`.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[1]
TOOLS_DIR: Final = ROOT / "tools"
for _dir in (ROOT, TOOLS_DIR):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import drift_guard  # noqa: E402

from clockspeed.data import locate  # noqa: E402

#: Synthetic build strings, never a real game build.
PINNED: Final = "1.0.0.0-100"
OTHER: Final = "1.0.0.0-200"
TODAY: Final = "2026-11-16"
HANDOFF_TEXT: Final = b"SYNTHETIC HAND-OFF\nSESSION: 1\n\nfirst item\n"


def _watch() -> ModuleType:
    try:
        return importlib.import_module("build_pin_watch")
    except ModuleNotFoundError:
        pytest.fail("tools/build_pin_watch.py does not exist - the check is not built")


@pytest.fixture
def handoff(tmp_path: Path) -> Path:
    path = tmp_path / "CS-NEXT-SESSION.txt"
    path.write_bytes(HANDOFF_TEXT)
    return path


def _check(path: Path, installed: Any, *, today: str = TODAY, pinned: str = PINNED) -> str:
    outcome: str = _watch().check(
        path,
        installed=installed,
        pinned=pinned,
        command=drift_guard.RE_EXTRACT_COMMAND,
        today=today,
    )
    return outcome


def _marked(path: Path) -> list[str]:
    marker = _watch().MARKER
    return [ln for ln in path.read_bytes().decode("ascii").splitlines() if ln.startswith(marker)]


def test_a_differing_build_writes_one_line_carrying_the_repin_command(handoff: Path) -> None:
    outcome = _check(handoff, lambda: OTHER)
    lines = _marked(handoff)
    assert outcome == "written"
    assert len(lines) == 1
    assert drift_guard.RE_EXTRACT_COMMAND in lines[0]
    assert OTHER in lines[0]
    assert PINNED in lines[0]
    assert TODAY in lines[0]
    # The rest of the hand-off is carried untouched, ahead of the one new line.
    assert handoff.read_bytes().startswith(HANDOFF_TEXT)


def test_the_default_command_is_the_public_one_guard_h_publishes() -> None:
    assert _watch().repin_command() == drift_guard.RE_EXTRACT_COMMAND


def test_a_matching_build_writes_nothing(handoff: Path) -> None:
    before = handoff.read_bytes()
    outcome = _check(handoff, lambda: PINNED)
    assert outcome == "match"
    assert handoff.read_bytes() == before


def test_a_second_run_the_same_day_writes_no_second_line(handoff: Path) -> None:
    assert _check(handoff, lambda: OTHER) == "written"
    once = handoff.read_bytes()
    assert _check(handoff, lambda: OTHER) == "unchanged"
    assert handoff.read_bytes() == once
    assert len(_marked(handoff)) == 1


def test_a_later_day_with_the_same_two_builds_keeps_the_one_line_as_it_was(handoff: Path) -> None:
    _check(handoff, lambda: OTHER)
    once = handoff.read_bytes()
    assert _check(handoff, lambda: OTHER, today="2026-11-17") == "unchanged"
    assert handoff.read_bytes() == once


def test_a_newer_installed_build_replaces_the_line_and_never_adds_one(handoff: Path) -> None:
    _check(handoff, lambda: OTHER)
    assert _check(handoff, lambda: "1.0.0.0-300") == "written"
    lines = _marked(handoff)
    assert len(lines) == 1
    assert "1.0.0.0-300" in lines[0]
    assert OTHER not in lines[0]


def test_an_unreadable_build_writes_nothing(handoff: Path) -> None:
    before = handoff.read_bytes()
    assert _check(handoff, lambda: None) == "unreadable"
    assert _check(handoff, lambda: "") == "unreadable"
    assert handoff.read_bytes() == before


def test_a_reader_that_raises_is_flagged_never_fatal(handoff: Path) -> None:
    def broken() -> str:
        raise OSError("planted fault")

    before = handoff.read_bytes()
    assert _check(handoff, broken) == "unreadable"
    assert handoff.read_bytes() == before


def test_a_build_string_that_is_not_plain_ascii_is_not_written(handoff: Path) -> None:
    before = handoff.read_bytes()
    assert _check(handoff, lambda: "1.0" + chr(0xE9) + "-200") == "unreadable"
    assert _check(handoff, lambda: "1.0\n-200") == "unreadable"
    assert handoff.read_bytes() == before


def test_an_unpinned_tree_writes_nothing(handoff: Path) -> None:
    before = handoff.read_bytes()
    assert _check(handoff, lambda: OTHER, pinned="") == "unpinned"
    assert handoff.read_bytes() == before


def test_a_missing_hand_off_is_never_created(tmp_path: Path) -> None:
    absent = tmp_path / "CS-NEXT-SESSION.txt"
    assert _check(absent, lambda: OTHER) == "no_handoff"
    assert not absent.exists()


def test_the_write_leaves_no_temp_file_beside_the_hand_off(handoff: Path) -> None:
    _check(handoff, lambda: OTHER)
    assert sorted(p.name for p in handoff.parent.iterdir()) == [handoff.name]


def test_the_line_is_one_ascii_line_with_no_path(handoff: Path) -> None:
    _check(handoff, lambda: OTHER)
    raw = handoff.read_bytes()
    raw.decode("ascii")
    assert b"\r" not in raw
    assert str(handoff.parent).encode("ascii") not in raw


def test_a_hand_off_without_a_final_newline_still_gets_its_own_line(tmp_path: Path) -> None:
    path = tmp_path / "CS-NEXT-SESSION.txt"
    path.write_bytes(b"no trailing newline")
    _check(path, lambda: OTHER)
    assert path.read_bytes().startswith(b"no trailing newline\n")
    assert len(_marked(path)) == 1


def test_no_live_install_is_read_when_the_reader_is_injected(
    handoff: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    def forbidden() -> Any:
        raise AssertionError("the live install locator was reached")

    monkeypatch.setattr(locate, "resolve_game_dir", forbidden)
    assert _check(handoff, lambda: OTHER) == "written"


def test_a_game_that_is_not_installed_reads_as_unknown_never_a_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setattr(locate, "resolve_game_dir", lambda: (None, "none"))
    assert _watch().installed_build() is None


def test_a_locator_that_raises_reads_as_unknown_never_fatal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def boom() -> Any:
        raise OSError("planted fault")

    monkeypatch.setattr(locate, "resolve_game_dir", boom)
    assert _watch().installed_build() is None


def test_the_real_reader_is_the_one_guard_h_reads_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The build comes from `scripts/verify_env.read_build_string`, not a second reader."""
    seen: list[Path | None] = []

    def fake_reader(game_dir: Path | None) -> tuple[str | None, str]:
        seen.append(game_dir)
        return OTHER, "synthetic"

    monkeypatch.setattr(locate, "resolve_game_dir", lambda: (tmp_path, "synthetic"))
    verify_env = drift_guard._load_verify_env()  # noqa: SLF001 - the shared reader, patched
    monkeypatch.setattr(verify_env, "read_build_string", fake_reader)
    assert _watch().installed_build() == OTHER
    assert seen == [tmp_path]


def test_run_never_raises_and_prints_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    watch = _watch()

    def boom(*args: Any, **kwargs: Any) -> str:
        del args, kwargs
        raise RuntimeError("planted fault")

    monkeypatch.setattr(watch, "check", boom)
    assert watch.run(tmp_path / "CS-NEXT-SESSION.txt") == "error"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
