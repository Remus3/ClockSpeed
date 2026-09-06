#!/usr/bin/env python3
"""Clockspeed drift guard - every guard, one consolidated verdict.

Guards, in the order they are reported:

  a  doc budgets         CONVENTIONS 2.1, delegated to tools/doc_budget.py by
                         import, never by shelling out, so there is one table.
  b  memory reachability the memory index and its leaves account for each other
                         BOTH ways. Every memory/*.md leaf except MEMORY.md is
                         reachable from MEMORY.md, directly or through an
                         INDEX_<domain>.md - CONVENTIONS 11 forbids unindexing a
                         file to save bytes, so an unreachable leaf is DRIFT, not
                         a style point. AND every citation resolves: a link
                         naming nothing used to be an element that matched
                         nothing, so a dangling wikilink inside a leaf, and an
                         index entry routing to a file that does not exist, both
                         passed CLEAN (CS-890). Citations are read outside fenced
                         code, where a TOML array-of-tables header is spelled
                         like a wikilink and cites nothing.
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

# CS-910. Run as a bare script and also loaded BY PATH by the suite, so this
# directory cannot be assumed on sys.path. The insert is the one _load_doc_budget
# below already makes, hoisted to module scope because the resolver is reached on
# the enumeration path rather than from one guard. The BARE module name is
# required: `tools` carries no __init__.py, so spelling it `tools.toolpath`
# hands mypy the same file under two module names and it refuses the run.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

#: The tool this guard asks which files are tracked. A NAME, resolved at runtime
#: and never spelled as a path - non-negotiable 3.
GIT_NAME = "git"

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
# WHY THE NUMERIC SHAPES ARE WIDER THAN THIS PROJECT'S HOUSE STYLE (CS-840).
# The guard used to see only a zero-padded four-digit-year ISO date and a
# day-first slash date. Three ordinary shapes were therefore INVISIBLE, and an
# invisible date is not "dated" at all - no arm of this guard can fire on it,
# whatever it says. ``2031/02/03`` (year-first slash), ``2031-2-3``
# (unpadded) and ``31-02-03`` (two-digit year) are all read now. Every
# addition carries the same digit lookaround, so none of them can match inside
# a longer run of digits - a two-digit-year shape cannot bite the tail off a
# four-digit-year one.
DATE_PATTERNS = (
    re.compile(r"(?<!\d)\d{4}-\d{1,2}-\d{1,2}(?!\d)"),
    re.compile(r"(?<!\d)\d{2}-\d{2}-\d{2}(?!\d)"),
    re.compile(r"(?<!\d)\d{4}/\d{1,2}/\d{1,2}(?!\d)"),
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
    # CS-910 - THE TOOL IS RESOLVED, NEVER NAMED. A bare "git" in an argv is
    # resolved by CreateProcess, which searches the CURRENT DIRECTORY before
    # PATH whenever the gate variable is absent from the environment - its state
    # at both machine and user scope on the development machine. This guard is
    # pointed at trees it did not create and is run from wherever the operator
    # is standing, so the current directory is not one it controls. An
    # unresolvable git yields the empty list, which is what a git that FAILS
    # already yields here.
    git = resolve_tool(GIT_NAME)
    if git is None:
        return []
    try:
        proc = subprocess.run(
            [git, "-C", str(root), "ls-files", "-z"],
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


# --- guard b: the memory partition, both directions -------------------------

_WIKILINK = re.compile(r"\[\[([^\]|#]+)")
_MDLINK = re.compile(r"\]\(([^)\s]+)")
_BACKTICK = re.compile(r"`([^`\n]+)`")

# A fence line under CommonMark: at most three spaces of indent, then a run of
# three or more backticks or tildes, then the rest of the line. The run and the
# remainder are captured separately because BOTH matter - an opener may carry
# an info string, a closer may not, and a closer must be at least as long as
# the opener it closes. Matching the shape alone is what CS-890's repair got
# wrong; see ``_outside_code``.
_FENCE_LINE = re.compile(r"^(?P<indent> *)(?P<run>`{3,}|~{3,})(?P<info>.*)$")

#: CommonMark caps a fence OPENER at three spaces of indent. The cap is applied
#: to openers only, never to closers - see ``_outside_code`` on P3.
_MAX_FENCE_INDENT = 3

# A target carrying a URL scheme cites something outside this store and is
# never resolved against a path in it. A single-letter scheme is matched on
# purpose so a Windows drive letter is excluded by the same clause.
_URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _link_targets(text: str) -> set[str]:
    """Every token that can COUNT AS AN INDEX ENTRY, backticked spans included.

    This is the REACHABILITY extractor and it is deliberately generous: an
    index that names a leaf in backticks has still routed to it, so refusing
    to count that would report a correctly indexed leaf as unreachable. It is
    the wrong extractor for resolution, and ``_citation_targets`` below is the
    narrower one that exists for that. See its docstring for why the two must
    not be merged.

    Args:
        text: The markdown source.

    Returns:
        Lowercased stems, with any directory prefix, ``.md`` suffix and
        fragment stripped.
    """
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


def _strip_inline_code(line: str) -> str:
    """Blank every inline code span in one line, delimiters included.

    P5, AND THE REASON THE NAME OF THIS SEAM MATTERED. The exclusion was
    spelled "fenced code" when the property it needs is CODE. Inline spans
    were not excluded at all, so a single line of ordinary prose -

        The TOML header `[[tool.mypy.overrides]]` is spelled like a wikilink.

    - turned guard (b) FAIL. That is not a hypothetical shape: ``MEMORY.md``
    already writes `assert count == 0` and `git commit -F` in inline
    spans, this module's own docstrings carry that token twice, and CS-890's
    lesson is a likely new memory leaf whose natural phrasing quotes it inline.
    The module knew about backtick spans on the reachability side all along -
    ``_link_targets`` harvests them deliberately - and was blind to them here.

    A span opens on a run of N backticks and closes on the next run of EXACTLY
    N, per CommonMark. An unmatched run is literal text and is left alone.

    Args:
        line: One line, already outside any fenced block.

    Returns:
        The line with each span replaced by spaces, so column positions - and
        therefore anything a caller may later report - are preserved.
    """
    out: list[str] = []
    index = 0
    length = len(line)
    while index < length:
        if line[index] != "`":
            out.append(line[index])
            index += 1
            continue
        run = 0
        while index + run < length and line[index + run] == "`":
            run += 1
        probe = index + run
        close = -1
        while probe < length:
            if line[probe] != "`":
                probe += 1
                continue
            width = 0
            while probe + width < length and line[probe + width] == "`":
                width += 1
            if width == run:
                close = probe
                break
            probe += width
        if close < 0:
            out.append("`" * run)
            index += run
            continue
        out.append(" " * (close + run - index))
        index = close + run
    return "".join(out)


def _outside_code(text: str) -> tuple[str, bool]:
    """Blank every CODE region - fenced blocks and inline spans alike.

    A ``[[token]]`` in code is sample material, not a cross-reference. The
    store quotes a TOML array-of-tables header spelled exactly like a
    wikilink, and citing nothing. Excluding a shape that is not a link is not
    the same as narrowing a clause until it reads as satisfied, and the
    exclusion is scoped: a dangling wikilink one line ABOVE a fence, or
    outside a span on the same line, still reddens the guard.

    WHY THIS IS NOT A PARITY TOGGLE, WHICH IS WHAT IT WAS. The first version
    flipped a boolean on any line whose first run was three or more backticks.
    Two defects followed, both measured rather than argued: two ordinary PROSE
    lines beginning with three backticks gave EVEN parity and silently
    swallowed everything between them, count line byte-identical to pristine
    and no skip at all (G1); and a four-backtick fence wrapping a
    three-backtick example was read as prose, so the guard went FAIL on
    correct content (F1). Fences now track the open run's CHARACTER and
    LENGTH.

    P3 - A CLOSER MAY BE INDENTED FURTHER THAN ITS OPENER. CommonMark caps a
    closer at three spaces, and applying that cap made a fence opened at two
    spaces and closed at four - what a fence in a list item looks like when
    the closer carries the item's indent - report as UNTERMINATED and fail the
    commit. That was F1's mistake with the opposite sign. The cap is therefore
    applied to openers only. This errs toward CLOSING a fence, which loses a
    little strictness and cannot swallow a file.

    STATED RESIDUALS - THIS MODEL IS LINE-ORIENTED AND HAS NO CONTAINER MODEL.
    Markdown containers are not tracked, so a fence is not recognised as
    belonging to a list item or a blockquote, and an indented code block is
    not recognised at all. Three shapes are therefore still reported as
    dangling citations when they are code. They are recorded here with their
    exact inputs, and pinned by name in the test module, rather than guessed
    at - a wrong container model would trade this loud failure for a SILENT
    one, which is the worse of the two:

      P1  a fenced block inside a NESTED list item, where the fence is
          indented four spaces and so is never seen as an opener:
          "- outer" / "  - inner" / "" / "    ```" / "    [[x]]" / "    ```"
      P2  a fenced block inside a BLOCKQUOTE, where every line is prefixed
          "> " and the fence never starts the line:
          "> ```" / "> [[x]]" / "> ```"
      P4  a top-level FOUR-SPACE INDENTED code block, which uses no fence at
          all: "" / "    [[x]]" / "    key = 1"

    A multi-line inline span - a run of backticks opened on one line and
    closed on the next - is a fourth residual, for the same reason: spans are
    matched within a line.

    Args:
        text: The markdown source.

    Returns:
        ``(body, unterminated)`` - the text with code regions replaced by
        blanks, and whether a fence was still open at end of file.
        UNTERMINATED IS RETURNED RATHER THAN SWALLOWED: an open fence blanks
        an arbitrary suffix, so a caller reporting a clean population over it
        would be reporting a green about a region it never read.
    """
    kept: list[str] = []
    run = ""
    for line in text.splitlines():
        match = _FENCE_LINE.match(line)
        if match is None:
            kept.append("" if run else _strip_inline_code(line))
            continue
        found = match.group("run")
        info = match.group("info")
        if not run:
            if len(match.group("indent")) > _MAX_FENCE_INDENT or (found[0] == "`" and "`" in info):
                # Too deeply indented to open a fence, or a backtick run whose
                # info string holds a backtick - which makes it inline code.
                kept.append(_strip_inline_code(line))
                continue
            run = found
            kept.append("")
            continue
        if found[0] == run[0] and len(found) >= len(run) and not info.strip():
            run = ""
        kept.append("")
    return "\n".join(kept), bool(run)


def _citation_targets(body: str) -> list[tuple[str, str]]:
    """Wikilink and markdown-link targets in an ALREADY code-blanked body.

    DELIBERATELY NARROWER THAN ``_link_targets``, AND THAT IS THE WHOLE POINT.
    ``_link_targets`` also harvests every backticked span, which is right for
    reachability - see its docstring - and catastrophic for resolution. The
    index today carries ``assert count == 0`` and ``git commit -F`` in
    backticks; a resolution check built on that extractor would demand both
    name files and would MANUFACTURE TWO FINDINGS THE MOMENT IT SHIPPED, in a
    guard the pre-commit and pre-push paths both run. So the two extractors
    stay separate on purpose. Neither is a refactor of the other, and merging
    them turns a green repository red.

    The caller passes the output of ``_outside_code`` rather than raw source, so
    that there is exactly one place in this module that decides what counts as
    fenced code and exactly one place that can get it wrong.

    Args:
        body: Markdown with code regions already blanked by ``_outside_code``.

    Returns:
        ``(kind, raw)`` pairs - kind being "wikilink" or "link" - in file
        order, duplicates collapsed, original spelling preserved so a finding
        can quote what the author actually wrote.
    """
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for kind, pattern in (("wikilink", _WIKILINK), ("link", _MDLINK)):
        for match in pattern.finditer(body):
            entry = (kind, match.group(1).strip())
            if entry[1] and entry not in seen:
                seen.add(entry)
                found.append(entry)
    return found


def _citation_resolves(memory_dir: Path, kind: str, raw: str) -> bool:
    """Whether one citation names a file that exists.

    THE URL EXCLUSION IS FOR MARKDOWN LINKS ONLY, and that asymmetry is
    deliberate. A markdown link is the correct way to cite a specification, so
    failing one would turn the guard red on the first note that did - the
    store carries none today, which is exactly why nothing else would notice.
    A WIKILINK carrying a scheme is not that: ``[[...]]`` names a note in this
    store by construction, so a colon in one is a broken link and is reported.
    Excluding it would silently forgive a citation that can never resolve,
    since a Windows filename cannot contain a colon at all.

    Args:
        memory_dir: The directory every citation is resolved relative to.
        kind: "wikilink" or "link".
        raw: The target exactly as written.

    Returns:
        True when the target names an existing file, and also when the target
        is a form that cites no file in this store - a bare ``#fragment`` in
        either shape, or an absolute URL or mail address in a markdown link.
    """
    target = raw.split("#", 1)[0].strip().replace("\\", "/")
    if not target:
        return True
    if kind == "wikilink":
        return (memory_dir / f"{target}.md").is_file()
    if _URL_SCHEME.match(target):
        return True
    if (memory_dir / target).is_file():
        return True
    return not target.lower().endswith(".md") and (memory_dir / f"{target}.md").is_file()


def _citation_findings(
    root: Path, memory_dir: Path, paths: list[Path], skips: list[Skip]
) -> tuple[int, list[str], list[str]]:
    """Resolve every citation in ``paths``.

    AN UNTERMINATED FENCE IS A FINDING, NOT A SKIP. It was a skip, and that
    was too weak: an open fence blanks an arbitrary SUFFIX of a file, so the
    guard would report a clean population over a region it never read. The
    first version could not even detect the case that actually swallowed - it
    tested fence-line PARITY, and the two-prose-line case that swallows has
    EVEN parity. Failing is safe here because an unterminated fence is
    malformed markdown that no correct note has: measured across the tracked
    store, zero files carry one.

    Args:
        root: The repository root, for rendering relative paths.
        memory_dir: The directory citations resolve against.
        paths: The files to read.
        skips: Skip records, appended to for anything unreadable.

    Returns:
        ``(citations checked, findings, files with an unterminated fence)``.
        The count is returned so a green verdict can state the population it
        covers - an empty population satisfies every zero, and a guard that
        checked nothing must not read the same as one that checked sixty.
    """
    checked = 0
    findings: list[str] = []
    unterminated_files: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            skips.append({"path": path.name, "reason": f"unreadable memory file: {_exc_text(exc)}"})
            continue
        body, unterminated = _outside_code(text)
        if unterminated:
            unterminated_files.append(_rel(root, path))
        for kind, raw in _citation_targets(body):
            checked += 1
            if not _citation_resolves(memory_dir, kind, raw):
                quoted = f"[[{raw}]]" if kind == "wikilink" else f"]({raw})"
                findings.append(f"{_rel(root, path)} cites {quoted}, which does not exist")
    return checked, findings, unterminated_files


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
    """Assert the memory index and its leaves account for each other BOTH ways.

    ONE PARTITION, THREE ARMS, ONE VERDICT. Reachability is a partition claim
    and this guard used to assert only one side of it: every leaf is named by
    a token the index can reach. A token naming NOTHING is an element that
    simply matches nothing, so the other side was never asserted at all. Two
    faults lived in that gap and both reported CLEAN (CS-890):

      LEG 0  every leaf is reachable from MEMORY.md. Unchanged, and carried
             with its own positive control, because a repair that adds a
             direction while silently breaking the one that already worked is
             a net loss.
      LEG 1  every citation in an ordinary leaf resolves. A note pointing at a
             lesson that is not there sends the next session nowhere.
      LEG 2  every citation in MEMORY.md and its INDEX_*.md children resolves.
             Worse than an unindexed leaf: the index IS the routing table.

    LEG 1 and LEG 2 partition the store between them - a file is a routing
    file or it is an ordinary leaf, never both - so a dangling link is
    reported once, under the heading whose remedy actually applies.

    THIS IS CS-497's SHAPE ONE STORE OVER: a partition asserted one way round
    is a subset check wearing a partition's name.

    Args:
        root: The repository root.

    Returns:
        The guard record and its skip records.
    """
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

    routing = [index, *(leaf for leaf in leaves if leaf.name.lower().startswith("index_"))]
    ordinary = [leaf for leaf in leaves if not leaf.name.lower().startswith("index_")]
    routes_checked, dangling_routes, routes_open = _citation_findings(
        root, memory_dir, routing, skips
    )
    refs_checked, dangling_refs, refs_open = _citation_findings(root, memory_dir, ordinary, skips)
    detail.append(
        f"index citations resolved (outside code): "
        f"{routes_checked - len(dangling_routes)} of {routes_checked}"
    )
    detail.append(
        f"leaf citations resolved (outside code): "
        f"{refs_checked - len(dangling_refs)} of {refs_checked}"
    )

    sections = (
        (
            [_rel(root, leaf) for leaf in unreachable],
            "UNREACHABLE - this is DRIFT, not a style point:",
            "Fix by adding a one-line hook to the index. Do NOT delete the leaf and "
            "do NOT unindex a file to save bytes (CONVENTIONS 11).",
        ),
        (
            dangling_routes,
            "THE INDEX ROUTES TO A FILE THAT DOES NOT EXIST:",
            "The index is the routing table, so a ghost entry misroutes every later "
            "session. Fix the target or drop the entry - do NOT create an empty file "
            "to satisfy the link.",
        ),
        (
            dangling_refs,
            "A LEAF CITES A NOTE THAT DOES NOT EXIST:",
            "Point it at the note that owns the lesson, or drop the reference. A "
            "dangling citation in the durable store sends the next session to a file "
            "that is not there.",
        ),
        (
            sorted(set(routes_open + refs_open)),
            "AN UNTERMINATED CODE FENCE HID THE REST OF THE FILE:",
            "Everything after the opening fence was read as code, so the citations "
            "in it were NOT checked and the counts above do not cover them. Close "
            "the fence. A line of prose that merely BEGINS with three backticks "
            "opens one under CommonMark - give it an indent or reword it.",
        ),
    )
    failed = False
    for entries, heading, remedy in sections:
        if entries:
            failed = True
            detail.append(heading)
            detail.extend(f"  {entry}" for entry in entries)
            detail.append(remedy)
    if failed:
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
# A FILE WITH DATED HEADINGS AND NO DECLARATION IS DRIFT TOO, and the first
# build of this repair got that wrong. It recorded a skip and passed, on the
# reasoning that the live arm had nothing to grade. But CS-840 was filed
# BECAUSE this guard reported its population instead of failing on it, and its
# item note says in terms that a guard which reports cannot lose. Shipping a
# fresh skip-instead-of-fail inside the repair reproduced the defect one level
# along, in the fix for it. An undeclared file is the case where this guard
# cannot tell a record from a live section marked historical - which is the
# most important case to fail on, not the one to excuse.


STATUS_DATE = "status"
PROVENANCE_DATE = "provenance"

LIVE = "LIVE"
HISTORICAL = "HISTORICAL"

# The declaration, as it appears in the header of a file that carries dated
# headings. Read only from the header - the region before the first level-2
# heading - so a quotation of the sentence further down the file cannot be
# mistaken for the file's own declaration.
STATUS_DECLARATION = re.compile(r"^\*\*Section status:[ \t]*(LIVE|HISTORICAL)\b", re.MULTILINE)

# A heading of ANY level, and the no-space form too. CommonMark does not call
# "##S" a heading, but ending the header early is the conservative direction -
# it shrinks the region a declaration may hide in rather than widening it.
_ATX_HEADING = re.compile(r"^[ \t]{0,3}#{1,6}")
_SETEXT_UNDERLINE = re.compile(r"^[ \t]{0,3}(?:=+|-+)[ \t]*$")
_FENCE_OPEN = re.compile(r"^[ \t]{0,3}(```|~~~)")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

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
    {"from", "to", "on", "in", "into", "out", "of", "by", "at", "as", "via", "continued", "and"}
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

    The gap may hold connectives, the name of a file being moved, and OTHER
    VOCABULARY VERBS - nothing else. Admitting other verbs is what lets a
    terminal verb keep hold of a date that a filing verb also sits beside:
    in "Superseded - filed 2031-02-03" the gap after "Superseded" is a
    connective and a filing verb, so "Superseded" still governs. Ordinary
    prose in the gap still disqualifies, which is what stops "closed" the
    ADJECTIVE claiming a date from the far end of a sentence.

    Args:
        gap: The text between the end of the verb and the start of the date.

    Returns:
        True when the gap holds only connectives, file names and other verbs.
    """
    remainder = _PATH_TOKEN.sub(" ", gap)
    return all(
        word.lower() in _GAP_CONNECTIVES or _is_vocabulary_word(word)
        for word in _GAP_WORD.findall(remainder)
    )


def _is_vocabulary_word(word: str) -> bool:
    """Is ``word`` one of the idioms this guard already knows?

    Args:
        word: A single word from a gap.

    Returns:
        True when some idiom matches the word exactly.
    """
    return any(
        match is not None and match.group(0) == word
        for pattern in DATE_IDIOMS
        for match in [pattern.search(word)]
    )


def classify_dated_heading(heading: str) -> str | None:
    """Classify a heading's date by SHAPE as a status date or a provenance date.

    A verb qualifies only if it GOVERNS the date - see ``_governs_the_date``.

    A GOVERNING TERMINAL VERB BEATS A FILING VERB WHEREVER IT SITS, and
    nearest-wins only breaks ties WITHIN a class. Letting proximity decide
    across the classes was a compliance failure against the ruling this
    function implements - the ruling says a terminal-state verb before the
    date IS a status date, and nearest-wins silently dropped it whenever a
    filing verb sat closer. "Superseded - filed 2031-02-03" read as
    provenance, which meant the guard's own error message - telling an author
    to put the date after a provenance verb - doubled as a recipe for
    laundering a historical section into a live file.

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

    # STATUS first: the first class with any governing verb decides, so a
    # terminal verb anywhere before the date outranks every filing verb.
    for family, patterns in ((STATUS_DATE, STATUS_IDIOMS), (PROVENANCE_DATE, PROVENANCE_IDIOMS)):
        nearest: int | None = None
        for pattern in patterns:
            for match in pattern.finditer(lead):
                if not _governs_the_date(lead[match.end() :]):
                    continue
                if nearest is None or match.end() > nearest:
                    nearest = match.end()
        if nearest is not None:
            return family
    return None


def _strip_unrendered(lines: list[str]) -> list[str]:
    """Blank out every line a reader of the RENDERED document cannot see.

    THE DECLARATION MUST SAY WHAT THE READER SEES (CS-840). Reading raw text
    meant a file could be forged from inside itself: three invisible lines at
    the top -

        <!--
        **Section status: HISTORICAL.**
        -->

    - and the guard read HISTORICAL while every human reading the file saw
    LIVE. A fenced code block did the same. Both are removed before the
    declaration is looked for, so a declaration nobody can see is not a
    declaration.

    An UNTERMINATED fence or comment blanks everything after it rather than
    being ignored: text the renderer will swallow is text the reader cannot
    see, and guessing the author meant otherwise is how the forge got in.

    Args:
        lines: The header lines, in order.

    Returns:
        The same number of lines, with unrendered ones replaced by blanks.
    """
    out: list[str] = []
    fence: str | None = None
    in_comment = False
    for line in lines:
        if fence is not None:
            out.append("")
            if line.strip().startswith(fence):
                fence = None
            continue
        if in_comment:
            out.append("")
            if "-->" in line:
                in_comment = False
            continue
        opener = _FENCE_OPEN.match(line)
        if opener:
            fence = opener.group(1)
            out.append("")
            continue
        without_comments = _HTML_COMMENT.sub(" ", line)
        if "<!--" in without_comments:
            in_comment = True
            out.append("")
            continue
        # A DECLARATION IS A PARAGRAPH, NEVER A TABLE CELL. A pipe table with
        # no leading pipe puts its first cell at the start of the line, which
        # is a third way to write a declaration the rendered document shows
        # only as one cell of a table. No real declaration contains a pipe.
        out.append("" if "|" in without_comments else without_comments)
    return out


def _header_lines(text: str) -> list[str]:
    """Return the document header - everything before its SECOND heading.

    A HEADING OF ANY LEVEL AND ANY STYLE ENDS THE HEADER (CS-840). Ending it
    only at ``## `` meant a level-three heading, a setext heading, or a line
    like ``##S`` could sit above a declaration and the declaration was still
    read as the file's own - so a SECTION could declare on the file's behalf
    simply by being level three.

    The first heading is allowed through because it is the document title;
    every file in this repository opens with one and the declaration sits
    directly beneath it. The second heading ends the header, whatever it is.

    Args:
        text: A whole markdown document.

    Returns:
        The header lines, with unrendered content blanked out.
    """
    lines = text.splitlines()
    header: list[str] = []
    headings = 0
    for index, line in enumerate(lines):
        previous = lines[index - 1] if index else ""
        is_setext = bool(_SETEXT_UNDERLINE.match(line)) and bool(previous.strip())
        if _ATX_HEADING.match(line) or is_setext:
            headings += 1
            if headings > 1:
                break
        header.append(line)
    return _strip_unrendered(header)


def read_status_declaration(text: str) -> str | None:
    """Read a document's own declaration of whether its sections are live.

    Read from the HEADER only, and only from text the rendered document
    actually shows - see :func:`_header_lines` and :func:`_strip_unrendered`
    for the two ways this was forgeable before.

    Args:
        text: A whole markdown document.

    Returns:
        ``LIVE``, ``HISTORICAL``, or None when the file does not declare.
    """
    match = STATUS_DECLARATION.search("\n".join(_header_lines(text)))
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
    undeclared: list[str] = []
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
            undeclared.append(relative)
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
    if undeclared:
        detail.append(
            "DRIFT - files carrying dated headings that declare no section status. This "
            "guard cannot tell a record from a live section marked historical without the "
            "declaration, and REPORTING that rather than failing on it is the exact defect "
            "CS-840 was filed for. Add one line to the file's header, above its first "
            f"level-2 heading: **Section status: {LIVE}** or **Section status: "
            f"{HISTORICAL}**:"
        )
        detail.extend(f"  {item}" for item in undeclared)
    if historical_in_live:
        detail.append(
            f"DRIFT - a {STATUS_DATE} date inside a file that declares itself {LIVE}. The "
            "heading marks its own section historical while the file says its sections are "
            "current, and those two cannot both be true. RESOLVE IT BY DECIDING WHICH IS "
            "TRUE, and then say so: if the section really is history, MOVE it to a file "
            f"that declares itself {HISTORICAL}, or change this file's declaration. If the "
            "section is current, the heading is misdescribing it and the HEADING is what "
            "has to change. Do NOT reword the heading to get past this check while leaving "
            "a historical section in a live file, and do NOT delete the date - both leave "
            "the reader believing something the tree does not support:"
        )
        detail.extend(f"  {item}" for item in historical_in_live)
    if unclassified:
        detail.append(
            "DRIFT - dated headings in an idiom the closed vocabulary does not cover. "
            "Whoever wrote each one decides what its date MEANS and makes the heading say "
            f"it: a {STATUS_DATE} date, which marks the section historical, or a "
            f"{PROVENANCE_DATE} date, which records only when the text was filed. If the "
            "idiom is a real one this project should know, widen the vocabulary in "
            "tools/drift_guard.py deliberately. Choose by what is TRUE of the section, "
            "never by which answer clears the check, and do NOT delete the date:"
        )
        detail.extend(f"  {item}" for item in unclassified)
    if undeclared or historical_in_live or unclassified:
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


# --- guard j: item-notes index ----------------------------------------------

# docs/item_notes.md stopped holding item bodies on 2026-08-25 and became an
# index over docs/item_notes/. THE INDEX IS A RESTATED FACT, which CLAUDE.md
# section 4 names as the one thing that will drift, so it is checked in both
# directions rather than trusted: a routed item with no section is red, a
# section with no routing row is red, and a row naming the wrong leaf is red.
#
# SET EQUALITY ALONE WOULD NOT BE ENOUGH. Two sets can match exactly while a
# row points at the wrong leaf, which sends a reader to a file that does not
# hold the block and reads as "the detail was never written" - the same silent
# shape as a missing body. The destination is compared per item, not pooled.
#
# AN EMPTY FAMILY IS A SKIP, NOT A PASS. Zero routed items and zero sections
# satisfy every equality below for free. Session 40 recorded six instances of
# an empty population passing an assertion of zero and being read as evidence,
# so the empty case is graded explicitly and names itself in the skip list.
# A HALF-empty family is different and is FAIL: rows routing to nothing, or
# sections nothing routes to, is drift rather than a wrong root.
ITEM_NOTES_INDEX_RELATIVE = "docs/item_notes.md"
ITEM_NOTES_LEAF_DIR_RELATIVE = "docs/item_notes"

_ITEM_NOTES_SECTION = re.compile(r"(?m)^## (CS-G?\d+)[ \t]*$")
# A routing row: "| CS-nnn | `docs/item_notes/<leaf>.md` |". The leaf is read
# from the row rather than assumed, so a row naming a path outside the family
# is reported as the wrong destination instead of quietly matching.
_ITEM_NOTES_ROW = re.compile(
    r"(?m)^\|\s*(CS-G?\d+)\s*\|\s*`([^`]+)`\s*\|\s*$",
)


def item_notes_routing(text: str) -> dict[str, str]:
    """Return item id mapped to the leaf path each routing row names.

    Args:
        text: The index file's text.

    Returns:
        Item id mapped to the repo-relative leaf path written in its row.
    """
    return {match.group(1): match.group(2) for match in _ITEM_NOTES_ROW.finditer(text)}


def item_notes_sections(root: Path) -> tuple[dict[str, str], list[str]]:
    """Return item id mapped to the leaf holding it, plus ids found twice.

    Args:
        root: The repository root under audit.

    Returns:
        (item id mapped to repo-relative leaf path, duplicated ids).
    """
    found: dict[str, str] = {}
    duplicated: list[str] = []
    leaf_dir = root / ITEM_NOTES_LEAF_DIR_RELATIVE
    for leaf in sorted(leaf_dir.glob("*.md")):
        relative = f"{ITEM_NOTES_LEAF_DIR_RELATIVE}/{leaf.name}"
        try:
            text = leaf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in _ITEM_NOTES_SECTION.finditer(text):
            item = match.group(1)
            if item in found:
                duplicated.append(f"{item} in {found[item]} and {relative}")
                continue
            found[item] = relative
    return found, duplicated


def guard_index(root: Path) -> tuple[Guard, list[Skip]]:
    """Assert the item-notes index routes to exactly the sections that exist.

    Args:
        root: The repository root under audit.

    Returns:
        (the guard verdict, skip records).
    """
    skips: list[Skip] = []
    name = "item-notes index"
    index_path = root / ITEM_NOTES_INDEX_RELATIVE
    leaf_dir = root / ITEM_NOTES_LEAF_DIR_RELATIVE

    try:
        index_text = index_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        skips.append(
            {"path": ITEM_NOTES_INDEX_RELATIVE, "reason": f"index not read ({_exc_text(exc)})"}
        )
        return _guard("j", name, "WARN", ["the index was not read - nothing was graded"]), skips

    if not leaf_dir.is_dir():
        skips.append(
            {
                "path": ITEM_NOTES_LEAF_DIR_RELATIVE,
                "reason": "leaf directory absent - a wrong root rather than drift",
            }
        )
        return (
            _guard("j", name, "WARN", [f"{ITEM_NOTES_LEAF_DIR_RELATIVE} is not a directory"]),
            skips,
        )

    bodies = [match.group(1) for match in _ITEM_NOTES_SECTION.finditer(index_text)]
    routed = item_notes_routing(index_text)
    sections, duplicated = item_notes_sections(root)

    detail = [
        f"routing rows in {ITEM_NOTES_INDEX_RELATIVE}: {len(routed)}",
        f"sections under {ITEM_NOTES_LEAF_DIR_RELATIVE}/: {len(sections)}",
    ]

    if not routed and not sections:
        skips.append(
            {
                "path": ITEM_NOTES_LEAF_DIR_RELATIVE,
                "reason": (
                    "the family holds no routing row and no section - every equality "
                    "below is satisfied by an empty population, so nothing was graded"
                ),
            }
        )
        detail.append("NOTHING TO GRADE - an empty family is a skip, never a pass")
        return _guard("j", name, "WARN", detail), skips

    problems: list[str] = []
    if bodies:
        problems.append(
            "the index carries item bodies, which are invisible to a reader following "
            "the routing table - move them to the leaf the membership rule names:"
        )
        problems.extend(
            f"  {ITEM_NOTES_INDEX_RELATIVE} holds a section for {item}" for item in bodies
        )

    if duplicated:
        problems.append("an item carries detail in more than one leaf:")
        problems.extend(f"  {row}" for row in duplicated)

    unrouted = sorted(set(sections) - set(routed))
    if unrouted:
        problems.append("these carry detail no routing row names, so nothing can find them:")
        problems.extend(f"  {item} in {sections[item]}" for item in unrouted)

    dangling = sorted(set(routed) - set(sections))
    if dangling:
        problems.append("these are routed to a section that does not exist:")
        problems.extend(f"  {item} routed to {routed[item]}" for item in dangling)

    misrouted = sorted(
        item for item in set(routed) & set(sections) if routed[item] != sections[item]
    )
    if misrouted:
        problems.append("these are routed to the wrong leaf:")
        problems.extend(
            f"  {item} routed to {routed[item]}, detail is in {sections[item]}"
            for item in misrouted
        )

    if problems:
        return _guard("j", name, "FAIL", detail + problems), skips

    detail.append(f"every routed item resolves to its own section across {len(sections)} id(s)")
    return _guard("j", name, "PASS", detail), skips


# --- guard k: the tier 1 budget ---------------------------------------------

# THE FACT THIS GUARD OWNS: how long tier 1 is allowed to take. CS-896 found it
# stated in THREE live places, none of which the lane had met in months. That is
# exactly the shape CLAUDE.md section 4 exists to prevent - a restated fact is a
# fact that will drift - and here the three copies drifted together into a
# target nobody had measured against.
#
# THREE LEVELS, THREE DIFFERENT JOBS, and conflating any two of them is the
# defect this guard exists to keep out:
#
#   budget   reported every run, warns loudly over, and NEVER fails. The lane
#            "must never be red" (CONVENTIONS.md section 8) and the runner's own
#            variance was measured at about 9 per cent on a byte-identical tree,
#            so a budget that hard-failed on noise would be red for no defect.
#   ceiling  FAILS the lane and names the number, strictly BELOW the cutoff.
#            This is the level that converts a breach into an actionable red.
#   cutoff   `timeout-minutes`, which CANCELS. A cancelled run is evidence of
#            nothing: nothing failed and nothing was measured. Raising it turns
#            a runaway detector into a budget and removes the only signal that
#            the lane is growing.
#
# THE ORDER IS WHAT MAKES THEM THREE RATHER THAN ONE, so the order is what this
# guard asserts and the values are what it merely reports. A number re-derived
# from a later measurement then costs no test edit, while an order violated is
# drift on every tree.

TIER1_WORKFLOW_RELATIVE = ".github/workflows/tier1.yml"
TIER1_BUDGET_KEY = "TIER1_BUDGET_SECONDS"
TIER1_CEILING_KEY = "TIER1_CEILING_SECONDS"
TIER1_TIMEOUT_KEY = "timeout-minutes"
SECONDS_PER_MINUTE = 60

# -- THE RECORDED LEVELS: A TWO-WAY RATCHET, NOT A COPY OF THE WORKFLOW. ------
#
# WHY THESE EXIST AT ALL. The order relation alone - budget < ceiling < cutoff -
# is satisfied by ANY three ascending numbers, so it grades the SHAPE and says
# nothing about the SIZE. MEASURED on the candidate this replaces: raising the
# cutoff alone from ten minutes to sixty passed every guard and every arm;
# raising all three together to 3000, 3500 and sixty passed; dropping the budget
# to one second passed. CS-896 was filed because this lane drifted past its
# stated target with nothing failing, and a repair that permits exactly that
# drift one level up is not a repair.
#
# THE SHAPE IS CS-891's, AND IT IS DELIBERATELY TWO-WAY. A pin that only caught
# inflation would be satisfied by lowering the number to something the lane can
# never breach, which buys the same silence from the other side. So the workflow
# must state EXACTLY these, and any move - up or down - is red until this line
# moves with it inside the same diff. That is the whole mechanism: a number
# somebody has to defend in a review, rather than a capitalised sentence that
# nothing enforces.
#
# THEY ARE INTEGER LITERALS ON PURPOSE. Deriving a bound from the thing it
# bounds - the `= len(the_table_it_limits)` tautology - is filed twice in this
# repository and makes both directions true by construction. tests/
# test_tier1_budget.py reads THIS MODULE'S SOURCE and refuses anything but a
# literal here.
#
# THE CUTOFF IS POLICY AND NOT A TUNABLE. The workflow says in capitals not to
# raise it to accommodate a slower lane; this is what makes that sentence cost
# something. It is pinned to its exact value rather than bounded, because there
# is no direction it is allowed to move on its own.
TIER1_RECORDED_BUDGET = 380
TIER1_RECORDED_CEILING = 420
TIER1_POLICY_CUTOFF_MINUTES = 10

# -- THE RESTATEMENT SCAN, AND WHY IT IS THIS NARROW. ------------------------
#
# A second owner of the number is a line that names the lane AND hangs a
# duration on a bound noun. All three conjuncts are required, because each one
# alone manufactures findings: prose about how long a run TOOK is a measurement
# and not a target, and a budget sentence about something else entirely is not
# about this lane at all. Both of those bounds are graded in
# tests/test_tier1_budget.py rather than asserted here, because a scan nobody
# can force to be wrong is not a scan.
#
# THE SPELLINGS WERE THE HOLE, AND THE WORST ONE WAS THE GUARD'S OWN OUTPUT.
# The first build required a unit WORD - "510 seconds", "9 minutes" - so it
# could not see `510s`, which is the spelling the workflow's own duration report
# emits AND the spelling this guard's own detail lines emit. A guard blind to
# the exact string its subject prints is a guard that will be walked past. Five
# more were MEASURED silent and are now covered: `8m30s`, `0:08:30`,
# `0.15 hours`, `510000 ms`, and a bound noun sitting on a different line from
# the duration it binds.
#
# EACH ALTERNATIVE IS SPELLED AS DATA rather than inlined into one pattern, so
# tests/test_tier1_budget.py can pin the membership in both directions and
# exercise every member. The first build inlined them, and deleting eighteen of
# the nineteen number words - or four of the five bound nouns - left the suite
# green, because the arms only ever exercised one alternative each.
TIER1_NUMBER_WORDS = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"fifteen|twenty|thirty|forty|forty-five|sixty|ninety"
)
TIER1_UNIT_WORDS = r"milliseconds?|msecs?|minutes?|mins?|seconds?|secs?|hours?|hrs?|ms"

#: A duration spelled with its unit as a word: "510 seconds", "0.15 hours".
TIER1_SPELLED_DURATION = (
    r"\b(?:\d+(?:\.\d+)?|" + TIER1_NUMBER_WORDS + r")[\s-]*(?:" + TIER1_UNIT_WORDS + r")\b"
)
#: A duration spelled with a bare unit SUFFIX: "510s", "9m", "2h". This is the
#: form GitHub's own summary and this guard's own detail lines use.
TIER1_SUFFIXED_DURATION = r"\b\d+(?:\.\d+)?[ ]?[smh]\b"
#: A compound duration: "8m30s", "1h20m".
TIER1_COMPOUND_DURATION = r"\b\d+[ ]?[hm][ ]?\d+[ ]?[ms]\b"
#: A duration spelled as a clock reading: "0:08:30", "10:30". The minute and
#: second fields are bounded to 0-59 so a `file:line` citation cannot match.
TIER1_CLOCK_DURATION = r"\b\d{1,2}:[0-5]\d(?::[0-5]\d)?\b"

TIER1_DURATION = re.compile(
    "|".join(
        (
            TIER1_COMPOUND_DURATION,
            TIER1_CLOCK_DURATION,
            TIER1_SPELLED_DURATION,
            TIER1_SUFFIXED_DURATION,
        )
    ),
    re.IGNORECASE,
)

TIER1_BOUND_NOUNS = ("target", "budget", "ceiling", "cutoff", "limit")
TIER1_BOUND_NOUN = re.compile(r"\b(?:" + "|".join(TIER1_BOUND_NOUNS) + r")\b", re.IGNORECASE)

#: A BARE INTEGER HUNG DIRECTLY OFF A BOUND NOUN, carrying no unit at all:
#: "budget: 540", "ceiling 570", "cutoff 600". MEASURED silent against every
#: scan above, because every one of them needs a unit somewhere and this shape
#: leaves the unit to the noun. One README line spelling all three levels this
#: way restated the whole set and nothing saw it.
#:
#: THE ADJACENCY IS THE ENTIRE BOUND. Only an optional colon or equals and
#: horizontal whitespace may sit between the noun and the number, so "the docs
#: size budget is 40 KB" does not match, a markdown table cell does not match,
#: and neither does a constant whose name merely ENDS in one of these words -
#: an underscore is a word character, so there is no boundary before it.
#: Widening this to "a bound noun and a number somewhere on one line" would
#: flag every table in the repository.
TIER1_BOUND_NUMBER = re.compile(
    r"\b(?:" + "|".join(TIER1_BOUND_NOUNS) + r")\b[ \t]*[:=]?[ \t]*\d+\b", re.IGNORECASE
)

#: THE LANE SPELLINGS, AND THERE ARE TWO RATHER THAN THREE. The first build
#: carried `tier1` as a third alternative beside `tier[\s-]?1`, which already
#: matches it - an EQUIVALENT mutant that no arm could ever kill. It is dropped
#: rather than graded, because a rung that cannot fail is not a rung.
TIER1_LANE_SPELLINGS = (r"tier[\s-]?1", r"fast lane")
TIER1_LANE = re.compile(r"\b(?:" + "|".join(TIER1_LANE_SPELLINGS) + r")\b", re.IGNORECASE)

#: How far from a duration line the lane token and the bound noun may sit. BOTH
#: are windowed. The first build windowed only the lane and required the bound
#: noun on the duration's own line, so a target split over two lines - the way
#: prose wraps - was invisible.
TIER1_LANE_WINDOW = 6

#: A SECOND FILE DECLARING THE LANE'S OWN ENV KEYS, WITH A VALUE. This is the
#: most literal second owner there is and the prose scan could not see it: a
#: full env block copied into another workflow states the numbers in machine-
#: readable form and spells no sentence at all. MEASURED silent on the candidate
#: this replaces.
#:
#: THE VALUE IS WHAT MAKES IT A STATEMENT. This module and the test module both
#: NAME these keys - they have to, to grade them - and naming a key is not
#: owning its number. So a digit is required after the separator, which is
#: exactly the difference between a grader and an owner.
TIER1_ENV_KEY_STATED = re.compile(
    r"\b(?:" + TIER1_BUDGET_KEY + r"|" + TIER1_CEILING_KEY + r")\b[\"']?[ \t]*[:=][ \t]*[\"']?\d"
)

# WHAT THIS GUARD DECLINES TO READ, STATED AS DATA WITH ITS REASONS. These files
# RECORD what was true or measured at a time; they do not configure the lane. A
# ledger entry is append-only by docs/LEDGER.md's own line 16, and an item LINE
# keeps the premise it was filed with while the correction lives in the note -
# both are settled practice, and neither is a second owner.
#
# THE PRICE IS STATED RATHER THAN HIDDEN. An exclusion nobody measures is a hole
# nobody counts, so the guard reports WHICH declined file actually carried a
# restatement rather than only how many it declined. A count alone answers how
# many reads a reason forgives and never which, which is CS-893's finding.
TIER1_NARRATIVE_RECORD = (
    ("docs/LEDGER.md", "append-only completion record - nothing in it is ever edited"),
    ("ROADMAP.md", "an item LINE keeps the premise it was filed with"),
    ("BACKLOG.md", "aspirational lines, never a statement of the lane's target"),
    ("WAKEUP_NOTES.md", "a session record, rewritten every session"),
    ("docs/GATED.md", "records what is blocked, not what the lane targets"),
    ("docs/history_notes.md", "deep archive of pruned notes and retired entries"),
    ("docs/item_notes.md", "the index over per-item detail, which records measurements"),
)
TIER1_NARRATIVE_PREFIXES = (
    ("docs/item_notes/", "per-item detail records what was measured and when"),
    ("docs/_archive/", "dated artifacts, excluded from a search for current truth"),
    ("memory/", "durable cross-session facts, not the lane's configuration"),
)


def stated_timeouts(text: str) -> list[str]:
    """Every ``timeout-minutes:`` line in the workflow, one per job that states it.

    Args:
        text: The workflow source.

    Returns:
        The matched lines.
    """
    return re.compile(rf"^[ \t]*{re.escape(TIER1_TIMEOUT_KEY)}:", re.MULTILINE).findall(text)


def _tier1_declaration(
    text: str, key: str, *, per_job: bool = False
) -> tuple[int | None, str | None]:
    """Read a whole-number declaration that every statement of must agree on.

    The key is matched only at the start of a line, so prose naming it in a
    comment is not a second declaration - which matters, because the workflow's
    own comments have to be able to explain what the key is for.

    ONE STATEMENT PER JOB RATHER THAN ONE PER FILE, and the difference is the
    lane's shape rather than a weakening. ``timeout-minutes`` is a JOB key, so a
    lane with two jobs states it twice and neither statement is a restatement of
    the other - there is no single place it could be written once. What the rule
    is FOR is that nobody raises one job's cutoff quietly, and disagreement is
    what catches that now. A lane whose shards carry different cutoffs has no
    cutoff, only the larger one.

    Args:
        text: The workflow source.
        key: The key to read.
        per_job: True for a key GitHub reads per job, which a multi-job lane
            therefore states more than once. False - the default - for a key
            with one place to live, where a second statement is a restatement
            and the thing this guard exists to catch.

    Returns:
        (the value, None) when the declarations are well-formed and agree, and
        (None, the problem) otherwise.
    """
    stated = re.compile(rf"^[ \t]*{re.escape(key)}:", re.MULTILINE).findall(text)
    if not stated:
        return None, f"{key} is not stated, so nothing owns that level"
    if not per_job and len(stated) > 1:
        return None, f"{key} is stated {len(stated)} times - it must have exactly one owner"
    valued = re.compile(
        rf"^[ \t]*{re.escape(key)}:[ \t]*[\"']?(\d+)[\"']?[ \t]*(?:#.*)?$", re.MULTILINE
    ).findall(text)
    if len(valued) != len(stated):
        return None, f"{key} is stated but its value is not a whole number"
    distinct = sorted(set(valued))
    if len(distinct) > 1:
        return None, (
            f"{key} is stated {len(stated)} times and they DISAGREE: {distinct}."
            " A per-job level must be the same level in every job"
        )
    return int(distinct[0]), None


def _tier1_narrative_reason(relative: str) -> str | None:
    """Why this path records a target rather than stating one, if it does.

    Args:
        relative: A repo-relative posix path.

    Returns:
        The reason, or None when the file is graded like any other.
    """
    for path, reason in TIER1_NARRATIVE_RECORD:
        if relative == path:
            return reason
    for prefix, reason in TIER1_NARRATIVE_PREFIXES:
        if relative.startswith(prefix):
            return reason
    return None


def _tier1_restatements(text: str) -> list[tuple[int, str]]:
    """Every line stating a tier 1 duration target, or declaring its env keys.

    THE ENV-KEY ARM DOES NOT NEED THE OTHER TWO CONJUNCTS. A line that declares
    this lane's own key with a value IS the number, in the form a runner reads;
    it needs no bound noun and no lane token nearby, because the key name is
    both of those.

    Args:
        text: The file's content.

    Returns:
        (line number, the stripped line) for each hit.
    """
    lines = text.splitlines()
    hits: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        if TIER1_ENV_KEY_STATED.search(line):
            hits.append((index + 1, line.strip()))
            continue
        bound_number = TIER1_BOUND_NUMBER.search(line)
        if not bound_number and not TIER1_DURATION.search(line):
            continue
        low = max(0, index - TIER1_LANE_WINDOW)
        high = min(len(lines), index + TIER1_LANE_WINDOW + 1)
        near = lines[low:high]
        # A bare number hung off a bound noun carries the bound WITH it, so the
        # window is only asked for one that is not already on this line.
        if not bound_number and not any(TIER1_BOUND_NOUN.search(one) for one in near):
            continue
        if any(TIER1_LANE.search(one) for one in near):
            hits.append((index + 1, line.strip()))
    return hits


def _tier1_second_owners(
    root: Path, files: list[Path], skips: list[Skip]
) -> tuple[list[str], int, int]:
    """Scan the tracked tree for a second statement of the lane's target.

    Args:
        root: The repository root under audit.
        files: The enumerated candidate files.
        skips: Skip records, appended to in place.

    Returns:
        (one record per restatement, files graded, files declined).
    """
    found: list[str] = []
    graded = 0
    declined = 0
    for path in files:
        relative = _rel(root, path)
        if relative == TIER1_WORKFLOW_RELATIVE:
            continue
        readable, _why = _classify(path)
        if not readable:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            skips.append({"path": relative, "reason": f"unreadable: {_exc_text(exc)}"})
            continue
        hits = _tier1_restatements(text)
        narrative = _tier1_narrative_reason(relative)
        if narrative is not None:
            declined += 1
            if hits:
                skips.append(
                    {
                        "path": relative,
                        "reason": f"states a tier 1 target and is not graded: {narrative}",
                    }
                )
            continue
        graded += 1
        found.extend(f"{relative}:{number}  {line}" for number, line in hits)
    return found, graded, declined


def _tier1_ratchet_problem(level: str, stated: int, recorded: int) -> str | None:
    """The two-way ratchet on one level, in CS-891's shape.

    Args:
        level: The level's name, for the message.
        stated: What the workflow states.
        recorded: What this module records as the maximum.

    Returns:
        The problem, or None when the two agree.
    """
    if stated > recorded:
        return (
            f"the {level} states {stated} against a recorded maximum of {recorded}."
            " The lane was allowed to grow. That is a finding to argue, not a line to"
            " type: make the lane faster, or raise the recorded maximum in this same"
            " change and say why - with a fresh timing sample from the runner"
        )
    if stated < recorded:
        return (
            f"the {level} states {stated} against a recorded maximum of {recorded}."
            f" The lane got faster and the maximum was not brought down with it."
            f" Lower it to {stated} - a slack maximum is banked room for a later"
            " inflation nobody will have to defend"
        )
    return None


def guard_tier1_budget(
    root: Path,
    files: list[Path],
    *,
    recorded_budget: int = TIER1_RECORDED_BUDGET,
    recorded_ceiling: int = TIER1_RECORDED_CEILING,
    policy_cutoff_minutes: int = TIER1_POLICY_CUTOFF_MINUTES,
) -> tuple[Guard, list[Skip]]:
    """Assert one file owns the tier 1 budget, its levels are ordered, and pinned.

    THE THREE RECORDED LEVELS ARE PARAMETERS WITH DEFAULTS, and that is not
    configurability - the driver never passes them. It exists so the ORDER arms
    in tests/test_tier1_budget.py can satisfy the ratchet and isolate the order
    relation. Without it every order arm would go red for two reasons at once,
    and deleting the order check would leave all of them green.

    Args:
        root: The repository root under audit.
        files: The enumerated candidate files.
        recorded_budget: The maximum the budget may state.
        recorded_ceiling: The maximum the ceiling may state.
        policy_cutoff_minutes: The exact value the runaway cutoff must state.

    Returns:
        (the guard record, skip records).
    """
    skips: list[Skip] = []
    name = "tier 1 budget"
    path = root / Path(TIER1_WORKFLOW_RELATIVE)
    if not path.is_file():
        skips.append(
            {"path": TIER1_WORKFLOW_RELATIVE, "reason": "absent - the tier 1 budget is ungraded"}
        )
        detail = [f"{TIER1_WORKFLOW_RELATIVE} does not exist, so no lane states a budget"]
        return _guard("k", name, "WARN", detail), skips
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        reason = _exc_text(exc)
        skips.append({"path": TIER1_WORKFLOW_RELATIVE, "reason": f"unreadable: {reason}"})
        detail = [f"{TIER1_WORKFLOW_RELATIVE} is unreadable: {reason}"]
        return _guard("k", name, "FAIL", detail), skips

    budget, budget_problem = _tier1_declaration(text, TIER1_BUDGET_KEY)
    ceiling, ceiling_problem = _tier1_declaration(text, TIER1_CEILING_KEY)
    # PER JOB, and only this one. `timeout-minutes` is a job key, so a two-shard
    # lane states it twice and neither statement restates the other. The budget and
    # the ceiling above are workflow-level `env:` and still have exactly one place
    # to live - a second statement of either is a restatement, which is what this
    # guard is for. MEASURED: a blanket relaxation let a job-level `env:` restate
    # the budget while the guard still printed one owner.
    minutes, minutes_problem = _tier1_declaration(text, TIER1_TIMEOUT_KEY, per_job=True)

    # -- E2: STATED BY EVERY JOB, not merely stated. --
    # A per-job key that one job omits is not inherited from the other; GitHub
    # applies its own 360-minute default to the silent one. MEASURED: deleting
    # `timeout-minutes` from the save shard left this guard green while that
    # shard's runaway detector became six hours. "Stated once per job" is only a
    # cutoff while the count matches the job count.
    declared_jobs = re.compile(r"^  ([A-Za-z0-9_-]+):$", re.MULTILINE).findall(
        text.partition("\njobs:\n")[2]
    )
    if minutes_problem is None and len(stated_timeouts(text)) != len(declared_jobs):
        minutes = None
        minutes_problem = (
            f"{TIER1_TIMEOUT_KEY} is stated {len(stated_timeouts(text))} time(s) for"
            f" {len(declared_jobs)} job(s) {sorted(declared_jobs)} - a job that states no"
            " cutoff inherits the platform default instead of this lane's"
        )
    problems = [item for item in (budget_problem, ceiling_problem, minutes_problem) if item]

    detail = [f"one owner: {TIER1_WORKFLOW_RELATIVE}"]
    if budget is not None and ceiling is not None and minutes is not None:
        cutoff = minutes * SECONDS_PER_MINUTE
        detail.append(f"budget {budget}s - reported every run, warns over, never fails")
        detail.append(f"ceiling {ceiling}s - fails the lane and names the number")
        detail.append(f"cutoff {cutoff}s ({minutes} min) - cancels, and proves nothing")
        detail.append(
            f"ratchet: budget and ceiling pinned two-way at {recorded_budget} and "
            f"{recorded_ceiling}; the cutoff is policy at {policy_cutoff_minutes} min"
        )
        if not budget < ceiling < cutoff:
            problems.append(
                f"the levels are out of order: budget {budget}s, ceiling {ceiling}s, "
                f"cutoff {cutoff}s. Each must sit strictly below the next, or a breach "
                f"is handed back to the canceller and reports nothing"
            )
        problems.extend(
            problem
            for problem in (
                _tier1_ratchet_problem("budget", budget, recorded_budget),
                _tier1_ratchet_problem("ceiling", ceiling, recorded_ceiling),
            )
            if problem is not None
        )
        if minutes != policy_cutoff_minutes:
            problems.append(
                f"the runaway cutoff states {minutes} min against a policy of "
                f"{policy_cutoff_minutes} min. IT IS NOT A TUNABLE. Raising it turns a "
                f"runaway detector into a budget and removes the only signal that the "
                f"lane is growing; lowering it hands a slow run back to the canceller, "
                f"which reports nothing. The ceiling is the level that moves"
            )

    found, graded, declined = _tier1_second_owners(root, files, skips)
    detail.append(f"graded {graded} tracked file(s) for a second statement of the target")
    detail.append(f"declined {declined} file(s) of the append-only record - see the skip list")
    if found:
        problems.append("these state a tier 1 duration target and the workflow already owns it:")
        problems.extend(f"  {item}" for item in found)

    if problems:
        return _guard("k", name, "FAIL", [*detail, "DRIFT:", *problems]), skips
    return _guard("k", name, "PASS", detail), skips


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
        guard_index,
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

    budget_guard, budget_skips = guard_tier1_budget(root, files)
    guards.append(budget_guard)
    skips.extend(budget_skips)

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
