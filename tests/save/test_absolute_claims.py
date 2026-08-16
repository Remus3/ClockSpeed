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

WHAT COUNTS AS PROSE (contract 5) is the kinds listed in
:data:`_PARAGRAPH_KINDS`, and the last two were added after measuring what
excluding them cost. The tuple is the record; this paragraph does not restate
its length, because a kind added later would leave a number here false.

A DOCSTRING and a COMMENT are obvious. An ASSERT MESSAGE is prose too: a reader
reads it as a statement about the current tree, which is ADR 0008's own test
for living text, and leaving it out would leave a place to write a banned
sentence that this fence does not read - the one thing ADR 0008's Consequences
say the rule must deny. It is not a theoretical hole. The second of the two
quotations that ``662432d`` killed sits in an assert message, and a
docstring-and-comment scan reported one of the two and passed.

A DIRECT CALL ARGUMENT IS THE LAST OF THEM, and contract 6 below is what found
it. ``pytest.skip("...")`` carries a sentence written for the OPERATOR to
explain a loss, and it is not a docstring, not a comment and not an assert
message, so the earlier kinds left it unread. This is the channel CLASS that
CS-435 shipped a false universal in - a warning detail string, which the fence
could not see at all. Only a DIRECT argument counts: a string nested inside a
dict or a tuple that is itself an argument is a data structure being passed
rather than a sentence being written, and reading those would make this module
red on its own grammar table.

A STRING LITERAL USED AS DATA IS NOT PROSE, and that line is drawn by AST
POSITION rather than by a scope rule. The assert message is reached through
``ast.Assert.msg``; a module-level assignment is reached by no prose route at
all. That is what keeps the control corpora below INERT BY CONSTRUCTION - they
are assignments - and a ``#`` inside one is not a comment either, because
comments come from :mod:`tokenize`.

COVERAGE IS CONSERVED (contract 6), and this is the half the earlier rounds of
repair did not have. In a module named in :data:`CENSUSED_MODULES` each string
literal is classified from ONE parse: read by a prose kind, or matched by the
one exemption, or UNACCOUNTED - and unaccounted reddens. Comment tokens are
accounted the same way against an independent :mod:`tokenize` pass. The claim
is NOT that the declared positions cover the language; it is that a position
nobody anticipated unbalances a count instead of passing unread.

THE EXEMPTION TURNS ON WHAT THE STRING IS, NOT ON THE SLOT IT SITS IN, and that
is what stops it becoming a write-anything channel. A module-scope assignment
whose value is a bare IDENTIFIER holds a token the module computes with - a
terminator word, a counter key. The same slot holding a SENTENCE is not an
identifier, so it is not exempt; no prose kind reads a bare assignment either,
so it lands unaccounted and reddens. An exemption keyed on POSITION would have
swallowed the two ``pytest.skip`` reasons along with the attribute names beside
them, which is a hole with a control bolted to it.

THE SCOPE IS DERIVED, NOT LISTED. A module declares :data:`_FENCE_MARKER` or
:data:`_CENSUS_MARKER` at module scope, and the tuples above are asserted EQUAL
to what a walk of the tree finds. Deleting a tuple entry disagrees with the
walk; deleting a marker disagrees with the tuple. Narrowing a scope takes both
edits and neither is silent on its own - which a hand-written tuple could not
offer, since deleting the entry naming this fence's own subject used to leave
the suite green.

THE CONTROLS ARE THE POINT, because a scanner returning zero findings would
pass the fenced scan in silence.
:func:`test_prose_is_read_from_the_declared_kinds_and_not_from_a_data_literal`
holds the extraction contract down at both ends: each kind is read, and an
assignment is not. It needs no filesystem and no game, and neither do the
boundary controls beside it.
:func:`test_a_marked_claim_at_each_parse_derived_position_is_caught` does need
the tree, because its subject is the censused module's own parse: it writes a
marked claim into each position that parse admits, and requires the scan to
report it or the census to lose it.

THE RESIDUAL, NAMED RATHER THAN IMPLIED AWAY, past the strength limit already
stated in contract 3:

- THE SCAN IS SCOPED to :data:`FENCED_MODULES`. ``clockspeed/save/objects.py``
  carries prose of the same class and is NOT fenced, because its
  ``_TAG_EXTRA_STRINGS`` docstring is CS-422's to repair and a fence that
  reddens on another item's file would be reverted rather than obeyed. ADR 0008
  scopes its own mechanical fence the same way and calls widening it separate
  work.
- THE CENSUS IS SCOPED NARROWER STILL, to one module, and the reason is
  measured rather than chosen for convenience. The positions that tile the
  censused module leave most of THIS module's string literals unaccounted: the
  grammar table is regexes inside a dict, the corpora are Python source held in
  assignments, and the controls compare against bare label strings. Censusing
  this module would take an exemption per shape, and an exemption per shape is
  the register of pardons contract 1 refuses. What that costs is stated plainly
  rather than implied away: a sentence written into a dict value HERE is read
  by no channel, and no count notices.
- A CLAIM THAT CONTINUES A SENTENCE INHERITS ITS CITATIONS. The rule's unit is
  a sentence, and a citation anywhere in one backs the whole of it, so a marked
  claim appended to a clause that already names a resolving test satisfies
  contract 1. That is contract 3's limit reached from a second direction rather
  than a fresh gap, and it is why the comment probe closes the preceding
  fragment before writing its claim.
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

#: This module declares itself fenced, and the declaration is what the scope
#: derivation reads. A fence written in prose that would fail itself is a fence
#: its author did not believe.
#:
#: It does NOT declare itself CENSUSED, and that is a measured limit rather
#: than an oversight - see the census residual in the module docstring.
CS420_FENCED: Final = True

#: Modules whose prose this fence governs, as repo-relative POSIX paths.
#:
#: The fenced module is CS-420's subject. This module is fenced too, and that
#: is not decoration: a fence written in prose that would fail itself is a
#: fence its author did not believe. Widening the tuple is how the rule spreads;
#: see the scoping residual in the module docstring for why it stops here.
FENCED_MODULES: Final = (
    "tests/save/test_absolute_claims.py",
    "tests/save/test_decode_oracles.py",
)

#: Modules whose string literals and comment tokens the fence has to ACCOUNT
#: FOR - contract 6. A strict subset of the fenced set, and the reason it is a
#: subset is stated in the residual rather than implied away.
CENSUSED_MODULES: Final = ("tests/save/test_decode_oracles.py",)

#: The module-scope names a module declares to opt itself into each contract.
#: The tuples above are asserted EQUAL to what a walk of the tree finds, so a
#: deleted tuple entry and a deleted marker are each caught on their own.
_FENCE_MARKER: Final = "CS420_FENCED"
_CENSUS_MARKER: Final = "CS420_CENSUSED"

#: Kind labels a string literal may carry. A PROSE kind is read by
#: :func:`prose_paragraphs` and graded; an EXEMPT kind is not read, and an
#: exempt kind carries a control pinning its BOUNDARY rather than its centre.
_PROSE_KINDS: Final = ("docstring", "assert", "argument")

#: The kinds :func:`prose_paragraphs` may emit: the string kinds above plus the
#: comment channel, which comes from :mod:`tokenize` rather than from the
#: syntax tree and so has no string literal to census. This tuple is what
#: contract 5 means by "the prose kinds"; the docstring points here rather than
#: restating its length.
_PARAGRAPH_KINDS: Final = (*_PROSE_KINDS, "comment")

#: The one exempt kind. A module-scope assignment whose value is a bare Python
#: IDENTIFIER is a token the module computes with - a terminator word, a
#: counter key, an attribute name - and not a sentence. The exemption turns on
#: WHAT THE STRING IS rather than on where it sits, which is what stops it
#: swallowing prose: the same assignment holding a sentence is not an
#: identifier, so it is not exempt, and no prose channel reads a bare
#: assignment either, so it lands UNACCOUNTED and reddens.
_MODULE_CONSTANT: Final = "module-constant"
_EXEMPT_KINDS: Final = (_MODULE_CONSTANT,)

#: Kind labels a comment token may carry. ``rule`` and ``blank`` are the two
#: comment exemptions: a horizontal rule and a line that decomments to an
#: empty string carry no prose, and the grouper drops both before paragraphs
#: are cut.
_COMMENT_KINDS: Final = ("comment", "rule", "blank")

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

#: A reference to a prose paragraph by its opening words.
_PARAGRAPH_REFERENCE_RE: Final = re.compile(r"beginning\s+(?:``([^`]+)``|'([^']+)')")

#: The token that makes "beginning <quoted>" a PARAGRAPH reference rather than
#: a sentence about a literal or a byte range.
_PARAGRAPH_ANCHOR: Final = "paragraph"

#: How many whitespace-separated tokens before "beginning" are searched for the
#: anchor. The base64url sentence in ``synthetic.py`` has the anchor absent
#: entirely.
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


@dataclass(frozen=True)
class StringLiteral:
    """One string literal, with its text already narrowed to ``str``.

    ``ast.Constant.value`` is typed as a union across the literal types, so a
    function handing back a bare node makes each caller re-prove that the value
    is text. The narrowing is done ONCE, where the isinstance chain is the
    proof, and carried on this pair.

    Attributes:
        node: The literal, whose identity keys the census classification and
            whose ``value`` the mutation control rewrites.
        text: Its text.
    """

    node: ast.Constant
    text: str

    @property
    def lineno(self) -> int:
        """The line the literal starts on."""
        return self.node.lineno


def _string_literal(node: ast.AST | None) -> StringLiteral | None:
    """Pair a node with its text when it is a string literal.

    Args:
        node: Any syntax node, or ``None`` for an absent optional field.

    Returns:
        The pair when the node is a ``str`` constant, else ``None``.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return StringLiteral(node=node, text=node.value)
    return None


def _string_literals(tree: ast.Module) -> list[StringLiteral]:
    """The string literals of a module, in a stable order.

    Args:
        tree: A parsed module.

    Returns:
        The literals, sorted by position, which is the census population.
    """
    found = [_string_literal(node) for node in ast.walk(tree)]
    present = [literal for literal in found if literal is not None]
    return sorted(present, key=lambda literal: (literal.node.lineno, literal.node.col_offset))


def _docstring_nodes(tree: ast.Module) -> list[StringLiteral]:
    """The docstring literal of each documentable node.

    Args:
        tree: A parsed module.

    Returns:
        One literal per docstring, in walk order.
    """
    found: list[StringLiteral] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        first = node.body[0] if node.body else None
        literal = _string_literal(first.value) if isinstance(first, ast.Expr) else None
        if literal is not None:
            found.append(literal)
    return found


def _docstring_literals(tree: ast.Module) -> list[tuple[int, str]]:
    """The docstring of each documentable node, with where it starts.

    Args:
        tree: A parsed module.

    Returns:
        ``(line_number, text)`` per docstring. The line number is carried
        because ``ast.get_docstring`` discards position, and a finding without
        one sends the reader hunting.
    """
    return [(literal.lineno, literal.text) for literal in _docstring_nodes(tree)]


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


def _argument_nodes(tree: ast.Module) -> list[StringLiteral]:
    """String literals passed DIRECTLY as an argument of a call.

    This is contract 5's fourth prose kind. ``pytest.skip("...")`` carries a
    sentence shipped to the OPERATOR to explain a loss, and no docstring,
    comment or assert message holds it - a reason CS-435 shipped a false
    universal in this exact position, in a warning detail, which the fence
    could not see at all.

    The rule is DIRECT arguments only. A string nested inside a dict, a tuple
    or a set that is itself an argument is a data structure being passed, not a
    sentence being written, and reading those would make this module fail
    itself on its own grammar table.

    Args:
        tree: A parsed module.

    Returns:
        The argument nodes, in walk order.
    """
    found: list[StringLiteral] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for arg in (*node.args, *(keyword.value for keyword in node.keywords)):
            literal = _string_literal(arg)
            if literal is not None:
                found.append(literal)
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
    kinds = _string_kinds(tree)
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
    for literal in _argument_nodes(tree):
        # An argument that sits INSIDE an assert message is already read as one,
        # and the kind map is what decides that, so a sentence in that position
        # is reported once rather than twice under two labels.
        if kinds.get(id(literal.node)) != "argument":
            continue
        text = citations.normalise_lines(literal.text.splitlines())
        if text:
            out.append(ProseParagraph(lineno=literal.lineno, kind="argument", text=text))
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
# The census - contract 6
# ---------------------------------------------------------------------------


def _string_kinds(tree: ast.Module) -> dict[int, str]:
    """Classify a module's string literals in ONE parse, by node identity.

    Each pass is a POSITIVE rule, and the first pass to claim a node keeps it,
    so the result is a partition rather than an overlap. A node no pass claims
    is absent from the mapping, which is what :func:`string_census` reports as
    unaccounted.

    Args:
        tree: A parsed module.

    Returns:
        ``id(node)`` mapped to a kind label. A label in :data:`_PROSE_KINDS` is
        read as prose; a label in :data:`_EXEMPT_KINDS` is not.
    """
    kinds: dict[int, str] = {}
    for literal in _docstring_nodes(tree):
        kinds.setdefault(id(literal.node), "docstring")
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and node.msg is not None:
            for part in ast.walk(node.msg):
                if _string_literal(part) is not None:
                    kinds.setdefault(id(part), "assert")
    for literal in _argument_nodes(tree):
        kinds.setdefault(id(literal.node), "argument")
    for node in tree.body:
        if not isinstance(node, ast.Assign | ast.AnnAssign):
            continue
        value = _string_literal(node.value)
        if value is not None and value.text.isidentifier():
            kinds.setdefault(id(value.node), _MODULE_CONSTANT)
    return kinds


@dataclass(frozen=True)
class StringCensus:
    """The conservation account for one module's string literals.

    Attributes:
        extracted: Nodes a prose channel reads, as ``(lineno, kind)``.
        exempt: Nodes an exemption matched, as ``(lineno, kind)``.
        unaccounted: Nodes no rule claimed, as ``(lineno, text)``. Non-empty
            means a string sits in a position no rule here covers.
    """

    extracted: tuple[tuple[int, str], ...]
    exempt: tuple[tuple[int, str], ...]
    unaccounted: tuple[tuple[int, str], ...]

    @property
    def total(self) -> int:
        """How many string literals the module holds."""
        return len(self.extracted) + len(self.exempt) + len(self.unaccounted)


def string_census(source: str) -> StringCensus:
    """Account for a module's string literals, from ONE parse.

    Args:
        source: A module's full text.

    Returns:
        The census. ``len(extracted) + len(exempt) == total`` exactly when the
        unaccounted set is empty, which is what the fenced test asserts.

    Raises:
        SyntaxError: If the source does not parse.
    """
    tree = ast.parse(source)
    kinds = _string_kinds(tree)
    extracted: list[tuple[int, str]] = []
    exempt: list[tuple[int, str]] = []
    unaccounted: list[tuple[int, str]] = []
    for literal in _string_literals(tree):
        kind = kinds.get(id(literal.node), "")
        if kind in _PROSE_KINDS:
            extracted.append((literal.lineno, kind))
        elif kind in _EXEMPT_KINDS:
            exempt.append((literal.lineno, kind))
        else:
            unaccounted.append((literal.lineno, literal.text[:_QUOTE_WIDTH]))
    return StringCensus(tuple(extracted), tuple(exempt), tuple(unaccounted))


def comment_census(source: str) -> dict[str, tuple[int, ...]]:
    """Account for a module's comment tokens.

    The total is taken from :mod:`tokenize` directly rather than from the run
    grouper, so a token the grouper drops shows up as a shortfall rather than
    going uncounted.

    WHICH FAULT TO SIMULATE WHEN GRADING THIS. The ``unaccounted`` bucket is
    reachable only while the grouper is losing a token, because the grouper
    walks the same token stream. Perturbing the ``seen.get`` default therefore
    leaves the bucket unexercised and the suite green - measured - and says
    little about whether the bucket works. The fault to inject is the grouper
    DROPPING a class of token, such as a trailing comment or a ``#:`` line.

    Args:
        source: A module's full text.

    Returns:
        A kind label mapped to the line numbers carrying it: ``comment`` for a
        token :func:`prose_paragraphs` reads, ``rule`` for a horizontal rule,
        ``blank`` for one that decomments to an empty string, and
        ``unaccounted`` for a token the run grouper did not yield.

    Raises:
        tokenize.TokenError: If the source does not tokenize.
    """
    seen: dict[int, str] = {}
    for run in _comment_runs(source):
        for lineno, text in run:
            if citations._RULE_RE.match(text):  # noqa: SLF001
                seen[lineno] = "rule"
            elif citations._decomment(text):  # noqa: SLF001
                seen[lineno] = "comment"
            else:
                seen[lineno] = "blank"
    out: dict[str, list[int]] = {label: [] for label in (*_COMMENT_KINDS, "unaccounted")}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            out[seen.get(token.start[0], "unaccounted")].append(token.start[0])
    return {label: tuple(lines) for label, lines in out.items()}


def string_position_mutants(source: str, claim: str) -> list[tuple[int, str, str]]:
    """One mutant per string literal, carrying the claim in that position.

    The positions are ENUMERATED FROM THE PARSE rather than written down, so a
    position added to the module tomorrow is probed without anyone remembering
    to list it. The mutant is rendered with :func:`ast.unparse` rather than by
    splicing text: CPython merges adjacent literal chunks of an implicitly
    concatenated f-string into ONE node whose source span crosses the quote
    characters between them, and a text splice over that span produces a module
    that does not parse.

    Args:
        source: A module's full text.
        claim: The sentence to write into each position. It carries a marker
            and cites no test, so a channel that reads it has to report it.

    Returns:
        ``(lineno, kind, mutant_source)`` per position, the kind taken from
        :func:`_string_kinds` so a caller knows which disposition is due.
        Rendering drops comments, which is why the comment positions are probed
        separately by :func:`comment_position_mutants`.

    Raises:
        SyntaxError: If the source does not parse.
    """
    tree = ast.parse(source)
    kinds = _string_kinds(tree)
    out: list[tuple[int, str, str]] = []
    for literal in _string_literals(tree):
        literal.node.value = claim
        try:
            kind = kinds.get(id(literal.node), "unaccounted")
            out.append((literal.lineno, kind, ast.unparse(tree)))
        finally:
            literal.node.value = literal.text
    return out


def comment_position_mutants(source: str, claim: str) -> list[tuple[int, str]]:
    """One mutant per comment token, the claim written over that comment.

    THE CLAIM IS PREFIXED WITH A SENTENCE TERMINATOR, and that is load-bearing
    rather than cosmetic. A comment line in the middle of a paragraph is a
    fragment of a sentence that starts on an earlier line, so a claim written
    over it CONTINUES that sentence instead of being one. It then inherits any
    citation the sentence already carried, and a sentence naming a resolving
    test satisfies contract 1 whatever else it says. That is contract 3's
    stated limit reached from a new direction rather than a fresh gap: a
    resolving citation is not evidence that the test backs the sentence. The
    terminator closes the preceding fragment so the probe asks the question it
    means to ask, which is whether a claim written AT this position is read.

    Args:
        source: A module's full text.
        claim: The sentence to write into each position.

    Returns:
        ``(lineno, mutant_source)`` per comment token. A comment span ends at
        the end of its line, so overwriting one is a safe text edit where
        overwriting a string literal is not.

    Raises:
        tokenize.TokenError: If the source does not tokenize.
    """
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    out: list[tuple[int, str]] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        begin = offsets[token.start[0] - 1] + token.start[1]
        end = offsets[token.end[0] - 1] + token.end[1]
        out.append((token.start[0], f"{source[:begin]}# . {claim}{source[end:]}"))
    return out


def modules_declaring(marker: str, sources: Mapping[str, str]) -> tuple[str, ...]:
    """The modules that declare a contract marker at module scope.

    Args:
        marker: The marker name, as :data:`_FENCE_MARKER` spells it.
        sources: Repo-relative POSIX path mapped to module text.

    Returns:
        The declaring paths, sorted. A module that does not parse is skipped
        rather than reported here - the fenced modules are parsed by the scan
        itself, which reports a SyntaxError.
    """
    found: list[str] = []
    for path, source in sorted(sources.items()):
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.AnnAssign):
                targets: list[ast.expr] = [node.target]
            elif isinstance(node, ast.Assign):
                targets = list(node.targets)
            else:
                continue
            names = {t.id for t in targets if isinstance(t, ast.Name)}
            declared = isinstance(node.value, ast.Constant) and node.value.value is True
            if marker in names and declared:
                found.append(path)
                break
    return tuple(found)


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
    skip("a skip reason telling the operator the walk always resynchronises")
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

#: One string in each position the census discriminates between. The pairs are
#: what pin the exemption BOUNDARIES: a token and a sentence in the SAME
#: module-scope assignment slot, and a direct call argument beside a string
#: nested one level inside one. A control that only showed the exempted thing
#: exempted would pin neither edge.
_CONTROL_CENSUS = '''\
"""A synthetic module docstring."""

TOKEN = "identifier"
SENTENCE = "a module-scope assignment holding a sentence rather than a token."
TABLE = {"nested": "a string inside a dict that is not a direct argument."}


def check(value: int) -> None:
    """A function docstring."""
    inner = "a function-scope assignment, which is not module scope."
    skip("a call argument carrying an operator-facing sentence.")
    wrap({"nested": "a string inside a dict passed as an argument."})
    assert value, "an assert message."
'''

#: Comment lines, one per class the grouper discriminates between. The last two
#: are the boundary: a line opening like a horizontal rule but carrying text is
#: prose, and a trailing comment beside code is prose too.
_CONTROL_COMMENT_CENSUS = """\
# ---------------------------------------------------------------------------
# A comment line carrying prose.
#
#: A Sphinx attribute-doc line.
# --- a line that opens like a rule and then carries text.
VALUE = "token"  # a trailing comment beside code.
"""

#: The sentence contract 6's mutation control writes into each position the
#: censused module's parse admits. It carries a listed marker and cites no
#: test, so a channel that READS it has to report it. Held in a module-level
#: assignment, which is not a prose channel, so it stays inert where it sits.
_MARKED_CLAIM: Final = "CONTROLPROBE - every payload reaches its terminator."

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


def test_the_fenced_and_censused_scopes_are_derived_from_the_tree(repo_root: Path) -> None:
    sources = _sources_under(repo_root, "tests")

    for marker, declared in ((_FENCE_MARKER, FENCED_MODULES), (_CENSUS_MARKER, CENSUSED_MODULES)):
        derived = modules_declaring(marker, sources)
        assert derived, (
            f"no module under tests/ declares {marker}, so the scope was derived "
            "from an empty walk and the tuple beside it is once again a "
            "hand-written allowlist. The walk has broken, or the markers have "
            "been deleted."
        )
        assert derived == tuple(sorted(declared)), (
            f"the {marker} scope declared in the tuple is {sorted(declared)} and "
            f"the walk of the tree found {list(derived)}. These are two "
            "independent records of one scope, so a disagreement means either a "
            "tuple entry was deleted while its module still declares itself, or "
            "a module's marker was deleted while the tuple still names it. "
            "Narrowing the scope takes both edits, and this is the test that "
            "makes each one alone visible."
        )
        assert len(derived) < len(sources), (
            f"{marker} selected the whole of tests/, so the derivation "
            "discriminates between no modules and would agree with any tuple."
        )

    assert set(CENSUSED_MODULES) <= set(FENCED_MODULES), (
        f"{sorted(set(CENSUSED_MODULES) - set(FENCED_MODULES))} is censused "
        "without being fenced, so its strings would be accounted for and then "
        "left ungraded."
    )


def test_every_string_and_comment_in_a_censused_module_is_read_or_exempt(repo_root: Path) -> None:
    sources = _sources_under(repo_root, "tests")
    for path in CENSUSED_MODULES:
        assert path in sources, f"{path} is censused and no such module was read"
        census = string_census(sources[path])

        assert census.extracted, (
            f"the census read no prose at all out of {path}. A census whose "
            "extracted set is empty balances by exempting the rest, which is "
            "the vacuous green contract 6 exists to prevent."
        )
        assert not census.unaccounted, (
            f"string literals in {path} that no prose channel reads and no "
            f"exemption claims: {list(census.unaccounted)}. Contract 6 admits "
            "two dispositions and no third: read it as prose, or match it with "
            "an exemption that carries a control pinning its boundary. Leaving "
            "it here means a sentence written in that position is invisible to "
            "the fence, which is the hole CS-420 measured rather than guessed."
        )
        assert len(census.extracted) + len(census.exempt) == census.total, (
            f"the census of {path} does not balance: {len(census.extracted)} "
            f"read plus {len(census.exempt)} exempt against {census.total} total."
        )

        comments = comment_census(sources[path])
        assert comments["comment"], (
            f"the census read no comment token at all out of {path}, so the "
            "comment half of contract 6 would pass on an empty scan."
        )
        assert not comments["unaccounted"], (
            f"comment tokens in {path} the run grouper did not yield, at lines "
            f"{list(comments['unaccounted'])}. tokenize found them and the "
            "extractor did not, so prose is being dropped between the two."
        )


def test_a_marked_claim_at_each_parse_derived_position_is_caught(repo_root: Path) -> None:
    sources = _sources_under(repo_root, "tests")
    for path in CENSUSED_MODULES:
        source = sources[path]
        rendered = ast.unparse(ast.parse(source))

        assert not unbacked_absolutes(path, rendered, sources), (
            f"{path} reports a finding with NO claim inserted, so the "
            "comparison below would credit the fence with catching a claim it "
            "did not catch. Rendering drops comments and leaves the rest as it "
            "was, so a finding here means the pristine module is already red."
        )

        by_scan: list[int] = []
        by_census: list[int] = []
        missed: list[str] = []
        for lineno, kind, mutant in string_position_mutants(source, _MARKED_CLAIM):
            reported = bool(unbacked_absolutes(path, mutant, sources))
            unaccounted = bool(string_census(mutant).unaccounted)
            if kind in _PROSE_KINDS and reported:
                by_scan.append(lineno)
            elif kind in _EXEMPT_KINDS and unaccounted:
                by_census.append(lineno)
            else:
                missed.append(f"line {lineno} ({kind}) scan={reported} census={unaccounted}")

        assert not missed, (
            f"a claim written into these positions of {path} was caught by "
            f"neither the scan nor the census: {missed}. A prose position has "
            "to be REPORTED, and an exempt position has to fall out of the "
            "census - an exemption that stays quiet when a sentence is written "
            "into it is a hole with a control bolted to it."
        )
        assert by_scan, (
            f"no position in {path} was caught by the SCAN, so the prose half "
            "of this control graded an empty population."
        )
        assert by_census, (
            f"no position in {path} was caught by the CENSUS, so the exemption "
            "half of this control graded an empty population and the boundary "
            "of the exempt class is unpinned."
        )

        comment_missed = [
            lineno
            for lineno, mutant in comment_position_mutants(source, _MARKED_CLAIM)
            if not unbacked_absolutes(path, mutant, sources)
        ]
        assert not comment_missed, (
            f"a claim written over the comment at these lines of {path} was "
            f"not reported: {comment_missed}. The dropped-as-blank and "
            "dropped-as-rule comment classes are exemptions too, so a comment "
            "position that swallows a sentence is the same hole in the other "
            "channel."
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
    assert set(_PARAGRAPH_KINDS) <= kinds, (
        f"the scanner read only {sorted(kinds)} out of the red control, which "
        f"carries a quantifier in each of contract 5's kinds "
        f"{sorted(_PARAGRAPH_KINDS)}. A kind the scan skips is a place the "
        "banned sentence may be written."
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


def test_prose_is_read_from_the_declared_kinds_and_not_from_a_data_literal() -> None:
    paragraphs = prose_paragraphs(_CONTROL_RED)
    kinds = {p.kind for p in paragraphs}
    assert kinds == set(_PARAGRAPH_KINDS), (
        f"the extractor did not recover contract 5's prose kinds: it read "
        f"{sorted(kinds)} where {sorted(_PARAGRAPH_KINDS)} are declared. The "
        "corpus carries one of each, so a shortfall is a channel that has "
        "stopped reading rather than a corpus that stopped covering."
    )

    carriers = [p.kind for p in paragraphs if "IT NEVER RAISES" in p.text]
    assert carriers == ["docstring"], (
        f"the banned sentence was read out of more than the docstring holding "
        f"it: {carriers}. The control corpora in this file are module-level "
        "assignments, so a reader that treated an assignment as prose would make "
        "this module fail itself, and the corpora would have to be moved out "
        "behind a scope rule - which is the artifact contract 1 refuses."
    )


def _corpus_line(corpus: str, needle: str) -> int:
    """Where a fragment sits in a control corpus, so no line number is written.

    Args:
        corpus: One of the corpora authored in this module.
        needle: Text identifying the line.

    Returns:
        The 1-indexed line number.

    Raises:
        AssertionError: If the fragment is absent, so editing a corpus out from
            under a control fails loudly rather than shifting what it grades.
    """
    for number, line in enumerate(corpus.splitlines(), start=1):
        if needle in line:
            return number
    raise AssertionError(f"the control corpus no longer carries {needle!r}")


def test_the_module_constant_exemption_stops_at_a_sentence_and_at_function_scope() -> None:
    census = string_census(_CONTROL_CENSUS)
    exempt = {lineno for lineno, kind in census.exempt if kind == _MODULE_CONSTANT}
    unaccounted = {lineno for lineno, _ in census.unaccounted}

    assert exempt == {_corpus_line(_CONTROL_CENSUS, "TOKEN =")}, (
        f"the module-scope token was not the one string exempted: {census.exempt}. "
        "The exemption is what lets a terminator word and a counter key stay out "
        "of the prose scan."
    )
    assert _corpus_line(_CONTROL_CENSUS, "SENTENCE =") in unaccounted, (
        "a module-scope assignment holding a SENTENCE was exempted alongside the "
        "token beside it. That is the write-anything channel: an exemption keyed "
        "on the slot rather than on what the string is would swallow any "
        "sentence an author put there, and the scan would not see it."
    )
    assert _corpus_line(_CONTROL_CENSUS, "inner =") in unaccounted, (
        "a FUNCTION-scope assignment holding a token was exempted. The exemption "
        "is bounded to module scope because that is where the constants it "
        "covers are declared; widening it silently is how a scope rule grows."
    )


def test_the_census_reads_a_direct_call_argument_and_not_one_nested_inside_a_literal() -> None:
    census = string_census(_CONTROL_CENSUS)
    argument = {lineno for lineno, kind in census.extracted if kind == "argument"}
    unaccounted = {lineno for lineno, _ in census.unaccounted}
    nested = {
        _corpus_line(_CONTROL_CENSUS, "TABLE ="),
        _corpus_line(_CONTROL_CENSUS, "wrap("),
    }

    assert _corpus_line(_CONTROL_CENSUS, "skip(") in argument, (
        f"the sentence passed DIRECTLY to a call was not read as prose: "
        f"{census.extracted}. That position is where pytest.skip carries a "
        "reason to the operator, and CS-435 shipped a false universal in its "
        "sibling, a warning detail, which no channel could see."
    )
    assert nested <= unaccounted, (
        f"a string nested inside a dict was read as a direct argument: "
        f"{census.extracted}. Reading those would make this module fail itself "
        "on its own grammar table, which is a list of regexes inside a dict "
        "inside a call - so the boundary is load-bearing rather than tidy."
    )


def test_the_comment_census_separates_prose_from_a_rule_and_a_blank() -> None:
    census = comment_census(_CONTROL_COMMENT_CENSUS)

    assert census == {
        "comment": (2, 4, 5, 6),
        "rule": (1,),
        "blank": (3,),
        "unaccounted": (),
    }, (
        f"the comment classifier put a token in the wrong class: {census}. Line "
        "5 opens like a horizontal rule and carries text, so it is prose; line "
        "6 is a trailing comment beside code, which is prose too. Widening "
        "either exemption to cover them would drop authored text on the floor."
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
