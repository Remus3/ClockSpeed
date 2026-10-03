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

A FILE INSIDE A BUNDLE DIRECTORY (CS-1232). MAIN ships a kit as a directory,
mirrored as ``<outbox>/<bundle-dir>/<file>`` and received as
``<inbox>/<bundle-dir>/<file>``. The inbox is THIS tree's inbox,
:data:`DEFAULT_INBOX`, never anything read from the note's spelling; a test
injects another with ``inbox_dir``, as it does ``config_path``. Both the inbox
and the note are resolved strictly (a missing note through its resolved
parent), so an 8.3 short name, a trailing dot, a ``.`` or ``..`` hop, or a
symlink or junction aliasing the inbox all land on the same real path.
Placement is then decided on the RESOLVED path alone:

- directly in the resolved inbox: looked up by its bare name, as before;
- one directory below it: looked up as ``<bundle-dir>/<file>`` through every
  step a top-level note takes, provided both names are plain components (see
  ``_PLAIN_COMPONENT``) and neither is ``moon_sync_inbox`` or
  ``moon_sync_outbox`` in any case - otherwise ``bundle-path-refused``;
- the inbox itself, or anything deeper: ``bundle-path-refused``;
- outside the resolved inbox, or when the inbox or note cannot be resolved:
  looked up by its bare name, exactly as before CS-1232.

A NOTE REACHED THROUGH A LINK IS REFUSED (``bundle-path-refused``) when it is
placed against the inbox: the note given lexically inside the inbox (after
``abspath`` and ``normcase``, against the inbox as given or as resolved) but
resolving outside it; a spelling whose trailing components, compared with
``normcase``, differ from the resolved parts below the inbox (a link that
lands elsewhere, an 8.3 short name or a trailing dot or space BELOW the
inbox, or a ``..`` inside the bundle); and a note file, or for a bundle file
its bundle directory, that is a symlink, a junction or any other reparse
point. A hard link is a plain file and stays accepted. A note given and
resolving outside the inbox keeps the pre-CS-1232 answer, trailing dot and
all. On MAIN's side a bundle directory that is a link is refused as
``outbox-file-absent``, the same reason a linked outbox file gets.

THE BYTES HASHED ARE THE FILE PLACED. A placed note is read through its
RESOLVED path by ONE open, and the open file's identity is then compared with
a fresh stat of that path; a note replaced or relinked under the read is
``note-unreadable``. ACCEPTED RESIDUAL: a swap that is undone between the open
and the stat is not seen - one open cannot see more.

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
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, NoReturn

# `tools` carries no __init__.py, so the sibling resolver is imported under its
# BARE name, the way tools/sha_citation_gate.py does it.
_TOOLS_DIR: Final = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

#: This repository's root - the default configuration resolves against it.
REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: The gitignored local configuration naming MAIN's tree root.
DEFAULT_CONFIG: Final = REPO_ROOT / "config" / "main_tree.local.json"

#: The configuration key holding MAIN's tree root.
ROOT_KEY: Final = "main_root"

#: MAIN's outbox, relative to its root.
OUTBOX_DIR: Final = "moon_sync_outbox"

#: This tree's inbox directory name.
INBOX_DIR: Final = "moon_sync_inbox"

#: This tree's inbox - the root a bundle file is placed against.
DEFAULT_INBOX: Final = REPO_ROOT / INBOX_DIR

#: One plain path component of a bundle path: printable, no separator, drive
#: or wildcard character, no leading space, and no trailing dot or space -
#: Windows strips those, so ``LICENSE.`` would alias ``LICENSE``.
_PLAIN_COMPONENT: Final = re.compile(r"[A-Za-z0-9._+-](?:[A-Za-z0-9._+ -]*[A-Za-z0-9_+-])?")

#: Names a bundle or bundle file may never take, compared case-insensitively.
_RESERVED_NAMES: Final = frozenset({INBOX_DIR.casefold(), OUTBOX_DIR.casefold()})

#: The Windows reparse-point attribute - a junction, a symlink, or another link.
_REPARSE_POINT: Final = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

#: Components below the inbox in a bundle file's path: the bundle, then the file.
_BUNDLE_DEPTH: Final = 2


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
BUNDLE_PATH_REFUSED: Final = "bundle-path-refused"
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
        BUNDLE_PATH_REFUSED,
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
    git = resolve_tool("git")
    if git is None:
        return None
    try:
        proc = subprocess.run(
            [
                git,
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


def _is_plain(component: str) -> bool:
    """Whether ``component`` is one plain path component a bundle path may use."""
    return component not in {".", ".."} and _PLAIN_COMPONENT.fullmatch(component) is not None


def inbox_rel(parts: tuple[str, ...]) -> tuple[str, str] | str:
    """Map a resolved note's parts below the resolved inbox to its outbox path.

    Returns:
        ``(rel, bundle)``: for one part, the bare name and ``""``; for two
        plain, unreserved parts, ``"<bundle>/<file>"`` and the bundle name.
        Otherwise :data:`BUNDLE_PATH_REFUSED`.
    """
    if len(parts) == 1:
        return parts[0], ""
    if len(parts) != _BUNDLE_DEPTH or not all(_is_plain(part) for part in parts):
        return BUNDLE_PATH_REFUSED
    if any(part.casefold() in _RESERVED_NAMES for part in parts):
        return BUNDLE_PATH_REFUSED
    return parts[0] + "/" + parts[1], parts[0]


def _resolve_note(note: Path) -> Path | None:
    """The note's real path, through its parent when the note itself is absent."""
    try:
        return note.resolve(strict=True)
    except OSError:
        pass
    if note.name in {"", ".", ".."}:
        return None
    try:
        return note.parent.resolve(strict=True) / note.name
    except OSError:
        return None


def _inside(note: Path, inbox_dir: Path, inbox: Path) -> bool:
    """Whether ``note`` is spelled inside the inbox, lexically - nothing is resolved."""
    # abspath, not resolve: the point is the spelling, before any link is followed.
    spelled = Path(os.path.normcase(os.path.abspath(note)))  # noqa: PTH100
    given_root = os.path.normcase(os.path.abspath(inbox_dir))  # noqa: PTH100
    roots = {given_root, os.path.normcase(str(inbox))}
    return any(spelled.is_relative_to(Path(root)) for root in roots)


def _agrees(note: Path, parts: tuple[str, ...]) -> bool:
    """Whether the spelling's tail names ``parts`` and no placed component is a link."""
    given = note.parts[-len(parts) :] if parts else ()
    if [os.path.normcase(p) for p in given] != [os.path.normcase(p) for p in parts]:
        return False
    return not (_is_link(note) or (len(parts) == _BUNDLE_DEPTH and _is_link(note.parent)))


def _placement(note: Path, inbox_dir: Path) -> tuple[str, str, Path | None] | str:
    """Place ``note`` against the resolved inbox; see the module docstring.

    Returns:
        ``(rel, bundle, real)`` - ``real`` is the resolved note to read, or
        None where the note keeps the pre-CS-1232 bare-name answer - or
        :data:`BUNDLE_PATH_REFUSED`.
    """
    try:
        inbox = inbox_dir.resolve(strict=True)
    except OSError:
        return note.name, "", None
    real = _resolve_note(note)
    if real is None or not real.is_relative_to(inbox):
        if _inside(note, inbox_dir, inbox):
            return BUNDLE_PATH_REFUSED
        return note.name, "", None
    parts = real.relative_to(inbox).parts
    if not _agrees(note, parts):
        return BUNDLE_PATH_REFUSED
    placed = inbox_rel(parts)
    if isinstance(placed, str):
        return placed
    return placed[0], placed[1], real


def _is_link(path: Path) -> bool:
    """Whether ``path`` is a symlink, a junction, or any other reparse point."""
    try:
        status = path.lstat()
    except OSError:
        return False
    if stat.S_ISLNK(status.st_mode):
        return True
    return bool(getattr(status, "st_file_attributes", 0) & _REPARSE_POINT)


def verify_main_note(
    note_path: Path,
    *,
    config_path: Path | None = None,
    inbox_dir: Path | None = None,
) -> Verdict:
    """Decide whether an inbox note is MAIN's, per ``CLAUDE.md`` section 6.1.

    Never raises: an unexpected failure anywhere in the check is the fixed
    reason ``check-failed``, so no exception text can carry a path out.

    Args:
        note_path: The note in this tree's inbox, or a file one bundle
            directory below it.
        config_path: The local configuration naming MAIN's root. Defaults to
            :data:`DEFAULT_CONFIG`; only a test passes another.
        inbox_dir: This tree's inbox. Defaults to :data:`DEFAULT_INBOX`; only
            a test passes another.

    Returns:
        ``Verdict(ok=True, reason="verified")`` when the note's SHA-256 equals
        HEAD's blob for the same-named file in MAIN's outbox - or, for a bundle
        file, the same bundle-relative path - and that file is tracked and
        byte-identical to the blob in both index and working tree; otherwise a
        refusal naming its reason.
    """
    try:
        reason, digest = _check(
            Path(note_path),
            DEFAULT_CONFIG if config_path is None else config_path,
            DEFAULT_INBOX if inbox_dir is None else inbox_dir,
        )
    except Exception:  # the boundary: no exception text may escape
        reason, digest = CHECK_FAILED, ""
    ok = reason == VERIFIED
    return Verdict(ok=ok, reason=reason, digest=digest if ok else "")


def _check(note: Path, config_path: Path, inbox_dir: Path) -> tuple[str, str]:
    """Run every step in order; return the first refusal, or VERIFIED and the digest."""
    resolved = _main_root(config_path)
    if isinstance(resolved, str):
        return resolved, ""
    placed = _placement(note, inbox_dir)
    if isinstance(placed, str):
        return placed, ""
    rel, bundle, real = placed
    located = _locate(resolved, rel, bundle)
    if located is not None:
        return located, ""
    blob = _committed_blob(resolved, OUTBOX_DIR + "/" + rel)
    if isinstance(blob, str):
        return blob, ""
    return _compare(note if real is None else real, resolved / OUTBOX_DIR / rel, blob, real)


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


def _locate(root: Path, rel: str, bundle: str) -> str | None:
    """Refuse a missing root, an unusable repository, or an absent outbox file.

    ``rel`` is the outbox-relative path; ``bundle`` names its bundle directory,
    or is empty for a top-level note. A linked bundle directory is absent.
    """
    if not root.is_dir():
        return MAIN_ROOT_ABSENT
    if rel in {"", ".", ".."}:
        return NOTE_UNREADABLE
    repository = _repository(root)
    if repository is not None:
        return repository
    if bundle and _is_link(root / OUTBOX_DIR / bundle):
        return OUTBOX_FILE_ABSENT
    outbox_file = root / OUTBOX_DIR / rel
    if outbox_file.is_symlink() or not outbox_file.is_file():
        return OUTBOX_FILE_ABSENT
    return None


def read_note(path: Path) -> tuple[bytes, os.stat_result] | None:
    """Read ``path`` through ONE open; return its bytes and the open file's stat."""
    try:
        with path.open("rb") as handle:
            return handle.read(), os.fstat(handle.fileno())
    except OSError:
        return None


def _still(path: Path, opened: os.stat_result) -> bool:
    """Whether ``path`` still names the file that was opened."""
    try:
        return os.path.samestat(opened, path.stat())
    except OSError:
        return False


def _compare(note: Path, outbox_file: Path, blob: bytes, placed: Path | None) -> tuple[str, str]:
    """Compare the working-tree file with the blob, then the note with the blob.

    ``placed`` is the resolved note when the note was placed against the inbox;
    the file opened must then still be the file at that path.

    Returns:
        The reason, and on VERIFIED the SHA-256 hex of the note bytes hashed.
    """
    try:
        outbox_bytes = outbox_file.read_bytes()
    except OSError:
        return OUTBOX_UNREADABLE, ""
    if outbox_bytes != blob:
        return WORKTREE_DIFFERS, ""
    read = read_note(note)
    if read is None:
        return NOTE_UNREADABLE, ""
    if placed is not None and not _still(placed, read[1]):
        return NOTE_UNREADABLE, ""
    note_bytes = read[0]
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
    parser.add_argument("note", type=Path, help="the inbox note, or a bundle file, to check")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="the local configuration naming MAIN's root (default: the gitignored file)",
    )
    parser.add_argument(
        "--inbox",
        type=Path,
        default=None,
        help="this tree's inbox (default: the repository's moon_sync_inbox)",
    )
    args = parser.parse_args(argv)
    try:
        verdict = verify_main_note(args.note, config_path=args.config, inbox_dir=args.inbox)
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
