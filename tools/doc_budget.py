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

tools/drift_guard.py imports evaluate() from this module rather than shelling
out, so the budget table has exactly one implementation.

Usage:
    python tools/doc_budget.py
    python tools/doc_budget.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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

WALK_SKIP_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "data",
        "dist",
        "build",
    }
)

_HEADERS = ("SEVERITY", "RULE", "FILE", "ACTUAL", "BUDGET", "USED", "STATUS")


def repo_root() -> Path:
    """Return the repository root, derived from this file's location."""
    return Path(__file__).resolve().parents[1]


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

    for path in sorted(root.rglob("CLAUDE.md")):
        if any(part in WALK_SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        remember(path)
    return found


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


def render(rows: list[dict]) -> list[str]:
    """Render the budget table and the verdict as printable lines."""
    out = ["Documentation size budgets (CONVENTIONS.md section 2.1; 1 KB = 1024 bytes)", ""]
    out.extend(_table(rows))

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

    rows = evaluate(repo_root())
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
                    "rows": rows,
                    "hard_failures": [row["file"] for row in hard],
                    "warnings": [row["file"] for row in warn],
                    "verdict": verdict,
                },
                indent=2,
            )
        )
    else:
        print("\n".join(render(rows)))

    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
