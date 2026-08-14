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
  g  dated sections      a doc heading carrying an explicit date marks its own
                         section historical. Detected and reported so those
                         sections are not audited as current. Never fails.
  h  version pin         clockspeed/data/version.py is internally consistent -
                         its integrity checksum matches its own fields - and,
                         where an install is resolvable, matches the live docs
                         file. An UNRESOLVABLE install is never a failure: tier
                         1 runs this on a runner with no game, so the pin's own
                         checksum is what makes a hand-edit detectable there.
                         Repair with --re-extract.

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
from typing import Any

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

DATE_PATTERNS = (
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September"
        r"|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept"
        r"|Oct|Nov|Dec)\b[^\n]{0,12}\b\d{4}\b"
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
        try:
            port = int(raw)
        except (TypeError, ValueError):
            problems.append(f"reserved entry {item!r} has no usable port number")
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


def guard_dated(root: Path, files: list[Path]) -> tuple[Guard, list[Skip]]:
    """Report headings carrying an explicit date. Never fails."""
    skips: list[Skip] = []
    findings: list[str] = []
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
        findings.extend(
            f"{_rel(root, path)}:{number}  {line.strip()}"
            for number, line in enumerate(text.splitlines(), start=1)
            if line.startswith("#") and any(p.search(line) for p in DATE_PATTERNS)
        )

    detail = [f"markdown files scanned: {scanned}"]
    if findings:
        detail.append(
            "headings carrying an explicit date - each marks its OWN section historical "
            "and must not be audited as current:"
        )
        detail.extend(f"  {item}" for item in findings)
    else:
        detail.append("no dated headings found; nothing is self-marked historical")
    return _guard("g", "dated sections (report only)", "PASS", detail), skips


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
