"""CS-923: every tracked git hook must be mode 100755 in the git index.

WHY A MODE BIT GETS ITS OWN TEST. Git refuses to run a hook that is not
executable and reports NOTHING when it declines - no warning, no non-zero exit,
no log line. A tier-0 gate that has silently stopped firing is indistinguishable
from one that fires and finds nothing wrong, so the failure mode is a green tick
over an absent gate.

THE OPERATOR'S MACHINE CANNOT SEE THIS. Git for Windows masks X_OK, so a hook at
100644 fires here exactly as one at 100755 does - measured both ways on git 2.53
during the CS-923 adjudication. The bit only decides anything on POSIX, which is
CI and any third-party clone, so the only place this can be caught is a test.

WHY THE BOOTSTRAP IS NOT ENOUGH. scripts/install_hooks.py sets the executable bit
on POSIX, which repairs a fresh clone. It does not survive a later `git pull`,
`checkout`, `merge` or `reset --hard` that REWRITES a hook file: git materialises
the file at the INDEX mode, so 100644 in the index puts a non-executable hook back
on disk while core.hooksPath stays set and the gate silently stops firing. Fixing
the index mode is what makes the repair durable rather than one-shot.

THIS TEST EXISTS SO A FOURTH HOOK CANNOT REINTRODUCE IT. A hook authored on
Windows and added with `git add` arrives at 100644 by default, and nothing else in
the tree grades the mode - measured at the CS-923 adjudication, a repo-wide search
for `100755`, `ls-files -s`, `update-index` and `core.filemode` over tracked files
returned zero hits.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import run_git

# The mode git records for a tracked regular file that it will execute. Any
# other value for a hook means git will decline to run it on POSIX.
EXECUTABLE_BLOB_MODE = "100755"

HOOKS_DIR = ".githooks"

# The three tier-0 hooks CLAUDE.md section 2.2 names as blocking gates. A count
# rather than a name list on purpose: this arm grades the MODE of whatever is
# tracked, and a fourth hook must raise the floor rather than slip past it.
MINIMUM_TRACKED_HOOKS = 3


def _tracked_hook_modes(repo_root: Path) -> dict[str, str]:
    """Return {path: index mode} for every tracked file under .githooks/.

    Reads the INDEX rather than the filesystem. The on-disk permission bits are
    what scripts/install_hooks.py repairs per clone; the index mode is what every
    future checkout materialises from, and it is the durable half.
    """
    proc = run_git(repo_root, "ls-files", "-s", "--", HOOKS_DIR)
    if proc is None or proc.returncode != 0:
        return {}
    modes: dict[str, str] = {}
    for raw in proc.stdout.decode("utf-8", "replace").splitlines():
        if not raw.strip():
            continue
        # Format: "<mode> <sha> <stage>\t<path>"
        meta, _, path = raw.partition("\t")
        mode = meta.split()[0] if meta.split() else ""
        if path:
            modes[path] = mode
    return modes


def test_every_tracked_hook_is_executable_in_the_index(
    repo_root: Path, git_available: bool
) -> None:
    """Fail if any tracked hook is not 100755, and fail if there are none."""
    if not git_available:
        pytest.skip("no git work tree, so there is no index to assert on")

    modes = _tracked_hook_modes(repo_root)

    # REFUSING TO PASS OVER AN EMPTY SET. If the directory were renamed or the
    # pathspec went stale this would find nothing and report green, which is the
    # exact shape of guard this test exists to prevent.
    found = len(modes)
    assert found >= MINIMUM_TRACKED_HOOKS, (
        f"expected at least {MINIMUM_TRACKED_HOOKS} tracked hooks under {HOOKS_DIR}/, "
        f"found {found}. A pass over an empty or shrunken set is not evidence."
    )

    wrong = sorted(p for p, m in modes.items() if m != EXECUTABLE_BLOB_MODE)
    wrong_count = len(wrong)
    detail = ", ".join(f"{p}={modes[p]}" for p in wrong)
    assert wrong_count == 0, (
        f"{wrong_count} tracked hook(s) are not {EXECUTABLE_BLOB_MODE}: {detail}. "
        "Git silently refuses to run a non-executable hook on POSIX and reports "
        "nothing, so the gate is absent rather than failing. Repair with: "
        f"git update-index --chmod=+x {' '.join(wrong) if wrong else '<hook>'}"
    )
