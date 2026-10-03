#!/usr/bin/env python3
"""CS-1222 - every commit sha an authored doc cites must be PUBLISHED, or the gate is red.

WHY. ``docs/LEDGER.md`` forbids citing a slice sha and names "A bare commit SHA"
an invalid pointer, and nothing enforced it: four tools grade a commit field's
SHAPE and never ask git, so the next unresolvable sha to land would land
silently. This gate asks git about every one.

THE INCLUSION RULE is published verbatim as :data:`INCLUSION_RULE` and printed
on every run, and it states what it does NOT admit and why.

THE RESOLVER. Each distinct admitted token is resolved with ``git rev-parse
--verify -q <token>^{commit}``, and the commit it names counts ONLY when it is
reachable from a PUBLISHED ref - ``refs/remotes/origin/main`` or a tag, and
nothing else. An object that lives only on a local branch, in a worktree, in
the reflog or on a side branch of the remote resolves today and dies the day
that branch is deleted, so it is reported ``unpublished`` and FAILS. An
ambiguous short sha does not resolve either - a citation two commits answer is
no citation.

THE EXCLUSION RULES are published as :data:`EXCLUSION_RULES`, each counted on
every run (zeros included) with every excluded site listed. Each is a STATED
property of the token or of the SAME line's text immediately around it - never
a path exemption, never a window reaching into another line - and each exists
for a non-commit class measured on 2026-10-02. Rules are tried in order and the
first match names the class.

THE ANTI-ESCAPE CONTROL. A rule wide enough to swallow a real commit is wide
enough to hide an unresolvable one, so every EXCLUDED token is resolved too,
and one that names a published commit is reported as ``overreach`` and makes
the gate exit 1. The rules therefore have to stay exactly as narrow as the
population they describe.

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

    exit 0   every admitted citation is a published commit, no exclusion
             swallowed one, and at least one citation was admitted
    exit 1   an admitted citation is not a published commit, or an excluded
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
GIT_TIMEOUT: Final = 120

#: The tracked files the sweep reads, as git pathspecs.
DOC_PATHSPECS: Final = ("*.md", "*.txt")

#: The refs whose history counts as published.
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

_GUID: Final = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_JOINED_BEFORE: Final = re.compile(r"[0-9A-Za-z]-$")
_JOINED_AFTER: Final = re.compile(r"-[0-9A-Za-z]")
#: ``name@`` / ``owner/repo@`` - git has no ``name@<sha>`` spelling of a commit,
#: so this form is never a native citation of one.
_FOREIGN_AT_SIGN: Final = re.compile(r"(?<![\w./-])([\w-]+(?:/[\w-]+)?)@$")
#: ``owner/repo at `` - two slash-joined dot-free segments with no further path
#: before them, so ``tools/x.py at`` and ``a/b/c at`` never match.
_FOREIGN_AT_WORD: Final = re.compile(r"(?<![\w./-])([\w-]+)/([\w-]+)\s+at\s+`?$")
#: ``sha256 X``, ``digest: X`` - and the ``Y`` of a labelled ``X...Y`` head-tail pair.
_DIGEST_LABEL: Final = re.compile(
    r"(?i)(?<![\w-])(?:sha-?256|digest)\s*[:=]?\s*`?(?:[0-9a-f]{7,64}\.\.\.)?$"
)
_BLOB_LABEL: Final = re.compile(r"(?i)(?<![\w-])blob\s*[:=]?\s*`?$")
_RUN_LABEL: Final = re.compile(r"(?i)(?<![\w-])run(?:[ _]id)?[\"'`:\s]*$")
_RUN_ID_WIDTH: Final = 8
#: The placeholder runs MEASURED in this tree's docs on 2026-10-02 - one, from
#: the CS-1174 survival table's synthetic Epic-shaped hex. Nothing else.
_PLACEHOLDER_RUNS: Final = ("a1b2c3d4",)


@dataclass(frozen=True)
class _Site:
    """One token's place in its line, with the context the rules read."""

    token: str
    prefix: str
    suffix: str
    line: str
    start: int
    end: int
    root: Path | None
    remotes: frozenset[str]


def _within_guid(site: _Site) -> bool:
    return any(
        match.start() <= site.start and site.end <= match.end()
        for match in _GUID.finditer(site.line)
    )


def _hyphen_joined(site: _Site) -> bool:
    return bool(_JOINED_BEFORE.search(site.prefix) or _JOINED_AFTER.match(site.suffix))


def _foreign_pin(site: _Site) -> bool:
    if _FOREIGN_AT_SIGN.search(site.prefix):
        return True
    match = _FOREIGN_AT_WORD.search(site.prefix)
    if match is None or match.group(1) in site.remotes:
        # ``origin/main at <sha>`` is a ref of THIS repository, not a foreign pin.
        return False
    # A pair that names a path in this tree is a path, not a foreign repository.
    pair = f"{match.group(1)}/{match.group(2)}"
    return site.root is None or not (site.root / pair).exists()


#: The stated rules, in the order they are tried. Each maps its class name to
#: the sentence that states it and the predicate that applies it.
_RULES: Final[dict[str, tuple[str, Callable[[_Site], bool]]]] = {
    "agent-id": (
        "the token directly follows `agent-`: a subagent or worktree id",
        lambda s: s.prefix.endswith("agent-"),
    ),
    "guid": (
        "the token sits inside an 8-4-4-4-12 lower-case hex GUID",
        _within_guid,
    ),
    "compound-name": (
        "the token is hyphen-joined to a letter or digit: one part of a file, branch or note name",
        _hyphen_joined,
    ),
    "foreign-pin": (
        "the token directly follows `name@` or `owner/repo@` (git has no `name@<sha>` "
        "spelling of a commit), or `owner/repo at ` where the two segments are dot-free, no "
        "further path precedes them, the owner is no remote of this repository and the pair "
        "names no path in this tree: a foreign repository pin",
        _foreign_pin,
    ),
    "content-digest": (
        "the token directly follows `sha256`, `sha-256` or `digest` (optionally `:`, `=` or a "
        "backtick) on the same line, or is the tail of such a labelled `head...tail` pair: a "
        "content digest prefix",
        lambda s: bool(_DIGEST_LABEL.search(s.prefix)),
    ),
    "git-blob": (
        "the token directly follows `blob` (optionally `:`, `=` or a backtick) on the same "
        "line, or names a blob or tree object in this store by `git cat-file -t`: a git "
        "object that is not a commit",
        lambda s: bool(_BLOB_LABEL.search(s.prefix)),
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
        "the token carries the measured placeholder run `a1b2c3d4`: a synthetic vector",
        lambda s: any(run in s.token for run in _PLACEHOLDER_RUNS),
    ),
}

#: The class the store-verified half of the ``git-blob`` rule assigns.
GIT_BLOB: Final = "git-blob"

EXCLUSION_RULES: Final[dict[str, str]] = {name: sentence for name, (sentence, _) in _RULES.items()}


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


def scan_text(
    text: str,
    path: str = "",
    root: Path | None = None,
    remotes: frozenset[str] = frozenset({"origin"}),
) -> list[Occurrence]:
    """Find every sha-shaped token in ``text`` and classify it by the text rules.

    Args:
        text: One file's text.
        path: The name the occurrences carry.
        root: The work tree, so the foreign-pin rule can refuse a real path;
            None when there is no tree to ask.
        remotes: This repository's remote names, which the foreign-pin rule
            refuses as owners.

    Returns:
        Every occurrence, in text order, each with its exclusion class or None.
    """
    found: list[Occurrence] = []
    for index, line in enumerate(text.splitlines()):
        for match in _TOKEN.finditer(line):
            token = match.group(0)
            if not (_HAS_DIGIT.search(token) and _HAS_LETTER.search(token)):
                continue
            site = _Site(
                token,
                line[: match.start()],
                line[match.end() :],
                line,
                match.start(),
                match.end(),
                root,
                remotes,
            )
            rule = next((name for name, (_, applies) in _RULES.items() if applies(site)), None)
            found.append(Occurrence(path, index + 1, token, rule))
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


def _is_tree_or_blob(repo: Path, token: str) -> bool:
    done = _git(repo, ["cat-file", "-t", token])
    return done.returncode == 0 and done.stdout.strip() in {b"blob", b"tree"}


def _published(repo: Path) -> tuple[int, set[str]]:
    refs = _git_out(repo, ["for-each-ref", "--format=%(refname)", *PUBLISHED_REFS]).split()
    if not refs:
        return 0, set()
    done = _git(repo, ["rev-list", "--stdin"], b"".join(ref + b"\n" for ref in refs))
    if done.returncode != 0:
        raise GateError(f"git rev-list exited {done.returncode}")
    listed = done.stdout.decode("ascii")
    return len(refs), set(listed.split())


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
    unresolved: list[tuple[Occurrence, str]] = field(default_factory=list)
    overreach: list[Occurrence] = field(default_factory=list)

    @property
    def admitted(self) -> list[Occurrence]:
        """The occurrences no exclusion rule removed."""
        return [entry for entry in self.occurrences if entry.rule is None]

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


def sweep(repo: Path) -> SweepReport:
    """Read every tracked doc in ``repo`` and judge every citation against published history.

    Args:
        repo: A work tree.

    Returns:
        The report. On a shallow clone, or with no published ref, nothing is
        resolved - nothing can be judged.

    Raises:
        GateError: When git cannot be run or ``repo`` is not a repository.
    """
    shallow = _git_out(repo, ["rev-parse", "--is-shallow-repository"]).strip() != b"false"
    listed = _git_out(repo, ["ls-files", "-z", "--", *DOC_PATHSPECS]).decode("utf-8")
    paths = sorted(name for name in listed.split("\0") if name)
    # A remote is any configured remote AND any name refs/remotes carries, so a
    # ref fetched without a configured remote still reads as this repository's.
    remote_refs = _git_out(repo, ["for-each-ref", "--format=%(refname)", "refs/remotes"])
    remotes = frozenset(
        _git_out(repo, ["remote"]).decode("utf-8").split()
        + [ref.split("/")[2] for ref in remote_refs.decode("utf-8").split() if ref.count("/") > 1]
    )
    occurrences: list[Occurrence] = []
    for name in paths:
        target = repo / name
        if target.is_file():
            text = target.read_text(encoding="utf-8", errors="replace")
            occurrences += scan_text(text, name, repo, remotes)
    ref_count, published = (0, set()) if shallow else _published(repo)
    report = SweepReport(len(paths), occurrences, shallow, ref_count, _commit_map(repo))
    if shallow or not ref_count:
        return report
    commits = {token: commit_of(repo, token) for token in sorted({e.token for e in occurrences})}
    blobs = {
        token
        for token, commit in commits.items()
        if commit is None and _is_tree_or_blob(repo, token)
    }
    report.occurrences = occurrences = [
        Occurrence(e.path, e.line, e.token, GIT_BLOB) if e.rule is None and e.token in blobs else e
        for e in occurrences
    ]
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
    ]
    for name, sentence in EXCLUSION_RULES.items():
        count = sum(1 for entry in report.occurrences if entry.rule == name)
        out.append(f"excluded-count {name} {count} - {sentence}")
    out += [
        f"excluded {entry.rule} {entry.path}:{entry.line} {entry.token}"
        for entry in report.occurrences
        if entry.rule is not None
    ]
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
            "or an exclusion swallowed one"
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
