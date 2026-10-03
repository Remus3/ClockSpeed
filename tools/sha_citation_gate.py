#!/usr/bin/env python3
"""CS-1222 - every commit sha an authored doc cites must be PUBLISHED, or the gate is red.

WHY. ``docs/LEDGER.md`` forbids citing a slice sha and names "A bare commit SHA"
an invalid pointer, and nothing enforced it: four tools grade a commit field's
SHAPE and never ask git, so the next unresolvable sha to land would land
silently. This gate asks git about every one.

THE INCLUSION RULE is published verbatim as :data:`INCLUSION_RULE` and printed
on every run, and it states what it does NOT admit and why.

THE RESOLVER. Each distinct sha-shaped token is resolved with ``git rev-parse
--verify -q <token>^{commit}``, and the commit it names counts ONLY when it is
reachable from a PUBLISHED ref - ``refs/remotes/origin/main`` or a tag, and
nothing else. An object that lives only on a local branch, in a worktree, in
the reflog or on a side branch of the remote resolves today and dies the day
that branch is deleted, so it is reported ``unpublished`` and FAILS. An
ambiguous short sha does not resolve either - a citation two commits answer is
no citation.

THE EXCLUSIONS ARE AN ALLOWLIST, NEVER A SHAPE. :data:`ALLOWLIST` is a table of
the exact non-commit tokens measured in this tree's docs, one row per token,
each with a class from the closed set :data:`CLASSES` and a stated reason. A
token the table does not name is a citation, WHATEVER TEXT SURROUNDS IT - an
``@``, an ``owner/repo at``, a ``...``, a ``-dirty``, a ``run`` label. A shape
rule was tried first and an adversary walked unresolvable shas through every
one of them; a shape is a denylist in disguise. Shapes survive only as HINTS
printed beside a failing token (:func:`hint_for`), so whoever adds a row knows
what the token looked like - a hint never excludes anything.

THE ANTI-ESCAPE CONTROL. Every allowlisted token is resolved too, and one that
names a published commit is reported as ``overreach`` and makes the gate exit
1: a row may name only a thing that is not a commit. Each run also lists the
rows no doc carries any more (``allowlist-unused``), so the table cannot rot
into a set of standing exemptions nobody can see.

AN EMPTY RESULT IS NEVER A PASS ON ITS OWN. Exit 0 needs a full-history
repository with at least one published ref AND at least one admitted citation,
every one published, and no overreach. A shallow clone, a repository with no
published ref, a missing git, or a sweep that admitted nothing exits 2,
"could not judge", because each of those reads exactly like a clean sweep.

THE DISCRIMINATOR. A sha that history rewriting removed and a sha that never
existed both fail to resolve. ``git filter-repo`` leaves a ``commit-map`` under
``<git-common-dir>/filter-repo/`` that tells them apart; every run states
whether it is present, and when it is, an unresolved sha the map names as an
OLD commit is labelled ``rewritten-away`` instead of ``never-resolved``. Both
still fail - the label says which repair applies, not whether one is due.

CLI::

    python tools/sha_citation_gate.py [--repo DIR]

    exit 0   every admitted citation is a published commit, no allowlisted
             token is one, and at least one citation was admitted
    exit 1   an admitted citation is not a published commit, or an allowlisted
             token is one (overreach)
    exit 2   could not judge - no git, not a repository, a shallow clone, no
             published ref, or a sweep that admitted nothing

stdout prints only repository-relative paths, line numbers and the tokens
themselves - never a doc line's text, and never an environment value.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

# `tools` carries no __init__.py, so the sibling resolver is imported under its
# BARE name, the way tools/trailer_census.py does it.
_TOOLS_DIR: Final = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

EXIT_CLEAN: Final = 0
EXIT_UNRESOLVED: Final = 1
EXIT_COULD_NOT_JUDGE: Final = 2

#: Seconds one git call may take.
GIT_TIMEOUT: Final = 120

#: The tracked files the sweep reads, as git pathspecs.
DOC_PATHSPECS: Final = ("*.md", "*.txt")

#: The refs whose history counts as published: the remote's main line and every
#: tag. A side branch, even a pushed one, can be deleted - and its citations with it.
PUBLISHED_REFS: Final = ("refs/remotes/origin/main", "refs/tags")

INCLUSION_RULE: Final = (
    "ADMITTED: a run of 7 to 40 lower-case hex characters carrying at least one digit and "
    "at least one letter, with no letter, digit or underscore on either side, in a tracked "
    "*.md or *.txt file. NOT ADMITTED, by design: an all-digit run, because decimal numbers "
    "(CI run ids, counts, offsets) outnumber any all-digit abbreviation and cannot be told "
    "from one; an all-letter run, because that is an English word as often as a sha; "
    "upper-case hex, because git prints every object name in lower case, so an upper-case "
    "run is a constant or an identifier and never a copied sha; and a run longer than 40, "
    "which is a sha256 and not a sha1 object name"
)

_TOKEN: Final = re.compile(r"(?<![0-9A-Za-z_])[0-9a-f]{7,40}(?![0-9A-Za-z_])")
_HAS_DIGIT: Final = re.compile(r"[0-9]")
_HAS_LETTER: Final = re.compile(r"[a-f]")

#: Variables that would point a child git at a repository other than ``--repo``.
#: The pre-push hook exports GIT_DIR, so a gate run beneath it must drop them.
_GIT_REDIRECTS: Final = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
)

#: The CLOSED set of non-commit classes - the acceptance's measured classes plus
#: guid. A row naming any other class is refused when the table is loaded.
CLASSES: Final[dict[str, str]] = {
    "agent-id": "a subagent, worktree or review-session id, never a git object",
    "sha256-prefix": "a prefix or tail of a sha256 content digest, never a git object",
    "foreign-pin": "a commit of a FOREIGN repository, pinned by a licence gate",
    "git-blob": "a git blob sha1 - an object, but not a commit",
    "lane-run-id": "a queue-lane run id minted from uuid4 hex",
    "fixture-vector": "a synthetic test vector written by hand",
    "guid": "one group of a GUID",
}


@dataclass(frozen=True)
class AllowRow:
    """One allowlisted non-commit token.

    Attributes:
        token: The exact token, as the docs spell it.
        klass: Its class, from :data:`CLASSES`.
        reason: Why it is not a commit, and where it was measured.
    """

    token: str
    klass: str
    reason: str


_A, _S, _F, _B, _R, _V, _G = CLASSES.keys()

#: The allowlist, MEASURED on this tree on 2026-10-02. Add a row only for a token
#: that is provably not a commit of this repository; the overreach control
#: reddens a row that turns out to be one.
ALLOWLIST: Final[tuple[AllowRow, ...]] = (
    AllowRow("ace624231ac7fd814", _A, "CS-1207 worktree id, CS-NEXT-SESSION and WAKEUP_NOTES"),
    AllowRow("a1d0d1c85dd5bc8fc", _A, "worktree id named by a prune record, history_notes"),
    AllowRow("a29bded19d0edd514", _A, "worktree branch id, phase4-followups-900"),
    AllowRow("a4f0885163222ba12", _A, "CS-815 builder worktree id, history_notes"),
    AllowRow("a7a207a7fac1a22b7", _A, "CS-492 round worktree id, phase4-followups-900"),
    AllowRow("a8b7284852bf73422", _A, "worktree removed on instruction, history_notes"),
    AllowRow("a8f0774be4d10c1fe", _A, "clean worktree removed by a prune, history_notes"),
    AllowRow("a970f46db2e225244", _A, "CS-492 round worktree id, phase4-followups-900"),
    AllowRow("ab7fcd5c63f9193ea", _A, "merged worktree branch id, history_notes"),
    AllowRow("abccd667b38e14135", _A, "worktree branch id, phase4-followups and -900"),
    AllowRow("ac95f3565beb2209d", _A, "worktree id holding unmerged work, history_notes"),
    AllowRow("ad45630ce2d98d6dd", _A, "CS-988 sweep worktree id, cs988-sweep-record"),
    AllowRow("af11f14194b6508f8", _A, "worktree branch id, phase4-followups-900"),
    AllowRow("af6f0393f63bd2adb", _A, "clean worktree id, history_notes"),
    AllowRow(
        "e085b4a92ab2",
        _A,
        "the CS-REVIEW session id inside a channel note's filename, history_notes - the "
        "one row whose class is inferred from the filename and not measured",
    ),
    AllowRow("05f4c6b", _S, "tail of the CHANNEL.md v1 sha256 `899f6eb9...05f4c6b`, LEDGER"),
    AllowRow("899f6eb9", _S, "head of the CHANNEL.md v1 sha256, LEDGER"),
    AllowRow("fc22e86e", _S, "head of the CHANNEL.md v2 sha256, LEDGER and history_notes"),
    AllowRow("fafa13c0", _S, "head of a regenerated integrity digest, LEDGER"),
    AllowRow("f1b4b011", _S, "head of the carriers' shared-file sha256, history_notes"),
    AllowRow("0b112a4f", _S, "head of a sixth repository's published digest, history_notes"),
    AllowRow("71fa2a683f2eaa04", _S, "head of UPSTREAM_SLOTS_DIGEST, history_notes"),
    AllowRow("72c750bb", _F, "tt-a1i/archify licence-gate pin, CS-1098 ruling quote, LEDGER"),
    AllowRow("72c750bb070d95171dbb2244e5b62b1b7da69c12", _F, "tt-a1i/archify full pin, LEDGER"),
    AllowRow("5bca294", _F, "mksglu/context-mode pin, CS-1099 ruling quote, LEDGER"),
    AllowRow("5bca2948959a7fb538e895d9a032c1a19b8685a5", _F, "mksglu/context-mode full pin"),
    AllowRow("a9317e03", _F, "timharris707/skills pin, CS-1100 ruling quote, LEDGER"),
    AllowRow("a9317e03733da7f54b5da0eaa8edcb2697495cf5", _F, "timharris707/skills full pin"),
    AllowRow("4b3a567", _B, "pre-commit hook blob, one of three blob SHAs, LEDGER"),
    AllowRow("b7a4cd0", _B, "pre-commit hook blob, one of three blob SHAs, LEDGER"),
    AllowRow("e12e087", _B, "pre-commit hook blob, one of three blob SHAs, LEDGER"),
    AllowRow("d90c7876", _B, "tools/precommit_gate.py blob verified by hash, LEDGER"),
    AllowRow("9c16958af3168e19005ab1c257b529f399d2fdfa", _B, "reach_guard.py hash-object"),
    AllowRow("5ff0ddfd", _R, "the 2026-09-11 lane start failure row, lane-start-failure-record"),
    AllowRow("62f29b90", _R, "the cycle-8 lane run with no worker log, history_notes"),
    AllowRow("e085d9aa", _R, "a lane status row's run_id, LEDGER"),
    AllowRow("a1b2c3d4e5f60718", _V, "CS-1174 survival table, synthetic Epic-shaped hex"),
    AllowRow("a1b2c3d4", _G, "first group of the CS-1174 synthetic braceless GUID"),
    AllowRow("def012345678", _G, "last group of the CS-1174 synthetic braceless GUID"),
)


def allowlist_map(rows: Sequence[AllowRow] = ALLOWLIST) -> dict[str, str]:
    """The table as ``token -> class``, refusing an unknown class or a duplicate.

    Args:
        rows: The rows to index.

    Returns:
        Each token mapped to its class.

    Raises:
        ValueError: On a class outside :data:`CLASSES`, an empty reason, a
            token outside the inclusion shape, or a token listed twice.
    """
    mapped: dict[str, str] = {}
    for row in rows:
        if row.klass not in CLASSES or not row.reason.strip():
            raise ValueError(f"allowlist row {row.token} has no stated class or reason")
        if not (
            _TOKEN.fullmatch(row.token)
            and _HAS_DIGIT.search(row.token)
            and _HAS_LETTER.search(row.token)
        ):
            raise ValueError(f"allowlist row {row.token} is not sha-shaped")
        if row.token in mapped:
            raise ValueError(f"allowlist row {row.token} is listed twice")
        mapped[row.token] = row.klass
    return mapped


# --- hints: shapes, used ONLY to describe a failing token ---------------------

_HINTS: Final[tuple[tuple[str, Callable[[str, str], bool]], ...]] = (
    ("looks like an agent or worktree id", lambda p, _s: p.endswith("agent-")),
    (
        "looks like a foreign pin",
        lambda p, _s: p.endswith("@") or bool(re.search(r"/\S+\s+at\s+`?$", p)),
    ),
    ("looks like a digest", lambda p, _s: bool(re.search(r"(?i)(sha-?256|digest)\W*$", p))),
    ("looks like a blob", lambda p, _s: bool(re.search(r"(?i)blob\W*$", p))),
    ("looks truncated", lambda p, s: s.startswith("...") or p.endswith("...")),
    ("looks like a run id", lambda p, _s: bool(re.search(r"(?i)\brun\W*$", p))),
    ("looks hyphen-joined", lambda p, s: p.endswith("-") or s.startswith("-")),
)


def hint_for(prefix: str, suffix: str) -> str | None:
    """A description of the token's surroundings - NEVER an exemption."""
    return next((text for text, applies in _HINTS if applies(prefix, suffix)), None)


@dataclass(frozen=True)
class Occurrence:
    """One sha-shaped token in one doc.

    Attributes:
        path: Repository-relative path, forward slashes.
        line: One-based line number.
        token: The token itself.
        rule: The allowlist class that excluded it, or None when admitted.
        hint: What its surroundings look like, for a reader - never a verdict.
    """

    path: str
    line: int
    token: str
    rule: str | None
    hint: str | None = None


def scan_text(
    text: str, path: str = "", allowlist: Mapping[str, str] | None = None
) -> list[Occurrence]:
    """Find every sha-shaped token in ``text`` and classify it by the allowlist alone.

    Args:
        text: One file's text.
        path: The name the occurrences carry.
        allowlist: ``token -> class``; the shipped table when None.

    Returns:
        Every occurrence, in text order, each with its class or None.
    """
    table = allowlist_map() if allowlist is None else allowlist
    found: list[Occurrence] = []
    for index, line in enumerate(text.splitlines()):
        for match in _TOKEN.finditer(line):
            token = match.group(0)
            if not (_HAS_DIGIT.search(token) and _HAS_LETTER.search(token)):
                continue
            hint = hint_for(line[: match.start()], line[match.end() :])
            found.append(Occurrence(path, index + 1, token, table.get(token), hint))
    return found


class GateError(Exception):
    """The gate could not run. The reason is fixed text, never a value."""

    def __init__(self, reason: str) -> None:
        """Keep ``reason`` as the one field the CLI prints."""
        super().__init__(reason)
        self.reason = reason


def _env() -> dict[str, str]:
    env = dict(os.environ)
    for name in _GIT_REDIRECTS:
        env.pop(name, None)
    return env


def _git(
    repo: Path, args: Sequence[str], data: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    git = resolve_tool("git")
    if git is None:
        raise GateError("git is not on PATH")
    try:
        return subprocess.run(
            [git, *args],
            cwd=repo,
            env=_env(),
            input=data,
            capture_output=True,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateError(f"git {args[0]} could not be run: {type(exc).__name__}") from None


def _git_out(repo: Path, args: Sequence[str]) -> bytes:
    done = _git(repo, args)
    if done.returncode != 0:
        raise GateError(f"git {args[0]} exited {done.returncode}")
    return done.stdout


def commit_of(repo: Path, token: str) -> str | None:
    """The full name of the ONE commit ``token`` names in ``repo``'s store, or None."""
    done = _git(repo, ["rev-parse", "--verify", "-q", f"{token}^{{commit}}"])
    return done.stdout.decode("ascii").strip() if done.returncode == 0 else None


def _published(repo: Path) -> tuple[int, set[str]]:
    refs = _git_out(repo, ["for-each-ref", "--format=%(refname)", *PUBLISHED_REFS]).split()
    if not refs:
        return 0, set()
    done = _git(repo, ["rev-list", "--stdin"], b"".join(ref + b"\n" for ref in refs))
    if done.returncode != 0:
        raise GateError(f"git rev-list exited {done.returncode}")
    return len(refs), set(done.stdout.decode("ascii").split())


def _commit_map(repo: Path) -> list[str] | None:
    common = _git_out(repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    target = Path(common.decode("utf-8").strip()) / "filter-repo" / "commit-map"
    if not target.is_file():
        return None
    olds: list[str] = []
    for raw in target.read_text(encoding="ascii", errors="replace").splitlines()[1:]:
        fields = raw.split()
        if fields:
            olds.append(fields[0])
    return olds


@dataclass
class SweepReport:
    """One run of the gate.

    Attributes:
        files: How many docs were read.
        occurrences: Every sha-shaped occurrence, admitted or excluded.
        shallow: Whether the repository is a shallow clone.
        published_refs: How many refs under :data:`PUBLISHED_REFS` exist.
        rewritten: The OLD shas a filter-repo commit-map names, or None when
            no map is present - the discriminator is unavailable.
        allowlist: The ``token -> class`` table this run used.
        unresolved: Each admitted occurrence that is not a published commit,
            with its state - ``unpublished``, ``rewritten-away`` or
            ``never-resolved``.
        overreach: Each EXCLUDED occurrence whose token IS a published commit.
    """

    files: int
    occurrences: list[Occurrence]
    shallow: bool
    published_refs: int
    rewritten: list[str] | None
    allowlist: Mapping[str, str]
    unresolved: list[tuple[Occurrence, str]] = field(default_factory=list)
    overreach: list[Occurrence] = field(default_factory=list)

    @property
    def admitted(self) -> list[Occurrence]:
        """The occurrences the allowlist did not name."""
        return [entry for entry in self.occurrences if entry.rule is None]

    @property
    def unused(self) -> list[str]:
        """Allowlist rows no doc carries any more."""
        seen = {entry.token for entry in self.occurrences}
        return sorted(token for token in self.allowlist if token not in seen)

    def verdict(self) -> int:
        """Exit 2 when nothing can be judged, 1 on a failure, else 0."""
        if self.shallow or not self.published_refs or not self.admitted:
            return EXIT_COULD_NOT_JUDGE
        return EXIT_UNRESOLVED if self.unresolved or self.overreach else EXIT_CLEAN


def _state(report: SweepReport, token: str, commit: str | None) -> str:
    if commit is not None:
        return "unpublished"
    if report.rewritten is not None and any(old.startswith(token) for old in report.rewritten):
        return "rewritten-away"
    return "never-resolved"


def sweep(repo: Path, allowlist: Mapping[str, str] | None = None) -> SweepReport:
    """Read every tracked doc in ``repo`` and judge every citation against published history.

    Args:
        repo: A work tree.
        allowlist: ``token -> class``; the shipped table when None.

    Returns:
        The report. On a shallow clone, or with no published ref, nothing is
        resolved - nothing can be judged.

    Raises:
        GateError: When git cannot be run or ``repo`` is not a repository.
    """
    table = allowlist_map() if allowlist is None else allowlist
    shallow = _git_out(repo, ["rev-parse", "--is-shallow-repository"]).strip() != b"false"
    listed = _git_out(repo, ["ls-files", "-z", "--", *DOC_PATHSPECS]).decode("utf-8")
    paths = sorted(name for name in listed.split("\0") if name)
    occurrences: list[Occurrence] = []
    for name in paths:
        target = repo / name
        if target.is_file():
            text = target.read_text(encoding="utf-8", errors="replace")
            occurrences += scan_text(text, name, table)
    ref_count, published = (0, set()) if shallow else _published(repo)
    report = SweepReport(len(paths), occurrences, shallow, ref_count, _commit_map(repo), table)
    if shallow or not ref_count:
        return report
    commits = {token: commit_of(repo, token) for token in sorted({e.token for e in occurrences})}
    for entry in occurrences:
        commit = commits[entry.token]
        is_published = commit is not None and commit in published
        if entry.rule is not None and is_published:
            report.overreach.append(entry)
        elif entry.rule is None and not is_published:
            report.unresolved.append((entry, _state(report, entry.token, commit)))
    return report


def render(report: SweepReport) -> list[str]:
    """The lines one run prints: rule, counts, every exclusion, resolver, verdict."""
    admitted = report.admitted
    out = [
        f"sha_citation_gate: inclusion - {INCLUSION_RULE}",
        f"sha_citation_gate: files {report.files}; sha-shaped occurrences "
        f"{len(report.occurrences)}; admitted {len(admitted)} "
        f"({len({entry.token for entry in admitted})} distinct); "
        f"unresolved {len(report.unresolved)}; overreach {len(report.overreach)}",
        f"allowlist rows {len(report.allowlist)}; unused {len(report.unused)} - exact tokens "
        "only, never a shape",
    ]
    for name, sentence in CLASSES.items():
        count = sum(1 for entry in report.occurrences if entry.rule == name)
        out.append(f"excluded-count {name} {count} - {sentence}")
    out += [
        f"excluded {entry.rule} {entry.path}:{entry.line} {entry.token}"
        for entry in report.occurrences
        if entry.rule is not None
    ]
    out += [f"allowlist-unused {token}" for token in report.unused]
    if report.shallow:
        out.append("resolver SHALLOW - a shallow clone holds no history, so nothing was resolved")
    elif not report.published_refs:
        out.append(
            "resolver NO-PUBLISHED-REF - no refs/remotes/origin/main and no tag, nothing resolved"
        )
    else:
        out.append(
            "resolver full - git rev-parse --verify -q <sha>^{commit}, counted only when "
            f"reachable from refs/remotes/origin/main or a tag ({report.published_refs} refs)"
        )
    out.append(
        "discriminator filter-repo commit-map: ABSENT - a sha rewritten away and one that "
        "never existed are indistinguishable here"
        if report.rewritten is None
        else f"discriminator filter-repo commit-map: AVAILABLE - {len(report.rewritten)} old shas"
    )
    out += [
        f"unresolved {entry.path}:{entry.line} {entry.token} {state}"
        + (
            f" (hint: {entry.hint}; if it is not a commit, add an ALLOWLIST row)"
            if entry.hint
            else ""
        )
        for entry, state in report.unresolved
    ]
    out += [
        f"overreach {entry.rule} {entry.path}:{entry.line} {entry.token} is a published commit"
        for entry in report.overreach
    ]
    verdict = report.verdict()
    if verdict == EXIT_CLEAN:
        out.append("sha_citation_gate: PASS - every admitted citation is a published commit")
    elif verdict == EXIT_UNRESOLVED:
        out.append(
            "sha_citation_gate: FAIL - a citation is not a published commit, "
            "or an allowlisted token is one"
        )
    else:
        if report.shallow:
            reason = "a shallow clone"
        elif not report.published_refs:
            reason = "no published ref"
        else:
            reason = "the sweep admitted nothing"
        out.append(f"sha_citation_gate: COULD NOT JUDGE - {reason}, which is not a pass")
    return out


def main(argv: list[str] | None = None) -> int:
    """Run the gate and print its report.

    Args:
        argv: Arguments, without the program name; ``sys.argv`` when None.

    Returns:
        0 clean, 1 a failing citation or an overreach, 2 could not judge.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--repo", type=Path, default=_TOOLS_DIR.parent, help="the work tree")
    args = parser.parse_args(argv)
    try:
        report = sweep(args.repo)
    except GateError as exc:
        print(f"sha_citation_gate: COULD NOT JUDGE - {exc.reason}", file=sys.stderr)
        return EXIT_COULD_NOT_JUDGE
    print("\n".join(render(report)))
    return report.verdict()


if __name__ == "__main__":
    sys.exit(main())
