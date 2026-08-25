#!/usr/bin/env python3
"""Clockspeed drift guard - every guard, one consolidated verdict.

Guards, in the order they are reported:

  a  doc budgets         CONVENTIONS 2.1, delegated to tools/doc_budget.py by
                         import, never by shelling out, so there is one table.
  b  memory reachability every memory/*.md leaf except MEMORY.md is reachable
                         from MEMORY.md, directly or through an INDEX_<domain>.md.
                         CONVENTIONS 11 forbids unindexing a file to save bytes,
                         so an unreachable leaf is DRIFT, not a style point.
  c  character set       every tracked authored text file is pure 7-bit ASCII.
  d  doc topology        every file named in the CONVENTIONS section 2 ownership
                         table exists. The table is PARSED at runtime rather than
                         restated here, so the guard cannot drift from the doc.
  e  port record         config/ports.json parses, its band contains its base
                         port, and no allocation conflicts with another.
  f  frozen files        read out of CLAUDE.md and reported so the operator can
                         see what is protected. Never fails.
  g  dated sections      every dated heading classifies as a STATUS date - the
                         date leads the heading, so the section is historical -
                         or as a PROVENANCE date, which records when the text
                         was filed and marks the status not at all. A dated
                         heading fitting NEITHER idiom is drift.
  h  version pin         clockspeed/data/version.py is internally consistent -
                         its integrity checksum matches its own fields - and,
                         where an install is resolvable, matches the live docs
                         file. An UNRESOLVABLE install is never a failure: tier
                         1 runs this on a runner with no game, so the pin's own
                         checksum is what makes a hand-edit detectable there.
                         Repair with --re-extract.
  i  work-item owners   every CS- work item is recorded in exactly one owner
                         file. The owner files are PARSED out of the CLAUDE.md
                         sentence that declares them, and ownership means an
                         ENTRY rather than a mention. On the ledger side an ID
                         is owned only once its newest record is a CLOSURE -
                         a grant is recorded BEFORE the edit it authorises, so
                         keying on any mention marks open items closed, and a
                         record forgives only the ids it names. Anything the
                         scan could not read is UNACCOUNTED and red.

Exits non-zero on any DRIFT.

WHY THE SKIP LIST PRINTS EVERY RUN, NOT ONLY WHEN VERBOSE:
CONVENTIONS 15.1 names the failure class - "a guard can be green while
self-excusing, skipping itself on the very files it is meant to cover". A green
verdict is only meaningful next to the list of what was never looked at. If that
list is long, or holds something surprising, the green is worth nothing.

Usage:
    python tools/drift_guard.py
    python tools/drift_guard.py --json
    python tools/drift_guard.py --re-extract
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import logging
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NamedTuple

# --- enumeration policy -----------------------------------------------------

WALK_SKIP_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".idea",
        ".vs",
    }
)

# Root-level directories holding generated or gitignored content. Not authored,
# so the character-set guard does not own them.
WALK_SKIP_ROOT_DIRS = frozenset({"data"})

TEXT_SUFFIXES = frozenset(
    {
        ".py",
        ".pyi",
        ".md",
        ".markdown",
        ".json",
        ".jsonc",
        ".txt",
        ".yml",
        ".yaml",
        ".toml",
        ".cfg",
        ".ini",
        ".ps1",
        ".psm1",
        ".sh",
        ".bash",
        ".bat",
        ".cmd",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sql",
        ".rst",
        ".xml",
        ".svg",
        ".gitignore",
        ".gitattributes",
        ".rgignore",
        ".editorconfig",
    }
)

TEXT_NAMES = frozenset(
    {
        ".gitignore",
        ".gitattributes",
        ".rgignore",
        ".editorconfig",
        ".gitmodules",
        "LICENSE",
        "NOTICE",
        "Makefile",
        "Dockerfile",
        "py.typed",
        "requirements.txt",
    }
)

MAX_ASCII = 126
BYTE_LF = 0x0A
FIRST_PRINTABLE = 0x20
ALLOWED_CONTROL = frozenset({0x09, 0x0A, 0x0D})
MAX_HITS_PER_FILE = 3

# WHY THESE USE A DIGIT LOOKAROUND AND NOT ``\b`` (CS-840). An underscore is a
# word character, so ``\b`` finds NO boundary in ``_2026-08-23_`` and the date
# was invisible to this guard - a leading status date could be smuggled past it
# by italicising the date. The real hazard a boundary guards against is
# splitting a longer run of digits, so the lookaround tests for a DIGIT and
# nothing else. Markdown emphasis, brackets and backticks now fall outside the
# token instead of hiding it.
#
# WHY THE MONTH-NAME PATTERN REQUIRES THE YEAR TO BE THE MONTH'S OWN (CS-840).
# The gap here was ``[^\n]{0,12}``, which let any twelve characters sit between
# a month name and a year: "This May need 2031 rework" was read as a date and
# reddened a heading carrying none. A year now has to follow the month
# directly, or follow a day number that follows the month.
DATE_PATTERNS = (
    re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)"),
    re.compile(r"(?<!\d)\d{1,2}/\d{1,2}/\d{2,4}(?!\d)"),
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September"
        r"|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept"
        r"|Oct|Nov|Dec)\b[ \t]*,?[ \t]*(?:\d{1,2}(?:st|nd|rd|th)?[ \t]*,?[ \t]*)?"
        r"\d{4}(?!\d)"
    ),
)

_GUARD_HEADERS = ("GUARD", "NAME", "VERDICT")

Guard = dict[str, Any]
Skip = dict[str, str]


def repo_root() -> Path:
    """Return the repository root, derived from this file's location."""
    return Path(__file__).resolve().parents[1]


def _load_doc_budget() -> Any:
    """Import the budget table by module, not by subprocess. One source."""
    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    # PLC0415: the import has to follow the sys.path insert above, and this
    # module must stay runnable as a bare script from any working directory.
    import doc_budget  # noqa: PLC0415

    return doc_budget


def _this_checkout() -> Path:
    """Return THIS file's own repository root, never the root under audit.

    Deliberately not :func:`repo_root`, even though the two are the same
    expression today. Guard (h) reads the PIN out of the root it was pointed
    at, but it must take the CODE that validates a pin from the checkout this
    script belongs to - otherwise auditing a tree would mean executing that
    tree's own validator to grade itself.

    Returns:
        The repository root containing this file.
    """
    return Path(__file__).resolve().parents[1]


def _load_pin_support() -> tuple[Any, Any, Any]:
    """Import the pin module, the resolver and the docs loader. One source.

    By module import, never by subprocess, for the same reason
    :func:`_load_doc_budget` is: a second implementation of any of these is a
    second answer waiting to disagree with the first. tools/ importing
    clockspeed/ is the correct direction (docs/ARCHITECTURE.md); the reverse
    never happens.

    Returns:
        (clockspeed.data.version, clockspeed.data.locate,
        clockspeed.data.docs_extract).

    Raises:
        ImportError: The package is not importable from this checkout.
    """
    root = _this_checkout()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    # PLC0415: the import has to follow the sys.path insert above, and this
    # module must stay runnable as a bare script from any working directory.
    from clockspeed.data import docs_extract, locate, version  # noqa: PLC0415

    return version, locate, docs_extract


def _load_locate() -> Any:
    """Import the resolver and redactor alone, without the rest of the layer.

    Narrower than :func:`_load_pin_support` on purpose. Redaction has to work
    on the path where the version pin, the docs loader or anything else in the
    data layer is broken or absent - that is exactly when messages get printed
    - so it must not be reachable only through an import that drags two more
    modules in with it.

    Returns:
        The clockspeed.data.locate module.

    Raises:
        ImportError: The package is not importable from this checkout.
    """
    root = _this_checkout()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    # PLC0415: the import has to follow the sys.path insert above, and this
    # module must stay runnable as a bare script from any working directory.
    from clockspeed.data import locate  # noqa: PLC0415

    return locate


def _redact(text: object) -> str:
    """Render anything path-bearing with the personal data taken out.

    FAILS CLOSED. If the redactor cannot be imported this returns a fixed
    token rather than the raw text. A tool that prints an unredacted home path
    whenever an unrelated import breaks is a tool that leaks on exactly the
    bad day, and CLAUDE.md non-negotiable 12 admits no "only when something
    else went wrong" exception. Restating a second redactor here as a fallback
    would be worse still - two redactors are two answers waiting to disagree.

    Args:
        text: Anything renderable.

    Returns:
        The redacted rendering, or a withheld-marker.
    """
    try:
        locate = _load_locate()
    except ImportError:
        return "<withheld: the redactor is not importable from this checkout>"
    return str(locate.redact(text))


def _exc_text(exc: BaseException) -> str:
    """Render an exception with no filename and no unredacted path in it.

    THE ROOT CAUSE, stated once here so the seven call sites do not each have
    to restate it: ``str()`` on a Windows OSError appends the filename it
    failed on - "[Errno 13] Permission denied: '<a path>'" - while
    ``strerror`` carries the reason alone. An error message is an echo path
    exactly like a debug dump or a hex preview (CLAUDE.md non-negotiable 12),
    so every guard that reports a failed read has to strip it.

    Non-OSError exceptions go through the redactor too rather than being
    trusted. An ImportError names the module FILE it could not load, which on
    a checkout under a home directory is an absolute path with the account
    name in it.

    Args:
        exc: The exception being reported.

    Returns:
        A rendering safe to print, never empty - an OSError with no strerror
        falls back to the class name rather than to nothing, because a skip
        record whose reason is blank tells the reader less than nothing.
    """
    if isinstance(exc, OSError):
        return _redact(exc.strerror or type(exc).__name__)
    return _redact(str(exc) or type(exc).__name__)


def _load_verify_env() -> Any:
    """Import the build-string reader from scripts/verify_env.py.

    The build string is a property of the installed binaries and that script
    already reads it, through the PE version resource with two fallbacks.
    Reimplementing it here would be a second answer to "which build is this".

    Returns:
        The verify_env module.

    Raises:
        ImportError: The script is not importable from this checkout.
    """
    scripts_dir = _this_checkout() / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import verify_env  # noqa: PLC0415

    return verify_env


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _guard(guard_id: str, name: str, status: str, detail: list[str]) -> Guard:
    return {"id": guard_id, "name": name, "status": status, "detail": detail}


# --- file enumeration -------------------------------------------------------


def _git_ls_files(root: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    return [entry for entry in (proc.stdout or "").split("\x00") if entry]


def _walk(root: Path) -> tuple[list[Path], list[Skip]]:
    files: list[Path] = []
    skips: list[Skip] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError as exc:
            skips.append(
                {"path": _rel(root, current), "reason": f"unreadable directory: {_exc_text(exc)}"}
            )
            continue
        for entry in entries:
            try:
                is_dir = entry.is_dir()
            except OSError:
                continue
            if not is_dir:
                files.append(entry)
            elif entry.name in WALK_SKIP_DIRS:
                skips.append(
                    {
                        "path": _rel(root, entry) + "/",
                        "reason": "excluded directory (tooling or vcs internals)",
                    }
                )
            elif entry.parent == root and entry.name in WALK_SKIP_ROOT_DIRS:
                skips.append(
                    {
                        "path": _rel(root, entry) + "/",
                        "reason": "generated artifact directory, gitignored, not authored",
                    }
                )
            else:
                stack.append(entry)
    return files, skips


def enumerate_files(root: Path) -> tuple[list[Path], str, list[Skip]]:
    """Return (candidate files, how they were enumerated, skip records).

    Prefers the git index. A repo with zero commits still has an index once
    something is staged; a repo with nothing staged yields an empty list, and
    that is NOT an error - it falls back to a directory walk. Handling the
    zero-commit case is the point: the scaffold runs before commit one exists.
    """
    skips: list[Skip] = []
    tracked = _git_ls_files(root)
    if tracked:
        files = []
        for relative in tracked:
            path = root / relative
            if path.is_file():
                files.append(path)
            else:
                skips.append({"path": relative, "reason": "in the git index but not on disk"})
        return files, f"git ls-files ({len(tracked)} entries)", skips

    files, walk_skips = _walk(root)
    skips.extend(walk_skips)
    return files, "directory walk (git index empty - no commits, nothing staged)", skips


def _classify(path: Path) -> tuple[bool, str]:
    if path.name in TEXT_NAMES:
        return True, ""
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True, ""
    if path.suffix == "" and ".githooks" in path.parts:
        return True, ""
    return False, f"not an authored text file type ({path.suffix or 'no extension'})"


# --- guard c: character set -------------------------------------------------


def _ascii_violations(path: Path) -> tuple[list[str], str]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [], f"unreadable: {_exc_text(exc)}"
    line = 1
    column = 1
    hits: list[str] = []
    for byte in data:
        if byte == BYTE_LF:
            line += 1
            column = 1
            continue
        if byte > MAX_ASCII or (byte < FIRST_PRINTABLE and byte not in ALLOWED_CONTROL):
            hits.append(f"line {line} col {column}: byte 0x{byte:02X}")
            if len(hits) >= MAX_HITS_PER_FILE:
                break
        column += 1
    return hits, ""


def guard_charset(root: Path, files: list[Path], source: str) -> tuple[Guard, list[Skip]]:
    """Assert every authored text file is pure 7-bit ASCII."""
    skips: list[Skip] = []
    checked = 0
    offenders: list[str] = []
    for path in files:
        ok, reason = _classify(path)
        if not ok:
            skips.append({"path": _rel(root, path), "reason": reason})
            continue
        hits, error = _ascii_violations(path)
        if error:
            skips.append({"path": _rel(root, path), "reason": error})
            continue
        checked += 1
        if hits:
            offenders.append(f"{_rel(root, path)} -> {'; '.join(hits)}")

    name = "character set (7-bit ASCII)"
    detail = [f"enumeration: {source}", f"text files checked: {checked}"]
    if offenders:
        detail.append(f"non-ASCII or control bytes in {len(offenders)} file(s):")
        detail.extend(f"  {line}" for line in offenders)
        return _guard("c", name, "FAIL", detail), skips
    if checked == 0:
        detail.append("nothing was checked - this guard proved nothing on this run")
        return _guard("c", name, "WARN", detail), skips
    return _guard("c", name, "PASS", detail), skips


# --- guard b: memory reachability -------------------------------------------

_WIKILINK = re.compile(r"\[\[([^\]|#]+)")
_MDLINK = re.compile(r"\]\(([^)\s]+)")
_BACKTICK = re.compile(r"`([^`\n]+)`")


def _link_targets(text: str) -> set[str]:
    tokens: set[str] = set()
    for pattern in (_WIKILINK, _MDLINK, _BACKTICK):
        for match in pattern.finditer(text):
            raw = match.group(1).strip().split("#", 1)[0].replace("\\", "/").rstrip("/")
            if not raw:
                continue
            stem = raw.rsplit("/", 1)[-1]
            if stem.lower().endswith(".md"):
                stem = stem[:-3]
            tokens.add(stem.lower())
    return tokens


def _reachable_from_index(memory_dir: Path, index: Path, skips: list[Skip]) -> set[str]:
    """Tokens reachable from the index, transitively through INDEX_*.md files."""
    reachable: set[str] = set()
    frontier = [index]
    visited: set[str] = set()
    while frontier:
        current = frontier.pop()
        key = current.name.lower()
        if key in visited:
            continue
        visited.add(key)
        try:
            text = current.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            skips.append({"path": current.name, "reason": f"unreadable index: {_exc_text(exc)}"})
            continue
        for token in _link_targets(text):
            reachable.add(token)
            if token.startswith("index_"):
                candidate = memory_dir / f"{token}.md"
                if candidate.is_file():
                    frontier.append(candidate)
    return reachable


def guard_memory(root: Path) -> tuple[Guard, list[Skip]]:
    """Assert every memory leaf is reachable from the memory index."""
    skips: list[Skip] = []
    name = "memory reachability"
    memory_dir = root / "memory"
    if not memory_dir.is_dir():
        skips.append({"path": "memory/", "reason": "directory absent - reachability unevaluated"})
        return _guard("b", name, "WARN", ["memory/ does not exist yet"]), skips

    index = memory_dir / "MEMORY.md"
    leaves = sorted(path for path in memory_dir.glob("*.md") if path.name != "MEMORY.md")
    detail = [f"leaves: {len(leaves)}"]

    if not index.is_file():
        detail.append("memory/MEMORY.md is ABSENT - every leaf is unreachable")
        detail.append(
            "CONVENTIONS 11 requires every memory to be reachable from the index; "
            "with no index there is nothing to be reachable from"
        )
        detail.extend(f"  unreachable: {_rel(root, leaf)}" for leaf in leaves)
        return _guard("b", name, "FAIL" if leaves else "WARN", detail), skips

    reachable = _reachable_from_index(memory_dir, index, skips)
    unreachable = [leaf for leaf in leaves if leaf.stem.lower() not in reachable]
    detail.append(
        "reachable from MEMORY.md (transitively through INDEX_*.md): "
        f"{len(leaves) - len(unreachable)}"
    )
    if unreachable:
        detail.append("UNREACHABLE - this is DRIFT, not a style point:")
        detail.extend(f"  {_rel(root, leaf)}" for leaf in unreachable)
        detail.append(
            "Fix by adding a one-line hook to the index. Do NOT delete the leaf and "
            "do NOT unindex a file to save bytes (CONVENTIONS 11)."
        )
        return _guard("b", name, "FAIL", detail), skips
    return _guard("b", name, "PASS", detail), skips


# --- guard d: doc topology --------------------------------------------------


def _topology_entries(root: Path) -> list[str] | None:
    """Parse the ownership table out of CONVENTIONS section 2 at runtime."""
    path = root / "CONVENTIONS.md"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^##\s+2\.\s", line):
            start = index
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith(("## ", "### ")):
            end = index
            break

    entries: list[str] = []
    for line in lines[start:end]:
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells:
            continue
        match = re.fullmatch(r"`([^`]+)`", cells[0])
        if match:
            entries.append(match.group(1))
    return entries


def guard_topology(root: Path) -> tuple[Guard, list[Skip]]:
    """Assert every owner file named in the CONVENTIONS section 2 table exists."""
    skips: list[Skip] = []
    name = "doc topology"
    entries = _topology_entries(root)
    if entries is None:
        skips.append(
            {"path": "CONVENTIONS.md", "reason": "unreadable or section 2 table not parseable"}
        )
        return (
            _guard("d", name, "WARN", ["CONVENTIONS.md section 2 table could not be parsed"]),
            skips,
        )

    present: list[str] = []
    missing: list[str] = []
    for entry in entries:
        target = root / entry.rstrip("/")
        exists = target.is_dir() if entry.endswith("/") else target.is_file()
        (present if exists else missing).append(entry)

    detail = [
        f"ownership table entries parsed from CONVENTIONS section 2: {len(entries)}",
        f"present: {len(present)}",
    ]
    if missing:
        detail.append("MISSING owner files - facts named in the table have nowhere to live:")
        detail.extend(f"  {entry}" for entry in missing)
        return _guard("d", name, "FAIL", detail), skips
    return _guard("d", name, "PASS", detail), skips


# --- guard e: port record ---------------------------------------------------


def _allocation_problems(
    allocations: object, start: int, end: int
) -> tuple[dict[int, str], list[str]]:
    problems: list[str] = []
    allocated: dict[int, str] = {}
    if not isinstance(allocations, dict):
        return allocated, ["allocations is not an object"]
    for key, purpose in allocations.items():
        try:
            port = int(key)
        except (TypeError, ValueError):
            problems.append(f"allocation key {key!r} is not a port number")
            continue
        if port in allocated:
            problems.append(f"port {port} is allocated twice")
        allocated[port] = str(purpose)
        if not start <= port <= end:
            problems.append(f"allocated port {port} falls outside the band")
    return allocated, problems


def _reserved_problems(
    entries: object, allocated: dict[int, str], start: int, end: int
) -> tuple[list[int], list[str]]:
    problems: list[str] = []
    reserved: list[int] = []
    if not isinstance(entries, list):
        return reserved, ["reserved is not a list"]
    for item in entries:
        raw = item.get("port") if isinstance(item, dict) else item
        unusable = f"reserved entry {item!r} has no usable port number"
        # THE None CASE IS SPLIT OUT OF THE HANDLER DELIBERATELY. int(None)
        # raises TypeError and the except below would catch it, so this is not
        # a behaviour fix - but a caught exception is not a proof the type
        # checker can read, and `raw` is Any | None here because a dict with no
        # "port" key is exactly how the None arrives. The handler still covers
        # everything else: a non-numeric string raises ValueError, a list raises
        # TypeError, and both still land on the same message.
        if raw is None:
            problems.append(unusable)
            continue
        try:
            port = int(raw)
        except (TypeError, ValueError):
            problems.append(unusable)
            continue
        if port in reserved:
            problems.append(f"port {port} is reserved twice")
        reserved.append(port)
        if not start <= port <= end:
            problems.append(f"reserved port {port} falls outside the band")
        if port in allocated:
            problems.append(f"port {port} is both allocated and reserved")
    return reserved, problems


def guard_ports(root: Path) -> tuple[Guard, list[Skip]]:
    """Assert the port record parses and holds no conflicting allocation."""
    skips: list[Skip] = []
    name = "port record"
    path = root / "config" / "ports.json"
    if not path.is_file():
        skips.append({"path": "config/ports.json", "reason": "absent - port record unevaluated"})
        return _guard("e", name, "FAIL", ["config/ports.json does not exist"]), skips
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return _guard(
            "e", name, "FAIL", [f"config/ports.json does not parse: {_exc_text(exc)}"]
        ), skips

    band = payload.get("band") or {}
    try:
        start = int(band["start"])
        end = int(band["end"])
        base = int(payload["base"])
    except (KeyError, TypeError, ValueError):
        detail = ["base, band.start or band.end is missing or not an integer"]
        return _guard("e", name, "FAIL", detail), skips

    problems: list[str] = []
    if end < start:
        problems.append(f"band is inverted: start {start} > end {end}")
    if not start <= base <= end:
        problems.append(f"band {start}-{end} does not contain the base port {base}")

    allocated, allocation_problems = _allocation_problems(payload.get("allocations"), start, end)
    reserved, reserved_problems = _reserved_problems(payload.get("reserved"), allocated, start, end)
    problems.extend(allocation_problems)
    problems.extend(reserved_problems)

    detail = [
        f"base {base}, band {start}-{end} ({end - start + 1} ports)",
        f"allocations: {len(allocated)}, reserved: {len(reserved)}",
    ]
    covered = set(allocated) | set(reserved)
    uncovered = [port for port in range(start, end + 1) if port not in covered]
    if uncovered:
        listed = ", ".join(str(port) for port in uncovered)
        detail.append(f"ports in the band with no record: {listed}")

    if problems:
        detail.append("CONFLICTS:")
        detail.extend(f"  {problem}" for problem in problems)
        return _guard("e", name, "FAIL", detail), skips
    if uncovered:
        return _guard("e", name, "WARN", detail), skips
    return _guard("e", name, "PASS", detail), skips


# --- guard f: frozen files --------------------------------------------------


def _frozen_section(lines: list[str]) -> list[str] | None:
    start = None
    for index, line in enumerate(lines):
        if line.startswith("## ") and "frozen" in line.lower():
            start = index
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return lines[start:end]


def _frozen_patterns(section: list[str]) -> list[str]:
    patterns: list[str] = []
    for line in section:
        stripped = line.strip()
        if not stripped.startswith(("-", "*")):
            continue
        match = re.search(r"`([^`]+)`", stripped)
        if match:
            patterns.append(match.group(1))
    return patterns


def _frozen_detail(root: Path, patterns: list[str]) -> list[str]:
    detail: list[str] = []
    for pattern in patterns:
        if any(char in pattern for char in "*?["):
            try:
                matches = sorted(_rel(root, p) for p in root.glob(pattern) if p.is_file())
            except (OSError, ValueError):
                matches = []
            listed = f": {', '.join(matches)}" if matches else ""
            detail.append(f"  {pattern} -> {len(matches)} file(s) match{listed}")
        else:
            state = "present" if (root / pattern).exists() else "not yet on disk"
            detail.append(f"  {pattern} -> {state}")
    return detail


def guard_frozen(root: Path) -> tuple[Guard, list[Skip]]:
    """Report the frozen-file list out of CLAUDE.md. Never fails."""
    skips: list[Skip] = []
    name = "frozen files (report only)"
    path = root / "CLAUDE.md"
    if not path.is_file():
        skips.append({"path": "CLAUDE.md", "reason": "absent - frozen list not readable"})
        return _guard("f", name, "WARN", ["CLAUDE.md does not exist"]), skips
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        skips.append(
            {"path": "CLAUDE.md", "reason": f"unreadable - frozen list not read: {_exc_text(exc)}"}
        )
        return _guard("f", name, "WARN", [f"CLAUDE.md unreadable: {_exc_text(exc)}"]), skips

    section = _frozen_section(lines)
    if section is None:
        skips.append({"path": "CLAUDE.md", "reason": "no frozen-file section to read"})
        return _guard("f", name, "WARN", ["no frozen-file section in CLAUDE.md"]), skips

    patterns = _frozen_patterns(section)
    detail = ["these require explicit operator approval to modify (CLAUDE.md frozen list):"]
    detail.extend(_frozen_detail(root, patterns))
    if not patterns:
        detail.append("  (section found but it holds no backticked entries)")
    detail.append(
        "This guard never fails. Enforcement is the adjudicator route plus a ledger "
        "grant, not a file check."
    )
    return _guard("f", name, "PASS", detail), skips


# --- guard g: dated sections ------------------------------------------------
#
# CS-840. A dated heading used to mean exactly one thing - "this section is
# historical" - and the arm that found them REPORTED the population instead of
# failing on it. That is how CLAUDE.md's dated-heading rule and
# docs/item_notes.md's live-instruction header contradicted each other for as
# long as they did: a guard that reports cannot lose, so the contradiction had
# no cost until somebody acted on the wrong half of it.
#
# THE OPERATOR RULED THAT SHAPE DECIDES what a date MEANS:
#
#   STATUS      the date is in the LEADING position - the heading opens with
#               it - or it follows a verb declaring the subject reached a
#               terminal state. The section IS historical.
#   PROVENANCE  the date follows a filing or measurement verb, or a numbered
#               session. It records WHEN the text was filed, moved or
#               measured. It marks the section's status NOT AT ALL.
#
# THE VOCABULARY IS CLOSED. A dated heading matching neither family is DRIFT.
# Silently absorbing a new idiom is what the old arm did; making its author say
# which family it belongs to is the repair.
#
# CLASSIFYING WAS NOT ENOUGH, AND THIS IS THE DEFECT AN ADVERSARY FOUND. The
# first build failed only when classification returned None, so a STATUS
# classification was a PASS outcome - and nine plants of a leading status date
# into live files all left this guard at exit 0. The guard could not redden for
# the one thing CS-840 exists to catch: a LIVE section marked historical by its
# own heading.
#
# SO A FILE DECLARES ITS OWN STATUS AND THIS GUARD READS THE DECLARATION. That
# is NOT the per-file list the operator rejected. A list lives in code, is
# hand-maintained, and rots the moment a file is renamed, split or archived -
# the list and the file drift apart because nothing binds them. A DECLARATION
# lives inside the file it describes: it is moved by the same edit that moves
# the file, deleted by the same edit that deletes it, and read by the same
# person who reads the header. It cannot drift from its subject because it has
# no separate existence. Most of these files already said this in prose; the
# declaration only makes the sentence machine-readable.
#
#   A STATUS DATE INSIDE A FILE THAT DECLARES ITSELF LIVE IS DRIFT.
#
# A file with dated headings and NO declaration is recorded as a SKIP rather
# than failed. The live arm has nothing to grade there, and CONVENTIONS 15.1
# is explicit that a guard which cannot look must SAY so rather than pass
# quietly. The tracked tree's completeness - that every dated file declares -
# is asserted by the suite against the real tree, which is where this project
# already puts its real-tree invariants.


STATUS_DATE = "status"
PROVENANCE_DATE = "provenance"

LIVE = "LIVE"
HISTORICAL = "HISTORICAL"

# The declaration, as it appears in the header of a file that carries dated
# headings. Read only from the header - the region before the first level-2
# heading - so a quotation of the sentence further down the file cannot be
# mistaken for the file's own declaration.
STATUS_DECLARATION = re.compile(r"^\*\*Section status:[ \t]*(LIVE|HISTORICAL)\b", re.MULTILINE)

_HEADING_MARK = re.compile(r"^#+[ \t]*")

# Markdown emphasis and brackets wrapped around a leading date. The operator's
# ruling is about POSITION, and "**2026-08-23** - CS-901" opens with its date
# exactly as "2026-08-23 - CS-901" does. Stripping the decoration is what makes
# the code honour the ruling it claims to implement.
_LEADING_DECORATION = re.compile(r"^[\s*_`~\"'([{<]+")

# Filing, relocation and measurement verbs, plus the numbered-session ordinal.
# A date after one of these says when the text arrived or when the reading was
# taken - never what the section's status is now.
PROVENANCE_IDIOMS = (
    re.compile(r"\brelocated\b", re.IGNORECASE),
    re.compile(r"\bmoved\b", re.IGNORECASE),
    re.compile(r"\bfiled\b", re.IGNORECASE),
    re.compile(r"\barchived\b", re.IGNORECASE),
    re.compile(r"\brecorded\b", re.IGNORECASE),
    re.compile(r"\bmeasured\b", re.IGNORECASE),
    re.compile(r"\bprobed\b", re.IGNORECASE),
    re.compile(r"\bobserved\b", re.IGNORECASE),
    re.compile(r"\boperator[ \t]+(?:decision|ruling)\b", re.IGNORECASE),
    re.compile(r"\bsession[ \t]+\d+\b", re.IGNORECASE),
)

# Terminal-state verbs. A date after one of these dates the state change, so
# the section it heads is historical for the same reason a leading date is.
STATUS_IDIOMS = (
    re.compile(r"\bclosed\b", re.IGNORECASE),
    re.compile(r"\bsuperseded\b", re.IGNORECASE),
    re.compile(r"\bretired\b", re.IGNORECASE),
    re.compile(r"\bwithdrawn\b", re.IGNORECASE),
)

DATE_IDIOMS = PROVENANCE_IDIOMS + STATUS_IDIOMS

# THE DATE HAS TO BE THE VERB'S OWN OBJECT (CS-840). Matching a verb anywhere
# before the date let "closed" the ADJECTIVE claim a date it had nothing to do
# with - "The closed vocabulary and its fence - reviewed 2031-02-03" read as a
# status date, which is this project's own idiom for a bounded set. So the gap
# between the verb and the date may hold only connective words and the name of
# a file being moved. Any other prose in the gap means the verb is not
# governing the date, the heading classifies as NEITHER, and its author is
# asked which family it belongs to.
_GAP_CONNECTIVES = frozenset(
    {"from", "to", "on", "in", "into", "out", "of", "by", "at", "as", "via", "continued"}
)
_PATH_TOKEN = re.compile(r"`[^`]*`|\b[\w-]+\.[A-Za-z]{2,4}\b|\b[\w.-]+/[\w./-]+\b")
_GAP_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


def _date_position(text: str) -> int | None:
    """Return where the EARLIEST date in ``text`` starts, or None if there is none.

    Args:
        text: One line.

    Returns:
        The start offset of the first date, or None.
    """
    starts = []
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match is not None:
            starts.append(match.start())
    return min(starts) if starts else None


def dated_headings(text: str) -> list[tuple[int, str]]:
    """Return (line number, heading) for every heading in ``text`` carrying a date.

    The one implementation of "this heading is dated". Guard (g) grades what
    this yields and the suite derives its population from it, so a second scan
    written somewhere else cannot disagree with the one being graded.

    Args:
        text: A whole markdown document.

    Returns:
        One row per dated heading, in file order.
    """
    return [
        (number, line.rstrip())
        for number, line in enumerate(text.splitlines(), start=1)
        if line.startswith("#") and _date_position(line) is not None
    ]


def heading_lead_in(heading: str) -> str | None:
    """Return the text a heading places BEFORE its date, stripped of decoration.

    THE ONLY REGION THE CLASSIFIER EVER CONSULTS, exposed so that a control
    grading the vocabulary reads the same region rather than the whole heading.
    A verb appearing only in a heading's TAIL - after the date - can never
    affect classification, so a control that searched whole headings would
    report a spare entry as dead weight.

    Args:
        heading: One heading line, with or without its leading hash marks.

    Returns:
        The lead-in, empty when the date is in the leading position, or None
        when the heading carries no date at all.
    """
    body = _LEADING_DECORATION.sub("", _HEADING_MARK.sub("", heading)).strip()
    at = _date_position(body)
    if at is None:
        return None
    return body[:at]


def _governs_the_date(gap: str) -> bool:
    """Is a verb ending ``gap`` chars before a date actually governing that date?

    Args:
        gap: The text between the end of the verb and the start of the date.

    Returns:
        True when the gap holds only connectives and file names.
    """
    remainder = _PATH_TOKEN.sub(" ", gap)
    return all(word.lower() in _GAP_CONNECTIVES for word in _GAP_WORD.findall(remainder))


def classify_dated_heading(heading: str) -> str | None:
    """Classify a heading's date by SHAPE as a status date or a provenance date.

    A verb qualifies only if it GOVERNS the date - see ``_governs_the_date``.
    Among qualifying verbs the nearest one wins, which is deterministic and
    needs no precedence table; in practice the governing rule leaves at most
    one. The nearest-verb rule no longer carries the weight it did: a heading
    reworded so that a status verb captures the date is now caught by the
    live-file arm in ``guard_dated`` rather than having to be caught here.

    Args:
        heading: One heading line, with or without its leading hash marks.

    Returns:
        ``STATUS_DATE``, ``PROVENANCE_DATE``, or None. None covers two cases
        that only the caller can tell apart: a heading carrying no date at
        all, and a dated heading whose idiom the closed vocabulary does not
        cover. Guard (g) knows the heading was dated, so guard (g) is what
        turns the second case into drift.
    """
    lead = heading_lead_in(heading)
    if lead is None:
        return None
    if not lead:
        return STATUS_DATE

    nearest: tuple[int, str] | None = None
    for family, patterns in ((PROVENANCE_DATE, PROVENANCE_IDIOMS), (STATUS_DATE, STATUS_IDIOMS)):
        for pattern in patterns:
            for match in pattern.finditer(lead):
                if not _governs_the_date(lead[match.end() :]):
                    continue
                if nearest is None or match.end() > nearest[0]:
                    nearest = (match.end(), family)
    return nearest[1] if nearest else None


def read_status_declaration(text: str) -> str | None:
    """Read a document's own declaration of whether its sections are live.

    Read from the HEADER only - everything before the first level-2 heading -
    so that a section quoting the declaration sentence cannot be mistaken for
    the file declaring itself.

    Args:
        text: A whole markdown document.

    Returns:
        ``LIVE``, ``HISTORICAL``, or None when the file does not declare.
    """
    header: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            break
        header.append(line)
    match = STATUS_DECLARATION.search("\n".join(header))
    return match.group(1) if match else None


def guard_dated(root: Path, files: list[Path]) -> tuple[Guard, list[Skip]]:
    """Classify every dated heading. FAILS on one that fits neither idiom.

    Args:
        root: The repository root under audit.
        files: The enumerated candidate files.

    Returns:
        (the guard record, skip records).
    """
    skips: list[Skip] = []
    classified: dict[str, list[str]] = {STATUS_DATE: [], PROVENANCE_DATE: []}
    unclassified: list[str] = []
    historical_in_live: list[str] = []
    scanned = 0
    for path in files:
        if path.suffix.lower() not in (".md", ".markdown"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            skips.append(
                {"path": _rel(root, path), "reason": f"unreadable markdown: {_exc_text(exc)}"}
            )
            continue
        scanned += 1
        headings = dated_headings(text)
        if not headings:
            continue
        relative = _rel(root, path)
        declaration = read_status_declaration(text)
        if declaration is None:
            skips.append(
                {
                    "path": relative,
                    "reason": "carries dated headings but declares no section status, so the "
                    "live-file arm could not grade it",
                }
            )
        for number, heading in headings:
            record = f"{relative}:{number}  {heading.strip()}"
            family = classify_dated_heading(heading)
            if family is None:
                unclassified.append(record)
                continue
            classified[family].append(record)
            if family == STATUS_DATE and declaration == LIVE:
                historical_in_live.append(record)

    detail = _dated_detail(scanned, classified)
    if historical_in_live:
        detail.append(
            f"DRIFT - a {STATUS_DATE} date inside a file that declares itself {LIVE}. The "
            "heading marks its own section historical while the file says its sections are "
            "current, and those two cannot both be true. Either the heading's date belongs "
            "after a provenance verb - because it records when the text was filed rather "
            f"than a status - or the file is no longer {LIVE} and its header should say so. "
            "Do NOT resolve it by deleting the date:"
        )
        detail.extend(f"  {item}" for item in historical_in_live)
    if unclassified:
        detail.append(
            "DRIFT - dated headings in an idiom the closed vocabulary does not cover. "
            f"Whoever wrote each one says which it is: a {STATUS_DATE} date, which marks "
            f"the section historical, or a {PROVENANCE_DATE} date, which does not. "
            "Reshape the heading, or widen the vocabulary in tools/drift_guard.py "
            "deliberately. Do NOT resolve it by deleting the date - that changes what a "
            "reader believes about the section:"
        )
        detail.extend(f"  {item}" for item in unclassified)
    if historical_in_live or unclassified:
        return _guard("g", "dated sections", "FAIL", detail), skips
    return _guard("g", "dated sections", "PASS", detail), skips


def _dated_detail(scanned: int, classified: dict[str, list[str]]) -> list[str]:
    """Render the classified populations. Counts are DERIVED here, never written.

    Args:
        scanned: How many markdown files were read.
        classified: Records per family.

    Returns:
        The detail lines.
    """
    status = classified[STATUS_DATE]
    provenance = classified[PROVENANCE_DATE]
    detail = [
        f"markdown files scanned: {scanned}",
        f"{STATUS_DATE} dates ({len(status)}) - the section IS historical and must not be "
        "audited as current:",
    ]
    detail.extend(f"  {item}" for item in status)
    detail.append(
        f"{PROVENANCE_DATE} dates ({len(provenance)}) - these record WHEN the text was "
        "filed, moved or measured. They say nothing about the section's status, and a "
        "live instruction is free to carry one:"
    )
    detail.extend(f"  {item}" for item in provenance)
    if not status and not provenance:
        detail.append("no dated headings found; nothing is self-marked historical")
    return detail


# --- guard a: doc budgets ---------------------------------------------------


def guard_budgets(root: Path) -> tuple[Guard, list[Skip]]:
    """Run the CONVENTIONS 2.1 budgets through tools/doc_budget.py."""
    skips: list[Skip] = []
    name = "doc budgets"
    try:
        doc_budget = _load_doc_budget()
    except ImportError as exc:
        skips.append({"path": "tools/doc_budget.py", "reason": f"not importable: {_exc_text(exc)}"})
        return _guard("a", name, "FAIL", ["tools/doc_budget.py could not be imported"]), skips

    rows = doc_budget.evaluate(root)
    hard = doc_budget.hard_failures(rows)
    warn = doc_budget.soft_failures(rows)
    measured = [row for row in rows if row["status"] != "MISSING"]
    missing = [row for row in rows if row["status"] == "MISSING"]
    skips.extend(
        {"path": row["file"], "reason": "budgeted file absent - size not measured"}
        for row in missing
    )

    detail = [f"measured {len(measured)} file(s), {len(missing)} absent"]
    detail.extend(
        f"  {row['severity']} {row['file']}: {row['actual_bytes']} bytes "
        f"against a {row['budget_bytes']} byte budget"
        for row in hard + warn
    )
    if hard or warn:
        detail.append(f"  {doc_budget.RELOCATE_GUIDANCE}")
    if hard:
        return _guard("a", name, "FAIL", detail), skips
    if warn:
        return _guard("a", name, "WARN", detail), skips
    return _guard("a", name, "PASS", detail), skips


# --- guard h: version pin ---------------------------------------------------

VERSION_PIN_RELATIVE = "clockspeed/data/version.py"
RE_EXTRACT_COMMAND = "python tools/drift_guard.py --re-extract"
RE_EXTRACT_GUIDANCE = (
    f"Repair by re-extracting from the live install: {RE_EXTRACT_COMMAND}. "
    "Do NOT hand-edit a value back - the pin records what was MEASURED, and "
    "editing it to match an expectation is how a stale pin survives."
)

# Where the install and the build string are reported when neither may be
# named. The install path, the account id and the machine name are personal
# data (CLAUDE.md non-negotiable 3), so a skip record about the install names
# the SUBJECT rather than the path.
_INSTALL_SUBJECT = "<game install>"
_BUILD_SUBJECT = "<game build string>"


@contextlib.contextmanager
def _quiet_unknown_groups(docs_module: Any) -> Iterator[None]:
    """Silence the docs loader's per-unknown-group warnings for one bulk pass.

    Configuring logging is an application's job and never a library's, and this
    file is an application entry point. The groups themselves are never dropped -
    the census still counts every one.

    Historical note, because the volume this suppresses has changed: the loader
    once recognized only a 21-name subset, so the full shipped document produced
    ninety-odd unknown-group lines in front of a one-line verdict. The loader now
    recognizes the pinned build's whole group census and that count is zero on a
    matching build. This guard is therefore quiet by default and stays here for
    the case it was written for - a PATCHED build carrying groups the pin has
    never seen, which is exactly when the verdict line matters most and exactly
    when the noise would return.

    Args:
        docs_module: The docs_extract module, so the logger is named by the
            module rather than by a restated string.

    Yields:
        None, for the duration of the quiet pass.
    """
    logger = logging.getLogger(docs_module.__name__)
    previous = logger.level
    logger.setLevel(logging.ERROR)
    try:
        yield
    finally:
        logger.setLevel(previous)


def _grouped(value: object) -> str:
    """Render a byte count with thousands separators.

    Not cosmetic. A bare eight-digit byte count has the same shape as a
    platform account id, so a PII scan over this output would either flag it or
    have to be weakened to ignore it. Separators keep the number readable and
    keep the scan strict.

    Args:
        value: The count, or anything else.

    Returns:
        The grouped rendering, or the plain string form of a non-integer.
    """
    return f"{value:,}" if isinstance(value, int) else str(value)


def _pin_summary(payload: dict[str, Any]) -> list[str]:
    """Describe what the pin claims, before anything is checked against it."""
    body = payload.get("census") or {}
    digest = str(payload.get("docs_sha256", ""))
    return [
        f"pinned build: {payload.get('game_build', '?')}",
        f"pinned docs: {payload.get('docs_relative', '?')}  "
        f"{_grouped(payload.get('docs_bytes'))} bytes  sha256 {digest[:12]}...",
        f"pinned census: {body.get('group_count', '?')} group(s), "
        f"{body.get('entry_count', '?')} entries",
    ]


def _live_build_string(game_dir: Path, skips: list[Skip]) -> str:
    """Read the installed build string, recording a skip when it cannot be read.

    Fail-soft in both directions, matching every other guard in this file: an
    unimportable reader and an unreadable build string are both a skip record
    and an uncompared field, never a traceback out of the driver.
    """
    try:
        verify_env = _load_verify_env()
    except ImportError as exc:
        skips.append(
            {
                "path": "scripts/verify_env.py",
                "reason": f"not importable ({_exc_text(exc)}) - the pinned build "
                "string was not compared",
            }
        )
        return ""
    build, how = verify_env.read_build_string(game_dir)
    if not build:
        skips.append(
            {
                "path": _BUILD_SUBJECT,
                "reason": f"not readable from the install ({how}) - the "
                "pinned build string was not compared",
            }
        )
        return ""
    return str(build)


def _live_differences(
    version: Any, docs_module: Any, payload: dict[str, Any], raw: bytes, build: str
) -> list[str]:
    """Name exactly which measured invariants moved between pin and live data.

    Only ever called once a hash or size mismatch has already been established,
    so the cost of parsing the whole document is paid on the failure path and
    never on the green one.
    """
    try:
        with _quiet_unknown_groups(docs_module):
            live = version.build_pin(raw, build)
    except docs_module.DocsExtractError as exc:
        return [
            f"  the live docs file could not be parsed for a detailed comparison: {_exc_text(exc)}"
        ]
    differences = version.compare(payload.get("census") or {}, live["census"])
    if not differences:
        return ["  the measured census is UNCHANGED - only the bytes moved"]
    return ["  what moved:", *(f"    {item}" for item in differences)]


def _pin_live_check(
    version: Any, locate: Any, docs_module: Any, payload: dict[str, Any]
) -> tuple[str, list[str], list[Skip]]:
    """Compare a valid pin against the installed game, if one is resolvable.

    Returns:
        (status, detail lines, skip records). The status is PASS or FAIL and is
        never WARN: an absent install is a PASS carrying an explicit skip
        record, because tier 1 runs on a runner with no game and the lane must
        never be red for it. FAIL is reserved for a pin that contradicts an
        install that IS present.
    """
    detail: list[str] = []
    skips: list[Skip] = []

    game_dir, resolver = locate.resolve_game_dir()
    if game_dir is None:
        skips.append(
            {
                "path": _INSTALL_SUBJECT,
                "reason": f"the game install is unresolved ({locate.redact(resolver)}) - the "
                "version pin was checked for internal integrity only, never against live "
                "game data",
            }
        )
        detail.append("live install NOT resolved - internal integrity only")
        detail.append(
            "  that is deliberate, not a gap: tier 1 runs on a runner with no game, so a "
            "hand-edited pin has to be detectable from the pin's own checksum alone"
        )
        return "PASS", detail, skips

    relative = str(payload.get("docs_relative") or version.DOCS_RELATIVE)
    try:
        raw = game_dir.joinpath(*relative.split("/")).read_bytes()
    except OSError as exc:
        # Only strerror. str(exc) on a Windows OSError carries the filename,
        # and the install path must never reach a printed line.
        reason = _exc_text(exc)
        skips.append(
            {
                "path": relative,
                "reason": f"not readable under the resolved install ({reason})"
                " - the pin was not compared against live game data",
            }
        )
        detail.append("live docs file NOT readable - internal integrity only")
        return "PASS", detail, skips

    digest = hashlib.sha256(raw).hexdigest()
    build = _live_build_string(game_dir, skips)
    mismatches: list[str] = []
    if len(raw) != payload.get("docs_bytes"):
        mismatches.append(
            f"docs size: pinned {_grouped(payload.get('docs_bytes'))}, live {_grouped(len(raw))}"
        )
    if digest != payload.get("docs_sha256"):
        mismatches.append(
            f"docs sha256: pinned {str(payload.get('docs_sha256', ''))[:12]}..., "
            f"live {digest[:12]}..."
        )
    if build and build != payload.get("game_build"):
        mismatches.append(f"game build: pinned {payload.get('game_build')}, live {build}")

    if not mismatches:
        detail.append(
            f"live install matches the pin ({relative}: {_grouped(len(raw))} bytes, "
            f"sha256 {digest[:12]}...)"
        )
        return "PASS", detail, skips

    detail.append(
        "the pin does NOT match the live install - the game was patched, or the pin is stale:"
    )
    detail.extend(f"  {item}" for item in mismatches)
    pinned_build = build or str(payload.get("game_build", ""))
    detail.extend(_live_differences(version, docs_module, payload, raw, pinned_build))
    detail.append(RE_EXTRACT_GUIDANCE)
    return "FAIL", detail, skips


def guard_version_pin(root: Path) -> tuple[Guard, list[Skip]]:
    """Assert the version pin is self-consistent, and matches a live install if present.

    The pin is read out of the tree under audit as TEXT and is never imported,
    so no code from that tree runs to grade it; the validator itself always
    comes from this checkout (see :func:`_this_checkout`).
    """
    skips: list[Skip] = []
    name = "version pin"
    path = root / "clockspeed" / "data" / "version.py"

    try:
        version, locate, docs_module = _load_pin_support()
    except ImportError as exc:
        skips.append(
            {"path": VERSION_PIN_RELATIVE, "reason": f"pin logic not importable: {_exc_text(exc)}"}
        )
        return _guard("h", name, "WARN", ["clockspeed.data.version is not importable"]), skips

    if not path.is_file():
        skips.append(
            {"path": VERSION_PIN_RELATIVE, "reason": "absent - the version pin was not evaluated"}
        )
        return _guard("h", name, "WARN", [f"{VERSION_PIN_RELATIVE} does not exist yet"]), skips

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        skips.append({"path": VERSION_PIN_RELATIVE, "reason": f"unreadable: {_exc_text(exc)}"})
        return _guard("h", name, "WARN", [f"{VERSION_PIN_RELATIVE} could not be read"]), skips

    try:
        payload = version.extract_pin_block(source)
    except version.PinError as exc:
        detail = [f"the generated pin block is unusable: {_exc_text(exc)}", RE_EXTRACT_GUIDANCE]
        return _guard("h", name, "FAIL", detail), skips

    detail = _pin_summary(payload)
    problems = version.validate_pin(payload)
    if problems:
        detail.append("the pin is INTERNALLY INCONSISTENT - a field was edited by hand:")
        detail.extend(f"  {problem}" for problem in problems)
        detail.append(RE_EXTRACT_GUIDANCE)
        return _guard("h", name, "FAIL", detail), skips

    detail.append("internal integrity: OK - the recorded checksum matches the recomputed one")
    status, live_detail, live_skips = _pin_live_check(version, locate, docs_module, payload)
    detail.extend(live_detail)
    skips.extend(live_skips)
    return _guard("h", name, status, detail), skips


# --- guard i: work-item ownership -------------------------------------------

# WHY NOTHING BELOW IS A HAND-WRITTEN LIST OF FILES, IDS OR EXEMPTIONS. Each of
# the three would rot in a different direction, and this project has shipped two
# of them already:
#
#   A LIST OF OWNER FILES is a scope restriction, which is an allowlist with the
#   sign flipped - deleting an entry deletes the coverage in silence. The set is
#   parsed instead out of the CLAUDE.md sentence that DECLARES it, so renaming an
#   owner file or adding a fifth state moves the guard with the doctrine.
#
#   A LIST OF IDS is invalidated by each close and each new item, so it is
#   stale within one session of being written.
#
#   A LIST OF EXEMPT IDS is the worst of the three: it forgives by name, so a
#   single line hides a real collision for as long as nobody re-reads it. What
#   replaces it here is a QUESTION asked of the ledger record itself - does this
#   record say, ABOUT THIS ID, that it did not close - so the exemption carries
#   its own justification, written by the author at the time, in the data. Every
#   id forgiven that way is REPORTED on every run, for the same reason the skip
#   list is (CONVENTIONS 15.1): a forgiveness nobody sees is an allowlist again.
#
# WHY THE BINDING TO AN ID IS LOAD-BEARING AND NOT A DETAIL. The first build of
# this guard asked its question of the record's whole BODY, which is a search of
# a document rather than a statement about an item. Under that predicate an
# ordinary closure record that also remarked, truly, that some OTHER item stays
# open exempted itself - so the collision this guard exists to find sat in the
# tree with the guard green, and the report printed the forgiving sentence and
# its foreign id side by side without noticing. Forgiving by WORDING ALONE is
# strictly worse than forgiving by id: an id list is at least auditable, while a
# phrase list is triggered silently by prose written for other purposes. The
# phrase list survives here only as the half that recognises a disposition; the
# half that decides WHOSE disposition it is is the id binding.
#
# THE RESIDUAL THAT BUYS COSTS, stated rather than implied away. A record that
# declares its non-closure without ever naming the item - "this entry is a grant
# record, not a completion record", with the id only in the heading and no
# disposition IN the heading - is now read as a closure. That is the loud
# direction on purpose: if such an id is also open elsewhere the guard says so,
# and the repair is a new ledger record naming the item, which is what an
# append-only file is for, and NOT a line in this guard naming the id.

#: The sentence in CLAUDE.md that names the owner file of each work-item state.
#: An anchor, not a restatement - the file:line is found at runtime and the
#: guard reports rather than passes when the anchor is absent.
WORK_ITEM_ANCHOR = "Work-item states"

#: One "<STATE> in `<path>`" pair out of that sentence.
_OWNER_DECLARATION = re.compile(r"\b([A-Z]{3,})\s+in\s+`([^`]+)`")

#: Any backticked markdown path the same sentence names. THIS IS THE
#: COMPLETENESS ORACLE, and it exists because the pair pattern above is a
#: SCOPE RESTRICTION - it reads only the clauses phrased the one way it knows.
#: A scope restriction is an allowlist with the sign flipped: reword one clause
#: and its file leaves the scan carrying its coverage with it, and nothing goes
#: red. Counting the paths the sentence names, independently of how the clause
#: around them is phrased, turns that silent deletion into a named file.
_DOCTRINE_PATH = re.compile(r"`([^`\s]+\.md)`")

#: The state whose owner file records a CLOSURE. Read as a key into the parsed
#: declaration rather than as a filename, so the ledger is identified by the
#: role the doctrine gives it.
CLOSED_STATE = "CLOSED"

#: A work-item ID. Two digits or more, which is what keeps the shape strings
#: "CS-nnn", "CS-0nn" and "CS-1nn" - block labels written in the prose of the
#: owner files themselves - from being read as items.
_WORK_ITEM_ID = re.compile(r"CS-G?\d{2,}")

# --- what an ENTRY HEAD looks like, in pieces so the near-miss detector below
# can reuse every piece except the separator.
#
# MENTION IS NOT OWNERSHIP, and that distinction is the whole of these patterns.
# A ROADMAP entry's NOTE cites the items it was earned by, a GATED item cites
# the roadmap item it feeds, and a ledger record cites its siblings. Matching an
# ID anywhere in a file rather than at the head of an entry reads those
# citations as collisions, which is a guard red against correct history.
_HEAD_MARKERS = r"(?:[-*+]\s+(?:\[[ xXvV]\]\s+)?|\d+[.)]\s+|\|\s*)*"
_HEAD_HASHES = r"(?:#+\s*)?"
_HEAD_DATE = r"(?:\d{4}[-/]\d{2}[-/]\d{2}\s*[-:]\s*)?"
_HEAD_EMPHASIS = r"[`*_]{0,3}"
_HEAD_ID_RUN = r"CS-G?\d{2,}(?:\s*(?:,|/|\band\b)\s*CS-G?\d{2,})*"
_HEAD_QUALIFIER = r"(?:\s+[A-Z][A-Z0-9-]*){0,2}"
_HEAD_SEPARATOR = r"(?:\s*-{1,3}\s|\s*:\s|\s*\|)"
_HEAD_PREFIX = rf"^[ \t]*{_HEAD_MARKERS}{_HEAD_HASHES}{_HEAD_DATE}{_HEAD_EMPHASIS}"

#: The head of an ENTRY. Deliberately wide across MARKUP - list bullets,
#: checkboxes, numbered items, table cells, bold, backticks, heading hashes -
#: because markup is presentation and none of it changes who owns the item.
_ENTRY_HEAD = re.compile(
    rf"{_HEAD_PREFIX}({_HEAD_ID_RUN}){_HEAD_EMPHASIS}{_HEAD_QUALIFIER}{_HEAD_SEPARATOR}"
)

#: A line that occupies a head POSITION - id first, then punctuation opening a
#: summary - which :data:`_ENTRY_HEAD` nonetheless could not read.
#:
#: THE TWO FAILURE DIRECTIONS ARE NOT SYMMETRIC, which is the whole reason this
#: pattern exists. A head the recogniser misses removes an item from the scan
#: and leaves the report GREEN - the tree looks clean because less of it was
#: read. So an unreadable head is UNACCOUNTED and red, never merely unread. The
#: separator class here is wider than the one above on purpose: it is asking
#: "was this line trying to be a head", not "is this line a head".
#:
#: A ledger body wraps, so an ordinary sentence can BEGIN with an id and
#: continue in prose. Those are excluded by requiring punctuation rather than a
#: word after the id, and the exclusion is graded by its own test.
_NEAR_MISS_HEAD = re.compile(
    rf"{_HEAD_PREFIX}({_HEAD_ID_RUN}){_HEAD_EMPHASIS}{_HEAD_QUALIFIER}\s*[-:|(\[{{=~]"
)

#: Any markdown heading. A heading is a record BOUNDARY whether or not it names
#: an item, which is what stops a later note's body merging into the record
#: above it and speaking for an item it never mentions.
_HEADING_LINE = re.compile(r"^[ \t]{0,3}#+")

#: One sentence boundary, used to scope a declaration to the clause that made
#: it rather than to the whole document.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")

#: How a ledger record DECLARES that the item it names did not close, as label
#: mapped to pattern, matched case-insensitively.
#:
#: FORGIVING BY WORDING IS WORSE THAN FORGIVING BY ID, and this list is only
#: half the mechanism for that reason. A phrase list is triggered silently by
#: prose written for entirely other purposes - a true remark about a DIFFERENT
#: item, or a general observation about grant records as a class - so on its
#: own it is an allowlist that nobody wrote and nobody can audit. What makes it
#: safe is the BINDING in :func:`_non_closure_bindings`: a phrase found here
#: forgives an id only when the clause carrying it is about THAT id.
_NON_CLOSURE_DECLARATIONS: tuple[tuple[str, str], ...] = (
    ("not-a-completion-record", r"not a completion record"),
    ("does-not-close", r"do(?:es)? not close|did not close|may not close"),
    ("stays-open", r"stays open|remains open|is reopened"),
)

#: How much of the declaring clause is quoted back in the report.
_DECLARATION_QUOTE = 120

#: Two owner files are what a collision needs, and they have to be two files
#: that each OWN something. Below that the cross-file half of this guard is
#: vacuous by construction, so it reports rather than passes.
_COLLISION_FLOOR = 2


def _owner_files(root: Path) -> tuple[dict[str, str], list[str], str]:
    """Parse the work-item state-to-owner-file map out of CLAUDE.md.

    Args:
        root: The repository root under audit.

    Returns:
        (state mapped to repo-relative path, paths the sentence named that no
        clause claimed, a problem string). The problem is empty when the map was
        parsed. It is never both empty and an empty map: a guard that scanned
        nothing has to say why.
    """
    path = root / "CLAUDE.md"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return {}, [], f"CLAUDE.md is unreadable: {_exc_text(exc)}"

    start = next((index for index, line in enumerate(lines) if WORK_ITEM_ANCHOR in line), None)
    if start is None:
        return {}, [], f"no sentence containing {WORK_ITEM_ANCHOR!r} in CLAUDE.md"

    end = start
    while end < len(lines) and lines[end].strip():
        end += 1
    sentence = " ".join(lines[start:end])
    found = dict(_OWNER_DECLARATION.findall(sentence))
    if not found:
        return {}, [], f"the {WORK_ITEM_ANCHOR!r} sentence names no backticked owner file"
    claimed = set(found.values())
    unclaimed = [name for name in _DOCTRINE_PATH.findall(sentence) if name not in claimed]
    return found, sorted(set(unclaimed)), ""


def _entry_head_ids(line: str) -> list[str]:
    """The work-item IDs a line OWNS, as opposed to the ones it merely mentions.

    Args:
        line: One line of an owner file.

    Returns:
        The IDs at the head of the entry, or an empty list when the line is not
        an entry head.
    """
    match = _ENTRY_HEAD.match(line)
    return _WORK_ITEM_ID.findall(match.group(1)) if match else []


def _unaccounted_heads(text: str) -> list[tuple[int, str]]:
    """Lines occupying a head position that the recogniser could not read.

    Args:
        text: The file's full text.

    Returns:
        ``(line_number, line)`` for each, in file order.
    """
    return [
        (number, line.strip())
        for number, line in enumerate(text.splitlines(), start=1)
        if not _entry_head_ids(line) and _NEAR_MISS_HEAD.match(line)
    ]


def _owned_ids(text: str) -> dict[str, int]:
    """Map every ID a file owns to the line its FIRST entry head sits on.

    Args:
        text: The file's full text.

    Returns:
        ID mapped to a 1-based line number.
    """
    found: dict[str, int] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        for item in _entry_head_ids(line):
            found.setdefault(item, number)
    return found


def _ledger_records(text: str) -> list[tuple[int, list[str], str, str]]:
    """Cut the ledger into records, newest first, heading kept apart from body.

    EVERY HEADING IS A BOUNDARY, including one that names no work-item at all.
    A heading with no ID is not a record - but if it is not a record ENDING
    either, its body merges upward into the record above and gets to speak for
    an item it never mentions. The ledger already carries id-less headings, so
    this is a live shape rather than a hypothetical one.

    The heading is returned separately from the body because a heading rarely
    ends in a full stop, so joining the two makes the first body sentence
    inherit the heading's ids and lets a generic remark borrow their authority.

    Args:
        text: The ledger's full text.

    Returns:
        ``(line_number, ids, heading, body)`` per record in file order, which
        the file's stated append discipline makes newest first. The body has its
        line wraps joined, so a clause split across two lines still reads as one.
    """
    lines = text.splitlines()
    bounds = [number for number, line in enumerate(lines, start=1) if _HEADING_LINE.match(line)]
    out: list[tuple[int, list[str], str, str]] = []
    for index, number in enumerate(bounds):
        ids = _entry_head_ids(lines[number - 1])
        if not ids:
            continue
        stop = bounds[index + 1] - 1 if index + 1 < len(bounds) else len(lines)
        body = re.sub(r"\s+", " ", " ".join(lines[number:stop]))
        out.append((number, ids, lines[number - 1].strip(), body))
    return out


def _non_closure_bindings(heading: str, body: str, ids: list[str]) -> dict[str, tuple[str, str]]:
    """Which of a record's OWN ids it declares did not close, and on what words.

    A DECLARATION IS ONLY AN EXEMPTION WHEN IT IS ABOUT THIS ITEM. A phrase
    search over the whole record body cannot tell a disposition from a passing
    remark, so a closure record that also observes - truly - that some OTHER
    item stays open exempts itself, and the exact shape this guard exists to
    catch sits in the tree green. Two things can bind a declaration to an id:

    - THE HEADING, which names its own ids by construction. "MEASUREMENT
      RECORD. THE ITEM STAYS OPEN" in a heading is about that heading's items
      and nothing else.
    - A BODY CLAUSE THAT NAMES THE ID. "This entry does not close CS-436" is
      about CS-436 whatever else the record goes on to say.

    Anything else - a remark about a different item, a general observation
    about grant records as a class - binds nothing and forgives nothing.

    Args:
        heading: The record's heading line.
        body: The record's body, line wraps already joined.
        ids: The ids the heading owns.

    Returns:
        Own id mapped to ``(label, quoted clause)``. An id absent from the
        mapping was not exempted by this record.
    """
    bound: dict[str, tuple[str, str]] = {}
    own = set(ids)
    for label, pattern in _NON_CLOSURE_DECLARATIONS:
        if re.search(pattern, heading, re.IGNORECASE):
            for item in ids:
                bound.setdefault(item, (label, heading[:_DECLARATION_QUOTE].strip()))
    for clause in _SENTENCE_BREAK.split(body):
        named = own.intersection(_WORK_ITEM_ID.findall(clause))
        if not named:
            continue
        for label, pattern in _NON_CLOSURE_DECLARATIONS:
            if re.search(pattern, clause, re.IGNORECASE):
                for item in named:
                    bound.setdefault(item, (label, clause[:_DECLARATION_QUOTE].strip()))
    return bound


def ledger_ownership(text: str) -> tuple[dict[str, int], list[dict[str, str]]]:
    """Which IDs the ledger owns as CLOSED, and which records were forgiven.

    THE SEQUENCING TRAP THIS FUNCTION EXISTS FOR. An ID reaches the ledger before
    it closes: a frozen-file grant is recorded BEFORE the edit it authorises
    (CLAUDE.md section 6), and a measurement record can report what shipped while
    saying the item stays open. Keying ownership on any MENTION of an ID, or on
    the mere presence of a heading, marks those items closed while they are
    correctly open in ROADMAP.md - a guard red against correct history, which
    gets switched off rather than obeyed.

    Only the NEWEST record for an ID is consulted, which is the discipline the
    ledger states for itself: it is append-only and newest first, and a record
    that turns out to be wrong is corrected by a LATER one. An item closed and
    then reopened by a correction is therefore open, without the guard holding
    any per-item knowledge.

    Args:
        text: The ledger's full text.

    Returns:
        (IDs owned as closed, mapped to the line of the deciding record;
        one report row per ID a record exempted).
    """
    closed: dict[str, int] = {}
    forgiven: list[dict[str, str]] = []
    decided: set[str] = set()
    for number, ids, heading, body in _ledger_records(text):
        bound = _non_closure_bindings(heading, body, ids)
        for item in ids:
            if item in decided:
                continue
            decided.add(item)
            if item not in bound:
                closed[item] = number
                continue
            label, quoted = bound[item]
            forgiven.append(
                {"ids": item, "line": str(number), "declaration": label, "quoted": quoted}
            )
    return closed, forgiven


def _collisions(owned: dict[str, dict[str, str]]) -> list[str]:
    """Render one line per ID recorded in more than one owner file.

    Args:
        owned: ID mapped to owner path mapped to a "<state> line <n>" locator.

    Returns:
        The findings, sorted by ID.
    """
    return [
        f"{item} is owned by {len(where)} files: "
        + "; ".join(f"{path} ({locator})" for path, locator in sorted(where.items()))
        for item, where in sorted(owned.items())
        if len(where) > 1
    ]


class _Scan(NamedTuple):
    """What one pass over the declared owner files found.

    Attributes:
        owned: ID mapped to owner path mapped to a "<state> line <n>" locator.
        census: One report line per owner file read.
        owning: How many of those files own at least one ID.
        forgiven: One row per ID a ledger record exempted.
        unaccounted: One row per line in a head position that was not read.
        unread: Repo-relative paths the doctrine declared and the tree lacks.
    """

    owned: dict[str, dict[str, str]]
    census: list[str]
    owning: int
    forgiven: list[dict[str, str]]
    unaccounted: list[str]
    unread: list[str]


def _read_owner_files(root: Path, owners: dict[str, str], skips: list[Skip]) -> _Scan:
    """Read each owner file and record which IDs it OWNS.

    Args:
        root: The repository root under audit.
        owners: State mapped to repo-relative path.
        skips: Skip records, appended to for every file not read.

    Returns:
        The scan.
    """
    scan = _Scan({}, [], 0, [], [], [])
    owning = 0
    for state, relative in sorted(owners.items()):
        try:
            text = (root / relative).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            skips.append({"path": relative, "reason": f"owner file not read ({_exc_text(exc)})"})
            scan.unread.append(relative)
            continue
        if state == CLOSED_STATE:
            found, records = ledger_ownership(text)
            scan.forgiven.extend(records)
        else:
            found = _owned_ids(text)
        scan.unaccounted.extend(
            f"  {relative}:{number}  {line}" for number, line in _unaccounted_heads(text)
        )
        owning += bool(found)
        scan.census.append(f"  {state:<13} {relative:<16} owns {len(found)} id(s)")
        for item, number in found.items():
            scan.owned.setdefault(item, {})[relative] = f"{state} line {number}"
    return scan._replace(owning=owning)


def guard_work_items(root: Path) -> tuple[Guard, list[Skip]]:
    """Assert every work-item ID is recorded in exactly one owner file.

    CLAUDE.md section 4 states the one-owner rule in prose. This is the machine
    check for it, on the file that states the thesis: a restated fact is a fact
    that will drift, and the ROADMAP line of a closed item is a restated fact.

    EVERY WAY THIS GUARD CAN READ LESS THAN THE WHOLE TREE IS RED, not green and
    not quiet. An owner clause that stopped parsing, a declared file the tree
    lacks, a line in a head position the recogniser cannot read - each deletes
    coverage, and coverage deleted in silence is how the two guards before this
    one shipped with their own scope restrictions intact. The one exception is a
    tree with NOTHING to scan, which is WARN: that is a wrong root rather than
    drift, and it names itself in the skip list.
    """
    skips: list[Skip] = []
    name = "work-item ownership"
    owners, unclaimed, problem = _owner_files(root)
    if problem:
        skips.append({"path": "CLAUDE.md", "reason": f"{problem} - no owner file was scanned"})
        detail = [f"the owner-file declaration was not read: {problem}"]
        return _guard("i", name, "WARN", detail), skips

    scan = _read_owner_files(root, owners, skips)
    detail = [f"owner files declared by CLAUDE.md: {len(owners)}", *scan.census]
    if scan.forgiven:
        detail.append(
            "ledger records read as NON-closures, each by its own words about its own "
            "item - printed every run, because a forgiveness nobody sees is an allowlist "
            "by another name:"
        )
        detail.extend(
            f"  line {row['line']}  {row['ids']}  [{row['declaration']}]  {row['quoted']}"
            for row in scan.forgiven
        )
    else:
        detail.append("no ledger record declared itself a non-closure on this run")

    if scan.owning < _COLLISION_FLOOR or not scan.owned:
        detail.append(
            f"{len(scan.census)} owner file(s) read, {scan.owning} of them owning any id, "
            f"and {len(scan.owned)} id(s) found - below the floor of {_COLLISION_FLOOR} "
            "files EACH owning at least one id, so this guard proved nothing on this run"
        )
        return _guard("i", name, "WARN", detail), skips

    detail.append(f"distinct ids found: {len(scan.owned)}")
    unaccounted = _unaccounted_detail(unclaimed, scan)
    findings = _collisions(scan.owned)
    if findings:
        detail.append("ONE ID, MORE THAN ONE OWNER FILE - CLAUDE.md section 4:")
        detail.extend(f"  {item}" for item in findings)
        detail.append(
            "Delete the entry from the file that no longer owns the item. A ledger "
            "record that is NOT a closure - a frozen-file grant, a measurement record - "
            "says so about the item BY NAME and is not reported here; if one of these is "
            "such a record, the record is what needs to say it."
        )
    if findings or unaccounted:
        return _guard("i", name, "FAIL", [*detail, *unaccounted]), skips
    return _guard("i", name, "PASS", detail), skips


def _unaccounted_detail(unclaimed: list[str], scan: _Scan) -> list[str]:
    """Render everything the scan could not account for, or nothing at all.

    Args:
        unclaimed: Doctrine paths no owner clause claimed.
        scan: The owner-file scan.

    Returns:
        Report lines. Empty when the scan accounted for everything, which is the
        only state this guard is allowed to call PASS.
    """
    detail: list[str] = []
    if unclaimed:
        detail.append(
            "UNACCOUNTED - the doctrine sentence names these files and no owner clause "
            "in it parsed to them, so they were never scanned. Reword the clause back "
            "into '<STATE> in `<path>`' or drop the path from the sentence:"
        )
        detail.extend(f"  {name}" for name in unclaimed)
    if scan.unread:
        detail.append(
            "UNACCOUNTED - the doctrine declares these owner files and the tree does not "
            "hold them, so part of the scan did not happen while the rest reported clean:"
        )
        detail.extend(f"  {name}" for name in scan.unread)
    if scan.unaccounted:
        detail.append(
            "UNACCOUNTED - these lines carry a work-item id in a head position that the "
            "entry recogniser cannot read. An unread head leaves the item out of the "
            "scan and the verdict green, so rewrite the head or widen the recogniser:"
        )
        detail.extend(scan.unaccounted)
    return detail


# --- re-extract -------------------------------------------------------------


def re_extract(root: Path) -> int:
    """Regenerate the version pin from the live install. Returns the exit code.

    The other half of the CS-200 criterion: red when the pin is corrupted,
    green after re-extract. Everything it writes goes to one tracked file in
    this repository, atomically. Nothing under the game install is opened for
    anything but reading (non-negotiable 1).
    """
    try:
        version, locate, docs_module = _load_pin_support()
        verify_env = _load_verify_env()
    except ImportError as exc:
        print(f"re-extract FAILED: {_exc_text(exc)}")
        return 1

    game_dir, resolver = locate.resolve_game_dir()
    if game_dir is None:
        print(f"re-extract FAILED: no game install resolved ({locate.redact(resolver)})")
        print("The pin is MEASURED from the installed game; there is nothing to measure.")
        return 1

    relative = version.DOCS_RELATIVE
    try:
        raw = game_dir.joinpath(*version.DOCS_RELATIVE_PARTS).read_bytes()
    except OSError as exc:
        print(f"re-extract FAILED: cannot read {relative} ({_exc_text(exc)})")
        return 1

    build, how = verify_env.read_build_string(game_dir)
    if not build:
        print(f"re-extract FAILED: the installed build string is unknown ({how}).")
        print("Refusing to pin a build that was not read - a wrong build string silently")
        print("invalidates every version-pinned artifact downstream.")
        return 1

    with _quiet_unknown_groups(docs_module):
        payload = version.build_pin(raw, str(build))
    target = root / "clockspeed" / "data" / "version.py"
    version.write_pin(target, payload)

    body = payload["census"]
    print(f"re-extracted the version pin into {VERSION_PIN_RELATIVE}")
    print(f"  build:     {payload['game_build']}  (via {how})")
    print(f"  docs:      {relative}  {_grouped(payload['docs_bytes'])} bytes")
    print(f"  sha256:    {payload['docs_sha256']}")
    print(
        f"  census:    {body['group_count']} group(s), {body['entry_count']} entries, "
        f"{body['distinct_class_names']} distinct ClassName(s)"
    )
    print(
        f"  exponents: {body['power_consumption_exponents']} "
        f"across {body['power_consumption_exponent_groups']} group(s)"
    )
    print(f"  integrity: {payload['integrity']}")
    return 0


# --- driver -----------------------------------------------------------------


def run_all(root: Path) -> tuple[list[Guard], list[Skip], str]:
    """Run every guard. Returns (guards, skip records, enumeration source)."""
    files, source, skips = enumerate_files(root)
    guards: list[Guard] = []

    for runner in (
        guard_budgets,
        guard_memory,
        guard_topology,
        guard_ports,
        guard_frozen,
        guard_version_pin,
        guard_work_items,
    ):
        guard, guard_skips = runner(root)
        guards.append(guard)
        skips.extend(guard_skips)

    charset_guard, charset_skips = guard_charset(root, files, source)
    guards.append(charset_guard)
    skips.extend(charset_skips)

    dated_guard, dated_skips = guard_dated(root, files)
    guards.append(dated_guard)
    skips.extend(dated_skips)

    guards.sort(key=lambda guard: guard["id"])
    return guards, skips, source


def _verdict_table(guards: list[Guard]) -> list[str]:
    rows = [[guard["id"], guard["name"], guard["status"]] for guard in guards]
    widths = [len(header) for header in _GUARD_HEADERS]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    out = [
        "  ".join(_GUARD_HEADERS[i].ljust(widths[i]) for i in range(len(_GUARD_HEADERS))).rstrip()
    ]
    out.append("  ".join("-" * widths[i] for i in range(len(_GUARD_HEADERS))))
    out.extend(
        "  ".join(row[i].ljust(widths[i]) for i in range(len(_GUARD_HEADERS))).rstrip()
        for row in rows
    )
    return out


def _detail_lines(guards: list[Guard]) -> list[str]:
    out = ["Detail"]
    for guard in guards:
        out.append(f"  [{guard['id']}] {guard['name']} - {guard['status']}")
        out.extend(f"      {line}" for line in guard["detail"])
    return out


def _skip_lines(skips: list[Skip]) -> list[str]:
    out = [
        "SKIPPED - printed every run, not only when verbose.",
        "A guard can be green while self-excusing (CONVENTIONS 15.1). A green verdict",
        "means nothing without the list of what was never looked at.",
    ]
    if not skips:
        out.append("  (nothing skipped)")
        return out
    collapsed: dict[str, list[str]] = {}
    for skip in skips:
        collapsed.setdefault(skip["reason"], []).append(skip["path"])
    for reason in sorted(collapsed):
        paths = sorted(collapsed[reason])
        out.append(f"  {reason}  ({len(paths)})")
        out.extend(f"      {path}" for path in paths)
    return out


def render(guards: list[Guard], skips: list[Skip], source: str, root: Path) -> list[str]:
    """Render the guard table, the detail, the skip list and the verdict.

    The repo line is redacted, matching scripts/verify_env.py, which prints
    the identical fact. It is latent on the settled root, which is not under a
    home directory - and it fires on every run of any clone that is, putting
    the operator's account name into the header of the output most likely to
    be pasted into an issue.
    """
    out = ["Clockspeed drift guard", f"repo: {_redact(root)}", f"enumeration: {source}", ""]
    out.extend(_verdict_table(guards))
    out.append("")
    out.extend(_detail_lines(guards))
    out.append("")
    out.extend(_skip_lines(skips))

    failed = [guard for guard in guards if guard["status"] == "FAIL"]
    warned = [guard for guard in guards if guard["status"] == "WARN"]
    passed = sum(1 for guard in guards if guard["status"] == "PASS")
    out.append("")
    out.append(
        f"guards: {len(guards)}    PASS {passed}    WARN {len(warned)}    "
        f"FAIL {len(failed)}    skipped paths: {len(skips)}"
    )
    if failed:
        named = ", ".join(f"{guard['name']} ({guard['id']})" for guard in failed)
        out.append(f"VERDICT: DRIFT - {named}")
    elif warned:
        named = ", ".join(f"{guard['name']} ({guard['id']})" for guard in warned)
        out.append(f"VERDICT: CLEAN with warnings - {named}")
    else:
        out.append("VERDICT: CLEAN - no drift detected")
    return out


def main(argv: list[str] | None = None) -> int:
    """Run every guard and print the result. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        description="Run every Clockspeed drift guard and report one consolidated verdict. "
        "Exits non-zero on any DRIFT. Always prints what it skipped."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--re-extract",
        action="store_true",
        help="regenerate clockspeed/data/version.py from the live install, then exit",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    if args.re_extract:
        return re_extract(root)

    guards, skips, source = run_all(root)
    failed = [guard for guard in guards if guard["status"] == "FAIL"]

    if args.json:
        print(
            json.dumps(
                {
                    "schema": 1,
                    "enumeration": source,
                    "guards": guards,
                    "skipped": skips,
                    "drift": [guard["id"] for guard in failed],
                    "verdict": "DRIFT" if failed else "CLEAN",
                },
                indent=2,
            )
        )
    else:
        print("\n".join(render(guards, skips, source, root)))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
