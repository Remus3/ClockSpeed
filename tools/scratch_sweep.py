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
directory goes to the Recycle Bin, never to a direct unlink. The shell's
``IFileOperation`` deletes with recycle-on-delete and undo, and a progress sink
watches every delete: the shell marks a delete it can send to the bin with
``TSF_DELETE_RECYCLE_IF_POSSIBLE``, and a delete WITHOUT that mark - one the bin
cannot take, which the shell would otherwise make permanent and report as a
success - is aborted before it happens. The sweep then reports it and STOPS;
nothing further is handed to the shell. A delete the shell reports done with no
item left in the bin is reported the same way. No dialog is ever shown. Elsewhere
than Windows there is no Recycle Bin to reach, so ``--apply`` removes nothing.

WHEN IT RUNS - ONLY AT /done, AFTER EVERY SUB-AGENT HAS FINISHED.
``.claude/commands/done.md`` runs it at the session's end, after every log the
ritual reads has been read back. The grace period protects an agent that
CREATES or WRITES; an agent that only READS a tree changes no timestamp, so
nothing on disk can protect it. So ``--apply`` refuses - exit 2, nothing moved -
while any progress file under ``ops/loop/control/progress/`` in the main
checkout reports ``running`` and was updated within twice its ``eta_s`` (never
less than :data:`LIVE_FLOOR_S`), or cannot be read; ``--ignore-task`` names the
caller's own progress file. The default is a DRY RUN that reports what it would
do; ``--apply`` acts.

CLI (exit 0 under the bound, 1 still at or over it or stopped, 2 refused)::

    python tools/scratch_sweep.py [--apply] [--bound N] [--grace-s S] [--scratchpad DIR]
                                  [--progress-dir DIR] [--ignore-task NAME ...]

Its output is counts only: no path, no session id, no environment value.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

#: The most files a session scratchpad may hold after a sweep - MAIN's target.
BOUND_FILES: Final = 5000

#: A top-level directory created, or written anywhere inside, more recently than
#: this is another agent's live work and is never swept.
GRACE_S: Final = 1800.0

#: The variable naming this session's id; its name only is ever spelled.
ENV_SESSION: Final = "CLAUDE_CODE_SESSION_ID"

#: The harness's session tree under the temp directory, as a glob prefix:
#: ``<temp>/<harness>/<project>/``. One string, so no constant reads as a start
#: of the CLI to the FLEET item 10 census.
SESSION_TREE_GLOB: Final = "claude/*/"

#: A session id is a lowercase UUID; anything else is refused, never globbed.
SESSION_ID: Final = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

EXIT_UNDER: Final = 0
EXIT_OVER: Final = 1
EXIT_REFUSED: Final = 2

#: This file's checkout; its main checkout holds the agents' progress files.
REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: A running progress file updated within this is live whatever its ``eta_s``.
LIVE_FLOOR_S: Final = 600.0

#: The shell operation: recycle on delete, with undo, no prompt, no dialog, and
#: stop the whole operation at the first error.
OPERATION_FLAGS: Final = (
    0x0004  # FOF_SILENT
    | 0x0010  # FOF_NOCONFIRMATION
    | 0x0040  # FOF_ALLOWUNDO
    | 0x0400  # FOF_NOERRORUI
    | 0x00080000  # FOFX_RECYCLEONDELETE
    | 0x00100000  # FOFX_EARLYFAILURE
)

#: TRANSFER_SOURCE_FLAGS: set on a delete only when the item will be recycled.
TSF_DELETE_RECYCLE_IF_POSSIBLE: Final = 0x80

#: IFileOperationProgressSink's methods, in vtable order.
SINK_METHODS: Final = (
    "QueryInterface",
    "AddRef",
    "Release",
    "StartOperations",
    "FinishOperations",
    "PreRenameItem",
    "PostRenameItem",
    "PreMoveItem",
    "PostMoveItem",
    "PreCopyItem",
    "PostCopyItem",
    "PreDeleteItem",
    "PostDeleteItem",
    "PreNewItem",
    "PostNewItem",
    "UpdateProgress",
    "ResetTimer",
    "PauseTimer",
    "ResumeTimer",
)

_S_OK: Final = 0
_E_ABORT: Final = -0x7FFFBFFC  # 0x80004004 as a signed HRESULT
_E_NOINTERFACE: Final = -0x7FFFBFFE  # 0x80004002
_COINIT_APARTMENTTHREADED: Final = 0x2
_CLSCTX_ALL: Final = 0x17

#: IFileOperation's vtable slots this module calls.
_ADVISE, _UNADVISE, _SET_FLAGS = 3, 4, 5
_DELETE_ITEM, _PERFORM, _ANY_ABORTED = 18, 21, 22
_RELEASE: Final = 2

_CLSID_FILE_OPERATION: Final = "3ad05575-8857-4850-9277-11b85bdb8e09"
_IID_FILE_OPERATION: Final = "947aab5f-0a5c-4c13-b4d6-4bf7836fc9f8"
_IID_SHELL_ITEM: Final = "43826d1e-e718-42ee-bc55-a1e261c37bfe"
_IID_PROGRESS_SINK: Final = "04b0f1a7-9490-44bc-96e1-4296a31252e2"
_IID_UNKNOWN: Final = "00000000-0000-0000-c000-000000000046"


class BinRefusedError(OSError):
    """The Recycle Bin could not take a directory; the sweep stops there."""


@dataclass(frozen=True)
class ShellOutcome:
    """What the shell did with one delete."""

    refused: bool
    outside_bin: bool
    recycled: bool


def allow_delete(flags: int) -> bool:
    """Whether a delete carrying ``flags`` goes to the Recycle Bin."""
    return bool(flags & TSF_DELETE_RECYCLE_IF_POSSIBLE)


@dataclass(frozen=True)
class SweepResult:
    """What one sweep found and did - or, in a dry run, would do."""

    before: int
    after: int
    recycled: int
    failed: int
    bound: int
    stopped: bool = False

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
    found = [
        path
        for path in temp.glob(SESSION_TREE_GLOB + session + "/scratchpad")
        if path.is_dir() and not path.is_symlink() and not path.is_junction()
    ]
    return found[0] if len(found) == 1 else None


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _GUID(ctypes.Structure):
        _fields_ = (
            ("data1", ctypes.c_ulong),
            ("data2", ctypes.c_ushort),
            ("data3", ctypes.c_ushort),
            ("data4", ctypes.c_ubyte * 8),
        )

    def _guid(text: str) -> _GUID:
        """A COM GUID from its string form, by the standard field layout."""
        value = uuid.UUID(text)
        guid = _GUID(value.fields[0], value.fields[1], value.fields[2])
        guid.data4[:] = list(value.bytes[8:])
        return guid

    _HR = ctypes.c_long
    _VOID = ctypes.c_void_p
    _DWORD = wintypes.DWORD

    #: Each sink method's arguments after ``this``, in :data:`SINK_METHODS` order.
    _SINK_ARGS: Final[tuple[tuple[Any, ...], ...]] = (
        (),  # StartOperations
        (_HR,),  # FinishOperations
        (_DWORD, _VOID, _VOID),  # PreRenameItem
        (_DWORD, _VOID, _VOID, _HR, _VOID),  # PostRenameItem
        (_DWORD, _VOID, _VOID, _VOID),  # PreMoveItem
        (_DWORD, _VOID, _VOID, _VOID, _HR, _VOID),  # PostMoveItem
        (_DWORD, _VOID, _VOID, _VOID),  # PreCopyItem
        (_DWORD, _VOID, _VOID, _VOID, _HR, _VOID),  # PostCopyItem
        (_DWORD, _VOID),  # PreDeleteItem
        (_DWORD, _VOID, _HR, _VOID),  # PostDeleteItem
        (_DWORD, _VOID, _VOID),  # PreNewItem
        (_DWORD, _VOID, _VOID, _VOID, _DWORD, _HR, _VOID),  # PostNewItem
        (ctypes.c_uint, ctypes.c_uint),  # UpdateProgress
        (),  # ResetTimer
        (),  # PauseTimer
        (),  # ResumeTimer
    )

    def _ok(*_args: object) -> int:
        """Every sink method this module does not watch: carry on."""
        return _S_OK

    class ProgressSink:
        """An ``IFileOperationProgressSink`` that stops every delete the bin cannot take.

        ``pointer`` is the COM interface pointer handed to ``Advise``. The object
        lives as long as this Python object; its reference count is nominal.
        """

        def __init__(self) -> None:
            """Build the vtable and the object the shell calls through."""
            self.refused = False
            self.outside_bin = False
            self.recycled = False
            proto = ctypes.WINFUNCTYPE
            query = proto(_HR, _VOID, ctypes.POINTER(_GUID), ctypes.POINTER(_VOID))(self._query)
            count = proto(ctypes.c_ulong, _VOID)(lambda _this: 1)
            self._callbacks: list[Any] = [query, count, count]
            handlers: dict[str, Callable[..., int]] = {
                "PreDeleteItem": self._pre_delete,
                "PostDeleteItem": self._post_delete,
            }
            for name, args in zip(SINK_METHODS[3:], _SINK_ARGS, strict=True):
                handler: Callable[..., int] = handlers.get(name, _ok)
                self._callbacks.append(proto(_HR, _VOID, *args)(handler))
            slots = [ctypes.cast(callback, _VOID).value for callback in self._callbacks]
            self._vtable = (_VOID * len(slots))(*slots)
            self._object = (_VOID * 1)(ctypes.addressof(self._vtable))
            self.pointer = _VOID(ctypes.addressof(self._object))
            self._accepted = (bytes(_guid(_IID_UNKNOWN)), bytes(_guid(_IID_PROGRESS_SINK)))

        def _query(self, this: int, riid: object, ppv: object) -> int:
            wanted = bytes(riid.contents)  # type: ignore[attr-defined]
            if wanted in self._accepted:
                ppv[0] = this  # type: ignore[index]
                return _S_OK
            ppv[0] = None  # type: ignore[index]
            return _E_NOINTERFACE

        def _pre_delete(self, _this: int, flags: int, _item: int) -> int:
            if allow_delete(flags):
                return _S_OK
            self.refused = True
            return _E_ABORT

        def _post_delete(self, _this: int, _flags: int, _item: int, hr: int, new: int) -> int:
            if hr >= 0:
                if new:
                    self.recycled = True
                else:
                    self.outside_bin = True
            return _S_OK

    def _slot(
        interface: ctypes.c_void_p, index: int, *args: Any, restype: Any = _HR
    ) -> Callable[..., int]:
        """Method ``index`` of the COM interface ``interface``, as a callable."""
        table = ctypes.cast(interface, ctypes.POINTER(ctypes.POINTER(_VOID))).contents
        method: Callable[..., int] = ctypes.WINFUNCTYPE(restype, _VOID, *args)(table[index])
        return method

    class _StepFailedError(OSError):
        """One shell step failed; the delete as a whole did not happen."""

    def _require(status: int, made: ctypes.c_void_p | None = None) -> None:
        """Raise :class:`_StepFailedError` on a failed HRESULT or a null result."""
        if status < 0 or (made is not None and not made.value):
            raise _StepFailedError

    def _file_operation_delete(path: Path) -> ShellOutcome:
        """Delete ``path`` through ``IFileOperation`` to the bin, in this STA thread."""
        failed = ShellOutcome(refused=False, outside_bin=False, recycled=False)
        ole32 = ctypes.windll.ole32
        init = ctypes.WINFUNCTYPE(_HR, _VOID, _DWORD)(("CoInitializeEx", ole32))
        uninit = ctypes.WINFUNCTYPE(None)(("CoUninitialize", ole32))
        create = ctypes.WINFUNCTYPE(
            _HR, ctypes.POINTER(_GUID), _VOID, _DWORD, ctypes.POINTER(_GUID), ctypes.POINTER(_VOID)
        )(("CoCreateInstance", ole32))
        parse = ctypes.WINFUNCTYPE(
            _HR, ctypes.c_wchar_p, _VOID, ctypes.POINTER(_GUID), ctypes.POINTER(_VOID)
        )(("SHCreateItemFromParsingName", ctypes.windll.shell32))
        if init(None, _COINIT_APARTMENTTHREADED) < 0:
            return failed
        sink = ProgressSink()
        operation = _VOID()
        item = _VOID()
        clsid = _guid(_CLSID_FILE_OPERATION)
        iid_op = _guid(_IID_FILE_OPERATION)
        iid_item = _guid(_IID_SHELL_ITEM)
        aborted = wintypes.BOOL(1)
        performed = -1
        try:
            made = create(
                ctypes.byref(clsid),
                None,
                _CLSCTX_ALL,
                ctypes.byref(iid_op),
                ctypes.byref(operation),
            )
            _require(made, operation)
            spelled = str(path.absolute())
            _require(parse(spelled, None, ctypes.byref(iid_item), ctypes.byref(item)), item)
            _require(_slot(operation, _SET_FLAGS, _DWORD)(operation, OPERATION_FLAGS))
            cookie = _DWORD()
            advise = _slot(operation, _ADVISE, _VOID, ctypes.POINTER(_DWORD))
            _require(advise(operation, sink.pointer, ctypes.byref(cookie)))
            try:
                _require(_slot(operation, _DELETE_ITEM, _VOID, _VOID)(operation, item, None))
                performed = _slot(operation, _PERFORM)(operation)
                any_aborted = _slot(operation, _ANY_ABORTED, ctypes.POINTER(wintypes.BOOL))
                any_aborted(operation, ctypes.byref(aborted))
            finally:
                _slot(operation, _UNADVISE, _DWORD)(operation, cookie)
        except _StepFailedError:
            return failed
        finally:
            for interface in (item, operation):
                if interface.value:
                    _slot(interface, _RELEASE, restype=ctypes.c_ulong)(interface)
            uninit()
        clean = performed >= 0 and not aborted.value and sink.recycled
        return ShellOutcome(refused=sink.refused, outside_bin=sink.outside_bin, recycled=clean)


def _shell_recycle(path: Path) -> ShellOutcome:
    """Run the shell delete on a thread of its own, which owns its COM apartment."""
    found: list[ShellOutcome] = []
    if sys.platform == "win32":
        worker = threading.Thread(target=lambda: found.append(_file_operation_delete(path)))
        worker.start()
        worker.join()
    return found[0] if found else ShellOutcome(refused=False, outside_bin=False, recycled=False)


def recycle(path: Path, deleter: Callable[[Path], ShellOutcome] | None = None) -> None:
    """Send ``path`` to the Recycle Bin (FLEET item 9); raise when it did not go there.

    Raises:
        BinRefusedError: The bin could not take ``path`` - the delete was stopped, so
            ``path`` stays - or the shell reported a delete that left nothing in
            the bin.
        OSError: Any other failure; ``path`` was not recycled. Elsewhere than
            Windows this is every call: no Recycle Bin is reachable.
    """
    if deleter is None:
        if sys.platform != "win32":
            raise OSError("no Recycle Bin is reachable on this platform")
        deleter = _shell_recycle
    outcome = deleter(path)
    if outcome.refused:
        raise BinRefusedError("the Recycle Bin cannot take it; the delete was stopped")
    if outcome.outside_bin:
        raise BinRefusedError("the shell reported a delete that left nothing in the Recycle Bin")
    if not outcome.recycled:
        raise OSError("the shell did not recycle it")


def _main_checkout(path: Path) -> Path:
    """The main working tree for ``path``, even when ``path`` is a linked worktree.

    File-only, as the fleet kit's own helper reads it: a linked worktree's
    ``.git`` is a file naming ``<main>/.git/worktrees/<name>``.
    """
    dotgit = path / ".git"
    try:
        raw = dotgit.read_text(encoding="utf-8").strip() if dotgit.is_file() else ""
    except (OSError, UnicodeError):
        raw = ""
    if raw.startswith("gitdir:"):
        gitdir = Path(raw.split(":", 1)[1].strip())
        gitdir = (gitdir if gitdir.is_absolute() else path / gitdir).resolve()
        if gitdir.parent.name == "worktrees":
            return gitdir.parents[2]
    return path


def live_progress(progress_dir: Path, now: float, ignore: Collection[str] = ()) -> int:
    """How many progress files may belong to a live agent.

    Live is ``running`` and updated within twice its ``eta_s``, never less than
    :data:`LIVE_FLOOR_S`; a file that cannot be read or parsed counts too,
    because it cannot prove its agent finished. A file whose name is in
    ``ignore`` - the caller's own - is skipped. A missing directory has none.
    """
    try:
        paths = sorted(progress_dir.glob("*.json"))
    except OSError:
        return 0
    live = 0
    for path in paths:
        if path.stem in ignore:
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            live += 1
            continue
        if not isinstance(doc, dict) or doc.get("status") != "running":
            continue
        try:
            updated = datetime.datetime.fromisoformat(str(doc.get("updated"))).timestamp()
            eta = float(doc.get("eta_s") or 0)
        except (TypeError, ValueError, OverflowError, OSError):
            live += 1
            continue
        if now - updated <= max(2 * eta, LIVE_FLOOR_S):
            live += 1
    return live


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
    stopped = False
    for entry in old:
        if projected < bound:
            break
        if apply:
            try:
                remove(entry.path)
            except BinRefusedError:
                failed += 1
                stopped = True
                break
            except OSError:
                failed += 1
                continue
        recycled += 1
        projected -= entry.files
    after = count_files(scratchpad) if apply else projected
    return SweepResult(
        before=before, after=after, recycled=recycled, failed=failed, bound=bound, stopped=stopped
    )


def main(argv: Sequence[str] | None = None, remove: Callable[[Path], None] | None = None) -> int:
    """Run the CLI; return 0 under the bound, 1 still at or over it, 2 refused."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="act; the default is a dry run")
    parser.add_argument("--bound", type=int, default=BOUND_FILES)
    parser.add_argument("--grace-s", type=float, default=GRACE_S)
    parser.add_argument("--scratchpad", type=Path, default=None)
    parser.add_argument("--progress-dir", type=Path, default=None)
    parser.add_argument("--ignore-task", action="append", default=[])
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
    progress = args.progress_dir
    if progress is None:
        progress = _main_checkout(REPO_ROOT) / "ops" / "loop" / "control" / "progress"
    live = live_progress(progress, time.time(), frozenset(args.ignore_task))
    if live and args.apply:
        print(
            f"scratch_sweep: REFUSED - {live} progress file(s) may be a live agent; nothing moved"
        )
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
        f" bound {result.bound}, {live} live agent progress file(s)"
        + (", STOPPED: the Recycle Bin could not take a directory" if result.stopped else "")
    )
    return EXIT_OVER if result.over_bound or result.stopped else EXIT_UNDER


if __name__ == "__main__":
    sys.exit(main())
