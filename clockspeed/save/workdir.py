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

A ROOT THAT WILL NOT RESOLVE REFUSES RATHER THAN VANISHING (CS-444). Resolution
is what the comparison above is built on, so a forbidden root whose resolution
fails leaves the check with nothing to compare against. That root used to be
dropped from the list, which meant the copy proceeded unchecked against it - a
fail-open in the direction of a write, inside the module the architecture picked
precisely so this invariant would be checkable in one place. It is now carried
as a :class:`ForbiddenRoot` with no resolved path and refuses on sight. A root
the resolvers report as ABSENT is a different fact and still forbids nothing:
having no game installed is a supported state.

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
from collections.abc import Sized
from dataclasses import dataclass
from errno import ENOENT, ENOTDIR
from pathlib import Path
from stat import S_ISREG
from typing import Final

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


def _pathless_cause(exc: OSError) -> OSError:
    """Clone an OSError without the two fields that carry the path.

    ``raise X(...) from exc`` makes the CAUSE's own text part of the formatted
    traceback, so redacting the wrapper's message is not enough on its own:
    ``OSError.__str__`` appends ``filename`` and ``filename2`` verbatim, and
    those hold the home directory, the account directory and the save name.
    Rebuilding from the two NAMED diagnostic fields carries errno and strerror
    across and leaves both filename fields unset, which closes that channel
    while keeping the reason the call failed.

    ``str()`` is the rendering measured here, because that is the one the
    traceback formatter uses. ``repr()`` would have been a false clearance - it
    omits filename even on the leaking original.

    The two-argument form is deliberate. Supplying ``winerror`` as a fourth
    argument renders ``[WinError None]`` whenever the original carried none,
    which is worse than the errno it would replace. The errno-based subclass
    mapping still runs, so a PermissionError stays a PermissionError.

    Args:
        exc: The caught failure. ONLY ``errno`` and ``strerror`` are read.

    Returns:
        A new OSError of the same errno-mapped subclass, carrying no path.
    """
    return OSError(exc.errno, exc.strerror)


# --- what the listing could not read ----------------------------------------

#: The errnos that SETTLE the question instead of leaving it open: the path
#: names nothing at all, or names something that is not a directory. Every
#: other errno - including one this module has no reading of - falls through to
#: the ``UNREADABLE`` codes, so an unrecognised failure is reported as "could
#: not tell" rather than as "nothing there". Only one of those two answers
#: licenses a caller to trust an empty result, and that is the one that has to
#: be earned.
_SETTLED_ERRNOS: Final = (ENOENT, ENOTDIR)

#: No directory is there to hold saves - the path is absent, or names a file.
LISTING_DIRECTORY_ABSENT: Final = "listing-directory-absent"

#: The directory did not list, for a reason that settles nothing.
LISTING_DIRECTORY_UNREADABLE: Final = "listing-directory-unreadable"

#: An entry named as a save names no file - a broken symlink, or one that went
#: away between the listing and the stat.
LISTING_ENTRY_ABSENT: Final = "listing-entry-absent"

#: One entry inside a directory that DID list could not be classified.
LISTING_ENTRY_UNREADABLE: Final = "listing-entry-unreadable"

#: The codes that leave the question open, which is what
#: :attr:`SaveListing.is_complete` tests for. A settled problem is still
#: REPORTED - nothing is dropped - but it does not make an empty result
#: untrustworthy, because it says there was nothing there to find.
_INCONCLUSIVE_CODES: Final = frozenset({LISTING_DIRECTORY_UNREADABLE, LISTING_ENTRY_UNREADABLE})

#: Keyed by code and fixed. Never built from an entry name, a path or an
#: exception, for the reason :class:`ListingProblem` states.
#:
#: EACH LINE IS TRUE OF ITS OWN CODE AND OF NOTHING ELSE. One line covering
#: absent, not-a-directory and refused together is what CS-430 already cost
#: this project once: absence IS evidence that there are no saves, and it is
#: the case that fires on every machine with no game installed, so a shared
#: sentence saying otherwise would be false on the common path.
_LISTING_DETAILS: Final[dict[str, str]] = {
    LISTING_DIRECTORY_ABSENT: (
        "the path names no directory, so it holds no saves and an empty result is the whole answer"
    ),
    LISTING_DIRECTORY_UNREADABLE: (
        "the directory did not list, for a reason that leaves open whether it "
        "holds saves, so an empty result is not evidence that it holds none"
    ),
    LISTING_ENTRY_ABSENT: (
        "an entry named as a save names no file, so it is not a save and is "
        "absent from this listing"
    ),
    LISTING_ENTRY_UNREADABLE: (
        "an entry named as a save could not be read, so whether it is a save "
        "is unknown and it is absent from this listing"
    ),
}


@dataclass(frozen=True)
class ListingProblem:
    """One thing the save listing could not read.

    WHY THIS CARRIES NO NAME AND NO PATH. A save's filename is
    ``<world>_<...>.sav`` and the directory holding it is named for the platform
    account id, so an entry name and the path to it are both personal data
    (CLAUDE.md non-negotiables 3, 11 and 12). An ``OSError`` carries that path
    in several places at once - ``str()`` appends it, and ``filename``,
    ``strerror`` and ``args`` reach it directly - so nothing derived from the
    exception is copied into this type except the errno, which is lifted out as
    a NAMED FIELD.

    Attributes:
        code: One of :data:`LISTING_DIRECTORY_ABSENT`,
            :data:`LISTING_DIRECTORY_UNREADABLE`,
            :data:`LISTING_ENTRY_ABSENT` or :data:`LISTING_ENTRY_UNREADABLE`.
        detail: The fixed line for that code, from :data:`_LISTING_DETAILS`.
        errno: The failure's errno, or None when the exception carried none.
    """

    code: str
    detail: str
    errno: int | None


@dataclass(frozen=True, repr=False)
class SaveListing:
    """What one directory scan found, and what it could not read.

    THE PAIR IS THE POINT. A bare list of paths has two indistinguishable
    causes for being short - the directory really holds that many saves, or
    something was swallowed on the way - and this layer is deliberately
    fail-soft, so the second cause used to vanish. Carrying the problems beside
    the saves is what makes "absent content is reported, never fatal" true of
    the code rather than only of its docstring.

    Attributes:
        saves: The ``.sav`` files that were confirmed to be regular files.
        problems: Everything the scan could not read. Empty on a clean scan.
    """

    saves: tuple[Path, ...]
    problems: tuple[ListingProblem, ...]

    def __repr__(self) -> str:
        """Count the saves, show the problems, and never render a path.

        A save's filename is ``<world>_<...>.sav`` and the directory holding it
        is named for the platform account id, so every element of ``saves`` is
        personal data - non-negotiables 3, 11 and 12. This type rendered those
        paths in full until CS-852, because a dataclass with no ``__repr__``
        generates one from its fields and nobody had written one.

        ``problems`` IS SHOWN RATHER THAN COUNTED, and that is deliberate on two
        grounds. :class:`ListingProblem` carries no name and no path by
        construction - its own docstring is explicit that only ``errno`` is
        lifted off the ``OSError`` - so there is nothing in it to withhold.
        And withholding it would be a CLAIM that it is sensitive: a field this
        repr does not disclose is one the CS-850 sweep then treats as withheld,
        which turned an existing errno-only assertion in the workdir tests into
        a leak finding. Counting a safe field is not a free precaution.

        THE COUNT CANNOT RAISE, AND THE STATED BOUND IS NARROWER THAN THE
        FIRST DRAFT CLAIMED. ``is_complete`` was called originally and reads
        ``problem.code`` off every element, so a forced arm planting a value
        the tuple cannot really hold turned the repr into an exception. The
        replacement then called ``len`` directly and STILL raised on
        ``saves=None``, which a CS-852 adversary demonstrated against a
        GENERATED repr that had been total there. The count is now guarded.
        ``problems`` is rendered with ``!r``, so an element whose own repr
        raises still propagates - that exposure is identical to the generated
        repr this replaced, and is stated rather than claimed away.

        Returns:
            The safe rendering.
        """
        saves = str(len(self.saves)) if isinstance(self.saves, Sized) else "?"
        return f"{type(self).__name__}(saves={saves}, problems={self.problems!r})"

    @property
    def is_complete(self) -> bool:
        """Whether an empty ``saves`` can be taken at face value.

        This is the absence of an INCONCLUSIVE problem rather than the absence
        of every problem. A directory that is simply not there answers True
        while still reporting itself, because "there is no such directory" and
        "there are no saves in it" are the same fact; a directory that refused
        to list answers False, because nothing was learned either way.

        Returns:
            True when nothing went unread that might have been a save.
        """
        return not any(problem.code in _INCONCLUSIVE_CODES for problem in self.problems)


def _listing_problem(settled: str, open_question: str, exc: OSError) -> ListingProblem:
    """Report one failure under whichever of two codes its errno earns.

    Args:
        settled: The code for a failure whose errno establishes that there was
            nothing there to find.
        open_question: The code for every other errno, including one this
            module has no reading of.
        exc: The caught failure. Only its ``errno`` is read - a NAMED FIELD -
            because the object and its other attributes carry the path it
            failed on.

    Returns:
        The problem, carrying the fixed detail belonging to the chosen code.
    """
    code = settled if exc.errno in _SETTLED_ERRNOS else open_question
    return ListingProblem(code=code, detail=_LISTING_DETAILS[code], errno=exc.errno)


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


#: The fixed English labels for the three roots. Fixed, and never built from a
#: path, because a message naming WHICH root refused must not render the root
#: itself: the save root's own subdirectory is a platform account id (CLAUDE.md
#: non-negotiable 3).
LABEL_SAVE_ROOT: Final = "the save root"
LABEL_ACCOUNT_DIR: Final = "the account directory"
LABEL_GAME_INSTALL: Final = "the game install"


@dataclass(frozen=True, repr=False)
class ForbiddenRoot:
    """One directory a copy must not land in, and whether it could be resolved.

    ``resolved`` IS NULLABLE AND THAT IS THE WHOLE OF CS-444. This type used to
    be a plain ``(Path, str)`` pair, which left no way to express a root that is
    THERE and would not resolve, so that root was dropped from the list instead
    - and a dropped root is a root the destination check never compares against.
    The failure direction was a write into the directory the check exists to
    protect, so the state is now carried rather than discarded.

    TWO DIFFERENT FACTS SHARE THE VALUE None AND THIS TYPE ONLY CARRIES ONE OF
    THEM. A resolver in ``clockspeed.data.locate`` answering None means there is
    no such root on this machine - a supported state, and nothing to forbid, so
    no ``ForbiddenRoot`` is built at all. A resolver answering a path that then
    fails to resolve means the root is there and could not be checked, which is
    what a None ``resolved`` records.

    Attributes:
        label: A fixed English string from the three above, so a refusal can say
            which root it could not clear without rendering a path.
        resolved: The fully resolved directory, or None when the root is present
            and its resolution failed.
    """

    label: str
    resolved: Path | None

    def __repr__(self) -> str:
        """Render the fixed label and WHETHER it resolved, never where.

        ``label`` exists so a refusal can say which root it could not clear
        WITHOUT rendering a path - this class's own attribute docstring says so
        in those words. The generated repr rendered ``resolved`` in full anyway,
        an absolute directory under the user profile, which is the design intent
        defeated by the field-rendering repr nobody chose. That is CS-852.

        Returns:
            The safe rendering.
        """
        state = "resolved" if self.resolved is not None else "unresolved"
        return f"{type(self).__name__}(label={self.label!r}, {state})"


def _forbidden_roots() -> list[ForbiddenRoot]:
    """List the directories a copy must never land in, each with a safe label.

    The account directory is included alongside the save root even though it
    normally sits inside it, because ``CLOCKSPEED_ACCOUNT_DIR`` may name a
    directory somewhere else entirely - ``locate.resolve_account_dir`` documents
    exactly that case - and a copy written into a relocated account directory is
    the same mistake.

    A ROOT THAT WOULD NOT RESOLVE IS REPORTED HERE RATHER THAN DROPPED, which is
    CS-444. Dropping it was a fail-OPEN: the caller then had nothing to compare
    a destination against for that root and let the copy through, which is the
    one direction this module's refusals may not fail in. Deduplication is
    applied to resolved roots only - an unresolved one has no path to compare,
    so it has nothing to be a duplicate of.

    Returns:
        One entry per root that is present, in save-root, account-directory,
        install order. An entry whose ``resolved`` is None is a root that could
        not be resolved, which :func:`_refuse_if_forbidden` treats as still
        forbidden.
    """
    save_root = locate.resolve_save_root()
    candidates: list[tuple[Path | None, str]] = [
        (save_root, LABEL_SAVE_ROOT),
        (locate.resolve_account_dir(save_root), LABEL_ACCOUNT_DIR),
        (locate.resolve_game_dir()[0], LABEL_GAME_INSTALL),
    ]
    roots: list[ForbiddenRoot] = []
    seen: list[Path] = []
    for candidate, label in candidates:
        if candidate is None:
            continue
        resolved = _resolved(candidate)
        if resolved is None:
            roots.append(ForbiddenRoot(label=label, resolved=None))
        elif all(resolved != known for known in seen):
            seen.append(resolved)
            roots.append(ForbiddenRoot(label=label, resolved=resolved))
    return roots


def _refuse_if_forbidden(destination: Path) -> None:
    """Raise unless ``destination`` provably sits outside every forbidden root.

    PROVABLY is the operative word. A destination that cannot be resolved is
    refused rather than allowed: an unresolvable path cannot be shown to be
    outside the save root, and the project's rule when a check is uncertain is
    to refuse.

    THE SAME RULE APPLIES TO THE OTHER OPERAND, which is CS-444. A forbidden
    root that is present and would not resolve leaves the comparison with
    nothing to compare against, so the destination cannot be shown to sit
    outside THAT root either, and the refusal follows for the identical reason.
    This is one rule read symmetrically rather than a second policy.

    THE UNRESOLVED ROOT IS NOT COMPARED AGAINST ITS UNRESOLVED PATH, and
    declining that is deliberate. A string comparison against a path that has
    not been resolved is what the module docstring already rejects: a relative
    path, a ``..`` traversal and a symlink each name a directory the comparison
    says is outside the save root and the filesystem says is inside it. Such a
    comparison would answer False for a destination that really is inside, so it
    would fail in the write direction while looking like a check.

    ROOTS ARE TAKEN IN THE ORDER :func:`_forbidden_roots` returns them, which is
    the fixed order of its candidate list. A destination inside a root that DID
    resolve therefore reports that specific root even when a later root did not
    resolve, so the more precise message is the one that survives.

    Args:
        destination: The directory a copy would be written into.

    Raises:
        DestinationRefusedError: It resolves inside a forbidden root, it cannot
            be resolved at all, or a forbidden root could not be resolved.
    """
    resolved = _resolved(destination)
    if resolved is None:
        raise DestinationRefusedError(
            "the destination cannot be resolved, so it cannot be shown to sit outside the "
            f"save root and the game install: {locate.redact(destination)}"
        )
    for root in _forbidden_roots():
        if root.resolved is None:
            raise DestinationRefusedError(
                f"{root.label} is present and did not resolve, so no destination can be shown "
                f"to sit outside it: {locate.redact(resolved)}. Clockspeed never writes to the "
                "game install or the save directory."
            )
        if resolved.is_relative_to(root.resolved):
            raise DestinationRefusedError(
                f"refusing to write inside {root.label}: {locate.redact(resolved)}. Clockspeed "
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
        ) from _pathless_cause(exc)


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


def _save_files(directory: Path) -> SaveListing:
    """List the save files directly inside ``directory``, and what did not read.

    ONE FLAT SCAN COVERS BOTH KINDS. A manual save and an autosave are siblings
    in the account directory that differ only by filename -
    ``<world>_<DDMMYY>-<HHMMSS>.sav`` against ``<world>_autosave_<N>.sav``
    (BOOTSTRAP.md section 2) - so there is nothing to recurse into. If a future
    probe finds a nested layout, this is the function that grows.

    IT REPORTS RATHER THAN RAISES, and that is deliberate rather than lazy: a
    machine with no game installed is a supported state, and the audit spy in
    ``tests/save/test_phase4_gate.py`` depends on this layer swallowing
    ``OSError`` rather than propagating it. What changed under CS-438 is that a
    swallowed failure now leaves a record in the return value instead of
    leaving nothing at all.

    CLASSIFICATION GOES THROUGH ``stat()`` AND NOT THROUGH ``is_file()``, and
    the difference is the whole item. ``Path.is_file()`` collapses two answers
    into one False: an entry that is genuinely not a regular file, and an entry
    it could not read at all. What it does with the underlying ``OSError``
    varies across the interpreter range this project supports - a broken
    symlink's ENOENT is swallowed on every one of them, while an errno pathlib
    does not ignore escapes on some versions and not on others - so a handler
    wrapped around ``is_file()`` is not a place where a failure can be reliably
    noticed. ``stat()`` raises on every failure, which is what makes one
    reportable. A directory named like a save still stats cleanly and is still
    skipped in silence, because that skip is understood.

    THE SUFFIX TEST COMES FIRST, and the entry report's wording depends on it:
    only an entry already named as a save is ever stat'ed, so an entry that
    cannot be read under any other name is never reached and never reported.

    Args:
        directory: The directory to scan.

    Returns:
        The confirmed ``.sav`` files, and one problem for each thing the scan
        could not read - absent content is reported, never fatal. The problem's
        CODE says whether what it could not read leaves any doubt that the
        result is complete.
    """
    try:
        entries = list(directory.iterdir())
    except OSError as exc:
        problem = _listing_problem(LISTING_DIRECTORY_ABSENT, LISTING_DIRECTORY_UNREADABLE, exc)
        return SaveListing((), (problem,))
    found: list[Path] = []
    problems: list[ListingProblem] = []
    for entry in entries:
        if entry.suffix.lower() != SAVE_SUFFIX:
            continue
        try:
            mode = entry.stat().st_mode
        except OSError as exc:
            problems.append(_listing_problem(LISTING_ENTRY_ABSENT, LISTING_ENTRY_UNREADABLE, exc))
            continue
        if S_ISREG(mode):
            found.append(entry)
    return SaveListing(tuple(found), tuple(problems))


def ranked_saves(
    account_dir: Path | None = None,
    *,
    problems: list[ListingProblem] | None = None,
) -> tuple[Path, ...]:
    """Return every save, newest first, across manual saves and autosaves.

    Ordering is by modification time descending with the FILENAME as a
    tiebreak, so two runs over the same directory return the same answer. An
    advisor that disagrees with itself between runs is a bug (CLAUDE.md
    section 1), and a tie broken by whatever order the filesystem listed things
    in is precisely how that happens. :func:`latest_save` is the head of this
    ranking and nothing else, so the two cannot disagree.

    WHY MORE THAN THE HEAD. The newest file is not always one the reader
    accepts: a save re-encoded by a third-party tool is refused, correctly, by
    the object reader. ``world.load_newest_world`` walks this ranking past such
    a refusal and flags it. This module does not parse and does not decide what
    is readable - it hands over the order.

    THE WHOLE ORDER, WITH NO CAP. The first cut handed back three, and three
    refused newest saves then left the companion with no world while readable
    ones remained - the defect again, one level down. Handing over the whole
    ranking costs a stat per save, which this function already paid to sort;
    the walk stops at the first save that loads, and the dashboard's provider
    remembers every refusal by file identity, so a long run of refused files
    is parsed once each and never again.

    Args:
        account_dir: The directory to search. Resolved from the environment,
            config/local.json and auto-detection when omitted.
        problems: A list to extend with whatever the scan could not read, or
            None to discard it - see :func:`latest_save`.

    Returns:
        Every save, newest first. Empty when the directory is absent, empty,
        or nothing resolves - never an exception for any of those.
    """
    directory = account_dir
    if directory is None:
        directory = locate.resolve_account_dir(locate.resolve_save_root())
    if directory is None:
        return ()
    listing = _save_files(directory)
    if problems is not None:
        problems.extend(listing.problems)
    ranked = sorted(listing.saves, key=lambda path: (-_mtime_ns(path), path.name))
    return tuple(ranked)


def latest_save(
    account_dir: Path | None = None, *, problems: list[ListingProblem] | None = None
) -> Path | None:
    """Return the most-recently-modified save, across manual saves and autosaves.

    The head of :func:`ranked_saves`, which owns the ordering: modification
    time descending with the FILENAME as a tiebreak, so two runs over the same
    directory return the same answer.

    THIS IS THE NEWEST FILE, NOT THE NEWEST READABLE ONE. A caller that is
    about to parse what it gets should go through ``world.load_newest_world``
    over :func:`ranked_saves`, which falls back past a save the reader refuses
    and flags it.

    Args:
        account_dir: The directory to search. Resolved from the environment,
            config/local.json and auto-detection when omitted.
        problems: A list to extend with whatever the scan could not read, or
            None to discard it. The return value is None both for a machine
            with no game and for a directory that refused to list; a caller
            that needs to tell those apart passes a list and reads the CODE,
            which differs between the two.

    Returns:
        The newest save, or None when the directory is absent, empty, or
        nothing resolves. Never raises for any of those - a machine with no
        game installed is a supported state, not an error.
    """
    ranked = ranked_saves(account_dir, problems=problems)
    return ranked[0] if ranked else None


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
        ) from _pathless_cause(exc)

    try:
        _replace_with_retry(partial, destination)
    except OSError as exc:
        _remove_quietly(partial)
        raise WorkDirError(
            f"the copy could not be renamed into place at {locate.redact(destination)}: "
            f"{type(exc).__name__}, errno {exc.errno}"
        ) from _pathless_cause(exc)

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
        ) from _pathless_cause(exc)
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


def discard_copy(copy: Path, *, work_root: Path | None = None) -> bool:
    """Delete ONE copy this module made, once its caller is done with it.

    WHY ONE COPY AND NOT A PURGE (CS-1309). A copy is kept after a load so a
    later reader of the same bytes can find it, but a copy whose save the
    reader REFUSED has no later reader: the refusal is the whole answer, and
    the dashboard's provider remembers it rather than copying again. Each
    refused save the fallback walk met used to stay in the work root for good
    - a real library left dozens of full-size copies there.

    The SAME TWO CONDITIONS AS :func:`purge_work_dir`, applied to the one path
    handed in: it sits in this module's copies directory under the work root
    AND carries this module's suffix. A path failing either - the save itself,
    a suffixed file in the save directory, a neighbour in the copies
    directory - is refused and left exactly where it is. A copies directory
    inside a forbidden root refuses too, so this can never remove anything in
    the save directory or the install. Uses the one remove call this module
    has; it adds no write surface.

    Args:
        copy: The copy, as :func:`copy_for_read` returned it.
        work_root: The work root it was made under. Defaults to
            :func:`work_root`.

    Returns:
        True when the copy was removed; False when it was refused, absent or
        would not remove - never an exception.
    """
    copies = _copies_dir(_resolve_work_root(work_root))
    try:
        _refuse_if_forbidden(copies)
    except WorkDirError:
        return False
    home = _resolved(copies)
    parent = _resolved(Path(copy).parent)
    if home is None or parent is None or parent != home:
        return False
    return _is_module_copy(Path(copy)) and _remove_quietly(Path(copy))


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
