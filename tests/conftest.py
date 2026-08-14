"""Shared fixtures for the Clockspeed test suite.

Dependency-free by design: standard library plus pytest, nothing else. The
rule suite has to run on a clean machine with no game installed
(BOOTSTRAP.md section 5.4), and a fixture that needs a package installed is a
fixture that does not run there.

Nothing here resolves a path from a literal. The repo root is derived from
this file's own location, and the file inventory is derived from git. An
absolute path under a user home directory in a tracked file is forbidden
outright (CONVENTIONS.md section 10, BOOTSTRAP.md section 12 item 3), and
tests/test_scaffold.py asserts the absence of one across the whole tree - a
harness that hardcoded one would be asserting against itself.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# File inventory
# ---------------------------------------------------------------------------

# Directories the fallback walk never descends into. These lists are ONLY used
# when git is unavailable; the git path gets the real answer from .gitignore.
# Kept in sync with .gitignore by intent, not by machine - if the two disagree,
# .gitignore wins and these lists are what is wrong.
#
# The split between "at any depth" and "at the root only" is load-bearing and
# mirrors the leading slash in .gitignore. /data/ is the gitignored generated
# artifact directory; clockspeed/data/ is the SOURCE package for the data
# layer. A name-only skip would silently drop the entire data layer from every
# scan below, which is the same bug the anchored pattern in .gitignore exists
# to prevent. The same reasoning covers work/, run/, logs/ and the rest.
_SKIP_DIR_NAMES_ANYWHERE = frozenset(
    {
        ".git",
        ".idea",
        ".mypy_cache",
        ".pytest_cache",
        ".recall",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "htmlcov",
        "node_modules",
        "venv",
    }
)
_SKIP_DIR_NAMES_AT_ROOT = frozenset(
    {
        "build",
        "captures",
        "certs",
        "corpus",
        "data",
        "dist",
        "gamedata",
        "logs",
        "run",
        "screenshots",
        "var",
        "work",
    }
)

# Suffixes that are legitimately not 7-bit ASCII because they are not text.
# This is a DENY list rather than an allow list on purpose: an unrecognised
# extension is treated as authored text and therefore gets scanned. That
# direction fails loudly on a new file type and is corrected by adding it here
# deliberately. An allow list would silently stop scanning whatever it did not
# know about, which is the failure mode that matters.
_BINARY_SUFFIXES = frozenset(
    {
        ".bin",
        ".bmp",
        ".dat",
        ".der",
        ".dll",
        ".exe",
        ".gif",
        ".gz",
        ".ico",
        ".icns",
        ".jpeg",
        ".jpg",
        ".pdf",
        ".pfx",
        ".png",
        ".pyc",
        ".pyd",
        ".sav",
        ".so",
        ".ttf",
        ".usmap",
        ".webp",
        ".woff",
        ".woff2",
        ".zip",
    }
)

_SNIFF_BYTES = 8192


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes] | None:
    """Run a git subcommand in ``root``, or return None if git is unusable.

    Public because test modules import it: git is the only tool that can
    answer "would this path be committed" and "is this path ignored", and both
    questions are asserted on in tests/test_scaffold.py.

    The executable is resolved from PATH rather than from an absolute path.
    That is required, not lazy: an absolute tool path in a tracked file
    hardcodes a machine layout (CONVENTIONS.md section 10).

    Args:
        root: Directory to run git in.
        *args: Arguments after the ``git -C <root>`` prefix.

    Returns:
        The completed process, or None if git is missing or timed out. A
        non-zero exit is returned rather than swallowed so the caller can
        decide whether it matters.
    """
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _git_inventory(root: Path) -> list[Path] | None:
    """List every file git tracks or WOULD track in ``root``.

    ``--cached`` covers tracked files and ``--others --exclude-standard``
    covers untracked files that .gitignore does not exclude. Together they are
    the set that a commit would capture, which is the correct set for a
    hygiene assertion: a file that is about to be committed is exactly as
    dangerous as one already committed.

    Args:
        root: Repository root.

    Returns:
        Absolute paths, or None if git could not answer.
    """
    proc = run_git(
        root,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "--full-name",
        "-z",
    )
    if proc is None or proc.returncode != 0:
        return None
    names = proc.stdout.decode("utf-8", "surrogateescape").split("\0")
    return [root / name for name in names if name]


def walk_inventory(root: Path) -> list[Path]:
    """List candidate files by walking the tree, skipping known noise.

    Public because tests/test_scaffold.py pins its directory-skip logic: the
    root-anchored half of that logic is what keeps the clockspeed/data/
    source package out of the gitignored /data/ bucket.

    The fallback for a checkout with no usable git. Less accurate than
    :func:`_git_inventory` because it approximates .gitignore rather than
    reading it, so it is deliberately the second choice.

    Args:
        root: Repository root.

    Returns:
        Absolute paths.
    """
    found: list[Path] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        for entry in sorted(directory.iterdir()):
            if entry.is_symlink():
                continue
            if entry.is_dir():
                at_root = entry.parent == root
                skipped = entry.name in _SKIP_DIR_NAMES_ANYWHERE or (
                    at_root and entry.name in _SKIP_DIR_NAMES_AT_ROOT
                )
                if not skipped:
                    stack.append(entry)
            elif entry.is_file():
                found.append(entry)
    return found


def _looks_binary(path: Path) -> bool:
    """Report whether a file should be treated as binary rather than authored text.

    Two independent signals, because either alone is weak: a known binary
    suffix, and a NUL byte in the first block. A file with neither is treated
    as authored text.

    Args:
        path: File to classify.

    Returns:
        True if the file is binary.
    """
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return True
    try:
        with path.open("rb") as handle:
            return b"\0" in handle.read(_SNIFF_BYTES)
    except OSError:
        return True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root, resolved from this file's location.

    Never a literal. This file lives at ``<root>/tests/conftest.py``, so the
    root is two parents up. Resolving it this way means the suite runs from a
    worktree, a fresh clone, or a temporary checkout with no edit.

    Returns:
        The repository root.
    """
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def git_available(repo_root: Path) -> bool:
    """Report whether git can answer questions about this checkout.

    Args:
        repo_root: Repository root.

    Returns:
        True if git is on PATH and ``repo_root`` is inside a work tree.
    """
    proc = run_git(repo_root, "rev-parse", "--is-inside-work-tree")
    return proc is not None and proc.returncode == 0


@pytest.fixture(scope="session")
def repo_files(repo_root: Path) -> list[Path]:
    """Every file that git tracks or would track, git being the authority.

    Falls back to a tree walk if git cannot answer, so the suite still runs in
    an exported tarball. The fallback approximates .gitignore and is therefore
    the weaker answer; it is never silently preferred.

    Args:
        repo_root: Repository root.

    Returns:
        Sorted absolute paths to existing files.
    """
    inventory = _git_inventory(repo_root)
    if inventory is None:
        inventory = walk_inventory(repo_root)
    return sorted(path for path in inventory if path.is_file())


@pytest.fixture(scope="session")
def authored_text_files(repo_files: list[Path]) -> list[Path]:
    """The authored text subset of the repository: what the character-set rule governs.

    Authored text is every tracked-or-would-be-tracked file that is not
    binary. Markdown, Python, TOML, JSON, YAML, shell hooks, extensionless
    scripts and anything else a human typed all qualify. The 7-bit ASCII rule
    covers all of it, not just source code (BOOTSTRAP.md section 12 item 4).

    Args:
        repo_files: Full file inventory.

    Returns:
        Sorted absolute paths.
    """
    return [path for path in repo_files if not _looks_binary(path)]
