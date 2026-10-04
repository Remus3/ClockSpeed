r"""CS-1226 - the one-shot inbox responder: spawn one routed worker when mail is waiting.

OPERATOR RULING, 2026-10-02 (recorded in docs/LEDGER.md): arm an autonomous
responder for the cross-repo channel. That ruling SUPERSEDES the "surfacing,
never replying" fence FOR THIS MODULE ONLY. The queue lane still never replies,
and `ops/loop/inbox_surface.py` keeps its fence and its tests unchanged.

THE FENCE STILL HOLDS BY STRUCTURE, so no exemption was written into it. This
module never composes, grades, sends or acknowledges anything. It decides
WHETHER to start a worker, starts it, and records the outcome. Everything the
worker does - reading notes, replying through the gated sender, acknowledging -
is instructed by the tracked prompt `tools/headless-inbox.md` and happens inside
the spawned process, so the reach walk over `ops/loop/*.py` in
`tests/ops/test_lane_inbox_surface.py` still finds no lane module that reaches
the sender, and it stays the arm that would redden if this file ever did.

ONE SHOT, `--once`, meant for a Windows scheduled task every fifteen minutes:

  1. A stop sentinel - `ops/loop/control/STOP` (the lane-wide one) or
     `ops/loop/control/lanes/INBOX_STOP` (this responder's own, mirroring the
     queue lane's QUEUE_STOP) - ends the run before anything else.
     The halted path still publishes `inbox_status.json` (state "halted")
     before it exits, so the widget shows a halt, never no signal.
  2. A single-instance named mutex; a run already in progress ends this one
     after refreshing the age of the status that run owns.
  3. The channel is listed through `inbox_surface.surface`, the watcher's READ
     API and nothing else. Zero unread ends the run quietly - no log line, so
     a quiet channel costs 96 no-ops a day and zero bytes. An UNMEASURED count
     never spawns: a run that could not look must not guess.
     LOOP DAMPING (`is_damped`): our OWN notes and notes marked TERMINAL or
     no-reply never start a run; with nothing else unread the pass is idle.
  4. A back-off file written after a usage-limit refusal holds every run for
     `BACKOFF_S`, so the account's "no" is not hammered every fifteen minutes.
  5. The worker's environment comes from `headless_route.child_env` - routed
     through the local proxy or REFUSED, never spawned any other way.
     CS-1234, MAIN 0855: at most `inbox_status.RUNS_CAP` starts per rolling
     24 hours, counted persistently under an exclusive lock. An unreadable
     counter refuses every start and is never reset (fail closed).
  6. `claude -p --output-format json --dangerously-skip-permissions`, the
     prompt piped on stdin, cwd the main tree root.
  7. The exit is classified and one JSON line is appended to a gitignored log
     under `data/`. The line holds outcome words, counts and durations ONLY -
     no path, no env value, no message body, no worker output (CLAUDE.md rules
     12 and 13).
  8. Every state change publishes the inbox-status file in the control directory
     (schema 1, MAIN 0915) through `ops/loop/inbox_status.py`.

THE SCHEDULED TASK, armed by the merger, never by this module. `<pythonw>` is
resolved at arm time (`(Get-Command pythonw).Source`); no interpreter path is
written into a tracked file:

  schtasks /Create /F /SC MINUTE /MO 15 /TN "Clockspeed inbox responder"
    /TR "\"<pythonw>\" \"C:\Clockspeed\ops\loop\inbox_responder.py\" --once"

It must run as the operator's own account, so the user environment store the
route reads is the right one.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Final

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

from ops.loop import headless_route, inbox_status, inbox_surface, winmutex  # noqa: E402

#: The control directory and the sentinels that stop this responder.
CONTROL: Final = _HERE / "control"
STOP_RELPATHS: Final = ("STOP", "lanes/INBOX_STOP")

#: The single-instance mutex, in the session namespace.
MUTEX_NAME: Final = "Local\\clockspeed-inbox-responder"

#: The tracked worker prompt, relative to the main tree root.
PROMPT_RELPATH: Final = Path("tools") / "headless-inbox.md"

#: The gitignored run log and back-off file, relative to the main tree root.
LOG_RELPATH: Final = Path("data") / "inbox_responder.jsonl"
BACKOFF_RELPATH: Final = Path("data") / "inbox_responder_backoff.json"

#: How long a usage-limit refusal holds every later run.
BACKOFF_S: Final = 3600.0

#: The worker's wall-clock ceiling. A reply plus a pushed fix runs the whole
#: suite in the pre-push hook; three hours bounds a wedged worker without
#: killing an honest one.
WORKER_TIMEOUT_S: Final = 3 * 3600.0

#: The worker argv after the resolved CLI. The prompt arrives on stdin.
WORKER_ARGS: Final = ("-p", "--output-format", "json", "--dangerously-skip-permissions")

#: Set on the worker for the reasons `ops/loop/run_lane.ps1` records (CS-1108):
#: nothing backgrounded, and a long foreground command survives.
WORKER_ENV: Final = {
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "2400000",
    "BASH_MAX_TIMEOUT_MS": "2400000",
    "BASH_DEFAULT_TIMEOUT_MS": "2400000",
}

EXIT_OK: Final = 0
EXIT_ROUTE_REFUSED: Final = 3
EXIT_WORKER_FAILED: Final = 4
EXIT_USAGE_LIMIT: Final = 5
EXIT_UNMEASURED: Final = 6
EXIT_SPAWN_FAILED: Final = 7
EXIT_TIMEOUT: Final = 8
EXIT_BUDGET_REFUSED: Final = 9

#: Every key a log line may carry. A closed set, graded by the tests.
LOG_KEYS: Final = frozenset(
    {"ts", "outcome", "exit", "unread", "returncode", "duration_s", "reason"}
)

#: The sender position in a channel note's name, and the damping markers.
_SENDER_RE: Final = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}-from-([A-Za-z0-9]+)-")
_TERMINAL_RE: Final = re.compile(r"terminal|no-?reply", re.IGNORECASE)
_EXEMPT_SENDER: Final = "MAIN"

_NO_WINDOW: Final = 0x08000000 if os.name == "nt" else 0
_KILL_TIMEOUT_S: Final = 20
_RENAME_ATTEMPTS: Final = 5
_RENAME_PAUSE_S: Final = 0.2


class WorkerTimeoutError(RuntimeError):
    """The worker outlived `WORKER_TIMEOUT_S` and was killed."""


def _default_lock() -> Any:
    return winmutex.hold(MUTEX_NAME, timeout=0.0)


def _kill_tree(pid: int) -> None:
    """Kill the worker and everything it started. Reports nothing."""
    killer = resolve_tool("taskkill")
    if killer is None:
        return
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run(
            [killer, "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            timeout=_KILL_TIMEOUT_S,
            check=False,
            creationflags=_NO_WINDOW,
        )


def _spawn_worker(
    argv: list[str], stdin: bytes, cwd: Path, env: dict[str, str], timeout: float
) -> tuple[int, str]:
    """Run the worker to completion. THE DEFAULT REALLY STARTS A PROCESS.

    Raises:
        OSError: The process could not be started.
        WorkerTimeoutError: The worker outlived ``timeout`` and was killed.
    """
    proc = subprocess.Popen(
        argv,
        cwd=str(cwd),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=_NO_WINDOW,
    )
    try:
        out, _ = proc.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(proc.pid)
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            proc.communicate(timeout=_KILL_TIMEOUT_S)
        raise WorkerTimeoutError from None
    return int(proc.returncode), out.decode("utf-8", errors="replace")


def _replace_with_retry(tmp: Path, target: Path) -> None:
    """``tmp.replace(target)``, retried for a reader holding the target on Windows."""
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            tmp.replace(target)
        except PermissionError:
            if attempt == _RENAME_ATTEMPTS - 1:
                raise
            time.sleep(_RENAME_PAUSE_S)
        else:
            return


def _backoff_until(path: Path) -> float:
    """The epoch second the back-off lifts, or 0 for none or an unreadable file."""
    try:
        parsed = json.loads(path.read_bytes().decode("ascii"))
    except (OSError, ValueError):
        return 0.0
    until = parsed.get("until") if isinstance(parsed, dict) else None
    if isinstance(until, bool) or not isinstance(until, (int, float)):
        return 0.0
    return float(until)


def _write_backoff(path: Path, until: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(json.dumps({"until": until}).encode("ascii") + b"\n")
    _replace_with_retry(tmp, path)


def _log(root: Path, now: float, outcome: str, code: int, **fields: Any) -> None:
    """Append one JSON line. Authored words, counts and durations only. Never raises."""
    record: dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
        "outcome": outcome,
        "exit": code,
    }
    record.update({key: val for key, val in fields.items() if key in LOG_KEYS})
    line = json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n"
    with contextlib.suppress(OSError):
        target = root / LOG_RELPATH
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("ab") as handle:
            handle.write(line.encode("ascii"))


def _stopped(control: Path) -> bool:
    return any((control / rel).exists() for rel in STOP_RELPATHS)


def _halted_since(control: Path, fallback: float) -> float:
    """When the standing sentinel was placed - its mtime - or ``fallback``."""
    stamps: list[float] = []
    for rel in STOP_RELPATHS:
        with contextlib.suppress(OSError):
            stamps.append((control / rel).stat().st_mtime)
    return min(stamps) if stamps else fallback


def is_damped(name: str) -> bool:
    """Loop damping (MAIN 0845 section 3, kept by 0855): a note that never starts a run.

    Two rules, read from the NAME only - a body scan damps the very orders that
    quote the rule (LL 0958 measured it on MAIN 0845 and 0855):

      1. OUR OWN note: the sender position, the first ``-from-<CODE>-`` after
         the timestamp, is this tree's code. A later ``-from-CS-`` quoted inside
         another sender's name is not ours.
      2. A note marked TERMINAL or no-reply, case-insensitive. MAIN's notes are
         exempt, because an order needs acting on whether or not it wants a reply.
    """
    match = _SENDER_RE.match(name)
    sender = match.group(1) if match else None
    if sender == inbox_status.CODE:
        return True
    if sender == _EXEMPT_SENDER:
        return False
    return _TERMINAL_RE.search(name) is not None


def _worthy(fact: Mapping[str, Any], unread: int) -> int:
    """Unread items that may start a run. An item past the listing cap counts as live."""
    names = fact.get("names")
    listed = [n for n in names if isinstance(n, str)] if isinstance(names, list) else []
    return max(0, unread - sum(1 for name in listed if is_damped(name)))


class _Board:
    """Publishes `inbox_status` for one pass. Every write is display only and never raises."""

    def __init__(
        self,
        control: Path,
        now: Callable[[], float],
        tick: Callable[[float], float | None],
    ) -> None:
        self.control = control
        self.now = now
        self.tick = tick
        self.clock = inbox_status.TaskClock(control)
        self.budget = inbox_status.RunBudget(control)
        self._tick: float | None = None
        self._tick_asked = False

    def next_tick(self, at: float) -> float | None:
        """The scheduler's next fire, asked once per pass unless it has passed."""
        if not self._tick_asked or (self._tick is not None and self._tick <= at):
            self._tick_asked = True
            self._tick = self.tick(at)
        return self._tick

    def window(self, at: float) -> inbox_status.Window:
        """The run window. An unreadable counter renders FULL - it refuses every start."""
        try:
            return self.budget.snapshot(at)
        except inbox_status.CounterUnreadableError:
            return inbox_status.Window(count=inbox_status.RUNS_CAP, frees_at=None)

    def show(
        self,
        state: str,
        task: str,
        *,
        started: float | None = None,
        window: inbox_status.Window | None = None,
    ) -> None:
        at = self.now()
        inbox_status.publish(
            self.control,
            now=at,
            state=state,
            task=task,
            task_started=at if started is None else started,
            eta_s=self.clock.eta(task),
            next_tick=self.next_tick(at),
            window=self.window(at) if window is None else window,
        )

    def idle(self) -> None:
        since = self.clock.idle_since()
        if since is None:
            since = self.now()
            self.clock.set_idle_since(since)
        self.show("idle", "Idle", started=since)

    def ended(self, finished: float, seconds: float) -> None:
        self.clock.record("Running Session", seconds)
        self.clock.set_idle_since(finished)

    def refresh(self) -> None:
        at = self.now()
        inbox_status.refresh(
            self.control, now=at, next_tick=self.next_tick(at), window=self.window(at)
        )


def _outcome_exit(outcome: str) -> int:
    return {
        headless_route.OUTCOME_OK: EXIT_OK,
        headless_route.OUTCOME_USAGE_LIMIT: EXIT_USAGE_LIMIT,
    }.get(outcome, EXIT_WORKER_FAILED)


def run_once(  # noqa: PLR0913 - every outward seam is injectable
    *,
    root: Path | None = None,
    control_dir: Path | None = None,
    now: Callable[[], float] = time.time,
    surface: Callable[[Any], Mapping[str, Any]] | None = None,
    lock: Callable[[], Any] | None = None,
    route: Callable[[Mapping[str, str]], dict[str, str]] | None = None,
    spawn: Callable[..., tuple[int, str]] | None = None,
    resolve: Callable[[str], str | None] | None = None,
    next_tick: Callable[[float], float | None] | None = None,
) -> int:
    """One responder pass. See the module docstring for the order.

    Args:
        root: The main tree root, or None to resolve it from this checkout.
        control_dir: The sentinel directory, or None for ``ops/loop/control``.
        now: The wall clock.
        surface: The channel lister, or None for ``inbox_surface.surface``.
        lock: A zero-argument context-manager factory, or None for the mutex.
        route: Builds the routed env, or None for ``headless_route.child_env``.
        spawn: Runs the worker, or None for the real spawn.
        resolve: Resolves a tool from PATH, or None for ``resolve_tool``.
        next_tick: The scheduler's next fire after an epoch, or None for the
            real query of `inbox_status.TASK_NAME`.

    Returns:
        The process exit code.
    """
    control = CONTROL if control_dir is None else Path(control_dir)
    board = _Board(control, now, inbox_status.query_next_tick if next_tick is None else next_tick)
    if _stopped(control):
        # QUIET in the log, like a quiet channel: a standing sentinel would
        # otherwise write 96 identical lines a day. The STATUS is still
        # published, so the widget shows a halt rather than no signal.
        board.show("halted", "Halted", started=_halted_since(control, now()))
        return EXIT_OK
    main_root = inbox_surface.channel_root() if root is None else Path(root)
    take = _default_lock if lock is None else lock
    try:
        with take():
            return _locked_pass(
                main_root,
                now,
                inbox_surface.surface if surface is None else surface,
                headless_route.child_env if route is None else route,
                _spawn_worker if spawn is None else spawn,
                resolve_tool if resolve is None else resolve,
                board,
            )
    except winmutex.MutexTimeout:
        # The run holding the lock owns the status; only its age is refreshed,
        # so an hours-long session still shows a live signal.
        board.refresh()
        _log(main_root, now(), "lock_held", EXIT_OK)
        return EXIT_OK


def _locked_pass(
    root: Path,
    now: Callable[[], float],
    surface: Callable[[Any], Mapping[str, Any]],
    route: Callable[[Mapping[str, str]], dict[str, str]],
    spawn: Callable[..., tuple[int, str]],
    resolve: Callable[[str], str | None],
    board: _Board,
) -> int:
    """Everything after the lock is held."""
    checking = now()
    board.show("idle", "Checking Inbox", started=checking)
    fact = surface(root)
    board.clock.record("Checking Inbox", now() - checking)
    unread = fact.get("unread")
    if type(unread) is not int:
        _log(root, now(), "unmeasured", EXIT_UNMEASURED)
        board.show("refused", "Halted")
        return EXIT_UNMEASURED
    if _worthy(fact, unread) == 0:
        board.idle()
        return EXIT_OK
    started = now()
    held_until = _backoff_until(root / BACKOFF_RELPATH)
    if started < held_until:
        _log(root, started, "backoff", EXIT_OK, unread=unread)
        board.show("backoff", "Backing Off", started=held_until - BACKOFF_S)
        return EXIT_OK
    try:
        env = route(os.environ)
    except headless_route.HeadlessRouteRefused as refused:
        _log(
            root, started, "route_refused", EXIT_ROUTE_REFUSED, unread=unread, reason=refused.reason
        )
        board.show("refused", "Halted")
        return EXIT_ROUTE_REFUSED
    env.update(WORKER_ENV)
    cli = resolve("claude")
    try:
        prompt = (root / PROMPT_RELPATH).read_bytes()
    except OSError:
        cli = None
    if cli is None:
        _log(root, started, "spawn_failed", EXIT_SPAWN_FAILED, unread=unread)
        board.show("refused", "Halted")
        return EXIT_SPAWN_FAILED
    return _counted_spawn(
        root,
        now,
        board,
        lambda: spawn([cli, *WORKER_ARGS], prompt, root, env, WORKER_TIMEOUT_S),
        unread,
        started,
    )


def _counted_spawn(
    root: Path,
    now: Callable[[], float],
    board: _Board,
    run: Callable[[], tuple[int, str]],
    unread: int,
    started: float,
) -> int:
    """Count the start against the cap, run the worker, publish and log the outcome."""
    try:
        verdict = board.budget.try_start(started)
    except inbox_status.CounterUnreadableError:
        # FAIL CLOSED: the counter is never reset, and nothing starts uncounted.
        _log(root, started, "budget_refused", EXIT_BUDGET_REFUSED, unread=unread)
        board.show("refused", "Halted")
        return EXIT_BUDGET_REFUSED
    window = inbox_status.Window(count=verdict.count, frees_at=verdict.frees_at)
    if not verdict.allowed:
        _log(root, started, "limit", EXIT_OK, unread=unread)
        board.show("limit", "Turn Limit Reached", window=window)
        return EXIT_OK
    board.show("running", "Running Session", started=started, window=window)
    try:
        returncode, output = run()
    except WorkerTimeoutError:
        finished = now()
        board.ended(finished, finished - started)
        _log(root, finished, "timeout", EXIT_TIMEOUT, unread=unread)
        board.idle()
        return EXIT_TIMEOUT
    except OSError:
        _log(root, started, "spawn_failed", EXIT_SPAWN_FAILED, unread=unread)
        board.show("refused", "Halted")
        return EXIT_SPAWN_FAILED
    outcome = headless_route.classify_exit(returncode, output)
    finished = now()
    board.ended(finished, finished - started)
    if outcome == headless_route.OUTCOME_USAGE_LIMIT:
        _write_backoff(root / BACKOFF_RELPATH, finished + BACKOFF_S)
    code = _outcome_exit(outcome)
    _log(
        root,
        finished,
        outcome,
        code,
        unread=unread,
        returncode=returncode,
        duration_s=round(finished - started, 3),
    )
    if outcome == headless_route.OUTCOME_USAGE_LIMIT:
        board.show("backoff", "Backing Off", started=finished)
    else:
        board.idle()
    return code


def main(argv: Sequence[str] | None = None) -> int:
    """Parse ``--once`` and run one pass."""
    parser = argparse.ArgumentParser(description="CS-1226 one-shot inbox responder")
    parser.add_argument("--once", action="store_true", required=True, help="run one pass")
    parser.parse_args(argv)
    return run_once()


if __name__ == "__main__":
    raise SystemExit(main())
