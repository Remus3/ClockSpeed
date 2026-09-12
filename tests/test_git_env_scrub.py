"""The suite's git helpers must not act on a repository they were never handed.

THE INCIDENT THIS GRADES, MEASURED 2026-09-11. A push of ``cs964-seam`` from its
worktree ran the pre-push suite, and the run left ``core.bare = true`` plus a
``[user]`` block naming the throwaway-repo fixture identity in the SHARED
``.git/config``. Afterwards every git command in every checkout failed with
``fatal: this operation must be run in a work tree``.

THE MECHANISM, AND THE HALF OF IT THAT WAS MISSED TWICE. ``git`` exports
``GIT_DIR`` to the pre-push hook WHEN AND ONLY WHEN the push comes from a linked
worktree. Measured side by side, same repository, same hook:

    push from the main checkout   GIT_EXEC_PATH, GIT_PREFIX
    push from a linked worktree   GIT_EXEC_PATH, GIT_PREFIX, GIT_DIR

Two separate investigations - one here, one on a sibling tree - measured only
the main-checkout case, concluded "no hook exports GIT_DIR", and recorded that
as a refutation of the whole mechanism. Both were measuring the one arrangement
in which the bug cannot fire. A negative measured in the wrong configuration is
not a refutation, and the cost of that particular mistake was a second outage.

WHAT THE ARMS BELOW DO. They plant ``GIT_DIR`` at a DECOY repository and then
ask a helper to build a throwaway one. The decoy is the oracle: if the helper
leaks, ``git init --bare`` re-initialises the decoy rather than the directory it
was aimed at, and the decoy's ``core.bare`` turns true. The decoy is checked
rather than the throwaway, because a leaked call can leave the throwaway looking
perfectly ordinary while the damage lands somewhere else entirely - which is
precisely how this went unnoticed.

EVERY ARM HERE FAILS WITHOUT THE SCRUB. That was measured before the scrub was
applied, not asserted afterwards, and it is the reason these arms exist rather
than a test that merely calls ``scrub`` and checks its output.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tests.git_env import REPO_LOCATING, scrub, scrubbed_env

GIT_TIMEOUT = 120


def plain_git(*args: str, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run git with EXACTLY the environment given, scrubbing nothing."""
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=False,
        env=env,
    )


def bare_flag(repo: Path) -> str | None:
    """What ``core.bare`` reads as in ``repo``, asked with no inherited pointer."""
    done = plain_git("config", "--get", "core.bare", cwd=repo, env=scrubbed_env())
    return done.stdout.strip() if done.returncode == 0 else None


@pytest.fixture
def decoy(tmp_path: Path) -> Path:
    """A repository that NOTHING in these arms is ever asked to act on.

    It stands in for the real checkout. An arm that finds this repository
    changed has found the leak, wherever the call was aimed.
    """
    root = tmp_path / "decoy"
    root.mkdir()
    started = plain_git("init", "-q", "-b", "main", cwd=root, env=scrubbed_env())
    assert started.returncode == 0, "the decoy repository could not be initialised"
    assert bare_flag(root) in (None, "false"), "the decoy started out bare"
    return root


# --------------------------------------------------------------------------
# the scrub itself
# --------------------------------------------------------------------------


def test_the_scrub_removes_a_planted_pointer_whatever_its_casing() -> None:
    """CONTROL. Windows folds env keys, so a case-sensitive pop removes nothing.

    Without this arm a scrub that pops the exact spelling it was handed passes
    every other test here while removing nothing on the platform that matters.
    """
    planted = {"GIT_DIR": "x", "Git_Work_Tree": "y", "PATH": "keep"}

    scrubbed = scrub(dict(planted))

    assert "PATH" in scrubbed, "the scrub removed something it was not asked to"
    assert not [key for key in scrubbed if key.upper() in REPO_LOCATING], (
        f"the scrub left a repository-locating variable behind: {sorted(scrubbed)}"
    )


def test_the_scrub_keeps_the_variables_that_isolate_a_fixture() -> None:
    """The isolating variables survive the scrub.

    GIT_CONFIG_GLOBAL and GIT_CONFIG_SYSTEM are how a fixture cuts the
    operator's own configuration off; removing them would undo the isolation
    the scrub exists to protect.
    """
    kept = scrub({"GIT_CONFIG_GLOBAL": "g", "GIT_CONFIG_SYSTEM": "s", "GIT_DIR": "d"})

    assert kept == {"GIT_CONFIG_GLOBAL": "g", "GIT_CONFIG_SYSTEM": "s"}


# --------------------------------------------------------------------------
# the incident, in miniature
# --------------------------------------------------------------------------


def test_an_inherited_git_dir_really_does_relocate_an_init(decoy: Path, tmp_path: Path) -> None:
    """CONTROL, AND THE ONE THAT MAKES THE ARM BELOW MEAN ANYTHING.

    It does the damage ON PURPOSE, with the pointer left in place, so the arm
    below is known to be asking a question that has a wrong answer available.
    Without this, an arm reporting "the decoy is not bare" reads identically
    when git ignores GIT_DIR, when the decoy was never reachable, and when the
    scrub works.
    """
    target = tmp_path / "aimed-at"
    target.mkdir()
    leaky = dict(os.environ)
    leaky["GIT_DIR"] = str(decoy / ".git")

    plain_git("init", "-q", "--bare", cwd=target, env=leaky)

    assert bare_flag(decoy) == "true", (
        "a planted GIT_DIR did not relocate git init on this toolchain, so the "
        "arm below cannot distinguish a working scrub from an unreachable decoy"
    )


def test_a_scrubbed_environment_keeps_an_init_inside_the_directory_it_was_aimed_at(
    decoy: Path, tmp_path: Path
) -> None:
    """THE ARM. The same call, through the scrub, must leave the decoy alone."""
    target = tmp_path / "aimed-at"
    target.mkdir()
    leaky = dict(os.environ)
    leaky["GIT_DIR"] = str(decoy / ".git")

    plain_git("init", "-q", "--bare", cwd=target, env=scrub(leaky))

    assert bare_flag(decoy) in (None, "false"), (
        "a throwaway git init reached the decoy repository through an inherited "
        "GIT_DIR. In the real suite the decoy is this checkout, and the flag it "
        "just acquired makes every git command in every worktree fail."
    )
    assert (target / "config").is_file(), "the init did not land in its own directory"


def test_a_scrubbed_environment_keeps_a_config_write_inside_its_own_repository(
    decoy: Path, tmp_path: Path
) -> None:
    """The other half of the incident: the stranded ``[user]`` block.

    ``git config`` relocates through ``GIT_DIR`` exactly as ``git init`` does,
    and the fixture identity it wrote into the shared config misattributed three
    commits before anyone noticed.
    """
    throwaway = tmp_path / "throwaway"
    throwaway.mkdir()
    assert plain_git("init", "-q", "-b", "main", cwd=throwaway, env=scrubbed_env()).returncode == 0
    leaky = dict(os.environ)
    leaky["GIT_DIR"] = str(decoy / ".git")

    plain_git("config", "user.email", "gate@example.invalid", cwd=throwaway, env=scrub(leaky))

    planted = plain_git("config", "--get", "user.email", cwd=decoy, env=scrubbed_env())
    assert planted.stdout.strip() != "gate@example.invalid", (
        "a throwaway config write reached the decoy repository. In the real "
        "suite that is the shared config every worktree reads, and every commit "
        "made afterwards is attributed to a test fixture."
    )
