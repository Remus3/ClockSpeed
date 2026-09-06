#!/usr/bin/env python3
"""CS-918 - the lane launcher: what turns a held lock into a running worker.

THE SPLIT THIS GRADES. ``ops/loop/lanes.py`` decides WHO may run and starts
nothing; ``ops/loop/lane_launcher.py`` is what actually runs. The separation is
what lets the lock be graded without spawning, and it is only worth anything if
the launcher half is graded without spawning too.

NO ARM HERE SPAWNS A PROCESS, SLEEPS, SHELLS OUT TO GIT OR TAKES A REAL OS
MUTEX. ``spawn`` is a parameter with a real default, and every arm passes its
own; the git call is a module attribute every arm rebinds; the kill is split
into a pure argv builder and the call that runs it, so the argv can be asserted
without a child. Two properties that cannot be reached by calling anything - the
DETACHED_PROCESS ban and the taskkill rule - are graded by walking the module's
own syntax tree, because the defect they describe is a flag that is passed, and
a flag that is never passed in a test is a flag no test can see.

ASSERTIONS ARE MADE ON SCALARS BOUND FIRST. Everything here works under
``tmp_path``, and pytest renders the sub-expressions of a failing assert with
their own reprs regardless of the message (CS-850). A bound local keeps a
temporary directory out of the failure report.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import sys
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
from ops.loop import lanes  # noqa: E402


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
    """The shape ``ensure_worktree`` reads back from the git seam."""

    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


@dataclass
class _Git:
    """A git seam that records argv and never starts a process."""

    make: Path | None = None
    returncode: int = 0
    calls: list[list[str]] = field(default_factory=list)

    def __call__(self, args: list[str], cwd: Any = None, timeout: Any = None) -> _GitResult:
        """Record the argv, optionally plant the worktree, and answer."""
        del cwd, timeout
        self.calls.append(list(args))
        if self.make is not None and "add" in args:
            (self.make / ".git").parent.mkdir(parents=True, exist_ok=True)
            (self.make / ".git").write_bytes(b"gitdir: planted\n")
        return _GitResult(returncode=self.returncode)


def _repo(tmp_path: Path) -> Path:
    """A stand-in repository carrying the tracked command doc a lane needs."""
    root = tmp_path / "repo"
    doc = root / launcher.LANE_COMMANDS["queue"]
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_bytes(b"# the worker prompt\n")
    return root


def _acquire(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Claim the lane in a tmp_path lock root and hand back the token."""
    root = tmp_path / "lock"
    answer: dict[str, Any] = lanes.try_acquire_lane(
        "queue", run_id=RUN_ID, worktree=tmp_path / "wt", root=root
    )
    return root, answer


def _held(root: Path) -> bool:
    """True while a lock file is still sitting in the lock root."""
    return (root / str(lanes.LOCK_NAME)).exists()


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


def test_the_worktree_is_named_for_the_lane(tmp_path: Path) -> None:
    named = launcher.worktree_path("queue", tmp_path).name
    assert named == "cs-lane-queue"


def test_the_branch_is_stable_across_fires() -> None:
    """One branch per lane, so a lane resumes its own history.

    A branch per fire would sprout a branch and a directory on every launch.
    """
    branch = launcher.branch_name("queue")
    assert branch == "lane/queue"


def test_the_default_worktree_base_is_outside_the_repository_and_any_home() -> None:
    """Worktrees live OUTSIDE the repository, and never under a user profile.

    Inside the repository they would land in the very tree the lane is forbidden
    to touch, and every repository-wide guard would then scan them. Under a home
    directory they would be an absolute personal path in a tracked file, which
    CLAUDE.md non-negotiable 3 forbids outright.
    """
    default = str(launcher.DEFAULT_WORKTREE_BASE).replace("/", "\\").lower()
    under_home = "\\users\\" in default or default.startswith("~")
    inside_repo = default.startswith(str(REPO_ROOT).lower())
    assert (under_home, inside_repo) == (False, False)


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


def test_an_existing_worktree_is_reused_without_calling_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reuse is deliberate - a worktree per fire leaves a directory behind."""
    base = tmp_path / "wts"
    (base / "cs-lane-queue").mkdir(parents=True)
    (base / "cs-lane-queue" / ".git").write_bytes(b"gitdir: already here\n")
    git = _Git()
    monkeypatch.setattr(launcher, "_git", git)
    found = launcher.ensure_worktree("queue", base=base, root=_repo(tmp_path))
    reused = found.name == "cs-lane-queue"
    assert reused
    called = len(git.calls)
    assert called == ZERO


def test_a_missing_worktree_is_created_on_the_lanes_own_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "wts"
    git = _Git(make=base / "cs-lane-queue")
    monkeypatch.setattr(launcher, "_git", git)
    launcher.ensure_worktree("queue", base=base, root=_repo(tmp_path))
    added = [args for args in git.calls if args[:2] == ["worktree", "add"]]
    made_one = len(added) == ONE
    assert made_one, "a missing worktree was not created exactly once"
    on_branch = "lane/queue" in added[0]
    assert on_branch, "the worktree was not put on the lane's own branch"


def test_a_worktree_git_could_not_create_is_a_launch_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(launcher, "_git", _Git(returncode=ONE))
    with pytest.raises(launcher.LaneLaunchError, match="worktree add"):
        launcher.ensure_worktree("queue", base=tmp_path / "wts", root=_repo(tmp_path))


def test_the_main_tree_is_refused_as_a_worktree_here_too(tmp_path: Path) -> None:
    """Worktree-mandatory, enforced a SECOND time and not by accident.

    The lock checked it at a different moment, and a path can be handed in
    between the two. Two writers in one working directory is the
    concurrent-index corruption class, and it is not recoverable by retrying.
    """
    root = tmp_path / "cs-lane-queue"
    root.mkdir()
    with pytest.raises(launcher.LaneLaunchError, match="main tree"):
        launcher.ensure_worktree("queue", base=tmp_path, root=root)


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
    """Run one launch against planted paths, with git and the spawn injected."""
    base = tmp_path / "wts"
    (base / "cs-lane-queue").mkdir(parents=True)
    (base / "cs-lane-queue" / ".git").write_bytes(b"gitdir: planted\n")
    answer: dict[str, Any] = launcher.launch_lane(
        "queue",
        run_id=RUN_ID,
        token=token,
        base=base,
        root=_repo(tmp_path),
        log_dir=tmp_path / "logs",
        spawn=spawn,
    )
    return answer


def test_a_launch_reports_the_worker_it_started(tmp_path: Path) -> None:
    root, claim = _acquire(tmp_path)
    answer = _launch(tmp_path, _Spawn(), claim["token"])
    keys = sorted(answer)
    assert keys == ["lane", "log", "pid", "prompt", "run_id", "started_at", "worktree"]
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
    assert handed == ("run_lane.ps1", "headless-queue.md", "cs-lane-queue", ".log")


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
            base=tmp_path / "wts",
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

    ``/T`` is deliberately NOT this function's business: the launcher kills the
    one pid it spawned and failed to track. The driver, which kills a whole lane
    tree, is where the tree flag belongs.
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
    assert flags == ["/F", "/PID", str(WORKER_PID)]
    assert Path(program).name.lower().startswith("taskkill")
    assert Path(program).is_absolute(), (
        f"the killer is not rooted, so the cwd could supply it: {program!r}"
    )
    cmdlet = [text for text in _executable_strings(LAUNCHER_SOURCE) if "Stop-Process" in text]
    assert cmdlet == []


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
