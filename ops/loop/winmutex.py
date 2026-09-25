#!/usr/bin/env python
r"""Named-mutex wrapper - a FORKED copy, and this header is the fork record.

WHAT CLOCKSPEED USES IT FOR. Exactly one thing: making the headless queue driver
a singleton on this box. The driver holds a named mutex for its whole run, so a
second launch of the same driver blocks or refuses instead of firing a second
worker into the same worktree. Nothing else in this repository serializes on the
OS namespace, and no resource name is declared here - the caller names its own
mutex, because a name declared in this file would be a name this file has to
know the purpose of.

THIS IS A FORK, DECLARED AS ONE. It descends from a file that was
BYTE-IDENTICAL-BY-CONTRACT across three sibling repositories, pinned there at

    forked from - historical
        sha256  f1b4b011112685efb88616c52752657cf896fbb0993b2d2d264e7b3edde8b4f4
    upstream status  GONE - measured 2026-09-20

The first line is the upstream these bytes were cut from. It is a statement
about HISTORY and is never bumped to whatever the carriers hold today - this
copy was not forked from that. The second says the upstream no longer exists to
compare against: the CS-1160 census of 2026-09-20 found no copy on this machine
carrying that digest, because the carriers have since moved their shared file.
The FORK's own digest - a claim about the present - is not restated here, since
no file can carry its own hash: ``tests/test_lane_lock.py`` owns it as
``FORKED_WINMUTEX_DIGEST``, and grades the two lines above against what this
tree can reach. An upstream this tree's files or history carry must match and
must not be declared GONE; one it cannot reach must be, with the measured date.

WHAT CHANGED:

  * the two module-level resource names the upstream declares - one for a
    metered third-party account, one for a GPU - are DELETED. Clockspeed has
    neither. ``tests/test_lane_lock.py`` asserts over this module's attributes
    that no such name came back;
  * the docstring is retargeted at this project and says what this project uses
    the primitive for;
  * the fail-open and abandoned-mutex behaviour below is UNCHANGED, because
    those are the measured parts and a fork is not a licence to redesign them.

WHY A BYTE-IDENTICAL JOIN WAS REFUSED. That pin is not a formatting convention,
it is a coordination protocol: the sibling trees deliberately share the OS
namespace those names live in, and their digest arm is what stops one of them
drifting away from the others silently. A fourth copy is not covered by that
pin, and a copy that carries their resource names would put this project into
their namespace over resources it does not use. Forking states the divergence in
the open instead of pretending to an identity that is not there. The price is
that the upstream's pin no longer covers these bytes, so this repository states
its own digest for this file in ``tests/test_lane_lock.py`` - a fork nothing
pins drifts exactly as silently as the copy it forked from.

ABANDONED MUTEX. If a holder dies without releasing, Windows hands the next
waiter WAIT_ABANDONED. That is treated as ACQUIRED, with a warning: the previous
holder's work may be half-done, but refusing to proceed would let one crashed
process deadlock the box indefinitely.

OFF WINDOWS this degrades to a context manager that yields unheld - and SAYS SO,
using the same UNSERIALIZED marker as the two fail-open branches. A SILENT yield
is the bug: every overlap arm then passes VACUOUSLY on a POSIX runner and the
log carries no evidence that nothing was serialized, so green proves nothing.
"""

from __future__ import annotations

import contextlib
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

_WAIT_OBJECT_0 = 0x00000000
_WAIT_ABANDONED = 0x00000080
_WAIT_TIMEOUT = 0x00000102
_INFINITE = 0xFFFFFFFF

_MS_PER_SECOND = 1000

#: The marker every unserialized path emits. ONE spelling, so a log reader can
#: find every occasion the lock was not actually held.
_UNSERIALIZED = "winmutex: UNSERIALIZED"


# The upstream spelling is kept so a caller ported alongside this file needs no
# edit. Renaming it to end in "Error" would be a second divergence from the fork
# parent bought with nothing.
class MutexTimeout(RuntimeError):  # noqa: N818 - fork parity, see above
    """The named mutex did not become free inside the caller's timeout."""


@contextmanager
def hold(
    name: str, *, timeout: float | None = None, log: Callable[[str], Any] | None = None
) -> Iterator[Any]:
    """Hold a named mutex for the duration of the block.

    Args:
        name: The mutex name, in the OS namespace the caller intends.
        timeout: Seconds to wait, or None to wait forever.
        log: A one-argument sink for the acquire and release trace. Passing one
            is what makes the hold window OBSERVABLE in a log file rather than
            merely arguable from reading this code.

    Yields:
        The mutex handle, or None when the block runs unserialized.

    Raises:
        MutexTimeout: The mutex did not become free in time. Callers treat that
            as a failed step, never as permission to proceed unserialized.
    """
    if sys.platform != "win32":
        # WINDOWS-ONLY ASSERTION, made explicit. Real serialization here needs
        # the Win32 named-mutex namespace and there is no primitive off Windows
        # to degrade to, so this yields unheld and says so with the SAME marker
        # as the two fail-open branches below. NOT an fcntl fallback: POSIX
        # record locks are per-process, so a two-threads-one-process arm would
        # stay red without a second lock layer.
        if log:
            log(
                f"{_UNSERIALIZED} {name} - no named mutex on {sys.platform};"
                " proceeding WITHOUT the lock"
            )
        yield None
        return

    import ctypes  # noqa: PLC0415 - Windows-only, deferred so import stays portable
    from ctypes import wintypes  # noqa: PLC0415 - same

    k32 = ctypes.windll.kernel32
    k32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    k32.CreateMutexW.restype = wintypes.HANDLE
    k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k32.WaitForSingleObject.restype = wintypes.DWORD
    k32.ReleaseMutex.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]

    handle = k32.CreateMutexW(None, False, name)
    if not handle:
        # Cannot create the mutex - rare, a name or ACL problem. Fail OPEN with
        # a loud log rather than wedging the run: an unserialized driver is a
        # risk, a deadlocked driver is a dead run.
        if log:
            log(f"{_UNSERIALIZED} {name} - CreateMutexW failed; proceeding WITHOUT the lock")
        yield None
        return

    milliseconds = _INFINITE if timeout is None else int(max(0.0, timeout) * _MS_PER_SECOND)
    acquired = False
    try:
        result = k32.WaitForSingleObject(handle, milliseconds)
        if result == _WAIT_TIMEOUT:
            message = f"{name} not free within {timeout}s"
            raise MutexTimeout(message)
        acquired = result in (_WAIT_OBJECT_0, _WAIT_ABANDONED)
        if result == _WAIT_ABANDONED and log:
            log(
                f"winmutex: {name} was ABANDONED by a dead holder - acquiring"
                " anyway (its work may be half-done)"
            )
        # ACQUIRED IS GATED ON `acquired`, AND THE FAIL-OPEN BRANCH EMITS A
        # DISTINCT MARKER. Getting this wrong is worse than not logging at all:
        # an unconditional ACQUIRED on a fail-open path opens a window that the
        # gated RELEASED never closes, so a window-pairing reader drops it
        # silently - making the ONE occasion the mutex did not serialize the one
        # occasion invisible to an overlap check.
        if acquired:
            if log:
                log(f"winmutex: ACQUIRED {name}")
        elif log:
            log(
                f"{_UNSERIALIZED} {name} - unexpected wait result {result};"
                " proceeding WITHOUT the lock"
            )
        yield handle
    finally:
        # A handle this process is finished with must not turn a real failure
        # into a second one on the way out, so both teardown calls are quiet.
        if acquired:
            if log:
                log(f"winmutex: RELEASED {name}")
            with contextlib.suppress(OSError):
                k32.ReleaseMutex(handle)
        with contextlib.suppress(OSError):
            k32.CloseHandle(handle)
