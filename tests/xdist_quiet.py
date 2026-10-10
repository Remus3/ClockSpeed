"""CS-1233 - a test that measures wall time can wait until no other worker of its run is live.

ITS OWN RUN ONLY. Each run locks under its own directory, so another whole
suite on the same box - the fleet suite gate admits two at once by default -
is never waited for; that load is a residual this barrier does not remove.

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

ONE WAITER AT A TIME. Two waiters that unlock and probe at the same instant
each see no live sibling, and both would run their quiet arm side by side.
So a waiter that finds the box quiet runs only once it also holds the run's
token lock, which it keeps until it waits again or its session ends; a
second waiter sees the first live again, or finds the token taken, and waits
on. The token is a lock like the liveness files, so a dead holder frees it.

Outside xdist there are no workers, so nothing is waited for. Standard library
plus pytest only, like tests/conftest.py, which registers the two hooks below.
"""

from __future__ import annotations

import contextlib
import errno
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

#: The longest a worker waits for quiet siblings before it fails LOUD: twice the
#: longest whole suite measured on this box, rounded up to a whole minute. A wait
#: sits inside the run it belongs to and never outlasts it, and the first waiting
#: arm waits for every sibling to drain the whole remaining queue - on a local
#: whole suite, for most of the run. The measurements, and the pin that holds
#: this bound above them, are in tests/test_claude_hook.py
#: (test_the_quiet_bound_outlasts_every_measured_wait_and_whole_suite).
#: IT IS NOT UNDER A CI JOB CUTOFF. A bound under the shortest one sat below the
#: waits measured locally and failed a sound whole suite. In CI every shard's
#: pytest step ends inside its duration level, far under this, so no sound wait
#: there comes near it; a hung sibling there is ended by the job's own cutoff -
#: loud, though it names no worker. Locally nothing else ends it, and this does.
QUIET_BOUND_SECONDS: Final = 2520.0

#: The file every waiter of a run competes for; see ONE WAITER AT A TIME above.
#: Not a liveness file, so no probe counts it.
QUIET_FILE_NAME: Final = "quiet.token"

#: How long a worker retries taking its own lock back after a wait. A sibling's
#: probe holds it for the instant between its own lock and unlock calls.
RELOCK_SECONDS: Final = 5.0
RELOCK_POLL_SECONDS: Final = 0.01

#: The errors a non-blocking lock raises when another descriptor holds the
#: byte: EACCES from msvcrt (measured here), EWOULDBLOCK from flock (EAGAIN
#: on Linux and macOS alike). Only these read as held.
HELD_ERRNOS: Final = frozenset({errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK})

LOCK_SUFFIX: Final = ".lock"

# A run id or worker id is used as a path component, so anything but these
# characters is dropped before it gets there.
UNSAFE_NAME: Final = re.compile(r"[^A-Za-z0-9_-]")


class HeldLock(NamedTuple):
    """One worker's liveness lock: the open descriptor and the file it locks."""

    fd: int
    path: Path


def _try_lock(fd: int) -> bool:
    """Take an exclusive, non-blocking lock on byte 0 of ``fd``; report success.

    False means another descriptor holds the byte, and nothing else does. Any
    other error is raised: read as held, a descriptor closed under a waiter
    kept it polling to the bound, and once the number was reused it locked an
    unrelated file.

    Raises:
        OSError: For any error but a held byte - EBADF on a closed descriptor.
    """
    try:
        if sys.platform == "win32":
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        if exc.errno in HELD_ERRNOS:
            return False
        raise
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
    directory = held.path.parent
    # The last worker out removes the token. No waiter is left to want it: a
    # waiter keeps its own liveness file until its session ends.
    with contextlib.suppress(OSError):
        if not any(directory.glob("*" + LOCK_SUFFIX)):
            (directory / QUIET_FILE_NAME).unlink()
    with contextlib.suppress(OSError):
        directory.rmdir()


def _held_elsewhere(fd: int, settle_seconds: float) -> bool:
    """Whether another descriptor holds ``fd``'s byte, retried for ``settle_seconds``.

    Zero tries once, as a poll that comes round again does.
    """
    deadline = time.perf_counter() + settle_seconds
    while not _try_lock(fd):
        if time.perf_counter() >= deadline:
            return True
        time.sleep(RELOCK_POLL_SECONDS)
    _unlock(fd)
    return False


def live_sibling_names(directory: Path, own: str, settle_seconds: float = 0.0) -> list[str]:
    """The ids of the workers other than ``own`` that still hold their lock in ``directory``.

    A file is probed by opening it WITHOUT creating it and trying the lock: a
    file that vanished, or whose lock can be taken, belongs to a worker that has
    finished, died, or is itself waiting. A held lock is retried for
    ``settle_seconds`` before it counts; see :func:`live_siblings_now`.
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
            if _held_elsewhere(fd, settle_seconds):
                live.append(path.name.removesuffix(LOCK_SUFFIX))
        finally:
            os.close(fd)
    return live


def live_sibling_count(directory: Path, own: str, settle_seconds: float = 0.0) -> int:
    """How many workers other than ``own`` still hold their lock in ``directory``."""
    return len(live_sibling_names(directory, own, settle_seconds))


class QuietWaitTimeoutError(RuntimeError):
    """A sibling worker stayed live, or another waiter kept the token, past QUIET_BOUND_SECONDS.

    The live worker ids are a named field, so a caller reads them without ever
    rendering the exception object.
    """

    def __init__(self, siblings: tuple[str, ...], waited: float) -> None:
        """Keep the live sibling ids and the seconds waited, and say both."""
        self.siblings = siblings
        self.waited = waited
        holder = (
            f"sibling worker(s) {list(siblings)} still live"
            if siblings
            else "the quiet token still held by another waiter"
        )
        super().__init__(
            f"CS-1233: {holder} after {waited:.0f}s - the arm that needs a quiet box did not run"
        )


class QuietToken:
    """One worker's descriptor on the run's token file, and whether it holds the lock now."""

    def __init__(self, fd: int) -> None:
        """Open, not yet held."""
        self.fd = fd
        self.held = False

    def take(self) -> bool:
        """Try the token's lock once; report whether this worker holds it now."""
        if not self.held:
            self.held = _try_lock(self.fd)
        return self.held

    def give_back(self) -> None:
        """Let the token go if this worker holds it."""
        if self.held:
            self.held = False
            _unlock(self.fd)


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
    """How many other workers of this run are live now; zero outside xdist.

    ONE SHOT, SO IT RETRIES. Another waiter's probe holds a waiting sibling's
    byte, or a stale file's, for the instant between its own lock and unlock
    calls - the hold :func:`_relock` retries past. A waiter just polls again,
    but a single check would read that instant as a live sibling. So a held
    byte counts only if it stays held for RELOCK_SECONDS; a live sibling holds
    it throughout and is still counted, after that bounded retry.
    """
    identity = _worker_identity(config)
    if identity is None:
        return 0
    return live_sibling_count(*identity, settle_seconds=RELOCK_SECONDS)


def await_quiet_siblings(config: pytest.Config) -> float:
    """Block until no other worker of this run is live; return the seconds waited.

    BOUNDED, AND LOUD AT THE BOUND. A sibling still live after
    QUIET_BOUND_SECONDS raises QuietWaitTimeoutError naming its worker id, so a
    hung sibling is reported here and never passes in silence.

    A WAITING WORKER IS NOT LIVE. It UNLOCKS its byte for the length of the wait
    and locks it again after, keeping its file and descriptor throughout. Arms in
    two files wait, so even ``--dist loadfile`` puts two waiters on two workers
    at once: a waiter that stayed live would count the other as busy, and each
    would wait for ever. The file stays, so the shared run directory is never
    empty while a waiter needs it, and a sibling's release can never remove it
    from under the relock.

    ONE WAITER AT A TIME. Quiet is not enough: the waiter also takes the run's
    token, keeping it until it next waits or its session ends, and gives it
    back on entry here so another waiter can have the box in between. Two
    waiters that find the box quiet together are let go one after the other.

    Raises:
        QuietWaitTimeoutError: When a sibling is still live, or another waiter
            still holds the token, at the bound.
    """
    identity = _worker_identity(config)
    if identity is None:
        return 0.0
    directory, worker = identity
    held = config.stash.get(_HELD, None)
    token = _quiet_token(config, directory)
    started = time.perf_counter()
    token.give_back()
    if held is not None:
        _unlock(held.fd)
    try:
        while (live := live_sibling_names(directory, worker)) or not token.take():
            waited = time.perf_counter() - started
            if waited >= QUIET_BOUND_SECONDS:
                raise QuietWaitTimeoutError(tuple(live), waited)
            time.sleep(POLL_SECONDS)
    finally:
        if held is not None:
            _relock(held)
    return time.perf_counter() - started


def _quiet_token(config: pytest.Config, directory: Path) -> QuietToken:
    """This worker's descriptor on the run's token file, opened on its first wait."""
    token = config.stash.get(_TOKEN, None)
    if token is None:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / QUIET_FILE_NAME
        token = QuietToken(os.open(path, os.O_RDWR | os.O_CREAT, 0o600))
        config.stash[_TOKEN] = token
    return token


_HELD: Final = pytest.StashKey[HeldLock]()
_TOKEN: Final = pytest.StashKey[QuietToken]()


def pytest_sessionstart(session: pytest.Session) -> None:
    """In an xdist worker, take this worker's liveness lock before collection."""
    identity = _worker_identity(session.config)
    if identity is not None:
        session.config.stash[_HELD] = hold_liveness_lock(*identity)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session: pytest.Session) -> None:
    """In an xdist worker, release the token and the liveness lock once its tests are done."""
    token = session.config.stash.get(_TOKEN, None)
    if token is not None:
        del session.config.stash[_TOKEN]
        # Unlocked before the close: Windows frees a lock left on a closed
        # handle only when it gets round to it.
        with contextlib.suppress(OSError):
            token.give_back()
        os.close(token.fd)
    held = session.config.stash.get(_HELD, None)
    if held is not None:
        del session.config.stash[_HELD]
        release_liveness_lock(held)
