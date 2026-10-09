"""CS-1233 - a test that measures wall time can wait until it is alone on the box.

THE DEFECT. tests/test_claude_hook.py holds the CS-815 wrapper's added latency
under a second, measured as the median of twenty wrapped-minus-direct pairs.
Under ``-n auto`` those pairs ran beside CPU-bound sibling workers. The wrapped
call starts about ten processes to the direct call's one, so contention
inflates it far more and pairing never cancels it. The windows guard shard of
tier2 read medians of 1.010s to 1.169s; the same arm run alone reads well under
the budget. The number graded was the sibling load, not the wrapper.

THE MECHANISM. Every xdist worker takes an exclusive lock on its own file under
a per-run directory at session start and releases it at session finish. A test
that measures wall time calls :func:`await_quiet_siblings`, which polls until no
other worker's file is locked. A LOCK, NOT A MARKER: the operating system frees
a lock when its process dies, so a crashed worker can never leave the measuring
test waiting on a file nobody will delete.

WHY IT CANNOT DEADLOCK. The waiting worker holds no lock another worker wants,
and xdist's scheduler hands the remaining queue to the other workers and shuts
each down once the queue is empty - independently of the waiting one. Every
worker is configured and locked before any test runs, because the scheduler
starts no test until every worker has reported its collection. A worker
unlocks its own byte while it waits, keeping its file, so two workers waiting
at once never count each other live and the run directory never empties under
a waiter. The wait is bounded and LOUD at the bound, naming the live sibling.

Outside xdist there are no workers, so nothing is waited for. Standard library
plus pytest only, like tests/conftest.py, which registers the two hooks below.
"""

from __future__ import annotations

import contextlib
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Final, NamedTuple

import pytest

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

#: The directory under the system temp root that holds one subdirectory per run.
LIVE_ROOT_NAME: Final = "clockspeed-xdist-live"

#: Seconds between two polls of the sibling locks.
POLL_SECONDS: Final = 0.25

#: The longest a worker waits for quiet siblings before it fails LOUD. It sits
#: under the tightest CI job cutoff that runs a waiting arm - tier 1's ten
#: minutes, with the job's setup steps ahead of pytest - so a hung sibling is
#: named by this module rather than lost in a cancellation that says nothing, and
#: above every sibling wait measured so far, which ended well inside it.
QUIET_BOUND_SECONDS: Final = 400.0

#: How long a worker retries taking its own lock back after a wait. A sibling's
#: probe holds it for the instant between its own lock and unlock calls.
RELOCK_SECONDS: Final = 5.0
RELOCK_POLL_SECONDS: Final = 0.01

LOCK_SUFFIX: Final = ".lock"

# A run id or worker id is used as a path component, so anything but these
# characters is dropped before it gets there.
UNSAFE_NAME: Final = re.compile(r"[^A-Za-z0-9_-]")


class HeldLock(NamedTuple):
    """One worker's liveness lock: the open descriptor and the file it locks."""

    fd: int
    path: Path


def _try_lock(fd: int) -> bool:
    """Take an exclusive, non-blocking lock on byte 0 of ``fd``; report success."""
    try:
        if sys.platform == "win32":
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(fd: int) -> None:
    """Release the lock :func:`_try_lock` took on ``fd``."""
    if sys.platform == "win32":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)


def live_directory(run_id: str) -> Path:
    """The directory every worker of one run locks its file in."""
    return Path(tempfile.gettempdir()) / LIVE_ROOT_NAME / (UNSAFE_NAME.sub("", run_id) or "run")


def hold_liveness_lock(directory: Path, worker: str) -> HeldLock:
    """Create and exclusively lock ``worker``'s file in ``directory``.

    Args:
        directory: The run's liveness directory.
        worker: The xdist worker id, such as ``gw0``.

    Returns:
        The held lock, to be passed to :func:`release_liveness_lock`.

    Raises:
        RuntimeError: When the file is already locked - two workers with one id.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ((UNSAFE_NAME.sub("", worker) or "worker") + LOCK_SUFFIX)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    if not _try_lock(fd):
        os.close(fd)
        raise RuntimeError("a worker liveness lock was already held under the same worker id")
    return HeldLock(fd, path)


def release_liveness_lock(held: HeldLock) -> None:
    """Release and remove one worker's file, and the run directory once it is empty."""
    with contextlib.suppress(OSError):
        _unlock(held.fd)
    os.close(held.fd)
    # A prober may have the file open this instant, which refuses an unlink on
    # Windows; the file is then left unlocked, and an unlocked file is not live.
    with contextlib.suppress(OSError):
        held.path.unlink()
    with contextlib.suppress(OSError):
        held.path.parent.rmdir()


def live_sibling_names(directory: Path, own: str) -> list[str]:
    """The ids of the workers other than ``own`` that still hold their lock in ``directory``.

    A file is probed by opening it WITHOUT creating it and trying the lock: a
    file that vanished, or whose lock can be taken, belongs to a worker that has
    finished, died, or is itself waiting.
    """
    if not directory.is_dir():
        return []
    own_name = (UNSAFE_NAME.sub("", own) or "worker") + LOCK_SUFFIX
    live: list[str] = []
    for path in sorted(directory.glob("*" + LOCK_SUFFIX)):
        if path.name == own_name:
            continue
        try:
            fd = os.open(path, os.O_RDWR)
        except OSError:
            continue
        try:
            if _try_lock(fd):
                _unlock(fd)
            else:
                live.append(path.name.removesuffix(LOCK_SUFFIX))
        finally:
            os.close(fd)
    return live


def live_sibling_count(directory: Path, own: str) -> int:
    """How many workers other than ``own`` still hold their lock in ``directory``."""
    return len(live_sibling_names(directory, own))


class QuietWaitTimeoutError(RuntimeError):
    """A sibling worker stayed live past QUIET_BOUND_SECONDS."""


def _relock(held: HeldLock) -> None:
    """Take a waiting worker's own lock back, retrying past a sibling's probe."""
    deadline = time.perf_counter() + RELOCK_SECONDS
    while not _try_lock(held.fd):
        if time.perf_counter() >= deadline:
            raise RuntimeError("a waiting worker could not take its own liveness lock back")
        time.sleep(RELOCK_POLL_SECONDS)


def _worker_identity(config: pytest.Config) -> tuple[Path, str] | None:
    """The run's liveness directory and this worker's id, or None outside xdist."""
    info = getattr(config, "workerinput", None)
    if not isinstance(info, dict):
        return None
    return live_directory(str(info.get("testrunuid", ""))), str(info.get("workerid", ""))


def live_siblings_now(config: pytest.Config) -> int:
    """How many other workers of this run are live now; zero outside xdist."""
    identity = _worker_identity(config)
    if identity is None:
        return 0
    return live_sibling_count(*identity)


def await_quiet_siblings(config: pytest.Config) -> float:
    """Block until no other worker of this run is live; return the seconds waited.

    BOUNDED, AND LOUD AT THE BOUND. A sibling still live after
    QUIET_BOUND_SECONDS raises QuietWaitTimeoutError naming its worker id, so a
    hung sibling is reported here and never passes in silence.

    A WAITING WORKER IS NOT LIVE. It UNLOCKS its byte for the length of the wait
    and locks it again after, keeping its file and descriptor throughout. Several
    arms wait, and a scheduler other than ``--dist loadfile`` can put two of them
    on two workers at once: a waiter that stayed live would count the other as
    busy, and each would wait for ever. The file stays, so the shared run
    directory is never empty while a waiter needs it, and a sibling's release
    can never remove it from under the relock.

    Raises:
        QuietWaitTimeoutError: When a sibling is still live at the bound.
    """
    identity = _worker_identity(config)
    if identity is None:
        return 0.0
    held = config.stash.get(_HELD, None)
    if held is not None:
        _unlock(held.fd)
    started = time.perf_counter()
    try:
        while live := live_sibling_names(*identity):
            waited = time.perf_counter() - started
            if waited >= QUIET_BOUND_SECONDS:
                raise QuietWaitTimeoutError(
                    f"CS-1233: sibling worker(s) {live} still live after {waited:.0f}s - "
                    "the arm that needs a quiet box did not run"
                )
            time.sleep(POLL_SECONDS)
    finally:
        if held is not None:
            _relock(held)
    return time.perf_counter() - started


_HELD: Final = pytest.StashKey[HeldLock]()


def pytest_sessionstart(session: pytest.Session) -> None:
    """In an xdist worker, take this worker's liveness lock before collection."""
    identity = _worker_identity(session.config)
    if identity is not None:
        session.config.stash[_HELD] = hold_liveness_lock(*identity)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session: pytest.Session) -> None:
    """In an xdist worker, release the liveness lock as soon as its tests are done."""
    held = session.config.stash.get(_HELD, None)
    if held is not None:
        del session.config.stash[_HELD]
        release_liveness_lock(held)
