"""CS-1344 - bound THIS session's Claude scratchpad, by the Recycle Bin, never wider.

WHY THIS EXISTS. MAIN's FIX of 2026-10-21 measured one Claude session scratchpad
at about 66.1k files; the temp directory's entry count costs boot time on this
machine, and the target is under 5k files per session scratchpad. The bulk is
whole-tree copies that agents extract to read a frozen candidate - hundreds of
files each, one per adversary or adjudicator - and nothing removed them.

WHAT IT DOES. It resolves exactly ONE directory - this session's scratchpad,
``<temp>/claude/<project>/<session id>/scratchpad``, the session id read from
:data:`ENV_SESSION` - or the one ``--scratchpad`` names, and counts the files in
it. While the count is at or over the bound it sends the LARGEST top-level
directories to the Recycle Bin, one at a time, and stops as soon as the count
is under the bound, so the fewest entries go.

WHAT IT NEVER TOUCHES, because other agents of the same session may still be
reading what they extracted, and a sweep wider than its own scratchpad is a
defect of its own:

  - a loose file at the top level - logs, scripts, notes - which is small and
    is often the only record of a step;
  - a link or a junction, at any depth: never followed, never counted, never
    removed;
  - a directory created, or written anywhere inside, within :data:`GRACE_S`;
  - anything outside the one resolved scratchpad. It never globs a shared
    parent, and a scratchpad that is itself a link is refused.

HOW IT DELETES (FLEET item 9). Scratch may hold something irreplaceable, so a
directory goes to the Recycle Bin, never to a direct unlink; a move the Recycle
Bin refuses is reported and the directory stays. Elsewhere than Windows there is
no Recycle Bin to reach, so ``--apply`` removes nothing there.

WHEN IT RUNS. ``.claude/commands/done.md`` runs it at the session's end, after
every log the ritual reads has been read back. The default is a DRY RUN that
reports what it would do; ``--apply`` acts.

CLI (exit 0 under the bound, 1 still at or over it, 2 refused)::

    python tools/scratch_sweep.py [--apply] [--bound N] [--grace-s S] [--scratchpad DIR]

Its output is counts only: no path, no session id, no environment value.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: The most files a session scratchpad may hold after a sweep - MAIN's target.
BOUND_FILES: Final = 5000

#: A top-level directory created, or written anywhere inside, more recently than
#: this is another agent's live work and is never swept.
GRACE_S: Final = 1800.0

#: The variable naming this session's id; its name only is ever spelled.
ENV_SESSION: Final = "CLAUDE_CODE_SESSION_ID"

#: A session id is a lowercase UUID; anything else is refused, never globbed.
SESSION_ID: Final = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

EXIT_UNDER: Final = 0
EXIT_OVER: Final = 1
EXIT_REFUSED: Final = 2

#: SHFileOperationW: delete, to the Recycle Bin, with no prompt and no dialog.
_FO_DELETE: Final = 3
_FOF_SILENT: Final = 0x0004
_FOF_NOCONFIRMATION: Final = 0x0010
_FOF_ALLOWUNDO: Final = 0x0040
_FOF_NOERRORUI: Final = 0x0400


@dataclass(frozen=True)
class SweepResult:
    """What one sweep found and did - or, in a dry run, would do."""

    before: int
    after: int
    recycled: int
    failed: int
    bound: int

    @property
    def over_bound(self) -> bool:
        """Whether the scratchpad still holds the bound or more."""
        return self.after >= self.bound


@dataclass(frozen=True)
class _Entry:
    """One top-level directory: its path, its file count and its newest time."""

    path: Path
    files: int
    newest: float


def _is_link(entry: os.DirEntry[str]) -> bool:
    """A symlink or a junction - never followed, counted or removed."""
    return entry.is_symlink() or entry.is_junction()


def _times(entry: os.DirEntry[str]) -> float:
    """The newest of an entry's creation and modification times, unfollowed."""
    info = entry.stat(follow_symlinks=False)
    born = getattr(info, "st_birthtime", info.st_ctime)
    return max(float(born), info.st_mtime)


def _walk(path: Path) -> tuple[int, float]:
    """Files under ``path`` and the newest time of anything there, links unfollowed."""
    files = 0
    newest = 0.0
    stack = [path]
    while stack:
        try:
            entries = list(os.scandir(stack.pop()))
        except OSError:
            continue
        for entry in entries:
            try:
                if _is_link(entry):
                    continue
                newest = max(newest, _times(entry))
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                else:
                    files += 1
            except OSError:
                continue
    return files, newest


def count_files(path: Path) -> int:
    """How many files are under ``path``; a link or a junction is never followed."""
    return _walk(path)[0]


def _top_level(scratchpad: Path) -> tuple[list[_Entry], int]:
    """The scratchpad's real top-level directories, and its loose file count."""
    directories: list[_Entry] = []
    loose = 0
    try:
        entries = list(os.scandir(scratchpad))
    except OSError:
        return directories, loose
    for entry in entries:
        try:
            if _is_link(entry):
                continue
            if not entry.is_dir(follow_symlinks=False):
                loose += 1
                continue
            files, newest = _walk(Path(entry.path))
            directories.append(_Entry(Path(entry.path), files, max(newest, _times(entry))))
        except OSError:
            continue
    return directories, loose


def resolve_scratchpad(env: Mapping[str, str], temp: Path) -> Path | None:
    """This session's scratchpad under ``temp``, or None when it is not exactly one.

    Args:
        env: The environment to read :data:`ENV_SESSION` from.
        temp: The system temp directory the harness keeps its session tree in.

    Returns:
        The one real directory ``<temp>/claude/<project>/<id>/scratchpad``; None
        when the id is unset or not a session id, or when none or several match.
    """
    session = env.get(ENV_SESSION, "")
    if not SESSION_ID.fullmatch(session):
        return None
    base = temp / "claude"
    found = [
        path
        for path in base.glob("*/" + session + "/scratchpad")
        if path.is_dir() and not path.is_symlink() and not path.is_junction()
    ]
    return found[0] if len(found) == 1 else None


def recycle(path: Path) -> None:
    """Send ``path`` to the Recycle Bin (FLEET item 9); raise OSError when refused.

    Windows only, through ``SHFileOperationW`` with undo allowed, so nothing is
    spawned and nothing is unlinked directly. Elsewhere it refuses.
    """
    if sys.platform != "win32":
        raise OSError("no Recycle Bin is reachable on this platform")
    import ctypes  # noqa: PLC0415 - Windows only
    from ctypes import wintypes  # noqa: PLC0415 - Windows only

    class _FileOp(ctypes.Structure):
        _fields_ = (
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", ctypes.c_void_p),
            ("pTo", ctypes.c_void_p),
            ("fFlags", ctypes.c_ushort),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", ctypes.c_void_p),
        )

    # Double-NUL terminated: the buffer adds one NUL after the one spelled here.
    source = ctypes.create_unicode_buffer(str(path.absolute()) + "\0")
    operation = _FileOp()
    operation.wFunc = _FO_DELETE
    operation.pFrom = ctypes.cast(source, ctypes.c_void_p).value
    operation.fFlags = _FOF_ALLOWUNDO | _FOF_NOCONFIRMATION | _FOF_SILENT | _FOF_NOERRORUI
    status = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
    if status != 0 or operation.fAnyOperationsAborted:
        raise OSError("the Recycle Bin refused the move")


def sweep(
    scratchpad: Path,
    *,
    apply: bool,
    remove: Callable[[Path], None] = recycle,
    bound: int = BOUND_FILES,
    grace_s: float = GRACE_S,
    now: float | None = None,
) -> SweepResult:
    """Bring ``scratchpad`` under ``bound`` files by its largest old directories.

    Args:
        scratchpad: The one directory to bound; nothing outside it is touched.
        apply: False for a dry run - ``remove`` is never called.
        remove: Sends one top-level directory away; :func:`recycle` by default.
        bound: The file count to get under.
        grace_s: A directory created or written within this is never swept.
        now: The clock to age against; the wall clock when omitted.

    Returns:
        The counts. ``after`` is re-measured after an applied sweep and projected
        in a dry run.
    """
    clock = time.time() if now is None else now
    directories, loose = _top_level(scratchpad)
    before = loose + sum(entry.files for entry in directories)
    old = [entry for entry in directories if clock - entry.newest > grace_s]
    old.sort(key=lambda entry: (-entry.files, entry.path.name))
    projected = before
    recycled = failed = 0
    for entry in old:
        if projected < bound:
            break
        if apply:
            try:
                remove(entry.path)
            except OSError:
                failed += 1
                continue
        recycled += 1
        projected -= entry.files
    after = count_files(scratchpad) if apply else projected
    return SweepResult(before=before, after=after, recycled=recycled, failed=failed, bound=bound)


def main(argv: Sequence[str] | None = None, remove: Callable[[Path], None] | None = None) -> int:
    """Run the CLI; return 0 under the bound, 1 still at or over it, 2 refused."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="act; the default is a dry run")
    parser.add_argument("--bound", type=int, default=BOUND_FILES)
    parser.add_argument("--grace-s", type=float, default=GRACE_S)
    parser.add_argument("--scratchpad", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.scratchpad is None:
        scratchpad = resolve_scratchpad(os.environ, Path(tempfile.gettempdir()))
    else:
        scratchpad = args.scratchpad
        if scratchpad.is_symlink() or scratchpad.is_junction() or not scratchpad.is_dir():
            scratchpad = None
    if scratchpad is None:
        print("scratch_sweep: REFUSED - no single real scratchpad resolved")
        return EXIT_REFUSED
    result = sweep(
        scratchpad,
        apply=args.apply,
        remove=recycle if remove is None else remove,
        bound=args.bound,
        grace_s=args.grace_s,
    )
    mode = "applied" if args.apply else "dry run"
    print(
        f"scratch_sweep: {mode} - {result.before} files before, {result.after} after,"
        f" {result.recycled} director(ies) to the Recycle Bin, {result.failed} refused,"
        f" bound {result.bound}"
    )
    return EXIT_OVER if result.over_bound else EXIT_UNDER


if __name__ == "__main__":
    sys.exit(main())
