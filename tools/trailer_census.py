#!/usr/bin/env python3
"""CS-1183 - the trailer-shaped census, as one command the flip and CS-704 both call.

THE DEFINITION IS NOT RESTATED HERE. It lives in ONE place, the paragraph headed
THE TRAILER-SHAPED CENSUS in ``docs/OPERATIONS.md`` section 12.6, and every other file
points at it. :func:`is_trailer_line` is that paragraph as code and nothing more;
its shape is the one ``.githooks/commit-msg`` refuses, because git's own trailer
parser finds the separator FIRST and trims the token AFTERWARDS.

WHY A CENSUS AND NOT A SUBSTRING SEARCH. A plain search for the key also matches
PROSE ABOUT THE RULE - ``docs/GATED.md`` CS-G03 measured one extra hit that way,
a commit message discussing the trailer. The colon separates the two.

THE CLI CONTRACT, published for ``tools/flip_checks.py`` (the S1/S8 executor) and
for CS-704, which code against it:

    python tools/trailer_census.py [--repo DIR] [--allow-empty] REV

    REV      anything ``git rev-list`` accepts as ONE argument - a ref, a SHA,
             or a range ``A..B``. An argument starting with ``-`` is refused, so
             an option cannot be smuggled in as a revision.
    exit 0   the walk found no trailer-shaped line
    exit 1   it found at least one
    exit 2   it could not run - no git, not a repository, a shallow or grafted
             history, an unresolvable or option-shaped REV, a stream it could
             not parse, or a walk of ZERO commits without ``--allow-empty``,
             because a census of nothing satisfies every zero and reads
             exactly like a clean one

    stdout carries ONE count line, ``trailer_census: commits walked N; trailer
    lines H; commits with a hit C``, then one ``hit <sha>`` line per offending
    commit. NEVER A MESSAGE BYTE: the value a trailer carries is an identity,
    and the census exists to find where one sits, not to copy it into a log.

STRIPPABILITY, for the S1 seventh axis. The CS-1180 paragraph beside the census
aborts S1 unless every hit is a line S7a's strip removes: the final body line of
a NON-merge commit's message, preceded by a blank line, one per commit.
:attr:`CommitCensus.strippable` answers exactly that, and it is judged on the
RAW message - the bytes after the header's blank line in ``git cat-file
commit`` - never on a ``git log`` format, which normalises whitespace.

THE MESSAGE IS READ FROM THE OBJECT STORE with ``git cat-file --batch``, in one
bounded call, and every object is checked to be the commit that was asked for:
a reader that quietly dropped or misread one would report a census that looks
exactly like a clean one.

THE OBJECTS READ ARE THE RAW ONES, AND A CUT HISTORY IS REFUSED (CS-701). A
``refs/replace/`` ref swaps one object for another in every read that honours
it - a clean commit for one carrying a trailer, or a ``--graft`` that skips it -
so every git call here runs with replace objects OFF. A shallow file or a graft
ends the walk early, and no flag switches that off, so a shallow or grafted
repository is refused by name (exit 2) rather than walked. This mirrors
``raw_object_env`` and ``refuse_cut_history`` in ``tools/flip_checks.py``, kept
here rather than imported because ``flip_checks`` imports this module. The CI
step that runs the census checks out with ``fetch-depth: 0``, which is not
shallow, and ``tests/test_trailer_routes.py`` pins that depth.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# `tools` carries no __init__.py, so the sibling resolver is imported under its
# BARE name, the way tools/doc_sweep.py and tools/provenance_stamp.py do it.
_TOOLS_DIR: Final = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

EXIT_CLEAN: Final = 0
EXIT_HITS: Final = 1
EXIT_COULD_NOT_RUN: Final = 2

#: The trailer key, WITHOUT the colon - the colon is the separator, not part of
#: the token, which is why ``Co-authored-by : x`` is a trailer to git.
TRAILER_KEY: Final = "co-authored-by"

#: Seconds one git call may take. The walk reads every commit object reachable
#: from REV in one call, so this sits well above a single object's cost.
GIT_TIMEOUT: Final = 300

#: Fields in a ``git cat-file --batch`` header: object, type and size.
BATCH_HEADER_FIELDS: Final = 3

#: The line a commit object uses to name one parent.
PARENT_PREFIX: Final = b"parent "

#: A message whose final line is its only trailer needs a subject, a blank
#: separator and the trailer at the least - so the trailer's index is at least 2.
MIN_STRIPPABLE_INDEX: Final = 2


class CensusError(Exception):
    """The census could not be taken. The reason is fixed text, never a message byte."""

    def __init__(self, reason: str) -> None:
        """Keep ``reason`` as the one field the CLI prints."""
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class CommitCensus:
    """One walked commit: its name, its parent count and where its trailers sit.

    Attributes:
        sha: The commit's full object name.
        parents: How many parents the commit object names.
        hit_lines: Zero-based indices of the message lines that are trailer
            shaped. Indices, never the lines themselves.
        strippable: Whether S7a's strip removes every hit - see the module
            docstring. True for a commit with no hit, which has nothing to strip.
    """

    sha: str
    parents: int
    hit_lines: tuple[int, ...]
    strippable: bool


def is_trailer_line(line: bytes) -> bool:
    """Whether one message line is trailer shaped, per the census definition.

    Args:
        line: One line of a raw commit message, without its terminating LF.

    Returns:
        True when the line carries a colon and the token before the first colon,
        trailing whitespace trimmed, folds case-insensitively to the key. A line
        whose token begins with whitespace is never a trailer to git, and the
        comparison refuses it for free: the leading whitespace survives the trim.
    """
    token, separator, _rest = line.partition(b":")
    if not separator:
        return False
    return token.decode("utf-8", errors="replace").rstrip().casefold() == TRAILER_KEY


def message_lines(message: bytes) -> list[bytes]:
    """Split a raw message into lines, dropping only the terminating LF.

    Args:
        message: The raw message bytes.

    Returns:
        The lines. A message ending in LF does not gain an empty final line.
    """
    lines = message.split(b"\n")
    if len(lines) > 1 and lines[-1] == b"":
        lines.pop()
    return lines


def is_strippable(lines: list[bytes], hits: tuple[int, ...], parents: int) -> bool:
    """Whether S7a's two-line strip removes every hit in one message.

    Args:
        lines: The message lines, from :func:`message_lines`.
        hits: The trailer-shaped line indices.
        parents: The commit's parent count.

    Returns:
        True for a commit with no hit. Otherwise True only for a non-merge
        commit with exactly one hit, sitting on the final line, at index 2 or
        later, with an EMPTY line immediately before it.
    """
    if not hits:
        return True
    if parents > 1 or len(hits) != 1:
        return False
    (index,) = hits
    return index == len(lines) - 1 and index >= MIN_STRIPPABLE_INDEX and lines[index - 1] == b""


def census_of(sha: str, raw: bytes) -> CommitCensus:
    """Take the census of one raw commit object.

    Args:
        sha: The commit's object name.
        raw: The object's bytes as ``git cat-file`` returns them.

    Returns:
        The commit's census.

    Raises:
        CensusError: When the object carries no header-ending blank line.
    """
    header, separator, message = raw.partition(b"\n\n")
    if not separator:
        raise CensusError(f"commit {sha} has no header-ending blank line")
    parents = sum(1 for line in header.split(b"\n") if line.startswith(PARENT_PREFIX))
    lines = message_lines(message)
    hits = tuple(index for index, line in enumerate(lines) if is_trailer_line(line))
    return CommitCensus(sha, parents, hits, is_strippable(lines, hits, parents))


def raw_object_env() -> dict[str, str]:
    """This environment with replace objects OFF, for every git call the census makes.

    Returns:
        A copy of ``os.environ`` with ``GIT_NO_REPLACE_OBJECTS`` set, so the walk
        and the read see the raw objects in the store. Grafts and a shallow file
        are not switched off by this; :func:`refuse_cut_history` refuses them.
    """
    env = dict(os.environ)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    return env


def refuse_cut_history(repo: Path) -> None:
    """Refuse a repository whose history is cut by a shallow file or by grafts.

    Either one ends the walk early, so a commit behind the cut is never read
    and a census over it reads exactly like a clean one.

    Args:
        repo: The repository.

    Raises:
        CensusError: Naming which of the two cuts was found.
    """
    shallow = _git(repo, ["rev-parse", "--is-shallow-repository"]).strip()
    if shallow != b"false":
        raise CensusError("the repository is shallow")
    grafts = _git(repo, ["rev-parse", "--git-path", "info/grafts"]).decode("utf-8", "replace")
    if (repo / grafts.strip()).exists():
        raise CensusError("the repository has grafts")


def _git(repo: Path, args: list[str], data: bytes | None = None) -> bytes:
    """Run one git command in ``repo``, replace objects off, and return its stdout.

    Args:
        repo: The repository to run in.
        args: The subcommand and its arguments, without git itself.
        data: Bytes for stdin, if any.

    Returns:
        Raw stdout.

    Raises:
        CensusError: When git is not on PATH, cannot be run, times out or exits
            non-zero. The reason names the subcommand only - never an argument,
            which could carry a path from the caller.
    """
    git = resolve_tool("git")
    if git is None:
        raise CensusError("git is not on PATH")
    try:
        completed = subprocess.run(
            [git, *args],
            cwd=repo,
            input=data,
            env=raw_object_env(),
            capture_output=True,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CensusError(f"git {args[0]} could not be run: {type(exc).__name__}") from None
    if completed.returncode != 0:
        raise CensusError(f"git {args[0]} exited {completed.returncode}")
    return completed.stdout


def read_commits(repo: Path, shas: list[str]) -> dict[str, bytes]:
    """Read every named commit object in one ``git cat-file --batch`` call.

    Args:
        repo: The repository.
        shas: Commit object names.

    Returns:
        Each sha mapped to its raw object bytes.

    Raises:
        CensusError: When the stream answers with an unparseable header, an
            object that is not a commit, a sha that was not asked for, or fewer
            objects than were asked for.
    """
    if not shas:
        return {}
    stream = _git(repo, ["cat-file", "--batch"], ("\n".join(shas) + "\n").encode("ascii"))
    objects: dict[str, bytes] = {}
    offset = 0
    for sha in shas:
        end = stream.find(b"\n", offset)
        header = stream[offset:end].decode("ascii", errors="replace").split()
        if end < 0 or len(header) != BATCH_HEADER_FIELDS or header[1] != "commit":
            raise CensusError(f"git cat-file answered an unexpected header for {sha}")
        if header[0] != sha:
            raise CensusError(f"git cat-file answered another object for {sha}")
        size = int(header[2])
        start = end + 1
        objects[sha] = stream[start : start + size]
        offset = start + size + 1
        if offset > len(stream):
            raise CensusError(f"git cat-file ended inside {sha}")
    return objects


def walk(repo: Path, rev: str) -> list[CommitCensus]:
    """Take the census of every commit ``git rev-list REV`` names.

    Args:
        repo: The repository to walk.
        rev: One ``git rev-list`` argument - a ref, a SHA or a range.

    Returns:
        One census per walked commit, in ``git rev-list`` order.

    Raises:
        CensusError: When REV is empty or option shaped, the history is cut by
            a shallow file or grafts, or the walk or the read could not be taken.
    """
    if not rev or rev.startswith("-"):
        raise CensusError("REV must be a revision, not empty and not an option")
    refuse_cut_history(repo)
    listed = _git(repo, ["rev-list", "--end-of-options", rev]).decode("ascii", errors="replace")
    shas = [line.strip() for line in listed.splitlines() if line.strip()]
    objects = read_commits(repo, shas)
    return [census_of(sha, objects[sha]) for sha in shas]


def main(argv: list[str] | None = None) -> int:
    """Run the census and print its counts and offending SHAs.

    Args:
        argv: Arguments, without the program name; ``sys.argv`` when None.

    Returns:
        0 no hit, 1 hits, 2 could not run.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("rev", help="one git rev-list argument: a ref, a SHA or a range")
    parser.add_argument(
        "--repo", type=Path, default=_TOOLS_DIR.parent, help="the repository to walk"
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="exit 0 rather than 2 when the walk names no commit",
    )
    args = parser.parse_args(argv)
    try:
        walked = walk(args.repo, args.rev)
    except CensusError as exc:
        print(f"trailer_census: could not run - {exc.reason}", file=sys.stderr)
        return EXIT_COULD_NOT_RUN
    if not walked and not args.allow_empty:
        print("trailer_census: could not run - the walk named no commit", file=sys.stderr)
        return EXIT_COULD_NOT_RUN
    hit = [entry for entry in walked if entry.hit_lines]
    lines = sum(len(entry.hit_lines) for entry in walked)
    print(
        f"trailer_census: commits walked {len(walked)}; trailer lines {lines}; "
        f"commits with a hit {len(hit)}"
    )
    for entry in hit:
        print(f"hit {entry.sha}")
    return EXIT_HITS if hit else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
