r"""CS-1234 - the inbox responder's live status file and its 120-per-24h run budget.

MAIN 0915 section 1 (operator order, relayed): every tree's responder publishes
its live state in ONE file at ONE relative path - the published inbox-status file
in the untracked control directory, named by `STATUS_NAME` below - schema 1,
written atomically on every state change and at least once per tick. The lane
widget reads it and never writes it. MAIN 0855 (operator order, relayed): AT MOST 120
headless runs STARTED per rolling 24 hours.

Three gitignored files live in the control directory beside each other:

  inbox_status.json        the published schema-1 status. Holds NO path, no env
                           value and no note name (CLAUDE.md rules 12 and 13).
  inbox_runs.json          the start counter, `{"schema": 1, "starts": [epoch]}`.
                           FAIL CLOSED: a counter that exists but cannot be read
                           or parsed refuses EVERY start and is never rewritten,
                           so it can never be "reset" by a garbled byte.
  inbox_status_tasks.json  the task clock - the last ten durations per task
                           name, for `task_eta_s`, and when the last run ended.
                           Display only, so a garbled one reads as empty.

SHAPED FOR THE KIT SWAP. FLEET-KIT v4 carries a `RunBudget` and a `STATES`
tuple; the state names here are the kit's, and `RunBudget.try_start` /
`RunBudget.snapshot` are the whole surface the responder uses, so a later slice
can replace this class without touching a caller.
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
from collections.abc import Callable, Iterator
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
RUNS_NAME: Final = "inbox_runs.json"
LOCK_NAME: Final = "inbox_runs.lock"
TASKS_NAME: Final = "inbox_status_tasks.json"

#: The scheduled task this responder runs under. A task NAME, not a path.
TASK_NAME: Final = "CS-InboxResponder"

#: ETA needs this many completed instances, and reads at most the last ten.
ETA_MIN: Final = 3
ETA_KEEP: Final = 10

_RENAME_ATTEMPTS: Final = 5
_RENAME_PAUSE_S: Final = 0.2
_LOCK_POLL_S: Final = 0.05
_QUERY_TIMEOUT_S: Final = 10
_NO_WINDOW: Final = 0x08000000 if os.name == "nt" else 0
_INTERVAL_RE: Final = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")
_TASK_NS: Final = "{http://schemas.microsoft.com/windows/2004/02/mit/task}"


class CounterUnreadableError(RuntimeError):
    """The start counter exists but cannot be read, parsed, locked or written."""


@dataclass(frozen=True)
class Window:
    """The starts inside the rolling window, and when the count next drops."""

    count: int
    frees_at: float | None


@dataclass(frozen=True)
class Verdict:
    """One start request's answer. ``count`` is the window AFTER the answer."""

    allowed: bool
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


# --- the run budget -------------------------------------------------------------


@contextlib.contextmanager
def _exclusive(lock_path: Path, timeout_s: float) -> Iterator[None]:
    """An exclusive OS lock on ``lock_path``. Raises `CounterUnreadableError` on timeout."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        deadline = time.monotonic() + timeout_s
        while True:
            try:
                if sys.platform == "win32":
                    import msvcrt  # noqa: PLC0415 - platform-specific

                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl  # noqa: PLC0415 - platform-specific

                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                if time.monotonic() >= deadline:
                    msg = "the start counter lock is held"
                    raise CounterUnreadableError(msg) from None
                time.sleep(_LOCK_POLL_S)
            else:
                break
        try:
            yield None
        finally:
            with contextlib.suppress(OSError):
                if sys.platform == "win32":
                    import msvcrt  # noqa: PLC0415 - platform-specific

                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl  # noqa: PLC0415 - platform-specific

                    fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


class RunBudget:
    """At most ``cap`` starts per rolling ``window_s``, counted persistently."""

    def __init__(
        self,
        control: Path,
        *,
        cap: int = RUNS_CAP,
        window_s: float = WINDOW_S,
        lock_timeout_s: float = 5.0,
    ) -> None:
        """Count starts in ``control``/`RUNS_NAME` under ``control``/`LOCK_NAME`."""
        self.path = Path(control) / RUNS_NAME
        self.lock_path = Path(control) / LOCK_NAME
        self.cap = cap
        self.window_s = float(window_s)
        self.lock_timeout_s = lock_timeout_s

    def locked(self) -> contextlib.AbstractContextManager[None]:
        """The counter's exclusive lock."""
        return _exclusive(self.lock_path, self.lock_timeout_s)

    def _starts(self) -> list[float]:
        """Every recorded start. A missing file is zero starts; anything else unreadable refuses."""
        try:
            data = self.path.read_bytes()
        except FileNotFoundError:
            return []
        except OSError:
            msg = "the start counter cannot be read"
            raise CounterUnreadableError(msg) from None
        try:
            parsed = json.loads(data.decode("ascii"))
        except ValueError:
            msg = "the start counter cannot be parsed"
            raise CounterUnreadableError(msg) from None
        starts = parsed.get("starts") if isinstance(parsed, dict) else None
        if not isinstance(starts, list) or not all(type(s) in (int, float) for s in starts):
            msg = "the start counter has the wrong shape"
            raise CounterUnreadableError(msg)
        return [float(s) for s in starts]

    def _window(self, starts: list[float], now: float) -> list[float]:
        return sorted(s for s in starts if s > now - self.window_s)

    def _frees(self, live: list[float]) -> float | None:
        return live[0] + self.window_s if live else None

    def snapshot(self, now: float) -> Window:
        """The window as it stands. Raises `CounterUnreadableError`."""
        with self.locked():
            live = self._window(self._starts(), now)
        return Window(count=len(live), frees_at=self._frees(live))

    def try_start(self, now: float) -> Verdict:
        """Record a start if the window has room. Raises `CounterUnreadableError`."""
        with self.locked():
            live = self._window(self._starts(), now)
            if len(live) >= self.cap:
                return Verdict(allowed=False, count=len(live), frees_at=self._frees(live))
            live.append(float(now))
            try:
                _atomic_write(self.path, _dump({"schema": SCHEMA, "starts": live}))
            except OSError:
                msg = "the start counter cannot be written"
                raise CounterUnreadableError(msg) from None
        return Verdict(allowed=True, count=len(live), frees_at=self._frees(live))


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
