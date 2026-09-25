"""CS-891 - the bare-path shape, its decline ladder, and the walks that close them.

WHY THIS MODULE EXISTS AS A SEPARATE FILE, and the reason is a size gate rather
than a design one, which is worth saying plainly instead of inventing a nobler
motive after the fact. ``tests/test_docs_citations.py`` grew past the size ceiling
that ``tests/data/test_phase2_gate.py`` asserts over every file under ``tests/`` -
the number lives there and is deliberately not restated here. That ceiling is a
NON-NEGOTIABLE 2 GUARD: it is the one check that
catches a trimmed slice of real game data dropped into a fixture directory, which
no content assertion would catch because a real slice parses perfectly. Raising it
to fit prose would launder a data-hygiene guard for a code-size reason, so the
module was split instead.

WHAT MOVED IS THE DERIVATION AND NOT THE JUDGEMENT. The shape, the ladder and the
two walk primitives live here; every arm that grades them stays where it was, and
imports what it needs. No test identifier changed in the move.

THE HAZARD THE SPLIT CREATES, WHICH IS THE WHOLE REASON THE COMPANION ARMS EXIST.
``tests/test_docs_citations.py`` closes two classes by walking its OWN globals:

  * every compiled ``*_RE`` must be a member of its boundary's judged shapes, so
    a new pattern cannot be judged by an arm while the boundary stays blind to it
  * every module-scope container must be bounded as a forgiveness or recorded as
    forgiving nothing, so a SIXTH escape hatch is red until somebody answers

A NAIVE SPLIT REOPENS EXACTLY THE EVASION THOSE WALKS FORBID. Declare a pattern or
a forgiveness table HERE and do not import it, and neither walk sees it: the table
forgives, the ladder consults it, and nothing counts it. That is the same fault as
naming a table so a filter misses it - which this family already refuted once as a
naming trick - arriving by another door.

AN IMPORTED NAME IS IN ``globals()``, which is what makes the mitigation cheap: a
pattern or table imported back into the module that judges it is walked exactly as
before. THAT ALONE IS NOT SUFFICIENT and the insufficiency is the point. So
``tests/test_bare_path_citations.py`` walks BOTH modules, over a population
DERIVED FROM THE IMPORT GRAPH rather than hand-listed - a hand-list of two is the
same fault as the hand-list of three this round already had to repair, one file
along.

THE WALK PRIMITIVES HAVE ONE OWNER, AND THEIR NAMESPACE IS REQUIRED RATHER THAN
DEFAULTED. :func:`module_containers` used to fall back to ``globals()``, which is
correct in exactly one module and silently wrong in every other - a function that
reads the wrong module's namespace and answers confidently is the shape this file
exists to close, so the parameter has no default.
"""

from __future__ import annotations

import ast
import importlib
import re
import subprocess
import tomllib
from collections.abc import Callable, Iterable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Final

#: This checkout's root. Derived from this file's own location rather than
#: passed in, and the ONE owner of the fact - the modules that judge citations
#: import it from here instead of each recomputing it, so two of them cannot
#: come to disagree about where the repository starts.
REPO_ROOT: Final = Path(__file__).resolve().parents[1]


# CS-891 - THE FIFTH SHAPE: A REPO-RELATIVE PATH WITH NOTHING AFTER IT.
#
# Every shape above needs a SEPARATOR after the path - a name after "::", or a
# number after a colon - so a doc that spells a module path plainly was matched
# by NONE of them. A pointer at a path that does not exist was green in every
# file in this repository, which is CS-442's founding finding one more level
# up: not "nothing read docs/", but "nothing read the commonest thing a doc
# says about the tree".
#
# THE BACKTICKS ARE THE SHAPE, not decoration, and that was MEASURED rather
# than preferred. On the tree this shape was derived against, the same pattern
# without them read 2944 sites where this one read 1996 - a past measurement
# with its corpus named, not a live count - and the 948 it adds are not prose:
# `.gitignore` PATTERNS, a
# workflow's YAML values, and a doc-budget fixture path. THREE of those reach
# the reported rung and all three are artifacts of reading configuration as if
# it were a sentence. A backtick is this repository's own marker for "this
# token is a path" - CLAUDE.md, the ADRs, the ledger and every docstring here
# use it - so requiring one is the cheapest available test of AUTHORIAL INTENT
# TO CITE, which is the property trap 2 says a path alone does not carry.
#
# THE PRICE, STATED RATHER THAN IMPLIED AWAY: a dead path spelled in prose
# WITHOUT backticks is invisible to this arm. That hole is real and it is NOT
# pinned, because pinning it would mean maintaining the wider pattern's
# 948-site residual forever in order to guard three sites that measured
# artifactual. The three declines below ARE pinned, because each is a rule
# rather than a pattern's edge.
#
# THE SECOND PRICE, WHICH THE FIRST BUILD DID NOT STATE AT ALL. The extension
# alternation below is a HAND-MAINTAINED SUFFIX LIST - the very boundary
# :func:`tests.test_docs_citations.line_pointer_carriers` records at length as
# the wrong one, because "the next extension to start carrying a pointer joins
# the unguarded set in silence". That was fixed on the CARRIER side and the
# identical list then
# shipped on the CITED side unmentioned.
#
# THE RESIDUAL, MEASURED: 86 backticked sites in exactly this shape fall outside
# it - 77 JavaScript under `shell/`, a root this repository owns and ships, plus
# html, css, C headers, a lock file and an archive, spread over `ROADMAP.md`,
# `docs/LEDGER.md`, `docs/OPERATIONS.md`, an ADR and a phase leaf. A dead
# citation among them is invisible to this arm.
#
# WIDENING WAS MEASURED AND DEFERRED, NOT DISMISSED: it moves the population
# from 2009 sites to 2095 with the reported rung still EMPTY, at a cost of four
# new disclosure rows. It is not taken here because it also widens what
# :func:`tests.test_docs_citations.carries_a_citation` answers, which moves the
# guarded-set boundary, and a repair slice that grows the adjudicated population
# is doing two jobs.
#
# A NON-LEADING SEGMENT MAY NOT START WITH A DOT, which refuses "..", and that
# is a mechanism rather than tidiness. `git check-ignore` FATALS on a path that
# escapes the repository - measured, on the traversal fixture in
# `tests/surface/test_server.py` - and one fatal kills the whole batch, so R2
# would silently stop declining for every path at once. The shape refuses the
# escape AND :func:`declares_untracked` fails loudly on a bad exit, so neither
# has to be trusted alone.
#
# THE FIRST SEGMENT MAY, because `.github/workflows/tier1.yml` is a real
# citation and a pattern anchored on an alphanumeric drops the dot and then
# reports a path that does not exist - the same measurement that shaped
# :data:`tests.test_docs_citations.LINE_POINTER_RE`.
#
# NO NESTED QUANTIFIER OVER OVERLAPPING CLASSES. Each repetition must begin
# with "/" and each segment with a character no other alternative accepts, so
# the pattern cannot backtrack exponentially on a near-miss. A guard that hangs
# on one unlucky line is a guard that gets switched off.
# CS-899 - THE ABSENCE DECLARATION, AND WHY IT IS A MECHANISM RATHER THAN A
# FORGIVENESS.
#
# THE PROBLEM IT ANSWERS. R4 partitions a PYTHON carrier by AST into author
# prose and the data a module feeds itself, and on this tree that partition is
# exact. Markdown has no AST and no equivalent, so prose that DISCUSSES a dead
# path - an ADR recording that a file is deliberately not created, a phase leaf
# naming a module phase 5 will build - was indistinguishable by shape from
# prose that CITES one. The only answer available was an entry in
# :data:`tests.test_citation_tables.BARE_PATH_REASONS`, and a keyword or
# negation detector over the sentence was priced and REFUSED for failing in the
# PERMISSIVE direction.
#
# THE DIFFERENCE FROM A RECORDED FORGIVENESS, WHICH IS THE WHOLE CLAIM AND IS
# NOT A PREFERENCE. This module's own table comment says a ``NO_TARGET`` or
# ``DELIBERATE`` disposition is the kind that NAMES NOTHING TO CHECK. A
# declaration names something checked on EVERY run, in three directions:
#
#   - the path it calls absent must still be absent, or the site is REPORTED
#     at :data:`DECLARED_ABSENT_BOUND` - so it cannot be spent once and left;
#   - the line it sits on must still spell that path as a citation, or
#     :func:`stale_declaration_problems` reports it - so prose that moves on
#     cannot leave it behind;
#   - it buys silence for ONE path on ONE line and for nothing else.
#
# AND IT TRAVELS WITH THE SENTENCE, which answers the question CS-891's merger
# demanded before dispatch and nobody answered: a forgiveness recorded against
# a carrier that is rewritten every session is a landmine, because the record
# outlives the prose. A declaration cannot outlive its line.
#
# THE PRICE, STATED. A declaration is authored, so an author can write one over
# a genuinely dead citation. It is not free to do so - the path must be absent
# AND stay absent AND the line must keep spelling it - but the spelling itself
# is an assertion by a human, exactly as `.gitignore` is R2's and as a
# docstring is R4's. What it cannot do is go quiet: every other route to
# silence here is a row in a table under a ceiling, and this one reddens on its
# own when the tree moves.
#
# THE SHAPE IS AN HTML COMMENT because markdown renders it as nothing, this
# tree already uses one for machine-and-human metadata in four files, and the
# path inside it carries NO BACKTICKS - so :data:`BARE_PATH_RE` does not read
# the declaration itself as a second citation of the same path.
ABSENT_DECLARATION_RE: Final = re.compile(r"<!--\s*absent:\s*([^\s>]+?)\s*-->")

_FIRST_SEGMENT: Final = r"\.?[A-Za-z0-9_][A-Za-z0-9_.-]*"
_LATER_SEGMENT: Final = r"[A-Za-z0-9_][A-Za-z0-9_.-]*"
BARE_PATH_RE: Final = re.compile(
    rf"`({_FIRST_SEGMENT}(?:/{_LATER_SEGMENT})*/{_LATER_SEGMENT}"
    r"\.(?:py|md|json|toml|yml|yaml|cfg|txt|ini))`"
)


# --- CS-891: the bare-path arm and its DECLINE LADDER -----------------------
#
# FIVE RUNGS, ORDERED, EACH MECHANICALLY DECIDABLE, and every site reports
# WHICH rung answered it. The distribution is the point: a single pass/fail
# number is silent about which half of the ladder did the work, so a rung that
# quietly stops firing - the check-ignore batch that stopped declining, below -
# looks exactly like a corpus that stopped needing it.
#
#   R0   the cited path is in `git ls-files`                        RESOLVED
#   R1   exactly ONE tracked path UNDER A DECLARED SOURCE ROOT ends with it
#        at a segment boundary                                       RESOLVED
#   R1!  MORE THAN ONE does                                          REPORTED
#   R2   `git check-ignore` says the repo DECLARES it untracked      DECLINED
#   R3   its first segment is not a tracked top-level entry          DECLINED
#   R4   the site sits in a Python string literal that is NOT a docstring
#                                                                    DECLINED
#   R5   the site is recorded in
#        :data:`tests.test_citation_tables.BARE_PATH_REASONS`
#                                                                    FORGIVEN
#        otherwise                                                   REPORTED
#
# WHY EACH DECLINE IS PRINCIPLED RATHER THAN CONVENIENT. A decline that is
# merely convenient is a permission list wearing a rule's clothes, so each one
# below states the mechanism that decides it and the price it charges.
#
# R1 IS TRAP 2 ONE NOTCH ALONG. This module's own docstring records that
# resolving an UNQUALIFIED name repo-relative and calling it missing
# manufactured six dead targets and ALL SIX WERE ARTIFACTS. A PARTIALLY
# qualified path is the same shape: `docs/ARCHITECTURE.md` writes a module map
# whose paths are relative to a package root stated in the surrounding table,
# so seventeen of its forty qualified paths are absent repo-relative and
# present one directory down.
#
# WHAT R1 PROVES AND WHAT IT DOES NOT. The first build said it needed no ratchet
# because it "is a RESOLUTION rather than a forgiveness" - restating trap 2's own
# property as though stating it had solved it. A UNIQUE SUFFIX HIT PROVES THE
# PATH NAMES A TRACKED FILE, NEVER THE INTENDED ONE. Those coincide only where
# the tree has one candidate per suffix, and `tests/` MIRRORS the package tree:
# a citation naming a helper under its `save` mirror had exactly one hit and it
# WAS that helper, which has no package counterpart. MEASURED: three such
# citations planted in the module map's own house style left the suite green -
# no finding, no disclosure grown, no ceiling spent - and one resolved into
# `.claude/`, which this module declares out of domain entirely.
#
# SO R1's CANDIDATE SET IS ROOTED. :func:`source_roots` derives from tracked
# packaging manifests which directories this repository SHIPS, and a hit outside
# them does not resolve. Still not a ratchet and still needing none - the rung
# can only RESOLVE - but now against the population a package-relative citation
# could be relative to. AND IT MUST STILL REQUIRE EXACTLY ONE HIT: an ambiguous
# suffix is REPORTED, because accepting it turns "the reader guessed" into "the
# citation resolved".
#
# R2 IS ANSWERED BY A TRACKED DECLARATION A HUMAN HAD TO WRITE. `.gitignore` is
# in the index; a path it matches is one this repository has said out loud will
# never be tracked. Two of its lines carry the whole rung: the local config
# override, and the game install's own directory - which is untracked for
# EXACTLY the reason the citation is legitimate, since non-negotiable 2 forbids
# committing anything extracted from the install. Calling such a citation dead
# would be reporting the repository for obeying its own rule.
#
# R3: A PATH WHOSE ROOT THIS REPO DOES NOT OWN IS NOT A REPO-RELATIVE CITATION.
# It is a metasyntactic example, or a fragment relative to something else. The
# roots MEASURED in the live corpus are the package-relative "advisor", and the
# example roots "also", "not" and "notes" that a guard's own fixtures spell.
#
# R4 IS AST-DECIDABLE, NOT A PROSE HEURISTIC, which is what makes it a rule
# rather than a hunch. A Python string literal that is not a docstring is
# DATA the module operates on; a docstring and a comment are the author
# TALKING. The split was measured over every tracked Python file and it is
# PERFECT: author prose holds every real citation, non-docstring literals hold
# every synthetic fixture path, and nothing sits in between.
#
# THE PRICE OF R2, R3 AND R4, STATED AND PINNED. A dead citation hidden under a
# broad gitignore pattern, or under an invented root, or inside a non-docstring
# literal, is INVISIBLE to this arm. So each rung's live membership is pinned
# below and asserted in BOTH directions: appending to a disclosure makes it
# DISAGREE with what the ladder derives and reddens, exactly as
# :data:`tests.test_docs_citations.UNFORBIDDEN_LINE_POINTERS` does.
#
# AND EACH DISCLOSURE IS ALSO BUDGETED, because "nothing can be added to one to
# buy silence" was the first build's claim and it was FALSE. The two-way pin
# catches a row added ALONE; it cannot catch a row added TOGETHER WITH the dead
# citation it describes, and that pair is exactly the purchase. Worse, it was the
# CHEAP purchase: the same dead citation spelled one segment longer costs an R5
# entry AND a ceiling raise, so the vaguer spelling was the less guarded one.
# Every rung here now spends a number somebody has to defend.

#: CS-899's rung, and it sits ABOVE R0 because it is TWO-WAY. Every other rung
#: asks whether a spelling resolves; this one asks whether a spelling the
#: carrier DECLARES absent is still absent, and a declaration the tree has
#: falsified is a finding rather than a resolution. Answering it after R0 would
#: mean a path that came back read as RESOLVED - green - with the sentence
#: around it now false and nothing said.
DECLARED_ABSENT: Final = "Rd declared absent"
DECLARED_ABSENT_BOUND: Final = "Rd! declared absent but bound"
RESOLVED_EXACT: Final = "R0 exact"
RESOLVED_SUFFIX: Final = "R1 unique suffix"
AMBIGUOUS_SUFFIX: Final = "R1! ambiguous suffix"
DECLARED_UNTRACKED: Final = "R2 declared untracked"
UNTRACKED_ROOT: Final = "R3 untracked root"
FIXTURE_LITERAL: Final = "R4 fixture literal"
RECORDED_REASON: Final = "R5 recorded reason"
UNRESOLVED: Final = "REPORTED"

#: Every rung, in the order they are tried. DERIVED FROM HERE by the ladder and
#: by every arm that reads a distribution, so a rung cannot be added to one and
#: missed by the other.
LADDER_RUNGS: Final = (
    DECLARED_ABSENT,
    DECLARED_ABSENT_BOUND,
    RESOLVED_EXACT,
    RESOLVED_SUFFIX,
    AMBIGUOUS_SUFFIX,
    DECLARED_UNTRACKED,
    UNTRACKED_ROOT,
    FIXTURE_LITERAL,
    RECORDED_REASON,
    UNRESOLVED,
)


@dataclass(frozen=True)
class BarePathSite:
    """One spelling of one bare repo-relative path in one carrier.

    Attributes:
        carrier: The file that spells it, repo-relative and POSIX-separated.
        cited: The path as spelled.
        line: 1-based line of the spelling, for the report only. DELIBERATELY
            NOT PART OF :attr:`identity` - see that property.
        column: 0-based column, used only to decide R4.
        anchor: The enclosing qualified symbol for a Python carrier, the
            nearest preceding heading for a markdown one, empty otherwise.
        in_fixture_literal: Whether the site sits inside a Python string
            literal that is not a docstring. Computed once at collection so the
            ladder stays a pure function of its arguments and a control can
            construct a site without a file behind it.
        declared_absent: Whether the LINE this spelling sits on also carries an
            absence declaration naming this same path. Computed at collection
            for :attr:`in_fixture_literal`'s reason, and DEFAULTED so that
            every control already constructing a site by hand keeps meaning
            what it meant.
    """

    carrier: str
    cited: str
    line: int
    column: int
    anchor: str
    in_fixture_literal: bool
    declared_absent: bool = False

    @property
    def identity(self) -> tuple[str, str, str]:
        """The key every table in this section is written against.

        AN IDENTITY, NOT A COUNT, and CS-893 is filed against this module for
        getting that wrong one table over. The `Disposition` table carried a bare
        count until CS-1121, so a COMPENSATING SWAP - delete one recorded site
        and add an unrelated one in the same edit - left the cardinality
        unchanged and passed in silence. A set of identities reports both halves
        of that swap. That table now carries site identities of its own.

        AN ANCHOR RATHER THAN A LINE, AND THAT WAS MEASURED. Prepending one
        session entry to a markdown file shifts every line below it and rewrites
        nothing under any heading, so a line-keyed table churns on an edit that
        changed none of what it records while an anchored one does not. It is
        the same reason trap 3 declines to judge a `file:line` pointer into an
        append-only file, applied to the table instead of to the pointer.

        WHAT AN ANCHOR CANNOT SEE, disclosed: two spellings of the same path
        under the same symbol are one identity. That is why each table below
        also records HOW MANY sites the identity covers - the identity closes
        the swap, the count closes the second spelling, and neither alone does
        both. `tests/chained_cause_guard.py` and `tests/pathless_clone_guard.py`
        already key on qualified names for the first half of this reason.
        """
        return (self.carrier, self.cited, self.anchor)


@dataclass(frozen=True)
class BarePathReason:
    """One recorded answer for one bare-path site that does not resolve.

    Attributes:
        why: The evidence, in one line, so the table is auditable without
            re-deriving it.
        sites: How many spellings this identity covers, for the reason
            :attr:`BarePathSite.identity` gives.
    """

    why: str
    sites: int


def markdown_anchor(text: str, line: int) -> str:
    """The nearest heading at or above ``line``, or empty above the first one."""
    heading = ""
    for number, raw in enumerate(text.split("\n"), start=1):
        if number > line:
            break
        if raw.startswith("#"):
            heading = raw.strip()
    return heading


def python_anchor(tree: ast.AST, line: int) -> str:
    """The innermost qualified symbol enclosing ``line``.

    Falls back to the module-level assignment target when no ``def`` or
    ``class`` encloses the line, so a path inside a module-level table is
    identified by the table it is in rather than by nothing at all. That
    fallback is not cosmetic: without it, five fixture paths in one module
    collapsed to a single identity and a sixth could have arrived unseen.

    Args:
        tree: The parsed carrier.
        line: 1-based line number.

    Returns:
        A dotted qualified name, the assignment target's name, or empty.
    """
    best = ""
    stack: list[tuple[str, ast.AST]] = [("", tree)]
    while stack:
        prefix, node = stack.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = f"{prefix}.{child.name}" if prefix else child.name
                end = getattr(child, "end_lineno", None) or child.lineno
                if child.lineno <= line <= end and len(qualified) > len(best):
                    best = qualified
                stack.append((qualified, child))
            else:
                stack.append((prefix, child))
    if best:
        return best
    for statement in getattr(tree, "body", []):
        end = getattr(statement, "end_lineno", None) or statement.lineno
        if not statement.lineno <= line <= end:
            continue
        targets: list[ast.expr] = []
        if isinstance(statement, ast.Assign):
            targets = list(statement.targets)
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
        for target in targets:
            if isinstance(target, ast.Name):
                return target.id
    return ""


def fixture_literal_spans(tree: ast.AST) -> tuple[tuple[int, int, int, int], ...]:
    """Every string-literal span that is NOT a docstring.

    R4's whole mechanism. A docstring is the author talking about the code; any
    other string literal is DATA the code operates on, and in this repository
    that data is overwhelmingly a synthetic fixture path that is supposed not
    to exist. The distinction is decided by the parse tree rather than by
    reading the sentence, which is what makes it a rule.

    F-strings are included whole, because a path may be spelled across a
    ``JoinedStr``'s parts and a span per part would leave the seam unjudged.

    Args:
        tree: The parsed carrier.

    Returns:
        ``(start_line, start_col, end_line, end_col)`` per literal, 1-based
        lines and 0-based columns, in no particular order.
    """
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = node.body
        if body and isinstance(body[0], ast.Expr):
            value = body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                docstrings.add(id(value))
    spans: list[tuple[int, int, int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Constant, ast.JoinedStr)):
            continue
        if isinstance(node, ast.Constant) and not isinstance(node.value, str):
            continue
        if id(node) in docstrings:
            continue
        end_line, end_column = node.end_lineno, node.end_col_offset
        if end_line is None or end_column is None:
            continue
        spans.append((node.lineno, node.col_offset, end_line, end_column))
    return tuple(spans)


def live_declarations(
    raw: str,
    number: int,
    spans: Sequence[tuple[int, int, int, int]],
) -> list[str]:
    """The absence declarations on one line that the AUTHOR wrote.

    R4, ONE FUNCTION, TWO CALLERS, and it is one function because it was two.
    :func:`stale_declaration_problems` applied the partition and
    :func:`bare_path_sites` did not, so a declaration written inside a
    non-docstring string literal silenced a genuinely dead citation spelled
    OUTSIDE that literal on the same line, AND was exempt from the staleness
    direction besides - two of the three directions, on a shape whose docstring
    claims all three. A verifier measured it; nothing in the round that built
    it did. Two callers asking the same question in two places is the fault
    this family's own boundary contract exists to refuse, arriving inside the
    repair that added the question.

    Args:
        raw: The line's text.
        number: Its 1-based line number, for the span test.
        spans: The carrier's non-docstring string-literal spans, empty for a
            carrier with no parse tree.

    Returns:
        Every declared path on the line, in the order written, less the ones
        sitting inside a fixture literal.
    """
    return [
        match.group(1)
        for match in ABSENT_DECLARATION_RE.finditer(raw)
        if not any((sl, sc) <= (number, match.start()) <= (el, ec) for sl, sc, el, ec in spans)
    ]


def bare_path_sites(carriers: Mapping[str, str]) -> list[BarePathSite]:
    """Every bare-path spelling in every carrier, with its identity attached.

    THE POPULATION IS THE CALLER'S, injected rather than derived here, so the
    live arm can hand it :func:`tests.test_docs_citations.line_pointer_carriers` - the boundary a
    contract already asserts - instead of this section growing a second
    population that is a second thing to rot.

    Args:
        carriers: Carrier path to the text its citations are read from.

    Returns:
        One :class:`BarePathSite` per spelling, carriers in sorted order.
    """
    sites: list[BarePathSite] = []
    for carrier in sorted(carriers):
        text = carriers[carrier]
        tree: ast.AST | None = None
        spans: tuple[tuple[int, int, int, int], ...] = ()
        if carrier.endswith(".py"):
            try:
                tree = ast.parse(text)
            except SyntaxError:
                tree = None
            else:
                spans = fixture_literal_spans(tree)
        lines = text.split("\n")
        declared = [
            frozenset(live_declarations(raw, number, spans))
            for number, raw in enumerate(lines, start=1)
        ]
        starts = [0]
        for raw in lines:
            starts.append(starts[-1] + len(raw) + 1)
        for match in BARE_PATH_RE.finditer(text):
            offset = match.start(1)
            line = 1
            while line < len(starts) and starts[line] <= offset:
                line += 1
            column = offset - starts[line - 1]
            if tree is not None:
                anchor = python_anchor(tree, line)
            elif carrier.endswith(".md"):
                anchor = markdown_anchor(text, line)
            else:
                anchor = ""
            sites.append(
                BarePathSite(
                    carrier=carrier,
                    cited=match.group(1),
                    line=line,
                    column=column,
                    anchor=anchor,
                    in_fixture_literal=any(
                        (sl, sc) <= (line, column) <= (el, ec) for sl, sc, el, ec in spans
                    ),
                    declared_absent=match.group(1) in declared[line - 1],
                )
            )
    return sites


#: Wall-clock bound for the git plumbing below (CS-896). An unbounded child
#: cannot fail the test that owns it - it burns the CI job's whole budget until
#: the lane is cancelled, which is evidence of nothing. 120s matches the git
#: timeout in tests/test_doc_budget.py and tests/test_commit_msg_gate.py. It is
#: deliberately generous: the job is to bound a hang, not to police speed, and a
#: tight value under two-worker contention on a 2-vCPU runner is a new flake.
GIT_TIMEOUT: Final = 120


def declares_untracked(paths: Sequence[str]) -> frozenset[str]:
    """Which of ``paths`` this repository's own `.gitignore` declares untracked.

    R2's evidence. Asked of git rather than reimplemented, because gitignore
    precedence - negations, directory patterns, per-directory files - is a
    specification this module has no business owning a second copy of.

    THE STDIN IS BINARY AND THE SEPARATOR IS NUL, AND BOTH ARE LOAD-BEARING.
    Under ``text=True`` on Windows the newline separator is translated to CRLF
    ON WRITE, git receives a path with a trailing carriage return, answers NOT
    IGNORED for every one of them, and this rung silently stops declining.
    MEASURED: the first run of this ladder under text mode reported R2 as zero
    and would have recorded seven mechanically declinable sites as
    forgivenesses instead. It fails toward MORE findings, which is the loud
    direction, and a table twice the size still looks plausible - which is
    exactly why the failure needs a mechanism rather than a reader.

    IT FAILS LOUDLY RATHER THAN DEGRADING. An unavailable subcommand, a fatal
    on a path outside the repository, or a git that is not there at all would
    otherwise all read as "nothing is ignored", which is the same output as a
    clean corpus. Exit 0 means at least one match and exit 1 means none;
    anything else is raised.

    Args:
        paths: Repo-relative POSIX paths. ASCII by non-negotiable 4, and
            encoded as ASCII here so a byte outside it is an error rather than
            a silent re-encoding.

    Returns:
        The subset git says is ignored.
    """
    if not paths:
        return frozenset()
    probe = subprocess.run(
        ["git", "check-ignore", "--no-index", "-z", "--stdin"],
        input=("\0".join(paths) + "\0").encode("ascii"),
        capture_output=True,
        cwd=REPO_ROOT,
        timeout=GIT_TIMEOUT,
        # Exit 1 means NO path matched, which is an answer rather than a
        # failure. The exits that ARE failures are raised below, so the
        # subprocess must not raise on the one that is not.
        check=False,
    )
    if probe.returncode not in (0, 1):
        raise RuntimeError(
            f"git check-ignore is unusable (exit {probe.returncode}):"
            f" {probe.stderr.decode('utf-8', 'replace').strip()}."
            " R2 cannot be decided, and treating that as 'nothing is ignored'"
            " would silently promote every declinable site to a finding."
        )
    return frozenset(found.decode("ascii") for found in probe.stdout.split(b"\0") if found)


def tracked_suffixes(tracked: Iterable[str]) -> dict[str, tuple[str, ...]]:
    """Every proper path suffix of every tracked file, at segment boundaries.

    R1's index. ``clockspeed/data/locate.py`` contributes ``data/locate.py``
    and ``locate.py``; the whole path is R0's business and is not indexed here.

    Args:
        tracked: Repo-relative POSIX paths.

    Returns:
        Suffix to the tracked paths carrying it, so the caller can require
        exactly one.
    """
    index: dict[str, list[str]] = {}
    for path in tracked:
        segments = path.split("/")
        for cut in range(1, len(segments)):
            index.setdefault("/".join(segments[cut:]), []).append(path)
    return {suffix: tuple(sorted(hits)) for suffix, hits in index.items()}


#: The manifest key that names the Python distribution's source packages. Read
#: rather than restated, for :func:`source_roots`' reason.
_SETUPTOOLS_FIND: Final = ("tool", "setuptools", "packages", "find", "include")

#: The file whose presence in a top-level directory declares that directory a
#: Node package. `shell/` carries one; nothing else in this repository does.
_NODE_MANIFEST: Final = "package.json"


def source_roots(tracked: Iterable[str], manifest: str) -> frozenset[str]:
    """Which top-level directories this repository PACKAGES as source.

    R1'S CANDIDATE SET, AND THE REASON IT HAS ONE. A unique suffix hit proves
    the path names A tracked file, never THE intended one. `tests/` MIRRORS the
    package tree, so a citation naming a helper under its `save` mirror has
    exactly one hit and it IS that helper, which has no package counterpart at
    all. MEASURED: three dead citations planted in `docs/ARCHITECTURE.md`'s own
    house style resolved silently at R1 - no finding, no disclosure grown, no
    ceiling spent - and one resolved into `.claude/`, which this module declares
    out of domain. Trap 2's own property, unrepaired, one notch along.

    NEITHER PURE RULE WORKS, WHICH IS WHY IT IS A ROOTED SUFFIX. A prefix test
    breaks the module-map spellings that omit two directories rather than one; a
    suffix test alone launders. Requiring the sole hit under a DECLARED SOURCE
    ROOT does both: all ten live module-map spellings still resolve uniquely,
    and every planted mirror-tree path falls through.

    DERIVED FROM TRACKED DECLARATIONS, NOT HAND-LISTED, because a literal root
    tuple is a boundary nobody re-derives and the next root would join the
    unguarded set in silence. Both halves read a manifest a human wrote and git
    tracks - R2's evidence standard applied to a second question: the Python
    half from `pyproject.toml`'s ``[tool.setuptools.packages.find]`` ``include``
    globs, the Node half from a top-level directory carrying a `package.json`.
    `tests/` answers to NEITHER, which is the point: it carries an
    ``__init__.py`` and would pass any "is it a package" test, so the question
    asked is whether this repository SHIPS it.

    THE FAILURE DIRECTION IS LOUD: a manifest that stops declaring yields an
    empty set and fourteen live sites become findings. A contract asserts the
    set non-empty besides.

    Args:
        tracked: Repo-relative POSIX paths.
        manifest: The text of `pyproject.toml`. Injected rather than read here
            so a control can pose the question against a manifest it wrote,
            which is the only way to prove the Python half consults it.

    Note:
        The glob is matched CASE-SENSITIVELY on every platform. Plain
        ``fnmatch`` normalises case on Windows and not on Linux, so the same
        manifest would derive a different root set on the developer machine
        than in CI - a determinism bug in a project whose first stated property
        is that a result is reproducible from the same inputs.

    Returns:
        Top-level directory names, without a trailing separator.
    """
    globs: Sequence[str] = ()
    node: object = tomllib.loads(manifest)
    for key in _SETUPTOOLS_FIND:
        if not isinstance(node, Mapping) or key not in node:
            node = None
            break
        node = node[key]
    if isinstance(node, list) and all(isinstance(entry, str) for entry in node):
        globs = tuple(node)
    paths = list(tracked)
    roots = {path.split("/", 1)[0] for path in paths if "/" in path}
    packaged = {root for root in roots if any(fnmatchcase(root, glob) for glob in globs)}
    packaged |= {
        path.split("/", 1)[0]
        for path in paths
        if path.count("/") == 1 and path.endswith("/" + _NODE_MANIFEST)
    }
    return frozenset(packaged)


def bare_path_ladder(
    sites: Iterable[BarePathSite],
    tracked: Iterable[str],
    declared_untracked: Iterable[str],
    reasons: Mapping[tuple[str, str, str], BarePathReason],
    roots_of_source: Iterable[str],
) -> dict[str, list[BarePathSite]]:
    """Run every site down the ladder and report WHICH rung answered it.

    A PURE FUNCTION OF ITS ARGUMENTS. Every input a rung consults is injected,
    so a control can pose any rung's question against a corpus with no
    filesystem and no subprocess behind it - which is the only way to prove a
    rung fires rather than merely that the live corpus is clean.

    Args:
        sites: The spellings to judge.
        tracked: Every path in the index.
        declared_untracked: The subset `.gitignore` declares will never be
            tracked, from :func:`declares_untracked`.
        reasons: The recorded answers, keyed by
            :attr:`BarePathSite.identity`.
        roots_of_source: R1's candidate set, from :func:`source_roots`. A
            suffix hit OUTSIDE these roots does not resolve, for the reason
            that function states. REQUIRED rather than defaulted to every
            root, because a default that restores the laundering route is the
            same fault one call site along.

    Returns:
        Rung name to the sites it answered, every rung in
        :data:`LADDER_RUNGS` present even when empty - an absent key and an
        empty one read the same to a caller counting a distribution, and only
        one of them is a rung that stopped firing.
    """
    exact = set(tracked)
    roots = {path.split("/", 1)[0] for path in exact}
    packaged = set(roots_of_source)
    suffixes = tracked_suffixes(
        path for path in exact if path.split("/", 1)[0] in packaged and "/" in path
    )
    ignored = set(declared_untracked)
    answered: dict[str, list[BarePathSite]] = {rung: [] for rung in LADDER_RUNGS}
    for site in sites:
        hits = suffixes.get(site.cited, ())
        if site.declared_absent:
            bound = site.cited in exact or bool(hits)
            answered[DECLARED_ABSENT_BOUND if bound else DECLARED_ABSENT].append(site)
            continue
        if site.cited in exact:
            answered[RESOLVED_EXACT].append(site)
            continue
        if len(hits) == 1:
            answered[RESOLVED_SUFFIX].append(site)
            continue
        if len(hits) > 1:
            answered[AMBIGUOUS_SUFFIX].append(site)
            continue
        if site.cited in ignored:
            answered[DECLARED_UNTRACKED].append(site)
            continue
        if site.cited.split("/", 1)[0] not in roots:
            answered[UNTRACKED_ROOT].append(site)
            continue
        if site.in_fixture_literal:
            answered[FIXTURE_LITERAL].append(site)
            continue
        if site.identity in reasons:
            answered[RECORDED_REASON].append(site)
            continue
        answered[UNRESOLVED].append(site)
    return answered


def stale_declaration_problems(carriers: Mapping[str, str]) -> list[str]:
    """Every absence declaration whose own line no longer spells what it names.

    THE DIRECTION THAT KEEPS A DECLARATION FROM BECOMING A LANDMINE. CS-891's
    merger demanded an answer to whether a forgiveness recorded against a
    carrier that is REWRITTEN EVERY SESSION is a working ratchet or a mine that
    reddens a later push for no defect. The round's own archive commit removed
    the only churning subject, so the question went moot without being
    answered.

    It is answered here by construction rather than by argument: a declaration
    buys silence for the citation ON ITS OWN LINE, so prose that is rewritten
    takes its declaration with it, and a declaration left behind is REPORTED
    instead of waiting for a path to die under it.

    THE DECLARED PATH MUST BE SPELLED AS A CITATION, not merely mentioned. The
    match is against :data:`BARE_PATH_RE`'s captures on that line, so a
    declaration naming a path the line spells without backticks is stale - the
    arm forgives exactly the shape it judges and nothing wider.

    R4 APPLIES HERE TOO, AND IT IS THE SAME RULE RATHER THAN A SECOND ONE. A
    declaration inside a Python string literal that is NOT a docstring is a
    CONTROL'S FIXTURE - the text an arm feeds this very function to prove it
    fires - and reading it as a live declaration would make every control that
    plants one a finding against the module that plants it. MEASURED: the three
    controls CS-899 shipped were reported by this arm on its first run, each
    spelling the declaration inside an f-string template whose placeholder is
    not a path at all. The partition is decided by the parse tree, exactly as
    the ladder's own R4 is.

    Args:
        carriers: Carrier path to the text its citations are read from, the
            same population :func:`bare_path_sites` is given.

    Returns:
        One line per stale declaration, carrier and line number included.
    """
    problems: list[str] = []
    for carrier in sorted(carriers):
        text = carriers[carrier]
        spans: tuple[tuple[int, int, int, int], ...] = ()
        if carrier.endswith(".py"):
            try:
                spans = fixture_literal_spans(ast.parse(text))
            except SyntaxError:
                spans = ()
        for number, raw in enumerate(text.split(chr(10)), start=1):
            spelled = set(BARE_PATH_RE.findall(raw))
            for path in live_declarations(raw, number, spans):
                if path in spelled:
                    continue
                problems.append(
                    f"{carrier}:{number} declares `{path}` absent and its line no longer"
                    " spells it as a citation, so the declaration is forgiving nothing."
                    " Move it with the prose or delete it."
                )
    return problems


def multiplicity(sites: Iterable[BarePathSite]) -> dict[tuple[str, str, str], int]:
    """How many spellings each identity covers."""
    counts: dict[tuple[str, str, str], int] = {}
    for site in sites:
        counts[site.identity] = counts.get(site.identity, 0) + 1
    return counts


def bare_path_problems(answered: Mapping[str, Sequence[BarePathSite]]) -> list[str]:
    """Every bare path this ladder could not answer.

    AMBIGUITY IS A FINDING, not a resolution. A suffix matching two tracked
    files tells the reader which file the author meant only by guessing, and a
    guard that guesses has stopped being evidence.
    """
    problems = [
        f"{site.carrier}:{site.line} -> {site.cited} - more than one tracked path ends"
        " with it, so the citation names no one file. Qualify it."
        for site in answered.get(AMBIGUOUS_SUFFIX, ())
    ]
    problems += [
        f"{site.carrier}:{site.line} -> {site.cited} - no tracked path is it or ends"
        " with it, the repo does not declare it untracked, its root is one this repo"
        " owns, and it is not a fixture literal. Repoint it, or record it in"
        " BARE_PATH_REASONS with the reason and raise the ceiling in the same change."
        for site in answered.get(UNRESOLVED, ())
    ]
    problems += [
        f"{site.carrier}:{site.line} -> {site.cited} - the line DECLARES this path"
        " absent and the tree now binds it, so the sentence around it is false."
        " Drop the declaration and let the citation resolve, or repoint it."
        for site in answered.get(DECLARED_ABSENT_BOUND, ())
    ]
    return problems


def pinned_rung_problems(
    answered: Mapping[str, Sequence[BarePathSite]],
    rung: str,
    pinned: Mapping[tuple[str, str, str], int],
) -> list[str]:
    """One decline rung's live membership against its pinned disclosure.

    BOTH DIRECTIONS, for :data:`tests.test_citation_tables.UNVERIFIED_LINE_POINTERS`' reason. A site
    the rung now declines that nothing discloses is a new invisibility; a disclosed site the rung no
    longer declines is a record that has outlived what it described. Appending an entry nobody
    argued for fails the second direction immediately, which is what makes this a disclosure rather
    than a permission list - there is nothing to gain by adding to it.

    Args:
        answered: The ladder's output.
        rung: Which rung to check.
        pinned: The recorded identities and how many spellings each covers.

    Returns:
        One line per disagreement.
    """
    derived = multiplicity(answered.get(rung, ()))
    problems = [
        f"{rung}: {identity} is declined {count} time(s) and is not disclosed"
        for identity, count in sorted(derived.items())
        if identity not in pinned
    ]
    problems += [
        f"{rung}: {identity} is disclosed and the rung no longer declines it"
        for identity in sorted(pinned)
        if identity not in derived
    ]
    problems += [
        f"{rung}: {identity} discloses {pinned[identity]} spelling(s), the corpus has"
        f" {derived[identity]}"
        for identity in sorted(set(pinned) & set(derived))
        if pinned[identity] != derived[identity]
    ]
    return problems


def bare_path_reason_problems(
    answered: Mapping[str, Sequence[BarePathSite]],
    reasons: Mapping[tuple[str, str, str], BarePathReason],
) -> list[str]:
    """Every recorded reason that no longer matches the corpus.

    THREE DIRECTIONS, and the third is the one CS-893 says a table normally
    lacks. An entry whose identity has vanished is stale. An entry covering
    more spellings than it records is a NEW dead citation arriving under an old
    forgiveness. An entry covering fewer is a record that outgrew its subject.
    A COMPENSATING SWAP - one identity deleted, another added, the cardinality
    unchanged - fails the first two at once, which a count alone would not see.
    """
    forgiven = multiplicity(answered.get(RECORDED_REASON, ()))
    problems = [
        f"{identity} - recorded, and the corpus no longer spells it"
        for identity in sorted(reasons)
        if identity not in forgiven
    ]
    problems += [
        f"{identity} - forgives {reasons[identity].sites} spelling(s), the corpus has"
        f" {forgiven[identity]}"
        for identity in sorted(set(reasons) & set(forgiven))
        if reasons[identity].sites != forgiven[identity]
    ]
    return problems


def graded_floor_names(source: str) -> frozenset[str]:
    """Every named constant this module actually USES as a non-vacuity floor.

    DERIVED, because the arm grading them began as a hand-written list of three
    - this round's own filed fault inside its own repair, since a FOURTH floor
    would have joined the ungraded set in silence. The derivation is the USE
    SITE rather than a naming convention: collecting names ending in ``_FLOOR``
    is the open-ended suffix rule this module has shipped twice, and
    ``MINIMUM_SITES`` would arrive exempt.

    WHAT IT CANNOT SEE, disclosed: a floor compared inline with ``>=``. That was
    the shape of all three before this round, and the reply is that an inline
    comparison cannot be posed a question at all.

    Args:
        source: This module's own text.

    Returns:
        The CONSTANT names passed as a floor - a lower-case name is a local and
        a literal is what a control passes; neither is a recorded floor.
    """
    named: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        # Sliced rather than length-checked: the floor is the third argument, and
        # an empty slice is a call that does not pass one.
        third = node.args[2:3]
        if node.func.id != "floor_problems" or not third:
            continue
        floor = third[0]
        if isinstance(floor, ast.Name) and floor.id.isupper():
            named.add(floor.id)
    return frozenset(named)


def floor_problems(what: str, measured: int, floor: int) -> list[str]:
    """One non-vacuity floor, checked - and the CHECK is the point.

    A floor exists so ``assert not problems`` cannot read as an answer when nothing was measured.
    EVERY ONE OF THEM WAS ITSELF GRADED BY NOTHING. VERIFIED: setting
    :data:`tests.test_docs_citations.BARE_PATH_POPULATION_FLOOR`,
    :data:`tests.test_docs_citations._ARCHITECTURE_RESOLVED_FLOOR` or
    :data:`tests.test_docs_citations._SELF_SPELLED_FLOOR` to ZERO left the whole module green, which
    restores exactly the defect each exists to prevent in a one-character diff. A floor compared
    inline cannot be posed a question; hoisted into a function, a control can ask whether the LIVE
    number rejects an empty measurement - which a floor of zero cannot pass.

    Args:
        what: The population, for the message.
        measured: How many were collected this run.
        floor: The recorded minimum.

    Returns:
        One line if the population came in under the floor, else none.
    """
    if measured >= floor:
        return []
    return [
        f"only {measured} {what} were collected, below the recorded floor of {floor}."
        " The shape or the population has stopped reading the tree, and an empty"
        " finding list would then be silence rather than an answer."
    ]


def decline_budget_problems(
    rung: str,
    pinned: Mapping[tuple[str, str, str], int],
    ceiling: int,
) -> list[str]:
    """THE DECLINE DISCLOSURES' RATCHET, and it exists because the asymmetry was real.

    THE FIRST BUILD SAID THESE NEEDED NO BUDGET - "there is nothing to be bought
    by adding to it". THAT SENTENCE WAS FALSE AS WRITTEN. A row appended ALONE
    does redden, because it discloses a decline the ladder does not derive; a
    row appended TOGETHER WITH the dead citation it describes leaves derived and
    pinned in agreement and the suite green. One dead citation, one row, no
    argument, no ceiling.

    THE ASYMMETRY IS THE FINDING RATHER THAN THE HOLE. A dead citation spelled in full costs a
    :data:`tests.test_citation_tables.BARE_PATH_REASONS` entry PLUS a ceiling raise. THE SAME
    CITATION ONE SEGMENT SHORTER lands on a decline rung and cost one unbudgeted row - so THE
    CHEAPER SPELLING WAS THE LESS GUARDED ONE, and the module map already spells six paths the short
    way. A guard whose price falls as the citation gets vaguer is pointed backwards.

    A CEILING PER RUNG, NEVER A POOLED ONE, for the doctrine
    :func:`bare_path_budget_problems` cites: a threshold summed over a
    population is met by its strongest member while the weakest goes unmeasured.

    Args:
        rung: Which rung the disclosure covers, for the message.
        pinned: The disclosed identities.
        ceiling: The recorded budget.

    Returns:
        One line per direction that has drifted, in
        :func:`bare_path_budget_problems`' shape and for its reasons.
    """
    spent = len(pinned)
    if spent > ceiling:
        return [
            f"{rung}: {spent} sites disclosed against a ceiling of {ceiling}."
            " A decline was added. That is a finding to argue, not a line to type:"
            " repoint the citation, or raise the ceiling in this same change and say"
            " why. A row added together with the dead citation it describes is green"
            " against the disclosure alone - this is the leg that is not."
        ]
    if spent < ceiling:
        return [
            f"{rung}: {spent} sites disclosed against a ceiling of {ceiling}."
            f" A citation was repointed and the ceiling was not lowered to match."
            f" Lower it to {spent} - a slack ceiling is banked room for an append"
            " nobody will have to defend."
        ]
    return []


def bare_path_budget_problems(
    reasons: Mapping[tuple[str, str, str], BarePathReason],
    ceiling: int,
) -> list[str]:
    """THE BARE-PATH RATCHET, and it is SEPARATE from the line-pointer one.

    A SEPARATE CEILING RATHER THAN A POOLED ONE, and the reason is measured
    doctrine rather than tidiness: a threshold summed over a population is met
    by its strongest member while the weakest goes unmeasured. Pooling the two
    would let a line-pointer repair bank room for a bare-path append, and each
    table's own repair progress would stop being visible.

    AND IT COULD NOT HAVE BEEN POOLED ANYWAY, which is worth recording because it was the first
    thing tried. :func:`tests.test_docs_citations.forgiveness_budget_problems` counts a disposition
    only when its key matches :data:`tests.test_docs_citations.LINE_POINTER_RE`, so a bare-path key
    spends NOTHING - it would have been silenceable the day it shipped, which is precisely the
    CS-889 round-one defect reproduced inside the module repaired for it.
    :func:`tests.test_docs_citations.citation_sites` fails the same way one step over: it dispatches
    on key SPELLING and falls through to an arm demanding a `test_` prefix, so a bare-path key in
    :data:`tests.test_citation_tables.DISPOSITIONS` would count zero sites and report itself stale
    on
    arrival.

    Args:
        reasons: The recorded answers.
        ceiling: The recorded budget.

    Returns:
        One line per direction that has drifted, in
        :func:`tests.test_docs_citations.forgiveness_budget_problems`' shape and for its reasons.
    """
    spent = len(reasons)
    if spent > ceiling:
        return [
            f"{spent} bare-path reasons recorded against a ceiling of {ceiling}."
            " Something was added to BARE_PATH_REASONS. That is a finding to argue,"
            " not a line to type: repoint the citation, or raise the ceiling in this"
            " same change and say why in the record."
        ]
    if spent < ceiling:
        return [
            f"{spent} bare-path reasons recorded against a ceiling of {ceiling}."
            f" A citation was repointed and the ceiling was not lowered to match."
            f" Lower it to {spent} - a slack ceiling is banked room for an append"
            " nobody will have to defend."
        ]
    return []


def non_citation_budget_problems(
    patterns: Sequence[re.Pattern[str]],
    ceiling: int,
) -> list[str]:
    """THE NON-CITATION DECLARATION'S RATCHET, and it is the one this family lacked.

    WHAT THE TWO-WAY PIN ALREADY BOUGHT, so the number is not sold as more than
    it is. :data:`tests.test_docs_citations.NON_CITATION_PATTERNS` is checked in
    BOTH directions against the patterns the family compiles: a row naming a
    pattern no module compiles reddens, and a compiled pattern in neither table
    reddens. That catches a row added ALONE.

    WHAT IT DID NOT BUY, WHICH IS THE PURCHASE THIS BOUNDS. A row added TOGETHER
    WITH the pattern it describes leaves both directions satisfied and the suite
    green - the same pair :func:`decline_budget_problems` exists for, one family
    over. So a future pattern that IS a citation shape could be declared not one
    in a single row carrying no number to query.

    A NUMBER SOMEBODY TYPED, NOT A DERIVED ONE. The ceiling is a literal the
    diff carries; :func:`derived_bound_problems` refuses the ``len(TABLE)``
    spelling that would make both directions true by construction.

    Args:
        patterns: The patterns declared not to be citation shapes.
        ceiling: The recorded budget.

    Returns:
        One line per direction that has drifted, in
        :func:`bare_path_budget_problems`' shape and for its reasons.
    """
    spent = len(patterns)
    if spent > ceiling:
        return [
            f"{spent} non-citation pattern declarations recorded against a ceiling of"
            f" {ceiling}. A pattern was declared not to be a citation shape. That is a"
            " finding to argue, not a line to type: judge it as a citation shape, or"
            " raise the ceiling in this same change and say why in the record."
        ]
    if spent < ceiling:
        return [
            f"{spent} non-citation pattern declarations recorded against a ceiling of"
            f" {ceiling}. A declaration was withdrawn and the ceiling was not lowered"
            f" to match. Lower it to {spent} - a slack ceiling is banked room for an"
            " append nobody will have to defend."
        ]
    return []


def _table_spellings(node: ast.AST) -> tuple[str, ...]:
    """Every way one expression node can NAME a registered forgiveness table.

    TWO SPELLINGS, AND THE SECOND ONLY BECAME WRITABLE WHEN THE FAMILY SPLIT.
    While a table and the ceiling that bounds it lived in one file, the
    tautology could only be ``len(TABLE)`` - an :class:`ast.Name`. A table
    relocated into a sibling module is spelled ``len(tables.TABLE)``, an
    :class:`ast.Attribute`, and a filter on ``Name`` alone reports a confident
    zero about it. That is the relocation evasion this family has already
    closed twice one level up, arriving inside the bound check itself.

    THE ATTRIBUTE'S OWNER IS NOT READ, DELIBERATELY. What is being detected is a
    bound whose value expression MENTIONS what it bounds, and the registered
    name is the attribute half however the module alias is spelled - requiring a
    particular alias would be the naming rule the container walk already refuted.

    Args:
        node: One node from the walk of a module-scope assignment's value.

    Returns:
        The names this node spells, empty for a node that spells none.
    """
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return (node.attr,)
    return ()


def derived_bound_problems(source: str, tables: Iterable[str]) -> list[str]:
    """Every module-scope constant COMPUTED FROM a table it is supposed to bound.

    THE TAUTOLOGY THAT DISARMS EVERY BUDGET IN THIS MODULE, AND IT IS ONE LINE.
    ``BARE_PATH_REASON_CEILING: Final = len(BARE_PATH_REASONS)`` makes
    ``spent == ceiling`` true by construction: both directions permanently
    satisfied, every future append free, and NO NUMBER IN THE DIFF to query.
    VERIFIED: ``bare_path_budget_problems(table, len(table))`` is empty for
    every table. Worse than the escape CS-889 was reopened on, which at least
    left a growing list somebody could see.

    NEITHER EXISTING CONTROL CATCHES IT: both budget arms pass SYNTHETIC
    arguments, so they prove the arithmetic and say nothing about where the live
    constant came from - and by import time it is just an int, so provenance has
    to be read out of the SOURCE.

    BOTH SPELLINGS OF A TABLE ARE READ - see :func:`_table_spellings`, which is
    what keeps a file split from making the disarm writable again one dot wider.

    THE POPULATION IS EVERY MODULE-SCOPE ASSIGNMENT, not a naming convention: a
    rule walking names ending in ``_CEILING`` is the open-ended filter this
    module has shipped twice, and ``BUDGET_MAX`` would arrive exempt. The
    predicate names the OFFENCE - a constant whose value expression mentions a
    registered forgiveness table is derived from what it bounds.

    TWO RESIDUALS, STATED. A wrong integer typed by hand still silences what it
    bounds; what is removed is the bound that CANNOT be wrong. And this reads
    ONE HOP - ``= _count_them()``, with the helper reading the table, mentions
    no registered name and passes. Closing that means resolving call graphs. The
    one-line version is what costs nothing to write and therefore what arrives.

    THE POPULATION IS THE CALLER'S, AND BOTH HALVES OF A REGISTRY PAIR ARE
    LEGITIMATE. The offence named here is a bound whose value expression mentions
    WHAT IT BOUNDS, which is indifferent to whether the subject forgives
    anything - a table recorded in :data:`NOT_A_FORGIVENESS` is still bounded by a
    ceiling, and ``tests/test_bare_path_citations.py`` passes both halves for
    exactly that reason. Widening the population at the call site is how that
    ceiling is reached; moving the table across the pair would buy the same reach
    by asserting something false about what it forgives.

    Args:
        source: This module's own text.
        tables: The names to look for. Every caller reading one half of a
            registry pair passes :data:`FORGIVENESS_TABLES`; a caller whose
            bounded table forgives nothing passes both halves.

    Returns:
        One line per module-scope assignment that reads one of them.
    """
    bounded = set(tables)
    problems: list[str] = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.AnnAssign):
            targets: list[ast.expr] = [node.target]
        elif isinstance(node, ast.Assign):
            targets = list(node.targets)
        else:
            continue
        if node.value is None:
            continue
        read = sorted(
            {
                spelled
                for node_read in ast.walk(node.value)
                for spelled in _table_spellings(node_read)
                if spelled in bounded
            }
        )
        if not read:
            continue
        problems.extend(
            f"{target.id} is computed from {', '.join(read)}, which it is meant to"
            " bound. A bound derived from its own subject is satisfied by"
            " construction and spends nothing. Type the number."
            for target in targets
            if isinstance(target, ast.Name)
        )
    return sorted(problems)


#: The names the INTERPRETER installs in a module's globals that are also
#: containers, excluded from the walk BY EXACT MATCH. Three of them, measured,
#: and the exactness is the whole point - see :func:`module_containers`.
_INTERPRETER_NAMES: Final = frozenset(
    {"__annotations__", "__builtins__", "__conditional_annotations__"}
)


def module_containers(namespace: Mapping[str, object]) -> dict[str, object]:
    """Every container a module holds at module scope, by name.

    DERIVED FROM THE NAMESPACE rather than listed, for the reason the judged-shape
    membership contract in ``tests/test_docs_citations.py`` is derived: a
    hand-written list of tables is exactly what lets the SIXTH one arrive
    unbounded.

    THE FIRST BUILD FILTERED ON ``name.isupper()`` AND ITS OWN QUESTION
    REFUTED IT. A walk whose job is to catch a table nobody registered cannot
    also require that table to be named in a particular case - a forgiveness
    spelled ``forgiven_paths`` would have escaped the contract written to make
    escaping impossible.

    THE REPAIR FOR THAT REPRODUCED IT ONE SHAPE ALONG, WHICH IS WHY THE
    EXCLUSION IS AN EXACT MATCH. It closed the lowercase spelling and excluded
    the interpreter's names with ``name.startswith("__")``, calling that in this
    docstring "a rule about a known, closed set". It was an OPEN-ENDED PREFIX
    RULE, and a table spelled with two leading underscores walked straight past
    the contract written to make walking past impossible - VERIFIED by
    execution. Naming the three outright is what the docstring already claimed.

    WHAT THIS WALK CLOSES, AND WHAT IT DOES NOT, stated because the contract
    reading it made a broader-sounding claim than the walk supports. It closes
    MODULE-SCOPE CONTAINERS. It does NOT close every way a walked module could
    forgive something: a ``str`` silencer - a prefix constant compared against a
    path, exactly what the out-of-domain and dated-archive prefixes in
    ``tests/test_docs_citations.py`` are - is invisible here, DELIBERATELY,
    since every ``str`` is iterable and admitting
    them floods the registries with dozens of names nobody would read. An
    ``int`` is invisible for the same reason. The reply is that a ceiling is
    checked by :func:`derived_bound_problems` and a prefix silencer widens
    nothing alone. What must not happen is the CLAIM outrunning the walk.

    Args:
        namespace: The mapping to walk, normally a module's ``vars()``. Injected
            so a control can pose the question against a namespace it built,
            which is the only way to prove the walk SEES a table the caller
            happens not to hold. REQUIRED, AND IT USED TO DEFAULT TO
            ``globals()`` - correct in the one module this function was written
            in and silently wrong from every other, which is exactly the
            relocation fault the split of that module had to close. A walk that
            reads the wrong namespace and answers confidently is worse than one
            that will not answer at all.

    Returns:
        Name to container, for every module-scope container the interpreter
        did not install.
    """
    return {
        name: value
        for name, value in namespace.items()
        if name not in _INTERPRETER_NAMES and isinstance(value, (Mapping, AbstractSet, tuple, list))
    }


def module_patterns(namespace: Mapping[str, object]) -> dict[str, re.Pattern[str]]:
    """Every compiled pattern a module holds at module scope, by name.

    THE COMPANION TO :func:`module_containers`, one shape over, and hoisted out
    of the arm that used to spell it inline for one reason: the walk now has to
    be run over a namespace that is not the caller's own. Two comprehensions
    asking the same question in two modules is two things to drift, and this
    family's founding finding is a boundary that learned a shape while an arm
    did not.

    THE RESIDUAL IS THE SUFFIX, DISCLOSED RATHER THAN WIDENED. A pattern not
    named ``*_RE`` is invisible here, which is the naming convention this
    project's own doctrine calls the wrong kind of boundary. It is kept because
    the alternative - every module-scope ``re.Pattern`` - was never what the
    boundary contract was written against, and widening it inside a slice whose
    job is a file split would be doing two jobs. THE SPLIT NEITHER WIDENS NOR
    NARROWS IT: the same names answer the same way, in one module or in four.
    CS-811 CLOSED THE RESIDUAL BESIDE THIS WALK RATHER THAN INSIDE IT:
    :func:`held_patterns` sees every held pattern, and this stays the narrow
    walk the NON_CITATION_PATTERNS staleness check needs - a wider one would
    count that table's own members as live and never call a row stale.

    Args:
        namespace: The mapping to walk, normally a module's ``vars()``. Required
            rather than defaulted, for the reason :func:`module_containers`
            states about its own.

    Returns:
        Name to compiled pattern, for every module-scope pattern so named.
    """
    return {
        name: value
        for name, value in namespace.items()
        if name.endswith("_RE") and isinstance(value, re.Pattern)
    }


def held_patterns(namespace: Mapping[str, object]) -> dict[str, re.Pattern[str]]:
    """Every compiled pattern a namespace HOLDS, under any name and at any depth.

    CS-811 - THE WALK :func:`module_patterns` IS NOT. That one reads a single
    shape, a module-scope pattern named ``*_RE``, and a pattern named anything
    else or held inside a module-scope dict or list escaped it; all three were
    measured green. This reads every module-scope value, and descends into every
    mapping (keys and values), tuple, list and set it finds, so the three
    namespace-held shapes are one answer. A pattern compiled at call time is
    never bound here at all - :func:`regex_call_sites` is its census.

    Args:
        namespace: The mapping to walk, normally a module's ``vars()``.
            Required, for the reason :func:`module_containers` states.

    Returns:
        An access path such as ``NAME``, ``NAME[0]`` or ``NAME['key']`` to the
        pattern held there. A pattern held twice appears twice.
    """
    found: dict[str, re.Pattern[str]] = {}
    pending: list[tuple[str, object]] = [
        (name, value) for name, value in namespace.items() if name not in _INTERPRETER_NAMES
    ]
    entered: set[int] = set()
    while pending:
        where, value = pending.pop()
        if isinstance(value, re.Pattern):
            found[where] = value
            continue
        if not isinstance(value, (Mapping, AbstractSet, tuple, list)) or id(value) in entered:
            continue
        entered.add(id(value))
        if isinstance(value, Mapping):
            for key, member in value.items():
                pending += [(f"{where}[{key!r}]", member), (f"{where}<key {key!r}>", key)]
        else:
            pending += [(f"{where}[{index}]", member) for index, member in enumerate(value)]
    return found


def regex_call_sites(source: str) -> dict[str, int]:
    """How many regex calls a module's source makes, keyed by enclosing scope.

    CS-811 - THE SHAPE NO NAMESPACE WALK CAN SEE. A pattern compiled or matched
    at call time is never bound at module scope, so :func:`held_patterns` is
    blind to it by construction. Counting the call sites in the SOURCE is what
    reaches it, and every spelling is read: ``re.<name>``, the module imported
    under another name, and a function imported out of it with or without an
    alias.

    Args:
        source: A module's text.

    Returns:
        ``<module>`` for the top level, or the dotted class and function path,
        to the number of regex calls made there. A scope making none is absent.
    """
    functions = {"compile", "search", "match", "fullmatch", "findall", "finditer"}
    functions |= {"sub", "subn", "split"}
    tree = ast.parse(source)
    modules = {"re"}
    direct: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {alias.asname or alias.name for alias in node.names if alias.name == "re"}
        elif isinstance(node, ast.ImportFrom) and node.module == "re":
            named = [alias for alias in node.names if alias.name in functions]
            direct |= {alias.asname or alias.name for alias in named}

    def is_regex_call(node: ast.AST) -> int:
        return int(
            isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id in direct)
                or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in functions
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in modules
                )
            )
        )

    return _count_by_scope(tree, is_regex_call)


def _count_by_scope(tree: ast.AST, weigh: Callable[[ast.AST], int]) -> dict[str, int]:
    """Sum ``weigh`` over every node, keyed by the enclosing class and function path.

    Args:
        tree: A parsed module.
        weigh: How many sites one node is.

    Returns:
        ``<module>`` or the dotted scope path to its total; a zero scope is absent.
    """
    counts: dict[str, int] = {}
    pending: list[tuple[ast.AST, str]] = [(tree, "<module>")]
    while pending:
        node, scope = pending.pop()
        for child in ast.iter_child_nodes(node):
            inner = scope
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                inner = child.name if scope == "<module>" else f"{scope}.{child.name}"
            if weight := weigh(child):
                counts[scope] = counts.get(scope, 0) + weight
            pending.append((child, inner))
    return counts


def substring_sites(source: str) -> dict[str, int]:
    """How many substring judgements a module's source makes, keyed by enclosing scope.

    CS-811's FIFTH SHAPE, an arm judging by substring rather than by a pattern.
    Two spellings are counted: an ``in`` or ``not in`` whose NEEDLE is a string
    or f-string literal, and a call to a str method that probes for a substring
    (``startswith``, ``endswith``, ``find``, ``rfind``, ``index``, ``rindex``,
    ``count``, ``partition``, ``rpartition``, ``split``, ``rsplit``,
    ``replace``, ``removeprefix``, ``removesuffix``).

    DECLINED FOR COST, NOT IMPOSSIBLE, AND DISCLOSED: a needle held in a
    variable (``needle in text``), ``operator.contains``, and slice equality
    (``text[:3] == "abc"``) are not counted. The syntax tree carries no operand
    types, so counting them means counting every membership and comparison
    test the family makes, and that pin would move on every unrelated edit.

    Args:
        source: A module's text.

    Returns:
        Scope path to site count, as :func:`regex_call_sites` keys it.
    """
    methods = {"startswith", "endswith", "find", "rfind", "index", "rindex", "count"}
    methods |= {"partition", "rpartition", "split", "rsplit", "replace"}
    methods |= {"removeprefix", "removesuffix"}

    def is_text(node: ast.expr) -> bool:
        literal = isinstance(node, ast.Constant) and isinstance(node.value, str)
        return literal or isinstance(node, ast.JoinedStr)

    def weigh(node: ast.AST) -> int:
        if isinstance(node, ast.Compare):
            needles = [node.left, *node.comparators[:-1]]
            tests = zip(node.ops, needles, strict=True)
            return sum(isinstance(op, (ast.In, ast.NotIn)) and is_text(left) for op, left in tests)
        return int(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in methods
        )

    return _count_by_scope(ast.parse(source), weigh)


#: CS-811 - EVERY REGEX CALL SITE IN THE FAMILY'S SOURCE, by module and scope.
#: AN EQUALITY PIN, so a pattern compiled or matched at call time - which no
#: namespace walk can see, because it is never bound - is a number in the diff
#: before it can judge anything. Module-scope sites are counted too: a top-level
#: ``re.search`` whose Match is dropped binds nothing. A module with no site has
#: no row. HELD HERE rather than beside the family-wide arm so the module that
#: judges can run the same census over itself without importing its own grader.
REGEX_CALL_SITES: Final[Mapping[str, Mapping[str, int]]] = {
    "tests.bare_path_guard": {
        "<module>": 2,
    },
    "tests.test_bare_path_citations": {
        "test_a_pattern_declared_one_module_over_is_reported_rather_than_unseen": 1,
    },
    "tests.test_docs_citations": {
        "<module>": 8,
        "test_appending_a_non_citation_pattern_spends_its_budget": 2,
    },
}

#: CS-811 - EVERY SUBSTRING SITE IN THE FAMILY'S SOURCE, as :func:`substring_sites`
#: counts them. The same equality pin, for the same reason, one shape over.
SUBSTRING_SITES: Final[Mapping[str, Mapping[str, int]]] = {
    "tests.bare_path_guard": {
        "bare_path_ladder": 4,
        "bare_path_sites": 3,
        "declares_untracked": 1,
        "markdown_anchor": 2,
        "module_file": 1,
        "module_patterns": 1,
        "registry_problems": 1,
        "sibling_imports": 1,
        "source_roots": 5,
        "stale_declaration_problems": 2,
        "tracked_suffixes": 1,
    },
    "tests.test_archive_rot": {
        "test_the_archive_rot_pin_is_typed_rather_than_computed_from_what_it_measures": 4,
        "test_the_deep_archive_exemption_rests_on_the_claim_its_own_header_makes": 1,
    },
    "tests.test_bare_path_citations": {
        "test_a_table_relocated_into_another_module_without_a_record_is_reported": 4,
        "test_the_import_walk_reads_both_spellings_of_a_module_import_and_no_function": 1,
        "test_the_separate_guard_ceiling_is_not_derived_from_the_table_it_bounds": 2,
    },
    "tests.test_citation_tables": {
        "file_lines": 1,
        "in_domain": 2,
        "line_pointer_carriers": 1,
        "module_basenames": 2,
        "scoped_text": 1,
        "sources": 1,
        "tracked_files": 1,
    },
    "tests.test_docs_citations": {
        "bare_name_problems": 1,
        "citation_site_anchors": 1,
        "citation_site_identities": 2,
        "citation_site_offsets": 2,
        "heading_chain": 2,
        "line_pointer_content_problems": 1,
        "line_pointer_problems": 1,
        "line_pointer_sites": 2,
        "test_a_bare_path_ceiling_left_slack_after_a_repair_is_reported": 1,
        "test_a_ceiling_left_slack_after_a_repair_is_reported": 1,
        "test_a_disposition_for_a_citation_that_has_vanished_is_reported": 1,
        "test_a_disposition_whose_target_stopped_resolving_is_reported": 1,
        "test_a_module_qualified_pointer_is_not_read_as_an_elided_one": 1,
        "test_a_pinned_pointer_whose_line_has_moved_under_it_is_reported": 1,
        "test_a_record_for_a_doc_that_has_since_been_guarded_is_reported": 1,
        "test_a_record_for_a_doc_that_stopped_carrying_citations_is_reported": 1,
        "test_a_record_naming_a_doc_that_is_not_tracked_is_reported": 1,
        "test_a_recorded_redirect_whose_target_stopped_resolving_is_reported": 1,
        "test_a_second_site_for_a_forgiven_citation_is_reported": 2,
        "test_a_stale_pin_is_reported": 1,
        "test_an_ambiguous_suffix_is_reported_rather_than_resolved": 1,
        "test_an_elided_only_name_is_visible_to_the_stale_disposition_check": 2,
        "test_appending_a_bare_path_reason_is_itself_a_finding": 1,
        "test_appending_a_fabricated_disposition_is_itself_a_finding": 1,
        "test_appending_a_non_citation_pattern_spends_its_budget": 2,
        "test_appending_a_pin_is_itself_a_finding": 1,
        "test_appending_to_a_decline_disclosure_is_itself_a_finding": 3,
        "test_appending_to_a_decline_disclosure_spends_its_budget": 2,
        "test_each_named_leg_of_the_bare_path_shape_is_load_bearing": 2,
        "test_every_bounded_table_names_a_contract_that_exists_and_every_exemption_a_reason": 1,
        "test_every_correctable_disposition_names_a_target_and_the_others_do_not": 1,
        "test_every_recorded_disposition_is_still_in_use": 2,
        "test_no_recorded_bound_is_computed_from_the_table_it_bounds": 2,
        "test_the_bare_path_population_is_the_line_pointer_population": 2,
        "test_the_carrier_population_is_every_tracked_file_less_the_recorded_ones": 1,
        "test_the_domain_excludes_a_harness_file_that_would_otherwise_be_a_carrier": 2,
        "test_the_domain_excludes_the_dated_archive": 2,
        "test_the_ignore_probe_answers_a_declared_path_and_a_tracked_one": 1,
        "test_the_ignore_probe_raises_rather_than_reading_a_bad_exit_as_nothing_ignored": 1,
        "test_the_interpreter_exclusion_is_a_closed_set_and_not_a_prefix": 2,
        "test_the_non_citation_pattern_ceiling_is_visible_to_the_derived_bound_check": 2,
        "test_the_recorded_exemptions_are_the_only_files_the_line_arm_declines": 1,
        "test_the_source_roots_are_derived_from_the_manifests_this_repo_tracks": 3,
        "unresolved_citations": 1,
    },
}


def census_drift(
    pinned: Mapping[str, Mapping[str, int]], measured: Mapping[str, Mapping[str, int]]
) -> list[str]:
    """Every module whose measured census differs from its pin, in either direction.

    Args:
        pinned: Module to scope to count, as recorded.
        measured: The same, as counted now. A module absent from either side
            reads as having no site.

    Returns:
        One line per module that differs, naming each scope that moved.
    """
    lines: list[str] = []
    for dotted in sorted(set(pinned) | set(measured)):
        want, have = pinned.get(dotted, {}), measured.get(dotted, {})
        moved = sorted(
            f"{scope} {want.get(scope, 0)}->{have.get(scope, 0)}"
            for scope in set(want) | set(have)
            if want.get(scope, 0) != have.get(scope, 0)
        )
        if moved:
            lines.append(f"  {dotted}: " + ", ".join(moved))
    return lines


def census_problems(dotted: str, source: str) -> list[str]:
    """Both CS-811 source censuses for ONE module, against their pins.

    Args:
        dotted: The module's dotted name, the pins' key.
        source: Its text.

    Returns:
        Drift lines for the regex census, then the substring census.
    """
    regex = census_drift(
        {dotted: REGEX_CALL_SITES.get(dotted, {})}, {dotted: regex_call_sites(source)}
    )
    text = census_drift(
        {dotted: SUBSTRING_SITES.get(dotted, {})}, {dotted: substring_sites(source)}
    )
    return [f"{line} (regex calls)" for line in regex] + [f"{line} (substring)" for line in text]


#: The package every module in the walked population belongs to. A DOTTED PREFIX rather than a
#: directory literal, joined into a path only at call time by :func:`module_file`, for the reason
#: :func:`tests.test_docs_citations.bare_path` gives about its own assembly - a path spelled whole
#: in this file is a citation this family's arm then reads back.
TESTS_PACKAGE: Final = "tests"


def module_file(dotted: str) -> Path:
    """The source file behind a dotted module name, present or not.

    Args:
        dotted: A dotted module name, rooted anywhere.

    Returns:
        The path the name would be imported from. Existence is the CALLER's
        question, because "no such module" and "not a module of ours" are
        different answers and collapsing them here would hide the second.
    """
    return REPO_ROOT.joinpath(*dotted.split(".")).with_suffix(".py")


def sibling_imports(source: str) -> frozenset[str]:
    """Every module inside :data:`TESTS_PACKAGE` that ``source`` imports.

    READ OUT OF THE SOURCE RATHER THAN OFF THE MODULE OBJECT, and the difference
    decides whether the walk works at all. ``from tests.bare_path_guard import
    bare_path_ladder`` binds the FUNCTION and never the module, so a walk that
    looked for module objects in ``globals()`` would find nothing and report a
    closure of one - a clean-looking zero about the wrong population, which is
    this project's most-repeated failure shape. The import STATEMENT is present
    either way.

    BOTH SPELLINGS OF A MODULE IMPORT ARE READ. ``from tests import x`` and
    ``from tests.save import y`` both name a module in the ``names`` list rather
    than in ``module``, so the candidate set takes the dotted join as well as
    ``module`` itself, and keeps whichever is a file on disk. A name that is a
    FUNCTION rather than a module joins the candidates and is dropped by that
    same test.

    WHAT IT DOES NOT READ, disclosed: a relative import, and a module reached by
    ``importlib`` at run time rather than by a statement. Neither is spelled
    anywhere in this family, and both would be a deliberate act rather than the
    quiet relocation this walk exists to catch.

    Args:
        source: A module's own text.

    Returns:
        The dotted names of the tests-package modules it imports.
    """
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return frozenset(
        name
        for name in found
        if name.startswith(f"{TESTS_PACKAGE}.") and module_file(name).is_file()
    )


def namespace_closure(roots: Iterable[str]) -> dict[str, Mapping[str, object]]:
    """Each root module and every tests module it transitively imports.

    THE POPULATION THE CLASS-CLOSING WALKS RUN OVER, DERIVED. A hand-list of the
    modules to walk is the identical fault to a hand-list of the tables to bound:
    it is correct on the day it is written and silently short the day a third
    module arrives. The graph is followed transitively, so a table relocated two
    hops away is still walked.

    WHY REACHABILITY IS THE RIGHT BOUNDARY AND NOT MERELY A CONVENIENT ONE. A
    table can only forgive something if the code consulting it RUNS, and it only
    runs if something imported it. A module nothing imports is inert - it holds
    no live forgiveness, judges nothing, and appears in no arm's verdict. So the
    set of modules that could hide a live escape hatch is exactly the set
    reachable from the arms, which is what this returns.

    Args:
        roots: Dotted names of the modules the walks start from.

    Returns:
        Dotted name to that module's namespace, roots included.
    """
    found: dict[str, Mapping[str, object]] = {}
    pending = list(roots)
    while pending:
        dotted = pending.pop()
        if dotted in found:
            continue
        found[dotted] = vars(importlib.import_module(dotted))
        # DECODED PERMISSIVELY, AND THE REASON IS A MEASURED PLANT RATHER THAN
        # CAUTION. A strict ascii read RAISES on the first byte above the range,
        # and it raises HERE - inside the derivation every arm in
        # `tests/test_bare_path_citations.py` depends on - so one planted byte
        # took the whole module down with a UnicodeDecodeError naming a byte
        # OFFSET and no file. The arm whose entire subject is that byte then
        # never ran. A replacement character cannot invent or hide an import,
        # because an import statement is ascii by construction, so reachability
        # is unchanged; what changes is that the finding reaches the arm that
        # can NAME the file instead of killing every arm that cannot.
        text = module_file(dotted).read_bytes().decode("ascii", errors="replace")
        pending.extend(sibling_imports(text))
    return found


#: The two names a module declares to opt its own containers into the walk.
#: A PAIR RATHER THAN ONE MAPPING, because "bounded by a contract" and "forgives
#: nothing" are different claims and collapsing them would let the second be
#: made silently about a table doing the first.
REGISTRY_NAMES: Final = ("FORGIVENESS_TABLES", "NOT_A_FORGIVENESS")


def registry_problems(namespace: Mapping[str, object]) -> list[str]:
    """Every module-scope container a namespace holds that its OWN registries miss.

    THE CROSS-MODULE FORM OF THE WALK ``tests/test_docs_citations.py`` runs over
    itself, and it exists because that arm reads ``globals()`` and therefore
    cannot see one byte of any other file. Splitting a module without this is
    the evasion the single-module walk was written to forbid, arriving by
    relocation instead of by naming: declare the table one file over, import
    nothing, and the walk that exists to catch an unregistered table reports a
    confident zero.

    A MODULE ANSWERS FOR WHAT IT HOLDS, which is why the registries are read out
    of the namespace being walked rather than passed in. A central registry
    would have to name modules as well as tables, and the module that forgot to
    add itself would be the one nobody noticed - the same shape one level up.

    FIVE LEGS, and each is a separate way the pair can be true-looking and
    empty:

      1. the pair is DECLARED at all - a module holding neither is not
         answering, it is silent, and silence is what this walk refuses
      2. the namespace holds at least one container, so the legs below are not
         reading an empty set and passing whatever went uncounted
      3. every container sits in one registry or the other
      4. no container sits in BOTH, which is a claim contradicting itself
      5. no registry names a container the module no longer holds - a stale row
         is a record that has stopped describing anything

    AND THE ROWS THEMSELVES ARE CHECKED, not merely counted: a bounded table
    must name a contract the same module defines and that is spelled as one,
    and an exemption must state a reason. A row naming nothing is a name with
    no case behind it.

    THE CEILING OF THE MECHANISM, STATED, because it is the same one the
    single-module arm claims: a FALSE reason still silences the walk. What is
    removed is doing it silently - the row sits in the diff as a sentence
    somebody has to defend.

    Args:
        namespace: The module namespace to walk, normally a module's ``vars()``.

    Returns:
        One line per fault, sorted within each leg so the report is stable.
    """
    declared = [name for name in REGISTRY_NAMES if isinstance(namespace.get(name), Mapping)]
    if len(declared) != len(REGISTRY_NAMES):
        missing = [name for name in REGISTRY_NAMES if name not in declared]
        return [
            "declares no registry for its own module-scope containers"
            f" - missing {', '.join(missing)}. Nothing counts what this module holds,"
            " so a forgiveness table relocated into it buys silence for free."
        ]
    bounded = namespace["FORGIVENESS_TABLES"]
    forgiving_nothing = namespace["NOT_A_FORGIVENESS"]
    assert isinstance(bounded, Mapping)
    assert isinstance(forgiving_nothing, Mapping)
    containers = module_containers(namespace)
    if not containers:
        return [
            "holds no module-scope container at all, so the registry check below reads"
            " an empty set and would pass whatever went uncounted"
        ]
    problems = [
        f"{name} neither ratchets nor records why it forgives nothing"
        for name in sorted(containers)
        if name not in bounded and name not in forgiving_nothing
    ]
    problems.extend(
        f"{name} is registered as both a forgiveness and not one"
        for name in sorted(set(bounded) & set(forgiving_nothing))
    )
    problems.extend(
        f"{name} is registered but this module no longer holds it"
        for name in sorted((set(bounded) | set(forgiving_nothing)) - set(containers))
    )
    for table, contract in sorted(bounded.items()):
        if not callable(namespace.get(contract)):
            problems.append(f"{table} names {contract}, which this module does not define")
        elif not str(contract).startswith("test_"):
            problems.append(f"{table} is bounded by {contract}, which is not a contract")
    problems.extend(
        f"{table} is recorded as forgiving nothing and states no reason"
        for table, why in sorted(forgiving_nothing.items())
        if not str(why).strip()
    )
    return problems


#: EVERY FORGIVENESS TABLE THIS MODULE HOLDS, and the contract that BOUNDS it.
#: EMPTY, WHICH IS A CLAIM AND NOT AN ABSENCE. This module derives; it does not
#: forgive. The claim is checked rather than trusted - every container here is
#: required to sit in this mapping or in :data:`NOT_A_FORGIVENESS`, so a table
#: added here that forgives anything has to be registered before the suite is
#: green, and registering it here demands a contract that bounds it.
FORGIVENESS_TABLES: Final[Mapping[str, str]] = {}

#: The other half of the same walk: every module-scope container that forgives
#: NOTHING, with the reason it does not. THE POINT OF THE PAIR LIVING HERE AT
#: ALL is that a container in this file is invisible to the module that judges
#: citations unless it is imported back, so relocating a table into this one
#: would otherwise buy silence for free. It does not: this registry is walked by
#: ``tests/test_bare_path_citations.py`` over a population derived from the
#: import graph, and an unregistered container here is as red as an unregistered
#: container there.
NOT_A_FORGIVENESS: Final[Mapping[str, str]] = {
    "FORGIVENESS_TABLES": "the registry itself, walked by the contract that reads it",
    "LADDER_RUNGS": "the ladder's rung names, in order",
    "NOT_A_FORGIVENESS": "the registry itself, walked by the contract that reads it",
    "REGEX_CALL_SITES": "an equality census of source sites; every site is counted, none forgiven",
    "REGISTRY_NAMES": "the two names a module declares the pair under; it forgives nothing",
    "SUBSTRING_SITES": "an equality census of source sites; every site is counted, none forgiven",
    "_INTERPRETER_NAMES": "the three names the interpreter installs, excluded by exact match",
    "_SETUPTOOLS_FIND": "the manifest key path source_roots reads; it forgives nothing",
}
