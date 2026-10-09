"""CS-1234 - the responder's status file and its task clock.

Every arm drives `ops/loop/inbox_status` against a tmp control directory. NO ARM
queries the real scheduler, reads the live control plane or renders a path or
an env value (CLAUDE.md rules 12 and 13): findings are bound to scalars first.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.fleet_kit import fleet_headless as kit  # noqa: E402
from ops.loop import inbox_status  # noqa: E402

T0: Final = 1_000_000.0
DAY: Final = 86400.0

SCHEMA_KEYS: Final = frozenset(
    {
        "schema",
        "code",
        "updated",
        "state",
        "task",
        "task_started",
        "task_eta_s",
        "next_tick",
        "runs_in_window",
        "runs_cap",
        "window_s",
        "cap_frees_at",
    }
)


def _read(control: Path) -> dict[str, Any]:
    parsed: dict[str, Any] = json.loads(
        (control / inbox_status.STATUS_NAME).read_bytes().decode("ascii")
    )
    return parsed


def test_the_constants_match_the_order() -> None:
    states = inbox_status.STATES == (
        "idle",
        "running",
        "limit",
        "backoff",
        "halted",
        "refused",
        "blocked",
    )
    tasks = set(inbox_status.TASKS) == {
        "Idle",
        "Checking Inbox",
        "Waiting for Slot",
        "Running Session",
        "Delivering Notes",
        "Committing",
        "Backing Off",
        "Halted",
        "Turn Limit Reached",
    }
    short = all(len(task) <= 24 for task in inbox_status.TASKS)  # noqa: PLR2004 - schema bound
    numbers = (inbox_status.RUNS_CAP, inbox_status.WINDOW_S, inbox_status.CODE)
    assert (states, tasks, short, numbers) == (True, True, True, (120, 86400, "CS"))


def test_publish_writes_schema_one_exactly(tmp_path: Path) -> None:
    window = inbox_status.Window(count=3, frees_at=T0 + 10)
    inbox_status.publish(
        tmp_path,
        now=T0,
        state="halted",
        task="Halted",
        task_started=T0 - 5,
        eta_s=None,
        next_tick=T0 + 900,
        window=window,
    )
    status = _read(tmp_path)
    keys = set(status) == SCHEMA_KEYS
    fixed = (status["schema"], status["code"], status["runs_cap"], status["window_s"])
    live = (status["state"], status["task"], status["task_eta_s"], status["runs_in_window"])
    stamps = [status[k] for k in ("updated", "task_started", "next_tick", "cap_frees_at")]
    offsets = all(datetime.fromisoformat(s).utcoffset() is not None for s in stamps)
    updated_ok = datetime.fromisoformat(status["updated"]).timestamp() == T0
    raw = (tmp_path / inbox_status.STATUS_NAME).read_bytes()
    ascii_lf = all(b < 0x80 for b in raw) and b"\r" not in raw  # noqa: PLR2004 - 7-bit bound
    no_tmp = sorted(p.name for p in tmp_path.iterdir()) == [inbox_status.STATUS_NAME]
    assert (keys, fixed, live, offsets, updated_ok, ascii_lf, no_tmp) == (
        True,
        (1, "CS", 120, 86400),
        ("halted", "Halted", None, 3),
        True,
        True,
        True,
        True,
    )


def test_publish_holds_no_path(tmp_path: Path) -> None:
    inbox_status.publish(
        tmp_path,
        now=T0,
        state="idle",
        task="Idle",
        task_started=T0,
        eta_s=4,
        next_tick=None,
        window=inbox_status.Window(count=0, frees_at=None),
    )
    raw = (tmp_path / inbox_status.STATUS_NAME).read_bytes().decode("ascii")
    no_sep = "\\" not in raw and "/" not in raw
    no_tree = tmp_path.name not in raw
    assert (no_sep, no_tree) == (True, True)


@pytest.mark.parametrize(("state", "task"), [("asleep", "Idle"), ("idle", "Sleeping Deeply")])
def test_publish_refuses_a_name_outside_the_sets(tmp_path: Path, state: str, task: str) -> None:
    with pytest.raises(ValueError, match="outside"):
        inbox_status.publish(
            tmp_path,
            now=T0,
            state=state,
            task=task,
            task_started=T0,
            eta_s=None,
            next_tick=None,
            window=inbox_status.Window(count=0, frees_at=None),
        )


def test_refresh_keeps_the_task_and_moves_updated(tmp_path: Path) -> None:
    window = inbox_status.Window(count=1, frees_at=T0 + DAY)
    inbox_status.publish(
        tmp_path,
        now=T0,
        state="running",
        task="Running Session",
        task_started=T0,
        eta_s=None,
        next_tick=None,
        window=window,
    )
    refreshed = inbox_status.refresh(tmp_path, now=T0 + 900, next_tick=T0 + 1800, window=window)
    status = _read(tmp_path)
    moved = datetime.fromisoformat(status["updated"]).timestamp() == T0 + 900
    kept = (status["state"], status["task"])
    started = datetime.fromisoformat(status["task_started"]).timestamp() == T0
    assert (refreshed, moved, kept, started) == (True, True, ("running", "Running Session"), True)


def test_refresh_without_a_status_file_writes_nothing(tmp_path: Path) -> None:
    window = inbox_status.Window(count=0, frees_at=None)
    refreshed = inbox_status.refresh(tmp_path, now=T0, next_tick=None, window=window)
    assert (refreshed, (tmp_path / inbox_status.STATUS_NAME).exists()) == (False, False)


# --- the task clock -------------------------------------------------------------


def test_eta_is_null_below_three_and_the_median_of_the_last_ten(tmp_path: Path) -> None:
    clock = inbox_status.TaskClock(tmp_path)
    clock.record("Running Session", 10)
    clock.record("Running Session", 20)
    two = clock.eta("Running Session")
    clock.record("Running Session", 90)
    three = clock.eta("Running Session")
    for _ in range(10):
        clock.record("Running Session", 50)
    ten = inbox_status.TaskClock(tmp_path).eta("Running Session")
    other = clock.eta("Checking Inbox")
    assert (two, three, ten, other) == (None, 20, 50, None)


def test_a_garbled_task_clock_reads_as_empty(tmp_path: Path) -> None:
    (tmp_path / inbox_status.TASKS_NAME).write_bytes(b"{garbled")
    clock = inbox_status.TaskClock(tmp_path)
    assert (clock.eta("Idle"), clock.idle_since()) == (None, None)


def test_idle_since_persists(tmp_path: Path) -> None:
    inbox_status.TaskClock(tmp_path).set_idle_since(T0)
    assert inbox_status.TaskClock(tmp_path).idle_since() == T0


# --- the next tick --------------------------------------------------------------

TASK_XML: Final = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <TimeTrigger>
      <StartBoundary>2026-10-02T23:11:00</StartBoundary>
      <Repetition>
        <Interval>PT15M</Interval>
      </Repetition>
    </TimeTrigger>
  </Triggers>
</Task>
"""


def test_the_next_tick_comes_from_the_task_trigger() -> None:
    start = datetime(2026, 10, 2, 23, 11).timestamp()
    now = start + 3 * 900 + 10
    tick = inbox_status.next_tick_from_xml(TASK_XML, now)
    on_boundary = inbox_status.next_tick_from_xml(TASK_XML, start + 900)
    assert (tick, on_boundary) == (start + 4 * 900, start + 2 * 900)


@pytest.mark.parametrize(
    ("interval", "seconds"), [("PT15M", 900), ("PT1H", 3600), ("PT1H30M", 5400), ("PT45S", 45)]
)
def test_the_interval_parses(interval: str, seconds: int) -> None:
    assert inbox_status.parse_interval(interval) == seconds


@pytest.mark.parametrize("text", ["", "<Task/>", TASK_XML.replace("PT15M", "P1D-bogus")])
def test_an_unknowable_tick_is_null(text: str) -> None:
    assert inbox_status.next_tick_from_xml(text, T0) is None


def test_the_tick_query_answers_null_without_a_scheduler() -> None:
    tick = inbox_status.query_next_tick(T0, resolve=lambda _name: None)
    assert tick is None


def test_the_published_cap_and_window_are_the_kits() -> None:
    """One budget: the numbers this schema publishes are the kit's, never a second pair."""
    numbers = (inbox_status.RUNS_CAP, inbox_status.WINDOW_S, set(inbox_status.STATES))
    assert numbers == (kit.RUNS_CAP, kit.WINDOW_S, set(kit.STATES))


def test_publish_accepts_the_kits_blocked_state(tmp_path: Path) -> None:
    """FLEET-KIT v14 (CS-1299) adds "blocked" to the kit's STATES; the schema publishes it."""
    inbox_status.publish(
        tmp_path,
        now=T0,
        state="blocked",
        task="Halted",
        task_started=T0 - 5,
        eta_s=None,
        next_tick=None,
        window=inbox_status.Window(count=0, frees_at=None),
    )
    assert _read(tmp_path)["state"] == "blocked"


def test_the_retired_counter_is_gone() -> None:
    """CS-1231 slice C retired the second counter; nothing may bring it back beside the kit's."""
    leftovers = [
        name
        for name in ("RunBudget", "CounterUnreadableError", "RUNS_NAME", "LOCK_NAME")
        if hasattr(inbox_status, name)
    ]
    assert leftovers == []
