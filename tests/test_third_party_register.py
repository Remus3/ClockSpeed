#!/usr/bin/env python3
"""The third-party register, graded against what this tree actually vendors.

``THIRD_PARTY.md`` is the OWNER of the fact "what is vendored here and under
what licence" (``CLAUDE.md`` section 4). An owner file that denies the thing it
owns is worse than no owner at all, because every other file is instructed to
link to it rather than restate it - so the denial is the answer a reader gets.

THE DEFECT THIS MODULE WAS WRITTEN AGAINST, measured before the repair: the
register's Current state section asserted that zero files in this repository
were copied, adapted or derived from an external codebase, and its table
carried a ``(none vendored)`` placeholder row. ``docs/CHANNEL.md`` had been
vendored byte-identical from another repository under Apache-2.0 five days
earlier, recorded in ``docs/LEDGER.md`` under CS-1095 and attributed in
``CLAUDE.md``'s section 4 topology row - which is the WRONG owner for a licence
verdict. Both register claims were false, and a register nothing grades drifts
the day after it is written.

THE LOAD-BEARING ARM IS :func:`test_every_byte_pinned_vendored_file_is_listed`,
and its oracle is deliberately NOT this document. A file that is vendored is a
file whose bytes this tree may not author, which is why each one carries a
byte-pin module; :data:`BYTE_PIN_ROSTER` reads the path out of that module
rather than out of the register, so deleting the register's row cannot make the
arm agree with the deletion. The roster's LIMIT is stated rather than left to be
discovered: it names the pin modules by hand, so a vendoring that arrives with
no pin module and no roster entry is invisible here. That is a narrower claim
than "nothing else is vendored" and this module never makes the wider one.

THE PHRASE ARM IS A BACKSTOP, NOT THE GUARD. :data:`DENIAL_PATTERNS` is a closed
vocabulary of blanket denials, so a future denial worded outside it escapes.
:func:`test_the_denial_vocabulary_is_not_vacuous` exists because a regex that
matches nothing passes this kind of arm for exactly the wrong reason - it fires
each pattern at a string built to trip it, so the arm cannot be green because
the vocabulary is broken.

THE ATTRIBUTION CELLS ARE PINNED AS CONTENT, transcribed from ``CLAUDE.md``
section 4's topology row and the CS-1095 licence-gate entry in
``docs/LEDGER.md`` - the two places the facts were recorded before this file
owned them. They are pinned HERE rather than read from those files at runtime
because the whole point of the repair is that the register becomes the owner:
an arm that read the attribution back out of ``CLAUDE.md`` would make the
register's correctness depend on a row the merger may legitimately reduce to a
pointer.
"""

from __future__ import annotations

import importlib
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The register itself.
REGISTER = REPO_ROOT / "THIRD_PARTY.md"

#: The heading that opens the machine-graded table of vendored files. The
#: register's other table records items merely CONSIDERED, which name no file
#: and must not be swept into a path-resolution arm.
VENDORED_HEADING = "### Vendored files"

#: Byte-pin modules, mapped to the module-level name holding the pinned path.
#:
#: A VENDORED FILE IS ONE THIS TREE MAY NOT AUTHOR, so each one carries a module
#: that pins its bytes. Reading the path out of THAT module is what keeps the
#: listed-here arm independent of the document it grades. Hand-maintained, and
#: see the module docstring for what that does not cover.
BYTE_PIN_ROSTER: dict[str, str] = {"tests.test_channel_doc": "CHANNEL_DOC"}

#: A backticked token, which is how every path in this tree's docs is spelled.
BACKTICK_RE = re.compile(r"`([^`\n]+)`")

#: Blanket denials of vendoring. Matched against WHITESPACE-NORMALISED text,
#: because the register wraps its prose and the original false sentence spanned
#: two lines - a line-anchored search would have missed the defect this module
#: was written against.
DENIAL_PATTERNS = (
    re.compile(r"no third-party source is vendored", re.IGNORECASE),
    re.compile(r"zero files in this repository were copied", re.IGNORECASE),
    re.compile(r"\(none vendored\)", re.IGNORECASE),
    re.compile(r"nothing in this repository is vendored", re.IGNORECASE),
    re.compile(r"nothing is vendored", re.IGNORECASE),
)

#: Text built to trip every pattern above, so the vocabulary cannot rot silently.
DENIAL_PROBE = (
    "No third-party source is vendored in this project. Zero files in this "
    "repository were copied, adapted or derived from an external codebase. "
    "| (none vendored) | - | Nothing in this repository is vendored. "
    "Nothing is vendored."
)

#: Cells the ``docs/CHANNEL.md`` row must carry, transcribed from CLAUDE.md
#: section 4 and the CS-1095 gate entry in docs/LEDGER.md. Each is a fact a
#: garbled re-pin would lose: the grant, the holder, the upstream repository,
#: the gate record and the module that holds the bytes to the pin.
CHANNEL_ROW_FACTS = (
    "Apache-2.0",
    "`Moonbeam`",
    "`Remus3/Amberstone`",
    "CS-1095",
    "`tests/test_channel_doc.py`",
)

#: Seconds allowed for the one child this module spawns. An unbounded child
#: cannot fail the arm that owns it; it burns the job budget instead.
GIT_TIMEOUT = 30

#: The rows a markdown table spends before its body: the header and the
#: separator under it. Named rather than spelled twice, so the slice below and
#: the assertion above it cannot drift.
TABLE_PREAMBLE_ROWS = 2


def _register_text() -> str:
    """Return the register decoded as ASCII with newlines normalised to LF.

    Returns:
        The document text.
    """
    return REGISTER.read_bytes().decode("ascii").replace("\r\n", "\n")


def _flat(text: str) -> str:
    """Return ``text`` with every run of whitespace collapsed to one space.

    Args:
        text: Any document text.

    Returns:
        The single-spaced form, which is what a wrapped sentence must be
        matched against.
    """
    return re.sub(r"\s+", " ", text)


def _table_rows(text: str, heading: str) -> list[list[str]]:
    """Return the body rows of the first markdown table under ``heading``.

    Args:
        text: The whole document.
        heading: The exact heading line that opens the table's section.

    Returns:
        One list of stripped cells per body row, header and separator dropped.

    Raises:
        AssertionError: If the heading is absent or no table follows it.
    """
    assert heading in text, f"{REGISTER.name} carries no {heading!r} section"
    section = text.split(heading, 1)[1]
    rows: list[list[str]] = []
    for line in section.splitlines():
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif rows:
            break
    assert len(rows) >= TABLE_PREAMBLE_ROWS, (
        f"the table under {heading!r} has no header and separator"
    )
    return rows[TABLE_PREAMBLE_ROWS:]


def _listed_paths(text: str) -> list[str]:
    """Return the repo-relative path each vendored row names, in file order.

    Args:
        text: The whole document.

    Returns:
        The backticked token from column 0 of every vendored-files row.

    Raises:
        AssertionError: If a row's first cell carries no backticked token.
    """
    listed: list[str] = []
    for row in _table_rows(text, VENDORED_HEADING):
        quoted = BACKTICK_RE.findall(row[0])
        assert quoted, f"a vendored row names no backticked file: {row[0]!r}"
        listed.append(quoted[0])
    return listed


def _byte_pinned_paths() -> list[str]:
    """Return the repo-relative path each byte-pin module pins, sorted.

    Returns:
        POSIX-spelled, repo-relative paths.

    Raises:
        AssertionError: If a roster member is missing, names no such attribute,
            or pins a path that is absent or outside the repository.
    """
    pinned: list[str] = []
    for module_name, attribute in BYTE_PIN_ROSTER.items():
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:  # pragma: no cover - a deleted pin module
            raise AssertionError(
                f"{module_name} is rostered as the byte pin for a vendored file "
                f"and cannot be imported - ImportError on {exc.name!r}. A "
                "vendored file whose pin has gone is not a file that stopped "
                "being vendored."
            ) from exc
        path = getattr(module, attribute, None)
        assert isinstance(path, Path), (
            f"{module_name}.{attribute} is {path!r}, not the Path this roster reads"
        )
        assert path.is_file(), f"{module_name}.{attribute} pins {path}, which is not a file"
        pinned.append(path.resolve().relative_to(REPO_ROOT).as_posix())
    return sorted(pinned)


def test_the_vendored_files_table_parses_and_names_at_least_one_file() -> None:
    # Anti-vacuity for every arm below: each of them reads this table, and a
    # table that had stopped parsing would make all of them agree about nothing.
    listed = _listed_paths(_register_text())
    assert listed, (
        "the register's vendored-files table has no rows, so every arm that "
        "reads it is measuring an empty population"
    )


def test_every_byte_pinned_vendored_file_is_listed() -> None:
    # THE ARM THE MODULE EXISTS FOR. Its oracle is the pin module, not the
    # register, so deleting a row cannot make this agree with the deletion.
    pinned = _byte_pinned_paths()
    assert pinned, "the byte-pin roster is empty, so this arm graded nothing"
    listed = _listed_paths(_register_text())
    missing = sorted(path for path in pinned if path not in listed)
    assert missing == [], (
        "a file this tree byte-pins because it was VENDORED is absent from the "
        f"third-party register: {missing}. The register is the owner of what is "
        "vendored and under what licence; a vendored file it does not name is a "
        "licence obligation recorded nowhere."
    )


def test_the_register_makes_no_blanket_denial_while_a_file_is_vendored() -> None:
    # The backstop arm. It is conditional on there BEING a vendored file, so a
    # tree that genuinely vendors nothing is free to say so.
    pinned = _byte_pinned_paths()
    assert pinned, "the byte-pin roster is empty, so this arm graded nothing"
    flat = _flat(_register_text())
    denials = [pattern.pattern for pattern in DENIAL_PATTERNS if pattern.search(flat)]
    assert denials == [], (
        f"the register denies that anything is vendored - {denials} - while "
        f"{pinned} are vendored and byte-pinned. The owner file's answer is the "
        "answer every other file points at."
    )


def test_the_denial_vocabulary_is_not_vacuous() -> None:
    # A regex that matches nothing passes the arm above for the wrong reason.
    silent = [
        pattern.pattern for pattern in DENIAL_PATTERNS if not pattern.search(_flat(DENIAL_PROBE))
    ]
    assert silent == [], (
        f"these denial patterns match nothing even in the probe built to trip "
        f"them: {silent}. The arm that uses them would be green by construction."
    )


def test_every_file_the_register_lists_is_present_and_tracked() -> None:
    # The other direction. A register that lists a file the tree no longer
    # carries is as wrong as one that omits a file the tree does carry - and
    # "on disk" is not enough here, because an untracked file is not something
    # this repository distributes and so carries no redistribution obligation.
    listed = _listed_paths(_register_text())
    absent = sorted(path for path in listed if not (REPO_ROOT / path).is_file())
    assert absent == [], f"the register lists a vendored file that is not in the tree: {absent}"

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", *listed],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        timeout=GIT_TIMEOUT,
    )
    assert tracked.returncode == 0, (
        "the register lists a vendored file git does not track, so the licence "
        f"obligation it records attaches to nothing this repository ships: "
        f"{tracked.stderr.decode('ascii', 'replace').strip()}"
    )


def test_the_channel_doc_row_carries_its_upstream_and_its_grant() -> None:
    # Apache-2.0 section 4 asks a redistributor to retain the attribution. The
    # vendored bytes may not be edited to carry a notice, so the attribution
    # lives in this row - which makes the row's CONTENT the obligation, not its
    # presence. A shape-only arm would pass on a blanked row.
    rows = _table_rows(_register_text(), VENDORED_HEADING)
    channel = [row for row in rows if "docs/CHANNEL.md" in row[0]]
    assert len(channel) == 1, (
        f"the register carries {len(channel)} rows for docs/CHANNEL.md, not exactly one"
    )
    cells = " | ".join(channel[0])
    missing = [fact for fact in CHANNEL_ROW_FACTS if fact not in cells]
    assert missing == [], (
        f"the vendored row for docs/CHANNEL.md has lost part of its Apache-2.0 "
        f"attribution: {missing}. The byte-pinned file cannot carry a notice of "
        "its own, so this row IS the retained attribution."
    )
