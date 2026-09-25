"""CS-1188 - the walk excludes the .git entry whether it is a file or a directory.

THE ACCEPTANCE, verbatim from the item note: "the walk excludes the .git entry
whether it is a file or a directory, with an arm that builds a linked worktree
in tmp_path and passes there, and a control that a genuine untracked extra in
the same worktree still reddens."

WHY IT WAS RED. `WALK_SKIP_DIRS` names `.git`, but `_skip_dir_reason` is the
only place it is consulted, and that runs for DIRECTORIES. A linked worktree
carries its marker as a FILE holding a gitdir pointer, so the file branch of
`_walk` collected it and the parity arm in `test_drift_guard_data.py` reported
it as an extra - in every linked worktree, never in a plain clone.

Every repository here is built under tmp_path with the operator's global and
system git configuration cut off, and every linked worktree is removed with
`git worktree remove` before tmp_path is torn down.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

from tests import conftest
from tests.git_env import relocates

DRIFT_GUARD_SOURCE = Path(__file__).resolve().parents[2] / "tools" / "drift_guard.py"


def _load_drift_guard() -> ModuleType:
    """Load tools/drift_guard.py from its file; tools/ is not a package."""
    name = "clockspeed_drift_guard_walk_worktree"
    spec = importlib.util.spec_from_file_location(name, DRIFT_GUARD_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {DRIFT_GUARD_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


drift_guard = _load_drift_guard()

#: The three authority states `_walk` distinguishes: git asked for itself,
#: git answering that nothing is ignored, and git unreachable (the floor alone).
_ASK_GIT = "ask-git"
AUTHORITIES = (_ASK_GIT, "git-says-nothing-ignored", "no-git")


def _git(root: Path, *args: str) -> None:
    """Run one git subcommand in ``root``; skip when git is absent, fail on non-zero."""
    proc = conftest.run_git(root, *args)
    if proc is None:
        pytest.skip("git is not installed, so no repository can be built")
    assert proc.returncode == 0, f"control: git {args[0]} exited {proc.returncode}"


def _indexed(root: Path) -> set[str]:
    """What git's index lists in ``root``, as root-relative posix strings."""
    proc = conftest.run_git(root, "ls-files")
    if proc is None:
        pytest.skip("git is not installed, so the index cannot be asked")
    assert proc.returncode == 0, f"control: git ls-files exited {proc.returncode}"
    return {line for line in proc.stdout.decode("utf-8", "replace").splitlines() if line}


def _walk(root: Path, authority: str) -> tuple[set[str], dict[str, str]]:
    """Walk ``root`` under one authority; return (files, skip path -> reason)."""
    if authority == _ASK_GIT:
        files, skips = drift_guard._walk(root)  # noqa: SLF001
    else:
        ignored: frozenset[str] | None = None
        if authority == "git-says-nothing-ignored":
            ignored = frozenset()
        files, skips = drift_guard._walk(root, worktrees=(), ignored=ignored)  # noqa: SLF001
    walked = {path.relative_to(root).as_posix() for path in files}
    return walked, {skip["path"]: skip["reason"] for skip in skips}


@pytest.fixture
def repos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Path, Path]]:
    """A main checkout and a SIBLING linked worktree of it, both under tmp_path.

    The sibling placement keeps the main walk free of the worktree, so each
    tree's walk is compared against its own index and nothing else.
    """
    for name in [key for key in os.environ if relocates(key)]:
        monkeypatch.delenv(name)
    empty_config = tmp_path / "empty.gitconfig"
    empty_config.write_bytes(b"")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    main = tmp_path / "main"
    (main / "docs").mkdir(parents=True)
    (main / "top.md").write_bytes(b"# clean\n")
    (main / "docs" / "deep.md").write_bytes(b"# deep\n")
    (main / ".gitignore").write_bytes(b"*.log\n")
    for args in (
        ("init", "--quiet"),
        ("config", "user.email", "suite@example.invalid"),
        ("config", "user.name", "suite"),
        ("config", "commit.gpgsign", "false"),
        ("add", "--", "top.md", "docs/deep.md", ".gitignore"),
        ("commit", "--quiet", "--no-verify", "-m", "base"),
    ):
        _git(main, *args)
    linked = tmp_path / "linked"
    _git(main, "worktree", "add", "--quiet", "--detach", str(linked))
    # An ignored file on disk in the worktree: git's answer, not the marker
    # rule, must be what keeps it out.
    (linked / "run.log").write_bytes(b"log\n")
    try:
        yield main, linked
    finally:
        conftest.run_git(main, "worktree", "remove", "--force", str(linked))


def test_the_linked_worktree_marker_is_a_file_and_the_main_one_a_directory(
    repos: tuple[Path, Path],
) -> None:
    """The control every arm below rests on: the two kinds are really present."""
    main, linked = repos
    assert (linked / ".git").is_file()
    assert (main / ".git").is_dir()


@pytest.mark.parametrize("authority", AUTHORITIES)
def test_the_walk_of_a_linked_worktree_matches_its_index(
    repos: tuple[Path, Path], authority: str
) -> None:
    """CS-1188: the .git FILE is not collected, under every authority.

    Where git ANSWERS that nothing is ignored, `run.log` is kept - git decides
    and the floor only names a class - so the comparison there is against the
    index plus that one file. With git unreachable the floor's `*.log` prunes
    it. Either way the point is that `.git` is absent whichever authority
    decides.
    """
    _main, linked = repos
    walked, _skips = _walk(linked, authority)
    expected = _indexed(linked)
    if authority == "git-says-nothing-ignored":
        expected |= {"run.log"}
    assert ".git" not in walked, sorted(walked)
    extra = sorted(walked - expected)
    missing = sorted(expected - walked)
    assert extra == [], extra
    assert missing == [], missing


def test_the_walk_of_a_plain_checkout_excludes_its_git_directory(
    repos: tuple[Path, Path],
) -> None:
    """CS-1188: the directory half, unchanged - the marker as a DIRECTORY is pruned."""
    main, _linked = repos
    walked, skips = _walk(main, _ASK_GIT)
    assert walked == _indexed(main), sorted(walked)
    assert skips.get(".git/") == "excluded directory (tooling or vcs internals)", skips


def test_the_marker_file_is_reported_as_a_skip_not_discarded(
    repos: tuple[Path, Path],
) -> None:
    """CS-1188: pruning is REPORTED, and a file record carries no trailing slash."""
    _main, linked = repos
    _walked, skips = _walk(linked, _ASK_GIT)
    assert ".git" in skips, sorted(skips)
    assert skips[".git"] == drift_guard.VCS_MARKER_FILE_REASON
    assert ".git/" not in skips, sorted(skips)


def test_a_genuine_untracked_extra_in_the_same_worktree_still_reddens(
    repos: tuple[Path, Path],
) -> None:
    """The acceptance's control: the fix did not simply stop reporting extras.

    An untracked, unignored file beside the marker must still be walked and so
    still differ from the index - exactly the difference the parity arm reds on.
    The marker is set aside in the comparison so this control grades the
    extras rule alone and stays green whether or not the marker is excluded.
    """
    _main, linked = repos
    (linked / "stray.md").write_bytes(b"# not indexed\n")
    walked, _skips = _walk(linked, _ASK_GIT)
    assert sorted(walked - _indexed(linked) - {".git"}) == ["stray.md"]


def test_a_nested_linked_worktree_is_still_pruned_by_the_boundary_rule(
    repos: tuple[Path, Path],
) -> None:
    """The at-any-depth decision's control: a nested .git FILE never reaches the file branch.

    Its directory is pruned first as a checkout root of its own, so a nested
    linked worktree's marker never reaches the name rule. The name rule does
    widen in one shape: a nested .git the boundary test cannot see (a dangling
    symlink) is skipped where it was walked. The registration is withheld
    (worktrees=()) so the marker rule, not the registry, is graded.
    """
    main, _linked = repos
    _git(main, "worktree", "add", "--quiet", "--detach", "inside/nested")
    nested = main / "inside" / "nested"
    try:
        assert (nested / ".git").is_file()
        files, skips = drift_guard._walk(main, worktrees=(), ignored=frozenset())  # noqa: SLF001
        walked = {path.relative_to(main).as_posix() for path in files}
        reasons = {skip["path"]: skip["reason"] for skip in skips}
        assert not any(path.startswith("inside/") for path in walked), sorted(walked)
        assert reasons.get("inside/nested/") == drift_guard.BOUNDARY_REASON, reasons
    finally:
        conftest.run_git(main, "worktree", "remove", "--force", str(nested))
