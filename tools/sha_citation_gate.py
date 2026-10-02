#!/usr/bin/env python3
"""CS-1222 - every commit sha an authored doc cites must resolve, or the gate is red.

WHY. ``docs/LEDGER.md`` forbids citing a slice sha and names "A bare commit SHA"
an invalid pointer, and nothing enforced it: four tools grade a commit field's
SHAPE and never ask git, so the next unresolvable sha to land would land
silently. This gate asks git about every one.

THE INCLUSION RULE, published verbatim as :data:`INCLUSION_RULE` and printed on
every run: a token is sha-shaped when it is a run of 7 to 40 LOWER-CASE hex
characters, carrying at least one digit AND at least one letter, with no letter,
digit or underscore on either side, inside a tracked ``*.md`` or ``*.txt`` file.
So a decimal run (a CI run id, a count), an all-letter word, upper-case hex, a
run embedded in a longer word and a 64-character sha256 are never admitted.

THE EXCLUSION RULES, published as :data:`EXCLUSION_RULES` and each counted on
every run, zeros included, with every excluded site listed. Each is a STATED
property of the token or of the text around it - never a path exemption - and
each exists for a non-commit class measured on 2026-10-02. A rule is judged on
the token's own line plus the line before it, because these docs are hard
wrapped and a label often sits one line up. Rules are tried in order and the
first match names the class.

THE RESOLVER is ``git rev-parse --verify -q <token>^{commit}``, one call per
distinct admitted token. An ambiguous short sha does not resolve either, and is
reported with the rest - a citation two commits answer is no citation.

AN EMPTY RESULT IS NEVER A PASS ON ITS OWN. Exit 0 needs a full-history
repository AND at least one admitted citation, every one resolving. A shallow
clone, a missing git, or a sweep that admitted nothing exits 2, "could not
judge", because each of those reads exactly like a clean sweep.

THE DISCRIMINATOR. A sha that history rewriting removed and a sha that never
existed both fail to resolve. ``git filter-repo`` leaves a ``commit-map`` under
``<git-common-dir>/filter-repo/`` that tells them apart; every run states
whether it is present, and when it is, an unresolved sha the map names as an
OLD commit is labelled ``rewritten-away`` instead of ``never-resolved``. Both
still fail - the label says which repair applies, not whether one is due.

THE RESOLVER'S SCOPE IS THIS OBJECT STORE. A slice commit that lives only on a
local branch or in a worktree resolves here and not in a fresh clone; the gate
grades the store it is run against and claims nothing about any other.

CLI::

    python tools/sha_citation_gate.py [--repo DIR]

    exit 0   every admitted citation resolves, and at least one was admitted
    exit 1   at least one admitted citation does not resolve
    exit 2   could not judge - no git, not a repository, a shallow clone, or a
             sweep that admitted nothing

stdout prints only repository-relative paths, line numbers and the tokens
themselves - never a doc line's text, and never an environment value.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
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
GIT_TIMEOUT: Final = 60

#: The tracked files the sweep reads, as git pathspecs.
DOC_PATHSPECS: Final = ("*.md", "*.txt")

INCLUSION_RULE: Final = (
    "a run of 7 to 40 lower-case hex characters with at least one digit and one letter, "
    "no letter, digit or underscore on either side, in a tracked *.md or *.txt file"
)

_TOKEN: Final = re.compile(r"(?<![0-9A-Za-z_])[0-9a-f]{7,40}(?![0-9A-Za-z_])")
_HAS_DIGIT: Final = re.compile(r"[0-9]")
_HAS_LETTER: Final = re.compile(r"[a-f]")

#: Characters of context a keyword rule reads before and after the token.
_BEFORE: Final = 60
_AFTER: Final = 30

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

_GUID: Final = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)
_FOREIGN_REPO_AT: Final = re.compile(r"[\w.-]+/[\w.-]+\s+at\s+$")
_JOINED_BEFORE: Final = re.compile(r"[0-9A-Za-z]-$")
_JOINED_AFTER: Final = re.compile(r"-[0-9A-Za-z]")
_RUN_LABEL: Final = re.compile(r"(?i)\brun(?:[ _]id)?[\"'`:\s]*$")
_RUN_ID_WIDTH: Final = 8
_PLACEHOLDER_RUNS: Final = ("a1b2c3", "012345", "123456", "abcdef", "deadbeef", "cafebabe")
_DIGEST_WORDS: Final = ("digest", "sha256", "sha-256", "hash")
_BLOB_WORDS: Final = ("blob", "hash-object")


@dataclass(frozen=True)
class _Site:
    """One token's place in its text, with the context the rules read."""

    token: str
    prefix: str
    suffix: str
    span_text: str
    start: int
    end: int


def _within_guid(site: _Site) -> bool:
    return any(
        match.start() <= site.start and site.end <= match.end()
        for match in _GUID.finditer(site.span_text)
    )


def _hyphen_joined(site: _Site) -> bool:
    return bool(_JOINED_BEFORE.search(site.prefix) or _JOINED_AFTER.match(site.suffix))


def _near(site: _Site, words: Sequence[str]) -> bool:
    window = (site.prefix[-_BEFORE:] + " " + site.token + " " + site.suffix[:_AFTER]).lower()
    return any(word in window for word in words)


#: The stated rules, in the order they are tried. Each maps its class name to
#: the sentence that states it and the predicate that applies it.
_RULES: Final[dict[str, tuple[str, Callable[[_Site], bool]]]] = {
    "agent-id": (
        "the token directly follows `agent-`: a subagent or worktree id",
        lambda s: s.prefix.endswith("agent-"),
    ),
    "guid": (
        "the token sits inside an 8-4-4-4-12 hex GUID",
        _within_guid,
    ),
    "compound-name": (
        "the token is hyphen-joined to a letter or digit: one part of a file, branch or note name",
        _hyphen_joined,
    ),
    "foreign-pin": (
        "the token directly follows `@`, or follows `owner/repo at `: a foreign repository pin",
        lambda s: s.prefix.endswith("@") or bool(_FOREIGN_REPO_AT.search(s.prefix)),
    ),
    "git-blob": (
        "`blob` or `hash-object` is near the token: a git blob sha1, not a commit",
        lambda s: _near(s, _BLOB_WORDS),
    ),
    "content-digest": (
        "`digest`, `sha256`, `sha-256` or `hash` is near the token: a content digest prefix",
        lambda s: _near(s, _DIGEST_WORDS),
    ),
    "truncation": (
        "the token is followed by `...` and then no letter or digit: a truncated digest",
        lambda s: s.suffix.startswith("...") and not s.suffix[3:4].isalnum(),
    ),
    "run-id": (
        "an 8-character token directly after `run`, `run id` or `run_id`: a lane run id",
        lambda s: len(s.token) == _RUN_ID_WIDTH and bool(_RUN_LABEL.search(s.prefix)),
    ),
    "fixture-vector": (
        "the token carries a placeholder run (a1b2c3, 012345, 123456, abcdef, deadbeef, "
        "cafebabe): a synthetic vector",
        lambda s: any(run in s.token for run in _PLACEHOLDER_RUNS),
    ),
}

#: Applied after the rules above: a token one site of a file classified is that
#: class at every other site of the same file.
SAME_FILE_LABEL: Final = "same-file-label"

EXCLUSION_RULES: Final[dict[str, str]] = {
    **{name: sentence for name, (sentence, _) in _RULES.items()},
    SAME_FILE_LABEL: "the same token is classified at another site of the same file",
}


@dataclass(frozen=True)
class Occurrence:
    """One sha-shaped token in one doc.

    Attributes:
        path: Repository-relative path, forward slashes.
        line: One-based line number.
        token: The token itself.
        rule: The exclusion class that removed it, or None when admitted.
    """

    path: str
    line: int
    token: str
    rule: str | None


def scan_text(text: str, path: str = "") -> list[Occurrence]:
    """Find every sha-shaped token in ``text`` and classify it.

    Args:
        text: One file's text.
        path: The name the occurrences carry.

    Returns:
        Every occurrence, in text order, each with its exclusion class or None.
    """
    lines = text.splitlines()
    found: list[Occurrence] = []
    for index, line in enumerate(lines):
        previous = lines[index - 1] if index else ""
        joined = previous + "\n" + line
        offset = len(previous) + 1
        for match in _TOKEN.finditer(line):
            token = match.group(0)
            if not (_HAS_DIGIT.search(token) and _HAS_LETTER.search(token)):
                continue
            site = _Site(
                token,
                joined[: offset + match.start()],
                line[match.end() :],
                joined,
                offset + match.start(),
                offset + match.end(),
            )
            rule = next((name for name, (_, applies) in _RULES.items() if applies(site)), None)
            found.append(Occurrence(path, index + 1, token, rule))
    labelled = {entry.token for entry in found if entry.rule is not None}
    return [
        Occurrence(entry.path, entry.line, entry.token, SAME_FILE_LABEL)
        if entry.rule is None and entry.token in labelled
        else entry
        for entry in found
    ]


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


def _git(repo: Path, args: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    git = resolve_tool("git")
    if git is None:
        raise GateError("git is not on PATH")
    try:
        return subprocess.run(
            [git, *args],
            cwd=repo,
            env=_env(),
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


def resolves(repo: Path, token: str) -> bool:
    """Whether ``token`` names exactly one commit in ``repo``'s object store."""
    return _git(repo, ["rev-parse", "--verify", "-q", f"{token}^{{commit}}"]).returncode == 0


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
        rewritten: The OLD shas a filter-repo commit-map names, or None when
            no map is present - the discriminator is unavailable.
        unresolved: The admitted occurrences that did not resolve.
        overreach: Distinct EXCLUDED tokens that resolve as commits after all -
            the rules' over-reach, measured on every run. Harmless to the
            verdict, since each resolves, but a rule that keeps growing this is
            a rule wide enough to hide an unresolvable citation.
    """

    files: int
    occurrences: list[Occurrence]
    shallow: bool
    rewritten: list[str] | None
    unresolved: list[Occurrence] = field(default_factory=list)
    overreach: list[str] = field(default_factory=list)

    @property
    def admitted(self) -> list[Occurrence]:
        """The occurrences no exclusion rule removed."""
        return [entry for entry in self.occurrences if entry.rule is None]

    def label(self, token: str) -> str:
        """Name an unresolved token's class: rewritten away or never resolved."""
        if self.rewritten is not None and any(old.startswith(token) for old in self.rewritten):
            return "rewritten-away"
        return "never-resolved"

    def verdict(self) -> int:
        """Exit 1 on an unresolved citation, 2 when nothing can be judged, else 0."""
        if self.shallow or not self.admitted:
            return EXIT_COULD_NOT_JUDGE
        return EXIT_UNRESOLVED if self.unresolved else EXIT_CLEAN


def sweep(repo: Path) -> SweepReport:
    """Read every tracked doc in ``repo`` and resolve every admitted citation.

    Args:
        repo: A work tree.

    Returns:
        The report. On a shallow clone nothing is resolved - nothing can be judged.

    Raises:
        GateError: When git cannot be run or ``repo`` is not a repository.
    """
    shallow = _git_out(repo, ["rev-parse", "--is-shallow-repository"]).strip() != b"false"
    listed = _git_out(repo, ["ls-files", "-z", "--", *DOC_PATHSPECS]).decode("utf-8")
    paths = sorted(name for name in listed.split("\0") if name)
    occurrences: list[Occurrence] = []
    for name in paths:
        target = repo / name
        if target.is_file():
            occurrences += scan_text(target.read_text(encoding="utf-8", errors="replace"), name)
    report = SweepReport(len(paths), occurrences, shallow, _commit_map(repo))
    if not shallow:
        distinct = sorted({entry.token for entry in report.admitted})
        failing = {token for token in distinct if not resolves(repo, token)}
        report.unresolved = [entry for entry in report.admitted if entry.token in failing]
        excluded = sorted({entry.token for entry in occurrences if entry.rule is not None})
        report.overreach = [token for token in excluded if resolves(repo, token)]
    return report


def render(report: SweepReport) -> list[str]:
    """The lines one run prints: rule, counts, every exclusion, resolver, verdict."""
    admitted = report.admitted
    out = [
        f"sha_citation_gate: inclusion - {INCLUSION_RULE}",
        f"sha_citation_gate: files {report.files}; sha-shaped occurrences "
        f"{len(report.occurrences)}; admitted {len(admitted)} "
        f"({len({entry.token for entry in admitted})} distinct); "
        f"unresolved {len(report.unresolved)}",
    ]
    for name, sentence in EXCLUSION_RULES.items():
        count = sum(1 for entry in report.occurrences if entry.rule == name)
        out.append(f"excluded-count {name} {count} - {sentence}")
    out += [
        f"excluded {entry.rule} {entry.path}:{entry.line} {entry.token}"
        for entry in report.occurrences
        if entry.rule is not None
    ]
    out.append(
        f"excluded-but-resolving {len(report.overreach)} - excluded tokens that DO resolve "
        "as commits: the rules' measured over-reach"
    )
    out += [f"excluded-resolving {token}" for token in report.overreach]
    out.append(
        "resolver SHALLOW - a shallow clone holds no history, so nothing was resolved"
        if report.shallow
        else "resolver full - git rev-parse --verify -q <sha>^{commit} on this object store"
    )
    out.append(
        "discriminator filter-repo commit-map: ABSENT - a sha rewritten away and one that "
        "never existed are indistinguishable here"
        if report.rewritten is None
        else f"discriminator filter-repo commit-map: AVAILABLE - {len(report.rewritten)} old shas"
    )
    out += [
        f"unresolved {entry.path}:{entry.line} {entry.token} {report.label(entry.token)}"
        for entry in report.unresolved
    ]
    verdict = report.verdict()
    if verdict == EXIT_CLEAN:
        out.append("sha_citation_gate: PASS - every admitted citation resolves")
    elif verdict == EXIT_UNRESOLVED:
        out.append("sha_citation_gate: FAIL - an admitted citation does not resolve")
    else:
        reason = "a shallow clone" if report.shallow else "the sweep admitted nothing"
        out.append(f"sha_citation_gate: COULD NOT JUDGE - {reason}, which is not a pass")
    return out


def main(argv: list[str] | None = None) -> int:
    """Run the gate and print its report.

    Args:
        argv: Arguments, without the program name; ``sys.argv`` when None.

    Returns:
        0 clean, 1 an unresolved citation, 2 could not judge.
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
