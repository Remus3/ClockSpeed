"""CS-420 clause 4 - no oracle named in prose lacks a test, and no citation is dead.

WHY THIS IS NOT A LIST. The obvious way to write this clause is a literal in the
test - the oracle names, each asserted to have a test somewhere. That version
passes forever: a fourth oracle added to the prose never touches the literal, so
nothing goes red, and the clause ships as decoration. There is no list here. The
oracle-to-test mapping is written in the PROSE ITSELF as a citation, and this
module resolves it, so the prose is the only place the mapping exists and the
prose is what gets checked.

THE CITATION FORM (contract 1) is ``tests/<path>.py::<test_name>``, optionally
inside double backticks. ruff pins ``line-length = 100`` and a test name here
routinely exceeds it, so a citation may be BROKEN ACROSS LINES - and it breaks
immediately after an underscore, never mid-word. Normalisation strips the
leading ``#`` and the indentation from each line, then joins a line to the next
with NO separator when it ends with ``_`` and with a single space otherwise.
Citations in ``clockspeed/save/`` are wrapped that way today, so a normaliser
that skipped this step would silently under-count rather than fail loudly.

THE PARAGRAPH CLASSIFIER (contract 2). Inside a column-0 comment block, an
INDENTED paragraph whose first line is an all-caps heading followed by `` - ``
is an ORACLE entry; a NON-INDENTED paragraph is narrative framing. That
distinction is already load-bearing in the shipped file rather than invented
here. Both classes are asserted non-empty, which is the classifier's own
liveness control: deleting the commentary block, or reflowing it so the
indentation is lost, turns this module red instead of vacuously green.

THE CONTROL IS THE POINT. The third test runs the scanner over a corpus
authored in this file carrying a resolvable citation, a citation to a test NAME
that does not exist, a citation to a FILE that does not exist, a citation
wrapped at an underscore, and an oracle paragraph in the correct heading shape
with no citation at all. A scanner that returned nothing would pass the other
two tests silently, and fails this one. That is what stops those two from being
vacuous, and it needs no library, no game install and no save.

THE RESIDUAL, stated rather than implied. This is a heuristic over prose, not a
parser of intent, and it sees only oracles written in the shape it knows. A
fourth oracle written as an ordinary narrative paragraph - not indented, no
all-caps heading - is invisible to the classifier, and so is one written in
another module's docstring or in a markdown file. The oracle test stays GREEN in
every one of those cases while the clause it stands for is actually violated.
What is genuinely closed here is the shape the decode commentary already uses,
plus the guarantee that no citation anywhere under ``clockspeed/`` points at a
test that does not exist. Widening the heuristic is a separate item; implying
the gap is not there would be the same failure this module exists to prevent.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

#: A citation: a path under tests/ ending in .py, then "::", then a test name.
#: Applied to NORMALISED text, so a citation wrapped across lines matches here.
CITATION_RE = re.compile(r"(tests/[\w/]+\.py)::(\w+)")

#: A horizontal rule bracketing a comment block. Carries no prose, so it is
#: dropped before paragraphs are cut rather than being read as content.
_RULE_RE = re.compile(r"^#\s*-{3,}\s*$")

#: An oracle heading: all caps, then a spaced hyphen, then the entry's prose.
_ORACLE_HEAD_RE = re.compile(r"^([A-Z][A-Z0-9 /-]*?) - \S")

#: Columns of indent past the "#" that mark a paragraph as an oracle entry.
#: Narrative paragraphs in the shipped commentary sit at one, entries at three.
_ORACLE_INDENT = 2

RESOLVED = "resolved"
MISSING_FILE = "missing-file"
MISSING_TEST = "missing-test"


# ---------------------------------------------------------------------------
# Normalisation and citation extraction
# ---------------------------------------------------------------------------


def _decomment(line: str) -> str:
    """Strip the comment marker and the surrounding indentation from one line.

    Args:
        line: A raw source line, with or without a leading ``#``.

    Returns:
        The line's prose, with no comment marker and no leading or trailing
        whitespace. Docstring lines simply have no marker to remove, which is
        why the same normaliser serves comments and docstrings alike.
    """
    text = line.strip()
    if text.startswith("#"):
        text = text[1:].strip()
    return text


def normalise_lines(lines: Iterable[str]) -> str:
    """Join wrapped lines into one string under the contract-1 rule.

    A line ending in ``_`` is a citation broken mid-name, so the next line is
    appended with NO separator. Every other line break is ordinary wrapping and
    becomes a single space.

    Args:
        lines: Raw source lines, in order.

    Returns:
        One normalised string in which no citation is split.
    """
    joined = ""
    for raw in lines:
        text = _decomment(raw)
        if not joined:
            joined = text
        elif joined.endswith("_"):
            joined += text
        else:
            joined += " " + text
    return joined


def _defines(source: str, name: str) -> bool:
    """Report whether a module's source defines a function of a given name.

    Args:
        source: The module's full text.
        name: The function name to look for.

    Returns:
        True when a ``def <name>(`` appears at any indentation. The trailing
        parenthesis is required so that a citation of ``test_foo`` is not
        satisfied by an unrelated ``test_foo_bar``.
    """
    pattern = re.compile(r"^\s*def\s+" + re.escape(name) + r"\s*\(", re.MULTILINE)
    return pattern.search(source) is not None


def resolve(
    citations: Iterable[tuple[str, str]],
    sources: Mapping[str, str],
) -> dict[tuple[str, str], str]:
    """Resolve each citation against a table of test-module sources.

    Args:
        citations: ``(path, test_name)`` pairs as extracted from prose.
        sources: Maps a repo-relative POSIX path to that module's full text.
            Injected rather than read from disk so the control can supply a
            corpus with no filesystem involved.

    Returns:
        Each citation mapped to :data:`RESOLVED`, :data:`MISSING_FILE` when no
        such module is present, or :data:`MISSING_TEST` when the module exists
        but defines no test of that name.
    """
    verdicts: dict[tuple[str, str], str] = {}
    for path, name in citations:
        source = sources.get(path)
        if source is None:
            verdicts[path, name] = MISSING_FILE
        elif _defines(source, name):
            verdicts[path, name] = RESOLVED
        else:
            verdicts[path, name] = MISSING_TEST
    return verdicts


# ---------------------------------------------------------------------------
# Paragraph classification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Paragraph:
    """One paragraph of a column-0 comment block, already classified."""

    lineno: int
    indented: bool
    heading: str | None
    text: str

    @property
    def is_oracle(self) -> bool:
        """Whether this paragraph is an ORACLE entry under contract 2."""
        return self.indented and self.heading is not None

    @property
    def is_narrative(self) -> bool:
        """Whether this paragraph is narrative framing under contract 2."""
        return not self.indented

    @property
    def citations(self) -> list[tuple[str, str]]:
        """Citations appearing INSIDE this paragraph, wraps already rejoined."""
        return CITATION_RE.findall(self.text)


def comment_regions(source: str) -> list[list[tuple[int, str]]]:
    """Cut a module into maximal runs of column-0 comment lines.

    Args:
        source: A module's full text.

    Returns:
        One list of ``(line_number, raw_line)`` pairs per run, in file order.
    """
    regions: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    for number, line in enumerate(source.splitlines(), start=1):
        if line.startswith("#"):
            current.append((number, line))
        elif current:
            regions.append(current)
            current = []
    if current:
        regions.append(current)
    return regions


def _build_paragraph(lines: list[tuple[int, str]]) -> Paragraph:
    """Classify one paragraph from its lines.

    Args:
        lines: ``(line_number, raw_line)`` pairs, first line first.

    Returns:
        The classified paragraph. Indentation is measured on the first line
        only, which is where the heading sits.
    """
    number, first = lines[0]
    body = first[1:]
    indent = len(body) - len(body.lstrip(" "))
    head = _ORACLE_HEAD_RE.match(body.strip())
    return Paragraph(
        lineno=number,
        indented=indent >= _ORACLE_INDENT,
        heading=head.group(1) if head else None,
        text=normalise_lines(line for _, line in lines),
    )


def paragraphs_of(region: list[tuple[int, str]]) -> list[Paragraph]:
    """Split one comment region into classified paragraphs.

    Horizontal rules carry no prose and are dropped. A bare ``#`` ends the
    current paragraph.

    Args:
        region: ``(line_number, raw_line)`` pairs from :func:`comment_regions`.

    Returns:
        The region's paragraphs, in file order.
    """
    out: list[Paragraph] = []
    current: list[tuple[int, str]] = []
    for number, line in region:
        if _RULE_RE.match(line):
            continue
        if line[1:].strip():
            current.append((number, line))
        elif current:
            out.append(_build_paragraph(current))
            current = []
    if current:
        out.append(_build_paragraph(current))
    return out


def _sources_under(root: Path, subdir: str) -> dict[str, str]:
    """Read every module under a subdirectory into a path-to-text table.

    Args:
        root: Repository root.
        subdir: Directory beneath it to walk.

    Returns:
        Repo-relative POSIX paths mapped to module text.
    """
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted((root / subdir).rglob("*.py"))
    }


# ---------------------------------------------------------------------------
# The control corpus - authored here, never imported, names nothing real
# ---------------------------------------------------------------------------

_CONTROL_COMMENTARY = """\
# ---------------------------------------------------------------------------
# A synthetic commentary block, authored as a string in the test that uses it.
# It is never imported and it names no module that exists in this repository.
#
# THIS PARAGRAPH IS NARRATIVE. It opens in capitals, but it is NOT indented,
# so the classifier has to leave it out of the oracle set.
#
#   PLAIN CITATION - resolves against the synthetic source table.
#   tests/synthetic/test_alpha.py::test_plain_citation_resolves
#
#   WRAPPED CITATION - the name breaks immediately after an underscore, and
#   the normaliser has to rejoin it with no separator before it can resolve.
#   tests/synthetic/test_alpha.py::test_wrapped_
#   name_resolves
#
#   DEAD NAME - the module is present in the table, the test name is not.
#   tests/synthetic/test_alpha.py::test_no_such_test_here
#
#   DEAD FILE - no such module in the table at all.
#   tests/synthetic/test_missing.py::test_anything
#
#   UNCITED ORACLE - correct heading shape, correct indentation, and no
#   citation anywhere inside this paragraph. This is the fourth-oracle case
#   the whole control exists for.
# ---------------------------------------------------------------------------
"""

_CONTROL_SOURCES = {
    "tests/synthetic/test_alpha.py": (
        "def test_plain_citation_resolves() -> None:\n"
        "    assert True\n"
        "\n"
        "\n"
        "def test_wrapped_name_resolves() -> None:\n"
        "    assert True\n"
    ),
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_every_test_citation_in_the_package_resolves(repo_root: Path) -> None:
    sources = _sources_under(repo_root, "tests")
    citing: dict[tuple[str, str], list[str]] = {}

    for module in sorted((repo_root / "clockspeed").rglob("*.py")):
        text = normalise_lines(module.read_text(encoding="utf-8").splitlines())
        for cite in CITATION_RE.findall(text):
            citing.setdefault(cite, []).append(module.relative_to(repo_root).as_posix())

    assert citing, (
        "no citation of the form tests/<path>.py::<name> was found anywhere under "
        "clockspeed/. This test exists to RESOLVE those citations, so finding none "
        "means either the scanner has broken or every citation has been deleted. "
        "Passing on an empty scan is the vacuous green CS-420 exists to prevent."
    )

    verdicts = resolve(list(citing), sources)
    broken = {
        f"{path}::{name}": f"{verdict}, cited by {', '.join(citing[path, name])}"
        for (path, name), verdict in verdicts.items()
        if verdict != RESOLVED
    }
    assert not broken, (
        f"citations that name a test which does not exist: {broken}. A dead citation "
        "is worse than none: it reads as evidence that an oracle is machine-checked "
        "when nothing checks it."
    )


def test_every_oracle_named_in_the_decode_commentary_cites_a_test(repo_root: Path) -> None:
    source = (repo_root / "clockspeed" / "save" / "objects.py").read_text(encoding="utf-8")
    blocks = [paragraphs_of(region) for region in comment_regions(source)]
    carrying = [paragraphs for paragraphs in blocks if any(p.is_oracle for p in paragraphs)]

    assert carrying, (
        "no ORACLE paragraph was found in clockspeed/save/objects.py. The decode "
        "commentary has been deleted, moved, or reflowed so its entries are no "
        "longer indented under an all-caps heading. Either way the classifier is "
        "no longer reading the thing it was written to read."
    )

    for paragraphs in carrying:
        oracles = [p for p in paragraphs if p.is_oracle]
        narrative = [p for p in paragraphs if p.is_narrative]

        assert narrative, (
            f"the comment block at line {paragraphs[0].lineno} classified every "
            "paragraph as an oracle and none as narrative. The two classes are "
            "distinguished by indentation alone, so an all-oracle block means the "
            "classifier has stopped discriminating and its greens are worthless."
        )

        uncited = [f"{p.heading} (line {p.lineno})" for p in oracles if not p.citations]
        assert not uncited, (
            f"oracles named in prose with no test cited inside their own paragraph: "
            f"{uncited}. CS-420 clause 4 requires the paragraph that CLAIMS an oracle "
            "to name the test that re-derives it, in the citation form "
            "tests/<path>.py::<test_name>."
        )


def test_the_citation_scanner_catches_an_uncited_oracle_and_a_dead_citation() -> None:
    (region,) = comment_regions(_CONTROL_COMMENTARY)
    paragraphs = paragraphs_of(region)
    oracles = [p for p in paragraphs if p.is_oracle]
    narrative = [p for p in paragraphs if p.is_narrative]

    assert [p.heading for p in oracles] == [
        "PLAIN CITATION",
        "WRAPPED CITATION",
        "DEAD NAME",
        "DEAD FILE",
        "UNCITED ORACLE",
    ], "the classifier did not recover the control's oracle entries in order"

    assert narrative, "the classifier read the control's framing prose as oracles"

    verdicts = resolve([c for p in oracles for c in p.citations], _CONTROL_SOURCES)
    assert verdicts == {
        ("tests/synthetic/test_alpha.py", "test_plain_citation_resolves"): RESOLVED,
        ("tests/synthetic/test_alpha.py", "test_wrapped_name_resolves"): RESOLVED,
        ("tests/synthetic/test_alpha.py", "test_no_such_test_here"): MISSING_TEST,
        ("tests/synthetic/test_missing.py", "test_anything"): MISSING_FILE,
    }, "the scanner mis-resolved a citation, or lost the one wrapped at an underscore"

    assert [p.heading for p in oracles if not p.citations] == ["UNCITED ORACLE"], (
        "the scanner did not flag the oracle paragraph that cites no test. Without "
        "this the other two tests in this module could pass by finding nothing."
    )
