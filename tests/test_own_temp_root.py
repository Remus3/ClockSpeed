"""CS-1319 - the tree-owned temp root's mechanism: claim, sweep, remove, finish.

The wiring - that a real run lands under the root - is graded in
``tests/test_suite_temp_root.py``. Here every arm drives
``tests/own_temp_root.py`` against a parent directory under ``tmp_path`` and a
plain dict standing in for the environment, so no arm touches the real root
or the real process environment.
"""

from __future__ import annotations

import os
import stat
import time
from pathlib import Path

import pytest

from tests import own_temp_root
from tests.own_temp_root import (
    ALIVE_NAME,
    ENV_NESTED,
    ENV_TEMPROOT,
    FAILED_NAME,
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


@pytest.mark.parametrize(
    ("exitstatus", "kept"), [(0, False), (1, True), (2, True), (3, True), (4, False), (5, False)]
)
def test_finish_removes_a_clean_run_and_keeps_a_failed_one(
    tmp_path: Path, exitstatus: int, kept: bool
) -> None:
    """A failed TOP-LEVEL run's retained tmp_paths are the record of the failure.

    Failed, interrupted and internal-error runs keep theirs; a usage error and
    an empty collection have no record to keep, so they are removed like a
    clean run (the second adversary's note: exit 5 kept an empty directory).

    ``tmp_path_retention_policy = "failed"`` keeps exactly those; removing the
    run directory on failure would throw that record away. A kept directory is
    bounded by the sweep instead.
    """
    run = own_temp_root.claim(tmp_path, {})
    if run is None:
        pytest.fail("the claim owned nothing")
    (run.path / "pytest-of-someone").mkdir()
    own_temp_root.finish(run, exitstatus)
    assert run.path.exists() == kept, "finish did not follow the exit status"


def test_a_top_level_claim_marks_the_environment_for_nested_runs(tmp_path: Path) -> None:
    """The marker is what tells a pytest spawned by a test that it is nested."""
    env: dict[str, str] = {}
    run = own_temp_root.claim(tmp_path, env)
    marked = run is not None and not run.nested and env.get(ENV_NESTED) == "1"
    assert marked, "a top-level claim did not mark the environment"


@pytest.mark.parametrize("exitstatus", [0, 1, 2])
def test_a_nested_run_removes_its_directory_whatever_its_exit_status(
    tmp_path: Path, exitstatus: int
) -> None:
    """A pytest a test spawned - often failing ON PURPOSE - leaves nothing behind.

    MEASURED on the first whole-suite run under this mechanism: 36 nested runs
    that cleared the temp-root variable kept their run directories, because
    the arm that spawned them expected a failing exit status. Their tmp_paths
    are not a record of anything; the spawning test grades their output.
    """
    run = own_temp_root.claim(tmp_path, {ENV_NESTED: "1"})
    if run is None:
        pytest.fail("the nested claim owned nothing")
    (run.path / "pytest-of-someone").mkdir()
    own_temp_root.finish(run, exitstatus)
    left = run.path.exists()
    assert not left, "a nested run left its directory behind"


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
        own_temp_root.finish(live, 0)
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
        own_temp_root.finish(live, 0)
    assert removed == 0, "the sweep counted a live run as removed"
    assert work_kept, "the sweep emptied a live run because it was old"


@pytest.mark.parametrize("ahead_s", [GRACE_S + 600, STALE_AFTER_S + HOUR])
def test_the_sweep_never_reaches_through_a_run_named_link(tmp_path: Path, ahead_s: float) -> None:
    """A ``run-*`` entry that is a junction is left alone, and so is its target.

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


def test_a_failed_runs_record_survives_the_next_claim_until_it_is_stale(tmp_path: Path) -> None:
    """The next run's sweep does not throw away the record a failed run kept.

    The second adversary's should-fix: the failed run's owner has exited, so
    its marker unlinks and the very next claim - any pytest, a nested one
    included - reclaimed the directory at once. A failed run is marked, and a
    marked run is kept until :data:`STALE_AFTER_S`, on every platform.
    """
    failed = own_temp_root.claim(tmp_path, {})
    if failed is None:
        pytest.fail("the claim owned nothing")
    record = failed.path / "pytest-of-someone" / "pytest-0" / "test_flake0" / "written.txt"
    record.parent.mkdir(parents=True)
    record.write_bytes(b"what the flake wrote")
    own_temp_root.finish(failed, 1)
    marked = (failed.path / FAILED_NAME).is_file()
    assert marked, "a failed run was not marked"
    _age(failed.path, GRACE_S + 60)
    nxt = own_temp_root.claim(tmp_path, {})
    if nxt is None:
        pytest.fail("the next claim owned nothing")
    own_temp_root.finish(nxt, 0)
    kept_by_next = record.is_file()
    assert kept_by_next, "the next claim swept a failed run's record"
    _age(failed.path, STALE_AFTER_S)
    removed = own_temp_root.sweep(tmp_path)
    gone = failed.path.exists()
    assert removed == 1, "the sweep did not reclaim the stale failed run"
    assert not gone, "a stale failed run was kept forever"


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


def test_only_the_newest_failed_run_is_kept(tmp_path: Path) -> None:
    """Failed runs do not pile up: the sweep keeps the newest one's record only.

    MEASURED on the first whole suite of this candidate: one failed run kept
    about sixteen thousand directories, most of them module-scoped temp
    directories the retention policy never prunes. A night of failing runs
    inside the stale age would stack those; the newest failure is the one a
    session investigates.
    """
    claims = [own_temp_root.claim(tmp_path, {}) for _ in range(3)]
    runs = [run for run in claims if run is not None]
    if len(runs) != len(claims):
        pytest.fail("a claim owned nothing")
    for run, age in zip(runs, (GRACE_S + 900, GRACE_S + 600, GRACE_S + 300), strict=True):
        own_temp_root.finish(run, 1)
        _age(run.path, age)
    removed = own_temp_root.sweep(tmp_path)
    survivors = sorted(path.name for path in tmp_path.iterdir())
    newest = runs[-1].path.name
    assert removed == len(runs) - 1, "the sweep did not reclaim every older failed run"
    assert survivors == [newest], "the sweep kept a failed run other than the newest"
