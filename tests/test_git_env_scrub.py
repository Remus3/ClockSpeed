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
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.git_env import REPO_LOCATING, gnu_timeout_first, scrub, scrubbed_env

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
    code = plain_git("init", "-q", "-b", "main", cwd=throwaway, env=scrubbed_env()).returncode
    assert code == 0
    leaky = dict(os.environ)
    leaky["GIT_DIR"] = str(decoy / ".git")

    plain_git("config", "user.email", "gate@example.invalid", cwd=throwaway, env=scrub(leaky))

    planted = plain_git("config", "--get", "user.email", cwd=decoy, env=scrubbed_env())
    assert planted.stdout.strip() != "gate@example.invalid", (
        "a throwaway config write reached the decoy repository. In the real "
        "suite that is the shared config every worktree reads, and every commit "
        "made afterwards is attributed to a test fixture."
    )


# --------------------------------------------------------------------------
# CS-1154 - the second channel: config injected by `git -c`
# --------------------------------------------------------------------------


def hooked_throwaway(root: Path) -> Path:
    """A repo whose REPO-LOCAL core.hooksPath points at a hook that refuses.

    The hook is the oracle. A commit that succeeds here is a commit whose hook
    never ran, and that is indistinguishable at the exit code from a gate that
    examined the change and approved it.
    """
    root.mkdir()
    code = plain_git("init", "-q", "-b", "main", cwd=root, env=scrubbed_env()).returncode
    assert code == 0
    for key, value in (
        ("user.email", "gate@example.invalid"),
        ("user.name", "Gate Test"),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", "own-hooks"),
    ):
        code = plain_git("config", key, value, cwd=root, env=scrubbed_env()).returncode
        assert code == 0
    hooks = root / "own-hooks"
    hooks.mkdir()
    hook = hooks / "pre-commit"
    hook.write_bytes(b"#!/bin/sh\nprintf 'refused by the repo-local hook\n' >&2\nexit 1\n")
    hook.chmod(0o755)
    (root / "seed.txt").write_bytes(b"seed\n")
    code = plain_git("add", "seed.txt", cwd=root, env=scrubbed_env()).returncode
    assert code == 0
    seeded = plain_git("commit", "-q", "-m", "seed", "--no-verify", cwd=root, env=scrubbed_env())
    assert seeded.returncode == 0, seeded.stderr
    (root / "change.txt").write_bytes(b"change\n")
    code = plain_git("add", "change.txt", cwd=root, env=scrubbed_env()).returncode
    assert code == 0
    return root


def test_an_inherited_config_override_really_does_disarm_a_repo_local_hook(
    tmp_path: Path,
) -> None:
    """CONTROL. `git -c` travels to every child as GIT_CONFIG_PARAMETERS.

    It does the damage ON PURPOSE so the arm below is known to be asking a
    question that has a wrong answer available. A command-line override OUTRANKS
    repository configuration, so an inherited one re-points core.hooksPath at a
    directory the throwaway repo does not have and the commit sails through with
    no hook output on either stream - which reads exactly like a gate that ran
    and approved.
    """
    repo = hooked_throwaway(tmp_path / "throwaway")
    leaky = scrubbed_env()
    leaky["GIT_CONFIG_PARAMETERS"] = "'core.hooksPath=absent-hooks'"

    done = plain_git("commit", "-m", "change", cwd=repo, env=leaky)

    assert done.returncode == 0, (
        "an inherited GIT_CONFIG_PARAMETERS did not disarm the repo-local hook "
        "on this toolchain, so the arm below cannot distinguish a working scrub "
        "from a hook that was never armed"
    )
    assert "refused by the repo-local hook" not in done.stderr, (
        "the hook ran anyway, so this control did no damage and proves nothing"
    )


def test_a_scrubbed_environment_leaves_a_repo_local_hook_armed(tmp_path: Path) -> None:
    """THE ARM. The same commit, through the scrub, must still be refused.

    CS-1154. `git -c core.hooksPath=.githooks push` exports its override to the
    pre-push hook, the suite inherits it, and every throwaway repo in
    tests/test_precommit_gate.py loses its hook - so the world-name PII arm
    accepted a commit it exists to block, three pushes running, with an empty
    stderr and no diagnostic anywhere.
    """
    repo = hooked_throwaway(tmp_path / "throwaway")
    leaky = scrubbed_env()
    leaky["GIT_CONFIG_PARAMETERS"] = "'core.hooksPath=absent-hooks'"

    done = plain_git("commit", "-m", "change", cwd=repo, env=scrub(leaky))

    assert done.returncode != 0, (
        "a repo-local pre-commit hook was disarmed by an inherited command-line "
        "override that the scrub let through. In the real suite that is every "
        "gate arm in tests/test_precommit_gate.py reporting PASS over a hook "
        "that never ran."
    )
    assert "refused by the repo-local hook" in done.stderr, done.stderr


def test_the_scrub_removes_an_injected_config_override_in_every_spelling() -> None:
    """The numbered pair form relocates identically and is not one fixed name.

    GIT_CONFIG_COUNT with GIT_CONFIG_KEY_n / GIT_CONFIG_VALUE_n is the same
    injection channel as GIT_CONFIG_PARAMETERS, so a scrub written as a fixed
    set of names covers one spelling and leaves the other armed.
    """
    planted = {
        "GIT_CONFIG_PARAMETERS": "'core.hooksPath=x'",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": "x",
        "Git_Config_Parameters": "'core.hooksPath=y'",
        "GIT_CONFIG_GLOBAL": "keep",
        "GIT_CONFIG_SYSTEM": "keep",
        "PATH": "keep",
    }

    scrubbed = scrub(dict(planted))

    assert scrubbed == {
        "GIT_CONFIG_GLOBAL": "keep",
        "GIT_CONFIG_SYSTEM": "keep",
        "PATH": "keep",
    }, f"the scrub left an injected override behind: {sorted(scrubbed)}"


# --- CS-1187: Windows' own timeout must not answer for the hooks ------------

#: GNU timeout's exit status when its bound expires; the hooks test for it.
GNU_TIMEOUT_EXPIRED = 124


def bound_expires(env: dict[str, str]) -> bool:
    """Whether the first ``timeout`` on ``env``'s PATH returns 124 on expiry.

    The same behavioural check the tracked hooks make before trusting the
    binary: a GNU timeout returns 124 when a short bound runs out. Windows'
    System32 ``timeout`` is a pause command and never does.
    """
    search = next(value for key, value in env.items() if key.upper() == "PATH")
    found = shutil.which("timeout", path=search)
    if found is None:
        return False
    proc = subprocess.run(
        [found, "-k", "1", "0.05", "sleep", "5"],
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=GIT_TIMEOUT,
        check=False,
    )
    return proc.returncode == GNU_TIMEOUT_EXPIRED


def shadowed_then_repaired() -> tuple[bool, bool]:
    """Plant System32 first on PATH; grade it before and after the repair.

    THE ENVIRONMENT NEVER REACHES THE ASSERTING FRAME. It is built and graded
    here, and only two booleans go back, so no failure report can render a
    variable's value (CLAUDE.md non-negotiable 13).
    """
    env = dict(os.environ)
    path_key = next(key for key in env if key.upper() == "PATH")
    system32 = Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32"
    env[path_key] = str(system32) + os.pathsep + env[path_key]
    return bound_expires(env), bound_expires(gnu_timeout_first(env))


@pytest.mark.skipif(os.name != "nt", reason="System32 shadowing exists only on Windows")
def test_system32_first_on_path_still_gives_the_hooks_a_gnu_timeout() -> None:
    """CS-1187 D4: a never-seen machine put System32 ahead of Git's usr/bin.

    The hooks then refused every probe ("no working GNU timeout was found") and
    thirteen hook arms went red. The control proves the shadowing is real on
    this machine before the repaired environment is graded.
    """
    shadowed, repaired = shadowed_then_repaired()
    assert not shadowed, "control: System32 first on PATH did not shadow GNU timeout"
    assert repaired, "gnu_timeout_first left no GNU timeout first on PATH"
