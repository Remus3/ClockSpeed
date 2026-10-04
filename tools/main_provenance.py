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
:data:`DEFAULT_INBOX`; a test injects another with ``inbox_dir``.

PLACEMENT IS BY FILE IDENTITY, NEVER BY SPELLING. The note is stat-ed
(following links) for its ``(st_dev, st_ino)``; a zero file index is
``check-failed``, and a note that cannot be stat-ed is ``note-unreadable``.
The tool then walks the resolved inbox ITSELF with ``os.scandir``, never
following a link and ignoring every link entry, and records the identity of
every entry at every depth, the inbox included. The note is placed by the
ON-DISK names of the entries carrying its identity:

- exactly one, a regular file directly in the inbox: its bare name;
- exactly one, a regular file one directory down: ``<bundle-dir>/<file>``,
  both names plain (``_PLAIN_COMPONENT``) and neither ``moon_sync_inbox`` nor
  ``moon_sync_outbox`` in any case;
- none: the note is outside the inbox, and keeps the pre-CS-1232 bare-name
  answer;
- anything else - two entries (a hard link at two inbox places), a deeper
  file, a directory, the inbox itself: ``bundle-path-refused``.

So no spelling - the Windows verbatim prefix, an admin-share UNC path, an 8.3 short name, a
trailing dot, a ``..`` hop, a junction aliasing the inbox - can move a note
from its place. Two rules still look at the path given, each by identity or
by one name, never by comparing spellings: the note's own final component
must name the entry it was placed as (under ``normcase``), so ``LICENSE.`` is
not verified as ``LICENSE``; and no ancestor of the path given, the note
included, may be a link that sits inside the inbox or leads to anything
inside it other than the inbox root - so ``inbox/x/LICENSE`` with ``x`` a
junction back to the inbox, or a link from outside to a bundle directory, is
refused, while a link standing for the whole inbox is followed. A hard link
is a plain file and is placed as its inbox twin. On MAIN's side a bundle
directory that is a link is refused as ``outbox-file-absent``, the same
reason a linked outbox file gets.

THE INBOX AND ITS CENSUS FAIL CLOSED. An absent inbox is NOT "no inbox":
every note is refused as ``inbox-absent`` - a worktree carries no inbox, and
:data:`DEFAULT_INBOX` derives from this file's location, so the bare-name
answer there would bind a bundle file elsewhere to MAIN's top-level blob. Any
other error resolving the inbox, listing it, or stat-ing any entry at any
depth is ``census-failed``. Neither ever falls back to the bare name.

DECLARED DIVERGENCES from the pre-CS-1232 tool (41f1835) for a note in the
inbox; a plain top-level note spelled plainly otherwise answers exactly as it
did, pinned by measured parity arms:

- a missing note is ``note-unreadable`` before MAIN's outbox is consulted
  (41f1835 named an outbox fault first where there was one);
- a final component that is not the on-disk name (a trailing dot or space,
  an 8.3 short name) is ``bundle-path-refused`` (41f1835: the name as given);
- a note reached through a link into or inside the inbox, a note at two inbox
  places, a deeper file, a directory, or the inbox itself is
  ``bundle-path-refused`` (41f1835: the bare name);
- an absent inbox refuses every note as ``inbox-absent`` (41f1835 had no
  notion of an inbox and answered by bare name);
- an inbox census error is ``census-failed``, a zero file index
  ``check-failed``;
- a note outside the inbox hard-linked into it is placed as its inbox twin;
- a file one bundle directory down is looked up as ``<bundle-dir>/<file>``.

THE BYTES HASHED ARE THE FILE PLACED. A placed note is read through the
inbox entry it was placed as, by ONE open; the open file must carry the
note's identity, and a fresh stat of the entry afterwards must still name
the opened file - otherwise ``note-unreadable``. Identity alone cannot see a
file deleted and a new one given the SAME identity: off Windows a freed inode
number is commonly reissued to the very next file created (measured on
ubuntu CI, CS-1232). So off Windows the note is PINNED - held open from
before its identity is taken until the bytes are compared - and an inode
that is still open is never freed, so no replacement can carry its number;
the pin must carry the note's identity, else ``note-unreadable``. Windows
needs no pin and takes none: its file index carries a sequence number, so a
reused record is a new identity, and an open handle there would block the
delete instead of witnessing it.

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
CENSUS_FAILED: Final = "census-failed"
INBOX_ABSENT: Final = "inbox-absent"
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
        CENSUS_FAILED,
        INBOX_ABSENT,
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


#: A file's identity: its device and file index.
Identity = tuple[int, int]


def _identity(status: os.stat_result) -> Identity:
    return status.st_dev, status.st_ino


@dataclass(frozen=True)
class _Entry:
    """One inbox entry: its on-disk parts below the inbox, and its kind."""

    parts: tuple[str, ...]
    regular: bool


def inbox_census(inbox: Path) -> dict[Identity, list[_Entry]]:
    """Every entry under ``inbox`` by identity, the inbox itself included.

    Walks with ``os.scandir``; a link entry is ignored and never descended.
    """
    found: dict[Identity, list[_Entry]] = {_identity(inbox.stat()): [_Entry((), False)]}
    pending: list[tuple[Path, tuple[str, ...]]] = [(inbox, ())]
    while pending:
        here, parts = pending.pop()
        with os.scandir(here) as entries:
            for entry in entries:
                path = Path(entry.path)
                status = path.lstat()
                if _is_link_status(status):
                    continue
                below = (*parts, entry.name)
                is_dir = stat.S_ISDIR(status.st_mode)
                regular = stat.S_ISREG(status.st_mode)
                found.setdefault(_identity(status), []).append(_Entry(below, regular))
                if is_dir:
                    pending.append((path, below))
    return found


def _linked_in(note: Path, inside: dict[Identity, list[_Entry]], root: Identity) -> bool:
    """Whether an ancestor of ``note`` (itself included) is a link into the inbox.

    A link counts when its parent is inside the inbox, or when it leads to
    anything inside the inbox other than the inbox root.
    """
    given = Path.cwd() / note
    for path in (given, *given.parents):
        if not is_link(path):
            continue
        try:
            parent = _identity(path.parent.stat())
            target = _identity(path.stat())
        except OSError:
            return True
        if parent in inside or (target in inside and target != root):
            return True
    return False


#: A placement: the outbox-relative path, the bundle name (empty for a
#: top-level note), the inbox entry to read and the note's identity - both
#: None where the note keeps the pre-CS-1232 bare-name answer.
Placed = tuple[str, str, Path | None, Identity | None]


def _survey(inbox_dir: Path) -> tuple[Path, dict[Identity, list[_Entry]], Identity] | str:
    """Resolve and census the inbox, or a refusal - every failure is fail-closed."""
    try:
        inbox = inbox_dir.resolve(strict=True)
    except FileNotFoundError:
        return INBOX_ABSENT
    except OSError:
        return CENSUS_FAILED
    try:
        return inbox, inbox_census(inbox), _identity(inbox.stat())
    except OSError:
        return CENSUS_FAILED


def _note_identity(note: Path) -> Identity | str:
    """The note's identity, following links; or a refusal reason."""
    try:
        identity = _identity(note.stat())
    except OSError:
        return NOTE_UNREADABLE
    if identity[1] == 0:
        return CHECK_FAILED
    return identity


def _placement(note: Path, inbox_dir: Path) -> Placed | str:
    """Place ``note`` by its file identity; see the module docstring."""
    identity = _note_identity(note)
    if isinstance(identity, str):
        return identity
    surveyed = _survey(inbox_dir)
    if isinstance(surveyed, str):
        return surveyed
    inbox, inside, root = surveyed
    if _linked_in(note, inside, root):
        return BUNDLE_PATH_REFUSED
    entries = inside.get(identity, [])
    if not entries:
        return note.name, "", None, None
    return _place_entry(note, entries, inbox, identity)


def _place_entry(
    note: Path, entries: list[_Entry], inbox: Path, identity: Identity
) -> Placed | str:
    """Place a note whose identity the inbox census holds."""
    if len(entries) != 1 or not entries[0].regular:
        return BUNDLE_PATH_REFUSED
    parts = entries[0].parts
    if os.path.normcase(note.name) != os.path.normcase(parts[-1]):
        return BUNDLE_PATH_REFUSED
    placed = inbox_rel(parts)
    if isinstance(placed, str):
        return placed
    return placed[0], placed[1], inbox.joinpath(*parts), identity


def _is_link_status(status: os.stat_result) -> bool:
    """Whether an lstat result is a symlink, a junction, or any other reparse point."""
    if stat.S_ISLNK(status.st_mode):
        return True
    return bool(getattr(status, "st_file_attributes", 0) & _REPARSE_POINT)


def is_link(path: Path) -> bool:
    """Whether ``path`` is a symlink, a junction, or any other reparse point.

    Fails closed: a missing path is not a link, but a path whose kind cannot
    be read for any other reason counts as one.
    """
    try:
        status = path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return _is_link_status(status)


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


def _steps(note: Path, config_path: Path, inbox_dir: Path, pin: int | None) -> tuple[str, str]:
    """Run every step in order; return the first refusal, or VERIFIED and the digest."""
    resolved = _main_root(config_path)
    if isinstance(resolved, str):
        return resolved, ""
    placed = _placement(note, inbox_dir)
    if isinstance(placed, str):
        return placed, ""
    rel, bundle, entry, identity = placed
    located = _locate(resolved, rel, bundle)
    if located is not None:
        return located, ""
    blob = _committed_blob(resolved, OUTBOX_DIR + "/" + rel)
    if isinstance(blob, str):
        return blob, ""
    target = note if entry is None else entry
    return _compare(target, resolved / OUTBOX_DIR / rel, blob, identity, pin)


def _check(note: Path, config_path: Path, inbox_dir: Path) -> tuple[str, str]:
    """Run every step with the note pinned where a pin is needed; see the module docstring."""
    pin = _pin(note)
    try:
        return _steps(note, config_path, inbox_dir, pin)
    finally:
        if pin is not None:
            os.close(pin)


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
    if bundle and is_link(root / OUTBOX_DIR / bundle):
        return OUTBOX_FILE_ABSENT
    outbox_file = root / OUTBOX_DIR / rel
    if outbox_file.is_symlink() or not outbox_file.is_file():
        return OUTBOX_FILE_ABSENT
    return None


#: Whether a placed note must be pinned open across the check: off Windows a
#: freed inode number is reissued, so identity alone cannot see a replacement.
_PIN_NEEDED: Final = os.name != "nt"


def _pin(note: Path) -> int | None:
    """Hold ``note`` open where :data:`_PIN_NEEDED`; None where unneeded, unopenable or not regular.

    The pin is taken BEFORE placement has seen the note's kind, so it opens
    non-blocking (a FIFO cannot hang the check), never as a controlling
    terminal, never through a final-component link, and keeps only a regular
    file - anything else is released and None returned, which a placed note
    turns into ``note-unreadable``. The bytes are never read through the pin.
    """
    if not _PIN_NEEDED:
        return None
    flags = os.O_RDONLY
    for name in ("O_NONBLOCK", "O_NOCTTY", "O_NOFOLLOW"):
        flags |= getattr(os, name, 0)
    try:
        fd = os.open(note, flags)
    except OSError:
        return None
    try:
        regular = stat.S_ISREG(os.fstat(fd).st_mode)
    except OSError:
        regular = False
    if not regular:
        os.close(fd)
        return None
    return fd


def _pinned(pin: int | None, identity: Identity) -> bool:
    """Whether the pin holds the placed identity, or no pin is needed."""
    if not _PIN_NEEDED:
        return True
    if pin is None:
        return False
    try:
        return _identity(os.fstat(pin)) == identity
    except OSError:
        return False


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


def _compare(
    note: Path, outbox_file: Path, blob: bytes, identity: Identity | None, pin: int | None
) -> tuple[str, str]:
    """Compare the working-tree file with the blob, then the note with the blob.

    ``identity`` is the placed note's identity, or None for a note outside the
    inbox; when given, the file opened must carry it and still be the file at
    ``note``, and where a pin is needed ``pin`` must hold it.

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
    if identity is not None and (
        not _pinned(pin, identity) or _identity(read[1]) != identity or not _still(note, read[1])
    ):
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
