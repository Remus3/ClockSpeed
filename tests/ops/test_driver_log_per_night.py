"""CS-1018 - the driver's own log is RETAINED PER NIGHT, never overwritten.

The 2026-09-10 night left a 262.5s gap between two lane cycles that no code
path accounts for, and the one record that would have settled it - the
driver's own stdout log for that night - was gone: the launcher redirected
stdout to ONE fixed file per lane, and `Start-Process` truncates its redirect
target on every launch, so a later night erased it. The item was re-scoped to
the instrument that would have caught it: every night keeps its own log.

THE ACCEPTANCE ARM RUNS THE DRIVER'S ENTRY POINT TWICE. `main` is driven for
real, `run_loop` included, with the seams the driver already has: the
singleton guard is a null context (no OS mutex), and every path - the reports
directory, the control directory - is a `tmp_path`. Nothing here can reach the
live lane: each night is stopped by a sentinel before cycle 1, so no worker is
launched, no `gh` or `git` call is made, and nothing sleeps.

THE TWO NIGHTS ARE TOLD APART BY WHAT THE DRIVER ITSELF SAID. Night one is
stopped by `STOP`, night two by `QUEUE_STOP`, and each stop line is emitted by
the real `run_loop`, so "each log holds its own night's output" is graded on
bytes the driver wrote rather than on a marker the test planted.
"""

from __future__ import annotations

import ast
import contextlib
import re
import sys
from pathlib import Path
from typing import Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip: a missing driver is a COLLECTION error.
from ops.loop import queue_loop  # noqa: E402

#: The whole of what a night log's NAME may carry: the folded lane, a UTC
#: start stamp and a run token. No account, world or home path can fit.
NAME_SHAPE: Final = re.compile(r"queue_loop_night-[A-Za-z0-9_]+-\d{8}T\d{6}Z-[0-9a-f]{8}\.log")

#: What each night's stop line says. The real `run_loop` writes these.
NIGHT_ONE_SAID: Final = "queue-loop stop: STOP present"
NIGHT_TWO_SAID: Final = "queue-loop stop: QUEUE_STOP present"

#: Two nights of the driver, so two logs.
NIGHTS: Final = 2


class _NoMutex:
    """The singleton seam: a zero-argument callable returning a null context."""

    def __call__(self):
        """Hand back a context manager that holds nothing."""
        return contextlib.nullcontext()


def _night(reports: Path, control: Path) -> int:
    """Run ONE night of the driver through its entry point.

    Args:
        reports: Where the ledger and the night log go.
        control: Where the stop sentinels live.

    Returns:
        The exit code `main` returned.
    """
    return queue_loop.main(
        [
            "--cycles",
            "1",
            "--no-ci-gate",
            "--reports-dir",
            str(reports),
            "--control-dir",
            str(control),
        ],
        singleton=_NoMutex(),
        retain_log=True,
    )


def _night_logs(reports: Path) -> list[Path]:
    return sorted(reports.glob("queue_loop_night-*.log"))


def test_two_consecutive_nights_leave_two_logs_each_holding_its_own_output(tmp_path):
    """THE ACCEPTANCE ARM - two nights, two logs, neither overwritten."""
    reports = tmp_path / "reports"
    control = tmp_path / "control"
    (control / "lanes").mkdir(parents=True)

    (control / "STOP").write_text("night one halt", encoding="utf-8")
    first_code = _night(reports, control)
    after_one = _night_logs(reports)
    assert len(after_one) == 1, f"night one left {len(after_one)} night log(s), not 1"
    first_bytes = after_one[0].read_bytes()

    (control / "STOP").unlink()
    (control / "lanes" / "QUEUE_STOP").write_text("night two halt", encoding="utf-8")
    second_code = _night(reports, control)

    logs = _night_logs(reports)
    assert len(logs) == NIGHTS, f"two nights left {len(logs)} night log(s), not 2"
    # NEVER OVERWRITTEN: night one's file is byte-identical after night two.
    assert after_one[0].read_bytes() == first_bytes, "night two rewrote night one's log"

    texts = {path: path.read_text(encoding="utf-8") for path in logs}
    one = [path for path, text in texts.items() if NIGHT_ONE_SAID in text]
    two = [path for path, text in texts.items() if NIGHT_TWO_SAID in text]
    assert len(one) == 1, f"night one's stop line is in {len(one)} log(s)"
    assert len(two) == 1, f"night two's stop line is in {len(two)} log(s)"
    assert one[0] != two[0], "both nights' output landed in ONE log"
    assert NIGHT_TWO_SAID not in texts[one[0]], "night one's log holds night two's output"
    assert NIGHT_ONE_SAID not in texts[two[0]], "night two's log holds night one's output"
    # AND EACH NAMES ITSELF ONCE - a log carrying two headers is two nights in one file.
    for path, text in texts.items():
        assert text.count("queue-loop night log:") == 1, f"{path.name} holds more than one night"
        assert path.name in text, f"{path.name} does not name itself"
    # The real exit path ran both times: a sentinel already present exits 2.
    assert (first_code, second_code) == (queue_loop.EXIT_STOP_SENTINEL,) * 2


def test_a_night_log_name_carries_only_lane_stamp_and_token(tmp_path):
    reports = tmp_path / "reports"
    control = tmp_path / "control"
    control.mkdir(parents=True)
    (control / "STOP").write_text("halt", encoding="utf-8")
    _night(reports, control)
    names = [path.name for path in _night_logs(reports)]
    assert len(names) == 1
    assert NAME_SHAPE.fullmatch(names[0]), f"night log name out of shape: {names[0]}"
    assert f"-{queue_loop.LANE}-" in names[0], "the lane is not in the name"


def test_a_lane_carrying_path_characters_cannot_escape_the_directory(tmp_path):
    with queue_loop.night_log("../up/and\\out", tmp_path / "reports") as name:
        pass
    assert name is not None
    assert NAME_SHAPE.fullmatch(name), f"folded name out of shape: {name}"
    assert [path.name for path in (tmp_path / "reports").iterdir()] == [name]


def test_an_existing_log_is_never_truncated_and_the_night_still_gets_its_own(tmp_path):
    """A COLLIDING NAME IS RE-MINTED, NEVER REOPENED.

    The clock and the token are pinned so the first name the driver tries is
    one already on disk. The planted file must keep every byte, and the night
    must still get a file of its own under a fresh token.
    """
    reports = tmp_path / "reports"
    reports.mkdir()
    tokens = iter(["aaaaaaaa", "aaaaaaaa", "bbbbbbbb"])
    fixed_clock = 1_790_000_000.0
    with queue_loop.night_log(
        "queue", reports, clock=lambda: fixed_clock, mint=lambda: next(tokens)
    ) as planted_name:
        pass
    assert planted_name is not None
    planted = reports / planted_name
    planted_bytes = planted.read_bytes()
    assert planted_bytes, "the first night wrote nothing to collide with"

    with queue_loop.night_log(
        "queue", reports, clock=lambda: fixed_clock, mint=lambda: next(tokens)
    ) as second_name:
        queue_loop._emit("second night only")  # noqa: SLF001 - the sink IS the subject

    assert planted.read_bytes() == planted_bytes, "a colliding name truncated a kept log"
    assert second_name is not None
    assert second_name != planted_name
    assert "-bbbbbbbb.log" in second_name, "the collision was not re-minted"
    assert "second night only" in (reports / second_name).read_text(encoding="utf-8")


def test_a_driver_that_raises_names_the_type_and_never_the_message(tmp_path, monkeypatch):
    """The last line of a crashed night says WHAT raised, never what it carried.

    `str()` on a caught exception is the personal-data channel non-negotiable
    12 closes, so only the type name reaches the kept log.
    """
    planted = "PLANTED-EXCEPTION-TEXT"

    def _boom(**_kw):
        raise RuntimeError(planted)

    monkeypatch.setattr(queue_loop, "run_loop", _boom)
    reports = tmp_path / "reports"
    with pytest.raises(RuntimeError):
        _night(reports, tmp_path / "control")
    logs = _night_logs(reports)
    assert len(logs) == 1
    text = logs[0].read_text(encoding="utf-8")
    assert "RuntimeError" in text, "a crashed night does not say what raised"
    assert planted not in text, "the exception's own text reached the kept log"


def test_main_called_as_a_function_writes_no_night_log_unless_asked(tmp_path, monkeypatch):
    """Existing callers of `main` must not start littering the real reports dir.

    The CONTROL half of the pair: the same run with `retain_log=True` does
    write one, which is graded above.
    """
    monkeypatch.setattr(
        queue_loop,
        "run_loop",
        lambda **_kw: {"cycles_run": 0, "stopped_by": "STOP", "records": []},
    )
    reports = tmp_path / "reports"
    queue_loop.main(
        ["--once", "--reports-dir", str(reports), "--control-dir", str(tmp_path / "control")],
        singleton=_NoMutex(),
    )
    assert not reports.exists() or not _night_logs(reports)


def test_the_script_entry_point_retains_the_log():
    """EVERY REAL NIGHT RETAINS - the `__main__` block is what a process runs.

    The launcher starts `queue_loop.py` as a script and the manual route in
    `docs/OPERATIONS.md` does too, so the only call that matters is the one in
    the module's `__main__` block. Read from the syntax tree, so formatting
    cannot hide it.
    """
    source = (ROOT / "ops" / "loop" / "queue_loop.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
    ]
    assert len(guards) == 1, "the driver has no single __main__ block"
    calls = [
        node
        for node in ast.walk(guards[0])
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "main"
    ]
    assert len(calls) == 1, "the __main__ block does not call main exactly once"
    retained = [
        kw
        for kw in calls[0].keywords
        if kw.arg == "retain_log" and isinstance(kw.value, ast.Constant) and kw.value.value is True
    ]
    assert retained, "the script entry point runs a night with no night log"


def test_the_sink_is_released_when_the_night_ends(tmp_path, capsys):
    """A line emitted AFTER a night is that night's no longer.

    A sink left pointing at the closed handle would make every later line try
    a write, fail, and print a spurious "write failed" warning - and a later
    night nested inside another caller would lose its restore.
    """
    with queue_loop.night_log("queue", tmp_path) as name:
        pass
    assert name is not None
    capsys.readouterr()
    queue_loop._emit("after the night")  # noqa: SLF001 - the sink IS the subject
    said = capsys.readouterr().out
    assert said == "after the night\n", f"a line after the night did more than print: {said!r}"
    assert "after the night" not in (tmp_path / name).read_text(encoding="utf-8")
