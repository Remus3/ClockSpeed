#!/usr/bin/env python3
"""CS-918 - the lane launcher: what turns a held lock into a running worker.

THE SPLIT THIS GRADES. ``ops/loop/lanes.py`` decides WHO may run and starts
nothing; ``ops/loop/lane_launcher.py`` is what actually runs. The separation is
what lets the lock be graded without spawning, and it is only worth anything if
the launcher half is graded without spawning too.

NO ARM HERE SPAWNS A PROCESS, SLEEPS, SHELLS OUT TO GIT OR TAKES A REAL OS
MUTEX - with ONE named exception. ``spawn`` is a parameter with a real default,
and every arm passes its own; the git call is a module attribute every arm
rebinds; the kill is split into a pure argv builder and the call that runs it,
so the argv can be asserted without a child. The exception is CS-1274 r3's
Windows-only arm, which starts a STUB process tree (two sleeping interpreters,
never a real worker) because the defect it grades - a kill that leaves the
wrapper's child alive - is a property of the operating system's process tree
that no argv assertion can observe. Two properties that cannot be reached by
calling anything - the DETACHED_PROCESS ban and the taskkill rule - are graded
by walking the module's own syntax tree, because the defect they describe is a
flag that is passed, and a flag that is never passed in a test is a flag no
test can see.

ASSERTIONS ARE MADE ON SCALARS BOUND FIRST. Everything here works under
``tmp_path``, and pytest renders the sub-expressions of a failing assert with
their own reprs regardless of the message (CS-850). A bound local keeps a
temporary directory out of the failure report.
"""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
LANES_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "lanes.py"
LAUNCHER_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "lane_launcher.py"
RUNNER_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "run_lane.ps1"

#: The SAME name ``tests/test_lane_lock.py`` uses. A second module object would
#: carry its own ``_OWNED`` table, and a re-point recorded in one copy would be
#: invisible to a release called on the other.
LANES_MODULE_NAME: Final = "clockspeed_loop_lanes"
LAUNCHER_MODULE_NAME: Final = "clockspeed_loop_lane_launcher"

#: Windows process creation flags, spelled here so the ban can be asserted
#: against a value this module owns rather than against the module under test
#: agreeing with itself.
CREATE_NO_WINDOW: Final = 0x08000000
DETACHED_PROCESS: Final = 0x00000008

RUN_ID = "cs918test"
WORKER_PID = 4321

#: Named locally because ruff's PLR2004 reads a bare integer in a comparison as
#: a magic value.
ZERO = 0
ONE = 1

#: How many ``raise LaneLaunchError(...)`` sites the launcher holds. Named
#: rather than inline so the structural sweep below states the population it
#: grades: a sweep that finds nothing passes for the wrong reason. CS-1274 moved
#: it: the one ``git worktree add`` site became three - an unreadable claim, a
#: worktree the kit refused, and a caller-named tree that is not a checkout.
RAISE_SITES: Final = 14

#: A full-length object id the git seam answers ``rev-parse`` with.
SHA: Final = "a" * 40

#: The last code point 7-bit ASCII covers. A .ps1 byte above it is the
#: PowerShell 5.1 ANSI-decode hazard, so this is a byte-level bound rather than
#: a style threshold.
HIGHEST_ASCII_BYTE: Final = 0x7E


def _load(name: str, source: Path) -> ModuleType:
    """Load one of the lane modules from its file.

    ``ops/loop`` is a directory of runtime scripts rather than an importable
    package, so the module is loaded by path the way ``tests/test_doc_budget.py``
    loads ``tools/doc_budget.py``.

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


# THE PACKAGE ROUTE, NOT A FILE-PATH LOAD, and that is the correction CS-918's
# first real cycle forced. Loading lanes.py by path here gave this module its own
# copy of the module object - and the launcher had another - so the arm asserting
# "the launcher binds the same lanes module this suite holds" passed while the
# DRIVER held a third. The lock was never released on a real run. A test that
# reaches its subject by a route production does not use is a test that agrees
# with itself.
from ops.loop import lane_launcher as launcher  # noqa: E402
from ops.loop import lanes, queue_loop  # noqa: E402


@dataclass
class _FakeProc:
    """What an injected spawn hands back in place of a real child."""

    pid: int | None = WORKER_PID


@dataclass
class _Spawn:
    """A spawn seam that records its arguments and starts nothing."""

    proc: _FakeProc | None = field(default_factory=_FakeProc)
    fail: bool = False
    calls: list[tuple[Path, Path, Path, Path]] = field(default_factory=list)

    def __call__(self, runner: Path, prompt: Path, cwd: Path, log: Path) -> _FakeProc | None:
        """Record the four paths a launch hands the runner, and start nothing."""
        self.calls.append((runner, prompt, cwd, log))
        if self.fail:
            message = "spawn refused"
            raise launcher.LaneLaunchError(message)
        return self.proc


@dataclass
class _GitResult:
    """The shape the kit's ``ensure_worktree`` reads back from the git seam."""

    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


@dataclass
class _Git:
    """A git seam that records argv and never starts a process.

    It stands in for EVERY git call the launcher makes, including the ones the
    kit's ``ensure_worktree`` makes through the launcher's adapter - so an arm
    can read the kit's whole conversation with git without a real repository.
    """

    returncode: int = 0
    status: str = ""
    calls: list[list[str]] = field(default_factory=list)

    def __call__(self, args: list[str], cwd: Any = None, timeout: Any = None) -> _GitResult:
        """Record the argv and answer like a repository whose base resolves."""
        del cwd, timeout
        self.calls.append(list(args))
        if "rev-parse" in args:
            return _GitResult(returncode=self.returncode, stdout=SHA + "\n")
        if "status" in args:
            return _GitResult(returncode=self.returncode, stdout=self.status)
        return _GitResult(returncode=self.returncode)


def _repo(tmp_path: Path) -> Path:
    """A stand-in repository carrying the tracked command doc a lane needs."""
    root = tmp_path / "repo"
    doc = root / launcher.LANE_COMMANDS["queue"]
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_bytes(b"# the worker prompt\n")
    return root


def _planted_tree(tmp_path: Path, name: str = "caller-named") -> Path:
    """A CALLER-NAMED checkout: a tree the claim names and the kit did not derive."""
    tree = tmp_path / "wts" / name
    tree.mkdir(parents=True, exist_ok=True)
    (tree / ".git").write_bytes(b"gitdir: planted\n")
    return tree


def _acquire(tmp_path: Path, worktree: Any = None) -> tuple[Path, dict[str, Any]]:
    """Claim the lane in a tmp_path lock root and hand back the token.

    The claim names the planted checkout unless told otherwise - since CS-1274
    the launcher runs the worker in the tree the CLAIM records, so the claim and
    the launch can no longer name two different directories.
    """
    root = tmp_path / "lock"
    tree = _planted_tree(tmp_path) if worktree is None else worktree
    answer: dict[str, Any] = lanes.try_acquire_lane(
        "queue", run_id=RUN_ID, worktree=tree, root=root
    )
    return root, answer


def _main_checkout(tmp_path: Path) -> Path:
    """A stand-in MAIN checkout, resolved, with the command doc a lane needs."""
    main = (tmp_path / "parent" / "Clockspeed").resolve()
    (main / ".git").mkdir(parents=True)
    doc = main / launcher.LANE_COMMANDS["queue"]
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_bytes(b"# the worker prompt\n")
    return main


def _held(root: Path) -> bool:
    """True while a lock file is still sitting in the lock root."""
    return (root / str(lanes.LOCK_NAME)).exists()


@pytest.fixture(autouse=True)
def _no_real_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every arm's git is a recording fake unless the arm binds its own.

    CS-1341. A launch reads its tree's HEAD through the git seam, so an arm
    that launches into a checkout would otherwise start a real git, and the
    module docstring's promise that no arm here shells out to git would be
    false. An arm that reads the calls binds its own ``_Git`` over this one.
    """
    monkeypatch.setattr(launcher, "_git", _Git())


# ===========================================================================
# a. One lanes module, not two
# ===========================================================================


def test_the_launcher_binds_the_same_lanes_module_this_suite_holds() -> None:
    """A SECOND module object is the measured defect, not a tidiness point.

    ``lanes`` carries process-global state - the ``_OWNED`` table that decides
    whether a release is ours. A file-path bind under a private name creates a
    second module with its OWN table, so a re-point recorded in one copy is
    invisible to a release called on the other and the lane can never be
    released. The launcher must reach the module already in ``sys.modules``.
    """
    shared = launcher.lanes is lanes
    assert shared, "the launcher bound a second copy of lanes.py"


def test_the_launcher_and_the_lock_agree_on_the_repository_root() -> None:
    same = launcher.REPO_ROOT == lanes.REPO_ROOT
    assert same, "two answers for the main tree is two answers for the guard"


# ===========================================================================
# b. Naming: the worktree, the branch and the command doc
# ===========================================================================


def test_a_lanes_home_worktree_is_the_kits_derivation_from_the_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1274 - the kit's ``<parent>/cs-worktrees/lane-<i>``, i the HOME index.

    Measured against the module that owns the derivation, after MOVING the
    repository root, so a base hardcoded anywhere in the launcher stays put and
    reddens this. A lane off the roster has no home and no worktree.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    homes = [
        Path(launcher.worktree_path(lane)).resolve().relative_to(main.parent).as_posix()
        for lane in lanes.LANES
    ]
    same_owner = [launcher.worktree_path(lane) == lanes.home_worktree(lane) for lane in lanes.LANES]
    with pytest.raises(ValueError, match="unknown lane"):
        launcher.worktree_path("not-a-lane")
    expected = [f"cs-worktrees/lane-{index}" for index in range(len(lanes.LANES))]
    assert (homes, same_owner) == (expected, [True] * len(lanes.LANES))


def test_the_launcher_carries_no_hardcoded_worktree_base() -> None:
    """The C: worktree base MAIN 2155's inventory named is gone, not re-spelled.

    A drive-rooted literal anywhere in the module is red - the base is DERIVED
    from the repository root by the kit, so a move of the root moves the lane
    worktrees with it and leaves nothing behind to edit. The two names that
    carried the old base are gone with it.
    """
    source = LAUNCHER_SOURCE.read_text(encoding="utf-8")
    drive_rooted = re.findall(r"\b[A-Za-z]:\\", source)
    leftovers = [
        name for name in ("DEFAULT_WORKTREE_BASE", "WORKTREE_BASE") if hasattr(launcher, name)
    ]
    assert (drive_rooted, leftovers) == ([], [])


def test_the_command_doc_is_a_tracked_path_and_not_the_gitignored_mirror() -> None:
    """A worktree is a fresh checkout and does not carry gitignored files.

    A lane pointed at the gitignored command mirror would start with an empty
    prompt - the same fresh-clone-has-no-wiring trap as the git hooks.
    """
    wired = sorted(launcher.LANE_COMMANDS.values())
    tracked = all(rel.startswith("tools/") and rel.endswith(".md") for rel in wired)
    assert tracked, "a lane is wired to something other than a tracked tools/*.md doc"


def test_every_wired_command_names_a_lane_on_the_roster() -> None:
    strays = sorted(set(launcher.LANE_COMMANDS) - set(lanes.LANES))
    assert strays == []


def test_an_unwired_lane_is_a_launch_error(tmp_path: Path) -> None:
    with pytest.raises(launcher.LaneLaunchError, match="no command doc"):
        launcher.command_path("not-a-lane", root=tmp_path)


def test_a_command_doc_missing_on_disk_is_a_launch_error(tmp_path: Path) -> None:
    """Absent, the worker would start against nothing and exit having done it."""
    with pytest.raises(launcher.LaneLaunchError, match="missing on disk"):
        launcher.command_path("queue", root=tmp_path / "empty")


def test_a_command_doc_present_on_disk_is_returned(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    found = launcher.command_path("queue", root=root).name
    assert found == "headless-queue.md"


# ===========================================================================
# c. The worktree: reused when present, refused when it is the main tree
# ===========================================================================


def test_a_caller_named_checkout_is_reused_with_one_head_read_and_no_kit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tree the CLAIM names and the kit did not derive is the caller's to keep.

    The launcher only ever MANAGES the kit's own per-index worktrees. A tree a
    caller named, already a checkout, is run in as it stands - no kit re-base
    underneath a directory somebody else chose, and no git but the one
    read-only ``rev-parse HEAD`` every launch takes its start head with
    (CS-1341).
    """
    git = _Git()
    monkeypatch.setattr(launcher, "_git", git)
    _, claim = _acquire(tmp_path)
    spawn = _Spawn()
    _launch(tmp_path, spawn, claim["token"])
    ran_in = spawn.calls[0][2].name
    asked = [(Path(args[1]).name, args[2:]) for args in git.calls]
    assert (ran_in, asked) == ("caller-named", [("caller-named", ["rev-parse", "HEAD"])])


def test_a_caller_named_tree_that_is_not_a_checkout_is_refused_and_released(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The launcher CREATES only the kit's layout; any other tree must exist.

    Refused with its own word before any spawn, and the lane is released.
    """
    monkeypatch.setattr(launcher, "_git", _Git())
    bare = tmp_path / "not-a-checkout"
    bare.mkdir()
    root, claim = _acquire(tmp_path, worktree=bare)
    spawn = _Spawn()
    with pytest.raises(launcher.LaneLaunchError) as caught:
        _launch(tmp_path, spawn, claim["token"])
    verdict = (caught.value.reason, len(spawn.calls), _held(root))
    assert verdict == (launcher.REASON_WORKTREE_MISSING, ZERO, False)


def test_the_kit_makes_a_missing_lane_worktree_detached_at_the_lane_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE KIT'S ensure_worktree, called - never a second implementation of it.

    A claim that asked for the kit's derivation is the kit's to prepare: the
    base is resolved in the main tree, and a missing worktree is added DETACHED
    at that commit. The base is ``origin/main``, so a lane never builds on - and
    never pushes - a commit the operator's own checkout has not published.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    git = _Git()
    monkeypatch.setattr(launcher, "_git", git)
    root = main / lanes.kit_lanes().LANES_REL
    claim = lanes.try_acquire_lane("queue", run_id=RUN_ID, worktree=lanes.lane_worktree, root=root)
    spawn = _Spawn()
    logs = tmp_path / "logs"
    try:
        launcher.launch_lane(
            "queue", run_id=RUN_ID, token=claim["token"], root=main, log_dir=logs, spawn=spawn
        )
    finally:
        lanes.release_lane(claim["token"], root=root)
    tree = str(lanes.lane_worktree(0))
    asked_base = ["-C", str(main), "rev-parse", "--verify", "origin/main^{commit}"] in git.calls
    added = ["-C", str(main), "worktree", "add", "--detach", tree, SHA] in git.calls
    ran_in = Path(spawn.calls[0][2]).resolve().relative_to(main.parent).as_posix()
    verdict = (launcher.LANE_BASE, asked_base, added, ran_in)
    assert verdict == ("origin/main", True, True, "cs-worktrees/lane-0")


def test_a_dirty_kit_worktree_is_refused_never_cleaned_and_released(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dirty lane worktree is a crashed run's work: the kit refuses it.

    The launcher turns the kit's refusal into its OWN word and its OWN fixed
    message - the kit's text carries the path, so it is never rendered - and
    nothing that could discard work (a checkout, a reset, a clean) is issued.
    """
    main = _main_checkout(tmp_path)
    monkeypatch.setattr(lanes, "REPO_ROOT", main)
    tree = lanes.lane_worktree(0)
    tree.mkdir(parents=True)
    linked = main / ".git" / "worktrees" / "lane-0"
    linked.mkdir(parents=True)
    (tree / ".git").write_text(f"gitdir: {linked}\n", encoding="utf-8")
    git = _Git(status=" M work-in-flight.py\n")
    monkeypatch.setattr(launcher, "_git", git)
    root = main / lanes.kit_lanes().LANES_REL
    claim = lanes.try_acquire_lane("queue", run_id=RUN_ID, worktree=lanes.lane_worktree, root=root)
    spawn = _Spawn()
    logs = tmp_path / "logs"
    with pytest.raises(launcher.LaneLaunchError) as caught:
        launcher.launch_lane(
            "queue", run_id=RUN_ID, token=claim["token"], root=main, log_dir=logs, spawn=spawn
        )
    destructive = [args for args in git.calls if {"checkout", "reset", "clean"} & set(args)]
    rendered = str(caught.value)
    leaks = str(tmp_path) in rendered or str(tree) in rendered
    verdict = (caught.value.reason, destructive, len(spawn.calls), _held(root), leaks)
    assert verdict == (launcher.REASON_WORKTREE_REFUSED, [], ZERO, False, False)


def test_a_claim_the_launcher_cannot_read_is_refused_by_its_own_word(tmp_path: Path) -> None:
    """The claim is the ONE source of the worktree; without it nothing runs.

    A token naming no readable lock cannot say where the worker belongs, so the
    launch is refused before anything is prepared or spawned.
    """
    missing = tmp_path / "lock" / "0.lock"
    spawn = _Spawn()
    with pytest.raises(launcher.LaneLaunchError) as caught:
        _launch(tmp_path, spawn, str(missing))
    verdict = (caught.value.reason, len(spawn.calls))
    assert verdict == (launcher.REASON_CLAIM_UNREADABLE, ZERO)


def test_the_main_tree_is_refused_as_a_worktree_here_too(tmp_path: Path) -> None:
    """Worktree-mandatory, enforced a SECOND time and not by accident.

    The lock checked it at a different moment, and a path can be handed in
    between the two. Two writers in one working directory is the
    concurrent-index corruption class, and it is not recoverable by retrying.
    """
    root = tmp_path / "a-checkout"
    root.mkdir()
    with pytest.raises(launcher.LaneLaunchError, match="main tree"):
        launcher._refuse_main_tree(root, root, "queue")  # noqa: SLF001 - the site under test


def test_the_repository_main_tree_is_refused_whatever_root_was_passed() -> None:
    """The guard consults the REAL main tree as well as the root it was given.

    Overriding ``root`` must not become a way to point a lane at the checkout
    the operator is reading.
    """
    with pytest.raises(launcher.LaneLaunchError, match="main tree"):
        launcher._refuse_main_tree(  # noqa: SLF001 - the site under test
            Path(lanes.REPO_ROOT), Path(lanes.REPO_ROOT).parent, "queue"
        )


# ===========================================================================
# d. Launching, and releasing the lane on every failure path
# ===========================================================================


def _launch(tmp_path: Path, spawn: _Spawn, token: Any) -> dict[str, Any]:
    """Run one launch against planted paths, with the spawn injected.

    The worktree is whatever the claim behind ``token`` recorded - see
    ``_acquire``. No base is passed: since CS-1274 the claim names the tree.
    """
    answer: dict[str, Any] = launcher.launch_lane(
        "queue",
        run_id=RUN_ID,
        token=token,
        root=_repo(tmp_path),
        log_dir=tmp_path / "logs",
        spawn=spawn,
    )
    return answer


def test_a_launch_reports_the_worker_it_started(tmp_path: Path) -> None:
    root, claim = _acquire(tmp_path)
    answer = _launch(tmp_path, _Spawn(), claim["token"])
    keys = sorted(answer)
    assert keys == [
        "lane",
        "log",
        "pid",
        "prompt",
        "run_id",
        "start_head",
        "started_at",
        "worktree",
    ]
    reported = (answer["lane"], answer["run_id"], answer["pid"])
    assert reported == ("queue", RUN_ID, WORKER_PID)
    still_held = _held(root)
    assert still_held, "a successful launch released the lane it just claimed"


def test_a_launch_runs_the_worker_in_the_worktree_and_not_the_main_tree(
    tmp_path: Path,
) -> None:
    _, claim = _acquire(tmp_path)
    spawn = _Spawn()
    _launch(tmp_path, spawn, claim["token"])
    runner, prompt, cwd, log = spawn.calls[0]
    handed = (runner.name, prompt.name, cwd.name, log.suffix)
    assert handed == ("run_lane.ps1", "headless-queue.md", "caller-named", ".log")


def test_a_launch_repoints_the_lock_at_the_worker(tmp_path: Path) -> None:
    """The pid in the lock is the WORKER's, never the claimer's.

    A driver claims the lane from a process that outlives every worker. Left
    that way, the lock's pid is always alive and the lane reads RUNNING forever
    after its worker died.
    """
    root, claim = _acquire(tmp_path)
    _launch(tmp_path, _Spawn(), claim["token"])
    holder = lanes.lane_state(root)["pid"]
    assert holder == WORKER_PID


# ===========================================================================
# CS-1341 - the start head: read in the tree the kit made, before the worker
# ===========================================================================


def _kit_made_tree(tmp_path: Path, events: list[str]) -> Any:
    """An ``ensure_worktree`` seam that MAKES its tree, the way the kit adds one.

    The tree has no ``.git`` until this seam runs, so a read taken before it
    finds no checkout to ask.
    """
    tree = tmp_path / "wts" / "kit-made"

    def ensure(_lane: str, **_kw: Any) -> Path:
        events.append("kit")
        tree.mkdir(parents=True, exist_ok=True)
        (tree / ".git").write_bytes(b"gitdir: planted\n")
        return tree

    return ensure


def test_a_launch_reads_its_start_head_between_the_kit_and_the_spawn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE ORDER IS THE FIX, so the order is what is graded - by recorded call sequence.

    The kit makes a missing tree, or moves a present one to the lane base,
    inside ``ensure_worktree``. A HEAD read before it sees no tree or the
    commit the kit is about to move away from; a read after the spawn may see
    the worker's first commit. Only a read between the two is the commit the
    worker started from. It asks the TREE's ``HEAD`` - never ``origin/main``,
    which says where work landed and not where this worker began.
    """
    events: list[str] = []
    git = _Git()

    def recording_git(args: list[str], cwd: Any = None, timeout: Any = None) -> _GitResult:
        events.append("git " + " ".join(args[2:]))
        return git(args, cwd=cwd, timeout=timeout)

    def spawn(runner: Path, prompt: Path, cwd: Path, log: Path) -> _FakeProc:
        del runner, prompt, cwd, log
        events.append("spawn")
        return _FakeProc()

    monkeypatch.setattr(launcher, "_git", recording_git)
    monkeypatch.setattr(launcher, "ensure_worktree", _kit_made_tree(tmp_path, events))
    _, claim = _acquire(tmp_path)
    answer = _launch(tmp_path, spawn, claim["token"])  # type: ignore[arg-type]
    asked_in = [Path(args[1]).name for args in git.calls if args[:1] == ["-C"]]
    verdict = (events, asked_in, answer.get("start_head"))
    assert verdict == (["kit", "git rev-parse HEAD", "spawn"], ["kit-made"], SHA)


@pytest.mark.parametrize(
    "fault",
    [
        pytest.param(_GitResult(returncode=128), id="git-refused"),
        pytest.param(_GitResult(stdout="\n"), id="git-said-nothing"),
        pytest.param(
            launcher.LaneLaunchError("git", reason=launcher.REASON_GIT_NOT_FOUND),
            id="git-not-found",
        ),
        pytest.param(subprocess.TimeoutExpired("git", 1), id="git-hung"),
        pytest.param(OSError("planted"), id="git-would-not-start"),
    ],
)
def test_a_start_head_git_cannot_give_is_none_and_the_launch_goes_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: _GitResult | BaseException
) -> None:
    """None on every failure, and NEVER a raise: the read is evidence, not a gate.

    The worker can still run in a tree whose HEAD could not be read, and the
    driver already has a fallback for a missing start. A raise here would turn
    a diagnostic read into a refused launch, released lane and all.
    """

    def failing_git(args: list[str], cwd: Any = None, timeout: Any = None) -> _GitResult:
        del args, cwd, timeout
        if isinstance(fault, BaseException):
            raise fault
        return fault

    monkeypatch.setattr(launcher, "_git", failing_git)
    monkeypatch.setattr(launcher, "ensure_worktree", _kit_made_tree(tmp_path, []))
    root, claim = _acquire(tmp_path)
    spawn = _Spawn()
    answer = _launch(tmp_path, spawn, claim["token"])
    verdict = ("start_head" in answer, answer.get("start_head"), len(spawn.calls), _held(root))
    assert verdict == (True, None, ONE, True)


def test_a_tree_with_no_git_of_its_own_is_never_asked_for_a_start_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``git -C`` in a directory that is not a checkout answers for an ENCLOSING one.

    Git searches upward for a repository, so a read in a tree with no ``.git``
    would report the HEAD of a checkout that contains it, if one does - a
    commit from a different tree, which is worse than no answer. Such a tree
    is not asked.
    """
    git = _Git()
    monkeypatch.setattr(launcher, "_git", git)
    bare = tmp_path / "wts" / "no-git"
    bare.mkdir(parents=True)
    monkeypatch.setattr(launcher, "ensure_worktree", lambda _lane, **_kw: bare)
    _, claim = _acquire(tmp_path)
    answer = _launch(tmp_path, _Spawn(), claim["token"])
    verdict = ("start_head" in answer, answer.get("start_head"), len(git.calls))
    assert verdict == (True, None, ZERO)


def _refusing_spawn(fault: BaseException) -> Any:
    """A spawn seam that refuses with ``fault`` - AFTER the start head was read."""

    def spawn(runner: Path, prompt: Path, cwd: Path, log: Path) -> _FakeProc:
        del runner, prompt, cwd, log
        raise fault

    return spawn


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        pytest.param(
            launcher.LaneLaunchError("spawn refused", reason=launcher.REASON_SPAWN_FAILED),
            launcher.REASON_SPAWN_FAILED,
            id="refused",
        ),
        pytest.param(ValueError("planted"), launcher.REASON_UNEXPECTED_FAULT, id="faulted"),
    ],
)
def test_a_refused_launch_carries_the_start_head_it_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: BaseException, reason: str
) -> None:
    """CS-1341 r2 - a refusal AFTER the kit moved the tree hands the driver its start.

    The kit has already moved the tree when the spawn refuses, so the driver's
    early read names a commit the tree no longer holds. The refusal carries the
    start head the launch read, on both refusal shapes: the launcher's own
    word, and the unexpected fault it converts into one.
    """
    monkeypatch.setattr(launcher, "ensure_worktree", _kit_made_tree(tmp_path, []))
    root, claim = _acquire(tmp_path)
    with pytest.raises(launcher.LaneLaunchError) as caught:
        _launch(tmp_path, _refusing_spawn(fault), claim["token"])
    carried = getattr(caught.value, "start_head", "absent")
    verdict = (caught.value.reason, carried, _held(root))
    assert verdict == (reason, SHA, False)


def test_a_launch_refused_before_its_read_carries_no_start_head(tmp_path: Path) -> None:
    """A refusal BEFORE the read carries None - never a stale or invented head."""
    bare = tmp_path / "not-a-checkout"
    bare.mkdir()
    root, claim = _acquire(tmp_path, worktree=bare)
    with pytest.raises(launcher.LaneLaunchError) as caught:
        _launch(tmp_path, _Spawn(), claim["token"])
    carried = getattr(caught.value, "start_head", "absent")
    verdict = (caught.value.reason, carried, _held(root))
    assert verdict == (launcher.REASON_WORKTREE_MISSING, None, False)


def test_a_spawn_that_fails_releases_the_lane(tmp_path: Path) -> None:
    """A lock with no process behind it is strictly worse than no lock at all."""
    root, claim = _acquire(tmp_path)
    with pytest.raises(launcher.LaneLaunchError):
        _launch(tmp_path, _Spawn(fail=True), claim["token"])
    released = not _held(root)
    assert released, "a failed spawn left the lane locked with nothing behind it"


def test_a_spawn_that_returns_no_pid_releases_the_lane(tmp_path: Path) -> None:
    root, claim = _acquire(tmp_path)
    with pytest.raises(launcher.LaneLaunchError, match="no pid"):
        _launch(tmp_path, _Spawn(proc=_FakeProc(pid=None)), claim["token"])
    released = not _held(root)
    assert released


def test_a_missing_command_doc_releases_the_lane(tmp_path: Path) -> None:
    root, claim = _acquire(tmp_path)
    with pytest.raises(launcher.LaneLaunchError, match="missing on disk"):
        launcher.launch_lane(
            "queue",
            run_id=RUN_ID,
            token=claim["token"],
            root=tmp_path / "empty",
            log_dir=tmp_path / "logs",
            spawn=_Spawn(),
        )
    released = not _held(root)
    assert released


def test_an_unexpected_fault_still_releases_the_lane(tmp_path: Path) -> None:
    """ANY fault must free the lane, not only the ones this module raises."""
    root, claim = _acquire(tmp_path)

    def explode(*_args: Any, **_kwargs: Any) -> None:
        message = "something nobody planned for"
        raise RuntimeError(message)

    with pytest.raises(launcher.LaneLaunchError, match="launch failed"):
        _launch(tmp_path, explode, claim["token"])  # type: ignore[arg-type]
    released = not _held(root)
    assert released


def test_a_lock_that_cannot_be_repointed_kills_the_worker_and_releases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A worker that cannot be TRACKED is worse than no worker.

    If the lock cannot be pointed at the spawned process, ``lane_state`` keeps
    probing the claimer and reports RUNNING forever. The worker is killed and
    the lane released rather than left running behind a lock nobody can read.
    """
    root, claim = _acquire(tmp_path)
    killed: list[int] = []

    def refuse(*_args: Any, **_kwargs: Any) -> bool:
        return False

    monkeypatch.setattr(launcher, "_kill", killed.append)
    monkeypatch.setattr(launcher.lanes, "repoint_lane_pid", refuse)
    with pytest.raises(launcher.LaneLaunchError, match="re-point"):
        _launch(tmp_path, _Spawn(), claim["token"])
    assert killed == [WORKER_PID]
    released = not _held(root)
    assert released


def test_cs1274_r2_an_interrupt_between_spawn_and_repoint_kills_and_releases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An INTERRUPT is not an ``Exception``, and the window is the same window.

    A ``KeyboardInterrupt`` (or ``SystemExit``) landing after the spawn and
    before the re-point used to skip both handlers: the worker kept running
    untracked behind a lock that still named the claimer. Now the worker is
    killed, the lane released, the abort recorded - and the interrupt itself
    re-raised unchanged, never converted into a launch refusal.
    """
    root, claim = _acquire(tmp_path)
    killed: list[int] = []

    def interrupted(*_args: Any, **_kwargs: Any) -> bool:
        raise KeyboardInterrupt

    monkeypatch.setattr(launcher, "_kill", killed.append)
    monkeypatch.setattr(launcher.lanes, "repoint_lane_pid", interrupted)
    with pytest.raises(KeyboardInterrupt):
        _launch(tmp_path, _Spawn(), claim["token"])
    monkeypatch.undo()
    logs = sorted((tmp_path / "logs").glob("*.log"))
    noted = bool(logs) and "reason=unexpected_fault" in logs[0].read_text(encoding="ascii")
    assert (killed, _held(root), noted) == ([WORKER_PID], False, True)


def test_cs1274_r2_a_fault_after_the_spawn_kills_the_untracked_worker_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE SIBLING: an ordinary fault in the same window, not only an interrupt.

    The catch-all released the lane and converted the fault, but left the
    worker it had just started running behind no lock - so the next claim
    handed that worktree to a second writer.
    """
    root, claim = _acquire(tmp_path)
    killed: list[int] = []

    def faulted(*_args: Any, **_kwargs: Any) -> bool:
        message = "a re-point nobody planned for"
        raise RuntimeError(message)

    monkeypatch.setattr(launcher, "_kill", killed.append)
    monkeypatch.setattr(launcher.lanes, "repoint_lane_pid", faulted)
    with pytest.raises(launcher.LaneLaunchError) as caught:
        _launch(tmp_path, _Spawn(), claim["token"])
    monkeypatch.undo()
    verdict = (killed, _held(root), caught.value.reason)
    assert verdict == ([WORKER_PID], False, launcher.REASON_UNEXPECTED_FAULT)


def test_cs1274_r2_a_tracked_worker_is_never_killed_by_the_clean_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE CONTROL: once the lock names the worker, the clean-up leaves it alone.

    A launch that succeeded kills nothing - the kill is for a worker no lock
    names, and a tracked one is the lock's to answer for.
    """
    _, claim = _acquire(tmp_path)
    killed: list[int] = []
    monkeypatch.setattr(launcher, "_kill", killed.append)
    answer = _launch(tmp_path, _Spawn(), claim["token"])
    monkeypatch.undo()
    assert (answer["pid"], killed) == (WORKER_PID, [])


def test_cs1274_r2_an_interrupt_inside_the_liveness_wait_kills_the_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other half of the window: the runner exists, ``_spawn`` has not returned it.

    No caller holds a pid yet, so ``_spawn`` itself is the only party that can
    kill what it started before the interrupt goes on up.
    """
    runner = tmp_path / "run_lane.ps1"
    runner.write_bytes(b"# a lane script\n")
    killed: list[int] = []

    class _InterruptedProc:
        pid = WORKER_PID

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            raise KeyboardInterrupt

    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *_a, **_k: _InterruptedProc())
    monkeypatch.setattr(launcher, "resolve_tool", lambda _name: "synthetic-shell")
    monkeypatch.setattr(launcher.headless_route, "child_env", lambda base, **_k: dict(base))
    monkeypatch.setattr(launcher, "_kill", killed.append)
    with pytest.raises(KeyboardInterrupt):
        launcher._spawn(runner, runner, tmp_path, tmp_path / "w.log")  # noqa: SLF001 - the seam
    monkeypatch.undo()
    assert killed == [WORKER_PID]


def test_a_log_name_carries_the_lane_and_a_sanitised_run_id(tmp_path: Path) -> None:
    """A run id reaches the filesystem, so it is filtered rather than trusted."""
    written = launcher._log_path(  # noqa: SLF001 - the site under test
        "queue", "a/b\\c:d*e", log_dir=tmp_path / "logs"
    ).name
    assert written == "lane_queue_abcde.log"


# ===========================================================================
# e. The two properties only the syntax tree can show
# ===========================================================================


def _creation_flag_arguments() -> list[str]:
    """Every expression handed to a ``creationflags=`` keyword in the launcher.

    Returns:
        One rendered expression per site, in source order.
    """
    tree = ast.parse(LAUNCHER_SOURCE.read_text(encoding="utf-8"))
    return [
        ast.unparse(keyword.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "creationflags"
    ]


def test_detached_process_is_never_passed_to_a_spawn() -> None:
    """MEASURED over three spawns of one script differing only in flags.

    With DETACHED_PROCESS a pid was issued, the return code was 0, and the log
    was NEVER WRITTEN - powershell cannot initialise its host without a console,
    so it exits immediately and silently. The lane would flip RUNNING then
    RECLAIMABLE on schedule having produced nothing, which is the worst shape a
    failure can take here. CREATE_NO_WINDOW alone already suppresses the console
    flash. This is graded on the SYNTAX because the defect is a flag that gets
    passed, and a flag no arm passes is a flag no arm can see.
    """
    passed = sorted(set(_creation_flag_arguments()))
    assert passed == ["_NO_WINDOW"]


def test_the_only_creation_flag_this_module_uses_excludes_detached_process() -> None:
    overlap = launcher._NO_WINDOW & DETACHED_PROCESS  # noqa: SLF001 - the value under test
    assert overlap == ZERO


def test_the_creation_flag_is_create_no_window_on_windows() -> None:
    flag = launcher._NO_WINDOW  # noqa: SLF001 - the value under test
    expected = CREATE_NO_WINDOW if os.name == "nt" else ZERO
    assert flag == expected


def _executable_strings(source: Path) -> list[str]:
    """Every string constant in a module that is NOT a docstring.

    A SUBSTRING SEARCH OVER A SELF-DOCUMENTING FILE IS A SEARCH OF ITS
    DOCUMENTATION. The launcher's own docstrings NAME the cmdlet they ban, so a
    plain ``in source`` check reports the ban as broken by the sentence that
    states it - and, worse, would go on passing after somebody deleted the
    prose and started using the thing. This walks what the interpreter would
    execute instead.

    Args:
        source: The module to read.

    Returns:
        One entry per executable string constant.
    """
    tree = ast.parse(source.read_text(encoding="utf-8"))
    documented = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in documented
    ]


@pytest.mark.skipif(
    sys.platform != "win32",
    reason=(
        "taskkill is a Windows binary, so _kill_argv resolves nothing on POSIX and this"
        " arm would grade its OWN skip rather than the killer. Read it as NOT RUN here,"
        " never as covered: the CS-910 rooting property below is UNMEASURED on this"
        " platform, not satisfied."
    ),
)
def test_a_kill_is_taskkill_and_never_the_powershell_cmdlet() -> None:
    """Stop-Process has hung the tooling pipe here before; taskkill has not.

    ``/T`` IS this function's business - CS-1274 r3 corrected the earlier
    reading that it was only the driver's. The pid the launcher kills is the
    PowerShell WRAPPER ``run_lane.ps1`` runs in, and ``claude`` is its child;
    without the tree flag the wrapper dies, the child keeps writing in the lane
    worktree, and the lane reads FREE behind it.
    """
    argv = launcher._kill_argv(WORKER_PID)  # noqa: SLF001 - the site under test
    # THE PROGRAM IS AN ABSOLUTE PATH, and asserting on it verbatim would pin
    # this machine's system directory into a tracked file - forbidden, and it
    # would also break on any other box. So the FLAGS are pinned exactly and the
    # program is graded on two properties instead: it is taskkill, and it is
    # rooted. That second half is the CS-910 property and it is the one that
    # matters here, because this spawn happens with the lane worktree as the
    # working directory - a bare name would be resolvable from a file the
    # worker itself wrote.
    assert argv is not None, "taskkill did not resolve on this machine"
    program, *flags = argv
    assert flags == ["/F", "/T", "/PID", str(WORKER_PID)]
    assert Path(program).name.lower().startswith("taskkill")
    assert Path(program).is_absolute(), (
        f"the killer is not rooted, so the cwd could supply it: {program!r}"
    )
    cmdlet = [text for text in _executable_strings(LAUNCHER_SOURCE) if "Stop-Process" in text]
    assert cmdlet == []


def test_cs1274_r3_the_launcher_and_the_driver_kill_with_the_same_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE TWO KILLERS ARE MIRRORS, PINNED TO AGREE - not one shared function.

    The driver's ``_taskkill`` is not reused: the launcher importing the driver
    would invert the seam (the driver consumes the launcher), and the driver's
    copy reports an unresolvable killer on its own output channel. So each
    keeps its own and this arm runs BOTH against one synthetic killer and one
    recorder, on every platform. A flag dropped from either side - the CS-1274
    r3 finding was ``/T`` missing from the launcher's - is red here.
    """
    ran: list[list[str]] = []

    def record(argv: list[str], **_kwargs: Any) -> None:
        ran.append(list(argv))

    monkeypatch.setattr(launcher, "resolve_tool", lambda _name: "synthetic-taskkill")
    monkeypatch.setattr(queue_loop, "resolve_tool", lambda _name: "synthetic-taskkill")
    monkeypatch.setattr(subprocess, "run", record)
    launcher._kill(WORKER_PID)  # noqa: SLF001 - the site under test
    queue_loop._taskkill(WORKER_PID)  # noqa: SLF001 - the mirror it must agree with
    monkeypatch.undo()
    expected = ["synthetic-taskkill", "/F", "/T", "/PID", str(WORKER_PID)]
    assert ran == [expected, expected]


#: The stand-in for ``run_lane.ps1`` starting ``claude``: a wrapper interpreter
#: that starts ONE child, records both pids atomically, then sleeps. Never a
#: real worker. Both sleeps are bounded so a leak from a red run expires alone.
_STUB_WRAPPER: Final = (
    "import os, subprocess, sys, time\n"
    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
    "out = sys.argv[1]\n"
    "with open(out + '.tmp', 'w') as handle:\n"
    "    handle.write(f'{os.getpid()} {child.pid}')\n"
    "os.replace(out + '.tmp', out)\n"
    "time.sleep(60)\n"
)

#: How long the stub gets to record its child, and how long a killed process
#: gets to read dead. Generous on purpose: a slow box must not turn a kill that
#: took into a red arm.
_STUB_DEADLINE_S: Final = 15.0
_POLL_S: Final = 0.05


def _gone(pid: int) -> bool:
    """True once ``pid`` reads dead, polled up to the stub deadline."""
    deadline = time.monotonic() + _STUB_DEADLINE_S
    while lanes.pid_alive(pid):
        if time.monotonic() > deadline:
            return False
        time.sleep(_POLL_S)
    return True


def _reap_stub_tree(pids: list[int]) -> None:
    """Best-effort clean-up of every stub pid, so a red run leaks nothing long."""
    killer = launcher.resolve_tool("taskkill")
    for pid in pids:
        if killer is not None:
            with contextlib.suppress(OSError, subprocess.SubprocessError):
                subprocess.run(
                    [killer, "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    timeout=_STUB_DEADLINE_S,
                    check=False,
                    creationflags=CREATE_NO_WINDOW,
                )


@pytest.mark.skipif(
    sys.platform != "win32",
    reason=(
        "the launcher's kill is taskkill, a Windows binary; on POSIX this arm would"
        " grade nothing. Read it as NOT RUN here, never as covered."
    ),
)
def test_cs1274_r3_an_untracked_kill_takes_the_wrappers_child_with_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The adversary's probe, as an arm: an interrupt between spawn and re-point.

    A REAL stub tree - a wrapper interpreter and its one child - stands in for
    PowerShell running ``claude``. The re-point is interrupted, so the launcher's
    clean-up kills the untracked wrapper and releases the lane. Before r3 the
    kill carried no ``/T``: the wrapper died, the child lived on, and the lane
    read FREE behind a live writer. Every kill site in the launcher reaches the
    same ``_kill``, so this one path grades the argv all four of them run.
    """
    root, claim = _acquire(tmp_path)
    record = tmp_path / "stub.pids"
    started: list[subprocess.Popen[bytes]] = []

    def spawn(runner: Path, prompt: Path, cwd: Path, log: Path) -> subprocess.Popen[bytes]:
        del runner, prompt, cwd, log
        proc = subprocess.Popen(
            [sys.executable, "-c", _STUB_WRAPPER, str(record)],
            creationflags=CREATE_NO_WINDOW,
        )
        started.append(proc)
        # The poll IS the bound: a wait on the wrapper's own handle, so a wrapper
        # that dies before recording ends the wait at once instead of idling out
        # the whole deadline, and the guard in tests/test_subprocess_timeouts.py
        # finds the Popen bounded where it was started. Timing out is the normal
        # case here - the wrapper is meant to be alive when it is handed back.
        deadline = time.monotonic() + _STUB_DEADLINE_S
        while not record.exists() and time.monotonic() < deadline:
            try:
                proc.wait(timeout=_POLL_S)
            except subprocess.TimeoutExpired:
                continue
            break
        return proc

    def interrupted(*_args: Any, **_kwargs: Any) -> bool:
        raise KeyboardInterrupt

    monkeypatch.setattr(launcher.lanes, "repoint_lane_pid", interrupted)
    stub_pids: list[int] = []
    try:
        with pytest.raises(KeyboardInterrupt):
            _launch(tmp_path, spawn, claim["token"])  # type: ignore[arg-type]
        monkeypatch.undo()
        if not record.exists():
            pytest.fail("the stub wrapper never recorded its pids")
        stub_pids = [int(word) for word in record.read_text(encoding="ascii").split()]
        wrapper_gone = _gone(stub_pids[0])
        child_gone = _gone(stub_pids[1])
    finally:
        _reap_stub_tree(stub_pids + [proc.pid for proc in started])
        for proc in started:
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=_STUB_DEADLINE_S)
    released = not _held(root)
    assert (wrapper_gone, child_gone, released) == (True, True, True)


# ===========================================================================
# f. The runner the launcher points at
# ===========================================================================


def test_the_runner_the_launcher_points_at_exists_on_disk() -> None:
    """A launcher wired to a missing runner spawns nothing, loudly or quietly."""
    present = Path(launcher.RUNNER).is_file()
    assert present, "RUNNER does not name a file"
    named = Path(launcher.RUNNER).name
    assert named == RUNNER_SOURCE.name


def test_the_runner_is_seven_bit_ascii_with_no_bom_and_lf_endings() -> None:
    """PowerShell 5.1 ANSI-decodes a BOM-less .ps1.

    A UTF-8 em-dash inside a double-quoted string then becomes a byte the
    tokenizer treats as a string terminator, and the whole script fails to
    parse. This is checked on the BYTES rather than by reading the file, because
    the fault is invisible to a reader and to a text-mode read.
    """
    raw = RUNNER_SOURCE.read_bytes()
    faults = []
    if raw.startswith(b"\xef\xbb\xbf"):
        faults.append("a UTF-8 BOM")
    if b"\r" in raw:
        faults.append("a CR byte")
    if any(byte > HIGHEST_ASCII_BYTE for byte in raw):
        faults.append("a byte above 7-bit ASCII")
    assert faults == []


def _runner_code() -> str:
    """The runner's EXECUTABLE lines, with its comment lines removed.

    The same lesson as ``_executable_strings``, and it is the one this
    repository already paid for once: a workflow guard that grepped a
    self-documenting file went green off two COMMENTS after the live flag they
    described had been deleted. Every property asserted about this runner is
    asserted about what PowerShell would run, because the runner's comments
    spell out every construct it bans.

    Returns:
        The runner's source with whole-line comments dropped.
    """
    return "\n".join(
        line
        for line in RUNNER_SOURCE.read_text(encoding="ascii").splitlines()
        if not line.lstrip().startswith("#")
    )


def test_the_runner_folds_every_stream_through_out_file_rather_than_redirecting() -> None:
    """MEASURED on a real 4298-byte lane log written the other way.

    A ``*>>`` redirection uses PowerShell 5.1's default Unicode encoding while
    an ``Out-File -Encoding utf8`` header line is UTF-8, so one file came out
    UTF-8 for its first 119 bytes and UTF-16LE for the remaining 4179 - 2066 NUL
    bytes in one log. Folding the streams into the pipeline lets Out-File set
    the encoding for all of them.
    """
    code = _runner_code()
    folds = "*>&1" in code
    assert folds, "the runner does not fold its streams into the pipeline"
    redirects = "*>>" in code or "2>>" in code
    assert redirects is False


def test_the_runner_clears_the_api_key_for_its_own_process_only() -> None:
    """MEASURED: a lane spawned correctly and died three seconds later.

    The key is set at MACHINE scope, a spawned lane inherits it, and the CLI
    prefers it over the subscription login - so the lane failed on a credit
    balance that has nothing to do with the subscription it should have used.
    Clearing it is scoped to this runner's process; the machine-wide variable is
    left alone, because other consumers on the box are none of this script's
    business.
    """
    code = _runner_code()
    cleared = "$env:ANTHROPIC_API_KEY = $null" in code
    assert cleared, "the runner does not clear the inherited API key"
    machine_scope = "SetEnvironmentVariable" in code or "[Environment]::" in code
    assert machine_scope is False


#: The prompt-on-stdin shape, matched tolerantly of quoting and of
#: ``-LiteralPath``, because the property is "read whole and piped" rather than
#: any one spelling of it.
PIPED_PROMPT: Final = re.compile(
    r"Get-Content\s+(?:-LiteralPath\s+)?\"?\$PromptFile\"?\s+-Raw\s*\|"
)


def test_the_runner_pipes_the_prompt_on_stdin() -> None:
    """No command-line quoting risk, and no length ceiling on the prompt."""
    piped = PIPED_PROMPT.search(_runner_code()) is not None
    assert piped, "the prompt is not piped to the worker on stdin"


def test_the_runner_does_not_let_native_stderr_kill_the_lane() -> None:
    tolerant = '$ErrorActionPreference = "Continue"' in _runner_code()
    assert tolerant


def test_the_runner_raises_the_background_wait_ceiling() -> None:
    """The worker's background subagents outlive the CLI's default ceiling.

    MEASURED: at the default a verifier was still re-running a suite when the
    CLI killed it, and the worker exited 0 having committed nothing.
    """
    raised = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS" in _runner_code()
    assert raised


def test_the_runner_reads_its_model_beside_itself_and_falls_back(tmp_path: Path) -> None:
    """The config is read through ``$PSScriptRoot``, never the worktree cwd.

    The runner lives in the MAIN tree while its working directory is a fresh
    checkout that does not carry a gitignored config, so reading it relative to
    the cwd would find nothing on every real fire. A fallback model is set
    first, because a lane must never fail to spawn over a config read.
    """
    del tmp_path
    code = _runner_code()
    beside_itself = "Join-Path $PSScriptRoot" in code
    assert beside_itself, "the model config is not read relative to the runner"
    falls_back = '$model = "claude-opus-5"' in code
    assert falls_back, "no known-good model is set before the config is read"


def test_the_runner_quotes_every_path_it_is_handed() -> None:
    """Every path this repository deals in can carry a space.

    An unquoted ``$Cwd`` or ``$Log`` splits on the first one and the runner
    either fails or writes somewhere nobody is reading.
    """
    unquoted = [
        line.strip()
        for line in _runner_code().splitlines()
        if ("Set-Location $Cwd" in line) or ("Out-File $Log" in line)
    ]
    assert unquoted == []


# ===========================================================================
# g. The refusal vocabulary - why a launch was refused, said in a closed word
# ===========================================================================


def _launch_error_raise_calls() -> list[ast.Call]:
    """Every ``raise LaneLaunchError(...)`` call node in the launcher.

    THE SAME TRAVERSAL IDIOM ``_creation_flag_arguments`` above uses, and
    deliberately so: a second traversal shape in one file is how two arms come
    to walk different trees. The property graded here - that a raise site NAMED
    a reason - is a keyword that is passed, and a keyword never passed in a test
    is a keyword no runtime test can see.

    Returns:
        One call node per raise site, in source order.
    """
    tree = ast.parse(LAUNCHER_SOURCE.read_text(encoding="utf-8"))
    found: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        raised = node.exc
        if not isinstance(raised, ast.Call) or not isinstance(raised.func, ast.Name):
            continue
        if raised.func.id == "LaneLaunchError":
            found.append(raised)
    return found


def _reason_keyword_values() -> list[ast.expr]:
    """The expression handed to every ``reason=`` on a launch-error raise site.

    Returns:
        One expression per site that passes the keyword, in source order.
    """
    return [
        keyword.value
        for call in _launch_error_raise_calls()
        for keyword in call.keywords
        if keyword.arg == "reason"
    ]


def test_every_launch_error_raise_site_names_a_reason() -> None:
    """A raise site that forgets its code is caught BEFORE it reaches main.

    The runtime default degrades safely to ``unspecified``, which is a real
    member of the closed set - but a launcher that refuses and cannot say why
    is the whole defect CS-970 exists to close, so the structural arm is what
    stops a new site from landing without one.

    The population is asserted NON-EMPTY and asserted to be exactly the twelve
    sites that exist, because a sweep over an empty population passes for the
    wrong reason: "every member has a reason" is vacuously true of no members.
    """
    calls = _launch_error_raise_calls()
    population = len(calls)
    assert population > ZERO, "no raise site was found - the sweep would be vacuous"
    assert population == RAISE_SITES, "the launcher's raise sites moved"
    unnamed = [
        ast.unparse(call)
        for call in calls
        if not any(keyword.arg == "reason" for keyword in call.keywords)
    ]
    assert unnamed == [], "a raise site refuses without naming a reason"
    values = _reason_keyword_values()
    not_a_constant = [ast.unparse(value) for value in values if not isinstance(value, ast.Name)]
    assert not_a_constant == [], "a reason was spelled inline instead of named"
    codes = [getattr(launcher, value.id, None) for value in values if isinstance(value, ast.Name)]
    unknown = [code for code in codes if code not in launcher.LAUNCH_REASONS]
    assert unknown == [], "a raise site names a code outside the closed vocabulary"
    distinct = len(set(codes))
    assert distinct == population, "two raise sites share one reason code"


def test_the_reason_vocabulary_is_lowercase_ascii_and_path_free() -> None:
    """Path-free BY CONSTRUCTION rather than by review.

    ``[a-z_]+`` cannot express a drive letter, a separator, a space or a digit,
    so no member of this tuple can ever carry a worktree path, an account id or
    a world name into a row an operator reads (CLAUDE.md non-negotiable 12).
    The guarantee is the character class, not anyone's care in choosing words.
    """
    vocabulary = launcher.LAUNCH_REASONS
    is_tuple = isinstance(vocabulary, tuple)
    assert is_tuple, "the vocabulary is not a tuple, so it is not closed"
    population = len(vocabulary)
    assert population > ZERO, "the vocabulary is empty"
    distinct = len(set(vocabulary))
    assert distinct == population, "the vocabulary repeats a code"
    offenders = [code for code in vocabulary if not re.fullmatch(r"[a-z_]+", str(code))]
    assert offenders == [], "a reason code is not lowercase-ascii and path-free"
    assert launcher.REASON_UNSPECIFIED in vocabulary


def test_a_lock_that_cannot_be_repointed_names_repoint_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal the C4 evidence names as the best-fit live cause.

    Same plant as ``test_a_lock_that_cannot_be_repointed_kills_the_worker_and_releases``
    above - re-authoring it would give two arms two subjects. What is new is the
    ORACLE: the code on the exception is asserted by VALUE, so an arm that only
    proved a reason was present would not pass this one.
    """
    root, claim = _acquire(tmp_path)
    killed: list[int] = []

    def refuse(*_args: Any, **_kwargs: Any) -> bool:
        return False

    monkeypatch.setattr(launcher, "_kill", killed.append)
    monkeypatch.setattr(launcher.lanes, "repoint_lane_pid", refuse)
    with pytest.raises(launcher.LaneLaunchError, match="re-point") as caught:
        _launch(tmp_path, _Spawn(), claim["token"])
    named = caught.value.reason
    assert named == launcher.REASON_REPOINT_REFUSED
    assert killed == [WORKER_PID]
    released = not _held(root)
    assert released


def test_a_raise_site_that_forgets_its_reason_degrades_to_unspecified() -> None:
    """The default is a DEFINED word, never a blank and never ``None``.

    A driver validates the code against a closed set before writing it. A blank
    default would fail that membership test and be discarded, so the row would
    say nothing at all; ``unspecified`` is a member, so the row says "the
    launcher refused and did not say why" - which is information.

    ``str(exc)`` is asserted verbatim because nine existing ``match=`` arms in
    this file and two bare constructions elsewhere depend on the rendering
    being byte-identical to what it was before the keyword existed.
    """
    message = "a message with no reason"
    exc = launcher.LaneLaunchError(message)
    named = exc.reason
    assert named == launcher.REASON_UNSPECIFIED
    assert named in launcher.LAUNCH_REASONS
    rendered = str(exc)
    assert rendered == message


# ---------------------------------------------------------------------------
# g2. CS-970 REPAIR - the fence, and the mapping the fence does not cover.
#
# The arm above walks nested functions, class bodies, except handlers and
# conditional branches, and an adversary confirmed it finds all four. What it
# could NOT see was the SHAPE of the raise: it required an `ast.Call` whose
# func is an `ast.Name`, so `exc = LaneLaunchError(...); raise exc`, an aliased
# name, `raise mod.LaneLaunchError(...)` and bare `raise LaneLaunchError` were
# all invisible to it. A probe planted eight such sites and the sweep saw four,
# and the `population == RAISE_SITES` fence did not fire either - so a
# thirteenth reasonless refusal path could land green.
#
# SEPARATELY: the arms above grade membership, distinctness and a count, and
# NOTHING binds a code to the MEANING of the site that raises it. Swapping
# REASON_GIT_NOT_FOUND onto the lane-not-wired site keeps the population at
# twelve, all members, all distinct - green. A wrong-but-valid code is worse
# than the bare type name it replaced, because the row then names a cause
# confidently and sends the operator to the wrong file.
# ---------------------------------------------------------------------------

#: Exception types the launcher may raise that are NOT launch refusals, named
#: here so the fence below can be DEFAULT-DENY. Everything not on this list and
#: not a direct `LaneLaunchError(...)` call is rejected, which is what makes the
#: via-variable, aliased, attribute-qualified and bare-class forms impossible to
#: land silently. Widening this list is a visible edit, which is the point.
NON_REFUSAL_RAISES: Final = ("ImportError",)

#: THE REVIEWED SITE-TO-CODE MAPPING, keyed by `(enclosing qualified function,
#: ordinal within that function)`.
#:
#: WHY THAT KEY. A line number rots on the next edit above it. A message string
#: rots on the next reword. A function name plus a position inside it is stable
#: across every edit that does not MOVE the site, and an edit that does move a
#: site is exactly the edit that should be re-reviewed. Swapping two codes
#: between any two sites reddens, because the key of each is unchanged while its
#: value is not.
SITE_REASONS: Final = {
    ("command_path", 0): "REASON_LANE_NOT_WIRED",
    ("command_path", 1): "REASON_COMMAND_DOC_MISSING",
    ("_git", 0): "REASON_GIT_NOT_FOUND",
    ("_refuse_main_tree", 0): "REASON_MAIN_TREE_REFUSED",
    ("claimed_worktree", 0): "REASON_CLAIM_UNREADABLE",
    ("prepare_worktree", 0): "REASON_WORKTREE_REFUSED",
    ("prepare_worktree", 1): "REASON_WORKTREE_MISSING",
    ("_spawn", 0): "REASON_RUNNER_MISSING",
    ("_spawn", 1): "REASON_SHELL_NOT_FOUND",
    ("_spawn", 2): "REASON_SPAWN_FAILED",
    ("_spawn", 3): "REASON_RUNNER_EXITED_EARLY",
    ("launch_lane", 0): "REASON_SPAWN_NO_PID",
    ("launch_lane", 1): "REASON_REPOINT_REFUSED",
    ("launch_lane", 2): "REASON_UNEXPECTED_FAULT",
}


def _raises_by_function() -> list[tuple[str, ast.Raise]]:
    """Every ``raise`` in the launcher, paired with its enclosing function.

    The qualified name is built on the way DOWN rather than looked up
    afterwards, because ``ast.walk`` discards the parent and a second pass to
    recover it is how two arms come to disagree about which function a node
    sits in. A raise at module scope gets the name ``"<module>"``, which is
    itself a site the mapping would have to declare.

    Returns:
        ``(qualified function name, raise node)`` pairs, in source order.
    """
    tree = ast.parse(LAUNCHER_SOURCE.read_text(encoding="utf-8"))
    found: list[tuple[str, ast.Raise]] = []

    def descend(node: ast.AST, qualname: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                descend(child, f"{qualname}.{child.name}" if qualname else child.name)
                continue
            if isinstance(child, ast.Raise):
                found.append((qualname or "<module>", child))
            descend(child, qualname)

    descend(tree, "")
    return found


def _refusal_sites() -> list[tuple[tuple[str, int], ast.Call]]:
    """Every launch-refusal raise site, keyed by function and ordinal.

    Returns:
        ``((function, ordinal), call node)`` pairs, in source order.
    """
    seen: dict[str, int] = {}
    sites: list[tuple[tuple[str, int], ast.Call]] = []
    for qualname, node in _raises_by_function():
        raised = node.exc
        if not isinstance(raised, ast.Call) or not isinstance(raised.func, ast.Name):
            continue
        if raised.func.id != "LaneLaunchError":
            continue
        ordinal = seen.get(qualname, 0)
        seen[qualname] = ordinal + 1
        sites.append(((qualname, ordinal), raised))
    return sites


def test_no_launch_refusal_can_hide_behind_an_ungraded_raise_shape() -> None:
    """DEFAULT-DENY over raise SHAPES, not an allowlist of the ones we thought of.

    The reason arm above can only grade a site it can SEE, and it sees only
    ``raise LaneLaunchError(...)`` spelled directly. This arm closes the gap
    from the other side: every ``raise`` in the launcher must be a shape the
    reason arm can grade, a bare re-raise, or a declared non-refusal type.
    Anything else - a variable, an attribute, an alias, a bare class - is a
    refusal path that could carry no reason and never be counted.
    """
    ungraded: list[str] = []
    for qualname, node in _raises_by_function():
        raised = node.exc
        if raised is None:
            continue  # a bare re-raise carries the original exception whole
        if (
            isinstance(raised, ast.Call)
            and isinstance(raised.func, ast.Name)
            and (raised.func.id == "LaneLaunchError" or raised.func.id in NON_REFUSAL_RAISES)
        ):
            continue
        ungraded.append(f"{qualname}: raise {ast.unparse(raised)}")
    assert ungraded == [], (
        "a raise shape the reason sweep cannot see - a refusal could land here "
        "carrying no reason code and never be counted"
    )


def test_every_raise_site_keeps_the_reason_code_it_was_reviewed_with() -> None:
    """THE MAPPING, pinned - membership and distinctness do not imply CORRECTNESS.

    Twelve distinct members can be twelve WRONG members. A code that names the
    wrong cause is worse than no code at all, because the operator acts on it.
    Only one of the twelve mappings had a value oracle before this arm; this
    pins the other eleven against the reading they were reviewed under.
    """
    sites = _refusal_sites()
    assert sites, "no refusal site was found - the sweep would be vacuous"
    actual: dict[tuple[str, int], str] = {}
    for key, call in sites:
        named = [kw.value for kw in call.keywords if kw.arg == "reason"]
        assert len(named) == 1, f"{key} does not pass exactly one reason"
        value = named[0]
        assert isinstance(value, ast.Name), f"{key} spells its reason inline"
        actual[key] = value.id
    assert actual == SITE_REASONS, (
        "a raise site no longer carries the reason code it was reviewed with; "
        "re-read the site and update SITE_REASONS deliberately"
    )


# ===========================================================================
# g. The one death a finally cannot cover
# ===========================================================================


@dataclass
class _HeaderSpawn:
    """A spawn that leaves the log a REAL runner leaves after its header.

    The point of the fake. ``_Spawn`` writes nothing, so an arm built on it
    cannot tell "the launcher appended a line" from "the launcher created the
    whole file", and the defect being graded is specifically a log that ALREADY
    HAS A HEADER and stops there.
    """

    header: bytes = b"lane start 2026-01-01T00:00:00 cwd=planted model=planted\n"
    proc: _FakeProc = field(default_factory=_FakeProc)

    def __call__(self, runner: Path, prompt: Path, cwd: Path, log: Path) -> _FakeProc:
        """Write the header the runner writes, and start nothing."""
        del runner, prompt, cwd
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_bytes(self.header)
        return self.proc


def _tail(log: Path) -> str:
    """The log's last non-empty line, decoded tolerantly of Out-File's BOM.

    Args:
        log: The log file.

    Returns:
        The last non-empty line, or an empty string.
    """
    if not log.is_file():
        return ""
    text = log.read_bytes().decode("utf-8-sig", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def test_a_worker_the_launcher_kills_leaves_a_terminal_line_in_its_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE DEFECT, MEASURED. Thirteen cycles left a 134-byte log.

    ``taskkill /F`` is TerminateProcess: no ``finally`` in the runner unwinds,
    so the process the launcher kills can never write its own exit line. Whoever
    fires the kill is therefore the only party that CAN write one, and a log
    that stops at its header is indistinguishable from a worker still running -
    which is what made every failing cycle on both recorded nights unreadable.
    """
    _, claim = _acquire(tmp_path)

    def refuse(*_args: Any, **_kwargs: Any) -> bool:
        return False

    monkeypatch.setattr(launcher, "_kill", lambda _pid: None)
    monkeypatch.setattr(launcher.lanes, "repoint_lane_pid", refuse)
    spawn = _HeaderSpawn()
    with pytest.raises(launcher.LaneLaunchError):
        _launch(tmp_path, spawn, claim["token"])  # type: ignore[arg-type]

    log = tmp_path / "logs" / f"lane_queue_{RUN_ID}.log"
    ended = _tail(log)
    assert ended.startswith("lane abort "), f"the log stops without a terminal line: {ended!r}"
    named = "repoint_refused" in ended
    assert named, f"the terminal line does not name what refused: {ended!r}"


def test_an_abort_note_is_appended_and_never_replaces_the_runners_own_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A note that TRUNCATED the log would destroy the diagnosis it exists for.

    The control for the arm above: "the last line names the refusal" is also
    what a writer that opened the file for truncation would produce, and that
    writer would throw away everything the worker had already said.
    """
    _, claim = _acquire(tmp_path)

    def refuse(*_args: Any, **_kwargs: Any) -> bool:
        return False

    monkeypatch.setattr(launcher, "_kill", lambda _pid: None)
    monkeypatch.setattr(launcher.lanes, "repoint_lane_pid", refuse)
    spawn = _HeaderSpawn()
    with pytest.raises(launcher.LaneLaunchError):
        _launch(tmp_path, spawn, claim["token"])  # type: ignore[arg-type]

    log = tmp_path / "logs" / f"lane_queue_{RUN_ID}.log"
    kept = spawn.header.decode("ascii").strip() in log.read_bytes().decode("utf-8-sig")
    assert kept, "the abort note overwrote the header the runner had already written"


def test_an_abort_note_writes_only_reason_words_the_launcher_itself_holds(
    tmp_path: Path,
) -> None:
    """THE SUBSTITUTION IS THE MECHANISM, not the validation.

    The same rule ``queue_loop._launch_fault`` obeys one seam over, and for the
    same reason: this line lands in a durable file an operator reads, so the
    word written is a literal THIS module holds, looked up by index, never the
    caller's object. A word the launcher does not hold degrades to
    ``unspecified`` rather than reaching the file.
    """
    log = tmp_path / "note.log"
    # A PATH-SHAPED WORD, assembled rather than written. The literal form of
    # this string is what `tests/test_scaffold.py` and
    # `tests/test_assertion_rendering.py` both forbid in an authored file:
    # pytest renders a failing assertion's sub-expressions itself, so a home
    # path spelled here reaches a failure report whatever the message says
    # (CLAUDE.md non-negotiables 3 and 12). What the arm needs is only that
    # the word carry separators and a drive letter - the characters the
    # `[a-z_]+` vocabulary cannot express.
    intruder = "Q:" + chr(92) + "somewhere" + chr(92) + "secret"
    launcher.note_worker_abort(log, intruder)
    written = _tail(log)
    degraded = launcher.REASON_UNSPECIFIED in written
    assert degraded, f"an unknown word was not degraded: {written!r}"
    leaked = "somewhere" in written or "secret" in written or "Q:" in written
    assert leaked is False, "the caller's string reached the log"


def test_an_abort_note_creates_a_log_the_runner_never_got_far_enough_to_write(
    tmp_path: Path,
) -> None:
    """A runner killed before its own header leaves NO file, not a short one.

    The launcher cannot assume the runner reached anything, so the note is the
    whole record in that case rather than an append to one.
    """
    log = tmp_path / "never" / "made.log"
    launcher.note_worker_abort(log, launcher.REASON_RUNNER_EXITED_EARLY)
    made = log.is_file()
    assert made, "no log was written for a runner that never wrote one"
    written = _tail(log)
    named = launcher.REASON_RUNNER_EXITED_EARLY in written
    assert named, f"the note does not name the reason: {written!r}"


def test_an_abort_note_that_cannot_be_written_is_swallowed(tmp_path: Path) -> None:
    """A note is DIAGNOSIS. It must never become the failure it was describing.

    This runs on the refusal path, after the lane is released and while a real
    ``LaneLaunchError`` is propagating. A raise here would replace the launch
    refusal an operator needs with an unrelated OSError about a log file.
    """
    directory = tmp_path / "a-directory"
    directory.mkdir()
    launcher.note_worker_abort(directory, launcher.REASON_SPAWN_FAILED)


def test_an_abort_note_with_no_log_at_all_is_a_no_op() -> None:
    """A launch can refuse BEFORE it has decided where the log goes.

    ``command_path`` and ``prepare_worktree`` both run ahead of ``_log_path``, so
    the refusal handler is reached with no log path at all and must not invent
    one.
    """
    launcher.note_worker_abort(None, launcher.REASON_COMMAND_DOC_MISSING)
