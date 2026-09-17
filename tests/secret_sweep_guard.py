"""CS-939 - the populations, the admission rule and the scans behind the sweep.

THIS MODULE DERIVES AND SCANS. IT JUDGES NOTHING. The arms and every control
live in ``tests/test_secret_sweep.py``; the split is the one every guard family
in this tree uses, and it keeps both halves under the size ceiling
``tests/data/test_phase2_gate.py`` holds every file under ``tests/`` to.

THE DEFECT. ``tools/precommit_gate.py`` runs over STAGED bytes or over
explicitly named files, so it can only ever see what is CHANGING NOW. Whatever
landed before it was wired is invisible to it forever, because nothing ever
re-reads what already landed.

NOTHING HERE IS RESTATED FROM THE GATE - NOT THE PATTERNS, NOT THE ADMISSION
RULE, NOT A SIZE CAP. :func:`admit` asks ``classify_for_read`` and
``accept_bytes`` what the gate itself would agree to scan, and the two checks
below are the gate's own ``check_secrets`` and ``check_charset``. A copy of any
of it would drift, and the arm
``test_the_sweep_reads_the_gates_own_pattern_list`` proves the absence of one
by substitution rather than by reading this source.

TWO CHECKS, BECAUSE THEY SHARE ONE ROOT CAUSE. Secrets are what the item asks
for. The charset rule is the same blindness wearing a different pattern - a
non-ASCII byte that landed before the gate existed is equally unreachable by a
staged-bytes check - so it is swept here rather than filed as a separate
discovery. CLAUDE.md non-negotiable 4 is the rule it answers.

TWO POPULATIONS, ANSWERING DIFFERENT QUESTIONS.

- THE TRACKED TREE is what a clone gets today.
- EVERY REACHABLE BLOB is what the object store still hands out, which is the
  only population that sees a credential a later commit removed. On a SHALLOW
  checkout this collapses to the tip tree - honest rather than a hole: the
  population is whatever the checkout reaches, an arm pins that it is never
  smaller than the tracked tree, and a full-history checkout (the pre-push
  hook, and tier 2's clean-checkout probe) sweeps the whole of it.

A SHA THAT IS COUNTED AND NOT READ IS THE FAILURE MODE THIS FILE GUARDS
AGAINST. A reader that quietly drops an object produces a report that is
byte-identical to a clean one, so :func:`blob_findings` RAISES on an object the
reader did not yield rather than scoring it clean.

NO FINDING CARRIES A MATCHED VALUE. ``Diagnostic.render`` spells the label, the
position and the RULE NAME, never the text it matched, so a red arm on a real
leak says where to look without copying the secret into a log.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections.abc import Callable, Iterable, Iterator, Sequence
from functools import cache
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: The tier-0 gate, loaded BY PATH rather than imported as
#: ``tools.precommit_gate``. That is this tree's standing idiom and it is
#: mechanical rather than stylistic: tools/ carries no ``__init__.py``, so a
#: package import puts the same source under two module names and the repo
#: -wide mypy gate refuses the tree outright. tests/test_precommit_gate.py
#: ::load_gate makes the same choice for the same reason.
GATE_PATH: Final = REPO_ROOT / "tools" / "precommit_gate.py"

#: Distinct from the name tests/test_precommit_gate.py registers, so neither
#: module can monkeypatch the other's copy out from under it.
GATE_MODULE_NAME: Final = "clockspeed_gate_for_sweep"


@cache
def gate() -> ModuleType:
    """Load the tier-0 gate from its path, once per process.

    Returns:
        The gate module. Every pattern, placeholder branch, size cap and
        admission rule this sweep applies is read off it at call time, so
        nothing here can drift from what actually blocks a commit.
    """
    spec = importlib.util.spec_from_file_location(GATE_MODULE_NAME, GATE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"the gate at {GATE_PATH.name} could not be loaded")
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module. The gate declares dataclasses under
    # `from __future__ import annotations`, and @dataclass resolves those
    # string annotations through sys.modules[cls.__module__] - an unregistered
    # module makes that lookup return None and the decorator raises inside the
    # class body.
    sys.modules[GATE_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


#: Seconds any one git call may take before it is treated as unavailable. The
#: object walk reads the whole store, so this sits well above the gate's own.
GIT_TIMEOUT: Final = 300

#: What the sweep calls itself when the gate asks where a unit came from.
ORIGIN: Final = "secret-sweep"

#: Fields in one ``git rev-list --objects`` line that names a path: the object
#: and the path. A line with one field is an object git named nothing for.
WALK_NAMED_FIELDS: Final = 2

#: Fields in one ``--batch-check`` answer this module reads: the object and its
#: type. Git writes more for some formats; the extras are ignored, not refused.
TYPE_FIELDS: Final = 2

#: Fields in a ``git cat-file --batch`` header: object, type and size. Any other
#: width means the stream has desynchronised and every later read is garbage.
BATCH_HEADER_FIELDS: Final = 3

BlobReader = Callable[[Sequence[str]], Iterable[tuple[str, bytes]]]
Check = Callable[[str, str, bytes], list[str]]


def _git(args: list[str]) -> bytes:
    """Run one git command from the repo root and return its stdout.

    Args:
        args: The git subcommand and its arguments, without ``git`` itself.

    Returns:
        Raw stdout.

    Raises:
        RuntimeError: When git cannot be run or exits non-zero. Silence here
            would make an empty population indistinguishable from a clean one,
            which is the exact fault this module exists to close.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT,
        )
    except OSError as exc:
        raise RuntimeError(f"git could not be run: {type(exc).__name__}") from None
    if result.returncode != 0:
        raise RuntimeError(f"git {args[0]} exited {result.returncode}")
    return result.stdout


@cache
def tracked_paths() -> tuple[str, ...]:
    """Every path git tracks, repo-relative and forward-slashed.

    Returns:
        The tracked paths, in git's own order.
    """
    listed = _git(["ls-files", "-z"]).decode("utf-8", errors="replace")
    return tuple(entry for entry in listed.split(chr(0)) if entry)


def admit(label: str, relative: str, data: bytes) -> bytes | None:
    """What the GATE would agree to scan of this item, or nothing.

    Args:
        label: What to call the item in a finding.
        relative: The path the item lives at, for its extension only.
        data: The item's bytes.

    Returns:
        The bytes to scan, or ``None`` when the gate itself would decline them -
        a known-binary extension, a size past the content cap, or a NUL sniff.
        THE RULE IS ASKED RATHER THAN REPRODUCED: a sweep that scanned what the
        gate skips would report findings no commit could ever have been blocked
        for, and one that skipped what the gate scans would be a hole.
    """
    report = gate().Report()
    ext = PurePosixPath(relative).suffix.lower()
    if not gate().classify_for_read(label, ext, report):
        return None
    unit = gate().Unit(label=label, origin=ORIGIN, ext=ext)
    if not gate().accept_bytes(unit, data, report):
        return None
    # Bound to a declared name rather than returned straight out. The gate is
    # loaded by path, so every attribute on it is Any to the type checker, and
    # the repo-wide gate refuses a function that returns one.
    admitted: bytes = unit.data
    return admitted


def secret_findings(label: str, relative: str, data: bytes) -> list[str]:
    """Every credential shape the gate's own rules find in one item.

    Args:
        label: What to call the item in a finding.
        relative: The path the item lives at, for its extension only.
        data: The item's bytes.

    Returns:
        One rendered diagnostic per finding.
    """
    admitted = admit(label, relative, data)
    if admitted is None:
        return []
    report = gate().Report()
    gate().check_secrets(label, admitted.decode("utf-8", errors="replace"), report)
    return [diag.render() for diag in report.diagnostics]


def charset_findings(label: str, relative: str, data: bytes) -> list[str]:
    """Every byte outside 7-bit ASCII the gate's own rule finds in one item.

    Args:
        label: What to call the item in a finding.
        relative: The path the item lives at, for its extension only.
        data: The item's bytes.

    Returns:
        One rendered diagnostic per finding.
    """
    admitted = admit(label, relative, data)
    if admitted is None:
        return []
    report = gate().Report()
    gate().check_charset(label, admitted, report)
    return [diag.render() for diag in report.diagnostics]


def scanned_paths(paths: Iterable[str], root: Path) -> tuple[str, ...]:
    """The subset of ``paths`` whose bytes the gate would actually read.

    Args:
        paths: Repo-relative candidate paths.
        root: The tree they are relative to.

    Returns:
        The paths a sweep reads. Two things narrow the list and both are real:
        ``git ls-files`` names a file deleted from the working tree but not yet
        staged, and :func:`admit` declines what the gate declines.
    """
    scanned: list[str] = []
    for relative in paths:
        target = root / relative
        if not target.is_file():
            continue
        if admit(relative, relative, target.read_bytes()) is not None:
            scanned.append(relative)
    return tuple(scanned)


def sweep_paths(paths: Iterable[str], root: Path, check: Check = secret_findings) -> list[str]:
    """Run one check over every readable file among ``paths``.

    Args:
        paths: Repo-relative candidate paths.
        root: The tree they are relative to. Injected so a control runs on a
            corpus of its own rather than on the repository it grades.
        check: Which of the gate's rules to apply.

    Returns:
        Every finding, in the order the paths were given.
    """
    findings: list[str] = []
    for relative in paths:
        target = root / relative
        if target.is_file():
            findings.extend(check(relative, relative, target.read_bytes()))
    return findings


@cache
def reachable_blobs() -> tuple[tuple[str, str], ...]:
    """Every blob reachable from every ref, with one path it is stored at.

    Returns:
        ``(sha, path)`` pairs, sorted, one per distinct blob. The path is the
        first git named for it and is used for its EXTENSION only - a blob that
        lives at several paths is one object and is scanned once.

    Raises:
        RuntimeError: Through :func:`_git`, when the walk cannot be taken.
    """
    walked = _git(["rev-list", "--objects", "--all"]).decode("utf-8", errors="replace")
    named: dict[str, str] = {}
    for line in walked.splitlines():
        fields = line.split(None, 1)
        if len(fields) == WALK_NAMED_FIELDS and fields[0] not in named:
            named[fields[0]] = fields[1].strip()
    if not named:
        return ()
    blobs = {sha for sha, kind in _batch_check(sorted(named)) if kind == "blob"}
    return tuple(sorted((sha, named[sha]) for sha in blobs))


def reachable_blob_shas() -> tuple[str, ...]:
    """Just the object names from :func:`reachable_blobs`.

    Returns:
        The blob shas, sorted.
    """
    return tuple(sha for sha, _path in reachable_blobs())


def _batch_check(shas: Sequence[str]) -> list[tuple[str, str]]:
    """Ask git the type of each object in one call.

    Args:
        shas: Object names.

    Returns:
        ``(sha, type)`` for each object git recognised.

    Raises:
        RuntimeError: When git cannot be run or exits non-zero.
    """
    try:
        result = subprocess.run(
            ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
            cwd=REPO_ROOT,
            input="\n".join(shas).encode("ascii"),
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT,
        )
    except OSError as exc:
        raise RuntimeError(f"git could not be run: {type(exc).__name__}") from None
    if result.returncode != 0:
        raise RuntimeError(f"git cat-file --batch-check exited {result.returncode}")
    typed: list[tuple[str, str]] = []
    for line in result.stdout.decode("ascii", errors="replace").splitlines():
        fields = line.split()
        if len(fields) >= TYPE_FIELDS:
            typed.append((fields[0], fields[1]))
    return typed


def read_blobs_from_git(shas: Sequence[str]) -> Iterator[tuple[str, bytes]]:
    """Stream each blob's bytes out of the object store, one process for all.

    Args:
        shas: Blob object names.

    Yields:
        ``(sha, bytes)`` in the order asked for.

    Raises:
        RuntimeError: When git cannot be started, or answers with a header this
            reader cannot parse - which would otherwise desynchronise the
            stream and make every later blob unreadable in silence.
    """
    if not shas:
        return
    try:
        proc = subprocess.Popen(
            ["git", "cat-file", "--batch"],
            cwd=REPO_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    except OSError as exc:
        raise RuntimeError(f"git could not be run: {type(exc).__name__}") from None
    if proc.stdin is None or proc.stdout is None:
        raise RuntimeError("git cat-file was started without the pipes it was asked for")
    try:
        for sha in shas:
            proc.stdin.write(f"{sha}\n".encode("ascii"))
            proc.stdin.flush()
            header = proc.stdout.readline().decode("ascii", errors="replace").split()
            if len(header) != BATCH_HEADER_FIELDS:
                raise RuntimeError(f"git cat-file answered {header!r} for {sha}")
            data = proc.stdout.read(int(header[2]))
            proc.stdout.read(1)
            yield sha, data
    finally:
        proc.stdin.close()
        proc.wait(timeout=GIT_TIMEOUT)


def blob_findings(
    blobs: Sequence[tuple[str, str]],
    check: Check = secret_findings,
    read: BlobReader | None = None,
) -> list[str]:
    """Run one check over every blob in ``blobs``.

    Args:
        blobs: ``(sha, path)`` pairs. The path supplies the extension only.
        check: Which of the gate's rules to apply.
        read: How to fetch the bytes. Injected so a control runs on a corpus of
            its own rather than writing an object into the store it grades.

    Returns:
        Every finding, in the order the reader yielded them.

    Raises:
        RuntimeError: When the reader did not yield every sha it was given. A
            dropped object would otherwise be counted and never scanned, and
            that report is byte-identical to a clean one.
    """
    reader = read_blobs_from_git if read is None else read
    at = dict(blobs)
    shas = [sha for sha, _path in blobs]
    findings: list[str] = []
    seen: set[str] = set()
    for sha, data in reader(shas):
        seen.add(sha)
        findings.extend(check(sha, at.get(sha, ""), data))
    missing = [sha for sha in shas if sha not in seen]
    if missing:
        raise RuntimeError(
            f"the blob reader did not yield {len(missing)} of {len(shas)} object(s), "
            f"first {missing[0]}"
        )
    return findings
