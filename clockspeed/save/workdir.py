"""The work directory: the one and only write in the save package.

WHY THIS MODULE EXISTS. Clockspeed never writes to the game install and never
modifies a save file (CLAUDE.md non-negotiable 1,
memory/never-write-to-the-game.md). That is an invariant, not a preference, and
an invariant is something a test asserts. Confining every write in
``clockspeed/save/`` to this one module is what makes it assertable: "no other
save module can write" stops being a rule reviewers have to remember and
becomes a static, machine-checkable property of the package
(docs/adr/0007 Decision item 6, docs/ARCHITECTURE.md section 1.1).

That commitment is only worth anything if this module keeps its own write
surface small enough to audit at a glance, so it is deliberately narrow:

  * ONE call opens a file for writing - ``_stream_copy``.
  * ONE call renames         - ``_replace_with_retry``.
  * ONE call removes         - ``_remove_quietly``.
  * ONE call creates a directory - ``_make_dir``.

Every other function in this file reads, resolves or decides. A change that
adds a second write-capable call site is the change that should be questioned.

THE MECHANISM BEHIND THE COPY RULE, which is concrete rather than
precautionary. The game holds file handles during autosave, so parsing a save
where it lies eventually meets a locked or half-written file. Not on the first
run - which is exactly what makes it dangerous - but on the run that happens to
overlap an autosave. The failure is intermittent, timing dependent, and
presents as a corrupt-save bug rather than as a concurrency bug. Copying first
turns a race into a snapshot (BOOTSTRAP.md section 8.2).

WHY ``copy_for_read`` CAN REFUSE. A copy written back INTO the save directory
would break the invariant just as thoroughly as an in-place parse would, so the
destination is checked against the save root, the account directory and the
game install before anything is created. Both sides are RESOLVED before they
are compared, because a relative path, a ``..`` traversal and a symlink all
name a directory that a string comparison says is outside the save root and the
filesystem says is inside it. The check runs twice - once before the work
directory is created and once after - because the first check is what prevents
the mkdir, and the second is what closes the window between deciding and
writing.

ORDER MATTERS MORE THAN THE CHECK DOES. A refusal raised after the directory
had been created would be a report of a violation rather than a prevention of
one, which is why ``test_a_refused_destination_is_not_created`` asserts on the
absence of the directory and not merely on the exception.

PRIVACY. The copies this module makes ARE real saves: the header carries the
platform name, a platform account id and the player's display name in plaintext
(BOOTSTRAP.md section 2.2, CLAUDE.md non-negotiables 11 and 12). Two
consequences, both load-bearing. The work root is gitignored - ``/work/`` in
.gitignore, asserted by ``test_the_default_work_root_is_gitignored`` against
git itself rather than against the text of the file. And every path this module
renders into an exception goes through :func:`clockspeed.data.locate.redact`
first. Messages carry a redacted path, a reason and at most an errno; never
file content, never a header string, never a token.

``purge_work_dir`` exists because those copies accumulate across runs. It
removes only what this module created, and proves that by two independent
conditions rather than one - the file sits in this module's own copies
directory AND carries this module's suffix. A purge keyed on the directory
alone would delete an operator's file that happened to be sitting in it.

SEAM. This module sits at the bottom of the save layer. It consumes
``clockspeed.data.locate`` for the resolvers and for ``redact``, and imports
nothing from any layer above it. It does not parse: it hands back a path, and
what the bytes mean is the next module's problem.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from clockspeed.data import locate

# --- override surface -------------------------------------------------------

#: Same shape as the resolvers in clockspeed/data/locate.py - a
#: CLOCKSPEED_-prefixed environment name first, then the gitignored
#: config/local.json, then the default.
ENV_WORK_ROOT = "CLOCKSPEED_WORK_ROOT"
CONFIG_WORK_ROOT = "work_root"

WORK_DIR_NAME = "work"

# Copies live in a NAMED SUBDIRECTORY of the work root rather than directly in
# it. That is what lets purge_work_dir be precise: the work root is the
# operator's directory and may hold anything, while this subdirectory is this
# module's and holds only what it put there.
COPIES_DIR_NAME = "saves"

# The second of purge's two conditions. Carried on the copy's own name so a
# file that lands in the copies directory by some other route is still not
# mistaken for one of ours.
COPY_SUFFIX = ".copy.sav"

# A partially written copy. Never handed to a caller: the copy is streamed to
# this name and renamed into place, so a reader never sees a half-written file
# (CLAUDE.md non-negotiable 5 - atomic writes for anything another process may
# read).
PARTIAL_SUFFIX = ".partial"

SAVE_SUFFIX = ".sav"

# Streamed rather than read whole. A save is small today and the operator's
# world only grows; a read_bytes() of an arbitrarily large file is the one
# unbounded allocation this module could contain.
_COPY_BLOCK_BYTES = 1 << 20

# Windows lets a virus scanner or an indexer hold a handle on a file that was
# closed microseconds ago, and os.replace then fails with PermissionError. The
# retry is short, bounded and specific to that error class.
_RENAME_ATTEMPTS = 5
_RENAME_BACKOFF_SECONDS = 0.05


# --- errors -----------------------------------------------------------------


class WorkDirError(Exception):
    """Base for every error this module raises.

    A caller that catches this has caught all of them, which is why the two
    below inherit from it rather than from OSError.
    """


class SourceUnreadableError(WorkDirError):
    """The save to copy is absent, is not a file, or could not be read."""


class DestinationRefusedError(WorkDirError):
    """The copy would have landed inside the save root or the game install.

    This is the code-level half of the never-write rule. It is raised BEFORE
    anything is created, so catching it means nothing was written.
    """


# --- resolution -------------------------------------------------------------


def _repo_root() -> Path:
    """Return the repository root, derived from this file's own location."""
    return Path(__file__).resolve().parents[2]


def work_root() -> Path:
    """Return where save copies are kept.

    Order: ``CLOCKSPEED_WORK_ROOT``, then config/local.json ``work_root``, then
    ``<repo>/work``.

    ASKING DOES NOT CREATE. Unlike the resolvers in
    ``clockspeed/data/locate.py``, which answer None for a directory that is
    not there, this returns a path that need not exist yet - it names a
    destination rather than discovering something. It has no side effect: a
    module that created a directory in the repo merely because something
    imported it and asked a question would do so on every machine, including
    one with no game and no save.

    Returns:
        The work root. May not exist.
    """
    override = (os.environ.get(ENV_WORK_ROOT) or "").strip()
    if not override:
        override = (locate.local_config().get(CONFIG_WORK_ROOT) or "").strip()
    if override:
        return Path(override)
    return _repo_root() / WORK_DIR_NAME


def _resolve_work_root(override: Path | None) -> Path:
    """Return the caller's work root, or the configured one."""
    return Path(override) if override is not None else work_root()


def _copies_dir(root: Path) -> Path:
    """Return the subdirectory of ``root`` that this module owns."""
    return root / COPIES_DIR_NAME


def _resolved(path: Path) -> Path | None:
    """Fully resolve a path, or return None if it cannot be resolved.

    Non-strict: a path that does not exist yet still has its existing prefix
    resolved, so a symlinked parent is followed even when the leaf has not been
    created. That is what makes the pre-mkdir refusal check sound.

    Args:
        path: The path to resolve.

    Returns:
        The resolved path, or None.
    """
    try:
        return path.resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def _forbidden_roots() -> list[tuple[Path, str]]:
    """List the directories a copy must never land in, each with a safe label.

    The account directory is included alongside the save root even though it
    normally sits inside it, because ``CLOCKSPEED_ACCOUNT_DIR`` may name a
    directory somewhere else entirely - ``locate.resolve_account_dir`` documents
    exactly that case - and a copy written into a relocated account directory is
    the same mistake.

    Returns:
        (resolved directory, label) pairs. The label is a fixed English string
        so a message can say WHICH root refused without rendering a path.
    """
    save_root = locate.resolve_save_root()
    candidates: list[tuple[Path | None, str]] = [
        (save_root, "the save root"),
        (locate.resolve_account_dir(save_root), "the account directory"),
        (locate.resolve_game_dir()[0], "the game install"),
    ]
    roots: list[tuple[Path, str]] = []
    for candidate, label in candidates:
        if candidate is None:
            continue
        resolved = _resolved(candidate)
        if resolved is not None and all(resolved != known for known, _ in roots):
            roots.append((resolved, label))
    return roots


def _refuse_if_forbidden(destination: Path) -> None:
    """Raise unless ``destination`` provably sits outside every forbidden root.

    PROVABLY is the operative word. A destination that cannot be resolved is
    refused rather than allowed: an unresolvable path cannot be shown to be
    outside the save root, and the project's rule when a check is uncertain is
    to refuse.

    Args:
        destination: The directory a copy would be written into.

    Raises:
        DestinationRefusedError: It resolves inside a forbidden root, or it
            cannot be resolved at all.
    """
    resolved = _resolved(destination)
    if resolved is None:
        raise DestinationRefusedError(
            "the destination cannot be resolved, so it cannot be shown to sit outside the "
            f"save root and the game install: {locate.redact(destination)}"
        )
    for root, label in _forbidden_roots():
        if resolved.is_relative_to(root):
            raise DestinationRefusedError(
                f"refusing to write inside {label}: {locate.redact(resolved)}. Clockspeed "
                "never writes to the game install or the save directory."
            )


# --- the four mutating calls, one each ---------------------------------------


def _make_dir(path: Path) -> None:
    """Create a directory. THE ONLY mkdir in this module.

    Args:
        path: The directory to create, with its parents.

    Raises:
        WorkDirError: It could not be created.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WorkDirError(
            f"cannot create the work directory {locate.redact(path)}: errno {exc.errno}"
        ) from exc


def _stream_copy(source: Path, destination: Path) -> int:
    """Copy bytes from ``source`` to ``destination``. THE ONLY WRITE.

    The source is opened ``rb`` and the destination ``wb`` - binary both ways,
    because a save is binary and a text-mode copy would rewrite every 0x0A on
    Windows. The source handle is acquired first, so a missing or locked source
    fails before the destination is created rather than after.

    Args:
        source: The file to read.
        destination: The file to write.

    Returns:
        The number of bytes copied.
    """
    copied = 0
    with source.open("rb") as reader, destination.open("wb") as writer:
        while True:
            block = reader.read(_COPY_BLOCK_BYTES)
            if not block:
                break
            writer.write(block)
            copied += len(block)
    return copied


def _replace_with_retry(partial: Path, destination: Path) -> None:
    """Rename the finished copy into place. THE ONLY rename in this module.

    Only PermissionError is retried, and only briefly. On Windows a scanner or
    an indexer can still hold a handle on a file closed moments ago; every other
    OSError is a real failure and propagates immediately.

    Args:
        partial: The fully written temporary file.
        destination: Its final name.

    Raises:
        OSError: The rename did not succeed within the retry budget.
    """
    last: OSError | None = None
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            partial.replace(destination)
        except PermissionError as exc:
            last = exc
            time.sleep(_RENAME_BACKOFF_SECONDS * (attempt + 1))
        else:
            return
    if last is None:
        last = OSError("the copy could not be renamed into place")
    raise last


def _remove_quietly(path: Path) -> bool:
    """Delete one file, reporting rather than raising. THE ONLY delete.

    Args:
        path: The file to remove.

    Returns:
        True if it is gone because this call removed it.
    """
    try:
        path.unlink()
    except OSError:
        return False
    return True


# --- the public surface -----------------------------------------------------


def _mtime_ns(path: Path) -> int:
    """Return a modification time in nanoseconds, or 0 for anything unreadable.

    Nanoseconds rather than the float seconds ``locate`` uses, because two
    saves written in the same second are ordinary and a whole-second field
    cannot tell them apart.
    """
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


def _save_files(directory: Path) -> list[Path]:
    """List the save files directly inside ``directory``.

    ONE FLAT SCAN COVERS BOTH KINDS. A manual save and an autosave are siblings
    in the account directory that differ only by filename -
    ``<world>_<DDMMYY>-<HHMMSS>.sav`` against ``<world>_autosave_<N>.sav``
    (BOOTSTRAP.md section 2) - so there is nothing to recurse into. If a future
    probe finds a nested layout, this is the function that grows.

    Args:
        directory: The directory to scan.

    Returns:
        Every ``.sav`` file in it. Empty when the directory is missing or
        unreadable - absent content is reported, never fatal.
    """
    try:
        entries = list(directory.iterdir())
    except OSError:
        return []
    found: list[Path] = []
    for entry in entries:
        try:
            if entry.suffix.lower() == SAVE_SUFFIX and entry.is_file():
                found.append(entry)
        except OSError:
            continue
    return found


def latest_save(account_dir: Path | None = None) -> Path | None:
    """Return the most-recently-modified save, across manual saves and autosaves.

    Ordering is by modification time descending with the FILENAME as a
    tiebreak, so two runs over the same directory return the same answer. An
    advisor that disagrees with itself between runs is a bug (CLAUDE.md
    section 1), and a tie broken by whatever order the filesystem listed things
    in is precisely how that happens.

    Args:
        account_dir: The directory to search. Resolved from the environment,
            config/local.json and auto-detection when omitted.

    Returns:
        The newest save, or None when the directory is absent, empty, or
        nothing resolves. Never raises for any of those - a machine with no
        game installed is a supported state, not an error.
    """
    directory = account_dir
    if directory is None:
        directory = locate.resolve_account_dir(locate.resolve_save_root())
    if directory is None:
        return None
    saves = _save_files(directory)
    if not saves:
        return None
    saves.sort(key=lambda path: (-_mtime_ns(path), path.name))
    return saves[0]


def copy_for_read(source: Path, *, work_root: Path | None = None) -> Path:
    """Copy a save into the work directory and return the copy's path.

    Nothing parses a save in place. See the module docstring for why the game's
    autosave handles make that a correctness issue rather than a courtesy.

    The source is opened read-only and is never opened for write for any
    reason. The destination is checked against the save root, the account
    directory and the game install BEFORE any directory is created, so a
    refusal means nothing was written.

    Args:
        source: The save to copy.
        work_root: Where to put the copy. Defaults to :func:`work_root`.

    Returns:
        The path of the copy. Byte-identical to the source.

    Raises:
        SourceUnreadableError: The source is absent, is not a file, or could
            not be read through.
        DestinationRefusedError: The copy would land inside the save root, the
            account directory or the game install.
        WorkDirError: The work directory could not be created, or the finished
            copy could not be renamed into place.
    """
    resolved_source = _readable_source(source)
    copies = _copies_dir(_resolve_work_root(work_root))

    # BEFORE anything is created. This is the check that prevents the write.
    _refuse_if_forbidden(copies)
    _make_dir(copies)
    # And again now that the directory exists and resolve() is authoritative
    # about it, which closes the window between deciding and writing.
    _refuse_if_forbidden(copies)

    destination = copies / (resolved_source.stem + COPY_SUFFIX)
    partial = destination.with_name(destination.name + PARTIAL_SUFFIX)

    try:
        _stream_copy(resolved_source, partial)
    except OSError as exc:
        _remove_quietly(partial)
        raise SourceUnreadableError(
            f"copying {locate.redact(resolved_source)} failed: "
            f"{type(exc).__name__}, errno {exc.errno}"
        ) from exc

    try:
        _replace_with_retry(partial, destination)
    except OSError as exc:
        _remove_quietly(partial)
        raise WorkDirError(
            f"the copy could not be renamed into place at {locate.redact(destination)}: "
            f"{type(exc).__name__}, errno {exc.errno}"
        ) from exc

    return destination


def _readable_source(source: Path) -> Path:
    """Resolve the source and confirm it is a file that can be read.

    Args:
        source: The candidate save.

    Returns:
        The resolved source path.

    Raises:
        SourceUnreadableError: It is absent, is not a file, or cannot be
            stat'ed.
    """
    candidate = Path(source)
    resolved = _resolved(candidate) or candidate
    try:
        is_file = resolved.is_file()
    except OSError as exc:
        raise SourceUnreadableError(
            f"cannot read {locate.redact(resolved)}: {type(exc).__name__}, errno {exc.errno}"
        ) from exc
    if not is_file:
        raise SourceUnreadableError(f"not a readable file: {locate.redact(resolved)}")
    return resolved


def _is_module_copy(path: Path) -> bool:
    """Return whether ``path`` is a file this module wrote.

    The suffix test is the second of purge's two conditions; the first is that
    the caller only ever offers entries from this module's own copies
    directory.
    """
    name = path.name
    if not name.endswith((COPY_SUFFIX, COPY_SUFFIX + PARTIAL_SUFFIX)):
        return False
    try:
        return path.is_file()
    except OSError:
        return False


def purge_work_dir(*, work_root: Path | None = None) -> int:
    """Delete the save copies this module made and report how many went.

    Removes ONLY this module's own copies: a file has to sit in the copies
    directory AND carry this module's suffix. Two independent conditions rather
    than one, because the work root is the operator's directory and a purge
    that swept it would eventually delete something that was not ours. Nothing
    recurses and no directory is ever removed.

    Args:
        work_root: Which work root to empty. Defaults to :func:`work_root`.

    Returns:
        How many files were removed. Zero when there is nothing there, when the
        directory does not exist, or when it cannot be read - never an
        exception, and never a directory created as a side effect of asking.
    """
    copies = _copies_dir(_resolve_work_root(work_root))
    try:
        entries = sorted(copies.iterdir())
    except OSError:
        return 0
    return sum(1 for entry in entries if _is_module_copy(entry) and _remove_quietly(entry))
