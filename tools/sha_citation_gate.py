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
finding makes it FAIL, which outranks it and prints both. The one exception is a
not-read file whose path AND SHA-256 match a row of :data:`KNOWN_BINARY_FILE`: it
is counted known-binary and named instead (CS-1292). Either way a not-read file's
raw bytes are still graded as latin-1, as stored and again with every NUL removed,
so UTF-16 text without a byte-order mark and a run split by NULs are joined and
seen. A COMPRESSED citation is no hex run in either view and is not seen; the pin
row's review is the only control for it. Every path the index OR ``HEAD``'s tree
holds is listed (:func:`_tracked`) - a committed path ``git rm`` or ``git mv`` dropped
from the index is still published by ``HEAD`` - and is read from the work tree
AND from each of its index and ``HEAD`` blobs that differs (:func:`_versions`), the
runs being the union, and a pin admits the path only when every unread version
matches it - a staged or committed blob, a case-variant path a case-insensitive
disk opens as its sibling, or a symlink entry's link text is judged by its own
bytes, never by what the path opens on disk. A gitlink's path holding a plain file
on disk is read as that file, and each path itself and each commit a gitlink names
is graded like a code run, at line 0 (:func:`scan_entry`). Only ``HEAD``'s tree is
read: a citation committed and removed again in a commit BEHIND ``HEAD`` is published
by the push and not seen here - a stated residual. A BOM-marked file is
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
Reachability is ONE ``git rev-list`` into a set. Every git call runs with git's
local views of history OFF (:func:`_env`): no replace ref and no grafts file is
honoured, because a push sends neither (CS-1292). The commit a token names counts
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

CS-700 - THE HISTORICAL SET, SO THE GATE SURVIVES THE S7a REWRITE. S7a
replays every commit of ``main`` under one identity, so every sha the tree
cites stops resolving at once. :data:`HISTORICAL_FILE` is a GENERATED tracked
file listing every token in tracked text that resolved to a published commit
when it was generated - tokens only, never an old-to-new pair - plus one
WITNESS pair the tree reads its own state from: ``pre`` (a commit of the
history S7a rewrites) and ``post`` (its S7a image). PRE, ``pre`` published and
``post`` not: every listed token must name a published commit
(``historical-stale`` otherwise). POST, the reverse: no listed token may name a
published commit (``historical-collision`` - a new commit answering an old
citation is no citation), and a listed token that is absent or names an
unpublished commit is HISTORICAL and passes; an allowlist row naming ``post``
or an :data:`S7A_IMAGE_ROWS` token is not overreach there. Both or neither
witness published: COULD NOT JUDGE. A token NOT on the list is judged exactly
as before, so an old sha nobody listed stays red. With the file absent the
gate is exactly the pre-CS-700 gate. The file itself is not swept as code:
every token in it is judged by the arms above. THE SET IS PINNED BY THE GATE:
its SHA-256 is :data:`HISTORICAL_SHA256` and its witness pair must equal
:data:`WITNESS`, both checked on every run in every state, and a set breaking
either is a FAILURE naming the file (``historical-digest-mismatch``,
``historical-witness-mismatch``) - so a token smuggled into the set by hand,
or a swapped witness, launders nothing. The set's bytes ride through S7a
unchanged, so the pin does too.

CLI::

    python tools/sha_citation_gate.py [--repo DIR]
    python tools/sha_citation_gate.py --emit-historical [--repo DIR]
    python tools/sha_citation_gate.py --flip-readiness [--repo DIR]

    exit 0   every admitted citation is a published commit, no allowlisted
             token is one, and at least one citation was admitted
    exit 1   an admitted citation is not a published commit, an allowlisted
             token is one (overreach), or a not-admitted, code or short run
             names an existing unpublished commit, or an ambiguous one has an
             unpublished candidate, a historical-stale or
             historical-collision token, or a set breaking a pin
    exit 2   could not judge - no git, not a repository, a shallow clone, no
             origin/main and no tag, a tracked file not read, a sweep that
             admitted nothing, or a historical set whose witnesses are both or
             neither published, or that does not parse

``--emit-historical`` regenerates the set, in the PRE state only (exit 2
otherwise, writing nothing), with :data:`WITNESS`, and pins its SHA-256 into
this gate's own source - refusing, exit 2, a tree whose gate is not this file.
``--flip-readiness`` exits 0 only in the PRE state with no listed token stale
and no token in tracked text naming a published commit outside the set.

stdout prints only repository-relative paths, line numbers and the tokens
themselves - never a doc line's text, and never an environment value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
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

#: CS-700 - this gate, repository-relative: the file whose pin names the set.
_GATE_PATH: Final = "tools/sha_citation_gate.py"

#: CS-700 - the generated historical set, repository-relative.
HISTORICAL_FILE: Final = "tools/sha_citation_historical.json"

#: CS-700 - this tree's witness pair: ``c6f3687`` and its S7a image, the pair the
#: S7a CS-704 IMAGE control pins. Used by ``--emit-historical`` when the file
#: does not exist yet; afterwards the file's own witness is read.
WITNESS: Final = (
    "c6f36874194aeed450c6d75a93be883f72c8f45e",
    "b7b4a2c4b71c942bb759aa2b4f3b9ba906ddc1ec",
)

#: CS-700 - allowlist rows that name an S7a IMAGE: unpublished in the PRE state,
#: published by design in the POST state, so not overreach there. ``389fe4a`` is
#: the rehearsal's output tip - the image of ``69d44c5``, which the real rewrite
#: reproduces byte for byte.
S7A_IMAGE_ROWS: Final = frozenset({"389fe4a", WITNESS[1]})

#: CS-700 - the SHA-256 of :data:`HISTORICAL_FILE`'s exact bytes, PINNED here so
#: the set cannot be edited by hand: a token smuggled into it would launder a
#: citation in the POST state. Written ONLY by ``--emit-historical``, in the PRE
#: state, into the gate that judges the tree; checked on every run in every
#: state. The set's bytes do not change across S7a, so the pin survives it.
HISTORICAL_SHA256: Final = "61dd059b3d991121ab120d33f1bd11fa0ab017f21f0aa7504503f3fd818bc6b7"

#: The one source line :data:`HISTORICAL_SHA256` lives on - ``--emit-historical``
#: rewrites exactly this line and refuses a source carrying it other than once.
_PIN_LINE: Final = re.compile(r'^HISTORICAL_SHA256: Final = "[0-9a-f]{64}"$', re.MULTILINE)

#: CS-1224 - every OTHER tracked file, read as CODE: each hex run in it is
#: resolved and red only when it names an existing unpublished commit. Measured
#: 2026-10-03 on this tree: 395 such files carry 442 distinct 7-to-40 runs, of
#: which 380 name no commit - fixture vectors, digests, ids - so grading code
#: like a doc would need hundreds of allowlist rows; resolving finds the
#: unpublished citations (two commits, five sites) without one. CS-700 - the
#: historical set is excluded: every token in it is judged by the historical arms.
CODE_PATHSPECS: Final = (
    ".",
    *(f":(exclude){spec}" for spec in DOC_PATHSPECS),
    f":(exclude){HISTORICAL_FILE}",
)

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
    "answers is red when any candidate is unpublished. Each path the index or HEAD's tree "
    "holds - one git rm or git mv dropped from the index included - is read from the "
    "work tree and from every index and HEAD blob of it that differs, the union judged; "
    "the path itself, and the commit a gitlink there names, is resolved like a code run. "
    "A tracked file is read as UTF-32 or "
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
    "tracked files the index holds as a blob but absent from the work tree, or whose "
    "work-tree bytes or any differing "
    "index and HEAD blob fail a strict decode behind a UTF-32 or "
    "UTF-16 byte-order mark, or carry a NUL once decoded (else UTF-8 with "
    "replacement), are binary or "
    "missing to this reader; any such file makes the run COULD NOT JUDGE, never a pass, "
    "unless an unpublished finding makes it FAIL"
)

#: CS-1292 - the HASH-PINNED allowlist of tracked binaries, repository-relative:
#: a JSON object mapping each reviewed binary's path to the SHA-256 of its exact
#: bytes. A not-read file whose path AND hash match a row is counted KNOWN BINARY
#: and named on every run; a binary off the list, or whose bytes have drifted from
#: its pin, stays NOT READ and the run stays COULD NOT JUDGE. A pin never stops a
#: file's raw bytes being graded. An extension-and-magic test was refuted: PNG
#: magic, a NUL, then text citing an unpublished commit, passed it with exit 0.
KNOWN_BINARY_FILE: Final = "tools/sha_citation_binaries.json"

#: One pinned digest: 64 lower-case hex characters.
_PIN_DIGEST: Final = re.compile(r"[0-9a-f]{64}")

#: CS-1292 - the reason printed beside the known-binary count on every run.
KNOWN_BINARY_REASON: Final = (
    f"tracked files the reader could not read whose path AND SHA-256 match a row of "
    f"{KNOWN_BINARY_FILE} - reviewed binaries - in the work tree and in every differing "
    "index and HEAD blob, so they are counted and named, never COULD NOT JUDGE; their raw "
    "bytes are still graded, as stored and with every NUL removed, but a compressed "
    "citation inside one is not seen, and the pin row's review is the only control for "
    "it; any other unreadable file stays not-read"
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
    AllowRow("a0e0b461487f82a18", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a11badacdf15b8cb4", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a19a1101efff97773", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a1b08f9553779e024", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a1ca6574c0fe3231a", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a2b6051f", _A, "CS-1295 review findings F007, a worktree id prefix"),
    AllowRow("a2b6051f5e76ede83", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a301eedf9a4d13fae", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a3040e24c9008c13d", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a4680c300742bd2e8", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a47d3ed3ae73c739f", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a50232a210328da57", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a50e3824837d24fcd", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a696864e", _A, "CS-1295 review findings F007, a worktree id prefix"),
    AllowRow("a696864ecd64dbe42", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a8915505dc0a69d68", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("a8d21d7d20ea1b118", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("ada15e8d", _A, "CS-1295 review findings F007, a worktree id prefix"),
    AllowRow("ada15e8ddd25abf3f", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("ae6825afcde250bcc", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("ae6cedd3443ae97ae", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("aeb066f9abbf062c9", _A, "CS-1295 review plan unit row, a linked worktree id"),
    AllowRow("afb8ac949de968d20", _A, "CS-1295 review plan unit row, a linked worktree id"),
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
    AllowRow(
        "389fe4a", _F, "CS-700 S7a rehearsal tip, rewritten graph, now published, history_notes"
    ),
    AllowRow(
        "b7b4a2c4b71c942bb759aa2b4f3b9ba906ddc1ec",
        _F,
        "CS-704 image of c6f3687 under the S7a rewrite, now published, LEDGER and history_notes",
    ),
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


def refusing_repeats(reason: str) -> Callable[[list[tuple[str, object]]], dict[str, object]]:
    """A ``json`` object hook refusing a key listed twice, with ``reason`` - CS-1332.

    JSON keeps the LAST value of a repeated key and says nothing, so a pin or a
    set read without this is whichever row happens to come last. The refusal is
    the one :func:`allowlist_map` and the historical tokens already make: a
    member listed twice is an error, never resolved.

    Raises:
        GateError: From the hook, when any object at any depth repeats a key.
    """

    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        keys = [key for key, _value in pairs]
        if len(set(keys)) != len(keys):
            raise GateError(reason)
        return dict(pairs)

    return unique


def load_known_binaries(repo: Path) -> dict[str, str]:
    """The tree's binary pins, ``path -> sha256``; empty when :data:`KNOWN_BINARY_FILE` is absent.

    Raises:
        GateError: When the file is not a JSON object of plain repository-relative
            POSIX paths to 64-character lower-case hex digests, each path listed
            once - a pin file the gate cannot trust is never read as an empty list,
            and a repeated path is never read as its last row (CS-1332).
    """
    target = repo / KNOWN_BINARY_FILE
    if not target.is_file():
        return {}
    try:
        data = json.loads(
            target.read_bytes().decode("ascii"),
            object_pairs_hook=refusing_repeats("a binary pin path is listed twice"),
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise GateError("the binary pin file is not ASCII JSON") from exc
    if not isinstance(data, dict):
        raise GateError("the binary pin file is not a JSON object")
    for name, digest in data.items():
        parts = name.split("/")
        plain = name and not name.startswith("/") and ":" not in name and "\\" not in name
        if not plain or any(part in ("", ".", "..") for part in parts):
            raise GateError("a binary pin names a path that is not plain repository-relative")
        if not isinstance(digest, str) or not _PIN_DIGEST.fullmatch(digest):
            raise GateError("a binary pin carries a digest that is not 64 lower-case hex")
    return dict(data)


def is_known_binary(name: str, raw: bytes, pins: Mapping[str, str]) -> bool:
    """Whether a NOT-READ tracked file's path AND exact bytes match a pin - CS-1292."""
    pinned = pins.get(name)
    return pinned is not None and hashlib.sha256(raw).hexdigest() == pinned


def _grade_unread(
    name: str, raw: bytes | None, views: list[str], pins: Mapping[str, str]
) -> tuple[bool, list[Occurrence], list[Occurrence]]:
    """A NOT-READ file: whether a pin admits it, and its raw bytes' runs - CS-1292.

    A file the decoder refused with no view at all is graded as its raw bytes
    read as latin-1, resolved-only like code, pinned or not - a citation hidden
    behind a NUL still fails the run. Bytes carrying a NUL are graded once more
    with every NUL removed, so UTF-16 text without a byte-order mark, or a run
    split by NULs, is joined and seen. A compressed run is not.
    """
    known = raw is not None and is_known_binary(name, raw, pins)
    if raw is None:
        return known, [], []
    graded = [] if views else [raw.decode("latin-1")]
    if b"\0" in raw:
        graded.append(raw.replace(b"\0", b"").decode("latin-1"))
    return (
        known,
        _union(scan_code(view, name) for view in graded),
        _union(scan_short(view, name) for view in graded),
    )


#: The metadata fields of one ``ls-files -s`` entry (mode, id, stage), of one
#: ``ls-tree`` entry (mode, type, id) and of one ``cat-file --batch`` header
#: (id, type, size).
_ENTRY_FIELDS: Final = 3

#: The index mode of a gitlink - a tree entry naming a commit, not content.
_GITLINK_MODE: Final = b"160000"


@dataclass(frozen=True)
class _Entries:
    """What the index and ``HEAD``'s tree hold, per path - CS-1292.

    Attributes:
        blobs: Each path's blob ids, the index's every stage first, then ``HEAD``'s.
        gitlinks: Each path's gitlink commits, the index's first, then ``HEAD``'s.
        indexed: Every path the index holds as a blob - the only paths whose
            absence from the work tree is a file dropping out, so NOT READ.
    """

    blobs: dict[str, list[str]]
    gitlinks: dict[str, list[str]]
    indexed: frozenset[str]


def _entries(repo: Path, head: bool) -> _Entries:
    """Each path's index entries, every stage, then its ``HEAD`` entry when ``head`` - CS-1292.

    A gitlink (mode 160000) names a commit, not content: its id is kept apart,
    to be graded as the run it is, never read as a blob.
    """
    blobs: dict[str, list[str]] = {}
    gitlinks: dict[str, list[str]] = {}
    indexed: set[str] = set()

    def add(into: dict[str, list[str]], name: bytes, oid: bytes) -> None:
        ids = into.setdefault(name.decode("utf-8"), [])
        if oid.decode("ascii") not in ids:
            ids.append(oid.decode("ascii"))

    for entry in _git_out(repo, ["ls-files", "-s", "-z"]).split(b"\0"):
        meta, _, name = entry.partition(b"\t")
        fields = meta.split()
        if not name or len(fields) != _ENTRY_FIELDS:
            continue
        if fields[0] == _GITLINK_MODE:
            add(gitlinks, name, fields[1])
        else:
            indexed.add(name.decode("utf-8"))
            add(blobs, name, fields[1])
    if head:
        for entry in _git_out(repo, ["ls-tree", "-r", "-z", "--full-tree", "HEAD"]).split(b"\0"):
            meta, _, name = entry.partition(b"\t")
            fields = meta.split()
            if name and len(fields) == _ENTRY_FIELDS and fields[1] in (b"blob", b"commit"):
                add(blobs if fields[1] == b"blob" else gitlinks, name, fields[2])
    return _Entries(blobs, gitlinks, frozenset(indexed))


def scan_entry(name: str, commits: Sequence[str] = ()) -> tuple[list[Occurrence], list[Occurrence]]:
    """A tree entry's own runs - its path, and each commit a gitlink there names - CS-1292.

    Both are published with the tree beside its bytes: a path is text every tree
    object carries, and a gitlink is a bare commit name. Each is graded like a
    code run, resolved-only, and carries line 0 - the entry itself, never a
    line of its bytes.

    Returns:
        The 7-to-40 runs, then the 5-or-6 runs, each at line 0.
    """
    code = [[replace(run, line=0) for run in scan_code(text, name)] for text in (name, *commits)]
    short = [[replace(run, line=0) for run in scan_short(name, name)]]
    return _union(code), _union(short)


def _blob_id(raw: bytes) -> str:
    """The sha1 object name git gives ``raw`` as a blob."""
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw, usedforsecurity=False).hexdigest()


def _read_blobs(repo: Path, oids: Sequence[str]) -> dict[str, bytes]:
    """Every blob in ``oids`` by its id, in ONE ``git cat-file --batch`` call - CS-1292.

    Raises:
        GateError: When git fails, or answers anything but each blob whole.
    """
    if not oids:
        return {}
    done = _git(repo, ["cat-file", "--batch"], "".join(f"{oid}\n" for oid in oids).encode())
    if done.returncode != 0:
        raise GateError(f"git cat-file exited {done.returncode}")
    out, at, blobs = done.stdout, 0, {}
    for oid in oids:
        end = out.find(b"\n", at)
        fields = out[at:end].split() if end >= 0 else []
        if len(fields) != _ENTRY_FIELDS or fields[0].decode("ascii") != oid or fields[1] != b"blob":
            raise GateError("git cat-file did not answer a blob for a tracked path")
        size = int(fields[2])
        blobs[oid] = out[end + 1 : end + 1 + size]
        at = end + 2 + size
    return blobs


def _versions(repo: Path, names: Sequence[str], entries: _Entries) -> dict[str, list[bytes | None]]:
    """Each path's distinct bytes: the work tree's, then each differing blob - CS-1292.

    The work tree's bytes come first, then each blob of the path's index entries
    and of ``HEAD`` that differs from them. The work tree alone is not what git
    publishes: a staged or committed blob, a case-variant path a case-insensitive
    disk opens as its sibling, or a symlink entry whose blob is its link text all
    differ from what the path opens on disk. An absent work-tree file is listed
    as None - NOT READ - only for a path the index holds as a blob: a staged
    deletion, a rename source or a gitlink is judged by its entries alone.
    """
    ids = entries.blobs
    raws = {name: (repo / name).read_bytes() if (repo / name).is_file() else None for name in names}
    wanted: dict[str, None] = {}
    for name in names:
        raw = raws[name]
        own = None if raw is None else _blob_id(raw)
        wanted.update(dict.fromkeys(oid for oid in ids.get(name, []) if oid != own))
    blobs = _read_blobs(repo, list(wanted))
    versions: dict[str, list[bytes | None]] = {}
    for name in names:
        raw = raws[name]
        found: list[bytes | None] = [raw] if raw is not None or name in entries.indexed else []
        for oid in ids.get(name, []):
            body = blobs.get(oid)
            if body is not None and body not in found:
                found.append(body)
        versions[name] = found
    return versions


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
    """The environment of EVERY git call the gate makes - :func:`_git` is the only caller.

    Beside dropping :data:`_GIT_REDIRECTS`, it turns off git's two LOCAL views of
    history - CS-1292 round 4. A replace ref swaps the bytes git reads for a blob,
    a tree or a commit, and a replace graft or an ``info/grafts`` line gives a
    commit parents it does not have; a push sends neither view, so honouring one
    hides a cited blob or makes an unpublished commit look reachable from
    ``HEAD``. ``GIT_NO_REPLACE_OBJECTS`` turns replace refs off and no config can
    turn them back on; it leaves the grafts file read, so ``GIT_GRAFT_FILE`` points
    at the null device, an empty grafts file.
    """
    env = dict(os.environ)
    for name in _GIT_REDIRECTS:
        env.pop(name, None)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_GRAFT_FILE"] = os.devnull
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


def _tracked(repo: Path, pathspecs: Sequence[str], head: bool) -> list[str]:
    """Every path the index holds, plus ``HEAD``'s the index dropped when ``head`` - CS-1292.

    ``--with-tree=HEAD`` overlays HEAD's tree on the index, so a path committed
    and then ``git rm``'d, or the source of a ``git mv``, is still listed: HEAD
    is what a push publishes, whatever the index says. Git matches the pathspecs.
    """
    overlay = ["--with-tree=HEAD"] if head else []
    listed = _git_out(repo, ["ls-files", "-z", *overlay, "--", *pathspecs]).decode("utf-8")
    return sorted({name for name in listed.split("\0") if name})


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


# --- CS-700: the state-witnessed historical set --------------------------------

_FULL_SHA: Final = re.compile(r"[0-9a-f]{40}")
_LISTED: Final = re.compile(r"[0-9a-f]{5,40}")

#: The states the witness pair can read: PRE and POST judge, the other two cannot.
STATE_PRE: Final = "PRE"
STATE_POST: Final = "POST"
STATE_BOTH: Final = "BOTH"
STATE_NEITHER: Final = "NEITHER"

#: How many times a rename onto the set is tried - Windows can hold the target briefly.
_RENAME_TRIES: Final = 5


@dataclass(frozen=True)
class Historical:
    """The parsed historical set.

    Attributes:
        witness: ``(pre, post)`` - a commit of the history S7a rewrites, and its image.
        tokens: Every listed token, lower case.
        digest: The SHA-256 of the bytes it was parsed from; empty when built in memory.
    """

    witness: tuple[str, str]
    tokens: frozenset[str]
    digest: str = ""


def parse_historical(raw: bytes) -> Historical:
    """Parse the set STRICTLY: exact keys, schema 1, full-sha witnesses, hex tokens.

    Raises:
        GateError: On any deviation. The reason is fixed text - never a value.
    """
    try:
        data = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=refusing_repeats("historical set has a key listed twice"),
        )
    except (UnicodeDecodeError, ValueError):
        raise GateError("historical set is not ASCII JSON") from None
    if not isinstance(data, dict) or set(data) != {"schema", "witness", "tokens"}:
        raise GateError("historical set keys are not exactly schema, witness, tokens")
    witness, tokens = data["witness"], data["tokens"]
    if data["schema"] != 1:
        raise GateError("historical set schema is not 1")
    if not isinstance(witness, dict) or set(witness) != {"pre", "post"}:
        raise GateError("historical witness keys are not exactly pre, post")
    pair = (witness["pre"], witness["post"])
    if not all(isinstance(sha, str) and _FULL_SHA.fullmatch(sha) for sha in pair):
        raise GateError("historical witness is not two full lower-case shas")
    if pair[0] == pair[1]:
        raise GateError("historical witness pre and post are the same commit")
    if not isinstance(tokens, list) or not all(
        isinstance(token, str) and _LISTED.fullmatch(token) for token in tokens
    ):
        raise GateError("historical tokens are not lower-case hex runs of 5 to 40")
    if len(set(tokens)) != len(tokens):
        raise GateError("historical set lists a token twice")
    return Historical((pair[0], pair[1]), frozenset(tokens), hashlib.sha256(raw).hexdigest())


def tamper_of(historical: Historical) -> list[str]:
    """Each pin the tree's set breaks: the gate's digest, then the gate's witness pair.

    A set whose bytes differ from :data:`HISTORICAL_SHA256` was edited outside
    ``--emit-historical``; a witness pair other than :data:`WITNESS` reads a
    state the gate never witnessed. Either one is a failure, in every state.
    """
    found: list[str] = []
    if historical.digest != HISTORICAL_SHA256:
        found.append("historical-digest-mismatch")
    if historical.witness != WITNESS:
        found.append("historical-witness-mismatch")
    return found


def repin_source(source: str, digest: str) -> str:
    """``source`` with its one :data:`HISTORICAL_SHA256` line set to ``digest``.

    Raises:
        GateError: When the pin line is not present exactly once, or ``digest``
            is not a SHA-256 hex digest.
    """
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise GateError("a historical pin is not a SHA-256 hex digest")
    if len(_PIN_LINE.findall(source)) != 1:
        raise GateError("the gate source does not carry its pin line exactly once")
    return _PIN_LINE.sub(f'HISTORICAL_SHA256: Final = "{digest}"', source)


def load_historical(repo: Path) -> Historical | None:
    """The tree's historical set, or None when :data:`HISTORICAL_FILE` is absent."""
    target = repo / HISTORICAL_FILE
    return parse_historical(target.read_bytes()) if target.is_file() else None


def render_historical(historical: Historical) -> bytes:
    """The set as the generated file's exact bytes: ASCII, LF, sorted, one final LF."""
    data = {
        "schema": 1,
        "witness": {"pre": historical.witness[0], "post": historical.witness[1]},
        "tokens": sorted(historical.tokens),
    }
    return (json.dumps(data, indent=2) + "\n").encode("ascii")


def write_atomic(target: Path, body: bytes) -> None:
    """Write ``body`` to ``target`` through a sibling temp file and a rename, retried."""
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_bytes(body)
    for attempt in range(_RENAME_TRIES):
        try:
            tmp.replace(target)
            return
        except PermissionError:
            if attempt == _RENAME_TRIES - 1:
                raise
            time.sleep(0.2)


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
        known_binary: Unreadable tracked files whose path and SHA-256 match a
            :data:`KNOWN_BINARY_FILE` pin - counted and named, never COULD NOT
            JUDGE, their raw bytes still graded (CS-1292).
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
    known_binary: list[str] = field(default_factory=list)
    ambiguous: list[Occurrence] = field(default_factory=list)
    ambiguous_unpublished: list[Occurrence] = field(default_factory=list)
    historical: Historical | None = None
    state: str | None = None
    historical_failures: list[tuple[str, str]] = field(default_factory=list)
    historical_tamper: list[str] = field(default_factory=list)
    historical_exempt: int = 0
    text_published: set[str] = field(default_factory=set)

    @property
    def everywhere(self) -> list[Occurrence]:
        """Every occurrence of every population - doc tokens, not-admitted, code, short."""
        return [*self.occurrences, *self.not_admitted, *self.code_runs, *self.short_runs]

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
        if self.historical_tamper:
            return EXIT_UNRESOLVED
        if self.shallow or not self.published_refs or not self.admitted:
            return EXIT_COULD_NOT_JUDGE
        if self.historical is not None and self.state not in (STATE_PRE, STATE_POST):
            return EXIT_COULD_NOT_JUDGE
        failed = (
            self.unresolved
            or self.overreach
            or self.not_admitted_unpublished
            or self.ambiguous_unpublished
            or self.historical_failures
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


def _read_versions(
    name: str, contents: Sequence[bytes | None], pins: Mapping[str, str]
) -> tuple[list[str], list[bool], list[Occurrence], list[Occurrence]]:
    """One path's versions read - its views, its unread verdicts and their raw runs.

    Returns:
        Its decoded views, each NOT-READ version's pin verdict, then those
        versions' raw 7-to-40 runs and 5-or-6 runs (:func:`_grade_unread`).
    """
    views: list[str] = []
    unread: list[bool] = []
    code: list[Occurrence] = []
    short: list[Occurrence] = []
    for raw in contents:
        seen, read = tracked_views(raw) if raw is not None else ([], False)
        if not read:
            known, raw_code, raw_short = _grade_unread(name, raw, seen, pins)
            unread.append(known)
            code += raw_code
            short += raw_short
        views += [text for text in seen if text not in views]
    return views, unread, code, short


def sweep(
    repo: Path,
    allowlist: Mapping[str, str] | None = None,
    historical: Historical | None = None,
) -> SweepReport:
    """Read every tracked doc in ``repo`` and judge every citation against published history.

    Args:
        repo: A work tree.
        allowlist: ``token -> class``; the shipped table when None.
        historical: The CS-700 set; read from :data:`HISTORICAL_FILE` when None,
            and absent - the pre-CS-700 gate - when that file is absent too.

    Returns:
        The report. On a shallow clone, or with neither origin/main nor a
        tag, nothing is resolved - nothing can be judged.

    Raises:
        GateError: When git cannot be run or ``repo`` is not a repository.
    """
    table = allowlist_map() if allowlist is None else allowlist
    shallow = _git_out(repo, ["rev-parse", "--is-shallow-repository"]).strip() != b"false"
    head = _git(repo, ["rev-parse", "--verify", "-q", "HEAD"]).returncode == 0
    paths = _tracked(repo, DOC_PATHSPECS, head)
    code_paths = _tracked(repo, CODE_PATHSPECS, head)
    code_set = set(code_paths)
    occurrences: list[Occurrence] = []
    not_admitted: list[Occurrence] = []
    code_runs: list[Occurrence] = []
    short_runs: list[Occurrence] = []
    not_judged = dict.fromkeys(NOT_JUDGED, 0)
    not_read: list[str] = []
    known_binary: list[str] = []
    pins = load_known_binaries(repo)
    names = [*paths, *code_paths]
    entries = _entries(repo, head)
    for name, contents in _versions(repo, names, entries).items():
        views, unread, raw_code, raw_short = _read_versions(name, contents, pins)
        entry_code, entry_short = scan_entry(name, entries.gitlinks.get(name, []))
        code_runs += raw_code + entry_code
        short_runs += raw_short + entry_short
        if unread:
            (known_binary if all(unread) else not_read).append(name)
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
    report.known_binary = known_binary
    if historical is None:
        report.historical = load_historical(repo)
        if report.historical is not None:
            report.historical_tamper = tamper_of(report.historical)
    else:
        report.historical = historical
    if shallow or not ref_count:
        return report
    _judge(repo, report, published)
    return report


def _witness_state(
    historical: Historical, runs: Mapping[str, str | None], published: set[str]
) -> str:
    """The state the witness pair reads: which of ``pre`` and ``post`` is published."""
    pre_pub, post_pub = (runs[sha] in published for sha in historical.witness)
    return {
        (True, False): STATE_PRE,
        (False, True): STATE_POST,
        (True, True): STATE_BOTH,
    }.get((pre_pub, post_pub), STATE_NEITHER)


def _judge(repo: Path, report: SweepReport, published: set[str]) -> None:
    """Resolve every run, listed token and witness ONCE, and fill every verdict field."""
    occurrences = report.occurrences
    resolved_only = [*report.not_admitted, *report.code_runs, *report.short_runs]
    every = {entry.token for entry in resolved_only} | {entry.token for entry in occurrences}
    historical = report.historical
    listed = historical.tokens if historical is not None else frozenset()
    witness = set(historical.witness) if historical is not None else set()
    runs, ambiguous = resolve_batch(repo, sorted(every | listed | witness))
    report.text_published = {token for token in every if runs[token] in published}
    image_rows: frozenset[str] = frozenset()
    if historical is not None:
        report.state = _witness_state(historical, runs, published)
        report.historical_failures = _historical_failures(
            report.state, listed, runs, ambiguous, published
        )
        if report.state == STATE_POST:
            image_rows = S7A_IMAGE_ROWS | {historical.witness[1]}
    post = report.state == STATE_POST

    def historical_exempt(token: str) -> bool:
        if post and token.lower() in listed:
            report.historical_exempt += 1
            return True
        return False

    report.not_admitted_unpublished = [
        entry
        for entry in resolved_only
        if (commit := runs[entry.token]) is not None
        and commit not in published
        and not historical_exempt(entry.token)
    ]
    report.ambiguous = [entry for entry in resolved_only if entry.token in ambiguous]
    unpublished_candidates = {token for token, commits in ambiguous.items() if commits - published}
    report.ambiguous_unpublished = [
        entry
        for entry in report.ambiguous
        if entry.token in unpublished_candidates and not historical_exempt(entry.token)
    ]
    for entry in occurrences:
        commit = runs[entry.token]
        is_published = commit is not None and commit in published
        if entry.rule is not None and is_published:
            if not any(image.startswith(entry.token) for image in image_rows):
                report.overreach.append(entry)
        elif entry.rule is None and not is_published and not historical_exempt(entry.token):
            report.unresolved.append((entry, _state(report, entry.token, commit)))


def _historical_failures(
    state: str,
    listed: frozenset[str],
    runs: Mapping[str, str | None],
    ambiguous: Mapping[str, set[str]],
    published: set[str],
) -> list[tuple[str, str]]:
    """Each listed token the witnessed state refuses, with its failure label.

    PRE: a listed token that is not exactly one published commit is STALE. POST:
    a listed token that one published commit - or any candidate of an ambiguous
    answer - names is a COLLISION. Any other state judges nothing here; the
    verdict already refuses to judge it.
    """
    failures: list[tuple[str, str]] = []
    for token in sorted(listed):
        commit = runs[token]
        names_published = commit in published or bool(ambiguous.get(token, set()) & published)
        if state == STATE_PRE and (commit is None or commit not in published):
            failures.append((token, "historical-stale"))
        elif state == STATE_POST and names_published:
            failures.append((token, "historical-collision"))
    return failures


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
    out.append(f"known-binary {len(report.known_binary)} - {KNOWN_BINARY_REASON}")
    out += [f"known-binary-file {name}" for name in report.known_binary]
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
    out += _render_historical(report)
    verdict = report.verdict()
    if verdict == EXIT_CLEAN:
        out.append("sha_citation_gate: PASS - every admitted citation is a published commit")
    elif verdict == EXIT_UNRESOLVED:
        out.append(
            "sha_citation_gate: FAIL - a citation is not a published commit, an "
            "allowlisted token is one, a not-admitted, code or short run names an "
            "unpublished commit, or the historical set breaks a pin"
        )
        if report.not_read:
            out.append(f"sha_citation_gate: ALSO COULD NOT JUDGE - {_not_read_reason(report)}")
    else:
        reason = _could_not_judge_reason(report)
        out.append(f"sha_citation_gate: COULD NOT JUDGE - {reason}, which is not a pass")
    return out


def _could_not_judge_reason(report: SweepReport) -> str:
    """Why a run exits 2, first cause first."""
    if report.shallow:
        return "a shallow clone"
    if not report.published_refs:
        return "no origin/main and no tag"
    if not report.admitted:
        return "the sweep admitted nothing"
    if report.historical is not None and report.state not in (STATE_PRE, STATE_POST):
        return f"the historical witness pair reads {report.state}"
    return _not_read_reason(report)


def _render_historical(report: SweepReport) -> list[str]:
    """The CS-700 lines: the set's presence, its witnessed state and every failure."""
    if report.historical is None:
        return [
            f"historical ABSENT - no {HISTORICAL_FILE}; every citation is judged against "
            "published history alone"
        ]
    out = [
        f"historical {report.state or 'UNJUDGED'} - {len(report.historical.tokens)} listed "
        f"tokens; exempt as history {report.historical_exempt}; PRE requires every listed "
        "token published, POST forbids any, BOTH and NEITHER cannot judge"
    ]
    out += [f"{label} {token}" for token, label in report.historical_failures]
    out += [f"{label} {HISTORICAL_FILE} - {_TAMPER[label]}" for label in report.historical_tamper]
    return out


#: CS-700 - what each broken pin means, printed beside the file it names.
_TAMPER: Final[dict[str, str]] = {
    "historical-digest-mismatch": (
        "its bytes are not the ones HISTORICAL_SHA256 pins in this gate; regenerate it "
        "with --emit-historical in the PRE state, never by hand"
    ),
    "historical-witness-mismatch": "its witness pair is not this gate's WITNESS",
}


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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--emit-historical", action="store_true", help="regenerate the CS-700 set (PRE only)"
    )
    mode.add_argument(
        "--flip-readiness", action="store_true", help="0 only if no citation is outside the set"
    )
    args = parser.parse_args(argv)
    try:
        if args.emit_historical:
            return emit_historical(args.repo)
        if args.flip_readiness:
            return flip_readiness(args.repo)
        report = sweep(args.repo)
    except GateError as exc:
        print(f"sha_citation_gate: COULD NOT JUDGE - {exc.reason}", file=sys.stderr)
        return EXIT_COULD_NOT_JUDGE
    print("\n".join(render(report)))
    return report.verdict()


def _pre_report(repo: Path, historical: Historical | None, mode: str) -> SweepReport | None:
    """A sweep under ``historical`` (the tree's own when None), or None unless PRE."""
    report = sweep(repo, historical=historical)
    if report.shallow or not report.published_refs or report.state != STATE_PRE:
        state = report.state or "UNJUDGED"
        print(
            f"sha_citation_gate: {mode} COULD NOT JUDGE - the witness pair reads {state}, "
            "or the clone is shallow or has no published ref; PRE is required"
        )
        return None
    return report


def emit_historical(repo: Path) -> int:
    """Regenerate :data:`HISTORICAL_FILE` from every published token in tracked text.

    PRE state only: after the rewrite no old token is published, so a regeneration
    would silently empty the set. The witness is always :data:`WITNESS`. The set's
    SHA-256 is then pinned into THIS gate's own source - so only the gate that
    judges ``repo`` may emit for it: one whose file is not ``repo``'s own
    ``tools/sha_citation_gate.py`` exits 2 and writes nothing.
    """
    own = Path(__file__).resolve()
    if (repo / _GATE_PATH).resolve() != own:
        print(
            "sha_citation_gate: emit-historical COULD NOT JUDGE - this gate is not the "
            f"judged tree's own {_GATE_PATH}, so it cannot pin that tree's set"
        )
        return EXIT_COULD_NOT_JUDGE
    report = _pre_report(repo, Historical(WITNESS, frozenset()), "emit-historical")
    if report is None:
        return EXIT_COULD_NOT_JUDGE
    tokens = frozenset(token.lower() for token in report.text_published)
    body = render_historical(Historical(WITNESS, tokens))
    pinned = repin_source(own.read_bytes().decode("ascii"), hashlib.sha256(body).hexdigest())
    write_atomic(repo / HISTORICAL_FILE, body)
    write_atomic(own, pinned.encode("ascii"))
    print(
        f"sha_citation_gate: emit-historical wrote {len(tokens)} tokens to {HISTORICAL_FILE} "
        f"and pinned its SHA-256 in {_GATE_PATH}"
    )
    return EXIT_CLEAN


def flip_readiness(repo: Path) -> int:
    """0 only in the PRE state with no stale listed token and no published token unlisted."""
    historical = load_historical(repo)
    if historical is None:
        print(f"sha_citation_gate: flip-readiness COULD NOT JUDGE - no {HISTORICAL_FILE}")
        return EXIT_COULD_NOT_JUDGE
    report = _pre_report(repo, None, "flip-readiness")
    if report is None:
        return EXIT_COULD_NOT_JUDGE
    outside = [
        entry
        for entry in report.everywhere
        if entry.token in report.text_published and entry.token.lower() not in historical.tokens
    ]
    out = [f"flip-outside {entry.path}:{entry.line} {entry.token}" for entry in outside]
    out += [f"{label} {token}" for token, label in report.historical_failures]
    out += [f"{label} {HISTORICAL_FILE}" for label in report.historical_tamper]
    failed = bool(outside or report.historical_failures or report.historical_tamper)
    out.append(
        f"sha_citation_gate: flip-readiness {'NOT READY' if failed else 'READY'} - "
        f"{len(historical.tokens)} listed; outside {len(outside)}; "
        f"stale {len(report.historical_failures)}"
    )
    print("\n".join(out))
    return EXIT_UNRESOLVED if failed else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
