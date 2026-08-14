#!/usr/bin/env python3
"""Clockspeed memory sync.

Validates the markdown memory, and reports honestly that no semantic recall
mirror is wired into this project yet.

MARKDOWN IS THE SINGLE SOURCE OF TRUTH. The semantic store is a MIRROR, never
the source. A fact is never fixed only in the mirror, and the mirror is never
consulted to decide what the markdown should say. If the two disagree, the
markdown wins and the mirror is re-synced (CONVENTIONS.md section 11).

WHAT THIS TOOL ACTUALLY DOES TODAY
It validates the markdown half: frontmatter shape on every memory/*.md leaf,
and reachability of every leaf from memory/MEMORY.md. That half is real.

WHAT IT DOES NOT DO, AND SAYS SO OUT LOUD
No semantic store is wired into this project. There is nothing to mirror INTO,
so this tool reports NO RECALL MIRROR CONFIGURED rather than printing a
reassuring "sync complete".

CONVENTIONS.md section 11.2 is explicit that a "healthy" status is NOT proof
recall works - a store can report healthy while most rows carry no embedding,
silently degrading recall to keyword matching, which is exactly the failure the
store exists to prevent. Only `embedded == active` proves coverage. Claiming a
mirror is healthy when none exists would be that failure in its purest form.

EXIT CODES, AND WHY THEY DIFFER
  plain run   exit 0    The fresh-clone bootstrap order in CONVENTIONS.md
                        section 1 runs this third, after install_hooks.py and
                        verify_env.py. A missing optional mirror must not break
                        the bootstrap of a clone that has not wired one yet.
  --verify    exit 1    --verify asserts that recall COVERAGE IS PROVEN. It is
                        not, and cannot be, while no store exists. CI tier 1
                        runs --verify, so the day a mirror lands and genuinely
                        reports embedded == active is the day this turns green,
                        and not one day earlier.

Usage:
    python tools/memory_sync.py
    python tools/memory_sync.py --verify
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

VALID_TYPES = ("user", "feedback", "project", "reference")

# What a real implementation must assert before it may report success. Printed
# every run so the contract stays visible to whoever eventually writes it.
FUTURE_ASSERTIONS = (
    "embedded == active for every row - a 'healthy' status is not proof of "
    "coverage, and a store with unembedded rows degrades recall to keyword match",
    "row count in the store == leaf count on disk, with the difference named "
    "leaf by leaf whenever it is not zero",
    "every row's content hash matches the current markdown, so a stale mirror is "
    "a failure rather than a silent pass",
    "the sync is idempotent - upsert by (category, key), never duplicate, so "
    "running it twice changes nothing the second time",
    "a deleted leaf removes its row, or the store answers recall with a fact the "
    "repo has already retracted",
    "the store, its config and its wiring stay LOCAL and gitignored; only this tool is tracked",
    "recall goes through a thin projection returning key plus one-line "
    "description, never the raw call that returns every hit's full body",
)

MIRROR_PROBES = (
    ".mcp.json naming a recall or memory server",
    "config/recall.json",
    "the CLOCKSPEED_RECALL_STORE environment variable",
    "data/recall/ (a local store directory)",
)


def repo_root() -> Path:
    """Return the repository root, derived from this file's location."""
    return Path(__file__).resolve().parents[1]


# --- frontmatter ------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse the narrow frontmatter shape CONVENTIONS.md section 11.1 specifies.

    Deliberately not a YAML parser: the shape is fixed (name, description, and a
    metadata block carrying type), and taking a YAML dependency for four keys
    would put a dependency in front of the fresh-clone bootstrap.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "no frontmatter block (the file must open with ---)"
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return {}, "frontmatter block is never closed"

    data: dict = {}
    section = None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indented = line[:1] in (" ", "\t")
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if indented and section:
            data.setdefault(section, {})[key] = value
        elif value == "":
            section = key
            data.setdefault(key, {})
        else:
            section = None
            data[key] = value
    return data, ""


def validate_leaf(path: Path) -> list[str]:
    """Return every frontmatter problem found in one memory leaf."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"unreadable: {exc}"]

    data, error = parse_frontmatter(text)
    if error:
        return [error]

    problems: list[str] = []
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        problems.append("frontmatter has no 'name'")
    elif name.strip() != path.stem:
        problems.append(f"name {name.strip()!r} does not match the filename stem {path.stem!r}")

    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        problems.append("frontmatter has no 'description' (recall relevance is judged on it)")

    metadata = data.get("metadata")
    kind = metadata.get("type") if isinstance(metadata, dict) else None
    if not kind:
        problems.append("metadata.type is missing")
    elif kind not in VALID_TYPES:
        allowed = "|".join(VALID_TYPES)
        problems.append(f"metadata.type {kind!r} is not one of {allowed}")

    if not text.split("---", 2)[-1].strip():
        problems.append("no body after the frontmatter")
    return problems


# --- reachability -----------------------------------------------------------

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


def reachability(memory_dir: Path, leaves: list[Path]) -> tuple[list[Path], str]:
    """Return (unreachable leaves, note). Transitive through INDEX_<domain>.md."""
    index = memory_dir / "MEMORY.md"
    if not index.is_file():
        return list(leaves), "memory/MEMORY.md is ABSENT - nothing to be reachable from"

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
        except OSError:
            continue
        for token in _link_targets(text):
            reachable.add(token)
            if token.startswith("index_"):
                candidate = memory_dir / f"{token}.md"
                if candidate.is_file():
                    frontier.append(candidate)
    return [leaf for leaf in leaves if leaf.stem.lower() not in reachable], ""


# --- mirror detection -------------------------------------------------------


def detect_mirror(root: Path) -> tuple[bool, list[str]]:
    """Probe for a wired recall store rather than asserting its absence.

    Returns (configured, evidence). The absence claim this tool prints is the
    result of this probe, not a hardcoded sentence that could go stale.
    """
    evidence: list[str] = []
    mcp = root / ".mcp.json"
    if mcp.is_file():
        try:
            text = mcp.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            text = ""
        if "recall" in text or "memory" in text:
            evidence.append(".mcp.json names a recall or memory server")
    if (root / "config" / "recall.json").is_file():
        evidence.append("config/recall.json exists")
    if os.environ.get("CLOCKSPEED_RECALL_STORE"):
        evidence.append("CLOCKSPEED_RECALL_STORE is set")
    if (root / "data" / "recall").is_dir():
        evidence.append("data/recall/ exists")
    return bool(evidence), evidence


# --- rendering --------------------------------------------------------------


def _markdown_lines(
    memory_dir: Path,
    leaves: list[Path],
    problems: dict[str, list[str]],
    unreachable: list[Path],
    note: str,
) -> list[str]:
    index_state = "present" if (memory_dir / "MEMORY.md").is_file() else "ABSENT"
    out = [
        "MARKDOWN (the source of truth)",
        f"  leaves found:             {len(leaves)}",
        f"  frontmatter valid:        {len(leaves) - len(problems)}",
        f"  frontmatter invalid:      {len(problems)}",
        f"  index memory/MEMORY.md:   {index_state}",
        f"  unreachable leaves:       {len(unreachable)}",
    ]
    if note:
        out.append(f"  note: {note}")

    if problems:
        out.extend(["", "  FRONTMATTER PROBLEMS"])
        for name in sorted(problems):
            out.append(f"    {name}")
            out.extend(f"      - {problem}" for problem in problems[name])

    if unreachable:
        out.extend(["", "  UNREACHABLE FROM THE INDEX"])
        out.extend(f"    {leaf.name}" for leaf in unreachable)
        out.append(
            "    Add a one-line hook to memory/MEMORY.md. Do NOT unindex a file to "
            "save bytes (CONVENTIONS.md section 11) - relocate detail instead."
        )
    return out


def _mirror_lines(configured: bool, evidence: list[str]) -> list[str]:
    out = ["RECALL MIRROR"]
    if configured:
        out.append("  STATUS: something resembling a store is present, but this tool has no")
        out.append("  implementation that can prove coverage. Treat it as UNVERIFIED.")
        out.extend(f"    evidence: {item}" for item in evidence)
    else:
        out.append("  STATUS: NO RECALL MIRROR IS CONFIGURED IN THIS PROJECT.")
        out.append("  Nothing was mirrored, because there is nothing to mirror into.")
        out.append("  That is a truthful report, not a failure of this run.")
    out.append("  probed for:")
    out.extend(f"    - {item}" for item in MIRROR_PROBES)
    out.extend(
        [
            "",
            "  A 'healthy' status is NOT proof recall works. A store can report healthy",
            "  while most rows carry no embedding, degrading recall to keyword matching -",
            "  the exact failure the store exists to prevent. Only embedded == active",
            "  proves coverage (CONVENTIONS.md section 11.2).",
            "",
            "  WHAT A FUTURE IMPLEMENTATION MUST ASSERT BEFORE REPORTING SUCCESS:",
        ]
    )
    out.extend(
        f"    {index}. {assertion}" for index, assertion in enumerate(FUTURE_ASSERTIONS, start=1)
    )
    return out


def _verdict_lines(verify: bool, dirty: bool) -> list[str]:
    if verify:
        return [
            "--verify: FAIL. Recall coverage cannot be proven - no store is wired, so",
            "embedded == active is unassertable. Exiting non-zero deliberately. This",
            "turns green when a mirror exists AND genuinely reports full embedding",
            "coverage, and not before.",
        ]
    out = [
        "plain run: exit 0. The markdown was validated and the mirror state was reported",
        "honestly. The fresh-clone bootstrap order is not broken by an optional component",
        "nobody has wired yet.",
    ]
    if dirty:
        out.extend(
            [
                "Markdown problems above are REAL and must be fixed. They do not change this",
                "exit code, because tools/drift_guard.py is the gate that fails on them. Run it.",
            ]
        )
    return out


def main(argv: list[str] | None = None) -> int:
    """Validate the memory markdown, report the mirror state, return the exit code."""
    parser = argparse.ArgumentParser(
        description="Validate the markdown memory and report the state of the recall "
        "mirror. A plain run exits 0 so a fresh-clone bootstrap does not break; --verify "
        "exits non-zero until recall coverage can actually be proven."
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="assert that recall coverage is PROVEN (embedded == active). Fails while no "
        "store is wired. CI tier 1 runs this.",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    memory_dir = root / "memory"
    out = ["Clockspeed memory sync", ""]

    leaves: list[Path] = []
    if memory_dir.is_dir():
        leaves = sorted(path for path in memory_dir.glob("*.md") if path.name != "MEMORY.md")
    else:
        out.append("memory/ does not exist - there is nothing to validate")

    problems = {leaf.name: found for leaf in leaves if (found := validate_leaf(leaf))}
    unreachable, note = reachability(memory_dir, leaves) if memory_dir.is_dir() else ([], "")

    out.extend(_markdown_lines(memory_dir, leaves, problems, unreachable, note))
    out.append("")
    configured, evidence = detect_mirror(root)
    out.extend(_mirror_lines(configured, evidence))
    out.append("")
    out.extend(_verdict_lines(args.verify, bool(problems or unreachable)))

    print("\n".join(out))
    return 1 if args.verify else 0


if __name__ == "__main__":
    sys.exit(main())
