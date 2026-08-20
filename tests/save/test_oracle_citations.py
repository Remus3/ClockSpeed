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
routinely exceeds it, so a citation may be BROKEN ACROSS LINES. Normalisation
strips the leading ``#`` and the indentation from each line, then joins a line
to the next with NO separator when it ends with ``_`` and with a single space
otherwise. That rejoins a break taken immediately after an underscore, which is
how the citations in ``clockspeed/save/`` are wrapped today.

A BREAK TAKEN ANYWHERE ELSE IS NOT NORMALISED - IT IS REPORTED. Chasing every
possible wrap point is unbounded, and the earlier version of this module simply
did not match those citations, which is the silent under-count its own prose
warned against: a break after the ``::``, after a ``/`` inside the path, after
the ``.`` in ``.py``, or before the ``::`` each removed the citation from the
scan and left the suite green. The rule now is loud instead. Every ``::`` in
scanned text must be covered by a complete citation match; a ``::`` that is not,
but that carries the token ``tests`` within :data:`_WRAP_LOOKBACK_TOKENS`
whitespace-separated tokens before it, is CITATION-SHAPED AND UNREADABLE and is
reported as an error. The token window is what bounds the guess: each wrap
inserts at most one space, so a citation broken twice is still recognised, and a
``::`` further than that from any ``tests`` token is taken to be ordinary prose -
a reST literal-block marker or a scope operator - and left alone.

THE PARAGRAPH CLASSIFIER (contract 2). Inside a column-0 comment block, an
INDENTED paragraph is an ORACLE entry and a NON-INDENTED paragraph is narrative
framing. That distinction is already load-bearing in the shipped file rather
than invented here. INDENTATION ALONE DECIDES, and the all-caps heading is a
LABEL for the failure message, never a gate. It used to be a gate, and that
made the classifier a partial function with a silent third bucket: a paragraph
indented like an entry but headed ``Fourth oracle`` rather than ``FOURTH
ORACLE`` was neither oracle nor narrative, so its citation was never required.
The shipped commentary carried such a paragraph, headed with a comma the old
regex rejected, and deleting its citation was invisible. That heading has since
been rewritten, so the live example is the control corpus rather than the
shipped file - see :data:`_CONTROL_HEADING_CASES`. The classifier
is now TOTAL: every paragraph is an oracle or narrative, never neither. Both
classes are asserted non-empty, which is the classifier's own liveness control:
deleting the commentary block, reflowing it so the indentation is lost, or
indenting all of it turns this module red instead of vacuously green.

RESOLUTION IS SYNTACTIC, NOT TEXTUAL (contract 3). A cited name resolves when
the cited module DEFINES a function of that name at MODULE SCOPE, read from
:func:`ast.parse`. Module scope is the whole of it because the citation form
carries one ``::``, and a pytest node id with one ``::`` can only address a
module-level function. The previous version matched ``def <name>(`` as text,
which a ``def`` inside a triple-quoted string satisfies - and modules under
``tests/`` do carry such lines - so a citation could resolve against a test
that does not exist. ``ast.parse`` never executes the module, which is why this
is not collection-based: importing a real test module could open a save, and
non-negotiable 11 puts that out of reach for a lint.

THE CONTROL IS THE POINT. The filesystem-free tests run the scanner over corpora
authored in this file: a resolvable citation, a citation to a test NAME that does
not exist, a citation to a FILE that does not exist, a citation wrapped at an
underscore, oracle paragraphs with no citation at all in both heading cases, a
``def`` that exists only inside a string, a module that does not parse, and the
same citation written in every wrap style below. A scanner that returned nothing would
pass the package-wide tests silently and fails these. That is what stops the
package-wide tests from being vacuous, and it needs no library, no game install
and no save.

THE PACKAGE SCAN IS SCOPED TO ``clockspeed/`` ON PURPOSE. The control corpora
below contain literal citation text, and they are under ``tests/``. Widening the
scan to the repository would turn this file's own deliberately-broken fragments
into failures, so the scan stays scoped and the corpora stay inert.

THE GUARANTEE, stated as what the code delivers. For every ``::`` under
``clockspeed/``: it is either part of a citation naming a module-scope function
that the cited module really defines, or it is reported. Nothing citation-shaped
under ``clockspeed/`` is skipped in silence. Inside ``clockspeed/save/objects.py``
every indented paragraph of a column-0 comment block that holds any indented
paragraph cites a test.

THE RESIDUAL, stated rather than implied. This is a heuristic over prose, not a
parser of intent.

- An oracle written as an ordinary NON-INDENTED paragraph is narrative to the
  classifier, and so is one written in another module's docstring or in a
  markdown file. Those stay invisible.
- A citation broken mid-name at a NON-underscore boundary yields a truncated
  name. That is normally loud, because the truncation does not resolve - but if
  the truncated prefix happens to name a real test, it resolves against the
  WRONG test and says nothing.
- A wrap that splits the ``::`` itself leaves no ``::`` in the normalised text
  and is not detected. A rule anchored on ``.py:`` was tried and rejected: the
  shipped corpus writes ``chunks.py:`` in ordinary prose, so the rule would be
  red on correct code, which is worse than the gap it closes.
- Resolution is by NAME. A citation is satisfied by a stub that asserts nothing;
  this module checks that the test exists, never that it is worth anything.

Widening any of these is a separate item. Implying the gaps are not there would
be the same failure this module exists to prevent.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

#: A citation: a path under tests/ ending in .py, then "::", then a test name.
#: Applied to NORMALISED text, so a citation wrapped at an underscore matches.
CITATION_RE = re.compile(r"(tests/[\w/]+\.py)::(\w+)")

#: A horizontal rule bracketing a comment block. Carries no prose, so it is
#: dropped before paragraphs are cut rather than being read as content.
_RULE_RE = re.compile(r"^#\s*-{3,}\s*$")

#: An oracle heading: a word, then a spaced hyphen, then the entry's prose.
#: Case-insensitive by design - see contract 2. This names a paragraph in a
#: failure message and does NOT decide whether the paragraph is an oracle.
_ORACLE_HEAD_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 /-]*?) - \S")

#: Columns of indent past the "#" that mark a paragraph as an oracle entry.
#: Narrative paragraphs in the shipped commentary sit at one, entries at three.
_ORACLE_INDENT = 2

#: How much of a paragraph's text labels it when it carries no heading.
_LABEL_WIDTH = 48

#: The citation separator. Every occurrence of it in scanned text is accounted
#: for: read as part of a citation, or reported as unreadable.
_SEPARATOR = "::"

#: The token that makes an unmatched separator CITATION-SHAPED rather than
#: ordinary prose, sought within _WRAP_LOOKBACK_TOKENS tokens before it.
_CITATION_ANCHOR = "tests"

#: How many whitespace-separated tokens before a separator are searched for the
#: anchor. Each wrap inserts at most one space, so this bounds how many broken
#: wrap points are still recognised as one citation - two, plus the token the
#: separator itself sits in.
_WRAP_LOOKBACK_TOKENS = 3

#: How many tokens after a separator are quoted back in a failure message.
_FRAGMENT_TAIL_TOKENS = 2

RESOLVED = "resolved"
MISSING_FILE = "missing-file"
MISSING_TEST = "missing-test"
UNPARSEABLE = "unparseable-module"


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
    becomes a single space. A citation broken at any other point is NOT rejoined
    here - :func:`unreadable_citation_fragments` reports it instead.

    Args:
        lines: Raw source lines, in order.

    Returns:
        One normalised string in which a citation wrapped at an underscore is
        whole again.
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


def unreadable_citation_fragments(text: str) -> list[str]:
    """Report every citation-shaped separator that is not part of a citation.

    This is the loud half of contract 1. A citation wrapped anywhere other than
    an underscore survives normalisation as a separator with a broken path or a
    detached name around it, which :data:`CITATION_RE` cannot match. Rather than
    let it vanish from the scan, it is returned here so the caller can fail.

    Args:
        text: Normalised text, as produced by :func:`normalise_lines`.

    Returns:
        One human-readable fragment per unreadable separator, in text order,
        quoting the tokens either side so the wrap point is visible. Empty when
        every separator in the text is part of a whole citation.
    """
    whole = [match.span() for match in CITATION_RE.finditer(text)]
    fragments: list[str] = []
    for hit in re.finditer(re.escape(_SEPARATOR), text):
        if any(start <= hit.start() and hit.end() <= end for start, end in whole):
            continue
        before = " ".join(text[: hit.start()].split()[-_WRAP_LOOKBACK_TOKENS:])
        if _CITATION_ANCHOR not in before:
            continue
        after = " ".join(text[hit.end() :].split()[:_FRAGMENT_TAIL_TOKENS])
        fragments.append(f"{before}{_SEPARATOR}{after}")
    return fragments


def module_scope_functions(source: str) -> frozenset[str]:
    """Names of the functions a module defines at module scope.

    Args:
        source: The module's full text.

    Returns:
        Every module-level ``def`` and ``async def`` name. Read from the syntax
        tree, so a ``def`` inside a string literal is not one, and a nested or
        method definition is not one either - a pytest node id carrying a single
        ``::`` can only address a module-level function.

    Raises:
        SyntaxError: If the source does not parse.
    """
    return frozenset(
        node.name
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    )


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
        such module is present, :data:`MISSING_TEST` when the module exists but
        defines no module-scope function of that name, or :data:`UNPARSEABLE`
        when the module does not parse and the question cannot be answered.
    """
    defined: dict[str, frozenset[str] | None] = {}
    verdicts: dict[tuple[str, str], str] = {}
    for path, name in citations:
        source = sources.get(path)
        if source is None:
            verdicts[path, name] = MISSING_FILE
            continue
        if path not in defined:
            try:
                defined[path] = module_scope_functions(source)
            except SyntaxError:
                defined[path] = None
        names = defined[path]
        if names is None:
            verdicts[path, name] = UNPARSEABLE
        elif name in names:
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
        """Whether this paragraph is an ORACLE entry under contract 2.

        Indentation alone. The heading is a label, not a gate, so a paragraph
        laid out like an entry cannot escape the citation requirement on the
        letter case of its first words.
        """
        return self.indented

    @property
    def is_narrative(self) -> bool:
        """Whether this paragraph is narrative framing under contract 2."""
        return not self.indented

    @property
    def label(self) -> str:
        """A short name for this paragraph, for failure messages only."""
        if self.heading is not None:
            return self.heading
        return self.text[:_LABEL_WIDTH].rstrip()

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
# The control corpora - authored here, never imported, naming nothing real
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
#
#   Uncited lower case - indented exactly like the entry above and differing
#   from it only in the case of its heading, which is the likeliest ACCIDENTAL
#   escape and the one contract 2 was widened to catch.
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

#: One dead citation written several ways, each flagged with whether contract 1
#: can read it. The unreadable ones are the styles that used to vanish silently.
_WRAP_STYLES: Mapping[str, tuple[list[str], bool]] = {
    "one-line": (["# tests/synthetic/test_alpha.py::test_name"], True),
    "after-underscore": (["# tests/synthetic/test_alpha.py::test_na_", "# me_here"], True),
    "after-colons": (["# tests/synthetic/test_alpha.py::", "# test_name"], False),
    "after-slash-root": (["# tests/", "# synthetic/test_alpha.py::test_name"], False),
    "after-slash-mid": (["# tests/synthetic/", "# test_alpha.py::test_name"], False),
    "after-dot": (["# tests/synthetic/test_alpha.", "# py::test_name"], False),
    "before-colons": (["# tests/synthetic/test_alpha.py", "# ::test_name"], False),
}

#: Prose carrying a separator that is NOT citation-shaped. None may be
#: reported, or the rule would be red on correct code. The last case is the
#: one that pins the WINDOW rather than the anchor: it does mention tests, but
#: far enough back that the separator is plainly not part of a citation.
_NON_CITATION_SEPARATORS = {
    "rest-literal-block": ["# the shape is as follows::", "# a thing"],
    "scope-operator": ["# FProperty::Serialize walks the tag before the value"],
    "tests-far-from-separator": [
        "# the tests in this module are listed in the order the walker visits",
        "# them, and the literal block below is introduced as follows::",
        "# a thing",
    ],
}

#: A module whose only matching ``def`` is inside a string literal. Textual
#: resolution accepts this; syntactic resolution does not.
_CONTROL_GHOST_SOURCE = '''\
_DOC = """
def test_only_inside_a_string() -> None:
    pass
"""
'''

#: A module defining the names only as a method and as a nested function.
#: Neither is addressable by a node id carrying a single "::", so neither may
#: resolve. This is what pins resolution to MODULE scope rather than any scope.
_CONTROL_NESTED_SOURCE = """\
class TestThing:
    def test_only_a_method(self) -> None:
        pass


def _wrapper() -> None:
    def test_only_nested() -> None:
        pass
"""

#: A module that does not parse, so the question cannot be answered at all.
_CONTROL_BROKEN_SOURCE = "def test_unfinished(\n"

#: Paragraphs differing only in indentation and heading. This is the control
#: that fails if contract 2 is reverted to gating on a heading at all, or on an
#: ALL-CAPS one, or if the indent threshold is narrowed past the shallowest
#: entry. The third entry carries NO heading the regex can match - a comma
#: stops it before any spaced hyphen - which is the exact shape of the shipped
#: paragraph that used to be classified as neither oracle nor narrative.
_CONTROL_HEADING_CASES = """\
# ---------------------------------------------------------------------------
# Narrative framing at column zero.
#
#   ALL CAPS HEADING - indented, uncited, and caught before this widening too.
#
#   Sentence case heading - indented and uncited, and it used to escape.
#
#   No heading here, the comma blocks the regex.
#
#  Two spaces of indent is still an entry.
#
# Non-indented heading - narrative, and it must stay out of the oracle set.
# ---------------------------------------------------------------------------
"""


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


def test_no_citation_under_the_package_is_too_broken_to_read(repo_root: Path) -> None:
    unreadable: dict[str, list[str]] = {}
    for module in sorted((repo_root / "clockspeed").rglob("*.py")):
        text = normalise_lines(module.read_text(encoding="utf-8").splitlines())
        found = unreadable_citation_fragments(text)
        if found:
            unreadable[module.relative_to(repo_root).as_posix()] = found

    assert not unreadable, (
        f"citation-shaped text the scanner could not read: {unreadable}. Contract 1 "
        "rejoins a citation broken immediately after an underscore and nothing else, "
        "so a break taken at the '::', at a '/' inside the path, or at the '.' in "
        "'.py' leaves a citation that no longer matches. Reporting it is the point: "
        "the alternative is that the oracle drops out of the scan and the suite goes "
        "green having checked one citation fewer than it did before."
    )


def test_every_oracle_named_in_the_decode_commentary_cites_a_test(repo_root: Path) -> None:
    source = (repo_root / "clockspeed" / "save" / "objects.py").read_text(encoding="utf-8")
    blocks = [paragraphs_of(region) for region in comment_regions(source)]
    carrying = [paragraphs for paragraphs in blocks if any(p.is_oracle for p in paragraphs)]

    assert carrying, (
        "no ORACLE paragraph was found in clockspeed/save/objects.py. The decode "
        "commentary has been deleted, moved, or reflowed so its entries are no "
        "longer indented. Either way the classifier is no longer reading the thing "
        "it was written to read."
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

        uncited = [f"{p.label} (line {p.lineno})" for p in oracles if not p.citations]
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

    assert [p.label for p in oracles] == [
        "PLAIN CITATION",
        "WRAPPED CITATION",
        "DEAD NAME",
        "DEAD FILE",
        "UNCITED ORACLE",
        "Uncited lower case",
    ], "the classifier did not recover the control's oracle entries in order"

    assert narrative, "the classifier read the control's framing prose as oracles"

    verdicts = resolve([c for p in oracles for c in p.citations], _CONTROL_SOURCES)
    assert verdicts == {
        ("tests/synthetic/test_alpha.py", "test_plain_citation_resolves"): RESOLVED,
        ("tests/synthetic/test_alpha.py", "test_wrapped_name_resolves"): RESOLVED,
        ("tests/synthetic/test_alpha.py", "test_no_such_test_here"): MISSING_TEST,
        ("tests/synthetic/test_missing.py", "test_anything"): MISSING_FILE,
    }, "the scanner mis-resolved a citation, or lost the one wrapped at an underscore"

    assert [p.label for p in oracles if not p.citations] == [
        "UNCITED ORACLE",
        "Uncited lower case",
    ], (
        "the scanner did not flag both oracle paragraphs that cite no test. Without "
        "this the package-wide tests could pass by finding nothing."
    )


def test_no_wrap_style_lets_a_citation_pass_unread() -> None:
    silent: list[str] = []
    misjudged: list[str] = []
    unactionable: list[str] = []
    for style, (lines, readable) in _WRAP_STYLES.items():
        text = normalise_lines(lines)
        found = CITATION_RE.findall(text)
        fragments = unreadable_citation_fragments(text)
        if not found and not fragments:
            silent.append(style)
        if readable and (not found or fragments):
            misjudged.append(f"{style} should be read whole")
        if not readable and not fragments:
            misjudged.append(f"{style} should be reported unreadable")
        if not readable and not all(_CITATION_ANCHOR in f and "test_name" in f for f in fragments):
            unactionable.append(f"{style} -> {fragments}")

    assert not silent, (
        f"these wrap styles make a citation INVISIBLE - neither read nor reported: "
        f"{silent}. Every one of them is the same dead citation, so a scan that is "
        "silent on any of them under-counts and goes green, which is exactly the "
        "failure contract 1 names."
    )
    assert not misjudged, (
        f"a wrap style was classified the wrong way: {misjudged}. A readable style "
        "must produce a whole citation and no fragment; a broken one must produce a "
        "fragment. Losing either direction reopens the escape."
    )
    assert not unactionable, (
        f"a reported fragment did not quote both ends of the citation: {unactionable}. "
        "The report is the whole remedy for a wrap this module refuses to guess at, so "
        "one that does not show the author which citation broke is not a remedy."
    )


def test_prose_that_merely_contains_a_separator_is_not_reported() -> None:
    reported = {
        label: unreadable_citation_fragments(normalise_lines(lines))
        for label, lines in _NON_CITATION_SEPARATORS.items()
        if unreadable_citation_fragments(normalise_lines(lines))
    }
    assert not reported, (
        f"ordinary prose was reported as an unreadable citation: {reported}. The "
        "anchor window is what separates a broken citation from a reST literal "
        "block or a scope operator, and a rule that is red on correct code is a "
        "rule someone will delete."
    )


def test_an_indented_paragraph_is_an_oracle_whatever_the_heading_case() -> None:
    (region,) = comment_regions(_CONTROL_HEADING_CASES)
    paragraphs = paragraphs_of(region)

    assert [p.label for p in paragraphs if p.is_oracle] == [
        "ALL CAPS HEADING",
        "Sentence case heading",
        "No heading here, the comma blocks the regex.",
        "Two spaces of indent is still an entry.",
    ], (
        "an indented paragraph was not classified as an oracle. Missing the "
        "sentence-case one means contract 2 has been reverted to gating on an "
        "ALL-CAPS heading; missing the comma one means it has been reverted to "
        "gating on a heading at all, which is the shape that once left a real "
        "paragraph of the shipped commentary in neither class; missing the "
        "two-space one means the indent threshold has been narrowed past the "
        "shallowest indent an entry may use. Each reopens an uncited oracle."
    )

    assert [p.label for p in paragraphs if p.is_narrative] == [
        "Narrative framing at column zero.",
        "Non-indented heading",
    ], "the classifier moved a non-indented paragraph into the oracle set"

    assert all(p.is_oracle != p.is_narrative for p in paragraphs), (
        "the classifier is not total: a paragraph was neither oracle nor narrative. "
        "That silent third bucket is what let an indented paragraph whose heading "
        "the regex rejected escape the citation requirement entirely."
    )


def test_a_def_inside_a_string_literal_does_not_resolve_a_citation() -> None:
    cite = ("tests/synthetic/test_ghost.py", "test_only_inside_a_string")
    verdicts = resolve([cite], {cite[0]: _CONTROL_GHOST_SOURCE})
    assert verdicts == {cite: MISSING_TEST}, (
        "a def that exists only inside a string literal satisfied the resolver. "
        "Resolution is syntactic under contract 3 precisely because modules under "
        "tests/ do carry such lines, so a textual match can certify a test that "
        "pytest would never collect."
    )


def test_a_method_or_a_nested_def_does_not_resolve_a_citation() -> None:
    path = "tests/synthetic/test_nested.py"
    cites = [(path, "test_only_a_method"), (path, "test_only_nested")]
    verdicts = resolve(cites, {path: _CONTROL_NESTED_SOURCE})
    assert verdicts == dict.fromkeys(cites, MISSING_TEST), (
        "a method or a nested function satisfied a citation. The citation form "
        "carries one '::', and a pytest node id with one '::' addresses a "
        "module-level function only, so resolving against any scope certifies a "
        "node id that does not exist."
    )


def test_a_module_that_does_not_parse_is_reported_rather_than_resolved() -> None:
    cite = ("tests/synthetic/test_broken.py", "test_unfinished")
    verdicts = resolve([cite], {cite[0]: _CONTROL_BROKEN_SOURCE})
    assert verdicts == {cite: UNPARSEABLE}, (
        "a module that does not parse did not report UNPARSEABLE. Resolution reads "
        "the syntax tree, so a module it cannot parse is a question it cannot "
        "answer, and answering it anyway in either direction would be a guess."
    )


# ---------------------------------------------------------------------------
# CS-471 - THIS MODULE'S LIBRARY REACH, DECLARED.
#
# The guard is owned by ``test_properties`` and applied across this package by
# the suite-wide test that lives beside it, which walks the package directory
# rather than waiting to be called. Before CS-471 this module touched a library
# primitive while declaring no reach at all, and the suite had no check that
# would say so.
#
# The wording here is deliberately free of the CS-420 quantifier vocabulary,
# because two modules carrying this block sit inside that fence.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches.
_GRADED_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})

#: Touches a primitive WITHOUT consuming a real save path, name to why.
#: Asserted still reaching, so a stale exemption reddens the guard.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType(
    {
        "_sources_under": (
            "rglob over THIS REPO's own tracked sources under the project "
            "root, never a save directory and never the account directory "
        ),
        "test_a_def_inside_a_string_literal_does_not_resolve_a_citation": (
            "matched by NAME and not by a filesystem call: it uses this "
            "module's own citation resolver, which is spelled resolve and "
            "takes an injected mapping of module text. It opens no file and "
            "touches no path at all "
        ),
        "test_a_method_or_a_nested_def_does_not_resolve_a_citation": (
            "matched by NAME and not by a filesystem call: it uses this "
            "module's own citation resolver, which is spelled resolve and "
            "takes an injected mapping of module text. It opens no file and "
            "touches no path at all "
        ),
        "test_a_module_that_does_not_parse_is_reported_rather_than_resolved": (
            "matched by NAME and not by a filesystem call: it uses this "
            "module's own citation resolver, which is spelled resolve and "
            "takes an injected mapping of module text. It opens no file and "
            "touches no path at all "
        ),
        "test_every_test_citation_in_the_package_resolves": (
            "rglob over THIS REPO's own tracked sources under the project "
            "root, and a resolve that is this module's own citation "
            "resolver over injected text rather than a filesystem call "
        ),
        "test_no_citation_under_the_package_is_too_broken_to_read": (
            "rglob over THIS REPO's own tracked sources under the project "
            "root, never a save directory and never the account directory "
        ),
        "test_the_citation_scanner_catches_an_uncited_oracle_and_a_dead_citation": (
            "matched by NAME and not by a filesystem call: it uses this "
            "module's own citation resolver, which is spelled resolve and "
            "takes an injected mapping of module text. It opens no file and "
            "touches no path at all "
        ),
    }
)
