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
import calendar
import contextlib
import re
import sys
import time
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


# ---------------------------------------------------------------------------
# CS-1018 repair - a kept log that could not answer the question that created
# the item is not the instrument the item asked for. The 2026-09-10 gap was a
# PAUSE, so the log must show when each line was written and which of the
# driver's own waits was open at the time.
# ---------------------------------------------------------------------------

#: Every night-log line starts with a UTC time to the millisecond.
LINE_STAMP: Final = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3})Z (.*)$")

#: The settle a two-cycle fake night sleeps between its cycles, in seconds.
SETTLE_S: Final = 2.5
#: A stall no driver code path owns, planted on the cycle-1 console line. The
#: number is the 2026-09-10 night's unexplained interval.
STALL_S: Final = 214.7


class _FakeClock:
    """A wall and a monotonic clock that move only when the fake night says so."""

    def __init__(self) -> None:
        """Start both clocks at a fixed instant."""
        self.wall = 1_790_000_000.0
        self.mono = 0.0

    def time(self) -> float:
        """Wall time - the name stamp and every line stamp."""
        return self.wall

    def monotonic(self) -> float:
        """Phase elapsed time."""
        return self.mono

    def sleep(self, seconds: float) -> None:
        """Advance both clocks instead of blocking."""
        self.advance(seconds)

    def advance(self, seconds: float) -> None:
        """Move both clocks by `seconds`."""
        self.wall += float(seconds)
        self.mono += float(seconds)


class _NullHold:
    """The ledger-mutex seam, holding no OS handle."""

    def __call__(self):
        """Hand back a context manager that holds nothing."""
        return contextlib.nullcontext()


def _fake_night(tmp_path: Path, clock: _FakeClock, emit) -> None:
    """Two REAL `run_loop` cycles with every external reach replaced by a seam.

    No worker is launched, no `git` or `gh` runs, nothing reads the live
    roadmap, claim store or inbox, and nothing sleeps for real.
    """
    tree = {"n": 0}

    def tree_sha(_cwd):
        tree["n"] += 1
        return f"commit-{tree['n']}"

    queue_loop.run_loop(
        max_cycles=2,
        settle_s=SETTLE_S,
        poll_s=1,
        ci_gate=False,
        acquire=lambda _lane, **_kw: {"ok": True, "token": "T"},
        release=lambda _token, **_kw: True,
        launch=lambda _lane, **_kw: {"pid": 1, "log": "l"},
        alive=lambda _pid: False,
        proc_started=lambda _pid: 1.0,
        stranger=lambda _pid, _s: False,
        kill=lambda _pid: None,
        head_sha=lambda: "sha-unchanged",
        tree_sha=tree_sha,
        permit=lambda _lane, *_a, **_kw: {
            "ok": True,
            "lane_scope": "fixture",
            "allowed": ("CS-FIXTURE",),
            "detail": "",
        },
        claim_states=lambda _root=None, _now=None: {},
        surface=lambda _worktree: {"unread": 0, "names": [], "more": 0, "reason": ""},
        worktree="fixture-lane-worktree",
        cycle_log=tmp_path / "ledger.jsonl",
        control_dir=tmp_path / "control",
        hold=_NullHold(),
        sleep=clock.sleep,
        clock=clock.time,
        monotonic=clock.monotonic,
        emit=emit,
    )


def _stamped(text: str) -> list[tuple[float, str]]:
    """Each night-log line as (seconds since the first line, the text after the stamp)."""
    out = []
    for line in text.splitlines():
        found = LINE_STAMP.match(line)
        assert found, f"a night-log line carries no UTC millisecond stamp: {line!r}"
        out.append((found.group(1), found.group(2)))
    first = _seconds(out[0][0])
    return [(round(_seconds(stamp) - first, 3), said) for stamp, said in out]


def _seconds(stamp: str) -> float:
    whole, millis = stamp.split(".")
    parsed = time.strptime(whole, "%Y-%m-%dT%H:%M:%S")
    return calendar.timegm(parsed) + int(millis) / 1000


def _at(lines: list[tuple[float, str]], prefix: str) -> tuple[int, float]:
    hits = [(i, when) for i, (when, said) in enumerate(lines) if said.startswith(prefix)]
    assert len(hits) == 1, f"{len(hits)} night-log line(s) start with {prefix!r}"
    return hits[0]


def test_every_night_log_line_carries_a_utc_millisecond_stamp(tmp_path):
    reports = tmp_path / "reports"
    control = tmp_path / "control"
    control.mkdir(parents=True)
    (control / "STOP").write_text("halt", encoding="utf-8")
    _night(reports, control)
    logs = _night_logs(reports)
    assert len(logs) == 1
    lines = _stamped(logs[0].read_text(encoding="utf-8"))
    assert any(NIGHT_ONE_SAID in said for _when, said in lines), "the stop line is missing"


def test_a_pause_is_attributed_to_the_named_phase_it_happened_in(tmp_path):
    """A SETTLE shows as the time between its own begin and end markers."""
    clock = _FakeClock()
    with queue_loop.night_log(
        "queue", tmp_path / "reports", clock=clock.time, monotonic=clock.monotonic
    ) as name:
        _fake_night(tmp_path, clock, queue_loop._emit)  # noqa: SLF001 - the sink IS the subject
    assert name is not None
    lines = _stamped((tmp_path / "reports" / name).read_text(encoding="utf-8"))

    one_at, _ = _at(lines, "queue-loop cycle 1/2 ")
    two_at, _ = _at(lines, "queue-loop cycle 2/2 ")
    begin_at, began = _at(lines, "queue-loop phase settle begin cycle=1")
    end_at, ended = _at(lines, "queue-loop phase settle end cycle=1 ok 2.500s")
    assert one_at < begin_at < end_at < two_at, "the settle markers do not sit between the cycles"
    assert ended - began == SETTLE_S, f"the settle's markers are {ended - began}s apart"
    # EVERY WAIT THE DRIVER OWNS on the path a cycle takes is bracketed.
    for phase in (
        "lane_head_pre",
        "permit",
        "head_sha_pre",
        "run_cycle",
        "lane_head_post",
        "append_record",
    ):
        _at(lines, f"queue-loop phase {phase} begin cycle=1")
        _at(lines, f"queue-loop phase {phase} end cycle=1 ok")


def test_a_pause_outside_every_phase_shows_as_unowned_time(tmp_path):
    """THE CS-1018 SHAPE: a stall no driver code path accounts for.

    The stall is planted on the cycle-1 console line, which sits between the
    ledger write and the settle and inside no phase. The log must show the
    whole of it between one phase's END and the next phase's BEGIN, so a
    reader can say "no named wait was open" rather than guess.
    """
    clock = _FakeClock()

    def stalling_emit(line: str) -> None:
        queue_loop._emit(line)  # noqa: SLF001 - the sink IS the subject
        if line.startswith("queue-loop cycle 1/2 "):
            clock.advance(STALL_S)

    with queue_loop.night_log(
        "queue", tmp_path / "reports", clock=clock.time, monotonic=clock.monotonic
    ) as name:
        _fake_night(tmp_path, clock, stalling_emit)
    assert name is not None
    lines = _stamped((tmp_path / "reports" / name).read_text(encoding="utf-8"))
    ledger_at, ledger_done = _at(lines, "queue-loop phase append_record end cycle=1 ok")
    settle_at, settle_began = _at(lines, "queue-loop phase settle begin cycle=1")
    assert settle_began - ledger_done == STALL_S, (
        f"the stall shows as {settle_began - ledger_done}s between the phases, not {STALL_S}s"
    )
    between = [said for _when, said in lines[ledger_at + 1 : settle_at]]
    assert not [said for said in between if said.startswith("queue-loop phase ")], (
        f"a phase was open across the unowned stall: {between}"
    )


def test_a_crashed_night_keeps_its_frames_and_never_the_message(tmp_path, monkeypatch):
    """The call site survives a crash even when the launcher's stderr is bypassed.

    Frames only, as `file:line:function` - no message, no source line, no
    locals, and no absolute path, because each can carry a home path or a
    player string.
    """
    planted_dir = "planted-home-dir"
    planted_text = "PLANTED-OS-ERROR-TEXT"

    def _deeper():
        raise OSError(2, planted_text, f"C:/{planted_dir}/planted-world.sav")

    def _boom(**_kw):
        _deeper()

    monkeypatch.setattr(queue_loop, "run_loop", _boom)
    reports = tmp_path / "reports"
    with pytest.raises(OSError):  # noqa: PT011 - the TYPE is the whole claim
        _night(reports, tmp_path / "control")
    logs = _night_logs(reports)
    assert len(logs) == 1
    text = logs[0].read_text(encoding="utf-8")
    frames = [
        said.removeprefix("queue-loop night log:   at ")
        for _when, said in _stamped(text)
        if said.startswith("queue-loop night log:   at ")
    ]
    here = "tests/ops/test_driver_log_per_night.py"
    functions = [frame.rsplit(":", 1)[-1] for frame in frames]
    assert functions[-2:] == ["_boom", "_deeper"], f"the raise site is not kept: {frames}"
    assert "_drive" in functions, f"the driver's own frame is not kept: {frames}"
    shape = re.compile(r"[A-Za-z0-9_./-]+:\d+:[A-Za-z0-9_<>]+")
    for frame in frames:
        assert shape.fullmatch(frame), f"a frame carries more than file:line:function: {frame}"
        assert not re.match(r"[A-Za-z]:|/", frame), f"a frame carries an absolute path: {frame}"
    assert any(frame.startswith(f"{here}:") for frame in frames), "repo frames are not relative"
    for planted in (planted_dir, planted_text, "planted-world"):
        assert planted not in text, "the exception's own text reached the kept log"
