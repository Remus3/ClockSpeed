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
  5. CS-1231 SLICE C - THE WORKER STARTS ONLY THROUGH THE FLEET KIT'S SPAWN
     HELPER (`ops/fleet_kit/fleet_headless.spawn`, FLEET item 10), the one path
     that starts `claude` on this machine. The kit reads the second-account
     proxy from the user store or REFUSES, with no fallback; counts the start
     against its tree-wide budget of 120 per rolling 24 hours under a lock,
     refusing every start on an unreadable budget and never resetting it
     (CS-1234, MAIN 0855); keeps the CLI off the working directory; and kills
     the whole tree on a timeout. `floors_in_hooks=True`, because this tree's
     floors live in hooks and `--bare` skips them, so the kit refuses a bare run.
  6. Strict MCP and project settings, the prompt on stdin, cwd the main tree
     root, `--dangerously-skip-permissions` the one extra flag. Sonnet unless a
     live note is an ORDER, FIX or RULING or sits past the listing cap; effort
     low only when every live note is an acknowledgement (`_kit_inputs`).
  7. The exit is classified and one JSON line is appended to a gitignored log
     under `data/`. The line holds outcome words, counts and durations ONLY -
     no path, no env value, no message body, no worker output (CLAUDE.md rules
     12 and 13).
  8. Every state change publishes the inbox-status file in the control directory
     (schema 1, MAIN 0915) through `ops/loop/inbox_status.py`. The kit writes the
     same file on its own transitions; the responder writes after each of them,
     so the published task, ETA and window are always the responder's.

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
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Final

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ops.fleet_kit import fleet_headless as kit  # noqa: E402
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

#: The one flag the kit's argv does not carry. The worker runs unattended, so a
#: permission prompt would wait forever; the kit refuses only fallback and bare
#: flags here.
KIT_EXTRA: Final = ("--dangerously-skip-permissions",)

#: The kit's refusal when its budget lock stays busy - a counting failure, so it
#: is logged with the unreadable budget rather than with a proxy refusal. The
#: kit is byte-pinned, so this string moves only with a new kit version.
KIT_LOCK_BUSY: Final = "budget lock busy"

#: Set on the worker for the reasons `ops/loop/run_lane.ps1` records (CS-1108):
#: nothing backgrounded, and a long foreground command survives. The kit builds
#: the child's environment from this process's own, so they are set here, for
#: the length of the spawn only.
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

_RENAME_ATTEMPTS: Final = 5
_RENAME_PAUSE_S: Final = 0.2

#: The kit's own spawn, and its injectable seams by name. The responder passes
#: every key through untouched; production passes none, so every seam is the
#: kit's fail-closed default.
KitSpawn = Callable[..., tuple[dict[str, Any], str]]


def _default_lock() -> Any:
    return winmutex.hold(MUTEX_NAME, timeout=0.0)


@contextlib.contextmanager
def _worker_env() -> Iterator[None]:
    """`WORKER_ENV` in this process's environment for the spawn, then restored."""
    saved = {key: os.environ.get(key) for key in WORKER_ENV}
    os.environ.update(WORKER_ENV)
    try:
        yield None
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def kit_spawn(
    root: Path,
    prompt: str,
    *,
    writes_code: bool,
    effort: str,
    before_start: Callable[[], None],
    **seams: Any,
) -> tuple[dict[str, Any], str]:
    """Start the worker through the fleet kit and wait. THE DEFAULT REALLY STARTS A PROCESS.

    ``before_start`` runs after the kit has refused or counted the start and
    written its own "running" status, immediately before the process starts, so
    the responder's status is the one the run is shown under.

    Args:
        root: The main tree root - the worker's cwd and the kit's file root.
        prompt: The worker prompt, sent on stdin.
        writes_code: Whether the kit picks the code model.
        effort: The kit effort word.
        before_start: Called once, just before the process starts.
        **seams: Passed to ``kit.spawn`` untouched. ``run`` is wrapped, not
            replaced, so the worker's own output can be classified.

    Returns:
        The kit's usage line, and the worker's captured stdout.

    Raises:
        kit.Refused: Before anything starts, when the fleet rules forbid it.
    """
    inner = seams.pop("run", None) or kit._run  # noqa: SLF001 - the kit's own default
    captured: list[str] = []

    def run(argv: list[str], **kw: Any) -> Any:
        before_start()
        proc = inner(argv, **kw)
        out = getattr(proc, "stdout", None)
        captured.append(out if isinstance(out, str) else "")
        return proc

    with _worker_env():
        line = kit.spawn(
            root,
            inbox_status.CODE,
            prompt,
            writes_code=writes_code,
            effort=effort,
            bare=False,
            floors_in_hooks=True,
            stdin=True,
            cwd=root,
            timeout=WORKER_TIMEOUT_S,
            extra=KIT_EXTRA,
            run=run,
            **seams,
        )
    usage: dict[str, Any] = dict(line) if isinstance(line, dict) else {}
    return usage, captured[-1] if captured else ""


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


def _listed(fact: Mapping[str, Any]) -> list[str]:
    names = fact.get("names")
    return [n for n in names if isinstance(n, str)] if isinstance(names, list) else []


def _worthy(fact: Mapping[str, Any], unread: int) -> int:
    """Unread items that may start a run. An item past the listing cap counts as live."""
    return max(0, unread - sum(1 for name in _listed(fact) if is_damped(name)))


def _kit_inputs(fact: Mapping[str, Any], unread: int) -> tuple[bool, str]:
    """``(writes_code, effort)`` for the kit, from the live note NAMES only.

    MAIN 0855: sonnet unless the work writes code, effort low for
    acknowledgements. One pass answers every live note, so the pass takes the
    heaviest: the code model when any live note is an ORDER, FIX or RULING (the
    classes the kit never damps), and effort low only when the kit reads every
    live note as an acknowledgement. A note past the listing cap is unseen, so
    it is assumed heavy rather than guessed light.
    """
    listed = _listed(fact)
    live = [name for name in listed if not is_damped(name)]
    unseen = unread > len(listed)
    writes_code = unseen or any(str(kit.note_class(name)) in kit.NEVER_DAMP for name in live)
    efforts = {str(kit.pick_effort(name)) for name in live}
    effort = "low" if live and not unseen and efforts == {"low"} else "medium"
    return writes_code, effort


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
        # THE KIT'S BUDGET, read where the kit writes it: one tree-wide count
        # for every headless start, never a second counter beside it.
        self.budget = kit.RunBudget(control / kit.BUDGET_REL.name)
        self._tick: float | None = None
        self._tick_asked = False

    def next_tick(self, at: float) -> float | None:
        """The scheduler's next fire, asked once per pass unless it has passed."""
        if not self._tick_asked or (self._tick is not None and self._tick <= at):
            self._tick_asked = True
            self._tick = self.tick(at)
        return self._tick

    def window(self, at: float) -> inbox_status.Window:
        """The kit's run window. An unreadable budget renders FULL - it refuses every start."""
        self.budget.clock = lambda: at
        count = int(self.budget.used())
        frees = self.budget.frees_at()
        return inbox_status.Window(count=count, frees_at=None if frees is None else float(frees))

    def show(self, state: str, task: str, *, started: float | None = None) -> None:
        at = self.now()
        inbox_status.publish(
            self.control,
            now=at,
            state=state,
            task=task,
            task_started=at if started is None else started,
            eta_s=self.clock.eta(task),
            next_tick=self.next_tick(at),
            window=self.window(at),
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


def run_once(
    *,
    root: Path | None = None,
    control_dir: Path | None = None,
    now: Callable[[], float] = time.time,
    surface: Callable[[Any], Mapping[str, Any]] | None = None,
    lock: Callable[[], Any] | None = None,
    spawn: KitSpawn | None = None,
    kit_seams: Mapping[str, Any] | None = None,
    next_tick: Callable[[float], float | None] | None = None,
) -> int:
    """One responder pass. See the module docstring for the order.

    Args:
        root: The main tree root, or None to resolve it from this checkout.
        control_dir: The sentinel directory, or None for ``ops/loop/control``.
        now: The wall clock.
        surface: The channel lister, or None for ``inbox_surface.surface``.
        lock: A zero-argument context-manager factory, or None for the mutex.
        spawn: The kit spawn, or None for `kit_spawn`.
        kit_seams: Passed to the kit's ``spawn`` untouched - its proxy, probe,
            executable and runner seams. None in production, so every one is
            the kit's fail-closed default.
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
                kit_spawn if spawn is None else spawn,
                dict(kit_seams or {}),
                board,
            )
    except winmutex.MutexTimeout:
        # The run holding the lock owns the status; only its age is refreshed,
        # so an hours-long session still shows a live signal.
        board.refresh()
        _log(main_root, now(), "lock_held", EXIT_OK)
        return EXIT_OK


def _locked_pass(  # noqa: PLR0911 - one return per recorded outcome
    root: Path,
    now: Callable[[], float],
    surface: Callable[[Any], Mapping[str, Any]],
    spawn: KitSpawn,
    seams: dict[str, Any],
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
        prompt = (root / PROMPT_RELPATH).read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        _log(root, started, "spawn_failed", EXIT_SPAWN_FAILED, unread=unread)
        board.show("refused", "Halted")
        return EXIT_SPAWN_FAILED
    writes_code, effort = _kit_inputs(fact, unread)

    def before_start() -> None:
        board.show("running", "Running Session", started=started)

    try:
        line, output = spawn(
            root,
            prompt,
            writes_code=writes_code,
            effort=effort,
            before_start=before_start,
            **seams,
        )
    except kit.Refused as refused:
        return _refused(root, board, refused, unread, started)
    except OSError:
        finished = now()
        board.ended(finished, finished - started)
        _log(root, finished, "spawn_failed", EXIT_SPAWN_FAILED, unread=unread)
        board.show("refused", "Halted")
        return EXIT_SPAWN_FAILED
    return _finished(root, now, board, line, output, unread, started)


def _refused(root: Path, board: _Board, refused: Exception, unread: int, started: float) -> int:
    """The kit refused before anything started. Nothing ran, so no duration is recorded."""
    if isinstance(refused, kit.BudgetUnreadable) or refused.args == (KIT_LOCK_BUSY,):
        # FAIL CLOSED: the kit never resets its budget, and nothing starts uncounted.
        _log(root, started, "budget_refused", EXIT_BUDGET_REFUSED, unread=unread)
        board.show("refused", "Halted")
        return EXIT_BUDGET_REFUSED
    window = board.window(started)
    if window.count >= board.budget.cap:
        _log(root, started, "limit", EXIT_OK, unread=unread)
        board.show("limit", "Turn Limit Reached")
        return EXIT_OK
    # The proxy, the door or the executable. The kit's words are not logged:
    # the outcome word is the closed vocabulary, and the reason stays authored.
    _log(root, started, "kit_refused", EXIT_ROUTE_REFUSED, unread=unread, reason="kit")
    board.show("refused", "Halted")
    return EXIT_ROUTE_REFUSED


def _finished(
    root: Path,
    now: Callable[[], float],
    board: _Board,
    line: Mapping[str, Any],
    output: str,
    unread: int,
    started: float,
) -> int:
    """Classify the finished run, publish and log it."""
    finished = now()
    board.ended(finished, finished - started)
    if line.get("error") == "timeout":
        _log(root, finished, "timeout", EXIT_TIMEOUT, unread=unread)
        board.idle()
        return EXIT_TIMEOUT
    rc = line.get("rc")
    returncode = rc if type(rc) is int else None
    outcome = headless_route.classify_exit(returncode, output)
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
