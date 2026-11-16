"""CS-1390 - the responder runs the build-pin check once per run and it never fails the run.

Only `main` binds the real check (the kit v30 pause-binding precedent), so every
`run_once` arm here and in `test_inbox_responder.py` stays off the live install
and the live hand-off. Every path is under `tmp_path`.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.loop import inbox_responder  # noqa: E402

T0: Final = 1_700_000_000.0


@contextmanager
def _free_lock() -> Iterator[None]:
    yield None


def _surface(unread: Any) -> Any:
    def surface(root: Any) -> dict[str, Any]:
        del root
        return {"unread": unread, "names": [], "more": 0, "reason": ""}

    return surface


def _run(tmp_path: Path, **overrides: Any) -> int:
    control = tmp_path / "ops" / "loop" / "control"
    control.mkdir(parents=True, exist_ok=True)
    kwargs: dict[str, Any] = {
        "root": tmp_path,
        "control_dir": control,
        "now": lambda: T0,
        "surface": _surface(0),
        "lock": _free_lock,
        "next_tick": lambda _now: None,
    }
    kwargs.update(overrides)
    code: int = inbox_responder.run_once(**kwargs)
    return code


class Spy:
    """A build-pin seam that counts its calls."""

    def __init__(self) -> None:
        """Start at zero calls."""
        self.calls = 0

    def __call__(self) -> None:
        """Record one call."""
        self.calls += 1


def test_a_quiet_run_calls_the_check_exactly_once(tmp_path: Path) -> None:
    spy = Spy()
    assert _run(tmp_path, build_pin=spy) == inbox_responder.EXIT_OK
    assert spy.calls == 1


def test_an_unmeasured_run_still_calls_the_check_once(tmp_path: Path) -> None:
    spy = Spy()
    code = _run(tmp_path, build_pin=spy, surface=_surface("UNMEASURED"))
    assert code == inbox_responder.EXIT_UNMEASURED
    assert spy.calls == 1


def test_a_run_that_lost_the_lock_does_not_call_the_check(tmp_path: Path) -> None:
    def held() -> Any:
        msg = "held by another run"
        raise inbox_responder.winmutex.MutexTimeout(msg)

    spy = Spy()
    assert _run(tmp_path, build_pin=spy, lock=held) == inbox_responder.EXIT_OK
    assert spy.calls == 0


def test_a_halted_run_does_not_call_the_check(tmp_path: Path) -> None:
    control = tmp_path / "ops" / "loop" / "control"
    control.mkdir(parents=True)
    (control / inbox_responder.STOP_RELPATHS[0]).write_bytes(b"halt\n")
    spy = Spy()
    assert _run(tmp_path, build_pin=spy) == inbox_responder.EXIT_OK
    assert spy.calls == 0


def test_a_check_that_raises_never_fails_the_run(tmp_path: Path) -> None:
    def boom() -> None:
        raise RuntimeError("planted fault")

    assert _run(tmp_path, build_pin=boom) == inbox_responder.EXIT_OK


def test_a_check_that_raises_does_not_stop_the_unmeasured_exit_either(tmp_path: Path) -> None:
    def boom() -> None:
        raise OSError("planted fault")

    code = _run(tmp_path, build_pin=boom, surface=_surface("UNMEASURED"))
    assert code == inbox_responder.EXIT_UNMEASURED


def test_a_run_given_no_seam_calls_no_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The default is a no-op: a pass a test drives never reaches the live install or hand-off."""
    reached: list[Any] = []
    monkeypatch.setattr(
        inbox_responder, "build_pin_watch_tick", lambda *a: reached.append(a), raising=False
    )
    assert _run(tmp_path) == inbox_responder.EXIT_OK
    assert reached == []


def test_the_cli_binds_the_real_check_to_this_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[dict[str, Any]] = []

    def recorder(**kw: Any) -> int:
        called.append(kw)
        return 0

    monkeypatch.setattr(inbox_responder, "run_once", recorder)
    inbox_responder.main(["--once"])
    bound = called[0].get("build_pin") if called else None
    expected = (inbox_responder.build_pin_watch_tick, (inbox_responder.KIT_ROOT,))
    assert (getattr(bound, "func", None), getattr(bound, "args", None)) == expected


def test_the_tick_hands_the_tool_the_hand_off_of_the_tree_it_was_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    got: list[Path] = []
    fake = ModuleType("build_pin_watch")
    fake.run = lambda handoff: got.append(Path(handoff))  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "build_pin_watch", fake)
    inbox_responder.build_pin_watch_tick(tmp_path)
    assert got == [tmp_path / "CS-NEXT-SESSION.txt"]
