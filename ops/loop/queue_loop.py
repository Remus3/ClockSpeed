#!/usr/bin/env python
r"""Queue loop - the driver that turns a ONE-ROW worker into a queue drain.

`ops/loop/lanes.py` decides WHO may run. `ops/loop/lane_launcher.py` turns a
claim into a running headless worker. Neither of them ever runs a second time on
its own. This module is the missing repeat, and it is also the thing that WAITS.

WHY THE DRIVER OWNS THE REPEAT, NOT THE WORKER. The cheaper design is a worker
that loops internally: read a row, do it, read the next. It fails two ways.
First, context - a `claude -p` worker accumulates every row's transcript for the
whole run, and quality degrades long before the window is full. Second, blast
radius - a worker killed on row three loses rows four through twelve with it,
because they were never separate units of work. ONE ROW PER PROCESS makes a
crash cost exactly one row and makes every row start from a clean context that
reads its state off disk. The price is a driver, and the driver is this file.

WHY THE DRIVER OWNS EVERY WAIT, AND THE WORKER OWNS NONE. This is the reason the
file exists in this shape rather than a cheaper one, and it was paid for twice
in the tree this was ported from. The rule "block until your own CI run
finishes" was written as PROSE in the worker's prompt and MEASURED over six
cycles: cycles 2 and 3 complied, cycles 4, 5 and 6 exited early, and each early
exit let the next cycle's push cancel the run the previous cycle was being
graded on. AN INSTRUCTION A WORKER CAN RATIONALIZE PAST IS NOT A MECHANISM. The
driver cannot rationalize: it is the only thing that starts the next cycle, so
while it is inside the wait there exists nothing that could cancel the run. The
serialization is structural rather than hopeful, and the cost is a Python
process sleeping - which is free, unlike an agent sitting in a poll loop.

WHAT THAT MEANS AGAINST **THIS** REPO'S CI, read out of the two workflow files
rather than assumed:

  - `.github/workflows/tier1.yml` fires on `push: branches: ['**']`, so a
    worker's push to `main` runs it automatically. It sets
    `concurrency.cancel-in-progress: true`, so cycle N+1's push CANCELS cycle
    N's still-running tier1. That is the same self-cancelling trap, and the
    driver-owned wait is what defeats it.
  - `.github/workflows/tier2.yml` fires on `schedule`, on a `v*` TAG push, and
    on `workflow_dispatch` - NOT on a branch push. So the full suite (both
    OSes, the clean-checkout probe, the shell suite) does not exist for a
    worker's commit unless something dispatches it. This driver dispatches it.
    tier2 sets `cancel-in-progress: false`, so a dispatched run cannot be
    cancelled by the next cycle at all.

So a cycle's acceptance is: tier1 on the pushed sha, plus a dispatched tier2,
both graded on their JOBS, both waited out here. The worker never blocks.

A NOTE THAT IS NOT AN EXCUSE: `.githooks/pre-push` runs the WHOLE suite with
`-x` on every push, despite its own header calling itself the fast subset. It is
a FROZEN file (CLAUDE.md section 6) and this item does not touch it. The
consequence is stated rather than hidden - the worker's push pays a full local
suite inside the hook, and the fast-subset rule in `tools/headless-queue.md`
therefore governs the worker's own iteration loop, not its push.

A VERDICT IS A SUMMARY LINE **AND** AN EXIT CODE, NEVER EITHER ALONE. A crashed
parallel run leaves no summary line, and `grep -c FAILED` over that log returns
0 - which reads exactly like green. `summarize_pytest` therefore answers `ok`
only when a summary line was PARSED and the exit code is 0, and it carries the
verbatim line and the integer code into the ledger so the claim can be re-graded
from the file alone. The same principle governs the CI grader: a required job
that matches NOTHING is `unavailable`, an answer about the tool, and never a
pass.

EVERY MATRIX LEG IS GRADED, NOT THE POOL. `full suite (ubuntu-latest)` and
`full suite (windows-latest)` are two jobs, and a grader that asked "did any leg
pass" would let the weakest go unmeasured while its acceptance clause still read
green. `grade_ci_jobs` requires EACH matched job to be `success` and names the
one that was not.

WHY THE LANE LOCK IS TAKEN PER CYCLE, NOT HELD ACROSS THE LOOP. `lane_state`
decides FREE / RUNNING / RECLAIMABLE by PROBING the recorded pid, and
`launch_lane` re-points the lock at the WORKER. Across a whole loop the lock
would name a worker that exits after row one while the driver keeps running, so
the lane would read RECLAIMABLE under a live driver - the exact ambiguity the
three states exist to remove. Per-cycle acquire plus a `finally` release keeps
the lock's meaning honest: held means a worker is up right now.

WHY A REFUSED ACQUIRE IS NOT AN ERROR. `try_acquire_lane` answers
`{"ok": False, "refused": "lane_held"}` and writes nothing when the lane is
genuinely busy. A driver that treated that as fatal would die the first night
the operator's own session overlapped by a minute.

WHY LIVENESS IS A PID PROBE AND NOT `Popen.wait()`. There is no Popen to wait
on - `launch_lane` spawns THROUGH powershell and hands back a pid. And this
driver may be killed and relaunched while a worker is still up, at which point
it has no child handles at all, only a pid it can read off the lock. A pid probe
works in both worlds, and it is the same probe `lane_state` uses, so the driver
and any dashboard can never disagree about whether a worker is alive.

A KILL IS NOT DONE UNTIL IT IS VERIFIED. `taskkill` can fail - access denied, or
a re-parented subagent that outlives the wrapper whose pid was killed - and it
reports that only in output `_taskkill` deliberately swallows. An UNVERIFIED
kill is the same hazard as no kill: cycle N+1 fires a second worker into the
same lane worktree while the first is still writing, and two writers in one
working directory is not recoverable by retrying. So the kill is followed by a
bounded re-probe of the SAME liveness predicate, and a worker that outlives it
is recorded `timeout_kill_failed` and STOPS the loop.

TWO CLOCKS, ON PURPOSE. `clock` (time.time) stamps the ledger, because a row an
operator reads at 3am has to carry wall time. `monotonic` measures every
deadline, because wall time is NOT monotonic: an NTP step backwards silently
EXTENDS a deadline by however far the clock moved, and a frozen clock extends it
forever. The worker deadline also starts at LAUNCH rather than at cycle start,
because the acquire retries above can legitimately burn ten minutes that are not
the worker's to pay for.

A PID IS NOT AN IDENTITY. A pid probe answers whether SOMETHING holds the pid,
never whether it is still OUR worker - an OS reissues pids. So the driver
captures the process start time at launch and pairs it with the pid, reusing
`lanes`' own predicate rather than deriving a second one. It is fail-soft in
every direction: no start time, no psutil, an unqueryable pid all degrade to the
plain pid probe rather than declaring a live worker dead.

ONE FAULT IS NOT THE WHOLE NIGHT. `run_cycle` is wrapped: an unexpected fault
becomes an `error` record that is appended and emitted like any other. The
SILENT half of that defect was the worse half - without it, a fault leaves NO
ledger row and the morning's only evidence is a log that stopped. A fault that
REPEATS is different, and `max_consecutive_errors` stops the loop.

ONE DRIVER PER BOX. The lane lock stops two WORKERS, not two DRIVERS. A named
mutex held for the process lifetime is the guard.

STOP IS THREE FILES, CHECKED BEFORE EVERY CYCLE INCLUDING THE FIRST. A driver
that only checks between cycles fires one unwanted worker on every start, and
against this lane that is one work item executed and committed.

SIDE-EFFECT FREE AT IMPORT. Nothing below creates a directory, reads the control
plane or spawns anything at import time. `lanes` and `lane_launcher` are bound
LAZILY through the module `__getattr__` at the bottom, so importing this file to
read a constant does not require the rest of the lane to be present.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import NamedTuple

_HERE = Path(__file__).resolve().parent

# tools/ carries no __init__.py, so `toolpath` is imported under its BARE name:
# importing it as `tools.toolpath` makes mypy resolve one file under two module
# names and refuse the run outright. This is the same six lines
# scripts/make_cert.py, scripts/make_shortcut.py and scripts/verify_env.py each
# carry, and the same reason.
_TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

LANE = "queue"

REPORTS = _HERE / "reports"
CONTROL = _HERE / "control"

#: Relative so `--control-dir` can point the whole set at a sandbox.
STOP_RELPATHS = ("STOP", "lanes/QUEUE_STOP", "lanes/QUEUE_DRAINED")
STOP_FILES = tuple(CONTROL / rel for rel in STOP_RELPATHS)
#: The bare names, derived from one definition rather than written out twice -
#: `stop_reason` reports a NAME and `main` has to turn it back into a path.
STOP_NAMES = tuple(Path(rel).name for rel in STOP_RELPATHS)

#: Append-only, one JSON object per line. NOT tmp+os.replace: the atomic-write
#: rule (CLAUDE.md non-negotiable 5) exists for files another process POLLS
#: mid-write, and this is the opposite shape - a ledger nothing polls, where a
#: replace would rewrite every prior row on every cycle and lose any concurrent
#: append. An O_APPEND write of one short line is the durable form here.
CYCLE_LOG = REPORTS / "queue_loop.jsonl"

#: Twelve rows is roughly one unattended night. A bound rather than "until
#: stopped" means a driver nobody notices still ends.
DEFAULT_MAX_CYCLES = 12
#: A WEDGE ceiling, not a work budget. It must sit above the worst LEGITIMATE
#: cycle, and a legitimate cycle here is the worker's own work plus a full local
#: suite inside the frozen pre-push hook. Everything below this is bounded by
#: the prompt's own budgets rather than by this kill.
DEFAULT_CYCLE_TIMEOUT_S = 14400
#: Between cycles, never after the last. Long enough for the worker's push to
#: land and for the remote ref to settle before the next worker reads the tree.
DEFAULT_SETTLE_S = 45
#: A dead worker is noticed within this. Polling faster buys nothing against a
#: multi-hour run and only wakes the box.
DEFAULT_POLL_S = 10
#: TOTAL acquire attempts, not attempts-after-the-first.
ACQUIRE_RETRIES = 20
ACQUIRE_WAIT_S = 30
#: How long a killed worker gets to actually die before the kill is declared
#: FAILED. Sized for a wedged process tree with children to reap, not for a slow
#: shutdown - `/F` grants none. Short enough that a driver which cannot kill its
#: worker says so within a poll or two.
DEFAULT_KILL_GRACE_S = 15
#: Consecutive `error` outcomes before the loop gives up. One genuine fault plus
#: two chances for it to be transient; a fourth would be watching the same
#: traceback scroll past all night.
DEFAULT_MAX_CONSECUTIVE_ERRORS = 3


# ---------------------------------------------------------------------------
# CI acceptance. See "WHAT THAT MEANS AGAINST THIS REPO'S CI" above.
# ---------------------------------------------------------------------------


class CiSpec(NamedTuple):
    """One workflow, and how to decide whether it passed.

    Attributes:
        workflow: The workflow file name, as `gh` names it.
        dispatch: True when the workflow declares `workflow_dispatch` AND does
            not fire on a branch push, so this driver has to ask for the run.
            False for a workflow the push already triggered - dispatching one
            of those can only fail, and the failure would read as a tooling
            fault rather than as the mistake it is.
        required: Job-name matchers that must EACH match at least one job, every
            match of which must conclude `success`. A matcher matches a job when
            the name is equal to it or starts with it - the prefix form is what
            covers a matrix, where one declared job becomes one job per leg.
        advisory: Job-name matchers excluded from grading entirely, because the
            workflow itself declares them advisory.
    """

    workflow: str
    dispatch: bool
    required: tuple[str, ...]
    advisory: tuple[str, ...]


#: A BRANCH ref, which is what `gh workflow run` takes.
CI_REF = "main"

#: `.github/workflows/tier1.yml` - `jobs.fast.name` and `jobs.save.name`. It
#: fires on every branch push, so it is never dispatched from here.
CI_TIER1 = CiSpec(
    workflow="tier1.yml",
    dispatch=False,
    required=("gates, lint, types, tests", "tests (save shard)"),
    advisory=(),
)

#: `.github/workflows/tier2.yml`. Three of its four jobs are matrices over
#: {ubuntu-latest, windows-latest}, hence the trailing " (" on each matcher -
#: that is what makes the grader see two legs and demand both. The audit job
#: names itself advisory and its steps carry `continue-on-error`, so grading it
#: would end a night over a dependency advisory.
CI_TIER2 = CiSpec(
    workflow="tier2.yml",
    dispatch=True,
    required=("full suite (", "clean-checkout probe (", "shell suite ("),
    advisory=("dependency and license audit (advisory)",),
)

CI_SPECS = (CI_TIER1, CI_TIER2)

#: The words a verdict may be. Anything outside this set is a bug in this file
#: rather than a state of the world, which is why the tuple is asserted in
#: tests/test_queue_loop.py.
CI_SUCCESS = "success"
CI_FAILURE = "failure"
CI_CANCELLED = "cancelled"
CI_SKIPPED = "skipped"
CI_TIMEOUT = "timeout"
CI_UNAVAILABLE = "unavailable"
CI_UNKNOWN = "unknown"
CI_VERDICTS = (
    CI_SUCCESS,
    CI_FAILURE,
    CI_CANCELLED,
    CI_SKIPPED,
    CI_TIMEOUT,
    CI_UNAVAILABLE,
    CI_UNKNOWN,
)

#: Worst-first. The roll-up across workflows returns the WORST verdict seen, so
#: one green workflow can never carry a second one that answered nothing.
_VERDICT_RANK = (
    CI_FAILURE,
    CI_TIMEOUT,
    CI_CANCELLED,
    CI_UNKNOWN,
    CI_UNAVAILABLE,
    CI_SKIPPED,
    CI_SUCCESS,
)

#: A GitHub job conclusion that means the job did not pass. `timed_out`,
#: `action_required` and `startup_failure` are separate words for the same
#: answer, and lumping them into `unknown` would let a job that never ran read
#: as an unclassified curiosity instead of a break.
_JOB_BAD = ("failure", "timed_out", "action_required", "startup_failure")

#: 90 minutes per workflow. tier2's own jobs carry a 30-minute `timeout-minutes`
#: each and run in parallel, so this bounds queueing on shared runners rather
#: than the work.
DEFAULT_CI_WAIT_S = 5400
#: A run is measured in tens of minutes. Polling faster than a minute buys
#: nothing and spends API quota `gh` shares with everything else on the box.
DEFAULT_CI_POLL_S = 60
#: Per `gh` / `git` invocation. These are single API round trips, never the run
#: itself - the run is waited out by polling, never by holding a subprocess.
GH_TIMEOUT_S = 120
#: One cycle's push plus the dispatch it triggers is two runs; this covers a
#: night of them plus whatever else was pushed in between.
CI_RUN_LIST_LIMIT = 20
#: A dispatched run takes a beat to become visible to `gh run list`.
CI_TRIGGER_TRIES = 6
CI_TRIGGER_WAIT_S = 10


def _console_interpreter() -> str:
    """`python.exe` in preference to the `pythonw.exe` this may be running as.

    The detached launcher starts this driver under `pythonw` so no console
    window flashes on the operator's desktop for a run measured in hours. That
    makes `sys.executable` pythonw, and handing pytest an interpreter with no
    console attached is a difference nobody wants to discover from a truncated
    log at 3am - the whole point of the suite verdict is that it reproduces what
    a person would get by typing the command themselves.

    Falls back to `sys.executable` when no sibling exists, which is every
    non-Windows layout and any embedded build.
    """
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        sibling = exe.with_name("python.exe")
        if sibling.is_file():
            return str(sibling)
    return str(exe)


#: The local full suite, for a box with no `gh` credentials and for proving a
#: cycle end to end without a CI round trip. `tests` is named explicitly rather
#: than left to a bare recursive run - CONVENTIONS.md section 7.1.
LOCAL_SUITE_ARGV = (_console_interpreter(), "-m", "pytest", "tests", "-q")
#: A full local suite has been measured in the tens of minutes here. This bounds
#: a wedge, not the work.
DEFAULT_SUITE_TIMEOUT_S = 5400

_NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW

#: Two names, never one. The driver mutex is held for the WHOLE run, so an
#: append taken under that same name would block every other appender for the
#: length of the night - correct-looking and useless.
DRIVER_MUTEX = "Global\\CS_QUEUE_LOOP_DRIVER"
LEDGER_MUTEX = "Global\\CS_QUEUE_LOOP_LEDGER"
#: The ledger append is a few hundred bytes; this is a wedged holder, not a busy
#: one. On timeout the append proceeds UNSERIALIZED and says so.
LEDGER_MUTEX_TIMEOUT_S = 5.0

OUTCOME_COMPLETED = "completed"
OUTCOME_TIMEOUT = "timeout_killed"
OUTCOME_LANE_HELD = "lane_held"
OUTCOME_LAUNCH_FAILED = "launch_failed"
#: The kill was issued and the worker OUTLIVED it. Distinct from
#: OUTCOME_TIMEOUT because the two demand opposite responses: a killed worker
#: frees the worktree and the loop goes on, a surviving one does not.
OUTCOME_KILL_FAILED = "timeout_kill_failed"
#: A fault `run_cycle` did not convert into an outcome of its own.
OUTCOME_ERROR = "error"

STOPPED_BY_MAX_CYCLES = "max_cycles"
STOPPED_BY_CONSECUTIVE_ERRORS = "consecutive_errors"
STOPPED_BY_CI_RED = "ci_red"
STOPPED_BY_SUITE_RED = "suite_red"

#: Process exit codes, distinct on purpose: a launcher and any future scheduled
#: task can only tell "ran the night" from "refused to start" by the number.
EXIT_OK = 0
EXIT_STOP_SENTINEL = 2  # zero cycles because a stop file was already there
EXIT_ALREADY_RUNNING = 3  # another driver holds DRIVER_MUTEX
EXIT_KILL_FAILED = 4  # a worker outlived its taskkill - worktree suspect
EXIT_CONSECUTIVE_ERRORS = 5  # the same fault repeated until the loop gave up
EXIT_CI_RED = 6  # a gating CI job went red on a pushed sha
EXIT_SUITE_RED = 7  # the driver's own local suite went red


# ---------------------------------------------------------------------------
# Lazy module binds. See the docstring's last paragraph.
# ---------------------------------------------------------------------------


def _bind(dotted: str, private: str, filename: str):
    """Bind the SAME module object everything else uses - never a second copy.

    `lanes.py` carries process-global state: the ownership map that decides
    whether a release is ours. A file-path bind under a fresh name creates a
    SECOND module object with its OWN copy of that map, so a claim recorded in
    one is invisible to a release called on the other and the lane can never be
    freed. The dotted name is tried first because that is the canonical one; the
    file-path fallback exists only for callers with no package on `sys.path`
    (the detached launcher runs this by absolute path), and it reuses the same
    private name so the fallback still yields one object.
    """
    try:
        return importlib.import_module(dotted)
    except ImportError:
        pass
    if private in sys.modules:
        return sys.modules[private]
    spec = importlib.util.spec_from_file_location(private, _HERE / filename)
    if spec is None or spec.loader is None:  # pragma: no cover - unreachable
        raise ModuleNotFoundError(f"cannot load {filename} by path")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[private] = mod
    spec.loader.exec_module(mod)
    return mod


_LAZY = {
    "lanes": ("ops.loop.lanes", "cs_loop_lanes", "lanes.py"),
    "lane_launcher": ("ops.loop.lane_launcher", "cs_loop_lane_launcher", "lane_launcher.py"),
    "winmutex": ("ops.loop.winmutex", "cs_loop_winmutex", "winmutex.py"),
}


def __getattr__(name: str):
    """Resolve `lanes`, `lane_launcher` and `winmutex` on first use (PEP 562).

    Binding them at import would make reading a constant out of this file
    require the whole lane to be on disk, and would make an import of the
    driver a side effect of importing anything that mentions it. Resolving here
    keeps the module importable on its own while still handing every caller ONE
    module object.

    This is NOT a mutable seam. A caller substituting a dependency does it by
    passing a keyword argument to `run_cycle` or `run_loop`, which is a
    deliberate act; nothing monkeypatches an attribute out from under a running
    driver.
    """
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = _bind(*spec)
    globals()[name] = mod
    return mod


# ---------------------------------------------------------------------------
# Small helpers.
# ---------------------------------------------------------------------------


def _mod(name: str):
    """The bound module for `name`, from this module's own namespace first.

    `__getattr__` (PEP 562) is consulted by the interpreter ONLY for an
    attribute that is missing, so calling it directly - which the code below
    used to do - bypasses the very namespace it populates. That made the bind
    unoverridable: assigning `queue_loop.lane_launcher` had no effect on a call
    site that reached past it. Going through the namespace first restores the
    ordinary meaning of a module attribute, and costs one dict lookup.
    """
    found = globals().get(name)
    return __getattr__(name) if found is None else found


def _taskkill(pid) -> None:
    """Hard-kill a wedged worker AND its children. Never raises.

    `/T` is not decoration: the pid is the powershell WRAPPER and `claude` is
    its child, so killing only the wrapper would orphan a live worker inside the
    lane worktree while the very next cycle fires a second worker into the SAME
    directory.

    Failure is swallowed on purpose - the caller is already recording a timeout,
    and a kill that could throw would turn one bad cycle into a dead driver. The
    caller re-probes liveness afterwards, which is the only thing that can
    actually prove the kill took.

    (The PowerShell process-stopping cmdlet is banned by CLAUDE.md because it
    hangs the MCP pipe. It is not named here even to forbid it: the house-rules
    guard in tests/test_queue_loop.py scans this file's code lines for it and
    cannot tell advice from a call site.)
    """
    # RESOLVED FROM PATH, NEVER NAMED (CS-910). This spawns while the lane
    # worktree is the working directory of the very worker being killed, so a
    # bare name here is the measured local-code-execution vector at its most
    # reachable. An unresolvable taskkill leaves the worker alive, `_await_death`
    # reports the kill did not take, and the loop STOPS - which is the answer
    # that matters, because the alternative is firing a second worker into a
    # worktree that still has a live writer.
    killer = resolve_tool("taskkill")
    if killer is None:
        _emit(
            "queue-loop: taskkill could not be resolved on PATH - the worker "
            "was NOT killed and this cycle will be recorded as a failed kill"
        )
        return
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run(
            [killer, "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            timeout=20,
            check=False,
            creationflags=_NO_WINDOW,
        )


def _fault(exc: BaseException) -> str:
    """Name a fault WITHOUT rendering the exception object. Never its ``str()``.

    CLAUDE.md non-negotiable 12. ``str()`` on an OSError appends the path it
    failed on, and a path on this machine carries the Windows account name. Two
    of this module's five former call sites wrote that string into the JSONL
    LEDGER, which is durable and is exactly the file an operator quotes.

    ``strerror`` is the operating system's own message for the failure - "The
    system cannot find the file specified" - and carries no path. Anything with
    no ``strerror`` degrades to its type name, which is a real answer: it says
    what went wrong in kind without inventing detail.

    Nothing is lost for debugging. Every raise in this module chains its cause,
    so the full text still reaches a traceback; it is only kept out of the
    strings that get written down.

    A PER-TYPE ALLOWLIST, modelled on `tools/precommit_gate.py::safe_exc_text`,
    which is this project's worked answer to the same question. It is not
    IMPORTED from there: that module is the tier-0 gate, and a lane driver that
    could fail to start because a gate module failed to import would be trading
    one silence for another. The shape is copied and cited instead.

    NOT one strerror-shaped branch for everything. `strerror` is an OSError
    attribute, so a helper that reaches for it on any other type finds nothing -
    and if it then fell back to `str()` it would be the leak it was written to
    prevent. Several types that reach here have no strerror at all, and each
    leaks differently: `TimeoutExpired` renders the whole command line, and
    `CalledProcessError` renders an argv this driver builds from paths.

    A LAUNCH FAILURE CONTRIBUTES ITS TYPE NAME AND NOTHING MORE, even though
    the launcher already sanitises its own message. The guard's exemption is
    structural - a module may render whole an exception type IT defines,
    because it builds that message - and `LaneLaunchError` is defined one module
    over. Trusting a promise made in another file is exactly what the structural
    rule refuses, and it is right to: the trade costs message detail and buys a
    guarantee. The row still names the OUTCOME and the lane, which is what an
    operator needs to reproduce it.
    """
    if isinstance(exc, OSError):
        return exc.strerror or type(exc).__name__
    if isinstance(exc, subprocess.TimeoutExpired):
        return f"{type(exc).__name__} after {exc.timeout} seconds"
    if isinstance(exc, subprocess.CalledProcessError):
        return f"{type(exc).__name__} exit {exc.returncode}"
    return type(exc).__name__


def _emit(line: str) -> None:
    """One progress line, FLUSHED.

    The launcher runs this under `pythonw.exe` with stdout redirected to a file,
    and a redirected non-tty stdout is block-buffered - without the flush the
    log stays empty for the whole run and an operator tailing it cannot tell a
    working driver from a hung one.
    """
    print(line, flush=True)


def _driver_singleton():
    """Hold DRIVER_MUTEX for the whole run, or raise MutexTimeout immediately.

    `timeout=0` makes this a TEST rather than a wait. A second driver must exit
    at once with a distinct code; queueing it behind the first for six hours
    would start a run nobody asked for, at a time nobody chose.
    """
    return _mod("winmutex").hold(DRIVER_MUTEX, timeout=0.0, log=_emit)


def _ledger_lock():
    """Hold LEDGER_MUTEX for one append.

    No `log=` here, unlike the driver mutex: two extra lines per cycle would
    bury the one line per cycle an operator actually reads.
    """
    return _mod("winmutex").hold(LEDGER_MUTEX, timeout=LEDGER_MUTEX_TIMEOUT_S)


# ---------------------------------------------------------------------------
# FIX 2 - a verdict is a summary line AND an exit code.
# ---------------------------------------------------------------------------

#: pytest's own terminal summary, in every shape it actually emits: bare under
#: `-q`, `=`-padded otherwise, with or without the parenthesised duration.
#: Anchored on the trailing ` in <float>s` because that is the one part every
#: shape shares, and required to carry at least one outcome word so an ordinary
#: line of prose containing "in 1.0s" cannot pass for a verdict.
_OUTCOME_WORDS = (
    "passed",
    "failed",
    "error",
    "errors",
    "skipped",
    "xfailed",
    "xpassed",
    "deselected",
    "warning",
    "warnings",
    "no tests ran",
)
_SUMMARY_RE = re.compile(r"\bin\s+\d+(?:\.\d+)?s\b")


def summarize_pytest(stdout: str, exit_code: int) -> dict:
    """Grade a pytest run from its output AND its exit code, never one alone.

    THE DEFECT THIS CLOSES. A crashed parallel run leaves no summary line at
    all: the workers die, the log stops mid-progress, and nothing in it says
    FAILED - so `grep -c FAILED` returns 0, which is indistinguishable from a
    green run. A grader that reads only the log accepts it. A grader that reads
    only the exit code accepts a run that never started.

    Args:
        stdout: The run's captured output. May be truncated; that is the point.
        exit_code: The process's real exit status.

    Returns:
        A dict carrying `summary` (the VERBATIM last summary line, or None),
        `exit_code`, `truncated` (no summary line was found) and `ok`, which is
        True only when a line WAS parsed and the exit code is 0.
    """
    summary = None
    for line in str(stdout or "").splitlines():
        stripped = line.strip()
        if not _SUMMARY_RE.search(stripped):
            continue
        lowered = stripped.lower()
        if not any(word in lowered for word in _OUTCOME_WORDS):
            continue
        summary = stripped
    try:
        code = int(exit_code)
    except (TypeError, ValueError):
        code = -1
    return {
        "summary": summary,
        "exit_code": code,
        "truncated": summary is None,
        "ok": summary is not None and code == 0,
    }


def _default_suite_runner(argv, cwd=None):
    """Run the suite in a subprocess and return (exit_code, combined output).

    Split out as the injection seam so no test ever runs a real suite inside a
    suite. Output is merged because a crash writes to stderr and the summary
    line to stdout, and a truncation check needs both in one stream.
    """
    proc = subprocess.run(
        list(argv),
        capture_output=True,
        text=True,
        cwd=None if cwd is None else str(cwd),
        timeout=DEFAULT_SUITE_TIMEOUT_S,
        check=False,
        creationflags=_NO_WINDOW,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def run_local_suite(*, argv=None, runner=None, cwd=None, monotonic=time.monotonic) -> dict:
    """Run the full local suite and grade it. NEVER raises.

    This is the driver-owned wait for a box with no `gh` credentials, and it is
    the shape used to prove one cycle end to end without a CI round trip.

    IT RUNS IN THE LANE WORKTREE, NOT IN THE DRIVER'S OWN TREE, and that is a
    correctness requirement rather than a convenience. The worker commits and
    pushes from the lane worktree; the driver's tree has not pulled and is
    whatever it was when the night started. A suite run there would grade a tree
    NOBODY pushed and report it as the cycle's acceptance - a green that is
    about the wrong commit is worse than no green at all, because it is
    indistinguishable from a real one in the ledger.

    Args:
        argv: The command to run. Defaults to the whole suite under this
            interpreter, with `tests` named explicitly - never a bare recursive
            run from a repo root (CONVENTIONS.md section 7.1).
        runner: `(argv, cwd) -> (exit_code, output)`. The injection seam.
        cwd: WHICH TREE is graded. The caller passes the lane worktree.
        monotonic: Deadline clock. Never wall time.

    Returns:
        The verdict from `summarize_pytest`, plus `argv`, `cwd`, `duration_s`
        and `detail`. A runner that explodes yields `ok=False` with the reason
        in `detail` - one cycle's verdict is lost, never the night.
    """
    argv = list(LOCAL_SUITE_ARGV if argv is None else argv)
    runner = _default_suite_runner if runner is None else runner
    started = monotonic()
    try:
        code, out = runner(argv, cwd)
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "summary": None,
            "exit_code": None,
            "truncated": True,
            "ok": False,
            "argv": argv,
            "cwd": str(cwd or ""),
            "duration_s": round(monotonic() - started, 1),
            "detail": _fault(exc)[:400],
        }
    verdict = summarize_pytest(out, code)
    verdict.update(
        {
            "argv": argv,
            "cwd": str(cwd or ""),
            "duration_s": round(monotonic() - started, 1),
            "detail": ""
            if verdict["ok"]
            else (
                "no summary line - the run was truncated or crashed"
                if verdict["truncated"]
                else f"exit {verdict['exit_code']}"
            ),
        }
    )
    return verdict


# ---------------------------------------------------------------------------
# Stop sentinels.
# ---------------------------------------------------------------------------


def stop_path_for(name, control_dir=None):
    """The full path of the sentinel called `name`, or None if it is not one.

    Derived from STOP_RELPATHS rather than by re-probing the disk, so `main`
    can still name the file that stopped a run in the race where someone
    removes it a moment later.
    """
    root = CONTROL if control_dir is None else Path(control_dir)
    for rel in STOP_RELPATHS:
        if Path(rel).name == name:
            return root / rel
    return None


def stop_reason(control_dir=None) -> str | None:
    """The NAME of whichever stop sentinel exists, or None.

    Checked in STOP_RELPATHS order, so the global halt is reported ahead of the
    lane-local one when both are present.
    """
    root = CONTROL if control_dir is None else Path(control_dir)
    for rel in STOP_RELPATHS:
        if (root / rel).exists():
            return Path(rel).name
    return None


# ---------------------------------------------------------------------------
# The ledger.
# ---------------------------------------------------------------------------


def _append_line(path: Path, line: str) -> None:
    r"""The raw O_APPEND write.

    `newline="\n"` so the ledger stays LF on Windows. Text mode would otherwise
    translate to CRLF, which silently changes byte counts and makes this file
    disagree with every other JSONL in the tree.
    """
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)


def append_record(record: dict, cycle_log=None, *, hold=None, emit=None) -> Path:
    """Append one cycle record to the JSONL ledger. Creates its dir on demand.

    Lazily, because `--reports-dir` may name a directory that does not exist yet
    and because import time must stay side-effect free.

    An O_APPEND write of one short line is close to atomic already, but "close
    to" is what interleaves two half-lines into an unparseable row at 3am, and
    the ledger is the only durable record of the night.

    Args:
        record: The row. Serialised with sorted keys so two rows diff cleanly.
        cycle_log: Where to write. Defaults to CYCLE_LOG.
        hold: Zero-argument callable returning the serialising context manager.
            The seam exists so a test can prove the write happens INSIDE the
            critical section without touching a real OS mutex.
        emit: Where the fail-open warning goes.

    Returns:
        The path written.
    """
    path = Path(CYCLE_LOG if cycle_log is None else cycle_log)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True) + "\n"
    hold = _ledger_lock if hold is None else hold
    emit = _emit if emit is None else emit
    try:
        with hold():
            _append_line(path, line)
    except _mod("winmutex").MutexTimeout:
        # FAIL OPEN, LOUDLY. A dropped row loses the only evidence of a cycle,
        # and this is called from `run_loop` OUTSIDE its try, so raising here
        # would end the night over a lock nobody else should be holding.
        emit(
            f"queue-loop: UNSERIALIZED ledger append - {LEDGER_MUTEX} not free "
            f"within {LEDGER_MUTEX_TIMEOUT_S}s; appending anyway"
        )
        _append_line(path, line)
    return path


# ---------------------------------------------------------------------------
# Talking to `gh`.
# ---------------------------------------------------------------------------


def _gh(args) -> tuple[int, str]:
    """The ONE `gh` call site. Returns (returncode, text) and never raises.

    Every CI question goes through here so the timeout, the console-window flag
    and the "a missing gh is an exit code, not a traceback" contract are set
    once. It is also the seam every test injects: a suite that could reach the
    real `gh` would fire a real CI run against the live repo from a unit test.

    On failure the text is stderr FIRST, because that is where `gh` puts the
    reason while stdout is usually empty; both are returned because which one
    carries the message varies by subcommand.
    """
    exe = resolve_tool("gh")
    if exe is None:
        # The same shape a missing `gh` already produced, and the same verdict:
        # `unavailable`, so a night with no CI evidence never reads as green.
        return 127, "gh could not be resolved from PATH"
    argv = [exe, *[str(a) for a in args]]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_S,
            check=False,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        # 127 is "command not found", the common case here (no gh on PATH under
        # a detached pythonw) and it reads correctly in a log.
        return 127, _fault(exc)
    if proc.returncode != 0:
        return proc.returncode, ((proc.stderr or "") + (proc.stdout or "")).strip()
    return 0, proc.stdout or ""


def remote_head_sha(ref: str = CI_REF) -> str | None:
    r"""The sha `origin/<ref>` points at right now, or None. Never raises.

    `git ls-remote`, not `git rev-parse`, for two independent reasons. The
    driver runs in the MAIN tree while the worker commits and pushes from
    `C:\cs-worktrees\cs-lane-queue`, so this tree's own HEAD is not what was
    pushed; and a local `origin/main` ref is only as fresh as the last fetch,
    which nothing in this loop performs. `ls-remote` asks the remote and mutates
    NOTHING - no fetch, no index, no reflog - which matters because the driver
    must never write into a tree a worker may be using.

    None on every failure. The caller turns that into an `unavailable` verdict
    rather than a skipped cycle: a night whose CI evidence is missing must not
    read like a night of greens.
    """
    exe = resolve_tool("git")
    if exe is None:
        return None
    try:
        proc = subprocess.run(
            [exe, "-C", str(_mod("lanes").REPO_ROOT), "ls-remote", "origin", "refs/heads/" + ref],
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_S,
            check=False,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    first = (proc.stdout or "").strip().split("\n", 1)[0]
    parts = first.split()
    return parts[0] if parts else None


def _gh_json(gh, args):
    """(parsed, None) or (None, why). Every shape surprise is a `why`.

    A missing field, a payload that is a list where an object was expected, a
    non-zero exit and unparseable output are all the SAME class - the CLI did
    not answer the question - and all of them must degrade to `unavailable`
    rather than raise, so they are normalised at the one place that talks to it.
    """
    rc, out = gh(args)
    rendered = " ".join(str(a) for a in args)
    if rc != 0:
        return None, f"gh {rendered} exited {rc}: {str(out).strip()[:300]}"
    try:
        return json.loads(out), None
    except (TypeError, ValueError) as exc:
        return None, f"gh {rendered} returned unparseable JSON: {_fault(exc)}"


def _run_list(gh, spec: CiSpec):
    """Recent runs of `spec.workflow`, newest first, as `gh` orders them."""
    data, err = _gh_json(
        gh,
        [
            "run",
            "list",
            "--workflow",
            spec.workflow,
            "--limit",
            str(CI_RUN_LIST_LIMIT),
            "--json",
            "databaseId,headSha,status,conclusion,event",
        ],
    )
    if err:
        return [], err
    if not isinstance(data, list):
        return [], (f"gh run list returned {type(data).__name__}, expected a list of runs")
    return [row for row in data if isinstance(row, dict)], None


def _pick_run(rows, sha):
    """The best existing run for `sha`, preferring a dispatch over a push.

    `event_name` is part of a concurrency group, so a `workflow_dispatch` run
    sits in a DIFFERENT group from every push and a later push cannot cancel it.
    A push run has no such protection. Rows arrive newest-first, so the first
    match within an event is the freshest.
    """
    matches = [row for row in rows if str(row.get("headSha") or "") == str(sha)]
    for event in ("workflow_dispatch", "push"):
        for row in matches:
            if str(row.get("event") or "") == event:
                return row
    return matches[0] if matches else None


def _trigger_run(gh, spec: CiSpec, sha, seen, *, sleep):
    """Fire one dispatch and return the run it created. (row, None) or (None, why).

    NEW-ID identification, not a timestamp comparison. `seen` holds every run id
    already accounted for, so "the run the trigger created" is "the newest run
    whose id we have not seen" - which needs no clock, no timezone and no ISO
    parsing, and cannot mistake the first dispatch for the second when a
    cancelled run is re-dispatched.

    An exact `headSha` match wins when one is offered. Otherwise the newest
    fresh dispatch run is accepted even though its head is a DESCENDANT of the
    sha asked about: `gh workflow run` takes a branch ref, so it builds `main`
    as of trigger time and a later sha subsumes an earlier one. What is NOT done
    is claim descent that was not proven - the run's own headSha is returned and
    recorded, so the ledger cites the tree CI actually built.
    """
    rc, out = gh(["workflow", "run", spec.workflow, "--ref", CI_REF])
    if rc != 0:
        return None, (f"gh workflow run {spec.workflow} exited {rc}: {str(out).strip()[:300]}")
    why = (
        f"no new {spec.workflow} run appeared within "
        f"{CI_TRIGGER_TRIES * CI_TRIGGER_WAIT_S}s of the dispatch"
    )
    for _ in range(CI_TRIGGER_TRIES):
        sleep(CI_TRIGGER_WAIT_S)
        rows, err = _run_list(gh, spec)
        if err:
            why = err
            continue
        fresh = [row for row in rows if row.get("databaseId") not in seen]
        exact = [row for row in fresh if str(row.get("headSha") or "") == str(sha)]
        dispatched = [row for row in fresh if str(row.get("event") or "") == "workflow_dispatch"]
        picked = (exact or dispatched or [None])[0]
        if picked is not None:
            seen.add(picked.get("databaseId"))
            return picked, None
    return None, why


def _matches(name: str, matchers) -> bool:
    """A matcher matches a job name by equality or by prefix.

    The prefix form is what covers a matrix: `full suite (` is one declared job
    that becomes `full suite (ubuntu-latest)` and `full suite (windows-latest)`,
    and both must be graded.
    """
    return any(name == m or name.startswith(m) for m in matchers)


def grade_ci_jobs(spec: CiSpec, data) -> tuple[str, str]:  # noqa: PLR0911
    """Decide whether one workflow run passed, from its JOBS.

    NEVER the run conclusion. Two independent reasons: a run's conclusion can be
    green while the job that matters was skipped, and `gh run watch
    --exit-status` returns 0 on a CANCELLED run. The only thing that means "the
    tree passed" is every graded job's own conclusion.

    THE POOLED-GUARD RULE. Each required matcher must match at least one job,
    and EVERY job it matched must be `success`. A grader that asked "did any leg
    pass" would let the weakest member go unmeasured while its acceptance clause
    still read green.

    A required matcher that matches NOTHING is `unavailable` - an answer about
    the TOOL, not about the world. A workflow renamed out from under this driver
    must never read as a pass.

    Args:
        spec: Which workflow, and its required and advisory job matchers.
        data: The parsed `gh run view --json jobs` payload.

    Returns:
        (verdict, detail). The detail names the job that decided it.
    """
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        return CI_UNAVAILABLE, "the run carried no jobs list"
    seen = [
        (str(row.get("name") or ""), str(row.get("conclusion") or "").strip().lower())
        for row in jobs
        if isinstance(row, dict)
    ]
    if not seen:
        return CI_UNAVAILABLE, "the run carried an empty jobs list"

    # Required-and-missing FIRST: a workflow that does not carry the job this
    # driver grades has not answered the question, whatever else it did.
    for matcher in spec.required:
        if not [name for name, _ in seen if _matches(name, (matcher,))]:
            return CI_UNAVAILABLE, (
                f"{spec.workflow} carried no job matching {matcher!r} - the "
                f"workflow was renamed, or the run did not reach it"
            )

    graded = [(name, conclusion) for name, conclusion in seen if not _matches(name, spec.advisory)]
    for name, conclusion in graded:
        if conclusion in _JOB_BAD:
            return CI_FAILURE, f"{spec.workflow} job {name!r} -> {conclusion}"
    for name, conclusion in graded:
        if conclusion == CI_CANCELLED:
            return CI_CANCELLED, f"{spec.workflow} job {name!r} was cancelled"
    for name, conclusion in graded:
        if _matches(name, spec.required) and conclusion != CI_SUCCESS:
            verdict = conclusion if conclusion in CI_VERDICTS else CI_UNKNOWN
            return verdict, (
                f"{spec.workflow} required job {name!r} -> {conclusion or 'no conclusion'}"
            )
    off = [
        f"{name} -> {conclusion or 'none'}"
        for name, conclusion in graded
        if conclusion not in (CI_SUCCESS, CI_SKIPPED)
    ]
    if off:
        return CI_UNKNOWN, f"{spec.workflow} jobs in an ungraded state: {'; '.join(off)}"
    return CI_SUCCESS, (f"{spec.workflow}: {len(graded)} graded job(s), all success or skipped")


def wait_for_workflow(
    spec: CiSpec,
    sha,
    *,
    budget_s: float = DEFAULT_CI_WAIT_S,
    poll_s: float = DEFAULT_CI_POLL_S,
    allow_trigger: bool = True,
    gh=_gh,
    sleep=time.sleep,
    monotonic=time.monotonic,
) -> dict:
    """Block until one workflow's run for `sha` is graded, and return a verdict.

    THIS FUNCTION NEVER RAISES. Every tooling fault - a missing `gh`, a non-zero
    exit, unparseable JSON, a payload missing a field - becomes `unavailable`
    with the reason in `detail`, because a CLI hiccup may not wedge or end an
    overnight loop. Only the VERDICT is allowed to be bad news.

    `monotonic`, never wall time: this can block for an hour and a half.

    Args:
        spec: Which workflow and how to grade it.
        sha: The sha the worker pushed. The verdict carries the head CI
            ACTUALLY built, which may be a descendant of this one.
        budget_s: How long to wait for the run to reach `completed`.
        poll_s: Seconds between reads.
        allow_trigger: False suppresses the dispatch, for a caller that only
            wants to grade what already exists.
        gh: `(args) -> (returncode, text)`. The one place this file shells out.
        sleep: Blocking seam. Tests pass a fake that advances a clock instead.
        monotonic: Deadline clock. Never wall time - see the module docstring.

    Returns:
        `{"workflow", "sha", "run_id", "status", "verdict", "jobs", "waited_s",
        "detail"}` where `verdict` is one of CI_VERDICTS.
    """
    started_m = monotonic()
    deadline = started_m + max(0.0, float(budget_s))

    def _out(verdict, *, run_id=None, status="unknown", detail="", head=None, jobs=None) -> dict:
        return {
            "workflow": spec.workflow,
            "sha": str(head or sha),
            "run_id": run_id,
            "status": status,
            "verdict": verdict,
            "jobs": jobs or {},
            "waited_s": round(monotonic() - started_m, 1),
            "detail": str(detail)[:400],
        }

    rows, err = _run_list(gh, spec)
    if err:
        return _out(CI_UNAVAILABLE, detail=err)
    # Everything visible BEFORE any trigger of ours. Anything outside this set
    # later is, by construction, a run we caused.
    seen_ids = {row.get("databaseId") for row in rows}

    run = _pick_run(rows, sha)
    if run is None:
        if not (spec.dispatch and allow_trigger):
            # Deliberately NOT a dispatch. tier1 has no `workflow_dispatch`
            # trigger, so asking for one can only fail - and the failure would
            # read as a tooling fault rather than as the mistake it is.
            return _out(
                CI_UNAVAILABLE,
                detail=(
                    f"no {spec.workflow} run found for {sha}"
                    + (
                        ""
                        if spec.dispatch
                        else " and it cannot be dispatched - it has no workflow_dispatch trigger"
                    )
                ),
            )
        run, err = _trigger_run(gh, spec, sha, seen_ids, sleep=sleep)
        if err:
            return _out(CI_UNAVAILABLE, detail=err)

    def _watch(row) -> dict:  # noqa: PLR0911
        run_id = row.get("databaseId")
        head = str(row.get("headSha") or "") or None
        if run_id is None:
            return _out(CI_UNAVAILABLE, head=head, detail="the run row carried no databaseId")
        status = str(row.get("status") or "")
        conclusion = str(row.get("conclusion") or "")
        while status != "completed":
            # Checked BEFORE the sleep so a zero budget answers immediately and
            # the last poll cannot overshoot the deadline by a whole poll_s.
            if monotonic() >= deadline:
                return _out(
                    CI_TIMEOUT,
                    run_id=run_id,
                    head=head,
                    status=status or "unknown",
                    detail=(f"run {run_id} was still {status or 'pending'} after {budget_s}s"),
                )
            sleep(poll_s)
            view, verr = _gh_json(gh, ["run", "view", str(run_id), "--json", "status,conclusion"])
            if verr:
                return _out(
                    CI_UNAVAILABLE,
                    run_id=run_id,
                    head=head,
                    status=status or "unknown",
                    detail=verr,
                )
            if not isinstance(view, dict):
                return _out(
                    CI_UNAVAILABLE,
                    run_id=run_id,
                    head=head,
                    status=status or "unknown",
                    detail=f"run {run_id} status payload was not an object",
                )
            status = str(view.get("status") or "")
            conclusion = str(view.get("conclusion") or "")
        if conclusion == CI_CANCELLED:
            # Read here rather than from the jobs, because a cancelled run's
            # jobs carry no useful conclusion - and the caller has a specific
            # remedy for this one word that it has for no other.
            return _out(
                CI_CANCELLED,
                run_id=run_id,
                head=head,
                status=status,
                detail=(
                    f"run {run_id} completed 'cancelled' - superseded, or a job hit its own ceiling"
                ),
            )
        data, jerr = _gh_json(gh, ["run", "view", str(run_id), "--json", "jobs"])
        if jerr:
            return _out(CI_UNAVAILABLE, run_id=run_id, head=head, status=status, detail=jerr)
        verdict, detail = grade_ci_jobs(spec, data)
        jobs = {}
        if isinstance(data, dict) and isinstance(data.get("jobs"), list):
            jobs = {
                str(row.get("name") or ""): str(row.get("conclusion") or "")
                for row in data["jobs"]
                if isinstance(row, dict)
            }
        return _out(verdict, run_id=run_id, head=head, status=status, detail=detail, jobs=jobs)

    out = _watch(run)
    if out["verdict"] != CI_CANCELLED or not (spec.dispatch and allow_trigger):
        return out
    # ONCE. Being superseded is the exact failure this wait exists to survive,
    # so one fresh run is worth starting - but a driver that re-dispatched on
    # every cancel would spend the whole budget starting runs instead of
    # watching one, and would keep the runner busy for a night.
    again, err = _trigger_run(gh, spec, sha, seen_ids, sleep=sleep)
    if err:
        return dict(out, detail=f"{out['detail']}; re-dispatch failed: {err}"[:400])
    return _watch(again)


def wait_for_ci(
    sha,
    *,
    specs=CI_SPECS,
    budget_s: float = DEFAULT_CI_WAIT_S,
    poll_s: float = DEFAULT_CI_POLL_S,
    gh=_gh,
    sleep=time.sleep,
    monotonic=time.monotonic,
    wait_one=None,
) -> dict:
    """Wait out every gating workflow for `sha` and roll their verdicts up.

    The roll-up returns the WORST verdict seen, ranked failure-first, so one
    green workflow can never carry a second one that answered nothing. Only
    `failure` is a hard stop for the caller; everything else is recorded and
    passed over, because none of the other words is evidence that `main` broke.

    Args:
        sha: The pushed sha.
        specs: Which workflows gate. Defaults to both tiers.
        budget_s: Per-workflow wait budget, not a total across them.
        poll_s: Seconds between reads of a run's status.
        gh: `(args) -> (returncode, text)`, forwarded to each waiter.
        sleep: Blocking seam, forwarded.
        monotonic: Deadline clock, forwarded. Never wall time.
        wait_one: The per-workflow waiter. The injection seam.

    Returns:
        `{"sha", "verdict", "waited_s", "workflows": [<per-workflow verdict>]}`.
    """
    wait_one = wait_for_workflow if wait_one is None else wait_one
    started = monotonic()
    results = [
        wait_one(
            spec, sha, budget_s=budget_s, poll_s=poll_s, gh=gh, sleep=sleep, monotonic=monotonic
        )
        for spec in specs
    ]
    verdicts = {str(row.get("verdict")) for row in results}
    rolled = CI_SUCCESS
    for word in _VERDICT_RANK:
        if word in verdicts:
            rolled = word
            break
    return {
        "sha": str(sha),
        "verdict": rolled,
        "waited_s": round(monotonic() - started, 1),
        "workflows": results,
    }


# ---------------------------------------------------------------------------
# One cycle.
# ---------------------------------------------------------------------------
#
# THE SEAMS ARE THE POINT, and they are why `run_cycle` and `run_loop` carry a
# PLR0913 / PLR0912 / PLR0915 exemption each rather than being split.
#
# Every external dependency of this driver is a keyword argument with a real
# default: the lock, the launcher, the liveness probe, the killer, both clocks,
# the sleeper, the CI waiter, the suite runner, the ledger lock and the emitter.
# That is what lets the whole file be graded without spawning a process,
# sleeping, shelling out to git or gh, or taking an OS mutex - which is a stated
# acceptance clause of this item and not a preference.
#
# SPLITTING THESE WOULD NOT REMOVE THE ARGUMENTS, IT WOULD MOVE THEM. A helper
# taking half the seams still takes half the seams, and the caller then has to
# thread them through - so the count is unchanged and one more layer sits
# between a test and the behaviour it grades. The branch and statement counts
# are the same story: each branch is a distinct RECORDED outcome (lane_held,
# launch_failed, timeout_killed, timeout_kill_failed, error, ci_red, suite_red),
# and collapsing two of them into one word is how a night that ended at cycle 2
# comes to look like a night that ran all twelve.
#
# The exemption is per-site and names its rules, never a directory-wide ignore:
# a NEW function in this package still has to justify itself.


def _is_launch_error(exc: BaseException) -> bool:
    """True when `exc` is the launcher's own "this lane cannot start" signal.

    Resolved here rather than named in an `except` clause, so that a caller who
    injected a `launch` seam does not have to have `lane_launcher.py` on disk
    just to be caught correctly. An `except lane_launcher.LaneLaunchError`
    binds the module at the moment the exception is raised, which turns an
    injected dependency back into a required one.

    The identity check is the CLASS, never the name: a bare name comparison
    would swallow any unrelated exception that happened to be called the same
    thing, and swallowing an unexpected fault as a launch failure would report
    a bad night as an ordinary one. A missing module answers False, so the
    fault propagates and is recorded as an `error` rather than mislabelled.
    """
    try:
        return isinstance(exc, _mod("lane_launcher").LaneLaunchError)
    except (OSError, AttributeError, ImportError, ModuleNotFoundError):
        return False


def _worker_is_up(pid, started, *, alive, stranger) -> bool:
    """True only while the ORIGINAL worker process is still running.

    Two probes, not one. `alive` answers whether SOMETHING holds the pid;
    `stranger` answers whether that something is still the process we launched.
    Reusing `lanes`' pair rather than deriving a second one is what keeps the
    driver and any dashboard from ever disagreeing about a lane.

    TOTAL by construction: every uncertain case answers "not a stranger", so an
    unavailable source degrades to the plain pid probe instead of declaring a
    live worker dead and firing a second one into its worktree.
    """
    if not alive(pid):
        return False
    return not stranger(pid, started)


def _await_death(pid, started, *, alive, stranger, kill_grace_s, poll_s, sleep, monotonic) -> bool:
    """Re-probe after a kill. True when the worker is gone inside the grace.

    This is the whole of the unverified-kill fix. `_taskkill` swallows its own
    failure on purpose, so the only evidence it took is the liveness probe
    coming back false. Bounded, because a driver that waits forever on a process
    it cannot kill is a wedged driver with extra steps.
    """
    grace = max(0.0, float(kill_grace_s))
    deadline = monotonic() + grace
    # Never slower than the normal poll and never longer than the whole grace: a
    # 10s step against a 2s grace would sleep straight past the answer and
    # report a failed kill that actually worked.
    step = max(0.0, min(float(poll_s), grace))
    while True:
        if not _worker_is_up(pid, started, alive=alive, stranger=stranger):
            return True
        if monotonic() >= deadline:
            return False
        sleep(step)


def run_cycle(  # noqa: PLR0913, PLR0912, PLR0915 - see THE SEAMS ARE THE POINT
    cycle: int,
    *,
    lane: str = LANE,
    worktree=None,
    run_id=None,
    repo_root=None,
    poll_s: float = DEFAULT_POLL_S,
    cycle_timeout_s: float = DEFAULT_CYCLE_TIMEOUT_S,
    kill_grace_s: float = DEFAULT_KILL_GRACE_S,
    acquire_retries: int = ACQUIRE_RETRIES,
    acquire_wait_s: float = ACQUIRE_WAIT_S,
    acquire=None,
    release=None,
    launch=None,
    alive=None,
    proc_started=None,
    stranger=None,
    kill=_taskkill,
    sleep=time.sleep,
    clock=time.time,
    monotonic=time.monotonic,
) -> dict:
    """Run exactly one lane cycle: claim, launch, wait for the worker, release.

    Returns a record. It does not raise for any outcome the driver is supposed
    to survive - `lane_held` and `launch_failed` are recorded and returned so
    the loop can go on. Only a genuinely unexpected fault propagates, and even
    then the lane is released first.

    Every dependency is a keyword seam. A `None` seam is resolved from `lanes`
    or `lane_launcher` at CALL time, which keeps this module importable without
    them while still making a substitution a deliberate act by the caller.
    """
    # Resolved INSIDE the guard rather than through a conditional expression, so
    # the module object is never typed as "maybe None" - a shape that reads as a
    # possible AttributeError on every line below it.
    if None in (acquire, release, alive, proc_started, stranger):
        lanes_mod = _mod("lanes")
        acquire = lanes_mod.try_acquire_lane if acquire is None else acquire
        release = lanes_mod.release_lane if release is None else release
        alive = lanes_mod.pid_alive if alive is None else alive
        proc_started = lanes_mod.proc_started if proc_started is None else proc_started
        stranger = lanes_mod.holder_is_a_stranger if stranger is None else stranger
    # The launcher module is resolved ONLY when it is actually needed - when no
    # launcher was injected, or when no worktree was named. A caller that
    # supplies both has substituted the whole dependency, and requiring the
    # module anyway would make the seam a fiction: the file would have to exist
    # for a call that never touches it.
    if launch is None or worktree is None:
        launcher = _mod("lane_launcher")
        if launch is None:
            real_launch = launcher.launch_lane

            def launch(lane_name, **kw):
                """Bind `repo_root` into the launcher's own `root` argument."""
                return real_launch(lane_name, root=repo_root, **kw)

        if worktree is None:
            worktree = launcher.worktree_path(lane)

    # Worktree-mandatory (enforced again in the lock and a third time in the
    # launcher). When it is not named it is resolved from the launcher above
    # rather than hardcoded here, so a lane relocation moves one definition.
    run_id = uuid.uuid4().hex[:8] if run_id is None else str(run_id)
    started_at = clock()

    def _record(outcome, ok, pid, ended_at, detail="") -> dict:
        return {
            "cycle": int(cycle),
            "run_id": run_id,
            "ok": bool(ok),
            "pid": pid,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_s": round(ended_at - started_at, 3),
            "outcome": outcome,
            "detail": detail,
        }

    # ---- claim, retrying while the lane is legitimately held elsewhere
    claim = None
    attempts = max(1, int(acquire_retries))
    for attempt in range(1, attempts + 1):
        claim = acquire(lane, run_id=run_id, worktree=str(worktree))
        if claim.get("ok"):
            break
        # A refusal writes nothing on disk, so retrying is free and safe. No
        # wait after the FINAL attempt - it would only delay the record.
        if attempt < attempts:
            sleep(acquire_wait_s)
    if not (claim and claim.get("ok")):
        holder = (claim or {}).get("holder")
        return _record(
            OUTCOME_LANE_HELD,
            False,
            None,
            clock(),
            f"lane held by {holder!r} (pid {(claim or {}).get('pid')}) after {attempts} attempts",
        )

    token = claim.get("token")
    outcome, detail, pid = OUTCOME_COMPLETED, "", None
    try:
        try:
            run = launch(lane, run_id=run_id, token=token)
        except Exception as exc:
            if not _is_launch_error(exc):
                raise
            # launch_lane has ALREADY released the lane on this path; the
            # finally below releases again, which is deliberate - release_lane
            # is idempotent, and an unconditional release is the only shape that
            # survives a future launcher that stops cleaning up after itself.
            outcome, detail = OUTCOME_LAUNCH_FAILED, _fault(exc)[:400]
        else:
            pid = run.get("pid")
            if not pid:
                outcome, detail = OUTCOME_LAUNCH_FAILED, "launch returned no pid"
            else:
                detail = str(run.get("log") or "")
                # Identity, captured ONCE and only here. A pid alone does not
                # name a process, so every later probe compares (pid, start
                # time) against THIS value. None is the fail-soft answer and
                # `stranger` reads it as "cannot prove reuse".
                worker_started = proc_started(pid)
                # The budget starts HERE, at launch, on the MONOTONIC clock -
                # the acquire retries above can burn ten legitimate minutes and
                # none of it is the worker's to pay for.
                launched_m = monotonic()
                while _worker_is_up(pid, worker_started, alive=alive, stranger=stranger):
                    waited = monotonic() - launched_m
                    if waited >= float(cycle_timeout_s):
                        # EXACTLY once - the break is load-bearing. A second
                        # kill could land on a pid the OS has already reissued
                        # to an unrelated process.
                        kill(pid)
                        ran_for = round(waited, 1)
                        if _await_death(
                            pid,
                            worker_started,
                            alive=alive,
                            stranger=stranger,
                            kill_grace_s=kill_grace_s,
                            poll_s=poll_s,
                            sleep=sleep,
                            monotonic=monotonic,
                        ):
                            outcome = OUTCOME_TIMEOUT
                            detail = (
                                f"worker ran {ran_for}s against a "
                                f"{cycle_timeout_s}s budget - killed"
                            )
                        else:
                            # Unrecoverable for the LOOP, not just this cycle.
                            outcome = OUTCOME_KILL_FAILED
                            detail = (
                                f"worker ran {ran_for}s against a "
                                f"{cycle_timeout_s}s budget - taskkill did "
                                f"NOT take within {kill_grace_s}s; pid "
                                f"{pid} may still be writing to {worktree}"
                            )
                        break
                    sleep(poll_s)
    finally:
        # Every path, including an exception nobody predicted. The release runs
        # BEFORE that exception escapes, because a driver that dies holding the
        # only lane slot wedges the lane until someone reclaims it by hand.
        release(token)

    return _record(outcome, outcome == OUTCOME_COMPLETED, pid, clock(), detail)


# ---------------------------------------------------------------------------
# The loop.
# ---------------------------------------------------------------------------


def run_loop(  # noqa: PLR0913, PLR0912, PLR0915 - see THE SEAMS ARE THE POINT
    *,
    max_cycles: int = DEFAULT_MAX_CYCLES,
    settle_s: float = DEFAULT_SETTLE_S,
    poll_s: float = DEFAULT_POLL_S,
    cycle_timeout_s: float = DEFAULT_CYCLE_TIMEOUT_S,
    kill_grace_s: float = DEFAULT_KILL_GRACE_S,
    max_consecutive_errors: int = DEFAULT_MAX_CONSECUTIVE_ERRORS,
    ci_gate: bool = True,
    ci_wait_s: float = DEFAULT_CI_WAIT_S,
    ci_poll_s: float = DEFAULT_CI_POLL_S,
    local_suite: bool = False,
    lane: str = LANE,
    worktree=None,
    repo_root=None,
    control_dir=None,
    cycle_log=None,
    acquire_retries: int = ACQUIRE_RETRIES,
    acquire_wait_s: float = ACQUIRE_WAIT_S,
    acquire=None,
    release=None,
    launch=None,
    alive=None,
    proc_started=None,
    stranger=None,
    kill=_taskkill,
    head_sha=None,
    gh=_gh,
    wait=None,
    suite=None,
    hold=None,
    sleep=time.sleep,
    clock=time.time,
    monotonic=time.monotonic,
    emit=_emit,
) -> dict:
    """Fire cycles until `max_cycles`, a stop sentinel, or a hard stop.

    THE WAITS LIVE HERE, BETWEEN CYCLES, AND NOWHERE ELSE. That placement is
    the mechanism: the only thing that can start cycle N+1 is this loop, and
    while it is inside a wait it is not starting anything. A wait delegated to
    the worker is a request; a wait taken here is a guarantee.

    The sentinel check is at the TOP of the iteration, which is what makes a
    QUEUE_DRAINED written by the worker mid-cycle stop the NEXT cycle rather
    than retroactively discard the one that wrote it. The hard stops are checked
    at the BOTTOM, after the offending record is appended and emitted - the
    evidence of why the night ended has to reach the ledger.

    THE CI GATE HANGS OFF `origin/main`, NOT OFF THE WORKER. The driver never
    looks inside the lane worktree and has no channel to the worker beyond a
    pid, so the only push signal available to it is the remote ref moving:
    `head_sha()` is read before and after each cycle, and an UNCHANGED answer
    means the worker shipped nothing and there is no run to wait for. The
    verdict is attached to the SAME record, so one JSONL row carries a cycle and
    its acceptance and nobody has to join two files at 3am.

    An ABSENT `ci` key means no gate ran for that cycle - gate off, no push
    detected, or an outcome other than `completed`. It deliberately is NOT
    recorded as `verdict="skipped"`, because that word already means a JOB was
    skipped, and one word cannot carry two conditions.

    Returns:
        `{"cycles_run", "stopped_by", "records"}`.
    """
    head_sha = remote_head_sha if head_sha is None else head_sha
    wait = wait_for_ci if wait is None else wait
    suite = run_local_suite if suite is None else suite

    records: list = []
    stopped_by = None
    consecutive_errors = 0
    error_limit = max(1, int(max_consecutive_errors))
    total = max(0, int(max_cycles))
    for cycle in range(1, total + 1):
        reason = stop_reason(control_dir)
        if reason:
            stopped_by = reason
            emit(f"queue-loop stop: {reason} present - {len(records)} cycle(s) run")
            break
        # Minted HERE, not inside run_cycle, so the error record below can name
        # the SAME run as the claim and the worker log. A cycle that faulted
        # before returning would otherwise leave a row nothing can be joined to.
        run_id = uuid.uuid4().hex[:8]
        started_at = clock()
        # BEFORE the cycle, unconditionally when the gate is on: the outcome is
        # not knowable in advance, and one `ls-remote` against a multi-hour
        # cycle is not a cost worth optimising.
        pre_sha = head_sha() if ci_gate else None
        try:
            record = run_cycle(
                cycle,
                lane=lane,
                worktree=worktree,
                repo_root=repo_root,
                run_id=run_id,
                poll_s=poll_s,
                cycle_timeout_s=cycle_timeout_s,
                kill_grace_s=kill_grace_s,
                acquire_retries=acquire_retries,
                acquire_wait_s=acquire_wait_s,
                acquire=acquire,
                release=release,
                launch=launch,
                alive=alive,
                proc_started=proc_started,
                stranger=stranger,
                kill=kill,
                sleep=sleep,
                clock=clock,
                monotonic=monotonic,
            )
        except Exception as exc:  # DELIBERATE catch-all - see the comment below
            # A night that ends at cycle 3 on ONE unexpected fault is the defect
            # this closes, and the SILENT half was worse: `append_record` is only
            # reached on the normal path, so a fault used to leave no ledger row
            # at all. Nothing leaks by catching here - run_cycle releases the
            # lane in its own `finally` before any exception escapes it.
            ended_at = clock()
            record = {
                "cycle": int(cycle),
                "run_id": run_id,
                "ok": False,
                "pid": None,
                "started_at": started_at,
                "ended_at": ended_at,
                "duration_s": round(ended_at - started_at, 3),
                "outcome": OUTCOME_ERROR,
                "detail": _fault(exc)[:400],
            }

        # ---- THE DRIVER-OWNED WAITS, before the append so ONE row carries
        # ---- the cycle and its acceptance together.
        note = ""
        if record["outcome"] == OUTCOME_COMPLETED and local_suite:
            # THE LANE WORKTREE, never this tree - see run_local_suite. The
            # worker's commit lives there; the driver's own checkout is whatever
            # it was when the night started.
            graded_tree = worktree
            if graded_tree is None:
                graded_tree = _mod("lane_launcher").worktree_path(lane)
            record["suite"] = suite(cwd=graded_tree, monotonic=monotonic)
        if ci_gate and record["outcome"] == OUTCOME_COMPLETED:
            post_sha = head_sha()
            if pre_sha is None or post_sha is None:
                # A tooling failure, recorded as one. Staying silent here would
                # make a night with no CI evidence read like a night of greens.
                record["ci"] = {
                    "sha": post_sha or pre_sha,
                    "verdict": CI_UNAVAILABLE,
                    "waited_s": 0.0,
                    "workflows": [],
                    "detail": (
                        f"origin/{CI_REF} could not be resolved, so this "
                        f"cycle's push could not be identified"
                    ),
                }
            elif post_sha == pre_sha:
                note = " ci=no-push"
            else:
                record["ci"] = wait(
                    post_sha,
                    budget_s=ci_wait_s,
                    poll_s=ci_poll_s,
                    gh=gh,
                    sleep=sleep,
                    monotonic=monotonic,
                )
        verdict = record.get("ci")
        if verdict:
            note = f" ci={verdict['verdict']} {verdict.get('waited_s', 0)}s"
        local = record.get("suite")
        if local:
            note += f" suite={'ok' if local['ok'] else 'RED'} [{local['summary']}]"

        records.append(record)
        append_record(record, cycle_log, hold=hold, emit=emit)
        # ONE line per cycle, still. The verdicts ride on it rather than taking
        # lines of their own, because an operator tailing this reads a night by
        # counting cycles down the left margin.
        emit(
            f"queue-loop cycle {cycle}/{total} {record['outcome']} "
            f"run_id={record['run_id']} pid={record['pid']} "
            f"{record['duration_s']}s{note} {record['detail']}".rstrip()
        )

        if verdict and verdict["verdict"] == CI_FAILURE:
            # HARD STOP, and the only CI verdict that is one. Every further
            # cycle would push another row on top of a break nobody is
            # watching, and the rows would then have to be untangled from each
            # other before either could be judged.
            stopped_by = STOPPED_BY_CI_RED
            emit(
                f"queue-loop stop: ci is RED on {verdict['sha']} - refusing to "
                f"push another row onto a broken {CI_REF}"
            )
            break
        if local and not local["ok"]:
            stopped_by = STOPPED_BY_SUITE_RED
            emit(
                f"queue-loop stop: the local suite is RED - "
                f"[{local['summary']}] exit {local['exit_code']}"
            )
            break
        if record["outcome"] == OUTCOME_KILL_FAILED:
            # HARD STOP. The next cycle would fire a second worker into a
            # worktree whose previous writer is still alive, and two writers in
            # one working directory is not recoverable by retrying.
            stopped_by = OUTCOME_KILL_FAILED
            emit(
                f"queue-loop stop: pid {record['pid']} survived its kill - "
                f"refusing to launch into {lane} again this run"
            )
            break
        if record["outcome"] == OUTCOME_ERROR:
            consecutive_errors += 1
            if consecutive_errors >= error_limit:
                stopped_by = STOPPED_BY_CONSECUTIVE_ERRORS
                emit(
                    f"queue-loop stop: {consecutive_errors} consecutive error "
                    f"cycles - {record['detail']}"
                )
                break
        else:
            # CONSECUTIVE, not cumulative. One bad cycle between good ones is a
            # transient the loop is supposed to survive; resetting here is what
            # keeps a flaky night from being scored as a broken one.
            consecutive_errors = 0

        # Between cycles only. A settle after the final cycle would just delay
        # the driver's own exit for nothing.
        if cycle < total:
            sleep(settle_s)
    if stopped_by is None:
        stopped_by = STOPPED_BY_MAX_CYCLES
    return {"cycles_run": len(records), "stopped_by": stopped_by, "records": records}


# ---------------------------------------------------------------------------
# The CLI.
# ---------------------------------------------------------------------------

#: stopped_by -> exit code, for the reasons that are not EXIT_OK. Held as one
#: table rather than a ladder of ifs so a new stop reason cannot be added
#: without giving it a number, which is the defect that made a night ending at
#: cycle 2 indistinguishable from a night that ran all twelve.
_STOP_EXIT = {
    OUTCOME_KILL_FAILED: EXIT_KILL_FAILED,
    STOPPED_BY_CONSECUTIVE_ERRORS: EXIT_CONSECUTIVE_ERRORS,
    STOPPED_BY_CI_RED: EXIT_CI_RED,
    STOPPED_BY_SUITE_RED: EXIT_SUITE_RED,
}


def main(argv=None, *, singleton=None) -> int:
    """CLI entry point for the detached launcher.

    A drained queue IS a successful outcome - but it is not the same outcome as
    a night's work, and one number cannot mean both. The distinction is drawn on
    `cycles_run`, so a sentinel that appears MID-run (the worker's own
    QUEUE_DRAINED, the normal end of a good drain) still exits 0, while a
    sentinel that was ALREADY there when the driver started exits
    EXIT_STOP_SENTINEL so no launcher can print a success banner over a no-op.

    Args:
        argv: Command line, for testing.
        singleton: A zero-argument callable returning a context manager held for
            the whole run. The seam exists so tests never touch a real OS mutex.

    Returns:
        One of the EXIT_* codes.
    """
    parser = argparse.ArgumentParser(
        prog="queue_loop", description="Re-fire the one-row queue lane worker cycle after cycle."
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=DEFAULT_MAX_CYCLES,
        help=f"max cycles to run (default {DEFAULT_MAX_CYCLES})",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=DEFAULT_SETTLE_S,
        help=f"seconds between cycles (default {DEFAULT_SETTLE_S})",
    )
    parser.add_argument(
        "--poll",
        type=float,
        default=DEFAULT_POLL_S,
        help=f"worker liveness poll seconds (default {DEFAULT_POLL_S})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_CYCLE_TIMEOUT_S,
        help=f"hard cycle deadline (default {DEFAULT_CYCLE_TIMEOUT_S})",
    )
    parser.add_argument("--lane", default=LANE, help=f"lane to drive (default {LANE})")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "the tree the lane's PROMPT and git operations come from; "
            "defaults to the main checkout. Point it at a branch worktree to "
            "prove a cycle before the lane's own code has reached main - "
            "without it the launcher reads a prompt that is not there yet and "
            "the cycle records launch_failed"
        ),
    )
    parser.add_argument(
        "--control-dir",
        default=None,
        help="where the stop sentinels live (default ops/loop/control)",
    )
    parser.add_argument(
        "--reports-dir",
        default=None,
        help="where queue_loop.jsonl is written (default ops/loop/reports)",
    )
    parser.add_argument(
        "--ci-wait",
        type=float,
        default=DEFAULT_CI_WAIT_S,
        help=(f"seconds to block on each gating workflow (default {DEFAULT_CI_WAIT_S})"),
    )
    # A kill switch, not a mode. The gate is the point of this driver owning the
    # wait at all; turning it off is for a run whose CI is already known bad, or
    # for a box with no `gh` credentials.
    parser.add_argument(
        "--no-ci-gate", action="store_true", help="do not wait on CI after a cycle pushes"
    )
    parser.add_argument(
        "--local-suite",
        action="store_true",
        help=(
            "also run the full local suite between cycles and record its summary line and exit code"
        ),
    )
    parser.add_argument(
        "--once", action="store_true", help="run exactly one cycle - overrides --cycles"
    )
    args = parser.parse_args(argv)

    cycles = 1 if args.once else args.cycles
    cycle_log = None if args.reports_dir is None else Path(args.reports_dir) / CYCLE_LOG.name
    control_dir = None if args.control_dir is None else Path(args.control_dir)

    guard = _driver_singleton if singleton is None else singleton
    try:
        with guard():
            summary = run_loop(
                max_cycles=cycles,
                settle_s=args.settle,
                poll_s=args.poll,
                cycle_timeout_s=args.timeout,
                ci_gate=not args.no_ci_gate,
                ci_wait_s=args.ci_wait,
                local_suite=args.local_suite,
                lane=args.lane,
                control_dir=control_dir,
                repo_root=(None if args.repo_root is None else Path(args.repo_root)),
                cycle_log=cycle_log,
            )
    except _mod("winmutex").MutexTimeout:
        # Not an error condition, a REFUSAL - and it must be loud, because the
        # symptom of two drivers is invisible at a glance: both survive, both
        # look busy, and each spends up to ten minutes per cycle losing the
        # acquire race to the other while their rows interleave in one ledger.
        _emit(
            f"queue-loop refused: another driver already holds {DRIVER_MUTEX}. "
            f"Two drivers interleave on the lane lock and append to one "
            f"ledger. Stop that one first: taskkill /F /T /PID <pid>"
        )
        return EXIT_ALREADY_RUNNING

    _emit(f"queue-loop done: {summary['cycles_run']} cycle(s), stopped_by={summary['stopped_by']}")
    if summary["cycles_run"] == 0 and summary["stopped_by"] in STOP_NAMES:
        sentinel = stop_path_for(summary["stopped_by"], control_dir)
        _emit(
            f"queue-loop refused: {summary['stopped_by']} was ALREADY present "
            f"at {sentinel} - zero cycles ran. Delete that file to run."
        )
        return EXIT_STOP_SENTINEL
    # Checked AFTER the sentinel branch and independently of cycles_run: a hard
    # stop always ran at least one cycle, so the two cannot collide.
    stopped = summary["stopped_by"]
    if stopped == OUTCOME_KILL_FAILED:
        _emit(
            "queue-loop ALERT: a worker outlived its kill - treat the lane "
            "worktree as having a possible live writer and check it by hand "
            "before firing again."
        )
    if stopped == STOPPED_BY_CI_RED:
        _emit(
            "queue-loop ALERT: CI went RED on a pushed sha - the night stopped "
            "rather than stack more rows onto a broken tree. Read the last row "
            f"of {CYCLE_LOG.name} for the run id, fix the red, then fire again."
        )
    return _STOP_EXIT.get(stopped, EXIT_OK)


if __name__ == "__main__":
    raise SystemExit(main())
