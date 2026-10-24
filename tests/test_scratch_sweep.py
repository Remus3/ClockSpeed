"""CS-1344 - this session's Claude scratchpad stays bounded, and the sweep is scoped.

THE ORDER. MAIN's FIX of 2026-10-21 measured one Claude session scratchpad at
about 66.1k files, and the temp directory's entry count costs boot time on this
machine; the target is under 5k files per session scratchpad. The bulk is
whole-tree copies agents extract to read a frozen candidate.
``tools/scratch_sweep.py`` sends the largest top-level directories of THIS
session's scratchpad to the Recycle Bin (FLEET item 9) until it holds under the
bound, and ``.claude/commands/done.md`` runs it as the session ends.

SCOPE. Other agents of the same session may still read what they extracted, so
nothing inside the grace period goes, no loose file goes, no link or junction is
followed or removed, and nothing outside the one resolved scratchpad is touched.

EVERY ARM RUNS AGAINST A SCRATCHPAD UNDER ``tmp_path`` with an injected remover,
so no arm reads or touches the real scratchpad or the real Recycle Bin, and each
remover records what it was handed so the arm can grade that every path was
inside its own scratchpad. Every observation is reduced to a bool or a count
before an assertion sees it.
"""

from __future__ import annotations

import ctypes
import importlib.util
import os
import shutil
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
TOOL_PATH: Final = REPO_ROOT / "tools" / "scratch_sweep.py"
MODULE_NAME: Final = "cs1344_scratch_sweep"
SESSION: Final = "0123abcd-4567-89ef-0123-456789abcdef"
OTHER_SESSION: Final = "fedcba98-7654-3210-fedc-ba9876543210"

#: The planted sizes, in files, and the bound most arms sweep against.
BOUND: Final = 50
BIG: Final = 60
MID: Final = 30
SMALL: Final = 10
FEW: Final = 5
TREE: Final = 20
MANY_LOOSE: Final = 80
OUTSIDE: Final = 100

#: ``SHFileOperationW``'s delete operation and its allow-undo flag.
FO_DELETE: Final = 3
FOF_ALLOWUNDO: Final = 0x0040


def _load() -> ModuleType:
    """Load the tool by path under a module name private to this file."""
    cached = sys.modules.get(MODULE_NAME)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(MODULE_NAME, TOOL_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(MODULE_NAME)
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


SWEEP = _load()

#: The tool's grace period, typed here: the module is loaded by path.
GRACE_S: Final[float] = SWEEP.GRACE_S


def _fill(directory: Path, files: int) -> Path:
    """Make ``directory`` holding ``files`` files, two levels deep."""
    (directory / "a" / "b").mkdir(parents=True)
    for index in range(files):
        (directory / "a" / "b" / f"f{index}.txt").write_bytes(b"x")
    return directory


def _loose(scratchpad: Path, files: int) -> None:
    """``files`` loose files directly in the scratchpad - logs, scripts, notes."""
    for index in range(files):
        (scratchpad / f"note{index}.log").write_bytes(b"x")


class Recorder:
    """A remover that records every path it is handed and removes it with rmtree."""

    def __init__(self, fail: bool = False) -> None:
        """A recorder; ``fail`` makes every call refuse, as a refused move does."""
        self.handed: list[Path] = []
        self.fail = fail

    def __call__(self, path: Path) -> None:
        """Record ``path``, then refuse or remove it."""
        self.handed.append(path)
        if self.fail:
            raise OSError("planted refusal")
        shutil.rmtree(path)

    def all_inside(self, scratchpad: Path) -> bool:
        """Whether every handed path is a direct child of ``scratchpad``."""
        return all(path.parent == scratchpad for path in self.handed)


def _later() -> float:
    """A clock past every grace period: every planted entry reads as old."""
    return time.time() + GRACE_S + 3600


@pytest.fixture
def scratchpad(tmp_path: Path) -> Path:
    """An empty stand-in scratchpad under the arm's own tmp_path."""
    path = tmp_path / "scratchpad"
    path.mkdir()
    return path


def test_a_scratchpad_under_the_bound_is_left_alone(scratchpad: Path) -> None:
    """Nothing is removed while the scratchpad holds fewer files than the bound."""
    _fill(scratchpad / "tree", TREE)
    _loose(scratchpad, FEW)
    remover = Recorder()
    result = SWEEP.sweep(scratchpad, apply=True, remove=remover, bound=BOUND, now=_later())
    handed = len(remover.handed)
    assert handed == 0, f"the sweep removed {handed} entr(ies) under the bound"
    assert result.before == TREE + FEW, f"the sweep counted {result.before} files"
    assert not result.over_bound, "a scratchpad under the bound read as over it"


def test_the_largest_old_directories_go_first_until_the_scratchpad_is_under_the_bound(
    scratchpad: Path,
) -> None:
    """Largest first, and no further than the bound needs: the fewest entries go."""
    big = _fill(scratchpad / "big", BIG)
    mid = _fill(scratchpad / "mid", MID)
    small = _fill(scratchpad / "small", SMALL)
    _loose(scratchpad, FEW)
    remover = Recorder()
    result = SWEEP.sweep(scratchpad, apply=True, remove=remover, bound=BOUND, now=_later())
    only_big = remover.handed == [big]
    assert only_big, "the sweep did not remove exactly the largest directory"
    assert remover.all_inside(scratchpad), "the sweep handed a path outside its scratchpad"
    kept = mid.is_dir() and small.is_dir() and len(list(scratchpad.glob("note*.log"))) == FEW
    assert kept, "the sweep removed more than the bound needed"
    assert result.before == BIG + MID + SMALL + FEW, f"counted {result.before} files before"
    assert result.after == MID + SMALL + FEW, f"the sweep left {result.after} files"
    assert result.recycled == 1, f"the sweep reported {result.recycled} recycled, not 1"
    assert not result.over_bound, "the swept scratchpad still read as over the bound"


def test_loose_files_are_never_swept(scratchpad: Path) -> None:
    """Logs, scripts and notes stay; a scratchpad of loose files alone stays over."""
    tree = _fill(scratchpad / "tree", SMALL)
    _loose(scratchpad, MANY_LOOSE)
    remover = Recorder()
    result = SWEEP.sweep(scratchpad, apply=True, remove=remover, bound=BOUND, now=_later())
    only_tree = remover.handed == [tree]
    assert only_tree, "the sweep handed something other than the one directory"
    loose = len(list(scratchpad.glob("note*.log")))
    assert loose == MANY_LOOSE, f"the sweep removed {MANY_LOOSE - loose} loose file(s)"
    assert result.over_bound, "a scratchpad of loose files over the bound read as under it"


def test_a_directory_inside_its_grace_period_is_never_swept(scratchpad: Path) -> None:
    """A tree another agent of this session extracted moments ago is not taken from it."""
    _fill(scratchpad / "fresh", BIG)
    remover = Recorder()
    result = SWEEP.sweep(scratchpad, apply=True, remove=remover, bound=BOUND, now=time.time())
    handed = len(remover.handed)
    assert handed == 0, f"the sweep removed {handed} directory(ies) inside the grace period"
    assert result.over_bound, "the scratchpad read as under the bound though nothing went"


def test_a_directory_written_inside_its_grace_period_is_never_swept(
    scratchpad: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An old directory an agent is still writing into is live: its newest write counts.

    On a scripted clock: every entry reads as made long ago except one file
    written just now, deep inside ``live``. Its sibling ``idle``, the same size
    and age with no recent write, is the control - it IS swept, so the arm is
    not passing because nothing was old enough to go.
    """
    clock = time.time()
    live = _fill(scratchpad / "live", BIG)
    idle = _fill(scratchpad / "idle", BIG)
    (live / "a" / "b" / "being_written.log").write_bytes(b"live")

    def scripted(entry: os.DirEntry[str]) -> float:
        if entry.name == "being_written.log":
            return clock
        return clock - GRACE_S - 3600

    monkeypatch.setattr(SWEEP, "_times", scripted)
    remover = Recorder()
    SWEEP.sweep(scratchpad, apply=True, remove=remover, bound=BOUND, now=clock)
    only_idle = remover.handed == [idle]
    assert only_idle, "the sweep took the directory being written, or not its idle sibling"
    assert live.is_dir(), "the sweep removed a directory an agent wrote into moments ago"


def _make_link(link: Path, target: Path) -> None:
    """A directory junction on Windows, a symlink elsewhere; a skip where neither works."""
    create: Callable[[str, str], None] | None = None
    if os.name == "nt":
        create = getattr(importlib.import_module("_winapi"), "CreateJunction", None)
    try:
        if create is not None:
            create(str(target), str(link))
        else:
            link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip("this filesystem will not create a link here: " + type(exc).__name__)


def test_a_link_or_junction_is_never_followed_counted_or_swept(
    tmp_path: Path, scratchpad: Path
) -> None:
    """A link in the scratchpad points somewhere this sweep does not own."""
    outside = _fill(tmp_path / "outside", OUTSIDE)
    link = scratchpad / "link"
    _make_link(link, outside)
    _fill(scratchpad / "tree", SMALL)
    remover = Recorder()
    result = SWEEP.sweep(scratchpad, apply=True, remove=remover, bound=FEW, now=_later())
    link_handed = any(path.name == "link" for path in remover.handed)
    assert not link_handed, "the sweep handed a link to its remover"
    outside_kept = len(list((outside / "a" / "b").iterdir())) == OUTSIDE
    assert outside_kept, "the sweep reached through a link"
    assert result.before == SMALL, f"the sweep counted {result.before} files, links included"


def test_a_link_nested_inside_a_tree_is_never_followed_or_counted(
    tmp_path: Path, scratchpad: Path
) -> None:
    """A junction deep inside an extracted tree is counted as nothing, not as its target.

    The top-level arm above never reaches the walk below the top level: there a
    link is skipped before any walk starts. This one plants the link INSIDE a
    tree, where only the walk's own check stands between the count and the
    target's files.
    """
    outside = _fill(tmp_path / "outside", OUTSIDE)
    tree = _fill(scratchpad / "tree", SMALL)
    _make_link(tree / "a" / "link", outside)
    remover = Recorder()
    result = SWEEP.sweep(scratchpad, apply=False, remove=remover, bound=BOUND, now=_later())
    assert result.before == SMALL, f"the walk counted {result.before} files, through a link"
    outside_kept = len(list((outside / "a" / "b").iterdir())) == OUTSIDE
    assert outside_kept, "a dry run touched a link's target"


def test_a_dry_run_removes_nothing_and_reports_what_it_would(scratchpad: Path) -> None:
    """The default is a dry run: the remover is never called, the result is projected."""
    big = _fill(scratchpad / "big", BIG)
    _fill(scratchpad / "small", SMALL)
    remover = Recorder()
    result = SWEEP.sweep(scratchpad, apply=False, remove=remover, bound=BOUND, now=_later())
    handed = len(remover.handed)
    assert handed == 0, "a dry run called the remover"
    assert big.is_dir(), "a dry run removed a directory"
    assert result.recycled == 1, f"the dry run projected {result.recycled} recycled, not 1"
    assert result.after == SMALL, f"the dry run projected {result.after} files left"


def test_a_remover_that_fails_leaves_the_directory_and_is_counted(scratchpad: Path) -> None:
    """A refused move is reported, never escalated to a direct delete."""
    big = _fill(scratchpad / "big", BIG)
    remover = Recorder(fail=True)
    result = SWEEP.sweep(scratchpad, apply=True, remove=remover, bound=BOUND, now=_later())
    assert big.is_dir(), "a refused move was escalated to a removal"
    assert result.failed == 1, f"the sweep reported {result.failed} failed, not 1"
    assert result.recycled == 0, f"the sweep reported {result.recycled} recycled, not 0"
    assert result.over_bound, "a scratchpad whose sweep failed read as under the bound"


def _session_tree(temp: Path, project: str, session: str) -> Path:
    """``<temp>/claude/<project>/<session>/scratchpad``, the harness's layout."""
    path = temp / "claude" / project / session / "scratchpad"
    path.mkdir(parents=True)
    return path


def test_the_scratchpad_is_resolved_from_this_sessions_id_only(tmp_path: Path) -> None:
    """The session id names one scratchpad; another session's is never chosen."""
    mine = _session_tree(tmp_path, "proj", SESSION)
    _session_tree(tmp_path, "proj", OTHER_SESSION)
    resolved = SWEEP.resolve_scratchpad({SWEEP.ENV_SESSION: SESSION}, tmp_path)
    right = resolved is not None and resolved == mine
    assert right, "the sweep did not resolve this session's own scratchpad"


@pytest.mark.parametrize("case", ["unset", "malformed", "ambiguous", "absent"])
def test_an_unresolvable_session_is_refused(tmp_path: Path, case: str) -> None:
    """No id, an id that is not a session id, two matches or none: nothing is chosen."""
    env: dict[str, str] = {SWEEP.ENV_SESSION: SESSION}
    if case == "unset":
        env = {}
    elif case == "malformed":
        env = {SWEEP.ENV_SESSION: "../" + SESSION}
        _session_tree(tmp_path, "proj", SESSION)
    elif case == "ambiguous":
        _session_tree(tmp_path, "proj", SESSION)
        _session_tree(tmp_path, "other", SESSION)
    resolved = SWEEP.resolve_scratchpad(env, tmp_path)
    assert resolved is None, f"{case}: the sweep resolved a scratchpad it should refuse"


def test_the_cli_reports_under_over_and_refused(tmp_path: Path, scratchpad: Path) -> None:
    """Exit 0 under the bound, 1 still over it, 2 refused - and a dry run by default."""
    _fill(scratchpad / "big", BIG)
    _loose(scratchpad, BIG)
    remover = Recorder()
    base = ["--scratchpad", str(scratchpad), "--bound", str(BOUND), "--grace-s", "0"]
    dry = SWEEP.main(base, remove=remover)
    applied = SWEEP.main([*base, "--apply"], remove=remover)
    refused = SWEEP.main(["--scratchpad", str(tmp_path / "absent")], remove=remover)
    assert dry == SWEEP.EXIT_OVER, f"the dry run exited {dry}, not over"
    assert applied == SWEEP.EXIT_OVER, f"the apply exited {applied}, not over"
    assert refused == SWEEP.EXIT_REFUSED, f"a missing scratchpad exited {refused}, not refused"
    handed = len(remover.handed)
    assert handed == 1, f"the CLI handed {handed} path(s), not the one directory"
    loose_left = len(list(scratchpad.glob("note*.log")))
    assert loose_left == BIG, "the CLI removed loose files"
    under = SWEEP.main([*base, "--bound", str(OUTSIDE), "--apply"], remove=remover)
    assert under == SWEEP.EXIT_UNDER, f"a scratchpad under the bound exited {under}"


@pytest.mark.skipif(sys.platform != "win32", reason="the Recycle Bin is reachable on Windows only")
@pytest.mark.parametrize("status", [0, 2])
def test_recycle_asks_the_shell_for_an_undoable_delete_of_exactly_the_one_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """The shell is asked to DELETE with UNDO - the Recycle Bin - one path, double-NUL ended.

    The shell call is stubbed, so nothing reaches the real Recycle Bin; a
    refusal from the shell raises rather than falling back to a direct unlink.
    """
    target = tmp_path / "tree"
    target.mkdir()
    spelled = str(target.absolute())
    seen: dict[str, object] = {}

    class FakeShell:
        def SHFileOperationW(self, ref: object) -> int:  # noqa: N802 - the Win32 name
            operation = ref._obj  # type: ignore[attr-defined]  # noqa: SLF001 - byref's target
            seen["func"] = operation.wFunc
            seen["flags"] = operation.fFlags
            seen["from"] = ctypes.wstring_at(operation.pFrom, len(spelled) + 2)
            return status

    monkeypatch.setattr(ctypes.windll, "shell32", FakeShell())
    raised = False
    try:
        SWEEP.recycle(target)
    except OSError:
        raised = True
    deleting = seen.get("func") == FO_DELETE
    flags = seen.get("flags")
    undoable = isinstance(flags, int) and bool(flags & FOF_ALLOWUNDO)
    one_path = seen.get("from") == spelled + "\0\0"
    assert deleting, "the shell was not asked to delete"
    assert undoable, "the delete was not sent to the Recycle Bin"
    assert one_path, "the shell was not handed exactly the one path, double-NUL ended"
    assert raised == (status != 0), f"shell status {status} was not reported as it should be"
    assert target.is_dir(), "the stubbed recycle removed the directory some other way"


@pytest.mark.skipif(sys.platform == "win32", reason="Windows has a Recycle Bin")
def test_recycle_refuses_where_there_is_no_recycle_bin(tmp_path: Path) -> None:
    """Never a direct unlink in its place: the directory stays and the call raises."""
    target = _fill(tmp_path / "tree", FEW)
    refused = False
    try:
        SWEEP.recycle(target)
    except OSError:
        refused = True
    assert refused, "recycle did not refuse where no Recycle Bin is reachable"
    assert target.is_dir(), "recycle removed the directory without a Recycle Bin"
