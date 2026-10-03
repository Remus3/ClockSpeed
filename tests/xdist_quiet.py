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
starts no test until every worker has reported its collection.

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


def live_sibling_count(directory: Path, own: str) -> int:
    """How many workers other than ``own`` still hold their lock in ``directory``.

    A file is probed by opening it WITHOUT creating it and trying the lock: a
    file that vanished, or whose lock can be taken, belongs to a worker that has
    finished or died.
    """
    if not directory.is_dir():
        return 0
    own_name = (UNSAFE_NAME.sub("", own) or "worker") + LOCK_SUFFIX
    live = 0
    for path in directory.glob("*" + LOCK_SUFFIX):
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
                live += 1
        finally:
            os.close(fd)
    return live


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

    No bound of its own: a sibling that never finishes is a hung suite, which
    the job's own timeout already ends, and a sibling that dies frees its lock.
    """
    identity = _worker_identity(config)
    if identity is None:
        return 0.0
    started = time.perf_counter()
    while live_sibling_count(*identity):
        time.sleep(POLL_SECONDS)
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
