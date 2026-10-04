r"""CS-1234 - the inbox responder's live status file and its task clock.

MAIN 0915 section 1 (operator order, relayed): every tree's responder publishes
its live state in ONE file at ONE relative path - the published inbox-status file
in the untracked control directory, named by `STATUS_NAME` below - schema 1,
written atomically on every state change and at least once per tick. The lane
widget reads it and never writes it. MAIN 0855 (operator order, relayed): AT MOST 120
headless runs STARTED per rolling 24 hours.

Two untracked files of this module live in the control directory:

  inbox_status.json        the published schema-1 status. Holds NO path, no env
                           value and no note name (CLAUDE.md rules 12 and 13).
  inbox_status_tasks.json  the task clock - the last ten durations per task
                           name, for `task_eta_s`, and when the last run ended.
                           Display only, so a garbled one reads as empty.

THE START COUNT IS THE KIT'S (CS-1231 slice C). This module once carried its
own `RunBudget`; it was retired when the responder moved onto FLEET-KIT v4's
spawn, which counts every headless start in the tree against ONE budget under
its lock and refuses every start on an unreadable one. Two counters would show
two different windows, so the responder reads the kit's budget for the
`runs_in_window` and `cap_frees_at` it publishes here. `RUNS_CAP` and
`WINDOW_S` below are the schema's published numbers and are pinned equal to the
kit's by the tests. The state names are the kit's `STATES`.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import statistics
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Final

_TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

SCHEMA: Final = 1
CODE: Final = "CS"

#: The schema's states, in the kit's spelling.
STATES: Final = ("idle", "running", "limit", "backoff", "halted", "refused")

#: The BASIC task names (MAIN 0915). Nothing finer is ever published.
TASKS: Final = (
    "Idle",
    "Checking Inbox",
    "Waiting for Slot",
    "Running Session",
    "Delivering Notes",
    "Committing",
    "Backing Off",
    "Halted",
    "Turn Limit Reached",
)

#: The one budget (MAIN 0855): starts per rolling window.
RUNS_CAP: Final = 120
WINDOW_S: Final = 86400

STATUS_NAME: Final = "inbox_status.json"
TASKS_NAME: Final = "inbox_status_tasks.json"

#: The scheduled task this responder runs under. A task NAME, not a path.
TASK_NAME: Final = "CS-InboxResponder"

#: ETA needs this many completed instances, and reads at most the last ten.
ETA_MIN: Final = 3
ETA_KEEP: Final = 10

_RENAME_ATTEMPTS: Final = 5
_RENAME_PAUSE_S: Final = 0.2
_QUERY_TIMEOUT_S: Final = 10
_NO_WINDOW: Final = 0x08000000 if os.name == "nt" else 0
_INTERVAL_RE: Final = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")
_TASK_NS: Final = "{http://schemas.microsoft.com/windows/2004/02/mit/task}"


@dataclass(frozen=True)
class Window:
    """The starts inside the kit's rolling window, and when the count next drops."""

    count: int
    frees_at: float | None


def iso(epoch: float) -> str:
    """ISO-8601 local time with its UTC offset, to the second."""
    return datetime.fromtimestamp(epoch).astimezone().isoformat(timespec="seconds")


def _atomic_write(target: Path, payload: bytes) -> None:
    """``tmp.write_bytes``; ``tmp.replace(target)``, retried for a Windows reader."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_bytes(payload)
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            tmp.replace(target)
        except PermissionError:
            if attempt == _RENAME_ATTEMPTS - 1:
                raise
            time.sleep(_RENAME_PAUSE_S)
        else:
            return


def _dump(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode("ascii")


# --- the task clock -------------------------------------------------------------


class TaskClock:
    """The last ten durations per task name, and when the last run ended."""

    def __init__(self, control: Path) -> None:
        """Keep the clock in ``control``/`TASKS_NAME`."""
        self.path = Path(control) / TASKS_NAME

    def _load(self) -> dict[str, Any]:
        try:
            parsed = json.loads(self.path.read_bytes().decode("ascii"))
        except (OSError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _durations(self, state: dict[str, Any], task: str) -> list[float]:
        table = state.get("durations")
        row = table.get(task) if isinstance(table, dict) else None
        if not isinstance(row, list):
            return []
        return [float(v) for v in row if type(v) in (int, float)]

    def _save(self, state: dict[str, Any]) -> None:
        with contextlib.suppress(OSError):
            _atomic_write(self.path, _dump(state))

    def record(self, task: str, seconds: float) -> None:
        """Append one completed instance. Never raises."""
        state = self._load()
        table = state.get("durations")
        table = dict(table) if isinstance(table, dict) else {}
        row = [*self._durations(state, task), round(float(seconds), 3)]
        table[task] = row[-ETA_KEEP:]
        state["durations"] = table
        self._save(state)

    def eta(self, task: str) -> int | None:
        """The median of the last ten, or None below three. Never a guess."""
        row = self._durations(self._load(), task)[-ETA_KEEP:]
        if len(row) < ETA_MIN:
            return None
        return round(statistics.median(row))

    def idle_since(self) -> float | None:
        """When the last run ended, or None."""
        value = self._load().get("idle_since")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    def set_idle_since(self, epoch: float) -> None:
        """Record when the last run ended. Never raises."""
        state = self._load()
        state["idle_since"] = float(epoch)
        self._save(state)


# --- the next tick --------------------------------------------------------------


def parse_interval(text: str) -> int | None:
    """An ISO-8601 duration as the scheduler writes it (``PT15M``), in seconds."""
    match = _INTERVAL_RE.match(text.strip())
    if match is None or not any(match.groups()):
        return None
    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    total = ((days * 24 + hours) * 60 + minutes) * 60 + seconds
    return total or None


def next_tick_from_xml(text: str, now: float) -> float | None:
    """The first trigger strictly after ``now``, from the task's XML export, or None."""
    try:
        root = ET.fromstring(text.encode("utf-8").replace(b'encoding="UTF-16"', b""))  # noqa: S314
    except (ET.ParseError, ValueError):
        return None
    start_el = next(root.iter(f"{_TASK_NS}StartBoundary"), None)
    interval_el = next(root.iter(f"{_TASK_NS}Interval"), None)
    if start_el is None or interval_el is None or not start_el.text or not interval_el.text:
        return None
    interval = parse_interval(interval_el.text)
    try:
        start = datetime.fromisoformat(start_el.text.strip()).timestamp()
    except ValueError:
        return None
    if interval is None:
        return None
    if now < start:
        return start
    steps = int((now - start) // interval) + 1
    return start + steps * interval


def query_next_tick(
    now: float, *, resolve: Callable[[str], str | None] = resolve_tool
) -> float | None:
    """Ask the scheduler for this responder's trigger. None when unknowable. NEVER RAISES.

    The export carries a user SID and the interpreter's home path, so nothing of
    it is ever echoed: only the two trigger fields are read.
    """
    tool = resolve("schtasks")
    if tool is None:
        return None
    try:
        done = subprocess.run(
            [tool, "/Query", "/TN", TASK_NAME, "/XML", "ONE"],
            capture_output=True,
            timeout=_QUERY_TIMEOUT_S,
            check=False,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    raw = done.stdout
    text = (
        raw.decode("utf-16")
        if raw[:2] in (b"\xff\xfe", b"\xfe\xff")
        else raw.decode("utf-8", errors="replace")
    )
    return next_tick_from_xml(text, now)


# --- the published status -------------------------------------------------------


def _record(
    *,
    now: float,
    state: str,
    task: str,
    task_started: float,
    eta_s: int | None,
    next_tick: float | None,
    window: Window,
) -> dict[str, Any]:
    if state not in STATES or task not in TASKS:
        msg = "a state or task name outside the published sets"
        raise ValueError(msg)
    return {
        "schema": SCHEMA,
        "code": CODE,
        "updated": iso(now),
        "state": state,
        "task": task,
        "task_started": iso(task_started),
        "task_eta_s": eta_s,
        "next_tick": None if next_tick is None else iso(next_tick),
        "runs_in_window": int(window.count),
        "runs_cap": RUNS_CAP,
        "window_s": WINDOW_S,
        "cap_frees_at": None if window.frees_at is None else iso(window.frees_at),
    }


def publish(
    control: Path,
    *,
    now: float,
    state: str,
    task: str,
    task_started: float,
    eta_s: int | None,
    next_tick: float | None,
    window: Window,
) -> None:
    """Write the schema-1 status atomically.

    Raises:
        ValueError: ``state`` or ``task`` is outside `STATES` / `TASKS`.
    """
    record = _record(
        now=now,
        state=state,
        task=task,
        task_started=task_started,
        eta_s=eta_s,
        next_tick=next_tick,
        window=window,
    )
    with contextlib.suppress(OSError):
        _atomic_write(Path(control) / STATUS_NAME, _dump(record))


def refresh(control: Path, *, now: float, next_tick: float | None, window: Window) -> bool:
    """Move ``updated`` on the standing status without changing its task. NEVER RAISES.

    The tick that finds another run holding the lock calls this, so a session
    that runs for hours still shows a live signal. Returns whether it wrote.
    """
    target = Path(control) / STATUS_NAME
    try:
        current = json.loads(target.read_bytes().decode("ascii"))
    except (OSError, ValueError):
        return False
    if not isinstance(current, dict) or current.get("schema") != SCHEMA:
        return False
    if current.get("state") not in STATES or current.get("task") not in TASKS:
        return False
    current["updated"] = iso(now)
    current["next_tick"] = None if next_tick is None else iso(next_tick)
    current["runs_in_window"] = int(window.count)
    current["cap_frees_at"] = None if window.frees_at is None else iso(window.frees_at)
    try:
        _atomic_write(target, _dump(current))
    except OSError:
        return False
    return True
