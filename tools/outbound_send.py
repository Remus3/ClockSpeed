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

ANY FAULT REFUSES THE WHOLE SEND, NEVER A SUBSET. A missing destination, or a
filename already present at any one of them, aborts everything. A partial
delivery leaves a partial record, and a partial record is precisely the CS-951
hole with extra steps - the reconciler's question is "does the copy this
repository believes it put there still exist", and it cannot be answered for a
destination the record never learned about.

UNMEASURED IS NOT CLEARED. A class the gate could not derive is a class nobody
looked at, so the default is to refuse and `--allow-unmeasured` is an explicit
operator act that lands in the record as the verdict at the time of sending.
A reader of that record can then tell a delivery that was fully graded from one
that was not, which a boolean "sent" flag could never express.

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

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTBOUND_GATE = REPO_ROOT / "tools" / "outbound_gate.py"

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


def grade(note: Path) -> tuple[int, str, str]:
    """Run the gate over `note`, returning (code, its stdout, its stderr).

    In process rather than as a subprocess, so the sender and the gate cannot
    drift into two different answers about the same bytes, and so no payload
    ever reaches an argument vector.
    """
    gate = load_outbound_gate()
    text = note.read_bytes().decode("utf-8")
    refusals, warnings, coverage = gate.scan(text)
    out, err = gate.render(refusals, warnings, coverage)
    return gate.verdict(refusals, coverage), out, err


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
    tmp.replace(path)


def deliver(source: Path, destination: Path) -> None:
    """Write `source`'s bytes into `destination` atomically.

    Through a temporary file in the SAME directory, because a replace across
    filesystems is not atomic and the destination is another repository's tree.
    A sibling's watcher keys on (name, content digest), so a half-written note
    would read as new mail carrying a truncated payload.
    """
    tmp = destination.with_name(destination.name + ".tmp")
    tmp.write_bytes(source.read_bytes())
    tmp.replace(destination)


def _refuse(lines: Sequence[str]) -> int:
    """Report a refusal and send nothing."""
    body = "".join("  " + _ascii(line) + "\n" for line in lines)
    write_stream(
        sys.stderr,
        "%s: REFUSED\n%s%s: REFUSED - nothing was sent.\n" % (TOOL, body, TOOL),
    )
    return EXIT_REFUSED


def gate_phase(note: Path, *, allow_unmeasured: bool) -> tuple[int, int | None]:
    """Grade the note and decide whether the send may continue.

    Returns (the gate's verdict, an exit code to stop on or None). Lifted out of
    :func:`main` so the ordering this module turns on is a NAMED STEP rather
    than a fact about statement order that a later edit could quietly reverse -
    and so the refusal paths are readable next to each other instead of buried
    among the channel's own failures.
    """
    code, gate_out, gate_err = grade(note)
    write_stream(sys.stdout, gate_out)
    if code == EXIT_REFUSED:
        write_stream(sys.stderr, gate_err)
        return code, _refuse(["the gate refused this note; its findings are above"])
    if code == EXIT_UNMEASURED and not allow_unmeasured:
        write_stream(
            sys.stderr,
            "%s: UNMEASURED - a class could not be derived here and was therefore not "
            "cleared. Nothing was sent. Pass --allow-unmeasured to send anyway.\n" % TOOL,
        )
        return code, EXIT_UNMEASURED
    return code, None


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

    try:
        note = Path(args.note)

        # THE GATE FIRST. Nothing about the channel has been touched yet, so a
        # refusal here cannot be reported alongside - or after - a fault the
        # operator would have to fix before seeing it.
        code, stop = gate_phase(note, allow_unmeasured=args.allow_unmeasured)
        if stop is not None:
            return stop

        root = channel_root(args.channel_root)
        names = inbox_holders(root) if args.all else list(dict.fromkeys(args.to))
        if not names:
            return _refuse(["no destination was named and none was discovered"])

        targets = []
        problems = []
        for name in names:
            inbox = root / name / INBOX
            if not inbox.is_dir():
                problems.append("destination %s has no %s directory" % (_ascii(name), INBOX))
                continue
            target = inbox / note.name
            if target.exists():
                problems.append(
                    "destination %s already holds a note named %s"
                    % (_ascii(name), _ascii(note.name))
                )
                continue
            targets.append((name, target))
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

        stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        entries: list[dict[str, object]] = []
        for name, target in targets:
            deliver(note, target)
            landed = target.read_bytes()
            entries.append(
                {
                    "sent_utc": stamp,
                    "note": note.name,
                    "destination": name,
                    "sha256": hashlib.sha256(landed).hexdigest(),
                    "bytes": len(landed),
                    "gate_verdict": verdict_name,
                }
            )
        append_record(record_path(), entries)
        write_stream(
            sys.stdout,
            "%s: DELIVERED %s to %d destination(s): %s [gate %s]\n"
            % (
                TOOL,
                _ascii(note.name),
                len(entries),
                _ascii(", ".join(name for name, _ in targets)),
                verdict_name,
            ),
        )
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
        return _refuse([_ascii(detail)])
    return EXIT_OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(EXIT_REFUSED) from None
