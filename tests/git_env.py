"""One owner for the git environment a test's child process is allowed to inherit.

WHY THIS EXISTS, MEASURED 2026-09-11. ``git push`` FROM A LINKED WORKTREE
exports ``GIT_DIR`` to the pre-push hook, pointing at that worktree's gitdir
under the main checkout. A push from the main checkout exports no such thing.
Measured side by side on this toolchain, same repository, same hook:

    push from the main checkout   GIT_EXEC_PATH, GIT_PREFIX
    push from a linked worktree   GIT_EXEC_PATH, GIT_PREFIX, GIT_DIR

``.githooks/pre-push`` runs ``pytest tests``, so every module in this suite can
run with that variable set. A test helper that spawns ``git`` without saying
what environment it wants inherits the pointer, and ``git init --bare`` then
re-initialises THE REAL REPOSITORY as bare rather than the directory under
tmp_path it was aimed at. ``core.bare`` and any ``git config`` write land in the
config every worktree shares, so the damage is not confined to the worktree that
caused it: every git command in every checkout then fails with ``fatal: this
operation must be run in a work tree``, which reads exactly like repository
corruption.

THAT IS NOT A HYPOTHETICAL. It happened twice - once to a lane worker whose
cycle 1 ran in a worktree, and once to a push of ``cs964-seam`` from its
worktree, which is the run that finally reproduced it under observation.

WHY A DEDICATED MODULE RATHER THAN A LINE IN EACH HELPER. There are more than a
dozen git-spawning helpers across this suite. Thirteen copies of a scrub written
thirteen ways is the fixture drift this project fences by name, and the failure
mode is silent: a helper that scrubs the wrong spelling looks identical to one
that scrubs correctly until the day a worktree pushes.

WHAT IS NOT SCRUBBED, AND WHY. ``GIT_CONFIG_GLOBAL`` and ``GIT_CONFIG_SYSTEM``
are how a fixture CUTS OFF the operator's own configuration, so a scrub that
removed them would undo the isolation it is meant to protect. ``GIT_EXEC_PATH``
locates git's own helper programs; removing it breaks git itself.
``GIT_AUTHOR_*`` name an identity rather than a repository. Only the variables
that RELOCATE a repository are removed.
"""

from __future__ import annotations

import functools
import os
import shutil
import subprocess
from pathlib import Path
from typing import Final

#: Variables that point git at a repository, an index or an object store. Any
#: one of them overrides ``-C`` and the process working directory, so a child
#: that inherits one answers about a repository the caller never named.
#:
#: ``GIT_DIR`` is the one that is actually exported by a worktree push and the
#: one that caused the incident. The rest are here because they relocate the
#: same way and cost nothing to remove - a scrub that waits for each to be
#: demonstrated individually is a scrub that gets extended after each outage.
REPO_LOCATING: Final[frozenset[str]] = frozenset(
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


#: Variables that inject CONFIGURATION rather than a location. ``git -c k=v``
#: exports its overrides through these, and a command-line override OUTRANKS
#: repository configuration - so a child that inherits one is configured by a
#: caller it never heard from. CS-1154 measured the cost: ``git -c
#: core.hooksPath=.githooks push`` handed that override to the pre-push suite,
#: every throwaway repo in ``tests/test_precommit_gate.py`` lost its repo-local
#: hook, and the world-name PII arm accepted the commit it exists to block with
#: an empty stderr and no diagnostic anywhere.
#:
#: ``GIT_CONFIG_GLOBAL`` and ``GIT_CONFIG_SYSTEM`` are deliberately NOT here.
#: They cut the operator's own configuration off rather than adding to it, and
#: removing them would undo the isolation this module exists to protect.
CONFIG_INJECTING: Final[frozenset[str]] = frozenset({"GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT"})

#: The numbered pair form of the same channel. It is a PREFIX rather than a
#: name, because ``GIT_CONFIG_COUNT=50`` means fifty distinct key names - a
#: fixed set would cover the first and leave the rest armed.
CONFIG_INJECTING_PREFIXES: Final[tuple[str, ...]] = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")


def relocates(name: str) -> bool:
    """Whether ``name`` points a git child somewhere its caller never named.

    THE COMPARISON IS UPPER-CASED for the reason ``scrub`` states: Windows
    folds environment keys, so a case-sensitive test measures nothing.
    """
    folded = name.upper()
    if folded in REPO_LOCATING or folded in CONFIG_INJECTING:
        return True
    return folded.startswith(CONFIG_INJECTING_PREFIXES)


def scrub(env: dict[str, str]) -> dict[str, str]:
    """Return ``env`` with every relocating variable removed.

    Two channels, not one. ``REPO_LOCATING`` moves a child to a different
    repository; ``CONFIG_INJECTING`` and its numbered prefixes reconfigure the
    repository the child is already in. Both make a child answer about
    something its caller never named, and the second one disarms hooks.

    THE COMPARISON IS UPPER-CASED, and that is not defensive noise. Windows
    folds environment keys and ``dict(os.environ)`` hands back upper-case ones,
    so popping a mixed-case spelling removes NOTHING while reporting success -
    a probe written that way measures nothing and says it is clean.

    The mapping is mutated in place and also returned, so this reads correctly
    both as a statement and as an expression.

    Args:
        env: An environment mapping, normally a copy of ``os.environ``.

    Returns:
        The same mapping, with the repository-locating variables gone.
    """
    for name in [key for key in env if relocates(key)]:
        env.pop(name)
    return env


def scrubbed_env() -> dict[str, str]:
    """This process's environment with every repository-locating variable gone.

    Returns:
        A fresh mapping safe to hand to a ``git`` child that must act on the
        directory it is pointed at rather than on an inherited repository.
    """
    return scrub(dict(os.environ))


@functools.lru_cache(maxsize=1)
def git_coreutils_dir() -> str | None:
    """The directory holding Git for Windows' GNU ``timeout``, or None.

    Derived from ``git --exec-path`` rather than from PATH, because a default
    Git for Windows install puts only its ``cmd`` directory on PATH and the
    coreutils directory is not on it at all. The exec path is
    ``<root>/mingw64/libexec/git-core`` and the coreutils sit in
    ``<root>/usr/bin``, so the ancestors are walked until one holds them.
    """
    try:
        proc = subprocess.run(
            ["git", "--exec-path"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    exec_path = proc.stdout.strip()
    if proc.returncode != 0 or not exec_path:
        return None
    for root in Path(exec_path).parents:
        candidate = root / "usr" / "bin"
        if (candidate / "timeout.exe").is_file():
            return str(candidate)
    return None


def program_on_child_path(env: dict[str, str], name: str) -> str:
    """``name`` resolved on ``env``'s PATH, else ``name`` itself.

    CS-1187: Windows resolves a bare program name in the PARENT's application
    directory and PATH, never in the ``env`` handed to the child. Inside a
    venv the running parent is the BASE interpreter, so a bare ``python``
    runs the base install, and on a default Git for Windows install a bare
    ``sh`` is not found at all. Resolving on the child's own PATH is what a
    hook's ``sh`` does. Falls back to the bare name, so a miss fails the same
    way it always did.
    """
    search = next((value for key, value in env.items() if key.upper() == "PATH"), None)
    return shutil.which(name, path=search) or name


def gnu_timeout_first(env: dict[str, str]) -> dict[str, str]:
    """Return ``env`` with Git's GNU coreutils ahead of System32 on PATH.

    CS-1187, MEASURED IN A NEVER-SEEN WINDOWS SANDBOX. The tracked hooks check
    ``timeout`` BY BEHAVIOUR and refuse to run a probe without a working GNU
    one. Windows ships its own ``timeout`` in System32, a pause command, and on
    a machine whose PATH lists System32 before Git's coreutils it answers
    first - so every hook arm refused with "no working GNU timeout was found".
    The hooks are right to refuse; the fixture is what must hand them the
    PATH a working Git for Windows hook run needs.

    A no-op off Windows, where nothing shadows coreutils, and a no-op when no
    Git coreutils directory is found. The mapping is mutated in place and also
    returned, matching ``scrub``.
    """
    if os.name != "nt":
        return env
    coreutils = git_coreutils_dir()
    if coreutils is None:
        return env
    path_key = next((key for key in env if key.upper() == "PATH"), "PATH")
    env[path_key] = coreutils + os.pathsep + env.get(path_key, "")
    return env
