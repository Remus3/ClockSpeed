#!/usr/bin/env python3
"""Clockspeed documentation size budgets.

Enforces exactly the table in CONVENTIONS.md section 2.1. Context is the binding
budget in every session, so a doc that grows past its budget spends the
operator's scarcest resource on every turn of every session.

    CLAUDE.md                  <  40 KB  hard fail
    any single auto-loaded     <  40 KB  hard fail
    memory/MEMORY.md (index)   <  20 KB  hard fail
    any memory/*.md leaf       <   6 KB  warn
    ROADMAP.md                 <  60 KB  warn, triggers a relocate pass
    docs/item_notes.md (index) <  16 KB  warn
    any docs/item_notes/*.md   < 128 KB  warn, triggers a relocate pass
    docs/upstream_watch.md     <  16 KB  warn

Exits non-zero only on a HARD failure. A WARN prints loudly and returns zero,
because a warn that blocks a commit gets disabled and then enforces nothing.

THE GUIDANCE IS NOT "TRIM". It is RELOCATE, DO NOT DELETE. Deleting detail to
fit a budget destroys the thing the budget exists to protect. Move the detail
to a sub-index or an archive file and leave a one-line pointer.

A missing file is reported as MISSING and is NOT a failure here. Whether a file
that should exist does exist is doc topology, which is tools/drift_guard.py
guard (d). This tool answers only "is what exists inside its budget".

A directory that refuses a listing is reported as UNLISTED (CS-1115): its
budgeted files were never seen, so the verdict reads INCOMPLETE, never PASS.
The exit code still moves on a HARD failure only; tools/drift_guard.py guard (a)
is what makes such a run UNGRADED.

THE POPULATION IS STATED, NOT GLOBBED (CS-475). WALKED_ROOTS names every root
this tool walks and WALK_BOUNDARY names the rule that stops the walk, both as
data carrying their own reasons, and both are printed. That is not tidiness:
this tool reports a COUNT that a reader trusts, and a population decided by a
glob is the failure class CONVENTIONS.md section 15.1 names and that
tools/drift_guard.py prints a skipped-paths list to defend against.

MEMBERSHIP TAKES THREE TESTS, NOT ONE, and none of them is belt-and-braces.
The boundary marker alone is FALSE for the whole duration of every worktree
teardown, because `git worktree remove` deletes the .git marker before it
deletes the files - measured 8 times out of 8. A registered-worktree test
covers that window; a tracked-or-not-ignored test decides what this tree owns
without dropping a genuinely new untracked file from the hard gate. Each was
added because a measurement showed the previous set was wrong, what any of
them excludes is REPORTED rather than dropped, and the reasoning for all three
is written out beside MEMBERSHIP_REASON.

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
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

# CS-910. This module is run as a bare script by a hook and is also loaded BY
# PATH by the suite, so this directory cannot be assumed to be on sys.path. The
# insert is the one tools/drift_guard.py already makes before importing THIS
# module, and the bare module name is the same shape for the same reason: `tools`
# carries no __init__.py, so spelling it `tools.toolpath` gives mypy the one file
# under two module names and it refuses the run.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

KB = 1024

CLAUDE_BUDGET = 40 * KB
AUTOLOADED_BUDGET = 40 * KB
MEMORY_INDEX_BUDGET = 20 * KB
MEMORY_LEAF_BUDGET = 6 * KB
ROADMAP_BUDGET = 60 * KB

# docs/item_notes.md owned the LIVE per-item detail for OPEN work as ONE file
# from 2026-08-23 until 2026-08-25, when it was SPLIT: it is now an index over
# docs/item_notes/, one leaf per phase, and the leaves hold the bodies
# (CLAUDE.md section 4). The split was taken at 96 per cent of the old 224 KB
# budget with ZERO closed sections left to relocate - the file's only designed
# shrink is an item CLOSING, and four items had merged that session without
# closing.
#
# THE INDEX IS BUDGETED TIGHT, and deliberately so. It carries one routing row
# per OPEN item plus the family's rules, and it MEASURED 9.1 KB on creation. A
# row is roughly 45 bytes, so 16 KB holds well over a hundred more items than
# the tree has - while being nowhere near enough to hold a body. The failure
# worth catching on THIS file is someone writing an item's detail here instead
# of in its leaf, which is also asserted directly by tools/drift_guard.py
# guard (j); a size warn is a weak second signal for it and a free one.
ITEM_NOTES_INDEX_BUDGET = 16 * KB

# EACH LEAF carries a budget rather than the family carrying one. A budget
# summed over a population is met by its strongest member while the weakest
# goes unmeasured, so the total is not the thing to bound - the individual file
# a session has to read is.
#
# THE TWO LARGEST LEAVES MEASURED 92.3 KB and 92.0 KB the moment they landed.
# 128 KB is roughly 37 per cent above that, which is the SAME reasoning and the
# same margin the 224 KB single-file budget was chosen with - kept identical on
# purpose, so the number is inherited rather than re-argued.
#
# THE HEADROOM IS THE POINT and its limit is disclosed. The split divides the
# population; it does not shrink it. Newly filed items land overwhelmingly in
# the CS-8nn follow-up leaf, so that leaf is the one that grows, and 128 KB
# leaves it roughly a dozen more items' worth of detail. CLOSURE IS STILL THE
# ONLY DESIGNED SHRINK. When a leaf fills, the remedy is the one this file
# already prescribes - relocate, do not delete - and the family's shape makes
# room for a further leaf without another topology change.
ITEM_NOTES_LEAF_BUDGET = 128 * KB

# docs/upstream_watch.md owns the upstream wiki watch list and the ordering it
# is read in (CLAUDE.md section 4). It MEASURED 5.4 KB on creation 2026-08-23.
# 16 KB is chosen deliberately TIGHT relative to the others - roughly three
# times the observed size, which is ample for the one thing legitimately
# missing from it (a per-page change signal for each group, unrecorded since
# the CS-485 research pass) and nowhere near enough to hold a page dump.
#
# A tight budget is a FEATURE on this specific file rather than an oversight.
# The file's stated "never contains" is lifted upstream content, and the CS-485
# licence gate REFUSED vendoring, so the failure mode worth catching early is
# this file growing because someone pasted a wiki table into it. A size warn is
# a weak signal for that and it is not the primary control - but it is a free
# one, and it points at the right file.
UPSTREAM_WATCH_BUDGET = 16 * KB

#: CS-1115 - the status of a row naming a DIRECTORY whose listing was refused.
#: Its budgeted files were never seen, so it is neither absent nor inside
#: budget, and the verdict reads INCOMPLETE rather than PASS over it.
UNLISTED = "UNLISTED"

#: CS-1117 - the status of a row whose budgeted name is carried by something
#: that is not a regular file, a directory in practice. A directory answers a
#: stat, so it used to print as an OK 0.0 KB row counted as measured. It is a
#: finding of its own: nothing was measured, and nothing is merely absent.
NOT_A_FILE = "NOT A FILE"

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

# MEMBERSHIP TAKES THREE COMPLEMENTARY TESTS, AND EACH ONE COVERS A HOLE THE
# OTHERS LEAVE OPEN. Every one of them was added because a measurement showed
# the previous set was wrong, not because more rules felt safer.
#
# (1) WALK_BOUNDARY, above. Structural, needs no git, prunes during the walk.
#     It is NECESSARY AND NOT SUFFICIENT: `git worktree remove` deletes the
#     .git marker BEFORE it deletes the worktree's files. Probed over 8
#     teardown rounds, 8 of 8 showed a window where the directory still held a
#     populated CLAUDE.md and carried no marker. The end-of-session ritual runs
#     this tool at exactly the moment agent worktrees are torn down, so that
#     window is the common case rather than an exotic one.
#
# (2) REGISTERED WORKTREES. In the same measured window, with the marker gone
#     and the files still on disk, git still LISTS the directory as a linked
#     worktree - confirmed True at both an ignored and an un-ignored path. So
#     the registration outlives the marker and closes exactly the window the
#     marker leaves open, at any path, without depending on where a harness
#     chose to put its worktrees.
#
# (3) TRACKED-OR-NOT-IGNORED. A file is this tree's if the index carries it, or
#     if it is untracked but not ignored. The earlier revision of this tool
#     used TRACKED ALONE and that was a real loss of enforcement: an untracked
#     but genuinely-this-tree nested CLAUDE.md over its budget stopped failing
#     the hard gate. Measured: docs/newarea/CLAUDE.md at 72900 bytes reported
#     PASS where it should hard-fail. Not-ignored brings that file back into
#     the population while still excluding a worktree copy under an ignored
#     path.
#
# WHY (2) IS NOT REDUNDANT WITH (3), which is the trap this nearly fell into:
# test (3) alone reopens the teardown window for a worktree at an UN-IGNORED
# path, because in that window the copy is untracked and not ignored and so
# looks exactly like a new file this tree owns. Measured directly, not assumed:
# in the marker-absent state the copy PASSED the tracked-or-not-ignored test at
# an un-ignored path and failed it at an ignored path. Test (2) is what makes
# the answer independent of the harness's directory layout.
#
# What any test excludes is REPORTED rather than silently dropped - CLAUDE.md
# non-negotiable 7 - and AUTOLOADED_EXPLICIT is exempt from (3), because
# CLAUDE.local.md is untracked BY DESIGN and still costs context.
MEMBERSHIP_REASON = (
    "measured only if this checkout's index carries it, or it is untracked and "
    "not ignored. A worktree copy under an ignored path fails that, and a "
    "genuinely new nested CLAUDE.md this tree owns passes it, so the hard gate "
    "still fires on an untracked file that is over budget. A walked file that "
    "fails is reported rather than measured, never silently dropped."
)

# THE COST OF THE RULE, AND WHY IT IS SHAPED THIS WAY. NO FIGURES HERE, on
# purpose. CLAUDE.md section 4 forbids restating a measured number in prose -
# a hardcoded figure is a lie with a timestamp on it - and a benchmark in a
# comment goes stale by MACHINE as well as by time. This tool's own item exists
# because a population was decided by a glob rather than stated; shipping a
# stale benchmark in its own comment would be that same defect one file along.
# An earlier revision of this comment carried three figures and one of them was
# not merely stale but backwards, claiming the tool had got faster end to end
# when it had measurably got slower.
#
# What is durable, and what a reader can re-derive on their own machine:
#
#   - The walk itself got FASTER. Pruning during the walk beats letting rglob
#     descend into .git and filtering afterwards.
#   - Essentially all of the added cost is the git subprocesses rather than the
#     Python. Handed a survey that has already been taken, evaluate() is
#     cheaper than the pre-CS-475 version was.
#   - There are TWO subprocesses per invocation - one listing for membership,
#     one for the worktree registration - and they are spawned once per
#     INVOCATION, not once per consumer. main() takes a single survey and hands
#     it to evaluate() and to the renderer, and evaluate() accepts a
#     pre-computed survey for the same reason. An earlier revision spawned
#     three, because each consumer queried independently.
#   - End to end this tool is SLOWER than before, by more than run-to-run
#     noise. That is accepted rather than optimised away: it is two process
#     spawns on a tool a session runs a handful of times, weighed against a
#     guard that was reporting another checkout's numbers as this one's.
#
# The subprocess count is pinned by a TEST rather than by this comment -
# tests/test_doc_budget.py::test_one_invocation_asks_git_once_per_question -
# because a count in prose is exactly what this paragraph must not become.
#
# Reading .git/worktrees/*/gitdir directly would save one subprocess and was
# rejected as FUNCTIONALLY WRONG, not merely impolite. A linked worktree's .git
# is a FILE holding a gitdir pointer, not a directory, so root/.git/worktrees
# does not exist when this tool runs from inside an agent worktree - which is
# exactly how this project runs it. `git worktree list --porcelain` answers
# correctly from any checkout, main or linked.
REGISTERED_WORKTREE_REASON = (
    "a directory git lists as a linked worktree is not descended into, even "
    "when its .git marker is already gone. `git worktree remove` deletes that "
    "marker before it deletes the files, and the registration outlives it, so "
    "this is the test that holds during a teardown at a path no ignore rule "
    "covers."
)

# The stated degradation. Non-negotiable 7 again: when git cannot answer, the
# tool says so in its output and falls back to the boundary marker alone rather
# than failing or pretending the weaker population is the stated one.
INDEX_UNAVAILABLE_REASON = (
    "git could not answer, so membership fell back to the boundary marker "
    "alone. That fallback does NOT close the teardown window described beside "
    "WALK_BOUNDARY, and it does not exclude ignored files."
)

GIT_TIMEOUT_SECONDS = 30

#: The tool this module asks about tracked membership. A NAME, resolved at
#: runtime by tools/toolpath.py and never spelled as a path - non-negotiable 3.
#: Named as a constant rather than written at the call so the census in
#: tests/toolpath_guard.py grades one site rather than a literal it has to
#: recognise by eye.
GIT_NAME = "git"

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


def _is_registered_worktree(path: Path, facts: GitFacts) -> bool:
    """True when git lists ``path`` as a linked worktree of this repository.

    This is the test that survives a teardown. The marker is already gone in
    that window; the registration is not.
    """
    if not facts.worktrees:
        return False
    try:
        resolved = str(path.resolve()).lower()
    except OSError:
        resolved = str(path).lower()
    return resolved in facts.worktrees


def _walk(
    root: Path, walked: WalkedRoot, facts: GitFacts
) -> tuple[list[Path], list[Path], list[Path]]:
    """Collect ``walked.filename`` under one declared root.

    Args:
        root: The repository root.
        walked: The declared root to walk.
        facts: Git's answers, so a registered worktree is pruned even once its
            .git marker has been removed by an in-progress teardown.

    Returns:
        The matching files, the directories the walk refused to enter because
        they are checkout roots of their own, and the directories it could not
        list. The second and third lists are REPORTED rather than discarded, so
        a reader can see what was left out instead of taking the count on trust.
    """
    base = _base_of(root, walked)
    wanted = walked.filename.lower()
    matches: list[Path] = []
    stopped: list[Path] = []
    refused: list[Path] = []

    def record(exc: OSError) -> None:
        # CS-1115. os.walk DISCARDS a refused listing unless told otherwise, so
        # a budgeted file behind one vanished from the population silently.
        refused.append(Path(exc.filename) if exc.filename else base)

    for current, dirnames, filenames in os.walk(base, onerror=record):
        here = Path(current)
        kept: list[str] = []
        for name in sorted(dirnames):
            if name in WALK_SKIP_DIRS:
                continue
            child = here / name
            if _is_checkout_root(child) or _is_registered_worktree(child, facts):
                stopped.append(child)
                continue
            kept.append(name)
        # The walk's own base is never tested against the boundary - this
        # checkout's root carries .git too, and pruning it would measure
        # nothing at all.
        dirnames[:] = kept
        matches.extend(here / name for name in filenames if name.lower() == wanted)

    return sorted(matches), sorted(stopped), sorted(refused)


@dataclass(frozen=True)
class GitFacts:
    """Everything git is asked, asked ONCE per survey.

    Two subprocesses, not one per question. The earlier revision spawned three
    git processes per invocation because evaluate(), survey() and
    checkout_boundaries() each walked and queried independently.

    Attributes:
        members: Paths this tree owns - tracked, or untracked and not ignored -
            lowercased and posix-style.
        worktrees: Resolved paths git lists as linked worktrees, excluding the
            root itself.
        available: False when git could not answer at all.
    """

    members: frozenset[str]
    worktrees: tuple[str, ...]
    available: bool


def _git(root: Path, *args: str) -> str | None:
    """Run one git command in ``root``. None when git cannot answer.

    CS-910 - THE TOOL IS RESOLVED, NEVER NAMED. A bare ``"git"`` in an argv is
    resolved by ``CreateProcess``, which searches the CURRENT DIRECTORY before
    PATH whenever the gate variable is absent from the environment - its state at
    both machine and user scope on the development machine. This module walks
    trees it did not create and is run by a hook from wherever the operator
    happens to be, so "the current directory" is not a directory it controls.
    An unresolvable git answers None, which is the same answer this function
    already gives for a git that fails.
    """
    git = resolve_tool(GIT_NAME)
    if git is None:
        return None
    try:
        done = subprocess.run(
            [git, "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return done.stdout


def git_facts(root: Path) -> GitFacts:
    """Ask git the two questions membership needs, once each.

    `ls-files --cached --others --exclude-standard` answers "tracked OR
    untracked-and-not-ignored" in a single call rather than two.
    """
    listing = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if listing is None:
        return GitFacts(members=frozenset(), worktrees=(), available=False)

    members = frozenset(entry.lower() for entry in listing.split("\0") if entry)

    registered: list[str] = []
    porcelain = _git(root, "worktree", "list", "--porcelain")
    if porcelain:
        try:
            here = str(root.resolve()).lower()
        except OSError:
            here = str(root).lower()
        for line in porcelain.splitlines():
            if not line.startswith("worktree "):
                continue
            raw = line.split(" ", 1)[1].strip()
            try:
                resolved = str(Path(raw).resolve()).lower()
            except OSError:
                resolved = raw.lower()
            if resolved != here:
                registered.append(resolved)

    return GitFacts(members=members, worktrees=tuple(sorted(registered)), available=True)


@dataclass(frozen=True)
class Survey:
    """One pass over the declared population, with everything it observed.

    Attributes:
        files: The walked files that passed every membership test.
        boundaries: Directories not descended into, being checkouts of their own.
        excluded: Walked files this tree does not own - reported, never
            silently dropped.
        index_available: False when git could not answer, in which case
            membership fell back to the boundary marker alone.
        unlisted: Directories under a walked root whose listing was refused,
            so whatever budgeted file they hold was never seen (CS-1115).
    """

    files: tuple[Path, ...]
    boundaries: tuple[str, ...]
    excluded: tuple[str, ...]
    index_available: bool
    unlisted: tuple[str, ...] = ()


def survey(root: Path | None = None, facts: GitFacts | None = None) -> Survey:
    """Walk the declared roots and apply every membership test.

    This is the single place the population is decided. Everything that reports
    a count, a row or a skipped path derives from here, so there is no second
    opinion about what this repository carries.

    Args:
        root: The repository root.
        facts: Pre-computed git answers, so one invocation asks git once
            instead of once per consumer.
    """
    root = root or repo_root()
    facts = facts if facts is not None else git_facts(root)

    files: list[Path] = []
    boundaries: list[str] = []
    excluded: list[str] = []
    unlisted: list[str] = []

    for walked in WALKED_ROOTS:
        matches, stopped, refused = _walk(root, walked, facts)
        boundaries.extend(_display(root, path) for path in stopped)
        unlisted.extend(_display(root, path) for path in refused)
        for path in matches:
            shown = _display(root, path)
            if facts.available and shown.lower() not in facts.members:
                excluded.append(shown)
                continue
            files.append(path)

    return Survey(
        files=tuple(files),
        boundaries=tuple(sorted(boundaries)),
        excluded=tuple(sorted(excluded)),
        index_available=facts.available,
        unlisted=tuple(sorted(unlisted)),
    )


def _autoloaded_files(root: Path, observed: Survey | None = None) -> list[Path]:
    """Every file that lands in context automatically, deduplicated."""
    found: list[Path] = []
    seen: set[str] = set()

    def remember(path: Path) -> None:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            found.append(path)

    # The explicit list is exempt from the membership test on purpose:
    # CLAUDE.local.md is the untracked local companion and costs context anyway.
    for relative in AUTOLOADED_EXPLICIT:
        remember(root / relative)

    for path in (observed if observed is not None else survey(root)).files:
        remember(path)
    return found


def checkout_boundaries(root: Path | None = None) -> list[dict]:
    """Every directory the walk stopped at because it is another checkout.

    Returns:
        One record per boundary, with the marker that identified it. Empty on
        a tree with no nested checkout, which is the ordinary case.
    """
    return [{"path": shown, "marker": WALK_BOUNDARY.marker} for shown in survey(root).boundaries]


def _markdown_in(directory: Path) -> list[Path]:
    """Return every ``*.md`` entry of a directory, RAISING on a refused listing.

    CS-1115. ``glob`` swallows a refused listing and yields nothing, so a
    budgeted population behind it vanished while the verdict still read PASS.
    ``iterdir`` raises instead, and the caller turns that into a reported row.
    An absent directory is still an empty population, as before.

    Raises:
        OSError: When the directory exists and cannot be listed.
    """
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if path.match("*.md"))


def _memory_leaves(root: Path) -> list[Path]:
    """Return every memory leaf. Raises OSError on a refused listing."""
    return [path for path in _markdown_in(root / "memory") if path.name != "MEMORY.md"]


def _item_notes_leaves(root: Path) -> list[Path]:
    """Return every leaf of the docs/item_notes/ family.

    DERIVED, never listed. A hand-maintained list of leaf names would let a new
    leaf join the tree unmeasured, which is the failure this tool's own
    population statement exists to refuse.

    Raises:
        OSError: When the directory exists and cannot be listed.
    """
    return _markdown_in(root / "docs" / "item_notes")


def _unlisted_entry(shown: str, budget: int, severity: str, rule: str) -> dict:
    """A row for a DIRECTORY whose budgeted files could not be enumerated."""
    return {
        "file": shown.rstrip("/") + "/",
        "rule": rule,
        "severity": severity,
        "budget_bytes": budget,
        "actual_bytes": None,
        "status": UNLISTED,
        "guidance": "",
    }


def _leaf_rows(
    root: Path, lister: Callable[[Path], list[Path]], directory: str, budget: int, rule: str
) -> list[dict]:
    """Measure every leaf a lister finds, or report the directory it could not list."""
    try:
        leaves = lister(root)
    except OSError:
        return [_unlisted_entry(directory, budget, "WARN", rule)]
    return [_entry(root, leaf, budget, "WARN", rule) for leaf in leaves]


def _size(path: Path) -> int | str | None:
    """The size of a regular file, NOT_A_FILE for anything else, None when absent."""
    try:
        observed = path.stat()
    except OSError:
        return None
    if not stat.S_ISREG(observed.st_mode):
        return NOT_A_FILE
    return observed.st_size


def _display(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _entry(root: Path, path: Path, budget: int, severity: str, rule: str) -> dict:
    actual = _size(path)
    if actual is None:
        status = "MISSING"
    elif isinstance(actual, str):
        status = actual
        actual = None
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


def evaluate(root: Path | None = None, observed: Survey | None = None) -> list[dict]:
    """Measure every budgeted file.

    This is the single implementation of the CONVENTIONS section 2.1 table.
    tools/drift_guard.py calls it directly rather than re-deriving the budgets.

    Args:
        root: The repository root.
        observed: A survey already taken for this root. Passing it keeps one
            invocation to ONE git query rather than one per consumer.
    """
    root = root or repo_root()
    observed = observed if observed is not None else survey(root)
    claude_md = root / "CLAUDE.md"
    rows = [_entry(root, claude_md, CLAUDE_BUDGET, "HARD", "CLAUDE.md")]

    rows.extend(
        _entry(root, path, AUTOLOADED_BUDGET, "HARD", "auto-loaded file")
        for path in _autoloaded_files(root, observed)
        if path != claude_md
    )
    rows.extend(
        _unlisted_entry(shown, AUTOLOADED_BUDGET, "HARD", "auto-loaded file")
        for shown in observed.unlisted
    )
    rows.append(
        _entry(root, root / "memory" / "MEMORY.md", MEMORY_INDEX_BUDGET, "HARD", "memory index")
    )
    rows.extend(_leaf_rows(root, _memory_leaves, "memory", MEMORY_LEAF_BUDGET, "memory leaf"))
    rows.append(_entry(root, root / "ROADMAP.md", ROADMAP_BUDGET, "WARN", "ROADMAP.md"))
    rows.append(
        _entry(
            root,
            root / "docs" / "item_notes.md",
            ITEM_NOTES_INDEX_BUDGET,
            "WARN",
            "docs/item_notes.md (index)",
        )
    )
    rows.extend(
        _leaf_rows(
            root, _item_notes_leaves, "docs/item_notes", ITEM_NOTES_LEAF_BUDGET, "item-notes leaf"
        )
    )
    rows.append(
        _entry(
            root,
            root / "docs" / "upstream_watch.md",
            UPSTREAM_WATCH_BUDGET,
            "WARN",
            "docs/upstream_watch.md",
        )
    )
    return rows


def hard_failures(rows: list[dict]) -> list[dict]:
    """Return the rows that breach a hard budget."""
    return [row for row in rows if row["status"] == "OVER" and row["severity"] == "HARD"]


def soft_failures(rows: list[dict]) -> list[dict]:
    """Return the rows that breach a warn-level budget."""
    return [row for row in rows if row["status"] == "OVER" and row["severity"] == "WARN"]


def unlisted_directories(rows: list[dict]) -> list[str]:
    """Return each directory a row reports as not listed, once, in order (CS-1115)."""
    return list(dict.fromkeys(row["file"] for row in rows if row["status"] == UNLISTED))


def not_files(rows: list[dict]) -> list[str]:
    """Return each budgeted name carried by something that is not a file, once (CS-1117)."""
    return list(dict.fromkeys(row["file"] for row in rows if row["status"] == NOT_A_FILE))


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


def _population_statement(observed: Survey | None) -> list[str]:
    """State which roots were walked, what stopped the walk, and what was left out.

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
    out.append(f"  stops at a registered worktree - {REGISTERED_WORKTREE_REASON}")
    out.append(f"  membership - {MEMBERSHIP_REASON}")
    if observed is None:
        return out

    if not observed.index_available:
        out.append(f"  DEGRADED - {INDEX_UNAVAILABLE_REASON}")
    if observed.boundaries:
        out.append("  not descended into (a checkout of its own, measured by its own tree):")
        out.extend(f"    {shown}" for shown in observed.boundaries)
    else:
        out.append("  not descended into: (no nested checkout found)")
    if observed.excluded:
        out.append("  walked but NOT measured (this tree does not own it):")
        out.extend(f"    {shown}" for shown in observed.excluded)
    return out


def render(rows: list[dict], observed: Survey | None = None) -> list[str]:
    """Render the budget table and the verdict as printable lines.

    Args:
        rows: The rows from :func:`evaluate`.
        observed: Optional result of :func:`survey`. When omitted the declared
            population is still stated; only what this run observed is left
            out, because that needs its own walk.
    """
    out = ["Documentation size budgets (CONVENTIONS.md section 2.1; 1 KB = 1024 bytes)", ""]
    out.extend(_table(rows))
    out.extend(_population_statement(observed))

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

    unlisted = unlisted_directories(rows)
    if unlisted:
        out.extend(
            [
                "",
                "NOT LISTED (the directory refused a listing - the budgeted files in it "
                "were never seen, so no count below covers them):",
            ]
        )
        out.extend(f"  {shown}" for shown in unlisted)

    shapes = not_files(rows)
    if shapes:
        out.extend(
            [
                "",
                "NOT A FILE (a directory carries a budgeted file's name - nothing was "
                "measured, and it is not merely absent; rename or remove it):",
            ]
        )
        out.extend(f"  {shown}" for shown in shapes)

    hard = hard_failures(rows)
    warn = soft_failures(rows)
    measured = sum(1 for row in rows if row["status"] not in ("MISSING", UNLISTED, NOT_A_FILE))
    out.append("")
    out.append(
        f"measured: {measured}    over budget: {len(over)} "
        f"(HARD {len(hard)}, WARN {len(warn)})    absent: {len(missing)}    "
        f"not listed: {len(unlisted)}    not a file: {len(shapes)}"
    )
    if hard:
        out.append(f"VERDICT: FAIL - {len(hard)} hard budget failure(s)")
    elif shapes:
        out.append(
            f"VERDICT: NOT A FILE - {len(shapes)} budgeted name(s) carried by a directory, "
            "so this run cannot say every budgeted file is inside its budget"
        )
    elif unlisted:
        out.append(
            f"VERDICT: INCOMPLETE - {len(unlisted)} director(ies) could not be listed, "
            "so this run cannot say every budgeted file is inside its budget"
        )
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
    # ONE survey, shared by the table and the statement. Two git calls for the
    # whole invocation rather than two per consumer.
    observed = survey(root)
    rows = evaluate(root, observed)
    hard = hard_failures(rows)
    warn = soft_failures(rows)

    unlisted = unlisted_directories(rows)
    shapes = not_files(rows)
    if args.json:
        if hard:
            verdict = "FAIL"
        elif shapes:
            verdict = "NOT_A_FILE"
        elif unlisted:
            verdict = "INCOMPLETE"
        else:
            verdict = "WARN" if warn else "PASS"
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
                        "membership_reason": MEMBERSHIP_REASON,
                        "registered_worktree_reason": REGISTERED_WORKTREE_REASON,
                        "index_available": observed.index_available,
                        "index_unavailable_reason": (
                            "" if observed.index_available else INDEX_UNAVAILABLE_REASON
                        ),
                        "not_descended_into": [
                            {"path": shown, "marker": WALK_BOUNDARY.marker}
                            for shown in observed.boundaries
                        ],
                        "walked_but_not_owned": list(observed.excluded),
                    },
                    "rows": rows,
                    "hard_failures": [row["file"] for row in hard],
                    "warnings": [row["file"] for row in warn],
                    "unlisted": unlisted,
                    "not_files": shapes,
                    "verdict": verdict,
                },
                indent=2,
            )
        )
    else:
        print("\n".join(render(rows, observed)))

    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
