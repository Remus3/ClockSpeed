#!/usr/bin/env python3
"""CS-1222 - a doc naming a commit that is not published turns the gate red.

WHY. ``docs/LEDGER.md`` forbids citing a slice sha and names "A bare commit SHA"
an invalid pointer, and nothing enforced it: four tools grade a commit field's
SHAPE and never ask git, so the next unresolvable sha to land would land
silently. This gate asks git about every one.

THE INCLUSION RULE is published verbatim as :data:`INCLUSION_RULE` and printed
on every run, and it states what it does NOT admit and why.

WHAT IS RED, EXACTLY. (1) An ADMITTED token that is not a published commit and
not on the allowlist. (2) ANY other run of 7 to 40 hex characters - digit-only,
all-letter, upper- or mixed-case, or joined to a letter, digit or underscore
(``-g<hex>`` from ``git describe``, ``0x<hex>``, ``sha_<hex>``, ``<hex>_fix``) -
that names a commit this store HOLDS but that is not published. Such a run
that names no commit at all, or a published one, is NOISE and stays silent:
decimal counts and run ids, English words and constants vastly outnumber
citations in those shapes, and only a run git itself resolves is evidence of
one. A run naming an unpublished commit the store does not hold is invisible
here - the one blind spot, stated rather than hidden.

CS-1224 WIDENS WHAT IS READ AND WHAT IS STATED. (3) Every tracked file OUTSIDE
the doc pathspecs - code, config, data - is read too (:data:`CODE_PATHSPECS`),
and each 7-to-40 run in it of any shape is resolved like a not-admitted doc run:
red when it names an existing unpublished commit, silent otherwise. (4) Every
run of 5 or 6 hex characters, any case, joined to anything, in any tracked
file, is resolved the same way - git accepts an abbreviation that short. The
4-character and the 41-or-more classes are NOT JUDGED, and each run prints
every such class (:data:`NOT_JUDGED`) with its count and the measured reason,
so an empty result there is never read as a pass. A resolved-only run that
more than one commit answers is counted ``ambiguous`` and is red when any
candidate is unpublished. A tracked file is decoded as UTF-32 or UTF-16 behind
a byte-order mark (UTF-32 first, since its mark opens with UTF-16's), else as
UTF-8 with replacement; one that is absent or carries a NUL is NOT READ, every
run prints that count and each such path, and any such file makes the run
COULD NOT JUDGE - a file dropping out is never a pass - unless an unpublished
finding makes it FAIL, which outranks it and prints both. A BOM-marked file is
decoded STRICTLY (a failure is NOT READ, never replacement) and is always also
scanned as raw latin-1 bytes, the runs being the union, because
8-bit text behind a stray mark decodes as CJK with every hex run gone. All three
resolved-only populations share the blind spot above, and the overreach
control and the allowlist apply to doc tokens only.

THE RESOLVER. Every distinct run is asked ``<token>^{commit}`` in ONE ``git
cat-file --batch-check`` call - the object-name resolution ``git rev-parse
--verify -q <token>^{commit}`` performs (:func:`commit_of`, kept as the
single-token reference the arms compare against), answered for the whole tree
in one process instead of one per token: an unknown or ambiguous name answers
``missing`` or ``ambiguous`` there exactly as it fails ``--verify`` there.
Reachability is ONE ``git rev-list`` into a set. The commit a token names counts
ONLY when it is
PUBLISHED - reachable from ``HEAD``, from ``refs/remotes/origin/main`` or from
a tag, and nothing else. ``HEAD`` counts because it is the commit whose tree is
being judged: everything reachable from it ships with it, so a note citing an
earlier commit of the same push batch passes the pre-push run that precedes
the push. An object that lives only on a local side branch, in a worktree, in
the reflog or on a side branch of the remote is not reachable from any of the
three, resolves today and dies the day that branch is deleted, so it is
reported ``unpublished`` and FAILS. An
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
repository carrying ``refs/remotes/origin/main`` or a tag AND at least one
admitted citation, every one published, and no overreach. A shallow clone, a
repository with neither ref, a missing git, or a sweep that admitted nothing exits 2,
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
    exit 1   an admitted citation is not a published commit, an allowlisted
             token is one (overreach), or a not-admitted, code or short run
             names an existing unpublished commit, or an ambiguous one has an
             unpublished candidate
    exit 2   could not judge - no git, not a repository, a shallow clone, no
             origin/main and no tag, a tracked file not read, or a sweep that
             admitted nothing

stdout prints only repository-relative paths, line numbers and the tokens
themselves - never a doc line's text, and never an environment value.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
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

#: The tracked files the sweep reads as DOCS, as git pathspecs.
DOC_PATHSPECS: Final = ("*.md", "*.txt")

#: CS-1224 - every OTHER tracked file, read as CODE: each hex run in it is
#: resolved and red only when it names an existing unpublished commit. Measured
#: 2026-10-03 on this tree: 395 such files carry 442 distinct 7-to-40 runs, of
#: which 380 name no commit - fixture vectors, digests, ids - so grading code
#: like a doc would need hundreds of allowlist rows; resolving finds the
#: unpublished citations (two commits, five sites) without one.
CODE_PATHSPECS: Final = (".", *(f":(exclude){spec}" for spec in DOC_PATHSPECS))

#: The refs whose history counts as published, beside ``HEAD`` itself: the
#: remote's main line and every tag. A side branch, even a pushed one, can be
#: deleted - and its citations with it. At least one of these must exist, or the
#: gate cannot tell a published tree from a private one and refuses to judge.
PUBLISHED_REFS: Final = ("refs/remotes/origin/main", "refs/tags")

INCLUSION_RULE: Final = (
    "ADMITTED: a run of 7 to 40 lower-case hex characters carrying at least one digit and "
    "at least one letter, with no letter, digit or underscore on either side, in a tracked "
    "*.md or *.txt file. NOT ADMITTED, by design: an all-digit run, because decimal numbers "
    "(CI run ids, counts, offsets) outnumber any all-digit abbreviation and cannot be told "
    "from one; an all-letter run, because that is an English word as often as a sha; "
    "upper-case hex, because git prints every object name in lower case, so an upper-case "
    "run is a constant or an identifier and never a copied sha; and a run longer than 40, "
    "which is a sha256 and not a sha1 object name. A NOT-ADMITTED run of 7 to 40 hex "
    "characters of any case, joined to anything, is still resolved: it is red when it "
    "names an existing commit that is not published, and silent noise otherwise. In every "
    "other tracked file - code, config, data - every run of 7 to 40 hex characters is "
    "resolved the same way and is red only when it names an existing unpublished commit, "
    "because hex literals that name nothing (test vectors, digests, ids) outnumber code "
    "citations there. Every run of 5 or 6 hex characters of any case, joined to anything, "
    "in any tracked file, is resolved the same way too, and one that more than one commit "
    "answers is red when any candidate is unpublished. A tracked file is read as UTF-32 or "
    "UTF-16 behind a byte-order mark, STRICTLY - scanned both decoded and as raw bytes, "
    "the union of the two, and NOT READ when the strict decode fails, though its raw "
    "bytes are still graded - else as UTF-8 with replacement; one absent or carrying a "
    "NUL is NOT "
    "READ, its count is stated on every run, and any such file makes the run COULD NOT "
    "JUDGE, except that an unpublished finding outranks it: that run exits 1 and prints "
    "both. NOT JUDGED, stated "
    "with a count on every run: a 4-character run and a run of 41 or more - see each "
    "not-judged line for why"
)

#: CS-1224 - the width classes the gate does NOT judge, each with the reason
#: printed beside its count on every run, so an empty result there is never
#: read as a pass. Measured 2026-10-03 over every tracked file of this tree,
#: whose store held 1741 commits: 4-character runs 43994 (1079 distinct, 849
#: all-digit), of which 29 resolve to a commit and 8 to an UNPUBLISHED one;
#: runs of 41 or more 45 (30 distinct), none whose leading 40 is a commit.
#: Every 5- or 6-character run of any shape - 386 distinct, 228 all-digit - named no
#: commit at all, so judging that class cost nothing measurable and it is judged.
NOT_JUDGED: Final[dict[str, str]] = {
    "w4": (
        "measured 2026-10-03: of 1079 distinct 4-character runs, 849 all-digit, 29 named "
        "a commit and 8 an unpublished one - judging them would redden the tree on years, "
        "ports and counts that cite nothing"
    ),
    "w41+": (
        "no sha1 object name is longer than 40, so git resolves nothing here and the "
        "answer would be vacuous; measured 2026-10-03: 30 distinct such runs, none whose "
        "leading 40 characters name a commit"
    ),
}

#: Every maximal run of hex characters, either case, joined to anything.
_ANY_RUN: Final = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{7,40}(?![0-9A-Fa-f])")

#: CS-1224 - every maximal run of 5 or 6 hex characters, either case, joined to anything.
_SHORT_RUN: Final = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{5,6}(?![0-9A-Fa-f])")

#: Each not-judged width class, as the maximal hex run that measures it.
_NOT_JUDGED_RUNS: Final[dict[str, re.Pattern[str]]] = {
    "w4": re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{4}(?![0-9A-Fa-f])"),
    "w41+": re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{41,}(?![0-9A-Fa-f])"),
}

#: CS-1224 - the reason printed beside the not-read count on every run.
NOT_READ_REASON: Final = (
    "tracked files absent from the work tree, failing a strict decode behind a UTF-32 or "
    "UTF-16 byte-order mark, or carrying a NUL once decoded (else UTF-8 with "
    "replacement), are binary or "
    "missing to this reader; any such file makes the run COULD NOT JUDGE, never a pass, "
    "unless an unpublished finding makes it FAIL"
)

#: The byte-order marks that make a tracked file read as UTF-32, tested first.
_UTF32_BOMS: Final = (b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")

#: The byte-order marks that make a tracked file read as UTF-16.
_UTF16_BOMS: Final = (b"\xff\xfe", b"\xfe\xff")

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


def scan_not_admitted(text: str, path: str = "") -> list[Occurrence]:
    """Every hex run of 7 to 40 characters the inclusion rule does NOT admit.

    Args:
        text: One file's text.
        path: The name the occurrences carry.

    Returns:
        Each run, in text order, with ``rule`` None - these are resolved, never
        allowlisted, and fail only when they name an existing unpublished commit.
    """
    runs: list[Occurrence] = []
    for index, line in enumerate(text.splitlines()):
        admitted = {
            match.span()
            for match in _TOKEN.finditer(line)
            if _HAS_DIGIT.search(match.group(0)) and _HAS_LETTER.search(match.group(0))
        }
        runs += [
            Occurrence(path, index + 1, match.group(0), None)
            for match in _ANY_RUN.finditer(line)
            if match.span() not in admitted
        ]
    return runs


def scan_code(text: str, path: str = "") -> list[Occurrence]:
    """Every hex run of 7 to 40 characters in a CODE file, any shape - CS-1224.

    Args:
        text: One file's text.
        path: The name the occurrences carry.

    Returns:
        Each run, in text order, with ``rule`` None - resolved, never allowlisted,
        red only when it names an existing unpublished commit.
    """
    return [
        Occurrence(path, index + 1, match.group(0), None)
        for index, line in enumerate(text.splitlines())
        for match in _ANY_RUN.finditer(line)
    ]


def scan_short(text: str, path: str = "") -> list[Occurrence]:
    """Every maximal 5- or 6-character hex run, any case, joined to anything.

    Args:
        text: One file's text.
        path: The name the occurrences carry.

    Returns:
        Each run, in text order, with ``rule`` None - resolved like a not-admitted
        run, red only when it names an existing unpublished commit.
    """
    return [
        Occurrence(path, index + 1, match.group(0), None)
        for index, line in enumerate(text.splitlines())
        for match in _SHORT_RUN.finditer(line)
    ]


def count_not_judged(text: str) -> dict[str, int]:
    """How many runs of each :data:`NOT_JUDGED` width class ``text`` carries."""
    return {name: len(pattern.findall(text)) for name, pattern in _NOT_JUDGED_RUNS.items()}


def tracked_views(raw: bytes) -> tuple[list[str], bool]:
    """The views of a tracked file that are scanned, and whether it was READ - CS-1224.

    A UTF-32 byte-order mark is tested FIRST, because the little-endian one
    opens with the UTF-16 one; then UTF-16. A BOM-marked file is ALWAYS scanned
    as its raw bytes read as latin-1, which finds an ASCII citation in 8-bit
    text behind a stray mark - such text decodes cleanly as UTF-16 into CJK,
    where every hex run vanishes. Its mark's codec is then tried STRICTLY: a
    decode that fails, or text carrying a NUL, means the file is NOT READ -
    never replacement, which turns a UTF-16LE file opening with U+0000 (whose
    bytes are the UTF-32LE mark) into U+FFFD with no run and no NUL, a silent
    pass. A strict decode with no NUL is scanned too, the runs being the union.
    Anything else is strict UTF-8 (a UTF-8 BOM is dropped), falling back to
    UTF-8 with replacement, so one stray Latin-1 byte still leaves the rest
    graded; text carrying a NUL there is not read and not scanned.
    """
    for boms, codec in ((_UTF32_BOMS, "utf-32"), (_UTF16_BOMS, "utf-16")):
        if raw.startswith(boms):
            byte_view = raw.decode("latin-1")
            try:
                text = raw.decode(codec)
            except UnicodeDecodeError:
                return [byte_view], False
            return ([byte_view], False) if "\0" in text else ([text, byte_view], True)
    plain = decode_tracked(raw)
    return ([], False) if plain is None else ([plain], True)


def _union(found: Iterable[list[Occurrence]]) -> list[Occurrence]:
    """Every occurrence across a file's views, each (line, token, rule) once, in order."""
    merged: dict[tuple[int, str, str | None], Occurrence] = {}
    for entries in found:
        for entry in entries:
            merged.setdefault((entry.line, entry.token, entry.rule), entry)
    return list(merged.values())


def decode_tracked(raw: bytes) -> str | None:
    """A non-BOM tracked file's UTF-8 text, or None when it carries a NUL."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
    return None if "\0" in text else text


def resolve_many(repo: Path, tokens: Sequence[str]) -> dict[str, str | None]:
    """Resolve many runs to commits in ONE ``git cat-file --batch-check`` call.

    ``<run>^{commit}`` is the same question ``rev-parse --verify`` answers; a
    batch keeps thousands of decimal runs from costing thousands of processes.
    Upper-case runs are asked in lower case, which names the same object.
    """
    return resolve_batch(repo, tokens)[0]


def _batch_check(repo: Path, names: Sequence[str]) -> list[list[str]]:
    """Ask ``git cat-file --batch-check`` about each name; one answer's fields per name."""
    data = "".join(f"{name}\n" for name in names).encode("ascii")
    done = _git(repo, ["cat-file", "--batch-check"], data)
    if done.returncode != 0:
        raise GateError(f"git cat-file exited {done.returncode}")
    answers = done.stdout.decode("ascii", errors="replace").splitlines()
    if len(answers) != len(names):
        raise GateError("git cat-file answered a different number of lines")
    return [answer.split() for answer in answers]


def _commits_of(repo: Path, tokens: Sequence[str]) -> dict[str, str | None]:
    names = [f"{token.lower()}^{{commit}}" for token in tokens]
    return {
        token: fields[0] if fields[1:2] == ["commit"] else None
        for token, fields in zip(tokens, _batch_check(repo, names), strict=True)
    }


def resolve_batch(
    repo: Path, tokens: Sequence[str]
) -> tuple[dict[str, str | None], dict[str, set[str]]]:
    """:func:`resolve_many`, plus every run more than one COMMIT answers - CS-1224.

    ``<run>^{commit}`` answers ``missing`` for a run two commits share, exactly
    as for an absent one, so each missing run is asked again bare: an
    ``ambiguous`` answer there is listed with ``rev-parse --disambiguate`` and
    peeled, and the run is ambiguous when ANY commit remains - a commit and a
    tag object at it share a prefix and peel to one commit, which is still
    ambiguous to git and is still red when that commit is unpublished.

    Returns:
        Each token mapped to its one commit or None, and each commit-ambiguous
        token mapped to the commits that answer it.
    """
    if not tokens:
        return {}, {}
    resolved = _commits_of(repo, tokens)
    missing = [token for token in tokens if resolved[token] is None]
    ambiguous: dict[str, set[str]] = {}
    if missing:
        bare = _batch_check(repo, [token.lower() for token in missing])
        for token, fields in zip(missing, bare, strict=True):
            if fields[1:2] == ["ambiguous"] and (found := candidate_commits(repo, token)):
                ambiguous[token] = found
    return resolved, ambiguous


def candidate_commits(repo: Path, token: str) -> set[str]:
    """Every commit an ambiguous ``token`` could name: ``rev-parse --disambiguate``, peeled."""
    listed = _git_out(repo, ["rev-parse", f"--disambiguate={token.lower()}"]).decode("ascii")
    objects = sorted(set(listed.split()))
    return {commit for commit in _commits_of(repo, objects).values() if commit is not None}


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
    roots = [b"HEAD", *refs]
    done = _git(repo, ["rev-list", "--stdin"], b"".join(ref + b"\n" for ref in roots))
    if done.returncode != 0:
        raise GateError(f"git rev-list exited {done.returncode}")
    return len(refs), set(done.stdout.decode("ascii").split())


def _tracked(repo: Path, pathspecs: Sequence[str]) -> list[str]:
    listed = _git_out(repo, ["ls-files", "-z", "--", *pathspecs]).decode("utf-8")
    return sorted(name for name in listed.split("\0") if name)


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
        published_refs: How many refs under :data:`PUBLISHED_REFS` exist -
            ``HEAD`` is always a root as well, and is not counted here.
        rewritten: The OLD shas a filter-repo commit-map names, or None when
            no map is present - the discriminator is unavailable.
        allowlist: The ``token -> class`` table this run used.
        unresolved: Each admitted occurrence that is not a published commit,
            with its state - ``unpublished``, ``rewritten-away`` or
            ``never-resolved``.
        overreach: Each EXCLUDED occurrence whose token IS a published commit.
        not_admitted: Every hex run the inclusion rule does not admit.
        not_admitted_unpublished: Each of those that names an EXISTING commit
            that is not published - red, like an unresolved citation.
        code_files: How many tracked files outside :data:`DOC_PATHSPECS` were read.
        code_runs: Every hex run of 7 to 40 in those files, resolved only.
        short_runs: Every judged 5- or 6-character run, docs and code, resolved only.
        not_judged: Each :data:`NOT_JUDGED` class mapped to its run count.
        not_read: Tracked files :func:`decode_tracked` could not judge - any
            one makes the run COULD NOT JUDGE.
        ambiguous: Resolved-only runs more than one commit answers.
        ambiguous_unpublished: Those of them with an unpublished candidate - red.

    ``not_admitted_unpublished`` carries every red run of all three resolved-only
    populations - not-admitted doc runs, code runs and short runs.
    """

    files: int
    occurrences: list[Occurrence]
    shallow: bool
    published_refs: int
    rewritten: list[str] | None
    allowlist: Mapping[str, str]
    unresolved: list[tuple[Occurrence, str]] = field(default_factory=list)
    overreach: list[Occurrence] = field(default_factory=list)
    not_admitted: list[Occurrence] = field(default_factory=list)
    not_admitted_unpublished: list[Occurrence] = field(default_factory=list)
    code_files: int = 0
    code_runs: list[Occurrence] = field(default_factory=list)
    short_runs: list[Occurrence] = field(default_factory=list)
    not_judged: dict[str, int] = field(default_factory=lambda: dict.fromkeys(NOT_JUDGED, 0))
    not_read: list[str] = field(default_factory=list)
    ambiguous: list[Occurrence] = field(default_factory=list)
    ambiguous_unpublished: list[Occurrence] = field(default_factory=list)

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
        """Exit 2 when nothing can be judged, 1 on a failure, else 0.

        A not-read file is exit 2 only when nothing else failed: an unpublished
        finding outranks it, and both are printed.
        """
        if self.shallow or not self.published_refs or not self.admitted:
            return EXIT_COULD_NOT_JUDGE
        failed = (
            self.unresolved
            or self.overreach
            or self.not_admitted_unpublished
            or self.ambiguous_unpublished
        )
        if failed:
            return EXIT_UNRESOLVED
        return EXIT_COULD_NOT_JUDGE if self.not_read else EXIT_CLEAN


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
        The report. On a shallow clone, or with neither origin/main nor a
        tag, nothing is resolved - nothing can be judged.

    Raises:
        GateError: When git cannot be run or ``repo`` is not a repository.
    """
    table = allowlist_map() if allowlist is None else allowlist
    shallow = _git_out(repo, ["rev-parse", "--is-shallow-repository"]).strip() != b"false"
    paths = _tracked(repo, DOC_PATHSPECS)
    code_paths = _tracked(repo, CODE_PATHSPECS)
    code_set = set(code_paths)
    occurrences: list[Occurrence] = []
    not_admitted: list[Occurrence] = []
    code_runs: list[Occurrence] = []
    short_runs: list[Occurrence] = []
    not_judged = dict.fromkeys(NOT_JUDGED, 0)
    not_read: list[str] = []
    for name in [*paths, *code_paths]:
        target = repo / name
        views, read = tracked_views(target.read_bytes()) if target.is_file() else ([], False)
        if not read:
            not_read.append(name)
        if name in code_set:
            code_runs += _union(scan_code(text, name) for text in views)
        else:
            occurrences += _union(scan_text(text, name, table) for text in views)
            not_admitted += _union(scan_not_admitted(text, name) for text in views)
        short_runs += _union(scan_short(text, name) for text in views)
        for text in views:
            for klass, count in count_not_judged(text).items():
                not_judged[klass] += count
    ref_count, published = (0, set()) if shallow else _published(repo)
    report = SweepReport(len(paths), occurrences, shallow, ref_count, _commit_map(repo), table)
    report.not_admitted = not_admitted
    report.code_files = len(code_paths)
    report.code_runs = code_runs
    report.short_runs = short_runs
    report.not_judged = not_judged
    report.not_read = not_read
    if shallow or not ref_count:
        return report
    resolved_only = [*not_admitted, *code_runs, *short_runs]
    every = {entry.token for entry in resolved_only} | {entry.token for entry in occurrences}
    runs, ambiguous = resolve_batch(repo, sorted(every))
    report.not_admitted_unpublished = [
        entry
        for entry in resolved_only
        if (commit := runs[entry.token]) is not None and commit not in published
    ]
    report.ambiguous = [entry for entry in resolved_only if entry.token in ambiguous]
    unpublished_candidates = {token for token, commits in ambiguous.items() if commits - published}
    report.ambiguous_unpublished = [
        entry for entry in report.ambiguous if entry.token in unpublished_candidates
    ]
    for entry in occurrences:
        commit = runs[entry.token]
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
        f"code files {report.code_files}; code runs {len(report.code_runs)}; short runs "
        f"{len(report.short_runs)}; not-admitted runs {len(report.not_admitted)}; all "
        f"resolved too; naming an unpublished commit {len(report.not_admitted_unpublished)}",
        f"allowlist rows {len(report.allowlist)}; unused {len(report.unused)} - exact tokens "
        "only, never a shape",
    ]
    out += [
        f"not-judged {name} {report.not_judged.get(name, 0)} - {reason}"
        for name, reason in NOT_JUDGED.items()
    ]
    out.append(f"not-read {len(report.not_read)} - {NOT_READ_REASON}")
    out.append(
        f"ambiguous {len(report.ambiguous)} - resolved-only runs more than one commit "
        f"answers; red when any candidate is unpublished: {len(report.ambiguous_unpublished)}"
    )
    out += [f"not-read-file {name}" for name in report.not_read]
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
            "resolver full - <sha>^{commit} in one git cat-file --batch-check, counted only when "
            "reachable from HEAD, refs/remotes/origin/main or a tag "
            f"({report.published_refs} refs beside HEAD)"
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
    out += [
        f"unpublished-not-admitted {entry.path}:{entry.line} {entry.token} names an "
        "existing commit that is not published"
        for entry in report.not_admitted_unpublished
    ]
    out += [
        f"ambiguous-unpublished {entry.path}:{entry.line} {entry.token} is answered by "
        "more than one commit, at least one not published"
        for entry in report.ambiguous_unpublished
    ]
    verdict = report.verdict()
    if verdict == EXIT_CLEAN:
        out.append("sha_citation_gate: PASS - every admitted citation is a published commit")
    elif verdict == EXIT_UNRESOLVED:
        out.append(
            "sha_citation_gate: FAIL - a citation is not a published commit, an "
            "allowlisted token is one, or a not-admitted, code or short run names an "
            "unpublished commit"
        )
        if report.not_read:
            out.append(f"sha_citation_gate: ALSO COULD NOT JUDGE - {_not_read_reason(report)}")
    else:
        if report.shallow:
            reason = "a shallow clone"
        elif not report.published_refs:
            reason = "no origin/main and no tag"
        elif not report.admitted:
            reason = "the sweep admitted nothing"
        else:
            reason = _not_read_reason(report)
        out.append(f"sha_citation_gate: COULD NOT JUDGE - {reason}, which is not a pass")
    return out


def _not_read_reason(report: SweepReport) -> str:
    count = len(report.not_read)
    return f"{count} tracked file{'' if count == 1 else 's'} not read"


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
