"""CS-1227 - the MAIN provenance check of ``CLAUDE.md`` section 6.1, as one function.

A note in this tree's inbox is MAIN's only if its SHA-256 equals the same-named
file in MAIN's outbox (``<main_root>/moon_sync_outbox/<name>``) and that file is
tracked and unmodified in MAIN's history. :func:`verify_main_note` is THE check;
the headless inbox worker calls it, or this file's CLI, instead of re-deriving
the steps from prose.

WHERE MAIN'S ROOT COMES FROM, and only there: the gitignored local
configuration file ``config/main_tree.local.json``, a JSON object whose
``main_root`` key names MAIN's tree root. Never a tracked file, never the
channel root, never the note. A test passes ``config_path`` to point at a
throwaway file; nothing else does.

WHAT IS READ OUTSIDE THIS TREE: the one outbox file, and MAIN's git - asked
whether that path is in HEAD, in the index, and unchanged against HEAD. Nothing
else there.

NOTHING RENDERS A PATH. Every outcome is a :class:`Verdict` whose ``reason`` is
one constant from :data:`REASONS`. No exception escapes, git's stderr is
captured and discarded, and the CLI prints the reason alone - the configured
root is a home path on this machine, and ``CLAUDE.md`` rules 12 and 13 count
error text and log lines as echo paths.

Usage::

    python tools/main_provenance.py NOTE [--config PATH]

Prints the reason. Exit 0 only on ``verified``, 1 on any refusal, 2 on bad usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: This repository's root - the default configuration resolves against it.
REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: The gitignored local configuration naming MAIN's tree root.
DEFAULT_CONFIG: Final = REPO_ROOT / "config" / "main_tree.local.json"

#: The configuration key holding MAIN's tree root.
ROOT_KEY: Final = "main_root"

#: MAIN's outbox, relative to its root.
OUTBOX_DIR: Final = "moon_sync_outbox"

#: Seconds one git call may take.
GIT_TIMEOUT: Final = 60

VERIFIED: Final = "verified"
CONFIG_ABSENT: Final = "config-absent"
CONFIG_UNPARSEABLE: Final = "config-unparseable"
CONFIG_NO_ROOT: Final = "config-no-root"
MAIN_ROOT_ABSENT: Final = "main-root-absent"
MAIN_NOT_A_REPO: Final = "main-not-a-repo"
NOTE_UNREADABLE: Final = "note-unreadable"
OUTBOX_FILE_ABSENT: Final = "outbox-file-absent"
OUTBOX_UNREADABLE: Final = "outbox-unreadable"
UNTRACKED: Final = "untracked"
MODIFIED: Final = "modified"
GIT_FAILED: Final = "git-failed"
DIGEST_MISMATCH: Final = "digest-mismatch"

#: The closed set of reasons a verdict may carry.
REASONS: Final = frozenset(
    {
        VERIFIED,
        CONFIG_ABSENT,
        CONFIG_UNPARSEABLE,
        CONFIG_NO_ROOT,
        MAIN_ROOT_ABSENT,
        MAIN_NOT_A_REPO,
        NOTE_UNREADABLE,
        OUTBOX_FILE_ABSENT,
        OUTBOX_UNREADABLE,
        UNTRACKED,
        MODIFIED,
        GIT_FAILED,
        DIGEST_MISMATCH,
    }
)

#: Inherited variables that would point a child git at another repository -
#: the pre-push hook exports GIT_DIR, for one.
_GIT_REDIRECTS: Final = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    }
)

EXIT_VERIFIED: Final = 0
EXIT_REFUSED: Final = 1


@dataclass(frozen=True)
class Verdict:
    """The outcome of one check. ``reason`` is always a member of REASONS."""

    ok: bool
    reason: str


def _main_root(config_path: Path) -> Path | str:
    """Read MAIN's root from the configuration, or return a refusal reason."""
    try:
        raw = config_path.read_bytes()
    except FileNotFoundError:
        return CONFIG_ABSENT
    except OSError:
        return CONFIG_UNPARSEABLE
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return CONFIG_UNPARSEABLE
    if not isinstance(data, dict):
        return CONFIG_UNPARSEABLE
    root = data.get(ROOT_KEY)
    if not isinstance(root, str) or not root.strip():
        return CONFIG_NO_ROOT
    return Path(root)


def _git_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in list(env):
        if key.upper() in _GIT_REDIRECTS:
            del env[key]
    return env


def _git(root: Path, *args: str) -> int | None:
    """Run one git query in ``root``; return its exit code, or None on failure.

    Output and stderr are captured and discarded - git's error text names paths.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            env=_git_env(),
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.returncode


def _tracking(root: Path, rel: str) -> str | None:
    """Return a refusal reason for MAIN's history of ``rel``, or None if clean."""
    in_head = _git(root, "cat-file", "-e", "HEAD:./" + rel)
    if in_head is None:
        return GIT_FAILED
    in_index = _git(root, "ls-files", "--error-unmatch", "--", rel)
    if in_index is None:
        return GIT_FAILED
    if in_head != 0 or in_index != 0:
        return UNTRACKED
    changed = _git(root, "diff", "--quiet", "HEAD", "--", rel)
    if changed == 0:
        return None
    if changed == 1:
        return MODIFIED
    return GIT_FAILED


def verify_main_note(note_path: Path, *, config_path: Path | None = None) -> Verdict:
    """Decide whether an inbox note is MAIN's, per ``CLAUDE.md`` section 6.1.

    Args:
        note_path: The note in this tree's inbox.
        config_path: The local configuration naming MAIN's root. Defaults to
            :data:`DEFAULT_CONFIG`; only a test passes another.

    Returns:
        ``Verdict(ok=True, reason="verified")`` when the note's SHA-256 equals
        the same-named file in MAIN's outbox and that file is tracked and
        unmodified in MAIN's history; otherwise a refusal naming its reason.
    """
    reason = _check(Path(note_path), DEFAULT_CONFIG if config_path is None else config_path)
    return Verdict(ok=reason == VERIFIED, reason=reason)


def _check(note: Path, config_path: Path) -> str:
    """Run every step in order and return the first refusal, or VERIFIED."""
    resolved = _main_root(config_path)
    if isinstance(resolved, str):
        return resolved
    name = note.name
    located = _locate(resolved, name)
    if located is not None:
        return located
    history = _tracking(resolved, OUTBOX_DIR + "/" + name)
    if history is not None:
        return history
    return _digest(note, resolved / OUTBOX_DIR / name)


def _locate(root: Path, name: str) -> str | None:
    """Refuse a missing root, a non-repository, or an absent outbox file."""
    if not root.is_dir():
        return MAIN_ROOT_ABSENT
    if name in {"", ".", ".."}:
        return NOTE_UNREADABLE
    inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if inside is None:
        return GIT_FAILED
    if inside != 0:
        return MAIN_NOT_A_REPO
    outbox_file = root / OUTBOX_DIR / name
    if outbox_file.is_symlink() or not outbox_file.is_file():
        return OUTBOX_FILE_ABSENT
    return None


def _digest(note: Path, outbox_file: Path) -> str:
    """Compare the note's SHA-256 with the outbox file's."""
    try:
        note_bytes = note.read_bytes()
    except OSError:
        return NOTE_UNREADABLE
    try:
        outbox_bytes = outbox_file.read_bytes()
    except OSError:
        return OUTBOX_UNREADABLE
    if hashlib.sha256(note_bytes).digest() != hashlib.sha256(outbox_bytes).digest():
        return DIGEST_MISMATCH
    return VERIFIED


def main(argv: list[str] | None = None) -> int:
    """Print the verdict's reason; exit 0 only when the note is verified."""
    parser = argparse.ArgumentParser(
        prog="main_provenance.py",
        description="The CLAUDE.md section 6.1 MAIN provenance check (CS-1227).",
    )
    parser.add_argument("note", type=Path, help="the inbox note to check")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="the local configuration naming MAIN's root (default: the gitignored file)",
    )
    args = parser.parse_args(argv)
    verdict = verify_main_note(args.note, config_path=args.config)
    sys.stdout.write(verdict.reason + "\n")
    return EXIT_VERIFIED if verdict.ok else EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
