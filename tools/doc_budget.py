#!/usr/bin/env python3
"""Clockspeed documentation size budgets.

Enforces exactly the table in CONVENTIONS.md section 2.1. Context is the binding
budget in every session, so a doc that grows past its budget spends the
operator's scarcest resource on every turn of every session.

    CLAUDE.md                  < 40 KB   hard fail
    any single auto-loaded     < 40 KB   hard fail
    memory/MEMORY.md (index)   < 20 KB   hard fail
    any memory/*.md leaf       <  6 KB   warn
    ROADMAP.md                 < 60 KB   warn, triggers a relocate pass

Exits non-zero only on a HARD failure. A WARN prints loudly and returns zero,
because a warn that blocks a commit gets disabled and then enforces nothing.

THE GUIDANCE IS NOT "TRIM". It is RELOCATE, DO NOT DELETE. Deleting detail to
fit a budget destroys the thing the budget exists to protect. Move the detail
to a sub-index or an archive file and leave a one-line pointer.

A missing file is reported as MISSING and is NOT a failure here. Whether a file
that should exist does exist is doc topology, which is tools/drift_guard.py
guard (d). This tool answers only "is what exists inside its budget".

THE POPULATION IS STATED, NOT GLOBBED (CS-475). WALKED_ROOTS names every root
this tool walks and WALK_BOUNDARY names the rule that stops the walk, both as
data carrying their own reasons, and both are printed. That is not tidiness:
this tool reports a COUNT that a reader trusts, and a population decided by a
glob is the failure class CONVENTIONS.md section 15.1 names and that
tools/drift_guard.py prints a skipped-paths list to defend against.

tools/drift_guard.py imports evaluate() from this module rather than shelling
out, so the budget table has exactly one implementation.

Usage:
    python tools/doc_budget.py
    python tools/doc_budget.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

KB = 1024

CLAUDE_BUDGET = 40 * KB
AUTOLOADED_BUDGET = 40 * KB
MEMORY_INDEX_BUDGET = 20 * KB
MEMORY_LEAF_BUDGET = 6 * KB
ROADMAP_BUDGET = 60 * KB

RELOCATE_GUIDANCE = (
    "RELOCATE, DO NOT DELETE - move detail to a sub-index (INDEX_<domain>.md) or "
    "an archive file under docs/_archive/ and leave a one-line pointer behind. "
    "Deleting the detail destroys what the budget exists to protect."
)

# Files pulled into context automatically at session start. CLAUDE.md and any
# nested CLAUDE.md are auto-loaded by the harness; CLAUDE.local.md is the
# untracked local companion and is measured when present because it costs the
# same context. memory/MEMORY.md is auto-loaded too but carries its own stricter
# 20 KB budget below, so it is not double-counted here.
AUTOLOADED_EXPLICIT = (
    "CLAUDE.md",
    "CLAUDE.local.md",
    ".claude/CLAUDE.md",
)


@dataclass(frozen=True)
class WalkedRoot:
    """One root this tool walks, and why it walks it.

    Attributes:
        relative: Path relative to the repository root; "." is the root.
        filename: The file name collected under it, matched without regard to
            case because a case-insensitive filesystem auto-loads a file
            whatever case it carries, and a population that changes with the
            host's filesystem is not a stated population.
        reason: Why this root is in the population.
    """

    relative: str
    filename: str
    reason: str


@dataclass(frozen=True)
class WalkBoundary:
    """The rule that stops a walk, and why it is that rule and not a name.

    Attributes:
        marker: The directory entry whose presence marks a checkout root.
        reason: Why a directory carrying it is outside this population.
    """

    marker: str
    reason: str


# THE POPULATION, STATED. There is one root and it is this repository's own
# working tree - "the files THIS checkout carries". Everything the tool
# measures beyond the explicit list above comes from here and nowhere else.
WALKED_ROOTS: tuple[WalkedRoot, ...] = (
    WalkedRoot(
        relative=".",
        filename="CLAUDE.md",
        reason=(
            "this repository's own working tree. A nested CLAUDE.md is auto-loaded "
            "by the harness when the session is working under it, so it costs the "
            "same context as the root one and carries the same budget."
        ),
    ),
)

# THE PRUNING RULE, STATED. CS-475: a linked worktree is a DIFFERENT checkout
# that happens to sit inside this one, and measuring its copy of a budgeted
# file reports another tree's number under this tree's name.
WALK_BOUNDARY = WalkBoundary(
    marker=".git",
    reason=(
        "a directory carrying a .git entry is itself a checkout root - a linked "
        "worktree, a submodule or a nested clone - and its files belong to that "
        "checkout, not to this one. Descending into one measures a DIFFERENT "
        "tree's copy of a budgeted file, which during a multi-agent session can "
        "report a stale copy inside budget while the tracked file is over. This "
        "is stated as a boundary rather than as a directory name deliberately: "
        "naming the harness's worktree directory would stop holding the day a "
        "harness put its worktrees somewhere else."
    ),
)

# Directories pruned for a different and weaker reason than the boundary above:
# they carry no authored documentation, only generated, vendored or cached
# bytes. The reason travels with each entry so nobody adds one without stating
# what it is. Membership is by NAME here, which is sound precisely because
# these are conventional tool directory names rather than a structural
# property - the structural property is WALK_BOUNDARY.
WALK_SKIP_DIRS: Mapping[str, str] = MappingProxyType(
    {
        ".git": "this checkout's own git metadata, not documentation",
        ".venv": "virtual environment - installed third-party bytes",
        "venv": "virtual environment - installed third-party bytes",
        "node_modules": "installed third-party packages",
        "__pycache__": "generated bytecode",
        ".mypy_cache": "generated tool cache",
        ".pytest_cache": "generated tool cache",
        ".ruff_cache": "generated tool cache",
        "data": "the gitignored generated-artifact directory (CLAUDE.md section 2.1)",
        "dist": "build output",
        "build": "build output",
    }
)

_HEADERS = ("SEVERITY", "RULE", "FILE", "ACTUAL", "BUDGET", "USED", "STATUS")


def repo_root() -> Path:
    """Return the repository root, derived from this file's location."""
    return Path(__file__).resolve().parents[1]


def _base_of(root: Path, walked: WalkedRoot) -> Path:
    """Resolve a declared walked root against the repository root."""
    return root if walked.relative == "." else root / walked.relative


def _is_checkout_root(path: Path) -> bool:
    """True when ``path`` is the root of a checkout of its own.

    A linked worktree carries .git as a FILE holding a gitdir pointer; a plain
    clone carries it as a directory. Both are checkout roots and neither one's
    files belong to this repository's population, so presence is the test and
    the kind is not.
    """
    return (path / WALK_BOUNDARY.marker).exists()


def _walk(root: Path, walked: WalkedRoot) -> tuple[list[Path], list[Path]]:
    """Collect ``walked.filename`` under one declared root.

    Args:
        root: The repository root.
        walked: The declared root to walk.

    Returns:
        The matching files, and the directories the walk refused to enter
        because they are checkout roots of their own. The second list is
        REPORTED rather than discarded, so a reader can see what was left out
        instead of taking the count on trust.
    """
    base = _base_of(root, walked)
    wanted = walked.filename.lower()
    matches: list[Path] = []
    stopped: list[Path] = []

    for current, dirnames, filenames in os.walk(base):
        here = Path(current)
        kept: list[str] = []
        for name in sorted(dirnames):
            if name in WALK_SKIP_DIRS:
                continue
            child = here / name
            if _is_checkout_root(child):
                stopped.append(child)
                continue
            kept.append(name)
        # The walk's own base is never tested against the boundary - this
        # checkout's root carries .git too, and pruning it would measure
        # nothing at all.
        dirnames[:] = kept
        matches.extend(here / name for name in filenames if name.lower() == wanted)

    return sorted(matches), sorted(stopped)


def _autoloaded_files(root: Path) -> list[Path]:
    """Every file that lands in context automatically, deduplicated."""
    found: list[Path] = []
    seen: set[str] = set()

    def remember(path: Path) -> None:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            found.append(path)

    for relative in AUTOLOADED_EXPLICIT:
        remember(root / relative)

    for walked in WALKED_ROOTS:
        matches, _ = _walk(root, walked)
        for path in matches:
            remember(path)
    return found


def checkout_boundaries(root: Path | None = None) -> list[dict]:
    """Every directory the walk stopped at because it is another checkout.

    Returns:
        One record per boundary, with the marker that identified it. Empty on
        a tree with no nested checkout, which is the ordinary case.
    """
    root = root or repo_root()
    out: list[dict] = []
    for walked in WALKED_ROOTS:
        _, stopped = _walk(root, walked)
        out.extend(
            {
                "path": _display(root, path),
                "walked_root": walked.relative,
                "marker": WALK_BOUNDARY.marker,
            }
            for path in stopped
        )
    return out


def _memory_leaves(root: Path) -> list[Path]:
    memory = root / "memory"
    if not memory.is_dir():
        return []
    return sorted(path for path in memory.glob("*.md") if path.name != "MEMORY.md")


def _size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def _display(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _entry(root: Path, path: Path, budget: int, severity: str, rule: str) -> dict:
    actual = _size(path)
    if actual is None:
        status = "MISSING"
    elif actual < budget:
        status = "OK"
    else:
        status = "OVER"
    return {
        "file": _display(root, path),
        "rule": rule,
        "severity": severity,
        "budget_bytes": budget,
        "actual_bytes": actual,
        "status": status,
        "guidance": RELOCATE_GUIDANCE if status == "OVER" else "",
    }


def evaluate(root: Path | None = None) -> list[dict]:
    """Measure every budgeted file.

    This is the single implementation of the CONVENTIONS section 2.1 table.
    tools/drift_guard.py calls it directly rather than re-deriving the budgets.
    """
    root = root or repo_root()
    claude_md = root / "CLAUDE.md"
    rows = [_entry(root, claude_md, CLAUDE_BUDGET, "HARD", "CLAUDE.md")]

    rows.extend(
        _entry(root, path, AUTOLOADED_BUDGET, "HARD", "auto-loaded file")
        for path in _autoloaded_files(root)
        if path != claude_md
    )
    rows.append(
        _entry(root, root / "memory" / "MEMORY.md", MEMORY_INDEX_BUDGET, "HARD", "memory index")
    )
    rows.extend(
        _entry(root, leaf, MEMORY_LEAF_BUDGET, "WARN", "memory leaf")
        for leaf in _memory_leaves(root)
    )
    rows.append(_entry(root, root / "ROADMAP.md", ROADMAP_BUDGET, "WARN", "ROADMAP.md"))
    return rows


def hard_failures(rows: list[dict]) -> list[dict]:
    """Return the rows that breach a hard budget."""
    return [row for row in rows if row["status"] == "OVER" and row["severity"] == "HARD"]


def soft_failures(rows: list[dict]) -> list[dict]:
    """Return the rows that breach a warn-level budget."""
    return [row for row in rows if row["status"] == "OVER" and row["severity"] == "WARN"]


def _fmt_kb(value: int) -> str:
    return f"{value / KB:.1f} KB"


def _table(rows: list[dict]) -> list[str]:
    body: list[list[str]] = []
    for row in rows:
        actual = "-" if row["actual_bytes"] is None else _fmt_kb(row["actual_bytes"])
        used = (
            "-"
            if row["actual_bytes"] is None
            else f"{round(100.0 * row['actual_bytes'] / row['budget_bytes'])}%"
        )
        body.append(
            [
                row["severity"],
                row["rule"],
                row["file"],
                actual,
                _fmt_kb(row["budget_bytes"]),
                used,
                row["status"],
            ]
        )

    widths = [len(header) for header in _HEADERS]
    for line in body:
        for index, cell in enumerate(line):
            widths[index] = max(widths[index], len(cell))

    out = ["  ".join(_HEADERS[i].ljust(widths[i]) for i in range(len(_HEADERS))).rstrip()]
    out.append("  ".join("-" * widths[i] for i in range(len(_HEADERS))))
    out.extend(
        "  ".join(line[i].ljust(widths[i]) for i in range(len(_HEADERS))).rstrip() for line in body
    )
    return out


def _population_statement(boundaries: list[dict] | None) -> list[str]:
    """State which roots were walked and what stopped the walk.

    A count is only as trustworthy as the population behind it, so the
    population is printed next to the count rather than left to be inferred
    from the table.
    """
    out = ["", "Population walked (CS-475 - stated, not globbed):"]
    out.extend(
        f"  root {walked.relative}  collecting {walked.filename} - {walked.reason}"
        for walked in WALKED_ROOTS
    )
    out.append(f"  stops at any directory carrying {WALK_BOUNDARY.marker} - {WALK_BOUNDARY.reason}")
    if boundaries is None:
        return out
    if boundaries:
        out.append("  not descended into (a checkout of its own, measured by its own tree):")
        out.extend(f"    {record['path']}" for record in boundaries)
    else:
        out.append("  not descended into: (no nested checkout found)")
    return out


def render(rows: list[dict], boundaries: list[dict] | None = None) -> list[str]:
    """Render the budget table and the verdict as printable lines.

    Args:
        rows: The rows from :func:`evaluate`.
        boundaries: Optional records from :func:`checkout_boundaries`. When
            omitted the declared population is still stated; only the observed
            boundary list is left out, because it needs its own walk.
    """
    out = ["Documentation size budgets (CONVENTIONS.md section 2.1; 1 KB = 1024 bytes)", ""]
    out.extend(_table(rows))
    out.extend(_population_statement(boundaries))

    over = [row for row in rows if row["status"] == "OVER"]
    if over:
        out.extend(["", "BUDGET HIT - the required action is:", "  " + RELOCATE_GUIDANCE])
        out.extend(
            f"  {row['severity']} {row['file']}: {_fmt_kb(row['actual_bytes'])} "
            f"against a {_fmt_kb(row['budget_bytes'])} budget"
            for row in over
        )

    missing = [row for row in rows if row["status"] == "MISSING"]
    if missing:
        out.extend(
            [
                "",
                "Not measured (file absent - not a budget failure; doc topology is "
                "tools/drift_guard.py guard d):",
            ]
        )
        out.extend(f"  {row['file']}" for row in missing)

    hard = hard_failures(rows)
    warn = soft_failures(rows)
    measured = sum(1 for row in rows if row["status"] != "MISSING")
    out.append("")
    out.append(
        f"measured: {measured}    over budget: {len(over)} "
        f"(HARD {len(hard)}, WARN {len(warn)})    absent: {len(missing)}"
    )
    if hard:
        out.append(f"VERDICT: FAIL - {len(hard)} hard budget failure(s)")
    elif warn:
        out.append(f"VERDICT: WARN - {len(warn)} soft budget failure(s), relocate pass due")
    else:
        out.append("VERDICT: PASS - every measured file is inside its budget")
    return out


def main(argv: list[str] | None = None) -> int:
    """Run the budget check and print the result. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        description="Enforce the CONVENTIONS.md section 2.1 documentation size "
        "budgets. Exits non-zero only on a HARD failure."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    root = repo_root()
    rows = evaluate(root)
    boundaries = checkout_boundaries(root)
    hard = hard_failures(rows)
    warn = soft_failures(rows)

    if args.json:
        verdict = "FAIL" if hard else ("WARN" if warn else "PASS")
        print(
            json.dumps(
                {
                    "schema": 1,
                    "kb": KB,
                    "guidance": RELOCATE_GUIDANCE,
                    "population": {
                        "walked_roots": [
                            {
                                "relative": walked.relative,
                                "filename": walked.filename,
                                "reason": walked.reason,
                            }
                            for walked in WALKED_ROOTS
                        ],
                        "boundary_marker": WALK_BOUNDARY.marker,
                        "boundary_reason": WALK_BOUNDARY.reason,
                        "skipped_directory_names": dict(WALK_SKIP_DIRS),
                        "not_descended_into": boundaries,
                    },
                    "rows": rows,
                    "hard_failures": [row["file"] for row in hard],
                    "warnings": [row["file"] for row in warn],
                    "verdict": verdict,
                },
                indent=2,
            )
        )
    else:
        print("\n".join(render(rows, boundaries)))

    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
