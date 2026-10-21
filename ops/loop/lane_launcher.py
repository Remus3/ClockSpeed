#!/usr/bin/env python
r"""Lane launcher - turn a held lane lock into a running headless worker.

``ops/loop/lanes.py`` decides WHO may run; this module is what actually runs.
The split is deliberate: the lock is pure state management and must stay
gradeable without spawning anything, so nothing in lanes.py starts a process and
nothing here decides eligibility.

WORKTREE-MANDATORY, ENFORCED TWICE. A lane may fire while an interactive session
is live, but it may only ever run against a git worktree - never the main tree.
``try_acquire_lane`` already refuses a worktree that resolves to the repository
root; this module refuses it AGAIN at spawn time, because the two checks happen
at different moments and a path can be handed in between them. Two writers in
one working directory is the concurrent-index corruption class, and it is not
recoverable by retrying.

THE PID IN THE LOCK IS THE WORKER'S, AND THE CLAIMER IS ITS HOLDER. A driver
claims the lane from a process that outlives every worker it starts.
``launch_lane`` re-points the lock through ``lanes.repoint_lane_pid`` as soon as
it has a real pid, which keeps the claiming driver as ``holder_pid`` - the kit's
``keep_claimer`` (CS-1274 r2) - so the lane stays held while the driver finishes
the cycle and is free once the driver releases it, or once worker and driver
are both gone. The launch RELEASES the lane if anything in the spawn path fails
- a lock with no process behind it is strictly worse than no lock at all - and
KILLS a worker it started but could not get the lock to name, interrupts
included: a worker no lock names is invisible to every reader.

DETACHED_PROCESS (0x8) IS BANNED, AND THAT IS A MEASUREMENT RATHER THAN A STYLE
CALL. Three spawns of one script differing only in creation flags:

    CREATE_NO_WINDOW | DETACHED_PROCESS -> pid issued, rc 0, log NEVER written
    CREATE_NO_WINDOW                    -> pid issued, rc 0, log written
    DETACHED_PROCESS                    -> pid issued, rc 0, log NEVER written

powershell.exe cannot initialise its host without a console, so it exits
immediately and SILENTLY - a success exit code, a real pid, and no work done.
The lane would flip RUNNING then RECLAIMABLE on schedule having produced
nothing, which is the worst shape a failure can take here. CREATE_NO_WINDOW
alone already suppresses the console flash, and the child outlives this process
anyway because nothing waits on it past the liveness grace below.

THE LIVENESS GRACE IS THIS PORT'S ONE DELIBERATE DIVERGENCE from the runner it
was ported from, and it is what turns that measurement into something the
launcher can SEE. A spawn is followed by a short bounded wait: still running is
the healthy outcome, and an exit inside the window is reported as a failed
launch instead of a tracked worker that was never there. It bounds the child the
way every other spawn in this repository is bounded, and it is honest about its
reach - it catches the immediate-exit class only. A worker that dies a minute
later is caught by the pid probe in ``lanes.lane_state``, which is what that
probe is for.

THE CLAIM NAMES THE WORKTREE, AND THE KIT PREPARES IT - CS-1274. The worker runs
in the tree the lane CLAIM records, read back off the lock, never in one this
module derives a second time: the lock is what ``ops/loop/claims.py`` and the
kit's lane widget read, so a launcher that chose its own directory would run a
worker somewhere every reader thinks it is not. A claim that asked for the
kit's per-index tree (``<parent>/cs-worktrees/lane-<i>``, derived from the main
tree by ``fleet_lanes.worktree_path``) is handed to the KIT'S
``ensure_worktree``, unedited and called: it adds a missing tree DETACHED at
``LANE_BASE``, refuses a dirty one rather than cleaning it, and saves unmerged
commits under ``refs/fleet-lanes/`` before it moves a clean one. A tree a
caller named instead is the caller's - run in as it stands, never created or
moved here. No worktree base is written anywhere in this file.
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent

# tools/ carries no __init__.py, so `toolpath` is imported under its BARE name:
# importing it as `tools.toolpath` makes mypy resolve one file under two module
# names and refuse the run outright. This is the same six lines
# scripts/make_cert.py, scripts/make_shortcut.py and scripts/verify_env.py each
# carry, and the same reason.
_TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402


def _load_route() -> Any:
    """Bind ops/loop/headless_route.py - package route first, file path as fallback.

    CS-1225. The route module holds NO process-global state, so the CS-1000
    two-copies hazard ``_load_lanes`` guards against cannot arise here: a second
    copy loaded by path behaves identically. The fallback exists for the same
    detached caller ``_load_lanes`` names, which has no ``ops`` package to import.
    """
    try:
        return importlib.import_module("ops.loop.headless_route")
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "cs_loop_headless_route", _HERE / "headless_route.py"
        )
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


#: CS-1225 - every headless spawn is routed through the local proxy, or refused.
headless_route = _load_route()

#: The ONE name ops/loop/lanes.py is bound under anywhere in this project.
#: lanes.py carries process-global state - ``_OWNED``, the ABA guard that
#: decides whether a release is ours. A file-path bind under a private name
#: creates a SECOND module object with its OWN table, so a re-point recorded in
#: one copy is invisible to a release called on the other and the lane can never
#: be released. That is measured rather than predicted: the first cut of the
#: upstream this was ported from did exactly that, and two launcher arms failed
#: on it.
_LANES_MODULE_NAME = "clockspeed_loop_lanes"

#: The CANONICAL name for the same file. A module loaded by path is published
#: under this name as well, so a sibling that reaches lanes.py through the
#: ordinary package route gets the object that is already loaded rather than
#: building a second one. See ``_load_lanes`` - this is the whole of CS-1000.
_LANES_DOTTED_NAME = "ops.loop.lanes"


def _load_lanes() -> Any:
    """Bind the SAME lanes module everything else uses - never a second copy.

    THE PACKAGE IMPORT IS TRIED FIRST, and that ordering is the whole fix.
    Preferring an already-loaded PRIVATE name was not enough: the driver reaches
    lanes.py as ``ops.loop.lanes`` - the ordinary package route, now that
    ``ops/`` carries ``__init__.py`` - so on a real cycle this module built a
    SECOND object under the private name and the two never met. MEASURED on the
    first real cycle: ``repoint_lane_pid`` recorded ownership in this copy,
    ``release_lane`` checked the driver's, refused, and the lock was still on
    disk when the cycle ended.

    The docstring above this one predicted that exact failure, and it happened
    anyway, because this module and its test agreed with each other - both
    loaded lanes by file path - while nothing asked the DRIVER. Two agreeing
    parties are not evidence when both rest on the same assumption.

    The private file-path bind stays as the FALLBACK, for a caller with no
    package on ``sys.path``: the detached launcher can run this file by
    absolute path, and that route has no ``ops`` package to import.

    AND THE FALLBACK PUBLISHES WHAT IT LOADED UNDER THE DOTTED NAME - CS-1000,
    and the second time this exact defect shipped. The prediction above was that
    preferring the private name would keep one object; what it actually keeps is
    one object PER PRIVATE NAME, and ``queue_loop.py`` falls back under a
    different one. On every detached run the package route fails for BOTH files
    - the driver is started as ``pythonw <repo>/ops/loop/queue_loop.py``, which
    puts ``ops/loop`` on ``sys.path`` and the repository root nowhere - so each
    loaded its own copy of ``lanes.py`` and the two ``_OWNED`` maps never met.
    MEASURED across two nights: cycle 1's re-point landed in this module's copy,
    its release was refused by the driver's, and from cycle 2 on this module
    refused to re-point, KILLED the freshly spawned worker and the lane produced
    exactly one row per launch - eleven wasted cycles the first night.

    Registering under the dotted name fixes it for any sibling, whatever private
    name that sibling chose, because ``import_module`` consults ``sys.modules``
    before it looks for a loader. ``setdefault``, never an assignment: a genuine
    package module already loaded is the canonical one and is never displaced.

    Returns:
        The lanes module.

    Raises:
        ImportError: lanes.py could not be turned into a module.
    """
    try:
        return importlib.import_module(_LANES_DOTTED_NAME)
    except ImportError:
        pass
    existing = sys.modules.get(_LANES_MODULE_NAME)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(_LANES_MODULE_NAME, _HERE / "lanes.py")
    if spec is None or spec.loader is None:
        message = "could not load ops/loop/lanes.py"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_LANES_MODULE_NAME] = module
    spec.loader.exec_module(module)
    # AFTER a successful exec, so a half-executed module is never published
    # under the name every other importer will now trust.
    sys.modules.setdefault(_LANES_DOTTED_NAME, module)
    return module


lanes = _load_lanes()

#: One answer for the main tree, taken from the module that owns the question.
REPO_ROOT = lanes.REPO_ROOT
RUNNER = _HERE / "run_lane.ps1"
LOG_DIR = _HERE / "reports"

#: CS-1274 - THE COMMIT A KIT LANE WORKTREE IS PREPARED AT, resolved in the main
#: tree. ``origin/main`` and not the main tree's ``HEAD``: the operator's own
#: checkout may carry commits it has not published, and a lane built on them
#: would push them to ``main`` as part of its own push. The worker fetches first
#: anyway (``tools/headless-queue.md`` section 4b), so a stale remote-tracking
#: ref costs a fast-forward, never a wrong base.
LANE_BASE = "origin/main"

#: Lane -> the command doc fed to the worker as its prompt. TRACKED paths only
#: (tools/*.md), never a gitignored command mirror: a worktree is a fresh
#: checkout and does not carry gitignored files, so a lane pointed at a mirror
#: would start with an empty prompt. It is the same trap as a fresh clone whose
#: git hooks are not wired yet - the file that makes it work is exactly the file
#: a new checkout does not have.
LANE_COMMANDS = {"queue": "tools/headless-queue.md"}

#: CREATE_NO_WINDOW, and nothing else. See the DETACHED_PROCESS measurement in
#: the module docstring - this is the whole of the creation-flag policy, and
#: ``tests/test_lane_launcher.py`` walks this module's syntax tree to assert
#: that no other expression ever reaches a ``creationflags=``.
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

#: How long a freshly spawned runner has to prove it survived its own start.
#: Sized for the immediate-exit class rather than for a slow worker: the failure
#: it exists to catch happens before the process has done anything at all.
_SPAWN_LIVENESS_GRACE_S = 2.0

#: CS-1017. The clock the liveness wait is MEASURED on - monotonic, because the
#: number is a duration and a wall-clock step inside the grace would falsify it.
#: A module attribute so an arm can substitute it without starting a process.
_monotonic = time.monotonic

#: CS-1017. Where ``_spawn`` leaves the seconds its liveness wait consumed on a
#: runner that SURVIVED the grace, so ``launch_lane`` can carry the number past
#: a refused re-point. An attribute on the handle rather than a second return
#: value, because ``spawn`` is an injection seam whose one-value shape every
#: caller and fake already honours.
_WAITED_ATTR = "cs_liveness_waited_s"

_GIT_TIMEOUT_S = 120
_KILL_TIMEOUT_S = 20

#: What a run id may contribute to a filename. A run id reaches the filesystem,
#: so it is filtered rather than trusted.
_SAFE_RUN_ID = "-_"
_SAFE_RUN_ID_LENGTH = 32


#: WHY A LAUNCH WAS REFUSED, as a closed vocabulary - one code per raise site
#: below, and one default for a site that names none. Drawn from ``[a-z_]+``
#: ONLY, which is the point rather than a style call: that character class
#: cannot express a drive letter, a separator, a space or a digit, so a code is
#: path-free BY CONSTRUCTION and can never carry a worktree path, an account id
#: or a world name into a row an operator reads (CLAUDE.md non-negotiable 12).
#:
#: A message is NOT a substitute. Three of the messages raised here embed a
#: path, so the driver that records a refusal cannot write any of them - it
#: writes the type name alone today, which says a launch failed and nothing
#: about why. The code is the part that is safe to copy out.
#:
#: THE DRIVER KEEPS ITS OWN COPY of this tuple and writes nothing that is not a
#: member of it. That is what makes a launcher running ahead of its driver
#: degrade to today's bare type name rather than leaking a word this module
#: chose after the driver was written.
REASON_LANE_NOT_WIRED = "lane_not_wired"
REASON_COMMAND_DOC_MISSING = "command_doc_missing"
REASON_GIT_NOT_FOUND = "git_not_found"
REASON_MAIN_TREE_REFUSED = "main_tree_refused"
#: CS-1274. The lock behind the token could not be read, so there is no
#: recorded worktree to run the worker in - and no other source for one.
REASON_CLAIM_UNREADABLE = "claim_unreadable"
#: CS-1274. The kit's ``ensure_worktree`` refused the lane's own worktree:
#: dirty (a crashed run's work, resolved by hand and never cleaned here), not a
#: linked worktree of this repository, or its base would not resolve.
REASON_WORKTREE_REFUSED = "worktree_refused"
#: CS-1274. A tree the claim NAMED, rather than the kit's derived one, is not a
#: checkout - and this module creates only the kit's layout.
REASON_WORKTREE_MISSING = "worktree_missing"
REASON_RUNNER_MISSING = "runner_missing"
REASON_SHELL_NOT_FOUND = "shell_not_found"
REASON_SPAWN_FAILED = "spawn_failed"
REASON_RUNNER_EXITED_EARLY = "runner_exited_early"
REASON_SPAWN_NO_PID = "spawn_no_pid"
REASON_REPOINT_REFUSED = "repoint_refused"
REASON_UNEXPECTED_FAULT = "unexpected_fault"

#: The default when a raise site names none. A DEFINED word rather than a blank
#: or ``None``: a reader validates the code against this tuple before recording
#: it, so a blank would be discarded and the row would say nothing at all,
#: while ``unspecified`` records "the launcher refused and did not say why".
REASON_UNSPECIFIED = "unspecified"

#: The closed set. ``tests/test_lane_launcher.py`` walks this module's syntax
#: tree and asserts every raise site names a distinct member, so a new site
#: that forgets one reddens the suite before it can reach main.
LAUNCH_REASONS = (
    REASON_LANE_NOT_WIRED,
    REASON_COMMAND_DOC_MISSING,
    REASON_GIT_NOT_FOUND,
    REASON_MAIN_TREE_REFUSED,
    REASON_CLAIM_UNREADABLE,
    REASON_WORKTREE_REFUSED,
    REASON_WORKTREE_MISSING,
    REASON_RUNNER_MISSING,
    REASON_SHELL_NOT_FOUND,
    REASON_SPAWN_FAILED,
    REASON_RUNNER_EXITED_EARLY,
    REASON_SPAWN_NO_PID,
    REASON_REPOINT_REFUSED,
    REASON_UNEXPECTED_FAULT,
    REASON_UNSPECIFIED,
)


#: Every word ``note_worker_abort`` will write. THE LAUNCH VOCABULARY AND
#: NOTHING ELSE, stated as its own name so a future caller reads what the note
#: accepts rather than inferring it. The driver's own kill - a timeout forty
#: minutes into a healthy cycle - is a SIBLING of this defect and is NOT wired
#: here: widening ``LAUNCH_REASONS`` for it would break the AST arm that binds
#: that tuple one-to-one to this module's raise sites and the equality arm
#: ``queue_loop.py`` holds against its copy, and a driver kill leaves a large
#: log plus a ``timeout`` row, not the 134-byte silence this closes.
ABORT_REASONS = LAUNCH_REASONS

#: How a terminal line written by the KILLER opens. Distinct from the runner's
#: own ``lane exit`` on purpose: a reader must be able to tell a worker that
#: finished from one that was terminated where it stood.
ABORT_PREFIX = "lane abort"


def note_worker_abort(log: Any, reason: Any) -> None:
    """Write the last line a killed worker could not write for itself.

    ``taskkill /F`` is TerminateProcess. No ``finally`` unwinds, no handler
    runs, and the runner's own exit line is never reached - so the party that
    FIRED the kill is the only one that can record the death. MEASURED across
    two nights: thirteen cycles left a log holding the runner's "lane start"
    header and nothing else, 134 bytes each, and a log that stops at its header
    cannot be told apart from a worker still running. Every one of those cycles
    was unreadable after the fact.

    APPENDED IN BINARY, NEVER REWRITTEN. The file may already hold everything
    the worker managed to say, and that is the diagnosis this note exists to
    complete rather than replace. Binary because the runner writes the file
    through ``Out-File -Encoding utf8``, which on Windows PowerShell 5.1 emits a
    BOM - a text-mode append would re-encode nothing but would let the platform
    choose a line ending, and this repository has already paid for a file whose
    two halves carried two encodings.

    THE WORD IS LOOKED UP, NOT RENDERED. ``reason`` is used only to find an
    index into :data:`ABORT_REASONS`, and what reaches the file is the element
    at that index - a literal THIS module holds. A caller's object never lands
    in the log however it spells itself, which is the same mechanism
    ``queue_loop._launch_fault`` uses one seam over and for the same reason: an
    exact ``str`` check rather than ``isinstance``, because a subclass can lie
    about both its comparison and its rendering.

    NEVER RAISES. This runs while a real ``LaneLaunchError`` is propagating and
    after the lane has already been released. A fault here would replace the
    refusal an operator needs with an unrelated error about a log file.

    Args:
        log: Where the worker's log lives, or None when the launch refused
            before it had decided. None is a real answer and a no-op.
        reason: A member of :data:`ABORT_REASONS`. Anything else degrades to
            ``REASON_UNSPECIFIED``, which records "it was aborted and nobody
            said why" rather than writing a word this module never chose.
    """
    if log is None or not str(log).strip():
        return
    word = REASON_UNSPECIFIED
    # EXACT ``str``, not ``isinstance`` - see the docstring.
    if type(reason) is str and reason in ABORT_REASONS:
        word = ABORT_REASONS[ABORT_REASONS.index(reason)]
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    line = f"{ABORT_PREFIX} {stamp} code=none reason={word}\n"
    with contextlib.suppress(OSError, ValueError, UnicodeEncodeError):
        target = Path(str(log))
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("ab") as handle:
            handle.write(line.encode("ascii"))


class LaneLaunchError(RuntimeError):
    """Anything that stops a lane from starting. Always releases the lane.

    Carries a machine-readable ``reason`` drawn from ``LAUNCH_REASONS`` beside
    the human message. ``str(exc)`` is the message and ONLY the message, exactly
    as it was before the keyword existed - the reason is a separate attribute
    precisely so that no caller's rendering changes.
    """

    def __init__(
        self,
        message: str,
        *,
        reason: str = REASON_UNSPECIFIED,
        waited_s: float | None = None,
        start_head: str | None = None,
    ) -> None:
        """Record the message, the refusal's reason, and the liveness wait it consumed.

        Args:
            message: What went wrong, in prose. May embed a path, so a caller
                that copies text out of this exception must copy the reason
                instead.
            reason: A member of ``LAUNCH_REASONS``. Defaults to
                ``REASON_UNSPECIFIED`` so a site that names none still hands a
                reader a word that is in the set.
            waited_s: CS-1017 - the seconds ``_spawn``'s liveness wait actually
                consumed, or None when the refusal came before any wait. It is
                what separates a runner that died INSIDE the grace from one
                killed AFTER it, which a cycle's total duration cannot.
            start_head: CS-1341 - the tree's HEAD ``launch_lane`` read before
                it was refused, or None when the refusal came before the read
                or the read got nothing. ``launch_lane`` sets it on the way
                out, so the driver's commit question still has the commit
                this tree held once the kit had made or moved it.
        """
        super().__init__(message)
        self.reason = reason
        self.waited_s = waited_s
        self.start_head = start_head
        # CS-1231 slice C - the runner log ``launch_lane`` had chosen, set by its
        # handler on the way out; None until then, and when it had chosen none.
        self.log: str | None = None


def worktree_path(lane: str) -> Path:
    """The worktree a lane runs in when it holds its HOME index - CS-1274.

    ``ops/loop/lanes.py`` owns the derivation, and it is the KIT'S:
    ``<parent of the main tree>/cs-worktrees/lane-<home index>``. This is the
    tree the driver reads a lane's HEAD in and keys its box-wide guard on; the
    tree a given cycle ACTUALLY runs in is the one its claim records, which is
    this one whenever the lane landed at home.

    Args:
        lane: The lane name.

    Returns:
        The lane's home worktree.

    Raises:
        ValueError: The lane is not on the roster, or has no home index.
    """
    return Path(lanes.home_worktree(lane))


def command_path(lane: str, root: Any = None) -> Path:
    """The tracked command doc that becomes the worker's prompt.

    Args:
        lane: The lane name.
        root: The repository root, or None for the main tree.

    Returns:
        The command doc's path.

    Raises:
        LaneLaunchError: The lane is not wired, or the doc is not on disk. A
            worker started against a doc that is not there would run to a clean
            exit having done nothing, which is the failure shape hardest to see.
    """
    relative = LANE_COMMANDS.get(lane)
    if relative is None:
        wired = ", ".join(sorted(LANE_COMMANDS)) or "none"
        message = f"lane {lane!r} has no command doc wired yet (wired: {wired})"
        raise LaneLaunchError(message, reason=REASON_LANE_NOT_WIRED)
    path = (REPO_ROOT if root is None else Path(root)) / relative
    if not path.is_file():
        message = f"command doc missing on disk: {path}"
        raise LaneLaunchError(message, reason=REASON_COMMAND_DOC_MISSING)
    return path


def _same_path(one: Any, other: Any) -> bool:
    """True when two spellings name the same directory.

    ``bool()`` around the comparison is not decoration: ``lanes`` is bound by
    file path, so its attributes are typed ``Any`` and the comparison would
    otherwise widen this function's declared ``bool`` back to ``Any`` the moment
    ``ops/`` joins the type gate.

    Args:
        one: A path.
        other: The path to compare it against.

    Returns:
        True when both spell the same directory.
    """
    return bool(lanes._key(one) == lanes._key(other))  # noqa: SLF001 - one owner, one spelling


def _git_free_env(environ: Mapping[str, str]) -> dict[str, str]:
    """``environ`` without any ``GIT_*`` name, the case of the name ignored.

    The filter every git child of this module gets - see ``_git``. CS-1341 -
    ``queue_loop._git_env`` is its twin for the driver's own reads, and
    ``tests/test_queue_loop.py`` feeds both one planted mapping and requires
    one answer. Only names are tested; no value is rendered (CLAUDE.md
    non-negotiable 13).

    Args:
        environ: The environment to filter.

    Returns:
        A copy of it with no ``GIT_*`` variable.
    """
    return {name: value for name, value in environ.items() if not name.upper().startswith("GIT_")}


def _git(args: list[str], cwd: Any = None, timeout: int = _GIT_TIMEOUT_S) -> Any:
    """Run one git command and hand back the completed process.

    The module attribute is the seam a test rebinds, so no arm here ever starts
    a real git - and since CS-1274 that holds for the kit's git calls too,
    because ``_kit_git`` hands the kit THIS function rather than letting it
    start its own.

    THE CHILD GETS NO ``GIT_*`` VARIABLE, as the kit's own runner does. A git
    started from inside a hook inherits ``GIT_DIR`` and ``GIT_INDEX_FILE``, and
    every ``-C`` below would then act on the repository the HOOK was running in.
    Only names are filtered; no value is read or rendered (CLAUDE.md
    non-negotiable 13). CS-1341 - ``queue_loop._git_env`` applies the SAME
    filter to the driver's own HEAD reads, so the start head read here and
    the HEAD the driver reads after the cycle name one repository; tests in
    ``tests/test_queue_loop.py`` hold the two to one environment and the two
    filters to one answer.

    Args:
        args: The arguments after ``git``.
        cwd: Where to run it.
        timeout: Seconds before the call is abandoned as hung.

    Returns:
        The completed process.
    """
    exe = resolve_tool("git")
    if exe is None:
        # A lane that cannot find git cannot make its worktree, and a worktree
        # is mandatory. Refusing loudly beats spawning into the wrong tree.
        raise LaneLaunchError("git could not be resolved from PATH", reason=REASON_GIT_NOT_FOUND)
    env = _git_free_env(os.environ)
    return subprocess.run(
        [exe, *args],
        # tracked file is forbidden by CLAUDE.md non-negotiable 3
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        creationflags=_NO_WINDOW,
    )


def _kit_git(*args: str) -> Any:
    """The kit's ``run`` seam, answered by ``_git`` - so git is still resolved from PATH.

    ``fleet_lanes.ensure_worktree`` takes a ``run(*args)`` and calls it with
    ``-C <repo>`` in front of every command. Routing it through ``_git`` keeps
    CS-910's rule - the program is RESOLVED FROM PATH, never named, so a
    ``git.exe`` planted in a working directory is never the one that runs -
    and keeps the arms' single git seam covering the kit's calls too.

    Args:
        *args: The arguments after ``git``, exactly as the kit passes them.

    Returns:
        The completed process.
    """
    return _git(list(args))


def _refuse_main_tree(worktree: Any, repo: Any, lane: str) -> None:
    """Refuse to run a lane against a main working tree.

    BOTH the root this call was given AND the repository's real root are
    consulted. Checking only the given root would make overriding ``root`` a way
    to point a lane at the checkout the operator is reading.

    Args:
        worktree: The proposed working directory.
        repo: The repository root this call was given.
        lane: The lane name, for the message.

    Raises:
        LaneLaunchError: The worktree is a main tree.
    """
    if _same_path(worktree, repo) or _same_path(worktree, REPO_ROOT):
        message = f"refusing to run lane {lane!r} against the main tree"
        raise LaneLaunchError(message, reason=REASON_MAIN_TREE_REFUSED)


def claimed_worktree(token: Any) -> tuple[Path, int | None]:
    """The worktree and index the lane CLAIM recorded - the only source of either.

    Read off the lock the token names. A lock written before CS-1274 carries
    no index, which reads as None and makes the tree a caller-named one.

    Args:
        token: What ``lanes.try_acquire_lane`` handed back.

    Returns:
        The recorded worktree and the recorded index.

    Raises:
        LaneLaunchError: No readable lock, or one that names no worktree.
    """
    record = lanes.read_payload(Path(str(token))) if token else {}
    recorded = lanes.str_or_none(record.get("worktree"))
    if recorded is None or not recorded.strip():
        message = "the lane claim could not be read, so it names no worktree to run in"
        raise LaneLaunchError(message, reason=REASON_CLAIM_UNREADABLE)
    index = record.get("index")
    return Path(recorded), index if type(index) is int else None


def _is_kit_tree(worktree: Path, index: int | None) -> bool:
    """True when the claim's tree IS the kit's derivation for the claim's index.

    Args:
        worktree: The recorded worktree.
        index: The recorded index, or None.

    Returns:
        True only for the kit's own per-index tree.
    """
    if index is None:
        return False
    try:
        derived = lanes.lane_worktree(index)
    except ValueError:
        return False
    return bool(lanes.same_tree(worktree, derived))


def prepare_worktree(worktree: Path, index: int | None, root: Any = None) -> Path:
    """Make the claimed tree ready to run in - through the KIT for the kit's own tree.

    THE KIT'S TREE IS THE KIT'S TO PREPARE. ``fleet_lanes.ensure_worktree`` is
    called, never re-implemented: a missing tree is added detached at
    ``LANE_BASE``; a present one must be a clean linked worktree of this
    repository, its unmerged commits saved under ``refs/fleet-lanes/`` before it
    moves to the base. A dirty one is REFUSED and never cleaned - it is a
    crashed run's work, and that is the kit's ruling.

    A CALLER-NAMED TREE IS THE CALLER'S. It is run in as it stands, and it must
    already be a checkout; this module creates only the kit's layout.

    NOTHING THE KIT SAYS IS RENDERED. Its refusal text carries the worktree
    path and git's own stderr, so the message raised here is fixed text and the
    kit's exception rides only as the chained cause.

    Args:
        worktree: The claimed tree.
        index: The claimed index, or None.
        root: The repository root git runs in, or None for the main tree.

    Returns:
        The tree, ready.

    Raises:
        LaneLaunchError: The kit refused the tree, or a caller-named tree is
            not a checkout.
    """
    repo = REPO_ROOT if root is None else Path(root)
    if _is_kit_tree(worktree, index):
        kit = lanes.kit_lanes()
        try:
            kit.ensure_worktree(repo, worktree, base=LANE_BASE, run=_kit_git)
        except kit.LaneRefused as exc:
            message = (
                "the kit refused this lane's worktree - a dirty tree is resolved by "
                "hand and never cleaned; see the kit's ensure_worktree"
            )
            raise LaneLaunchError(message, reason=REASON_WORKTREE_REFUSED) from exc
        return worktree
    if not (worktree / ".git").exists():
        message = "the worktree this claim names is not a checkout, and only the kit's are made"
        raise LaneLaunchError(message, reason=REASON_WORKTREE_MISSING)
    return worktree


def ensure_worktree(lane: str, *, token: Any, root: Any = None) -> Path:
    """The ONE worktree step of a launch: read the claim, guard it, prepare it.

    The name is kept from before CS-1274 because it is the seam the launch
    arms substitute; what it does changed - it no longer derives a path from
    the lane, it runs the worker where the CLAIM says.

    Args:
        lane: The lane name, for the main-tree refusal's message.
        token: What ``lanes.try_acquire_lane`` handed back.
        root: The repository root git runs in, or None for the main tree.

    Returns:
        The worktree, ready to run in.

    Raises:
        LaneLaunchError: The claim is unreadable, names a main tree, or names a
            tree that cannot be made ready.
    """
    claimed, index = claimed_worktree(token)
    # BEFORE the kit is asked to touch it: a main tree is refused before any
    # git runs in or against it.
    _refuse_main_tree(claimed, REPO_ROOT if root is None else Path(root), lane)
    return prepare_worktree(claimed, index, root=root)


def _start_head(worktree: Any) -> str | None:
    """The commit the worker STARTS from: the tree's own ``HEAD``, read after the kit.

    CS-1341. The kit makes a missing lane tree, and moves a present one to
    ``LANE_BASE``, inside ``ensure_worktree`` - so a read taken before the
    launch, where the driver used to take its only one, sees no tree at all or
    the commit the kit is about to move away from. Read here, between the kit
    and the spawn, it is the commit this cycle's worker begins at.

    The tree's ``HEAD`` and never ``origin/main``: the remote says where work
    landed, not where this worker began. ``rev-parse`` mutates nothing - no
    fetch, no index lock. A tree with no ``.git`` of its own is not asked,
    because git searches upward and would answer for a checkout that
    contains it.

    None on every failure and NEVER a raise. The read is evidence for the
    driver, not a gate on the launch, and the driver falls back to its own
    early read when this is None.

    Args:
        worktree: The tree ``ensure_worktree`` returned.

    Returns:
        The tree's HEAD, or None.
    """
    try:
        if not (Path(worktree) / ".git").exists():
            return None
        proc = _git(["-C", str(worktree), "rev-parse", "HEAD"])
    except Exception:  # see the docstring - a failed read is a None, never a refusal
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip() or None


def _log_path(lane: str, run_id: Any, log_dir: Any = None) -> Path:
    """Where this fire's worker log is written.

    Args:
        lane: The lane name.
        run_id: The caller's run identifier. Filtered before it reaches a
            filename - a run id is an input, and an input that becomes a path
            is a path traversal waiting for the wrong caller.
        log_dir: The log directory, or None for the default.

    Returns:
        The log path.
    """
    directory = LOG_DIR if log_dir is None else Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe = "".join(
        character for character in str(run_id) if character.isalnum() or character in _SAFE_RUN_ID
    )[:_SAFE_RUN_ID_LENGTH]
    return directory / f"lane_{lane}_{safe or 'run'}.log"


def _spawn(runner: Path, prompt: Path, cwd: Path, log: Path) -> Any:
    """Start the hidden PowerShell runner and prove it survived its own start.

    Args:
        runner: The PowerShell runner.
        prompt: The command doc piped to the worker on stdin.
        cwd: The worktree the worker runs in.
        log: Where the worker's output is written.

    Returns:
        The process handle.

    Raises:
        LaneLaunchError: The runner is missing, the spawn failed, or the runner
            exited inside the liveness grace - see the module docstring.
    """
    if not runner.is_file():
        message = f"runner missing: {runner}"
        raise LaneLaunchError(message, reason=REASON_RUNNER_MISSING)
    # RESOLVED FROM PATH, NEVER NAMED (CS-910). This is the single most exposed
    # spawn in the tree: `cwd` below is the LANE WORKTREE, the directory an
    # unattended worker writes into for hours, and Windows searches the current
    # directory before PATH. A `powershell.exe` dropped there by the worker
    # would be executed by the launcher that started it, on the next cycle.
    shell = resolve_tool("powershell")
    if shell is None:
        raise LaneLaunchError(
            "powershell could not be resolved from PATH", reason=REASON_SHELL_NOT_FOUND
        )
    argv = [
        shell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(runner),
        "-PromptFile",
        str(prompt),
        "-Cwd",
        str(cwd),
        "-Log",
        str(log),
    ]
    try:
        # CS-1225 - ROUTED OR REFUSED. The child's environment is a COPY built
        # by the route module, which fails closed when the proxy variable is
        # unset or the proxy is down. A refusal joins the OSError below at the
        # ONE spawn-failed raise site rather than adding a thirteenth, because
        # the reason vocabulary is pinned one-to-one to raise sites and copied
        # into the driver; the authored ``.reason`` is what reaches the message.
        env = headless_route.child_env(os.environ)
        # A fixed argv assembled here - no shell, and no caller string reaches
        # the command line. "powershell" is resolved from PATH because an
        # absolute tool path in a tracked file is forbidden by CLAUDE.md
        # non-negotiable 3.
        proc = subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_NO_WINDOW,
        )
    except (OSError, headless_route.HeadlessRouteRefused) as exc:
        # A NAMED FIELD, NEVER THE OBJECT. ``str()`` on an OSError appends the
        # PATH it failed on, and the paths this function handles run through a
        # user profile - so rendering the exception whole is a personal-data
        # echo path (CLAUDE.md non-negotiable 12). ``strerror`` is the operating
        # system's message text and carries no path; the type name is the
        # fallback when there is no strerror to render. A route refusal's
        # ``reason`` is authored, names the variable and never its value.
        if isinstance(exc, OSError):
            detail = exc.strerror or type(exc).__name__
        else:
            detail = f"headless route refused - {exc.reason}"
        message = f"spawn failed: {detail}"
        raise LaneLaunchError(message, reason=REASON_SPAWN_FAILED) from exc

    # CS-1017 - MEASURED around the wait itself and nothing else, so the number
    # is the grace consumed rather than the spawn plus the grace.
    wait_began = _monotonic()
    try:
        code = proc.wait(timeout=_SPAWN_LIVENESS_GRACE_S)
    except subprocess.TimeoutExpired:
        setattr(proc, _WAITED_ATTR, round(_monotonic() - wait_began, 3))
        return proc
    except BaseException:
        # CS-1274 r2 - INTERRUPTED INSIDE THE GRACE. The runner exists and no
        # caller holds its pid yet, so this is the only party that can stop it
        # before the interrupt goes on up; left alone it is a worker no lock
        # names. The interrupt itself is re-raised whole.
        _kill(proc.pid)
        raise
    waited = round(_monotonic() - wait_began, 3)
    message = (
        f"the runner exited {code} within {_SPAWN_LIVENESS_GRACE_S}s of starting,"
        " so no worker is behind this lane"
    )
    raise LaneLaunchError(message, reason=REASON_RUNNER_EXITED_EARLY, waited_s=waited)


def _kill_argv(pid: Any) -> list[str] | None:
    """The argv that kills a process tree, or None when taskkill cannot be found.

    taskkill, never the PowerShell cmdlet - Stop-Process has hung the tooling
    pipe on this machine.

    ``/T`` IS REQUIRED, the same flag for the same reason as the driver's
    ``queue_loop._taskkill`` (CS-1274 r3). The pid this module spawned is the
    PowerShell WRAPPER ``run_lane.ps1`` runs in; its child is the fleet kit's
    ``python``, and ``claude`` is the kit's child - the wrapper's GRANDCHILD
    (CS-1231 slice C): killing only the wrapper leaves a live writer in the
    lane worktree while the lane is released and reads FREE behind it. The two
    killers are mirrors rather than one shared function - the launcher importing
    the driver would invert the seam - and ``tests/test_lane_launcher.py`` pins
    their argv to agree. Neither has a POSIX branch: the runner is a PowerShell
    script.

    THE PROGRAM IS RESOLVED FROM PATH, NEVER NAMED (CS-910). Windows searches
    the current directory before PATH, and this spawn happens with the LANE
    WORKTREE as the working directory - the one place an unattended worker has
    been writing files for hours. A bare name here is that finding at its most
    reachable.

    Args:
        pid: The process id.

    Returns:
        The argv, or None when taskkill did not resolve. None is a real answer
        rather than an error: the only caller already treats a failed kill as a
        failed kill, and the driver's own verified re-probe is what turns that
        into a stop.
    """
    killer = resolve_tool("taskkill")
    return None if killer is None else [killer, "/F", "/T", "/PID", str(pid)]


def _kill(pid: Any) -> None:
    """Kill one process and its whole tree, reporting nothing.

    Args:
        pid: The process id.
    """
    # A kill that itself fails must not mask the failure that asked for it.
    argv = _kill_argv(pid)
    if argv is None:
        return
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run(
            argv,
            capture_output=True,
            timeout=_KILL_TIMEOUT_S,
            check=False,
            creationflags=_NO_WINDOW,
        )


def _kill_untracked(pid: Any, *, tracked: bool) -> None:
    """Kill a spawned worker no lock names yet; a tracked or absent one is left alone.

    A TRACKED worker is the lock's: the lane reads RUNNING behind it for as long
    as it lives, which is the honest answer. An UNTRACKED one is invisible to
    every reader, so once the lane is released its worktree would be handed to
    a second writer.

    Args:
        pid: The worker's pid, or None when no worker was started.
        tracked: True once the lock was re-pointed at it.
    """
    if pid and not tracked:
        _kill(pid)


def launch_lane(
    lane: str,
    *,
    run_id: Any,
    token: Any,
    base: Any = None,
    root: Any = None,
    log_dir: Any = None,
    spawn: Any = None,
) -> dict[str, Any]:
    """Start the lane's worker and re-point its lock at the spawned process.

    On ANY failure the lane is released before the error propagates, so a failed
    launch can never leave a lock nobody is behind. If the lock cannot be
    re-pointed the spawned worker is KILLED and the launch fails: a worker that
    cannot be tracked is worse than no worker, because the lane would read
    RUNNING behind the claimer forever while a real process kept working.

    Args:
        lane: The lane to start.
        run_id: The caller's run identifier.
        token: What ``lanes.try_acquire_lane`` handed back. The worktree is the
            one its lock records - see ``claimed_worktree``.
        base: ACCEPTED AND IGNORED since CS-1274, so an older caller does not
            raise. It used to name a directory worktrees were derived under; the
            claim names the worktree now, and a second derivation here could
            only ever disagree with the one every reader of the lock trusts.
        root: The repository root, or None for the main tree.
        log_dir: The log directory, or None for the default.
        spawn: The injection seam. The DEFAULT REALLY STARTS A PROCESS and no
            test may reach it.

    Returns:
        The lane, the run id, the worker pid, the worktree, the log, the
        prompt, the start head (CS-1341 - the tree's HEAD after the kit and
        before the spawn, None when it could not be read) and the wall-clock
        start time. The liveness wait a SURVIVING worker
        consumed is not among them: this key set is pinned by
        ``tests/test_lane_launcher.py``, and the wait is carried only on a
        refusal, where it is what tells an early exit from a post-grace kill.

    Raises:
        LaneLaunchError: Anything at all went wrong. The lane is released first.
    """
    del base  # see Args - superseded by the claim's own worktree
    starter = _spawn if spawn is None else spawn
    repo = REPO_ROOT if root is None else Path(root)
    # BOUND BEFORE THE TRY, so the refusal handlers can reach it whether or not
    # the launch got as far as choosing one. A refusal ahead of ``_log_path``
    # leaves it None, which ``note_worker_abort`` reads as "there is no log to
    # complete" rather than inventing a path.
    log: Path | None = None
    # CS-1274 r2 - THE SPAWN-TO-RE-POINT WINDOW. ``pid`` is bound the moment a
    # worker exists and ``tracked`` once the lock names it; a fault or an
    # interrupt between the two leaves a worker NO lock names, so every handler
    # below kills it before the lane is released.
    pid: Any = None
    tracked = False
    # CS-1341 - BOUND BEFORE THE TRY too, so a refusal after the read hands
    # the driver what the read got, and one before it hands back None.
    start_head: str | None = None
    try:
        prompt = command_path(lane, root=root)
        worktree = ensure_worktree(lane, token=token, root=root)
        # AGAIN after the worktree step: the two checks happen at different
        # moments, and a path can be handed in between.
        _refuse_main_tree(worktree, repo, lane)
        # CS-1341 - AFTER the kit has made or moved the tree, BEFORE the worker
        # can commit in it: the one place the read names the commit this
        # worker starts from. See `_start_head`.
        start_head = _start_head(worktree)
        log = _log_path(lane, run_id, log_dir=log_dir)
        proc = starter(RUNNER, prompt, worktree, log)
        pid = getattr(proc, "pid", None)
        # CS-1017. None from a spawn seam that does not measure, which the
        # driver writes as None rather than as a number nobody took.
        waited = getattr(proc, _WAITED_ATTR, None)
        if not pid:
            message = "spawn returned no pid"
            raise LaneLaunchError(message, reason=REASON_SPAWN_NO_PID, waited_s=waited)
        if not lanes.repoint_lane_pid(token, pid):
            _kill(pid)
            message = "could not re-point the lane lock at the worker"
            raise LaneLaunchError(message, reason=REASON_REPOINT_REFUSED, waited_s=waited)
        tracked = True
    except LaneLaunchError as exc:
        lanes.release_lane(token)
        # AFTER the release, never before. The lane is the thing another cycle
        # is waiting on; the note is diagnosis, and diagnosis never delays a
        # release.
        note_worker_abort(log, exc.reason)
        # CS-1231 slice C, R1 - THE LOG GOES BACK WITH THE REFUSAL. The runner
        # starts the fleet kit, and a kit refusal ends it inside the liveness
        # grace on every run, so this refusal is the ONLY answer the driver gets;
        # the runner's last lines name the kit's code, and the driver reads them
        # off this path - its own literal, never this exception's message.
        exc.log = None if log is None else str(log)
        exc.start_head = start_head
        raise
    except Exception as exc:  # ANY fault at all must free the lane, not only ours
        # BEFORE the release: a worker no lock names must not outlive the lane
        # it was started for, or the next claim hands its worktree to a second.
        _kill_untracked(pid, tracked=tracked)
        lanes.release_lane(token)
        note_worker_abort(log, REASON_UNEXPECTED_FAULT)
        # The TYPE only. This handler catches anything at all, so there is no
        # type whose fields are known to be path-free - and the chained cause
        # still carries the full detail into the traceback for a reader who is
        # entitled to it (CLAUDE.md non-negotiable 12).
        message = f"launch failed: {type(exc).__name__}"
        raise LaneLaunchError(
            message, reason=REASON_UNEXPECTED_FAULT, start_head=start_head
        ) from exc
    except BaseException:
        # CS-1274 r2 - AN INTERRUPT IS NOT AN ``Exception``. KeyboardInterrupt
        # or SystemExit between the spawn and the re-point used to skip both
        # handlers above and leave the worker running untracked. The same
        # clean-up, then the interrupt re-raised WHOLE - converting it into a
        # launch refusal would let a driver's own catch-all swallow a stop.
        _kill_untracked(pid, tracked=tracked)
        lanes.release_lane(token)
        note_worker_abort(log, REASON_UNEXPECTED_FAULT)
        raise
    return {
        "lane": lane,
        "run_id": str(run_id),
        "pid": pid,
        "worktree": str(worktree),
        "log": str(log),
        "prompt": str(prompt),
        "start_head": start_head,
        "started_at": time.time(),
    }
