#!/usr/bin/env python3
"""CS-1095 - the vendored cross-repo channel conventions doc, byte-pinned.

``docs/CHANNEL.md`` is VENDORED, not authored here. The same bytes sit at the
same relative path in five participating repositories, and the doc's own
section 9 makes the pin a joint act: a byte change without a CHANNEL_VERSION
bump, or a bump without a re-pin, is red by construction because this module
binds the two together.

WHAT THAT MEANS FOR A REPAIR, and it inverts the usual instinct. A failing arm
here is NEVER fixed by editing the doc. The doc is a copy of somebody else's
bytes; editing it does not make this tree agree with the channel, it makes this
tree the only one that disagrees. A guard that refuses the doc gets an
EXEMPTION in the guard, or a topology row - never a byte of the document.

THE SEVEN ARMS ARE THE CHANNEL'S PORTABLE CORE, reproduced here in the order
the announcing note spelled them. They are deliberately self-contained: no
repo sweep tooling is imported into the arms, because the same seven have to
run in a tree with a different guard set. The one exception is arm 5's ORACLE
LEG, which is optional by construction - see :func:`test_no_heading_carries_a_date`.

WHAT IS DELIBERATELY NOT VENDORED: the announcing tree's own gate module. It
hard-imports tooling that exists in exactly one repository, so vendoring it
would import a dependency this tree does not have in order to check a document
that needs none.

THE DIGEST IS OVER LF-NORMALISED BYTES, not raw bytes, and that is the channel's
choice rather than this tree's. Not every participant pins markdown to LF in
its attributes file, so a raw-byte pin would be red in a tree whose working copy
checks out CRLF even though all five git blobs are identical. This tree DOES
pin ``*.md text eol=lf``, which is what makes arm 3 - zero CR bytes - a valid
arm here; arm 3 asserts that precondition itself rather than assuming it, so
the arm cannot quietly become a statement about somebody's checkout.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The vendored document, at the relative path the channel pins.
CHANNEL_DOC = REPO_ROOT / "docs" / "CHANNEL.md"

#: The sha256 of the LF-normalised bytes, MEASURED from this tree's own disk
#: (CS-1095) and reproducing the value the announcing note published. It is
#: spelled here as a digest of a public document and is deliberately NOT
#: labelled as a key, a token or a secret: the channel's own convention 1
#: records that a credential scanner in at least one participating tree
#: refuses that shape on a 32-plus hex run.
CHANNEL_DIGEST = "899f6eb957cc26ee25993d83d65d8ca291841fe4eec24a48f729c2dc005f4c6b"

#: The version the vendored bytes declare. Bound to the digest above by
#: arm 4 plus arm 2, which is the "red by construction" the doc's section 9
#: describes.
CHANNEL_VERSION = 1

#: The attributes rule arm 3 rests on.
MARKDOWN_LF_RULE = re.compile(r"^\*\.md\s+text\s+eol=lf\s*$", re.MULTILINE)

#: The declaration line, read from the document's own text.
VERSION_LINE = re.compile(r"^CHANNEL_VERSION:[ \t]*(\d+)[ \t]*$", re.MULTILINE)

# ---------------------------------------------------------------------------
# Arm 5's date vocabulary.
#
# TRANSCRIBED from ``tools/drift_guard.py``'s DATE_PATTERNS rather than
# invented, because arm 5 exists to answer the question THAT guard asks. A
# looser pattern here would pass a heading the guard reddens, which is the
# worst of both: a green arm and a red commit. The transcription is checked
# against the original at runtime by the oracle leg below, so the two cannot
# drift apart in silence.
#
# Each shape carries the same digit lookaround as the original, so none of them
# can match inside a longer run of digits.
# ---------------------------------------------------------------------------
DATE_PATTERNS = (
    re.compile(r"(?<!\d)\d{4}-\d{1,2}-\d{1,2}(?!\d)"),
    re.compile(r"(?<!\d)\d{2}-\d{2}-\d{2}(?!\d)"),
    re.compile(r"(?<!\d)\d{4}/\d{1,2}/\d{1,2}(?!\d)"),
    re.compile(r"(?<!\d)\d{1,2}/\d{1,2}/\d{2,4}(?!\d)"),
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September"
        r"|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept"
        r"|Oct|Nov|Dec)\b[ \t]*,?[ \t]*(?:\d{1,2}(?:st|nd|rd|th)?[ \t]*,?[ \t]*)?"
        r"\d{4}(?!\d)"
    ),
)

# ---------------------------------------------------------------------------
# Arm 6's populations.
#
# The doc names three KINDS of filesystem token and only one of them is a
# repo-relative path. Saying which is which is the whole arm: a population that
# swept all three would manufacture findings on tokens the document explicitly
# declares unresolvable, and a population that swept none would pass by
# measuring nothing.
# ---------------------------------------------------------------------------

#: A backticked token. The document quotes every path it names, and the bare
#: leg below asserts that claim rather than trusting it.
BACKTICKED = re.compile(r"`([^`\n]+)`")

#: A ``file:line`` pointer. Anchored on a file EXTENSION so a channel note's
#: date-and-time stem, a ``pid:`` label or a ``subject_sha256:`` label cannot
#: match. Arm 6's second half asserts the doc carries none of these at all.
FILE_LINE = re.compile(r"[\w.\-/]+\.[A-Za-z]{1,5}:\d+")

#: Repo-relative paths the doc names that DO NOT resolve here, each with the
#: reason, and each checked in BOTH directions by arm 6: a member that starts
#: resolving is as much a finding as a non-member that stops.
UNRESOLVED_REPO_PATHS: dict[str, str] = {}

#: Repo-relative paths whose PRESENCE IS A PROPERTY OF THE CHECKOUT AND NOT OF
#: THE REPOSITORY, so neither resolving nor failing to resolve is a finding.
#:
#: THIS ROSTER EXISTS BECAUSE THE FIRST VERSION OF ARM 6 SHIPPED A RED. It
#: recorded the inbox directory as a non-resolver, which is what a worktree
#: measures - the arm was built and graded in one, and a worktree is a fresh
#: checkout that never created a gitignored directory. The PRIMARY checkout has
#: one, because that is where notes actually arrive. So the arm passed where it
#: was written and failed where it was merged, and the roster was not wrong so
#: much as asking the wrong question.
#:
#: EXISTENCE IS THE WRONG PROPERTY TO ASSERT ABOUT A GITIGNORED PATH. Being
#: IGNORED is the right one: it is a fact about the repository, it is identical
#: in a worktree and in the primary tree, and it is what the document is
#: actually claiming when it says a clone has no channel. The arm asserts that
#: instead, and says nothing about whether the directory happens to be there.
CHECKOUT_DEPENDENT_REPO_PATHS = {
    "moon_sync_inbox/": (
        "gitignored at /moon_sync_inbox/, so it exists in the primary checkout "
        "where notes arrive and in no worktree. The document says this about "
        "itself in its own header and again in section 5 property 5."
    ),
}

#: The name of the cross-repo charter, cited by the doc's section 9.
#:
#: CS-1095 FINDING, recorded here rather than absorbed: this token is
#: RC-RELATIVE. The charter is tracked in the announcing tree and this tree
#: does not carry it, so the name resolves nowhere here. It is spelled without
#: a directory component in the doc, which is what keeps it out of the
#: repo-relative population - but a reader who found it in the bare pile with
#: no explanation would reasonably read it as one more channel note, and it is
#: not. Naming it is the difference between a record and a silence.
CROSS_REPO_CHARTER = "CROSS_REPO_CONVERGENCE_CHARTER.md"

#: Provenance notes the doc cites by BARE FILENAME on purpose. Its section 4
#: states the rule: provenance is cited by bare name because the directory
#: these notes live in is gitignored and a line cite into it resolves in no
#: tree at all. Arm 6 does not resolve these - but the COUNT is pinned, so one
#: growing a directory component moves between populations visibly.
PROVENANCE_NOTE_CITES = 8

#: Synthetic filenames in the grammar table. The doc says of them, in its own
#: words, that they are synthetic and that no live note name appears there -
#: so these name no file BY CONSTRUCTION and resolving them would be a
#: category error rather than a finding.
SYNTHETIC_EXAMPLE_CITES = 4

#: What marks a grammar-table example. Kept as data beside the count above so
#: the rule that builds the population is readable next to its size.
SYNTHETIC_MARKER = "example-topic"

#: Tokens naming a path outside any repository. One member: the poller status
#: file, written unexpanded in the doc on purpose (its section 8 invariant 1).
NON_REPO_PATHS = {"%LOCALAPPDATA%\\moonsync\\status.md"}

#: Repo-relative paths the doc names that DO resolve here, pinned to the exact
#: measured value rather than to a non-empty test.
#:
#: CS-1095 REPAIR: this population is a SINGLE SELF-REFERENCE - the document
#: naming its own path - because the repo-relative population is exactly two
#: tokens and the other is the recorded non-resolver above. The arm's former
#: ``assert resolved`` anti-vacuity guard was therefore satisfied by a fact arm
#: 1 already proves, and could never fire. An honest narrow pin beats a guard
#: advertising a property it cannot hold; do NOT manufacture a second resolving
#: path to make one look alive.
RESOLVED_REPO_PATHS = ["docs/CHANNEL.md"]

# ---------------------------------------------------------------------------
# Arm 7's table.
#
# CS-1095 REPAIR. The arm graded the table's SHAPE and not its CONTENT: column
# count, row count, the Shape column, verdict MEMBERSHIP and a backticked
# column 0 - never four of the seven columns. Replayed over mutated text it
# measured GREEN on a garbled PRIMARY vector, a garbled Variant A vector, a
# swapped pair of vectors, a PRIMARY verdict flipped ADMIT to REFUSE, and all
# four responder columns blanked on every row. Only a deleted separator row
# reddened it.
#
# The blast radius is NOT today - arm 2's digest reddens on any byte change
# now. It is the CHANNEL_VERSION 2 re-pin, when the digest legitimately moves
# and a hand-copied table is most likely to be mangled. That is the one moment
# this arm is ever load-bearing, so the roster below pins every cell.
#
# TABLE_ROWS is kept BESIDE the roster as its size and asserted against it: on
# this project a member goes absent exactly where a count miscounts.
# ---------------------------------------------------------------------------

TABLE_HEADING = "### Filename grammar table"
TABLE_COLUMNS = 7
TABLE_ROWS = 4
TABLE_SHAPES = ("PRIMARY", "Variant A", "Variant B", "Variant C")
TABLE_VERDICTS = frozenset({"ADMIT", "REFUSE"})

#: Every cell of every body row, in file order, exactly as the vendored bytes
#: spell them - vector, the RC gate 6 verdict, the four responder columns, and
#: the shape. Transcribed from this tree's own disk at the pinned digest.
TABLE_VECTORS = (
    (
        "`2026-09-15-0930-from-RC-FYI-example-topic.md`",
        "ADMIT",
        "routes",
        "any entry",
        "no responder",
        "no responder",
        "PRIMARY",
    ),
    (
        "`2026-09-15-from-RC-FYI-example-topic.md`",
        "REFUSE",
        "routes",
        "any entry",
        "no responder",
        "no responder",
        "Variant A",
    ),
    (
        "`from-RC-2026-09-15-0930-FYI-example-topic.md`",
        "REFUSE",
        "zero destinations",
        "any entry",
        "no responder",
        "no responder",
        "Variant B",
    ),
    (
        "`2026-09-15-0930-from-RC-FYI-example-topic.txt`",
        "REFUSE",
        "routes",
        "any entry",
        "no responder",
        "no responder",
        "Variant C",
    ),
)


def _read_bytes() -> bytes:
    """Return the vendored document's raw bytes.

    Returns:
        The bytes exactly as they sit on this tree's disk.
    """
    return CHANNEL_DOC.read_bytes()


def _read_text() -> str:
    """Return the vendored document decoded as ASCII, newlines normalised to LF.

    Returns:
        The document text.
    """
    return _read_bytes().decode("ascii").replace("\r\n", "\n")


def _lf_digest(raw: bytes) -> str:
    """Return the sha256 over the LF-normalised form of ``raw``.

    Args:
        raw: The bytes read from disk.

    Returns:
        The lowercase hex digest.
    """
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def _date_in(line: str) -> bool:
    """Whether ``line`` carries a date under the transcribed vocabulary.

    Args:
        line: One line of the document.

    Returns:
        True when any shape in :data:`DATE_PATTERNS` matches.
    """
    return any(pattern.search(line) for pattern in DATE_PATTERNS)


def _heading_lines(text: str) -> list[tuple[int, str]]:
    """Return every line that opens with a hash mark, numbered from one.

    The channel's arm 5 grades HEADING LINES, and the drift guard it defends
    against decides headingness by the same crude test - a leading ``#`` - so
    reproducing that test is the point rather than an approximation of it.

    Args:
        text: The whole document.

    Returns:
        ``(line number, line)`` for each heading line, in file order.
    """
    return [
        (number, line.rstrip())
        for number, line in enumerate(text.splitlines(), start=1)
        if line.startswith("#")
    ]


def _quoted_tokens(text: str) -> list[str]:
    """Return every backticked token in ``text``, in file order.

    Args:
        text: The whole document.

    Returns:
        The token bodies, without their backticks.
    """
    return BACKTICKED.findall(text)


def _looks_like_a_path(token: str) -> bool:
    """Whether ``token`` names something on a filesystem rather than a label.

    A path either carries a directory separator or ends in a file extension.
    A grammar TEMPLATE - a name spelled with ``YYYY-MM-DD`` or ``<CODE>``
    placeholders - names no file and is excluded by the placeholder test, which
    is stated rather than left to the extension test to half-handle.

    Args:
        token: One backticked token body.

    Returns:
        True when the token is a path candidate.
    """
    if "<" in token or "YYYY" in token:
        return False
    if " " in token:
        return False
    return "/" in token or "\\" in token or bool(re.search(r"\.[A-Za-z]{1,5}$", token))


def test_the_vendored_doc_exists_at_the_pinned_relative_path() -> None:
    # Arm 1. The channel pins the RELATIVE path, not an absolute one, because
    # an absolute path differs per tree and per machine.
    assert CHANNEL_DOC.is_file(), (
        f"the vendored channel doc is missing at {CHANNEL_DOC.relative_to(REPO_ROOT)}"
    )


def test_the_lf_normalised_digest_matches_the_pin() -> None:
    # Arm 2, and the reason the other six can be trusted: every one of them
    # grades a document this arm has proved is the pinned one.
    measured = _lf_digest(_read_bytes())
    assert measured == CHANNEL_DIGEST, (
        "the vendored doc's LF-normalised sha256 has moved off the pin. Do NOT "
        "edit the document to get past this: these bytes are byte-identical in "
        "five repositories and a local edit makes this tree the one that "
        "disagrees. A genuine channel re-pin arrives as a note naming a new "
        f"CHANNEL_VERSION. measured={measured} pinned={CHANNEL_DIGEST}"
    )


def test_the_vendored_doc_carries_no_carriage_returns() -> None:
    # Arm 3, with its own precondition. The channel says to drop this arm in a
    # tree that does not pin markdown to LF, so the arm asserts the pin first -
    # otherwise a red here would be a statement about the checkout rather than
    # about the document, which is exactly the misreading the channel warns of.
    attributes = (REPO_ROOT / ".gitattributes").read_text(encoding="ascii")
    assert MARKDOWN_LF_RULE.search(attributes) is not None, (
        "this arm is only valid while .gitattributes pins `*.md text eol=lf`. "
        "The rule is gone, so a CR finding below would be about the checkout."
    )
    raw = _read_bytes()
    assert raw.count(b"\r") == 0, (
        f"the vendored doc carries {raw.count(b'\r')} CR bytes. It was copied "
        "through a text write rather than at byte level, which is the exact "
        "failure the channel's section 9 step 2 names."
    )


def test_the_declared_channel_version_parses_and_matches_the_pin() -> None:
    # Arm 4. The doc DECLARES its version in its own text; nothing outside the
    # bytes may assert it. Binding the parsed value to the digest is what makes
    # a byte change without a bump red.
    match = VERSION_LINE.search(_read_text())
    assert match is not None, "the vendored doc declares no CHANNEL_VERSION line"
    declared = int(match.group(1))
    assert declared == CHANNEL_VERSION, (
        f"the vendored doc declares CHANNEL_VERSION {declared} but this tree "
        f"pins {CHANNEL_VERSION}. A version bump and a re-pin travel together."
    )


def test_no_heading_carries_a_date() -> None:
    # Arm 5. This tree's dated-heading drift guard - tools/drift_guard.py guard
    # (g) - FAILS on a dated heading whose idiom its closed vocabulary does not
    # cover. A vendored doc cannot be reworded to satisfy it, so the arm proves
    # up front that the question never arises.
    text = _read_text()
    headings = _heading_lines(text)
    assert headings, "the vendored doc carries no headings at all; the arm read nothing"
    dated = [f"line {number}: {line}" for number, line in headings if _date_in(line)]
    assert dated == [], (
        "the vendored doc carries a dated heading, which this tree's "
        "dated-heading guard grades against a closed idiom vocabulary. The doc "
        f"cannot be reworded to satisfy it - the guard needs an exemption: {dated}"
    )

    # THE ORACLE LEG, optional by construction. The vocabulary above is a
    # TRANSCRIPTION, and a transcription that drifts from its original passes
    # while the guard it defends against fails. Where the guard is importable,
    # its own implementation is asked the same question about the same bytes.
    # Where it is not - another participating tree, or a trimmed checkout - the
    # portable leg above still ran and this leg simply does not.
    tools = str(REPO_ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from drift_guard import dated_headings  # noqa: PLC0415
    except ImportError:  # pragma: no cover - the portable path in a foreign tree
        return
    assert dated_headings(text) == [], (
        "the transcribed date vocabulary in this module says the doc has no "
        "dated heading and tools/drift_guard.py says it does. The transcription "
        "has drifted from the guard it exists to defend against."
    )


def test_every_repo_relative_path_resolves_and_no_file_line_is_cited() -> None:
    """Grade the document's filesystem citations, both halves.

    THE RESOLVING HALF CARRIES NO INDEPENDENT EVIDENCE, and this arm says so
    rather than advertising a property it cannot hold. The repo-relative
    population is exactly two tokens - the document's own path and the recorded
    non-resolver ``moon_sync_inbox/`` - so what resolves is the document naming
    ITSELF, which arm 1 already proves. See :data:`RESOLVED_REPO_PATHS`.

    THE ARM'S LIVE CONTENT is its other legs: the no-``file:line`` leg, the
    three separately counted bare-name populations, the non-resolver roster
    checked in both directions, and the unbackticked leg.
    """
    # Arm 6, both halves measured. The second half is what lets this tree's
    # docs-citation guard have nothing to say about the document.
    #
    # TWO MEASURED NARROWINGS of the population built below, recorded (CS-1095)
    # so a future re-pin sees them rather than rediscovering them:
    #   - :func:`_looks_like_a_path` drops any token containing a SPACE, so a
    #     backticked path with a space in it is invisible to this arm.
    #   - :data:`BACKTICKED` refuses a newline inside a token, so a path
    #     wrapped across a line break is invisible to it too.
    text = _read_text()

    pointers = FILE_LINE.findall(text)
    assert pointers == [], (
        f"the vendored doc cites a file:line pointer: {pointers}. The channel's "
        "own section 4 records why it does not - a line cite into a gitignored "
        "directory resolves in no tree at all."
    )

    candidates = [token for token in _quoted_tokens(text) if _looks_like_a_path(token)]
    assert candidates, "arm 6 found no path token at all; it graded nothing"

    repo_relative = sorted({t for t in candidates if "/" in t and t not in NON_REPO_PATHS})
    bare = sorted({t for t in candidates if "/" not in t and t not in NON_REPO_PATHS})

    # The bare-filename population is RECORDED, not resolved - and it is
    # recorded in THREE parts, because one pooled count would be satisfied by
    # its largest member while a single misfiled token went unmeasured. Each
    # part carries its own reason above.
    synthetic = sorted(t for t in bare if SYNTHETIC_MARKER in t)
    charter = sorted(t for t in bare if t == CROSS_REPO_CHARTER)
    provenance = sorted(set(bare) - set(synthetic) - set(charter))

    assert len(synthetic) == SYNTHETIC_EXAMPLE_CITES, (
        f"the grammar table's synthetic examples number {len(synthetic)}, not "
        f"{SYNTHETIC_EXAMPLE_CITES}: {synthetic}"
    )
    assert charter == [CROSS_REPO_CHARTER], (
        f"the cross-repo charter citation changed: {charter}. It is RC-relative "
        "and resolves nowhere in this tree; see CROSS_REPO_CHARTER above."
    )
    assert len(provenance) == PROVENANCE_NOTE_CITES, (
        f"the bare provenance-note citation count moved from "
        f"{PROVENANCE_NOTE_CITES} to {len(provenance)}: {provenance}"
    )
    assert len(synthetic) + len(charter) + len(provenance) == len(set(bare)), (
        "a bare filename the doc cites falls outside all three recorded "
        f"populations, so nothing grades it: {sorted(set(bare))}"
    )

    # A gitignored path is asked whether git IGNORES it, never whether it is on
    # disk - the second answer differs between the primary checkout and a
    # worktree and would make this arm report on the checkout it happens to run
    # in. git check-ignore exits 0 when the path IS ignored.
    #
    # THE TRAILING SLASH IS LOAD-BEARING AND WAS MEASURED, NOT ASSUMED. The
    # ignore rule is /moon_sync_inbox/, a DIRECTORY-ONLY pattern, and git can
    # only tell that a pathspec names a directory from the trailing slash or
    # from the path existing on disk. Strip the slash and check-ignore answers
    # from the filesystem instead of the rules: measured 5 of 5 runs exit 1 in a
    # worktree, where the directory is absent, and exit 0 in the primary, where
    # it is not - which is the exact checkout-dependence this arm exists to
    # remove. With the slash kept it is 0 in both.
    for token, reason in CHECKOUT_DEPENDENT_REPO_PATHS.items():
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", token],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        assert ignored.returncode == 0, (
            f"{token} is recorded as checkout-dependent because it is "
            f"gitignored - {reason} - but git does not ignore it here, so its "
            "presence has become a real finding rather than an artifact of "
            "which checkout is running this arm"
        )

    graded = [t for t in repo_relative if t not in CHECKOUT_DEPENDENT_REPO_PATHS]
    missing = sorted(t for t in graded if not (REPO_ROOT / t.rstrip("/")).exists())
    assert missing == sorted(UNRESOLVED_REPO_PATHS), (
        "the set of repo-relative paths the vendored doc names that do not "
        "resolve in this tree has changed. Each non-resolving member needs a "
        "recorded reason, and a member that starts resolving is a finding too. "
        f"measured={missing} recorded={sorted(UNRESOLVED_REPO_PATHS)}"
    )

    resolved = [t for t in graded if t not in UNRESOLVED_REPO_PATHS]
    assert resolved == RESOLVED_REPO_PATHS, (
        "the repo-relative paths the vendored doc names that DO resolve here "
        "have changed. This population is one self-reference by construction, "
        "so a new member means the document now points at something else in "
        f"this tree. measured={resolved} pinned={RESOLVED_REPO_PATHS}"
    )

    # The unbackticked leg. The doc quotes every path it names; asserting that
    # is what stops the backticked population from being a silent narrowing.
    unquoted = BACKTICKED.sub("", text)
    loose = {
        token
        for token in re.findall(r"\b[\w.\-]+/[\w.\-/]*", unquoted)
        if (REPO_ROOT / token.split("/")[0]).exists()
    }
    assert loose == set(), f"the doc names a repo-relative path outside backticks: {loose}"


def test_the_filename_variant_table_is_present_and_parses() -> None:
    # Arm 7. The table IS the grammar's test-vector source - there is no second
    # file carrying the vectors - so a table that stopped parsing would take
    # the vectors with it silently.
    text = _read_text()
    assert TABLE_HEADING in text, f"the vendored doc carries no {TABLE_HEADING!r} section"

    section = text.split(TABLE_HEADING, 1)[1]
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in section.splitlines()
        if line.startswith("|")
    ]
    assert rows, "the filename grammar table has no rows"

    header, separator, *body = rows
    assert header[0] == "Example", f"the table's first column is {header[0]!r}, not 'Example'"
    assert header[-1] == "Shape", f"the table's last column is {header[-1]!r}, not 'Shape'"
    assert len(header) == TABLE_COLUMNS, (
        f"the table declares {len(header)} columns, not {TABLE_COLUMNS}: {header}"
    )
    assert all(set(cell) <= set("-: ") for cell in separator), (
        f"the row under the table header is not a separator: {separator}"
    )

    assert len(body) == TABLE_ROWS, (
        f"the table carries {len(body)} vectors, not {TABLE_ROWS}: {[r[0] for r in body]}"
    )
    assert all(len(row) == TABLE_COLUMNS for row in body), (
        f"a table row is ragged: {[row for row in body if len(row) != TABLE_COLUMNS]}"
    )
    assert [row[-1] for row in body] == list(TABLE_SHAPES), (
        f"the table's shapes are {[row[-1] for row in body]}, not {list(TABLE_SHAPES)}"
    )
    verdicts = {row[1] for row in body}
    assert verdicts <= TABLE_VERDICTS, (
        f"the graded column carries a verdict outside {sorted(TABLE_VERDICTS)}: {verdicts}"
    )
    assert all(row[0].startswith("`") and row[0].endswith("`") for row in body), (
        f"a vector is not spelled as a literal filename: {[row[0] for row in body]}"
    )

    # THE CONTENT PIN, and the reason the shape checks above are not enough.
    # The roster's size is asserted against TABLE_ROWS first, so a roster that
    # lost a member cannot quietly agree with a table that lost the same one.
    assert len(TABLE_VECTORS) == TABLE_ROWS, (
        f"the pinned roster holds {len(TABLE_VECTORS)} vectors while TABLE_ROWS "
        f"says {TABLE_ROWS}; the roster and its size have drifted apart"
    )
    measured = [tuple(row) for row in body]
    assert measured == list(TABLE_VECTORS), (
        "the filename grammar table's CONTENT has moved off the pin. The table "
        "is the grammar's only test-vector source, so a mangled vector, a "
        "swapped pair or a flipped verdict changes what the channel's grammar "
        "is tested against with nothing else to catch it. Do NOT edit the "
        "document to get past this - see arm 2. "
        f"measured={measured} pinned={list(TABLE_VECTORS)}"
    )
