"""The repository's own git configuration must not carry test-fixture residue.

WHY THIS MODULE EXISTS, MEASURED 2026-09-11. The shared configuration at
``.git/config`` was found carrying ``core.bare = true`` in its ``[core]``
section plus a ``[user]`` block naming ``Gate Test <gate@example.invalid>`` and
``[commit] gpgsign = false``. That triple is exactly what this suite's own
throwaway-repo fixtures write - the ``throwaway_repo``, ``hooked_repo`` and
``tracked_hook_repo`` fixtures in tests/test_precommit_gate.py each write the
same three keys - so something ran a fixture's configuration writes against the
real repository rather than against a directory under tmp_path.

CITED BY SYMBOL RATHER THAN BY LINE, deliberately. A line pointer at a tracked
python module rots the first time anything above it moves, and this project's
guard refuses a repoint even when the line content carries over unchanged.

WHAT THAT COSTS, and why it is worth a tier-0-shaped guard. While ``core.bare``
is set, EVERY git command in the main checkout and in every worktree fails with
``fatal: this operation must be run in a work tree`` and ``git worktree list``
labels the main checkout ``(bare)``. It reads exactly like repository
corruption and it is not. Every lane cycle after the one that stranded it died
in seconds, because a launcher that cannot run ``git worktree add`` cannot
launch. A stranded ``[user]`` block is quieter and worse: it misattributes
every commit made afterwards to a fixture identity, and three commits were
authored that way before anyone noticed.

THIS GUARD DOES NOT NAME A CULPRIT, AND THAT IS DELIBERATE. Three mechanisms
were proposed and all three were refuted by measurement on 2026-09-11:

  * ``GIT_DIR`` inherited from a hook. Measured on this toolchain: ``pre-push``
    exports only ``GIT_EXEC_PATH`` and ``GIT_PREFIX``, and ``pre-commit`` adds
    ``GIT_AUTHOR_*``, ``GIT_EDITOR`` and a RELATIVE ``GIT_INDEX_FILE``. Neither
    exports ``GIT_DIR`` at all.
  * The suite mutating the shared config under ``-n auto``. Measured: the
    thirteen git-touching modules, run with ``-n auto --dist loadfile`` and a
    20ms watcher on the shared config, produced 468 passed and ZERO writes.
  * The same, run from inside a worktree, where ``.git`` is a FILE and the
    config is shared. Also zero writes.

So the guard is written against the STATE rather than against any code path.
A guard that waits for a mechanism to be identified protects nothing in the
meantime, and this state has already broken the box once.

THE READER IS ASKED OF GIT, NEVER PARSED OUT OF THE FILE. ``git config --get``
applies git's own precedence and its own spelling rules; a hand-rolled INI
parse would disagree with git the first time a value is quoted, a section is
repeated, or an include is followed.

AND IT IS ASKED OF THE COMMON DIRECTORY. ``Path(__file__).parents[1]`` is the
WORKTREE when a lane or a subagent runs this suite, and ``core.bare`` lives in
the SHARED config that every worktree reads. Deriving the target from this
file's own location would grade the wrong repository from exactly the place the
incident happened.

EVERY NEGATIVE HERE IS FRONTED BY A CONTROL. An arm asserting "this repository
is not bare" passes identically when the reader is broken, when git is missing,
and when the question was never really asked - so each negative is paired with
an arm that plants the condition in a throwaway repository and requires the
SAME reader to see it. Without the pair, a green result is a statement about
nothing.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

GIT_TIMEOUT = 120

FIXTURE_EMAIL = "gate@example.invalid"
FIXTURE_NAME = "Gate Test"

# Repository-locating variables. A child that inherits one of these answers
# about whatever repository the variable names rather than about the directory
# it was pointed at, which would make every control arm below grade the real
# repository instead of its own throwaway one.
#
# COMPARED UPPER-CASED. Windows folds environment keys and ``dict(os.environ)``
# hands back upper-case ones, so popping a mixed-case spelling removes nothing
# and the scrub reports success while measuring nothing.
REPO_LOCATING = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_CEILING_DIRECTORIES",
    }
)


def scrubbed_env() -> dict[str, str]:
    """This process's environment with every repository-locating variable gone."""
    env = dict(os.environ)
    for name in [key for key in env if key.upper() in REPO_LOCATING]:
        env.pop(name)
    return env


def run_git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run one git command in ``cwd`` with no inherited repository pointer."""
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=False,
        env=scrubbed_env(),
    )


def config_value(repo: Path, key: str) -> str | None:
    """What git reports for ``key`` in ``repo``, or None when it is unset.

    Returns:
        The trimmed value, or None when git has no value for the key.
    """
    done = run_git("config", "--get", key, cwd=repo)
    if done.returncode != 0:
        return None
    return done.stdout.strip()


def common_dir(start: Path) -> Path:
    """The directory holding the SHARED config that ``start`` reads.

    In a worktree this is the main checkout's ``.git``, not the worktree's own
    ``.git`` file, which is the whole reason this is asked of git.

    Returns:
        The resolved common git directory.
    """
    done = run_git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=start)
    assert done.returncode == 0, "git could not resolve the common git directory"
    resolved = done.stdout.strip()
    assert resolved, "git reported an empty common git directory"
    return Path(resolved).resolve()


@pytest.fixture
def shared_config_owner() -> Path:
    """The working tree whose SHARED configuration this module grades."""
    return common_dir(Path(__file__).resolve().parent).parent


@pytest.fixture
def planted_repo(tmp_path: Path) -> Path:
    """A throwaway repository carrying exactly the residue the incident left."""
    root = tmp_path / "planted"
    root.mkdir()
    assert run_git("init", "-q", "-b", "main", cwd=root).returncode == 0
    for key, value in (
        ("core.bare", "true"),
        ("user.email", FIXTURE_EMAIL),
        ("user.name", FIXTURE_NAME),
    ):
        assert run_git("config", key, value, cwd=root).returncode == 0, key
    return root


# --------------------------------------------------------------------------
# core.bare
# --------------------------------------------------------------------------


def test_the_bare_reader_sees_a_planted_bare_flag(planted_repo: Path) -> None:
    """CONTROL. The reader must report a bare flag that IS there.

    Without this, the arm below passes when the reader is broken, when git
    cannot be spawned, and when the key name is misspelled.
    """
    assert config_value(planted_repo, "core.bare") == "true"


def test_this_repository_is_not_configured_bare(shared_config_owner: Path) -> None:
    """The shared config must not carry core.bare.

    A stranded ``core.bare = true`` makes every git command in the main
    checkout and in every worktree fail as though the repository were corrupt.
    """
    observed = config_value(shared_config_owner, "core.bare")
    assert observed in (None, "false"), (
        "the shared git config carries core.bare="
        f"{observed!r}. Every git command in this checkout and in every "
        "worktree will fail with 'this operation must be run in a work tree'. "
        "Remove that ONE line from the [core] section of the common .git/config."
    )


# --------------------------------------------------------------------------
# the fixture identity
# --------------------------------------------------------------------------


def test_the_identity_reader_sees_a_planted_fixture_identity(planted_repo: Path) -> None:
    """CONTROL. The reader must report a fixture identity that IS there."""
    assert config_value(planted_repo, "user.email") == FIXTURE_EMAIL
    assert config_value(planted_repo, "user.name") == FIXTURE_NAME


def test_this_repository_does_not_carry_the_fixture_identity(
    shared_config_owner: Path,
) -> None:
    """The shared config must not name the throwaway-repo fixture identity.

    This one is quiet rather than loud: nothing fails, and every commit made
    afterwards is simply attributed to a test fixture. Three were, before the
    residue was noticed.
    """
    email = config_value(shared_config_owner, "user.email")
    name = config_value(shared_config_owner, "user.name")
    residue = (
        "which this suite's throwaway-repo fixtures write. Every commit made "
        "from this checkout is being misattributed. Remove the [user] block "
        "from the common .git/config and re-author any commit already made "
        "under it."
    )
    assert email != FIXTURE_EMAIL, (
        f"the shared git config sets user.email to the fixture address, {residue}"
    )
    assert name != FIXTURE_NAME, (
        f"the shared git config sets user.name to the fixture name, {residue}"
    )
