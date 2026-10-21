#!/usr/bin/env python3
"""CS-1183 - the seven tier-3 flip checks, the trailer and identity axes, against ONE ref.

RUN BY HAND, ON THIS MACHINE, AND NOWHERE ELSE - ADR 0025 in ``docs/adr/``
records why. No workflow, hook, scheduled task or lane invokes this file, and
``tests/test_flip_checks.py`` pins that none names it. The check-2 needles are
derived from this machine's save header and account directory, which a CI
runner does not have; uploading them as repository secrets would move exactly
the personal data this check guards onto the forge.

THE CLI CONTRACT:

    python tools/flip_checks.py REF --stage {s1,s8} [--repo DIR]
        [--trailer-baseline-ref BASE --trailer-baseline-count N]

    REF is resolved ONCE to a full commit SHA, printed first. Every population
    below is that SHA's tree and its reachable history - never the working tree,
    the index, or another ref. ``--stage`` selects the trailer axis's rule: the
    CS-700 plan runs this at S1, before S7a strips the trailers, and at S8, after.

    exit 0   every automated half passed, every positive control was found and
             no automated half skipped anything
    exit 1   any check failed, any control was not found, anything skipped, or
             the scratch directory could not be removed
    exit 2   the run could not run at all - no git, not a repository, an
             unresolvable REF, a half-given baseline, a refusal under CI, or
             any exception no check absorbed (a child that would not die)
    exit 130 the operator interrupted it

    NO TRACEBACK EVER RENDERS. The last-resort handler in :func:`main` prints a
    fixed line naming the phase (``check N`` and the like) and the exception's
    TYPE only, because a traceback's frames carry the interpreter's install
    path and an exception's text can carry a child's argv or stderr.

    THE FINAL LINE IS NEVER A BARE PASS. It states the automated verdict, the
    number of human halves NOT-RUN-HERE, and that this run does not clear CS-G03.
    CS-G03 clears only on an adjudicated ``docs/LEDGER.md`` record at the flip SHA
    (ADR 0025 decision item 8); an exit of 0 is evidence for that record, never
    the record.

OUTPUT IS COUNTS, COMMIT SHAS AND BLOB SHAS ONLY. No path, no message byte, no
package name, no needle. A child tool's own output is parsed for its counts and
never relayed, because it prints paths and names this contract does not.

THE CHECKS, each with a positive control in its OWN command family - a planted
hit in a throwaway repository or tree in the scratch directory, found by the
same function that grades the named ref:

  1. SECRETS over every blob and every commit message reachable from REF, with
     the tier-0 gate's own ``check_secrets``, reached through the sweep engine in
     ``tests/secret_sweep_guard.py``. A blob the gate's admission rule declines is
     scanned RAW rather than skipped, so no member of the population goes unread.
  2. PII over blob content, every path any reachable tree ever held, and every
     raw commit object. Needles are derived IN-PROCESS by :func:`derive_needles`
     - see NEEDLES below.
  3. LICENCES - ``tools/licence_audit.py`` over the REF tree. A dependency the
     audit could not walk is counted as a skip.
  4. PUBLISHER-OWNED ASSETS - every path any reachable tree ever held, graded by
     the gate's own ``check_path`` PUBLISHER rule.
  5. README - the automatable half: README's own command lines run in a scratch
     clone of REF, with the game, save, account and local-config overrides
     aimed at NONEXISTENT relative paths and the dashboard port at a free one.
     That is an APPROXIMATION outside README, not a README step. A command
     passes by exiting 0 or by binding the port; one still running at its bound
     that never bound FAILS. The human half is NOT-RUN-HERE - CS-1186's no-game
     walk. Its standing was cleared when CS-G03 closed, by the CS-G03 record in
     ``docs/LEDGER.md``, and is never restated here; a fresh walk is CS-1334.
  6. DOC SWEEP - ``tools/doc_sweep.py``'s own sweep with URLs fetched, run
     in-process over the REF tree, under ADR 0025 point 10: one exact URL pin,
     matched by URL and reported by its own count, the pre-publication pin
     deleted after S12 as point 10b orders - see :func:`doc_sweep`. A file the
     sweep could not read is excused only by a path-and-SHA-256 pin (CS-1332).
  7. CLEAN CHECKOUT - the automatable half: a fresh clone of REF, the bootstrap
     block of ``docs/OPERATIONS.md``, and a staged non-ASCII violation that must
     leave HEAD unmoved. Its control commits the same violation with no hook
     and must see HEAD move. The human half - a machine that has never seen the
     project - is NOT-RUN-HERE, CS-1187's walk, its standing cleared the same
     way by the CS-G03 record; a fresh walk is CS-1334.
  T. THE TRAILER AXIS (CS-1180) through ``tools/trailer_census.py``. At S1 a hit
     is an EARLY WARNING and the axis fails on zero hits or on any hit S7a's
     strip would leave behind; at S8 any hit fails, and the pre-S7a baseline ref
     and its recorded count are required as the axis's second control - absent,
     they are a skip.
  I. THE IDENTITY AXIS (CS-701, CS-700 S8). Every author and committer name and
     address on every commit reachable from REF, read from the RAW commit object
     - never a ``git log`` format, which a mailmap can rewrite - must be on an
     allowlist DERIVED AT RUN TIME: exactly one name, ``git config user.name`` of
     the repository, and exactly one address, the forge noreply address built from
     ``gh api user``'s id and login. Neither value is written to disk, printed or
     raised, and :class:`IdentityAllowlist` withholds both from ``repr``. A source
     that does not resolve FAILS the axis, as does an empty walk. At S1, before
     S7a maps identity, a field off the allowlist is an EARLY WARNING, counted and
     not failed; at S8 one is a failure. The control is a negative probe: a
     synthetic commit under the control identity must be flagged.

NEEDLES (ADR 0025 decision item 3). Derived at run time from
``clockspeed/data/locate.py`` - the account directory names, the Windows account
name, the machine name, every home-path rendering - and from
``clockspeed/save/header.py::reveal_strings`` with its explicit opt-in, used at
the one render site :func:`_add_header_needles`: every length-prefixed string
decoded out of a hex-valued options field (the display name and the identity
strings live there) plus the session name. A needle is never written to disk,
never printed, never raised in an exception, and never placed by this tool in a
child's argv or environment. Matching is in-process over ``git cat-file
--batch`` output. :class:`NeedleSet` and :class:`Matcher` withhold every value
from ``repr``.

WHAT A CHILD STILL CARRIES, stated rather than implied (ADR 0025 decision item
3): no NEEDLE ever enters a child's argv or environment. A child's argv[0] may
carry the interpreter's own path, which on this machine sits under a home
directory, and the child inherits the environment the operator handed this
process unchanged; the tool never renders an argv, a child's output or a child's
stderr. Every path this tool BUILDS is relative - save where two Windows drives
leave no relative spelling, when it is drive-anchored and refused if it would
render a home directory (CS-1230) - and the scratch directory lives
inside the repository's git directory, never under the temp directory, whose 8.3
short form carries the account name.

A NEEDLE SOURCE THAT DOES NOT RESOLVE FAILS CHECK 2, never a skip - a PII scan
with no needles is vacuous (decision item 4). A needle dropped as too short to
match safely, a save that could not be read, and a needle the in-memory
self-match control cannot find are each COUNTED AS A SKIP, and any skip fails
the run.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Final

# `tools` carries no __init__.py, so siblings are imported under their BARE
# names, the way tools/doc_sweep.py does it; the repository root goes on the path
# so the clockspeed layer can be imported, which docs/ARCHITECTURE.md permits
# tools/ to do.
_TOOLS_DIR: Final = Path(__file__).resolve().parent
REPO_ROOT: Final = _TOOLS_DIR.parent
for _entry in (str(_TOOLS_DIR), str(REPO_ROOT)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import trailer_census  # noqa: E402
from toolpath import resolve_tool  # noqa: E402

from clockspeed.data import locate  # noqa: E402
from clockspeed.save import header  # noqa: E402

EXIT_PASS: Final = 0
EXIT_FAIL: Final = 1
EXIT_COULD_NOT_RUN: Final = 2

#: The conventional status for a run the operator interrupted with Ctrl-C.
EXIT_INTERRUPTED: Final = 130

#: What the run is doing now, as fixed text - ``setup``, ``check N`` or
#: ``report``. Read only by :func:`main`'s last-resort handler,
#: which names it and the exception TYPE and nothing else.
PHASE: list[str] = ["setup"]

STAGE_S1: Final = "s1"
STAGE_S8: Final = "s8"

#: The human halves this tool never runs: the item that walked each, the gate whose
#: closing record in ``docs/LEDGER.md`` cleared its standing - pointed at, never
#: restated - and the open item that owns a fresh walk.
HUMAN_HALVES: Final = (
    ("5", "CS-1186; standing cleared by CS-G03; a fresh walk is CS-1334"),
    ("7", "CS-1187; standing cleared by CS-G03; a fresh walk is CS-1334"),
)

#: Seconds one git call may take. The object walk reads every reachable object.
GIT_TIMEOUT: Final = 600

#: Seconds one child tool - the licence audit, the doc sweep, a bootstrap step,
#: a commit through the hooks - may take.
CHILD_TIMEOUT: Final = 600

#: Seconds a README command may run before it must have exited 0 or bound its
#: port. A command still running at this point that never bound is a failure.
README_COMMAND_TIMEOUT: Final = 180

#: The bound the README control's own hang is held to - the control proves the
#: rule, so it need not wait out the full bound the real walk grants.
CONTROL_COMMAND_TIMEOUT: Final = 10

#: Seconds between polls of a running README command.
POLL_SECONDS: Final = 0.25

#: How many times, and how far apart, a scratch removal is attempted.
REMOVE_ATTEMPTS: Final = 5
REMOVE_PAUSE_SECONDS: Final = 0.5

#: Seconds one TCP connect probe may take.
CONNECT_TIMEOUT: Final = 0.5

#: Fields in a ``git cat-file --batch`` header: object, type and size.
BATCH_HEADER_FIELDS: Final = 3

#: Fields in one ``git rev-list --objects`` line that names a path.
WALK_NAMED_FIELDS: Final = 2

#: Header-decoded strings the SPEC names as non-personal constants
#: (``BOOTSTRAP.md`` section 2.2: decoding a real header yields the platform
#: name, ``None``, an account id blob and the display name). They are not
#: needles, because they are not personal data; compared case-folded.
NON_PERSONAL_HEADER_STRINGS: Final = frozenset({"steam", "none"})

#: The longest length-prefixed string the options decoder accepts, in
#: characters. Far above any display name or identity string.
MAX_DECODED_STRING: Final = 256

#: A length prefix is a little-endian int32.
LENGTH_PREFIX_BYTES: Final = 4

#: Printable ASCII, the only bytes a decoded narrow string may carry.
PRINTABLE_LOW: Final = 0x20
PRINTABLE_HIGH: Final = 0x7E

#: The word boundary the gate's own whole-word matchers use, in bytes.
_BOUNDARY_BEFORE: Final = rb"(?<![A-Za-z0-9_-])"
_BOUNDARY_AFTER: Final = rb"(?![A-Za-z0-9_-])"

#: Needle kinds whose values are paths, matched with either slash.
PATH_KINDS: Final = frozenset({"home-path"})

#: The redaction tokens ``clockspeed/data/locate.py`` pairs its needles with,
#: mapped to the kind a count is reported under. Every other token is a path.
_TOKEN_KINDS: Final = {"<user>": "account-name", "<machine>": "machine-name"}

#: The dashboard port override (``clockspeed/surface/config.py::PORT_ENV``).
PORT_ENV: Final = "CLOCKSPEED_DASHBOARD_PORT"

#: ADR 0025 point 10a. PERMANENT: CS-485 forbids any automated fetch of this host.
NO_FETCH_PINNED: Final = frozenset(
    {"https://satisfactory.wiki.gg/wiki/Satisfactory_Wiki:Copyrights"}
)

#: The name of doc_sweep's own no-fetch predicate, which check 6 wraps for the run
#: of one in-process sweep to learn each skipped URL by identity, then restores.
NO_FETCH_PREDICATE: Final = "_no_fetch"

#: CS-1332 - the name of doc_sweep's own reader, wrapped the same way to learn each
#: file the sweep could not read by identity, then restored.
READ_TEXT_HOOK: Final = "_read_text"

#: The floor of an HTTP error status: a URL answering at or above it is dead.
HTTP_ERROR: Final = 400

#: Seconds the forge account read (``gh api user``) may take.
PROBE_TIMEOUT: Final = 20

#: The prefix every project override carries. A walk scrubs them all from the
#: child environment first, because an outsider's machine has none of them.
PROJECT_ENV_PREFIX: Final = "CLOCKSPEED_"

#: Where every scratch tree lives: inside the repository's git directory.
SCRATCH_DIRNAME: Final = "flip-checks"

#: The relative, nonexistent directory a README walk aims its overrides at.
ABSENT_DIRNAME: Final = "flip-absent"

#: A hooks path that names no directory, so a control commit runs no hook.
NO_HOOKS: Final = ".flip-no-hooks"

#: The one file a clean-checkout probe stages.
PROBE_FILE: Final = "flip_probe.txt"

#: What the README control plants: one command that fails and one that hangs.
CONTROL_README_COMMANDS: Final = 2

#: README and OPERATIONS command lines this tool will run: the interpreter on a
#: repository script, or on a module. Anything else in a command block is
#: counted as unrunnable, never run.
_RUNNABLE_RE: Final = re.compile(r"^python (?:-m [A-Za-z0-9_.]+|[A-Za-z0-9_./-]+\.py)(?: .*)?$")

#: A fenced code block in markdown.
_FENCE_RE: Final = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)

#: The level-2 heading that owns the fresh-clone bootstrap in docs/OPERATIONS.md.
BOOTSTRAP_HEADING_RE: Final = re.compile(r"^## .*bootstrap", re.IGNORECASE | re.MULTILINE)

#: The synthetic identity every probe commit is written under.
_PROBE_IDENTITY: Final = (
    "-c",
    "user.name=flip-check",
    "-c",
    "user.email=flip-check@example.invalid",
)

SECRET_SWEEP_PATH: Final = REPO_ROOT / "tests" / "secret_sweep_guard.py"
DOC_SWEEP_PATH: Final = _TOOLS_DIR / "doc_sweep.py"
CITATION_GATE_PATH: Final = _TOOLS_DIR / "sha_citation_gate.py"
LICENCE_AUDIT_PATH: Final = _TOOLS_DIR / "licence_audit.py"


class FlipError(Exception):
    """A step could not be taken. The reason is fixed text - never a path or a value."""

    def __init__(self, reason: str) -> None:
        """Keep ``reason`` as the one field the CLI prints."""
        super().__init__(reason)
        self.reason = reason


# --- results ------------------------------------------------------------------


@dataclass
class CheckResult:
    """What one check measured. Counts, SHAs and fixed-text reasons only.

    Attributes:
        key: The check's number, or ``T`` for the trailer axis.
        title: A short fixed name.
        counts: Named population and finding counts.
        shas: Commit or blob SHAs the findings sit in.
        skips: Members of the population the check did not measure.
        control: Whether the positive control was found.
        failures: Fixed-text reasons the check failed, never a value.
    """

    key: str
    title: str
    counts: dict[str, int] = field(default_factory=dict)
    shas: list[str] = field(default_factory=list)
    skips: int = 0
    control: bool = False
    failures: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True only when the control was found, nothing skipped and nothing failed."""
        return self.control and self.skips == 0 and not self.failures

    def render(self) -> list[str]:
        """The lines this check prints."""
        counts = "; ".join(f"{name} {value}" for name, value in self.counts.items())
        verdict = "PASS" if self.passed else "FAIL"
        control = "FOUND" if self.control else "NOT FOUND"
        lines = [
            f"check {self.key} {self.title}: {counts}; skips {self.skips}; "
            f"control {control}; {verdict}"
        ]
        lines.extend(f"  sha {sha}" for sha in sorted(set(self.shas)))
        lines.extend(f"  reason: {reason}" for reason in self.failures)
        return lines


# --- git ----------------------------------------------------------------------


def _git_path() -> str:
    """The absolute path to git, resolved from PATH only (``tools/toolpath.py``)."""
    found = resolve_tool("git")
    if found is None:
        raise FlipError("git is not on PATH")
    return found


def raw_object_env() -> dict[str, str]:
    """This environment with replace objects OFF, for every git call that reads history.

    A ``refs/replace/`` ref swaps one object for another in every read that
    honours it, so a commit off the allowlist, or a blob carrying a credential,
    could be hidden from a walk that followed it. With replace objects off the
    walk and the read see the RAW objects in the store (CS-701 adversary).
    Grafts and a shallow file are not switched off by this; they are refused by
    :func:`refuse_cut_history`.
    """
    env = dict(os.environ)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    return env


def git(
    repo: Path,
    args: Sequence[str],
    data: bytes | None = None,
    env: dict[str, str] | None = None,
) -> bytes:
    """Run one git command in ``repo`` and return its stdout.

    Args:
        repo: The directory to run in.
        args: The subcommand and its arguments, without git itself.
        data: Bytes for stdin, if any.
        env: The child environment, or None for this one with replace objects
            off (:func:`raw_object_env`).

    Returns:
        Raw stdout.

    Raises:
        FlipError: When git cannot be run, times out or exits non-zero. The
            reason names the subcommand only.
    """
    try:
        completed = subprocess.run(
            [_git_path(), *args],
            cwd=repo,
            input=data,
            env=raw_object_env() if env is None else env,
            capture_output=True,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FlipError(f"git {args[0]} could not be run: {type(exc).__name__}") from None
    if completed.returncode != 0:
        raise FlipError(f"git {args[0]} exited {completed.returncode}")
    return completed.stdout


def resolve_ref(repo: Path, ref: str) -> str:
    """Resolve ``ref`` to one full commit SHA.

    Args:
        repo: The repository.
        ref: A ref, a SHA or any single revision expression.

    Returns:
        The full SHA.

    Raises:
        FlipError: When the ref is empty, option shaped, or names no commit.
    """
    if not ref or ref.startswith("-"):
        raise FlipError("REF must be a revision, not empty and not an option")
    out = git(repo, ["rev-parse", "--verify", "--quiet", "--end-of-options", f"{ref}^{{commit}}"])
    sha = out.decode("ascii", errors="replace").strip()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
        raise FlipError("REF did not resolve to one commit")
    return sha


def refuse_cut_history(repo: Path) -> None:
    """Refuse a repository whose history is cut by a shallow file or by grafts.

    Either one ends the walk early, so every commit behind the cut - and every
    object only it reaches - is hidden from a scan that would otherwise report
    PASS over it. A cut history is refused by name, never walked.

    Raises:
        FlipError: Naming which of the two cuts was found.
    """
    shallow = git(repo, ["rev-parse", "--is-shallow-repository"]).strip()
    if shallow != b"false":
        raise FlipError("the repository is shallow")
    grafts = git(repo, ["rev-parse", "--git-path", "info/grafts"]).decode("utf-8", "replace")
    if (repo / grafts.strip()).exists():
        raise FlipError("the repository has grafts")


def reachable_objects(repo: Path, sha: str) -> list[tuple[str, str]]:
    """Every object reachable from ``sha``, with the path git first named it at.

    Args:
        repo: The repository.
        sha: The commit.

    Returns:
        ``(object, path)`` pairs; the path is empty for a commit.
    """
    walked = git(repo, ["rev-list", "--objects", sha]).decode("utf-8", errors="replace")
    pairs: list[tuple[str, str]] = []
    for line in walked.splitlines():
        fields = line.split(None, 1)
        if fields:
            path = fields[1].strip() if len(fields) == WALK_NAMED_FIELDS else ""
            pairs.append((fields[0], path))
    return pairs


def object_types(repo: Path, shas: Sequence[str]) -> dict[str, str]:
    """The type of each named object, in one ``--batch-check`` call."""
    if not shas:
        return {}
    out = git(
        repo,
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"],
        ("\n".join(shas) + "\n").encode("ascii"),
    )
    typed: dict[str, str] = {}
    for line in out.decode("ascii", errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= WALK_NAMED_FIELDS:
            typed[parts[0]] = parts[1]
    return typed


def population(repo: Path, sha: str) -> tuple[dict[str, str], list[str], list[str]]:
    """REF's reachable objects: each object's first path, its blobs and its commits."""
    refuse_cut_history(repo)
    named = dict(reachable_objects(repo, sha))
    types = object_types(repo, list(named))
    blobs = [obj for obj in named if types.get(obj) == "blob"]
    commits = [obj for obj in named if types.get(obj) == "commit"]
    return named, blobs, commits


def stream_objects(repo: Path, shas: Sequence[str]) -> Iterator[tuple[str, bytes]]:
    """Stream each object's bytes out of the store, one process for all.

    One sha is written and its answer read before the next is written, so the
    pipes never fill and the whole population is never held in memory at once.

    Args:
        repo: The repository.
        shas: Object names.

    Yields:
        ``(sha, bytes)`` in the order asked for.

    Raises:
        FlipError: When git cannot be started, or answers with a header this
            reader cannot parse - which would desynchronise every later read.
    """
    if not shas:
        return
    try:
        proc = subprocess.Popen(
            [_git_path(), "cat-file", "--batch"],
            cwd=repo,
            env=raw_object_env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise FlipError(f"git cat-file could not be run: {type(exc).__name__}") from None
    try:
        if proc.stdin is None or proc.stdout is None:
            raise FlipError("git cat-file was started without its pipes")
        for sha in shas:
            proc.stdin.write(f"{sha}\n".encode("ascii"))
            proc.stdin.flush()
            fields = proc.stdout.readline().decode("ascii", errors="replace").split()
            if len(fields) != BATCH_HEADER_FIELDS or fields[0] != sha:
                raise FlipError("git cat-file answered an unexpected header")
            data = proc.stdout.read(int(fields[2]))
            proc.stdout.read(1)
            yield sha, data
    finally:
        if proc.stdin is not None:
            proc.stdin.close()
        try:
            proc.wait(timeout=GIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=GIT_TIMEOUT)


def history_paths(repo: Path, sha: str) -> dict[str, str]:
    """Every path any tree reachable from ``sha`` ever held, with a commit that held it.

    Every path in a reachable tree was added or modified by SOME reachable
    commit relative to one of its parents, or sits in a root commit's tree, so
    the union of those diffs - merges diffed against each parent, renames split
    into their add - is the whole set. ``git rev-list --objects`` is not: it
    names each blob ONCE, so one blob stored at two paths hides the second.

    Args:
        repo: The repository.
        sha: The commit.

    Returns:
        Each path mapped to the first commit the walk saw introduce it.
    """
    refuse_cut_history(repo)
    out = git(
        repo,
        [
            "log",
            "--no-renames",
            "-m",
            "--root",
            "--name-only",
            "-z",
            "--diff-filter=d",
            "--format=%x01%H",
            sha,
        ],
    )
    paths: dict[str, str] = {}
    current = sha
    for token in out.split(b"\0"):
        entry = token.lstrip(b"\n")
        if entry.startswith(b"\x01"):
            current = entry[1:].decode("ascii", errors="replace")
        elif entry:
            paths.setdefault(entry.decode("utf-8", errors="replace"), current)
    for path in git(repo, ["ls-tree", "-r", "-z", "--name-only", sha]).split(b"\0"):
        if path:
            paths.setdefault(path.decode("utf-8", errors="replace"), sha)
    return paths


def message_of(raw_commit: bytes) -> bytes:
    """The raw message of a commit object - the bytes after the header's blank line."""
    return raw_commit.partition(b"\n\n")[2]


# --- the gate and the sweep engine, loaded by path ----------------------------


def _load_by_path(name: str, path: Path) -> ModuleType:
    """Load one module by path, once per process."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise FlipError("a sibling module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module: dataclasses resolve their annotations
    # through sys.modules, so an unregistered module raises inside a class body.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sweep_engine() -> ModuleType:
    """``tests/secret_sweep_guard.py``, the engine check 1 reuses rather than rebuilds."""
    return _load_by_path("clockspeed_sweep_for_flip", SECRET_SWEEP_PATH)


def gate() -> ModuleType:
    """The tier-0 gate, as the sweep engine loads it - one copy of the rules."""
    loaded: ModuleType = sweep_engine().gate()
    return loaded


# --- check 1: secrets ---------------------------------------------------------


def raw_secret_findings(label: str, data: bytes) -> list[str]:
    """The gate's ``check_secrets`` over bytes its admission rule did not gate."""
    report = gate().Report()
    gate().check_secrets(label, data.decode("utf-8", errors="replace"), report)
    return [diag.render() for diag in report.diagnostics]


def secret_scan(repo: Path, sha: str) -> CheckResult:
    """Every credential shape the gate's own rules find in REF's history.

    Args:
        repo: The repository.
        sha: The resolved commit.

    Returns:
        The result; its control is set by :func:`measure`.
    """
    engine = sweep_engine()
    result = CheckResult("1", "secret-scan")
    named, blobs, commits = population(repo, sha)
    declined = 0
    findings = 0
    hit: set[str] = set()
    for blob_sha, data in stream_objects(repo, blobs):
        relative = named.get(blob_sha, "")
        if engine.admit(blob_sha, relative, data) is not None:
            found: list[str] = engine.secret_findings(blob_sha, relative, data)
        else:
            declined += 1
            found = raw_secret_findings(blob_sha, data)
        if found:
            hit.add(blob_sha)
            findings += len(found)
    for commit_sha, raw in stream_objects(repo, commits):
        found = raw_secret_findings(commit_sha, message_of(raw))
        if found:
            hit.add(commit_sha)
            findings += len(found)
    result.counts = {
        "blobs": len(blobs),
        "commit messages": len(commits),
        "declined by the gate and scanned raw": declined,
        "findings": findings,
    }
    result.shas = sorted(hit)
    if findings:
        result.failures.append("a credential shape the gate blocks is reachable from REF")
    if not blobs:
        result.failures.append("the blob population is empty")
    return result


# --- check 2: personal data ---------------------------------------------------


class Matcher:
    """One compiled needle kind. Its ``repr`` withholds the pattern."""

    def __init__(self, kind: str, pattern: re.Pattern[bytes], prefilter: tuple[bytes, ...]) -> None:
        """Keep the kind, the pattern and the lowercased literals one of which must occur."""
        self.kind = kind
        self._pattern = pattern
        self._prefilter = prefilter

    def __repr__(self) -> str:
        """Name the kind; withhold the pattern."""
        return f"<Matcher {self.kind}: pattern withheld>"

    @classmethod
    def of_values(cls, kind: str, values: Sequence[str]) -> Matcher:
        """Build a whole-word, case-insensitive matcher over literal values."""
        pieces: list[bytes] = []
        prefilter: list[bytes] = []
        for value in values:
            encoded = value.encode("utf-8")
            escaped = re.escape(encoded)
            if kind in PATH_KINDS:
                escaped = escaped.replace(b"/", rb"[\\/]+")
                segments = [part for part in encoded.split(b"/") if part]
                prefilter.append(max(segments, key=len).lower() if segments else encoded.lower())
            else:
                prefilter.append(encoded.lower())
            pieces.append(escaped)
        ordered: list[bytes] = sorted(pieces, key=len, reverse=True)
        body = b"|".join(ordered)
        pattern = re.compile(
            _BOUNDARY_BEFORE + b"(?:" + body + b")" + _BOUNDARY_AFTER, re.IGNORECASE
        )
        return cls(kind, pattern, tuple(prefilter))

    def count(self, data: bytes, lowered: bytes | None = None) -> int:
        """How many times this kind occurs in ``data``."""
        if self._prefilter:
            low = data.lower() if lowered is None else lowered
            if not any(literal in low for literal in self._prefilter):
                return 0
        return sum(1 for _match in self._pattern.finditer(data))


class NeedleSet:
    """The check-2 needles. EVERY VALUE IS WITHHELD FROM ``repr``.

    Held in memory for one run and never written anywhere. A test runner, a
    logger and a traceback renderer all repr an object before a human chooses
    what to print, so ``repr`` names a count and nothing else.
    """

    def __init__(self) -> None:
        """Start empty."""
        self._values: dict[str, set[str]] = {}
        self._patterns: list[tuple[str, re.Pattern[bytes], tuple[bytes, ...]]] = []
        self.dropped = 0
        self.unreadable = 0
        self.failures: list[str] = []

    def __repr__(self) -> str:
        """Name the count; withhold every value."""
        return f"<NeedleSet: {sum(self.counts().values())} needles withheld>"

    def add(self, kind: str, value: str | None) -> None:
        """Add one needle value under ``kind``, dropping one too short to match safely."""
        text = (value or "").strip()
        if not text:
            return
        if kind == "header-string" and text.casefold() in NON_PERSONAL_HEADER_STRINGS:
            return
        if len(text) < locate.MIN_REDACTABLE_LEN:
            self.dropped += 1
            return
        self._values.setdefault(kind, set()).add(text)

    def add_pattern(
        self, kind: str, pattern: re.Pattern[bytes], prefilter: tuple[bytes, ...]
    ) -> None:
        """Add a PATTERN needle - a shape rather than a value, such as any home path."""
        self._patterns.append((kind, pattern, prefilter))

    def with_value(self, kind: str, value: str) -> NeedleSet:
        """A copy of this set with one more value - the check-2 control's plant."""
        copy = NeedleSet()
        copy._values = {name: set(values) for name, values in self._values.items()}
        copy._patterns = list(self._patterns)
        copy.add(kind, value)
        return copy

    def counts(self) -> dict[str, int]:
        """How many needles of each kind, and nothing else."""
        counted = {kind: len(values) for kind, values in sorted(self._values.items())}
        for kind, _pattern, _prefilter in self._patterns:
            counted[kind] = counted.get(kind, 0) + 1
        return counted

    def matchers(self) -> list[Matcher]:
        """One compiled matcher per value kind, then one per pattern."""
        built = [
            Matcher.of_values(kind, sorted(values)) for kind, values in sorted(self._values.items())
        ]
        built.extend(
            Matcher(kind, pattern, prefilter) for kind, pattern, prefilter in self._patterns
        )
        return built

    def self_match_misses(self) -> int:
        """How many value needles the matcher of their own kind cannot find.

        The in-memory control, run over bytes built here and never written: each
        value is set between two spaces and must be found by its kind's matcher.
        """
        misses = 0
        for kind, values in self._values.items():
            matcher = Matcher.of_values(kind, sorted(values))
            for value in values:
                if not matcher.count(b" " + value.encode("utf-8") + b" "):
                    misses += 1
        return misses


def decoded_option_strings(options: str) -> list[str]:
    """Every length-prefixed string inside the hex-valued fields of an options string.

    The options string is a query string, ``?key=value?key=value``. A value
    that is an even-length run of hex digits is decoded to bytes, and every
    length-prefixed string inside it is returned - an int32 length counting the
    terminator, then that many bytes ending in NUL, or a negative length for
    UTF-16. That is where the display name and the identity strings sit
    (``BOOTSTRAP.md`` section 2.2), and no field NAME is relied on.

    Args:
        options: The options string, from ``reveal_strings`` at the render site.

    Returns:
        The decoded strings, in field order.
    """
    found: list[str] = []
    for segment in options.split("?"):
        _key, separator, value = segment.partition("=")
        if not separator or len(value) % 2 or not re.fullmatch(r"[0-9A-Fa-f]+", value):
            continue
        found.extend(_length_prefixed_strings(bytes.fromhex(value)))
    return found


def _length_prefixed_strings(blob: bytes) -> list[str]:
    """Every plausible length-prefixed string in ``blob``, scanning every offset."""
    found: list[str] = []
    index = 0
    while index + LENGTH_PREFIX_BYTES <= len(blob):
        length = int.from_bytes(blob[index : index + LENGTH_PREFIX_BYTES], "little", signed=True)
        start = index + LENGTH_PREFIX_BYTES
        decoded = _decode_at(blob, start, length)
        if decoded is None:
            index += 1
            continue
        text, width = decoded
        found.append(text)
        index = start + width
    return found


def _decode_at(blob: bytes, start: int, length: int) -> tuple[str, int] | None:
    """Decode one length-prefixed string at ``start``, or None when it is not one."""
    if 1 < length <= MAX_DECODED_STRING:
        return _decode_narrow(blob[start : start + length], length)
    if -MAX_DECODED_STRING <= length < -1:
        return _decode_wide(blob[start : start - length * 2], -length * 2)
    return None


def _decode_narrow(body: bytes, width: int) -> tuple[str, int] | None:
    """A narrow string: ``width`` bytes, NUL-terminated, printable ASCII before it."""
    if len(body) != width or body[-1] != 0:
        return None
    text = body[:-1]
    if not all(PRINTABLE_LOW <= byte <= PRINTABLE_HIGH for byte in text):
        return None
    return text.decode("ascii"), width


def _decode_wide(body: bytes, width: int) -> tuple[str, int] | None:
    """A UTF-16-LE string: ``width`` bytes ending in a two-byte NUL, printable before it."""
    if len(body) != width or body[-2:] != b"\0\0":
        return None
    try:
        text = body[:-2].decode("utf-16-le")
    except UnicodeDecodeError:
        return None
    return (text, width) if text.isprintable() else None


def _add_header_needles(needles: NeedleSet, data: bytes) -> tuple[int, int]:
    """Add one header's personal strings. THIS IS THE RENDER SITE of the opt-in.

    The revealed strings go straight into the needle set and nowhere else, the
    result object is unbound before this returns, and a refusal is counted,
    never re-raised, so no value can travel out as exception context.

    Returns:
        ``(headers parsed, strings decoded)``.
    """
    try:
        strings = header.reveal_strings(data, reveal_personal_data=True)
    except header.HeaderError:
        needles.unreadable += 1
        return 0, 0
    try:
        needles.add("world-name", strings.session_name)
        values = decoded_option_strings(strings.map_options)
        for value in values:
            needles.add("header-string", value)
        return 1, len(values)
    finally:
        del strings


def derive_needles() -> NeedleSet:
    """Derive this machine's PII needles, in-process, at run time.

    Returns:
        The needles. A source that does not resolve is recorded in
        ``failures`` as fixed text; a save that could not be read counts in
        ``unreadable``. Neither ever names a value or a path.
    """
    needles = NeedleSet()
    save_root = locate.resolve_save_root()
    if save_root is None:
        needles.failures.append("the save root did not resolve")
    accounts = {str(path): path for path in locate.numeric_account_dirs(save_root)}
    resolved = locate.resolve_account_dir(save_root)
    if resolved is not None:
        accounts[str(resolved)] = resolved
    if not accounts:
        needles.failures.append("no account directory resolved")
    for directory in accounts.values():
        needles.add("account-id", directory.name)
    for value, token in locate._redaction_pairs():  # noqa: SLF001 - one owner of these needles
        needles.add(_TOKEN_KINDS.get(token, "home-path"), value)
    for pattern in (gate().PII_WIN_HOME_RE, gate().PII_NIX_HOME_RE):
        compiled = re.compile(pattern.pattern.encode("ascii"))
        needles.add_pattern("any-home-path", compiled, (b"users", b"home"))
    parsed = 0
    decoded = 0
    for directory in accounts.values():
        for save in sorted(directory.glob("*.sav")):
            try:
                with save.open("rb") as handle:
                    data = handle.read(header.MAX_HEADER_BYTES)
            except OSError:
                needles.unreadable += 1
                continue
            parsed_here, decoded_here = _add_header_needles(needles, data)
            del data
            parsed += parsed_here
            decoded += decoded_here
    if not parsed:
        needles.failures.append("no save header could be read")
    if not decoded:
        needles.failures.append("no header string was decoded, so no display name was derived")
    return needles


def pii_scan(repo: Path, sha: str, needles: NeedleSet) -> CheckResult:
    """Every needle hit in REF's blobs, history paths and raw commit objects.

    Args:
        repo: The repository.
        sha: The resolved commit.
        needles: The needle set; never rendered.

    Returns:
        Counts per channel and per kind, and the SHAs of the hit blobs and of the
        commits that carry or introduced a hit.
    """
    result = CheckResult("2", "pii-scan")
    matchers = needles.matchers()
    _named, blobs, commits = population(repo, sha)
    per_kind: dict[str, int] = {}
    hit: set[str] = set()

    def scan(data: bytes) -> int:
        lowered = data.lower()
        total = 0
        for matcher in matchers:
            found = matcher.count(data, lowered)
            if found:
                per_kind[matcher.kind] = per_kind.get(matcher.kind, 0) + found
                total += found
        return total

    channels = {"blob hits": 0, "path hits": 0, "commit hits": 0}
    for blob_sha, data in stream_objects(repo, blobs):
        found = scan(data)
        if found:
            hit.add(blob_sha)
            channels["blob hits"] += found
    for commit_sha, raw in stream_objects(repo, commits):
        found = scan(raw)
        if found:
            hit.add(commit_sha)
            channels["commit hits"] += found
    for path, introduced_by in history_paths(repo, sha).items():
        found = scan(path.encode("utf-8"))
        if found:
            hit.add(introduced_by)
            channels["path hits"] += found
    counts = needles.counts()
    result.counts = {"needles": sum(counts.values())}
    result.counts.update({f"needles {kind}": count for kind, count in counts.items()})
    result.counts.update({"blobs": len(blobs), "commits": len(commits), **channels})
    result.counts.update({f"hits {kind}": count for kind, count in sorted(per_kind.items())})
    result.shas = sorted(hit)
    result.skips = needles.dropped + needles.unreadable + needles.self_match_misses()
    result.failures.extend(needles.failures)
    if any(channels.values()):
        result.failures.append("a needle is reachable from REF")
    if not blobs:
        result.failures.append("the blob population is empty")
    return result


# --- check 4: publisher-owned assets ------------------------------------------


def publisher_scan(repo: Path, sha: str) -> CheckResult:
    """Every path any reachable tree held that the gate's PUBLISHER rule refuses."""
    result = CheckResult("4", "publisher-assets")
    paths = history_paths(repo, sha)
    offending: set[str] = set()
    hits = 0
    for path, introduced_by in paths.items():
        report = gate().Report()
        gate().check_path(path, report)
        if any(diag.code == "PUBLISHER" for diag in report.diagnostics):
            hits += 1
            offending.add(introduced_by)
    result.counts = {"history paths": len(paths), "publisher paths": hits}
    result.shas = sorted(offending)
    if hits:
        result.failures.append("a publisher-owned asset path is reachable from REF")
    if not paths:
        result.failures.append("the path population is empty")
    return result


# --- child tools: checks 3 and 6 ----------------------------------------------


@dataclass(frozen=True)
class ChildRun:
    """One child process: its exit code and captured output, which is never printed."""

    code: int
    output: str


def run_child(argv: Sequence[str], cwd: Path, env: dict[str, str] | None = None) -> ChildRun:
    """Run one bounded child, capturing its output so none of it reaches ours."""
    try:
        completed = subprocess.run(
            list(argv),
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CHILD_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FlipError(f"a child tool could not be run: {type(exc).__name__}") from None
    return ChildRun(completed.returncode, completed.stdout + completed.stderr)


#: The ONE absolute shape the cross-drive fallback allows: a plain drive-letter
#: path. A UNC share, a ``\\?\`` verbatim or a ``\\.\`` device spelling - each
#: able to name a home in no drive-letter shape - never matches.
_PLAIN_DRIVE_PATH: Final = re.compile(r"[A-Za-z]:\\(?![\\/])")


def _under_a_home(named: str) -> bool:
    """Whether ``named`` renders a home: any home shape in any case, or this home."""
    rules = gate()
    for rule in (rules.PII_WIN_HOME_RE, rules.PII_NIX_HOME_RE):
        if re.search(rule.pattern, named, re.IGNORECASE):
            return True
    try:
        located = Path.home()
    except RuntimeError:
        # No home to rule out is no proof of being outside one: refuse.
        raise FlipError("the home directory did not resolve, so no path is allowed") from None
    home = os.path.normcase(os.path.realpath(located)).rstrip("\\/")
    folded = os.path.normcase(named)
    return folded == home or folded.startswith(home + "\\")


def _relative_or_anchored(path: Path, start: Path) -> str:
    """``path`` named relative to ``start``; across two drives, an ALLOWLISTED absolute.

    ``os.path.relpath`` raises ``ValueError`` when the two sit on different
    Windows drives - the GitHub windows runner checks the repository out on D:
    while pytest's scratch is on C: (CS-1230). No relative spelling exists then.
    The real path is used instead ONLY when both it and the given spelling are
    plain drive-letter paths and it is neither under the real home nor a home
    shape in any case. Anything else is refused with fixed text naming no path.

    Raises:
        FlipError: No relative spelling exists and no allowed absolute one does.
    """
    try:
        return os.path.relpath(path, start)
    except ValueError:
        anchored = os.path.realpath(path)
    plain = all(_PLAIN_DRIVE_PATH.match(spelling) for spelling in (str(path), anchored))
    if not plain or _under_a_home(anchored):
        raise FlipError("a path on another drive has no spelling outside a home")
    return anchored


def _tool_argv(tool: Path, cwd: Path, *args: str) -> list[str]:
    """This interpreter on a sibling tool, named by a path RELATIVE to ``cwd``.

    Across two Windows drives no relative path exists; :func:`_relative_or_anchored`
    names the tool by its drive-anchored path instead, refusing one under a home.
    """
    return [sys.executable, "-B", _relative_or_anchored(tool, cwd), *args]


def licence_audit(tree: Path) -> CheckResult:
    """``tools/licence_audit.py`` over ``tree``: counts parsed, output never relayed."""
    result = CheckResult("3", "licence-audit")
    run = run_child(_tool_argv(LICENCE_AUDIT_PATH, tree, "--root", "."), tree)
    summary = re.search(r"findings (\d+); notes (\d+)", run.output)
    result.counts = {
        "exit": run.code,
        "findings": int(summary.group(1)) if summary else 0,
        "notes": int(summary.group(2)) if summary else 0,
    }
    result.skips = len(re.findall(r"^  python: `", run.output, re.MULTILINE))
    if summary is None:
        result.failures.append("the licence audit printed no summary line")
    if run.code != 0:
        result.failures.append("the licence audit exited non-zero")
    return result


def doc_sweep_module() -> ModuleType:
    """``tools/doc_sweep.py``, loaded by path under a name only this tool uses."""
    return _load_by_path("clockspeed_doc_sweep_for_flip", DOC_SWEEP_PATH)


def citation_gate() -> ModuleType:
    """``tools/sha_citation_gate.py``, whose binary pins check 6 reads - CS-1332."""
    return _load_by_path("clockspeed_sha_citation_gate_for_flip", CITATION_GATE_PATH)


def recording_reader(
    reader: Callable[[Path, str], str | None], unread: list[str]
) -> Callable[[Path, str], str | None]:
    """doc_sweep's own reader, wrapped to record each tracked name it returns nothing for."""

    def recording_read(root: Path, name: str) -> str | None:
        text = reader(root, name)
        if text is None:
            unread.append(name)
        return text

    return recording_read


def excused_binaries(
    tree: Path, unread: Sequence[str], counted: int, markdown_suffix: str, result: CheckResult
) -> int:
    """CS-1332: how many files the sweep could not read a hash pin excuses.

    The pins are the sha-citation gate's own file in the REF tree, read by that
    gate's own loader and matched by its own ``is_known_binary`` - path AND
    SHA-256 of the exact bytes, never an extension or a magic number. Every file
    not excused stays a skip. A pin source the loader refuses or cannot read
    FAILS the check and excuses nothing. A pinned path whose bytes have drifted
    FAILS. A markdown file is never excused, pinned or not: the sweep's rules
    read markdown, so a NUL there hides its links, anchors and URLs. When the
    sweep counted a different number of unreadable files from the ones its
    wrapped reader saw, the check FAILS and nothing is excused, because a count
    no identity stands behind is never offset.

    Args:
        tree: A checkout of REF.
        unread: The tracked files doc_sweep's own reader returned nothing for.
        counted: doc_sweep's own unreadable-or-binary skip count.
        markdown_suffix: doc_sweep's own markdown suffix.
        result: Check 6's result, which each fixed failure reason is added to.

    Returns:
        The number of files excused.
    """
    module = citation_gate()
    unseen = counted != len(unread)
    if unseen:
        result.failures.append("the unreadable files were not all learned by identity")
    try:
        pins = module.load_known_binaries(tree)
    except (module.GateError, OSError):
        result.failures.append("the binary pin source could not be read or trusted")
        return 0
    excused = 0
    markdown = drifted = False
    for name in sorted(set(unread)):
        if name.casefold().endswith(markdown_suffix.casefold()):
            markdown = True
            continue
        if name not in pins:
            continue
        try:
            raw = (tree / name).read_bytes()
        except OSError:
            continue
        if module.is_known_binary(name, raw, pins):
            excused += 1
        else:
            drifted = True
    if markdown:
        result.failures.append("a markdown file the sweep could not read")
    if drifted:
        result.failures.append("a pinned binary whose bytes have drifted from its pin")
    return 0 if unseen else excused


def doc_sweep(
    tree: Path,
    *,
    fetch: Callable[[str], int] | None = None,
    allowlists: tuple[dict[str, str], dict[str, str]] | None = None,
    no_fetch_pinned: frozenset[str] = NO_FETCH_PINNED,
) -> CheckResult:
    """Check 6: ``tools/doc_sweep.py``'s own sweep, with ``--urls``, under ADR 0025 point 10.

    a. :data:`NO_FETCH_PINNED` - the exact distinct URLs on a doc_sweep no-fetch host
       the tree may carry. PERMANENT: CS-485 forbids any automated fetch of it, so it
       holds at S1, at S8 and after the flip. A pinned URL is reported
       ``policy-excluded``, never passed, and is not counted as a skip.
    b. The pre-publication pin is DELETED, as point 10b orders for the first commit
       after S12: the repository answers publicly, so every dead URL FAILS, README's
       tier1 badge included, and nothing excuses one.
    c. MATCHED BY URL, NEVER BY COUNT. The check FAILS on any skipped URL outside
       its pin, any dead URL, any skip kind other than no-fetch-host, and any pinned
       URL the tree no longer carries (a stale pin).
    d. REPORTED, NEVER SILENT. ``policy-excluded`` is a count of its own, apart from
       skips and findings, and the final line names it.
    e. CS-1332 - A FILE THE SWEEP COULD NOT READ is learned by identity too, through
       doc_sweep's own reader, wrapped the same way. One whose path AND SHA-256 match
       a pin in the REF tree's sha-citation binary pin file is counted
       ``known-binary``, never a skip; every other one stays a skip and FAILS - see
       :func:`excused_binaries` for the drifted, markdown and untrusted-pin cases.

    The sweep runs IN-PROCESS so every URL is known by identity: the skipped ones
    through doc_sweep's own no-fetch predicate, wrapped to record what it refused,
    and the fetched ones through a recording fetcher. doc_sweep's CLI prints skip
    counts, not skipped URLs, and that file is not this slice's to change. No URL is
    ever printed here, and no path.

    Args:
        tree: A checkout of REF.
        fetch: The URL fetcher; doc_sweep's own when None. The arms pass a stub.
        allowlists: doc_sweep's live and stale allowlists; its own when None.
        no_fetch_pinned: Pin a.

    Returns:
        The result; its control is set by :func:`measure`.
    """
    result = CheckResult("6", "doc-sweep")
    module = doc_sweep_module()
    fetcher: Callable[[str], int] = fetch or module.fetch_status
    statuses: dict[str, int | None] = {}
    skipped: set[str] = set()
    predicate = getattr(module, NO_FETCH_PREDICATE)  # doc_sweep's own rule, wrapped not copied

    def recording_fetch(url: str) -> int:
        try:
            status = fetcher(url)
        except Exception:
            statuses[url] = None
            raise
        statuses[url] = status
        return status

    def recording_no_fetch(url: str, hosts: Mapping[str, str]) -> bool:
        refused = bool(predicate(url, hosts))
        if refused:
            skipped.add(url)
        return refused

    reader = getattr(module, READ_TEXT_HOOK)  # doc_sweep's own reader, wrapped not copied
    unread: list[str] = []
    live, stale = allowlists if allowlists is not None else (None, None)
    setattr(module, NO_FETCH_PREDICATE, recording_no_fetch)
    setattr(module, READ_TEXT_HOOK, recording_reader(reader, unread))
    try:
        report = module.sweep(
            tree, allowlist=live, stale_allowlist=stale, check_urls=True, fetch=recording_fetch
        )
    except module.CouldNotRunError:
        result.failures.append("the doc sweep could not run")
        return result
    finally:
        setattr(module, NO_FETCH_PREDICATE, predicate)
        setattr(module, READ_TEXT_HOOK, reader)
    counted = report.skips.get(module.SKIP_UNREADABLE, 0)
    known = excused_binaries(tree, unread, counted, module.MARKDOWN_SUFFIX, result)
    dead = {url for url, status in statuses.items() if status is None or status >= HTTP_ERROR}
    other_kinds = sum(n for kind, n in report.skips.items() if kind != module.SKIP_NO_FETCH_HOST)
    other_kinds -= known
    excluded = skipped & no_fetch_pinned
    url_findings = sum(1 for finding in report.findings if finding.kind == module.DEAD_URL)
    result.counts = {
        "urls checked": report.urls_checked,
        "findings": len(report.findings) - url_findings + len(dead),
        "policy-excluded": len(excluded),
        "known-binary": known,
    }
    result.skips = other_kinds + len(skipped - no_fetch_pinned)
    if skipped - no_fetch_pinned:
        result.failures.append("a no-fetch URL outside the pinned set")
    if other_kinds:
        result.failures.append("a skip of a kind other than no-fetch-host")
    if no_fetch_pinned - skipped:
        result.failures.append("a pinned URL the tree no longer carries")
    if dead:
        result.failures.append("a dead URL")
    if len(report.findings) - url_findings:
        result.failures.append("the doc sweep reported a finding")
    return result


# --- checks 5 and 7: command walks in a scratch clone -------------------------


def command_lines(markdown: str, *, after: re.Pattern[str] | None = None) -> tuple[list[str], int]:
    """The command lines of every fenced block made only of ``python`` lines.

    Args:
        markdown: The document.
        after: When given, only the FIRST such block after this heading counts.

    Returns:
        ``(runnable lines, unrunnable lines)``. A block is a command block when
        every non-empty line starts with ``python ``; a trailing `` # comment``
        is dropped; a line :data:`_RUNNABLE_RE` refuses is counted, never run.
    """
    text = markdown
    if after is not None:
        heading = after.search(markdown)
        if heading is None:
            return [], 0
        text = markdown[heading.end() :]
    runnable: list[str] = []
    unrunnable = 0
    for block in _FENCE_RE.finditer(text):
        lines = [line.split(" #", 1)[0].strip() for line in block.group(1).splitlines()]
        lines = [line for line in lines if line]
        if not lines or not all(line.startswith("python ") for line in lines):
            continue
        for line in lines:
            if _RUNNABLE_RE.match(line):
                runnable.append(line)
            else:
                unrunnable += 1
        if after is not None:
            break
    return runnable, unrunnable


def command_argv(line: str, python: str | None = None) -> list[str]:
    """Turn one runnable command line into an argv with ``python`` resolved from PATH."""
    interpreter = python or resolve_tool("python")
    if interpreter is None:
        raise FlipError("python is not on PATH")
    return [interpreter, *shlex.split(line, posix=True)[1:]]


def scrubbed_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """This environment without any project override, plus ``extra``.

    Windows upper-cases environment keys, so the prefix is compared upper-cased.
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(PROJECT_ENV_PREFIX)
    }
    env.update(extra or {})
    return env


def free_port() -> int:
    """A loopback port nothing is listening on at the moment of asking."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
    return port


def port_open(port: int) -> bool:
    """Whether something accepts a TCP connection on loopback ``port``."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=CONNECT_TIMEOUT):
            return True
    except OSError:
        return False


def run_command(
    argv: Sequence[str], cwd: Path, env: dict[str, str], port: int, timeout: float
) -> bool:
    """Run one README command: it passes by exiting 0, or by binding ``port``.

    A command still running at ``timeout`` that never bound the port FAILS - a
    hang is not a serve. A command that bound is stopped once it has.
    """
    try:
        proc = subprocess.Popen(
            list(argv),
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False
    deadline = time.monotonic() + timeout
    passed = False
    try:
        while time.monotonic() < deadline:
            code = proc.poll()
            if code is not None:
                passed = code == 0
                break
            if port_open(port):
                passed = True
                break
            time.sleep(POLL_SECONDS)
    finally:
        stop(proc)
        proc.wait(timeout=CHILD_TIMEOUT)
    return passed


def stop(proc: subprocess.Popen[bytes]) -> None:
    """Stop a child AND its descendants, then reap it.

    ``Popen.kill`` ends one process. A server that started a child, or a launcher
    that re-executed a real interpreter, would leave the descendant holding the
    port and the scratch tree, so on Windows the whole tree goes through
    ``taskkill /T``, resolved from PATH like every other tool here.
    """
    if proc.poll() is None:
        taskkill = resolve_tool("taskkill") if sys.platform == "win32" else None
        if taskkill is not None:
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                subprocess.run(
                    [taskkill, "/T", "/F", "/PID", str(proc.pid)],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=CHILD_TIMEOUT,
                    check=False,
                )
        if proc.poll() is None:
            proc.kill()
    proc.wait(timeout=CHILD_TIMEOUT)


def readme_walk(
    tree: Path, *, python: str | None = None, timeout: float = README_COMMAND_TIMEOUT
) -> CheckResult:
    """Check 5's automatable half: README's own command lines, run in ``tree``.

    Args:
        tree: A checkout of REF.
        python: The interpreter to run ``python`` as; PATH's when None.
        timeout: Seconds each command gets to exit 0 or bind the port.

    Returns:
        The result. The overrides are RELATIVE paths under a directory that does
        not exist in ``tree``, so they resolve to nothing and carry no home.
    """
    result = CheckResult("5", "readme-walk (automated half)")
    try:
        markdown = (tree / "README.md").read_text(encoding="utf-8")
    except OSError:
        result.failures.append("README.md could not be read")
        return result
    lines, unrunnable = command_lines(markdown)
    absent = Path(ABSENT_DIRNAME)
    port = free_port()
    env = scrubbed_env(
        {
            locate.ENV_GAME_DIR: str(absent / "game"),
            locate.ENV_SAVE_ROOT: str(absent / "saves"),
            locate.ENV_ACCOUNT_DIR: str(absent / "account"),
            locate.ENV_LOCAL_CONFIG: str(absent / "local.json"),
            PORT_ENV: str(port),
        }
    )
    if (tree / absent).exists():
        result.failures.append("the override directory exists in the tree")
    if port_open(port):
        result.failures.append("the chosen port was already bound before the walk")
    failed = 0
    for line in lines:
        if not run_command(command_argv(line, python), tree, env, port, timeout):
            failed += 1
    result.counts = {"commands": len(lines), "failed": failed}
    result.skips = unrunnable
    if not lines:
        result.failures.append("README carries no runnable command line")
    if failed:
        result.failures.append("a README command neither exited 0 nor served")
    return result


def head_of(clone: Path) -> str:
    """The clone's HEAD commit."""
    return git(clone, ["rev-parse", "HEAD"]).decode("ascii").strip()


def violation_moves_head(clone: Path, env: dict[str, str], *, hooks_off: bool) -> bool | None:
    """Stage a non-ASCII violation, attempt a real commit, report whether HEAD moved.

    The violating byte is generated here at run time, never spelled in source.

    Returns:
        True when HEAD moved, False when it did not, None when the attempt could
        not be made at all.
    """
    (clone / PROBE_FILE).write_bytes(b"flip probe " + bytes([0xC3, 0xA9]) + b"\n")
    try:
        git(clone, ["add", PROBE_FILE], env=env)
        before = head_of(clone)
    except FlipError:
        return None
    config = list(_PROBE_IDENTITY)
    if hooks_off:
        config += ["-c", f"core.hooksPath={NO_HOOKS}"]
    try:
        subprocess.run(
            [_git_path(), *config, "commit", "-q", "-m", "CS-1183 - flip check probe"],
            cwd=clone,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=CHILD_TIMEOUT,
            check=False,
        )
        return head_of(clone) != before
    except (OSError, subprocess.TimeoutExpired, FlipError):
        return None


def clean_checkout(clone: Path, sha: str, *, python: str | None = None) -> CheckResult:
    """Check 7's automatable half, in a FRESH clone of REF.

    The control runs first: the same staged violation, committed with no hook,
    must MOVE HEAD - which proves the probe can see a commit land. The clone is
    then reset to REF, the ``docs/OPERATIONS.md`` bootstrap block runs, and the
    violation must leave HEAD unmoved.
    """
    result = CheckResult("7", "clean-checkout (automated half)")
    env = scrubbed_env()
    if (clone / NO_HOOKS).exists():
        result.failures.append("the no-hooks path exists in the tree")
    result.control = bool(violation_moves_head(clone, env, hooks_off=True))
    git(clone, ["reset", "-q", "--hard", sha], env=env)
    try:
        operations = (clone / "docs" / "OPERATIONS.md").read_text(encoding="utf-8")
    except OSError:
        result.failures.append("docs/OPERATIONS.md could not be read")
        return result
    lines, unrunnable = command_lines(operations, after=BOOTSTRAP_HEADING_RE)
    failed = sum(1 for line in lines if run_child(command_argv(line, python), clone, env).code)
    moved = violation_moves_head(clone, env, hooks_off=False)
    result.counts = {"bootstrap commands": len(lines), "failed": failed}
    result.skips = unrunnable
    if not lines:
        result.failures.append("docs/OPERATIONS.md carries no bootstrap command block")
    if failed:
        result.failures.append("a bootstrap command exited non-zero")
    if moved is None:
        result.failures.append("the staged violation could not be attempted")
    elif moved:
        result.failures.append("a staged violation committed - the armed hooks did not fire")
    return result


# --- the trailer axis ---------------------------------------------------------


def trailer_axis(
    repo: Path, sha: str, stage: str, baseline: tuple[str, int] | None = None
) -> CheckResult:
    """The CS-1180 seventh axis, through ``tools/trailer_census.py``.

    Args:
        repo: The repository.
        sha: The resolved commit.
        stage: ``s1`` or ``s8``.
        baseline: At S8, the pre-S7a baseline ref and the count it recorded.

    Returns:
        The result. At S1 hits are an early warning and fail only on zero or on
        a hit the strip would leave behind; at S8 any hit fails, and a missing
        baseline control is a skip while a mismatched one is a failure.
    """
    result = CheckResult("T", f"trailer-axis ({stage})")
    walked = trailer_census.walk(repo, sha)
    hit = [entry for entry in walked if entry.hit_lines]
    left_behind = [entry for entry in hit if not entry.strippable]
    result.counts = {
        "commits walked": len(walked),
        "trailer lines": sum(len(entry.hit_lines) for entry in walked),
        "commits with a hit": len(hit),
        "not strippable": len(left_behind),
    }
    result.shas = [entry.sha for entry in hit]
    if stage == STAGE_S1:
        if not hit:
            result.failures.append("S1 found zero trailers, so the census measured nothing")
        if left_behind:
            result.failures.append("a trailer S7a's strip would leave behind")
        return result
    if hit:
        result.failures.append("a trailer is reachable from REF after the strip")
    if baseline is None:
        result.skips += 1
        result.failures.append("the S8 baseline control was not supplied")
    else:
        result.failures.extend(_baseline_failures(repo, baseline))
    return result


def _baseline_failures(repo: Path, baseline: tuple[str, int]) -> list[str]:
    """The S8 second control: the census over the pre-S7a baseline returns its count."""
    ref, expected = baseline
    try:
        base_sha = resolve_ref(repo, ref)
        counted = sum(len(entry.hit_lines) for entry in trailer_census.walk(repo, base_sha))
    except (FlipError, trailer_census.CensusError):
        return ["the S8 baseline ref could not be walked"]
    if expected <= 0 or counted != expected:
        return ["the S8 baseline census did not return its recorded non-zero count"]
    return []


# --- the identity axis --------------------------------------------------------

#: The forge's noreply domain. The address is ``<id>+<login>@`` this.
NOREPLY_DOMAIN: Final = "users.noreply.github.com"

#: A forge login: letters, digits and single hyphens. Anything else derives nothing.
_LOGIN_RE: Final = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}")

#: One identity header line of a raw commit object: role, name, address, date.
_IDENT_RE: Final = re.compile(rb"^(author|committer) (.*) <([^<>]*)> -?\d+ [+-]\d{4}$")

#: A commit carries exactly two identity lines, author then committer; any other
#: count is a commit this axis cannot grade, and is counted as a skip.
IDENT_FIELDS: Final = 2

ForgeUser = Callable[[], "Mapping[str, object] | None"]


class IdentityAllowlist:
    """The S8 identity allowlist. EVERY VALUE IS WITHHELD FROM ``repr``.

    Held in memory for one run and never written anywhere, as :class:`NeedleSet`.
    """

    def __init__(
        self,
        names: frozenset[str] = frozenset(),
        addresses: frozenset[str] = frozenset(),
        failures: Sequence[str] = (),
    ) -> None:
        """Keep the allowed names and addresses and any derivation failures."""
        self._names = frozenset(name.encode("utf-8") for name in names)
        self._addresses = frozenset(address.encode("utf-8") for address in addresses)
        self.failures = list(failures)

    def __repr__(self) -> str:
        """Name the counts; withhold every value."""
        return (
            f"<IdentityAllowlist: {len(self._names)} names, "
            f"{len(self._addresses)} addresses withheld>"
        )

    def counts(self) -> dict[str, int]:
        """How many names and addresses are allowed, and nothing else."""
        return {
            "allowlisted names": len(self._names),
            "allowlisted addresses": len(self._addresses),
        }

    def admits_name(self, name: bytes) -> bool:
        """Whether ``name`` is on the allowlist, byte for byte."""
        return name in self._names

    def admits_address(self, address: bytes) -> bool:
        """Whether ``address`` is on the allowlist, byte for byte."""
        return address in self._addresses


def forge_noreply(user: Mapping[str, object] | None) -> str | None:
    """The forge noreply address for an account answer, or None when it is malformed."""
    if not isinstance(user, Mapping):
        return None
    ident = user.get("id")
    login = user.get("login")
    if isinstance(ident, bool) or not isinstance(ident, int) or ident <= 0:
        return None
    if not isinstance(login, str) or not _LOGIN_RE.fullmatch(login):
        return None
    return f"{ident}+{login}@{NOREPLY_DOMAIN}"


def gh_user() -> Mapping[str, object] | None:
    """The authenticated forge account, from ``gh api user``; None on any failure.

    The child's output is parsed here and never relayed; a failure is None, never
    an exception carrying the child's text.
    """
    found = resolve_tool("gh")
    if found is None:
        return None
    try:
        completed = subprocess.run(
            [found, "api", "user"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=PROBE_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    try:
        answer = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return answer if isinstance(answer, dict) else None


def derive_identity_allowlist(repo: Path, forge_user: ForgeUser | None = None) -> IdentityAllowlist:
    """Derive the identity allowlist at run time, in-process.

    Args:
        repo: The repository whose configured ``user.name`` is the one allowed name.
        forge_user: What answers the forge account; :func:`gh_user` when None.
            Injected by the tests, which never let a real account near the run.

    Returns:
        The allowlist. A source that does not resolve is recorded in ``failures``
        as fixed text, never a value.
    """
    names: set[str] = set()
    addresses: set[str] = set()
    failures: list[str] = []
    try:
        name = git(repo, ["config", "--get", "user.name"]).decode("utf-8").strip()
    except (FlipError, UnicodeDecodeError):
        name = ""
    if name:
        names.add(name)
    else:
        failures.append("the configured author name did not resolve")
    address = forge_noreply((forge_user or gh_user)())
    if address:
        addresses.add(address)
    else:
        failures.append("the forge noreply address did not resolve")
    return IdentityAllowlist(frozenset(names), frozenset(addresses), failures)


def commit_identities(repo: Path, sha: str) -> list[tuple[str, list[tuple[bytes, bytes]], int]]:
    """Every commit reachable from ``sha`` with its raw author and committer identities.

    Every parent of every commit is walked, and both the walk and the read run
    with replace objects off (:func:`raw_object_env`), so what is graded is the
    raw commit object in the store. A shallow or grafted repository is refused
    (:func:`refuse_cut_history`).

    Returns:
        ``(commit, [(name, address), ...], identity lines)`` per commit, read
        from the raw object header - author first, committer second. The last
        field counts every header line naming a role, parsed or not, so a line
        that does not parse is visible to the caller as a mismatch.

    Raises:
        FlipError: When the history is cut, or git cannot walk or read it.
    """
    refuse_cut_history(repo)
    walked = git(repo, ["rev-list", sha]).decode("ascii", errors="replace").split()
    found: list[tuple[str, list[tuple[bytes, bytes]], int]] = []
    for commit_sha, raw in stream_objects(repo, walked):
        head = raw.split(b"\n\n", 1)[0]
        idents: list[tuple[bytes, bytes]] = []
        role_lines = 0
        for line in head.split(b"\n"):
            role_lines += line.startswith((b"author ", b"committer "))
            matched = _IDENT_RE.match(line)
            if matched:
                idents.append((matched.group(2), matched.group(3)))
        found.append((commit_sha, idents, role_lines))
    return found


def identity_scan(repo: Path, sha: str, allowlist: IdentityAllowlist, stage: str) -> CheckResult:
    """The identity axis: every author and committer field on the derived allowlist.

    Args:
        repo: The repository.
        sha: The resolved commit.
        allowlist: The run-time allowlist; never rendered.
        stage: ``s1`` or ``s8``.

    Returns:
        Counts only. At S1 a field off the allowlist is an early warning; at S8 it
        fails, and the off-allowlist commits' SHAs are recorded.
    """
    result = CheckResult("I", f"identity ({stage})")
    walked = commit_identities(repo, sha)
    names: set[bytes] = set()
    addresses: set[bytes] = set()
    off_fields = 0
    off_commits: list[str] = []
    malformed = 0
    for commit_sha, idents, role_lines in walked:
        if len(idents) != IDENT_FIELDS or role_lines != IDENT_FIELDS:
            malformed += 1
        off_here = 0
        for name, address in idents:
            names.add(name)
            addresses.add(address)
            off_here += (not allowlist.admits_name(name)) + (not allowlist.admits_address(address))
        off_fields += off_here
        if off_here:
            off_commits.append(commit_sha)
    result.counts = {
        "commits walked": len(walked),
        **allowlist.counts(),
        "distinct names": len(names),
        "distinct addresses": len(addresses),
        "off-allowlist fields": off_fields,
        "commits off the allowlist": len(off_commits),
    }
    result.skips = malformed
    result.failures.extend(allowlist.failures)
    counted = allowlist.counts()
    if counted["allowlisted names"] != 1 or counted["allowlisted addresses"] != 1:
        result.failures.append("the allowlist is not exactly one name and one address")
    if not walked:
        result.failures.append("the commit walk is empty")
    if stage != STAGE_S1:
        result.shas = off_commits
        if off_fields:
            result.failures.append("an identity off the allowlist is reachable from REF")
    return result


# --- throwaway repositories for the positive controls --------------------------


class ControlRepo:
    """A throwaway repository, written with plumbing only.

    ``git commit-tree`` runs no hook and cleans up no message, and the operator's
    git configuration is excluded, so a control commits exactly what it plants.
    """

    def __init__(self, path: Path) -> None:
        """Create the repository at ``path``."""
        self.path = path
        path.mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ)
        absent = str(path.parent / "absent-gitconfig")
        self.env["GIT_CONFIG_GLOBAL"] = absent
        self.env["GIT_CONFIG_SYSTEM"] = absent
        for role in ("AUTHOR", "COMMITTER"):
            self.env[f"GIT_{role}_NAME"] = "flip-control"
            self.env[f"GIT_{role}_EMAIL"] = "flip-control@example.invalid"
        git(path, ["init", "-q"], env=self.env)
        self.head: str | None = None

    def commit(self, files: dict[str, bytes], message: bytes) -> str:
        """Replace the whole tree with ``files`` - top-level names only - and commit on main."""
        entries: list[bytes] = []
        for name, data in sorted(files.items()):
            blob = git(self.path, ["hash-object", "-w", "--stdin"], data, self.env).strip()
            entries.append(b"100644 blob " + blob + b"\t" + name.encode("utf-8"))
        listing = b"\n".join(entries) + b"\n" if entries else b""
        tree = git(self.path, ["mktree"], listing, self.env).decode("ascii").strip()
        argv = ["commit-tree", tree]
        if self.head:
            argv += ["-p", self.head]
        self.head = git(self.path, argv, message, self.env).decode("ascii").strip()
        git(self.path, ["update-ref", "refs/heads/main", self.head], env=self.env)
        return self.head


def synthetic_credential() -> str:
    """A credential-shaped value built at run time, matching the gate's AWS rule."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ234567"
    return "AKIA" + "".join(secrets.choice(alphabet) for _ in range(16))


def control_secret(scratch: Path) -> bool:
    """A credential planted and then deleted must be found in history only."""
    repo = ControlRepo(scratch / "control-secret")
    line = "access" + "_key = " + synthetic_credential() + "\n"
    repo.commit({"config.py": line.encode("ascii")}, b"plant\n")
    tip = repo.commit({"README.md": b"clean\n"}, b"remove\n")
    return secret_scan(repo.path, tip).counts.get("findings", 0) > 0


def control_pii(scratch: Path, needles: NeedleSet) -> bool:
    """A synthetic needle planted in a blob, a path and a message must be found in all three."""
    token = "flipcontrol" + secrets.token_hex(8)
    planted = needles.with_value("control", token)
    repo = ControlRepo(scratch / "control-pii")
    content = f"a line naming {token}\n".encode("ascii")
    repo.commit({f"{token}.md": content}, f"plant {token}\n".encode("ascii"))
    tip = repo.commit({"README.md": b"clean\n"}, b"remove\n")
    counts = pii_scan(repo.path, tip, planted).counts
    return all(counts.get(channel, 0) > 0 for channel in ("blob hits", "path hits", "commit hits"))


def control_publisher(scratch: Path) -> bool:
    """A publisher-owned path added and then deleted must be found in history."""
    repo = ControlRepo(scratch / "control-publisher")
    repo.commit({"world.sav": b"synthetic\n"}, b"plant\n")
    tip = repo.commit({"README.md": b"clean\n"}, b"remove\n")
    return publisher_scan(repo.path, tip).counts.get("publisher paths", 0) > 0


def control_trailer(scratch: Path) -> bool:
    """A planted trailer must be found by the same census."""
    repo = ControlRepo(scratch / "control-trailer")
    message = b"subject\n\nbody\n\nCo-authored-by: Synthetic <synthetic@example.invalid>\n"
    tip = repo.commit({"README.md": b"x\n"}, message)
    return any(entry.hit_lines for entry in trailer_census.walk(repo.path, tip))


def control_identity(scratch: Path, allowlist: IdentityAllowlist) -> bool:
    """The negative probe: a commit under the synthetic control identity must be flagged."""
    repo = ControlRepo(scratch / "control-identity")
    tip = repo.commit({"README.md": b"x\n"}, b"probe\n")
    counts = identity_scan(repo.path, tip, allowlist, STAGE_S8).counts
    return counts.get("off-allowlist fields", 0) > 0


def control_licence(tree: Path, scratch: Path) -> bool:
    """A lockfile package with no verdict row must be a licence-audit finding."""
    control = scratch / "control-licence"
    inputs = ("THIRD_PARTY.md", "pyproject.toml", "shell/package.json", "shell/package-lock.json")
    for relative in inputs:
        target = control / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tree / relative, target)
    before = licence_audit(control).counts.get("findings", 0)
    lock = control / "shell" / "package-lock.json"
    text = lock.read_text(encoding="utf-8")
    anchor = '"packages": {'
    if anchor not in text:
        return False
    canary = anchor + '\n    "node_modules/flip-control-canary": {"version": "0.0.0"},'
    lock.write_text(text.replace(anchor, canary, 1), encoding="utf-8")
    after = licence_audit(control)
    return after.counts.get("exit") == EXIT_FAIL and after.counts.get("findings", 0) > before


def control_doc_sweep(scratch: Path) -> bool:
    """A tracked markdown file nothing references must ADD a doc-sweep finding.

    Compared against the same repository without the plant, because the sweep's
    own allowlists report entries a small tree does not carry - so "any finding"
    would be found whether or not the orphan rule works.
    """
    repo = ControlRepo(scratch / "control-docs")
    repo.commit({"README.md": b"# control\n"}, b"baseline\n")
    git(repo.path, ["checkout", "-q", "-f", "main"], env=repo.env)
    before = doc_sweep(repo.path).counts.get("findings", 0)
    repo.commit({"README.md": b"# control\n", "orphan.md": b"# orphan\n"}, b"plant\n")
    git(repo.path, ["checkout", "-q", "-f", "main"], env=repo.env)
    return doc_sweep(repo.path).counts.get("findings", 0) > before


def control_readme(scratch: Path, *, python: str | None = None) -> bool:
    """A README command that fails, and one that hangs without serving, must both fail."""
    tree = scratch / "control-readme"
    (tree / "scripts").mkdir(parents=True, exist_ok=True)
    (tree / "scripts" / "exits_three.py").write_bytes(b"raise SystemExit(3)\n")
    (tree / "scripts" / "hangs.py").write_bytes(b"import time\ntime.sleep(3600)\n")
    (tree / "README.md").write_bytes(
        b"```\npython scripts/exits_three.py\n```\n\n```\npython scripts/hangs.py\n```\n"
    )
    counts = readme_walk(tree, python=python, timeout=CONTROL_COMMAND_TIMEOUT).counts
    return counts.get("commands") == CONTROL_README_COMMANDS == counts.get("failed")


# --- the run ------------------------------------------------------------------


def scratch_root(repo: Path) -> Path:
    """A fresh scratch directory inside ``repo``'s git directory - never under home."""
    common = git(repo, ["rev-parse", "--git-common-dir"]).decode("utf-8").strip()
    base = (repo / common).resolve() / SCRATCH_DIRNAME
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="run-", dir=base))


def clone_at(repo: Path, sha: str, target: Path) -> Path:
    """A fresh clone of ``repo`` checked out, detached, at ``sha``, named relatively.

    Across two Windows drives the source is drive-anchored instead, never a home
    (:func:`_relative_or_anchored`).

    ``--no-hardlinks`` COPIES the object store (CS-1267). A local clone otherwise
    hard-links it, commit-graph included, and a concurrent git that has the
    source's commit-graph mapped then blocks removing the clone's name for the
    same file - the scratch removal failed and a run whose checks all passed
    exited 1.
    """
    source = _relative_or_anchored(repo, target.parent)
    git(target.parent, ["clone", "-q", "--no-checkout", "--no-hardlinks", source, target.name])
    git(target, ["checkout", "-q", "--detach", sha])
    return target


_MEASURE_ERRORS: Final = (FlipError, trailer_census.CensusError, OSError, RuntimeError, ValueError)


def measure(
    key: str, title: str, body: Callable[[], CheckResult], control: Callable[[], bool]
) -> CheckResult:
    """Run one check and its control; a step that could not be taken FAILS the check.

    Only the listed error types are turned into a failure here. Anything else -
    a child that would not die, an interrupt - escapes to :func:`main`, which
    ends the run with exit 2 or 130 and names the check id recorded below.
    """
    PHASE[0] = f"check {key}"
    try:
        result = body()
    except _MEASURE_ERRORS as exc:
        reason = getattr(exc, "reason", type(exc).__name__)
        result = CheckResult(key, title, failures=[f"could not measure: {reason}"])
    try:
        result.control = result.control or control()
    except _MEASURE_ERRORS:
        result.control = False
    return result


def run_all(
    repo: Path, sha: str, stage: str, scratch: Path, baseline: tuple[str, int] | None
) -> list[CheckResult]:
    """Run every automated half against ``sha``, each with its control."""
    needles = derive_needles()
    allowlist = derive_identity_allowlist(repo)
    tree = clone_at(repo, sha, scratch / "tree")
    fresh = clone_at(repo, sha, scratch / "fresh")
    return [
        measure(
            "1", "secret-scan", lambda: secret_scan(repo, sha), lambda: control_secret(scratch)
        ),
        measure(
            "2",
            "pii-scan",
            lambda: pii_scan(repo, sha, needles),
            lambda: control_pii(scratch, needles),
        ),
        measure(
            "3",
            "licence-audit",
            lambda: licence_audit(tree),
            lambda: control_licence(tree, scratch),
        ),
        measure(
            "4",
            "publisher-assets",
            lambda: publisher_scan(repo, sha),
            lambda: control_publisher(scratch),
        ),
        measure("5", "readme-walk", lambda: readme_walk(tree), lambda: control_readme(scratch)),
        measure("6", "doc-sweep", lambda: doc_sweep(tree), lambda: control_doc_sweep(scratch)),
        measure("7", "clean-checkout", lambda: clean_checkout(fresh, sha), lambda: False),
        measure(
            "T",
            "trailer-axis",
            lambda: trailer_axis(repo, sha, stage, baseline),
            lambda: control_trailer(scratch),
        ),
        measure(
            "I",
            "identity",
            lambda: identity_scan(repo, sha, allowlist, stage),
            lambda: control_identity(scratch, allowlist),
        ),
    ]


def final_line(results: Iterable[CheckResult]) -> str:
    """The closing line. Never a bare PASS - see the module docstring."""
    listed = list(results)
    failed = sum(1 for result in listed if not result.passed)
    verdict = "PASS" if listed and not failed else "FAIL"
    excluded = sum(result.counts.get("policy-excluded", 0) for result in listed)
    return (
        f"flip_checks: automated verdict {verdict} - {failed} of {len(listed)} automated "
        f"checks failed; policy-excluded {excluded}; "
        f"human halves NOT-RUN-HERE {len(HUMAN_HALVES)}; this run does not clear CS-G03 "
        "(ADR 0025)"
    )


def remove_tree(path: Path) -> bool:
    """Remove a scratch tree, clearing the read-only bit git sets on its objects.

    RETRIED, because on Windows a handle a just-stopped child held can outlive
    the child by a moment - measured once on this tool's own scratch tree, where
    the first removal failed and a second one a moment later succeeded. The
    scratch base is then removed too when no other run is using it.
    """

    def clear(function: Callable[[str], object], target: str, _exc: BaseException) -> None:
        Path(target).chmod(0o700)
        function(target)

    for _attempt in range(REMOVE_ATTEMPTS):
        try:
            shutil.rmtree(path, onexc=clear)
        except OSError:
            time.sleep(REMOVE_PAUSE_SECONDS)
            continue
        break
    with contextlib.suppress(OSError):
        path.parent.rmdir()
    return not path.exists()


def _scratch_name(scratch: Path, repo: Path) -> str:
    """The leftover scratch tree, named relative to ``repo`` so no home renders.

    Across two drives with no allowed absolute spelling, fixed text naming no
    path stands in (:func:`_relative_or_anchored`).
    """
    try:
        return Path(_relative_or_anchored(scratch, repo)).as_posix()
    except FlipError:
        return f"{SCRATCH_DIRNAME}/{scratch.name} in the git directory"


Runner = Callable[[Path, str, str, Path, "tuple[str, int] | None"], list[CheckResult]]


def main(argv: Sequence[str] | None = None, *, runner: Runner = run_all) -> int:
    """Resolve REF, run every check, print counts and SHAs, return the exit code.

    Args:
        argv: Arguments, without the program name; ``sys.argv`` when None.
        runner: What runs the checks. Injected by the tests, which never let a
            real needle derivation or a real save directory near this process.

    Returns:
        0, 1 or 2 per the module docstring.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("ref", help="the ref to grade; resolved once to a full SHA")
    parser.add_argument("--stage", required=True, choices=(STAGE_S1, STAGE_S8))
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help="the repository")
    parser.add_argument("--trailer-baseline-ref", default=None)
    parser.add_argument("--trailer-baseline-count", type=int, default=None)
    args = parser.parse_args(argv)
    PHASE[0] = "setup"
    # EVERY exception ends here, and none renders a traceback. A traceback prints
    # stdlib frames whose file paths carry the interpreter's install directory -
    # under a home directory on this machine - and an exception's own text can
    # carry a child's argv. So the only words printed are the phase and the
    # exception's TYPE (ADR 0025 decision item 3).
    try:
        return _run(args, runner)
    except KeyboardInterrupt:
        print(f"flip_checks: interrupted during {PHASE[0]}", file=sys.stderr)
        return EXIT_INTERRUPTED
    except BaseException as exc:
        name = type(exc).__name__
        print(f"flip_checks: could not run - {name} during {PHASE[0]}", file=sys.stderr)
        return EXIT_COULD_NOT_RUN


def _run(args: argparse.Namespace, runner: Runner) -> int:
    """The body of :func:`main`, after argument parsing."""
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        print("flip_checks: could not run - tier 3 runs locally only (ADR 0025)", file=sys.stderr)
        return EXIT_COULD_NOT_RUN
    if (args.trailer_baseline_ref is None) != (args.trailer_baseline_count is None):
        print("flip_checks: could not run - a baseline needs a ref and a count", file=sys.stderr)
        return EXIT_COULD_NOT_RUN
    baseline = (
        None
        if args.trailer_baseline_ref is None
        else (args.trailer_baseline_ref, args.trailer_baseline_count)
    )
    try:
        # Resolved ONCE, to its long real form, before any path arithmetic: an 8.3
        # short spelling beside the long-form scratch root makes a relative clone
        # source git refuses. Never printed.
        args.repo = Path(os.path.realpath(args.repo))
        sha = resolve_ref(args.repo, args.ref)
        scratch = scratch_root(args.repo)
    except FlipError as exc:
        print(f"flip_checks: could not run - {exc.reason}", file=sys.stderr)
        return EXIT_COULD_NOT_RUN
    print(f"flip_checks: ref {sha}")
    print(f"flip_checks: stage {args.stage}")
    try:
        results = runner(args.repo, sha, args.stage, scratch, baseline)
    except FlipError as exc:
        print(f"flip_checks: could not run - {exc.reason}", file=sys.stderr)
        return EXIT_COULD_NOT_RUN
    finally:
        # PHASE is left alone here: when an exception is unwinding, the phase it
        # escaped from is the one the last-resort handler must name.
        cleaned = remove_tree(scratch)
    PHASE[0] = "report"
    for result in results:
        for line in result.render():
            print(line)
    for key, owner in HUMAN_HALVES:
        print(f"check {key} human half: NOT-RUN-HERE - {owner}")
    if not cleaned:
        leftover = _scratch_name(scratch, args.repo)
        print(f"flip_checks: the scratch directory could not be removed - {leftover}")
    print(final_line(results))
    passed = cleaned and bool(results) and all(result.passed for result in results)
    return EXIT_PASS if passed else EXIT_FAIL


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(EXIT_INTERRUPTED)
