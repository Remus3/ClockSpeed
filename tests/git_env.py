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

import os
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


def scrub(env: dict[str, str]) -> dict[str, str]:
    """Return ``env`` with every repository-locating variable removed.

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
    for name in [key for key in env if key.upper() in REPO_LOCATING]:
        env.pop(name)
    return env


def scrubbed_env() -> dict[str, str]:
    """This process's environment with every repository-locating variable gone.

    Returns:
        A fresh mapping safe to hand to a ``git`` child that must act on the
        directory it is pointed at rather than on an inherited repository.
    """
    return scrub(dict(os.environ))
