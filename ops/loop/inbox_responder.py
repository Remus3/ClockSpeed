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
  2. A single-instance named mutex; a run already in progress ends this one.
  3. The channel is listed through `inbox_surface.surface`, the watcher's READ
     API and nothing else. Zero unread ends the run quietly - no log line, so
     a quiet channel costs 96 no-ops a day and zero bytes. An UNMEASURED count
     never spawns: a run that could not look must not guess.
  4. A back-off file written after a usage-limit refusal holds every run for
     `BACKOFF_S`, so the account's "no" is not hammered every fifteen minutes.
  5. The worker's environment comes from `headless_route.child_env` - routed
     through the local proxy or REFUSED, never spawned any other way.
  6. `claude -p --output-format json --dangerously-skip-permissions`, the
     prompt piped on stdin, cwd the main tree root.
  7. The exit is classified and one JSON line is appended to a gitignored log
     under `data/`. The line holds outcome words, counts and durations ONLY -
     no path, no env value, no message body, no worker output (CLAUDE.md rules
     12 and 13).

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

from ops.loop import headless_route, inbox_surface, winmutex  # noqa: E402

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

#: Every key a log line may carry. A closed set, graded by the tests.
LOG_KEYS: Final = frozenset(
    {"ts", "outcome", "exit", "unread", "returncode", "duration_s", "reason"}
)

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


def _outcome_exit(outcome: str) -> int:
    return {
        headless_route.OUTCOME_OK: EXIT_OK,
        headless_route.OUTCOME_USAGE_LIMIT: EXIT_USAGE_LIMIT,
    }.get(outcome, EXIT_WORKER_FAILED)


def run_once(
    *,
    root: Path | None = None,
    control_dir: Path | None = None,
    now: Callable[[], float] = time.time,
    surface: Callable[[Any], Mapping[str, Any]] | None = None,
    lock: Callable[[], Any] | None = None,
    route: Callable[[Mapping[str, str]], dict[str, str]] | None = None,
    spawn: Callable[..., tuple[int, str]] | None = None,
    resolve: Callable[[str], str | None] | None = None,
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

    Returns:
        The process exit code.
    """
    main_root = inbox_surface.channel_root() if root is None else Path(root)
    control = CONTROL if control_dir is None else Path(control_dir)
    if _stopped(control):
        # QUIET, like a quiet channel: a standing sentinel would otherwise write
        # 96 identical lines a day for as long as it stands.
        return EXIT_OK
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
            )
    except winmutex.MutexTimeout:
        _log(main_root, now(), "lock_held", EXIT_OK)
        return EXIT_OK


def _locked_pass(  # noqa: PLR0911 - one return per outcome, each logged
    root: Path,
    now: Callable[[], float],
    surface: Callable[[Any], Mapping[str, Any]],
    route: Callable[[Mapping[str, str]], dict[str, str]],
    spawn: Callable[..., tuple[int, str]],
    resolve: Callable[[str], str | None],
) -> int:
    """Everything after the lock is held."""
    fact = surface(root)
    unread = fact.get("unread")
    if type(unread) is not int:
        _log(root, now(), "unmeasured", EXIT_UNMEASURED)
        return EXIT_UNMEASURED
    if unread == 0:
        return EXIT_OK
    started = now()
    if started < _backoff_until(root / BACKOFF_RELPATH):
        _log(root, started, "backoff", EXIT_OK, unread=unread)
        return EXIT_OK
    try:
        env = route(os.environ)
    except headless_route.HeadlessRouteRefused as refused:
        _log(
            root, started, "route_refused", EXIT_ROUTE_REFUSED, unread=unread, reason=refused.reason
        )
        return EXIT_ROUTE_REFUSED
    env.update(WORKER_ENV)
    cli = resolve("claude")
    try:
        prompt = (root / PROMPT_RELPATH).read_bytes()
    except OSError:
        cli = None
    if cli is None:
        _log(root, started, "spawn_failed", EXIT_SPAWN_FAILED, unread=unread)
        return EXIT_SPAWN_FAILED
    try:
        returncode, output = spawn([cli, *WORKER_ARGS], prompt, root, env, WORKER_TIMEOUT_S)
    except WorkerTimeoutError:
        _log(root, started, "timeout", EXIT_TIMEOUT, unread=unread)
        return EXIT_TIMEOUT
    except OSError:
        _log(root, started, "spawn_failed", EXIT_SPAWN_FAILED, unread=unread)
        return EXIT_SPAWN_FAILED
    outcome = headless_route.classify_exit(returncode, output)
    finished = now()
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
    return code


def main(argv: Sequence[str] | None = None) -> int:
    """Parse ``--once`` and run one pass."""
    parser = argparse.ArgumentParser(description="CS-1226 one-shot inbox responder")
    parser.add_argument("--once", action="store_true", required=True, help="run one pass")
    parser.parse_args(argv)
    return run_once()


if __name__ == "__main__":
    raise SystemExit(main())
