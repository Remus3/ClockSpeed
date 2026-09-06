#!/usr/bin/env python3
"""CS-918 - the lane lock substrate: states, refusal, holder identity and ABA.

WHAT THIS GRADES. ``ops/loop/lanes.py`` decides WHO may run a headless lane. It
starts nothing, so every arm here is pure state management over a lock file in
``tmp_path``. NO ARM SPAWNS A PROCESS, SLEEPS, SHELLS OUT TO GIT OR TAKES A REAL
OS MUTEX, and that is a hard rule rather than a preference: the sibling project
this substrate is ported from shipped two arms that took the real named mutex
its driver holds, and those arms went red exactly when a lane was running - a
suite that fails because the feature is working is a suite nobody reads.

THE SEAMS, AND WHY THEY ARE MODULE ATTRIBUTES RATHER THAN PARAMETERS. The public
signatures are fixed by the specification because a driver is being written
against them, so liveness is injected by rebinding ``pid_alive`` and
``proc_started`` on the module object instead of by widening a signature. Both
have real defaults, both are named in the interface, and both are consulted
through the module namespace at call time, which is what makes the rebinding
take. The two arms that exercise the REAL implementations use only this
process's own pid and a pid the operating system cannot issue.

ASSERTIONS ARE MADE ON SCALARS BOUND FIRST, NOT ON THE EXPRESSIONS THAT PRODUCE
THEM. pytest rewrites ``assert TEST, MESSAGE`` so the sub-expressions of TEST are
rendered with their own reprs, independently of MESSAGE (CS-850,
``tests/assertion_rendering_guard.py``). Every arm here works on paths under
``tmp_path``, so an assertion written over a ``Path`` or a payload dict would
print a temporary directory into the failure report. Binding the answer to a
plain local first is what keeps the rendered frame down to a name and a verdict.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
LANES_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "lanes.py"
WINMUTEX_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "winmutex.py"

#: The one name ``ops/loop/lanes.py`` is ever bound under. A SECOND module
#: object would carry its own ``_OWNED`` table, so a re-point recorded in one
#: copy is invisible to a release called on the other and the lane could never
#: be released. That is measured in the sibling project rather than predicted
#: here, and ``tests/test_lane_launcher.py`` grades the launcher's half of it.
LANES_MODULE_NAME: Final = "clockspeed_loop_lanes"
WINMUTEX_MODULE_NAME: Final = "clockspeed_loop_winmutex"

#: The upstream files this repository FORKED FROM and DERIVED FROM, by digest.
#: Neither upstream file is edited, read at runtime or vendored - the digests
#: are recorded so the provenance stated in a header can be checked
#: mechanically instead of believed.
UPSTREAM_WINMUTEX_DIGEST: Final = "f1b4b011112685efb88616c52752657cf896fbb0993b2d2d264e7b3edde8b4f4"
UPSTREAM_SLOTS_DIGEST: Final = "5297f2d041030398a9ba240aad527b2b01a86d6e7f57a196719af8f0a91cb0a6"

#: Named locally because ruff's PLR2004 reads a bare integer in a comparison as
#: a magic value, and a name in the comparison reads better than a suppression.
ONE = 1
TWO = 2

#: A pid the operating system cannot issue, used to grade the REAL ``pid_alive``
#: and ``proc_started`` without going anywhere near a process this suite does
#: not own. Probing a pid nobody here created is how a guard ends up asserting
#: something about whatever happened to be running on the box that minute.
IMPOSSIBLE_PID = 0

#: A holder pid that is never probed for real - every arm using it rebinds the
#: liveness seams first.
OTHER_PID = 4321
LATER_PID = 5678

#: A start time, and one that is provably a different process. The gap is whole
#: seconds because the identity comparison tolerates representation drift
#: between two reads of the same process, not a real reissue.
STARTED_AT = 1_000_000.0
STARTED_ELSEWHEN = 1_000_060.0

RUN_ID = "cs918test"

#: The prose shape CLAUDE.md section 4 forbids beside the tuple that owns it.
RECITED_ROSTER_SIZE: Final = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+lanes?\b",
    re.IGNORECASE,
)


def _load(name: str, source: Path) -> ModuleType:
    """Load one of the lane modules from its file.

    ``ops/loop`` is a directory of runtime scripts rather than an importable
    package, so the module is loaded by path the same way
    ``tests/test_doc_budget.py`` loads ``tools/doc_budget.py``.

    Args:
        name: The name to register the module under.
        source: The file to load.

    Returns:
        The loaded module.

    Raises:
        ImportError: The file could not be turned into a module.
    """
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        message = f"could not load {source.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lanes = _load(LANES_MODULE_NAME, LANES_SOURCE)
winmutex = _load(WINMUTEX_MODULE_NAME, WINMUTEX_SOURCE)


def _payload(**overrides: Any) -> dict[str, Any]:
    """A lock payload carrying every field a reader consults."""
    record: dict[str, Any] = {
        "pid": os.getpid(),
        "lane": "queue",
        "run_id": RUN_ID,
        "worktree": "a-worktree",
        "ts": STARTED_AT,
        "repo": "a-repo",
        "pid_started": STARTED_AT,
    }
    record.update(overrides)
    return record


def _write_lock(root: Path, record: dict[str, Any] | None) -> Path:
    """Plant a lock file directly, bypassing the acquire path.

    Args:
        root: The lock root.
        record: The payload, or None to plant an unparseable lock.

    Returns:
        The lock path.
    """
    root.mkdir(parents=True, exist_ok=True)
    lock = root / str(lanes.LOCK_NAME)
    lock.write_bytes(b"" if record is None else json.dumps(record).encode("utf-8"))
    return lock


def _snapshot(root: Path) -> dict[str, bytes]:
    """Every file under root and its bytes - the before and after of a refusal."""
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _alive(answer: bool) -> Callable[[object], bool]:
    """A ``pid_alive`` stand-in answering the same way for every pid."""

    def probe(_pid: object) -> bool:
        return answer

    return probe


def _started(answer: float | None) -> Callable[[object], float | None]:
    """A ``proc_started`` stand-in answering the same way for every pid."""

    def probe(_pid: object) -> float | None:
        return answer

    return probe


def _acquire(root: Path, worktree: Path, run_id: str = RUN_ID) -> dict[str, Any]:
    """Claim the lane in a tmp_path root - the setup half of most arms below."""
    answer: dict[str, Any] = lanes.try_acquire_lane(
        "queue", run_id=run_id, worktree=worktree, root=root
    )
    return answer


# ===========================================================================
# a. The roster, and the count deliberately absent from the prose
# ===========================================================================


def test_the_roster_carries_the_queue_lane_and_a_single_slot() -> None:
    wired = "queue" in lanes.LANES
    assert wired, "the queue lane is the roster's reason to exist"
    assert lanes.MAX_SLOTS == ONE
    assert lanes.LOCK_NAME == "0.lock"


def test_the_module_docstring_does_not_recite_the_size_of_the_roster() -> None:
    """A count in prose beside the tuple that carries it is drift waiting.

    The sibling project's docstring said one number while the tuple two lines
    below it already carried another. CLAUDE.md section 4: a measured number is
    not restated in prose.
    """
    recited = RECITED_ROSTER_SIZE.search(lanes.__doc__ or "")
    spelled = None if recited is None else recited.group(0)
    assert spelled is None, "the roster's size is recited in prose beside the roster"


# ===========================================================================
# b. REPO_ROOT survives being imported from a worktree
# ===========================================================================


def _plant_worktree(tmp_path: Path, *, absolute: bool = True) -> tuple[Path, Path]:
    """Build a main tree and a linked worktree, the way git lays them out.

    Args:
        tmp_path: The per-test temporary directory.
        absolute: Whether the ``gitdir:`` pointer is written absolute.

    Returns:
        The main tree and the worktree.
    """
    main = tmp_path / "main-tree"
    admin = main / ".git" / "worktrees" / "wt"
    admin.mkdir(parents=True)
    worktree = tmp_path / "wt"
    worktree.mkdir()
    pointer = admin if absolute else Path(os.path.relpath(admin, worktree))
    (worktree / ".git").write_bytes(f"gitdir: {pointer}\n".encode())
    return main, worktree


def test_a_worktree_resolves_to_the_main_tree(tmp_path: Path) -> None:
    """The worktree-mandatory guard INVERTS without this, so it has its own arm.

    ``parents[2]`` alone answers the WORKTREE. The guard would then reject the
    worktree a lane legitimately runs in and accept the main tree it must never
    touch. This lane is worktree-mandatory, so the naive form is a live hole.
    """
    main, worktree = _plant_worktree(tmp_path)
    resolved = lanes._main_tree_root(worktree)  # noqa: SLF001 - the site under test
    same = resolved == main
    assert same, "a worktree did not resolve through its .git file to the main tree"


def test_a_relative_gitdir_pointer_resolves_against_the_worktree(tmp_path: Path) -> None:
    main, worktree = _plant_worktree(tmp_path, absolute=False)
    resolved = lanes._main_tree_root(worktree)  # noqa: SLF001 - the site under test
    same = resolved == main
    assert same, "a relative gitdir: pointer was not resolved against the worktree"


def test_a_main_tree_resolves_to_itself(tmp_path: Path) -> None:
    main = tmp_path / "main-tree"
    (main / ".git").mkdir(parents=True)
    resolved = lanes._main_tree_root(main)  # noqa: SLF001 - the site under test
    same = resolved == main
    assert same, "a main tree, whose .git is a directory, did not resolve to itself"


def test_a_tree_with_no_git_metadata_resolves_rather_than_raising(tmp_path: Path) -> None:
    """Total by construction - a plain export, or a temporary directory."""
    bare = tmp_path / "exported"
    bare.mkdir()
    resolved = lanes._main_tree_root(bare)  # noqa: SLF001 - the site under test
    same = resolved == bare
    assert same, "a tree with no .git at all must answer itself rather than raise"


def test_a_dot_git_file_that_is_not_a_pointer_resolves_rather_than_raising(
    tmp_path: Path,
) -> None:
    odd = tmp_path / "odd"
    odd.mkdir()
    (odd / ".git").write_bytes(b"not a gitdir pointer\n")
    resolved = lanes._main_tree_root(odd)  # noqa: SLF001 - the site under test
    same = resolved == odd
    assert same, "an unrecognised .git file must degrade to the candidate"


def test_the_module_level_repo_root_is_a_main_tree() -> None:
    """The import-time answer, graded on the property rather than the value.

    The value is a path on this machine and is never asserted literally. What is
    asserted is the property the guard depends on: whatever REPO_ROOT names, its
    ``.git`` is a DIRECTORY - which is what a main tree has and a worktree does
    not. This module is itself loaded from a worktree during lane work, so the
    arm is exercising the indirection rather than describing it.
    """
    dotgit = Path(lanes.REPO_ROOT) / ".git"
    is_main_tree = dotgit.is_dir()
    assert is_main_tree, "REPO_ROOT does not name a main tree - the worktree guard inverts"


# ===========================================================================
# c. Three states, decided by probing the pid and never by stat-ing the file
# ===========================================================================


def test_a_missing_lock_reads_free(tmp_path: Path) -> None:
    state = lanes.lane_state(tmp_path)["state"]
    assert state == lanes.FREE


def test_a_read_of_a_missing_root_does_not_create_it(tmp_path: Path) -> None:
    root = tmp_path / "lanes"
    lanes.lane_state(root)
    created = root.exists()
    assert created is False


def test_a_live_holder_reads_running(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_lock(tmp_path, _payload())
    monkeypatch.setattr(lanes, "pid_alive", _alive(True))
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_AT))
    state = lanes.lane_state(tmp_path)["state"]
    assert state == lanes.RUNNING


def test_a_dead_holder_reads_reclaimable_and_never_running(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lock whose pid is dead is indistinguishable from a live one by stat.

    Every reader that treats EXISTENCE as RUNNING reports a lane that is not
    there. The state is decided by PROBING the pid, and RECLAIMABLE must never
    render as RUNNING.
    """
    _write_lock(tmp_path, _payload())
    monkeypatch.setattr(lanes, "pid_alive", _alive(False))
    state = lanes.lane_state(tmp_path)["state"]
    assert state == lanes.RECLAIMABLE


def test_a_read_never_clears_a_reclaimable_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reads do not write. Clearing is ``try_acquire_lane``'s job alone.

    A poll path that auto-cleared would make a rendering pass mutate the control
    plane, and two pollers would then race each other into a reclaim.
    """
    _write_lock(tmp_path, _payload())
    monkeypatch.setattr(lanes, "pid_alive", _alive(False))
    before = _snapshot(tmp_path)
    lanes.lane_state(tmp_path)
    lanes.lane_state(tmp_path)
    unchanged = _snapshot(tmp_path) == before
    assert unchanged, "a read mutated the control plane"


def test_an_unreadable_lock_inside_the_write_grace_is_presumed_live(tmp_path: Path) -> None:
    """The exclusive create makes an EMPTY lock, filled a moment later.

    Inside that window an unparseable lock is presumed live, so a reader cannot
    reclaim a lane out from under an acquirer that is mid-write.
    """
    lock = _write_lock(tmp_path, None)
    now = lock.stat().st_mtime + ONE
    state = lanes.lane_state(tmp_path, now=now)["state"]
    assert state == lanes.RUNNING


def test_an_unreadable_lock_past_the_write_grace_reads_reclaimable(tmp_path: Path) -> None:
    """Past the window nothing about it can be proven alive, so it must not wedge."""
    lock = _write_lock(tmp_path, None)
    now = lock.stat().st_mtime + lanes.WRITE_GRACE_S + ONE
    state = lanes.lane_state(tmp_path, now=now)["state"]
    assert state == lanes.RECLAIMABLE


def test_the_state_carries_the_holder_it_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_lock(tmp_path, _payload(pid=OTHER_PID))
    monkeypatch.setattr(lanes, "pid_alive", _alive(True))
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_AT))
    state = lanes.lane_state(tmp_path)
    reported = (state["lane"], state["run_id"], state["pid"])
    assert reported == ("queue", RUN_ID, OTHER_PID)


# ===========================================================================
# d. (pid, start time) is the identity, and every uncertainty degrades safely
# ===========================================================================


def test_a_reissued_pid_reads_reclaimable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Alive, but provably not the process that claimed the lane.

    A pid alone does not name a process - the operating system reissues it.
    Without the second half of the identity the lane reads RUNNING behind
    whatever service inherited the number, and it reads that way forever.
    """
    _write_lock(tmp_path, _payload(pid_started=STARTED_AT))
    monkeypatch.setattr(lanes, "pid_alive", _alive(True))
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_ELSEWHEN))
    state = lanes.lane_state(tmp_path)["state"]
    assert state == lanes.RECLAIMABLE


def test_an_unreadable_start_time_is_not_proof_of_reuse(monkeypatch: pytest.MonkeyPatch) -> None:
    """None means "cannot prove reuse", never "free the lane"."""
    monkeypatch.setattr(lanes, "proc_started", _started(None))
    stranger = lanes.holder_is_a_stranger(OTHER_PID, STARTED_AT)
    assert stranger is False


def test_a_lock_with_no_recorded_start_time_is_not_proof_of_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_ELSEWHEN))
    stranger = lanes.holder_is_a_stranger(OTHER_PID, None)
    assert stranger is False


def test_an_unparseable_recorded_start_time_is_not_proof_of_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_ELSEWHEN))
    stranger = lanes.holder_is_a_stranger(OTHER_PID, "not a number")
    assert stranger is False


def test_two_reads_of_the_same_start_time_are_not_a_stranger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_AT))
    stranger = lanes.holder_is_a_stranger(OTHER_PID, STARTED_AT)
    assert stranger is False


def test_proc_started_is_total_for_a_pid_the_system_cannot_issue() -> None:
    """The REAL implementation, on inputs that reach no live process."""
    answers = [
        lanes.proc_started(IMPOSSIBLE_PID),
        lanes.proc_started(-1),
        lanes.proc_started(None),
        lanes.proc_started("not a pid"),
    ]
    all_none = all(answer is None for answer in answers)
    assert all_none, "proc_started must answer None rather than raise on a bad pid"


def test_pid_alive_answers_for_this_process_and_refuses_an_impossible_pid() -> None:
    """The REAL implementation, on this process and on a pid that cannot exist."""
    ours = lanes.pid_alive(os.getpid())
    impossible = lanes.pid_alive(IMPOSSIBLE_PID)
    verdicts = (ours, impossible)
    assert verdicts == (True, False)


# ===========================================================================
# e. Acquire: refuse, do not queue - and reclaim rather than deadlock
# ===========================================================================


def test_an_acquire_hands_back_a_token_and_records_the_holder(tmp_path: Path) -> None:
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")
    ok = answer["ok"]
    assert ok, "a free lane refused an acquire"
    record = json.loads((root / lanes.LOCK_NAME).read_text(encoding="utf-8"))
    recorded = (record["lane"], record["run_id"], record["pid"])
    assert recorded == ("queue", RUN_ID, os.getpid())


def test_an_acquire_records_the_claimers_start_time(tmp_path: Path) -> None:
    """The other half of the holder's identity, written at claim time.

    ``ts`` is when the lane was CLAIMED and is not a substitute: a worker
    legitimately starts seconds after the claim, so comparing a start time
    against ``ts`` needs a tolerance and is wrong in both directions.
    """
    root = tmp_path / "lanes"
    _acquire(root, tmp_path / "wt")
    record = json.loads((root / lanes.LOCK_NAME).read_text(encoding="utf-8"))
    recorded = record.get("pid_started")
    expected = lanes.proc_started(os.getpid())
    assert recorded == expected


def test_a_fire_against_a_live_holder_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "lanes"
    _write_lock(root, _payload(pid=OTHER_PID))
    monkeypatch.setattr(lanes, "pid_alive", _alive(True))
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_AT))
    answer = _acquire(root, tmp_path / "wt", run_id="second")
    verdict = (answer["ok"], answer["refused"], answer["holder"], answer["pid"])
    assert verdict == (False, "lane_held", "queue", OTHER_PID)


def test_a_refusal_mutates_nothing_on_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse, do not queue - and refuse without touching the filesystem.

    A queue would turn one fire into a run that starts minutes later against a
    tree that has moved on, and a refusal that rewrote the lock would destroy
    the holder record the caller is being refused in favour of.
    """
    root = tmp_path / "lanes"
    _write_lock(root, _payload(pid=OTHER_PID))
    monkeypatch.setattr(lanes, "pid_alive", _alive(True))
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_AT))
    before = _snapshot(root)
    _acquire(root, tmp_path / "wt", run_id="second")
    unchanged = _snapshot(root) == before
    assert unchanged, "a refused acquire wrote to the lock root"


def test_a_refusal_leaves_no_stray_file_in_the_lock_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The state is read BEFORE any mkdir or scratch write."""
    root = tmp_path / "lanes"
    _write_lock(root, _payload(pid=OTHER_PID))
    monkeypatch.setattr(lanes, "pid_alive", _alive(True))
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_AT))
    _acquire(root, tmp_path / "wt", run_id="second")
    stray = sorted(path.name for path in root.iterdir())
    assert stray == [lanes.LOCK_NAME]


def test_a_dead_holder_is_reclaimed_rather_than_respected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A crashed lane must never deadlock the next one."""
    root = tmp_path / "lanes"
    _write_lock(root, _payload(pid=OTHER_PID))
    monkeypatch.setattr(lanes, "pid_alive", _alive(False))
    answer = _acquire(root, tmp_path / "wt", run_id="second")
    ok = answer["ok"]
    assert ok, "a lock whose holder is provably gone was respected"
    record = json.loads((root / lanes.LOCK_NAME).read_text(encoding="utf-8"))
    reclaimed = record["run_id"]
    assert reclaimed == "second"


def test_the_exclusive_create_refuses_a_lock_that_already_exists(tmp_path: Path) -> None:
    """Exclusivity IS the mutex, and a replace could not provide it.

    The bucket is DERIVED from the sibling project's shared slot governor rather
    than copied from it, so this arm grades the derived primitive directly.
    """
    root = tmp_path / "lanes"
    _write_lock(root, _payload())
    taken = lanes._exclusive_create(root, _payload())  # noqa: SLF001 - under test
    assert taken is None


def test_the_exclusive_create_makes_the_lock_when_the_lane_is_free(tmp_path: Path) -> None:
    root = tmp_path / "lanes"
    taken = lanes._exclusive_create(root, _payload())  # noqa: SLF001 - under test
    made = taken is not None and taken.name == lanes.LOCK_NAME
    assert made, "the exclusive create did not make the lock on a free lane"


def test_an_unknown_lane_is_a_hard_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown lane"):
        lanes.try_acquire_lane("not-a-lane", run_id=RUN_ID, worktree=tmp_path / "wt", root=tmp_path)


@pytest.mark.parametrize("worktree", [None, "", "   "])
def test_an_absent_worktree_is_a_hard_error(tmp_path: Path, worktree: str | None) -> None:
    """Worktree-mandatory. An absent worktree is an error, never a default."""
    with pytest.raises(ValueError, match="worktree is mandatory"):
        lanes.try_acquire_lane("queue", run_id=RUN_ID, worktree=worktree, root=tmp_path)


def test_the_main_tree_may_never_be_a_lane_worktree(tmp_path: Path) -> None:
    """A lane rewrites files while it works.

    Pointed at the main tree it edits the checkout the operator is reading, and
    two writers in one working directory is the concurrent-index corruption
    class, which is not recoverable by retrying.
    """
    with pytest.raises(ValueError, match="main tree"):
        lanes.try_acquire_lane("queue", run_id=RUN_ID, worktree=lanes.REPO_ROOT, root=tmp_path)


# ===========================================================================
# f. Re-pointing the lock at the process that ACTUALLY runs the lane
# ===========================================================================


def test_a_repoint_moves_the_pid_and_re_records_the_start_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The claimer's start time must never be left behind.

    The claimer can be a long-lived driver whose start time is hours old, so a
    stale value here would make every re-pointed lock - which is every real lane
    fire - read as a pid reuse and free itself under a live worker. The seam is
    rebound AFTER the claim so the two values cannot coincide by accident.
    """
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")
    monkeypatch.setattr(lanes, "proc_started", _started(STARTED_ELSEWHEN))
    moved = lanes.repoint_lane_pid(answer["token"], OTHER_PID, root=root)
    assert moved is True
    record = json.loads((root / lanes.LOCK_NAME).read_text(encoding="utf-8"))
    installed = (record["pid"], record["claimed_by_pid"], record["pid_started"])
    assert installed == (OTHER_PID, os.getpid(), STARTED_ELSEWHEN)


def test_a_repoint_refuses_a_lock_another_holder_now_owns(tmp_path: Path) -> None:
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")
    _write_lock(root, _payload(run_id="somebody-else", pid=OTHER_PID))
    moved = lanes.repoint_lane_pid(answer["token"], LATER_PID, root=root)
    assert moved is False


def test_a_repoint_of_a_missing_lock_returns_false_rather_than_raising(tmp_path: Path) -> None:
    """A launcher failing to re-point must fall back to releasing the lane."""
    moved = lanes.repoint_lane_pid(str(tmp_path / "lanes" / lanes.LOCK_NAME), OTHER_PID)
    assert moved is False


@pytest.mark.parametrize("token", [None, "", "   "])
def test_a_repoint_with_no_token_returns_false(token: str | None) -> None:
    moved = lanes.repoint_lane_pid(token, OTHER_PID)
    assert moved is False


def test_a_repoint_with_an_unparseable_pid_returns_false(tmp_path: Path) -> None:
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")
    moved = lanes.repoint_lane_pid(answer["token"], "not a pid", root=root)
    assert moved is False


def test_a_repoint_retries_a_rename_that_windows_lost(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A scanner or an open handle can lose a rename on Windows.

    The precedent and its reason are the rename retry in
    ``scripts/make_cert.py``. A few short retries turn a transient sharing
    violation into a completed write; without them a re-point fails and the
    launcher kills the worker it has just started.
    """
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")
    real = Path.replace
    attempts = {"n": 0}

    def flaky(_self: Path, _target: Any) -> Path:
        attempts["n"] += 1
        if attempts["n"] <= TWO:
            message = "the file is in use by another process"
            raise PermissionError(message)
        return real(_self, _target)

    monkeypatch.setattr(lanes, "_RENAME_PAUSE_SECONDS", 0.0)
    monkeypatch.setattr(Path, "replace", flaky)
    moved = lanes.repoint_lane_pid(answer["token"], OTHER_PID, root=root)
    monkeypatch.undo()
    assert moved is True
    tried = attempts["n"]
    assert tried > TWO


def test_a_repoint_whose_rename_never_lands_returns_false_and_leaves_no_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Returns False rather than raising - a launcher must not crash mid-spawn."""
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")

    def refuse(_self: Path, _target: Any) -> Path:
        message = "the file is in use by another process"
        raise PermissionError(message)

    monkeypatch.setattr(lanes, "_RENAME_PAUSE_SECONDS", 0.0)
    monkeypatch.setattr(Path, "replace", refuse)
    moved = lanes.repoint_lane_pid(answer["token"], OTHER_PID, root=root)
    monkeypatch.undo()
    assert moved is False
    residue = sorted(path.name for path in root.iterdir())
    assert residue == [lanes.LOCK_NAME]


# ===========================================================================
# g. Release, and the ABA guard
# ===========================================================================


def test_a_release_removes_our_own_lock(tmp_path: Path) -> None:
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")
    released = lanes.release_lane(answer["token"], root=root)
    assert released is True
    gone = not (root / lanes.LOCK_NAME).exists()
    assert gone, "the lock survived its own release"


def test_a_release_is_idempotent(tmp_path: Path) -> None:
    """A release runs in a finally, and one that can throw turns one failure into two."""
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")
    lanes.release_lane(answer["token"], root=root)
    again = lanes.release_lane(answer["token"], root=root)
    assert again is False


def test_a_late_release_cannot_unlink_a_reclaimers_lock(tmp_path: Path) -> None:
    """The ABA guard, stated as the failure it prevents.

    The lane is claimed, reclaimed by somebody else, and only then does the
    first holder get around to releasing. Without the identity check that late
    release unlinks the NEW holder's lock and two workers run in one worktree.
    """
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")
    _write_lock(root, _payload(run_id="the-reclaimer", pid=OTHER_PID))
    released = lanes.release_lane(answer["token"], root=root)
    assert released is False
    survived = (root / lanes.LOCK_NAME).exists()
    assert survived, "a late release unlinked the reclaimer's lock"


def test_a_release_of_a_corrupt_lock_reports_rather_than_raising(tmp_path: Path) -> None:
    root = tmp_path / "lanes"
    answer = _acquire(root, tmp_path / "wt")
    _write_lock(root, None)
    released = lanes.release_lane(answer["token"], root=root)
    assert released is False


@pytest.mark.parametrize("token", [None, "", "   "])
def test_a_release_with_no_token_returns_false(token: str | None) -> None:
    released = lanes.release_lane(token)
    assert released is False


def test_a_lock_neither_ours_nor_recorded_is_not_released(tmp_path: Path) -> None:
    root = tmp_path / "lanes"
    lock = _write_lock(root, _payload(pid=OTHER_PID))
    released = lanes.release_lane(str(lock), root=root)
    assert released is False


# ===========================================================================
# h. The fork ruling, recorded in the bytes rather than in a note
# ===========================================================================


def _digest(path: Path) -> str:
    """The sha256 of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_the_forked_mutex_wrapper_names_the_upstream_it_forked_from() -> None:
    """A fourth copy of a byte-identical shared file is a fork, declared as one.

    The sibling projects pin their copies to one digest and coordinate through
    the protocol those bytes implement, so joining the pin would mean joining
    the protocol. This copy is FORKED, and its header carries the upstream
    digest, the deletions and the reason a byte-identical join was refused.
    """
    header = WINMUTEX_SOURCE.read_text(encoding="utf-8")
    states_fork = "FORKED" in header
    names_upstream = UPSTREAM_WINMUTEX_DIGEST in header
    assert (states_fork, names_upstream) == (True, True)


def test_the_forked_mutex_wrapper_declares_no_foreign_resource_name() -> None:
    """The upstream names two resources this project has nothing to do with.

    They are dropped rather than carried, and the check is over the module's
    ATTRIBUTES rather than its text so the header stays free to say WHICH names
    were dropped without satisfying its own arm by spelling them.
    """
    declared = sorted(name for name in dir(winmutex) if name.endswith("_MUTEX"))
    assert declared == []


def test_the_forked_copy_is_pinned_by_its_own_digest() -> None:
    """A fork that nothing pins drifts as silently as the copy it forked from.

    This is the whole price of forking: the upstream's pin no longer covers
    these bytes, so the repository states its own. An edit here is red until
    somebody updates this digest deliberately.
    """
    digest = _digest(WINMUTEX_SOURCE)
    assert digest == FORKED_WINMUTEX_DIGEST


def test_the_derived_bucket_records_the_file_it_was_derived_from() -> None:
    """``slots.py`` is DERIVED FROM, never copied.

    Copying it would enrol this project in a machine-wide token bucket that
    other trees ration between themselves, so it would consume one of THEIR
    slots - a behavioural change to another tree, made unilaterally.
    """
    source = LANES_SOURCE.read_text(encoding="utf-8")
    states_derivation = "DERIVED" in source
    names_upstream = UPSTREAM_SLOTS_DIGEST in source
    assert (states_derivation, names_upstream) == (True, True)


def test_this_project_never_joins_the_shared_machine_wide_slot_bucket() -> None:
    """The default lock root is inside this repository, not under ProgramData."""
    root = str(lanes.DEFAULT_ROOT).replace("\\", "/").lower()
    joined = "programdata" in root
    assert joined is False


#: THE DIGEST OF THIS REPOSITORY'S OWN FORKED COPY. Declared after the arms that
#: read it so the number sits beside nothing it could be mistaken for, and typed
#: by hand rather than computed - a pin derived from the file it pins is a
#: tautology that reports green through any edit.
FORKED_WINMUTEX_DIGEST: Final = "e0d3ac7d9ba0be16dbe27e95354820393b9bf4edd335c97c98b39dfafb662d3f"
