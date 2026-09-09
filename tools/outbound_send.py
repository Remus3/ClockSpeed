#!/usr/bin/env python3
"""CS-958 - the only way a note leaves this machine, with the gate in front.

WHY THIS EXISTS. `tools/outbound_gate.py` grades outbound text and, until this
module, NOTHING CALLED IT - measured: a repo-wide grep returned the gate and its
tests and zero call sites. An instrument beside the channel is not a gate in
front of it. This module is what makes the grading unavoidable, by being the
thing that does the writing.

THE CHANNEL HAD NO SENDER AT ALL, which is the other half of why this exists.
Every delivery this project has ever made was a hand-run script, including the
correction sent to four sibling repositories on 2026-09-08, whose only record is
a paragraph a human typed into the ledger. That is CS-951's subject: 19 outbound
notes are traceable in sibling inboxes and none was recorded here.

DRY RUN IS THE DEFAULT AND `--send` IS THE ONLY WAY TO WRITE A BYTE. A send is
irreversible in the way that matters - the bytes are in another repository
before anyone re-reads them, and this project has already watched a sibling
publish an operator's address and be unable to unpublish it. When the reversible
and irreversible options are both available, the default has to be the
reversible one.

THE GATE RUNS FIRST, BEFORE ANY DESTINATION IS RESOLVED, and the ordering is a
property rather than an implementation detail. A sender that resolved the
channel first would report the wrong cause when both faults are present: the
operator fixes the missing sibling, re-runs, and only then discovers the note
carries a home path. The gate is also the cheaper check, and the one whose
answer cannot be changed by the state of the channel.

ANY FAULT REFUSES THE WHOLE SEND, AND THE FIRST VERSION OF THIS CLAIM WAS
FALSE. It validated every destination and then wrote in a loop, so a failure on
the third write left the first two delivered while stderr said "nothing was
sent" - demonstrated in one command by an adversary, who put a DIRECTORY at the
temporary name the writer uses, a name validation never checked. The repair is
two phases: every destination is STAGED to a temporary file first, and only when
all of them are staged is any of them renamed into place. The failure-prone work
- space, permissions, a path too long, a name already taken - happens in the
phase where nothing has been delivered yet, and a failure there unlinks the
staged files and delivers nothing.

WHAT TWO PHASES STILL DO NOT BUY, stated rather than glossed. A failure DURING
the rename phase can still leave a subset delivered; a rename is per-file and
this is not a transaction. So the tool no longer claims otherwise: it records
every destination that actually landed, names them, and says plainly that a
partial delivery occurred. A record that is honest about a partial send is what
a CS-951 reconciler needs; a message asserting "nothing was sent" over a
delivered note is worse than the partial send itself.

UNMEASURED IS NOT CLEARED. A class the gate could not derive is a class nobody
looked at, so the default is to refuse and `--allow-unmeasured` is an explicit
operator act that lands in the record as the verdict at the time of sending.
A reader of that record can then tell a delivery that was fully graded from one
that was not, which a boolean "sent" flag could never express.

THE NOTE IS READ EXACTLY ONCE, AND THAT IS A SECURITY PROPERTY RATHER THAN AN
OPTIMISATION. The first version read the note to grade it and read it AGAIN to
deliver it, so anything that changed the file in between was delivered
ungraded. Demonstrated: a writer thread swapping a home path into a large note
during the gate's scan produced a delivery whose bytes the gate would have
refused, recorded under `"gate_verdict": "CLEAN"` beside the digest of the
DIRTY bytes - the record permanently attesting a grade that never happened to
the bytes it names. The payload is now read once, graded as bytes, delivered as
those same bytes, and recorded by their digest. There is no window because
there is no second read.

A DESTINATION IS GRADED AS A RESOLVED PATH, NOT AS A STRING, AND THE FIRST
VERSION OF THIS CLAIM WAS ALSO FALSE. It checked the SPELLING - no separator, no
drive, no leading dot, one path component - and then followed wherever that
spelling led. A string cannot tell you where a path goes. Measured, all three
against a synthetic root: a junction made with `mklink /J` passed the shape
check and delivered a note OUTSIDE the channel root with exit 0; `--to` at this
repository's own name delivered into this repository's own inbox, because the
self-exclusion lived in the discovery function that only `--all` calls; and a
trailing dot, which Win32 strips, put the note in one directory and recorded it
under a name no directory has.

So a destination is accepted only when `root / name / INBOX` RESOLVES to a
directory whose grandparent is the resolved channel root and which is not this
repository, and the name that reaches the record is RE-DERIVED from that
resolved directory. The shape check stays in front of it because it is cheap and
because an absolute name really does replace the root outright - `Path("/a") /
"C:/b"` yields `C:/b` - but it is a fast rejection and never the containment
guarantee. The same resolved path is what the dedup is keyed on: two spellings
of one directory on a case-insensitive filesystem are one destination, not two,
and treating them as two staged one temporary file twice and reported a complete
delivery as PARTIAL.

AND THIS REPOSITORY'S IDENTITY IS DERIVED FROM THE REPOSITORY, NOT FROM WHERE
THIS FILE SITS. The clause above refuses a destination that resolves to us, and
its first cut compared against the directory the running file sits in. That is
the WORKTREE when the tool runs from one, and worktree-isolated slices are this
project's default session shape - so the clause was false in exactly the place
the work is done, and `--to <our own name>` resolved into our own inbox as
before. `self_root()` walks up to `.git` and reads the worktree link when it
finds a file rather than a directory, degrading to the file-relative answer
when there is no `.git` at all.

WHAT THIS RECORDS AND WHAT IT DOES NOT. One entry per DESTINATION rather than
one per send, because a pooled entry for two siblings cannot answer the
reconciler's question about either. It records the destination by NAME and never
by path: an absolute path in a record is a path that leaks the machine, and the
name is what a later run needs to look the delivery up again. It never records a
byte of the payload.

THIS IS HALF OF CS-951 AND SAYS SO. Detecting that a recorded delivery has since
VANISHED from its destination is the other half and belongs to that item. The
record is built to be sufficient for it - name, digest, size, timestamp - and
this module does not attempt it.

Exit codes, a closed set a caller can branch on:

    0  delivered, or a dry run that would have delivered
    1  refused - by the gate, a missing destination, a collision, or because
       this tool itself raised. Fail closed.
    2  usage
    3  the gate returned UNMEASURED and --allow-unmeasured was not given
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

#: Where THIS FILE sits, which is what the gate beside it and the record
#: beneath it are relative to. It is NOT this project's identity on the
#: channel - see :func:`self_root`, and the two really do differ in the shape
#: this project works in every day.
REPO_ROOT = Path(__file__).resolve().parents[1]
OUTBOUND_GATE = REPO_ROOT / "tools" / "outbound_gate.py"


def _main_checkout_of_worktree(dot_git: Path) -> Path | None:
    """The main checkout behind a worktree's `.git` FILE, or None if it is unreadable.

    A worktree's `.git` is a file holding one `gitdir:` line pointing at
    `<main checkout>/.git/worktrees/<name>`, and that directory holds a
    `commondir` file whose contents locate the shared `.git`. Both are plain
    text and both are read here with plain file I/O - NO SUBPROCESS. A tool
    whose whole job is to decide whether bytes may leave should not shell out
    to answer a question about its own installation, and a `git` that is
    absent, slow or hooked would turn a delivery decision into a process
    launch.

    None means "cannot tell", never a guess: the caller degrades rather than
    inventing an identity.
    """
    try:
        gitdir_line = next(
            (
                line
                for line in dot_git.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip().startswith("gitdir:")
            ),
            None,
        )
        if gitdir_line is None:
            return None
        gitdir = Path(gitdir_line.split(":", 1)[1].strip())
        if not gitdir.is_absolute():
            gitdir = dot_git.parent / gitdir
        gitdir = gitdir.resolve()
        commondir = gitdir / "commondir"
        if commondir.is_file():
            relative = commondir.read_text(encoding="utf-8", errors="replace").strip()
            common = (gitdir / relative).resolve() if relative else None
        elif gitdir.parent.name == "worktrees":
            common = gitdir.parent.parent
        else:
            common = None
    except OSError:
        return None
    if common is None or common.name != ".git":
        return None
    return common.parent


def self_root() -> Path:
    """WHICH CHANNEL PARTICIPANT THIS PROCESS IS. Not the directory this file sits in.

    THE DISTINCTION IS THE WHOLE OF CS-958 D3 AND IT WAS MEASURED, not argued.
    The identity clause in :func:`resolve_targets` refuses a destination that
    resolves to this repository, and its first cut compared against
    `Path(__file__).resolve().parents[1]`. That is the checkout the running
    FILE sits in - which, in a git worktree, is the worktree and not the
    project on the channel. This project's default session shape is
    worktree-isolated slices, so the acceptance clause was false in the shape
    the work is actually done in: a copy running from a worktree resolved this
    repository's own name into this repository's own inbox exactly as it had
    before the repair.

    So the identity is derived from the REPOSITORY rather than from the file:
    walk up from this file to the first `.git`. A `.git` DIRECTORY means an
    ordinary checkout and its parent is the answer. A `.git` FILE means a
    worktree, and it carries a `gitdir:` line from which the main checkout is
    derivable - see :func:`_main_checkout_of_worktree`.

    IT DEGRADES AND NEVER RAISES, and the fallback is stated because a caller
    reading a refusal deserves to know what was compared. When there is no
    `.git` anywhere above this file - a tarball export, a vendored copy, a
    single-file deployment - or when the worktree link cannot be read, the
    answer falls back to :data:`REPO_ROOT`, which is exactly the old behaviour
    and is correct for every checkout that is not a worktree. A send must not
    fail because the tool could not work out its own name.
    """
    here = Path(__file__).resolve()
    for candidate in here.parents:
        dot_git = candidate / ".git"
        try:
            if dot_git.is_dir():
                return candidate
            if dot_git.is_file():
                found = _main_checkout_of_worktree(dot_git)
                return found if found is not None else REPO_ROOT
        except OSError:
            return REPO_ROOT
    return REPO_ROOT


try:
    #: This repository's identity ON THE CHANNEL, resolved once at import.
    SELF_ROOT = self_root()
except OSError:  # pragma: no cover - degrade rather than refuse to start
    SELF_ROOT = REPO_ROOT

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2
EXIT_UNMEASURED = 3

#: The inbox directory name every participant on this channel uses.
INBOX = "moon_sync_inbox"

#: Where the delivery record lives by default. Under `data/`, which is
#: gitignored, because it is a generated runtime artifact and not a tracked
#: fact. The environment override exists so a test can redirect it out of the
#: repository entirely - a suite that appended to the operator's real record
#: would corrupt the very history CS-951 wants to reconcile against.
ENV_RECORD = "CLOCKSPEED_OUTBOUND_RECORD"
DEFAULT_RECORD = REPO_ROOT / "data" / "outbound_deliveries.json"

#: The gate's verdicts, spelled the way the gate spells them so a reader of the
#: record and a reader of the gate's own output are reading one vocabulary.
VERDICT_NAME = {EXIT_OK: "CLEAN", EXIT_UNMEASURED: "UNMEASURED"}

TOOL = "outbound-send"

# How a refusal refers to the note's own filename. A LABEL AND NEVER THE VALUE:
# the filename is the one string that is simultaneously outbound bytes, a
# record field and a thing a sibling's watcher prints, so a refusal about it
# must not be a second copy of it.
NOTE_LABEL = "the note's filename"


class QuietParser(argparse.ArgumentParser):
    """An argument parser that never echoes what it was given.

    The same defect the gate carried and the same repair: the stock parser's
    error path writes the argument vector to stderr, and the ordinary slip of
    passing a note's TEXT rather than its path would print the whole ungraded
    payload. `--help` maps to the usage code because 0 means DELIVERED here and
    a help run delivered nothing.
    """

    def error(self, message: str) -> None:  # type: ignore[override]  # noqa: ARG002
        """Report a usage error without quoting the argument vector."""
        write_stream(sys.stderr, "%s: usage error; nothing was sent\n" % TOOL)
        raise SystemExit(EXIT_USAGE)

    def exit(self, status: int = 0, message: str | None = None) -> None:  # type: ignore[override]
        """Leave through the usage code, never through the delivered code."""
        if message:
            write_stream(sys.stderr, message)
        raise SystemExit(EXIT_USAGE if status == 0 else status)


def write_stream(stream: object, payload: str) -> None:
    """Write to a stream, tolerating one that has gone away.

    Swallowing the write is not enough on its own: a failed flush leaves the
    payload in the buffer and CPython flushes again at interpreter shutdown,
    which it reports by overriding the exit status with 120 - a code outside the
    set this tool tells a caller to branch on. Pointing the descriptor at the
    null device discards the buffer's destination so the shutdown flush succeeds
    against nothing. Measured on the gate, repaired there first, and reproduced
    here rather than imported because the two tools must not share a failure.
    """
    try:
        stream.write(payload)  # type: ignore[attr-defined]
        stream.flush()  # type: ignore[attr-defined]
    except (OSError, ValueError, AttributeError):
        _neutralise(stream)


def _neutralise(stream: object) -> None:
    """Point a broken stream at the null device so shutdown cannot re-raise."""
    try:
        fileno = stream.fileno()  # type: ignore[attr-defined]
    except (OSError, ValueError, AttributeError):
        return
    try:
        null = os.open(os.devnull, os.O_WRONLY)
    except OSError:
        return
    try:
        with contextlib.suppress(OSError):
            os.dup2(null, fileno)
    finally:
        with contextlib.suppress(OSError):
            os.close(null)


def _ascii(value: str) -> str:
    """Force a rendered line to 7-bit ASCII (CLAUDE.md non-negotiable 4)."""
    return value.encode("ascii", "replace").decode("ascii")


def load_outbound_gate() -> ModuleType:
    """Load the gate by path rather than by package import.

    `tools/` is a namespace package with no `__init__.py`, so the import form
    depends on the caller's `sys.path`, and the invocation path of whatever
    drives this sender is not this project's to assume.
    """
    name = "clockspeed_outbound_gate_for_sender"
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, OUTBOUND_GATE)
    if spec is None or spec.loader is None:
        message = "cannot load the outbound gate from " + OUTBOUND_GATE.name
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def channel_root(override: str | None) -> Path:
    """Where sibling projects live.

    Defaults to the repository root's PARENT, resolved from this file and never
    from the working directory - a tool that resolves its own paths from
    wherever the process happens to be standing is a tool that silently reads
    the wrong tree.
    """
    return Path(override).resolve() if override else REPO_ROOT.parent


def inbox_holders(root: Path) -> list[str]:
    """Every project directory under `root` with an inbox DIRECTORY.

    A directory and not merely an existing path: a project whose
    `moon_sync_inbox` is a file is not a destination, and writing a note
    "into" it would fail halfway through a multi-destination send.

    THIS REPOSITORY IS EXCLUDED FROM ITS OWN BROADCAST. Found by running the
    real thing rather than by reading it: a dry run against the live channel
    listed five destinations and the first was this project, because it has an
    inbox like every other participant. A note delivered there would be read
    back by this repository's own watcher as inbound mail from itself - unread
    count up by one, sender ourselves, and nothing on the channel to show for
    it.
    """
    if not root.is_dir():
        return []
    found: list[str] = []
    with contextlib.suppress(OSError):
        found.extend(
            entry.name
            for entry in sorted(root.iterdir())
            if entry.is_dir() and (entry / INBOX).is_dir() and entry.resolve() != REPO_ROOT
        )
    return found


def grade(payload: bytes) -> tuple[int, str, str]:
    """Grade BYTES ALREADY IN HAND, returning (code, its stdout, its stderr).

    Bytes rather than a path, so that what was graded and what is delivered are
    the same object and no window exists between them. Taking a path here is
    what made the gate bypassable: the grader read the file, the writer read it
    again, and anything that changed in between shipped ungraded under a CLEAN
    verdict.

    In process rather than as a subprocess so the sender and the gate cannot
    drift into two answers about one payload, and so no payload ever reaches an
    argument vector.

    THIS FUNCTION GRADES THE PAYLOAD AND ONLY THE PAYLOAD. It took `payload:
    bytes` and nothing else for its whole first life, which meant a note's
    FILENAME and a destination's NAME were never graded at all - the gate stood
    in front of the content and beside everything else, and the same value it
    REFUSES in a note shipped as that note's filename under a recorded verdict
    of CLEAN (CS-958 F1). The names go through :func:`grade_names`, which is
    the same gate through a different door, NOT a second scanner.
    """
    gate = load_outbound_gate()
    refusals, warnings, coverage = gate.scan(payload.decode("utf-8"))
    out, err = gate.render(refusals, warnings, coverage)
    return gate.verdict(refusals, coverage), out, err


def _which(position: int, discovered: bool) -> tuple[str, str]:
    """Name ONE destination in a refusal, without echoing what it is called.

    Returns (how to refer to it, how to locate it). For a TYPED destination the
    reference is an ORDINAL and it counts the `--to` flags the operator wrote.
    For a DISCOVERED one there is no typed list, and an ordinal into a sorted
    directory listing names nothing the operator has ever seen - so the refusal
    says the destination was discovered and names the one move that makes the
    fault locatable, which is to pass `--to` and read the ordinal off their own
    list.

    LIFTED OUT OF :func:`resolve_targets` BECAUSE IT NOW HAS TWO CALLERS and
    the two must not drift: a metadata refusal that numbered destinations
    differently from a containment refusal would send the operator to edit a
    name that was fine, which is the D2 fault this wording exists to fix.
    """
    if discovered:
        return (
            "a destination discovered by --all",
            "; re-run naming destinations with --to to identify it",
        )
    return "destination %d" % position, ""


def grade_names(labelled: Sequence[tuple[str, str]]) -> tuple[list[str], frozenset[int]]:
    """Grade metadata STRINGS - a filename, a destination name - as outbound text.

    CS-958 F1, and the reason this exists at all: a filename is outbound bytes.
    It is written into a sibling's tree, printed by that sibling's watcher,
    echoed on this tool's own stdout and stored in the delivery record forever.
    The gate refused the value in content and stamped the identical value CLEAN
    as a name, which is not a gap in the rule table - it is the rule table
    never being asked.

    SO IT IS THE SAME GATE THROUGH A DIFFERENT DOOR AND NOT A SECOND SCANNER.
    `gate.scan` already takes text, so a name is graded by the same rule table,
    the same exclusions and the same independent oracle as a payload. A second
    scanner here would be the CS-948 mistake in a new place: two implementations
    of one rule, free to drift, with the weaker one deciding.

    IT CONSUMES THE REFUSALS AND NOT THE COVERAGE ROWS, which is a decision and
    not an omission. Coverage says which classes could be derived ON THIS
    MACHINE at all; it is a property of the box, it is identical for every
    string graded in one run, and the payload's own grade has already reported
    it. Folding it in again would report one unmeasured class two or three
    times for a single note, and would let a filename turn a send UNMEASURED
    for a reason that has nothing to do with the filename. Warnings are left
    alone for the same reason the gate leaves them alone: a warning never
    changes a verdict.

    ONE SCAN FOR THE WHOLE BATCH, attributed by LINE. `Finding` carries a line
    number, so joining the values with newlines and reading the line back is
    the gate's own attribution rather than a per-value loop that would rebuild
    the matcher population once per destination. A value CARRYING a line break
    would destroy that attribution, so it is refused before the join rather
    than silently mis-attributed - and a name with a newline in it is not a
    project name on any platform.

    NO REFUSAL HERE ECHOES THE VALUE IT MATCHED. It names the label, the class
    and the gate's own reason. This function exists because outbound strings
    leak; a refusal that rendered what it refused would report the fault by
    committing a smaller version of it.
    """
    problems: list[str] = []
    refused: set[int] = set()
    scannable: list[tuple[int, str, str]] = []
    for index, (label, value) in enumerate(labelled, start=1):
        if "\n" in value or "\r" in value:
            problems.append("%s carries a line break and cannot be graded as one name" % label)
            refused.add(index)
            continue
        scannable.append((index, label, value))
    if not scannable:
        return problems, frozenset(refused)

    gate = load_outbound_gate()
    refusals, _warnings, _coverage = gate.scan(
        "\n".join(value for _index, _label, value in scannable)
    )
    by_line: dict[int, set[str]] = {}
    for finding in refusals:
        by_line.setdefault(finding.line, set()).add(finding.klass)
    for line, (index, label, _value) in enumerate(scannable, start=1):
        for klass in sorted(by_line.get(line, ())):
            reason = gate.CLASS_REASONS.get(klass, "a class the gate refuses")
            problems.append("%s carries <pii:%s> - %s" % (label, klass, _ascii(reason)))
            refused.add(index)
    return problems, frozenset(refused)


def is_plain_segment(name: str) -> bool:
    """A CHEAP FRONT CHECK ON THE SPELLING. It is NOT the containment guarantee.

    That distinction is the whole of CS-958 F3 and this docstring used to get it
    wrong. This function grades a STRING, and a string cannot tell you where a
    path goes: `NUL`, `CON`, `COM1`, an 8.3 short name, a fullwidth solidus and a
    trailing dot all pass the shape test, and a junction sitting at a perfectly
    ordinary name resolves clean out of the channel root. Measured: a junction
    made under a synthetic root with `mklink /J` was accepted here, followed
    through `is_dir()`, and the note was written outside the root with exit 0.
    What contains the send is :func:`resolve_targets` grading the RESOLVED path;
    everything below is a fast rejection of shapes that are obviously not a
    project name, kept because it is cheap and because it refuses before any
    filesystem call is made.

    The shape it does rule out matters on its own terms: a destination is joined
    onto the channel root, and `Path("/a") / "C:/b"` yields `C:/b` - so an
    absolute or separator-bearing name replaces the root outright. Measured:
    `--to` with a drive-qualified path resolved to this repository's own inbox
    and wrote an absolute path into the record.
    """
    if not name or name in {".", ".."} or name.startswith("."):
        return False
    if any(separator in name for separator in ("/", "\\", ":")):
        return False
    return len(Path(name).parts) == 1 and not Path(name).is_absolute()


def record_path() -> Path:
    """The delivery record's location, overridable for tests."""
    override = os.environ.get(ENV_RECORD)
    return Path(override) if override else DEFAULT_RECORD


def load_record(path: Path) -> list[dict[str, object]]:
    """Read the record, treating an unreadable one as EMPTY rather than fatal.

    A record this tool cannot parse must not block a send, but it must also
    never be silently overwritten - `append_record` writes the surviving
    entries plus the new ones, so a corrupt file costs the history it could not
    parse and nothing that follows it.
    """
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return loaded if isinstance(loaded, list) else []


def append_record(path: Path, entries: Sequence[dict[str, object]]) -> None:
    """Append entries to the record atomically (non-negotiable 5)."""
    existing = load_record(path)
    existing.extend(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8", newline="\n")
    try:
        tmp.replace(path)
    except OSError:
        # THE STAGING FILE IS REMOVED ON FAILURE. Measured: a record path
        # that could not be replaced left a `.tmp` beside it, so the next
        # run would find a stale staging file and no record at all - the
        # failure preserved in a shape nothing reads.
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise


def staging_name(destination: Path) -> Path:
    """The temporary file `destination` is staged through.

    In the SAME directory, because a replace across filesystems is not atomic
    and the destination is another repository's tree. A sibling's watcher keys
    on (name, content digest), so a half-written note would read as new mail
    carrying a truncated payload.
    """
    return destination.with_name(destination.name + ".tmp")


def stage_all(payload: bytes, targets: Sequence[tuple[str, Path]]) -> tuple[list[Path], str]:
    """Write every destination's temporary file. All or none.

    PHASE ONE OF TWO, and the phase where every plausible failure lives: no
    space, no permission, a path too long, a name already taken. Nothing has
    been delivered when it fails, so the staged files are unlinked and the send
    is refused with nothing on the channel - which is what the first version
    claimed to do and did not.
    """
    staged: list[Path] = []
    for _name, target in targets:
        tmp = staging_name(target)
        try:
            tmp.write_bytes(payload)
        except OSError as exc:
            for done in staged:
                with contextlib.suppress(OSError):
                    done.unlink()
            gate = None
            with contextlib.suppress(BaseException):
                gate = load_outbound_gate().load_precommit_gate()
            detail = gate.safe_exc_text(exc) if gate is not None else type(exc).__name__
            return [], detail
        staged.append(tmp)
    return staged, ""


def commit_all(targets: Sequence[tuple[str, Path]]) -> tuple[list[str], str]:
    """Rename every staged file into place, reporting what actually landed.

    PHASE TWO. A rename is per file and this is not a transaction, so a failure
    here CAN leave a subset delivered. The names that landed are returned rather
    than discarded, because the caller has to record them and has to tell the
    truth about them - a tool that says "nothing was sent" over a delivered note
    is worse than the partial send it is hiding.
    """
    landed: list[str] = []
    for name, target in targets:
        try:
            staging_name(target).replace(target)
        except OSError as exc:
            gate = None
            with contextlib.suppress(BaseException):
                gate = load_outbound_gate().load_precommit_gate()
            detail = gate.safe_exc_text(exc) if gate is not None else type(exc).__name__
            return landed, detail
        landed.append(name)
    return landed, ""


def _refuse(lines: Sequence[str]) -> int:
    """Report a refusal and send nothing."""
    body = "".join("  " + _ascii(line) + "\n" for line in lines)
    write_stream(sys.stderr, "%s: REFUSED\n%s%s: REFUSED.\n" % (TOOL, body, TOOL))
    return EXIT_REFUSED


def gate_phase(payload: bytes, note_name: str, *, allow_unmeasured: bool) -> tuple[int, int | None]:
    """Grade the note - its BYTES and its FILENAME - and decide whether to go on.

    Returns (the gate's verdict, an exit code to stop on or None). Lifted out of
    :func:`main` so the ordering this module turns on is a NAMED STEP rather
    than a fact about statement order that a later edit could quietly reverse -
    and so the refusal paths are readable next to each other instead of buried
    among the channel's own failures.

    THE FILENAME IS GRADED HERE BECAUSE HERE IS BEFORE EVERYTHING THAT PRINTS
    IT (CS-958 F1). The name reaches stdout in the DRY RUN and DELIVERED lines,
    reaches a refusal inside :func:`resolve_targets`, and reaches the record's
    `note` field. Measured on the unrepaired tool: a note whose filename was a
    well-formed credential delivered at exit 0 and was recorded `gate_verdict:
    CLEAN`, while the identical string in the note's CONTENT was refused. No
    destination has been touched at this point either, so the refusal cannot
    arrive alongside a channel fault the operator would have to fix first.

    A REFUSAL DOMINATES AN UNMEASURED CLASS, which is the gate's own precedence
    (`outbound_gate.verdict`: a finding first, then an unmeasured class, then
    clean). So the name is graded between the two payload branches rather than
    after them: a dirty filename refuses whether or not `--allow-unmeasured`
    was passed, and it refuses for its own reason rather than being reported as
    a coverage problem.

    THE RETURNED VERDICT STAYS THE PAYLOAD'S. It is what lands in the record as
    the gate verdict at the time of sending, and a metadata refusal never gets
    that far - there is no send to record.
    """
    code, gate_out, gate_err = grade(payload)
    write_stream(sys.stdout, gate_out)
    if code == EXIT_REFUSED:
        write_stream(sys.stderr, gate_err)
        return code, _refuse(["the gate refused this note; its findings are above"])
    name_problems, _refused = grade_names([(NOTE_LABEL, note_name)])
    if name_problems:
        return code, _refuse(name_problems)
    if code == EXIT_UNMEASURED and not allow_unmeasured:
        write_stream(
            sys.stderr,
            "%s: UNMEASURED - a class could not be derived here and was therefore not "
            "cleared. Nothing was sent. Pass --allow-unmeasured to send anyway.\n" % TOOL,
        )
        return code, EXIT_UNMEASURED
    return code, None


def perform_send(
    payload: bytes,
    note_name: str,
    targets: Sequence[tuple[str, Path]],
    verdict_name: str,
    delivered: list[str],
) -> int:
    """Stage every destination, commit them, record what landed, and report.

    `delivered` is the caller's own list and is appended to in place, so a
    failure raised anywhere after a rename is still visible to the handler that
    reports it. A tool that says nothing was sent over a delivered note is worse
    than the partial send it hides.
    """
    _staged, stage_error = stage_all(payload, targets)
    if stage_error:
        return _refuse(
            [
                "could not stage every destination: " + stage_error,
                "nothing was delivered; the staged files were removed",
            ]
        )

    landed_names, commit_error = commit_all(targets)
    delivered.extend(landed_names)

    # THE RECORD IS WRITTEN FOR WHAT LANDED, EVEN WHEN THE SEND WENT WRONG.
    # A delivery the record never learned about is exactly the CS-951 hole,
    # and a rename that failed halfway is when the record matters most.
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    digest = hashlib.sha256(payload).hexdigest()
    entries: list[dict[str, object]] = [
        {
            "sent_utc": stamp,
            "note": note_name,
            "destination": name,
            "sha256": digest,
            "bytes": len(payload),
            "gate_verdict": verdict_name,
        }
        for name in landed_names
    ]
    record_error = ""
    if entries:
        try:
            append_record(record_path(), entries)
        except OSError as exc:
            record_error = type(exc).__name__

    if commit_error:
        return _refuse(
            [
                "the send failed part way through: " + commit_error,
                "DELIVERED to %d of %d destination(s): %s"
                % (
                    len(landed_names),
                    len(targets),
                    _ascii(", ".join(landed_names)) or "none",
                ),
                "this is a PARTIAL delivery and the record says so",
            ]
        )
    if record_error:
        return _refuse(
            [
                "the notes were DELIVERED but the record could not be written: " + record_error,
                "delivered to: " + _ascii(", ".join(landed_names)),
                "record this by hand or the reconciler will not know",
            ]
        )
    write_stream(
        sys.stdout,
        "%s: DELIVERED %s to %d destination(s): %s [gate %s]\n"
        % (
            TOOL,
            _ascii(note_name),
            len(landed_names),
            _ascii(", ".join(landed_names)),
            verdict_name,
        ),
    )
    return EXIT_OK


def resolve_targets(
    root: Path, names: Sequence[str], note_name: str, *, discovered: bool = False
) -> tuple[list[tuple[str, Path]], list[str]]:
    """Turn destination names into targets, collecting every problem found.

    EVERY problem rather than the first, because a send that reports one fault
    per run costs an operator one round trip per destination, and the whole
    point of validating before staging is that the operator learns the full
    story while nothing has been written.

    THE STRING IS NOT GRADED. THE RESOLVED PATH IS. A destination is accepted
    only when `root / name / INBOX` RESOLVES to a directory whose grandparent is
    the resolved channel root and which is not this repository. One check, and
    it closes three separately measured holes at once:

      * a junction under the channel root pointing outside it was accepted by
        the shape check, followed by `is_dir()`, and delivered a note outside
        the root with exit 0 (F3). Its resolved grandparent is not the root, so
        it is refused now;
      * `--to <this repository's own name>` delivered into this repository's own
        inbox, because the self-exclusion lived in :func:`inbox_holders` and
        ONLY `--all` calls that (F2). The identity clause here covers the path
        an operator actually types, and it is compared against
        :data:`SELF_ROOT` - the repository, derived from `.git` - rather than
        against the directory this file happens to sit in. The first cut
        compared against the latter and was therefore false in a worktree,
        which is this project's default session shape (D3);
      * a trailing dot is stripped by Win32, so the note landed in the undotted
        directory while the record filed it under the dotted name - a name no
        destination has (F7). The name is now RE-DERIVED from the resolved
        directory, so the record cannot name a directory that does not exist.

    AND THE DEDUP IS THIS FUNCTION'S JOB AND KEYED ON THE RESOLVED PATH, for
    the same reason. The caller used to dedup with `dict.fromkeys` before
    calling, which dedups case-SENSITIVELY while Windows resolves
    case-INSENSITIVELY, so two spellings of one directory staged one temporary
    file twice; the first rename consumed it and the second raised, and a
    delivery that had completely succeeded was reported as PARTIAL and recorded
    that way (F7). Two spellings of one directory are one target, and there is
    now exactly one place that decides so.

    NO REFUSAL ADDED HERE ECHOES THE VALUE IT MATCHED, and the shape refusal
    stopped doing so. Measured on the unrepaired tool: a `--to` carrying a
    drive-qualified home path came back as `destination '<the whole path>' is
    not a plain project name`, so the one check whose job is to catch a name
    that is secretly a path was the one that printed the path. This tool exists
    because outbound bytes leak; a refusal that renders what it refused reports
    the fault by committing a smaller version of it.

    WHAT THE REFUSAL SAYS INSTEAD, and the docstring claims only what was
    measured. For a TYPED destination it is an ORDINAL, and the ordinal counts
    the `--to` flags the operator wrote. That is a repair too: the caller's
    deduplication ran BEFORE this enumeration, so a repeated spelling shifted
    every later position left, and a fault at the fifth typed name was measured
    reporting as `destination 3` (D2). An ordinal pointing at the wrong name is
    worse than none, because the operator edits a name that was fine.

    For a DISCOVERED destination - `--all` - there is no typed list, and an
    ordinal into a sorted directory listing names nothing the operator has ever
    seen. So the refusal says the destination was discovered and names the one
    move that makes the fault locatable, which is to pass `--to` explicitly and
    read the ordinal off their own list. `discovered` is the caller's statement
    about where the names came from; it changes no decision, only the wording.
    """
    resolved_root = root.resolve()
    targets: list[tuple[str, Path]] = []
    # EVERY NAME IS GRADED BEFORE THE LOOP BELOW CAN PUT ONE IN A MESSAGE.
    # `destination %s has no %s directory` echoes the typed spelling, and a
    # typed spelling is operator input that reaches this project's stdout
    # (CS-958 F1, and D6). Grading the whole list in one scan rather than
    # per-destination rebuilds the gate's matcher population once instead of
    # once per name.
    problems, refused = grade_names(
        [(_which(position, discovered)[0], name) for position, name in enumerate(names, start=1)]
    )
    # The label and the resolved name of every destination this loop accepts,
    # graded together after it. THE NAME THE TOOL PRINTS AND RECORDS IS THE
    # RESOLVED DIRECTORY'S OWN, not the spelling that was typed, so grading the
    # typed list alone would grade a string the tool then discards.
    resolved_names: list[tuple[str, str]] = []
    # Resolved inbox -> the position that already claimed it, so a second
    # spelling of one directory collapses rather than staging it twice.
    claimed: dict[Path, int] = {}
    for position, name in enumerate(names, start=1):
        # WHICH DESTINATION, said in the only terms the operator can act on.
        # An ordinal is meaningful when they typed the list; when `--all`
        # discovered it, the actionable thing is the way to get an ordinal.
        if position in refused:
            # ALREADY REFUSED BY THE GRADE ABOVE, AND EXAMINING IT FURTHER IS
            # WHAT LEAKS IT. The send is refused whatever the rest of this
            # loop would find, and every remaining message about THIS name
            # renders the spelling that was typed - `destination <name> has
            # no moon_sync_inbox directory` first among them. Measured: with
            # the grade in place but the name still walked, the refused value
            # reached stderr through exactly that line.
            continue
        which, locate = _which(position, discovered)
        if not is_plain_segment(name):
            problems.append("%s is not a plain project name%s" % (which, locate))
            continue
        try:
            inbox = (root / name / INBOX).resolve()
        except OSError:
            # A name the operating system will not even resolve is refused
            # rather than raised on, so one bad destination reports alongside
            # the others instead of ending the run at the first fault.
            problems.append("%s could not be resolved%s" % (which, locate))
            continue
        if not inbox.is_dir():
            problems.append("destination %s has no %s directory" % (_ascii(name), INBOX))
            continue
        project = inbox.parent
        if project.parent != resolved_root or project == SELF_ROOT:
            problems.append(
                "%s does not resolve to a project directly inside the "
                "channel root, or resolves to this repository itself%s" % (which, locate)
            )
            continue
        if inbox in claimed:
            continue
        claimed[inbox] = position
        # THE NAME IS THE RESOLVED DIRECTORY'S OWN, not the spelling that was
        # typed. The record must name a directory that exists.
        real_name = project.name
        resolved_names.append((which, real_name))
        target = inbox / note_name
        if target.exists():
            # NEITHER OF THE TWO MESSAGES BELOW RENDERS THE DESTINATION'S NAME,
            # and that is the F1 repair rather than a style choice. This name
            # is the RESOLVED directory's, read off the operator's real sibling
            # tree, and it reaches this line before the grade below has run on
            # it. The ordinal locates the destination without echoing it; the
            # note name is graded in `main` before this function is called.
            problems.append(
                "%s already holds a note named %s%s" % (which, _ascii(note_name), locate)
            )
            continue
        if staging_name(target).exists():
            # THE VALIDATION MUST COVER THE NAME THE WRITER ACTUALLY USES. The
            # first version checked only the final name, so a directory at the
            # staging name made the write raise AFTER earlier destinations had
            # already been delivered - a partial send reported as no send.
            problems.append(
                "%s already holds a staging file for %s%s" % (which, _ascii(note_name), locate)
            )
            continue
        targets.append((real_name, target))
    # THE RESOLVED NAMES ARE GRADED BEFORE THE CALLER CAN PRINT OR RECORD ONE.
    # This is the value that reaches the DRY RUN line, the DELIVERED line and
    # the record's `destination` field, and a link at an ordinary name pointing
    # at a directory the gate refuses passes every containment check in this
    # function - its grandparent IS the channel root.
    resolved_problems, _resolved_refused = grade_names(resolved_names)
    problems.extend(resolved_problems)
    return targets, problems


def main(argv: Sequence[str] | None = None) -> int:
    """Grade a note, then deliver it, or explain why it was not delivered."""
    parser = QuietParser(
        prog=TOOL,
        description="Deliver a note to sibling project inboxes, gated and recorded.",
    )
    parser.add_argument("--note", required=True, help="the note file to deliver")
    parser.add_argument("--to", action="append", default=[], help="destination project name")
    parser.add_argument("--all", action="store_true", help="every sibling that has an inbox")
    parser.add_argument("--send", action="store_true", help="actually write; default is a dry run")
    parser.add_argument(
        "--allow-unmeasured",
        action="store_true",
        help="proceed when the gate could not derive every class",
    )
    parser.add_argument("--channel-root", default=None, help="where sibling projects live")
    args = parser.parse_args(argv)

    # Visible to the handler below, so a failure AFTER a delivery cannot report
    # that nothing was sent. Measured: it did.
    delivered: list[str] = []
    try:
        note = Path(args.note)

        # THE GATE FIRST. Nothing about the channel has been touched yet, so a
        # refusal here cannot be reported alongside - or after - a fault the
        # operator would have to fix before seeing it.
        payload = note.read_bytes()
        code, stop = gate_phase(payload, note.name, allow_unmeasured=args.allow_unmeasured)
        if stop is not None:
            return stop

        root = channel_root(args.channel_root)
        # THE TYPED LIST REACHES THE RESOLVER INTACT, duplicates and all. It
        # used to be deduplicated here with `dict.fromkeys`, which did two
        # things wrong at once: it deduplicated by SPELLING, so two spellings
        # of one directory survived as two destinations and staged one
        # temporary file twice (F7); and it shortened the list the resolver
        # then enumerated, so every refusal after a repeat reported an ordinal
        # into a list the operator never typed - measured, a fault at the fifth
        # name reported as `destination 3` (D2). Deduplication now happens once,
        # in `resolve_targets`, keyed on the resolved inbox.
        names = inbox_holders(root) if args.all else list(args.to)
        if not names:
            return _refuse(["no destination was named and none was discovered"])

        targets, problems = resolve_targets(root, names, note.name, discovered=args.all)
        if problems:
            return _refuse(problems)

        verdict_name = VERDICT_NAME.get(code, str(code))
        if not args.send:
            write_stream(
                sys.stdout,
                "%s: DRY RUN - would deliver %s to %d destination(s): %s\n"
                "%s: nothing was written. Pass --send to deliver.\n"
                % (
                    TOOL,
                    _ascii(note.name),
                    len(targets),
                    _ascii(", ".join(name for name, _ in targets)),
                    TOOL,
                ),
            )
            return EXIT_OK

        return perform_send(payload, note.name, targets, verdict_name, delivered)

    except BaseException as exc:
        # FAIL CLOSED, AND CATCH BaseException. Every failure leaves the send in
        # an unknown state, and an unknown state must never read as a success. A
        # bare `Exception` would let a SystemExit raised inside the loaded gate
        # escape and print an interpreter traceback, which renders this file's
        # absolute path per frame - personal data wherever the tool runs from a
        # home-rooted checkout, which is the deployment it is written for.
        if isinstance(exc, KeyboardInterrupt):
            raise
        try:
            detail = load_outbound_gate().load_precommit_gate().safe_exc_text(exc)
        except BaseException:  # the renderer is best-effort
            detail = type(exc).__name__
        lines = [_ascii(detail)]
        if delivered:
            lines.append("NOTE ALREADY DELIVERED to: " + _ascii(", ".join(delivered)))
        return _refuse(lines)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(EXIT_REFUSED) from None
