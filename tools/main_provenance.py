"""CS-1227 - the MAIN provenance check of ``CLAUDE.md`` section 6.1, as one function.

A note in this tree's inbox is MAIN's only if its SHA-256 equals the same-named
file in MAIN's outbox (``<main_root>/moon_sync_outbox/<name>``) and that file is
tracked and unmodified in MAIN's history. :func:`verify_main_note` is THE check;
the headless inbox worker calls it, or this file's CLI, instead of re-deriving
the steps from prose.

WHERE MAIN'S ROOT COMES FROM, and only there: the gitignored local
configuration file ``main_tree.local.json`` in ``config``, a JSON object whose
``main_root`` key names MAIN's tree root as an ABSOLUTE path - a relative one
would resolve against whatever the cwd happens to be, and is refused. Never a
tracked file, never the channel root, never the note. A test passes
``config_path`` to point at a throwaway file; nothing else does.

THE COMMITTED BLOB IS THE TRUTH, NOT GIT'S STAT CACHE. The note is hashed
against the bytes of HEAD's blob for the outbox path, read with ``git cat-file``.
"Unmodified" is then decided by comparing BYTES: the index entry must name the
same object as HEAD (else ``modified``), and the working-tree file must equal
the blob byte for byte (else ``worktree-differs-from-commit``). ``git diff
--quiet HEAD`` is never asked - it trusts the stat cache, so
``--assume-unchanged``, ``--skip-worktree`` or a same-size edit with its mtime
restored would all read as clean. A tree whose checkout filters change the
bytes on disk (eol, autocrlf, smudge) is refused by design, so MAIN must keep
its outbox LF on disk.

WHAT IS READ OUTSIDE THIS TREE: the one outbox file, and MAIN's git - asked for
the object ids of that path in HEAD and in the index, and for HEAD's blob.
Nothing else there. Git runs with ``--no-optional-locks``,
``--no-replace-objects`` and every inherited ``GIT_*`` variable dropped, so
neither a hook's ``GIT_DIR``, an injected ``GIT_CONFIG_*``, nor a
``refs/replace/`` entry standing a never-committed blob or commit in for HEAD's
steers it. A shallow repository is refused outright (``main-shallow``).

ACCEPTED RESIDUAL: a detached HEAD on a commit no branch reaches is accepted as
"MAIN's history", because the check asks what HEAD names and not how it got
there.

THE VERDICT BINDS TO THE BYTES IT VERIFIED. A verified :class:`Verdict` carries
the SHA-256 hex of the note bytes it hashed, and the CLI prints it on a second
line, so a caller acts only on a note whose bytes still hash to it - the note
can change between the check and the read.

NOTHING RENDERS A PATH, AND NOTHING RAISES. Every outcome is a :class:`Verdict`
whose ``reason`` is one constant from :data:`REASONS`. Any unexpected failure
inside the check is the fixed reason ``check-failed``, git's stdout and stderr
are captured and discarded, and the CLI prints the reason alone - the
configured root is a home path on this machine, and ``CLAUDE.md`` rules 12 and
13 count tracebacks, error text and log lines as echo paths.

Usage::

    python tools/main_provenance.py NOTE [--config PATH]

Prints the reason, and after ``verified`` the note's SHA-256 hex on a second
line. Exit 0 only on ``verified``, 1 on any refusal or interrupt, 2 on bad
usage (printed as ``usage-error``, never echoing an argument).
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
from typing import Final, NoReturn

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
CONFIG_ROOT_NOT_ABSOLUTE: Final = "config-root-not-absolute"
MAIN_ROOT_ABSENT: Final = "main-root-absent"
MAIN_NOT_A_REPO: Final = "main-not-a-repo"
MAIN_SHALLOW: Final = "main-shallow"
NOTE_UNREADABLE: Final = "note-unreadable"
OUTBOX_FILE_ABSENT: Final = "outbox-file-absent"
OUTBOX_UNREADABLE: Final = "outbox-unreadable"
UNTRACKED: Final = "untracked"
MODIFIED: Final = "modified"
WORKTREE_DIFFERS: Final = "worktree-differs-from-commit"
GIT_FAILED: Final = "git-failed"
DIGEST_MISMATCH: Final = "digest-mismatch"
CHECK_FAILED: Final = "check-failed"
INTERRUPTED: Final = "interrupted"
USAGE_ERROR: Final = "usage-error"

#: The closed set of reasons a verdict - or the CLI - may carry.
REASONS: Final = frozenset(
    {
        VERIFIED,
        CONFIG_ABSENT,
        CONFIG_UNPARSEABLE,
        CONFIG_NO_ROOT,
        CONFIG_ROOT_NOT_ABSOLUTE,
        MAIN_ROOT_ABSENT,
        MAIN_NOT_A_REPO,
        MAIN_SHALLOW,
        NOTE_UNREADABLE,
        OUTBOX_FILE_ABSENT,
        OUTBOX_UNREADABLE,
        UNTRACKED,
        MODIFIED,
        WORKTREE_DIFFERS,
        GIT_FAILED,
        DIGEST_MISMATCH,
        CHECK_FAILED,
        INTERRUPTED,
        USAGE_ERROR,
    }
)

EXIT_VERIFIED: Final = 0
EXIT_REFUSED: Final = 1
EXIT_USAGE: Final = 2


@dataclass(frozen=True)
class Verdict:
    """The outcome of one check. ``reason`` is always a member of REASONS.

    ``digest`` is the SHA-256 hex of the note bytes a VERIFIED check hashed, and
    empty on every refusal.
    """

    ok: bool
    reason: str
    digest: str = ""


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
    except (ValueError, RecursionError, MemoryError):
        # UnicodeDecodeError and JSONDecodeError are ValueErrors; a deeply
        # nested document raises RecursionError, which is not.
        return CONFIG_UNPARSEABLE
    return _root_from(data)


def _root_from(data: object) -> Path | str:
    """Pick the absolute root out of a parsed configuration, or a refusal reason."""
    if not isinstance(data, dict):
        return CONFIG_UNPARSEABLE
    root = data.get(ROOT_KEY)
    if not isinstance(root, str) or not root.strip():
        return CONFIG_NO_ROOT
    path = Path(root)
    if not path.is_absolute():
        return CONFIG_ROOT_NOT_ABSOLUTE
    return path


def _git_env() -> dict[str, str]:
    """The inherited environment with EVERY ``GIT_*`` variable removed."""
    return {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}


def _git(root: Path, *args: str) -> tuple[int, bytes] | None:
    """Run one read-only git query in ``root``.

    Returns:
        The exit code and stdout, or None when git could not be run. Stderr is
        captured and discarded - git's error text names paths.
    """
    try:
        proc = subprocess.run(
            [
                "git",
                "--no-optional-locks",
                "--no-replace-objects",
                "-c",
                "core.fsmonitor=false",
                "-C",
                str(root),
                *args,
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            env=_git_env(),
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.returncode, proc.stdout


def _object_id(root: Path, spec: str) -> str | None:
    """The object id ``spec`` names in MAIN, or None if it names nothing."""
    result = _git(root, "rev-parse", "--verify", "--quiet", spec)
    if result is None or result[0] != 0:
        return None
    return result[1].decode("ascii", "replace").strip() or None


def _committed_blob(root: Path, rel: str) -> bytes | str:
    """HEAD's bytes for ``rel``, or a refusal reason.

    The path must be in HEAD and in the index, and the index entry must name
    the same object as HEAD - a staged edit is a modification even when the
    working tree has been put back.
    """
    head_id = _object_id(root, "HEAD:./" + rel)
    index_id = _object_id(root, ":./" + rel)
    if head_id is None or index_id is None:
        return UNTRACKED
    if head_id != index_id:
        return MODIFIED
    blob = _git(root, "cat-file", "blob", head_id)
    if blob is None or blob[0] != 0:
        return GIT_FAILED
    return blob[1]


def verify_main_note(note_path: Path, *, config_path: Path | None = None) -> Verdict:
    """Decide whether an inbox note is MAIN's, per ``CLAUDE.md`` section 6.1.

    Never raises: an unexpected failure anywhere in the check is the fixed
    reason ``check-failed``, so no exception text can carry a path out.

    Args:
        note_path: The note in this tree's inbox.
        config_path: The local configuration naming MAIN's root. Defaults to
            :data:`DEFAULT_CONFIG`; only a test passes another.

    Returns:
        ``Verdict(ok=True, reason="verified")`` when the note's SHA-256 equals
        HEAD's blob for the same-named file in MAIN's outbox, and that file is
        tracked and byte-identical to the blob in both index and working tree;
        otherwise a refusal naming its reason.
    """
    try:
        reason, digest = _check(
            Path(note_path), DEFAULT_CONFIG if config_path is None else config_path
        )
    except Exception:  # the boundary: no exception text may escape
        reason, digest = CHECK_FAILED, ""
    ok = reason == VERIFIED
    return Verdict(ok=ok, reason=reason, digest=digest if ok else "")


def _check(note: Path, config_path: Path) -> tuple[str, str]:
    """Run every step in order; return the first refusal, or VERIFIED and the digest."""
    resolved = _main_root(config_path)
    if isinstance(resolved, str):
        return resolved, ""
    name = note.name
    located = _locate(resolved, name)
    if located is not None:
        return located, ""
    blob = _committed_blob(resolved, OUTBOX_DIR + "/" + name)
    if isinstance(blob, str):
        return blob, ""
    return _compare(note, resolved / OUTBOX_DIR / name, blob)


def _repository(root: Path) -> str | None:
    """Refuse a root that is not a git work tree, or is a shallow repository."""
    inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if inside is None:
        return GIT_FAILED
    if inside[0] != 0:
        return MAIN_NOT_A_REPO
    shallow = _git(root, "rev-parse", "--is-shallow-repository")
    if shallow is None or shallow[0] != 0:
        return GIT_FAILED
    if shallow[1].strip() != b"false":
        return MAIN_SHALLOW
    return None


def _locate(root: Path, name: str) -> str | None:
    """Refuse a missing root, an unusable repository, or an absent outbox file."""
    if not root.is_dir():
        return MAIN_ROOT_ABSENT
    if name in {"", ".", ".."}:
        return NOTE_UNREADABLE
    repository = _repository(root)
    if repository is not None:
        return repository
    outbox_file = root / OUTBOX_DIR / name
    if outbox_file.is_symlink() or not outbox_file.is_file():
        return OUTBOX_FILE_ABSENT
    return None


def _compare(note: Path, outbox_file: Path, blob: bytes) -> tuple[str, str]:
    """Compare the working-tree file with the blob, then the note with the blob.

    Returns:
        The reason, and on VERIFIED the SHA-256 hex of the note bytes hashed.
    """
    try:
        outbox_bytes = outbox_file.read_bytes()
    except OSError:
        return OUTBOX_UNREADABLE, ""
    if outbox_bytes != blob:
        return WORKTREE_DIFFERS, ""
    try:
        note_bytes = note.read_bytes()
    except OSError:
        return NOTE_UNREADABLE, ""
    note_digest = hashlib.sha256(note_bytes).hexdigest()
    if note_digest != hashlib.sha256(blob).hexdigest():
        return DIGEST_MISMATCH, ""
    return VERIFIED, note_digest


class _Parser(argparse.ArgumentParser):
    """An argument parser whose usage errors never echo an argument."""

    def error(self, message: str) -> NoReturn:
        del message
        sys.stdout.write(USAGE_ERROR + "\n")
        sys.exit(EXIT_USAGE)


def main(argv: list[str] | None = None) -> int:
    """Print the verdict's reason; exit 0 only when the note is verified."""
    parser = _Parser(
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
    try:
        verdict = verify_main_note(args.note, config_path=args.config)
    except KeyboardInterrupt:
        verdict = Verdict(ok=False, reason=INTERRUPTED)
    except Exception:  # the CLI boundary: a reason, never a traceback
        verdict = Verdict(ok=False, reason=CHECK_FAILED)
    sys.stdout.write(verdict.reason + "\n")
    if verdict.ok:
        sys.stdout.write(verdict.digest + "\n")
    return EXIT_VERIFIED if verdict.ok else EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
