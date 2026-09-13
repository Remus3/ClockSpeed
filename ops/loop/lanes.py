#!/usr/bin/env python
r"""Lane lock - a headless lane is mutually exclusive, one holder at a time.

The roster is stated ONCE, in ``LANES`` below, and this prose deliberately does
not recite its size. The upstream this was ported from carried a spelled count
here while the tuple two lines under it already held a different number, and a
count in prose goes stale the moment the roster changes (CLAUDE.md section 4).

DERIVED FROM, NOT COPIED FROM. Two things this module needs come from the
sibling projects' shared slot governor, ``slots.py``, pinned across those trees
at sha256

    71fa2a683f2eaa04dd61feb2bebc646b5f9086e692c5acc05a9239de49d07d1b

by a digest arm in each tree that vendors it. RE-RECORDED 2026-09-07: the
carriers reworded that file's opening paragraph so it names no sibling project,
and the digest above was re-measured on THIS disk across all three carrier
working copies rather than taken from the hand-off note that announced it. The
change was prose only - the differing line indices are five consecutive
docstring lines and nothing else - so what is derived here is unaffected in
behaviour and only its recorded identity moved. The pid probe and the
``O_CREAT|O_EXCL`` bucket at a single slot are re-implemented HERE rather than
copied, and the reason is behavioural rather than stylistic. That file sets its
default root to a machine-wide token bucket under ProgramData which several
other trees ration between themselves. Importing it would enrol Clockspeed in
that bucket and consume a slot those trees are sharing - a behavioural change to
other repositories, made unilaterally, which is exactly the silent divergence
their byte-identity pin exists to prevent. So the DEFAULT_ROOT here is inside
this repository, the two primitives are local, and no upstream file is read,
imported or edited. See ``ops/loop/winmutex.py`` for the other half of the
ruling, which came out the other way and is a declared FORK.

ONE SLOT PER LANE, AND THE SLOT IS DERIVED FROM THE ROSTER. ``lock_name`` places
a lane at ``<slot>.lock`` by its position in ``LANES``, so widening the roster
widens the bucket with it and no second constant has to be remembered. THE
SHARED-SLOT SHAPE IS THE DEFECT THIS REPLACES: a guard taken per lane over ONE
shared lock file is worse than either half by itself, because the guards wave
every lane through while the file quietly serialises them, and each holder
believes it owns something another holder also believes it owns. A lane off the
roster gets no slot at all rather than the default one - handing a typo the
first lane's lock would claim a running worker's slot.

WHY THREE STATES AND NOT TWO. A lock file whose pid is DEAD is indistinguishable
from a live holder by file inspection alone: it has the same name, the same
shape and a plausible timestamp. Every reader that treats EXISTENCE as RUNNING
therefore reports a worker that is not there, and the lane stays wedged until
somebody deletes the file by hand. ``lane_state`` answers FREE, RUNNING or
RECLAIMABLE and decides by PROBING the pid, never by stat-ing the file.
RECLAIMABLE must never render as RUNNING.

READS DO NOT WRITE. ``lane_state`` is the poll path a dashboard and a driver
both call. Auto-clearing a stale lock inside a read would make a rendering pass
mutate the control plane, and two pollers would then race each other into a
reclaim. Clearing is a deliberate act and happens only inside
``try_acquire_lane``.

REFUSE, DO NOT QUEUE. A fire against a genuinely held lane returns
``{"ok": False, "refused": "lane_held", ...}`` and mutates NOTHING on disk. A
queue would turn one fire into a run that starts minutes later against a tree
that has moved on.

NOTHING HERE STARTS A PROCESS. This module is pure state management: it decides
who may run, it does not run anything, and it is therefore testable without
spawning. ``pid`` in the payload is the pid of whatever CLAIMED the lane;
``ops/loop/lane_launcher.py`` re-points it at the worker it spawns.
"""

from __future__ import annotations

import contextlib
import json
import os
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent

#: The pointer a git worktree's ``.git`` FILE carries, and the directory name
#: git puts its per-worktree administrative area under.
_GITDIR_PREFIX = "gitdir:"
_WORKTREES_DIR = "worktrees"


def _main_tree_root(root: Path | None = None) -> Path:
    """Resolve the MAIN working tree, even when imported from a worktree.

    ``parents[2]`` alone is wrong the moment this module is imported from inside
    a git worktree: it answers the WORKTREE, and the worktree-mandatory guard
    below then INVERTS - it would reject the worktree a lane legitimately runs
    in, and accept the main tree it must never touch. This lane is
    worktree-mandatory, so the naive form is a live hole rather than a
    theoretical one, and it is live in this repository today.

    Detection needs no subprocess. In a main tree ``.git`` is a DIRECTORY; in a
    worktree it is a FILE holding ``gitdir: <main>/.git/worktrees/<name>``, and
    the main tree is that path's third parent. A relative pointer is joined to
    the worktree and normalised TEXTUALLY rather than through ``resolve()``,
    because ``resolve()`` on Windows also expands 8.3 short path components and
    would answer a different spelling of the same directory.

    Total by construction: a missing, unreadable or unrecognised ``.git``
    degrades to the candidate rather than raising at import time, which keeps a
    plain export and a temporary directory working.

    Args:
        root: The candidate tree root. Defaults to this file's third parent.

    Returns:
        The main working tree.
    """
    candidate = Path(__file__).resolve().parents[2] if root is None else Path(root)
    dotgit = candidate / ".git"
    with contextlib.suppress(OSError):
        if dotgit.is_file():
            raw = dotgit.read_text(encoding="utf-8").strip()
            if raw.startswith(_GITDIR_PREFIX):
                gitdir = Path(raw[len(_GITDIR_PREFIX) :].strip())
                if not gitdir.is_absolute():
                    gitdir = Path(os.path.normpath(candidate / gitdir))
                if gitdir.parent.name == _WORKTREES_DIR:
                    return gitdir.parents[2]
    return candidate


#: The MAIN tree, resolved through the ``.git``-file indirection above. Read at
#: import so every caller shares one answer.
REPO_ROOT = _main_tree_root()

#: The roster. Its size is not written anywhere but here.
LANES = ("queue", "queue-b")


def slot_index(lane: Any) -> int:
    """The slot a lane owns, DERIVED from its position on the roster.

    A ROSTER MEMBER IS NOT A DEFAULT. An unrecognised lane raises rather than
    answering slot 0: a typo handed the first lane's own lock would claim a
    running worker's slot, and a caller that cannot spell its lane has no
    business holding anything.

    Args:
        lane: The lane to place.

    Returns:
        Its slot index.

    Raises:
        ValueError: The lane is not on the roster.
    """
    try:
        return LANES.index(str(lane))
    except ValueError:
        message = f"unknown lane {lane!r} - valid lanes are {', '.join(LANES)}"
        raise ValueError(message) from None


def lock_name(lane: Any) -> str:
    """The lock file one lane holds. The upstream bucket names slot i ``<i>.lock``.

    ONE FILE PER LANE IS THE WHOLE MUTEX. A per-lane guard layered over a
    SHARED slot file is worse than either half alone: the guards wave both
    lanes through while the file serialises them, so each lane believes it
    holds something the other also believes it holds.

    Args:
        lane: The lane.

    Returns:
        The lock's file name.

    Raises:
        ValueError: The lane is not on the roster.
    """
    return f"{slot_index(lane)}.lock"


#: One holder per lane, so the width IS the roster's. DERIVED rather than
#: restated: a number written beside the tuple it counts is a number that drifts
#: the moment the tuple changes (CLAUDE.md section 4).
MAX_SLOTS = len(LANES)

#: THE LANE A CALLER THAT NAMES NONE GETS, and it is stated rather than implied.
#: The poll path predates the roster's widening and a required argument here
#: would have been a silent behaviour change for every existing reader. A reader
#: that cares which lane it is looking at must SAY so - see ``lane_states`` for
#: the whole-roster answer.
DEFAULT_LANE = LANES[0]
LOCK_NAME = lock_name(DEFAULT_LANE)

#: Inside this repository, deliberately - see the DERIVED FROM note above on
#: why joining the shared machine-wide bucket was refused.
DEFAULT_ROOT = _HERE / "control" / "lanes"

FREE = "FREE"
RUNNING = "RUNNING"
RECLAIMABLE = "RECLAIMABLE"

#: A lock is created EMPTY by the exclusive create and filled a moment later.
#: Inside this window an unparseable lock is presumed live, so a reader cannot
#: reclaim a lane out from under an acquirer that is mid-write. Past it nothing
#: about the lock can be proven alive, so it reads RECLAIMABLE rather than
#: wedging the lane forever.
WRITE_GRACE_S = 30.0

#: Two reads of the SAME process's creation time are the same float, so this is
#: a guard against representation drift and not a tolerance to tune. A real pid
#: reuse is separated by whole seconds at minimum, so nothing legitimate lands
#: inside it.
_PID_IDENTITY_EPS_S = 1.0

#: ``Path.replace`` can lose to a virus scanner or an open handle on Windows. A
#: few short retries turn a transient sharing violation into a completed rename
#: - the precedent and its reason are the rename retry in
#: ``scripts/make_cert.py``.
_RENAME_ATTEMPTS = 5
_RENAME_PAUSE_SECONDS = 0.05

#: OpenProcess flags and exit codes, named so no bare integer stands in a
#: comparison. ERROR_INVALID_PARAMETER is what Windows reports when there is no
#: such process; anything else means it exists and we may not look at it.
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_STILL_ACTIVE = 259
_ERROR_INVALID_PARAMETER = 87

#: Lock path -> the identity THIS process wrote there. The ABA guard: a late
#: release from a previous holder must not unlink the lock of whoever reclaimed
#: the lane after it.
_OWNED: dict[str, tuple[str | None, float | None, int | None]] = {}


# ---------------------------------------------------------------------------
# Small readers
# ---------------------------------------------------------------------------


def _key(path: Any) -> str:
    """A comparable spelling of a path.

    ``normpath`` rather than ``resolve`` on purpose: resolve expands 8.3 short
    components on Windows, so two spellings of one directory stop comparing
    equal depending on which one the caller happened to hold.

    Args:
        path: Anything path-like.

    Returns:
        The case-folded, normalised, absolute spelling.
    """
    return os.path.normcase(os.path.normpath(str(Path(path).absolute())))


def _int_or_none(value: Any) -> int | None:
    """The value as an int, or None when it is not one."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    """The value as a float, or None when it is not one."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _str_or_none(value: Any) -> str | None:
    """The value as a string, or None when it is absent."""
    return None if value is None else str(value)


def _remove_quietly(path: Path) -> None:
    """Delete one file, reporting nothing. Used only on scratch and on locks."""
    with contextlib.suppress(OSError):
        path.unlink()


def _posix_alive(pid: int) -> bool:
    """Signal 0 as a liveness probe. A pid we may not signal is treated ALIVE."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _windows_alive(pid: int) -> bool:
    """OpenProcess with QUERY_LIMITED_INFORMATION as a liveness probe.

    That access level succeeds for processes owned by OTHER users too, which
    matters here: a lane may be started by a scheduled task and read by an
    interactive session. A pid that exists but cannot be inspected is treated as
    ALIVE - waiting is the conservative error, double-booking a lane is not.

    Args:
        pid: The process id to probe.

    Returns:
        True when the process is alive, or exists and cannot be inspected.
    """
    import ctypes  # noqa: PLC0415 - Windows-only, deferred so import stays portable

    k32 = ctypes.windll.kernel32
    handle = k32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return bool(k32.GetLastError() != _ERROR_INVALID_PARAMETER)
    try:
        code = ctypes.c_ulong()
        if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return True
        return bool(code.value == _STILL_ACTIVE)
    finally:
        k32.CloseHandle(handle)


def pid_alive(pid: Any) -> bool:
    """True when the pid names a live process.

    DERIVED from the sibling projects' shared ``slots.py`` rather than imported
    from it - see the module docstring on why a copy was refused.

    Args:
        pid: The process id to probe.

    Returns:
        True when the process is alive or exists but cannot be inspected.
    """
    number = _int_or_none(pid)
    if number is None or number <= 0:
        return False
    return _windows_alive(number) if os.name == "nt" else _posix_alive(number)


def proc_started(pid: Any) -> float | None:
    """The process's creation time, or None when it cannot be established.

    A pid alone does not name a process - the operating system reissues it, and
    a lane whose worker died can otherwise read RUNNING behind whatever service
    inherited the number. ``(pid, start time)`` does name one, and this is the
    second half of that pair.

    TOTAL BY CONSTRUCTION. A dead pid, a pid this process may not query, a
    missing psutil and anything else that goes wrong all answer None. Every
    caller reads None as "cannot prove reuse" and falls back to the pid probe
    alone, so an unavailable source degrades to the previous behaviour instead
    of freeing a lane that is live.

    Args:
        pid: The process id to probe.

    Returns:
        The creation time, or None when it cannot be established.
    """
    number = _int_or_none(pid)
    if number is None or number <= 0:
        return None
    try:
        import psutil  # noqa: PLC0415 - optional; absence must degrade, not fail
    except ImportError:
        return None
    try:
        return float(psutil.Process(number).create_time())
    except Exception:  # NoSuchProcess, AccessDenied, anything at all - see above
        return None


#: PUBLIC ON PURPOSE (merge decision, CS-918). `ops/loop/queue_loop.py` uses
#: this as its liveness seam, and a driver reaching into another module's
#: PRIVATE name for the one predicate both must agree on is the shape that lets
#: the two quietly diverge. The upstream this was ported from does exactly that
#: and its own docstring has to apologise for it.
def holder_is_a_stranger(pid: Any, recorded: Any) -> bool:
    """True only when the live pid is PROVABLY not the process that claimed it.

    Every uncertain case answers False - no recorded value, an unparseable one,
    or no readable start time for the live pid. Freeing a lane on a guess
    double-books a running worker, which is strictly worse than the wedge this
    function exists to prevent.

    Args:
        pid: The pid currently in the lock.
        recorded: The creation time the lock recorded for it.

    Returns:
        True when the two provably name different processes.
    """
    expected = _float_or_none(recorded)
    if expected is None:
        return False
    actual = proc_started(pid)
    if actual is None:
        return False
    return abs(actual - expected) > _PID_IDENTITY_EPS_S


def _resolve_root(root: Any) -> Path:
    """The lock root to use, defaulting to this repository's own."""
    return DEFAULT_ROOT if root is None else Path(root)


def lock_path(root: Any = None, lane: Any = None) -> Path:
    """Where one lane's lock lives.

    Read-only helper - it creates nothing, so it is safe on the poll path.

    Args:
        root: The lock root, or None for the default.
        lane: The lane, or None for ``DEFAULT_LANE``.

    Returns:
        The lock's path.

    Raises:
        ValueError: The lane is not on the roster.
    """
    return _resolve_root(root) / lock_name(DEFAULT_LANE if lane is None else lane)


def _read_payload(lock: Path) -> dict[str, Any]:
    """The lock's payload, or {} when it is missing, empty or half-written.

    Args:
        lock: The lock file.

    Returns:
        The decoded payload, or an empty mapping.
    """
    try:
        raw = lock.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        record = json.loads(raw)
    except ValueError:
        return {}
    return record if isinstance(record, dict) else {}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def lane_state(root: Any = None, now: Any = None, lane: Any = None) -> dict[str, Any]:
    """FREE, RUNNING or RECLAIMABLE for one lane's lock. NEVER mutates anything.

    RECLAIMABLE means a lock file is present but its holder is provably gone. It
    is REPORTED, not acted on: clearing it is ``try_acquire_lane``'s job, for
    the reason in the module docstring.

    Args:
        root: The lock root, or None for the default.
        now: The wall clock reading to age the lock against. Injected so an
            ageing arm never has to sleep.
        lane: The lane to read, or None for ``DEFAULT_LANE``. A reader covering
            the whole roster wants ``lane_states`` instead - asking for one lane
            and reading the answer as "the lane" is how a widened roster goes
            unnoticed.

    Returns:
        The state, the holder it read, and the lock's age in seconds.

    Raises:
        ValueError: The lane is not on the roster.
    """
    lock = lock_path(root, lane)
    reading = time.time() if now is None else float(now)
    if not lock.exists():
        return {
            "state": FREE,
            "lane": None,
            "pid": None,
            "run_id": None,
            "worktree": None,
            "age_s": None,
        }

    record = _read_payload(lock)
    stamp = _float_or_none(record.get("ts"))
    if stamp is None:
        try:
            stamp = lock.stat().st_mtime
        except OSError:
            stamp = None
    pid = _int_or_none(record.get("pid"))
    answer: dict[str, Any] = {
        "state": RUNNING,
        "lane": _str_or_none(record.get("lane")),
        "pid": pid,
        "run_id": _str_or_none(record.get("run_id")),
        "worktree": _str_or_none(record.get("worktree")),
        "age_s": None if stamp is None else max(0.0, reading - stamp),
    }
    if pid is None:
        # No readable holder at all - see WRITE_GRACE_S.
        if answer["age_s"] is not None and answer["age_s"] > WRITE_GRACE_S:
            answer["state"] = RECLAIMABLE
    elif not pid_alive(pid):
        answer["state"] = RECLAIMABLE
    elif holder_is_a_stranger(pid, record.get("pid_started")):
        # Alive, but not the same process: the holder died and the operating
        # system reissued its pid. Without this the lane reads RUNNING forever.
        answer["state"] = RECLAIMABLE
    return answer


def lane_states(root: Any = None, now: Any = None) -> dict[str, dict[str, Any]]:
    """Every lane on the roster and its state. NEVER mutates anything.

    THE WHOLE-ROSTER READ, so a dashboard or a driver never has to know the
    roster's width to poll it. Deriving the population here rather than at each
    caller is what stops a widened roster from being invisible to a reader that
    asked about one lane and rendered the answer as "the lane".

    Args:
        root: The lock root, or None for the default.
        now: The wall clock reading to age the locks against.

    Returns:
        A mapping of lane to the state ``lane_state`` reports for it.
    """
    return {lane: lane_state(root, now, lane) for lane in LANES}


# ---------------------------------------------------------------------------
# Acquire and release
# ---------------------------------------------------------------------------


def _require_worktree(worktree: Any) -> Path:
    """A lane may NEVER run against the main tree.

    A lane rewrites files while it works; pointed at the checkout the operator
    is reading, it edits the tree out from under them, and two writers in one
    working directory is the concurrent-index corruption class, which is not
    recoverable by retrying. Only a git worktree is a legal target, so an absent
    worktree is a hard error rather than a default.

    Args:
        worktree: The proposed working directory.

    Returns:
        The worktree as a path.

    Raises:
        ValueError: The worktree is absent, or it is the main tree.
    """
    if worktree is None or not str(worktree).strip():
        message = "worktree is mandatory"
        raise ValueError(message)
    path = Path(str(worktree).strip()).expanduser()
    if _key(path) == _key(REPO_ROOT):
        message = "worktree is mandatory - a lane may never run against the main tree"
        raise ValueError(message)
    return path


def _exclusive_create(root: Any, lane: Any, payload: dict[str, Any]) -> Path | None:
    """Create the lock, or answer None because somebody else already holds it.

    ``O_CREAT|O_EXCL`` rather than the tmp-plus-replace this module uses for
    every other write: EXCLUSIVITY IS THE MUTEX, and a replace cannot be
    exclusive. DERIVED from the sibling projects' shared bucket - see the module
    docstring on why it is not imported.

    Args:
        root: The lock root.
        lane: The lane claiming, which decides WHICH slot is created.
        payload: The holder record to write into the lock.

    Returns:
        The lock path, or None when the lane was already taken.
    """
    directory = Path(root)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / lock_name(lane)
    try:
        handle = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        return None
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream)
    except OSError:
        _remove_quietly(lock)
        return None
    return lock


def _atomic_write(target: Path, data: bytes) -> bool:
    """Replace a file's contents without ever leaving the path absent.

    tmp plus ``Path.replace``, so the exclusivity another acquirer relies on
    holds throughout. The retry is for Windows, where a scanner or an open
    handle can lose a rename that would succeed a moment later. The scratch file
    is removed on every failure path, and the pause is skipped entirely when it
    is zero so a test never has to sleep.

    Args:
        target: The file to replace.
        data: Its new contents.

    Returns:
        True when the replacement landed.
    """
    scratch = target.with_name(f"{target.name}.{os.getpid()}.tmp")
    try:
        scratch.write_bytes(data)
    except OSError:
        _remove_quietly(scratch)
        return False
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            scratch.replace(target)
        except PermissionError:
            if _RENAME_PAUSE_SECONDS:
                time.sleep(_RENAME_PAUSE_SECONDS * (attempt + 1))
        except OSError:
            break
        else:
            return True
    _remove_quietly(scratch)
    return False


def _reclaim(root: Path, lane: Any) -> bool:
    """Clear a lock whose holder is provably gone. Never touches a live one.

    Args:
        root: The lock root.
        lane: The lane whose slot is being reclaimed. THE SLOT IS PART OF THE
            DECISION: reclaiming by root alone would clear the default lane's
            lock whichever lane asked, which is a live worker's lock.

    Returns:
        True when the lane is free afterwards.
    """
    lock = lock_path(root, lane)
    if not lock.exists():
        return True
    if lane_state(root, None, lane)["state"] != RECLAIMABLE:
        return False
    _remove_quietly(lock)
    return not lock.exists()


def _refusal(state: dict[str, Any]) -> dict[str, Any]:
    """The answer a genuinely held lane gets. Writes nothing, by construction."""
    return {"ok": False, "refused": "lane_held", "holder": state["lane"], "pid": state["pid"]}


def try_acquire_lane(lane: str, *, run_id: Any, worktree: Any, root: Any = None) -> dict[str, Any]:
    """Claim the lane lock, or refuse.

    A holder whose pid is dead is reclaimed rather than respected: a crashed
    lane must never deadlock the next fire. A holder that is genuinely live is
    refused, and the refusal touches nothing on disk - the state is read BEFORE
    any mkdir or scratch write for exactly that reason.

    Args:
        lane: The lane to claim. Must be in ``LANES``.
        run_id: The caller's identifier for this run.
        worktree: The working directory the lane will run in. Mandatory.
        root: The lock root, or None for the default.

    Returns:
        ``{"ok": True, "lane", "run_id", "worktree", "token"}`` on success -
        ``token`` is the lock path and is what ``release_lane`` wants back - or
        ``{"ok": False, "refused": "lane_held", "holder", "pid"}``, which is a
        normal answer rather than an error.

    Raises:
        ValueError: The lane is unknown, or the worktree is absent or the main
            tree.
    """
    slot_index(lane)  # ROSTER CHECK, raising the one message for an unknown lane
    target = _require_worktree(worktree)
    directory = _resolve_root(root)

    state = lane_state(directory, None, lane)
    if state["state"] == RUNNING:
        return _refusal(state)
    if state["state"] == RECLAIMABLE:
        _reclaim(directory, lane)

    payload: dict[str, Any] = {
        "pid": os.getpid(),
        "lane": lane,
        "run_id": str(run_id),
        "worktree": str(target),
        "ts": time.time(),
        "repo": str(REPO_ROOT),
        # The other half of the holder's identity. `ts` is when the lane was
        # CLAIMED and is not a substitute: a worker legitimately starts seconds
        # after the claim, so comparing a start time against ts needs a
        # tolerance and is wrong in both directions.
        "pid_started": proc_started(os.getpid()),
    }
    token = _exclusive_create(directory, lane, payload)
    if token is None:
        # Lost a race between the read above and the exclusive create.
        return _refusal(lane_state(directory, None, lane))
    _OWNED[_key(token)] = (payload["run_id"], payload["ts"], payload["pid"])
    return {
        "ok": True,
        "lane": lane,
        "run_id": payload["run_id"],
        "worktree": payload["worktree"],
        "token": str(token),
    }


def _lock_for(token: Any, root: Any) -> Path | None:
    """The lock a token names, or None when the token is empty.

    Args:
        token: What ``try_acquire_lane`` handed back.
        root: The lock root, used only when the token is a bare name.

    Returns:
        The lock path, or None.
    """
    if token is None or not str(token).strip():
        return None
    lock = Path(str(token).strip())
    if not lock.is_absolute():
        lock = _resolve_root(root) / lock.name
    return lock


def _identity(record: dict[str, Any]) -> tuple[str | None, float | None, int | None]:
    """The triple that names one holder of one lock."""
    return (
        _str_or_none(record.get("run_id")),
        _float_or_none(record.get("ts")),
        _int_or_none(record.get("pid")),
    )


def _is_ours(lock: Path, record: dict[str, Any]) -> bool:
    """True when the lock's CURRENT payload is the identity we recorded.

    This is the ABA guard. If the lane was reclaimed and re-acquired after our
    token was issued, the payload has moved on and this answers False, so a late
    release cannot unlink the new holder's lock. Limit, stated rather than
    hidden: a token is a path and every holder uses the same path, so two
    acquisitions by THIS process are indistinguishable - harmless, since both
    are us. The cross-process case, the one that matters, is caught.

    Args:
        lock: The lock file.
        record: Its current payload.

    Returns:
        True when this process may act on the lock.
    """
    owned = _OWNED.get(_key(lock))
    identity = _identity(record)
    if owned is not None:
        return identity == owned
    return identity[2] == os.getpid()


def repoint_lane_pid(token: Any, pid: Any, root: Any = None) -> bool:
    """Re-point a held lock at the process that ACTUALLY runs the lane.

    ``try_acquire_lane`` records the pid of whatever CLAIMED the lane, which for
    a driver-owned loop is a process that outlives every worker. Left that way,
    ``lane_state`` probes a pid that is always alive and the lane reads RUNNING
    forever after its worker died - the stale-lock failure the three states
    exist to prevent. The launcher re-points the lock the moment it has a worker
    pid.

    The claimer's start time is REPLACED rather than left behind. A driver's
    start time can be hours old, so a stale value here would make every
    re-pointed lock - which is every real lane fire - read as a pid reuse and
    free itself under a live worker.

    ``_OWNED`` is updated in the same breath, or the ABA guard in
    ``release_lane`` would refuse to release a lock this process owns.

    Returns False rather than raising: a launcher that cannot re-point must fall
    back to releasing the lane, not crash mid-spawn.

    Args:
        token: What ``try_acquire_lane`` handed back.
        pid: The worker's pid.
        root: The lock root, used only when the token is a bare name.

    Returns:
        True when the lock now names the worker.
    """
    lock = _lock_for(token, root)
    if lock is None:
        return False
    record = _read_payload(lock)
    worker = _int_or_none(pid)
    if not record or worker is None or not _is_ours(lock, record):
        return False

    key = _key(lock)
    owned = _OWNED.get(key)
    run_id, stamp, claimer = _identity(record)
    record["pid"] = worker
    record["claimed_by_pid"] = claimer
    record["pid_started"] = proc_started(worker)
    if not _atomic_write(lock, json.dumps(record).encode("utf-8")):
        return False
    _OWNED[key] = (owned[0], owned[1], worker) if owned is not None else (run_id, stamp, worker)
    return True


def release_lane(token: Any, root: Any = None) -> bool:
    """Release a lock handed out by ``try_acquire_lane``. Idempotent.

    True when this call removed the lock; False when there was nothing of ours
    to remove. NEVER raises - a release runs in a finally, and a release that
    can throw turns one failure into two.

    Args:
        token: What ``try_acquire_lane`` handed back.
        root: The lock root, used only when the token is a bare name.

    Returns:
        True when this call removed the lock.
    """
    lock = _lock_for(token, root)
    if lock is None:
        return False
    key = _key(lock)
    if not lock.exists():
        _OWNED.pop(key, None)
        return False
    record = _read_payload(lock)
    if not record or not _is_ours(lock, record):
        # Half-written, corrupt, or somebody else's now - not provably ours.
        return False
    try:
        lock.unlink()
    except OSError:
        return False
    _OWNED.pop(key, None)
    return True
