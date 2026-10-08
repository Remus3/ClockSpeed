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
ruling, which came out the other way and is a declared FORK. CS-1274 imports
the kit's LANE module, ``ops/fleet_kit/fleet_lanes.py``, for its lane model
only: nothing here takes a governor slot, and that bucket stays untouched.

THE KIT'S LANE MODEL, CS-1274. The vendored kit (v9) owns three facts this
module now defers to rather than restates: the lane CAP, validated by
``fleet_lanes.lane_cap`` against the kit's own ceiling; the lock LAYOUT, an
``<i>.lock`` per index under ``ops/loop/control/lanes`` with the lane NAME a
payload field and never a file name; and the WORKTREE an index runs in,
``fleet_lanes.worktree_path``, DERIVED from the main tree so that no base path
is written anywhere in this repository. Locks written here are on-disk
compatible with the kit's: its lane widget reads them, its acquirer and this
one serialise on its one acquire mutex, and a lane either of them claims is
visible to both. The cap is ``LANE_CAP`` and is DECOUPLED from the roster (MAIN
2237 section 4a) - the roster says which lanes exist, the cap how many hold a
slot at once.

A HOME INDEX FIRST, THEN ANY INDEX. A lane is tried first at its roster
position, its HOME, so in the ordinary case it keeps one worktree across
cycles and the driver's before-and-after HEAD reads look at the tree its
worker used. When the home slot is held - by another lane, or by a claim the
kit's own acquirer made under a name this roster does not carry - the lane
takes the lowest free index instead, which is the kit's rule that any roster
lane runs at any index. A full bucket refuses with the kit's own word. THE
SHARED-SLOT SHAPE STAYS THE DEFECT THIS REPLACED: a guard taken per lane over
ONE shared lock file is worse than either half by itself, because the guards
wave every lane through while the file quietly serialises them. A lane off the
roster gets no slot at all rather than a default one.

THE RECORDED LANE IS AUTHORITATIVE, THE SLOT INDEX IS NOT. That was measured
rather than imagined: inserting a lane at the FRONT of a positional roster
re-pointed every slot under it, so a reader looking at the wrong file reported
FREE over a live worker and the next claim double-booked its worktree. TWO
THINGS ANSWER IT, and neither is enough alone:

  * ``tests/test_lane_lock.py`` PINS THE ROSTER'S ORDER by literal equality,
    because the order decides each lane's home. A pin is a tripwire.
  * ``lock_for_lane`` resolves a lane to the lock that NAMES it, wherever in the
    bucket it sits, and prefers a live holder over a stale record of the same
    name - so neither a re-pointed home nor a crashed fallback claim can hide a
    live holder from anybody who edited past the pin.

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

THE PRIMITIVES ARE A PUBLIC SEAM, NOT A PRIVATE CONVENIENCE. ``pid_alive``,
``proc_started``, ``holder_is_a_stranger``, ``path_key``, ``read_payload``,
``exclusive_create``, ``require_worktree``, ``remove_quietly`` and the three
coercers are public because ``ops/loop/claims.py`` holds the SAME mutex shape
over a different subject - a `ROADMAP.md` row rather than a lane - and answers
the same FREE / held / RECLAIMABLE question by the same probe. A second copy of
any of them there would be a second place for the answer to go subtly wrong, and
a caller reaching past a leading underscore for the one predicate both must
agree on is exactly the shape ``holder_is_a_stranger``'s own note calls out
upstream. WHAT IS NOT SHARED IS THE NAMING: this module places a lane at a slot
derived from the roster, the claim store keys a row by its id, and those two
derivations are deliberately separate because a claim keyed by position would
re-point every record the moment a row above it closed.

NOTHING HERE STARTS A PROCESS. This module is pure state management: it decides
who may run, it does not run anything, and it is therefore testable without
spawning. ``pid`` in the payload is the pid of whatever CLAIMED the lane;
``ops/loop/lane_launcher.py`` re-points it at the worker it spawns, keeping the
claimer as ``holder_pid`` so the lane stays held until the claimer releases it
(CS-1274 r2), and it is the launcher that hands the claimed worktree to the kit
to prepare.

A RELEASE IS THE KIT'S RELEASE (CS-1274 r2): retried, then neutralised in place
when the operating system still refuses the unlink - see ``release_lane``.
"""

from __future__ import annotations

import contextlib
import functools
import importlib
import importlib.util
import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent

#: The kit module's canonical dotted name, and the private name a file-path load
#: registers it under when no ``ops`` package is importable - the detached
#: driver is started as ``pythonw <repo>/ops/loop/queue_loop.py`` and carries no
#: repository root on ``sys.path`` (CS-1000). HYPHENATED, and the spelling is
#: load-bearing: ``tests/ops/test_lane_refusal_contract.py`` reads every
#: snake-case literal in this file as a possible refusal word, so a private name
#: spelled in snake case would be a stray word that contract cannot vouch for.
_KIT_LANES_DOTTED = "ops.fleet_kit.fleet_lanes"
_KIT_LANES_PRIVATE = "cs-kit-fleet-lanes"
#: The vendored file, as ONE relative spelling for the same reason.
_KIT_LANES_FILE = "fleet_kit/fleet_lanes.py"


def _load_kit_lanes() -> Any:
    """Bind the vendored ``fleet_lanes`` - the package route first, the file second.

    The kit module is READ, never edited (FLEET item 11), and it holds no
    process-global state of its own, so the two-copies hazard ``_OWNED`` carries
    here cannot arise in it. A file-path load is published under the dotted name
    all the same - ``setdefault``, never an assignment - so every later importer
    gets the one object.

    Returns:
        The kit's lane module.

    Raises:
        ImportError: The vendored file could not be turned into a module.
        OSError: The vendored file is not on disk.
    """
    with contextlib.suppress(ImportError):
        return importlib.import_module(_KIT_LANES_DOTTED)
    existing = sys.modules.get(_KIT_LANES_PRIVATE)
    if existing is not None:
        return existing
    source = _HERE.parent / _KIT_LANES_FILE
    spec = importlib.util.spec_from_file_location(_KIT_LANES_PRIVATE, source)
    if spec is None or spec.loader is None:
        message = "could not load the vendored fleet_lanes module"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_KIT_LANES_PRIVATE] = module
    spec.loader.exec_module(module)
    sys.modules.setdefault(_KIT_LANES_DOTTED, module)
    return module


@functools.cache
def kit_lanes() -> Any:
    """The vendored kit's lane module, bound on FIRST USE (FLEET item 11 - called, never edited).

    LAZY, and that is the same ruling ``ops/loop/queue_loop.py`` makes for its
    own binds: importing a module to read lane STATE must not require the rest
    of the lane on disk. ``ops/loop/claims.py`` imports this file from inside a
    worker's own checkout to answer exactly that question, and reading a lock
    needs nothing from the kit. Placing a claim and deriving a worktree do, and
    both reach the kit through here - so a checkout without the kit can READ
    lanes and cannot CLAIM one, which fails loudly rather than quietly placing
    a claim no kit acquirer serialises against.

    VALIDATES THE CAP on the way in: the kit's ``lane_cap`` is the one place the
    1..LANE_CAP_MAX bound is written, and a cap it would change is refused.

    Returns:
        The kit's lane module.

    Raises:
        ImportError: The vendored module could not be bound.
        OSError: The vendored file is not on disk.
        ValueError: ``LANE_CAP`` is outside the kit's bound.
    """
    module = _load_kit_lanes()
    if module.lane_cap(LANE_CAP) != LANE_CAP:
        message = f"lane cap {LANE_CAP} is not one the kit accepts as given"
        raise ValueError(message)
    return module


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

#: The roster. Its size is not written anywhere but here. CS-1274 widened it to
#: the kit's cap: a lane NAME is exclusive, so a roster narrower than the cap
#: could never fill the cap with this tree's own lanes.
LANES = ("queue", "queue-b", "queue-c")

#: The kit repo code this tree's lane worktrees are named by -
#: ``<parent of the main tree>/cs-worktrees/lane-<i>``. Alphanumeric, as
#: ``fleet_lanes.worktree_path`` requires.
LANE_CODE = "CS"

#: CS-1274 - THE WIDTH IS THE KIT'S LANE CAP, NOT THE ROSTER'S LENGTH (MAIN 2237
#: section 4a). The value is the kit's ceiling and the cap MAIN 2237 section 3
#: item 2 sets for every tree without a measured reason for less; this tree has
#: none recorded. Validated against the kit's own ``lane_cap`` the first time
#: the kit is bound - see ``kit_lanes`` - so the bound is written in one place.
LANE_CAP = 3
MAX_SLOTS: int = LANE_CAP

#: How long an acquire waits on the kit's per-repo acquire mutex before it
#: refuses. Scan, reclaim and create run under THAT mutex - the kit's own, by
#: the kit's own name - so a kit acquirer and this one can never both take one
#: index, and, now that a lane may land at any index, two acquirers of one lane
#: NAME can never land at two. The kit's default wait; a module attribute so an
#: arm can make the refusal immediate.
ACQUIRE_WAIT_S = 5.0

#: Where a lane is POINTED AT A SUBJECT. ``CLOCKSPEED_LANE_SCOPE_QUEUE=dashboard``
#: narrows the queue lane to the scope of that name in ``config/lane_scopes.json``
#: - see ``ops/loop/scope.py`` for what a scope is and how it is validated.
#:
#: AN ENVIRONMENT VARIABLE RATHER THAN A TRACKED BINDING, deliberately. Pointing
#: a lane at a subject is an operator act for one run, and writing it into a
#: tracked file would make the DEFAULT queue silently narrower for every clone
#: and every later session - a lane that has quietly stopped reading most of
#: `ROADMAP.md` is exactly the failure the loud refusal in ``scope.py`` exists to
#: prevent, wearing a different hat. So the declaration of what a scope CONTAINS
#: is tracked and reviewable, and the decision to APPLY one is not.
LANE_SCOPE_ENV_PREFIX = "CLOCKSPEED_LANE_SCOPE_"

#: Lane name -> the scope it runs under when nothing points it elsewhere. EMPTY,
#: and that is the whole point: a lane with no entry here keeps reading the whole
#: of `ROADMAP.md` exactly as `tools/headless-queue.md` section 5 has always
#: said, and scoping is opt-in per run. A lane gains an entry here only when the
#: operator decides that lane's DEFAULT subject is narrower than the file.
DEFAULT_LANE_SCOPES: dict[str, str] = {}


def slot_index(lane: Any) -> int:
    """A lane's position on the roster - its HOME index - and the roster check.

    A ROSTER MEMBER IS NOT A DEFAULT. An unrecognised lane raises rather than
    answering slot 0: a typo handed the first lane's own lock would claim a
    running worker's slot, and a caller that cannot spell its lane has no
    business holding anything.

    Args:
        lane: The lane to place.

    Returns:
        Its roster position.

    Raises:
        ValueError: The lane is not on the roster.
    """
    try:
        return LANES.index(str(lane))
    except ValueError:
        message = f"unknown lane {lane!r} - valid lanes are {', '.join(LANES)}"
        raise ValueError(message) from None


def home_index(lane: Any) -> int | None:
    """The index a lane is tried at first, or None when it has no home under the cap.

    A roster wider than the cap leaves its later lanes without a home; they
    take whichever index is free, which is the kit's any-index rule and needs
    no home at all.

    Args:
        lane: The lane.

    Returns:
        Its home index, or None.

    Raises:
        ValueError: The lane is not on the roster.
    """
    position = slot_index(lane)
    return position if position < MAX_SLOTS else None


def lane_worktree(index: Any) -> Path:
    """The worktree lane index ``index`` runs in - the KIT'S derivation, never a base.

    ``fleet_lanes.worktree_path`` builds ``<parent>/cs-worktrees/lane-<i>``
    from the MAIN tree, so moving the repository moves every lane worktree with
    it and no path is written down anywhere. Read at call time, so a caller
    that names a different main tree gets that tree's layout.

    This is also the DERIVATION ``try_acquire_lane`` accepts in place of a
    path: a lane does not know its index until the claim chooses one.

    Args:
        index: A lane index inside the cap.

    Returns:
        The worktree path for that index.

    Raises:
        ValueError: The index is not an integer inside the cap.
    """
    number = None if isinstance(index, bool) else int_or_none(index)
    if number is None or not 0 <= number < MAX_SLOTS:
        message = f"lane index {index!r} outside 0..{MAX_SLOTS - 1}"
        raise ValueError(message)
    return Path(kit_lanes().worktree_path(REPO_ROOT, LANE_CODE, number))


def home_worktree(lane: Any) -> Path:
    """The worktree a lane runs in when it holds its HOME index.

    Args:
        lane: The lane.

    Returns:
        The home index's worktree.

    Raises:
        ValueError: The lane is not on the roster, or has no home under the cap.
    """
    home = home_index(lane)
    if home is None:
        message = f"lane {lane!r} has no home index under the cap of {MAX_SLOTS}"
        raise ValueError(message)
    return lane_worktree(home)


def lock_name(lane: Any) -> str:
    """The lock file at a lane's HOME index. The kit names index i ``<i>.lock``.

    ONE FILE PER INDEX IS THE WHOLE MUTEX. A per-lane guard layered over a
    SHARED slot file is worse than either half alone: the guards wave both
    lanes through while the file serialises them, so each lane believes it
    holds something the other also believes it holds. This is where a claim is
    TRIED first; where a lane actually holds its lock is ``lock_for_lane``'s
    answer.

    Args:
        lane: The lane.

    Returns:
        The home lock's file name.

    Raises:
        ValueError: The lane is not on the roster.
    """
    return f"{slot_index(lane)}.lock"


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

#: CS-1274 r2 - THE KIT'S RELEASE RETRY, MIRRORED: ``fleet_lanes.RETRIES``
#: unlinks, ``fleet_lanes.RETRY_SLEEP`` apart, before a lock is NEUTRALISED in
#: place. Windows refuses to unlink a file another process holds open - the
#: kit's lane widget, another lane's scan, a scanner - and the refuted CS-1274 first cut
#: tried once, so the lock kept naming the live driver and every later claim of
#: the lane was refused until that driver exited. Written here rather than read
#: off the kit because a release runs in a ``finally`` and must never raise,
#: binding the kit can; ``tests/test_lane_lock.py`` pins both equal to the kit's.
_RELEASE_ATTEMPTS = 12
_RELEASE_PAUSE_SECONDS = 0.025

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


def scope_for_lane(lane: Any, env: dict[str, str] | None = None) -> str | None:
    """The scope name this lane is pointed at, or None for the whole file.

    Reads ``CLOCKSPEED_LANE_SCOPE_<LANE>`` first and falls back to
    ``DEFAULT_LANE_SCOPES``. The lane name is upper-cased into the variable
    name, so the ``queue`` lane reads ``CLOCKSPEED_LANE_SCOPE_QUEUE``.

    A BLANK VALUE MEANS UNSCOPED, NOT A SCOPE NAMED "". Exporting the variable
    empty is how a shell unsets a pointer in practice, and treating that as a
    scope name would refuse every run under it for a reason nobody would guess.

    THIS DOES NOT VALIDATE THE NAME. Whether a scope exists, and whether its
    members are still takeable, is ``ops/loop/scope.py``'s job and it refuses
    loudly. Resolving the pointer and grading it are deliberately separate: a
    pointer this function could not resolve would otherwise be indistinguishable
    from a scope whose rows have all closed.

    Args:
        lane: The lane name.
        env: The environment to read, or None for the live process environment.

    Returns:
        The scope name, or None.
    """
    name = str(lane).strip()
    if not name:
        return None
    source = os.environ if env is None else env
    pointed = str(source.get(LANE_SCOPE_ENV_PREFIX + name.upper(), "")).strip()
    if pointed:
        return pointed
    return DEFAULT_LANE_SCOPES.get(name)


def path_key(path: Any) -> str:
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


#: ONE DEFINITION, TWO NAMES, and the second one is on its way out.
#: ``ops/loop/lane_launcher.py`` reads ``lanes._key`` behind an ``SLF001``
#: suppression, written when this was private. The rename made it public rather
#: than adding a second spelling of the same normalisation - two normalisers is
#: how two modules stop agreeing about whether one directory is another - and
#: this alias exists only so that caller keeps working until it is next edited.
_key = path_key


def int_or_none(value: Any) -> int | None:
    """The value as an int, or None when it is not one."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def float_or_none(value: Any) -> float | None:
    """The value as a float, or None when it is not one."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def str_or_none(value: Any) -> str | None:
    """The value as a string, or None when it is absent."""
    return None if value is None else str(value)


def remove_quietly(path: Path) -> None:
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
    number = int_or_none(pid)
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
    number = int_or_none(pid)
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
    expected = float_or_none(recorded)
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


def _lock_files(root: Any) -> list[Path]:
    """Every lock file sitting in one root, sorted. Reads nothing else.

    Total by construction: a root that does not exist, or cannot be listed,
    answers an empty list rather than raising on the poll path.

    Args:
        root: The lock root.

    Returns:
        The lock files present.
    """
    try:
        return sorted(p for p in Path(root).iterdir() if p.suffix == ".lock" and p.is_file())
    except OSError:
        return []


def _index_lock(directory: Path, index: int) -> Path:
    """The lock file at one index - the kit's ``<i>.lock``."""
    return directory / f"{index}.lock"


def _holding_lock(directory: Path, wanted: str) -> Path | None:
    """The lock that NAMES this lane, a live one first, or None when none does.

    THE RECORDED LANE IS AUTHORITATIVE, THE SLOT INDEX IS NOT. Every lock in the
    root is read, wherever it sits, so a lane placed off its home - or a lock an
    older build wrote at a slot the current roster would not derive - is still
    found by its name.

    A LIVE HOLDER WINS OVER A STALE RECORD OF THE SAME NAME. A lane that crashed
    at a fallback index leaves a RECLAIMABLE lock naming it there, and its next
    claim lands at its home: two locks then name one lane, and a reader that
    took the first in file order would report the dead one over the live worker.

    THE ONE UNNAMED LOCK IT ATTRIBUTES is at the lane's own home slot: a lock
    with no readable payload names nobody, so it is left to whichever lane's
    home it occupies - the write-grace window in ``lane_state`` is the answer
    to it - rather than claimed by the first reader that stumbles on it.

    Args:
        directory: The lock root.
        wanted: The lane, already checked against the roster.

    Returns:
        The lock holding the lane, or None.
    """
    named = [
        candidate
        for candidate in _lock_files(directory)
        if str_or_none(read_payload(candidate).get("lane")) == wanted
    ]
    live = [candidate for candidate in named if _reading(candidate, None)["state"] == RUNNING]
    if live or named:
        return (live or named)[0]
    home = _index_lock(directory, slot_index(wanted))
    if home.exists() and str_or_none(read_payload(home).get("lane")) is None:
        return home
    return None


def _free_index(directory: Path, lane: Any) -> int | None:
    """The index a new claim for this lane takes: its home if free, else the lowest free.

    FREE or RECLAIMABLE both count - a reclaimable lock is cleared by the claim
    that chooses it, and only then. READS ONLY, so the refusal it lets a caller
    make before taking the mutex touches nothing.

    Args:
        directory: The lock root.
        lane: The lane, already checked against the roster.

    Returns:
        The chosen index, or None when every index inside the cap is held.
    """
    home = home_index(lane)
    order = list(range(MAX_SLOTS))
    if home is not None:
        order.remove(home)
        order.insert(0, home)
    for index in order:
        lock = _index_lock(directory, index)
        if not lock.exists() or _reading(lock, None)["state"] != RUNNING:
            return index
    return None


def _holders(directory: Path) -> list[str | None]:
    """The lane named by every RUNNING lock inside the cap - who a full bucket waits on."""
    found: list[str | None] = []
    for index in range(MAX_SLOTS):
        lock = _index_lock(directory, index)
        if lock.exists():
            reading = _reading(lock, None)
            if reading["state"] == RUNNING:
                found.append(reading["lane"])
    return found


def lock_for_lane(root: Any = None, lane: Any = None) -> Path:
    """The lock that HOLDS this lane, or the slot a new claim would be written to.

    The holding lock is resolved by NAME - see ``_holding_lock``. When nothing
    names the lane the answer is where a claim would go now: the home slot if
    free, else the lowest free index, and the home slot when the bucket is full
    and nothing is free to name. Readers asking "is this lane running" should
    ask ``lane_state``, which does not rely on this fallback path.

    Args:
        root: The lock root, or None for the default.
        lane: The lane, or None for ``DEFAULT_LANE``.

    Returns:
        The lock holding the lane, or the slot it would be claimed in.

    Raises:
        ValueError: The lane is not on the roster.
    """
    wanted = str(DEFAULT_LANE if lane is None else lane)
    home = lock_path(root, wanted)
    directory = _resolve_root(root)
    held = _holding_lock(directory, wanted)
    if held is not None:
        return held
    index = _free_index(directory, wanted)
    return home if index is None else _index_lock(directory, index)


def read_payload(lock: Path) -> dict[str, Any]:
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
    wanted = str(DEFAULT_LANE if lane is None else lane)
    slot_index(wanted)  # ROSTER CHECK, raising the one message for an unknown lane
    lock = _holding_lock(_resolve_root(root), wanted)
    return _reading(lock, now)


def _reading(lock: Path | None, now: Any) -> dict[str, Any]:
    """FREE, RUNNING or RECLAIMABLE for ONE lock file. NEVER mutates anything.

    The per-file half of ``lane_state``, so placement can weigh an index by the
    same rule a reader weighs a lane by - two rules would be two answers.

    KIT-COMPATIBLE ON A RE-POINTED CLAIM. The kit's ``repoint_lane_pid`` keeps
    the CLAIMER alive as ``holder_pid`` beside the worker's ``pid``, and so,
    since CS-1274 r2, does this module's - and the kit reads such a lock
    RUNNING while either lives. This reads it the same way, or a claim whose
    worker had exited would read RECLAIMABLE here and be reclaimed from under
    the claimer still finishing behind it.

    Args:
        lock: The lock file, or None for no lock at all.
        now: The wall clock reading to age the lock against, or None.

    Returns:
        The state, the holder it read, and the lock's age in seconds.
    """
    reading = time.time() if now is None else float(now)
    if lock is None or not lock.exists():
        return {
            "state": FREE,
            "lane": None,
            "pid": None,
            "run_id": None,
            "worktree": None,
            "age_s": None,
        }

    record = read_payload(lock)
    stamp = float_or_none(record.get("ts"))
    if stamp is None:
        try:
            stamp = lock.stat().st_mtime
        except OSError:
            stamp = None
    pid = int_or_none(record.get("pid"))
    answer: dict[str, Any] = {
        "state": RUNNING,
        "lane": str_or_none(record.get("lane")),
        "pid": pid,
        "run_id": str_or_none(record.get("run_id")),
        "worktree": str_or_none(record.get("worktree")),
        "age_s": None if stamp is None else max(0.0, reading - stamp),
    }
    if pid is None:
        # No readable holder at all - see WRITE_GRACE_S.
        if answer["age_s"] is not None and answer["age_s"] > WRITE_GRACE_S:
            answer["state"] = RECLAIMABLE
    elif not _is_live(pid, record.get("pid_started")) and not _is_live(
        int_or_none(record.get("holder_pid")), record.get("holder_started")
    ):
        # Dead, or alive but not the same process: the holder died and the
        # operating system reissued its pid. Without the second half the lane
        # reads RUNNING forever.
        answer["state"] = RECLAIMABLE
    return answer


def _is_live(pid: int | None, started: Any) -> bool:
    """True when ``pid`` is alive AND is provably-or-plausibly the recorded process."""
    return pid is not None and pid_alive(pid) and not holder_is_a_stranger(pid, started)


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


def require_worktree(worktree: Any) -> Path:
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
    if path_key(path) == path_key(REPO_ROOT):
        message = "worktree is mandatory - a lane may never run against the main tree"
        raise ValueError(message)
    return path


def exclusive_create(target: Any, payload: dict[str, Any]) -> Path | None:
    """Create one file exclusively and fill it, or answer None.

    ``O_CREAT|O_EXCL`` rather than the tmp-plus-replace this module uses for
    every other write: EXCLUSIVITY IS THE MUTEX, and a replace cannot be
    exclusive. DERIVED from the sibling projects' shared bucket - see the module
    docstring on why it is not imported.

    TAKES THE TARGET PATH RATHER THAN DERIVING IT. ``ops/loop/claims.py`` runs
    the same mutex over a different file naming, and a second copy of this
    function there would be a second place for the exclusivity to get subtly
    wrong - the exact divergence the module docstring refuses elsewhere.

    Args:
        target: The file to create.
        payload: The holder record to write into it.

    Returns:
        The path, or None when the file already existed or could not be filled.
    """
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        return None
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream)
    except OSError:
        remove_quietly(path)
        return None
    return path


def _exclusive_create(root: Any, lane: Any, payload: dict[str, Any]) -> Path | None:
    """The lane-shaped entry to :func:`exclusive_create`, which does the work.

    Args:
        root: The lock root.
        lane: The lane claiming, which decides WHICH slot is created.
        payload: The holder record to write into the lock.

    Returns:
        The lock path, or None when the lane was already taken.
    """
    return exclusive_create(Path(root) / lock_name(lane), payload)


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
        remove_quietly(scratch)
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
    remove_quietly(scratch)
    return False


def _reclaim(lock: Path) -> bool:
    """Clear ONE index's lock whose holder is provably gone. Never touches a live one.

    The bytes judged are the bytes deleted: the file is re-read after the
    verdict and left alone if it changed in between - the kit's own rule for
    every delete it makes. Called only under the acquire mutex, by the claim
    that chose this index. The unlink is the kit's RETRIED one (CS-1274 r2): a
    single attempt turned a crashed lane's lock that a reader held open for a
    moment into a ``lane_held`` refusal naming a lane nobody runs.

    Args:
        lock: The lock at the chosen index.

    Returns:
        True when the index is free afterwards.
    """
    judged = _bytes_or_none(lock)
    if judged is None:
        return not lock.exists()
    if _reading(lock, None)["state"] != RECLAIMABLE or _bytes_or_none(lock) != judged:
        return False
    return _unlink_judged(lock, judged)


def _bytes_or_none(path: Path) -> bytes | None:
    """A file's bytes, or None when it is missing or cannot be read."""
    try:
        return path.read_bytes()
    except OSError:
        return None


def _decoded(raw: bytes) -> dict[str, Any]:
    """The JSON object in ``raw``, or {} when it is empty, half-written or not an object."""
    if not raw.strip():
        return {}
    try:
        record = json.loads(raw.decode("utf-8"))
    except ValueError:
        return {}
    return record if isinstance(record, dict) else {}


def _unlink_judged(lock: Path, judged: bytes) -> bool:
    """Unlink ``lock`` while its bytes are still ``judged`` - the kit's ``_unlink_if_raw``.

    MIRRORED, NOT CALLED: ``fleet_lanes._unlink_if_raw`` is private to the kit
    and the vendored file is never edited (FLEET item 11). The same shape: up to
    ``_RELEASE_ATTEMPTS`` tries ``_RELEASE_PAUSE_SECONDS`` apart, each re-reading
    the bytes first, so a lock somebody rewrote between the verdict and the
    unlink is LEFT ALONE - the ABA guard holds on every attempt, not only the
    first. Never raises.

    Args:
        lock: The lock file.
        judged: The bytes the caller judged ours, or reclaimable.

    Returns:
        True when the lock is gone.
    """
    for attempt in range(_RELEASE_ATTEMPTS):
        now = _bytes_or_none(lock)
        if now is None:
            return not lock.exists()
        if now != judged:
            return False
        try:
            lock.unlink()
        except FileNotFoundError:
            return True
        except OSError:
            if attempt + 1 < _RELEASE_ATTEMPTS and _RELEASE_PAUSE_SECONDS:
                time.sleep(_RELEASE_PAUSE_SECONDS)
            continue
        return True
    return False


def _neutralise(lock: Path, judged: bytes, record: dict[str, Any]) -> bool:
    """Make an undeletable lock of OURS read RECLAIMABLE at once - the kit's neutralise.

    ``fleet_lanes._release``'s fallback, mirrored: re-check the bytes are still
    the ones judged ours, then write the same record back with ``pid`` 0 and
    ``ts`` 0 and ``orphaned`` set, so the next claim - the kit's or this
    module's - reclaims it the moment the handle closes. The lane name and run
    id stay, so a reader still sees whose it was.

    ONE FIELD FURTHER THAN THE KIT, deliberately: ``holder_pid`` is zeroed too.
    A re-pointed lock names its claimer there (see ``repoint_lane_pid``), and the
    claimer is the very process releasing - alive. Zeroing ``pid`` alone would
    leave the lane RUNNING behind it until it exited, which is the wedge this
    exists to remove. The kit's own neutralise has that gap for a
    ``keep_claimer`` claim, and it is reported upstream rather than edited here.

    IN PLACE, NOT tmp-plus-replace, as the kit does it and for the reason this
    runs at all: a replace onto a file another process holds open is refused by
    Windows exactly as the unlink was. A reader catching it mid-write sees an
    unparseable lock, which the write-grace window already answers. Never raises.

    Args:
        lock: The lock file.
        judged: The bytes the release judged ours.
        record: Those bytes, decoded.

    Returns:
        True when the neutralised record was written.
    """
    if _bytes_or_none(lock) != judged:
        return False
    # A copy and then field by field, never a ``**`` unpack or a ``dict()`` call:
    # the refusal-word contract in tests/ops/test_lane_refusal_contract.py cannot
    # read past either, and it fails closed on what it cannot read.
    orphan = record.copy()
    orphan["pid"] = 0
    orphan["ts"] = 0.0
    orphan["orphaned"] = True
    if orphan.get("holder_pid") is not None:
        orphan["holder_pid"] = 0
    try:
        with lock.open("w", encoding="ascii") as stream:
            json.dump(orphan, stream)
    except (OSError, ValueError):
        return False
    return True


def same_tree(left: Any, right: Any) -> bool:
    """Whether two spellings name one directory.

    RESOLVED ON BOTH SIDES BEFORE COMPARING. Windows hands out 8.3 short
    components - a path under a long account name is the common source - and
    :func:`path_key` normalises case and separators but does NOT expand them, so
    two spellings of one directory would compare unequal. Public because
    ``ops/loop/claims.py`` asks the same question about the same worktrees, and
    a second copy of a path comparison is a second place for it to go subtly
    wrong.

    Args:
        left: One path.
        right: The other.

    Returns:
        True when both name one directory.
    """
    try:
        return path_key(Path(str(left)).resolve()) == path_key(Path(str(right)).resolve())
    except OSError:
        return False


def _refusal(state: dict[str, Any]) -> dict[str, Any]:
    """The answer a genuinely held lane gets. Writes nothing, by construction."""
    return {"ok": False, "refused": "lane_held", "holder": state["lane"], "pid": state["pid"]}


def _worktree_refusal(state: dict[str, Any]) -> dict[str, Any]:
    """The answer a lane pointed at somebody else's tree gets. Writes nothing.

    ITS OWN REASON STRING, not ``lane_held``. The two faults need different
    operator actions - one waits, the other repoints a lane - and a driver log
    that showed the same word for both would send whoever reads it looking at
    the wrong lane.
    """
    return {
        "ok": False,
        "refused": "worktree_in_use",
        "holder": state["lane"],
        "pid": state["pid"],
        "worktree": state["worktree"],
    }


def _worktree_occupant(root: Path, lane: Any, target: Path) -> dict[str, Any] | None:
    """The OTHER lane running in this worktree, if any.

    TWO LANES IN ONE TREE IS A CROSS-LANE DELETION, measured rather than
    theorised. ``ops/loop/claims.py`` derives WHICH LANE a releasing process
    belongs to by matching its checkout against the worktree these locks record.
    With two live locks naming one tree that derivation is ambiguous, and an
    adversary measured the consequence: one lane deleted the other's LIVE claim
    record while naming nothing but the public row id, and the lane that lost
    the tie could never release its own records at all.

    ``claims.py`` now refuses to guess when it sees this state, which turns the
    deletion into a leak. This stops the state being reached in the first place,
    and the two are not redundant: a lock written by an older build is already
    on disk and never passes through here.

    Args:
        root: The lock root.
        lane: The lane asking, which is not its own occupant.
        target: The worktree it wants.

    Returns:
        The occupying lane's reading, or None when the tree is free.
    """
    for other in LANES:
        if other == str(lane):
            continue
        reading = lane_state(root, None, other)
        if reading["state"] != RUNNING:
            continue
        recorded = str_or_none(reading.get("worktree"))
        if recorded is not None and same_tree(recorded, target):
            return reading
    return None


def _full_refusal(directory: Path) -> dict[str, Any]:
    """The answer a lane gets when every index inside the cap is held. Writes nothing.

    THE KIT'S OWN WORD, and its own reason string rather than ``lane_held``:
    that one names a HOLDER of this lane, and a full bucket has none - it
    names the lanes it is waiting on instead.
    """
    return {
        "ok": False,
        "refused": "lanes_full",
        "holder": None,
        "pid": None,
        "holders": _holders(directory),
    }


def _busy_refusal() -> dict[str, Any]:
    """The answer a lane gets when another acquirer holds the kit's acquire mutex.

    Transient, and its own word: a scan and a create are a few milliseconds
    under the mutex, so a refusal here means a holder is wedged or mid-claim,
    not that a lane is running.
    """
    return {"ok": False, "refused": "acquire_busy", "holder": None, "pid": None}


def try_acquire_lane(lane: str, *, run_id: Any, worktree: Any, root: Any = None) -> dict[str, Any]:
    """Claim a lane lock at the lane's home index or any free one, or refuse.

    A holder whose pid is dead is reclaimed rather than respected: a crashed
    lane must never deadlock the next fire. A holder that is genuinely live is
    refused, and the refusal touches nothing on disk - the state is read BEFORE
    any mkdir or scratch write for exactly that reason, and again under the
    kit's acquire mutex before anything is written.

    A WORKTREE ANOTHER LIVE LANE RECORDS IS REFUSED TOO, and for a reason that
    belongs to a different module - see :func:`_worktree_occupant`. Two lanes in
    one tree was measured to let one delete the other's live row claim.

    THE WORKTREE IS A PATH OR THE KIT'S DERIVATION. A path is recorded as given.
    ``lane_worktree`` - or any callable taking the claimed index - is the
    kit's per-index tree, resolved only once the index is chosen, which is the
    only moment it can be: under the any-index rule a lane does not know where
    it will land until it has landed.

    Args:
        lane: The lane to claim. Must be in ``LANES``.
        run_id: The caller's identifier for this run.
        worktree: The working directory the lane will run in, or a callable
            deriving it from the claimed index. Mandatory either way.
        root: The lock root, or None for the default.

    Returns:
        ``{"ok": True, "lane", "run_id", "worktree", "token", "index"}`` on
        success - ``token`` is the lock path and is what ``release_lane`` wants
        back - or a refusal: ``lane_held`` when this lane is running,
        ``worktree_in_use`` when another live lane is already in that tree,
        ``lanes_full`` when every index is held, ``acquire_busy`` when the
        acquire mutex is. Every refusal is a normal answer rather than an error.

    Raises:
        ValueError: The lane is unknown, or the worktree is absent or the main
            tree.
    """
    slot_index(lane)  # ROSTER CHECK, raising the one message for an unknown lane
    explicit, resolve = _resolver(worktree)
    directory = _resolve_root(root)

    # READ-ONLY PASS FIRST, so the refusals a held lane, an occupied tree and a
    # full bucket get touch nothing on disk - not even the mutex file.
    early = _refusal_before_writing(directory, lane, explicit)
    if early is not None:
        return early
    kit = kit_lanes()
    try:
        # SLF001: the KIT'S acquire mutex, deliberately - see ACQUIRE_WAIT_S. A
        # mutex of this module's own would serialise nothing against the kit.
        with kit._acquire_mutex(directory, wait=ACQUIRE_WAIT_S):  # noqa: SLF001
            return _claim_under_mutex(directory, lane, run_id, explicit, resolve)
    except kit.LaneRefused:
        return _busy_refusal()


def _resolver(worktree: Any) -> tuple[Path | None, Callable[[int], Path]]:
    """The named worktree (or None) and the function that answers it for an index.

    Args:
        worktree: A path, or a callable deriving one from the claimed index.

    Returns:
        ``(explicit, resolve)``: the checked path when one was named, and the
        resolver a claim calls once it has chosen its index.

    Raises:
        ValueError: A named worktree is absent or the main tree.
    """
    if callable(worktree):
        return None, functools.partial(_derived_tree, worktree)
    fixed = require_worktree(worktree)
    return fixed, functools.partial(_fixed_tree, fixed)


def _derived_tree(derive: Callable[[int], Any], index: int) -> Path:
    """A derived worktree, held to the same main-tree guard as a named one."""
    return require_worktree(derive(index))


def _fixed_tree(fixed: Path, _index: int) -> Path:
    """A named worktree, the same whichever index the claim lands on."""
    return fixed


def _refusal_before_writing(
    directory: Path, lane: str, explicit: Path | None
) -> dict[str, Any] | None:
    """The refusal this claim gets on the state as read, or None. Reads only.

    Args:
        directory: The lock root.
        lane: The lane asking.
        explicit: The worktree it named, or None when it asked for a derivation.

    Returns:
        A refusal, or None when a claim may proceed.
    """
    state = lane_state(directory, None, lane)
    if state["state"] == RUNNING:
        return _refusal(state)
    if explicit is not None:
        occupant = _worktree_occupant(directory, lane, explicit)
        if occupant is not None:
            return _worktree_refusal(occupant)
    if _free_index(directory, lane) is None:
        return _full_refusal(directory)
    return None


def _claim_under_mutex(
    directory: Path,
    lane: str,
    run_id: Any,
    explicit: Path | None,
    resolve: Callable[[int], Path],
) -> dict[str, Any]:
    """Re-read, choose an index, reclaim it if stale, and write the claim.

    Everything is re-decided here because the read-only pass above ran before
    the mutex was held. Only this function writes, and only under the mutex.

    Args:
        directory: The lock root.
        lane: The lane claiming.
        run_id: The caller's identifier for this run.
        explicit: The worktree it named, or None when it asked for a derivation.
        resolve: Answers the worktree for the chosen index.

    Returns:
        The claim, or a refusal.
    """
    early = _refusal_before_writing(directory, lane, explicit)
    if early is not None:
        return early
    index = _free_index(directory, lane)
    if index is None:
        return _full_refusal(directory)
    target = resolve(index)
    occupant = _worktree_occupant(directory, lane, target)
    if occupant is not None:
        return _worktree_refusal(occupant)
    lock = _index_lock(directory, index)
    if lock.exists() and not _reclaim(lock):
        return _refusal(lane_state(directory, None, lane))

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
        # The kit's payload field, so its lane widget and this module agree on
        # which index a claim holds without parsing a file name.
        "index": index,
    }
    token = exclusive_create(lock, payload)
    if token is None:
        # Lost a race the mutex should have made impossible - an acquirer that
        # does not take it. Refused as held, never forced.
        return _refusal(lane_state(directory, None, lane))
    _OWNED[path_key(token)] = (payload["run_id"], payload["ts"], payload["pid"])
    return {
        "ok": True,
        "lane": lane,
        "run_id": payload["run_id"],
        "worktree": payload["worktree"],
        "token": str(token),
        "index": index,
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
        str_or_none(record.get("run_id")),
        float_or_none(record.get("ts")),
        int_or_none(record.get("pid")),
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
    owned = _OWNED.get(path_key(lock))
    identity = _identity(record)
    if owned is not None:
        return identity == owned
    return identity[2] == os.getpid()


def repoint_lane_pid(token: Any, pid: Any, root: Any = None) -> bool:
    """Re-point a held lock at the process that ACTUALLY runs the lane.

    ``try_acquire_lane`` records the pid of whatever CLAIMED the lane. The
    launcher re-points the lock the moment it has a worker pid, so a reader
    probes the process doing the work - and a driver that dies with its worker
    still up leaves a lock that stays RUNNING exactly as long as that worker.

    THE CLAIMER STAYS THE HOLDER - CS-1274 r2, the kit's ``keep_claimer``,
    which the kit FORCES for a claim whose claimer releases it. The claimer is
    recorded as ``holder_pid`` (with its start time as ``holder_started``) and
    the lock reads RUNNING while EITHER lives. The driver is still finishing
    the cycle after its worker exits - it ends ``progress/lane-<i>.json`` and
    then releases - and the refuted CS-1274 first cut, which wrote no holder, read
    RECLAIMABLE in that window: another lane took the index while this one's
    progress file was still being finished. The lane is no longer "free the
    instant the worker dies"; it is free when the claimer releases it, or when
    worker and claimer are both gone. A SECOND re-point keeps the original
    claimer as the holder - the holder is whoever releases.

    The claimer's start time is REPLACED as ``pid_started`` rather than left
    behind. A driver's start time can be hours old, so a stale value there
    would make every re-pointed lock read as a pid reuse of its WORKER.

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
    record = read_payload(lock)
    worker = int_or_none(pid)
    if not record or worker is None or not _is_ours(lock, record):
        return False

    key = path_key(lock)
    owned = _OWNED.get(key)
    run_id, stamp, claimer = _identity(record)
    if int_or_none(record.get("holder_pid")) is None:
        # The FIRST re-point: the claimer becomes the holder, as the kit does it.
        record["holder_pid"] = claimer
        record["holder_started"] = record.get("pid_started")
        record["claimed_by_pid"] = claimer
    record["pid"] = worker
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

    THE KIT'S RELEASE SEMANTICS - CS-1274 r2. The unlink is RETRIED
    (``_unlink_judged``), and a lock of ours that still cannot be removed is
    NEUTRALISED in place (``_neutralise``) so it reads RECLAIMABLE and the next
    claim takes it the moment the other handle closes. That answers False - the
    file is still there - but the lane is free. The refuted CS-1274 first cut unlinked
    once and returned, leaving a lock that named the live driver.

    Args:
        token: What ``try_acquire_lane`` handed back.
        root: The lock root, used only when the token is a bare name.

    Returns:
        True when this call removed the lock.
    """
    lock = _lock_for(token, root)
    if lock is None:
        return False
    key = path_key(lock)
    judged = _bytes_or_none(lock)
    if judged is None:
        if not lock.exists():
            _OWNED.pop(key, None)
        return False
    record = _decoded(judged)
    if not record or not _is_ours(lock, record):
        # Half-written, corrupt, or somebody else's now - not provably ours.
        return False
    if _unlink_judged(lock, judged):
        _OWNED.pop(key, None)
        return True
    if _neutralise(lock, judged, record):
        # No longer ours on disk - pid 0 is nobody's identity.
        _OWNED.pop(key, None)
    return False
