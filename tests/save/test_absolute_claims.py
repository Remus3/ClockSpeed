"""CS-420 - an unbounded claim in the fenced prose names a test, or it goes.

WHY A SECOND FENCE STANDS BESIDE ``test_oracle_citations``. That module asks
whether an ORACLE named in prose cites a test, and ADR 0008 scopes its rule to
DETECTION claims - sentences about which test reddens under which fault. The
sentence that reopened CS-420 was not one of those. ``IT NEVER RAISES`` is a
claim about RUNTIME BEHAVIOUR, so a detection-only fence does not reach it, and
``test_the_scanner_reddens_on_a_reinserted_absolute`` is where that exact
string is measured caught. The wider class is what this module fences: prose
carrying an UNBOUNDED QUANTIFIER.

THE RULE (contract 1). A sentence in the prose of a module named in
:data:`FENCED_MODULES` that carries such a quantifier has to name a test, in a
form :func:`backing_citations` can resolve. A sentence that does not is
deleted, or narrowed until the quantifier is gone. Those are the two
dispositions, and THERE IS NO REGISTER OF PARDONS. An allowlist of exempted
sentences is the artifact that rots - four rounds of hand repair on the fenced
module, each shipping a fresh false sentence, are what that rot looks like, and
a list of forgiven sentences would have hidden the lot.

THE MARKER SET IS A LIST TOO, AND ITS FAILURE DIRECTION IS THE OPPOSITE ONE.
:data:`ABSOLUTE_PATTERNS` is hand-written, so a sentence phrased around a
marker absent from it passes unread. That is UNDER-detection: widening the set
makes the fence stricter, and no entry in it forgives a sentence. An exemption
list fails the other way, which is why one is here and one is banned.

TWO CITATION FORMS RESOLVE (contract 2), both syntactically, both by importing
``test_oracle_citations`` rather than transcribing it - a third copy of that
resolver would be a third place to get it subtly wrong.

- A FULL citation, ``tests/<path>.py::<test_name>``, resolves against the cited
  module. Its form is unambiguous, so a dead one is reported as an error by
  :func:`dead_full_citations`.
- A LOCAL citation, a double-backticked ``test_name``, resolves against the
  module-scope functions of the module the sentence sits in. Its form is
  ambiguous - ``test_properties`` is a MODULE written the same way - so one
  that does not resolve is read as ordinary prose rather than reported. It
  simply fails to back the sentence it sits in.

WHAT THIS BUYS, STATED AT ITS REAL STRENGTH RATHER THAN AT A REASSURING ONE
(contract 3). A resolving citation proves the named test EXISTS. It does NOT
prove that test BACKS the sentence: resolution is by name, and a stub that
asserts zero satisfies it. What the fence delivers is that the falsification
surface becomes LOCAL AND NAMED - a reader checks the claim by reading one
named test instead of by re-deriving the whole suite. That is strictly weaker
than "established by execution", and writing the reassuring version of this
paragraph is the precise failure CS-420 exists to stop.

THE PARAGRAPH REFERENCE (contract 4) closes a gap this project measured rather
than guessed at. ``test_oracle_citations`` resolves ``tests/<path>.py::<name>``
and does not resolve a paragraph named by its opening words, so when ``662432d``
renamed the ``objects.py`` paragraph that two of its own sentences quoted, both
quotes died and the suite stayed green. A reference of the form ``paragraph ...
beginning `<text>` `` now has to prefix-match a real prose paragraph somewhere
under ``clockspeed/`` or ``tests/``. The anchor token bounds the guess, on the
same reasoning as contract 1 of ``test_oracle_citations``: ``synthetic.py``
writes "literal beginning ``Clockspeed``" about a base64url literal, and a rule
firing on that would be red against correct prose.

WHAT COUNTS AS PROSE (contract 5) is three kinds, and the third was added
after measuring what excluding it cost. A DOCSTRING and a COMMENT are obvious.
An ASSERT MESSAGE is prose too: a reader reads it as a statement about the
current tree, which is ADR 0008's own test for living text, and leaving it out
would leave a place to write a banned sentence that this fence does not read -
the one thing ADR 0008's Consequences say the rule must deny. It is not a
theoretical hole. The second of the two quotations that ``662432d`` killed sits
in an assert message, and a docstring-and-comment scan reported one of the two
and passed.

A STRING LITERAL USED AS DATA IS NOT PROSE, and that line is drawn by AST
POSITION rather than by a scope rule. The assert message is reached through
``ast.Assert.msg``; a module-level assignment is reached by neither route. That
is what keeps the control corpora below INERT BY CONSTRUCTION - they are
assignments - and a ``#`` inside one is not a comment either, because comments
come from :mod:`tokenize`.

THE CONTROLS ARE THE POINT, because a scanner returning zero findings would
pass the fenced scan in silence. They need no filesystem and no game.
:func:`test_prose_is_read_from_the_three_kinds_and_not_from_a_data_literal`
holds the extraction contract down at both ends: each kind is read, and an
assignment is not.

THE RESIDUAL, NAMED RATHER THAN IMPLIED AWAY, past the strength limit already
stated in contract 3:

- THE SCAN IS SCOPED to :data:`FENCED_MODULES`. ``clockspeed/save/objects.py``
  carries prose of the same class and is NOT fenced, because its
  ``_TAG_EXTRA_STRINGS`` docstring is CS-422's to repair and a fence that
  reddens on another item's file would be reverted rather than obeyed. ADR 0008
  scopes its own mechanical fence the same way and calls widening it separate
  work. No claim in this module covers that file.
- A SYNONYM ESCAPES, and this is the residual most likely to be mistaken for a
  stronger result than it is. Swapping a universal determiner for a
  distributive one - "each" in place of the listed marker - satisfies the fence
  and changes no meaning. Where a swap like that was the whole of a repair,
  what was bought is that the phrasing no longer reads as a standing universal,
  and that is all. Where a sentence was DELETED or made to name a test, more
  was bought. The marker set is a floor on what may be written, not evidence
  that the surviving prose is true.
- THE SENTENCE SPLIT IS A HEURISTIC over a period followed by whitespace. A bad
  split shortens a sentence, which can separate a marker from the citation that
  backs it. That direction over-reports and is loud; it does not hide a claim.
- A MARKER INSIDE A QUOTED FRAGMENT still counts. A sentence quoting a banned
  phrase in order to ban it has to cite a test like any other, which is a cost
  paid to keep the rule free of a judgement call about intent.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from tests.save import test_oracle_citations as citations

# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

#: Modules whose prose this fence governs, as repo-relative POSIX paths.
#:
#: The fenced module is CS-420's subject. This module is fenced too, and that
#: is not decoration: a fence written in prose that would fail itself is a
#: fence its author did not believe. Widening the tuple is how the rule spreads;
#: see the scoping residual in the module docstring for why it stops here.
FENCED_MODULES: Final = (
    "tests/save/test_decode_oracles.py",
    "tests/save/test_absolute_claims.py",
)

#: Markers of an UNBOUNDED QUANTIFIER, as label mapped to pattern, matched
#: case-insensitively against one sentence.
#:
#: Chosen on ADR 0008's discriminator, which is the size of a sentence's
#: FALSIFICATION SURFACE rather than its tone. A word here quantifies over a
#: domain with no stated bound - the whole suite, the whole of time, or all
#: possible inputs - so a local edit is unable to be reviewed against it and an
#: unrelated addition elsewhere can falsify it.
#:
#: DETERMINERS THAT MERELY NEGATE A LOCAL NOUN ARE ABSENT ON PURPOSE. "no save
#: library", "all six widths" and "only the offset" bound themselves to
#: something a reader checks by reading the code beside them, which is ADR
#: 0008's third tier - a MECHANISTIC claim, which stays prose. Adding them
#: would flag that tier and the fence would be deleted for noise.
ABSOLUTE_PATTERNS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "never": r"\bnever\b",
        "always": r"\balways\b",
        "ever": r"\bever\b",
        "every": r"\bevery\b",
        "everything": r"\beverything\b",
        "everywhere": r"\beverywhere\b",
        "nothing": r"\bnothing\b",
        "nowhere": r"\bnowhere\b",
        "cannot": r"\bcannot\b|\bcan not\b",
        "the-only": r"\bthe only\b|\bthe sole\b",
        "whatsoever": r"\bwhatsoever\b",
        "impossible": r"\bimpossible\b",
        "no-x-can": r"\bno \w+ can\b",
        "all-time": r"\bfor all time\b|\bat all times\b",
    }
)

#: A LOCAL citation: a double-backticked identifier in the test namespace. It
#: backs a sentence when the enclosing module defines a function of that name
#: at module scope, and is read as ordinary prose when it does not.
LOCAL_CITATION_RE: Final = re.compile(r"``(test_\w+)``")

#: A sentence boundary: a terminator followed by whitespace. See the residual.
_SENTENCE_SPLIT_RE: Final = re.compile(r"(?<=[.!?])\s+")

#: A reference to a prose paragraph by its opening words, in either quoting
#: style the tree uses.
_PARAGRAPH_REFERENCE_RE: Final = re.compile(r"beginning\s+(?:``([^`]+)``|'([^']+)')")

#: The token that makes "beginning <quoted>" a PARAGRAPH reference rather than
#: a sentence about a literal or a byte range.
_PARAGRAPH_ANCHOR: Final = "paragraph"

#: How many whitespace-separated tokens before "beginning" are searched for the
#: anchor. Measured against the tree: the widest real gap is three tokens, and
#: the base64url sentence in ``synthetic.py`` has the anchor absent entirely.
_PARAGRAPH_LOOKBACK_TOKENS: Final = 6

#: Directories whose modules supply the paragraph index that contract 4
#: resolves against.
_PARAGRAPH_INDEX_ROOTS: Final = ("clockspeed", "tests")

#: How much of a sentence a failure message quotes back.
_QUOTE_WIDTH: Final = 160


# ---------------------------------------------------------------------------
# Prose extraction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProseParagraph:
    """One paragraph of authored prose, with where it came from.

    Attributes:
        lineno: The line the paragraph starts on, for a failure message.
        kind: ``docstring``, ``comment`` or ``assert`` - see contract 5.
        text: The paragraph, line wraps already rejoined.
    """

    lineno: int
    kind: str
    text: str


def _docstring_literals(tree: ast.Module) -> list[tuple[int, str]]:
    """The docstring of each documentable node, with where it starts.

    Args:
        tree: A parsed module.

    Returns:
        ``(line_number, text)`` per docstring. The line number is carried
        because ``ast.get_docstring`` discards position, and a finding without
        one sends the reader hunting.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        first = node.body[0] if node.body else None
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            # Narrowed HERE, where the isinstance chain is the proof, rather
            # than at the use site - a returned node loses the narrowing and
            # the caller would need a cast to get it back.
            found.append((first.value.lineno, first.value.value))
    return found


def _assert_messages(tree: ast.Module) -> list[tuple[int, str]]:
    """The literal text of each ``assert`` statement's message.

    Args:
        tree: A parsed module.

    Returns:
        ``(line_number, text)`` per message that carries literal text. An
        f-string's interpolated slots are runtime data rather than prose, so
        only its constant chunks are kept - which is why the text may read with
        a gap where a value would go.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert) or node.msg is None:
            continue
        chunks = [
            part.value
            for part in ast.walk(node.msg)
            if isinstance(part, ast.Constant) and isinstance(part.value, str)
        ]
        if chunks:
            found.append((node.lineno, "".join(chunks)))
    return found


def _comment_runs(source: str) -> list[list[tuple[int, str]]]:
    """Group comment tokens into runs of consecutive lines.

    Args:
        source: A module's full text.

    Returns:
        One list of ``(line_number, token_text)`` pairs per run. Read from
        :mod:`tokenize`, so a ``#`` inside a string literal is not a comment -
        which is what keeps this file's own control corpora inert.

    Raises:
        tokenize.TokenError: If the source does not tokenize.
    """
    runs: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    previous: int | None = None
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        if previous is not None and line != previous + 1 and current:
            runs.append(current)
            current = []
        # "#:" is Sphinx attribute-doc syntax. Reducing it to "#" lets the
        # imported normaliser strip the marker without leaving a stray colon
        # at the head of the paragraph.
        text = token.string
        current.append((line, "#" + text[2:] if text.startswith("#:") else text))
        previous = line
    if current:
        runs.append(current)
    return runs


def _split_at_blank(lines: list[tuple[int, str]]) -> list[list[tuple[int, str]]]:
    """Cut numbered lines into groups at blank or rule-only lines.

    Args:
        lines: ``(line_number, text)`` pairs in order.

    Returns:
        One group per paragraph, blanks and horizontal rules dropped.
    """
    groups: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    for number, raw in lines:
        if citations._RULE_RE.match(raw):  # noqa: SLF001
            continue
        if citations._decomment(raw):  # noqa: SLF001
            current.append((number, raw))
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def prose_paragraphs(source: str) -> list[ProseParagraph]:
    """Extract authored prose from a module, paragraph by paragraph.

    Prose is a docstring, a comment or an assert message - contract 5. A string
    literal used as data sits outside that definition by AST position.

    Args:
        source: A module's full text.

    Returns:
        The paragraphs, grouped by kind rather than in file order.

    Raises:
        SyntaxError: If the source does not parse.
    """
    tree = ast.parse(source)
    out: list[ProseParagraph] = []
    for start, docstring in _docstring_literals(tree):
        numbered = [(start + offset, line) for offset, line in enumerate(docstring.splitlines())]
        for group in _split_at_blank(numbered):
            text = citations.normalise_lines(line for _, line in group)
            out.append(ProseParagraph(lineno=group[0][0], kind="docstring", text=text))
    for run in _comment_runs(source):
        for group in _split_at_blank(run):
            text = citations.normalise_lines(line for _, line in group)
            out.append(ProseParagraph(lineno=group[0][0], kind="comment", text=text))
    for lineno, message in _assert_messages(tree):
        text = citations.normalise_lines(message.splitlines())
        if text:
            out.append(ProseParagraph(lineno=lineno, kind="assert", text=text))
    return out


def sentences_of(text: str) -> list[str]:
    """Split one paragraph into sentences.

    Args:
        text: A normalised paragraph.

    Returns:
        The sentences, stripped, with blanks dropped.
    """
    return [part.strip() for part in _SENTENCE_SPLIT_RE.split(text) if part.strip()]


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One sentence quantifying over an unbounded domain with no test named.

    Attributes:
        path: Repo-relative POSIX path of the module it sits in.
        lineno: Where its paragraph starts.
        kind: ``docstring`` or ``comment``.
        markers: Which entries of :data:`ABSOLUTE_PATTERNS` matched.
        sentence: The sentence, truncated for a failure message.
    """

    path: str
    lineno: int
    kind: str
    markers: tuple[str, ...]
    sentence: str


def absolute_markers(sentence: str) -> tuple[str, ...]:
    """Which unbounded-quantifier markers a sentence carries.

    Args:
        sentence: One sentence of prose.

    Returns:
        The matching labels, sorted, so a failure message is stable.
    """
    return tuple(
        sorted(
            label
            for label, pattern in ABSOLUTE_PATTERNS.items()
            if re.search(pattern, sentence, re.IGNORECASE)
        )
    )


def backing_citations(
    sentence: str,
    defined: frozenset[str],
    sources: Mapping[str, str],
) -> list[str]:
    """The citations in one sentence that RESOLVE, in either form.

    Args:
        sentence: One sentence of prose.
        defined: Module-scope function names of the module the sentence is in,
            which is what a LOCAL citation resolves against.
        sources: Repo-relative POSIX path mapped to module text, injected so a
            control needs no filesystem.

    Returns:
        A label per resolving citation. Empty when the sentence names no test
        that exists, which is what leaves an unbounded claim unbacked.
    """
    found: list[str] = []
    full = citations.CITATION_RE.findall(sentence)
    for path, name in full:
        if citations.resolve([(path, name)], sources)[path, name] == citations.RESOLVED:
            found.append(f"{path}::{name}")
    found.extend(name for name in LOCAL_CITATION_RE.findall(sentence) if name in defined)
    return found


def unbacked_absolutes(
    path: str,
    source: str,
    sources: Mapping[str, str],
) -> list[Finding]:
    """The sentences in one module's prose that quantify without naming a test.

    Args:
        path: Repo-relative POSIX path of the module, for the report.
        source: Its full text.
        sources: The resolution table, as :func:`backing_citations` takes it.

    Returns:
        The findings, in the order the paragraphs were read.
    """
    defined = citations.module_scope_functions(source)
    out: list[Finding] = []
    for paragraph in prose_paragraphs(source):
        for sentence in sentences_of(paragraph.text):
            markers = absolute_markers(sentence)
            if not markers or backing_citations(sentence, defined, sources):
                continue
            out.append(
                Finding(
                    path=path,
                    lineno=paragraph.lineno,
                    kind=paragraph.kind,
                    markers=markers,
                    sentence=sentence[:_QUOTE_WIDTH],
                )
            )
    return out


def dead_full_citations(source: str, sources: Mapping[str, str]) -> dict[str, str]:
    """Full-form citations in a module's prose that name a test which is absent.

    The unambiguous half of contract 2. ``test_oracle_citations`` runs this
    scan over ``clockspeed/`` and not over ``tests/``, so a citation written in
    a test module's own prose had no resolver before this.

    Args:
        source: A module's full text.
        sources: The resolution table.

    Returns:
        Each unresolved citation mapped to its verdict.
    """
    cited = [
        cite
        for paragraph in prose_paragraphs(source)
        for cite in citations.CITATION_RE.findall(paragraph.text)
    ]
    return {
        f"{path}::{name}": verdict
        for (path, name), verdict in citations.resolve(cited, sources).items()
        if verdict != citations.RESOLVED
    }


def sentence_count(source: str) -> int:
    """How many sentences of prose a module holds.

    The fenced scan's liveness floor reads this. A scanner that extracted zero
    prose would report zero findings and pass in silence.

    Args:
        source: A module's full text.

    Returns:
        The count.
    """
    return sum(len(sentences_of(p.text)) for p in prose_paragraphs(source))


# ---------------------------------------------------------------------------
# Paragraph references - contract 4
# ---------------------------------------------------------------------------


def paragraph_references(text: str) -> list[str]:
    """The paragraph openings a piece of prose quotes.

    Args:
        text: A normalised paragraph.

    Returns:
        The quoted text of each reference anchored by the token
        :data:`_PARAGRAPH_ANCHOR` within :data:`_PARAGRAPH_LOOKBACK_TOKENS`
        tokens before it. A quotation with the anchor absent is read as being
        about something other than a paragraph and is left alone.
    """
    out: list[str] = []
    for hit in _PARAGRAPH_REFERENCE_RE.finditer(text):
        window = text[: hit.start()].split()[-_PARAGRAPH_LOOKBACK_TOKENS:]
        if _PARAGRAPH_ANCHOR not in " ".join(window).lower():
            continue
        out.append((hit.group(1) or hit.group(2)).strip())
    return out


def unresolved_paragraph_references(text: str, index: Iterable[str]) -> list[str]:
    """Quoted paragraph openings that prefix-match no paragraph in the index.

    Args:
        text: A normalised paragraph of prose.
        index: The text of the known prose paragraphs.

    Returns:
        The dead references, in text order.
    """
    known = tuple(index)
    return [
        quoted
        for quoted in paragraph_references(text)
        if not any(paragraph.startswith(quoted) for paragraph in known)
    ]


def _sources_under(root: Path, subdir: str) -> dict[str, str]:
    """Read the modules under a subdirectory into a path-to-text table.

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


def _paragraph_index(root: Path) -> list[str]:
    """The text of the prose paragraphs under the indexed roots.

    Args:
        root: Repository root.

    Returns:
        Paragraph texts, which contract 4 prefix-matches against.
    """
    return [
        paragraph.text
        for subdir in _PARAGRAPH_INDEX_ROOTS
        for source in _sources_under(root, subdir).values()
        for paragraph in prose_paragraphs(source)
    ]


# ---------------------------------------------------------------------------
# The control corpora - authored here, not imported, and naming no real module
# ---------------------------------------------------------------------------

_CONTROL_RED = '''\
"""A synthetic module docstring. IT NEVER RAISES.

A second paragraph, and this one claims that every payload reaches.
"""

# A comment run that says nothing else catches the fault.
VALUE = "IT NEVER RAISES inside a data literal is data, and stays unread."


def check(value: int) -> None:
    """A docstring on a function, which is a third place prose hides."""
    assert value, "an assert message claiming the walk is always synchronised"
'''

_CONTROL_CLEAN = '''\
"""A synthetic module docstring stating a bounded fact.

The walk reads two widths from the shipped constant and advances by the extent
the shipped header reported. A reader checks that by reading the function.
"""

# A comment run with no unbounded quantifier in it at all.
VALUE = "data"
'''

_CONTROL_CITED = '''\
"""Docstring paragraph one. Every width is graded by ``test_local_backer``.

Docstring paragraph two. Every width is graded by ``test_absent_backer``.

Docstring paragraph three. Every width is graded by
tests/synthetic/test_alpha.py::test_full_backer.

Docstring paragraph four. Every width is graded by
tests/synthetic/test_alpha.py::test_full_ghost.
"""


def test_local_backer() -> None:
    assert True
'''

_CONTROL_CITED_SOURCES: Final[Mapping[str, str]] = MappingProxyType(
    {"tests/synthetic/test_alpha.py": "def test_full_backer() -> None:\n    assert True\n"}
)

#: Docstring paragraphs of the red control that carry a quantifier: its summary
#: line and its second paragraph. A property of the corpus authored above, not
#: a measurement of the tree.
_CONTROL_RED_DOCSTRING_FINDINGS: Final = 2

#: Sentences of the cited control naming a test that fails to resolve: one per
#: citation form, which is what pins both forms in the same run.
_CONTROL_UNRESOLVED_CITATIONS: Final = 2

_CONTROL_PARAGRAPH_INDEX: Final = (
    "THAT JOIN CARRIES TWO QUANTITIES AND THEY DO NOT GRADE THE TAG WIDTHS "
    "BELOW ALIKE - one mechanism read at two quantities.",
    "SHIPPED REDUNDANCY - a string-bearing value carries its own length prefix.",
)

#: References in the styles the tree uses. The flag is whether the
#: reference has to resolve; a quotation with the anchor absent is not a
#: paragraph reference and has to stay unread, or the rule would be red against
#: the base64url sentence in ``tests/save/synthetic.py``.
_CONTROL_PARAGRAPH_REFERENCES: Final[Mapping[str, tuple[str, bool]]] = MappingProxyType(
    {
        "live-backtick": ("the paragraph beginning ``THAT JOIN CARRIES TWO``", True),
        "live-quote": ("the shipped paragraph beginning 'SHIPPED REDUNDANCY'", True),
        "renamed-backtick": ("the paragraph beginning ``THAT JOIN IS NOT A CHECK``", True),
        "gapped-anchor": ("such a paragraph - the one beginning ``THAT JOIN IS NOT``", True),
        "not-a-paragraph": ("a base64url literal beginning ``Clockspeed``", False),
    }
)


# ---------------------------------------------------------------------------
# The fenced scan
# ---------------------------------------------------------------------------


def test_the_fenced_prose_carries_no_unbacked_absolute_claim(repo_root: Path) -> None:
    sources = _sources_under(repo_root, "tests")
    scanned = 0
    findings: list[Finding] = []
    for path in FENCED_MODULES:
        assert path in sources, (
            f"{path} is named in FENCED_MODULES and no such module was read. The "
            "fence is scanning a file that has been renamed or deleted, so its "
            "green is silent about the prose it was written to govern."
        )
        scanned += sentence_count(sources[path])
        findings.extend(unbacked_absolutes(path, sources[path], sources))

    assert scanned, (
        "the scanner extracted no prose at all from the fenced modules. A scan "
        "that reads zero sentences reports zero findings and passes, which is "
        "the vacuous green this fence exists to prevent."
    )
    assert not findings, (
        "sentences quantifying over an unbounded domain with no test named:\n"
        + "\n".join(
            f"  {f.path}:{f.lineno} ({f.kind}) {list(f.markers)}\n    {f.sentence}"
            for f in findings
        )
        + "\n\nEach one is deleted, or narrowed until the quantifier is gone, or "
        "made to name a test that resolves. Adding it to an exemption list is "
        "not a third option - see contract 1."
    )


def test_every_full_citation_in_the_fenced_prose_resolves(repo_root: Path) -> None:
    sources = _sources_under(repo_root, "tests")
    dead = {
        path: dead_full_citations(sources[path], sources)
        for path in FENCED_MODULES
        if dead_full_citations(sources[path], sources)
    }
    assert not dead, (
        f"full-form citations naming a test that does not exist: {dead}. The "
        "package scan in test_oracle_citations reads clockspeed/ and not tests/, "
        "so a citation written in a test module's own prose is resolved here or "
        "by no scan at all."
    )


def test_every_paragraph_reference_under_the_indexed_roots_resolves(repo_root: Path) -> None:
    index = _paragraph_index(repo_root)
    assert index, (
        "the paragraph index is empty, so contract 4 would resolve no reference "
        "and report no dead one. The extractor has broken."
    )
    dead: dict[str, list[str]] = {}
    for subdir in _PARAGRAPH_INDEX_ROOTS:
        for path, source in _sources_under(repo_root, subdir).items():
            found = [
                quoted
                for paragraph in prose_paragraphs(source)
                for quoted in unresolved_paragraph_references(paragraph.text, index)
            ]
            if found:
                dead[path] = found
    assert not dead, (
        f"prose quoting a paragraph that no longer opens that way: {dead}. A "
        "rename leaves the quotation behind and the suite stayed green through "
        "exactly this once already - 662432d renamed the objects.py join "
        "paragraph and two sentences went on quoting the old opening."
    )


# ---------------------------------------------------------------------------
# The controls - filesystem-free, and what stops the scan above being vacuous
# ---------------------------------------------------------------------------


def test_the_scanner_reddens_on_a_reinserted_absolute() -> None:
    findings = unbacked_absolutes("synthetic.py", _CONTROL_RED, {})
    quoted = [f.sentence for f in findings]

    assert any("IT NEVER RAISES" in sentence for sentence in quoted), (
        f"re-inserting the exact sentence CS-420 was reopened over did not "
        f"redden the scanner. It reported {quoted}. A fence blind to the string "
        "that reopened the item is decoration."
    )
    docstring_hits = [f.kind for f in findings].count("docstring")
    assert docstring_hits >= _CONTROL_RED_DOCSTRING_FINDINGS, (
        f"the scanner read {docstring_hits} docstring findings out of the red "
        f"control: {[(f.kind, f.markers) for f in findings]}. Both the summary "
        "line and the second paragraph carry a quantifier."
    )
    kinds = {f.kind for f in findings}
    assert {"docstring", "comment", "assert"} <= kinds, (
        f"the scanner read only {sorted(kinds)} out of the red control, which "
        "carries a quantifier in each of contract 5's three prose kinds. A kind "
        "the scan skips is a place the banned sentence may be written."
    )


def test_the_scanner_passes_prose_with_no_unbounded_quantifier() -> None:
    findings = unbacked_absolutes("synthetic.py", _CONTROL_CLEAN, {})
    assert not findings, (
        f"clean prose was reported: {[(f.markers, f.sentence) for f in findings]}. "
        "Without this the red control proves only that the scanner rejects all "
        "prose put to it, which is a different and worthless property."
    )


def test_a_resolving_citation_backs_an_absolute_and_an_unresolvable_one_does_not() -> None:
    findings = unbacked_absolutes("synthetic.py", _CONTROL_CITED, _CONTROL_CITED_SOURCES)
    reported = [f.sentence for f in findings]

    assert len(findings) == _CONTROL_UNRESOLVED_CITATIONS, (
        f"expected the two sentences whose citation does not resolve and got "
        f"{reported}. Both citation forms have to back a sentence when they "
        "resolve, and neither may back one when it does not."
    )
    assert any("test_absent_backer" in sentence for sentence in reported), (
        f"a LOCAL citation naming a function the module does not define backed "
        f"its sentence anyway. Reported: {reported}."
    )
    assert any("test_full_ghost" in sentence for sentence in reported), (
        f"a FULL citation naming a test absent from the source table backed its "
        f"sentence anyway. Reported: {reported}."
    )


def test_a_dead_full_citation_in_prose_is_reported() -> None:
    dead = dead_full_citations(_CONTROL_CITED, _CONTROL_CITED_SOURCES)
    assert dead == {"tests/synthetic/test_alpha.py::test_full_ghost": citations.MISSING_TEST}, (
        f"the dead full-form citation was not reported: {dead}. Its form is "
        "unambiguous, so an unresolved one is an error rather than prose."
    )


def test_prose_is_read_from_the_three_kinds_and_not_from_a_data_literal() -> None:
    paragraphs = prose_paragraphs(_CONTROL_RED)
    kinds = {p.kind for p in paragraphs}
    assert kinds == {"docstring", "comment", "assert"}, (
        f"the extractor did not recover contract 5's three prose kinds: {sorted(kinds)}."
    )

    carriers = [p.kind for p in paragraphs if "IT NEVER RAISES" in p.text]
    assert carriers == ["docstring"], (
        f"the banned sentence was read out of more than the docstring holding "
        f"it: {carriers}. The control corpora in this file are module-level "
        "assignments, so a reader that treated an assignment as prose would make "
        "this module fail itself, and the corpora would have to be moved out "
        "behind a scope rule - which is the artifact contract 1 refuses."
    )


def test_a_paragraph_reference_resolves_only_against_a_paragraph_that_opens_that_way() -> None:
    misread: list[str] = []
    for label, (text, must_resolve) in _CONTROL_PARAGRAPH_REFERENCES.items():
        seen = paragraph_references(text)
        if must_resolve and not seen:
            misread.append(f"{label} was not read as a paragraph reference at all")
        if not must_resolve and seen:
            misread.append(f"{label} was read as a paragraph reference: {seen}")
    assert not misread, (
        f"the anchor window misjudged a reference: {misread}. A quotation with "
        "no paragraph token near it is about something else, and a rule red on "
        "that would be red against correct prose."
    )

    live = _CONTROL_PARAGRAPH_REFERENCES["live-backtick"][0]
    assert not unresolved_paragraph_references(live, _CONTROL_PARAGRAPH_INDEX), (
        "a reference quoting the opening of a paragraph that IS in the index was "
        "reported dead, so contract 4 would be red on correct prose."
    )

    renamed = _CONTROL_PARAGRAPH_REFERENCES["renamed-backtick"][0]
    assert unresolved_paragraph_references(renamed, _CONTROL_PARAGRAPH_INDEX) == [
        "THAT JOIN IS NOT A CHECK"
    ], (
        "a reference quoting a heading that was RENAMED away resolved anyway. "
        "This is the exact 662432d rename, and a fence that misses it closes "
        "no gap."
    )
