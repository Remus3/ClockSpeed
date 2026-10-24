"""CS-1319 - the tree-owned temp root's mechanism: claim, sweep, remove, finish.

The wiring - that a real run lands under the root - is graded in
``tests/test_suite_temp_root.py``. Here every arm drives
``tests/own_temp_root.py`` against a parent directory under ``tmp_path`` and a
plain dict standing in for the environment, so no arm touches the real root
or the real process environment. The ``install`` arms are the exception they
must be: ``install`` reads the process environment and the system temp
directory, so those arms point the temp directory at ``tmp_path`` and clear
the temp-root variables through ``monkeypatch``, which restores both.
"""

from __future__ import annotations

import getpass
import os
import stat
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from _pytest import tmpdir as pytest_tmpdir

from tests import own_temp_root
from tests.own_temp_root import (
    ALIVE_NAME,
    ENV_NESTED,
    ENV_TEMPROOT,
    GRACE_S,
    RUN_PREFIX,
    STALE_AFTER_S,
)

HOUR = 3600.0


def test_a_claim_creates_a_fresh_run_directory_and_points_the_environment_at_it(
    tmp_path: Path,
) -> None:
    """The run directory is new, under the parent, and named for a run."""
    env: dict[str, str] = {}
    claimed_run = own_temp_root.claim(tmp_path, env)
    run = None if claimed_run is None else claimed_run.path
    claimed = run is not None and run.is_dir() and run.parent == tmp_path
    assert claimed, "no run directory was claimed under the parent"
    pointed = run is not None and env.get(ENV_TEMPROOT) == str(run)
    assert pointed, "the environment does not name the claimed run directory"
    named = run is not None and run.name.startswith(RUN_PREFIX)
    assert named, "the run directory does not carry the run prefix"


def test_two_claims_never_share_a_run_directory(tmp_path: Path) -> None:
    """Concurrent suites - two gate slots, worktrees - each get their own."""
    first = own_temp_root.claim(tmp_path, {})
    second = own_temp_root.claim(tmp_path, {})
    distinct = first is not None and second is not None and first.path != second.path
    assert distinct, "two claims returned the same run directory"


def test_a_root_already_named_in_the_environment_is_never_overridden(tmp_path: Path) -> None:
    """An xdist worker, a nested run or an operator's own choice keeps its root.

    The claim returns None, so the caller owns nothing and removes nothing,
    and nothing is created under the parent.
    """
    chosen = str(tmp_path / "chosen")
    env = {ENV_TEMPROOT: chosen}
    run = own_temp_root.claim(tmp_path / "parent", env)
    kept = run is None and env == {ENV_TEMPROOT: chosen}
    assert kept, "an existing temp root was overridden"
    created = (tmp_path / "parent").exists()
    assert not created, "a claim that owns nothing still created the parent"


def _age(path: Path, seconds: float) -> None:
    """Back-date ``path``'s modification time by ``seconds``."""
    when = path.stat().st_mtime - seconds
    os.utime(path, (when, when))


def test_the_sweep_removes_only_stale_run_directories(tmp_path: Path) -> None:
    """A killed run's directory goes once stale; a live one and a stranger stay."""
    stale = tmp_path / (RUN_PREFIX + "1-stale")
    fresh = tmp_path / (RUN_PREFIX + "2-fresh")
    stranger = tmp_path / "not-a-run"
    for directory in (stale, fresh, stranger):
        (directory / "pytest-of-someone" / "pytest-0").mkdir(parents=True)
    _age(stale, STALE_AFTER_S + HOUR)
    _age(stranger, STALE_AFTER_S + HOUR)
    removed = own_temp_root.sweep(tmp_path)
    survivors = sorted(path.name for path in tmp_path.iterdir())
    assert removed == 1, "the sweep did not report exactly one removal"
    assert survivors == sorted([fresh.name, stranger.name]), "the sweep took the wrong entries"


def test_a_claim_sweeps_stale_siblings_first(tmp_path: Path) -> None:
    """A killed run is reclaimed by the next run, with no session finish of its own."""
    stale = tmp_path / (RUN_PREFIX + "1-stale")
    stale.mkdir()
    _age(stale, STALE_AFTER_S + HOUR)
    own_temp_root.claim(tmp_path, {})
    still_there = stale.exists()
    assert not still_there, "the claim left a stale run directory standing"


def test_a_missing_parent_sweeps_nothing(tmp_path: Path) -> None:
    """The first run on a machine has no root yet; that is not an error."""
    removed = own_temp_root.sweep(tmp_path / "absent")
    assert removed == 0, "a sweep of a missing parent reported removals"


def _make_junction(link: Path, target: Path) -> None:
    """A directory junction, or a skip where the platform has none."""
    winapi = pytest.importorskip("_winapi")
    create = getattr(winapi, "CreateJunction", None)
    if create is None:
        pytest.skip("this platform has no directory junctions")
    try:
        create(str(target), str(link))
    except OSError as exc:
        pytest.skip("this filesystem will not create a junction here: " + type(exc).__name__)


def test_removal_clears_read_only_entries_and_never_follows_a_link(tmp_path: Path) -> None:
    """Read-only files, directories and links all go; a link's target is untouched.

    The shape ``tests/save/test_workdir.py`` plants: read-only entries, and a
    junction pointing OUT of the tree. A removal that followed the junction
    would delete the target's contents - the outcome this arm exists to rule
    out - so the target is asserted intact before the verdict on the tree.
    """
    target = tmp_path / "outside"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_bytes(b"must survive")
    tree = tmp_path / "run"
    inner = tree / "inner"
    inner.mkdir(parents=True)
    locked = inner / "locked.txt"
    locked.write_bytes(b"read-only")
    locked.chmod(stat.S_IREAD)
    junction = tree / "junction"
    _make_junction(junction, target)
    if os.chmod in os.supports_follow_symlinks:
        junction.chmod(stat.S_IREAD, follow_symlinks=False)
    inner.chmod(stat.S_IREAD | stat.S_IEXEC)
    own_temp_root.remove_tree(tree)
    target_intact = sentinel.read_bytes() == b"must survive"
    assert target_intact, "the removal followed a junction out of the tree"
    gone = tree.exists()
    assert not gone, "the read-only tree was not removed"


@pytest.mark.skipif(os.name != "nt", reason="only Win32 path normalisation strips a trailing dot")
def test_removal_takes_a_name_the_win32_path_layer_cannot_spell(tmp_path: Path) -> None:
    """A file named ``zz.`` - planted by the inbox lstat arms - is removed too.

    MEASURED after the first whole-suite run under this mechanism: one run
    directory survived every sweep because two files named ``zz.`` sat in it,
    and a plain path drops the trailing dot, so neither the unlink nor the
    rmdir above it could succeed. pytest's own removal leaks them the same
    way into the shared root. Only the extended-length form names them.
    """
    tree = tmp_path / "run"
    tree.mkdir()
    extended = "\\\\?\\" + str(tree.resolve()) + "\\zz."
    with open(extended, "wb") as handle:  # noqa: PTH123 - pathlib would drop the dot
        handle.write(b"x")
    planted = os.path.lexists(extended)
    assert planted, "the trailing-dot fixture did not plant"
    own_temp_root.remove_tree(tree)
    gone = tree.exists()
    assert not gone, "a trailing-dot name kept the tree standing"


def test_removal_of_a_missing_tree_is_quiet(tmp_path: Path) -> None:
    """Another process got there first; that is not an error."""
    own_temp_root.remove_tree(tmp_path / "absent")


@pytest.mark.parametrize("nested", [False, True])
def test_finish_removes_the_whole_run_directory_top_level_or_nested(
    tmp_path: Path, nested: bool
) -> None:
    """CS-1344 - every finish clears its run's output; nothing reads the exit status.

    CS-1319 kept a failed, interrupted or internal-error TOP-LEVEL run's
    directory as the record of the failure, and removed a nested one's - a
    pytest a test spawned, often failing on purpose: the first whole suite
    under that mechanism left 36 of them. MAIN's FIX of 2026-10-21 overrides
    the retention: one failed whole suite kept about sixteen thousand
    directories, and the temp directory's entry count costs boot time. An
    operator who wants a failure's tmp_paths passes ``--basetemp``, which this
    mechanism never claims or removes. The real exit statuses - passing,
    failing, erroring, interrupted - are driven through a real session in
    ``tests/test_cs1344_temp_teardown.py``.
    """
    run = own_temp_root.claim(tmp_path, {ENV_NESTED: "1"} if nested else {})
    if run is None:
        pytest.fail("the claim owned nothing")
    (run.path / "pytest-of-someone" / "pytest-0").mkdir(parents=True)
    own_temp_root.finish(run)
    left = os.path.lexists(run.path)
    assert not left, "finish kept the run directory"


def test_a_top_level_claim_marks_the_environment_for_nested_runs(tmp_path: Path) -> None:
    """The marker is what tells a pytest spawned by a test that it is nested."""
    env: dict[str, str] = {}
    run = own_temp_root.claim(tmp_path, env)
    marked = run is not None and not run.nested and env.get(ENV_NESTED) == "1"
    assert marked, "a top-level claim did not mark the environment"


def _dead_run(parent: Path, name: str, age_s: float) -> Path:
    """A run directory whose owner is gone: no live handle on its marker."""
    run = parent / (RUN_PREFIX + name)
    (run / "pytest-of-someone" / "pytest-0").mkdir(parents=True)
    (run / ALIVE_NAME).write_bytes(b"")
    _age(run, age_s)
    return run


@pytest.mark.skipif(os.name != "nt", reason="only Windows refuses to unlink an open file")
def test_the_sweep_reclaims_a_killed_run_long_before_it_is_stale(tmp_path: Path) -> None:
    """A killed run is reclaimed by the NEXT run, not six hours later.

    A live owner holds its marker open, and Windows refuses to unlink an open
    file; a killed process's handles are closed by the system. So a run
    directory whose marker can be unlinked has no live owner.
    """
    live = own_temp_root.claim(tmp_path, {})
    if live is None:
        pytest.fail("the claim owned nothing")
    work = live.path / "pytest-of-someone" / "pytest-0" / "work.txt"
    work.parent.mkdir(parents=True)
    work.write_bytes(b"a live run's work")
    _age(live.path, GRACE_S + 60)
    dead = _dead_run(tmp_path, "1-dead", GRACE_S + 60)
    try:
        removed = own_temp_root.sweep(tmp_path)
        survivors = sorted(path.name for path in tmp_path.iterdir())
        work_kept = work.is_file()
    finally:
        own_temp_root.finish(live)
    assert removed == 1, "the sweep did not reclaim exactly the dead run"
    dead_kept = dead.name in survivors
    assert not dead_kept, "the sweep kept a dead run"
    assert work_kept, "the sweep emptied a live run"


@pytest.mark.skipif(os.name != "nt", reason="only Windows refuses to unlink an open file")
def test_a_live_run_is_never_swept_however_old_it_is(tmp_path: Path) -> None:
    """Age never overrules a held marker: a run open for hours keeps its tmp_paths.

    The adversary's blocker on the first candidate: past six hours the sweep
    removed a LIVE run's contents - a ``--pdb`` session or a hung run - because
    age was checked before liveness.
    """
    live = own_temp_root.claim(tmp_path, {})
    if live is None:
        pytest.fail("the claim owned nothing")
    work = live.path / "pytest-of-someone" / "pytest-0" / "work.txt"
    work.parent.mkdir(parents=True)
    work.write_bytes(b"a live run's work")
    _age(live.path, STALE_AFTER_S + HOUR)
    try:
        removed = own_temp_root.sweep(tmp_path)
        work_kept = work.is_file()
    finally:
        own_temp_root.finish(live)
    assert removed == 0, "the sweep counted a live run as removed"
    assert work_kept, "the sweep emptied a live run because it was old"


@pytest.mark.parametrize("ahead_s", [GRACE_S + 600, STALE_AFTER_S + HOUR])
def test_the_sweep_never_reaches_through_a_run_named_link(tmp_path: Path, ahead_s: float) -> None:
    """An ``r-*`` entry that is a junction is left alone, and so is its target.

    The adversary's finding on the first candidate: inside the liveness window
    the probe unlinked the marker THROUGH the junction, deleting a file outside
    the root. Graded in both windows - the liveness probe and the stale age.
    No claim makes a link, so a link is never this mechanism's to remove.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / ALIVE_NAME
    marker.write_bytes(b"")
    keep = outside / "keep.txt"
    keep.write_bytes(b"must survive")
    parent = tmp_path / "root"
    parent.mkdir()
    link = parent / (RUN_PREFIX + "999-link")
    _make_junction(link, outside)
    own_temp_root.sweep(parent, now=time.time() + ahead_s)
    untouched = marker.exists() and keep.read_bytes() == b"must survive"
    assert untouched, "the sweep reached through a run-named link"
    link_kept = link.is_junction()
    assert link_kept, "the sweep removed an entry it did not make"


def test_a_claim_that_cannot_make_its_root_owns_nothing_and_raises_nothing(
    tmp_path: Path,
) -> None:
    """A configure hook that raised would stop the whole session (INTERNALERROR).

    With the root's name taken by a file, the claim falls back to pytest's
    default - it owns nothing and leaves the environment as it found it.
    """
    blocked = tmp_path / "root"
    blocked.write_bytes(b"a file where the root should be")
    env: dict[str, str] = {}
    run = own_temp_root.claim(blocked, env)
    fell_back = run is None and env == {}
    assert fell_back, "a claim that could not make its root still claimed or changed the env"


def test_a_run_directory_inside_its_grace_period_is_never_swept(tmp_path: Path) -> None:
    """A sibling between its mkdir and its marker's open is not yet holding it."""
    young = tmp_path / (RUN_PREFIX + "1-young")
    young.mkdir()
    removed = own_temp_root.sweep(tmp_path)
    assert removed == 0, "the sweep took a run directory inside its grace period"


def test_a_run_whose_removal_left_something_is_reclaimed_by_the_next_sweep_at_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1344 - a teardown that could not finish its removal is not left for hours.

    A removal can fail part-way - a file a leaked child still holds open on
    Windows. The owner has finished, so neither the grace period (a sibling
    between its mkdir and its marker's open) nor the stale age (a platform with
    no liveness proof) protects anything: the very next sweep reclaims it, on
    every platform. The failed removal is simulated by a removal that does
    nothing, so the run is still inside its grace period at the sweep.
    """
    run = own_temp_root.claim(tmp_path, {})
    if run is None:
        pytest.fail("the claim owned nothing")
    work = run.path / "pytest-of-someone" / "pytest-0" / "work.txt"
    work.parent.mkdir(parents=True)
    work.write_bytes(b"what the run wrote")
    with monkeypatch.context() as patch:
        patch.setattr(own_temp_root, "remove_tree", lambda _path: None)
        own_temp_root.finish(run)
    left_by_finish = os.path.lexists(run.path)
    assert left_by_finish, "the simulated failed removal removed the run anyway"
    removed = own_temp_root.sweep(tmp_path)
    gone = not os.path.lexists(run.path)
    assert removed == 1, "the next sweep did not reclaim the finished run's leftover"
    assert gone, "a finished run's leftover waited out the grace period or the stale age"


def test_a_half_made_run_is_removed_when_its_marker_cannot_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The run directory is made but its marker cannot be: nothing is left behind.

    The second adversary found no arm guarding this cleanup. The marker's name
    is pointed into a directory that does not exist, so the open fails after
    the run directory's mkdir succeeded.
    """
    monkeypatch.setattr(own_temp_root, "ALIVE_NAME", "absent-subdir/.alive")
    env: dict[str, str] = {}
    run = own_temp_root.claim(tmp_path, env)
    left = sorted(path.name for path in tmp_path.iterdir())
    fell_back = run is None and env == {}
    assert fell_back, "a claim whose marker could not open still claimed"
    assert left == [], "a half-made run directory was left behind"


#: The marker the CS-1319 finisher wrote into a failed run's kept directory.
#: Spelled out, not imported: a worktree on an older commit still writes it.
CS1319_FAILED_MARKER = ".failed"


def test_every_failed_run_older_code_kept_is_reclaimed_at_once(tmp_path: Path) -> None:
    """CS-1344 - no failed run's directory is kept, the newest one included.

    The CS-1319 finisher kept the newest failed run until the stale age, and a
    worktree on an older commit still does. Its owner has finished, so the
    next sweep reclaims every one of them, inside the grace period or past it,
    and the root is left empty.
    """
    ages = (30.0, 60.0, GRACE_S + 300)
    runs = []
    for index, age in enumerate(ages):
        run = tmp_path / (RUN_PREFIX + f"{index}-failed")
        (run / "pytest-of-someone" / "pytest-0").mkdir(parents=True)
        (run / CS1319_FAILED_MARKER).write_bytes(b"")
        _age(run, age)
        runs.append(run)
    planted = len(runs)
    removed = own_temp_root.sweep(tmp_path)
    survivors = len(list(tmp_path.iterdir()))
    assert removed == planted, "the sweep did not reclaim every failed run"
    assert survivors == 0, f"the sweep kept {survivors} failed run(s)"


def test_finish_never_touches_another_runs_directory(tmp_path: Path) -> None:
    """CS-1344 - a teardown removes its own run directory and nothing beside it.

    Other suites run concurrently under the same root. A failing run's finish
    leaves a live sibling, a sibling inside its grace period, a sibling whose
    owner is gone (the NEXT claim's to reclaim, never a finish's) and a
    stranger exactly as it found them.
    """
    own = own_temp_root.claim(tmp_path, {})
    live = own_temp_root.claim(tmp_path, {})
    if own is None or live is None:
        pytest.fail("a claim owned nothing")
    young = tmp_path / (RUN_PREFIX + "young")
    dead = _dead_run(tmp_path, "dead", GRACE_S + 600)
    stranger = tmp_path / "not-a-run"
    works = [live.path / "work.txt", young / "work.txt", dead / "work.txt", stranger / "work.txt"]
    try:
        for work in works:
            work.parent.mkdir(exist_ok=True)
            work.write_bytes(b"another run's work")
        _age(dead, GRACE_S + 600)
        own_temp_root.finish(own)
        kept = sum(1 for work in works if work.is_file())
        own_gone = not os.path.lexists(own.path)
    finally:
        own_temp_root.finish(live)
    planted = len(works)
    assert own_gone, "the failing run's finish kept its own run directory"
    assert kept == planted, f"the finish removed {planted - kept} sibling work file(s)"


def test_dead_runs_under_the_cs1319_root_name_are_still_reclaimed(tmp_path: Path) -> None:
    """CS-1320 renamed the root; a killed run left under the old name is not orphaned.

    The old root's runs carry the old prefix and the same liveness marker, so
    the same sweep verdicts apply to them: a stale run goes, a fresh one and a
    stranger stay. A root left empty is removed.
    """
    legacy = tmp_path / own_temp_root.LEGACY_ROOT_NAME
    stale = legacy / (own_temp_root.LEGACY_RUN_PREFIX + "1-stale")
    fresh = legacy / (own_temp_root.LEGACY_RUN_PREFIX + "2-fresh")
    stranger = legacy / "not-a-run"
    for directory in (stale, fresh, stranger):
        (directory / "pytest-of-someone" / "pytest-0").mkdir(parents=True)
    _age(stale, STALE_AFTER_S + HOUR)
    removed = own_temp_root.sweep_legacy(tmp_path)
    survivors = sorted(path.name for path in legacy.iterdir())
    assert removed == 1, "the legacy sweep did not report exactly one removal"
    kept_right = survivors == sorted([fresh.name, stranger.name])
    assert kept_right, "the legacy sweep took the wrong entries"
    for directory in (fresh, stranger):
        own_temp_root.remove_tree(directory)
    own_temp_root.sweep_legacy(tmp_path)
    root_left = legacy.exists()
    assert not root_left, "an empty legacy root was left standing"


def test_a_missing_legacy_root_sweeps_nothing(tmp_path: Path) -> None:
    """A machine that never ran the CS-1319 layout has no old root; not an error."""
    removed = own_temp_root.sweep_legacy(tmp_path)
    assert removed == 0, "a sweep of a missing legacy root reported removals"


def test_an_aged_stranger_under_the_legacy_root_is_never_swept(tmp_path: Path) -> None:
    """Only ``run-*`` entries under the CS-1319 root are this sweep's to remove.

    The first legacy arm's stranger was young, so the grace period alone kept
    it and an emptied prefix filter passed unseen. This stranger is past the
    stale age, carries no held marker, and must still survive.
    """
    legacy = tmp_path / own_temp_root.LEGACY_ROOT_NAME
    stranger = legacy / "not-a-run"
    (stranger / "pytest-of-someone" / "pytest-0").mkdir(parents=True)
    _age(stranger, STALE_AFTER_S + HOUR)
    removed = own_temp_root.sweep_legacy(tmp_path)
    kept = stranger.is_dir()
    assert kept, "the legacy sweep removed an aged entry without the run prefix"
    assert removed == 0, "the legacy sweep counted a stranger as a removal"


def _make_link(kind: str, link: Path, target: Path) -> None:
    """A junction or a directory symlink at ``link``, or a skip where none can be made."""
    if kind == "junction":
        _make_junction(link, target)
        return
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip("this account cannot create a symlink here: " + type(exc).__name__)


@pytest.mark.parametrize("kind", ["junction", "symlink"])
def test_a_legacy_root_that_is_a_link_is_never_reached_through(tmp_path: Path, kind: str) -> None:
    """A CS-1319 root name that is a link is left alone, and so is its target.

    The target holds a dead, stale ``run-*`` directory - one the sweep WOULD
    remove from a real legacy root - so only the link guard keeps it.
    """
    outside = tmp_path / "outside"
    target_run = outside / (own_temp_root.LEGACY_RUN_PREFIX + "1-dead")
    (target_run / "pytest-of-someone" / "pytest-0").mkdir(parents=True)
    (target_run / ALIVE_NAME).write_bytes(b"")
    _age(target_run, STALE_AFTER_S + HOUR)
    temp = tmp_path / "temp"
    temp.mkdir()
    link = temp / own_temp_root.LEGACY_ROOT_NAME
    _make_link(kind, link, outside)
    removed = own_temp_root.sweep_legacy(temp)
    untouched = target_run.is_dir()
    assert untouched, "the legacy sweep reached through a linked root"
    assert removed == 0, "the legacy sweep counted a removal through a linked root"
    link_kept = os.path.lexists(link)
    assert link_kept, "the legacy sweep removed a link it did not make"


class _FakePluginManager:
    """The two plugin-manager calls :func:`own_temp_root.install` makes."""

    def __init__(self) -> None:
        self.registered: dict[str, object] = {}

    def has_plugin(self, name: str) -> bool:
        """Whether ``name`` was registered."""
        return name in self.registered

    def register(self, plugin: object, name: str) -> None:
        """Record ``plugin`` under ``name``."""
        self.registered[name] = plugin


class _FakeConfig:
    """A configuration with no ``--basetemp`` and a stand-in temp path factory."""

    def __init__(self) -> None:
        self.option = SimpleNamespace(basetemp=None)
        self.pluginmanager = _FakePluginManager()
        self.original_factory = object()
        self._tmp_path_factory: object = self.original_factory

    def getoption(self, name: str, default: object = None) -> object:
        """An option's value, as ``pytest.Config.getoption`` reads it."""
        return getattr(self.option, name, default)


@dataclass
class _Installed:
    """What one :func:`own_temp_root.install` call against ``tmp_path`` left."""

    config: _FakeConfig
    run: own_temp_root.Claim | None
    root: Path
    handed: list[str]


def _install_under(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rebuild: Callable[[_FakeConfig], object] | None = None,
) -> _Installed:
    """Run :func:`own_temp_root.install` with ``tmp_path`` as the system temp.

    The temp-root variables are cleared through ``monkeypatch``, so this
    process's own claim is restored after the arm. ``rebuild`` stands in for
    pytest's factory rebuild; the default records the base temp it was handed.
    """
    monkeypatch.setattr(own_temp_root.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.delenv(ENV_TEMPROOT, raising=False)
    monkeypatch.delenv(ENV_NESTED, raising=False)
    handed: list[str] = []

    def rebuild_from(config: _FakeConfig, **_kwargs: object) -> object:
        if rebuild is not None:
            return rebuild(config)
        handed.append(str(config.option.basetemp))
        return object()

    monkeypatch.setattr(pytest.TempPathFactory, "from_config", rebuild_from)
    config = _FakeConfig()
    run = own_temp_root.install(cast("pytest.Config", config))
    root = tmp_path / own_temp_root.ROOT_NAME
    return _Installed(config=config, run=run, root=root, handed=handed)


def _release(installed: _Installed) -> None:
    """Finish an arm's claim, so no marker is left held open."""
    if installed.run is not None:
        own_temp_root.finish(installed.run)


def test_the_base_temp_given_to_pytest_is_strictly_inside_the_run_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A given base temp is emptied by pytest, so it is never the marker's directory.

    The handed base temp must be a STRICT descendant of the claimed run
    directory: the run directory itself holds the owner's alive marker, and
    pytest would delete it - and with it the sweep's proof of a live owner.
    """
    installed = _install_under(tmp_path, monkeypatch)
    try:
        run = installed.run
        if run is None:
            pytest.fail("the install owned nothing")
        given = Path(installed.config.option.basetemp)
        strictly_inside = run.path in given.parents
        assert strictly_inside, "the base temp is not strictly inside the run directory"
        not_marker_dir = given != (run.path / ALIVE_NAME).parent
        assert not_marker_dir, "the base temp is the directory holding the alive marker"
        handed_same = installed.handed == [str(given)]
        assert handed_same, "the factory was not rebuilt from the given base temp"
        factory = installed.config._tmp_path_factory  # noqa: SLF001
        replaced = factory is not installed.config.original_factory
        assert replaced, "the rebuilt factory was not handed to pytest"
    finally:
        _release(installed)


def _named_for_pytests_user(name: str) -> bool:
    """Whether ``name`` is the per-user value pytest puts in its ``pytest-of-<user>``.

    Derived through pytest's own ``get_user`` rather than through the module
    under test, so the two derivations check each other. A bool, so a failing
    arm renders no account name.
    """
    return name == (pytest_tmpdir.get_user() or "unknown")


def test_the_base_temp_is_named_for_pytests_own_per_user_component(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1322 - the base temp keeps the per-user level pytest's own layout has.

    MEASURED on the ubuntu tier1 lane at 8601200: CS-1320 named the base temp
    ``t``, and ``/tmp`` sits outside the home directory there, so no tmp_path
    carried anything ``redact`` rewrites - 13 privacy arms failed, 11 of them
    UNPROVEN for want of a needle. pytest's default carries the account in
    ``pytest-of-<user>``; the base temp is named for that same per-user value,
    directly inside the run directory, so every tmp_path carries the account
    again on every platform.
    """
    installed = _install_under(tmp_path, monkeypatch)
    try:
        run = installed.run
        if run is None:
            pytest.fail("the install owned nothing")
        given = Path(installed.config.option.basetemp)
        directly_inside = given.parent == run.path
        assert directly_inside, "the base temp is not directly inside the run directory"
        per_user = _named_for_pytests_user(given.name)
        assert per_user, "the base temp lacks pytest's per-user component"
    finally:
        _release(installed)


def _account_reads_as(monkeypatch: pytest.MonkeyPatch, value: str | None) -> None:
    """Make ``getpass.getuser`` answer ``value``, or raise as pytest guards for when None."""

    def getuser() -> str:
        if value is None:
            raise OSError("no account name")
        return value

    monkeypatch.setattr(getpass, "getuser", getuser)


@pytest.mark.parametrize("value", [None, ""], ids=["unreadable", "empty"])
def test_an_unreadable_account_name_falls_back_to_unknown_as_pytest_does(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    """An account pytest cannot read names its level ``pytest-of-unknown``; so here too."""
    _account_reads_as(monkeypatch, value)
    installed = _install_under(tmp_path, monkeypatch)
    try:
        run = installed.run
        if run is None:
            pytest.fail("the install owned nothing")
        given = Path(installed.config.option.basetemp)
        fell_back = given == run.path / "unknown"
        assert fell_back, "an unreadable account name did not fall back to unknown"
    finally:
        _release(installed)


@pytest.mark.parametrize(
    "value", ["..", "a/b", "a\x00b", ALIVE_NAME], ids=["parent", "separator", "nul", "taken"]
)
def test_an_account_name_that_cannot_be_a_fresh_directory_falls_back_to_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """The fallback pytest takes: a ``pytest-of-<user>`` it cannot make is ``pytest-of-unknown``.

    pytest empties a given base temp before use, so it must be a fresh
    directory directly inside the run directory whatever the account is
    called: ``..`` would hand pytest the tree-owned root itself, a separator
    would nest it, a NUL cannot be spelled at all, and a name already taken in
    the run directory - the owner's marker - is not fresh.
    """
    _account_reads_as(monkeypatch, value)
    installed = _install_under(tmp_path, monkeypatch)
    try:
        run = installed.run
        if run is None:
            pytest.fail("the install owned nothing")
        given = Path(installed.config.option.basetemp)
        fell_back = given == run.path / "unknown"
        assert fell_back, "an account name that cannot be a directory did not fall back"
        marker_kept = (run.path / ALIVE_NAME).is_file()
        assert marker_kept, "the per-user probe disturbed the owner's marker"
    finally:
        _release(installed)


def _within_pytests_default_depth(prefix_length: int) -> bool:
    """Whether ``prefix_length`` fits pytest's own default above the temp directory.

    That default is ``pytest-of-<user>/pytest-<N>``, ``N`` one digit at its
    shortest, so the bound is the strictest one - the same bound
    ``tests/test_suite_temp_root.py`` grades a real run against.
    """
    user = pytest_tmpdir.get_user() or "unknown"
    return prefix_length <= len(os.sep + "pytest-of-" + user + os.sep + "pytest-0")


def test_the_handed_base_temp_is_no_deeper_than_pytests_own_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1320's path budget, graded where no ``--basetemp`` and no xdist can skip it.

    The per-user leaf CS-1322 restores must not cost the depth CS-1320
    removed: root, run directory and leaf together stay no longer than
    pytest's own ``pytest-of-<user>/pytest-<N>``. A leaf spelled
    ``pytest-of-<user>`` under the run directory would be eight characters
    over this bound for every account name.
    """
    installed = _install_under(tmp_path, monkeypatch)
    try:
        if installed.run is None:
            pytest.fail("the install owned nothing")
        given = str(installed.config.option.basetemp)
        within = _within_pytests_default_depth(len(given) - len(str(tmp_path)))
        assert within, "the base temp is deeper than pytest's own default layout"
    finally:
        _release(installed)


def test_a_failed_factory_rebuild_releases_the_claim_and_raises_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pytest whose factory API moved degrades to its default, never INTERNALERROR.

    The adversary's finding on CS-1320: ``pyproject.toml`` admits any pytest
    from 8.0 up, and ``TempPathFactory.from_config`` is not public API. A
    rebuild that raised inside ``pytest_configure`` stopped the session with
    exit 3 and left a claimed run directory with its marker held open. Now the
    claim is released whole: no run directory, no variable, pytest's own
    factory and option untouched, no finisher.
    """

    def moved(_config: _FakeConfig) -> object:
        raise AttributeError("from_config")

    installed = _install_under(tmp_path, monkeypatch, rebuild=moved)
    try:
        owned_nothing = installed.run is None
        assert owned_nothing, "a failed rebuild still returned a claim"
        runs_left = len(list(installed.root.glob(RUN_PREFIX + "*")))
        assert runs_left == 0, "a failed rebuild left a claimed run directory"
        env_named = bool(os.environ.get(ENV_TEMPROOT)) or bool(os.environ.get(ENV_NESTED))
        assert not env_named, "a failed rebuild left the temp-root variables set"
        option_restored = installed.config.option.basetemp is None
        assert option_restored, "a failed rebuild left the base temp option amended"
        factory = installed.config._tmp_path_factory  # noqa: SLF001
        factory_kept = factory is installed.config.original_factory
        assert factory_kept, "a failed rebuild replaced pytest's own factory"
        finisher = own_temp_root.PLUGIN_NAME in installed.config.pluginmanager.registered
        assert not finisher, "a failed rebuild still registered the finisher"
    finally:
        _release(installed)


def test_install_reclaims_a_dead_run_under_the_legacy_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every install sweeps the CS-1319 root, so a run killed under it is not orphaned."""
    legacy = tmp_path / own_temp_root.LEGACY_ROOT_NAME
    dead = legacy / (own_temp_root.LEGACY_RUN_PREFIX + "1-dead")
    (dead / "pytest-of-someone" / "pytest-0").mkdir(parents=True)
    (dead / ALIVE_NAME).write_bytes(b"")
    _age(dead, STALE_AFTER_S + HOUR)
    installed = _install_under(tmp_path, monkeypatch)
    try:
        left = dead.exists()
        assert not left, "install did not sweep the dead run under the legacy root"
    finally:
        _release(installed)
