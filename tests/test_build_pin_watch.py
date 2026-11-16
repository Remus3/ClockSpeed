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

from clockspeed.data import locate, version  # noqa: E402

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


def test_the_default_command_is_the_pin_modules_public_one() -> None:
    assert _watch().repin_command() == version.REGENERATE_COMMAND


def test_the_pin_modules_command_is_the_one_guard_h_publishes() -> None:
    """Two equal literals, bound here: the walk-visible tool reads only the pin module's."""
    assert version.REGENERATE_COMMAND == drift_guard.RE_EXTRACT_COMMAND


def test_the_public_command_survives_a_re_extract_of_the_generated_block() -> None:
    """The name sits outside the BEGIN/END markers the rewriter replaces."""
    source = Path(version.__file__).read_bytes().decode("ascii")
    payload = version.extract_pin_block(source)
    rewritten = version.rewrite_pin_source(source, {**payload, "game_build": "9.9.9.9-1"})
    assert rewritten != source
    assert "REGENERATE_COMMAND: Final = _REGENERATE_COMMAND" in rewritten.splitlines()


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


# ---- CS-1390 repair: the write is a read-modify-write of a TRACKED shared file, so it
# yields to a live claim and to a concurrent writer, and never invalidates a done marker.


SECOND_PROBE: Final = 2


def _unclaimed(_paths: list[str]) -> list[Any]:
    return []


def _tmps(path: Path) -> list[Path]:
    return [p for p in path.parent.iterdir() if p.name.endswith(".tmp")]


NOW: Final = 1_800_000_000.0  # the injected clock: a fixed epoch, never the real one


def _check_with(path: Path, claimed: Any) -> str:
    outcome: str = _watch().check(
        path,
        installed=lambda: OTHER,
        pinned=PINNED,
        command=drift_guard.RE_EXTRACT_COMMAND,
        today=TODAY,
        claimed=claimed,
        now=lambda: NOW,
    )
    return outcome


def test_a_foreign_claim_holds_the_write_and_leaves_the_file_untouched(handoff: Path) -> None:
    probed: list[list[str]] = []

    def claimed(paths: list[str]) -> list[Any]:
        probed.append(list(paths))
        return [(paths[0], 3.0)]

    assert _check_with(handoff, claimed) == "held"
    assert probed
    assert handoff.read_bytes() == HANDOFF_TEXT
    assert _tmps(handoff) == []


def test_a_probe_that_raises_holds_the_write(handoff: Path) -> None:
    def claimed(_paths: list[str]) -> list[Any]:
        raise OSError("planted fault")

    assert _check_with(handoff, claimed) == "held"
    assert handoff.read_bytes() == HANDOFF_TEXT
    assert _tmps(handoff) == []


def test_a_writer_between_the_read_and_the_rename_wins_and_the_write_is_dropped(
    handoff: Path,
) -> None:
    other_writer: Final = HANDOFF_TEXT + b"another writer's line\n"
    calls: list[int] = []

    def claimed(_paths: list[str]) -> list[Any]:
        calls.append(1)
        if len(calls) == SECOND_PROBE:  # the second probe runs after the read, before the rename
            handoff.write_bytes(other_writer)
        return []

    assert _check_with(handoff, claimed) == "raced"
    assert handoff.read_bytes() == other_writer
    assert _tmps(handoff) == []


def test_control_unclaimed_and_unchanged_still_writes(handoff: Path) -> None:
    assert _check_with(handoff, _unclaimed) == "written"
    assert len(_marked(handoff)) == 1
    assert _tmps(handoff) == []


def test_the_default_probe_is_the_kits_foreign_claims() -> None:
    from ops.fleet_kit import fleet_claims  # noqa: PLC0415

    assert _watch().default_claimed() is fleet_claims.foreign_claims


def _write_marker(
    root: Path,
    handoff: Path,
    *,
    digest: str | None = None,
    age_s: float | None = 60.0,
    at: Any = None,
) -> None:
    """A /done marker over `handoff`, written `age_s` before the injected clock."""
    import datetime  # noqa: PLC0415
    import hashlib  # noqa: PLC0415
    import json  # noqa: PLC0415

    sha = digest or hashlib.sha256(handoff.read_bytes()).hexdigest()
    doc: dict[str, Any] = {
        "schema": 1,
        "status": "done",
        "handoff": handoff.name,
        "handoff_sha256": sha,
    }
    if at is not None:
        doc["at"] = at
    elif age_s is not None:
        stamp = datetime.datetime.fromtimestamp(NOW - age_s, datetime.UTC)
        doc["at"] = stamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    marker = root / "ops" / "loop" / "control" / "session_done.json"
    marker.parent.mkdir(parents=True)
    marker.write_text(json.dumps(doc), encoding="ascii")


def test_fresh_done_marker_still_pins(handoff: Path) -> None:
    """`fleet_done.validate` hashes the hand-off: a later write reads as work after /done."""
    _write_marker(handoff.parent, handoff, age_s=60.0)
    assert _check_with(handoff, _unclaimed) == "held"
    assert handoff.read_bytes() == HANDOFF_TEXT


def test_stale_done_marker_does_not_pin(handoff: Path) -> None:
    """A marker the session left behind hours ago must not mute the warning for good."""
    _write_marker(handoff.parent, handoff, age_s=7200.0)
    assert _check_with(handoff, _unclaimed) == "written"


@pytest.mark.parametrize("at", ["not a time", 12345, "2026-13-45T99:99:99Z", ""])
def test_a_marker_with_an_unparseable_at_pins_nothing(handoff: Path, at: Any) -> None:
    _write_marker(handoff.parent, handoff, at=at)
    assert _check_with(handoff, _unclaimed) == "written"


def test_a_marker_with_no_at_pins_nothing(handoff: Path) -> None:
    _write_marker(handoff.parent, handoff, age_s=None)
    assert _check_with(handoff, _unclaimed) == "written"


def test_a_marker_over_other_bytes_pins_nothing(handoff: Path) -> None:
    _write_marker(handoff.parent, handoff, digest="0" * 64)
    assert _check_with(handoff, _unclaimed) == "written"
